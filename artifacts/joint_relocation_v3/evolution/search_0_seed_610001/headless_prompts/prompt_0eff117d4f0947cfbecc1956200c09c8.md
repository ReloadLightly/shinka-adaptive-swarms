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

**Shrink the diameter rule toward the successful constant.** Keep four particles, compute `s=max(0, swarm_diameter)/max(default_radius, 1e-12)`, and set `radius_scale=1.21875 + a*max(-1, min(1, s-1))`, testing `a=0.0078125` and `a=-0.0078125` separately. Generation 21’s lower worst-case error provides limited motivation for revisiting geometry, while the smaller adjustment and incumbent-centered range address its poorer mean without presuming that geometry caused its tail result.
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
    count = min(3, int(observation["swarm_size"]))
    radius_scale = 1.4375
    return {"count": count, "radius_scale": radius_scale}
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.19
mean_offline_error: 4.33; worst_case_offline_error: 12.58; case_error_std: 2.80; cases_completed: 16

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 5.717989; mean error remaining at interval end 3.97654; detection used 15.81% and memory refresh 1.18% of objective evaluations; 236 responses with mean radius 0.71875 (mean multiplier 1.4375), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 236, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 236, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 236, "4": 0, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.551893; mean error remaining at interval end 0.4834; detection used 15.89% and memory refresh 1.81% of objective evaluations; 362 responses with mean radius 0.71875 (mean multiplier 1.4375), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 362, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 362, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 362, "4": 0, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 4.203304; mean error remaining at interval end 3.00402; detection used 15.78% and memory refresh 1.20% of objective evaluations; 240 responses with mean radius 0.71875 (mean multiplier 1.4375), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 240, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 240, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 240, "4": 0, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.659825; mean error remaining at interval end 1.30236; detection used 15.82% and memory refresh 1.37% of objective evaluations; 274 responses with mean radius 0.71875 (mean multiplier 1.4375), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 274, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 274, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 274, "4": 0, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.806242; mean error remaining at interval end 1.31643; detection used 16.03% and memory refresh 0.72% of objective evaluations; 144 responses with mean radius 0.71875 (mean multiplier 1.4375), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 144, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 144, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 144, "4": 0, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.296322; mean error remaining at interval end 0.499031; detection used 15.86% and memory refresh 0.53% of objective evaluations; 107 responses with mean radius 0.71875 (mean multiplier 1.4375), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 107, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 107, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 107, "4": 0, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.765758; mean error remaining at interval end 1.9273; detection used 15.95% and memory refresh 0.50% of objective evaluations; 99 responses with mean radius 0.71875 (mean multiplier 1.4375), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 99, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 99, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 99, "4": 0, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.089107; mean error remaining at interval end 1.63877; detection used 15.84% and memory refresh 0.56% of objective evaluations; 112 responses with mean radius 0.71875 (mean multiplier 1.4375), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 112, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 112, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 112, "4": 0, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.468790; mean error remaining at interval end 1.2038; detection used 16.01% and memory refresh 1.68% of objective evaluations; 336 responses with mean radius 2.15625 (mean multiplier 1.4375), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 336, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 336, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 336, "4": 0, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.560337; mean error remaining at interval end 1.2055; detection used 15.96% and memory refresh 1.57% of objective evaluations; 313 responses with mean radius 2.15625 (mean multiplier 1.4375), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 313, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 313, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 313, "4": 0, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 7.650898; mean error remaining at interval end 3.99981; detection used 15.82% and memory refresh 1.31% of objective evaluations; 263 responses with mean radius 2.15625 (mean multiplier 1.4375), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 263, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 263, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 263, "4": 0, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 6.056801; mean error remaining at interval end 2.82593; detection used 15.94% and memory refresh 1.56% of objective evaluations; 312 responses with mean radius 2.15625 (mean multiplier 1.4375), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 312, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 312, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 312, "4": 0, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 4.093406; mean error remaining at interval end 2.72938; detection used 15.95% and memory refresh 0.55% of objective evaluations; 110 responses with mean radius 2.15625 (mean multiplier 1.4375), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 110, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 110, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 110, "4": 0, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 4.464130; mean error remaining at interval end 1.16939; detection used 16.11% and memory refresh 0.84% of objective evaluations; 168 responses with mean radius 2.15625 (mean multiplier 1.4375), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 168, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 168, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 168, "4": 0, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.279790; mean error remaining at interval end 1.60541; detection used 15.35% and memory refresh 0.33% of objective evaluations; 65 responses with mean radius 2.15625 (mean multiplier 1.4375), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 65, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 65, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 65, "4": 0, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 12.578483; mean error remaining at interval end 11.3719; detection used 15.71% and memory refresh 0.48% of objective evaluations; 97 responses with mean radius 2.15625 (mean multiplier 1.4375), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 97, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 97, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 97, "4": 0, "5": 0}. Largest tracking error: case_015. Examine joint integer allocation and radius multiplier using public observed state, with all memories reevaluated and retained velocities fixed. Allocated fraction is allocated_count/swarm_size; the adapter encoding fraction only encodes an integer for the ceiling rule. Allocated counts are selected indices, not a claim of completed movement; horizon-truncated responses separately retain counts with objective queries. Constant count/radius pairs are permitted and receive no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.

```python
"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Apply a constant relocation policy within the available swarm capacity.
    The fixed adapter reevaluates memories and retains velocities.
    Non-relocated particles continue ordinary PSO motion.
    """
    # Select the joint policy independently of response construction.
    requested_count, radius_scale = 4, 1.25
    # Respect available capacity using the public observation.
    swarm_size = int(observation["swarm_size"])
    count = min(requested_count, swarm_size)
    return {"count": count, "radius_scale": radius_scale}
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
    count = min(4, int(observation["swarm_size"]))
    fitness_drop = observation["fitness_drop"]
    recent_improvement = max(0.0, observation["recent_improvement"])
    radius_scale = 1.25
    if fitness_drop > 0.0 and recent_improvement >= fitness_drop:
        radius_scale = 1.1875
    return {"count": count, "radius_scale": radius_scale}
# EVOLVE-BLOCK-END

```

Here are the performance metrics of the program:

Combined score to maximize: 0.21
mean_offline_error: 3.76; worst_case_offline_error: 12.15; case_error_std: 2.61; cases_completed: 16

Here is additional text feedback about the current program:

Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.862526; mean error remaining at interval end 1.37792; detection used 15.87% and memory refresh 1.54% of objective evaluations; 308 responses with mean radius 0.62429 (mean multiplier 1.24858), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 308, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 308, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 308, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.201166; mean error remaining at interval end 0.40109; detection used 15.88% and memory refresh 1.92% of objective evaluations; 384 responses with mean radius 0.624186 (mean multiplier 1.24837), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 384, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 384, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 384, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.670912; mean error remaining at interval end 1.34835; detection used 15.88% and memory refresh 1.43% of objective evaluations; 285 responses with mean radius 0.624232 (mean multiplier 1.24846), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 285, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 285, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 285, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.900201; mean error remaining at interval end 2.68421; detection used 15.78% and memory refresh 1.32% of objective evaluations; 264 responses with mean radius 0.62429 (mean multiplier 1.24858), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 264, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 264, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 264, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.638465; mean error remaining at interval end 1.20826; detection used 16.05% and memory refresh 0.74% of objective evaluations; 149 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 149, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 149, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 149, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.164451; mean error remaining at interval end 0.489492; detection used 15.85% and memory refresh 0.52% of objective evaluations; 103 responses with mean radius 0.623483 (mean multiplier 1.24697), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.777384; mean error remaining at interval end 3.28948; detection used 15.99% and memory refresh 0.56% of objective evaluations; 112 responses with mean radius 0.624442 (mean multiplier 1.24888), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 112, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 112, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 112, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.381495; mean error remaining at interval end 0.89649; detection used 15.89% and memory refresh 0.60% of objective evaluations; 121 responses with mean radius 0.624742 (mean multiplier 1.24948), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 121, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 121, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 121, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.130593; mean error remaining at interval end 0.987463; detection used 15.98% and memory refresh 1.68% of objective evaluations; 335 responses with mean radius 1.87136 (mean multiplier 1.24757), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 335, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 335, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 335, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.259213; mean error remaining at interval end 1.03957; detection used 15.99% and memory refresh 1.69% of objective evaluations; 337 responses with mean radius 1.87444 (mean multiplier 1.24963), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 337, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 337, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 337, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.498932; mean error remaining at interval end 2.03383; detection used 15.85% and memory refresh 1.39% of objective evaluations; 277 responses with mean radius 1.87331 (mean multiplier 1.24887), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 277, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 277, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 277, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.725199; mean error remaining at interval end 2.04553; detection used 15.96% and memory refresh 1.79% of objective evaluations; 358 responses with mean radius 1.87317 (mean multiplier 1.24878), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 358, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 358, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 358, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.507451; mean error remaining at interval end 1.90419; detection used 15.93% and memory refresh 0.52% of objective evaluations; 104 responses with mean radius 1.8723 (mean multiplier 1.2482), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 104, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 104, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 104, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.167489; mean error remaining at interval end 0.40777; detection used 16.06% and memory refresh 0.80% of objective evaluations; 160 responses with mean radius 1.87383 (mean multiplier 1.24922), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 160, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 160, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 160, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.172569; mean error remaining at interval end 1.60614; detection used 15.30% and memory refresh 0.33% of objective evaluations; 66 responses with mean radius 1.86648 (mean multiplier 1.24432), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 66, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 66, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 66, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 12.150107; mean error remaining at interval end 10.8364; detection used 15.74% and memory refresh 0.47% of objective evaluations; 94 responses with mean radius 1.874 (mean multiplier 1.24934), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 94, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 94, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 94, "5": 0}. Largest tracking error: case_015. Examine joint integer allocation and radius multiplier using public observed state, with all memories reevaluated and retained velocities fixed. Allocated fraction is allocated_count/swarm_size; the adapter encoding fraction only encodes an integer for the ceiling rule. Allocated counts are selected indices, not a claim of completed movement; horizon-truncated responses separately retain counts with objective queries. Constant count/radius pairs are permitted and receive no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


# Task

Rewrite the program to improve its performance on the specified metrics.
Provide the complete new program code.

IMPORTANT: Make sure your rewritten program maintains the same inputs and outputs as the original program, but with improved internal implementation.
