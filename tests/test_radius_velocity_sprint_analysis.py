"""Saved-measurement risks only; fabricated cases, no simulator/model calls."""
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sprint_analysis", ROOT / "scripts/analyze_radius_velocity_sprint.py")
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


def test_interaction_keeps_paired_history_variation_and_regimes():
    configs = [{"move_severity": severity, "period": period} for severity in (1, 3) for period in (2500, 5000) for _ in range(2)]
    errors = {method: [10.] * 8 for method in analysis.METHODS}
    errors["c4_r1p5_retain"] = [11., 8.] * 4
    errors["c4_r1p5_reset"] = [8., 13.] * 4
    result = analysis.phase_a_effects(errors, configs)["radius_by_velocity_interaction"]
    assert result["values"] == [-3., 5.] * 4
    assert result["mean"] == result["equal_regime_mean"] == 1.
    assert result["sd"] > 4
    assert all(row["values"] == [-3., 5.] for row in result["regimes"].values())


def test_recovery_uses_saved_offsets_and_boundary_belongs_to_old_environment():
    case = {"config": {"period": 100, "environment_seed": 4}, "trace": [
        {"evaluations": 100, "environment": 0, "current_error": 99.},
        {"evaluations": 125, "environment": 1, "current_error": 8.},
        {"evaluations": 200, "environment": 1, "current_error": 2.},
        {"evaluations": 225, "environment": 2, "current_error": 4.}]}
    curve = analysis.recovery_case_curve(case)
    assert set(curve["offsets"]) == {25, 100}
    assert curve["offsets"][25]["mean_current_error"] == 6.
    assert curve["offsets"][100]["mean_current_error"] == 2.
    assert curve["offsets"][25]["contributing_environments"] == 2
    case["trace"][2]["environment"] = 2
    with pytest.raises(ValueError, match="query-boundary"):
        analysis.recovery_case_curve(case)


def test_actions_weight_cases_equally_and_use_actual_allocation():
    response = {"decision": {"memory": "reevaluate", "radius_scale": 1.5, "reset_velocity": False},
                "relocated_indices": [0, 1, 2, 3], "observation": {"swarm_size": 5}, "completed": False}
    first = analysis.action_summary({"response_log": [response] * 100})
    second_response = deepcopy(response)
    second_response["decision"]["reset_velocity"] = True
    second = analysis.action_summary({"response_log": [second_response]})
    missing = analysis.action_summary({"response_log": []})
    summary = analysis.mean_actions([first, second, missing])
    assert [row["probability"] for row in summary["equal_case_joint_actions"]] == [.5, .5]
    assert summary["no_response_cases"] == 1
    assert first["incomplete_responses"] == 100
    assert first["joint_actions"][0]["count"] == 4
    response["requested_count"] = 3
    with pytest.raises(ValueError, match="Requested count"):
        analysis.action_summary({"response_log": [response]})


def test_pairing_rejects_changed_landscape_and_uncharged_queries():
    reference = {"config": {"budget": 100000}, "evaluations": 100000,
                 "evaluation_counts": {"particle": 100000}, "offline_error": 1.,
                 "initial_environment": {"sha256": "same"}, "environment_changes": []}
    candidate = deepcopy(reference)
    candidate["initial_environment"]["sha256"] = "different"
    with pytest.raises(ValueError, match="environmental histories"):
        analysis.validate_pair(reference, candidate)
    candidate = deepcopy(reference)
    candidate["evaluation_counts"]["particle"] -= 1
    with pytest.raises(ValueError, match="accounting"):
        analysis.validate_pair(reference, candidate)


def test_pilot_descriptive_bootstrap_retains_paired_sign_and_fixed_regime_weights():
    configs = [{"move_severity": severity, "period": period} for severity in (1, 3) for period in (2500, 5000) for _ in range(2)]
    result = analysis.paired_effect([-1.] * 8, configs, pilot=True)
    assert result["descriptive_bootstrap_95_percent_interval"] == [-1., -1.]
    assert result["improved_cases"] == 8
    assert analysis.PILOT_BOOTSTRAP_RESAMPLES == 2000
