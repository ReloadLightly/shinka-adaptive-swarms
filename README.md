# Evolving Adaptive Collective Search

**Interpretable program evolution for multi-swarm optimization in changing environments**

## Abstract

Can a learned recovery rule improve how particle swarms track moving optima? We reconstruct the
Blackwell–Branke–Li multi-swarm optimizer from pinned DEAP source and evolve response programs with
native ShinkaEvolve. Across the earlier studies, better development scores have not established a
useful conditional recovery mechanism. In V3, joint count/radius evolution produced a selected rule
whose difference from the corrected baseline on 80 fresh histories was **+0.0227**, with a **97.5%
interval [−0.2044, +0.2368]**; lower error is better. The bounded radius/velocity sprint finds a
small mean interaction (**−0.0440**) with large case dispersion (**SD 0.8362**) on eight reused
development histories. Native evolution selects a simple constant: relocate four particles at radius
multiplier **1.25**, retaining velocity. Its eight-case fresh pilot difference from the original
baseline is **−0.6303 [−1.4721, +0.2241]** (descriptive 95%), strongly influenced by one retained
large benefit. Neither useful conditional recovery nor velocity-mediated overshoot is established.

The [sprint report](docs/sprints/radius_velocity_20260916/REPORT.md) contains exact programs,
measured feedback, native lineage, resource accounting and the next experiment. The [pre-search
interim record](docs/sprints/radius_velocity_20260916/INTERIM.md) shows what the diagnostic changed
before any native descendants were evaluated.

## Question and source

**Does relocation radius interact with retained particle velocity, and can native evolution find a
useful recovery rule?** Blackwell, Branke and Li (2008), printed p.215, suggest retained velocity as
an explanation for relocation overshoot and preferred radius. This is a hypothesis: tracking-error
interactions can also reflect swarm spread, later PSO motion, query allocation or stochastic
closed-loop trajectories, without identifying an overshoot mediator.

The reconstruction uses DEAP revision `8a96fd3a75026f7b30e835f595a5199c75634ddf`. Its particle-conversion
correction is baseline work. [Source fidelity](docs/reproduction.md) records numerical choices and
historical uncertainty; exact book-table reproduction or superiority to stronger variants is not claimed.

## Method

The simulator has five dimensions, ten moving conical peaks, five particles per subswarm, exclusion
and adaptive swarm birth/removal. The corrected baseline relocates all five particles in a
uniform-volume ball of radius `0.5 × severity`, reevaluates memories and retains velocity. Each
sprint case uses **100,000 queries**, counting detection, memory and exclusion. Severity/period
regimes `{1, 3} × {2,500, 5,000}` receive equal case counts.

**Offline error** averages the optimum-to-best-discovered fitness gap since the latest change;
smaller is better. Native fitness is `1/(1+mean_offline_error)`. Separate RNGs permit paired
landscape histories, verified by hashes. Matched optimizer seeds do not imply identical subsequent
perturbations or states: policies change complete trajectories and may consume different random
draws.

The [current task](tasks/radius_velocity_sprint) fixes count four and memory reevaluation. It
evolves `choose_recovery(observation)`, returning `radius_scale` and `reset_velocity`; reset zeros
relocated particles’ velocity at their update. Public state includes fitness loss, diameter, recent
progress and default radius; hidden peaks, optima, seeds and pilot outcomes are excluded. Constants
and conditions share the same objective without complexity bonuses. Exact sources are reviewed
before transfer.

ShinkaEvolve revision `9912af12d423504b8d580f4179fd15f5f88b8c50` and the named [sprint
profile](configs/shinka/radius_velocity_sprint.json) retain weighted parents, two islands,
inspirations, migration, embedding-plus-LLM novelty and meta-memory from `research_v3`. Prompt
co-evolution stays off; mutation uses one fixed model. Actual feedback adds paired baseline/seed
differences, regime means and action occupancy. Native search controls proposals, selection and
ancestry.

All roles use subscription-authenticated `headless/codex@gpt-6-astra`, with no paid fallback.
Requested supervising Astra/Ultra differs from inner calls with no effort override and an unverified
effective default. Existing local embeddings are reused. [Sprint
limits](docs/radius_velocity_sprint_protocol.md) are local: 180 minutes, 168 full executions before
reuse and 60 requested native logical responses including retries; they do not restrict future
research.

## Results

### Radius and velocity: exploratory mechanism experiment

Six methods share eight recorded V3 development histories, two per regime. New traces sample every
25 queries; a focused numerical check verifies that recording density leaves the optimizer's
outcomes unchanged. All 48 cases, including unfavorable outcomes, remain in the analysis.

| Response | Mean offline error |
|---|---:|
| Count 4, radius 1, retain velocity | **3.041839** |
| Count 4, radius 1.5, retain velocity | 3.089088 |
| Count 4, radius 1, reset velocity | 3.329122 |
| Count 4, radius 1.5, reset velocity | 3.332410 |
| Original baseline: count 5, radius 1, retain | 3.423599 |
| Exact frozen V3 selected policy | 3.152140 |

Within each history, the interaction is `(error[1.5, reset] − error[1, reset]) − (error[1.5, retain]
− error[1, retain])`. Its mean is **−0.043961**, SD **0.836208**, range **[−1.815428, +0.930971]**.
Increasing radius changes mean error by **+0.047249** with retained velocity and **+0.003288** with
reset. Reset itself costs **+0.287283** at radius one and **+0.243322** at radius 1.5 on average.
Opposing individual and regime effects make a broad overshoot explanation unsupported; eight
histories are not a significance gate or evidence that no interaction exists.

The direct **count 4 / radius 1.5 / retained velocity** control clarifies V3's nearly constant rule.
The exact historical policy has **+0.063052** higher mean error than that constant (paired SD
**0.391413**, range **[−0.559022, +0.832095]**). It chooses count three on **7.26%** of responses
with equal case weighting, otherwise four, and always uses radius 1.5. This reused development
subset does not replace V3's fresh final comparison or confirm a constant advantage.

![Measured five-dimensional radius–velocity interaction and recovery](assets/radius_velocity_sprint/phase_a_interaction_recovery.png)

*Dots are paired histories; diamonds are means. Recovery uses actual recorded query offsets,
excludes the initial landscape, averages environments within case and then cases equally. No
unrecorded immediate response is interpolated.*

### Native discovery and exploratory transfer

One native search completed **13 terminal slots / 12 valid descendants**. Generation 3, from seed
generation 0 with generation 2 as archive inspiration, was selected on development error
(**2.886761**). Its exact recovery function is:

```python
def choose_recovery(observation: dict) -> dict:
    return {"radius_scale": 1.25, "reset_velocity": False}
```

The adapter fixes count four and memory reevaluation. Frozen before new pilot seeds existed, this
constant averaged **3.562580** versus baseline **4.192856** on eight fresh paired histories:
**−0.630275**, SD **2.277171**, descriptive 95% paired-bootstrap interval **[−1.472066, +0.224123]**. Four cases
improved and four worsened; a **−6.197993** difference in case seven strongly influences the mean
and remains included. This small probe compares complete methods, without isolating radius tuning or
establishing generalization, equivalence or a conditional mechanism.

The sprint used **160 new full executions / 16 million queries**: 48 diagnostic, 96 native and 16
pilot cases. Eight seed cases were reused exactly; eight repeated descendant cases consumed queries
and remain counted. Native receipts record **45 logical responses**: 13 mutation, 13 novelty and 19
meta, within the 60 limit. Small implementation fixtures and unobserved provider retries are
separate.

**Next experiment:** keep the constant as a candidate and compare count four/radius one with
count four/radius 1.25 on a modest fresh paired suite, both retaining velocity. This isolates the
radius question left open by the pilot; these data do not justify a larger adaptive-rule search.

### Preserved V3 result: no established fresh-history advantage

V3 ran three 30-slot native searches jointly evolving count and radius, followed by frozen
validation and **80 fresh paired histories**. The corrected baseline and validation-selected fixed
pair coincide at count five/radius one. Their mean final error was **3.4779**, versus **3.5006** for
the overall winner. Both primary labels therefore share the same **+0.0227 [−0.2044, +0.2368]**
contrast at 97.5%. All three search winners had higher mean error than the baseline. Component
substitutions and the frozen joint-action sampler also left useful current-state dependence
unestablished. These intervals do not establish equivalence.

![Measured V3 primary effects on fresh paired histories](assets/joint_relocation_v3/primary_effects.png)

*Measured 5D outcomes, equal regime weights, 20,000 paired bootstrap resamples. The two control
labels share one execution class and are not independent evidence.*

The [complete V3 report](docs/joint_relocation_v3.md) preserves all 2,960 executions / 296 million
queries, exact sources, action distributions, recovery curves, primary uncertainty and documented
amendments. V1 found no independent advantage; V2 beat its validation-selected constant but did not
establish useful state dependence and had higher mean error than the corrected original baseline.
Their [V1](docs/comparison.md) and [V2](docs/relocation_allocation_v2.md) records remain separate
from this sprint's exploratory evidence.

## Reproducibility and study records

Saved cases, sources, databases, receipts and figures are in [the inventory](artifacts/README.md).
The [sprint report](docs/sprints/radius_velocity_20260916/REPORT.md) contains the exact run
identity, selection chronology, accounting and terminal/WebUI commands. Historical browser details
remain in [recovery](docs/recovery.md) and [native integration](docs/shinkaevolve.md).

```bash
# Existing pinned environment; inspect saved results without model/objective calls.
source .venv/bin/activate
python scripts/analyze_radius_velocity_sprint.py \
  --run artifacts/radius_velocity_sprint/20260916T113359Z --phase-a \
  --output /tmp/radius-velocity-phase-a
```

Dependencies are locked in `uv.lock`; see [setup](docs/reproduction.md). Resume retains frozen settings
and checkpoints but does not restore native proposal RNG state. Source fidelity, execution, optimizer
performance and scientific discovery are distinct.

## References

- Blackwell, T., Branke, J., & Li, X. (2008). [Particle Swarms for Dynamic Optimization Problems](https://doi.org/10.1007/978-3-540-74089-6_6). In *Swarm Intelligence: Introduction and Applications*. Springer.
- DEAP contributors. [Pinned multi-swarm source](https://github.com/DEAP/deap/blob/8a96fd3a75026f7b30e835f595a5199c75634ddf/examples/pso/multiswarm.py). Upstream licensing and notices apply.
- Sakana AI. [ShinkaEvolve](https://github.com/SakanaAI/ShinkaEvolve). Citation metadata for this project: [CITATION.cff](CITATION.cff).
