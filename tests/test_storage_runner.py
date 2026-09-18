"""Focused rollback/resume checks; native evaluation and model calls are mocked."""
import asyncio
import errno
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from adaptive_swarms.execution import INFRASTRUCTURE_EXIT_CODE, InfrastructureError
from adaptive_swarms.storage_runner import ResumeRunnerMixin

ROOT = Path(__file__).resolve().parents[1]


def launcher_module():
    spec = importlib.util.spec_from_file_location("rollback_test_launcher", ROOT / "scripts/run_evolution.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


class ResumableFake(ResumeRunnerMixin, FakeNative):
    pass


def test_evaluation_timeout_excludes_proposal_and_preserves_native_timing():
    runner = ResumableFake()
    seen = []
    def check(job):
        seen.append(job)
        # A 100-second limit at t=250: proposal began at 10, evaluation at 200.
        return 250 - job.start_time <= 100
    runner.scheduler = SimpleNamespace(run=lambda *a: None,
        get_job_results_async=lambda *a: None, check_job_status=check)
    runner.configure_resume(SimpleNamespace(event=lambda *a, **k: None))
    process = object()
    job = SimpleNamespace(start_time=10, evaluation_started_at=200,
                          job_id=process, generation=9)
    assert runner.scheduler.check_job_status(job)
    assert job.start_time == 10
    assert seen[-1].job_id is process and seen[-1].generation == 9
    job.evaluation_started_at = 100
    assert not runner.scheduler.check_job_status(job)
    # Legacy/seed jobs without a separate evaluation clock keep their behavior.
    legacy = SimpleNamespace(start_time=10)
    assert not runner.scheduler.check_job_status(legacy)
    assert seen[-1] is legacy


def test_scheduler_accepts_work_with_historical_storage_stop(tmp_path, monkeypatch):
    (tmp_path / "storage-stop.json").write_text('{"status":"storage_paused"}')
    monkeypatch.setenv("ADAPTIVE_SWARMS_STORAGE_CONFIG", '{"checkpoint_gib":10}')
    monkeypatch.setattr(os, "statvfs", lambda path: SimpleNamespace(f_bavail=0, f_frsize=4096))
    runner = ResumableFake()
    runner.results_dir = tmp_path
    runner.configure_resume(SimpleNamespace(event=lambda *a, **k: None))
    asyncio.run(runner._start_proposals(1))
    asyncio.run(runner._submit_evaluation_job_with_slot("gen_3/main.py", "results", None))
    assert runner.scheduled == 2
    assert not runner.should_stop.is_set()
    assert (tmp_path / "storage-stop.json").is_file()


def test_launcher_reaches_native_with_zero_reported_space_and_no_mount_probe(tmp_path, monkeypatch):
    launcher = launcher_module()
    monkeypatch.setattr(os, "statvfs", lambda path: SimpleNamespace(f_bavail=0, f_frsize=4096))
    monkeypatch.setenv("ADAPTIVE_SWARMS_STORAGE_CONFIG", '{"checkpoint_gib":10}')
    monkeypatch.setattr(launcher, "inspect_runtime", lambda *a: {"ready": True, "errors": [], "model_calls_performed_by_check": 0})
    monkeypatch.setattr(launcher, "prepare_snapshot", lambda *a: {})
    monkeypatch.setattr(launcher, "summarize_database", lambda *a: {"generation_records": 1, "valid_programs": 1, "valid_descendants": 0})
    calls = []
    def native(*args):
        assert "ADAPTIVE_SWARMS_STORAGE_CONFIG" not in os.environ
        calls.append(args)
    monkeypatch.setattr(launcher, "run_native", native)
    monkeypatch.setattr("subprocess.run", lambda *a, **k: pytest.fail("No mount or external runtime probe is needed after the mocked runtime check"))
    monkeypatch.setattr("sys.argv", ["run_evolution.py", "--seed-only", "--results-root", str(tmp_path)])
    assert launcher.main() == 0
    assert len(calls) == 1
    assert not list(tmp_path.glob("*/storage-stop.json"))
    assert not list(tmp_path.glob("*/programs.sqlite"))


def test_frozen_scientific_evaluator_helpers_are_preserved(tmp_path):
    launcher = launcher_module()
    frozen = ROOT / "tests/fixtures/evaluate_pre_storage.py"
    (tmp_path / "task_snapshot").mkdir()
    (tmp_path / "task_snapshot/evaluate.py").write_bytes(frozen.read_bytes())
    path = launcher.prepare_storage_evaluator(tmp_path)
    assert path.is_file()
    assert path.parent.parent.name == "storage_runtime"
    record = json.loads((path.parent / "provenance.json").read_text())
    assert record["evaluation_version"] == launcher.EVALUATION_VERSION
    assert (tmp_path / "task_snapshot/evaluate.py").read_bytes() == frozen.read_bytes()


@pytest.mark.parametrize("status,returncode", [("infrastructure_error", INFRASTRUCTURE_EXIT_CODE), ("storage_paused", 75)])
def test_native_result_boundary_never_scores_infrastructure_failure(tmp_path, status, returncode):
    (tmp_path / "evaluation-checkpoint.json").write_text(json.dumps({"status": status}))
    runner = ResumableFake()
    runner.configure_resume(SimpleNamespace(event=lambda *a, **k: None))
    job = SimpleNamespace(results_dir=str(tmp_path), job_id=SimpleNamespace(returncode=returncode), generation=3)
    with pytest.raises(InfrastructureError):
        asyncio.run(runner._persist_completed_job(job))
    assert runner.persisted == 0


def test_native_seed_result_boundary_preserves_enospc(tmp_path):
    runner = ResumableFake()
    def seed_run(*args, **kwargs):
        raise OSError(errno.ENOSPC, "simulated native output full")
    runner.scheduler = SimpleNamespace(run=seed_run, get_job_results_async=lambda *a: None)
    runner.configure_resume(SimpleNamespace(event=lambda *a, **k: None))
    with pytest.raises(InfrastructureError) as error:
        runner.scheduler.run("gen_0/main.py", str(tmp_path))
    assert isinstance(error.value.__cause__, OSError)
    assert error.value.__cause__.errno == errno.ENOSPC
    assert runner.persisted == 0


def test_pending_resume_returns_before_second_slot_and_retains_lineage(tmp_path, monkeypatch):
    from adaptive_swarms import native_storage
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
        runner = ResumableFake()
        runner.results_dir = tmp_path
        runner.db = object()
        runner.evo_config = SimpleNamespace(num_generations=3)
        async def persisted(): return {0}
        runner.async_db = SimpleNamespace(get_persisted_generation_ids_async=persisted)
        runner.next_generation_to_submit = 1
        runner.submitted_jobs = {}
        runner.slot_available = asyncio.Event()
        runner.configure_resume(SimpleNamespace(event=lambda *a, **k: None))
        slot = asyncio.Semaphore(1)
        async def submit(exec_fname, results_dir, sampling_worker_id):
            await slot.acquire()
            return exec_fname, 0, 2.0, 2.0, 1
        runner._submit_evaluation_job_with_slot = submit
        await asyncio.wait_for(runner._restore_pending_jobs(), timeout=0.1)
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


def test_background_io_failure_wakes_controller_without_scientific_result():
    class BackgroundNative(FakeNative):
        async def _run_async(self):
            def failed_output():
                try:
                    self._fail_infrastructure(OSError(errno.ENOSPC, "background output full"))
                except InfrastructureError:
                    # Native output threads can consume their own exception.
                    pass
            await asyncio.to_thread(failed_output)
            await asyncio.Event().wait()

    class Runner(ResumeRunnerMixin, BackgroundNative):
        pass

    async def exercise():
        runner = Runner()
        runner.configure_resume(SimpleNamespace(event=lambda *a, **k: None))
        with pytest.raises(InfrastructureError) as error:
            await asyncio.wait_for(runner._run_async(), timeout=1)
        assert error.value.__cause__.errno == errno.ENOSPC
        assert runner.should_stop.is_set()
        assert runner.persisted == 0
    asyncio.run(exercise(), debug=True)


def test_event_log_io_failure_stays_visible_without_retry(tmp_path):
    from adaptive_swarms.logging import EventLogger
    log = EventLogger(tmp_path)
    original = log._json
    writes, failures = [], []
    class FullStream:
        def write(self, text):
            writes.append(text)
            raise OSError(errno.ENOSPC, "event log full")
        def close(self):
            original.close()
    log._json = FullStream()
    log.on_io_error = failures.append
    with pytest.raises(InfrastructureError) as error:
        log.event("case_complete", case_id="saved-case")
    assert error.value.__cause__.errno == errno.ENOSPC
    with pytest.raises(InfrastructureError):
        log.event("case_complete", case_id="saved-case")
    with pytest.raises(InfrastructureError):
        log.__exit__(None, None, None)
    assert len(writes) == len(failures) == 1
