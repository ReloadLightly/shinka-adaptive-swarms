# System Instructions

You are an expert programming assistant generating actionable recommendations for future program mutations based on successful patterns and insights.

# Previous Messages

[]

# User Request

# Global Insights
## Successful Algorithmic Patterns
- **Workload-Adjusted Neutral Population Hysteresis is the strongest evaluated program:** score **0.3414**, mean error **1.9287**. Its combined loss, workload, and previous-target rule reduces mean error by **12.0% versus Fixed Five**, **7.8% versus Fixed Three**, and **7.3% versus Fixed Two**. These results support the complete policy; they do not isolate each component’s contribution.
- **Smaller constant populations improved development performance.** Fixed Three raised the baseline score from **0.3134 to 0.3235**, reducing mean error by **0.09969**. Fixed Two improved further to **0.3246**, although its additional mean-error reduction was only **0.01120**.
- **The best policy actively uses both targets.** It requested three on **36.7%** of decisions and two on **63.3%**, with **1,582 additions and 2,503 removals** across four cases. Its realized mean population of **2.55–2.57 neutrals** accompanied lower error than either constant endpoint.
## Ineffective Approaches
- **Fixed Four provided little benefit over Fixed Five.** Its score was **0.3143**, with mean error only **0.00984** below the baseline. It was worse than Fixed Three in every case, averaging **0.08985** more error. Retaining that additional neutral did not yield a compensating performance benefit in these histories; the specific causal pathway remains unresolved.
- **Unconditional shrinking to two had a reliability tradeoff.** Compared with Fixed Three, Fixed Two slightly improved mean error but increased worst-case error from **2.2565 to 2.2902** and case-error standard deviation from **0.2212 to 0.2603**. Smaller populations therefore did not improve every performance measure.
## Implementation Insights
- **The best policy raises the loss threshold as workload grows.** With `W = total_particle_count + max(1, swarm_count)`, it requests three when nonnegative relative loss exceeds `threshold × (1 + W/160)`. Thus, the same observed deterioration is less likely to trigger growth when existing movement and detection workload is greater.
- **Previous-target feedback creates explicit hysteresis.** Adjusted loss must exceed **0.08** to enter target three, but only **0.04** to retain it. Between those thresholds, the previous request determines the result. This creates persistence without mutable internal state, although reduced switching was not independently measured against a policy without hysteresis.
- **Requested targets differ from realized populations.** The adapter starts swarms at five and changes population by at most one after detected change and memory refresh. Consequently, the best policy still realizes four- and five-neutral populations during transitions. Constant policies also exhibit population variation through this mechanism; their stale five-neutral docstrings do not describe their executed requests.
- **Population changes affect several budgeted operations.** For the best policy, ordinary movement consumed approximately **53%** of queries, detection **21.2%**, and permanent quantum sampling **21.2%**. The workload estimate captures routine movement and detection, but omits additional memory, birth, and exclusion costs. These shares describe execution, not isolated causes of improvement.
## Performance Analysis
| Program | Score ↑ | Mean error ↓ | Worst-case error ↓ | Case-error SD ↓ |
|---|---:|---:|---:|---:|
| Fixed Five-Neutral Baseline | 0.3134 | 2.1913 | 2.7483 | 0.4241 |
| Fixed Three-Neutral | 0.3235 | 2.0916 | 2.2565 | 0.2212 |
| Fixed Two-Neutral | 0.3246 | 2.0804 | 2.2902 | 0.2603 |
| Fixed Four-Neutral | 0.3143 | 2.1814 | 2.3499 | 0.2646 |
| **Workload-Adjusted Hysteresis** | **0.3414** | **1.9287** | **2.1535** | **0.2081** |
- **The best policy leads on every reported error summary.** Saved case results also show it beats Fixed Two, Three, and Four in all four cases. Against Fixed Five, it wins three cases and loses case_001 by **0.01767**.
- **Fixed Two is the strongest evaluated constant by mean error.** The feedback’s `best_tested_fixed_target: target_3` label describes its comparator set; it does not incorporate the better generation-two constant into that label.
- **Aggregate gains coexist with substantial episode regressions.** The best policy’s case_003/environment_31 error exceeded Fixed Three by **5.4574**; case_001/environment_2 exceeded Fixed Five by **10.9319**. Its lower worst-case whole-history error does not imply uniformly better recovery.
- **Evidence remains development-only.** All programs passed validation under the same corrected engine and four reused 500,000-query histories. The findings establish observed selection performance, without establishing fresh-case generalization, superiority over every constant, or a causal advantage specifically attributable to hysteresis.

# Previous Recommendations (if any)
*No previous recommendations available.*

# Current Best Program
# Program to Analyze

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

The program is correct and passes all validation tests.

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
