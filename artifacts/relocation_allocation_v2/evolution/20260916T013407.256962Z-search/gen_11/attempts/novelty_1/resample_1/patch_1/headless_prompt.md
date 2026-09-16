# System Instructions

Evolve choose_relocation_count(observation) in the marked evolve block only.
Return a Python int in [0, observation['swarm_size']] (five in this study).
The fixed adapter holds radius_scale=2, memory='reevaluate', reset_velocity=False;
it implements exact relocation counts. Non-relocated particles keep ordinary
PSO motion. Use only public observations and deterministic computation. Do not
read files, environment variables, seeds, benchmark internals, global optima or
held-out inputs. Do not modify the evaluator, objective budgets or result files.
Optimize measured mean offline error, ranked by 1/(1+mean_offline_error), over
the equally weighted 16 search cases at 100,000 objective queries each. Count
detection and memory queries. Use measured text_feedback, per-case error,
recovery diagnostics and executed count distributions when forming a proposal.
An adaptive rule is not required to win or vary: no complexity or adaptation
bonus applies. Treat hypotheses as competing explanations, not target results.


# Scientific context supplied to mutation

# Scientific context for relocation allocation v2

This experiment follows the corrected multiswarm reconstruction of Blackwell,
Branke and Li (2008), using DEAP source pinned in this repository. Five neutral
particles form each swarm; exclusion and swarm birth/death maintain exploration.
A counted reevaluation detects changed fitness at the remembered swarm best.
The fixed simulator then asks the candidate how many particles to relocate.

V1's selected adaptive radius/fraction policy improved its search score but
had independent mean error 3.7857 versus corrected baseline 3.7230. A predefined
fixed radius multiplier 2/count-three control had error 3.4496. Those results
motivate allocation as a mechanism question; they do not establish its cause.
V1's selected policy moved four particles in 953 of 1,283 responses, with mean
radius multiplier 2.1856, so radius and allocation both differed. The v1 archive
and its floating-point count behavior remain unchanged.

V2 asks whether, at a fixed relocation radius rule, the useful count depends on
observed swarm state. Competing explanations are useful conditional allocation,
a sufficient global constant, and differences explained by environmental regime
scale alone. A constant winner is informative. There is no bonus for complexity,
branch count, apparent adaptation or agreement with any proposed hypothesis.

Evolve only `choose_relocation_count(observation)` to return an integer from zero
through swarm_size (five). Invalid types and bounds fail; no rounding is allowed.
The fixed adapter converts positive count k to (k - 0.5)/swarm_size and zero to
zero so the unchanged simulator's ceiling rule selects exactly k particles.
Radius_scale=2, memory='reevaluate' and reset_velocity=False remain fixed.
Radius therefore equals configured movement severity; this study does not test
adaptation without access to the baseline severity scale.

Particles not selected for relocation continue ordinary PSO motion and are not
stationary anchors. Personal memories of every particle are reevaluated and
retained. Fitness is deterministic for a landscape, but changing peak heights,
widths and stochastic histories make observed loss an imperfect movement signal.

Public observations are dimension, bounds_width, swarm_size, swarm_count,
swarm_diameter, previous_best_fitness, current_best_fitness, fitness_drop,
relative_fitness_drop, recent_improvement, evaluations_since_response,
previous_response_radius, default_radius, observed_best_displacement and
evals_remaining. Signed change is current_best_fitness-previous_best_fitness;
fitness_drop uses the opposite sign. Use only these observations and ordinary
deterministic computation. Do not inspect files, environment variables, seeds,
evaluator internals, latent peaks, true optima or held-out cases. Candidate Python
execution is not a security sandbox; selected source is inspected for compliance.

The search crosses movement severity 1 and 3 with change periods 2,500 and 5,000,
at fixed 100,000-query horizon, five dimensions and ten conical peaks. Four cases
per regime give sixteen equally weighted cases. Every query counts, including
change detection and memory reevaluation. Native selection maximizes
1/(1+mean_offline_error), a monotonic transform of the primary outcome; lower
offline error is better. Feedback includes actual per-case error, error remaining
before the next change, evaluation shares and executed allocation distributions.
Incomplete final responses retain their flags and separate queried-relocation
counts. Response records and trajectory checkpoints are not independent cases.

One native search has twenty generation slots including the count-three seed.
Afterwards the top three source-distinct valid programs and all six constants
receive separate one-time validation. Program, constant and a regime-conditioned
state-independent count-sampling control are frozen before generating fresh final
cases. Final outcomes never feed mutation or selection. The primary contrast is
evolved minus validation-selected constant error; the mechanism contrast removes
association between selected count and current state while approximately retaining
the regime's validation count distribution. That control also changes temporal
dependence, so it is not a perfect single-variable causal intervention. Results
apply to fresh histories within these four regimes, not unseen conditions or a
claim of reliable search discovery across independent evolutionary runs.

You MUST respond using an edit name, description, and the exact SEARCH/REPLACE diff format shown below to indicate changes:

<NAME>
A shortened name summarizing the edit you are proposing. Lowercase, no spaces, underscores allowed.
</NAME>

<DESCRIPTION>
A description and argumentation process of the edit you are proposing.
</DESCRIPTION>

<DIFF>
<<<<<<< SEARCH
# Original code to find and replace (must match exactly including indentation)
=======
# New replacement code
>>>>>>> REPLACE

</DIFF>


Example of a valid diff format:
<DIFF>
<<<<<<< SEARCH
for i in range(m):
    for j in range(p):
        for k in range(n):
            C[i, j] += A[i, k] * B[k, j]
=======
# Reorder loops for better memory access pattern
for i in range(m):
    for k in range(n):
        for j in range(p):
            C[i, j] += A[i, k] * B[k, j]
>>>>>>> REPLACE

</DIFF>

* You may only modify text that lies below a line containing "EVOLVE-BLOCK-START" and above the next "EVOLVE-BLOCK-END". Everything outside those markers is read-only.
* Do not repeat the markers "EVOLVE-BLOCK-START" and "EVOLVE-BLOCK-END" in the SEARCH/REPLACE blocks.  
* Every block’s SEARCH section must be copied **verbatim** from the current file, including indentation.
* You can propose multiple independent edits. SEARCH/REPLACE blocks follow one after another. DO NOT ADD ANY OTHER TEXT BETWEEN THESE BLOCKS.
* Make sure the file still runs after your changes.

# Previous Messages

[]

# User Request

Here are the performance metrics of a set of previously implemented programs:

# Prior programs

```python
"""V2 allocation seed: relocate three particles after a detected change.

The fixed adapter controls radius, memory, velocity, integer validation and
count-to-fraction conversion. The numerical simulator is outside this program.
"""


# EVOLVE-BLOCK-START
def choose_relocation_count(observation: dict) -> int:
    """Use three relocations unless broad coverage supports a smaller response."""
    swarm_size = int(observation["swarm_size"])
    if swarm_size <= 0:
        return 0
    radius = max(2.0 * float(observation["default_radius"]), 1e-12)
    diameter = max(0.0, float(observation["swarm_diameter"]))
    deteriorated = (
        float(observation["fitness_drop"]) > 0.0
        and float(observation["relative_fitness_drop"]) > 0.05
    )
    if diameter >= 2.0 * radius and not deteriorated:
        return min(swarm_size, 2)
    return min(swarm_size, 3)
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.22
mean_offline_error: 3.47; worst_case_offline_error: 5.42; case_error_std: 1.25; cases_completed: 16

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.924529; mean error remaining at interval end 2.65366; detection used 15.84% and memory refresh 1.24% of objective evaluations; 249 responses with mean radius 1 and relocated fraction 0.485542; requested counts {"0": 0, "1": 0, "2": 18, "3": 231, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 18, "3": 231, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 18, "3": 231, "4": 0, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.659558; mean error remaining at interval end 1.87906; detection used 15.85% and memory refresh 1.24% of objective evaluations; 248 responses with mean radius 1 and relocated fraction 0.482258; requested counts {"0": 0, "1": 0, "2": 22, "3": 226, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 22, "3": 226, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 22, "3": 226, "4": 0, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 4.376102; mean error remaining at interval end 3.02446; detection used 15.84% and memory refresh 1.28% of objective evaluations; 256 responses with mean radius 1 and relocated fraction 0.485938; requested counts {"0": 0, "1": 0, "2": 18, "3": 238, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 18, "3": 238, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 18, "3": 238, "4": 0, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 4.817656; mean error remaining at interval end 3.96324; detection used 15.78% and memory refresh 1.17% of objective evaluations; 234 responses with mean radius 1 and relocated fraction 0.482906; requested counts {"0": 0, "1": 0, "2": 20, "3": 214, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 20, "3": 214, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 20, "3": 214, "4": 0, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.665270; mean error remaining at interval end 2.80215; detection used 15.96% and memory refresh 0.58% of objective evaluations; 116 responses with mean radius 1 and relocated fraction 0.486207; requested counts {"0": 0, "1": 0, "2": 8, "3": 108, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 8, "3": 108, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 8, "3": 108, "4": 0, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.933019; mean error remaining at interval end 1.48312; detection used 15.95% and memory refresh 0.55% of objective evaluations; 109 responses with mean radius 1 and relocated fraction 0.481651; requested counts {"0": 0, "1": 0, "2": 10, "3": 99, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 10, "3": 99, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 10, "3": 99, "4": 0, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.065721; mean error remaining at interval end 2.10655; detection used 16.03% and memory refresh 0.68% of objective evaluations; 135 responses with mean radius 1 and relocated fraction 0.485185; requested counts {"0": 0, "1": 0, "2": 10, "3": 125, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 10, "3": 125, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 10, "3": 125, "4": 0, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.587905; mean error remaining at interval end 0.889196; detection used 15.79% and memory refresh 0.45% of objective evaluations; 89 responses with mean radius 1 and relocated fraction 0.482022; requested counts {"0": 0, "1": 0, "2": 8, "3": 81, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 8, "3": 81, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 8, "3": 81, "4": 0, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.638208; mean error remaining at interval end 2.31735; detection used 15.93% and memory refresh 1.52% of objective evaluations; 304 responses with mean radius 3 and relocated fraction 0.490789; requested counts {"0": 0, "1": 0, "2": 14, "3": 290, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 14, "3": 290, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 14, "3": 290, "4": 0, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.415319; mean error remaining at interval end 3.38308; detection used 15.67% and memory refresh 0.92% of objective evaluations; 185 responses with mean radius 3 and relocated fraction 0.485946; requested counts {"0": 0, "1": 0, "2": 13, "3": 172, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 13, "3": 172, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 13, "3": 172, "4": 0, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.372480; mean error remaining at interval end 2.60974; detection used 15.74% and memory refresh 1.23% of objective evaluations; 246 responses with mean radius 3 and relocated fraction 0.48374; requested counts {"0": 0, "1": 0, "2": 20, "3": 226, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 20, "3": 226, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 20, "3": 226, "4": 0, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 3.466790; mean error remaining at interval end 0.851761; detection used 15.93% and memory refresh 1.45% of objective evaluations; 290 responses with mean radius 3 and relocated fraction 0.490345; requested counts {"0": 0, "1": 0, "2": 14, "3": 276, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 14, "3": 276, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 14, "3": 276, "4": 0, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.661595; mean error remaining at interval end 0.686046; detection used 15.97% and memory refresh 0.66% of objective evaluations; 133 responses with mean radius 3 and relocated fraction 0.490977; requested counts {"0": 0, "1": 0, "2": 6, "3": 127, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 6, "3": 127, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 6, "3": 127, "4": 0, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.895907; mean error remaining at interval end 2.48957; detection used 16.10% and memory refresh 0.78% of objective evaluations; 155 responses with mean radius 3 and relocated fraction 0.488387; requested counts {"0": 0, "1": 0, "2": 9, "3": 146, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 9, "3": 146, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 9, "3": 146, "4": 0, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 1.875022; mean error remaining at interval end 0.455911; detection used 15.93% and memory refresh 0.68% of objective evaluations; 135 responses with mean radius 3 and relocated fraction 0.485185; requested counts {"0": 0, "1": 0, "2": 10, "3": 125, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 10, "3": 125, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 10, "3": 125, "4": 0, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.225445; mean error remaining at interval end 0.984792; detection used 15.92% and memory refresh 0.58% of objective evaluations; 117 responses with mean radius 3 and relocated fraction 0.489744; requested counts {"0": 0, "1": 0, "2": 6, "3": 111, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 6, "3": 111, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 6, "3": 111, "4": 0, "5": 0}. Largest tracking error: case_009. Examine integer allocation using public observed state, with radius scale 2, all memories reevaluated and retained velocities fixed. Executed counts mean the actual simulator particle allocation; horizon-truncated responses separately retain counts with objective queries. Constant allocation is permitted and receives no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.

```python
"""V2 allocation seed: relocate three particles after a detected change.

The fixed adapter controls radius, memory, velocity, integer validation and
count-to-fraction conversion. The numerical simulator is outside this program.
"""


# EVOLVE-BLOCK-START
def choose_relocation_count(observation: dict) -> int:
    """Preserve more ordinary PSO motion when progress covers fitness loss."""
    swarm_size = int(observation["swarm_size"])
    if swarm_size <= 0:
        return 0
    loss = max(0.0, float(observation["fitness_drop"]))
    recovery_credit = max(0.0, float(observation["recent_improvement"]))
    # Positive historical progress is evidence, not a guaranteed recovery rate.
    # Avoid interpreting fitness deterioration as a spatial displacement.
    # Restrict reduced allocation to the larger-radius regime.
    larger_radius = float(observation["default_radius"]) > 1.0
    count = 2 if larger_radius and recovery_credit >= loss else 3
    return min(swarm_size, count)
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.23
mean_offline_error: 3.26; worst_case_offline_error: 5.35; case_error_std: 1.09; cases_completed: 16

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.592099; mean error remaining at interval end 2.59071; detection used 15.86% and memory refresh 1.27% of objective evaluations; 254 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.336280; mean error remaining at interval end 1.41162; detection used 15.91% and memory refresh 1.44% of objective evaluations; 287 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 287, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 287, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 287, "4": 0, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.472551; mean error remaining at interval end 2.46068; detection used 15.84% and memory refresh 1.27% of objective evaluations; 254 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 4.787996; mean error remaining at interval end 3.83536; detection used 15.82% and memory refresh 1.16% of objective evaluations; 232 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 232, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 232, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 232, "4": 0, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.580532; mean error remaining at interval end 2.68589; detection used 15.96% and memory refresh 0.61% of objective evaluations; 123 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 123, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 123, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 123, "4": 0, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.461606; mean error remaining at interval end 1.71538; detection used 15.86% and memory refresh 0.53% of objective evaluations; 107 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 107, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 107, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 107, "4": 0, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.169184; mean error remaining at interval end 2.21217; detection used 15.98% and memory refresh 0.66% of objective evaluations; 133 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 133, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 133, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 133, "4": 0, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.572745; mean error remaining at interval end 0.899178; detection used 15.63% and memory refresh 0.39% of objective evaluations; 77 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 77, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 77, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 77, "4": 0, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.588378; mean error remaining at interval end 2.18914; detection used 15.93% and memory refresh 1.49% of objective evaluations; 297 responses with mean radius 3 and relocated fraction 0.481145; requested counts {"0": 0, "1": 0, "2": 28, "3": 269, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 28, "3": 269, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 28, "3": 269, "4": 0, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.345074; mean error remaining at interval end 3.40082; detection used 15.75% and memory refresh 0.97% of objective evaluations; 194 responses with mean radius 3 and relocated fraction 0.472165; requested counts {"0": 0, "1": 0, "2": 27, "3": 167, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 27, "3": 167, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 27, "3": 167, "4": 0, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.386450; mean error remaining at interval end 2.00686; detection used 15.74% and memory refresh 1.21% of objective evaluations; 242 responses with mean radius 3 and relocated fraction 0.476033; requested counts {"0": 0, "1": 0, "2": 29, "3": 213, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 29, "3": 213, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 29, "3": 213, "4": 0, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 3.319570; mean error remaining at interval end 0.65267; detection used 15.96% and memory refresh 1.49% of objective evaluations; 297 responses with mean radius 3 and relocated fraction 0.479125; requested counts {"0": 0, "1": 0, "2": 31, "3": 266, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 31, "3": 266, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 31, "3": 266, "4": 0, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.423822; mean error remaining at interval end 0.385806; detection used 16.01% and memory refresh 0.77% of objective evaluations; 154 responses with mean radius 3 and relocated fraction 0.485714; requested counts {"0": 0, "1": 0, "2": 11, "3": 143, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 11, "3": 143, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 11, "3": 143, "4": 0, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.042095; mean error remaining at interval end 1.08332; detection used 16.13% and memory refresh 0.81% of objective evaluations; 163 responses with mean radius 3 and relocated fraction 0.47546; requested counts {"0": 0, "1": 0, "2": 20, "3": 143, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 20, "3": 143, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 20, "3": 143, "4": 0, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.025161; mean error remaining at interval end 0.476177; detection used 15.96% and memory refresh 0.66% of objective evaluations; 132 responses with mean radius 3 and relocated fraction 0.472727; requested counts {"0": 0, "1": 0, "2": 18, "3": 114, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 18, "3": 114, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 18, "3": 114, "4": 0, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.121757; mean error remaining at interval end 0.886675; detection used 15.91% and memory refresh 0.59% of objective evaluations; 118 responses with mean radius 3 and relocated fraction 0.474576; requested counts {"0": 0, "1": 0, "2": 15, "3": 103, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 15, "3": 103, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 15, "3": 103, "4": 0, "5": 0}. Largest tracking error: case_009. Examine integer allocation using public observed state, with radius scale 2, all memories reevaluated and retained velocities fixed. Executed counts mean the actual simulator particle allocation; horizon-truncated responses separately retain counts with objective queries. Constant allocation is permitted and receives no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


# Current program

Here is the current program we are trying to improve (you will need to propose a modification to it below):

```python
"""V2 allocation seed: relocate three particles after a detected change.

The fixed adapter controls radius, memory, velocity, integer validation and
count-to-fraction conversion. The numerical simulator is outside this program.
"""


# EVOLVE-BLOCK-START
def choose_relocation_count(observation: dict) -> int:
    """Preserve more ordinary PSO motion when progress covers fitness loss."""
    swarm_size = int(observation["swarm_size"])
    if swarm_size <= 0:
        return 0
    loss = max(0.0, float(observation["fitness_drop"]))
    recovery_credit = max(0.0, float(observation["recent_improvement"]))
    # Positive historical progress is evidence, not a guaranteed recovery rate.
    # Avoid interpreting fitness deterioration as a spatial displacement.
    count = 2 if recovery_credit >= loss else 3
    return min(swarm_size, count)
# EVOLVE-BLOCK-END

```

Here are the performance metrics of the program:

Combined score to maximize: 0.23
mean_offline_error: 3.36; worst_case_offline_error: 5.35; case_error_std: 1.13; cases_completed: 16

Here is additional text feedback about the current program:

Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.405954; mean error remaining at interval end 2.27968; detection used 15.89% and memory refresh 1.30% of objective evaluations; 260 responses with mean radius 1 and relocated fraction 0.458462; requested counts {"0": 0, "1": 0, "2": 54, "3": 206, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 54, "3": 206, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 54, "3": 206, "4": 0, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.430857; mean error remaining at interval end 2.71481; detection used 15.91% and memory refresh 1.30% of objective evaluations; 260 responses with mean radius 1 and relocated fraction 0.443846; requested counts {"0": 0, "1": 0, "2": 73, "3": 187, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 73, "3": 187, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 73, "3": 187, "4": 0, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 4.092139; mean error remaining at interval end 2.85571; detection used 15.82% and memory refresh 1.26% of objective evaluations; 252 responses with mean radius 1 and relocated fraction 0.446825; requested counts {"0": 0, "1": 0, "2": 67, "3": 185, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 67, "3": 185, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 67, "3": 185, "4": 0, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.574618; mean error remaining at interval end 1.35746; detection used 15.79% and memory refresh 1.26% of objective evaluations; 251 responses with mean radius 1 and relocated fraction 0.443426; requested counts {"0": 0, "1": 0, "2": 71, "3": 180, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 71, "3": 180, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 71, "3": 180, "4": 0, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.757944; mean error remaining at interval end 2.87667; detection used 15.98% and memory refresh 0.59% of objective evaluations; 118 responses with mean radius 1 and relocated fraction 0.452542; requested counts {"0": 0, "1": 0, "2": 28, "3": 90, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 28, "3": 90, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 28, "3": 90, "4": 0, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.977915; mean error remaining at interval end 1.35682; detection used 15.93% and memory refresh 0.56% of objective evaluations; 113 responses with mean radius 1 and relocated fraction 0.432743; requested counts {"0": 0, "1": 0, "2": 38, "3": 75, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 38, "3": 75, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 38, "3": 75, "4": 0, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 5.223529; mean error remaining at interval end 4.31346; detection used 15.95% and memory refresh 0.58% of objective evaluations; 117 responses with mean radius 1 and relocated fraction 0.445299; requested counts {"0": 0, "1": 0, "2": 32, "3": 85, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 32, "3": 85, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 32, "3": 85, "4": 0, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.039631; mean error remaining at interval end 0.921549; detection used 15.80% and memory refresh 0.47% of objective evaluations; 95 responses with mean radius 1 and relocated fraction 0.453684; requested counts {"0": 0, "1": 0, "2": 22, "3": 73, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 22, "3": 73, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 22, "3": 73, "4": 0, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.588378; mean error remaining at interval end 2.18914; detection used 15.93% and memory refresh 1.49% of objective evaluations; 297 responses with mean radius 3 and relocated fraction 0.481145; requested counts {"0": 0, "1": 0, "2": 28, "3": 269, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 28, "3": 269, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 28, "3": 269, "4": 0, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.345074; mean error remaining at interval end 3.40082; detection used 15.75% and memory refresh 0.97% of objective evaluations; 194 responses with mean radius 3 and relocated fraction 0.472165; requested counts {"0": 0, "1": 0, "2": 27, "3": 167, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 27, "3": 167, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 27, "3": 167, "4": 0, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.386450; mean error remaining at interval end 2.00686; detection used 15.74% and memory refresh 1.21% of objective evaluations; 242 responses with mean radius 3 and relocated fraction 0.476033; requested counts {"0": 0, "1": 0, "2": 29, "3": 213, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 29, "3": 213, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 29, "3": 213, "4": 0, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 3.319570; mean error remaining at interval end 0.65267; detection used 15.96% and memory refresh 1.49% of objective evaluations; 297 responses with mean radius 3 and relocated fraction 0.479125; requested counts {"0": 0, "1": 0, "2": 31, "3": 266, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 31, "3": 266, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 31, "3": 266, "4": 0, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.423822; mean error remaining at interval end 0.385806; detection used 16.01% and memory refresh 0.77% of objective evaluations; 154 responses with mean radius 3 and relocated fraction 0.485714; requested counts {"0": 0, "1": 0, "2": 11, "3": 143, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 11, "3": 143, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 11, "3": 143, "4": 0, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.042095; mean error remaining at interval end 1.08332; detection used 16.13% and memory refresh 0.81% of objective evaluations; 163 responses with mean radius 3 and relocated fraction 0.47546; requested counts {"0": 0, "1": 0, "2": 20, "3": 143, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 20, "3": 143, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 20, "3": 143, "4": 0, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.025161; mean error remaining at interval end 0.476177; detection used 15.96% and memory refresh 0.66% of objective evaluations; 132 responses with mean radius 3 and relocated fraction 0.472727; requested counts {"0": 0, "1": 0, "2": 18, "3": 114, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 18, "3": 114, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 18, "3": 114, "4": 0, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.121757; mean error remaining at interval end 0.886675; detection used 15.91% and memory refresh 0.59% of objective evaluations; 118 responses with mean radius 3 and relocated fraction 0.474576; requested counts {"0": 0, "1": 0, "2": 15, "3": 103, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 15, "3": 103, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 15, "3": 103, "4": 0, "5": 0}. Largest tracking error: case_009. Examine integer allocation using public observed state, with radius scale 2, all memories reevaluated and retained velocities fixed. Executed counts mean the actual simulator particle allocation; horizon-truncated responses separately retain counts with objective queries. Constant allocation is permitted and receives no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


# Instructions

Make sure that the changes you propose are consistent with each other. For example, if you refer to a new config variable somewhere, you should also propose a change to add that variable.

Note that the changes you propose will be applied sequentially, so you should assume that the previous changes have already been applied when writing the SEARCH block.

# Task

Suggest a new idea to improve the performance of the code that is inspired by your expert knowledge of the considered subject.
Your goal is to maximize the `combined_score` of the program.
Describe each change with a SEARCH/REPLACE block.

IMPORTANT: Do not rewrite the entire program - focus on targeted improvements.
