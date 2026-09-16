#!/usr/bin/env python3
"""Bounded book-mpso-schedule registration and paired reference checkpoints."""
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
from adaptive_swarms.book_schedule import schedule_fingerprint, load_schedule
from adaptive_swarms.book_mpso import run_case
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


def register(folder):
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "registration.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        path = folder / "references/manifest.json"
        if path.exists():
            manifest = read_json(path)
            verify_registration(folder, manifest)
            print(json.dumps({"status": "existing_registration_verified", "path": str(path)}))
            return
        # Reconcile partial registration explicitly instead of replacing seed identities.
        if (folder / "development_cases.json").exists() or (folder / "programs").exists():
            raise RuntimeError("Partial registration requires review; no fresh identities overwrite it")
        session = read_json(folder / "session.json")
        if datetime.now(timezone.utc) >= datetime.fromisoformat(session["deadline_utc"]):
            raise TimeoutError("Study deadline passed before registration")
        contracts = ["docs/book_mpso_schedule_v1_protocol.md", "tasks/book_mpso_schedule_v1/evaluate.py",
                     "scripts/run_book_mpso.py", "docs/studies/book_mpso_schedule_v1/analysis_specification.json",
                     "docs/book_mpso_source_record.md", "configs/shinka/book_mpso_schedule_v1.json"]
        frozen_contract_sources = {p: sha(ROOT / p) for p in contracts}
        scientific_sources = schedule_fingerprint()
        with EventLogger(folder / "operations") as log:
            log.set_activity("Inventorying historical RNG seeds before fresh development cases")
            audit = collect_used_seeds([ROOT / "configs", ROOT / "artifacts", ROOT / "results"],
                exclude=[folder], progress=lambda files, seeds: log.event("seed_inventory_progress", files=files, reserved_seeds=seeds))
            forbidden = set(audit["reserved_seed_values"])
            planned_seeds = {"native_search_seed": 640001, "analysis_seed": 2026091608}
            forbidden.update(planned_seeds.values())
            master_seed = secrets.randbits(128)
            rng = random.Random(master_seed)
            def fresh():
                while True:
                    value = rng.randrange(1, 2**31)
                    if value not in forbidden:
                        forbidden.add(value)
                        return value
            template = {"dimension": 5, "npeaks": 10, "correlation": 0.0, "budget": 500000,
                        "particles_per_swarm": 5, "nexcess": 1, "trace_interval": 100, "snapshot_interval": 0}
            cases = [_validated_config({**template, "move_severity": severity, "period": period,
                                        "environment_seed": fresh(), "optimizer_seed": fresh()})
                     for severity, period in [(1.0,5000)] for _ in range(8)]
            record = {"schema": "book-mpso-schedule-development-v1", "generated_at": now(),
                      "seed_generation_master_seed": master_seed,
                      "seed_generation_algorithm": "random.Random(secrets.randbits(128)); reject all historical role seeds",
                      "historical_seed_audit": audit, "planned_role_seeds": planned_seeds,
                      "cases": cases, "development_only": True}
            programs = folder / "programs"
            programs.mkdir()
            methods = {}
            for name, source_name in [("mpso_5_0", "initial.py"), ("mpso_5_1", "initial.py")]:
                source = ROOT / "tasks/book_mpso_schedule_v1" / source_name
                target = programs / f"{name}.py"
                with target.open("x") as stream:
                    stream.write(source.read_text())
                # Structural verification performs no simulation or model call.
                load_schedule(target)
                methods[name] = {"kind": "temporary_quantum_schedule", "permanent_quantum": int(name == "mpso_5_1"), "source": str(target.relative_to(folder)),
                                 "sha256": sha(target), "original_source": str(source.relative_to(ROOT))}
            atomic_json(folder / "development_cases.json", record)
            manifest = {"schema": "book-mpso-schedule-reference-v1", "stage": "references", "created_at": now(),
                        "cases": cases, "methods": methods, "maximum_new_executions": 16,
                        "whole_study_maximum_executions": 104, "scientific_sources": scientific_sources,
                        "frozen_contract_sources": frozen_contract_sources,
                        "development_cases_sha256": sha(folder / "development_cases.json")}
            atomic_json(path, manifest)
            log.event("references_registered", cases=8, methods=list(methods), maximum_new_executions=16,
                      unique_fresh_seeds=16, manifest=str(path))


def execute(folder, max_new_cases=None, stage="references"):
    stage_dir = folder / stage
    manifest = read_json(stage_dir / "manifest.json")
    if manifest["scientific_sources"] != schedule_fingerprint():
        raise ValueError("Scientific sources changed after stage registration.")
    verify_registration(folder, read_json(folder / "references/manifest.json"))
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
                        if event.get("event") in {"progress", "environment_change"} and queries % 50000 == 0:
                            atomic_json(ledger_path, ledger)
                            log.event("case_progress", method=name, case_index=i, evaluations=queries, offline_error=event.get("offline_error"))

                    try:
                        schedule = load_schedule(folder / method["source"])
                        result = run_case(config, schedule, progress, permanent_quantum=method["permanent_quantum"])
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
    if ledger["status"] != "completed" or len(ledger["attempts"]) != 16:
        raise ValueError("All sixteen paired reference cases must complete before freezing feedback")
    references = {}
    reference_results = {}
    for role, name in [("mpso_5_0", "mpso_5_0"), ("mpso_5_1", "mpso_5_1")]:
        method = manifest["methods"][name]
        paths, hashes, rows = [], [], []
        for index, config in enumerate(manifest["cases"]):
            path = (folder / "references" / name / f"case_{index:03d}.json.gz").resolve()
            result = read_json(path)
            if result.get("case_id") != f"case_{index:03d}" or result["config"] != config:
                raise ValueError("Reference identity differs")
            validate_pair(result, result)
            completed = [a for a in ledger["attempts"] if a["method"] == name and a["case_index"] == index and a["status"] == "completed"]
            if len(completed) != 1 or completed[0]["artifact_sha256"] != sha(path):
                raise ValueError("Reference execution ledger does not match saved artifact")
            paths.append(str(path)); hashes.append(sha(path)); rows.append(result)
        reference_results[role] = rows
        references[role] = {"method": name, "case_artifacts": paths, "case_sha256": hashes,
                            "source_sha256": method["sha256"], "scientific_sources": schedule_fingerprint(), "permanent_quantum": method["permanent_quantum"]}
    for first, second in zip(reference_results["mpso_5_0"], reference_results["mpso_5_1"]):
        validate_pair(first, second)
    suite = {"schema": "book-mpso-schedule-search-suite-v1", "study": "book_mpso_schedule_v1",
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
        log.event("search_suite_frozen", suite=str(path), sha256=sha(path), seed_source_sha256=references["mpso_5_1"]["source_sha256"],
                  exact_seed_cache_cases=8, reference_new_executions=16, reference_objective_queries=8000000)
    print(json.dumps({"suite": str(path), "sha256": sha(path), "roles": list(references)}))


def freeze_selection(folder):
    """Freeze development ranking and all sources before generating fresh seeds."""
    verify_registration(folder, read_json(folder / "references/manifest.json"))
    target = folder / "selection.json"
    if target.exists():
        saved = read_json(target)
        if sha(folder / saved['selected']['source']) != saved['selected']['sha256']:
            raise ValueError('Frozen selected source changed')
        return saved
    search = folder / 'evolution/search_seed_640001'
    state = read_json(search / 'manifest.json')
    if state['status'] != 'search_complete' and not (folder / 'operations/early_stop.json').exists():
        raise ValueError('Selection requires completed search or recorded bounded early stop')
    ranking = []
    for gen in sorted(search.glob('gen_*'), key=lambda p: int(p.name.split('_')[1])):
        path = gen / 'results/metrics.json'
        if not path.exists(): continue
        metrics = read_json(path)
        if metrics.get('public', {}).get('cases_completed') != 8 or metrics.get('combined_score', 0) <= 0: continue
        source = gen / 'main.py'
        load_schedule(source)
        rows = [read_json(gen / 'results' / f'case_{i:03d}.json.gz') for i in range(8)]
        for i, row in enumerate(rows):
            validate_pair(read_json(folder / 'references/mpso_5_1' / f'case_{i:03d}.json.gz'), row)
        ranking.append({'generation': int(gen.name[4:]), 'source': str(source.relative_to(folder)),
                        'sha256': sha(source), 'mean_offline_error': sum(r['offline_error'] for r in rows)/8,
                        'result_directory': str((gen/'results').relative_to(folder))})
    if not ranking or not any(r['generation'] == 0 for r in ranking):
        raise ValueError('Missing valid seed or complete development candidates')
    ranking.sort(key=lambda r: (r['mean_offline_error'], r['generation'], r['sha256']))
    winner = dict(ranking[0]); seed = next(r for r in ranking if r['generation'] == 0)
    destination = folder / 'programs/selected.py'
    with destination.open('xb') as stream: stream.write((folder/winner['source']).read_bytes())
    winner['native_source'] = winner['source']; winner['source'] = str(destination.relative_to(folder))
    # Identical completed outcomes are treated conservatively as execution-equivalent on development.
    winner_rows = [read_json(folder/winner['result_directory']/f'case_{i:03d}.json.gz') for i in range(8)]
    seed_rows = [read_json(folder/seed['result_directory']/f'case_{i:03d}.json.gz') for i in range(8)]
    same_outcomes = all(a['offline_error'] == b['offline_error'] and a['evaluation_counts'] == b['evaluation_counts'] for a,b in zip(winner_rows,seed_rows))
    proceed = winner['sha256'] != seed['sha256'] and winner['mean_offline_error'] < seed['mean_offline_error'] and not same_outcomes
    manifest = read_json(folder/'references/manifest.json')
    methods = dict(manifest['methods'])
    methods['selected'] = {'kind':'temporary_quantum_schedule','permanent_quantum':1,'source':winner['source'],'sha256':winner['sha256']}
    record = {'frozen_at':now(),'selection_basis':'development only; mean error, earlier generation, source SHA256',
              'ranking':ranking,'selected':winner,'native_seed':seed,'methods':methods,
              'analysis_specification':'docs/studies/book_mpso_schedule_v1/analysis_specification.json',
              'analysis_sha256':sha(ROOT/'docs/studies/book_mpso_schedule_v1/analysis_specification.json'),
              'scientific_sources':schedule_fingerprint(),'fresh_comparison_required':proceed,
              'fresh_case_identities_generated':False,'equivalent_on_complete_development_outcomes':same_outcomes}
    atomic_json(target,record)
    with EventLogger(folder/'operations') as log:
        log.event('selection_frozen',generation=winner['generation'],mean_offline_error=winner['mean_offline_error'],fresh_comparison_required=proceed,source_sha256=winner['sha256'])
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
    if path.exists(): return read_json(path)
    with EventLogger(folder/'operations') as log:
        audit = collect_used_seeds([ROOT/'configs',ROOT/'artifacts',ROOT/'results'], progress=lambda files,seeds: log.event('fresh_seed_inventory',files=files,reserved_seeds=seeds))
        forbidden = set(audit['reserved_seed_values']) | {640001,2026091608}
        master = secrets.randbits(128); rng = random.Random(master)
        def fresh():
            while True:
                value=rng.randrange(1,2**31)
                if value not in forbidden: forbidden.add(value); return value
        template=read_json(folder/'development_cases.json')['cases'][0]
        cases=[{**template,'environment_seed':fresh(),'optimizer_seed':fresh()} for _ in range(8)]
        record={'schema':'book-mpso-fresh-v1','stage':'fresh','created_at':now(),
                'selection_frozen_at':selection['frozen_at'],'selection_sha256':sha(folder/'selection.json'),
                'source_review_sha256':sha(folder/'source_review.json'),'seed_generation_master_seed':master,
                'historical_seed_audit':audit,'cases':cases,'methods':selection['methods'],
                'scientific_sources':schedule_fingerprint(),'maximum_new_executions':24,
                'interpretation':'independent exploratory paired comparison; no feedback to search'}
        atomic_json(path,record)
        log.event('fresh_cases_registered',cases=8,methods=3,maximum_queries=12000000)
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
