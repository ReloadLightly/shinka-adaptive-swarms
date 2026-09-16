"""Published MPSO 5+1 temporary-conversion schedule."""

# EVOLVE-BLOCK-START
def choose_temporary_quantum_count(observation) -> int:
    if observation["change_detected"]:
        if abs(observation["relative_fitness_drop"]) <= 0.01:
            return 4
        return 5
    return 0
# EVOLVE-BLOCK-END
