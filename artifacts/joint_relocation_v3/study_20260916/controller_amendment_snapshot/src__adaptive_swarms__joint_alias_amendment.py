"""Explicit, source-bound V3 component-alias amendment and portable receipts.

This module never imports candidates or evaluates objectives. Reviewed partial
output facts do not establish that the original joint policy is constant.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re

from .artifacts import read_json

AMENDMENT_VERSION = "joint-v3-component-alias-amendment-v1"
AMENDMENT_FILE = "controller_amendment.json"
SNAPSHOT_DIR = "controller_amendment_snapshot"
CONTROLLER = "src/adaptive_swarms/joint_study.py"
SUPPORT = "src/adaptive_swarms/joint_alias_amendment.py"
PROOF_VERSION = "joint-v3-reviewed-partial-output-v1"
PROTECTED = ("source_review.json", "validation", "selection.json", "final_cases.json", "final", "analysis.json")

DOMAIN = {
    "particles_per_swarm": 5, "dimension": 5, "move_severity": [1.0, 3.0],
    "default_radius": [0.5, 1.5], "swarm_size_python_type": "int",
    "observations": "Unmodified simulator public scalar observations; finite Python-float distances produced by _distance, not arbitrary custom numeric objects.",
    "distance_bound": "A finite _distance result is sqrt of a finite nonnegative binary64 sum, hence at most sqrt(sys.float_info.max).",
}
COMMON_REASONING = [
    "The exact module contains only a docstring and one ordinary function with safe dict annotations. No imports, decorators, defaults, RNG, persistent state, observation mutation, external access or external side effects occur. Any fresh local response dictionary is not shared state.",
    "The only calls are unshadowed pure numeric builtins. The declared swarm_size is Python int 5, so min/max clamps preserve the branch's Python integer 3 or 4.",
    "The guarded default radius is exactly 0.5 or 1.5. Finite simulator distances are at most sqrt(max_binary64), so division by either radius remains finite. Denominators are positive; all count arithmetic is total on this domain.",
    "All return paths produce exactly count and the source's declared finite constant radius_scale. The whole policy remains state-dependent; only the radius output is constant.",
    "After count replacement, the original pure, total function still returns a valid action; replacing its count leaves the constant pair (replacement, certified radius). Equal actions imply equal optimizer trajectories and objective queries with the same case RNGs. Instruction paths and telemetry labels need not match.",
]
REVIEWED_OUTPUTS = {
    "dc9811577267e4cef6c128d348ad9c2ffd28ffabc34f6f0fdd526cd1fa7632d7": {
        "label": "search_1 generation 26", "outputs": {"radius_scale": 1.25},
        "reasoning": "With d=max(0,observed_best_displacement)/scale finite and nonnegative, 1+d remains finite and positive, and d/(1+d) is finite. The finite threshold determines only count 3 versus 4; radius is always 1.25.",
    },
    "f4047cf27d7484f890ab84e4c35d2caa2a2b52d14f351083fa883591b812ff43": {
        "label": "search_1 generation 27", "outputs": {"radius_scale": 1.25},
        "reasoning": "The threshold 4.5*radius_reference is exactly 2.25 or 6.75. Comparing the finite diameter selects only integer count 3 or 4; radius is always 1.25.",
    },
    "9406700ee6e2cd7fa88df9ab592813fd5f14e56bdef8b8098d5c053f809a74de": {
        "label": "search_1 generation 28", "outputs": {"radius_scale": 1.25},
        "reasoning": "float casts preserve the simulator's scalar values. Diameter/radius_reference is finite and comparing it to 4.5 selects only integer count 3 or 4; clamps preserve that count and radius is always 1.25.",
    },
    "75dbb71c2cd09d9eb960007c9207ad5a35172e235f1435dd79903117d9da95e3": {
        "label": "search_2 generation 21", "outputs": {"radius_scale": 1.5},
        "reasoning": "A fresh local response starts with radius 1.5 and count 4. The early return retains both. Otherwise diameter>3*default_radius>=1.5, so the guarded division has positive denominator and its ratio is in [0,1]. Squaring, coverage and the loss threshold are finite. Only response['count'] can change to 3; every return retains radius 1.5.",
    },
    "acefdf34161e9e666deb778e914d0e3287e74a42642946513cc93ceb73a467ec": {
        "label": "search_2 generation 14", "outputs": {"radius_scale": 1.5},
        "reasoning": "Two finite public-scalar comparisons gate count 3 versus 4. The diameter threshold 3*default_radius is exactly 1.5 or 4.5, and min with swarm_size 5 preserves the valid count. The return always contains literal radius 1.5.",
    },
    "b68862e0f7464e0e8d68b16dd7ee5c2c4a231da5cf28da3b1a486a9ffadd386c": {
        "label": "search_2 generation 23", "outputs": {"radius_scale": 1.5},
        "reasoning": "Two finite public-scalar comparisons gate count 3 versus 4. The diameter threshold 3.5*default_radius is exactly 1.75 or 5.25, and min with swarm_size 5 preserves the valid count. The return always contains literal radius 1.5.",
    },
}
SOURCE_REVIEWS = {
    "search_1": {"path": "operations/search1-source-prereview.json",
                 "sha256": "143e72e74436768a0f3c7a08933b9e272b57125ef2bfa2b8fd9a0ed75b0257d8"},
    "search_2": {"path": "operations/search2-source-prereview.json",
                 "sha256": "ff57d015ee6c0c7382e0c0354d31f4198b7db1d5a4309df162da76f7f389ca27"},
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def registry_fingerprint():
    return digest({"version": PROOF_VERSION, "domain": DOMAIN, "reasoning": COMMON_REASONING,
                   "sources": REVIEWED_OUTPUTS, "source_reviews": SOURCE_REVIEWS})


def reviewed_output_proof(source_sha256):
    fact = REVIEWED_OUTPUTS.get(source_sha256)
    if fact is None:
        return None
    return {"version": PROOF_VERSION, "source_sha256": source_sha256,
            "registry_sha256": registry_fingerprint(), "outputs": deepcopy(fact["outputs"]),
            "domain": deepcopy(DOMAIN), "reasoning": [*COMMON_REASONING, fact["reasoning"]],
            "source_review": deepcopy(SOURCE_REVIEWS[fact["label"].split()[0]]), "label": fact["label"]}


def require_domain(config):
    if type(config.get("particles_per_swarm")) is not int or config["particles_per_swarm"] != 5 or type(config.get("dimension")) is not int or config["dimension"] != 5 or type(config.get("move_severity")) not in (float, int) or config["move_severity"] not in (1., 3.):
        raise ValueError("Partial output proof is outside the declared size-5, dimension-5, severity-1/3 domain.")


def component_constant_action(method, config):
    """Return only a certified *post-substitution* constant, never retype E."""
    program = method["program"]
    supplied = program.get("proven_constant_outputs")
    if supplied is None:
        return None
    expected = reviewed_output_proof(program.get("sha256"))
    if expected is None or supplied != expected:
        raise ValueError("Partial output proof differs from its exact reviewed source/registry.")
    require_domain(config)
    component = method["component"]
    if component not in {"count", "radius_scale"}:
        raise ValueError("Unknown component substitution.")
    retained = "radius_scale" if component == "count" else "count"
    if retained not in expected["outputs"]:
        return None
    action = {component: method["replacement"], retained: expected["outputs"][retained]}
    if type(action["count"]) is not int or not 0 <= action["count"] <= 5 or type(action["radius_scale"]) not in (float, int) or not math.isfinite(action["radius_scale"]) or action["radius_scale"] < 0:
        raise ValueError("Certified component substitution violates the joint output contract.")
    return {"count": action["count"], "radius_scale": float(action["radius_scale"])}


def verify_original_registration(folder):
    """Verify original immutable registration/snapshots without accepting new code."""
    record = read_json(folder / "registration.json")
    fields = ("settings", "searches", "engine_config", "search_cases", "validation_cases", "execution_sources", "task_sources", "analysis")
    if digest({key: record[key] for key in fields}) != record["signature"]:
        raise ValueError("Registered prospective settings changed.")
    for name, expected in record["runner_snapshot"].items():
        path = folder / "runner_snapshot" / name
        if path.resolve().parent != (folder / "runner_snapshot").resolve() or file_sha(path) != expected:
            raise ValueError(f"Frozen source snapshot changed: {name}")
    return record


def require_preprotected(folder):
    present = [name for name in (*PROTECTED, "constant_alias_certification.json") if (folder / name).exists()]
    if present:
        raise ValueError(f"Controller amendment must precede certification/source review/protected stages: {present}")


def validate_source_delta(original, current):
    changed = {name for name in original if current.get(name) != original[name]}
    added = set(current) - set(original)
    if changed != {CONTROLLER} or added != {SUPPORT}:
        raise ValueError("Amendment permits only the registered controller change and new alias-support module.")


def verify_amendment(folder, registration, current_sources):
    path = folder / AMENDMENT_FILE
    if not path.exists():
        if registration["execution_sources"] != current_sources:
            raise ValueError("Scientific comparison sources changed without the explicit committed controller amendment.")
        return None
    record = read_json(path)
    if record.get("version") != AMENDMENT_VERSION or digest({key: value for key, value in record.items() if key != "amendment_id"}) != record.get("amendment_id"):
        raise ValueError("Controller amendment record changed or has an unknown version.")
    if record["registration_sha256"] != file_sha(folder / "registration.json") or record["original_execution_sources"] != registration["execution_sources"] or record["new_execution_sources"] != current_sources:
        raise ValueError("Controller amendment does not match original registration and current sources.")
    validate_source_delta(registration["execution_sources"], current_sources)
    if record["partial_output_registry_sha256"] != registry_fingerprint() or record["protected_artifacts_present_at_install"] != [] or record["commit_verification"] != "Every recorded source matched git show at the recorded full commit before installation.":
        raise ValueError("Controller amendment registry, chronology guard or commit receipt differs.")
    if not re.fullmatch(r"[0-9a-f]{40,64}", record["source_revision"]):
        raise ValueError("Controller amendment lacks a complete committed revision.")
    snapshot_root = (folder / SNAPSHOT_DIR).resolve()
    if snapshot_root.parent != folder.resolve() or set(record["snapshot_sources"]) != set(record["snapshot_paths"]):
        raise ValueError("Controller amendment snapshot directory escapes the study or its inventory differs.")
    for source, expected in record["snapshot_sources"].items():
        relative = record["snapshot_paths"][source]
        snapshot = (folder / relative).resolve()
        if snapshot.parent != snapshot_root or file_sha(snapshot) != expected:
            raise ValueError(f"Controller amendment snapshot changed or escaped: {source}")
    if any(record["snapshot_sources"].get(name) != current_sources[name] for name in (CONTROLLER, SUPPORT)):
        raise ValueError("Controller amendment snapshot omits the exact scientific changes.")
    installed = datetime.fromisoformat(record["installed_at"])
    if installed < datetime.fromisoformat(registration["registered_at"]):
        raise ValueError("Controller amendment predates its original registration.")
    chronology = (("source_review.json", "reviewed_at"), ("validation/manifest.json", "created_at"),
                  ("selection.json", "frozen_at"), ("final_cases.json", "generated_at"),
                  ("final/manifest.json", "created_at"), ("analysis.json", "analyzed_at"))
    for relative, timestamp in chronology:
        artifact = folder / relative
        if artifact.exists() and datetime.fromisoformat(read_json(artifact)[timestamp]) < installed:
            raise ValueError(f"Protected artifact predates controller amendment: {relative}")
    return record


def controller_reference(folder):
    path = folder / AMENDMENT_FILE
    if path.exists():
        record = read_json(path)
        return {"kind": AMENDMENT_VERSION, "path": AMENDMENT_FILE,
                "sha256": file_sha(path), "amendment_id": record["amendment_id"]}
    return {"kind": "original_registration", "registration_sha256": file_sha(folder / "registration.json")}
