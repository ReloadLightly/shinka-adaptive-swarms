# System Instructions

You are an expert programming assistant analyzing an individual program. Create a standalone summary focusing on implementation details and evaluation feedback. Consider how this specific program performs and what implementation choices were made.

# Previous Messages

[]

# User Request

# Program to Analyze
# Program to Analyze

```python
"""Count-four recovery policy; memory reevaluation is fixed by the adapter."""

# EVOLVE-BLOCK-START
def choose_recovery(observation: dict) -> dict:
    compactness = observation["swarm_diameter"] / max(
        observation["default_radius"], 1e-12
    )
    radius_scale = 1.25 if compactness < 2.0 else 1.2
    return {"radius_scale": radius_scale, "reset_velocity": False}
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.26
mean_offline_error: 2.91; worst_case_offline_error: 4.08; case_error_std: 1.05; cases_completed: 8

The program is correct and passes all validation tests.

Text feedback:
Development feedback only. Lower offline error is better; fitness=1/(1+mean error). Paired differences below are candidate minus comparator (negative is better). Baseline is baseline; fixed seed is c4_r1_retain. Same environment and optimizer seeds pair complete closed-loop methods; optimizer draws may diverge. Action occupancy is measured output behavior, not syntactic branch coverage.
case_000 severity=1.0,period=2500: error=2.682379, delta baseline=-1.826416, delta fixed seed=-0.307950; reset on 0/306 responses; 2 observed action pairs; most frequent [radius=1.25,reset=False: 254 (83.0%); radius=1.2,reset=False: 52 (17.0%)]; interval-end error=1.3548766864886796; query shares={"detection": 0.15861, "exclusion": 0.02845, "initialization": 5e-05, "memory": 0.0153, "particle": 0.79759}; horizon-truncated responses=0.
case_001 severity=1.0,period=2500: error=2.699125, delta baseline=-0.840783, delta fixed seed=+0.218557; reset on 0/355 responses; 2 observed action pairs; most frequent [radius=1.25,reset=False: 299 (84.2%); radius=1.2,reset=False: 56 (15.8%)]; interval-end error=0.8923648261650987; query shares={"detection": 0.1588, "exclusion": 0.0231, "initialization": 5e-05, "memory": 0.01775, "particle": 0.8003}; horizon-truncated responses=0.
case_002 severity=1.0,period=5000: error=1.722592, delta baseline=-0.044309, delta fixed seed=-0.028623; reset on 0/149 responses; 2 observed action pairs; most frequent [radius=1.25,reset=False: 127 (85.2%); radius=1.2,reset=False: 22 (14.8%)]; interval-end error=1.216768959672041; query shares={"detection": 0.1604, "exclusion": 0.0244, "initialization": 5e-05, "memory": 0.00745, "particle": 0.8077}; horizon-truncated responses=0.
case_003 severity=1.0,period=5000: error=1.164451, delta baseline=-0.340940, delta fixed seed=-0.028805; reset on 0/103 responses; 2 observed action pairs; most frequent [radius=1.25,reset=False: 85 (82.5%); radius=1.2,reset=False: 18 (17.5%)]; interval-end error=0.48949180927197594; query shares={"detection": 0.15845, "exclusion": 0.04, "initialization": 5e-05, "memory": 0.00515, "particle": 0.79635}; horizon-truncated responses=0.
case_004 severity=3.0,period=2500: error=4.079832, delta baseline=+0.066755, delta fixed seed=-1.199176; reset on 0/334 responses; 2 observed action pairs; most frequent [radius=1.25,reset=False: 286 (85.6%); radius=1.2,reset=False: 48 (14.4%)]; interval-end error=0.9238388791204857; query shares={"detection": 0.15991, "exclusion": 0.0198, "initialization": 5e-05, "memory": 0.0167, "particle": 0.80354}; horizon-truncated responses=0.
case_005 severity=3.0,period=2500: error=3.955441, delta baseline=+0.018642, delta fixed seed=+0.199930; reset on 0/334 responses; 2 observed action pairs; most frequent [radius=1.25,reset=False: 282 (84.4%); radius=1.2,reset=False: 52 (15.6%)]; interval-end error=0.614261017104259; query shares={"detection": 0.1597, "exclusion": 0.0212, "initialization": 5e-05, "memory": 0.0167, "particle": 0.80235}; horizon-truncated responses=0.
case_006 severity=3.0,period=5000: error=3.609229, delta baseline=-1.396126, delta fixed seed=+0.010187; reset on 0/104 responses; 2 observed action pairs; most frequent [radius=1.25,reset=False: 87 (83.7%); radius=1.2,reset=False: 17 (16.3%)]; interval-end error=1.908340630221695; query shares={"detection": 0.15929, "exclusion": 0.0338, "initialization": 5e-05, "memory": 0.0052, "particle": 0.80166}; horizon-truncated responses=0.
case_007 severity=3.0,period=5000: error=3.376668, delta baseline=+0.264101, delta fixed seed=+0.090883; reset on 0/157 responses; 2 observed action pairs; most frequent [radius=1.25,reset=False: 136 (86.6%); radius=1.2,reset=False: 21 (13.4%)]; interval-end error=0.4031353256665174; query shares={"detection": 0.16052, "exclusion": 0.0235, "initialization": 5e-05, "memory": 0.00785, "particle": 0.80808}; horizon-truncated responses=0.
Paired regime summary: {"baseline_difference_sd": 0.6969475461238804, "baseline_mean_difference": -1.3335993277141693, "cases": 2, "mean_offline_error": 2.6907522400203883, "regime": "severity=1.0,period=2500", "seed_difference_sd": 0.37229694701840665, "seed_mean_difference": -0.044696493834344375}
Paired regime summary: {"baseline_difference_sd": 0.2097503130714814, "baseline_mean_difference": -0.19262453020384818, "cases": 2, "mean_offline_error": 1.4435215315640888, "regime": "severity=1.0,period=5000", "seed_difference_sd": 0.000128968994333226, "seed_mean_difference": -0.028714198024081483}
Paired regime summary: {"baseline_difference_sd": 0.034021590560911745, "baseline_mean_difference": 0.04269841140639197, "cases": 2, "mean_offline_error": 4.0176365762353345, "regime": "severity=3.0,period=2500", "seed_difference_sd": 0.9893175502609739, "seed_mean_difference": -0.49962302576491213}
Paired regime summary: {"baseline_difference_sd": 1.1739576716409204, "baseline_mean_difference": -0.5660127040114828, "cases": 2, "mean_offline_error": 3.4929482831656418, "regime": "severity=3.0,period=5000", "seed_difference_sd": 0.057060791640577695, "seed_mean_difference": 0.05053506896203319}
Four selected particles and memory reevaluation are fixed. Constants and conditions are equally legitimate. Radius/velocity outcome interactions do not prove overshoot; neither velocity-mediated overshoot nor an ideal radius is directly measured. Evaluate competing explanations, including constant tuning, swarm spread, query allocation and stochastic closed-loop effects. No protected pilot outcomes enter this feedback.



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
