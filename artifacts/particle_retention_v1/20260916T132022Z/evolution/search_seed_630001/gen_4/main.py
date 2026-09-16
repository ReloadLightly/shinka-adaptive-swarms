"""Retain the strongest refreshed personal-best particle for ordinary PSO."""

# EVOLVE-BLOCK-START
def retention_priority(particle_features, swarm_features) -> float:
    """Prefer low integrated distance along a damped inertial trajectory."""
    distance = float(particle_features["distance_to_best_normalized"])
    travel = 0.73 * float(particle_features["speed_normalized"])
    alignment = max(
        -1.0, min(1.0, float(particle_features["velocity_alignment"]))
    )
    # Scale before squaring to avoid overflow.
    scale = max(1.0, distance, travel)
    d = distance / scale
    v = travel / scale
    # Integral over t in [0, 1] of squared distance:
    # d*d - alignment*d*v + v*v/3.
    # This equivalent nonnegative form avoids cancellation.
    radial_midpoint = d - 0.5 * alignment * v
    path_energy = radial_midpoint * radial_midpoint + (
        (1.0 - alignment * alignment) / 4.0 + 1.0 / 12.0
    ) * v * v
    rms_distance = scale * path_energy ** 0.5
    return 1.0 / (1.0 + rms_distance)
# EVOLVE-BLOCK-END
