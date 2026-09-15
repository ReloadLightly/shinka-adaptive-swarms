"""Project-local host/output storage checks and a shared, latched pause signal.

The Windows host check intentionally uses the verified C: mount. WSL ext4 free
space cannot establish how much room remains for its expanding VHDX on C:.
Nothing here changes optimizer configuration or interprets a pause as fitness.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import errno
import json
import os
from pathlib import Path
import re
import subprocess
import threading
import time
from typing import Callable

GIB = 1024 ** 3
MIB = 1024 ** 2
ENV_CONFIG = "ADAPTIVE_SWARMS_STORAGE_CONFIG"
DISK_FULL_ERRNOS = {errno.ENOSPC, errno.EDQUOT}


class StorageInterrupted(BaseException):
    """A resumable operational pause; bypass candidate-failure Exception handlers."""


@dataclass(frozen=True)
class StorageConfig:
    warn_gib: float = 15.0
    checkpoint_gib: float = 10.0
    output_checkpoint_gib: float = 1.0
    worker_headroom_mib: float = 64.0
    check_interval_seconds: float = 5.0
    report_interval_seconds: float = 20.0
    scan_interval_seconds: float = 60.0

    def __post_init__(self):
        values = asdict(self)
        if any(not isinstance(v, (int, float)) or not 0 <= v < float("inf") for v in values.values()):
            raise ValueError("Storage settings must be finite nonnegative numbers")
        if self.warn_gib < self.checkpoint_gib:
            raise ValueError("Storage warning threshold must be at least the checkpoint threshold")
        if self.check_interval_seconds <= 0 or self.scan_interval_seconds <= 0:
            raise ValueError("Storage check and scan intervals must be positive")

    def as_dict(self):
        return asdict(self)


def verify_windows_c_mount() -> dict:
    """Reject an absent mount, a normal Linux /mnt/c directory, or another drive."""
    try:
        result = subprocess.run(
            ["findmnt", "--json", "--target", "/mnt/c", "--output", "TARGET,SOURCE,FSTYPE,OPTIONS"],
            capture_output=True, text=True, check=True, timeout=10,
        )
        mounts = json.loads(result.stdout)["filesystems"]
        mount = mounts[0]
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, IndexError) as exc:
        raise RuntimeError("Cannot verify /mnt/c as the mounted Windows C: drive") from exc
    target = str(mount.get("target", ""))
    source = str(mount.get("source", "")).rstrip("\\/").upper()
    fs = str(mount.get("fstype", "")).lower()
    options = str(mount.get("options", ""))
    is_drvfs = fs == "drvfs" or (
        fs == "9p" and "aname=drvfs" in options
        and re.search(r"(?:^|[;,])path=C:[\\/](?:[;,]|$)", options, re.I) is not None
    )
    if target != "/mnt/c" or source != "C:" or not is_drvfs:
        raise RuntimeError(f"/mnt/c is not verified Windows C: (target={target!r}, source={source!r}, fstype={fs!r})")
    return mount


def available_bytes(path: Path | str) -> int:
    """Space available to this user on the actual filesystem containing path."""
    path = Path(path)
    while not path.exists():
        parent = path.parent
        if parent == path:
            raise FileNotFoundError(path)
        path = parent
    info = os.statvfs(path)
    return info.f_bavail * info.f_frsize


def run_storage_bytes(run_dir: Path) -> int:
    """Allocated bytes in only this run; skip symlinks and tolerate atomic renames."""
    size = 0
    for folder, directories, files in os.walk(run_dir, followlinks=False):
        directories[:] = [name for name in directories if not (Path(folder) / name).is_symlink()]
        for name in files:
            path = Path(folder) / name
            try:
                if not path.is_symlink():
                    stat = path.stat()
                    size += getattr(stat, "st_blocks", (stat.st_size + 511) // 512) * 512
            except FileNotFoundError:
                pass
    return size


class StorageGuard:
    """Shared stop marker plus cheap periodic space checks and infrequent run scans.

    The 64 MiB default per active worker is project output headroom, added to
    both checkpoint floors. It covers multiple compressed case files and a
    small native checkpoint, while chunked writers and worker cancellation
    provide enforcement. It is configurable and is not a RAM restriction.
    """

    def __init__(self, run_dir: Path | str, config: StorageConfig | None = None,
                 reporter: Callable | None = None, *, output_dir: Path | str | None = None):
        self.run_dir = Path(run_dir).resolve()
        self.output_dir = Path(output_dir or run_dir).resolve()
        self.config = config or StorageConfig()
        self.reporter = reporter
        self.stop_path = self.run_dir / "storage-stop.json"
        self.stopped = False
        self.last_snapshot: dict | None = None
        self._lock = threading.RLock()
        self._mount = None
        self._last_check = self._last_report = self._last_scan = float("-inf")
        self._initial_bytes = None
        self._run_bytes = 0
        self._active_workers = 1
        self._last_warning = None
        self._stop_record_attempted = False
        self.checkpoint_write_active = False

    def install_environment(self, active_workers: int | None = None):
        """Make evaluator subprocesses use the same limits and shared stop path."""
        payload = {"run_dir": str(self.run_dir), "config": self.config.as_dict(),
                   "active_workers": self._active_workers if active_workers is None else active_workers}
        os.environ[ENV_CONFIG] = json.dumps(payload, separators=(",", ":"))
        return payload

    def _report(self, event: str, **fields):
        try:
            if self.reporter is not None:
                self.reporter(event, **fields)
            else:
                stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
                print(f"[{stamp}] {event}: " + " ".join(f"{key}={value}" for key, value in fields.items()), flush=True)
        except OSError as exc:
            if exc.errno not in DISK_FULL_ERRNOS:
                raise
            self.request_stop("disk_full_while_reporting", error=str(exc))
            raise StorageInterrupted("Storage full while recording progress") from exc

    def request_stop(self, reason: str = "storage_checkpoint_requested", **details):
        """Latch exactly one pause; attempt one small atomic marker write, no retry."""
        with self._lock:
            self.stopped = True
            record = {"status": "storage_paused", "reason": reason,
                      "time": datetime.now(timezone.utc).isoformat(),
                      "run_dir": str(self.run_dir), "storage": self.last_snapshot,
                      **details}
            if self._stop_record_attempted or self.stop_path.exists():
                return record
            self._stop_record_attempted = True
            temporary = self.stop_path.with_name(f".{self.stop_path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
            try:
                self.run_dir.mkdir(parents=True, exist_ok=True)
                with temporary.open("x", encoding="utf-8") as stream:
                    json.dump(record, stream, indent=2, default=str)
                    stream.write("\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                temporary.replace(self.stop_path)
            except OSError as exc:
                # ENOSPC can make even a marker impossible. The in-memory latch
                # still stops scheduling; completed case/native checkpoints stay.
                if exc.errno not in DISK_FULL_ERRNOS:
                    raise
            finally:
                # Only this invocation's incomplete marker is disposable.
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
            return record

    def check(self, force: bool = False, activity: str = "storage check",
              active_workers: int | None = None, *, ignore_stop: bool = False) -> dict:
        """Check before scheduling (force=True), on writer chunks and periodically.

        active_workers must include work about to launch, so concurrent workers'
        completion/checkpoint headroom is reserved before that launch.
        ignore_stop is only for checking whether an explicit resume is possible;
        it never removes the previous interruption record.
        """
        with self._lock:
            if not ignore_stop and (self.stopped or self.stop_path.exists()):
                self.stopped = True
                raise StorageInterrupted(f"Storage pause requested; checkpoint: {self.stop_path}")
            if active_workers is not None:
                if active_workers < 0:
                    raise ValueError("active_workers must be nonnegative")
                if active_workers != self._active_workers:
                    force = True
                self._active_workers = active_workers
            now = time.monotonic()
            if not force and now - self._last_check < self.config.check_interval_seconds:
                return self.last_snapshot or {}
            if self._mount is None:
                self._mount = verify_windows_c_mount()
            host_free = available_bytes("/mnt/c")
            output_free = available_bytes(self.output_dir)
            self._last_check = now
            if now - self._last_scan >= self.config.scan_interval_seconds:
                self._run_bytes = run_storage_bytes(self.run_dir)
                self._last_scan = now
                if self._initial_bytes is None:
                    self._initial_bytes = self._run_bytes
            reserve = self._active_workers * self.config.worker_headroom_mib * MIB
            host_floor = self.config.checkpoint_gib * GIB + reserve
            output_floor = self.config.output_checkpoint_gib * GIB + reserve
            warning = host_free <= self.config.warn_gib * GIB
            snapshot = {"host_mount": self._mount, "host_free_bytes": host_free,
                        "output_free_bytes": output_free, "output_dir": str(self.output_dir),
                        "run_bytes": self._run_bytes,
                        "run_growth_bytes": self._run_bytes - (self._initial_bytes or 0),
                        "growth_sample_age_s": round(now - self._last_scan, 3),
                        "active_workers": self._active_workers,
                        "worker_headroom_bytes": int(reserve),
                        "effective_host_checkpoint_bytes": int(host_floor),
                        "effective_output_checkpoint_bytes": int(output_floor),
                        "warning": warning, "activity": activity,
                        "settings": self.config.as_dict()}
            self.last_snapshot = snapshot
            low = host_free <= host_floor or output_free <= output_floor
            if low:
                self.request_stop("low_storage", activity=activity)
            if low or now - self._last_report >= self.config.report_interval_seconds or warning != self._last_warning:
                self._last_report = now
                self._last_warning = warning
                self._report("storage_checkpoint" if low else ("storage_warning" if warning else "storage_status"),
                             activity=activity, host_free_gib=round(host_free / GIB, 3),
                             output_free_gib=round(output_free / GIB, 3),
                             run_growth_mib=round(snapshot["run_growth_bytes"] / MIB, 3),
                             growth_sample_age_s=snapshot["growth_sample_age_s"],
                             active_workers=self._active_workers,
                             host_checkpoint_gib=round(host_floor / GIB, 3),
                             output_checkpoint_gib=round(output_floor / GIB, 3))
            if low:
                raise StorageInterrupted(f"Storage checkpoint required during {activity}; checkpoint: {self.stop_path}")
            return snapshot

    def clear_stop_for_resume(self, active_workers: int = 1):
        """Check real free space then retain the old marker as resume evidence."""
        snapshot = self.check(force=True, activity="resume storage preflight", active_workers=active_workers,
                              ignore_stop=True)
        if self.stop_path.exists():
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
            self.stop_path.replace(self.stop_path.with_name(f"storage-stop-{stamp}.json"))
        self.stopped = False
        self._stop_record_attempted = False
        return snapshot

    def disk_full(self, exc: OSError, activity: str = "writing output"):
        if exc.errno not in DISK_FULL_ERRNOS:
            raise exc
        self.request_stop("disk_full", activity=activity, error=str(exc))
        raise StorageInterrupted(f"Disk full during {activity}; completed checkpoints retained") from exc

    def check_checkpoint_write(self, bytes_written: int, next_bytes: int,
                               activity: str = "saving completed case") -> dict:
        """Permit one bounded completed-case save after the shared pause latch.

        A completed objective budget is scientific evidence worth finishing. The
        writer supplies its cumulative *uncompressed* byte count (conservative
        for gzip), bounded by one worker's declared storage headroom. Fresh host
        and output checks still run for every chunk; at least 1 MiB remains for
        the small status/checkpoint records. This never authorizes another case.
        """
        maximum = int(self.config.worker_headroom_mib * MIB)
        if bytes_written < 0 or next_bytes < 0 or bytes_written + next_bytes > maximum:
            self.request_stop("completed_case_checkpoint_allowance_exhausted", activity=activity,
                              bytes_written=bytes_written, next_bytes=next_bytes, allowance_bytes=maximum)
            raise StorageInterrupted("Completed case exceeds its bounded storage checkpoint allowance")
        try:
            snapshot = self.check(force=True, activity=activity, ignore_stop=True)
        except StorageInterrupted:
            snapshot = self.last_snapshot
        if snapshot is None:
            raise StorageInterrupted("Cannot verify space for a completed-case checkpoint")
        # Keep a small margin for the gzip trailer, metadata and atomic rename;
        # concurrent writers must each retain a full next chunk as well.
        needed = MIB + next_bytes * max(1, self._active_workers)
        if min(snapshot["host_free_bytes"], snapshot["output_free_bytes"]) <= needed:
            self.request_stop("insufficient_checkpoint_space", activity=activity, required_bytes=needed)
            raise StorageInterrupted("Insufficient real space to finish the completed-case checkpoint")
        return snapshot

    def guarded_write(self, stream, data, activity: str = "writing output", chunk_size: int = MIB):
        """Bound unchecked writes; use with binary or text streams, including gzip."""
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        try:
            for start in range(0, len(data), chunk_size):
                self.check(force=True, activity=activity)
                stream.write(data[start:start + chunk_size])
        except OSError as exc:
            self.disk_full(exc, activity=activity)


_ENV_GUARDS: dict[tuple[str, str], StorageGuard] = {}


def get_storage_guard(output_dir: Path | str | None = None) -> StorageGuard | None:
    """Return the launcher-configured guard in evaluator children; opt-in elsewhere."""
    raw = os.environ.get(ENV_CONFIG)
    if not raw:
        return None
    payload = json.loads(raw)
    output = str(Path(output_dir or payload["run_dir"]).resolve())
    key = (raw, output)
    if key not in _ENV_GUARDS:
        _ENV_GUARDS[key] = StorageGuard(payload["run_dir"], StorageConfig(**payload["config"]), output_dir=output)
        _ENV_GUARDS[key]._active_workers = payload.get("active_workers", 1)
    return _ENV_GUARDS[key]
