#!/usr/bin/env python3
"""Bounded chapter population study using existing case/stage checkpoints."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import random
import secrets
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from adaptive_swarms.artifacts import read_json, write_compressed_json
from adaptive_swarms.comparison import validate_pair
from adaptive_swarms.joint_study import collect_used_seeds
from adaptive_swarms.logging import EventLogger, atomic_json
from adaptive_swarms.population_policy import population_fingerprint as schedule_fingerprint, load_population_policy as load_schedule
from adaptive_swarms.book_population import run_case
from adaptive_swarms.simulator import _validated_config


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def verify_registration(folder, manifest):
    if manifest["scientific_sources"] != schedule_fingerprint():
        raise ValueError("Scientific sources changed after registration")
    for relative, digest in manifest["frozen_contract_sources"].items():
        if sha(ROOT / relative) != digest:
            raise ValueError(f"Frozen contract changed: {relative}")
    for method in manifest["methods"].values():
        if sha(folder / method["source"]) != method["sha256"]:
            raise ValueError("Frozen method source changed")
    if sha(folder / "development_cases.json") != manifest["development_cases_sha256"]:
        raise ValueError("Frozen development cases changed")


def verify_fresh_manifest(folder, manifest):
    """Bind resumed fresh work to the sources and review frozen before seeds."""
    selection = read_json(folder / "selection.json")
    if manifest["selection_sha256"] != sha(folder / "selection.json"):
        raise ValueError("Fresh selection freeze changed")
    if manifest["source_review_sha256"] != sha(folder / "source_review.json"):
        raise ValueError("Fresh source review changed")
    if manifest["methods"] != selection["methods"]:
        raise ValueError("Fresh methods differ from the frozen selection")
    if sha(ROOT / selection["analysis_specification"]) != selection["analysis_sha256"]:
        raise ValueError("Fresh analysis specification changed")


def validate_completed_case(saved, config, method):
    if saved["config"] != config or saved["evaluations"] != config["budget"]:
        raise ValueError("Saved case configuration or budget differs")
    if saved.get("permanent_quantum") != method["permanent_quantum"]:
        raise ValueError("Saved permanent quantum mode differs")
    validate_pair(saved, saved)


def recover_completed_artifact(ledger, name, index, saved, path):
    """Recover the atomic case-write/ledger-write crash window without a rerun."""
    attempts = [a for a in ledger["attempts"]
                if a["method"] == name and a["case_index"] == index]
    if len(attempts) != 1:
        raise ValueError("Saved case requires exactly one original execution attempt")
    attempt = attempts[0]
    digest = sha(path)
    if attempt["status"] == "completed":
        if attempt["artifact_sha256"] != digest:
            raise ValueError("Completed case artifact changed")
        return False
    if attempt["status"] not in {"running", "failed_or_interrupted"}:
        raise ValueError("Saved case has an unsupported attempt state")
    if attempt["reserved_queries"] != saved["evaluations"]:
        raise ValueError("Saved case differs from its reserved objective budget")
    attempt.update(recovery_previous_status=attempt["status"], status="completed",
                   completed_at=now(), actual_queries=saved["evaluations"],
                   last_reported_queries=saved["evaluations"], offline_error=saved["offline_error"],
                   artifact_sha256=digest, recovered_from_completed_artifact=True,
                   recovery_note="Validated atomic full-case artifact; no objective queries repeated. Completion wall time was not observed.")
    return True


def register(folder):
    """Freeze four prospectively generated development pairs and two controls."""
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "registration.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        path = folder / "references/manifest.json"
        if path.exists():
            verify_registration(folder, read_json(path))
            return
        if (folder / "development_cases.json").exists() or (folder / "programs").exists():
            raise RuntimeError("Partial registration requires review; never overwrite cases")
        session = read_json(folder / "session.json")
        if datetime.now(timezone.utc) >= datetime.fromisoformat(session["deadline_utc"]):
            raise TimeoutError("Study deadline passed")
        source = ROOT / "configs/book_mpso_population_200_v1/development.json"
        record = read_json(source)
        if len(record["cases"]) != 4 or any(c["npeaks"] != 200 or c["budget"] != 500000 for c in record["cases"]):
            raise ValueError("Expected four 200-peak full-horizon development cases")
        required = {"dimension": 5, "npeaks": 200, "budget": 500000,
                    "move_severity": 1.0, "period": 5000, "correlation": 0.0, "nexcess": 1}
        if any(any(c.get(k) != v for k, v in required.items()) for c in record["cases"]):
            raise ValueError("Frozen 200-peak chapter settings differ")
        if len({(c["environment_seed"], c["optimizer_seed"]) for c in record["cases"]}) != 4:
            raise ValueError("Four distinct development seed pairs are required")
        record = {**record, "registered_at": now(), "source_sha256": sha(source)}
        contracts = ["docs/book_mpso_population_200_v1_protocol.md", "tasks/book_mpso_population_200_v1/evaluate.py",
                     "scripts/run_book_population_200.py", "docs/studies/book_mpso_population_200_v1/analysis_specification.json",
                     "docs/book_mpso_source_record.md", "configs/shinka/book_mpso_population_200_v1.json",
                     "configs/book_mpso_population_200_v1/development.json",
                     "tasks/book_mpso_population_200_v1/initial.py", "tasks/book_mpso_population_200_v1/context.md",
                     "tasks/book_mpso_population_200_v1/task_prompt.txt"]
        methods = {}
        programs = folder / "programs"; programs.mkdir()
        initial = ROOT / "tasks/book_mpso_population_200_v1/initial.py"
        for target_count in (5, 3):
            name = f"target_{target_count}"; destination = programs / f"{name}.py"
            source_text = initial.read_text() if target_count == 5 else (
                f'"""Fixed target {target_count}; starts at five and changes by at most one per detection."""\n'
                f'def choose_neutral_count(observation) -> int:\n    return {target_count}\n')
            destination.write_text(source_text)
            load_schedule(destination)
            methods[name] = {"kind": "neutral_population_target", "permanent_quantum": 1,
                             "fixed_target": target_count, "source": str(destination.relative_to(folder)),
                             "sha256": sha(destination)}
        atomic_json(folder / "development_cases.json", record)
        manifest = {"schema": "book-mpso-population-reference-v1", "stage": "references", "created_at": now(),
                    "cases": record["cases"], "methods": methods, "maximum_new_executions": 8,
                    "whole_study_maximum_executions": 44, "scientific_sources": schedule_fingerprint(),
                    "frozen_contract_sources": {p: sha(ROOT / p) for p in contracts},
                    "development_cases_sha256": sha(folder / "development_cases.json")}
        atomic_json(path, manifest)
        with EventLogger(folder / "operations") as log:
            log.event("references_registered", cases=4, methods=list(methods), reused_development_identities=False,
                      maximum_new_executions=8, manifest=str(path))


def execute(folder, max_new_cases=None, stage="references"):
    stage_dir = folder / stage
    manifest = read_json(stage_dir / "manifest.json")
    if manifest["scientific_sources"] != schedule_fingerprint():
        raise ValueError("Scientific sources changed after stage registration.")
    verify_registration(folder, read_json(folder / "references/manifest.json"))
    if stage == "fresh":
        verify_fresh_manifest(folder, manifest)
    for method in manifest["methods"].values():
        if method["source"] and sha(folder / method["source"]) != method["sha256"]:
            raise ValueError("Frozen method source changed.")
    session = read_json(folder / "session.json")
    deadline = datetime.fromisoformat(session["research_deadline_utc"])
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
                        validate_completed_case(saved, config, method)
                        cached = [a for a in ledger["attempts"] if a["method"] == name and a["case_index"] == i and a["status"] == "reused"]
                        if cached and (len(cached) != 1 or cached[0]["artifact_sha256"] != sha(path)):
                            raise ValueError("Imported artifact changed")
                        if not cached and recover_completed_artifact(ledger, name, i, saved, path):
                            atomic_json(ledger_path, ledger)
                            log.event("case_recovered", method=name, case_index=i,
                                      artifact=str(path), new_objective_queries=0)
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
                    if sum(a["status"] != "reused" for a in ledger["attempts"]) >= manifest["maximum_new_executions"]:
                        raise RuntimeError("Stage execution ceiling exhausted.")
                    attempt = {"method": name, "case_index": i, "status": "running",
                               "started_at": datetime.now(timezone.utc).isoformat(), "reserved_queries": config["budget"],
                               "last_reported_queries": 0, "artifact": str(path.relative_to(folder))}
                    ledger["attempts"].append(attempt)
                    ledger["status"] = "running"
                    atomic_json(ledger_path, ledger)
                    start = time.monotonic()
                    log.set_activity(f"{stage} {name} case {i + 1}/{len(manifest['cases'])}")
                    log.event("case_start", method=name, case_index=i, budget=config["budget"])
                    operations.event("case_start", stage=stage, method=name, case_index=i, completed=len(ledger["attempts"])-1)

                    def progress(event):
                        queries = event.get("evaluations", 0)
                        attempt["last_reported_queries"] = max(attempt["last_reported_queries"], queries)
                        if event.get("event") in {"progress", "environment_change"} and queries % 50000 == 0:
                            atomic_json(ledger_path, ledger)
                            log.event("case_progress", method=name, case_index=i, evaluations=queries, offline_error=event.get("offline_error"))

                    try:
                        schedule = load_schedule(folder / method["source"])
                        result = run_case(config, schedule, progress)
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
                        if getattr(exc, "objective_queries", None) is not None:
                            attempt["exact_partial_queries"] = exc.objective_queries
                            attempt["last_reported_queries"] = exc.objective_queries
                        attempt.update(status="failed_or_interrupted", error=f"{type(exc).__name__}: {exc}", elapsed_seconds=time.monotonic()-start,
                                       accounting_note="Full requested budget remains reserved; exact partial query count is unavailable beyond last progress event.")
                        atomic_json(ledger_path, ledger)
                        (stage_dir / "error.txt").write_text(traceback.format_exc())
                        raise
            ledger.update(status="completed", completed_at=datetime.now(timezone.utc).isoformat())
            atomic_json(ledger_path, ledger)
            operations.event("stage_complete", stage=stage, new_executions=sum(a["status"] == "completed" for a in ledger["attempts"]), objective_queries=sum(a.get("actual_queries", 0) for a in ledger["attempts"]))


def freeze_suite(folder):
    manifest = read_json(folder / "references/manifest.json")
    verify_registration(folder, manifest)
    ledger = read_json(folder / "references/execution_ledger.json")
    if ledger["status"] != "completed" or len(ledger["attempts"]) != 8:
        raise ValueError("All eight paired reference records must complete before freezing feedback")
    references = {}
    reference_results = {}
    for role, name in [(f"target_{k}", f"target_{k}") for k in (3, 5)]:
        method = manifest["methods"][name]
        paths, hashes, rows = [], [], []
        for index, config in enumerate(manifest["cases"]):
            path = (folder / "references" / name / f"case_{index:03d}.json.gz").resolve()
            result = read_json(path)
            if result.get("case_id") != f"case_{index:03d}" or result["config"] != config:
                raise ValueError("Reference identity differs")
            validate_pair(result, result)
            completed = [a for a in ledger["attempts"] if a["method"] == name and a["case_index"] == index and a["status"] in {"completed", "reused"}]
            if len(completed) != 1 or completed[0]["artifact_sha256"] != sha(path):
                raise ValueError("Reference execution ledger does not match saved artifact")
            paths.append(str(path)); hashes.append(sha(path)); rows.append(result)
        reference_results[role] = rows
        references[role] = {"method": name, "case_artifacts": paths, "case_sha256": hashes,
                            "source_sha256": method["sha256"], "scientific_sources": schedule_fingerprint(), "permanent_quantum": method["permanent_quantum"]}
    for role in ("target_3",):
        for first, second in zip(reference_results[role], reference_results["target_5"]):
            validate_pair(first, second)
    suite = {"schema": "book-mpso-population-search-suite-v1", "study": "book_mpso_population_200_v1",
             "cases": manifest["cases"], "feedback_references": references,
             "reference_manifest_sha256": sha(folder / "references/manifest.json"),
             "development_only": True, "permanent_quantum": 1}
    path = folder / "search_suite.json"
    if path.exists():
        if read_json(path) != suite:
            raise ValueError("Existing frozen search suite differs")
    else:
        atomic_json(path, suite)
    with EventLogger(folder / "operations") as log:
        log.event("search_suite_frozen", suite=str(path), sha256=sha(path), seed_source_sha256=references["target_5"]["source_sha256"],
                  exact_seed_cache_cases=4, reference_new_executions=sum(a["status"] == "completed" for a in ledger["attempts"]),
                  reference_objective_queries=sum(a.get("actual_queries", 0) for a in ledger["attempts"]))
    print(json.dumps({"suite": str(path), "sha256": sha(path), "roles": list(references)}))


def freeze_selection(folder):
    """Freeze complete native ranking and tested fixed control before fresh seeds."""
    manifest = read_json(folder / "references/manifest.json")
    verify_registration(folder, manifest)
    target = folder / "selection.json"
    if target.exists():
        saved = read_json(target)
        for method in saved["methods"].values():
            if sha(folder / method["source"]) != method["sha256"]:
                raise ValueError("Frozen source changed")
        return saved
    search = folder / "evolution/search_seed_660001"
    state = read_json(search / "manifest.json")
    if state["status"] != "search_complete" and not (folder / "operations/early_stop.json").exists():
        raise ValueError("Selection requires terminal search or recorded bounded stop")
    ranking = []
    for gen in sorted(search.glob("gen_*"), key=lambda p: int(p.name[4:])):
        path = gen / "results/evaluation-checkpoint.json"
        if not path.exists() or read_json(path).get("status") != "completed": continue
        checkpoint = read_json(path)
        expected_identity = {"program_sha256": sha(gen / "main.py"),
            "suite_sha256": sha(folder / "search_suite.json"),
            "evaluator_sha256": sha(ROOT / "tasks/book_mpso_population_200_v1/evaluate.py"),
            "scientific_sources": schedule_fingerprint()}
        if any(checkpoint.get("identity", {}).get(k) != v for k, v in expected_identity.items()):
            raise ValueError("Completed native checkpoint identity differs from frozen source/task/suite")
        metrics = read_json(gen / "results/metrics.json")
        if metrics.get("public", {}).get("cases_completed") != 4 or metrics.get("combined_score", 0) <= 0: continue
        source = gen / "main.py"; load_schedule(source)
        rows = [read_json(gen / "results" / f"case_{i:03d}.json.gz") for i in range(4)]
        for i, row in enumerate(rows):
            validate_completed_case(row, manifest["cases"][i], {"permanent_quantum": 1})
            validate_pair(read_json(folder / "references/target_5" / f"case_{i:03d}.json.gz"), row)
        ranking.append({"generation": int(gen.name[4:]), "source": str(source.relative_to(folder)),
                        "sha256": sha(source), "mean_offline_error": sum(r["offline_error"] for r in rows)/4,
                        "result_directory": str((gen/"results").relative_to(folder))})
    if not ranking or not any(r["generation"] == 0 for r in ranking):
        raise ValueError("Missing complete valid seed")
    ranking.sort(key=lambda r: (r["mean_offline_error"], r["generation"], r["sha256"]))
    winner = dict(ranking[0]); seed = next(r for r in ranking if r["generation"] == 0)
    fixed_ranking = [{"target": k, "method": f"target_{k}", "mean_offline_error":
        sum(read_json(folder/f"references/target_{k}/case_{i:03d}.json.gz")["offline_error"] for i in range(4))/4} for k in (3,5)]
    fixed_ranking.sort(key=lambda r: (r["mean_offline_error"], r["target"]))
    best_fixed = fixed_ranking[0]
    destination = folder / "programs/selected.py"
    with destination.open("xb") as stream: stream.write((folder/winner["source"]).read_bytes())
    winner["native_source"] = winner["source"]; winner["source"] = str(destination.relative_to(folder))
    proceed = (winner["generation"] > 0 and winner["sha256"] != seed["sha256"] and
               winner["mean_offline_error"] < seed["mean_offline_error"] and
               winner["mean_offline_error"] < best_fixed["mean_offline_error"])
    methods = {name: manifest["methods"][name] for name in ("target_5", "target_3")}
    methods["selected"] = {"kind": "neutral_population_target", "permanent_quantum": 1,
                           "source": winner["source"], "sha256": winner["sha256"]}
    aliases = {"development_selected_fixed_target": best_fixed["method"]}
    if winner["generation"] == 0: aliases["selected"] = "target_5"
    spec = "docs/studies/book_mpso_population_200_v1/analysis_specification.json"
    record = {"frozen_at": now(), "selection_basis": "development mean, earlier generation, source SHA256",
        "ranking": ranking, "selected": winner, "native_seed": seed, "methods": methods,
        "selected_fixed_target": best_fixed["target"], "fixed_target_ranking": fixed_ranking,
        "fixed_target_tie_break": "mean error then numeric target ascending", "execution_aliases": aliases,
        "analysis_specification": spec, "analysis_sha256": sha(ROOT/spec),
        "scientific_sources": schedule_fingerprint(), "fresh_comparison_required": proceed,
        "fresh_case_identities_generated": False}
    atomic_json(target, record)
    with EventLogger(folder / "operations") as log:
        log.event("selection_frozen", generation=winner["generation"], mean_offline_error=winner["mean_offline_error"],
                  selected_fixed_target=best_fixed["target"], fresh_comparison_required=proceed,
                  source_sha256=winner["sha256"])
    return record


def register_fresh(folder):
    # This command must be called after exact selected source review.
    selection = read_json(folder/'selection.json')
    if not selection['fresh_comparison_required']:
        raise ValueError('No distinct development-advantaged candidate; do not manufacture duplicate comparison')
    review = read_json(folder/'source_review.json')
    if review.get('approved_source_sha256') != selection['selected']['sha256']:
        raise ValueError('Exact frozen source must be reviewed before protected comparison')
    if sha(ROOT/selection['analysis_specification']) != selection['analysis_sha256']:
        raise ValueError('Analysis changed after freeze')
    for method in selection['methods'].values():
        if sha(folder/method['source']) != method['sha256']: raise ValueError('Frozen source changed')
    path = folder/'fresh/manifest.json'
    if path.exists():
        existing = read_json(path)
        verify_fresh_manifest(folder, existing)
        return existing
    with EventLogger(folder/'operations') as log:
        audit = collect_used_seeds([ROOT/'configs',ROOT/'artifacts',ROOT/'results'], progress=lambda files,seeds: log.event('fresh_seed_inventory',files=files,reserved_seeds=seeds))
        forbidden = set(audit['reserved_seed_values']) | {660001,2026091701}
        master = secrets.randbits(128); rng = random.Random(master)
        def fresh():
            while True:
                value=rng.randrange(1,2**31)
                if value not in forbidden: forbidden.add(value); return value
        template=read_json(folder/'development_cases.json')['cases'][0]
        cases=[{**template,'environment_seed':fresh(),'optimizer_seed':fresh()} for _ in range(4)]
        record={'schema':'book-mpso-fresh-v1','stage':'fresh','created_at':now(),
                'selection_frozen_at':selection['frozen_at'],'selection_sha256':sha(folder/'selection.json'),
                'source_review_sha256':sha(folder/'source_review.json'),'seed_generation_master_seed':master,
                'historical_seed_audit':audit,'cases':cases,'methods':selection['methods'],
                'scientific_sources':schedule_fingerprint(),'maximum_new_executions':12,
                'interpretation':'independent exploratory paired comparison; no feedback to search'}
        atomic_json(path,record)
        log.event('fresh_cases_registered',cases=4,methods=len(record["methods"]),maximum_queries=4*len(record["methods"])*500000)
        return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["register", "references", "freeze-suite", "freeze-selection", "register-fresh", "fresh"])
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--limit-cases", type=int)
    args = parser.parse_args()
    if args.limit_cases is not None and args.limit_cases < 0:
        parser.error("--limit-cases must be nonnegative")
    folder = args.run.resolve()
    if args.command == "register": register(folder)
    elif args.command == "references": execute(folder, args.limit_cases)
    elif args.command == "freeze-suite": freeze_suite(folder)
    elif args.command == "freeze-selection": freeze_selection(folder)
    elif args.command == "register-fresh": register_fresh(folder)
    else: execute(folder, args.limit_cases, stage="fresh")
