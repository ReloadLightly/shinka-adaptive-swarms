# Emergence across substrates: adaptive MPSO and international cooperation

**Research note, 18 September 2026.** Optimizer evidence below is frozen to the
completed **Session 1** checkpoint of `book_mpso_population_200_v2`, including
generations 0–6. It is not a report of the concurrently resumed session.
This literature and mechanism analysis consumes no objective evaluations and
does not add conditions or interventions to the registered optimizer campaign.

Adaptive MPSO and cooperative international structures can resemble one another
in how repeated interactions, shared information, group organization and feedback
produce aggregate patterns. The present experiment demonstrates an evolving
**allocation rule inside an already cooperative optimizer**. It does not
demonstrate cooperation emerging among actors with conflicting interests, or
validate a theory of international institutions. The useful comparison concerns
specified mechanisms and testable responses to interventions, not particles
standing literally for countries.

## What has actually emerged in this experiment?

Three levels must remain separate:

| Level | What is specified in advance | What can develop during execution |
|---|---|---|
| Particle and subswarm dynamics | Personal/shared memories, movement equations, exploratory sampling and swarm management | Particular trajectories, concentrations of search effort, swarm lifetimes and tracking behavior |
| Population adaptation | A bounded interface, allowed observations and a one-particle resizing adapter | Different group sizes and query allocation induced by a candidate rule |
| Native program evolution | Shinka's mutation, selection and evaluation machinery | New program expressions and their recorded descendants |

The [implemented corrected engine](../src/adaptive_swarms/book_population_v2.py)
shares discoveries within each subswarm. Exclusion reinitializes a poorer swarm
when remembered best positions are too close; the convergence rule drives
creation/removal of swarms. These are prescribed operations. The permanent
exploratory role and ordinary-particle role are also prescribed; they are not
spontaneously discovered professions. The chapter motivating these mechanisms
is [Blackwell, Branke and Li (2008)](https://doi.org/10.1007/978-3-540-74089-6_6).
Exact reconstruction conventions and corrections are recorded in
[reproduction.md](reproduction.md) and the
[versioned fidelity record](book_mpso_population_200_v2_source_record.md).

There is no policy that decides whether to share honestly, withhold information,
defect, negotiate membership or create a rule. Particles have no divergent
utilities. Global particle/swarm counts are available to the allocation policy,
and centralized code enforces exclusion and birth/removal. Calling this purely
local self-government would therefore misdescribe the implementation. Particle
counts change through additions/removals; particles do not migrate between
groups and there is no conserved global membership pool.

At the inspected checkpoint, the archived native database contains **seven valid
programs: the seed and six descendants**. Generation four descends from generation
two, whose parent is generation one, whose parent is the seed. The executed
[generation-four source](../artifacts/book_mpso_population_200_v2/20260917T065325Z/session_001/evolution/search_seed_670001/gen_4/main.py)
requests two or three ordinary particles according to observed fitness
deterioration, total workload and its preceding requested target. Its two
thresholds explicitly encode hysteresis. That condition was produced in the
outer program search; it is subsequently executed as code inside each simulation.

The rule's four-history development error is **1.928740**, compared with
**2.191283** for corrected 5+1 and **2.080392** for the strongest measured constant
target, two. All methods receive 500,000 objective queries per history in five
dimensions. Across those four histories, generation four makes **1,582 additions
and 2,503 removals**. These establish active resizing and an interim performance
advantage on selected development data. They do not isolate the benefit of
hysteresis, prove generalization, measure institutional cooperation or identify
distinct-peak coverage from swarm counts. The enclosing-ball correction is
baseline fidelity work, not an evolved improvement. Evidence: the
[Session 1 report](studies/book_mpso_population_200_v2/REPORT.md),
[native database](../artifacts/book_mpso_population_200_v2/20260917T065325Z/session_001/evolution/search_seed_670001/programs.sqlite),
[metrics](../artifacts/book_mpso_population_200_v2/20260917T065325Z/session_001/evolution/search_seed_670001/gen_4/results/metrics.json)
and [raw case 000](../artifacts/book_mpso_population_200_v2/20260917T065325Z/session_001/evolution/search_seed_670001/gen_4/results/case_000.json.gz).

Here, *emergence* can provisionally mean a reproducible aggregate pattern generated
by interacting components, whose particular outcome is not directly prescribed.
This is a working measurement convention. Bedau's stricter weak-emergence concept
requires derivability from the underlying dynamics and conditions **only through
simulation**. Running a simulation does not prove that requirement; this project
has established neither computational irreducibility nor strong emergence.
[Bedau (1997), definition and discussion](https://people.reed.edu/~mab/papers/weak.emergence.pdf).

## Mechanism correspondences and their limits

The following are **analytical analogies**, not observations about a particular
country or treaty. A consistent provisional mapping is particle → actor,
subswarm → cooperative group, and optimizer population → interacting groups.
This mapping fails where countries have overlapping memberships, different
interests and voluntary institutional choices absent from the code.

| Mechanism | MPSO implementation or observation | Proposed international analogue | Boundary of the claim |
|---|---|---|---|
| Information aggregation | A discovery can update a shared attractor and redirect other particles | Members pooling information and adapting policies to a common reference | MPSO sharing is compulsory, immediate within its update ordering, and nonstrategic |
| Coordination within groups; differentiation between groups | Common attractors coexist with exclusion and exploratory swarms | Cooperation inside organizations alongside competition or specialization between them | Exclusion is a programmed diversity operator, not bargaining, war or sovereign exit |
| Persistent memory | Personal/shared bests survive and are reevaluated; the evolved rule also uses its previous target | Institutional memory and history-dependent commitments | The mechanism generating persistence differs; two numerical thresholds do not explain treaty durability |
| Adaptation after disruption | Counted checks detect changed returns; populations and trajectories respond | Revising cooperation when conditions or perceived returns change | Benchmark shocks are exogenous; political actors can alter one another's environment |
| Multiple centers of activity | Several subswarms explore concurrently | Polycentric experimentation and learning | MPSO groups do not independently make or contest their governing rules |
| Resource and monitoring tradeoffs | Group size changes the shares of movement, detection and memory queries | Costs of coordination and information provision can affect feasible cooperation | Objective queries are not a measured proxy for diplomatic expenditure or political welfare |

The international side draws on distinct theories. Axelrod and Keohane identify
interest alignment, expected future interaction and actor number as important
conditions for cooperation, while emphasizing perceptions, issue linkages and
institutions. Actors can deliberately change those conditions. None of that
implies that cooperation is automatic whenever a population contains many
interacting units. [Axelrod and Keohane (1985)](https://doi.org/10.2307/2010357).

Ostrom's account of polycentric governance emphasizes multiple authorities at
different scales, local knowledge, learning and mutual monitoring. It explicitly
allows institutional independence and also recognizes coordination failures and
opportunism. This supplies a closer organizational analogy than a single global
best attractor would, but sharing the appearance of multiple centers is
insufficient: the institutional mechanisms must also be represented.
[Ostrom (2010), especially section 4](https://commonsblog.wordpress.com/wp-content/uploads/2007/10/elinor-ostrom-polycentric-system-for-coping-with-climate-change.pdf).

Reciprocity is a further, currently missing mechanism. Axelrod and Hamilton's
repeated-game model permits cooperation or defection, with individually evaluated
consequences and a probability of future encounters. Conditional cooperation can
persist under specified conditions; unconditional defection can also persist.
Ordinary MPSO attraction to a shared best contains no analogous temptation to
defect. [Axelrod and Hamilton (1981)](https://doi.org/10.1126/science.7466396).
Likewise, Axelrod's norms model studies behavioral rules and enforcement, including
punishment of non-enforcement. MPSO exclusion does not implement that mechanism:
it responds to spatial redundancy, not a violated social obligation.
[Axelrod (1986)](https://doi.org/10.2307/1960858).

One revealing resemblance is feedback between aggregate organization and local
action. Generation four uses total particle and swarm counts to adjust a local
resizing threshold; those choices subsequently change the totals. This supplies
a fully inspectable feedback loop. An institution can similarly influence member
decisions that sustain or change it. The latter is an inference suggested by the
institutional literature, not a causal finding from these optimizer runs. In the
code, the feedback channel is explicitly supplied by the observer interface.

## What could be established across substrates?

Four evidential steps should not be collapsed:

1. **Resemblance:** both systems display grouping or persistence. This supports
   a descriptive comparison, with many possible underlying explanations.
2. **Shared formal mechanism:** explicitly mapped variables and update rules
   yield corresponding behavior under stated assumptions. This establishes a
   conditional mathematical result or model equivalence, not political truth.
3. **Shared causal response:** matched interventions change corresponding
   observables in the predicted direction in both domains, beyond rival models.
4. **Empirical transfer:** an independently specified mapping predicts previously
   unused political observations. This requires social data and identification
   of alternative causes; successful optimization alone cannot supply it.

A useful precedent is Axelrod and Bennett's landscape model of aggregation,
which explicitly represents actor sizes and bilateral alignment propensities
and examines national and company alliances. Under symmetric propensities, an
actor's local reduction in frustration reduces a system-level energy function.
That is a conditional bridge between local interaction and aggregate organization,
not simply a visual metaphor. [Axelrod and Bennett (1993), including note 2](https://doi.org/10.1017/S000712340000973X).

For example, write a single-counted pair potential
`E = sum(i<j) size[i] * size[j] * propensity[i,j] * separation[i,j]`, and individual
frustration `F[i] = sum(j!=i) size[j] * propensity[i,j] * separation[i,j]`.
For a unilateral move, symmetric propensities and fixed positive sizes give
`change(E) = size[i] * change(F[i])`. This restates the mechanism with a different
normalization. Asymmetric preferences or changing relationships remove this
guarantee. The current MPSO's fitness landscape is an externally supplied function
over candidate positions, not this landscape over actors' coalition memberships;
the algorithms are not isomorphic.

A serious cross-domain claim would specify the shared variables, observables,
information access, time scales, disturbances and interventions before checking
results. Comparable dimensionless ratios—such as adaptation delay divided by
environmental-change interval—are more meaningful than equating one particle
update with one political year. Similar aggregate distributions alone cannot
establish the same mechanism. Human interpretation, heterogeneous power,
conflicting preferences and deliberate rule revision remain substantive model
choices, not details removable by renaming variables.

## Falsifiable next questions

These are **proposed separate studies**, not changes to the running 50-descendant
campaign. The current campaign's frozen controls, selection and fresh-comparison
procedure retain priority.

| Hypothesis | Intervention and comparison | Outcome that would count against it |
|---|---|---|
| H1. Shared information improves tracking in the studied MPSO regime | Compare frozen shared-best search with a competent personal-memory-only control; prespecify tuning effort and equal counted-query budgets, keep environmental histories paired | No reliable tracking improvement on fresh histories; grouping by itself is insufficient |
| H2. Generation four benefits from responding to current state and history, beyond smaller populations | Freeze variants removing the workload input or hysteresis, and a state-independent target process fitted only on development data to approximate target frequencies and dwell times; retain the same adapter | Comparable fresh performance from the state-independent process, or loss of the effect after competent size controls, weakens the adaptation explanation |
| H3. Differentiated groups preserve useful alternatives under changing conditions | In separate optimizer and cooperation models, vary group coupling while holding opportunities and costs explicit; measure recovery, redundancy and persistence | Benefits occur only in one model or disappear after resource matching; a universal claim fails even if one domain benefits |
| H4. Anticipated future interaction sustains voluntary cooperation under conflicting payoffs | In a new repeated-interaction model, vary encounter continuation, information reliability and private benefits from defection; let agents choose costly sharing and assess their own returns | Cooperation survives solely because sharing is imposed or policies are selected directly for collective welfare; that would not explain voluntary cooperation |
| H5. A common organizational mechanism predicts political observations beyond analogy | Select one domain, such as information-sharing institutions; freeze mappings to participation, contributions, monitoring and disruption; test unused periods against persistence, power and common-interest alternatives | Failed predictions, equally good simpler alternatives, or dependence on parameters chosen after seeing the test data |

H1–H3 need whole-history outcome analysis, not thousands of correlated updates
treated as independent replications. Removing shared attraction also changes
motion, so H1 identifies the complete sharing mechanism's effect, not an isolated
semantic effect of “cooperation.” H2's matched target process cannot preserve
every downstream population or workload trajectory; these are mediators affected
by the intervention and should be reported rather than silently controlled away.
If a benefit survives H2, a follow-up mediator study can examine which response
pathway carries it.

H4 requires a different model: heterogeneous actors, private consequences,
optional costly communication, observable commitments and possible exit. To test
institutional emergence, start without the target institution already enforced
and permit actors to establish or abandon its rules. Record both unsuccessful
attempts and stable formations. Evolutionary reproduction or learning must use
the specified actor incentives; selecting every actor policy for a global welfare
score would answer a designer's optimization question instead.

For every extension, report the grouping rule, membership persistence, actual
information/contribution flows, distributions of actor returns, cost accounting
and recovery after shocks. A coalition's existence does not show that its members
cooperate, that outsiders benefit, or that its outcome is normatively desirable.
The concrete result presently supported is narrower: a recorded native program
changed population allocation and improved selected MPSO development outcomes.
The comparison with international organization identifies plausible mechanisms
and discriminating tests; empirical equivalence across substrates remains open.
