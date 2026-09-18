# Agent C research memo: coordination conventions, cost sorting and what the objective leaves out

Prepared from the preserved generation-30 evidence while `paper_trajectory_v2` continues independently. This memo is interpretation, not an amendment to the frozen experiment. No simulations, evaluator invocations, policy mutations or campaign-state writes were performed. The only new numerical operation counted edges in four already-retained representative terminal graphs; the input hash and counts are in `cooperative-network-agent-c-snapshot-analysis.json`. Those selected examples are not population estimates. Conclusions about proposals after generation 30 require the supervisor's later integration.

## Strongest findings

### 1. The policies discover a way to construct valuable groups; they do not discover the value of closure from an unstructured world

**Observed code and algebra.** Generation 5 explicitly chooses an ideal overlapping-clique degree; generation 12 improves this to enumeration of balanced partitions, and generation 26 preserves that construction logic. With degree `k` in both layers of a clique, the supplied utility reduces to

`U_i(k) = (d − c_i0 − c_i1) k² + (2 + e − d) k`.

This follows because there are `k(k−1)/2` triangles in each layer and `k` overlapping partners. It is the formula actually evaluated in `gen_26/main.java:169–204`, not an ex post fitted model. When `d > c_i0+c_i1`, its quadratic term is positive; at the frozen nonnegative incentives, maximal feasible clique size is especially attractive. At `d=1.2` and high costs `(0.6,0.6)`, the quadratic term is zero and the linear term remains positive. Thus the panel's high-triangle conditions directly favor extreme closure. The generation-30 payoff decomposition attributes 92.88% of raw improvement to `d≥1.2`; added mean triangle benefits are 1174.1311, against 626.8799 added quadratic costs.

**Interpretation.** The important computational achievement is crossing a construction barrier under local action and bilateral-consent constraints. The final topology's payoff advantage is already contained in the objective; it is not evidence that dense groups generally improve cooperation outside this model. Burghardt–Maoz explicitly study triangle/overlap returns and the role of temporarily adverse moves in escaping local traps ([2018, especially model specification and Fig. 4](https://doi.org/10.1038/s41598-018-31960-y); [primary full text](https://escholarship.org/content/qt3518m2fs/qt3518m2fs.pdf)).

**Club connection and its limit.** Buchanan's question—how membership size changes the value of a shared arrangement—is a useful conceptual comparison ([1965, *An Economic Theory of Clubs*, pp. 1–14](https://doi.org/10.2307/2552442)). Here the evolved rule computes a preferred group size and excludes outsiders. However, these are not Buchanan-style club equilibria: there are no membership prices, cost sharing, transferable compensation or endogenous constitution. G26's variable `bestPopulationUtility` assumes *every actor has the observing actor's own costs*. It is a local homogeneous-counterfactual calculation, not an observation or optimization of actual heterogeneous population welfare.

**Rival explanation.** The large development gain may depend mainly on the payoff's strong quadratic closure incentive and universal adoption, while the exact partition/overlap/memory refinements mainly accelerate construction. Existing whole-program comparisons do not identify those components separately.

### 2. The strongest new saved-graph observation is cost segregation, which differs from the programmed ID partition

**Observed saved graphs.** In two already-selected adverse-shock examples at `d=0.8,e=2`, the terminal g26 network has *no edges joining low-cost and high-cost actors*, in either layer:

| Existing illustrative case | Original mixed-cost edges, per layer | G26 mixed-cost edges, per layer | G26 low-cost subgraph, each layer |
|---|---:|---:|---|
| `6e08f32626dad8d078a9c925`, LH-13 | 38 | 0 | Complete graph on 27 actors: 351 edges |
| `f4477faf0cefc316a6433134`, LH-26, worst actor-loss example | 51 | 0 | Complete graph on 14 actors: 91 edges |

In the existing favorable-shock illustration `6e7612cbe1d242b48a1987a0` (`d=1.2,e=1.6`), g26 instead connects *all forty* actors in both layers, including all 364 mixed-cost pairs. Cost segregation is therefore a specific observed outcome, not a universal description of the policy. These counts come from `review.json → representatives → adjacency → {baseline,g26} → 100`; the analysis receipt records the review SHA-256. The entire review remains the source for aggregate statements.

**Observed code.** G26 cannot observe partners' costs. Its construction membership is instead a contiguous ID block (`gen_26/main.java:206–221`); each actor computes block size from its own costs. In the worst-loss case, high-cost actor 34's ideal five-actor block is IDs 30–34; actors 30,31,32 have low costs and their preferred block contains everyone. Yet the terminal graph places 30–32 in the complete low-cost component, gives 33 one partner per layer, and isolates 34. Therefore neither “it just enforces the ID blocks” nor “it explicitly discriminates against high-cost partners” explains the final graph on its own.

**Interpretation.** The result is compatible with endogenous sorting through asymmetric payoff opportunities, shared conventions and subsequent myopic cleanup. It resembles Schelling's distinction between local decision rules and aggregate segregation, but the analogy needs care: the construction rule already contains explicit ID-based exclusion, whereas *cost-based* segregation in these examples is not directly specified ([Schelling 1971, *Dynamic Models of Segregation*](https://doi.org/10.1080/0022250X.1971.9989794)). It is not evidence of social prejudice, strategic punishment or a general segregation theorem.

**A precise access barrier.** In the worst-loss terminal graph, isolated actor 34 would gain `1−0.6=0.4` from a first tie to low-cost actor 30. Actor 30 has degree 13 in that layer and no common neighbor with 34, so its immediate gain would be `1−0.2(14²−13²)=−4.4`. There is no pre-existing cross-layer tie to add an overlap bonus. Under the original acceptance rule used after time 93, this tie would be refused. This is exact arithmetic on a saved graph, not a recorded attempted offer or proof that this refusal caused the isolation.

**Rival explanations.** Late cleanup may sever connections that the construction regime would maintain; irreversible rejection caching may prevent recovery earlier; finite time or action order may leave unfinished groups. G26 stores a rejected partner in `memory[partner]` and excludes it in both layers on later construction turns (`main.java:55–65,100–129`); it never clears that entry, although original behavior ignores this cache after 93. No complete action trace survives to adjudicate the causal path. Calling this memory “reciprocity” would be too strong: it is also interpretable as a one-strike negative cache.

### 3. Mean-optimal does not mean incentive-compatible, inclusive or best over the life of the network

**Observed historical contrasts.** Saved results show:

| Generation | Raw terminal gain over original | Actor losses below −1e−9 / 11520 | Terminal isolates |
|---|---:|---:|---:|
| 5 | 606.129756944 | 31 | 3 |
| 12 | 606.155659722 | 5 | 3 |
| 26 | 607.013923611 | 287 | 105 |

G26 improves the mean over g12 by 0.858263889 utility units. In the paired g26-versus-g12 comparison, 658 actor-case observations gain, 568 lose and 10294 tie within the reported tolerance. These are related development observations, not independent people. G26 remains the winner under the frozen selection rule; this table identifies an alternative distributional tradeoff, not a basis for silently replacing that rule.

**Interpretation supported by network economics.** Bilateral consent to a rule-generated offer is distinct from incentive compatibility of adopting and continuing the rule. Jackson and Wolinsky show why network efficiency and pairwise stability are different concepts, with different conclusions even in simple network models ([1996, *A Strategic Model of Social and Economic Networks*, pp. 44–74](https://doi.org/10.1006/jeth.1996.0108)). Here every actor is assigned the evolved policy, including its willingness to accept temporary losses. Neither resistance to unilateral policy deviation nor a pairwise-stability audit of final graphs was evaluated. Higher total utility cannot by itself certify either. The literature is a warning about the distinction, not a theorem automatically applicable to these multiplex dynamics.

**An additional, less obvious connection: investment feasibility.** The HH no-shock control falls from mean utility 1.7233 at time 50 to −58.8006 at time 68 before ending at 332.6767. Across actor-cases, g26 has 1531 cumulative-utility losses versus original beyond tolerance, compared with 287 terminal losses. The model imposes no wealth, borrowing, solvency or survival constraint; utility is a payoff measure, not a spendable balance. Consequently “temporary sacrifice” describes the payoff path, but does not establish the ability to finance or politically sustain that path. Liquidity theory distinguishes valuable eventual investment from its feasibility under intermediate resource constraints ([Holmström and Tirole 1998, *Private and Public Supply of Liquidity*](https://doi.org/10.1086/250001)). That is a useful missing-mechanism analogy, not a claim that this network model reproduces a financial crisis.

**Rival explanation.** Temporary losses may be an acceptable abstraction for a technological or institutional construction process without a binding resource budget. Then the right limitation is domain scope, not that the program is scientifically invalid. Discounted and cumulative utility would answer different questions; neither should replace the frozen terminal score now.

### 4. Shared timing and identities function as coordination infrastructure; novelty of code is not necessarily novelty of social mechanism

**Observed code.** G26 begins construction at public time 50 and ends at 93 (`main.java:87–90`). G5 and g12 also begin at 50 but do not use g26's fixed cleanup. All use the same arithmetic ID convention across actors. IDs provide a common way to choose group members without negotiating membership; the clock synchronizes temporary tolerance of losses. This is decentralized execution of a supplied common protocol. Neither the common protocol nor common clock is itself discovered by the actors during a trajectory.

**Interpretation.** A connection to distributed computing is more exact than simply saying “no central authority”: information about identities and network structure changes what otherwise identical processors can coordinate, as Angluin explicitly analyzes ([1980, *Local and Global Properties in Networks of Processors*, pp. 82–93](https://doi.org/10.1145/800141.804655)). No impossibility theorem from that work is claimed for this stochastic interface. Public clock and labels are real resources here, even though neither reveals the hidden shock-recipient list. Their usefulness is untested under inconsistent labels, asynchronous phase transitions or alternative adoption.

**Observed distinction between novelty measures.** G25 changes g12's layer-selection rule but exactly reproduces every terminal actor utility and terminal adjacency on the panel; its cumulative utility is nevertheless 0.757674 lower per actor on average, with 632 actor-case cumulative losses and 617 gains. G26 versus its parent20 adds only 0.001875 terminal utility but 191.596181 cumulative utility on average. These are different notions of behavior, not contradictory results. Native local code embeddings and LLM novelty decisions are retained search mechanisms; they are not a direct estimate of distance between network trajectories. Behavioral novelty research makes the choice of behavioral characterization explicit ([Lehman and Stanley 2011, *Abandoning Objectives*](https://doi.org/10.1162/EVCO_a_00025); [author manuscript](https://www.cs.swarthmore.edu/~meeden/DevelopmentalRobotics/lehman_ecj11.pdf)). This project should retain its current novelty settings and describe observed diversity separately.

**Rival explanation.** Apparently small refinements may change intermediate burden-sharing enough to be substantively important, even if endpoint graphs coincide. Conversely, different source text or accepted embedding distance may still implement the same coordination convention. Neither source distance nor fitness plateau alone resolves mechanism diversity.

## Smallest discriminating follow-ups — future work only, not executed

1. **Which mechanism creates cost segregation?** First use existing actor degree/utility time series to locate when the known isolated actors lose ties, without rerunning. If a causal test is later authorized, replay the *one named LH-26 case* with g26 and a single fixed change that disables only the time-93 handoff; retain adjacency/event traces around 92–100. If isolation predates cleanup, compare a separately predeclared rejection-cache reset. This is a diagnostic pilot, not a generalization test; do not combine both interventions and attribute the result to one.
2. **Do conventions merely allocate identities, or depend on a particular alignment?** A future paired label-permutation test must preserve physical actors' costs, shock recipients, pre-shock graph and activation schedule while changing only the IDs visible to the policy. Renaming actors *together with everything attached to them* is a relabeling and cannot test identity dependence. A minimal pilot uses the same selected partial-shock case and one public bijection; several independent permutations would be needed for an estimate. Do not conflate random relabeling with private disagreement about labels or anonymity.
3. **Are gains voluntarily stable and affordable?** Start with a static saved-graph audit for mutually profitable absent ties and unilateral deletions; that would address pairwise incentives at the endpoint only. A future single-actor deviation during the construction phase tests a different claim about adopting the policy. For resource feasibility, begin by reporting minimum cumulative recovery payoff on existing paths; only a separately authorized model extension should add budgets/exit. No equilibrium, patience or financing claim follows from the current endpoint objective.

These proposals are deliberately outside the ongoing frozen discovery campaign. A future saved-results behavioral comparison can also place endpoint adjacency, time paths and actor-loss distributions alongside native code novelty; it does not require changing native search or reranking the current winner.

## Evidence index

- `results/paper_trajectory_v2/search/gen_5/main.java`: target-degree formula99–118; ID mapping163–190; membership acceptance63–76.
- `results/paper_trajectory_v2/search/gen_12/main.java`: balanced-partition objective102–140; membership rule191–224; no fixed cleanup6–12.
- `results/paper_trajectory_v2/search/gen_26/main.java`: actions6–66; acceptance68–85; timing87–90; rejection cache/overlap-first partners92–131; local-cost partition169–221.
- `java-paper/paper/Observation.java:3–10`, `java-paper/paper/Memory.java:3–12`, and `experiments/paper_trajectory_v2/task_prompt.md`: capabilities, persistent private memory, no partner costs, terminal objective, paired shocks and consent/deletion semantics.
- `results/paper_trajectory_v2/report/generation-30-review/review.json`: `progress` entries5,12,25,26,30; `representatives`; `worst_actor`; `condition_curves`; `incentives`; `scope`.
- `assets/readme/generation30-network-example.json`: exact worst-loss adjacency and actor34 outcomes.
- `paper_trajectory_v2/native.py:63–65`: preserved code-embedding and novelty configuration.
- New read-only receipt: [cost-mixing-evidence.json](cost-mixing-evidence.json), derived from review SHA-256 `8cad1fd0a854e699e7139dad286c9c799841dd11238043f6054261fb70d0b2ab`.
