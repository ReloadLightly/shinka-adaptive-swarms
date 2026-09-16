"""Scientific checks for the joint interface, exact baseline and honest feedback."""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import pytest

from adaptive_swarms.artifacts import read_json
from adaptive_swarms.execution import INFRASTRUCTURE_EXIT_CODE
from adaptive_swarms.joint_relocation import (
    annotate_joint_log, constant_joint_policy, joint_diagnostics,
    joint_fingerprint, joint_policy_adapter, load_joint_policy,
)
from adaptive_swarms.simulator import run_case

ROOT = Path(__file__).resolve().parents[1]
SMALL = {"dimension": 5, "npeaks": 10, "budget": 800, "period": 100,
         "environment_seed": 7, "optimizer_seed": 11, "move_severity": 1,
         "correlation": 0, "trace_interval": 20, "snapshot_interval": 20}


def evaluator_module():
    spec = importlib.util.spec_from_file_location(
        "joint_evaluator_test", ROOT / "tasks/joint_relocation_v3/evaluate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("count", range(6))
def test_exact_count_allocation_and_query_accounting(count):
    adapter = joint_policy_adapter(constant_joint_policy(count, 1.5))
    decision = adapter({"swarm_size": 5})
    assert math.ceil(decision["fraction"] * 5) == count
    assert decision["memory"] == "reevaluate"
    assert decision["reset_velocity"] is False
    assert decision["radius_scale"] == 1.5
    adapter = joint_policy_adapter(constant_joint_policy(count, 1.5))
    result = annotate_joint_log(run_case(SMALL, adapter), adapter)
    assert result["response_log"]
    assert all(item["requested_count"] == item["allocated_count"] == count
               for item in result["response_log"])
    assert all(item["evaluated_relocation_count"] == count
               for item in result["response_log"] if item["completed"])
    assert all(item["allocated_fraction"] == count / 5 for item in result["response_log"])
    assert result["evaluations"] == sum(result["evaluation_counts"].values()) == SMALL["budget"]
    assert joint_diagnostics(result)["allocated_count_distribution"][str(count)] == len(result["response_log"])


@pytest.mark.parametrize("invalid", [True, False, 3.0, 2.7, -1, 6, "3", None])
def test_invalid_count_is_not_coerced(invalid):
    with pytest.raises(ValueError):
        joint_policy_adapter(lambda observation: {"count": invalid, "radius_scale": 1.0})({"swarm_size": 5})


@pytest.mark.parametrize("invalid", [True, False, -0.1, math.nan, math.inf, -math.inf, "1.0", None])
def test_invalid_radius_is_not_clipped_or_coerced(invalid):
    with pytest.raises(ValueError):
        joint_policy_adapter(lambda observation: {"count": 3, "radius_scale": invalid})({"swarm_size": 5})


@pytest.mark.parametrize("action", [None, 3, {"count": 3}, {"radius_scale": 1},
                                  {"count": 3, "radius_scale": 1, "memory": "reset"}])
def test_action_has_exact_contract(action):
    with pytest.raises(ValueError, match="exactly count and radius_scale"):
        joint_policy_adapter(lambda observation: action)({"swarm_size": 5})


def test_zero_radius_and_integral_radius_are_valid():
    for radius in (0, 0.0, 1, 4.0):
        action = joint_policy_adapter(constant_joint_policy(5, radius))({"swarm_size": 5})
        assert type(action["radius_scale"]) is float
        assert action["radius_scale"] == radius


@pytest.mark.parametrize("severity,period,seed", [(1, 100, 11), (3, 163, 12), (1, 97, 13)])
def test_seed_preserves_corrected_baseline_queries_and_movement(severity, period, seed):
    config = {**SMALL, "move_severity": severity, "period": period, "optimizer_seed": seed}
    adapter = joint_policy_adapter(load_joint_policy(ROOT / "tasks/joint_relocation_v3/initial.py"))
    current = annotate_joint_log(run_case(config, adapter), adapter)
    baseline = run_case(config)
    for key in ("offline_error", "final_error", "evaluations", "evaluation_counts", "trace",
                "snapshots", "environment_changes", "partial_environment", "iterations", "final_swarm_count"):
        assert current[key] == baseline[key], key
    assert len(current["response_log"]) == len(baseline["response_log"]) > 1
    for response, original in zip(current["response_log"], baseline["response_log"]):
        # Safe fraction .9 and original fraction 1 select the same five particles.
        assert response["adapter_encoding_fraction"] == 0.9
        assert response["allocated_fraction"] == 1.0
        for key in ("relocated_indices", "observation", "radius", "center_before_refresh",
                    "completed", "evaluations_after_detection", "detected_at_evaluation"):
            assert response[key] == original[key], key


def test_count_zero_static_grid_aliases_have_identical_optimization_behavior():
    results = []
    for radius in (0.5, 1.0, 2.0, 4.0):
        adapter = joint_policy_adapter(constant_joint_policy(0, radius))
        results.append(annotate_joint_log(run_case(SMALL, adapter), adapter))
    for current in results[1:]:
        for key in ("offline_error", "final_error", "evaluation_counts", "trace", "snapshots",
                    "environment_changes", "iterations", "final_swarm_count"):
            assert current[key] == results[0][key], key
        assert all(not item["relocated_indices"] for item in current["response_log"])
    # Recorded response state differs, so this alias applies to literal static
    # zero-count rules, not all conditional programs choosing zero temporarily.
    assert results[0]["response_log"][-1]["observation"]["previous_response_radius"] != \
        results[-1]["response_log"][-1]["observation"]["previous_response_radius"]


@pytest.mark.parametrize("queries_after_detection", [2, 7])
def test_horizon_truncation_separates_allocated_and_queried_particles(queries_after_detection):
    reference = joint_policy_adapter(constant_joint_policy(3, 1.0))
    first = run_case(SMALL, reference)["response_log"][0]
    config = {**SMALL, "budget": first["detected_at_evaluation"] + queries_after_detection}
    adapter = joint_policy_adapter(constant_joint_policy(3, 1.0))
    result = annotate_joint_log(run_case(config, adapter), adapter)
    response = result["response_log"][-1]
    assert response["completed"] is False
    assert response["requested_count"] == response["allocated_count"] == 3
    assert response["evaluations_after_detection"] == queries_after_detection
    queried_particles = max(0, queries_after_detection - 5)
    assert response["evaluated_relocation_count"] == sum(
        index < queried_particles for index in response["relocated_indices"])
    assert joint_diagnostics(result)["incomplete_responses"] == 1


def test_observation_copy_preserves_fixed_inputs():
    def choose(observation):
        observation["swarm_size"] = 0
        return {"count": 3, "radius_scale": 1.0}

    original = {"swarm_size": 5}
    assert joint_policy_adapter(choose)(original)["fraction"] == 0.5
    assert original == {"swarm_size": 5}


def test_feedback_distinguishes_allocated_and_encoding_fractions():
    evaluator = evaluator_module()
    adapter = joint_policy_adapter(constant_joint_policy(3, 2.0))
    result = annotate_joint_log(run_case(SMALL, adapter), adapter)
    diagnostics = evaluator.case_diagnostics(result)
    assert diagnostics["mean_allocated_fraction"] == 0.6
    assert diagnostics["mean_adapter_encoding_fraction"] == 0.5
    text = evaluator.describe_case({"case_id": "check", "offline_error": result["offline_error"], **diagnostics})
    assert "allocated fraction 0.6" in text
    assert "adapter encoding fraction 0.5 (encoding only)" in text
    assert "allocated counts" in text


def test_checkpoint_reuses_completed_case_and_identifies_evaluator(tmp_path, monkeypatch):
    evaluator = evaluator_module()
    program = tmp_path / "main.py"
    program.write_bytes((ROOT / "tasks/joint_relocation_v3/initial.py").read_bytes())
    suite = tmp_path / "suite.json"
    suite.write_text(json.dumps([SMALL, {**SMALL, "optimizer_seed": 12}]))
    output = tmp_path / "results"
    run = evaluator.run_case
    calls = []

    def interrupt_second(config, **kwargs):
        calls.append(config["optimizer_seed"])
        if len(calls) == 2:
            raise OSError("diagnostic interrupted evaluator")
        return run(config, **kwargs)

    monkeypatch.setattr(evaluator, "run_case", interrupt_second)
    assert evaluator.evaluate(program, output, suite) == INFRASTRUCTURE_EXIT_CODE
    first = output / "case_000.json.gz"
    first_bytes, first_mtime = first.read_bytes(), first.stat().st_mtime_ns
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
    assert "Allocated fraction is allocated_count/swarm_size" in metrics["text_feedback"]
    assert "horizon-truncated" in metrics["text_feedback"]
    identity = read_json(output / "evaluation-checkpoint.json")["identity"]
    assert identity["evaluation_version"] == "joint_relocation_v3_score_reciprocal"
    assert identity["evaluator_sha256"]
    assert identity["scientific_sources"] == joint_fingerprint()
    saved_metrics = (output / "metrics.json").read_bytes()
    program.write_text("def choose_relocation(observation): return {'count': 4, 'radius_scale': 1.0}\n")
    with pytest.raises(ValueError, match="candidate, suite, or scientific sources differ"):
        evaluator.evaluate(program, output, suite)
    assert (output / "metrics.json").read_bytes() == saved_metrics
