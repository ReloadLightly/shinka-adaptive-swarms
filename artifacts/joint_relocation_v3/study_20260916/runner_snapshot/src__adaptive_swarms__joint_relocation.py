"""V3 joint relocation decisions, adapted to the unchanged numerical simulator.

An integer allocation and a radius multiplier are the only candidate outputs.
Memory reevaluation and retained velocities remain fixed. Requested allocation,
selected particles, and objective queries are recorded as distinct quantities.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable
import hashlib
import importlib.util
import math
from pathlib import Path

from .cli import simulator_fingerprint

ADAPTER_VERSION = "interior_fraction_joint_relocation_v3"


def joint_fingerprint() -> dict:
    """Identify the numerical sources and this independently versioned adapter."""
    return {**simulator_fingerprint(),
            "src/adaptive_swarms/joint_relocation.py":
                hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def validate_decision(value, swarm_size: int) -> dict:
    if type(swarm_size) is not int or swarm_size < 1:
        raise ValueError("swarm_size must be a positive Python int")
    if type(value) is not dict or set(value) != {"count", "radius_scale"}:
        raise ValueError("choose_relocation must return a dict with exactly count and radius_scale")
    count = value["count"]
    if type(count) is not int:
        raise ValueError("count must be a Python int (not bool or float)")
    if not 0 <= count <= swarm_size:
        raise ValueError(f"Relocation count {count} is outside [0, {swarm_size}]")
    radius_scale = value["radius_scale"]
    if type(radius_scale) not in (int, float):
        raise ValueError("radius_scale must be a finite nonnegative number (not bool)")
    try:
        radius_scale = float(radius_scale)
    except (OverflowError, ValueError) as exc:
        raise ValueError("radius_scale must be a finite nonnegative number") from exc
    if not math.isfinite(radius_scale) or radius_scale < 0:
        raise ValueError("radius_scale must be a finite nonnegative number")
    return {"count": count, "radius_scale": radius_scale}


class JointRelocationAdapter:
    """Validate the candidate action and encode its exact integer allocation."""

    def __init__(self, choose_relocation: Callable[[dict], dict]):
        if not callable(choose_relocation):
            raise TypeError("Joint relocation policy must be callable")
        self.choose_relocation = choose_relocation
        self.requested_decisions: list[dict] = []

    def __call__(self, observation: dict) -> dict:
        # All public observations are scalar. The copy prevents accidental
        # mutation of fixed adapter inputs while the candidate is called.
        action = validate_decision(self.choose_relocation(dict(observation)),
                                   observation["swarm_size"])
        count, size = action["count"], observation["swarm_size"]
        fraction = (count - 0.5) / size if count else 0.0
        if math.ceil(fraction * size) != count:
            raise ValueError("Interior fraction failed to encode the requested count")
        self.requested_decisions.append(action)
        return {"radius_scale": action["radius_scale"], "fraction": fraction,
                "memory": "reevaluate", "reset_velocity": False}


def joint_policy_adapter(choose_relocation: Callable[[dict], dict]) -> JointRelocationAdapter:
    return JointRelocationAdapter(choose_relocation)


def load_joint_policy(path: str | Path) -> Callable[[dict], dict]:
    """Load a fresh module for each independent case, without module reuse."""
    spec = importlib.util.spec_from_file_location("candidate_joint_relocation", Path(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load candidate: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    policy = getattr(module, "choose_relocation", None)
    if not callable(policy):
        raise ValueError("Candidate must define choose_relocation(observation)")
    return policy


def constant_joint_policy(count: int, radius_scale: float) -> Callable[[dict], dict]:
    # Validate the action independently of a future simulator observation.
    action = validate_decision({"count": count, "radius_scale": radius_scale},
                               max(1, count) if type(count) is int else 1)

    def choose_relocation(observation: dict) -> dict:
        return validate_decision(action, observation["swarm_size"])

    return choose_relocation


def annotate_joint_log(result: dict, adapter: JointRelocationAdapter) -> dict:
    """Distinguish intended allocation, selected indices and queried relocations.

    At a detected change, every particle in this reevaluate-only task already
    has a personal memory. The simulator queries those memories first, then
    visits particles in index order. This permits exact query accounting even
    when the objective budget interrupts the final response. It does not claim
    that every allocated particle has already been moved or evaluated.
    """
    responses = result["response_log"]
    if len(responses) != len(adapter.requested_decisions):
        raise ValueError("Requested action log and simulator responses differ")
    for response, requested in zip(responses, adapter.requested_decisions):
        allocated = len(response["relocated_indices"])
        if allocated != requested["count"]:
            raise ValueError(f"Requested {requested['count']} relocations; simulator allocated {allocated}")
        if response["decision"]["radius_scale"] != requested["radius_scale"]:
            raise ValueError("Requested and simulator radius multipliers differ")
        size = response["observation"]["swarm_size"]
        evaluated_particles = max(0, min(size, response["evaluations_after_detection"] - size))
        response.update(
            requested_count=requested["count"], allocated_count=allocated,
            evaluated_relocation_count=sum(
                index < evaluated_particles for index in response["relocated_indices"]),
            requested_radius_scale=requested["radius_scale"],
            allocated_fraction=allocated / size,
            adapter_encoding_fraction=response["decision"]["fraction"],
        )
    result["joint_relocation_interface"] = {
        "version": ADAPTER_VERSION, "memory": "reevaluate", "reset_velocity": False,
        "allocated_count_semantics": "number of selected particle indices; not a claim of completed movement",
        "evaluated_relocation_count_semantics": "selected particles with an objective query during this response",
        "allocated_fraction_semantics": "allocated_count / swarm_size",
        "adapter_encoding_fraction_semantics": "interior encoding for simulator ceiling rule, not the allocated fraction",
        "radius_semantics": "default_radius * requested_radius_scale; default_radius retains the known baseline severity scale",
    }
    return result


def joint_diagnostics(result: dict) -> dict:
    """Case-level summaries; response records are repeated measurements."""
    responses = result["response_log"]
    size = result["config"]["particles_per_swarm"]
    summary = {"incomplete_responses": sum(not item["completed"] for item in responses)}
    for field in ("requested_count", "allocated_count", "evaluated_relocation_count"):
        counts = Counter(item[field] for item in responses)
        summary[field + "_distribution"] = {str(k): counts[k] for k in range(size + 1)}
    return summary
