#!/usr/bin/env python3
"""Serve a pinned local ONNX code encoder through Shinka's embeddings protocol.

Runtime dependencies live in an isolated workspace environment. Model downloads
are a separate explicit setup step; this server never contacts a model API.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.metadata
import json
from pathlib import Path
import threading
import time
import traceback

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer


class LocalEncoder:
    def __init__(self, args):
        self.args = args
        self.started = time.monotonic()
        self.lock = threading.Lock()
        self.log_lock = threading.Lock()
        args.log_dir.mkdir(parents=True, exist_ok=True)
        self.events = (args.log_dir / "events.jsonl").open("a", buffering=1)
        self.manifest = json.loads(args.model_manifest.read_text())
        for record in self.manifest["artifacts"]:
            actual = hashlib.sha256((args.model_dir / record["file"]).read_bytes()).hexdigest()
            if actual != record["sha256"]:
                raise ValueError(f"Pinned model artifact changed: {record['file']}")
        self.tokenizer = Tokenizer.from_file(str(args.model_dir / "tokenizer.json"))
        # Preserve every input token through disjoint windows. This bounds the
        # quadratic attention working set without silently truncating source.
        self.tokenizer.no_truncation()
        self.tokenizer.no_padding()
        self.cls_id = self.tokenizer.token_to_id("<s>")
        self.sep_id = self.tokenizer.token_to_id("</s>")
        if self.cls_id != 0 or self.sep_id != 2:
            raise ValueError("Pinned Jina tokenizer special tokens differ")
        options = ort.SessionOptions()
        options.intra_op_num_threads = args.threads
        options.inter_op_num_threads = 1
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        self.session = ort.InferenceSession(
            str(args.model_dir / "onnx/model_quantized.onnx"),
            sess_options=options, providers=["CPUExecutionProvider"])
        self.inputs = {item.name: item.type for item in self.session.get_inputs()}
        self.output = self.session.get_outputs()[0].name
        self.metadata = {
            "model": args.served_model, "repository": self.manifest["repository"],
            "revision": self.manifest["revision"], "dimensions": 768,
            "provider": "CPUExecutionProvider", "quantization": "official ONNX int8 artifact",
            "chunk_tokens": args.chunk_tokens, "chunk_stride": 0,
            "pooling": "attention-mask token mean across all disjoint windows, then L2 normalize",
            "overlong_input": "all windows encoded; no source tokens discarded; window special tokens retained",
            "threads": args.threads, "inputs": self.inputs, "output": self.output,
            "runtime_versions": {name: importlib.metadata.version(name)
                                 for name in ["numpy", "onnxruntime", "tokenizers"]},
            "server_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "model_manifest_sha256": hashlib.sha256(args.model_manifest.read_bytes()).hexdigest(),
            "network_model_calls": False,
        }
        self.emit("model_loaded", **self.metadata)

    def emit(self, event, **values):
        record = {"timestamp": datetime.now(timezone.utc).isoformat(),
                  "elapsed_seconds": round(time.monotonic() - self.started, 3),
                  "event": event, **values}
        with self.log_lock:
            line = json.dumps(record, sort_keys=True)
            self.events.write(line + "\n")
            print(line, flush=True)

    def encode(self, texts):
        embeddings, token_counts, chunk_counts = [], [], []
        with self.lock:
            for text in texts:
                payload = self.tokenizer.encode(text, add_special_tokens=False).ids
                width = self.args.chunk_tokens - 2
                pieces = [payload[start:start + width] for start in range(0, len(payload), width)] or [[]]
                chunks = [[self.cls_id, *piece, self.sep_id] for piece in pieces]
                if sum(len(chunk) - 2 for chunk in chunks) != len(payload):
                    raise ValueError("Local chunk construction lost input tokens")
                total = np.zeros(768, dtype=np.float64)
                count = 0
                for chunk in chunks:
                    arrays = {"input_ids": np.asarray([chunk], dtype=np.int64),
                              "attention_mask": np.ones((1, len(chunk)), dtype=np.int64),
                              "token_type_ids": np.zeros((1, len(chunk)), dtype=np.int64)}
                    unknown = set(self.inputs) - set(arrays)
                    if unknown:
                        raise ValueError(f"Unsupported pinned ONNX inputs: {sorted(unknown)}")
                    output = self.session.run([self.output], {name: arrays[name] for name in self.inputs})[0]
                    if output.ndim != 3 or output.shape[-1] != 768:
                        raise ValueError(f"Unexpected token embedding shape: {output.shape}")
                    mask = arrays["attention_mask"][0].astype(bool)
                    total += output[0][mask].sum(axis=0, dtype=np.float64)
                    count += int(mask.sum())
                vector = total / max(count, 1)
                norm = float(np.linalg.norm(vector))
                if not np.isfinite(vector).all() or not np.isfinite(norm) or norm <= 0:
                    raise ValueError("Encoder produced an invalid vector")
                embeddings.append((vector / norm).astype(np.float32).tolist())
                token_counts.append(count)
                chunk_counts.append(len(chunks))
        return embeddings, token_counts, chunk_counts


def serve(args):
    encoder = LocalEncoder(args)

    class Handler(BaseHTTPRequestHandler):
        server_version = "LocalCodeEmbeddings/1"

        def log_message(self, fmt, *values):
            # Structured request logs below avoid duplicate un-timestamped logs.
            pass

        def respond(self, status, body):
            data = json.dumps(body, allow_nan=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path in {"/health", "/v1/health"}:
                self.respond(200, {"status": "ready", **encoder.metadata})
            elif path in {"/models", "/v1/models"}:
                self.respond(200, {"object": "list", "data": [{"id": args.served_model,
                    "object": "model", "created": 0, "owned_by": "local"}]})
            else:
                self.respond(404, {"error": {"message": "Unknown local endpoint"}})

        def do_POST(self):
            started = time.monotonic()
            try:
                if self.path.split("?", 1)[0] not in {"/embeddings", "/v1/embeddings"}:
                    self.respond(404, {"error": {"message": "Unknown local endpoint"}})
                    return
                request = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
                if request.get("model") != args.served_model:
                    raise ValueError("Unknown model; no remote model fallback is available")
                if request.get("encoding_format", "float") != "float":
                    raise ValueError("This local endpoint supports float embeddings")
                texts = request.get("input")
                if isinstance(texts, str):
                    texts = [texts]
                if not isinstance(texts, list) or not texts or not all(isinstance(t, str) for t in texts):
                    raise ValueError("input must be a string or nonempty list of strings")
                encoder.emit("embedding_started", input_count=len(texts),
                             input_sha256=[hashlib.sha256(t.encode()).hexdigest() for t in texts])
                embeddings, token_counts, chunks = encoder.encode(texts)
                self.respond(200, {"object": "list", "model": args.served_model,
                    "data": [{"object": "embedding", "index": i, "embedding": vector}
                             for i, vector in enumerate(embeddings)],
                    "usage": {"prompt_tokens": sum(token_counts), "total_tokens": sum(token_counts)}})
                encoder.emit("embedding_complete", input_count=len(texts), token_counts=token_counts,
                             chunk_counts=chunks, dimensions=768,
                             duration_seconds=round(time.monotonic() - started, 4))
            except (ValueError, TypeError) as exc:
                encoder.emit("request_error", error=f"{type(exc).__name__}: {exc}")
                self.respond(400, {"error": {"message": str(exc), "type": "invalid_request_error"}})
            except Exception as exc:
                encoder.emit("embedding_error", error=f"{type(exc).__name__}: {exc}")
                traceback.print_exc()
                self.respond(500, {"error": {"message": str(exc), "type": "local_inference_error"}})

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    encoder.emit("service_ready", endpoint=f"http://127.0.0.1:{args.port}/v1",
                 shinka_route=f"local/{args.served_model}@http://127.0.0.1:{args.port}/v1")
    try:
        server.serve_forever()
    finally:
        server.server_close()
        encoder.events.close()


def main():
    root = Path(__file__).resolve().parents[1]
    cache = root / "results/joint_relocation_v3/embedding"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=cache / "model")
    parser.add_argument("--model-manifest", type=Path, default=cache / "model-manifest.json")
    parser.add_argument("--served-model", default="jina-code-v2-q8")
    parser.add_argument("--port", type=int, default=8910)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--chunk-tokens", type=int, default=512)
    parser.add_argument("--log-dir", type=Path, default=root / "results/joint_relocation_v3/operations/embedding-service")
    args = parser.parse_args()
    if args.threads < 1 or not 4 <= args.chunk_tokens <= 8192:
        parser.error("threads must be positive and chunk-tokens must be in [4,8192]")
    serve(args)


if __name__ == "__main__":
    main()
