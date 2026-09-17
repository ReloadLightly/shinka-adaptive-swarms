"""Campaign/session boundaries using synthetic ledgers; no objective/model calls."""
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from adaptive_swarms.campaign_accounting import research_accounting, enforce_research_allowance
from adaptive_swarms.execution import InfrastructureError
from adaptive_swarms.logging import atomic_json
from adaptive_swarms.sprint_budget import LogicalResponseBudget, SprintLimitReached

ROOT = Path(__file__).resolve().parents[1]


def load_controller():
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("population_campaign_test_controller", ROOT / "scripts/run_population_campaign.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_conservative_research_counts_all_stages_and_preserves_partial(tmp_path):
    atomic_json(tmp_path / "references/execution_ledger.json", {"attempts": [
        {"status": "completed", "actual_queries": 500000, "reserved_queries": 500000},
        {"status": "reused", "actual_queries": 500000, "reserved_queries": 500000},
        {"status": "failed_or_interrupted", "exact_partial_queries": 17, "reserved_queries": 500000},
    ]})
    atomic_json(tmp_path / "fresh/execution_ledger.json", {"attempts": [
        {"status": "running", "last_reported_queries": 50, "reserved_queries": 500000},
    ]})
    atomic_json(tmp_path / "evolution/search_seed_670001/gen_1/results/execution-attempts.json", [
        {"status": "completed", "exact_objective_queries": 500000, "reserved_objective_queries": 500000},
        {"status": "failed", "exact_objective_queries": 31, "reserved_objective_queries": 500000},
    ])
    state = research_accounting(tmp_path)
    assert state["full_case_attempts"] == 5
    assert state["completed_full_cases"] == 2
    assert state["known_completed_queries"] == 1000000
    assert state["conservative_research_queries"] == 2500000


def test_research_ceiling_counts_reserved_attempt_even_if_queries_unknown(tmp_path):
    atomic_json(tmp_path / "references/execution_ledger.json", {"attempts": [
        {"status": "running", "reserved_queries": 500000} for _ in range(399)]})
    assert enforce_research_allowance(tmp_path, additional_cases=1)["full_case_attempts"] == 399
    with pytest.raises(InfrastructureError, match="allowance exhausted"):
        enforce_research_allowance(tmp_path, additional_cases=2)


def test_session_response_delta_is_separate_from_immutable_400_limit(tmp_path):
    atomic_json(tmp_path / "engine_calls/previous.json", {"requested_logical_responses": 100})
    budget = LogicalResponseBudget(tmp_path, 400, session_limit=80, session_start=100)
    receipt = {"requested_logical_responses": 80, "role": "mutation", "call_id": "synthetic"}
    budget.reserve(tmp_path / "engine_calls/current.json", receipt, 80)
    assert budget.used == 180 and budget.limit == 400
    with pytest.raises(SprintLimitReached):
        budget.reserve(tmp_path / "engine_calls/declined.json", {"role": "meta", "call_id": "declined"}, 1)
    assert not (tmp_path / "engine_calls/declined.json").exists()
    next_session = LogicalResponseBudget(tmp_path, 400, session_limit=80, session_start=180)
    assert next_session.used == 180 and next_session.limit == 400


def test_controller_native_command_has_campaign_and_session_limits(tmp_path, monkeypatch):
    module = load_controller()
    deadline = datetime.now(timezone.utc) + timedelta(minutes=70)
    session = {"session_id": "synthetic", "deadline_utc": deadline.isoformat(),
               "research_deadline_utc": deadline.isoformat(), "response_start": 20,
               "session_stop_generation": 7}
    monkeypatch.setattr(module, "session_record", lambda *args: session)
    monkeypatch.setattr(module, "register", lambda *args: None)
    monkeypatch.setattr(module, "freeze_suite", lambda *args: None)
    monkeypatch.setattr(module, "forecast", lambda *args: {
        "affordable_serial_descendants_now": 3, "conservative_case_seconds": 150,
        "complete_descendant_admission_seconds": 1200})
    monkeypatch.setattr(module, "enforce_research_allowance", lambda *args, **kwargs: None)
    monkeypatch.setattr(module, "write_state", lambda *args: None)
    commands = []
    monkeypatch.setattr(module.subprocess, "run", lambda command, **kwargs:
                        commands.append(command) or SimpleNamespace(returncode=0))
    module.run_session(tmp_path, SimpleNamespace(stage="search", limit_cases=None))
    command = commands[0]
    for option, value in (("--generations", "51"), ("--logical-response-limit", "400"),
                          ("--session-response-limit", "80"), ("--session-response-start", "20"),
                          ("--session-max-descendants", "6"), ("--session-stop-generation", "7"),
                          ("--model", "gpt-6-astra"), ("--effort", "xhigh")):
        assert command[command.index(option) + 1] == value
    assert "--run-dir" in command


def test_existing_session_resume_does_not_reset_allowances(tmp_path):
    module = load_controller()
    args = SimpleNamespace(new_session=False, started_at=None, minutes=180)
    original = module.session_record(tmp_path, args)
    atomic_json(tmp_path / "evolution/search_seed_670001/engine_calls/synthetic.json",
                {"role": "mutation", "requested_logical_responses": 70})
    assert module.session_record(tmp_path, args) == original
    assert original["response_start"] == 0
    assert original["session_stop_generation"] == 7
    args.new_session = True
    with pytest.raises(RuntimeError, match="not published/closed"):
        module.session_record(tmp_path, args)


def test_development_histories_preserved_exactly():
    old = json.loads((ROOT / "artifacts/book_mpso_population_200_v1/20260917T025219Z/development_cases.json").read_text())
    new = json.loads((ROOT / "configs/book_mpso_population_200_v2/development.json").read_text())
    assert new["cases"] == old["cases"]
    assert new["results_reused"] is False
