# Interim: particle selection after four descendant slots

**16 September 2026, 13:50 UTC.** This review uses the completed seed and
descendant slots 1–4: **three valid descendants and one terminal failure**.
Generation 5 is already being proposed by the same native controller. No task,
case, fitness, source-checking rule or numerical setting changes at this review.

## What has appeared

| Method / generation | Actual rule | Mean development error ↓ |
|---|---|---:|
| Random reference | Equal scores; common random tie permutation | 3.722188 |
| Heuristic seed / 0 | Highest refreshed personal-best quality | 3.901685 |
| 1 | Equal scores; reproduces random reference behavior | 3.722188 |
| 2 | Maximize `1/(1 + normalized_distance + normalized_speed)` | **3.680712** |
| 3 | Intended projected inertial distance; rejected before execution | Failed, zero queries |
| 4 | Minimize an integrated damped-inertial squared-distance score | 3.724536 |

Generation 1 is a rediscovery of an explicitly supplied reference, not a new
mechanism. Generation 2 favors a nearby, slowly moving particle, irrespective of
its personal-best quality. On its reached snapshots it agrees with the strongest
refreshed-memory heuristic on **27.67%** of decisions, with equal case weighting;
rank one through five occupy **27.67%, 23.27%, 24.50%, 17.98%, 6.57%**.
Its selected particles have mean normalized distance **4.5881**, speed **10.2393**
and velocity alignment **−0.1378**. These are descriptions of its own trajectories,
not a matched-state causal comparison with another method.

Generation 4 also uses direction, approximately scoring the integrated squared
distance along a straight path using 0.73 times the current velocity. This is a
candidate's proxy; the actual ordinary PSO step also uses random cognitive/social
attraction and asynchronous attractor updates. Its near-random aggregate result
does not validate the proxy or identify an overshoot mechanism.

Generation 3's local `import math` was rejected by the frozen checker. The task
prompt permits pure math but does not explicitly state the module-scope-only
import restriction; `zip` in that proposed source is also outside the checker's
allowed builtins. This is an interface limitation, not evidence that the intended
scientific rule performs badly. Preserve the failed slot and exact error. Do not
relax the task and replace it with an extra evaluation.

## What the measurements mean

Generation 2 minus random is **−0.041476**, paired SD **0.663883**, with four
improved and four worse histories. The descriptive stratified 95% interval is
**[−0.411177, +0.328224]**. The median effect is **+0.023083**; the largest absolute
case effect is an unfavorable **+1.292666** in case 003. The small mean therefore
does not establish useful selection over randomness.

Against the heuristic, generation 2 is **−0.220973**, SD **0.387657**, six wins and
two losses, descriptive interval **[−0.389604, −0.052342]**. The same cases selected
this rule, so that interval is not independent validation. Every unfavorable
case remains included. All personal-best memories survive under every method;
the intervention chooses ordinary trajectory continuation, not memory retention.

## Decision within the original batch

Continue the remaining **four original descendant slots**, subject to the existing
40-response/time ceilings. The proposals have explored distinct particle choices,
and there has been one admission failure rather than repeated nonfunctional output.
The concrete uncertainty is whether proximity, speed and direction can select a
useful continuation more consistently than the simple distance-plus-speed rule,
or whether its small advantage over random is an unstable case mixture. Native
parent selection, inspirations and meta-memory retain control of the proposals.
No intervention is manually inserted and no new comparison campaign is scheduled.

Saved evidence: `analysis/interim_four_slots/analysis.json` and the exact native
generation sources, metrics, feedback and lineage under
`particle_retention_v1/20260916T132022Z`. These eight histories remain development
data regardless of the final result. Further proposals cannot establish transfer;
the completed report must retain that limitation.
