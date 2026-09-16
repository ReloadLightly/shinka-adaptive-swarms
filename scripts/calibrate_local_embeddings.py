#!/usr/bin/env python3
"""Freeze a local novelty threshold using authored development source only.

No optimization cases, validation outcomes, protected inputs or LLM calls are
used. All vectors and pair labels are retained, including imperfect separation.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
import time
import urllib.request


BASE = 'def choose_relocation(observation):\n    return {"count": 5, "radius_scale": 1.0}\n'
CONDITIONAL = '''def choose_relocation(observation):
    count = 3
    radius = 1.0
    if observation["fitness_drop"] > observation["recent_improvement"]:
        count = 5
        radius = 2.0
    return {"count": count, "radius_scale": radius}
'''


def development_sources():
    snippets = {"baseline": BASE, "conditional": CONDITIONAL,
        "identical": BASE,
        "whitespace": 'def choose_relocation( observation ):\n\n    return { "count" : 5, "radius_scale" : 1.0 }\n',
        "comment": '# Relocate every particle at the baseline radius.\n' + BASE,
        "docstring": BASE.replace('    return', '    """Choose the fixed baseline relocation response."""\n    return'),
        "argument_rename": BASE.replace('observation', 'state'),
        "dictionary_order": 'def choose_relocation(observation):\n    return {"radius_scale": 1.0, "count": 5}\n',
        "local_assignment": 'def choose_relocation(observation):\n    answer = {"count": 5, "radius_scale": 1.0}\n    return answer\n',
        "count_four": BASE.replace('"count": 5', '"count": 4'),
        "count_three": BASE.replace('"count": 5', '"count": 3'),
        "count_zero": BASE.replace('"count": 5', '"count": 0'),
        "radius_half": BASE.replace('"radius_scale": 1.0', '"radius_scale": 0.5'),
        "radius_two": BASE.replace('"radius_scale": 1.0', '"radius_scale": 2.0'),
        "radius_four": BASE.replace('"radius_scale": 1.0', '"radius_scale": 4.0'),
        "conditional_comment": '# Observed deterioration can increase exploration.\n' + CONDITIONAL,
        "conditional_rename": CONDITIONAL.replace('count', 'allocation').replace('"allocation"', '"count"'),
        "conditional_count_four": CONDITIONAL.replace('count = 5', 'count = 4'),
        "conditional_radius_four": CONDITIONAL.replace('radius = 2.0', 'radius = 4.0'),
        "conditional_reversed_sign": CONDITIONAL.replace('] > observation', '] < observation'),
    }
    cosmetic = [("baseline", name) for name in ["identical", "whitespace", "comment", "docstring",
        "argument_rename", "dictionary_order", "local_assignment"]]
    cosmetic += [("conditional", name) for name in ["conditional_comment", "conditional_rename"]]
    meaningful = [("baseline", name) for name in ["count_four", "count_three", "count_zero",
        "radius_half", "radius_two", "radius_four", "conditional"]]
    meaningful += [("conditional", name) for name in ["conditional_count_four", "conditional_radius_four",
        "conditional_reversed_sign"]]
    return snippets, cosmetic, meaningful


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b)) / math.sqrt(sum(x*x for x in a) * sum(y*y for y in b))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route", default="local/jina-code-v2-q8@http://127.0.0.1:8910/v1")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Preserve completed calibration: choose a new output directory")
    from shinka.embed.embedding import EmbeddingClient, AsyncEmbeddingClient
    from shinka.local_openai_config import parse_local_openai_model
    resolved = parse_local_openai_model(args.route)
    if resolved is None or not resolved.base_url.startswith("http://127.0.0.1:"):
        raise SystemExit("Calibration requires the explicit loopback local embedding route")
    args.output.mkdir(parents=True)
    with urllib.request.urlopen(resolved.base_url + "/health", timeout=10) as response:
        service = json.load(response)
    snippets, cosmetic, meaningful = development_sources()
    declaration = {
        "declared_at": datetime.now(timezone.utc).isoformat(), "sources": snippets,
        "cosmetic_pairs": cosmetic, "meaningful_pairs": meaningful,
        "threshold_rule": "If max meaningful similarity < min cosmetic similarity, use their midpoint. Otherwise use min cosmetic similarity minus 0.000001, clipped to [0,1], forwarding every listed cosmetic duplicate to the native LLM judge; report overlapping meaningful changes.",
        "scope": "Authored development code only; no simulator runs, benchmark cases or Codex inference",
    }
    (args.output / "declaration.json").write_text(json.dumps(declaration, indent=2) + "\n")
    started = time.monotonic()
    print(datetime.now(timezone.utc).isoformat(), "development_embedding_start", len(snippets), "sources", flush=True)
    client = EmbeddingClient(model_name=args.route)
    names = list(snippets)
    embeddings, cost = client.get_embedding([snippets[name] for name in names])
    if len(embeddings) != len(names) or any(len(vector) != 768 for vector in embeddings):
        raise RuntimeError("Native embedding client returned missing or wrong-sized real vectors")
    if not all(math.isfinite(value) for vector in embeddings for value in vector):
        raise RuntimeError("Local model produced nonfinite vectors")
    vectors = dict(zip(names, embeddings))
    pairs = [{"kind": kind, "left": left, "right": right, "cosine_similarity": cosine(vectors[left], vectors[right])}
             for kind, group in [("cosmetic", cosmetic), ("meaningful", meaningful)] for left, right in group]
    cmin = min(row["cosine_similarity"] for row in pairs if row["kind"] == "cosmetic")
    mmax = max(row["cosine_similarity"] for row in pairs if row["kind"] == "meaningful")
    threshold = (cmin + mmax) / 2 if mmax < cmin else max(0.0, min(1.0, cmin - 0.000001))
    for row in pairs:
        row["native_judge_triggered"] = row["cosine_similarity"] > threshold
    # Exercise the actual asynchronous native path used by the engine as well.
    async def smoke():
        return await AsyncEmbeddingClient(model_name=args.route).embed_async(BASE)
    async_vector, async_cost = asyncio.run(smoke())
    if len(async_vector) != 768:
        raise RuntimeError("Native async embedding client returned an empty or malformed vector")
    # A changed tail after multiple windows tests the server's all-window path.
    long_prefix = ''.join(f'# Development-only padding line {i}: code embedding window coverage.\n' for i in range(120))
    long_sources = [long_prefix + BASE, long_prefix + snippets["count_zero"]]
    long_vectors, long_cost = client.get_embedding(long_sources)
    if len(long_vectors) != 2 or any(len(v) != 768 for v in long_vectors):
        raise RuntimeError("Long-source embedding request failed")
    result = {
        "completed_at": datetime.now(timezone.utc).isoformat(), "route": args.route,
        "service": service, "threshold": threshold, "threshold_rule": declaration["threshold_rule"],
        "cosmetic_min_similarity": cmin, "meaningful_max_similarity": mmax,
        "groups_separated": mmax < cmin, "pairs": pairs,
        "cosmetic_pairs_forwarded_to_judge": sum(r["native_judge_triggered"] for r in pairs if r["kind"] == "cosmetic"),
        "meaningful_pairs_forwarded_to_judge": sum(r["native_judge_triggered"] for r in pairs if r["kind"] == "meaningful"),
        "cosmetic_pair_count": len(cosmetic), "meaningful_pair_count": len(meaningful),
        "native_sync_async_cosine": cosine(vectors["baseline"], async_vector),
        "long_source_tail_change_cosine": cosine(*long_vectors),
        "local_cost_reported_by_native_client": cost + async_cost + long_cost,
        "dimensions": 768, "duration_seconds": time.monotonic() - started,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "limitations": [
            "Cosine similarity is a heuristic for routing to the native LLM novelty judge, not a behavior-equivalence oracle or originality measure.",
            "Meaningful numeric changes can have higher similarity than cosmetic rewrites; false positives and unseen cosmetic false negatives remain possible.",
            "A small authored calibration set does not estimate novelty quality across future evolved programs.",
            "Official quantized ONNX inference and 512-token disjoint window pooling are the frozen local representation; long-window aggregation differs from one full-context pass.",
            "Local inference uses no paid model API. This check makes no mutation, novelty-judge or meta-memory Codex calls.",
        ],
    }
    (args.output / "vectors.json").write_text(json.dumps({"sources": snippets, "vectors": vectors,
        "async_baseline_vector": async_vector, "long_sources": long_sources, "long_vectors": long_vectors}, indent=2) + "\n")
    (args.output / "calibration.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ["threshold", "cosmetic_min_similarity", "meaningful_max_similarity",
        "groups_separated", "cosmetic_pairs_forwarded_to_judge", "meaningful_pairs_forwarded_to_judge", "duration_seconds"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
