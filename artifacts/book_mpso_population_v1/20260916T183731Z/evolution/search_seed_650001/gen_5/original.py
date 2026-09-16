"""Reconstructed MPSO 5+1: maintain five neutral particles."""

# EVOLVE-BLOCK-START
def choose_neutral_count(observation) -> int:
    radius = max(observation["default_radius"], 1e-12)
    previous_best = observation["previous_best_fitness"]
    refreshed_loss = previous_best - observation["current_best_fitness"]
    if (
        refreshed_loss > 0.05 * max(1.0, abs(previous_best))
        and observation["neutral_diameter"] <= 2.0 * radius
        and observation["mean_neutral_distance_to_best"] <= radius
        and observation["mean_neutral_speed"] <= radius
    ):
        return 6
    return 5
# EVOLVE-BLOCK-END
