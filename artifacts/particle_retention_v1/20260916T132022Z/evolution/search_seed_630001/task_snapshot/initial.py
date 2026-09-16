"""Retain the strongest refreshed personal-best particle for ordinary PSO."""

# EVOLVE-BLOCK-START
def retention_priority(particle_features, swarm_features) -> float:
    return -particle_features["personal_best_rank"]
# EVOLVE-BLOCK-END
