# System Instructions

You are an expert programming assistant analyzing an individual program. Create a standalone summary focusing on implementation details and evaluation feedback. Consider how this specific program performs and what implementation choices were made.

# Previous Messages

[]

# User Request

# Program to Analyze
# Program to Analyze

```python
"""Retain the strongest refreshed personal-best particle for ordinary PSO."""

# EVOLVE-BLOCK-START
def retention_priority(particle_features, swarm_features) -> float:
    """Prefer low integrated distance along a damped inertial trajectory."""
    distance = float(particle_features["distance_to_best_normalized"])
    travel = 0.73 * float(particle_features["speed_normalized"])
    alignment = max(
        -1.0, min(1.0, float(particle_features["velocity_alignment"]))
    )
    # Scale before squaring to avoid overflow.
    scale = max(1.0, distance, travel)
    d = distance / scale
    v = travel / scale
    # Integral over t in [0, 1] of squared distance:
    # d*d - alignment*d*v + v*v/3.
    # This equivalent nonnegative form avoids cancellation.
    radial_midpoint = d - 0.5 * alignment * v
    path_energy = radial_midpoint * radial_midpoint + (
        (1.0 - alignment * alignment) / 4.0 + 1.0 / 12.0
    ) * v * v
    rms_distance = scale * path_energy ** 0.5
    return 1.0 / (1.0 + rms_distance)
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.21
mean_offline_error: 3.72; worst_case_offline_error: 5.20; case_error_std: 1.15; cases_completed: 8

The program is correct and passes all validation tests.

Text feedback:
Development feedback only. Lower offline error is better; fitness=1/(1+mean error). Paired differences are candidate minus comparator (negative is better). Random reference is random; heuristic seed is heuristic. All personal-best memories survive and are reevaluated. The exempted particle continues ordinary PSO; it is neither stationary nor a permanent leader. Choices change complete closed-loop trajectories. Agreement is measured against the heuristic on each candidate snapshot, not across reference trajectories.
case_000 severity=1.0,period=2500: error=4.033720, delta random=+0.000730, delta heuristic=-0.086383; heuristic agreements=81/245; selected ranks={'2': 68, '1': 81, '3': 45, '5': 16, '4': 35}; selected feature means={'personal_best_rank': 2.3346938775510204, 'distance_to_best_normalized': 5.849073155014955, 'speed_normalized': 15.139428060206457, 'velocity_alignment': -0.01790057038539746}; interval-end error=3.1332035872776265; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 8.20810091634027, "completed_environment": 7, "difference": -1.4028721757604643, "reference_environment_error": 9.610973092100734}, "most_unfavorable": {"candidate_environment_error": 1.5256197276961827, "completed_environment": 16, "difference": 0.7992166219451575, "reference_environment_error": 0.7264031057510252}}
case_001 severity=1.0,period=2500: error=2.510732, delta random=+0.121043, delta heuristic=-0.141301; heuristic agreements=86/273; selected ranks={'4': 35, '1': 86, '2': 77, '3': 64, '5': 11}; selected feature means={'personal_best_rank': 2.2967032967032965, 'distance_to_best_normalized': 3.9401738980444856, 'speed_normalized': 16.372618854726735, 'velocity_alignment': -0.008644567705116277}; interval-end error=1.5510470072492075; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 1.4995173721002528, "completed_environment": 33, "difference": -1.10067860105287, "reference_environment_error": 2.600195973153123}, "most_unfavorable": {"candidate_environment_error": 2.941127432358593, "completed_environment": 39, "difference": 0.7097873874666285, "reference_environment_error": 2.2313400448919647}}
case_002 severity=1.0,period=5000: error=2.432667, delta random=-0.928965, delta heuristic=-0.064913; heuristic agreements=39/113; selected ranks={'2': 25, '1': 39, '3': 27, '4': 17, '5': 5}; selected feature means={'personal_best_rank': 2.327433628318584, 'distance_to_best_normalized': 7.377021539315129, 'speed_normalized': 12.431239750855427, 'velocity_alignment': 0.05332235228424236}; interval-end error=1.85025046349615; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 1.9332486230430164, "completed_environment": 7, "difference": -1.113419333204787, "reference_environment_error": 3.0466679562478034}, "most_unfavorable": {"candidate_environment_error": 1.9770350692080036, "completed_environment": 3, "difference": 0.9424684215692636, "reference_environment_error": 1.03456664763874}}
case_003 severity=1.0,period=5000: error=4.932270, delta random=+0.637663, delta heuristic=-0.367405; heuristic agreements=35/91; selected ranks={'1': 35, '3': 26, '2': 12, '4': 11, '5': 7}; selected feature means={'personal_best_rank': 2.3736263736263736, 'distance_to_best_normalized': 7.734228316013689, 'speed_normalized': 22.909920227883752, 'velocity_alignment': 0.005657033129816678}; interval-end error=4.1085263906227105; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 4.96981406464863, "completed_environment": 13, "difference": -5.650404637179704, "reference_environment_error": 10.620218701828334}, "most_unfavorable": {"candidate_environment_error": 0.3126323149931868, "completed_environment": 18, "difference": 0.1632659769494966, "reference_environment_error": 0.14936633804369018}}
case_004 severity=3.0,period=2500: error=5.204623, delta random=-0.078081, delta heuristic=-0.269077; heuristic agreements=73/221; selected ranks={'2': 48, '4': 35, '1': 73, '3': 49, '5': 16}; selected feature means={'personal_best_rank': 2.425339366515837, 'distance_to_best_normalized': 2.638107545774059, 'speed_normalized': 5.785121041970215, 'velocity_alignment': -0.043630569988151305}; interval-end error=3.726915769217101; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 2.2789394448426163, "completed_environment": 5, "difference": -9.71632416080488, "reference_environment_error": 11.995263605647496}, "most_unfavorable": {"candidate_environment_error": 3.573403151902721, "completed_environment": 16, "difference": 2.114846107327314, "reference_environment_error": 1.4585570445754066}}
case_005 severity=3.0,period=2500: error=3.973940, delta random=+0.149035, delta heuristic=+0.253791; heuristic agreements=90/338; selected ranks={'1': 90, '3': 77, '2': 89, '4': 51, '5': 31}; selected feature means={'personal_best_rank': 2.5384615384615383, 'distance_to_best_normalized': 1.6888978683278897, 'speed_normalized': 3.6272240062379035, 'velocity_alignment': -0.0011624291557603352}; interval-end error=1.2840304349232723; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 1.7414148310882873, "completed_environment": 9, "difference": -2.1686475456329743, "reference_environment_error": 3.9100623767212617}, "most_unfavorable": {"candidate_environment_error": 7.504631262583923, "completed_environment": 37, "difference": 2.9023155151492617, "reference_environment_error": 4.602315747434662}}
case_006 severity=3.0,period=5000: error=2.333664, delta random=+0.071947, delta heuristic=-0.762278; heuristic agreements=40/115; selected ranks={'3': 27, '5': 7, '2': 25, '1': 40, '4': 16}; selected feature means={'personal_best_rank': 2.347826086956522, 'distance_to_best_normalized': 2.9059877842228086, 'speed_normalized': 5.613266576836145, 'velocity_alignment': -0.04984919232864315}; interval-end error=0.6052251078726784; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 1.5417253633309798, "completed_environment": 11, "difference": -12.578778596175395, "reference_environment_error": 14.120503959506374}, "most_unfavorable": {"candidate_environment_error": 3.892819559779008, "completed_environment": 14, "difference": 3.410470741773338, "reference_environment_error": 0.48234881800566964}}
case_007 severity=3.0,period=5000: error=4.374669, delta random=+0.045405, delta heuristic=+0.020368; heuristic agreements=22/91; selected ranks={'2': 28, '1': 22, '3': 23, '4': 14, '5': 4}; selected feature means={'personal_best_rank': 2.4505494505494507, 'distance_to_best_normalized': 3.5337465964436334, 'speed_normalized': 7.472273495002837, 'velocity_alignment': -0.03642014798255477}; interval-end error=3.487919880092259; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 2.25355679933456, "completed_environment": 4, "difference": -2.0840571111327737, "reference_environment_error": 4.337613910467334}, "most_unfavorable": {"candidate_environment_error": 3.6376925785171412, "completed_environment": 3, "difference": 3.1183724055882296, "reference_environment_error": 0.5193201729289116}}
Paired regime summary: {"cases": 2, "mean_offline_error": 3.2722258822090318, "random_difference_sd": 0.08507413254817449, "random_mean_difference": 0.06088650977048515, "regime": "severity=1.0,period=2500", "seed_difference_sd": 0.03883279299420116, "seed_mean_difference": -0.11384188060501765}
Paired regime summary: {"cases": 2, "mean_offline_error": 3.6824685604005953, "random_difference_sd": 1.1077731569936453, "random_mean_difference": -0.14565132880748566, "regime": "severity=1.0,period=5000", "seed_difference_sd": 0.2138945152785534, "seed_mean_difference": -0.2161591741255835}
Paired regime summary: {"cases": 2, "mean_offline_error": 4.5892814679287035, "random_difference_sd": 0.16059557049812034, "random_mean_difference": 0.03547718170947922, "regime": "severity=3.0,period=2500", "seed_difference_sd": 0.3697235934581715, "seed_mean_difference": -0.0076426782801839455}
Paired regime summary: {"cases": 2, "mean_offline_error": 3.3541663082444497, "random_difference_sd": 0.018768111044570317, "random_mean_difference": 0.05867589708047949, "regime": "severity=3.0,period=5000", "seed_difference_sd": 0.5534143969456183, "seed_mean_difference": -0.370954823564309}
Exactly four of five particles relocate at radius1.25 with retained velocities and fixed memory reevaluation. Only the per-particle retention priority evolves. Simple rules and constants are legitimate. Competing explanations include trajectory continuity, geometric diversity, later asynchronous attractor updates, query allocation and stochastic closed-loop variation. No fresh validation is planned in this bounded development experiment.



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
