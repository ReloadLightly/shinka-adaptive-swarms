"""Compact final evidence from completed read-only native audit and receipts."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

repo=Path.cwd();study=Path(__file__).resolve().parent.parent;run=study/'evolution/search_seed_640001'
sys.path.insert(0,str(repo/'src'))
from adaptive_swarms.artifacts import read_json
from adaptive_swarms.logging import atomic_json

audit=read_json(study/'operations/native-inspection-final.json')['native']
if audit['status']!='search_complete':raise RuntimeError('Final native completion required')
manifest=read_json(run/'manifest.json');receipts=[read_json(p) for p in (run/'engine_calls').glob('*.json')]
con=sqlite3.connect(f'file:{run}/programs.sqlite?mode=ro',uri=True);con.row_factory=sqlite3.Row
rows=[dict(r) for r in con.execute('select * from programs')]
for row in rows:
 for key in ['metadata','archive_inspiration_ids','top_k_inspiration_ids','public_metrics']:
  row[key]=json.loads(row[key]) if isinstance(row.get(key),str) else row.get(key)
by_id={r['id']:r for r in rows}; originals=[r for r in rows if not any((r['metadata'] or {}).get(k) for k in ['_is_island_copy','is_island_copy','island_copy'])]
valid=[r for r in originals if r['correct']]
best=min(valid,key=lambda r:(r['public_metrics']['mean_offline_error'],r['generation'],hashlib.sha256(r['code'].encode()).hexdigest()))
selection_path=study/'selection.json'
if selection_path.exists():
 selected=read_json(selection_path)['selected']
 best=next(r for r in valid if r['generation']==selected['generation'])
parent=by_id.get(best['parent_id'])
def identity(row):
 if row is None:return None
 return {k:row.get(k) for k in ['id','generation','island_idx','parent_id']}|{'is_island_copy':any((row['metadata'] or {}).get(k) for k in ['_is_island_copy','is_island_copy','island_copy'])}
sampling=[s for s in audit['native_sampling'] if s['generation']==best['generation']]
if not sampling and best['generation']==0:
 sampling=audit['native_sampling'][:1]  # The seed has no mutation; show its actual supplied feedback in the first descendant prompt.
prompts=[c for s in sampling for c in s['saved_attempt_prompt_checks']]
feedback=[]
for prompt in prompts:
 path=study/prompt['prompt']; text=path.read_text()
 for source in prompt['sources']:
  row=by_id[source['native_id']]; f=row.get('text_feedback') or ''
  feedback.append({'prompt':str(path.relative_to(study)),'native_id':row['id'],'generation':row['generation'],'full_feedback_supplied':bool(f) and f.strip() in text,'excerpt':f[:1400]})
role_accounting={}
for role in ['mutation','novelty','meta']:
 rs=[r for r in receipts if r['role']==role]
 role_accounting[role]={'native_wrappers':len(rs),'requested_logical_responses':sum(r['requested_logical_responses'] for r in rs),'returned_usable_responses':sum(r.get('valid_responses',0) or 0 for r in rs),'exposed_native_retry_responses':sum(r.get('exposed_native_retry_responses',0) for r in rs),'status_counts':dict(Counter(r['status'] for r in rs)),'configured_routes':sorted({m for r in rs for m in r['configured_models']}),'client_settings':rs[0].get('configured_client_settings') if rs else None}
work=[]
for d in sorted(run.glob('gen_*'),key=lambda p:int(p.name[4:])):
 c=d/'results/evaluation-checkpoint.json'
 if not c.exists():continue
 check=read_json(c);attempts_path=d/'results/execution-attempts.json';attempts=read_json(attempts_path) if attempts_path.exists() else []
 work.append({'generation':int(d.name[4:]),'status':check['status'],'completed_case_artifacts':len(check['completed_cases']),'physical_full_cases':sum(a['status']=='completed' for a in attempts),'physical_completed_queries':sum(a.get('exact_objective_queries',0) or 0 for a in attempts if a['status']=='completed'),'attempts':attempts,'case_cache_reuses':len(check['completed_cases'])-sum(a['status']=='completed' for a in attempts),'source_sha256':hashlib.sha256((d/'main.py').read_bytes()).hexdigest()})
repeat=[]
# A changed source can execute an already tested behavior. Compare every saved
# complete outcome, not only scores, and count each repeated physical case once.
prior=[(name,study/'references'/name) for name in ['mpso_5_0','mpso_5_1']]
for entry in work:
 if entry['generation']==0 or entry['status']!='completed':continue
 directory=run/f"gen_{entry['generation']}/results"
 matches=[]
 for method,other in prior:
  equal=[]
  for i in range(8):
   a=read_json(other/f'case_{i:03d}.json.gz');b=read_json(directory/f'case_{i:03d}.json.gz')
   relevant=lambda r:{k:v for k,v in r.items() if k not in {'policy_name','case_id'}}
   equal.append(relevant(a)==relevant(b))
  if all(equal):matches.append(method)
 if matches:repeat.append({'generation':entry['generation'],'equivalent_to':matches,'identical_complete_numerical_records':8,'excluded_metadata':['policy_name','case_id']})
 prior.append((f"generation_{entry['generation']}",directory))
metainjections=[m for m in audit['meta']['mutation_prompt_injections'] if m['matched_recommendations']]
meta_examples=[]
for injection in metainjections[:2]:
 for m in injection['matched_recommendations'][:1]:
  art=next(a for a in audit['meta']['saved_artifacts'] if a['artifact']==m['artifact'])
  meta_examples.append({'generation':injection['preceding_native_sampling_context']['generation'],'receipt':injection['receipt'],'artifact':m['artifact'],'recommendation_index':m['recommendation_index'],'actual_injected_text':art['recommendations'][m['recommendation_index']-1]})
start=datetime.fromisoformat(manifest['started_at']);end=datetime.fromisoformat(manifest['finished_at']);events=[json.loads(l) for l in (run/'events.jsonl').read_text().splitlines() if l]
obs=read_json(study/'operations/native-codex-process-settings-observed.json')
record={'recorded_at':datetime.now(timezone.utc).isoformat(),'status':audit['status'],'terminal_slots':audit['terminal_slots'],'valid_descendants':audit['valid_descendants'],'terminal_failed_slots':audit['terminal_failed_slots'],'role_accounting':role_accounting,'totals':{'native_wrappers':len(receipts),'requested_logical_responses':sum(r['requested_logical_responses'] for r in receipts),'returned_usable_responses':sum(r.get('valid_responses',0) or 0 for r in receipts),'allowance':40,'exposed_native_retry_responses':sum(r.get('exposed_native_retry_responses',0) for r in receipts),'provider_internal_retries':'unobserved','supervising_usage':'excluded/unobserved by native receipts','native_cost_estimates':'not subscription charges or paid API usage'},'model_and_effort':{'requested_supervising':'gpt-6-astra / Ultra','supervising_mode_independently_inspected':False,'requested_inner':'gpt-6-astra / xhigh','explicit_supported_selected':'gpt-6-astra / xhigh','CLI_evidence':'operations/native-codex-process-settings-observed.json','provider_independent_attestation':False,'native_reasoning_efforts_disabled_is_provider_effort':False,'limitation':'The installed pinned native provider accepts low,medium,high,xhigh; strongest supported task-local xhigh was prospectively selected. Inner xhigh is not relabeled supervising Ultra.'},'machinery':{'prompt_verification':audit['prompt_verification_summary'],'novelty':audit['novelty'],'embeddings':audit['native_embeddings'],'meta_updates':len(audit['meta']['updates_completed']),'exact_meta_injections':len(metainjections),'meta_examples':meta_examples,'migration_transfers':len(audit['migration_history']),'migration_interpretation':'Nine generation slots stop before the ten-generation migration interval; zero observed migrations are expected if recorded here.','degradation_events':audit['degradation_events'],'patch_types':audit['patch_types_original_evaluated_rows']},'selected_native_program':identity(best)|{'patch_type':best['metadata'].get('patch_type'),'combined_score':best['combined_score'],'mean_offline_error':best['public_metrics'].get('mean_offline_error'),'source':best['code'],'source_sha256':hashlib.sha256(best['code'].encode()).hexdigest(),'parent':identity(parent),'archive_inspirations':[identity(by_id[i]) for i in best['archive_inspiration_ids']],'top_ranked_inspirations':[identity(by_id[i]) for i in best['top_k_inspiration_ids']],'actual_feedback_examples':feedback},'work':{'by_generation':work,'physical_full_cases':sum(x['physical_full_cases'] for x in work),'physical_completed_queries':sum(x['physical_completed_queries'] for x in work),'cached_case_reuses':sum(x['case_cache_reuses'] for x in work),'exact_control_repetition_comparison':repeat,'repeated_cases_included':sum(x['identical_complete_numerical_records'] for x in repeat),'repeated_queries_included':500000*sum(x['identical_complete_numerical_records'] for x in repeat)},'runtime':{'started_at':manifest['started_at'],'finished_at':manifest['finished_at'],'UTC_wall_seconds':(end-start).total_seconds(),'UTC_wall_hours':(end-start).total_seconds()/3600,'last_logged_monotonic_elapsed_seconds':events[-1].get('elapsed_s')},'limitations':['This task permits function-local math imports and documented numerical builtins, including zip; any actual failed slots are counted from saved evidence, not repaired or replaced.','CLI wrapper and binary subprocesses can both appear in process observations; these are not separate logical requests. Receipt counts govern request accounting.','Native proposal RNG state is not restored across process restarts; inspect continuation records before claiming an uninterrupted proposal sequence.'],'audit_model_calls':0,'audit_objective_queries':0}
record['model_and_effort']['observed_roles_from_exact_prompt_receipt_matches']=sorted({m['role'] for row in obs['observations'] for prompt in row.get('headless_prompt_evidence',[]) for m in prompt['exact_system_and_user_message_matches']})
record['model_and_effort']['observed_visible_model_settings']=[list(pair) for pair in sorted({tuple(setting) for row in obs['observations'] for setting in row['visible_model_and_effort_arguments']})]
record['model_and_effort']['process_observation_count_not_request_count']=len(obs['observations'])
record['machinery']['within_slot_novelty_resamples']=sum(s.get('novelty_attempt',1)>1 for s in audit['native_sampling'])
record['runtime']['resume_attempts']=len(manifest.get('resume_attempts',[]))
record['runtime']['clock_note']='UTC wall interval and logger monotonic elapsed differ; both are retained, with no inferred cause.'
atomic_json(study/'operations/native-accounting-summary.json',record)
print(json.dumps({'saved':'operations/native-accounting-summary.json','terminal_slots':record['terminal_slots'],'valid_descendants':record['valid_descendants'],'totals':record['totals'],'selected_generation':best['generation'],'work':{k:record['work'][k] for k in ['physical_full_cases','physical_completed_queries','cached_case_reuses','repeated_cases_included']}}))
