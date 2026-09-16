# System Instructions

You are an expert programming assistant analyzing specific program evaluation results to extract actionable optimization insights. Focus on concrete performance data and implementation details from the actual programs that were evaluated.

# Previous Messages

[]

# User Request

# Individual Program Summaries
**Program Name: Constant Unit-Radius Recovery with Velocity Retention**
- **Implementation**: `choose_recovery` ignores observations and always returns `radius_scale=1.0` and `reset_velocity=False`, preserving velocity without adapting the radius multiplier. Four-particle selection and memory reevaluation remain fixed by the adapter.
- **Performance**: Passed all validation tests across 8 cases, achieving a combined score of 0.25, mean offline error of 3.04, worst-case error of 5.28, and case-error standard deviation of 1.27.
- **Feedback**: The policy matched the fixed seed exactly and beat the baseline in 6 of 8 cases, demonstrating no improvement over the seed policy. Its strongest average baseline gain occurred at severity 1.0 with period 2500, while severity 3.0 with period 2500 showed an average regression; these results do not establish an ideal radius or velocity-induced overshoot.
**Program Identifier:** Generation 0 - Patch Name initial_program - Correct Program: True

**Program Name: Fixed Reduced-Radius Recovery with Velocity Retention**
- **Implementation**: Always returns `radius_scale=0.75` and `reset_velocity=False`, ignoring observations and retaining existing velocities. Four-particle selection and memory reevaluation remain fixed by the adapter.
- **Performance**: Passed all validation tests across 8 cases, achieving a score of 0.23, mean offline error of 3.34, worst-case error of 6.88, and case-error standard deviation of 1.77.
- **Feedback**: Improved over baseline in 5/8 cases but beat the fixed-seed comparator in only 3/8, with the largest regression under severe, frequent changes. Results support regime-dependent constant tuning, but do not establish velocity overshoot or an optimal radius; swarm spread, query allocation, and stochastic closed-loop effects remain competing explanations.
**Program Identifier:** Generation 1 - Patch Name smaller_radius_retained_velocity - Correct Program: True

**Program Name: Constant Half-Radius Recovery with Retained Velocity**
- **Implementation**: Always returns `radius_scale=0.5` and `reset_velocity=False`, ignoring observations and retaining particle velocities. Four-particle selection and memory reevaluation remain fixed by the adapter.
- **Performance**: Passed all validation tests across 8 cases, achieving a score of 0.23, mean offline error of 3.31, worst-case error of 6.29, and case error standard deviation of 1.57.
- **Feedback**: Improved on baseline in 5 of 8 cases but outperformed the fixed-seed comparator in only 3; both severe, frequent-change cases worsened against both comparators. The constant action was confirmed throughout evaluation, but these results do not establish overshoot or an optimal radius.
**Program Identifier:** Generation 2 - Patch Name smaller_radius_retained_velocity - Correct Program: True

**Program Name: Constant Expanded-Radius Recovery with Velocity Retention**
- **Implementation**: Always returns `radius_scale=1.25` and `reset_velocity=False`, ignoring observations. Four-particle selection and memory reevaluation remain fixed by the adapter.
- **Performance**: Passed all validation tests across 8 cases, achieving a combined score of 0.26, mean offline error of 2.89, worst-case error of 4.27, and case-error standard deviation of 1.15.
- **Feedback**: Outperformed baseline in 5/8 cases and the fixed-seed comparator in 7/8, but underperformed baseline in both high-severity, short-period cases. Every observed response used the same action; these development results support constant tuning but do not establish an ideal radius or a velocity-overshoot mechanism.
**Program Identifier:** Generation 3 - Patch Name intermediate_radius_retain_velocity - Correct Program: True

**Program Name: Constant Radius Expansion with Velocity Retention**
- **Implementation**: Ignores observations and always returns `radius_scale=1.2` and `reset_velocity=False`. Four selected particles and memory reevaluation remain fixed by the adapter.
- **Performance**: Passed all validation tests across 8 cases, achieving a combined score of 0.25, mean offline error of 2.94, worst-case error of 4.41, and case-error standard deviation of 1.17.
- **Feedback**: The policy improved offline error against baseline in 5/8 cases and against the fixed seed in 6/8, but underperformed baseline in both high-severity, short-period cases. Observed behavior was entirely constant; results support regime-dependent tuning effects without establishing velocity overshoot or an optimal radius.
**Program Identifier:** Generation 4 - Patch Name refine_retained_velocity_radius - Correct Program: True

# Previous Global Insights (if any)
*No previous insights available.*

# Current Best Program
# Program to Analyze

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

The program is correct and passes all validation tests.

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



# Instructions

Analyze the SPECIFIC program evaluation results above to extract concrete optimization insights. Look at the actual performance scores, implementation details, and evaluation feedback to identify patterns. Reference specific programs and their results.
Make sure to incorporate the previous insights into the new insights.

**CRITICAL: Pay special attention to the current best program and how it compares to other evaluated programs. Ensure the best program's successful patterns are prominently featured in your analysis.**

Update or create insights in these sections:

## Successful Algorithmic Patterns
- Identify specific implementation changes that led to score improvements
- Reference which programs achieved these improvements and their scores
- **Highlight patterns from the current best program**
- Note the specific techniques or approaches that worked (2-4 bullet points)

## Ineffective Approaches
- Identify specific implementation changes that worsened performance
- Reference which programs had these issues and how scores were affected
- Note why these approaches failed based on evaluation feedback (2-4 bullet points)

## Implementation Insights
- Extract specific coding patterns/techniques from the evaluated programs
- **Analyze what makes the current best program effective**
- Connect implementation details to their performance impact
- Reference concrete examples from the program summaries (2-4 bullet points)

## Performance Analysis
- Analyze actual score changes and trends from the evaluated programs
- **Compare other programs' performance against the current best**
- Compare performance between different implementation approaches
- Identify score patterns and correlations (2-4 bullet points)

CRITICAL: Base insights on the ACTUAL individual program summaries, previous insights, and the current best program information. Reference specific program names, scores, and implementation details. Build upon previous insights with concrete evidence from the new evaluations. IMPORTANT: Make sure that the best results are not ignored and are prominently featured in your analysis. Do not make recommendations for the next steps. ONLY PERFORM THE ANALYSIS.
