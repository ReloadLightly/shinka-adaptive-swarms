"""Storage checks replay small saved research fixtures; no model/objective calls."""
import ast
import copy
import errno
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from adaptive_swarms import artifacts, figures, storage


ROOT = Path(__file__).resolve().parents[1]
LEGACY_EVALUATOR = ROOT / "tests/fixtures/evaluate_pre_storage.py"
SAVED_SEED = ROOT / "artifacts/evolution/20260915T094647.219057Z-seed/gen_0/results"


def module_from(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def evaluators():
    return (module_from(LEGACY_EVALUATOR, "legacy_evaluator"),
            module_from(ROOT / "tasks/adaptive_swarm/evaluate.py", "storage_evaluator"))


@pytest.fixture
def saved_cases():
    # Four archived seed cases occupy less than half a MiB, including traces.
    return [artifacts.read_json(path) for path in artifacts.case_artifacts(SAVED_SEED)]


def input_files(tmp_path, saved_cases):
    program = tmp_path / "gen_0/main.py"
    program.parent.mkdir(parents=True)
    program.write_bytes((ROOT / "tasks/adaptive_swarm/initial.py").read_bytes())
    suite = tmp_path / "suite.json"
    suite.write_text(json.dumps([{**case["config"], "case_id": case["case_id"]}
                                 for case in saved_cases]))
    return program, suite


def replay(cases, calls):
    def run_case(config, policy=None, progress=None):
        calls.append(config["environment_seed"])
        expected = next(case for case in cases if case["config"] == config)
        result = copy.deepcopy(expected)
        result.pop("case_id")
        return result
    return run_case


def without_artifact_extensions(metrics):
    result = copy.deepcopy(metrics)
    for case in result["private"]["cases"]:
        case["artifact"] = case["artifact"].removesuffix(".gz")
    return result


def test_frozen_scientific_helpers_and_replayed_metrics_are_unchanged(
        tmp_path, monkeypatch, evaluators, saved_cases):
    legacy, current = evaluators
    assert hashlib.sha256(LEGACY_EVALUATOR.read_bytes()).hexdigest() == (
        "a8e89feb16fad03f3cd84b3a9e5644f3394706cb6b18c108db040e659a16b50c")
    trees = [ast.parse(path.read_text()) for path in
             (LEGACY_EVALUATOR, ROOT / "tasks/adaptive_swarm/evaluate.py")]
    for name in ("load_policy", "load_cases", "case_diagnostics", "describe_case"):
        nodes = [next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
                 for tree in trees]
        assert ast.dump(nodes[0]) == ast.dump(nodes[1])
    assert legacy.EVALUATION_VERSION == current.EVALUATION_VERSION
    assert legacy.FEEDBACK_VERSION == current.FEEDBACK_VERSION
    program, suite = input_files(tmp_path, saved_cases)
    old_dir, new_dir = program.parent / "legacy", program.parent / "results"
    for evaluator, folder in ((legacy, old_dir), (current, new_dir)):
        monkeypatch.setattr(evaluator, "run_case", replay(saved_cases, []))
        assert evaluator.evaluate(program, folder, suite) == 0
    assert artifacts.read_json(old_dir / "metrics.json") == without_artifact_extensions(
        artifacts.read_json(new_dir / "metrics.json"))
    for case in saved_cases:
        assert artifacts.read_json(new_dir / f"{case['case_id']}.json") == case
        assert not (new_dir / f"{case['case_id']}.json").exists()
    assert sum(path.stat().st_size for path in artifacts.case_artifacts(new_dir)) < (
        sum(path.stat().st_size for path in artifacts.case_artifacts(old_dir)) / 3)


def test_actual_figures_read_compressed_and_legacy_cases(tmp_path, saved_cases):
    folder = tmp_path / "run"
    compressed = artifacts.write_compressed_json(folder / "case_000.json", saved_cases[0])
    legacy = folder / "case_001.json"
    legacy.write_text(json.dumps(saved_cases[1]))
    assert artifacts.read_json(compressed) == saved_cases[0]
    assert artifacts.case_artifacts(folder) == [compressed, legacy]
    output = tmp_path / "figures"
    figures.render_run(folder, output)
    assert (output / "baseline_tracking.png").is_file()
    assert (output / "evaluation_accounting.svg").is_file()
    assert artifacts.read_json(output / "figure_provenance.json")["case_seeds"] == [
        case["config"]["environment_seed"] for case in saved_cases[:2]]


def test_legacy_completed_evaluation_is_reused_byte_for_byte(
        tmp_path, monkeypatch, evaluators, saved_cases):
    legacy, current = evaluators
    program, suite = input_files(tmp_path, saved_cases)
    folder = program.parent / "results"
    monkeypatch.setattr(legacy, "run_case", replay(saved_cases, []))
    assert legacy.evaluate(program, folder, suite) == 0
    preserved = {path: path.read_bytes() for path in
                 [*artifacts.case_artifacts(folder), folder / "metrics.json", folder / "correct.json"]}
    def no_rerun(*args, **kwargs):
        raise AssertionError("Completed evaluation must never execute again")
    monkeypatch.setattr(current, "run_case", no_rerun)
    assert current.evaluate(program, folder, suite) == 0
    assert all(path.read_bytes() == original for path, original in preserved.items())
    checkpoint = artifacts.read_json(folder / "evaluation-checkpoint.json")
    assert checkpoint["legacy_cases_reused"] is True
    assert checkpoint["status"] == "completed"
    assert len(checkpoint["completed_cases"]) == len(saved_cases)


@pytest.mark.parametrize("low_stage", ["before_next_case", "during_completed_case_write", "at_final_progress_event"])
def test_low_space_stops_next_case_and_resume_retains_completed_work(
        tmp_path, monkeypatch, evaluators, saved_cases, low_stage):
    _, evaluator = evaluators
    saved_cases = saved_cases[:2]
    program, suite = input_files(tmp_path, saved_cases)
    folder = program.parent / "results"
    free = {"host": 33 * storage.GIB}
    monkeypatch.setattr(storage, "verify_windows_c_mount", lambda: {"target": "/mnt/c", "source": "C:"})
    monkeypatch.setattr(storage, "available_bytes", lambda path: free["host"] if str(path) == "/mnt/c" else 100 * storage.GIB)
    guard = storage.StorageGuard(tmp_path, output_dir=folder)
    monkeypatch.setattr(evaluator, "get_storage_guard", lambda path: guard)
    check = guard.check
    interrupt = {"armed": True}
    def controlled_check(*args, **kwargs):
        activity = kwargs.get("activity")
        low_activity = "scheduling case_001" if low_stage == "before_next_case" else "writing compressed case case_000.json.gz"
        if activity == low_activity and interrupt["armed"] and low_stage != "at_final_progress_event":
            free["host"] = 9 * storage.GIB
        return check(*args, **kwargs)
    monkeypatch.setattr(guard, "check", controlled_check)
    calls = []
    replay_case = replay(saved_cases, calls)
    def completed_case(config, policy=None, progress=None):
        result = replay_case(config, policy, progress)
        if low_stage == "at_final_progress_event" and interrupt["armed"]:
            free["host"] = 9 * storage.GIB
            progress({"event": "run_completed", "evaluations": result["evaluations"]})
        return result
    monkeypatch.setattr(evaluator, "run_case", completed_case)
    assert evaluator.evaluate(program, folder, suite) == 75
    assert calls == [saved_cases[0]["config"]["environment_seed"]]
    checkpoint = artifacts.read_json(folder / "evaluation-checkpoint.json")
    assert checkpoint["status"] == "storage_checkpoint"
    assert len(checkpoint["completed_cases"]) == 1
    first = folder / "case_000.json.gz"
    first_bytes = first.read_bytes()
    assert not (folder / "metrics.json").exists()
    assert not (folder / "correct.json").exists()
    assert guard.stop_path.is_file()
    interrupt["armed"] = False
    free["host"] = 33 * storage.GIB
    guard.clear_stop_for_resume()
    assert evaluator.evaluate(program, folder, suite) == 0
    assert calls == [case["config"]["environment_seed"] for case in saved_cases]
    assert first.read_bytes() == first_bytes
    assert artifacts.read_json(folder / "metrics.json")["public"]["cases_completed"] == 2


def test_guard_interrupts_bulk_writer_and_removes_only_its_temporary(tmp_path):
    historical = tmp_path / "historical.json"
    historical.write_text('{"keep": true}')
    class Guard:
        checks = 0
        def check(self, **kwargs):
            self.checks += 1
            if self.checks == 3:
                raise storage.StorageInterrupted("synthetic low space")
    guard = Guard()
    with pytest.raises(storage.StorageInterrupted):
        artifacts.write_compressed_json(tmp_path / "case_000.json", ["trace" * 100] * 6000, guard)
    assert guard.checks == 3
    assert sorted(path.name for path in tmp_path.iterdir()) == ["historical.json"]


def test_disk_full_is_single_storage_pause_without_fitness(
        tmp_path, monkeypatch, evaluators, saved_cases):
    _, evaluator = evaluators
    program, suite = input_files(tmp_path, saved_cases[:1])
    folder = program.parent / "results"
    guard = storage.StorageGuard(tmp_path, output_dir=folder)
    monkeypatch.setattr(guard, "check", lambda **kwargs: {})
    monkeypatch.setattr(evaluator, "get_storage_guard", lambda path: guard)
    monkeypatch.setattr(evaluator, "run_case", replay(saved_cases, []))
    attempts = []
    def disk_full(*args, **kwargs):
        attempts.append(1)
        raise OSError(errno.ENOSPC, "simulated disk full")
    monkeypatch.setattr(evaluator, "write_compressed_json", disk_full)
    assert evaluator.evaluate(program, folder, suite) == 75
    assert attempts == [1]
    assert guard.stop_path.is_file()
    assert not (folder / "metrics.json").exists()
    assert not (folder / "correct.json").exists()


def test_changed_checkpoint_candidate_preserves_existing_results(
        tmp_path, monkeypatch, evaluators, saved_cases):
    _, evaluator = evaluators
    program, suite = input_files(tmp_path, saved_cases[:1])
    folder = program.parent / "results"
    monkeypatch.setattr(evaluator, "run_case", replay(saved_cases, []))
    assert evaluator.evaluate(program, folder, suite) == 0
    metrics = (folder / "metrics.json").read_bytes()
    program.write_text("def choose_response(observation): return {'fraction': 0.0}\n")
    with pytest.raises(ValueError, match="candidate, suite, or scientific sources differ"):
        evaluator.evaluate(program, folder, suite)
    assert (folder / "metrics.json").read_bytes() == metrics
