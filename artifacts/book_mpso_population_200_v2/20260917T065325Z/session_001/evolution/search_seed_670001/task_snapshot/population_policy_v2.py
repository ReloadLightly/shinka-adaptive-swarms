"""Unchanged population interface with the corrected-engine source identity."""
from __future__ import annotations

import hashlib
from pathlib import Path

from .cli import simulator_fingerprint
from .population_policy import (
    INTERFACE_VERSION, PopulationPolicyError, inspect_population_source,
    load_population_policy, validated_target,
)


def population_fingerprint():
    """No historical diameter-engine record can match this scientific identity."""
    root = Path(__file__).resolve().parents[2]
    paths = (
        "src/adaptive_swarms/population_policy.py",
        "src/adaptive_swarms/population_policy_v2.py",
        "src/adaptive_swarms/book_population_v2.py",
        "src/adaptive_swarms/enclosing_ball.py",
        "src/adaptive_swarms/book_mpso.py",
    )
    return {**simulator_fingerprint(), **{
        path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in paths}}
