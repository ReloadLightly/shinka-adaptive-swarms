"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Choose allocation by normalized diameter at a fixed radius multiplier."""
    q = observation["swarm_diameter"] / max(
        observation["default_radius"], 1e-12
    )
    count = 3 if q > 4.0 else 4
    return {
        "count": max(0, min(count, int(observation["swarm_size"]))),
        "radius_scale": 1.25,
    }
# EVOLVE-BLOCK-END
