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
    return {
        "radius_scale": 1.0,
        "fraction": 1.0,
        "memory": "reevaluate",
        "reset_velocity": False,
    }
# EVOLVE-BLOCK-END
