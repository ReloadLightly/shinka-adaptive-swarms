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
Convergence uses the accurate smallest enclosing ball of all current neutral positions (excluding the permanent role), with documented numerical tolerance. neutral_diameter remains the maximum pairwise distance observation; it is not the enclosing-ball radius. PSO, exclusion after each subswarm
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

Fitness=1/(1+mean offline error), using FOUR reused DEVELOPMENT histories with the corrected convergence engine,
each 500,000 counted objective queries: five dimensions, 200 conical peaks,
movement severity 1, period 5000, correlation 0, nexcess 1. These same four cases
remain fixed throughout selection. Every evaluation category shares this budget.
References are fixed targets 3 and 5 with the SAME start-at-five/one-step adapter;
target 3 is not a historical chapter configuration initialized with three neutrals.
Target 5 is the reconstructed chapter 5+1 and exact native seed; its reference
executions are reused for that source-identical seed. No ten-peak outcome is
substituted for a current reference. Feedback supplies paired errors against both
controls, requested and realized populations, additions/removals, total particles,
subswarm counts, query shares and favorable/unfavorable recovery episodes.
The public global workload fields swarm_count and total_particle_count and the
history field previous_requested_target are available; their use is optional.
Two controls do not exhaust constant rules. Constants remain legitimate; complexity,
conditionality and population variability receive no bonus. Subswarm counts do not
directly establish peak coverage. Fresh outcomes, if any, remain unavailable to
mutation, novelty and meta-memory.

Campaign: 50 descendant slots plus the seed; a session pause is not final selection. All seven constant targets 2..8 are campaign controls, while mutation feedback consistently uses targets 3/5. No fresh comparison occurs in Session 1. Geometry correction is source fidelity, not evolutionary improvement.


# Scientific context supplied to mutation

# Chapter-grounded population allocation: 200 peaks

Blackwell, Branke and Li, "Particle Swarms for Dynamic Optimization Problems"
(2008), describe MPSO's tension between local convergence inside a subswarm and
maintaining several search groups. Personal and shared memories support local
convergence; exclusion and swarm birth/removal sustain search across space. The
chapter identifies adapting particle numbers within a subswarm as future work.
That rationale is a hypothesis to test, not evidence that adaptation must help.

Question: can an evolved population rule improve reconstructed chapter 5+1 MPSO
when 200 peaks compete for a fixed counted objective-evaluation budget?

The preceding ten-peak population study evaluated six valid native descendants.
None improved the reconstructed target-five mean of 1.744569. Fixed target three
scored 1.806340, target seven 1.871657, and the closest descendant (constant target
six) 1.776112. Larger groups shifted queries toward ordinary PSO while average
subswarm counts changed little. Accepted rules did not use the available global
workload or previous-target fields. These are historical ten-peak development
findings, not performance estimates for this new 200-peak condition. The earlier
temporary-conversion search likewise found no better schedule; retain the
published change response throughout this experiment.

Only choose_neutral_count(observation) evolves. The public interface and deterministic resizing adapter are unchanged. The VERSIONED engine repairs convergence: the smallest enclosing ball of neutral positions must fit the current convergence radius; the historical pairwise-diameter approximation is no longer used. This is a source-fidelity repair, never an evolutionary gain. Each newborn/reinitialized swarm
starts with five neutrals plus one permanent quantum particle. The target is an
integer from two through eight; counted change detection and completed memory
refresh precede the call. At most one neutral is added or removed toward the
target before movement. All current neutrals take the chapter quantum-response
movement on that detected update and ordinary PSO otherwise. The permanent
quantum role always samples. Radius, retained velocities, personal memories,
coefficients, exclusion order and swarm birth/removal remain fixed; the corrected enclosing-ball convergence convention is shared by every control and candidate. This changes population within groups, without particle transfers
or conservation of a global particle total.

The four development seed pairs registered in the preceding 200-peak study use five dimensions, 200 conical peaks,
severity one, changes every 5000 queries, correlation zero, nexcess one and
exactly 500000 queries each. All four remain fixed throughout selection. Every
movement, initialization, detector check and memory refresh shares that budget.
Independent environment randomness pairs landscape histories across programs.

Newly measured fixed targets three and five supply the contemporary paired
controls. Both start at five and resize by at most one per detection. Target
five is the reconstructed chapter 5+1 and native seed; source-identical seed
evaluation reuses its four current control cases. No ten-peak record is reused
as a 200-peak result. Candidate fitness is 1/(1+mean offline error), without
complexity or adaptation bonuses. Constant rules are legitimate candidates.

Available public workload fields include swarm_count and total_particle_count;
previous_requested_target records the preceding target of this same subswarm.
These may help express a rule but their use is optional. Other public observations
describe counted deterioration/improvement, neutral spread and motion. Hidden
peak counts/locations, optimum, benchmark error, seeds and future changes are
unavailable to the policy. The known benchmark scale still supplies its radius.

Additional ordinary trajectories may help local search; fewer particles may
permit more subswarm updates under the same budget. Changed convergence and
birth/removal timing, memory quality, random closed-loop effects and constant
size tuning are competing explanations. A conditional expression alone isolates
none of them. Subswarm count is not a count of distinct peaks covered.

This is a resumable 50-descendant campaign, including the seed in final native selection. Session pauses are interim and cannot trigger winner freezing or fresh testing. All seven constant targets 2..8 will be measured before final selection; evolutionary feedback stays consistently against targets three and five. At campaign completion, a distinct native program improving on the seed can trigger a later frozen comparison on 50 NEW paired histories against the corrected 5+1 and independently development-selected constant. Fresh outcomes remain outside mutation, novelty and meta-memory. Constants are legitimate and no complexity or variability bonus applies. This small MPSO extension does not reproduce all chapter conditions, compare SPSO, establish global optimality, or identify a causal benefit of a particular Shinka mechanism.


# Potential Recommendations
The following are potential recommendations for the next program generation:

**Add an exceptional target-four recovery branch.** Using the original adjusted pressure, request four above `0.20`, retain four above `0.12` when the previous request was four, and otherwise apply the two/three rule with its retention threshold for previous targets three or four. Fixed Four’s weak results argue for restricting this extension to exceptional deterioration; the large episode regressions make it a plausible, unproven recovery variation. The existing one-particle resize limit means a swarm at two must sustain the condition across detections to reach four.
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
    """Request two or three neutrals from loss remaining after refresh."""
    previous_best = observation["previous_best_fitness"]
    remaining_loss = max(
        0.0,
        (previous_best - observation["current_best_fitness"])
        / max(1.0, abs(previous_best)),
    )
    loss = min(
        max(0.0, observation["relative_fitness_drop"]), remaining_loss
    )
    swarms = max(1, observation["swarm_count"])
    sweep_queries = max(1.0, observation["total_particle_count"] + swarms)
    threshold = (
        0.04 if observation["previous_requested_target"] == 3 else 0.08
    )
    if loss > threshold * (1.0 + sweep_queries / 160.0):
        return 3
    return 2
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.33
mean_offline_error: 1.99; worst_case_offline_error: 2.24; case_error_std: 0.25; cases_completed: 4

Text feedback:
Four reused DEVELOPMENT histories under the corrected enclosing-ball engine, each five-dimensional with 200 conical peaks, severity 1, change period 5000, correlation 0 and nexcess 1. These same cases are reused throughout selection; no fresh comparison outcome is supplied. Lower offline error is better; fitness=1/(1+mean error). Paired differences are candidate minus comparator (negative is better). Target 5 is the reconstructed chapter 5+1 and native seed. Fixed targets 3 and 5 start at five and resize by at most one per detected event using exactly the same adapter. Best tested fixed target by development mean (numeric target breaks ties): target_3. Only neutral population targets change. Every current neutral quantum-samples on detected change, otherwise uses ordinary PSO; one permanent quantum particle always samples. Whole trajectories, convergence/birth timing and later random draws can diverge. Available public workload fields are swarm_count and total_particle_count; previous_requested_target supplies the preceding target for the same subswarm. The policy may use these fields but need not branch or vary population.
case_000 peaks=200,severity=1.0,period=5000: error=2.238038, deltatarget_3=-0.018421, deltatarget_5=-0.510286; interval-end error=1.4374583333729776; incomplete responses=0.
Measured population behavior: {"additions": 403, "mean_neutral_count_per_subswarm_update": 2.559602867342998, "neutral_count_sum": 271730, "no_change_requests": 1626, "policy_calls": 2668, "population_decisions": 2668, "realized_neutral_count_histogram": {"2": 59780, "3": 37835, "4": 4065, "5": 4481, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 34], "recorded_total_particle_count_range": [6, 123], "removals": 639, "requested_target_histogram": {"2": 1675, "3": 993, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 106161, "trace_mean_sampling": "Regular samples every 100 counted objective evaluations; first-query extra sample excluded", "trace_sampled_mean_swarm_count": 26.9114, "trace_sampled_mean_total_particle_count": 95.0976}
Query shares: {"birth": 0.006912, "detection": 0.212322, "exclusion": 0.005952, "initialization": 1.2e-05, "memory": 0.019022, "ordinary": 0.530246, "permanent_quantum": 0.21232, "temporary_quantum": 0.013214}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 2.8092365695894825, "completed_environment": 6, "difference": -7.506815135357962, "reference_environment_error": 10.316051704947444}, "most_unfavorable": {"candidate_environment_error": 9.508130453488802, "completed_environment": 5, "difference": 3.2210279349700075, "reference_environment_error": 6.287102518518794}}
Observed episodes versus target_3: {"most_favorable": {"candidate_environment_error": 5.073319364623701, "completed_environment": 11, "difference": -3.5624690398215266, "reference_environment_error": 8.635788404445227}, "most_unfavorable": {"candidate_environment_error": 9.508130453488802, "completed_environment": 5, "difference": 4.055578904405338, "reference_environment_error": 5.452551549083464}}
case_001 peaks=200,severity=1.0,period=5000: error=2.027388, deltatarget_3=-0.181353, deltatarget_5=+0.105872; interval-end error=1.3734415616290996; incomplete responses=0.
Measured population behavior: {"additions": 391, "mean_neutral_count_per_subswarm_update": 2.569279321714555, "neutral_count_sum": 272729, "no_change_requests": 1472, "policy_calls": 2486, "population_decisions": 2486, "realized_neutral_count_histogram": {"2": 60291, "3": 36361, "4": 4426, "5": 5072, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 32], "recorded_total_particle_count_range": [6, 116], "removals": 623, "requested_target_histogram": {"2": 1585, "3": 901, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 106150, "trace_mean_sampling": "Regular samples every 100 counted objective evaluations; first-query extra sample excluded", "trace_sampled_mean_swarm_count": 25.2464, "trace_sampled_mean_total_particle_count": 89.2882}
Query shares: {"birth": 0.006924, "detection": 0.2123, "exclusion": 0.005304, "initialization": 1.2e-05, "memory": 0.017702, "ordinary": 0.533192, "permanent_quantum": 0.2123, "temporary_quantum": 0.012266}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 0.6038688477903027, "completed_environment": 41, "difference": -3.9505782491883426, "reference_environment_error": 4.554447096978645}, "most_unfavorable": {"candidate_environment_error": 13.968353035725569, "completed_environment": 2, "difference": 10.931850956701222, "reference_environment_error": 3.0365020790243475}}
Observed episodes versus target_3: {"most_favorable": {"candidate_environment_error": 0.6038688477903027, "completed_environment": 41, "difference": -3.679113186714701, "reference_environment_error": 4.282982034505004}, "most_unfavorable": {"candidate_environment_error": 6.0538619451467275, "completed_environment": 82, "difference": 4.500669366386239, "reference_environment_error": 1.553192578760489}}
case_002 peaks=200,severity=1.0,period=5000: error=1.633743, deltatarget_3=-0.135050, deltatarget_5=-0.173896; interval-end error=1.0653649677314039; incomplete responses=0.
Measured population behavior: {"additions": 353, "mean_neutral_count_per_subswarm_update": 2.5664033036657115, "neutral_count_sum": 272203, "no_change_requests": 1380, "policy_calls": 2326, "population_decisions": 2326, "realized_neutral_count_histogram": {"2": 61291, "3": 34822, "4": 4600, "5": 5351, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 31], "recorded_total_particle_count_range": [6, 112], "removals": 593, "requested_target_histogram": {"2": 1526, "3": 800, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 106064, "trace_mean_sampling": "Regular samples every 100 counted objective evaluations; first-query extra sample excluded", "trace_sampled_mean_swarm_count": 23.57, "trace_sampled_mean_total_particle_count": 83.4784}
Query shares: {"birth": 0.006708, "detection": 0.212128, "exclusion": 0.008016, "initialization": 1.2e-05, "memory": 0.016602, "ordinary": 0.532936, "permanent_quantum": 0.212128, "temporary_quantum": 0.01147}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 2.2094900063865053, "completed_environment": 14, "difference": -3.5449168463457355, "reference_environment_error": 5.754406852732241}, "most_unfavorable": {"candidate_environment_error": 4.344919641589527, "completed_environment": 35, "difference": 3.131756388736685, "reference_environment_error": 1.2131632528528422}}
Observed episodes versus target_3: {"most_favorable": {"candidate_environment_error": 0.6867002898719605, "completed_environment": 17, "difference": -2.1796331237050808, "reference_environment_error": 2.8663334135770415}, "most_unfavorable": {"candidate_environment_error": 4.667319618213355, "completed_environment": 36, "difference": 2.6332715099013693, "reference_environment_error": 2.034048108311986}}
case_003 peaks=200,severity=1.0,period=5000: error=2.059940, deltatarget_3=-0.072439, deltatarget_5=-0.227714; interval-end error=1.3452534976003652; incomplete responses=0.
Measured population behavior: {"additions": 406, "mean_neutral_count_per_subswarm_update": 2.5635064127916833, "neutral_count_sum": 272229, "no_change_requests": 1527, "policy_calls": 2574, "population_decisions": 2574, "realized_neutral_count_histogram": {"2": 60675, "3": 36328, "4": 4060, "5": 5131, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 33], "recorded_total_particle_count_range": [6, 119], "removals": 641, "requested_target_histogram": {"2": 1652, "3": 922, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 106194, "trace_mean_sampling": "Regular samples every 100 counted objective evaluations; first-query extra sample excluded", "trace_sampled_mean_swarm_count": 26.0396, "trace_sampled_mean_total_particle_count": 91.912}
Query shares: {"birth": 0.00714, "detection": 0.212388, "exclusion": 0.005316, "initialization": 1.2e-05, "memory": 0.018302, "ordinary": 0.531772, "permanent_quantum": 0.212386, "temporary_quantum": 0.012684}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 2.023802968819908, "completed_environment": 14, "difference": -4.08099384043409, "reference_environment_error": 6.104796809253998}, "most_unfavorable": {"candidate_environment_error": 6.866966423261682, "completed_environment": 46, "difference": 5.69987593681798, "reference_environment_error": 1.1670904864437026}}
Observed episodes versus target_3: {"most_favorable": {"candidate_environment_error": 0.5742465567153288, "completed_environment": 71, "difference": -3.831962388747087, "reference_environment_error": 4.406208945462415}, "most_unfavorable": {"candidate_environment_error": 6.866966423261682, "completed_environment": 46, "difference": 5.58128367094495, "reference_environment_error": 1.2856827523167322}}
Paired regime summary: {"best_tested_fixed_target": "target_3", "cases": 4, "mean_offline_error": 1.9897772921634755, "regime": "peaks=200,severity=1.0,period=5000", "target_3_difference_sd": 0.0712935475480183, "target_3_mean_difference": -0.10181598081093118, "target_5_difference_sd": 0.25250464212468865, "target_5_mean_difference": -0.2015059102908478}
Influential cases versus target_3: best={"case_id": "case_001", "offline_error": 2.027388162097834, "paired_differences": {"target_3": -0.18135307281510693, "target_5": 0.10587205152850232}}; worst={"case_id": "case_000", "offline_error": 2.2380378253935294, "paired_differences": {"target_3": -0.018421378362869945, "target_5": -0.5102864052852332}}
Influential cases versus target_5: best={"case_id": "case_000", "offline_error": 2.2380378253935294, "paired_differences": {"target_3": -0.018421378362869945, "target_5": -0.5102864052852332}}; worst={"case_id": "case_001", "offline_error": 2.027388162097834, "paired_differences": {"target_3": -0.18135307281510693, "target_5": 0.10587205152850232}}
The chapter suggests adaptive particles within subswarms as future work. This task tests allocation within groups without particle transfer or conserved global population. More trajectories, slower update cycling, convergence changes, memory quality and random closed-loop variation are competing explanations. Fixed targets do not exhaust all constants. Constants remain legitimate; complexity and population variability receive no reward. Every case uses the registered full 500000-query development horizon. Subswarm count does not directly measure distinct peak coverage. No protected outcome is supplied.

```python
"""Reconstructed MPSO 5+1: maintain five neutral particles."""

# EVOLVE-BLOCK-START
def choose_neutral_count(observation) -> int:
    """Choose two or three neutrals using workload-adjusted loss hysteresis."""
    # Estimate movement and detection queries per optimizer sweep.
    loss = max(0.0, observation["relative_fitness_drop"])
    swarms = max(1, observation["swarm_count"])
    sweep_queries = max(
        1.0, observation["total_particle_count"] + swarms
    )
    # Greater existing workload raises the evidence required for growth.
    recovery_pressure = loss / (1.0 + sweep_queries / 160.0)
    # History is supplied by the caller; no state is retained here.
    threshold = (
        0.04 if observation["previous_requested_target"] == 3 else 0.08
    )
    return 3 if recovery_pressure > threshold else 2
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.34
mean_offline_error: 1.93; worst_case_offline_error: 2.15; case_error_std: 0.21; cases_completed: 4

Text feedback:
Four reused DEVELOPMENT histories under the corrected enclosing-ball engine, each five-dimensional with 200 conical peaks, severity 1, change period 5000, correlation 0 and nexcess 1. These same cases are reused throughout selection; no fresh comparison outcome is supplied. Lower offline error is better; fitness=1/(1+mean error). Paired differences are candidate minus comparator (negative is better). Target 5 is the reconstructed chapter 5+1 and native seed. Fixed targets 3 and 5 start at five and resize by at most one per detected event using exactly the same adapter. Best tested fixed target by development mean (numeric target breaks ties): target_3. Only neutral population targets change. Every current neutral quantum-samples on detected change, otherwise uses ordinary PSO; one permanent quantum particle always samples. Whole trajectories, convergence/birth timing and later random draws can diverge. Available public workload fields are swarm_count and total_particle_count; previous_requested_target supplies the preceding target for the same subswarm. The policy may use these fields but need not branch or vary population.
case_000 peaks=200,severity=1.0,period=5000: error=2.153475, deltatarget_3=-0.102985, deltatarget_5=-0.594850; interval-end error=1.4093421129266235; incomplete responses=0.
Measured population behavior: {"additions": 397, "mean_neutral_count_per_subswarm_update": 2.561776571277759, "neutral_count_sum": 271784, "no_change_requests": 1581, "policy_calls": 2610, "population_decisions": 2610, "realized_neutral_count_histogram": {"2": 60006, "3": 37227, "4": 4204, "5": 4655, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 34], "recorded_total_particle_count_range": [6, 123], "removals": 632, "requested_target_histogram": {"2": 1638, "3": 972, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 106092, "trace_mean_sampling": "Regular samples every 100 counted objective evaluations; first-query extra sample excluded", "trace_sampled_mean_swarm_count": 26.3706, "trace_sampled_mean_total_particle_count": 93.2734}
Query shares: {"birth": 0.006912, "detection": 0.212184, "exclusion": 0.00654, "initialization": 1.2e-05, "memory": 0.018606, "ordinary": 0.530648, "permanent_quantum": 0.212182, "temporary_quantum": 0.012916}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 2.8092365695894825, "completed_environment": 6, "difference": -7.506815135357962, "reference_environment_error": 10.316051704947444}, "most_unfavorable": {"candidate_environment_error": 9.508130453488802, "completed_environment": 5, "difference": 3.2210279349700075, "reference_environment_error": 6.287102518518794}}
Observed episodes versus target_3: {"most_favorable": {"candidate_environment_error": 5.073319364623701, "completed_environment": 11, "difference": -3.5624690398215266, "reference_environment_error": 8.635788404445227}, "most_unfavorable": {"candidate_environment_error": 9.508130453488802, "completed_environment": 5, "difference": 4.055578904405338, "reference_environment_error": 5.452551549083464}}
case_001 peaks=200,severity=1.0,period=5000: error=1.939183, deltatarget_3=-0.269559, deltatarget_5=+0.017667; interval-end error=1.271768183485142; incomplete responses=0.
Measured population behavior: {"additions": 408, "mean_neutral_count_per_subswarm_update": 2.556054064730946, "neutral_count_sum": 271752, "no_change_requests": 1582, "policy_calls": 2628, "population_decisions": 2628, "realized_neutral_count_histogram": {"2": 61040, "3": 36162, "4": 4389, "5": 4726, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 36], "recorded_total_particle_count_range": [6, 129], "removals": 638, "requested_target_histogram": {"2": 1680, "3": 948, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 106317, "trace_mean_sampling": "Regular samples every 100 counted objective evaluations; first-query extra sample excluded", "trace_sampled_mean_swarm_count": 26.5616, "trace_sampled_mean_total_particle_count": 93.4648}
Query shares: {"birth": 0.006792, "detection": 0.212634, "exclusion": 0.005796, "initialization": 1.2e-05, "memory": 0.018628, "ordinary": 0.530592, "permanent_quantum": 0.212634, "temporary_quantum": 0.012912}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 0.4317047407780971, "completed_environment": 41, "difference": -4.122742356200548, "reference_environment_error": 4.554447096978645}, "most_unfavorable": {"candidate_environment_error": 13.968353035725569, "completed_environment": 2, "difference": 10.931850956701222, "reference_environment_error": 3.0365020790243475}}
Observed episodes versus target_3: {"most_favorable": {"candidate_environment_error": 0.4317047407780971, "completed_environment": 41, "difference": -3.851277293726907, "reference_environment_error": 4.282982034505004}, "most_unfavorable": {"candidate_environment_error": 3.712816943371616, "completed_environment": 16, "difference": 3.141108713411068, "reference_environment_error": 0.5717082299605483}}
case_002 peaks=200,severity=1.0,period=5000: error=1.650449, deltatarget_3=-0.118344, deltatarget_5=-0.157189; interval-end error=1.0267682454573024; incomplete responses=0.
Measured population behavior: {"additions": 364, "mean_neutral_count_per_subswarm_update": 2.573597303650834, "neutral_count_sum": 272598, "no_change_requests": 1516, "policy_calls": 2469, "population_decisions": 2469, "realized_neutral_count_histogram": {"2": 59404, "3": 37342, "4": 4111, "5": 5064, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 31], "recorded_total_particle_count_range": [6, 116], "removals": 589, "requested_target_histogram": {"2": 1541, "3": 928, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 105921, "trace_mean_sampling": "Regular samples every 100 counted objective evaluations; first-query extra sample excluded", "trace_sampled_mean_swarm_count": 25.0232, "trace_sampled_mean_total_particle_count": 88.8348}
Query shares: {"birth": 0.006576, "detection": 0.211842, "exclusion": 0.0069, "initialization": 1.2e-05, "memory": 0.017638, "ordinary": 0.532942, "permanent_quantum": 0.21184, "temporary_quantum": 0.01225}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 2.3573688482263897, "completed_environment": 14, "difference": -3.397038004505851, "reference_environment_error": 5.754406852732241}, "most_unfavorable": {"candidate_environment_error": 4.777122637859883, "completed_environment": 27, "difference": 2.4990758195503293, "reference_environment_error": 2.2780468183095532}}
Observed episodes versus target_3: {"most_favorable": {"candidate_environment_error": 0.5700764142274642, "completed_environment": 17, "difference": -2.2962569993495774, "reference_environment_error": 2.8663334135770415}, "most_unfavorable": {"candidate_environment_error": 4.777122637859883, "completed_environment": 27, "difference": 2.3810573188631126, "reference_environment_error": 2.39606531899677}}
case_003 peaks=200,severity=1.0,period=5000: error=1.971854, deltatarget_3=-0.160526, deltatarget_5=-0.315800; interval-end error=1.2365797858081824; incomplete responses=0.
Measured population behavior: {"additions": 413, "mean_neutral_count_per_subswarm_update": 2.552527683254686, "neutral_count_sum": 271543, "no_change_requests": 1677, "policy_calls": 2734, "population_decisions": 2734, "realized_neutral_count_histogram": {"2": 61388, "3": 36147, "4": 3909, "5": 4938, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 37], "recorded_total_particle_count_range": [6, 131], "removals": 644, "requested_target_histogram": {"2": 1749, "3": 985, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 106382, "trace_mean_sampling": "Regular samples every 100 counted objective evaluations; first-query extra sample excluded", "trace_sampled_mean_swarm_count": 27.7034, "trace_sampled_mean_total_particle_count": 97.46}
Query shares: {"birth": 0.00678, "detection": 0.212764, "exclusion": 0.005244, "initialization": 1.2e-05, "memory": 0.019354, "ordinary": 0.52966, "permanent_quantum": 0.212762, "temporary_quantum": 0.013424}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 2.023802968819908, "completed_environment": 14, "difference": -4.08099384043409, "reference_environment_error": 6.104796809253998}, "most_unfavorable": {"candidate_environment_error": 6.520279341630464, "completed_environment": 31, "difference": 3.899981481749599, "reference_environment_error": 2.620297859880865}}
Observed episodes versus target_3: {"most_favorable": {"candidate_environment_error": 0.5138094519401106, "completed_environment": 71, "difference": -3.892399493522305, "reference_environment_error": 4.406208945462415}, "most_unfavorable": {"candidate_environment_error": 6.520279341630464, "completed_environment": 31, "difference": 5.457440656476967, "reference_environment_error": 1.0628386851534968}}
Paired regime summary: {"best_tested_fixed_target": "target_3", "cases": 4, "mean_offline_error": 1.9287400327972029, "regime": "peaks=200,severity=1.0,period=5000", "target_3_difference_sd": 0.07518149204672546, "target_3_mean_difference": -0.16285324017720398, "target_5_difference_sd": 0.26005177592629647, "target_5_mean_difference": -0.2625431696571206}
Influential cases versus target_3: best={"case_id": "case_001", "offline_error": 1.939182673604377, "paired_differences": {"target_3": -0.26955856130856404, "target_5": 0.017666563035045213}}; worst={"case_id": "case_000", "offline_error": 2.1534746286538526, "paired_differences": {"target_3": -0.10298457510254666, "target_5": -0.5948496020249099}}
Influential cases versus target_5: best={"case_id": "case_000", "offline_error": 2.1534746286538526, "paired_differences": {"target_3": -0.10298457510254666, "target_5": -0.5948496020249099}}; worst={"case_id": "case_001", "offline_error": 1.939182673604377, "paired_differences": {"target_3": -0.26955856130856404, "target_5": 0.017666563035045213}}
The chapter suggests adaptive particles within subswarms as future work. This task tests allocation within groups without particle transfer or conserved global population. More trajectories, slower update cycling, convergence changes, memory quality and random closed-loop variation are competing explanations. Fixed targets do not exhaust all constants. Constants remain legitimate; complexity and population variability receive no reward. Every case uses the registered full 500000-query development horizon. Subswarm count does not directly measure distinct peak coverage. No protected outcome is supplied.


# Current program

Here is the current program we are trying to improve (you will need to propose a modification to it below):

```python
"""Reconstructed MPSO 5+1: maintain five neutral particles."""

# EVOLVE-BLOCK-START
def choose_neutral_count(observation) -> int:
    """Choose two or three neutrals using workload-adjusted loss hysteresis."""
    # Estimate movement and detection queries per optimizer sweep.
    loss = max(0.0, observation["relative_fitness_drop"])
    swarms = max(1, observation["swarm_count"])
    sweep_queries = max(
        1.0, observation["total_particle_count"] + swarms
    )
    # Raise the evidence required for growth, with a bounded workload penalty.
    recovery_pressure = loss / (1.0 + min(sweep_queries, 120.0) / 160.0)
    # History is supplied by the caller; no state is retained here.
    threshold = (
        0.04 if observation["previous_requested_target"] == 3 else 0.08
    )
    return 3 if recovery_pressure > threshold else 2
# EVOLVE-BLOCK-END

```

Here are the performance metrics of the program:

Combined score to maximize: 0.33
mean_offline_error: 2.06; worst_case_offline_error: 2.24; case_error_std: 0.20; cases_completed: 4

Here is additional text feedback about the current program:

Four reused DEVELOPMENT histories under the corrected enclosing-ball engine, each five-dimensional with 200 conical peaks, severity 1, change period 5000, correlation 0 and nexcess 1. These same cases are reused throughout selection; no fresh comparison outcome is supplied. Lower offline error is better; fitness=1/(1+mean error). Paired differences are candidate minus comparator (negative is better). Target 5 is the reconstructed chapter 5+1 and native seed. Fixed targets 3 and 5 start at five and resize by at most one per detected event using exactly the same adapter. Best tested fixed target by development mean (numeric target breaks ties): target_3. Only neutral population targets change. Every current neutral quantum-samples on detected change, otherwise uses ordinary PSO; one permanent quantum particle always samples. Whole trajectories, convergence/birth timing and later random draws can diverge. Available public workload fields are swarm_count and total_particle_count; previous_requested_target supplies the preceding target for the same subswarm. The policy may use these fields but need not branch or vary population.
case_000 peaks=200,severity=1.0,period=5000: error=2.154890, deltatarget_3=-0.101569, deltatarget_5=-0.593434; interval-end error=1.3743739109734145; incomplete responses=0.
Measured population behavior: {"additions": 413, "mean_neutral_count_per_subswarm_update": 2.5811969049806325, "neutral_count_sum": 272546, "no_change_requests": 1707, "policy_calls": 2776, "population_decisions": 2776, "realized_neutral_count_histogram": {"2": 57026, "3": 40134, "4": 4053, "5": 4376, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 35], "recorded_total_particle_count_range": [6, 128], "removals": 656, "requested_target_histogram": {"2": 1654, "3": 1122, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 105589, "trace_mean_sampling": "Regular samples every 100 counted objective evaluations; first-query extra sample excluded", "trace_sampled_mean_swarm_count": 28.0072, "trace_sampled_mean_total_particle_count": 99.5722}
Query shares: {"birth": 0.00648, "detection": 0.211178, "exclusion": 0.006156, "initialization": 1.2e-05, "memory": 0.019908, "ordinary": 0.53122, "permanent_quantum": 0.211176, "temporary_quantum": 0.01387}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 2.8092365695894825, "completed_environment": 6, "difference": -7.506815135357962, "reference_environment_error": 10.316051704947444}, "most_unfavorable": {"candidate_environment_error": 9.508130453488802, "completed_environment": 5, "difference": 3.2210279349700075, "reference_environment_error": 6.287102518518794}}
Observed episodes versus target_3: {"most_favorable": {"candidate_environment_error": 5.073319364623701, "completed_environment": 11, "difference": -3.5624690398215266, "reference_environment_error": 8.635788404445227}, "most_unfavorable": {"candidate_environment_error": 9.508130453488802, "completed_environment": 5, "difference": 4.055578904405338, "reference_environment_error": 5.452551549083464}}
case_001 peaks=200,severity=1.0,period=5000: error=2.241244, deltatarget_3=+0.032502, deltatarget_5=+0.319727; interval-end error=1.5750915446968135; incomplete responses=0.
Measured population behavior: {"additions": 427, "mean_neutral_count_per_subswarm_update": 2.5977427921092566, "neutral_count_sum": 273906, "no_change_requests": 1489, "policy_calls": 2574, "population_decisions": 2574, "realized_neutral_count_histogram": {"2": 56567, "3": 39618, "4": 4357, "5": 4898, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 35], "recorded_total_particle_count_range": [6, 128], "removals": 658, "requested_target_histogram": {"2": 1541, "3": 1033, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 105440, "trace_mean_sampling": "Regular samples every 100 counted objective evaluations; first-query extra sample excluded", "trace_sampled_mean_swarm_count": 26.0198, "trace_sampled_mean_total_particle_count": 92.7364}
Query shares: {"birth": 0.006684, "detection": 0.21088, "exclusion": 0.005244, "initialization": 1.2e-05, "memory": 0.018488, "ordinary": 0.534934, "permanent_quantum": 0.21088, "temporary_quantum": 0.012878}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 0.6390085343517046, "completed_environment": 41, "difference": -3.9154385626269406, "reference_environment_error": 4.554447096978645}, "most_unfavorable": {"candidate_environment_error": 13.968353035725569, "completed_environment": 2, "difference": 10.931850956701222, "reference_environment_error": 3.0365020790243475}}
Observed episodes versus target_3: {"most_favorable": {"candidate_environment_error": 0.6390085343517046, "completed_environment": 41, "difference": -3.643973500153299, "reference_environment_error": 4.282982034505004}, "most_unfavorable": {"candidate_environment_error": 6.37949577634846, "completed_environment": 82, "difference": 4.82630319758797, "reference_environment_error": 1.553192578760489}}
case_002 peaks=200,severity=1.0,period=5000: error=1.787491, deltatarget_3=+0.018697, deltatarget_5=-0.020148; interval-end error=1.105290034026838; incomplete responses=0.
Measured population behavior: {"additions": 379, "mean_neutral_count_per_subswarm_update": 2.5766670129281444, "neutral_count_sum": 272851, "no_change_requests": 1539, "policy_calls": 2527, "population_decisions": 2527, "realized_neutral_count_histogram": {"2": 58655, "3": 38318, "4": 4013, "5": 4907, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 33], "recorded_total_particle_count_range": [6, 123], "removals": 609, "requested_target_histogram": {"2": 1555, "3": 972, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 105893, "trace_mean_sampling": "Regular samples every 100 counted objective evaluations; first-query extra sample excluded", "trace_sampled_mean_swarm_count": 25.5714, "trace_sampled_mean_total_particle_count": 90.8498}
Query shares: {"birth": 0.006564, "detection": 0.211786, "exclusion": 0.006072, "initialization": 1.2e-05, "memory": 0.018086, "ordinary": 0.533124, "permanent_quantum": 0.211784, "temporary_quantum": 0.012572}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 2.3573688482263897, "completed_environment": 14, "difference": -3.397038004505851, "reference_environment_error": 5.754406852732241}, "most_unfavorable": {"candidate_environment_error": 7.908351875199906, "completed_environment": 68, "difference": 4.3476910902556565, "reference_environment_error": 3.56066078494425}}
Observed episodes versus target_3: {"most_favorable": {"candidate_environment_error": 0.5700764142274642, "completed_environment": 17, "difference": -2.2962569993495774, "reference_environment_error": 2.8663334135770415}, "most_unfavorable": {"candidate_environment_error": 7.908351875199906, "completed_environment": 68, "difference": 4.492827829933141, "reference_environment_error": 3.4155240452667646}}
case_003 peaks=200,severity=1.0,period=5000: error=2.047271, deltatarget_3=-0.085109, deltatarget_5=-0.240383; interval-end error=1.291114683764719; incomplete responses=0.
Measured population behavior: {"additions": 404, "mean_neutral_count_per_subswarm_update": 2.565914701946816, "neutral_count_sum": 272300, "no_change_requests": 1520, "policy_calls": 2547, "population_decisions": 2547, "realized_neutral_count_histogram": {"2": 60136, "3": 36987, "4": 3928, "5": 5071, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 32], "recorded_total_particle_count_range": [6, 116], "removals": 623, "requested_target_histogram": {"2": 1596, "3": 951, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 106122, "trace_mean_sampling": "Regular samples every 100 counted objective evaluations; first-query extra sample excluded", "trace_sampled_mean_swarm_count": 25.8206, "trace_sampled_mean_total_particle_count": 91.278}
Query shares: {"birth": 0.00732, "detection": 0.212244, "exclusion": 0.005484, "initialization": 1.2e-05, "memory": 0.018096, "ordinary": 0.532036, "permanent_quantum": 0.212244, "temporary_quantum": 0.012564}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 2.023802968819908, "completed_environment": 14, "difference": -4.08099384043409, "reference_environment_error": 6.104796809253998}, "most_unfavorable": {"candidate_environment_error": 6.520279341630464, "completed_environment": 31, "difference": 3.899981481749599, "reference_environment_error": 2.620297859880865}}
Observed episodes versus target_3: {"most_favorable": {"candidate_environment_error": 2.319408373608672, "completed_environment": 30, "difference": -3.4627154399570905, "reference_environment_error": 5.782123813565763}, "most_unfavorable": {"candidate_environment_error": 6.520279341630464, "completed_environment": 31, "difference": 5.457440656476967, "reference_environment_error": 1.0628386851534968}}
Paired regime summary: {"best_tested_fixed_target": "target_3", "cases": 4, "mean_offline_error": 2.0577237198827083, "regime": "peaks=200,severity=1.0,period=5000", "target_3_difference_sd": 0.06922717904302914, "target_3_mean_difference": -0.03386955309169842, "target_5_difference_sd": 0.38350460133011727, "target_5_mean_difference": -0.13355948257161504}
Influential cases versus target_3: best={"case_id": "case_000", "offline_error": 2.1548898884768177, "paired_differences": {"target_3": -0.10156931527958157, "target_5": -0.5934343422019448}}; worst={"case_id": "case_001", "offline_error": 2.241243543238394, "paired_differences": {"target_3": 0.0325023083254532, "target_5": 0.31972743266906245}}
Influential cases versus target_5: best={"case_id": "case_000", "offline_error": 2.1548898884768177, "paired_differences": {"target_3": -0.10156931527958157, "target_5": -0.5934343422019448}}; worst={"case_id": "case_001", "offline_error": 2.241243543238394, "paired_differences": {"target_3": 0.0325023083254532, "target_5": 0.31972743266906245}}
The chapter suggests adaptive particles within subswarms as future work. This task tests allocation within groups without particle transfer or conserved global population. More trajectories, slower update cycling, convergence changes, memory quality and random closed-loop variation are competing explanations. Fixed targets do not exhaust all constants. Constants remain legitimate; complexity and population variability receive no reward. Every case uses the registered full 500000-query development horizon. Subswarm count does not directly measure distinct peak coverage. No protected outcome is supplied.


# Instructions

Make sure that the changes you propose are consistent with each other. For example, if you refer to a new config variable somewhere, you should also propose a change to add that variable.

Note that the changes you propose will be applied sequentially, so you should assume that the previous changes have already been applied when writing the SEARCH block.

# Task

Suggest a new idea to improve the performance of the code that is inspired by your expert knowledge of the considered subject.
Your goal is to maximize the `combined_score` of the program.
Describe each change with a SEARCH/REPLACE block.

IMPORTANT: Do not rewrite the entire program - focus on targeted improvements.
