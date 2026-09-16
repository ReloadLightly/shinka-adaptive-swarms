# System Instructions

You are evolving an interpretable response policy for dynamic
multiswarm particle swarm optimization, based on Blackwell's chapter in Swarm
Intelligence: Introduction and Applications and the DEAP multiswarm example.
The fixed simulator performs PSO, exclusion, swarm birth/death, change detection,
and Moving Peaks objective evaluations. Change only the marked evolve block.
Evolve choose_response(observation), using optimizer-visible observations to
select relocation radius_scale, fraction, memory (reevaluate or reset), and
reset_velocity. Baseline relocates all particles around the previous swarm best
with radius 0.5 times benchmark movement severity, retaining velocities and
reevaluating memories. Discover an adaptive, comprehensible rule that tracks
changing peaks better under the same objective-evaluation budget. Lower mean
offline error is better; combined_score=1/(1+mean_offline_error). Use feedback across
cases to reason about when relocation helps and when it destroys useful memory.
Do not import the simulator, read task/results files or hidden landscape state,
access the network, invoke other models, change random seeds, or alter evaluator
behavior. The result must be a reusable policy, not case-specific answers.
Explain the behavioral hypothesis of the proposed change in the patch description.


# Scientific context supplied to mutation

# Scientific context supplied to native program evolution

Source: Blackwell, Branke and Li (2008), [Particle Swarms for Dynamic Optimization
Problems](https://doi.org/10.1007/978-3-540-74089-6_6), pp.193–217, especially §4.2
and §5.1–5.3. Implementation anchor: [DEAP multiswarm.py at
8a96fd3](https://github.com/DEAP/deap/blob/8a96fd3a75026f7b30e835f595a5199c75634ddf/examples/pso/multiswarm.py).
The following is a mechanism summary and research hypothesis, not a quotation.

Several particle swarms search a landscape whose peaks move between intervals.
Within each swarm, attraction to personal and swarm memories concentrates search.
Exclusion avoids redundant swarms occupying the same region; convergence checks
and swarm creation/deletion maintain exploratory capacity. After a detected change,
temporary stochastic particle relocation helps recover the displaced peak. These
mechanisms create a tradeoff between preserving a useful local search and exploring
far enough to recover from change.

Our selected baseline has five neutral particles per swarm, no permanently quantum
particles, and one desired free swarm. It relocates all particles in the affected
swarm with a uniform-volume draw around its remembered best, radius 0.5 times the
configured movement severity, reevaluates memories, and preserves velocities.
The DEAP conversion function's distribution-selector bug is corrected in the
shared simulator. That correction is already part of the baseline, not a discovery.

Evolve only `choose_response(observation)` inside the marked program region. This
hook runs after an observed change is detected for a swarm; it is not called at
every particle step. It returns:

- `radius_scale`: finite nonnegative multiplier of the baseline relocation radius;
- `fraction`: fraction of particles to relocate, between zero and one;
- `memory`: `reevaluate` or `reset`;
- `reset_velocity`: Boolean.

Use only the supplied optimizer observations and ordinary deterministic computation.
Do not inspect files, seeds, evaluator internals, latent peak coordinates, the true
optimum, or held-out cases. Python execution is not a security sandbox: this is the
scientific contract and selected programs will be inspected for compliance.

A testable hypothesis is that a response conditioned on observed fitness
deterioration, swarm dispersion, recent improvement and previous responses can
preserve good search states after small changes while broadening exploration after
large changes. Unconditional relocation can waste useful structure; a narrow
response can fail to recover; memory reset and reevaluation have different costs.
These are hypotheses to investigate, not instructions to force a particular result.

Every objective query counts, including detection and memory reevaluation. The
primary measurement is mean offline error over search cases; lower is better.
Native selection maximizes `1 / (1 + mean_offline_error)`. Use measured per-case
errors and recovery/evaluation-accounting feedback to explain changes. Do not
optimize metadata, exploit result writing, or treat a training gain as independent
evidence. Keep the program interpretable enough for a later mechanism ablation.

Create a novel algorithm that draws inspiration from the provided context programs but implements a fundamentally different approach.
Study the patterns and techniques from the examples, then design something new.
You MUST respond using a short summary name, description and the full code:

<NAME>
A shortened name summarizing the code you are proposing. Lowercase, no spaces, underscores allowed.
</NAME>

<DESCRIPTION>
Explain how you drew inspiration from the context programs and what novel approach you are implementing. Detail the key insights that led to this design.
</DESCRIPTION>

<CODE>
```{language}
# The inspired but novel algorithm implementation here.
```
</CODE>

* Keep the markers "EVOLVE-BLOCK-START" and "EVOLVE-BLOCK-END" in the code.
* Learn from the context programs but don't copy their approaches directly.
* Combine ideas in novel ways or apply insights to different algorithmic paradigms.
* Maintain the same inputs and outputs as the original program.
* Use the <NAME>, <DESCRIPTION>, and <CODE> delimiters to structure your response. It will be parsed afterwards.

# Previous Messages

[]

# User Request

Here are the performance metrics of a set of previously implemented programs:

# Prior programs

```python
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
    return {
        "radius_scale": radius_scale,
        "fraction": fraction,
        "memory": "reevaluate",
        "reset_velocity": False,
    }
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.33
mean_offline_error: 2.03; worst_case_offline_error: 2.68; case_error_std: 0.72; cases_completed: 4

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.410080; mean error remaining at interval end 1.91141; detection used 15.46% and memory refresh 0.40% of objective evaluations; 40 responses with mean radius 0.81068 and relocated fraction 0.57984. case_001 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.001169; mean error remaining at interval end 0.57746; detection used 15.92% and memory refresh 0.66% of objective evaluations; 66 responses with mean radius 0.909257 and relocated fraction 0.636528. case_002 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 1.030198; mean error remaining at interval end 0.0055099; detection used 15.85% and memory refresh 0.50% of objective evaluations; 50 responses with mean radius 3.02978 and relocated fraction 0.673764. case_003 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.682702; mean error remaining at interval end 1.5115; detection used 15.81% and memory refresh 0.43% of objective evaluations; 43 responses with mean radius 3.06115 and relocated fraction 0.683739. Largest tracking error: case_003. Examine relocation radius, fraction, and memory response to observable change severity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.

```python
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

```

Performance metrics:
Combined score to maximize: 0.34
mean_offline_error: 1.97; worst_case_offline_error: 2.96; case_error_std: 0.88; cases_completed: 4

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.466150; mean error remaining at interval end 1.98023; detection used 15.42% and memory refresh 0.40% of objective evaluations; 40 responses with mean radius 1.03912 and relocated fraction 0.647401. case_001 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.308247; mean error remaining at interval end 0.264273; detection used 15.98% and memory refresh 0.67% of objective evaluations; 67 responses with mean radius 1.04927 and relocated fraction 0.671503. case_002 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 1.145215; mean error remaining at interval end 0.00764906; detection used 15.85% and memory refresh 0.51% of objective evaluations; 51 responses with mean radius 3.2789 and relocated fraction 0.696827. case_003 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.961766; mean error remaining at interval end 1.53071; detection used 15.79% and memory refresh 0.46% of objective evaluations; 46 responses with mean radius 3.35105 and relocated fraction 0.717136. Largest tracking error: case_003. Examine relocation radius, fraction, and memory response to observable change severity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


# Current program

Here is the current program we are trying to improve (you will need to propose a new program with the same inputs and outputs as the original program, but with improved internal implementation):

```python
"""Book/DEAP response policy: relocate every particle after a detected change.

This file is the evolvable program. The simulator, objective, search cases, and
evaluation budget remain outside it. The policy receives observations available
to the optimizer; inspecting hidden landscape state is outside the task contract.
"""


# EVOLVE-BLOCK-START
def choose_response(observation: dict) -> dict:
    """Map observed loss to recovery demand, then account for spatial coverage."""
    drop = max(0.0, float(observation["relative_fitness_drop"]))
    default_radius = max(0.0, float(observation["default_radius"]))
    diameter = max(0.0, float(observation["swarm_diameter"]))
    # Each knot specifies (relative loss, radius multiplier, relocation fraction).
    # Interpolation makes recovery demand grow gradually with observed damage.
    schedule = (
        (0.00, 0.75, 0.40),
        (0.03, 0.75, 0.40),
        (0.08, 1.75, 0.60),
        (0.15, 2.50, 0.80),
    )
    radius_scale, fraction = schedule[-1][1:]
    for left, right in zip(schedule, schedule[1:]):
        if drop <= right[0]:
            weight = (drop - left[0]) / (right[0] - left[0])
            weight = min(1.0, max(0.0, weight))
            radius_scale = left[1] + weight * (right[1] - left[1])
            fraction = left[2] + weight * (right[2] - left[2])
            break
    # Spatial coverage can substitute for relocation after modest damage.
    # Fade this allowance as damage grows: dispersion alone does not establish
    # that particles still cover useful regions after a substantial change.
    if diameter > 4.0 * default_radius:
        recovery_priority = min(
            1.0, max(0.0, (drop - 0.03) / (0.15 - 0.03))
        )
        fraction = 0.40 + recovery_priority * (fraction - 0.40)
    return {
        "radius_scale": radius_scale,
        "fraction": fraction,
        "memory": "reevaluate",
        "reset_velocity": False,
    }
# EVOLVE-BLOCK-END

```

Here are the performance metrics of the program:

Combined score to maximize: 0.33
mean_offline_error: 2.00; worst_case_offline_error: 2.68; case_error_std: 0.78; cases_completed: 4

Here is additional text feedback about the current program:

Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.410080; mean error remaining at interval end 1.91141; detection used 15.46% and memory refresh 0.40% of objective evaluations; 40 responses with mean radius 0.85443 and relocated fraction 0.61484. case_001 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.020817; mean error remaining at interval end 0.653333; detection used 15.92% and memory refresh 0.66% of objective evaluations; 66 responses with mean radius 0.92027 and relocated fraction 0.644338. case_002 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 0.903061; mean error remaining at interval end 0.00288841; detection used 15.83% and memory refresh 0.50% of objective evaluations; 50 responses with mean radius 3.13517 and relocated fraction 0.701823. case_003 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.682702; mean error remaining at interval end 1.5115; detection used 15.81% and memory refresh 0.43% of objective evaluations; 43 responses with mean radius 3.14836 and relocated fraction 0.706995. Largest tracking error: case_003. Examine relocation radius, fraction, and memory response to observable change severity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


# Task

Rewrite the program to improve its performance on the specified metrics.
Provide the complete new program code.

IMPORTANT: Make sure your rewritten program maintains the same inputs and outputs as the original program, but with improved internal implementation.
