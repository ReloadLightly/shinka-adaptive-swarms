"""V2 allocation seed: relocate three particles after a detected change.

The fixed adapter controls radius, memory, velocity, integer validation and
count-to-fraction conversion. The numerical simulator is outside this program.
"""


# EVOLVE-BLOCK-START
def choose_relocation_count(observation: dict) -> int:
    """Relocate four particles, capped by the available swarm size."""
    swarm_size = int(observation["swarm_size"])
    if swarm_size <= 0:
        return 0
    return min(4, swarm_size)
# EVOLVE-BLOCK-END
