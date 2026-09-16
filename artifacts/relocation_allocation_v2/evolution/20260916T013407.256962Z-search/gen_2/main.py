"""V2 allocation seed: relocate three particles after a detected change.

The fixed adapter controls radius, memory, velocity, integer validation and
count-to-fraction conversion. The numerical simulator is outside this program.
"""


# EVOLVE-BLOCK-START
def choose_relocation_count(observation: dict) -> int:
    """Return an integer from zero through observation['swarm_size'].

    Public state: dimension, bounds_width, swarm_size, swarm_count,
    swarm_diameter, previous_best_fitness, current_best_fitness, fitness_drop,
    relative_fitness_drop, recent_improvement, evaluations_since_response,
    previous_response_radius, default_radius, observed_best_displacement,
    evals_remaining. Signed fitness change is current_best_fitness minus
    previous_best_fitness (fitness_drop has the opposite sign).

    Non-relocated particles still move by ordinary PSO; all personal memories
    are reevaluated. Radius is fixed at twice default_radius, velocity retained.
    """
    return min(2, observation["swarm_size"])
# EVOLVE-BLOCK-END
