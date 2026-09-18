#!/usr/bin/env python3
"""Continue authorized v2 windows, preserving every controller admission gate."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cooperative.native import atomic_json
from scripts.paper_review_target import review_target, review_reached, review_reason, set_review_target

SEARCH = ROOT / "results/paper_trajectory_v2/search"
MANIFEST = ROOT / "campaigns/paper_trajectory_v2.json"
STATE = SEARCH / "operations/continuation-windows.json"
COMMAND = [str(ROOT / ".venv/bin/python"), str(ROOT / "scripts/paper_campaign.py"),
           "resume", "--session-minutes", "900", "--workers", "1"]


def stop_reason(manifest):
    for name in ("subscription-pause.json", "infrastructure-pause.json",
                 "provider-infrastructure-pause.json", "recovery-pending.json"):
        if (SEARCH / name).exists():
            return "Preserved pause: " + name
    if manifest.get("active_batch"):
        return "Controller exited with an unresolved active batch; inspect before resuming"
    if manifest.get("native_batches", []) and manifest["native_batches"][-1]["returncode"]:
        return "Last native batch failed; inspect its receipt before resuming"
    if review_reached(manifest['accounting'], SEARCH):
        return review_reason(SEARCH)
    if (SEARCH / 'pause-request.json').exists():
        return 'Preserved pause: pause-request.json'
    return None


def document_checkpoint(manifest, phase, reason=None):
    accounting = manifest["accounting"]
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    state = {"recorded_at_utc": now, "supervisor_pid": os.getpid(), "phase": phase,
             "operational_review_target": review_target(SEARCH), "campaign_proposal_ceiling": 50,
             "reason": reason, "command": COMMAND,
             "terminal_slots": accounting["terminal_slots"],
             "valid_descendants": accounting["valid_descendants"],
             "remaining_descendant_slots": accounting["remaining_descendant_slots"],
             "model_responses": accounting["model_responses"],
             "logical_completed_model_responses": accounting["logical_completed_model_responses"],
             "numerical": accounting["numerical"], "publication": manifest.get("publication")}
    atomic_json(STATE, state)
    used = 50 - accounting["remaining_descendant_slots"]
    best = accounting.get("database", {})
    summary = (f"**Latest supervised checkpoint ({now}): {phase}.** "
               f"{used}/50 descendant proposal slots consumed; "
               f"{accounting['valid_descendants']} valid descendants; "
               f"{accounting['remaining_descendant_slots']} slots remain. "
               f"Best development program: generation {best.get('best_generation')}, "
               f"scaled score {best.get('best_score')}. "
               f"Native-returned model responses: {accounting['model_responses']}; "
               f"observed logical completions including the archived late reply: "
               f"{accounting['logical_completed_model_responses']}. "
               f"Completed physical trajectories: {accounting['numerical']['completed_physical_trajectories']:,}; "
               f"evaluator invocations: {accounting['numerical']['evaluation_invocations']}; "
               f"exact-cache reuses: {accounting['numerical']['exact_cache_reuses']}. "
               "All evaluations retain the frozen 288-condition panel. "
               "These remain development results; fresh confirmation and full-paper reproduction are unfinished.")
    if reason:
        summary += " Pause reason: " + reason + "."
    start = "<!-- V2_CONTINUATION_STATUS_START -->"
    end = "<!-- V2_CONTINUATION_STATUS_END -->"
    for relative in ("README.md", "docs/NEXT_SESSION.md"):
        path = ROOT / relative
        content = path.read_text()
        if start not in content or end not in content:
            raise RuntimeError("Missing continuation status markers in " + relative)
        before, rest = content.split(start, 1)
        _, after = rest.split(end, 1)
        path.write_text(before + start + "\n" + summary + "\n" + end + after)
    print(json.dumps({key: state[key] for key in
                      ("recorded_at_utc", "phase", "reason", "valid_descendants",
                       "remaining_descendant_slots", "model_responses", "numerical")}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wait-for-controller", type=int)
    parser.add_argument("--review-target", type=int,
                        help="Explicitly change the operational review target after the current controller drains")
    args = parser.parse_args()
    # This lock prevents duplicate supervisors; the unchanged controller still
    # acquires the campaign's scientific/SQLite lock for every actual window.
    with (ROOT / "campaigns/paper_trajectory_v2.windows.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.wait_for_controller:
            import psutil
            process = psutil.Process(args.wait_for_controller)
            command = process.cmdline()
            if "resume" not in command or not any(arg.endswith("scripts/paper_campaign.py") for arg in command):
                raise RuntimeError("Wait target is not the authorized discovery controller")
            atomic_json(STATE, {"supervisor_pid": os.getpid(), "phase": "waiting_for_current_window",
                               "controller_pid": process.pid, "controller_created_at": process.create_time(),
                               "command": COMMAND})
            process.wait()
        if args.review_target is not None:
            with (ROOT / "campaigns/paper_trajectory_v2.lock").open("a+") as campaign_lock:
                fcntl.flock(campaign_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                set_review_target(args.review_target, SEARCH)
        while True:
            manifest = json.loads(MANIFEST.read_text())
            reason = stop_reason(manifest)
            if reason:
                review = reason == review_reason(SEARCH)
                document_checkpoint(manifest, "paused_for_review" if review else "paused", reason)
                return 0 if review else 1
            if manifest["accounting"]["remaining_descendant_slots"] == 0:
                document_checkpoint(manifest, "discovery_complete")
                return 0
            document_checkpoint(manifest, "continuing")
            before = manifest["accounting"]["terminal_slots"]
            result = subprocess.run(COMMAND, cwd=ROOT)
            manifest = json.loads(MANIFEST.read_text())
            if result.returncode:
                document_checkpoint(manifest, "paused", f"Controller exit {result.returncode}")
                return result.returncode
            if (manifest["accounting"]["terminal_slots"] == before
                    and not manifest.get("admission_pause") and not stop_reason(manifest)):
                document_checkpoint(manifest, "paused", "Controller returned without progress or a recorded admission boundary")
                return 1


if __name__ == "__main__":
    raise SystemExit(main())
