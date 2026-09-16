"""Prospectively registered, checkpointed joint relocation V3 comparisons.

Three native search identities precede outcomes. Shortlists precede validation;
selection, joint controls and analysis precede fresh final seeds. Historical
controllers are imported only for shared immutable artifact/pairing utilities.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from contextlib import contextmanager
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

from .artifacts import read_json, write_compressed_json
from .cli import source_revision
from .comparison import load_suite, regime_key, validate_pair, behavior_summary
from .engine_progress import terminal_failure_generations
from .joint_relocation import (joint_fingerprint, load_joint_policy, joint_policy_adapter,
                               annotate_joint_log, constant_joint_policy, validate_decision)
from .logging import EventLogger, atomic_json
from .simulator import run_case

VERSION = "joint_relocation_v3_frozen_study_v1"
REGIMES = ((1.0, 2500), (1.0, 5000), (3.0, 2500), (3.0, 5000))
BOOTSTRAP_SEED = 2026091603
BOOTSTRAP_REPLICATES = 20000
CONTROL_MASTER_SEED = 2026091604
DEFAULT_CONFIG = Path("configs/joint_relocation_v3/study.json")


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def execution_fingerprint():
    values = joint_fingerprint()
    for name in ("joint_study.py", "comparison.py", "artifacts.py"):
        values[f"src/adaptive_swarms/{name}"] = file_sha(Path(__file__).with_name(name))
    return values


def analysis_specification():
    return {"analysis_seed": BOOTSTRAP_SEED, "bootstrap_resamples": BOOTSTRAP_REPLICATES,
            "unit": "independent paired case", "strata": "four equally weighted regimes",
            "primary_contrasts": ["overall winner minus corrected baseline", "overall winner minus validation-selected fixed pair"],
            "primary_interval_level": .975, "secondary_interval_level": .95,
            "claim_rule": "superiority over both primary controls only if both 97.5% two-sided percentile interval upper bounds are below zero",
            "family_interpretation": "Bonferroni allocation for an approximate simultaneous 95% family",
            "interaction": "overall winner - radius_replaced - count_replaced + best_fixed",
            "interaction_interpretation": "descriptive closed-loop policy interaction; state visitation is not held fixed",
            "secondary_interpretation": "descriptive 95% intervals; the three winners share the same independent final histories",
            "standard_error": "sqrt(sum(unbiased within-regime paired variance / regime sample count)) / number of regimes",
            "recovery_resolution": "saved measurements only; no inferred immediate recovery between 500-query checkpoints",
            "failures": "retain all measured histories including large sustained tracking failures"}


def assert_cases(cases, per_regime):
    if Counter((c["move_severity"], c["period"]) for c in cases) != Counter({r: per_regime for r in REGIMES}):
        raise ValueError(f"Expected {per_regime} cases in each protocol regime.")
    required = {"budget": 100000, "dimension": 5, "npeaks": 10, "particles_per_swarm": 5, "nexcess": 1, "correlation": 0.0}
    if any(any(case[key] != value for key, value in required.items()) for case in cases):
        raise ValueError("Case differs from fixed V3 scientific settings.")
    seeds = [case[key] for case in cases for key in ("environment_seed", "optimizer_seed")]
    if len(seeds) != len(set(seeds)) or any(type(seed) is not int for seed in seeds):
        raise ValueError("Case seeds must be integer and individually unique across both roles.")


def register_study(folder: Path, searches: dict[int, Path], engine_path: Path,
                   study_path: Path = DEFAULT_CONFIG,
                   search_suite: Path = Path("configs/joint_relocation_v3/search.json"),
                   validation_suite: Path = Path("configs/joint_relocation_v3/validation.json")):
    settings = read_json(study_path)
    _, search_cases = load_suite(search_suite)
    _, validation_cases = load_suite(validation_suite)
    assert_cases(search_cases, 4)
    assert_cases(validation_cases, 8)
    roles = [case[key] for case in search_cases + validation_cases for key in ("environment_seed", "optimizer_seed")]
    if len(roles) != len(set(roles)):
        raise ValueError("Search and validation seeds collide across roles.")
    if set(searches) != {0, 1, 2} or len({path.resolve() for path in searches.values()}) != 3:
        raise ValueError("Register exactly three distinct search paths, indexed 0, 1 and 2.")
    if settings["search_replicates"] != 3 or settings["generation_slots_per_search"] != 30 or settings["shortlist_per_search"] != 3:
        raise ValueError("Study settings differ from the declared three-search, thirty-slot protocol.")
    if len(settings["search_seeds"]) != 3 or len(set(settings["search_seeds"])) != 3 or any(type(seed) is not int or not 0 <= seed < 2**32 for seed in settings["search_seeds"]):
        raise ValueError("Three independent recorded integer search seeds are required.")
    if settings["fixed_radius_multipliers"] != [.5, 1.0, 2.0, 4.0] or settings["fixed_counts"] != list(range(6)):
        raise ValueError("Fixed comparison grid differs from the prospective protocol.")
    if settings["analysis_seed"] != BOOTSTRAP_SEED or settings["bootstrap_resamples"] != BOOTSTRAP_REPLICATES or settings["primary_two_sided_interval_level"] != .975:
        raise ValueError("Analysis settings differ from the prospective protocol.")
    engine = read_json(engine_path)
    engine = engine.get("engine_config", engine)
    identities = [{"search_index": index, "run": str(searches[index].resolve()), "search_seed": settings["search_seeds"][index]} for index in range(3)]
    task_paths = {"evaluate.py": Path("tasks/joint_relocation_v3/evaluate.py"),
                  "initial.py": Path("tasks/joint_relocation_v3/initial.py"),
                  "joint_relocation.py": Path("src/adaptive_swarms/joint_relocation.py"),
                  "evolution_context.md": Path("tasks/joint_relocation_v3/context.md"),
                  "task_prompt.txt": Path("tasks/joint_relocation_v3/task_prompt.txt"),
                  "protocol.md": Path(settings["protocol"])}
    task_contents = {name: path.read_bytes() for name, path in task_paths.items()}
    task_contents["task_system_prompt.txt"] = (task_contents["task_prompt.txt"].decode() + "\n\n# Scientific context supplied to mutation\n\n" + task_contents["evolution_context.md"].decode()).encode()
    task_sources = {name: hashlib.sha256(content).hexdigest() for name, content in task_contents.items()}
    inputs = {"settings": settings, "searches": identities, "engine_config": engine,
              "search_cases": search_cases, "validation_cases": validation_cases,
              "execution_sources": execution_fingerprint(), "task_sources": task_sources, "analysis": analysis_specification()}
    signature = digest(inputs)
    path = folder / "registration.json"
    if path.exists():
        record = verify_registration(folder)
        if record["signature"] != signature:
            raise ValueError("Registered search identities or prospective settings changed.")
        return record
    for search in searches.values():
        if (search / "programs.sqlite").exists() or (search / "manifest.json").exists() or any(search.glob("gen_*")):
            raise ValueError("Register all search identities before research outcomes exist.")
    if (folder / "shortlists.json").exists() or (folder / "validation").exists():
        raise ValueError("Existing study outcomes require their original registration.")
    snapshot = folder / "runner_snapshot"
    snapshot.mkdir(parents=True, exist_ok=True)
    snapshots = {}
    for source, expected in inputs["execution_sources"].items():
        name = source.replace("/", "__")
        (snapshot / name).write_bytes(Path(source).read_bytes())
        snapshots[name] = expected
    for name, content in task_contents.items():
        (snapshot / ("task__" + name)).write_bytes(content)
        snapshots["task__" + name] = task_sources[name]
    atomic_json(folder / "study_config.json", settings)
    atomic_json(folder / "search_cases.json", {"cases": search_cases})
    atomic_json(folder / "validation_cases.json", {"cases": validation_cases})
    atomic_json(folder / "engine_config.json", engine)
    record = {"version": VERSION, "registered_at": now(), "source_revision": source_revision(),
              "signature": signature, **inputs, "runner_snapshot": snapshots,
              "protocol_sha256": file_sha(settings["protocol"]),
              "source_files": {str(path): file_sha(path) for path in (study_path, search_suite, validation_suite, engine_path)}}
    atomic_json(path, record)
    with EventLogger(folder) as log:
        log.event("study_registered", searches=identities, signature=signature,
                  message="Prospective identities, controls and analysis recorded before research outcomes.")
    return record


def verify_registration(folder):
    record = read_json(folder / "registration.json")
    if record["execution_sources"] != execution_fingerprint():
        raise ValueError("Scientific comparison sources changed after registration.")
    for name, expected in record["runner_snapshot"].items():
        if file_sha(folder / "runner_snapshot" / name) != expected:
            raise ValueError(f"Frozen source snapshot changed: {name}")
    fields = ("settings", "searches", "engine_config", "search_cases", "validation_cases", "execution_sources", "task_sources", "analysis")
    if digest({key: record[key] for key in fields}) != record["signature"]:
        raise ValueError("Registered prospective settings changed.")
    return record


def proven_constant(source):
    """Prove only side-effect-free direct returns; never infer from outcomes."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    def doc(node):
        return isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and type(node.value.value) is str
    nodes = [node for node in tree.body if not doc(node)]
    if len(nodes) != 1 or not isinstance(nodes[0], ast.FunctionDef):
        return None
    fn = nodes[0]
    args = fn.args.posonlyargs + fn.args.args
    if fn.name != "choose_relocation" or len(args) != 1 or fn.decorator_list or fn.args.defaults or fn.args.kw_defaults or fn.args.vararg or fn.args.kwarg or fn.args.kwonlyargs:
        return None
    if any(value is not None and not (isinstance(value, ast.Name) and value.id in {"dict", "int", "float"}) for value in [fn.returns, args[0].annotation]):
        return None
    body = [node for node in fn.body if not doc(node)]
    if len(body) != 1 or not isinstance(body[0], ast.Return) or not isinstance(body[0].value, ast.Dict):
        return None
    expression = body[0].value
    if len(expression.keys) != 2 or any(not isinstance(key, ast.Constant) or type(key.value) is not str for key in expression.keys):
        return None
    values = {key.value: value for key, value in zip(expression.keys, expression.values)}
    if set(values) != {"count", "radius_scale"}:
        return None
    count_node, radius_node = values["count"], values["radius_scale"]
    if isinstance(count_node, ast.Subscript) and isinstance(count_node.value, ast.Name) and count_node.value.id == args[0].arg and isinstance(count_node.slice, ast.Constant) and count_node.slice.value == "swarm_size":
        count = "swarm_size"
    elif isinstance(count_node, ast.Constant) and type(count_node.value) is int and 0 <= count_node.value <= 5:
        count = count_node.value
    else:
        return None
    if not isinstance(radius_node, ast.Constant) or type(radius_node.value) not in (float, int):
        return None
    radius = float(radius_node.value)
    if not math.isfinite(radius) or radius < 0:
        return None
    return {"count": count, "radius_scale": radius}


def native_search_record(identity, registration):
    run = Path(identity["run"])
    manifest = read_json(run / "manifest.json")
    required = {"task": "joint_relocation_v3", "evaluation_version": "joint_relocation_v3_score_reciprocal",
                "status": "search_complete", "generation_target": 30, "search_seed": identity["search_seed"]}
    if any(manifest.get(key) != value for key, value in required.items()):
        raise ValueError(f"Search {identity['search_index']} is not the registered completed V3 search.")
    if manifest.get("engine_config") != registration["engine_config"]:
        raise ValueError("Resolved engine configuration differs across registered searches.")
    for name, expected in registration["task_sources"].items():
        if manifest.get("source_hashes", {}).get(name) != expected or file_sha(run / "task_snapshot" / name) != expected:
            raise ValueError(f"Native task snapshot differs from prospective registration: {name}")
    _, cases = load_suite(run / "search-suite.json")
    if cases != registration["search_cases"]:
        raise ValueError("Search cases differ from registered shared development suite.")
    connection = sqlite3.connect(f"file:{(run / 'programs.sqlite').resolve()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows = [dict(row) for row in connection.execute("SELECT id,code,parent_id,generation,combined_score,correct,metadata,public_metrics,text_feedback FROM programs")]
        failures = terminal_failure_generations(run, connection)
    finally:
        connection.close()
    originals = [row for row in rows if not any(json.loads(row["metadata"] or "{}").get(key) for key in ("_is_island_copy", "is_island_copy", "island_copy"))]
    evaluated = {row["generation"] for row in originals}
    if evaluated | failures != set(range(30)):
        raise ValueError("Thirty terminal native slots require the evaluated/terminal-failure union to equal 0 through 29.")
    valid = [row for row in originals if row["correct"] and row["combined_score"] is not None and math.isfinite(row["combined_score"]) and row["combined_score"] > 0]
    if not any(row["generation"] == 0 for row in valid):
        raise ValueError("Registered search lacks a valid evaluated seed.")
    for row in valid:
        metrics = json.loads(row["public_metrics"] or "{}")
        error = metrics.get("mean_offline_error")
        if error is None:
            error = 1 / row["combined_score"] - 1
        if not math.isfinite(error) or error < 0:
            raise ValueError("Invalid native mean-error metric.")
        row.update(sha256=hashlib.sha256(row["code"].encode()).hexdigest(), search_mean_error=error)
    valid.sort(key=lambda row: (row["search_mean_error"], row["generation"], row["sha256"], row["id"]))
    unique = {}
    for row in valid:
        unique.setdefault(row["sha256"], row)
    return {**identity, "native_manifest_sha256": file_sha(run / "manifest.json"),
            "evaluated_generation_ids": sorted(evaluated), "terminal_failed_generation_ids": sorted(failures - evaluated),
            "terminal_generation_ids": sorted(evaluated | failures), "valid_source_distinct_programs": len(unique),
            "shortlist_rows": list(unique.values())[:3]}


def freeze_shortlists(folder):
    registration = verify_registration(folder)
    if (folder / "shortlists.json").exists():
        return verify_shortlists(folder)
    searches = [native_search_record(identity, registration) for identity in registration["searches"]]
    programs = {}
    (folder / "programs").mkdir(exist_ok=True)
    for search in searches:
        references = []
        for rank, row in enumerate(search.pop("shortlist_rows"), 1):
            name = "program_" + row["sha256"]
            policy = str(Path("programs") / f"{row['sha256']}.py")
            if name not in programs:
                (folder / policy).write_text(row["code"])
                programs[name] = {"name": name, "policy": policy, "sha256": row["sha256"],
                                  "proven_constant": proven_constant(row["code"]), "occurrences": []}
            occurrence = {"name": name, "sha256": row["sha256"], "search_index": search["search_index"],
                          "generation": row["generation"], "native_id": row["id"], "parent_id": row["parent_id"],
                          "search_rank": rank, "search_mean_error": row["search_mean_error"],
                          "search_score": row["combined_score"], "text_feedback": row["text_feedback"]}
            programs[name]["occurrences"].append(occurrence)
            references.append(occurrence)
        search["shortlist"] = references
    frozen = {"version": VERSION, "frozen_at": now(), "registration_sha256": file_sha(folder / "registration.json"),
              "searches": searches, "programs": programs,
              "selection_rule": "per search: lowest mean search error, earlier generation, source SHA-256; at most three source-distinct valid programs",
              "cross_search_aliases": [{"program": name, "occurrences": p["occurrences"]} for name, p in programs.items() if len(p["occurrences"]) > 1]}
    atomic_json(folder / "shortlists.json", frozen)
    with EventLogger(folder) as log:
        log.event("shortlists_frozen", unique_programs=len(programs), per_search=[len(s["shortlist"]) for s in searches])
    return frozen


def verify_shortlists(folder):
    verify_registration(folder)
    record = read_json(folder / "shortlists.json")
    if record["registration_sha256"] != file_sha(folder / "registration.json"):
        raise ValueError("Registration changed after shortlists froze.")
    for program in record["programs"].values():
        if file_sha(folder / program["policy"]) != program["sha256"]:
            raise ValueError("Frozen candidate source changed.")
    return record


def record_source_review(folder, review_path):
    shortlist = verify_shortlists(folder)
    review = read_json(review_path)
    expected = {p["sha256"] for p in shortlist["programs"].values()}
    if set(review.get("approved_source_sha256", [])) != expected or not review.get("reviewer") or not review.get("notes"):
        raise ValueError("Exact source review requires every unique shortlisted SHA, reviewer and notes.")
    path = folder / "source_review.json"
    if path.exists():
        saved = read_json(path)
        if saved["review"] != review:
            raise ValueError("Completed source review is immutable.")
        return saved
    record = {"reviewed_at": now(), "shortlists_sha256": file_sha(folder / "shortlists.json"), "review": review}
    atomic_json(path, record)
    return record


def verify_review(folder):
    shortlist = verify_shortlists(folder)
    review = read_json(folder / "source_review.json")
    if review["shortlists_sha256"] != file_sha(folder / "shortlists.json") or set(review["review"]["approved_source_sha256"]) != {p["sha256"] for p in shortlist["programs"].values()}:
        raise ValueError("Source review no longer matches exact shortlisted sources.")
    return shortlist


def fixed_name(count, radius):
    return f"fixed_k{count}_r{radius:g}".replace(".", "p")


def fixed_grid():
    return {fixed_name(k, radius): {"kind": "fixed", "count": k, "radius_scale": radius} for radius in (.5, 1.0, 2.0, 4.0) for k in range(6)}


def _constant_identity(action, config):
    count = config["particles_per_swarm"] if action["count"] == "swarm_size" else action["count"]
    # Zero-radius labels remain in method metadata; only literal/state-free
    # constant policies can ignore their previous_response_radius observation.
    return {"kind": "joint_constant", "count": count, "radius_scale": 0.0 if count == 0 else float(action["radius_scale"])}


def sampler_seed(method, config):
    return int(digest({"namespace": "joint_relocation_v3_joint_sampler", "master_seed": method["rng_master_seed"], "config": config})[:16], 16)


def method_identity(method, config):
    kind = method["kind"]
    if kind == "baseline":
        return _constant_identity({"count": 5, "radius_scale": 1.0}, config)
    if kind == "fixed":
        return _constant_identity(method, config)
    if kind == "program":
        if method.get("proven_constant") is not None:
            return _constant_identity(method["proven_constant"], config)
        return {"kind": "joint_program", "sha256": method["sha256"]}
    if kind == "component":
        constant = method["program"].get("proven_constant")
        if constant is not None:
            return _constant_identity({**constant, method["component"]: method["replacement"]}, config)
        return {"kind": "joint_component", "sha256": method["program"]["sha256"],
                "component": method["component"], "replacement": method["replacement"]}
    if kind == "joint_sampler":
        regime_cases = method["regime_cases"][regime_key(config)]
        pairs = {tuple(pair) for case in regime_cases for pair in case["action_pairs"]}
        if len(pairs) == 1:
            count, radius = next(iter(pairs))
            return _constant_identity({"count": count, "radius_scale": radius}, config)
        return {"kind": "joint_sampler", "distribution_sha256": digest(regime_cases),
                "rng_seed": sampler_seed(method, config), "rng_algorithm": "python.random.Random; uniform case then uniform full action pair"}
    raise ValueError(f"Unknown frozen method kind: {kind}")


class ComponentPolicy:
    """Call the original function on reached state before replacing one output."""
    def __init__(self, function, component, replacement):
        self.function, self.component, self.replacement = function, component, replacement
        self.original_decisions = []

    def __call__(self, observation):
        action = validate_decision(self.function(dict(observation)), observation["swarm_size"])
        self.original_decisions.append(dict(action))
        return {**action, self.component: self.replacement}


def joint_sampler_policy(regime_cases, rng_seed):
    """Sample a case equally, then a complete pair; never independent marginals."""
    if not regime_cases or any(not case["action_pairs"] for case in regime_cases):
        raise ValueError("Joint sampler requires a nonempty frozen pair list for every case.")
    rng = random.Random(rng_seed)
    def choose_relocation(_observation):
        case = regime_cases[rng.randrange(len(regime_cases))]
        count, radius = case["action_pairs"][rng.randrange(len(case["action_pairs"]))]
        return {"count": count, "radius_scale": radius}
    return choose_relocation


def build_policy(folder, method, config):
    kind = method["kind"]
    if kind == "baseline":
        function = constant_joint_policy(5, 1.0)
    elif kind == "fixed":
        function = constant_joint_policy(method["count"], method["radius_scale"])
    elif kind == "program":
        function = load_joint_policy(folder / method["policy"])
    elif kind == "component":
        function = ComponentPolicy(load_joint_policy(folder / method["program"]["policy"]), method["component"], method["replacement"])
    elif kind == "joint_sampler":
        function = joint_sampler_policy(method["regime_cases"][regime_key(config)], sampler_seed(method, config))
    else:
        raise ValueError(f"Unknown method kind: {kind}")
    return joint_policy_adapter(function)


def equal_regime_mean(values):
    groups = defaultdict(list)
    for case in values:
        groups[regime_key(case["config"])].append(case["offline_error"])
    return statistics.mean(statistics.mean(group) for group in groups.values())


def nominal_constant_action(method, config):
    """Nominal pair, retaining radius even when a zero-count cache canonicalizes it."""
    kind = method["kind"]
    action = None
    if kind == "baseline":
        action = {"count": 5, "radius_scale": 1.0}
    elif kind == "fixed":
        action = {key: method[key] for key in ("count", "radius_scale")}
    elif kind == "program":
        action = method.get("proven_constant")
    elif kind == "component" and method["program"].get("proven_constant") is not None:
        action = {**method["program"]["proven_constant"], method["component"]: method["replacement"]}
    elif kind == "joint_sampler":
        pairs = {tuple(pair) for case in method["regime_cases"][regime_key(config)] for pair in case["action_pairs"]}
        if len(pairs) == 1:
            count, radius = next(iter(pairs))
            action = {"count": count, "radius_scale": radius}
    if action is None:
        return None
    return {"count": config["particles_per_swarm"] if action["count"] == "swarm_size" else action["count"],
            "radius_scale": float(action["radius_scale"])}


def nominal_action_pairs(case, method=None):
    """Analyze an alias's defined actions without rewriting its measured checkpoint.

    Zero-count literal constants share trajectories while their unused radius
    labels differ. This explicit projection preserves those nominal labels in
    joint controls and action figures. It is not a claim of another execution.
    No-response cases stay empty; sampler construction owns the baseline fallback.
    """
    method = method or case.get("analysis_method_metadata")
    constant = nominal_constant_action(method, case["config"]) if method else None
    if constant is not None:
        return [[constant["count"], constant["radius_scale"]] for _ in case["response_log"]]
    return [[r["requested_count"], r["requested_radius_scale"]] for r in case["response_log"]]


def load_stage_outcomes(folder, stage):
    manifest = read_json(folder / stage / "manifest.json")
    if manifest["status"] != "completed":
        raise ValueError(f"{stage} is incomplete.")
    outcomes = {}
    for name, paths in manifest["case_artifacts"].items():
        if len(paths) != len(manifest["cases"]):
            raise ValueError("Stage is missing a planned method case.")
        values = []
        for path, config in zip(paths, manifest["cases"]):
            case = read_json(folder / stage / path)
            identity = method_identity(manifest["methods"][name], config)
            expected = digest({"signature": manifest["signature"], "config": config, "execution_identity": identity})
            if case.get("signature") != manifest["signature"] or case["config"] != config or case.get("cache_key") != expected or case.get("execution_identity") != identity:
                raise ValueError("Saved checkpoint provenance or execution identity differs.")
            validate_pair(case, case)
            # Each read creates a distinct view per nominal method. The saved
            # checkpoint and its actual response log are never rewritten.
            case["analysis_method_metadata"] = manifest["methods"][name]
            constant = nominal_constant_action(manifest["methods"][name], config)
            if constant is not None and any(r["requested_count"] != constant["count"] or r["requested_radius_scale"] != constant["radius_scale"] for r in case["response_log"]):
                case["nominal_action_projection"] = {"nominal_method": name, "executed_method": case["method"],
                    "nominal_action": constant, "reason": "Proven constant equivalence; preserve an aliased zero-count policy's unused nominal radius in action analysis. Raw measured response_log remains unchanged."}
            values.append(case)
        outcomes[name] = values
    return manifest, outcomes


def run_stage(folder, stage, cases, methods, frozen_sha):
    verify_review(folder)
    directory = folder / stage
    signature = digest({"version": VERSION, "stage": stage, "cases": cases, "methods": methods,
                        "freeze_sha256": frozen_sha, "execution_sources": execution_fingerprint()})
    path = directory / "manifest.json"
    if path.exists():
        manifest = read_json(path)
        if manifest["signature"] != signature:
            raise ValueError("Resume configuration differs from the frozen stage.")
        if manifest["status"] == "completed":
            _, saved = load_stage_outcomes(folder, stage)
            reference = next(iter(saved.values()))
            for values in saved.values():
                for a, b in zip(reference, values):
                    validate_pair(a, b)
            with EventLogger(directory) as log:
                log.event("stage_reused", stage=stage, cases=len(cases), methods=len(methods), message="Verified completed checkpoints; no evaluations repeated.")
            return read_json(directory / "summary.json")
    else:
        manifest = {"version": VERSION, "stage": stage, "signature": signature, "created_at": now(),
                    "cases": cases, "methods": methods, "freeze_sha256": frozen_sha,
                    "execution_sources": execution_fingerprint(), "case_artifacts": {name: [] for name in methods}, "aliases": []}
    manifest["status"] = "running"
    atomic_json(path, manifest)
    outcomes = {name: [] for name in methods}
    aliases, completed, reused = [], 0, 0
    try:
        with EventLogger(directory) as log:
            log.event("stage_started", stage=stage, cases=len(cases), nominal_methods=len(methods))
            for index, config in enumerate(cases):
                seen, reference = {}, None
                for name, method in methods.items():
                    identity = method_identity(method, config)
                    cache_key = digest({"signature": signature, "config": config, "execution_identity": identity})
                    relative = f"cache/{cache_key}.json.gz"
                    checkpoint = directory / relative
                    if cache_key in seen:
                        original, result = seen[cache_key]
                        aliases.append({"case_index": index, "method": name, "alias_of": original, "cache_key": cache_key,
                                        "execution_identity": identity,
                                        "note": "Execution-equivalent source/constant; nominal actions and encoding fields remain defined by method metadata. Zero-count constant radius can change logged previous_response_radius without changing optimizer trajectories."})
                        log.event("case_aliased", stage=stage, case=index + 1, method=name, alias_of=original)
                    elif checkpoint.exists():
                        result = read_json(checkpoint)
                        if result.get("signature") != signature or result["config"] != config or result.get("execution_identity") != identity or result.get("cache_key") != cache_key:
                            raise ValueError("Existing case cannot be reused under changed provenance.")
                        reused += 1
                        log.event("case_reused", stage=stage, case=index + 1, method=name, offline_error=result["offline_error"])
                    else:
                        verify_review(folder)
                        log.set_activity(f"{stage}, {name}, case {index + 1}/{len(cases)}")
                        log.event("case_started", stage=stage, case=index + 1, method=name, budget=config["budget"],
                                  completed_executions=completed, reused_executions=reused,
                                  environment_seed=config["environment_seed"], optimizer_seed=config["optimizer_seed"])
                        def progress(event):
                            fields = dict(event)
                            kind = fields.pop("event", "simulation_progress")
                            fields.pop("config", None)
                            log.event(kind, stage=stage, method=name, case=index + 1, **fields)
                        start = time.monotonic()
                        policy = build_policy(folder, method, config)
                        result = run_case(config, policy=policy, progress=progress)
                        annotate_joint_log(result, policy)
                        if isinstance(policy.choose_relocation, ComponentPolicy):
                            originals = policy.choose_relocation.original_decisions
                            if len(originals) != len(result["response_log"]):
                                raise ValueError("Component intervention original action log differs.")
                            for response, action in zip(result["response_log"], originals):
                                response["original_candidate_action"] = action
                                response["component_substitution"] = {"component": method["component"], "replacement": method["replacement"]}
                        result.update(signature=signature, cache_key=cache_key, execution_identity=identity, method=name,
                                      case_index=index, wall_time_seconds=time.monotonic() - start)
                        write_compressed_json(checkpoint, result)
                        completed += 1
                        log.event("case_completed", stage=stage, case=index + 1, method=name, offline_error=result["offline_error"],
                                  elapsed_case_seconds=result["wall_time_seconds"], completed_executions=completed, checkpoint=str(checkpoint))
                    validate_pair(result, result if reference is None else reference)
                    reference = result if reference is None else reference
                    seen.setdefault(cache_key, (name, result))
                    outcomes[name].append(result)
                    paths = manifest["case_artifacts"][name]
                    if len(paths) <= index:
                        paths.append(relative)
                    elif paths[index] != relative:
                        raise ValueError("Saved alias path differs from execution identity.")
                    manifest["aliases"] = aliases
                    manifest["completed_method_cases"] = {key: len(value) for key, value in outcomes.items()}
                    atomic_json(path, manifest)
                log.event("paired_case_completed", stage=stage, case=index + 1, total_cases=len(cases))
            summary = {"status": "completed", "completed_at": now(), "stage": stage, "case_count": len(cases),
                       "method_mean_offline_errors": {name: equal_regime_mean(values) for name, values in outcomes.items()},
                       "method_case_errors": {name: [case["offline_error"] for case in values] for name, values in outcomes.items()},
                       "unique_executed_method_cases": len({p for paths in manifest["case_artifacts"].values() for p in paths}), "aliases": aliases}
            atomic_json(directory / "summary.json", summary)
            manifest.update(status="completed", completed_at=now())
            atomic_json(path, manifest)
            log.event("stage_completed", stage=stage, unique_executed_method_cases=summary["unique_executed_method_cases"],
                      nominal_methods=len(methods), aliases=len(aliases), method_mean_offline_errors=summary["method_mean_offline_errors"])
    except BaseException as exc:
        manifest.update(status="interrupted_or_failed", last_error=f"{type(exc).__name__}: {exc}")
        atomic_json(path, manifest)
        raise
    return summary


def validate_shortlists(folder):
    shortlists = verify_review(folder)
    registration = verify_registration(folder)
    cases = registration["validation_cases"]
    assert_cases(cases, 8)
    methods = fixed_grid()
    methods.update({name: {"kind": "program", **program} for name, program in shortlists["programs"].items()})
    return run_stage(folder, "validation", cases, methods, file_sha(folder / "shortlists.json"))


def freeze_joint_sampler(cases, method=None):
    groups = defaultdict(list)
    for index, case in enumerate(cases):
        pairs = nominal_action_pairs(case, method)
        groups[regime_key(case["config"])].append({"validation_case_index": index,
            "response_count": len(pairs), "no_response_baseline_fallback": not pairs,
            "action_pairs": pairs or [[5, 1.0]], "nominal_action_projection": case.get("nominal_action_projection")})
    return {"kind": "joint_sampler", "regime_cases": dict(groups), "rng_master_seed": CONTROL_MASTER_SEED,
            "sampling": "uniform validation case within regime, then uniform response action pair within that case",
            "rng": "dedicated per-final-case python.random.Random; seed SHA-256 derived from namespace, frozen master seed and case configuration",
            "intervention": "removes current-state association and changes temporal dependence; preserves full joint action pair and equal-case weighting"}


def select_and_freeze(folder):
    shortlist = verify_review(folder)
    registration = verify_registration(folder)
    manifest, outcomes = load_stage_outcomes(folder, "validation")
    summary = read_json(folder / "validation/summary.json")
    provenance = {"shortlists_sha256": file_sha(folder / "shortlists.json"), "validation_signature": manifest["signature"],
                  "validation_summary_sha256": file_sha(folder / "validation/summary.json")}
    path = folder / "selection.json"
    if path.exists():
        record = read_json(path)
        if record["provenance"] != provenance:
            raise ValueError("Validation changed after selection freeze.")
        return record
    errors = {name: equal_regime_mean(values) for name, values in outcomes.items()}
    if errors != summary["method_mean_offline_errors"]:
        raise ValueError("Validation summary differs from saved case measurements.")
    winners = []
    for search in shortlist["searches"]:
        winner = min(search["shortlist"], key=lambda p: (errors[p["name"]], p["search_index"], p["generation"], p["sha256"]))
        winners.append({**winner, "validation_mean_error": errors[winner["name"]], "method": f"winner_search_{search['search_index']}"})
    overall = min(winners, key=lambda p: (p["validation_mean_error"], p["search_index"], p["generation"], p["sha256"]))
    grid = fixed_grid()
    fixed = min(grid, key=lambda name: (errors[name], grid[name]["count"], grid[name]["radius_scale"]))
    selected_program = {"kind": "program", **shortlist["programs"][overall["name"]]}
    sampler = freeze_joint_sampler(outcomes[overall["name"]], selected_program)
    methods = {winner["method"]: {"kind": "program", **shortlist["programs"][winner["name"]]} for winner in winners}
    methods.update(baseline={"kind": "baseline"}, best_fixed=grid[fixed],
                   radius_replaced={"kind": "component", "program": selected_program, "component": "radius_scale", "replacement": grid[fixed]["radius_scale"]},
                   count_replaced={"kind": "component", "program": selected_program, "component": "count", "replacement": grid[fixed]["count"]},
                   joint_sampler=sampler)
    record = {"version": VERSION, "frozen_at": now(), "provenance": provenance,
              "per_search_winners": winners, "overall_winner": overall, "overall_winner_method": overall["method"],
              "selected_fixed_label": fixed, "selected_fixed_pair": grid[fixed], "selected_fixed_validation_error": errors[fixed],
              "validation_mean_errors": errors, "fixed_grid": grid, "methods": methods, "joint_sampler": sampler,
              "selection_rule": "lowest equal-regime validation error; programs earlier search index, earlier generation, source hash; fixed pairs smaller count then smaller radius",
              "analysis": registration["analysis"], "final_cases_existed_at_freeze": False}
    if (folder / "final_cases.json").exists():
        raise ValueError("Final cases exist before the required selection/control/analysis freeze.")
    atomic_json(path, record)
    with EventLogger(folder) as log:
        log.event("selection_and_controls_frozen", overall=overall["method"], selected_fixed=fixed, means={w["method"]: w["validation_mean_error"] for w in winners})
    return record


def collect_used_seeds(roots, exclude=(), progress=None):
    """Reserve scalar/list RNG seeds across roles, including historical searches."""
    excluded = [Path(p).resolve() for p in exclude]
    files, found, sources = set(), set(), []
    def visit(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if (key == "seed" or key.endswith("_seed")) and type(child) is int:
                    found.add(child)
                elif key.endswith("_seeds") and isinstance(child, list):
                    found.update(item for item in child if type(item) is int)
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    for root in roots:
        root = Path(root)
        paths = [root] if root.is_file() else list(root.rglob("*.json")) + list(root.rglob("*.json.gz"))
        for path in sorted(paths):
            resolved = path.resolve()
            if resolved in files or any(resolved == p or p in resolved.parents for p in excluded):
                continue
            files.add(resolved)
            before = len(found)
            try:
                visit(read_json(path))
            except (ValueError, OSError) as exc:
                raise ValueError(f"Cannot verify historical seed evidence {path}: {exc}") from exc
            if len(found) != before:
                sources.append({"path": str(path), "sha256": file_sha(path)})
            if progress and len(files) % 250 == 0:
                progress(len(files), len(found))
    return {"reserved_seed_values": sorted(found), "files_inspected": len(files), "sources_adding_seeds": sources,
            "rule": "all scalar seed/*_seed values and integer *_seeds lists from saved JSON/GZ; reserve across all roles"}


def generate_final_cases(folder, roots):
    registration = verify_registration(folder)
    selection = select_and_freeze(folder)
    path = folder / "final_cases.json"
    expected = file_sha(folder / "selection.json")
    if path.exists():
        saved = read_json(path)
        if saved["selection_sha256"] != expected:
            raise ValueError("Final cases belong to a different selection freeze.")
        assert_cases(saved["cases"], 20)
        return saved
    with EventLogger(folder) as log:
        log.set_activity("Inventorying historical RNG seeds before fresh final generation")
        log.event("final_seed_inventory_started", roots=[str(p) for p in roots])
        audit = collect_used_seeds([*roots, folder / "registration.json", *(Path(s["run"]) for s in registration["searches"])],
                                  progress=lambda files, seeds: log.event("seed_inventory_progress", files=files, reserved_seeds=seeds))
        forbidden = set(audit["reserved_seed_values"])
        master_seed = secrets.randbits(128)
        rng = random.Random(master_seed)
        def fresh():
            while True:
                value = rng.randrange(1, 2**31)
                if value not in forbidden:
                    forbidden.add(value)
                    return value
        template = registration["validation_cases"][0]
        cases = [{**template, "move_severity": severity, "period": period,
                  "environment_seed": fresh(), "optimizer_seed": fresh()}
                 for severity, period in REGIMES for _ in range(20)]
        assert_cases(cases, 20)
        record = {"version": VERSION, "generated_at": now(), "selection_frozen_at": selection["frozen_at"],
                  "selection_sha256": expected, "seed_generation_master_seed": master_seed,
                  "seed_generation_algorithm": "python.random.Random initialized from secrets.randbits(128) only after selection/control/analysis freeze",
                  "historical_seed_audit": audit, "cases": cases}
        atomic_json(path, record)
        log.event("final_cases_generated", cases=80, unique_new_seed_values=160, selection_frozen_at=selection["frozen_at"])
    return record


def run_final(folder, roots):
    cases = generate_final_cases(folder, roots)
    selection = read_json(folder / "selection.json")
    if len(selection["methods"]) > 8:
        raise ValueError("Final method plan exceeds eight nominal methods.")
    return run_stage(folder, "final", cases["cases"], selection["methods"], file_sha(folder / "selection.json"))


def paired_statistics(deltas, regimes, interval_level=.95):
    groups = defaultdict(list)
    for delta, regime in zip(deltas, regimes):
        groups[regime].append(float(delta))
    result = {"n": len(deltas), "mean_delta": statistics.mean(statistics.mean(group) for group in groups.values()),
              "interval_level": interval_level, "improved_cases": sum(x < 0 for x in deltas),
              "worsened_cases": sum(x > 0 for x in deltas), "tied_cases": sum(x == 0 for x in deltas)}
    if all(len(values) > 1 for values in groups.values()):
        rng = np.random.default_rng(BOOTSTRAP_SEED)
        samples = np.zeros(BOOTSTRAP_REPLICATES)
        for key in sorted(groups):
            values = np.asarray(groups[key])
            samples += rng.choice(values, size=(BOOTSTRAP_REPLICATES, len(values))).mean(axis=1) / len(groups)
        tail = (1 - interval_level) / 2
        result["bootstrap_interval"] = np.quantile(samples, [tail, 1 - tail]).tolist()
        result["stratified_se_delta"] = math.sqrt(sum(statistics.variance(group) / len(group) for group in groups.values())) / len(groups)
    else:
        result.update(bootstrap_interval=None, stratified_se_delta=None)
    return result


def contrast_record(deltas, configs, level, method_errors=None, comparator_errors=None):
    regimes = [regime_key(config) for config in configs]
    by_regime = {}
    for key in sorted(set(regimes)):
        indices = [i for i, regime in enumerate(regimes) if regime == key]
        values = [deltas[i] for i in indices]
        by_regime[key] = paired_statistics(values, [key] * len(indices), level)
        if method_errors is not None:
            by_regime[key].update(mean_method_error=statistics.mean(method_errors[i] for i in indices),
                                  mean_comparator_error=statistics.mean(comparator_errors[i] for i in indices))
    rows = []
    for index, config in enumerate(configs):
        row = {"case_index": index, "environment_seed": config["environment_seed"], "optimizer_seed": config["optimizer_seed"], "regime": regimes[index], "delta": deltas[index]}
        if method_errors is not None:
            row.update(method_offline_error=method_errors[index], comparator_offline_error=comparator_errors[index])
        rows.append(row)
    return {**paired_statistics(deltas, regimes, level), "regimes": by_regime, "cases": rows}


def joint_behavior(cases):
    result = behavior_summary(cases)
    regimes = defaultdict(list)
    for case in cases:
        regimes[regime_key(case["config"])].append(case)
    by_regime = {}
    for key, values in regimes.items():
        pooled = Counter()
        weighted = defaultdict(float)
        no_response = []
        responding_cases = sum(bool(case["response_log"]) for case in values)
        for index, case in enumerate(values):
            counts = Counter(tuple(pair) for pair in nominal_action_pairs(case))
            pooled.update(counts)
            if counts:
                for pair, count in counts.items():
                    weighted[pair] += count / sum(counts.values()) / responding_cases
            else:
                no_response.append(index)
        by_regime[key] = {"response_count": sum(pooled.values()),
                          "joint_actions": [{"count": pair[0], "radius_scale": pair[1], "responses": pooled[pair], "equal_case_probability": weighted[pair]} for pair in sorted(weighted)],
                          "no_response_cases_within_regime": no_response,
                          "responding_case_count": responding_cases,
                          "action_probability_weighting": "equal weight among cases with at least one response; no-response cases omitted from empirical action probabilities",
                          "incomplete_responses": sum(not r["completed"] for c in values for r in c["response_log"]),
                          "mean_error": statistics.mean(c["offline_error"] for c in values)}
    result["regimes"] = by_regime
    result["nominal_action_projections"] = [{"case_index": index, **case["nominal_action_projection"]} for index, case in enumerate(cases) if case.get("nominal_action_projection")]
    result["joint_action_semantics"] = "Measured requested action pairs except explicit proven-constant zero-count alias projections; projections retain nominal unused radius and do not change measurements."
    result["pooled_radius_summary_semantics"] = "mean_radius_scale uses raw representative execution logs; nominal alias actions are reported explicitly in joint_actions and nominal_action_projections."
    result["worst_cases"] = sorted([{"case_index": index, "offline_error": case["offline_error"], "regime": regime_key(case["config"]),
                                      "maximum_environment_offline_error": max((c["environment_offline_error"] for c in case["environment_changes"]), default=None)} for index, case in enumerate(cases)], key=lambda row: row["offline_error"], reverse=True)
    result["measurement_note"] = "Full case checkpoints retain per-environment error, 500-query traces, swarm counts, observations and objective accounting. All large errors remain in analysis; no post-change interpolation is interpreted as measured immediate recovery."
    return result


def analyze(folder):
    verify_review(folder)
    selection = select_and_freeze(folder)
    manifest, outcomes = load_stage_outcomes(folder, "final")
    if manifest["freeze_sha256"] != file_sha(folder / "selection.json") or manifest["methods"] != selection["methods"]:
        raise ValueError("Final executions differ from frozen selected methods or controls.")
    reference = outcomes["baseline"]
    pairing = {}
    for name, values in outcomes.items():
        pairing[name] = [validate_pair(a, b) for a, b in zip(reference, values)]
    overall = selection["overall_winner_method"]
    errors = {name: [case["offline_error"] for case in values] for name, values in outcomes.items()}
    comparisons = {}
    pairs = [(winner["method"], comparator) for winner in selection["per_search_winners"] for comparator in ("baseline", "best_fixed")]
    pairs += [(overall, comparator) for comparator in ("radius_replaced", "count_replaced", "joint_sampler")]
    for method, comparator in pairs:
        primary = method == overall and comparator in {"baseline", "best_fixed"}
        deltas = [a - b for a, b in zip(errors[method], errors[comparator])]
        comparisons[f"{method}_minus_{comparator}"] = {"method": method, "comparator": comparator,
            "role": "primary" if primary else "descriptive secondary", "sign": "negative favors named method",
            **contrast_record(deltas, manifest["cases"], .975 if primary else .95, errors[method], errors[comparator])}
    interaction_values = [e - radius - count + fixed for e, radius, count, fixed in zip(errors[overall], errors["radius_replaced"], errors["count_replaced"], errors["best_fixed"])]
    interaction = {"expression": "E - radius_replaced - count_replaced + best_fixed", "role": "descriptive closed-loop component interaction",
                   **contrast_record(interaction_values, manifest["cases"], .95)}
    primary_results = [value for value in comparisons.values() if value["role"] == "primary"]
    superiority = all(value["bootstrap_interval"] is not None and value["bootstrap_interval"][1] < 0 for value in primary_results)
    result = {"version": VERSION, "status": "completed", "analyzed_at": now(), "paired_case_count": len(reference),
              "overall_winner_method": overall, "method_mean_offline_errors": {name: equal_regime_mean(values) for name, values in outcomes.items()},
              "comparisons": comparisons, "interaction": interaction,
              "claim": {"superiority_over_both_primary_controls_supported": superiority, "rule": selection["analysis"]["claim_rule"], "primary_contrasts": [key for key, value in comparisons.items() if value["role"] == "primary"]},
              "pairing_checks": pairing, "behavior": {name: joint_behavior(values) for name, values in outcomes.items()},
              "selection": selection, "aliases": manifest["aliases"], "uncertainty": selection["analysis"],
              "execution_accounting": {"final_unique_method_cases": len({path for paths in manifest["case_artifacts"].values() for path in paths}), "final_nominal_methods": len(outcomes)}}
    atomic_json(folder / "analysis.json", result)
    return result


@contextmanager
def exclusive_study(folder):
    import fcntl
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / ".study-controller.lock").open("a+") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Another controller owns this comparison study; attach to its progress.") from exc
        yield


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["register", "freeze-shortlists", "review", "validate", "select", "final", "analyze"])
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--search", action="append", default=[], metavar="INDEX=PATH")
    parser.add_argument("--engine-config", type=Path)
    parser.add_argument("--study-config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--search-suite", type=Path, default=Path("configs/joint_relocation_v3/search.json"))
    parser.add_argument("--validation-suite", type=Path, default=Path("configs/joint_relocation_v3/validation.json"))
    parser.add_argument("--review-record", type=Path)
    parser.add_argument("--seed-roots", type=Path, nargs="+", default=[Path("configs"), Path("results"), Path("artifacts")])
    args = parser.parse_args()
    with exclusive_study(args.run):
        if args.stage == "register":
            if not args.engine_config:
                parser.error("register requires --engine-config with resolved prospective engine settings")
            searches = {}
            for entry in args.search:
                index, separator, path = entry.partition("=")
                if not separator or not index.isdigit() or int(index) in searches:
                    parser.error("Use unique --search INDEX=PATH entries")
                searches[int(index)] = Path(path)
            result = register_study(args.run, searches, args.engine_config, args.study_config, args.search_suite, args.validation_suite)
        elif args.stage == "freeze-shortlists":
            result = freeze_shortlists(args.run)
        elif args.stage == "review":
            if not args.review_record:
                parser.error("review requires --review-record")
            result = record_source_review(args.run, args.review_record)
        elif args.stage == "validate":
            result = validate_shortlists(args.run)
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
