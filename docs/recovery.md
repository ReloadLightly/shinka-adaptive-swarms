# WSL recovery, 16 September 2026

Host process inspection found no surviving controller or WebUI for this project
after the WSL restart. The saved experiment had already completed at
**15 September 2026, 12:41:51 UTC**. Its manifest, final event, native database,
case files and checkpoints agreed, so no completed search evaluation was repeated.

The preserved search is
`results/evolution/20260915T101024.562418Z-search`. Its published copy is
[the native search archive](../artifacts/evolution/20260915T101024.562418Z-search).
SQLite integrity passed; 21 rows represent 20 evaluated programs because the seed
also has an island copy. All 80 case artifacts were readable, with 50,000 counted
objective evaluations each. Candidate source, lineage, completed checkpoints and
best-artifact hashes were checked. A consistent SQLite backup included the saved
WAL before the WebUI was opened; the original run and earlier results were retained.

The next authorized stage completed using the existing comparison runner in
`results/comparison/20260916T001949Z-frozen`. Generation 12 was selected strictly
by search score. Before execution, it was frozen with its native parent as a
compactness ablation and an investigator-defined fixed-response control. A
readiness audit had already inspected the suite configuration, but no comparison
outcomes existed and none informed selection or controls; this is recorded in
`freeze.json`. All **32 method cases** and **3.2 million objective evaluations**
completed at **16 September 2026, 00:23:42 UTC**. Selected-minus-baseline mean
offline error was +0.0627, with a bootstrap 95% interval spanning zero. This does
not establish a performance advantage. See [the comparison report](comparison.md)
for results and limits.

## Terminal progress

The comparison was launched in a detached host process with unbuffered stdout,
timestamped events, an honest 20-second idle heartbeat, and immediate atomic
checkpoints after each method-case evaluation. Detaching survives a terminal or
editor disconnect; a WSL shutdown still requires a checkpoint-based resume.

From the repository, attach to the most recently updated experiment:

```bash
bash scripts/progress.sh
```

The same command is available as the VS Code task **Research: attach live
progress**. It prints saved status and completion counts, then follows the log.
It never launches evaluations. A completed run has no further progress events.
Use an explicit directory to inspect another run:

```bash
bash scripts/progress.sh results/evolution/20260915T101024.562418Z-search
tail -n 30 -F results/operations/recovery_20260916/comparison-terminal.log
```

If the comparison is interrupted and its controller has exited, this command
validates the frozen sources and configuration and skips every saved method case:

```bash
.venv/bin/python -u scripts/run_comparison.py \
  --run results/comparison/20260916T001949Z-frozen --resume \
  --figures assets/comparison
```

There is no reason to restart the already completed evolution controller. For a
different unfinished evolution run, use the existing `--resume` launcher with
that run's original target and saved settings; see [native execution](shinkaevolve.md).

## Native WebUI

The restored native ShinkaEvolve WebUI serves the original database at
[http://localhost:8888](http://localhost:8888). If it stops, launch it with:

```bash
bash scripts/webui.sh results/evolution/20260915T101024.562418Z-search 8888
```

Use only one server on that port. The portable published copy is also viewable:

```bash
bash scripts/webui.sh artifacts/evolution/20260915T101024.562418Z-search 8888
```

Browser verification exercised the dashboard, ancestry tree, program list and
selected program source. The dashboard showed all 21 rows and 20 generations.
No browser page errors occurred; a native Plotly deprecation warning was retained
in the verification record. Its cost widgets are native API-equivalent accounting estimates, not evidence of
paid API use. Historical mutation calls used the subscription Headless Codex
route; saved inner effort was unspecified. Recovery and comparison required no
new mutation calls. The outer supervising mode and inner mutation settings are
separate, and no setting was relabelled.

Operational PID records, launch commands, persistent logs, database backup and
verification screenshots remain under `results/operations/recovery_20260916/`.
PIDs are historical identifiers and must be checked against current processes
before taking action.
