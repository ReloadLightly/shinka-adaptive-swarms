"""Native Shinka evaluator for v2 integer relocation allocation."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import statistics
import sys
import traceback
from pathlib import Path

ROOT = Path(os.environ.get("ADAPTIVE_SWARMS_PROJECT_ROOT", Path(__file__).resolve().parents[2])).resolve()
sys.path.insert(0, str(ROOT / "src"))

from adaptive_swarms.logging import EventLogger, atomic_json
from adaptive_swarms.simulator import run_case, _validated_config
from adaptive_swarms.artifacts import case_artifacts, read_json, resolve_json, write_compressed_json
from adaptive_swarms.relocation_allocation import (allocation_fingerprint, load_count_policy,
    count_policy_adapter, annotate_count_log, count_diagnostics)
from adaptive_swarms.execution import InfrastructureError, INFRASTRUCTURE_EXIT_CODE

EVALUATION_VERSION = "relocation_allocation_v2_score_reciprocal"
FEEDBACK_VERSION = "allocation_tracking_diagnostics_v2"
STORAGE_VERSION = "streaming_gzip_case_checkpoint_v1"


def load_policy(program_path: Path):
    return count_policy_adapter(load_count_policy(program_path))


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
        **count_diagnostics(result),
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
        f"and relocated fraction {fmt(case['mean_relocation_fraction'])}; "
        f"requested counts {json.dumps(case['requested_count_distribution'], sort_keys=True)}, "
        f"executed counts {json.dumps(case['executed_count_distribution'], sort_keys=True)}; "
        f"{case['incomplete_responses']} horizon-truncated responses; "
        f"counts with objective queries {json.dumps(case['evaluated_relocation_count_distribution'], sort_keys=True)}"
    )


def evaluation_identity(program_path: Path, suite_path: Path) -> dict:
    return {"program_sha256": hashlib.sha256(program_path.read_bytes()).hexdigest(),
            "suite_sha256": hashlib.sha256(suite_path.read_bytes()).hexdigest(),
            "evaluation_version": EVALUATION_VERSION, "feedback_version": FEEDBACK_VERSION,
            "scientific_sources": allocation_fingerprint()}


def validate_saved_case(result: dict, config: dict, case_id: str, artifact: Path):
    if result.get("case_id") != case_id or result.get("config") != _validated_config(config):
        raise ValueError(f"Saved case inputs differ: {artifact}")
    budget = result["config"]["budget"]
    if result.get("evaluations") != budget or sum(result["evaluation_counts"].values()) != budget:
        raise ValueError(f"Incomplete objective budget in saved case: {artifact}")
    error = float(result["offline_error"])
    if not math.isfinite(error) or error < 0:
        raise ValueError(f"Invalid saved offline error: {artifact}")


def prepare_checkpoint(program_path: Path, results_dir: Path, suite_path: Path) -> dict:
    identity = evaluation_identity(program_path, suite_path)
    path = results_dir / "evaluation-checkpoint.json"
    if path.exists():
        checkpoint = read_json(path)
        if checkpoint["identity"] != identity:
            raise ValueError("Evaluation checkpoint candidate, suite, or scientific sources differ.")
        return checkpoint
    existing = case_artifacts(results_dir)
    legacy = False
    if existing:
        # Legacy native generations retain immutable main.py beside results,
        # with suite/version evidence in either metrics or the run manifest.
        source = results_dir.parent / "main.py"
        if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest() != identity["program_sha256"]:
            raise ValueError("Cannot establish legacy case candidate provenance.")
        metrics_path = results_dir / "metrics.json"
        manifest_path = results_dir.parent.parent / "manifest.json"
        evidence = read_json(metrics_path).get("private", {}) if metrics_path.exists() else (
            read_json(manifest_path) if manifest_path.exists() else {})
        if any(evidence.get(key) != identity[key] for key in ("suite_sha256", "evaluation_version")):
            raise ValueError("Cannot establish legacy case suite/evaluator provenance.")
        legacy = True
    checkpoint = {"storage_version": STORAGE_VERSION, "identity": identity,
                  "status": "running", "completed_cases": [], "legacy_cases_reused": legacy}
    atomic_json(path, checkpoint)
    return checkpoint


def _evaluate(program_path: Path, results_dir: Path, suite_path: Path) -> int:
    results_dir.mkdir(parents=True, exist_ok=True)
    # Provenance errors occur before the scientific failure handler, preventing
    # an unrelated candidate from overwriting completed experimental evidence.
    checkpoint = prepare_checkpoint(program_path, results_dir, suite_path)
    checkpoint_path = results_dir / "evaluation-checkpoint.json"
    cases = load_cases(suite_path)
    for index, saved_config in enumerate(cases):
        config = dict(saved_config)
        case_id = str(config.pop("case_id", config.pop("id", f"case_{index:03d}")))
        config.pop("name", None)
        artifact = resolve_json(results_dir / f"case_{index:03d}.json")
        if artifact.exists():
            validate_saved_case(read_json(artifact), config, case_id, artifact)
    outcomes = []
    error = ""
    metrics = {"combined_score": 0.0, "public": {}, "private": {"evaluation_version": EVALUATION_VERSION}}
    with EventLogger(results_dir, heartbeat_seconds=20) as log:
        try:
            log.set_activity("loading candidate and evaluation cases")
            log.event("evaluation_start", message="Executing candidate in the fixed simulator", cases=len(cases))
            for index, config in enumerate(cases):
                config = dict(config)
                case_id = str(config.pop("case_id", config.pop("id", f"case_{index:03d}")))
                config.pop("name", None)
                artifact = resolve_json(results_dir / f"case_{index:03d}.json")
                if artifact.exists():
                    result = read_json(artifact)
                    outcomes.append({"case_id": case_id, "offline_error": float(result["offline_error"]),
                                     "artifact": artifact.name, **case_diagnostics(result)})
                    log.event("case_reused", message=f"Reusing completed {case_id}", case_id=case_id,
                              offline_error=result["offline_error"], checkpoint=str(artifact))
                    continue
                checkpoint.update(status="running", completed_cases=outcomes, active_case=case_id)
                atomic_json(checkpoint_path, checkpoint)
                # A fresh module isolates any policy memory across independent cases,
                # matching the comparison CLI's treatment of candidate state.
                policy = load_policy(program_path)
                log.set_activity(f"evaluating {case_id} ({index + 1}/{len(cases)})")
                log.event("case_start", message=f"Evaluating {case_id}", case_id=case_id, index=index + 1, total=len(cases), config=config)

                def progress(event, case_id=case_id):
                    event = dict(event)
                    phase = event.pop("phase", event.pop("event", "simulation_progress"))
                    message = event.pop("message", f"{case_id}: {phase}")
                    event.pop("case_id", None)
                    log.event(phase, message=message, case_id=case_id, **event)

                result = annotate_count_log(run_case(config, policy=policy, progress=progress), policy)
                offline_error = float(result["offline_error"])
                if not math.isfinite(offline_error) or offline_error < 0:
                    raise ValueError(f"Invalid offline error for {case_id}: {offline_error}")
                # Retain scientific traces rather than reducing the experiment to its score.
                artifact = write_compressed_json(artifact, {"case_id": case_id, **result})
                outcomes.append({"case_id": case_id, "offline_error": offline_error, "artifact": artifact.name, **case_diagnostics(result)})
                checkpoint.update(completed_cases=outcomes, active_case=None)
                atomic_json(checkpoint_path, checkpoint)
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
                    + f". Largest tracking error: {worst['case_id']}. Examine integer allocation "
                    "using public observed state, with radius scale 2, all memories reevaluated "
                    "and retained velocities fixed. Executed counts mean the actual simulator "
                    "particle allocation; horizon-truncated responses separately retain counts "
                    "with objective queries. Constant allocation is permitted and receives no "
                    "penalty for simplicity. Large interval-end "
                    "errors indicate tracking still missed by the next change, while detection and "
                    "memory shares expose objective-evaluation overhead. These diagnostics describe "
                    "behavior and do not by themselves prove its cause. Improvements must "
                    "preserve the fixed simulator and objective-evaluation budget. These are search "
                    "results; generalization requires separate comparison cases."
                ),
            }
            log.event("evaluation_complete", message="Candidate evaluation complete", **metrics["public"])
        except OSError:
            # Failed reads or writes are infrastructure failures, never fitness.
            raise
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            metrics["private"].update({"error": error, "cases": outcomes})
            metrics["text_feedback"] = "Candidate evaluation failed: " + error
            (results_dir / "error.txt").write_text(traceback.format_exc())
            log.event("evaluation_failed", message=error, cases_completed=len(outcomes))
        for filename, value in (("metrics.json", metrics), ("correct.json", {"correct": not error, "error": error})):
            destination = results_dir / filename
            if not destination.exists() or read_json(destination) != value:
                atomic_json(destination, value)
        checkpoint.update(status="failed" if error else "completed", completed_cases=outcomes, active_case=None)
        atomic_json(checkpoint_path, checkpoint)
    return 1 if error else 0


def evaluate(program_path: Path, results_dir: Path, suite_path: Path) -> int:
    try:
        return _evaluate(program_path, results_dir, suite_path)
    except (OSError, InfrastructureError):
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        return INFRASTRUCTURE_EXIT_CODE


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--program_path", type=Path, required=True)
    parser.add_argument("--results_dir", type=Path, required=True)
    parser.add_argument("--suite", type=Path, default=ROOT / "configs" / "relocation_allocation_v2" / "search.json")
    args = parser.parse_args()
    return evaluate(args.program_path.resolve(), args.results_dir.resolve(), args.suite.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
