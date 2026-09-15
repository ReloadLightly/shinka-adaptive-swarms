# Authorized Codex continuation

## Goal

Complete the first substantive `shinka-adaptive-swarms` experiment: documented reconstruction → real native ShinkaEvolve program evolution through the Codex subscription → independent frozen-program comparison → interpretable figures and scientific README → GitHub publication with verified remote commit.

Work from the existing repository and artifacts. The user has authorized this continuation, routine fixes, execution and publication. Continue through the result; do not stop after writing a plan, evaluator or launcher.

## User launch in WSL

For an existing checkout:

```bash
cd ~/actir/shinka-adaptive-swarms
code --new-window .
```

If a checkout is needed:

```bash
mkdir -p ~/actir
git clone https://github.com/ReloadLightly/shinka-adaptive-swarms.git ~/actir/shinka-adaptive-swarms
cd ~/actir/shinka-adaptive-swarms
code --new-window .
```

In the Codex interface, select the requested **Astra + Ultra** workflow and ask it to execute this handoff. Ultra may designate orchestration rather than a literal `model_reasoning_effort` value; do not pass an unverified `ultra` value to the CLI. A terminal launcher may use the installed runtime's verified equivalent and must describe the actual settings without relabeling them. Preserve live output and verify the launch outcome; a written command does not establish that a run started.

## Read first, then act

Read `README.md`, `docs/research_plan.md`, the current configuration, code provenance and run summaries. Inspect git status and active processes so a live experiment is not duplicated or interrupted. Reuse valid completed results. Perform only setup needed to execute this project.

The source anchor is Blackwell, Branke and Li (2008), pp.193–217, especially §4.2 and §5.1–5.3. The implementation anchor is DEAP revision `8a96fd3a75026f7b30e835f595a5199c75634ddf`, `examples/pso/multiswarm.py` and `deap/benchmarks/movingpeaks.py`.

Use the selected `(5+0)` baseline: five neutral particles, no permanent quantum particles, `NEXCESS=1`, UVD conversion after detected change, with the documented upstream correction. Call this a conceptual reproduction from an established implementation. Keep published values and new measured values separate. The initial reproduction configuration has three cases at 500,000 evaluations each. Pinned DEAP source severity is 1.0 despite stale descriptive text suggesting 1.5; override its correlation default of 0.5 with the book's 0.0 explicitly.

## Execute the experiment

1. **Reuse the completed baseline.** `artifacts/reconstruction_v1/summary.json` records three cases × 500,000 evaluations, mean error 1.7024473162. Read its evidence and `docs/reproduction.md`; rerun only to resolve a concrete remaining risk. The chapter’s 50-run table is a reference, not a requirement to delay model evolution. The committed native seed check also already succeeded, without model calls.
2. **Run real ShinkaEvolve.** After `bash scripts/setup.sh` and `source .venv/bin/activate`, use `python -u scripts/run_evolution.py --generations 20` with the native Headless Codex subscription provider. This requests 20 native generation slots, including the seed and up to 19 descendant slots. Adjust for a justified experimental reason or user steering; it must not become an arbitrary gate. Keep native mutation, evaluation, island archive and lineage. The initial configuration enables text feedback and disables embeddings/novelty, meta-recommendations and prompt evolution. Record actual calls and candidates. Do not claim that a hand-written challenger is an evolved result.
3. **Keep progress visible.** Print active stage, candidate/generation, completed evaluations, measured outcomes and saved paths. During long calls or evaluations, emit an honest heartbeat every 15–30 seconds. Run `bash scripts/webui.sh` and point it at the native archive. Verify the page and archive when accessible; report if browser verification is unavailable.
4. **Compare the frozen program.** Select using search data, save the selected program, then compare it with the fixed baseline on new seeds. Match objective-query budgets and environmental histories where feasible. Include targeted changed conditions that test the mechanism. Save each completed case and report paired effects and uncertainty. Preserve and explain a null or negative finding.
5. **Explain behavior.** Inspect the evolved source and traces. Perform a focused ablation of the mechanism actually found, where it answers a concrete question. Generate plots with `python -m adaptive_swarms figures --run <run-directory>` and update documentation from saved outcomes.
6. **Publish.** Update README’s abstract, results, discussion, commands and provenance to match what actually ran. Update the GitHub About description if needed. Commit the complete relevant work, push it, and verify that local `HEAD` equals the remote branch commit. Report the SHA and links.

## Execution requirements

- Use the existing authenticated Codex subscription for model calls. No paid API fallback and no separate API-credit requirement. If native Headless authentication fails, diagnose the actual route rather than silently changing provider.
- Use the requested Astra/Ultra supervising mode where the Codex interface provides it. Verify supported CLI settings before configuring a terminal launch; do not invent a literal `ultra` reasoning value or silently label another setting Ultra. Record the inner mutation model identity actually used; outer settings do not automatically configure inner calls. Default inner effort is unspecified and unverified, not Ultra.
- Keep the benchmark, objective-query accounting and hidden optimum outside candidate control. Evolve the adaptation program through the supported interface. Explain any necessary interface change before interpreting its results.
- Preserve existing source changes, programs, native databases, partial results and logs. Resume instead of blanket rerunning completed work.
- Do not add arbitrary Windows/Linux RAM reserves, experimental stop thresholds, repeated approvals or unrelated infrastructure tasks. Use normal failure handling and incremental saving. Keep retries bounded to the observed fault.
- If a real external blocker persists, save the complete continuation state and identify the failing command, observed error, completed work and exact next action. A blocker is not successful execution.

## Completion report

Report baseline evidence, actual ShinkaEvolve proposal and evaluation counts (novelty is disabled in the initial configuration), selected program and its behavior, completed independent cases, paired outcomes, limitations, figure paths, native archive location and local/remote commit verification. Clearly distinguish completed experiments from pending work. The user should be able to open the repository and see the substantive research result.
