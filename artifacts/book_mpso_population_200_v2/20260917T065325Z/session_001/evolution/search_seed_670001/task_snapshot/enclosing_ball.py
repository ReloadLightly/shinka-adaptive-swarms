"""Deterministic enclosing-ball decision for the chapter's small neutral groups.

The test is whether the minimum enclosing radius is at most ``radius``. We
normalize translated coordinates by that radius and use a relative radius
tolerance of 1e-12 (squared comparisons use ``(1 + 1e-12)**2``). This is an
inclusive numerical boundary convention, not an extra search parameter. Input
coordinates are the existing binary64 particle positions; translation cannot
recover information that was already lost when representing those positions.

Most calls use cheap certificates: a pair farther than twice the radius
proves nonconvergence, while an enclosing ball about a pair midpoint or the
centroid proves convergence. Only ambiguous clouds solve affine support
systems, stopping as soon as an upper or lower certificate is decisive. An
MEB has an affinely independent support of at most dimension + 1 points, so
finite support search is complete for the 2--8 neutral particles here. It is
not performed blindly on every optimizer update.

Every trial center gives an upper bound. Nonnegative barycentric weights give
the dual lower bound sum(i<j) w_i*w_j*||p_i-p_j||**2. This bound remains valid
even if a nearly singular affine solve gives an inaccurate circumcenter:
weights are clipped and renormalized before using it. Neither objective calls
nor random-number draws occur in this module.
"""
from __future__ import annotations

import itertools
import math

import numpy as np


RELATIVE_RADIUS_TOLERANCE = 1e-12
GEOMETRY_VERSION = "neutral_minimum_enclosing_ball_v1"


def enclosing_ball_converged(positions, radius):
    """Whether a ball of ``radius`` encloses every supplied neutral position.

    Radius-zero convergence requires exactly coincident represented positions.
    Nonfinite coordinates or a negative/nonfinite radius fail explicitly. The
    support search uses binary64 least squares with NumPy's default SVD rank
    cutoff; affine-dependent supports are skipped, because a smaller support
    represents their minimum ball. A final upper-bound decision covers the
    numerical boundary when roundoff prevents an earlier certificate.
    """
    radius = float(radius)
    points = tuple(tuple(float(value) for value in point) for point in positions)
    if not math.isfinite(radius) or radius < 0:
        raise ValueError("Enclosing-ball radius must be finite and nonnegative")
    if not points:
        return True
    dimension = len(points[0])
    if not dimension or any(len(point) != dimension or
                            any(not math.isfinite(value) for value in point)
                            for point in points):
        raise ValueError("Enclosing-ball positions must have one finite dimension")
    if radius == 0:
        return all(point == points[0] for point in points)
    if len(points) == 1:
        return True

    # Pure Python avoids a NumPy dispatch for the common far-pair rejection.
    # Translate first so the geometry is insensitive to the coordinate origin.
    scaled = tuple(tuple((value - base) / radius
                         for value, base in zip(point, points[0])) for point in points)
    threshold = (1.0 + RELATIVE_RADIUS_TOLERANCE) ** 2
    farthest, diameter_squared = (0, 1), -1.0
    squared_distances = {}
    for left, right in itertools.combinations(range(len(points)), 2):
        distance_squared = math.fsum((a - b) ** 2 for a, b in
                                     zip(scaled[left], scaled[right]))
        if distance_squared > 4.0 * threshold:
            return False
        squared_distances[left, right] = distance_squared
        if distance_squared > diameter_squared:
            farthest, diameter_squared = (left, right), distance_squared

    def upper_squared(center):
        return max(math.fsum((value - coordinate) ** 2 for value, coordinate in
                             zip(point, center)) for point in scaled)

    midpoint = tuple((a + b) / 2 for a, b in zip(scaled[farthest[0]], scaled[farthest[1]]))
    best_upper = upper_squared(midpoint)
    if best_upper <= threshold:
        return True
    centroid = tuple(math.fsum(point[axis] for point in scaled) / len(points)
                     for axis in range(dimension))
    best_upper = min(best_upper, upper_squared(centroid))
    if best_upper <= threshold:
        return True

    array = np.asarray(scaled, dtype=np.float64)
    # A guard around the lower certificate is conservative: false is returned
    # only when it clears both the declared boundary and a rounding margin.
    rounding_margin = 64 * np.finfo(np.float64).eps * max(len(points), dimension)
    for size in range(3, min(len(points), dimension + 1) + 1):
        for support in itertools.combinations(range(len(points)), size):
            subset = array[list(support)]
            differences = subset[1:] - subset[0]
            rhs = np.einsum("ij,ij->i", differences, differences) / 2.0
            offset, _, rank, _ = np.linalg.lstsq(differences, rhs, rcond=None)
            if rank != size - 1:
                continue
            center = subset[0] + offset
            best_upper = min(best_upper, upper_squared(center))
            if best_upper <= threshold:
                return True

            coefficients = np.linalg.lstsq(differences.T, offset, rcond=None)[0]
            weights = np.maximum(np.r_[1.0 - coefficients.sum(), coefficients], 0.0)
            weights /= weights.sum()
            lower = math.fsum(float(weights[i] * weights[j]) *
                              squared_distances[support[i], support[j]]
                              for i, j in itertools.combinations(range(size), 2))
            if lower > threshold + rounding_margin:
                return False
    return best_upper <= threshold
