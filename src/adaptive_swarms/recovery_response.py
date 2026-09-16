"""Sprint-local radius/velocity response; four allocations and memory are fixed.

This adapter leaves the numerical simulator and historical V3 contract intact.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable
import hashlib
import importlib.util
import math
from pathlib import Path

from .cli import simulator_fingerprint

ADAPTER_VERSION = "fixed_four_radius_velocity_sprint_v1"
FIXED_COUNT = 4


def recovery_fingerprint() -> dict:
    return {**simulator_fingerprint(), "src/adaptive_swarms/recovery_response.py":
            hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def validate_recovery_decision(value) -> dict:
    if type(value) is not dict or set(value) != {"radius_scale", "reset_velocity"}:
        raise ValueError("choose_recovery must return exactly radius_scale and reset_velocity")
    radius = value["radius_scale"]
    if type(radius) not in (int, float):
        raise ValueError("radius_scale must be a finite nonnegative Python number, not bool")
    try:
        radius = float(radius)
    except (OverflowError, ValueError) as exc:
        raise ValueError("radius_scale must be finite and nonnegative") from exc
    if not math.isfinite(radius) or radius < 0:
        raise ValueError("radius_scale must be finite and nonnegative")
    reset = value["reset_velocity"]
    if type(reset) is not bool:
        raise ValueError("reset_velocity must be a Python bool")
    return {"radius_scale": radius, "reset_velocity": reset}


class RecoveryResponseAdapter:
    def __init__(self, choose_recovery: Callable[[dict], dict]):
        if not callable(choose_recovery):
            raise TypeError("Recovery policy must be callable")
        self.choose_recovery = choose_recovery
        self.requested_decisions: list[dict] = []

    def __call__(self, observation: dict) -> dict:
        size = observation["swarm_size"]
        if type(size) is not int or size < FIXED_COUNT:
            raise ValueError("Fixed-four recovery requires at least four particles")
        action = validate_recovery_decision(self.choose_recovery(dict(observation)))
        fraction = (FIXED_COUNT - 0.5) / size
        if math.ceil(fraction * size) != FIXED_COUNT:
            raise ValueError("Interior fraction failed to encode four particles")
        self.requested_decisions.append(action)
        return {**action, "fraction": fraction, "memory": "reevaluate"}


def recovery_policy_adapter(choose_recovery: Callable[[dict], dict]) -> RecoveryResponseAdapter:
    return RecoveryResponseAdapter(choose_recovery)


def constant_recovery_policy(radius_scale: float, reset_velocity: bool) -> Callable[[dict], dict]:
    action = validate_recovery_decision({"radius_scale": radius_scale, "reset_velocity": reset_velocity})

    def choose_recovery(observation: dict) -> dict:
        return dict(action)

    return choose_recovery


def load_recovery_policy(path: str | Path) -> Callable[[dict], dict]:
    spec = importlib.util.spec_from_file_location("candidate_recovery_response", Path(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load recovery policy: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    policy = getattr(module, "choose_recovery", None)
    if not callable(policy):
        raise ValueError("Candidate must define choose_recovery(observation)")
    return policy


def annotate_recovery_log(result: dict, adapter: RecoveryResponseAdapter) -> dict:
    responses = result["response_log"]
    if len(responses) != len(adapter.requested_decisions):
        raise ValueError("Requested action and simulator response logs differ")
    for response, action in zip(responses, adapter.requested_decisions):
        size = response["observation"]["swarm_size"]
        allocated = len(response["relocated_indices"])
        if allocated != FIXED_COUNT:
            raise ValueError("Simulator did not allocate exactly four particles")
        for key in ("radius_scale", "reset_velocity"):
            if response["decision"][key] != action[key]:
                raise ValueError(f"Requested and simulator {key} differ")
        evaluated = max(0, min(size, response["evaluations_after_detection"] - size))
        response.update(requested_count=FIXED_COUNT, allocated_count=allocated,
                        evaluated_relocation_count=sum(index < evaluated for index in response["relocated_indices"]),
                        requested_radius_scale=action["radius_scale"],
                        requested_reset_velocity=action["reset_velocity"],
                        allocated_fraction=allocated / size,
                        adapter_encoding_fraction=response["decision"]["fraction"])
    result["recovery_response_interface"] = {
        "version": ADAPTER_VERSION, "count": FIXED_COUNT, "memory": "reevaluate",
        "reset_velocity_semantics": "zero velocity only for relocated particles when their update is reached",
        "allocated_count_semantics": "selected indices; horizon may interrupt actual movement or objective queries",
        "allocated_fraction_semantics": "allocated_count / swarm_size",
        "adapter_encoding_fraction_semantics": "interior encoding for ceiling rule; not allocated fraction",
        "radius_semantics": "default_radius * requested_radius_scale; baseline known severity scale retained",
    }
    return result


def recovery_diagnostics(result: dict) -> dict:
    responses = result["response_log"]
    counts = Counter((item["requested_radius_scale"], item["requested_reset_velocity"]) for item in responses)
    return {
        "response_count": len(responses),
        "incomplete_responses": sum(not item["completed"] for item in responses),
        "reset_velocity_count": sum(item["requested_reset_velocity"] for item in responses),
        "observed_action_distribution": [
            {"radius_scale": radius, "reset_velocity": reset, "count": count,
             "fraction": count / len(responses)}
            for (radius, reset), count in sorted(counts.items())],
        "occupancy_semantics": "observed action pairs, not syntactic branch coverage",
    }
