"""Retain the strongest refreshed personal-best particle for ordinary PSO."""

# EVOLVE-BLOCK-START
def retention_priority(particle_features, swarm_features) -> float:
    """Prefer proximity and low speed with separately compressed penalties."""
    distance = max(0.0, float(particle_features["distance_to_best_normalized"]))
    speed = max(0.0, float(particle_features["speed_normalized"]))
    return 1.0 / (1.0 + distance ** 0.5 + speed ** 0.5)
# EVOLVE-BLOCK-END
