"""Frozen validation, final comparison and mechanism analysis for allocation v2.

Stage boundaries are durable and explicit: shortlist -> source review -> validation
-> selection/control freeze -> fresh final seeds -> final outcomes. Candidate code
receives only public simulator observations. This is not a Python security sandbox.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import secrets
import sqlite3
import statistics
import time

import numpy as np

from .artifacts import read_json, resolve_json, write_compressed_json
from .cli import simulator_fingerprint, source_revision
from .comparison import load_suite, regime_key, validate_pair, behavior_summary
from .logging import EventLogger, atomic_json
from .relocation_allocation import (load_count_policy, count_policy_adapter,
                                   constant_count_policy, annotate_count_log)
from .simulator import run_case

VERSION = "allocation_v2_frozen_study_v1"
BOOTSTRAP_SEED = 20260916
BOOTSTRAP_REPLICATES = 20000
REGIMES = ((1.0, 2500), (1.0, 5000), (3.0, 2500), (3.0, 5000))


def _now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def execution_fingerprint():
    result = simulator_fingerprint()
    for name in ("relocation_allocation.py", "allocation_study.py", "comparison.py", "artifacts.py"):
        path = Path(__file__).with_name(name)
        result[f"src/adaptive_swarms/{name}"] = file_sha(path)
    return result


def proven_constant(source: str) -> int | None:
    """Conservative exact equivalence proof, never infer constancy from traces."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    def doc(node):
        return isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
    nodes = [node for node in tree.body if not doc(node)]
    if len(nodes) != 1 or not isinstance(nodes[0], ast.FunctionDef):
        return None
    fn = nodes[0]
    if fn.name != "choose_relocation_count" or fn.decorator_list or fn.args.defaults or fn.args.kw_defaults:
        return None
    if len(fn.args.posonlyargs) + len(fn.args.args) != 1 or fn.args.vararg or fn.args.kwarg or fn.args.kwonlyargs:
        return None
    # Import-time annotations are executable Python. Permit only the inert
    # built-in annotations used by the seed, or no annotations.
    for annotation in [fn.returns, *(arg.annotation for arg in fn.args.posonlyargs + fn.args.args)]:
        if annotation is not None and not (isinstance(annotation, ast.Name) and annotation.id in {"dict", "int"}):
            return None
    body = [node for node in fn.body if not doc(node)]
    if len(body) != 1 or not isinstance(body[0], ast.Return) or not isinstance(body[0].value, ast.Constant):
        return None
    value = body[0].value.value
    return value if type(value) is int and 0 <= value <= 5 else None


def verify_shortlist(folder: Path) -> dict:
    record = read_json(folder / "shortlist.json")
    if record["execution_sources"] != execution_fingerprint():
        raise ValueError("Simulator/adapter differs from frozen shortlist.")
    for program in record["programs"]:
        if file_sha(folder / program["policy"]) != program["sha256"]:
            raise ValueError(f"Frozen source changed: {program['name']}")
    for name, expected in record["runner_snapshot"].items():
        if file_sha(folder / "runner_snapshot" / name) != expected:
            raise ValueError(f"Frozen study runner snapshot changed: {name}")
    return record


def freeze_shortlist(search_run: Path, folder: Path) -> dict:
    """Read native results and freeze top three, without opening validation cases."""
    if (folder / "shortlist.json").exists():
        saved = verify_shortlist(folder)
        if Path(saved["search_run"]).resolve() != search_run.resolve():
            raise ValueError("Existing shortlist belongs to a different search.")
        return saved
    if (folder / "validation").exists() or (folder / "selection.json").exists():
        raise ValueError("Refusing to replace existing study without a shortlist.")
    search_manifest = read_json(search_run / "manifest.json")
    required = {"task": "relocation_allocation_v2", "evaluation_version": "relocation_allocation_v2_score_reciprocal",
                "status": "search_complete", "generation_target": 20}
    if any(search_manifest.get(key) != value for key, value in required.items()):
        raise ValueError("Shortlisting requires a completed 20-slot native allocation-v2 search.")
    db = search_run / "programs.sqlite"
    connection = sqlite3.connect(f"file:{db.resolve()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        generations = [row[0] for row in connection.execute("SELECT DISTINCT generation FROM programs ORDER BY generation")]
        if generations != list(range(20)):
            raise ValueError("Native archive does not contain exactly the declared generation slots 0 through 19.")
        rows = [dict(row) for row in connection.execute("SELECT id, code, parent_id, generation, combined_score, correct, metadata, public_metrics, text_feedback FROM programs WHERE correct=1")]
    finally:
        connection.close()
    for row in rows:
        row["sha256"] = hashlib.sha256(row["code"].encode()).hexdigest()
    rows = [row for row in rows if row["combined_score"] is not None and math.isfinite(row["combined_score"])]
    rows.sort(key=lambda row: (-row["combined_score"], row["generation"], row["sha256"], row["id"]))
    unique = {}
    for row in rows:
        unique.setdefault(row["sha256"], row)
    chosen = list(unique.values())[:3]
    if not chosen:
        raise ValueError("Native archive contains no valid scored program.")
    programs = []
    (folder / "programs").mkdir(parents=True, exist_ok=True)
    snapshot = folder / "runner_snapshot"
    snapshot.mkdir(exist_ok=True)
    snapshot_hashes = {}
    for name in ("allocation_study.py", "relocation_allocation.py", "comparison.py", "artifacts.py"):
        source = Path(__file__).with_name(name)
        (snapshot / name).write_bytes(source.read_bytes())
        snapshot_hashes[name] = file_sha(source)
    for rank, row in enumerate(chosen, 1):
        name = f"shortlist_{rank}"
        path = Path("programs") / f"{name}.py"
        (folder / path).write_text(row["code"])
        programs.append({"name": name, "policy": str(path), "sha256": row["sha256"],
                         "native_id": row["id"], "parent_id": row["parent_id"],
                         "generation": row["generation"], "search_score": row["combined_score"],
                         "proven_constant": proven_constant(row["code"]),
                         "native_metadata": row["metadata"], "text_feedback": row["text_feedback"]})
    record = {"version": VERSION, "frozen_at": _now(), "search_run": str(search_run.resolve()),
              "source_revision": source_revision(), "selection_rule": "top three source-distinct correct programs; descending search score, earlier generation, source SHA-256",
              "available_source_distinct_valid_programs": len(unique), "programs": programs,
              "execution_sources": execution_fingerprint(),
              "runner_snapshot": snapshot_hashes, "native_generation_slots": generations,
              "native_search_manifest_sha256": file_sha(search_run / "manifest.json"),
              "source_review_required": "Exact frozen sources must be reviewed before validation execution."}
    atomic_json(folder / "shortlist.json", record)
    return record


def record_source_review(folder: Path, review_path: Path) -> dict:
    shortlist = verify_shortlist(folder)
    review = read_json(review_path)
    expected = {program["sha256"] for program in shortlist["programs"]}
    if set(review.get("approved_source_sha256", [])) != expected or not review.get("reviewer") or not review.get("notes"):
        raise ValueError("Review requires reviewer, notes and approved_source_sha256 matching every frozen source exactly.")
    if (folder / "source_review.json").exists():
        saved = read_json(folder / "source_review.json")
        if saved["review"] != review:
            raise ValueError("Existing source review is immutable.")
        return saved
    record = {"recorded_at": _now(), "shortlist_sha256": file_sha(folder / "shortlist.json"), "review": review}
    atomic_json(folder / "source_review.json", record)
    return record


def _verify_review(folder):
    shortlist = verify_shortlist(folder)
    review = read_json(folder / "source_review.json")
    if review["shortlist_sha256"] != file_sha(folder / "shortlist.json") or set(review["review"]["approved_source_sha256"]) != {p["sha256"] for p in shortlist["programs"]}:
        raise ValueError("Source review does not match frozen shortlist.")
    return shortlist


def assert_protocol_cases(cases: list[dict], per_regime: int):
    counts = Counter((case["move_severity"], case["period"]) for case in cases)
    if counts != Counter({regime: per_regime for regime in REGIMES}):
        raise ValueError(f"Expected {per_regime} cases in each of four protocol regimes.")
    for case in cases:
        required = {"budget": 100000, "dimension": 5, "npeaks": 10, "particles_per_swarm": 5, "nexcess": 1, "correlation": 0.0}
        if any(case[key] != value for key, value in required.items()):
            raise ValueError("Case differs from the declared fixed v2 settings.")
    seeds = [case[key] for case in cases for key in ("environment_seed", "optimizer_seed")]
    if len(seeds) != len(set(seeds)):
        raise ValueError("Protocol cases must have unique individual environment and optimizer seeds.")


def _constant_method(count):
    return {"kind": "constant", "count": count}


def _program_method(program):
    return {"kind": "program", **program}


def method_identity(method: dict, config: dict) -> dict:
    if method["kind"] == "baseline":
        return {"kind": "corrected_v1_baseline"}
    if method["kind"] == "constant":
        return {"kind": "allocation_constant", "count": method["count"]}
    if method["kind"] == "program":
        if method.get("proven_constant") is not None:
            return {"kind": "allocation_constant", "count": method["proven_constant"]}
        return {"kind": "allocation_program", "sha256": method["sha256"]}
    probabilities = method["distributions"][regime_key(config)]
    support = [k for k, value in enumerate(probabilities) if value > 0]
    if len(support) == 1:
        return {"kind": "allocation_constant", "count": support[0]}
    return {"kind": "state_free", "probabilities": probabilities,
            "rng_seed": _control_seed(method, config), "rng_algorithm": "python.random.Random"}


def _control_seed(method, config):
    return int(digest({"namespace": "allocation_v2_state_free_control", "master_seed": method["rng_master_seed"], "config": config})[:16], 16)


def state_free_count_policy(probabilities, rng_seed):
    """Dedicated RNG; observations are deliberately ignored by count selection."""
    if len(probabilities) != 6 or any(p < 0 for p in probabilities) or not math.isclose(sum(probabilities), 1):
        raise ValueError("Invalid frozen count distribution.")
    rng = random.Random(rng_seed)
    def choose_relocation_count(_observation):
        return rng.choices(range(6), weights=probabilities, k=1)[0]
    return choose_relocation_count


def _policy(folder, method, config):
    identity = method_identity(method, config)
    if identity["kind"] == "corrected_v1_baseline":
        return None
    if identity["kind"] == "allocation_constant":
        function = constant_count_policy(identity["count"])
    elif identity["kind"] == "allocation_program":
        function = load_count_policy(folder / method["policy"])
    else:
        function = state_free_count_policy(identity["probabilities"], identity["rng_seed"])
    return count_policy_adapter(function)


def _run_stage(folder: Path, stage: str, cases: list[dict], methods: dict, freeze_sha: str) -> dict:
    """Checkpoint each distinct execution; alias only execution-identical policies."""
    _verify_review(folder)
    directory = folder / stage
    signature = digest({"version": VERSION, "stage": stage, "cases": cases, "methods": methods,
                        "freeze_sha256": freeze_sha, "execution_sources": execution_fingerprint()})
    path = directory / "manifest.json"
    if path.exists():
        manifest = read_json(path)
        if manifest["signature"] != signature:
            raise ValueError("Resume stage settings differ from saved manifest.")
        if manifest["status"] == "completed":
            _, saved_outcomes = load_stage_outcomes(folder, stage)
            reference = next(iter(saved_outcomes.values()))
            for values in saved_outcomes.values():
                for first, second in zip(reference, values):
                    validate_pair(first, second)
            # Preserve the exact validation summary used by the selection freeze.
            with EventLogger(directory) as log:
                log.event("stage_reused", stage=stage, cases=len(cases), methods=list(methods),
                          message="All completed case checkpoints verified; no evaluations repeated.")
            return read_json(directory / "summary.json")
    else:
        manifest = {"version": VERSION, "stage": stage, "created_at": _now(), "signature": signature,
                    "cases": cases, "methods": methods, "freeze_sha256": freeze_sha,
                    "execution_sources": execution_fingerprint(), "case_artifacts": {name: [] for name in methods}, "aliases": []}
    manifest["status"] = "running"
    atomic_json(path, manifest)
    outcomes = {name: [] for name in methods}
    completed, reused, aliases = 0, 0, []
    try:
        with EventLogger(directory) as log:
            log.event("stage_started", stage=stage, cases=len(cases), methods=list(methods), signature=signature)
            for index, config in enumerate(cases):
                seen = {}
                reference = None
                for name, metadata in methods.items():
                    identity = method_identity(metadata, config)
                    cache_key = digest({"signature": signature, "config": config, "execution_identity": identity})
                    relative = str(Path("cache") / f"{cache_key}.json.gz")
                    checkpoint = directory / relative
                    if cache_key in seen:
                        original, result = seen[cache_key]
                        aliases.append({"case_index": index, "method": name, "alias_of": original,
                                        "cache_key": cache_key, "execution_identity": identity,
                                        "reason": "identical fixed adapter count" if identity["kind"] == "allocation_constant" else "identical source and configuration"})
                        log.event("case_aliased", stage=stage, case=index + 1, method=name, alias_of=original, offline_error=result["offline_error"])
                    elif checkpoint.exists():
                        result = read_json(checkpoint)
                        if result.get("cache_key") != cache_key or result.get("signature") != signature or result["config"] != config or result.get("execution_identity") != identity:
                            raise ValueError(f"Checkpoint provenance mismatch: {checkpoint}")
                        reused += 1
                        log.event("case_reused", stage=stage, case=index + 1, method=name, offline_error=result["offline_error"])
                    else:
                        _verify_review(folder)
                        log.set_activity(f"{stage}, {name}, case {index + 1}/{len(cases)}")
                        log.event("case_started", stage=stage, case=index + 1, method=name, budget=config["budget"],
                                  completed_executions=completed, reused_executions=reused,
                                  environment_seed=config["environment_seed"], optimizer_seed=config["optimizer_seed"])
                        def progress(event):
                            details = dict(event)
                            kind = details.pop("event", "simulation_progress")
                            details.pop("config", None)
                            log.event(kind, stage=stage, method=name, case=index + 1, **details)
                        start = time.monotonic()
                        policy = _policy(folder, metadata, config)
                        result = run_case(config, policy=policy, progress=progress)
                        if policy is not None:
                            annotate_count_log(result, policy)
                        else:
                            for response in result["response_log"]:
                                response.update(requested_count=response["observation"]["swarm_size"], executed_count=len(response["relocated_indices"]))
                        result.update(signature=signature, cache_key=cache_key, execution_identity=identity,
                                      method=name, case_index=index, wall_time_seconds=time.monotonic() - start)
                        # Persist a completed expensive case before any cross-method check.
                        write_compressed_json(checkpoint, result)
                        completed += 1
                        log.event("case_completed", stage=stage, method=name, case=index + 1,
                                  offline_error=result["offline_error"], checkpoint=str(checkpoint),
                                  elapsed_case_seconds=result["wall_time_seconds"], completed_executions=completed)
                    validate_pair(result, result if reference is None else reference)
                    reference = result if reference is None else reference
                    seen.setdefault(cache_key, (name, result))
                    outcomes[name].append(result)
                    saved_paths = manifest["case_artifacts"][name]
                    if len(saved_paths) <= index:
                        saved_paths.append(relative)
                    elif saved_paths[index] != relative:
                        raise ValueError("Saved method alias path differs from execution identity.")
                    manifest["aliases"] = aliases
                    manifest["completed_method_cases"] = {method: len(values) for method, values in outcomes.items()}
                    atomic_json(path, manifest)
                log.event("paired_case_completed", stage=stage, case=index + 1, total=len(cases))
            summary = {"status": "completed", "stage": stage, "completed_at": _now(),
                       "method_mean_offline_errors": {name: equal_regime_mean(values) for name, values in outcomes.items()},
                       "method_case_errors": {name: [case["offline_error"] for case in values] for name, values in outcomes.items()},
                       "case_count": len(cases), "unique_executed_method_cases": len({path for paths in manifest["case_artifacts"].values() for path in paths}),
                       "aliases": aliases}
            atomic_json(directory / "summary.json", summary)
            manifest.update(status="completed", completed_at=_now())
            atomic_json(path, manifest)
            log.event("stage_completed", stage=stage, method_mean_offline_errors=summary["method_mean_offline_errors"],
                      unique_executed_method_cases=summary["unique_executed_method_cases"], aliases=len(aliases))
    except BaseException as exc:
        manifest.update(status="interrupted_or_failed", last_error=f"{type(exc).__name__}: {exc}")
        atomic_json(path, manifest)
        raise
    return summary


def equal_regime_mean(cases):
    groups = defaultdict(list)
    for case in cases:
        groups[regime_key(case["config"])].append(case["offline_error"])
    return statistics.mean(statistics.mean(values) for values in groups.values())


def validate_shortlist(folder: Path, suite_path: Path) -> dict:
    shortlist = _verify_review(folder)
    _, cases = load_suite(suite_path)
    assert_protocol_cases(cases, 4)
    methods = {f"constant_{k}": _constant_method(k) for k in range(6)}
    methods.update({program["name"]: _program_method(program) for program in shortlist["programs"]})
    return _run_stage(folder, "validation", cases, methods, file_sha(folder / "shortlist.json"))


def load_stage_outcomes(folder, stage):
    manifest = read_json(folder / stage / "manifest.json")
    if manifest["status"] != "completed":
        raise ValueError(f"{stage} is not complete.")
    outcomes = {name: [read_json(folder / stage / path) for path in paths] for name, paths in manifest["case_artifacts"].items()}
    for name, values in outcomes.items():
        if len(values) != len(manifest["cases"]):
            raise ValueError(f"Incomplete {stage} method: {name}")
        for case, config in zip(values, manifest["cases"]):
            if case["config"] != config or case.get("signature") != manifest["signature"]:
                raise ValueError("Saved stage outcome provenance mismatch.")
            identity = method_identity(manifest["methods"][name], config)
            expected_key = digest({"signature": manifest["signature"], "config": config, "execution_identity": identity})
            if case.get("cache_key") != expected_key or case.get("execution_identity") != identity:
                raise ValueError("Saved stage cache identity mismatch.")
            validate_pair(case, case)
    return manifest, outcomes


def control_distributions(cases: list[dict]) -> dict:
    """Each independent case contributes equally, regardless of response count."""
    groups = defaultdict(list)
    details = []
    for index, case in enumerate(cases):
        counts = Counter(response["requested_count"] for response in case["response_log"])
        total = sum(counts.values())
        probabilities = [counts[k] / total for k in range(6)] if total else [0, 0, 0, 1, 0, 0]
        regime = regime_key(case["config"])
        groups[regime].append(probabilities)
        details.append({"case_index": index, "regime": regime, "response_count": total,
                        "probabilities": probabilities, "no_response_count_three_fallback": total == 0})
    return {"distributions": {regime: [statistics.mean(p[k] for p in proportions) for k in range(6)] for regime, proportions in groups.items()},
            "case_proportions": details, "weighting": "equal independent validation cases within each regime",
            "count_measure": "requested integer count at each response, including horizon-truncated responses",
            "rng_master_seed": 2026091602, "rng_algorithm": "python.random.Random per case, SHA-256-derived dedicated seed; never shares environment or optimizer RNG"}


def select_and_freeze(folder: Path) -> dict:
    shortlist = _verify_review(folder)
    manifest, outcomes = load_stage_outcomes(folder, "validation")
    summary = read_json(folder / "validation/summary.json")
    provenance = {"shortlist_sha256": file_sha(folder / "shortlist.json"), "validation_signature": manifest["signature"],
                  "validation_summary_sha256": file_sha(folder / "validation/summary.json")}
    if (folder / "selection.json").exists():
        frozen = read_json(folder / "selection.json")
        if frozen["provenance"] != provenance:
            raise ValueError("Validation results changed after selection freeze.")
        return frozen
    errors = summary["method_mean_offline_errors"]
    selected = min(shortlist["programs"], key=lambda p: (errors[p["name"]], p["generation"], p["sha256"]))
    count = min(range(6), key=lambda k: (errors[f"constant_{k}"], k))
    control = control_distributions(outcomes[selected["name"]])
    methods = {"baseline": {"kind": "baseline"}, "constant_three": _constant_method(3),
               "best_constant": _constant_method(count), "evolved": _program_method(selected),
               "state_free_control": {"kind": "state_free", **control}}
    frozen = {"version": VERSION, "frozen_at": _now(), "provenance": provenance,
              "selected_program": selected, "selected_program_validation_error": errors[selected["name"]],
              "selected_constant": count, "selected_constant_validation_error": errors[f"constant_{count}"],
              "selection_rule": "lowest equal-regime mean validation error; program ties earlier generation then source hash; constant ties smaller count",
              "validation_mean_errors": errors, "methods": methods, "control": control,
              "final_cases_not_generated": True,
              "interpretation": "Control removes current-state association and changes temporal dependence; regime identity remains available."}
    atomic_json(folder / "selection.json", frozen)
    return frozen


def collect_used_seeds(roots: list[Path], exclude: set[Path] | None = None) -> dict:
    """Read all saved JSON metadata and case checkpoints; reject unreadable history."""
    excluded = {path.resolve() for path in (exclude or set())}
    found = {"environment_seed": set(), "optimizer_seed": set()}
    sources = []
    seen_files = set()
    def visit(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in found and type(item) is int:
                    found[key].add(item)
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)
    for root in roots:
        paths = [root] if root.is_file() else list(root.rglob("*.json")) + list(root.rglob("*.json.gz"))
        for path in sorted(paths):
            resolved = path.resolve()
            if resolved in seen_files or resolved in excluded or not path.is_file():
                continue
            seen_files.add(resolved)
            before = tuple(len(found[key]) for key in found)
            try:
                value = read_json(path)
            except (OSError, ValueError) as exc:
                raise ValueError(f"Cannot verify historical seeds in {path}: {exc}") from exc
            visit(value)
            if tuple(len(found[key]) for key in found) != before:
                sources.append({"path": str(path), "sha256": file_sha(path)})
    return {key + "s": sorted(value) for key, value in found.items()} | {"sources_adding_seeds": sources, "files_inspected": len(seen_files)}


def generate_final_cases(folder: Path, seed_roots: list[Path]) -> dict:
    _verify_review(folder)
    frozen = select_and_freeze(folder)
    path = folder / "final_cases.json"
    selection_sha = file_sha(folder / "selection.json")
    if path.exists():
        saved = read_json(path)
        if saved["selection_sha256"] != selection_sha:
            raise ValueError("Final cases belong to a different frozen selection.")
        assert_protocol_cases(saved["cases"], 10)
        return saved
    historical = collect_used_seeds(seed_roots)
    # Always include this study's validation and the native search, even when a
    # caller supplies narrower historical roots.
    study_seeds = collect_used_seeds([folder / "validation/manifest.json", Path(read_json(folder / "shortlist.json")["search_run"])])
    forbidden = set(historical["environment_seeds"] + historical["optimizer_seeds"] + study_seeds["environment_seeds"] + study_seeds["optimizer_seeds"])
    master_seed = secrets.randbits(128)
    rng = random.Random(master_seed)
    def fresh():
        while True:
            seed = rng.randrange(1, 2**31)
            if seed not in forbidden:
                forbidden.add(seed)
                return seed
    validation = read_json(folder / "validation/manifest.json")["cases"]
    template = validation[0]
    cases = []
    for severity, period in REGIMES:
        for _ in range(10):
            cases.append({**template, "move_severity": severity, "period": period,
                          "environment_seed": fresh(), "optimizer_seed": fresh()})
    assert_protocol_cases(cases, 10)
    record = {"version": VERSION, "generated_at": _now(), "selection_frozen_at": frozen["frozen_at"],
              "selection_sha256": selection_sha, "seed_generation_master_seed": master_seed,
              "seed_generation_algorithm": "Python random.Random initialized from secrets.randbits(128), after selection/control freeze",
              "exclusion_rule": "Every historical environment and optimizer seed excluded from either new seed role; new roles and cases mutually distinct",
              "historical_seed_audit": historical, "current_study_seed_audit": study_seeds, "cases": cases}
    atomic_json(path, record)
    return record


def run_final(folder: Path, seed_roots: list[Path]) -> dict:
    record = generate_final_cases(folder, seed_roots)
    selection = read_json(folder / "selection.json")
    return _run_stage(folder, "final", record["cases"], selection["methods"], file_sha(folder / "selection.json"))


def paired_statistics(deltas, regimes):
    groups = defaultdict(list)
    for delta, regime in zip(deltas, regimes):
        groups[regime].append(float(delta))
    means = [statistics.mean(group) for group in groups.values()]
    result = {"n": len(deltas), "mean_delta": statistics.mean(means),
              "improved_cases": sum(value < 0 for value in deltas),
              "worsened_cases": sum(value > 0 for value in deltas), "tied_cases": sum(value == 0 for value in deltas)}
    if all(len(group) > 1 for group in groups.values()):
        rng = np.random.default_rng(BOOTSTRAP_SEED)
        samples = np.zeros(BOOTSTRAP_REPLICATES)
        for regime in sorted(groups):
            group = np.asarray(groups[regime])
            samples += rng.choice(group, size=(BOOTSTRAP_REPLICATES, len(group))).mean(axis=1) / len(groups)
        result["bootstrap_95_percent_interval"] = np.quantile(samples, [.025, .975]).tolist()
        result["stratified_se_delta"] = math.sqrt(sum(statistics.variance(group) / len(group) for group in groups.values())) / len(groups)
    else:
        result.update(bootstrap_95_percent_interval=None, stratified_se_delta=None)
    return result


def allocation_behavior(cases):
    result = behavior_summary(cases)
    by_regime = defaultdict(list)
    state_bins = defaultdict(Counter)
    for case in cases:
        regime = regime_key(case["config"])
        by_regime[regime].append(case)
        for response in case["response_log"]:
            obs = response["observation"]
            count = response["requested_count"]
            drop = obs["relative_fitness_drop"]
            diameter_ratio = obs["swarm_diameter"] / max(obs["default_radius"], 1e-12)
            bins = {"relative_fitness_drop": "<=0" if drop <= 0 else "(0,0.05]" if drop <= .05 else "(0.05,0.15]" if drop <= .15 else ">0.15",
                    "diameter/default_radius": "<=2" if diameter_ratio <= 2 else "(2,5]" if diameter_ratio <= 5 else ">5",
                    "recent_improvement": "<=0" if obs["recent_improvement"] <= 0 else ">0"}
            for variable, label in bins.items():
                state_bins[(regime, variable, label)][count] += 1
    def distribution(values, field):
        counts = Counter(r.get(field, len(r["relocated_indices"])) for c in values for r in c["response_log"])
        total = sum(counts.values())
        return {"counts": [counts[k] for k in range(6)], "proportions": [counts[k] / total for k in range(6)] if total else None, "responses": total}
    result["regimes"] = {regime: {"requested": distribution(values, "requested_count"), "executed": distribution(values, "executed_count"),
                                           "equal_case_requested_proportions": control_distributions(values)["distributions"][regime],
                                           "case_mean_error": statistics.mean(c["offline_error"] for c in values),
                                           "incomplete_responses": sum(not r["completed"] for c in values for r in c["response_log"])}
                         for regime, values in by_regime.items()}
    result["observed_state_bins"] = [{"regime": regime, "variable": variable, "bin": label,
                                      "requested_counts": [counts[k] for k in range(6)], "responses": sum(counts.values())}
                                     for (regime, variable, label), counts in sorted(state_bins.items())]
    result["state_bin_note"] = "Descriptive response distributions only; state and trajectories affect both action and recovery. Responses are not independent cases."
    return result


def analyze(folder: Path) -> dict:
    _verify_review(folder)
    manifest, outcomes = load_stage_outcomes(folder, "final")
    regimes = [regime_key(config) for config in manifest["cases"]]
    comparisons = {}
    for method, comparator, role in [("evolved", "best_constant", "primary"), ("evolved", "state_free_control", "predeclared mechanism"),
                                      ("evolved", "baseline", "contextual"), ("evolved", "constant_three", "contextual")]:
        current, control = outcomes[method], outcomes[comparator]
        checks = [validate_pair(a, b) for a, b in zip(current, control)]
        deltas = [a["offline_error"] - b["offline_error"] for a, b in zip(current, control)]
        groups = {}
        for regime in sorted(set(regimes)):
            indices = [i for i, value in enumerate(regimes) if value == regime]
            groups[regime] = {**paired_statistics([deltas[i] for i in indices], [regime] * len(indices)),
                              "mean_method_error": statistics.mean(current[i]["offline_error"] for i in indices),
                              "mean_comparator_error": statistics.mean(control[i]["offline_error"] for i in indices)}
        comparisons[f"{method}_minus_{comparator}"] = {"role": role, "method": method, "comparator": comparator,
            "sign": "negative favors evolved", **paired_statistics(deltas, regimes), "regimes": groups,
            "cases": [{"case_index": i, "environment_seed": config["environment_seed"], "optimizer_seed": config["optimizer_seed"],
                       "regime": regimes[i], "delta": deltas[i], "method_offline_error": current[i]["offline_error"],
                       "comparator_offline_error": control[i]["offline_error"], **checks[i]} for i, config in enumerate(manifest["cases"])]}
    result = {"version": VERSION, "status": "completed", "analyzed_at": _now(), "paired_case_count": len(regimes),
              "method_mean_offline_errors": {name: equal_regime_mean(values) for name, values in outcomes.items()},
              "comparisons": comparisons, "behavior": {name: allocation_behavior(values) for name, values in outcomes.items()},
              "selection": read_json(folder / "selection.json"), "aliases": manifest["aliases"],
              "uncertainty": {"bootstrap_replicates": BOOTSTRAP_REPLICATES, "analysis_rng_seed": BOOTSTRAP_SEED,
                              "method": "paired percentile bootstrap within regime, equal 1/4 regime weights; independent cases are resampling units",
                              "standard_error": "sqrt(sum(sample variance of paired differences in each regime / regime case count)) / 4",
                              "secondary_intervals": "descriptive; no multiplicity-adjusted confirmatory claims"},
              "saved_measurements": "Every compressed case includes per-environment error, recovery traces, swarm count, query accounting and full observed response state."}
    atomic_json(folder / "analysis.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["freeze-shortlist", "review", "validate", "select", "final", "analyze"])
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--search-run", type=Path)
    parser.add_argument("--review-record", type=Path)
    parser.add_argument("--validation-config", type=Path, default=Path("configs/relocation_allocation_v2/validation.json"))
    parser.add_argument("--seed-roots", type=Path, nargs="+", default=[Path("configs"), Path("results"), Path("artifacts")])
    args = parser.parse_args()
    if args.stage == "freeze-shortlist":
        if args.search_run is None:
            parser.error("freeze-shortlist requires --search-run")
        result = freeze_shortlist(args.search_run, args.run)
    elif args.stage == "review":
        if args.review_record is None:
            parser.error("review requires --review-record")
        result = record_source_review(args.run, args.review_record)
    elif args.stage == "validate":
        result = validate_shortlist(args.run, args.validation_config)
    elif args.stage == "select":
        result = select_and_freeze(args.run)
    elif args.stage == "final":
        result = run_final(args.run, args.seed_roots)
    else:
        result = analyze(args.run)
    print(json.dumps({"stage": args.stage, "run": str(args.run), "status": result.get("status", "frozen"),
                      "method_mean_offline_errors": result.get("method_mean_offline_errors")}), flush=True)


if __name__ == "__main__":
    main()
