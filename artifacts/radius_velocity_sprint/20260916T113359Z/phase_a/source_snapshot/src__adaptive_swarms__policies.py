"""Source-grounded baseline policies and the candidate response contract."""

import math
from collections.abc import Mapping


def book_response(observation: dict) -> dict:
    """The chapter's one-iteration conversion, with attractor reevaluation."""
    return {"radius_scale": 1.0, "fraction": 1.0,
            "memory": "reevaluate", "reset_velocity": False}


def no_relocation_response(observation: dict) -> dict:
    """Ablation retaining change detection and attractor reevaluation."""
    return {"radius_scale": 1.0, "fraction": 0.0,
            "memory": "reevaluate", "reset_velocity": False}


def normalize_response(value: Mapping) -> dict:
    """Validate a candidate decision; invalid decisions fail explicitly."""
    if not isinstance(value, Mapping):
        raise ValueError("choose_response must return a mapping")
    allowed = {"radius_scale", "fraction", "memory", "reset_velocity"}
    if set(value) - allowed:
        raise ValueError(f"Unknown response keys: {sorted(set(value) - allowed)}")
    response = {**book_response({}), **value}
    for key in ("radius_scale", "fraction"):
        number = response[key]
        if isinstance(number, bool) or not isinstance(number, (int, float)):
            raise ValueError(f"{key} must be a finite number")
        if not math.isfinite(number) or number < 0:
            raise ValueError(f"{key} must be finite and nonnegative")
        response[key] = float(number)
    if response["fraction"] > 1:
        raise ValueError("fraction must lie in [0, 1]")
    if response["memory"] not in {"reevaluate", "reset"}:
        raise ValueError("memory must be 'reevaluate' or 'reset'")
    if not isinstance(response["reset_velocity"], bool):
        raise ValueError("reset_velocity must be Boolean")
    return response
