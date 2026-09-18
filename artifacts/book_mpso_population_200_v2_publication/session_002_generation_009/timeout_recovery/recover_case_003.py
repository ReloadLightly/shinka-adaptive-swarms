"""One reviewed replay of G9's interrupted fourth case; no candidate changes."""
import fcntl
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from adaptive_swarms.artifacts import read_json, write_compressed_json
from adaptive_swarms.logging import EventLogger, atomic_json
from adaptive_swarms.campaign_accounting import enforce_research_allowance
from archive_joint_v3 import copy_bytes, timestamp
from run_population_campaign import verify_numerical_runtime

run = ROOT / "results/book_mpso_population_200_v2/20260917T065325Z"
native = run / "evolution/search_seed_670001"
folder = native / "gen_9/results"
recovery = Path(__file__).parent
spec = importlib.util.spec_from_file_location("frozen_population_evaluator", native / "task_snapshot/evaluate.py")
evaluator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluator)

with (run / "campaign-controller.lock").open("a+") as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    runtime = verify_numerical_runtime(run)
    suite = run / "search_suite.json"
    cases = evaluator.load_cases(suite)
    case_id, config = evaluator.normalized_case(cases[3], 3)
    assert case_id == "case_003"
    program = native / "gen_9/main.py"
    checkpoint = read_json(folder / "evaluation-checkpoint.json")
    assert checkpoint["identity"]["program_sha256"] == evaluator.sha256(program)
    assert checkpoint["identity"]["evaluator_sha256"] == evaluator.sha256(native / "task_snapshot/evaluate.py")
    assert checkpoint["identity"]["scientific_sources"] == evaluator.population_fingerprint()
    assert checkpoint["identity"]["suite_sha256"] == evaluator.sha256(suite)
    assert [c["case_id"] for c in checkpoint["completed_cases"]] == ["case_000", "case_001", "case_002"]
    assert not (folder / "case_003.json.gz").exists()
    attempts = read_json(folder / "execution-attempts.json")
    assert len(attempts) == 4 and attempts[-1]["status"] == "running"
    before = recovery / "before"
    before.mkdir(exist_ok=False)  # This exact recovery may never silently repeat.
    copies = {}
    for name in ("execution-attempts.json", "evaluation-checkpoint.json", "events.jsonl", "run.log"):
        copies[name] = copy_bytes(folder / name, before / name)
    original_hashes = {f.name: evaluator.sha256(f) for f in folder.glob("case_*.json.gz")}
    enforce_research_allowance(run, additional_cases=1)
    review = {
        "reviewed_at": timestamp(), "generation": 9, "case_id": case_id,
        "cause": "Native local scheduler measured its 993-second evaluation timeout from proposal start, including mutation and novelty latency",
        "evidence": "session_002-terminal.log records Process 25469 exceeded timeout of 00:16:33; case_003 last environment event evaluations=140000",
        "decision": "Retain accepted source and three complete cases; preserve interrupted fourth attempt and charge its full 500000 reservation; execute only case_003 once with unchanged frozen engine/config/runtime",
        "partial_observed_queries_lower_bound": 140000,
        "partial_exact_queries": None, "partial_reserved_queries": 500000,
        "additional_reserved_queries": 500000, "new_model_calls": 0,
        "same_session_limits": True, "runtime": runtime,
        "program_sha256": evaluator.sha256(program), "completed_case_hashes": original_hashes,
        "preserved_files": copies,
    }
    atomic_json(recovery / "review.json", review)
    attempts[-1].update(status="interrupted", observed_objective_queries_lower_bound=140000,
                        recovery_review=str(recovery / "review.json"), exact_objective_queries=None)
    attempt = {"case_id": case_id, "status": "running", "reserved_objective_queries": 500000,
               "observed_objective_queries_lower_bound": 0, "exact_objective_queries": None,
               "recovery_of_attempt_index": 3, "recovery_review": str(recovery / "review.json")}
    attempts.append(attempt)
    atomic_json(folder / "execution-attempts.json", attempts)
    with EventLogger(recovery, heartbeat_seconds=20) as log:
        log.event("reviewed_case_recovery", **{k: review[k] for k in ("generation", "case_id", "decision", "new_model_calls")})
        log.set_activity("generation 9: reviewed replay of interrupted case_003; cases 000–002 retained")
        def progress(event):
            item = dict(event)
            if "evaluations" in item:
                attempt["observed_objective_queries_lower_bound"] = max(attempt["observed_objective_queries_lower_bound"], item["evaluations"])
                atomic_json(folder / "execution-attempts.json", attempts)
            kind = item.pop("phase", item.pop("event", "simulation_progress"))
            item.pop("case_id", None)
            log.event(kind, generation=9, case_id=case_id, **item)
        result = {"case_id": case_id, **evaluator.run_case(config, evaluator.load_population_policy(program), progress)}
        evaluator.validate_saved_case(result, config, case_id, folder / "case_003.json.gz")
        for role, reference in read_json(suite)["feedback_references"].items():
            path = Path(reference["case_artifacts"][3])
            assert evaluator.sha256(path) == reference["case_sha256"][3]
            assert evaluator.landscape_identity(result) == evaluator.landscape_identity(read_json(path))
        artifact = write_compressed_json(folder / "case_003.json", result)
        attempt.update(status="completed", exact_objective_queries=result["evaluations"], observed_objective_queries_lower_bound=result["evaluations"])
        atomic_json(folder / "execution-attempts.json", attempts)
        assert all(evaluator.sha256(folder / name) == digest for name, digest in original_hashes.items())
        log.event("case_recovery_complete", generation=9, case_id=case_id, new_objective_queries=result["evaluations"],
                  offline_error=result["offline_error"], artifact=str(artifact), completed_original_cases_unchanged=True,
                  next_step="Native resume will reuse all four saved cases and compute the full score")
