# Resume the corrected 200-peak population campaign

**18 September 2026 update:** [Session 2](SESSION_002.md) was launched at 08:18:43
UTC from generation 7. Attach to its log/WebUI while it runs; do not execute the
`--new-session` command concurrently. The current research cutoff is 10:58:43 UTC.
Its terminal log is `operations/session_002-terminal.log` under the live run.
At 09:17 UTC, generations 8 and 9 were complete and Shinka was updating
meta-memory before generation 10: eight valid descendants plus seed, with generation 7 an operational
failed slot. The current controller resumed at 09:15:54 after a reviewed
generation-9 fourth-case recovery; do not launch a second controller.
At 08:33 UTC it recovered from an optimizer-runtime restoration error and resumed
generation 8 with the same limits; generation 7 remains an operational failed slot.
The optimizer requires the archived **Python 3.13.5 / NumPy 2.5.3** runtime. The
Python 3.10.12 encoder is separate. The launcher now checks this before any calls.
The instructions below remain the procedure for subsequent explicitly launched
sessions after a published pause, or recovery of the current session as indicated.

This procedure resumes the same campaign, database, immutable task snapshot and
four development histories. Session 1 is an interim checkpoint, not a six-slot
scientific study. A later session requires a new user launch.

From `/home/roland/actir/shinka-adaptive-swarms`, the next user-authorized session
has this single command (180 minutes, including a final 20-minute reserve):

```bash
.venv/bin/python -u scripts/run_population_campaign.py session \
  --run results/book_mpso_population_200_v2/20260917T065325Z \
  --minutes 180 --new-session --control-targets 2,4,6,7,8
```

The new session checks the constant-target controls using individual checkpoints
and finishes any remaining cases, then admits native descendants only if a complete four-history
evaluation, model/novelty work and draining fit. Targets three/five remain the
unchanged evolutionary feedback references. The launcher retains `--generations
51 --logical-response-limit 400`; the new session receives at most six additional
terminal slots and an 80-response delta allowance. All attempted full budgets
remain in the cumulative 400-attempt/200-million-query ledger. Proven literal native
constants can supply execution-identical control cases: source, database, scientific
fingerprint, case pairing and counted attempts are checked, and the original native
attempt is counted once. The imported control label adds zero queries. Ceilings are not
usage targets. It does not launch another session or fresh comparison.

If the *current* session is interrupted before publication, resume it without
`--new-session`; this preserves its deadline, response baseline and cumulative
slot stop. Incomplete numerical attempts require explicit recovery review and are
not silently repeated or assigned an inferior score.

```bash
.venv/bin/python -u scripts/run_population_campaign.py session \
  --run results/book_mpso_population_200_v2/20260917T065325Z --minutes 180
```

Each native session restores validated summary/scratchpad, recommendations/history,
pending evaluated program IDs and processed counts before proposing. Database
commits ahead of a checkpoint reconcile once; unknown/duplicate IDs fail visibly.
Python/NumPy sampler state is restored at drained boundaries. Accepted pending
proposals retain their source and generation. An interrupted provider operation
cannot promise an identical future LLM response or RNG replay between checkpoints.
Normal interval-five meta remains active; the extra closing meta summary waits
until campaign completion.

The live run is preserved in `results/`; immutable publication snapshots are under
`artifacts/book_mpso_population_200_v2/20260917T065325Z/session_001/` and later
session directories. Do not start a new empty campaign if the live directory is
missing: restore/reconcile the latest published checkpoint first. The command
above targets this workspace's retained live directory.

```bash
tail -F results/book_mpso_population_200_v2/20260917T065325Z/operations/run.log
bash scripts/progress.sh results/book_mpso_population_200_v2/20260917T065325Z/evolution/search_seed_670001
# Only if this viewer is no longer running; do not replace an occupied port:
bash scripts/webui.sh results/book_mpso_population_200_v2/20260917T065325Z/evolution 8899
```

WebUI: `http://localhost:8899/viz_tree.html?db_path=search_seed_670001%2Fprograms.sqlite`.
The viewer reads the real native database and makes no research/model calls.
Native roles use the existing subscription-backed `gpt-6-astra/xhigh` route and
local embedding service at port 8910. It is not inner Ultra. No provider switch,
global settings change or paid API fallback is part of this procedure.

After 50 terminal descendant slots and all seven constants, perform the registered
final selection and only then determine whether later fresh testing is warranted.
Session reports must not freeze a winner or trigger fresh cases from interim scores.
See the [prospective analysis](analysis_specification.json) and
[protocol](../../book_mpso_population_200_v2_protocol.md).
