"""200-peak registration, accounting and selection fixtures; zero objective queries."""
import copy
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "population_200_runner", Path(__file__).parents[1] / "scripts/run_book_population_200.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)
TASK = "book_mpso_population_200_v1"


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    folder = root / "results/study"
    folder.mkdir(parents=True)
    contracts = [f"docs/{TASK}_protocol.md", f"tasks/{TASK}/evaluate.py",
                 "scripts/run_book_population_200.py", f"docs/studies/{TASK}/analysis_specification.json",
                 "docs/book_mpso_source_record.md", f"configs/shinka/{TASK}.json",
                 f"tasks/{TASK}/context.md", f"tasks/{TASK}/task_prompt.txt"]
    for relative in contracts:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("prospective synthetic contract\n")
    (root / f"tasks/{TASK}/initial.py").write_text(
        "def choose_neutral_count(observation):\n    return 5\n")
    cases = [runner._validated_config({"npeaks": 200, "budget": 500000,
             "environment_seed": i * 2 + 1, "optimizer_seed": i * 2 + 2}) for i in range(4)]
    runner.atomic_json(root / f"configs/{TASK}/development.json", {"cases": cases})
    monkeypatch.setattr(runner, "ROOT", root)
    monkeypatch.setattr(runner, "schedule_fingerprint", lambda: {"simulator": "synthetic-stable"})
    monkeypatch.setattr(runner, "run_case", lambda *a, **kw: pytest.fail("No numerical queries in fixtures"))
    runner.atomic_json(folder / "session.json", {"deadline_utc": "2099-01-01T00:00:00+00:00",
                        "research_deadline_utc": "2098-12-31T23:45:00+00:00"})
    return folder


@pytest.fixture
def registered(prepared):
    runner.register(prepared)
    return prepared


def fake_result(config, *args, **kwargs):
    return {"config": config, "evaluations": config["budget"],
            "evaluation_counts": {"synthetic": config["budget"]}, "permanent_quantum": 1,
            "population_stats": {}, "offline_error": 1.0,
            "initial_environment": {"sha256": str(config["environment_seed"])}, "environment_changes": []}


@pytest.mark.parametrize("change", ["ten_peaks", "short_horizon", "extra_case"])
def test_registration_rejects_wrong_condition_or_case_count(prepared, change):
    path = runner.ROOT / f"configs/{TASK}/development.json"
    record = runner.read_json(path)
    if change == "ten_peaks":
        record["cases"][0]["npeaks"] = 10
    elif change == "short_horizon":
        record["cases"][0]["budget"] = 50000
    else:
        record["cases"].append(copy.deepcopy(record["cases"][0]))
    runner.atomic_json(path, record)
    with pytest.raises(ValueError, match="four 200-peak full-horizon"):
        runner.register(prepared)
    assert not (prepared / "references/manifest.json").exists()


def test_registration_preserves_seed_and_freezes_cases(registered):
    runner.register(registered)
    manifest = runner.read_json(registered / "references/manifest.json")
    assert list(manifest["methods"]) == ["target_5", "target_3"]
    assert manifest["maximum_new_executions"] == 8
    assert len(manifest["cases"]) == 4
    assert (registered / "programs/target_5.py").read_bytes() == (
        runner.ROOT / f"tasks/{TASK}/initial.py").read_bytes()
    path = registered / "development_cases.json"
    changed = runner.read_json(path)
    changed["cases"][0]["environment_seed"] += 100
    runner.atomic_json(path, changed)
    with pytest.raises(ValueError, match="Frozen development cases"):
        runner.register(registered)


def test_first_measurement_is_five_then_recovery_and_two_control_freeze(registered, monkeypatch):
    calls = []
    def simulate(config, policy, progress):
        calls.append((config, policy({})))
        return fake_result(config)
    monkeypatch.setattr(runner, "run_case", simulate)
    runner.execute(registered, max_new_cases=1)
    assert [target for _, target in calls] == [5]
    with pytest.raises(ValueError, match="All eight paired"):
        runner.freeze_suite(registered)
    ledger_path = registered / "references/execution_ledger.json"
    ledger = runner.read_json(ledger_path)
    ledger["attempts"][0]["status"] = "running"  # Atomic artifact saved before ledger completion.
    runner.atomic_json(ledger_path, ledger)
    runner.execute(registered)
    runner.execute(registered)
    assert len(calls) == 8
    assert runner.read_json(ledger_path)["attempts"][0]["recovered_from_completed_artifact"]
    runner.freeze_suite(registered)
    runner.freeze_suite(registered)
    suite = runner.read_json(registered / "search_suite.json")
    assert set(suite["feedback_references"]) == {"target_3", "target_5"}
    assert suite["development_only"] is True
    assert all(len(r["case_artifacts"]) == 4 for r in suite["feedback_references"].values())
    assert suite["feedback_references"]["target_5"]["source_sha256"] == runner.sha(
        registered / "programs/target_5.py")


def make_search(folder, seed, three, descendants):
    cases = runner.read_json(folder / "development_cases.json")["cases"]
    for target, error in [(3, three), (5, seed)]:
        for i, config in enumerate(cases):
            runner.write_compressed_json(folder / f"references/target_{target}/case_{i:03d}.json.gz",
                {"case_id": f"case_{i:03d}", **fake_result(config), "offline_error": error})
    search = folder / "evolution/search_seed_660001"
    runner.atomic_json(search / "manifest.json", {"status": "search_complete"})
    suite_path = folder / "search_suite.json"
    runner.atomic_json(suite_path, {"cases": cases})
    for generation, error, status, count in [(0, seed, "completed", 4), *descendants]:
        gen = search / f"gen_{generation}"
        gen.mkdir(parents=True, exist_ok=True)
        (gen / "main.py").write_text((folder / "programs/target_5.py").read_text() if generation == 0
            else f"def choose_neutral_count(observation):\n    return {generation + 1}\n")
        identity = {"program_sha256": runner.sha(gen / "main.py"), "suite_sha256": runner.sha(suite_path),
                    "scientific_sources": runner.schedule_fingerprint(),
                    "evaluator_sha256": runner.sha(runner.ROOT / f"tasks/{TASK}/evaluate.py")}
        runner.atomic_json(gen / "results/evaluation-checkpoint.json", {"status": status, "identity": identity})
        runner.atomic_json(gen / "results/metrics.json", {"public": {"cases_completed": count},
                                                        "combined_score": 1/(1+error)})
        for i, config in enumerate(cases[:count]):
            runner.write_compressed_json(gen / f"results/case_{i:03d}.json.gz",
                {"case_id": f"case_{i:03d}", **fake_result(config), "offline_error": error})
    return search


@pytest.mark.parametrize("seed,three,descendant,required,winner", [
    (1., .8, .85, False, 1), (1., .8, .8, False, 1),
    (1., .8, .7, True, 1), (.8, 1., .7, True, 1),
    (.8, 1., .8, False, 0), (.8, 1., .9, False, 0),
])
def test_selection_includes_seed_and_fresh_requires_strict_advantage_over_both(
        registered, monkeypatch, seed, three, descendant, required, winner):
    make_search(registered, seed, three, [(1, descendant, "completed", 4)])
    selection = runner.freeze_selection(registered)
    assert selection["fresh_comparison_required"] is required
    assert selection["selected"]["generation"] == winner
    assert set(selection["methods"]) == {"target_5", "target_3", "selected"}
    assert runner.freeze_selection(registered) == selection
    if winner == 0:
        assert selection["execution_aliases"]["selected"] == "target_5"
    if not required:
        monkeypatch.setattr(runner, "collect_used_seeds", lambda *a, **kw: pytest.fail("No fresh seed generation"))
        with pytest.raises(ValueError, match="No distinct"):
            runner.register_fresh(registered)
    assert not (registered / "fresh/manifest.json").exists()


def test_incomplete_programs_are_not_ranked_and_earlier_complete_generation_wins(registered):
    make_search(registered, 1., 1.1, [(1, .8, "completed", 4), (2, .8, "completed", 4),
                (3, .1, "running", 3), (4, .1, "completed", 3)])
    selection = runner.freeze_selection(registered)
    assert [entry["generation"] for entry in selection["ranking"]] == [1, 2, 0]
    assert selection["selected"]["generation"] == 1


def test_changed_native_source_is_rejected_before_selection(registered):
    search = make_search(registered, 1., 1.1, [(1, .8, "completed", 4)])
    (search / "gen_1/main.py").write_text("def choose_neutral_count(observation):\n    return 8\n")
    with pytest.raises(ValueError, match="checkpoint identity"):
        runner.freeze_selection(registered)
    assert not (registered / "programs/selected.py").exists()


def test_failed_case_is_not_repeated_and_partial_accounting_is_retained(registered, monkeypatch):
    class Failed(RuntimeError):
        objective_queries = 17  # Synthetic metadata, no actual objective queries.
    monkeypatch.setattr(runner, "run_case", lambda *a, **kw: (_ for _ in ()).throw(Failed("synthetic")))
    with pytest.raises(Failed):
        runner.execute(registered)
    ledger = runner.read_json(registered / "references/execution_ledger.json")
    assert ledger["attempts"][0]["exact_partial_queries"] == 17
    monkeypatch.setattr(runner, "run_case", lambda *a, **kw: pytest.fail("No implicit repeated execution"))
    with pytest.raises(RuntimeError, match="recovery review"):
        runner.execute(registered)
