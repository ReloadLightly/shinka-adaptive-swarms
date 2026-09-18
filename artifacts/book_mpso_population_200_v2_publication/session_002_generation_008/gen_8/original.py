"""Reconstructed MPSO 5+1: maintain five neutral particles."""

# EVOLVE-BLOCK-START
def choose_neutral_count(observation) -> int:
    """Choose two or three neutrals using workload-adjusted loss hysteresis."""
    # Estimate movement and detection queries per optimizer sweep.
    loss = max(0.0, observation["relative_fitness_drop"])
    swarms = max(1, observation["swarm_count"])
    sweep_queries = max(
        1.0, observation["total_particle_count"] + swarms
    )
    # Raise the evidence required for growth, with a bounded workload penalty.
    recovery_pressure = loss / (1.0 + min(sweep_queries, 120.0) / 160.0)
    # History is supplied by the caller; no state is retained here.
    threshold = (
        0.04 if observation["previous_requested_target"] == 3 else 0.08
    )
    return 3 if recovery_pressure > threshold else 2
# EVOLVE-BLOCK-END