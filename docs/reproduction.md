# Source fidelity and experimental interpretation

This project reconstructs a specific published swarm algorithm and evolves
its response to environmental change. It is not a claim to have reproduced
the book's numerical tables, and it does not interpret synthetic landscape
peaks as measured geopolitical entities.

## Published case

Tim Blackwell, Jürgen Branke and Xiaodong Li, **Particle Swarms for Dynamic
Optimization Problems**, in *Swarm Intelligence: Introduction and Applications*
(2008), printed pages 193–218. Page numbers below refer to the uploaded book.

The exact chapter is named in the docstring of DEAP's
[`examples/pso/multiswarm.py`](https://github.com/DEAP/deap/blob/8a96fd3a75026f7b30e835f595a5199c75634ddf/examples/pso/multiswarm.py).
The [official DEAP tutorial](https://deap.readthedocs.io/en/master/examples/pso_multiswarm.html)
also explains the implementation, though its bibliography cites the earlier
Blackwell–Branke 2004 paper. Source provenance is recorded in
`vendor/deap/PROVENANCE.md`.

| Book location | Reconstructed mechanism |
|---|---|
| pp. 195–196, equations 1–3 | Constricted PSO motion; chi 0.729843788, c 2.05 |
| p. 199 | Uniform-volume quantum sampling inside a ball |
| pp. 201–203 | Multiple swarms; exclusion; adaptive birth/removal of swarms |
| p. 203 | Temporary quantum conversion after detecting environmental change |
| p. 204, Algorithm 3 | Best-point reevaluation, attractor refresh, update and exclusion |
| pp. 208–209, Table 1 | Five-dimensional Moving Peaks scenario and offline error |
| pp. 210–211, Table 3 | Five-neutral, zero-permanent-quantum particle configuration |

The v1 baseline is the book-tested **5 + 0** configuration: five neutral
particles per swarm, temporarily converted to quantum particles for one
iteration after change. `nexcess=1`; initial swarm count is one. The book
also tested permanent quantum particles; its stronger **5 + 1** comparison
is not implemented or claimed here. A score better than 5 + 0 alone would
not establish superiority over all algorithms or settings in the chapter.

## Landscape configuration

The pristine vendored `MovingPeaks` implementation uses conical peaks.
The default case explicitly sets five dimensions, ten peaks, coordinate
range [0,100], peak-height range [30,70], width range [1,12], change period
5,000 evaluations, displacement severity 1.0 and movement correlation 0.0.
Height- and width-change severities are 7.0 and 1.0, following DEAP Scenario 2.
DEAP initialization sets all initial heights to 50 and samples widths and
positions. The book does not provide original seeds or an unambiguous complete
initialization record, so exact trajectory matching is not claimed.

The pinned source sets Scenario 2 displacement severity to **1.0**, despite
the documentation table advertising 1.5. Its correlation is **0.5**;
the book's Table 1 uses **0.0**. The runner explicitly configures both.

The original table protocol averaged 50 runs of 500,000 evaluations
(100 change boundaries) per setting. The runner permits that protocol, but
shorter evolutionary evaluations or diagnostics must be labeled by their
actual horizon and repetitions. They are not table reproductions.

## Corrected defect and documented implementation choices

1. **Quantum sampling defect.** In the pinned DEAP `convertQuantum`, the
   argument `dist` is overwritten by a floating-point direction norm before
   being compared to the distribution names. All three relocation branches
   are unreachable. The original file remains pristine. The research
   simulator implements the book's UVD formula using a distinct norm
   variable. A focused test isolates the upstream function and demonstrates
   its behavior; another tests the corrected distribution. This correction
   is baseline work, not a ShinkaEvolve discovery or improvement.
2. **Attractor reevaluation.** The baseline reevaluates each personal best
   following a detected change, then rebuilds the swarm best, as in Algorithm
   3. The DEAP example instead clears memories. Memory reset remains an
   explicit option available to an evolved response policy.
3. **Convergence convention.** Following DEAP, a swarm is free if its maximum
   pairwise particle distance exceeds twice the exclusion radius. The radius
   is X/(2 M^(1/d)). This diameter convention is a practical approximation
   to the book's smallest-enclosing-circle description; it is not an exact
   enclosing-ball computation. The radius is calculated before swarm birth
   or removal within each iteration, following DEAP's ordering.
4. **Particle motion and boundaries.** Initial positions and velocities follow
   DEAP (positions within the domain, velocity components in [-X/2,X/2]).
   Particle positions are not clipped; the landscape's peak positions reflect
   at its boundaries. Quantum conversion retains velocity unless a candidate
   explicitly changes that response. Random-number consumption order need
   not match the upstream code's exact trajectories.
5. **Asynchronous updates.** Attractors update as particles are evaluated.
   Quantum particles sample around the current refreshed swarm attractor.
   A landscape change can occur during detection, memory reevaluation or
   particle updates. The algorithm learns of change by subsequent counted
   best-point reevaluation, not an oracle change flag. A partially stale
   memory can therefore persist until detection, as in the source procedure.
6. **Finite horizon.** Evaluation stops at exactly the requested budget even
   if an iteration, refresh or exclusion operation is incomplete. Such a
   response is retained with `completed=false`. DEAP's loop can overshoot a
   budget; equal experimental accounting takes precedence here.

## Candidate-program interface

The fixed simulator calls `choose_response(observation)` only when a counted
reevaluation of a swarm's remembered best changes its observed fitness.
The function returns a dictionary; omitted fields take baseline defaults.

| Return field | Meaning | Baseline |
|---|---|---|
| `radius_scale` | Nonnegative finite multiplier of 0.5 times displacement severity | 1.0 |
| `fraction` | Fraction of particles relocated; ceil(fraction × swarm size), selected uniformly | 1.0 |
| `memory` | `reevaluate` all personal bests, or `reset` all memories | `reevaluate` |
| `reset_velocity` | Set relocated particles' velocities to zero | false |

All particles continue to receive their normal per-iteration evaluation;
selecting fewer relocations does not remove those evaluations. Reevaluation
uses extra objective evaluations, which are charged to the same budget.
Resetting memory can therefore trade information against evaluation cost.
Zero `fraction` disables relocation but retains the selected memory response.

The observation contains dimension, domain width, swarm size and count,
swarm diameter, previous and current observed best fitness, absolute and
relative fitness drop, recent improvement, evaluations since the last
response, previous response radius, default radius, displacement between
observed best positions at successive responses, and remaining evaluations.
The baseline radius intentionally uses the configured displacement severity,
as in the book. True peak positions, global optimum, offline error and RNG
seeds are never passed to the policy. Results may contain evaluator-side
landscape data for analysis and visualization after execution.

The baseline returns:

```python
{"radius_scale": 1.0, "fraction": 1.0,
 "memory": "reevaluate", "reset_velocity": False}
```

Invalid keys or values fail explicitly. Candidate policies may implement
conditions and formulas over the observations; research interpretation must
describe the behavior of the evolved program, not only its fitness value.

## Optional particle-retention experiment

The separate `particle_retention_v1` task adds an optional `retention_priority`
keyword to `run_case`. Calls without that hook retain the historical numerical
path and RNG consumption, checked against the preceding published simulator.
After all existing counted personal-best reevaluations, the hook scores one
immutable snapshot of all five particles and exempts one from relocation. That
particle continues ordinary PSO movement; all five memories survive. The other
four relocate at radius multiplier 1.25 with velocities retained. Movement order,
asynchronous attractor updates and objective accounting remain unchanged.

The [task contract](../tasks/particle_retention_v1/task_prompt.txt) defines refreshed
personal-best quality/rank, normalized position and motion features, zero-distance
alignment and the separate selection RNG. No index, hidden optimum, error or new
objective query supplies a feature. Every selection draws the same kind of random
permutation whether tied or not. Its random reference is therefore newly evaluated,
not substituted from historical trajectories. The benchmark still supplies the
environmental scale through `default_radius = 0.5 * move_severity`.
See the [prospective protocol](particle_retention_v1_protocol.md); the eight-case
suite is development data, with no automatic fresh validation campaign.

## Measurement, reproducibility and records

`run_case(config, policy=None, progress=None)` returns JSONable configuration,
offline error, evaluation counts, per-environment records, sampled error
traces, response decisions and optional particle/landscape snapshots.

Every objective call counts: initial particles, best-point change detection,
personal-best memory refresh, ordinary or quantum particles, and exclusion
reinitialization. No candidate receives free objective queries. Landscape
optima are used only by the fixed evaluator to measure error.

The landscape owns a Python `random.Random(environment_seed)` independent of
the optimizer's RNG. Candidate-specific random draws therefore do not change
the landscape sequence. Each initial and subsequent environment includes a
SHA-256 hash of its positions, heights and widths, enabling exact pairing
between runs. Optimizer seeds may also be matched, but policies that consume
different random draws need not have identical particle trajectories.

The primary outcome is the chapter's **offline error**: the average, over
every evaluated point, of the gap between the true optimum and the best
fitness observed since the latest environmental change. Smaller is better.
The vendored code sets `_optimum=None` at a change and resets its best error
on the next objective evaluation. Tests verify this reset and that a trace
recorded at every evaluation integrates to the reported overall score.

A change occurs immediately after the evaluation at a period boundary;
that evaluation and error belong to the previous environment. The final
budget boundary may therefore generate a new landscape with no subsequent
observations. `environments_evaluated` distinguishes visited environments
from generated change boundaries. Boundary records capture the completed
environment's error and the next environment's landscape separately.

`environment_change` progress events contain completed-environment offline,
initial and final error, evaluation count and swarm count. Responses retain
their observation, returned decision, radius, particle selection and actual
evaluation costs. Optional snapshots record positions at the indicated
evaluation instant; a particle's just-computed fitness may not yet have been
committed to the optimizer's remembered attractor in that snapshot.

The focused tests establish implementation properties. A working pipeline,
source correction or small diagnostic run does not establish that an evolved
policy generalizes. That requires the actual search and frozen-policy
comparisons reported with their seeds, scenarios, horizons and uncertainty.
