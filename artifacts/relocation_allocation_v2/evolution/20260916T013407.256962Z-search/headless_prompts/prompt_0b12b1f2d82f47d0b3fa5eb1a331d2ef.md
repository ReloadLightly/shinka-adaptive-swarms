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

Here are the performance metrics of a set of previously implemented programs:

# Prior programs

```python
"""V2 allocation seed: relocate three particles after a detected change.

The fixed adapter controls radius, memory, velocity, integer validation and
count-to-fraction conversion. The numerical simulator is outside this program.
"""


# EVOLVE-BLOCK-START
def choose_relocation_count(observation: dict) -> int:
    """Allocate relocation using public spread and fitness-change observations."""
    swarm_size = int(observation["swarm_size"])
    if swarm_size <= 0:
        return 0
    # Express current spatial coverage relative to the fixed relocation radius.
    radius = max(2.0 * float(observation["default_radius"]), 1e-12)
    coverage = max(0.0, float(observation["swarm_diameter"])) / radius
    # Fitness deterioration is an imperfect signal, not a movement estimate.
    relative_drop = float(observation["relative_fitness_drop"])
    deteriorated = (
        float(observation["fitness_drop"]) > 0.0
        and relative_drop > 0.05
    )
    # Ordered decision table: expand compact swarms that deteriorated;
    # spend fewer relocations when the swarm already has broad coverage.
    allocation_rules = (
        (coverage < 1.0 and deteriorated, 4),
        (coverage >= 2.0, 2),
        (True, 3),
    )
    for applies, count in allocation_rules:
        if applies:
            return min(swarm_size, count)
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.21
mean_offline_error: 3.81; worst_case_offline_error: 5.64; case_error_std: 1.27; cases_completed: 16

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 5.333531; mean error remaining at interval end 4.1749; detection used 15.85% and memory refresh 1.16% of objective evaluations; 232 responses with mean radius 1 and relocated fraction 0.587931; requested counts {"0": 0, "1": 0, "2": 41, "3": 48, "4": 143, "5": 0}, executed counts {"0": 0, "1": 0, "2": 41, "3": 48, "4": 143, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 41, "3": 48, "4": 143, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.763654; mean error remaining at interval end 1.83633; detection used 15.93% and memory refresh 1.36% of objective evaluations; 272 responses with mean radius 1 and relocated fraction 0.563235; requested counts {"0": 0, "1": 0, "2": 49, "3": 88, "4": 135, "5": 0}, executed counts {"0": 0, "1": 0, "2": 49, "3": 88, "4": 135, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 49, "3": 88, "4": 135, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 4.194240; mean error remaining at interval end 2.96359; detection used 15.88% and memory refresh 1.29% of objective evaluations; 259 responses with mean radius 1 and relocated fraction 0.571042; requested counts {"0": 0, "1": 0, "2": 43, "3": 81, "4": 135, "5": 0}, executed counts {"0": 0, "1": 0, "2": 43, "3": 81, "4": 135, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 43, "3": 81, "4": 135, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 4.007657; mean error remaining at interval end 2.98609; detection used 15.84% and memory refresh 1.29% of objective evaluations; 257 responses with mean radius 1 and relocated fraction 0.563813; requested counts {"0": 0, "1": 0, "2": 43, "3": 89, "4": 125, "5": 0}, executed counts {"0": 0, "1": 0, "2": 43, "3": 89, "4": 125, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 43, "3": 89, "4": 125, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.541515; mean error remaining at interval end 2.85339; detection used 15.98% and memory refresh 0.58% of objective evaluations; 117 responses with mean radius 1 and relocated fraction 0.571795; requested counts {"0": 0, "1": 0, "2": 20, "3": 35, "4": 62, "5": 0}, executed counts {"0": 0, "1": 0, "2": 20, "3": 35, "4": 62, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 20, "3": 35, "4": 62, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 4.327131; mean error remaining at interval end 2.85999; detection used 15.94% and memory refresh 0.57% of objective evaluations; 114 responses with mean radius 1 and relocated fraction 0.550877; requested counts {"0": 0, "1": 0, "2": 22, "3": 41, "4": 51, "5": 0}, executed counts {"0": 0, "1": 0, "2": 22, "3": 41, "4": 51, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 22, "3": 41, "4": 51, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 5.170356; mean error remaining at interval end 4.4027; detection used 15.90% and memory refresh 0.57% of objective evaluations; 114 responses with mean radius 1 and relocated fraction 0.582456; requested counts {"0": 0, "1": 0, "2": 18, "3": 31, "4": 65, "5": 0}, executed counts {"0": 0, "1": 0, "2": 18, "3": 31, "4": 65, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 18, "3": 31, "4": 65, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.696405; mean error remaining at interval end 0.895345; detection used 15.66% and memory refresh 0.43% of objective evaluations; 85 responses with mean radius 1 and relocated fraction 0.523529; requested counts {"0": 0, "1": 0, "2": 26, "3": 23, "4": 36, "5": 0}, executed counts {"0": 0, "1": 0, "2": 26, "3": 23, "4": 36, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 26, "3": 23, "4": 36, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.425587; mean error remaining at interval end 2.04293; detection used 15.96% and memory refresh 1.70% of objective evaluations; 340 responses with mean radius 3 and relocated fraction 0.628235; requested counts {"0": 0, "1": 0, "2": 44, "3": 34, "4": 262, "5": 0}, executed counts {"0": 0, "1": 0, "2": 44, "3": 34, "4": 262, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 44, "3": 34, "4": 262, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.636562; mean error remaining at interval end 3.36697; detection used 15.70% and memory refresh 0.95% of objective evaluations; 191 responses with mean radius 3 and relocated fraction 0.602618; requested counts {"0": 0, "1": 0, "2": 39, "3": 15, "4": 137, "5": 0}, executed counts {"0": 0, "1": 0, "2": 39, "3": 15, "4": 137, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 39, "3": 15, "4": 137, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.532026; mean error remaining at interval end 3.15931; detection used 15.75% and memory refresh 1.20% of objective evaluations; 240 responses with mean radius 3 and relocated fraction 0.605833; requested counts {"0": 0, "1": 0, "2": 47, "3": 19, "4": 174, "5": 0}, executed counts {"0": 0, "1": 0, "2": 47, "3": 19, "4": 174, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 47, "3": 19, "4": 174, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 3.127351; mean error remaining at interval end 0.539973; detection used 15.95% and memory refresh 1.50% of objective evaluations; 301 responses with mean radius 3 and relocated fraction 0.612292; requested counts {"0": 0, "1": 0, "2": 48, "3": 36, "4": 217, "5": 0}, executed counts {"0": 0, "1": 0, "2": 48, "3": 36, "4": 217, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 48, "3": 36, "4": 217, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.936696; mean error remaining at interval end 1.15215; detection used 15.98% and memory refresh 0.69% of objective evaluations; 139 responses with mean radius 3 and relocated fraction 0.628058; requested counts {"0": 0, "1": 0, "2": 22, "3": 6, "4": 111, "5": 0}, executed counts {"0": 0, "1": 0, "2": 22, "3": 6, "4": 111, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 22, "3": 6, "4": 111, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 4.098320; mean error remaining at interval end 2.14074; detection used 16.01% and memory refresh 0.66% of objective evaluations; 133 responses with mean radius 3 and relocated fraction 0.599248; requested counts {"0": 0, "1": 0, "2": 21, "3": 25, "4": 87, "5": 0}, executed counts {"0": 0, "1": 0, "2": 21, "3": 25, "4": 87, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 21, "3": 25, "4": 87, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.357225; mean error remaining at interval end 0.782506; detection used 15.93% and memory refresh 0.65% of objective evaluations; 129 responses with mean radius 3 and relocated fraction 0.627132; requested counts {"0": 0, "1": 0, "2": 20, "3": 7, "4": 102, "5": 0}, executed counts {"0": 0, "1": 0, "2": 20, "3": 7, "4": 102, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 20, "3": 7, "4": 102, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 1.816652; mean error remaining at interval end 0.605037; detection used 15.93% and memory refresh 0.59% of objective evaluations; 118 responses with mean radius 3 and relocated fraction 0.615254; requested counts {"0": 0, "1": 0, "2": 19, "3": 12, "4": 87, "5": 0}, executed counts {"0": 0, "1": 0, "2": 19, "3": 12, "4": 87, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 19, "3": 12, "4": 87, "5": 0}. Largest tracking error: case_009. Examine integer allocation using public observed state, with radius scale 2, all memories reevaluated and retained velocities fixed. Executed counts mean the actual simulator particle allocation; horizon-truncated responses separately retain counts with objective queries. Constant allocation is permitted and receives no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.

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

Performance metrics:
Combined score to maximize: 0.23
mean_offline_error: 3.36; worst_case_offline_error: 5.56; case_error_std: 1.21; cases_completed: 16

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.592099; mean error remaining at interval end 2.59071; detection used 15.86% and memory refresh 1.27% of objective evaluations; 254 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.336280; mean error remaining at interval end 1.41162; detection used 15.91% and memory refresh 1.44% of objective evaluations; 287 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 287, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 287, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 287, "4": 0, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.472551; mean error remaining at interval end 2.46068; detection used 15.84% and memory refresh 1.27% of objective evaluations; 254 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 254, "4": 0, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 4.787996; mean error remaining at interval end 3.83536; detection used 15.82% and memory refresh 1.16% of objective evaluations; 232 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 232, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 232, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 232, "4": 0, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.580532; mean error remaining at interval end 2.68589; detection used 15.96% and memory refresh 0.61% of objective evaluations; 123 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 123, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 123, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 123, "4": 0, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.461606; mean error remaining at interval end 1.71538; detection used 15.86% and memory refresh 0.53% of objective evaluations; 107 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 107, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 107, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 107, "4": 0, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.169184; mean error remaining at interval end 2.21217; detection used 15.98% and memory refresh 0.66% of objective evaluations; 133 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 133, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 133, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 133, "4": 0, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.572745; mean error remaining at interval end 0.899178; detection used 15.63% and memory refresh 0.39% of objective evaluations; 77 responses with mean radius 1 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 77, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 77, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 77, "4": 0, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.650203; mean error remaining at interval end 2.3527; detection used 15.91% and memory refresh 1.40% of objective evaluations; 280 responses with mean radius 3 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 280, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 280, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 280, "4": 0, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.266066; mean error remaining at interval end 3.19875; detection used 15.81% and memory refresh 1.10% of objective evaluations; 220 responses with mean radius 3 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 220, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 220, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 220, "4": 0, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.561199; mean error remaining at interval end 2.93968; detection used 15.68% and memory refresh 1.16% of objective evaluations; 232 responses with mean radius 3 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 232, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 232, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 232, "4": 0, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 3.705923; mean error remaining at interval end 1.12288; detection used 15.96% and memory refresh 1.82% of objective evaluations; 364 responses with mean radius 3 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 364, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 364, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 364, "4": 0, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.658859; mean error remaining at interval end 0.668973; detection used 15.99% and memory refresh 0.65% of objective evaluations; 130 responses with mean radius 3 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 130, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 130, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 130, "4": 0, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.067204; mean error remaining at interval end 0.977376; detection used 16.14% and memory refresh 0.82% of objective evaluations; 164 responses with mean radius 3 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 164, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 164, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 164, "4": 0, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.058818; mean error remaining at interval end 0.465645; detection used 15.94% and memory refresh 0.66% of objective evaluations; 132 responses with mean radius 3 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 132, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 132, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 132, "4": 0, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 1.885757; mean error remaining at interval end 0.600616; detection used 15.97% and memory refresh 0.61% of objective evaluations; 122 responses with mean radius 3 and relocated fraction 0.5; requested counts {"0": 0, "1": 0, "2": 0, "3": 122, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 122, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 122, "4": 0, "5": 0}. Largest tracking error: case_010. Examine integer allocation using public observed state, with radius scale 2, all memories reevaluated and retained velocities fixed. Executed counts mean the actual simulator particle allocation; horizon-truncated responses separately retain counts with objective queries. Constant allocation is permitted and receives no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


# Current program

Here is the current program we are trying to improve (you will need to propose a new program with the same inputs and outputs as the original program, but with improved internal implementation):

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

Here are the performance metrics of the program:

Combined score to maximize: 0.22
mean_offline_error: 3.47; worst_case_offline_error: 5.42; case_error_std: 1.25; cases_completed: 16

Here is additional text feedback about the current program:

Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.924529; mean error remaining at interval end 2.65366; detection used 15.84% and memory refresh 1.24% of objective evaluations; 249 responses with mean radius 1 and relocated fraction 0.485542; requested counts {"0": 0, "1": 0, "2": 18, "3": 231, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 18, "3": 231, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 18, "3": 231, "4": 0, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.659558; mean error remaining at interval end 1.87906; detection used 15.85% and memory refresh 1.24% of objective evaluations; 248 responses with mean radius 1 and relocated fraction 0.482258; requested counts {"0": 0, "1": 0, "2": 22, "3": 226, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 22, "3": 226, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 22, "3": 226, "4": 0, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 4.376102; mean error remaining at interval end 3.02446; detection used 15.84% and memory refresh 1.28% of objective evaluations; 256 responses with mean radius 1 and relocated fraction 0.485938; requested counts {"0": 0, "1": 0, "2": 18, "3": 238, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 18, "3": 238, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 18, "3": 238, "4": 0, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 4.817656; mean error remaining at interval end 3.96324; detection used 15.78% and memory refresh 1.17% of objective evaluations; 234 responses with mean radius 1 and relocated fraction 0.482906; requested counts {"0": 0, "1": 0, "2": 20, "3": 214, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 20, "3": 214, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 20, "3": 214, "4": 0, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.665270; mean error remaining at interval end 2.80215; detection used 15.96% and memory refresh 0.58% of objective evaluations; 116 responses with mean radius 1 and relocated fraction 0.486207; requested counts {"0": 0, "1": 0, "2": 8, "3": 108, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 8, "3": 108, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 8, "3": 108, "4": 0, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.933019; mean error remaining at interval end 1.48312; detection used 15.95% and memory refresh 0.55% of objective evaluations; 109 responses with mean radius 1 and relocated fraction 0.481651; requested counts {"0": 0, "1": 0, "2": 10, "3": 99, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 10, "3": 99, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 10, "3": 99, "4": 0, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 3.065721; mean error remaining at interval end 2.10655; detection used 16.03% and memory refresh 0.68% of objective evaluations; 135 responses with mean radius 1 and relocated fraction 0.485185; requested counts {"0": 0, "1": 0, "2": 10, "3": 125, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 10, "3": 125, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 10, "3": 125, "4": 0, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.587905; mean error remaining at interval end 0.889196; detection used 15.79% and memory refresh 0.45% of objective evaluations; 89 responses with mean radius 1 and relocated fraction 0.482022; requested counts {"0": 0, "1": 0, "2": 8, "3": 81, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 8, "3": 81, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 8, "3": 81, "4": 0, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.638208; mean error remaining at interval end 2.31735; detection used 15.93% and memory refresh 1.52% of objective evaluations; 304 responses with mean radius 3 and relocated fraction 0.490789; requested counts {"0": 0, "1": 0, "2": 14, "3": 290, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 14, "3": 290, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 14, "3": 290, "4": 0, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.415319; mean error remaining at interval end 3.38308; detection used 15.67% and memory refresh 0.92% of objective evaluations; 185 responses with mean radius 3 and relocated fraction 0.485946; requested counts {"0": 0, "1": 0, "2": 13, "3": 172, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 13, "3": 172, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 13, "3": 172, "4": 0, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.372480; mean error remaining at interval end 2.60974; detection used 15.74% and memory refresh 1.23% of objective evaluations; 246 responses with mean radius 3 and relocated fraction 0.48374; requested counts {"0": 0, "1": 0, "2": 20, "3": 226, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 20, "3": 226, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 20, "3": 226, "4": 0, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 3.466790; mean error remaining at interval end 0.851761; detection used 15.93% and memory refresh 1.45% of objective evaluations; 290 responses with mean radius 3 and relocated fraction 0.490345; requested counts {"0": 0, "1": 0, "2": 14, "3": 276, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 14, "3": 276, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 14, "3": 276, "4": 0, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.661595; mean error remaining at interval end 0.686046; detection used 15.97% and memory refresh 0.66% of objective evaluations; 133 responses with mean radius 3 and relocated fraction 0.490977; requested counts {"0": 0, "1": 0, "2": 6, "3": 127, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 6, "3": 127, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 6, "3": 127, "4": 0, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 3.895907; mean error remaining at interval end 2.48957; detection used 16.10% and memory refresh 0.78% of objective evaluations; 155 responses with mean radius 3 and relocated fraction 0.488387; requested counts {"0": 0, "1": 0, "2": 9, "3": 146, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 9, "3": 146, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 9, "3": 146, "4": 0, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 1.875022; mean error remaining at interval end 0.455911; detection used 15.93% and memory refresh 0.68% of objective evaluations; 135 responses with mean radius 3 and relocated fraction 0.485185; requested counts {"0": 0, "1": 0, "2": 10, "3": 125, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 10, "3": 125, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 10, "3": 125, "4": 0, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.225445; mean error remaining at interval end 0.984792; detection used 15.92% and memory refresh 0.58% of objective evaluations; 117 responses with mean radius 3 and relocated fraction 0.489744; requested counts {"0": 0, "1": 0, "2": 6, "3": 111, "4": 0, "5": 0}, executed counts {"0": 0, "1": 0, "2": 6, "3": 111, "4": 0, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 6, "3": 111, "4": 0, "5": 0}. Largest tracking error: case_009. Examine integer allocation using public observed state, with radius scale 2, all memories reevaluated and retained velocities fixed. Executed counts mean the actual simulator particle allocation; horizon-truncated responses separately retain counts with objective queries. Constant allocation is permitted and receives no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


# Task

Rewrite the program to improve its performance on the specified metrics.
Provide the complete new program code.

IMPORTANT: Make sure your rewritten program maintains the same inputs and outputs as the original program, but with improved internal implementation.
