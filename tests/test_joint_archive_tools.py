"""Portable saved-evidence tooling; fabricated files only, no objective calls."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

import pytest

from adaptive_swarms import joint_study as study
from adaptive_swarms.logging import atomic_json


ROOT = Path(__file__).resolve().parents[1]


def script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


audit_tool = script("audit_joint_progress")
analysis_tool = script("check_joint_analysis")


@pytest.fixture
def archive_fixture(tmp_path):
    source = tmp_path / "unavailable-original-location"
    live_study = source / "study"
    paths = {index: source / "evolution" / f"search_{index}_seed_{610001+index}" for index in range(3)}
    engine = tmp_path / "engine.json"
    atomic_json(engine, {"engine_config": {"profile_name": "fabricated_archive_fixture"}})
    registration = study.register_study(live_study, paths, engine)
    root = tmp_path / "published-copy"
    folder = root / "study"
    shutil.copytree(live_study, folder)
    for identity in registration["searches"]:
        run = root / "evolution" / Path(identity["run"]).name
        run.mkdir(parents=True)
        atomic_json(run / "manifest.json", {"run_dir": identity["run"], "task": "joint_relocation_v3",
            "evaluation_version": "joint_relocation_v3_score_reciprocal", "generation_target": 30,
            "search_seed": identity["search_seed"], "engine_config": registration["engine_config"], "status": "fixture_partial"})
        for name in registration["task_sources"]:
            target = run / "task_snapshot" / name
            target.parent.mkdir(exist_ok=True)
            target.write_bytes((folder / "runner_snapshot" / ("task__" + name)).read_bytes())
        code = "# Fabricated archival checkpoint; never executed.\n"
        (run / "gen_0").mkdir()
        (run / "gen_0/main.py").write_text(code)
        atomic_json(run / "gen_0/results/evaluation-checkpoint.json", {
            "status": "fixture_partial", "identity": {"program_sha256": hashlib.sha256(code.encode()).hexdigest()}})
        state = {"fabricated_fixture": True}
        state["sha256"] = audit_tool.digest(state)
        atomic_json(run / "gen_0/results/case_000.json", {
            "config": registration["search_cases"][0], "evaluations": 100000,
            "evaluation_counts": {"synthetic_placeholder": 100000}, "offline_error": 2.0,
            "response_log": [{"observation": {"swarm_size": 5}, "requested_count": 2,
                "allocated_count": 2, "relocated_indices": [0, 1], "adapter_encoding_fraction": .3,
                "requested_radius_scale": 1., "allocated_fraction": .4,
                "decision": {"radius_scale": 1., "memory": "reevaluate", "reset_velocity": False}, "completed": True}],
            "initial_environment": state, "environment_changes": []})
    shutil.rmtree(source)
    return root, folder, registration


def test_archive_audit_never_requires_original_paths_or_mutates_registration(archive_fixture):
    root, folder, registration = archive_fixture
    before = (folder / "registration.json").read_bytes()
    assert all(not Path(row["run"]).exists() for row in registration["searches"])
    result = audit_tool.audit(folder, archive_root=root)
    assert result["path_resolution"]["mode"] == "archive_only"
    assert result["totals"]["saved_case_executions"] == 3
    assert result["actions"]["simulations_launched"] == 0
    for original, resolved in zip(registration["searches"], result["searches"]):
        assert resolved["registered_run"] == original["run"]
        assert Path(resolved["run"]).parent == root / "evolution"
    assert (folder / "registration.json").read_bytes() == before
    assert study.verify_registration(folder) == registration


def test_archive_missing_search_refuses_live_fallback(archive_fixture):
    root, folder, registration = archive_fixture
    row = registration["searches"][0]
    archived = root / "evolution" / Path(row["run"]).name
    Path(row["run"]).parent.mkdir(parents=True)
    shutil.move(str(archived), row["run"])
    assert Path(row["run"]).is_dir()
    with pytest.raises(ValueError, match="missing or escapes"):
        audit_tool.audit(folder, archive_root=root)


def test_archive_mismatched_identity_and_escaped_search_fail(archive_fixture, tmp_path):
    root, folder, registration = archive_fixture
    run = root / "evolution" / Path(registration["searches"][0]["run"]).name
    path = run / "manifest.json"
    record = json.loads(path.read_text())
    atomic_json(path, {**record, "search_seed": -1})
    with pytest.raises(ValueError, match="mismatches registered"):
        audit_tool.audit(folder, archive_root=root)
    atomic_json(path, record)
    moved = tmp_path / "outside-archive"
    shutil.move(str(run), moved)
    run.symlink_to(moved, target_is_directory=True)
    with pytest.raises(ValueError, match="missing or escapes"):
        audit_tool.audit(folder, archive_root=root)


def test_archive_frozen_manifest_hash_is_checked(archive_fixture):
    root, folder, registration = archive_fixture
    atomic_json(folder / "shortlists.json", {"searches": [
        {"search_index": row["search_index"], "native_manifest_sha256": "0"*64}
        for row in registration["searches"]]})
    with pytest.raises(ValueError, match="differs from frozen shortlist"):
        audit_tool.audit(folder, archive_root=root)


def test_statistics_check_uses_saved_values_and_detects_interval_changes():
    # Two repeated measurements per regime suffice for a tiny pure-statistics
    # fixture. The public checker separately enforces the actual 80-case suite.
    configs = [{"dimension": 5, "npeaks": 10, "period": period, "move_severity": severity,
                "correlation": 0., "environment_seed": index, "optimizer_seed": 100+index}
               for index, (severity, period) in enumerate([r for r in study.REGIMES for _ in range(2)])]
    names = [*(f"winner_search_{i}" for i in range(3)), "baseline", "best_fixed", "radius_replaced", "count_replaced", "joint_sampler"]
    outcomes = {name: [{"config": config, "offline_error": 1.0 + method*.1 + index*.01}
                       for index, config in enumerate(configs)] for method, name in enumerate(names)}
    selection = {"overall_winner_method": names[0], "per_search_winners": [{"method": name} for name in names[:3]],
                 "analysis": study.analysis_specification()}
    manifest = {"cases": configs, "aliases": [], "case_artifacts": {name: [f"{name}_{i}" for i in range(8)] for name in names}}
    computed = analysis_tool.recompute_statistics(selection, manifest, outcomes)
    assert len(computed["comparisons"]) == 9
    assert sum(item["interval_level"] == .975 for item in computed["comparisons"].values()) == 2
    assert computed["interaction"]["interval_level"] == .95
    analysis_tool.require_match(deepcopy(computed), computed)
    corrupted = deepcopy(computed)
    corrupted["comparisons"]["winner_search_0_minus_baseline"]["bootstrap_interval"][1] += .01
    with pytest.raises(ValueError, match="bootstrap_interval"):
        analysis_tool.require_match(corrupted, computed)
