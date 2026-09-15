"""Storage boundaries around the pinned native Shinka scheduler.

Search, selection, evaluation and database persistence remain native. A storage
stop cancels operational work and leaves accepted programs available for resume.
"""
from __future__ import annotations

import asyncio
import contextlib
from dataclasses import fields
import json
import sqlite3
from pathlib import Path
import time

from .logging import atomic_json
from .storage import StorageInterrupted


class StorageRunnerMixin:
    def configure_storage(self, guard, log):
        self.storage_guard = guard
        self.storage_log = log
        self._storage_interrupt = None
        self._storage_workers_stopped = False
        # Generation zero uses scheduler.run directly, outside proposal/finished
        # job hooks. Guard the actual synchronous and asynchronous result boundary
        # before native code can turn a paused evaluator's missing files into 0.
        if hasattr(self, "scheduler"):
            original_run = self.scheduler.run
            original_results = self.scheduler.get_job_results_async

            def guarded_run(exec_fname, results_dir, *args, **kwargs):
                self.storage_guard.check(force=True, activity="before native seed evaluation", active_workers=1)
                try:
                    result = original_run(exec_fname, results_dir, *args, **kwargs)
                except OSError as exc:
                    self.storage_guard.disk_full(exc, activity="native seed evaluation")
                self._check_evaluation_storage(results_dir)
                return result

            async def guarded_results(job_id, results_dir, *args, **kwargs):
                self._check_evaluation_storage(results_dir, job_id)
                try:
                    result = await original_results(job_id, results_dir, *args, **kwargs)
                except OSError as exc:
                    self.storage_guard.disk_full(exc, activity="reading native evaluation results")
                self._check_evaluation_storage(results_dir, job_id)
                return result

            self.scheduler.run = guarded_run
            self.scheduler.get_job_results_async = guarded_results

    def _check_evaluation_storage(self, results_dir, job_id=None):
        checkpoint = Path(results_dir) / "evaluation-checkpoint.json"
        paused = checkpoint.exists() and json.loads(checkpoint.read_text()).get("status") == "storage_paused"
        returncode = getattr(job_id, "returncode", None)
        if paused or returncode == 75:
            self.storage_guard.request_stop("evaluator requested storage checkpoint", results_dir=str(results_dir))
        self.storage_guard.check(force=True, activity=f"before reading evaluation {Path(results_dir).parent.name}")

    def _storage_check(self, activity, extra_workers=0):
        try:
            self.storage_guard.check(force=True, activity=activity,
                active_workers=len(self.running_jobs) + len(self.active_proposal_tasks) + extra_workers)
        except StorageInterrupted as exc:
            self._storage_interrupt = exc
            self.should_stop.set()
            # Cancellation also bypasses native scientific-failure handlers, and
            # behaves correctly in native proposal tasks' done callbacks.
            raise asyncio.CancelledError(str(exc)) from exc

    async def _start_proposals(self, num_proposals):
        self._storage_check("before native proposal scheduling", extra_workers=num_proposals)
        return await super()._start_proposals(num_proposals)

    async def _submit_evaluation_job_with_slot(self, exec_fname, results_dir, sampling_worker_id):
        self._storage_check(f"before evaluation {Path(exec_fname).parent.name}", extra_workers=1)
        try:
            return await super()._submit_evaluation_job_with_slot(exec_fname, results_dir, sampling_worker_id)
        except OSError as exc:
            self.storage_guard.disk_full(exc, activity="submitting native evaluation")

    def _save_storage_job(self, job):
        record = {field.name: getattr(job, field.name) for field in fields(job)
                  if field.name != "job_id"}
        record["checkpoint_version"] = 1
        try:
            atomic_json(Path(job.exec_fname).parent / "storage-job.json", record)
        except OSError as exc:
            self.storage_guard.disk_full(exc, activity="saving accepted native job checkpoint")

    async def _generate_proposal_async(self, generation, task_id):
        self._storage_check(f"generation {generation}: proposal")
        try:
            result = await super()._generate_proposal_async(generation, task_id)
        except OSError as exc:
            self.storage_guard.disk_full(exc, activity=f"generation {generation} proposal")
        if result is not None:
            self._save_storage_job(result)
        return result

    async def _persist_completed_job(self, job):
        try:
            self._check_evaluation_storage(job.results_dir, job.job_id)
        except StorageInterrupted as exc:
            self._storage_interrupt = exc
            self.should_stop.set()
            raise asyncio.CancelledError(str(exc)) from exc
        return await super()._persist_completed_job(job)

    def _install_storage_database_boundary(self):
        database = self.async_db
        if getattr(database, "_project_storage_guarded", False):
            return
        original_add = database.add_program_async

        async def guarded_add(*args, **kwargs):
            self.storage_guard.check(force=True, activity="before native database persistence")
            try:
                return await original_add(*args, **kwargs)
            except OSError as exc:
                self.storage_guard.disk_full(exc, activity="native database persistence")
            except sqlite3.DatabaseError as exc:
                if getattr(exc, "sqlite_errorcode", None) != sqlite3.SQLITE_FULL and "database or disk is full" not in str(exc).lower():
                    raise
                self.storage_guard.request_stop("native_database_full", error=str(exc))
                raise StorageInterrupted("Native database full; retained results await resume") from exc

        database.add_program_async = guarded_add
        database._project_storage_guarded = True

    async def _setup_initial_program_with_metadata(self, *args, **kwargs):
        self._install_storage_database_boundary()
        return await super()._setup_initial_program_with_metadata(*args, **kwargs)

    async def _record_terminal_failed_proposal(self, *args, **kwargs):
        reason = str(kwargs.get("failure_reason", "")).lower()
        if any(message in reason for message in ("no space left on device", "disk quota exceeded", "database or disk is full")):
            self.storage_guard.request_stop("native_proposal_storage_error", error=reason)
        self._storage_check("before native scientific proposal-failure record")
        return await super()._record_terminal_failed_proposal(*args, **kwargs)

    async def _setup_async(self):
        await super()._setup_async()
        self._install_storage_database_boundary()
        await self._restore_storage_jobs()

    async def _restore_storage_jobs(self):
        from shinka.core.async_runner import AsyncRunningJob
        from .native_storage import recover_pending_spec

        persisted = set(await self.async_db.get_persisted_generation_ids_async())
        pending = []
        for folder in sorted(Path(self.results_dir).glob("gen_*"), key=lambda p: int(p.name.split("_")[-1])):
            generation = int(folder.name.split("_")[-1])
            if generation in persisted or generation >= self.evo_config.num_generations:
                continue
            record = recover_pending_spec(folder, self.db)
            if record is None:
                # Retain incomplete proposal evidence; native can create its next attempt.
                archive = Path(self.results_dir) / "interrupted_proposals"
                archive.mkdir(exist_ok=True)
                folder.rename(archive / f"{folder.name}-{time.time_ns()}")
                self.next_generation_to_submit = min(self.next_generation_to_submit, generation)
                continue
            record.pop("checkpoint_version", None)
            record.pop("job_id", None)
            pending.append((folder, generation, record))

        async def submit_saved(folder, generation, record, task_id):
            try:
                self._storage_check(f"resume accepted generation {generation}", extra_workers=1)
                jid, wid, submitted, started, running = await self._submit_evaluation_job_with_slot(
                    str(folder / "main.py"), str(folder / "results"), None)
                record.update(job_id=jid, exec_fname=str(folder / "main.py"), results_dir=str(folder / "results"),
                              evaluation_worker_id=wid, evaluation_submitted_at=submitted,
                              evaluation_started_at=started, running_eval_jobs_at_submit=running,
                              evaluation_slot_released=False, discard_if_completed=False,
                              start_time=time.time(), db_retry_count=0)
                valid_fields = {f.name for f in fields(AsyncRunningJob)}
                job = AsyncRunningJob(**{k:v for k,v in record.items() if k in valid_fields})
                self.running_jobs.append(job)
                self.submitted_jobs[str(jid)] = job
                self._save_storage_job(job)
                self.storage_log.event("accepted_program_resumed", generation=generation,
                    message="Saved native proposal retained; completed cases will be reused", program=str(folder / "main.py"))
            except StorageInterrupted as exc:
                self._storage_interrupt = exc
                self.should_stop.set()
            finally:
                self.active_proposal_tasks.pop(task_id, None)
                self.slot_available.set()

        # Register waiting accepted evaluations as in-flight tasks, then return
        # so the native monitor can release slots. Awaiting all submissions here
        # deadlocks when pending programs exceed the evaluation worker count.
        for folder, generation, record in pending:
            task_id = f"storage_resume_{generation}"
            self.next_generation_to_submit = max(self.next_generation_to_submit, generation + 1)
            task = asyncio.create_task(submit_saved(folder, generation, record, task_id), name=task_id)
            self.active_proposal_tasks[task_id] = task

    async def _stop_storage_workers(self):
        if self._storage_workers_stopped:
            return
        self._storage_workers_stopped = True
        self.should_stop.set()
        # Cancel proposal scheduling first. Shared marker checks stop evaluator
        # writes; the short grace period permits completed-case checkpointing.
        tasks = list(self.active_proposal_tasks.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.wait(tasks, timeout=0.5)
        jobs = {job.generation: job for job in list(getattr(self, "submitted_jobs", {}).values()) + list(self.running_jobs)}
        for job in jobs.values():
            with contextlib.suppress(StorageInterrupted):
                self._save_storage_job(job)
        import psutil
        children = psutil.Process().children(recursive=True)
        await asyncio.sleep(5)
        # Use native cancellation for its tracked evaluator jobs before enforcing
        # cancellation on any remaining owned descendants (including proposals).
        for job in jobs.values():
            if getattr(job.job_id, "poll", lambda: 0)() is None:
                with contextlib.suppress(asyncio.TimeoutError, StorageInterrupted, OSError):
                    await asyncio.wait_for(self.scheduler.cancel_job_async(job.job_id), timeout=2)
        for child in children:
            with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied):
                child.terminate()
        _, alive = await asyncio.to_thread(psutil.wait_procs, children, timeout=2)
        for child in alive:
            with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied):
                child.kill()
        with contextlib.suppress(StorageInterrupted, OSError):
            self.storage_log.event("storage_workers_stopped", message="Owned workers stopped; native records and case checkpoints retained",
                checkpoint=str(self.storage_guard.stop_path), completed_generations=self.completed_generations)

    async def _run_async(self):
        async def monitor():
            while True:
                try:
                    self.storage_guard.check(force=True, activity="native workers running",
                        active_workers=len(self.running_jobs) + len(self.active_proposal_tasks))
                except StorageInterrupted as exc:
                    self._storage_interrupt = exc
                    self.should_stop.set()
                    return
                await asyncio.sleep(self.storage_guard.config.check_interval_seconds)

        self._storage_check("before native initialization")
        native = asyncio.create_task(super()._run_async())
        watcher = asyncio.create_task(monitor())
        try:
            done, _ = await asyncio.wait([native, watcher], return_when=asyncio.FIRST_COMPLETED)
            if native in done:
                try:
                    await native
                except StorageInterrupted as exc:
                    self._storage_interrupt = exc
                except asyncio.CancelledError:
                    if self._storage_interrupt is None:
                        raise
            if watcher in done:
                # Surface unexpected monitor failures instead of abandoning live
                # workers silently (ordinary space pauses return successfully).
                await watcher
            if self._storage_interrupt or self.storage_guard.stopped:
                await self._stop_storage_workers()
                native.cancel()
                with contextlib.suppress(asyncio.CancelledError, StorageInterrupted):
                    await native
                raise self._storage_interrupt or StorageInterrupted("Storage checkpoint requested")
        finally:
            watcher.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await watcher
            if not native.done():
                native.cancel()
                with contextlib.suppress(asyncio.CancelledError, StorageInterrupted):
                    await native
