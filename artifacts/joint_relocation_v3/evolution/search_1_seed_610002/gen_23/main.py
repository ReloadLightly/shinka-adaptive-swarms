"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Relocate four particles, reducing to three for very broad swarms."""
    radius_reference = max(observation["default_radius"], 1e-12)
    count = 3 if observation["swarm_diameter"] > 6.0 * radius_reference else 4
    return {
        "count": min(count, int(observation["swarm_size"])),
        "radius_scale": 1.25,
    }
# EVOLVE-BLOCK-END
