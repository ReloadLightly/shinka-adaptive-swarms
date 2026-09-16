"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Continuously taper relocation radius as existing spatial spread grows."""
    swarm_size = int(observation["swarm_size"])
    default_radius = max(float(observation["default_radius"]), 1e-12)
    diameter = max(0.0, float(observation["swarm_diameter"]))
    reference_diameter = 4.5 * default_radius
    compactness = reference_diameter / (reference_diameter + diameter)
    radius_scale = 1.0 + 0.25 * compactness
    return {
        "count": max(0, min(swarm_size, 4)),
        "radius_scale": float(radius_scale),
    }
# EVOLVE-BLOCK-END
