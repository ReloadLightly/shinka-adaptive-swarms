"""Operational review boundary; deliberately separate from the frozen experiment."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import time

from cooperative.native import atomic_json

ROOT = Path(__file__).resolve().parents[1]
SEARCH = ROOT / "results/paper_trajectory_v2/search"


def review_target(search=SEARCH):
    path = search / "review-target.json"
    target = json.loads(path.read_text())["generation"] if path.exists() else 50
    if type(target) is not int or not 1 <= target <= 50:
        raise RuntimeError("Invalid operational review target; refusing admission")
    return target


def review_reached(accounting, search=SEARCH):
    target = review_target(search)
    return target < 50 and set(range(1, target + 1)) <= set(accounting["terminal_slots"])


def review_reason(search=SEARCH):
    return f"paused for generation-{review_target(search)} review"


def set_review_target(target, search=SEARCH):
    """Call only under the campaign lock, after accepted work has drained."""
    if type(target) is not int or not 1 <= target <= 50:
        raise ValueError("Review target must be an integer from 1 through 50")
    old = review_target(search)
    pause = search / "pause-request.json"
    if pause.exists():
        receipt = json.loads(pause.read_text())
        if receipt.get("kind") != "generation_review" or receipt.get('generation') != old or target <= old:
            raise RuntimeError("Preserved pause cannot be cleared by this review-target change")
        archive = search / "operations/review-pauses" / f"{time.time_ns()}.json"
        atomic_json(archive, receipt)
        pause.unlink()
    previous = search / "review-target.json"
    if previous.exists() and old != target:
        atomic_json(search / "operations/review-targets" / f"{time.time_ns()}.json",
                    json.loads(previous.read_text()))
    atomic_json(previous, {"schema": "paper-operational-review-target-v1",
                          "generation": target, "campaign_proposal_ceiling": 50,
                          "reason": f"Pause after proposal slot {target}; retain failed/rejected slot accounting",
                          "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                          "authority": "Explicit user generation review instruction"})


def record_review_pause(accounting, search=SEARCH):
    if not review_reached(accounting, search):
        return None
    target = review_target(search)
    receipt = {"kind": "generation_review", "reason": review_reason(search),
               "generation": target, "campaign_proposal_ceiling": 50,
               "terminal_slots": accounting["terminal_slots"],
               "overshoot_slots": [g for g in accounting["terminal_slots"] if g > target],
               "recorded_at_utc": datetime.now(timezone.utc).isoformat()}
    path = search / "pause-request.json"
    if not path.exists():
        atomic_json(path, receipt)
    return receipt
