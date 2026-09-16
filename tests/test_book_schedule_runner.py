"""No-query checks for bounded reference registration, freeze, and recovery."""
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location("book_schedule_runner", Path(__file__).resolve().parents[1] / "scripts/run_book_mpso.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


@pytest.fixture
def registered(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    folder = root / "results/study"
    folder.mkdir(parents=True)
    for name in ["docs/book_mpso_schedule_v1_protocol.md", "tasks/book_mpso_schedule_v1/evaluate.py", "scripts/run_book_mpso.py", "docs/studies/book_mpso_schedule_v1/analysis_specification.json", "docs/book_mpso_source_record.md", "configs/shinka/book_mpso_schedule_v1.json"]:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("frozen contract fixture\n")
    for name in ["initial.py"]:
        (root / "tasks/book_mpso_schedule_v1" / name).write_text("def choose_temporary_quantum_count(observation):\n    return 5 if observation['change_detected'] else 0\n")
    monkeypatch.setattr(runner, "ROOT", root)
    monkeypatch.setattr(runner, "schedule_fingerprint", lambda: {"simulator": "fixture-stable"})
    monkeypatch.setattr(runner, "collect_used_seeds", lambda *a, **kw: {"reserved_seed_values": [1, 2], "files_inspected": 1})
    runner.atomic_json(folder / "session.json", {"deadline_utc": "2099-01-01T00:00:00+00:00"})
    runner.register(folder)
    return folder


def fake_result(config, *args, **kwargs):
    return {"config": config, "evaluations": config["budget"], "evaluation_counts": {"fake_fixture": config["budget"]},
            "permanent_quantum":kwargs.get("permanent_quantum",1), "schedule_stats":{}, "offline_error": 1.0, "initial_environment": {"sha256": str(config["environment_seed"])}, "environment_changes": []}


def test_seed_identity_checkpoint_reuse_and_freeze(registered, monkeypatch):
    folder = registered
    identities = runner.read_json(folder / "development_cases.json")
    cases = identities["cases"]
    assert len(cases) == 8
    assert len({(c["move_severity"], c["period"]) for c in cases}) == 1
    assert len({c[k] for c in cases for k in ["environment_seed", "optimizer_seed"]}) == 16
    runner.register(folder)
    assert runner.read_json(folder / "development_cases.json") == identities
    calls = []
    def counted(config, *args, **kwargs):
        calls.append(config)
        return fake_result(config, *args, **kwargs)
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
    assert set(suite["feedback_references"]) == {"mpso_5_0", "mpso_5_1"}
    assert all(Path(p).is_absolute() for v in suite["feedback_references"].values() for p in v["case_artifacts"])
    assert suite["feedback_references"]["mpso_5_1"]["source_sha256"] == runner.sha(folder / "programs/mpso_5_1.py")
    (folder / "programs/mpso_5_1.py").write_text("changed")
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


def test_fresh_seeds_are_blocked_until_selection_sources_and_analysis_are_frozen(registered,monkeypatch):
    folder=registered
    def forbidden(*args,**kwargs):
        pytest.fail('no seed generation before required source review')
    monkeypatch.setattr(runner,'collect_used_seeds',forbidden)
    with pytest.raises(FileNotFoundError):
        runner.register_fresh(folder)
    spec='docs/studies/book_mpso_schedule_v1/analysis_specification.json'
    source=folder/'programs/selected.py';source.write_text('def choose_temporary_quantum_count(obs):\n return 2\n')
    methods=dict(runner.read_json(folder/'references/manifest.json')['methods'])
    methods['selected']={'source':'programs/selected.py','sha256':runner.sha(source),'permanent_quantum':1}
    frozen={'fresh_comparison_required':True,'selected':methods['selected'],'methods':methods,
            'analysis_specification':spec,'analysis_sha256':runner.sha(runner.ROOT/spec),'frozen_at':runner.now()}
    runner.atomic_json(folder/'selection.json',frozen)
    with pytest.raises(FileNotFoundError):
        runner.register_fresh(folder)
    runner.atomic_json(folder/'source_review.json',{'approved_source_sha256':'wrong'})
    with pytest.raises(ValueError,match='reviewed'):
        runner.register_fresh(folder)
    runner.atomic_json(folder/'source_review.json',{'approved_source_sha256':methods['selected']['sha256']})
    (runner.ROOT/spec).write_text('analysis changed after selection')
    with pytest.raises(ValueError,match='Analysis changed'):
        runner.register_fresh(folder)
    assert not (folder/'fresh/manifest.json').exists()


def test_seed_best_skips_duplicate_fresh_comparison(registered,monkeypatch):
    runner.atomic_json(registered/'selection.json',{'fresh_comparison_required':False})
    monkeypatch.setattr(runner,'collect_used_seeds',lambda *a,**kw:pytest.fail('no unnecessary fresh seeds'))
    with pytest.raises(ValueError,match='No distinct'):
        runner.register_fresh(registered)
