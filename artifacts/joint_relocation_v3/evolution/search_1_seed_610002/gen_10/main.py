"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Test three relocations for moderate loss and four for larger loss."""
    swarm_size = int(observation["swarm_size"])
    count = 3 if observation["relative_fitness_drop"] <= 0.1 else 4
    radius_scale = 1.0
    return {
        "count": max(0, min(swarm_size, count)),
        "radius_scale": radius_scale,
    }
# EVOLVE-BLOCK-END
