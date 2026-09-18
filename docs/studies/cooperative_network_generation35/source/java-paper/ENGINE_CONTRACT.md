# Separate full-trajectory v2 engine contract

This subtree does not amend `adaptive_exploration_v1`. Its Java build uses the four
unchanged upstream files at commit `b3d7737613578da260fee561b6f73122dc4f2ab0`
and `vendor/mason.20.jar`; it never compiles against the v1 research adapter.
The original source's copyright and unresolved code-license status remain as
recorded in `docs/source_fidelity.md`. `PaperAgent`'s counter-reset implementation
is derived from that upstream method; it is not an independent relicensing.

## Running and identity

Run `bash scripts/build_paper_java.sh`, then
`python3 java-paper/build_identity.py verify`. The build receipt is
`build/paper-build-identity.json`: exact source, dependency, and compiled-class
hashes, plus an engine digest computed from the canonical source-hash mapping.
The orchestration layer must refuse changed sources or classes before accepting
any case and must retain the engine digest in each cache identity.

One case occupies one JVM because the upstream parameters are static:

```
.tools/jdk-17.0.20.1+1/bin/java -cp build/paper-classes:vendor/mason.20.jar agents.PaperRunner CASE.json TRAJECTORY.json paper.ReferencePolicy
```

The last argument can instead be `CandidatePolicy`; a freshly compiled candidate
directory must precede `build/paper-classes` on the class path. Every actor gets a
fresh policy object and its own 64-cell finite, bounded Memory, retained through
formation, the shock, and recovery. A separate Python validator constrains the
candidate to the declared capabilities; JVM execution alone is not a sandbox.

Case fields are `case_id,n,m,d,e,p,cost_before,cost_after,shock_count,shock_time,
horizon,seed,shock_seed,interpretation,sampling,record_events`; optional
`shock_recipients` gives the exact selected identities. Main cases use N=40,
m=10, empty initial networks, shock immediately after observing time50, and
observation through time100. N=100 uses general boolean adjacency and MASON
networks, with no 64-bit neighbor mask. d and e vary independently. Positive
input costs become negative actor cost coefficients in the original utility.

## Common scientific mechanics

There are two undirected layers, no self ties, bilateral consent to a new edge,
and unilateral deletion. The exact utility expression and its arithmetic order
are the upstream implementation: layer degree benefit minus actor cost times
degree squared, plus d times incident closed triangles in each layer, plus e
times incident edges appearing in both layers. Integer degree/triangle/overlap
caches make evaluations faster. Focused fixtures compare their current,
addition, deletion and rewiring utilities **bitwise** against the unchanged
`AgentsSimulation.utility(Agent, explicitAdjacency)` oracle. The engine does not
add an epsilon to the original strict-improvement comparisons.

Shock identities use a separately seeded `java.util.Random` shuffle, or an
explicit supplied list, independent of action RNG. Both layers' costs change for
the selected actors. Controls still retain selected identities but apply an
unchanged cost. This is a declared pairing override: the original executable
selects partial-shock identities from its evolving action RNG. Full-horizon
observation also overrides the original equilibrium stopping option. Neither
override is claimed to reproduce an untouched batch invocation byte for byte.

Actor utilities and cumulative utilities are observed at each integer time.
The cumulative value sums end-of-round utility, not a continuous-time integral.
Time0 is the genuinely empty network. The row at50 is before the cost change;
the next activation starts at time50 with the new costs. The row at51 is after
one complete post-shock interval. The shock never resets memory or topology.

## Named interpretations

`source_executable` with `sampling=random` preserves the actual executable
controller: shuffle all actors once per round; each independently chooses its
random or strategic branch with fixed p. It calls unchanged `bestAdd(m)` and
`bestDrop`, and unchanged `bestAddDropCombo(m)`, including the `dropCount` bug
which searches deletions only for the first eligible addition. The independent
final deletion after a successful swap is preserved; a source activation can
therefore add one edge and delete two distinct old edges. Searches retain the
source's replacement draws, wasted candidates, ties, strict comparisons and RNG
consumption. All four fixed-noise references are tested against unchanged
`GamePlayerAgent` over complete N=40, 100-round trajectories with identical
explicit timing/recipient overrides; every adjacency, current/cumulative actor
utility and RNG state must match.

`paper_directed` interprets the article and supplement literally: choose one
actor uniformly; a strategic episode repeats that **same actor** N times, each
action advancing time by1/N; a noisy episode performs one action advancing1/N.
Strategic episodes continue across integer observation times and shocks, and
are truncated only at the declared horizon. This is not N independently chosen
actors, and is not the source's shuffled schedule. The swap deletion counter is
reset for every candidate addition, and successful swaps do not trigger the
source's extra independent deletion. Each action permits one addition and one
deletion. In random sampling mode, the source's m draws per layer and m sampled
swap-deletion candidates per layer are retained as explicit source-backed
choices: prose says m individuals and does not resolve per-layer allocation or
the swap-deletion subset. Standalone deletion scans all incident ties.

For `paper_directed,sampling=smart`, each current neighbor supplies either an
opposite-layer candidate or one randomly selected eligible same-layer friend of
a friend, with equal probability; unused opportunities are filled randomly.
Both addition and swap addition searches use this mechanism. Neighbor iteration
is ascending identity order (unspecified in prose), and m opportunities per
layer are the same declared source-backed allocation. A neighbor consumes an
opportunity even if its selected route has no eligible candidate. Swap deletions
remain m sampled opportunities per layer per eligible addition. These remaining
choices are recorded, not claimed to be uniquely determined by the paper.

`source_executable,sampling=smart` is a **blocked dormant-method diagnostic**,
not a supported published smart reference. The original main controller never
calls `bestAddSmartSearch`. That dormant method iterates friend-of-friend IDs
instead of randomly choosing one, shares/mutates its search budget differently,
and leaves swaps random. More decisively, its random-fill phase resets the best
identity but retains an earlier positive gain: it can return a stale gain with
an existing edge or self. The focused N100 fixture retains the exact case,
returned and actual gains, and graph. The adapter refuses the invalid new-edge
proposal. It does not silently fix the source, create self edges, discard those
declared reference cells, or pretend the full replication gate has passed.

## All-actor policy capabilities and current extension boundary

`ActorPolicy.act(Turn, Memory)` permits choosing partners, inspecting bounded
candidate utility, proposing an add, dropping an existing incident edge,
rewiring contingent on recipient acceptance, or doing nothing. It is not a
probability-only policy. The recipient's own `accept(Offer, Memory)` controls
every proposal, including beneficial ones. `ReferencePolicy` accepts strictly
beneficial offers, otherwise draws its configured p, exactly as the source.
The seed `CandidatePolicy` delegates the same reference turn and acceptance
through this interface; it is a separate newly instantiated class for each actor.

The turn capability expires after its activation and is inaccessible during a
recipient callback. It exposes only own utility/costs/degree/triangle/overlap,
permitted static parameters, true event/microstep/time and own previous outcome,
own neighbors and neighbors of own neighbors. Candidate inspection reveals
only the actor's hypothetical utility. Other actor utilities/costs, global
summary metrics, shock labels/identities, and future shocks are absent. Previous
offer/proposal outcomes retain the correct partner, layer and result event even
when rejected. Private memory is never shared by the engine.

Manual policies get m addition inspections per layer. Swap inspections permit
one candidate addition in the source interpretation (its actual counter bug),
or up to m distinct additions per layer in paper interpretation, with m deletion
inspections per layer for each. Existing incident drops may be inspected like
the exhaustive source drop scan. One proposal attempt is allowed, including
rejections. At most one edge can be added; dropping that new edge is forbidden.
Paper allows one old-edge deletion; source allows a second only after an
accepted addition. Bounded RNG queries are an execution guard, not extra edit
opportunities. The audited `originalTurn()` is exclusive with manual actions.

The current reference implementation uses fixed case p to choose the paper
episode length. Before evolving programs without external fixed-noise
conditions, the actor-owned episode-choice callback and exact candidate
scheduling contract must be settled and versioned. This unresolved extension
boundary does not authorize any mutation before the full reference gate. The
reference results are not evidence for a completed policy-extension study.

## Output and undefined quantities

Output retains every integer-time actor observation and utility, all raw degree,
triangle, overlap and clustering counts, and full adjacency at0, shock time and
horizon. `record_events=true` additionally retains each policy callback's local
observation, proposer/recipient identity, actual microstep and result event;
callbacks are sorted by their monotonic event IDs. Exposure labels in trajectory
rows are **observer-only** and never supplied to policies.

Network size uses mean total degree across both layers, consistent with the
retained upstream analysis; mean degree per layer is a diagnostic. Eq6
spillover is twice overlap degree divided by total degree. Eq8 paper exposure
counts neighbor ties by layer, so overlap contributes twice. The original
analysis instead uses unique union-layer neighbors: both are emitted with raw
numerators and denominators. Raw undefined ratios are null. Explicitly named
source-zero conventions and low-degree/isolate counts remain alongside them;
legacy mean aliases retain only those disclosed source conventions. Systemic
shock comparisons must represent the absent unshocked group as null, and Eq4/5
cross-case normalizers and regressions are handled by the analysis layer.

Run focused checks, writing reviewable receipts, with:

```
.tools/jdk-17.0.20.1+1/bin/java -Xmx1g -cp build/paper-classes:vendor/mason.20.jar agents.PaperChecks docs/paper_trajectory_v2
```

`engine_checks.json`, `figure4_fixture.json`, and `source_smart_failure.json`
carry the compiled engine identity. The actual three-actor Fig4 fixture checks
the high-cost c=.6 bridge loss and d=.8 strict closure/endpoint threshold. It
also preserves the paper-caption qualification: aggregate triangle welfare
crosses the single-edge total at d=2/3, while .8 is the sufficient strict
endpoint/Pareto threshold. At exactly .8, original binary arithmetic may leave
tiny positive gains; analytical equality assertions use a tolerance without
changing the executable comparison.
