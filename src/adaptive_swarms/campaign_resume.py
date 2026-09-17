"""Opt-in persistence for the pinned native runner's multi-session campaigns.

Native code still selects, mutates, judges novelty, evaluates and updates meta
memory. This layer owns durable state and admission at session boundaries. It
uses explicit serialization because upstream meta save/load swallow errors.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
import sqlite3
import time
from datetime import datetime, timezone

import numpy as np

from .execution import InfrastructureError
from .logging import atomic_json
from .engine_progress import terminal_failure_generations

META_FIELDS = ("meta_summary", "meta_scratch_pad", "meta_recommendations", "meta_recommendations_history")


def _digest(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, allow_nan=False).encode()).hexdigest()


def _tuples(value):
    return tuple(_tuples(v) for v in value) if isinstance(value, list) else value


def sampler_state():
    state = np.random.get_state()
    return {"python": random.getstate(), "numpy": [state[0], state[1].tolist(), state[2], state[3], state[4]]}


def restore_sampler_state(state):
    random.setstate(_tuples(state["python"]))
    algorithm, keys, position, gaussian, cached = state["numpy"]
    np.random.set_state((algorithm, np.asarray(keys, dtype=np.uint32), position, gaussian, cached))


def validate_meta_state(state, programs):
    """Return ordered pending IDs after reconciling authoritative database rows."""
    expected = state.get("sha256")
    payload = {key: value for key, value in state.items() if key != "sha256"}
    if expected != _digest(payload) or state.get("version") != 1:
        raise InfrastructureError("Campaign checkpoint integrity/version check failed")
    meta = state["meta"]
    pending, processed = meta["pending_program_ids"], meta["processed_program_ids"]
    if len(pending) != len(set(pending)) or len(processed) != len(set(processed)) or set(pending) & set(processed):
        raise InfrastructureError("Campaign meta checkpoint contains duplicated or overlapping IDs")
    if meta["total_programs_processed"] != len(processed):
        raise InfrastructureError("Campaign meta processed count disagrees with its IDs")
    absent = (set(pending) | set(processed)) - set(programs)
    if absent:
        raise InfrastructureError(f"Campaign checkpoint refers to missing database programs: {sorted(absent)}")
    known = set(pending) | set(processed)
    missing = sorted((p for key, p in programs.items() if key not in known), key=lambda p: (p.generation, p.id))
    return list(pending) + [p.id for p in missing]


async def reuse_existing_native_seed(runner, *, resuming, log):
    """Pinned native last_iteration==0 resumes need this existing compatibility."""
    if resuming and await runner.async_db.get_total_program_count_async() > 0:
        await runner._restore_resume_progress()
        log.event("seed_reused", message="Existing native seed retained without another evaluation",
                  completed_generations=runner.completed_generations)
        return True
    return False


class CampaignResumeRunnerMixin:
    """Enable only through configure_campaign; historical runs stay unchanged."""

    def configure_campaign(self, *, campaign_generations, log, deadline_utc=None,
                           admission_seconds=0, response_reserve=12):
        self._campaign_size = campaign_generations
        self._campaign_log = log
        self._campaign_processed_ids = set()
        self._campaign_rng = None
        self._campaign_restored = False
        self._campaign_rng_restored = False
        self._campaign_had_checkpoint = (Path(self.results_dir) / "campaign-checkpoint.json").exists()
        self._campaign_pause_reason = None
        self._campaign_admission_seconds = float(admission_seconds)
        self._campaign_response_reserve = int(response_reserve)
        self._campaign_deadline = (datetime.fromisoformat(deadline_utc.replace("Z", "+00:00")).timestamp()
                                   if deadline_utc else None)
        self._campaign_monotonic_deadline = (time.monotonic() + max(0, self._campaign_deadline - time.time())
                                             if self._campaign_deadline else None)
        if self.meta_summarizer is None:
            raise ValueError("Resumable campaign requires the configured native meta summarizer")
        meta = self.meta_summarizer
        sync = meta.sync_summarizer
        original_add = sync.add_evaluated_program
        original_update = meta.update_meta_memory_async
        original_final = meta.perform_final_summary_async

        def add(program):
            if program.id in self._campaign_processed_ids or any(p.id == program.id for p in sync.evaluated_since_last_meta):
                return
            original_add(program)
            self._checkpoint_campaign("tracked_program")

        async def update(*args, **kwargs):
            before = {p.id for p in sync.evaluated_since_last_meta}
            result = await original_update(*args, **kwargs)
            after = {p.id for p in sync.evaluated_since_last_meta}
            self._campaign_processed_ids.update(before - after)
            self._checkpoint_campaign("meta_update")
            return result

        async def final(*args, **kwargs):
            if not self._campaign_complete():
                self._campaign_log.event("intermediate_meta_summary_suppressed",
                    message="Session pause retains pending meta programs; interval-five updates remain active",
                    campaign_generations=self._campaign_size)
                return False, 0.0
            return await original_final(*args, **kwargs)

        sync.add_evaluated_program = add
        meta.update_meta_memory_async = update
        meta.perform_final_summary_async = final

    def _campaign_programs(self):
        return {p.id: p for p in self.db.get_all_programs()
                if not any((p.metadata or {}).get(k) for k in ("_is_island_copy", "is_island_copy", "island_copy"))}

    def _campaign_complete(self):
        terminal = {p.generation for p in self._campaign_programs().values()}
        terminal |= terminal_failure_generations(Path(self.results_dir))
        return set(range(self._campaign_size)).issubset(terminal)

    def _checkpoint_campaign(self, reason, *, drained=False):
        if not hasattr(self, "_campaign_size"):
            return
        try:
            sync = self.meta_summarizer.sync_summarizer
            programs = self._campaign_programs()
            if drained:
                self._campaign_rng = sampler_state()
            payload = {"version": 1, "saved_at": datetime.now(timezone.utc).isoformat(),
                "reason": reason, "drained": drained, "campaign_generations": self._campaign_size,
                "session_generation_target": self.evo_config.num_generations,
                "next_generation_to_submit": self.next_generation_to_submit,
                "status": "campaign_complete" if self._campaign_complete() else "campaign_paused" if drained else "running",
                "meta": {**{key: getattr(sync, key) for key in META_FIELDS},
                    "pending_program_ids": [p.id for p in sync.evaluated_since_last_meta],
                    "processed_program_ids": sorted(self._campaign_processed_ids),
                    "total_programs_processed": sync.total_programs_processed},
                "sampler_rng": self._campaign_rng,
                "rng_scope": "Python/NumPy global samplers at last drained boundary; interrupted active work and provider outputs are not replay-guaranteed"}
            payload["sha256"] = _digest(payload)
            validate_meta_state(payload, programs)
            path = Path(self.results_dir) / "campaign-checkpoint.json"
            atomic_json(path, payload)
            saved = json.loads(path.read_text())
            validate_meta_state(saved, programs)
            if saved != json.loads(json.dumps(payload)):
                raise InfrastructureError("Campaign checkpoint read-back differs from written state")
            self._campaign_log.event("campaign_checkpoint", message=f"Validated campaign checkpoint: {reason}",
                drained=drained, pending_meta=len(payload["meta"]["pending_program_ids"]),
                processed_meta=sync.total_programs_processed, checkpoint=str(path))
        except (OSError, ValueError, KeyError, InfrastructureError) as exc:
            self._fail_infrastructure(exc if isinstance(exc, InfrastructureError) else InfrastructureError(str(exc)))

    def _restore_campaign(self):
        path = Path(self.results_dir) / "campaign-checkpoint.json"
        programs = self._campaign_programs()
        sync = self.meta_summarizer.sync_summarizer
        if path.exists():
            state = json.loads(path.read_text())
            if state["campaign_generations"] != self._campaign_size:
                raise InfrastructureError("Campaign size differs from immutable checkpoint")
            pending = validate_meta_state(state, programs)
            for key in META_FIELDS:
                setattr(sync, key, state["meta"][key])
            self._campaign_processed_ids = set(state["meta"]["processed_program_ids"])
            sync.total_programs_processed = state["meta"]["total_programs_processed"]
            sync.evaluated_since_last_meta = [programs[pid] for pid in pending]
            self._campaign_rng = state.get("sampler_rng")
            if self._campaign_rng is not None:
                restore_sampler_state(self._campaign_rng)
            self._campaign_restored = self._campaign_had_checkpoint
            self._campaign_rng_restored = self._campaign_had_checkpoint and self._campaign_rng is not None
            self._campaign_log.event("campaign_restored", message="Meta state and known sampler state restored before proposal admission",
                pending_meta_ids=pending, processed_meta=sync.total_programs_processed,
                rng_restored=self._campaign_rng is not None, previous_checkpoint_drained=state["drained"])
        elif programs:
            # The first seed may already have been tracked during native setup.
            # A preexisting campaign database without a checkpoint cannot be
            # silently treated as having empty historical meta memory.
            if any(p.generation > 0 for p in programs.values()):
                raise InfrastructureError("Campaign descendants exist without a meta checkpoint")
            sync.evaluated_since_last_meta = sorted(programs.values(), key=lambda p: (p.generation, p.id))
        self._checkpoint_campaign("setup_reconciled", drained=not self.running_jobs and not self.active_proposal_tasks)

    async def _setup_async(self):
        await super()._setup_async()
        if hasattr(self, "_campaign_size"):
            self._restore_campaign()

    async def _start_proposals(self, num_proposals):
        if hasattr(self, "_campaign_size"):
            # One proposal/evaluation worker, with no pipeline of unevaluated
            # proposals across a boundary: drain native maintenance/meta first.
            if self.running_jobs or self.active_proposal_tasks or self._get_completed_job_work_count() or self._has_background_side_effect_work():
                return
            remaining = min(self._campaign_deadline - time.time(), self._campaign_monotonic_deadline - time.monotonic()) if self._campaign_deadline else float("inf")
            budget = getattr(self, "logical_response_budget", None)
            response_remaining = min(budget.limit - budget.used,
                budget.session_start + budget.session_limit - budget.used if budget.session_limit is not None else float("inf")) if budget else float("inf")
            if remaining < self._campaign_admission_seconds or response_remaining < self._campaign_response_reserve:
                self._campaign_pause_reason = "insufficient_complete_proposal_time" if remaining < self._campaign_admission_seconds else "session_model_reserve"
                self.evo_config.num_generations = self.next_generation_to_submit
                self.slot_available.set()
                self._campaign_log.event("campaign_admission_closed", message="No further proposal admitted; draining this session",
                    reason=self._campaign_pause_reason, remaining_seconds=remaining, responses_remaining=response_remaining,
                    generation_target=self.evo_config.num_generations)
                return
            self._checkpoint_campaign("before_proposal", drained=True)
        return await super()._start_proposals(num_proposals)

    async def _cleanup_async(self):
        if hasattr(self, "_campaign_size"):
            # Native normal finalization already awaited these. Repeat joins are
            # safe; exceptional exits must not label incomplete work drained.
            clean = self.finalization_complete.is_set() and not self.running_jobs and not self.active_proposal_tasks
            if clean:
                await self._wait_for_completed_job_batches()
                await self._wait_for_background_side_effects()
                task = getattr(self, "_prompt_percentile_recompute_task", None)
                if task is not None:
                    await task
                with sqlite3.connect(str(Path(self.results_dir) / "programs.sqlite")) as connection:
                    connection.execute("PRAGMA wal_checkpoint(FULL)")
                self._checkpoint_campaign("clean_pause" if not self._campaign_complete() else "campaign_complete", drained=True)
            else:
                self._checkpoint_campaign("interrupted_boundary", drained=False)
        await super()._cleanup_async()

    async def _print_final_summary(self):
        if hasattr(self, "_campaign_size") and not self._campaign_complete():
            self._campaign_log.event("campaign_session_paused", message="Session finished; campaign remains open, no winner freeze or fresh evaluation",
                session_generation_target=self.evo_config.num_generations, campaign_generations=self._campaign_size)
            return
        await super()._print_final_summary()
