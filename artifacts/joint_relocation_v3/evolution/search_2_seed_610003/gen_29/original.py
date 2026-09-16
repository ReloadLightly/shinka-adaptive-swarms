"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Relocate up to four particles at 1.5 times the default radius."""
    count = min(4, int(observation["swarm_size"]))
    return {"count": count, "radius_scale": 1.5}
# EVOLVE-BLOCK-END
