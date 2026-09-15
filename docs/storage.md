# Artifact compatibility after the storage rollback

The storage implementation task is canceled. The targeted rollback of
`997675c57c7f199d127f5c73cf68818b5523de0f` removes its execution restrictions while
retaining recorded scientific work and the compatibility needed to read and
resume it. The comparison script predates that task and remains in place.

## Removed restrictions

The launcher, scheduler, evaluator environment and current runtime adapters no
longer enforce:

- Mandatory verification that `/mnt/c` is Windows C:.
- The 10-GiB host and 1-GiB output filesystem free-space floors.
- The additional 64-MiB allowance per worker.
- The 64-MiB checkpoint-write cap.
- Periodic low-space cancellation, pause markers or resume headroom checks.
- Storage-specific runtime readiness requirements.

The corresponding command-line options and storage-guard environment activation
have been removed. Existing storage settings and stop markers remain historical
records. No replacement limits, experiment-budget reductions or RAM reserves
were added. Any disk reporting is informational.

Actual I/O failures still fail visibly. Evaluator infrastructure errors use exit
74 and remain separate from candidate correctness and fitness. Resume recognizes
historical evaluator exit 75 and incomplete checkpoints as unfinished execution,
without enforcing the canceled space policy.

## Retained compatibility

- Readers accept existing `case_XXX.json.gz` and legacy `case_XXX.json` files;
  atomic gzip serialization remains available without a write cap. Completed
  cases keep their original bytes and paths.
- `evaluation-checkpoint.json` retains candidate, suite and scientific-source
  identity so a resume reuses completed cases.
- Existing `storage-job.json` descriptors and retained native acceptance evidence
  preserve accepted candidate programs, parents, inspirations and explanations.
  Completed database generations are skipped on resume.
- `best/artifacts.json` keeps references and SHA-256 hashes pointing to original
  generation artifacts. Existing historical best trees remain in place.
- Rotated compressed logs remain readable and retained. Native subprocess sinks
  append to the existing evidence and propagate real I/O failures.
- The launcher selects the current evaluator from
  `storage_runtime/<bundle-hash>/`, with provenance linking it to the frozen
  scientific evaluator. Historical `storage_runtime` bundles and the original
  task snapshot remain untouched evidence.

The simulator, search suite, budgets, seeds, objective accounting, feedback and
native selection settings are unchanged. Compatibility checks replay small saved
fixtures or mock native execution; they do not run model calls or new benchmark
evaluations.

## Completed run and terminal commands

`results/evolution/20260915T101024.562418Z-search` completed at
**2026-09-15 12:41:51 UTC**, before rollback began. All **20 generations (0–19)**
were present at inspection, with **21 database rows** because native initialization
also stores a seed island copy. PID 16326 had exited. No controller interruption
or restart was needed, and the existing native WebUI (PID 14342) was left alone.

For an unfinished run only, use its existing configuration and target:

```bash
cd /home/roland/actir/shinka-adaptive-swarms
.venv/bin/python -u scripts/run_evolution.py \
  --resume "results/evolution/<unfinished-run>" \
  --generations 20 --model gpt-6-astra
```

The completed run's saved inner effort remains unspecified, and its model route
remains subscription-authenticated `headless/codex@gpt-6-astra`.

The existing WebUI serves the actual native database at http://localhost:8888.
If it is later stopped, its launch command is:

```bash
bash scripts/webui.sh results/evolution 8888
```

Launchers retain flushed, timestamped terminal progress and persistent logs.

## Focused verification and recovery

```bash
.venv/bin/python -m pytest -q \
  tests/test_storage_runner.py tests/test_storage_artifacts.py \
  tests/test_native_storage.py
```

These checks cover unrestricted scheduling and launcher activation, gzip and
artifact readers, saved-case reuse, pending-proposal lineage, and actual I/O
failures. The previous tests that enforced the canceled limits have been removed.

Before editing, the recovery branch
`recovery/canceled-storage-20260915-997675c` retained the original commit. Local
recovery records under `results/rollback/20260915T124531Z/` contain uncommitted
code patches and a hash/database inventory, without copying the result tree.
The original continuation records under the run's `storage-evidence/` remain
historical evidence of work completed before this reversal.

The post-edit read-only inventory matched all **447 recorded files** and all
**six database tables**. Generations **0–19** and **21 program rows** remained
present before and after the rollback. All **80 case artifacts**, including
**68 gzip files**, remained readable; **16 best-artifact references** verified.
No completed candidate or evaluation was regenerated. The completed experiment
was left stopped, and the WebUI remained running.

Focused rollback verification reported **24 passed, 1 skipped** on 15 September
2026. The historical interrupted-generation-3 test skipped because that
proposal has since completed. A minimal `asyncio.to_thread` check reproduced a
sandbox-only shutdown hang, so the focused checks ran outside that sandbox and
completed successfully. Timestamped output is retained in
`results/rollback/20260915T124531Z/verification.log`.
