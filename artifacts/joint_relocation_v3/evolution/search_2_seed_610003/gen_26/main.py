"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Continuously adjust relocation radius using loss and existing spread."""
    swarm_size = int(observation["swarm_size"])
    reference_radius = max(1e-12, float(observation["default_radius"]))
    diameter = max(0.0, float(observation["swarm_diameter"]))
    loss = max(0.0, float(observation["relative_fitness_drop"]))
    # Smooth, bounded signals: neither introduces a hard response boundary.
    loss_pressure = 1.0 - 1.0 / (1.0 + loss / 0.075)
    existing_coverage = 1.0 - 1.0 / (
        1.0 + diameter / reference_radius / 3.0
    )
    # Compact, deteriorating swarms receive broader relocation.
    # Broad, stable swarms receive more concentrated relocation.
    radius_scale = 1.5 + 0.5 * (loss_pressure - existing_coverage)
    return {
        "count": min(4, swarm_size),
        "radius_scale": float(radius_scale),
    }
# EVOLVE-BLOCK-END
