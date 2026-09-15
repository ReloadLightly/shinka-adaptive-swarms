"""Flushed human and JSONL logs, with honest heartbeat messages during long work."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import threading
import time
import os
import sys
import traceback

from .execution import InfrastructureError


class EventLogger:
    def __init__(self, run_dir, heartbeat_seconds=20):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self._json = (self.run_dir / "events.jsonl").open("a", buffering=1)
        self._human = (self.run_dir / "run.log").open("a", buffering=1)
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._start = time.monotonic()
        self._last = self._start
        self._activity = "initializing"
        self._interval = heartbeat_seconds
        self._thread = threading.Thread(target=self._heartbeat, daemon=True)
        self._io_error = None
        self.on_io_error = None

    def __enter__(self):
        self._thread.start()
        return self

    def set_activity(self, message):
        with self._lock:
            self._activity = message

    def _check_io_error(self):
        if self._io_error is not None:
            raise self._io_error from self._io_error.__cause__

    def _fail_io(self, exc):
        if self._io_error is None:
            self._io_error = InfrastructureError(f"Event log I/O failure: {exc}")
            self._io_error.__cause__ = exc
            if self.on_io_error is not None:
                self.on_io_error(self._io_error)
        self._check_io_error()

    def event(self, event, **fields):
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._lock:
            self._check_io_error()
            record = {"time": now, "elapsed_s": round(time.monotonic()-self._start, 2),
                      "event": event, **fields}
            details = " ".join(f"{k}={v:.5g}" if isinstance(v, float) else f"{k}={v}"
                               for k, v in fields.items())
            line = f"[{now}] +{record['elapsed_s']:8.1f}s {event}: {details}"
            try:
                print(line, flush=True)
                self._json.write(json.dumps(record, default=str, allow_nan=False) + "\n")
                self._json.flush()
                self._human.write(line + "\n")
                self._human.flush()
            except OSError as exc:
                self._fail_io(exc)
            if event != "heartbeat":
                self._last = time.monotonic()

    def _heartbeat(self):
        while not self._stop.wait(self._interval):
            with self._lock:
                idle = time.monotonic()-self._last
                activity = self._activity
            if idle >= self._interval:
                try:
                    self.event("heartbeat", activity=activity, seconds_since_event=round(idle, 1),
                               message="Process is alive; no new result has arrived.")
                except InfrastructureError:
                    # Thread failures remain visible and are raised by the next
                    # foreground event or context exit, even if space recovers.
                    traceback.print_exc(file=sys.stderr)
                    sys.stderr.flush()
                    return

    def __exit__(self, exc_type, exc, tb):
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=2)
        try:
            self._check_io_error()
            if exc:
                self.event("interrupted" if isinstance(exc, KeyboardInterrupt) else "failed",
                           error=f"{type(exc).__name__}: {exc}")
        finally:
            try:
                self._json.close()
            finally:
                self._human.close()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    try:
        with temporary.open("w") as stream:
            json.dump(value, stream, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
