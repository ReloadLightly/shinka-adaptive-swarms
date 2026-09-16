#!/usr/bin/env python3
"""Recompute the frozen V2 audit from saved measurements; no simulation/model calls.

Writes results/review_v2/independent_audit.json. Run with ordinary Python,
without -O, because scientific consistency checks use assertions.
"""
from pathlib import Path
import json,gzip,hashlib,sqlite3,random,math,statistics
from collections import defaultdict,Counter
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'artifacts/relocation_allocation_v2/study_20260916'
Q=ROOT/'artifacts/relocation_allocation_v2/evolution/20260916T013407.256962Z-search'
J=lambda p: json.loads(p.read_text())
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
audit={'read_only_measurement_audit':True,'new_objective_evaluations':0,'new_model_calls':0,'checked_stages':{},'checks':{},'comparisons':{},'diagnostics':{}}
histories={}
def inspect(d,key):
 c=d['config'];assert d['evaluations']==c['budget']==100000
 assert sum(d['evaluation_counts'].values())==100000
 assert math.isfinite(d['offline_error'])
 history=[d['initial_environment']['sha256']]+[x['next_environment']['sha256'] for x in d['environment_changes']]
 assert len(history)==100000//c['period']+1
 ckey=(c['environment_seed'],c['optimizer_seed'])
 if ckey in histories: assert histories[ckey]==history
 else:histories[ckey]=history
 for r in d['response_log']:
  assert r['completed']
  if 'requested_count' in r:assert r['requested_count']==r['executed_count']==len(r['relocated_indices'])
  if 'evaluated_relocation_count' in r:assert r['executed_count']==r['evaluated_relocation_count']
 return d['offline_error']
search={}
for gen in range(20):
 vals=[]
 for f in sorted((Q/f'gen_{gen}/results').glob('case_*.json.gz')):
  with gzip.open(f,'rt') as inp:d=json.load(inp)
  vals.append(inspect(d,('search',gen)))
 assert len(vals)==16
 search[gen]=vals
 metrics=J(Q/f'gen_{gen}/results/metrics.json')
 assert abs(metrics['combined_score']-1/(1+statistics.mean(vals)))<1e-12
stage_data={}
for stage,nmethods,ncases in [('validation',9,16),('final',5,40)]:
 m=J(P/stage/'manifest.json');s=J(P/stage/'summary.json');results={}
 assert m['status']==s['status']=='completed';assert not m['aliases'];assert len(m['methods'])==nmethods
 for method,paths in m['case_artifacts'].items():
  values=[]
  for i,path in enumerate(paths):
   with gzip.open(P/stage/path,'rt') as inp:d=json.load(inp)
   assert d['case_index']==i;assert d['method']==method;assert d['config']==m['cases'][i]
   inspect(d,(stage,method,i));values.append(d)
  assert len(values)==ncases
  assert [d['offline_error'] for d in values]==s['method_case_errors'][method]
  assert abs(statistics.mean(d['offline_error'] for d in values)-s['method_mean_offline_errors'][method])<1e-12
  results[method]=values
 stage_data[stage]=results
 audit['checked_stages'][stage]={'method_cases':nmethods*ncases,'queries':nmethods*ncases*100000,'methods':nmethods,'paired_histories':ncases}
short=J(P/'shortlist.json');sel=J(P/'selection.json');fin=J(P/'final_cases.json');an=J(P/'analysis.json')
for prog in short['programs']:assert sha(P/prog['policy'])==prog['sha256']
con=sqlite3.connect(f'file:{Q}/programs.sqlite?immutable=1',uri=True);con.row_factory=sqlite3.Row
assert con.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
rows=[dict(row) for row in con.execute('select * from programs')];assert len(rows)==21;assert all(r['correct'] for r in rows)
uniq={}
for row in sorted(rows,key=lambda r:(-r['combined_score'],r['generation'],hashlib.sha256(r['code'].encode()).hexdigest(),r['id'])):
 uniq.setdefault(hashlib.sha256(row['code'].encode()).hexdigest(),row)
assert len(uniq)==20
assert [p['sha256'] for p in short['programs']]==list(uniq)[:3]
for h,row in uniq.items():assert hashlib.sha256((Q/f"gen_{row['generation']}/main.py").read_bytes()).hexdigest()==h
sval=J(P/'validation/summary.json')['method_mean_offline_errors']
assert sel['selected_program']['name']==min((p['name'] for p in short['programs']),key=sval.get)
assert sel['selected_constant']==min(range(6),key=lambda k:(sval[f'constant_{k}'],k))
assert fin['selection_sha256']==sha(P/'selection.json');assert fin['selection_frozen_at']==sel['frozen_at']
assert short['frozen_at']<J(P/'source_review.json')['recorded_at']<J(P/'validation/manifest.json')['created_at']<J(P/'validation/summary.json')['completed_at']<sel['frozen_at']<fin['generated_at']<J(P/'final/manifest.json')['created_at']<J(P/'final/summary.json')['completed_at']<an['analyzed_at']
assert J(P/'final/manifest.json')['freeze_sha256']==sha(P/'selection.json')
seeds=[x for env,opt in histories for x in (env,opt)]
assert len(seeds)==len(set(seeds))==144
# Reconstruct control distributions from validation cases with equal case weights.
probs=defaultdict(list)
for d in stage_data['validation'][sel['selected_program']['name']]:
 c=d['config'];k=f"dimension={c['dimension']}; npeaks={c['npeaks']}; period={c['period']}; move_severity={c['move_severity']:g}; correlation={c['correlation']:g}"
 ct=Counter(r['requested_count'] for r in d['response_log']);n=sum(ct.values());assert n
 probs[k].append([ct[j]/n for j in range(6)])
for k,vs in probs.items():assert np.max(np.abs(np.array(vs).mean(axis=0)-sel['control']['distributions'][k]))<1e-12
for d in stage_data['final']['state_free_control']:
 ident=d['execution_identity'];rng=random.Random(ident['rng_seed'])
 assert [rng.choices(range(6),weights=ident['probabilities'],k=1)[0] for r in d['response_log']]==[r['requested_count'] for r in d['response_log']]
final=stage_data['final'];casecfg=J(P/'final/manifest.json')['cases']
regimes=[f"dimension={c['dimension']}; npeaks={c['npeaks']}; period={c['period']}; move_severity={c['move_severity']:g}; correlation={c['correlation']:g}" for c in casecfg]
for comparator in ['best_constant','state_free_control','baseline','constant_three']:
 delta=np.array([a['offline_error']-b['offline_error'] for a,b in zip(final['evolved'],final[comparator])]);groups=[delta[np.array(regimes)==r] for r in sorted(set(regimes))]
 rng=np.random.default_rng(20260916);boot=np.zeros(20000)
 for group in groups:boot+=rng.choice(group,size=(20000,len(group))).mean(axis=1)/4
 mean=float(np.mean([g.mean() for g in groups]));ci=np.quantile(boot,[.025,.975]);se=math.sqrt(sum(g.var(ddof=1)/len(g) for g in groups))/4
 expected=an['comparisons'][f'evolved_minus_{comparator}']
 assert abs(mean-expected['mean_delta'])<1e-12;assert np.max(np.abs(ci-expected['bootstrap_95_percent_interval']))<1e-12;assert abs(se-expected['stratified_se_delta'])<1e-12
 audit['comparisons'][comparator]={'mean_delta':mean,'ci95':ci.tolist(),'stratified_se':se,'wins':int(sum(delta<0)),'losses':int(sum(delta>0)),'median_delta':float(np.median(delta)),'regime_means':[float(g.mean()) for g in groups]}
 if comparator=='state_free_control':audit['diagnostics']['largest_loss']={'case':int(np.argmax(delta)),'delta':float(delta.max()),'share_of_total_signed_delta':float(delta.max()/delta.sum()),'mean_without_largest_loss_POSTHOC':float(np.delete(delta,np.argmax(delta)).mean())}
audit['checked_stages']['search']={'method_cases':320,'queries':32000000,'programs':20,'database_rows':21,'paired_histories':16,'source_distinct_programs':20}
audit['checks']={'all_664_exact_budgets':True,'all_72_paired_landscapes':True,'source_hashes_and_top3_ranking':True,'validation_selection_correct':True,'freeze_chronology_and_hashes':True,'all_144_rng_seed_values_distinct_across_v2_stages':True,'control_distribution_recomputed':True,'all_40_control_action_sequences_reproduced':True,'four_final_statistics_recomputed_to_1e-12':True}
audit['method_means']={k:statistics.mean(d['offline_error'] for d in v) for k,v in final.items()}
audit['validation_means']=sval
audit['response_counts']={method:dict(Counter(r['requested_count'] for d in final[method] for r in d['response_log'])) for method in ['evolved','state_free_control']}
audit['diagnostics']['duplicate_search_error_vectors']=[gens for gens in [[g for g,v in search.items() if tuple(v)==t] for t in {tuple(v) for v in search.values()}] if len(gens)>1]
audit['diagnostics']['runtime_seconds_saved']={stage:sum(d['wall_time_seconds'] for cases in values.values() for d in cases) for stage,values in stage_data.items()}
(ROOT/'results/review_v2').mkdir(parents=True,exist_ok=True)
(ROOT/'results/review_v2/independent_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps(audit,indent=2))
