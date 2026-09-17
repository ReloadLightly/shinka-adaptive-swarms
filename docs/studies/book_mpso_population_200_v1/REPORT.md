# 200-peak MPSO population allocation: runtime-constrained stop

**Bounded stop before native search, not a negative evolutionary result.** The first
already-planned target-five reference case completed its full 500,000-query horizon.
Its measured runtime did not support even the two-descendant version with the
required conditional fresh comparison and publication reserves inside the 120-minute
ceiling. No remaining control, descendant, fresh case or follow-on campaign was run.
The substantive optimizer-improvement question is therefore **unresolved**.

Run: `book_mpso_population_200_v1/20260917T025219Z`; prospective native search seed
**660001**, never used by a native run. [Protocol](../../book_mpso_population_200_v1_protocol.md)
· [Frozen suite](../../../configs/book_mpso_population_200_v1/development.json)
· [Runtime resolution](../../../configs/book_mpso_population_200_v1/runtime_resolution.json)
· [Analysis specification](analysis_specification.json)
· [Archive](../../../artifacts/book_mpso_population_200_v1/20260917T025219Z).

## Chapter question and unchanged intervention

Can an evolved population rule improve reconstructed chapter 5+1 MPSO when 200
peaks compete for a fixed objective-evaluation budget? Blackwell, Branke and Li
(2008) discuss local convergence versus maintaining multiple search groups and
identify adaptive within-subswarm population as future work. The preceding ten-peak
study found no improving descendant. Larger groups shifted queries toward ordinary
PSO with little change in average group counts; its accepted rules did not use
available global workload or previous-target fields. These motivate a different
condition without implying that adaptation must help.

The numerical engine, population adapter and public observation interface are
unchanged. Only `choose_neutral_count(observation) -> int` in 2–8 is evolvable.
All swarms begin at five neutrals plus one permanent quantum particle. Calls occur
after counted change detection and personal-best refresh, before movement. The adapter
moves at most one neutral toward the target, using the existing deterministic worst-memory
removal and velocity-only addition followed by its first counted quantum move.
Survivor states, permanent sampling, radius, retained velocities, published temporary
schedule, PSO equations, exclusion and group birth/removal remain fixed. This is
within-subswarm allocation, not particle transfers or a conserved global population.
The chapter's known-scale radius and neutral pairwise-diameter approximation remain
explicit reconstruction conventions; see [the source record](../../book_mpso_source_record.md).

## Prospective suite and controls

Four new seed pairs were generated before outcomes after reserving historical seed
values across roles. They remain frozen and were not selected or replaced by scores.
All use five dimensions, **200 conical peaks**, movement severity 1, period 5,000,
correlation zero, `nexcess=1` and exactly **500,000 objective queries**. Other settings
match the preceding reconstruction: domain [0,100], initial peak heights 50, height
range [30,70], width range [1,12], height/width severities 7/1, chi 0.729843788 and
c 2.05, unclipped particles and independent environment RNG. Trace interval is 100.

| Case | Environment seed | Optimizer seed | Execution status |
|---|---:|---:|---|
| 000 | 1371848574 | 1949644975 | Target 5 complete |
| 001 | 1024741923 | 1979149083 | Unexecuted |
| 002 | 1695455020 | 202638145 | Unexecuted |
| 003 | 463558677 | 734165703 | Unexecuted |

The two planned controls request five and three, both starting at five and resizing
by at most one step on each detected change. Target three is not a historical configuration
initialized at three. Its four cases were **not executed**. Ten-peak outcomes were
not reused. The intended native seed would reuse the four newly executed target-five
references, but only one reference exists and no native seed was submitted.

Prospective suite, task, analysis specification, controller and maximum limits were
committed as **`9c0c938` before the first reference case**. The new evaluator and task
context explicitly say four development cases, 200 peaks and controls three/five.
The complete adapter contract and permitted mathematics remain aligned.

## Measured runtime and bounded decision

The first target-five case ran from **02:57:56.707601 to 03:00:52.255028 UTC**:
**175.55 seconds UTC**, versus **149.15 seconds monotonic**. Both measurements are
retained. The 26.39-second discrepancy is unexplained; budgeting uses the larger
observed duration against the UTC task ceiling, rather than asserting a cause.
The case is retained as development case 000, not repeated as a timing fixture.

At resolution, **105.11 minutes remained** until 04:52:19 UTC. Projection uses
175.55 seconds per remaining full execution plus 20% numerical variation, native
latency allowance, fifteen minutes for publication, and three minutes for remaining
freezes/registration. For D descendants the native allowance is 300D + 300 seconds,
based on the prior six-descendant search's ~26.5 minutes of model-wrapper latency.
For two descendants, the prior first two mutation/novelty pairs plus largest meta
round took 573.49 seconds; adding 50% variation fits the reserved 900 seconds.
Closing meta-work is reserved even below the five-program update interval. Detailed
latency review raised the initial thirteen-minute minimum-model reserve to fifteen
minutes; the stop decision was unchanged and both resolution records are retained.

| Descendants considered | Maximum full executions | Remaining after measured case | Projected remaining minutes | Fits 105.11 minutes? |
|---:|---:|---:|---:|---|
| 6 | 44 | 43 | 203.97 | No |
| 4 | 36 | 35 | 165.88 | No |
| 2 | 28 | 27 | 127.80 | No |

Each projection reserves all twelve possible fresh executions as required. The
smallest plan needs **127.80 further minutes**, exceeding the remaining allowance
by **22.68 minutes**. This is a conservative feasibility estimate, not a measured
runtime for unexecuted cases. It uses timing and historical model latency only;
reference error did not set the allowance. The resolved allowance is **zero native
slots**, under the user's explicit stop-before-search contingency. We stopped the
reference stage after its single completed case instead of running an unrelated
control campaign, shortening horizons or discarding the fresh-comparison reserve.

## The one completed case: measured behavior, no comparison

There is no selected native program. The only executed rule is the exact reference:

```python
def choose_neutral_count(observation) -> int:
    return 5
```

[Exact executed reference source](../../../artifacts/book_mpso_population_200_v1/20260917T025219Z/programs/target_5.py).
It requests five uniformly, ignores workload/history, and makes **zero additions,
zero removals and zero resizing reversals**. All **3,422** detected decisions request
five. The permanent sampling particle remains present in every group.

| Single-case observation | Value |
|---|---:|
| Counted evaluations | 500,000 |
| Offline error | 2.586442550 |
| Final current error | 1.894108847 |
| Mean total particles on the 100-query grid | 209.6328 |
| Mean subswarms on that grid | 34.9388 |
| Sampled subswarm range | 2–53 |
| Ordinary movement queries | 322,967 (64.5934%) |
| Temporary quantum queries | 17,110 (3.4220%) |
| Permanent quantum queries | 68,015 (13.6030%) |
| Detection queries | 68,016 (13.6032%) |
| Memory refresh queries | 20,532 (4.1064%) |
| Initialization / birth / exclusion queries | 6 / 1,890 / 1,464 (0.6720% combined) |

Mean populations are query-grid summaries of one trajectory, not independent samples
or four-case means. The change in total particles comes entirely from the unchanged
swarm birth/removal and exclusion dynamics, with six particles per group. Group count
does not reveal how many distinct peaks were covered, specialization or cooperation.
The single offline-error value is not compared to the ten-peak mean or a printed
chapter score as evidence of improvement.

![Single planned reference case: population and tracking](../../../assets/book_mpso_population_200_v1/population_and_tracking.png)

*Measured 5D/200-peak target-five case 000 only, against counted objective evaluations.
This is an unranked partial reference stage, not a complete control or evolutionary
comparison. The full recorded horizon, including deteriorations, is retained. No
additional simulation replay was used.*

Target-three differences, evolution's effect, favorable/unfavorable paired episodes,
case influence, development uncertainty and a fresh comparison are **unavailable**.
No bootstrap interval is estimated from one case or from its particle/episode samples.
The fresh trigger was not assessed; it was neither met nor rejected by an evolutionary
result. No protected identities were generated.

## Accounting, machinery and checks

| Stage | Full executions | Objective queries | Status |
|---|---:|---:|---|
| Target-five reference | 1 | 500,000 | Case 000 complete; three unexecuted |
| Target-three reference | 0 | 0 | Four unexecuted |
| Native seed / descendants | 0 | 0 | Not started |
| Fresh comparison | 0 | 0 | Not started; no identities generated |
| Small fixtures | 0 numerical fixtures | 0 | Synthetic configuration/controller checks only |
| **Total** | **1** | **500,000** | **Bounded stop before search** |

There are **zero terminal native slots, zero valid descendants and zero native logical
responses** (mutation 0, novelty 0, meta 0), zero native embedding calls, no failed or
partial numerical cases and no unknown queries. The 36-response ceiling was unused.
Supervising use is outside the native counter; provider-hidden retries are not exposed.

The installed Shinka revision was verified as
`9912af12d423504b8d580f4179fd15f5f88b8c50`. Subscription authentication and the existing
local 768-dimensional Jina embedding service were ready. The committed one-island
profile retains weighted selection, archive/top inspirations, diff/full/crossover,
embedding-plus-LLM novelty, meta-memory, fixed model and prompt coevolution off;
migration is inactive. **None of those native search mechanisms executed in this run.**
No parent/inspiration or recommendation-insertion claim can therefore be made.

The configured internal route is subscription **`gpt-6-astra/xhigh`** (supported by
the pinned route, not inner Ultra). There were no actual internal model invocations.
Supervising Astra/Ultra was requested but its actual label is not independently exposed.
No paid API fallback or global settings change occurred. Preflight records and the
runtime decision distinguish configuration, readiness and actual execution.

**25 focused synthetic checks passed**, covering changed configuration, two controls,
exact seed compatibility, paired accounting, recovery and complete-only selection.
No validated adapter rerun or numerical testing campaign was added. The saved completed
case was separately checked for its full budget, category sum, environment-integrated
error, fixed-five decisions, permanent-role handling and population diagnostics.
Prospective controller tests use synthetic records, not new objective queries.

## Benchmark coverage, limitations and decision

| Chapter condition | Chapter-aligned repository evidence |
|---|---|
| Ten peaks, severity one | Completed schedule and population searches, eight development cases each |
| 200 peaks, severity one | This four-case registered extension; **one target-five case measured, native search unexecuted** |
| Ten peaks, severity five | Untested by chapter-aligned search |
| 200 peaks, severity five | Untested by chapter-aligned search |

This adds a reproducible 200-peak suite, task context, one measured full-horizon
reference and runtime evidence to the chapter comparison. It adds **no evidence
for or against evolutionary improvement** in that condition. It is not a complete
chapter reproduction, a fifty-run comparison or an SPSO comparison. Numerical
conventions, known movement scale and the unresolved clock discrepancy limit the
feasibility estimate and interpretation. Historical negative findings and all
existing README figures remain preserved.

**Next decision:** arrange a separate, longer execution window before considering the
two-descendant option with the frozen suite; preserve this completed case and remeasure remaining
allowance against the recorded runtime. The present conservative projection needs
about 128 additional minutes including the conditional comparison and publication.
No continuation or new campaign was automatically launched.

## Inspect and reproduce the saved evidence

```bash
cd ~/actir/shinka-adaptive-swarms
study_run=results/book_mpso_population_200_v1/20260917T025219Z
tail -n 80 -F "$study_run/operations/run.log"
# Saved-data analysis only: no objective/model calls.
MPLCONFIGDIR=/tmp/book-population-200-mpl .venv/bin/python \
  scripts/analyze_book_population_200.py --run "$study_run" \
  --allow-partial --output /tmp/book-population-200-stop
```

No new native database exists, so no WebUI instance was created for this stopped
study. The existing viewers were not disturbed; port 8899 was checked free. For a
separately authorized continuation **after an actual database exists**, its native
attachment command is `bash scripts/webui.sh "$study_run/evolution" 8899`, with
`http://localhost:8899/viz_tree.html?db_path=search_seed_660001%2Fprograms.sqlite`.
That is a dormant command, not a currently available database or a launched search.

The immutable archive preserves the completed checkpoint, timing, exact sources,
prospective settings, audit and measured figure. Publication and the verified remote
SHA are recorded separately after archive closure, avoiding self-referential hashes.
