# Follow-up design: when should a swarm relocate more particles?

**Status:** completed on 16 September 2026; see the [measured v2 report](relocation_allocation_v2.md).
The design below is retained from the prospective protocol at commit `28c57e3`;
the native run also contains its unchanged pre-execution snapshot. The report
records the retained feedback-label deviation and actual execution chronology.
**Designed:** 2026-09-16, from the completed study at commit `571f439`.

## Evidence motivating this experiment

The [completed comparison](comparison.md) found search improvement without an
independent advantage: generation 12 had error 3.7857 versus baseline 3.7230 on
eight cases. The paired difference was +0.0627, with an exploratory stratified
bootstrap 95% interval of [-0.1470, +0.2724]. This is not evidence of equivalence.

The predefined fixed response had error 3.4496, beat generation 12 in six of eight
cases, and had a lower mean in all four regimes. It always relocated three of
five particles at radius multiplier 2. Generation 12 relocated four particles in
953 of 1,283 responses and also varied radius. Its mean multiplier was 2.1856.
These differences suggest a mechanism question, but do not establish that
relocating four rather than three particles caused the poorer outcome.

The original comparison changed horizon, seeds and some environmental conditions
together. Its severity-2/period-2,500 condition did not isolate either factor.
Only two independent histories per regime supported its uncertainty estimates.
All previous outcomes now constitute development evidence for this follow-up.

## Question and competing explanations

**At a fixed relocation-radius rule, can ShinkaEvolve discover when to allocate
more particles to exploratory relocation, improving on competent constant
allocations under the same objective-evaluation budget?**

- **Conditional allocation:** the useful number depends on observed swarm state;
  a compact, poorly recovering swarm may benefit from more relocation.
- **Sufficient constant allocation:** a stable count balances ordinary PSO motion
  and exploration as effectively as the evolved controller.
- **Regime allocation:** the useful count differs between environmental regimes,
  but detailed response to current swarm state adds no value.

An adaptive program is not required to win or even to vary its decisions. A
constant winner is an informative result. No bonus rewards code complexity,
branch count, novelty labels or the mere presence of adaptation.

## Experimental intervention

Create a separate `relocation_allocation_v2` task. Evolve:

```python
def choose_relocation_count(observation: dict) -> int:
    return 3
```

The returned count is an integer from 0 through the observed swarm size (five
in this study). Public observations retain the existing optimizer interface,
including signed fitness change, dispersion, recent improvement, observed
best-position displacement and previous response information. The experiment
does not require particular thresholds or a predetermined behavioral rule.

Hold `radius_scale=2`, `memory="reevaluate"`, and `reset_velocity=False` constant
for the allocation programs. These are controls for this mechanism experiment,
not restrictions on what ShinkaEvolve can evolve in other studies. The radius is
still twice `default_radius`, hence equal to the configured movement severity;
this does not test adaptation without knowledge of that severity scale.

Retain the existing numerical simulator. A fixed adapter converts positive count
`k` to the interior fraction `(k - 0.5) / swarm_size`, and count zero to fraction
zero. Under the existing `ceil(fraction * swarm_size)` rule, this yields exactly
`k` without floating-point boundary ambiguity. Validate integer type and bounds;
do not silently round invalid candidate outputs. Log requested and executed count.

The old selected program and its floating-point behavior remain unchanged in the
v1 archive. In particular, this adapter is a new task interface, not a correction
retroactively applied to the original result.

Non-relocated particles continue ordinary PSO motion. They are not stationary
anchors. Personal-best memories of all particles are reevaluated and retained.
This study concerns allocation between two motion modes, not memory erasure.
Fitness values are deterministic given the landscape; stochastic histories and
height/width changes make observed fitness loss an imperfect displacement signal.

## Cases and environmental factors

Cross two movement severities with two change periods, giving four equally
weighted regimes. Use the same 100,000-evaluation horizon at every stage.

| Movement severity | Evaluations between changes |
|---:|---:|
| 1 | 2,500 |
| 1 | 5,000 |
| 3 | 2,500 |
| 3 | 5,000 |

Other settings retain five dimensions, ten conical peaks, five particles per
swarm, NEXCESS=1, correlation zero and the documented corrected optimizer.
This design measures generalization to fresh histories within these four
regimes; it does not claim extrapolation to unseen severities or dimensions.

| Stage | Independent cases per regime | Total cases | Use |
|---|---:|---:|---|
| Search | 4 | 16 | Native evolutionary feedback |
| Validation | 4 | 16 | One-time program and constant selection |
| Final comparison | 10 | 40 | Frozen-program comparison |

The search and validation manifests are provided under
`configs/relocation_allocation_v2/`. Before execution, check seed pairs against
existing manifests and record any collision replacement before outcomes exist.
Generate and save the 40 final seed pairs **after** program selection and the
ablation definition are frozen. Exclude all previously used environment and
optimizer seeds, including search, validation and the original study. Do not
inspect final trajectories or use final outcomes for mutation or selection.

The final cases are independent across regimes; each method receives the same
environment history and paired optimizer seed within a case. Verify landscape
hashes and exact query budgets. Different methods need not share particle paths.
All detection and memory queries count. Checkpoints and responses are repeated
measurements, not additional independent cases.

## Native search and selection

Run **one new native ShinkaEvolve search with 20 generation slots**, including
the constant-three seed and up to 19 descendant slots. This is a practical first
mechanism study, not a claim that one search establishes the reliability of
ShinkaEvolve across independent searches. Do not append to or resume the finished
v1 study with a changed task or suite.

Use the established subscription route and actual recorded model settings;
log inner settings separately from supervising Codex Astra/Ultra. Preserve native
archive, sampling, mutation and feedback. Retain the existing declared optional
feature configuration unless a concrete incompatibility requires a documented
change. No new paid API route is part of this design.

Selection score remains `1 / (1 + mean_offline_error)` with equal case and regime
weights. Supply this document's mechanism context, the v1 finding, actual per-case
errors, recovery diagnostics and executed count distributions through the task
prompt and enabled string `text_feedback`. Inspect an actual mutation prompt to
verify delivery. Do not reward the proposed hypothesis independently of outcomes.

After search, take the top three source-distinct valid programs by search score,
including the seed if it qualifies. If fewer exist, use all available and report
that fact. Freeze this shortlist before running validation. Ties use earlier
generation, then source hash. Evaluate the shortlist and **all six constant
counts k=0,...,5** once on the same 16 validation cases.

Select one shortlisted program and one constant by mean validation error. Use
the same deterministic tie rule for programs; constant ties use the smaller
count. Freeze source, scores, hashes and selection rules before generating final
cases. The constant is one global choice across the declared regime mixture,
not an oracle selected separately on each test case. Validation outcomes do not
flow back into this search. The best constant can coincide with count three.

## Final methods and mechanism control

| Method | Purpose |
|---|---|
| Original corrected baseline: multiplier 1, all five relocated | Continuity with v1 |
| Fixed multiplier 2, count three | Reassess the promising original control |
| Validation-selected constant count, multiplier 2 | Primary competent comparator |
| Validation-selected evolved allocation program, multiplier 2 | Main experimental method |
| Control sampling counts without current swarm-state information | Test the value of conditional allocation |

For the last control, freeze a separate count distribution for each of the four
known regimes from the selected program's validation traces. Within a regime,
average each case's count proportions equally; do not let cases with many
responses dominate. If a case has no response, use the initial count-three
distribution for that case and disclose it. The control samples from that fixed
distribution at each response using a dedicated, recorded RNG independent of
the environment and ordinary optimizer RNGs. It receives the declared regime
identity but no current swarm-state inputs for selecting counts.

This deliberately gives the control known-regime information and approximately
preserves the selected controller's allocation distribution within each regime.
It removes association with current state and also changes temporal dependence.
It is therefore a targeted mechanism comparison, not a perfect intervention on
one causal variable. Its final action proportions may differ by sampling noise
and because trajectories change. Report those differences. If the selected
program is constant within a regime, the control may be identical there.

Evaluate at most five methods on each of the 40 final cases. Execute genuinely
identical methods only once, with explicit aliases and compatible cache keys.
Preserve every historical result; none of the 80 search or 32 comparison cases
from v1 is repeated as part of this protocol.

## Analysis and interpretation

The primary effect is **evolved error minus validation-selected constant error**;
negative favors the evolved controller. Report the mean paired effect, all
case-level differences, four regime means and a stratified paired bootstrap 95%
interval using 20,000 resamples and analysis seed 20260916. Resample independent
case pairs within each regime and retain equal regime weights. Show the standard
error of the equally weighted regime mean as an additional precision check.

The predeclared mechanism contrast is evolved minus the control without current
state information. Interpret secondary intervals descriptively; do not present
multiple favorable comparisons as independent confirmations. Comparisons to the
original baseline and count three are contextual. Forty cases improve sampling
coverage over the previous eight, but do not guarantee precision for small effects.

Save executed-count distributions by regime and observed state, per-environment
error, recovery trajectories, swarm counts, query accounting, and source/lineage.
Treat correlations between chosen counts and recovery as descriptive; state
influences both. Use the matched program/control simulations for outcome claims.

- Beating the constant and the state-information control would support useful
  conditional allocation within this model and these regimes.
- Beating the constant but not the latter control would leave state dependence
  unestablished; a suitable distribution of actions may explain the outcome.
- A constant winner, or an interval spanning useful gains and losses, is reported
  directly. It does not imply that all adaptation is ineffective.
- A controller depending only on regime scale is described as such, not as
  demonstrated response to detailed current swarm state.

This design uses one search realization and holds the radius rule fixed. It does
not establish an optimal radius, algorithm superiority over the stronger (5+1)
literature baseline, reliability across search replications, or geopolitical
effectiveness. Its contribution is an interpretable finding about allocation
between exploratory relocation and ordinary swarm motion.

## Work estimate and implementation handoff

The maximum planned work is 320 search method cases, 144 validation method cases
and 200 final method cases: **664 cases / 66.4 million objective evaluations**,
before cache reuse. The model budget is one 20-slot search; native call attempts
can differ from descendant slots and must be logged. Validation, final simulations
and the mechanism control need no LLM calls. These counts define this experiment;
do not silently extend it until a favorable result appears.

The existing launcher supports suites and result directories, but not an alternate
initial program/task snapshot or validation selection. Consequently, the existing
v1 launch command alone does **not** execute this protocol. The implementation
work is to add a separate task path or a small task-selection option, the fixed
integer adapter, selection/freeze support and the control described above. Keep
the native search engine and existing persistence/logging machinery.

Focused verification should establish exact count mapping for 0–5, equivalence
of constant three to the original fixed control's executed decisions, task/context
snapshot integrity, and valid resume without duplicate completed cases. Then run
the substantive experiment; these checks are not a separate research campaign.

When executing this design in WSL, inspect existing processes, use new v2 run
directories, preserve v1, and keep timestamped progress plus the native WebUI
visible. Save compressed case checkpoints and resume compatible partial results.
Update README and a v2 report with code, comparisons, uncertainty and figures;
publish completed work and verify the remote commit. The present design commit
does not claim these v2 implementation or execution steps have happened.
