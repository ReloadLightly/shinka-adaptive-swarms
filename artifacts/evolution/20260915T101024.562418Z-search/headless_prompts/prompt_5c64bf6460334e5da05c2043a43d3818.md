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

Analyze the current program to identify its key parameters and algorithmic components, then design a new algorithm with different parameter settings and configurations.
You MUST respond using a short summary name, description and the full code:

<NAME>
A shortened name summarizing the code you are proposing. Lowercase, no 
spaces, underscores allowed.
</NAME>

<DESCRIPTION>
Identify the key parameters in the current approach and explain how your new parameter choices or algorithmic configuration will lead to better performance.
</DESCRIPTION>

<CODE>
```{language}
# The new parametric algorithm implementation here.
```
</CODE>

* Keep the markers "EVOLVE-BLOCK-START" and "EVOLVE-BLOCK-END" in the code.
* Identify parameters like: learning rates, iteration counts, thresholds, weights, selection criteria, etc.
* Design a new algorithm with different parameter values or configurations.
* Consider adaptive parameters, different optimization strategies, or alternative heuristics.
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
    """Adapt relocation to observed deterioration and search geometry."""
    def number(key, default=0.0):
        try:
            value = float(observation.get(key, default))
        except (TypeError, ValueError, OverflowError):
            return default
        if value != value or value in (float("inf"), -float("inf")):
            return default
        return value
    def clamp(value, lower, upper):
        return max(lower, min(upper, value))
    default_radius = max(0.0, number("default_radius"))
    diameter = max(0.0, number("swarm_diameter"))
    fitness_scale = max(1.0, abs(number("previous_best_fitness")))
    relative_drop = max(
        0.0,
        number(
            "relative_fitness_drop",
            max(0.0, number("fitness_drop")) / fitness_scale,
        ),
    )
    recent_gain = max(0.0, number("recent_improvement")) / fitness_scale
    # Changes below 2% receive a restrained response; 20% saturates it.
    severity = clamp((relative_drop - 0.02) / 0.18, 0.0, 1.0)
    radius_scale = 0.75 + 1.25 * severity
    # Best-position movement is a bounded recovery cue, not a peak location.
    if default_radius > 0.0:
        displacement_ratio = (
            max(0.0, number("observed_best_displacement")) / default_radius
        )
        radius_scale = max(
            radius_scale,
            severity * clamp(displacement_ratio, 0.0, 2.0),
        )
    response_radius = default_radius * radius_scale
    compact = diameter <= response_radius
    dispersed = diameter >= 4.0 * max(response_radius, 1e-12)
    if severity < 0.25:
        fraction = 0.4
    elif severity < 0.75:
        fraction = 0.6
    else:
        fraction = 1.0 if compact else 0.8
    # Existing spatial coverage supplies some of the desired exploration.
    if dispersed:
        fraction = max(0.4, fraction - 0.2)
    stalled = recent_gain <= 0.005
    reset_velocity = bool(severity >= 0.75 and compact and stalled)
    return {
        "radius_scale": radius_scale,
        "fraction": fraction,
        "memory": "reevaluate",
        "reset_velocity": reset_velocity,
    }
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.28
mean_offline_error: 2.55; worst_case_offline_error: 3.73; case_error_std: 1.17; cases_completed: 4

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.508574; mean error remaining at interval end 2.01483; detection used 15.45% and memory refresh 0.40% of objective evaluations; 40 responses with mean radius 0.64686 and relocated fraction 0.59. case_001 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.008797; mean error remaining at interval end 1.49319; detection used 15.92% and memory refresh 0.67% of objective evaluations; 67 responses with mean radius 0.724612 and relocated fraction 0.674627. case_002 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 0.965605; mean error remaining at interval end 0.00407116; detection used 15.85% and memory refresh 0.52% of objective evaluations; 52 responses with mean radius 2.34862 and relocated fraction 0.680769. case_003 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.727854; mean error remaining at interval end 2.48601; detection used 15.83% and memory refresh 0.45% of objective evaluations; 45 responses with mean radius 2.55334 and relocated fraction 0.791111. Largest tracking error: case_003. Examine relocation radius, fraction, and memory response to observable change severity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.

```python
"""Book/DEAP response policy: relocate every particle after a detected change.

This file is the evolvable program. The simulator, objective, search cases, and
evaluation budget remain outside it. The policy receives observations available
to the optimizer; inspecting hidden landscape state is outside the task contract.
"""


# EVOLVE-BLOCK-START
def choose_response(observation: dict) -> dict:
    """Bound relocation while preserving useful spatial and velocity memory."""
    def number(key, default=0.0):
        try:
            value = float(observation.get(key, default))
        except (TypeError, ValueError, OverflowError):
            return default
        if value != value or value in (float("inf"), -float("inf")):
            return default
        return value
    def clamp(value, lower, upper):
        return max(lower, min(upper, value))
    default_radius = max(0.0, number("default_radius"))
    diameter = max(0.0, number("swarm_diameter"))
    fitness_scale = max(1.0, abs(number("previous_best_fitness")))
    relative_drop = max(
        0.0,
        number(
            "relative_fitness_drop",
            max(0.0, number("fitness_drop")) / fitness_scale,
        ),
    )
    recent_gain = max(0.0, number("recent_improvement")) / fitness_scale
    # Deterioration below 3% is mild; 18% saturates response strength.
    severity = clamp((relative_drop - 0.03) / 0.15, 0.0, 1.0)
    # Improvement of at least 1% argues for preserving the current search.
    progress = clamp(recent_gain / 0.01, 0.0, 1.0)
    radius_scale = 0.85 + severity * (0.65 - 0.25 * progress)
    # Preserve two spatial anchors even after a large fitness drop:
    # deterioration alone does not establish how far the peak moved.
    if severity < 0.25:
        fraction = 0.4
    else:
        fraction = 0.6
    response_radius = default_radius * radius_scale
    # A broad swarm already supplies exploration: move fewer particles.
    if response_radius > 0.0 and diameter >= 4.0 * response_radius:
        fraction = max(0.4, fraction - 0.2)
        radius_scale = min(radius_scale, 1.1)
    # Successful recent search warrants a similarly restrained response.
    if progress >= 1.0 and severity < 0.75:
        fraction = 0.4
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
mean_offline_error: 1.98; worst_case_offline_error: 2.62; case_error_std: 0.73; cases_completed: 4

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.510841; mean error remaining at interval end 1.91761; detection used 15.41% and memory refresh 0.40% of objective evaluations; 40 responses with mean radius 0.543421 and relocated fraction 0.47. case_001 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.710274; mean error remaining at interval end 0.730099; detection used 15.92% and memory refresh 0.61% of objective evaluations; 61 responses with mean radius 0.580068 and relocated fraction 0.504918. case_002 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 1.061813; mean error remaining at interval end 0.091079; detection used 15.94% and memory refresh 0.50% of objective evaluations; 50 responses with mean radius 1.84036 and relocated fraction 0.532. case_003 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.624288; mean error remaining at interval end 1.50752; detection used 15.84% and memory refresh 0.48% of objective evaluations; 48 responses with mean radius 1.95161 and relocated fraction 0.545833. Largest tracking error: case_003. Examine relocation radius, fraction, and memory response to observable change severity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


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
    """Bound relocation while preserving useful spatial and velocity memory."""
    def number(key, default=0.0):
        try:
            value = float(observation.get(key, default))
        except (TypeError, ValueError, OverflowError):
            return default
        if value != value or value in (float("inf"), -float("inf")):
            return default
        return value
    def clamp(value, lower, upper):
        return max(lower, min(upper, value))
    default_radius = max(0.0, number("default_radius"))
    diameter = max(0.0, number("swarm_diameter"))
    fitness_scale = max(1.0, abs(number("previous_best_fitness")))
    relative_drop = max(
        0.0,
        number(
            "relative_fitness_drop",
            max(0.0, number("fitness_drop")) / fitness_scale,
        ),
    )
    recent_gain = max(0.0, number("recent_improvement")) / fitness_scale
    # Deterioration below 3% is mild; 18% saturates response strength.
    severity = clamp((relative_drop - 0.03) / 0.15, 0.0, 1.0)
    # Improvement of at least 1% argues for preserving the current search.
    progress = clamp(recent_gain / 0.01, 0.0, 1.0)
    radius_scale = 0.85 + severity * (0.65 - 0.25 * progress)
    # With five particles, retain at least one particle even after large drops.
    if severity < 0.25:
        fraction = 0.4
    elif severity < 0.75:
        fraction = 0.6
    else:
        fraction = 0.8
    response_radius = default_radius * radius_scale
    # A broad swarm already supplies exploration: move fewer particles.
    if response_radius > 0.0 and diameter >= 4.0 * response_radius:
        fraction = max(0.4, fraction - 0.2)
        radius_scale = min(radius_scale, 1.1)
    # Successful recent search warrants a similarly restrained response.
    if progress >= 1.0 and severity < 0.75:
        fraction = 0.4
    return {
        "radius_scale": radius_scale,
        "fraction": fraction,
        "memory": "reevaluate",
        "reset_velocity": False,
    }
# EVOLVE-BLOCK-END

```

Here are the performance metrics of the program:

Combined score to maximize: 0.30
mean_offline_error: 2.31; worst_case_offline_error: 3.76; case_error_std: 1.16; cases_completed: 4

Here is additional text feedback about the current program:

Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.502855; mean error remaining at interval end 1.91068; detection used 15.49% and memory refresh 0.38% of objective evaluations; 38 responses with mean radius 0.556515 and relocated fraction 0.573684. case_001 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.983292; mean error remaining at interval end 0.530828; detection used 15.91% and memory refresh 0.69% of objective evaluations; 69 responses with mean radius 0.587476 and relocated fraction 0.597101. case_002 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 0.979903; mean error remaining at interval end 0.00679846; detection used 15.87% and memory refresh 0.51% of objective evaluations; 51 responses with mean radius 1.83378 and relocated fraction 0.631373. case_003 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.755373; mean error remaining at interval end 2.44706; detection used 15.85% and memory refresh 0.49% of objective evaluations; 49 responses with mean radius 1.94168 and relocated fraction 0.681633. Largest tracking error: case_003. Examine relocation radius, fraction, and memory response to observable change severity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


# Task

Rewrite the program to improve its performance on the specified metrics.
Provide the complete new program code.

IMPORTANT: Make sure your rewritten program maintains the same inputs and outputs as the original program, but with improved internal implementation.
