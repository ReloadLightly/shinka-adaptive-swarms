"""Fresh-task adaptation of the pinned native search, memory and prompt lifecycle.

Only operational helpers are reused from v1. This module never opens its
population, prompts, rewards, case cache or manifest. Some telemetry filenames
retain ``phase-b`` for compatibility with the existing read-only inspector;
their payloads and the bandit pickle carry this campaign's independent identity.
The controller must hold its campaign OS lock before constructing a runner.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import os
from pathlib import Path
import pickle
import random
import sqlite3
import subprocess
import time
import urllib.request

import numpy as np

from cooperative.native import atomic_json, event, make_runner_class as persistent_runner
from cooperative.native_memory import make_memory_runner_class
from cooperative.native_search import (
    DATABASE_SETTINGS, _atomic_json, _atomic_pickle, _bandit_state, _event,
    install_phase_b_hooks, make_search_runner_class,
)

CAMPAIGN_ID = "paper_trajectory_v2"
PRIMARY_ROUTE = "headless/codex@gpt-6-astra?effort=xhigh"
SECOND_ROUTE = "headless/codex@gpt-5.6-sol?effort=xhigh"
EMBEDDING_IDENTITY = {
    "model": "jina-code-v2-q8", "revision": "516f4baf13dec4ddddda8631e019b5737c8bc250",
    "dimensions": 768, "provider": "CPUExecutionProvider",
    "server_source_sha256": "f154b14398398b518805af9cb3a199141a89ddef5089c3463f4fe53b2710e78e",
    "model_manifest_sha256": "22e488956c5f7809cb4ec795d2a30cfb3611dbcae55b5a2694c25a2a8a4308d1",
    "network_model_calls": False,
}
SEARCH_INSTRUCTIONS = """Use the measured native parent, archive inspirations, local feedback and
available meta recommendations to propose substantive, interpretable policy
changes. Explore bounded link addition, deletion, rewiring, partner selection
and consent rules within the immutable all-actor policy interface. Compare
formation, shock response and terminal population utility, including unequal
or adverse effects. Treat measured development selection as exploratory; do
not claim generalization or mutual benefit. Preserve every immutable scientific
constraint. This evolvable text controls search strategy only.
"""


def configuration(primary_route=PRIMARY_ROUTE, second_route=SECOND_ROUTE):
    """Full native settings from initialization, without reading a prior task."""
    if primary_route == second_route:
        raise ValueError("Two genuinely distinct subscription arms are required")
    evolution = dict(
        language="java", llm_models=[primary_route, second_route],
        llm_dynamic_selection="ucb", llm_dynamic_selection_kwargs={"cost_aware_coef": 0.0},
        llm_kwargs={"temperatures": [0.0], "max_tokens": 16384},
        patch_types=["diff", "full", "cross"], patch_type_probs=[0.5, 0.3, 0.2],
        max_patch_resamples=3, max_patch_attempts=3, max_novelty_attempts=3,
        embedding_model="local/jina-code-v2-q8@http://127.0.0.1:8910/v1",
        novelty_llm_models=[primary_route], novelty_llm_kwargs={"temperatures": [0.0], "max_tokens": 4096},
        code_embed_sim_threshold=0.99, meta_rec_interval=10, meta_llm_models=[primary_route],
        meta_llm_kwargs={"temperatures": [0.0], "max_tokens": 8192},
        meta_max_recommendations=5, sample_single_meta_rec=True,
        evolve_prompts=True, prompt_evolution_interval=10, prompt_archive_size=10,
        prompt_llm_models=[primary_route], prompt_llm_kwargs={"temperatures": [0.0], "max_tokens": 8192},
        prompt_patch_types=["diff", "full"], prompt_patch_type_probs=[0.5, 0.5],
        prompt_ucb_exploration_constant=1.0, prompt_epsilon=0.1,
        prompt_evo_top_k_programs=3, prompt_percentile_recompute_interval=20,
        use_text_feedback=True, enable_wandb_logging=False,
        proposal_buffer_max=0, proposal_target_hard_cap=1, enable_controlled_oversubscription=False,
    )
    database = dict(DATABASE_SETTINGS, archive_selection_strategy="fitness")
    return {"evolution": evolution, "database": database,
            "max_evaluation_jobs": 1, "max_proposal_jobs": 1, "max_db_workers": 1,
            "search_prompt_sha256": hashlib.sha256(SEARCH_INSTRUCTIONS.encode()).hexdigest()}


def configuration_hash(settings):
    return hashlib.sha256(json.dumps(settings, sort_keys=True, allow_nan=False).encode()).hexdigest()


def subscription_preflight():
    """Free local readiness checks; call only after the scientific gate passes.

    This performs no route/model/quota probe, installs nothing, changes no
    credentials and starts no service. One local embedding is explicitly an
    operational probe. The caller owns persistence of the returned receipt.
    """
    child = os.environ.copy()
    for key in list(child):
        upper = key.upper()
        if upper.endswith(("API_KEY", "API_TOKEN")) or upper in {
                "AZURE_OPENAI_AD_TOKEN", "GOOGLE_APPLICATION_CREDENTIALS", "AWS_ACCESS_KEY_ID",
                "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "OPENAI_BASE_URL", "OPENAI_API_BASE",
                "ANTHROPIC_BASE_URL", "CODEX_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN"}:
            child.pop(key, None)
    child.update(npm_config_offline="true", NPM_CONFIG_OFFLINE="true",
                 npm_config_update_notifier="false", npm_config_audit="false", npm_config_fund="false",
                 SHINKA_PRICING_MODE="offline", SHINKA_HEADLESS_COMMAND="npx -y @roberttlange/headless@0.6.1")
    root = Path(__file__).resolve().parents[1]
    auth = subprocess.run(["codex", "login", "status"], env=child, cwd=root,
                          capture_output=True, text=True, timeout=15)
    if auth.returncode != 0 or "chatgpt" not in (auth.stdout + auth.stderr).lower():
        raise RuntimeError("ChatGPT subscription authentication is unavailable; no inference fallback is permitted")
    bridge = subprocess.run(["npx", "-y", "@roberttlange/headless@0.6.1", "--check"],
                            env=child, cwd=root, capture_output=True, text=True, timeout=60)
    if bridge.returncode != 0:
        raise RuntimeError("Pinned Headless0.6.1 offline availability check failed; no install, model probe or fallback attempted")
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            raise RuntimeError("Local embedding preflight refused an HTTP redirect")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open("http://127.0.0.1:8910/health", timeout=5) as response:
        health = json.load(response)
    if health.get("status") != "ready" or any(health.get(key) != value for key, value in EMBEDDING_IDENTITY.items()):
        raise RuntimeError("Frozen local embedding health/identity mismatch; no model call or paid fallback allowed")
    probe = "// paper_trajectory_v2 operational embedding readiness probe\npublic final class EmbeddingPreflight {}\n"
    request = urllib.request.Request("http://127.0.0.1:8910/v1/embeddings",
        data=json.dumps({"model": EMBEDDING_IDENTITY["model"], "input": probe}).encode(),
        headers={"Content-Type": "application/json"})
    with opener.open(request, timeout=60) as response:
        payload = json.load(response)
    rows = payload.get("data", [])
    vector = rows[0].get("embedding", []) if len(rows) == 1 else []
    if (payload.get("model") != EMBEDDING_IDENTITY["model"] or len(vector) != 768
            or not all(type(value) in (int, float) and math.isfinite(value) for value in vector)
            or not any(value != 0 for value in vector)):
        raise RuntimeError("Local embedding operational probe returned an invalid vector; discovery remains paused")
    return {"schema": "paper-subscription-preflight-v1", "chatgpt_authenticated": True,
        "headless_package": "@roberttlange/headless@0.6.1", "headless_check_passed": True,
        "npm_offline": True, "model_routes": [PRIMARY_ROUTE, SECOND_ROUTE],
        "model_route_probes": 0, "logical_model_responses": 0, "paid_api_authorized": False,
        "quota_availability_tested": False, "global_environment_changed": False,
        "embedding_health": health,
        "operational_local_embedding_probe": {"count": 1, "dimensions": len(vector),
            "input_sha256": hashlib.sha256(probe.encode()).hexdigest(),
            "vector_sha256": configuration_hash(vector), "finite_nonzero": True},
        "scope": "Free authentication/bridge checks and one local embedding; prior route evidence is retained, no new model/provider attestation is claimed."}


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _config_record(config, excluded=()):
    values = dataclasses.asdict(config)
    return {key: value for key, value in values.items() if key not in excluded}


def _local_job_identity(config):
    """Freeze executable evaluator bytes while excluding host-specific locations.

    The scientific contract binds its imports and data. Interpreter location is
    operational; all timeout, threading and extra arguments remain exact. An
    activation script, if configured, is also bound by bytes rather than path.
    """
    record = _config_record(config)
    evaluator = Path(config.eval_program_path).resolve()
    if not evaluator.is_file():
        raise RuntimeError("Declared local evaluator source is missing")
    evaluator_identity = _hash(evaluator)
    repository = Path(__file__).resolve().parents[1]
    relative = 'paper_trajectory_v2/evaluate.py'
    if evaluator == repository / relative:
        # Preserve the scientific identity only after checking the exact recorded
        # operational replacement; its executed bytes are bound separately.
        from scripts.paper_operational_compatibility import ORIGINAL, resolved_digest
        resolved_digest(relative, ORIGINAL[relative], lambda name: (repository / name).read_bytes())
        evaluator_identity = ORIGINAL[relative]
    record.update(eval_program_path="<local-evaluator>", eval_program_sha256=evaluator_identity,
                  python_executable="<local-python-interpreter>")
    if record.get("activate_script"):
        script = Path(record["activate_script"]).resolve()
        if not script.is_file():
            raise RuntimeError("Declared local activation script is missing")
        record.update(activate_script="<local-activation-script>", activate_script_sha256=_hash(script))
    return record


def make_runner_class(search, *, campaign_id=CAMPAIGN_ID, scientific_identity,
                      immutable_prompt_path, search_prompt_path, max_descendant_proposals=50,
                      recovery_id=None, recovery_lock_fd=None, recovery_repository=None):
    """Compose native mechanisms under an isolated, fail-closed task identity.

    One explicitly evaluated seed is initialization. Generations 1..50 are the
    descendant proposal slots; resamples/patch/novelty attempts retain their
    native limits and independent receipts. Native administrative island copies
    never create an additional generation, reward or prompt/meta observation.
    """
    if campaign_id != CAMPAIGN_ID or max_descendant_proposals != 50:
        raise ValueError("This frozen campaign requires its own identity and 50 descendant slots")
    root = Path(search).resolve()
    immutable = Path(immutable_prompt_path).resolve()
    guidance = Path(search_prompt_path).resolve()
    target = max_descendant_proposals + 1
    install_phase_b_hooks(root)
    composed = make_memory_runner_class(make_search_runner_class(persistent_runner()),
        immutable_prompt_path=immutable, search_prompt_path=guidance,
        phase_start_generation=0, bootstrap_program_ids=(), overall_target_slots=target)

    class PaperTrajectoryRunner(composed):
        def __init__(self, *args, **kwargs):
            if (root / "infrastructure-pause.json").exists():
                raise RuntimeError("Unresolved evaluation/infrastructure pause; no automatic native recovery")
            if (root / "recovery-pending.json").exists() or recovery_id is not None:
                if recovery_id is None:raise RuntimeError("Recovery pending; ordinary native admission is blocked")
                from paper_trajectory_v2.recovery import permit
                permit(recovery_repository,root,recovery_id,recovery_lock_fd,target=kwargs['evo_config'].num_generations)
            if args:
                raise TypeError("Use explicit native configuration keyword arguments")
            evo, db = kwargs["evo_config"], kwargs["db_config"]
            # Avoid native CPU-count-dependent defaults changing the persisted
            # job identity when a checkout moves to another machine.
            job = kwargs["job_config"]
            if hasattr(job, "numeric_threads_per_job") and job.numeric_threads_per_job is None:
                job.numeric_threads_per_job = 1
            if Path(evo.results_dir).resolve() != root:
                raise RuntimeError("Runner results directory differs from campaign identity")
            if not 1 <= evo.num_generations <= target:
                raise RuntimeError("Requested native target exceeds the 50-descendant ceiling")
            if (Path(evo.init_program_path).resolve() != root / "frozen/CandidatePolicy.java"
                    or evo.task_sys_msg != immutable.read_text()):
                raise RuntimeError("Native executed seed/prompt differs from declared frozen copies")
            expected = json.loads((root / "seed-verification/metrics.json").read_text())
            correct = json.loads((root / "seed-verification/correct.json").read_text())
            if correct.get("correct") is not True or expected.get("combined_score") != 0.0:
                raise RuntimeError("The independently verified initialization reference must score zero")
            self._paper_identity = {
                "schema_version": 2, "campaign_id": campaign_id,
                "scientific_identity": scientific_identity,
                "initialization_programs": 1, "max_descendant_proposals": max_descendant_proposals,
                "immutable_prompt_sha256": _hash(immutable), "search_prompt_sha256": _hash(guidance),
                "seed_sha256": _hash(evo.init_program_path),
                "evolution": _config_record(evo, {"num_generations", "results_dir", "init_program_path"}),
                "database": _config_record(db, {"db_path"}),
                "job": _local_job_identity(kwargs["job_config"]),
            }
            self._paper_identity_sha256 = configuration_hash(self._paper_identity)
            identity_path = root / "native-task-identity.json"
            if identity_path.exists():
                if json.loads(identity_path.read_text()) != self._paper_identity:
                    raise RuntimeError("Native task identity/configuration changed; refusing state import or reset")
            else:
                existing = [name for name in ("programs.sqlite", "bandit_state.pkl", "prompts.sqlite", "native_memory/state.json")
                            if (root / name).exists()]
                if existing:
                    raise RuntimeError("Existing native state lacks this task identity: " + ", ".join(existing))
                atomic_json(identity_path, self._paper_identity)
            self._check_saved_state_identity()
            super().__init__(**kwargs)

        def _verify_evaluator_source(self):
            if (root / "recovery-pending.json").exists():
                if recovery_id is None:raise RuntimeError("Recovery pending; ordinary admission blocked")
                from paper_trajectory_v2.recovery import permit
                permit(recovery_repository,root,recovery_id,recovery_lock_fd)
            if (root / "infrastructure-pause.json").exists():
                raise RuntimeError("Unresolved infrastructure interruption; no new proposal or automatic recovery")
            # Use the actual scheduler configuration at submission, so relocating
            # a checkout is allowed but changing the executed evaluator is not.
            scheduler_job = getattr(getattr(self, "scheduler", None), "config", self.job_config)
            for job in (self.job_config, scheduler_job):
                if _local_job_identity(job) != self._paper_identity["job"]:
                    raise RuntimeError("Actual local evaluator bytes/configuration differ from the frozen native identity")

        async def _setup_initial_program(self, code):
            self._verify_evaluator_source()
            original_add = self.async_db.add_program_async
            async def guarded_add(program, *args, **kwargs):
                if (self._evaluation_interrupted(root / "gen_0/results", 0)
                    or (program.metadata or {}).get("evaluation_failed") or not program.correct
                    or program.combined_score != 0.0):
                    self.should_stop.set()
                    raise RuntimeError("Initialization evaluation was interrupted or disagrees with its independently verified zero score")
                return await original_add(program, *args, **kwargs)
            self.async_db.add_program_async = guarded_add
            try:
                return await super()._setup_initial_program(code)
            finally:
                self.async_db.add_program_async = original_add

        def _evaluation_interrupted(self, results, generation):
            results = Path(results)
            marker = results / "evaluation-interrupted.json"
            if marker.exists():
                return True
            # A killed evaluator cannot write its own interruption receipt.
            # Missing/corrupt outputs therefore require inspection, never fitness.
            try:
                metrics = json.loads((results / "metrics.json").read_text())
                correct = json.loads((results / "correct.json").read_text())
                complete = (isinstance(correct.get("correct"), bool)
                            and type(metrics.get("combined_score")) in (int, float)
                            and math.isfinite(metrics["combined_score"]))
            except (OSError, ValueError, TypeError, AttributeError):
                complete = False
            if complete:
                return False
            receipt = {"time": time.time(), "reason": "Accepted evaluation has missing or corrupt terminal outputs; preserve and reconcile before recovery",
                       "failure_classification": "infrastructure_interruption", "generation": generation,
                       "results_dir": str(results), "accepted_job_path": str(results.parent / "accepted-job.json"),
                       "candidate_path": str(results.parent / "main.java"), "automatic_retry": False, "fitness_recorded": False}
            atomic_json(marker, receipt)
            if not (root / "infrastructure-pause.json").exists():
                atomic_json(root / "infrastructure-pause.json", receipt)
            return True

        async def _submit_evaluation_job_with_slot(self, *args, **kwargs):
            self._verify_evaluator_source()
            if (root / "infrastructure-pause.json").exists():
                raise RuntimeError("Infrastructure interruption requires explicit source/lineage reconciliation before submission")
            if recovery_id is not None:
                from paper_trajectory_v2.recovery import permit
                permit(recovery_repository,root,recovery_id,recovery_lock_fd,
                       program=args[0] if args else kwargs.get('exec_fname'),
                       results=args[1] if len(args)>1 else kwargs.get('results_dir'))
            return await super()._submit_evaluation_job_with_slot(*args, **kwargs)

        async def _process_single_job_safely(self, job):
            interrupted = Path(job.results_dir) / "evaluation-interrupted.json"
            if self._evaluation_interrupted(job.results_dir, job.generation):
                # Keep accepted-job.json, source and exact-case receipts untouched.
                # Missing metrics must not become native invalid fitness/reward.
                self.should_stop.set()
                event(root, "paper_evaluation_ingestion_paused", generation=job.generation,
                      job_id=str(job.job_id), interruption_path=str(interrupted),
                      automatic_retry=False, fitness_recorded=False)
                # The pinned monitor normally signals finalization only after
                # reaching its generation target. A paused accepted slot has no
                # terminal fitness, so explicitly finalize a drained boundary.
                if not self.running_jobs and not self.active_proposal_tasks:
                    self.slot_available.set()
                    self.finalization_complete.set()
                return False
            return await super()._process_single_job_safely(job)

        def _check_saved_state_identity(self):
            memory = root / "native_memory/state.json"
            if memory.exists():
                payload = json.loads(memory.read_text())
                if payload.get("campaign_identity_sha256") != self._paper_identity_sha256:
                    raise RuntimeError("Native meta/prompt state belongs to another task or lacks provenance")
            path = root / "bandit_state.pkl"
            if path.exists():
                with path.open("rb") as stream:
                    state = pickle.load(stream)
                if state.get("campaign_extension", {}).get("identity_sha256") != self._paper_identity_sha256:
                    raise RuntimeError("Native UCB state belongs to another task or lacks provenance")

        def _save_bandit_state(self):
            state = _bandit_state(self.llm_selection, getattr(self, "_phase_b_rewarded_ids", ()))
            extension = state.pop("phase_b_extension")
            extension.update(campaign_id=campaign_id, identity_sha256=self._paper_identity_sha256)
            state["campaign_extension"] = extension
            _atomic_pickle(root / "bandit_state.pkl", state)
            _atomic_json(root / "phase-b-bandit-summary.json", {
                "campaign_id": campaign_id, "campaign_identity_sha256": self._paper_identity_sha256,
                "native_state": self.llm_selection.get_state(),
                "rewarded_program_ids": sorted(getattr(self, "_phase_b_rewarded_ids", ())),
                "monetary_cost_weight": self.llm_selection.cost_aware_coefficient,
                "legacy_filename_only": True, "rng_limitation": extension["rng_limitation"]})

        def _load_bandit_state(self):
            with (root / "bandit_state.pkl").open("rb") as stream:
                state = pickle.load(stream)
            extension = state.get("campaign_extension", {})
            if (extension.get("identity_sha256") != self._paper_identity_sha256
                    or extension.get("sampler_class") != "AsymmetricUCB"
                    or state.get("arm_names") != self.llm_selection._arm_names):
                raise RuntimeError("Saved UCB state differs from this campaign identity or native arms")
            self.llm_selection.set_state(state)
            random.setstate(extension["python_random_state"])
            np.random.set_state(extension["numpy_random_state"])
            self.llm_selection.rng.bit_generator.state = extension["bandit_rng_state"]
            self._phase_b_rewarded_ids = set(extension["rewarded_program_ids"])
            _event(root, "native_ucb_state_restored", campaign_id=campaign_id,
                   arm_names=state["arm_names"], n_completed=self.llm_selection.n_completed,
                   rewarded_program_ids=sorted(self._phase_b_rewarded_ids))

        def _save_native_memory(self):
            super()._save_native_memory()
            if getattr(self, "_native_memory_ready", False):
                payload = json.loads(self._memory_path.read_text())
                payload.update(campaign_id=campaign_id, campaign_identity_sha256=self._paper_identity_sha256)
                atomic_json(self._memory_path, payload)

        async def _setup_async(self):
            if (root / "infrastructure-pause.json").exists() or any(root.glob("gen_*/results/evaluation-interrupted.json")):
                raise RuntimeError("Interrupted evaluation evidence requires explicit reconciliation; no automatic recovery or new proposal")
            # The reused helper's prepared-only replay is not guaranteed by the
            # native directory lock. Fail closed before it can silently re-propose.
            persisted = set()
            if (root / "programs.sqlite").exists():
                connection = sqlite3.connect((root / "programs.sqlite").as_uri() + "?mode=ro", uri=True)
                try:
                    persisted = {row[0] for row in connection.execute("SELECT DISTINCT generation FROM programs")}
                finally:
                    connection.close()
            for folder in root.glob("gen_*"):
                generation = int(folder.name[4:])
                if generation and generation not in persisted and not (folder / "failure.json").exists() and not (folder / "accepted-job.json").exists():
                    raise RuntimeError(f"Interrupted unaccepted generation {generation}; preserve and reconcile its source/receipts before resume")
            await super()._setup_async()
            originals = [p for p in self.db.get_all_programs() if not (p.metadata or {}).get("administrative_copy")]
            if any(p.generation < 0 or p.generation >= target for p in originals):
                raise RuntimeError("Population contains a generation outside this campaign's fixed budget")
            self._save_bandit_state()
            event(root, "paper_task_state_verified", campaign_id=campaign_id,
                  identity_sha256=self._paper_identity_sha256, original_programs=len(originals),
                  administrative_copies=len(self.db.get_all_programs()) - len(originals))

        async def _generate_proposal_async(self, generation, task_id):
            if recovery_id is not None:raise RuntimeError("Recovery may not generate any proposal")
            if not 1 <= generation <= max_descendant_proposals:
                raise RuntimeError("Descendant generation outside the fixed 50-proposal budget")
            self._verify_evaluator_source()
            return await super()._generate_proposal_async(generation, task_id)

    return PaperTrajectoryRunner
