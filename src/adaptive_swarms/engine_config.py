"""Explicit native Shinka profiles, subscription routes, and immutable resume intent.

Resolution imports no Shinka clients and performs no model calls. Optional
machinery is requested explicitly; a missing local embedding route is an error.
"""
from __future__ import annotations

import copy
import hashlib
import ipaddress
import json
import math
import re
import socket
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

DEFAULT_MODEL = "gpt-6-astra"
SUPPORTED_EFFORTS = {"low", "medium", "high", "xhigh"}
HISTORICAL_EVOLUTION = {
    "llm_models": ["$codex"], "llm_dynamic_selection": "fixed",
    "llm_kwargs": {"temperatures": [0.0], "max_tokens": 16384},
    "patch_types": ["diff", "full", "cross"], "patch_type_probs": [0.5, 0.3, 0.2],
    "max_patch_resamples": 1, "max_patch_attempts": 1, "max_novelty_attempts": 1,
    "embedding_model": None, "novelty_llm_models": None,
    "meta_rec_interval": None, "meta_llm_models": None,
    "evolve_prompts": False, "use_text_feedback": True, "enable_wandb_logging": False,
    "code_embed_sim_threshold": 0.99,
}
HISTORICAL_DATABASE = {
    "num_islands": 2, "archive_size": 40,
    "num_archive_inspirations": 1, "num_top_k_inspirations": 1,
    "parent_selection_strategy": "weighted", "parent_selection_lambda": 10.0,
    "migration_interval": 10, "migration_rate": 0.0,
    "island_elitism": True, "enforce_island_separation": True,
}
EVOLUTION_KEYS = set(HISTORICAL_EVOLUTION) | {
    "meta_llm_kwargs", "novelty_llm_kwargs", "llm_dynamic_selection_kwargs",
    "meta_max_recommendations", "sample_single_meta_rec",
}
DATABASE_KEYS = set(HISTORICAL_DATABASE) | {
    "elite_selection_ratio", "island_selection_strategy", "exploitation_alpha",
    "exploitation_ratio", "archive_selection_strategy",
}


def digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def codex_route(model: str, effort: str | None) -> str:
    if not isinstance(model, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", model):
        raise ValueError("--model must be a Codex model name, not a provider route or URL.")
    if effort is not None and effort not in SUPPORTED_EFFORTS:
        raise ValueError(f"Unsupported inner Codex effort {effort!r}; pinned Shinka supports {sorted(SUPPORTED_EFFORTS)}. No effort was substituted.")
    return f"headless/codex@{model}" + (f"?effort={effort}" if effort else "")


def describe_route(route: str) -> dict:
    if not isinstance(route, str) or not route.startswith("headless/codex@"):
        raise ValueError("All LLM roles require explicit headless/codex@ subscription routes; paid API routes are not authorized.")
    body = route.removeprefix("headless/codex@")
    model, _, query = body.partition("?")
    options = parse_qs(query, keep_blank_values=True)
    if set(options) - {"effort"} or any(len(values) != 1 for values in options.values()):
        raise ValueError(f"Unsupported Codex route options: {route}")
    effort = options.get("effort", [None])[0]
    if codex_route(model, effort) != route:
        raise ValueError(f"Invalid Codex route: {route}")
    return {"route": route, "model_requested": model, "inner_effort_requested": effort,
            "inner_effort_effective": None,
            "status": "configured; actual model and effort require invocation evidence"}


def embedding_endpoint(route: str):
    if not isinstance(route, str) or not route.startswith("local/") or "@" not in route:
        raise ValueError("Novelty requires --embedding-model 'local/<served-model>@http://127.0.0.1:<port>/v1'; no paid embedding fallback is configured.")
    model, url = route[len("local/"):].split("@", 1)
    parsed = urlsplit(url)
    try:
        local = parsed.hostname == "localhost" or ipaddress.ip_address(parsed.hostname or "").is_loopback
    except ValueError:
        local = False
    if not model or parsed.scheme not in {"http", "https"} or not local or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path.rstrip("/") != "/v1":
        raise ValueError("Embedding route must name a served model at a loopback http(s)://host[:port]/v1 endpoint, without credentials or query parameters.")
    # Accessing port also validates malformed or out-of-range port values.
    return parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80)


def validate_engine(evolution: dict, database: dict) -> None:
    if not isinstance(evolution.get("llm_models"), list) or not evolution["llm_models"]:
        raise ValueError("llm_models must contain at least one subscription mutation route.")
    for key in ("llm_models", "meta_llm_models", "novelty_llm_models"):
        routes = evolution.get(key)
        if routes is not None:
            if not isinstance(routes, list) or not routes or len(routes) != len(set(routes)):
                raise ValueError(f"{key} must contain distinct subscription model routes.")
            for route in routes:
                describe_route(route)
    selector = evolution["llm_dynamic_selection"]
    if selector not in {"fixed", "ucb", "thompson"}:
        raise ValueError("llm_dynamic_selection must be fixed, ucb, or thompson.")
    if selector != "fixed" and len(evolution["llm_models"]) < 2:
        raise ValueError("Adaptive model selection requires at least two distinct mutation routes.")
    if bool(evolution["meta_rec_interval"]) != bool(evolution["meta_llm_models"]):
        raise ValueError("Meta-scratchpad requires both meta_rec_interval and meta_llm_models.")
    if bool(evolution["embedding_model"]) != bool(evolution["novelty_llm_models"]):
        raise ValueError("This profile requires both a local embedding model and novelty_llm_models; partial novelty configuration is not activated silently.")
    if evolution["embedding_model"]:
        embedding_endpoint(evolution["embedding_model"])
    if evolution["evolve_prompts"] or evolution["enable_wandb_logging"]:
        raise ValueError("This launcher supports fixed task prompts and native local logs; prompt evolution and W&B require a separate explicit integration.")
    for key in ("use_text_feedback", "evolve_prompts", "enable_wandb_logging", "sample_single_meta_rec"):
        if key in evolution and type(evolution[key]) is not bool:
            raise ValueError(f"{key} must be a JSON Boolean.")
    types, probabilities = evolution["patch_types"], evolution["patch_type_probs"]
    if not isinstance(types, list) or not types or len(types) != len(set(types)) or set(types) - {"diff", "full", "cross"}:
        raise ValueError("patch_types must be distinct native diff/full/cross proposal types.")
    if len(types) != len(probabilities) or any(not isinstance(p, (int, float)) or not math.isfinite(p) or p < 0 for p in probabilities) or not math.isclose(sum(probabilities), 1.0):
        raise ValueError("patch_type_probs must be nonnegative and sum to one.")
    for key in ("max_patch_resamples", "max_patch_attempts", "max_novelty_attempts", "meta_rec_interval", "meta_max_recommendations"):
        value = evolution.get(key)
        if value is not None and (type(value) is not int or value < 1):
            raise ValueError(f"{key} must be a positive integer.")
    for key in ("num_islands", "archive_size", "migration_interval", "num_archive_inspirations", "num_top_k_inspirations"):
        value = database[key]
        minimum = 0 if "inspirations" in key else 1
        if type(value) is not int or value < minimum:
            raise ValueError(f"{key} must be an integer >= {minimum}.")
    if not 0 <= database["migration_rate"] <= 1 or not -1 <= evolution["code_embed_sim_threshold"] <= 1:
        raise ValueError("Migration rate must be in [0, 1] and cosine similarity threshold in [-1, 1].")
    if database["parent_selection_strategy"] not in {"weighted", "power_law", "beam_search"}:
        raise ValueError("Unknown native parent selection strategy.")


def build_engine(definition: dict | None = None, *, model=DEFAULT_MODEL, effort=None, embedding_model=None) -> dict:
    definition = copy.deepcopy(definition if definition is not None else {"schema_version": 1, "name": "historical"})
    if not isinstance(definition, dict):
        raise ValueError("Engine profile must be a JSON object.")
    if set(definition) - {"schema_version", "name", "description", "evolution", "database"} or definition.get("schema_version") != 1:
        raise ValueError("Unknown engine-profile schema or keys; expected schema_version 1.")
    evolution = copy.deepcopy(HISTORICAL_EVOLUTION)
    database = copy.deepcopy(HISTORICAL_DATABASE)
    for section, target, allowed in (("evolution", evolution, EVOLUTION_KEYS), ("database", database, DATABASE_KEYS)):
        overrides = definition.get(section, {})
        if not isinstance(overrides, dict) or set(overrides) - allowed:
            raise ValueError(f"Unsupported {section} settings in engine profile.")
        target.update(overrides)
    route = codex_route(model, effort)
    for role in ("llm_models", "meta_llm_models", "novelty_llm_models"):
        if evolution.get(role) is not None:
            evolution[role] = [route if item == "$codex" else item for item in evolution[role]]
    if embedding_model is not None:
        evolution["embedding_model"] = embedding_model
    if evolution["embedding_model"] == "$local_embedding":
        raise ValueError("Requested native novelty filtering needs --embedding-model 'local/<served-model>@http://127.0.0.1:<port>/v1'. Configuration resolution performs no downloads or model calls.")
    validate_engine(evolution, database)
    result = {"schema_version": 1, "profile_name": definition.get("name", "custom"),
              "profile_definition": definition, "default_model": model, "default_effort": effort,
              "evolution": evolution, "database": database}
    result["sha256"] = digest(result)
    return result


def resolve_engine(*, profile_path: Path | None = None, model=None, effort=None,
                   embedding_model=None, saved_manifest: dict | None = None) -> dict:
    saved = (saved_manifest or {}).get("engine_config")
    if saved:
        if digest({k: v for k, v in saved.items() if k != "sha256"}) != saved.get("sha256"):
            raise ValueError("Saved engine configuration hash differs; refusing resume.")
        validate_engine(saved["evolution"], saved["database"])
    elif saved_manifest is not None:
        # Published historical launches had this exact profile. Prefer the last
        # recorded continuation's route when recovering pre-profile manifests.
        previous = (saved_manifest.get("resume_attempts") or [saved_manifest])[-1]
        saved = build_engine(model=previous.get("model_requested", saved_manifest.get("model_requested", DEFAULT_MODEL)),
                             effort=previous.get("inner_effort_requested", saved_manifest.get("inner_effort_requested")))
    if saved is not None and all(value is None for value in (profile_path, model, effort, embedding_model)):
        return copy.deepcopy(saved)
    definition = json.loads(profile_path.read_text()) if profile_path else (saved["profile_definition"] if saved else None)
    resolved = build_engine(definition, model=model or (saved["default_model"] if saved else DEFAULT_MODEL),
                            effort=effort if effort is not None else (saved["default_effort"] if saved else None),
                            embedding_model=embedding_model or (saved["evolution"]["embedding_model"] if saved else None))
    if saved is not None and any(resolved[key] != saved[key] for key in ("evolution", "database", "default_model", "default_effort")):
        raise ValueError("Engine settings differ from the saved run. Resume inherits its recorded profile; use a new run for a different engine configuration.")
    return copy.deepcopy(saved) if saved is not None else resolved


def native_settings(engine: dict, *, seed_only=False) -> tuple[dict, dict]:
    evolution, database = copy.deepcopy(engine["evolution"]), copy.deepcopy(engine["database"])
    if seed_only:
        evolution.update(llm_models=[], llm_dynamic_selection=None, embedding_model=None,
                         novelty_llm_models=None, meta_rec_interval=None, meta_llm_models=None)
    return evolution, database


def feature_state(engine: dict, *, seed_only=False) -> dict:
    evolution, database = native_settings(engine, seed_only=seed_only)
    return {"status": "resolved configuration; runtime mechanisms require event evidence",
            "profile": engine["profile_name"], "sha256": engine["sha256"], "seed_only": seed_only,
            "parent_sampling": database["parent_selection_strategy"], "num_islands": database["num_islands"],
            "migration_rate": database["migration_rate"], "migration_interval": database["migration_interval"],
            "archive_inspirations": database["num_archive_inspirations"], "top_k_inspirations": database["num_top_k_inspirations"],
            "patch_types": evolution["patch_types"], "patch_type_probs": evolution["patch_type_probs"],
            "novelty_configured": bool(evolution["embedding_model"] and evolution["novelty_llm_models"]),
            "embedding_model": evolution["embedding_model"], "novelty_attempts": evolution["max_novelty_attempts"],
            "meta_configured": bool(evolution["meta_rec_interval"] and evolution["meta_llm_models"]),
            "meta_interval": evolution["meta_rec_interval"], "text_feedback": evolution["use_text_feedback"],
            "model_selection": evolution["llm_dynamic_selection"],
            "model_roles": {role: [describe_route(route) for route in evolution.get(key) or []]
                            for role, key in (("mutation", "llm_models"), ("meta", "meta_llm_models"), ("novelty", "novelty_llm_models"))},
            "prompt_evolution": evolution["evolve_prompts"]}


def check_embedding_endpoint(engine: dict, *, seed_only=False) -> dict:
    """Check a local listener without sending text or making an embedding call."""
    route = native_settings(engine, seed_only=seed_only)[0]["embedding_model"]
    if not route:
        return {"required": False, "model_calls": 0}
    host, port = embedding_endpoint(route)
    try:
        with socket.create_connection((host, port), timeout=3):
            pass
    except OSError as exc:
        raise RuntimeError(f"Requested local embedding endpoint is unavailable at {host}:{port}. Start the named local embedding server; native novelty will not be disabled or routed to a paid provider.") from exc
    return {"required": True, "route": route, "listener_reachable": True,
            "embedding_function_verified": False, "model_calls": 0,
            "note": "TCP listener only; actual embedding and novelty coverage are recorded during execution."}
