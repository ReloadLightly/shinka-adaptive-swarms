"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Relocate four particles with selectively expanded radius.
    Non-relocated particles continue ordinary PSO motion. The fixed adapter
    reevaluates personal memories and retains velocities.
    """
    count = min(4, int(observation["swarm_size"]))
    radius_scale = 1.25
    if (
        observation["relative_fitness_drop"] > 0.1
        and observation["swarm_diameter"]
        < 2.0 * observation["default_radius"]
    ):
        radius_scale = 1.5
    return {"count": count, "radius_scale": radius_scale}
# EVOLVE-BLOCK-END
