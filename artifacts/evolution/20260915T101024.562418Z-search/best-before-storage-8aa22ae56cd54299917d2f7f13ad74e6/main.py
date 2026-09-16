"""Book/DEAP response policy: relocate every particle after a detected change.

This file is the evolvable program. The simulator, objective, search cases, and
evaluation budget remain outside it. The policy receives observations available
to the optimizer; inspecting hidden landscape state is outside the task contract.
"""


# EVOLVE-BLOCK-START
def choose_response(observation: dict) -> dict:
    """Choose a relocation response using optimizer-visible observations.

    Inputs include dimension, bounds_width, swarm_size, swarm_count,
    swarm_diameter, previous_best_fitness, current_best_fitness, fitness_drop,
    relative_fitness_drop, recent_improvement, evaluations_since_response,
    previous_response_radius, default_radius, observed_best_displacement,
    and evals_remaining. All observations are supplied by the fixed simulator.

    radius_scale multiplies default_radius; fraction controls relocation;
    memory is 'reevaluate' or 'reset'; reset_velocity must be a bool.
    """
    drop = max(0.0, float(observation["relative_fitness_drop"]))
    default_radius = max(0.0, float(observation["default_radius"]))
    diameter = max(0.0, float(observation["swarm_diameter"]))
    # Preserve most particles after mild changes; widen recovery as loss grows.
    if drop <= 0.03:
        radius_scale, fraction = 0.75, 0.4
    elif drop < 0.15:
        radius_scale, fraction = 1.5, 0.6
    else:
        radius_scale, fraction = 2.5, 0.8
    # Existing spatial coverage reduces the need to relocate more particles.
    if drop < 0.15 and diameter > 4.0 * default_radius:
        fraction = 0.4
    return {
        "radius_scale": radius_scale,
        "fraction": fraction,
        "memory": "reevaluate",
        "reset_velocity": False,
    }
# EVOLVE-BLOCK-END
