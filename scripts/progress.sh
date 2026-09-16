#!/usr/bin/env bash
# Attach to saved progress without starting another experiment controller.
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"
python_bin="${project_root}/.venv/bin/python"
if [[ ! -x "$python_bin" ]]; then python_bin="python3"; fi
run_dir="${1:-}"
if [[ -z "$run_dir" ]]; then
  run_dir="$("$python_bin" - <<'PY'
from pathlib import Path
roots = [Path("results") / kind for kind in ("comparison", "evolution")]
roots.append(Path("results/relocation_allocation_v2"))
roots.append(Path("results/joint_relocation_v3"))
paths = [p for root in roots for p in root.rglob("manifest.json")
         if (p.parent / "run.log").exists()]
if not paths:
    raise SystemExit("No saved experiment log found; pass a run directory.")
print(max(paths, key=lambda p: p.stat().st_mtime_ns).parent)
PY
)"
fi
"$python_bin" - "$run_dir" <<'PY'
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
folder = Path(sys.argv[1])
manifest = json.loads((folder / "manifest.json").read_text())
now = datetime.now(timezone.utc).isoformat(timespec="seconds")
print(f"[{now}] Attaching to {folder}; saved status={manifest.get('status', 'unknown')}", flush=True)
summary_path = folder / "summary.json"
if summary_path.exists():
    summary = json.loads(summary_path.read_text())
    if "unique_executed_method_cases" in summary:
        print(f"Stage: {summary['stage']}; paired cases: {summary['case_count']}; "
              f"distinct executions: {summary['unique_executed_method_cases']}; "
              f"identical-method aliases: {len(summary['aliases'])}", flush=True)
        print(f"Mean offline errors: {json.dumps(summary['method_mean_offline_errors'], sort_keys=True)}", flush=True)
    else:
        print(f"Completed method cases: {summary.get('completed_method_cases')}; "
              f"paired cases: {summary.get('paired_case_count')}/{summary.get('planned_case_count')}", flush=True)
elif "completed_method_cases" in manifest:
    print(f"Completed cases per method: {json.dumps(manifest['completed_method_cases'], sort_keys=True)}", flush=True)
elif "latest_summary" in manifest:
    print(json.dumps(manifest["latest_summary"], sort_keys=True), flush=True)
print("Following timestamped saved output. A completed run produces no new events. Ctrl-C detaches.", flush=True)
PY
logs=("$run_dir/run.log")
if [[ -f "$run_dir/evolution_run.log" ]]; then
  logs+=("$run_dir/evolution_run.log")
fi
exec tail -n 25 -F -- "${logs[@]}"
