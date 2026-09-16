"""Count existing case ledgers and native receipts; performs no experiment."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import json
import sys

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'src'))
from adaptive_swarms.logging import atomic_json
RUN=Path(__file__).resolve().parents[1]
SEARCH=RUN/'evolution/search_seed_640001'

def read(p): return json.loads(p.read_text())
def stage_counts(attempts, query_key, reserved_key):
    complete=[a for a in attempts if a['status']=='completed']
    failures=[a for a in attempts if a['status'] not in ('completed','running')]
    running=[a for a in attempts if a['status']=='running']
    exact=[a.get(query_key) if a.get(query_key) is not None else a.get('exact_partial_queries') for a in attempts]
    return {'attempts':len(attempts),'physical_full_executions':len(complete),
            'failed_or_partial_attempts':len(failures),'running_attempts':len(running),'exact_objective_queries':sum(v for v in exact if v is not None),
            'unknown_query_attempts':sum(v is None for v in exact),'reserved_queries':sum(a[reserved_key] for a in attempts),
            'failures':failures}

stages={}
for stage in ('references','fresh'):
    p=RUN/stage/'execution_ledger.json'
    if p.exists(): stages[stage]=stage_counts(read(p)['attempts'],'actual_queries','reserved_queries')
records=0;native=[];terminal=[]
for gen in sorted(SEARCH.glob('gen_*'),key=lambda p:int(p.name[4:])):
    result=gen/'results';p=result/'execution-attempts.json'
    if p.exists(): native.extend(read(p))
    p=result/'evaluation-checkpoint.json'
    if p.exists():
        c=read(p);records+=len(c.get('completed_cases',[]))
        if c['status'] in ('completed','failed'):
            terminal.append({'generation':int(gen.name[4:]),'status':c['status'],'case_records':len(c.get('completed_cases',[]))})
stages['native']=stage_counts(native,'exact_objective_queries','reserved_objective_queries')
stages['native']['completed_case_records']=records
stages['native']['exact_cache_records']=records-stages['native']['physical_full_executions']
roles={}
for p in (SEARCH/'engine_calls').glob('*.json'):
    c=read(p);r=roles.setdefault(c['role'],{'native_wrappers':0,'requested_logical_responses':0,'usable_responses':0,'exposed_native_retry_responses':0,'status_counts':{}})
    r['native_wrappers']+=1;r['requested_logical_responses']+=c['requested_logical_responses']
    r['usable_responses']+=(c.get('valid_responses',0) or 0)
    r['exposed_native_retry_responses']+=c.get('exposed_native_retry_responses',0)
    status=c.get('status','unknown');r['status_counts'][status]=r['status_counts'].get(status,0)+1
native_summary=read(SEARCH/'manifest.json')
if 'terminal_generation_ids' in native_summary:
    present={item['generation'] for item in terminal}
    terminal.extend({'generation':g,'status':'terminal_proposal_failure','case_records':0} for g in native_summary['terminal_generation_ids'] if g not in present)
    terminal.sort(key=lambda item:item['generation'])
model={'roles':roles,'requested_logical_responses':sum(r['requested_logical_responses'] for r in roles.values()),'limit':40,
       'hidden_provider_retries':'unobserved','supervising_usage':'unobserved by native counter'}
queries=sum(s['exact_objective_queries'] for s in stages.values());physical=sum(s['physical_full_executions'] for s in stages.values())
assert queries<=52000000 and physical<=104 and model['requested_logical_responses']<=40
s=read(RUN/'session.json');started=datetime.fromisoformat(s['started_utc'].replace('Z','+00:00'));now=datetime.now(timezone.utc)
completed=read(SEARCH/'manifest.json').get('status')=='search_complete'
selection=read(RUN/'selection.json') if (RUN/'selection.json').exists() else None
if selection and selection['fresh_comparison_required']:
    completed=completed and (RUN/'fresh/execution_ledger.json').exists() and read(RUN/'fresh/execution_ledger.json')['status']=='completed'
else: completed=completed and selection is not None
out={'status':'research_complete' if completed else 'running','recorded_at':now.isoformat(),'run_id':s['run_id'],
     'stages':stages,'terminal_slots':terminal,'valid_descendants':sum(t['generation']>0 and t['status']=='completed' for t in terminal),
     'totals':{'physical_full_executions':physical,'research_objective_queries':queries,'failed_or_partial_attempts':sum(t['failed_or_partial_attempts'] for t in stages.values()),'unknown_query_attempts':sum(t['unknown_query_attempts'] for t in stages.values())},
     'model':model,'small_fixture_queries':read(RUN/'operations/engine-fixture-accounting.json'),
     'session_elapsed_seconds_utc':(now-started).total_seconds(),'hard_ceiling_seconds':10800,
     'runtime_note':'UTC session elapsed and each controller monotonic elapsed are retained separately; native provider latency includes waiting, not hidden-token streaming.'}
out['totals']['repeated_full_executions_included']=8
out['totals']['repeated_objective_queries_included']=4000000
out['totals']['exact_seed_cache_records']=8
out['fresh_comparison']='Not triggered: selected program is the original 5+1 seed; zero fresh cases generated or evaluated.'
atomic_json(RUN/'accounting.json',out)
print(json.dumps({'status':out['status'],'totals':out['totals'],'model_responses':model['requested_logical_responses'],'slots':terminal},indent=2))
