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
"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Allocate up to four particles with an intermediate constant radius.
    The fixed adapter reevaluates memories and retains velocities.
    Non-relocated particles continue ordinary PSO motion.
    """
    count = min(4, int(observation["swarm_size"]))
    return {"count": count, "radius_scale": 1.375}
# EVOLVE-BLOCK-END

```

**PROPOSED CODE:**
```python
"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Allocate up to three particles at a constant radius multiplier of 1.25.
    Use only public observations and deterministic computation. Personal
    memories are reevaluated and velocities retained by the fixed adapter.
    Non-relocated particles continue ordinary PSO motion.
    """
    count = min(3, int(observation["swarm_size"]))
    radius_scale = 1.25
    return {"count": count, "radius_scale": radius_scale}
# EVOLVE-BLOCK-END

```

Are these codes meaningfully different? Respond with NOVEL or NOT_NOVEL followed by your explanation.
