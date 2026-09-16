# Can evolution improve the chapter's MPSO diversification schedule?

**Completed bounded study, 16 September 2026. No distinct evolved schedule improved
on either matched reference's mean development error.** The published MPSO 5+1
seed remained the best native program: **1.744569**, versus **1.743485** for
reconstructed 5+0. Their paired difference is **+0.001084**, descriptive 95%
interval **[−0.306345,+0.285559]**, with four wins and four losses. The search
found no improving rule in this batch; this does not establish optimality of
the published schedule or equivalence of the two references.

Native evolution evaluated eight valid descendants, comprising seven distinct
behaviors. Longer, weaker and locally gated temporary-conversion schedules all
had worse mean development error. A cross-island duplicate was evaluated and
remains counted. Because the original seed won, the declared fresh-comparison
condition was not met: **no fresh case identities or duplicate comparison were
generated**. The selected function is the original schedule, not a discovery.

Run: `book_mpso_schedule_v1/20260916T154109Z`; search seed **640001**.
[Protocol](../../book_mpso_schedule_v1_protocol.md) · [Four-slot review](INTERIM.md) ·
[Complete archive](../../../artifacts/book_mpso_schedule_v1/20260916T154109Z) ·
[Frozen selection](../../../artifacts/book_mpso_schedule_v1/20260916T154109Z/selection.json).

## Scientific question and source

Can native ShinkaEvolve improve Blackwell, Branke and Li's temporary diversification
schedule within an otherwise fixed cooperative MPSO? This compares complete optimizer
methods. It neither isolates cooperation against independent search nor compares
all algorithm families in the chapter.

We read the author-hosted chapter, *Particle Swarms for Dynamic Optimization Problems*
(2008), especially §4.1, §4.2/Algorithm 3, §5.1 and §5.3/Table 3. The
[source-to-implementation record](../../book_mpso_source_record.md) documents its
anchors and reconstruction conventions. Table 3 reports 5+0 at **1.80 (SE 0.08)**
and 5+1 at **1.73 (SE 0.08)** for `nexcess=1`, across 50 runs of 500,000 evaluations.
Those are historical context; other settings and SPSO appear in the chapter.
No implementation choice was tuned to reproduce this ranking or its printed scores.

Both new references have five fixed neutral-role particles. Reference 5+1 adds one
permanent quantum-role particle, which samples at every update. The published
schedule temporarily converts all five neutrals on the update whose counted check
detects change, and none otherwise. Quantum sampling is uniform by volume around
the current shared best, radius **0.5 × severity**, and replaces the PSO step.
Neutral velocity survives for later ordinary updates. Every personal best,
including that of the permanent quantum particle, participates in change refresh
and subsequent shared-best discovery.

The new shared engine applies exclusion after each subswarm update, unlike the
historical all-swarms-then-exclusion path. It processes five neutral identities
before the permanent quantum role, updates attractors asynchronously, and
initializes new or excluded swarms with counted queries. Convergence uses only
neutral positions and retains the documented maximum-pairwise-distance approximation
to the chapter's smallest-enclosing-ball definition. No exact geometry claim is made.
DEAP initialization, unbounded particle positions, birth/removal conventions and
exact-budget termination are documented. Historical simulators and completed scores
remain unchanged; adding the missing reference is implementation work, not evolution.

## Frozen experimental design

The new task is `book_mpso_schedule_v1`. Evolution changes only
`choose_temporary_quantum_count(observation) -> int` in `[0,5]`, called each subswarm
update after counted detection and any memory refresh and before movement. Radius,
retained velocity, memory reevaluation, PSO coefficients, permanent role count,
structural membership, exclusion, birth/removal and accounting remain fixed.

Public information includes the current counted detection flag, observed fitness
changes, age since this swarm detected change, neutral geometry and motion, previous
count and known default radius. It excludes hidden peaks, optimum, benchmark error,
future changes, seeds and evaluator internals. A dedicated task RNG draws a full
permutation of neutral indices every update regardless of count; the first `k`
receive quantum moves. It is separate from movement and landscape RNGs. Pairing
preserves environmental histories, not identical future perturbations or decisions.

Eight recorded development seed pairs were generated before outcomes. Each case
uses five dimensions, ten conical peaks, peak domain `[0,100]^5`, severity one,
period 5,000, correlation zero, `nexcess=1` and exactly **500,000 counted queries**.
Pinned DEAP Scenario 2 initializes heights at 50 and samples widths and locations;
height and width ranges are `[30,70]` and `[1,12]`, with change severities 7 and 1.
These conventions are declared, not claimed to reconstruct unknown historical seeds.

Offline error averages the current optimum minus the best discovered value since
the latest environment change over every query. All initialization, detection,
memory, ordinary, temporary/permanent quantum, birth and exclusion evaluations count.
Boundary evaluations belong to the old environment. Trace interval 100 provides
actual recorded recovery offsets without separate replay. Each completed case is
saved independently with its configuration, environment hashes and query categories.

The prospective implementation and analysis were committed at
`383eea9204ab5f143751f9c1358cf35f546bfd92`. The exact 5+1 source supplies the native seed,
with its eight source/task/configuration-compatible cases reused. Native search is
limited to eight descendant slots; terminal failures consume slots. Fitness remains
`1/(1 + mean offline error)` without bonuses for branching or complexity. Selection
includes the seed and breaks equal mean error by earlier generation, then source hash.

The [analysis specification](analysis_specification.json) froze before evolution:
equal independent case weights, **20,000 paired-case bootstrap resamples**, seed
**2026091608**, descriptive 95% percentile intervals, and all case outcomes retained.
Development uncertainty does not correct selection bias. Fresh case pairs are only
generated after source/analysis freezes when a distinct descendant improves on the
seed. Particle updates and environment episodes are not independent replicates.

## Reference measurements before evolution

New development means were **1.743485 for 5+0** and **1.744569 for 5+1**. The paired
5+1-minus-5+0 mean is **+0.001084**, median **+0.032693**, SD **0.453496**, with
descriptive interval **[−0.306345,+0.285559]** and four wins/four losses. The mean
does not recover the historical ranking; the small paired suite does not establish
equivalence either. All declared implementation conventions remained fixed.

Both original schedules request five temporary conversions only on detected-change
updates. Their equal-case fractions of neutral updates converted were **1.0364%**
(5+0) and **1.2074%** (5+1), because their reached states and detected updates differ.
Across 5+1's four million development queries, permanent quantum updates used
**546,686 queries** and registered **44,666 shared-best improvements**. These
measurements establish that the additional role executed and contributed discoveries;
they do not measure its isolated causal value or explain the nearly equal mean.

The first already-planned full 5+0 case completed in **14.89 seconds** and remained
in the reference checkpoint. Its error was **2.212450**. This throughput supported
the original bounded search without shortening the chapter horizon. The local code
embedding service was reused without downloading or recalibrating a model.

## Retained executable and all matched outcomes

The exact frozen selected source has SHA256
`c1ec64da1e05a1c1b9181e9a58e30600a97499f4ea28912d703fa251c668a284`:

```python
"""Published MPSO 5+1 temporary-conversion schedule."""

# EVOLVE-BLOCK-START
def choose_temporary_quantum_count(observation) -> int:
    return 5 if observation["change_detected"] else 0
# EVOLVE-BLOCK-END
```

The [selected file](../../../artifacts/book_mpso_schedule_v1/20260916T154109Z/programs/selected.py)
is byte-identical to the native seed and the standalone reference schedule.
The 5+0 and 5+1 reference functions share this source, but their explicit
permanent-quantum modes differ: zero versus one. They are not execution aliases.
Selected and 5+1 share both source and mode and **are** an exact alias. No
selected-minus-5+1 difference or interval is interpreted as fresh evidence:
it is identically zero because these are the same method.

Selection froze at **16:39:34 UTC**, after native search completed. The function
requests five temporary quantum moves on current counted detection and zero
otherwise. Five fixed neutrals then return to ordinary PSO; the permanent
quantum role continues sampling. All memories survive and are refreshed.

### Complete development pairs

Selected native program is the published 5+1 seed; it is not a third distinct method.

| Case | 5+0 | 5+1 (selected seed) | 5+1 − 5+0 |
|---|---:|---:|---:|
| 000 | 2.212450 | 2.050730 | -0.161720 |
| 001 | 1.713591 | 2.232646 | +0.519055 |
| 002 | 1.859831 | 2.270948 | +0.411117 |
| 003 | 0.977286 | 0.847983 | -0.129303 |
| 004 | 1.508322 | 1.903934 | +0.395612 |
| 005 | 2.003133 | 1.295917 | -0.707216 |
| 006 | 1.491013 | 1.685701 | +0.194688 |
| 007 | 2.182251 | 1.668691 | -0.513560 |

5+1 minus 5+0: mean +0.001084; median +0.032693; SD 0.453496; descriptive 95% interval [-0.306345, +0.285559]; 4 wins / 4 losses / 0 ties.


Every pair has identical configuration, 500,000 counted queries and **101 matching
landscape hashes**, including the generated but unevaluated final boundary.
These are eight independent histories in one regime, not 800 independent change
episodes. The complete per-case seeds, traces and errors remain in the archive.

The very small mean conceals cancellation. Case 005 contributes **−0.088402** to
the pooled 5+1-minus-5+0 mean; case 001 contributes **+0.064882**. Leave-one-case-out
means range **[−0.072912,+0.102270]**. The largest absolute completed-environment
contribution is case 006/environment 4: **+16.440294** environment mean error,
contributing **+0.020550** to the overall paired mean, about 19 times its near-zero
net value. In the same case, environment 31 contributes a **−10.092263**
environment difference. No case or event was removed. The full decomposition
is descriptive, not a change in the independent resampling unit.

![Measured paired performance and actual schedule behavior](../../../assets/book_mpso_schedule_v1/schedule_and_performance.png)

*Five-dimensional measurements; eight development histories per program. The
selected program aliases 5+1, so there is no invented third method. The heatmap
shows actual mean requested counts by observed age since each swarm's detection.
Both published temporary schedules coincide; only 5+1 has the permanent role.
Recovery uses actual recorded offsets and equal case weights. Generation 8
repeats generation 6, and both physical executions remain visible.*

## What native evolution actually tested

| Generation | Executed behavior | Mean error | Difference from seed | Better / worse cases | Neutral conversions |
|---|---|---:|---:|---:|---:|
| 0 | Published: 5 on detection, 0 otherwise | 1.744569 | +0.000000 | 0 / 0 | 1.2074% |
| 1 | 5 on detection; 2 on each next three updates | 1.902573 | +0.158004 | 3 / 5 | 2.6039% |
| 2 | 5 on detection; 2 at age one only when preceding improvement is zero | 1.813739 | +0.069170 | 4 / 4 | 1.2454% |
| 3 | 3 on detection, 0 otherwise | 1.919122 | +0.174553 | 1 / 7 | 0.7064% |
| 4 | 3 on detection; 1 on each next two updates | 1.970515 | +0.225946 | 2 / 6 | 1.1522% |
| 5 | 5 on detection; 1 on each next two updates | 2.040693 | +0.296124 | 4 / 4 | 1.6540% |
| 6 | 4 if absolute relative observed change ≤0.01, otherwise 5; detection only | 2.092992 | +0.348423 | 2 / 6 | 1.1827% |
| 7 | 4 on detection, 0 otherwise | 2.126656 | +0.382088 | 2 / 6 | 0.9302% |
| 8 | Same decisions as generation 6; reordered guard | 2.092992 | +0.348423 | 2 / 6 | 1.1827% |

Percentages describe equal-case fractions of neutral updates assigned quantum
movement; terminal partial updates are separately represented in the saved
executed fraction. Every valid program has eight full-horizon case outcomes.
All 72 native case records, including eight cached seed records, are retained.

Generation 2 was the closest modification, still worse by **+0.069170** on
average. Its count-two exception occupied **0.0925% of all updates**. Generation
1's large loss in case 004 (**+1.427936**) would reverse its aggregate effect if
removed; it stays included. These observations illustrate why a plausible
conditional expression is not sufficient evidence of a useful recovery mechanism.
The [four-slot interim](INTERIM.md) records the actual decision to finish the
remaining original slots, with no evaluator change, handcrafted offspring or
p-value gate.

Generation 6's rare intensity gate needs careful interpretation. Count four
occurred on **3.3047% of detected-change decisions**, with per-case frequencies
2.60–4.88%. Negative previous shared-best quality occurred on **3.2215%** of
count-four decisions versus **9.5388%** of count-five decisions, with equal case
weight. Median neutral diameter/default-radius in count-four states ranged
**0.0114–0.1377** across cases. Thus this gate often acts on compact swarms and
did not preferentially select negative-quality states. It responds to a **local
observed fitness difference**, not the benchmark's true movement severity,
which is one everywhere. These saved-data descriptions are post hoc behavioral
context, not a measured causal mediator; see the
[trigger summary](../../../artifacts/book_mpso_schedule_v1/20260916T154109Z/analysis/gen6_trigger_behavior.json).

### Decision examples and measured contributions

Examples were chosen before examining outcomes: first update, first detected
change, and first updates at or beyond quarter, half and three-quarter query
budgets. In 5+1 case 000, the first update at query **7** uses five ordinary
moves and one permanent quantum sample. The first detected response is decided
at query **5,012**, after the query-5,006 detection and six memory reevaluations.
It makes five temporary plus one permanent quantum update; the shared-best
fitness rises from **48.607631 to 49.491020**. Sample distances from each current
center lie between **0.4255 and 0.4811**, within the fixed radius 0.5; neutral
velocities are retained.

The prechosen three-quarter example at query **375,011** uses the same six
quantum moves but produces **no immediate shared-best improvement**, retaining
55.098517. Subsequent global best-discovered errors in these two examples are:

| Prechosen decision | First saved sample ≥100 queries later | Error | First saved sample ≥500 queries later | Error |
|---|---:|---:|---:|---:|
| First detection, query 5,012 | Actual offset 188 | 5.829460 | Actual offset 588 | 5.648834 |
| Three-quarter budget, query 375,011 | Actual offset 189 | 4.867965 | Actual offset 589 | 3.022116 |

Other swarms and updates intervene. These are recorded subsequent recoveries,
not isolated causal effects of one local decision. The complete prospective
examples and both post hoc favorable/unfavorable environment extremes remain
saved, so interpretation does not depend on selecting attractive illustrations.

![Measured ordinary and quantum contributions](../../../assets/book_mpso_schedule_v1/schedule_contributions.png)

*Counts and summed gains are attributed to the update that improved an existing
finite shared best; initial creation and memory refresh are excluded from these
movement contributions. Query-normalized summaries give cases equal weight.
They do not identify an independent causal benefit of a movement category.*

## Actual native lineage and feedback

The selected seed has no parent. Its native ID is
`54ff2a7f-b967-4211-982d-ac6df00a415f` on island zero; native initialization also
places the identical seed on island one as
`59433c06-18b3-4d5d-85d6-4c86e6655b66`. That copy is neither another generation
slot nor another numerical evaluation. The ten database rows therefore represent
nine evaluated slots. The actual evaluated descendant lineage is:

| Generation | Native ID | Island | Parent generation | Archive inspiration generations | Top inspiration generations | Patch |
|---|---|---:|---:|---|---|---|
| [1](../../../artifacts/book_mpso_schedule_v1/20260916T154109Z/evolution/search_seed_640001/gen_1/main.py) | `fefe4a5d-1838-4e21-b765-efe051d5f939` | 1 | 0 | — | — | diff |
| [2](../../../artifacts/book_mpso_schedule_v1/20260916T154109Z/evolution/search_seed_640001/gen_2/main.py) | `4db962bb-6988-4649-bcb2-d3411f25f8d3` | 1 | 0 | 1 | — | cross |
| [3](../../../artifacts/book_mpso_schedule_v1/20260916T154109Z/evolution/search_seed_640001/gen_3/main.py) | `e9041f37-b744-4937-a514-5059463380e1` | 1 | 0 | 1 | 2 | full |
| [4](../../../artifacts/book_mpso_schedule_v1/20260916T154109Z/evolution/search_seed_640001/gen_4/main.py) | `7e40065d-f7a4-4c95-9455-6cd890bb067e` | 0 | 0 | — | — | diff |
| [5](../../../artifacts/book_mpso_schedule_v1/20260916T154109Z/evolution/search_seed_640001/gen_5/main.py) | `21924dd0-082b-477d-abc0-c0b09bb67b57` | 0 | 0 | 4 | — | cross |
| [6](../../../artifacts/book_mpso_schedule_v1/20260916T154109Z/evolution/search_seed_640001/gen_6/main.py) | `0d79bea7-253f-4892-8a09-5b70b51636fe` | 0 | 0 | 5 | 4 | diff |
| [7](../../../artifacts/book_mpso_schedule_v1/20260916T154109Z/evolution/search_seed_640001/gen_7/main.py) | `50376b8d-89fa-4893-b275-5237f52b77f6` | 0 | 4 | 0 | 5 | diff |
| [8](../../../artifacts/book_mpso_schedule_v1/20260916T154109Z/evolution/search_seed_640001/gen_8/main.py) | `7fc83e10-4f74-47b9-b2fa-2f14e5fe7d7a` | 1 | 2 | 3 | 0 | full |

All **21 source/feedback references in nine saved mutation prompts** were
verified against the actual parent and inspiration identities. The ninth
prompt is a retry within slot 8, not an extra generation. For example, both
actual generation-2 and generation-3 prompts include generation 1's unfavorable
feedback:

```text
case_004 severity=1.0,period=5000: error=3.331870,
delta5+0=+1.823548, delta5+1=+1.427936;
interval-end error=2.7394387174541066; incomplete responses=0.
```

The saved [generation-2 prompt](../../../artifacts/book_mpso_schedule_v1/20260916T154109Z/evolution/search_seed_640001/gen_2/attempts/novelty_1/resample_1/patch_1/headless_prompt.md)
contains the original line, complete sources, paired outcomes and behavioral
feedback. Per-case raw summaries are verbose; the evidence is what was actually
supplied, not a claim inferred from configuration flags.

Native meta-memory performed two updates, generating nine individual program
summaries plus two global summaries and two recommendation responses. Three
actual mutation prompts received verified recommendations, in generations 6,
7 and 8. The first update suggested reducing the burst when absolute relative
observed fitness change is at most 0.01; generation 6 implements that hypothesis.
Its poorer score neither identifies a harmful effect of meta-memory nor proves
that all fitness-dependent schedules fail. No engine-feature ablation was run.

### Novelty filtering worked locally and missed a cross-island duplicate

Native embeddings and judging accepted eight proposals and rejected one, with
no fallback. Slot 8 first proposed an exact copy of generation 7. Similarity
was **1.0**, and the native judge returned `NOT_NOVEL` before any objective
execution. The normal retry then used parent generation 2 on island one,
with generation 3 as archive inspiration and the seed as top inspiration.
Its differently written function is logically equivalent to generation 6.

The [native-source and prompt audit](../../../artifacts/book_mpso_schedule_v1/20260916T154109Z/operations/novelty-cross-island-duplicate.json)
shows why: the native novelty pool is restricted to the parent's island. The
retry was compared against generation 2 on island one, while equivalent
generation 6 existed on island zero. The supplied pair was meaningfully
different; the other-island equivalent was outside the comparison pool. Thus
this is a **cross-island duplicate-detection limitation**, not evidence that
the LLM rejected or accepted a pair it never saw.

All eight complete generation-8 outcome dictionaries exactly equal generation
6's. These are **eight repeated physical executions / four million queries**,
not exact cache reuse and not an additional distinct behavior. They remain in
the original eight-descendant allowance. No compensating generation was added.

![Actual native development search](../../../assets/book_mpso_schedule_v1/native_search.png)

## Model, machinery and resource accounting

Pinned native ShinkaEvolve revision:
`9912af12d423504b8d580f4179fd15f5f88b8c50`. The named task profile retains weighted
parent sampling, two islands, archive and top inspirations, diff/full/crossover
probabilities 0.5/0.3/0.2, three novelty attempts and meta updates every five
programs. Prompt co-evolution is off and mutation-model selection is fixed.
Shinka's islands contain candidate programs; they are not the numerical MPSO
subswarms. Actual evaluated patch types were four diff, two full and two crossover.

The reused local route is
`local/jina-code-v2-q8@http://127.0.0.1:8910/v1`, with **768-dimensional** vectors
and the previously frozen threshold **0.830958258366903**. Ten embeddings
completed: the seed and nine proposal attempts. No model download or calibration
campaign was added. Native migration was configured at fraction 0.1 every ten
generations, but **zero migrations** occurred in this nine-slot study.

| Internal role | Native wrappers | Requested logical responses | Usable responses |
|---|---:|---:|---:|
| Mutation | 9 | 9 | 9 |
| Novelty judging | 9 | 9 | 9 |
| Meta-memory | 6 | 13 | 13 |
| **Total** | **24** | **31 / 40 ceiling** | **31** |

All roles used subscription `headless/codex@gpt-6-astra?effort=xhigh`.
Process observations matched each role's prompts and verified CLI arguments
`--model gpt-6-astra` and `-c model_reasoning_effort="xhigh"`. The pinned route
supports xhigh but not inner Ultra; requested supervising Astra/Ultra is
recorded separately. The manifest retains its earlier preflight effort-status
text, so later CLI observations and receipts are the actual invocation evidence.
Native client temperature/token-limit fields are not assumed to have been
forwarded to Codex. Native dollar fields are estimates, not paid API charges.

There were **zero exposed transport retries**, unclosed wrappers, response
shortfalls or degraded-mechanism events. The extra mutation/judgment pair was
a visible novelty retry within slot 8. Provider-internal retries and supervising
usage are unobserved by this native counter. Waiting heartbeats indicate waiting,
not model-token streaming or access to hidden reasoning.

| Stage | Completed case records | New physical full executions | New objective queries |
|---|---:|---:|---:|
| Two development references | 16 | 16 | 8,000,000 |
| Native seed | 8 | 0 | 0; exact compatible reuse |
| Descendants 1–7 | 56 | 56 | 28,000,000 |
| Descendant 8, behavior-equivalent repeat of 6 | 8 | 8 | 4,000,000 |
| Fresh comparison | 0 | 0 | 0; selection condition not met |
| **Total** | **88** | **80** | **40,000,000** |

The physical total includes 72 distinct method/case executions and eight
repeated executions. There were no failed, truncated or unknown-count research
attempts. Nine terminal native slots contain the seed and eight valid
descendants; seven descendant behaviors are distinct. The initial planning
maximum was 104 executions / 52 million queries. No numerical budget or horizon
was shortened and no additional search was started.

Native execution ran **16:04:28.754–16:37:41.059 UTC**, **33 minutes 12.3 seconds**.
Its logger reports **31 minutes 19.6 seconds** elapsed; both time bases are
retained rather than silently conflated. The discrepancy's cause is unverified.
The session began **15:41:09 UTC** and the scientific archive closed at
**16:46:52 UTC**, **65 minutes 43 seconds** later, including implementation,
execution, interpretation and report preparation. GitHub publication follows
that archive closure within the registered 180-minute ceiling. The [accounting record](../../../artifacts/book_mpso_schedule_v1/20260916T154109Z/accounting.json)
and operations logs retain phase and session timestamps; the publication
verification record separately timestamps the remote commit checks.

Focused small fixtures are separate from the 40-million research budget.
The initial engine checks consumed **20,798 queries** across two invocations;
the first invocation included a test-path typo, corrected before research.
Task/checkpoint/freeze and analysis checks also used synthetic, zero-query
fixtures. The final regression passed **52 focused checks** after a zero-query
synthetic fixture correction; total small numerical fixtures consumed **32,297
queries**, including all preparation and regression invocations. These counts
come from recorded executions, not a test-count estimate. The
[independent scientific review](../../../artifacts/book_mpso_schedule_v1/20260916T154109Z/operations/final-scientific-review.json)
also recomputed paired statistics, bootstrap intervals, behavior, recovery,
influence and the exact duplicate from saved cases. No historical campaign was rerun.

## Deviations, limitations and next decision

Before any reference outcome, a documented controller amendment hardened reuse
of atomically saved cases after ledger interruption and checked permanent-role
and selection identities. A source-path error in a small test was corrected.
The measured first-case throughput supported retaining the original eight slots.
The numerical engine, cases and scientific settings then remained fixed.
Presentation was subsequently adjusted to show the selected seed as an alias
and retain terminal failures without inventing numerical scores. The bootstrap
specification did not change. No controller restart or blanket rerun occurred.

The principal source conventions are the neutral pairwise-diameter approximation,
neutral-before-permanent ordering, immediate counted initialization, asynchronous
attractors, DEAP initialization and PSO precision, unclipped particles and exact
budget termination. Exclusion now follows each subswarm as in Algorithm 3;
historical paths and findings remain preserved. Table 3's original 50-run
protocol and seeds were not reproduced. Printed scores were not used as fitted
targets or unmatched controls.

Eight development histories and one short search cannot rule out beneficial
unexplored schedules or establish reliability across repeated searches. Some
source changes have large closed-loop effects despite rare action differences.
The cross-island novelty limitation spent part of the allowance redundantly.
None of these results isolates the causal value of cooperation, a movement
feature, or an engine mechanism. The completed V3 null result, inconclusive
radius/velocity pilot and development-only retention finding remain unchanged.

**Decision: retain the published 5+1 schedule.** Before further schedule tuning,
an independent paired comparison of reconstructed **5+0 versus 5+1** in this
same core setting is justified: their close mean here masks sizeable opposing
case effects, leaving the value of permanent sampling uncertain. This is one
recommended next experiment, not an automatically launched campaign.

## Reproduce, inspect and attach

```bash
cd ~/actir/shinka-adaptive-swarms
source .venv/bin/activate
# Saved-data-only analysis; no objective or model calls.
python scripts/analyze_book_mpso.py \
  --run artifacts/book_mpso_schedule_v1/20260916T154109Z \
  --phase development --selected-generation 0 --output /tmp/book-mpso-analysis

# Timestamped operations and native progress; completed logs remain inspectable.
bash scripts/progress.sh results/book_mpso_schedule_v1/20260916T154109Z/operations
tail -n 80 -F results/book_mpso_schedule_v1/20260916T154109Z/evolution/search_seed_640001/run.log

# Reuse the existing correct native WebUI. Launch only if that instance is absent.
bash scripts/webui.sh results/book_mpso_schedule_v1/20260916T154109Z/evolution 8896
```

Open [the native archive](http://localhost:8896/viz_tree.html?db_path=search_seed_640001%2Fprograms.sqlite).
The database selection, seed source, descendant source and parent/inspiration
lineage were checked in the real WebUI; screenshots and exact URLs are operational
artifacts, not scientific figures. Finished cases and terminal slots are durable.
The existing wrapper does not restore native proposal RNG state after restart;
this run did not restart. Credentials and the copyrighted chapter are excluded
from publication.

Prospective commits are `383eea9204ab5f143751f9c1358cf35f546bfd92` (implementation),
`be462cf` (registered suite/recovery), and `a31b3b5` (measured throughput and
resolved search allowance). The final publication verification records the
local and remote result commit, avoiding a self-referential commit hash in this
report. The [artifact inventory](../../../artifacts/README.md) links the immutable
study record and its publication receipts.
