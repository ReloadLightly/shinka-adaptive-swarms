"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Choose partial relocation using publicly observed fitness deterioration."""
    swarm_size = int(observation["swarm_size"])
    relative_drop = float(observation["relative_fitness_drop"])
    count = 3 if relative_drop <= 0.05 else 4
    return {
        "count": max(0, min(swarm_size, count)),
        "radius_scale": 1.25,
    }
# EVOLVE-BLOCK-END
