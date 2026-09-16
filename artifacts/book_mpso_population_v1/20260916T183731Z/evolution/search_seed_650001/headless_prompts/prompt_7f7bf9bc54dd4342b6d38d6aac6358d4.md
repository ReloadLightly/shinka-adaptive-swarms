# System Instructions

You are an expert programming assistant generating actionable recommendations for future program mutations based on successful patterns and insights.

# Previous Messages

[]

# User Request

# Global Insights
**Successful Algorithmic Patterns**
- **Fixed Five-Neutral MPSO remains best:** `return 5` scores **0.364356**, with mean error **1.744569**, worst-case error **2.270948**, and case-error SD **0.485328**. It preserves five neutrals, change-triggered quantum sampling, and one permanent quantum particle. No evaluated mutation improves its mean.
- **Fixed Six-Neutral-Particle MPSO is now the strongest descendant**, replacing compact four-or-five in that position. Its score **0.360216** and mean error **1.776112** improve on compact shrinking by **0.032146** mean error, but remain **0.031543 worse than fixed five**. It also beats fixed targets three and seven by **0.030228** and **0.095545**, respectively.
- **Compact shrinking remains the strongest conditional policy.** Requesting four only for compact, slow swarms with nonpositive fitness drop improved fixed four’s score from **0.327586 to 0.356093**, reducing mean error by **0.244379**. Conditional shrinking recovered much of unconditional shrinking’s deficit without surpassing fixed five.
**Ineffective Approaches**
- **Generation 5’s Loss-Triggered Neutral Population Adjustment loses despite winning 5/8 cases.** Shrinking after substantial refreshed fitness loss scores **0.340052**, with mean error **1.940724**, **11.24% above fixed five**. Its **case_004 regression of +1.430292** accounts for approximately **91% of the net error increase**; excluding that case still leaves mean error **0.019850 higher**.
- **Reversing the loss-triggered action did not establish a useful trigger.** Generation 5 requests four where generation 3 requested six under the same predicate. Shrinking slightly improves expansion’s score, **0.338652 → 0.340052**, but both trail fixed five substantially. Their largest case regressions differ: expansion loses **1.431403** on case_002, while shrinking loses **1.430292** on case_004.
- **Neither unconditional reduction nor stricter improvement gating worked well.** Fixed four loses **7/8 cases**, with mean error **2.052637**. Restricting compact shrinking to `relative_fitness_drop ≤ -0.05` scores **0.332414**, below the broader compact policy’s **0.356093**. Staying closer to five particles did not reliably preserve performance.
**Implementation Insights**
- **Fixed five makes resizing a no-op.** Subswarms start at five neutrals, so the winning function causes zero additions or removals and preserves the reconstructed baseline trajectory. Its exact target-five match comes from certified archive reuse, with derived population diagnostics; it supplies no independent replication or evolutionary improvement.
- **Targets differ from realized populations.** Decisions occur after detected change and counted memory refresh, with at most one addition or removal. Fixed six therefore averages **5.84–5.88** neutrals, while generation 5 averages **4.38–4.47**. Shrinking removes the worst refreshed neutral memory; additions first evaluate through quantum sampling. Fixed six’s executable `return 6` determines behavior despite its stale five-particle docstring.
- **The fitness predicates measure different events.** Compact shrinking and selective shrinking use reevaluation of the previously remembered best. Generations 3 and 5 compare previous fitness with the best recovered after all memory refreshes. Consequently, their “loss” conditions cannot be interpreted as interchangeable thresholds.
- **Population changes redistribute queries without a monotonic performance benefit.** Ordinary-search shares are **63.61%** for fixed four, **65.04%** for generation 5, **67.51%** for fixed five, and **70.49%** for fixed six. Fixed six reduces detection’s share to **12.19%**, versus **13.67%** for fixed five, yet has higher error. These allocations accompany changes in trajectories, update cycling, and convergence; they do not isolate causation.
**Performance Analysis**
- **Rounded scores conceal meaningful ordering:** fixed five **0.364356**, fixed six **0.360216**, and compact shrinking **0.356093** all display **0.36**. Their mean errors are **1.744569**, **1.776112**, and **1.808258**, respectively.
- **Fixed five retains the lowest observed worst-case error and variability.** Fixed six approaches it at worst-case error **2.277798** and SD **0.519281**; generation 5 is substantially worse at **3.334226** and **0.718831**.
- **Case sensitivity remains substantial.** Fixed six beats fixed five in only **3/8 cases**. Its **+0.609107** regression on case_007 reverses the aggregate ranking: excluding that case gives fixed six a **0.050966** mean advantage. Conversely, generation 5’s majority of case wins fails to offset its larger losses.
- **The evidence establishes a development ranking only.** All seven programs passed validation on eight reused cases, each using **500,000 queries**, severity **1**, and period **5,000**. Execution correctness is established; adaptive superiority, held-out generalization, and optimality across all constant targets are not.

# Previous Recommendations (if any)
1. **Refine the strongest compact-swarm rule.** Keep five as the default and retain `fitness_drop <= 0`; try tightening either `mean_neutral_distance_to_best` or `mean_neutral_speed` from `r` to `0.5*r`, separately, where `r = max(default_radius, 1e-12)`. This extends the strongest descendant’s geometry conditions without repeating the unsuccessful `relative_fitness_drop <= -0.05` restriction; tighter conditions remain hypotheses, not guaranteed improvements.
2. **Limit shrinking to one detected-change interval.** Add `if observation["neutral_count"] < 5: return 5` before the compact rule, allowing a reduction only when five neutrals are present. This restores five at the next detected event and tests whether temporary reductions can retain benefits without the sustained smaller population associated with fixed four’s regression.
3. **Protect particles while the swarm is making progress.** Extend the compact rule to return four only when `recent_improvement <= 0` and `mean_velocity_alignment_to_best <= 0`; otherwise return five. These available signals distinguish compact swarms with stalled or misdirected motion from compact swarms still improving, although their predictive value remains untested.
4. **Try the unexplored neighboring constant `return 6`.** Fixed five’s lead supports keeping simple population targets competitive, and the tested constants do not establish its optimality. Constant six also differs materially from loss-triggered expansion: it maintains the target across detected events instead of repeatedly switching between five and six.
5. **Explore tightly bounded expansion under low swarm load.** As a lower-priority mutation, request six only when `swarm_count <= 2`, normalized loss after memory refresh exceeds `0.05`, `recent_improvement <= 0`, and `neutral_diameter > 2*r`; otherwise request five, including whenever six neutrals are already present. This tests a dispersed, stalled swarm with few competing subswarms, distinct from the unsuccessful compact-swarm expansion, while limiting expansion to one detected-change interval.

# Current Best Program
# Program to Analyze

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

The program is correct and passes all validation tests.

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



# Instructions

Based on the global insights above and the current best program, generate 5 actionable recommendations for future program mutations. Each recommendation should be:

1. **Specific**: Clear about what to implement or try
2. **Actionable**: Something that can be directly applied
3. **Evidence-based**: Grounded in the successful patterns identified
4. **Diverse**: Cover different types of optimizations
5. **Best-program informed**: Consider what makes the current best program successful

Format as a numbered list:

1. [Specific recommendation based on successful patterns]
2. [Another recommendation focusing on a different aspect]
...

**CRITICAL: Prioritize recommendations that build upon or extend the successful patterns from the current best program. Consider both incremental improvements to the best program's approach and novel variations that could surpass it.**

Focus on the most promising approaches that have shown success in recent evaluations, especially those demonstrated by the best program. Avoid generic advice - provide 2-3 sentences per recommendation. DO NOT RECOMMEND CHANGING THE EVALUATION CODE. ONLY MAKE ALGORITHMIC RECOMMENDATIONS.
