"""Synthetic checkpoint, cache provenance, and fresh-trigger risks; zero queries."""
import copy
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location("population_runner", Path(__file__).parents[1] / "scripts/run_book_population.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


@pytest.fixture
def registered(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    folder = root / "results/study"
    folder.mkdir(parents=True)
    contracts = ["docs/book_mpso_population_v1_protocol.md", "tasks/book_mpso_population_v1/evaluate.py",
                 "scripts/run_book_population.py", "docs/studies/book_mpso_population_v1/analysis_specification.json",
                 "docs/book_mpso_source_record.md", "configs/shinka/book_mpso_population_v1.json",
                 "configs/book_mpso_population_v1/study.json"]
    for relative in contracts:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("prospective synthetic contract\n")
    initial = root / "tasks/book_mpso_population_v1/initial.py"
    initial.write_text("def choose_neutral_count(observation):\n    return 5\n")
    cases = [runner._validated_config({"budget": 500000, "environment_seed": i * 2 + 1,
                                      "optimizer_seed": i * 2 + 2}) for i in range(8)]
    legacy = "configs/book_mpso_schedule_v1/development.json"
    runner.atomic_json(root / legacy, {"cases": cases})
    runner.atomic_json(root / "configs/book_mpso_population_v1/development.json", {"cases": cases, "reused_from": legacy})
    monkeypatch.setattr(runner, "ROOT", root)
    monkeypatch.setattr(runner, "schedule_fingerprint", lambda: {"simulator": "synthetic-stable"})
    runner.atomic_json(folder / "session.json", {"deadline_utc": "2099-01-01T00:00:00+00:00"})
    runner.register(folder)
    return folder


def fake_result(config, *args, **kwargs):
    return {"config": config, "evaluations": config["budget"], "evaluation_counts": {"synthetic": config["budget"]},
            "permanent_quantum": 1, "population_stats": {}, "offline_error": 1.0,
            "initial_environment": {"sha256": str(config["environment_seed"])}, "environment_changes": []}


def test_import_requires_current_proof_and_historical_hash_then_reuses(registered, monkeypatch):
    folder = registered
    proof_path = folder / "operations/target5-compatibility.json"
    runner.atomic_json(proof_path, {"status": "passed", "scientific_sources": {"simulator": "old"}})
    with pytest.raises(ValueError, match="compatibility"):
        runner.import_target5(folder)
    runner.atomic_json(proof_path, {"status": "passed", "scientific_sources": runner.schedule_fingerprint()})
    old = runner.ROOT / "artifacts/book_mpso_schedule_v1/20260916T154109Z"
    manifest = []
    for i, cfg in enumerate(runner.read_json(folder / "development_cases.json")["cases"]):
        path = old / "references/mpso_5_1" / f"case_{i:03d}.json.gz"
        runner.write_compressed_json(path, {"case_id": f"case_{i:03d}", **fake_result(cfg)})
        manifest.append({"path": str(path.relative_to(old)), "sha256": runner.sha(path)})
    runner.atomic_json(old / "MANIFEST.json", manifest)
    monkeypatch.setattr(runner, "from_compatible_fixed_five_result", copy.deepcopy)
    monkeypatch.setattr(runner, "run_case", lambda *a, **kw: pytest.fail("cache import must not execute objectives"))
    runner.import_target5(folder)
    runner.import_target5(folder)
    ledger = runner.read_json(folder / "references/execution_ledger.json")
    assert len(ledger["attempts"]) == 8
    assert all(row["status"] == "reused" and row["actual_queries"] == 0 for row in ledger["attempts"])
    # Recover an import completed atomically before its ledger completion.
    ledger["attempts"][0]["status"] = "importing"
    runner.atomic_json(folder / "references/execution_ledger.json", ledger)
    runner.import_target5(folder)
    assert runner.read_json(folder / "references/execution_ledger.json")["attempts"][0]["status"] == "reused"
    target = folder / "references/target_5/case_000.json.gz"
    changed = runner.read_json(target)
    changed["offline_error"] = 123.0
    target.unlink()  # Deliberate corruption of this synthetic temporary artifact.
    runner.write_compressed_json(target, changed)
    with pytest.raises(ValueError, match="import|artifact",):
        runner.import_target5(folder)


def test_all_controls_complete_before_freeze_and_no_repeat_after_atomic_recovery(registered, monkeypatch):
    folder = registered
    calls = []
    def simulate(config, *args, **kwargs):
        calls.append(config)
        return fake_result(config)
    monkeypatch.setattr(runner, "run_case", simulate)
    runner.execute(folder, max_new_cases=1)
    assert len(calls) == 1
    with pytest.raises(ValueError, match="twenty-four"):
        runner.freeze_suite(folder)
    ledger_path = folder / "references/execution_ledger.json"
    ledger = runner.read_json(ledger_path)
    ledger["attempts"][0]["status"] = "running"
    runner.atomic_json(ledger_path, ledger)
    runner.execute(folder)
    runner.execute(folder)
    assert len(calls) == 24
    assert runner.read_json(ledger_path)["attempts"][0]["recovered_from_completed_artifact"]
    runner.freeze_suite(folder)
    runner.freeze_suite(folder)
    suite = runner.read_json(folder / "search_suite.json")
    assert set(suite["feedback_references"]) == {"target_3", "target_5", "target_7"}
    assert suite["development_only"] is True


@pytest.mark.parametrize("seed,three,seven,descendant,required,methods", [
    (1., .8, .9, .85, False, {"target_5", "target_3", "selected"}),
    (1., .8, .9, .8, False, {"target_5", "target_3", "selected"}),
    (1., .8, .9, .7, True, {"target_5", "target_3", "selected"}),
    (.8, 1., .9, .7, True, {"target_5", "selected"}),
    (.8, 1., .9, .9, False, {"target_5", "selected"}),
])
def test_fresh_trigger_requires_strict_advantage_over_both_and_aliases_fixed_five(
        registered, monkeypatch, seed, three, seven, descendant, required, methods):
    folder = registered
    cases = runner.read_json(folder / "development_cases.json")["cases"]
    for k, error in [(3, three), (5, seed), (7, seven)]:
        for i, cfg in enumerate(cases):
            runner.write_compressed_json(folder / f"references/target_{k}/case_{i:03d}.json.gz",
                                         {"case_id": f"case_{i:03d}", **fake_result(cfg), "offline_error": error})
    search = folder / "evolution/search_seed_650001"
    runner.atomic_json(search / "manifest.json", {"status": "search_complete"})
    suite_path = folder / "search_suite.json"
    runner.atomic_json(suite_path, {"cases": cases})
    for generation, error in [(0, seed), (1, descendant)]:
        gen = search / f"gen_{generation}"
        gen.mkdir(parents=True, exist_ok=True)
        (gen / "main.py").write_text((folder / "programs/target_5.py").read_text() if generation == 0
                                      else "def choose_neutral_count(observation):\n    return 2\n")
        identity = {"program_sha256": runner.sha(gen / "main.py"), "suite_sha256": runner.sha(suite_path),
                    "scientific_sources": runner.schedule_fingerprint(),
                    "evaluator_sha256": runner.sha(runner.ROOT / "tasks/book_mpso_population_v1/evaluate.py")}
        runner.atomic_json(gen / "results/evaluation-checkpoint.json", {"status": "completed", "identity": identity})
        runner.atomic_json(gen / "results/metrics.json", {"public": {"cases_completed": 8}, "combined_score": 1/(1+error)})
        for i, cfg in enumerate(cases):
            runner.write_compressed_json(gen / f"results/case_{i:03d}.json.gz",
                                         {"case_id": f"case_{i:03d}", **fake_result(cfg), "offline_error": error})
    checkpoint_path = search / "gen_1/results/evaluation-checkpoint.json"
    checkpoint = runner.read_json(checkpoint_path)
    changed = copy.deepcopy(checkpoint)
    changed["identity"]["program_sha256"] = "changed source"
    runner.atomic_json(checkpoint_path, changed)
    with pytest.raises(ValueError, match="checkpoint identity"):
        runner.freeze_selection(folder)
    runner.atomic_json(checkpoint_path, checkpoint)
    selected = runner.freeze_selection(folder)
    assert selected["fresh_comparison_required"] is required
    assert set(selected["methods"]) == methods
    if selected["selected"]["generation"] == 0:
        assert selected["execution_aliases"]["selected"] == "target_5"
    if not required:
        monkeypatch.setattr(runner, "collect_used_seeds", lambda *a, **kw: pytest.fail("no fresh seed generation"))
        with pytest.raises(ValueError, match="No distinct"):
            runner.register_fresh(folder)
    assert not (folder / "fresh/manifest.json").exists()


def test_terminal_failed_case_is_not_repeated(registered, monkeypatch):
    class Failed(RuntimeError):
        objective_queries = 17  # synthetic accounting fixture, no actual queries
    monkeypatch.setattr(runner, "run_case", lambda *a, **kw: (_ for _ in ()).throw(Failed("synthetic")))
    with pytest.raises(Failed):
        runner.execute(registered)
    ledger = runner.read_json(registered / "references/execution_ledger.json")
    assert ledger["attempts"][0]["exact_partial_queries"] == 17
    monkeypatch.setattr(runner, "run_case", lambda *a, **kw: pytest.fail("terminal failure cannot be rerun implicitly"))
    with pytest.raises(RuntimeError, match="recovery review"):
        runner.execute(registered)
