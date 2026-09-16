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
    if observation["relative_fitness_drop"] <= -0.05:
        radius = max(observation["default_radius"], 1e-12)
        if (
            observation["neutral_diameter"] <= 2.0 * radius
            and observation["mean_neutral_distance_to_best"] <= radius
            and observation["mean_neutral_speed"] <= radius
        ):
            return 4
    return 5
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.33
mean_offline_error: 2.01; worst_case_offline_error: 3.35; case_error_std: 0.77; cases_completed: 8

The program is correct and passes all validation tests.

Text feedback:
Reused development cases only. Lower offline error is better; fitness=1/(1+mean error). Paired differences are candidate minus comparator (negative is better). Target5 is the reconstructed chapter5+1 and native seed. Fixed targets3/7 start at five and resize by at most one per detected event using exactly the same adapter. Best tested fixed target by development mean (numeric target breaks ties): target_5. Only neutral population targets change. Every current neutral quantum-samples on detected change, otherwise uses ordinary PSO; one permanent quantum particle always samples. Whole trajectories, convergence/birth timing and later random draws can diverge.
case_000 severity=1.0,period=5000: error=2.151469, deltatarget_3=+0.220740, deltatarget_5=+0.100739, deltatarget_7=-0.217759; interval-end error=1.5167675534910352; incomplete responses=0.
Measured population behavior: {"additions": 66, "mean_neutral_count_per_subswarm_update": 4.896970571263704, "neutral_count_sum": 339458, "no_change_requests": 687, "policy_calls": 820, "population_decisions": 820, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 7142, "5": 62178, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 11], "recorded_total_particle_count_range": [6, 66], "removals": 67, "requested_target_histogram": {"2": 0, "3": 0, "4": 83, "5": 737, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 69320}
Query shares: {"birth": 0.003312, "detection": 0.13864, "exclusion": 0.030816, "initialization": 1.2e-05, "memory": 0.009676, "ordinary": 0.670872, "permanent_quantum": 0.138638, "temporary_quantum": 0.008034}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 0.43892523666658023, "completed_environment": 20, "difference": -4.093391420600904, "reference_environment_error": 4.532316657267484}, "most_unfavorable": {"candidate_environment_error": 13.675910535435664, "completed_environment": 14, "difference": 13.069769992012386, "reference_environment_error": 0.6061405434232772}}
case_001 severity=1.0,period=5000: error=2.085072, deltatarget_3=+0.062904, deltatarget_5=-0.147573, deltatarget_7=-0.506124; interval-end error=1.2513042648598394; incomplete responses=0.
Measured population behavior: {"additions": 74, "mean_neutral_count_per_subswarm_update": 4.904915726304304, "neutral_count_sum": 341647, "no_change_requests": 743, "policy_calls": 892, "population_decisions": 892, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 6623, "5": 63031, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 12], "recorded_total_particle_count_range": [6, 72], "removals": 75, "requested_target_histogram": {"2": 0, "3": 0, "4": 85, "5": 807, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 69654}
Query shares: {"birth": 0.003852, "detection": 0.139308, "exclusion": 0.0237, "initialization": 1.2e-05, "memory": 0.010536, "ordinary": 0.674536, "permanent_quantum": 0.139306, "temporary_quantum": 0.00875}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 1.8376710216025782, "completed_environment": 49, "difference": -7.839115336448383, "reference_environment_error": 9.676786358050961}, "most_unfavorable": {"candidate_environment_error": 6.598435953697312, "completed_environment": 15, "difference": 2.788396118537714, "reference_environment_error": 3.8100398351595977}}
case_002 severity=1.0,period=5000: error=2.079126, deltatarget_3=-0.263002, deltatarget_5=-0.191821, deltatarget_7=+0.157746; interval-end error=1.2428676858775423; incomplete responses=0.
Measured population behavior: {"additions": 45, "mean_neutral_count_per_subswarm_update": 4.93276137850807, "neutral_count_sum": 339226, "no_change_requests": 671, "policy_calls": 761, "population_decisions": 761, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 4624, "5": 64146, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 13], "recorded_total_particle_count_range": [6, 78], "removals": 45, "requested_target_histogram": {"2": 0, "3": 0, "4": 51, "5": 710, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 68770}
Query shares: {"birth": 0.00426, "detection": 0.13754, "exclusion": 0.033168, "initialization": 1.2e-05, "memory": 0.00903, "ordinary": 0.670944, "permanent_quantum": 0.137538, "temporary_quantum": 0.007508}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 3.42654468932546, "completed_environment": 52, "difference": -7.190064418417013, "reference_environment_error": 10.616609107742473}, "most_unfavorable": {"candidate_environment_error": 5.737989895232518, "completed_environment": 44, "difference": 5.497987568048297, "reference_environment_error": 0.2400023271842213}}
case_003 severity=1.0,period=5000: error=0.762090, deltatarget_3=+0.039202, deltatarget_5=-0.085893, deltatarget_7=+0.070737; interval-end error=0.1264909983834574; incomplete responses=0.
Measured population behavior: {"additions": 81, "mean_neutral_count_per_subswarm_update": 4.902850971922247, "neutral_count_sum": 340503, "no_change_requests": 795, "policy_calls": 958, "population_decisions": 958, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 6747, "5": 62703, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 12], "recorded_total_particle_count_range": [6, 72], "removals": 82, "requested_target_histogram": {"2": 0, "3": 0, "4": 96, "5": 862, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 69450}
Query shares: {"birth": 0.003648, "detection": 0.1389, "exclusion": 0.026232, "initialization": 1.2e-05, "memory": 0.011306, "ordinary": 0.671616, "permanent_quantum": 0.138898, "temporary_quantum": 0.009388}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 0.7220728471492478, "completed_environment": 37, "difference": -5.379445200067589, "reference_environment_error": 6.101518047216836}, "most_unfavorable": {"candidate_environment_error": 5.260402071272549, "completed_environment": 30, "difference": 4.471478888711603, "reference_environment_error": 0.7889231825609457}}
case_004 severity=1.0,period=5000: error=3.350493, deltatarget_3=+1.393658, deltatarget_5=+1.446559, deltatarget_7=+1.253686; interval-end error=2.741731200685599; incomplete responses=0.
Measured population behavior: {"additions": 57, "mean_neutral_count_per_subswarm_update": 4.900741386829481, "neutral_count_sum": 337122, "no_change_requests": 593, "policy_calls": 707, "population_decisions": 707, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 6828, "5": 61962, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 9], "recorded_total_particle_count_range": [6, 54], "removals": 57, "requested_target_histogram": {"2": 0, "3": 0, "4": 69, "5": 638, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 68790}
Query shares: {"birth": 0.00324, "detection": 0.13758, "exclusion": 0.039, "initialization": 1.2e-05, "memory": 0.008346, "ordinary": 0.667312, "permanent_quantum": 0.137578, "temporary_quantum": 0.006932}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 0.5681275978528154, "completed_environment": 29, "difference": -0.9820509995630881, "reference_environment_error": 1.5501785974159035}, "most_unfavorable": {"candidate_environment_error": 18.22246959614225, "completed_environment": 35, "difference": 16.757647985947322, "reference_environment_error": 1.4648216101949276}}
case_005 severity=1.0,period=5000: error=1.392977, deltatarget_3=-0.129239, deltatarget_5=+0.097060, deltatarget_7=-0.050892; interval-end error=0.6268942017659566; incomplete responses=0.
Measured population behavior: {"additions": 83, "mean_neutral_count_per_subswarm_update": 4.887057193174929, "neutral_count_sum": 338546, "no_change_requests": 678, "policy_calls": 845, "population_decisions": 845, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 7824, "5": 61450, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 12], "recorded_total_particle_count_range": [6, 72], "removals": 84, "requested_target_histogram": {"2": 0, "3": 0, "4": 99, "5": 746, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 69274}
Query shares: {"birth": 0.003144, "detection": 0.138548, "exclusion": 0.032724, "initialization": 1.2e-05, "memory": 0.009944, "ordinary": 0.66883, "permanent_quantum": 0.138546, "temporary_quantum": 0.008252}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 7.683316499027514, "completed_environment": 43, "difference": -0.8420185649003447, "reference_environment_error": 8.525335063927859}, "most_unfavorable": {"candidate_environment_error": 6.171934584732475, "completed_environment": 33, "difference": 5.772417799716315, "reference_environment_error": 0.39951678501615945}}
case_006 severity=1.0,period=5000: error=2.530683, deltatarget_3=+0.899330, deltatarget_5=+0.844982, deltatarget_7=+0.824308; interval-end error=1.744757860546424; incomplete responses=0.
Measured population behavior: {"additions": 50, "mean_neutral_count_per_subswarm_update": 4.917899075511952, "neutral_count_sum": 338858, "no_change_requests": 627, "policy_calls": 727, "population_decisions": 727, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 5657, "5": 63246, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 11], "recorded_total_particle_count_range": [6, 66], "removals": 50, "requested_target_histogram": {"2": 0, "3": 0, "4": 58, "5": 669, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 68903}
Query shares: {"birth": 0.003636, "detection": 0.137806, "exclusion": 0.034428, "initialization": 1.2e-05, "memory": 0.008608, "ordinary": 0.670552, "permanent_quantum": 0.137804, "temporary_quantum": 0.007154}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 4.921571117845564, "completed_environment": 29, "difference": -1.4702588125934204, "reference_environment_error": 6.391829930438984}, "most_unfavorable": {"candidate_environment_error": 17.330475882107052, "completed_environment": 17, "difference": 11.843538535101501, "reference_environment_error": 5.486937347005552}}
case_007 severity=1.0,period=5000: error=1.714498, deltatarget_3=-0.607906, deltatarget_5=+0.045808, deltatarget_7=-0.438552; interval-end error=0.9018087229503126; incomplete responses=0.
Measured population behavior: {"additions": 74, "mean_neutral_count_per_subswarm_update": 4.9032485367923035, "neutral_count_sum": 340967, "no_change_requests": 763, "policy_calls": 912, "population_decisions": 912, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 6728, "5": 62811, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 12], "recorded_total_particle_count_range": [6, 72], "removals": 75, "requested_target_histogram": {"2": 0, "3": 0, "4": 86, "5": 826, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 69539}
Query shares: {"birth": 0.003384, "detection": 0.139078, "exclusion": 0.025752, "initialization": 1.2e-05, "memory": 0.010774, "ordinary": 0.672976, "permanent_quantum": 0.139076, "temporary_quantum": 0.008948}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 1.292390182737989, "completed_environment": 31, "difference": -3.6934478541262377, "reference_environment_error": 4.9858380368642266}, "most_unfavorable": {"candidate_environment_error": 4.302245503381009, "completed_environment": 47, "difference": 1.50379049890316, "reference_environment_error": 2.798455004477849}}
Paired regime summary: {"best_tested_fixed_target": "target_5", "cases": 8, "mean_offline_error": 2.008301179090116, "regime": "severity=1.0,period=5000", "target_3_difference_sd": 0.6474582076522474, "target_3_mean_difference": 0.20196084181802848, "target_5_difference_sd": 0.5778912285444536, "target_5_mean_difference": 0.2637323975751853, "target_7_difference_sd": 0.6129817162019592, "target_7_mean_difference": 0.13664377138974948}
Influential cases versus target_3: best={"case_id": "case_007", "offline_error": 1.7144984042819829, "paired_differences": {"target_3": -0.6079060730555437, "target_5": 0.045807728139437565, "target_7": -0.43855225160006883}}; worst={"case_id": "case_004", "offline_error": 3.3504930893606475, "paired_differences": {"target_3": 1.3936583356555357, "target_5": 1.4465592289715237, "target_7": 1.253685610371174}}
Influential cases versus target_5: best={"case_id": "case_002", "offline_error": 2.079126450012901, "paired_differences": {"target_3": -0.2630024316716204, "target_5": -0.1918214096093287, "target_7": 0.15774641590810523}}; worst={"case_id": "case_004", "offline_error": 3.3504930893606475, "paired_differences": {"target_3": 1.3936583356555357, "target_5": 1.4465592289715237, "target_7": 1.253685610371174}}
Influential cases versus target_7: best={"case_id": "case_001", "offline_error": 2.0850722192783464, "paired_differences": {"target_3": 0.06290418647416152, "target_5": -0.14757338000359344, "target_7": -0.5061241253244488}}; worst={"case_id": "case_004", "offline_error": 3.3504930893606475, "paired_differences": {"target_3": 1.3936583356555357, "target_5": 1.4465592289715237, "target_7": 1.253685610371174}}
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
