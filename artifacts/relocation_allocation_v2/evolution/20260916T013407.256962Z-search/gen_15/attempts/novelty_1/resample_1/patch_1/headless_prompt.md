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
"""V2 allocation seed: relocate three particles after a detected change.

The fixed adapter controls radius, memory, velocity, integer validation and
count-to-fraction conversion. The numerical simulator is outside this program.
"""


# EVOLVE-BLOCK-START
def choose_relocation_count(observation: dict) -> int:
    """Allocate an extra relocation for contracted swarms losing progress."""
    swarm_size = int(observation["swarm_size"])
    if swarm_size <= 0:
        return 0
    radius = max(0.0, 2.0 * float(observation["default_radius"]))
    diameter = max(0.0, float(observation["swarm_diameter"]))
    loss = float(observation["fitness_drop"])
    improvement = max(0.0, float(observation["recent_improvement"]))
    count = 3
    if diameter < radius and loss > improvement:
        count = 4
    return min(count, swarm_size)
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.24
mean_offline_error: 3.21; worst_case_offline_error: 5.43; case_error_std: 1.22; cases_completed: 16

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.145781; mean error remaining at interval end 1.81788; detection used 15.90% and memory refresh 1.42% of objective evaluations; 284 responses with mean radius 1 and relocated fraction 0.63662; requested counts {"0": 0, "1": 0, "2": 0, "3": 90, "4": 194, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 90, "4": 194, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 90, "4": 194, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.370724; mean error remaining at interval end 2.69116; detection used 15.89% and memory refresh 1.21% of objective evaluations; 242 responses with mean radius 1 and relocated fraction 0.630579; requested counts {"0": 0, "1": 0, "2": 0, "3": 84, "4": 158, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 84, "4": 158, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 84, "4": 158, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 4.018436; mean error remaining at interval end 2.96012; detection used 15.90% and memory refresh 1.34% of objective evaluations; 268 responses with mean radius 1 and relocated fraction 0.627612; requested counts {"0": 0, "1": 0, "2": 0, "3": 97, "4": 171, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 97, "4": 171, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 97, "4": 171, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.470060; mean error remaining at interval end 1.31398; detection used 15.87% and memory refresh 1.27% of objective evaluations; 255 responses with mean radius 1 and relocated fraction 0.623137; requested counts {"0": 0, "1": 0, "2": 0, "3": 98, "4": 157, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 98, "4": 157, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 98, "4": 157, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.569972; mean error remaining at interval end 1.6085; detection used 16.05% and memory refresh 0.66% of objective evaluations; 133 responses with mean radius 1 and relocated fraction 0.633835; requested counts {"0": 0, "1": 0, "2": 0, "3": 44, "4": 89, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 44, "4": 89, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 44, "4": 89, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.291532; mean error remaining at interval end 1.30591; detection used 15.92% and memory refresh 0.58% of objective evaluations; 117 responses with mean radius 1 and relocated fraction 0.619658; requested counts {"0": 0, "1": 0, "2": 0, "3": 47, "4": 70, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 47, "4": 70, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 47, "4": 70, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 4.706401; mean error remaining at interval end 3.73317; detection used 16.00% and memory refresh 0.63% of objective evaluations; 126 responses with mean radius 1 and relocated fraction 0.631746; requested counts {"0": 0, "1": 0, "2": 0, "3": 43, "4": 83, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 43, "4": 83, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 43, "4": 83, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.266778; mean error remaining at interval end 0.485315; detection used 15.79% and memory refresh 0.46% of objective evaluations; 93 responses with mean radius 1 and relocated fraction 0.616129; requested counts {"0": 0, "1": 0, "2": 0, "3": 39, "4": 54, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 39, "4": 54, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 39, "4": 54, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.227762; mean error remaining at interval end 1.96319; detection used 15.94% and memory refresh 1.55% of objective evaluations; 310 responses with mean radius 3 and relocated fraction 0.66; requested counts {"0": 0, "1": 0, "2": 0, "3": 62, "4": 248, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 62, "4": 248, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 62, "4": 248, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.426337; mean error remaining at interval end 3.33387; detection used 15.66% and memory refresh 0.94% of objective evaluations; 187 responses with mean radius 3 and relocated fraction 0.648663; requested counts {"0": 0, "1": 0, "2": 0, "3": 48, "4": 139, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 48, "4": 139, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 48, "4": 139, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.193272; mean error remaining at interval end 2.74066; detection used 15.71% and memory refresh 1.05% of objective evaluations; 210 responses with mean radius 3 and relocated fraction 0.649524; requested counts {"0": 0, "1": 0, "2": 0, "3": 53, "4": 157, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 53, "4": 157, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 53, "4": 157, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 3.483830; mean error remaining at interval end 0.68381; detection used 15.91% and memory refresh 1.54% of objective evaluations; 309 responses with mean radius 3 and relocated fraction 0.650809; requested counts {"0": 0, "1": 0, "2": 0, "3": 76, "4": 233, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 76, "4": 233, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 76, "4": 233, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.589981; mean error remaining at interval end 0.814697; detection used 15.94% and memory refresh 0.62% of objective evaluations; 125 responses with mean radius 3 and relocated fraction 0.6632; requested counts {"0": 0, "1": 0, "2": 0, "3": 23, "4": 102, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 23, "4": 102, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 23, "4": 102, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.519768; mean error remaining at interval end 1.2397; detection used 16.10% and memory refresh 0.80% of objective evaluations; 160 responses with mean radius 3 and relocated fraction 0.66; requested counts {"0": 0, "1": 0, "2": 0, "3": 32, "4": 128, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 32, "4": 128, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 32, "4": 128, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.160008; mean error remaining at interval end 0.575499; detection used 15.93% and memory refresh 0.63% of objective evaluations; 126 responses with mean radius 3 and relocated fraction 0.661905; requested counts {"0": 0, "1": 0, "2": 0, "3": 24, "4": 102, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 24, "4": 102, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 24, "4": 102, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 1.878290; mean error remaining at interval end 0.605036; detection used 15.91% and memory refresh 0.58% of objective evaluations; 116 responses with mean radius 3 and relocated fraction 0.655172; requested counts {"0": 0, "1": 0, "2": 0, "3": 26, "4": 90, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 26, "4": 90, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 26, "4": 90, "5": 0}. Largest tracking error: case_009. Examine integer allocation using public observed state, with radius scale 2, all memories reevaluated and retained velocities fixed. Executed counts mean the actual simulator particle allocation; horizon-truncated responses separately retain counts with objective queries. Constant allocation is permitted and receives no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.

```python
"""V2 allocation seed: relocate three particles after a detected change.

The fixed adapter controls radius, memory, velocity, integer validation and
count-to-fraction conversion. The numerical simulator is outside this program.
"""


# EVOLVE-BLOCK-START
def choose_relocation_count(observation: dict) -> int:
    """Use three relocations, or four for tightly contracted, losing swarms."""
    swarm_size = int(observation["swarm_size"])
    if swarm_size <= 0:
        return 0
    half_relocation_radius = max(0.0, float(observation["default_radius"]))
    diameter = max(0.0, float(observation["swarm_diameter"]))
    loss = float(observation["fitness_drop"])
    improvement = max(0.0, float(observation["recent_improvement"]))
    count = 3
    if diameter < half_relocation_radius and loss > improvement:
        count = 4
    return min(count, swarm_size)
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.24
mean_offline_error: 3.19; worst_case_offline_error: 5.77; case_error_std: 1.28; cases_completed: 16

Text feedback:
Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.091040; mean error remaining at interval end 1.80442; detection used 15.90% and memory refresh 1.42% of objective evaluations; 284 responses with mean radius 1 and relocated fraction 0.622535; requested counts {"0": 0, "1": 0, "2": 0, "3": 110, "4": 174, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 110, "4": 174, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 110, "4": 174, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.873940; mean error remaining at interval end 2.17026; detection used 15.90% and memory refresh 1.32% of objective evaluations; 264 responses with mean radius 1 and relocated fraction 0.62197; requested counts {"0": 0, "1": 0, "2": 0, "3": 103, "4": 161, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 103, "4": 161, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 103, "4": 161, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.737810; mean error remaining at interval end 2.70471; detection used 15.89% and memory refresh 1.27% of objective evaluations; 254 responses with mean radius 1 and relocated fraction 0.615748; requested counts {"0": 0, "1": 0, "2": 0, "3": 107, "4": 147, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 107, "4": 147, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 107, "4": 147, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.545827; mean error remaining at interval end 1.28181; detection used 15.87% and memory refresh 1.31% of objective evaluations; 261 responses with mean radius 1 and relocated fraction 0.61341; requested counts {"0": 0, "1": 0, "2": 0, "3": 113, "4": 148, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 113, "4": 148, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 113, "4": 148, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.554740; mean error remaining at interval end 1.60976; detection used 16.05% and memory refresh 0.67% of objective evaluations; 134 responses with mean radius 1 and relocated fraction 0.631343; requested counts {"0": 0, "1": 0, "2": 0, "3": 46, "4": 88, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 46, "4": 88, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 46, "4": 88, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.291532; mean error remaining at interval end 1.30591; detection used 15.92% and memory refresh 0.58% of objective evaluations; 117 responses with mean radius 1 and relocated fraction 0.619658; requested counts {"0": 0, "1": 0, "2": 0, "3": 47, "4": 70, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 47, "4": 70, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 47, "4": 70, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 4.706401; mean error remaining at interval end 3.73317; detection used 16.00% and memory refresh 0.63% of objective evaluations; 126 responses with mean radius 1 and relocated fraction 0.631746; requested counts {"0": 0, "1": 0, "2": 0, "3": 43, "4": 83, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 43, "4": 83, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 43, "4": 83, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.266778; mean error remaining at interval end 0.485315; detection used 15.79% and memory refresh 0.46% of objective evaluations; 93 responses with mean radius 1 and relocated fraction 0.616129; requested counts {"0": 0, "1": 0, "2": 0, "3": 39, "4": 54, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 39, "4": 54, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 39, "4": 54, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.372018; mean error remaining at interval end 1.92862; detection used 15.97% and memory refresh 1.65% of objective evaluations; 329 responses with mean radius 3 and relocated fraction 0.637386; requested counts {"0": 0, "1": 0, "2": 0, "3": 103, "4": 226, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 103, "4": 226, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 103, "4": 226, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.426337; mean error remaining at interval end 3.33387; detection used 15.66% and memory refresh 0.94% of objective evaluations; 187 responses with mean radius 3 and relocated fraction 0.648663; requested counts {"0": 0, "1": 0, "2": 0, "3": 48, "4": 139, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 48, "4": 139, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 48, "4": 139, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.768937; mean error remaining at interval end 3.44168; detection used 15.65% and memory refresh 1.06% of objective evaluations; 213 responses with mean radius 3 and relocated fraction 0.651174; requested counts {"0": 0, "1": 0, "2": 0, "3": 52, "4": 161, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 52, "4": 161, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 52, "4": 161, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 3.328243; mean error remaining at interval end 0.66814; detection used 15.95% and memory refresh 1.62% of objective evaluations; 324 responses with mean radius 3 and relocated fraction 0.632716; requested counts {"0": 0, "1": 0, "2": 0, "3": 109, "4": 215, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 109, "4": 215, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 109, "4": 215, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.589981; mean error remaining at interval end 0.814697; detection used 15.94% and memory refresh 0.62% of objective evaluations; 125 responses with mean radius 3 and relocated fraction 0.6632; requested counts {"0": 0, "1": 0, "2": 0, "3": 23, "4": 102, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 23, "4": 102, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 23, "4": 102, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.519768; mean error remaining at interval end 1.2397; detection used 16.10% and memory refresh 0.80% of objective evaluations; 160 responses with mean radius 3 and relocated fraction 0.66; requested counts {"0": 0, "1": 0, "2": 0, "3": 32, "4": 128, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 32, "4": 128, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 32, "4": 128, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.160008; mean error remaining at interval end 0.575499; detection used 15.93% and memory refresh 0.63% of objective evaluations; 126 responses with mean radius 3 and relocated fraction 0.661905; requested counts {"0": 0, "1": 0, "2": 0, "3": 24, "4": 102, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 24, "4": 102, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 24, "4": 102, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 1.878290; mean error remaining at interval end 0.605036; detection used 15.91% and memory refresh 0.58% of objective evaluations; 116 responses with mean radius 3 and relocated fraction 0.655172; requested counts {"0": 0, "1": 0, "2": 0, "3": 26, "4": 90, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 26, "4": 90, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 26, "4": 90, "5": 0}. Largest tracking error: case_010. Examine integer allocation using public observed state, with radius scale 2, all memories reevaluated and retained velocities fixed. Executed counts mean the actual simulator particle allocation; horizon-truncated responses separately retain counts with objective queries. Constant allocation is permitted and receives no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


# Current program

Here is the current program we are trying to improve (you will need to propose a new program with the same inputs and outputs as the original program, but with improved internal implementation):

```python
"""V2 allocation seed: relocate three particles after a detected change.

The fixed adapter controls radius, memory, velocity, integer validation and
count-to-fraction conversion. The numerical simulator is outside this program.
"""


# EVOLVE-BLOCK-START
def choose_relocation_count(observation: dict) -> int:
    """Combine tight and broad contraction thresholds by public radius scale."""
    swarm_size = int(observation["swarm_size"])
    if swarm_size <= 0:
        return 0
    default_radius = max(0.0, float(observation["default_radius"]))
    diameter = max(0.0, float(observation["swarm_diameter"]))
    loss = float(observation["fitness_drop"])
    improvement = max(0.0, float(observation["recent_improvement"]))
    threshold = default_radius
    if default_radius > 1.0:
        threshold *= 2.0
    count = 3
    if diameter < threshold and loss > improvement:
        count = 4
    return min(count, swarm_size)
# EVOLVE-BLOCK-END

```

Here are the performance metrics of the program:

Combined score to maximize: 0.24
mean_offline_error: 3.16; worst_case_offline_error: 5.43; case_error_std: 1.21; cases_completed: 16

Here is additional text feedback about the current program:

Lower offline error is better; combined_score=1/(1+mean_offline_error) is a strictly monotonic ranking transformation. case_000 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.091040; mean error remaining at interval end 1.80442; detection used 15.90% and memory refresh 1.42% of objective evaluations; 284 responses with mean radius 1 and relocated fraction 0.622535; requested counts {"0": 0, "1": 0, "2": 0, "3": 110, "4": 174, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 110, "4": 174, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 110, "4": 174, "5": 0}. case_001 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.873940; mean error remaining at interval end 2.17026; detection used 15.90% and memory refresh 1.32% of objective evaluations; 264 responses with mean radius 1 and relocated fraction 0.62197; requested counts {"0": 0, "1": 0, "2": 0, "3": 103, "4": 161, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 103, "4": 161, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 103, "4": 161, "5": 0}. case_002 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 3.737810; mean error remaining at interval end 2.70471; detection used 15.89% and memory refresh 1.27% of objective evaluations; 254 responses with mean radius 1 and relocated fraction 0.615748; requested counts {"0": 0, "1": 0, "2": 0, "3": 107, "4": 147, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 107, "4": 147, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 107, "4": 147, "5": 0}. case_003 (5D, 10 peaks, move severity 1.0, interval 2500 evaluations): offline error 2.545827; mean error remaining at interval end 1.28181; detection used 15.87% and memory refresh 1.31% of objective evaluations; 261 responses with mean radius 1 and relocated fraction 0.61341; requested counts {"0": 0, "1": 0, "2": 0, "3": 113, "4": 148, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 113, "4": 148, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 113, "4": 148, "5": 0}. case_004 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.554740; mean error remaining at interval end 1.60976; detection used 16.05% and memory refresh 0.67% of objective evaluations; 134 responses with mean radius 1 and relocated fraction 0.631343; requested counts {"0": 0, "1": 0, "2": 0, "3": 46, "4": 88, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 46, "4": 88, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 46, "4": 88, "5": 0}. case_005 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 2.291532; mean error remaining at interval end 1.30591; detection used 15.92% and memory refresh 0.58% of objective evaluations; 117 responses with mean radius 1 and relocated fraction 0.619658; requested counts {"0": 0, "1": 0, "2": 0, "3": 47, "4": 70, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 47, "4": 70, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 47, "4": 70, "5": 0}. case_006 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 4.706401; mean error remaining at interval end 3.73317; detection used 16.00% and memory refresh 0.63% of objective evaluations; 126 responses with mean radius 1 and relocated fraction 0.631746; requested counts {"0": 0, "1": 0, "2": 0, "3": 43, "4": 83, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 43, "4": 83, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 43, "4": 83, "5": 0}. case_007 (5D, 10 peaks, move severity 1.0, interval 5000 evaluations): offline error 1.266778; mean error remaining at interval end 0.485315; detection used 15.79% and memory refresh 0.46% of objective evaluations; 93 responses with mean radius 1 and relocated fraction 0.616129; requested counts {"0": 0, "1": 0, "2": 0, "3": 39, "4": 54, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 39, "4": 54, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 39, "4": 54, "5": 0}. case_008 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 4.227762; mean error remaining at interval end 1.96319; detection used 15.94% and memory refresh 1.55% of objective evaluations; 310 responses with mean radius 3 and relocated fraction 0.66; requested counts {"0": 0, "1": 0, "2": 0, "3": 62, "4": 248, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 62, "4": 248, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 62, "4": 248, "5": 0}. case_009 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.426337; mean error remaining at interval end 3.33387; detection used 15.66% and memory refresh 0.94% of objective evaluations; 187 responses with mean radius 3 and relocated fraction 0.648663; requested counts {"0": 0, "1": 0, "2": 0, "3": 48, "4": 139, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 48, "4": 139, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 48, "4": 139, "5": 0}. case_010 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 5.193272; mean error remaining at interval end 2.74066; detection used 15.71% and memory refresh 1.05% of objective evaluations; 210 responses with mean radius 3 and relocated fraction 0.649524; requested counts {"0": 0, "1": 0, "2": 0, "3": 53, "4": 157, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 53, "4": 157, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 53, "4": 157, "5": 0}. case_011 (5D, 10 peaks, move severity 3.0, interval 2500 evaluations): offline error 3.483830; mean error remaining at interval end 0.68381; detection used 15.91% and memory refresh 1.54% of objective evaluations; 309 responses with mean radius 3 and relocated fraction 0.650809; requested counts {"0": 0, "1": 0, "2": 0, "3": 76, "4": 233, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 76, "4": 233, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 76, "4": 233, "5": 0}. case_012 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.589981; mean error remaining at interval end 0.814697; detection used 15.94% and memory refresh 0.62% of objective evaluations; 125 responses with mean radius 3 and relocated fraction 0.6632; requested counts {"0": 0, "1": 0, "2": 0, "3": 23, "4": 102, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 23, "4": 102, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 23, "4": 102, "5": 0}. case_013 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.519768; mean error remaining at interval end 1.2397; detection used 16.10% and memory refresh 0.80% of objective evaluations; 160 responses with mean radius 3 and relocated fraction 0.66; requested counts {"0": 0, "1": 0, "2": 0, "3": 32, "4": 128, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 32, "4": 128, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 32, "4": 128, "5": 0}. case_014 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 2.160008; mean error remaining at interval end 0.575499; detection used 15.93% and memory refresh 0.63% of objective evaluations; 126 responses with mean radius 3 and relocated fraction 0.661905; requested counts {"0": 0, "1": 0, "2": 0, "3": 24, "4": 102, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 24, "4": 102, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 24, "4": 102, "5": 0}. case_015 (5D, 10 peaks, move severity 3.0, interval 5000 evaluations): offline error 1.878290; mean error remaining at interval end 0.605036; detection used 15.91% and memory refresh 0.58% of objective evaluations; 116 responses with mean radius 3 and relocated fraction 0.655172; requested counts {"0": 0, "1": 0, "2": 0, "3": 26, "4": 90, "5": 0}, executed counts {"0": 0, "1": 0, "2": 0, "3": 26, "4": 90, "5": 0}; 0 horizon-truncated responses; counts with objective queries {"0": 0, "1": 0, "2": 0, "3": 26, "4": 90, "5": 0}. Largest tracking error: case_009. Examine integer allocation using public observed state, with radius scale 2, all memories reevaluated and retained velocities fixed. Executed counts mean the actual simulator particle allocation; horizon-truncated responses separately retain counts with objective queries. Constant allocation is permitted and receives no penalty for simplicity. Large interval-end errors indicate tracking still missed by the next change, while detection and memory shares expose objective-evaluation overhead. These diagnostics describe behavior and do not by themselves prove its cause. Improvements must preserve the fixed simulator and objective-evaluation budget. These are search results; generalization requires separate comparison cases.


# Task

Rewrite the program to improve its performance on the specified metrics.
Provide the complete new program code.

IMPORTANT: Make sure your rewritten program maintains the same inputs and outputs as the original program, but with improved internal implementation.
