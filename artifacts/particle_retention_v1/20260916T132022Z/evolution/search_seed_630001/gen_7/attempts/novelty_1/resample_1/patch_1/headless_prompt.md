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

**Tune the distance–speed weighting first.** Let `d = particle_features["distance_to_best_normalized"]` and `v = particle_features["speed_normalized"]`; try `1/(1 + d + w*v)` with `w` in `{0.5, 0.75, 1.5, 2.0}`. This directly extends the strongest observed rule while testing whether its equal coefficients are optimal, without reintroducing the unsuccessful personal-best rank preference.
Analyze the current program to identify its key parameters and algorithmic components, then design a new algorithm with different parameter settings and configurations.
You MUST respond using a short summary name, description and the full code:

<NAME>
A shortened name summarizing the code you are proposing. Lowercase, no 
spaces, underscores allowed.
</NAME>

<DESCRIPTION>
Identify the key parameters in the current approach and explain how your new parameter choices or algorithmic configuration will lead to better performance.
</DESCRIPTION>

<CODE>
```{language}
# The new parametric algorithm implementation here.
```
</CODE>

* Keep the markers "EVOLVE-BLOCK-START" and "EVOLVE-BLOCK-END" in the code.
* Identify parameters like: learning rates, iteration counts, thresholds, weights, selection criteria, etc.
* Design a new algorithm with different parameter values or configurations.
* Consider adaptive parameters, different optimization strategies, or alternative heuristics.
* Maintain the same inputs and outputs as the original program.
* Use the <NAME>, <DESCRIPTION>, and <CODE> delimiters to structure your response. It will be parsed afterwards.

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


# Current program

Here is the current program we are trying to improve (you will need to propose a new program with the same inputs and outputs as the original program, but with improved internal implementation):

```python
"""Retain the strongest refreshed personal-best particle for ordinary PSO."""

# EVOLVE-BLOCK-START
def retention_priority(particle_features, swarm_features) -> float:
    distance = particle_features["distance_to_best_normalized"]
    speed = particle_features["speed_normalized"]
    return 1.0 / (1.0 + distance + speed)
# EVOLVE-BLOCK-END

```

Here are the performance metrics of the program:

Combined score to maximize: 0.21
mean_offline_error: 3.68; worst_case_offline_error: 5.59; case_error_std: 1.17; cases_completed: 8

Here is additional text feedback about the current program:

Development feedback only. Lower offline error is better; fitness=1/(1+mean error). Paired differences are candidate minus comparator (negative is better). Random reference is random; heuristic seed is heuristic. All personal-best memories survive and are reevaluated. The exempted particle continues ordinary PSO; it is neither stationary nor a permanent leader. Choices change complete closed-loop trajectories. Agreement is measured against the heuristic on each candidate snapshot, not across reference trajectories.
case_000 severity=1.0,period=2500: error=3.963754, delta random=-0.069236, delta heuristic=-0.156349; heuristic agreements=63/245; selected ranks={'4': 44, '1': 63, '3': 61, '5': 17, '2': 60}; selected feature means={'personal_best_rank': 2.559183673469388, 'distance_to_best_normalized': 7.274517157557297, 'speed_normalized': 14.741612700445966, 'velocity_alignment': -0.19133391489872775}; interval-end error=3.1370214841528696; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 8.250916853200081, "completed_environment": 7, "difference": -1.3600562389006523, "reference_environment_error": 9.610973092100734}, "most_unfavorable": {"candidate_environment_error": 1.4104665432127743, "completed_environment": 24, "difference": 0.41483994975484684, "reference_environment_error": 0.9956265934579275}}
case_001 severity=1.0,period=2500: error=2.505091, delta random=+0.115403, delta heuristic=-0.146941; heuristic agreements=62/271; selected ranks={'4': 69, '1': 62, '2': 65, '3': 65, '5': 10}; selected feature means={'personal_best_rank': 2.6309963099630997, 'distance_to_best_normalized': 4.447048258827792, 'speed_normalized': 16.330472628949, 'velocity_alignment': -0.09086038263722768}; interval-end error=1.5600283871009908; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 1.3271309706387258, "completed_environment": 33, "difference": -1.273065002514397, "reference_environment_error": 2.600195973153123}, "most_unfavorable": {"candidate_environment_error": 2.0368798508414527, "completed_environment": 24, "difference": 0.36954092931940186, "reference_environment_error": 1.6673389215220509}}
case_002 severity=1.0,period=5000: error=2.418935, delta random=-0.942697, delta heuristic=-0.078644; heuristic agreements=35/108; selected ranks={'2': 27, '1': 35, '4': 21, '3': 22, '5': 3}; selected feature means={'personal_best_rank': 2.3518518518518516, 'distance_to_best_normalized': 6.94705199146454, 'speed_normalized': 12.60126660550776, 'velocity_alignment': -0.11002859038854482}; interval-end error=1.8455102453614969; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 0.47837464308166666, "completed_environment": 15, "difference": -4.422334362272082, "reference_environment_error": 4.9007090053537485}, "most_unfavorable": {"candidate_environment_error": 4.597648520259427, "completed_environment": 19, "difference": 3.712117890208544, "reference_environment_error": 0.8855306300508833}}
case_003 severity=1.0,period=5000: error=5.587274, delta random=+1.292666, delta heuristic=+0.287598; heuristic agreements=27/92; selected ranks={'1': 27, '4': 17, '3': 26, '2': 19, '5': 3}; selected feature means={'personal_best_rank': 2.4565217391304346, 'distance_to_best_normalized': 7.742258053063493, 'speed_normalized': 21.033998550192184, 'velocity_alignment': -0.08307197854995187}; interval-end error=4.551950915433793; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 0.5130374581224008, "completed_environment": 16, "difference": -1.1156083879468275, "reference_environment_error": 1.6286458460692281}, "most_unfavorable": {"candidate_environment_error": 18.741781498892284, "completed_environment": 13, "difference": 8.12156279706395, "reference_environment_error": 10.620218701828334}}
case_004 severity=3.0,period=2500: error=4.712015, delta random=-0.570689, delta heuristic=-0.761685; heuristic agreements=63/219; selected ranks={'3': 57, '2': 44, '4': 40, '1': 63, '5': 15}; selected feature means={'personal_best_rank': 2.5433789954337898, 'distance_to_best_normalized': 2.852981967267297, 'speed_normalized': 5.014310703500791, 'velocity_alignment': -0.15232182134337174}; interval-end error=2.942983764900269; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 5.595669411205818, "completed_environment": 34, "difference": -16.89133474252129, "reference_environment_error": 22.48700415372711}, "most_unfavorable": {"candidate_environment_error": 2.9239362962665374, "completed_environment": 14, "difference": 2.211623198624932, "reference_environment_error": 0.7123130976416053}}
case_005 severity=3.0,period=2500: error=3.941265, delta random=+0.116361, delta heuristic=+0.221117; heuristic agreements=97/345; selected ranks={'3': 86, '1': 97, '2': 84, '5': 23, '4': 55}; selected feature means={'personal_best_rank': 2.4869565217391303, 'distance_to_best_normalized': 1.9171981930032558, 'speed_normalized': 3.5481812542776225, 'velocity_alignment': -0.17384602790263984}; interval-end error=1.1894122609591515; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 1.6327300758113725, "completed_environment": 9, "difference": -2.2773323009098894, "reference_environment_error": 3.9100623767212617}, "most_unfavorable": {"candidate_environment_error": 4.4914563556125, "completed_environment": 11, "difference": 2.4615639244258287, "reference_environment_error": 2.029892431186671}}
case_006 severity=3.0,period=5000: error=2.393708, delta random=+0.131991, delta heuristic=-0.702234; heuristic agreements=31/130; selected ranks={'3': 29, '2': 33, '5': 16, '1': 31, '4': 21}; selected feature means={'personal_best_rank': 2.6769230769230767, 'distance_to_best_normalized': 2.205994522825557, 'speed_normalized': 3.027150052197335, 'velocity_alignment': -0.12176270938666095}; interval-end error=0.6688800862408364; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 2.0174801157091933, "completed_environment": 13, "difference": -5.604630869879591, "reference_environment_error": 7.622110985588784}, "most_unfavorable": {"candidate_environment_error": 2.491703716736051, "completed_environment": 14, "difference": 2.0093548987303818, "reference_environment_error": 0.48234881800566964}}
case_007 severity=3.0,period=5000: error=3.923654, delta random=-0.405610, delta heuristic=-0.430647; heuristic agreements=30/99; selected ranks={'3': 25, '2': 22, '1': 30, '4': 12, '5': 10}; selected feature means={'personal_best_rank': 2.494949494949495, 'distance_to_best_normalized': 3.317869905134358, 'speed_normalized': 5.617704004878381, 'velocity_alignment': -0.17907473506534138}; interval-end error=2.975825238651738; incomplete responses=0.
Observed environment episodes versus heuristic (descriptive extrema, not selected confirmation): {"most_favorable": {"candidate_environment_error": 0.9866627102790037, "completed_environment": 7, "difference": -5.51183530608752, "reference_environment_error": 6.498498016366524}, "most_unfavorable": {"candidate_environment_error": 12.263204526425044, "completed_environment": 14, "difference": 2.5886466494505243, "reference_environment_error": 9.67455787697452}}
Paired regime summary: {"cases": 2, "mean_offline_error": 3.2344227747801577, "random_difference_sd": 0.13055909577254843, "random_mean_difference": 0.023083402341611103, "regime": "severity=1.0,period=2500", "seed_difference_sd": 0.006652170230172764, "seed_mean_difference": -0.1516449880338917}
Paired regime summary: {"cases": 2, "mean_offline_error": 4.003104796626859, "random_difference_sd": 1.5806404426300158, "random_mean_difference": 0.17498490741877815, "regime": "severity=1.0,period=5000", "seed_difference_sd": 0.25897277035781713, "seed_mean_difference": 0.1044770621006803}
Paired regime summary: {"cases": 2, "mean_offline_error": 4.326640169596648, "random_difference_sd": 0.48581793776056154, "random_mean_difference": -0.22716411662257596, "regime": "severity=3.0,period=2500", "seed_difference_sd": 0.6949459607206127, "seed_mean_difference": -0.27028397661223913}
Paired regime summary: {"cases": 2, "mean_offline_error": 3.1586809656670662, "random_difference_sd": 0.3801413469797772, "random_mean_difference": -0.136809445496904, "regime": "severity=3.0,period=5000", "seed_difference_sd": 0.1920411610104114, "seed_mean_difference": -0.5664401661416925}
Exactly four of five particles relocate at radius1.25 with retained velocities and fixed memory reevaluation. Only the per-particle retention priority evolves. Simple rules and constants are legitimate. Competing explanations include trajectory continuity, geometric diversity, later asynchronous attractor updates, query allocation and stochastic closed-loop variation. No fresh validation is planned in this bounded development experiment.


# Task

Rewrite the program to improve its performance on the specified metrics.
Provide the complete new program code.

IMPORTANT: Make sure your rewritten program maintains the same inputs and outputs as the original program, but with improved internal implementation.
