"""Optional run-local response allowance, using native call receipts as its ledger.

No limit is active unless explicitly supplied to the launcher. Initial batch
responses are reserved together; exposed native-client retries reserve one more
response before dispatch. Unobserved provider retries are outside this count.
"""
from __future__ import annotations

from contextvars import ContextVar
from datetime import datetime, timezone
import json
from pathlib import Path
import threading

from .execution import InfrastructureError
from .logging import atomic_json


class SprintLimitReached(InfrastructureError):
    """Operational stop, never a candidate fitness or terminal failed slot."""


native_request_context = ContextVar("adaptive_swarms_native_request", default=None)


class LogicalResponseBudget:
    def __init__(self, run_dir: Path, limit: int, *, session_limit=None, session_start=None):
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("Logical response limit must be a positive integer.")
        self.run_dir, self.limit = Path(run_dir), limit
        self.session_limit = session_limit
        self._lock = threading.RLock()
        self.used = 0
        for path in (self.run_dir / "engine_calls").glob("*.json"):
            value = json.loads(path.read_text())["requested_logical_responses"]
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"Malformed response reservation in {path}")
            self.used += value
        self.session_start = self.used if session_start is None else int(session_start)
        if self.session_start < 0 or self.session_start > self.used or (session_limit is not None and session_limit < 1):
            raise ValueError("Invalid session response ledger boundary")
        if self.used > limit:
            raise ValueError(f"Existing receipts already reserve {self.used} responses, above limit {limit}.")

    def reserve(self, path, receipt, count, *, retry=False):
        """Persist the reservation before any model submission can begin."""
        if isinstance(count, bool) or not isinstance(count, int) or count < 1:
            raise ValueError("Native response count must be a positive integer.")
        with self._lock:
            session_exceeded = self.session_limit is not None and self.used + count - self.session_start > self.session_limit
            if self.used + count > self.limit or session_exceeded:
                record = {"status": "sprint_limit_reached", "time": datetime.now(timezone.utc).isoformat(),
                          "logical_response_limit": self.limit, "reserved_logical_responses": self.used,
                          "session_response_limit": self.session_limit, "session_start_responses": self.session_start,
                          "declined_responses": count, "declined_role": receipt["role"],
                          "declined_call_id": receipt["call_id"], "declined_native_retry": retry,
                          "scientific_failure": False,
                          "scope": "This run only; completed records and checkpoints are retained. No declined model call was submitted."}
                atomic_json(self.run_dir / "sprint-stop.json", record)
                raise SprintLimitReached(f"Run-local model allowance: {self.used}/{self.limit} reserved; "
                                         f"next {receipt['role']} request needs {count} more; "
                                         f"session used={self.used - self.session_start}/{self.session_limit}.")
            if retry:
                receipt["requested_logical_responses"] += count
                receipt["exposed_native_retry_responses"] += count
            else:
                receipt["initial_logical_responses"] = count
                receipt["exposed_native_retry_responses"] = 0
                receipt["native_dispatch_attempts"] = []
                receipt["reservation_scope"] = "Full initial batch plus exposed native-client retries; started reservations survive crashes; hidden provider retries unknown."
            receipt["logical_response_limit"] = self.limit
            if self.session_limit is not None:
                receipt["session_response_limit"] = self.session_limit
                receipt["session_start_responses"] = self.session_start
            receipt["run_reserved_logical_responses_at_reservation"] = self.used + count
            atomic_json(path, receipt)
            self.used += count


def install_native_retry_observer(budget, stop):
    """Observe pinned native retries without altering their selection or timing."""
    from shinka.llm import llm
    original = llm.query_async

    async def observed(*args, **kwargs):
        context = native_request_context.get()
        if context is None:
            return await original(*args, **kwargs)
        receipt, path = context
        attempts = receipt["native_dispatch_attempts"]
        if len(attempts) >= receipt["initial_logical_responses"]:
            try:
                budget.reserve(path, receipt, 1, retry=True)
            except SprintLimitReached as exc:
                stop(exc)
                raise
        attempt = {"index": len(attempts) + 1, "started_at": datetime.now(timezone.utc).isoformat(),
                   "model_name": kwargs.get("model_name"), "status": "started"}
        attempts.append(attempt)
        atomic_json(path, receipt)
        try:
            result = await original(*args, **kwargs)
        except BaseException as exc:
            attempt.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            raise
        else:
            attempt["status"] = "returned"
            return result
        finally:
            attempt["finished_at"] = datetime.now(timezone.utc).isoformat()
            atomic_json(path, receipt)

    llm.query_async = observed
    return lambda: setattr(llm, "query_async", original)
