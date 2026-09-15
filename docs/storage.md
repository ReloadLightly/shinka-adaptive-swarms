# Storage and continuation

The storage changes preserve the search suite, budgets, seeds, policy interface,
objective/feedback formulas, pinned simulator, and native Shinka selection. The
original task snapshot remains unchanged. Each storage evaluator adapter is
saved under `storage_runtime/<bundle-hash>/` with provenance linking it to the
frozen evaluator and supporting source hashes.

## Actual output path

`scripts/run_evolution.py` installs `StorageRunnerMixin` and
`install_native_storage` on the pinned native runner. Its `LocalJobConfig`
executes the recorded storage evaluator. This evaluator calls the same
`adaptive_swarms.simulator.run_case` and saves each completed case atomically.

- Case traces: `gen_N/results/case_XXX.json.gz`, streamed JSON serialization into
  gzip level 3, followed by decompression/checksum verification and atomic rename.
  No intermediate campaign of uncompressed cases is created. Existing JSON cases
  remain readable and unchanged. Baseline, comparison, and figure readers accept
  both formats. The simulator constructs one case result in memory, as before;
  it does not require an uncompressed output file.
- Candidate workspaces: native local submission passes the candidate and evaluator
  paths directly. It does not clone/copy the repository, environment, caches or
  historical results. Fresh module loading still isolates policy memory between
  cases. Python bytecode cache creation is disabled for launched children.
- Best result: `best/artifacts.json` references immutable generation artifacts with
  SHA-256 hashes; `best/main.py` is a small independent compatibility copy. An
  existing upstream best tree is retained by rename when first replaced. There
  are no mutable hard links or new full-tree copies.
- Logs: active verbose logs rotate at 4 MiB into losslessly compressed, verified
  segments. All archives are retained because old native logs can contain unique
  lineage evidence. `events.jsonl`, metrics, correctness judgments, candidate
  sources, prompts, responses and SQLite remain separate research evidence.
- Native Headless uses its existing fixed-version npm cache and the run's prompt
  files. There are no per-evaluation dependency installations or temporary builds
  in this launcher. Existing caches/environments are not removed.

The initial inspection found approximately 4.2 MiB in this evolution directory,
including a duplicated best tree. That does not explain all historical Windows
storage consumption; this patch protects this project's actual writers.

## Effective defaults

| Setting | Default |
|---|---:|
| C: warning | 15 GiB free |
| C: checkpoint floor | 10 GiB free |
| Output filesystem checkpoint floor | 1 GiB free |
| Additional finish/checkpoint allowance | 64 MiB per concurrent/next worker |
| Worker storage check | 5 seconds |
| Terminal storage report | 20 seconds |
| Run-only allocated-byte scan | 60 seconds |
| Compressed serialization | gzip level 3 |
| Active operational log segment | 4 MiB |

The launcher verifies that `/mnt/c` is the Windows C: drvfs mount before using
its available-byte reading. It also checks the filesystem containing the output.
A large Linux `/` free-space number cannot substitute for the host reading.
Two possible concurrent workers reserve 128 MiB, giving a C: launch/checkpoint
floor of **10.125 GiB**, not a 30 GiB start requirement. This modest allowance
covers bounded writer chunks and checkpoint/cancellation overhead; it is a
project storage setting, not a RAM reserve or a change to experiment size.

The scheduler checks before proposals and evaluation submissions. Writers check
while serializing large outputs, and a watcher checks during active jobs/model
calls. Reports include C: free space, output free space, active worker allowance,
run growth and the age of its run-only sample. No recurring home-directory scan
is used.

## Pause and resume

A low-space reading latches `storage-stop.json`, blocks new scheduling, preserves
job descriptors in `gen_N/storage-job.json`, and stops only this controller's
workers using a bounded grace period and native cancellation. Completed cases
remain at their original paths. `evaluation-checkpoint.json` records their
candidate/suite/scientific-source identity. Exit **75** and `storage_paused`
mean an operational interruption; they never mean zero fitness or scientific
failure. ENOSPC/EDQUOT follow the same path without automatic output retries.
A completely full disk may prevent writing a new marker; the in-memory latch
still stops workers, while previously committed checkpoints remain intact.

An explicit resume checks headroom again, archives the previous stop marker,
reuses completed database rows/cases, and resubmits an accepted pending candidate
without regenerating it. Legacy accepted proposals require unambiguous retained
native acceptance and lineage evidence. Incomplete proposal evidence is retained
before native generation resumes. Only an incomplete case may restart.

Resume the existing authorized 20-slot experiment:

```bash
cd /home/roland/actir/shinka-adaptive-swarms
.venv/bin/python -u scripts/run_evolution.py \
  --resume results/evolution/20260915T101024.562418Z-search \
  --generations 20 --model gpt-6-astra \
  --storage-warn-gib 15 --storage-checkpoint-gib 10 \
  --storage-output-checkpoint-gib 1 --storage-worker-headroom-mib 64 \
  --storage-check-seconds 5 --storage-report-seconds 20
```

Inner effort remains unspecified, as in the saved configuration. The subscription
route remains `headless/codex@gpt-6-astra`; there is no paid API fallback.

In another terminal:

```bash
bash scripts/webui.sh results/evolution 8888
# http://localhost:8888 — native UI on the actual programs.sqlite
```

Keep the launcher in a terminal (or an existing terminal multiplexer). Its flushed
progress and persistent rotating logs provide the current activity and measured
outcomes. The controller lock prevents duplicate launches. There is no automatic
low-storage restart loop.

## Focused verification

```bash
.venv/bin/python -m pytest -q
```

Storage tests use simulated readings and small fixtures. They check compressed
round trips and real downstream readers, frozen-evaluator scientific equivalence,
case reuse after interruption, separate host/output limits, in-flight writer stop,
ENOSPC latching, native best references/log rotation, and the real launcher/native
scheduler. Storage testing does not make experimental model calls or rerun the
completed study.

### Observed continuation (15 September 2026)

The final full test run reported **48 passed, 1 skipped**; the skipped read-only
legacy generation-3 recovery test no longer applies after that generation was
successfully completed (it passed before launch). The real-entrypoint test uses
a 31-query seed, simulates a low-space resume, then proves a healthy native resume
retains database rows, case bytes and modification time without reevaluation.
The adapter provenance check was rerun after making bundle directories immutable
across supporting-code changes.

At launch, verified C: free space was **31.951 GiB**. Generation 3 reused its saved
native proposal and lineage, completed four cases of 50,000 objective queries,
and wrote **91,461 gzip bytes** for **328,784 bytes** of lossless JSON. Generation
4 subsequently completed through native mutation/evaluation. The controller
continues the originally requested 20-slot experiment. Search performance is
separate from storage verification.

A before/after inventory verified **36 existing program/result/prompt files**
and the four original database rows were unchanged. The live native WebUI passed
HTTP database checks and browser navigation/screenshot checks with no reported
browser errors. Run-local records are in `storage-evidence/before-resume.json`
and `storage-evidence/resume-verification.json`; they contain hashes and outcomes,
not copied result trees.
