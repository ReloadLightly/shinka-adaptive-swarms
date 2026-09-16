"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Relocate three particles at a constant radius multiplier of 1.25.
    Non-relocated particles continue ordinary PSO motion. The fixed adapter
    reevaluates personal memories and retains velocities.
    """
    count = min(3, int(observation["swarm_size"]))
    radius_scale = 1.25
    return {"count": count, "radius_scale": radius_scale}
# EVOLVE-BLOCK-END
