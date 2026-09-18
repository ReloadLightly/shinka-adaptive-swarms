# Evolving Adaptive Multi-Swarm Search in Changing Environments

### Interpretable population adaptation for multi-swarm PSO with ShinkaEvolve

**Can an evolved rule improve a published optimizer's ability to track changing opportunities under the same objective-evaluation budget?**

[Current results](#4-results-the-corrected-200-peak-campaign) · [Reconstruction](#2-source-and-reconstruction) · [Earlier evidence](#5-cumulative-evidence) · [Evidence and reproducibility](#7-evidence-and-reproducibility) · [Programs and data](artifacts/README.md)

## Abstract

Collective search must balance exploiting discoveries, retaining alternative trajectories, and recovering when previously useful information becomes stale. This repository reconstructs the multi-swarm particle swarm optimizer (MPSO) of Blackwell, Branke and Li (2008), then uses native ShinkaEvolve to search for small, inspectable adaptation rules. The active experiment addresses a future-work direction stated in the chapter: adapting particle numbers within subswarms. The simulator, evaluation budget, quantum response, and swarm-management mechanisms remain fixed; only a function choosing the neutral-particle target evolves.

The corrected 200-peak campaign's interim leader uses workload-adjusted fitness deterioration and previous-target history to request two or three neutral particles. On four five-dimensional development histories of 500,000 objective queries each, its mean offline error is **1.928740**, compared with **2.191283** for corrected reconstructed MPSO 5+1 and **2.080392** for the strongest tested constant target. These are development reductions of **11.98%** and **7.29%**, respectively. The rule repeatedly grows and shrinks subswarms; its behavior is not a disguised constant. Nevertheless, selection on four histories does not establish generalization, and the observed behavior does not isolate the causal value of hysteresis or any Shinka feature.

Earlier ten-peak schedule and population searches found no improvement over their reconstructed seed. Larger historical experiments include a preserved null result on 80 fresh histories. The repository therefore presents a cumulative experimental record: source-fidelity repairs, successful native program evolution, development findings, and independent evidence are kept separate. The latest published checkpoint covers **nine of 50 planned descendant slots: eight valid descendants and one operational failure, plus the seed**. Generation four remains the interim leader; the campaign is unfinished and has not reached final selection.

## 1. Introduction

A swarm optimizer can become very good at exploiting yesterday's discovery and still adapt poorly to tomorrow's environment. Concentrating search makes local improvement efficient, but can erase alternatives. Memory accelerates search, but a remembered solution can become misleading after the objective changes.

Blackwell, Branke and Li's MPSO addresses this tension through small cooperative subswarms. Ordinary, or **neutral**, particles update their motion using personal and shared best positions. **Quantum** particles instead sample around a swarm's shared best; here “quantum” names a probability distribution, not quantum hardware. Exclusion and swarm birth/removal distribute effort among promising regions. After a detected change, a short exploratory response helps reacquire useful locations.

This project asks whether **native program evolution can improve one part of that existing design**, rather than inventing an optimizer without a reference. After unsuccessful searches over the temporary response schedule, the active experiment changes the number of neutral particles maintained within each subswarm. The authors identify this direction explicitly on printed p.215.

There are two different adaptation processes. During an optimizer run, particles move and subswarms change. Between runs, ShinkaEvolve mutates the Python rule that controls population adaptation and evaluates each candidate on complete benchmark histories. **Shinka's islands contain candidate programs; MPSO's subswarms contain particles.** They are not the same population.

![Illustrative two-dimensional swarm redistribution](assets/illustration/swarm_dynamics.gif)

*Illustration, not a research comparison. This separate two-dimensional visualization uses saved positions and landscape snapshots. The experiments reported below use five dimensions; hidden landscape information is not supplied to the evolved rule.*

## 2. Source and reconstruction

### 2.1 The published reference

The source is [*Particle Swarms for Dynamic Optimization Problems*](https://doi.org/10.1007/978-3-540-74089-6_6), by Tim Blackwell, Jürgen Branke and Xiaodong Li, in Christian Blum and Daniel Merkle's edited volume *Swarm Intelligence: Introduction and Applications* (2008), pp.193–217.

The chapter studies MPSO and speciation-based PSO (SPSO), different sampling distributions, particle configurations, and four combinations of peak count and movement severity. This repository reconstructs and extends selected **MPSO** conditions. It does not reproduce the entire chapter or compare against SPSO.

| Historical Table 3 reference, `nexcess=1` | Published offline error | Published standard error | Original protocol |
|---|---:|---:|---|
| MPSO 5+0 | 1.80 | 0.08 | 50 runs × 500,000 evaluations |
| MPSO 5+1 | 1.73 | 0.08 | 50 runs × 500,000 evaluations |

*Printed historical values, not repository measurements or calibration targets. The chapter includes other settings; 5+1 / `nexcess=1` is not presented here as its best overall setting. In Table 6 on p.214, the 200-peak/severity-one MPSO value is 2.18, while adjacent prose says 2.12. That source discrepancy is retained rather than silently reconciled.*

### 2.2 What “chapter-aligned” means here

The reference has five designated neutral particles and one additional permanent quantum particle per newborn subswarm. All current neutrals use quantum movement for one update after a counted change detection, then resume ordinary PSO. The permanent quantum particle samples throughout. Sampling is uniform by volume in a ball with radius `0.5 × movement severity`; in five dimensions the radial factor is `U**(1/5)`.

Every objective call counts: initialization, detection, memory refresh, movement, swarm birth and exclusion. Detection comes from reevaluating the shared best, not from an oracle change flag. On detection, every existing personal-best memory is reevaluated, including the permanent quantum particle's memory. Quantum sampling replaces an ordinary movement for that update; neutral velocities remain available for later ordinary updates. Attractors update asynchronously, and exclusion occurs after each subswarm update, following the ordering of Algorithm 3.

The [original source record](docs/book_mpso_source_record.md) distinguishes chapter mechanisms from implementation conventions. These include pinned DEAP Moving Peaks, initial heights of 50, sampled initial widths and positions, initial velocities, unclipped particle positions, asynchronous ordering, and exact stopping at 500,000 queries even within an operation. Independent environment and optimizer random streams make paired landscapes comparable without promising identical later particle trajectories.

**The current geometry is corrected; historical scores are not rewritten.** The earlier chapter-schedule and ten-peak population engines approximated convergence with maximum pairwise neutral distance. That is not the chapter's smallest-enclosing-ball criterion. The active [versioned engine](src/adaptive_swarms/book_population_v2.py) uses [neutral-only enclosing-ball convergence](src/adaptive_swarms/enclosing_ball.py), with deterministic certificates and an ambiguous-case solver. Geometry consumes no objective queries or random draws. Corrected controls were measured anew, and historical trajectories are not reused as corrected measurements. See the [versioned source record](docs/book_mpso_population_200_v2_source_record.md).

These repairs improve reconstruction fidelity; **they are not evolutionary discoveries**. The evidence supports a documented chapter-aligned reconstruction and matched contemporary comparisons, not exact numerical replication of the historical tables.

| Peaks | Movement severity | Chapter-aligned evidence |
|---:|---:|---|
| 10 | 1 | Completed schedule and population searches; eight development cases each |
| 200 | 1 | Historical one-case runtime stop; corrected enclosing-ball continuation now has paired controls and an interim native campaign on four development histories |
| 10 | 5 | Still untested by the chapter-aligned search |
| 200 | 5 | Still untested by the chapter-aligned search |

*The ten-peak and corrected 200-peak studies differ in convergence geometry as well as peak count. Their contrast does not isolate the effect of peak count.*

## 3. Method and active experimental design

### 3.1 One small program inside a fixed optimizer

The active task is [`book_mpso_population_200_v2`](tasks/book_mpso_population_200_v2). Shinka evolves only:

```python
def choose_neutral_count(observation) -> int:
    return 5
```

The returned integer target is between two and eight. Every new or replacement subswarm starts with five neutrals plus one permanent quantum particle. After counted detection and memory refresh, the adapter moves the neutral count **at most one step** toward the requested target. Shrinking removes the worst refreshed neutral personal-best memory, with a fixed tie rule. Growing inserts one neutral before the permanent particle; its ensuing quantum-response move provides its first evaluated position. Survivor state and order persist.

This is **within-subswarm population adaptation**, not transfers between groups or conservation of a global particle total. Radius, ordinary PSO, memory handling, the permanent quantum role, exclusion and swarm birth/removal stay fixed. Target five reproduces the corrected 5+1 reference without population mutation.

```mermaid
flowchart TD
    C[Counted shared-best check] --> D{Change detected?}
    D -->|Yes| R[Refresh all existing personal memories]
    R --> T[Evolved rule requests target 2 through 8]
    T --> A[Add or remove at most one neutral]
    A --> Q[All current neutrals use quantum response]
    D -->|No| N[Current neutrals use ordinary PSO]
    Q --> P[Permanent quantum particle samples]
    N --> P
    P --> E[Exclusion after this subswarm update]
```

*Mechanism schematic, not measured data. The benchmark changes exogenously over the run; its generator and protocol are fixed across compared methods.*

The immutable observation is captured after refresh and before resizing. It includes local deterioration, spread and speed, previous requested target, and global particle/swarm counts. It excludes hidden peak coordinates, the hidden peak count, optimum, benchmark error, seeds, future changes and protected outcomes. The known sampling radius remains available. The [task prompt](tasks/book_mpso_population_200_v2/task_prompt.txt) defines timing, normalization and permitted operations. There is no reward for source complexity or conditional branches.

### 3.2 Native evolution and feedback

The pinned ShinkaEvolve revision is `9912af12d423504b8d580f4179fd15f5f88b8c50`. The active campaign uses one island, weighted parent sampling, archive/top inspirations, diff/full/crossover mutation, local code embeddings with native LLM novelty judging, and interval-five meta-memory. The mutation model is fixed; prompt coevolution is off and migration is inactive. These are declared design choices, not a claim that every optional feature is enabled.

Session 1 records three diff, two full and one crossover mutation, seven local embeddings and six accepted novelty decisions. Complete parent/inspiration sources and measured feedback were checked in saved prompts. Generation four was produced from generation two with generations one/three as inspirations. Its gain **preceded** the interval-five meta update. A later recommendation appears in generation six's prompt; the native crossover format used for generation five omits that recommendation section.

The numerical evaluator reports whole-history errors, paired differences against fixed targets three/five, actual population behavior, query shares and favorable/unfavorable recovery episodes. Its maximized fitness is `1 / (1 + mean_offline_error)`, a monotonic transformation of the minimized error. Candidate evaluation uses the simulator, not an LLM's opinion about optimizer quality. Native execution, useful optimizer behavior and the causal contribution of an individual Shinka feature remain separate claims.

### 3.3 Registered protocol

| Quantity | Corrected 200-peak campaign |
|---|---|
| Benchmark | Pinned DEAP Moving Peaks, 200 conical peaks, five dimensions |
| Peak domain | `[0,100]^5`; particle positions are not clipped to this domain |
| Changes | Movement severity 1, every 5,000 counted queries, correlation zero |
| Height / width settings | Ranges `[30,70]` / `[1,12]`; change severities 7 / 1 |
| Per-history budget | Exactly 500,000 objective queries, including overhead categories |
| Development data | Four reused, fixed history identities; new corrected trajectories |
| Native search | 50 planned descendant slots plus seed; latest published checkpoint: 9 terminal slots, 8 valid descendants and 1 operational failure |
| Constant controls | Every integer target 2–8, with the same start-at-five, step-one adapter |
| Selection | Complete valid development mean, including seed; ties by earlier generation then source hash |
| Fresh stage | After final freeze, 50 new paired histories if a distinct selected native program improves on seed |
| Fresh comparators | Corrected 5+1 and the development-selected constant target |
| Analysis | Primary comparison against 5+1, then prespecified secondary; whole-history paired bootstrap |

Offline error averages the gap between the current optimum and the best value discovered since the latest environmental change over every counted query. The optimum is available to measurement, not to the evolved decision rule. A boundary query belongs to the environment it evaluated.

The [prospective protocol](docs/book_mpso_population_200_v2_protocol.md) and [analysis specification](docs/studies/book_mpso_population_200_v2/analysis_specification.json) were frozen before mutation. Fresh outcomes cannot enter mutation, novelty, meta-memory or selection. Periods and particles within a history are not independent replications. Interim intervals below summarize selected development data; they are not the registered final test.

## 4. Results: the corrected 200-peak campaign

### 4.1 A conditional development leader, not yet a confirmed winner

Generation four remains the interim leader through nine completed descendant slots. Its exact executed behavior is preserved in the [native source](artifacts/book_mpso_population_200_v2/20260917T065325Z/session_001/evolution/search_seed_670001/gen_4/main.py):

```python
def choose_neutral_count(observation) -> int:
    """Choose two or three neutrals using workload-adjusted loss hysteresis."""
    # Estimate movement and detection queries per optimizer sweep.
    loss = max(0.0, observation["relative_fitness_drop"])
    swarms = max(1, observation["swarm_count"])
    sweep_queries = max(
        1.0, observation["total_particle_count"] + swarms
    )
    # Greater existing workload raises the evidence required for growth.
    recovery_pressure = loss / (1.0 + sweep_queries / 160.0)
    # History is supplied by the caller; no state is retained here.
    threshold = (
        0.04 if observation["previous_requested_target"] == 3 else 0.08
    )
    return 3 if recovery_pressure > threshold else 2
```

It defaults to a smaller group, requests an additional neutral when deterioration is sufficiently large relative to estimated workload, and uses a lower threshold to retain target three than to enter it. The workload term is a proxy, not an exact account of all queries in a sweep. This interpretation describes the executed function, not an established causal explanation of its performance.

| Method | Mean development error | Difference from corrected 5+1 | Paired wins/losses |
|---|---:|---:|---:|
| Corrected 5+1 / target five | 2.191283 | 0 | — |
| Constant target three | 2.091593 | −0.099690 | 3 / 1 |
| Native constant target two | 2.080392 | −0.110892 | 3 / 1 |
| **Generation four: conditional targets two/three** | **1.928740** | **−0.262543** | **3 / 1** |

The leading rule lowers development mean error by **11.98% against corrected 5+1** and **7.29% against target two**, the strongest of all seven tested constants. The intermediate comparison against target three is 7.79%. All constants use the same adapter; these results do not compare every possible fixed-size initialization or every population policy.

| Constant target | Case 000 | Case 001 | Case 002 | Case 003 | Mean |
|---:|---:|---:|---:|---:|---:|
| 2 | 2.290227 | 2.050520 | 1.723802 | 2.257017 | 2.080392 |
| 3 | 2.256459 | 2.208741 | 1.768793 | 2.132379 | 2.091593 |
| 4 | 2.349921 | 2.235428 | 1.792776 | 2.347646 | 2.181443 |
| 5 | 2.748324 | 1.921516 | 1.807639 | 2.287654 | 2.191283 |
| 6 | 2.763961 | 2.193985 | 1.958697 | 2.483343 | 2.349997 |
| 7 | 2.628220 | 2.322572 | 2.031650 | 2.427255 | 2.352424 |
| 8 | 3.157858 | 2.345415 | 2.356839 | 2.487131 | 2.586811 |

Against corrected 5+1, the four paired differences are −0.594850, +0.017667, −0.157189 and −0.315800; the descriptive 95% interval is [−0.485435, −0.065700]. Case 000 contributes 56.64% of the net gain, although all leave-one-history-out means remain negative. Against target two, all four histories improve, with mean difference −0.151651 and descriptive interval [−0.241707, −0.089203]. **These selection-biased, four-history summaries do not establish fresh generalization.**

### 4.2 Evolution through the latest published checkpoint

The latest published PSO results are the **18 September 2026, 09:17 UTC checkpoint through generation nine**. A generation number identifies a proposal slot; it does not imply a single chain of nine successive improvements. The original seed is generation zero and is counted separately.

| Generation | Executed rule or outcome | Mean offline error ↓ | Difference from corrected 5+1 |
|---:|---|---:|---:|
| 0 | Seed: constant target five | 2.191283 | 0 |
| 1 | Constant target three | 2.091593 | −0.099690 |
| 2 | Constant target two | 2.080392 | −0.110892 |
| 3 | Constant target four | 2.181443 | −0.009840 |
| **4** | **Workload-adjusted loss hysteresis; targets two/three** | **1.928740** | **−0.262543** |
| 5 | Cap detected loss by deterioration remaining after memory refresh | 1.989777 | −0.201506 |
| 6 | Cap the workload proxy at 120 before normalizing loss | 2.057724 | −0.133559 |
| 7 | Operational failure: numerical runtime mismatch | — | — |
| 8 | Remove workload cap; allow target four under high recovery pressure | 2.023027 | −0.168256 |
| 9 | Remove target four; raise target-three retention threshold to 0.05 | 1.995239 | −0.196044 |

Generation eight descends from generation six; generation nine descends from eight. Their errors improve on their respective parents by 0.034697 and 0.027787, but both remain above generation four. Generation eight actually requests target four 354 times across the four cases. These whole-policy comparisons do not separately identify the effects of the simultaneous edits.

Generation seven has **no comparable scientific score**: its first case was executed under an incorrectly restored numerical runtime and failed exact landscape pairing. Generation nine was fully evaluated after a documented replay of its interrupted fourth case. Its original accepted source and three completed cases were preserved. Neither infrastructure repair counts as an evolutionary improvement.

The [Session 1 report](docs/studies/book_mpso_population_200_v2/REPORT.md), [Session 2 checkpoint report](docs/studies/book_mpso_population_200_v2/SESSION_002.md), and [saved lineage and scores](docs/studies/book_mpso_population_200_v2/session_002_figures/native_evolution.json) retain the detailed evidence. They establish the published checkpoint, not the current state of a process on another machine. There is no final winner freeze or fresh comparison for this campaign.

![Observed native evolution through generation nine](docs/studies/book_mpso_population_200_v2/session_002_figures/native_evolution.png)

*Means from four reused 5D development histories, 500,000 counted queries per case. Lines connect actual parents and descendants; generation 7 has no score. [Sources, checkpoints and recovery evidence](docs/studies/book_mpso_population_200_v2/SESSION_002.md#measured-evolution-after-wsl-returned) accompany the plot. No fresh confirmation has occurred.*

### 4.3 What the rule actually changes

The rule requests two in 63.27% and three in 36.73% of detected-change decisions, averaging histories equally. It produces 1,582 additions, 2,503 removals and 2,921 reversals of resizing direction across the four histories. Births still begin at five, so transient counts of four/five remain. Unlike a constant target, the rule repeatedly requests both growth and shrinkage.

Mean total particles fall from 215.48 under corrected 5+1 to 93.26; mean subswarm count falls from 35.91 to 26.41. Both methods still spend **500,000 objective queries per history**. Fewer particles therefore do not mean 57% fewer objective evaluations or a demonstrated equivalent reduction in wall time. Population, detection frequency, memory work, exclusion and birth trajectories change together. Subswarm count is not a measurement of distinct-peak coverage.

![Corrected 200-peak population and tracking](assets/book_mpso_population_200_v2/session_001/population_and_tracking.png)

*Measured five-dimensional development evidence: four paired full-horizon histories. Solid population curves count particles; dashed curves count subswarms on the labeled right axis. Neutral bands describe population spread, not confidence intervals. Paired intervals are descriptive and selection-biased.*

![Favorable and unfavorable corrected 200-peak episodes](assets/book_mpso_population_200_v2/session_001/tracking_episodes.png)

*Both sides of the result. The registered largest-contribution rule selects a favorable episode, case 000/period 6, and an unfavorable episode, case 001/period 2. Their mean-error differences from 5+1 are −7.506815 and +10.931851. These extrema are not typical-effect estimates or independent replications; no illustrative replay was added.*

### 4.4 Evaluation and execution accounting

| Published boundary | Completed numerical work | Interpretation |
|---|---|---|
| Session 1, generations 0–6 and all constant controls | 44 physical cases × 500,000 queries = 22 million research queries; 12 additional cached case records | Six valid descendants plus seed; a clean, published session boundary |
| Cumulative through Session 2, generation nine | 53 completed physical cases = 26.5 million known completed queries; one interrupted attempt additionally reserved at 500,000 | 54 full-budget attempts charged conservatively at 27 million queries; an interim checkpoint |

The cumulative count includes generation seven's completed but incomparable runtime-failure case and generation nine's replay. The interrupted attempt's observed lower bound is 140,000 queries; its exact total is unknown, so the full reservation is retained. Cached case records add no objective queries. Session 1 also records 401 separately counted fixture queries.

Session 1 used 19 logical native responses: six mutation, six novelty and seven meta responses. This is a **Session 1 count**, not the cumulative model-call total through generation nine. Sources, attempted programs, failures, receipts and case-level checkpoints remain preserved. See the [Session 1 publication receipt](artifacts/book_mpso_population_200_v2_publication/session_001/PUBLICATION.json) and [generation-nine manifest](artifacts/book_mpso_population_200_v2_publication/session_002_generation_009/MANIFEST.json).

## 5. Cumulative evidence

The studies below remain part of the result, not discarded attempts. Their engines, histories and interventions differ. **They are not a shared leaderboard**, and development intervals must not be read as independent confirmation.

### 5.1 Ten-peak population adaptation: the seed remained selected

On eight reused ten-peak development histories, six valid native descendants failed to improve the reconstructed 5+1 seed. The closest descendant was simply `return 6`; the selected program remained `return 5`. Its fresh-comparison trigger was not met. These historical experiments used the documented diameter approximation, not the current enclosing-ball engine.

| Method, all starting at five neutrals | Mean error ↓ | Method − target five | Descriptive 95% interval | Wins / losses |
|---|---:|---:|---|---:|
| Fixed target three | 1.806340 | +0.061772 | [−0.092645,+0.257007] | 4 / 4 |
| **Target five / selected seed** | **1.744569** | Execution reference | — | — |
| Fixed target seven | 1.871657 | +0.127089 | [−0.058890,+0.296543] | 2 / 6 |
| Best native descendant: constant target six | 1.776112 | +0.031543 | [−0.185736,+0.250921] | 3 / 5 |

[Completed population report](docs/studies/book_mpso_population_v1/REPORT.md).

<details>
<summary><strong>Ten-peak protocol, allocation table and measured figures</strong></summary>

These are the original study's settings, not the active 200-peak campaign protocol.

| Quantity | Chapter-aligned comparison |
|---|---|
| Landscape | Pinned DEAP Moving Peaks; ten conical peaks |
| Domain and dimensions | Peak positions in `[0,100]^5`; five dimensions |
| Changes | Severity 1, every 5,000 counted queries, movement correlation zero |
| Heights and widths | Heights `[30,70]`, widths `[1,12]`; change severities 7 and 1 |
| Initialization convention | Initial heights 50; widths and positions sampled as in pinned DEAP |
| Swarm allocation | Start five neutrals + one permanent quantum per subswarm; neutral target 2–8, step at most one on detected change; `nexcess=1` |
| Per-case horizon | Exactly 500,000 objective queries, matching the chapter's horizon |
| Development | Reuse all eight prior chapter-schedule seed pairs; explicitly development data |
| Native search | Exact target-five seed plus at most six descendant slots; one island |
| Independent comparison | Eight fresh pairs only if a distinct native winner beats target five and the best tested fixed target |
| Selection / fitness | Lowest mean error; `combined_score = 1 / (1 + mean_offline_error)` |
| Descriptive uncertainty | 20,000 independent paired-case bootstrap resamples, seed 2026091609, 95% intervals |

| Measured allocation | Target three | Target five | Target seven | Native target six |
|---|---:|---:|---:|---:|
| Mean total particles at saved query grid | 37.48 | 51.63 | 64.91 | 59.66 |
| Mean subswarms | 8.800 | 8.605 | 8.393 | 8.672 |
| Ordinary movement share | 58.58% | 67.51% | 72.81% | 70.49% |
| Permanent quantum share | 18.05% | 13.67% | 11.03% | 12.19% |
| Detection share | 18.05% | 13.67% | 11.03% | 12.19% |
| Memory-refresh share | 0.72% | 0.99% | 1.25% | 1.15% |

![Measured MPSO populations and tracking](assets/book_mpso_population_v1/population_and_tracking.png)

*Measured 5D development trajectories over counted queries, retaining all eight paired effects. Population bands show mean within-case minima/maxima, not uncertainty. Target six is the closest descendant, not the selected method.*

![Measured target requests, realized sizes and recovery](assets/book_mpso_population_v1/population_behavior.png)

*Requested targets, realized populations and measured recovery. Even a constant target produces transient size heterogeneity because new swarms start at five; that is not learned conditionality.*

![Measured native population search and behavior](assets/book_mpso_population_v1/native_search.png)

*Every native program uses all eight development histories. Conditional shrink/grow rules were behaviorally active but did not lower mean error. Only this ten-peak batch left the available workload and previous-target fields unused.*

The study completed 64 new full executions / 32 million queries, with 16 cache uses of eight existing target-five cases. These reused histories are not independent new replications.

</details>

### 5.2 Ten-peak temporary conversion: no improved schedule

Eight evaluated descendants failed to improve the original 5+1 seed's mean development error. The selected schedule remained `5 if observation["change_detected"] else 0`: all five neutrals sample on detection, none temporarily sample otherwise; the permanent quantum particle remains active throughout.

| Matched development method | Mean offline error ↓ | Median case error | Status |
|---|---:|---:|---|
| Reconstructed MPSO 5+0 | 1.743485 | 1.786711 | External reference |
| Reconstructed MPSO 5+1 | 1.744569 | 1.794818 | Native seed and selected program |

The paired 5+1-minus-5+0 mean is +0.001084, with descriptive interval [−0.306345,+0.285559] and four wins/four losses. This neither establishes equivalence nor convincingly recovers the printed historical ranking. [Completed schedule report](docs/studies/book_mpso_schedule_v1/REPORT.md).

<details>
<summary><strong>Schedule mechanisms, all descendant results and measured figures</strong></summary>

| Mechanism | Reconstructed MPSO 5+0 | Reconstructed MPSO 5+1 / preceding schedule study |
|---|---|---|
| Designated neutral particles | Five | Five |
| Permanent quantum particles | None | One additional particle |
| Published temporary conversion | All five for the detected-change update | All five for the detected-change update |
| Published behavior between detected changes | Ordinary neutral PSO | Ordinary neutral PSO plus permanent quantum sampling |
| Evolvable decision | External fixed reference | Temporary quantum count, 0 through 5, each subswarm update |

| Native descendant | Executed temporary-conversion rule | Mean error ↓ | Difference from 5+1 |
|---|---|---:|---:|
| 1 | 5 on detection; 2 for the next three updates | 1.902573 | +0.158004 |
| 2 | 5 on detection; 2 on the next update only after no improvement | 1.813739 | +0.069170 |
| 3 | 3 on detection; 0 otherwise | 1.919122 | +0.174553 |
| 4 | 3 on detection; 1 for the next two updates | 1.970515 | +0.225946 |
| 5 | 5 on detection; 1 for the next two updates | 2.040693 | +0.296124 |
| 6 | 4 for absolute relative observed change ≤1%, otherwise 5; detection only | 2.092992 | +0.348423 |
| 7 | 4 on detection; 0 otherwise | 2.126656 | +0.382088 |
| 8 | Same decisions as generation 6; reordered guard | 2.092992 | +0.348423 |

![Measured chapter comparison and native schedule behavior](assets/book_mpso_schedule_v1/schedule_and_performance.png)

*Measured 5D development results on eight paired 500,000-query histories. All programs and unfavorable histories remain visible; recovery averages histories, not independent particle updates.*

![Measured ordinary and quantum contributions](assets/book_mpso_schedule_v1/schedule_contributions.png)

*Observed shared-best improvements by update type. Attribution on a reached trajectory is not an isolated causal value for a particle type.*

![Measured native chapter-schedule search](assets/book_mpso_schedule_v1/native_search.png)

*One seed and eight valid descendants, but only seven distinct descendant behaviors. Generation eight repeated generation six; the island-local novelty pool missed the cross-island equivalence. The repeated executions remain counted.*

The study used 80 new full executions / 40 million queries, including eight repeated executions, plus eight cached seed records. The seed remained selected and no fresh comparison was triggered.

</details>

### 5.3 Historical recovery studies: positive contrasts and preserved nulls

| Study | Comparison and independent evidence | Finding |
|---|---|---|
| V1: broad recovery program | Selected − corrected baseline; 8 fresh paired histories | +0.0627, descriptive 95% interval [−0.1470,+0.2724]; no established advantage |
| V2: exact count at radius multiplier 2 | Selected − validation-selected count two; 40 fresh histories | −0.4265 [−0.6903,−0.1829]; improved that comparator, not a demonstrated conditional mechanism |
| V3: joint count and radius | Overall winner − baseline/selected fixed pair; 80 fresh histories | +0.0227, predeclared 97.5% interval [−0.2044,+0.2368]; both control labels coincide |
| Radius/velocity sprint | Constant count 4 / radius multiplier 1.25 − original baseline; 8 fresh pilot histories | −0.6303, descriptive 95% interval [−1.4721,+0.2241]; inconclusive and influenced by a large retained benefit |

V2's favorable comparison against its selected constant did **not** mean it improved the original corrected baseline on average. V3 ran three 30-slot searches; its overall selected rule scored 3.5006 against a 3.4779 baseline on 80 fresh histories. The fixed comparator and baseline coincided, so they were not two independent corroborations. The current development signal does not turn those earlier results into successes.

[Full V1 analysis](docs/comparison.md) · [V2 analysis](docs/relocation_allocation_v2.md) · [V3 analysis](docs/joint_relocation_v3.md) · [Radius/velocity report](docs/sprints/radius_velocity_20260916/REPORT.md)

<details>
<summary><strong>Historical final-comparison and radius–velocity figures</strong></summary>

![Measured V3 primary paired contrasts](assets/joint_relocation_v3/primary_effects.png)

*Measured 5D final comparison on 80 fresh histories. Intervals use the registered within-regime, paired-history analysis. All unfavorable cases remain. Both primary control labels share one execution class.*

![Measured radius–velocity interaction and recovery](assets/radius_velocity_sprint/phase_a_interaction_recovery.png)

*Measured 5D development diagnostic. The small average interaction concealed opposing regime effects; no overshoot mediator was measured. The later eight-history radius-multiplier-1.25 pilot remained inconclusive.*

</details>

### 5.4 Particle retention: an inspectable, development-only candidate

A separate search evolved a score that favors proximity to the refreshed swarm best with a reduced penalty on retained speed. The highest-scoring particle keeps ordinary PSO motion; the other four relocate. The selected score is `1 / (1 + distance + 0.5 * speed)`, with both features normalized by the known default radius.

| Method | Mean offline error ↓ | Selected − method | Descriptive 95% interval | Selected wins/losses |
|---|---:|---:|---:|---:|
| Random retention | 3.722188 | −0.154688 | [−0.305334, −0.006405] | 4 / 4 |
| Strongest refreshed-pbest heuristic | 3.901685 | −0.334185 | [−0.525500, −0.142869] | 6 / 2 |
| Selected generation 7 | **3.567500** | — | — | — |

These are selected development results. Against random retention, all four slower-change histories improved and all four faster-change histories worsened; one history contributed about 80% of the net benefit. Independent confirmation of this score remains absent. [Full retention report](docs/sprints/particle_retention_20260916/REPORT.md).

<details>
<summary><strong>Retention search, paired outcomes and observed behavior</strong></summary>

![Measured native particle-retention search](assets/particle_retention_v1/native/search_progress.png)

*Eight valid numerical programs. A separate terminal slot failed static checking before numerical execution; the proposed idea was not evaluated. Its source and lineage remain preserved.*

![Measured particle-retention effects and recovery](assets/particle_retention_v1/paired_effects_recovery.png)

*All eight paired development effects and regime-specific recovery summaries. The longer-period advantage is a development observation, not a confirmed regime law.*

![Measured retained-particle characteristics](assets/particle_retention_v1/retention_behavior.png)

*Measured choices and state characteristics, summarized at case level. Agreement with another rule on the same reached state does not isolate a causal effect.*

[Saved favorable and unfavorable recovery episodes](assets/particle_retention_v1/recovery_episode_extremes.png) remain available. The original report also preserves the prospective examples, failed-slot accounting and admission limitation.

</details>

### 5.5 Reconstruction and runtime history

The original three-history reconstruction and the first, stopped 200-peak attempt remain historical evidence, not corrected controls. The first 200-peak attempt completed one target-five history, then stopped at runtime assessment before native search. Its score is not evidence for or against population adaptation.

<details>
<summary><strong>Original reconstruction and stopped 200-peak reference figures</strong></summary>

![Measured five-dimensional historical baseline tracking and swarm population](assets/reconstruction/baseline_tracking.png)

*Three historical 500,000-query histories, mean error 1.7024, sample SD 0.7896. Different seeds and the older engine prevent treating this as numerical replication of the printed table or as a current evolved-versus-reference comparison.*

![Measured single 200-peak reference trajectory](assets/book_mpso_population_200_v1/population_and_tracking.png)

*One historical diameter-engine case, error 2.586443, with no native seed or descendant execution. The corrected campaign measured its controls anew rather than reusing this trajectory. [Runtime-stop report](docs/studies/book_mpso_population_200_v1/REPORT.md).*

</details>

## 6. Discussion and limitations

**The current contribution is a testable candidate mechanism.** The leading rule combines local loss, global workload and supplied history, changes actual population repeatedly, and lowers development error beyond every constant target admitted by the interface. This is more specific than a functioning pipeline or a source-level conditional that almost never executes. It is still not fresh confirmation.

**The discovery data are small.** The planned 50-slot campaign repeatedly consults four histories; only nine descendant slots are documented at the latest published checkpoint. Selection bias remains even when a development bootstrap interval excludes zero. The registered later 50-history comparison is therefore central, not optional decoration. Future independent searches would be needed to characterize the reliability of the discovery process itself.

**Lower error does not identify its cause.** Population adaptation alters movement, detection, memory, convergence and exclusion together. Fixed targets help challenge simple size tuning but do not isolate hysteresis, the workload normalization, or the value of matching decisions to current state. Those require separately specified interventions after the present campaign, not changes to its frozen evaluator.

**Source fidelity is versioned and partial.** The corrected enclosing-ball path repairs a documented discrepancy. Other conventions remain declared; the published 50-run numerical protocol, all configurations and SPSO have not been reproduced. Results under the old geometry remain informative about that implementation, not interchangeable with corrected-engine results.

**Native provenance is not comparative discovery efficiency.** Saved sources, prompts, lineage and receipts establish that Shinka produced the candidates. They do not establish that Shinka beats independent generation, random program search, or another search system under matched discovery budgets. Nor can the generation-four improvement be credited to meta-memory that updated afterward.

**The benchmark is synthetic and known-scale.** Peak movements are exogenous; the sampling radius uses the configured severity. Success on this benchmark does not by itself establish robustness to unknown severity, new objective families, severe shifts, or real-world decision consequences.

### 6.1 Collective adaptation and the social-science motivation

The substantive motivation is collective adaptation: maintaining useful alternatives, responding to stale information, and allocating limited search effort across changing opportunities. This makes MPSO a controlled laboratory for studying a mechanism that may also matter in other collective systems.

It is **not a geopolitical simulator or a demonstrated model of institutional emergence**. Particles are candidate solutions, not states. Subswarm separation is not political rivalry. Every candidate is evaluated against a shared benchmark objective; the active rule also receives global counts, and the fixed optimizer manages births and exclusions. There are no actor-specific interests, bargaining, endogenous institutions, or strategic actions that reshape another actor's landscape.

A future social-science application would have to specify the actors, observations, incentives and interaction mechanisms independently, then test that mapping against evidence. The present experiment can inform questions about adaptation and collective search; it cannot establish conclusions about particular countries, regional arrangements or policies. Preserving that boundary lets the algorithmic result stand on its own merits.

The [cross-substrate research note](docs/emergence_across_substrates.md) compares information sharing, coordination within groups, differentiation between groups, memory and feedback with primary research on international cooperation. It separates these analogies from shared causal mechanisms and proposes falsifiable tests. Current MPSO implements cooperation; voluntary sharing, defection, conflicting actor interests and institution formation are absent.

## 7. Evidence and reproducibility

### 7.1 Programs, measurements and protocols

| Research object | Repository evidence |
|---|---|
| Interim leading executable | [Generation-four Python source](artifacts/book_mpso_population_200_v2/20260917T065325Z/session_001/evolution/search_seed_670001/gen_4/main.py) |
| Original development measurements, controls and behavior analysis | [Session 1 report](docs/studies/book_mpso_population_200_v2/REPORT.md) · [Immutable Session 1 artifacts](artifacts/book_mpso_population_200_v2/20260917T065325Z/session_001/) |
| Latest completed-generation publication | [Generation-nine source, cases, database and recovery manifest](artifacts/book_mpso_population_200_v2_publication/session_002_generation_009/) |
| Evolutionary continuation and failures | [Session 2 report](docs/studies/book_mpso_population_200_v2/SESSION_002.md) · [Lineage and numerical figure data](docs/studies/book_mpso_population_200_v2/session_002_figures/native_evolution.json) |
| Frozen design and prospective analysis | [Protocol](docs/book_mpso_population_200_v2_protocol.md) · [Analysis specification](docs/studies/book_mpso_population_200_v2/analysis_specification.json) |
| Source fidelity and implementation | [Reconstruction record](docs/reproduction.md) · [Original chapter mapping](docs/book_mpso_source_record.md) · [Corrected convergence record](docs/book_mpso_population_200_v2_source_record.md) |
| Complete cumulative record | [Artifact inventory](artifacts/README.md) · [17 September README snapshot](README.history-2026-09-17.md) |

The evidence above belongs to the multi-swarm PSO study. The 35-generation cooperative-network study copied under `docs/studies/cooperative_network_generation35/` is a separate experiment and supplies **none of this README's results**.

The historical narrative and individual study reports retain their original context. Scientific sources, completed experiments and frozen protocols are unchanged by this README correction.

### 7.2 Inspect the saved native database

With the repository's native Shinka dependencies installed, open the published generation-nine database without running candidates or making model calls:

```bash
bash scripts/webui.sh \
  artifacts/book_mpso_population_200_v2_publication/session_002_generation_009 \
  8899
```

Open `http://localhost:8899/viz_tree.html?db_path=programs.sqlite` on the machine running the viewer. Use a free port. The database preserves program sources, parent relationships, evaluation records and the failed generation-seven row. The [native integration documentation](docs/shinkaevolve.md) describes setup; its original V1 research-launch defaults are historical.

### 7.3 Continuing the registered campaign

The published record ends at generation nine. It does not establish whether a local controller is currently running, and this README update launches no research. The [campaign-specific resume procedure](docs/studies/book_mpso_population_200_v2/RESUME.md) and [Session 2 recovery record](docs/studies/book_mpso_population_200_v2/SESSION_002.md) explain continuation from retained state. A completed-generation snapshot is not a drained final-session archive; restoration must reconcile the latest available campaign state before further proposals.

The optimizer runtime recorded for the latest campaign is Python **3.13.5**, NumPy **2.5.3**, and ShinkaEvolve **0.0.7** at revision `9912af12d423504b8d580f4179fd15f5f88b8c50`. Session 2 demonstrated why runtime identity matters: a different restored runtime changed landscape hashes despite initially matching seeds. Restoring the recorded versions reproduced all 404 saved initial/change snapshots in an environment-only diagnostic. Dependency versions and independent random streams both matter for exact pairing.

The saved model receipts identify subscription-backed inner **`gpt-6-astra/xhigh`**, with no paid API fallback. Supervising model effort is separate. Native cost displays are estimates, and logical-response counts exclude supervising usage and unexposed provider retries. Local embeddings, mutation, novelty and meta-memory have distinct roles; the numerical simulator measures optimizer performance.

After all 50 registered descendant slots and the constant controls, final selection includes the seed. A distinct selected native program improving on the seed permits a later frozen comparison on **50 new paired histories**, against corrected 5+1 and the development-selected constant. Sources and analysis must be frozen before fresh outcomes; those outcomes cannot return to selection or mutation. Until that comparison exists, the current improvement remains a development finding.

## References

- Blackwell, T., Branke, J., & Li, X. (2008). [Particle Swarms for Dynamic Optimization Problems](https://doi.org/10.1007/978-3-540-74089-6_6). In C. Blum & D. Merkle (Eds.), *Swarm Intelligence: Introduction and Applications*, pp.193–217. Springer. [Author-hosted chapter](https://titan.csit.rmit.edu.au/~e46507/publications/si-chaper-dynamic-blackwell-li.pdf).
- Blackwell, T., & Branke, J. (2006). [Multiswarms, exclusion, and anti-convergence in dynamic environments](https://doi.org/10.1109/TEVC.2005.857074). *IEEE Transactions on Evolutionary Computation*, 10(4), 459–472.
- DEAP contributors. [Pinned multi-swarm example](https://github.com/DEAP/deap/blob/8a96fd3a75026f7b30e835f595a5199c75634ddf/examples/pso/multiswarm.py) and [Moving Peaks source](https://github.com/DEAP/deap/blob/8a96fd3a75026f7b30e835f595a5199c75634ddf/deap/benchmarks/movingpeaks.py). Original licensing and notices apply.
- Sakana AI. [ShinkaEvolve](https://github.com/SakanaAI/ShinkaEvolve), pinned revision `9912af12d423504b8d580f4179fd15f5f88b8c50`. Project citation metadata: [CITATION.cff](CITATION.cff).
