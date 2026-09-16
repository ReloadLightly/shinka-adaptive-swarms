"""Retain the strongest refreshed personal-best particle for ordinary PSO."""

# EVOLVE-BLOCK-START
def retention_priority(particle_features, swarm_features) -> float:
    """Favor proximity after a damped inertial step, before PSO attraction."""
    import math
    position = particle_features["relative_position_normalized"]
    velocity = particle_features["velocity_normalized"]
    projected_distance = math.hypot(
        *(offset + 0.73 * motion for offset, motion in zip(position, velocity))
    )
    return 1.0 / (1.0 + projected_distance)
# EVOLVE-BLOCK-END
