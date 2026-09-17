# System Instructions

You are an expert code reviewer tasked with determining if two code snippets are meaningfully different from each other.

Your job is to analyze both programs and determine if the proposed code introduces meaningful changes compared to the existing code. Consider:

1. **Algorithmic differences**: Different approaches, logic, or strategies
2. **Structural changes**: Different data structures, control flow, or organization
3. **Functional improvements**: New features, optimizations, or capabilities
4. **Implementation variations**: Different ways of achieving the same goal that could lead to different performance characteristics
5. **Hyperparameter changes**: Different hyperparameters that could lead to different performance characteristics

Ignore trivial differences like:
- Variable name changes
- Minor formatting or style changes
- Comments or documentation changes
- Insignificant refactoring that doesn't change the core logic

Respond with:
- **NOVEL**: If the codes are meaningfully different
- **NOT_NOVEL**: If the codes are essentially the same with only trivial differences

After your decision, provide a brief explanation of your reasoning.

# Previous Messages

[]

# User Request

Please analyze these two code snippets:

**EXISTING CODE:**
```python
"""Reconstructed MPSO 5+1: maintain five neutral particles."""

# EVOLVE-BLOCK-START
def choose_neutral_count(observation) -> int:
    """Choose two or three neutrals using workload-adjusted loss hysteresis."""
    # Estimate movement and detection queries per optimizer sweep.
    loss = max(0.0, observation["relative_fitness_drop"])
    swarms = max(1, observation["swarm_count"])
    sweep_queries = max(
        1.0, observation["total_particle_count"] + swarms
    )
    # Greater existing workload raises the evidence required for growth.
    recovery_pressure = loss / (1.0 + sweep_queries / 160.0)
    # History is supplied by the caller; no state is retained here.
    threshold = (
        0.04 if observation["previous_requested_target"] == 3 else 0.08
    )
    return 3 if recovery_pressure > threshold else 2
# EVOLVE-BLOCK-END

```

**PROPOSED CODE:**
```python
"""Reconstructed MPSO 5+1: maintain five neutral particles."""

# EVOLVE-BLOCK-START
def choose_neutral_count(observation) -> int:
    """Request two or three neutrals from loss remaining after refresh."""
    previous_best = observation["previous_best_fitness"]
    remaining_loss = max(
        0.0,
        (previous_best - observation["current_best_fitness"])
        / max(1.0, abs(previous_best)),
    )
    loss = min(
        max(0.0, observation["relative_fitness_drop"]), remaining_loss
    )
    swarms = max(1, observation["swarm_count"])
    sweep_queries = max(1.0, observation["total_particle_count"] + swarms)
    threshold = (
        0.04 if observation["previous_requested_target"] == 3 else 0.08
    )
    if loss > threshold * (1.0 + sweep_queries / 160.0):
        return 3
    return 2
# EVOLVE-BLOCK-END

```

Are these codes meaningfully different? Respond with NOVEL or NOT_NOVEL followed by your explanation.
