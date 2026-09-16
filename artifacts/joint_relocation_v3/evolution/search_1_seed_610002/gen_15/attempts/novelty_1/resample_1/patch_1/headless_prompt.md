# System Instructions

Evolve choose_relocation(observation) in the marked evolve block only.
Return a dict with exactly two keys: count is a Python int between zero and
observation['swarm_size'] (five here); radius_scale is a finite nonnegative
Python int or float, normalized to float by the fixed adapter. Booleans are
invalid. Absolute radius is default_radius * radius_scale. The adapter fixes
memory='reevaluate' and reset_velocity=False and encodes the exact count for
the unchanged simulator. Non-relocated particles continue ordinary PSO motion.
Use only public observations and deterministic computation. Do not read files,
environment variables, seeds, benchmark internals, true optima or held-out inputs.
Do not modify the evaluator, objective budget or result files.
Optimize measured mean offline error across sixteen equally weighted search
cases at 100,000 objective queries each, ranked by 1/(1+mean_offline_error).
Detection and memory refresh queries count. Use measured feedback, per-case
error, radius and allocation summaries, and recovery diagnostics. Actual
allocated_fraction is allocated_count/swarm_size. adapter_encoding_fraction
only encodes that integer for the simulator and is not the relocated fraction.
The seed is the corrected original baseline: count five, radius multiplier one.
Constants are permitted; complexity, apparent adaptation, and novelty carry
no performance bonus. A small parameter change can be behaviorally meaningful.
Treat research hypotheses and meta recommendations as propositions to test,
not target results. New search outcomes do not establish final generalization.


# Scientific context supplied to mutation

# Scientific context for joint relocation v3

This is a cumulative study of Blackwell, Branke and Li's (2008) multi-swarm
particle swarm optimizer, reconstructed from the pinned DEAP implementation.
The numerical simulator is preserved. Five neutral particles form a swarm;
exclusion and swarm birth/death maintain search capacity. A counted reevaluation
of a remembered swarm best detects changed fitness. The response redistributes
selected particles using uniform-volume sampling around the refreshed swarm
best, and the remaining particles make ordinary PSO moves. Every objective
query counts, including change detection and memory reevaluation.

## Evidence motivating the new question

V1's selected program improved search performance but did not demonstrate
independent superiority over the corrected baseline. A fixed radius multiplier
two/count-three control had a promising independent mean, motivating the v2
allocation study. V2 then fixed radius multiplier two and evolved integer count.
Those choices were investigator decisions, not inherent ShinkaEvolve limits.

V2 completed one native twenty-slot search, separate validation selection, and
forty fresh final cases. Mean final offline error was 3.554065 for the selected
generation 13, 3.980588 for validation-selected constant count two, 3.626680 for
constant count three, 3.469960 for a frozen control without current-state
information, and 3.214605 for the original corrected baseline. The evolved-minus-
selected-constant difference was -0.426523 with a stratified bootstrap 95%
interval [-0.690272, -0.182927]. The evolved-minus-control difference was
+0.084105 [-0.178679, +0.409602]; the original corrected baseline comparison
was +0.339460 [+0.053050, +0.659607]. Secondary intervals are descriptive.

Thus v2 supports improvement over that frozen selected constant, not useful
current-state dependence, superiority over every constant, or overall optimizer
superiority. The selected program chose three or four particles according to
observed fitness loss, improvement and compactness. Its control retained a
validation-derived within-regime count mixture while changing state association
and temporal dependence; this was not a perfect single-variable intervention.
The original corrected baseline used radius multiplier one and count five.
V2 therefore left the joint effect of count and radius unresolved.

One auxiliary v2 feedback field incorrectly called the adapter encoding fraction
a relocated fraction. Actual allocation counts and fitness were correct; its
possible influence on mutation remains disclosed. V3 distinguishes allocated
fraction k/n from the adapter encoding (k-0.5)/n for positive k. The v2 artifacts
are preserved. Their aggregate results are now development evidence for this
new protocol, not new confirmatory evidence; no final case identifiers or seeds
are supplied in this mutation context.

## Candidate interface and competing explanations

Evolve choose_relocation(observation) to return exactly count and radius_scale.
Count is a Python int from zero through swarm_size; radius_scale is a finite
nonnegative Python number. Invalid values fail without rounding or clipping.
The adapter holds memory='reevaluate' and reset_velocity=False fixed. The seed
uses count five/radius multiplier one, exactly the corrected baseline's numerical
behavior. The new space includes the original baseline and all v2 responses.

The useful response may be a constant pair, state-dependent count, state-dependent
radius, or an interaction between them. None is privileged by the fitness
function. Larger displacement, a broader swarm and recent fitness deterioration
need not imply the same response: objective loss also reflects changing peak
heights and widths. Relocation sacrifices current positions but retains velocity
and reevaluated personal memory. Count zero means no relocation; all particles
still take ordinary PSO steps. Literal constant-count-zero policies with different
finite radius multipliers have identical optimization trajectories, although the
recorded previous_response_radius differs and could matter to a conditional
policy later. Radius zero is valid and places selected particles at the center.

The absolute relocation radius is default_radius * radius_scale. The existing
default_radius is half the configured movement severity. Keeping this public
input preserves a known severity scale; v3 does not test adaptation without it.
Do not infer access to latent peak positions or actual peak movement vectors.
The public observations are dimension, bounds_width, swarm_size, swarm_count,
swarm_diameter, previous_best_fitness, current_best_fitness, fitness_drop,
relative_fitness_drop, recent_improvement, evaluations_since_response,
previous_response_radius, default_radius, observed_best_displacement and
evals_remaining. Signed fitness change is current minus previous; fitness_drop
has the opposite sign. Use these observations and ordinary deterministic
computation only. Candidate Python execution is not a security sandbox; source
inspection checks prohibited access before independent comparison.

## Measurement and inference

The search suite crosses movement severity one/three and change period 2,500/
5,000, at a fixed 100,000-query horizon, five dimensions and ten conical peaks.
Four independent cases per regime give sixteen equally weighted cases. Native
selection maximizes 1/(1+mean_offline_error); lower offline error means better
tracking. Search feedback contains measured per-case error, interval-end error,
objective-query shares, actual radius multipliers, exact requested and allocated
counts, and selected particles that received objective queries. A final response
may be truncated; allocation is not a claim that every selected particle was
already moved or evaluated. Responses and trajectory checkpoints are repeated
measurements within independent cases, not extra statistical replicates.

The prospective follow-up plans three independent native searches, each with
thirty slots including this seed, followed by separate validation and fresh final
comparison. Those counts are study settings, not candidate-enforced rules.
The static comparison grid crosses counts zero through five with radius
multipliers 0.5, one, two and four, representing twenty-one distinct constant
optimization behaviors after aliasing the four count-zero rules. Compare against
the corrected baseline and competitive static responses, not only a weak selected
control. Validation and final outcomes must not enter mutation, novelty judging
or the meta-scratchpad. Independent search repeats address variability in what
the engine discovers; held-out case uncertainty alone does not capture that.

Source fidelity, successful execution, optimizer performance, useful conditional
mechanisms and scientific discovery are separate claims. These synthetic regimes
do not establish unseen-regime transfer, superiority over the literature's
permanent quantum (5+1) baseline, or real-world application effectiveness.

## Sources

- Blackwell, Branke and Li (2008), Particle Swarms for Dynamic Optimization
  Problems, in Swarm Intelligence: Introduction and Applications, pp. 193-217;
  multi-swarm mechanisms, Moving Peaks and particle conversion experiments:
  https://doi.org/10.1007/978-3-540-74089-6_6
- Pinned established optimizer code and landscape:
  https://github.com/DEAP/deap/blob/8a96fd3a75026f7b30e835f595a5199c75634ddf/examples/pso/multiswarm.py
  https://github.com/DEAP/deap/blob/8a96fd3a75026f7b30e835f595a5199c75634ddf/deap/benchmarks/movingpeaks.py
- Project reconstruction and preserved v2 outcomes: docs/reproduction.md and
  docs/relocation_allocation_v2.md. These source references document provenance;
  candidates must use the supplied context rather than accessing files.


# Potential Recommendations
The following are potential recommendations for the next program generation:

**Adjust radius modestly using observed best-position displacement.** Retain four particles, define `u=max(0.0, observed_best_displacement)/max(default_radius, 1e-12)`, and try `radius_scale=1.25 + 0.125*(u-1)/(u+1)`. This smoothly bounds the multiplier between `1.125` and `1.375`, extending the successful moderate-radius policy with a spatial signal; observed displacement should be treated as a proxy, not true peak movement.
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
"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Return {'count': Python int in [0, swarm_size], 'radius_scale': number}.

    Radius multiplier must be finite and nonnegative. The absolute radius is
    default_radius * radius_scale; default_radius is the known baseline scale,
    half the configured movement severity. Five particles form a swarm here.

    Public observations: dimension, bounds_width, swarm_size, swarm_count,
    swarm_diameter, previous_best_fitness, current_best_fitness, fitness_drop,
    relative_fitness_drop, recent_improvement, evaluations_since_response,
    previous_response_radius, default_radius, observed_best_displacement,
    evals_remaining. fitness_drop is previous minus current best fitness.

    Non-relocated particles still make ordinary PSO moves. All personal
    memories are reevaluated. Velocities are retained after relocation.
    """
    return {"count": min(3, int(observation["swarm_size"])), "radius_scale": 1.0}
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.20
mean_offline_error: 3.89; worst_case_offline_error: 9.81; case_error_std: 2.13; cases_completed: 16

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 5.757218; mean error remaining at interval end 3.89019; detection used 15.80% and memory refresh 1.19% of objective evaluations; 237 responses with mean radius 0.5 (mean multiplier 1), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 237, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 237, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 237, "4": 0, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.513112; mean error remaining at interval end 0.447344; detection used 15.87% and memory refresh 1.80% of objective evaluations; 360 responses with mean radius 0.5 (mean multiplier 1), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 360, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 360, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 360, "4": 0, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.970554; mean error remaining at interval end 1.82253; detection used 15.73% and memory refresh 1.10% of objective evaluations; 221 responses with mean radius 0.5 (mean multiplier 1), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 221, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 221, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 221, "4": 0, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.849620; mean error remaining at interval end 1.43677; detection used 15.85% and memory refresh 1.44% of objective evaluations; 289 responses with mean radius 0.5 (mean multiplier 1), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 289, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 289, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 289, "4": 0, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.771761; mean error remaining at interval end 1.28992; detection used 16.07% and memory refresh 0.71% of objective evaluations; 143 responses with mean radius 0.5 (mean multiplier 1), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 143, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 143, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 143, "4": 0, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.507372; mean error remaining at interval end 0.553681; detection used 15.85% and memory refresh 0.52% of objective evaluations; 103 responses with mean radius 0.5 (mean multiplier 1), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 103, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 103, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 103, "4": 0, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.694618; mean error remaining at interval end 1.9266; detection used 15.95% and memory refresh 0.50% of objective evaluations; 99 responses with mean radius 0.5 (mean multiplier 1), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 99, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 99, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 99, "4": 0, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.169571; mean error remaining at interval end 1.64802; detection used 15.88% and memory refresh 0.56% of objective evaluations; 111 responses with mean radius 0.5 (mean multiplier 1), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 111, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 111, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 111, "4": 0, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.759685; mean error remaining at interval end 1.15863; detection used 16.00% and memory refresh 1.78% of objective evaluations; 356 responses with mean radius 1.5 (mean multiplier 1), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 356, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 356, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 356, "4": 0, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.403711; mean error remaining at interval end 1.09815; detection used 15.97% and memory refresh 1.50% of objective evaluations; 301 responses with mean radius 1.5 (mean multiplier 1), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 301, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 301, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 301, "4": 0, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.759348; mean error remaining at interval end 2.35692; detection used 15.89% and memory refresh 1.35% of objective evaluations; 271 responses with mean radius 1.5 (mean multiplier 1), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 271, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 271, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 271, "4": 0, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.130166; mean error remaining at interval end 2.22801; detection used 15.93% and memory refresh 1.52% of objective evaluations; 305 responses with mean radius 1.5 (mean multiplier 1), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 305, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 305, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 305, "4": 0, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 4.975327; mean error remaining at interval end 3.35408; detection used 15.88% and memory refresh 0.49% of objective evaluations; 98 responses with mean radius 1.5 (mean multiplier 1), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 98, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 98, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 98, "4": 0, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.120318; mean error remaining at interval end 0.21003; detection used 16.05% and memory refresh 0.80% of objective evaluations; 160 responses with mean radius 1.5 (mean multiplier 1), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 160, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 160, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 160, "4": 0, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.109963; mean error remaining at interval end 1.60369; detection used 15.24% and memory refresh 0.29% of objective evaluations; 57 responses with mean radius 1.5 (mean multiplier 1), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 57, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 57, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 57, "4": 0, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 9.814296; mean error remaining at interval end 8.02505; detection used 15.69% and memory refresh 0.51% of objective evaluations; 101 responses with mean radius 1.5 (mean multiplier 1), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 101, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 101, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 101, "4": 0, "5": 0}. Largest tracking error: case_015. Examine joint integer allocation and radius multiplier using public observed state, with all memories reevaluated and retained velocities fixed. Allocated fraction is allocated_count/swarm_size; the adapter encoding fraction only encodes an integer for the ceiling rule. Allocated counts are selected indices, not a claim of completed movement; horizon-truncated responses separately retain counts with objective queries. Constant count/radius pairs are permitted and receive no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.

```python
"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Return {'count': Python int in [0, swarm_size], 'radius_scale': number}.

    Radius multiplier must be finite and nonnegative. The absolute radius is
    default_radius * radius_scale; default_radius is the known baseline scale,
    half the configured movement severity. Five particles form a swarm here.

    Public observations: dimension, bounds_width, swarm_size, swarm_count,
    swarm_diameter, previous_best_fitness, current_best_fitness, fitness_drop,
    relative_fitness_drop, recent_improvement, evaluations_since_response,
    previous_response_radius, default_radius, observed_best_displacement,
    evals_remaining. fitness_drop is previous minus current best fitness.

    Non-relocated particles still make ordinary PSO moves. All personal
    memories are reevaluated. Velocities are retained after relocation.
    """
    return {"count": min(4, int(observation["swarm_size"])), "radius_scale": 1.25}
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.21
mean_offline_error: 3.76; worst_case_offline_error: 12.15; case_error_std: 2.60; cases_completed: 16

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.838723; mean error remaining at interval end 1.5432; detection used 15.81% and memory refresh 1.31% of objective evaluations; 263 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 263, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 263, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 263, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.251629; mean error remaining at interval end 0.480402; detection used 15.88% and memory refresh 1.92% of objective evaluations; 383 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 383, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 383, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 383, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.660868; mean error remaining at interval end 1.34956; detection used 15.88% and memory refresh 1.43% of objective evaluations; 285 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 285, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 285, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 285, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.901186; mean error remaining at interval end 2.67754; detection used 15.78% and memory refresh 1.32% of objective evaluations; 264 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 264, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 264, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 264, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.638465; mean error remaining at interval end 1.20826; detection used 16.05% and memory refresh 0.74% of objective evaluations; 149 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 149, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 149, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 149, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.164450; mean error remaining at interval end 0.489492; detection used 15.85% and memory refresh 0.52% of objective evaluations; 103 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.777384; mean error remaining at interval end 3.28948; detection used 15.99% and memory refresh 0.56% of objective evaluations; 112 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 112, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 112, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 112, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.381495; mean error remaining at interval end 0.89649; detection used 15.89% and memory refresh 0.60% of objective evaluations; 121 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 121, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 121, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 121, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.266670; mean error remaining at interval end 0.962046; detection used 15.98% and memory refresh 1.68% of objective evaluations; 336 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 336, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 336, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 336, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.259213; mean error remaining at interval end 1.03957; detection used 15.99% and memory refresh 1.69% of objective evaluations; 337 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 337, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 337, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 337, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.498932; mean error remaining at interval end 2.03383; detection used 15.85% and memory refresh 1.39% of objective evaluations; 277 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 277, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 277, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 277, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.498382; mean error remaining at interval end 2.33657; detection used 15.95% and memory refresh 1.69% of objective evaluations; 337 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 337, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 337, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 337, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.507451; mean error remaining at interval end 1.90419; detection used 15.93% and memory refresh 0.52% of objective evaluations; 104 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 104, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 104, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 104, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.167489; mean error remaining at interval end 0.40777; detection used 16.06% and memory refresh 0.80% of objective evaluations; 160 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 160, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 160, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 160, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.172569; mean error remaining at interval end 1.60614; detection used 15.30% and memory refresh 0.33% of objective evaluations; 66 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 66, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 66, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 66, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 12.150105; mean error remaining at interval end 10.8364; detection used 15.74% and memory refresh 0.47% of objective evaluations; 94 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 94, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 94, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 94, "5": 0}. Largest tracking error: case_015. Examine joint integer allocation and radius multiplier using public observed state, with all memories reevaluated and retained velocities fixed. Allocated fraction is allocated_count/swarm_size; the adapter encoding fraction only encodes an integer for the ceiling rule. Allocated counts are selected indices, not a claim of completed movement; horizon-truncated responses separately retain counts with objective queries. Constant count/radius pairs are permitted and receive no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


# Current program

Here is the current program we are trying to improve (you will need to propose a new program with the same inputs and outputs as the original program, but with improved internal implementation):

```python
"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Relocate four particles with selectively expanded radius.
    Non-relocated particles continue ordinary PSO motion. The fixed adapter
    reevaluates personal memories and retains velocities.
    """
    count = min(4, int(observation["swarm_size"]))
    radius_scale = 1.25
    if (
        observation["relative_fitness_drop"] > 0.1
        and observation["swarm_diameter"]
        < 2.0 * observation["default_radius"]
    ):
        radius_scale = 1.5
    return {"count": count, "radius_scale": radius_scale}
# EVOLVE-BLOCK-END

```

Here are the performance metrics of the program:

Combined score to maximize: 0.21
mean_offline_error: 3.88; worst_case_offline_error: 12.30; case_error_std: 2.60; cases_completed: 16

Here is additional text feedback about the current program:

Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.952370; mean error remaining at interval end 1.5508; detection used 15.82% and memory refresh 1.29% of objective evaluations; 257 responses with mean radius 0.686284 (mean multiplier 1.37257), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 257, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 257, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 257, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.872218; mean error remaining at interval end 0.998651; detection used 15.86% and memory refresh 1.79% of objective evaluations; 358 responses with mean radius 0.692388 (mean multiplier 1.38478), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 358, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 358, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 358, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.721134; mean error remaining at interval end 1.35932; detection used 15.89% and memory refresh 1.43% of objective evaluations; 285 responses with mean radius 0.687281 (mean multiplier 1.37456), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 285, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 285, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 285, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 4.463594; mean error remaining at interval end 3.21721; detection used 15.78% and memory refresh 1.38% of objective evaluations; 276 responses with mean radius 0.683877 (mean multiplier 1.36775), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 276, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 276, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 276, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.650938; mean error remaining at interval end 1.21412; detection used 16.05% and memory refresh 0.74% of objective evaluations; 149 responses with mean radius 0.667785 (mean multiplier 1.33557), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 149, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 149, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 149, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.174786; mean error remaining at interval end 0.489878; detection used 15.85% and memory refresh 0.52% of objective evaluations; 103 responses with mean radius 0.667476 (mean multiplier 1.33495), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.784946; mean error remaining at interval end 3.28794; detection used 15.99% and memory refresh 0.56% of objective evaluations; 112 responses with mean radius 0.6875 (mean multiplier 1.375), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 112, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 112, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 112, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.390261; mean error remaining at interval end 0.895963; detection used 15.85% and memory refresh 0.56% of objective evaluations; 113 responses with mean radius 0.67146 (mean multiplier 1.34292), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 113, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 113, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 113, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.512640; mean error remaining at interval end 1.04557; detection used 16.02% and memory refresh 1.81% of objective evaluations; 362 responses with mean radius 2.16609 (mean multiplier 1.44406), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 362, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 362, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 362, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.234011; mean error remaining at interval end 0.935675; detection used 15.95% and memory refresh 1.48% of objective evaluations; 296 responses with mean radius 2.17525 (mean multiplier 1.45017), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 296, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 296, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 296, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.736998; mean error remaining at interval end 2.33613; detection used 15.88% and memory refresh 1.45% of objective evaluations; 290 responses with mean radius 2.17371 (mean multiplier 1.44914), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 290, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 290, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 290, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.803956; mean error remaining at interval end 1.87972; detection used 15.95% and memory refresh 1.70% of objective evaluations; 339 responses with mean radius 2.16261 (mean multiplier 1.44174), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 339, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 339, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 339, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.929371; mean error remaining at interval end 1.92613; detection used 15.95% and memory refresh 0.55% of objective evaluations; 109 responses with mean radius 2.12959 (mean multiplier 1.41972), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 109, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 109, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 109, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.373721; mean error remaining at interval end 0.375109; detection used 16.11% and memory refresh 0.94% of objective evaluations; 187 responses with mean radius 2.18583 (mean multiplier 1.45722), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 187, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 187, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 187, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.113014; mean error remaining at interval end 1.60437; detection used 15.55% and memory refresh 0.36% of objective evaluations; 73 responses with mean radius 2.08562 (mean multiplier 1.39041), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 73, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 73, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 73, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 12.302222; mean error remaining at interval end 10.4991; detection used 15.78% and memory refresh 0.51% of objective evaluations; 102 responses with mean radius 2.14706 (mean multiplier 1.43137), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 102, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 102, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 102, "5": 0}. Largest tracking error: case_015. Examine joint integer allocation and radius multiplier using public observed state, with all memories reevaluated and retained velocities fixed. Allocated fraction is allocated_count/swarm_size; the adapter encoding fraction only encodes an integer for the ceiling rule. Allocated counts are selected indices, not a claim of completed movement; horizon-truncated responses separately retain counts with objective queries. Constant count/radius pairs are permitted and receive no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


# Task

Rewrite the program to improve its performance on the specified metrics.
Provide the complete new program code.

IMPORTANT: Make sure your rewritten program maintains the same inputs and outputs as the original program, but with improved internal implementation.
