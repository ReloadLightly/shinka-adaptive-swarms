# Corrected 200-peak campaign — Session 2 continuation

**Session 2 was launched on 18 September 2026 at 08:18:43 UTC from the
published Session 1 checkpoint.** This is a running-session record, not final
selection or a completed-session publication. The launch inherited six valid
descendants (generations 1–6), seed generation 0, all seven constant controls,
and 44 completed physical cases / 22 million objective queries.

The native controller resumes generation 7 and allows at most six further
terminal slots, through generation 12. It retains the 50-descendant campaign,
400-response campaign ceiling and 80-response session allowance. The research
cutoff is 10:58:43 UTC, with the final 20 minutes of the 180-minute ceiling
reserved. No subsequent session or fresh comparison is automatically launched.

## Restoration and actual continuation

This workspace had no live run or Python environment. All 303 files in the
immutable Session 1 manifest passed SHA-256 and size checks before copying to
`results/book_mpso_population_200_v2/20260917T065325Z`. SQLite integrity was `ok`,
with seven valid program rows. The archived `publication_ready` session status
was reconciled to `published` in the live copy using the already-published
Session 1 receipt; the archive was not modified.

The pinned Shinka revision, Python 3.10.12, NumPy 2.2.6 and pinned local embedding
model were restored. The checkpoint validated five processed and two pending
meta programs. At 08:19:01 UTC, the real native controller logged
`campaign_restored`, including `rng_restored=True`, before generation 7 sampling.
This observes an actual restart with retained state; it does not promise identical
future LLM responses. Completed controls were checked and reused without new
objective evaluations.

The first generation-7 attempt selected generation 4 as parent and used a full
rewrite. It repeated generation 6's capped-workload rule. Native novelty rejected
it at 08:20:15 UTC before numerical evaluation, then sampled generation 5 as
parent for a second attempt within the same slot. Rejected attempts consume their
actual model responses and retain their prompts/sources; they are not counted as
completed generations or new optimizer findings.

The second attempt, `soft_refresh_discount`, was accepted and entered numerical
evaluation around 08:22 UTC. It replaces generation 5's hard residual-loss cap
with `0.75 * detected_loss + 0.25 * min(detected_loss, residual_loss)`, leaving
the unbounded workload penalty and thresholds unchanged. This tests partial
discounting by refreshed memories. It is a hypothesis about recovery, not an
established gain; a complete four-history score is required before ranking.

The running Codex child was directly observed with `gpt-6-astra` and
`model_reasoning_effort=xhigh`. `codex login status` confirmed ChatGPT subscription
authentication. These are inner settings; supervising Astra/Ultra remains the
client-requested setting and is not inferred from child receipts. No paid API
fallback is enabled. Shinka's displayed dollar amounts are estimates.

## What each program tests and what the logs explain

Every admitted program chooses an integer neutral target from 2 through 8 after
detected change and counted memory refresh. The fixed adapter changes population
by at most one, retaining the permanent quantum particle and corrected engine.
The same four five-dimensional, 200-peak development histories each receive
500,000 objective queries. Detection and memory refresh count toward that budget;
environment RNGs remain independent of optimizer RNGs. Mean offline error is the
ranking criterion, with frozen evolutionary feedback against targets three/five.

The added observational logger records:

- `scientific_test`: intervention, fixed mechanisms, histories, budgets and
  development-only interpretation.
- `program_under_test` and `program_change`: exact parent/inspiration identities,
  mutation type, author's hypothesis, source hash, referenced observation fields
  and line-by-line executable differences.
- `program_measured`: validity, completed cases, observed mean error and difference
  from the actual parent; invalid/partial programs do not claim an improvement.

Native sampling, novelty, evaluation, per-case checkpoints and meta updates retain
their existing logs. Timestamped, flushed heartbeats mean a process is waiting for
a result; they do not represent token streaming or access to hidden reasoning.
The hypothesis text is attributed to the proposing model and is distinct from
observed behavior and performance. This logging adds no candidate observations,
scientific changes, objective evaluations or model calls.

Twenty-three focused resume/control checks passed. The narrative logger was
checked on archived generation 4 and on an invalid-outcome fixture, using zero
additional objective/model calls. The browser displayed all seven existing native
programs, the actual generation-4 source and its lineage, with no reported errors.

## Watch the running session

[Native Shinka WebUI](http://localhost:8899/viz_tree.html?db_path=search_seed_670001%2Fprograms.sqlite)

```bash
# Complete session terminal, including child output and explanatory events:
tail -F results/book_mpso_population_200_v2/20260917T065325Z/operations/session_002-terminal.log

# Focused native progress and persistent explanations:
bash scripts/progress.sh results/book_mpso_population_200_v2/20260917T065325Z/evolution/search_seed_670001

# Only if the existing viewer has ended and port 8899 is free:
bash scripts/webui.sh results/book_mpso_population_200_v2/20260917T065325Z/evolution 8899
```

Do not launch a second controller while this one is active. If interrupted before
its deadline, resume with the existing session allowance:

```bash
.venv/bin/python -u scripts/run_population_campaign.py session \
  --run results/book_mpso_population_200_v2/20260917T065325Z --minutes 180
```

Restoration, process launch, actual model arguments and browser verification
receipts are retained in the live `operations/` directory. Session metadata is
under `sessions/session_002/`; each completed numerical case is independently
checkpointed. The unchanged [Session 1 report](REPORT.md) remains the completed
historical record.

The separately requested [cross-substrate emergence research](../../emergence_across_substrates.md)
distinguishes collective dynamics inside an imposed cooperative optimizer from
voluntary cooperation and institution formation. It proposes falsifiable future
tests without adding them to this campaign.
