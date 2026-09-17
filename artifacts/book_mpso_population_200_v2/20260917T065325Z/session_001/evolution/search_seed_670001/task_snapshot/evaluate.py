"""Native Shinka evaluator: four-case, 200-peak chapter population continuation."""
from __future__ import annotations

import argparse
from collections import defaultdict
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
from adaptive_swarms.campaign_accounting import enforce_research_allowance
from adaptive_swarms.execution import InfrastructureError, INFRASTRUCTURE_EXIT_CODE
from adaptive_swarms.logging import EventLogger, atomic_json
from adaptive_swarms.population_policy_v2 import population_fingerprint, load_population_policy
from adaptive_swarms.book_population_v2 import run_case, ENGINE_VERSION
from adaptive_swarms.simulator import _validated_config

EVALUATION_VERSION = "book_mpso_population_200_v2_reciprocal_v1"
FEEDBACK_VERSION = "paired_book_population_200_enclosing_ball_recovery_v2"
STORAGE_VERSION = "streaming_gzip_case_checkpoint_v1"
REFERENCE_ROLES = ("target_3", "target_5")
REQUIRED_SETTINGS = {"dimension": 5, "npeaks": 200, "period": 5000,
                     "move_severity": 1.0, "correlation": 0.0, "nexcess": 1,
                     "budget": 500000, "particles_per_swarm": 5,
                     "bounds": [0.0, 100.0], "height_severity": 7.0,
                     "width_severity": 1.0, "chi": 0.729843788, "c": 2.05,
                     "trace_interval": 100, "snapshot_interval": 0,
                     "progress_interval": 5000}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalized_case(case, index):
    config = dict(case)
    case_id = str(config.pop("case_id", config.pop("id", f"case_{index:03d}")))
    config.pop("name", None)
    return case_id, _validated_config(config)


def load_cases(suite_path):
    suite = read_json(suite_path)
    if not isinstance(suite, dict) or not isinstance(suite.get("cases"), list) or len(suite["cases"]) != 4:
        raise ValueError("200-peak development suite requires exactly four cases")
    identities = set()
    seed_pairs = set()
    for index, case in enumerate(suite["cases"]):
        case_id, config = normalized_case(case, index)
        for key, value in REQUIRED_SETTINGS.items():
            if config[key] != value:
                raise ValueError(f"Frozen 200-peak development setting differs: {key}")
        pair = (config["environment_seed"], config["optimizer_seed"])
        if case_id in identities or pair in seed_pairs:
            raise ValueError("Development case identities and seed pairs must be distinct")
        identities.add(case_id)
        seed_pairs.add(pair)
    return suite["cases"]


def validate_saved_case(result, config, case_id, artifact, permanent_quantum=1):
    if result.get("engine_version") != ENGINE_VERSION:
        raise ValueError(f"Saved convergence-engine identity differs: {artifact}")
    if result.get("permanent_quantum") != permanent_quantum:
        raise ValueError(f"Saved permanent quantum mode differs: {artifact}")
    if "population_stats" not in result:
        raise ValueError(f"Saved case lacks population-task diagnostics: {artifact}")
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
    if not isinstance(references, dict) or set(references) != set(REFERENCE_ROLES):
        raise ValueError("Frozen fixed-target 3 and 5 feedback references are required")
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
            validate_saved_case(result, config, case_id, artifact, permanent_quantum=1)
            loaded[role].append(result)
            identities[role].append({"path": str(artifact), "sha256": digest})
    for role in ("target_3",):
        for baseline, seed in zip(loaded[role], loaded["target_5"]):
            if landscape_identity(baseline) != landscape_identity(seed):
                raise ValueError("Reference landscapes are not paired")
    return references, loaded, identities


def evaluation_identity(program_path, suite_path, reference_identities=None):
    if reference_identities is None:
        _, _, reference_identities = load_references(suite_path, load_cases(suite_path))
    return {"program_sha256": sha256(program_path), "suite_sha256": sha256(suite_path),
            "evaluation_version": EVALUATION_VERSION, "feedback_version": FEEDBACK_VERSION,
            "evaluator_sha256": sha256(__file__), "scientific_sources": population_fingerprint(),
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


def population_diagnostics(result):
    stats = {key: value for key, value in result["population_stats"].items() if key != "decision_examples"}
    stats["mean_neutral_count_per_subswarm_update"] = (stats.get("neutral_count_sum", 0) / stats["total_neutral_updates"]
        if stats.get("total_neutral_updates") else None)
    traces = result.get("trace", [])
    interval = result["config"]["trace_interval"]
    regular_trace = [row for row in traces if row["evaluations"] % interval == 0]
    for key in ("total_particle_count", "swarm_count"):
        values = [row[key] for row in traces if key in row]
        stats["recorded_" + key + "_range"] = [min(values), max(values)] if values else None
        sampled = [row[key] for row in regular_trace if key in row]
        stats["trace_sampled_mean_" + key] = statistics.mean(sampled) if sampled else None
    stats["trace_mean_sampling"] = "Regular samples every 100 counted objective evaluations; first-query extra sample excluded"
    return {"population_stats": stats,
            "incomplete_responses": sum(not r.get("completed", True) for r in result.get("response_log", []))}


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
    return {"regime": f"peaks={result['config']['npeaks']},severity={result['config']['move_severity']},period={result['config']['period']}",
            "paired_differences": {role: result["offline_error"] - reference["offline_error"] for role, reference in references.items()},
            "mean_interval_end_error": statistics.mean(e["environment_final_error"] for e in ends) if ends else None,
            "query_category_shares": {key: value / result["evaluations"] for key, value in counts.items()},
            "recovery_episodes": episodes, **population_diagnostics(result)}


def measured_feedback(outcomes, references):
    roles = REFERENCE_ROLES
    best_fixed = min(roles, key=lambda role: (statistics.mean(
        c["offline_error"] - c["paired_differences"][role] for c in outcomes), int(role.split("_")[1])))
    groups = defaultdict(list)
    parts = ["Four reused DEVELOPMENT histories under the corrected enclosing-ball engine, each five-dimensional with 200 conical peaks, "
             "severity 1, change period 5000, correlation 0 and nexcess 1. These same cases are reused "
             "throughout selection; no fresh comparison outcome is supplied. "
             "Lower offline error is better; fitness=1/(1+mean error). "
             "Paired differences are candidate minus comparator (negative is better). "
             "Target 5 is the reconstructed chapter 5+1 and native seed. Fixed targets 3 and 5 start at five "
             "and resize by at most one per detected event using exactly the same adapter. "
             f"Best tested fixed target by development mean (numeric target breaks ties): {best_fixed}. "
             "Only neutral population targets change. Every current neutral quantum-samples on detected "
             "change, otherwise uses ordinary PSO; one permanent quantum particle always samples. "
             "Whole trajectories, convergence/birth timing and later random draws can diverge. "
             "Available public workload fields are swarm_count and total_particle_count; "
             "previous_requested_target supplies the preceding target for the same subswarm. "
             "The policy may use these fields but need not branch or vary population."]
    for case in outcomes:
        groups[case["regime"]].append(case)
        parts.append(f"{case['case_id']} {case['regime']}: error={case['offline_error']:.6f}, "
                     + ", ".join(f"delta{role}={case['paired_differences'][role]:+.6f}" for role in roles)
                     + f"; interval-end error={case['mean_interval_end_error']}; incomplete responses={case['incomplete_responses']}.")
        parts.append("Measured population behavior: " + json.dumps(case["population_stats"], sort_keys=True))
        parts.append("Query shares: " + json.dumps(case["query_category_shares"], sort_keys=True))
        parts.append("Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): "
                     + json.dumps(case["recovery_episodes"]["target_5"], sort_keys=True))
        if best_fixed != "target_5":
            parts.append(f"Observed episodes versus {best_fixed}: " + json.dumps(case["recovery_episodes"][best_fixed], sort_keys=True))
    summaries = []
    for regime, cases in sorted(groups.items()):
        summary = {"regime": regime, "cases": len(cases), "mean_offline_error": statistics.mean(c["offline_error"] for c in cases),
                   "best_tested_fixed_target": best_fixed}
        for role in roles:
            values = [c["paired_differences"][role] for c in cases]
            summary[role + "_mean_difference"] = statistics.mean(values)
            summary[role + "_difference_sd"] = statistics.stdev(values) if len(values) > 1 else 0.0
        summaries.append(summary)
        parts.append("Paired regime summary: " + json.dumps(summary, sort_keys=True))
    for role in roles:
        ranking = sorted(outcomes, key=lambda c: (c["paired_differences"][role], c["case_id"]))
        parts.append(f"Influential cases versus {role}: best=" + json.dumps({k:ranking[0][k] for k in ("case_id","offline_error","paired_differences")}, sort_keys=True)
                     + "; worst=" + json.dumps({k:ranking[-1][k] for k in ("case_id","offline_error","paired_differences")}, sort_keys=True))
    parts.append("The chapter suggests adaptive particles within subswarms as future work. This task tests "
                 "allocation within groups without particle transfer or conserved global population. "
                 "More trajectories, slower update cycling, convergence changes, memory quality and random "
                 "closed-loop variation are competing explanations. Fixed targets do not exhaust all constants. "
                 "Constants remain legitimate; complexity and population variability receive no reward. "
                 "Every case uses the registered full 500000-query development horizon. "
                 "Subswarm count does not directly measure distinct peak coverage. No protected outcome is supplied.")
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
    seed_reuse = checkpoint["identity"]["program_sha256"] == references["target_5"].get("source_sha256")
    if seed_reuse and (references["target_5"].get("scientific_sources") != population_fingerprint()
                       or not references["target_5"].get("case_sha256")):
        raise ValueError("Exact seed reuse requires matching frozen scientific sources and artifact hashes")
    attempt_path = results_dir / "execution-attempts.json"
    attempts = read_json(attempt_path) if attempt_path.exists() else []
    outcomes, error = [], ""
    metrics = {"combined_score": 0.0, "public": {}, "private": {"evaluation_version": EVALUATION_VERSION}}
    with EventLogger(results_dir, heartbeat_seconds=20) as log:
        try:
            log.event("evaluation_start", message="Evaluating 200-peak chapter MPSO neutral-population target", cases=len(cases))
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
                    result = reference_results["target_5"][index]
                    artifact = write_compressed_json(artifact, result)
                    log.event("case_reused", case_id=case_id, reason="exact source, config and scientific fingerprint match",
                              reference=reference_identities["target_5"][index], checkpoint=str(artifact), new_objective_queries=0)
                else:
                    if any(item["case_id"] == case_id for item in attempts):
                        raise InfrastructureError("Incomplete attempted case requires recovery review; reserved work is preserved")
                    campaign = read_json(suite_path).get("campaign_directory")
                    if not campaign:
                        raise ValueError("Campaign accounting directory missing")
                    enforce_research_allowance(campaign)
                    population_policy = load_population_policy(program_path)
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
                        result = {"case_id": case_id, **run_case(config, population_policy, progress)}
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
        except (OSError, InfrastructureError):
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
