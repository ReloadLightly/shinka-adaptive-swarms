"""Accepted-proposal resume compatibility and actual I/O failure boundaries.

No free-space, mount, write-size, or periodic storage checks run here. Historical
storage-job.json files retain their names so accepted proposals keep their lineage.
"""
from __future__ import annotations

import asyncio
import contextlib
from dataclasses import fields
import sqlite3
from pathlib import Path
import time

from .execution import InfrastructureError, INFRASTRUCTURE_EXIT_CODE
from .logging import atomic_json
from .engine_progress import terminal_failure_generations


class ResumeRunnerMixin:
    def configure_resume(self, log):
        self.resume_log = log
        self._infrastructure_error = None
        self._infrastructure_failed = asyncio.Event()
        self._execution_loop = None
        if hasattr(self, "scheduler"):
            original_run = self.scheduler.run
            original_results = self.scheduler.get_job_results_async

            def run(exec_fname, results_dir, *args, **kwargs):
                try:
                    result = original_run(exec_fname, results_dir, *args, **kwargs)
                    self._check_evaluation_result(results_dir)
                    return result
                except (OSError, InfrastructureError) as exc:
                    self._fail_infrastructure(exc)

            async def results(job_id, results_dir, *args, **kwargs):
                try:
                    self._check_evaluation_result(results_dir, job_id)
                    result = await original_results(job_id, results_dir, *args, **kwargs)
                    self._check_evaluation_result(results_dir, job_id)
                    return result
                except (OSError, InfrastructureError) as exc:
                    self._fail_infrastructure(exc)

            self.scheduler.run = run
            self.scheduler.get_job_results_async = results

    def _fail_infrastructure(self, error):
        failure = error if isinstance(error, InfrastructureError) else InfrastructureError(str(error))
        self._infrastructure_error = failure

        def notify():
            self._infrastructure_failed.set()
            self.should_stop.set()

        # Native seed evaluation and log sinks also run in worker threads.
        # Dispatch their actual error notification onto the controller loop.
        if self._execution_loop is not None and self._execution_loop.is_running():
            self._execution_loop.call_soon_threadsafe(notify)
        else:
            notify()
        if failure is error:
            raise failure
        raise failure from error

    def _check_output_errors(self):
        check = getattr(self, "check_output_errors", None)
        if check is not None:
            try:
                check()
            except (OSError, InfrastructureError) as exc:
                self._fail_infrastructure(exc)

    def _check_evaluation_result(self, results_dir, job_id=None):
        self._check_output_errors()
        # Exit 75 is retained only for historical evaluator compatibility. An
        # old storage-stop marker or low free-space reading never blocks work.
        returncode = getattr(job_id, "returncode", None)
        if returncode in {INFRASTRUCTURE_EXIT_CODE, 75}:
            self._fail_infrastructure(InfrastructureError(
                f"Evaluator exited {returncode}: {results_dir}; see job_log.err"))
        for name in ("metrics.json", "correct.json"):
            if not (Path(results_dir) / name).is_file():
                self._fail_infrastructure(InfrastructureError(
                    f"Evaluator did not write {name}: {results_dir}; no scientific judgment recorded"))

    async def _submit_evaluation_job_with_slot(self, exec_fname, results_dir, sampling_worker_id):
        try:
            return await super()._submit_evaluation_job_with_slot(exec_fname, results_dir, sampling_worker_id)
        except (OSError, InfrastructureError) as exc:
            self._fail_infrastructure(exc)

    def _save_pending_job(self, job):
        record = {field.name: getattr(job, field.name) for field in fields(job)
                  if field.name != "job_id"}
        record["checkpoint_version"] = 1
        try:
            atomic_json(Path(job.exec_fname).parent / "storage-job.json", record)
        except OSError as exc:
            self._fail_infrastructure(exc)

    async def _generate_proposal_async(self, generation, task_id):
        try:
            result = await super()._generate_proposal_async(generation, task_id)
            if result is not None:
                self._save_pending_job(result)
            return result
        except (OSError, InfrastructureError) as exc:
            self._fail_infrastructure(exc)

    async def _persist_completed_job(self, job):
        self._check_evaluation_result(job.results_dir, job.job_id)
        return await super()._persist_completed_job(job)

    def _install_database_failure_boundary(self):
        database = self.async_db
        if getattr(database, "_project_io_boundary", False):
            return
        original_add = database.add_program_async

        async def add(*args, **kwargs):
            self._check_output_errors()
            try:
                return await original_add(*args, **kwargs)
            except (OSError, sqlite3.DatabaseError) as exc:
                self._fail_infrastructure(exc)

        database.add_program_async = add
        database._project_io_boundary = True

    async def _setup_initial_program_with_metadata(self, *args, **kwargs):
        self._install_database_failure_boundary()
        return await super()._setup_initial_program_with_metadata(*args, **kwargs)

    async def _record_terminal_failed_proposal(self, *args, **kwargs):
        reason = str(kwargs.get("failure_reason", "")).lower()
        if any(message in reason for message in ("no space left on device", "disk quota exceeded", "database or disk is full")):
            self._fail_infrastructure(InfrastructureError(reason))
        self._check_output_errors()
        return await super()._record_terminal_failed_proposal(*args, **kwargs)

    async def _setup_async(self):
        await super()._setup_async()
        self._install_database_failure_boundary()
        await self._restore_pending_jobs()

    async def _restore_pending_jobs(self):
        from shinka.core.async_runner import AsyncRunningJob
        from .native_storage import recover_pending_spec

        persisted = set(await self.async_db.get_persisted_generation_ids_async())
        terminal_failures = terminal_failure_generations(Path(self.results_dir))
        self._preserved_terminal_failures = terminal_failures
        if terminal_failures:
            self.next_generation_to_submit = max(self.next_generation_to_submit, max(terminal_failures) + 1)
            self.resume_log.event("terminal_proposals_retained", message="Native terminal proposal failures retained without new mutations or evaluations",
                                  generations=sorted(terminal_failures))
        pending = []
        for folder in sorted(Path(self.results_dir).glob("gen_*"), key=lambda p: int(p.name.split("_")[-1])):
            generation = int(folder.name.split("_")[-1])
            if generation in persisted or generation in terminal_failures or generation >= self.evo_config.num_generations:
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
                self._save_pending_job(job)
                self.resume_log.event("accepted_program_resumed", generation=generation,
                    message="Saved native proposal retained; completed cases will be reused", program=str(folder / "main.py"))
            except (OSError, InfrastructureError) as exc:
                self._fail_infrastructure(exc)
            finally:
                self.active_proposal_tasks.pop(task_id, None)
                self.slot_available.set()

        # Register waiting accepted evaluations as in-flight tasks, then return
        # so the native monitor can release slots. Awaiting all submissions here
        # deadlocks when pending programs exceed the evaluation worker count.
        for folder, generation, record in pending:
            task_id = f"accepted_resume_{generation}"
            self.next_generation_to_submit = max(self.next_generation_to_submit, generation + 1)
            task = asyncio.create_task(submit_saved(folder, generation, record, task_id), name=task_id)
            self.active_proposal_tasks[task_id] = task

    async def _start_proposals(self, num_proposals):
        # An earlier interrupted proposal can rewind the assignment cursor.
        # Skip already terminal slots as the native coordinator reaches them.
        terminal = getattr(self, "_preserved_terminal_failures", set())
        if not terminal:
            return await super()._start_proposals(num_proposals)
        for _ in range(num_proposals):
            while self.next_generation_to_submit in terminal:
                self.next_generation_to_submit += 1
            await super()._start_proposals(1)

    async def _run_async(self):
        # Native background task callbacks can consume exceptions. Surface an
        # actual failed I/O operation to the launcher even in that case. This
        # waits on an error event; it never polls disks or imposes a pause rule.
        self._execution_loop = asyncio.get_running_loop()
        native = asyncio.create_task(super()._run_async())
        failed = asyncio.create_task(self._infrastructure_failed.wait())
        try:
            done, _ = await asyncio.wait([native, failed], return_when=asyncio.FIRST_COMPLETED)
            if native in done:
                await native
            if self._infrastructure_error is not None:
                raise self._infrastructure_error
            self._check_output_errors()
        finally:
            failed.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await failed
            if not native.done():
                native.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await native
