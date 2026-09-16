"""V2 allocation seed: relocate three particles after a detected change.

The fixed adapter controls radius, memory, velocity, integer validation and
count-to-fraction conversion. The numerical simulator is outside this program.
"""


# EVOLVE-BLOCK-START
def choose_relocation_count(observation: dict) -> int:
    """Apply the strongest measured fixed allocation within swarm bounds."""
    swarm_size = int(observation["swarm_size"])
    return max(0, min(3, swarm_size))
# EVOLVE-BLOCK-END
