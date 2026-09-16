# System Instructions

Evolve choose_recovery(observation) inside the marked block only. Return exactly
radius_scale (finite nonnegative Python int/float, not bool) and reset_velocity
(Python bool). Four of five particles are selected uniformly for relocation.
The adapter fixes count four and reevaluates all personal-best memories.
Radius is default_radius * radius_scale. Resetting velocity zeros only the
selected particles' velocities when their relocation update occurs.

Public scalar observations: dimension, bounds_width, swarm_size, swarm_count,
swarm_diameter, previous_best_fitness, current_best_fitness, fitness_drop,
relative_fitness_drop, recent_improvement, evaluations_since_response,
previous_response_radius, default_radius, observed_best_displacement,
evals_remaining. The baseline's default_radius is half the configured movement
severity. No true optimum, peak positions, seeds or future histories are inputs.
Use deterministic computation and public observations only. Do not read files,
environment variables or evaluator internals; do not modify budgets or results.

Fitness is 1/(1+mean_offline_error) over eight equally weighted development cases
at 100,000 counted objective queries each. Detection and memory queries count.
The evaluator supplies paired differences from the original corrected baseline
and the Phase A selected fixed-four seed, regime summaries and observed action
occupancy. Occupancy is output behavior, not syntactic branch coverage.
Constants and conditions are both legitimate; complexity and apparent adaptation
receive no bonus. Short search improvements require a separate transfer probe.
The scientific hypothesis is radius/retained-velocity interaction, not a required
positive finding; outcome interaction alone cannot establish overshoot as mediator.


# Scientific context supplied to mutation

# Scientific context: bounded radius/velocity discovery

Blackwell, Branke and Li (2008), printed p.215, propose that retained velocities
can contribute to relocation overshoot and explain a preferred sampling radius.
This is a hypothesis; outcome interaction alone cannot identify overshoot. Our
fixed simulator resets only relocated particles when reset_velocity is true;
subsequent PSO and memory dynamics remain unchanged.

Phase A used the same eight development cases as this search, two for each
severity1/3 by period2500/5000 regime, 5D, ten peaks, 100000 counted queries.
Mean errors: count4/r1/retain 3.041839; count4/r1.5/retain 3.089088;
count4/r1/reset 3.329122; count4/r1.5/reset 3.332410; corrected count5/r1/retain
baseline 3.423599; exact V3 selected policy 3.152140. The seed is the best
fixed count-four policy, r1/retain, chosen on development data. V3 always used
radius1.5 and occasionally count3; it was +0.063052 worse than constant4/1.5
here (paired SD0.391413). This is reused development evidence, not confirmation.

The radius1.5-minus1 effect is +0.047249 retained, +0.003288 reset. The within-case
radius-by-velocity interaction mean is -0.043961, SD0.836208, range[-1.815428,
+0.930971]. Reset-minus-retain mean errors are +0.287283 (r1) and +0.243322 (r1.5).
All eight outcomes are retained; no significance gate controls continuation.
These observations do not support universal resetting or a single coherent
overshoot explanation. Individual cases and regimes differ materially.

The task evolves radius_scale and reset_velocity only; count4 and personal-best
memory reevaluation are fixed. Use the public scalar observations listed in the
task prompt. Constants and conditional functions are legitimate, with no reward
for complexity or a branch. Feedback compares every case with both the original
baseline and fixed seed, groups paired differences by regime and records actual
output-action occupancy. This does not expose hidden peak locations, optimum,
seeds or pilot data. Competing explanations include better constant radius,
conditional responses to observed loss/spread, altered query allocation and
stochastic closed-loop paths. Observational correlations do not identify a
mediator. This is a twelve-descendant probe, not exhaustive search. Any transfer
claim needs the separately frozen exploratory pilot; its outcomes are unavailable.

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


# Current program

Here is the current program we are trying to improve (you will need to propose a modification to it below):

```python
"""Count-four recovery policy; memory reevaluation is fixed by the adapter."""

# EVOLVE-BLOCK-START
def choose_recovery(observation: dict) -> dict:
    return {"radius_scale": 1.0, "reset_velocity": False}
# EVOLVE-BLOCK-END

```

Here are the performance metrics of the program:

Combined score to maximize: 0.25
mean_offline_error: 3.04; worst_case_offline_error: 5.28; case_error_std: 1.27; cases_completed: 8

Here is additional text feedback about the current program:

Development feedback only. Lower offline error is better; fitness=1/(1+mean error). Paired differences below are candidate minus comparator (negative is better). Baseline is baseline; fixed seed is c4_r1_retain. Same environment and optimizer seeds pair complete closed-loop methods; optimizer draws may diverge. Action occupancy is measured output behavior, not syntactic branch coverage.
case_000 severity=1.0,period=2500: error=2.990329, delta baseline=-1.518465, delta fixed seed=+0.000000; reset on 0/275 responses; 1 observed action pairs; most frequent [radius=1,reset=False: 275 (100.0%)]; interval-end error=1.6222516047964048; query shares={"detection": 0.15819, "exclusion": 0.0324, "initialization": 5e-05, "memory": 0.01375, "particle": 0.79561}; horizon-truncated responses=0.
case_001 severity=1.0,period=2500: error=2.480568, delta baseline=-1.059340, delta fixed seed=+0.000000; reset on 0/385 responses; 1 observed action pairs; most frequent [radius=1,reset=False: 385 (100.0%)]; interval-end error=0.5700302603257079; query shares={"detection": 0.15903, "exclusion": 0.0201, "initialization": 5e-05, "memory": 0.01925, "particle": 0.80157}; horizon-truncated responses=0.
case_002 severity=1.0,period=5000: error=1.751215, delta baseline=-0.015686, delta fixed seed=+0.000000; reset on 0/150 responses; 1 observed action pairs; most frequent [radius=1,reset=False: 150 (100.0%)]; interval-end error=1.2144450558170496; query shares={"detection": 0.16046, "exclusion": 0.02405, "initialization": 5e-05, "memory": 0.0075, "particle": 0.80794}; horizon-truncated responses=0.
case_003 severity=1.0,period=5000: error=1.193256, delta baseline=-0.312135, delta fixed seed=+0.000000; reset on 0/103 responses; 1 observed action pairs; most frequent [radius=1,reset=False: 103 (100.0%)]; interval-end error=0.492574572391014; query shares={"detection": 0.15845, "exclusion": 0.04, "initialization": 5e-05, "memory": 0.00515, "particle": 0.79635}; horizon-truncated responses=0.
case_004 severity=3.0,period=2500: error=5.279008, delta baseline=+1.265931, delta fixed seed=+0.000000; reset on 0/353 responses; 1 observed action pairs; most frequent [radius=1,reset=False: 353 (100.0%)]; interval-end error=1.9202539839155157; query shares={"detection": 0.16008, "exclusion": 0.01605, "initialization": 5e-05, "memory": 0.01765, "particle": 0.80617}; horizon-truncated responses=0.
case_005 severity=3.0,period=2500: error=3.755511, delta baseline=-0.181289, delta fixed seed=+0.000000; reset on 0/332 responses; 1 observed action pairs; most frequent [radius=1,reset=False: 332 (100.0%)]; interval-end error=0.6546174542120274; query shares={"detection": 0.15956, "exclusion": 0.02045, "initialization": 5e-05, "memory": 0.0166, "particle": 0.80334}; horizon-truncated responses=0.
case_006 severity=3.0,period=5000: error=3.599042, delta baseline=-1.406313, delta fixed seed=+0.000000; reset on 0/104 responses; 1 observed action pairs; most frequent [radius=1,reset=False: 104 (100.0%)]; interval-end error=1.9058872366691832; query shares={"detection": 0.15934, "exclusion": 0.0329, "initialization": 5e-05, "memory": 0.0052, "particle": 0.80251}; horizon-truncated responses=0.
case_007 severity=3.0,period=5000: error=3.285785, delta baseline=+0.173218, delta fixed seed=+0.000000; reset on 0/183 responses; 1 observed action pairs; most frequent [radius=1,reset=False: 183 (100.0%)]; interval-end error=0.35050154923053717; query shares={"detection": 0.16108, "exclusion": 0.01965, "initialization": 5e-05, "memory": 0.00915, "particle": 0.81007}; horizon-truncated responses=0.
Paired regime summary: {"baseline_difference_sd": 0.3246505991054738, "baseline_mean_difference": -1.288902833879825, "cases": 2, "mean_offline_error": 2.7354487338547324, "regime": "severity=1.0,period=2500", "seed_difference_sd": 0.0, "seed_mean_difference": 0.0}
Paired regime summary: {"baseline_difference_sd": 0.20962134407714816, "baseline_mean_difference": -0.1639103321797667, "cases": 2, "mean_offline_error": 1.4722357295881703, "regime": "severity=1.0,period=5000", "seed_difference_sd": 0.0, "seed_mean_difference": 0.0}
Paired regime summary: {"baseline_difference_sd": 1.0233391408218857, "baseline_mean_difference": 0.5423214371713041, "cases": 2, "mean_offline_error": 4.517259602000246, "regime": "severity=3.0,period=2500", "seed_difference_sd": 0.0, "seed_mean_difference": 0.0}
Paired regime summary: {"baseline_difference_sd": 1.1168968800003427, "baseline_mean_difference": -0.616547772973516, "cases": 2, "mean_offline_error": 3.442413214203609, "regime": "severity=3.0,period=5000", "seed_difference_sd": 0.0, "seed_mean_difference": 0.0}
Four selected particles and memory reevaluation are fixed. Constants and conditions are equally legitimate. Radius/velocity outcome interactions do not prove overshoot; neither velocity-mediated overshoot nor an ideal radius is directly measured. Evaluate competing explanations, including constant tuning, swarm spread, query allocation and stochastic closed-loop effects. No protected pilot outcomes enter this feedback.


# Instructions

Make sure that the changes you propose are consistent with each other. For example, if you refer to a new config variable somewhere, you should also propose a change to add that variable.

Note that the changes you propose will be applied sequentially, so you should assume that the previous changes have already been applied when writing the SEARCH block.

# Task

Suggest a new idea to improve the performance of the code that is inspired by your expert knowledge of the considered subject.
Your goal is to maximize the `combined_score` of the program.
Describe each change with a SEARCH/REPLACE block.

IMPORTANT: Do not rewrite the entire program - focus on targeted improvements.
