"""Corrected book-style MPSO with a narrow, interpretable response hook.

The landscape is the pristine DEAP implementation pinned in vendor/deap.
The optimizer follows Blackwell, Branke and Li (2008), pp. 193--218,
Algorithm 3, using the book-tested five-neutral/zero-permanent-quantum case.
See docs/reproduction.md for the exact reconstruction and differences.
"""

from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import math
import random
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .policies import book_response, normalize_response


_VENDOR_FILE = Path(__file__).resolve().parents[2] / "vendor/deap/movingpeaks.py"
_SPEC = importlib.util.spec_from_file_location("_adaptive_swarms_movingpeaks", _VENDOR_FILE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"Cannot load the pinned landscape implementation: {_VENDOR_FILE}")
_MPB = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MPB)


DEFAULT_CONFIG = {
    "dimension": 5, "npeaks": 10, "period": 5000,
    "move_severity": 1.0, "correlation": 0.0, "budget": 500000,
    "environment_seed": 0, "optimizer_seed": 1,
    "particles_per_swarm": 5, "nexcess": 1,
    "trace_interval": 100, "snapshot_interval": 0, "progress_interval": 5000,
    "bounds": [0.0, 100.0], "height_severity": 7.0, "width_severity": 1.0,
    "chi": 0.729843788, "c": 2.05,
}


@dataclass
class Particle:
    position: list[float]
    velocity: list[float]
    best: list[float] | None = None
    best_fitness: float | None = None
    fitness: float | None = None


@dataclass
class Swarm:
    identifier: int
    particles: list[Particle]
    best: list[float] | None = None
    best_fitness: float | None = None
    last_response_eval: int = 0
    previous_response_radius: float = 0.0
    previous_response_center: list[float] | None = None
    recent_improvement: float = 0.0


class BudgetExhausted(Exception):
    """Internal control flow: every objective access uses the same budget."""


def sample_uvd(rng: random.Random, center: list[float], radius: float) -> list[float]:
    """Uniform-volume sampling from the book, p. 199; handles zero radius."""
    if radius == 0:
        return list(center)
    direction = [rng.gauss(0, 1) for _ in center]
    norm = math.sqrt(sum(x * x for x in direction))
    # A zero Gaussian vector has probability zero theoretically, but can be
    # returned by a deterministic testing RNG. Redraw, rather than divide by 0.
    while norm == 0:
        direction = [rng.gauss(0, 1) for _ in center]
        norm = math.sqrt(sum(x * x for x in direction))
    scale = radius * rng.random() ** (1.0 / len(center)) / norm
    return [c + scale * x for c, x in zip(center, direction)]


def _distance(a, b) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _diameter(swarm: Swarm) -> float:
    return max((_distance(a.position, b.position)
                for a, b in itertools.combinations(swarm.particles, 2)), default=0.0)


def _validated_config(config: dict) -> dict:
    unknown = set(config) - set(DEFAULT_CONFIG)
    if unknown:
        raise ValueError(f"Unknown case configuration: {sorted(unknown)}")
    cfg = {**DEFAULT_CONFIG, **config}
    for key in ("dimension", "npeaks", "budget", "particles_per_swarm", "nexcess"):
        if isinstance(cfg[key], bool) or not isinstance(cfg[key], int) or cfg[key] < 1:
            raise ValueError(f"{key} must be a positive integer")
    for key in ("period", "trace_interval", "snapshot_interval", "progress_interval"):
        if isinstance(cfg[key], bool) or not isinstance(cfg[key], int) or cfg[key] < 0:
            raise ValueError(f"{key} must be a nonnegative integer")
    if len(cfg["bounds"]) != 2 or not all(math.isfinite(v) for v in cfg["bounds"]):
        raise ValueError("bounds must contain two finite numbers")
    if cfg["bounds"][0] >= cfg["bounds"][1]:
        raise ValueError("bounds must be strictly increasing")
    cfg["bounds"] = [float(v) for v in cfg["bounds"]]
    for key in ("move_severity", "height_severity", "width_severity", "chi", "c"):
        if not math.isfinite(cfg[key]) or cfg[key] < 0:
            raise ValueError(f"{key} must be finite and nonnegative")
    if not 0 <= cfg["correlation"] <= 1:
        raise ValueError("correlation must lie in [0, 1]")
    return cfg


def run_case(config: dict, policy: Callable | None = None,
             progress: Callable | None = None, *, retention_priority: Callable | None = None) -> dict:
    """Execute one case and return JSONable measurements and behavioral traces.

    ``policy(observation)`` is called only after change is detected by an
    ordinary, counted reevaluation. It returns radius_scale, fraction, memory
    and reset_velocity; omitted fields use the book policy defaults. Candidate
    observations contain no true peak positions, optimum, error or RNG seed.

    The optional particle-retention hook scores immutable refreshed snapshots
    after all five memory queries and before movement. It requires the fixed
    four-particle, radius-1.25, reevaluate/retain response. Omitted hooks preserve
    the original numerical path, including its optimizer RNG consumption.

    ``progress(event_dict)`` receives run_started, environment_change, progress,
    and run_completed events. Exceptions from policies/callbacks are propagated.
    Every objective call, including initialization, detection, memory refresh
    and exclusion, consumes one evaluation. Runs terminate at exactly budget.
    """
    cfg = _validated_config(config)
    choose_response = policy or book_response
    rng = random.Random(cfg["optimizer_seed"])
    env_rng = random.Random(cfg["environment_seed"])
    if retention_priority is not None:
        if not callable(retention_priority) or cfg["particles_per_swarm"] != 5:
            raise ValueError("Retention hook requires a callable priority and five particles")
        from .particle_retention import (retention_snapshot, select_retained_particle,
                                         selection_rng_for_seed)
        selection_rng = selection_rng_for_seed(cfg["optimizer_seed"])
    retention_example_initial_done = retention_example_late_done = False
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
    population: list[Swarm] = []
    next_identifier = 0
    epoch = 0
    epoch_error_sum = 0.0
    epoch_eval_count = 0
    epoch_first_error = None
    epoch_first_eval = 1

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
                                      "particles": [list(p.position) for p in s.particles]}
                                     for s in population],
                          "landscape": environment_state()})

    def evaluate(position, kind):
        nonlocal epoch, epoch_error_sum, epoch_eval_count, epoch_first_error, epoch_first_eval
        if landscape.nevals >= cfg["budget"]:
            raise BudgetExhausted
        if not all(math.isfinite(x) for x in position):
            raise ValueError("Non-finite particle position")
        optimum = (landscape.globalMaximum()[0] if landscape._optimum is None
                   else landscape._optimum)
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
                     "offline_error": landscape.offlineError(),
                     "swarm_count": len(population), "next_environment": environment_state()}
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
            for _ in range(cfg["particles_per_swarm"])], previous_response_radius=default_radius)
        next_identifier += 1
        return swarm

    def update_attractors(swarm, particle, value):
        particle.fitness = value
        if particle.best_fitness is None or value > particle.best_fitness:
            particle.best, particle.best_fitness = list(particle.position), value
        if swarm.best_fitness is None or value > swarm.best_fitness:
            if swarm.best_fitness is not None:
                swarm.recent_improvement += value - swarm.best_fitness
            swarm.best, swarm.best_fitness = list(particle.position), value

    def initialize_swarm(swarm, kind):
        for particle in swarm.particles:
            update_attractors(swarm, particle, evaluate(particle.position, kind))

    def update_swarm(swarm):
        nonlocal retention_example_initial_done, retention_example_late_done
        response_entry = None
        selected = set()
        decision = None
        try:
            if swarm.best is not None:
                previous_fitness = swarm.best_fitness
                current_fitness = evaluate(swarm.best, "detection")
                if current_fitness != previous_fitness:
                    observation = {
                        "dimension": cfg["dimension"], "bounds_width": width,
                        "swarm_size": len(swarm.particles), "swarm_count": len(population),
                        "swarm_diameter": _diameter(swarm),
                        "previous_best_fitness": previous_fitness, "current_best_fitness": current_fitness,
                        "fitness_drop": previous_fitness - current_fitness,
                        "relative_fitness_drop": (previous_fitness - current_fitness) / max(1.0, abs(previous_fitness)),
                        "recent_improvement": swarm.recent_improvement,
                        "evaluations_since_response": landscape.nevals - swarm.last_response_eval,
                        "previous_response_radius": swarm.previous_response_radius,
                        "default_radius": default_radius,
                        "observed_best_displacement": (0.0 if swarm.previous_response_center is None
                                                       else _distance(swarm.best, swarm.previous_response_center)),
                        "evals_remaining": cfg["budget"] - landscape.nevals,
                    }
                    decision = normalize_response(choose_response(dict(observation)))
                    radius = default_radius * decision["radius_scale"]
                    if not math.isfinite(radius):
                        raise ValueError("Response radius overflow")
                    nselected = math.ceil(decision["fraction"] * len(swarm.particles))
                    if retention_priority is None:
                        selected = set(range(len(swarm.particles))) if nselected == len(swarm.particles) else set(
                            rng.sample(range(len(swarm.particles)), nselected))
                    elif (nselected != 4 or decision["radius_scale"] != 1.25
                          or decision["memory"] != "reevaluate" or decision["reset_velocity"]):
                        raise ValueError("Retention hook requires count four, radius 1.25, memory reevaluation and retained velocity")
                    response_entry = {"swarm_id": swarm.identifier,
                                      "detected_at_evaluation": landscape.nevals,
                                      "observation": observation, "decision": decision,
                                      "radius": radius, "relocated_indices": sorted(selected),
                                      "center_before_refresh": list(swarm.best), "completed": False}
                    response_log.append(response_entry)
                    swarm.last_response_eval = landscape.nevals
                    swarm.previous_response_radius = radius
                    swarm.previous_response_center = list(swarm.best)
                    if decision["memory"] == "reevaluate":
                        for particle in swarm.particles:
                            if particle.best is not None:
                                particle.best_fitness = evaluate(particle.best, "memory")
                        best_particle = max(swarm.particles, key=lambda p: p.best_fitness
                                            if p.best_fitness is not None else -math.inf)
                        swarm.best, swarm.best_fitness = list(best_particle.best), best_particle.best_fitness
                        if retention_priority is not None:
                            try:
                                features, shared = retention_snapshot(swarm.particles, swarm.best, observation)
                                retention = select_retained_particle(retention_priority, features, shared, selection_rng)
                            except Exception as exc:
                                exc.objective_queries = landscape.nevals
                                exc.evaluation_counts = dict(counts)
                                raise
                            retained_index = retention["selected_index"]
                            selected = set(range(5)) - {retained_index}
                            response_entry["relocated_indices"] = sorted(selected)
                            retained = swarm.particles[retained_index]
                            retention.update(decided_at_evaluation=landscape.nevals,
                                selected_before={"position": list(retained.position), "velocity": list(retained.velocity)},
                                selected_after=None, selected_update_reached=False, selected_objective_queried=False)
                            criteria = []
                            if not retention_example_initial_done:
                                criteria.append("first_completed_response")
                            if landscape.nevals >= 50000 and not retention_example_late_done:
                                criteria.append("first_completed_response_at_or_after_50000_queries")
                            if criteria:
                                retention["example"] = {"criteria": criteria,
                                    "particles_before": [{"position": list(p.position), "velocity": list(p.velocity)}
                                                         for p in swarm.particles], "particles_after": None}
                            response_entry["retention"] = retention
                    else:
                        for particle in swarm.particles:
                            particle.best = particle.best_fitness = None
                        swarm.best = swarm.best_fitness = None

            swarm.recent_improvement = 0.0
            for index, particle in enumerate(swarm.particles):
                if (response_entry is not None and "retention" in response_entry
                        and index == response_entry["retention"]["selected_index"]):
                    response_entry["retention"]["selected_update_reached"] = True
                if index in selected:
                    center = (swarm.best if swarm.best is not None
                              else response_entry["center_before_refresh"])
                    particle.position = sample_uvd(rng, center, response_entry["radius"])
                    if decision["reset_velocity"]:
                        particle.velocity = [0.0] * cfg["dimension"]
                elif swarm.best is not None and particle.best is not None:
                    for dim in range(cfg["dimension"]):
                        attraction = cfg["c"] * rng.random() * (swarm.best[dim] - particle.position[dim])
                        attraction += cfg["c"] * rng.random() * (particle.best[dim] - particle.position[dim])
                        particle.velocity[dim] = cfg["chi"] * (particle.velocity[dim] + attraction)
                        particle.position[dim] += particle.velocity[dim]
                update_attractors(swarm, particle, evaluate(particle.position, "particle"))
                if (response_entry is not None and "retention" in response_entry
                        and index == response_entry["retention"]["selected_index"]):
                    response_entry["retention"]["selected_objective_queried"] = True
            if response_entry is not None:
                response_entry["completed"] = True
                if "retention" in response_entry and "example" in response_entry["retention"]:
                    criteria = response_entry["retention"]["example"]["criteria"]
                    retention_example_initial_done |= "first_completed_response" in criteria
                    retention_example_late_done |= "first_completed_response_at_or_after_50000_queries" in criteria
        finally:
            if response_entry is not None:
                response_entry["finished_at_evaluation"] = landscape.nevals
                response_entry["evaluations_after_detection"] = landscape.nevals - response_entry["detected_at_evaluation"]
                if "retention" in response_entry:
                    retention = response_entry["retention"]
                    retained = swarm.particles[retention["selected_index"]]
                    retention["selected_after"] = {"position": list(retained.position), "velocity": list(retained.velocity)}
                    if "example" in retention:
                        if response_entry["completed"]:
                            retention["example"]["particles_after"] = [
                                {"position": list(p.position), "velocity": list(p.velocity)} for p in swarm.particles]
                        else:
                            del retention["example"]

    variant = f"book_mpso_{cfg['particles_per_swarm']}_plus_0"
    emit("run_started", config=cfg, baseline=variant, budget=cfg["budget"])
    iterations = 0
    population.append(make_swarm())
    if cfg["snapshot_interval"]:
        add_snapshot()
    try:
        initialize_swarm(population[0], "initialization")
        while landscape.nevals < cfg["budget"]:
            iterations += 1
            # Same radius/diameter convention as the pinned DEAP implementation.
            exclusion_radius = width / (2 * len(population) ** (1.0 / cfg["dimension"]))
            free_swarms = [s for s in population if _diameter(s) > 2 * exclusion_radius]
            if not free_swarms:
                population.append(make_swarm())
            elif len(free_swarms) > cfg["nexcess"]:
                worst = min(free_swarms, key=lambda s: s.best_fitness
                            if s.best_fitness is not None else -math.inf)
                population.remove(worst)
            for swarm in population:
                update_swarm(swarm)
            reinitialize = set()
            for i, j in itertools.combinations(range(len(population)), 2):
                a, b = population[i], population[j]
                if i in reinitialize or j in reinitialize or a.best is None or b.best is None:
                    continue
                if _distance(a.best, b.best) < exclusion_radius:
                    reinitialize.add(i if a.best_fitness <= b.best_fitness else j)
            for i in sorted(reinitialize):
                population[i] = make_swarm()
                initialize_swarm(population[i], "exclusion")
    except BudgetExhausted:
        pass
    if cfg["snapshot_interval"]:
        add_snapshot()
    result = {"config": cfg, "baseline_variant": variant,
              "policy_name": getattr(choose_response, "__name__", type(choose_response).__name__),
              "evaluations": landscape.nevals, "evaluation_counts": dict(counts),
              "offline_error": landscape.offlineError(), "final_error": landscape.currentError(),
              "iterations": iterations, "final_swarm_count": len(population),
              "environments_evaluated": (1 + (landscape.nevals - 1) // cfg["period"] if cfg["period"] else 1),
              "initial_environment": initial_environment, "environment_changes": environment_changes,
              "trace": trace, "response_log": response_log, "snapshots": snapshots,
              "partial_environment": ({"environment": epoch, "evaluations": epoch_eval_count,
                                       "offline_error": epoch_error_sum / epoch_eval_count,
                                       "initial_error": epoch_first_error,
                                       "final_error": landscape.currentError()} if epoch_eval_count else None)}
    assert result["evaluations"] == cfg["budget"] == sum(counts.values())
    emit("run_completed", evaluations=landscape.nevals, offline_error=result["offline_error"],
         response_count=len(response_log), swarm_count=len(population))
    return result
