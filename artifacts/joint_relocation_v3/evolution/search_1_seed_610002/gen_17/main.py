"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Reduce relocation only within a moderate observed spread range."""
    swarm_size = int(observation["swarm_size"])
    default_radius = max(float(observation["default_radius"]), 1e-12)
    relative_spread = float(observation["swarm_diameter"]) / default_radius
    count = 3 if 4.0 < relative_spread <= 8.0 else 4
    return {
        "count": max(0, min(swarm_size, count)),
        "radius_scale": 1.25,
    }
# EVOLVE-BLOCK-END
