# System Instructions

You are an expert programming assistant analyzing an individual program. Create a standalone summary focusing on implementation details and evaluation feedback. Consider how this specific program performs and what implementation choices were made.

# Previous Messages

[]

# User Request

# Program to Analyze
# Program to Analyze

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

Performance metrics:
Combined score to maximize: 0.36
mean_offline_error: 1.81; worst_case_offline_error: 2.42; case_error_std: 0.53; cases_completed: 8

The program is correct and passes all validation tests.

Text feedback:
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

Create a standalone summary for this program using the following exact format:

**Program Name: [Short summary name of the algorithm (up to 10 words)]**
- **Implementation**: [Key implementation details (1-2 sentences)]
- **Performance**: [Score/metrics summary (1 sentence)]
- **Feedback**: [Key insights from evaluation (1-2 sentences)]

Focus on:
1. What specific implementation details were done
2. How these details affected performance
3. Implementation details that are relevant to the approach
4. Any evaluation feedback that provides insights

Keep the program summary concise but informative. Follow the format exactly.
