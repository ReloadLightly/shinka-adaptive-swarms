#!/usr/bin/env python3
"""Explicitly install the isolated v3 embedding runtime and pinned public model."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request

REPOSITORY = "jinaai/jina-embeddings-v2-base-code"
REVISION = "516f4baf13dec4ddddda8631e019b5737c8bc250"
ARTIFACTS = {
    "config.json": "e426aa684c7f9a95c5f020aa855faf93a24f065f5fad0c9e17b124670cabdea6",
    "tokenizer.json": "b01c78a902aa4facb2f47f95449f48e2f7bbfea5d2472ee2f6ce92323c6f86e5",
    "tokenizer_config.json": "f477aeb15ff9f78d3c1ddf2361d2b0b8b20cf55220f839f29a37f3a18efddd89",
    "special_tokens_map.json": "06e405a36dfe4b9604f484f6a1e619af1a7f7d09e34a8555eb0b77b66318067f",
    "README.md": "d3fcc84f4fa0b18b54e54a62171b7bb363109e776226edd02c96e105c097f494",
    "onnx/model_quantized.onnx": "ed45870251c9f0cf656e78aab0d37a23489066df8a222bb1c8caf8a45f2cb16d",
}
PACKAGES = [
    "anyio==4.15.1", "certifi==2026.7.22", "click==8.5.0", "coloredlogs==15.0.1",
    "exceptiongroup==1.3.1", "filelock==3.32.7", "flatbuffers==25.12.19", "fsspec==2026.7.0",
    "h11==0.16.0", "hf-xet==1.6.0", "httpcore==1.0.9", "httpx==0.28.1",
    "huggingface-hub==1.31.0", "humanfriendly==10.0", "idna==3.19", "mpmath==1.3.0",
    "numpy==2.2.6", "onnxruntime==1.23.2", "packaging==26.3", "protobuf==7.36.1",
    "pyyaml==6.0.3", "sympy==1.14.0", "tokenizers==0.23.2", "tqdm==4.70.1",
    "typing-extensions==4.16.0",
]


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=root / "results/joint_relocation_v3/embedding")
    parser.add_argument("--python", default="/usr/bin/python3.10")
    args = parser.parse_args()
    cache = args.cache.resolve()
    cache.mkdir(parents=True, exist_ok=True)
    environment = {**os.environ, "UV_CACHE_DIR": str(cache / "uv-cache")}
    python = cache / "venv/bin/python"
    if not python.exists():
        subprocess.run(["uv", "venv", "--python", args.python, str(cache / "venv")], env=environment, check=True)
    subprocess.run(["uv", "pip", "install", "--python", str(python), *PACKAGES], env=environment, check=True)
    locked = subprocess.run(["uv", "pip", "freeze", "--python", str(python)], env=environment,
                            capture_output=True, text=True, check=True).stdout
    (cache / "requirements.lock.txt").write_text(locked)
    records = []
    for name, expected in ARTIFACTS.items():
        path = cache / "model" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://huggingface.co/{REPOSITORY}/resolve/{REVISION}/{name}"
        if not path.exists():
            print(datetime.now(timezone.utc).isoformat(), "downloading", name, flush=True)
            temporary = path.with_name(path.name + ".download")
            with urllib.request.urlopen(url, timeout=120) as response, temporary.open("wb") as output:
                while data := response.read(1024 * 1024):
                    output.write(data)
            if hashlib.sha256(temporary.read_bytes()).hexdigest() != expected:
                raise ValueError(f"Downloaded artifact checksum mismatch: {name}")
            temporary.replace(path)
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Existing model artifact differs; preserved for inspection: {name}")
        records.append({"file": name, "url": url, "bytes": path.stat().st_size, "sha256": actual})
        print(datetime.now(timezone.utc).isoformat(), "verified", name, path.stat().st_size, flush=True)
    destination = cache / "model-manifest.json"
    if destination.exists():
        previous = json.loads(destination.read_text())
        if previous["revision"] != REVISION or previous["artifacts"] != records:
            raise ValueError("Existing model manifest differs; it was preserved")
    else:
        destination.write_text(json.dumps({
            "downloaded_at": datetime.now(timezone.utc).isoformat(), "repository": REPOSITORY,
            "revision": REVISION, "served_model_alias": "jina-code-v2-q8", "artifacts": records,
            "source_model_card": f"https://huggingface.co/{REPOSITORY}/blob/{REVISION}/README.md",
            "inference": "local ONNX Runtime CPU; official quantized weights; attention-mask mean pooling followed by L2 normalization",
        }, indent=2) + "\n")
    print("Local embedding assets ready:", destination, flush=True)


if __name__ == "__main__":
    main()
