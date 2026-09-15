# Initial experimental record

These files are measured outputs from the first build, before its initial Git
commit. Execution-time paths are retained verbatim. Source fingerprints and
provenance notes identify the numerical code used. `MANIFEST.json` inventories the
published files by relative path, byte count and SHA-256, excluding the inventory
itself and disposable Python bytecode caches.

| Directory | Role | Completed work |
|---|---|---|
| `reconstruction_initial` | Short initial diagnostic | 3 × 50,000 evaluations |
| `reconstruction_v1` | Reported 5D reconstruction | 3 × 500,000 evaluations |
| `visualization_v1` | Separate 2D illustration | 1 × 9,000 evaluations |
| `evolution/20260915T094509.711861Z-seed` | Historical integration check using negative selection score | Seed only; native best-score display exposed an upstream initialization issue |
| `evolution/20260915T094647.219057Z-seed` | Corrected native seed check using reciprocal score | 4 × 50,000 evaluations; one seed plus one native island copy |

Neither native check made model calls or generated descendants. The corrected
selection score is `1 / (1 + mean_offline_error)` and raw error remains the
scientific measurement. Two archive rows do not represent two evaluated programs.
The historical negative-score database is retained as an audit record, not used
as the starting point for future search.

After installing dependencies, inspect the archived native run:

```bash
bash scripts/webui.sh artifacts/evolution
```

Open http://localhost:8888 and select the later `094647` seed database. New live
evolution runs are written to ignored `results/evolution`; preserve selected raw
outputs and regenerate the inventory when publishing future experiments. Use a
new run for the first model-generated search so its final evaluator/context
snapshot is explicit. Resume interrupted runs with the launcher's `--resume`
option rather than starting duplicate controllers.
