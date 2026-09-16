"""Checks for the v2 intervention, preserved fixed control and checkpoint resume."""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import pytest

from adaptive_swarms.artifacts import read_json
from adaptive_swarms.execution import INFRASTRUCTURE_EXIT_CODE
from adaptive_swarms.relocation_allocation import (
    allocation_fingerprint, annotate_count_log, constant_count_policy,
    count_diagnostics, count_policy_adapter,
)
from adaptive_swarms.simulator import run_case

ROOT = Path(__file__).resolve().parents[1]
SMALL = {"dimension": 5, "npeaks": 10, "budget": 800, "period": 100,
         "environment_seed": 7, "optimizer_seed": 11, "move_severity": 1,
         "correlation": 0, "trace_interval": 20}


def evaluator_module():
    spec = importlib.util.spec_from_file_location(
        "allocation_evaluator_test", ROOT / "tasks/relocation_allocation_v2/evaluate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("count", range(6))
def test_interior_adapter_executes_exact_integer_counts(count):
    adapter = count_policy_adapter(constant_count_policy(count))
    decision = adapter({"swarm_size": 5})
    assert math.ceil(decision["fraction"] * 5) == count
    assert decision["radius_scale"] == 2
    assert decision["memory"] == "reevaluate"
    assert decision["reset_velocity"] is False
    adapter = count_policy_adapter(constant_count_policy(count))
    result = annotate_count_log(run_case(SMALL, adapter), adapter)
    assert result["response_log"]
    assert all(response["requested_count"] == response["executed_count"] == count
               for response in result["response_log"])
    assert all(response["evaluated_relocation_count"] == count
               for response in result["response_log"] if response["completed"])
    assert result["evaluations"] == sum(result["evaluation_counts"].values()) == SMALL["budget"]
    assert count_diagnostics(result)["executed_count_distribution"][str(count)] == len(result["response_log"])


@pytest.mark.parametrize("invalid", [True, False, 3.0, 2.7, -1, 6, "3", None])
def test_invalid_counts_are_rejected_without_rounding(invalid):
    with pytest.raises(ValueError):
        count_policy_adapter(lambda observation: invalid)({"swarm_size": 5})


def test_constant_three_preserves_original_fixed_control_trajectory():
    adapter = count_policy_adapter(constant_count_policy(3))
    result = annotate_count_log(run_case(SMALL, adapter), adapter)
    legacy = run_case(SMALL, lambda observation: {
        "radius_scale": 2, "fraction": 0.6, "memory": "reevaluate", "reset_velocity": False})
    # The scientific trajectories agree, even though the safe encoding is 0.5
    # and the published v1 control keeps its historical 0.6 representation.
    for key in ("offline_error", "evaluation_counts", "trace", "environment_changes"):
        assert result[key] == legacy[key]
    for current, original in zip(result["response_log"], legacy["response_log"]):
        assert current["relocated_indices"] == original["relocated_indices"]
        assert current["observation"] == original["observation"]
        assert current["radius"] == original["radius"]


def test_observation_copied_and_signed_fitness_retained():
    seen = []

    def choose(observation):
        seen.append(dict(observation))
        observation["swarm_size"] = 0
        return 3

    original = {"swarm_size": 5, "previous_best_fitness": 3, "current_best_fitness": 5,
                "fitness_drop": -2}
    assert count_policy_adapter(choose)(original)["fraction"] == 0.5
    assert seen == [original]
    assert original["swarm_size"] == 5


def test_resume_reuses_completed_v2_case_and_retains_count_feedback(tmp_path, monkeypatch):
    evaluator = evaluator_module()
    program = tmp_path / "main.py"
    program.write_bytes((ROOT / "tasks/relocation_allocation_v2/initial.py").read_bytes())
    suite = tmp_path / "suite.json"
    suite.write_text(json.dumps([SMALL, {**SMALL, "optimizer_seed": 12}]))
    output = tmp_path / "results"
    run = evaluator.run_case
    calls = []

    def interrupt_second_case(config, **kwargs):
        calls.append(config["optimizer_seed"])
        if len(calls) == 2:
            raise OSError("diagnostic interrupted evaluator")
        return run(config, **kwargs)

    monkeypatch.setattr(evaluator, "run_case", interrupt_second_case)
    assert evaluator.evaluate(program, output, suite) == INFRASTRUCTURE_EXIT_CODE
    first = output / "case_000.json.gz"
    first_bytes, first_mtime = first.read_bytes(), first.stat().st_mtime_ns
    assert not (output / "metrics.json").exists()
    calls.clear()

    def record_run(config, **kwargs):
        calls.append(config["optimizer_seed"])
        return run(config, **kwargs)

    monkeypatch.setattr(evaluator, "run_case", record_run)
    assert evaluator.evaluate(program, output, suite) == 0
    assert calls == [12]
    assert first.read_bytes() == first_bytes
    assert first.stat().st_mtime_ns == first_mtime
    metrics = read_json(output / "metrics.json")
    assert metrics["public"]["cases_completed"] == 2
    assert "executed counts" in metrics["text_feedback"]
    assert "horizon-truncated" in metrics["text_feedback"]
    assert "src/adaptive_swarms/relocation_allocation.py" in allocation_fingerprint()
    saved_metrics = (output / "metrics.json").read_bytes()
    program.write_text("def choose_relocation_count(observation): return 4\n")
    with pytest.raises(ValueError, match="candidate, suite, or scientific sources differ"):
        evaluator.evaluate(program, output, suite)
    assert (output / "metrics.json").read_bytes() == saved_metrics
