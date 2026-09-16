"""Crash attachment and progress races, without research or language-model calls."""
from __future__ import annotations

import fcntl
import importlib.util
import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = {"sha256": "frozen-engine", "default_model": "gpt-6-astra", "default_effort": None,
          "evolution": {"embedding_model": "local/test@http://127.0.0.1:8910/v1"}}


def module():
    spec = importlib.util.spec_from_file_location("joint_search_supervisor_test", ROOT / "scripts/run_joint_searches.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def command(folder, profile, seed=610001):
    return ["python", "-u", str(ROOT / "scripts/run_evolution.py"), "--task", "joint_relocation_v3",
            "--generations", "30", "--search-seed", str(seed), "--run-dir", str(folder),
            "--model", "gpt-6-astra", "--embedding-model", ENGINE["evolution"]["embedding_model"],
            "--engine-profile", str(profile)]


def fake_process(tmp_path, pid, args, start="100", state="S"):
    proc = tmp_path / "proc" / str(pid)
    proc.mkdir(parents=True, exist_ok=True)
    fields = [state] + ["0"] * 18 + [start]
    (proc / "stat").write_text(f"{pid} (python worker) " + " ".join(fields))
    (proc / "cmdline").write_bytes(("\0".join(args) + "\0").encode())
    (proc / "cwd").symlink_to(ROOT, target_is_directory=True)
    return tmp_path / "proc"


def test_surviving_native_flock_and_exact_command_attach_without_mutating_lock(tmp_path):
    supervisor = module()
    folder = tmp_path / "evolution/search_0"
    folder.parent.mkdir()
    profile = tmp_path / "profile.json"
    proc = fake_process(tmp_path, 123, command(folder, profile))
    lockpath = folder.parent / ".controller.lock"
    with lockpath.open("w+") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        stream.write("123")
        stream.flush()
        record = supervisor.surviving_controller(folder, 610001, ENGINE, profile, recorded_pid=123, proc_root=proc)
        assert record["pid"] == 123 and record["native_lock_held"]
        assert record["start_ticks"] == "100"
        assert lockpath.read_text() == "123"


def test_unrelated_native_controller_is_preserved(tmp_path):
    supervisor = module()
    folder = tmp_path / "evolution/search_0"
    folder.parent.mkdir()
    profile = tmp_path / "profile.json"
    proc = fake_process(tmp_path, 456, command(tmp_path / "unrelated", profile))
    lockpath = folder.parent / ".controller.lock"
    with lockpath.open("w+") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        stream.write("456")
        stream.flush()
        with pytest.raises(RuntimeError, match="unrelated or unverifiable"):
            supervisor.surviving_controller(folder, 610001, ENGINE, profile, proc_root=proc)
        assert lockpath.read_text() == "456"
        assert (proc / "456/cmdline").exists()


def test_recorded_exact_child_attaches_during_prelock_startup(tmp_path):
    supervisor = module()
    folder, profile = tmp_path / "search_0", tmp_path / "profile.json"
    proc = fake_process(tmp_path, 123, command(folder, profile))
    record = supervisor.surviving_controller(folder, 610001, ENGINE, profile, recorded_pid=123, proc_root=proc)
    assert record["pid"] == 123 and not record["native_lock_held"]
    # Reused PIDs belonging to unrelated commands do not authorize attachment.
    (proc / "123/cmdline").write_bytes(b"python\0some_other_script.py\0")
    assert supervisor.surviving_controller(folder, 610001, ENGINE, profile, recorded_pid=123, proc_root=proc) is None


@pytest.mark.parametrize("field,replacement", [("--generations", "31"), ("--search-seed", "610002"),
    ("--task", "relocation_allocation_v2"), ("--model", "different-model"),
    ("--embedding-model", "local/other@http://127.0.0.1:8910/v1")])
def test_attachment_rejects_changed_registered_scientific_settings(tmp_path, field, replacement):
    supervisor = module()
    folder, profile = tmp_path / "search", tmp_path / "profile.json"
    args = command(folder, profile)
    args[args.index(field) + 1] = replacement
    record = {"command": args, "cwd": ROOT}
    assert not supervisor.matches_native_process(record, folder, 610001, ENGINE, profile)


@pytest.mark.parametrize("message", ["no such table: programs", "database is locked",
                                    "database table is locked: programs", "database schema is locked: main"])
def test_only_transient_sqlite_progress_races_are_deferred(tmp_path, monkeypatch, message):
    supervisor = module()
    (tmp_path / "programs.sqlite").touch()
    def fail(folder):
        raise sqlite3.OperationalError(message)
    monkeypatch.setattr(supervisor, "summarize_database", fail)
    assert supervisor.progress_summary(tmp_path) == (None, message)


@pytest.mark.parametrize("error", [sqlite3.OperationalError("disk I/O error"),
                                  sqlite3.DatabaseError("database disk image is malformed")])
def test_genuine_sqlite_errors_are_not_hidden(tmp_path, monkeypatch, error):
    supervisor = module()
    (tmp_path / "programs.sqlite").touch()
    def fail(folder):
        raise error
    monkeypatch.setattr(supervisor, "summarize_database", fail)
    with pytest.raises(type(error), match=str(error)):
        supervisor.progress_summary(tmp_path)


def test_monitor_survives_initialization_race_and_observes_new_progress(tmp_path, monkeypatch):
    supervisor = module()
    polls = iter([None, None, 0])
    child = SimpleNamespace(poll=lambda: next(polls), returncode=0)
    readings = iter([(None, "no such table: programs"), ({"terminal_slots": 1, "valid_descendants": 0}, None)])
    monkeypatch.setattr(supervisor, "progress_summary", lambda folder: next(readings))
    waits = []
    monkeypatch.setattr(supervisor.time, "sleep", waits.append)
    events = []
    log = SimpleNamespace(event=lambda event, **fields: events.append(event))
    assert supervisor.monitor_controller(tmp_path, 0, 610001, {"pid": 123}, log, child=child) == 0
    assert waits == [20, 20]
    assert events == ["search_progress_temporarily_unavailable", "search_checkpoint_progress"]


def test_attached_monitor_stops_on_pid_reuse_without_signaling_process(tmp_path, monkeypatch):
    supervisor = module()
    monkeypatch.setattr(supervisor, "process_record", lambda pid: {"start_ticks": "new"})
    monkeypatch.setattr(supervisor, "progress_summary", lambda folder: pytest.fail("Reused process must not be monitored"))
    assert supervisor.monitor_controller(tmp_path, 0, 610001, {"pid": 123, "start_ticks": "old"}, None) is None


def prepare_campaign(tmp_path, monkeypatch, supervisor, statuses):
    study, operations = tmp_path / "study", tmp_path / "operations"
    study.mkdir()
    operations.mkdir()
    profile, engine = tmp_path / "profile.json", tmp_path / "engine.json"
    profile.write_text("{}")
    engine.write_text(json.dumps(ENGINE))
    searches = [{"search_index": index, "search_seed": 610001 + index,
                 "run": str(tmp_path / "evolution" / f"search_{index}")} for index in range(3)]
    (study / "registration.json").write_text(json.dumps({"searches": searches, "engine_config": ENGINE}))
    for item, status in zip(searches, statuses):
        if status is None:
            continue
        folder = Path(item["run"])
        folder.mkdir(parents=True)
        (folder / "programs.sqlite").touch()
        (folder / "manifest.json").write_text(json.dumps({"task": "joint_relocation_v3",
            "search_seed": item["search_seed"], "generation_target": 30, "engine_config": ENGINE, "status": status}))
    monkeypatch.setattr(supervisor, "resolve_engine", lambda **kwargs: ENGINE)
    monkeypatch.setattr("sys.argv", ["run_joint_searches.py", "--run", str(study),
        "--engine-config", str(engine), "--engine-profile", str(profile), "--operations", str(operations)])
    return study, operations, searches


def test_recovered_supervisor_attaches_without_launch_and_skips_verified_completions(tmp_path, monkeypatch):
    supervisor = module()
    study, operations, searches = prepare_campaign(tmp_path, monkeypatch, supervisor,
                                                  ["search_complete", "preflight", "search_complete"])
    (operations / "manifest.json").write_text(json.dumps({"study": str(study), "engine_config_sha256": ENGINE["sha256"],
        "searches": searches, "active_run": searches[1]["run"], "child_pid": 321}))
    monkeypatch.setattr(supervisor, "summarize_database", lambda folder: {"terminal_generation_ids": list(range(30)), "valid_seed": True})
    monkeypatch.setattr(supervisor.subprocess, "Popen", lambda *args, **kwargs: pytest.fail("Surviving native child must not be relaunched"))
    def survivor(folder, seed, engine, profile, recorded_pid):
        assert str(folder) == searches[1]["run"] and recorded_pid == 321
        return {"pid": 321, "start_ticks": "100", "command": command(folder, profile, seed), "native_lock_held": True}
    monkeypatch.setattr(supervisor, "surviving_controller", survivor)
    def monitor(folder, index, seed, record, log, child):
        assert child is None and record["pid"] == 321
        saved = json.loads((folder / "manifest.json").read_text())
        saved["status"] = "search_complete"
        (folder / "manifest.json").write_text(json.dumps(saved))
        return None
    monkeypatch.setattr(supervisor, "monitor_controller", monitor)
    supervisor.main()
    result = json.loads((operations / "manifest.json").read_text())
    assert result["status"] == "searches_complete"
    assert len(result["completed_searches"]) == 3
    events = [json.loads(line)["event"] for line in (operations / "events.jsonl").read_text().splitlines()]
    assert events.count("search_reused") == 2 and events.count("search_controller_attached") == 1


def test_new_child_detaches_and_survives_supervisor_progress_failure(tmp_path, monkeypatch):
    supervisor = module()
    _, operations, _ = prepare_campaign(tmp_path, monkeypatch, supervisor, [None, None, None])
    monkeypatch.setattr(supervisor, "surviving_controller", lambda *args, **kwargs: None)
    captured = []
    def launch(args, **kwargs):
        captured.append((args, kwargs))
        return SimpleNamespace(pid=777)
    monkeypatch.setattr(supervisor.subprocess, "Popen", launch)
    def fail(*args, **kwargs):
        raise sqlite3.DatabaseError("database disk image is malformed")
    monkeypatch.setattr(supervisor, "monitor_controller", fail)
    with pytest.raises(sqlite3.DatabaseError, match="malformed"):
        supervisor.main()
    assert len(captured) == 1
    assert captured[0][1]["start_new_session"] and captured[0][1]["close_fds"]
    result = json.loads((operations / "manifest.json").read_text())
    assert result["status"] == "interrupted_or_failed" and result["child_pid"] == 777
    assert "malformed" in result["error"]
