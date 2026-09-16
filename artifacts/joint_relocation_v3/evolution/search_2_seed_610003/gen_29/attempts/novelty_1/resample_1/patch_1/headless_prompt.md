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
    """Relocate up to four particles at 1.375 times the default radius.
    With five particles, four relocate and one continues ordinary PSO motion.
    The fixed adapter reevaluates memories and retains velocities.
    """
    count = min(4, int(observation["swarm_size"]))
    return {"count": count, "radius_scale": 1.375}
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.20
mean_offline_error: 4.10; worst_case_offline_error: 12.79; case_error_std: 2.97; cases_completed: 16

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.765510; mean error remaining at interval end 1.24938; detection used 15.83% and memory refresh 1.54% of objective evaluations; 309 responses with mean radius 0.6875 (mean multiplier 1.375), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 309, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 309, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 309, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.304396; mean error remaining at interval end 0.442463; detection used 15.89% and memory refresh 1.93% of objective evaluations; 386 responses with mean radius 0.6875 (mean multiplier 1.375), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 386, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 386, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 386, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.672469; mean error remaining at interval end 1.33016; detection used 15.88% and memory refresh 1.45% of objective evaluations; 290 responses with mean radius 0.6875 (mean multiplier 1.375), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 290, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 290, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 290, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.839303; mean error remaining at interval end 2.50939; detection used 15.78% and memory refresh 1.38% of objective evaluations; 276 responses with mean radius 0.6875 (mean multiplier 1.375), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 276, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 276, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 276, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.732260; mean error remaining at interval end 1.22568; detection used 16.04% and memory refresh 0.75% of objective evaluations; 150 responses with mean radius 0.6875 (mean multiplier 1.375), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 150, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 150, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 150, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.162979; mean error remaining at interval end 0.491202; detection used 15.85% and memory refresh 0.52% of objective evaluations; 103 responses with mean radius 0.6875 (mean multiplier 1.375), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.794325; mean error remaining at interval end 3.28729; detection used 15.98% and memory refresh 0.56% of objective evaluations; 111 responses with mean radius 0.6875 (mean multiplier 1.375), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 111, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 111, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 111, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.339948; mean error remaining at interval end 0.893232; detection used 15.87% and memory refresh 0.56% of objective evaluations; 111 responses with mean radius 0.6875 (mean multiplier 1.375), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 111, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 111, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 111, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.935656; mean error remaining at interval end 2.55176; detection used 16.04% and memory refresh 1.78% of objective evaluations; 356 responses with mean radius 2.0625 (mean multiplier 1.375), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 356, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 356, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 356, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.045103; mean error remaining at interval end 0.871901; detection used 15.94% and memory refresh 1.52% of objective evaluations; 305 responses with mean radius 2.0625 (mean multiplier 1.375), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 305, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 305, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 305, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 8.364445; mean error remaining at interval end 5.42581; detection used 15.86% and memory refresh 1.27% of objective evaluations; 254 responses with mean radius 2.0625 (mean multiplier 1.375), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 254, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 254, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 254, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.556245; mean error remaining at interval end 2.30806; detection used 15.95% and memory refresh 1.69% of objective evaluations; 338 responses with mean radius 2.0625 (mean multiplier 1.375), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 338, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 338, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 338, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.860383; mean error remaining at interval end 1.87952; detection used 15.94% and memory refresh 0.55% of objective evaluations; 110 responses with mean radius 2.0625 (mean multiplier 1.375), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 110, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 110, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 110, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.356509; mean error remaining at interval end 0.352515; detection used 16.11% and memory refresh 0.89% of objective evaluations; 177 responses with mean radius 2.0625 (mean multiplier 1.375), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 177, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 177, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 177, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.142013; mean error remaining at interval end 1.60367; detection used 15.53% and memory refresh 0.36% of objective evaluations; 73 responses with mean radius 2.0625 (mean multiplier 1.375), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 73, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 73, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 73, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 12.785219; mean error remaining at interval end 11.1056; detection used 15.73% and memory refresh 0.52% of objective evaluations; 103 responses with mean radius 2.0625 (mean multiplier 1.375), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}. Largest tracking error: case_015. Examine joint integer allocation and radius multiplier using public observed state, with all memories reevaluated and retained velocities fixed. Allocated fraction is allocated_count/swarm_size; the adapter encoding fraction only encodes an integer for the ceiling rule. Allocated counts are selected indices, not a claim of completed movement; horizon-truncated responses separately retain counts with objective queries. Constant count/radius pairs are permitted and receive no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.

```python
"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Combine damped displacement scaling with modest loss-based expansion."""
    count = min(4, int(observation["swarm_size"]))
    default_radius = observation["default_radius"]
    displacement_ratio = observation["observed_best_displacement"] / max(
        default_radius, 1e-12
    )
    radius_scale = 1.25 + 0.125 * max(
        -1.0, min(1.0, displacement_ratio - 1.5)
    )
    if (
        observation["relative_fitness_drop"] > 0.1
        and observation["swarm_diameter"] <= 3.0 * default_radius
    ):
        radius_scale += 0.125
    return {"count": count, "radius_scale": float(radius_scale)}
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.21
mean_offline_error: 3.80; worst_case_offline_error: 11.90; case_error_std: 2.58; cases_completed: 16

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.388350; mean error remaining at interval end 1.78934; detection used 15.83% and memory refresh 1.39% of objective evaluations; 278 responses with mean radius 0.674423 (mean multiplier 1.34885), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 278, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 278, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 278, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.706154; mean error remaining at interval end 0.888172; detection used 15.86% and memory refresh 1.76% of objective evaluations; 353 responses with mean radius 0.681694 (mean multiplier 1.36339), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 353, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 353, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 353, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.762177; mean error remaining at interval end 1.40277; detection used 15.87% and memory refresh 1.44% of objective evaluations; 289 responses with mean radius 0.672789 (mean multiplier 1.34558), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 289, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 289, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 289, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.325573; mean error remaining at interval end 1.12785; detection used 15.85% and memory refresh 1.49% of objective evaluations; 299 responses with mean radius 0.676938 (mean multiplier 1.35388), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 299, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 299, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 299, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.755970; mean error remaining at interval end 1.23055; detection used 16.04% and memory refresh 0.74% of objective evaluations; 149 responses with mean radius 0.663021 (mean multiplier 1.32604), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 149, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 149, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 149, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.170296; mean error remaining at interval end 0.489231; detection used 15.85% and memory refresh 0.52% of objective evaluations; 103 responses with mean radius 0.656569 (mean multiplier 1.31314), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.780993; mean error remaining at interval end 3.28513; detection used 15.99% and memory refresh 0.56% of objective evaluations; 112 responses with mean radius 0.670653 (mean multiplier 1.34131), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 112, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 112, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 112, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.476590; mean error remaining at interval end 0.975025; detection used 15.89% and memory refresh 0.60% of objective evaluations; 121 responses with mean radius 0.665758 (mean multiplier 1.33152), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 121, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 121, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 121, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.695641; mean error remaining at interval end 1.23245; detection used 16.03% and memory refresh 1.78% of objective evaluations; 356 responses with mean radius 2.08319 (mean multiplier 1.38879), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 356, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 356, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 356, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.060241; mean error remaining at interval end 0.920452; detection used 15.96% and memory refresh 1.54% of objective evaluations; 308 responses with mean radius 2.07655 (mean multiplier 1.38437), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 308, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 308, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 308, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.803235; mean error remaining at interval end 2.32174; detection used 15.86% and memory refresh 1.37% of objective evaluations; 274 responses with mean radius 2.08172 (mean multiplier 1.38781), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 274, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 274, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 274, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.984139; mean error remaining at interval end 3.10556; detection used 15.97% and memory refresh 1.73% of objective evaluations; 346 responses with mean radius 2.07859 (mean multiplier 1.38573), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 346, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 346, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 346, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.354376; mean error remaining at interval end 1.72007; detection used 15.95% and memory refresh 0.53% of objective evaluations; 106 responses with mean radius 2.04029 (mean multiplier 1.36019), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 106, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 106, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 106, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.492342; mean error remaining at interval end 0.478857; detection used 16.09% and memory refresh 0.86% of objective evaluations; 173 responses with mean radius 2.08492 (mean multiplier 1.38995), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 173, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 173, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 173, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.061923; mean error remaining at interval end 1.60355; detection used 15.31% and memory refresh 0.29% of objective evaluations; 58 responses with mean radius 1.98763 (mean multiplier 1.32508), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 58, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 58, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 58, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 11.904287; mean error remaining at interval end 10.3728; detection used 15.82% and memory refresh 0.54% of objective evaluations; 108 responses with mean radius 2.05964 (mean multiplier 1.37309), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 108, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 108, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 108, "5": 0}. Largest tracking error: case_015. Examine joint integer allocation and radius multiplier using public observed state, with all memories reevaluated and retained velocities fixed. Allocated fraction is allocated_count/swarm_size; the adapter encoding fraction only encodes an integer for the ceiling rule. Allocated counts are selected indices, not a claim of completed movement; horizon-truncated responses separately retain counts with objective queries. Constant count/radius pairs are permitted and receive no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


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
    """Relocate up to four particles at 1.5 times the default radius."""
    count = min(4, int(observation["swarm_size"]))
    return {"count": count, "radius_scale": 1.5}
# EVOLVE-BLOCK-END

```

Here are the performance metrics of the program:

Combined score to maximize: 0.21
mean_offline_error: 3.81; worst_case_offline_error: 9.18; case_error_std: 2.28; cases_completed: 16

Here is additional text feedback about the current program:

Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.693591; mean error remaining at interval end 2.25605; detection used 15.79% and memory refresh 1.23% of objective evaluations; 246 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 246, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 246, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 246, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.359011; mean error remaining at interval end 0.453908; detection used 15.87% and memory refresh 1.93% of objective evaluations; 385 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 385, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 385, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 385, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.675704; mean error remaining at interval end 1.35852; detection used 15.87% and memory refresh 1.41% of objective evaluations; 282 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 282, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 282, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 282, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.744475; mean error remaining at interval end 2.46768; detection used 15.80% and memory refresh 1.42% of objective evaluations; 283 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 283, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 283, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 283, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.757310; mean error remaining at interval end 1.22994; detection used 16.04% and memory refresh 0.75% of objective evaluations; 150 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 150, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 150, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 150, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.211991; mean error remaining at interval end 0.492377; detection used 15.84% and memory refresh 0.50% of objective evaluations; 100 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 100, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 100, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 100, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.788862; mean error remaining at interval end 3.28552; detection used 15.98% and memory refresh 0.56% of objective evaluations; 111 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 111, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 111, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 111, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.474203; mean error remaining at interval end 0.899091; detection used 15.84% and memory refresh 0.56% of objective evaluations; 113 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 113, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 113, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 113, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.667916; mean error remaining at interval end 1.05621; detection used 15.98% and memory refresh 1.71% of objective evaluations; 342 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 342, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 342, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 342, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 3.982621; mean error remaining at interval end 1.05869; detection used 15.95% and memory refresh 1.47% of objective evaluations; 294 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 294, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 294, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 294, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 9.181107; mean error remaining at interval end 5.8816; detection used 15.90% and memory refresh 1.43% of objective evaluations; 286 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 286, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 286, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 286, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.508388; mean error remaining at interval end 1.08991; detection used 15.98% and memory refresh 1.93% of objective evaluations; 385 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 385, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 385, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 385, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.620115; mean error remaining at interval end 1.91478; detection used 15.93% and memory refresh 0.53% of objective evaluations; 106 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 106, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 106, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 106, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.420150; mean error remaining at interval end 0.452855; detection used 16.08% and memory refresh 0.88% of objective evaluations; 176 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 176, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 176, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 176, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.092057; mean error remaining at interval end 1.60342; detection used 15.25% and memory refresh 0.29% of objective evaluations; 57 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 57, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 57, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 57, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 8.816085; mean error remaining at interval end 6.0212; detection used 15.85% and memory refresh 0.58% of objective evaluations; 117 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 117, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 117, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 117, "5": 0}. Largest tracking error: case_010. Examine joint integer allocation and radius multiplier using public observed state, with all memories reevaluated and retained velocities fixed. Allocated fraction is allocated_count/swarm_size; the adapter encoding fraction only encodes an integer for the ceiling rule. Allocated counts are selected indices, not a claim of completed movement; horizon-truncated responses separately retain counts with objective queries. Constant count/radius pairs are permitted and receive no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


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
    """Relocate up to four particles at 1.375 times the default radius.
    With five particles, four relocate and one continues ordinary PSO motion.
    The fixed adapter reevaluates memories and retains velocities.
    """
    count = min(4, int(observation["swarm_size"]))
    return {"count": count, "radius_scale": 1.375}
# EVOLVE-BLOCK-END

```

Performance metrics: Combined score to maximize: 0.20
mean_offline_error: 4.10; worst_case_offline_error: 12.79; case_error_std: 2.97; cases_completed: 16


