"""Native Shinka evaluator: particle trajectory-continuation priorities."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import sys
import traceback

ROOT = Path(os.environ.get("ADAPTIVE_SWARMS_PROJECT_ROOT", Path(__file__).resolve().parents[2])).resolve()
sys.path.insert(0, str(ROOT / "src"))
from adaptive_swarms.artifacts import case_artifacts, read_json, resolve_json, write_compressed_json
from adaptive_swarms.execution import InfrastructureError, INFRASTRUCTURE_EXIT_CODE
from adaptive_swarms.logging import EventLogger, atomic_json
from adaptive_swarms.particle_retention import (retention_fingerprint, load_retention_priority, fixed_retention_response)
from adaptive_swarms.simulator import run_case, _validated_config

EVALUATION_VERSION = "particle_retention_v1_reciprocal_v1"
FEEDBACK_VERSION = "paired_retention_features_and_recovery_v1"
STORAGE_VERSION = "streaming_gzip_case_checkpoint_v1"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalized_case(case, index):
    config = dict(case)
    case_id = str(config.pop("case_id", config.pop("id", f"case_{index:03d}")))
    config.pop("name", None)
    return case_id, _validated_config(config)


def load_cases(suite_path):
    suite = read_json(suite_path)
    if not isinstance(suite, dict) or not isinstance(suite.get("cases"), list) or not suite["cases"]:
        raise ValueError("Sprint suite requires an explicit nonempty cases list")
    for index, case in enumerate(suite["cases"]):
        normalized_case(case, index)
    return suite["cases"]


def validate_saved_case(result, config, case_id, artifact):
    if result.get("case_id") != case_id or result.get("config") != config:
        raise ValueError(f"Saved case inputs differ: {artifact}")
    if result.get("evaluations") != config["budget"] or sum(result["evaluation_counts"].values()) != config["budget"]:
        raise ValueError(f"Incomplete objective budget: {artifact}")
    if not math.isfinite(result["offline_error"]) or result["offline_error"] < 0:
        raise ValueError(f"Invalid offline error: {artifact}")


def landscape_identity(result):
    return [result["initial_environment"]["sha256"]] + [
        item["next_environment"]["sha256"] for item in result["environment_changes"]]


def load_references(suite_path, cases):
    references = read_json(suite_path).get("feedback_references")
    if not isinstance(references, dict) or set(references) != {"random", "seed"}:
        raise ValueError("Frozen random and heuristic seed feedback references are required")
    loaded, identities = {}, {}
    for role, reference in references.items():
        paths = reference.get("case_artifacts", [])
        if not reference.get("method") or len(paths) != len(cases):
            raise ValueError(f"Missing {role} reference artifacts")
        expected_hashes = reference.get("case_sha256")
        if expected_hashes is not None and len(expected_hashes) != len(paths):
            raise ValueError(f"Wrong {role} reference hash count")
        loaded[role], identities[role] = [], []
        for index, path in enumerate(paths):
            artifact = Path(path)
            if not artifact.is_absolute() or not artifact.is_file():
                raise ValueError(f"Missing absolute reference artifact: {artifact}")
            digest = sha256(artifact)
            if expected_hashes is not None and digest != expected_hashes[index]:
                raise ValueError(f"Frozen reference hash differs: {artifact}")
            result = read_json(artifact)
            case_id, config = normalized_case(cases[index], index)
            validate_saved_case(result, config, case_id, artifact)
            loaded[role].append(result)
            identities[role].append({"path": str(artifact), "sha256": digest})
    for baseline, seed in zip(loaded["random"], loaded["seed"]):
        if landscape_identity(baseline) != landscape_identity(seed):
            raise ValueError("Reference landscapes are not paired")
    return references, loaded, identities


def evaluation_identity(program_path, suite_path, reference_identities=None):
    if reference_identities is None:
        _, _, reference_identities = load_references(suite_path, load_cases(suite_path))
    return {"program_sha256": sha256(program_path), "suite_sha256": sha256(suite_path),
            "evaluation_version": EVALUATION_VERSION, "feedback_version": FEEDBACK_VERSION,
            "evaluator_sha256": sha256(__file__), "scientific_sources": retention_fingerprint(),
            "feedback_reference_artifacts": reference_identities}


def prepare_checkpoint(program_path, results_dir, suite_path, reference_identities=None):
    identity = evaluation_identity(program_path, suite_path, reference_identities)
    path = results_dir / "evaluation-checkpoint.json"
    if path.exists():
        checkpoint = read_json(path)
        if checkpoint["identity"] != identity:
            raise ValueError("Checkpoint candidate, suite, references or scientific sources differ")
        return checkpoint
    if case_artifacts(results_dir):
        raise ValueError("Saved cases require original checkpoint provenance")
    checkpoint = {"storage_version": STORAGE_VERSION, "identity": identity,
                  "status": "running", "completed_cases": []}
    atomic_json(path, checkpoint)
    return checkpoint


def retention_diagnostics(result):
    rows = [r["retention"] for r in result["response_log"] if "retention" in r]
    selected = [r["features"][r["selected_index"]] for r in rows]
    names = ("personal_best_rank", "distance_to_best_normalized", "speed_normalized", "velocity_alignment")
    return {"retention_decisions": len(rows),
            "heuristic_agreements": sum(r["agrees_with_heuristic"] for r in rows),
            "heuristic_agreement_fraction": (sum(r["agrees_with_heuristic"] for r in rows)/len(rows) if rows else None),
            "selected_rank_counts": dict(Counter(str(int(f["personal_best_rank"])) for f in selected)),
            "selected_feature_means": {name: statistics.mean(f[name] for f in selected) if selected else None for name in names},
            "incomplete_responses": sum(not r["completed"] for r in result["response_log"]),
            "interpretation": "Heuristic agreement is a counterfactual choice on this method's same snapshot/tie order, not particle matching across diverged trajectories."}


def case_diagnostics(result, references):
    counts = result["evaluation_counts"]
    ends = result["environment_changes"]
    episodes = {}
    for role, reference in references.items():
        if landscape_identity(result) != landscape_identity(reference):
            raise ValueError("Candidate and reference landscape histories differ")
        differences = [{"completed_environment": a["completed_environment"],
                        "difference": a["environment_offline_error"] - b["environment_offline_error"],
                        "candidate_environment_error": a["environment_offline_error"],
                        "reference_environment_error": b["environment_offline_error"]}
                       for a, b in zip(ends, reference["environment_changes"], strict=True) if a["completed_environment"] > 0]
        episodes[role] = {"most_favorable": min(differences, key=lambda d: (d["difference"], d["completed_environment"])),
                          "most_unfavorable": max(differences, key=lambda d: (d["difference"], -d["completed_environment"]))} if differences else {}
    return {"regime": f"severity={result['config']['move_severity']},period={result['config']['period']}",
            "paired_differences": {role: result["offline_error"] - reference["offline_error"] for role, reference in references.items()},
            "mean_interval_end_error": statistics.mean(e["environment_final_error"] for e in ends) if ends else None,
            "query_category_shares": {key: value / result["evaluations"] for key, value in counts.items()},
            "recovery_episodes": episodes, **retention_diagnostics(result)}


def measured_feedback(outcomes, references):
    groups = defaultdict(list)
    parts = ["Development feedback only. Lower offline error is better; fitness=1/(1+mean error). "
             "Paired differences are candidate minus comparator (negative is better). "
             f"Random reference is {references['random']['method']}; heuristic seed is {references['seed']['method']}. "
             "All personal-best memories survive and are reevaluated. The exempted particle continues ordinary PSO; "
             "it is neither stationary nor a permanent leader. Choices change complete closed-loop trajectories. "
             "Agreement is measured against the heuristic on each candidate snapshot, not across reference trajectories."]
    for case in outcomes:
        groups[case["regime"]].append(case)
        parts.append(f"{case['case_id']} {case['regime']}: error={case['offline_error']:.6f}, "
                     f"delta random={case['paired_differences']['random']:+.6f}, delta heuristic={case['paired_differences']['seed']:+.6f}; "
                     f"heuristic agreements={case['heuristic_agreements']}/{case['retention_decisions']}; "
                     f"selected ranks={case['selected_rank_counts']}; selected feature means={case['selected_feature_means']}; "
                     f"interval-end error={case['mean_interval_end_error']}; incomplete responses={case['incomplete_responses']}.")
        parts.append("Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): " + json.dumps(case["recovery_episodes"]["seed"], sort_keys=True))
    summaries = []
    for regime, cases in sorted(groups.items()):
        summary = {"regime": regime, "cases": len(cases), "mean_offline_error": statistics.mean(c["offline_error"] for c in cases)}
        for role in ("random", "seed"):
            values = [c["paired_differences"][role] for c in cases]
            summary[role + "_mean_difference"] = statistics.mean(values)
            summary[role + "_difference_sd"] = statistics.stdev(values) if len(values) > 1 else 0.0
        summaries.append(summary)
        parts.append("Paired regime summary: " + json.dumps(summary, sort_keys=True))
    parts.append("Exactly four of five particles relocate at radius1.25 with retained velocities and fixed memory reevaluation. "
                 "Only the per-particle retention priority evolves. Simple rules and constants are legitimate. "
                 "Competing explanations include trajectory continuity, geometric diversity, later asynchronous attractor updates, "
                 "query allocation and stochastic closed-loop variation. No fresh validation is planned in this bounded development experiment.")
    return "\n".join(parts), summaries


def _evaluate(program_path, results_dir, suite_path):
    results_dir.mkdir(parents=True, exist_ok=True)
    cases = load_cases(suite_path)
    references, reference_results, reference_identities = load_references(suite_path, cases)
    checkpoint = prepare_checkpoint(program_path, results_dir, suite_path, reference_identities)
    checkpoint_path = results_dir / "evaluation-checkpoint.json"
    for index, case in enumerate(cases):
        case_id, config = normalized_case(case, index)
        path = resolve_json(results_dir / f"case_{index:03d}.json")
        if path.exists():
            validate_saved_case(read_json(path), config, case_id, path)
    # Failed proposals are terminal evidence, not a request to retry numerical work.
    if checkpoint["status"] in {"completed", "failed"}:
        if not (results_dir / "metrics.json").exists() or not (results_dir / "correct.json").exists():
            raise ValueError("Terminal checkpoint lacks native result files")
        return 0 if checkpoint["status"] == "completed" else 1
    seed_reuse = checkpoint["identity"]["program_sha256"] == references["seed"].get("source_sha256")
    if seed_reuse and (references["seed"].get("scientific_sources") != retention_fingerprint()
                       or not references["seed"].get("case_sha256")):
        raise ValueError("Exact seed reuse requires matching frozen scientific sources and artifact hashes")
    attempt_path = results_dir / "execution-attempts.json"
    attempts = read_json(attempt_path) if attempt_path.exists() else []
    outcomes, error = [], ""
    metrics = {"combined_score": 0.0, "public": {}, "private": {"evaluation_version": EVALUATION_VERSION}}
    with EventLogger(results_dir, heartbeat_seconds=20) as log:
        try:
            log.event("evaluation_start", message="Evaluating fixed recovery with particle retention priorities", cases=len(cases))
            for index, case in enumerate(cases):
                case_id, config = normalized_case(case, index)
                artifact = resolve_json(results_dir / f"case_{index:03d}.json")
                checkpoint.update(status="running", completed_cases=outcomes, active_case=case_id)
                atomic_json(checkpoint_path, checkpoint)
                if artifact.exists():
                    result = read_json(artifact)
                    for prior in attempts:
                        if prior["case_id"] == case_id and prior["status"] == "running":
                            prior.update(status="completed", exact_objective_queries=result["evaluations"],
                                         observed_objective_queries_lower_bound=result["evaluations"],
                                         recovered_from_completed_artifact=True)
                            atomic_json(attempt_path, attempts)
                    log.event("case_reused", case_id=case_id, reason="completed checkpoint", checkpoint=str(artifact))
                elif seed_reuse:
                    result = reference_results["seed"][index]
                    artifact = write_compressed_json(artifact, result)
                    log.event("case_reused", case_id=case_id, reason="exact source, config and scientific fingerprint match",
                              reference=reference_identities["seed"][index], checkpoint=str(artifact), new_objective_queries=0)
                else:
                    if any(item["case_id"] == case_id for item in attempts):
                        raise InfrastructureError("Incomplete attempted case requires recovery review; reserved work is preserved")
                    priority = load_retention_priority(program_path)
                    attempt = {"case_id": case_id, "status": "running", "reserved_objective_queries": config["budget"],
                               "observed_objective_queries_lower_bound": 0, "exact_objective_queries": None}
                    attempts.append(attempt)
                    atomic_json(attempt_path, attempts)
                    log.set_activity(f"evaluating {case_id} ({index + 1}/{len(cases)})")
                    log.event("case_start", case_id=case_id, index=index + 1, total=len(cases), config=config)
                    def progress(event):
                        item = dict(event)
                        if "evaluations" in item:
                            attempt["observed_objective_queries_lower_bound"] = max(
                                attempt["observed_objective_queries_lower_bound"], item["evaluations"])
                        kind = item.pop("phase", item.pop("event", "simulation_progress"))
                        item.pop("case_id", None)
                        log.event(kind, case_id=case_id, **item)
                    try:
                        result = {"case_id": case_id, **run_case(config, fixed_retention_response, progress,
                                                               retention_priority=priority)}
                    except Exception as exc:
                        if getattr(exc, "objective_queries", None) is not None:
                            attempt["exact_objective_queries"] = exc.objective_queries
                            attempt["observed_objective_queries_lower_bound"] = exc.objective_queries
                        raise
                    attempt.update(status="completed", exact_objective_queries=result["evaluations"],
                                   observed_objective_queries_lower_bound=result["evaluations"])
                    atomic_json(attempt_path, attempts)
                    validate_saved_case(result, config, case_id, artifact)
                    artifact = write_compressed_json(artifact, result)
                    log.event("case_complete", case_id=case_id, offline_error=result["offline_error"], new_objective_queries=result["evaluations"])
                outcomes.append({"case_id": case_id, "offline_error": result["offline_error"], "artifact": artifact.name,
                                 **case_diagnostics(result, {role: rows[index] for role, rows in reference_results.items()})})
                checkpoint.update(completed_cases=outcomes, active_case=None)
                atomic_json(checkpoint_path, checkpoint)
            errors = [case["offline_error"] for case in outcomes]
            feedback, regimes = measured_feedback(outcomes, references)
            metrics = {"combined_score": 1.0 / (1.0 + statistics.mean(errors)),
                       "public": {"mean_offline_error": statistics.mean(errors), "worst_case_offline_error": max(errors),
                                  "case_error_std": statistics.stdev(errors) if len(errors) > 1 else 0.0, "cases_completed": len(cases)},
                       "private": {"cases": outcomes, "regime_paired_summaries": regimes, "suite_sha256": sha256(suite_path),
                                   "evaluation_version": EVALUATION_VERSION, "feedback_version": FEEDBACK_VERSION},
                       "text_feedback": feedback}
            log.event("evaluation_complete", **metrics["public"])
        except OSError:
            raise
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            if attempts and attempts[-1]["status"] == "running":
                attempts[-1].update(status="failed", error=error)
                atomic_json(attempt_path, attempts)
            metrics["private"].update(error=error, cases=outcomes, execution_attempts=attempts)
            metrics["text_feedback"] = "Candidate evaluation failed: " + error
            (results_dir / "error.txt").write_text(traceback.format_exc())
            log.event("evaluation_failed", error=error, cases_completed=len(outcomes))
        atomic_json(results_dir / "metrics.json", metrics)
        atomic_json(results_dir / "correct.json", {"correct": not error, "error": error})
        checkpoint.update(status="failed" if error else "completed", completed_cases=outcomes, active_case=None)
        atomic_json(checkpoint_path, checkpoint)
    return 1 if error else 0


def evaluate(program_path, results_dir, suite_path):
    try:
        return _evaluate(Path(program_path), Path(results_dir), Path(suite_path))
    except (OSError, InfrastructureError):
        traceback.print_exc(file=sys.stderr)
        return INFRASTRUCTURE_EXIT_CODE


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--program_path", type=Path, required=True)
    parser.add_argument("--results_dir", type=Path, required=True)
    parser.add_argument("--suite", type=Path, required=True)
    args = parser.parse_args()
    return evaluate(args.program_path.resolve(), args.results_dir.resolve(), args.suite.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
