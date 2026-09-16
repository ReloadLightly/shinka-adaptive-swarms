"""Published MPSO 5+1 temporary-conversion schedule."""

# EVOLVE-BLOCK-START
def choose_temporary_quantum_count(observation) -> int:
    return 3 if observation["change_detected"] else 0
# EVOLVE-BLOCK-END
