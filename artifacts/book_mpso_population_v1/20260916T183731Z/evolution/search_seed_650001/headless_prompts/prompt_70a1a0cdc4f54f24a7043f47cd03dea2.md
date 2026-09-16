# System Instructions

Evolve only choose_neutral_count(observation) inside the marked block.
Return a Python integer from 2 through 8 (not bool): requested neutral population.
The function runs ONLY when the existing counted shared-best check detects change,
after all existing personal-best memories have been reevaluated and before movement.
The seed returns 5. Every newborn/replacement subswarm starts with FIVE neutral
particles and ONE permanent quantum particle, regardless of policy target.

A fixed adapter moves the current neutral population at most ONE particle toward
this requested target. Shrinking removes the neutral with lowest freshly refreshed
personal-best fitness; ties remove the last surviving neutral in update order.
Permanent quantum particles cannot be removed. Survivor order, positions, velocities
and personal memories are preserved; the shared best is rebuilt from surviving
initialized memories. Growing inserts one new neutral just before the permanent
quantum role. Its velocity uses the existing initialization convention and its
first position is evaluated by the ensuing chapter quantum-response movement.
No fitness is copied and no extra initialization evaluation is added. Requesting
five when five are present changes nothing and consumes no extra movement RNG.

Retain the published schedule: ALL current neutrals receive one quantum movement
on this detected-change update and ordinary PSO on other updates. One permanent
quantum particle always samples. A quantum move samples uniformly by volume around
the asynchronous current shared best and REPLACES ordinary PSO, retaining neutral
velocity for later PSO. Radius stays 0.5*known benchmark movement severity.
All personal memories survive and refresh, including the permanent quantum role.
Convergence uses all current neutrals (excluding the permanent role), retaining
the declared pairwise-diameter approximation. PSO, exclusion after each subswarm
update, swarm birth/removal and objective accounting remain fixed. This changes
population WITHIN subswarms: it does not transfer particles or conserve their
number across subswarms. Larger populations spend more of the shared query budget.

Public immutable observation keys, sampled after refresh and BEFORE resizing:
- neutral_count: current number of ordinary-role particles; swarm_size is this
  count plus the one permanent quantum role; permanent_quantum_count=1.
- swarm_count and total_particle_count: current whole-optimizer counts, before
  this policy call's resize. New/excluded swarms use their actual current sizes.
- previous_requested_target: preceding target requested by this subswarm; 5 at birth.
- change_detected: always True for this hook, from the current counted check;
  has_detected_change is True. No hidden environment signal is exposed.
- updates_since_detected_change: zero on this currently detected update.
- evaluations_since_detected_change: counted queries since this detection,
  including its memory refresh. They do not report the oracle time of change.
- fitness_drop: remembered best fitness before the check minus its counted
  reevaluation; relative_fitness_drop divides it by max(1,abs(previous_best_fitness)).
  Positive means observed deterioration; negative means improvement.
- previous_best_fitness: best remembered quality before the detector check.
- current_best_fitness: shared-best quality rebuilt after the memory refresh.
  Personal-best quality is NOT necessarily current-position fitness.
- recent_improvement: shared-best improvement during this swarm's preceding update.
- neutral_diameter: maximum pairwise distance among current neutral positions.
- mean_neutral_distance_to_best: mean Euclidean current-position distance to the
  refreshed shared best; mean_neutral_speed: mean Euclidean velocity length.
- mean_velocity_alignment_to_best: mean cosine of velocity toward refreshed best,
  zero contribution if either vector has zero length, otherwise in [-1,1].
- previous_conversion_count: neutrals temporarily converted in the preceding update.
- default_radius, dimension, bounds_width: existing known numerical settings.
Geometry is in coordinate units; normalization by max(default_radius,1e-12) is
permitted. Features add no objective queries. Do not access hidden peaks/counts,
optima, benchmark error, future changes, seeds, case identity or evaluator data.
The known-scale radius is supplied by this benchmark, not inferred online.

The function must be deterministic and stateless. Permitted: pure arithmetic,
comparisons, branches, finite for loops/comprehensions, helper functions,
immutable literal module constants; import math or explicit math imports at
MODULE OR FUNCTION scope (aliases supported); public math functions/constants;
mapping.get; builtins abs,all,any,bool,dict,enumerate,float,int,len,list,max,min,
pow,range,reversed,round,sorted,sum,tuple,zip. Function defaults may be immutable
literals. No random numbers, I/O, clocks, environment variables, external imports,
reflection, global/nonlocal mutations, classes, yield or while loops. Only local
temporary state is allowed; observation mutation fails. Return an exact int 2..8.

Fitness=1/(1+mean offline error), using the eight REUSED DEVELOPMENT cases, each
500,000 counted objective queries: five dimensions, ten conical peaks, severity1,
period5000, correlation0,nexcess1. Every evaluation category shares this budget.
References are fixed targets3,5,7 with the SAME start-at-five/one-step adapter;
3 and7 are not historical chapter configurations initialized at those sizes.
Feedback supplies paired errors against all three, the development-best tested
fixed target, population diagnostics and favorable/unfavorable episodes. These
three controls do not exhaust constant rules. Constants are legitimate and no
complexity, conditionality or population-variability bonus is supplied. Fresh
outcomes, if any, remain unavailable to mutation, novelty and meta-memory.


# Scientific context supplied to mutation

# Chapter-grounded population allocation within subswarms

Blackwell, Branke and Li, "Particle Swarms for Dynamic Optimization Problems"
(2008), describe cooperative MPSO: personal/shared memories support convergence
inside subswarms, while exclusion and swarm birth/removal sustain diversity.
Their stated future direction includes adapting particle counts within a swarm.
The central question is whether native Shinka can improve this optimizer under
matched changing landscapes and objective-query budgets.

The preceding chapter-aligned schedule search found no descendant with better
mean development error than the published 5+1 seed (1.744569). Reconstructed5+0
was1.743485, with no clear paired difference across eight cases. Longer, weaker
and fitness-gated temporary conversions were worse in that bounded batch. We
therefore KEEP the published temporary schedule and evolve only a neutral-count
target at detected changes. Earlier relocation and retention findings remain
historical evidence, not numerical results from this new population contract.

A fixed population of five neutrals may allocate effort poorly: additional
ordinary trajectories could help some states, while fewer particles could allow
more frequent subswarm updates under the same counted budget. The permanent
quantum particle continues sampling and all memories are refreshed. Competing
explanations include constant-size tuning, changed budget allocation, altered
convergence/birth/removal timing, best-memory quality, closed-loop random effects
and population-state dependence. A conditional expression alone identifies none
of these mechanisms. This is NOT particle transfer or conservation across groups.

All candidates share the documented new adapter; only the target2..8 changes,
with at most one neutral addition/removal per detected event. Reference target5
reconstructs the existing5+1 execution. References3/7 start at5 too. Target5's
native seed reuses compatible control evaluations. Candidates cannot change the
radius, permanent role, memory handling, quantum response schedule, coefficients,
exclusion, swarm management or objective accounting.

The same eight previously registered development cases retain chapter conditions
5D,tenpeaks,severity1,period5000,500000queries. Reusing these cases does not create
fresh evidence or reproduce the chapter's50-run tables. No superiority over all
constants, all chapter algorithms, independent search or other program-search
methods follows from this one bounded experiment. Explain observed decisions
and uncertainty; neither adaptation nor more particles is presumed beneficial.

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
"""Reconstructed MPSO 5+1: maintain five neutral particles."""

# EVOLVE-BLOCK-START
def choose_neutral_count(observation) -> int:
    return 4
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.33
mean_offline_error: 2.05; worst_case_offline_error: 3.50; case_error_std: 0.81; cases_completed: 8

Text feedback:
Reused development cases only. Lower offline error is better; fitness=1/(1+mean error). Paired differences are candidate minus comparator (negative is better). Target5 is the reconstructed chapter5+1 and native seed. Fixed targets3/7 start at five and resize by at most one per detected event using exactly the same adapter. Best tested fixed target by development mean (numeric target breaks ties): target_5. Only neutral population targets change. Every current neutral quantum-samples on detected change, otherwise uses ordinary PSO; one permanent quantum particle always samples. Whole trajectories, convergence/birth timing and later random draws can diverge.
case_000 severity=1.0,period=5000: error=2.172372, deltatarget_3=+0.241643, deltatarget_5=+0.121642, deltatarget_7=-0.196856; interval-end error=1.5606021568055013; incomplete responses=0.
Measured population behavior: {"additions": 0, "mean_neutral_count_per_subswarm_update": 4.13709843758057, "neutral_count_sum": 320923, "no_change_requests": 676, "policy_calls": 777, "population_decisions": 777, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 66937, "5": 10635, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 11], "recorded_total_particle_count_range": [6, 57], "removals": 101, "requested_target_histogram": {"2": 0, "3": 0, "4": 777, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 77572}
Query shares: {"birth": 0.00342, "detection": 0.155144, "exclusion": 0.036468, "initialization": 1.2e-05, "memory": 0.007972, "ordinary": 0.635626, "permanent_quantum": 0.155142, "temporary_quantum": 0.006216}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 0.5513178259543797, "completed_environment": 20, "difference": -3.980998831313104, "reference_environment_error": 4.532316657267484}, "most_unfavorable": {"candidate_environment_error": 13.655529639530881, "completed_environment": 14, "difference": 13.049389096107603, "reference_environment_error": 0.6061405434232772}}
case_001 severity=1.0,period=5000: error=2.555209, deltatarget_3=+0.533041, deltatarget_5=+0.322563, deltatarget_7=-0.035987; interval-end error=1.824873415051349; incomplete responses=0.
Measured population behavior: {"additions": 0, "mean_neutral_count_per_subswarm_update": 4.12934725648334, "neutral_count_sum": 323076, "no_change_requests": 703, "policy_calls": 801, "population_decisions": 801, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 68119, "5": 10120, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 11], "recorded_total_particle_count_range": [6, 57], "removals": 98, "requested_target_histogram": {"2": 0, "3": 0, "4": 801, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 78239}
Query shares: {"birth": 0.003108, "detection": 0.156478, "exclusion": 0.029568, "initialization": 1.2e-05, "memory": 0.008206, "ordinary": 0.639744, "permanent_quantum": 0.156476, "temporary_quantum": 0.006408}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 1.1199850372321145, "completed_environment": 99, "difference": -5.838462889974322, "reference_environment_error": 6.958447927206436}, "most_unfavorable": {"candidate_environment_error": 11.477154955445677, "completed_environment": 17, "difference": 10.896218094119781, "reference_environment_error": 0.5809368613258956}}
case_002 severity=1.0,period=5000: error=3.497789, deltatarget_3=+1.155660, deltatarget_5=+1.226841, deltatarget_7=+1.576409; interval-end error=2.7211113092147197; incomplete responses=0.
Measured population behavior: {"additions": 0, "mean_neutral_count_per_subswarm_update": 4.156673063617019, "neutral_count_sum": 318397, "no_change_requests": 597, "policy_calls": 696, "population_decisions": 696, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 64598, "5": 12001, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 12], "recorded_total_particle_count_range": [6, 61], "removals": 99, "requested_target_histogram": {"2": 0, "3": 0, "4": 696, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 76599}
Query shares: {"birth": 0.00444, "detection": 0.153198, "exclusion": 0.045204, "initialization": 1.2e-05, "memory": 0.007158, "ordinary": 0.631224, "permanent_quantum": 0.153196, "temporary_quantum": 0.005568}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 0.6605194575236399, "completed_environment": 53, "difference": -6.588277477788845, "reference_environment_error": 7.248796935312485}, "most_unfavorable": {"candidate_environment_error": 15.22096969244736, "completed_environment": 35, "difference": 14.596775755872338, "reference_environment_error": 0.6241939365750224}}
case_003 severity=1.0,period=5000: error=0.732082, deltatarget_3=+0.009194, deltatarget_5=-0.115901, deltatarget_7=+0.040730; interval-end error=0.08126307244321801; incomplete responses=0.
Measured population behavior: {"additions": 0, "mean_neutral_count_per_subswarm_update": 4.112440985070818, "neutral_count_sum": 322292, "no_change_requests": 846, "policy_calls": 937, "population_decisions": 937, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 69558, "5": 8812, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 12], "recorded_total_particle_count_range": [6, 62], "removals": 91, "requested_target_histogram": {"2": 0, "3": 0, "4": 937, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 78370}
Query shares: {"birth": 0.002832, "detection": 0.15674, "exclusion": 0.029544, "initialization": 1.2e-05, "memory": 0.009552, "ordinary": 0.637086, "permanent_quantum": 0.156738, "temporary_quantum": 0.007496}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 1.4160479829251846, "completed_environment": 37, "difference": -4.685470064291652, "reference_environment_error": 6.101518047216836}, "most_unfavorable": {"candidate_environment_error": 3.57783002104059, "completed_environment": 56, "difference": 2.6298491019922814, "reference_environment_error": 0.9479809190483082}}
case_004 severity=1.0,period=5000: error=1.994134, deltatarget_3=+0.037299, deltatarget_5=+0.090200, deltatarget_7=-0.102674; interval-end error=1.2379559246417051; incomplete responses=0.
Measured population behavior: {"additions": 0, "mean_neutral_count_per_subswarm_update": 4.149052369400807, "neutral_count_sum": 319838, "no_change_requests": 644, "policy_calls": 742, "population_decisions": 742, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 65597, "5": 11490, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 11], "recorded_total_particle_count_range": [6, 56], "removals": 98, "requested_target_histogram": {"2": 0, "3": 0, "4": 742, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 77087}
Query shares: {"birth": 0.003504, "detection": 0.154174, "exclusion": 0.040848, "initialization": 1.2e-05, "memory": 0.007616, "ordinary": 0.633738, "permanent_quantum": 0.154172, "temporary_quantum": 0.005936}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 1.2554936706363373, "completed_environment": 37, "difference": -12.472959466332112, "reference_environment_error": 13.728453136968449}, "most_unfavorable": {"candidate_environment_error": 9.559005934448152, "completed_environment": 8, "difference": 9.151292682802215, "reference_environment_error": 0.4077132516459373}}
case_005 severity=1.0,period=5000: error=1.484595, deltatarget_3=-0.037621, deltatarget_5=+0.188678, deltatarget_7=+0.040726; interval-end error=0.6921598631378211; incomplete responses=0.
Measured population behavior: {"additions": 0, "mean_neutral_count_per_subswarm_update": 4.122517657897431, "neutral_count_sum": 322183, "no_change_requests": 787, "policy_calls": 888, "population_decisions": 888, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 68577, "5": 9575, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 12], "recorded_total_particle_count_range": [6, 62], "removals": 101, "requested_target_histogram": {"2": 0, "3": 0, "4": 888, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 78152}
Query shares: {"birth": 0.002964, "detection": 0.156304, "exclusion": 0.030972, "initialization": 1.2e-05, "memory": 0.009082, "ordinary": 0.63726, "permanent_quantum": 0.156302, "temporary_quantum": 0.007104}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 1.1273568750908778, "completed_environment": 60, "difference": -0.9153308898668162, "reference_environment_error": 2.042687764957694}, "most_unfavorable": {"candidate_environment_error": 13.68292277497604, "completed_environment": 48, "difference": 12.18944550824671, "reference_environment_error": 1.49347726672933}}
case_006 severity=1.0,period=5000: error=1.709514, deltatarget_3=+0.078161, deltatarget_5=+0.023813, deltatarget_7=+0.003139; interval-end error=0.8154953806745595; incomplete responses=0.
Measured population behavior: {"additions": 0, "mean_neutral_count_per_subswarm_update": 4.15061517783292, "neutral_count_sum": 321158, "no_change_requests": 674, "policy_calls": 772, "population_decisions": 772, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 65722, "5": 11654, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 11], "recorded_total_particle_count_range": [6, 57], "removals": 98, "requested_target_histogram": {"2": 0, "3": 0, "4": 772, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 77376}
Query shares: {"birth": 0.003696, "detection": 0.154752, "exclusion": 0.036564, "initialization": 1.2e-05, "memory": 0.007916, "ordinary": 0.636134, "permanent_quantum": 0.15475, "temporary_quantum": 0.006176}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 0.6283663663164571, "completed_environment": 4, "difference": -16.368346336005697, "reference_environment_error": 16.996712702322153}, "most_unfavorable": {"candidate_environment_error": 13.677288567802062, "completed_environment": 36, "difference": 11.613917901468355, "reference_environment_error": 2.0633706663337072}}
case_007 severity=1.0,period=5000: error=2.275401, deltatarget_3=-0.047003, deltatarget_5=+0.606710, deltatarget_7=+0.122350; interval-end error=1.5132049721490224; incomplete responses=0.
Measured population behavior: {"additions": 0, "mean_neutral_count_per_subswarm_update": 4.124034872424196, "neutral_count_sum": 322615, "no_change_requests": 770, "policy_calls": 870, "population_decisions": 870, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 68525, "5": 9703, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 12], "recorded_total_particle_count_range": [6, 61], "removals": 100, "requested_target_histogram": {"2": 0, "3": 0, "4": 870, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 78228}
Query shares: {"birth": 0.003384, "detection": 0.156456, "exclusion": 0.029568, "initialization": 1.2e-05, "memory": 0.0089, "ordinary": 0.638266, "permanent_quantum": 0.156454, "temporary_quantum": 0.00696}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 1.212558756746236, "completed_environment": 47, "difference": -1.585896247731613, "reference_environment_error": 2.798455004477849}, "most_unfavorable": {"candidate_environment_error": 10.888402854040327, "completed_environment": 37, "difference": 9.910882541426226, "reference_environment_error": 0.977520312614101}}
Paired regime summary: {"best_tested_fixed_target": "target_5", "cases": 8, "mean_offline_error": 2.05263705974142, "regime": "severity=1.0,period=5000", "target_3_difference_sd": 0.4147264335080855, "target_3_mean_difference": 0.24629672246933235, "target_5_difference_sd": 0.4293793955330849, "target_5_mean_difference": 0.3080682782264892, "target_7_difference_sd": 0.5722038519975585, "target_7_mean_difference": 0.18097965204105335}
Influential cases versus target_3: best={"case_id": "case_007", "offline_error": 2.2754010579695443, "paired_differences": {"target_3": -0.047003419367982247, "target_5": 0.606710381826999, "target_7": 0.1223504020874926}}; worst={"case_id": "case_002", "offline_error": 3.497788543553557, "paired_differences": {"target_3": 1.1556596618690356, "target_5": 1.2268406839313273, "target_7": 1.5764085094487612}}
Influential cases versus target_5: best={"case_id": "case_003", "offline_error": 0.7320822231537835, "paired_differences": {"target_3": 0.009194422370308875, "target_5": -0.11590118341546263, "target_7": 0.04072956244203785}}; worst={"case_id": "case_002", "offline_error": 3.497788543553557, "paired_differences": {"target_3": 1.1556596618690356, "target_5": 1.2268406839313273, "target_7": 1.5764085094487612}}
Influential cases versus target_7: best={"case_id": "case_000", "offline_error": 2.172372085905322, "paired_differences": {"target_3": 0.24164268630742103, "target_5": 0.12164180669502889, "target_7": -0.19685557542536225}}; worst={"case_id": "case_002", "offline_error": 3.497788543553557, "paired_differences": {"target_3": 1.1556596618690356, "target_5": 1.2268406839313273, "target_7": 1.5764085094487612}}
The chapter suggests adaptive particles within subswarms as future work. This task tests allocation within groups without particle transfer or conserved global population. More trajectories, slower update cycling, convergence changes, memory quality and random closed-loop variation are competing explanations. Fixed targets do not exhaust all constants. Constants remain legitimate; complexity and population variability receive no reward. Every case uses the registered full500000-query development horizon. No protected outcome is supplied.

```python
"""Reconstructed MPSO 5+1: maintain five neutral particles."""

# EVOLVE-BLOCK-START
def choose_neutral_count(observation) -> int:
    return 5
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.36
mean_offline_error: 1.74; worst_case_offline_error: 2.27; case_error_std: 0.49; cases_completed: 8

Text feedback:
Reused development cases only. Lower offline error is better; fitness=1/(1+mean error). Paired differences are candidate minus comparator (negative is better). Target5 is the reconstructed chapter5+1 and native seed. Fixed targets3/7 start at five and resize by at most one per detected event using exactly the same adapter. Best tested fixed target by development mean (numeric target breaks ties): target_5. Only neutral population targets change. Every current neutral quantum-samples on detected change, otherwise uses ordinary PSO; one permanent quantum particle always samples. Whole trajectories, convergence/birth timing and later random draws can diverge.
case_000 severity=1.0,period=5000: error=2.050730, deltatarget_3=+0.120001, deltatarget_5=+0.000000, deltatarget_7=-0.318497; interval-end error=1.3488386340270624; incomplete responses=0.
Measured population behavior: {"additions": 0, "diagnostic_origin": "derived_exactly_from_certified_fixed_five_archive", "mean_neutral_count_per_subswarm_update": 5.0, "neutral_count_sum": 341060, "no_change_requests": 762, "policy_calls": 762, "population_decisions": 762, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 0, "5": 68212, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 11], "recorded_total_particle_count_range": [6, 66], "removals": 0, "requested_target_histogram": {"2": 0, "3": 0, "4": 0, "5": 762, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 68212}
Query shares: {"birth": 0.003312, "detection": 0.136424, "exclusion": 0.032568, "initialization": 1.2e-05, "memory": 0.009144, "ordinary": 0.674498, "permanent_quantum": 0.136422, "temporary_quantum": 0.00762}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 5.580342491664115, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 5.580342491664115}, "most_unfavorable": {"candidate_environment_error": 5.580342491664115, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 5.580342491664115}}
case_001 severity=1.0,period=5000: error=2.232646, deltatarget_3=+0.210478, deltatarget_5=+0.000000, deltatarget_7=-0.358551; interval-end error=1.4366393107545157; incomplete responses=0.
Measured population behavior: {"additions": 0, "diagnostic_origin": "derived_exactly_from_certified_fixed_five_archive", "mean_neutral_count_per_subswarm_update": 5.0, "neutral_count_sum": 343810, "no_change_requests": 887, "policy_calls": 887, "population_decisions": 887, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 0, "5": 68762, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 11], "recorded_total_particle_count_range": [6, 66], "removals": 0, "requested_target_histogram": {"2": 0, "3": 0, "4": 0, "5": 887, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 68762}
Query shares: {"birth": 0.002904, "detection": 0.137524, "exclusion": 0.023772, "initialization": 1.2e-05, "memory": 0.010644, "ordinary": 0.67875, "permanent_quantum": 0.137524, "temporary_quantum": 0.00887}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 0.43098806465241307, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 0.43098806465241307}, "most_unfavorable": {"candidate_environment_error": 0.43098806465241307, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 0.43098806465241307}}
case_002 severity=1.0,period=5000: error=2.270948, deltatarget_3=-0.071181, deltatarget_5=+0.000000, deltatarget_7=+0.349568; interval-end error=1.4596780123398139; incomplete responses=0.
Measured population behavior: {"additions": 0, "diagnostic_origin": "derived_exactly_from_certified_fixed_five_archive", "mean_neutral_count_per_subswarm_update": 5.0, "neutral_count_sum": 340495, "no_change_requests": 757, "policy_calls": 757, "population_decisions": 757, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 0, "5": 68099, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 12], "recorded_total_particle_count_range": [6, 72], "removals": 0, "requested_target_histogram": {"2": 0, "3": 0, "4": 0, "5": 757, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 68099}
Query shares: {"birth": 0.003828, "detection": 0.136198, "exclusion": 0.033696, "initialization": 1.2e-05, "memory": 0.009084, "ordinary": 0.673416, "permanent_quantum": 0.136196, "temporary_quantum": 0.00757}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 8.443235438605006, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 8.443235438605006}, "most_unfavorable": {"candidate_environment_error": 8.443235438605006, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 8.443235438605006}}
case_003 severity=1.0,period=5000: error=0.847983, deltatarget_3=+0.125096, deltatarget_5=+0.000000, deltatarget_7=+0.156631; interval-end error=0.20450217650071778; incomplete responses=0.
Measured population behavior: {"additions": 0, "diagnostic_origin": "derived_exactly_from_certified_fixed_five_archive", "mean_neutral_count_per_subswarm_update": 5.0, "neutral_count_sum": 342750, "no_change_requests": 951, "policy_calls": 951, "population_decisions": 951, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 0, "5": 68550, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 12], "recorded_total_particle_count_range": [6, 72], "removals": 0, "requested_target_histogram": {"2": 0, "3": 0, "4": 0, "5": 951, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 68550}
Query shares: {"birth": 0.002736, "detection": 0.1371, "exclusion": 0.026148, "initialization": 1.2e-05, "memory": 0.011412, "ordinary": 0.675984, "permanent_quantum": 0.137098, "temporary_quantum": 0.00951}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 0.45001874948806153, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 0.45001874948806153}, "most_unfavorable": {"candidate_environment_error": 0.45001874948806153, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 0.45001874948806153}}
case_004 severity=1.0,period=5000: error=1.903934, deltatarget_3=-0.052901, deltatarget_5=+0.000000, deltatarget_7=-0.192874; interval-end error=1.0985351676820563; incomplete responses=0.
Measured population behavior: {"additions": 0, "diagnostic_origin": "derived_exactly_from_certified_fixed_five_archive", "mean_neutral_count_per_subswarm_update": 5.0, "neutral_count_sum": 341095, "no_change_requests": 824, "policy_calls": 824, "population_decisions": 824, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 0, "5": 68219, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 11], "recorded_total_particle_count_range": [6, 66], "removals": 0, "requested_target_histogram": {"2": 0, "3": 0, "4": 0, "5": 824, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 68219}
Query shares: {"birth": 0.002952, "detection": 0.136438, "exclusion": 0.032088, "initialization": 1.2e-05, "memory": 0.009888, "ordinary": 0.673946, "permanent_quantum": 0.136436, "temporary_quantum": 0.00824}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 11.472654224584753, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 11.472654224584753}, "most_unfavorable": {"candidate_environment_error": 11.472654224584753, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 11.472654224584753}}
case_005 severity=1.0,period=5000: error=1.295917, deltatarget_3=-0.226299, deltatarget_5=+0.000000, deltatarget_7=-0.147952; interval-end error=0.4735486709067553; incomplete responses=0.
Measured population behavior: {"additions": 0, "diagnostic_origin": "derived_exactly_from_certified_fixed_five_archive", "mean_neutral_count_per_subswarm_update": 5.0, "neutral_count_sum": 341170, "no_change_requests": 851, "policy_calls": 851, "population_decisions": 851, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 0, "5": 68234, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 12], "recorded_total_particle_count_range": [6, 72], "removals": 0, "requested_target_histogram": {"2": 0, "3": 0, "4": 0, "5": 851, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 68234}
Query shares: {"birth": 0.003108, "detection": 0.136468, "exclusion": 0.031404, "initialization": 1.2e-05, "memory": 0.010212, "ordinary": 0.67382, "permanent_quantum": 0.136466, "temporary_quantum": 0.00851}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 0.13441163866412179, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 0.13441163866412179}, "most_unfavorable": {"candidate_environment_error": 0.13441163866412179, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 0.13441163866412179}}
case_006 severity=1.0,period=5000: error=1.685701, deltatarget_3=+0.054348, deltatarget_5=+0.000000, deltatarget_7=-0.020673; interval-end error=0.8975375693612154; incomplete responses=0.
Measured population behavior: {"additions": 0, "diagnostic_origin": "derived_exactly_from_certified_fixed_five_archive", "mean_neutral_count_per_subswarm_update": 5.0, "neutral_count_sum": 340345, "no_change_requests": 746, "policy_calls": 746, "population_decisions": 746, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 0, "5": 68069, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 11], "recorded_total_particle_count_range": [6, 66], "removals": 0, "requested_target_histogram": {"2": 0, "3": 0, "4": 0, "5": 746, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 68069}
Query shares: {"birth": 0.004092, "detection": 0.136138, "exclusion": 0.033984, "initialization": 1.2e-05, "memory": 0.008952, "ordinary": 0.673226, "permanent_quantum": 0.136136, "temporary_quantum": 0.00746}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 5.411399204515185, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 5.411399204515185}, "most_unfavorable": {"candidate_environment_error": 5.411399204515185, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 5.411399204515185}}
case_007 severity=1.0,period=5000: error=1.668691, deltatarget_3=-0.653714, deltatarget_5=+0.000000, deltatarget_7=-0.484360; interval-end error=0.9185106624752166; incomplete responses=0.
Measured population behavior: {"additions": 0, "diagnostic_origin": "derived_exactly_from_certified_fixed_five_archive", "mean_neutral_count_per_subswarm_update": 5.0, "neutral_count_sum": 342740, "no_change_requests": 824, "policy_calls": 824, "population_decisions": 824, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 0, "5": 68548, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 11], "recorded_total_particle_count_range": [6, 66], "removals": 0, "requested_target_histogram": {"2": 0, "3": 0, "4": 0, "5": 824, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 68548}
Query shares: {"birth": 0.003456, "detection": 0.137096, "exclusion": 0.026976, "initialization": 1.2e-05, "memory": 0.009888, "ordinary": 0.677238, "permanent_quantum": 0.137094, "temporary_quantum": 0.00824}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 3.16316666371599, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 3.16316666371599}, "most_unfavorable": {"candidate_environment_error": 3.16316666371599, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 3.16316666371599}}
Paired regime summary: {"best_tested_fixed_target": "target_5", "cases": 8, "mean_offline_error": 1.7445687815149309, "regime": "severity=1.0,period=5000", "target_3_difference_sd": 0.27599069133623494, "target_3_mean_difference": -0.061771555757156815, "target_5_difference_sd": 0.0, "target_5_mean_difference": 0.0, "target_7_difference_sd": 0.27816749035801897, "target_7_mean_difference": -0.12708862618543582}
Influential cases versus target_3: best={"case_id": "case_007", "offline_error": 1.6686906761425453, "paired_differences": {"target_3": -0.6537138011949812, "target_5": 0.0, "target_7": -0.4843599797395064}}; worst={"case_id": "case_001", "offline_error": 2.23264559928194, "paired_differences": {"target_3": 0.21047756647775495, "target_5": 0.0, "target_7": -0.3585507453208554}}
Influential cases versus target_5: best={"case_id": "case_000", "offline_error": 2.0507302792102933, "paired_differences": {"target_3": 0.12000087961239214, "target_5": 0.0, "target_7": -0.31849738212039114}}; worst={"case_id": "case_007", "offline_error": 1.6686906761425453, "paired_differences": {"target_3": -0.6537138011949812, "target_5": 0.0, "target_7": -0.4843599797395064}}
Influential cases versus target_7: best={"case_id": "case_007", "offline_error": 1.6686906761425453, "paired_differences": {"target_3": -0.6537138011949812, "target_5": 0.0, "target_7": -0.4843599797395064}}; worst={"case_id": "case_002", "offline_error": 2.27094785962223, "paired_differences": {"target_3": -0.07118102206229171, "target_5": 0.0, "target_7": 0.3495678255174339}}
The chapter suggests adaptive particles within subswarms as future work. This task tests allocation within groups without particle transfer or conserved global population. More trajectories, slower update cycling, convergence changes, memory quality and random closed-loop variation are competing explanations. Fixed targets do not exhaust all constants. Constants remain legitimate; complexity and population variability receive no reward. Every case uses the registered full500000-query development horizon. No protected outcome is supplied.


# Current program

Here is the current program we are trying to improve (you will need to propose a modification to it below):

```python
"""Reconstructed MPSO 5+1: maintain five neutral particles."""

# EVOLVE-BLOCK-START
def choose_neutral_count(observation) -> int:
    radius = max(observation["default_radius"], 1e-12)
    if (
        observation["fitness_drop"] <= 0.0
        and observation["neutral_diameter"] <= 2.0 * radius
        and observation["mean_neutral_distance_to_best"] <= radius
        and observation["mean_neutral_speed"] <= radius
    ):
        return 4
    return 5
# EVOLVE-BLOCK-END

```

Here are the performance metrics of the program:

Combined score to maximize: 0.36
mean_offline_error: 1.81; worst_case_offline_error: 2.42; case_error_std: 0.53; cases_completed: 8

Here is additional text feedback about the current program:

Reused development cases only. Lower offline error is better; fitness=1/(1+mean error). Paired differences are candidate minus comparator (negative is better). Target5 is the reconstructed chapter5+1 and native seed. Fixed targets3/7 start at five and resize by at most one per detected event using exactly the same adapter. Best tested fixed target by development mean (numeric target breaks ties): target_5. Only neutral population targets change. Every current neutral quantum-samples on detected change, otherwise uses ordinary PSO; one permanent quantum particle always samples. Whole trajectories, convergence/birth timing and later random draws can diverge.
case_000 severity=1.0,period=5000: error=2.166611, deltatarget_3=+0.235882, deltatarget_5=+0.115881, deltatarget_7=-0.202616; interval-end error=1.5434195036715765; incomplete responses=0.
Measured population behavior: {"additions": 99, "mean_neutral_count_per_subswarm_update": 4.830980476292641, "neutral_count_sum": 337758, "no_change_requests": 570, "policy_calls": 769, "population_decisions": 769, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 11817, "5": 58098, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 11], "recorded_total_particle_count_range": [6, 65], "removals": 100, "requested_target_histogram": {"2": 0, "3": 0, "4": 135, "5": 634, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 69915}
Query shares: {"birth": 0.003696, "detection": 0.13983, "exclusion": 0.03216, "initialization": 1.2e-05, "memory": 0.00896, "ordinary": 0.668094, "permanent_quantum": 0.139828, "temporary_quantum": 0.00742}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 0.695891987308826, "completed_environment": 20, "difference": -3.836424669958658, "reference_environment_error": 4.532316657267484}, "most_unfavorable": {"candidate_environment_error": 14.156798838495515, "completed_environment": 14, "difference": 13.550658295072237, "reference_environment_error": 0.6061405434232772}}
case_001 severity=1.0,period=5000: error=1.929450, deltatarget_3=-0.092718, deltatarget_5=-0.303195, deltatarget_7=-0.661746; interval-end error=1.1930498241269174; incomplete responses=0.
Measured population behavior: {"additions": 98, "mean_neutral_count_per_subswarm_update": 4.8519278155222265, "neutral_count_sum": 340649, "no_change_requests": 616, "policy_calls": 813, "population_decisions": 813, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 10396, "5": 59813, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 11], "recorded_total_particle_count_range": [6, 66], "removals": 99, "requested_target_histogram": {"2": 0, "3": 0, "4": 120, "5": 693, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 70209}
Query shares: {"birth": 0.003804, "detection": 0.140418, "exclusion": 0.02454, "initialization": 1.2e-05, "memory": 0.009518, "ordinary": 0.673402, "permanent_quantum": 0.140416, "temporary_quantum": 0.00789}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 1.164134033776776, "completed_environment": 88, "difference": -14.300269154151032, "reference_environment_error": 15.464403187927807}, "most_unfavorable": {"candidate_environment_error": 6.858081916631075, "completed_environment": 53, "difference": 6.151289515394355, "reference_environment_error": 0.7067924012367199}}
case_002 severity=1.0,period=5000: error=1.892415, deltatarget_3=-0.449714, deltatarget_5=-0.378533, deltatarget_7=-0.028965; interval-end error=0.9697472077666124; incomplete responses=0.
Measured population behavior: {"additions": 84, "mean_neutral_count_per_subswarm_update": 4.868089024442878, "neutral_count_sum": 338376, "no_change_requests": 645, "policy_calls": 815, "population_decisions": 815, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 9169, "5": 60340, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 13], "recorded_total_particle_count_range": [6, 78], "removals": 86, "requested_target_histogram": {"2": 0, "3": 0, "4": 106, "5": 709, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 69509}
Query shares: {"birth": 0.003648, "detection": 0.139018, "exclusion": 0.03198, "initialization": 1.2e-05, "memory": 0.009572, "ordinary": 0.668814, "permanent_quantum": 0.139018, "temporary_quantum": 0.007938}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 0.8524914400768563, "completed_environment": 52, "difference": -9.764117667665618, "reference_environment_error": 10.616609107742473}, "most_unfavorable": {"candidate_environment_error": 3.398386566410843, "completed_environment": 63, "difference": 2.6016729834989345, "reference_environment_error": 0.7967135829119084}}
case_003 severity=1.0,period=5000: error=0.695222, deltatarget_3=-0.027666, deltatarget_5=-0.152761, deltatarget_7=+0.003869; interval-end error=0.07376321097441249; incomplete responses=0.
Measured population behavior: {"additions": 130, "mean_neutral_count_per_subswarm_update": 4.826106144297022, "neutral_count_sum": 339005, "no_change_requests": 675, "policy_calls": 936, "population_decisions": 936, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 12215, "5": 58029, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 13], "recorded_total_particle_count_range": [6, 75], "removals": 131, "requested_target_histogram": {"2": 0, "3": 0, "4": 170, "5": 766, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 70244}
Query shares: {"birth": 0.003504, "detection": 0.140488, "exclusion": 0.026616, "initialization": 1.2e-05, "memory": 0.010894, "ordinary": 0.66898, "permanent_quantum": 0.140486, "temporary_quantum": 0.00902}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 1.177942437295992, "completed_environment": 37, "difference": -4.923575609920844, "reference_environment_error": 6.101518047216836}, "most_unfavorable": {"candidate_environment_error": 3.2610611173871273, "completed_environment": 56, "difference": 2.3130801983388194, "reference_environment_error": 0.9479809190483082}}
case_004 severity=1.0,period=5000: error=2.419979, deltatarget_3=+0.463144, deltatarget_5=+0.516045, deltatarget_7=+0.323171; interval-end error=1.6489155265275581; incomplete responses=0.
Measured population behavior: {"additions": 81, "mean_neutral_count_per_subswarm_update": 4.858102544099164, "neutral_count_sum": 336273, "no_change_requests": 565, "policy_calls": 727, "population_decisions": 727, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 9822, "5": 59397, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 10], "recorded_total_particle_count_range": [6, 60], "removals": 81, "requested_target_histogram": {"2": 0, "3": 0, "4": 109, "5": 618, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 69219}
Query shares: {"birth": 0.00384, "detection": 0.138438, "exclusion": 0.03822, "initialization": 1.2e-05, "memory": 0.008506, "ordinary": 0.665494, "permanent_quantum": 0.138438, "temporary_quantum": 0.007052}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 0.7497422313310481, "completed_environment": 63, "difference": -0.8177927361121583, "reference_environment_error": 1.5675349674432064}, "most_unfavorable": {"candidate_environment_error": 9.590262471185364, "completed_environment": 19, "difference": 8.694136971983536, "reference_environment_error": 0.8961254992018288}}
case_005 severity=1.0,period=5000: error=1.450967, deltatarget_3=-0.071249, deltatarget_5=+0.155050, deltatarget_7=+0.007097; interval-end error=0.6303402165714665; incomplete responses=0.
Measured population behavior: {"additions": 107, "mean_neutral_count_per_subswarm_update": 4.846395476676614, "neutral_count_sum": 339427, "no_change_requests": 697, "policy_calls": 915, "population_decisions": 915, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 10758, "5": 59279, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 12], "recorded_total_particle_count_range": [6, 72], "removals": 111, "requested_target_histogram": {"2": 0, "3": 0, "4": 142, "5": 773, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 70037}
Query shares: {"birth": 0.00348, "detection": 0.140074, "exclusion": 0.026808, "initialization": 1.2e-05, "memory": 0.010704, "ordinary": 0.669984, "permanent_quantum": 0.140072, "temporary_quantum": 0.008866}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 0.4228098935544287, "completed_environment": 32, "difference": -2.038460099011214, "reference_environment_error": 2.4612699925656427}, "most_unfavorable": {"candidate_environment_error": 13.445190913769236, "completed_environment": 48, "difference": 11.951713647039906, "reference_environment_error": 1.49347726672933}}
case_006 severity=1.0,period=5000: error=2.065435, deltatarget_3=+0.434082, deltatarget_5=+0.379734, deltatarget_7=+0.359061; interval-end error=1.2392707911671885; incomplete responses=0.
Measured population behavior: {"additions": 88, "mean_neutral_count_per_subswarm_update": 4.854112934599369, "neutral_count_sum": 336890, "no_change_requests": 572, "policy_calls": 748, "population_decisions": 748, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 10125, "5": 59278, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 11], "recorded_total_particle_count_range": [6, 66], "removals": 88, "requested_target_histogram": {"2": 0, "3": 0, "4": 108, "5": 640, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 69403}
Query shares: {"birth": 0.0042, "detection": 0.138806, "exclusion": 0.03564, "initialization": 1.2e-05, "memory": 0.00876, "ordinary": 0.666514, "permanent_quantum": 0.138804, "temporary_quantum": 0.007264}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 0.506742026235899, "completed_environment": 35, "difference": -4.030634814144387, "reference_environment_error": 4.537376840380285}, "most_unfavorable": {"candidate_environment_error": 17.266434354825666, "completed_environment": 17, "difference": 11.779497007820115, "reference_environment_error": 5.486937347005552}}
case_007 severity=1.0,period=5000: error=1.845983, deltatarget_3=-0.476421, deltatarget_5=+0.177292, deltatarget_7=-0.307068; interval-end error=1.0841001975429165; incomplete responses=0.
Measured population behavior: {"additions": 101, "mean_neutral_count_per_subswarm_update": 4.843526823973034, "neutral_count_sum": 339105, "no_change_requests": 639, "policy_calls": 844, "population_decisions": 844, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 10955, "5": 59057, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 11], "recorded_total_particle_count_range": [6, 66], "removals": 104, "requested_target_histogram": {"2": 0, "3": 0, "4": 132, "5": 712, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 70012}
Query shares: {"birth": 0.003816, "detection": 0.140024, "exclusion": 0.028056, "initialization": 1.2e-05, "memory": 0.00987, "ordinary": 0.670024, "permanent_quantum": 0.140022, "temporary_quantum": 0.008176}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 1.2980750865054327, "completed_environment": 67, "difference": -18.02867479973032, "reference_environment_error": 19.326749886235753}, "most_unfavorable": {"candidate_environment_error": 10.919795802533024, "completed_environment": 37, "difference": 9.942275489918924, "reference_environment_error": 0.977520312614101}}
Paired regime summary: {"best_tested_fixed_target": "target_5", "cases": 8, "mean_offline_error": 1.8082577784910272, "regime": "severity=1.0,period=5000", "target_3_difference_sd": 0.3590063547380531, "target_3_mean_difference": 0.0019174412189395668, "target_5_difference_sd": 0.31746810148537574, "target_5_mean_difference": 0.06368899697609638, "target_7_difference_sd": 0.33281572890496597, "target_7_mean_difference": -0.06339962920933943}
Influential cases versus target_3: best={"case_id": "case_007", "offline_error": 1.8459831039954604, "paired_differences": {"target_3": -0.47642137334206613, "target_5": 0.1772924278529151, "target_7": -0.3070675518865913}}; worst={"case_id": "case_004", "offline_error": 2.4199786592919827, "paired_differences": {"target_3": 0.4631439055868709, "target_5": 0.5160447989028589, "target_7": 0.32317118030250924}}
Influential cases versus target_5: best={"case_id": "case_002", "offline_error": 1.8924147958224533, "paired_differences": {"target_3": -0.4497140858620683, "target_5": -0.3785330637997766, "target_7": -0.028965238282342654}}; worst={"case_id": "case_004", "offline_error": 2.4199786592919827, "paired_differences": {"target_3": 0.4631439055868709, "target_5": 0.5160447989028589, "target_7": 0.32317118030250924}}
Influential cases versus target_7: best={"case_id": "case_001", "offline_error": 1.9294502048541728, "paired_differences": {"target_3": -0.09271782795001204, "target_5": -0.303195394427767, "target_7": -0.6617461397486224}}; worst={"case_id": "case_006", "offline_error": 2.065435449740856, "paired_differences": {"target_3": 0.43408210933513147, "target_5": 0.3797339575202583, "target_7": 0.35906057465347585}}
The chapter suggests adaptive particles within subswarms as future work. This task tests allocation within groups without particle transfer or conserved global population. More trajectories, slower update cycling, convergence changes, memory quality and random closed-loop variation are competing explanations. Fixed targets do not exhaust all constants. Constants remain legitimate; complexity and population variability receive no reward. Every case uses the registered full500000-query development horizon. No protected outcome is supplied.


# Instructions

Make sure that the changes you propose are consistent with each other. For example, if you refer to a new config variable somewhere, you should also propose a change to add that variable.

Note that the changes you propose will be applied sequentially, so you should assume that the previous changes have already been applied when writing the SEARCH block.

# Task

Suggest a new idea to improve the performance of the code that is inspired by your expert knowledge of the considered subject.
Your goal is to maximize the `combined_score` of the program.
Describe each change with a SEARCH/REPLACE block.

IMPORTANT: Do not rewrite the entire program - focus on targeted improvements.
