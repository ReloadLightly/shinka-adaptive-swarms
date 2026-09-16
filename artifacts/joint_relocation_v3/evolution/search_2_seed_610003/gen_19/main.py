"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Allocate relocation using existing spread and observed fitness loss."""
    swarm_size = int(observation["swarm_size"])
    diameter = max(0.0, float(observation["swarm_diameter"]))
    reference_diameter = 3.0 * max(
        0.0, float(observation["default_radius"])
    )
    fitness_loss = max(
        0.0, float(observation["relative_fitness_drop"])
    )
    # Coverage reserve grows smoothly from zero beyond the reference diameter.
    # Its squared ratio makes the decision depend jointly on spread and loss.
    coverage_reserve = 0.0
    if diameter > reference_diameter:
        coverage_reserve = 1.0 - (reference_diameter / diameter) ** 2
    # Broad swarms can retain two particles for ordinary PSO motion.
    # The tolerated loss approaches 10% as the coverage reserve increases.
    count = 4
    if coverage_reserve > 0.0 and fitness_loss <= 0.10 * coverage_reserve:
        count = 3
    return {
        "count": min(count, swarm_size),
        "radius_scale": 1.5,
    }
# EVOLVE-BLOCK-END
