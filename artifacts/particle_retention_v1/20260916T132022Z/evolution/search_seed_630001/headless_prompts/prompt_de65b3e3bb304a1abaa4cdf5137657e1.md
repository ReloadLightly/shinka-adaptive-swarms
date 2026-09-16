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
"""Retain the strongest refreshed personal-best particle for ordinary PSO."""

# EVOLVE-BLOCK-START
def retention_priority(particle_features, swarm_features) -> float:
    distance = particle_features["distance_to_best_normalized"]
    speed = particle_features["speed_normalized"]
    return 1.0 / (1.0 + distance + speed)
# EVOLVE-BLOCK-END

```

**PROPOSED CODE:**
```python
"""Retain the strongest refreshed personal-best particle for ordinary PSO."""

# EVOLVE-BLOCK-START
def retention_priority(particle_features, swarm_features) -> float:
    """Favor proximity with a reduced penalty on retained speed."""
    distance = particle_features["distance_to_best_normalized"]
    speed = particle_features["speed_normalized"]
    speed_weight = 0.5
    return 1.0 / (1.0 + distance + speed_weight * speed)
# EVOLVE-BLOCK-END

```

Are these codes meaningfully different? Respond with NOVEL or NOT_NOVEL followed by your explanation.
