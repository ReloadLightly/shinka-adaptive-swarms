# Cooperation under international anarchy: evidence and limits

Agent A research memo, 18 September 2026. Read-only interpretation of the frozen `paper_trajectory_v2` experiment, with generations 5, 12 and 26 as historical anchors. The numerical statements below refer to the preserved generation-30 review, not to the eventual generation-50 winner. No simulations, evaluator invocations, campaign/provider inference calls, live-state changes or discovery-context additions were made for this memo.

**Strongest conclusion.** The experiment demonstrates that a common, locally executed coordination rule can reorganize a multiplex network and greatly raise its terminal population payoff while excluding some actors. It does not yet demonstrate that independently strategic states would adopt, maintain or enforce that rule. Decentralized execution is observed; decentralized agreement on the rule and resistance to profitable deviation are untested.

Labels used below: **Observed** means directly inspected code or retained numerical output; **Interpretation** is an inference grounded in those observations and cited literature; **Hypothesis** requires further evidence.

## 1. The relevant form of anarchy is operational, with substantial coordination supplied

**Observed.** Addition requires the recipient's `accept` callback; deletion requires no callback from the departing actor's partner. `java-paper/agents/PaperSimulation.java:150–167,269–271` implements those rights. Each actor receives a separate policy object and private memory, but the same factory installs the same candidate code in all forty actors (`:30–45`). `java-paper/paper/Observation.java:3–10` exposes local payoffs, own costs, public time, population size and identity; it excludes other actors' costs and future shock membership. No actor can command another actor's acceptance or edit an arbitrary third-party edge.

**Interpretation.** This is a useful minimal instance of cooperation without a superior decision maker at execution time. It remains compatible with organization and conventions: international anarchy means absence of common government, not absence of durable rules or order. Axelrod and Keohane explicitly separate anarchy from disorder and cooperation from identical interests; their framework emphasizes mixed interests, repeated interaction and institutional context. [Axelrod and Keohane, 1985, pp. 226–228](https://websites.umich.edu/~axe/Axelrod%20and%20Keohane%20Coop%20.pdf).

The experiment nevertheless centrally selects a population-wide program against an externally specified terminal objective. Actors do not bargain over its adoption, evolve different policies, elect an institution, or decide whether to continue following it. Common code does permit conflicting realized incentives after heterogeneous cost shocks; it does not make every actor's interests identical. Equally, an absence of centralized edge commands does not establish spontaneous agreement on the governing convention. This design cannot, by itself, adjudicate structural realism, institutionalism or constructivism.

## 2. The evolved contribution is construction across a coordination barrier, not a demonstrated enforcement solution

**Observed.** Generation 5 selects cohorts using a calculation of desirable clique degree, proposes randomly among missing within-cohort partners, prunes outsiders and accepts within-cohort offers without requiring immediate gain (`results/paper_trajectory_v2/search/gen_5/main.java:8–11,63–76,99–118,132–190`). Generation 12 replaces the rounded degree heuristic with explicit comparison of balanced cohort counts, using only the focal actor's own costs (`gen_12/main.java:102–140`). Despite the variable name `bestPopulationUtility`, this is a hypothetical homogeneous-cost calculation, not access to actual population welfare.

Generation 26 retains that partition architecture and adds preference for partners already linked on the other layer (`gen_26/main.java:92–131`). Its construction phase accepts any finite within-cohort offer, regardless of the sign of its gain; before time 50, from time 93, and below triangle benefit 0.4 it uses the original rule (`:68–90`). The executable transition is explicit:

```java
return observation.time() < 50.0
        || observation.time() >= 93.0
        || observation.triangleBenefit() < 0.4;
```

**Interpretation.** A common membership rule and willingness to pass through unfavorable intermediate states provide a plausible route around local coordination barriers. Burghardt and Maoz's original model studies partial cost shocks, local tie changes, triangle rewards and cross-layer rewards, with random exploration allowing departures from immediate optimization. This extension evolves the decision rule itself. The preceding Smaldino–D'Souza–Maoz model establishes a closely related distinction between networks that can be maintained at high costs and networks that can first be constructed there: historical structures can remain entrenched after incentives change. [Burghardt and Maoz, 2018](https://www.nature.com/articles/s41598-018-31960-y); [Smaldino, D'Souza and Maoz, author manuscript, sections III.1–III.4](https://arxiv.org/abs/1610.07221).

The saved construction troughs support the presence of temporary costs, but do not isolate which code component caused the gains. In the HH unchanged-cost control, g26 mean utility falls from 1.7233 at time 50 to −58.8006 at time 68 before reaching 332.6767 at time 100. A terminal score tolerates these losses. Individual eventual compensation is not guaranteed.

**Rival explanation.** Much of the apparent cooperation improvement may be efficient exploitation of the model's strong clique payoff and known horizon rather than a general solution to cooperation under strategic uncertainty. The policy reorganizes unchanged-cost controls too, and its onset follows the public clock rather than detecting a shock. No ablation separates public timing, membership, temporary acceptance, overlap preference and cleanup.

The acceptance convention is also not evidence of incentive compatibility. Fearon distinguishes bargaining over a cooperative arrangement from monitoring and enforcing it; this experiment supplies a shared policy and does not test those strategic problems. [Fearon, 1998, pp. 269–276](https://www.web.stanford.edu/group/fearon-research/cgi-bin/wordpress/wp-content/uploads/2013/10/Bargaining-Enforcement-and-International-Cooperation.pdf). A future profitable-deviation test is needed before calling its costly acceptance self-enforcing.

## 3. Partner choice creates selective cooperation; the memory is not established reciprocity

**Observed.** G26's `cohortBounds` assigns contiguous public-ID blocks (`gen_26/main.java:206–221`). Agents facing different costs can calculate different block boundaries. A failed proposal sets `memory[partner]=1`, and subsequent proposals skip that partner (`:54–65,102–106,119–123`). This is a permanent construction-phase blacklist indexed by partner, shared across the two layers within that actor's memory. It neither evaluates motives for refusal nor conditions future acceptance on the partner's previous cooperation. Incoming acceptance still follows current cohort membership.

**Interpretation.** This mechanism is partner selection and rejection avoidance. Calling it tit-for-tat, trust, reputation, punishment or treaty enforcement would import mechanisms not established by the code. Blacklisting could economize on repeated incompatible offers, but could also preserve an early coordination failure after its circumstances cease to apply. That latter claim remains a **hypothesis**; retained endpoint records do not identify each causal refusal.

Public IDs supply common categories. They are not observed ethnicities, ideologies, alliance commitments or “like-mindedness.” Under partial shocks, cost-dependent disagreement over categories provides a plausible route to exclusion even when everyone runs identical code. This is a sharper connection to institutions than visual similarity between a simulated clique and a diplomatic grouping: the experiment supplies a common rule for who should coordinate, while leaving rule negotiation and legitimacy outside the model.

## 4. Absolute gains, relative gains and unequal exposure must be kept separate

**Observed.** In the retained review, the original p=0 policy's mean terminal utility is 75.039097. The following use the same 11,520 actor-case observations, comprising 288 related cases and 36 history families:

| Historical program | Mean terminal utility | Gain over original | Actor losses below −1e−9 | Isolated actor-case observations |
|---|---:|---:|---:|---:|
| Generation 5 | 681.168854 | +606.129757 | 31 | 3 |
| Generation 12 | 681.194757 | +606.155660 | 5 | 3 |
| Generation 26 | 682.053021 | +607.013924 | 287 | 105 |

These values are directly retained in `results/paper_trajectory_v2/report/generation-30-review/review.json`, `progress[generation=5,12,26].baseline_actor_effects` and `.network`. Strict negative signs, including roundoff, count 95, 83 and 399 respectively; they must not be silently mixed with the displayed tolerance-defined losses. The globally selected g26 satisfies the frozen mean-utility objective. G12 is a distributional alternative, not a retrospectively substituted winner. G26's scaled fitness 2.8459607445 is its raw gain divided by 213.2896333106, not a percentage.

All 287 substantive g26 terminal losses occur at triangle incentives 0.4 or 0.8 among high-cost actors: 177 directly shocked LH observations and 110 unshocked HL observations. The worst observed loss, actor 34 in case `f4477faf0cefc316a6433134`, is approximately −6: a three-neighbor, fully overlapping configuration with utility 6 under the comparator becomes isolation with utility 0 under g26 (`review.json.worst_actor`). This is a paired policy comparison, not a claim that a particular observed deletion caused the loss. No complete event trace supports the latter assignment.

**Interpretation.** Consent over additions is weaker than guaranteed benefit: partners may delete existing relationships unilaterally, and a common convention can accept present losses without ensuring eventual repayment. A favorable partial shock can therefore coexist with losses for actors whose own costs never changed.

These distributional differences are not evidence of **relative-gains preferences**. The payoff function contains own ties, costs, triangles and overlap; it does not value outranking another actor or preventing another's future power (`PaperSimulation.java:61–68`). Snidal shows why explicitly relative-gains motivations have consequences depending on interaction structure and the number of relevant competitors; such a motive would require a new model, not relabeling inequality already measured here. [Snidal, 1991](https://doi.org/10.2307/1963847).

## 5. Multiplex dependence is a defensible IR connection; coercion requires additional mechanisms

**Interpretation.** Maoz treats international politics as interacting networks generated by states' choices about relationships, including spillovers among security cooperation, trade and institutions. This supports studying dependence across relations instead of treating each bilateral tie in isolation. It does not identify the present two binary layers with any actual pair of institutions or sectors. [Maoz, *Networks of Nations*, 2010, publisher description and chapter 5](https://www.cambridge.org/core/books/networks-of-nations/D648F66AF4B78F8E086C931618C2CC52).

**Observed.** G26 deliberately prefers a missing tie when the same partner is present on the other layer. Mean endpoint overlap rises from 0.6541 under the original to 0.9356; degree per actor per layer rises from 5.2673 to 25.1033. The utility function already rewards overlap. Neither the accounting reward nor a denser network establishes improved real-world resilience. In LH-13, g26's payoff is 285.9339 below its own LL control, while the comparator's penalty is 29.4597 (`review.json.shock_control_contrasts[condition=LH-13]`). G26 has a higher absolute payoff in the shock case but a larger shock/control gap.

**Interpretation.** Farrell and Newman require asymmetric network positions and political authority over consequential hubs to explain information advantages and denial of access. This experiment has no directed economic flows, jurisdiction over infrastructure, surveillance, bargaining threat or strategic coercion objective. An isolated actor is an exclusion outcome; it is not automatically evidence of weaponized interdependence. [Farrell and Newman, 2019](https://doi.org/10.1162/ISEC_a_00351).

Japan's updated FOIP documents connect supply-chain resilience, economic cooperation/common rules and multilayer security cooperation. They supply an empirical motivation for asking when relationships across domains reinforce access and when concentration creates vulnerability. They are statements of policy intent, not evidence that the simulated mechanism explains implementation or welfare. [MOFA, 2 May 2026](https://www.mofa.go.jp/policy/pageite_000001_01612.html). ASEAN's own Outlook emphasizes centrality, inclusiveness and ASEAN-led mechanisms, making partner agency indispensable to any empirical mapping. [ASEAN Outlook, 2019](https://www.asean.org/wp-content/uploads/2019/06/ASEAN-Outlook-on-the-Indo-Pacific_FINAL_22062019.pdf).

A defensible Japan study would separately record offers, recipient consent, delivery, use and withdrawal; measure directed sector-specific dependence and alternatives; and include third-party relationships. Common actor-ID cohorts cannot identify Japan, ASEAN, the Quad or any actual coalition. An empirically attractive policy document does not fill the missing mechanisms.

## 6. Two connections that sharpen the research question

**Stability versus efficiency.** Jackson and Wolinsky formalize why individually stable networks need not maximize collective value, even with bilateral link formation and unilateral severance. Their distinction fits the permissions here, but no current result establishes pairwise stability: g26's final original-policy phase samples only bounded opportunities and the experiment stops at time 100. More importantly, terminal network stability would not establish stability of the costly construction strategy. [Jackson and Wolinsky, 1996](https://doi.org/10.1006/jeth.1996.0108). This makes equilibrium verification and policy adoption separate questions rather than synonyms for a high score.

**Network interference.** Unshocked is not equivalent to untreated. A partner's cost change can alter one's ties, overlap and triangles. The review correctly fixes partner exposure using the original time-50 network rather than the endogenously reorganized graph, but that descriptive grouping alone does not identify a causal exposure effect. Aronow and Samii's framework distinguishes assignment, network exposure and the estimand; it supplies a way to specify a later empirical or computational design without pretending the current actor observations are independent. [Aronow and Samii, 2017](https://doi.org/10.1214/16-AOAS1005).

## Future work: smallest discriminating tests, not executed

1. **Convention or adaptation?** On one predeclared partial-shock and one unchanged-cost history, compare g26 with clock-shifted versions while preserving all other code. Shifting only the shock time versus only the policy phase would distinguish event responsiveness from a construction schedule tuned to the horizon. Use temporary losses and terminal outcomes together; no new objective is implied.
2. **Self-enforcing cooperation or common-code commitment?** Replace one predeclared actor's costly-offer acceptance with the original immediate-improvement rule, leaving its other actions and every other actor unchanged. Compare that actor's cumulative and terminal utility, others' losses and cohort completion. A private gain from deviation would refute that particular self-enforcement claim; one unsuccessful deviation would not prove equilibrium against all strategies.
3. **Coordination resource or arbitrary exclusion?** On one saved partial-shock setup, compare a common random permutation of IDs against independently scrambled actor interpretations of membership. The first changes who belongs together while preserving a public convention; the second disrupts common categorization. Repeating just enough independently chosen histories to avoid an anecdote would then test whether gains and exclusion depend primarily on shared agreement or a fortunate particular partition. This is an interface/mechanism sensitivity study requiring separate authorization.

Each proposal belongs outside the frozen continuation. The immediate contribution is the documented mechanism, its unequal outcomes and explicit boundaries on international interpretation; generation-50 findings should update these conclusions only where completed evidence changes them.
