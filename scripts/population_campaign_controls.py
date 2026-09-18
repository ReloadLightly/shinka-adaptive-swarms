#!/usr/bin/env python3
"""Corrected population campaign controls; resumable case/stage checkpoints."""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import random
import secrets
import sqlite3
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from adaptive_swarms.artifacts import read_json, write_compressed_json
from adaptive_swarms.comparison import validate_pair
from adaptive_swarms.joint_study import collect_used_seeds
from adaptive_swarms.logging import EventLogger, atomic_json
from adaptive_swarms.population_policy_v2 import population_fingerprint as schedule_fingerprint, load_population_policy as load_schedule
from adaptive_swarms.book_population_v2 import run_case, ENGINE_VERSION
from adaptive_swarms.simulator import _validated_config
from adaptive_swarms.campaign_accounting import enforce_research_allowance, research_accounting


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def literal_constant_target(source):
    """A narrow execution-equivalence proof, independent of measured fitness."""
    def statements(body):
        return [n for n in body if not (isinstance(n, ast.Expr) and
                isinstance(n.value, ast.Constant) and isinstance(n.value.value, str))]
    body = statements(ast.parse(source).body)
    if len(body) != 1 or not isinstance(body[0], ast.FunctionDef): return None
    fun = body[0]; args = fun.args; body = statements(fun.body)
    if (fun.name != 'choose_neutral_count' or fun.decorator_list or getattr(fun, 'type_params', []) or args.posonlyargs or
        len(args.args) != 1 or args.args[0].arg != 'observation' or args.args[0].annotation or
        args.vararg or args.kwarg or args.kwonlyargs or args.defaults or args.kw_defaults or
        (fun.returns is not None and not (isinstance(fun.returns, ast.Name) and fun.returns.id == 'int')) or
        len(body) != 1): return None
    stmt = body[0]
    if (isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Constant) and
        type(stmt.value.value) is int and 2 <= stmt.value.value <= 8): return stmt.value.value
    return None


def reuse_native_constant(folder, manifest, name, index, path, ledger):
    """Copy an established identical native execution; recover a copy/ledger gap."""
    method = manifest['methods'][name]
    target = literal_constant_target((folder / method['source']).read_text())
    attempts = [a for a in ledger['attempts'] if a['method'] == name and a['case_index'] == index]
    if target is None or attempts and (len(attempts) != 1 or attempts[0]['status'] != 'reused'):
        return False  # Never erase or disguise an actual control attempt.
    for directory in sorted((folder / 'evolution').glob('search_seed_*/gen_*')):
        checkpoint_path = directory / 'results/evaluation-checkpoint.json'
        source = directory / 'main.py'
        if not checkpoint_path.exists() or not source.exists(): continue
        checkpoint = read_json(checkpoint_path)
        if checkpoint['status'] != 'completed' or literal_constant_target(source.read_text()) != target: continue
        source_case = directory / 'results' / f'case_{index:03d}.json.gz'
        if attempts and attempts[0].get('source_artifact') != str(source_case.relative_to(folder)): continue
        identity = checkpoint['identity']
        if (identity['scientific_sources'] != manifest['scientific_sources'] or
            identity['program_sha256'] != sha(source) or
            identity['suite_sha256'] != sha(directory.parent / 'search-suite.json') or
            identity['evaluation_version'] != 'book_mpso_population_200_v2_reciprocal_v1' or
            identity['evaluator_sha256'] != manifest['frozen_contract_sources']['tasks/book_mpso_population_200_v2/evaluate.py']):
            raise ValueError('Native constant reuse source/fingerprint changed')
        if read_json(directory / 'results/correct.json')['correct'] is not True: continue
        metrics = read_json(directory / 'results/metrics.json')
        if metrics['public']['cases_completed'] != 4: continue
        expected_ids = {f'case_{i:03d}' for i in range(4)}
        completed = checkpoint['completed_cases']
        native_attempt_path = directory / 'results/execution-attempts.json'
        native_attempts = read_json(native_attempt_path)
        if (len(completed) != 4 or {c['case_id'] for c in completed} != expected_ids or
            len(native_attempts) != 4 or {c['case_id'] for c in native_attempts} != expected_ids or
            any(c['status'] != 'completed' or c['exact_objective_queries'] != 500000 or
                c['reserved_objective_queries'] != 500000 for c in native_attempts)):
            raise ValueError('Native constant lacks four completed counted attempts')
        generation = int(directory.name[4:])
        with sqlite3.connect(f'file:{directory.parent / "programs.sqlite"}?mode=ro', uri=True) as db:
            rows = db.execute('SELECT id,code,correct,combined_score FROM programs WHERE generation=?', (generation,)).fetchall()
        if len(rows) != 1 or rows[0][1] != source.read_text() or not rows[0][2] or rows[0][3] != metrics['combined_score']:
            raise ValueError('Native constant database provenance differs')
        saved = read_json(source_case)
        validate_completed_case(saved, manifest['cases'][index], method)
        if saved['case_id'] != f'case_{index:03d}': raise ValueError('Native constant case pairing differs')
        validate_pair(read_json(folder / 'references/target_5' / f'case_{index:03d}.json.gz'), saved)
        if next(c['offline_error'] for c in completed if c['case_id'] == saved['case_id']) != saved['offline_error']:
            raise ValueError('Native constant checkpoint score differs from case')
        digest = sha(source_case)
        if attempts and attempts[0]['artifact_sha256'] != digest:
            raise ValueError('Established native reuse record differs')
        if path.exists():
            if sha(path) != digest: raise ValueError('Existing constant artifact differs from proven alias')
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(path.suffix + '.tmp')
            with temporary.open('wb') as stream:
                stream.write(source_case.read_bytes()); stream.flush(); os.fsync(stream.fileno())
            os.replace(temporary, path)
        if not attempts:
            ledger['attempts'].append({'method':name, 'case_index':index, 'status':'reused',
                'completed_at':now(), 'actual_queries':0, 'reserved_queries':0,
                'offline_error':saved['offline_error'], 'artifact':str(path.relative_to(folder)),
                'artifact_sha256':digest, 'source_artifact':str(source_case.relative_to(folder)),
                'source_program_sha256':sha(source), 'control_program_sha256':method['sha256'],
                'native_program_id':rows[0][0], 'native_generation':generation,
                'native_attempt_ledger_sha256':sha(native_attempt_path),
                'native_checkpoint_sha256':sha(checkpoint_path),
                'proof':'Both modules contain only optional docstrings and one undecorated pure function returning the same literal integer. Same corrected scientific fingerprint, full paired configuration and RNG streams; original native physical attempt remains counted. No equality-of-score inference.'})
            atomic_json(folder / 'references/execution_ledger.json', ledger)
        return True
    return False


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
    if saved.get("engine_version") != ENGINE_VERSION:
        raise ValueError("Historical convergence engine cannot provide corrected scores")
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
    """Freeze four existing development histories and all seven constant-target sources."""
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
        source = ROOT / "configs/book_mpso_population_200_v2/development.json"
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
        contracts = ["docs/book_mpso_population_200_v2_protocol.md", "tasks/book_mpso_population_200_v2/evaluate.py",
                     "docs/studies/book_mpso_population_200_v2/analysis_specification.json",
                     "docs/book_mpso_source_record.md", "docs/book_mpso_population_200_v2_source_record.md",
                     "src/adaptive_swarms/campaign_accounting.py", "configs/shinka/book_mpso_population_200_v2.json",
                     "configs/book_mpso_population_200_v2/development.json",
                     "tasks/book_mpso_population_200_v2/initial.py", "tasks/book_mpso_population_200_v2/context.md",
                     "tasks/book_mpso_population_200_v2/task_prompt.txt"]
        methods = {}
        programs = folder / "programs"; programs.mkdir()
        initial = ROOT / "tasks/book_mpso_population_200_v2/initial.py"
        for target_count in (5, 3, 2, 4, 6, 7, 8):
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
                    "cases": record["cases"], "methods": methods, "maximum_new_executions": 28,
                    "whole_study_maximum_executions": 400, "scientific_sources": schedule_fingerprint(),
                    "frozen_contract_sources": {p: sha(ROOT / p) for p in contracts},
                    "development_cases_sha256": sha(folder / "development_cases.json")}
        atomic_json(path, manifest)
        with EventLogger(folder / "operations") as log:
            log.event("references_registered", cases=4, methods=list(methods), reused_development_identities=True,
                      maximum_new_executions=28, manifest=str(path))


def execute(folder, max_new_cases=None, stage="references", targets=(5, 3)):
    """Session 1 runs only 5/3; remaining constants are deferred, never erased."""
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
    new_queries = 0
    with (stage_dir / "controller.lock").open("a") as lock, EventLogger(stage_dir) as log:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with EventLogger(folder / "operations") as operations:
            for i, config in enumerate(manifest["cases"]):
                reference = None
                for name, method in manifest["methods"].items():
                    if method["fixed_target"] not in targets:
                        continue
                    path = stage_dir / name / f"case_{i:03d}.json.gz"
                    if stage == 'references':
                        reuse_native_constant(folder, manifest, name, i, path, ledger)
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
                    elapsed = [a["elapsed_seconds"] for a in ledger["attempts"] if a["status"] == "completed" and "elapsed_seconds" in a]
                    reserve = max(300.0, max(elapsed, default=0) * 1.5)
                    if (deadline-datetime.now(timezone.utc)).total_seconds() < reserve:
                        log.event("case_admission_closed", reserve_seconds=reserve)
                        return
                    enforce_research_allowance(folder)
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
                    operations.set_activity(f"{stage} {name} case {i + 1}/{len(manifest['cases'])}; waiting for counted simulator progress")
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
                        new_queries += result["evaluations"]
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
            ledger.update(status="session_targets_completed", completed_targets=list(targets), completed_at=datetime.now(timezone.utc).isoformat())
            atomic_json(ledger_path, ledger)
            operations.event("stage_complete", stage=stage,
                             new_executions=new_count, new_objective_queries=new_queries,
                             cumulative_completed_executions=sum(a["status"] == "completed" for a in ledger["attempts"]),
                             cumulative_objective_queries=sum(a.get("actual_queries", 0) for a in ledger["attempts"]))


def freeze_suite(folder):
    manifest = read_json(folder / "references/manifest.json")
    verify_registration(folder, manifest)
    ledger = read_json(folder / "references/execution_ledger.json")
    if sum(a["status"] == "completed" and a["method"] in {"target_3", "target_5"} for a in ledger["attempts"]) != 8:
        raise ValueError("All eight corrected 3/5 reference records must complete before feedback")
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
            validate_completed_case(result, config, method)
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
    suite = {"schema": "book-mpso-population-search-suite-v1", "study": "book_mpso_population_200_v2",
             "cases": manifest["cases"], "feedback_references": references,
             "reference_manifest_sha256": sha(folder / "references/manifest.json"),
             "development_only": True, "permanent_quantum": 1, "campaign_directory": str(folder.resolve())}
    path = folder / "search_suite.json"
    if path.exists():
        if read_json(path) != suite:
            raise ValueError("Existing frozen search suite differs")
    else:
        atomic_json(path, suite)
    with EventLogger(folder / "operations") as log:
        log.event("search_suite_frozen", suite=str(path), sha256=sha(path), seed_source_sha256=references["target_5"]["source_sha256"],
                  exact_seed_cache_cases=4, cumulative_reference_executions=sum(a["status"] == "completed" for a in ledger["attempts"]),
                  cumulative_reference_objective_queries=sum(a.get("actual_queries", 0) for a in ledger["attempts"]))
    print(json.dumps({"suite": str(path), "sha256": sha(path), "roles": list(references)}))
