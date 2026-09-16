"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Choose relocation allocation and radius from public observations."""
    swarm_size = int(observation["swarm_size"])
    fitness_drop = float(observation["fitness_drop"])
    recent_gain = max(0.0, float(observation["recent_improvement"]))
    recovery_state = "default"
    if fitness_drop > 0.0 and recent_gain >= fitness_drop:
        recovery_state = "covered_loss"
    radius_by_state = {
        "default": 1.25,
        "covered_loss": 1.1875,
    }
    return {
        "count": min(4, swarm_size),
        "radius_scale": radius_by_state[recovery_state],
    }
# EVOLVE-BLOCK-END
