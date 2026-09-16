"""Scientific display checks; no candidate or simulator execution."""
import numpy as np
import pytest

from adaptive_swarms.joint_figures import (
    _case_pairs, _regime_key, _state, action_pair, interval, pair_histogram, summarize_pairs,
)


def test_joint_histogram_keeps_zero_and_radius_boundaries_separate():
    pairs = [(0, 0.), (1, .5), (2, 1.), (3, 2.), (4, 4.), (5, 4.01)]
    actual = pair_histogram(pairs)
    np.testing.assert_array_equal(actual, np.eye(6) / 6)
    assert pair_histogram([]) is None


def test_joint_mixture_weights_cases_not_number_of_responses():
    result = summarize_pairs([[(0, 0.)] * 10, [(5, 1.)], []])
    assert result["independent_cases"] == 3
    assert result["no_response_cases"] == 1
    assert result["histogram"][0][0] == .5
    assert result["histogram"][5][2] == .5
    assert [entry["probability"] for entry in result["exact_pairs"]] == [.5, .5]


def test_interval_never_labels_95_percent_bounds_as_975():
    with pytest.raises(KeyError):
        interval({"interval_level": .975, "bootstrap_95_percent_interval": [-1., 2.]})
    assert interval({"interval_level": .975, "bootstrap_interval": [-1., 2.]}) == (.975, [-1., 2.])


def test_action_audit_distinguishes_allocated_from_encoding_fraction():
    response = {"requested_count": 3, "allocated_count": 3, "requested_radius_scale": 2.,
                "relocated_indices": [0, 1, 2], "observation": {"swarm_size": 5},
                "allocated_fraction": .6, "adapter_encoding_fraction": .5}
    assert action_pair(response) == (3, 2.)
    response["allocated_fraction"] = .5
    with pytest.raises(ValueError, match="Allocated fraction"):
        action_pair(response)


def test_state_diameter_denominator_is_known_before_current_action():
    response = {"observation": {"swarm_diameter": 20., "default_radius": 2.},
                "requested_radius_scale": 100.}
    assert _state(response, "relative_diameter") == 10.
    assert _regime_key((1., 2500)) == "dimension=5; npeaks=10; period=2500; move_severity=1; correlation=0"


def test_action_figures_retain_explicit_nominal_constant_alias_radius():
    response = {"requested_count": 0, "requested_radius_scale": .5}
    case = {"config": {"particles_per_swarm": 5}, "response_log": [response],
            "analysis_method_metadata": {"kind": "fixed", "count": 0, "radius_scale": 4.}}
    assert _case_pairs(case) == [(0, 4.)]
    assert response["requested_radius_scale"] == .5
    case["response_log"] = []
    assert _case_pairs(case) == []
