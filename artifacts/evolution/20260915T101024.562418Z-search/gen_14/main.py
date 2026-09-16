"""Book/DEAP response policy: relocate every particle after a detected change.

This file is the evolvable program. The simulator, objective, search cases, and
evaluation budget remain outside it. The policy receives observations available
to the optimizer; inspecting hidden landscape state is outside the task contract.
"""


# EVOLVE-BLOCK-START
def choose_response(observation: dict) -> dict:
    """Bound relocation while preserving useful spatial and velocity memory."""
    def number(key, default=0.0):
        try:
            value = float(observation.get(key, default))
        except (TypeError, ValueError, OverflowError):
            return default
        if value != value or value in (float("inf"), -float("inf")):
            return default
        return value
    def clamp(value, lower, upper):
        return max(lower, min(upper, value))
    default_radius = max(0.0, number("default_radius"))
    diameter = max(0.0, number("swarm_diameter"))
    fitness_scale = max(1.0, abs(number("previous_best_fitness")))
    relative_drop = max(
        0.0,
        number(
            "relative_fitness_drop",
            max(0.0, number("fitness_drop")) / fitness_scale,
        ),
    )
    recent_gain = max(0.0, number("recent_improvement")) / fitness_scale
    # Deterioration below 3% is mild; 18% saturates response strength.
    severity = clamp((relative_drop - 0.03) / 0.15, 0.0, 1.0)
    # Improvement of at least 1% argues for preserving the current search.
    progress = clamp(recent_gain / 0.01, 0.0, 1.0)
    radius_scale = 0.85 + severity * (0.65 - 0.25 * progress)
    # Mild deterioration gets one scout, preserving four spatial anchors.
    # Stronger deterioration still relocates three of the five particles.
    if severity < 0.25:
        fraction = 0.2
    else:
        fraction = 0.6
    response_radius = default_radius * radius_scale
    # A broad swarm already supplies exploration: move fewer particles.
    if response_radius > 0.0 and diameter >= 4.0 * response_radius:
        fraction = max(0.2, fraction - 0.2)
        radius_scale = min(radius_scale, 1.1)
    # Recent progress can reduce relocation, never increase it.
    if progress >= 1.0 and severity < 0.75:
        fraction = min(fraction, 0.4)
    return {
        "radius_scale": radius_scale,
        "fraction": fraction,
        "memory": "reevaluate",
        "reset_velocity": False,
    }
# EVOLVE-BLOCK-END
