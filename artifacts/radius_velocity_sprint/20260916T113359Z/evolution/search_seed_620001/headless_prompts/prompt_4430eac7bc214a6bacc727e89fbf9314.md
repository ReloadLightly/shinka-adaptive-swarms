# System Instructions

You are an expert programming assistant generating actionable recommendations for future program mutations based on successful patterns and insights.

# Previous Messages

[]

# User Request

# Global Insights
## Successful Algorithmic Patterns
- **Generation 3 remains the best evaluated program.** Constant `radius_scale=1.25` with `reset_velocity=False` achieves **0.2573**, reducing mean error from Generation 0’s **3.0418 to 2.8868**—a **5.1% improvement**, with **7/8 wins** against the fixed seed. Worst-case error also falls from **5.2790 to 4.2667**.
- **Generation 12’s compactness-conditioned recovery is the closest new competitor.** Selecting **1.25** below compactness **2.0**, otherwise **1.2**, achieves **0.2557** and mean error **2.9112**. It improves on constant radius **1.2** (Generation 4: **0.2541**, error **2.9362**), but does not surpass Generation 3.
- **Velocity retention remains the stronger observed policy at radius 1.25.** Generation 3’s mean error is **0.3889 lower** than unconditional-reset Generations 6–7. This supports retention on these development cases without establishing a velocity-overshoot mechanism.
## Ineffective Approaches
- **Generation 10’s spread-and-pressure adaptation underperforms the winning constant.** Its bounded **[0.85, 1.35]** radius adjustment scores **0.2394**, with mean error **3.1771**—**0.2903 higher** than Generation 3 and **0.1352 higher** than the fixed seed. Fitness-loss and spread conditioning did not yield an aggregate advantage.
- **Generation 11’s midpoint radius does not interpolate performance.** Constant radius **1.225**, retaining velocity, scores **0.2416** with error **3.1390**, worse than both **1.2** and **1.25**. Its **6/8 baseline wins** therefore do not imply superiority to Generation 3’s **5/8**.
- **Both radius contraction and larger expansion remain inferior.** Radii **0.75/0.5** produce errors **3.3351/3.3136**; radii **1.3/1.275** produce **3.0432/3.0853**. These outcomes, together with Generation 11, reinforce a nonmonotonic response.
- **Velocity-reset conditions have not improved recovery.** Unconditional reset scores **0.2339**; Generation 9’s `relative_fitness_drop > 0.15` gate scores **0.2220**, with error **3.5053**. Both gated actions occurred in every case, so an inactive condition does not explain its weak result.
## Implementation Insights
- **The best program demonstrates effective constant tuning.** Generation 3 ignores observations and returns `(1.25, False)` for all **1,835 responses**. Its advantage requires neither state-dependent decisions nor additional policy complexity. The multiplier acts on the default radius, so absolute relocation distance still varies across regimes.
- **Generation 12 implements active but modest adaptation.** Its diameter/default-radius ratio uses a **1e-12 denominator floor**, and radius **1.25** accounts for approximately **83–87%** of responses. Its proximity to Generation 3 is consistent with predominantly using the winning action; observed branching alone does not establish beneficial state dependence.
- **Fixed adapter settings isolate policy outputs without fixing trajectories.** All candidates relocate four selected particles and reevaluate memory. Retained-velocity candidates differ in radius policy, but subsequent swarm spread, random-number consumption and query allocation can diverge.
- **Evaluation costs remain relevant despite constant outputs.** Generation 3 allocates approximately **79.6–80.9%** of queries to particles, **15.8–16.1%** to detection and **0.5–1.9%** to memory. These measured shares do not establish which mechanism caused its improvement.
## Performance Analysis
- **Rounded scores conceal the distinction between the leaders.** Generations 3 and 12 both display **0.26**, but their actual scores are **0.25728 versus 0.25568**. Generation 12’s mean error is **0.02445 higher**, approximately **0.85% worse**.
- **Generation 12 improves secondary metrics while losing on the objective.** Its worst-case error is **4.0798 versus 4.2667**, and case-error standard deviation is **1.0503 versus 1.1453**. Fitness rewards mean error through `1/(1+mean error)`, so these improvements do not displace Generation 3.
- **Their regime differences reveal a tradeoff.** Generation 12 lowers severe, frequent-change mean error from **4.2629 to 4.0176**, but increases error in the other three regimes. Both programs still lose to baseline in both severe, frequent-change cases.
- **Comparator choice and evidence scope remain essential.** Generation 3 improves regime-average error against the fixed seed in all four regimes, despite one individual loss. Generations 10–11 beat baseline more often than their mean-error ranking suggests. All programs pass validation, but eight development cases establish neither generalization, an ideal radius, nor a causal advantage from adaptation or velocity-mediated overshoot.

# Previous Recommendations (if any)
1. **Refine the strongest constant policy.** Create separate mutations returning `radius_scale=1.225`, `1.2375`, and `1.2625`, each with `reset_velocity=False`. The successful 1.2–1.25 settings and deterioration at 1.275–1.3 make small local changes the strongest supported direction.
2. **Adapt radius smoothly within the successful range.** Set `d = max(0.0, observation["relative_fitness_drop"])` and return `radius_scale = 1.2 + 0.05*d/(0.1+d)`, always retaining velocity. This tests whether larger observed losses favor 1.25 while avoiding both aggressive expansion and the unsuccessful fitness-drop-triggered reset.
3. **Use swarm compactness to select between successful constants.** Compute `q = observation["swarm_diameter"] / max(observation["default_radius"], 1e-12)` and choose radius 1.25 when `q < 2.0`, otherwise 1.2, with velocity retained. This tests the unproven hypothesis that compact swarms benefit more from expansion while limiting both actions to settings that already improved mean error.
4. **Scale modest expansion with observed attractor movement.** Compute `m = max(0.0, observation["observed_best_displacement"]) / max(observation["default_radius"], 1e-12)` and return `radius_scale = 1.2 + 0.05*m/(1.0+m)`, with `reset_velocity=False`. Observed displacement supplies a geometric signal distinct from fitness loss; the bounded formula preserves the successful expansion range without treating that displacement as true peak motion.
5. **Introduce bounded persistence in radius adjustments.** Set `p = min(1.25, max(1.2, observation["previous_response_radius"] / max(observation["default_radius"], 1e-12)))`; return `min(1.25, p+0.0125)` when `fitness_drop > max(0.0, recent_improvement)`, otherwise `max(1.2, p-0.0125)`, retaining velocity throughout. This tests gradual adjustment across responses using the supplied previous radius, while preventing the escalation beyond 1.25 that weakened earlier candidates.

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
