# Joint relocation radius and particle allocation: prospective V3

Status: follow-up design and task/engine preparation, 16 September 2026.
No V3 evolutionary campaign or protected final comparison has run. Completed
V1/V2 records remain unchanged. The V3 comparison controller described below
is still to be implemented; the native search task and engine profile are
prepared separately from that controller.

## Question and evidence

Can a response program evolved with native ShinkaEvolve improve tracking
relative to both the corrected original baseline and a validation-selected
fixed radius/count pair? If so, does the improvement require conditional
radius, conditional count, or their combination?

[The V2 review](review_v2_and_next.md) motivates the design: selected allocation
beat validation-selected count two, but its fixed radius multiplier two
prevented recovery of the original baseline response, which had lower error
in every final regime mean. V2 also repeated three observed execution profiles
and left state-dependence benefits unresolved.

## Evolved object and faithful seed

The candidate defines `choose_relocation(observation)` and returns:

```python
{"count": 5, "radius_scale": 1.0}
```

`count` is an exact Python integer in `[0, swarm_size]`; `radius_scale` is a
finite, nonnegative real multiplier of `default_radius`. Boolean counts or
radii, nonfinite numbers and malformed outputs fail explicitly. Radius is
not restricted to the fixed comparison grid. The seed above implements the
corrected baseline's count and radius. Memory reevaluation and retained
velocity remain fixed. Other swarm mechanisms and objective accounting retain
the established simulator.

An interior encoding `(count - 0.5)/swarm_size` for positive counts, or zero,
avoids the V1 floating-point boundary issue. Requested allocation, actual
selected indices, objectively evaluated relocations, actual allocated fraction
and adapter encoding fraction are separately labeled. A final partial response
is never relabeled complete. Seed equivalence concerns executed trajectories
and objective accounting; the encoding field can differ from the historical
baseline's fraction one.

Use the existing public observations, including the known severity-derived
default radius. The test does not establish adaptation without that scale.
No latent peaks, optimum, seeds or protected data enter candidate observations.
Constants remain valid discoveries; there is no branching or adaptivity bonus.

## Cases, search and selection

Retain five dimensions, ten conical peaks, five particles per swarm, movement
correlation zero, and the four severity `{1,3}` × period `{2500,5000}` regimes.
Every execution receives 100,000 counted objective queries. Regimes and cases
within regimes receive equal weight.

| Stage | Design | Maximum executions |
|---|---|---:|
| Evolution | 3 independent searches × 30 native slots × 16 shared search cases | 1,440 |
| Validation | Up to 9 shortlisted programs + 21 distinct fixed controls, each on 32 cases | 960 |
| Final | Up to 8 frozen methods on 80 fresh paired histories | 640 |
| Total | Before valid aliases; failures and inference retries logged separately | **3,040** |

This totals at most **304 million objective queries**, about 4.58 times V2's
completed protocol, excluding small implementation checks. Thirty slots mean
one seed and up to 29 descendants; rejected/invalid slots are retained, not
silently replaced until 29 successes occur. Three searches provide initial
evidence about search-path variability conditional on one shared development
suite. They do not establish reliability across independent data selections.
All three use the same rich engine profile and independent recorded search
seeds. Hosted model nondeterminism prevents a seed from guaranteeing identical
proposals. Resume retains completed work; exact future sampling is not promised
unless its complete RNG state is actually preserved.

The 16 search cases contain four histories per regime; validation contains
eight per regime. Their prospective manifests are saved under
`configs/joint_relocation_v3/` and audited against existing seed values in both
RNG roles. V1/V2 results now inform development of V3, but remain independent
evidence for their original frozen claims. Generate the 80 final histories
(20 per regime) only after V3 program/control selection is frozen. No final
data may feed novelty judging, meta-memory, mutation or selection.

Freeze the three best source-distinct valid programs per search using search
mean error, then earlier generation and source hash for ties. Include the seed
when its search rank qualifies. Native failure records remain visible. Review
exact sources for prohibited access before validation. Evaluate the union of
these at most nine programs once on validation; deduplicate identical sources
with explicit aliases, not by equal aggregate scores.

The fixed family crosses radius multipliers `{0.5,1,2,4}` with counts
`{0,1,2,3,4,5}`. It includes both historical radius choices plus a smaller and
larger comparison scale. The four zero-count radius choices have the same
optimizer behavior for these literal constant programs, giving 21 distinct
executions; record the equivalence and retain all 24 nominal labels. The
baseline is multiplier one/count five. This is a finite, competent grid,
not an oracle over all possible fixed radii.

Choose one validation winner per search and the overall winner among them;
choose one globally best fixed pair. Ties prefer earlier search index, earlier
generation, then source hash; fixed ties prefer smaller count, then smaller
radius multiplier. Freeze the source hashes, grid, validation means, tie rules,
all mechanism controls and analysis specification before final seed generation.

## Final comparisons and claims

Execute these frozen methods on the same 80 histories, with explicit aliases
when identical execution can be established:

1. The three per-search validation winners, including the overall winner.
2. The corrected original baseline.
3. The validation-selected fixed radius/count pair.
4. The overall winner with its radius replaced by the selected fixed radius.
5. The overall winner with its count replaced by the selected fixed count.
6. A regime-conditioned sampler of the overall winner's **joint** validation
   `(count, radius_scale)` distribution, using an independent recorded RNG.

The enumeration yields at most eight distinct methods. Component substitutions
are applied after calling the original candidate on the actually reached
observation. Replacing both components gives the selected fixed pair. Together
these form a 2×2 comparison of retaining/replacing the two output components.
They are interventions on whole closed-loop policies: subsequent states can
change, so effects do not hold state visitation fixed. Report the interaction
`E - radius_replaced - count_replaced + fixed` descriptively.

For the sampling control, choose a validation case uniformly within the known
regime, then one of that case's response action pairs uniformly. This preserves
equal case weight and the association between radius and count. Sampling the
two marginals independently is not equivalent. For an empty-response case use
the baseline pair and disclose it. Freeze the empirical distributions before
final generation. This control removes current-state association while also
changing temporal dependence; no pure state-only causal claim follows.

Two primary contrasts are overall winner minus baseline and overall winner
minus validation-selected fixed pair. Negative favors evolution. Use paired
case resampling within regimes, equal regime weights, 20,000 resamples and a
recorded analysis RNG seed. Report **97.5% two-sided percentile intervals for
each primary contrast** (Bonferroni allocation for an approximate simultaneous
95% family). Claim superiority over both controls only when both upper bounds
are below zero. Report exact effects even if this criterion is not met. It is
a claim rule, not an execution gate or a required effect-size threshold.

Other program, ablation and sampling-control contrasts receive descriptive
95% intervals. Show all per-search winners rather than reporting only a lucky
search. Three search replicates are too few for a precise search-reliability
estimate. Do not treat trajectory points or the shared 80-case suites across
winners as independent additional histories. The sample size improves
precision but is not a guaranteed-power calculation.

Retain all histories, including large tracking failures. Report error by
regime, recovery after changes, radius/count distributions, objective shares,
and large sustained failures. Preserve measurement resolution; do not invent
immediate post-change recovery from a 500-query trace interval. No final reruns
are justified merely by an unfavorable outcome.

## Native ShinkaEvolve configuration

The explicit `configs/shinka/research_v3.json` profile adds native mechanisms
to the historical configuration. The upstream revision remains
`9912af12d423504b8d580f4179fd15f5f88b8c50`.

| Mechanism | V3 setting and reason |
|---|---|
| Parent selection | Weighted fitness × underused-parent preference; preserve successful alternatives |
| Inspirations | One archive and one top-ranked eligible program; keep actual context in saved prompts |
| Islands | Two; migration fraction 0.1 every ten generations; report actual transfers |
| Mutation | Diff/full/crossover probabilities 0.5/0.3/0.2 |
| Native novelty | Local embeddings plus subscription-backed novelty judge; at most three native novelty attempts |
| Meta-memory | Summaries/recommendations every five evaluated programs using the same subscription route |
| Evaluator feedback | Measured error and correctly labeled behavioral diagnostics |
| Mutation model | One explicit Astra route by default; fixed selection because there is one arm |
| Optional ensemble | Explicit multi-model subscription pool and UCB are supported; not claimed active with one model |
| Prompt co-evolution | Off; separate from meta-memory and unnecessary for this specified experiment |

The local embedding service must provide a working OpenAI-compatible endpoint;
the profile's requested features must not silently disappear when it is absent.
Startup checks the configured local listener. Mid-run errors retain native
retry/fallback behavior and receive explicit degradation events; they do not
become successful novelty checks or trigger a new blanket cancellation rule.
Resolve and inspect the actual embedding model and similarities. The stock
0.99 threshold is not automatically calibrated to every embedding model;
verify examples of cosmetic duplicates and meaningful count/radius changes
using development code, then freeze the threshold before search. Preserve
novelty decisions and errors; an enabled judge is not proof a successful check
occurred. Embedding novelty is not a claim of scientific originality or
guaranteed behavioral diversity.

With all 90 slots evaluated, interval-five meta-work entails roughly 126
logical LLM calls (one summary per program plus two synthesis/recommendation
calls per batch), in addition to 87 first mutation attempts and any novelty
judgments/retries. This estimate is not a hard call cap. Record actual requests
by role, elapsed time, errors and subscription usage when exposed. No paid
model API fallback is authorized. Outer Astra/Ultra and internal model effort
are recorded separately; omitted inner effort is not labeled Ultra.

## Execution visibility and remaining implementation

Before the campaign, complete the comparison controller for the freezes,
aliases, joint sampler, component interventions and analysis above. Keep all
completed V1/V2 evaluations. The task, profile and prospective suites are
reviewable now; preparing them does not mean the full campaign has executed.

For configuration inspection without model calls:

```bash
python scripts/run_evolution.py --task joint_relocation_v3 \
  --engine-profile configs/shinka/research_v3.json \
  --embedding-model 'local/<served-model>@http://127.0.0.1:<port>/v1' \
  --print-engine-config
```

Replace the placeholders with the verified local service. Inspect resolved
roles, model/effort, settings and endpoint before starting the first search.
Each search needs its own run directory and recorded search seed. Do not use
an existing completed run's resume path to change its task or engine profile.

Attach to a created run and its native database with:

```bash
bash scripts/progress.sh results/joint_relocation_v3/evolution/<run>
bash scripts/webui.sh results/joint_relocation_v3/evolution/<run> 8890
```

Use a free port; these commands do not establish that a WebUI is currently
running. Show current stage, case/proposal, parent/inspirations, novelty outcome,
meta updates, migrations, elapsed time, completed work and exceptions. Retain
the actual prompts, raw proposal records and native database. Heartbeats
describe waiting; they are not hidden model reasoning or token streaming.

Per-role model receipts are saved under `engine_calls/`, with request/response
status and paths in the timestamped `events.jsonl` and `run.log`. They distinguish
configured models, native-client reported models and unverified effective effort.
Logical requests do not count hidden provider retries or expose thinking tokens.
Native pre-evaluation terminal failures count as finished slots, separately from
evaluated programs, and are preserved on resume.
`progress.sh` also follows `evolution_run.log` when present, retaining native
sampling, archive and migration messages alongside the structured task events.

Publish results and figures after the specified analysis regardless of sign.
The V3 report must distinguish changes to the policy search space, engine
configuration and evaluator labels. A V3 improvement alone will not attribute
causal benefit to novelty, migration or meta-memory individually.
