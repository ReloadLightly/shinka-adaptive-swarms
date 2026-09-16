"""Published MPSO 5+1 temporary-conversion schedule."""

# EVOLVE-BLOCK-START
def choose_temporary_quantum_count(observation) -> int:
    if observation["change_detected"]:
        return 3
    if (
        observation["has_detected_change"]
        and 1 <= observation["updates_since_detected_change"] <= 2
    ):
        return 1
    return 0
# EVOLVE-BLOCK-END
