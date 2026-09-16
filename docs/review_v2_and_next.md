# V2 review and the next research question

Reviewed 16 September 2026 against completed-study commit
`e5737a0`. This review uses saved programs and measurements; it adds no
evolutionary proposals or benchmark comparison cases. V1 and V2 remain frozen.

## What the project has established

The project now contains a documented conceptual reconstruction, two native
ShinkaEvolve searches, and a prospective validation/final protocol with a
substantive mechanism control. The evidence supports a narrower result than
an improved multi-swarm optimizer: **V2's evolved rule beats the constant
selected by its validation procedure, but useful state dependence and overall
optimizer superiority remain unestablished.**

The independent review recomputed outcomes from all 664 saved executions,
checked exact objective budgets and landscape pairing, inspected the native
database and frozen sources, reproduced validation selection, and regenerated
the four reported paired bootstrap intervals. It also reproduced the 40
dedicated control RNG action sequences. Numerical differences were below
`1e-12`. See [the reproducible audit](review_v2_audit.json) and
[the original full report](relocation_allocation_v2.md).

| Stage | Completed executions | Objective queries | What it establishes |
|---|---:|---:|---|
| Native search: 20 slots × 16 cases | 320 | 32,000,000 | A functioning, measured evolutionary search |
| Validation: 9 methods × 16 cases | 144 | 14,400,000 | Frozen program and constant selection |
| Final: 5 methods × 40 cases | 200 | 20,000,000 | Independent comparison within four declared regimes |
| Total V2 | **664** | **66,400,000** | Complete protocol; no discarded final cases |

There were 19 recorded subscription-backed mutation attempts, all successful.
The seed's island copy is not an additional evaluation. One search realization
does not estimate the reliability of the evolutionary search procedure.

## Performance: a real but limited positive result

Lower offline error is better. Each final method received the same 40
environment histories, ten per regime, and 100,000 objective queries per case.

| Method | Final mean error | Evolved minus method | Paired 95% interval |
|---|---:|---:|---|
| Corrected original baseline: radius multiplier 1, count 5 | **3.214605** | +0.339460 | [+0.053050, +0.659607] |
| Regime-conditioned random count control: multiplier 2 | 3.469960 | +0.084105 | [−0.178679, +0.409602] |
| Evolved generation 13: multiplier 2 | 3.554065 | — | — |
| Fixed count 3: multiplier 2 | 3.626680 | −0.072615 | [−0.317470, +0.167732] |
| Validation-selected count 2: multiplier 2 | 3.980588 | **−0.426523** | **[−0.690272, −0.182927]** |

The predeclared primary advantage is 10.72% relative to the selected constant.
It is not a comparison against the best constant in hindsight. Count two won
validation but performed worse than count three on final cases. Counts zero,
one, four and five at multiplier two were not all tested in the final stage.
The constant selection procedure was legitimate; its ranking was unstable.

The baseline comparison is secondary in V2 and its interval is descriptive.
Nevertheless, the baseline has lower error in every regime mean and wins
29/40 paired cases. This is strong practical motivation to retain it as an
explicit primary comparator in V3. Neither V1 nor V2 establishes superiority
over the chapter's other algorithms or its stronger 5+1 configuration.

## Mechanism: the rule changes actions, but the benefit is unresolved

Generation 13 follows lineage `0 → 7 → 13`; its final step was native crossover.
It normally moves three particles and moves four when both conditions hold:

1. The swarm is sufficiently compact relative to the supplied radius scale.
2. Observed fitness loss exceeds nonnegative recent improvement.

The compactness threshold is 0.5 for severity one and 3 for severity three.
The actual relocation radii are respectively 1 and 3. The policy therefore
combines known severity scale with current observations. `recent_improvement`
means improvement during the preceding swarm update, not cumulative recovery
since the preceding landscape change.

On final trajectories both gates mattered: 5,688 responses satisfied both and
moved four; 837 satisfied compactness alone; 1,073 satisfied the loss condition
alone; 640 satisfied neither. All 8,238 responses executed the requested
allocation. These events verify conditional behavior, not independent samples
or evidence that the conditions improve performance.

The control independently draws three or four from a validation-frozen
distribution for each known regime. It is not a shuffle of the candidate's
final action sequence. It approximately preserves action frequencies while
also changing temporal structure, subsequent states and optimizer RNG
consumption. Its interval against the evolved rule supports neither a benefit
from the state conditions nor equivalence.

Case 16 is informative: evolved error 8.018923 versus control 2.919520. Their
first action difference occurs at objective query 5,014; sustained tracking
losses follow over several environment intervals. This observation cannot
identify that first action as the cause, since trajectories subsequently
diverge. The case stays in every primary analysis. Repeated poor recovery is
a useful diagnostic target; deleting an unfavorable history would not be.

## Search quality and an actual feedback defect

All 20 programs have distinct source hashes, but three descendant pairs
repeat complete observed search behavior: generations **0/4, 7/16 and 12/18**.
Each pair agrees across all 16 cases in error, query accounting, response
logs, sampled traces and environment records. Thus 17 distinct observed
execution profiles used 20 slots. The repeats consumed 48 case evaluations,
or 4.8 million objective queries. Finite observed agreement is not universal
program equivalence, but it gives novelty filtering a concrete purpose.

The three shortlisted programs also belong to one compactness/loss/count-3-or-4
family. More archive memory and occasional migration can expose alternatives
to this narrow lineage context. They cannot guarantee better programs.

V2 text feedback called the adapter's encoding fraction the "relocated
fraction." Count three was encoded as 0.5 although three of five particles
means an actual allocated fraction of 0.6. The count records, simulator and
fitness remained correct. Adjacent correct information does not prove that
the label had no effect on proposals. Preserve the historical record and fix
the label in the separately versioned V3 evaluator.

## Follow-up decision

**Evolve radius and exact particle count jointly, starting from the corrected
baseline.** V2's fixed multiplier-two restriction excluded the baseline's
response. Its results justify reopening this design choice; they do not prove
radius alone caused the deficit, because baseline count also differed.

The proposed [V3 protocol](followup_joint_relocation_v3.md) uses a strong fixed
radius/count comparison, three independent evolutionary searches, separate
validation and fresh final histories. It retains the native parent/inspiration
sampling and crossover, and adds native novelty filtering, meta-memory and
migration. It also records actual behavior and unsuccessful novelty checks.

The scientific claim remains about optimizer performance and interpretable
response mechanisms. Changing the search space and engine together will not
identify which engine feature caused any improvement. A separate engine
ablation is appropriate only if that attribution becomes the research question.

This is a useful research position: the project has a reproducible mixed
result, a verified conditional rule, competent counterexamples, and a
specific next experiment. The evidence does not yet support a headline
claim of a generally superior adaptive swarm algorithm.
