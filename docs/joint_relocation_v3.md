# Joint relocation v3: prospective study record

**Status: prospective implementation; no v3 research outcomes are reported here.**
This study follows the frozen [v3 protocol](followup_joint_relocation_v3.md)
and the [review of v2](review_v2_and_next.md). The existing v1 and v2 studies
remain separate evidence. The small archived preparation check is an interface
check, not a search replicate or a final benchmark result.

## Question and controlled interface

Can a jointly chosen relocation count and radius improve tracking beyond both
the corrected Blackwell–Branke–Li reconstruction and a validation-selected fixed
count/radius pair? A second question is whether any benefit depends on the
observed state, on one component alone, or on their interaction.

`choose_relocation(observation)` returns exactly `{"count": k,
"radius_scale": r}`. The count is a Python integer from zero through the
subswarm size; the radius multiplier is finite and nonnegative. The simulator
keeps memory reevaluation and retained velocity fixed. Candidates receive scalar
optimizer observations only: no peak coordinates, hidden optimum, environment
seed, final inputs, or benchmark object. The known severity-derived default
radius remains public. The source review checks that candidate programs respect
this interface and use only the supplied observation and permitted computation.

An interior fraction `(k - 0.5) / swarm_size` encodes each positive integer count
for the simulator's ceiling rule; zero encodes zero. This encoding is distinct
from the allocated fraction `k / swarm_size`. Saved responses distinguish the
requested count, allocated indices, and relocated particles that actually
received objective evaluations. The last category can be smaller when the
budget ends during a response. Radius changes still update the remembered
response radius at count zero, so count-zero equivalence is restricted to
literal fixed controls whose subsequent actions do not depend on that memory.

The initial action, count five and radius multiplier one, has the corrected
baseline's executed behavior. The source-fidelity correction that preceded v1
is not an evolutionary discovery. Executable programs, search fitness, fresh
case performance, and evidence of a conditional mechanism will be reported
separately.

## Prepared evidence and prospective chronology

The [preparation record](v3_preparation_checks.json) and
[archived native seed check](../artifacts/preparation_joint_v3/20260916-native-seed/runs/20260916T024936.637020Z-seed/manifest.json)
document one 1,000-query case with model calls disabled. Its two native database
rows are the seed placed on two islands, not two evaluated cases. The saved
case, program and manifest hashes match the preparation record. Its eight
complete responses all request, allocate and evaluate five relocated particles;
feedback correctly reports allocated fraction 1.0 and encoding fraction 0.9.
Focused preparation tests cover baseline-equivalent trajectories, all integer
counts, malformed outputs, budget-truncated responses and checkpoint reuse.
This seed-only historical profile does not demonstrate the richer novelty or
meta-analysis mechanisms required for the research searches.

The planned research uses three native ShinkaEvolve searches, each with 30
terminal generation slots including the baseline-equivalent seed. All searches
share 16 search cases, with independent search RNG seeds. The environment is 5D,
with ten peaks, severity one or three and change period 2,500 or 5,000; every
case has exactly 100,000 objective queries. Detection, initialization, exclusion,
ordinary particle evaluation and memory refresh all count against that budget.
Environment and optimizer randomness remain separate.

The top three valid source-distinct programs per search form a reviewed union
shortlist. Validation uses 32 separate cases and the fixed grid of counts zero
through five and radius multipliers 0.5, 1, 2 and 4. The 24 nominal fixed pairs
have 21 executable behavior classes because the four literal count-zero
controls are equivalent. Selection chooses one winner per search, an overall
winner among those three, and one fixed pair using the predeclared tie rules.
Sources, selection, component controls, joint action distributions and analysis
settings freeze before the 80 final seed pairs are generated. All historical,
search and validation seed values are excluded across both RNG roles.

The final comparison contains at most eight distinct methods: three selected
search winners, the corrected baseline, the selected fixed pair, the overall
winner with its radius replaced, the overall winner with its count replaced,
and the state-free joint sampler. The overall winner is an alias for one of the
three search winners, not an additional execution. Every alias must identify its
source and justification. The substituted-component methods first call the
original program on the observation actually reached by that method, then
replace the specified component. Their resulting trajectories can diverge.

## Frozen comparisons and mechanism interpretation

The two primary effects are the overall winner's offline error minus (1) the
corrected baseline and (2) the selected fixed pair. Each effect uses paired
case differences, 20,000 bootstrap resamples within regimes, and equal quarter
weight for the four regimes. Each two-sided interval has 97.5% coverage, giving
an approximate Bonferroni 95% family. A claim of superiority to both requires
both upper bounds below zero. This rule controls interpretation; it does not
gate execution or justify rerunning unfavorable cases.

All other search-winner and component contrasts, the joint sampler contrast,
and the interaction use descriptive 95% intervals. The interaction is
`overall - radius_replaced - count_replaced + fixed`. It is a contrast between
closed-loop methods, not an isolated causal effect on a shared fixed state.
The independent unit is the paired environment/optimizer case. All three search
winners share the same 80 final histories; these are not 240 independent cases.
Three searches offer limited evidence about reliability across future searches.

The joint sampler chooses a validation case uniformly within the known regime,
then one of that case's recorded count/radius pairs uniformly. This preserves
the within-pair association and equal case weighting; a case with no responses
uses the explicitly recorded baseline fallback. The sampler has independent
recorded randomness. Removing the link to current state also changes temporal
dependence and visited optimizer states. Thus its contrast addresses a broad
state-association mechanism, not a pure causal effect of one observation.

## Prospective figures and artifact policy

[The figure renderer](../scripts/plot_joint_study.py) reads completed saved
analysis and checkpoints only. It performs no candidate, objective or model
calls. It checks all 80 paired configurations, exact budgets, annotated action
counts and agreement between saved case differences and the inferential
analysis before rendering:

- The two primary 97.5% contrasts, all three search winners' effects and raw
  case outcomes, and the component/interaction 95% contrasts.
- Equal-case joint count/radius distributions for the validation target, final
  overall winner and sampler. Fixed display radius bins are exact zero,
  `(0, .5]`, `(.5, 1]`, `(1, 2]`, `(2, 4]` and `>4`; exact action pairs remain
  in figure provenance.
- Conditional count and radius summaries against observed relative fitness
  loss and diameter divided by the known default radius. Pooled observed-state
  quartile bins are descriptive; each occupied case contributes equally.
  Normalizing by the current chosen radius would condition on the action, so
  the pre-action default is used instead.
- Measured recovery curves, cumulative tracking error, subswarm counts,
  interval-end error and charged query categories for every final method.

Recovery uses saved `trace.current_error`: best-discovered error within the
current environment. A boundary evaluation belongs to the preceding
environment, with offset `((evaluations - 1) % period) + 1`. The initial
environment is excluded. Environments are averaged within each case at each
shared measured offset, then cases receive equal weight. Markers show saved
measurements and lines only join them; no unsampled immediate recovery is
inferred. Repeated responses, checkpoints and change intervals do not become
independent samples for uncertainty calculations.

Prospective commands, actual native feature use, validation/final selection,
measured outcomes, figures, source hashes, operation logs and remote publication
verification will be added after their corresponding artifacts exist. The
report will retain failures, degradation and deviations alongside successful
executions, and distinguish configured features from observed runtime use.
