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
    count = 2 if larger_radius and 8.0 * recovery_credit >= loss else 3
    return min(swarm_size, count)
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.24
mean_offline_error: 3.22; worst_case_offline_error: 5.38; case_error_std: 1.12; cases_completed: 16

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.592099; mean error remaining at interval end 2.59071; detection used 15.86% and memory refresh 1.27% of objective evaluations; 254 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.336280; mean error remaining at interval end 1.41162; detection used 15.91% and memory refresh 1.44% of objective evaluations; 287 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 287, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 287, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 287, "4": 0, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.472551; mean error remaining at interval end 2.46068; detection used 15.84% and memory refresh 1.27% of objective evaluations; 254 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 4.787996; mean error remaining at interval end 3.83536; detection used 15.82% and memory refresh 1.16% of objective evaluations; 232 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 232, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 232, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 232, "4": 0, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.580532; mean error remaining at interval end 2.68589; detection used 15.96% and memory refresh 0.61% of objective evaluations; 123 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 123, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 123, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 123, "4": 0, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.461606; mean error remaining at interval end 1.71538; detection used 15.86% and memory refresh 0.53% of objective evaluations; 107 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 107, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 107, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 107, "4": 0, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.169184; mean error remaining at interval end 2.21217; detection used 15.98% and memory refresh 0.66% of objective evaluations; 133 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 133, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 133, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 133, "4": 0, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.572745; mean error remaining at interval end 0.899178; detection used 15.63% and memory refresh 0.39% of objective evaluations; 77 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 77, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 77, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 77, "4": 0, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.497070; mean error remaining at interval end 1.9149; detection used 15.93% and memory refresh 1.64% of objective evaluations; 328 responses with mean radius 3 and relocated fraction 0.47378; requested counts {"0": 0, "1": 0, "2": 43, "3": 285, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 43, "3": 285, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 43, "3": 285, "4": 0, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.377856; mean error remaining at interval end 3.50218; detection used 15.75% and memory refresh 1.00% of objective evaluations; 200 responses with mean radius 3 and relocated fraction 0.465; requested counts {"0": 0, "1": 0, "2": 35, "3": 165, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 35, "3": 165, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 35, "3": 165, "4": 0, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.617720; mean error remaining at interval end 1.98478; detection used 15.76% and memory refresh 1.24% of objective evaluations; 249 responses with mean radius 3 and relocated fraction 0.474297; requested counts {"0": 0, "1": 0, "2": 32, "3": 217, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 32, "3": 217, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 32, "3": 217, "4": 0, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 3.143376; mean error remaining at interval end 0.614082; detection used 15.96% and memory refresh 1.52% of objective evaluations; 305 responses with mean radius 3 and relocated fraction 0.471148; requested counts {"0": 0, "1": 0, "2": 44, "3": 261, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 44, "3": 261, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 44, "3": 261, "4": 0, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.371395; mean error remaining at interval end 0.374466; detection used 16.00% and memory refresh 0.73% of objective evaluations; 145 responses with mean radius 3 and relocated fraction 0.477931; requested counts {"0": 0, "1": 0, "2": 16, "3": 129, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 16, "3": 129, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 16, "3": 129, "4": 0, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.273734; mean error remaining at interval end 0.469886; detection used 16.13% and memory refresh 0.74% of objective evaluations; 149 responses with mean radius 3 and relocated fraction 0.473154; requested counts {"0": 0, "1": 0, "2": 20, "3": 129, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 20, "3": 129, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 20, "3": 129, "4": 0, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.084866; mean error remaining at interval end 0.456272; detection used 15.95% and memory refresh 0.66% of objective evaluations; 133 responses with mean radius 3 and relocated fraction 0.471429; requested counts {"0": 0, "1": 0, "2": 19, "3": 114, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 19, "3": 114, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 19, "3": 114, "4": 0, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.242704; mean error remaining at interval end 0.896552; detection used 15.93% and memory refresh 0.60% of objective evaluations; 120 responses with mean radius 3 and relocated fraction 0.468333; requested counts {"0": 0, "1": 0, "2": 19, "3": 101, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 19, "3": 101, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 19, "3": 101, "4": 0, "5": 0}. Largest tracking error: case_009. Examine integer allocation using public observed state, with radius scale 2, all memories reevaluated and retained velocities fixed. Executed counts mean the actual simulator particle allocation; horizon-truncated responses separately retain counts with objective queries. Constant allocation is permitted and receives no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


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
    # Restrict reduced allocation to the larger-radius regime.
    larger_radius = float(observation["default_radius"]) > 1.0
    count = 2 if larger_radius and 4.0 * recovery_credit >= loss else 3
    return min(swarm_size, count)
# EVOLVE-BLOCK-END

```

Here are the performance metrics of the program:

Combined score to maximize: 0.24
mean_offline_error: 3.23; worst_case_offline_error: 5.24; case_error_std: 1.12; cases_completed: 16

Here is additional text feedback about the current program:

Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.592099; mean error remaining at interval end 2.59071; detection used 15.86% and memory refresh 1.27% of objective evaluations; 254 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.336280; mean error remaining at interval end 1.41162; detection used 15.91% and memory refresh 1.44% of objective evaluations; 287 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 287, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 287, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 287, "4": 0, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.472551; mean error remaining at interval end 2.46068; detection used 15.84% and memory refresh 1.27% of objective evaluations; 254 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 4.787996; mean error remaining at interval end 3.83536; detection used 15.82% and memory refresh 1.16% of objective evaluations; 232 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 232, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 232, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 232, "4": 0, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.580532; mean error remaining at interval end 2.68589; detection used 15.96% and memory refresh 0.61% of objective evaluations; 123 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 123, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 123, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 123, "4": 0, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.461606; mean error remaining at interval end 1.71538; detection used 15.86% and memory refresh 0.53% of objective evaluations; 107 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 107, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 107, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 107, "4": 0, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.169184; mean error remaining at interval end 2.21217; detection used 15.98% and memory refresh 0.66% of objective evaluations; 133 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 133, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 133, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 133, "4": 0, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.572745; mean error remaining at interval end 0.899178; detection used 15.63% and memory refresh 0.39% of objective evaluations; 77 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 77, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 77, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 77, "4": 0, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.773058; mean error remaining at interval end 2.08761; detection used 15.93% and memory refresh 1.68% of objective evaluations; 336 responses with mean radius 3 and relocated fraction 0.475595; requested counts {"0": 0, "1": 0, "2": 41, "3": 295, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 41, "3": 295, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 41, "3": 295, "4": 0, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.244633; mean error remaining at interval end 3.38938; detection used 15.71% and memory refresh 0.97% of objective evaluations; 193 responses with mean radius 3 and relocated fraction 0.468912; requested counts {"0": 0, "1": 0, "2": 30, "3": 163, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 30, "3": 163, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 30, "3": 163, "4": 0, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.565091; mean error remaining at interval end 2.04694; detection used 15.77% and memory refresh 1.31% of objective evaluations; 262 responses with mean radius 3 and relocated fraction 0.477099; requested counts {"0": 0, "1": 0, "2": 30, "3": 232, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 30, "3": 232, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 30, "3": 232, "4": 0, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 3.143376; mean error remaining at interval end 0.614082; detection used 15.96% and memory refresh 1.52% of objective evaluations; 305 responses with mean radius 3 and relocated fraction 0.471148; requested counts {"0": 0, "1": 0, "2": 44, "3": 261, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 44, "3": 261, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 44, "3": 261, "4": 0, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.405854; mean error remaining at interval end 0.352648; detection used 16.01% and memory refresh 0.73% of objective evaluations; 145 responses with mean radius 3 and relocated fraction 0.48069; requested counts {"0": 0, "1": 0, "2": 14, "3": 131, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 14, "3": 131, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 14, "3": 131, "4": 0, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.273734; mean error remaining at interval end 0.469886; detection used 16.13% and memory refresh 0.74% of objective evaluations; 149 responses with mean radius 3 and relocated fraction 0.473154; requested counts {"0": 0, "1": 0, "2": 20, "3": 129, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 20, "3": 129, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 20, "3": 129, "4": 0, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.084866; mean error remaining at interval end 0.456272; detection used 15.95% and memory refresh 0.66% of objective evaluations; 133 responses with mean radius 3 and relocated fraction 0.471429; requested counts {"0": 0, "1": 0, "2": 19, "3": 114, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 19, "3": 114, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 19, "3": 114, "4": 0, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.261787; mean error remaining at interval end 0.899006; detection used 15.91% and memory refresh 0.58% of objective evaluations; 116 responses with mean radius 3 and relocated fraction 0.472414; requested counts {"0": 0, "1": 0, "2": 16, "3": 100, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 16, "3": 100, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 16, "3": 100, "4": 0, "5": 0}. Largest tracking error: case_009. Examine integer allocation using public observed state, with radius scale 2, all memories reevaluated and retained velocities fixed. Executed counts mean the actual simulator particle allocation; horizon-truncated responses separately retain counts with objective queries. Constant allocation is permitted and receives no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


# Instructions

Make sure that the changes you propose are consistent with each other. For example, if you refer to a new config variable somewhere, you should also propose a change to add that variable.

Note that the changes you propose will be applied sequentially, so you should assume that the previous changes have already been applied when writing the SEARCH block.

# Task

Suggest a new idea to improve the performance of the code that is inspired by your expert knowledge of the considered subject.
Your goal is to maximize the `combined_score` of the program.
Describe each change with a SEARCH/REPLACE block.

IMPORTANT: Do not rewrite the entire program - focus on targeted improvements.
