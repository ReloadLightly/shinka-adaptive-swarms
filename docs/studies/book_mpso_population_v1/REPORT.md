# Can population allocation improve chapter-aligned MPSO?

**Completed numerical batch: no distinct evolved population rule improved the reconstructed
chapter 5+1 reference on mean development error.** The target-five seed remains
selected at **1.744569**, ahead of fixed targets three (**1.806340**) and seven
(**1.871657**). The best of six valid native descendants requests **six everywhere**,
scoring **1.776112**: difference from five **+0.031543**, descriptive 95% interval
**[−0.185736,+0.250921]**, with three wins and five losses. It is constant population
size tuning, and it did not win. The conditional rules also failed to improve the mean.

The fresh-comparison trigger was not met. **No fresh identities or executions were
generated.** This supports retaining five in this setting, not equivalence, optimality
of five or rejection of population adaptation in other circumstances.

Run **`book_mpso_population_v1/20260916T183731Z`**, search seed **650001**.
[Prospective protocol](../../book_mpso_population_v1_protocol.md) ·
[Source record](../../book_mpso_source_record.md) ·
[Frozen analysis](analysis_specification.json) ·
[Complete archive](../../../artifacts/book_mpso_population_v1/20260916T183731Z).

## Question, source and fixed intervention

The project asks whether native ShinkaEvolve can improve the chapter's multi-swarm
optimizer under matched dynamic-optimization conditions and counted objective budgets.
The preceding schedule search found no better temporary-conversion schedule; that
published response remains fixed. Blackwell, Branke and Li (2008), printed p.215,
identify adapting the number of particles within MPSO subswarms as future work.
Printed p.213 also explains a competing effect: increasing particle numbers can slow
convergence and the creation of new swarms. Neither argument prescribes a useful rule.

Evolution changes only `choose_neutral_count(observation) -> int` in **[2,8]**.
This count is structural neutral population, not the earlier relocation count from
a fixed five-particle swarm. The retained schedule converts all current neutrals.
Every newly created or reinitialized swarm starts at five neutral particles and one
permanent quantum particle. The candidate is called only when the existing counted
best-point check detects change, after all personal-best memories have been refreshed
and before resizing or movement. Its target changes population by at most one.

The fixed adapter removes the worst refreshed neutral personal-best memory when
shrinking; ties remove the last neutral in the current order. It rebuilds the shared
best from surviving initialized memories and never removes the permanent role.
Growing inserts one neutral before the permanent particle, with the existing velocity
initialization. Its ensuing quantum-response move supplies its first evaluated
position and memory; no copied fitness or extra initialization query is assigned.
Survivor order, positions, velocities and memories persist. Requesting five at five
consumes no new random draw and changes no numerical execution.

All current neutrals receive a quantum move on the detected-change update and ordinary
PSO otherwise. The permanent quantum particle samples every update. Sampling radius
is the chapter's known-scale `0.5 × movement severity`; memory handling, retained
velocities, PSO coefficients, birth/removal, exclusion and accounting remain fixed.
Population grows or shrinks **within** subswarms; no conserved total or transfers are
implemented. Convergence includes all current neutrals, excludes the permanent quantum
role, and retains the documented pairwise-diameter approximation to enclosing geometry.

Observations are immutable public snapshots after refresh and before resizing: current
neutral population, observed deterioration/recent improvement, neutral geometry and
motion, current swarm and total particle counts, previous requested target and known
radius. Refreshed personal-best quality is not current-position fitness. Hidden peaks,
optimum, benchmark error, future changes, seeds and protected outcomes are excluded.
The prompt and checker agree on admitted pure mathematical expressions; no candidate
randomness, file or network access is permitted.

## Frozen design and compatible reuse

Every method receives the eight **reused development cases** from the chapter-schedule
study: five dimensions, ten conical peaks, `[0,100]^5`, severity one, change period
5,000, correlation zero, `nexcess=1`, and **500,000 counted queries per case**.
The remaining registered landscape/numerical settings are unchanged. This is one
chapter condition with eight repetitions, not the full Table 6 or a 50-run numerical
reproduction. Published Table 3 means remain context, not targets for tuning conventions.

Three fixed-target controls request three, five and seven. Every one starts at five
and takes step-one population changes after detection; target three/seven are not
historical variants initialized at those sizes. The exact target-five source is the
native seed. Its certified archived numerical outcomes are reused after compatibility
checks. Derived fixed-five diagnostic fields are marked; no old score is overwritten.
Native seed reuse adds no physical executions.

Native programs are ranked by complete development mean, then earlier generation and
source hash, including the seed. The best of targets {3,5,7} is ranked by mean and then
lower numeric target. The declared fresh trigger requires a distinct native candidate
to beat **both target five and the best fixed control**. All sources, comparator and
analysis freeze before any fresh identities; no fresh results return to search.

Paired effects are method minus reference; negative favors the first method. Descriptive
95% intervals use **20,000 independent paired-case bootstrap resamples**, analysis seed
**2026091609**, equal case weight and all cases retained. Development intervals do not
correct selection bias. Particles, updates and environmental episodes are not treated
as independent replicates. Complete trajectories can diverge even with paired landscape
histories because population decisions change optimizer draws and query allocation.

## What evolution produced

The exact selected function, unchanged from the native seed, is:

```python
def choose_neutral_count(observation) -> int:
    return 5
```

[Exact frozen selected file](../../../artifacts/book_mpso_population_v1/20260916T183731Z/programs/selected.py),
SHA256 `7e66f66ab613b6113eaea186f8c12af91a01c94d87b87822784bfc9396e4aebd`.
This maintains the reference's five neutrals and makes no population mutation.
It is a retained human-designed setting, not an evolutionary discovery.

The best descendant, generation six, instead returns `6` unconditionally. Its
[exact source](../../../artifacts/book_mpso_population_v1/20260916T183731Z/evolution/search_seed_650001/gen_6/main.py)
has SHA256 `dc6f14455aca90b62a3fc5a92cd7931cf5bcf1b35c90d843b000c63c5fc41644`.
The archived module heading still says five, inherited from the seed; the executed
function returns six. Figures label it as the **best descendant, with the seed retained**,
not as the overall selected program.

Generation six adds one neutral when each surviving new subswarm first detects a
change, taking it from five to six. Subsequent target-six requests leave that swarm
at six. Birth and exclusion replacements restart at five. All groups receive the
same target: observed differences between their sizes reflect their lifetimes and
detection timing, not a learned state-dependent allocation. The new neutral's first
move is quantum; thereafter it ordinarily uses PSO except on detected-change updates.

| Case | Target 3 | Target 5 / selected seed | Target 7 | Native target 6 | 6 − 5 |
|---|---:|---:|---:|---:|---:|
| 000 | 1.930729 | 2.050730 | 2.369228 | 2.175111 | +0.124381 |
| 001 | 2.022168 | 2.232646 | 2.591196 | 2.020689 | -0.211956 |
| 002 | 2.342129 | 2.270948 | 1.921380 | 1.760300 | -0.510648 |
| 003 | 0.722888 | 0.847983 | 0.691353 | 0.647147 | -0.200836 |
| 004 | 1.956835 | 1.903934 | 2.096807 | 1.997863 | +0.093929 |
| 005 | 1.522216 | 1.295917 | 1.443870 | 1.480358 | +0.184441 |
| 006 | 1.631353 | 1.685701 | 1.706375 | 1.849629 | +0.163928 |
| 007 | 2.322404 | 1.668691 | 2.153051 | 2.277798 | +0.609107 |

| Paired contrast | Mean | Median | SD | Descriptive 95% interval | Wins / losses |
|---|---:|---:|---:|---|---:|
| Target 3 − target 5 | +0.061772 | -0.000724 | 0.275991 | [-0.092645,+0.257007] | 4 / 4 |
| Target 7 − target 5 | +0.127089 | +0.170413 | 0.278167 | [-0.058890,+0.296543] | 2 / 6 |
| Best descendant (target 6) − target 5 | +0.031543 | +0.109155 | 0.336846 | [-0.185736,+0.250921] | 3 / 5 |

All eight paired control effects, in case order 000–007:

- Target 3 − 5: -0.120001, -0.210478, +0.071181, -0.125096, +0.052901, +0.226299, -0.054348, +0.653714.
- Target 7 − 5: +0.318497, +0.358551, -0.349568, -0.156631, +0.192874, +0.147952, +0.020673, +0.484360.


The selected program and the development-selected fixed control both alias the
reconstructed target-five reference. Their difference is exactly zero because they
share execution records, not because an independent equivalence test succeeded.
Generation six's higher mean fails the predeclared improvement trigger. Consequently,
there is no fresh-case claim and no separate baseline-validation study.

![Measured population allocation and tracking](../../../assets/book_mpso_population_v1/population_and_tracking.png)

*Measured five-dimensional outcomes. The horizontal trajectory axis is counted objective
evaluations; means give cases equal weight. All methods begin each new swarm at five.
Paired intervals are descriptive; development data are reused and informed selection.*

## Population allocation, recovery and influence

| Method | Mean total particles at saved query grid | Mean subswarms | Realized target frequency over updates | Added / removed neutrals |
|---|---:|---:|---:|---:|
| Fixed target three | 37.48 | 8.800 | Three: 85.26% | 0 / 860 |
| Target five / selected seed | 51.63 | 8.605 | Five: 100% | 0 / 0 |
| Fixed target seven | 64.91 | 8.393 | Seven: 84.06% | 869 / 0 |
| Best descendant: target six | 59.66 | 8.672 | Six: 86.72% | 789 / 0 |

Means give each case equal weight. Population means use the registered 100-query
trace grid; addition/removal totals pool the eight cases. Generation six requested
six on **all 6,676 detected decisions**. It nevertheless contains both five- and
six-neutral swarms at **97.22%** of saved grid points, averaged across cases.
That variation belongs to the common adapter and swarm turnover, not conditionality
in the evolved function. Constant targets three/seven likewise yield heterogeneous
realized sizes at approximately 99% of grid points.

| Method | Ordinary queries | Permanent quantum | Detection | Memory refresh | Temporary quantum |
|---|---:|---:|---:|---:|---:|
| Target three | 58.58% | 18.05% | 18.05% | 0.72% | 0.53% |
| Target five | 67.51% | 13.67% | 13.67% | 0.99% | 0.83% |
| Target seven | 72.81% | 11.03% | 11.03% | 1.25% | 1.11% |
| Native target six | 70.49% | 12.19% | 12.19% | 1.15% | 1.00% |

Initialization, births and exclusions account for the remainder; the complete
category totals are saved in analysis. More neutrals shifted the budget toward
ordinary PSO and away from permanent sampling/detection opportunities. The number
of subswarms remained similar on average for targets five/six. This is a measured
allocation tradeoff, not evidence that any single query category caused the result.

The conditional descendants made real changes. Generation two requested four on
15.51% of detections and produced 788 additions/800 removals; generation three
requested six on 58.25% and produced 1,246/1,189; generation four requested four on
9.41% and produced 530/535; generation five requested four on 59.93% and produced
1,109/1,171. Thus their conditions induced repeated resizing rather than merely
restating five. Their mean errors were 1.808258, 1.952881, 2.008301 and 1.940724.
An observed fitness loss is not environmental movement severity; heights/widths
also change, while configured movement severity is one throughout.

![Measured target requests and realized population](../../../assets/book_mpso_population_v1/population_behavior.png)

*Target requests occur only at counted detections. Realized populations summarize actual
subswarm updates, including the step-one transitions and new swarms starting at five.
Recovery uses saved actual offsets after environmental boundaries, excluding initialization,
first averaging environments within each case and then cases. No replay or immediate-error
interpolation was used.*

The apparent near tie between targets six/five is not a uniform effect. Case 007's
**+0.609107** loss contributes **+0.076138** to the eight-case mean, more than twice
the net +0.031543 disadvantage. The other seven average **−0.050966**. The median
is +0.109155 and five of eight cases worsen. Every case is retained; this influence
calculation is not a leave-one-out alternative result.

Examples use the prospectively fixed first-detection and quarter-budget rules,
plus the declared largest favorable/unfavorable completed-environment contrasts:

- **Case 000, first detected response, query 5,012:** generation six requests six
  from five and adds one particle. The six temporary moves and permanent quantum
  move finish at query 5,019. At actual offsets 100/500/1,000 after the environmental
  boundary, its error is **6.3102 / 5.6894 / 5.5561**, versus five's
  **5.9882 / 5.6488 / 5.5740**. Immediate differences have both signs.
- **Case 000, first update reaching one-quarter budget, query 125,014:** the swarm
  already has six and no particle is added. Errors at recorded boundary offsets
  100/500/1,000 are **3.3561 / 0.8849 / 0.6924**, versus
  **2.0909 / 1.1581 / 0.4326**. Identical target requests do not restore identical
  trajectories. All five prospective examples per case remain saved. An example
  with `resize=not_called` is not represented as a population-policy request.
- **Largest favorable episode:** case 001, environment 88, queries
  **440,001–445,000**. Environment mean error is **1.058839 versus 15.464403**,
  difference **−14.405564**. At actual offset 5,000, errors are **0.110183 versus
  14.730418**. Ten recorded population decisions request six: one addition, nine
  no-ops. This extreme describes the full reached trajectory, not the isolated
  effect of that addition.
- **Largest unfavorable episode:** case 000, environment 14, queries
  **70,001–75,000**. Mean error is **13.951269 versus 0.606141**, difference
  **+13.345129**. At offset 5,000, errors are **13.193972 versus 0.004774**.
  Seven decisions request six: one addition, six no-ops. The same nominal action
  pattern can accompany a large loss.

The extremes are explicitly post hoc examples, chosen by the frozen rule, not
representative frequencies. Neither one explains the aggregate result causally.

These observations compare reached closed-loop trajectories. Population size changes
ordinary/quantum opportunities, memory/detection shares and birth/removal timing at once.
They do not identify any one pathway as a causal mediator or show that adaptation itself
is necessary. Constants three, five and seven are useful controls, not all possible constants.

## Actual native lineage and feedback

| Gen | Native ID | Parent | Archive / top inspirations | Patch | Actual rule | Mean error |
|---|---|---:|---|---|---|---:|
| [0](../../../artifacts/book_mpso_population_v1/20260916T183731Z/evolution/search_seed_650001/gen_0/main.py) | `ec98378b` | — | [] / [] | init | Always five | 1.744569 |
| [1](../../../artifacts/book_mpso_population_v1/20260916T183731Z/evolution/search_seed_650001/gen_1/main.py) | `1b682f90` | 0 | [] / [] | diff | Always four | 2.052637 |
| [2](../../../artifacts/book_mpso_population_v1/20260916T183731Z/evolution/search_seed_650001/gen_2/main.py) | `bdcfd4d4` | 0 | [1] / [] | cross | Four after non-deteriorating check and compact/slow geometry; otherwise five | 1.808258 |
| [3](../../../artifacts/book_mpso_population_v1/20260916T183731Z/evolution/search_seed_650001/gen_3/main.py) | `096c1dd0` | 2 | [0] / [1] | diff | Six after >5% refreshed loss and compact/slow geometry; otherwise five | 1.952881 |
| [4](../../../artifacts/book_mpso_population_v1/20260916T183731Z/evolution/search_seed_650001/gen_4/main.py) | `602d966b` | 2 | [0] / [3] | cross | Four after ≥5% checked improvement and compact/slow geometry; otherwise five | 2.008301 |
| [5](../../../artifacts/book_mpso_population_v1/20260916T183731Z/evolution/search_seed_650001/gen_5/main.py) | `4b2e46cc` | 3 | [0] / [2] | diff | Four after >5% refreshed loss and compact/slow geometry; otherwise five | 1.940724 |
| [6](../../../artifacts/book_mpso_population_v1/20260916T183731Z/evolution/search_seed_650001/gen_6/main.py) | `9d9563c1` | 0 | [4] / [2] | diff | Always six | 1.776112 |

The complete native UUIDs, source hashes and prompt checks are in
[the lineage receipt](../../../artifacts/book_mpso_population_v1/20260916T183731Z/operations/native-lineage-numerical-complete.json).
Generation six descends directly from the seed, with generations four and two as
archive/top inspirations. It was proposed natively, not manually inserted.

![Native population search](../../../assets/book_mpso_population_v1/native_search.png)

The saved generation-six prompt contains the full parent and inspiration sources,
their measured feedback, the frozen task context and a native meta recommendation.
For example, the seed feedback actually supplied includes:

> case_000 severity=1.0,period=5000: error=2.050730, deltatarget_3=+0.120001, deltatarget_5=+0.000000, deltatarget_7=-0.318497

Its paired regime summary identifies target five as the best tested fixed target,
mean 1.744569, with differences −0.061772 and −0.127089 from targets three/seven.
The exact injected meta recommendation includes:

> Try the unexplored neighboring constant `return 6`.

It distinguishes maintaining six from repeated switching under loss-triggered
expansion. Generation six implements that recommendation. This establishes actual
recommendation use; it does not identify a causal benefit of meta-memory. The
[actual prompt](../../../artifacts/book_mpso_population_v1/20260916T183731Z/evolution/search_seed_650001/gen_6/attempts/novelty_1/resample_1/patch_1/headless_prompt.md)
and all rejected proposals are archived. The [interim review](INTERIM.md) reports
what the first four descendants changed before the final two original slots.

The pinned native ShinkaEvolve revision is
`9912af12d423504b8d580f4179fd15f5f88b8c50`. The task-specific profile preserves weighted
parents, archive/top inspirations, diff/full/crossover probabilities 0.5/0.3/0.2,
embedding-plus-LLM novelty and meta-memory at five evaluated programs. One island
removes the preceding experiment's cross-island novelty separation; it does not prove
behavioral novelty. Migration is inactive. Mutation-model selection stays fixed and
prompt coevolution stays off; this is not an adaptive model ensemble.

The one-island search evaluated the seed and **six valid descendants**, with no
terminal failed slot. Eight proposals were generated: **five diff, one full rewrite,
and two crossover attempts**. Six were accepted (four diff, two crossover). The
full rewrite proposed the exact seed and was rejected; another diff repeated
constant four and was rejected. Both novelty decisions occurred before evaluation,
so neither consumed numerical queries. All proposal attempts remain archived.

Native execution recorded **nine local embedding requests**, **six accepted and two
rejected novelty decisions**, **two meta updates** and **one recommendation insertion**.
All eight saved attempt prompts contain the frozen scientific context; all 21
parent/inspiration references contain the actual source and measured feedback. There
was no novelty fallback or degraded mechanism. The first meta update summarized the
seed plus four descendants; its constant-six recommendation entered generation six. Generation five had already
been proposed before those recommendations became available. A closing update
summarized the final two programs. No migration occurred in the single island.
The existing **768-dimensional** embedding route
`local/jina-code-v2-q8@http://127.0.0.1:8910/v1` and its frozen threshold
**0.830958258366903** were reused unchanged; no calibration or model download was
repeated. [Final execution receipts](../../../artifacts/book_mpso_population_v1/20260916T183731Z/operations/native-accounting-summary.json)
retain role, context, novelty and meta evidence.

## Execution and model accounting

| Stage | New full executions | New objective queries | Exact reused case records |
|---|---:|---:|---:|
| Fixed-target controls | 16 | 8,000,000 | 8 historical target-five records |
| Native seed | 0 | 0 | Same eight compatible target-five records |
| Six descendants | 48 | 24,000,000 | 0 |
| Conditional fresh comparison | 0 | 0 | Not triggered |
| **Total** | **64** | **32,000,000** | **16 uses of eight prior cases** |

All planned executions reached the full horizon. There were **zero failed/partial
numerical cases, zero unaccounted queries and zero repeated full descendant cases**.
Seven terminal native slots comprise the seed and six valid descendants. Two rejected
proposals consumed ordinary native retries inside their original slots, not replacement
slots. The initial numerical ceiling was 96 / 48 million, reduced by exact baseline
reuse to 88 / 44 million; unused allowance was not filled.

Small implementation fixtures consumed **23,756 additional queries** across two
passes. The focused final regression passed **54 checks**; other checker/controller
fixtures used synthetic records and no objective calls. Independent saved-artifact
review checked all 80 control/native records, exact query accounting, paired landscape
hashes, case integrals, source selection, bootstrap values and population diagnostics.
These checks establish implementation/accounting fidelity, not an evolutionary gain.

| Native role | Requested logical responses | Wrapper calls |
|---|---:|---:|
| Mutation | 8 | 8 |
| Novelty judging | 8 | 8 |
| Meta-memory | 11 | 6 batched/single wrappers |
| **Total** | **27 / 36 limit** | **22** |

All requested responses returned; no exposed transport retry or paid fallback was
observed. Duplicate-proposal retries are already included in the mutation/novelty
counts. Receipt boundaries do not reveal provider-hidden retries or supervising use.

The native run spans **18:56:31–19:28:42 UTC (32m11s)**; its logged monotonic duration
is **1,804.35 seconds (30m04s)**. Both clocks are retained in
[the runtime record](../../../artifacts/book_mpso_population_v1/20260916T183731Z/operations/runtime-clock-record.json);
the **126.65-second discrepancy** is unresolved and is not silently corrected or
attributed to a guessed cause. The 120-minute overall ceiling uses conservative UTC.
Publication completion and full session elapsed time are verified separately after push.

One reference-controller launch dereferenced the virtual-environment Python link and
failed on missing NumPy **before a case started: zero queries**. Relaunching with the
correct virtual-environment path recovered it; no native controller restart or numerical
rerun occurred. There was no amendment to horizons, cases, policy semantics, fitness or
selection. The one-island profile change was explicit and prospective.

All internal model roles use subscription-authenticated Codex with `gpt-6-astra` and the
verified strongest pinned-route effort **xhigh**. Inner Ultra is unsupported by that route;
requested supervising Astra/Ultra is recorded separately and cannot be inferred from
native receipts. The native logical-response counter includes exposed role requests and
retries, but excludes supervising usage and unobserved provider-internal retries.
No paid API fallback, new model download or unrelated service setup occurred.

## Interpretation, limitations and next decision

**Retain target five and the published response in this chapter condition.** Native
search tested constant tuning and several state-dependent resizing rules, but none
improved development mean over the existing reference. The closest descendant was
a simple constant, and its small adverse mean concealed large opposing case effects.
The result does not establish that five is optimal or that adaptation is impossible.

The next justified experiment would test whether the fixed-target allocation tradeoff
changes in the chapter's **200-peak condition**, beginning with simple matched controls
before another adaptive search. That follows the chapter's concern about convergence
and coverage as population grows. It is a recommendation only: no new condition,
validation study or follow-on campaign was launched.

This bounded search cannot establish superiority of Shinka over another search procedure
or attribute any gain to one engine feature. The eight reused development histories can
support selection but cannot establish generalization. Known severity, synthetic conical
peaks, one chapter condition, the declared reconstruction conventions and a small native
batch bound what transfers. Accepted native programs requested only four, five or
six and did not use the available global workload or previous-target fields; the
negative result does not cover every permitted population policy. Historical V1–V3, radius/velocity and retention findings remain
unchanged; no historical campaign was rerun.

## Reproducibility and live inspection

Prospective implementation and settings were committed as
`aa89058e07cc301ff75c3c887b3a0588a685370b` before new research outcomes. The
[engine](../../../src/adaptive_swarms/book_population.py),
[evaluator](../../../tasks/book_mpso_population_v1/evaluate.py),
[task prompt](../../../tasks/book_mpso_population_v1/task_prompt.txt),
[task profile](../../../configs/shinka/book_mpso_population_v1.json) and
[selection freeze](../../../artifacts/book_mpso_population_v1/20260916T183731Z/selection.json)
record the exact contract and sources. The original chapter engine remains unchanged.

```bash
source .venv/bin/activate
python scripts/analyze_book_population.py \
  --run artifacts/book_mpso_population_v1/20260916T183731Z \
  --phase development --output /tmp/book-population-analysis
```

This regenerates analysis/figures from saved cases, with zero objective/model calls.
The native WebUI uses the actual new SQLite archive at
[localhost:8897](http://localhost:8897/viz_tree.html?db_path=search_seed_650001%2Fprograms.sqlite),
without replacing another viewer. From the repository root:

```bash
study_run=results/book_mpso_population_v1/20260916T183731Z
bash scripts/progress.sh "$study_run/evolution/search_seed_650001"
tail -F "$study_run/operations/run.log"
# Only if the existing viewer stops:
bash scripts/webui.sh "$study_run/evolution" 8897
```

Completed cases, accepted sources, attempts and terminal slots are durable. There
was no native-controller restart; the existing wrapper still does not restore native
proposal RNG state across a future process restart. Query heartbeats describe waiting
and saved progress, not token streaming or access to hidden reasoning. Publication
and remote-SHA verification are recorded separately from the scientific freeze.
