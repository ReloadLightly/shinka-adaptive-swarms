"""Task boundaries must keep v2 scientific snapshots separate from legacy runs."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def launcher():
    spec = importlib.util.spec_from_file_location("task_launcher_test", ROOT / "scripts/run_evolution.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v2_freezes_adapter_prompt_and_executes_exact_evaluator(tmp_path):
    module = launcher()
    args = SimpleNamespace(task="relocation_allocation_v2", resume=None)
    hashes = module.prepare_snapshot(args, tmp_path)
    snapshot = tmp_path / "task_snapshot"
    for name in ("relocation_allocation.py", "task_prompt.txt", "task_system_prompt.txt", "protocol.md"):
        assert module.file_hash(snapshot / name) == hashes[name]
    assert "choose_relocation_count" in (snapshot / "task_system_prompt.txt").read_text()
    (tmp_path / "manifest.json").write_text(json.dumps({"task": args.task}))
    assert module.prepare_storage_evaluator(tmp_path) == snapshot / "evaluate.py"
    args.resume = tmp_path
    assert module.prepare_snapshot(args, tmp_path) == hashes
    (snapshot / "task_system_prompt.txt").write_text("changed interface")
    with pytest.raises(RuntimeError, match="Saved task context changed"):
        module.prepare_snapshot(args, tmp_path)


def test_wrong_task_resume_rejected_before_log_or_native_mutation(tmp_path, monkeypatch):
    module = launcher()
    (tmp_path / "programs.sqlite").touch()
    (tmp_path / "manifest.json").write_text(json.dumps({"evaluation_version": module.EVALUATION_VERSION}))
    monkeypatch.setattr("sys.argv", ["run_evolution.py", "--resume", str(tmp_path), "--task", "relocation_allocation_v2"])
    with pytest.raises(SystemExit) as error:
        module.main()
    assert error.value.code == 2
    assert not (tmp_path / "run.log").exists()


def test_v2_new_run_uses_versioned_manifest_and_suite(tmp_path, monkeypatch):
    module = launcher()
    monkeypatch.setattr(module, "inspect_runtime", lambda *a: {"ready": True, "errors": []})
    monkeypatch.setattr(module, "run_native", lambda *a: None)
    monkeypatch.setattr(module, "summarize_database", lambda *a: {"generation_records": 1, "valid_programs": 1})
    monkeypatch.setattr("sys.argv", ["run_evolution.py", "--task", "relocation_allocation_v2", "--seed-only", "--results-root", str(tmp_path)])
    assert module.main() == 0
    manifest = json.loads(next(tmp_path.glob("*/manifest.json")).read_text())
    assert manifest["task"] == "relocation_allocation_v2"
    assert manifest["evaluation_version"] == "relocation_allocation_v2_score_reciprocal"
    assert manifest["suite_sha256"] == module.file_hash(ROOT / "configs/relocation_allocation_v2/search.json")
