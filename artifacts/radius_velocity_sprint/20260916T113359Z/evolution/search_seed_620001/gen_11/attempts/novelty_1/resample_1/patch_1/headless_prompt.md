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
"""Count-four recovery policy; memory reevaluation is fixed by the adapter."""

# EVOLVE-BLOCK-START
def choose_recovery(observation: dict) -> dict:
    return {"radius_scale": 1.0, "reset_velocity": False}
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.25
mean_offline_error: 3.04; worst_case_offline_error: 5.28; case_error_std: 1.27; cases_completed: 8

Text feedback:
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

```python
"""Count-four recovery policy; memory reevaluation is fixed by the adapter."""

# EVOLVE-BLOCK-START
def choose_recovery(observation: dict) -> dict:
    return {"radius_scale": 1.25, "reset_velocity": False}
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.26
mean_offline_error: 2.89; worst_case_offline_error: 4.27; case_error_std: 1.15; cases_completed: 8

Text feedback:
Development feedback only. Lower offline error is better; fitness=1/(1+mean error). Paired differences below are candidate minus comparator (negative is better). Baseline is baseline; fixed seed is c4_r1_retain. Same environment and optimizer seeds pair complete closed-loop methods; optimizer draws may diverge. Action occupancy is measured output behavior, not syntactic branch coverage.
case_000 severity=1.0,period=2500: error=2.838723, delta baseline=-1.670072, delta fixed seed=-0.151607; reset on 0/263 responses; 1 observed action pairs; most frequent [radius=1.25,reset=False: 263 (100.0%)]; interval-end error=1.5432015353215995; query shares={"detection": 0.15812, "exclusion": 0.0328, "initialization": 5e-05, "memory": 0.01315, "particle": 0.79588}; horizon-truncated responses=0.
case_001 severity=1.0,period=2500: error=2.251629, delta baseline=-1.288279, delta fixed seed=-0.228939; reset on 0/383 responses; 1 observed action pairs; most frequent [radius=1.25,reset=False: 383 (100.0%)]; interval-end error=0.4804019417855853; query shares={"detection": 0.1588, "exclusion": 0.0218, "initialization": 5e-05, "memory": 0.01915, "particle": 0.8002}; horizon-truncated responses=0.
case_002 severity=1.0,period=5000: error=1.638465, delta baseline=-0.128436, delta fixed seed=-0.112750; reset on 0/149 responses; 1 observed action pairs; most frequent [radius=1.25,reset=False: 149 (100.0%)]; interval-end error=1.208256013679394; query shares={"detection": 0.16045, "exclusion": 0.02405, "initialization": 5e-05, "memory": 0.00745, "particle": 0.808}; horizon-truncated responses=0.
case_003 severity=1.0,period=5000: error=1.164450, delta baseline=-0.340941, delta fixed seed=-0.028806; reset on 0/103 responses; 1 observed action pairs; most frequent [radius=1.25,reset=False: 103 (100.0%)]; interval-end error=0.48949180927197594; query shares={"detection": 0.15845, "exclusion": 0.04, "initialization": 5e-05, "memory": 0.00515, "particle": 0.79635}; horizon-truncated responses=0.
case_004 severity=3.0,period=2500: error=4.266670, delta baseline=+0.253594, delta fixed seed=-1.012338; reset on 0/336 responses; 1 observed action pairs; most frequent [radius=1.25,reset=False: 336 (100.0%)]; interval-end error=0.962045962435788; query shares={"detection": 0.15979, "exclusion": 0.0201, "initialization": 5e-05, "memory": 0.0168, "particle": 0.80326}; horizon-truncated responses=0.
case_005 severity=3.0,period=2500: error=4.259213, delta baseline=+0.322413, delta fixed seed=+0.503702; reset on 0/337 responses; 1 observed action pairs; most frequent [radius=1.25,reset=False: 337 (100.0%)]; interval-end error=1.0395703522167277; query shares={"detection": 0.15989, "exclusion": 0.01995, "initialization": 5e-05, "memory": 0.01685, "particle": 0.80326}; horizon-truncated responses=0.
case_006 severity=3.0,period=5000: error=3.507451, delta baseline=-1.497904, delta fixed seed=-0.091590; reset on 0/104 responses; 1 observed action pairs; most frequent [radius=1.25,reset=False: 104 (100.0%)]; interval-end error=1.9041941636765845; query shares={"detection": 0.15925, "exclusion": 0.0338, "initialization": 5e-05, "memory": 0.0052, "particle": 0.8017}; horizon-truncated responses=0.
case_007 severity=3.0,period=5000: error=3.167489, delta baseline=+0.054922, delta fixed seed=-0.118296; reset on 0/160 responses; 1 observed action pairs; most frequent [radius=1.25,reset=False: 160 (100.0%)]; interval-end error=0.4077700636691432; query shares={"detection": 0.16057, "exclusion": 0.0228, "initialization": 5e-05, "memory": 0.008, "particle": 0.80858}; horizon-truncated responses=0.
Paired regime summary: {"baseline_difference_sd": 0.269968452010547, "baseline_mean_difference": -1.4791758344524717, "cases": 2, "mean_offline_error": 2.5451757332820857, "regime": "severity=1.0,period=2500", "seed_difference_sd": 0.054682147094926824, "seed_mean_difference": -0.19027300057264673}
Paired regime summary: {"baseline_difference_sd": 0.15026385534147405, "baseline_mean_difference": -0.23468842549234803, "cases": 2, "mean_offline_error": 1.4014576362755888, "regime": "severity=1.0,period=5000", "seed_difference_sd": 0.059357488735674126, "seed_mean_difference": -0.07077809331258134}
Paired regime summary: {"baseline_difference_sd": 0.04866259287758665, "baseline_mean_difference": 0.2880035329503221, "cases": 2, "mean_offline_error": 4.262941697779264, "regime": "severity=3.0,period=2500", "seed_difference_sd": 1.0720017336994723, "seed_mean_difference": -0.254317904220982}
Paired regime summary: {"baseline_difference_sd": 1.0980133870665005, "baseline_mean_difference": -0.7214908560289097, "cases": 2, "mean_offline_error": 3.3374701311482147, "regime": "severity=3.0,period=5000", "seed_difference_sd": 0.018883492933842158, "seed_mean_difference": -0.10494308305539368}
Four selected particles and memory reevaluation are fixed. Constants and conditions are equally legitimate. Radius/velocity outcome interactions do not prove overshoot; neither velocity-mediated overshoot nor an ideal radius is directly measured. Evaluate competing explanations, including constant tuning, swarm spread, query allocation and stochastic closed-loop effects. No protected pilot outcomes enter this feedback.


# Current program

Here is the current program we are trying to improve (you will need to propose a new program with the same inputs and outputs as the original program, but with improved internal implementation):

```python
"""Count-four recovery policy; memory reevaluation is fixed by the adapter."""

# EVOLVE-BLOCK-START
def choose_recovery(observation: dict) -> dict:
    return {"radius_scale": 1.2, "reset_velocity": False}
# EVOLVE-BLOCK-END

```

Here are the performance metrics of the program:

Combined score to maximize: 0.25
mean_offline_error: 2.94; worst_case_offline_error: 4.41; case_error_std: 1.17; cases_completed: 8

Here is additional text feedback about the current program:

Development feedback only. Lower offline error is better; fitness=1/(1+mean error). Paired differences below are candidate minus comparator (negative is better). Baseline is baseline; fixed seed is c4_r1_retain. Same environment and optimizer seeds pair complete closed-loop methods; optimizer draws may diverge. Action occupancy is measured output behavior, not syntactic branch coverage.
case_000 severity=1.0,period=2500: error=3.192556, delta baseline=-1.316239, delta fixed seed=+0.202227; reset on 0/256 responses; 1 observed action pairs; most frequent [radius=1.2,reset=False: 256 (100.0%)]; interval-end error=1.637738921035444; query shares={"detection": 0.15797, "exclusion": 0.03425, "initialization": 5e-05, "memory": 0.0128, "particle": 0.79493}; horizon-truncated responses=0.
case_001 severity=1.0,period=2500: error=2.365529, delta baseline=-1.174379, delta fixed seed=-0.115039; reset on 0/386 responses; 1 observed action pairs; most frequent [radius=1.2,reset=False: 386 (100.0%)]; interval-end error=0.4337930149999515; query shares={"detection": 0.15895, "exclusion": 0.0208, "initialization": 5e-05, "memory": 0.0193, "particle": 0.8009}; horizon-truncated responses=0.
case_002 severity=1.0,period=5000: error=1.635350, delta baseline=-0.131551, delta fixed seed=-0.115865; reset on 0/142 responses; 1 observed action pairs; most frequent [radius=1.2,reset=False: 142 (100.0%)]; interval-end error=1.0909906721284375; query shares={"detection": 0.16031, "exclusion": 0.0262, "initialization": 5e-05, "memory": 0.0071, "particle": 0.80634}; horizon-truncated responses=0.
case_003 severity=1.0,period=5000: error=1.181317, delta baseline=-0.324074, delta fixed seed=-0.011939; reset on 0/103 responses; 1 observed action pairs; most frequent [radius=1.2,reset=False: 103 (100.0%)]; interval-end error=0.4892635402909349; query shares={"detection": 0.15845, "exclusion": 0.04, "initialization": 5e-05, "memory": 0.00515, "particle": 0.79635}; horizon-truncated responses=0.
case_004 severity=3.0,period=2500: error=4.401092, delta baseline=+0.388015, delta fixed seed=-0.877916; reset on 0/332 responses; 1 observed action pairs; most frequent [radius=1.2,reset=False: 332 (100.0%)]; interval-end error=1.0150616087465696; query shares={"detection": 0.15987, "exclusion": 0.0201, "initialization": 5e-05, "memory": 0.0166, "particle": 0.80338}; horizon-truncated responses=0.
case_005 severity=3.0,period=2500: error=4.409325, delta baseline=+0.472525, delta fixed seed=+0.653814; reset on 0/294 responses; 1 observed action pairs; most frequent [radius=1.2,reset=False: 294 (100.0%)]; interval-end error=1.5328573179471499; query shares={"detection": 0.15951, "exclusion": 0.02465, "initialization": 5e-05, "memory": 0.0147, "particle": 0.80109}; horizon-truncated responses=0.
case_006 severity=3.0,period=5000: error=3.109042, delta baseline=-1.896313, delta fixed seed=-0.490000; reset on 0/111 responses; 1 observed action pairs; most frequent [radius=1.2,reset=False: 111 (100.0%)]; interval-end error=1.704200327398415; query shares={"detection": 0.15947, "exclusion": 0.03333, "initialization": 5e-05, "memory": 0.00555, "particle": 0.8016}; horizon-truncated responses=0.
case_007 severity=3.0,period=5000: error=3.195540, delta baseline=+0.082972, delta fixed seed=-0.090245; reset on 0/166 responses; 1 observed action pairs; most frequent [radius=1.2,reset=False: 166 (100.0%)]; interval-end error=0.41113777624034037; query shares={"detection": 0.16079, "exclusion": 0.0219, "initialization": 5e-05, "memory": 0.0083, "particle": 0.80896}; horizon-truncated responses=0.
Paired regime summary: {"baseline_difference_sd": 0.10030964452484378, "baseline_mean_difference": -1.2453089974844775, "cases": 2, "mean_offline_error": 2.7790425702500796, "regime": "severity=1.0,period=2500", "seed_difference_sd": 0.22434095458063003, "seed_mean_difference": 0.04359383639534742}
Paired regime summary: {"baseline_difference_sd": 0.13613416048985863, "baseline_mean_difference": -0.22781239039414247, "cases": 2, "mean_offline_error": 1.4083336713737946, "regime": "severity=1.0,period=5000", "seed_difference_sd": 0.07348718358728955, "seed_mean_difference": -0.06390205821437578}
Paired regime summary: {"baseline_difference_sd": 0.05975733805051209, "baseline_mean_difference": 0.43027027470846657, "cases": 2, "mean_offline_error": 4.405208439537409, "regime": "severity=3.0,period=2500", "seed_difference_sd": 1.0830964788723978, "seed_mean_difference": -0.11205116246283753}
Paired regime summary: {"baseline_difference_sd": 1.3995662550529107, "baseline_mean_difference": -0.9066704217680175, "cases": 2, "mean_offline_error": 3.152290565409107, "regime": "severity=3.0,period=5000", "seed_difference_sd": 0.28266937505256784, "seed_mean_difference": -0.29012264879450145}
Four selected particles and memory reevaluation are fixed. Constants and conditions are equally legitimate. Radius/velocity outcome interactions do not prove overshoot; neither velocity-mediated overshoot nor an ideal radius is directly measured. Evaluate competing explanations, including constant tuning, swarm spread, query allocation and stochastic closed-loop effects. No protected pilot outcomes enter this feedback.


# Task

Perform a cross-over between the code script above and the one below. Aim to combine the best parts of both code implementations that improves the score.
Provide the complete new program code.

IMPORTANT: Make sure your rewritten program maintains the same inputs and outputs as the original program, but with improved internal implementation.

# Crossover Inspiration Programs
```python
"""Count-four recovery policy; memory reevaluation is fixed by the adapter."""

# EVOLVE-BLOCK-START
def choose_recovery(observation: dict) -> dict:
    return {"radius_scale": 1.25, "reset_velocity": False}
# EVOLVE-BLOCK-END

```

Performance metrics: Combined score to maximize: 0.26
mean_offline_error: 2.89; worst_case_offline_error: 4.27; case_error_std: 1.15; cases_completed: 8


