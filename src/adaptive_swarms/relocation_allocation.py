"""The v2 integer-allocation interface; the numerical simulator is unchanged.

Only optimizer-visible observations reach the candidate. Selection count is
recorded separately from horizon-truncated, objectively evaluated relocations.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable
import hashlib
import importlib.util
import math
from pathlib import Path

from .cli import simulator_fingerprint

ADAPTER_VERSION = "interior_fraction_integer_allocation_v2"


def allocation_fingerprint() -> dict:
    """Identify the unchanged simulator and the fixed v2 intervention."""
    return {**simulator_fingerprint(),
            "src/adaptive_swarms/relocation_allocation.py":
                hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def validate_count(value, swarm_size: int) -> int:
    if type(value) is not int:
        raise ValueError("choose_relocation_count must return an int (not bool or float)")
    if type(swarm_size) is not int or swarm_size < 1:
        raise ValueError("swarm_size must be a positive int")
    if not 0 <= value <= swarm_size:
        raise ValueError(f"Relocation count {value} is outside [0, {swarm_size}]")
    return value


class CountPolicyAdapter:
    """Adapt exact integer decisions to the existing response-policy interface."""

    def __init__(self, choose_count: Callable[[dict], int]):
        if not callable(choose_count):
            raise TypeError("Count policy must be callable")
        self.choose_count = choose_count
        self.requested_counts: list[int] = []

    def __call__(self, observation: dict) -> dict:
        # Copy prevents candidate mutation from changing fixed adapter inputs.
        count = validate_count(self.choose_count(dict(observation)), observation["swarm_size"])
        size = observation["swarm_size"]
        fraction = (count - 0.5) / size if count else 0.0
        if math.ceil(fraction * size) != count:
            raise ValueError("Interior fraction failed to encode the requested count")
        self.requested_counts.append(count)
        return {"radius_scale": 2.0, "fraction": fraction,
                "memory": "reevaluate", "reset_velocity": False}


def count_policy_adapter(choose_count: Callable[[dict], int]) -> CountPolicyAdapter:
    return CountPolicyAdapter(choose_count)


def load_count_policy(path: str | Path) -> Callable[[dict], int]:
    """Load a fresh candidate module for each independent case."""
    spec = importlib.util.spec_from_file_location("candidate_allocation", Path(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load candidate: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    policy = getattr(module, "choose_relocation_count", None)
    if not callable(policy):
        raise ValueError("Candidate must define choose_relocation_count(observation)")
    return policy


def constant_count_policy(count: int) -> Callable[[dict], int]:
    validate_count(count, 5)

    def choose_count(observation: dict) -> int:
        return validate_count(count, observation["swarm_size"])

    return choose_count


def annotate_count_log(result: dict, adapter: CountPolicyAdapter) -> dict:
    """Save requested and simulator-selected counts without altering simulation.

    ``executed_count`` is the simulator's actual ceil/fraction allocation,
    obtained from its selected particle indices. A final partial response can
    exhaust its budget during memory refresh or particle updates; the additional
    ``evaluated_relocation_count`` counts selected particles with an objective
    query during this response, rather than claiming a completed conversion.
    """
    responses = result["response_log"]
    if len(responses) != len(adapter.requested_counts):
        raise ValueError("Requested count log and simulator responses differ")
    for response, requested in zip(responses, adapter.requested_counts):
        executed = len(response["relocated_indices"])
        if executed != requested:
            raise ValueError(f"Requested {requested} relocations; simulator allocated {executed}")
        size = response["observation"]["swarm_size"]
        # All personal memories exist at a detected change in this fixed,
        # reevaluate-only task. Their queries precede the particle queries.
        evaluated_particles = max(0, min(size, response["evaluations_after_detection"] - size))
        response.update(requested_count=requested, executed_count=executed,
                        evaluated_relocation_count=sum(
                            index < evaluated_particles for index in response["relocated_indices"]))
    result["allocation_interface"] = {
        "version": ADAPTER_VERSION,
        "executed_count_semantics": "actual simulator-selected allocation; incomplete responses remain flagged",
        "radius_scale": 2.0, "memory": "reevaluate", "reset_velocity": False,
    }
    return result


def count_diagnostics(result: dict) -> dict:
    """Case-level allocation summaries; responses are repeated measurements."""
    responses = result["response_log"]
    size = result["config"]["particles_per_swarm"]
    requested = Counter(response["requested_count"] for response in responses)
    executed = Counter(response["executed_count"] for response in responses)
    evaluated = Counter(response["evaluated_relocation_count"] for response in responses)
    return {
        "requested_count_distribution": {str(k): requested[k] for k in range(size + 1)},
        "executed_count_distribution": {str(k): executed[k] for k in range(size + 1)},
        "evaluated_relocation_count_distribution": {str(k): evaluated[k] for k in range(size + 1)},
        "incomplete_responses": sum(not response["completed"] for response in responses),
    }
