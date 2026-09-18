# Generation-35 scientific review — completed development continuation

> **Separate cooperative-network study — not PSO results.** This report and its selected Java policy come from [`shinka-cooperative-network` at `42ccaaf`](https://github.com/ReloadLightly/shinka-cooperative-network/commit/42ccaaf4b4f9c361f671cf54b6d874bc4d442359). Generation 35 is the review boundary; **generation 34 is the selected program**. Scientific claims and checkpoint descriptions refer to that source study. This small publication contains reports, the selected source and four figures; supporting records remain linked to the source commit. It does not change the adaptive-swarms campaign or publish a runnable campaign checkpoint. [File provenance](PROVENANCE.json).

The continuation finds a new ID-based membership convention within the established overlapping-cohort construction family. Generation 34 changes contiguous groups to round-robin groups and improves mean terminal utility by only **0.007465278** over generation 26. It reduces terminal-loss observations but increases isolation and cumulative-loss observations. Two other proposals exactly reproduce earlier saved trajectories. The additional search contributes evidence about identity-dependent distributional tradeoffs and a plateau, rather than a new cooperation architecture or a demonstrated generalization gain.

**Paused after generation-35 review; further discovery and fresh confirmation await a subsequent decision.** All five new proposals are valid on the frozen 288-condition development panel. Across the campaign, 35 descendant proposal slots are consumed and 32 descendants are valid; seed 0 is separate. Failed and invalid proposals retain their slots. No proposal 36 or unfinished accepted work remains. The eventual fifty-proposal ceiling is preserved, with fifteen slots unused.

The [generation-30 review](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/docs/paper_trajectory_v2/generation30_review.md) remains historical evidence. The [research-team synthesis](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/docs/paper_trajectory_v2/research_synthesis.md) distinguishes observed outcomes from interpretations and proposed future tests. The [persistent operational log](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/report/research_progress.md) records accounting; this report explains executable changes.

## What each new proposal tests

### Generation 31: completion-aware balanced cohorts

**Provenance.** Parent 15 (`172965e7-9e12-4ec2-b066-f70fbb57e3cd`), archive inspiration 21 and top inspiration 18; island 1; actual model `headless/codex@gpt-5.6-sol?effort=xhigh`; crossover patch; native evolved prompt `aab9b733…`. [Executable](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/search/gen_31/main.java).

**Executable change.** The child removes its parent's population-wide construction override before time 50 at strong triangle incentives. Instead, it evaluates hypothetical balanced ID partitions using its own costs, builds during recovery and permits a short finishing period through time 95. From time 93, an actor permanently returns to the original rule if no unblacklisted, missing within-group partner remains. This local exhaustion test does not prove that the clique is complete: previously rejecting partners are ignored, outside ties can remain, and the flag is set during the actor's own turn.

```java
if (observation.time() >= 93.0 && !hasEligibleMissingPartner(...)) {
    memory.set(63, 1.0);
    turn.originalTurn();
    return;
}
```

This shortened excerpt illustrates the handoff; the executable retains the full arguments. The author's stated aims are a bounded, completion-aware handoff and removal of an allegedly underperforming early override. Those are proposal hypotheses. The crossover changes several components, so its evaluation does not isolate their individual effects. Code inspection identifies a recombination of the existing cohort family, with substantial similarity to G22, rather than a new coordination mechanism.

**Measured outcome.** Valid on all 288 conditions. Raw mean terminal gain over the original is **607.013680556**: **+0.012638889** versus parent 15 and **−0.000243056** versus incumbent 26. Scaled fitness is **2.845959604945028**, obtained by dividing the raw gain by the frozen scale **213.28963331061775**; it is not a percentage. G26 remains selected.

Compared with parent 15, substantive terminal-loss observations fall from **349 to 289** and isolates from **146 to 96**, while cumulative-loss observations rise from **920 to 1,550**. Mean cumulative gain falls from **38,505.091389 to 13,925.668472**. Code inspection establishes that the child removes early construction; the measured contrast establishes a large change in the payoff path. Because other components also change, the comparison does not isolate how much of that difference is caused by removing the early phase. A small terminal improvement therefore coexists with a substantial path tradeoff.

Against the original, saved-output analysis records **289 substantive terminal losses, 96 isolates and 1,550 substantive cumulative losses**, compared with G26's **287, 105 and 1,531**. Of **11,520** paired actor-case observations, **150 gain and 147 lose** relative to G26; **11,223** are within **1e−9**. All **288** terminal population means exactly match G22. A subsequent comparison finds all **288** retained compressed trajectory hashes identical to G22, establishing identity of the saved paths as well as the endpoints. [Trajectory-hash comparison](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/report/continuation-trajectory-equivalence.json).

Mean degree **25.1026**, zero-convention clustering **0.74890** and overlap **0.93650** remain close to G26. All **288** time-50 graphs and actor utilities equal the baseline. [Saved analysis](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/report/generation-31-incremental/review.json).

**Native events.** UCB selected Sol/xhigh from the preserved Astra/Sol portfolio. Local source embeddings admitted the proposal with maximum similarity approximately **0.97075**, below **0.99**; no novelty-model check was triggered. Code-novelty admission does not establish a new behavioral mechanism. The next native meta update triggered after completion and completed normally; the final accounting below reconciles its twelve responses.

### Generation 32: overlap and triangle priority

**Provenance.** Parent 21, archive inspiration 23 and top inspiration 31; island 1; actual model Astra/xhigh; diff patch `overlap_triangle_priority`, using evolved prompt `aab9b733…`. [Executable](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/search/gen_32/main.java).

**Tested behavior.** The child retains its parent's cohort targets, pruning based on cost relief, rejection memory, costly within-cohort acceptance and fixed time-93 handoff. Missing-partner selection now prioritizes actors already linked on the other layer, then ranks those candidates by common within-cohort neighbors on the addition layer. If none has an opposite-layer tie, it retains uniform reservoir selection and the previous random-draw order. Common-neighbor counts use the permitted local neighbor-of-neighbor interface.

```java
int priority = contains(otherNeighbors, partner)
        ? common[partner - first]
        : -1;
```

The proposal text hypothesizes quicker overlap and triangle completion and explicitly recognizes a risk of concentrating construction around existing clusters. This is a local partner-ranking refinement, not a new shared convention. Native sampling supplied the completed meta update's triangle-priority recommendation. That is observed use of advice, not an isolated causal test of the meta mechanism.

**Measured outcome.** Valid on all **288** conditions. Raw mean gain is **607.011493056**: **−0.000173611** versus parent 21 and **−0.002430556** versus incumbent 26. Scaled fitness is **2.8459493489378977**; G26 remains selected.

G32 produces **308 substantive terminal losses and 113 isolates** against the original; parent 21 has **309 and 107**, while G26 has **287 and 105**. Mean degree **25.10043**, zero-convention clustering **0.75229** and overlap **0.93462** do not establish improved endpoint overlap.

Cumulative-loss observations decline from **1,582** for parent 21 to **1,543**, and mean cumulative gain rises from **13,924.030382 to 14,089.567778**. Thus a mutation that loses on the terminal objective still changes path outcomes. It trails G26's mean cumulative gain of **14,117.387639** and **1,531** cumulative-loss observations.

G32's **308** terminal losses comprise **204** directly shocked actor-case observations under adverse shocks, **99** unshocked observations under favorable partial shocks and **5** observations in the high-cost control. These are actor-case counts, not independent individuals. [Saved-output review](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/report/generation-32-incremental/review.json).

**Native events.** The implemented priority follows the selected native meta recommendation, verified in the actual provider prompt and accepted-job receipt. This establishes transmission and implementation of advice, not a causal benefit from the meta mechanism. G32's completion triggered the third native prompt evolution; the resulting prompt `b1b2c70d…` was selected for G33–35.

### Generation 33: return from time 95 to time 93

**Provenance.** Parent 29, archive inspiration 16 and top inspiration 19; island 0; actual model Sol/xhigh; diff patch `handoff_at_93`; newly evolved prompt `b1b2c70d-9030-41be-a518-0bfcfd72a73c`. [Executable](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/search/gen_33/main.java).

**Tested behavior.** A one-line edit changes the shared construction predicate from `time < 95.0` to `time < 93.0`, returning both action and acceptance to the original policy two rounds earlier. The proposal text describes the change as allowing more cleanup time, consistent with the selected native meta advice to test neighboring cutoff times independently. All other parent-29 mechanisms remain unchanged. This is a timing refinement within an established family.

**Native novelty.** Maximum local source similarity **0.9995416403** exceeded **0.99**; one Astra/xhigh novelty call admitted the candidate. The judge's actual context compares only parent 29 with candidate 33. Its admission therefore concerns novelty relative to that parent, not the full archive. Code inspection finds that the edit restores G26's substantive balanced-partition, overlap-first and time-93 combination, although source organization and guards differ. The chosen native meta advice proposed neighboring **92/94** cutoffs; this mutation instead restores the known **93** cutoff. Admission alone cannot establish behavioral novelty. [Novelty evidence](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/report/g33-novelty-evidence.json).

**Measured outcome.** Valid on **288/288** conditions. Raw gain **607.013923611** equals incumbent 26 exactly and improves on parent 29 by **0.011597222**. Native fitness **2.8459607445013755** ties G26, which remains selected.

All **11,520** terminal actor utilities, all **288** terminal population means and every retained compressed trajectory hash equal G26. Thus the saved paths, endpoint structure and cumulative observations are reproduced, not merely the aggregate score. G33 retains **287 substantive terminal losses, 105 isolates and 1,531 cumulative-loss observations** against the original. [Saved analysis](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/report/generation-33-incremental/review.json), [trajectory identity](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/report/continuation-trajectory-equivalence.json).

### Generation 34: round-robin membership

**Provenance.** Parent 30, archive inspiration 22 and top inspiration 26; island 2; actual model Sol/xhigh; full replacement `round_robin_cohorts`, using native prompt `b1b2c70d…`. [Executable](selected_program/main.java).

**Tested behavior.** The mutation replaces contiguous ID blocks with residue-class membership:

```java
return actor % cohortCount == other % cohortCount;
```

The optimized cohort count and multiset of cohort sizes remain unchanged. Actual membership changes, as can the size of a particular actor's cohort. Partner enumeration, acceptance and every outside-tie deletion test consistently use the new rule. Overlap-first selection, private rejection memory, paired cleanup and phase timing remain the parent's mechanisms.

Code inspection finds the first such membership convention among the available earlier candidate sources. This is a new grouping convention within the existing construction family, rather than a new cooperation architecture. The proposal tests whether rematching identities, histories and shock exposure helps; a modulo rule alone establishes neither better mixing nor anonymous coordination. This specific native meta recommendation is retained in the actual provider prompt. Local similarity **0.975919** is below **0.99**, so no novelty-model call was triggered.

**Measured outcome.** Valid on all **288 conditions**. Mean terminal utility is **682.060486111**, raw gain **607.021388889**, and native fitness **2.845995745160629**. It improves on parent 30 by **0.008645833** and on incumbent 26 by **0.007465278**, becoming the new development winner under the unchanged rule.

The result is mixed distributionally. Substantive terminal-loss observations decline from G26's **287 to 271**, but isolates rise from **105 to 118** and cumulative-loss observations from **1,531 to 1,549**. Against G26, **337** actor-case observations gain and **310** lose beyond the descriptive tolerance; **10,873** tie within it. Mean cumulative gain rises only **0.641493**, to **14,118.029132**, despite more cumulative-loss observations. These are different criteria: fewer terminal losses do not imply less isolation or fewer losses along the path.

Mean degree is **25.10955**, zero-convention clustering **0.75403** and overlap **0.93835**. In the historical actor-34 collapse case, G34 leaves that actor with one overlapping partner and terminal utility **2.8**, improving on G26's zero but remaining below the original's **6.0**. The membership change therefore redistributes outcomes without eliminating exclusion. [Saved-output analysis](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/report/generation-34-incremental/review.json), [native membership advice and code evidence](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/report/g34-membership-evidence.json).

### Generation 35: choose a layer by eligible overlap availability

**Provenance.** Parent 16, archive inspiration 19 and top inspiration 33; island 0; actual model Astra/xhigh; diff patch `overlap_availability_tiebreak`, using native prompt `b1b2c70d…`. [Executable](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/search/gen_35/main.java).

**Tested behavior.** When both layers have the same total degree, count eligible within-cohort partners missing on each layer but present on the opposite one. Choose layer 1 only when its eligible overlap count exceeds layer 0's; retain layer 0 on a tie. The count ignores self and remembered failures, and consumes no random draws. Unequal degrees retain the sparser-layer choice. Partner selection remains uniform within the chosen eligible pool, so selecting that layer does not guarantee an overlapping partner.

The tie break is inactive when all current neighbors are within the cohort and unblacklisted: equal degrees then imply equal one-sided overlap counts. Its effect therefore requires unequal external or remembered-failure contributions. The parent's local handoff from time 93 and hard cutoff 97 remain unchanged. This implements the native meta recommendation to extend overlap preference to layer choice. The proposal text identifies faster spillover construction as a hypothesis and delayed triangle closure as a possible cost. It is a narrow scheduling refinement, preserving the parent's partition, acceptance, pruning, memory and phase transitions. Local similarity **0.972987** admitted it without a novelty-model call. [Advice provenance](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/report/g35-meta-advice-evidence.json).

**Measured outcome.** Valid on all **288 conditions**. Mean terminal utility is **682.048576389**, raw gain **607.009479167**, and native fitness **2.8459399068995874**. It loses **0.001458333** versus parent 16 and **0.011909722** versus incumbent 34. The frozen winner remains G34.

Against the original, G35 has **310 substantive terminal losses, 107 isolates and 1,586 cumulative-loss observations**. Mean cumulative gain is **13,924.229653**. Mean degree is **25.09983**, zero-convention clustering **0.75229**, and overlap **0.93485**. Relative to historical G26, 178 actor-case observations gain, 202 lose and 11,140 tie within the descriptive tolerance. In the historical actor-34 case it ends isolated, at utility zero, with cumulative effect **−243.6**. This narrow scheduling refinement provides no terminal-objective improvement and does not establish a more inclusive recovery mechanism. [Final saved-output analysis](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/report/generation-35-review/review.json).

## What the additional search contributed

| Proposal | Parent; archive/top inspirations | Island; actual mutation model | Raw gain over original | Difference from parent | Difference from incumbent then | Scientific interpretation |
|---|---|---|---:|---:|---:|---|
| 31 | 15; 21/18 | 1; Sol/xhigh | 607.013681 | +0.012639 | −0.000243 | Recombination; saved paths exactly reproduce G22 |
| 32 | 21; 23/31 | 1; Astra/xhigh | 607.011493 | −0.000174 | −0.002431 | Partner ranking changes path outcomes, loses terminal objective |
| 33 | 29; 16/19 | 0; Sol/xhigh | 607.013924 | +0.011597 | 0, exact tie | Time-93 handoff reproduces G26 paths |
| 34 | 30; 22/26 | 2; Sol/xhigh | **607.021389** | +0.008646 | **+0.007465** | New membership convention within the same construction family |
| 35 | 16; 19/33 | 0; Astra/xhigh | 607.009479 | −0.001458 | −0.011910 | Layer-choice refinement loses to parent and incumbent |

All rows are complete evaluations. The descriptive table rounds values; exact native fitness determines selection and retains G26 on G33's exact tie. Raw utility gains are not percentages. The incumbent for G31–34 is G26 and for G35 is G34. There are no new failures or invalidities to score.

![Continuation utility differences](figures/continuation-progress.png)

*The continuation changes are tiny relative to G26's mean terminal utility of 682.053021. G34's improvement is observed on a repeatedly used development panel; no claim of statistical significance or fresh-history superiority follows. Failures and invalid proposals are represented only as statuses, never fabricated zero utilities.*

The family remains scheduled construction of dense, overlapping groups, followed by a return to the original rule. G31 recombines a known completion-aware handoff, G32 changes partner ranking, G33 restores a known cutoff, G34 rematches membership, and G35 changes which layer gets an addition opportunity. The most defensible conclusion is **local refinement with repeated behavioral rediscovery**. Source diversity and novelty admission overstate functional diversity in the two byte-identical trajectory rediscoveries. Their changed sources nevertheless required evaluation under the frozen exact-cache rules; no semantic-equivalence cache shortcut was introduced.

### Gains, exclusion and costs along the path

| Policy | Mean terminal utility | Terminal-loss observations | Isolated observations | Cumulative-loss observations |
|---|---:|---:|---:|---:|
| G5, initial construction reference | 681.168854 | 31 | 3 | 1,533 |
| G12, retained lower-harm alternative | 681.194757 | 5 | 3 | 1,500 |
| G26, prior objective winner | 682.053021 | 287 | 105 | 1,531 |
| G31 | 682.052778 | 289 | 96 | 1,550 |
| G32 | 682.050590 | 308 | 113 | 1,543 |
| G33 | 682.053021 | 287 | 105 | 1,531 |
| **G34, selected winner** | **682.060486** | **271** | **118** | **1,549** |
| G35 | 682.048576 | 310 | 107 | 1,586 |

Each policy has **11,520 dependent actor-case observations**, grouped into 288 conditions and 36 related-history families. “Loss” in this table means a paired effect below **−1e−9** versus the original; exact-sign counts remain in the JSON. Isolation means zero links on both layers. Cumulative utility sums saved end-of-round utilities through time 100 without discounting; it is not a terminal statistic or a separate optimized objective. Clustering assigns zero when undefined, with defined-only means separately retained in the JSON; overlap uses the analogous explicit zero convention. These choices must be consistent when comparing programs.

![Mean utility and actor losses](figures/utility-and-actor-losses.png)

*Historical G5/G12/G26 rows reuse the preserved generation-30 analysis; new rows use retained trajectory data only. G34's higher population mean does not dominate G12's markedly smaller terminal-loss and isolation counts. The frozen selection rule still chooses G34; the alternative is retained for scientific comparison.*

G34's 271 terminal losses comprise **171 directly shocked observations under adverse shocks** and **100 unshocked observations under favorable partial shocks**. None occurs in its high- or low-cost controls. Thus favorable shocks can exclude actors who did not receive the favorable cost change. These categories describe measured exposure, not motives, coercion or relative-gains preferences.

Higher absolute utility under shocks must also be separated from the shock penalty relative to a policy's own control. For the 13-of-40 adverse-shock condition, G34's mean shock-minus-control contrast is **−285.911111**, compared with **−29.459722** for the original. Large gains over the original do not establish attenuation of that adverse-shock penalty. Full matched contrasts, parameters and history IDs are retained in the final review JSON.

![Actor 34 through construction and cleanup](figures/actor34-construction-and-cleanup.png)

*This is the historically selected G26 worst terminal actor-loss example, not a prevalence estimate. At time 93 G26's actor 34 has degree 4/4, six triangles per layer and four overlapping ties; it is isolated from time 97. G34 ends with one overlapping partner and utility 2.8 versus original 6.0. Its cumulative effect remains −178.0. G12 ends at 6.4 but has cumulative effect −209.6. The curves establish ordering and outcomes, not which unrecorded action initiated the collapse, nor unchanged group membership between snapshots.*

The [three-network illustration](figures/generation35-network-example.svg) uses identical positions and actual retained time-100 adjacency. In this selected case, population means are original **12.700**, G26 **41.220** and G34 **41.140**: G34 improves actor 34's position while this case's population mean falls slightly. This is distinct from its positive average change across the full panel. Exact edge changes and image provenance are in the [figure receipt](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/assets/readme/generation35-network-example.json).

### What native ShinkaEvolve actually did

The [native mechanism audit](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/report/generation-35-review/native-mechanisms.json) binds receipts, log line numbers and database evidence. All five proposals use native parent/inspiration sampling, island assignment, mutation, admission and UCB reward updates. There are five portfolio selections, submissions and rewards, and five restores of the persistent bandit state across controller windows. Final arm counts are **13 Astra and 20 Sol completed programs**; these are rewarded-program counts, not total model-response counts. Mutation used Sol for G31/G33/G34 and Astra for G32/G35, always xhigh through the authorized ChatGPT-authenticated Headless 0.6.1 routes.

The retained population spans three islands. Final database row/correct counts are island 0 **10/10**, island 1 **12/11**, island 2 **14/14**; administrative copies are included in these database counts. The archive has **35 members**. No migration occurred during G31–35. Eight earlier migration moves at generations 10, 20 and 30 remain in the receipts. Conditional island spawning was enabled but did not trigger; no event was forced for reporting.

All five proposals used local source embeddings. Only G33 exceeded the 0.99 similarity threshold and triggered an Astra/xhigh novelty judgment. Its parent-only comparison admitted a program that reproduces G26's saved behavior, so this event cannot establish archive-wide behavioral novelty.

One ordinary native meta update completed after G31: the retained G22–30 buffer plus G31 supplied ten evaluated programs. It made twelve Astra/xhigh responses (ten individual summaries, scratchpad synthesis and recommendations). Buffer occupancy, not the decimal proposal number, explains the trigger. Native advice is visibly transmitted into subsequent proposals, with triangle priority, membership rematching and layer selection implemented. No controlled comparison identifies the meta mechanism's causal benefit.

The third native prompt evolution completed after G32. G31/G32 used `aab9b733-663b-48d2-8d3f-6885f152f239`; G33–35 used the new `b1b2c70d-9030-41be-a518-0bfcfd72a73c`. Four prompt rows remain: the initial prompt and three evolved prompts. At the drained boundary there is no active meta operation; **G32–35 remain in the pending four-program buffer**, with 30 programs processed across three completed updates. No extra call was forced to empty it. Research-team literature and interpretations were kept outside the frozen discovery context.

## Cooperation and emergence across substrates

The [integrated research memo](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/docs/paper_trajectory_v2/research_synthesis.md) reconciles three independent literature-and-code analyses and labels observations, interpretations, hypotheses and rival explanations. All actors execute locally, additions require bilateral acceptance, and exits are unilateral. Yet a common evolved policy, actor IDs, a public clock and a centralized evolutionary objective supply major coordination resources. The target cohort convention is explicitly programmed; realized ties, incomplete construction, segregation and collapse result from interactions. This is evolution of one policy deployed across all actors, **not cooperative coevolution of independently evolving actor populations**.

The connection to international cooperation is therefore conditional. Network formation without a superior executing authority, unequal exposure, partner choice and cross-layer dependence are defensible abstractions. It does not establish voluntary adoption of the policy, self-enforcing political commitments, strategic retaliation, asymmetric jurisdictional power or empirically calibrated Japanese partnerships. Nor does it verify structural realism. The memo connects these limits to primary work by Burghardt and Maoz, Axelrod and Keohane, Jackson and Wolinsky, Fearon, Snidal, Reynolds, and Farrell and Newman, retaining disagreements rather than treating repeated interpretations as independent confirmation.

## Checkpoint, scope and reproducibility

The controller and supervisor stopped at the same operational target **35** and drained accepted work. [Drain verification](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/search/operations/generation-35-drained-verification.json) records free campaign/supervisor locks, no active discovery processes, no proposal 36, and no unfinished accepted job. The native target count 36 includes seed 0; it is not permission for proposal 36. The supported target-change operation archived the matching generation-30 pause under lock; prior failed proposals and completed recoveries remain intact.

The consistent checkpoint is [programs-036.sqlite](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/search/checkpoints/programs-036.sqlite), with SHA256 `a9ea1ab968feb284d92d18c8191bb977086209cdf3968b88b73a517245935106` and full-record fingerprint `da9979f9be831520db19fc3672adc1bab9f8c6606c4aea26bd879685e2caab92`. Matching native state is [native-036](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/search/checkpoints/native-036). The manifest preserves population, lineage, islands, archive, bandit, meta memory, prompt database, usage and exact-case caches. The selected program is G34, native ID `76f5377c-4401-4d21-8dac-e4516aeedbae`.

| Accounting category | Added during G31–35 | Campaign total |
|---|---:|---:|
| Descendant proposal slots | 5 | 35 |
| Valid descendants | 5 | 32 |
| Native-returned research model responses | 19 | 76 |
| Observed logical completions including historical late G1 reply | 19 | 77 |
| Completed physical trajectories | 1,440 | 14,075 |
| Evaluator invocations | 5 | 38 |
| Exact-cache reuses | 0 | 495 |

The 19 new responses comprise five mutation, twelve meta, one novelty and one prompt-evolution response. Campaign totals comprise 34 mutation, 36 meta, three novelty and three prompt responses; the archived late G1 reply is separate. Historical accounting retains 86 attempts, six retries and nine local allowance denials. Completed numerical work is 4,559 reference trajectories, twelve operational benchmark trajectories, 288 independent seed trajectories and 9,216 descendant trajectories. One historical failed numerical attempt remains separately recorded. API-style cost estimates in the native viewer are accounting estimates, not evidence of a paid fallback; inference stayed on the authorized subscription routes.

The initial continuation preflight failed before G31 admission because the embedding service's manifest download timestamp differed. A focused operational wrapper proves that only `downloaded_at` changed, verifies all six model artifacts and the original operational embedding probe, and restores the frozen identity before the native runner. It changes neither scientific code nor encoder weights, routing or model effort. [Reconciliation](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/search/operations/embedding-metadata-reconciliation.json) and [focused checks](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/search/operations/embedding-metadata-focused-checks.json) document the repair. No original seed evaluation, deferred grid, fresh confirmation or ablation was launched.

The [analysis methods](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/scripts/analysis/README.md) document exclusive-output scripts and exact commands. The final review uses the drained database, verifies new case/cache identities, and reuses prior verified compact extracts; figures read saved JSON. It adds no simulation, model response or evaluator invocation. Full integer-time trajectories are inspected only for four fixed historical examples; no new panel-wide claim about the timing of troughs is made. First-render layout drafts are preserved separately. The [generation-30 review](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/docs/paper_trajectory_v2/generation30_review.md) is unchanged.

## Recommended next experiment — not executed

Keep discovery paused. Predeclare a **fresh, paired-history confirmation of G34, G12 and the original comparator**, evaluating terminal population utility together with actor losses, isolation, cumulative utility and shock-minus-own-control contrasts. Treat independent history families as the sampling units. This directly tests whether the small objective gain and the lower-harm alternative persist outside selection data. If the aim is specifically attribution to membership rematching, add parent G30 as a separate planned contrast; code comparisons alone cannot settle that mechanism.

A later small handoff diagnostic could test construction versus cleanup in the historical collapse case, but matched seeds do not guarantee identical endogenous random-draw consumption after programs diverge. Heterogeneous policy adoption, anonymous coordination, strategic coercion and empirical country networks are model extensions, not findings of this continuation. None is authorized or executed here. The remaining fifteen proposal slots await a separate decision; they are not an automatic next step.
