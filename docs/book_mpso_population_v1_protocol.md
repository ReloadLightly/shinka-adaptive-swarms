# Prospective chapter population experiment

Registered 16 September 2026, before new research outcomes. Session begins
18:37:31 UTC; hard ceiling 20:37:31 UTC, including publication. Run identity:
`book_mpso_population_v1/20260916T183731Z`; native search seed **650001**.

## Question and source

Can ShinkaEvolve improve the chapter's MPSO under matched conditions and counted
objective budgets by changing the neutral population within each subswarm?
Blackwell, Branke and Li (2008), printed p.215, identifies adapting MPSO's
within-subswarm particle count as future work. This differs from SPSO's allocation
of a fixed overall population. The author chapter was inspected in the existing
temporary extraction; its provenance remains in
[the source record](book_mpso_source_record.md). The copyrighted PDF is excluded.

The preceding schedule search found no improvement. Retain its published response:
all current neutrals make quantum moves for the detected-change update, ordinary
PSO otherwise; one permanent quantum particle samples every update. This study
does not test cooperation's causal advantage or recreate the entire chapter table.

## Fixed population adapter

The separate `book_population.py` path preserves the historical engines. Every
newborn or exclusion replacement starts with five neutrals followed by one
permanent quantum particle. Only `choose_neutral_count(observation) -> int` evolves,
with exact Python integer targets **2 through 8**, excluding bool.

Call the policy only after a counted shared-best reevaluation detects change and
all existing personal memories are reevaluated, before any particle movement.
Take an immutable public snapshot. Move the current neutral count at most one
toward the target; no transfers or global particle-count conservation are imposed.

- Shrink: remove the lowest refreshed personal-best neutral. Equal minima remove
  the last neutral in current update order. Never remove the permanent role.
  Rebuild the shared best from surviving initialized memories.
- Grow: insert a neutral just before the permanent role. Its velocity is sampled
  from the existing uniform per-coordinate convention. It has no fitness or
  personal memory; a temporary placeholder position is overwritten by the ensuing
  counted quantum move. No copied fitness or extra initialization query is used.
- Preserve survivor order, positions, velocities and memories. A no-op target
  consumes no extra movement RNG. The unchanged task-selection RNG shuffles the
  current neutral indices each update, preserving the earlier five-neutral path.
- Convergence measures all current neutral positions, excludes the permanent role,
  and retains the pairwise-diameter approximation. Radius, PSO, asynchronous best
  updates, exclusion after each subswarm, birth/removal and exact budgets stay fixed.

Public fields and their timing are specified in
[`task_prompt.txt`](../tasks/book_mpso_population_v1/task_prompt.txt): current count,
spread/motion, observed deterioration, preceding improvement, global swarm/particle
counts and previous requested target. Geometry uses coordinate units; default radius
is the chapter's known scale, half configured movement severity. No hidden peak
locations/counts, optimum, benchmark error, future change, seeds or protected data
are passed to a candidate. Documented pure arithmetic, numerical builtins and math
imports at module or function scope are permitted consistently by the checker.

## Cases, controls and exact reuse

Reuse the eight complete development configurations from the schedule study,
without generating new development identities or changing their numerical settings:
5D, ten conical peaks, severity 1, period 5,000, correlation 0, `nexcess=1`, and
**500,000 counted queries** per execution. The trace interval remains 100.
These are reused development cases, not fresh evidence.

Controls request targets **3, 5 and 7**, all using the same start-at-five and
one-step adapter. Targets 3/7 are not historical configurations initialized at
those sizes. Target five is the native seed and reconstructed chapter 5+1.
Import its eight archived cases only after structural RNG/update-order review and
focused exact numerical checks. Preserve original numerical values and provenance;
label added fixed-five population diagnostics as derived. Native seed reuse requires
the new source, scientific fingerprint, suite and artifact identities to match.

## Native search and limits

One pinned native ShinkaEvolve search, **seed plus at most six descendant slots**.
Use one island, weighted native parents, one archive/top inspiration, native
diff/full/crossover probabilities 0.5/0.3/0.2, existing local embeddings and threshold,
LLM novelty with three attempts, meta-memory every five programs, and measured
feedback. Migration is inactive with one island. Fixed subscription mutation model;
prompt co-evolution off. One island removes the previous separation, not every
possible behavioral duplicate. Native selection, retries and archive remain in control.

Use `headless/codex@gpt-6-astra?effort=xhigh`, the strongest supported pinned inner
effort. Supervising Astra/Ultra is requested separately and is not inferred from
inner settings. No paid API fallback or global settings changes. The ceiling is
**36 requested native logical responses** across all roles and exposed retries;
provider-hidden retries and supervising usage are outside this observed counter.

At most **96 new full executions / 48 million queries**, or **88 / 44 million**
with archived target-five reuse: 24 control records, 48 descendant cases and at most
24 conditional fresh cases. Native seed cache adds no execution. Small fixtures
are counted separately. Failed slots consume their allocation; partial cases are
never ranked as complete. Prior measured throughput (14.89 seconds per full case;
33m12s for the prior eight-descendant native run) supports six slots with time for
the conditional comparison and publication. Keep horizons intact and stop launching
work that cannot fit; do not fill unused allowance.

## Selection, conditional comparison and analysis

Rank complete valid native programs including seed by mean development offline
error, then earlier generation, then source SHA256. Fitness remains
`1/(1+mean_offline_error)`, with no complexity or variability bonus. Select the best
fixed target by mean error, then lower numeric target. Constants are legitimate.

Fresh work occurs only if a distinct native winner strictly beats both target five
and the best tested fixed target. Otherwise report and stop, with no separate
baseline-validation stage. Freeze sources, selected fixed control and the
[analysis specification](studies/book_mpso_population_v1/analysis_specification.json)
before generating eight fresh seed pairs excluding historical role seeds. Evaluate
selected, target five and the selected fixed target, aliasing identical control
labels. Never return fresh outcomes to evolution or revise the candidate afterward.

Use 20,000 independent paired-case bootstrap resamples, analysis seed **2026091609**,
descriptive 95% intervals, all case effects, mean/median, wins/losses, dispersion,
leave-one-out influence and retained unfavorable cases. These eight pairs are an
exploratory comparison, not a generalization guarantee or search-method comparison.

Record targets, realized counts, resizing, total particles/swarms over counted
evaluations, query shares and recovery during planned executions. Examples are
first update/detection and first updates reaching quarter/half/three-quarter budgets;
also show the largest favorable/unfavorable completed-environment paired contributions,
explicitly labeled post hoc extremes. No extra simulation replay. A constant gain is
population-size tuning; a conditional gain against 3/5/7 does not isolate adaptation's
causal value or exhaust constants. Publish the measured result and preserve prior
findings, rich README figures and exact archives regardless of outcome.
