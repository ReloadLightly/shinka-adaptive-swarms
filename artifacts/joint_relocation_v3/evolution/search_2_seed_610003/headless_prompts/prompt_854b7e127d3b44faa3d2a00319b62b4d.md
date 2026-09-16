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

**Bracket G14’s fitness-loss threshold.** Create separate mutations replacing `0.075` with `0.0625` and `0.0875`, keeping the diameter condition, four-particle default, and radius multiplier `1.5`. G14’s advantage over G6 supports refining this boundary, but does not establish that further increases will help.
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
    """Select relocation intensity from observed loss and recent improvement."""
    swarm_size = int(observation["swarm_size"])
    loss = observation["fitness_drop"]
    recent_gain = max(observation["recent_improvement"], 0.0)
    # Assess whether observed deterioration exceeds recent progress.
    uncovered_loss = loss > recent_gain
    substantial_loss = observation["relative_fitness_drop"] > 0.1
    # Preserve ordinary PSO motion for more particles after smaller losses.
    if uncovered_loss and substantial_loss:
        requested_count = swarm_size
    elif uncovered_loss:
        requested_count = 4
    else:
        requested_count = 3
    return {
        "count": min(requested_count, swarm_size),
        "radius_scale": 1.5,
    }
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.20
mean_offline_error: 4.12; worst_case_offline_error: 12.00; case_error_std: 2.65; cases_completed: 16

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 5.301259; mean error remaining at interval end 4.18688; detection used 15.72% and memory refresh 1.04% of objective evaluations; 209 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.850718, and adapter encoding fraction 0.750718 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 54, "4": 48, "5": 107}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 54, "4": 48, "5": 107}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 54, "4": 48, "5": 107}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.299773; mean error remaining at interval end 1.28857; detection used 15.85% and memory refresh 1.66% of objective evaluations; 332 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.889157, and adapter encoding fraction 0.789157 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 62, "4": 60, "5": 210}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 62, "4": 60, "5": 210}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 62, "4": 60, "5": 210}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 4.434035; mean error remaining at interval end 3.1769; detection used 15.84% and memory refresh 1.29% of objective evaluations; 258 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.866667, and adapter encoding fraction 0.766667 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 62, "4": 48, "5": 148}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 62, "4": 48, "5": 148}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 62, "4": 48, "5": 148}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.934903; mean error remaining at interval end 1.66823; detection used 15.81% and memory refresh 1.30% of objective evaluations; 260 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.865385, and adapter encoding fraction 0.765385 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 61, "4": 53, "5": 146}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 61, "4": 53, "5": 146}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 61, "4": 53, "5": 146}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.749876; mean error remaining at interval end 1.20649; detection used 16.06% and memory refresh 0.73% of objective evaluations; 147 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.831293, and adapter encoding fraction 0.731293 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 36, "4": 52, "5": 59}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 36, "4": 52, "5": 59}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 36, "4": 52, "5": 59}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.229153; mean error remaining at interval end 0.489241; detection used 15.86% and memory refresh 0.54% of objective evaluations; 108 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.824074, and adapter encoding fraction 0.724074 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 33, "4": 29, "5": 46}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 33, "4": 29, "5": 46}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 33, "4": 29, "5": 46}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.867117; mean error remaining at interval end 1.19198; detection used 16.00% and memory refresh 0.57% of objective evaluations; 115 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.874783, and adapter encoding fraction 0.774783 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 24, "4": 24, "5": 67}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 24, "4": 24, "5": 67}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 24, "4": 24, "5": 67}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.644975; mean error remaining at interval end 1.15597; detection used 15.96% and memory refresh 0.64% of objective evaluations; 127 responses with mean radius 0.75 (mean multiplier 1.5), allocated fraction 0.864567, and adapter encoding fraction 0.764567 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 29, "4": 28, "5": 70}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 29, "4": 28, "5": 70}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 29, "4": 28, "5": 70}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.988658; mean error remaining at interval end 1.75867; detection used 15.96% and memory refresh 1.64% of objective evaluations; 327 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.952905, and adapter encoding fraction 0.852905 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 29, "4": 19, "5": 279}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 29, "4": 19, "5": 279}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 29, "4": 19, "5": 279}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.808105; mean error remaining at interval end 1.78961; detection used 15.98% and memory refresh 1.52% of objective evaluations; 304 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.961842, and adapter encoding fraction 0.861842 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 25, "4": 8, "5": 271}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 25, "4": 8, "5": 271}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 25, "4": 8, "5": 271}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 6.742821; mean error remaining at interval end 3.55981; detection used 15.92% and memory refresh 1.62% of objective evaluations; 323 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.972755, and adapter encoding fraction 0.872755 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 18, "4": 8, "5": 297}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 18, "4": 8, "5": 297}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 18, "4": 8, "5": 297}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.190470; mean error remaining at interval end 2.47318; detection used 15.95% and memory refresh 1.62% of objective evaluations; 324 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.953086, and adapter encoding fraction 0.853086 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 26, "4": 24, "5": 274}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 26, "4": 24, "5": 274}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 26, "4": 24, "5": 274}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 4.407165; mean error remaining at interval end 3.34013; detection used 15.86% and memory refresh 0.46% of objective evaluations; 91 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.916484, and adapter encoding fraction 0.816484 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 15, "4": 8, "5": 68}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 15, "4": 8, "5": 68}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 15, "4": 8, "5": 68}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.201033; mean error remaining at interval end 0.393244; detection used 16.02% and memory refresh 0.74% of objective evaluations; 148 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.954054, and adapter encoding fraction 0.854054 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 14, "4": 6, "5": 128}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 14, "4": 6, "5": 128}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 14, "4": 6, "5": 128}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.108822; mean error remaining at interval end 1.60401; detection used 15.42% and memory refresh 0.36% of objective evaluations; 71 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.88169, and adapter encoding fraction 0.78169 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 15, "4": 12, "5": 44}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 15, "4": 12, "5": 44}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 15, "4": 12, "5": 44}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 11.996546; mean error remaining at interval end 10.7546; detection used 15.72% and memory refresh 0.52% of objective evaluations; 103 responses with mean radius 2.25 (mean multiplier 1.5), allocated fraction 0.937864, and adapter encoding fraction 0.837864 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 13, "4": 6, "5": 84}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 13, "4": 6, "5": 84}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 13, "4": 6, "5": 84}. Largest tracking error: case_015. Examine joint integer allocation and radius multiplier using public observed state, with all memories reevaluated and retained velocities fixed. Allocated fraction is allocated_count/swarm_size; the adapter encoding fraction only encodes an integer for the ceiling rule. Allocated counts are selected indices, not a claim of completed movement; horizon-truncated responses separately retain counts with objective queries. Constant count/radius pairs are permitted and receive no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.

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

Here are the performance metrics of the program:

Combined score to maximize: 0.21
mean_offline_error: 3.81; worst_case_offline_error: 12.11; case_error_std: 2.63; cases_completed: 16

Here is additional text feedback about the current program:

Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.488098; mean error remaining at interval end 1.9055; detection used 15.81% and memory refresh 1.39% of objective evaluations; 277 responses with mean radius 0.644066 (mean multiplier 1.28813), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 277, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 277, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 277, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.420737; mean error remaining at interval end 0.457378; detection used 15.90% and memory refresh 1.90% of objective evaluations; 380 responses with mean radius 0.646575 (mean multiplier 1.29315), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 380, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 380, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 380, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.666927; mean error remaining at interval end 1.34878; detection used 15.85% and memory refresh 1.45% of objective evaluations; 290 responses with mean radius 0.642997 (mean multiplier 1.28599), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 290, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 290, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 290, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.196137; mean error remaining at interval end 0.998796; detection used 15.85% and memory refresh 1.38% of objective evaluations; 275 responses with mean radius 0.643063 (mean multiplier 1.28613), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 275, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 275, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 275, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.819274; mean error remaining at interval end 1.24349; detection used 16.04% and memory refresh 0.74% of objective evaluations; 149 responses with mean radius 0.640486 (mean multiplier 1.28097), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 149, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 149, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 149, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.190208; mean error remaining at interval end 0.492092; detection used 15.85% and memory refresh 0.52% of objective evaluations; 103 responses with mean radius 0.635222 (mean multiplier 1.27044), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 103, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.780528; mean error remaining at interval end 3.28619; detection used 15.98% and memory refresh 0.56% of objective evaluations; 111 responses with mean radius 0.638996 (mean multiplier 1.27799), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 111, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 111, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 111, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.445180; mean error remaining at interval end 0.895205; detection used 15.89% and memory refresh 0.60% of objective evaluations; 121 responses with mean radius 0.640617 (mean multiplier 1.28123), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 121, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 121, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 121, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 6.088332; mean error remaining at interval end 2.77772; detection used 16.02% and memory refresh 1.76% of objective evaluations; 352 responses with mean radius 1.93233 (mean multiplier 1.28822), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 352, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 352, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 352, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.167384; mean error remaining at interval end 1.11968; detection used 16.00% and memory refresh 1.65% of objective evaluations; 331 responses with mean radius 1.93184 (mean multiplier 1.28789), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 331, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 331, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 331, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.765256; mean error remaining at interval end 2.56302; detection used 15.87% and memory refresh 1.39% of objective evaluations; 278 responses with mean radius 1.92819 (mean multiplier 1.28546), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 278, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 278, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 278, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.523412; mean error remaining at interval end 0.966383; detection used 15.96% and memory refresh 1.89% of objective evaluations; 378 responses with mean radius 1.934 (mean multiplier 1.28933), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 378, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 378, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 378, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.628899; mean error remaining at interval end 1.91489; detection used 15.96% and memory refresh 0.57% of objective evaluations; 114 responses with mean radius 1.91542 (mean multiplier 1.27695), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 114, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 114, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 114, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.618309; mean error remaining at interval end 0.422826; detection used 16.09% and memory refresh 0.89% of objective evaluations; 178 responses with mean radius 1.92967 (mean multiplier 1.28645), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 178, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 178, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 178, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.048655; mean error remaining at interval end 1.60343; detection used 15.31% and memory refresh 0.29% of objective evaluations; 58 responses with mean radius 1.88741 (mean multiplier 1.25827), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 58, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 58, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 58, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 12.105623; mean error remaining at interval end 10.3849; detection used 15.79% and memory refresh 0.56% of objective evaluations; 111 responses with mean radius 1.91239 (mean multiplier 1.27493), allocated fraction 0.8, and adapter encoding fraction 0.7 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 111, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 111, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 111, "5": 0}. Largest tracking error: case_015. Examine joint integer allocation and radius multiplier using public observed state, with all memories reevaluated and retained velocities fixed. Allocated fraction is allocated_count/swarm_size; the adapter encoding fraction only encodes an integer for the ceiling rule. Allocated counts are selected indices, not a claim of completed movement; horizon-truncated responses separately retain counts with objective queries. Constant count/radius pairs are permitted and receive no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


# Task

Rewrite the program to improve its performance on the specified metrics.
Provide the complete new program code.

IMPORTANT: Make sure your rewritten program maintains the same inputs and outputs as the original program, but with improved internal implementation.
