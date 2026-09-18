#!/usr/bin/env python3
"""One user-launched 180-minute session of the corrected 50-slot campaign."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import fcntl
import importlib.metadata
import json
import math
import os
import platform
from pathlib import Path
import sqlite3
import statistics
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from adaptive_swarms.artifacts import read_json
from adaptive_swarms.campaign_accounting import research_accounting, enforce_research_allowance
from adaptive_swarms.engine_progress import terminal_failure_generations
from adaptive_swarms.logging import atomic_json, EventLogger
from population_campaign_controls import register, execute, freeze_suite, sha

TASK='book_mpso_population_200_v2'
SEARCH_SEED=670001


def utcnow(): return datetime.now(timezone.utc)


def verify_numerical_runtime(folder):
    """A resumed campaign must use its recorded optimizer runtime, not the encoder's."""
    path=folder/'operations/numerical-runtime.json'
    if not path.exists():
        if (folder/'session.json').exists():
            raise RuntimeError('Resumed campaign lacks its recorded numerical-runtime.json; restore it before launch')
        return None
    expected=read_json(path)
    actual={'python':platform.python_version(),
            'numpy':importlib.metadata.version('numpy'),
            'shinka_evolve':importlib.metadata.version('shinka-evolve')}
    mismatches={key:{'recorded':expected.get(key),'installed':value}
                for key,value in actual.items() if expected.get(key)!=value}
    if mismatches:
        raise RuntimeError(f'Optimizer runtime differs from the saved campaign: {mismatches}. Restore the recorded runtime before any model/evaluation calls; the local embedding service has a separate runtime.')
    return actual


def native_counts(folder):
    run=folder/f'evolution/search_seed_{SEARCH_SEED}'
    receipts=[read_json(p) for p in (run/'engine_calls').glob('*.json')]
    roles=Counter()
    for row in receipts: roles[row['role']]+=row['requested_logical_responses']
    rows=[]
    if (run/'programs.sqlite').exists():
        with sqlite3.connect(f'file:{run/"programs.sqlite"}?mode=ro',uri=True) as db:
            db.row_factory=sqlite3.Row
            rows=[dict(r) for r in db.execute('SELECT id,generation,correct,combined_score FROM programs')]
    failures=terminal_failure_generations(run)
    terminal={r['generation'] for r in rows}|failures
    allocated={int(p.name[4:]) for p in run.glob('gen_*') if p.is_dir() and p.name[4:].isdigit()} | terminal
    return {'logical_responses':sum(roles.values()),'model_role_counts':dict(roles),
            'terminal_generations':sorted(terminal),'terminal_descendants':len(terminal-{0}),
            'valid_descendants':sum(bool(r['correct']) and r['generation']>0 for r in rows),
            'failed_descendants':len(failures | {r['generation'] for r in rows if not r['correct'] and r['generation']>0}),
            'programs':rows,'attempted_descendant_generations':sorted(allocated-{0}),
            'pending_generations':sorted(allocated-terminal),
            'accepted_pending_generations':[int(p.parent.name[4:]) for p in run.glob('gen_*/storage-job.json') if int(p.parent.name[4:]) not in terminal]}


def write_state(folder, session, status):
    native=native_counts(folder); research=research_accounting(folder)
    reference_ledger=folder/'references/execution_ledger.json'
    control_records=read_json(reference_ledger)['attempts'] if reference_ledger.exists() else []
    controls={(a.get('method'),a.get('case_index')) for a in control_records if a['status'] in {'completed','reused'}}
    all_controls={(f'target_{k}',i) for k in range(2,9) for i in range(4)}.issubset(controls)
    all_slots=set(range(51)).issubset(native['terminal_generations'])
    development_complete=all_controls and all_slots
    state={'schema':'population-campaign-state-v2','updated_at':utcnow().isoformat(),
           'campaign_status':'development_complete_awaiting_final_analysis' if development_complete else 'in_progress','session_status':status,'session_id':session['session_id'],
           'campaign_descendant_limit':50,'campaign_response_limit':400,'campaign_full_attempt_limit':400,
           'campaign_query_limit':200000000,'session_descendant_limit':6,'session_response_limit':80,
           'elapsed_wall_seconds':(utcnow()-datetime.fromisoformat(session['started_at'])).total_seconds(),
           'session_native_responses':native['logical_responses']-session['response_start'],
           'session_terminal_descendants':native['terminal_descendants']-session['terminal_descendants_start'],
           'session_new_full_attempts':research['full_case_attempts']-session['full_attempts_start'],
           'fixture_queries_separate':401,'native':native,'research':research,
           'all_seven_constant_controls_complete':all_controls,'all_50_descendant_slots_terminal':all_slots,
           'final_selection_allowed':development_complete,'fresh_testing_allowed_this_session':False}
    atomic_json(folder/'campaign_state.json',state)
    atomic_json(folder/'sessions'/session['session_id']/'state.json',state)
    return state


def session_record(folder,args):
    path=folder/'session.json'
    if path.exists() and not args.new_session:
        record=read_json(path)
        if utcnow()>=datetime.fromisoformat(record['deadline_utc']):
            raise RuntimeError('Existing session has expired; a later user launch must explicitly use --new-session')
        return record
    if path.exists() and read_json(path).get('status')!='published':
        raise RuntimeError('Previous session is not published/closed; resume it rather than reset its allowance')
    start=datetime.fromisoformat(args.started_at.replace('Z','+00:00')) if args.started_at else utcnow()
    session_id=f'session_{len(list((folder/"sessions").glob("session_*")))+1:03d}'
    native=native_counts(folder); research=research_accounting(folder)
    record={'session_id':session_id,'started_at':start.isoformat(),'minutes':args.minutes,
            'deadline_utc':(start+timedelta(minutes=args.minutes)).isoformat(),
            'research_deadline_utc':(start+timedelta(minutes=args.minutes-20)).isoformat(),
            'status':'active','response_start':native['logical_responses'],
            'terminal_descendants_start':native['terminal_descendants'],
            'full_attempts_start':research['full_case_attempts'],
            'session_stop_generation':min(51,1+native['terminal_descendants']+6),
            'outer_model_requested':'GPT-6 Astra / Ultra if selected in client',
            'outer_actual':'Client-selected model/effort not programmatically exposed; not changed by this controller',
            'inner_model':'gpt-6-astra','inner_effort':'xhigh','authentication':'subscription only'}
    atomic_json(path,record);atomic_json(folder/'sessions'/session_id/'session.json',record)
    return record


def forecast(folder,session):
    ledger=read_json(folder/'references/execution_ledger.json')
    # UTC wall clock governs admission; retain monotonic timing separately.
    durations=[max(a.get('elapsed_seconds',0),(datetime.fromisoformat(a['completed_at'])-datetime.fromisoformat(a['started_at'])).total_seconds()) for a in ledger['attempts'] if a['status']=='completed']
    if not durations: raise RuntimeError('First planned corrected reference case must finish before forecasting')
    historical=ROOT/'artifacts/book_mpso_population_v1/20260916T183731Z/evolution/search_seed_650001/engine_calls'
    latencies=[read_json(p).get('elapsed_seconds',0) for p in historical.glob('*.json')]
    conservative_case=max(durations)*1.35
    model_allowance=max(360.,3*max(latencies,default=120.))
    admission=4*conservative_case+model_allowance+120
    remaining=(datetime.fromisoformat(session['research_deadline_utc'])-utcnow()).total_seconds()
    result={'computed_at':utcnow().isoformat(),'first_case_seconds':durations[0],
            'observed_case_seconds':durations,'conservative_case_seconds':conservative_case,
            'historical_max_native_wrapper_seconds':max(latencies,default=None),
            'mutation_novelty_meta_allowance_seconds':model_allowance,'drain_seconds':120,
            'complete_descendant_admission_seconds':admission,'research_seconds_remaining':remaining,
            'affordable_serial_descendants_now':max(0,min(6,int(remaining//admission))),
            'campaign_remaining_case_runtime_hours_at_conservative_rate':max(0,378-research_accounting(folder)['completed_full_cases'])*conservative_case/3600,
            'note':'Feasibility uses elapsed time and recorded latency, never reference scores; future campaign/fresh work need not fit this session.'}
    atomic_json(folder/'sessions'/session['session_id']/'runtime_forecast.json',result)
    return result


def run_session(folder,args):
    folder.mkdir(parents=True,exist_ok=True)
    runtime=verify_numerical_runtime(folder)
    with (folder/'campaign-controller.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        lock.seek(0);lock.truncate();lock.write(str(os.getpid()));lock.flush()
        session=session_record(folder,args)
        with EventLogger(folder/'operations') as log:
            log.event('session_controller_start',session_id=session['session_id'],stage=args.stage,deadline=session['deadline_utc'])
            if runtime: log.event('numerical_runtime_verified',**runtime)
            register(folder)
            log.set_activity('waiting for corrected control cases; details in references/run.log')
            if args.stage in ('session','controls'):
                execute(folder,args.limit_cases,targets=tuple(int(k) for k in args.control_targets.split(',')))
                timing=forecast(folder,session)
                log.event('runtime_forecast',**timing)
                write_state(folder,session,'controls_checkpoint')
                if args.stage=='controls': return
                ledger=read_json(folder/'references/execution_ledger.json')
                complete=sum(a['status']=='completed' and a['method'] in {'target_3','target_5'} for a in ledger['attempts'])
                if complete!=8:
                    log.event('research_pause',reason='Corrected controls incomplete; checkpoint retained without native selection')
                    write_state(folder,session,'controls_incomplete_pause'); return
            freeze_suite(folder)
            timing=forecast(folder,session)
            if timing['affordable_serial_descendants_now']<1:
                log.event('research_pause',reason='A full candidate and drain no longer fit; campaign remains open')
                write_state(folder,session,'runtime_constrained_pause'); return
            enforce_research_allowance(folder,additional_cases=4)
            native=folder/f'evolution/search_seed_{SEARCH_SEED}'
            remaining=(datetime.fromisoformat(session['research_deadline_utc'])-utcnow()).total_seconds()
            eval_seconds=min(int(4*timing['conservative_case_seconds']+120),int(remaining-60))
            timeout=f'{eval_seconds//3600:02d}:{(eval_seconds%3600)//60:02d}:{eval_seconds%60:02d}'
            command=[str(ROOT/'.venv/bin/python'),str(ROOT/'scripts/run_evolution.py'),
                     '--task',TASK,'--generations','51','--logical-response-limit','400',
                     '--session-max-descendants','6','--session-stop-generation',str(session['session_stop_generation']),
                     '--session-response-limit','80','--session-response-start',str(session['response_start']),
                     '--session-deadline-utc',session['research_deadline_utc'],
                     '--admission-seconds',str(timing['complete_descendant_admission_seconds']),
                     '--admission-overhead-seconds',str(timing.get('mutation_novelty_meta_allowance_seconds',360)+timing.get('drain_seconds',120)),
                     '--model','gpt-6-astra','--effort','xhigh',
                     '--engine-profile',str(ROOT/f'configs/shinka/{TASK}.json'),
                     '--embedding-model','local/jina-code-v2-q8@http://127.0.0.1:8910/v1',
                     '--search-seed',str(SEARCH_SEED),'--suite',str(folder/'search_suite.json'),
                     '--evaluation-timeout',timeout,'--proposal-timeout-seconds',str(min(600,int(remaining-60))),
                     '--resume' if (native/'manifest.json').exists() else '--run-dir',str(native)]
            atomic_json(folder/'sessions'/session['session_id']/'native_command.json',{'command':command,'recorded_at':utcnow().isoformat(),'forecast':timing})
            log.event('native_launch',command=command,admission_seconds=timing['complete_descendant_admission_seconds'])
            write_state(folder,session,'native_running')
            log.set_activity('native evolution owns proposal/evaluation; waiting for flushed child progress')
            result=subprocess.run(command,cwd=ROOT,check=False)
            log.event('native_return',exit_code=result.returncode)
            write_state(folder,session,'research_paused' if result.returncode==0 else 'infrastructure_review_required')
            if result.returncode: raise SystemExit(result.returncode)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['session','status'])
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--minutes',type=int,default=180)
    p.add_argument('--new-session',action='store_true')
    p.add_argument('--started-at')
    p.add_argument('--stage',choices=['session','controls','search'],default='session')
    p.add_argument('--limit-cases',type=int)
    p.add_argument('--control-targets',default='5,3',help='Comma-separated registered constant targets; default Session1 controls5/3, later sessions may finish2,4,6,7,8')
    args=p.parse_args()
    if args.minutes!=180: p.error('Registered sessions use a 180-minute ceiling')
    if not args.control_targets or any(k not in set('2345678') for k in args.control_targets.split(',')):
        p.error('Control targets must be integers2..8')
    folder=args.run.resolve()
    if args.command=='status': print(json.dumps(write_state(folder,read_json(folder/'session.json'),'inspection'),indent=2))
    else: run_session(folder,args)

if __name__=='__main__':main()
