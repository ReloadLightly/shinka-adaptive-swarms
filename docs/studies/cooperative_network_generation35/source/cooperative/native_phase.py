"""Explicit search-only Phase B settings; the scientific Phase A freeze stays intact."""
from __future__ import annotations

import copy
import hashlib
import json

SECOND_ROUTE = "headless/codex@gpt-5.6-sol?effort=xhigh"
PHASE_B_SEARCH_PROMPT = """Search for effective, simple local exploration policies using the native parent,
archive inspirations, evaluation feedback and available recommendations. Compare
the measured strengths and failure modes of candidate rules, and propose a
substantive, testable modification. Treat all immutable scientific instructions
as binding. This evolvable text controls search strategy only. It cannot change
the experiment, evaluator, objective, cases, permitted information, policy API or
code outside the allowed evolution block. The historical embedding wording in
the immutable prompt is an acknowledged erratum: novelty uses the frozen local
embedding service, never a paid embedding API.
"""


def configuration(phase_a_evolution, phase_a_database, primary_route):
    evolution, database = copy.deepcopy(phase_a_evolution), copy.deepcopy(phase_a_database)
    evolution.update(
        llm_models=[primary_route, SECOND_ROUTE], llm_dynamic_selection="ucb",
        llm_dynamic_selection_kwargs={"cost_aware_coef": 0.0},
        max_patch_resamples=3, max_patch_attempts=3, max_novelty_attempts=3,
        meta_rec_interval=10, meta_llm_models=[primary_route],
        meta_llm_kwargs={"temperatures": [0.0], "max_tokens": 8192},
        meta_max_recommendations=5, sample_single_meta_rec=True,
        evolve_prompts=True, prompt_evolution_interval=10,
        prompt_archive_size=10, prompt_llm_models=[primary_route],
        prompt_llm_kwargs={"temperatures": [0.0], "max_tokens": 8192},
        prompt_patch_types=["diff", "full"], prompt_patch_type_probs=[0.5, 0.5],
        prompt_ucb_exploration_constant=1.0, prompt_epsilon=0.1,
        prompt_evo_top_k_programs=3, prompt_percentile_recompute_interval=20)
    database.update(
        num_islands=3, archive_size=64, archive_selection_strategy="fitness",
        island_selection_strategy="uniform", migration_interval=10,
        migration_rate=0.1, island_elitism=True, enforce_island_separation=True,
        enable_dynamic_islands=True, stagnation_threshold=20,
        island_spawn_strategy="archive_random", island_spawn_subtree_size=1)
    return {"evolution": evolution, "database": database,
            "search_prompt_sha256": hashlib.sha256(PHASE_B_SEARCH_PROMPT.encode()).hexdigest(),
            "max_evaluation_jobs": 1, "max_proposal_jobs": 1, "max_db_workers": 1}


def configuration_hash(settings):
    return hashlib.sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest()
