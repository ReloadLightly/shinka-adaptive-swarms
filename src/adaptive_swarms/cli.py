"""Research command line: cases are checkpointed and progress is flushed live."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time

from .logging import EventLogger, atomic_json


def run_id(prefix):
    return f"{prefix}_{datetime.now(timezone.utc):%Y%m%dT%H%M%S_%fZ}"


def source_revision():
    p = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else "uncommitted-initial-build"


def simulator_fingerprint():
    root = Path(__file__).resolve().parents[2]
    inputs = [root / "src/adaptive_swarms/simulator.py", root / "src/adaptive_swarms/policies.py",
              root / "vendor/deap/movingpeaks.py"]
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}


def load_policy(path):
    if not path:
        return None
    spec = importlib.util.spec_from_file_location("candidate_policy", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, "choose_response", None)):
        raise ValueError("Candidate must define choose_response(observation)")
    return module.choose_response


def baseline(args):
    from .simulator import run_case
    config = json.loads(Path(args.config).read_text())
    if args.budget is not None:
        config["budget"] = args.budget
    cases = config.pop("cases", [{}])
    study = config.pop("study", "baseline")
    folder = Path(args.run or (Path("results") / run_id(study)))
    if (folder / "manifest.json").exists() and not args.resume:
        raise SystemExit(f"Existing run at {folder}; use --resume to continue matching saved cases.")
    policy_source = Path(args.policy).read_text() if args.policy else "corrected_book_baseline"
    fingerprint = simulator_fingerprint()
    signature = hashlib.sha256(json.dumps({"config": config, "cases": cases,
                                         "policy_source": policy_source, "simulator_sources": fingerprint}, sort_keys=True).encode()).hexdigest()
    manifest_file = folder / "manifest.json"
    if manifest_file.exists():
        saved = json.loads(manifest_file.read_text())
        if saved["signature"] != signature:
            raise SystemExit("Resume configuration/policy differs from saved run; choose a new run directory.")
    folder.mkdir(parents=True, exist_ok=True)
    if manifest_file.exists():
        manifest = json.loads(manifest_file.read_text())
        manifest["status"] = "running"
        manifest.setdefault("continuations", []).append({"source_revision": source_revision(),
                   "time": datetime.now(timezone.utc).isoformat()})
    else:
        manifest = {"study": study, "signature": signature, "config": config,
                               "cases": cases, "policy": args.policy or "baseline",
                               "source_revision": source_revision(), "python": platform.python_version(),
                               "simulator_sources": fingerprint, "status": "running"}
    atomic_json(manifest_file, manifest)
    if args.policy:
        (folder / "policy.py").write_text(policy_source)
    outcomes = []
    try:
        with EventLogger(folder) as log:
            log.event("study_started", study=study, cases=len(cases), budget_per_case=config.get("budget"),
                      policy=args.policy or "corrected baseline", directory=str(folder))
            for idx, overrides in enumerate(cases):
                case_file = folder / f"case_{idx:03d}.json"
                if args.resume and case_file.exists():
                    result = json.loads(case_file.read_text())
                    if result.get("signature") != signature:
                        raise ValueError(f"Saved case provenance does not match this run: {case_file}")
                    outcomes.append(result)
                    log.event("case_reused", case=idx + 1, offline_error=result["offline_error"])
                    continue
                merged = {**config, **overrides}
                log.set_activity(f"simulating case {idx+1}/{len(cases)}")
                log.event("case_started", case=idx + 1, total_cases=len(cases), **overrides)
                def progress(event):
                    event = dict(event)
                    kind = event.pop("event", "simulation_progress")
                    log.event(kind, case_index=idx + 1, **event)
                start = time.monotonic()
                result = run_case(merged, policy=load_policy(args.policy), progress=progress)
                result["wall_time_seconds"] = time.monotonic()-start
                result["signature"] = signature
                result["policy_source_sha256"] = hashlib.sha256(policy_source.encode()).hexdigest()
                atomic_json(case_file, result)
                outcomes.append(result)
                log.event("case_completed", case=idx + 1, offline_error=result["offline_error"],
                          wall_time_s=result["wall_time_seconds"], checkpoint=str(case_file))
            values = [r["offline_error"] for r in outcomes]
            summary = {"study": study, "status": "completed", "case_count": len(values),
                       "mean_offline_error": statistics.mean(values),
                       "sd_offline_error": statistics.stdev(values) if len(values)>1 else None,
                       "offline_errors": values, "model_calls": 0,
                       "policy": args.policy or "baseline",
                       "note": "Single-policy measurements; evolutionary provenance and improvement require an explicit comparison."}
            atomic_json(folder / "summary.json", summary)
            manifest = json.loads(manifest_file.read_text())
            manifest["status"] = "completed"
            atomic_json(manifest_file, manifest)
            log.event("study_completed", **summary)
    except BaseException:
        manifest = json.loads(manifest_file.read_text())
        manifest["status"] = "interrupted_or_failed"
        manifest["completed_cases"] = len(outcomes)
        atomic_json(manifest_file, manifest)
        raise
    print(f"\nSaved run: {folder}\nFigures: python -m adaptive_swarms figures --run {folder}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("baseline", help="Run corrected baseline or a supplied policy on a suite")
    run.add_argument("--config", default="configs/reproduction.json")
    run.add_argument("--run", help="New output folder; otherwise timestamped")
    run.add_argument("--resume", action="store_true")
    run.add_argument("--budget", type=int, help="Explicit override; saved in manifest")
    run.add_argument("--policy", help="Candidate Python file with choose_response")
    run.set_defaults(func=baseline)
    plots = commands.add_parser("figures", help="Render research figures from a completed run")
    plots.add_argument("--run", required=True)
    plots.add_argument("--output", help="Default is <run>/figures")
    def figures(args):
        from .figures import render_run
        render_run(Path(args.run), Path(args.output) if args.output else None)
    plots.set_defaults(func=figures)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
