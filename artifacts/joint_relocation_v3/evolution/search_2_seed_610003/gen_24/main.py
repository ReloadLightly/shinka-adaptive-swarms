"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Trade relocation breadth for more samples at fixed radial effort."""
    swarm_size = int(observation["swarm_size"])
    base_count = min(4, swarm_size)
    count = base_count
    compact = (
        observation["swarm_diameter"]
        <= 3.0 * observation["default_radius"]
    )
    substantial_loss = observation["relative_fitness_drop"] > 0.0875
    if compact and substantial_loss:
        count = min(base_count + 1, swarm_size)
    # Uniform-volume sampling has expected squared radius proportional
    # to radius_scale**2 at fixed dimension.
    radius_scale = 1.5
    if count > 0:
        radius_scale *= (base_count / count) ** 0.5
    return {
        "count": count,
        "radius_scale": float(radius_scale),
    }
# EVOLVE-BLOCK-END
