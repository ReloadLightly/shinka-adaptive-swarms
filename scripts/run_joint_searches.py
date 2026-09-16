#!/usr/bin/env python3
"""Run the three registered native V3 searches sequentially and recover saved work.

This supervisor never chooses parents, mutations, novelty decisions or winners.
It starts the native launcher with the frozen profile and preserves its outputs.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from adaptive_swarms.logging import EventLogger, atomic_json
from adaptive_swarms.engine_config import resolve_engine
from run_evolution import summarize_database


def process_record(pid, proc_root=Path("/proc")):
    """Read process identity without signaling it; start ticks protect PID reuse."""
    try:
        folder = proc_root / str(int(pid))
        fields = (folder / "stat").read_text().rsplit(")", 1)[1].split()
        command = (folder / "cmdline").read_bytes().decode().rstrip("\0").split("\0")
        if fields[0] == "Z" or not command or command == [""]:
            return None
        return {"pid": int(pid), "start_ticks": fields[19], "command": command,
                "cwd": (folder / "cwd").resolve()}
    except (FileNotFoundError, ProcessLookupError):
        return None


def matches_native_process(record, folder, seed, engine, profile):
    if record is None:
        return False
    command, cwd = record["command"], record["cwd"]

    def option(name):
        indexes = [i for i, value in enumerate(command) if value == name]
        return command[indexes[0] + 1] if len(indexes) == 1 and indexes[0] + 1 < len(command) else None

    def path(value):
        return (cwd / value).resolve() if value is not None else None

    script = ROOT / "scripts/run_evolution.py"
    if not any(path(value) == script for value in command[1:] if value.endswith("run_evolution.py")):
        return False
    destinations = [option(name) for name in ("--run-dir", "--resume") if option(name) is not None]
    return (len(destinations) == 1 and path(destinations[0]) == folder.resolve()
            and option("--task") == "joint_relocation_v3"
            and option("--generations") == "30" and option("--search-seed") == str(seed)
            and option("--model") == engine["default_model"]
            and option("--effort") == engine["default_effort"]
            and option("--embedding-model") == engine["evolution"]["embedding_model"]
            and path(option("--engine-profile")) == profile.resolve())


def native_lock_owner(folder):
    """Return a held native lock's recorded PID, leaving its content unchanged."""
    path = folder.parent / ".controller.lock"
    try:
        with path.open("r+") as stream:
            try:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                value = stream.read().strip()
                if not value.isdigit():
                    raise RuntimeError(f"Native controller lock is held but its PID is not readable: {path}")
                return int(value)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
                return None
    except FileNotFoundError:
        return None


def surviving_controller(folder, seed, engine, profile, recorded_pid=None, proc_root=Path("/proc")):
    owner = native_lock_owner(folder)
    if owner is not None:
        record = process_record(owner, proc_root)
        if not matches_native_process(record, folder, seed, engine, profile):
            raise RuntimeError(f"Native lock belongs to an unrelated or unverifiable controller PID {owner}; preserved")
        return {**record, "native_lock_held": True}
    if recorded_pid is not None:
        record = process_record(recorded_pid, proc_root)
        if matches_native_process(record, folder, seed, engine, profile):
            # The child may be between Popen and lock acquisition, or releasing
            # its lock after completion. An exact live command is never repeated.
            return {**record, "native_lock_held": False}
    return None


def progress_summary(folder):
    if not (folder / "programs.sqlite").exists():
        return None, None
    try:
        return summarize_database(folder), None
    except sqlite3.OperationalError as exc:
        message = str(exc).lower()
        if message.startswith("no such table:") or message in {"database is locked", "database table is locked", "database schema is locked"} or message.startswith(("database table is locked:", "database schema is locked:")):
            return None, str(exc)
        raise


def monitor_controller(folder, index, seed, record, log, child=None, interval=20):
    previous, previous_error = None, None
    while True:
        if child is not None:
            if child.poll() is not None:
                return child.returncode
        else:
            current = process_record(record["pid"])
            if current is None or current["start_ticks"] != record["start_ticks"]:
                return None  # An attached orphan's exit status is not available.
        summary, error = progress_summary(folder)
        if error != previous_error:
            previous_error = error
            if error:
                log.event("search_progress_temporarily_unavailable", search_index=index,
                          search_seed=seed, error=error, message="Native child remains attached; waiting for readable SQLite progress")
        if summary is not None:
            signature = (summary.get("terminal_slots"), summary.get("valid_descendants"),
                         len(list(folder.glob("gen_*/results/case_*.json.gz"))))
            if signature != previous:
                previous = signature
                log.event("search_checkpoint_progress", search_index=index, search_seed=seed,
                          terminal_slots=signature[0], valid_descendants=signature[1],
                          completed_case_checkpoints=signature[2], saved_path=str(folder))
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True, help="Registered study directory")
    parser.add_argument("--engine-config", type=Path, required=True, help="Frozen resolved engine JSON")
    parser.add_argument("--engine-profile", type=Path, default=ROOT / "configs/shinka/research_v3.json")
    parser.add_argument("--operations", type=Path, default=ROOT / "results/joint_relocation_v3/operations")
    args = parser.parse_args()
    study = args.run.resolve()
    registered = json.loads((study / "registration.json").read_text())
    raw_engine = json.loads(args.engine_config.read_text())
    engine = raw_engine.get("engine_config", raw_engine)
    resolved = resolve_engine(profile_path=args.engine_profile,
                              model=engine["default_model"], effort=engine["default_effort"],
                              embedding_model=engine["evolution"]["embedding_model"])
    if resolved != engine:
        raise ValueError("Current profile differs from the prospective resolved settings")
    searches = registered["searches"]
    if registered["engine_config"] != engine:
        raise ValueError("Registered engine differs from supplied frozen configuration")
    if [item["search_index"] for item in searches] != [0, 1, 2] or [item["search_seed"] for item in searches] != [610001, 610002, 610003]:
        raise ValueError("Registered search identities differ from the specified three searches")
    operations = args.operations.resolve()
    operations.mkdir(parents=True, exist_ok=True)
    with (operations / ".campaign.lock").open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        prior_path = operations / "manifest.json"
        prior = json.loads(prior_path.read_text()) if prior_path.exists() else {}
        if prior and (prior.get("study") != str(study) or prior.get("engine_config_sha256") != engine["sha256"] or prior.get("searches") != searches):
            raise ValueError("Saved supervisor belongs to different registered searches or settings")
        lock.seek(0)
        lock.truncate()
        lock.write(str(os.getpid()))
        lock.flush()
        state = {"status": "running", "controller_pid": os.getpid(), "study": str(study),
                 "engine_config_sha256": engine["sha256"], "searches": searches,
                 "completed_searches": [], "scope": "Three native searches only; no protected data in this supervisor"}
        with EventLogger(operations) as log:
            log.event("search_campaign_started", message="Sequential native search supervisor attached", **state)
            try:
                for item in searches:
                    index, seed = item["search_index"], item["search_seed"]
                    folder = Path(item["run"]).resolve()
                    manifest_path = folder / "manifest.json"
                    existing = json.loads(manifest_path.read_text()) if manifest_path.exists() else None
                    if existing:
                        if existing.get("task") != "joint_relocation_v3" or existing.get("search_seed") != seed or existing.get("generation_target") != 30 or existing.get("engine_config") != engine:
                            raise ValueError(f"Saved search identity/settings mismatch: {folder}")
                        if existing.get("status") == "search_complete":
                            summary = summarize_database(folder)
                            if summary["terminal_generation_ids"] != list(range(30)) or not summary["valid_seed"]:
                                raise ValueError(f"Completed manifest contradicts native archive: {folder}")
                            state["completed_searches"].append({"index": index, **summary})
                            log.event("search_reused", search_index=index, search_seed=seed, message="Completed native search verified; no model requests or evaluations repeated", **summary)
                            continue
                    recorded_pid = prior.get("child_pid") if prior.get("active_run") == str(folder) else None
                    survivor = surviving_controller(folder, seed, engine, args.engine_profile,
                                                    recorded_pid=recorded_pid)
                    if existing and not survivor and not (folder / "programs.sqlite").exists():
                        raise RuntimeError(f"Saved preflight has no native database and no surviving child; preserve and inspect {folder} before recovery")
                    command = [sys.executable, "-u", str(ROOT / "scripts/run_evolution.py"),
                               "--task", "joint_relocation_v3", "--generations", "30",
                               "--engine-profile", str(args.engine_profile.resolve()),
                               "--embedding-model", engine["evolution"]["embedding_model"],
                               "--model", engine["default_model"], "--search-seed", str(seed),
                               "--resume" if existing else "--run-dir", str(folder)]
                    if engine["default_effort"] is not None:
                        command.extend(["--effort", engine["default_effort"]])
                    transcript = operations / f"search_{index}-terminal.log"
                    with transcript.open("ab", buffering=0) as output:
                        child = None
                        if survivor:
                            record = survivor
                            command = survivor["command"]
                        else:
                            child = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL,
                                                     stdout=output, stderr=subprocess.STDOUT,
                                                     start_new_session=True, close_fds=True)
                            record = {"pid": child.pid}
                        state.update(active_search=index, active_search_seed=seed, active_run=str(folder),
                                     child_pid=record["pid"], command=command, terminal_log=str(transcript),
                                     attached_surviving_child=bool(survivor))
                        atomic_json(operations / "manifest.json", state)
                        log.set_activity(f"search {index}, seed {seed}, native controller PID {record['pid']}; detailed progress in {folder / 'run.log'}")
                        log.event("search_controller_attached" if survivor else "search_controller_started",
                                  search_index=index, search_seed=seed, child_pid=record["pid"],
                                  resuming=bool(existing), run=str(folder), terminal_log=str(transcript),
                                  native_lock_held=survivor["native_lock_held"] if survivor else None)
                        returncode = monitor_controller(folder, index, seed, record, log, child=child)
                        log.event("search_controller_exited", search_index=index, search_seed=seed,
                                  returncode=returncode, exit_status_known=child is not None)
                        if returncode:
                            raise RuntimeError(f"Search {index} exited {returncode}; preserve checkpoints and inspect {transcript}")
                    completed = json.loads(manifest_path.read_text())
                    summary = summarize_database(folder)
                    if completed["status"] != "search_complete" or summary["terminal_generation_ids"] != list(range(30)) or not summary["valid_seed"]:
                        raise RuntimeError(f"Search {index} did not finish all 30 terminal slots: {summary}")
                    state["completed_searches"].append({"index": index, **summary})
                    atomic_json(operations / "manifest.json", state)
                    log.event("search_completed", search_index=index, search_seed=seed, **summary)
                state.update(status="searches_complete", active_search=None, child_pid=None)
                atomic_json(operations / "manifest.json", state)
                log.event("search_campaign_complete", message="All three native searches complete; freeze/review shortlists before protected evaluation")
            except BaseException as exc:
                state.update(status="interrupted_or_failed", error=f"{type(exc).__name__}: {exc}")
                atomic_json(operations / "manifest.json", state)
                raise


if __name__ == "__main__":
    main()
