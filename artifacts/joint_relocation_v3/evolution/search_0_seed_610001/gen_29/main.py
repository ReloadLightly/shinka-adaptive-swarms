"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Relocate up to four particles using the baseline radius.
    The fixed adapter reevaluates memories and retains velocities.
    Non-relocated particles continue ordinary PSO motion.
    """
    swarm_size = int(observation["swarm_size"])
    return {
        "count": max(0, min(4, swarm_size)),
        "radius_scale": 1.0,
    }
# EVOLVE-BLOCK-END
