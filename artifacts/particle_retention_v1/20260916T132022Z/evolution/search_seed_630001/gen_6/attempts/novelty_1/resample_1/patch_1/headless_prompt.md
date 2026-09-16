# System Instructions

Evolve only retention_priority(particle_features, swarm_features) inside the marked
block. Return a finite Python int/float, not bool. The same pure deterministic
function scores each of five particles from one immutable snapshot after all
existing personal-best reevaluations and before any particle moves. Highest score
exempts one particle; the other four relocate. A dedicated recorded random
permutation resolves ties, generated once at EVERY selection regardless of ties.
A constant score therefore gives the random-reference strategy. Do not use random
numbers, mutable globals, files, environment variables, clocks or external code.

Fixed: four of five relocate; radius_scale=1.25; velocities retained; personal-best
memories reevaluated; numerical PSO, landscapes, birth/removal/exclusion and budgets
unchanged. All memories survive including relocated particles' memories. The
exempted particle continues ordinary PSO movement; it does not stay stationary and
is not a permanent leader. No other decision is evolvable.

Particle features, all captured before movement:
- personal_best_fitness: latest counted reevaluation of this remembered best;
  higher is better. NOT current-position fitness.
- personal_best_rank: 1 + number of strictly better refreshed personal bests;
  1 is best,5 is worst; equal qualities have equal competition rank.
- personal_best_rank_fraction: (rank-1)/4,0 best to1 worst.
- distance_to_best: Euclidean current-position distance to refreshed swarm-best
  position; distance_to_best_normalized divides by max(default_radius,1e-12).
- speed: Euclidean velocity norm; speed_normalized divides by the same scale.
- velocity_alignment: cosine between velocity and vector from current position
  toward refreshed swarm-best position; +1toward,-1away,0if either norm is zero.
- relative_position_normalized: current position minus refreshed best, component
  tuple divided by that scale; velocity_normalized: velocity components/scale.
Swarm features: dimension,swarm_size,default_radius,diameter,diameter_normalized,
relative_fitness_drop,mean_speed_normalized. Diameter is maximum pairwise current
particle distance; normalized values divide by max(default_radius,1e-12).
relative_fitness_drop is the existing public best-point detection statistic.
The default radius is half the CONFIGURED movement severity supplied by the
benchmark. This experiment does not infer unknown severity.

No particle identity/index, RNG seed, hidden peak, true optimum, future change or
objective error is a predictive feature. Do not import simulator/evaluator code.
Pure math is permitted. Constants and simple rules are legitimate; there is no
bonus for complexity, branching or agreement with a preferred hypothesis.

Fitness=1/(1+mean offline error) over eight fixed balanced DEVELOPMENT cases,
100,000 counted queries each. All detection and memory queries count. Feedback
includes paired differences versus random and strongest-refreshed-personal-best
references, regimes, chosen characteristics, agreement with that heuristic on the
same snapshot and favorable/unfavorable measured recovery episodes. Cases remain
development data; no generalization or search-method-superiority claim follows.


# Scientific context supplied to mutation

# Scientific context: allocating trajectory continuity

The preceding radius/velocity sprint selected fixedcount4,radius1.25,retained
velocity. Its fresh8-case pilot versus corrected count5/radius1baseline had mean
error difference−0.6303,descriptive95%interval[−1.4721,+0.2241],fourwins/fourlosses,
with a large individual baseline loss influencing the mean. Conditional recovery
and velocity-mediated overshoot remain unestablished. V3 likewise did not establish
fresh-history superiority or useful current-state dependence.

Here the narrow question is which one particle should CONTINUE ordinary PSO when
the other four relocate after a detected change. All personal-best memories are
preserved and reevaluated, so this is not a test of saving otherwise-erased memories.
Strong refreshed personal-best quality might identify a useful trajectory, but
current position, velocity and refreshed memory can point in different directions.
Geometry, direction, speed and continuity/diversity tradeoffs are plausible; changed
asynchronous attractor updates and stochastic complete trajectories are competing
explanations. A complicated expression alone is not a collective mechanism.

The initial program exempts the particle with the strongest refreshed personal best.
The external random reference gives equal priorities under the same per-selection
random tie permutation. Both use the new selection-RNG arrangement; historical
random-policy outcomes are not substituted. Only retention priorities evolve.
The benchmark supplies default_radius=0.5*configuredmovementseverity. Unknown-shock
or unknown-severity adaptation is outside this study. No additional campaign or
fresh validation automatically follows this bounded search.

A landscape change can occur during sequential memory refresh. Features report
the latest actual counted reevaluations, not oracle-synchronized current fitnesses.

# Measured reference feedback before native descendants

On these same eight development cases, random mean offline error is 3.722188;
the strongest-refreshed-personal-best heuristic mean is 3.901685.
Heuristic minus random is +0.179497, paired SD 0.575626;
2/8 cases favor the heuristic. Individual paired effects in fixed case order:
[0.08711296308851235, 0.26234381766249326, -0.8640523282206134, 1.005068018856809, 0.19099570316085135, -0.10475598318152501, 0.8342248521209767, 0.025036589168600187]. These are development observations, not fresh validation.
Native initial feedback supplies the complete paired outcomes and measured behavior.


# Potential Recommendations
The following are potential recommendations for the next program generation:

**Compress individual geometric penalties.** Try `1/(1 + d**0.5 + v**0.5)`, then variants compressing only distance or only speed. These retain the best program’s preference for proximity and low speed while testing whether large feature magnitudes exert excessive influence; unlike transforming the complete `d + v` sum, they can change particle rankings.
You MUST respond using an edit name, description, and the exact SEARCH/REPLACE diff format shown below to indicate changes:

<NAME>
A shortened name summarizing the edit you are proposing. Lowercase, no spaces, underscores allowed.
</NAME>

<DESCRIPTION>
A description and argumentation process of the edit you are proposing.
</DESCRIPTION>

<DIFF>
<<<<<<< SEARCH
# Original code to find and replace (must match exactly including indentation)
=======
# New replacement code
>>>>>>> REPLACE

</DIFF>


Example of a valid diff format:
<DIFF>
<<<<<<< SEARCH
for i in range(m):
    for j in range(p):
        for k in range(n):
            C[i, j] += A[i, k] * B[k, j]
=======
# Reorder loops for better memory access pattern
for i in range(m):
    for k in range(n):
        for j in range(p):
            C[i, j] += A[i, k] * B[k, j]
>>>>>>> REPLACE

</DIFF>

* You may only modify text that lies below a line containing "EVOLVE-BLOCK-START" and above the next "EVOLVE-BLOCK-END". Everything outside those markers is read-only.
* Do not repeat the markers "EVOLVE-BLOCK-START" and "EVOLVE-BLOCK-END" in the SEARCH/REPLACE blocks.  
* Every block’s SEARCH section must be copied **verbatim** from the current file, including indentation.
* You can propose multiple independent edits. SEARCH/REPLACE blocks follow one after another. DO NOT ADD ANY OTHER TEXT BETWEEN THESE BLOCKS.
* Make sure the file still runs after your changes.

# Previous Messages

[]

# User Request

Here are the performance metrics of a set of previously implemented programs:

# Prior programs

```python
"""Retain the strongest refreshed personal-best particle for ordinary PSO."""

# EVOLVE-BLOCK-START
def retention_priority(particle_features, swarm_features) -> float:
    return -particle_features["personal_best_rank"]
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.20
mean_offline_error: 3.90; worst_case_offline_error: 5.47; case_error_std: 1.13; cases_completed: 8

Text feedback:
Development feedback only. Lower offline error is better; fitness=1/(1+mean error). Paired differences are candidate minus comparator (negative is better). Random reference is random; heuristic seed is heuristic. All personal-best memories survive and are reevaluated. The exempted particle continues ordinary PSO; it is neither stationary nor a permanent leader. Choices change complete closed-loop trajectories. Agreement is measured against the heuristic on each candidate snapshot, not across reference trajectories.
case_000 severity=1.0,period=2500: error=4.120103, delta random=+0.087113, delta heuristic=+0.000000; heuristic agreements=240/240; selected ranks={'1': 240}; selected feature means={'personal_best_rank': 1, 'distance_to_best_normalized': 9.760753831402312, 'speed_normalized': 17.33525409986445, 'velocity_alignment': -0.4410162116932311}; interval-end error=3.142434508164019; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 3.977814299497103, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 3.977814299497103}, "most_unfavorable": {"candidate_environment_error": 3.977814299497103, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 3.977814299497103}}
case_001 severity=1.0,period=2500: error=2.652032, delta random=+0.262344, delta heuristic=+0.000000; heuristic agreements=260/260; selected ranks={'1': 260}; selected feature means={'personal_best_rank': 1, 'distance_to_best_normalized': 8.65863443686278, 'speed_normalized': 18.317980649449737, 'velocity_alignment': -0.4719908653630618}; interval-end error=1.6864361745599443; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 14.659259620251337, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 14.659259620251337}, "most_unfavorable": {"candidate_environment_error": 14.659259620251337, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 14.659259620251337}}
case_002 severity=1.0,period=5000: error=2.497580, delta random=-0.864052, delta heuristic=+0.000000; heuristic agreements=117/117; selected ranks={'1': 117}; selected feature means={'personal_best_rank': 1, 'distance_to_best_normalized': 6.145555819356218, 'speed_normalized': 16.42569422132051, 'velocity_alignment': -0.3931824725100938}; interval-end error=1.757100843137016; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 0.35446592495787405, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 0.35446592495787405}, "most_unfavorable": {"candidate_environment_error": 0.35446592495787405, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 0.35446592495787405}}
case_003 severity=1.0,period=5000: error=5.299676, delta random=+1.005068, delta heuristic=+0.000000; heuristic agreements=86/86; selected ranks={'1': 86}; selected feature means={'personal_best_rank': 1, 'distance_to_best_normalized': 10.182017785468956, 'speed_normalized': 22.720648272991355, 'velocity_alignment': -0.39746589663149773}; interval-end error=4.357535466754301; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 6.3578355597089855, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 6.3578355597089855}, "most_unfavorable": {"candidate_environment_error": 6.3578355597089855, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 6.3578355597089855}}
case_004 severity=3.0,period=2500: error=5.473700, delta random=+0.190996, delta heuristic=+0.000000; heuristic agreements=206/206; selected ranks={'1': 206}; selected feature means={'personal_best_rank': 1, 'distance_to_best_normalized': 4.466672427032202, 'speed_normalized': 7.726416605237953, 'velocity_alignment': -0.491286368969343}; interval-end error=3.8943881127244664; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 8.890634693906259, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 8.890634693906259}, "most_unfavorable": {"candidate_environment_error": 8.890634693906259, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 8.890634693906259}}
case_005 severity=3.0,period=2500: error=3.720148, delta random=-0.104756, delta heuristic=+0.000000; heuristic agreements=342/342; selected ranks={'1': 342}; selected feature means={'personal_best_rank': 1, 'distance_to_best_normalized': 2.1856582062814094, 'speed_normalized': 4.818924543584261, 'velocity_alignment': -0.41159572788131465}; interval-end error=1.1337059262609572; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 8.611016439957822, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 8.611016439957822}, "most_unfavorable": {"candidate_environment_error": 8.611016439957822, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 8.611016439957822}}
case_006 severity=3.0,period=5000: error=3.095942, delta random=+0.834225, delta heuristic=+0.000000; heuristic agreements=126/126; selected ranks={'1': 126}; selected feature means={'personal_best_rank': 1, 'distance_to_best_normalized': 3.16796971023856, 'speed_normalized': 4.550967572891807, 'velocity_alignment': -0.49511882791792555}; interval-end error=1.747914590888642; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 3.5729459767192653, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 3.5729459767192653}, "most_unfavorable": {"candidate_environment_error": 3.5729459767192653, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 3.5729459767192653}}
case_007 severity=3.0,period=5000: error=4.354300, delta random=+0.025037, delta heuristic=+0.000000; heuristic agreements=90/90; selected ranks={'1': 90}; selected feature means={'personal_best_rank': 1, 'distance_to_best_normalized': 4.666959098179327, 'speed_normalized': 6.966568142120525, 'velocity_alignment': -0.46751769748937483}; interval-end error=3.5157704285620577; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 18.294987670245487, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 18.294987670245487}, "most_unfavorable": {"candidate_environment_error": 18.294987670245487, "completed_environment": 1, "difference": 0.0, "reference_environment_error": 18.294987670245487}}
Paired regime summary: {"cases": 2, "mean_offline_error": 3.38606776281405, "random_difference_sd": 0.12390692554237565, "random_mean_difference": 0.1747283903755028, "regime": "severity=1.0,period=2500", "seed_difference_sd": 0.0, "seed_mean_difference": 0.0}
Paired regime summary: {"cases": 2, "mean_offline_error": 3.898627734526179, "random_difference_sd": 1.3216676722721987, "random_mean_difference": 0.07050784531809784, "regime": "severity=1.0,period=5000", "seed_difference_sd": 0.0, "seed_mean_difference": 0.0}
Paired regime summary: {"cases": 2, "mean_offline_error": 4.596924146208887, "random_difference_sd": 0.20912802296005115, "random_mean_difference": 0.04311985998966317, "regime": "severity=3.0,period=2500", "seed_difference_sd": 0.0, "seed_mean_difference": 0.0}
Paired regime summary: {"cases": 2, "mean_offline_error": 3.7251211318087587, "random_difference_sd": 0.5721825079901887, "random_mean_difference": 0.42963072064478847, "regime": "severity=3.0,period=5000", "seed_difference_sd": 0.0, "seed_mean_difference": 0.0}
Exactly four of five particles relocate at radius1.25 with retained velocities and fixed memory reevaluation. Only the per-particle retention priority evolves. Simple rules and constants are legitimate. Competing explanations include trajectory continuity, geometric diversity, later asynchronous attractor updates, query allocation and stochastic closed-loop variation. No fresh validation is planned in this bounded development experiment.

```python
"""Retain the strongest refreshed personal-best particle for ordinary PSO."""

# EVOLVE-BLOCK-START
def retention_priority(particle_features, swarm_features) -> float:
    """Assign equal priorities; the existing tie permutation selects exemption."""
    return 0.0
# EVOLVE-BLOCK-END

```

Performance metrics:
Combined score to maximize: 0.21
mean_offline_error: 3.72; worst_case_offline_error: 5.28; case_error_std: 1.02; cases_completed: 8

Text feedback:
Development feedback only. Lower offline error is better; fitness=1/(1+mean error). Paired differences are candidate minus comparator (negative is better). Random reference is random; heuristic seed is heuristic. All personal-best memories survive and are reevaluated. The exempted particle continues ordinary PSO; it is neither stationary nor a permanent leader. Choices change complete closed-loop trajectories. Agreement is measured against the heuristic on each candidate snapshot, not across reference trajectories.
case_000 severity=1.0,period=2500: error=4.032990, delta random=+0.000000, delta heuristic=-0.087113; heuristic agreements=47/248; selected ranks={'4': 49, '5': 58, '1': 47, '2': 58, '3': 36}; selected feature means={'personal_best_rank': 3.0524193548387095, 'distance_to_best_normalized': 18.779125049643113, 'speed_normalized': 18.830631278323388, 'velocity_alignment': -0.3770456212029959}; interval-end error=3.1231357599972953; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 8.22776295907268, "completed_environment": 7, "difference": -1.3832101330280544, "reference_environment_error": 9.610973092100734}, "most_unfavorable": {"candidate_environment_error": 1.3893913077758264, "completed_environment": 18, "difference": 0.720886972840931, "reference_environment_error": 0.6685043349348955}}
case_001 severity=1.0,period=2500: error=2.389689, delta random=+0.000000, delta heuristic=-0.262344; heuristic agreements=61/274; selected ranks={'2': 57, '3': 47, '4': 62, '1': 61, '5': 47}; selected feature means={'personal_best_rank': 2.9160583941605838, 'distance_to_best_normalized': 16.391350537170837, 'speed_normalized': 16.905873934624505, 'velocity_alignment': -0.39545852913985763}; interval-end error=1.4052287636320706; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 1.1524065893668152, "completed_environment": 4, "difference": -5.597827291766531, "reference_environment_error": 6.7502338811333455}, "most_unfavorable": {"candidate_environment_error": 4.149373528716931, "completed_environment": 39, "difference": 1.9180334838249666, "reference_environment_error": 2.2313400448919647}}
case_002 severity=1.0,period=5000: error=3.361632, delta random=+0.000000, delta heuristic=+0.864052; heuristic agreements=21/107; selected ranks={'3': 22, '2': 20, '1': 21, '4': 20, '5': 24}; selected feature means={'personal_best_rank': 3.05607476635514, 'distance_to_best_normalized': 21.938264561409817, 'speed_normalized': 20.592771680548623, 'velocity_alignment': -0.3928981716541631}; interval-end error=2.8682866124888164; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 1.1754325513502384, "completed_environment": 7, "difference": -1.871235404897565, "reference_environment_error": 3.0466679562478034}, "most_unfavorable": {"candidate_environment_error": 8.415187197893196, "completed_environment": 19, "difference": 7.529656567842313, "reference_environment_error": 0.8855306300508833}}
case_003 severity=1.0,period=5000: error=4.294608, delta random=+0.000000, delta heuristic=-1.005068; heuristic agreements=22/89; selected ranks={'1': 22, '5': 19, '4': 12, '2': 17, '3': 19}; selected feature means={'personal_best_rank': 2.8764044943820224, 'distance_to_best_normalized': 34.22226894690194, 'speed_normalized': 28.313473838490346, 'velocity_alignment': -0.3589918125895899}; interval-end error=3.1615665071006878; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 11.723575686833533, "completed_environment": 12, "difference": -9.265296024208512, "reference_environment_error": 20.988871711042044}, "most_unfavorable": {"candidate_environment_error": 0.8637983793438447, "completed_environment": 17, "difference": 0.4851676289555376, "reference_environment_error": 0.3786307503883071}}
case_004 severity=3.0,period=2500: error=5.282704, delta random=+0.000000, delta heuristic=-0.190996; heuristic agreements=41/237; selected ranks={'3': 53, '2': 57, '4': 48, '1': 41, '5': 38}; selected feature means={'personal_best_rank': 2.9367088607594938, 'distance_to_best_normalized': 6.764120951387236, 'speed_normalized': 7.268161626191005, 'velocity_alignment': -0.3614904094413995}; interval-end error=3.627904279795636; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 2.144805256455358, "completed_environment": 28, "difference": -7.167583239001402, "reference_environment_error": 9.31238849545676}, "most_unfavorable": {"candidate_environment_error": 8.385385622694493, "completed_environment": 33, "difference": 2.2443655882555253, "reference_environment_error": 6.141020034438967}}
case_005 severity=3.0,period=2500: error=3.824904, delta random=+0.000000, delta heuristic=+0.104756; heuristic agreements=83/349; selected ranks={'1': 83, '5': 82, '2': 57, '4': 63, '3': 64}; selected feature means={'personal_best_rank': 3.011461318051576, 'distance_to_best_normalized': 5.274637358921803, 'speed_normalized': 5.374986686234252, 'velocity_alignment': -0.3874908545689548}; interval-end error=1.192356201318899; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 2.504573588349162, "completed_environment": 13, "difference": -2.0178159371302957, "reference_environment_error": 4.522389525479458}, "most_unfavorable": {"candidate_environment_error": 10.34426862155463, "completed_environment": 3, "difference": 1.9319439312359687, "reference_environment_error": 8.41232469031866}}
case_006 severity=3.0,period=5000: error=2.261717, delta random=+0.000000, delta heuristic=-0.834225; heuristic agreements=18/115; selected ranks={'4': 27, '5': 24, '2': 29, '1': 18, '3': 17}; selected feature means={'personal_best_rank': 3.0869565217391304, 'distance_to_best_normalized': 6.972361271835961, 'speed_normalized': 6.929263215960519, 'velocity_alignment': -0.32652295998494324}; interval-end error=0.7854737942965222; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 1.0249671226165928, "completed_environment": 11, "difference": -13.095536836889782, "reference_environment_error": 14.120503959506374}, "most_unfavorable": {"candidate_environment_error": 2.82943825365175, "completed_environment": 14, "difference": 2.3470894356460805, "reference_environment_error": 0.48234881800566964}}
case_007 severity=3.0,period=5000: error=4.329264, delta random=+0.000000, delta heuristic=-0.025037; heuristic agreements=22/101; selected ranks={'1': 22, '4': 19, '3': 25, '5': 19, '2': 16}; selected feature means={'personal_best_rank': 2.9702970297029703, 'distance_to_best_normalized': 8.66346122996612, 'speed_normalized': 8.568664063517858, 'velocity_alignment': -0.34232052310690614}; interval-end error=3.5175357067889323; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 0.7353499952247763, "completed_environment": 19, "difference": -0.94769804471943, "reference_environment_error": 1.6830480399442063}, "most_unfavorable": {"candidate_environment_error": 1.1462893465517863, "completed_environment": 10, "difference": 0.5355715159440975, "reference_environment_error": 0.6107178306076888}}
Paired regime summary: {"cases": 2, "mean_offline_error": 3.211339372438547, "random_difference_sd": 0.0, "random_mean_difference": 0.0, "regime": "severity=1.0,period=2500", "seed_difference_sd": 0.12390692554237565, "seed_mean_difference": -0.1747283903755028}
Paired regime summary: {"cases": 2, "mean_offline_error": 3.8281198892080814, "random_difference_sd": 0.0, "random_mean_difference": 0.0, "regime": "severity=1.0,period=5000", "seed_difference_sd": 1.3216676722721987, "seed_mean_difference": -0.07050784531809784}
Paired regime summary: {"cases": 2, "mean_offline_error": 4.553804286219224, "random_difference_sd": 0.0, "random_mean_difference": 0.0, "regime": "severity=3.0,period=2500", "seed_difference_sd": 0.20912802296005115, "seed_mean_difference": -0.04311985998966317}
Paired regime summary: {"cases": 2, "mean_offline_error": 3.2954904111639705, "random_difference_sd": 0.0, "random_mean_difference": 0.0, "regime": "severity=3.0,period=5000", "seed_difference_sd": 0.5721825079901887, "seed_mean_difference": -0.42963072064478847}
Exactly four of five particles relocate at radius1.25 with retained velocities and fixed memory reevaluation. Only the per-particle retention priority evolves. Simple rules and constants are legitimate. Competing explanations include trajectory continuity, geometric diversity, later asynchronous attractor updates, query allocation and stochastic closed-loop variation. No fresh validation is planned in this bounded development experiment.


# Current program

Here is the current program we are trying to improve (you will need to propose a modification to it below):

```python
"""Retain the strongest refreshed personal-best particle for ordinary PSO."""

# EVOLVE-BLOCK-START
def retention_priority(particle_features, swarm_features) -> float:
    """Prefer low integrated distance along a damped inertial trajectory."""
    distance = float(particle_features["distance_to_best_normalized"])
    travel = 0.73 * float(particle_features["speed_normalized"])
    alignment = max(
        -1.0, min(1.0, float(particle_features["velocity_alignment"]))
    )
    # Scale before squaring to avoid overflow.
    scale = max(1.0, distance, travel)
    d = distance / scale
    v = travel / scale
    # Integral over t in [0, 1] of squared distance:
    # d*d - alignment*d*v + v*v/3.
    # This equivalent nonnegative form avoids cancellation.
    radial_midpoint = d - 0.5 * alignment * v
    path_energy = radial_midpoint * radial_midpoint + (
        (1.0 - alignment * alignment) / 4.0 + 1.0 / 12.0
    ) * v * v
    rms_distance = scale * path_energy ** 0.5
    return 1.0 / (1.0 + rms_distance)
# EVOLVE-BLOCK-END

```

Here are the performance metrics of the program:

Combined score to maximize: 0.21
mean_offline_error: 3.72; worst_case_offline_error: 5.20; case_error_std: 1.15; cases_completed: 8

Here is additional text feedback about the current program:

Development feedback only. Lower offline error is better; fitness=1/(1+mean error). Paired differences are candidate minus comparator (negative is better). Random reference is random; heuristic seed is heuristic. All personal-best memories survive and are reevaluated. The exempted particle continues ordinary PSO; it is neither stationary nor a permanent leader. Choices change complete closed-loop trajectories. Agreement is measured against the heuristic on each candidate snapshot, not across reference trajectories.
case_000 severity=1.0,period=2500: error=4.033720, delta random=+0.000730, delta heuristic=-0.086383; heuristic agreements=81/245; selected ranks={'2': 68, '1': 81, '3': 45, '5': 16, '4': 35}; selected feature means={'personal_best_rank': 2.3346938775510204, 'distance_to_best_normalized': 5.849073155014955, 'speed_normalized': 15.139428060206457, 'velocity_alignment': -0.01790057038539746}; interval-end error=3.1332035872776265; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 8.20810091634027, "completed_environment": 7, "difference": -1.4028721757604643, "reference_environment_error": 9.610973092100734}, "most_unfavorable": {"candidate_environment_error": 1.5256197276961827, "completed_environment": 16, "difference": 0.7992166219451575, "reference_environment_error": 0.7264031057510252}}
case_001 severity=1.0,period=2500: error=2.510732, delta random=+0.121043, delta heuristic=-0.141301; heuristic agreements=86/273; selected ranks={'4': 35, '1': 86, '2': 77, '3': 64, '5': 11}; selected feature means={'personal_best_rank': 2.2967032967032965, 'distance_to_best_normalized': 3.9401738980444856, 'speed_normalized': 16.372618854726735, 'velocity_alignment': -0.008644567705116277}; interval-end error=1.5510470072492075; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 1.4995173721002528, "completed_environment": 33, "difference": -1.10067860105287, "reference_environment_error": 2.600195973153123}, "most_unfavorable": {"candidate_environment_error": 2.941127432358593, "completed_environment": 39, "difference": 0.7097873874666285, "reference_environment_error": 2.2313400448919647}}
case_002 severity=1.0,period=5000: error=2.432667, delta random=-0.928965, delta heuristic=-0.064913; heuristic agreements=39/113; selected ranks={'2': 25, '1': 39, '3': 27, '4': 17, '5': 5}; selected feature means={'personal_best_rank': 2.327433628318584, 'distance_to_best_normalized': 7.377021539315129, 'speed_normalized': 12.431239750855427, 'velocity_alignment': 0.05332235228424236}; interval-end error=1.85025046349615; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 1.9332486230430164, "completed_environment": 7, "difference": -1.113419333204787, "reference_environment_error": 3.0466679562478034}, "most_unfavorable": {"candidate_environment_error": 1.9770350692080036, "completed_environment": 3, "difference": 0.9424684215692636, "reference_environment_error": 1.03456664763874}}
case_003 severity=1.0,period=5000: error=4.932270, delta random=+0.637663, delta heuristic=-0.367405; heuristic agreements=35/91; selected ranks={'1': 35, '3': 26, '2': 12, '4': 11, '5': 7}; selected feature means={'personal_best_rank': 2.3736263736263736, 'distance_to_best_normalized': 7.734228316013689, 'speed_normalized': 22.909920227883752, 'velocity_alignment': 0.005657033129816678}; interval-end error=4.1085263906227105; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 4.96981406464863, "completed_environment": 13, "difference": -5.650404637179704, "reference_environment_error": 10.620218701828334}, "most_unfavorable": {"candidate_environment_error": 0.3126323149931868, "completed_environment": 18, "difference": 0.1632659769494966, "reference_environment_error": 0.14936633804369018}}
case_004 severity=3.0,period=2500: error=5.204623, delta random=-0.078081, delta heuristic=-0.269077; heuristic agreements=73/221; selected ranks={'2': 48, '4': 35, '1': 73, '3': 49, '5': 16}; selected feature means={'personal_best_rank': 2.425339366515837, 'distance_to_best_normalized': 2.638107545774059, 'speed_normalized': 5.785121041970215, 'velocity_alignment': -0.043630569988151305}; interval-end error=3.726915769217101; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 2.2789394448426163, "completed_environment": 5, "difference": -9.71632416080488, "reference_environment_error": 11.995263605647496}, "most_unfavorable": {"candidate_environment_error": 3.573403151902721, "completed_environment": 16, "difference": 2.114846107327314, "reference_environment_error": 1.4585570445754066}}
case_005 severity=3.0,period=2500: error=3.973940, delta random=+0.149035, delta heuristic=+0.253791; heuristic agreements=90/338; selected ranks={'1': 90, '3': 77, '2': 89, '4': 51, '5': 31}; selected feature means={'personal_best_rank': 2.5384615384615383, 'distance_to_best_normalized': 1.6888978683278897, 'speed_normalized': 3.6272240062379035, 'velocity_alignment': -0.0011624291557603352}; interval-end error=1.2840304349232723; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 1.7414148310882873, "completed_environment": 9, "difference": -2.1686475456329743, "reference_environment_error": 3.9100623767212617}, "most_unfavorable": {"candidate_environment_error": 7.504631262583923, "completed_environment": 37, "difference": 2.9023155151492617, "reference_environment_error": 4.602315747434662}}
case_006 severity=3.0,period=5000: error=2.333664, delta random=+0.071947, delta heuristic=-0.762278; heuristic agreements=40/115; selected ranks={'3': 27, '5': 7, '2': 25, '1': 40, '4': 16}; selected feature means={'personal_best_rank': 2.347826086956522, 'distance_to_best_normalized': 2.9059877842228086, 'speed_normalized': 5.613266576836145, 'velocity_alignment': -0.04984919232864315}; interval-end error=0.6052251078726784; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 1.5417253633309798, "completed_environment": 11, "difference": -12.578778596175395, "reference_environment_error": 14.120503959506374}, "most_unfavorable": {"candidate_environment_error": 3.892819559779008, "completed_environment": 14, "difference": 3.410470741773338, "reference_environment_error": 0.48234881800566964}}
case_007 severity=3.0,period=5000: error=4.374669, delta random=+0.045405, delta heuristic=+0.020368; heuristic agreements=22/91; selected ranks={'2': 28, '1': 22, '3': 23, '4': 14, '5': 4}; selected feature means={'personal_best_rank': 2.4505494505494507, 'distance_to_best_normalized': 3.5337465964436334, 'speed_normalized': 7.472273495002837, 'velocity_alignment': -0.03642014798255477}; interval-end error=3.487919880092259; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 2.25355679933456, "completed_environment": 4, "difference": -2.0840571111327737, "reference_environment_error": 4.337613910467334}, "most_unfavorable": {"candidate_environment_error": 3.6376925785171412, "completed_environment": 3, "difference": 3.1183724055882296, "reference_environment_error": 0.5193201729289116}}
Paired regime summary: {"cases": 2, "mean_offline_error": 3.2722258822090318, "random_difference_sd": 0.08507413254817449, "random_mean_difference": 0.06088650977048515, "regime": "severity=1.0,period=2500", "seed_difference_sd": 0.03883279299420116, "seed_mean_difference": -0.11384188060501765}
Paired regime summary: {"cases": 2, "mean_offline_error": 3.6824685604005953, "random_difference_sd": 1.1077731569936453, "random_mean_difference": -0.14565132880748566, "regime": "severity=1.0,period=5000", "seed_difference_sd": 0.2138945152785534, "seed_mean_difference": -0.2161591741255835}
Paired regime summary: {"cases": 2, "mean_offline_error": 4.5892814679287035, "random_difference_sd": 0.16059557049812034, "random_mean_difference": 0.03547718170947922, "regime": "severity=3.0,period=2500", "seed_difference_sd": 0.3697235934581715, "seed_mean_difference": -0.0076426782801839455}
Paired regime summary: {"cases": 2, "mean_offline_error": 3.3541663082444497, "random_difference_sd": 0.018768111044570317, "random_mean_difference": 0.05867589708047949, "regime": "severity=3.0,period=5000", "seed_difference_sd": 0.5534143969456183, "seed_mean_difference": -0.370954823564309}
Exactly four of five particles relocate at radius1.25 with retained velocities and fixed memory reevaluation. Only the per-particle retention priority evolves. Simple rules and constants are legitimate. Competing explanations include trajectory continuity, geometric diversity, later asynchronous attractor updates, query allocation and stochastic closed-loop variation. No fresh validation is planned in this bounded development experiment.


# Instructions

Make sure that the changes you propose are consistent with each other. For example, if you refer to a new config variable somewhere, you should also propose a change to add that variable.

Note that the changes you propose will be applied sequentially, so you should assume that the previous changes have already been applied when writing the SEARCH block.

# Task

Suggest a new idea to improve the performance of the code that is inspired by your expert knowledge of the considered subject.
Your goal is to maximize the `combined_score` of the program.
Describe each change with a SEARCH/REPLACE block.

IMPORTANT: Do not rewrite the entire program - focus on targeted improvements.
