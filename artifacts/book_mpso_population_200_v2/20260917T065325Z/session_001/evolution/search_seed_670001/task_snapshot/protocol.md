# Corrected enclosing-ball population campaign, version 2

Registered continuation of `book_mpso_population_200_v1/20260917T025219Z`.
The old one-case diameter-engine trajectory remains historical. It supplies no
corrected control score. The four development seed pairs are retained unchanged.

Question: does a native Shinka-derived population rule reduce mean offline error
relative to corrected reconstructed 5+1 MPSO in the chapter's 200-peak,
movement-severity-one condition under equal objective-query budgets?

## Scientific contract

Five dimensions; 200 conical peaks; severity 1; period 5,000 queries; correlation
zero; nexcess one; exactly 500,000 counted objective queries per history.
Remaining numerical settings are frozen in the versioned development JSON.
Environment and optimizer RNGs are separate. Initialization, replacement,
detection, memory refresh and movement all share this objective budget.

The only engine repair is accurate smallest-enclosing-ball convergence over
neutral positions. See [versioned source fidelity](book_mpso_population_200_v2_source_record.md).
This repair is not an evolutionary gain. The policy interface, public observations,
PSO/UVD movement, permanent quantum role, radius convention, retained velocities,
memories, asynchronous exclusion and swarm birth/removal remain unchanged.

Only `choose_neutral_count(observation) -> int` evolves, returning 2..8. New and
replacement subswarms start with five neutrals and one permanent quantum particle.
After counted detection and completed memory refresh, move at most one neutral
toward the requested target. Deterministic shrinking removes the worst refreshed
personal best, ties last in update order; growing inserts immediately before the
permanent role with existing velocity initialization, first evaluated by the
ensuing temporary quantum response. No copied fitness or extra initialization
query. Survivor order/state persists. Five-at-five consumes no resize RNG.
All current neutrals use quantum movement for the detected update and ordinary
PSO otherwise. Start-at-five and step-one resizing are our extension choices.
This is within-subswarm allocation, without transfers or conserved total size.
`neutral_diameter` remains the honestly named pairwise-distance observation.
The task prompt defines every field and allowed pure mathematical operation.

## Prospective campaign and session limits

Campaign: 50 descendant slots plus native seed (`--generations 51`), at most
400 logical model responses, 400 full-case attempts and 200,000,000 conservative
research queries. Failed terminal slots consume allocation. The nominal complete
design is at most 378 histories before exact reuse: 28 constant controls, 200
descendant histories and 150 later fresh-method histories. Ceilings are not targets.

Session 1 begins 2026-09-17 06:53:25 UTC. Its hard stop is 09:53:25 UTC; admission
must reserve approximately the final 20 minutes for draining, reporting and
publication. Maximum six descendant slots and 80 receipt-counted responses this
session, enforced separately from the immutable 400 campaign allowance. Timing
of the first planned corrected target-five case is retained and informs admission.
Aim for two or three complete descendants; admit more only if measured time fits.
One controller, one proposal worker and one evaluation worker. No shortened cases.
Incomplete work stays unranked and its attempted full budget remains reserved.

Measure targets five/three across all four histories now. Source-identical corrected
target-five records serve the native seed without new executions. Measure the
remaining constant targets 2,4,6,7,8 in later user-launched sessions if necessary.
All are constant-TARGET controls: newborn/replacement swarms still start at five.
Evolution feedback stays consistently against targets three and five throughout.

## Native machinery and resumability

Pinned native ShinkaEvolve `9912af12d423504b8d580f4179fd15f5f88b8c50`;
subscription-authenticated inner `gpt-6-astra/xhigh` (not Ultra), no paid fallback.
Requested supervising Astra/Ultra is separate; actual client selection cannot be
changed or inferred from native receipts. One island; weighted parent sampling;
archive/top inspirations; diff/full/crossover probabilities 0.5/0.3/0.2; calibrated
local embedding-plus-LLM novelty; interval-five meta; fixed mutation model;
prompt coevolution off. Migration is inactive.

Atomic campaign compatibility state preserves native meta summary, scratchpad,
recommendations/history, processed counts and pending evaluated IDs reconciled
with the real database. Restore before proposing; drain database and background
meta/maintenance before clean checkpoints. Save Python/NumPy sampler state at
clean boundaries. Intermediate pauses suppress only the extra terminal meta
summary; ordinary interval-five updates remain. Receipts, accepted pending jobs,
immutable task snapshot and lineage persist. Recovery cannot promise identical
future LLM outputs or replay of a crash between non-atomic provider operations.
Logical response accounting excludes supervising usage and hidden provider retries.

## Prospective final analysis

[Exact analysis settings](studies/book_mpso_population_200_v2/analysis_specification.json)
are frozen before mutation. After 50 terminal descendant slots, select the minimum
complete valid native development mean INCLUDING the seed; ties by earlier
generation then source SHA256. Independently select the best of all seven constant
targets, ties by lower target. Session completion does not authorize finalization.

If a distinct selected native program improves on seed, freeze sources and analysis
before creating 50 NEW paired full histories, excluding all recorded historical
pairs, in later explicitly launched sessions. Compare evolved, corrected 5+1 and
the selected constant; reuse only established execution-identical methods. If seed
remains best, report no discovered improvement and avoid a self comparison.
Fresh histories/outcomes cannot enter mutation, novelty, meta-memory or selection.

Primary comparison is evolved-minus-5+1 error; a 95% paired bootstrap interval
entirely below zero supports improvement in this condition. Only if primary is
supported interpret the prespecified secondary against the selected constant.
Use 20,000 percentile resamples with NumPy default_rng seed 2026091702, resampling
whole paired histories, never particles or the 100 periods within each history.
Report every pair, absolute/relative effect, mean/median/SD, wins/losses and
influential histories. No significance stopping or retuning from partial fresh data.
Four development histories give interim selection-biased evidence, not confirmation.

Use planned diagnostics/trajectories only, against counted objective evaluations.
Keep unfavorable episodes under the explicit extrema rule; no extra replay campaign.
Distinguish optimizer improvement, observed allocation behavior and Shinka's actual
contribution. Constant winners are target tuning; conditional winners do not isolate
adaptation causally. No claim of peak coverage from swarm count, global optimality,
SPSO superiority, all-condition reproduction or comparative discovery efficiency.
