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
"""Reconstructed MPSO 5+1: maintain five neutral particles."""

# EVOLVE-BLOCK-START
def choose_neutral_count(observation) -> int:
    return 4
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.31
mean_offline_error: 2.18; worst_case_offline_error: 2.35; case_error_std: 0.26; cases_completed: 4

Text feedback:
Four reused DEVELOPMENT histories under the corrected enclosing-ball engine, each five-dimensional with 200 conical peaks, severity 1, change period 5000, correlation 0 and nexcess 1. These same cases are reused throughout selection; no fresh comparison outcome is supplied. Lower offline error is better; fitness=1/(1+mean error). Paired differences are candidate minus comparator (negative is better). Target 5 is the reconstructed chapter 5+1 and native seed. Fixed targets 3 and 5 start at five and resize by at most one per detected event using exactly the same adapter. Best tested fixed target by development mean (numeric target breaks ties): target_3. Only neutral population targets change. Every current neutral quantum-samples on detected change, otherwise uses ordinary PSO; one permanent quantum particle always samples. Whole trajectories, convergence/birth timing and later random draws can diverge. Available public workload fields are swarm_count and total_particle_count; previous_requested_target supplies the preceding target for the same subswarm. The policy may use these fields but need not branch or vary population.
case_000 peaks=200,severity=1.0,period=5000: error=2.349921, deltatarget_3=+0.093462, deltatarget_5=-0.398403; interval-end error=1.5478801218167828; incomplete responses=0.
Measured population behavior: {"additions": 0, "mean_neutral_count_per_subswarm_update": 4.03632151312208, "neutral_count_sum": 318825, "no_change_requests": 3714, "policy_calls": 3829, "population_decisions": 3829, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 76120, "5": 2869, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 55], "recorded_total_particle_count_range": [6, 277], "removals": 115, "requested_target_histogram": {"2": 0, "3": 0, "4": 3829, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 78989, "trace_mean_sampling": "Regular samples every 100 counted objective evaluations; first-query extra sample excluded", "trace_sampled_mean_swarm_count": 38.8878, "trace_sampled_mean_total_particle_count": 195.3778}
Query shares: {"birth": 0.003444, "detection": 0.157978, "exclusion": 0.004428, "initialization": 1.2e-05, "memory": 0.03852, "ordinary": 0.60701, "permanent_quantum": 0.157976, "temporary_quantum": 0.030632}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 2.4466357100143648, "completed_environment": 6, "difference": -7.86941599493308, "reference_environment_error": 10.316051704947444}, "most_unfavorable": {"candidate_environment_error": 5.919581459676875, "completed_environment": 96, "difference": 3.6560391140790216, "reference_environment_error": 2.2635423455978536}}
Observed episodes versus target_3: {"most_favorable": {"candidate_environment_error": 1.0966028144813027, "completed_environment": 12, "difference": -4.077052383220473, "reference_environment_error": 5.173655197701776}, "most_unfavorable": {"candidate_environment_error": 9.802022022245206, "completed_environment": 5, "difference": 4.349470473161742, "reference_environment_error": 5.452551549083464}}
case_001 peaks=200,severity=1.0,period=5000: error=2.235428, deltatarget_3=+0.026687, deltatarget_5=+0.313912; interval-end error=1.4746951994479007; incomplete responses=0.
Measured population behavior: {"additions": 0, "mean_neutral_count_per_subswarm_update": 4.039482167916156, "neutral_count_sum": 319519, "no_change_requests": 3647, "policy_calls": 3756, "population_decisions": 3756, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 75976, "5": 3123, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 55], "recorded_total_particle_count_range": [6, 276], "removals": 109, "requested_target_histogram": {"2": 0, "3": 0, "4": 3756, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 79099, "trace_mean_sampling": "Regular samples every 100 counted objective evaluations; first-query extra sample excluded", "trace_sampled_mean_swarm_count": 38.2554, "trace_sampled_mean_total_particle_count": 192.1894}
Query shares: {"birth": 0.003744, "detection": 0.158198, "exclusion": 0.003036, "initialization": 1.2e-05, "memory": 0.037778, "ordinary": 0.608988, "permanent_quantum": 0.158196, "temporary_quantum": 0.030048}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 1.3565483131312557, "completed_environment": 41, "difference": -3.1978987838473896, "reference_environment_error": 4.554447096978645}, "most_unfavorable": {"candidate_environment_error": 13.96090240983191, "completed_environment": 2, "difference": 10.924400330807561, "reference_environment_error": 3.0365020790243475}}
Observed episodes versus target_3: {"most_favorable": {"candidate_environment_error": 1.3771583843921014, "completed_environment": 47, "difference": -3.0990647736282804, "reference_environment_error": 4.476223158020382}, "most_unfavorable": {"candidate_environment_error": 3.994585459594383, "completed_environment": 4, "difference": 3.4911361243234444, "reference_environment_error": 0.5034493352709385}}
case_002 peaks=200,severity=1.0,period=5000: error=1.792776, deltatarget_3=+0.023983, deltatarget_5=-0.014862; interval-end error=1.0825097150055882; incomplete responses=0.
Measured population behavior: {"additions": 0, "mean_neutral_count_per_subswarm_update": 4.035545593840621, "neutral_count_sum": 318683, "no_change_requests": 3774, "policy_calls": 3881, "population_decisions": 3881, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 76162, "5": 2807, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 54], "recorded_total_particle_count_range": [6, 272], "removals": 107, "requested_target_histogram": {"2": 0, "3": 0, "4": 3881, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 78969, "trace_mean_sampling": "Regular samples every 100 counted objective evaluations; first-query extra sample excluded", "trace_sampled_mean_swarm_count": 39.3992, "trace_sampled_mean_total_particle_count": 197.9148}
Query shares: {"birth": 0.003816, "detection": 0.157938, "exclusion": 0.003912, "initialization": 1.2e-05, "memory": 0.039024, "ordinary": 0.606314, "permanent_quantum": 0.157936, "temporary_quantum": 0.031048}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 2.436275087261907, "completed_environment": 14, "difference": -3.318131765470334, "reference_environment_error": 5.754406852732241}, "most_unfavorable": {"candidate_environment_error": 2.5274873236979394, "completed_environment": 96, "difference": 1.660766137906728, "reference_environment_error": 0.8667211857912114}}
Observed episodes versus target_3: {"most_favorable": {"candidate_environment_error": 1.8711066483071253, "completed_environment": 97, "difference": -1.7610702956636117, "reference_environment_error": 3.632176943970737}, "most_unfavorable": {"candidate_environment_error": 3.1170715436735836, "completed_environment": 32, "difference": 2.1154753784005282, "reference_environment_error": 1.0015961652730554}}
case_003 peaks=200,severity=1.0,period=5000: error=2.347646, deltatarget_3=+0.215266, deltatarget_5=+0.059992; interval-end error=1.4583419523457464; incomplete responses=0.
Measured population behavior: {"additions": 0, "mean_neutral_count_per_subswarm_update": 4.040079551068493, "neutral_count_sum": 318936, "no_change_requests": 3744, "policy_calls": 3855, "population_decisions": 3855, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 75779, "5": 3164, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 57], "recorded_total_particle_count_range": [6, 286], "removals": 111, "requested_target_histogram": {"2": 0, "3": 0, "4": 3855, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 78943, "trace_mean_sampling": "Regular samples every 100 counted objective evaluations; first-query extra sample excluded", "trace_sampled_mean_swarm_count": 39.2018, "trace_sampled_mean_total_particle_count": 196.9662}
Query shares: {"birth": 0.003888, "detection": 0.157886, "exclusion": 0.003684, "initialization": 1.2e-05, "memory": 0.038772, "ordinary": 0.607032, "permanent_quantum": 0.157886, "temporary_quantum": 0.03084}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 1.91432148003634, "completed_environment": 14, "difference": -4.190475329217659, "reference_environment_error": 6.104796809253998}, "most_unfavorable": {"candidate_environment_error": 4.600907765157836, "completed_environment": 42, "difference": 3.8561068024748884, "reference_environment_error": 0.7448009626829477}}
Observed episodes versus target_3: {"most_favorable": {"candidate_environment_error": 0.7074777120508212, "completed_environment": 71, "difference": -3.698731233411594, "reference_environment_error": 4.406208945462415}, "most_unfavorable": {"candidate_environment_error": 6.323582288525097, "completed_environment": 31, "difference": 5.2607436033716, "reference_environment_error": 1.0628386851534968}}
Paired regime summary: {"best_tested_fixed_target": "target_3", "cases": 4, "mean_offline_error": 2.181442892162108, "regime": "peaks=200,severity=1.0,period=5000", "target_3_difference_sd": 0.08957360551429902, "target_3_mean_difference": 0.08984961918770112, "target_5_difference_sd": 0.2947872793082829, "target_5_mean_difference": -0.009840310292215493}
Influential cases versus target_3: best={"case_id": "case_002", "offline_error": 1.792776358155414, "paired_differences": {"target_3": 0.02398313774726968, "target_5": -0.014862283324037495}}; worst={"case_id": "case_003", "offline_error": 2.3476457762368925, "paired_differences": {"target_3": 0.21526634341674988, "target_5": 0.05999194914714456}}
Influential cases versus target_5: best={"case_id": "case_000", "offline_error": 2.34992103906504, "paired_differences": {"target_3": 0.0934618353086405, "target_5": -0.39840319161372273}}; worst={"case_id": "case_001", "offline_error": 2.2354283951910854, "paired_differences": {"target_3": 0.02668716027814444, "target_5": 0.3139122846217537}}
The chapter suggests adaptive particles within subswarms as future work. This task tests allocation within groups without particle transfer or conserved global population. More trajectories, slower update cycling, convergence changes, memory quality and random closed-loop variation are competing explanations. Fixed targets do not exhaust all constants. Constants remain legitimate; complexity and population variability receive no reward. Every case uses the registered full 500000-query development horizon. Subswarm count does not directly measure distinct peak coverage. No protected outcome is supplied.

```python
"""Reconstructed MPSO 5+1: maintain five neutral particles."""

# EVOLVE-BLOCK-START
def choose_neutral_count(observation) -> int:
    return 3
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.32
mean_offline_error: 2.09; worst_case_offline_error: 2.26; case_error_std: 0.22; cases_completed: 4

Text feedback:
Four reused DEVELOPMENT histories under the corrected enclosing-ball engine, each five-dimensional with 200 conical peaks, severity 1, change period 5000, correlation 0 and nexcess 1. These same cases are reused throughout selection; no fresh comparison outcome is supplied. Lower offline error is better; fitness=1/(1+mean error). Paired differences are candidate minus comparator (negative is better). Target 5 is the reconstructed chapter 5+1 and native seed. Fixed targets 3 and 5 start at five and resize by at most one per detected event using exactly the same adapter. Best tested fixed target by development mean (numeric target breaks ties): target_3. Only neutral population targets change. Every current neutral quantum-samples on detected change, otherwise uses ordinary PSO; one permanent quantum particle always samples. Whole trajectories, convergence/birth timing and later random draws can diverge. Available public workload fields are swarm_count and total_particle_count; previous_requested_target supplies the preceding target for the same subswarm. The policy may use these fields but need not branch or vary population.
case_000 peaks=200,severity=1.0,period=5000: error=2.256459, deltatarget_3=+0.000000, deltatarget_5=-0.491865; interval-end error=1.3687752481883848; incomplete responses=0.
Measured population behavior: {"additions": 0, "mean_neutral_count_per_subswarm_update": 3.100491238516502, "neutral_count_sum": 291595, "no_change_requests": 3700, "policy_calls": 3882, "population_decisions": 3882, "realized_neutral_count_histogram": {"2": 0, "3": 87917, "4": 2811, "5": 3320, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 56], "recorded_total_particle_count_range": [6, 228], "removals": 182, "requested_target_histogram": {"2": 0, "3": 3882, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 94048, "trace_mean_sampling": "Regular samples every 100 counted objective evaluations; first-query extra sample excluded", "trace_sampled_mean_swarm_count": 39.5024, "trace_sampled_mean_total_particle_count": 160.6978}
Query shares: {"birth": 0.00384, "detection": 0.188096, "exclusion": 0.005112, "initialization": 1.2e-05, "memory": 0.031654, "ordinary": 0.559664, "permanent_quantum": 0.188096, "temporary_quantum": 0.023526}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 2.800267424347734, "completed_environment": 6, "difference": -7.515784280599711, "reference_environment_error": 10.316051704947444}, "most_unfavorable": {"candidate_environment_error": 3.5607528725685627, "completed_environment": 81, "difference": 2.599706348632061, "reference_environment_error": 0.9610465239365018}}
Observed episodes versus target_3: {"most_favorable": {"candidate_environment_error": 9.865756478874337, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 9.865756478874337}, "most_unfavorable": {"candidate_environment_error": 9.865756478874337, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 9.865756478874337}}
case_001 peaks=200,severity=1.0,period=5000: error=2.208741, deltatarget_3=+0.000000, deltatarget_5=+0.287225; interval-end error=1.429258795644731; incomplete responses=0.
Measured population behavior: {"additions": 0, "mean_neutral_count_per_subswarm_update": 3.1126910582095118, "neutral_count_sum": 292235, "no_change_requests": 3823, "policy_calls": 4013, "population_decisions": 4013, "realized_neutral_count_histogram": {"2": 0, "3": 87026, "4": 3138, "5": 3721, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 62], "recorded_total_particle_count_range": [6, 251], "removals": 190, "requested_target_histogram": {"2": 0, "3": 4013, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 93885, "trace_mean_sampling": "Regular samples every 100 counted objective evaluations; first-query extra sample excluded", "trace_sampled_mean_swarm_count": 40.8412, "trace_sampled_mean_total_particle_count": 166.2194}
Query shares: {"birth": 0.003564, "detection": 0.18777, "exclusion": 0.003696, "initialization": 1.2e-05, "memory": 0.032724, "ordinary": 0.560148, "permanent_quantum": 0.187768, "temporary_quantum": 0.024318}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 1.682828159849046, "completed_environment": 62, "difference": -1.6892161584535688, "reference_environment_error": 3.3720443183026148}, "most_unfavorable": {"candidate_environment_error": 13.968353035725569, "completed_environment": 2, "difference": 10.931850956701222, "reference_environment_error": 3.0365020790243475}}
Observed episodes versus target_3: {"most_favorable": {"candidate_environment_error": 7.774793536706052, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 7.774793536706052}, "most_unfavorable": {"candidate_environment_error": 7.774793536706052, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 7.774793536706052}}
case_002 peaks=200,severity=1.0,period=5000: error=1.768793, deltatarget_3=+0.000000, deltatarget_5=-0.038845; interval-end error=1.0896625242572944; incomplete responses=0.
Measured population behavior: {"additions": 0, "mean_neutral_count_per_subswarm_update": 3.099064843217451, "neutral_count_sum": 290965, "no_change_requests": 4108, "policy_calls": 4291, "population_decisions": 4291, "realized_neutral_count_histogram": {"2": 0, "3": 87801, "4": 2873, "5": 3214, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 64], "recorded_total_particle_count_range": [6, 259], "removals": 183, "requested_target_histogram": {"2": 0, "3": 4291, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 93888, "trace_mean_sampling": "Regular samples every 100 counted objective evaluations; first-query extra sample excluded", "trace_sampled_mean_swarm_count": 43.694, "trace_sampled_mean_total_particle_count": 177.493}
Query shares: {"birth": 0.003804, "detection": 0.187776, "exclusion": 0.003792, "initialization": 1.2e-05, "memory": 0.034912, "ordinary": 0.555966, "permanent_quantum": 0.187774, "temporary_quantum": 0.025964}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 3.019275267706303, "completed_environment": 14, "difference": -2.735131585025938, "reference_environment_error": 5.754406852732241}, "most_unfavorable": {"candidate_environment_error": 3.3505044463824984, "completed_environment": 46, "difference": 1.7219498498180033, "reference_environment_error": 1.6285545965644952}}
Observed episodes versus target_3: {"most_favorable": {"candidate_environment_error": 5.256110653105504, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 5.256110653105504}, "most_unfavorable": {"candidate_environment_error": 5.256110653105504, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 5.256110653105504}}
case_003 peaks=200,severity=1.0,period=5000: error=2.132379, deltatarget_3=+0.000000, deltatarget_5=-0.155274; interval-end error=1.281774004484304; incomplete responses=0.
Measured population behavior: {"additions": 0, "mean_neutral_count_per_subswarm_update": 3.106849839847616, "neutral_count_sum": 291960, "no_change_requests": 3792, "policy_calls": 3974, "population_decisions": 3974, "realized_neutral_count_histogram": {"2": 0, "3": 87503, "4": 2899, "5": 3571, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 60], "recorded_total_particle_count_range": [6, 244], "removals": 182, "requested_target_histogram": {"2": 0, "3": 3974, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 93973, "trace_mean_sampling": "Regular samples every 100 counted objective evaluations; first-query extra sample excluded", "trace_sampled_mean_swarm_count": 40.4298, "trace_sampled_mean_total_particle_count": 164.4278}
Query shares: {"birth": 0.003804, "detection": 0.187946, "exclusion": 0.003996, "initialization": 1.2e-05, "memory": 0.03238, "ordinary": 0.55985, "permanent_quantum": 0.187944, "temporary_quantum": 0.024068}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 0.6822339481453827, "completed_environment": 10, "difference": -5.05045208304688, "reference_environment_error": 5.732686031192263}, "most_unfavorable": {"candidate_environment_error": 5.782123813565763, "completed_environment": 30, "difference": 3.9380575630494823, "reference_environment_error": 1.8440662505162804}}
Observed episodes versus target_3: {"most_favorable": {"candidate_environment_error": 9.88605586334042, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 9.88605586334042}, "most_unfavorable": {"candidate_environment_error": 9.88605586334042, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 9.88605586334042}}
Paired regime summary: {"best_tested_fixed_target": "target_3", "cases": 4, "mean_offline_error": 2.0915932729744067, "regime": "peaks=200,severity=1.0,period=5000", "target_3_difference_sd": 0.0, "target_3_mean_difference": 0.0, "target_5_difference_sd": 0.32160858863878616, "target_5_mean_difference": -0.09968992947991662}
Influential cases versus target_3: best={"case_id": "case_000", "offline_error": 2.2564592037563993, "paired_differences": {"target_3": 0.0, "target_5": -0.4918650269223632}}; worst={"case_id": "case_003", "offline_error": 2.1323794328201426, "paired_differences": {"target_3": 0.0, "target_5": -0.15527439426960532}}
Influential cases versus target_5: best={"case_id": "case_000", "offline_error": 2.2564592037563993, "paired_differences": {"target_3": 0.0, "target_5": -0.4918650269223632}}; worst={"case_id": "case_001", "offline_error": 2.208741234912941, "paired_differences": {"target_3": 0.0, "target_5": 0.28722512434360925}}
The chapter suggests adaptive particles within subswarms as future work. This task tests allocation within groups without particle transfer or conserved global population. More trajectories, slower update cycling, convergence changes, memory quality and random closed-loop variation are competing explanations. Fixed targets do not exhaust all constants. Constants remain legitimate; complexity and population variability receive no reward. Every case uses the registered full 500000-query development horizon. Subswarm count does not directly measure distinct peak coverage. No protected outcome is supplied.


# Current program

Here is the current program we are trying to improve (you will need to propose a new program with the same inputs and outputs as the original program, but with improved internal implementation):

```python
"""Reconstructed MPSO 5+1: maintain five neutral particles."""

# EVOLVE-BLOCK-START
def choose_neutral_count(observation) -> int:
    return 2
# EVOLVE-BLOCK-END

```

Here are the performance metrics of the program:

Combined score to maximize: 0.32
mean_offline_error: 2.08; worst_case_offline_error: 2.29; case_error_std: 0.26; cases_completed: 4

Here is additional text feedback about the current program:

Four reused DEVELOPMENT histories under the corrected enclosing-ball engine, each five-dimensional with 200 conical peaks, severity 1, change period 5000, correlation 0 and nexcess 1. These same cases are reused throughout selection; no fresh comparison outcome is supplied. Lower offline error is better; fitness=1/(1+mean error). Paired differences are candidate minus comparator (negative is better). Target 5 is the reconstructed chapter 5+1 and native seed. Fixed targets 3 and 5 start at five and resize by at most one per detected event using exactly the same adapter. Best tested fixed target by development mean (numeric target breaks ties): target_3. Only neutral population targets change. Every current neutral quantum-samples on detected change, otherwise uses ordinary PSO; one permanent quantum particle always samples. Whole trajectories, convergence/birth timing and later random draws can diverge. Available public workload fields are swarm_count and total_particle_count; previous_requested_target supplies the preceding target for the same subswarm. The policy may use these fields but need not branch or vary population.
case_000 peaks=200,severity=1.0,period=5000: error=2.290227, deltatarget_3=+0.033768, deltatarget_5=-0.458097; interval-end error=1.3987834015850136; incomplete responses=0.
Measured population behavior: {"additions": 0, "mean_neutral_count_per_subswarm_update": 2.1786234018225286, "neutral_count_sum": 251509, "no_change_requests": 3936, "policy_calls": 4197, "population_decisions": 4197, "realized_neutral_count_histogram": {"2": 105497, "3": 2952, "4": 3316, "5": 3679, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 61], "recorded_total_particle_count_range": [6, 188], "removals": 261, "requested_target_histogram": {"2": 4197, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 115444, "trace_mean_sampling": "Regular samples every 100 counted objective evaluations; first-query extra sample excluded", "trace_sampled_mean_swarm_count": 42.6636, "trace_sampled_mean_total_particle_count": 133.204}
Query shares: {"birth": 0.003756, "detection": 0.230888, "exclusion": 0.005124, "initialization": 1.2e-05, "memory": 0.026316, "ordinary": 0.485618, "permanent_quantum": 0.230886, "temporary_quantum": 0.0174}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 2.312887940916403, "completed_environment": 6, "difference": -8.003163764031042, "reference_environment_error": 10.316051704947444}, "most_unfavorable": {"candidate_environment_error": 5.471891495432558, "completed_environment": 28, "difference": 4.361563201145347, "reference_environment_error": 1.1103282942872115}}
Observed episodes versus target_3: {"most_favorable": {"candidate_environment_error": 3.5153468874376825, "completed_environment": 11, "difference": -5.120441517007545, "reference_environment_error": 8.635788404445227}, "most_unfavorable": {"candidate_environment_error": 5.471891495432558, "completed_environment": 28, "difference": 3.595361523914867, "reference_environment_error": 1.8765299715176913}}
case_001 peaks=200,severity=1.0,period=5000: error=2.050520, deltatarget_3=-0.158221, deltatarget_5=+0.129004; interval-end error=1.3535207786345584; incomplete responses=0.
Measured population behavior: {"additions": 0, "mean_neutral_count_per_subswarm_update": 2.1985395869415747, "neutral_count_sum": 252610, "no_change_requests": 3938, "policy_calls": 4204, "population_decisions": 4204, "realized_neutral_count_histogram": {"2": 104035, "3": 3131, "4": 3518, "5": 4215, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 61], "recorded_total_particle_count_range": [6, 189], "removals": 266, "requested_target_histogram": {"2": 4204, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 114899, "trace_mean_sampling": "Regular samples every 100 counted objective evaluations; first-query extra sample excluded", "trace_sampled_mean_swarm_count": 42.6356, "trace_sampled_mean_total_particle_count": 133.2852}
Query shares: {"birth": 0.004092, "detection": 0.229798, "exclusion": 0.00468, "initialization": 1.2e-05, "memory": 0.0264, "ordinary": 0.48776, "permanent_quantum": 0.229798, "temporary_quantum": 0.01746}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 0.8593736863118705, "completed_environment": 66, "difference": -3.6089482510993416, "reference_environment_error": 4.468321937411212}, "most_unfavorable": {"candidate_environment_error": 13.968353035725569, "completed_environment": 2, "difference": 10.931850956701222, "reference_environment_error": 3.0365020790243475}}
Observed episodes versus target_3: {"most_favorable": {"candidate_environment_error": 0.8593736863118705, "completed_environment": 66, "difference": -3.5226025156807608, "reference_environment_error": 4.381976201992631}, "most_unfavorable": {"candidate_environment_error": 2.640107192219205, "completed_environment": 16, "difference": 2.068398962258657, "reference_environment_error": 0.5717082299605483}}
case_002 peaks=200,severity=1.0,period=5000: error=1.723802, deltatarget_3=-0.044991, deltatarget_5=-0.083837; interval-end error=1.032564263198371; incomplete responses=0.
Measured population behavior: {"additions": 0, "mean_neutral_count_per_subswarm_update": 2.183397817374256, "neutral_count_sum": 251689, "no_change_requests": 4100, "policy_calls": 4371, "population_decisions": 4371, "realized_neutral_count_histogram": {"2": 105092, "3": 3026, "4": 3353, "5": 3803, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 67], "recorded_total_particle_count_range": [6, 207], "removals": 271, "requested_target_histogram": {"2": 4371, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 115274, "trace_mean_sampling": "Regular samples every 100 counted objective evaluations; first-query extra sample excluded", "trace_sampled_mean_swarm_count": 44.4104, "trace_sampled_mean_total_particle_count": 138.7056}
Query shares: {"birth": 0.00372, "detection": 0.230548, "exclusion": 0.004404, "initialization": 1.2e-05, "memory": 0.027396, "ordinary": 0.485262, "permanent_quantum": 0.230546, "temporary_quantum": 0.018112}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 1.383506757928668, "completed_environment": 14, "difference": -4.370900094803573, "reference_environment_error": 5.754406852732241}, "most_unfavorable": {"candidate_environment_error": 3.2172606650919513, "completed_environment": 34, "difference": 1.8315018998297115, "reference_environment_error": 1.3857587652622398}}
Observed episodes versus target_3: {"most_favorable": {"candidate_environment_error": 1.141165297736576, "completed_environment": 17, "difference": -1.7251681158404655, "reference_environment_error": 2.8663334135770415}, "most_unfavorable": {"candidate_environment_error": 3.2172606650919513, "completed_environment": 34, "difference": 2.107940815580077, "reference_environment_error": 1.1093198495118743}}
case_003 peaks=200,severity=1.0,period=5000: error=2.257017, deltatarget_3=+0.124637, deltatarget_5=-0.030637; interval-end error=1.3783620736906175; incomplete responses=0.
Measured population behavior: {"additions": 0, "mean_neutral_count_per_subswarm_update": 2.1951681256078923, "neutral_count_sum": 252778, "no_change_requests": 3744, "policy_calls": 4007, "population_decisions": 4007, "realized_neutral_count_histogram": {"2": 104630, "3": 2895, "4": 3302, "5": 4325, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 61], "recorded_total_particle_count_range": [6, 192], "removals": 263, "requested_target_histogram": {"2": 4007, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 115152, "trace_mean_sampling": "Regular samples every 100 counted objective evaluations; first-query extra sample excluded", "trace_sampled_mean_swarm_count": 40.7532, "trace_sampled_mean_total_particle_count": 127.6388}
Query shares: {"birth": 0.004332, "detection": 0.230304, "exclusion": 0.004284, "initialization": 1.2e-05, "memory": 0.02521, "ordinary": 0.488886, "permanent_quantum": 0.230302, "temporary_quantum": 0.01667}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 0.9050248546730998, "completed_environment": 10, "difference": -4.827661176519164, "reference_environment_error": 5.732686031192263}, "most_unfavorable": {"candidate_environment_error": 5.287541876338801, "completed_environment": 45, "difference": 3.9010617495762316, "reference_environment_error": 1.3864801267625688}}
Observed episodes versus target_3: {"most_favorable": {"candidate_environment_error": 0.8209002537451539, "completed_environment": 75, "difference": -2.6186031279936186, "reference_environment_error": 3.4395033817387723}, "most_unfavorable": {"candidate_environment_error": 6.561003900890927, "completed_environment": 28, "difference": 3.7507468533294, "reference_environment_error": 2.8102570475615267}}
Paired regime summary: {"best_tested_fixed_target": "target_3", "cases": 4, "mean_offline_error": 2.0803915162058892, "regime": "peaks=200,severity=1.0,period=5000", "target_3_difference_sd": 0.12004313255126935, "target_3_mean_difference": -0.011201756768517646, "target_5_difference_sd": 0.24851156168622218, "target_5_mean_difference": -0.11089168624843426}
Influential cases versus target_3: best={"case_id": "case_001", "offline_error": 2.0505198204988146, "paired_differences": {"target_3": -0.1582214144141263, "target_5": 0.12900370992948296}}; worst={"case_id": "case_003", "offline_error": 2.257016770916077, "paired_differences": {"target_3": 0.12463733809593425, "target_5": -0.030637056173671073}}
Influential cases versus target_5: best={"case_id": "case_000", "offline_error": 2.290227412850835, "paired_differences": {"target_3": 0.033768209094435786, "target_5": -0.45809681782792744}}; worst={"case_id": "case_001", "offline_error": 2.0505198204988146, "paired_differences": {"target_3": -0.1582214144141263, "target_5": 0.12900370992948296}}
The chapter suggests adaptive particles within subswarms as future work. This task tests allocation within groups without particle transfer or conserved global population. More trajectories, slower update cycling, convergence changes, memory quality and random closed-loop variation are competing explanations. Fixed targets do not exhaust all constants. Constants remain legitimate; complexity and population variability receive no reward. Every case uses the registered full 500000-query development horizon. Subswarm count does not directly measure distinct peak coverage. No protected outcome is supplied.


# Task

Rewrite the program to improve its performance on the specified metrics.
Provide the complete new program code.

IMPORTANT: Make sure your rewritten program maintains the same inputs and outputs as the original program, but with improved internal implementation.
