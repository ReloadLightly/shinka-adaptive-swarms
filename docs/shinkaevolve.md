# Native ShinkaEvolve execution

The integration uses SakanaAI/ShinkaEvolve commit
`9912af12d423504b8d580f4179fd15f5f88b8c50` and its official
[subscription-backed Headless example](https://github.com/SakanaAI/ShinkaEvolve/tree/9912af12d423504b8d580f4179fd15f5f88b8c50/examples/sine_approx_headless).
Shinka performs parent/inspiration selection, candidate mutation, execution,
fitness-based selection, and archive/database updates. The launcher adds phase
logging; it does not replace those algorithms.

## What evolves

`tasks/adaptive_swarm/initial.py` contains the initial `choose_response` policy.
Its marked region can evolve relocation radius, relocated fraction, memory
handling, and velocity reset decisions as functions of observable swarm state.
The fixed simulator owns objective evaluations, random streams, landscape
changes, PSO, exclusion, and swarm creation/removal. Candidate evaluation invokes
the simulator with this policy; it does not call a language model.

The evaluator averages offline error across `configs/search.json`, returning
`combined_score = 1 / (1 + mean_offline_error)` because Shinka maximizes scores.
This strictly monotonic transformation preserves the ranking of lower raw
tracking errors and avoids a native summary display that initializes its best
score at zero. The evaluation version is `search_v1_score_reciprocal`. An earlier
seed verification used negative error; it is historical integration evidence,
and the changed score scale is not an improvement in swarm behavior. Per-case outcomes,
traces, response logs, and text feedback are retained. A search-suite score
improvement is a hypothesis to investigate with held-out comparisons and a
mechanism ablation. It does not establish general improvement by itself.
Candidate source should be audited before claiming an improvement: observations
exclude hidden landscape internals, but ordinary Python execution is not a hard
security boundary against deliberately inspecting other files or process state.

## Install and launch

The separate [allocation-v2 study](relocation_allocation_v2.md) evolves
`choose_relocation_count(observation) -> int` in
`tasks/relocation_allocation_v2/initial.py`. Its fixed adapter holds radius
multiplier 2, memory reevaluation and retained velocity constant. A new v2
reproduction uses `--task relocation_allocation_v2 --generations 20`; its default
suite and output root are `configs/relocation_allocation_v2/search.json` and
`results/relocation_allocation_v2/evolution`. V1 remains the default task.
Resumption infers the saved task, verifies its frozen sources and rejects a
conflicting explicit task. Validation and final selection use the separate
staged commands in the v2 report; changing a v1 suite alone does not implement
that protocol.

From the repository, in an activated Python environment:

```bash
python -m pip install -e '.[evolution]'
python scripts/check_runtime.py
python -u scripts/run_evolution.py --generations 20 --model gpt-6-astra --effort xhigh
```

The final command explicitly requests **inner mutation effort `xhigh`**. It is
not labelled Ultra. Omitting `--effort` passes no effort override and allows the
Codex profile/default to apply; the manifest records effective effort as
unverified, rather than inventing a value. `--generations 20` means the native
target of 20 generation slots including seed generation 0: at most 19 descendant
slots, with failed proposals recorded by the engine.

The default Headless command is pinned to
`npx -y @roberttlange/headless@0.6.1`. Node/npx, Codex CLI, and an existing
**ChatGPT subscription login** are needed on the executing machine. Check with
`codex login status`. Mutation consumes subscription allowance. Conventional
model APIs are not used or authorized. The runtime check sends no model request.

### Astra and Ultra are separate settings

Current [OpenAI model documentation](https://learn.chatgpt.com/docs/models)
identifies `gpt-6-astra` and describes Ultra as orchestration that uses subagents.
Select Astra and Ultra in the outer Codex interface for the coding/research work.
That does not establish an inner Headless `ultra` reasoning-effort setting.

Both the pinned [Shinka Headless provider](https://github.com/SakanaAI/ShinkaEvolve/blob/9912af12d423504b8d580f4179fd15f5f88b8c50/shinka/llm/providers/headless.py)
and Headless CLI 0.6.1 accept `low`, `medium`, `high`, and `xhigh`. Headless passes
that value to Codex as `model_reasoning_effort`. This matches the published
[Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).
No allowlist is patched and no lower setting is silently substituted. Availability
and actual execution of a chosen model still depend on the user's authenticated
Codex installation. A declared setting is not proof of executed inference.

## Baseline through the native engine, without a model

```bash
python -u scripts/run_evolution.py --seed-only
```

This executes generation 0 using the native scheduler and creates the native
database/archive. Its model pool is empty; embeddings, meta calls, and prompt
evolution are disabled. It needs Shinka installed but not Codex authentication.
The output is labelled **seed evaluation**, never a completed evolution search.

## Live visibility and retained evidence

Each new run creates a UTC timestamped directory under
`results/evolution/`. A process lock prevents duplicate controllers using that
results root. The launcher records explicit model/effort settings, suite hash,
generation target, phases, outcome, and errors in `manifest.json`, `events.jsonl`,
and `run.log`. Native Shinka also writes `evolution_run.log`, candidate programs,
mutation prompts, metrics, attempts, lineage, and `programs.sqlite`.

Each new run also freezes the evaluator, initial program, chapter-derived context
and actual task system prompt under `task_snapshot/`. Hashes identify the simulator,
baseline policy and Moving Peaks source. Candidate feedback includes per-regime
tracking error, error remaining at the end of each change interval, objective
evaluation shares and observed relocation behavior.

Resume an interrupted native run without duplicating its seed evaluation:

```bash
python -u scripts/run_evolution.py --resume results/evolution/<run-name> --generations 20
```

The saved search suite is reused automatically. Resume checks its hash, the
evaluation version and source snapshots, preserves initial metadata and appends
a continuation record. The generation target is the total desired count, not an
additional number of generations. Pass any intended inner model/effort overrides
explicitly; they are recorded as continuation settings. A temporary-copy test of
the pinned engine's generation-0 resume path passed with no repeated evaluation,
no proposal and unchanged existing program rows and evaluator outputs.

While a proposal is waiting for Codex, the heartbeat reports the actual current
activity every 20 seconds of silence. Evaluator progress is relayed live from
its child process logs. `--heartbeat-seconds`, `--proposal-timeout-seconds`, and
`--evaluation-timeout` are explicit runtime options. Output is flushed. Failures
and interruptions return nonzero exit codes while retaining completed records.

Native optional settings for this study are explicit: one proposal and one
evaluation at a time; two islands; parent/inspiration sampling and diff/full/
crossover mutations enabled; textual feedback enabled; embeddings, embedding-
based novelty filtering, LLM novelty judging, meta recommendations, and prompt
co-evolution disabled. No embedding API is called. Thus this is native
ShinkaEvolve with a declared feature configuration, not an assertion that every
optional mechanism from the paper is active.

## Native WebUI

```bash
bash scripts/webui.sh results/evolution 8888
```

Open `http://localhost:8888`. This invokes the pinned native
`shinka.webui.visualization` module and displays actual databases, programs,
metrics, and lineage. It can be launched separately during a run. The upstream
server listens on all local interfaces; use the localhost URL on your machine.
An empty directory is not evidence of an experiment, and a seed-only database
does not contain an evolved descendant.

Source verification date: 2026-09-15. The simulator and baseline can be tested
locally without claiming that authenticated model execution has occurred.
