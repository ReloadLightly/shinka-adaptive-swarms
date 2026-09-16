"""Independent review of saved study data; never invokes an optimizer or model."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
RUN = Path(__file__).resolve().parents[1]
SEARCH = RUN/'evolution/search_seed_650001'
sys.path.insert(0,str(ROOT/'src'))
from adaptive_swarms.population_policy import population_fingerprint as schedule_fingerprint
from audit_population_cases import inspect_case


def read(p):
    if str(p).endswith('.gz'):
        with gzip.open(p,'rt') as stream: return json.load(stream)
    return json.loads(p.read_text())


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def near(a,b): assert math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12),(a,b)
def history(row): return [row['initial_environment']['sha256']]+[x['next_environment']['sha256'] for x in row['environment_changes']]


def load(folder, configs, reference=None, permanent=1):
    rows=[]
    for i,cfg in enumerate(configs):
        row=read(folder/f'case_{i:03d}.json.gz')
        assert row['config']==cfg and row['case_id']==f'case_{i:03d}'
        assert row['permanent_quantum']==permanent
        assert row['evaluations']==sum(row['evaluation_counts'].values())==500000
        assert len(row['environment_changes'])==100
        assert [x['evaluations'] for x in row['environment_changes']]==list(range(5000,500001,5000))
        assert math.isfinite(row['offline_error']) and row['offline_error']>=0
        if reference: assert history(row)==history(reference[i])
        inspect_case(row)
        s=row['schedule_stats'];hist=s['count_histogram']
        assert sum(hist.values())==s['updates']==s['selection_permutations']
        assert sum(int(k)*n for k,n in hist.items())==s['requested_neutral_conversions']
        assert sum(x['updates'] for x in s['age_bins'].values())==s['updates']
        assert sum(x['neutral_conversions'] for x in s['age_bins'].values())==s['requested_neutral_conversions']
        assert row['evaluation_counts'].get('permanent_quantum',0)==permanent*s['completed_updates']
        weighted=sum(e['environment_offline_error']*e['environment_evaluations'] for e in row['environment_changes'])/500000
        near(weighted,row['offline_error'])
        rows.append(row)
    return rows


def verify_best_descendant(analysis, programs, reference, spec):
    descendants={g:rows for g,rows in programs.items() if g>0}
    if not descendants:
        assert analysis.get('best_descendant') is None
        return None
    generation=min(descendants,key=lambda g:(statistics.mean(r['offline_error'] for r in descendants[g]),g,sha(SEARCH/f'gen_{g}/main.py')))
    rows=descendants[generation];saved=analysis['best_descendant']
    assert saved['generation']==generation and saved['source_sha256']==sha(SEARCH/f'gen_{generation}/main.py')
    assert saved['case_errors']==[r['offline_error'] for r in rows]
    near(saved['mean_offline_error'],statistics.mean(r['offline_error'] for r in rows))
    behavior=analysis['best_descendant_behavior']
    assert behavior['additions']==sum(r['population_stats']['additions'] for r in rows)
    assert behavior['removals']==sum(r['population_stats']['removals'] for r in rows)
    for count in range(2,9):
        near(behavior['equal_case_requested_target_probabilities'][str(count)],statistics.mean(r['population_stats']['requested_target_histogram'][str(count)]/r['population_stats']['policy_calls'] for r in rows))
        near(behavior['equal_case_realized_neutral_count_probabilities'][str(count)],statistics.mean(r['population_stats']['realized_neutral_count_histogram'][str(count)]/r['population_stats']['total_neutral_updates'] for r in rows))
    paired=analysis['best_descendant_versus_target_5']
    effects=np.array([x['offline_error']-y['offline_error'] for x,y in zip(rows,reference)])
    assert paired['values']==list(effects)
    near(paired['mean'],float(effects.mean()));near(paired['median'],float(np.median(effects)));near(paired['sd'],float(effects.std(ddof=1)))
    assert paired['wins']==int(sum(effects<0)) and paired['losses']==int(sum(effects>0)) and paired['ties']==int(sum(effects==0))
    settings=read(spec)['bootstrap'];indices=np.random.default_rng(settings['seed']).integers(0,8,size=(settings['resamples'],8))
    bounds=np.quantile(effects[indices].mean(axis=1),[.025,.975])
    for a,b in zip(paired['descriptive_95_percent_interval'],bounds):near(a,float(b))
    for index,value in enumerate(paired['leave_one_case_out_means']):near(value,float(np.delete(effects,index).mean()))
    episodes=[]
    for index,(x,y) in enumerate(zip(rows,reference)):
        for ex,ey in zip(x['environment_changes'],y['environment_changes']):
            episodes.append((index,ex['completed_environment'],(ex['environment_offline_error']-ey['environment_offline_error'])/800))
    near(sum(v[2] for v in episodes),float(effects.mean()))
    eligible=[v for v in episodes if v[1]>0]
    details=analysis['best_descendant_episode_influence']
    for name,sign in [('most_favorable',1),('most_unfavorable',-1)]:
        expected=min(eligible,key=lambda x:(sign*x[2],x[0],x[1]));actual=details[name]
        assert (actual['case_index'],actual['environment'])==expected[:2]
        near(actual['contribution_to_paired_mean'],expected[2])
    return {'generation':generation,'selected_as_final_policy':False,'mean_error':saved['mean_offline_error'],
        'paired_mean_minus_target5':float(effects.mean()),'descriptive_95_percent_interval':list(bounds),
        'wins':paired['wins'],'losses':paired['losses'],'all_case_effects':list(effects),
        'population_histograms_and_prespecified_extreme_episode_selection_verified':True}


def verify_analysis(path,outcomes,analysis_spec):
    a=read(path)
    assert a['analysis_specification_sha256']==sha(analysis_spec)
    settings=read(analysis_spec)['bootstrap']
    assert settings['resamples']==20000 and settings['seed']==2026091609
    for method,rows in outcomes.items():
        errors=[r['offline_error'] for r in rows]
        assert a['method_errors'][method]['values']==errors
        near(a['method_errors'][method]['mean'],statistics.mean(errors))
        near(a['method_errors'][method]['median'],statistics.median(errors))
        near(a['method_errors'][method]['sd'],statistics.stdev(errors))
        assert a['query_category_totals'][method]==dict(sum((Counter(r['evaluation_counts']) for r in rows),Counter()))
        behavior=a['behavior'][method]
        near(behavior['additions'],sum(r['population_stats']['additions'] for r in rows))
        near(behavior['removals'],sum(r['population_stats']['removals'] for r in rows))
        for count in range(2,9):
            requested=[r['population_stats']['requested_target_histogram'][str(count)]/r['population_stats']['policy_calls'] for r in rows]
            realized=[r['population_stats']['realized_neutral_count_histogram'][str(count)]/r['population_stats']['total_neutral_updates'] for r in rows]
            near(behavior['equal_case_requested_target_probabilities'][str(count)],statistics.mean(requested))
            near(behavior['equal_case_realized_neutral_count_probabilities'][str(count)],statistics.mean(realized))
        regular=[[p for p in r['trace'] if p['evaluations']%r['config']['trace_interval']==0] for r in rows]
        near(behavior['equal_case_trace_sampled_mean_total_particles'],statistics.mean(statistics.mean(p['total_particle_count'] for p in points) for points in regular))
        near(behavior['equal_case_trace_sampled_mean_swarms'],statistics.mean(statistics.mean(p['swarm_count'] for p in points) for points in regular))
        near(behavior['equal_case_trace_fraction_with_different_subswarm_neutral_counts'],statistics.mean(statistics.mean(p['neutral_count_max']>p['neutral_count_min'] for p in points) for points in regular))
        per_case=[]
        for row in rows:
            offsets=defaultdict(list)
            for point in row['trace']:
                epoch=(point['evaluations']-1)//5000;offset=(point['evaluations']-1)%5000+1
                assert point['environment']==epoch
                if epoch:offsets[offset].append(point['current_error'])
            per_case.append({offset:statistics.mean(v) for offset,v in offsets.items()})
        for point in a['recovery'][method]:
            values=[row[point['offset']] for row in per_case if point['offset'] in row]
            assert len(values)==point['contributing_cases']==8
            near(statistics.mean(values),point['mean_error'])
    contrasts={}
    for name,stored in a['contrasts'].items():
        method,reference=stored['method'],stored['reference']
        deltas=np.array([x['offline_error']-y['offline_error'] for x,y in zip(outcomes[method],outcomes[reference])])
        assert list(deltas)==stored['values']
        near(float(deltas.mean()),stored['mean']);near(float(np.median(deltas)),stored['median'])
        near(float(deltas.std(ddof=1)),stored['sd'])
        assert int(sum(deltas<0))==stored['wins'] and int(sum(deltas>0))==stored['losses'] and int(sum(deltas==0))==stored['ties']
        indices=np.random.default_rng(settings['seed']).integers(0,8,size=(settings['resamples'],8))
        bounds=np.quantile(deltas[indices].mean(axis=1),[.025,.975])
        for actual,expected in zip(stored['descriptive_95_percent_interval'],bounds):near(actual,float(expected))
        for i,mean in enumerate(stored['leave_one_case_out_means']):near(mean,float(np.delete(deltas,i).mean()))
        largest=int(np.argmax(abs(deltas)));assert stored['largest_absolute_case_contribution']['case_index']==largest
        near(stored['largest_absolute_case_contribution']['difference'],float(deltas[largest]))
        contrasts[name]={'mean':stored['mean'],'median':stored['median'],'descriptive_95_percent_interval':list(bounds),'wins':stored['wins'],'losses':stored['losses'],'ties':stored['ties']}
    for reference,details in a['episode_influence'].items():
        effects=[]
        for i,(x,y) in enumerate(zip(outcomes['selected'],outcomes[reference])):
            for ex,ey in zip(x['environment_changes'],y['environment_changes']):
                effects.append((i,ex['completed_environment'],(ex['environment_offline_error']-ey['environment_offline_error'])/800))
        near(sum(x[2] for x in effects),a['contrasts']['selected_minus_'+reference]['mean'])
        largest=max(effects,key=lambda x:abs(x[2]));saved=details['largest_absolute_contribution']
        assert (saved['case_index'],saved['environment'])==largest[:2]
        near(saved['contribution_to_paired_mean'],largest[2])
    for relative,digest in a['input_sha256'].items():assert sha(RUN/relative)==digest
    return {'analysis_file':str(path.relative_to(RUN)),'sha256':sha(path),'all_saved_case_statistics_and_bootstraps_independently_verified':True,'contrasts':contrasts}


def main():
    native=read(SEARCH/'manifest.json')
    if native['status']!='search_complete' or not (RUN/'selection.json').exists():
        print('Waiting for terminal search and frozen selection; no final review written.');return
    account=read(RUN/'accounting.json')
    if account['status']!='research_complete':
        print('Waiting for final case accounting; no final review written.');return
    selection=read(RUN/'selection.json');manifest=read(RUN/'references/manifest.json')
    assert manifest['scientific_sources']==schedule_fingerprint()==selection['scientific_sources']
    for relative,digest in manifest['frozen_contract_sources'].items():assert sha(ROOT/relative)==digest
    assert sha(RUN/'development_cases.json')==manifest['development_cases_sha256']
    configs=manifest['cases'];assert len(configs)==8
    assert len({c['environment_seed'] for c in configs}|{c['optimizer_seed'] for c in configs})==16
    for cfg in configs:
        for k,v in {'dimension':5,'npeaks':10,'move_severity':1,'period':5000,'correlation':0,'budget':500000,'nexcess':1,'particles_per_swarm':5}.items():assert cfg[k]==v
    five=load(RUN/'references/target_5',configs)
    controls={5:five,3:load(RUN/'references/target_3',configs,five),7:load(RUN/'references/target_7',configs,five)}
    programs={};ranking=[];failed_slots=[];failed_slot_complete_cases=0
    for gen in sorted(SEARCH.glob('gen_*'),key=lambda p:int(p.name[4:])):
        cp=gen/'results/evaluation-checkpoint.json'
        if not cp.exists():continue
        checkpoint=read(cp)
        assert checkpoint['status'] in ('completed','failed')
        identity=checkpoint['identity']
        assert identity['program_sha256']==sha(gen/'main.py')
        assert identity['suite_sha256']==sha(RUN/'search_suite.json')
        assert identity['scientific_sources']==schedule_fingerprint()
        assert identity['evaluator_sha256']==sha(ROOT/'tasks/book_mpso_population_v1/evaluate.py')
        if checkpoint['status']!='completed':
            failed_slots.append(int(gen.name[4:]))
            for case_path in (gen/'results').glob('case_*.json.gz'):
                index=int(case_path.name.split('.')[0].split('_')[1]);row=read(case_path)
                assert row['config']==configs[index] and history(row)==history(five[index])
                inspect_case(row);failed_slot_complete_cases+=1
            continue
        generation=int(gen.name[4:]);rows=load(gen/'results',configs,five)
        programs[generation]=rows
        mean=statistics.mean(x['offline_error'] for x in rows)
        metrics=read(gen/'results/metrics.json');near(metrics['combined_score'],1/(1+mean))
        ranking.append((mean,generation,sha(gen/'main.py')))
    assert programs[0]==five,'Cached native seed must equal standalone reference artifact content'
    behavior_repeats=[]
    def numerical_projection(rows):
        projected=[]
        for row in rows:
            value={k:row[k] for k in ('offline_error','evaluation_counts','trace','environment_changes','response_log','snapshots','schedule_stats','population_stats')}
            value['population_stats']=dict(value['population_stats'])
            value['population_stats'].pop('diagnostic_origin',None)
            projected.append(value)
        return projected
    for generation in sorted(programs):
        if generation==0:continue
        comparators=[(f'fixed_target_{k}',rows) for k,rows in controls.items()]
        comparators += [(f'generation_{earlier}',programs[earlier]) for earlier in sorted(programs) if earlier<generation]
        for earlier,rows in comparators:
            if numerical_projection(programs[generation])==numerical_projection(rows):
                behavior_repeats.append({'first_method':earlier,'repeated_generation':generation,
                    'equal_saved_numerical_records':8,'repeated_full_executions':8,'repeated_objective_queries':4000000,
                    'included_in_physical_totals':True,'interpretation':'Identical complete saved development trajectories, not a general proof on all observations.'})
                break
    assert not (SEARCH/'gen_0/results/execution-attempts.json').exists() or read(SEARCH/'gen_0/results/execution-attempts.json')==[]
    assert sha(SEARCH/'gen_0/main.py')==manifest['methods']['target_5']['sha256']
    best_fixed=min(controls,key=lambda k:(statistics.mean(x['offline_error'] for x in controls[k]),k))
    assert selection['selected_fixed_target']==best_fixed
    winner=min(ranking);assert selection['selected']['generation']==winner[1]
    near(selection['selected']['mean_offline_error'],winner[0]);assert selection['selected']['sha256']==winner[2]
    assert sha(RUN/selection['selected']['source'])==winner[2]
    analyses=[];spec=ROOT/selection['analysis_specification'];assert sha(spec)==selection['analysis_sha256']
    development_path=RUN/'analysis/development/analysis.json'
    if not development_path.exists():
        print('Waiting for final development analysis; no final review written.');return
    analyses.append(verify_analysis(development_path,{**{f'target_{k}':rows for k,rows in controls.items()},'selected':programs[winner[1]]},spec))
    best_descendant_review=verify_best_descendant(read(development_path),programs,five,spec)
    expected_fresh=(winner[1]>0 and winner[0]<statistics.mean(x['offline_error'] for x in five) and winner[0]<statistics.mean(x['offline_error'] for x in controls[best_fixed]))
    assert selection['fresh_comparison_required']==expected_fresh
    fresh=False
    if selection['fresh_comparison_required']:
        fresh=True;frozen=read(RUN/'fresh/manifest.json')
        assert datetime.fromisoformat(selection['frozen_at'])<datetime.fromisoformat(frozen['created_at'])
        assert sha(RUN/'selection.json')==frozen['selection_sha256']
        assert sha(RUN/'source_review.json')==frozen['source_review_sha256']
        assert read(RUN/'source_review.json')['approved_source_sha256']==winner[2]
        assert frozen['methods']==selection['methods']
        for method in frozen['methods'].values():assert sha(RUN/method['source'])==method['sha256']
        fresh_configs=frozen['cases'];assert len(fresh_configs)==8
        old_seeds={c[k] for c in configs for k in ('environment_seed','optimizer_seed')}
        new_seeds={c[k] for c in fresh_configs for k in ('environment_seed','optimizer_seed')}
        assert len(new_seeds)==16 and not(old_seeds&new_seeds)
        x=load(RUN/'fresh/target_5',fresh_configs)
        outcomes={'target_5':x,'selected':load(RUN/'fresh/selected',fresh_configs,x)}
        if best_fixed!=5:outcomes[f'target_{best_fixed}']=load(RUN/f'fresh/target_{best_fixed}',fresh_configs,x)
        assert len(frozen['methods'])==len(outcomes)
        forbidden=set(frozen['historical_seed_audit']['reserved_seed_values'])
        assert not(new_seeds&forbidden)
        analyses.append(verify_analysis(RUN/'analysis/fresh/analysis.json',outcomes,spec))
    else:
        assert not expected_fresh
        assert not(RUN/'fresh/manifest.json').exists()
    physical=0;queries=0;stages={}
    for stage in ('references','fresh'):
        p=RUN/stage/'execution_ledger.json'
        if not p.exists():continue
        ledger=read(p);assert ledger['status']=='completed'
        complete=[a for a in ledger['attempts'] if a['status']=='completed']
        assert all(a['status'] in ('completed','reused') for a in ledger['attempts'])
        if stage=='references':assert sum(a['status']=='reused' for a in ledger['attempts'])==8
        exact=sum(a['actual_queries'] for a in complete)
        stages[stage]={'full_executions':len(complete),'queries':exact};physical+=len(complete);queries+=exact
    attempts=[]
    for p in SEARCH.glob('gen_*/results/execution-attempts.json'):attempts+=read(p)
    assert all(a['status'] in ('completed','failed') for a in attempts)
    complete_attempts=[a for a in attempts if a['status']=='completed']
    failed_attempts=[a for a in attempts if a['status']=='failed']
    known=[a['exact_objective_queries'] for a in attempts if a.get('exact_objective_queries') is not None]
    unknown_attempts=[a for a in attempts if a.get('exact_objective_queries') is None]
    exact=sum(known)
    stages['native']={'full_executions':len(complete_attempts),'queries':exact,'seed_cache_records':8,
        'failed_attempts':len(failed_attempts),'unknown_query_attempts':len(unknown_attempts),
        'unknown_reserved_query_upper_bound':sum(a['reserved_objective_queries'] for a in unknown_attempts)}
    physical+=len(complete_attempts);queries+=exact
    assert physical==account['totals']['physical_full_executions']<=96
    assert queries==account['totals']['research_objective_queries']<=48000000
    assert len(programs)-1==account['valid_descendants']
    assert len(account['terminal_slots'])<=7
    assert account['totals']['unknown_query_attempts']==len(unknown_attempts)
    assert account['totals']['failed_or_partial_attempts']==len(failed_attempts)
    roles=Counter();role_statuses=Counter()
    for p in (SEARCH/'engine_calls').glob('*.json'):
        receipt=read(p);assert receipt['status'] in ('returned','failed','degraded','stopped_allowance')
        role_statuses[receipt['status']]+=1
        roles[receipt['role']]+=receipt['requested_logical_responses']
    assert sum(roles.values())==account['model']['requested_logical_responses']<=36
    for role,count in roles.items():assert account['model']['roles'][role]['requested_logical_responses']==count
    final={'status':'passed','reviewed_at':datetime.now(timezone.utc).isoformat(),
           'new_objective_queries':0,'new_model_calls':0,'scope':'Independent computations over saved raw cases, frozen sources, native receipts and final analysis; no rerun.',
           'reference_and_native_cases_verified':24+8*len(programs),
           'valid_native_programs_including_seed':len(programs),'terminal_failed_evaluation_slots':failed_slots,'failed_slot_completed_cases_verified':failed_slot_complete_cases,'selected_generation':winner[1],
           'selected_mean_offline_error':winner[0],'development_selected_fixed_target':best_fixed,'seed_cache_content_exact':True,
           'fresh_comparison_performed':fresh,'freeze_source_identity_and_order_verified':True,
           'stages':stages,'physical_full_executions':physical,'research_objective_queries':queries,
           'native_logical_responses_by_role':dict(roles),'native_receipt_statuses':dict(role_statuses),'analyses':analyses,'best_descendant_descriptive_analysis':best_descendant_review,'behavioral_repetitions':behavior_repeats,
           'limitations':['Development outcomes informed search and selection; descriptive intervals do not correct selection bias.',
             'No conclusion about other chapter scenarios or algorithm families, cooperation causality, or search-method superiority follows.',
             'Shared-best gains describe reached trajectories, not isolated causal effects of quantum versus ordinary movement.']}
    (RUN/'operations/final-scientific-review.json').write_text(json.dumps(final,indent=2)+'\n')
    print(json.dumps(final,indent=2))

if __name__=='__main__':main()
