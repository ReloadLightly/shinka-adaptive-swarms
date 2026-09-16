"""Reconstructed MPSO 5+1: maintain five neutral particles."""

# EVOLVE-BLOCK-START
def choose_neutral_count(observation) -> int:
    if observation["relative_fitness_drop"] <= -0.05:
        radius = max(observation["default_radius"], 1e-12)
        if (
            observation["neutral_diameter"] <= 2.0 * radius
            and observation["mean_neutral_distance_to_best"] <= radius
            and observation["mean_neutral_speed"] <= radius
        ):
            return 4
    return 5
# EVOLVE-BLOCK-END
