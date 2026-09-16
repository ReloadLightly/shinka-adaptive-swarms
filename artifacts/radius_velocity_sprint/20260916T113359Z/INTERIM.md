# Interim: radius and velocity, before native discovery

Recorded 2026-09-16T11:47:16.784775+00:00. All 48 planned diagnostic executions completed
at 100,000 queries each (4.8 million queries). Eight recorded V3 development
histories, two per regime, are exploratory; these are not new validation data.
All paired configurations, budgets and landscape histories matched. Dense
25-query traces passed the focused numerical-invariance check.

| Method | Mean offline error (lower is better) |
|---|---:|
| c4_r1_retain | 3.041839 |
| c4_r1p5_retain | 3.089088 |
| c4_r1_reset | 3.329122 |
| c4_r1p5_reset | 3.332410 |
| baseline | 3.423599 |
| v3_selected | 3.152140 |

For radius 1.5 minus radius 1, the retained-velocity mean effect is
+0.047249 (SD 0.365551);
the reset-velocity effect is +0.003288
(SD 0.570773). Their within-case interaction averages
**-0.043961, SD 0.836208**, ranging from
-1.815428 to +0.930971. Opposing individual outcomes are retained:

| Case | Severity / period | Radius effect, retain | Radius effect, reset | Interaction |
|---|---|---:|---:|---:|
| 0 | 1 / 2500 | +0.703262 | -1.112167 | -1.815428 |
| 1 | 1 / 2500 | -0.121557 | -0.174501 | -0.052945 |
| 2 | 1 / 5000 | +0.006094 | +0.056287 | +0.050192 |
| 3 | 1 / 5000 | +0.018735 | +0.006841 | -0.011894 |
| 4 | 3 / 2500 | -0.611092 | +0.170100 | +0.781191 |
| 5 | 3 / 2500 | +0.227110 | -0.118500 | -0.345610 |
| 6 | 3 / 5000 | +0.021073 | +0.952044 | +0.930971 |
| 7 | 3 / 5000 | +0.134365 | +0.246199 | +0.111834 |

Reset minus retain averages +0.287283 at radius 1 and +0.243322 at radius 1.5.
Thus resetting is not a broadly successful recovery intervention in this small
suite. The small aggregate interaction hides marked history/regime variation;
it neither proves no interaction nor identifies velocity-mediated overshoot.
We did not measure overshoot relative to peaks or a causal mediator.

The exact frozen V3 policy minus the direct constant count4/radius1.5/retain is
**+0.063052**, SD
0.391413, range
[-0.559022,
+0.832095]. Its count-three branch has no
mean advantage on this reused development subset. This does not revise V3's
fresh-final null result or serve as fresh confirmation of a constant advantage.

## Consequence for the next step

Seed native ShinkaEvolve with the development-selected **count4/radius1/retain**
constant. The native batch may discover constant tuning or conditional recovery;
no adaptive branch is required. Paired baseline/seed feedback and observed action
occupancy will expose whether gains come from a single constant or a conditional
response. Inspect after approximately four and eight descendants. Competing
explanations include radius tuning, changed subsequent PSO dynamics, query
allocation, swarm spread and stochastic closed-loop trajectories. Keep the
13-slot and 60-logical-response limits; ambiguous interaction does not justify
additional validation campaigns. Select the pilot comparator only after reviewing
the development winner, then freeze it before generating fresh histories.

Measured figures and all case effects are saved in the sprint's phase_a folder;
this interim record precedes all native descendant and pilot outcomes.
