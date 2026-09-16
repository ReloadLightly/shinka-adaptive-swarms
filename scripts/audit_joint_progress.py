#!/usr/bin/env python3
"""Read saved V3 evidence without evaluating programs or changing controller state.

Counts refer to durable checkpoints and logical native receipts, never hidden
provider retries or objective work in an unfinished, uncheckpointed case.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from adaptive_swarms.artifacts import case_artifacts, read_json
from adaptive_swarms.engine_progress import terminal_failure_generations
from adaptive_swarms.joint_study import verify_registration
from adaptive_swarms.logging import atomic_json


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def check_case(case, config):
    if case["config"] != config:
        raise ValueError("Saved checkpoint differs from the registered case.")
    if case["evaluations"] != config["budget"] or sum(case["evaluation_counts"].values()) != config["budget"]:
        raise ValueError("Saved checkpoint has an incomplete or uncharged objective budget.")
    if not math.isfinite(case["offline_error"]) or case["offline_error"] < 0:
        raise ValueError("Invalid saved error.")
    for response in case["response_log"]:
        size = response["observation"]["swarm_size"]
        count = response["requested_count"]
        if count != response["allocated_count"] or count != len(response["relocated_indices"]) or count != math.ceil(response["adapter_encoding_fraction"] * size):
            raise ValueError("Requested/allocated/encoded counts disagree.")
        if response["requested_radius_scale"] != response["decision"]["radius_scale"] or response["allocated_fraction"] != count / size:
            raise ValueError("Requested radius or allocated fraction disagrees.")
        if response["decision"]["memory"] != "reevaluate" or response["decision"]["reset_velocity"]:
            raise ValueError("Fixed memory/velocity settings changed.")
    states = [case["initial_environment"], *(item["next_environment"] for item in case["environment_changes"])]
    for state in states:
        if digest({key: value for key, value in state.items() if key != "sha256"}) != state["sha256"]:
            raise ValueError("Saved environment state content differs from its hash.")
    return [state["sha256"] for state in states]


def summarized_case(path, config, cache):
    key = str(path.resolve())
    stat = path.stat()
    identity = [stat.st_size, stat.st_mtime_ns, digest(config)]
    saved = cache.get(key)
    if saved and saved["identity"] == identity:
        return saved["summary"]
    case = read_json(path)
    history = check_case(case, config)
    summary = {"history": history, "queries": case["evaluation_counts"],
               "offline_error": case["offline_error"], "response_count": len(case["response_log"]),
               "incomplete_responses": sum(not row["completed"] for row in case["response_log"]),
               "case_index": case.get("case_index"), "method": case.get("method")}
    cache[key] = {"identity": identity, "summary": summary}
    return summary


def latest_native_event(run):
    path = run / "events.jsonl"
    latest, active = None, None
    ignored = {"environment_change", "simulation_progress", "progress", "run_started", "run_completed", "heartbeat"}
    if path.exists():
        with path.open() as stream:
            for line in stream:
                if not line.endswith("\n"):
                    continue  # An active logger may be midway through its newest line.
                event = json.loads(line)
                if type(event.get("generation")) is int:
                    active = max(active if active is not None else -1, event["generation"])
                match = re.search(r"\bgen_(\d+)\b", str(event.get("message", "")))
                if match:
                    active = max(active if active is not None else -1, int(match.group(1)))
                if event.get("event") not in ignored:
                    latest = {key: event[key] for key in ("time", "event", "generation", "role", "status", "call_id", "error") if key in event}
                    if event.get("message"):
                        latest["message"] = str(event["message"])[:500]
    return latest, active


def receipts(run):
    by_role = defaultdict(lambda: {"logical_requests": 0, "requested_logical_responses": 0,
                                   "usable_responses": 0, "statuses": Counter(), "reported_input_tokens": 0,
                                   "reported_output_tokens": 0, "elapsed_completed_seconds": 0.0})
    paths = []
    for path in sorted((run / "engine_calls").glob("*.json")):
        record = read_json(path)
        role = by_role[record["role"]]
        role["logical_requests"] += 1
        role["requested_logical_responses"] += record.get("requested_logical_responses", 1)
        role["usable_responses"] += record.get("valid_responses", 0)
        role["statuses"][record["status"]] += 1
        role["elapsed_completed_seconds"] += record.get("elapsed_seconds", 0.0)
        for response in record.get("responses", []):
            role["reported_input_tokens"] += response.get("input_tokens") or 0
            role["reported_output_tokens"] += response.get("output_tokens") or 0
        paths.append({"path": str(path.relative_to(run)), "call_id": record["call_id"], "role": record["role"], "status": record["status"]})
    return {"roles": dict(by_role), "receipt_records": paths,
            "count_scope": "logical native request wrappers and requested responses; hidden provider retries/usage are not inferred"}


def audit_search(identity, registration, cache):
    run = Path(identity["run"])
    if not (run / "manifest.json").exists():
        return {**identity, "status": "not_started", "saved_cases": 0, "completed_checkpoint_objective_queries": 0,
                "terminal_slots": 0, "valid_descendants": 0, "active_generation": None,
                "latest_interesting_event": None, "shortlist_ready": False, "model_receipts": {"roles": {}}}
    manifest = read_json(run / "manifest.json")
    if manifest.get("task") != "joint_relocation_v3" or manifest.get("generation_target") != 30 or manifest.get("search_seed") != identity["search_seed"]:
        raise ValueError("Active search identity differs from registration.")
    if manifest.get("engine_config") != registration["engine_config"]:
        raise ValueError("Active native engine differs from the registered rich profile.")
    originals, copies, failures = [], [], set()
    if (run / "programs.sqlite").exists():
        connection = sqlite3.connect(f"file:{(run / 'programs.sqlite').resolve()}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("BEGIN")
            rows = [dict(row) for row in connection.execute("SELECT id,code,parent_id,generation,combined_score,correct,metadata,public_metrics FROM programs")]
            failures = terminal_failure_generations(run, connection)
        finally:
            connection.close()
        for row in rows:
            metadata = json.loads(row.pop("metadata") or "{}")
            (copies if any(metadata.get(key) for key in ("_is_island_copy", "is_island_copy", "island_copy")) else originals).append(row)
    evaluated = {row["generation"] for row in originals}
    terminal = evaluated | failures
    if not terminal <= set(range(30)):
        raise ValueError("Native evidence contains slots outside the registered thirty-slot campaign.")
    for name, expected in registration["task_sources"].items():
        path = run / "task_snapshot" / name
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Search task snapshot differs: {path}")
    generations, queries, histories = {}, Counter(), {}
    counts, responses, incomplete = 0, 0, 0
    for directory in sorted(run.glob("gen_*"), key=lambda p: int(p.name.split("_")[-1])):
        paths = case_artifacts(directory / "results")
        if not paths:
            continue
        generation = int(directory.name.split("_")[-1])
        checkpoint = read_json(directory / "results/evaluation-checkpoint.json")
        if checkpoint["identity"]["program_sha256"] != hashlib.sha256((directory / "main.py").read_bytes()).hexdigest():
            raise ValueError("Case checkpoint program source fingerprint changed.")
        errors = []
        for path in paths:
            index = int(path.name.split("_")[1].split(".")[0])
            case = summarized_case(path, registration["search_cases"][index], cache)
            history = case["history"]
            if index in histories and history != histories[index]:
                raise ValueError("Candidates encountered different paired environmental histories.")
            histories.setdefault(index, history)
            counts += 1
            queries.update(case["queries"])
            responses += case["response_count"]
            incomplete += case["incomplete_responses"]
            errors.append(case["offline_error"])
        generations[str(generation)] = {"saved_cases": len(paths), "checkpoint_status": checkpoint["status"],
                                       "mean_saved_case_error": statistics.mean(errors), "complete_suite": len(paths) == len(registration["search_cases"])}
    valid_sources = set()
    for row in originals:
        path = run / f"gen_{row['generation']}" / "main.py"
        if path.exists() and path.read_text() != row["code"]:
            raise ValueError("Native program source differs from saved source.")
        if row["correct"]:
            valid_sources.add(hashlib.sha256(row["code"].encode()).hexdigest())
            summary = generations.get(str(row["generation"]))
            if summary is None or not summary["complete_suite"]:
                raise ValueError("Valid native record has an incomplete case suite.")
            if not math.isclose(row["combined_score"], 1/(1+summary["mean_saved_case_error"]), rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError("Native score differs from checkpoint measurements.")
    model_receipts = receipts(run)
    latest, active = latest_native_event(run)
    pending = sum(role["statuses"].get("started", 0) for role in model_receipts["roles"].values())
    if manifest["status"] in {"search_complete", "interrupted", "infrastructure_failed", "failed", "blocked_runtime"}:
        status = manifest["status"]
    elif pending and any(not item["complete_suite"] for item in generations.values()):
        status = "pending_model_receipts_and_partial_case_suite"
    elif pending:
        status = "pending_native_model_receipts"
    elif any(not item["complete_suite"] for item in generations.values()):
        status = "partial_case_suite"
    else:
        status = "native_proposal_or_postprocessing"
    return {**identity, "status": status, "saved_manifest_status": manifest["status"], "evaluated_slots": len(evaluated),
            "evaluated_generation_ids": sorted(evaluated), "valid_programs": sum(bool(row["correct"]) for row in originals),
            "valid_descendants": sum(row["generation"] > 0 and bool(row["correct"]) for row in originals),
            "active_generation": active, "latest_interesting_event": latest,
            "invalid_evaluated_programs": sum(not row["correct"] for row in originals), "native_island_copy_rows": len(copies),
            "terminal_failed_generation_ids": sorted(failures - evaluated), "terminal_slots": len(terminal),
            "unfinished_slots": sorted(set(range(30)) - terminal), "valid_source_distinct_programs": len(valid_sources),
            "shortlist_ready": manifest["status"] == "search_complete" and terminal == set(range(30)) and any(row["generation"] == 0 and row["correct"] for row in originals),
            "saved_cases": counts, "completed_checkpoint_objective_queries": sum(queries.values()), "query_accounting": dict(queries),
            "saved_response_count": responses, "incomplete_responses_retained": incomplete, "generations": generations,
            "paired_environment_histories_sha256": {str(index): digest(values) for index, values in histories.items()},
            "model_receipts": model_receipts}


def audit_comparison(folder, stage, cache):
    path = folder / stage / "manifest.json"
    if not path.exists():
        return {"status": "not_started", "saved_cases": 0, "completed_checkpoint_objective_queries": 0}
    manifest = read_json(path)
    paths = sorted((folder / stage / "cache").glob("*.json.gz"))
    histories, queries, methods = {}, Counter(), Counter()
    for path in paths:
        saved = cache.get(str(path.resolve()))
        index = saved["summary"]["case_index"] if saved else read_json(path)["case_index"]
        case = summarized_case(path, manifest["cases"][index], cache)
        history = case["history"]
        if index in histories and history != histories[index]:
            raise ValueError("Comparison methods encountered different environment histories.")
        histories.setdefault(index, history)
        queries.update(case["queries"])
        methods[case["method"]] += 1
    return {"status": manifest["status"], "planned_nominal_method_cases": len(manifest["methods"])*len(manifest["cases"]),
            "saved_cases": len(paths), "completed_checkpoint_objective_queries": sum(queries.values()),
            "saved_executions_by_representative_method": dict(methods), "aliases_recorded": len(manifest["aliases"]), "query_accounting": dict(queries)}


def audit(folder, only_search=None, cache_record=None):
    registration = verify_registration(folder)
    cache_record = cache_record if cache_record is not None else {}
    cache_identity = {"registration_signature": registration["signature"], "audit_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    if cache_record.get("identity") != cache_identity:
        cache_record.clear()
        cache_record.update(identity=cache_identity, cases={})
    cache = cache_record["cases"]
    searches = [audit_search(identity, registration, cache) for identity in registration["searches"] if only_search is None or identity["search_index"] == only_search]
    comparisons = {stage: audit_comparison(folder, stage, cache) for stage in ("validation", "final")}
    all_stages = searches + list(comparisons.values())
    return {"format": "joint-v3-durable-progress-audit-v1", "audited_at": datetime.now(timezone.utc).isoformat(),
            "status": "saved_evidence_checks_passed", "registration_signature": registration["signature"],
            "frozen_scientific_sources_unchanged": True, "searches": searches, "comparisons": comparisons,
            "totals": {"saved_case_executions": sum(stage["saved_cases"] for stage in all_stages),
                       "completed_checkpoint_objective_queries": sum(stage["completed_checkpoint_objective_queries"] for stage in all_stages),
                       "terminal_search_slots": sum(stage["terminal_slots"] for stage in searches),
                       "all_searches_ready_for_shortlisting": len(searches) == 3 and all(stage["shortlist_ready"] for stage in searches)},
            "registered_maximum": {"method_cases": 3040, "objective_queries": 304000000},
            "limitations": ["This is a read-only snapshot; an active controller can create new durable evidence while it runs.",
                            "Optional operational cache reuses prior checks only when case size/mtime, registered config and this audit helper's source hash match. It never changes research checkpoints.",
                            "Objective totals cover completed saved case checkpoints. Queries inside a currently running or failed incomplete uncheckpointed case are not inferred.",
                            "Logical request receipts do not reveal hidden provider retries or model reasoning. Started receipts are pending, not successful responses.",
                            "Terminal proposal failures count toward thirty slots but are not evaluated programs. Native seed island copies do not add objective evaluations."],
            "actions": {"simulations_launched": 0, "model_calls_launched": 0, "controller_or_checkpoint_mutations": 0}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, default=Path("results/joint_relocation_v3/study_20260916"))
    parser.add_argument("--search-index", type=int, choices=(0, 1, 2))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--cache", type=Path, help="Optional operational cache of previously verified immutable checkpoints")
    args = parser.parse_args()
    cache = read_json(args.cache) if args.cache and args.cache.exists() else {}
    result = audit(args.study, args.search_index, cache)
    if args.cache:
        atomic_json(args.cache, cache)
    if args.output:
        if args.output.exists():
            raise FileExistsError(f"Preserving previous audit; choose a new output path: {args.output}")
        atomic_json(args.output, result)
    print(json.dumps({"status": result["status"], "audited_at": result["audited_at"], **result["totals"],
                      "search_progress": [{"index": row["search_index"], "status": row["status"], "terminal_slots": row["terminal_slots"],
                                           "valid_descendants": row["valid_descendants"], "saved_cases": row["saved_cases"],
                                           "objective_queries": row["completed_checkpoint_objective_queries"], "active_generation": row["active_generation"],
                                           "role_receipts": {role: {key: value[key] for key in ("logical_requests", "requested_logical_responses", "usable_responses", "statuses")} for role, value in row["model_receipts"]["roles"].items()},
                                           "latest_event": row["latest_interesting_event"]} for row in result["searches"]],
                      "output": str(args.output) if args.output else None}, indent=2), flush=True)


if __name__ == "__main__":
    main()
