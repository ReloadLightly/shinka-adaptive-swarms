"""Immutable refreshed-particle features and pure retention priorities.

The scalar score selects the single exempt particle; larger scores retain it.
Selection randomness is separate from numerical PSO and landscape RNGs.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import math
from pathlib import Path
import random
from types import MappingProxyType

from .cli import simulator_fingerprint

INTERFACE_VERSION = "particle_retention_v1_refreshed_snapshot"
SELECTION_RNG_VERSION = "sha256_particle_retention_v1_selection_optimizer_seed"


class RetentionPolicyError(ValueError):
    """Invalid pure priority; simulator attaches exact consumed-query evidence."""


def retention_fingerprint():
    return {**simulator_fingerprint(), "src/adaptive_swarms/particle_retention.py":
            hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def fixed_retention_response(observation):
    if observation["swarm_size"] != 5:
        raise ValueError("Particle retention task requires five particles")
    return {"radius_scale": 1.25, "fraction": 0.7, "memory": "reevaluate", "reset_velocity": False}


def selection_rng_for_seed(optimizer_seed):
    payload = f"particle_retention_v1_selection:{optimizer_seed}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def best_memory_priority(particle_features, swarm_features):
    return -particle_features["personal_best_rank"]


def random_priority(particle_features, swarm_features):
    return 0.0


def retention_snapshot(particles, best_position, observation):
    """Freeze public state after all counted memory refreshes and before movement.

    Personal-best fitness values are the actual sequential observations. A
    landscape can change during refresh; no hidden freshness oracle is supplied.
    Competition ranks assign equal values equal ranks: one plus the number of
    strictly better remembered fitnesses. Rank one is best; (rank-1)/4 normalizes.
    """
    if len(particles) != 5 or any(p.best is None or p.best_fitness is None for p in particles):
        raise ValueError("Retention snapshot requires five refreshed personal memories")
    center = tuple(float(v) for v in best_position)
    positions = [tuple(float(v) for v in p.position) for p in particles]
    velocities = [tuple(float(v) for v in p.velocity) for p in particles]
    fitness = [float(p.best_fitness) for p in particles]
    if not all(math.isfinite(v) for row in positions + velocities + [center, fitness] for v in row):
        raise ValueError("Non-finite public retention state")
    scale = max(float(observation["default_radius"]), 1e-12)
    speeds = [math.hypot(*v) for v in velocities]
    diameter = max(math.dist(a, b) for a in positions for b in positions)
    swarm = MappingProxyType({"dimension": len(center), "swarm_size": 5,
        "default_radius": float(observation["default_radius"]), "diameter": diameter,
        "diameter_normalized": diameter / scale,
        "relative_fitness_drop": float(observation["relative_fitness_drop"]),
        "mean_speed_normalized": math.fsum(speeds) / (5 * scale)})
    features = []
    for position, velocity, value, speed in zip(positions, velocities, fitness, speeds):
        distance = math.dist(position, center)
        rank = 1 + sum(other > value for other in fitness)
        alignment = (math.fsum((c - x) / distance * (v / speed)
                              for c, x, v in zip(center, position, velocity))
                     if distance > 0 and speed > 0 else 0.0)
        features.append(MappingProxyType({"personal_best_fitness": value,
            "personal_best_rank": rank, "personal_best_rank_fraction": (rank - 1) / 4,
            "distance_to_best": distance, "distance_to_best_normalized": distance / scale,
            "speed": speed, "speed_normalized": speed / scale,
            "velocity_alignment": max(-1.0, min(1.0, alignment)),
            "relative_position_normalized": tuple((x - c) / scale for x, c in zip(position, center)),
            "velocity_normalized": tuple(v / scale for v in velocity)}))
    return tuple(features), swarm


def select_retained_particle(priority, particle_features, swarm_features, selection_rng):
    """Score a frozen snapshot, using one permutation regardless of score ties."""
    tie_order = selection_rng.sample(range(5), 5)
    scores = []
    for features in particle_features:
        try:
            value = priority(features, swarm_features)
            if type(value) not in (int, float) or not math.isfinite(float(value)):
                raise ValueError("retention_priority must return a finite Python number, not bool")
            scores.append(float(value))
        except Exception as exc:
            raise RetentionPolicyError(f"Invalid retention priority: {type(exc).__name__}: {exc}") from exc
    selected = max(tie_order, key=lambda index: scores[index])
    heuristic = max(tie_order, key=lambda index: best_memory_priority(particle_features[index], swarm_features))
    return {"selected_index": selected, "heuristic_index": heuristic,
            "agrees_with_heuristic": selected == heuristic, "scores": scores, "tie_order": tie_order,
            "features": [dict(features) for features in particle_features], "swarm_features": dict(swarm_features)}


def inspect_priority_source(source):
    """Reject external access and state mutation before importing a candidate.

    This is a narrow pure-expression contract check, not a Python security sandbox.
    Exact selected programs additionally receive scientific source review.
    """
    tree = ast.parse(source)
    functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    if "retention_priority" not in functions:
        raise RetentionPolicyError("Candidate must define retention_priority(particle_features, swarm_features)")
    imported = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            if any(alias.name != "math" or alias.asname not in (None, "math") for alias in node.names):
                raise RetentionPolicyError("Only import math is permitted")
        elif isinstance(node, ast.ImportFrom):
            if node.module != "math" or node.level or any(alias.asname or alias.name.startswith('_') for alias in node.names):
                raise RetentionPolicyError("Only explicit math imports are permitted")
            imported.update(alias.name for alias in node.names)
        elif not isinstance(node, (ast.FunctionDef, ast.Expr)) or isinstance(node, ast.Expr) and not isinstance(node.value, ast.Constant):
            raise RetentionPolicyError("Only pure function definitions, docstrings and math imports are permitted at module scope")
    allowed_calls = {"abs", "min", "max", "float", "int", "bool", "sum", "len", "round", "pow", "tuple", "range", "sorted"} | functions | imported
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(part, ast.Attribute) for target in targets for part in ast.walk(target)):
                raise RetentionPolicyError("Mutation of imported or external state is outside the pure priority contract")
        if isinstance(node, ast.FunctionDef):
            if node.decorator_list or node.args.defaults or any(v is not None for v in node.args.kw_defaults):
                raise RetentionPolicyError("Decorators and mutable/default function state are outside the pure priority contract")
            if node.name == "retention_priority" and (len(node.args.args) != 2 or node.args.posonlyargs or node.args.vararg or node.args.kwarg or node.args.kwonlyargs):
                raise RetentionPolicyError("retention_priority requires exactly two feature arguments")
        if isinstance(node, (ast.Import, ast.ImportFrom)) and node not in tree.body:
            raise RetentionPolicyError("Imports must be explicit math imports at module scope")
        if isinstance(node, (ast.Global, ast.Nonlocal, ast.With, ast.AsyncWith, ast.AsyncFunctionDef,
                             ast.ClassDef, ast.Delete, ast.While, ast.Yield, ast.YieldFrom, ast.Await)):
            raise RetentionPolicyError("External or mutable execution state is outside the priority contract")
        if isinstance(node, ast.Attribute):
            math_attr = isinstance(node.value, ast.Name) and node.value.id == "math" and not node.attr.startswith('_')
            mapping_get = isinstance(node.value, ast.Name) and node.value.id in {"particle_features", "swarm_features"} and node.attr == "get"
            if not (math_attr or mapping_get):
                raise RetentionPolicyError("Only math operations and public feature lookup are permitted")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id not in allowed_calls:
            raise RetentionPolicyError(f"Unapproved call in pure priority: {node.func.id}")
        if isinstance(node, ast.Call) and not isinstance(node.func, (ast.Name, ast.Attribute)):
            raise RetentionPolicyError("Indirect calls are outside the pure priority contract")
    return tree


def load_retention_priority(path):
    path = Path(path)
    try:
        inspect_priority_source(path.read_text())
        spec = importlib.util.spec_from_file_location("candidate_particle_retention", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load retention priority: {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.retention_priority
    except Exception as exc:
        exc.objective_queries = 0
        raise
