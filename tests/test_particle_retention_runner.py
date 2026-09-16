"""No-query checks for bounded reference registration, freeze, and recovery."""
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location("retention_runner", Path(__file__).resolve().parents[1] / "scripts/run_particle_retention.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


@pytest.fixture
def registered(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    folder = root / "results/study"
    folder.mkdir(parents=True)
    for name in ["docs/particle_retention_v1_protocol.md", "tasks/particle_retention_v1/evaluate.py", "scripts/run_particle_retention.py"]:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("frozen contract fixture\n")
    for name in ["random.py", "initial.py"]:
        (root / "tasks/particle_retention_v1" / name).write_text("def retention_priority(particle_features, swarm_features):\n    return 0.0\n")
    monkeypatch.setattr(runner, "ROOT", root)
    monkeypatch.setattr(runner, "retention_fingerprint", lambda: {"simulator": "fixture-stable"})
    monkeypatch.setattr(runner, "collect_used_seeds", lambda *a, **kw: {"reserved_seed_values": [1, 2], "files_inspected": 1})
    runner.atomic_json(folder / "session.json", {"deadline_utc": "2099-01-01T00:00:00+00:00"})
    runner.register(folder)
    return folder


def fake_result(config, *args, **kwargs):
    return {"config": config, "evaluations": config["budget"], "evaluation_counts": {"fake_fixture": config["budget"]},
            "offline_error": 1.0, "initial_environment": {"sha256": str(config["environment_seed"])}, "environment_changes": []}


def test_seed_identity_checkpoint_reuse_and_freeze(registered, monkeypatch):
    folder = registered
    identities = runner.read_json(folder / "development_cases.json")
    cases = identities["cases"]
    assert len(cases) == 8
    assert len({(c["move_severity"], c["period"]) for c in cases}) == 4
    assert len({c[k] for c in cases for k in ["environment_seed", "optimizer_seed"]}) == 16
    runner.register(folder)
    assert runner.read_json(folder / "development_cases.json") == identities
    calls = []
    def counted(config, *args, **kwargs):
        calls.append(config)
        return fake_result(config)
    monkeypatch.setattr(runner, "run_case", counted)
    runner.execute(folder, 1)
    assert len(calls) == 1
    with pytest.raises(ValueError, match="sixteen"):
        runner.freeze_suite(folder)
    runner.execute(folder)
    assert len(calls) == 16
    runner.execute(folder)
    assert len(calls) == 16
    runner.freeze_suite(folder)
    runner.freeze_suite(folder)
    suite = runner.read_json(folder / "search_suite.json")
    assert set(suite["feedback_references"]) == {"random", "seed"}
    assert all(Path(p).is_absolute() for v in suite["feedback_references"].values() for p in v["case_artifacts"])
    assert suite["feedback_references"]["seed"]["source_sha256"] == runner.sha(folder / "programs/heuristic.py")
    (folder / "programs/heuristic.py").write_text("changed")
    with pytest.raises(ValueError, match="source changed"):
        runner.execute(folder)


def test_failed_case_is_preserved_and_never_implicitly_repeated(registered, monkeypatch):
    class Failure(RuntimeError):
        objective_queries = 17
    def failed(*args, **kwargs):
        raise Failure("fixture interruption")
    monkeypatch.setattr(runner, "run_case", failed)
    with pytest.raises(Failure):
        runner.execute(registered)
    ledger = runner.read_json(registered / "references/execution_ledger.json")
    assert ledger["attempts"][0]["exact_partial_queries"] == 17
    assert ledger["attempts"][0]["status"] == "failed_or_interrupted"
    monkeypatch.setattr(runner, "run_case", lambda *a, **kw: pytest.fail("must not repeat failed work"))
    with pytest.raises(RuntimeError, match="recovery review"):
        runner.execute(registered)
