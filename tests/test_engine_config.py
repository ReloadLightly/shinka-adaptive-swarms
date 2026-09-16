"""Profiles must reach native settings and survive resume without changing roles."""
import asyncio
import importlib.util
import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from adaptive_swarms.engine_config import (
    build_engine, check_embedding_endpoint, feature_state, native_settings, resolve_engine,
)
from adaptive_swarms.engine_runtime import install_engine_observers
from adaptive_swarms.engine_progress import terminal_failure_generations
from adaptive_swarms.storage_runner import ResumeRunnerMixin
from adaptive_swarms.logging import EventLogger

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "configs/shinka/research_v3.json"
EMBEDDING = "local/test-embedding@http://127.0.0.1:8766/v1"


def load_launcher():
    spec = importlib.util.spec_from_file_location("engine_launcher_test", ROOT / "scripts/run_evolution.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_research_profile_activates_native_roles_and_preserves_historical_default():
    legacy = build_engine()
    assert legacy["evolution"]["meta_llm_models"] is None
    assert legacy["evolution"]["embedding_model"] is None
    assert legacy["database"]["migration_rate"] == 0
    rich = resolve_engine(profile_path=PROFILE, effort="xhigh", embedding_model=EMBEDDING)
    evolution, database = native_settings(rich)
    for role in ("llm_models", "meta_llm_models", "novelty_llm_models"):
        assert evolution[role] == ["headless/codex@gpt-6-astra?effort=xhigh"]
    assert evolution["meta_rec_interval"] == 5
    assert evolution["max_novelty_attempts"] == 3
    assert database["migration_rate"] == 0.1
    assert database["parent_selection_strategy"] == "weighted"
    assert evolution["patch_type_probs"] == legacy["evolution"]["patch_type_probs"]
    # Instantiate actual pinned dataclasses when the optional native dependency
    # is installed, without constructing clients or making inference calls.
    pytest.importorskip("shinka")
    from shinka.core.config import EvolutionConfig
    from shinka.database import DatabaseConfig
    assert EvolutionConfig(**evolution).novelty_llm_models == evolution["novelty_llm_models"]
    assert DatabaseConfig(**database).migration_rate == 0.1


def test_requested_novelty_and_subscription_routes_do_not_fall_back():
    with pytest.raises(ValueError, match="needs --embedding-model"):
        resolve_engine(profile_path=PROFILE)
    for forbidden in ("text-embedding-3-small", "local/test@https://api.example.com/v1"):
        with pytest.raises(ValueError):
            resolve_engine(profile_path=PROFILE, embedding_model=forbidden)
    definition = json.loads(PROFILE.read_text())
    definition["evolution"]["meta_llm_models"] = ["gpt-6-astra"]
    with pytest.raises(ValueError, match="subscription routes"):
        build_engine(definition, embedding_model=EMBEDDING)
    with pytest.raises(ValueError, match="Unsupported inner Codex effort"):
        build_engine(effort="ultra")


def test_adaptive_selector_requires_explicit_distinct_pool():
    definition = {"schema_version": 1, "name": "two-model", "evolution": {"llm_dynamic_selection": "ucb"}}
    with pytest.raises(ValueError, match="at least two"):
        build_engine(definition)
    definition["evolution"]["llm_models"] = ["$codex", "headless/codex@second-model?effort=high"]
    result = build_engine(definition)
    assert feature_state(result)["model_selection"] == "ucb"
    assert len(feature_state(result)["model_roles"]["mutation"]) == 2


def test_resume_inherits_frozen_profile_and_rejects_changes(tmp_path):
    rich = resolve_engine(profile_path=PROFILE, embedding_model=EMBEDDING, effort="high")
    saved = {"engine_config": rich}
    assert resolve_engine(saved_manifest=saved) == rich
    assert resolve_engine(profile_path=PROFILE, saved_manifest=saved) == rich
    with pytest.raises(ValueError, match="differ from the saved run"):
        resolve_engine(saved_manifest=saved, effort="xhigh")
    with pytest.raises(ValueError, match="differ from the saved run"):
        resolve_engine(saved_manifest=saved, embedding_model=EMBEDDING.replace("8766", "8767"))
    changed = json.loads(PROFILE.read_text())
    changed["database"]["migration_rate"] = 0.2
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="differ from the saved run"):
        resolve_engine(profile_path=path, saved_manifest=saved)
    saved["engine_config"]["evolution"]["max_novelty_attempts"] = 4
    with pytest.raises(ValueError, match="hash differs"):
        resolve_engine(saved_manifest=saved)


def test_historical_resume_keeps_its_previous_inner_model_and_effort():
    saved = {"model_requested": "gpt-6-astra", "inner_effort_requested": "high"}
    resolved = resolve_engine(saved_manifest=saved)
    assert resolved["profile_name"] == "historical"
    assert resolved["evolution"]["llm_models"] == ["headless/codex@gpt-6-astra?effort=high"]
    with pytest.raises(ValueError, match="differ from the saved run"):
        resolve_engine(profile_path=PROFILE, embedding_model=EMBEDDING, saved_manifest=saved)


def test_seed_only_disables_all_model_roles_without_losing_search_intent(monkeypatch):
    rich = resolve_engine(profile_path=PROFILE, embedding_model=EMBEDDING)
    state = feature_state(rich, seed_only=True)
    assert all(not roles for roles in state["model_roles"].values())
    assert not state["meta_configured"] and not state["novelty_configured"]
    assert rich["evolution"]["meta_rec_interval"] == 5
    monkeypatch.setattr("socket.create_connection", lambda *a, **k: pytest.fail("No listener check is needed for seed-only mode"))
    assert check_embedding_endpoint(rich, seed_only=True) == {"required": False, "model_calls": 0}


def test_missing_embedding_listener_is_explicit(monkeypatch):
    rich = resolve_engine(profile_path=PROFILE, embedding_model=EMBEDDING)
    def refused(*args, **kwargs):
        raise ConnectionRefusedError("not serving")
    monkeypatch.setattr("socket.create_connection", refused)
    with pytest.raises(RuntimeError, match="will not be disabled"):
        check_embedding_endpoint(rich)


def test_config_print_creates_no_run_and_makes_no_runtime_calls(tmp_path, monkeypatch, capsys):
    launcher = load_launcher()
    monkeypatch.setattr(launcher, "inspect_runtime", lambda *a: pytest.fail("No runtime calls"))
    monkeypatch.setattr("sys.argv", ["run_evolution.py", "--task", "joint_relocation_v3", "--engine-profile", str(PROFILE),
                                    "--embedding-model", EMBEDDING, "--print-engine-config", "--results-root", str(tmp_path / "runs")])
    assert launcher.main() == 0
    output = json.loads(capsys.readouterr().out)
    assert output["task"] == "joint_relocation_v3"
    assert output["features"]["meta_configured"] and output["model_calls"] == 0
    assert not (tmp_path / "runs").exists()


def test_resume_mismatch_is_rejected_before_run_log_mutation(tmp_path, monkeypatch):
    launcher = load_launcher()
    (tmp_path / "programs.sqlite").touch()
    manifest = {"model_requested": "gpt-6-astra", "inner_effort_requested": None}
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    before = path.read_bytes()
    monkeypatch.setattr("sys.argv", ["run_evolution.py", "--resume", str(tmp_path), "--engine-profile", str(PROFILE), "--embedding-model", EMBEDDING])
    with pytest.raises(SystemExit) as exc:
        launcher.main()
    assert exc.value.code == 2
    assert path.read_bytes() == before
    assert not (tmp_path / "run.log").exists()


class FakeClient:
    model_names = ["headless/codex@test"]

    async def query(self, *args, **kwargs):
        return None

    async def batch_kwargs_query(self, *args, **kwargs):
        return []


def test_missing_novelty_response_is_logged_without_changing_native_fallback(tmp_path):
    client = FakeClient()
    def fail(error):
        raise error
    runner = SimpleNamespace(llm=FakeClient(), meta_summarizer=None, embedding_client=None,
                             _fail_infrastructure=fail,
                             novelty_judge=SimpleNamespace(async_llm_client=client,
                                 assess_novelty_with_rejection_sampling_async=client.query))
    with EventLogger(tmp_path, heartbeat_seconds=20) as log:
        install_engine_observers(runner, log, tmp_path)
        assert asyncio.run(client.query(msg="candidate code", system_msg="novelty instructions")) is None
    receipt = json.loads(next((tmp_path / "engine_calls").glob("*.json")).read_text())
    assert receipt["role"] == "novelty" and receipt["valid_responses"] == 0
    assert receipt["system_msg"] == "novelty instructions"
    events = [json.loads(line)["event"] for line in (tmp_path / "events.jsonl").read_text().splitlines()]
    assert "engine_role_call_start" in events and "engine_feature_degraded" in events
    assert receipt["status"] == "degraded"


def test_empty_embedding_preserves_native_behavior_with_explicit_degradation(tmp_path):
    async def embedding(program):
        return [], 0.0
    def fail(error):
        raise error
    runner = SimpleNamespace(llm=FakeClient(), meta_summarizer=None, novelty_judge=None,
                             embedding_client=object(), _get_code_embedding_async=embedding, _fail_infrastructure=fail)
    with EventLogger(tmp_path, heartbeat_seconds=20) as log:
        install_engine_observers(runner, log, tmp_path)
        assert asyncio.run(runner._get_code_embedding_async("initial.py")) == ([], 0.0)
    events = [json.loads(line) for line in (tmp_path / "events.jsonl").read_text().splitlines()]
    assert any(event["event"] == "engine_feature_degraded" and event["role"] == "embedding" for event in events)


def test_terminal_novelty_failure_finishes_slot_without_claiming_evaluation(tmp_path):
    launcher = load_launcher()
    with sqlite3.connect(tmp_path / "programs.sqlite") as database:
        database.execute("CREATE TABLE programs(generation INTEGER, correct INTEGER, combined_score REAL, metadata TEXT)")
        database.executemany("INSERT INTO programs VALUES (?, ?, ?, ?)", [(0, 1, .2, "{}"), (0, 1, .2, '{"_is_island_copy": true}'), (2, 0, 0., "{}")])
        database.execute("CREATE TABLE attempt_log(generation INTEGER, status TEXT, details TEXT)")
        database.execute("INSERT INTO attempt_log VALUES (1, 'failed', ?)", (json.dumps({"node_kind": "failed_proposal", "downstream_eval_submitted": False}),))
        database.execute("INSERT INTO attempt_log VALUES (3, 'failed', ?)", (json.dumps({"node_kind": "patch_attempt"}),))
    summary = launcher.summarize_database(tmp_path)
    assert summary["generation_records"] == 2
    assert summary["evaluated_programs"] == 2
    assert summary["valid_programs"] == 1 and summary["valid_descendants"] == 0
    assert summary["terminal_generation_ids"] == [0, 1, 2]
    assert summary["terminal_failed_generation_ids"] == [1]


def test_terminal_failure_identity_and_resume_preservation(tmp_path):
    folder = tmp_path / "gen_1"
    folder.mkdir()
    record = {"generation": 1, "node_kind": "failed_proposal", "downstream_eval_submitted": False,
              "failure_stage": "novelty", "failure_reason": "All novelty attempts rejected"}
    failure = folder / "failure.json"
    failure.write_text(json.dumps(record))
    original = failure.read_bytes()
    assert terminal_failure_generations(tmp_path) == {1}

    class Database:
        async def get_persisted_generation_ids_async(self):
            return [0]

    runner = ResumeRunnerMixin()
    runner.results_dir = str(tmp_path)
    runner.async_db = Database()
    runner.evo_config = SimpleNamespace(num_generations=3)
    runner.next_generation_to_submit = 1
    runner.db = object()
    with EventLogger(tmp_path, heartbeat_seconds=20) as log:
        runner.resume_log = log
        asyncio.run(runner._restore_pending_jobs())
    assert runner.next_generation_to_submit == 2
    assert failure.read_bytes() == original
    assert not (tmp_path / "interrupted_proposals").exists()
    record["generation"] = 2
    failure.write_text(json.dumps(record))
    with pytest.raises(RuntimeError, match="disagrees"):
        terminal_failure_generations(tmp_path)


def test_resume_assignment_skips_retained_terminal_slots():
    class Native:
        async def _start_proposals(self, count):
            self.assigned.append(self.next_generation_to_submit)
            self.next_generation_to_submit += count

    class Runner(ResumeRunnerMixin, Native):
        pass

    runner = Runner()
    runner._preserved_terminal_failures = {2, 3}
    runner.next_generation_to_submit = 1
    runner.assigned = []
    asyncio.run(runner._start_proposals(2))
    assert runner.assigned == [1, 4]
