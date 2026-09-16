"""Book/DEAP response policy: relocate every particle after a detected change.

This file is the evolvable program. The simulator, objective, search cases, and
evaluation budget remain outside it. The policy receives observations available
to the optimizer; inspecting hidden landscape state is outside the task contract.
"""


# EVOLVE-BLOCK-START
def choose_response(observation: dict) -> dict:
    """Scale recovery by observed fitness loss and existing spatial coverage."""
    drop = max(0.0, float(observation["relative_fitness_drop"]))
    default_radius = max(0.0, float(observation["default_radius"]))
    diameter = max(0.0, float(observation["swarm_diameter"]))
    dispersed = diameter > 4.0 * default_radius
    if drop <= 0.03:
        # Small losses warrant limited disruption of useful search states.
        radius_scale, fraction = 0.75, 0.4
    elif drop < 0.15:
        radius_scale = 1.5
        fraction = 0.4 if dispersed else 0.6
    elif dispersed:
        # Existing coverage permits the conservative parent's response.
        radius_scale, fraction = 2.0, 0.6
    else:
        # Concentrated swarms use the stronger parent's broad recovery.
        radius_scale, fraction = 2.5, 0.8
    return {
        "radius_scale": radius_scale,
        "fraction": fraction,
        "memory": "reevaluate",
        "reset_velocity": False,
    }
# EVOLVE-BLOCK-END
