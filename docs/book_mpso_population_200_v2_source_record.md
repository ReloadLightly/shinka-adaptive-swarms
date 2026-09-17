# Versioned source-fidelity continuation: enclosing-ball convergence

This record supplements, and does not replace or rehash,
[the original frozen source record](book_mpso_source_record.md).
Source: Blackwell, Branke and Li (2008), “Particle Swarms for Dynamic Optimization
Problems,” printed pp. 193–217, DOI
[10.1007/978-3-540-74089-6_6](https://doi.org/10.1007/978-3-540-74089-6_6).
The available local author copy was inspected; the copyrighted PDF is not committed.
[Author copy](https://titan.csit.rmit.edu.au/~e46507/publications/si-chaper-dynamic-blackwell-li.pdf).

Printed p. 201 defines convergence through the smallest enclosing circle/ball of
neutral positions. The historical engine used maximum pairwise distance <= twice
radius, a documented approximation. An equilateral triangle of side 1.9*r in five
dimensions passes that test while its enclosing radius 1.9*r/sqrt(3) exceeds r.
Changing neutral counts can interact with this discrepancy. Historical sources and
scores remain unchanged and are explicitly incompatible with corrected controls.

The versioned `book_population_v2.py` instead calls `enclosing_ball_converged`.
Pair distances provide a valid rejection certificate; a farthest-pair midpoint or
centroid ball enclosing all points provides a valid acceptance certificate.
Ambiguous clouds use affine support systems (at most dimension+1 support points)
and valid upper/dual lower certificates, stopping when decisive. Finite supports
are not enumerated on every update. Coordinates are translated and normalized by
the tested radius; binary64 relative radius tolerance is 1e-12 with inclusive
boundary comparison. Affinely dependent supports are skipped via NumPy's standard
SVD rank cutoff. The exact zero-radius case requires coincident represented points.
Boundary roundoff, including information already lost under huge translations,
cannot be undone. Geometry consumes neither objective queries nor RNG draws.
`neutral_diameter` remains maximum pairwise neutral distance as a public observation.

The source anchors otherwise remain: pp. 202–204 adaptive swarm birth/removal,
nexcess=1, exclusion radius X/(2*M**(1/d)), counted detection and memory refresh,
and exclusion after each subswarm update; p. 203 one detected-update temporary
quantum response for all neutrals; pp. 210–211/Table 3 support one permanent quantum
role; pp. 208–209 Scenario 2 with five dimensions, 5,000-query changes, offline
error and 500,000 queries per run. Printed p. 214/Table 6 explicitly includes 200
peaks/severity one: its MPSO score **2.18** conflicts with **2.12** in adjacent prose.
Neither is an exact reproduction target. The decisive comparison uses the same
corrected contemporary engine, paired environments and counted budget.

Printed p. 215 proposes adapting particles within MPSO subswarms as future work.
Our 2..8 target action, start-at-five births and one-step change-only resizing are
extension choices, not claimed author algorithms. The permanent quantum particle,
known-scale radius (0.5 times configured severity), retained velocities, PSO/UVD,
personal/shared memories, exclusion and birth/removal remain fixed. This campaign
is a small MPSO extension in one condition, not a full chapter reproduction or SPSO
comparison. The new scientific fingerprint and task/evaluation identity prevent
reuse of the historical one-case trajectory as a corrected reference.
