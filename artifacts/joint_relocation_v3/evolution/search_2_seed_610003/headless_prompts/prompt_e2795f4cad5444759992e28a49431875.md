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
    return {"count": observation["swarm_size"], "radius_scale": 1.0}
# EVOLVE-BLOCK-END

```

Here are the performance metrics of the program:

Combined score to maximize: 0.19
mean_offline_error: 4.16; worst_case_offline_error: 12.92; case_error_std: 2.79; cases_completed: 16

Here is additional text feedback about the current program:

Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 4.508795; mean error remaining at interval end 3.27935; detection used 15.73% and memory refresh 1.14% of objective evaluations; 227 responses with mean radius 0.5 (mean multiplier 1), allocated fraction 1, and adapter encoding fraction 0.9 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 227}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 227}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 227}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.539908; mean error remaining at interval end 1.7744; detection used 15.81% and memory refresh 1.65% of objective evaluations; 330 responses with mean radius 0.5 (mean multiplier 1), allocated fraction 1, and adapter encoding fraction 0.9 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 330}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 330}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 330}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.521015; mean error remaining at interval end 1.04454; detection used 15.89% and memory refresh 1.50% of objective evaluations; 300 responses with mean radius 0.5 (mean multiplier 1), allocated fraction 1, and adapter encoding fraction 0.9 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 300}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 300}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 300}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.159082; mean error remaining at interval end 1.81529; detection used 15.73% and memory refresh 1.21% of objective evaluations; 243 responses with mean radius 0.5 (mean multiplier 1), allocated fraction 1, and adapter encoding fraction 0.9 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 243}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 243}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 243}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.766901; mean error remaining at interval end 1.30214; detection used 15.99% and memory refresh 0.70% of objective evaluations; 141 responses with mean radius 0.5 (mean multiplier 1), allocated fraction 1, and adapter encoding fraction 0.9 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 141}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 141}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 141}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.505391; mean error remaining at interval end 0.873582; detection used 15.79% and memory refresh 0.47% of objective evaluations; 95 responses with mean radius 0.5 (mean multiplier 1), allocated fraction 1, and adapter encoding fraction 0.9 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 95}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 95}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 95}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 4.071680; mean error remaining at interval end 3.61259; detection used 15.86% and memory refresh 0.40% of objective evaluations; 81 responses with mean radius 0.5 (mean multiplier 1), allocated fraction 1, and adapter encoding fraction 0.9 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 81}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 81}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 81}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.705611; mean error remaining at interval end 1.17296; detection used 15.79% and memory refresh 0.53% of objective evaluations; 106 responses with mean radius 0.5 (mean multiplier 1), allocated fraction 1, and adapter encoding fraction 0.9 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 106}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 106}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 106}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.013076; mean error remaining at interval end 0.880132; detection used 15.98% and memory refresh 1.65% of objective evaluations; 329 responses with mean radius 1.5 (mean multiplier 1), allocated fraction 1, and adapter encoding fraction 0.9 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 329}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 329}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 329}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 3.936800; mean error remaining at interval end 0.755056; detection used 15.94% and memory refresh 1.71% of objective evaluations; 343 responses with mean radius 1.5 (mean multiplier 1), allocated fraction 1, and adapter encoding fraction 0.9 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 343}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 343}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 343}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 7.215672; mean error remaining at interval end 3.92126; detection used 15.87% and memory refresh 1.57% of objective evaluations; 313 responses with mean radius 1.5 (mean multiplier 1), allocated fraction 1, and adapter encoding fraction 0.9 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 313}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 313}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 313}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.468519; mean error remaining at interval end 2.82698; detection used 15.95% and memory refresh 1.73% of objective evaluations; 345 responses with mean radius 1.5 (mean multiplier 1), allocated fraction 1, and adapter encoding fraction 0.9 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 345}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 345}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 345}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 5.005355; mean error remaining at interval end 3.94712; detection used 15.85% and memory refresh 0.46% of objective evaluations; 92 responses with mean radius 1.5 (mean multiplier 1), allocated fraction 1, and adapter encoding fraction 0.9 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 92}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 92}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 92}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.112567; mean error remaining at interval end 0.154196; detection used 16.10% and memory refresh 0.86% of objective evaluations; 172 responses with mean radius 1.5 (mean multiplier 1), allocated fraction 1, and adapter encoding fraction 0.9 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 172}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 172}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 172}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.100673; mean error remaining at interval end 1.61059; detection used 15.30% and memory refresh 0.28% of objective evaluations; 56 responses with mean radius 1.5 (mean multiplier 1), allocated fraction 1, and adapter encoding fraction 0.9 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 56}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 56}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 56}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 12.922211; mean error remaining at interval end 10.4619; detection used 15.72% and memory refresh 0.51% of objective evaluations; 102 responses with mean radius 1.5 (mean multiplier 1), allocated fraction 1, and adapter encoding fraction 0.9 (encoding only); requested counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 102}, allocated counts {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 102}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 102}. Largest tracking error: case_015. Examine joint integer allocation and radius multiplier using public observed state, with all memories reevaluated and retained velocities fixed. Allocated fraction is allocated_count/swarm_size; the adapter encoding fraction only encodes an integer for the ceiling rule. Allocated counts are selected indices, not a claim of completed movement; horizon-truncated responses separately retain counts with objective queries. Constant count/radius pairs are permitted and receive no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


# Task

Rewrite the program to improve its performance on the specified metrics.
Provide the complete new program code.

IMPORTANT: Make sure your rewritten program maintains the same inputs and outputs as the original program, but with improved internal implementation.
