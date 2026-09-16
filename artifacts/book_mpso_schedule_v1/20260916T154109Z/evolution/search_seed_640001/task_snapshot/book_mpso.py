"""Versioned chapter-aligned MPSO 5+0 / 5+1 and temporary-conversion schedules.

This is a separate numerical path: historical ``simulator.run_case`` is unchanged.
Designated neutral roles are indices 0..4 throughout a swarm's lifetime. A sixth
particle, when present, is permanently quantum. Neutral particles update first;
all attractors update asynchronously. Exclusion follows EACH subswarm update.
The documented convergence convention remains the neutral pairwise-diameter
approximation, not an exact smallest-enclosing-ball calculation.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import random
from collections import Counter
from typing import Callable

from .simulator import (BudgetExhausted, Particle, Swarm, _MPB, _distance,
                        _validated_config, sample_uvd)

NEUTRAL_COUNT = 5
ENGINE_VERSION = "book_mpso_schedule_v1"
AGE_BINS = ("never_detected", "0", "1", "2-3", "4-7", "8-15", "16-31", "32+")


def published_schedule(observation):
    """Published one-update conversion, shared by both standalone references."""
    return 5 if observation["change_detected"] else 0


def selection_rng_for_seed(optimizer_seed):
    digest = hashlib.sha256(
        f"book_mpso_schedule_v1:neutral-permutation:{optimizer_seed}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def neutral_diameter(swarm):
    return max((_distance(a.position, b.position) for a, b in
                itertools.combinations(swarm.particles[:NEUTRAL_COUNT], 2)), default=0.0)


def move_particle(particle, center, rng, cfg, quantum):
    """Quantum sampling replaces ordinary PSO and leaves velocity untouched."""
    if quantum:
        particle.position = sample_uvd(rng, center, 0.5 * cfg["move_severity"])
    elif particle.best is not None:
        for dim in range(cfg["dimension"]):
            attraction = cfg["c"] * rng.random() * (center[dim] - particle.position[dim])
            attraction += cfg["c"] * rng.random() * (particle.best[dim] - particle.position[dim])
            particle.velocity[dim] = cfg["chi"] * (particle.velocity[dim] + attraction)
            particle.position[dim] += particle.velocity[dim]


def age_bin(age, has_detected):
    if not has_detected:
        return "never_detected"
    if age < 2:
        return str(age)
    for upper, label in ((3, "2-3"), (7, "4-7"), (15, "8-15"), (31, "16-31")):
        if age <= upper:
            return label
    return "32+"


def run_case(config: dict, schedule: Callable | None = None,
             progress: Callable | None = None, *, permanent_quantum: int = 1) -> dict:
    """Run the chapter comparison with exact counted objective accounting.

    ``particles_per_swarm=5`` denotes the fixed neutral membership; actual size
    is five plus ``permanent_quantum`` (zero or one). The candidate receives a
    fresh read-only public snapshot after detection and all required memory
    queries. A dedicated selection RNG shuffles all five indices EVERY update,
    even for zero/full conversion; candidate scores consume no simulator RNG.
    """
    from types import MappingProxyType
    from .book_schedule import validated_count

    cfg = _validated_config(config)
    if cfg["particles_per_swarm"] != NEUTRAL_COUNT:
        raise ValueError("Chapter schedule path requires exactly five designated neutrals")
    if type(permanent_quantum) is not int or permanent_quantum not in (0, 1):
        raise ValueError("permanent_quantum must be the integer zero or one")
    choose = published_schedule if schedule is None else schedule
    if not callable(choose):
        raise TypeError("schedule must be callable")
    rng = random.Random(cfg["optimizer_seed"])
    selection_rng = selection_rng_for_seed(cfg["optimizer_seed"])
    env_rng = random.Random(cfg["environment_seed"])
    scenario = dict(_MPB.SCENARIO_2)
    scenario.update(npeaks=cfg["npeaks"], period=cfg["period"],
                    move_severity=cfg["move_severity"], lambda_=cfg["correlation"],
                    height_severity=cfg["height_severity"], width_severity=cfg["width_severity"],
                    min_coord=cfg["bounds"][0], max_coord=cfg["bounds"][1])
    landscape = _MPB.MovingPeaks(dim=cfg["dimension"], random=env_rng, **scenario)
    width = cfg["bounds"][1] - cfg["bounds"][0]
    default_radius = 0.5 * cfg["move_severity"]
    counts = Counter()
    trace, snapshots, response_log, environment_changes = [], [], [], []
    population, state = [], {}
    next_identifier = 0
    epoch = 0
    epoch_error_sum = 0.0
    epoch_eval_count = 0
    epoch_first_error = None
    epoch_first_eval = 1
    stats = {"updates": 0, "completed_updates": 0, "detected_change_updates": 0,
             "requested_neutral_conversions": 0,
             "count_histogram": {str(k): 0 for k in range(6)},
             "age_bins": {label: {"updates": 0, "neutral_conversions": 0,
                           "count_histogram": {str(k): 0 for k in range(6)}} for label in AGE_BINS},
             "shared_best_improvements": {kind: {"count": 0, "total_gain": 0.0}
                 for kind in ("ordinary", "temporary_quantum", "permanent_quantum")},
             "decision_examples": [], "selection_permutations": 0,
             "births": 0, "removals": 0, "exclusion_reinitializations": 0}
    example_criteria_done = set()

    def emit(event, **data):
        if progress is not None:
            progress({"event": event, **data})

    def environment_state():
        data = {"positions": [list(p) for p in landscape.peaks_position],
                "heights": list(landscape.peaks_height), "widths": list(landscape.peaks_width)}
        data["sha256"] = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        return data

    initial_environment = environment_state()

    def add_snapshot():
        if snapshots and snapshots[-1]["evaluations"] == landscape.nevals:
            return
        snapshots.append({"evaluations": landscape.nevals, "environment": epoch,
                          "swarms": [{"id": s.identifier, "best": s.best,
                                      "neutral_count": NEUTRAL_COUNT,
                                      "particles": [list(p.position) for p in s.particles]}
                                     for s in population], "landscape": environment_state()})

    def evaluate(position, kind):
        nonlocal epoch, epoch_error_sum, epoch_eval_count, epoch_first_error, epoch_first_eval
        if landscape.nevals >= cfg["budget"]:
            raise BudgetExhausted
        if not all(math.isfinite(x) for x in position):
            raise ValueError("Non-finite particle position")
        optimum = (landscape.globalMaximum()[0] if landscape._optimum is None else landscape._optimum)
        value = landscape(position)[0]
        counts[kind] += 1
        error = landscape.currentError()
        epoch_error_sum += error
        epoch_eval_count += 1
        if epoch_first_error is None:
            epoch_first_error = error
        boundary = bool(cfg["period"] and landscape.nevals % cfg["period"] == 0)
        if (landscape.nevals == 1 or landscape.nevals == cfg["budget"] or boundary
                or (cfg["trace_interval"] and landscape.nevals % cfg["trace_interval"] == 0)):
            trace.append({"evaluations": landscape.nevals, "environment": epoch,
                          "current_error": error, "offline_error": landscape.offlineError(),
                          "optimum": optimum, "evaluated_fitness": value,
                          "swarm_count": len(population), "evaluation_kind": kind})
        if boundary:
            entry = {"evaluations": landscape.nevals, "completed_environment": epoch,
                     "environment_offline_error": epoch_error_sum / epoch_eval_count,
                     "environment_initial_error": epoch_first_error,
                     "environment_final_error": error, "first_evaluation": epoch_first_eval,
                     "environment_evaluations": epoch_eval_count,
                     "offline_error": landscape.offlineError(), "swarm_count": len(population),
                     "next_environment": environment_state()}
            environment_changes.append(entry)
            emit("environment_change", **{k: v for k, v in entry.items() if k != "next_environment"})
            epoch += 1
            epoch_error_sum, epoch_eval_count, epoch_first_error = 0.0, 0, None
            epoch_first_eval = landscape.nevals + 1
        elif cfg["progress_interval"] and landscape.nevals % cfg["progress_interval"] == 0:
            emit("progress", evaluations=landscape.nevals, budget=cfg["budget"],
                 offline_error=landscape.offlineError(), swarm_count=len(population))
        if cfg["snapshot_interval"] and landscape.nevals % cfg["snapshot_interval"] == 0:
            add_snapshot()
        return value

    def make_swarm():
        nonlocal next_identifier
        swarm = Swarm(next_identifier, [Particle(
            [rng.uniform(*cfg["bounds"]) for _ in range(cfg["dimension"])],
            [rng.uniform(-width / 2, width / 2) for _ in range(cfg["dimension"])])
            for _ in range(NEUTRAL_COUNT + permanent_quantum)])
        next_identifier += 1
        state[swarm.identifier] = {"last_detection_eval": landscape.nevals,
            "updates_since_detection": 0, "has_detected": False, "previous_count": 0}
        return swarm

    def update_attractors(swarm, particle, value, kind):
        particle.fitness = value
        if particle.best_fitness is None or value > particle.best_fitness:
            particle.best, particle.best_fitness = list(particle.position), value
        if swarm.best_fitness is None or value > swarm.best_fitness:
            if swarm.best_fitness is not None:
                gain = value - swarm.best_fitness
                swarm.recent_improvement += gain
                if kind in stats["shared_best_improvements"]:
                    stats["shared_best_improvements"][kind]["count"] += 1
                    stats["shared_best_improvements"][kind]["total_gain"] += gain
            swarm.best, swarm.best_fitness = list(particle.position), value

    def initialize_swarm(swarm, kind):
        for particle in swarm.particles:
            update_attractors(swarm, particle, evaluate(particle.position, kind), kind)
        swarm.recent_improvement = 0.0

    def observation_for(swarm, detected, previous_fitness, checked_fitness):
        data = state[swarm.identifier]
        speeds, distances, alignments = [], [], []
        for particle in swarm.particles[:NEUTRAL_COUNT]:
            direction = [b - x for b, x in zip(swarm.best, particle.position)]
            distance = math.sqrt(sum(x * x for x in direction))
            speed = math.sqrt(sum(v * v for v in particle.velocity))
            distances.append(distance)
            speeds.append(speed)
            alignment = (sum(v * d for v, d in zip(particle.velocity, direction)) / (speed * distance)
                         if speed and distance else 0.0)
            alignments.append(max(-1.0, min(1.0, alignment)))
        return {"change_detected": detected, "has_detected_change": data["has_detected"],
                "updates_since_detected_change": data["updates_since_detection"],
                "evaluations_since_detected_change": landscape.nevals - data["last_detection_eval"],
                "fitness_drop": previous_fitness - checked_fitness,
                "relative_fitness_drop": (previous_fitness - checked_fitness) / max(1.0, abs(previous_fitness)),
                "recent_improvement": swarm.recent_improvement,
                "previous_best_fitness": previous_fitness, "current_best_fitness": swarm.best_fitness,
                "neutral_diameter": neutral_diameter(swarm),
                "mean_neutral_distance_to_best": sum(distances) / NEUTRAL_COUNT,
                "mean_neutral_speed": sum(speeds) / NEUTRAL_COUNT,
                "mean_velocity_alignment_to_best": sum(alignments) / NEUTRAL_COUNT,
                "previous_conversion_count": data["previous_count"], "default_radius": default_radius,
                "swarm_count": len(population), "dimension": cfg["dimension"], "bounds_width": width,
                "swarm_size": len(swarm.particles), "neutral_count": NEUTRAL_COUNT,
                "permanent_quantum_count": permanent_quantum}

    def update_swarm(swarm):
        # Every live swarm is initialized before entering this routine.
        previous_fitness = swarm.best_fitness
        checked_fitness = evaluate(swarm.best, "detection")
        detected = checked_fitness != previous_fitness
        data = state[swarm.identifier]
        detected_at = landscape.nevals
        if detected:
            data.update(last_detection_eval=detected_at, updates_since_detection=0, has_detected=True)
            for particle in swarm.particles:
                particle.best_fitness = evaluate(particle.best, "memory")
            best_particle = max(swarm.particles, key=lambda p: p.best_fitness)
            swarm.best, swarm.best_fitness = list(best_particle.best), best_particle.best_fitness
        observation = observation_for(swarm, detected, previous_fitness, checked_fitness)
        count = validated_count(choose(MappingProxyType(observation)))
        permutation = list(range(NEUTRAL_COUNT))
        selection_rng.shuffle(permutation)
        selected = set(permutation[:count])
        stats["selection_permutations"] += 1
        stats["updates"] += 1
        stats["detected_change_updates"] += int(detected)
        stats["requested_neutral_conversions"] += count
        stats["count_histogram"][str(count)] += 1
        bucket = stats["age_bins"][age_bin(data["updates_since_detection"], data["has_detected"])]
        bucket["updates"] += 1
        bucket["neutral_conversions"] += count
        bucket["count_histogram"][str(count)] += 1
        entry = {"swarm_id": swarm.identifier, "decided_at_evaluation": landscape.nevals,
                 "detected_at_evaluation": detected_at if detected else None,
                 "observation": observation, "decision": {"temporary_quantum_count": count},
                 "selected_neutral_indices": sorted(selected), "completed": False}
        if detected:
            response_log.append(entry)
        criteria = []
        if "first_update" not in example_criteria_done:
            criteria.append("first_update")
        if detected and "first_detected_change" not in example_criteria_done:
            criteria.append("first_detected_change")
        for fraction, name in ((0.25, "quarter_budget"), (0.5, "half_budget"), (0.75, "three_quarter_budget")):
            if landscape.nevals >= fraction * cfg["budget"] and name not in example_criteria_done:
                criteria.append(name)
        if criteria:
            example_criteria_done.update(criteria)
            entry["example_criteria"] = criteria
            entry["particles_before"] = [{"position": list(p.position), "velocity": list(p.velocity)}
                                         for p in swarm.particles]
            entry["best_before"] = list(swarm.best)
            entry["best_fitness_before"] = swarm.best_fitness
            entry["selection_permutation"] = permutation
            entry["particle_updates"] = []
            stats["decision_examples"].append(entry)
        data["previous_count"] = count
        swarm.recent_improvement = 0.0
        try:
            for index, particle in enumerate(swarm.particles):
                quantum = index >= NEUTRAL_COUNT or index in selected
                kind = ("permanent_quantum" if index >= NEUTRAL_COUNT else
                        "temporary_quantum" if quantum else "ordinary")
                center = list(swarm.best)
                move_particle(particle, center, rng, cfg, quantum)
                value = evaluate(particle.position, kind)
                update_attractors(swarm, particle, value, kind)
                if criteria:
                    entry["particle_updates"].append({"index": index, "kind": kind,
                        "center": center, "position": list(particle.position),
                        "velocity": list(particle.velocity), "fitness": value,
                        "best_after": swarm.best_fitness})
            entry["completed"] = True
            stats["completed_updates"] += 1
            data["updates_since_detection"] += 1
        finally:
            entry["finished_at_evaluation"] = landscape.nevals
            if criteria:
                entry["best_fitness_after"] = swarm.best_fitness

    variant = f"chapter_mpso_5_plus_{permanent_quantum}"
    emit("run_started", config=cfg, baseline=variant, budget=cfg["budget"])
    iterations = 0
    population.append(make_swarm())
    if cfg["snapshot_interval"]:
        add_snapshot()
    try:
        initialize_swarm(population[0], "initialization")
        while landscape.nevals < cfg["budget"]:
            iterations += 1
            # Radius is fixed for this outer iteration, before birth/removal.
            exclusion_radius = width / (2 * len(population) ** (1.0 / cfg["dimension"]))
            free = [s for s in population if neutral_diameter(s) > 2 * exclusion_radius]
            if not free:
                population.append(make_swarm())
                stats["births"] += 1
                initialize_swarm(population[-1], "birth")
            elif len(free) > cfg["nexcess"]:
                worst = min(free, key=lambda s: s.best_fitness)
                population.remove(worst)
                stats["removals"] += 1
            for index in range(len(population)):
                update_swarm(population[index])
                # Algorithm 3: exclusion is inside the subswarm loop. Immediate
                # replacements participate in remaining comparisons. A later
                # list position still receives its scheduled update this pass.
                for other in range(len(population)):
                    if other == index:
                        continue
                    a, b = population[index], population[other]
                    if _distance(a.best, b.best) < exclusion_radius:
                        loser = index if a.best_fitness <= b.best_fitness else other
                        population[loser] = make_swarm()
                        stats["exclusion_reinitializations"] += 1
                        initialize_swarm(population[loser], "exclusion")
    except BudgetExhausted:
        pass
    except Exception as exc:
        exc.objective_queries = landscape.nevals
        exc.evaluation_counts = dict(counts)
        raise
    if cfg["snapshot_interval"]:
        add_snapshot()
    stats["neutral_conversion_fraction"] = (stats["requested_neutral_conversions"] /
        (NEUTRAL_COUNT * stats["updates"]) if stats["updates"] else 0.0)
    stats["executed_neutral_conversion_fraction"] = (counts["temporary_quantum"] /
        (counts["temporary_quantum"] + counts["ordinary"])
        if counts["temporary_quantum"] + counts["ordinary"] else 0.0)
    result = {"config": cfg, "engine_version": ENGINE_VERSION, "baseline_variant": variant,
              "permanent_quantum": permanent_quantum,
              "policy_name": getattr(choose, "__name__", type(choose).__name__),
              "evaluations": landscape.nevals, "evaluation_counts": dict(counts),
              "offline_error": landscape.offlineError(), "final_error": landscape.currentError(),
              "iterations": iterations, "final_swarm_count": len(population),
              "environments_evaluated": (1 + (landscape.nevals - 1) // cfg["period"] if cfg["period"] else 1),
              "initial_environment": initial_environment, "environment_changes": environment_changes,
              "trace": trace, "response_log": response_log, "snapshots": snapshots,
              "schedule_stats": stats,
              "partial_environment": ({"environment": epoch, "evaluations": epoch_eval_count,
                  "offline_error": epoch_error_sum / epoch_eval_count,
                  "initial_error": epoch_first_error, "final_error": landscape.currentError()}
                  if epoch_eval_count else None)}
    assert result["evaluations"] == cfg["budget"] == sum(counts.values())
    emit("run_completed", evaluations=landscape.nevals, offline_error=result["offline_error"],
         response_count=len(response_log), swarm_count=len(population))
    return result
