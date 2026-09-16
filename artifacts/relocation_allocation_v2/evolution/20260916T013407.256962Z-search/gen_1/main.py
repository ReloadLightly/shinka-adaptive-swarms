"""V2 allocation seed: relocate three particles after a detected change.

The fixed adapter controls radius, memory, velocity, integer validation and
count-to-fraction conversion. The numerical simulator is outside this program.
"""


# EVOLVE-BLOCK-START
def choose_relocation_count(observation: dict) -> int:
    """Allocate relocation using public spread and fitness-change observations."""
    swarm_size = int(observation["swarm_size"])
    if swarm_size <= 0:
        return 0
    # Express current spatial coverage relative to the fixed relocation radius.
    radius = max(2.0 * float(observation["default_radius"]), 1e-12)
    coverage = max(0.0, float(observation["swarm_diameter"])) / radius
    # Fitness deterioration is an imperfect signal, not a movement estimate.
    relative_drop = float(observation["relative_fitness_drop"])
    deteriorated = (
        float(observation["fitness_drop"]) > 0.0
        and relative_drop > 0.05
    )
    # Ordered decision table: expand compact swarms that deteriorated;
    # spend fewer relocations when the swarm already has broad coverage.
    allocation_rules = (
        (coverage < 1.0 and deteriorated, 4),
        (coverage >= 2.0, 2),
        (True, 3),
    )
    for applies, count in allocation_rules:
        if applies:
            return min(swarm_size, count)
# EVOLVE-BLOCK-END
