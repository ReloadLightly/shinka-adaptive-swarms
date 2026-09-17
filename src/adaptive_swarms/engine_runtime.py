"""Observable native engine calls and explicit degradation of requested machinery.

These adapters preserve native sampling, prompts, retries and novelty decisions.
They record logical requests (not hidden provider retry or token-stream counts).
"""
from __future__ import annotations

import math
import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .logging import atomic_json


def install_sampling_observer(runner, log) -> None:
    """Record the exact native sampling result without drawing additional RNGs."""
    database = runner.async_db
    original = database.sample_with_fix_mode_async

    async def sample(*args, **kwargs):
        result = await original(*args, **kwargs)
        parent, archive, top, needs_fix = result
        log.event("native_sampling", message="Native parent and inspiration selection completed",
                  generation=kwargs.get("target_generation"),
                  novelty_attempt=kwargs.get("novelty_attempt"),
                  resample_attempt=kwargs.get("resample_attempt"),
                  parent_id=getattr(parent, "id", None),
                  parent_generation=getattr(parent, "generation", None),
                  archive_inspiration_ids=[p.id for p in archive],
                  top_k_inspiration_ids=[p.id for p in top], needs_fix=needs_fix)
        return result

    database.sample_with_fix_mode_async = sample


def install_engine_observers(runner, log, run_dir: Path, logical_response_limit=None, session_response_limit=None, session_response_start=None) -> Callable[[], None]:
    from .sprint_budget import (LogicalResponseBudget, SprintLimitReached,
                                install_native_retry_observer, native_request_context)
    budget = LogicalResponseBudget(run_dir, logical_response_limit, session_limit=session_response_limit, session_start=session_response_start) if logical_response_limit is not None else None
    runner.logical_response_budget = budget
    def stop_for_allowance(error):
        log.event("sprint_limit_reached", message=str(error), limit=budget.limit,
                  reserved_logical_responses=budget.used, scientific_failure=False)
        runner._fail_infrastructure(error)
    remove_retry_observer = install_native_retry_observer(budget, stop_for_allowance) if budget else lambda: None
    class MigrationLogBridge(logging.Handler):
        def emit(self, record):
            message = record.getMessage()
            if "migration" in message.lower() or "migrated" in message.lower():
                log.event("native_migration_log", message=message,
                          native_logger=record.name, level=record.levelname,
                          evidence_scope="native message; exact transfers remain in database migration_history")

    migration_logger = logging.getLogger("shinka.database.islands")
    migration_bridge = MigrationLogBridge(level=logging.INFO)
    migration_logger.addHandler(migration_bridge)

    def degraded(message, **details):
        log.event("engine_feature_degraded", message=message, native_fallback_preserved=True, **details)

    def observe_client(client, role, required):
        if client is None:
            return
        for method_name in ("query", "batch_kwargs_query"):
            original = getattr(client, method_name)

            def make_wrapper(original, method_name):
                async def observed(*args, **kwargs):
                    call_id = role + "-" + uuid.uuid4().hex
                    started = time.monotonic()
                    batch = method_name == "batch_kwargs_query"
                    requested = kwargs.get("num_samples", args[0] if args and batch else 1)
                    receipt = {"call_id": call_id, "role": role, "method": method_name,
                               "started_at": datetime.now(timezone.utc).isoformat(),
                               "requested_logical_responses": requested,
                               "configured_models": list(client.model_names), "status": "started",
                               "configured_client_settings": {key: getattr(client, key, None)
                                                              for key in ("temperatures", "max_tokens", "reasoning_efforts")},
                               "explicit_request_kwargs": kwargs.get("llm_kwargs", args[3] if not batch and len(args) > 3 else None),
                               "effective_provider_effort": "unverified; configured/requested values are recorded separately",
                               "system_msg": kwargs.get("system_msg", args[2 if batch else 1] if len(args) > (2 if batch else 1) else None),
                               "msg": kwargs.get("msg", args[1 if batch else 0] if len(args) > (1 if batch else 0) else None),
                               "count_scope": "logical native requests only; internal provider retry counts and coverage are unknown"}
                    path = run_dir / "engine_calls" / (call_id + ".json")
                    if budget:
                        try:
                            budget.reserve(path, receipt, requested)
                        except SprintLimitReached as exc:
                            stop_for_allowance(exc)
                            raise
                    else:
                        atomic_json(path, receipt)
                    log.set_activity(f"{role}: waiting for {requested} native model response(s)")
                    log.event("engine_role_call_start", message=f"{role}: native {method_name}, {requested} response(s) requested",
                              call_id=call_id, role=role, requested_logical_responses=requested, receipt=str(path))
                    token = native_request_context.set((receipt, path)) if budget else None
                    try:
                        timeout = getattr(runner, "_campaign_deadline", None)
                        if timeout is not None:
                            remaining = min(timeout - time.time(), runner._campaign_monotonic_deadline - time.monotonic())
                            if remaining <= 0:
                                runner._fail_infrastructure(SprintLimitReached("Session research cutoff reached before native model dispatch"))
                            try:
                                result = await asyncio.wait_for(original(*args, **kwargs), timeout=remaining)
                            except asyncio.TimeoutError as exc:
                                from .execution import InfrastructureError
                                runner._fail_infrastructure(InfrastructureError(
                                    "Native model wait reached the bounded session deadline; preserve pending work"))
                                raise exc
                        else:
                            result = await original(*args, **kwargs)
                    except SprintLimitReached as exc:
                        receipt.update(status="stopped_allowance", finished_at=datetime.now(timezone.utc).isoformat(),
                                       error=str(exc), elapsed_seconds=time.monotonic() - started)
                        atomic_json(path, receipt)
                        raise
                    except Exception as exc:
                        receipt.update(status="failed", finished_at=datetime.now(timezone.utc).isoformat(), error=f"{type(exc).__name__}: {exc}", elapsed_seconds=time.monotonic() - started)
                        atomic_json(path, receipt)
                        log.event("engine_role_call_failed", message=f"{role}: native request failed", call_id=call_id, role=role, error=receipt["error"])
                        if required:
                            degraded(f"Requested {role} model call failed; native error handling applies", role=role, call_id=call_id)
                        raise
                    finally:
                        if token is not None:
                            native_request_context.reset(token)
                    responses = result if batch else [result]
                    valid = [response for response in responses or [] if response is not None and getattr(response, "content", None)]
                    receipt.update(status="returned", finished_at=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic() - started,
                                   valid_responses=len(valid), responses=[{
                                       "model_reported_by_native_client": getattr(response, "model_name", None),
                                       "input_tokens": getattr(response, "input_tokens", None),
                                       "output_tokens": getattr(response, "output_tokens", None),
                                       "reported_api_cost": getattr(response, "cost", None),
                                       "content": response.content,
                                   } for response in valid])
                    atomic_json(path, receipt)
                    log.event("engine_role_call_returned", message=f"{role}: {len(valid)}/{requested} native responses returned",
                              call_id=call_id, role=role, valid_responses=len(valid), elapsed_seconds=receipt["elapsed_seconds"], receipt=str(path))
                    if required and len(valid) != requested:
                        receipt["status"] = "degraded"
                        atomic_json(path, receipt)
                        degraded(f"Requested {role} machinery returned {len(valid)}/{requested} usable responses; native fallback applies", role=role, call_id=call_id)
                    return result
                return observed

            setattr(client, method_name, make_wrapper(original, method_name))

    observe_client(runner.llm, "mutation", required=False)
    if runner.meta_summarizer:
        observe_client(runner.meta_summarizer.async_llm_client, "meta", required=True)
        original_update = runner.meta_summarizer.update_meta_memory_async

        async def update_meta(*args, **kwargs):
            pending = len(runner.meta_summarizer.sync_summarizer.evaluated_since_last_meta)
            log.event("meta_update_start", message="Native meta-scratchpad update started", pending_programs=pending)
            result = await original_update(*args, **kwargs)
            if not result or not result[0]:
                if pending:
                    degraded("Native meta-scratchpad update produced no new recommendations", role="meta")
                else:
                    log.event("meta_update_noop", message="Native meta update had no new programs to summarize")
            else:
                log.event("meta_update_complete", message="Native meta-scratchpad recommendations updated")
            return result

        runner.meta_summarizer.update_meta_memory_async = update_meta
    if runner.novelty_judge:
        observe_client(runner.novelty_judge.async_llm_client, "novelty", required=True)
        original_assess = runner.novelty_judge.assess_novelty_with_rejection_sampling_async

        async def assess_novelty(*args, **kwargs):
            accepted, details = await original_assess(*args, **kwargs)
            # Native accepts on some errors. Preserve that algorithmic behavior
            # while separating fallback acceptance from a substantive judgment.
            explanation = details.get("novelty_explanation", "")
            fallback = "similarity_scores" not in details or explanation.startswith(("Error in novelty check:", "LLM response was empty"))
            if fallback:
                degraded("Native novelty used fallback handling; acceptance does not establish a passed novelty check", role="novelty")
            log.event("novelty_decision", message=f"Native novelty {'fallback ' if fallback else ''}{'accepted' if accepted else 'rejected'} candidate",
                      accepted=accepted, fallback=fallback, **details)
            return accepted, details

        runner.novelty_judge.assess_novelty_with_rejection_sampling_async = assess_novelty
    if runner.embedding_client:
        original_embedding = runner._get_code_embedding_async

        async def code_embedding(exec_fname):
            log.event("embedding_start", message="Waiting for local code embedding", program=str(exec_fname))
            vector, cost = await original_embedding(exec_fname)
            try:
                finite = vector is not None and len(vector) > 0 and all(math.isfinite(value) for value in vector)
            except (TypeError, ValueError):
                finite = False
            if not finite:
                degraded("Local code embedding returned no finite vector; native novelty may skip this candidate", role="embedding", program=str(exec_fname))
            else:
                log.event("embedding_complete", message="Local code embedding returned", program=str(exec_fname), dimensions=len(vector))
            return vector, cost

        runner._get_code_embedding_async = code_embedding

    def cleanup():
        migration_logger.removeHandler(migration_bridge)
        remove_retry_observer()
    return cleanup
