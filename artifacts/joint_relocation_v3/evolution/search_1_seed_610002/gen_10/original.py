"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Test wider partial relocation after substantial loss in a compact swarm."""
    swarm_size = int(observation["swarm_size"])
    count = 4
    radius_scale = 1.0
    if (
        observation["relative_fitness_drop"] > 0.1
        and observation["swarm_diameter"] < 2.0 * observation["default_radius"]
    ):
        count = 3
        radius_scale = 1.5
    return {
        "count": max(0, min(swarm_size, count)),
        "radius_scale": radius_scale,
    }
# EVOLVE-BLOCK-END
