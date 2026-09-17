"""Reconstructed MPSO 5+1: maintain five neutral particles."""

# EVOLVE-BLOCK-START
def choose_neutral_count(observation) -> int:
    """Request two or three neutrals from loss remaining after refresh."""
    previous_best = observation["previous_best_fitness"]
    remaining_loss = max(
        0.0,
        (previous_best - observation["current_best_fitness"])
        / max(1.0, abs(previous_best)),
    )
    loss = min(
        max(0.0, observation["relative_fitness_drop"]), remaining_loss
    )
    swarms = max(1, observation["swarm_count"])
    sweep_queries = max(1.0, observation["total_particle_count"] + swarms)
    threshold = (
        0.04 if observation["previous_requested_target"] == 3 else 0.08
    )
    if loss > threshold * (1.0 + sweep_queries / 160.0):
        return 3
    return 2
# EVOLVE-BLOCK-END
