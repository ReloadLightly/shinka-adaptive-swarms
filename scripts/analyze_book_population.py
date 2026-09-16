#!/usr/bin/env python3
"""Analyze saved MPSO population cases; no objective or model calls."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from analyze_book_mpso import (aggregate_recovery, configs_from, describe, episode_effects,
    find_case_manifest, load_cases, paired_effect, sha)
from adaptive_swarms.artifacts import read_json
from adaptive_swarms.comparison import validate_pair
from adaptive_swarms.engine_progress import terminal_failure_generations
from adaptive_swarms.figures import _save, _style
from adaptive_swarms.logging import atomic_json
import matplotlib.pyplot as plt
import numpy as np

SPEC_PATH = ROOT / 'docs/studies/book_mpso_population_v1/analysis_specification.json'
CONTROLS = ('target_3', 'target_5', 'target_7')
LABELS = {'target_3': 'Fixed target 3', 'target_5': 'Chapter 5+1 / target 5',
          'target_7': 'Fixed target 7', 'selected': 'Selected native rule'}
COLORS = {'target_3': '#596faf', 'target_5': '#d47b34', 'target_7': '#8c669c', 'selected': '#187b80'}


def population_behavior(cases):
    rows = []
    for case in cases:
        stats = case.get('population_stats', {})
        responses = case.get('population_response_log', case.get('response_log', []))
        decisions = [row for row in responses if row.get('observation', {}).get('change_detected', True)]
        histogram = Counter()
        realized = Counter()
        additions, removals = 0, 0
        for row in decisions:
            decision = row.get('decision', {})
            target = decision.get('requested_target', decision.get('target_neutral_count', row.get('requested_target', 5)))
            before = row.get('neutral_count_before', row.get('observation', {}).get('neutral_count', 5))
            after = row.get('neutral_count_after', decision.get('realized_neutral_count', before))
            histogram[str(target)] += 1
            realized[str(after)] += 1
            additions += max(0, after - before)
            removals += max(0, before - after)
        # Engine histograms cover all requested/completed updates, rather than a response-log subset.
        request_hist = stats.get('request_histogram', stats.get('requested_target_histogram', histogram))
        realized_hist = stats.get('realized_neutral_count_histogram', stats.get('realized_count_histogram', stats.get('neutral_count_histogram', realized)))
        requests = sum(request_hist.values())
        realized_total = sum(realized_hist.values())
        if not requests:
            raise ValueError('No recorded population decisions')
        row = {'decisions': requests, 'requested_target_probabilities': {str(k): request_hist.get(str(k), 0)/requests for k in range(2,9)},
               'realized_neutral_count_probabilities': {str(k): realized_hist.get(str(k), 0)/realized_total if realized_total else 0 for k in range(2,9)},
               'additions': stats.get('additions', additions), 'removals': stats.get('removals', removals),
               'query_category_shares': {key: value/case['evaluations'] for key,value in case['evaluation_counts'].items()},
               'diagnostic_provenance': stats.get('diagnostic_origin', case.get('population_diagnostic_provenance', 'Measured in population execution' if stats else 'Derived fixed-five diagnostics from compatible archived schedule execution')),
               'recorded_examples': case.get('decision_examples', stats.get('decision_examples', case.get('schedule_stats', {}).get('decision_examples', [])))}
        regular_trace = [point for point in case['trace'] if point['evaluations'] % case['config']['trace_interval'] == 0]
        row['trace_sampled_mean_swarms'] = statistics.mean(point['swarm_count'] for point in regular_trace)
        row['trace_sampled_mean_total_particles'] = statistics.mean(point.get('total_particle_count', 6*point['swarm_count']) for point in regular_trace)
        row['trace_fraction_with_different_subswarm_neutral_counts'] = statistics.mean(point.get('neutral_count_max',5)>point.get('neutral_count_min',5) for point in regular_trace)
        request_by_environment = defaultdict(set)
        for decision in decisions:
            target = decision.get('requested_target',decision.get('decision',{}).get('requested_target',5))
            request_by_environment[(decision.get('decided_at_evaluation',1)-1)//case['config']['period']].add(target)
        row['fraction_detected_environments_with_multiple_requested_targets'] = (statistics.mean(len(values)>1 for values in request_by_environment.values()) if request_by_environment else 0)
        rows.append(row)
    return {'cases': rows, 'decisions': sum(row['decisions'] for row in rows),
            'additions': sum(row['additions'] for row in rows), 'removals': sum(row['removals'] for row in rows),
            'equal_case_trace_sampled_mean_swarms': statistics.mean(row['trace_sampled_mean_swarms'] for row in rows),
            'equal_case_trace_sampled_mean_total_particles': statistics.mean(row['trace_sampled_mean_total_particles'] for row in rows),
            'equal_case_trace_fraction_with_different_subswarm_neutral_counts': statistics.mean(row['trace_fraction_with_different_subswarm_neutral_counts'] for row in rows),
            'equal_case_fraction_detected_environments_with_multiple_requested_targets': statistics.mean(row['fraction_detected_environments_with_multiple_requested_targets'] for row in rows),
            'equal_case_requested_target_probabilities': {str(k): statistics.mean(row['requested_target_probabilities'][str(k)] for row in rows) for k in range(2,9)},
            'equal_case_realized_neutral_count_probabilities': {str(k): statistics.mean(row['realized_neutral_count_probabilities'][str(k)] for row in rows) for k in range(2,9)},
            'equal_case_query_category_shares': {key: statistics.mean(row['query_category_shares'].get(key,0) for row in rows) for key in sorted(set().union(*(row['query_category_shares'] for row in rows)))},
            'interpretation': 'Requests occur only at counted detections; at most one particle changes per decision. Update observations are not independent replicates. Population changes are within swarms, not inter-swarm transfers.'}


def population_curves(cases):
    by_query = defaultdict(list)
    for case in cases:
        for point in case['trace']:
            swarms = point['swarm_count']
            neutrals = point.get('total_neutral_count', 5*swarms)
            total = point.get('total_particle_count', point.get('total_particles', neutrals+swarms))
            by_query[point['evaluations']].append({'offline_error': point['offline_error'], 'current_error': point['current_error'],
                'swarm_count': swarms, 'total_neutral_count': neutrals, 'total_particle_count': total,
                'mean_neutral_count': neutrals/swarms if swarms else 0,
                'neutral_count_min': point.get('neutral_count_min', 5), 'neutral_count_max': point.get('neutral_count_max', 5)})
    return [{'evaluations': query, 'contributing_cases': len(rows),
             **{key: statistics.mean(row[key] for row in rows) for key in rows[0]}}
            for query,rows in sorted(by_query.items()) if len(rows)==len(cases)]


def population_episode_effects(selected, reference):
    details = episode_effects(selected, reference)
    eligible = [row for row in details['all_completed_environment_effects'] if not row['initialization_environment']]
    for label, sign in (('most_favorable', 1), ('most_unfavorable', -1)):
        chosen = min(eligible, key=lambda row: (sign*row['contribution_to_paired_mean'], row['case_index'], row['environment']))
        epoch, index = chosen['environment'], chosen['case_index']
        details[label] = {**chosen,
            'selected_trace': [point for point in selected[index]['trace'] if point['environment']==epoch],
            'reference_trace': [point for point in reference[index]['trace'] if point['environment']==epoch],
            'selected_decisions': [row for row in selected[index].get('response_log',[]) if epoch*5000 < row.get('decided_at_evaluation',0) <= (epoch+1)*5000],
            'reference_decisions': [row for row in reference[index].get('response_log',[]) if epoch*5000 < row.get('decided_at_evaluation',0) <= (epoch+1)*5000]}
    return details


def native_programs(run, configs, hashes):
    searches = [folder for folder in (run/'evolution').glob('*') if folder.is_dir()]
    if not searches:
        return None, [], []
    if len(searches)!=1:
        raise ValueError('Expected one native search')
    search=searches[0]
    programs, slots=[],[]
    for folder in sorted(search.glob('gen_*'),key=lambda p:int(p.name.split('_')[-1])):
        path=folder/'results/evaluation-checkpoint.json'
        if not path.exists():
            continue
        saved=read_json(path)
        row={'generation':int(folder.name.split('_')[-1]),'status':saved['status'],
             'source':str((folder/'main.py').relative_to(run)),'source_sha256':sha(folder/'main.py')}
        slots.append(row)
        if saved['status']!='completed':
            continue
        correct=folder/'results/correct.json'
        if correct.exists() and read_json(correct).get('correct') is False:
            continue
        cases=load_cases(folder/'results',configs,hashes,run)
        programs.append({**row,'mean_offline_error':statistics.mean(c['offline_error'] for c in cases),
                         'case_errors':[c['offline_error'] for c in cases],'behavior':population_behavior(cases)})
    seen={r['generation'] for r in slots}
    for generation in sorted(terminal_failure_generations(search)-seen):
        slots.append({'generation':generation,'status':'terminal_failed_proposal','objective_evaluation_submitted':False})
    return search,programs,sorted(slots,key=lambda r:r['generation'])


def analyze(run,phase='development',output=None,references_only=False):
    run=Path(run).resolve()
    spec=read_json(SPEC_PATH)
    manifest=find_case_manifest(run,phase)
    configs=configs_from(manifest)
    hashes={}
    programs,slots=[],[]
    selection=read_json(run/'selection.json') if (run/'selection.json').exists() else {}
    if phase=='development':
        outcomes={method:load_cases(run/'references'/method,configs,hashes,run) for method in CONTROLS}
        best_fixed=min(CONTROLS,key=lambda m:(statistics.mean(c['offline_error'] for c in outcomes[m]),int(m[-1])))
        selected=None
        if not references_only:
            search,programs,slots=native_programs(run,configs,hashes)
            if not programs:
                raise ValueError('No completed valid native program')
            selected=min(programs,key=lambda r:(r['mean_offline_error'],r['generation'],r['source_sha256']))
            outcomes['selected']=load_cases(search/f"gen_{selected['generation']}/results",configs,hashes,run)
    else:
        best_fixed=selection.get('selected_fixed_target',selection.get('best_fixed_target'))
        if isinstance(best_fixed,int):
            best_fixed=f'target_{best_fixed}'
        if isinstance(best_fixed,dict):
            best_fixed=best_fixed.get('method', f"target_{best_fixed.get('target')}")
        if best_fixed not in CONTROLS:
            raise ValueError('Frozen development-selected fixed target missing')
        aliases=selection.get('execution_aliases',{})
        outcomes={method:load_cases(run/'fresh'/aliases.get(method,method),configs,hashes,run) for method in dict.fromkeys(('target_5',best_fixed,'selected'))}
        selected=selection.get('selected')
    aliases={}
    if 'selected' in outcomes:
        for method in CONTROLS:
            if method in outcomes and all(a['offline_error']==b['offline_error'] and a['evaluation_counts']==b['evaluation_counts'] and a['trace']==b['trace'] for a,b in zip(outcomes['selected'],outcomes[method])):
                aliases['selected']=method
                break
    errors={m:[c['offline_error'] for c in cases] for m,cases in outcomes.items()}
    checks={m:[validate_pair(a,b) for a,b in zip(outcomes['target_5'],cases,strict=True)] for m,cases in outcomes.items()}
    pairs=[(m,'target_5') for m in ('target_3','target_7') if m in outcomes]
    if 'selected' in outcomes:
        pairs += list(dict.fromkeys((('selected','target_5'),('selected',best_fixed))))
    contrasts={f'{a}_minus_{b}':{'method':a,'reference':b,**paired_effect([x-y for x,y in zip(errors[a],errors[b])],spec)} for a,b in pairs}
    selected_error=statistics.mean(errors['selected']) if 'selected' in errors else None
    fresh_trigger=bool(selected_error is not None and selected and selected.get('generation',0)>0 and 'selected' not in aliases and selected_error<statistics.mean(errors['target_5']) and selected_error<statistics.mean(errors[best_fixed])) if phase=='development' else selection.get('fresh_comparison_required')
    result={'study':'book_mpso_population_v1','phase':phase,'analyzed_at':datetime.now(timezone.utc).isoformat(),
            'analysis_settings':spec,'analysis_specification_sha256':sha(SPEC_PATH),'analysis_source_sha256':sha(__file__),
            'case_manifest_sha256':sha(manifest),'input_sha256':hashes,'configs':configs,
            'selected':{k:v for k,v in selected.items() if k!='behavior'} if selected else None,
            'best_fixed_target':best_fixed,'fresh_comparison_required':fresh_trigger,'execution_aliases':aliases,
            'native_programs':programs,'native_slots':slots,'pair_checks':checks,
            'method_errors':{m:describe(v) for m,v in errors.items()},'contrasts':contrasts,
            'behavior':{m:population_behavior(c) for m,c in outcomes.items()},
            'population_trajectories':{m:population_curves(c) for m,c in outcomes.items()},
            'recovery':{m:aggregate_recovery(c) for m,c in outcomes.items()},
            'episode_influence':{m:population_episode_effects(outcomes['selected'],outcomes[m]) for m in dict.fromkeys(('target_5',best_fixed))} if 'selected' in outcomes else {},
            'query_category_totals':{m:dict(sum((Counter(c['evaluation_counts']) for c in cases),Counter())) for m,cases in outcomes.items()},
            'interpretation':spec['development_interpretation' if phase=='development' else 'fresh_interpretation']}
    output=Path(output) if output else run/'analysis'/phase
    output.mkdir(parents=True,exist_ok=True)
    atomic_json(output/'analysis.json',result)
    render(result,output)
    (output/'tables.md').write_text(markdown_tables(result))
    return result


def markdown_tables(data):
    methods=list(data['method_errors'])
    lines=[f"## {data['phase'].capitalize()} paired outcomes",'', '| Case | '+' | '.join(LABELS[m] for m in methods)+' |', '|---|'+'---:|'*len(methods)]
    for index in range(8):
        lines.append(f'| {index:03d} | '+' | '.join(f"{data['method_errors'][m]['values'][index]:.6f}" for m in methods)+' |')
    lines += ['', '| Contrast | Every paired effect, cases 000–007 | Mean | Median | SD | Descriptive 95% interval | W / L / T |', '|---|---|---:|---:|---:|---|---:|']
    for name,row in data['contrasts'].items():
        low,high=row['descriptive_95_percent_interval']
        lines.append(f"| {name} | "+', '.join(f'{v:+.6f}' for v in row['values'])+f" | {row['mean']:+.6f} | {row['median']:+.6f} | {row['sd']:.6f} | [{low:+.6f}, {high:+.6f}] | {row['wins']} / {row['losses']} / {row['ties']} |")
    return '\n'.join(lines)+'\n'


def render(data,output):
    _style()
    methods=[m for m in data['method_errors'] if m not in data['execution_aliases']]
    fig,axes=plt.subplots(2,2,figsize=(12,8.4),constrained_layout=True)
    for method in methods:
        rows=data['population_trajectories'][method]
        queries=[r['evaluations'] for r in rows]
        for ax,field in ((axes[0,0],'mean_neutral_count'),(axes[0,1],'total_particle_count'),(axes[1,0],'offline_error')):
            ax.plot(queries,[r[field] for r in rows],color=COLORS[method],label=LABELS[method],lw=1.65)
    axes[0,0].set(title='Realized neutral population per subswarm',ylabel='Mean neutral particles',ylim=(1.8,8.2))
    axes[0,1].set(title='Total optimizer population',ylabel='Neutral + permanent quantum particles')
    axes[1,0].set(title='Tracking over the full counted horizon',ylabel='Cumulative offline error')
    for ax in (axes[0,0],axes[0,1],axes[1,0]):
        ax.set(xlabel='Counted objective evaluations',xlim=(0,500000))
        ax.ticklabel_format(axis='x',style='sci',scilimits=(0,0))
        ax.grid(alpha=.15)
    axes[0,0].legend(frameon=False,fontsize=8)
    contrast_keys=([k for k in data['contrasts'] if k.startswith('selected_')] if 'selected' not in data['execution_aliases'] else [])
    if not contrast_keys:
        contrast_keys=[k for k in data['contrasts'] if not k.startswith('selected_')]
    for index,key in enumerate(contrast_keys):
        row=data['contrasts'][key]
        axes[1,1].scatter(row['values'],np.arange(8)+index*.17,s=25,color=COLORS[row['method']],label=f"{LABELS[row['method']]} − {LABELS[row['reference']]}")
        axes[1,1].plot(row['descriptive_95_percent_interval'],[-1-index*.55]*2,color=COLORS[row['method']],lw=2)
        axes[1,1].scatter(row['mean'],-1-index*.55,marker='D',color=COLORS[row['method']],s=40)
    axes[1,1].axvline(0,color='#8796a5',ls='--',lw=1)
    axes[1,1].set(title='Every paired case, mean and descriptive 95% interval',xlabel='Paired offline-error difference (negative favors first)',yticks=range(8),yticklabels=[f'{i:03d}' for i in range(8)])
    axes[1,1].legend(frameon=False,fontsize=7,loc='best')
    axes[1,1].grid(alpha=.15)
    fig.suptitle(f"MPSO population allocation · eight {data['phase']} pairs · 500,000 queries per case",fontsize=14)
    fig.supxlabel('Five dimensions, ten peaks, severity 1, period 5,000. All methods start with five neutrals per new swarm.\n'+('Reused development histories informed selection; intervals are descriptive, not fresh confirmation.' if data['phase']=='development' else 'Frozen rules on fresh histories; exploratory comparison in one chapter condition.'),fontsize=9)
    _save(fig,output/'population_and_tracking')
    fig,axes=plt.subplots(1,3,figsize=(13,4.5),constrained_layout=True)
    x=np.arange(2,9)
    width=.8/len(methods)
    for i,method in enumerate(methods):
        behavior=data['behavior'][method]
        shift=(i-(len(methods)-1)/2)*width
        for panel,field in ((0,'equal_case_requested_target_probabilities'),(1,'equal_case_realized_neutral_count_probabilities')):
            axes[panel].bar(x+shift,[100*behavior[field][str(k)] for k in x],width=width,color=COLORS[method],label=LABELS[method])
        curve=data['recovery'][method]
        axes[2].plot([r['offset'] for r in curve],[r['mean_error'] for r in curve],color=COLORS[method],lw=1.8,label=LABELS[method])
    axes[0].set(title='Requested population at counted detections',xlabel='Requested target',ylabel='Within-case decisions (%)',xticks=x)
    axes[1].set(title='Realized neutral population',xlabel='Neutral particles',ylabel='Within-case subswarm updates (%)',xticks=x)
    axes[2].set(title='Measured recovery',xlabel='Actual query offset after environmental change',ylabel='Best-discovered error')
    axes[0].legend(frameon=False,fontsize=7)
    for ax in axes:ax.grid(alpha=.15,axis='y')
    fig.suptitle('Requested targets, realized populations and recovery',fontsize=14)
    fig.supxlabel('Equal case weight. Dynamics include births, exclusions and detection; no particle transfers between subswarms.\nRecovery excludes initialization and uses saved actual query offsets without replay.',fontsize=9)
    _save(fig,output/'population_behavior')
    if data['native_programs']:
        fig,ax=plt.subplots(figsize=(9.5,4.5),constrained_layout=True)
        rows=data['native_programs']
        ax.scatter([r['generation'] for r in rows],[r['mean_offline_error'] for r in rows],color=COLORS['selected'],s=55,label='Native program',zorder=3)
        for method in CONTROLS:
            if method in data['method_errors']:ax.axhline(data['method_errors'][method]['mean'],color=COLORS[method],ls='--',label=LABELS[method])
        ax.set(title='One bounded native population search',xlabel='Generation slot (zero is target 5)',ylabel='Mean development offline error',xticks=range(max(r['generation'] for r in data['native_slots'])+1))
        ax.legend(frameon=False,fontsize=8);ax.grid(alpha=.15)
        _save(fig,output/'native_search')
    atomic_json(output/'figure_provenance.json',{'analysis_sha256':sha(output/'analysis.json'),'source_sha256':sha(__file__),'dimension':5,'phase':data['phase'],'objective_calls':0,'model_calls':0,'files':{p.name:sha(p) for p in sorted(output.glob('*.png'))+sorted(output.glob('*.svg'))}})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--phase',choices=('development','fresh'),default='development')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--references-only',action='store_true')
    args=parser.parse_args()
    data=analyze(args.run,args.phase,args.output,args.references_only)
    print(json.dumps({'phase':data['phase'],'selected':data['selected'],'best_fixed_target':data['best_fixed_target'],'fresh_comparison_required':data['fresh_comparison_required'],'method_errors':data['method_errors']},indent=2),flush=True)


if __name__=='__main__':main()
