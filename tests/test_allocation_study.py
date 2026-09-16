"""Concrete leakage, selection, alias, control and checkpoint risks in v2."""
import copy
import json
from pathlib import Path
import random
import sqlite3

import pytest

from adaptive_swarms import allocation_study as study
from adaptive_swarms.logging import atomic_json
from adaptive_swarms.simulator import _validated_config


def synthetic_study(tmp_path):
    search = tmp_path / "search"
    search.mkdir()
    connection = sqlite3.connect(search / "programs.sqlite")
    connection.execute("CREATE TABLE programs (id TEXT, code TEXT, parent_id TEXT, generation INTEGER, combined_score REAL, correct INTEGER, metadata TEXT, public_metrics TEXT, text_feedback TEXT)")
    sources = [
        ("later", "def choose_relocation_count(observation):\n    return 3\n", 4, .3, 1),
        ("earlier", "def choose_relocation_count(observation):\n    return 2\n", 2, .3, 1),
        ("duplicate", "def choose_relocation_count(observation):\n    return 3\n", 5, .3, 1),
        ("invalid", "def choose_relocation_count(observation):\n    return 0\n", 1, .9, 0),
        ("adaptive", "def choose_relocation_count(observation):\n    return 4 if observation['relative_fitness_drop'] > 0 else 1\n", 3, .2, 1),
    ]
    for name, source, generation, score, correct in sources:
        connection.execute("INSERT INTO programs VALUES (?,?,NULL,?,?,?,NULL,NULL,NULL)", (name, source, generation, score, correct))
    for generation in set(range(20)) - {2, 4, 5, 1, 3}:
        connection.execute("INSERT INTO programs VALUES (?,?,NULL,?,?,?,NULL,NULL,NULL)", (f"failed_{generation}", "", generation, None, 0))
    connection.commit()
    connection.close()
    atomic_json(search / "manifest.json", {"task": "relocation_allocation_v2", "evaluation_version": "relocation_allocation_v2_score_reciprocal",
                                          "status": "search_complete", "generation_target": 20})
    folder = tmp_path / "study"
    record = study.freeze_shortlist(search, folder)
    review = tmp_path / "review.json"
    atomic_json(review, {"reviewer": "test fixture", "notes": "Synthetic literal/observation-only functions inspected.",
                         "approved_source_sha256": [p["sha256"] for p in record["programs"]]})
    study.record_source_review(folder, review)
    return folder, record


def test_shortlist_correct_source_distinct_deterministic_and_immutable(tmp_path):
    folder, record = synthetic_study(tmp_path)
    assert [p["native_id"] for p in record["programs"]] == ["earlier", "later", "adaptive"]
    assert record["available_source_distinct_valid_programs"] == 3
    assert record["programs"][0]["proven_constant"] == 2
    assert record["programs"][2]["proven_constant"] is None
    assert not (folder / "final_cases.json").exists()
    (folder / record["programs"][0]["policy"]).write_text("raise RuntimeError()")
    with pytest.raises(ValueError, match="Frozen source changed"):
        study.verify_shortlist(folder)


def test_constancy_proof_never_uses_observed_traces():
    assert study.proven_constant('"""doc"""\ndef choose_relocation_count(observation: dict) -> int:\n    """doc"""\n    return 3\n') == 3
    assert study.proven_constant("def choose_relocation_count(o):\n    return True") is None
    assert study.proven_constant("x = 3\ndef choose_relocation_count(o):\n    return x") is None
    assert study.proven_constant("def choose_relocation_count(o):\n    return 3 if o['swarm_size']==5 else 1") is None


def test_case_equal_control_fallback_and_rng_independence():
    config = _validated_config({"budget": 61})
    cases = [{"config": config, "response_log": [{"requested_count": 1}] * 100},
             {"config": config, "response_log": [{"requested_count": 5}]},
             {"config": config, "response_log": []}]
    control = study.control_distributions(cases)
    probabilities = control["distributions"][study.regime_key(config)]
    assert probabilities == [0, 1/3, 0, 1/3, 0, 1/3]
    assert control["case_proportions"][-1]["no_response_count_three_fallback"]
    first = study.state_free_count_policy(probabilities, 29)
    second = study.state_free_count_policy(probabilities, 29)
    sequence = [first({"relative_fitness_drop": i}) for i in range(50)]
    for _ in range(200):
        random.random()
    assert sequence == [second({"hidden": "ignored"}) for _ in range(50)]


def test_paired_statistics_equal_regime_weights_and_precision():
    result = study.paired_statistics([-2, -2, 2, 2, 2], ["a", "a", "b", "b", "b"])
    assert result["mean_delta"] == 0
    assert result["stratified_se_delta"] == 0
    assert result["bootstrap_95_percent_interval"] == [0, 0]
    varied = study.paired_statistics([0, 2, 2, 4], ["a", "a", "b", "b"])
    assert varied["stratified_se_delta"] == pytest.approx(2 ** -.5)


def test_checkpoint_resume_does_not_repeat_and_constants_alias(tmp_path, monkeypatch):
    folder, shortlist = synthetic_study(tmp_path)
    cases = [_validated_config({"budget": 71, "period": 20, "environment_seed": seed, "optimizer_seed": seed + 10}) for seed in (801, 802)]
    methods = {"constant_3": study._constant_method(3), "shortlist_2": study._program_method(shortlist["programs"][1]),
               "constant_1": study._constant_method(1)}
    original = study.run_case
    calls = []
    def interrupt(config, policy=None, progress=None):
        calls.append(config["environment_seed"])
        if len(calls) == 2:
            raise RuntimeError("interrupt after completed cache")
        return original(config, policy, progress)
    monkeypatch.setattr(study, "run_case", interrupt)
    with pytest.raises(RuntimeError, match="interrupt after"):
        study._run_stage(folder, "validation", cases, methods, study.file_sha(folder / "shortlist.json"))
    checkpoints = list((folder / "validation/cache").glob("*.json.gz"))
    assert len(checkpoints) == 1
    preserved = checkpoints[0].read_bytes()
    calls.clear()
    def tracked(config, policy=None, progress=None):
        calls.append(config["environment_seed"])
        return original(config, policy, progress)
    monkeypatch.setattr(study, "run_case", tracked)
    result = study._run_stage(folder, "validation", cases, methods, study.file_sha(folder / "shortlist.json"))
    assert calls == [801, 802, 802]
    assert result["unique_executed_method_cases"] == 4
    assert len(result["aliases"]) == 2
    assert checkpoints[0].read_bytes() == preserved
    manifest, outcomes = study.load_stage_outcomes(folder, "validation")
    assert manifest["case_artifacts"]["constant_3"] == manifest["case_artifacts"]["shortlist_2"]
    assert all(study.validate_pair(a, b)["matching_environment_hashes"] for a, b in zip(outcomes["constant_3"], outcomes["constant_1"]))
    calls.clear()
    study._run_stage(folder, "validation", cases, methods, study.file_sha(folder / "shortlist.json"))
    assert calls == []


def test_historical_seed_collection_cross_role_and_gzip(tmp_path):
    atomic_json(tmp_path / "manifest.json", {"nested": [{"environment_seed": 73, "optimizer_seed": 12}]})
    study.write_compressed_json(tmp_path / "case.json", {"config": {"environment_seed": 91, "optimizer_seed": 73}})
    result = study.collect_used_seeds([tmp_path])
    assert result["environment_seeds"] == [73, 91]
    assert result["optimizer_seeds"] == [12, 73]
    assert result["files_inspected"] == 2


def test_final_generation_follows_freeze_and_excludes_every_seed_role(tmp_path, monkeypatch):
    folder, _ = synthetic_study(tmp_path)
    configs = [_validated_config({"move_severity": severity, "period": period, "budget": 100000,
                                  "environment_seed": 20 + i, "optimizer_seed": 40 + i}) for i, (severity, period) in enumerate(study.REGIMES)]
    atomic_json(folder / "validation/manifest.json", {"cases": configs})
    frozen = {"frozen_at": "2000-01-01T00:00:00+00:00"}
    atomic_json(folder / "selection.json", frozen)
    monkeypatch.setattr(study, "select_and_freeze", lambda path: frozen)
    monkeypatch.setattr(study.secrets, "randbits", lambda bits: 7)
    reserved = random.Random(7).randrange(1, 2**31)
    history = tmp_path / "history.json"
    atomic_json(history, {"environment_seed": reserved, "optimizer_seed": 99})
    result = study.generate_final_cases(folder, [history])
    seeds = [case[key] for case in result["cases"] for key in ("environment_seed", "optimizer_seed")]
    assert len(seeds) == len(set(seeds)) == 80
    assert reserved not in seeds
    assert not set(seeds) & {20, 21, 22, 23, 40, 41, 42, 43, 99}
    assert result["selection_frozen_at"] < result["generated_at"]
    assert study.generate_final_cases(folder, []) == result


def test_point_mass_control_aliases_constant_only_by_exact_distribution():
    config = _validated_config({})
    control = {"kind": "state_free", "rng_master_seed": 123,
               "distributions": {study.regime_key(config): [0, 0, 0, 1, 0, 0]}}
    assert study.method_identity(control, config) == study.method_identity(study._constant_method(3), config)
    control["distributions"][study.regime_key(config)] = [0, 0, .01, .99, 0, 0]
    assert study.method_identity(control, config)["kind"] == "state_free"


def test_selection_freezes_ties_and_control_before_final_cases(tmp_path, monkeypatch):
    folder, shortlist = synthetic_study(tmp_path)
    cases = [_validated_config({"budget": 71, "period": 20, "environment_seed": 100 + i,
                                 "optimizer_seed": 500 + i, "move_severity": severity})
             for i, severity in enumerate((1, 1, 3, 3))]
    methods = {f"constant_{k}": study._constant_method(k) for k in range(6)}
    methods.update({p["name"]: study._program_method(p) for p in shortlist["programs"]})
    original = study.run_case
    def tied_measurement(config, policy=None, progress=None):
        result = original(config, policy, progress)
        result["offline_error"] = 1.0  # Deliberate tie fixture, not an experimental outcome.
        return result
    monkeypatch.setattr(study, "run_case", tied_measurement)
    study._run_stage(folder, "validation", cases, methods, study.file_sha(folder / "shortlist.json"))
    selected = study.select_and_freeze(folder)
    assert selected["selected_program"]["native_id"] == "earlier"
    assert selected["selected_constant"] == 0
    assert all(proportions == [0, 0, 1, 0, 0, 0] for proportions in selected["control"]["distributions"].values())
    assert not (folder / "final_cases.json").exists()
    summary_before = (folder / "validation/summary.json").read_bytes()
    study._run_stage(folder, "validation", cases, methods, study.file_sha(folder / "shortlist.json"))
    assert (folder / "validation/summary.json").read_bytes() == summary_before
    assert study.select_and_freeze(folder) == selected


def test_shortlist_rejects_unfinished_or_wrong_task(tmp_path):
    search = tmp_path / "wrong"
    search.mkdir()
    atomic_json(search / "manifest.json", {"task": "adaptive_swarm", "status": "search_complete", "generation_target": 20})
    with pytest.raises(ValueError, match="completed 20-slot native allocation-v2"):
        study.freeze_shortlist(search, tmp_path / "target")
