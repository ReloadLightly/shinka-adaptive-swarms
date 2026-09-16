# Chapter-to-implementation record: MPSO schedule v1

**Read before research outcomes, 16 September 2026.** Source: Tim Blackwell,
Jürgen Branke and Xiaodong Li, *Particle Swarms for Dynamic Optimization Problems*,
in *Swarm Intelligence: Introduction and Applications* (2008), printed pp.193–217.
[DOI](https://doi.org/10.1007/978-3-540-74089-6_6) ·
[author-hosted chapter](https://titan.csit.rmit.edu.au/~e46507/publications/si-chaper-dynamic-blackwell-li.pdf).
The author PDF has25 pages, SHA256
`d41837baac988e5a18c7fbb424e294de3dafaf61047184805b556bc84eece368`.
It was read from temporary local storage and is excluded from publication.

## Source anchors and shared implementation

| Source | Implemented mechanism |
|---|---|
| §4.1, p.199 | Gaussian direction normalized to a unit vector; radius times U^(1/d) gives uniform-volume sampling. Quantum movement replaces ordinary PSO. |
| §4.2, pp.201–204; Algorithm3 | Counted shared-best check; refresh every personal memory on observed change; asynchronous attractor updates; immediate exclusion after each subswarm update. |
| §4.2, pp.202–203 | Dynamic swarm count, one initial swarm, nexcess1; radius X/(2 M^(1/d)); cloud radius half movement severity. |
| §5.1, pp.208–209 | Five-dimensional, ten-peak Scenario2, severity1, period5000, correlation0; offline error integrates best error since each environmental change. |
| §5.3, Table3, pp.209–211 | Five neutral roles; zero/one permanent quantum role; neutral conversion lasts the detected-change update. |

Historical Table3, nexcess1: **5+0:1.80(SE0.08); 5+1:1.73(SE0.08)**,
50 runs of500,000 evaluations. Other excess settings and SPSO are also studied.
These numbers are context, not calibration targets or matched contemporary controls.

## Prospective reconstruction conventions

The implementation is `src/adaptive_swarms/book_mpso.py`; the old simulator remains
unchanged. Both new references and every evolved program use all conventions below.
They are fixed before observing whether the historical ranking appears.

- **Roles and order.** Neutral indices0–4 are structural identities; permanent
  quantum index5 follows them. Updates use current asynchronous shared best.
  A temporary quantum update preserves neutral velocity for later ordinary PSO.
  All particles, including the permanent quantum role, retain personal memories
  and participate in refresh and shared-best discovery.
- **Exclusion.** After each subswarm update, compare it against other swarms in
  list order. Immediately replace and initialize the weaker one; ties replace
  the currently processed swarm. Continue comparisons with the replacement.
  Reinitializing a later list entry does not remove its later scheduled update.
  The historical simulator instead excludes after the whole swarm-update sweep.
- **Birth and convergence.** New swarms receive immediate counted initialization.
  Radius is computed before birth/removal in each outer iteration. Convergence
  uses only designated neutral positions, with maximum Euclidean pairwise
  distance at most twice the exclusion radius. This retains the DEAP geometry
  approximation; it is not an exact smallest-enclosing-ball calculation. A
  permanent quantum particle never enters this convergence measurement.
- **Numerics.** Reuse pristine pinned DEAP MovingPeaks, revision
  `8a96fd3a75026f7b30e835f595a5199c75634ddf`, conical Scenario2. Heights initialize
  at50; widths and peak locations are sampled, with ranges[30,70] and[1,12],
  height/width change severities7/1. This initialization is declared rather than
  claimed to reconstruct unknown historical seeds. PSO chi0.729843788 and c2.05
  retain the existing precision convention. Initial velocities are uniform in
  [-50,50] per coordinate. Particle positions are not clipped; peaks reflect.
- **Timing and budget.** Environment moves after its boundary evaluation;
  detection is the next changed counted best-point check, never an oracle flag.
  Changes can occur within memory refresh/update. Stop at exactly500,000 queries,
  retaining incomplete final updates. Initialization, detection, memory, ordinary,
  temporary/permanent quantum and exclusion queries share that budget.
- **Subset randomness.** A dedicated task RNG derived from optimizer seed by the
  documented engine SHA256 rule generates a full permutation of five neutral
  indices every update regardless of k. First k convert; movement and landscape
  RNGs are separate. Pairing guarantees identical environments, not identical
  optimizer perturbations after schedules diverge.

## Search boundary

Shinka changes only the integer temporary-conversion count on each update in
5+1. It cannot alter permanent role count, radius, PSO, memory, topology,
exclusion or budgets. The seed implements the same schedule as standalone5+1,
with exact compatible evaluation reuse. Public observations derive from counted
optimizer information; the chapter's known environmental scale supplies the
radius. No hidden optimum, peak position, future change or evaluation error is
available to programs. Pure mathematical expressions and function-local math
imports are allowed; external access and randomness are not.

This is a chapter-aligned reconstruction and matched comparison with eight
repetitions, not an exact numerical reproduction of Table3. Fixing the previous
absence of permanent quantum particles and chapter ordering is reference work,
not an evolutionary discovery. Earlier studies retain their original execution
and conclusions.
