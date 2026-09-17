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


def test_short_session_never_enables_final_selection(tmp_path, monkeypatch):
    module = load_controller()
    session = {'session_id':'synthetic','started_at':datetime.now(timezone.utc).isoformat(),
               'response_start':0,'terminal_descendants_start':0,'full_attempts_start':0}
    def counts(n):
        return {'logical_responses':0,'terminal_descendants':n,'terminal_generations':list(range(n+1))}
    research={'full_case_attempts':28,'attempts':[{'stage':'references','method':f'target_{k}','case_index':i,'status':'completed'} for k in range(2,9) for i in range(4)]}
    monkeypatch.setattr(module,'native_counts',lambda folder:counts(6))
    monkeypatch.setattr(module,'research_accounting',lambda folder:research)
    atomic_json(tmp_path/'references/execution_ledger.json',research)
    assert module.write_state(tmp_path,session,'research_paused')['final_selection_allowed'] is False
    monkeypatch.setattr(module,'native_counts',lambda folder:counts(50))
    assert module.write_state(tmp_path,session,'research_paused')['final_selection_allowed'] is True
    research['attempts'].pop()
    atomic_json(tmp_path/'references/execution_ledger.json',research)
    assert module.write_state(tmp_path,session,'research_paused')['final_selection_allowed'] is False


def test_proven_reused_controls_count_toward_completion_without_new_queries(tmp_path, monkeypatch):
    module=load_controller()
    session={'session_id':'synthetic','started_at':datetime.now(timezone.utc).isoformat(),
             'response_start':0,'terminal_descendants_start':0,'full_attempts_start':0}
    atomic_json(tmp_path/'references/execution_ledger.json',{'attempts':[
        {'method':f'target_{k}','case_index':i,'status':'reused','actual_queries':0,'reserved_queries':0}
        for k in range(2,9) for i in range(4)]})
    monkeypatch.setattr(module,'native_counts',lambda folder:{'logical_responses':0,'terminal_descendants':50,'terminal_generations':list(range(51))})
    state=module.write_state(tmp_path,session,'research_paused')
    assert state['final_selection_allowed'] and state['all_seven_constant_controls_complete']
    assert state['research']['full_case_attempts']==0


def test_constant_equivalence_is_structural_not_score_matching():
    load_controller()
    from population_campaign_controls import literal_constant_target
    assert literal_constant_target('"""label"""\ndef choose_neutral_count(observation) -> int:\n    """pure"""\n    return 2\n')==2
    for source in ['def choose_neutral_count(observation):\n return True',
                   'def choose_neutral_count(observation):\n return 2 if observation else 2',
                   'x=2\ndef choose_neutral_count(observation):\n return x',
                   'def choose_neutral_count(observation=2):\n return 2',
                   '@other\ndef choose_neutral_count(observation):\n return 2']:
        assert literal_constant_target(source) is None


def test_native_constant_copy_gap_recovers_without_evaluation(tmp_path, monkeypatch):
    load_controller()
    import population_campaign_controls as controls
    import sqlite3
    from adaptive_swarms.artifacts import write_compressed_json
    source='def choose_neutral_count(observation) -> int:\n    return 2\n'
    program=tmp_path/'programs/target_2.py'; program.parent.mkdir(); program.write_text(source)
    native=tmp_path/'evolution/search_seed_670001/gen_2'; results=native/'results';results.mkdir(parents=True)
    (native/'main.py').write_text(source); (native.parent/'search-suite.json').write_text('{}')
    identity={'scientific_sources':{},'program_sha256':controls.sha(program),
              'suite_sha256':controls.sha(native.parent/'search-suite.json'),
              'evaluation_version':'book_mpso_population_200_v2_reciprocal_v1','evaluator_sha256':'fixture'}
    completed=[{'case_id':f'case_{i:03d}','offline_error':1.0} for i in range(4)]
    atomic_json(results/'evaluation-checkpoint.json',{'status':'completed','identity':identity,'completed_cases':completed})
    atomic_json(results/'correct.json',{'correct':True})
    atomic_json(results/'metrics.json',{'public':{'cases_completed':4},'combined_score':0.5})
    attempts=[{'case_id':c['case_id'],'status':'completed','exact_objective_queries':500000,'reserved_objective_queries':500000} for c in completed]
    atomic_json(results/'execution-attempts.json',attempts)
    with sqlite3.connect(native.parent/'programs.sqlite') as db:
        db.execute('CREATE TABLE programs(id TEXT,code TEXT,correct INTEGER,combined_score REAL,generation INTEGER)')
        db.execute('INSERT INTO programs VALUES(?,?,?,?,?)',('synthetic',source,1,0.5,2))
    case={'case_id':'case_000','offline_error':1.0}
    write_compressed_json(results/'case_000.json.gz',case)
    write_compressed_json(tmp_path/'references/target_5/case_000.json.gz',case)
    manifest={'methods':{'target_2':{'source':'programs/target_2.py','sha256':controls.sha(program)}},
              'scientific_sources':{},'cases':[{}]*4,'frozen_contract_sources':{'tasks/book_mpso_population_200_v2/evaluate.py':'fixture'}}
    monkeypatch.setattr(controls,'validate_completed_case',lambda *args:None)
    monkeypatch.setattr(controls,'validate_pair',lambda *args:None)
    destination=tmp_path/'references/target_2/case_000.json.gz';ledger={'attempts':[]}
    assert controls.reuse_native_constant(tmp_path,manifest,'target_2',0,destination,ledger)
    original=destination.read_bytes()
    ledger={'attempts':[]}  # Atomic bytes reached disk before a lost ledger write.
    assert controls.reuse_native_constant(tmp_path,manifest,'target_2',0,destination,ledger)
    assert controls.reuse_native_constant(tmp_path,manifest,'target_2',0,destination,ledger)
    assert len(ledger['attempts'])==1 and ledger['attempts'][0]['actual_queries']==0
    assert destination.read_bytes()==original
    assert json.loads((results/'execution-attempts.json').read_text())==attempts
    assert research_accounting(tmp_path)['conservative_research_queries']==2000000
    destination.write_bytes(b'conflict')
    with pytest.raises(ValueError,match='differs from proven alias'):
        controls.reuse_native_constant(tmp_path,manifest,'target_2',0,destination,ledger)
