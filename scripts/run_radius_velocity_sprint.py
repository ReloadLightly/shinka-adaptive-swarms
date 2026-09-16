#!/usr/bin/env python3
"""Small checkpointed diagnostic/pilot runner; never launches model calls."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from adaptive_swarms.artifacts import read_json, write_compressed_json
from adaptive_swarms.cli import simulator_fingerprint
from adaptive_swarms.comparison import validate_pair
from adaptive_swarms.joint_relocation import load_joint_policy, joint_policy_adapter, annotate_joint_log
from adaptive_swarms.logging import EventLogger, atomic_json
from adaptive_swarms.recovery_response import load_recovery_policy, recovery_policy_adapter, annotate_recovery_log, recovery_fingerprint
from adaptive_swarms.simulator import run_case, _validated_config


METHODS = {
    "c4_r1_retain": (1.0, False), "c4_r1p5_retain": (1.5, False),
    "c4_r1_reset": (1.0, True), "c4_r1p5_reset": (1.5, True),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def initialize(folder):
    if (folder / "phase_a/manifest.json").exists():
        raise FileExistsError("Phase A is already registered; run reuses completed cases.")
    old = ROOT / "artifacts/joint_relocation_v3/study_20260916"
    source_cases = read_json(old / "search_cases.json")["cases"]
    indices = [0, 1, 4, 5, 8, 9, 12, 13]
    cases = [_validated_config({**source_cases[i], "trace_interval": 25}) for i in indices]
    programs = folder / "programs"
    programs.mkdir(exist_ok=True)
    methods = {}
    for name, (radius, reset) in METHODS.items():
        path = programs / f"{name}.py"
        source = ('"""Count-four recovery policy; memory reevaluation is fixed by the adapter."""\n\n'
                  '# EVOLVE-BLOCK-START\ndef choose_recovery(observation: dict) -> dict:\n'
                  f'    return {{"radius_scale": {radius!r}, "reset_velocity": {reset!r}}}\n'
                  '# EVOLVE-BLOCK-END\n')
        with path.open("x") as stream:
            stream.write(source)
        methods[name] = {"kind": "recovery", "source": f"programs/{name}.py", "sha256": sha(path),
                         "radius_scale": radius, "reset_velocity": reset, "count": 4}
    methods["baseline"] = {"kind": "baseline", "source": None, "count": 5,
                           "radius_scale": 1.0, "reset_velocity": False}
    historical = old / "programs/acefdf34161e9e666deb778e914d0e3287e74a42642946513cc93ceb73a467ec.py"
    historical_copy = programs / "v3_selected.py"
    assert sha(historical) == historical.stem
    shutil.copyfile(historical, historical_copy)
    methods["v3_selected"] = {"kind": "joint", "source": "programs/v3_selected.py",
                               "sha256": sha(historical_copy), "historical_source": str(historical.relative_to(ROOT))}
    manifest = {"schema": "radius-velocity-sprint-stage-v1", "stage": "phase_a",
                "created_at": datetime.now(timezone.utc).isoformat(), "cases": cases, "methods": methods,
                "source_case_indices": indices, "source_case_manifest": str(old / "search_cases.json"),
                "source_case_manifest_sha256": sha(old / "search_cases.json"),
                "scientific_sources": recovery_fingerprint(), "simulator_sources": simulator_fingerprint(),
                "maximum_new_executions": 48, "trace_note": "Dense interval25; historical interval500 is not an exact observational-cache match."}
    atomic_json(folder / "phase_a/manifest.json", manifest)
    atomic_json(folder / "operations/manifest.json", {"status": "running", "study": "radius_velocity_sprint", "session": "../session.json"})
    print(json.dumps({"status": "registered", "stage": "phase_a", "cases": len(cases), "methods": list(methods)}, indent=2))


def execute(folder, stage, max_new_cases=None):
    stage_dir = folder / stage
    manifest = read_json(stage_dir / "manifest.json")
    if manifest["scientific_sources"] != recovery_fingerprint():
        raise ValueError("Scientific sources changed after stage registration.")
    for method in manifest["methods"].values():
        if method["source"] and sha(folder / method["source"]) != method["sha256"]:
            raise ValueError("Frozen method source changed.")
    session = read_json(folder / "session.json")
    deadline = datetime.fromisoformat(session["deadline_utc"])
    ledger_path = stage_dir / "execution_ledger.json"
    ledger = read_json(ledger_path) if ledger_path.exists() else {"attempts": [], "status": "registered"}
    new_count = 0
    with (stage_dir / "controller.lock").open("a") as lock, EventLogger(stage_dir) as log:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with EventLogger(folder / "operations") as operations:
            for i, config in enumerate(manifest["cases"]):
                reference = None
                for name, method in manifest["methods"].items():
                    path = stage_dir / name / f"case_{i:03d}.json.gz"
                    if path.exists():
                        saved = read_json(path)
                        assert saved["config"] == config and saved["evaluations"] == config["budget"]
                        validate_pair(saved, saved)
                        completed = [a for a in ledger["attempts"] if a["method"] == name and a["case_index"] == i and a["status"] == "completed"]
                        assert len(completed) == 1 and completed[0]["artifact_sha256"] == sha(path)
                        log.event("case_reused", method=name, case_index=i, artifact=str(path))
                        if reference is None: reference = saved
                        else: validate_pair(reference, saved)
                        continue
                    if max_new_cases is not None and new_count >= max_new_cases:
                        log.event("paused_after_measurement", new_executions=new_count)
                        return
                    if datetime.now(timezone.utc) >= deadline:
                        raise TimeoutError("Sprint elapsed-time ceiling reached before new case.")
                    if any(a["method"] == name and a["case_index"] == i for a in ledger["attempts"]):
                        raise RuntimeError("Unfinished/failed attempted case requires explicit recovery review; no automatic repeat.")
                    if len(ledger["attempts"]) >= manifest["maximum_new_executions"]:
                        raise RuntimeError("Stage execution ceiling exhausted.")
                    attempt = {"method": name, "case_index": i, "status": "running",
                               "started_at": datetime.now(timezone.utc).isoformat(), "reserved_queries": config["budget"],
                               "last_reported_queries": 0, "artifact": str(path.relative_to(folder))}
                    ledger["attempts"].append(attempt)
                    ledger["status"] = "running"
                    atomic_json(ledger_path, ledger)
                    start = time.monotonic()
                    log.set_activity(f"{stage} {name} case {i + 1}/8")
                    log.event("case_start", method=name, case_index=i, budget=config["budget"])
                    operations.event("case_start", stage=stage, method=name, case_index=i, completed=len(ledger["attempts"])-1)

                    def progress(event):
                        queries = event.get("evaluations", 0)
                        attempt["last_reported_queries"] = max(attempt["last_reported_queries"], queries)
                        if event.get("event") == "progress":
                            atomic_json(ledger_path, ledger)
                            log.event("case_progress", method=name, case_index=i, evaluations=queries)

                    try:
                        if method["kind"] == "recovery":
                            policy = recovery_policy_adapter(load_recovery_policy(folder / method["source"]))
                            result = annotate_recovery_log(run_case(config, policy, progress), policy)
                        elif method["kind"] == "joint":
                            policy = joint_policy_adapter(load_joint_policy(folder / method["source"]))
                            result = annotate_joint_log(run_case(config, policy, progress), policy)
                        elif method["kind"] == "baseline":
                            result = run_case(config, progress=progress)
                        else:
                            raise ValueError("Unknown frozen method kind")
                        validate_pair(result, result)
                        if reference is None: reference = result
                        else: validate_pair(reference, result)
                        write_compressed_json(path, {"case_id": f"case_{i:03d}", **result})
                        attempt.update(status="completed", completed_at=datetime.now(timezone.utc).isoformat(),
                                       actual_queries=result["evaluations"], offline_error=result["offline_error"],
                                       elapsed_seconds=time.monotonic()-start, artifact_sha256=sha(path))
                        new_count += 1
                        atomic_json(ledger_path, ledger)
                        log.event("case_complete", method=name, case_index=i, offline_error=result["offline_error"], elapsed_seconds=attempt["elapsed_seconds"], completed=len(ledger["attempts"]))
                        operations.event("case_complete", stage=stage, method=name, case_index=i, offline_error=result["offline_error"], elapsed_seconds=attempt["elapsed_seconds"], completed=len(ledger["attempts"]))
                    except BaseException as exc:
                        attempt.update(status="failed_or_interrupted", error=f"{type(exc).__name__}: {exc}", elapsed_seconds=time.monotonic()-start,
                                       accounting_note="Full requested budget remains reserved; exact partial query count is unavailable beyond last progress event.")
                        atomic_json(ledger_path, ledger)
                        (stage_dir / "error.txt").write_text(traceback.format_exc())
                        raise
            ledger.update(status="completed", completed_at=datetime.now(timezone.utc).isoformat())
            atomic_json(ledger_path, ledger)
            operations.event("stage_complete", stage=stage, new_executions=sum(a["status"] == "completed" for a in ledger["attempts"]), objective_queries=sum(a.get("actual_queries", 0) for a in ledger["attempts"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["init", "run"])
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--stage", choices=["phase_a", "pilot"], default="phase_a")
    parser.add_argument("--max-new-cases", type=int)
    args = parser.parse_args()
    if args.command == "init": initialize(args.run.resolve())
    else: execute(args.run.resolve(), args.stage, args.max_new_cases)
