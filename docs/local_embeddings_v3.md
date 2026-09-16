# V3 local code embeddings and development calibration

The prospective V3 engine uses
`local/jina-code-v2-q8@http://127.0.0.1:8910/v1`. All embedding inference runs
locally on CPU. The mutation, novelty-judge and meta-memory language-model calls
retain the separately configured subscription-backed Codex route.

The encoder is Jina's code-specific model, using the owner's official quantized
ONNX artifact. Its model card describes training for code/docstring similarity
and prescribes mean pooling followed by normalization. This makes it a relevant
small local encoder to test; it does not establish sensitivity to policy behavior.
Sources inspected before setup: [Jina model card](https://huggingface.co/jinaai/jina-embeddings-v2-base-code/blob/516f4baf13dec4ddddda8631e019b5737c8bc250/README.md),
[official ONNX artifacts](https://huggingface.co/jinaai/jina-embeddings-v2-base-code/tree/516f4baf13dec4ddddda8631e019b5737c8bc250/onnx),
and [ONNX Runtime inference API](https://onnxruntime.ai/docs/api/python/api_summary.html).

| Frozen setting | Value |
|---|---|
| Model | `jinaai/jina-embeddings-v2-base-code` |
| Repository revision | `516f4baf13dec4ddddda8631e019b5737c8bc250` |
| ONNX file | `onnx/model_quantized.onnx`, 161,895,621 bytes |
| ONNX SHA-256 | `ed45870251c9f0cf656e78aab0d37a23489066df8a222bb1c8caf8a45f2cb16d` |
| Embedding dimension | 768 |
| Runtime | Python 3.10.12; ONNX Runtime 1.23.2; tokenizers 0.23.2; NumPy 2.2.6 |
| Execution | CPU, two intra-operation threads, one inter-operation thread |
| Input handling | Raw source; no AST normalization, comment removal or semantic execution |
| Long source | Explicit disjoint 510-token payload windows plus two special tokens |
| Pooling | Mean over all non-padding window tokens, then L2 normalization |
| Native judge trigger | cosine similarity **greater than 0.830958258366903** |

The server keeps every raw input token. Long-input pooling includes each window's
special tokens and differs from a single full-context model pass. This choice
keeps attention work bounded for longer programs. Model files are checked against
the pinned manifest at startup. The server binds only to `127.0.0.1`, reads local
weights and provides no remote inference fallback. Unknown model names fail.

## Calibration evidence and limitations

Before any V3 search, `scripts/calibrate_local_embeddings.py` embedded twenty
authored development snippets through the actual pinned Shinka embedding clients.
Nine labeled cosmetic pairs covered identical source, formatting, comments,
docstrings, argument renaming, dictionary order and local assignment. Ten
meaningful pairs changed counts, radii or conditions. No optimizer cases,
validation measurements, held-out inputs or Codex calls were used.

The declared rule chooses the midpoint if the groups separate. If they overlap,
it uses the minimum cosmetic similarity minus 0.000001, forwarding all listed
cosmetic duplicates to the native language-model judge. That rule was recorded
before the local inference calls.

The observed groups **overlapped**: minimum cosmetic similarity was
**0.830959258366903**, while maximum meaningful-change similarity was
**0.9937252841917575**. The resulting threshold forwards **9/9 cosmetic pairs
and 10/10 meaningful pairs** to the judge. It is therefore a broad routing filter
on these examples, not a successful automatic distinction between cosmetic and
behavioral changes. The stock 0.99 would miss several cosmetic rewrites while
still routing some numeric changes. The native judge can accept meaningful
changes above the threshold; the embedding threshold does not itself establish
scientific novelty. A small authored set gives no future-error-rate guarantee.

Synchronous and asynchronous native-client embeddings agreed for the same
development source. A long-input probe retained all 1,704 payload tokens in four
windows, producing 1,712 tokens including the eight added special tokens. Changing
the late count altered the resulting vector (cosine 0.999894099395823).

An initial development service relied on the tokenizer's automatic overflow
objects, which exposed only 516 tokens for this same long input. This concrete
failure was corrected with explicit token slicing before research execution.
Both calibration directories and the original service logs are preserved; the
short-snippet similarities and selected threshold were unchanged. This is an
implementation correction, not an evolutionary improvement.

## Setup, launch and reproduction

The setup script installs pinned dependencies in the ignored
`results/joint_relocation_v3/embedding/venv` and downloads only the fixed public
model artifacts. It preserves existing valid assets and refuses mismatched files.
The research `.venv`, `pyproject.toml` and `uv.lock` are unchanged.

```bash
python scripts/setup_local_embeddings.py --python /usr/bin/python3.10

# Keep this terminal open, or use the recorded detached launch command.
results/joint_relocation_v3/embedding/venv/bin/python -u \
  scripts/serve_local_embeddings.py --port 8910 --threads 2 --chunk-tokens 512

curl http://127.0.0.1:8910/health

# Use a new directory; completed development measurements are never overwritten.
.venv/bin/python -u scripts/calibrate_local_embeddings.py \
  --route 'local/jina-code-v2-q8@http://127.0.0.1:8910/v1' \
  --output results/joint_relocation_v3/embedding/calibration_reproduction

tail -F results/joint_relocation_v3/operations/embedding-terminal.log
```

The recorded service launch uses port 8910 because an existing listener occupied
8891 and was preserved. Do not start a second copy on the same port. Persistent
JSONL events record timestamps, input hashes, token/window counts, dimensions,
elapsed time and errors; they do not include input source text. The operations
directory retains the launch command, PID, complete dependency list, model
manifest, calibration declarations, full source/vector data and compatibility
checks. Local compute is not a paid API call; native zero-dollar embedding
metadata is not an accounting of electricity or host cost.
