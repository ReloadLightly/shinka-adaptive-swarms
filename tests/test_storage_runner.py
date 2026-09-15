"""Focused scheduler/real-entrypoint checks; no experimental model calls."""
import argparse
import asyncio
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from adaptive_swarms import storage
from adaptive_swarms.storage_runner import StorageRunnerMixin

ROOT = Path(__file__).resolve().parents[1]


def mocked_space(monkeypatch, gib=30):
    reading = {"gib": gib}
    monkeypatch.setattr(storage, "verify_windows_c_mount", lambda: {"target": "/mnt/c", "source": "C:\\", "fstype": "9p"})
    monkeypatch.setattr(storage, "available_bytes", lambda path: reading["gib"] * storage.GIB)
    return reading


class FakeNative:
    def __init__(self):
        self.running_jobs = []
        self.active_proposal_tasks = {}
        self.should_stop = asyncio.Event()
        self.scheduled = 0
        self.persisted = 0

    async def _start_proposals(self, count):
        self.scheduled += count

    async def _submit_evaluation_job_with_slot(self, *args):
        self.scheduled += 1

    async def _persist_completed_job(self, job):
        self.persisted += 1


class GuardedFake(StorageRunnerMixin, FakeNative):
    pass


def test_scheduler_blocks_new_work_and_never_scores_storage_pause(tmp_path, monkeypatch):
    space = mocked_space(monkeypatch)
    guard = storage.StorageGuard(tmp_path)
    runner = GuardedFake()
    runner.configure_storage(guard, SimpleNamespace(event=lambda *a, **k: None))
    asyncio.run(runner._start_proposals(1))
    assert runner.scheduled == 1
    space["gib"] = 9
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(runner._submit_evaluation_job_with_slot("gen_3/main.py", "results", None))
    assert runner.scheduled == 1
    assert runner.should_stop.is_set()
    assert json.loads(guard.stop_path.read_text())["status"] == "storage_paused"
    job = SimpleNamespace(results_dir=str(tmp_path), job_id=SimpleNamespace(returncode=75), generation=3)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(runner._persist_completed_job(job))
    assert runner.persisted == 0
    space["gib"] = 30
    guard.clear_stop_for_resume()
    asyncio.run(runner._start_proposals(1))
    assert runner.scheduled == 2


def test_low_space_real_entrypoint_stops_before_runtime_or_models(tmp_path, monkeypatch):
    monkeypatch.setenv(storage.ENV_CONFIG, "")
    mocked_space(monkeypatch, gib=9)
    spec = importlib.util.spec_from_file_location("storage_test_launcher", ROOT / "scripts/run_evolution.py")
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    monkeypatch.setattr(launcher, "inspect_runtime", lambda *args: pytest.fail("low-space launch must not inspect or invoke model runtime"))
    monkeypatch.setattr("sys.argv", ["run_evolution.py", "--seed-only", "--results-root", str(tmp_path)])
    assert launcher.main() == 75
    markers = list(tmp_path.glob("*/storage-stop.json"))
    assert len(markers) == 1
    assert json.loads(markers[0].read_text())["status"] == "storage_paused"
    assert not list(tmp_path.glob("*/programs.sqlite"))


def test_frozen_scientific_evaluator_helpers_are_preserved(tmp_path):
    spec = importlib.util.spec_from_file_location("storage_adapter_launcher", ROOT / "scripts/run_evolution.py")
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    frozen = ROOT / "results/evolution/20260915T101024.562418Z-search/task_snapshot/evaluate.py"
    if not frozen.exists():
        frozen = ROOT / "tasks/adaptive_swarm/evaluate.py"
    (tmp_path / "task_snapshot").mkdir()
    (tmp_path / "task_snapshot/evaluate.py").write_bytes(frozen.read_bytes())
    path = launcher.prepare_storage_evaluator(tmp_path)
    assert path.is_file()
    record = json.loads((path.parent / "provenance.json").read_text())
    assert record["evaluation_version"] == launcher.EVALUATION_VERSION
    assert (tmp_path / "task_snapshot/evaluate.py").read_bytes() == frozen.read_bytes()


def test_native_seed_result_boundary_rejects_paused_missing_metrics(tmp_path, monkeypatch):
    mocked_space(monkeypatch)
    guard = storage.StorageGuard(tmp_path)
    runner = GuardedFake()
    def seed_run(*args, **kwargs):
        (tmp_path / "evaluation-checkpoint.json").write_text(json.dumps({"status": "storage_paused"}))
        return {}, 0.01
    runner.scheduler = SimpleNamespace(run=seed_run, get_job_results_async=lambda *a: None)
    runner.configure_storage(guard, SimpleNamespace(event=lambda *a, **k: None))
    with pytest.raises(storage.StorageInterrupted):
        runner.scheduler.run("gen_0/main.py", str(tmp_path))
    assert guard.stopped
    assert runner.persisted == 0


def test_native_seed_result_boundary_maps_enospc_to_pause(tmp_path, monkeypatch):
    import errno
    mocked_space(monkeypatch)
    guard = storage.StorageGuard(tmp_path)
    runner = GuardedFake()
    def seed_run(*args, **kwargs):
        raise OSError(errno.ENOSPC, "simulated native output full")
    runner.scheduler = SimpleNamespace(run=seed_run, get_job_results_async=lambda *a: None)
    runner.configure_storage(guard, SimpleNamespace(event=lambda *a, **k: None))
    with pytest.raises(storage.StorageInterrupted):
        runner.scheduler.run("gen_0/main.py", str(tmp_path))
    assert guard.stopped
    assert runner.persisted == 0


def test_real_native_entrypoint_preserves_seed_after_storage_resume(tmp_path, monkeypatch):
    """A real 31-query fixture, then low/healthy resume with no repeated evaluator."""
    import sqlite3
    monkeypatch.setenv(storage.ENV_CONFIG, "")
    space = mocked_space(monkeypatch)
    spec = importlib.util.spec_from_file_location("storage_native_launcher", ROOT / "scripts/run_evolution.py")
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    monkeypatch.setattr(launcher, "inspect_runtime", lambda *a: {"ready": True, "errors": [], "model_calls_performed_by_check": 0})
    suite = tmp_path / "tiny-suite.json"
    suite.write_text(json.dumps({"budget": 31, "period": 10, "cases": [{}]}))
    root = tmp_path / "runs"
    monkeypatch.setattr("sys.argv", ["run_evolution.py", "--seed-only", "--suite", str(suite), "--results-root", str(root)])
    assert launcher.main() == 0
    run = next(root.glob("*-seed"))
    case = run / "gen_0/results/case_000.json.gz"
    case_before = case.read_bytes()
    mtime_before = case.stat().st_mtime_ns
    with sqlite3.connect(run / "programs.sqlite") as db:
        rows_before = db.execute("SELECT id,generation,correct,combined_score FROM programs ORDER BY id").fetchall()
    assert rows_before and all(row[1] == 0 and row[2] for row in rows_before)
    monkeypatch.setattr("sys.argv", ["run_evolution.py", "--seed-only", "--resume", str(run)])
    space["gib"] = 9
    assert launcher.main() == 75
    assert (run / "storage-stop.json").exists()
    space["gib"] = 30
    from shinka.launch.scheduler import JobScheduler
    monkeypatch.setattr(JobScheduler, "run", lambda *a, **k: pytest.fail("completed native seed must not be evaluated on resume"))
    assert launcher.main() == 0
    assert not (run / "storage-stop.json").exists()
    assert list(run.glob("storage-stop-*.json"))
    assert case.read_bytes() == case_before
    assert case.stat().st_mtime_ns == mtime_before
    with sqlite3.connect(run / "programs.sqlite") as db:
        assert db.execute("SELECT id,generation,correct,combined_score FROM programs ORDER BY id").fetchall() == rows_before


def test_pending_resume_returns_before_second_slot_and_retains_lineage(tmp_path, monkeypatch):
    from adaptive_swarms import native_storage
    mocked_space(monkeypatch)
    for generation in (1, 2):
        folder = tmp_path / f"gen_{generation}"
        folder.mkdir()
        (folder / "main.py").write_text("def choose_response(o): return {}")
    def recover(folder, db):
        generation = int(folder.name[4:])
        return {"generation": generation, "exec_fname": str(folder / "main.py"),
                "results_dir": str(folder / "results"), "start_time": 1.0,
                "proposal_started_at": 1.0, "evaluation_submitted_at": 1.0,
                "parent_id": "original-parent", "meta_patch_data": {"patch_description": "retained hypothesis"}}
    monkeypatch.setattr(native_storage, "recover_pending_spec", recover)

    async def exercise():
        runner = GuardedFake()
        runner.results_dir = tmp_path
        runner.db = object()
        runner.evo_config = SimpleNamespace(num_generations=3)
        async def persisted(): return {0}
        runner.async_db = SimpleNamespace(get_persisted_generation_ids_async=persisted)
        runner.next_generation_to_submit = 1
        runner.submitted_jobs = {}
        runner.slot_available = asyncio.Event()
        runner.configure_storage(storage.StorageGuard(tmp_path), SimpleNamespace(event=lambda *a, **k: None))
        slot = asyncio.Semaphore(1)
        async def submit(exec_fname, results_dir, sampling_worker_id):
            await slot.acquire()
            return exec_fname, 0, 2.0, 2.0, 1
        runner._submit_evaluation_job_with_slot = submit
        await asyncio.wait_for(runner._restore_storage_jobs(), timeout=0.1)
        tasks = list(runner.active_proposal_tasks.values())
        assert len(tasks) == 2
        await asyncio.sleep(0)
        assert len(runner.running_jobs) == 1
        assert runner.next_generation_to_submit == 3
        slot.release()
        await asyncio.wait_for(asyncio.gather(*tasks), timeout=0.1)
        assert len(runner.running_jobs) == 2
        assert not runner.active_proposal_tasks
        assert all(job.parent_id == "original-parent" for job in runner.running_jobs)
        assert all(job.meta_patch_data["patch_description"] == "retained hypothesis" for job in runner.running_jobs)
    asyncio.run(exercise())


def test_storage_stop_calls_native_cancellation_without_scoring(tmp_path, monkeypatch):
    from shinka.core.async_runner import AsyncRunningJob
    import psutil
    mocked_space(monkeypatch)
    monkeypatch.setattr(psutil, "Process", lambda: SimpleNamespace(children=lambda **kwargs: []))
    original_sleep = asyncio.sleep
    async def immediate_sleep(seconds): await original_sleep(0)
    monkeypatch.setattr(asyncio, "sleep", immediate_sleep)
    async def exercise():
        runner = GuardedFake()
        runner.configure_storage(storage.StorageGuard(tmp_path), SimpleNamespace(event=lambda *a, **k: None))
        candidate = tmp_path / "gen_1/main.py"
        candidate.parent.mkdir()
        candidate.write_text("def choose_response(o): return {}")
        job = AsyncRunningJob(job_id=SimpleNamespace(poll=lambda: None), exec_fname=str(candidate),
            results_dir=str(candidate.parent / "results"), start_time=0, proposal_started_at=0,
            evaluation_submitted_at=0, generation=1)
        runner.running_jobs = [job]
        runner.submitted_jobs = {"job1": job}
        runner.completed_generations = 1
        cancelled = []
        async def cancel(jid): cancelled.append(jid)
        runner.scheduler = SimpleNamespace(cancel_job_async=cancel)
        runner.storage_guard.request_stop("simulated")
        await runner._stop_storage_workers()
        assert cancelled == [job.job_id]
        assert json.loads((candidate.parent / "storage-job.json").read_text())["generation"] == 1
        assert runner.persisted == 0
    asyncio.run(exercise())
