"""Focused sprint risks; every numerical fixture is durably accounted separately."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import tempfile
from datetime import datetime, timezone

import pytest

from adaptive_swarms.artifacts import read_json, write_compressed_json
from adaptive_swarms.logging import atomic_json
from adaptive_swarms.recovery_response import (annotate_recovery_log, constant_recovery_policy,
    recovery_policy_adapter, recovery_fingerprint, validate_recovery_decision)
from adaptive_swarms import simulator

ROOT = Path(__file__).resolve().parents[1]
LEDGER = Path(os.environ.get("SPRINT_FIXTURE_LEDGER", Path(tempfile.gettempdir()) /
                             f"recovery-response-fixtures-{os.getpid()}.json"))
SMALL = {"dimension": 5, "npeaks": 10, "budget": 1000, "period": 100,
         "environment_seed": 811, "optimizer_seed": 812, "move_severity": 1,
         "trace_interval": 25, "snapshot_interval": 0, "progress_interval": 0}


def fixture_run(config, policy, label):
    result = simulator.run_case(config, policy)
    ledger = read_json(LEDGER) if LEDGER.exists() else {"scope": "small numerical implementation fixtures, excluded from research allocation", "executions": []}
    ledger["executions"].append({"time": datetime.now(timezone.utc).isoformat(), "label": label,
                                 "config": result["config"], "evaluations": result["evaluations"],
                                 "offline_error": result["offline_error"], "evaluation_counts": result["evaluation_counts"],
                                 "status": "completed"})
    seen = {}
    for index, item in enumerate(ledger["executions"]):
        key = (item["label"], json.dumps(item["config"], sort_keys=True))
        item["repeat_of_execution_index"] = seen.get(key)
        seen.setdefault(key, index)
    ledger["total_completed_queries"] = sum(item["evaluations"] for item in ledger["executions"])
    ledger["repeated_fixture_queries"] = sum(item["evaluations"] for item in ledger["executions"] if item["repeat_of_execution_index"] is not None)
    atomic_json(LEDGER, ledger)
    return result


@pytest.fixture(scope="module")
def trace_results():
    outputs = {}
    for trace_interval in (25, 500):
        adapter = recovery_policy_adapter(constant_recovery_policy(1.5, False))
        outputs[trace_interval] = annotate_recovery_log(fixture_run(
            {**SMALL, "trace_interval": trace_interval}, adapter, f"trace_resolution_{trace_interval}"), adapter)
    return outputs


@pytest.fixture(scope="module")
def reset_results():
    outputs = {}
    adapter = recovery_policy_adapter(constant_recovery_policy(1.5, True))
    outputs["reset"] = annotate_recovery_log(fixture_run(SMALL, adapter, "adapter_reset_velocity"), adapter)
    outputs["direct"] = fixture_run(SMALL, lambda obs: {"radius_scale": 1.5,
        "reset_velocity": True, "fraction": 0.7, "memory": "reevaluate"}, "general_interface_reset_velocity")
    return outputs


def test_trace_resolution_changes_only_observation(trace_results):
    dense, sparse = trace_results[25], trace_results[500]
    for key in set(dense) - {"config", "trace"}:
        assert dense[key] == sparse[key], key
    assert len(dense["trace"]) > len(sparse["trace"])
    dense_by_query = {row["evaluations"]: row for row in dense["trace"]}
    assert all(dense_by_query[row["evaluations"]] == row for row in sparse["trace"])


def test_exact_count_and_reset_interface_match_general_simulator(reset_results):
    adapted, general = reset_results["reset"], reset_results["direct"]
    for key in set(general) - {"response_log", "policy_name"}:
        assert adapted[key] == general[key], key
    assert adapted["response_log"]
    for response, original in zip(adapted["response_log"], general["response_log"]):
        assert all(response[key] == value for key, value in original.items())
        assert response["requested_count"] == response["allocated_count"] == 4
        assert response["allocated_fraction"] == 0.8
        assert response["adapter_encoding_fraction"] == 0.7
        assert response["decision"]["reset_velocity"] is True
        assert response["decision"]["memory"] == "reevaluate"
        if response["completed"]:
            assert response["evaluated_relocation_count"] == 4
    assert adapted["evaluations"] == sum(adapted["evaluation_counts"].values()) == 1000


@pytest.mark.parametrize("value", [True, -1, math.nan, math.inf, "1"])
def test_radius_contract(value):
    with pytest.raises(ValueError):
        validate_recovery_decision({"radius_scale": value, "reset_velocity": False})


@pytest.mark.parametrize("value", [0, 1, "false", None])
def test_velocity_contract(value):
    with pytest.raises(ValueError):
        validate_recovery_decision({"radius_scale": 1, "reset_velocity": value})


def evaluator_module():
    spec = importlib.util.spec_from_file_location("sprint_evaluator_tests", ROOT / "tasks/radius_velocity_sprint/evaluate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def checkpoint_fixture(tmp_path, trace_results):
    program = tmp_path / "program.py"
    program.write_text('def choose_recovery(observation):\n    return {"radius_scale": 1.5, "reset_velocity": False}\n')
    result = {"case_id": "case_000", **trace_results[25]}
    reference = write_compressed_json(tmp_path / "reference.json", result)
    ref = {"method": "small_fixture_fixed_control", "case_artifacts": [str(reference)],
           "case_sha256": [hashlib.sha256(reference.read_bytes()).hexdigest()],
           "source_sha256": hashlib.sha256(program.read_bytes()).hexdigest(),
           "scientific_sources": recovery_fingerprint()}
    suite = tmp_path / "suite.json"
    suite.write_text(json.dumps({"cases": [SMALL], "feedback_references": {"baseline": ref, "seed": ref}}))
    return evaluator_module(), program, suite, tmp_path / "evaluation", reference


def test_exact_seed_reuse_and_checkpoint_no_numerical_repetition(checkpoint_fixture, monkeypatch):
    module, program, suite, destination, reference = checkpoint_fixture
    def forbidden(*args, **kwargs):
        raise AssertionError("Exact seed and checkpoint reuse must not execute another case")
    monkeypatch.setattr(module, "run_case", forbidden)
    assert module.evaluate(program, destination, suite) == 0
    artifact = destination / "case_000.json.gz"
    first_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert read_json(artifact) == read_json(reference)
    metrics = read_json(destination / "metrics.json")
    assert metrics["private"]["cases"][0]["paired_differences"] == {"baseline": 0.0, "seed": 0.0}
    assert "syntactic branch coverage" in metrics["text_feedback"]
    assert module.evaluate(program, destination, suite) == 0
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == first_hash
    events = [json.loads(line) for line in (destination / "events.jsonl").read_text().splitlines()]
    assert [e for e in events if e["event"] == "case_reused"][0]["new_objective_queries"] == 0
    assert not [e for e in events if e["event"] == "case_start"]
    program.write_text(program.read_text() + "\n# changed identity\n")
    with pytest.raises(ValueError, match="Checkpoint"):
        module.evaluate(program, destination, suite)


def test_missing_or_changed_reference_is_hard_error(checkpoint_fixture):
    module, program, suite, destination, reference = checkpoint_fixture
    reference.write_bytes(reference.read_bytes() + b" ")
    with pytest.raises(ValueError, match="reference hash differs"):
        module.evaluate(program, destination, suite)
    assert not (destination / "correct.json").exists()
    reference.unlink()
    with pytest.raises(ValueError, match="Missing absolute reference"):
        module.evaluate(program, destination, suite)


def test_terminal_failed_candidate_is_not_reexecuted(checkpoint_fixture, monkeypatch):
    module, program, suite, destination, reference = checkpoint_fixture
    program.write_text(program.read_text() + "\n# distinct test candidate\n")
    calls = []
    def failed_without_numerics(*args, **kwargs):
        calls.append(1)
        raise ValueError("synthetic candidate failure; zero objective calls")
    monkeypatch.setattr(module, "run_case", failed_without_numerics)
    assert module.evaluate(program, destination, suite) == 1
    assert module.evaluate(program, destination, suite) == 1
    assert len(calls) == 1
    assert read_json(destination / "evaluation-checkpoint.json")["status"] == "failed"
    attempts = read_json(destination / "execution-attempts.json")
    assert len(attempts) == 1
    assert attempts[0]["reserved_objective_queries"] == SMALL["budget"]
    assert attempts[0]["exact_objective_queries"] is None
    assert attempts[0]["observed_objective_queries_lower_bound"] == 0
