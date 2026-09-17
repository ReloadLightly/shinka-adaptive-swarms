"""Corrected campaign evaluator checks; synthetic records, zero objective queries."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from adaptive_swarms.artifacts import read_json, write_compressed_json
from adaptive_swarms.population_policy_v2 import population_fingerprint, PopulationPolicyError
from adaptive_swarms.book_population_v2 import ENGINE_VERSION
from adaptive_swarms.execution import INFRASTRUCTURE_EXIT_CODE
from adaptive_swarms.campaign_accounting import research_accounting
from adaptive_swarms.simulator import _validated_config

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def setup(tmp_path):
    path = ROOT / "tasks/book_mpso_population_200_v2/evaluate.py"
    spec = importlib.util.spec_from_file_location("population_200_evaluator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    program = tmp_path / "main.py"
    program.write_bytes((path.parent / "initial.py").read_bytes())
    cases, paths = [], []
    for index in range(4):
        config = _validated_config({**module.REQUIRED_SETTINGS,
            "environment_seed": 810 + index, "optimizer_seed": 910 + index})
        cases.append(config)
        result = {"case_id": f"case_{index:03d}", "config": config,
            "evaluations": 500000, "evaluation_counts": {"ordinary": 300000, "detection": 100000, "memory": 100000},
            "engine_version": ENGINE_VERSION, "permanent_quantum": 1, "population_stats": {"additions": 0, "removals": 0},
            "offline_error": 2.0 + index / 10,
            "initial_environment": {"sha256": f"synthetic-{index}"},
            "environment_changes": [], "response_log": [],
            "trace": [{"evaluations": 1, "swarm_count": 1, "total_particle_count": 6},
                      {"evaluations": 100, "swarm_count": 2, "total_particle_count": 12},
                      {"evaluations": 500000, "swarm_count": 4, "total_particle_count": 24}]}
        paths.append(write_compressed_json(tmp_path / f"reference_{index}.json.gz", result))
    reference = {"method": "synthetic fixture, no objective calls",
        "case_artifacts": [str(path.resolve()) for path in paths],
        "case_sha256": [digest(path) for path in paths],
        "source_sha256": digest(program), "scientific_sources": population_fingerprint()}
    suite = tmp_path / "suite.json"
    suite.write_text(json.dumps({"campaign_directory": str(tmp_path), "cases": cases, "feedback_references": {
        "target_3": reference, "target_5": reference}}))
    return module, program, suite, tmp_path / "evolution/search_seed_670001/gen_1/results", paths


def test_exact_seed_reuses_all_four_current_200_peak_cases(setup, monkeypatch):
    module, program, suite, folder, paths = setup
    def forbidden(*args, **kwargs):
        raise AssertionError("Exact seed reuse must make no objective calls")
    monkeypatch.setattr(module, "run_case", forbidden)
    assert module.evaluate(program, folder, suite) == 0
    saved_hashes = [digest(folder / f"case_{index:03d}.json.gz") for index in range(4)]
    assert module.evaluate(program, folder, suite) == 0
    assert [digest(folder / f"case_{index:03d}.json.gz") for index in range(4)] == saved_hashes
    metrics = read_json(folder / "metrics.json")
    assert metrics["public"]["cases_completed"] == 4
    assert metrics["private"]["cases"][0]["paired_differences"] == {"target_3": 0.0, "target_5": 0.0}
    assert "200 conical peaks" in metrics["text_feedback"]
    assert "total_particle_count" in metrics["text_feedback"]
    assert "previous_requested_target" in metrics["text_feedback"]
    assert "target_7" not in metrics["text_feedback"]
    stats = metrics["private"]["cases"][0]["population_stats"]
    assert stats["trace_sampled_mean_swarm_count"] == 3
    assert stats["trace_sampled_mean_total_particle_count"] == 18
    assert not (folder / "execution-attempts.json").exists()


@pytest.mark.parametrize("key,value", [("npeaks", 10), ("budget", 100000), ("move_severity", 5), ("correlation", .5)])
def test_wrong_frozen_condition_rejected_before_execution(setup, key, value):
    module, program, suite, folder, _ = setup
    data = read_json(suite)
    data["cases"][0][key] = value
    suite.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="Frozen 200-peak development setting differs"):
        module.evaluate(program, folder, suite)
    assert not (folder / "evaluation-checkpoint.json").exists()


def test_case_count_and_duplicate_pairs_rejected(setup):
    module, _, suite, _, _ = setup
    data = read_json(suite)
    shorter = copy.deepcopy(data)
    shorter["cases"].pop()
    suite.write_text(json.dumps(shorter))
    with pytest.raises(ValueError, match="exactly four"):
        module.load_cases(suite)
    data["cases"][1] = copy.deepcopy(data["cases"][0])
    suite.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="seed pairs must be distinct"):
        module.load_cases(suite)


def test_reference_pairing_is_required(setup):
    module, program, suite, folder, paths = setup
    data = read_json(suite)
    altered = read_json(paths[0])
    altered["initial_environment"]["sha256"] = "unpaired-synthetic-history"
    different = write_compressed_json(suite.parent / "unpaired.json.gz", altered)
    data["feedback_references"]["target_3"]["case_artifacts"][0] = str(different)
    data["feedback_references"]["target_3"]["case_sha256"][0] = digest(different)
    suite.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="landscapes are not paired"):
        module.evaluate(program, folder, suite)


def test_saved_full_budget_and_reference_hash_required(setup):
    module, program, suite, folder, paths = setup
    paths[0].write_bytes(paths[0].read_bytes() + b" ")
    with pytest.raises(ValueError, match="reference hash differs"):
        module.evaluate(program, folder, suite)
    result = read_json(paths[1])
    result["evaluation_counts"]["ordinary"] -= 1
    with pytest.raises(ValueError, match="Incomplete objective budget"):
        module.validate_saved_case(result, result["config"], result["case_id"], paths[1])


def test_other_condition_control_is_not_silently_accepted(setup):
    module, program, suite, folder, _ = setup
    data = read_json(suite)
    data["feedback_references"]["target_7"] = data["feedback_references"]["target_3"]
    suite.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="fixed-target 3 and 5"):
        module.evaluate(program, folder, suite)


def test_failed_slot_retains_exact_partial_query_accounting(setup, monkeypatch):
    module, program, suite, folder, _ = setup
    program.write_text(program.read_text() + "\n# different synthetic source\n")
    calls = []
    def failure(*args, **kwargs):
        calls.append(1)
        exc = PopulationPolicyError("Synthetic invalid response; no actual objective calls")
        exc.objective_queries = 17
        raise exc
    monkeypatch.setattr(module, "run_case", failure)
    assert module.evaluate(program, folder, suite) == 1
    assert module.evaluate(program, folder, suite) == 1
    assert calls == [1]
    attempt = read_json(folder / "execution-attempts.json")[0]
    assert attempt["exact_objective_queries"] == 17
    assert attempt["reserved_objective_queries"] == 500000
    assert read_json(folder / "correct.json")["correct"] is False


def test_documented_local_math_and_workload_fields_are_accepted(setup, monkeypatch):
    module, program, suite, folder, paths = setup
    program.write_text("def choose_neutral_count(obs):\n import math\n return min(8, max(2, int(math.sqrt(16)) + (obs.get('swarm_count', 1) > 99)))\n")
    policies = []
    def synthetic_execution(config, policy, progress):
        policies.append(policy({"swarm_count": 3, "previous_requested_target": 5}))
        result = read_json(paths[len(policies) - 1])
        return {key: value for key, value in result.items() if key != "case_id"}
    monkeypatch.setattr(module, "run_case", synthetic_execution)
    assert module.evaluate(program, folder, suite) == 0
    assert policies == [4, 4, 4, 4]
    assert read_json(folder / "metrics.json")["combined_score"] == pytest.approx(1 / 3.15)


def test_historical_geometry_cannot_supply_corrected_reference(setup):
    module, program, suite, folder, paths = setup
    data = read_json(suite)
    result = read_json(paths[0])
    result["engine_version"] = "book_mpso_population_v1"
    old = write_compressed_json(suite.parent / "old-geometry.json.gz", result)
    data["feedback_references"]["target_5"]["case_artifacts"][0] = str(old)
    data["feedback_references"]["target_5"]["case_sha256"][0] = digest(old)
    suite.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="convergence-engine identity"):
        module.evaluate(program, folder, suite)
    assert not (folder / "execution-attempts.json").exists()


def test_unresolved_attempt_is_infrastructure_pause_and_keeps_reservation(setup, monkeypatch):
    module, program, suite, folder, _ = setup
    program.write_text(program.read_text() + "\n# distinct pending source\n")
    folder.mkdir(parents=True)
    module.prepare_checkpoint(program, folder, suite)
    attempt = {"case_id": "case_000", "status": "running", "reserved_objective_queries": 500000,
               "observed_objective_queries_lower_bound": 37, "exact_objective_queries": None}
    (folder / "execution-attempts.json").write_text(json.dumps([attempt]))
    monkeypatch.setattr(module, "run_case", lambda *args: pytest.fail("No interrupted case replay"))
    assert module.evaluate(program, folder, suite) == INFRASTRUCTURE_EXIT_CODE
    assert not (folder / "correct.json").exists()
    assert read_json(folder / "execution-attempts.json") == [attempt]
    accounting = research_accounting(suite.parent)
    assert accounting["full_case_attempts"] == 1
    assert accounting["conservative_research_queries"] == 500000
    assert accounting["known_completed_queries"] == 0
