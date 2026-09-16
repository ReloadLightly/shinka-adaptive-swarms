"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Select relocation intensity from observed loss and recent improvement."""
    swarm_size = int(observation["swarm_size"])
    loss = observation["fitness_drop"]
    recent_gain = max(observation["recent_improvement"], 0.0)
    # Assess whether observed deterioration exceeds recent progress.
    uncovered_loss = loss > recent_gain
    substantial_loss = observation["relative_fitness_drop"] > 0.1
    # Preserve ordinary PSO motion for more particles after smaller losses.
    if uncovered_loss and substantial_loss:
        requested_count = swarm_size
    elif uncovered_loss:
        requested_count = 4
    else:
        requested_count = 3
    return {
        "count": min(requested_count, swarm_size),
        "radius_scale": 1.5,
    }
# EVOLVE-BLOCK-END
