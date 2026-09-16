# Evolving Adaptive Collective Search

**LLM program evolution for dynamic multi-swarm optimization**

This project studies whether ShinkaEvolve can discover better adaptation rules for a population of particle swarms searching a changing landscape. The starting point is the multi-swarm particle swarm optimizer described by Blackwell, Branke and Li in *Swarm Intelligence: Introduction and Applications* (2008), reconstructed from an established DEAP implementation.

**Status (16 September 2026):** crash recovery confirmed the native 20-generation search had already completed; all 80 search cases were preserved without reevaluation. The pending independent comparison and mechanism study are now complete: eight cases × four methods × 100,000 objective evaluations. The selected program improved search error but did **not** outperform the corrected baseline on the independent suite. The native WebUI is restored. See [results and mechanism analysis](docs/comparison.md) and [recovery and live terminal commands](docs/recovery.md).

## Abstract

Collective search must preserve useful information while responding to environmental change. We reconstructed a corrected multi-swarm particle swarm optimizer and used native ShinkaEvolve to generate 19 descendants through subscription-authenticated Codex. The selected program adjusts relocation radius and particle fraction using observed fitness loss and swarm spread. Its mean search offline error fell from 2.7751 to 1.9703, but its independent mean error was 3.7857 versus the baseline's 3.7230. A parent ablation and a fixed-response control provide no clear evidence that the evolved observation dependence is beneficial on this small suite. The contribution is an executable, traceable study of a search improvement that did not establish generalization, with matched objective budgets and preserved lineage.

## Research question

**Can evolved control programs improve the tracking of moving optima, and which changes to collective search explain any improvement?**

The central tension is between concentrating evaluations on promising regions and keeping enough exploratory capacity to find displaced or newly competitive peaks. We examine this tension through observable swarm behavior and tracking error.

## Background and provenance

The case study comes from [“Particle Swarms for Dynamic Optimization Problems”](https://doi.org/10.1007/978-3-540-74089-6_6), pp.193–217, especially multi-swarm PSO (§4.2, pp.201–204), the Moving Peaks setup (§5.1, pp.208–209), and the particle-conversion comparison (pp.210–211).

The reconstruction uses DEAP commit **`8a96fd3a75026f7b30e835f595a5199c75634ddf`**:

- [Multi-swarm optimizer example](https://github.com/DEAP/deap/blob/8a96fd3a75026f7b30e835f595a5199c75634ddf/examples/pso/multiswarm.py).
- [Moving Peaks implementation](https://github.com/DEAP/deap/blob/8a96fd3a75026f7b30e835f595a5199c75634ddf/deap/benchmarks/movingpeaks.py).

This is a **conceptual reproduction using a later established implementation**. It does not claim possession of the authors’ original code, original seeds, or exact numerical reproduction of every table. Upstream code, local corrections and experimental extensions are recorded separately.

## Method

The baseline uses five neutral particles per subswarm, no permanent quantum particles, one desired free swarm (`NEXCESS=1`), and temporary UVD particle conversion following detected environmental changes. Here “quantum” denotes stochastic particle placement in a search region; no quantum hardware is involved.

The benchmark exposes evaluated objective values to the optimizer. Its latent peak positions and optimum are used for measurement, not as privileged inputs to the adaptation program. Every objective query, including change detection and memory reevaluation, counts toward the evaluation budget.

ShinkaEvolve modifies `choose_response(observation)` in `tasks/adaptive_swarm/initial.py` through its native proposal, evaluation, island archive and parent-selection workflow. The initial configuration enables measured text feedback and disables embedding novelty checks, meta-recommendations and prompt evolution. The program controls relocation radius, the fraction of particles relocated, whether remembered solutions are reevaluated or reset, and whether velocity is reset after detected change. It receives optimizer-visible state such as fitness deterioration, recent improvement, swarm diameter and prior response information. Candidate programs are executed against the benchmark and archived with feedback and ancestry. The measured landscape and result accounting remain outside the candidate interface; Python execution is not a security sandbox, so selected programs must also be inspected for prohibited access.

The primary outcome is **offline error**: the average gap between the current optimum and the best solution found since the latest environmental change. Lower values indicate better tracking. Native selection maximizes `1 / (1 + mean_offline_error)`; the research report retains the underlying error, recovery trajectories, swarm counts and evaluation use. [Scientific context](docs/evolution_context.md) is supplied to the mutation prompt and saved with each new run.

## Reproduction

The book’s reference configuration is Moving Peaks Scenario 2:

| Setting | Book reference |
|---|---:|
| Dimensions | 5 |
| Search domain | `[0, 100]^5` |
| Peaks | 10 |
| Peak height interval | `[30, 70]` |
| Peak width interval | `[1, 12]` |
| Evaluations between changes | 5,000 |
| Change severity | 1.0 |
| Movement correlation | 0 |
| Evaluations per run | 500,000 |
| Independent runs in the book | 50 |

Table 3 on p.211 reports offline error **1.80 (standard error 0.08)** for the `(5+0)` configuration with `NEXCESS=1`. This is a published comparison point, **not a result obtained by this repository**. The initial reconstruction configuration uses three independent cases at 500,000 evaluations each. The pinned DEAP source sets movement severity to 1.0, despite a stale description suggesting 1.5, and uses correlation 0.5; this project explicitly sets correlation to the book's 0.0. Sample sizes and other implementation differences must accompany the results.

Install the pinned research environment (Python 3.10+; `uv` is preferred):

```bash
bash scripts/setup.sh
source .venv/bin/activate
python -m pytest -q
```

Completed reconstruction outputs are already in [artifacts/reconstruction_v1](artifacts/reconstruction_v1). To perform a new reconstruction:

```bash
python -m adaptive_swarms baseline --config configs/reproduction.json
```

## Experiments

1. **Reconstruction:** establish that the documented baseline tracks a changing landscape and that its individual mechanisms behave as specified. Record numerical agreement and remaining differences with the book.
2. **Program evolution:** run native ShinkaEvolve from the baseline adaptation program, initially requesting 20 generation slots: one seed and up to 19 descendant slots. This is a practical first search size and can be changed; it is not an evidence threshold.
3. **Independent comparison:** freeze the selected program and compare it with the baseline on previously unused seeds and changes in environmental conditions, using matched objective-query budgets.
4. **Mechanism study:** inspect the evolved code and traces, then remove the mechanism that appears to explain its behavior. Add only comparisons that answer a concrete remaining question.

```bash
# Terminal 1: requires Codex CLI authenticated with a ChatGPT subscription
python -u scripts/run_evolution.py --generations 20

# Terminal 2: native live archive, open http://localhost:8888
bash scripts/webui.sh results/evolution

# Inspect the published native search without making model calls
bash scripts/webui.sh artifacts/evolution

# Reconnect to timestamped progress without launching another controller
bash scripts/progress.sh

# Regenerate the scientific figures from completed measurements
python -m adaptive_swarms figures --run artifacts/reconstruction_v1 --output assets/reconstruction
python scripts/plot_evolution.py --run artifacts/evolution/20260915T101024.562418Z-search
```

Run only one WebUI command on a given port. The native WebUI exposes candidate source, measured fitness, ancestry and the archive as it grows. Terminal output identifies active stages, proposal/case identities, measured outcomes and saved paths. Evaluation progress is relayed live; a 20-second heartbeat identifies waiting during model calls. Each run saves `run.log`, `events.jsonl`, manifests, case data and the native `programs.sqlite`. This is operational logging, not a promise of streamed model reasoning. Recovery verification passed HTTP, database, browser navigation and source/ancestry checks. No browser page errors occurred; the native Plotly dependency emitted a deprecation warning. See [native integration](docs/shinkaevolve.md), [the research plan](docs/research_plan.md) and [the Codex handoff](docs/codex_handoff.md).

### Artifacts and resumption

Readers accept both legacy JSON and compressed case traces. Completed cases,
accepted native proposals, lineage, rotated logs and `best/artifacts.json`
references remain available. The launcher has no mandatory `/mnt/c` verification,
free-space floors, worker storage allowances, checkpoint-write cap, or low-space
cancellation watcher. Actual I/O failures remain errors and do not become
scientific fitness judgments.

The run `results/evolution/20260915T101024.562418Z-search` finished before the
crash: generations **0–19** are complete, with **21 database rows** including
the native seed island copy. Recovery verified all **80 saved cases**, database
integrity, parent links and best-artifact hashes. No search controller restart
was needed. The native WebUI was restarted on the original database; a consistent
SQLite backup preserved its WAL state. The comparison continued in a new directory,
`results/comparison/20260916T001949Z-frozen`, checkpointing all 32 method cases.
The complete search and comparison are published under [artifacts](artifacts/README.md).

For an unfinished run, retain its original target and saved scientific settings:

```bash
.venv/bin/python -u scripts/run_evolution.py \
  --resume "results/evolution/<unfinished-run>" \
  --generations 20 --model gpt-6-astra
```

The saved inner effort for the completed run remains unspecified. Comparison
execution makes no model calls. For the completed comparison's checkpoint-based
resume command and terminal/WebUI attachment, see [recovery](docs/recovery.md).
Historical [artifact compatibility and rollback verification](docs/storage.md)
remain available.

## Results

| Evidence | Current status |
|---|---|
| Baseline reconstruction | 3 × 500,000 evaluations; mean offline error **1.7024**, sample SD **0.7896** |
| Native seed evaluation | 4 × 50,000 evaluations; mean offline error **2.7751**, selection score **0.264895** |
| Native ShinkaEvolve descendants | **19 evaluated descendants**; selected generation 12, mean search error **1.9703**, score **0.336661** |
| Frozen-program independent comparison | **8 × 100,000 evaluations per method**; baseline **3.7230**, selected **3.7857** |
| Mechanism comparisons | Native parent without compactness rule **3.8037**; fixed response **3.4496** on the same eight cases |

Individual reconstruction errors were 2.4152, 0.8536 and 1.8384. Three cases do not establish numerical equivalence to the book's 50-run result, and implementation differences remain documented in [the reproduction record](docs/reproduction.md). The seed evaluation uses a different, shorter search suite; its error should not be compared directly with the reconstruction mean. Native initialization stores the seed and an island copy: two database rows represent one evaluated program, not two discoveries.

The selected [generation-12 program](artifacts/comparison/20260916T001949Z-frozen/programs/selected.py) uses fitness deterioration to adjust relocation, preserves more particles when the swarm already covers a broad region, and adds a recovery floor for compact swarms. Memory reevaluation and retained velocity remain baseline choices. The native parent chain is **0 → 4 → 9 → 10 → 12**. The [published native archive](artifacts/evolution/20260915T101024.562418Z-search) contains the actual subscription-backed mutations, explanations, programs and measured cases.

![Measured native search outcomes across 20 generation slots](assets/evolution/search_progress.png)

*Five-dimensional search: four cases × 50,000 evaluations per program. The seed island copy is counted once. These repeatedly used search cases do not establish generalization.*

On eight fresh cases across four regimes, **selected minus baseline error was +0.0627**, with a stratified bootstrap 95% interval **[−0.1470, +0.2724]**; negative favors the selected program. It improved two cases and worsened six. Removing the compactness addition changed mean error by **+0.0180** relative to selected, with interval **[−0.3253, +0.3612]**. The fixed control (radius scale 2, fraction 0.6) had lower error than selected by **0.3361**, but it is an investigator-defined control, not an evolved discovery. Its interval against the baseline still spans zero.

Each regime has only two independent cases, so bootstrap coverage is uncertain and broad generalization is unsupported. Budgets include detection and memory queries; paired methods encountered identical landscape histories. Programs were frozen before independent execution, with the pre-freeze audit's configuration access disclosed in the selection record. See [the full report](docs/comparison.md) for regime effects, behavior, provenance and limitations.

![Measured paired outcomes and uncertainty for the independent five-dimensional comparison](assets/comparison/paired_offline_error.png)

*Eight independent paired landscapes; four frozen methods, each with 100,000 objective evaluations per case. Dots are cases, not trajectory checkpoints.*

![Measured cumulative tracking error and swarm count over three 5D reconstruction cases](assets/reconstruction/baseline_tracking.png)

*Five-dimensional reconstruction: cumulative offline error and swarm count, computed from saved evaluation traces.*

![Allocation of objective evaluations in the reconstruction](assets/reconstruction/evaluation_accounting.png)

*Objective queries used by ordinary search, change detection, memory updates and other baseline operations. Detection and memory costs are included in the budget.*

![Illustrative two-dimensional swarm dynamics](assets/illustration/swarm_dynamics.gif)

*Separate two-dimensional illustration with five peaks and larger movement severity. This makes particle behavior visible; it is not one of the three five-dimensional reconstruction cases. Environment changes and particle positions come from recorded simulation snapshots.*

Raw data, logs and archive databases are committed under [artifacts](artifacts/README.md), with a SHA-256 inventory. The earlier negative-score seed check is preserved as integration history and clearly distinguished from the corrected positive-score seed check.

## Discussion

The search successfully generated executable, traceable adaptation rules, but its best search score did not establish an independent performance advantage. The compactness mechanism helped some fresh cases and hurt others; its small pooled effect is inconclusive. A fixed response performed better than the selected program in this suite, so the observations do not support attributing value to the added adaptation complexity. Floating-point rounding at the simulator's `ceil(fraction × 5)` boundary also affects how many particles actually move; the study retains that executed behavior and reports actual relocation counts.

This study concerns dynamic optimization in a synthetic environment. Applications to robotics, resource allocation or policy require their own models and evidence. Differences in random number generation, boundary handling, change timing, particle conversion and objective-query accounting may affect numerical comparability with the 2008 results.

## Reproducibility

Reported runs retain configurations, environment and algorithm seeds, source provenance, evaluation budgets, programs, per-case outcomes and timing. This first build ran before the initial Git commit; its manifests say so explicitly and include source fingerprints instead of an invented revision. Dependencies are locked in `uv.lock`; ShinkaEvolve is pinned to `9912af12d423504b8d580f4179fd15f5f88b8c50`. Evolutionary runs additionally retain native records, requested model settings, actual call outcomes and resume information. Corrected upstream behavior is documented separately from evolved changes.

The intended model route uses an authenticated Codex subscription through ShinkaEvolve’s native Headless provider. It must not silently fall back to a paid API. The requested supervising workflow is **Astra + Ultra in the Codex interface**. A UI orchestration mode must not be silently translated into an unsupported CLI reasoning value; launch configuration and the actual inner model settings are recorded separately.

For the WSL workspace:

```bash
cd ~/actir/shinka-adaptive-swarms
code --new-window .
```

Select the requested Astra/Ultra mode in Codex, then use [the continuation handoff](docs/codex_handoff.md). A terminal launcher can be used when its settings are supported by the installed runtime. The continuation covers execution, result interpretation, README updates and GitHub publication. Existing valid results are reused.

The included `.vscode/tasks.json` provides setup, reconstruction, native evolution and WebUI terminal tasks. `scripts/codex_work.sh` can save an interactive Codex terminal transcript. The default inner mutation route is `headless/codex@gpt-6-astra`; no explicit inner effort is set or claimed to be Ultra. See [the runtime notes](docs/shinkaevolve.md) before changing that setting.

## References

- Blackwell, T., Branke, J., & Li, X. (2008). [Particle Swarms for Dynamic Optimization Problems](https://doi.org/10.1007/978-3-540-74089-6_6). In C. Blum & D. Merkle (Eds.), *Swarm Intelligence: Introduction and Applications*, pp.193–217. Springer.
- Blackwell, T., & Branke, J. (2006). [Multiswarms, exclusion, and anti-convergence in dynamic environments](https://doi.org/10.1109/TEVC.2005.857074). *IEEE Transactions on Evolutionary Computation*, 10(4), 459–472.
- DEAP contributors. [DEAP](https://github.com/DEAP/deap), pinned source revision above. Upstream licensing and notices apply to reused source.
- Sakana AI. [ShinkaEvolve](https://sakanaai.github.io/ShinkaEvolve/) and [source repository](https://github.com/SakanaAI/ShinkaEvolve).

Citation metadata for this repository is available in [CITATION.cff](CITATION.cff).
