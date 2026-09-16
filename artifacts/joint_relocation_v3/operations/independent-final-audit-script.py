"""Read saved V3 checkpoints sequentially; no candidate, simulator, or model imports."""
import collections, datetime, gzip, hashlib, json, math, random, resource, statistics
from pathlib import Path
import numpy as np
ROOT=Path('/home/roland/actir/shinka-adaptive-swarms'); D=ROOT/'results/joint_relocation_v3/study_20260916'; O=ROOT/'results/joint_relocation_v3/operations'
def read(p):
    with (gzip.open(p,'rt') if str(p).endswith('.gz') else p.open()) as f:return json.load(f)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,allow_nan=False).encode()).hexdigest()
def same(a,b,where='value'):
    if isinstance(b,dict):
        for k,v in b.items():same(a[k],v,where+'.'+k)
    elif isinstance(b,list):
        assert len(a)==len(b),where
        for i,(x,y) in enumerate(zip(a,b)):same(x,y,f'{where}[{i}]')
    elif isinstance(b,float):assert math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12),(where,a,b)
    else:assert a==b,(where,a,b)
def regime(c):return '; '.join(f'{k}={c[k]:g}' for k in ['dimension','npeaks','period','move_severity','correlation'])
def constant(a,c):return {'kind':'joint_constant','count':c['particles_per_swarm'] if a['count']=='swarm_size' else a['count'],'radius_scale':0. if a['count']==0 else float(a['radius_scale'])}
# Exact source-bound facts independently inspected before validation; do not invoke source.
RADII={'dc9811577267e4cef6c128d348ad9c2ffd28ffabc34f6f0fdd526cd1fa7632d7':1.25,'f4047cf27d7484f890ab84e4c35d2caa2a2b52d14f351083fa883591b812ff43':1.25,'9406700ee6e2cd7fa88df9ab592813fd5f14e56bdef8b8098d5c053f809a74de':1.25,'75dbb71c2cd09d9eb960007c9207ad5a35172e235f1435dd79903117d9da95e3':1.5,'acefdf34161e9e666deb778e914d0e3287e74a42642946513cc93ceb73a467ec':1.5,'b68862e0f7464e0e8d68b16dd7ee5c2c4a231da5cf28da3b1a486a9ffadd386c':1.5}
def sampler_seed(m,c):return int(digest({'namespace':'joint_relocation_v3_joint_sampler','master_seed':m['rng_master_seed'],'config':c})[:16],16)
def identity(m,c):
    k=m['kind']
    if k=='baseline':return constant({'count':5,'radius_scale':1.},c)
    if k=='fixed':return constant(m,c)
    if k=='program':return constant(m['proven_constant'],c) if m.get('proven_constant') else {'kind':'joint_program','sha256':m['sha256']}
    if k=='component':
        p=m['program'];a=p.get('proven_constant')
        if a:return constant({**a,m['component']:m['replacement']},c)
        if m['component']=='count' and p['sha256'] in RADII:return constant({'count':m['replacement'],'radius_scale':RADII[p['sha256']]},c)
        return {'kind':'joint_component','sha256':p['sha256'],'component':m['component'],'replacement':m['replacement']}
    if k=='joint_sampler':
        group=m['regime_cases'][regime(c)]; pairs={tuple(p) for row in group for p in row['action_pairs']}
        if len(pairs)==1:
            count,radius=pairs.pop();return constant({'count':count,'radius_scale':radius},c)
        return {'kind':'joint_sampler','distribution_sha256':digest(group),'rng_seed':sampler_seed(m,c),'rng_algorithm':'python.random.Random; uniform case then uniform full action pair'}
    raise AssertionError(k)
def independent_stats(values,keys,level):
    # Integer index draws and manually interpolated sorted quantiles are independent
    # of the controller's choice(values) and np.quantile implementation.
    groups={key:np.array([v for v,k in zip(values,keys) if k==key],dtype=float) for key in sorted(set(keys))}
    means=[math.fsum(a)/len(a) for a in groups.values()]; samples=np.zeros(20000); rng=np.random.default_rng(2026091603)
    for a in groups.values():
        for first in range(0,20000,1000):
            ix=rng.integers(0,len(a),size=(1000,len(a)))
            samples[first:first+1000]+=a[ix].mean(axis=1)/len(groups)
    samples.sort()
    def quantile(q):
        rank=q*(len(samples)-1);lo=int(math.floor(rank));hi=int(math.ceil(rank));return float(samples[lo]+(samples[hi]-samples[lo])*(rank-lo))
    tail=(1-level)/2
    return {'n':len(values),'mean_delta':math.fsum(means)/len(means),'interval_level':level,'improved_cases':sum(v<0 for v in values),'worsened_cases':sum(v>0 for v in values),'tied_cases':sum(v==0 for v in values),'bootstrap_interval':[quantile(tail),quantile(1-tail)],'stratified_se_delta':math.sqrt(math.fsum(statistics.variance(a.tolist())/len(a) for a in groups.values()))/len(groups)}
def mean_error(errors,cases):
    groups=collections.defaultdict(list)
    for v,c in zip(errors,cases):groups[regime(c)].append(v)
    return statistics.mean(statistics.mean(v) for v in groups.values())
reg=read(D/'registration.json'); sel=read(D/'selection.json'); short=read(D/'shortlists.json'); finalcases=read(D/'final_cases.json'); analysis=read(D/'analysis.json')
assert analysis['status']=='completed'
reg_keys=['settings','searches','engine_config','search_cases','validation_cases','execution_sources','task_sources','analysis']
assert reg['signature']==digest({k:reg[k] for k in reg_keys})
for name,expected in reg['runner_snapshot'].items():assert sha(D/'runner_snapshot'/name)==expected
for p in short['programs'].values():assert sha(D/p['policy'])==p['sha256']
assert sel['analysis']==reg['analysis']==analysis['uncertainty']; assert analysis['selection']==sel
assert finalcases['selection_sha256']==sha(D/'selection.json')
assert sel['frozen_at']==finalcases['selection_frozen_at']<finalcases['generated_at']
assert not sel['final_cases_existed_at_freeze']
seeds=[c[k] for c in finalcases['cases'] for k in ['environment_seed','optimizer_seed']]
assert len(seeds)==len(set(seeds))==160
reserved=set(finalcases['historical_seed_audit']['reserved_seed_values']);assert not set(seeds)&reserved
for c in reg['search_cases']+reg['validation_cases']:
    assert c['environment_seed'] in reserved and c['optimizer_seed'] in reserved
rng=random.Random(finalcases['seed_generation_master_seed']); replay=[]
for _ in range(160):
    while True:
        x=rng.randrange(1,2**31)
        if x not in reserved:reserved.add(x);replay.append(x);break
assert replay==seeds
stage_results={}; final_error_arrays=None
for stage in ['validation','final']:
    manifest=read(D/stage/'manifest.json'); summary=read(D/stage/'summary.json'); cases=manifest['cases']; methods=manifest['methods']; n=len(cases)
    assert manifest['status']==summary['status']=='completed'
    assert cases==(reg['validation_cases'] if stage=='validation' else finalcases['cases'])
    assert manifest['signature']==digest({'version':manifest['version'],'stage':stage,'cases':cases,'methods':methods,'freeze_sha256':manifest['freeze_sha256'],'execution_sources':manifest['execution_sources']})
    for source,expected in manifest['execution_sources'].items():assert sha(ROOT/source)==expected
    assert manifest['freeze_sha256']==sha(D/('shortlists.json' if stage=='validation' else 'selection.json'))
    assert collections.Counter((c['move_severity'],c['period']) for c in cases)=={(1.,2500):n//4,(1.,5000):n//4,(3.,2500):n//4,(3.,5000):n//4}
    errors={name:[] for name in methods};response_counts=collections.Counter();query_categories=collections.Counter(); component_rows=collections.Counter(); action_counts={name:collections.Counter() for name in methods}; noresponse=collections.Counter(); actual_aliases=[]; unique_paths=set(); queried=0; truncated=0; sampler_replayed=0; observed_components=0; histories=[]; worst={name:[] for name in methods}
    for name,paths in manifest['case_artifacts'].items():assert len(paths)==n
    for i,c in enumerate(cases):
        seen={};history=None
        for name,m in methods.items():
            expected_id=identity(m,c);key=digest({'signature':manifest['signature'],'config':c,'execution_identity':expected_id});relative=f'cache/{key}.json.gz'
            assert manifest['case_artifacts'][name][i]==relative
            if key in seen:
                ref=seen[key]; errors[name].append(errors[ref][-1]); actual_aliases.append((i,name,ref,key));continue
            unique_paths.add(relative);case=read(D/stage/relative);seen[key]=name
            assert case['method']==name and case['case_index']==i and case['config']==c and case['signature']==manifest['signature'] and case['execution_identity']==expected_id and case['cache_key']==key
            assert c['budget']==case['evaluations']==sum(case['evaluation_counts'].values())==100000
            assert math.isfinite(case['offline_error']) and case['offline_error']>=0
            h=[case['initial_environment']['sha256']]+[x['next_environment']['sha256'] for x in case['environment_changes']]
            if history is None:history=h
            else:assert history==h
            errors[name].append(case['offline_error']);queried+=case['evaluations'];query_categories.update(case['evaluation_counts']);worst[name].append({'case_index':i,'offline_error':case['offline_error'],'maximum_environment_offline_error':max(x['environment_offline_error'] for x in case['environment_changes'])})
            if stage=='final':
                rng=random.Random(sampler_seed(m,c)) if m['kind']=='joint_sampler' else None
                group=m['regime_cases'][regime(c)] if rng else None
                for r in case['response_log']:
                    k=r['requested_count'];radius=r['requested_radius_scale'];size=r['observation']['swarm_size'];indices=r['relocated_indices'];encoding=(k-.5)/size if k else 0.
                    assert type(k) is int and 0<=k<=size==5 and math.isfinite(radius) and radius>=0
                    assert k==r['allocated_count']==len(indices) and len(set(indices))==k and all(0<=j<5 for j in indices)
                    assert r['allocated_fraction']==k/size and r['adapter_encoding_fraction']==r['decision']['fraction']==encoding
                    assert r['decision']['radius_scale']==radius and r['decision']['memory']=='reevaluate' and r['decision']['reset_velocity'] is False
                    evaluated=max(0,min(size,r['evaluations_after_detection']-size));assert r['evaluated_relocation_count']==sum(j<evaluated for j in indices)
                    if m['kind']=='component':
                        original=r['original_candidate_action'];assert r['component_substitution']=={'component':m['component'],'replacement':m['replacement']}
                        action={**original,m['component']:m['replacement']};assert action=={'count':k,'radius_scale':radius}
                        assert type(original['count']) is int and original['count'] in [3,4] and original['radius_scale']==RADII[m['program']['sha256']]
                        component_rows[name]+=1;observed_components+=1
                    else:assert 'original_candidate_action' not in r and 'component_substitution' not in r
                    if rng:
                        sampled_case=group[rng.randrange(len(group))];pair=sampled_case['action_pairs'][rng.randrange(len(sampled_case['action_pairs']))];assert pair==[k,radius];sampler_replayed+=1
                    response_counts[name]+=1;action_counts[name][(k,radius)]+=1;truncated+=not r['completed']
                if not case['response_log']:noresponse[name]+=1
                if m['kind']=='program' and m.get('proven_constant'):
                    assert all((k,radius)==(m['proven_constant']['count'],m['proven_constant']['radius_scale']) for k,radius in action_counts[name])
            if stage=='validation' and name==sel['overall_winner']['name']:
                group=sel['joint_sampler']['regime_cases'][regime(c)];entry=next(x for x in group if x['validation_case_index']==i);pairs=[[r['requested_count'],r['requested_radius_scale']] for r in case['response_log']]
                assert entry['response_count']==len(pairs) and entry['no_response_baseline_fallback']==(not pairs) and entry['action_pairs']==(pairs or [[5,1.]])
            del case
        histories.append(digest(history))
    assert set(unique_paths)=={str(p.relative_to(D/stage)) for p in (D/stage/'cache').glob('*.json.gz')}
    assert sorted(actual_aliases)==sorted((a['case_index'],a['method'],a['alias_of'],a['cache_key']) for a in manifest['aliases'])
    assert summary['unique_executed_method_cases']==len(unique_paths)
    means={name:mean_error(v,cases) for name,v in errors.items()};same(summary['method_mean_offline_errors'],means);same(summary['method_case_errors'],errors)
    if stage=='validation':
        same(sel['validation_mean_errors'],means);winners=[]
        for search in short['searches']:
            w=min(search['shortlist'],key=lambda p:(means[p['name']],p['search_index'],p['generation'],p['sha256']));winners.append(w)
            recorded=sel['per_search_winners'][search['search_index']];assert recorded['sha256']==w['sha256'];same(recorded['validation_mean_error'],means[w['name']])
        winner=min(winners,key=lambda p:(means[p['name']],p['search_index'],p['generation'],p['sha256']));assert winner['sha256']==sel['overall_winner']['sha256']
        fixed=min(sel['fixed_grid'],key=lambda name:(means[name],methods[name]['count'],methods[name]['radius_scale']));assert fixed==sel['selected_fixed_label'];assert sel['selected_fixed_pair']==methods[fixed]
        assert sel['provenance']=={'shortlists_sha256':sha(D/'shortlists.json'),'validation_signature':manifest['signature'],'validation_summary_sha256':sha(D/'validation/summary.json')}
    else:
        assert methods==sel['methods'];assert finalcases['generated_at']<=manifest['created_at']<manifest['completed_at']<=analysis['analyzed_at'];assert n==80
        final_error_arrays=errors;final_configs=cases;same(analysis['method_mean_offline_errors'],means)
        for name in methods:
            same(analysis['pairing_checks'][name],[{'equal_objective_budgets':True,'matching_environment_hashes':True,'environment_hash_count':100000//c['period']+1,'environment_history_sha256':h} for c,h in zip(cases,histories)])
            saved=analysis['behavior'][name]['worst_cases'];assert len(saved)==80 and {r['case_index'] for r in saved}==set(range(80));assert [r['offline_error'] for r in saved]==sorted(errors[name],reverse=True)
    stage_results[stage]={'case_count':n,'nominal_methods':len(methods),'unique_executed_cases':len(unique_paths),'alias_records':len(actual_aliases),'objective_queries':queried,'objective_categories':dict(query_categories),'means':means,'response_records_checked':dict(response_counts),'component_original_action_rows':dict(component_rows),'sampler_pairs_replayed':sampler_replayed,'truncated_responses':truncated,'no_response_cases':dict(noresponse),'all_saved_cases_retained':True}
    print(f'{datetime.datetime.now(datetime.timezone.utc).isoformat()} independent audit: {stage} {len(unique_paths)} checkpoints verified, {queried} queries',flush=True)
# No full case objects remain; statistics use eight arrays of 80 errors only.
E=final_error_arrays; C=final_configs; keys=[regime(c) for c in C]; overall=sel['overall_winner_method'];contrasts={}
def verify_contrast(saved,values,level,method=None,comparator=None):
    record=independent_stats(values,keys,level);same(saved,record)
    for r in sorted(set(keys)):
        ix=[i for i,k in enumerate(keys) if k==r];vals=[values[i] for i in ix];specific=independent_stats(vals,[r]*len(ix),level)
        if method:specific.update(mean_method_error=statistics.mean(E[method][i] for i in ix),mean_comparator_error=statistics.mean(E[comparator][i] for i in ix))
        same(saved['regimes'][r],specific)
    expected=[]
    for i,(value,c) in enumerate(zip(values,C)):
        row={'case_index':i,'environment_seed':c['environment_seed'],'optimizer_seed':c['optimizer_seed'],'regime':keys[i],'delta':value}
        if method:row.update(method_offline_error=E[method][i],comparator_offline_error=E[comparator][i])
        expected.append(row)
    same(saved['cases'],expected);return record
pairs=[(w['method'],comp) for w in sel['per_search_winners'] for comp in ['baseline','best_fixed']]+[(overall,comp) for comp in ['radius_replaced','count_replaced','joint_sampler']]
assert len(analysis['comparisons'])==len(pairs)==9
primary=[]
for method,comp in pairs:
    name=f'{method}_minus_{comp}';main=method==overall and comp in ['baseline','best_fixed'];saved=analysis['comparisons'][name]
    assert saved['method']==method and saved['comparator']==comp and saved['role']==('primary' if main else 'descriptive secondary')
    contrasts[name]=verify_contrast(saved,[a-b for a,b in zip(E[method],E[comp])],.975 if main else .95,method,comp)
    if main:primary.append(name)
interaction=verify_contrast(analysis['interaction'],[e-r-k+f for e,r,k,f in zip(E[overall],E['radius_replaced'],E['count_replaced'],E['best_fixed'])],.95)
claim=all(contrasts[k]['bootstrap_interval'][1]<0 for k in primary);assert len(primary)==2;assert analysis['claim']['primary_contrasts']==primary and analysis['claim']['superiority_over_both_primary_controls_supported']==claim
assert analysis['execution_accounting']=={'final_unique_method_cases':560,'final_nominal_methods':8}
assert E['baseline']==E['best_fixed']
report={'format':'joint-v3-independent-final-audit-v1','reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'passed','scope':'Independent sequential checkpoint, frozen selection/control, identity, alias, seed chronology, paired-history, response annotation, sampler replay and independently implemented stratified bootstrap audit. No candidate imports or calls, simulator calls, model calls, source edits or study artifact writes.','analysis_sha256':sha(D/'analysis.json'),'script_sha256':sha(Path(__file__)),'stages':stage_results,'statistical_implementation':{'resamples':20000,'analysis_seed':2026091603,'rng':'numpy.default_rng integer-index sampling, in chunks of1000 per sorted regime','quantiles':'Independent sorted linear interpolation; 0.0125/0.9875 primary,0.025/0.975 secondary','stratified_standard_error':'sqrt(sum(unbiased sample variance / n within each regime))/4','numeric_tolerance':1e-12,'all_global_and_per_regime_statistics_match':True},'contrasts':contrasts,'interaction':interaction,'claim':{'two_primary_contrasts':primary,'superiority_over_both_supported':claim,'primary_comparators_share_execution':'The validation-selected fixed pair is count5/radius1, execution-equivalent to baseline, so the two prescribed primary contrasts coincide; this is reported, not treated as independent controls.'},'seeds':{'paired_final_cases':80,'regime_counts':[20,20,20,20],'distinct_values_across_roles':160,'fresh_against_recorded_historical_inventory':True,'saved_generator_replay_matches':True,'selection_before_generation_before_execution':True},'overall_winner':{'method':overall,'source_sha256':sel['overall_winner']['sha256'],'search_index':sel['overall_winner']['search_index'],'generation':sel['overall_winner']['generation']},'selected_fixed_pair':sel['selected_fixed_pair'],'research_accounting':{'search_cases':1440,'validation_cases':stage_results['validation']['unique_executed_cases'],'final_cases':stage_results['final']['unique_executed_cases'],'total_case_executions':1440+stage_results['validation']['unique_executed_cases']+stage_results['final']['unique_executed_cases'],'total_objective_queries':144000000+stage_results['validation']['objective_queries']+stage_results['final']['objective_queries'],'preparation_excluded':True},'memory':{'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'strategy':'One decompressed case at a time; only compact error/config/accounting arrays retained.'},'source_hashes':{str(p.relative_to(ROOT)):sha(p) for p in [D/'registration.json',D/'controller_amendment.json',D/'shortlists.json',D/'source_review.json',D/'selection.json',D/'final_cases.json',D/'final/manifest.json',D/'validation/manifest.json',D/'analysis.json']},'actions':{'candidate_calls':0,'objective_queries':0,'model_calls':0,'frozen_source_or_study_edits':0}}
output=O/'independent-final-analysis-audit.json'
with output.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
output.chmod(0o444)
print(json.dumps({'output':str(output.relative_to(ROOT)),'sha256':sha(output),'peak_rss_kib':report['memory']['peak_rss_kib'],'primary':{k:contrasts[k] for k in primary},'interaction':interaction,'research_accounting':report['research_accounting']},indent=2),flush=True)
