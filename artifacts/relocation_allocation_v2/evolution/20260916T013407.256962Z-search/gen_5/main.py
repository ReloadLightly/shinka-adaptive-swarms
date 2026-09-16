"""V2 allocation seed: relocate three particles after a detected change.

The fixed adapter controls radius, memory, velocity, integer validation and
count-to-fraction conversion. The numerical simulator is outside this program.
"""


# EVOLVE-BLOCK-START
def choose_relocation_count(observation: dict) -> int:
    """Default to three; reduce only with broad coverage and improved fitness."""
    swarm_size = int(observation["swarm_size"])
    if swarm_size <= 0:
        return 0
    radius = max(2.0 * float(observation["default_radius"]), 1e-12)
    diameter = max(0.0, float(observation["swarm_diameter"]))
    if (
        diameter >= 2.0 * radius
        and float(observation["fitness_drop"]) < 0.0
    ):
        return min(swarm_size, 2)
    return min(swarm_size, 3)
# EVOLVE-BLOCK-END
