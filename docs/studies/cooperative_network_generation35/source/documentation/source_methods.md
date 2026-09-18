# Primary-source methods audit

Sources were retrieved and read on 2026-09-17: Burghardt and Maoz, *Partial shocks on cooperative multiplex networks with varying degrees of noise*, Scientific Reports 8, 13619 (2018), [DOI](https://doi.org/10.1038/s41598-018-31960-y); its actual five-page supplement; and the full nine-file source tree at [`b3d7737613578da260fee561b6f73122dc4f2ab0`](https://github.com/KeithBurghardt/MultiplexShockCode/tree/b3d7737613578da260fee561b6f73122dc4f2ab0). The downloaded bytes, hashes and extraction details are recorded in [source_provenance.json](source_provenance.json). This is a source audit, not evidence that a numerical result has been reproduced.

The subsequent [explicit user precedence decision](../experiments/paper_trajectory_v2/primary_reference_decision.json) selects the pinned `source_executable` behavior as primary and retains `paper_directed` as sensitivity. The [source-to-code mapping](source_behavior_mapping.md) records verified scheduling, noise invocation, sampling, acceptance and ordering, with the declared timing/shock overrides. Historical scheduler and production-seed uncertainty remain source limitations; under the hash-bound decision they do not indefinitely block this prospective methodological choice. Remaining executions, actual defects and separate unresolved analysis specifications are not waived.

## Parameters, timing and repetitions

The main paper fixes two undirected layers, N=40, b=1 and candidate search size m=10. Costs are .2 and .6; triangle reward d and overlap reward e each vary independently from0 to2. Report cost directions numerically: the Methods paragraph reverses the LH/HL labels when assigning the two costs, while subsequent interpretation consistently treats increasing cost as LH. The intended measurement times are pre-shock t=50 and terminal t=100, with the shock immediately after50. Figure2 explicitly uses p=0 and13/26/40 shocked actors. Figure3 shows p=0/.25/.50 and26 shocked; the text and Figure7 additionally use .75.

The retained Java `AgentsSimulation.main` has d,e in {0,.4,.8,1.2,1.6,2}, five runs per parameter combination, only p=.75 enabled, both pre/post costs, shock counts13/26/40, shock time200 and horizon400. Figure2/3 images visibly use six bins per reward axis, consistent with the six-point grid. Nevertheless, neither the article nor supplement explicitly states the reward step or simulation repetition count. Five repetitions and this grid are a **source-backed reconstruction choice**, not a verified published run manifest. Java comments also retain an alternative .1-step triangle grid; comments do not establish execution.

Supplement TableS1 has21,600 observations for each (LL or HH, noise) cell. The product40 actors ×36 reward cells ×5 repetitions ×3 nominal shock-count conditions equals21,600, consistent with the retained loops. This is an inference, not a reported decomposition. Its observations must not be treated as21,600 independent simulated histories. The source seeds each run from wall-clock milliseconds and stores no reproducible seed manifest in the repository.

## Dynamics and the executable discrepancy

The formal list in the main Methods and supplement supports a literal interpretation in which an episode selects one actor uniformly, then that same actor repeats the strategic step N times with probability1−p, each substep advancing time by1/N. Its noisy branch performs one rewiring step and advances time by1/N. The placement of actor selection outside the repeated list, repeated references to the same actor i, and the nested time increment support this reading. They do **not** establish that it was the authors' executed schedule: other prose and the pinned executable conflict with it. A strategic step compares doing nothing, adding, deleting, or swapping against immediate utility; additions require consent and deletion is unilateral. See the [independent source recheck](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/docs/paper_trajectory_v2/scheduling_source_recheck.md) for exact locators and the historical ambiguity.

This literal episode rule also changes the meaning of the nominal noise parameter. Its expected long-run fraction of **actions** taken through the noisy branch is `p / [N*(1−p)+p]`, whereas the shuffled source controller's fraction is p. For example, at p=.75 it is about.06977 for N40 and.02913 for N100 under the literal rule. Finite histories can differ because episodes are truncated. Comparisons between these interpretations therefore compare different schedules and effective noise exposure; a higher utility in one interpretation is not an evolved improvement. The N repeated activations also concentrate strategic opportunities in one actor instead of giving every actor one turn per round.

The retained `GamePlayerAgent.step` instead shuffles every actor and gives each exactly one move per scheduler round. Its swap search does not reset its deletion-layer counter for each new addition, and its final standalone deletion can follow a successful swap. These are separate from the intended utility equation. V2 retains an executable-source track and a separately named literal-prose sensitivity track; neither is asserted to recover an unavailable production manifest. Whether an episode continues across a shock, when time advances, and how the horizon truncates work must be explicit. The main text also describes p as the fraction of random moves, and the supplement's complexity discussion counts N agents per timestep plus an extra N repetitions near p=0. Those statements do not consistently resolve the nested algorithm. Historical scheduler/timing remains unresolved. The explicit user precedence decision resolves which behavior v2 uses as primary without asserting a recovered historical fact.

The supplement's smart search examines each existing neighbor: with equal probability it considers the missing opposite-layer tie, or a randomly chosen neighbor-of-that-neighbor that is not already connected to the focal actor. After exhausting neighbors, remaining candidate slots are filled randomly; swap additions use the same selection rule. It leaves layer aggregation, neighbor ordering, budget exhaustion when degree exceeds m, and empty friend-of-friend pools unspecified. These require disclosed v2 choices. In the source, `bestAddSmartSearch` instead loops friend-of-friend candidates in index order, decrements a mutable budget, and has a fallback that can replace a stored candidate's identity while retaining its prior gain. `bestSmartSearchAddDropCombo` retains the ordinary random search and deletion-counter issue. The active `GamePlayerAgent` calls ordinary search. Naming a dormant source method “smart” therefore does not establish fidelity to the supplement.

The later [smart-behavior review](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/docs/paper_trajectory_v2/smart_defect_review.md) clarifies the saved N40 stop: it is an adapter incompatibility, not demonstrated upstream failure. At the recorded p=0 self proposal the unchanged utility gain is zero, and original acceptance rejects without consuming RNG state; the caller can continue its subsequent deletion logic. At positive noise an accepted self proposal can create diagonal adjacency, which original utility excludes but full-matrix output/analysis can observe. A faithful source-smart reference therefore needs a separately versioned execution/measurement path; the current guard cannot simply be removed. All original receipts and completed supported tracks remain unchanged.

## Outcomes and Equations4–8

Let k_iℓ be degree in layer ℓ, z_iℓ the number of triangles containing actor i, and v_i the count of neighbors connected in both layers. The utility is

`u_i = e*v_i + Σ_ℓ [k_iℓ − c_i*k_iℓ² + d*z_iℓ]`.

The four requested statistics are total degree across layers, mean local clustering across layers, overlap fraction, and utility. The retained analysis uses local clustering `z_iℓ / choose(k_iℓ,2)` with0 for degree below2, then takes the mean of the two layers. Mean network clustering is the average over all actors, including these zeros; it is not transitivity. Degree is the sum of the two layer degrees. These conventions come from the original analysis code, whereas the main paper does not spell out every isolate convention.

Equation4: `resilience δ = 1 − (NS_pre − NS_post) / NS_LL`.

Equation5: `flexibility θ = (NS_post − NS_pre) / NS_LL`.

`NS_LL` is the average corresponding low-cost control statistic at t=50. Use an explicit matched control stratum (N, search/scheduler, d,e,p) and record its sample count. Matching details beyond “low-cost control” are a v2 choice. These metrics are not ratios of terminal high-cost and low-cost outcomes, and they can exceed1 or be negative. The paper does not define division when the LL statistic is zero; retain missing/undefined with the denominator and count, rather than inserting a favorable score. Utility denominators can also be near zero or negative and must be displayed.

Equation6: `spillover_i = 2*Σ_j(A_ij0*A_ij1) / Σ_j(A_ij0+A_ij1)`.

This weights an overlap pair as two of the actor's layer-edges. The original analysis assigns0 for isolated actors. The mean is a mean of actor fractions, not the ratio of total overlap to total network degree.

Equation7, fit separately for numeric cost directions, is

`NS_post,i = a + b1*NS_pre,i + b2*(shocked_i*p) + b3*p + b4*neighbor_exposure_i + b5*shocked_i + b6*e + b7*d + error_i`.

The utility outcome and corresponding pre-shock predictor use a cumulative distribution transformation `F(u_i)=P(u≤u_i)` across conditions and times. The main article concerns N40 random-search conditions; its pool must not change when a different scheduler, N100 or smart-search model is added. V2 therefore uses one pool per (scheduler interpretation, N, search method), spanning all of that method's conditions, actors and101 recorded times. Every pre/post value and shock subgroup within that method shares the same pool. The paper does not specify empirical tie handling, which retained times enter the pool, or a reusable evaluation reference pool; the supplement also leaves its cross-method pooling unspecified. Separate supplementary method pools are an explicit reconstruction, not recovered author metadata. Candidate-specific or shock-group-specific re-ranking would change the comparison and is excluded. Figure6 plots coefficients in the native scales of the outcomes (including degree coefficients of order tens), not a specified standardized coefficient system.

The paper calls the method mixed-effect OLS but Equation7 contains no random-effect term, grouping variable, random slopes, covariance estimator or fitting algorithm. Neither supplement nor pinned analysis supplies these details. The complete repository tree contains only simulation, parsing and nodal-metric code. A history-clustered OLS fit or a specified random-intercept model is therefore a disclosed reconstruction, not an exact replication of the unidentified estimator. Nodes within a simulated network cannot be counted as independent repetitions for uncertainty.

Equation8: `neighbor_exposure_i = Σ_(ℓ,j≠i) A_pre,ijℓ*shocked_j / Σ_(ℓ,j≠i) A_pre,ijℓ`.

The equation counts an overlapping neighbor twice. `NodalStatistics.py` instead thresholds the sum of the layers and counts **unique neighbors**, assigning0 to isolates. Preserve both columns and identify the paper-equation exposure as such; do not silently equate the two. The paper gives no isolate-exposure rule, so retaining the source's0 rule is an explicit choice.

## Figure-specific comparison targets

Figure2 is a six-by-six d/e heatmap set for all four metrics, both cost directions and the three shock counts with p=0. It needs the separate LL control at50. Figure3 is terminal utility over independent d/e and noise, with26 shocked. Its published color bar spans0–1, although its discussion describes utility and defines the CDF only later in the regression section. The Figure3 color transformation is unresolved; retain raw mean utility and label any common-CDF view separately.

Figure4 is a **three-actor, one-layer** high-cost example with b=1,c=.6 and no spillover contribution. Start with edge i−j and isolated k: utilities are(.4,.4,0). Adding j−k creates a path: the middle actor falls to−.4 while the two endpoints have.4. Closing i−k creates a triangle with utility d−.4 for every actor. The closure gain for its endpoints is d−.8. For d>.8 all actors exceed their initial utilities and the last tie is strictly attractive; the middle actor initially incurred the barrier cost. At d=.8 the gain is zero in exact arithmetic. The [actual unchanged-oracle fixture](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/docs/paper_trajectory_v2/figure4_fixture.json) records a positive binary residual of approximately1.11e−16, so the original strict `>` comparison can accept at the nominal threshold; no epsilon was added to change this behavior. The caption's .8 threshold is a sufficient Pareto/strict-closure threshold. Aggregate triangle utility exceeds the original edge already at d>2/3, a different comparison; do not substitute that threshold for the actual barrier test.

Figure5 displays examples at d=e=1.2,N40 and p=0/.25/.50/.75. The shown density/clustering pairs are(.076,.011),(.490,.698),(.499,.697),(.991,.991). Cost condition, shock count, displayed layer or union, observation time and random seed are not specified. Thus these are illustrative published values, not recoverable exact graph fixtures. V2 should record all those settings and select example histories by a rule fixed before seeing outcomes.

Figure6 compares the eight Equation7 coefficients for each of four outcomes and both cost directions. Figure7 stratifies the four nodal outcomes by shocked versus unshocked actors and noise with26 shocked. Its caption says errors are below marker size but does not identify the error-bar estimator. A v2 history-based interval is a transparent replacement, not a recovered original interval.

The supplement has the following distinct targets:

| Target | Actual source content |
|---|---|
| S1 | Utility resilience/flexibility for N40 random, N40 smart and N100 random; each panel has low/medium/high shock columns. Caption says26 shocked, inconsistent even with its N40 multiple shock columns and unclear for N100. FigureS3 explicitly gives33/66/100, but does not establish S1's actual counts. The frozen v2 use of Figure2/S3 grids is a declared reconstruction; S1 remains ambiguous. |
| S2 | All four Equation7 outcome fits, both cost directions, comparing those three N/search conditions; regression grouping remains unspecified. |
| S3 | All four resilience/flexibility metrics, N100,p0,33/66/100 shocked. |
| S4 | All four shocked/unshocked nodal outcomes, N100,66 shocked, noise grid. |
| TableS1 | No-shock utility drift t100−t50 for LL and HH, separated by noise. The table has21,600 nodal observations per cell. |

| Cost condition | p | Published mean drift | Published standard deviation | Published N |
|---|---:|---:|---:|---:|
| LL | 0 | 0 | 0 | 21,600 |
| LL | .25 | 66.39 | 254.73 | 21,600 |
| LL | .50 | 34.70 | 195.82 | 21,600 |
| LL | .75 | 11.93 | 96.63 | 21,600 |
| HH | 0 | 0 | 0 | 21,600 |
| HH | .25 | 8.08 | 29.98 | 21,600 |
| HH | .50 | 22.17 | 68.34 | 21,600 |
| HH | .75 | 40.62 | 131.95 | 21,600 |

The reported one-way ANOVA has F(3,86396)=655.13 for LL and1208.92 for HH. These are published reference values, not new v2 findings; reproducing them exactly requires recovering the unidentified original observations and analysis choices.

## Figure1 and data availability

Figure1 concerns empirical alliance and trade networks over1870–2010, separate from the simulation. The article defines a significant trade tie relative to .5% of a country's total imports plus exports and cites Maoz's *Networks of Nations*, the Correlates of War alliance work by Gibler/Sarkees and Gibler, and Barbieri/Keshk/Pollins trade data. The article does not provide an analysis-ready historical dataset or complete symmetrization/missingness recipe in its supplement or pinned code. The full Git tree proves those assets are absent there; it does not prove the historical datasets are unavailable elsewhere. Empirical reconstruction remains a separate unavailable-provenance item within this v2 source packet. Simulated results must not be presented as a reproduction of Figure1 or as a calibrated Japan model.
