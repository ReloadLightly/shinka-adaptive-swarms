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


# Current program

Here is the current program we are trying to improve (you will need to propose a modification to it below):

```python
"""Retain the strongest refreshed personal-best particle for ordinary PSO."""

# EVOLVE-BLOCK-START
def retention_priority(particle_features, swarm_features) -> float:
    return -particle_features["personal_best_rank"]
# EVOLVE-BLOCK-END

```

Here are the performance metrics of the program:

Combined score to maximize: 0.20
mean_offline_error: 3.90; worst_case_offline_error: 5.47; case_error_std: 1.13; cases_completed: 8

Here is additional text feedback about the current program:

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


# Instructions

Make sure that the changes you propose are consistent with each other. For example, if you refer to a new config variable somewhere, you should also propose a change to add that variable.

Note that the changes you propose will be applied sequentially, so you should assume that the previous changes have already been applied when writing the SEARCH block.

# Task

Suggest a new idea to improve the performance of the code that is inspired by your expert knowledge of the considered subject.
Your goal is to maximize the `combined_score` of the program.
Describe each change with a SEARCH/REPLACE block.

IMPORTANT: Do not rewrite the entire program - focus on targeted improvements.
