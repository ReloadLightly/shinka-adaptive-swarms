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

**Refine the successful fitness-drop threshold.** Starting from Generation 14, test `0.0875` and `0.10` as separate replacements for `0.075`, keeping the diameter condition and radius multiplier `1.5` unchanged. The previous threshold increase reduced mean error by 5.99%, making a further modest extension the strongest immediate lead, although improvement need not continue monotonically.
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
    count = 4
    if (
        observation["relative_fitness_drop"] <= 0.05
        and observation["swarm_diameter"] > 3.0 * observation["default_radius"]
    ):
        count = 3
    return {"count": min(count, int(observation["swarm_size"])), "radius_scale": 1.5}
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.21
mean_offline_error: 3.75; worst_case_offline_error: 8.90; case_error_std: 2.01; cases_completed: 16

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.613455; mean error remaining at interval end 1.99023; detection used 15.77% and memory refresh 1.24% of objective evaluations; 249 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.786345, and adapter encoding fraction 0.686345 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 17, "4": 232, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 17, "4": 232, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 17, "4": 232, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.171280; mean error remaining at interval end 1.1357; detection used 15.86% and memory refresh 1.71% of objective evaluations; 342 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.787135, and adapter encoding fraction 0.687135 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 22, "4": 320, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 22, "4": 320, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 22, "4": 320, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.859220; mean error remaining at interval end 2.68805; detection used 15.88% and memory refresh 1.40% of objective evaluations; 280 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.786429, and adapter encoding fraction 0.686429 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 19, "4": 261, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 19, "4": 261, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 19, "4": 261, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.800642; mean error remaining at interval end 2.64646; detection used 15.80% and memory refresh 1.30% of objective evaluations; 260 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.786154, and adapter encoding fraction 0.686154 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 18, "4": 242, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 18, "4": 242, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 18, "4": 242, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.666350; mean error remaining at interval end 1.20768; detection used 16.05% and memory refresh 0.76% of objective evaluations; 152 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.792105, and adapter encoding fraction 0.692105 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 6, "4": 146, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 6, "4": 146, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 6, "4": 146, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.249643; mean error remaining at interval end 0.494985; detection used 15.93% and memory refresh 0.58% of objective evaluations; 116 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.787931, and adapter encoding fraction 0.687931 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 7, "4": 109, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 7, "4": 109, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 7, "4": 109, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.859288; mean error remaining at interval end 1.02418; detection used 16.00% and memory refresh 0.56% of objective evaluations; 112 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.7875, and adapter encoding fraction 0.6875 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 7, "4": 105, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 7, "4": 105, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 7, "4": 105, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.872016; mean error remaining at interval end 1.33821; detection used 15.83% and memory refresh 0.51% of objective evaluations; 102 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.792157, and adapter encoding fraction 0.692157 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 4, "4": 98, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 4, "4": 98, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 4, "4": 98, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.108894; mean error remaining at interval end 0.990081; detection used 16.00% and memory refresh 1.65% of objective evaluations; 329 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.787234, and adapter encoding fraction 0.687234 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 21, "4": 308, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 21, "4": 308, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 21, "4": 308, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.097712; mean error remaining at interval end 1.14765; detection used 15.91% and memory refresh 1.39% of objective evaluations; 278 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.784892, and adapter encoding fraction 0.684892 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 21, "4": 257, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 21, "4": 257, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 21, "4": 257, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 6.868166; mean error remaining at interval end 3.65783; detection used 15.83% and memory refresh 1.34% of objective evaluations; 268 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.786567, and adapter encoding fraction 0.686567 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 18, "4": 250, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 18, "4": 250, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 18, "4": 250, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.257924; mean error remaining at interval end 2.06832; detection used 15.98% and memory refresh 1.76% of objective evaluations; 352 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.793182, and adapter encoding fraction 0.693182 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 12, "4": 340, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 12, "4": 340, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 12, "4": 340, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 4.452210; mean error remaining at interval end 3.31101; detection used 15.90% and memory refresh 0.48% of objective evaluations; 97 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.779381, and adapter encoding fraction 0.679381 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 10, "4": 87, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 10, "4": 87, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 10, "4": 87, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.197302; mean error remaining at interval end 0.439009; detection used 16.07% and memory refresh 0.80% of objective evaluations; 159 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.791195, and adapter encoding fraction 0.691195 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 7, "4": 152, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 7, "4": 152, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 7, "4": 152, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.084981; mean error remaining at interval end 1.60346; detection used 15.33% and memory refresh 0.33% of objective evaluations; 66 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.769697, and adapter encoding fraction 0.669697 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 10, "4": 56, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 10, "4": 56, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 10, "4": 56, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 8.895466; mean error remaining at interval end 6.0203; detection used 15.88% and memory refresh 0.57% of objective evaluations; 115 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.791304, and adapter encoding fraction 0.691304 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 5, "4": 110, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 5, "4": 110, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 5, "4": 110, "5": 0}. Largest tracking error: case_015. Examine joint integer allocation and radius multiplier using public observed state, with all memories reevaluated and retained velocities fixed. Allocated fraction is allocated_count/swarm_size; the adapter encoding fraction only encodes an integer for the ceiling rule. Allocated counts are selected indices, not a claim of completed movement; horizon-truncated responses separately retain counts with objective queries. Constant count/radius pairs are permitted and receive no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.

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
    count = 4
    if (
        observation["relative_fitness_drop"] <= 0.075
        and observation["swarm_diameter"] > 3.0 * observation["default_radius"]
    ):
        count = 3
    return {"count": min(count, int(observation["swarm_size"])), "radius_scale": 1.5}
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.22
mean_offline_error: 3.53; worst_case_offline_error: 8.90; case_error_std: 1.88; cases_completed: 16

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.613455; mean error remaining at interval end 1.99023; detection used 15.77% and memory refresh 1.24% of objective evaluations; 249 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.786345, and adapter encoding fraction 0.686345 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 17, "4": 232, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 17, "4": 232, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 17, "4": 232, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.655439; mean error remaining at interval end 0.622752; detection used 15.88% and memory refresh 1.89% of objective evaluations; 378 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.787302, and adapter encoding fraction 0.687302 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 24, "4": 354, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 24, "4": 354, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 24, "4": 354, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.782967; mean error remaining at interval end 1.52459; detection used 15.87% and memory refresh 1.35% of objective evaluations; 271 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.783026, and adapter encoding fraction 0.683026 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 23, "4": 248, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 23, "4": 248, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 23, "4": 248, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.757596; mean error remaining at interval end 2.57369; detection used 15.76% and memory refresh 1.29% of objective evaluations; 258 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.784496, and adapter encoding fraction 0.684496 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 20, "4": 238, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 20, "4": 238, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 20, "4": 238, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.740210; mean error remaining at interval end 1.2893; detection used 16.00% and memory refresh 0.71% of objective evaluations; 143 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.783217, and adapter encoding fraction 0.683217 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 12, "4": 131, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 12, "4": 131, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 12, "4": 131, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.243583; mean error remaining at interval end 0.509209; detection used 15.92% and memory refresh 0.58% of objective evaluations; 116 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.786207, and adapter encoding fraction 0.686207 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 8, "4": 108, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 8, "4": 108, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 8, "4": 108, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.859288; mean error remaining at interval end 1.02418; detection used 16.00% and memory refresh 0.56% of objective evaluations; 112 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.7875, and adapter encoding fraction 0.6875 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 7, "4": 105, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 7, "4": 105, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 7, "4": 105, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.872016; mean error remaining at interval end 1.33821; detection used 15.83% and memory refresh 0.51% of objective evaluations; 102 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.792157, and adapter encoding fraction 0.692157 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 4, "4": 98, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 4, "4": 98, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 4, "4": 98, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.108894; mean error remaining at interval end 0.990081; detection used 16.00% and memory refresh 1.65% of objective evaluations; 329 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.787234, and adapter encoding fraction 0.687234 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 21, "4": 308, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 21, "4": 308, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 21, "4": 308, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 3.939512; mean error remaining at interval end 1.10882; detection used 15.92% and memory refresh 1.39% of objective evaluations; 278 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.784173, and adapter encoding fraction 0.684173 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 22, "4": 256, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 22, "4": 256, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 22, "4": 256, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.690976; mean error remaining at interval end 2.27939; detection used 15.82% and memory refresh 1.39% of objective evaluations; 278 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.786331, and adapter encoding fraction 0.686331 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 19, "4": 259, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 19, "4": 259, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 19, "4": 259, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.298280; mean error remaining at interval end 1.02554; detection used 15.97% and memory refresh 1.85% of objective evaluations; 369 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.789702, and adapter encoding fraction 0.689702 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 19, "4": 350, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 19, "4": 350, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 19, "4": 350, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 4.452210; mean error remaining at interval end 3.31101; detection used 15.90% and memory refresh 0.48% of objective evaluations; 97 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.779381, and adapter encoding fraction 0.679381 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 10, "4": 87, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 10, "4": 87, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 10, "4": 87, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.463812; mean error remaining at interval end 0.484587; detection used 16.11% and memory refresh 0.90% of objective evaluations; 180 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.79, and adapter encoding fraction 0.69 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 9, "4": 171, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 9, "4": 171, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 9, "4": 171, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.084981; mean error remaining at interval end 1.60346; detection used 15.33% and memory refresh 0.33% of objective evaluations; 66 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.769697, and adapter encoding fraction 0.669697 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 10, "4": 56, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 10, "4": 56, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 10, "4": 56, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 8.895466; mean error remaining at interval end 6.0203; detection used 15.88% and memory refresh 0.57% of objective evaluations; 115 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.791304, and adapter encoding fraction 0.691304 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 5, "4": 110, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 5, "4": 110, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 5, "4": 110, "5": 0}. Largest tracking error: case_015. Examine joint integer allocation and radius multiplier using public observed state, with all memories reevaluated and retained velocities fixed. Allocated fraction is allocated_count/swarm_size; the adapter encoding fraction only encodes an integer for the ceiling rule. Allocated counts are selected indices, not a claim of completed movement; horizon-truncated responses separately retain counts with objective queries. Constant count/radius pairs are permitted and receive no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


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
    count = 4
    if (
        observation["relative_fitness_drop"] <= 0.05
        and observation["swarm_diameter"] > 3.0 * observation["default_radius"]
    ):
        count = 3
    radius_scale = 1.5
    if (
        observation["relative_fitness_drop"] > 0.1
        and observation["swarm_diameter"] <= 3.0 * observation["default_radius"]
    ):
        radius_scale = 1.75
    return {"count": min(count, int(observation["swarm_size"])), "radius_scale": radius_scale}
# EVOLVE-BLOCK-END

```

Here are the performance metrics of the program:

Combined score to maximize: 0.21
mean_offline_error: 3.79; worst_case_offline_error: 9.00; case_error_std: 1.97; cases_completed: 16

Here is additional text feedback about the current program:

Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.949878; mean error remaining at interval end 1.55255; detection used 15.79% and memory refresh 1.21% of objective evaluations; 241 responses with mean radius 0.810685 (mean multiplier 1.62137), allocated fraction 0.780913, and adapter encoding fraction 0.680913 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 23, "4": 218, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 23, "4": 218, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 23, "4": 218, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.543528; mean error remaining at interval end 0.484042; detection used 15.91% and memory refresh 1.88% of objective evaluations; 376 responses with mean radius 0.820479 (mean multiplier 1.64096), allocated fraction 0.789362, and adapter encoding fraction 0.689362 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 20, "4": 356, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 20, "4": 356, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 20, "4": 356, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.352446; mean error remaining at interval end 1.00033; detection used 15.88% and memory refresh 1.44% of objective evaluations; 287 responses with mean radius 0.808362 (mean multiplier 1.61672), allocated fraction 0.782578, and adapter encoding fraction 0.682578 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 25, "4": 262, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 25, "4": 262, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 25, "4": 262, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.787619; mean error remaining at interval end 2.57484; detection used 15.81% and memory refresh 1.40% of objective evaluations; 279 responses with mean radius 0.810484 (mean multiplier 1.62097), allocated fraction 0.787097, and adapter encoding fraction 0.687097 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 18, "4": 261, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 18, "4": 261, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 18, "4": 261, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.677898; mean error remaining at interval end 1.20688; detection used 16.05% and memory refresh 0.76% of objective evaluations; 152 responses with mean radius 0.793586 (mean multiplier 1.58717), allocated fraction 0.792105, and adapter encoding fraction 0.692105 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 6, "4": 146, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 6, "4": 146, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 6, "4": 146, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.227181; mean error remaining at interval end 0.489064; detection used 15.93% and memory refresh 0.58% of objective evaluations; 116 responses with mean radius 0.797414 (mean multiplier 1.59483), allocated fraction 0.787931, and adapter encoding fraction 0.687931 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 7, "4": 109, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 7, "4": 109, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 7, "4": 109, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 4.144284; mean error remaining at interval end 3.675; detection used 15.97% and memory refresh 0.51% of objective evaluations; 102 responses with mean radius 0.810049 (mean multiplier 1.6201), allocated fraction 0.784314, and adapter encoding fraction 0.684314 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 8, "4": 94, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 8, "4": 94, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 8, "4": 94, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.029475; mean error remaining at interval end 1.34056; detection used 15.83% and memory refresh 0.51% of objective evaluations; 102 responses with mean radius 0.796569 (mean multiplier 1.59314), allocated fraction 0.792157, and adapter encoding fraction 0.692157 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 4, "4": 98, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 4, "4": 98, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 4, "4": 98, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.552540; mean error remaining at interval end 1.41837; detection used 16.01% and memory refresh 1.79% of objective evaluations; 357 responses with mean radius 2.54622 (mean multiplier 1.69748), allocated fraction 0.787675, and adapter encoding fraction 0.687675 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 22, "4": 335, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 22, "4": 335, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 22, "4": 335, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.338672; mean error remaining at interval end 1.11735; detection used 15.96% and memory refresh 1.63% of objective evaluations; 326 responses with mean radius 2.55253 (mean multiplier 1.70169), allocated fraction 0.78773, and adapter encoding fraction 0.68773 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 20, "4": 306, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 20, "4": 306, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 20, "4": 306, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 6.088905; mean error remaining at interval end 2.70686; detection used 15.87% and memory refresh 1.46% of objective evaluations; 292 responses with mean radius 2.55437 (mean multiplier 1.70291), allocated fraction 0.789726, and adapter encoding fraction 0.689726 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 15, "4": 277, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 15, "4": 277, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 15, "4": 277, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.956097; mean error remaining at interval end 2.06303; detection used 15.96% and memory refresh 1.73% of objective evaluations; 346 responses with mean radius 2.54155 (mean multiplier 1.69436), allocated fraction 0.789017, and adapter encoding fraction 0.689017 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 19, "4": 327, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 19, "4": 327, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 19, "4": 327, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 5.258407; mean error remaining at interval end 4.00397; detection used 15.86% and memory refresh 0.48% of objective evaluations; 97 responses with mean radius 2.48969 (mean multiplier 1.65979), allocated fraction 0.785567, and adapter encoding fraction 0.685567 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 7, "4": 90, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 7, "4": 90, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 7, "4": 90, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.672431; mean error remaining at interval end 0.390468; detection used 16.07% and memory refresh 0.85% of objective evaluations; 170 responses with mean radius 2.55662 (mean multiplier 1.70441), allocated fraction 0.792941, and adapter encoding fraction 0.692941 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 6, "4": 164, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 6, "4": 164, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 6, "4": 164, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.103593; mean error remaining at interval end 1.60526; detection used 15.28% and memory refresh 0.32% of objective evaluations; 63 responses with mean radius 2.42857 (mean multiplier 1.61905), allocated fraction 0.774603, and adapter encoding fraction 0.674603 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 8, "4": 55, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 8, "4": 55, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 8, "4": 55, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 9.004032; mean error remaining at interval end 6.02609; detection used 15.87% and memory refresh 0.57% of objective evaluations; 115 responses with mean radius 2.5337 (mean multiplier 1.68913), allocated fraction 0.794783, and adapter encoding fraction 0.694783 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 3, "4": 112, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 3, "4": 112, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 3, "4": 112, "5": 0}. Largest tracking error: case_015. Examine joint integer allocation and radius multiplier using public observed state, with all memories reevaluated and retained velocities fixed. Allocated fraction is allocated_count/swarm_size; the adapter encoding fraction only encodes an integer for the ceiling rule. Allocated counts are selected indices, not a claim of completed movement; horizon-truncated responses separately retain counts with objective queries. Constant count/radius pairs are permitted and receive no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


# Task

Rewrite the program to improve its performance on the specified metrics.
Provide the complete new program code.

IMPORTANT: Make sure your rewritten program maintains the same inputs and outputs as the original program, but with improved internal implementation.
