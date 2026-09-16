# Cumulative experimental record

The initial reconstruction and seed checks predate the first Git commit; later
native evolution and independent comparisons retain their own source revisions.
Execution-time paths are retained verbatim. Source fingerprints and
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
| `evolution/20260915T101024.562418Z-search` | Completed subscription-backed native evolution | Seed plus 19 evaluated descendants; 80 cases × 50,000 evaluations; 21 database rows including seed island copy |
| `comparison/20260916T001949Z-frozen` | Frozen selected program, corrected baseline, parent ablation, fixed control | 8 paired cases × 4 methods × 100,000 evaluations; all 32 method checkpoints |
| `recovery/20260916` | Post-crash audit and restored native WebUI | Search integrity/lineage/case verification, WebUI HTTP/browser checks and screenshot |

Neither initial native seed check made model calls or generated descendants. The corrected
selection score is `1 / (1 + mean_offline_error)` and raw error remains the
scientific measurement. Two archive rows do not represent two evaluated programs.
The historical negative-score database is retained as an audit record, not used
as the starting point for future search.

After installing dependencies, inspect the archived native run:

```bash
bash scripts/webui.sh artifacts/evolution
```

Open http://localhost:8888 and select `101024` for the completed model-generated
search, or an earlier seed check for integration history. The search database was
published using SQLite's consistent backup API, merging the saved WAL; all native
program rows match the original. Other result files were copied byte-for-byte,
excluding disposable Python caches and SQLite sidecars. Historical absolute paths
remain provenance; the relative generation directories contain the saved outputs.

New runs are written to ignored `results/evolution` or `results/comparison`.
The original local search, comparison, logs and recovery backup remain intact.
Resume unfinished runs with `--resume` rather than starting duplicate controllers.
The published comparison has frozen program hashes, all case-level objective
accounting and landscape histories, summary statistics and appended progress logs.
See [the comparison report](../docs/comparison.md) and
[recovery commands](../docs/recovery.md). No extra model calls were made during
recovery; native cost fields are accounting estimates, not paid API charges.
