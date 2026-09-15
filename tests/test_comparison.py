"""Concrete pairing, freeze and resumability risks in independent comparisons."""
import copy
import json
from pathlib import Path

import pytest

from adaptive_swarms import comparison
from adaptive_swarms.simulator import run_case


def test_pairing_rejects_environment_and_budget_mismatch():
    baseline = run_case({"budget": 61, "period": 20, "environment_seed": 9001, "optimizer_seed": 9101})
    candidate = run_case(baseline["config"], policy=lambda observation: {"fraction": 0.0, "memory": "reset"})
    check = comparison.validate_pair(baseline, candidate)
    assert check["environment_hash_count"] == 4
    mismatched = copy.deepcopy(candidate)
    mismatched["environment_changes"][0]["next_environment"]["sha256"] = "different-history"
    with pytest.raises(ValueError, match="environmental histories"):
        comparison.validate_pair(baseline, mismatched)
    candidate["evaluation_counts"]["free_probe"] = 1
    with pytest.raises(ValueError, match="accounting"):
        comparison.validate_pair(baseline, candidate)


def test_frozen_program_resume_reuses_completed_method_case(tmp_path, monkeypatch):
    policy = tmp_path / "candidate.py"
    policy.write_text("def choose_response(observation):\n    return {'fraction': 0.0}\n")
    suite = tmp_path / "suite.json"
    suite.write_text(json.dumps({"budget": 41, "period": 20, "cases": [
        {"environment_seed": 9901, "optimizer_seed": 9911},
        {"environment_seed": 9902, "optimizer_seed": 9912}]}))
    folder = tmp_path / "comparison"
    comparison.freeze_programs(folder, policy, {}, {"reason": "synthetic runner diagnostic, not heldout data"})
    # Subsequent edits to the original source cannot alter frozen execution.
    policy.write_text("raise RuntimeError('must not execute mutable original')\n")
    original = comparison.run_case
    calls = []
    def fail_selected(config, policy=None, progress=None):
        calls.append((config["environment_seed"], policy is not None))
        if policy:
            raise RuntimeError("interrupted after baseline checkpoint")
        return original(config, policy, progress)
    monkeypatch.setattr(comparison, "run_case", fail_selected)
    with pytest.raises(RuntimeError, match="after baseline checkpoint"):
        comparison.run_comparison(folder, suite)
    assert (folder / "baseline/case_000.json.gz").exists()
    assert not (folder / "selected/case_000.json.gz").exists()
    calls.clear()
    def track(config, policy=None, progress=None):
        calls.append((config["environment_seed"], policy is not None))
        return original(config, policy, progress)
    monkeypatch.setattr(comparison, "run_case", track)
    summary = comparison.run_comparison(folder, suite, resume=True)
    assert calls == [(9901, True), (9902, False), (9902, True)]
    assert summary["paired_case_count"] == 2
    assert summary["status"] == "completed"
    assert all(case["matching_environment_hashes"] for case in summary["comparisons"]["selected_minus_baseline"]["cases"])
    frozen = json.loads((folder / "freeze.json").read_text())
    manifest = json.loads((folder / "manifest.json").read_text())
    assert frozen["frozen_at"] <= manifest["comparison_started_at"]
    (folder / "programs/selected.py").write_text("def choose_response(o): return {}\n")
    with pytest.raises(ValueError, match="Frozen source changed"):
        comparison.run_comparison(folder, suite, resume=True)


def test_stratified_uncertainty_preserves_fixed_regime_mix():
    # All uncertainty is between regimes, so fixed-regime resampling has zero
    # variance even though the unstratified sample SD is large.
    result = comparison._paired_statistics([-2, -2, 2, 2], ["a", "a", "b", "b"])
    assert result["mean_delta"] == 0
    assert result["sd_delta"] > 0
    assert result["stratified_se_delta"] == 0
    assert result["bootstrap_95_percent_interval"] == [0, 0]
    assert result["improved_cases"] == result["worsened_cases"] == 2
