"""Persistence/observability around pinned native Shinka, not a search algorithm."""
from __future__ import annotations

import asyncio
import dataclasses
import contextvars
import hashlib
import json
import math
import os
from pathlib import Path
import time
import uuid

ROUTE = "headless/codex@gpt-6-astra?effort=xhigh"
REQUEST_ROLE = contextvars.ContextVar("request_role", default="mutation")


def atomic_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n")
    temporary.replace(path)


def event(root, kind, **data):
    with (root / "controller-events.jsonl").open("a") as stream:
        stream.write(json.dumps({"time": time.time(), "event": kind, **data}, allow_nan=False) + "\n")


def sanitize_environment():
    """Process-only defense; never print values or alter global credentials."""
    removed = []
    for key in list(os.environ):
        upper = key.upper()
        if (upper.endswith("API_KEY") or upper.endswith("API_TOKEN") or upper in {
            "AZURE_OPENAI_AD_TOKEN", "GOOGLE_APPLICATION_CREDENTIALS", "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "OPENAI_BASE_URL", "OPENAI_API_BASE",
            "ANTHROPIC_BASE_URL", "CODEX_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN"}):
            removed.append(key)
            os.environ.pop(key, None)
    os.environ.update(SHINKA_HEADLESS_COMMAND="npx -y @roberttlange/headless@0.6.1",
                      SHINKA_PRICING_MODE="offline", PYTHONUNBUFFERED="1", PYTHONDONTWRITEBYTECODE="1",
                      MPLCONFIGDIR=str(Path(os.environ.get("TMPDIR", "/tmp")) / "cooperation-matplotlib"))
    return sorted(removed)


def terminal_failures(root):
    found = set()
    for path in root.glob("gen_*/failure.json"):
        data = json.loads(path.read_text())
        generation = int(path.parent.name[4:])
        if data.get("generation") != generation:
            raise RuntimeError(f"Failure identity mismatch: {path}")
        if data.get("node_kind") == "failed_proposal" and data.get("downstream_eval_submitted") is False:
            found.add(generation)
    return found


def install_usage_observer(root, allowed_routes=None, phase=None):
    """Observe every exposed native provider attempt, including native retries."""
    import shinka.llm.llm as llm_module
    from shinka.llm.providers.errors import NonRetryableLLMError
    original = llm_module.query_async
    llm_module.MAX_RETRIES = 2
    attempts = {}
    from shinka.llm.providers import headless
    routes = frozenset((ROUTE,) if allowed_routes is None else allowed_routes)
    if not routes:
        raise ValueError("At least one explicit subscription route is required")
    parsed_routes = {route: headless.parse_headless_model(route) for route in routes}
    if any(model.agent != "codex" or not model.agent_model for model in parsed_routes.values()):
        raise ValueError("Only explicit ChatGPT-authenticated Codex model routes are authorized")
    receipt_context = contextvars.ContextVar("usage_receipt_id", default=None)

    def role_fields():
        value = REQUEST_ROLE.get()
        role, subrole = value if isinstance(value, tuple) else (value, None)
        return {"role": role, "subrole": subrole, "phase": phase}

    original_command = headless._build_headless_command
    def command_with_receipt(**kwargs):
        command = original_command(**kwargs)
        model = kwargs["model"]
        route = "headless/" + model.agent + "@" + model.agent_model
        if model.effort:
            route += "?effort=" + model.effort
        atomic_json(root / "dispatches" / (uuid.uuid4().hex + ".json"), {
            "time": time.time(), **role_fields(), "command": command,
            "route": route, "model_requested": model.agent_model, "effort_requested": model.effort,
            "usage_receipt_id": receipt_context.get(),
            "evidence": "Actual Headless subprocess command built by pinned native provider; not independent provider-side model attestation"})
        return command
    headless._build_headless_command = command_with_receipt

    async def observed(**kwargs):
        route = kwargs.get("model_name")
        if route not in routes:
            raise NonRetryableLLMError("Only the explicitly authorized ChatGPT subscription routes may be called")
        if (root / "subscription-pause.json").exists():
            raise NonRetryableLLMError("Subscription capacity pause is active; no retry submitted")
        key = hashlib.sha256(json.dumps(kwargs, sort_keys=True, default=str).encode()).hexdigest()
        attempts[key] = attempts.get(key, 0) + 1
        attempt = attempts[key]
        receipt_id = uuid.uuid4().hex
        path = root / "usage" / (receipt_id + ".json")
        model = parsed_routes[route]
        record = {"id": receipt_id, **role_fields(), "attempt": attempt,
                  "is_retry": attempt > 1, "status": "started", "started_at": time.time(),
                  "route": route, "model_requested": model.agent_model,
                  "effort_requested": model.effort, "paid_api_authorized": False,
                  "scope": "exposed Shinka provider calls; bridge/provider internal retries unobservable",
                  "request_identity": key, "prompt": kwargs.get("msg"), "system_prompt": kwargs.get("system_msg")}
        atomic_json(path, record)
        started = time.monotonic()
        receipt_token = receipt_context.set(receipt_id)
        try:
            sanitize_environment()
            response = await original(**kwargs)
        except Exception as exc:
            message = str(exc)
            quota = any(word in message.lower() for word in ("usage limit", "usage_limit", "quota", "rate limit", "rate_limit", "too many requests", "subscription limit", "credits", "capacity"))
            record.update(status="capacity_paused" if quota else "failed", error=message,
                          elapsed_seconds=time.monotonic() - started, finished_at=time.time())
            atomic_json(path, record)
            if quota:
                atomic_json(root / "subscription-pause.json", {"time": time.time(), "receipt": str(path.relative_to(root)), "reason": message})
                raise NonRetryableLLMError("Subscription capacity unavailable; checkpoint and pause") from exc
            raise
        finally:
            receipt_context.reset(receipt_token)
        record.update(status="returned", elapsed_seconds=time.monotonic() - started,
                      finished_at=time.time(), response=response.to_dict())
        atomic_json(path, record)
        return response

    llm_module.query_async = observed



def install_role_context(client, role, subrole=None):
    if client is None:
        return
    for name in ("query", "batch_kwargs_query"):
        original = getattr(client, name)
        def wrap(method, method_name):
            async def contextual(*args, **kwargs):
                token = REQUEST_ROLE.set((role, subrole or method_name))
                try:
                    return await method(*args, **kwargs)
                finally:
                    REQUEST_ROLE.reset(token)
            return contextual
        setattr(client, name, wrap(original, name))


def make_runner_class():
    from shinka.core import ShinkaEvolveRunner
    from shinka.core.async_runner import AsyncRunningJob

    class PersistentRunner(ShinkaEvolveRunner):
        async def _get_code_embedding_async(self, exec_fname):
            result = await super()._get_code_embedding_async(exec_fname)
            if self.evo_config.embedding_model:
                vector, cost = result
                if not vector or len(vector) != 768 or not all(math.isfinite(x) for x in vector) or cost != 0:
                    atomic_json(Path(self.results_dir) / "infrastructure-pause.json", {
                        "time": time.time(), "reason": "Frozen local embedding returned invalid vector or nonzero native cost"})
                    raise RuntimeError("Local embedding failed; no silent novelty disable or paid fallback")
            return result

        async def _setup_initial_program(self, code):
            # Upstream's resume predicate excludes last_iteration == 0.
            if await self.async_db.get_total_program_count_async() > 0:
                self._load_bandit_state()
                await self._restore_resume_progress()
                event(Path(self.results_dir), "seed_reused")
                return
            await super()._setup_initial_program(code)

        async def _setup_async(self):
            await super()._setup_async()
            root = Path(self.results_dir)
            # Reject upstream's exception fallback that labels a zero-score seed correct.
            seeds = [p for p in self.db.get_all_programs() if p.generation == 0
                     and not (p.metadata or {}).get("administrative_copy")]
            if len(seeds) != 1:
                raise RuntimeError("Campaign requires exactly one native seed identity")
            seed = seeds[0]
            expected = json.loads((root / "seed-verification" / "metrics.json").read_text())
            correct = json.loads((root / "seed-verification" / "correct.json").read_text())
            if (correct.get("correct") is not True or not seed.correct or
                (seed.metadata or {}).get("evaluation_failed") or
                not math.isclose(seed.combined_score, expected["combined_score"], rel_tol=0, abs_tol=1e-12) or
                seed.code != (root / "frozen" / "CandidatePolicy.java").read_text()):
                raise RuntimeError("Native seed disagrees with independently verified evaluation")
            event(root, "seed_verified", seed_id=seed.id, score=seed.combined_score)
            self._resume_patches = {}
            persisted = set(await self.async_db.get_persisted_generation_ids_async())
            failures = terminal_failures(root)
            self.next_generation_to_submit = max(persisted | failures | {0}) + 1
            for folder in sorted(root.glob("gen_*"), key=lambda p: int(p.name[4:])):
                generation = int(folder.name[4:])
                if generation in persisted | failures or generation >= self.evo_config.num_generations:
                    continue
                pending_path = folder / "accepted-job.json"
                if not pending_path.exists():
                    patch_path = folder / "prepared-patch.json"
                    if patch_path.exists():
                        record = json.loads(patch_path.read_text())
                        if hashlib.sha256((folder / "main.java").read_bytes()).hexdigest() != record["candidate_sha256"]:
                            raise RuntimeError("Prepared native patch changed before crash recovery")
                        self._resume_patches[generation] = record
                        self.next_generation_to_submit = min(self.next_generation_to_submit, generation)
                        event(root, "prepared_patch_recovered", generation=generation, parent_id=record["parent_id"])
                        continue
                    if (folder / "main.java").exists() and any(json.loads(p.read_text()).get("success") for p in folder.glob("attempts/**/metadata.json")):
                        raise RuntimeError(f"Generation {generation} has a successful patch without durable lineage; retained for explicit reconciliation")
                    # Preserve all interrupted proposal evidence before reassigning its slot.
                    preserved = root / "interrupted_proposals" / (folder.name + "-" + str(time.time_ns()))
                    preserved.parent.mkdir(exist_ok=True)
                    folder.rename(preserved)
                    self.next_generation_to_submit = min(self.next_generation_to_submit, generation)
                    event(root, "incomplete_proposal_preserved", generation=generation, path=str(preserved))
                    continue
                record = json.loads(pending_path.read_text())
                candidate = folder / "main.java"
                if hashlib.sha256(candidate.read_bytes()).hexdigest() != record.pop("candidate_sha256"):
                    raise RuntimeError("Accepted candidate source changed before resume")
                jid, wid, submitted, started, running = await self._submit_evaluation_job_with_slot(str(candidate), str(folder / "results"), None)
                record.update(job_id=jid, exec_fname=str(candidate), results_dir=str(folder / "results"),
                              evaluation_worker_id=wid, evaluation_submitted_at=submitted,
                              evaluation_started_at=started, running_eval_jobs_at_submit=running,
                              evaluation_slot_released=False, discard_if_completed=False,
                              start_time=started if started is not None else submitted, db_retry_count=0)
                fields = {field.name for field in dataclasses.fields(AsyncRunningJob)}
                job = AsyncRunningJob(**{k: v for k, v in record.items() if k in fields})
                self.running_jobs.append(job)
                self.submitted_jobs[str(jid)] = job
                self.next_generation_to_submit = max(self.next_generation_to_submit, generation + 1)
                event(root, "accepted_candidate_resumed", generation=generation, parent_id=job.parent_id)
            original = self.async_db.sample_with_fix_mode_async

            async def sampled(*args, **kwargs):
                generation = kwargs.get("target_generation")
                if generation in self._resume_patches:
                    record = self._resume_patches[generation]
                    parent = self.db.get(record["parent_id"])
                    archive = [self.db.get(pid) for pid in record["archive_ids"]]
                    top = [self.db.get(pid) for pid in record["top_ids"]]
                    if parent is None or any(p is None for p in archive + top):
                        raise RuntimeError("Recovered patch lineage absent from native population")
                    result = (parent, archive, top, False)
                else:
                    result = await original(*args, **kwargs)
                parent, archive, top, fix = result
                event(root, "native_sampling", generation=kwargs.get("target_generation"), parent_id=parent.id,
                      parent_generation=parent.generation, parent_island=parent.island_idx,
                      parent_is_administrative_copy=bool((parent.metadata or {}).get("administrative_copy")),
                      archive_ids=[p.id for p in archive], top_ids=[p.id for p in top], needs_fix=fix)
                return result

            self.async_db.sample_with_fix_mode_async = sampled

        async def _run_patch_async(self, parent_program, archive_programs, top_k_programs, generation, *args, **kwargs):
            saved = getattr(self, "_resume_patches", {}).pop(generation, None)
            if saved is not None:
                return tuple(saved["patch_result"])
            result = await super()._run_patch_async(parent_program, archive_programs, top_k_programs, generation, *args, **kwargs)
            if result and result[2]:
                candidate = Path(self.results_dir) / f"gen_{generation}" / "main.java"
                atomic_json(candidate.parent / "prepared-patch.json", {
                    "candidate_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
                    "parent_id": parent_program.id, "archive_ids": [p.id for p in archive_programs],
                    "top_ids": [p.id for p in top_k_programs], "patch_result": result})
            return result

        async def _generate_evolved_proposal(self, *args, **kwargs):
            job = await super()._generate_evolved_proposal(*args, **kwargs)
            if job is not None:
                # The pinned local scheduler times out against start_time, whereas
                # upstream initializes it before mutation/novelty. Fix this before
                # the outer proposal method yields during lock cleanup, when the
                # monitor can first inspect the registered job. Pipeline accounting
                # continues to use the unchanged proposal_started_at.
                job.start_time = (job.evaluation_started_at if job.evaluation_started_at is not None
                                  else job.evaluation_submitted_at)
            return job

        async def _generate_proposal_async(self, generation, task_id):
            job = await super()._generate_proposal_async(generation, task_id)
            if job is not None:
                record = {field.name: getattr(job, field.name) for field in dataclasses.fields(job) if field.name != "job_id"}
                record["candidate_sha256"] = hashlib.sha256(Path(job.exec_fname).read_bytes()).hexdigest()
                atomic_json(Path(job.exec_fname).parent / "accepted-job.json", record)
            return job

        async def _count_completed_generations_from_db(self):
            persisted = set(await self.async_db.get_persisted_generation_ids_async())
            return len((persisted | terminal_failures(Path(self.results_dir))) & set(range(self.evo_config.num_generations)))

        async def _get_missing_persisted_generations(self):
            persisted = set(await self.async_db.get_persisted_generation_ids_async())
            return sorted(set(range(self.evo_config.num_generations)) - persisted - terminal_failures(Path(self.results_dir)))

    return PersistentRunner
