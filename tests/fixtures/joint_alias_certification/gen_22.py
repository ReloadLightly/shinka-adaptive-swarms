"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Allocate up to four particles at the midpoint of parental radii."""
    return {
        "count": min(4, int(observation["swarm_size"])),
        "radius_scale": 1.21875,
    }
# EVOLVE-BLOCK-END
