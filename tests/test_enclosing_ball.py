"""Bounded independent geometry checks: zero objective queries/model calls."""
import itertools
import math
import random

import numpy as np
import pytest

from adaptive_swarms.enclosing_ball import (
    RELATIVE_RADIUS_TOLERANCE, enclosing_ball_converged,
)
from adaptive_swarms import book_population, book_population_v2
from adaptive_swarms.population_policy import population_fingerprint as old_fingerprint
from adaptive_swarms.population_policy_v2 import population_fingerprint
from adaptive_swarms.simulator import Particle, Swarm


def reference_radius(points):
    """Independent tiny reference: enumerate enclosing spheres via KKT weights.

    Production solves affine coordinate equations and uses upper/dual decision
    certificates. This deliberately slow reference instead solves the augmented
    Gram system for each subset and minimizes radii of balls enclosing the cloud.
    It is confined to small synthetic fixtures.
    """
    array = np.asarray(points, dtype=float)
    array = array - array[0]
    scale = max(float(np.max(np.abs(array))), 1e-100)
    array /= scale
    best = math.inf
    for size in range(1, min(len(array), array.shape[1] + 1) + 1):
        for subset_ids in itertools.combinations(range(len(array)), size):
            subset = array[list(subset_ids)]
            gram = subset @ subset.T
            matrix = np.block([[2 * gram, np.ones((size, 1))],
                               [np.ones((1, size)), np.zeros((1, 1))]])
            try:
                solution = np.linalg.solve(matrix, np.r_[np.diag(gram), 1.0])
            except np.linalg.LinAlgError:
                continue
            center = solution[:-1] @ subset
            squared = np.sum((array - center) ** 2, axis=1)
            radius_squared = float(np.sum((subset[0] - center) ** 2))
            if np.max(squared) <= radius_squared + 1e-11:
                best = min(best, math.sqrt(max(0.0, radius_squared)))
    assert math.isfinite(best)
    return best * scale


def test_equilateral_counterexample_in_five_dimensions():
    side = 1.9
    points = [[0, 0, 0, 0, 0], [side, 0, 0, 0, 0],
              [side / 2, side * math.sqrt(3) / 2, 0, 0, 0]]
    swarm = Swarm(1, [Particle(point, [0] * 5) for point in points] +
                  [Particle([1e9] * 5, [0] * 5)])
    assert book_population_v2.neutral_diameter(swarm) == pytest.approx(side)
    assert book_population_v2.neutral_diameter(swarm) <= 2
    assert reference_radius(points) == pytest.approx(side / math.sqrt(3))
    assert not enclosing_ball_converged(points, 1)
    assert enclosing_ball_converged(points, side / math.sqrt(3))


@pytest.mark.parametrize("points,expected", [
    ([[3, 2, -1, 7, 8]] * 8, 0),
    ([[i, 0, 0, 0, 0] for i in range(8)], 3.5),
    ([[0, 0, 0, 0, 0], [2, 0, 0, 0, 0]] * 4, 1),
    ([[1, 0, 0, 0, 0], [-1, 0, 0, 0, 0],
      [0, 1, 0, 0, 0], [0, -1, 0, 0, 0]], 1),
])
def test_duplicate_collinear_and_rank_deficient_clouds(points, expected):
    assert reference_radius(points) == pytest.approx(expected, abs=1e-12)
    assert enclosing_ball_converged(points, expected)
    if expected:
        assert not enclosing_ball_converged(points, expected * (1 - 1e-7))
    else:
        assert enclosing_ball_converged(points, 0)


def test_near_boundary_convention_is_explicit():
    points = [[-1, 0, 0, 0, 0], [1, 0, 0, 0, 0]]
    tolerance = RELATIVE_RADIUS_TOLERANCE
    assert enclosing_ball_converged(points, 1)
    assert enclosing_ball_converged(points, 1 - tolerance / 4)
    assert not enclosing_ball_converged(points, 1 - tolerance * 4)
    assert enclosing_ball_converged(points, 1 + tolerance * 4)


@pytest.mark.parametrize("scale,translation", [
    (1e-9, 0), (1e9, 0), (0.01, 1e4), (1, 1e7), (17, -348.2),
])
def test_translation_and_scale_against_independent_reference(scale, translation):
    base = np.asarray([[0, 0, 0, 0, 0], [1.9, 0, 0, 0, 0],
                       [.95, 1.9 * math.sqrt(3) / 2, 0, 0, 0],
                       [.9, .5, 0, 0, 0]])
    points = base * scale + translation
    radius = reference_radius(points)
    assert enclosing_ball_converged(points, radius * (1 + 1e-7))
    assert not enclosing_ball_converged(points, radius * (1 - 1e-7))


def test_bounded_random_clouds_against_independent_reference():
    generator = np.random.default_rng(2026091701)
    for count in range(2, 9):
        for index in range(12):
            points = generator.normal(size=(count, 5))
            if index % 4 == 0:
                points[:, 2:] = 0  # lower-dimensional affine span
            if index % 4 == 1:
                points[-1] = points[0]  # duplicates
            if index % 4 == 2:
                points[:, 2:] *= 1e-11  # nearly rank deficient
            radius = reference_radius(points)
            assert enclosing_ball_converged(points, radius * (1 + 1e-7))
            if radius:
                assert not enclosing_ball_converged(points, radius * (1 - 1e-7))


def test_quick_certificates_skip_affine_solves(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("A quick certificate must avoid support solves")
    monkeypatch.setattr(np.linalg, "lstsq", forbidden)
    assert enclosing_ball_converged([[0, 0], [1, 0], [.5, .1]], 1)
    assert not enclosing_ball_converged([[0, 0], [3, 0], [.5, .1]], 1)


def test_geometry_preserves_global_random_streams_and_engine_identity():
    before_python = random.getstate()
    before_numpy = np.random.get_state()
    enclosing_ball_converged([[0, 0], [1.9, 0], [.95, 1.6]], 1)
    assert random.getstate() == before_python
    after_numpy = np.random.get_state()
    assert before_numpy[0] == after_numpy[0]
    np.testing.assert_array_equal(before_numpy[1], after_numpy[1])
    assert before_numpy[2:] == after_numpy[2:]
    assert book_population_v2.ENGINE_VERSION != book_population.ENGINE_VERSION
    assert population_fingerprint() != old_fingerprint()
    assert "src/adaptive_swarms/enclosing_ball.py" in population_fingerprint()
    assert not hasattr(book_population_v2, "from_compatible_fixed_five_result")


@pytest.mark.parametrize("points,radius", [([[math.nan, 0]], 1), ([[0, 0]], -1),
                                         ([[0, 0]], math.inf), ([[0], [0, 1]], 1)])
def test_invalid_geometry_fails_explicitly(points, radius):
    with pytest.raises(ValueError):
        enclosing_ball_converged(points, radius)
