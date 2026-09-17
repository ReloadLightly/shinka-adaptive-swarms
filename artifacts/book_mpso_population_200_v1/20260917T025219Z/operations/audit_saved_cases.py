#!/usr/bin/env python3
"""Independent saved-case audit; no simulations, candidate calls or model calls."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[4]
RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from adaptive_swarms.artifacts import read_json
from adaptive_swarms.logging import atomic_json
from adaptive_swarms.population_policy import population_fingerprint

CONTROLS = ("target_5", "target_3")
SETTINGS = {"dimension": 5, "npeaks": 200, "period": 5000,
            "move_severity": 1.0, "correlation": 0.0, "nexcess": 1,
            "budget": 500000, "particles_per_swarm": 5,
            "bounds": [0.0, 100.0], "height_severity": 7.0,
            "width_severity": 1.0, "chi": 0.729843788, "c": 2.05,
            "trace_interval": 100, "snapshot_interval": 0, "progress_interval": 5000}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_hashes(entries, root):
    for relative, digest in entries.items():
        require(sha(root / relative) == digest, f"Source hash differs: {relative}")


def inspect_case(result, config, case_id, target=None):
    require(result["config"] == config and result["case_id"] == case_id, "Case identity/configuration differs")
    require(all(config[key] == value for key, value in SETTINGS.items()), "Wrong frozen 200-peak condition")
    require(result["evaluations"] == config["budget"] == sum(result["evaluation_counts"].values()) == 500000,
            "Incomplete objective budget or category accounting")
    require(result["permanent_quantum"] == 1 and result["engine_version"] == "book_mpso_population_v1", "Numerical engine/role differs")
    require(math.isfinite(result["offline_error"]) and result["offline_error"] >= 0, "Invalid offline error")
    ends = result["environment_changes"]
    require(len(ends) == result["environments_evaluated"] == 100, "Wrong full-case environment count")
    for index, row in enumerate(ends):
        require(row["completed_environment"] == index and row["evaluations"] == (index + 1) * 5000,
                "Environment boundary identity/order differs")
        require(row["environment_evaluations"] == 5000 and row["first_evaluation"] == index * 5000 + 1,
                "Environment accounting differs")
    integrated = sum(row["environment_offline_error"] * row["environment_evaluations"] for row in ends) / 500000
    require(math.isclose(integrated, result["offline_error"], rel_tol=0, abs_tol=1e-10), "Offline error does not integrate")
    known_categories = {"initialization", "birth", "exclusion", "detection", "memory", "ordinary", "temporary_quantum", "permanent_quantum"}
    require(set(result["evaluation_counts"]) <= known_categories, "Unknown evaluation category")
    require(result["evaluation_counts"]["initialization"] == 6, "Initial swarm does not cost six queries")
    landscapes = [result["initial_environment"]] + [row["next_environment"] for row in ends]
    for landscape in landscapes:
        values = {key: value for key, value in landscape.items() if key != "sha256"}
        require(hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest() == landscape["sha256"], "Landscape hash does not match data")
        require(len(landscape["positions"]) == len(landscape["heights"]) == len(landscape["widths"]) == 200,
                "Saved landscape does not contain 200 peaks")
    stats, schedule = result["population_stats"], result["schedule_stats"]
    require(stats["policy_calls"] == stats["population_decisions"] == len(result["response_log"]) == schedule["detected_change_updates"],
            "Policy/detection/response counts differ")
    requested, additions, removals, previous = Counter(), 0, 0, {}
    for row in result["response_log"]:
        obs = row["observation"]
        before, after, request = row["neutral_count_before"], row["neutral_count_after"], row["requested_target"]
        require(type(request) is int and 2 <= request <= 8, "Invalid requested target")
        if target is not None:
            require(request == target, "Fixed control requested a different target")
        require(obs["change_detected"] is True and obs["has_detected_change"] is True, "Policy called outside detected change")
        require(row["decided_at_evaluation"] - row["detected_at_evaluation"] == before + 1, "Policy timing does not follow all memory refreshes")
        require(obs["neutral_count"] == before and obs["swarm_size"] == before + 1 and obs["permanent_quantum_count"] == 1,
                "Observation population roles differ")
        require(obs["evaluations_since_detected_change"] == before + 1 and obs["updates_since_detected_change"] == 0,
                "Public detection timing differs")
        require(2 <= before <= 8 and 2 <= after <= 8 and after == before + (request > before) - (request < before), "Resize is not one step toward target")
        if row["swarm_id"] not in previous:
            require(before == obs["previous_requested_target"] == 5, "New observed swarm did not begin with target/count five")
        else:
            last_count, last_request = previous[row["swarm_id"]]
            require(before == last_count and obs["previous_requested_target"] == last_request, "Surviving swarm count/history differs")
        previous[row["swarm_id"]] = (after, request)
        require(row["decision"]["temporary_quantum_count"] == after and row["selected_neutral_indices"] == list(range(after)),
                "Published response does not cover all current neutrals")
        require(row["total_particle_count"] == row["total_neutral_count"] + obs["swarm_count"], "Post-resize permanent role accounting differs")
        require(row["total_particle_count"] == obs["total_particle_count"] + after - before, "Workload observation is not pre-resize")
        require(row["finished_at_evaluation"] <= 500000, "Response exceeded horizon")
        movement_count = row["finished_at_evaluation"] - row["decided_at_evaluation"]
        require(movement_count == after + 1 if row["completed"] else 0 <= movement_count < after + 1,
                "Quantum response movement accounting differs")
        if after > before:
            require(row["decision"]["added_neutral_index"] == before, "Growth did not precede permanent quantum role")
            additions += 1
        elif after < before:
            require(0 <= row["decision"]["removed_neutral_index"] < before and math.isfinite(row["decision"]["removed_best_fitness"]),
                    "Removal eligibility/fitness differs")
            removals += 1
        requested[str(request)] += 1
    require(additions == stats["additions"] and removals == stats["removals"], "Resize totals differ")
    require({key: value for key, value in stats["requested_target_histogram"].items() if value} == dict(requested), "Requested histogram differs")
    require(stats["no_change_requests"] + additions + removals == stats["population_decisions"], "No-change accounting differs")
    require(sum(stats["realized_neutral_count_histogram"].values()) == stats["total_neutral_updates"] == schedule["updates"], "Realized update count differs")
    require(sum(int(key) * value for key, value in stats["realized_neutral_count_histogram"].items()) == stats["neutral_count_sum"], "Realized neutral total differs")
    last_query = 0
    for point in result["trace"]:
        require(last_query < point["evaluations"] <= 500000, "Trace query order differs")
        last_query = point["evaluations"]
        swarms = point["swarm_count"]
        require(point["total_particle_count"] == point["total_neutral_count"] + swarms, "Trace role accounting differs")
        require(2 <= point["neutral_count_min"] <= point["neutral_count_max"] <= 8, "Trace neutral bounds differ")
        require(point["neutral_count_min"] * swarms <= point["total_neutral_count"] <= point["neutral_count_max"] * swarms, "Trace neutral count inconsistent")
    require(last_query == 500000 and result["partial_environment"] is None, "Full terminal boundary missing")
    example_updates = 0
    for example in stats["decision_examples"]:
        before_particles = example["particles_before"]
        require(len(before_particles) == example["neutral_count_after"] + 1, "Example permanent role count differs")
        for update in example["particle_updates"]:
            permanent = update["index"] == example["neutral_count_after"]
            quantum = permanent or example["observation"]["change_detected"]
            require((update["kind"] == "permanent_quantum") == permanent and (update["kind"] != "ordinary") == quantum,
                    "Recorded movement role differs from published schedule")
            if quantum:
                require(math.dist(update["position"], update["center"]) <= .5 + 1e-10, "Quantum move exceeds fixed radius")
                require(update["velocity"] == before_particles[update["index"]]["velocity"], "Quantum move changed retained velocity")
            example_updates += 1
    return {"offline_error": result["offline_error"], "queries": 500000,
            "decisions": len(result["response_log"]), "additions": additions, "removals": removals,
            "recorded_particle_updates_checked": example_updates,
            "landscape_hashes": [landscape["sha256"] for landscape in landscapes],
            "query_categories": result["evaluation_counts"], "requested_target_counts": dict(requested)}


def main():
    fingerprint = population_fingerprint()
    manifest = read_json(RUN / "references/manifest.json")
    require(manifest["scientific_sources"] == fingerprint, "Current numerical fingerprint differs")
    check_hashes(manifest["scientific_sources"], ROOT)
    check_hashes(manifest["frozen_contract_sources"], ROOT)
    require(sha(RUN / "development_cases.json") == manifest["development_cases_sha256"], "Development freeze hash differs")
    require(set(manifest["methods"]) == set(CONTROLS) and len(manifest["cases"]) == 4, "Reference suite differs")
    historical = read_json(RUN / "operations/historical-seed-audit.json")["reserved_seed_values"]
    require(not (set(historical) & {row[key] for row in manifest["cases"] for key in ("environment_seed", "optimizer_seed")}),
            "Development seed collides with pre-study historical inventory")
    all_rows, stage_states, attempts, pairing = [], {}, [], {}
    pending_artifact_commits = []

    def audit_saved(path, config, case_index, stage, method, target=None):
        result = read_json(path)
        try:
            row = inspect_case(result, config, f"case_{case_index:03d}", target)
        except Exception as exc:
            raise ValueError(f"{path.relative_to(RUN)}: {exc}") from exc
        key = ("fresh" if stage == "fresh" else "development", case_index)
        if key in pairing:
            require(row["landscape_hashes"] == pairing[key], f"Unpaired landscapes: {path}")
        else:
            pairing[key] = row["landscape_hashes"]
        row.update(case_index=case_index, stage=stage, method=method, artifact=str(path.relative_to(RUN)), sha256=sha(path))
        all_rows.append(row)
        return row

    for stage in ("references", "fresh"):
        path = RUN / stage / "manifest.json"
        if not path.exists():
            continue
        current = read_json(path)
        require(current["scientific_sources"] == fingerprint and len(current["cases"]) == 4, "Stage fingerprint/case count differs")
        if stage == "fresh":
            require(sha(RUN / "selection.json") == current["selection_sha256"] and sha(RUN / "source_review.json") == current["source_review_sha256"], "Fresh freeze differs")
            selection = read_json(RUN / "selection.json")
            require(current["methods"] == selection["methods"] and selection["fresh_comparison_required"], "Fresh condition/method freeze differs")
            frozen_seeds = set(current["historical_seed_audit"]["reserved_seed_values"])
            require(not (frozen_seeds & {row[key] for row in current["cases"] for key in ("environment_seed", "optimizer_seed")}), "Fresh seeds collide with historical/development inventory")
        ledger_path = RUN / stage / "execution_ledger.json"
        ledger = read_json(ledger_path) if ledger_path.exists() else {"attempts": [], "status": "registered"}
        stage_states[stage] = ledger["status"]
        attempts.extend({"stage": stage, **attempt} for attempt in ledger["attempts"])
        for method, detail in current["methods"].items():
            require(sha(RUN / detail["source"]) == detail["sha256"], "Frozen method source differs")
            for index, config in enumerate(current["cases"]):
                artifact = RUN / stage / method / f"case_{index:03d}.json.gz"
                matches = [attempt for attempt in ledger["attempts"] if attempt["method"] == method and attempt["case_index"] == index]
                require(len(matches) <= 1, "Duplicate physical attempt identity")
                if not artifact.exists():
                    require(not matches or matches[0]["status"] != "completed", "Completed ledger entry lacks artifact")
                    continue
                require(len(matches) == 1, "Artifact lacks physical attempt")
                row = audit_saved(artifact, config, index, stage, method, detail.get("fixed_target"))
                attempt = matches[0]
                if attempt["status"] == "completed":
                    require(attempt["artifact_sha256"] == row["sha256"] and attempt["actual_queries"] == 500000, "Ledger artifact/query match failed")
                else:
                    pending_artifact_commits.append(str(artifact.relative_to(RUN)))

    native_rankable = []
    native_case_reuse = 0
    for search in (RUN / "evolution").glob("search_seed_*"):
        native_manifest = read_json(search / "manifest.json")
        stage_states["native_search"] = native_manifest["status"]
        snapshot = search / "task_snapshot"
        snapshot_hashes = read_json(snapshot / "source_hashes.json")
        for name, digest in snapshot_hashes.items():
            if (snapshot / name).is_file():
                require(sha(snapshot / name) == digest, f"Native snapshot changed: {name}")
        for generation in sorted(search.glob("gen_*"), key=lambda path: int(path.name[4:])):
            checkpoint_path = generation / "results/evaluation-checkpoint.json"
            if not checkpoint_path.exists():
                continue
            checkpoint = read_json(checkpoint_path)
            identity = checkpoint["identity"]
            require(identity["program_sha256"] == sha(generation / "main.py") and identity["scientific_sources"] == fingerprint,
                    "Native candidate/scientific fingerprint differs")
            require(identity["suite_sha256"] == sha(RUN / "search_suite.json") and identity["evaluator_sha256"] == sha(snapshot / "evaluate.py"),
                    "Native suite/evaluator fingerprint differs")
            require(identity["evaluation_version"] == "book_mpso_population_200_v1_reciprocal_v1", "Native evaluator version differs")
            for references in identity["feedback_reference_artifacts"].values():
                for reference in references:
                    source = Path(reference["path"])
                    if not source.exists():
                        source = RUN / "references" / source.parent.name / source.name
                    require(sha(source) == reference["sha256"], "Native feedback reference changed")
            attempt_path = generation / "results/execution-attempts.json"
            physical = read_json(attempt_path) if attempt_path.exists() else []
            attempts.extend({"stage": "native", "method": generation.name, **attempt} for attempt in physical)
            found = []
            for index, config in enumerate(manifest["cases"]):
                artifact = generation / "results" / f"case_{index:03d}.json.gz"
                if not artifact.exists():
                    continue
                row = audit_saved(artifact, config, index, "native", generation.name)
                found.append(row)
                matching = [attempt for attempt in physical if attempt["case_id"] == f"case_{index:03d}"]
                if not matching:
                    require(identity["program_sha256"] == manifest["methods"]["target_5"]["sha256"], "Reuse lacks exact target-five source")
                    require(read_json(artifact) == read_json(RUN / "references/target_5" / artifact.name), "Reused native seed result differs")
                    native_case_reuse += 1
                else:
                    require(len(matching) == 1, "Duplicate native physical attempt")
                    if matching[0]["status"] == "completed":
                        require(matching[0]["exact_objective_queries"] == 500000, "Native query accounting differs")
                    else:
                        pending_artifact_commits.append(str(artifact.relative_to(RUN)))
            if checkpoint["status"] == "completed":
                require(len(found) == len(checkpoint["completed_cases"]) == 4, "Terminal native checkpoint is incomplete")
                correct = read_json(generation / "results/correct.json")
                metrics = read_json(generation / "results/metrics.json")
                require(correct["correct"] is True and metrics["public"]["cases_completed"] == 4, "Completed native case count/validity differs")
                mean = statistics.mean(row["offline_error"] for row in found)
                require(math.isclose(metrics["public"]["mean_offline_error"], mean, rel_tol=0, abs_tol=1e-12) and
                        math.isclose(metrics["combined_score"], 1 / (1 + mean), rel_tol=0, abs_tol=1e-12), "Native score differs from complete cases")
                native_rankable.append({"generation": int(generation.name[4:]), "mean_offline_error": mean, "sha256": identity["program_sha256"]})

    if (RUN / "selection.json").exists():
        selection = read_json(RUN / "selection.json")
        ordered = sorted(native_rankable, key=lambda row: (row["mean_offline_error"], row["generation"], row["sha256"]))
        require(ordered and all(selection["selected"][key] == ordered[0][key] for key in ordered[0]), "Selected source differs from complete valid ranking")
        require(len(selection["ranking"]) == len(ordered), "Selection omitted a complete valid native program")
        for name, detail in selection["methods"].items():
            require(sha(RUN / detail["source"]) == detail["sha256"], "Selected method source changed")
        require(sha(ROOT / selection["analysis_specification"]) == selection["analysis_sha256"], "Frozen analysis changed")
        target_means = {method: statistics.mean(row["offline_error"] for row in all_rows if row["stage"] == "references" and row["method"] == method) for method in CONTROLS}
        seed_source = manifest["methods"]["target_5"]["sha256"]
        expected_fresh = ordered[0]["generation"] > 0 and ordered[0]["sha256"] != seed_source and ordered[0]["mean_offline_error"] < min(target_means.values())
        require(selection["fresh_comparison_required"] == expected_fresh, "Fresh trigger differs from frozen comparisons")

    complete_physical = [attempt for attempt in attempts if attempt["status"] == "completed"]
    incomplete_physical = [attempt for attempt in attempts if attempt["status"] not in {"completed", "reused"}]
    exact_queries = sum(attempt.get("actual_queries", attempt.get("exact_objective_queries", 0)) or 0 for attempt in complete_physical)
    exact_partial = sum(attempt.get("exact_partial_queries", attempt.get("exact_objective_queries", 0)) or 0 for attempt in incomplete_physical)
    complete_study = ((RUN / "selection.json").exists() and not incomplete_physical and not pending_artifact_commits and
                      stage_states.get("references") == "completed" and stage_states.get("native_search") == "search_complete" and
                      (not read_json(RUN / "selection.json")["fresh_comparison_required"] or stage_states.get("fresh") == "completed"))
    stop_path = RUN / "operations/stop.json"
    bounded_stop = stop_path.exists() and read_json(stop_path).get("status") == "runtime_constrained_stop_before_search"
    if bounded_stop:
        require(len(all_rows) == len(complete_physical) == 1 and not incomplete_physical and not pending_artifact_commits,
                "Runtime stop must retain exactly the one completed planned execution")
        require(all_rows[0]["stage"] == "references" and all_rows[0]["method"] == "target_5" and all_rows[0]["case_index"] == 0,
                "Runtime stop retained an unexpected execution")
        require(not native_rankable and not (RUN / "selection.json").exists(), "Runtime-only record must remain unranked")
    fully_paired_development = sum(all(any(row["stage"] == "references" and row["method"] == method and row["case_index"] == index
                                         for row in all_rows) for method in CONTROLS) for index in range(4))
    record = {"status": "bounded_stop_saved_case_passed_unranked" if bounded_stop else "passed" if complete_study else "saved_cases_passed_stages_incomplete",
        "recorded_at": datetime.now(timezone.utc).isoformat(), "stage_states": stage_states,
        "complete_case_records": len(all_rows), "complete_rankable_native_programs": native_rankable,
        "physical_completed_executions": len(complete_physical), "physical_incomplete_attempts": incomplete_physical,
        "completed_physical_queries": exact_queries, "exact_partial_queries": exact_partial,
        "native_seed_reused_case_records": native_case_reuse, "pending_artifact_ledger_commits": pending_artifact_commits,
        "development_environment_identities_audited": len({row["case_index"] for row in all_rows if row["stage"] != "fresh"}),
        "fully_paired_development_case_identities": fully_paired_development,
        "fresh_environment_identities_audited": len({row["case_index"] for row in all_rows if row["stage"] == "fresh"}),
        "comparative_performance_inference_available": fully_paired_development == 4,
        "evolutionary_inference_available": len(native_rankable) > 1,
        "cases": all_rows,
        "checks": ["Exact 500000 category accounting and offline-error integral", "101 self-consistent paired landscape states with 200 peaks",
            "All current memories refreshed before policy call", "Five-neutral start for observed swarm identities", "At most one neutral resize and permanent role last",
            "Pre-resize workload/history and complete/incomplete response movement accounting", "Recorded quantum responses replace PSO, retain velocity and use fixed radius",
            "Immutable scientific/task/program fingerprints", "Exact current-reference native-seed reuse", "Only complete valid native programs enter ranking",
            "Fresh source/analysis/seed freeze and trigger if applicable"],
        "scope_note": "Saved evidence only. Exhaustive survivor memory values are not logged; no claim to reverify those values at every event. Partial evaluations are retained in accounting but excluded from ranking. Atomic artifact/ledger completion windows are explicitly marked, never treated as rerun authority.",
        "scientific_interpretation": "Runtime feasibility result only; single complete reference case belongs to an incomplete unranked comparison. No claim about control superiority or Shinka improvement." if bounded_stop else "Saved-record fidelity does not establish optimizer improvement.",
        "objective_queries_in_this_audit": 0, "model_responses_in_this_audit": 0}
    destination = RUN / "operations" / ("saved-case-audit.json" if complete_study or bounded_stop else "saved-case-audit-progress.json")
    atomic_json(destination, record)
    print(json.dumps({key: value for key, value in record.items() if key not in ("cases", "checks")}, indent=2))


if __name__ == "__main__":
    main()
