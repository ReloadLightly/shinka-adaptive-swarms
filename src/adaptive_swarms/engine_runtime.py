"""Observable native engine calls and explicit degradation of requested machinery.

These adapters preserve native sampling, prompts, retries and novelty decisions.
They record logical requests (not hidden provider retry or token-stream counts).
"""
from __future__ import annotations

import math
import time
import uuid
from pathlib import Path

from .logging import atomic_json


def install_engine_observers(runner, log, run_dir: Path) -> None:
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
                               "requested_logical_responses": requested,
                               "configured_models": list(client.model_names), "status": "started",
                               "system_msg": kwargs.get("system_msg", args[2 if batch else 1] if len(args) > (2 if batch else 1) else None),
                               "msg": kwargs.get("msg", args[1 if batch else 0] if len(args) > (1 if batch else 0) else None),
                               "count_scope": "logical native requests only; internal provider retry counts and coverage are unknown"}
                    path = run_dir / "engine_calls" / (call_id + ".json")
                    atomic_json(path, receipt)
                    log.set_activity(f"{role}: waiting for {requested} native model response(s)")
                    log.event("engine_role_call_start", message=f"{role}: native {method_name}, {requested} response(s) requested",
                              call_id=call_id, role=role, requested_logical_responses=requested, receipt=str(path))
                    try:
                        result = await original(*args, **kwargs)
                    except Exception as exc:
                        receipt.update(status="failed", error=f"{type(exc).__name__}: {exc}", elapsed_seconds=time.monotonic() - started)
                        atomic_json(path, receipt)
                        log.event("engine_role_call_failed", message=f"{role}: native request failed", call_id=call_id, role=role, error=receipt["error"])
                        if required:
                            degraded(f"Requested {role} model call failed; native error handling applies", role=role, call_id=call_id)
                        raise
                    responses = result if batch else [result]
                    valid = [response for response in responses or [] if response is not None and getattr(response, "content", None)]
                    receipt.update(status="returned", elapsed_seconds=time.monotonic() - started,
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
