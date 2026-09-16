"""V2 allocation seed: relocate three particles after a detected change.

The fixed adapter controls radius, memory, velocity, integer validation and
count-to-fraction conversion. The numerical simulator is outside this program.
"""


# EVOLVE-BLOCK-START
def choose_relocation_count(observation: dict) -> int:
    """Combine tight and broad contraction thresholds by public radius scale."""
    swarm_size = int(observation["swarm_size"])
    if swarm_size <= 0:
        return 0
    default_radius = max(0.0, float(observation["default_radius"]))
    diameter = max(0.0, float(observation["swarm_diameter"]))
    loss = float(observation["fitness_drop"])
    improvement = max(0.0, float(observation["recent_improvement"]))
    threshold = default_radius
    if default_radius > 1.0:
        threshold *= 2.0
    count = 3
    if diameter < threshold and loss > improvement:
        count = 4
    return min(count, swarm_size)
# EVOLVE-BLOCK-END
