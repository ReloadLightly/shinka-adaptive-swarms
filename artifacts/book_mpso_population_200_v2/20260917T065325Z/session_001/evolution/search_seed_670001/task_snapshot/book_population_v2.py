"""Versioned MPSO population adaptation with the published response schedule.

Historical book_mpso.py is unchanged. Every swarm starts with five neutral
particles and one permanent quantum particle. Only a counted detected change
can resize its neutral population, by at most one, toward a target in [2, 8].
Neutral survivor order and the permanent role are preserved. This continuation
changes only convergence geometry to the chapter's minimum enclosing ball.
Target five is the corrected reconstructed 5+1 reference; historical diameter-
engine scores are not compatible with this version.
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
ENGINE_VERSION = "book_mpso_population_v2_enclosing_ball"
AGE_BINS = ("never_detected", "0", "1", "2-3", "4-7", "8-15", "16-31", "32+")


from .book_mpso import move_particle, selection_rng_for_seed
from .enclosing_ball import enclosing_ball_converged


def fixed_five(observation):
    return 5


def neutral_count(swarm):
    """Permanent quantum role is always the last particle."""
    return len(swarm.particles) - 1


def neutral_diameter(swarm):
    return max((_distance(a.position, b.position) for a, b in
                itertools.combinations(swarm.particles[:-1], 2)), default=0.0)


def resize_neutrals(swarm, target, rng, cfg):
    """Resize by at most one after refresh, without objective evaluations.

    Equal worst memories remove the last neutral in the current stable order.
    The new particle has no fitness or remembered position. Its placeholder
    position is replaced by the following quantum update before evaluation.
    """
    current = neutral_count(swarm)
    event = {"requested_target": target, "neutral_count_before": current,
             "neutral_count_after": current, "resize": "none"}
    if target < current:
        index = min(range(current), key=lambda i: (swarm.particles[i].best_fitness, -i))
        removed = swarm.particles.pop(index)
        best = max(swarm.particles, key=lambda particle: particle.best_fitness)
        swarm.best, swarm.best_fitness = list(best.best), best.best_fitness
        event.update(neutral_count_after=current - 1, resize="remove",
                     removed_neutral_index=index, removed_best_fitness=removed.best_fitness)
    elif target > current:
        width = cfg["bounds"][1] - cfg["bounds"][0]
        new_particle = Particle(list(swarm.best),
            [rng.uniform(-width / 2, width / 2) for _ in range(cfg["dimension"])])
        swarm.particles.insert(current, new_particle)
        event.update(neutral_count_after=current + 1, resize="add",
                     added_neutral_index=current)
    return event


def age_bin(age, has_detected):
    if not has_detected:
        return "never_detected"
    if age < 2:
        return str(age)
    for upper, label in ((3, "2-3"), (7, "4-7"), (15, "8-15"), (31, "16-31")):
        if age <= upper:
            return label
    return "32+"


def run_case(config: dict, population_policy: Callable | None = None,
             progress: Callable | None = None) -> dict:
    """Run fixed chapter 5+1 with optional change-triggered population targets.

    The policy sees one immutable public snapshot after all existing memories
    are refreshed and before resizing/movement. Five is the corrected reference:
    no resize and no extra RNG draws. Only convergence differs from v1.
    """
    from types import MappingProxyType
    from .population_policy_v2 import validated_target

    cfg = _validated_config(config)
    if cfg["particles_per_swarm"] != NEUTRAL_COUNT:
        raise ValueError("Population path starts with exactly five neutral particles")
    permanent_quantum = 1
    choose = fixed_five if population_policy is None else population_policy
    if not callable(choose):
        raise TypeError("population_policy must be callable")
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
             "count_histogram": {str(k): 0 for k in range(9)},
             "age_bins": {label: {"updates": 0, "neutral_conversions": 0,
                           "count_histogram": {str(k): 0 for k in range(9)}} for label in AGE_BINS},
             "shared_best_improvements": {kind: {"count": 0, "total_gain": 0.0}
                 for kind in ("ordinary", "temporary_quantum", "permanent_quantum")},
             "decision_examples": [], "selection_permutations": 0,
             "births": 0, "removals": 0, "exclusion_reinitializations": 0}
    population_stats = {
        "policy_calls": 0, "population_decisions": 0,
        "requested_target_histogram": {str(k): 0 for k in range(2, 9)},
        "realized_neutral_count_histogram": {str(k): 0 for k in range(2, 9)},
        "additions": 0, "removals": 0, "no_change_requests": 0,
        "total_neutral_updates": 0, "neutral_count_sum": 0,
        "decision_examples": [],
    }
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

    def population_summary():
        sizes = [neutral_count(swarm) for swarm in population]
        return {"total_particle_count": sum(sizes) + len(sizes),
                "total_neutral_count": sum(sizes),
                "mean_neutral_count": sum(sizes) / len(sizes) if sizes else 0.0,
                "neutral_count_min": min(sizes) if sizes else 0,
                "neutral_count_max": max(sizes) if sizes else 0}

    def add_snapshot():
        if snapshots and snapshots[-1]["evaluations"] == landscape.nevals:
            return
        snapshots.append({"evaluations": landscape.nevals, "environment": epoch,
                          "swarms": [{"id": s.identifier, "best": s.best,
                                      "neutral_count": neutral_count(s),
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
                          "swarm_count": len(population), "evaluation_kind": kind, **population_summary()})
        if boundary:
            entry = {"evaluations": landscape.nevals, "completed_environment": epoch,
                     "environment_offline_error": epoch_error_sum / epoch_eval_count,
                     "environment_initial_error": epoch_first_error,
                     "environment_final_error": error, "first_evaluation": epoch_first_eval,
                     "environment_evaluations": epoch_eval_count,
                     "offline_error": landscape.offlineError(), "swarm_count": len(population),
                     "next_environment": environment_state(), **population_summary()}
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
            "updates_since_detection": 0, "has_detected": False, "previous_count": 0,
            "previous_requested_target": 5}
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
        for particle in swarm.particles[:-1]:
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
                "mean_neutral_distance_to_best": sum(distances) / neutral_count(swarm),
                "mean_neutral_speed": sum(speeds) / neutral_count(swarm),
                "mean_velocity_alignment_to_best": sum(alignments) / neutral_count(swarm),
                "previous_conversion_count": data["previous_count"], "default_radius": default_radius,
                "swarm_count": len(population), "dimension": cfg["dimension"], "bounds_width": width,
                "swarm_size": len(swarm.particles), "neutral_count": neutral_count(swarm),
                "total_particle_count": sum(len(s.particles) for s in population),
                "previous_requested_target": data["previous_requested_target"],
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
        resize = {"requested_target": data["previous_requested_target"],
                  "neutral_count_before": neutral_count(swarm),
                  "neutral_count_after": neutral_count(swarm), "resize": "not_called"}
        if detected:
            target = validated_target(choose(MappingProxyType(observation)))
            resize = resize_neutrals(swarm, target, rng, cfg)
            population_stats["policy_calls"] += 1
            population_stats["population_decisions"] += 1
            population_stats["requested_target_histogram"][str(target)] += 1
            population_stats["additions"] += int(resize["resize"] == "add")
            population_stats["removals"] += int(resize["resize"] == "remove")
            population_stats["no_change_requests"] += int(resize["resize"] == "none")
            data["previous_requested_target"] = target
        current_neutral_count = neutral_count(swarm)
        count = current_neutral_count if detected else 0
        population_stats["realized_neutral_count_histogram"][str(current_neutral_count)] += 1
        population_stats["total_neutral_updates"] += 1
        population_stats["neutral_count_sum"] += current_neutral_count
        permutation = list(range(current_neutral_count))
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
                 "observation": observation, "decision": {"temporary_quantum_count": count, **resize},
                 **resize, **population_summary(),
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
            population_stats["decision_examples"].append(entry)
        data["previous_count"] = count
        swarm.recent_improvement = 0.0
        try:
            for index, particle in enumerate(swarm.particles):
                quantum = index >= current_neutral_count or index in selected
                kind = ("permanent_quantum" if index >= current_neutral_count else
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

    variant = "chapter_mpso_population_plus_1"
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
            free = [s for s in population if not enclosing_ball_converged(
                (particle.position for particle in s.particles[:-1]), exclusion_radius)]
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
        (population_stats["neutral_count_sum"]) if stats["updates"] else 0.0)
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
              "schedule_stats": stats, "population_stats": population_stats,
              "partial_environment": ({"environment": epoch, "evaluations": epoch_eval_count,
                  "offline_error": epoch_error_sum / epoch_eval_count,
                  "initial_error": epoch_first_error, "final_error": landscape.currentError()}
                  if epoch_eval_count else None)}
    assert result["evaluations"] == cfg["budget"] == sum(counts.values())
    emit("run_completed", evaluations=landscape.nevals, offline_error=result["offline_error"],
         response_count=len(response_log), swarm_count=len(population))
    return result
