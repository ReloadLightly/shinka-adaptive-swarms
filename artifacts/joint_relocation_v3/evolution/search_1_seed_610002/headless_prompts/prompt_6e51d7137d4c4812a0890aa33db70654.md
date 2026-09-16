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
    """Test three relocations for moderate loss and four for larger loss."""
    swarm_size = int(observation["swarm_size"])
    count = 3 if observation["relative_fitness_drop"] <= 0.1 else 4
    radius_scale = 1.0
    return {
        "count": max(0, min(swarm_size, count)),
        "radius_scale": radius_scale,
    }
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.20
mean_offline_error: 4.04; worst_case_offline_error: 12.44; case_error_std: 2.77; cases_completed: 16

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.616924; mean error remaining at interval end 2.01087; detection used 15.79% and memory refresh 1.28% of objective evaluations; 256 responses with mean radius 0.5 (mean multiplier 1), allocated fraction 0.716406, and adapter encoding fraction 0.616406 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 107, "4": 149, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 107, "4": 149, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 107, "4": 149, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.491099; mean error remaining at interval end 0.476555; detection used 15.88% and memory refresh 1.92% of objective evaluations; 383 responses with mean radius 0.5 (mean multiplier 1), allocated fraction 0.724282, and adapter encoding fraction 0.624282 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 145, "4": 238, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 145, "4": 238, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 145, "4": 238, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.883363; mean error remaining at interval end 1.55379; detection used 15.88% and memory refresh 1.48% of objective evaluations; 296 responses with mean radius 0.5 (mean multiplier 1), allocated fraction 0.714189, and adapter encoding fraction 0.614189 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 127, "4": 169, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 127, "4": 169, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 127, "4": 169, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 4.484124; mean error remaining at interval end 2.93377; detection used 15.80% and memory refresh 1.34% of objective evaluations; 268 responses with mean radius 0.5 (mean multiplier 1), allocated fraction 0.722388, and adapter encoding fraction 0.622388 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 104, "4": 164, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 104, "4": 164, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 104, "4": 164, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.468839; mean error remaining at interval end 0.89931; detection used 16.04% and memory refresh 0.75% of objective evaluations; 150 responses with mean radius 0.5 (mean multiplier 1), allocated fraction 0.682667, and adapter encoding fraction 0.582667 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 88, "4": 62, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 88, "4": 62, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 88, "4": 62, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.339930; mean error remaining at interval end 0.500384; detection used 15.86% and memory refresh 0.52% of objective evaluations; 104 responses with mean radius 0.5 (mean multiplier 1), allocated fraction 0.696154, and adapter encoding fraction 0.596154 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 54, "4": 50, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 54, "4": 50, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 54, "4": 50, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.784151; mean error remaining at interval end 0.985616; detection used 16.01% and memory refresh 0.57% of objective evaluations; 114 responses with mean radius 0.5 (mean multiplier 1), allocated fraction 0.712281, and adapter encoding fraction 0.612281 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 50, "4": 64, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 50, "4": 64, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 50, "4": 64, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.667832; mean error remaining at interval end 0.937331; detection used 15.96% and memory refresh 0.69% of objective evaluations; 137 responses with mean radius 0.5 (mean multiplier 1), allocated fraction 0.70219, and adapter encoding fraction 0.60219 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 67, "4": 70, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 67, "4": 70, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 67, "4": 70, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.835828; mean error remaining at interval end 1.19962; detection used 16.04% and memory refresh 1.79% of objective evaluations; 357 responses with mean radius 1.5 (mean multiplier 1), allocated fraction 0.776471, and adapter encoding fraction 0.676471 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 42, "4": 315, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 42, "4": 315, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 42, "4": 315, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.486014; mean error remaining at interval end 1.71227; detection used 15.98% and memory refresh 1.58% of objective evaluations; 316 responses with mean radius 1.5 (mean multiplier 1), allocated fraction 0.776582, and adapter encoding fraction 0.676582 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 37, "4": 279, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 37, "4": 279, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 37, "4": 279, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 7.205451; mean error remaining at interval end 3.88671; detection used 15.87% and memory refresh 1.51% of objective evaluations; 302 responses with mean radius 1.5 (mean multiplier 1), allocated fraction 0.778808, and adapter encoding fraction 0.678808 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 32, "4": 270, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 32, "4": 270, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 32, "4": 270, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.937396; mean error remaining at interval end 1.99658; detection used 16.00% and memory refresh 1.75% of objective evaluations; 349 responses with mean radius 1.5 (mean multiplier 1), allocated fraction 0.775358, and adapter encoding fraction 0.675358 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 43, "4": 306, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 43, "4": 306, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 43, "4": 306, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 5.173637; mean error remaining at interval end 3.95122; detection used 15.98% and memory refresh 0.54% of objective evaluations; 108 responses with mean radius 1.5 (mean multiplier 1), allocated fraction 0.753704, and adapter encoding fraction 0.653704 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 25, "4": 83, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 25, "4": 83, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 25, "4": 83, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.574405; mean error remaining at interval end 0.420839; detection used 16.09% and memory refresh 0.89% of objective evaluations; 178 responses with mean radius 1.5 (mean multiplier 1), allocated fraction 0.778652, and adapter encoding fraction 0.678652 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 19, "4": 159, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 19, "4": 159, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 19, "4": 159, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.282797; mean error remaining at interval end 1.60571; detection used 15.30% and memory refresh 0.30% of objective evaluations; 61 responses with mean radius 1.5 (mean multiplier 1), allocated fraction 0.737705, and adapter encoding fraction 0.637705 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 19, "4": 42, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 19, "4": 42, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 19, "4": 42, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 12.438050; mean error remaining at interval end 10.4946; detection used 15.80% and memory refresh 0.49% of objective evaluations; 98 responses with mean radius 1.5 (mean multiplier 1), allocated fraction 0.773469, and adapter encoding fraction 0.673469 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 13, "4": 85, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 13, "4": 85, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 13, "4": 85, "5": 0}. Largest tracking error: case_015. Examine joint integer allocation and radius multiplier using public observed state, with all memories reevaluated and retained velocities fixed. Allocated fraction is allocated_count/swarm_size; the adapter encoding fraction only encodes an integer for the ceiling rule. Allocated counts are selected indices, not a claim of completed movement; horizon-truncated responses separately retain counts with objective queries. Constant count/radius pairs are permitted and receive no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.

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
    q = observation["swarm_diameter"] / max(observation["default_radius"], 1e-12)
    count = 3 if q > 5.0 else 4
    return {"count": min(count, int(observation["swarm_size"])), "radius_scale": 1.25}
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.21
mean_offline_error: 3.68; worst_case_offline_error: 9.42; case_error_std: 2.09; cases_completed: 16

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.568729; mean error remaining at interval end 2.09144; detection used 15.82% and memory refresh 1.31% of objective evaluations; 263 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.769582, and adapter encoding fraction 0.669582 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 40, "4": 223, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 40, "4": 223, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 40, "4": 223, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.870004; mean error remaining at interval end 1.22195; detection used 15.90% and memory refresh 1.66% of objective evaluations; 332 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.775301, and adapter encoding fraction 0.675301 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 41, "4": 291, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 41, "4": 291, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 41, "4": 291, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.465982; mean error remaining at interval end 1.23121; detection used 15.91% and memory refresh 1.52% of objective evaluations; 304 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.774342, and adapter encoding fraction 0.674342 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 39, "4": 265, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 39, "4": 265, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 39, "4": 265, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.488693; mean error remaining at interval end 2.14969; detection used 15.82% and memory refresh 1.60% of objective evaluations; 320 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.7725, and adapter encoding fraction 0.6725 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 44, "4": 276, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 44, "4": 276, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 44, "4": 276, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.725605; mean error remaining at interval end 1.29137; detection used 16.06% and memory refresh 0.70% of objective evaluations; 141 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.770213, and adapter encoding fraction 0.670213 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 21, "4": 120, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 21, "4": 120, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 21, "4": 120, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.262604; mean error remaining at interval end 0.496853; detection used 15.96% and memory refresh 0.60% of objective evaluations; 121 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.768595, and adapter encoding fraction 0.668595 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 19, "4": 102, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 19, "4": 102, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 19, "4": 102, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.295352; mean error remaining at interval end 0.372626; detection used 16.05% and memory refresh 0.58% of objective evaluations; 116 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.768966, and adapter encoding fraction 0.668966 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 18, "4": 98, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 18, "4": 98, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 18, "4": 98, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.078156; mean error remaining at interval end 1.57973; detection used 15.86% and memory refresh 0.56% of objective evaluations; 113 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.761062, and adapter encoding fraction 0.661062 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 22, "4": 91, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 22, "4": 91, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 22, "4": 91, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.017874; mean error remaining at interval end 1.55168; detection used 16.02% and memory refresh 1.63% of objective evaluations; 326 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.774847, and adapter encoding fraction 0.674847 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 41, "4": 285, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 41, "4": 285, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 41, "4": 285, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.064942; mean error remaining at interval end 1.10549; detection used 15.97% and memory refresh 1.50% of objective evaluations; 301 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.774086, and adapter encoding fraction 0.674086 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 39, "4": 262, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 39, "4": 262, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 39, "4": 262, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.680349; mean error remaining at interval end 2.3438; detection used 15.87% and memory refresh 1.36% of objective evaluations; 272 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.769118, and adapter encoding fraction 0.669118 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 42, "4": 230, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 42, "4": 230, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 42, "4": 230, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.200737; mean error remaining at interval end 2.17183; detection used 15.97% and memory refresh 1.75% of objective evaluations; 349 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.774212, and adapter encoding fraction 0.674212 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 45, "4": 304, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 45, "4": 304, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 45, "4": 304, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 5.188948; mean error remaining at interval end 3.96992; detection used 15.95% and memory refresh 0.50% of objective evaluations; 100 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.768, and adapter encoding fraction 0.668 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 16, "4": 84, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 16, "4": 84, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 16, "4": 84, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.216257; mean error remaining at interval end 0.468883; detection used 16.11% and memory refresh 0.83% of objective evaluations; 165 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.774545, and adapter encoding fraction 0.674545 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 21, "4": 144, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 21, "4": 144, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 21, "4": 144, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.263131; mean error remaining at interval end 1.60416; detection used 15.32% and memory refresh 0.33% of objective evaluations; 65 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.738462, and adapter encoding fraction 0.638462 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 20, "4": 45, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 20, "4": 45, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 20, "4": 45, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 9.423029; mean error remaining at interval end 7.23657; detection used 15.86% and memory refresh 0.58% of objective evaluations; 117 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.77265, and adapter encoding fraction 0.67265 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 16, "4": 101, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 16, "4": 101, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 16, "4": 101, "5": 0}. Largest tracking error: case_015. Examine joint integer allocation and radius multiplier using public observed state, with all memories reevaluated and retained velocities fixed. Allocated fraction is allocated_count/swarm_size; the adapter encoding fraction only encodes an integer for the ceiling rule. Allocated counts are selected indices, not a claim of completed movement; horizon-truncated responses separately retain counts with objective queries. Constant count/radius pairs are permitted and receive no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


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
    """Choose relocation count and radius using normalized swarm diameter."""
    q = observation["swarm_diameter"] / max(
        observation["default_radius"], 1e-12
    )
    if q > 4.0:
        count = 3
        radius_scale = 1.25
    else:
        count = 4
        radius_scale = 1.3125
    return {
        "count": min(count, int(observation["swarm_size"])),
        "radius_scale": radius_scale,
    }
# EVOLVE-BLOCK-END

```

Here are the performance metrics of the program:

Combined score to maximize: 0.21
mean_offline_error: 3.77; worst_case_offline_error: 10.35; case_error_std: 2.30; cases_completed: 16

Here is additional text feedback about the current program:

Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.850910; mean error remaining at interval end 1.3566; detection used 15.83% and memory refresh 1.36% of objective evaluations; 273 responses with mean radius 0.651213 (mean multiplier 1.30243), allocated fraction 0.767766, and adapter encoding fraction 0.667766 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 44, "4": 229, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 44, "4": 229, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 44, "4": 229, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.559943; mean error remaining at interval end 0.572768; detection used 15.88% and memory refresh 1.82% of objective evaluations; 365 responses with mean radius 0.652568 (mean multiplier 1.30514), allocated fraction 0.776438, and adapter encoding fraction 0.676438 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 43, "4": 322, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 43, "4": 322, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 43, "4": 322, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.592974; mean error remaining at interval end 1.27704; detection used 15.89% and memory refresh 1.52% of objective evaluations; 303 responses with mean radius 0.651712 (mean multiplier 1.30342), allocated fraction 0.770957, and adapter encoding fraction 0.670957 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 44, "4": 259, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 44, "4": 259, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 44, "4": 259, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.980775; mean error remaining at interval end 2.63811; detection used 15.83% and memory refresh 1.46% of objective evaluations; 291 responses with mean radius 0.651632 (mean multiplier 1.30326), allocated fraction 0.770447, and adapter encoding fraction 0.670447 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 43, "4": 248, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 43, "4": 248, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 43, "4": 248, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.776384; mean error remaining at interval end 1.29741; detection used 16.03% and memory refresh 0.71% of objective evaluations; 143 responses with mean radius 0.651661 (mean multiplier 1.30332), allocated fraction 0.770629, and adapter encoding fraction 0.670629 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 21, "4": 122, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 21, "4": 122, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 21, "4": 122, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.327548; mean error remaining at interval end 0.494961; detection used 15.96% and memory refresh 0.60% of objective evaluations; 121 responses with mean radius 0.651601 (mean multiplier 1.3032), allocated fraction 0.770248, and adapter encoding fraction 0.670248 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 18, "4": 103, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 18, "4": 103, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 18, "4": 103, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.242784; mean error remaining at interval end 0.376561; detection used 16.04% and memory refresh 0.59% of objective evaluations; 118 responses with mean radius 0.650953 (mean multiplier 1.30191), allocated fraction 0.766102, and adapter encoding fraction 0.666102 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 20, "4": 98, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 20, "4": 98, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 20, "4": 98, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.114894; mean error remaining at interval end 1.57898; detection used 15.85% and memory refresh 0.54% of objective evaluations; 108 responses with mean radius 0.650463 (mean multiplier 1.30093), allocated fraction 0.762963, and adapter encoding fraction 0.662963 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 20, "4": 88, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 20, "4": 88, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 20, "4": 88, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.200140; mean error remaining at interval end 1.49883; detection used 16.00% and memory refresh 1.79% of objective evaluations; 358 responses with mean radius 1.9567 (mean multiplier 1.30447), allocated fraction 0.774302, and adapter encoding fraction 0.674302 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 46, "4": 312, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 46, "4": 312, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 46, "4": 312, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.321190; mean error remaining at interval end 1.17503; detection used 15.98% and memory refresh 1.64% of objective evaluations; 327 responses with mean radius 1.95614 (mean multiplier 1.30409), allocated fraction 0.773089, and adapter encoding fraction 0.673089 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 44, "4": 283, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 44, "4": 283, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 44, "4": 283, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.612615; mean error remaining at interval end 2.38051; detection used 15.85% and memory refresh 1.41% of objective evaluations; 282 responses with mean radius 1.95512 (mean multiplier 1.30341), allocated fraction 0.770922, and adapter encoding fraction 0.670922 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 41, "4": 241, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 41, "4": 241, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 41, "4": 241, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.336785; mean error remaining at interval end 2.69915; detection used 15.94% and memory refresh 1.69% of objective evaluations; 337 responses with mean radius 1.95707 (mean multiplier 1.30471), allocated fraction 0.775074, and adapter encoding fraction 0.675074 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 42, "4": 295, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 42, "4": 295, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 42, "4": 295, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 5.450692; mean error remaining at interval end 4.30072; detection used 15.95% and memory refresh 0.50% of objective evaluations; 100 responses with mean radius 1.95281 (mean multiplier 1.30187), allocated fraction 0.766, and adapter encoding fraction 0.666 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 17, "4": 83, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 17, "4": 83, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 17, "4": 83, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.283539; mean error remaining at interval end 0.403442; detection used 16.07% and memory refresh 0.83% of objective evaluations; 165 responses with mean radius 1.95682 (mean multiplier 1.30455), allocated fraction 0.774545, and adapter encoding fraction 0.674545 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 21, "4": 144, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 21, "4": 144, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 21, "4": 144, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.330177; mean error remaining at interval end 1.60685; detection used 15.31% and memory refresh 0.28% of objective evaluations; 56 responses with mean radius 1.94196 (mean multiplier 1.29464), allocated fraction 0.742857, and adapter encoding fraction 0.642857 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 16, "4": 40, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 16, "4": 40, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 16, "4": 40, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 10.348679; mean error remaining at interval end 7.94952; detection used 15.86% and memory refresh 0.58% of objective evaluations; 117 responses with mean radius 1.95593 (mean multiplier 1.30395), allocated fraction 0.77265, and adapter encoding fraction 0.67265 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 16, "4": 101, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 16, "4": 101, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 16, "4": 101, "5": 0}. Largest tracking error: case_015. Examine joint integer allocation and radius multiplier using public observed state, with all memories reevaluated and retained velocities fixed. Allocated fraction is allocated_count/swarm_size; the adapter encoding fraction only encodes an integer for the ceiling rule. Allocated counts are selected indices, not a claim of completed movement; horizon-truncated responses separately retain counts with objective queries. Constant count/radius pairs are permitted and receive no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


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
    q = observation["swarm_diameter"] / max(observation["default_radius"], 1e-12)
    count = 3 if q > 5.0 else 4
    return {"count": min(count, int(observation["swarm_size"])), "radius_scale": 1.25}
# EVOLVE-BLOCK-END

```

Performance metrics: Combined score to maximize: 0.21
mean_offline_error: 3.68; worst_case_offline_error: 9.42; case_error_std: 2.09; cases_completed: 16


