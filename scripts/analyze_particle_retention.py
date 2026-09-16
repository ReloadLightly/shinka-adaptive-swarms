#!/usr/bin/env python3
"""Saved-data-only, prospective particle-retention development analysis.

No candidate functions, simulator evaluations or model calls run here. Eight
cases remain development data even if their identities were initially fresh.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from adaptive_swarms.artifacts import read_json, resolve_json
from adaptive_swarms.allocation_figures import recovery_case_curve
from adaptive_swarms.comparison import validate_pair
from adaptive_swarms.figures import _save, _style
from adaptive_swarms.logging import atomic_json
from adaptive_swarms.simulator import _validated_config

ANALYSIS_SETTINGS = {
    'version': 'particle_retention_descriptive_v1', 'bootstrap_resamples': 2000,
    'bootstrap_seed': 2026091607, 'interval_level': .95,
    'weighting': 'equal regime weights; paired resampling within regime',
    'interpretation': 'Development-only descriptive uncertainty; no significance gate or fresh-validation claim.',
    'selection': 'minimum mean error among valid completed native seed/descendants; earlier generation then source SHA on ties',
    'decision_examples': ['first completed response in each case', 'first completed response decided at or after query50000 in each case'],
    'decision_recovery_offsets': [25, 100, 500],
    'decision_recovery_rule': 'nearest actual recorded trace at or after requested offset from decision; never cross next environment boundary',
    'episode_selection': 'post hoc lowest and highest selected-minus-heuristic completed-environment mean error, excluding initial environment; ties by earlier environment then case index',
}
FEATURES = ('personal_best_rank', 'speed_normalized', 'distance_to_best_normalized', 'velocity_alignment')
METHODS = ('random', 'heuristic', 'selected')
COLORS = {'random': '#8796a5', 'heuristic': '#d47b34', 'selected': '#187b80'}
LABELS = {'random': 'Random retention', 'heuristic': 'Refreshed-pbest heuristic', 'selected': 'Development-selected native rule'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def regime(config):
    return f"severity={config['move_severity']:g};period={config['period']}"


def describe(values, include_values=False):
    values = [float(v) for v in values]
    if not values or not all(math.isfinite(v) for v in values):
        raise ValueError('Expected nonempty finite saved measurements')
    result = {'n': len(values), 'mean': statistics.mean(values), 'sd': statistics.stdev(values) if len(values) > 1 else None,
              'median': statistics.median(values), 'min': min(values), 'max': max(values)}
    if include_values:
        result['values'] = values
    return result


def paired_effect(deltas, configs):
    groups = defaultdict(list)
    for value, config in zip(deltas, configs, strict=True):
        groups[regime(config)].append(value)
    samples = np.zeros(ANALYSIS_SETTINGS['bootstrap_resamples'])
    rng = np.random.default_rng(ANALYSIS_SETTINGS['bootstrap_seed'])
    for key in sorted(groups):
        group = groups[key]
        samples += rng.choice(group, (len(samples), len(group))).mean(axis=1) / len(groups)
    extreme = max(range(len(deltas)), key=lambda i: (abs(deltas[i]), -i))
    return {**describe(deltas, True), 'regimes': {key: describe(group, True) for key, group in sorted(groups.items())},
            'descriptive_bootstrap_95_percent_interval': np.quantile(samples, [.025, .975]).tolist(),
            'equal_regime_mean': statistics.mean(statistics.mean(group) for group in groups.values()),
            'improved_cases': sum(v < 0 for v in deltas), 'worsened_cases': sum(v > 0 for v in deltas),
            'tied_cases': sum(v == 0 for v in deltas),
            'largest_absolute_contribution': {'case_index': extreme, 'delta': deltas[extreme],
                 'contribution_to_eight_case_mean': deltas[extreme] / len(deltas), 'retained': True}}


def retention_rows(case):
    rows = []
    for response in case['response_log']:
        item = response.get('retention')
        if item is None:
            # A response may exhaust its exact budget before the five memory refreshes finish.
            if response['completed']:
                raise ValueError('A completed retention response has no saved decision')
            continue
        features = item['features']; index = item['selected_index']
        if len(features) != 5 or type(index) is not int or not 0 <= index < 5:
            raise ValueError('Invalid saved retention selection')
        if sorted(item['tie_order']) != list(range(5)):
            raise ValueError('Invalid same-snapshot tie permutation')
        if len(item['scores']) != 5 or not all(math.isfinite(value) for value in item['scores']):
            raise ValueError('Invalid saved priority scores')
        if max(item['tie_order'], key=lambda i: item['scores'][i]) != index:
            raise ValueError('Exempt particle disagrees with saved priority scores/tie order')
        expected = max(item['tie_order'], key=lambda i: -features[i]['personal_best_rank'])
        if item['heuristic_index'] != expected or item['agrees_with_heuristic'] != (index == expected):
            raise ValueError('Heuristic agreement does not use the actual decision snapshot/tie order')
        if response['relocated_indices'] != [i for i in range(5) if i != index]:
            raise ValueError('Selected particle must be the sole relocation exemption')
        if response['decision']['radius_scale'] != 1.25 or response['decision']['reset_velocity'] or response['decision']['memory'] != 'reevaluate':
            raise ValueError('Fixed recovery settings changed')
        rows.append((response, item))
    return rows


def summarize_case_behavior(case):
    rows = retention_rows(case)
    selected = [item['features'][item['selected_index']] for _, item in rows]
    ranks = Counter(int(value['personal_best_rank']) for value in selected)
    if not selected:
        return {'decisions': 0, 'no_decision': True, 'rank_probabilities': [0.] * 5,
                'heuristic_agreement': None, 'chosen_features': {}, 'snapshot_population_means': {}}
    return {'decisions': len(rows), 'no_decision': False,
            'rank_probabilities': [ranks[rank] / len(rows) for rank in range(1, 6)],
            'heuristic_agreement': sum(item['agrees_with_heuristic'] for _, item in rows) / len(rows),
            'chosen_features': {feature: describe([value[feature] for value in selected]) for feature in FEATURES},
            'snapshot_population_means': {feature: describe([statistics.mean(value[feature] for value in item['features']) for _, item in rows]) for feature in FEATURES},
            'selected_update_reached': sum(item.get('selected_update_reached', False) for _, item in rows),
            'selected_objective_queried': sum(item.get('selected_objective_queried', False) for _, item in rows),
            'incomplete_responses_with_decision': sum(not response['completed'] for response, _ in rows)}


def summarize_behavior(cases):
    summaries = [summarize_case_behavior(case) for case in cases]
    available = [row for row in summaries if not row['no_decision']]
    return {'cases': summaries, 'total_decisions': sum(row['decisions'] for row in summaries),
            'no_decision_cases': len(summaries) - len(available),
            'equal_case_rank_probabilities': np.mean([row['rank_probabilities'] for row in available], axis=0).tolist() if available else [0.] * 5,
            'equal_case_heuristic_agreement': statistics.mean(row['heuristic_agreement'] for row in available) if available else None,
            'chosen_feature_case_means': {feature: describe([row['chosen_features'][feature]['mean'] for row in available], True) for feature in FEATURES} if available else {},
            'weighting': 'Every case with a decision has equal weight; individual responses are not independent replications.',
            'agreement_scope': 'Heuristic choice recomputed from the same reached snapshot and tie order, not particle matching across methods.'}


def decision_recovery(case, decision_query):
    boundary = min((decision_query // case['config']['period'] + 1) * case['config']['period'], case['config']['budget'])
    trace = case['trace']
    values = []
    for offset in ANALYSIS_SETTINGS['decision_recovery_offsets']:
        point = next((point for point in trace if decision_query + offset <= point['evaluations'] <= boundary), None)
        values.append({'requested_query_offset': offset, 'actual_query_offset': point['evaluations'] - decision_query if point else None,
                       'evaluations': point['evaluations'] if point else None, 'current_error': point['current_error'] if point else None,
                       'missing_reason': None if point else 'No recorded point before next environmental change or budget end'})
    return {'decided_at_evaluation': decision_query, 'next_boundary_or_horizon': boundary, 'recorded_samples': values,
            'interpretation': 'Subsequent complete-optimizer error; other responses and updates can intervene, so this is not the causal effect of this choice.'}


def decision_examples(case, case_index):
    rows = [(response, item) for response, item in retention_rows(case) if response['completed']]
    selections = [('first_completed_response', rows[0] if rows else None),
                  ('first_completed_response_at_or_after_50000', next(((response, item) for response, item in rows if item['decided_at_evaluation'] >= 50000), None))]
    result = []
    for criterion, row in selections:
        if row is None:
            result.append({'case_index': case_index, 'criterion': criterion, 'available': False})
            continue
        response, item = row
        result.append({'case_index': case_index, 'criterion': criterion, 'available': True,
            'environment_seed': case['config']['environment_seed'], 'optimizer_seed': case['config']['optimizer_seed'],
            'swarm_id': response['swarm_id'], 'response_completed': response['completed'], 'retention': item,
            'recovery': decision_recovery(case, item['decided_at_evaluation'])})
    return result


def episode_details(case, environment):
    record = next(row for row in case['environment_changes'] if row['completed_environment'] == environment)
    decisions = []
    period = case['config']['period']
    for response, item in retention_rows(case):
        if item['decided_at_evaluation'] // period == environment:
            index = item['selected_index']
            decisions.append({'decided_at_evaluation': item['decided_at_evaluation'], 'swarm_id': response['swarm_id'],
                'selected_index': index, 'heuristic_index': item['heuristic_index'], 'agrees_with_heuristic': item['agrees_with_heuristic'],
                'selected_features': item['features'][index], 'all_particle_features': item['features'],
                'scores': item['scores'], 'tie_order': item['tie_order'], 'response_completed': response['completed']})
    return {'environment': environment, 'mean_error': record['environment_offline_error'],
            'initial_error': record['environment_initial_error'], 'final_error': record['environment_final_error'],
            'first_evaluation': record['first_evaluation'], 'last_evaluation': record['evaluations'],
            'trace': [point for point in case['trace'] if point['environment'] == environment], 'decisions': decisions}


def extreme_episodes(selected, heuristic):
    differences = []
    for index, (method, control) in enumerate(zip(selected, heuristic, strict=True)):
        left = {row['completed_environment']: row for row in method['environment_changes']}
        right = {row['completed_environment']: row for row in control['environment_changes']}
        if set(left) != set(right):
            raise ValueError('Paired completed-environment records differ')
        for environment in sorted(left):
            if environment == 0:
                continue
            differences.append({'case_index': index, 'environment': environment,
                'delta': left[environment]['environment_offline_error'] - right[environment]['environment_offline_error']})
    result = {'selection': ANALYSIS_SETTINGS['episode_selection'], 'eligible_episodes': len(differences),
              'all_paired_environment_effects': differences,
              'any_harmful_episode': any(row['delta'] > 0 for row in differences),
              'any_beneficial_episode': any(row['delta'] < 0 for row in differences),
              'interpretation': 'Post hoc descriptive extremes. Different reached states and intervening updates prevent single-choice causal attribution.'}
    for label, key in [('most_favorable', lambda row: (row['delta'], row['environment'], row['case_index'])),
                       ('most_unfavorable', lambda row: (-row['delta'], row['environment'], row['case_index']))]:
        chosen = min(differences, key=key)
        result[label] = {**chosen, 'config': selected[chosen['case_index']]['config'],
            'selected': episode_details(selected[chosen['case_index']], chosen['environment']),
            'heuristic': episode_details(heuristic[chosen['case_index']], chosen['environment'])}
    return result


def load_cases(folder, configs, input_hashes, run):
    values = []
    for index, config in enumerate(configs):
        path = resolve_json(folder / f'case_{index:03d}.json')
        case = read_json(path)
        if case['config'] != config:
            raise ValueError(f'Frozen case configuration differs: {path}')
        validate_pair(case, case)
        input_hashes[str(path.relative_to(run))] = sha(path)
        values.append(case)
    return values


def load_native(run, configs, hashes):
    records = []
    for folder in sorted((run / 'evolution/search_seed_630001').glob('gen_*'), key=lambda p: int(p.name.split('_')[-1])):
        checkpoint = folder / 'results/evaluation-checkpoint.json'
        if not checkpoint.exists() or read_json(checkpoint).get('status') != 'completed':
            continue
        cases = load_cases(folder / 'results', configs, hashes, run)
        correct_path = folder / 'results/correct.json'
        if correct_path.exists() and read_json(correct_path).get('correct') is False:
            continue
        records.append({'generation': int(folder.name.split('_')[-1]), 'source_sha256': sha(folder / 'main.py'),
                        'source': str((folder / 'main.py').relative_to(run)),
                        'case_mean_errors': [case['offline_error'] for case in cases],
                        'mean_offline_error': statistics.mean(case['offline_error'] for case in cases),
                        'behavior': summarize_behavior(cases)})
    return records


def aggregate_curves(cases):
    samples = defaultdict(list)
    for case in cases:
        for offset, row in recovery_case_curve(case)['offsets'].items():
            samples[int(offset)].append(row['mean_current_error'])
    return [{'offset': offset, 'mean_error': statistics.mean(values), 'contributing_cases': len(values)} for offset, values in sorted(samples.items())]


def analyze(run, selected_generation=None, output=None):
    run = Path(run)
    manifest_path = run / 'development_cases.json'
    manifest = read_json(manifest_path)
    configs = [_validated_config(config) for config in (manifest['cases'] if isinstance(manifest, dict) else manifest)]
    if len(configs) != 8 or Counter((c['move_severity'], c['period']) for c in configs) != Counter({(1.,2500):2,(1.,5000):2,(3.,2500):2,(3.,5000):2}):
        raise ValueError('Eight equally balanced declared development cases required')
    if any(c['budget'] != 100000 or c['dimension'] != 5 or c['npeaks'] != 10 for c in configs):
        raise ValueError('Unexpected numerical development contract')
    hashes = {}; outcomes = {method: load_cases(run / 'references' / method, configs, hashes, run) for method in ('random', 'heuristic')}
    programs = load_native(run, configs, hashes)
    if not programs:
        raise ValueError('No completed native seed or descendant is available')
    ranking = sorted(programs, key=lambda row: (row['mean_offline_error'], row['generation'], row['source_sha256']))
    selected = ranking[0]
    if selected_generation is not None and selected_generation != selected['generation']:
        raise ValueError('Specified selected generation disagrees with frozen development ranking/ties')
    outcomes['selected'] = load_cases(run / f"evolution/search_seed_630001/gen_{selected['generation']}/results", configs, hashes, run)
    checks = {method: [validate_pair(reference, candidate) for reference, candidate in zip(outcomes['random'], cases, strict=True)] for method, cases in outcomes.items()}
    errors = {method: [case['offline_error'] for case in cases] for method, cases in outcomes.items()}
    pairs = [('selected', 'random'), ('selected', 'heuristic'), ('heuristic', 'random')]
    comparisons = {f'{method}_minus_{control}': {'method': method, 'comparator': control,
        **paired_effect([a-b for a,b in zip(errors[method], errors[control], strict=True)], configs)} for method, control in pairs}
    result = {'analyzed_at': datetime.now(timezone.utc).isoformat(), 'study': 'particle_retention_v1', 'scope': 'development_only',
        'analysis_settings': ANALYSIS_SETTINGS, 'source_sha256': sha(__file__), 'case_manifest_sha256': sha(manifest_path),
        'configs': configs, 'selected': {key:value for key,value in selected.items() if key != 'behavior'},
        'method_errors': {method: describe(values, True) for method, values in errors.items()}, 'comparisons': comparisons,
        'best_overall_reported_method': min(METHODS, key=lambda method: statistics.mean(errors[method])),
        'behavior': {method: summarize_behavior(cases) for method, cases in outcomes.items()},
        'native_programs': programs, 'pair_checks': checks, 'input_sha256': hashes,
        'decision_examples': {method: [example for i,case in enumerate(cases) for example in decision_examples(case,i)] for method,cases in outcomes.items()},
        'episode_extremes_vs_heuristic': extreme_episodes(outcomes['selected'], outcomes['heuristic']),
        'recovery': {method: {str(period): aggregate_curves([case for case in cases if case['config']['period']==period]) for period in (2500,5000)} for method,cases in outcomes.items()},
        'query_category_totals': {method: dict(sum((Counter(case['evaluation_counts']) for case in cases), Counter())) for method,cases in outcomes.items()},
        'limitations': ['All eight cases were used for native development and selection; no fresh validation.',
            'Retained particle follows ordinary PSO; all five memories are reevaluated and retain velocity.',
            'Decision features are sequentially observed refreshed memories; no hidden freshness oracle.',
            'Behavior and post hoc episodes do not identify a causal mediator.']}
    output = Path(output) if output else run / 'analysis'
    output.mkdir(parents=True, exist_ok=True)
    atomic_json(output / 'analysis.json', result)
    render(result, output)
    return result


def render(data, output):
    _style()
    fig, axes = plt.subplots(2,2,figsize=(12.5,8.6), constrained_layout=True)
    for ax, comparator in zip(axes[0], ('random','heuristic')):
        value = data['comparisons'][f'selected_minus_{comparator}']
        for j,(key,group) in enumerate(value['regimes'].items()):
            y=4-j;ax.scatter(group['values'],y+np.linspace(-.09,.09,group['n']),s=35,color=COLORS['selected'])
            ax.scatter(group['mean'],y,s=45,marker='D',color='#243447')
        ax.plot(value['descriptive_bootstrap_95_percent_interval'],[0,0],color='#243447',lw=2.5)
        ax.scatter(value['mean'],0,s=60,marker='D',color='#243447');ax.axvline(0,color='#8796a5',ls='--',lw=1)
        ax.set_yticks([4,3,2,1,0],[*(key.replace(';','\n') for key in value['regimes']), 'Equal-regime mean\nDescriptive 95% interval'])
        ax.set(title=f"Selected − {LABELS[comparator].lower()}",xlabel='Paired development error difference\nNegative favors selected rule')
    for ax,period in zip(axes[1],(2500,5000)):
        for method in METHODS:
            rows=data['recovery'][method][str(period)]
            ax.plot([r['offset'] for r in rows],[r['mean_error'] for r in rows],label=LABELS[method],color=COLORS[method],lw=1.8)
        ax.set(title=f'Measured recovery · period {period:,}',xlabel='Actual query offset after change',ylabel='Best-discovered error')
    axes[1,1].legend(fontsize=8,frameon=False)
    for ax in axes.flat:ax.grid(alpha=.15)
    fig.suptitle('Particle retention · eight paired 5D development histories',fontsize=14)
    fig.supxlabel('All cases remain included. Cases were reused for native evolution and selection; these intervals are not fresh validation.\nRecovery averages environments within case, then cases equally; no unrecorded immediate value is interpolated.',fontsize=9)
    _save(fig,output/'paired_effects_recovery')

    fig,axes=plt.subplots(2,2,figsize=(12.5,8.2),constrained_layout=True)
    for j,method in enumerate(METHODS):
        behavior=data['behavior'][method]; rows=[row for row in behavior['cases'] if not row['no_decision']]
        axes[0,0].bar(np.arange(1,6)+(j-1)*.24,np.asarray(behavior['equal_case_rank_probabilities'])*100,width=.24,color=COLORS[method],label=LABELS[method])
        agreement=[row['heuristic_agreement']*100 for row in rows]
        axes[0,1].scatter(np.full(len(rows),j)+np.linspace(-.12,.12,len(rows)),agreement,color=COLORS[method],s=25)
        axes[0,1].scatter(j,np.mean(agreement),marker='D',color='#243447',s=60)
        distance=[row['chosen_features']['distance_to_best_normalized']['mean'] for row in rows]
        speed=[row['chosen_features']['speed_normalized']['mean'] for row in rows]
        axes[1,0].scatter(distance,speed,label=LABELS[method],color=COLORS[method],s=34,alpha=.8)
        alignment=[row['chosen_features']['velocity_alignment']['mean'] for row in rows]
        axes[1,1].scatter(alignment,np.full(len(rows),j)+np.linspace(-.10,.10,len(rows)),color=COLORS[method],s=28)
        axes[1,1].scatter(np.mean(alignment),j,marker='D',color='#243447',s=60)
    axes[0,0].set(title='Which refreshed personal-best rank survives?',xlabel='Retained particle rank (1 = best; ties share rank)',ylabel='Mean within-case decisions (%)',xticks=range(1,6))
    axes[0,0].legend(fontsize=8,frameon=False)
    axes[0,1].set(title='Agreement on the same reached snapshot',ylabel='Decisions matching heuristic (%)',ylim=(-3,103))
    axes[0,1].set_xticks(range(3),['Random','Heuristic','Selected'])
    axes[1,0].set(title='Chosen trajectory state · one dot per case',xlabel='Mean distance / default radius',ylabel='Mean speed / default radius',xscale='symlog',yscale='symlog')
    axes[1,1].set(title='Chosen velocity direction',xlabel='Case mean cosine toward refreshed swarm best',xlim=(-1.05,1.05))
    axes[1,1].set_yticks(range(3),['Random','Heuristic','Selected']);axes[1,1].axvline(0,color='#8796a5',lw=1,ls='--')
    for ax in axes.flat:ax.grid(alpha=.15)
    fig.suptitle('Retained-particle behavior · count four / radius 1.25 / retained velocity',fontsize=14)
    fig.supxlabel('Cases receive equal weight. Rank uses sequentially refreshed memories; every personal best is reevaluated.\nThe retained particle takes its ordinary PSO step; it is neither a stationary anchor nor a protected leader.',fontsize=9)
    _save(fig,output/'retention_behavior')

    fig,axes=plt.subplots(2,2,figsize=(12.5,7.9),constrained_layout=True)
    for column,key in enumerate(('most_favorable','most_unfavorable')):
        episode=data['episode_extremes_vs_heuristic'][key];period=episode['config']['period']
        for method in ('selected','heuristic'):
            saved=episode[method];trace=saved['trace']
            axes[0,column].plot([(p['evaluations']-1)%period+1 for p in trace],[p['current_error'] for p in trace],label=LABELS[method],color=COLORS[method],lw=1.8)
            decisions=saved['decisions']
            axes[1,column].scatter([p['decided_at_evaluation']%period for p in decisions],[p['selected_features']['personal_best_rank'] for p in decisions],s=30,alpha=.65,color=COLORS[method],label=LABELS[method])
        axes[0,column].set(title=f"{key.replace('_',' ').capitalize()} episode\nCase {episode['case_index']}, environment {episode['environment']}: Δ = {episode['delta']:+.4f}",ylabel='Best-discovered error')
        axes[1,column].set(xlabel='Recorded query offset in this environment',ylabel='Retained personal-best rank',yticks=range(1,6),ylim=(.7,5.3))
    axes[0,0].legend(fontsize=8,frameon=False)
    for ax in axes.flat:ax.grid(alpha=.15)
    fig.suptitle('Post hoc recovery extremes versus heuristic · complete episodes retained',fontsize=14)
    fig.supxlabel('Episodes selected by paired completed-environment mean-error difference, excluding initialization.\nRank points are decisions on each method’s own trajectory; these comparisons do not isolate a single choice’s causal effect.',fontsize=9)
    _save(fig,output/'recovery_episode_extremes')
    atomic_json(output/'figure_provenance.json',{'analysis_sha256':sha(output/'analysis.json'),'source_sha256':sha(__file__),'dimension':5,'scope':'development_only','files':{path.name:sha(path) for path in sorted(output.glob('*.png'))+sorted(output.glob('*.svg'))}})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True);parser.add_argument('--selected-generation',type=int);parser.add_argument('--output',type=Path)
    args=parser.parse_args();result=analyze(args.run,args.selected_generation,args.output)
    print(json.dumps({'selected':result['selected'],'method_errors':result['method_errors'],'comparisons':result['comparisons']},indent=2),flush=True)


if __name__=='__main__':main()
