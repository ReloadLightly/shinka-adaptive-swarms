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

**Test the remaining narrow threshold interval.** Keep radius `1.25` and implement `count = 3 if q > 4.5 else 4`, preserving the clamp. G20’s threshold five nearly matches G11, whereas six performs worse, so testing the midpoint between four and five is better supported than continuing to raise the threshold.
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
    """Test wider partial relocation after substantial loss in a compact swarm."""
    swarm_size = int(observation["swarm_size"])
    count = 4
    radius_scale = 1.0
    if (
        observation["relative_fitness_drop"] > 0.1
        and observation["swarm_diameter"] < 2.0 * observation["default_radius"]
    ):
        count = 3
        radius_scale = 1.5
    return {
        "count": max(0, min(swarm_size, count)),
        "radius_scale": radius_scale,
    }
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.20
mean_offline_error: 3.98; worst_case_offline_error: 10.13; case_error_std: 2.30; cases_completed: 16

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 4.798415; mean error remaining at interval end 3.25709; detection used 15.72% and memory refresh 1.12% of objective evaluations; 224 responses with mean radius 0.61942 (mean multiplier 1.23884), allocated fraction 0.704464, and adapter encoding fraction 0.604464 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 107, "4": 117, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 107, "4": 117, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 107, "4": 117, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.592788; mean error remaining at interval end 0.545359; detection used 15.87% and memory refresh 1.94% of objective evaluations; 388 responses with mean radius 0.63982 (mean multiplier 1.27964), allocated fraction 0.688144, and adapter encoding fraction 0.588144 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 217, "4": 171, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 217, "4": 171, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 217, "4": 171, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.004631; mean error remaining at interval end 1.53177; detection used 15.89% and memory refresh 1.40% of objective evaluations; 280 responses with mean radius 0.623214 (mean multiplier 1.24643), allocated fraction 0.701429, and adapter encoding fraction 0.601429 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 138, "4": 142, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 138, "4": 142, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 138, "4": 142, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.816196; mean error remaining at interval end 2.61865; detection used 15.80% and memory refresh 1.33% of objective evaluations; 267 responses with mean radius 0.61985 (mean multiplier 1.2397), allocated fraction 0.70412, and adapter encoding fraction 0.60412 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 128, "4": 139, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 128, "4": 139, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 128, "4": 139, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.764005; mean error remaining at interval end 1.22325; detection used 16.05% and memory refresh 0.78% of objective evaluations; 156 responses with mean radius 0.583333 (mean multiplier 1.16667), allocated fraction 0.733333, and adapter encoding fraction 0.633333 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 52, "4": 104, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 52, "4": 104, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 52, "4": 104, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.317176; mean error remaining at interval end 0.492004; detection used 15.82% and memory refresh 0.51% of objective evaluations; 101 responses with mean radius 0.589109 (mean multiplier 1.17822), allocated fraction 0.728713, and adapter encoding fraction 0.628713 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 36, "4": 65, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 36, "4": 65, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 36, "4": 65, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.015655; mean error remaining at interval end 1.22945; detection used 15.95% and memory refresh 0.48% of objective evaluations; 97 responses with mean radius 0.613402 (mean multiplier 1.2268), allocated fraction 0.709278, and adapter encoding fraction 0.609278 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 44, "4": 53, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 44, "4": 53, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 44, "4": 53, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.599821; mean error remaining at interval end 1.15123; detection used 15.89% and memory refresh 0.58% of objective evaluations; 116 responses with mean radius 0.592672 (mean multiplier 1.18534), allocated fraction 0.725862, and adapter encoding fraction 0.625862 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 43, "4": 73, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 43, "4": 73, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 43, "4": 73, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 6.249686; mean error remaining at interval end 2.82042; detection used 15.97% and memory refresh 1.67% of objective evaluations; 333 responses with mean radius 2.08108 (mean multiplier 1.38739), allocated fraction 0.645045, and adapter encoding fraction 0.545045 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 258, "4": 75, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 258, "4": 75, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 258, "4": 75, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.660651; mean error remaining at interval end 1.34618; detection used 15.97% and memory refresh 1.62% of objective evaluations; 323 responses with mean radius 2.10604 (mean multiplier 1.40402), allocated fraction 0.63839, and adapter encoding fraction 0.53839 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 261, "4": 62, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 261, "4": 62, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 261, "4": 62, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 6.087659; mean error remaining at interval end 2.42613; detection used 15.85% and memory refresh 1.37% of objective evaluations; 274 responses with mean radius 2.08029 (mean multiplier 1.38686), allocated fraction 0.645255, and adapter encoding fraction 0.545255 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 212, "4": 62, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 212, "4": 62, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 212, "4": 62, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.233745; mean error remaining at interval end 2.17521; detection used 15.93% and memory refresh 1.65% of objective evaluations; 329 responses with mean radius 2.07219 (mean multiplier 1.38146), allocated fraction 0.647416, and adapter encoding fraction 0.547416 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 251, "4": 78, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 251, "4": 78, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 251, "4": 78, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 5.040340; mean error remaining at interval end 3.47617; detection used 15.91% and memory refresh 0.47% of objective evaluations; 94 responses with mean radius 1.99468 (mean multiplier 1.32979), allocated fraction 0.668085, and adapter encoding fraction 0.568085 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 62, "4": 32, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 62, "4": 32, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 62, "4": 32, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.307776; mean error remaining at interval end 0.405467; detection used 16.09% and memory refresh 0.88% of objective evaluations; 176 responses with mean radius 2.11364 (mean multiplier 1.40909), allocated fraction 0.636364, and adapter encoding fraction 0.536364 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 144, "4": 32, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 144, "4": 32, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 144, "4": 32, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.114699; mean error remaining at interval end 1.60356; detection used 15.24% and memory refresh 0.30% of objective evaluations; 61 responses with mean radius 1.83197 (mean multiplier 1.22131), allocated fraction 0.711475, and adapter encoding fraction 0.611475 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 27, "4": 34, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 27, "4": 34, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 27, "4": 34, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 10.127117; mean error remaining at interval end 7.80183; detection used 15.78% and memory refresh 0.52% of objective evaluations; 104 responses with mean radius 2.03365 (mean multiplier 1.35577), allocated fraction 0.657692, and adapter encoding fraction 0.557692 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 74, "4": 30, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 74, "4": 30, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 74, "4": 30, "5": 0}. Largest tracking error: case_015. Examine joint integer allocation and radius multiplier using public observed state, with all memories reevaluated and retained velocities fixed. Allocated fraction is allocated_count/swarm_size; the adapter encoding fraction only encodes an integer for the ceiling rule. Allocated counts are selected indices, not a claim of completed movement; horizon-truncated responses separately retain counts with objective queries. Constant count/radius pairs are permitted and receive no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.

```python
"""Joint relocation seed: the original corrected baseline response.

The adapter fixes memory reevaluation and retained velocities. It converts the
integer count to the unchanged simulator's fraction interface without rounding
ambiguity. The seed allocates every particle at the baseline radius multiplier.
"""


# EVOLVE-BLOCK-START
def choose_relocation(observation: dict) -> dict:
    """Reduce relocation allocation when the swarm is already dispersed."""
    swarm_size = int(observation["swarm_size"])
    default_radius = max(float(observation["default_radius"]), 1e-12)
    relative_spread = float(observation["swarm_diameter"]) / default_radius
    requested_count = 3 if relative_spread > 4.0 else 4
    return {
        "count": max(0, min(swarm_size, requested_count)),
        "radius_scale": 1.25,
    }
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.21
mean_offline_error: 3.67; worst_case_offline_error: 9.42; case_error_std: 2.08; cases_completed: 16

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.568729; mean error remaining at interval end 2.09144; detection used 15.82% and memory refresh 1.31% of objective evaluations; 263 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.769582, and adapter encoding fraction 0.669582 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 40, "4": 223, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 40, "4": 223, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 40, "4": 223, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.870004; mean error remaining at interval end 1.22195; detection used 15.90% and memory refresh 1.66% of objective evaluations; 332 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.775301, and adapter encoding fraction 0.675301 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 41, "4": 291, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 41, "4": 291, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 41, "4": 291, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.487836; mean error remaining at interval end 1.27386; detection used 15.91% and memory refresh 1.52% of objective evaluations; 304 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.773684, and adapter encoding fraction 0.673684 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 40, "4": 264, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 40, "4": 264, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 40, "4": 264, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.550240; mean error remaining at interval end 2.14023; detection used 15.83% and memory refresh 1.62% of objective evaluations; 323 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.770898, and adapter encoding fraction 0.670898 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 47, "4": 276, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 47, "4": 276, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 47, "4": 276, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.725605; mean error remaining at interval end 1.29137; detection used 16.06% and memory refresh 0.70% of objective evaluations; 141 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.770213, and adapter encoding fraction 0.670213 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 21, "4": 120, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 21, "4": 120, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 21, "4": 120, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.262604; mean error remaining at interval end 0.496853; detection used 15.96% and memory refresh 0.60% of objective evaluations; 121 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.768595, and adapter encoding fraction 0.668595 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 19, "4": 102, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 19, "4": 102, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 19, "4": 102, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.295352; mean error remaining at interval end 0.372626; detection used 16.05% and memory refresh 0.58% of objective evaluations; 116 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.768966, and adapter encoding fraction 0.668966 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 18, "4": 98, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 18, "4": 98, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 18, "4": 98, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.078156; mean error remaining at interval end 1.57973; detection used 15.86% and memory refresh 0.56% of objective evaluations; 113 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.761062, and adapter encoding fraction 0.661062 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 22, "4": 91, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 22, "4": 91, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 22, "4": 91, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.004653; mean error remaining at interval end 1.49974; detection used 16.00% and memory refresh 1.75% of objective evaluations; 350 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.774857, and adapter encoding fraction 0.674857 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 44, "4": 306, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 44, "4": 306, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 44, "4": 306, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.064942; mean error remaining at interval end 1.10549; detection used 15.97% and memory refresh 1.50% of objective evaluations; 301 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.774086, and adapter encoding fraction 0.674086 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 39, "4": 262, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 39, "4": 262, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 39, "4": 262, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.492178; mean error remaining at interval end 2.4227; detection used 15.86% and memory refresh 1.40% of objective evaluations; 280 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.771429, and adapter encoding fraction 0.671429 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 40, "4": 240, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 40, "4": 240, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 40, "4": 240, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.200737; mean error remaining at interval end 2.17183; detection used 15.97% and memory refresh 1.75% of objective evaluations; 349 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.774212, and adapter encoding fraction 0.674212 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 45, "4": 304, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 45, "4": 304, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 45, "4": 304, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 5.188948; mean error remaining at interval end 3.96992; detection used 15.95% and memory refresh 0.50% of objective evaluations; 100 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.768, and adapter encoding fraction 0.668 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 16, "4": 84, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 16, "4": 84, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 16, "4": 84, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.216257; mean error remaining at interval end 0.468883; detection used 16.11% and memory refresh 0.83% of objective evaluations; 165 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.774545, and adapter encoding fraction 0.674545 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 21, "4": 144, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 21, "4": 144, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 21, "4": 144, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.263131; mean error remaining at interval end 1.60416; detection used 15.32% and memory refresh 0.33% of objective evaluations; 65 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.738462, and adapter encoding fraction 0.638462 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 20, "4": 45, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 20, "4": 45, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 20, "4": 45, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 9.423029; mean error remaining at interval end 7.23657; detection used 15.86% and memory refresh 0.58% of objective evaluations; 117 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.77265, and adapter encoding fraction 0.67265 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 16, "4": 101, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 16, "4": 101, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 16, "4": 101, "5": 0}. Largest tracking error: case_015. Examine joint integer allocation and radius multiplier using public observed state, with all memories reevaluated and retained velocities fixed. Allocated fraction is allocated_count/swarm_size; the adapter encoding fraction only encodes an integer for the ceiling rule. Allocated counts are selected indices, not a claim of completed movement; horizon-truncated responses separately retain counts with objective queries. Constant count/radius pairs are permitted and receive no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


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
    """Relocate three particles when relative spread exceeds 4.5, otherwise four."""
    swarm_size = int(observation["swarm_size"])
    default_radius = max(float(observation["default_radius"]), 1e-12)
    relative_spread = float(observation["swarm_diameter"]) / default_radius
    requested_count = 3 if relative_spread > 4.5 else 4
    return {
        "count": max(0, min(swarm_size, requested_count)),
        "radius_scale": 1.25,
    }
# EVOLVE-BLOCK-END

```

Here are the performance metrics of the program:

Combined score to maximize: 0.21
mean_offline_error: 3.66; worst_case_offline_error: 9.42; case_error_std: 2.08; cases_completed: 16

Here is additional text feedback about the current program:

Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.568729; mean error remaining at interval end 2.09144; detection used 15.82% and memory refresh 1.31% of objective evaluations; 263 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.769582, and adapter encoding fraction 0.669582 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 40, "4": 223, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 40, "4": 223, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 40, "4": 223, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.870004; mean error remaining at interval end 1.22195; detection used 15.90% and memory refresh 1.66% of objective evaluations; 332 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.775301, and adapter encoding fraction 0.675301 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 41, "4": 291, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 41, "4": 291, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 41, "4": 291, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.465982; mean error remaining at interval end 1.23121; detection used 15.91% and memory refresh 1.52% of objective evaluations; 304 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.774342, and adapter encoding fraction 0.674342 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 39, "4": 265, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 39, "4": 265, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 39, "4": 265, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.488693; mean error remaining at interval end 2.14969; detection used 15.82% and memory refresh 1.60% of objective evaluations; 320 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.7725, and adapter encoding fraction 0.6725 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 44, "4": 276, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 44, "4": 276, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 44, "4": 276, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.725605; mean error remaining at interval end 1.29137; detection used 16.06% and memory refresh 0.70% of objective evaluations; 141 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.770213, and adapter encoding fraction 0.670213 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 21, "4": 120, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 21, "4": 120, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 21, "4": 120, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.262604; mean error remaining at interval end 0.496853; detection used 15.96% and memory refresh 0.60% of objective evaluations; 121 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.768595, and adapter encoding fraction 0.668595 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 19, "4": 102, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 19, "4": 102, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 19, "4": 102, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.295352; mean error remaining at interval end 0.372626; detection used 16.05% and memory refresh 0.58% of objective evaluations; 116 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.768966, and adapter encoding fraction 0.668966 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 18, "4": 98, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 18, "4": 98, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 18, "4": 98, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.078156; mean error remaining at interval end 1.57973; detection used 15.86% and memory refresh 0.56% of objective evaluations; 113 responses with mean radius 0.625 (mean multiplier 1.25), allocated fraction 0.761062, and adapter encoding fraction 0.661062 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 22, "4": 91, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 22, "4": 91, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 22, "4": 91, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.004653; mean error remaining at interval end 1.49974; detection used 16.00% and memory refresh 1.75% of objective evaluations; 350 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.774857, and adapter encoding fraction 0.674857 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 44, "4": 306, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 44, "4": 306, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 44, "4": 306, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.064942; mean error remaining at interval end 1.10549; detection used 15.97% and memory refresh 1.50% of objective evaluations; 301 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.774086, and adapter encoding fraction 0.674086 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 39, "4": 262, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 39, "4": 262, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 39, "4": 262, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.492178; mean error remaining at interval end 2.4227; detection used 15.86% and memory refresh 1.40% of objective evaluations; 280 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.771429, and adapter encoding fraction 0.671429 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 40, "4": 240, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 40, "4": 240, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 40, "4": 240, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.200737; mean error remaining at interval end 2.17183; detection used 15.97% and memory refresh 1.75% of objective evaluations; 349 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.774212, and adapter encoding fraction 0.674212 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 45, "4": 304, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 45, "4": 304, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 45, "4": 304, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 5.188948; mean error remaining at interval end 3.96992; detection used 15.95% and memory refresh 0.50% of objective evaluations; 100 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.768, and adapter encoding fraction 0.668 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 16, "4": 84, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 16, "4": 84, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 16, "4": 84, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.216257; mean error remaining at interval end 0.468883; detection used 16.11% and memory refresh 0.83% of objective evaluations; 165 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.774545, and adapter encoding fraction 0.674545 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 21, "4": 144, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 21, "4": 144, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 21, "4": 144, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.263131; mean error remaining at interval end 1.60416; detection used 15.32% and memory refresh 0.33% of objective evaluations; 65 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.738462, and adapter encoding fraction 0.638462 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 20, "4": 45, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 20, "4": 45, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 20, "4": 45, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 9.423029; mean error remaining at interval end 7.23657; detection used 15.86% and memory refresh 0.58% of objective evaluations; 117 responses with mean radius 1.875 (mean multiplier 1.25), allocated fraction 0.77265, and adapter encoding fraction 0.67265 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 16, "4": 101, "5": 0}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 16, "4": 101, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 16, "4": 101, "5": 0}. Largest tracking error: case_015. Examine joint integer allocation and radius multiplier using public observed state, with all memories reevaluated and retained velocities fixed. Allocated fraction is allocated_count/swarm_size; the adapter encoding fraction only encodes an integer for the ceiling rule. Allocated counts are selected indices, not a claim of completed movement; horizon-truncated responses separately retain counts with objective queries. Constant count/radius pairs are permitted and receive no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


# Task

Rewrite the program to improve its performance on the specified metrics.
Provide the complete new program code.

IMPORTANT: Make sure your rewritten program maintains the same inputs and outputs as the original program, but with improved internal implementation.
