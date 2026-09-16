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

You are given multiple code scripts implementing the same algorithm.
You are tasked with generating a new code snippet that combines these code scripts in a way that is more efficient. 
I.e. perform crossover between the code scripts.
Provide the complete new program code.
You MUST respond using a short summary name, description, and the full code:

<NAME>
A shortened name summarizing the code you are proposing. Lowercase, no spaces, underscores allowed.
</NAME>

<DESCRIPTION>
A description and argumentation process of the code you are proposing.
</DESCRIPTION>

<CODE>
```{language}
# The new rewritten program here.
```
</CODE>

* Keep the markers "EVOLVE-BLOCK-START" and "EVOLVE-BLOCK-END" in the code. Do not change the code outside of these markers.
* Make sure your rewritten program maintains the same inputs and outputs as the original program, but with improved internal implementation.
* Make sure the file still runs after your changes.
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
    """Relocate up to three particles at 1.625 times the default radius.
    With five particles, three relocate and two continue ordinary PSO motion.
    The fixed adapter reevaluates memories and retains velocities.
    """
    count = min(3, int(observation["swarm_size"]))
    return {"count": count, "radius_scale": 1.625}
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.20
mean_offline_error: 3.99; worst_case_offline_error: 8.52; case_error_std: 1.84; cases_completed: 16

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 4.839602; mean error remaining at interval end 3.34849; detection used 15.83% and memory refresh 1.30% of objective evaluations; 260 responses with mean radius 0.8125 (mean multiplier 1.625), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 260, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 260, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 260, "4": 0, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.835373; mean error remaining at interval end 0.563533; detection used 15.86% and memory refresh 1.75% of objective evaluations; 349 responses with mean radius 0.8125 (mean multiplier 1.625), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 349, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 349, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 349, "4": 0, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 4.320267; mean error remaining at interval end 3.16072; detection used 15.77% and memory refresh 1.16% of objective evaluations; 232 responses with mean radius 0.8125 (mean multiplier 1.625), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 232, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 232, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 232, "4": 0, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.294955; mean error remaining at interval end 1.86548; detection used 15.84% and memory refresh 1.42% of objective evaluations; 283 responses with mean radius 0.8125 (mean multiplier 1.625), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 283, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 283, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 283, "4": 0, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.744280; mean error remaining at interval end 1.28673; detection used 16.05% and memory refresh 0.76% of objective evaluations; 151 responses with mean radius 0.8125 (mean multiplier 1.625), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 151, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 151, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 151, "4": 0, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.275218; mean error remaining at interval end 0.494427; detection used 15.86% and memory refresh 0.53% of objective evaluations; 107 responses with mean radius 0.8125 (mean multiplier 1.625), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 107, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 107, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 107, "4": 0, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.776614; mean error remaining at interval end 1.93869; detection used 15.96% and memory refresh 0.50% of objective evaluations; 99 responses with mean radius 0.8125 (mean multiplier 1.625), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 99, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 99, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 99, "4": 0, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.212247; mean error remaining at interval end 1.68388; detection used 15.88% and memory refresh 0.56% of objective evaluations; 113 responses with mean radius 0.8125 (mean multiplier 1.625), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 113, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 113, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 113, "4": 0, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.646065; mean error remaining at interval end 1.13573; detection used 16.00% and memory refresh 1.72% of objective evaluations; 344 responses with mean radius 2.4375 (mean multiplier 1.625), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 344, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 344, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 344, "4": 0, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.313749; mean error remaining at interval end 0.962373; detection used 15.97% and memory refresh 1.60% of objective evaluations; 320 responses with mean radius 2.4375 (mean multiplier 1.625), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 320, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 320, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 320, "4": 0, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.868378; mean error remaining at interval end 2.68829; detection used 15.74% and memory refresh 1.15% of objective evaluations; 230 responses with mean radius 2.4375 (mean multiplier 1.625), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 230, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 230, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 230, "4": 0, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.521836; mean error remaining at interval end 2.21511; detection used 15.95% and memory refresh 1.70% of objective evaluations; 341 responses with mean radius 2.4375 (mean multiplier 1.625), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 341, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 341, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 341, "4": 0, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 5.134839; mean error remaining at interval end 3.40122; detection used 15.95% and memory refresh 0.53% of objective evaluations; 107 responses with mean radius 2.4375 (mean multiplier 1.625), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 107, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 107, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 107, "4": 0, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 4.175739; mean error remaining at interval end 0.167291; detection used 16.10% and memory refresh 0.89% of objective evaluations; 177 responses with mean radius 2.4375 (mean multiplier 1.625), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 177, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 177, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 177, "4": 0, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.383365; mean error remaining at interval end 1.6039; detection used 15.24% and memory refresh 0.29% of objective evaluations; 59 responses with mean radius 2.4375 (mean multiplier 1.625), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 59, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 59, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 59, "4": 0, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 8.519771; mean error remaining at interval end 6.28055; detection used 15.72% and memory refresh 0.53% of objective evaluations; 105 responses with mean radius 2.4375 (mean multiplier 1.625), allocated fraction 0.6, and adapter encoding fraction 0.5 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 105, "4": 0, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 105, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 105, "4": 0, "5": 0}. Largest tracking error: case_015. Examine joint integer allocation and radius multiplier using public observed state, with all memories reevaluated and retained velocities fixed. Allocated fraction is allocated_count/swarm_size; the adapter encoding fraction only encodes an integer for the ceiling rule. Allocated counts are selected indices, not a claim of completed movement; horizon-truncated responses separately retain counts with objective queries. Constant count/radius pairs are permitted and receive no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.

```python
"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Relocate up to four particles with a damped displacement-based radius."""
    count = min(4, int(observation["swarm_size"]))
    displacement_ratio = observation["observed_best_displacement"] / max(
        observation["default_radius"], 1e-12
    )
    radius_scale = 1.25 + 0.125 * max(
        -1.0, min(1.0, displacement_ratio - 1.5)
    )
    return {"count": count, "radius_scale": float(radius_scale)}
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.21
mean_offline_error: 3.81; worst_case_offline_error: 12.11; case_error_std: 2.63; cases_completed: 16

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.488098; mean error remaining at interval end 1.9055; detection used 15.81% and memory refresh 1.39% of objective evaluations; 277 responses with mean radius 0.644066 (mean multiplier 1.28813), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 277, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 277, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 277, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.420737; mean error remaining at interval end 0.457378; detection used 15.90% and memory refresh 1.90% of objective evaluations; 380 responses with mean radius 0.646575 (mean multiplier 1.29315), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 380, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 380, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 380, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.666927; mean error remaining at interval end 1.34878; detection used 15.85% and memory refresh 1.45% of objective evaluations; 290 responses with mean radius 0.642997 (mean multiplier 1.28599), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 290, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 290, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 290, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.196137; mean error remaining at interval end 0.998796; detection used 15.85% and memory refresh 1.38% of objective evaluations; 275 responses with mean radius 0.643063 (mean multiplier 1.28613), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 275, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 275, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 275, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.819274; mean error remaining at interval end 1.24349; detection used 16.04% and memory refresh 0.74% of objective evaluations; 149 responses with mean radius 0.640486 (mean multiplier 1.28097), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 149, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 149, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 149, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.190208; mean error remaining at interval end 0.492092; detection used 15.85% and memory refresh 0.52% of objective evaluations; 103 responses with mean radius 0.635222 (mean multiplier 1.27044), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.780528; mean error remaining at interval end 3.28619; detection used 15.98% and memory refresh 0.56% of objective evaluations; 111 responses with mean radius 0.638996 (mean multiplier 1.27799), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 111, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 111, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 111, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.445180; mean error remaining at interval end 0.895205; detection used 15.89% and memory refresh 0.60% of objective evaluations; 121 responses with mean radius 0.640617 (mean multiplier 1.28123), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 121, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 121, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 121, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 6.088332; mean error remaining at interval end 2.77772; detection used 16.02% and memory refresh 1.76% of objective evaluations; 352 responses with mean radius 1.93233 (mean multiplier 1.28822), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 352, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 352, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 352, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.167384; mean error remaining at interval end 1.11968; detection used 16.00% and memory refresh 1.65% of objective evaluations; 331 responses with mean radius 1.93184 (mean multiplier 1.28789), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 331, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 331, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 331, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.765256; mean error remaining at interval end 2.56302; detection used 15.87% and memory refresh 1.39% of objective evaluations; 278 responses with mean radius 1.92819 (mean multiplier 1.28546), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 278, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 278, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 278, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.523412; mean error remaining at interval end 0.966383; detection used 15.96% and memory refresh 1.89% of objective evaluations; 378 responses with mean radius 1.934 (mean multiplier 1.28933), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 378, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 378, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 378, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.628899; mean error remaining at interval end 1.91489; detection used 15.96% and memory refresh 0.57% of objective evaluations; 114 responses with mean radius 1.91542 (mean multiplier 1.27695), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 114, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 114, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 114, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.618309; mean error remaining at interval end 0.422826; detection used 16.09% and memory refresh 0.89% of objective evaluations; 178 responses with mean radius 1.92967 (mean multiplier 1.28645), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 178, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 178, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 178, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.048655; mean error remaining at interval end 1.60343; detection used 15.31% and memory refresh 0.29% of objective evaluations; 58 responses with mean radius 1.88741 (mean multiplier 1.25827), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 58, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 58, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 58, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 12.105623; mean error remaining at interval end 10.3849; detection used 15.79% and memory refresh 0.56% of objective evaluations; 111 responses with mean radius 1.91239 (mean multiplier 1.27493), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 111, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 111, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 111, "5": 0}. Largest tracking error: case_015. Examine joint integer allocation and radius multiplier using public observed state, with all memories reevaluated and retained velocities fixed. Allocated fraction is allocated_count/swarm_size; the adapter encoding fraction only encodes an integer for the ceiling rule. Allocated counts are selected indices, not a claim of completed movement; horizon-truncated responses separately retain counts with objective queries. Constant count/radius pairs are permitted and receive no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


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
    """Relocate up to four particles, expanding radius for compact, damaged swarms."""
    count = min(4, int(observation["swarm_size"]))
    radius_scale = 1.5
    if (
        observation["relative_fitness_drop"] > 0.1
        and observation["swarm_diameter"] <= 3.0 * observation["default_radius"]
    ):
        radius_scale = 1.75
    return {"count": count, "radius_scale": float(radius_scale)}
# EVOLVE-BLOCK-END

```

Here are the performance metrics of the program:

Combined score to maximize: 0.21
mean_offline_error: 3.88; worst_case_offline_error: 10.02; case_error_std: 2.16; cases_completed: 16

Here is additional text feedback about the current program:

Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 4.012334; mean error remaining at interval end 2.72649; detection used 15.77% and memory refresh 1.15% of objective evaluations; 230 responses with mean radius 0.809783 (mean multiplier 1.61957), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 230, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 230, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 230, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.893612; mean error remaining at interval end 0.982487; detection used 15.87% and memory refresh 1.79% of objective evaluations; 358 responses with mean radius 0.820182 (mean multiplier 1.64036), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 358, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 358, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 358, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.747655; mean error remaining at interval end 1.35019; detection used 15.88% and memory refresh 1.46% of objective evaluations; 291 responses with mean radius 0.813144 (mean multiplier 1.62629), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 291, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 291, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 291, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 4.682262; mean error remaining at interval end 3.6014; detection used 15.77% and memory refresh 1.37% of objective evaluations; 274 responses with mean radius 0.8125 (mean multiplier 1.625), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 274, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 274, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 274, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.733004; mean error remaining at interval end 1.22218; detection used 16.04% and memory refresh 0.75% of objective evaluations; 150 responses with mean radius 0.794167 (mean multiplier 1.58833), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 150, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 150, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 150, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.146884; mean error remaining at interval end 0.489019; detection used 15.85% and memory refresh 0.52% of objective evaluations; 103 responses with mean radius 0.792476 (mean multiplier 1.58495), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.800933; mean error remaining at interval end 3.28645; detection used 15.98% and memory refresh 0.56% of objective evaluations; 111 responses with mean radius 0.814189 (mean multiplier 1.62838), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 111, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 111, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 111, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.463989; mean error remaining at interval end 0.903103; detection used 15.89% and memory refresh 0.60% of objective evaluations; 121 responses with mean radius 0.798554 (mean multiplier 1.59711), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 121, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 121, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 121, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.693130; mean error remaining at interval end 2.14111; detection used 15.99% and memory refresh 1.71% of objective evaluations; 343 responses with mean radius 2.53972 (mean multiplier 1.69315), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 343, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 343, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 343, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 3.841790; mean error remaining at interval end 0.717056; detection used 15.94% and memory refresh 1.54% of objective evaluations; 308 responses with mean radius 2.54464 (mean multiplier 1.69643), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 308, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 308, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 308, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.763579; mean error remaining at interval end 2.15738; detection used 15.89% and memory refresh 1.48% of objective evaluations; 296 responses with mean radius 2.54899 (mean multiplier 1.69932), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 296, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 296, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 296, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.921174; mean error remaining at interval end 2.02348; detection used 15.95% and memory refresh 1.70% of objective evaluations; 341 responses with mean radius 2.54362 (mean multiplier 1.69575), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 341, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 341, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 341, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.676816; mean error remaining at interval end 1.92126; detection used 15.92% and memory refresh 0.52% of objective evaluations; 103 responses with mean radius 2.51214 (mean multiplier 1.67476), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.531979; mean error remaining at interval end 0.383987; detection used 16.10% and memory refresh 0.89% of objective evaluations; 177 responses with mean radius 2.56356 (mean multiplier 1.70904), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 177, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 177, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 177, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.107051; mean error remaining at interval end 1.60423; detection used 15.30% and memory refresh 0.29% of objective evaluations; 59 responses with mean radius 2.44068 (mean multiplier 1.62712), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 59, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 59, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 59, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 10.021859; mean error remaining at interval end 7.21323; detection used 15.87% and memory refresh 0.60% of objective evaluations; 119 responses with mean radius 2.52731 (mean multiplier 1.68487), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 119, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 119, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 119, "5": 0}. Largest tracking error: case_015. Examine joint integer allocation and radius multiplier using public observed state, with all memories reevaluated and retained velocities fixed. Allocated fraction is allocated_count/swarm_size; the adapter encoding fraction only encodes an integer for the ceiling rule. Allocated counts are selected indices, not a claim of completed movement; horizon-truncated responses separately retain counts with objective queries. Constant count/radius pairs are permitted and receive no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


# Task

Perform a cross-over between the code script above and the one below. Aim to combine the best parts of both code implementations that improves the score.
Provide the complete new program code.

IMPORTANT: Make sure your rewritten program maintains the same inputs and outputs as the original program, but with improved internal implementation.

# Crossover Inspiration Programs
```python
"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Relocate up to three particles at 1.625 times the default radius.
    With five particles, three relocate and two continue ordinary PSO motion.
    The fixed adapter reevaluates memories and retains velocities.
    """
    count = min(3, int(observation["swarm_size"]))
    return {"count": count, "radius_scale": 1.625}
# EVOLVE-BLOCK-END

```

Performance metrics: Combined score to maximize: 0.20
mean_offline_error: 3.99; worst_case_offline_error: 8.52; case_error_std: 1.84; cases_completed: 16


