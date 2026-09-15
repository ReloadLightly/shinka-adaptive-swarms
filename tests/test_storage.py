import errno
import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from adaptive_swarms import storage
from adaptive_swarms.storage import GIB, MIB, StorageConfig, StorageGuard, StorageInterrupted


C_MOUNT = {"target": "/mnt/c", "source": "C:\\", "fstype": "9p",
           "options": "ro,aname=drvfs;path=C:\\;uid=1000"}


@pytest.fixture
def readings(monkeypatch):
    values = {"host": 33 * GIB, "output": 300 * GIB}
    monkeypatch.setattr(storage, "verify_windows_c_mount", lambda: C_MOUNT)
    monkeypatch.setattr(storage, "available_bytes", lambda path: values["host" if str(path) == "/mnt/c" else "output"])
    return values


def test_mount_check_accepts_windows_drvfs_and_rejects_linux_directory(monkeypatch):
    def supply(mount):
        monkeypatch.setattr(storage.subprocess, "run", lambda *a, **k: SimpleNamespace(
            stdout=json.dumps({"filesystems": [mount]})))
    original = storage.verify_windows_c_mount
    supply(C_MOUNT)
    assert original() == C_MOUNT
    supply({**C_MOUNT, "fstype": "drvfs"})
    assert original()["fstype"] == "drvfs"
    for changed in [{"target": "/", "source": "/dev/sdc", "fstype": "ext4"},
                    {**C_MOUNT, "source": "D:\\"},
                    {**C_MOUNT, "options": "aname=drvfs;path=D:\\;uid=1000"},
                    {**C_MOUNT, "fstype": "ext4"}]:
        supply(changed)
        with pytest.raises(RuntimeError, match="not verified Windows C"):
            original()


def test_host_space_is_enforced_even_when_linux_reports_hundreds_of_gib(tmp_path, readings):
    events = []
    guard = StorageGuard(tmp_path, reporter=lambda event, **fields: events.append((event, fields)))
    assert guard.check(force=True, active_workers=2)["host_free_bytes"] == 33 * GIB
    readings["host"] = 14 * GIB
    assert guard.check(force=True)["warning"]
    assert events[-1][0] == "storage_warning"
    # Space above 10 GiB is reserved for the two workers before they launch.
    readings["host"] = 10 * GIB + 100 * MIB
    with pytest.raises(StorageInterrupted):
        guard.check(force=True, activity="schedule generation 3", active_workers=2)
    record = json.loads(guard.stop_path.read_text())
    assert record["status"] == "storage_paused"
    assert record["storage"]["output_free_bytes"] == 300 * GIB
    assert record["storage"]["worker_headroom_bytes"] == 128 * MIB
    assert events[-1][0] == "storage_checkpoint"


def test_output_filesystem_is_checked_independently(tmp_path, readings):
    guard = StorageGuard(tmp_path)
    readings["output"] = GIB
    with pytest.raises(StorageInterrupted):
        guard.check(force=True)
    assert guard.last_snapshot["host_free_bytes"] == 33 * GIB


def test_pause_is_shared_and_resume_retains_completed_work(tmp_path, readings):
    completed = tmp_path / "case_000.json"
    completed.write_text('{"offline_error": 1.25}')
    first, peer = StorageGuard(tmp_path), StorageGuard(tmp_path)
    peer.check()
    readings["host"] = 9 * GIB
    with pytest.raises(StorageInterrupted):
        first.check(force=True)
    # A shared pause bypasses the peer's cached healthy free-space reading.
    with pytest.raises(StorageInterrupted):
        peer.check()
    with pytest.raises(StorageInterrupted):
        first.clear_stop_for_resume()
    readings["host"] = 33 * GIB
    first.clear_stop_for_resume(active_workers=2)
    assert first.check(force=True)["active_workers"] == 2
    assert not first.stop_path.exists()
    assert len(list(tmp_path.glob("storage-stop-*.json"))) == 1
    assert completed.read_text() == '{"offline_error": 1.25}'


def test_writes_stop_mid_file_before_further_unchecked_growth(tmp_path, readings):
    guard = StorageGuard(tmp_path)

    class ConsumingWriter(io.BytesIO):
        def write(self, data):
            result = super().write(data)
            readings["host"] = 9 * GIB
            return result
    stream = ConsumingWriter()
    with pytest.raises(StorageInterrupted):
        guard.guarded_write(stream, b"abcdefgh", chunk_size=4)
    assert stream.getvalue() == b"abcd"


def test_disk_full_latches_without_marker_retry_loop(tmp_path, readings, monkeypatch):
    guard = StorageGuard(tmp_path)
    attempts = []
    original_open = Path.open

    def no_room(path, *args, **kwargs):
        if path.name.endswith(".tmp"):
            attempts.append(path)
            raise OSError(errno.ENOSPC, "simulated full disk")
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", no_room)
    for _ in range(3):
        with pytest.raises(StorageInterrupted):
            guard.disk_full(OSError(errno.ENOSPC, "simulated"))
    assert len(attempts) == 1
    with pytest.raises(StorageInterrupted):
        guard.check()
    assert not list(tmp_path.iterdir())
    with pytest.raises(OSError) as error:
        guard.disk_full(OSError(errno.EACCES, "not a full disk"))
    assert error.value.errno == errno.EACCES


def test_env_guard_retains_worker_headroom_and_child_output_filesystem(tmp_path, readings, monkeypatch):
    monkeypatch.setenv(storage.ENV_CONFIG, "")
    assert storage.get_storage_guard() is None
    guard = StorageGuard(tmp_path, StorageConfig(worker_headroom_mib=32))
    guard.install_environment(active_workers=3)
    child = storage.get_storage_guard(tmp_path / "gen_4/results")
    assert child is storage.get_storage_guard(tmp_path / "gen_4/results")
    snapshot = child.check()
    assert snapshot["worker_headroom_bytes"] == 96 * MIB
    assert child.stop_path == guard.stop_path
    assert snapshot["output_dir"] == str(tmp_path / "gen_4/results")


def test_run_scan_is_cached_and_does_not_follow_symlinks(tmp_path, readings, monkeypatch):
    run = tmp_path / "run"
    run.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "large").write_bytes(b"x" * 100_000)
    (run / "external").symlink_to(outside, target_is_directory=True)
    (run / "case.json").write_text("{}")
    assert storage.run_storage_bytes(run) < 100_000
    calls = []
    original = storage.run_storage_bytes
    monkeypatch.setattr(storage, "run_storage_bytes", lambda path: calls.append(path) or original(path))
    guard = StorageGuard(run)
    guard.check(force=True)
    guard.check(force=True)
    assert calls == [run]


def test_storage_pause_bypasses_scientific_exception_handlers():
    caught = False
    with pytest.raises(StorageInterrupted):
        try:
            raise StorageInterrupted("operational pause")
        except Exception:
            caught = True
    assert not caught


def test_completed_case_checkpoint_is_bounded_and_checks_real_space(tmp_path, readings):
    guard = StorageGuard(tmp_path, StorageConfig(worker_headroom_mib=2))
    readings["host"] = 9 * GIB
    with pytest.raises(StorageInterrupted):
        guard.check(force=True)
    assert guard.check_checkpoint_write(0, 1024)["host_free_bytes"] == 9 * GIB
    assert guard.stopped
    with pytest.raises(StorageInterrupted, match="allowance"):
        guard.check_checkpoint_write(2 * MIB, 1)
    readings["host"] = MIB
    with pytest.raises(StorageInterrupted, match="Insufficient real space"):
        guard.check_checkpoint_write(0, 1024)
