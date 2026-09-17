# Corrected 200-peak population campaign — Session 1

**Session 1 research is complete and cleanly paused: six of 50 descendant slots,
all six valid, and all seven constant-target controls complete.** Generation four
is the interim native leader. It improves development mean error over corrected
5+1 and every tested constant target, with no fresh confirmation or final winner
freeze. Research finished at 08:46:33 UTC, 113 minutes after the 06:53:25 start;
publication is part of the same 180-minute ceiling and has its own verified receipt.

- [Prospective protocol](../../book_mpso_population_200_v2_protocol.md)
- [Source-fidelity continuation](../../book_mpso_population_200_v2_source_record.md)
- [Final-analysis specification](analysis_specification.json)
- [Exact next-session procedure](RESUME.md)

The prior 200-peak archive and all historical experiments remain unchanged. The
corrected enclosing-ball engine uses the same four development histories but no
historical numerical score. Both corrected targets five/three are measured anew.

## Corrected controls

All eight corrected control executions completed their registered 500,000 queries:
**4,000,000 research queries**, with no historical-score reuse. The exact native
seed reuses the four source-identical corrected target-five records. The first
planned case took **100.59 wall seconds**; all control cases ranged **100.59–140.97
seconds**. Admission uses the maximum with a 35% margin, recorded model latency
and drain overhead; complete native evaluation timings can raise that reserve.

| Constant target | Case 000 | Case 001 | Case 002 | Case 003 | Mean |
|---|---:|---:|---:|---:|---:|
| Five / corrected 5+1 | 2.748324 | 1.921516 | 1.807639 | 2.287654 | 2.191283 |
| Three | 2.256459 | 2.208741 | 1.768793 | 2.132379 | 2.091593 |
| Three minus five | −0.491865 | +0.287225 | −0.038845 | −0.155274 | −0.099690 |

Target three's mean is 4.55% lower, with three wins and one loss. Its paired median
is −0.097060, SD 0.321609 and descriptive paired 95% bootstrap interval
[−0.378610,+0.176600]. Case 000 contributes −0.122966 to the net mean: without it,
the other three differences average +0.031035. Every case is retained. Four reused
development histories give an exploratory, selection-biased setting comparison,
not confirmation. No population rule has been frozen for fresh evaluation.

| Control | Mean total particles | Mean subswarms | Additions / removals | Ordinary queries | Permanent quantum | Detection | Memory |
|---|---:|---:|---:|---:|---:|---:|---:|
| Target five | 215.48 | 35.91 | 0 / 0 | 64.38% | 13.58% | 13.58% | 4.24% |
| Target three | 167.21 | 41.12 | 0 / 737 | 55.89% | 18.79% | 18.79% | 3.29% |

Population means use the saved 100-query grid, giving histories equal weight;
additions/removals pool histories. Target three requests three uniformly, reaches
three in 93.20% of subswarm updates and retains four/five during transitions and
births. It uses no state/history fields. Its smaller groups coincide with fewer
total particles, more subswarms and larger permanent-sampling/detection shares.
This differs from the earlier ten-peak allocation pattern. Neither swarm count
nor this joint change identifies peak coverage or an isolated causal mechanism.

## Native development finding: workload-adjusted loss hysteresis

All six Session 1 descendants completed all four histories. Generation four is the
**interim best executed native program**, including the seed in ranking. Its mean
error is **1.928740**, versus **2.191283** for corrected 5+1 (11.98% lower) and
**2.091593** for constant target three (7.79% lower). This is a conditional rule,
not a constant population target. It is not a frozen campaign winner.

```python
def choose_neutral_count(observation) -> int:
    """Choose two or three neutrals using workload-adjusted loss hysteresis."""
    # Estimate movement and detection queries per optimizer sweep.
    loss = max(0.0, observation["relative_fitness_drop"])
    swarms = max(1, observation["swarm_count"])
    sweep_queries = max(
        1.0, observation["total_particle_count"] + swarms
    )
    # Greater existing workload raises the evidence required for growth.
    recovery_pressure = loss / (1.0 + sweep_queries / 160.0)
    # History is supplied by the caller; no state is retained here.
    threshold = (
        0.04 if observation["previous_requested_target"] == 3 else 0.08
    )
    return 3 if recovery_pressure > threshold else 2
```

[Full unmodified source](../../../artifacts/book_mpso_population_200_v2/20260917T065325Z/session_001/evolution/search_seed_670001/gen_4/main.py),
SHA-256 `85a203cf0fdd5ba2c6a34cda2ec80133e84cb22bf821d36bafae99d48b0b475c`.
The inherited module heading outside the evolve block still describes the seed;
the function above is the executed rule. The saved source is preserved verbatim.

Let N be current total particles and M current subswarms. The rule divides the
positive relative deterioration of the old shared-best position by
`1 + (N + M)/160`. N+M is a workload proxy, not a measurement of every query in a
sweep: memory refresh, birth and exclusion can add work. It requests three if this
pressure exceeds 0.04 when the preceding target was three, or 0.08 otherwise;
it requests two below that threshold. The lower threshold for retaining three
implements hysteresis using the existing public history field. All requests still
pass through the unchanged one-step, detected-change-only adapter.

| Native generation | Executed rule | Mean error | Difference from 5+1 |
|---:|---|---:|---:|
| 0 | `return 5` (reused corrected seed) | 2.191283 | 0 |
| 1 | `return 3` | 2.091593 | −0.099690 |
| 2 | `return 2` | 2.080392 | −0.110892 |
| 3 | `return 4` | 2.181443 | −0.009840 |
| **4** | **Workload-adjusted loss hysteresis, targets 2/3** | **1.928740** | **−0.262543** |
| 5 | Also caps loss by deterioration remaining after memory refresh | 1.989777 | −0.201506 |
| 6 | Caps the workload proxy at 120 before normalizing loss | 2.057724 | −0.133559 |

Every descendant is valid; none failed, was replaced or remains partially ranked.
Generation one rediscovers the supplied target-three control exactly; its four
physical executions remain counted. Constants two/four provide useful settings,
but generation four improves further on these development histories. The later
conditional variants do not improve on generation four. No fresh histories were
generated or evaluated, and no candidate was revised from fresh outcomes.

| Paired history | Corrected 5+1 | Target three | Generation four | G4 − 5+1 | G4 − three |
|---|---:|---:|---:|---:|---:|
| 000 | 2.748324 | 2.256459 | 2.153475 | −0.594850 | −0.102985 |
| 001 | 1.921516 | 2.208741 | 1.939183 | +0.017667 | −0.269559 |
| 002 | 1.807639 | 1.768793 | 1.650449 | −0.157189 | −0.118344 |
| 003 | 2.287654 | 2.132379 | 1.971854 | −0.315800 | −0.160526 |
| Mean | 2.191283 | 2.091593 | 1.928740 | −0.262543 | −0.162853 |

Against 5+1, the paired median is −0.236495, SD 0.260052, with three wins and one
loss. The descriptive 95% paired-bootstrap interval is [−0.485435,−0.065700].
Case 000 contributes 56.64% of the net gain; removing it leaves a mean difference
of −0.151774. All four leave-one-history-out means remain negative, ranging
−0.355946 to −0.151774. Against three, all four cases improve; paired median
−0.139435, SD 0.075181, interval [−0.231755,−0.110664]. These are four-history,
selection-biased development intervals. Their exclusion of zero is not the
registered later 50-history confirmation and does not justify early finalization.

### What the rule makes the optimizer do

The rule requests two in 63.27% and three in 36.73% of detected-change decisions
(equal-history averages). Realized populations are two in 56.94% of subswarm
updates, three in 34.58%, four in 3.91% and five in 4.56%. New and replacement
swarms still start at five; four/five are transitional counts. Across four histories,
there are **1,582 additions, 2,503 removals, 3,199 requested-target switches and
2,921 reversals of nonzero resizing direction**. Both growth and shrinkage occur
within 302 recorded subswarm lifetimes. This repeatedly changes population;
it does not settle at a single constant target.

Requests differ within 99.75% of observed detected-change periods. The executed
source uses local deterioration, global particle/swarm counts and the preceding
target. Different realized sizes alone would be weaker evidence: births also
create temporary heterogeneity under constant targets. No particle transfers or
global population conservation occur.

| Method | Mean total particles | Mean subswarms | Movement queries | Detection + memory | Initialization/birth/exclusion |
|---|---:|---:|---:|---:|---:|
| Corrected 5+1 | 215.48 | 35.91 | 81.49% | 17.82% | 0.69% |
| Target three | 167.21 | 41.12 | 77.13% | 22.08% | 0.79% |
| Native constant two | 133.21 | 42.62 | 73.47% | 25.67% | 0.86% |
| Generation four | 93.26 | 26.41 | 75.62% | 23.09% | 1.29% |

For generation four, ordinary PSO consumes 53.10%, permanent quantum sampling
21.24%, temporary quantum response 1.29%, detection 21.24% and memory refresh
1.86% of all queries. The reference shares are 64.38%, 13.58%, 3.53%, 13.58% and
4.24%. Counts and query shares change jointly with convergence, exclusion and
birth/removal trajectories. Fewer subswarms do not establish poorer or better
peak coverage, and these records do not isolate hysteresis or a workload field as
the cause of the gain.

Recovery is measured at actual saved query offsets after changes, excluding
initialization and averaging periods within each history before histories. At
100, 500, 1,000 and 5,000 queries after change, generation four's mean discovered
errors are 4.731, 2.779, 2.247 and 1.249; corrected 5+1 gives 6.684, 2.946, 2.426
and 1.405. This supports improved average tracking on these histories while
retaining the unfavorable individual case and episodes.

![Population and tracking](../../../assets/book_mpso_population_200_v2/session_001/population_and_tracking.png)

Population and tracking use counted objective evaluations throughout. Solid
population curves count particles; dashed curves count subswarms on the labeled
right axis. Neutral bands describe population spread, not statistical uncertainty.
All four paired history outcomes remain visible.

![Favorable and unfavorable recovery episodes](../../../assets/book_mpso_population_200_v2/session_001/tracking_episodes.png)

The frozen example rule chooses the largest negative and largest positive
completed-period contribution, excluding initialization, with ties by case then
period. The favorable example is case 000/period 6 (30,001–35,000 queries),
mean-error difference −7.506815. The unfavorable example is case 001/period 2
(10,001–15,000), +10.931851. These are explicitly selected extrema, not frequency
estimates. Both come from planned executions; there are no illustrative replays.

The evidence supports three different statements: the executed rule lowers
matched development mean error; its state-dependent population behavior is
observed directly; native Shinka produced the rule from its recorded lineage and
feedback. It does not establish fresh generalization, superiority to another
search engine, or a causal benefit of one native engine feature.

## All seven constant-target controls

The measured runtime allowed the remaining registered controls to finish after the
native batch drained, within the same session. Evolutionary feedback stayed frozen
against targets three/five. Targets two/four reuse the pure constant native
generations two/three after structural equivalence, database, source/fingerprint,
paired-case and objective-accounting checks. Their compressed case bytes are
unchanged, and the eight original native physical attempts remain counted.
Only targets six/seven/eight add twelve further physical executions. This support
was committed as `dcd8386` before those new control outcomes. The registered
constant list, cases, horizon, sources and final-analysis plan did not change.

| Constant target | Case 000 | Case 001 | Case 002 | Case 003 | Mean |
|---:|---:|---:|---:|---:|---:|
| 2 | 2.290227 | 2.050520 | 1.723802 | 2.257017 | 2.080392 |
| 3 | 2.256459 | 2.208741 | 1.768793 | 2.132379 | 2.091593 |
| 4 | 2.349921 | 2.235428 | 1.792776 | 2.347646 | 2.181443 |
| 5 | 2.748324 | 1.921516 | 1.807639 | 2.287654 | 2.191283 |
| 6 | 2.763961 | 2.193985 | 1.958697 | 2.483343 | 2.349997 |
| 7 | 2.628220 | 2.322572 | 2.031650 | 2.427255 | 2.352424 |
| 8 | 3.157858 | 2.345415 | 2.356839 | 2.487131 | 2.586811 |

Target two is the development-leading constant, **2.080392**. Generation four is
7.29% lower, with paired differences −0.136753, −0.111337, −0.073353 and −0.285163:
four wins, mean −0.151651, median −0.124045, SD 0.092742, and descriptive 95%
interval [−0.241707,−0.089203]. Case 003 contributes 47.01% of this net difference;
all leave-one-history-out means remain negative (−0.177751 to −0.107148). This
interim comparison is selection-biased; it is not the future prespecified fresh
secondary test or an isolation of adaptation's causal value. All seven integer
constant targets permitted by this interface are now measured; fixed-size variants
initialized at those sizes are not part of this comparison.

Targets six/seven/eight shift ordinary PSO to 67.02%/68.97%/71.15% of queries.
Their mean subswarm counts are 33.36/31.07/26.70 and mean total particles
232.69/246.44/236.43. All three have worse mean error than corrected 5+1.
These coupled population/query-allocation changes are measurements, not separate
causal effects or peak-coverage counts.

## Repair, provenance and planned final analysis

The historical diameter criterion could accept an equilateral triangle with side
1.9*r even though its minimum enclosing radius exceeds r. The versioned engine
now checks the neutral-only enclosing ball using valid quick certificates and an
accurate ambiguous-case solver. Relative radius tolerance is 1e-12; the documented
inclusive boundary is a numerical convention. Geometry draws no randomness and
uses no objective queries. Neutral diameter remains the public pairwise-distance
observation. The permanent quantum role, PSO/UVD movement, retained velocities,
memory handling, known-scale radius, temporary conversion, asynchronous exclusion,
birth/removal and resizing adapter are otherwise unchanged.

The original source record, historical engines, completed studies and fourteen
README figures remain intact. The local author copy supports the p. 201 geometry
repair and p. 215 particle-count extension rationale. Table 6 lists 2.18 for this
MPSO condition while nearby prose says 2.12; neither is an exact reproduction
target. Contemporary paired comparisons use the corrected engine throughout.
This is one-condition MPSO research, not full chapter reproduction or SPSO testing.
The geometry also differs from the historical ten-peak studies, so differences
between those studies and this campaign cannot be attributed solely to peak count.

The prospective scientific commit was
`6bdcd9d` and persistence commit `31aabfe`, both before native outcomes. The
runtime-admission update was committed as `8b22597` before mutation. The new
scientific fingerprint, evaluator identity, native task mappings and immutable
snapshot prevent old-engine score reuse. Four development identities are reused;
new corrected trajectories are not four new independent benchmark histories.

The campaign remains **50 descendant slots**, with seed included in final selection.
All seven constant targets 2..8 must be compared before final selection; today’s
required controls are three/five. These are constant-target rules, with newborn
and replacement swarms always starting at five. The start-at-five and one-step,
change-only adapter constraints are our extension choices. They do not transfer
particles or conserve a global particle total.

After 50 terminal slots, select the minimum complete valid native development
mean, ties by earlier generation then source hash; independently select the best
constant, ties by lower target. A distinct native winner improving on seed permits
a later, separately launched comparison on **50 new paired histories**, after
freezing sources and analysis. If seed remains best, there is no seed-versus-itself
test. Fresh outcomes cannot enter mutation, novelty, meta-memory or selection.
The primary evolved-minus-5+1 contrast precedes the selected-constant secondary
contrast. The registered 95% percentile bootstrap uses 20,000 resamples and seed
2026091702, resampling whole histories. Periods within a history are not independent
replicates. No significance stopping or retuning from partial fresh outcomes.

## Native machinery and durable pause

The installed ShinkaEvolve version is 0.0.7 at pinned revision
`9912af12d423504b8d580f4179fd15f5f88b8c50`. The actual Codex child invocation was
observed with model `gpt-6-astra` and `model_reasoning_effort=xhigh`; native receipts
also report that fixed headless route. This is subscription authentication with
no paid API fallback. Native cost displays are estimates, not billing receipts.
Supervising Astra/Ultra was requested in the client; its exact client selection
is not programmatically exposed here and was not changed or inferred from inner
receipts. The native response counter excludes supervising usage and hidden
provider retries.

The campaign retains one island, weighted parents, archive/top inspirations,
diff/full/crossover probabilities 0.5/0.3/0.2, calibrated 768-dimensional local
embeddings with threshold 0.830958258366903, native embedding-plus-LLM novelty,
measured textual feedback and interval-five meta-memory. Prompt coevolution is
off; the mutation model is fixed. Migration is inactive with one island. Configured
mechanisms and actual observed uses are reported separately in the saved audit.

The first actual mutation request contains the complete seed source and paired
feedback, four-case/200-peak context, corrected enclosing-ball contract and public
workload/history fields. Generation two’s parent is generation one, with the seed
as archive inspiration. The first prompt precedes meta-memory recommendations;
recommendation insertion is checked separately after the scheduled update.

The observed batch used **19 logical responses**, all returned: six mutation,
six novelty and seven meta, across 15 native wrappers. Seven local embeddings and
six novelty decisions executed; all six proposals were accepted, with no novelty
fallback or feature-degradation event. Actual mutations were three diff, two full
and one crossover. Complete parent/inspiration source and feedback were verified
in all six saved attempt prompts. Generation four used generation two as parent,
with generations one/three as archive/top inspirations. Its gain preceded the meta
update and cannot be credited to that later update.

The interval-five update consumed the seed and generations one–four. Generation
six's prompt contains one saved recommendation verbatim. Generation five used the
native crossover format, which omits recommendation insertion. The final clean
pause has **five processed and two pending meta programs** (generations five/six),
seven valid database rows, and zero pending proposals/evaluations. SQLite integrity
and checkpoint digest/ID reconciliation pass; Python/NumPy sampler state is saved.
The additional terminal summary was suppressed. No native controller restart or
hidden replacement generation occurred. Native execution ran 07:22:03–08:24:36 UTC.

The manifest retains its original preflight effort fields. Its
`observed_native_model` annotation and
[observed-role record](../../../artifacts/book_mpso_population_200_v2/20260917T065325Z/session_001/operations/observed_model_settings.json)
separately establish the actual executed route; the pre-annotation manifest is
preserved. The requested experiments skill was not available under that exact
name; the pinned native `shinka-run` and `shinka-inspect` skills were read and used.

The compatibility layer atomically saves and validates summary, scratchpad,
recommendations/history, pending evaluated-program IDs and processed counts. It
reconciles IDs against the real database before proposing and explicitly fails on
corruption or missing/duplicated IDs. Clean pauses drain database persistence and
background meta/maintenance before saving Python/NumPy sampler state. Interval-five
meta remains active; the extra terminal summary is suppressed until campaign
completion. Accepted pending proposals and terminal failed slots retain their
identities. Session completion cannot freeze a final winner or launch fresh cases.

No-model tests verify round-trip state, pending IDs, actual pinned generation-zero
resume counters without seed reevaluation, next-generation continuation, session
response deltas, admission and finalization gates. Eighteen geometry checks include
84 random/degenerate clouds against an independent KKT reference. The single engine
integration fixture consumed **401 objective queries**, separately from research.
An unchanged legacy background-I/O thread fixture hung and was excluded after its
test process was interrupted; the other targeted compatibility checks passed.
No extra model calls were made to certify infrastructure.

There has been no native controller restart in this session. Persistence is
supported by focused tests and the real saved checkpoint; continuity of resumed
model output has not yet been observed. Restoring sampler state does not promise
identical LLM outputs or replay of an interrupted provider operation. Interrupted
numerical work preserves its full reservation and requires explicit recovery
review; completed cases are reused individually.

The [resume procedure](RESUME.md) supplies the exact next-session command, terminal
attachment and native-WebUI launch commands. No later session or fresh confirmation
is launched automatically.

## Session accounting and bounded recovery

| Quantity | Session 1 observed | Campaign ceiling |
|---|---:|---:|
| Terminal descendant slots | 6 | 50 |
| Valid / failed / pending descendants | 6 / 0 / 0 | Failed terminal slots consume allocation |
| Full-case physical attempts / completions | 44 / 44 | 400 attempts |
| Exact and conservative research queries | 22,000,000 / 22,000,000 | 200,000,000 |
| Logical native responses requested / returned | 19 / 19 | 400 (Session 1 delta cap 80) |
| Native wrapper invocations | 15 | Not the logical-response unit |
| Separate numerical fixture queries | 401 | Reported separately |

The 44 physical cases comprise 20 control cases and 24 descendant cases. There
are 56 saved method/case labels: 28 controls plus 28 native labels including seed.
Twelve labels are reuse: four exact corrected target-five records for seed, and
eight constant-control imports from already executed native programs. The native
constant-three rediscovery was physically evaluated; those four cases are not
retroactively removed from accounting. There were no interrupted research cases,
model retries exposed by the native receipts, or replacement slots.

The initial forecast used the first planned reference case and recorded native
latency, independently of scores. Six slots were the prospective session ceiling;
per-proposal admission and measured complete evaluations allowed all six to finish.
Control case times span 88.22–161.71 UTC seconds; the largest completed native
case was 168 seconds. The remaining-control admission reserved 2,841.6 seconds
against 4,052.8 seconds before the research cutoff, including a 35% case margin.
Those controls actually finished in about 20 minutes 41 seconds. The final nominal
remaining case-only forecast is 20.25 hours at the conservative control rate,
before exact future reuse and model/maintenance overhead; this is a planning
estimate, not a runtime guarantee or a requirement to finish the campaign today.

Fifty-five focused geometry, evaluator, controller and persistence checks pass,
with only the 401-query engine fixture making objective calls. A final aggregate
analysis process was killed with exit 137 while retaining every raw method at
once; memory pressure was suspected but no kernel OOM receipt was available.
Analysis was changed to retain the reference and one method at a time, then
completed from saved data. All previously successful method summaries, comparisons
and selected episodes match exactly. No case was replayed and the frozen analysis
settings did not change. This operational recovery is unrelated to optimizer
fitness. The unchanged legacy thread-test exclusion is disclosed above.

The session uses no additional scientific conditions, shortened horizons, SPSO
comparison or fresh histories. All earlier experiment archives, fourteen historical
README figures and the original hashed source record remain intact. The added
figures are measured 5D trajectories, with case-averaged neutral minima/maxima as
descriptive population bands. Neither this session nor the native pause closes the
prospective campaign as a final positive or negative result.

## Archive, attachment and next decision

The [session inventory](../../../artifacts/book_mpso_population_200_v2/20260917T065325Z/session_001/MANIFEST.json)
contains the immutable task snapshot, all completed case records, reference and
native attempt ledgers, exact source/lineage, model receipts, native database,
validated meta/RNG checkpoint, measured analyses and operational logs. The live
campaign remains at `results/book_mpso_population_200_v2/20260917T065325Z`.
The [publication receipt](../../../artifacts/book_mpso_population_200_v2_publication/session_001/PUBLICATION.json)
records the payload commit and verified remote SHA without a self-referential
commit hash in the research archive.

```bash
tail -F results/book_mpso_population_200_v2/20260917T065325Z/operations/run.log
bash scripts/progress.sh results/book_mpso_population_200_v2/20260917T065325Z/evolution/search_seed_670001
# Only if this viewer has ended and port 8899 is free:
bash scripts/webui.sh results/book_mpso_population_200_v2/20260917T065325Z/evolution 8899
```

[Native WebUI](http://localhost:8899/viz_tree.html?db_path=search_seed_670001%2Fprograms.sqlite)
was visually checked with seven programs, one island, generation four's actual
code and no reported browser errors. Other viewers were preserved. This browser
check and all report/figure work consume zero objective/model calls.

The evidence-based next decision is to resume the registered campaign from
**generation seven**, retaining this conditional rule and its measured controls,
then challenge the interim ranking through the remaining slots before any final
freeze. The exact next user-launched 180-minute command is:

```bash
.venv/bin/python -u scripts/run_population_campaign.py session \
  --run results/book_mpso_population_200_v2/20260917T065325Z \
  --minutes 180 --new-session --control-targets 2,4,6,7,8
```

Existing complete controls are checked/reused, not rerun. The session receives at
most six more slots and an 80-response delta; campaign limits remain 50 slots,
400 logical responses and 400 full-case attempts/200 million research queries.
No next session or fresh comparison has been launched automatically.
