"""No provider calls: test the real native retry/batch boundaries with fake transport."""
import asyncio
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from adaptive_swarms.engine_runtime import install_engine_observers
from adaptive_swarms.logging import EventLogger
from adaptive_swarms.sprint_budget import LogicalResponseBudget, SprintLimitReached
from adaptive_swarms.storage_runner import ResumeRunnerMixin

ROOT = Path(__file__).resolve().parents[1]


def launcher():
    spec = importlib.util.spec_from_file_location("sprint_launcher_test", ROOT / "scripts/run_evolution.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def native_client(monkeypatch, transport):
    pytest.importorskip("shinka")
    from shinka.llm import llm
    monkeypatch.setattr(llm, "query_async", transport)
    monkeypatch.setattr(llm, "sample_model_kwargs", lambda **kwargs: {"model_name": "headless/codex@gpt-6-astra"})
    return llm.AsyncLLMClient(model_names=["headless/codex@gpt-6-astra"], verbose=False)


def runner_for(client):
    def stop(error):
        raise error
    return SimpleNamespace(llm=client, meta_summarizer=None, novelty_judge=None,
                           embedding_client=None, _fail_infrastructure=stop)


def test_full_native_batch_is_reserved_before_any_dispatch_and_retained_on_resume(tmp_path, monkeypatch):
    calls = []
    async def transport(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(content="answer")
    client = native_client(monkeypatch, transport)
    with EventLogger(tmp_path) as log:
        cleanup = install_engine_observers(runner_for(client), log, tmp_path, logical_response_limit=3)
        try:
            assert len(asyncio.run(client.batch_kwargs_query(2, "message", "system"))) == 2
            assert len(calls) == 2
            with pytest.raises(SprintLimitReached):
                asyncio.run(client.batch_kwargs_query(2, "next", "system"))
        finally:
            cleanup()
    assert len(calls) == 2
    assert LogicalResponseBudget(tmp_path, 3).used == 2
    receipts = list((tmp_path / "engine_calls").glob("*.json"))
    assert len(receipts) == 1
    receipt = json.loads(receipts[0].read_text())
    assert receipt["requested_logical_responses"] == 2
    assert len(receipt["native_dispatch_attempts"]) == 2
    stop = json.loads((tmp_path / "sprint-stop.json").read_text())
    assert stop["declined_responses"] == 2 and not stop["scientific_failure"]


def test_exposed_native_retry_consumes_allowance_and_next_retry_never_dispatches(tmp_path, monkeypatch):
    calls = []
    async def transport(**kwargs):
        calls.append(kwargs)
        raise RuntimeError("synthetic transient native transport failure")
    client = native_client(monkeypatch, transport)
    with EventLogger(tmp_path) as log:
        cleanup = install_engine_observers(runner_for(client), log, tmp_path, logical_response_limit=2)
        try:
            with pytest.raises(SprintLimitReached):
                asyncio.run(client.query("message", "system"))
        finally:
            cleanup()
    assert len(calls) == 2
    receipt = json.loads(next((tmp_path / "engine_calls").glob("*.json")).read_text())
    assert receipt["initial_logical_responses"] == 1
    assert receipt["requested_logical_responses"] == 2
    assert receipt["exposed_native_retry_responses"] == 1
    assert [a["status"] for a in receipt["native_dispatch_attempts"]] == ["failed", "failed"]
    assert LogicalResponseBudget(tmp_path, 2).used == 2


def test_allowance_stop_wakes_native_background_loop_and_preserves_checkpoint(tmp_path):
    checkpoint = tmp_path / "storage-job.json"
    checkpoint.write_text('{"generation": 4, "parent_id": "retained-native-parent"}')
    before = checkpoint.read_bytes()
    class Native:
        async def _run_async(self):
            try:
                self._fail_infrastructure(SprintLimitReached("allowance exhausted"))
            except SprintLimitReached:
                pass  # Native task boundaries can consume their own exception.
            await asyncio.Event().wait()
    class Runner(ResumeRunnerMixin, Native):
        pass
    async def exercise():
        runner = Runner()
        runner.should_stop = asyncio.Event()
        runner.configure_resume(SimpleNamespace(event=lambda *a, **k: None))
        with pytest.raises(SprintLimitReached):
            await asyncio.wait_for(runner._run_async(), timeout=1)
        assert runner.should_stop.is_set()
    asyncio.run(exercise())
    assert checkpoint.read_bytes() == before
    assert not (tmp_path / "failure.json").exists()


def test_launcher_labels_allowance_stop_without_terminal_candidate_failure(tmp_path, monkeypatch):
    module = launcher()
    monkeypatch.setattr(module, "inspect_runtime", lambda *a: {"ready": True, "errors": []})
    monkeypatch.setattr(module, "prepare_snapshot", lambda *a: {})
    monkeypatch.setattr(module, "summarize_database", lambda *a: {"terminal_slots": 4, "valid_descendants": 3, "terminal_failed_generation_ids": []})
    def stop(*args):
        raise SprintLimitReached("60 reserved, batch requires 5")
    monkeypatch.setattr(module, "run_native", stop)
    monkeypatch.setattr("sys.argv", ["run_evolution.py", "--seed-only", "--run-dir", str(tmp_path / "run"), "--logical-response-limit", "60"])
    assert module.main() == 77
    manifest = json.loads((tmp_path / "run/manifest.json").read_text())
    assert manifest["status"] == "sprint_limit_reached" and manifest["logical_response_limit"] == 60
    assert manifest["latest_summary"]["terminal_failed_generation_ids"] == []


def test_resume_cannot_drop_or_increase_recorded_sprint_allowance(tmp_path, monkeypatch):
    module = launcher()
    (tmp_path / "programs.sqlite").touch()
    (tmp_path / "manifest.json").write_text(json.dumps({"logical_response_limit": 60}))
    monkeypatch.setattr("sys.argv", ["run_evolution.py", "--resume", str(tmp_path), "--logical-response-limit", "61"])
    with pytest.raises(SystemExit) as exc:
        module.main()
    assert exc.value.code == 2
    assert not (tmp_path / "run.log").exists()
    monkeypatch.setattr("sys.argv", ["run_evolution.py", "--resume", str(tmp_path), "--print-engine-config"])
    assert module.main() == 0


def test_sprint_profile_preserves_every_native_research_v3_setting():
    original = json.loads((ROOT / "configs/shinka/research_v3.json").read_text())
    sprint = json.loads((ROOT / "configs/shinka/radius_velocity_sprint.json").read_text())
    assert sprint["evolution"] == original["evolution"]
    assert sprint["database"] == original["database"]
    module = launcher()
    assert module.TASK_VERSIONS["radius_velocity_sprint"] == "fixed_four_radius_velocity_sprint_score_reciprocal_v1"
