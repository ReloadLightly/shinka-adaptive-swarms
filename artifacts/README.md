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
| `relocation_allocation_v2/evolution/20260916T013407.256962Z-search` | Separate native integer-allocation search | 20 evaluated slots, 19 subscription mutation attempts, 320 cases × 100,000 queries; 21 database rows including seed island copy |
| `relocation_allocation_v2/study_20260916` | Frozen validation selection, final comparison and mechanism analysis | 144 validation and 200 final method cases × 100,000 queries; 40 independent final landscapes, no aliases |
| `relocation_allocation_v2/operations` | V2 execution and independent audits | Seed separation, source reviews, prompt delivery, query/lineage checks, WebUI evidence and publication records |
| `preparation_joint_v3/20260916-native-seed` | V3 native task integration diagnostic, not the prospective research campaign | One baseline-equivalent seed case × 1,000 queries; zero LLM or embedding calls |
| `preparation_joint_v3/20260916-execution-readiness` | Prospective V3 execution settings and local embedding calibration | Recorded before research; separate from research-case totals |
| `joint_relocation_v3/evolution` | Three native research-profile searches, seeds 610001/610002/610003 | 30 terminal slots and 29 valid descendants each; 1,440 executions × 100,000 queries; no terminal failures |
| `joint_relocation_v3/study_20260916` | Frozen source review, validation, selection, fresh final comparison and analysis | 960 validation + 560 final executions × 100,000 queries; 80 independent final histories; 24 nominal fixed settings/21 execution classes |
| `joint_relocation_v3/operations` | V3 calibration, model receipts audit, freeze/seed checks, independent statistical verification and operational evidence | 236 native wrappers/308 usable logical responses; 94 research embeddings; preserved clock, browser and supervision limitations |
| `joint_relocation_v3_publication` | Read-only checks after closing the immutable research archive | Portable archive/accounting/statistical verification and final browser-address evidence; no new research executions |

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

The [allocation-v2 report](../docs/relocation_allocation_v2.md) explains the mixed
final result and the retained auxiliary search-feedback labeling deviation.
V2 contains a frozen shortlist, exact source review, all six constant validation
results, selected generation-13 source and global count-two comparator,
case-weighted mechanism-control distributions, post-selection fresh seeds,
all compressed checkpoints, `analysis.json` and `final_case_outcomes.csv`.
Every final method uses exactly 100,000 objective queries, including detection
and memory reevaluation. The primary and mechanism contrasts retain all 40
paired effects and their stratified bootstrap uncertainty.

The v2 native database was published through SQLite's consistent backup API;
every table and row matches the original. Other scientific files are copied
byte-for-byte. Existing v1 scientific files remain unchanged. V2's recorded
inner model is `headless/codex@gpt-6-astra`, with no effort override and an
unverified effective default. No model calls were made in validation or final
comparison. The 664 v2 method cases used 66.4 million objective evaluations.

```bash
# Native archive viewer; does not execute candidates or call a model.
bash scripts/webui.sh artifacts/relocation_allocation_v2/evolution 8889

# Regenerate measured figures from archived outcomes.
.venv/bin/python scripts/plot_allocation_study.py \
  --run artifacts/relocation_allocation_v2/study_20260916 \
  --output assets/relocation_allocation_v2
```

The [joint-relocation V3 report](../docs/joint_relocation_v3.md) records a
completed negative result: overall winner minus corrected baseline is
**+0.0227 [−0.2044, +0.2368]** with the predeclared 97.5% interval. The
validation-selected fixed pair is identical to the baseline, so the two primary
labels are one distinct numerical comparison. Component and joint-sampler
contrasts do not establish useful current-state dependence. All three winners,
all 80 final histories and all large losses are retained.

V3 totals **2,960 physical executions / 296 million counted objective queries**,
excluding implementation checks. The 24 nominal validation fixed settings have
21 established execution classes; final evaluation has eight labels and seven
execution classes. Alias records identify representative checkpoints. The
original registration and source snapshots remain alongside the two dated,
pre-protected alias amendments. Sources, controls, sampler pairs and analysis
were frozen before the 160 fresh final seed values were generated.

`joint_relocation_v3/ARCHIVE.json` records each byte-identical scientific copy,
each bounded operational-log snapshot and each consistent SQLite backup. All
schema objects and table rows were verified. Its local `MANIFEST.json` is the
archive completion marker and inventories every payload file. The previous
global inventory is preserved as
`joint_relocation_v3/operations/artifacts-inventory-before-v3.json`; durable
historical scientific artifacts remain unchanged. Disposable SQLite sidecars
are represented by their database backups, not retained as inventory promises.

The V3 archive includes the exact sources and explanatory lineage for all
programs, native prompts and `engine_calls` receipts, novelty retries, meta
recommendations, migration evidence, every compressed case checkpoint, frozen
selection, final seeds, analysis, independent audit script and local embedding
calibration. Model weights, environments, authentication data and disposable
runtime state are excluded. The archived 1,000-query seed diagnostic is not a
measurement of cumulative preparation-test queries, which were uninstrumented.

```bash
# View the actual archived native databases without research/model calls.
bash scripts/webui.sh artifacts/joint_relocation_v3/evolution 8893

# Read-only verification with paths resolved inside the published archive.
.venv/bin/python scripts/audit_joint_progress.py \
  --study artifacts/joint_relocation_v3/study_20260916 \
  --archive-root artifacts/joint_relocation_v3
.venv/bin/python scripts/check_joint_analysis.py \
  --run artifacts/joint_relocation_v3/study_20260916

# Regenerate measured 5D figures; no candidate or objective execution.
.venv/bin/python scripts/plot_joint_study.py \
  --run artifacts/joint_relocation_v3/study_20260916 \
  --output assets/joint_relocation_v3
```

Use another free port if a correct native viewer already occupies 8893. The
original local V3 runs, persistent logs and services remain in `results/`.
