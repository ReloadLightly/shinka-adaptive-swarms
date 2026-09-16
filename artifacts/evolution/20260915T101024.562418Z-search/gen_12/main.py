"""Book/DEAP response policy: relocate every particle after a detected change.

This file is the evolvable program. The simulator, objective, search cases, and
evaluation budget remain outside it. The policy receives observations available
to the optimizer; inspecting hidden landscape state is outside the task contract.
"""


# EVOLVE-BLOCK-START
def choose_response(observation: dict) -> dict:
    """Blend recovery demand with anchor preservation using observed coverage."""
    drop = max(0.0, float(observation["relative_fitness_drop"]))
    default_radius = max(0.0, float(observation["default_radius"]))
    diameter = max(0.0, float(observation["swarm_diameter"]))
    # Preserve the stronger parent's smooth response to observed deterioration.
    if drop <= 0.03:
        radius_scale, fraction = 0.75, 0.40
    elif drop < 0.08:
        weight = (drop - 0.03) / 0.05
        radius_scale = 0.75 + weight
        fraction = 0.40 + 0.20 * weight
    elif drop < 0.15:
        weight = (drop - 0.08) / 0.07
        radius_scale = 1.75 + 0.75 * weight
        fraction = 0.60 + 0.20 * weight
    else:
        radius_scale, fraction = 2.50, 0.80
    # Coverage gradually enables the conservative parent's anchor preservation.
    # Avoid dividing by zero when the baseline relocation radius is zero.
    if default_radius > 0.0:
        coverage = min(
            1.0, max(0.0, diameter / default_radius - 4.0) / 4.0
        )
    else:
        coverage = 0.0
    # Even dispersed swarms receive a meaningful response after severe loss.
    # At severe loss the conservative target is radius 2.0, fraction 0.6.
    recovery_priority = min(1.0, max(0.0, (drop - 0.03) / 0.12))
    conservative_radius = 0.75 + 1.25 * recovery_priority
    conservative_fraction = 0.40 + 0.20 * recovery_priority
    radius_scale += coverage * (conservative_radius - radius_scale)
    fraction += coverage * (conservative_fraction - fraction)
    # Small fitness loss can conceal displacement. A compact swarm has
    # little spatial coverage, so retain anchors but broaden its recovery.
    if default_radius > 0.0:
        compactness = max(
            0.0, 1.0 - diameter / (2.0 * default_radius)
        )
        radius_scale += compactness * max(0.0, 2.0 - radius_scale)
        fraction += compactness * max(0.0, 0.60 - fraction)
    return {
        "radius_scale": radius_scale,
        "fraction": fraction,
        "memory": "reevaluate",
        "reset_velocity": False,
    }
# EVOLVE-BLOCK-END
