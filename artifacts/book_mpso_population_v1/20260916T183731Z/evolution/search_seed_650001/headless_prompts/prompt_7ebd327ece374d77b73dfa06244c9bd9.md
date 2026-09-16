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
    previous_best = observation["previous_best_fitness"]
    refreshed_loss = previous_best - observation["current_best_fitness"]
    if (
        refreshed_loss > 0.05 * max(1.0, abs(previous_best))
        and observation["neutral_diameter"] <= 2.0 * radius
        and observation["mean_neutral_distance_to_best"] <= radius
        and observation["mean_neutral_speed"] <= radius
    ):
        return 4
    return 5
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.34
mean_offline_error: 1.94; worst_case_offline_error: 3.33; case_error_std: 0.72; cases_completed: 8

The program is correct and passes all validation tests.

Text feedback:
Reused development cases only. Lower offline error is better; fitness=1/(1+mean error). Paired differences are candidate minus comparator (negative is better). Target5 is the reconstructed chapter5+1 and native seed. Fixed targets3/7 start at five and resize by at most one per detected event using exactly the same adapter. Best tested fixed target by development mean (numeric target breaks ties): target_5. Only neutral population targets change. Every current neutral quantum-samples on detected change, otherwise uses ordinary PSO; one permanent quantum particle always samples. Whole trajectories, convergence/birth timing and later random draws can diverge.
case_000 severity=1.0,period=5000: error=1.945758, deltatarget_3=+0.015029, deltatarget_5=-0.104972, deltatarget_7=-0.423469; interval-end error=1.17770460442798; incomplete responses=0.
Measured population behavior: {"additions": 140, "mean_neutral_count_per_subswarm_update": 4.435229942480625, "neutral_count_sum": 328482, "no_change_requests": 497, "policy_calls": 787, "population_decisions": 787, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 41828, "5": 32234, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 12], "recorded_total_particle_count_range": [6, 66], "removals": 150, "requested_target_histogram": {"2": 0, "3": 0, "4": 460, "5": 327, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 74062}
Query shares: {"birth": 0.003876, "detection": 0.148124, "exclusion": 0.034356, "initialization": 1.2e-05, "memory": 0.008544, "ordinary": 0.650014, "permanent_quantum": 0.148124, "temporary_quantum": 0.00695}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 0.40882902323298087, "completed_environment": 21, "difference": -3.5796378387361543, "reference_environment_error": 3.988466861969135}, "most_unfavorable": {"candidate_environment_error": 18.64826037973236, "completed_environment": 13, "difference": 2.4410743051590416, "reference_environment_error": 16.20718607457332}}
case_001 severity=1.0,period=5000: error=2.194912, deltatarget_3=+0.172744, deltatarget_5=-0.037733, deltatarget_7=-0.396284; interval-end error=1.4811468857509882; incomplete responses=0.
Measured population behavior: {"additions": 125, "mean_neutral_count_per_subswarm_update": 4.394929081795883, "neutral_count_sum": 329690, "no_change_requests": 534, "policy_calls": 791, "population_decisions": 791, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 45390, "5": 29626, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 11], "recorded_total_particle_count_range": [6, 61], "removals": 132, "requested_target_histogram": {"2": 0, "3": 0, "4": 494, "5": 297, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 75016}
Query shares: {"birth": 0.004044, "detection": 0.150032, "exclusion": 0.027984, "initialization": 1.2e-05, "memory": 0.008518, "ordinary": 0.652458, "permanent_quantum": 0.15003, "temporary_quantum": 0.006922}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 1.2693735994080044, "completed_environment": 88, "difference": -14.195029588519803, "reference_environment_error": 15.464403187927807}, "most_unfavorable": {"candidate_environment_error": 11.688089928123983, "completed_environment": 17, "difference": 11.107153066798087, "reference_environment_error": 0.5809368613258956}}
case_002 severity=1.0,period=5000: error=1.873129, deltatarget_3=-0.469000, deltatarget_5=-0.397819, deltatarget_7=-0.048251; interval-end error=1.0166945255328441; incomplete responses=0.
Measured population behavior: {"additions": 116, "mean_neutral_count_per_subswarm_update": 4.391653139798506, "neutral_count_sum": 327367, "no_change_requests": 562, "policy_calls": 803, "population_decisions": 803, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 45348, "5": 29195, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 12], "recorded_total_particle_count_range": [6, 65], "removals": 125, "requested_target_histogram": {"2": 0, "3": 0, "4": 504, "5": 299, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 74543}
Query shares: {"birth": 0.004644, "detection": 0.149086, "exclusion": 0.033804, "initialization": 1.2e-05, "memory": 0.008646, "ordinary": 0.647702, "permanent_quantum": 0.149084, "temporary_quantum": 0.007022}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 0.5107839756943122, "completed_environment": 17, "difference": -8.793568022392826, "reference_environment_error": 9.304351998087139}, "most_unfavorable": {"candidate_environment_error": 3.471377027612027, "completed_environment": 63, "difference": 2.6746634447001183, "reference_environment_error": 0.7967135829119084}}
case_003 severity=1.0,period=5000: error=0.836936, deltatarget_3=+0.114049, deltatarget_5=-0.011047, deltatarget_7=+0.145584; interval-end error=0.24344715195059408; incomplete responses=0.
Measured population behavior: {"additions": 185, "mean_neutral_count_per_subswarm_update": 4.46673329911667, "neutral_count_sum": 330708, "no_change_requests": 576, "policy_calls": 952, "population_decisions": 952, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 39482, "5": 34556, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 13], "recorded_total_particle_count_range": [6, 69], "removals": 191, "requested_target_histogram": {"2": 0, "3": 0, "4": 525, "5": 427, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 74038}
Query shares: {"birth": 0.003672, "detection": 0.148076, "exclusion": 0.028368, "initialization": 1.2e-05, "memory": 0.010386, "ordinary": 0.652942, "permanent_quantum": 0.148074, "temporary_quantum": 0.00847}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 0.9430979376917307, "completed_environment": 37, "difference": -5.158420109525106, "reference_environment_error": 6.101518047216836}, "most_unfavorable": {"candidate_environment_error": 6.587084770411326, "completed_environment": 93, "difference": 4.932539141577149, "reference_environment_error": 1.6545456288341767}}
case_004 severity=1.0,period=5000: error=3.334226, deltatarget_3=+1.377391, deltatarget_5=+1.430292, deltatarget_7=+1.237419; interval-end error=2.6526569748723894; incomplete responses=0.
Measured population behavior: {"additions": 124, "mean_neutral_count_per_subswarm_update": 4.415809559898229, "neutral_count_sum": 326293, "no_change_requests": 468, "policy_calls": 722, "population_decisions": 722, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 43167, "5": 30725, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 10], "recorded_total_particle_count_range": [6, 55], "removals": 130, "requested_target_histogram": {"2": 0, "3": 0, "4": 431, "5": 291, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 73892}
Query shares: {"birth": 0.0036, "detection": 0.147784, "exclusion": 0.040428, "initialization": 1.2e-05, "memory": 0.007814, "ordinary": 0.646222, "permanent_quantum": 0.147782, "temporary_quantum": 0.006358}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 0.31892519146524334, "completed_environment": 29, "difference": -1.2312534059506601, "reference_environment_error": 1.5501785974159035}, "most_unfavorable": {"candidate_environment_error": 13.78560226975935, "completed_environment": 35, "difference": 12.320780659564422, "reference_environment_error": 1.4648216101949276}}
case_005 severity=1.0,period=5000: error=1.510725, deltatarget_3=-0.011491, deltatarget_5=+0.214808, deltatarget_7=+0.066856; interval-end error=0.7419223000992631; incomplete responses=0.
Measured population behavior: {"additions": 159, "mean_neutral_count_per_subswarm_update": 4.470418215865607, "neutral_count_sum": 329443, "no_change_requests": 510, "policy_calls": 834, "population_decisions": 834, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 39027, "5": 34667, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 12], "recorded_total_particle_count_range": [6, 69], "removals": 165, "requested_target_histogram": {"2": 0, "3": 0, "4": 478, "5": 356, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 73694}
Query shares: {"birth": 0.003708, "detection": 0.147388, "exclusion": 0.033564, "initialization": 1.2e-05, "memory": 0.009064, "ordinary": 0.651494, "permanent_quantum": 0.147386, "temporary_quantum": 0.007384}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 0.758169125239157, "completed_environment": 51, "difference": -0.6608510924146919, "reference_environment_error": 1.419020217653849}, "most_unfavorable": {"candidate_environment_error": 13.51794999528084, "completed_environment": 48, "difference": 12.02447272855151, "reference_environment_error": 1.49347726672933}}
case_006 severity=1.0,period=5000: error=1.597716, deltatarget_3=-0.033638, deltatarget_5=-0.087986, deltatarget_7=-0.108659; interval-end error=0.7222788055046112; incomplete responses=0.
Measured population behavior: {"additions": 125, "mean_neutral_count_per_subswarm_update": 4.381554357112345, "neutral_count_sum": 328231, "no_change_requests": 535, "policy_calls": 794, "population_decisions": 794, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 46329, "5": 28583, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 11], "recorded_total_particle_count_range": [6, 62], "removals": 134, "requested_target_histogram": {"2": 0, "3": 0, "4": 505, "5": 289, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 74912}
Query shares: {"birth": 0.004044, "detection": 0.149824, "exclusion": 0.031308, "initialization": 1.2e-05, "memory": 0.008536, "ordinary": 0.649524, "permanent_quantum": 0.149822, "temporary_quantum": 0.00693}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 1.1566983434748623, "completed_environment": 4, "difference": -15.840014358847291, "reference_environment_error": 16.996712702322153}, "most_unfavorable": {"candidate_environment_error": 11.734529305178189, "completed_environment": 31, "difference": 10.064318701445492, "reference_environment_error": 1.6702106037326971}}
case_007 severity=1.0,period=5000: error=2.232390, deltatarget_3=-0.090014, deltatarget_5=+0.563699, deltatarget_7=+0.079339; interval-end error=1.4874104338044287; incomplete responses=0.
Measured population behavior: {"additions": 135, "mean_neutral_count_per_subswarm_update": 4.420525321796434, "neutral_count_sum": 330032, "no_change_requests": 557, "policy_calls": 836, "population_decisions": 836, "realized_neutral_count_histogram": {"2": 0, "3": 0, "4": 43263, "5": 31396, "6": 0, "7": 0, "8": 0}, "recorded_swarm_count_range": [1, 12], "recorded_total_particle_count_range": [6, 65], "removals": 144, "requested_target_histogram": {"2": 0, "3": 0, "4": 502, "5": 334, "6": 0, "7": 0, "8": 0}, "total_neutral_updates": 74659}
Query shares: {"birth": 0.003828, "detection": 0.149318, "exclusion": 0.028416, "initialization": 1.2e-05, "memory": 0.009046, "ordinary": 0.652708, "permanent_quantum": 0.149316, "temporary_quantum": 0.007356}
Observed episodes versus target5 (descriptive extrema; retain unfavorable episodes): {"most_favorable": {"candidate_environment_error": 0.8385435009862459, "completed_environment": 24, "difference": -1.5577197745664226, "reference_environment_error": 2.3962632755526685}, "most_unfavorable": {"candidate_environment_error": 10.86209024547839, "completed_environment": 37, "difference": 9.884569932864288, "reference_environment_error": 0.977520312614101}}
Paired regime summary: {"best_tested_fixed_target": "target_5", "cases": 8, "mean_offline_error": 1.9407241332546394, "regime": "severity=1.0,period=5000", "target_3_difference_sd": 0.5378708906746268, "target_3_mean_difference": 0.13438379598255182, "target_5_difference_sd": 0.5707622280136481, "target_5_mean_difference": 0.19615535173970863, "target_7_difference_sd": 0.5176188593342228, "target_7_mean_difference": 0.06906672555427282}
Influential cases versus target_3: best={"case_id": "case_002", "offline_error": 1.873129092893317, "paired_differences": {"target_3": -0.4689997887912045, "target_5": -0.3978187667289128, "target_7": -0.04825094121147888}}; worst={"case_id": "case_004", "offline_error": 3.3342262276113632, "paired_differences": {"target_3": 1.3773914739062514, "target_5": 1.4302923672222394, "target_7": 1.2374187486218897}}
Influential cases versus target_5: best={"case_id": "case_002", "offline_error": 1.873129092893317, "paired_differences": {"target_3": -0.4689997887912045, "target_5": -0.3978187667289128, "target_7": -0.04825094121147888}}; worst={"case_id": "case_004", "offline_error": 3.3342262276113632, "paired_differences": {"target_3": 1.3773914739062514, "target_5": 1.4302923672222394, "target_7": 1.2374187486218897}}
Influential cases versus target_7: best={"case_id": "case_000", "offline_error": 1.9457581990553172, "paired_differences": {"target_3": 0.015028799457416087, "target_5": -0.10497208015497606, "target_7": -0.4234694622753672}}; worst={"case_id": "case_004", "offline_error": 3.3342262276113632, "paired_differences": {"target_3": 1.3773914739062514, "target_5": 1.4302923672222394, "target_7": 1.2374187486218897}}
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
