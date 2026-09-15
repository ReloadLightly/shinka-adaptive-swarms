# Research plan: evolving adaptive collective search

## Objective

Reconstruct a documented multi-swarm particle swarm optimizer, use native ShinkaEvolve to evolve its adaptation program, and explain the resulting behavior in a changing search landscape. The first deliverable is a completed experiment with executable programs and evidence. Improvement is an empirical question.

## Scientific anchor

Blackwell, Branke and Li (2008), “Particle Swarms for Dynamic Optimization Problems,” pp.193–217 in Blum and Merkle’s *Swarm Intelligence: Introduction and Applications*, provides the case study. Section 4.2 explains multiple swarms, exclusion, convergence, adaptive swarm creation/removal and particle conversion after change. Sections 5.1–5.3 establish the Moving Peaks setup and the tested `(5+0)` variant.

DEAP commit `8a96fd3a75026f7b30e835f595a5199c75634ddf` supplies the later established implementation: `examples/pso/multiswarm.py` and `deap/benchmarks/movingpeaks.py`. The project reconstructs the chapter’s concepts using this code. It does not label a later implementation as the original authors’ software.

The baseline is five neutral particles per swarm, no permanent quantum particles, one desired free swarm (`NEXCESS=1`), and UVD conversion immediately after detected change. UVD means a uniform distribution over the volume of the specified search region. Any upstream conversion correction must be recorded in the implementation provenance and applied consistently to baseline and evolved comparisons.

## Research question and proposed explanation

Can program evolution produce an adaptation rule that tracks moving optima better than this baseline under the same objective-query budget?

A proposed explanation is that useful recovery after change depends on the optimizer’s observable state. A fixed response may disturb particles that still occupy useful regions, or relocate them too narrowly after a large displacement. An evolved response may improve that balance, or it may overfit a particular benchmark regime.

The initial interface is `choose_response(observation)` in `tasks/adaptive_swarm/initial.py`. It returns relocation radius scale, relocation fraction, memory handling (`reevaluate` or `reset`) and a velocity-reset flag. Observations include fitness deterioration, recent improvement, swarm diameter, swarm count, prior response information and remaining evaluations. Swarm creation and exclusion remain baseline mechanisms in this first experiment. Claims must follow this executed interface and observed code.

Three comparisons separate the relevant questions:

- **Reconstruction:** does the baseline implement the selected literature mechanisms and exhibit the corresponding search behavior?
- **Discovery:** does native ShinkaEvolve produce executable descendants with better search-set outcomes?
- **Generalization and explanation:** does the frozen selected program retain its advantage on independent cases, and does removing its proposed mechanism remove that advantage?

## Experimental units and information

The experimental unit for performance comparison is an independently generated landscape history paired with algorithm randomness. Baseline and challenger receive the same landscape history where feasible. Use separate random streams for landscape evolution and optimizer choices so a candidate’s use of randomness cannot alter the environmental changes it encounters.

The optimizer can use objective evaluations and the observations provided by its public state interface. Peak locations, the true optimum, future changes and reference answers are reserved for outcome measurement. Count all objective queries, including probes used for change detection and reevaluation, against each method’s budget.

Synthetic benchmark parameters are experimental controls, not measured properties of a real deployment. Keep this distinction in results and discussions.

## Reproduction scope

Use the chapter’s Scenario 2 settings as the reference: 5 dimensions, domain `[0,100]^5`, 10 peaks, heights `[30,70]`, widths `[1,12]`, a change every 5,000 evaluations, shift severity 1.0 and movement correlation 0. The book uses 500,000 evaluations per run and averages 50 independent runs.

Table 3 (p.211) reports offline error 1.80 with standard error 0.08 for `(5+0)`, `NEXCESS=1`. Report this separately from project results. The initial configuration uses three cases with paired environment/optimizer seeds `(101,1101)`, `(202,1202)` and `(303,1303)`, each at 500,000 evaluations. Exact table agreement is not a prerequisite for beginning evolution. Resolve implementation differences that would invalidate the intended comparison, then proceed.

The pinned DEAP source's movement severity is 1.0; a stale description referring to 1.5 must not override the source. Its default movement correlation is 0.5, whereas the book uses 0.0. Set the reconstruction correlation explicitly to 0.0 and retain the source-versus-configuration distinction in the provenance.

Record deviations in change timing, boundary handling, random streams, memory updates, UVD conversion and budget accounting. Distinguish a source correction from a scientific extension. Keep the corrected baseline fixed for the relevant comparison.

## Native program evolution

Use ShinkaEvolve’s own run, database, island archive, parent/inspiration selection, mutation and evaluation workflow. The initial configuration disables embedding novelty checks, meta-recommendations and prompt evolution and enables measured text feedback. Supply the chapter-derived mechanism description, the baseline program and measured feedback as context. Use the native Headless route to the authenticated Codex subscription. Do not substitute API calls or a separately invented mutation loop.

The initial requested search has 20 native generation slots, including one seed and up to 19 descendant slots. This is a changeable first experiment, not a mandatory threshold or claim of adequate statistical power. Proceed from the already executed baseline to real model-generated descendants. Retain candidate source, ancestry, explanations, evaluation outcomes and failure information as they occur. Seed copies placed on other islands are not additional evaluated programs.

Keep the scalar selection score aligned with offline error and show the actual measurement beside it. Preserve additional observations that make behavior interpretable, such as error after each change, number of swarms and evaluation allocation. A numerical gain becomes a research finding only after its conditions and program mechanism are examined.

## Independent comparison

Freeze the selected program before opening the reserved comparison cases. Compare it with the unchanged baseline at matched objective-query budgets. Start with new seeds in the reference regime, then use targeted shifts in change severity, change frequency or landscape complexity to examine the discovered mechanism. Name the actual tested shifts in the report.

The primary effect is paired offline-error difference, with the sign stated explicitly. Retain per-case values and report uncertainty across independent cases. Describe the number of completed cases and any missing cases. Do not treat different checkpoints of one trajectory as independent replications.

If evolution improves its search score but not the independent comparison, report that result directly. Further work should answer the observed failure mode rather than start a larger unmotivated sweep.

## Mechanism analysis

Inspect the selected source and trajectories before choosing an ablation. For an adaptive threshold, compare with a frozen threshold; for conditional diversification, disable that condition; for a state-dependent recovery rule, replace it with the baseline rule. Use the same cases and budget for the full program and its ablation.

Ablate only mechanisms present in the program. The aim is to determine why the evolved strategy behaves differently, not to accumulate experiment variants. A tuned baseline comparison is appropriate if the apparent discovery could be explained by a simple constant change.

## Reporting and completion

The report should contain the literature-to-code mapping, actual completed experiment counts, selected program, search lineage, paired outcomes, interpretable figures, mechanism analysis and limitations. Record a null or mixed result with the same detail as a gain.

Save results incrementally. Continue valid existing runs rather than recreate them. Long stages emit a meaningful status heartbeat every 15–30 seconds, and the native WebUI points to the active archive. Do not introduce arbitrary host-memory reserves or unrelated preflight work. Actual failures receive a bounded diagnosis and recovery; disclose a persistent external blocker with its saved progress.

After the authorized experiment, update README, figures and repository description, commit the resulting work, push it and verify the remote commit. Do not report planned steps as completed.
