"""Retain the strongest refreshed personal-best particle for ordinary PSO."""

# EVOLVE-BLOCK-START
def retention_priority(particle_features, swarm_features) -> float:
    distance = particle_features["distance_to_best_normalized"]
    speed = particle_features["speed_normalized"]
    return 1.0 / (1.0 + distance + speed)
# EVOLVE-BLOCK-END
