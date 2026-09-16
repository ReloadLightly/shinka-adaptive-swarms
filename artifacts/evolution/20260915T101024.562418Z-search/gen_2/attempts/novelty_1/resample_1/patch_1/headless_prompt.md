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
    """Choose a relocation response using optimizer-visible observations.

    Inputs include dimension, bounds_width, swarm_size, swarm_count,
    swarm_diameter, previous_best_fitness, current_best_fitness, fitness_drop,
    relative_fitness_drop, recent_improvement, evaluations_since_response,
    previous_response_radius, default_radius, observed_best_displacement,
    and evals_remaining. All observations are supplied by the fixed simulator.

    radius_scale multiplies default_radius; fraction controls relocation;
    memory is 'reevaluate' or 'reset'; reset_velocity must be a bool.
    """
    return {
        "radius_scale": 1.0,
        "fraction": 1.0,
        "memory": "reevaluate",
        "reset_velocity": False,
    }
# EVOLVE-BLOCK-END

```

Here are the performance metrics of the program:

Combined score to maximize: 0.26
mean_offline_error: 2.78; worst_case_offline_error: 5.69; case_error_std: 2.02; cases_completed: 4

Here is additional text feedback about the current program:

Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 5.694844; mean error remaining at interval end 5.281; detection used 15.31% and memory refresh 0.32% of objective evaluations; 32 responses with mean radius 0.5 and relocated fraction 1. case_001 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.050179; mean error remaining at interval end 0.997931; detection used 15.92% and memory refresh 0.65% of objective evaluations; 65 responses with mean radius 0.5 and relocated fraction 1. case_002 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 1.049280; mean error remaining at interval end 0.0727921; detection used 15.94% and memory refresh 0.52% of objective evaluations; 52 responses with mean radius 1.5 and relocated fraction 1. case_003 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.306006; mean error remaining at interval end 1.21489; detection used 15.92% and memory refresh 0.53% of objective evaluations; 53 responses with mean radius 1.5 and relocated fraction 1. Largest tracking error: case_000. Examine relocation radius, fraction, and memory response to observable change severity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


# Task

Rewrite the program to improve its performance on the specified metrics.
Provide the complete new program code.

IMPORTANT: Make sure your rewritten program maintains the same inputs and outputs as the original program, but with improved internal implementation.
