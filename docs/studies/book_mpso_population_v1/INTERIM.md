# First measurement: population targets change allocation, without a mean gain

Recorded **16 September 2026, 18:56 UTC**, after all fixed-target controls completed,
before reviewing evolutionary outcomes. No task or evaluator setting changes follow
this measurement. Eight reused development pairs have 500,000 queries each.

| Fixed target, starting at five | Mean offline error | Difference from target five | Paired SD | Descriptive 95% interval | Wins / losses |
|---|---:|---:|---:|---|---:|
| Three | 1.806340 | +0.061772 | 0.275991 | [−0.092645,+0.257007] | 4 / 4 |
| Five: chapter 5+1 | **1.744569** | — | — | — | — |
| Seven | 1.871657 | +0.127089 | 0.278167 | [−0.058890,+0.296543] | 2 / 6 |

Target five is the best of the three tested controls on these development histories.
The target-three median difference is nearly zero (−0.000724). Case 007's +0.653714
loss more than accounts for its net mean disadvantage: the other seven average
−0.022792. That is an influence description, not a reason to remove the case. Target
seven's mean remains worse under each leave-one-case-out deletion. These descriptive
intervals are not significance gates, and the eight cases are not fresh evidence.

The adapter visibly changes effort allocation. Across eight cases, target three
removed **860 neutrals**, while target seven added **869**. They realize their final
target on **85.26%** and **84.06%** of subswarm updates, respectively; births, exclusions
and step-one transitions leave other sizes present. All targets still begin at five.
The mean sampled total population is **37.48 / 51.63 / 64.91 particles** for targets
three/five/seven, while mean swarm counts are **8.80 / 8.60 / 8.39**. A constant request
therefore does not imply identical sizes across all live subswarms: at about 99% of
saved query-grid points, target-three/seven executions contain multiple neutral sizes.
This heterogeneity follows the fixed adapter and swarm lifetimes, not an adaptive branch.

| Target | Ordinary movement queries | Permanent quantum queries | Detection queries | Memory refresh queries |
|---|---:|---:|---:|---:|
| Three | 58.58% | 18.05% | 18.05% | 0.72% |
| Five | 67.51% | 13.67% | 13.67% | 0.99% |
| Seven | 72.81% | 11.03% | 11.03% | 1.25% |

Smaller populations give permanent sampling and detection more opportunities within
the fixed query budget, while larger populations devote more queries to ordinary PSO.
These are measured allocation differences; they do not isolate which pathway explains
a case's tracking error. Complete closed-loop trajectories and birth/removal opportunities
also diverge. The chapter's qualitative future direction does not specify an optimum.

The original six-descendant native allowance can now ask whether an intermediate or
state-dependent target improves tracking beyond the best tested constant. No branch,
variability or preferred hypothesis is rewarded. A native constant improvement would
be size tuning. All control feedback enters through the frozen measured-feedback
interface; fresh outcomes remain absent. No additional control grid or validation
campaign is scheduled.

Accounting at this point: **16 new full executions / 8 million queries**, plus eight
certified archived target-five records. The native seed will reuse those records again
without new queries. Analysis and figures used saved artifacts, with zero simulation or
model calls. [Full control tables](../../../artifacts/book_mpso_population_v1/20260916T183731Z/analysis/reference_stage/tables.md)
are included in the final archived run.

## Four-descendant review — 19:14 UTC

All four completed descendants are valid full-horizon evaluations. The seed still
leads. The following occupancies give each of the eight cases equal weight;
additions/removals are pooled counts across those cases.

| Native generation | Actual behavior | Mean error | Non-five target frequency at detection | Additions / removals |
|---|---|---:|---:|---:|
| 0 | Always request five | **1.744569** | 0% | 0 / 0 |
| 1 | Always request four | 2.052637 | Four: 100% | 0 / 786 |
| 2 | Request four only after a non-deteriorating checked best, with compact, slow neutrals; otherwise five | 1.808258 | Four: 15.51% | 788 / 800 |
| 3 | Request six after a refreshed-best loss greater than 5%, with compact, slow neutrals; otherwise five | 1.952881 | Six: 58.25% | 1,246 / 1,189 |
| 4 | Request four after a checked-best improvement of at least 5%, with the same compact/slow gate; otherwise five | 2.008301 | Four: 9.41% | 530 / 535 |

The geometry gate uses diameter at most twice the default radius, mean distance to
the refreshed best at most one radius, and mean speed at most one radius. Generation
three's observed-loss threshold is **not** environmental movement severity: severity
is one in every case, and fitness changes also reflect changing peak heights/widths.
Its seemingly selective growth condition actually fired on 58.25% of detected
decisions. Generation four's narrower shrink gate reduced intervention frequency
but did not improve the mean relative to generation two. Source complexity and
rarity therefore do not explain performance by themselves.

Generation two is the best descendant so far, not the selected overall winner.
Its difference from target five is **+0.063689**, median **+0.135465**, SD **0.317468**,
with three wins/five losses and descriptive interval **[−0.143676,+0.268554]**.
Case 004's +0.516045 loss slightly exceeds the net mean contribution; deleting it
would nearly center the other seven (−0.000933), but it remains included. The gate
caused repeated shrink/regrow cycles, not a stable global transfer of particles.

Native novelty rejected two exact repeats before numerical evaluation: the original
seed and generation one's constant-four rule. Distinct accepted proposals nevertheless
remain worse than the seed. The one-island pool makes these comparisons available;
this does not establish that it prevents every behavioral duplicate or improves fitness.

The remaining two **original** slots can resolve whether a different population rule
avoids the observed churn or balances the competing ordinary/sampling query shares.
Native meta-memory has the first five evaluated programs to summarize. No manual
proposal, prompt change, task revision, numerical extension or p-value continuation
gate is introduced. If the batch ends without a distinct advantage over target five
and the best tested fixed target, the registered next step is reporting, not fresh
validation. This review does not treat partial generation-five work as a completed result.
