"""Durability for pinned Shinka meta memory and native prompt coevolution.

Integration::

    Runner = make_memory_runner_class(
        make_runner_class(), immutable_prompt_path=search / "frozen/task_prompt.md",
        search_prompt_path=search / "phase_b/search_instructions.md",
        phase_start_generation=27, bootstrap_program_ids=phase_a_ids,
    )
    runner = Runner(evo_config=..., db_config=..., job_config=..., ...)

All selection, fitness, summarization and mutation use native Shinka objects.
``native_memory/state.json`` is an atomic native-meta-compatible payload with
additional lifecycle bookkeeping. Interrupted meta/prompt operations fail closed
rather than repeating uncertain model calls. The controller owns the OS lock.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
import time

from cooperative.native import REQUEST_ROLE, atomic_json, event, install_role_context


def _hash_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _prompt_signature(database):
    if database is None:
        return None
    records = sorted((p.to_dict() for p in database.get_all_prompts()), key=lambda p: p["id"])
    return _hash_bytes(json.dumps(records, sort_keys=True, allow_nan=False).encode())


def make_memory_runner_class(base_runner_class, *, immutable_prompt_path,
                             search_prompt_path, phase_start_generation,
                             bootstrap_program_ids=(), overall_target_slots=51):
    """Add restart-safe native memory to an existing persistent runner class.

    Bootstrap IDs must be measured programs strictly before the Phase-B boundary.
    Supplying no IDs disables bootstrap. The native meta interval counts newly
    evaluated programs; the native prompt interval counts prompt-attributed
    evaluated programs, including invalid evaluations, not rejected proposals.
    """
    immutable_path = Path(immutable_prompt_path)
    search_path = Path(search_prompt_path)
    bootstrap_ids = tuple(bootstrap_program_ids)
    if len(set(bootstrap_ids)) != len(bootstrap_ids):
        raise ValueError("Bootstrap program IDs must be unique")

    class NativeMemoryRunner(base_runner_class):
        def _initialize_native_memory(self):
            if getattr(self, "_native_memory_ready", False):
                return
            self._memory_directory = Path(self.results_dir) / "native_memory"
            self._memory_directory.mkdir(parents=True, exist_ok=True)
            self._memory_path = self._memory_directory / "state.json"
            # Native prompt and meta side effects use separate locks. One
            # lifecycle lock protects the shared receipt across their awaits.
            self._native_memory_lock = asyncio.Lock()
            identity = {
                "schema_version": 1,
                "phase_start_generation": phase_start_generation,
                "overall_target_slots": overall_target_slots,
                "immutable_prompt_sha256": _hash_bytes(immutable_path.read_bytes()),
                "initial_search_prompt_sha256": _hash_bytes(search_path.read_bytes()),
                "bootstrap_program_ids": list(bootstrap_ids),
                "meta_interval": self.evo_config.meta_rec_interval,
                "prompt_interval": self.evo_config.prompt_evolution_interval,
                "percentile_interval": self.evo_config.prompt_percentile_recompute_interval,
            }
            self._memory = {"identity": identity, "seen_meta_ids": [],
                            "fitness_program_ids": [], "evolution_program_ids": [],
                            "bootstrap": {"status": "pending" if bootstrap_ids else "disabled"},
                            "operation": None, "meta_updates": 0, "meta_api_cost": 0.0,
                            "recovery_meta_cost": 0.0}
            self._loaded_prompt_signature = None
            self._resume_percentile_pending = False
            if self._memory_path.exists():
                payload = json.loads(self._memory_path.read_text())
                saved = payload["_continuity"]
                if saved["identity"] != identity:
                    raise RuntimeError("Native-memory identity/configuration changed; reconcile before resuming")
                if saved.get("operation") or saved["bootstrap"]["status"] in {"started", "failed"}:
                    raise RuntimeError("Interrupted native memory operation requires explicit reconciliation; no automatic model replay")
                self._memory = saved
                if self.meta_summarizer is not None:
                    if not self.meta_summarizer.load_meta_state(str(self._memory_path)):
                        raise RuntimeError("Native meta-memory load failed")
                    restored = [p.id for p in self.meta_summarizer.evaluated_since_last_meta]
                    expected = [p["id"] for p in payload["unprocessed_programs"]]
                    if restored != expected:
                        raise RuntimeError("Native meta-memory load lost pending program identities")
                self.prompt_evolution_counter = saved["prompt_evolution_counter"]
                self.prompt_percentile_recompute_counter = saved["prompt_percentile_recompute_counter"]
                self.prompt_api_cost = saved["prompt_api_cost"]
                self._loaded_prompt_signature = saved.get("prompt_database_signature")
                self._resume_percentile_pending = saved.get("percentile_recompute_pending", False)
            elif (Path(self.results_dir) / "prompts.sqlite").exists():
                raise RuntimeError("Existing prompt database has no lifecycle state; refusing counter reset")
            self._native_memory_ready = True
            self._install_meta_memory_hooks()
            if getattr(self, "prompt_llm", None) is not None:
                install_role_context(self.prompt_llm, "prompt", "evolution")

        def _save_native_memory(self):
            if not getattr(self, "_native_memory_ready", False):
                return
            payload = {"unprocessed_programs": [], "meta_summary": None,
                       "meta_scratch_pad": None, "meta_recommendations": None,
                       "meta_recommendations_history": [], "total_programs_meta_processed": 0}
            if self.meta_summarizer is not None:
                native_path = self._memory_directory / "native-meta-export.json"
                native_path.unlink(missing_ok=True)
                self.meta_summarizer.save_meta_state(str(native_path))
                if not native_path.exists():
                    raise RuntimeError("Native meta-memory save failed")
                payload = json.loads(native_path.read_text())
                if [p["id"] for p in payload["unprocessed_programs"]] != [p.id for p in self.meta_summarizer.evaluated_since_last_meta]:
                    raise RuntimeError("Native meta-memory save lost pending program identities")
            task = getattr(self, "_prompt_percentile_recompute_task", None)
            self._memory.update(
                prompt_evolution_counter=self.prompt_evolution_counter,
                prompt_percentile_recompute_counter=self.prompt_percentile_recompute_counter,
                prompt_api_cost=self.prompt_api_cost,
                percentile_recompute_pending=bool(getattr(self, "_prompt_percentile_recompute_pending", False)
                                                 or (task is not None and not task.done())),
                prompt_database_signature=_prompt_signature(getattr(self, "prompt_db", None)),
                saved_at=time.time(),
            )
            atomic_json(self._memory_path, {**payload, "_continuity": self._memory})

        def _begin_memory_operation(self, kind, **details):
            if self._memory.get("operation") is not None:
                raise RuntimeError("Native memory operation still unresolved")
            self._memory["operation"] = {"kind": kind, "started_at": time.time(), **details}
            self._save_native_memory()

        def _finish_memory_operation(self):
            self._memory["operation"] = None
            self._save_native_memory()

        def _install_meta_memory_hooks(self):
            meta = self.meta_summarizer
            if meta is None:
                if bootstrap_ids:
                    raise RuntimeError("Meta bootstrap requested with native meta disabled")
                return
            from shinka.prompts import META_STEP1_SYSTEM_MSG, META_STEP2_SYSTEM_MSG, META_STEP3_SYSTEM_MSG
            stages = {META_STEP1_SYSTEM_MSG: "individual_summary", META_STEP2_SYSTEM_MSG: "scratchpad",
                      META_STEP3_SYSTEM_MSG: "recommendations"}
            for method_name in ("query", "batch_kwargs_query"):
                original_method = getattr(meta.async_llm_client, method_name)
                def contextual(method, fallback):
                    async def call(*args, **kwargs):
                        purpose = "bootstrap" if self._memory["bootstrap"]["status"] == "started" else "periodic"
                        stage = stages.get(kwargs.get("system_msg"), fallback)
                        token = REQUEST_ROLE.set(("meta", purpose + "." + stage))
                        try:
                            return await method(*args, **kwargs)
                        finally:
                            REQUEST_ROLE.reset(token)
                    return call
                setattr(meta.async_llm_client, method_name, contextual(original_method, method_name))
            # Native Step 1 filters absent responses before indexing identifiers.
            # Refuse partial batches to prevent mislabeled individual summaries.
            original_batch = meta.async_llm_client.batch_kwargs_query
            async def complete_batch(*args, **kwargs):
                responses = await original_batch(*args, **kwargs)
                if (not responses or len(responses) != kwargs["num_samples"]
                        or any(r is None or not r.content for r in responses)):
                    raise RuntimeError("Incomplete native meta-summary batch; preserve receipts and pause")
                return responses
            meta.async_llm_client.batch_kwargs_query = complete_batch
            original_add = meta.add_evaluated_program
            def add_once(program):
                if (program.metadata or {}).get("administrative_copy"):
                    return
                if program.id in self._memory["seen_meta_ids"]:
                    return
                original_add(program)
                self._memory["seen_meta_ids"].append(program.id)
                self._save_native_memory()
            meta.add_evaluated_program = add_once
            original_update = meta.update_meta_memory_async
            async def update(*args, **kwargs):
                async with self._native_memory_lock:
                    self._begin_memory_operation("meta_update", pending_ids=[p.id for p in meta.evaluated_since_last_meta])
                    result = await original_update(*args, **kwargs)
                    recommendations, cost = result
                    self._memory["meta_api_cost"] += cost or 0.0
                    if not recommendations:
                        self._save_native_memory()
                        raise RuntimeError("Native meta update did not complete; retained for reconciliation")
                    self._memory["meta_updates"] += 1
                    self._finish_memory_operation()
                    event(Path(self.results_dir), "native_meta_memory_updated",
                          total_programs_processed=meta.total_programs_processed,
                          update_count=self._memory["meta_updates"])
                    return result
            meta.update_meta_memory_async = update
            original_final = meta.perform_final_summary_async
            async def final_summary(*args, **kwargs):
                if self.completed_generations < overall_target_slots:
                    self._save_native_memory()
                    event(Path(self.results_dir), "native_meta_final_deferred", batch_target=self.evo_config.num_generations)
                    return False, 0.0
                return await original_final(*args, **kwargs)
            meta.perform_final_summary_async = final_summary

        async def _setup_prompt_evolution(self):
            """Use native components but test actual rows, not last_generation > 0."""
            from shinka.database.prompt_dbase import SystemPromptConfig, SystemPromptDatabase, create_system_prompt
            from shinka.core.prompt_evolver import SystemPromptSampler, AsyncSystemPromptEvolver
            config = SystemPromptConfig(db_path=str(Path(self.results_dir) / "prompts.sqlite"),
                archive_size=self.evo_config.prompt_archive_size,
                ucb_exploration_constant=self.evo_config.prompt_ucb_exploration_constant,
                epsilon=self.evo_config.prompt_epsilon)
            self.prompt_db = SystemPromptDatabase(config)
            if self.prompt_db._count_prompts_in_db() == 0:
                self.prompt_db.add(create_system_prompt(prompt_text=search_path.read_text(), generation=0,
                    patch_type="init", metadata={"source": "phase_b_search_instructions",
                    "immutable_prefix_sha256": self._memory["identity"]["immutable_prompt_sha256"]},
                    name="initial_search_instructions", description="Only these search instructions may coevolve."),
                    verbose=self.verbose)
            if self._loaded_prompt_signature is not None and _prompt_signature(self.prompt_db) != self._loaded_prompt_signature:
                raise RuntimeError("Native prompt database differs from saved lifecycle state")
            self.prompt_sampler_evo = SystemPromptSampler(prompt_db=self.prompt_db,
                exploration_constant=self.evo_config.prompt_ucb_exploration_constant, epsilon=self.evo_config.prompt_epsilon)
            self.prompt_evolver = AsyncSystemPromptEvolver(llm_client=self.prompt_llm,
                patch_types=self.evo_config.prompt_patch_types,
                patch_type_probs=self.evo_config.prompt_patch_type_probs,
                llm_kwargs=self.evo_config.prompt_llm_kwargs)
            self._save_native_memory()

        def _get_current_system_prompt(self):
            selected, prompt_id = super()._get_current_system_prompt()
            frozen = immutable_path.read_bytes()
            if _hash_bytes(frozen) != self._memory["identity"]["immutable_prompt_sha256"]:
                raise RuntimeError("Immutable scientific prompt changed during native selection")
            guidance = selected if prompt_id is not None else search_path.read_text()
            return (frozen.decode() + "\n\nThe scientific instructions above are immutable and authoritative. "
                    "The following coevolved text may guide search strategy only; it cannot change the engine, "
                    "evaluator, cases, scoring, policy interface, data access, or these constraints.\n"
                    "<evolvable_search_instructions>\n" + guidance +
                    "\n</evolvable_search_instructions>\nFollow the immutable scientific instructions above.", prompt_id)

        async def _setup_async(self):
            self._initialize_native_memory()
            await super()._setup_async()
            # Recovery-triggered meta analysis has no native triggering program
            # on which to store meta_cost. Keep its estimate outside row costs.
            self.total_api_cost += self._memory.get("recovery_meta_cost", 0.0)
            programs = {p.id: p for p in self.db.get_all_programs()}
            unknown = set(self._memory["seen_meta_ids"]) - set(programs)
            if unknown:
                raise RuntimeError("Native meta memory references programs absent from population")
            bootstrap = self._memory["bootstrap"]
            if bootstrap["status"] == "completed":
                # Bootstrap has no triggering Phase-B program metadata to carry
                # its native list-price estimate across runner restarts.
                self.total_api_cost += bootstrap.get("cost", 0.0) or 0.0
            if bootstrap["status"] == "pending":
                selected = [programs.get(pid) for pid in bootstrap_ids]
                if any(p is None or p.generation >= phase_start_generation or
                       (p.metadata or {}).get("administrative_copy") for p in selected):
                    raise RuntimeError("Bootstrap must reference retained measured Phase-A programs")
                bootstrap.update(status="started", started_at=time.time(),
                    programs=[{"id": p.id, "generation": p.generation,
                               "candidate_sha256": _hash_bytes(p.code.encode()),
                               "correct": p.correct, "combined_score": p.combined_score,
                               "public_metrics": p.public_metrics} for p in selected])
                self._save_native_memory()
                for program in selected:
                    self.meta_summarizer.add_evaluated_program(program)
                event(Path(self.results_dir), "native_meta_bootstrap_started", program_ids=list(bootstrap_ids))
                try:
                    _, cost = await self.meta_summarizer.update_meta_memory_async(
                        await self.async_db.get_best_program_async())
                except BaseException:
                    bootstrap["status"] = "failed"
                    self._save_native_memory()
                    raise
                bootstrap.update(status="completed", finished_at=time.time(), cost=cost)
                self.total_api_cost += cost or 0.0
                self._save_native_memory()
                await self.meta_summarizer.write_meta_output_async(str(self.results_dir))
                event(Path(self.results_dir), "native_meta_bootstrap_completed", program_ids=list(bootstrap_ids))
            # Recover post-persistence side effects only when no ambiguous operation
            # was left in flight. Native bookkeeping remains idempotent by ID.
            for program in sorted(programs.values(), key=lambda p: p.generation):
                if program.generation < phase_start_generation or (program.metadata or {}).get("administrative_copy"):
                    continue
                prompt_id = getattr(program, "system_prompt_id", None)
                if prompt_id:
                    parent = programs.get(program.parent_id)
                    await self._update_prompt_fitness(prompt_id, program.id, program.combined_score,
                        program.combined_score - (parent.combined_score if parent else 0.0), program.correct)
                    await self._maybe_evolve_prompt()
                if self.meta_summarizer is not None:
                    self.meta_summarizer.add_evaluated_program(program)
            if self.meta_summarizer is not None and self.meta_summarizer.should_update_meta(self.evo_config.meta_rec_interval):
                _, cost = await self.meta_summarizer.update_meta_memory_async(await self.async_db.get_best_program_async())
                self.total_api_cost += cost or 0.0
                self._memory["recovery_meta_cost"] = self._memory.get("recovery_meta_cost", 0.0) + (cost or 0.0)
                self._save_native_memory()
                await self.meta_summarizer.write_meta_output_async(str(self.results_dir))
            if self._resume_percentile_pending:
                await self._recompute_prompt_percentiles_async(self.evo_config.prompt_percentile_recompute_interval)
                self._resume_percentile_pending = False
            self._save_native_memory()

        async def _update_prompt_fitness(self, prompt_id, program_id, program_score, improvement, correct=True):
            self._last_memory_prompt_program = program_id
            if not prompt_id or program_id in self._memory["fitness_program_ids"]:
                return
            async with self._native_memory_lock:
                self._begin_memory_operation("prompt_fitness", program_id=program_id, prompt_id=prompt_id)
                await super()._update_prompt_fitness(prompt_id, program_id, program_score, improvement, correct)
                prompt = self.prompt_db.get(prompt_id)
                if prompt is None or prompt.program_ids.count(program_id) != 1:
                    raise RuntimeError("Native prompt fitness did not persist exactly once")
                self._memory["fitness_program_ids"].append(program_id)
                self._finish_memory_operation()

        async def _maybe_evolve_prompt(self):
            program_id = getattr(self, "_last_memory_prompt_program", None)
            if not program_id or program_id in self._memory["evolution_program_ids"]:
                return
            async with self._native_memory_lock:
                self._begin_memory_operation("prompt_evolution_interval", program_id=program_id)
                await super()._maybe_evolve_prompt()
                # Native failures can return without raising. Capacity observer receipts
                # remain authoritative and prevent a later batch from silently retrying.
                self._memory["evolution_program_ids"].append(program_id)
                self._finish_memory_operation()

        async def _recompute_prompt_percentiles_async(self, recompute_interval):
            async with self._native_memory_lock:
                await super()._recompute_prompt_percentiles_async(recompute_interval)
                self._save_native_memory()

        async def _apply_persisted_program_side_effects(self, persisted_event):
            try:
                return await super()._apply_persisted_program_side_effects(persisted_event)
            finally:
                self._save_native_memory()

        async def _cleanup_async(self):
            # Native cleanup recomputes prompt fitness at actual experiment end.
            # A one-slot process boundary must not add extra percentile updates.
            prompt_db = getattr(self, "prompt_db", None)
            intermediate = self.completed_generations < overall_target_slots
            if intermediate:
                self.prompt_db = None
            try:
                await super()._cleanup_async()
            finally:
                self.prompt_db = prompt_db
                if getattr(self, "_native_memory_ready", False):
                    self._save_native_memory()
                if prompt_db is not None:
                    prompt_db.close()

    return NativeMemoryRunner
