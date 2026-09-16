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


# Current program

Here is the current program we are trying to improve (you will need to propose a new program with the same inputs and outputs as the original program, but with improved internal implementation):

```python
"""V2 allocation seed: relocate three particles after a detected change.

The fixed adapter controls radius, memory, velocity, integer validation and
count-to-fraction conversion. The numerical simulator is outside this program.
"""


# EVOLVE-BLOCK-START
def choose_relocation_count(observation: dict) -> int:
    """Return an integer from zero through observation['swarm_size'].

    Public state: dimension, bounds_width, swarm_size, swarm_count,
    swarm_diameter, previous_best_fitness, current_best_fitness, fitness_drop,
    relative_fitness_drop, recent_improvement, evaluations_since_response,
    previous_response_radius, default_radius, observed_best_displacement,
    evals_remaining. Signed fitness change is current_best_fitness minus
    previous_best_fitness (fitness_drop has the opposite sign).

    Non-relocated particles still move by ordinary PSO; all personal memories
    are reevaluated. Radius is fixed at twice default_radius, velocity retained.
    """
    return 3
# EVOLVE-BLOCK-END

```

Here are the performance metrics of the program:

Combined score to maximize: 0.23
mean_offline_error: 3.36; worst_case_offline_error: 5.56; case_error_std: 1.21; cases_completed: 16

Here is additional text feedback about the current program:

Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.592099; mean error remaining at interval end 2.59071; detection used 15.86% and memory refresh 1.27% of objective evaluations; 254 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.336280; mean error remaining at interval end 1.41162; detection used 15.91% and memory refresh 1.44% of objective evaluations; 287 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 287, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 287, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 287, "4": 0, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.472551; mean error remaining at interval end 2.46068; detection used 15.84% and memory refresh 1.27% of objective evaluations; 254 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 4.787996; mean error remaining at interval end 3.83536; detection used 15.82% and memory refresh 1.16% of objective evaluations; 232 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 232, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 232, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 232, "4": 0, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.580532; mean error remaining at interval end 2.68589; detection used 15.96% and memory refresh 0.61% of objective evaluations; 123 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 123, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 123, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 123, "4": 0, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.461606; mean error remaining at interval end 1.71538; detection used 15.86% and memory refresh 0.53% of objective evaluations; 107 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 107, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 107, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 107, "4": 0, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.169184; mean error remaining at interval end 2.21217; detection used 15.98% and memory refresh 0.66% of objective evaluations; 133 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 133, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 133, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 133, "4": 0, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.572745; mean error remaining at interval end 0.899178; detection used 15.63% and memory refresh 0.39% of objective evaluations; 77 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 77, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 77, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 77, "4": 0, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.650203; mean error remaining at interval end 2.3527; detection used 15.91% and memory refresh 1.40% of objective evaluations; 280 responses with mean radius 3 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 280, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 280, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 280, "4": 0, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.266066; mean error remaining at interval end 3.19875; detection used 15.81% and memory refresh 1.10% of objective evaluations; 220 responses with mean radius 3 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 220, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 220, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 220, "4": 0, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.561199; mean error remaining at interval end 2.93968; detection used 15.68% and memory refresh 1.16% of objective evaluations; 232 responses with mean radius 3 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 232, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 232, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 232, "4": 0, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 3.705923; mean error remaining at interval end 1.12288; detection used 15.96% and memory refresh 1.82% of objective evaluations; 364 responses with mean radius 3 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 364, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 364, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 364, "4": 0, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.658859; mean error remaining at interval end 0.668973; detection used 15.99% and memory refresh 0.65% of objective evaluations; 130 responses with mean radius 3 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 130, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 130, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 130, "4": 0, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.067204; mean error remaining at interval end 0.977376; detection used 16.14% and memory refresh 0.82% of objective evaluations; 164 responses with mean radius 3 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 164, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 164, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 164, "4": 0, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.058818; mean error remaining at interval end 0.465645; detection used 15.94% and memory refresh 0.66% of objective evaluations; 132 responses with mean radius 3 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 132, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 132, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 132, "4": 0, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 1.885757; mean error remaining at interval end 0.600616; detection used 15.97% and memory refresh 0.61% of objective evaluations; 122 responses with mean radius 3 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 122, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 122, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 122, "4": 0, "5": 0}. Largest tracking error: case_010. Examine integer allocation using public observed state, with radius scale 2, all memories reevaluated and retained velocities fixed. Executed counts mean the actual simulator particle allocation; horizon-truncated responses separately retain counts with objective queries. Constant allocation is permitted and receives no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


# Task

Rewrite the program to improve its performance on the specified metrics.
Provide the complete new program code.

IMPORTANT: Make sure your rewritten program maintains the same inputs and outputs as the original program, but with improved internal implementation.
