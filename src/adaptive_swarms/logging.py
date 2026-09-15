"""Flushed human and JSONL logs, with honest heartbeat messages during long work."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import threading
import time


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

    def __enter__(self):
        self._thread.start()
        return self

    def set_activity(self, message):
        with self._lock:
            self._activity = message

    def event(self, event, **fields):
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._lock:
            record = {"time": now, "elapsed_s": round(time.monotonic()-self._start, 2),
                      "event": event, **fields}
            self._json.write(json.dumps(record, default=str, allow_nan=False) + "\n")
            self._json.flush()
            details = " ".join(f"{k}={v:.5g}" if isinstance(v, float) else f"{k}={v}"
                               for k, v in fields.items())
            line = f"[{now}] +{record['elapsed_s']:8.1f}s {event}: {details}"
            print(line, flush=True)
            self._human.write(line + "\n")
            self._human.flush()
            if event != "heartbeat":
                self._last = time.monotonic()

    def _heartbeat(self):
        while not self._stop.wait(self._interval):
            with self._lock:
                idle = time.monotonic()-self._last
                activity = self._activity
            if idle >= self._interval:
                self.event("heartbeat", activity=activity, seconds_since_event=round(idle, 1),
                           message="Process is alive; no new result has arrived.")

    def __exit__(self, exc_type, exc, tb):
        if exc:
            self.event("interrupted" if isinstance(exc, KeyboardInterrupt) else "failed",
                       error=f"{type(exc).__name__}: {exc}")
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=2)
        self._json.close()
        self._human.close()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)
