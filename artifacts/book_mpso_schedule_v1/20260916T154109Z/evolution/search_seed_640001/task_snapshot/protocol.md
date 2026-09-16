# Prospective chapter-aligned MPSO schedule experiment

Registered 16 September 2026, before numerical research outcomes. Run identity:
`book_mpso_schedule_v1/20260916T154109Z`; search seed **640001**.
Session began 15:41:09 UTC; hard stop 18:41:09 UTC, including publication.

## Question and fixed comparison

Can native ShinkaEvolve improve the human-designed temporary diversification
schedule in Blackwell, Branke and Li (2008), under matched conditions? This
compares schedules within a cooperative multi-swarm optimizer, not cooperation
against independent search. See [source record](book_mpso_source_record.md).

The new versioned reference path has five designated neutral particles and either
zero (5+0) or one (5+1) permanent quantum particle. Both reference schedules
convert all five neutral particles for one update after the optimizer's counted
best-point check detects change; otherwise none convert. Quantum sampling replaces
PSO movement. The permanent particle samples every update. All memories survive,
are reevaluated after detected change, and contribute to the shared best.

Only `choose_temporary_quantum_count(observation) -> int` in [0,5] evolves, called
on every subswarm update after detection/refresh and before movement. The native
seed is exactly the standalone 5+1 source, using the same execution path. A
separate task RNG shuffles all five neutral indices every update regardless of
count; the first k convert. Constants are valid. Fitness is
`1/(1+mean_offline_error)`, without complexity or conditionality rewards.

Radius remains `0.5 * configured movement severity`. Velocities, memory handling,
PSO coefficients, structural roles, birth/removal, exclusion and objective
accounting are fixed. The public observations and numerical-expression checker
are specified in `tasks/book_mpso_schedule_v1/task_prompt.txt`; math imports
inside functions are permitted. No external access, candidate randomness, hidden
peaks, evaluation error, future changes, seeds or fresh outcomes enter candidates.

## Cases and resource limits

Eight development seed pairs are generated and saved before outcomes, rejecting
all recorded historical seeds. Each case has five dimensions, ten conical peaks,
domain [0,100]^5, severity1, period5000, correlation0, nexcess1 and exactly
500,000 objective queries. Height/width and initialization conventions are fixed
in the source record. Trace interval100 records recovery without replay; no
horizon is shortened. All complete landscape-history hashes must match in pairs.

Two references consume16 executions. The native seed reuses the compatible eight
5+1 records, requiring exact source/task/configuration/history identity. Up to
eight descendant generation slots consume at most64 executions. Terminal failed
slots count, with no replacement slots. Failed/partial/repeated work is reported
separately. Small focused fixtures are recorded separately.

Measure the first already-planned full reference case and keep its checkpoint.
If projected execution/model latency threatens the time envelope, reduce the
planned descendant slots before search with a recorded amendment. At four slots,
inspect actual sources and measured feedback and write INTERIM.md; continue only
if remaining original slots address a concrete uncertainty. Do not stop on a
p-value or spend the allowance merely because it remains.

Native logical response ceiling40 includes mutation, novelty, meta and exposed
retries; hidden provider retries and supervising usage are unobserved. Reuse the
named research profile and existing local embedding route. Keep native weighted
parents, two islands, archive/top inspirations, novelty and meta-memory. Migration
may not occur in this short run. Prompt co-evolution is off and model selection
is fixed. Strongest supported task-local inner effort is verified separately
from requested supervising Astra/Ultra. Subscription Codex only; no paid fallback.

## Selection and independent comparison

Rank complete valid native programs including seed by mean development error,
then earlier generation, then source SHA256. Freeze winner, both references,
analysis settings and exact source review before generating fresh identities.
If the seed wins, source is identical, or complete development execution is
identical, avoid a duplicate fresh comparison. Otherwise, a distinct candidate
with lower development mean triggers eight fresh seed pairs and three frozen
methods,24 executions. No fresh feedback reaches search or source revision.

Maximum physical full work:104 executions/52 million queries. Exact cache records
are separate. No automatic extension, new regimes, SPSO, parameter sweeps or
repeated searches. The independent comparison is exploratory evidence for this
one chapter setting, not reproduction of the 50-run table or Shinka superiority.

The [frozen analysis specification](studies/book_mpso_schedule_v1/analysis_specification.json)
uses equal case weights,20,000 paired-case bootstrap samples, seed2026091608 and
descriptive95% intervals. Report every case, mean/median/SD/range, wins/losses,
leave-one-case-out influence, favorable/unfavorable episodes, conversion timing,
ordinary/quantum contributions, actual lineage/feedback and actual role counts.
Development intervals remain selection-biased. Updates/particles are not replicates.

## Recovery and publication

Checkpoint every case and stage, verify frozen fingerprints and retain terminal
failures. No blanket reruns or duplicate controllers. Native proposal RNG state
is not restored by the current wrapper across process restarts; any restart is
recorded. Persistent timestamped terminal and JSONL events report honest waiting.
Use the actual new native SQLite archive in the WebUI. Commit prospective code
and settings before evolutionary outcomes. Preserve all earlier research and
publish report, exact source, measured figures and coherent paper-style README;
verify the pushed remote SHA. Do not publish authentication material or chapter PDF.
