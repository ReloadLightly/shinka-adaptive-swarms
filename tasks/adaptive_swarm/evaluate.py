"""Native Shinka evaluator for response policies in a fixed Moving Peaks model."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import statistics
import sys
import traceback
from pathlib import Path

ROOT = Path(os.environ.get("ADAPTIVE_SWARMS_PROJECT_ROOT", Path(__file__).resolve().parents[2])).resolve()
sys.path.insert(0, str(ROOT / "src"))

from adaptive_swarms.logging import EventLogger
from adaptive_swarms.simulator import run_case

EVALUATION_VERSION = "search_v1_score_reciprocal"
FEEDBACK_VERSION = "tracking_diagnostics_v1"


def load_policy(program_path: Path):
    spec = importlib.util.spec_from_file_location("candidate_response", program_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load candidate: {program_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    policy = getattr(module, "choose_response", None)
    if not callable(policy):
        raise ValueError("Candidate must define choose_response(observation).")
    return policy


def load_cases(suite_path: Path) -> list[dict]:
    suite = json.loads(suite_path.read_text())
    # Both an explicit case list and a manifest with shared defaults are useful.
    if isinstance(suite, list):
        cases = suite
    else:
        defaults = suite.get("base", suite.get("defaults"))
        if defaults is None:
            defaults = {key: value for key, value in suite.items() if key not in {"cases", "study", "description"}}
        cases = [{**defaults, **case} for case in suite["cases"]]
    if not cases:
        raise ValueError("Evaluation suite contains no cases.")
    return cases


def case_diagnostics(result: dict) -> dict:
    """Behavior summaries from already-measured simulator evidence."""
    counts = result["evaluation_counts"]
    total = max(1, sum(counts.values()))
    responses = result["response_log"]
    ends = [float(item["environment_final_error"]) for item in result["environment_changes"]]
    config = result["config"]
    return {
        "regime": f"{config['dimension']}D, {config['npeaks']} peaks, move severity {config['move_severity']}, interval {config['period']} evaluations",
        "mean_interval_end_error": statistics.mean(ends) if ends else None,
        "detection_evaluation_share": counts.get("detection", 0) / total,
        "memory_evaluation_share": counts.get("memory", 0) / total,
        "mean_response_radius": statistics.mean(item["radius"] for item in responses) if responses else None,
        "mean_relocation_fraction": statistics.mean(item["decision"]["fraction"] for item in responses) if responses else None,
        "response_count": len(responses),
    }


def describe_case(case: dict) -> str:
    def fmt(value):
        return "not observed" if value is None else f"{value:.6g}"
    return (
        f"{case['case_id']} ({case['regime']}): offline error {case['offline_error']:.6f}; "
        f"mean error remaining at interval end {fmt(case['mean_interval_end_error'])}; "
        f"detection used {case['detection_evaluation_share']:.2%} and memory refresh "
        f"{case['memory_evaluation_share']:.2%} of objective evaluations; "
        f"{case['response_count']} responses with mean radius {fmt(case['mean_response_radius'])} "
        f"and relocated fraction {fmt(case['mean_relocation_fraction'])}"
    )


def evaluate(program_path: Path, results_dir: Path, suite_path: Path) -> int:
    results_dir.mkdir(parents=True, exist_ok=True)
    outcomes = []
    error = ""
    metrics = {"combined_score": 0.0, "public": {}, "private": {"evaluation_version": EVALUATION_VERSION}}
    with EventLogger(results_dir, heartbeat_seconds=20) as log:
        try:
            log.set_activity("loading candidate and evaluation cases")
            cases = load_cases(suite_path)
            log.event("evaluation_start", message="Executing candidate in the fixed simulator", cases=len(cases))
            for index, config in enumerate(cases):
                # A fresh module isolates any policy memory across independent cases,
                # matching the comparison CLI's treatment of candidate state.
                policy = load_policy(program_path)
                config = dict(config)
                case_id = str(config.pop("case_id", config.pop("id", f"case_{index:03d}")))
                config.pop("name", None)
                log.set_activity(f"evaluating {case_id} ({index + 1}/{len(cases)})")
                log.event("case_start", message=f"Evaluating {case_id}", case_id=case_id, index=index + 1, total=len(cases), config=config)

                def progress(event, case_id=case_id):
                    event = dict(event)
                    phase = event.pop("phase", event.pop("event", "simulation_progress"))
                    message = event.pop("message", f"{case_id}: {phase}")
                    event.pop("case_id", None)
                    log.event(phase, message=message, case_id=case_id, **event)

                result = run_case(config, policy=policy, progress=progress)
                offline_error = float(result["offline_error"])
                if not math.isfinite(offline_error) or offline_error < 0:
                    raise ValueError(f"Invalid offline error for {case_id}: {offline_error}")
                # Retain scientific traces rather than reducing the experiment to its score.
                artifact = results_dir / f"case_{index:03d}.json"
                artifact.write_text(json.dumps({"case_id": case_id, **result}, indent=2, allow_nan=False))
                outcomes.append({"case_id": case_id, "offline_error": offline_error, "artifact": artifact.name, **case_diagnostics(result)})
                log.event("case_complete", message=f"{case_id} complete", case_id=case_id, offline_error=offline_error)
            errors = [case["offline_error"] for case in outcomes]
            mean_error = statistics.mean(errors)
            worst = max(outcomes, key=lambda case: case["offline_error"])
            metrics = {
                "combined_score": 1.0 / (1.0 + mean_error),
                "public": {
                    "mean_offline_error": mean_error,
                    "worst_case_offline_error": max(errors),
                    "case_error_std": statistics.stdev(errors) if len(errors) > 1 else 0.0,
                    "cases_completed": len(outcomes),
                },
                "private": {"cases": outcomes, "suite_sha256": hashlib.sha256(suite_path.read_bytes()).hexdigest(), "evaluation_version": EVALUATION_VERSION, "feedback_version": FEEDBACK_VERSION},
                "text_feedback": (
                    "Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. "
                    + ". ".join(describe_case(case) for case in outcomes)
                    + f". Largest tracking error: {worst['case_id']}. Examine relocation radius, "
                    "fraction, and memory response to observable change severity. Large interval-end "
                    "errors indicate tracking still missed by the next change, while detection and "
                    "memory shares expose objective-evaluation overhead. These diagnostics describe "
                    "behavior and do not by themselves prove its cause. Improvements must "
                    "preserve the fixed simulator and objective-evaluation budget. These are search "
                    "results; generalization requires separate comparison cases."
                ),
            }
            log.event("evaluation_complete", message="Candidate evaluation complete", **metrics["public"])
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            metrics["private"].update({"error": error, "cases": outcomes})
            metrics["text_feedback"] = "Candidate evaluation failed: " + error
            (results_dir / "error.txt").write_text(traceback.format_exc())
            log.event("evaluation_failed", message=error, cases_completed=len(outcomes))
        finally:
            (results_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, allow_nan=False))
            (results_dir / "correct.json").write_text(json.dumps({"correct": not error, "error": error}, indent=2))
    return 1 if error else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--program_path", type=Path, required=True)
    parser.add_argument("--results_dir", type=Path, required=True)
    parser.add_argument("--suite", type=Path, default=ROOT / "configs" / "search.json")
    args = parser.parse_args()
    return evaluate(args.program_path.resolve(), args.results_dir.resolve(), args.suite.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
