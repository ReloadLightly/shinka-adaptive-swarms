"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Apply a fixed partial restart with a conservative relocation radius.
    Memory reevaluation and retained velocities remain adapter-controlled.
    Non-relocated particles continue ordinary PSO motion.
    """
    count = min(4, int(observation["swarm_size"]))
    return {"count": count, "radius_scale": 1.25}
# EVOLVE-BLOCK-END
