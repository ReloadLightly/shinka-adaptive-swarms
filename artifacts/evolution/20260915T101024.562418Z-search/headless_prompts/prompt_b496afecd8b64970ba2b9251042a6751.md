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

Redesign the program with a different structural approach while potentially using similar core concepts.
Focus on changing the overall architecture, data flow, or program organization.
You MUST respond using a short summary name, description and the full code:

<NAME>
A shortened name summarizing the code you are proposing. Lowercase, no spaces, underscores allowed.
</NAME>

<DESCRIPTION>
Describe the structural changes you are making and how they improve the program's performance, maintainability, or efficiency.
</DESCRIPTION>

<CODE>
```{language}
# The structurally redesigned program here.
```
</CODE>

* Keep the markers "EVOLVE-BLOCK-START" and "EVOLVE-BLOCK-END" in the code.
* Focus on changing the program's structure: modularization, data flow, control flow, or architectural patterns.
* The core problem-solving approach may be similar but organized differently.
* Ensure the same inputs and outputs are maintained.
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
    """Combine broad recovery with preservation of existing spatial coverage."""
    drop = max(0.0, float(observation["relative_fitness_drop"]))
    default_radius = max(0.0, float(observation["default_radius"]))
    diameter = max(0.0, float(observation["swarm_diameter"]))
    dispersed = diameter > 4.0 * default_radius
    if drop <= 0.03:
        # Mild changes warrant limited disturbance of useful search states.
        radius_scale, fraction = 0.75, 0.4
    elif drop < 0.15:
        radius_scale = 1.5
        fraction = 0.4 if dispersed else 0.6
    else:
        # Keep the stronger parent's reach, while inheriting the other
        # parent's positional anchors when coverage already exists.
        radius_scale = 2.5
        fraction = 0.6 if dispersed else 0.8
    return {
        "radius_scale": radius_scale,
        "fraction": fraction,
        "memory": "reevaluate",
        "reset_velocity": False,
    }
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.28
mean_offline_error: 2.55; worst_case_offline_error: 3.65; case_error_std: 1.12; cases_completed: 4

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.347470; mean error remaining at interval end 1.73749; detection used 15.30% and memory refresh 0.40% of objective evaluations; 40 responses with mean radius 0.75625 and relocated fraction 0.56. case_001 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.651223; mean error remaining at interval end 2.4112; detection used 15.93% and memory refresh 0.62% of objective evaluations; 62 responses with mean radius 0.834677 and relocated fraction 0.606452. case_002 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 1.079715; mean error remaining at interval end 0.00582908; detection used 15.79% and memory refresh 0.44% of objective evaluations; 44 responses with mean radius 2.95739 and relocated fraction 0.659091. case_003 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.114919; mean error remaining at interval end 1.63675; detection used 15.88% and memory refresh 0.48% of objective evaluations; 48 responses with mean radius 3.21094 and relocated fraction 0.6875. Largest tracking error: case_001. Examine relocation radius, fraction, and memory response to observable change severity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.

```python
"""Book/DEAP response policy: relocate every particle after a detected change.

This file is the evolvable program. The simulator, objective, search cases, and
evaluation budget remain outside it. The policy receives observations available
to the optimizer; inspecting hidden landscape state is outside the task contract.
"""


# EVOLVE-BLOCK-START
def choose_response(observation: dict) -> dict:
    """Choose a relocation response using optimizer-visible observations.

    Inputs include dimension, bounds_width, swarm_size, swarm_count,
    swarm_diameter, previous_best_fitness, current_best_fitness, fitness_drop,
    relative_fitness_drop, recent_improvement, evaluations_since_response,
    previous_response_radius, default_radius, observed_best_displacement,
    and evals_remaining. All observations are supplied by the fixed simulator.

    radius_scale multiplies default_radius; fraction controls relocation;
    memory is 'reevaluate' or 'reset'; reset_velocity must be a bool.
    """
    drop = max(0.0, float(observation["relative_fitness_drop"]))
    default_radius = max(0.0, float(observation["default_radius"]))
    diameter = max(0.0, float(observation["swarm_diameter"]))
    # Preserve most particles after mild changes; widen recovery as loss grows.
    if drop <= 0.03:
        radius_scale, fraction = 0.75, 0.4
    elif drop < 0.15:
        radius_scale, fraction = 1.5, 0.6
    else:
        radius_scale, fraction = 2.5, 0.8
    # Existing spatial coverage reduces the need to relocate more particles.
    if drop < 0.15 and diameter > 4.0 * default_radius:
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
Combined score to maximize: 0.32
mean_offline_error: 2.11; worst_case_offline_error: 2.83; case_error_std: 0.84; cases_completed: 4

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.607891; mean error remaining at interval end 1.9215; detection used 15.45% and memory refresh 0.39% of objective evaluations; 39 responses with mean radius 0.826923 and relocated fraction 0.610256. case_001 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.026881; mean error remaining at interval end 0.542956; detection used 15.93% and memory refresh 0.70% of objective evaluations; 70 responses with mean radius 0.876786 and relocated fraction 0.637143. case_002 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 0.959087; mean error remaining at interval end 0.00605153; detection used 15.90% and memory refresh 0.51% of objective evaluations; 51 responses with mean radius 2.72794 and relocated fraction 0.654902. case_003 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.827788; mean error remaining at interval end 1.57757; detection used 15.82% and memory refresh 0.47% of objective evaluations; 47 responses with mean radius 3.08777 and relocated fraction 0.702128. Largest tracking error: case_003. Examine relocation radius, fraction, and memory response to observable change severity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


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
    """Scale recovery by observed fitness loss and existing spatial coverage."""
    drop = max(0.0, float(observation["relative_fitness_drop"]))
    default_radius = max(0.0, float(observation["default_radius"]))
    diameter = max(0.0, float(observation["swarm_diameter"]))
    dispersed = diameter > 4.0 * default_radius
    if drop <= 0.03:
        # Small losses warrant limited disruption of useful search states.
        radius_scale, fraction = 0.75, 0.4
    elif drop < 0.15:
        radius_scale = 1.5
        fraction = 0.4 if dispersed else 0.6
    elif dispersed:
        # Existing coverage permits the conservative parent's response.
        radius_scale, fraction = 2.0, 0.6
    else:
        # Concentrated swarms use the stronger parent's broad recovery.
        radius_scale, fraction = 2.5, 0.8
    return {
        "radius_scale": radius_scale,
        "fraction": fraction,
        "memory": "reevaluate",
        "reset_velocity": False,
    }
# EVOLVE-BLOCK-END

```

Here are the performance metrics of the program:

Combined score to maximize: 0.29
mean_offline_error: 2.50; worst_case_offline_error: 3.63; case_error_std: 1.16; cases_completed: 4

Here is additional text feedback about the current program:

Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.347472; mean error remaining at interval end 1.73749; detection used 15.30% and memory refresh 0.40% of objective evaluations; 40 responses with mean radius 0.73125 and relocated fraction 0.56. case_001 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.634126; mean error remaining at interval end 2.40633; detection used 15.93% and memory refresh 0.62% of objective evaluations; 62 responses with mean radius 0.822581 and relocated fraction 0.606452. case_002 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 0.959799; mean error remaining at interval end 0.00497001; detection used 15.85% and memory refresh 0.49% of objective evaluations; 49 responses with mean radius 2.77041 and relocated fraction 0.644898. case_003 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.069744; mean error remaining at interval end 1.62127; detection used 15.88% and memory refresh 0.48% of objective evaluations; 48 responses with mean radius 3.08594 and relocated fraction 0.6875. Largest tracking error: case_001. Examine relocation radius, fraction, and memory response to observable change severity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


# Task

Rewrite the program to improve its performance on the specified metrics.
Provide the complete new program code.

IMPORTANT: Make sure your rewritten program maintains the same inputs and outputs as the original program, but with improved internal implementation.
