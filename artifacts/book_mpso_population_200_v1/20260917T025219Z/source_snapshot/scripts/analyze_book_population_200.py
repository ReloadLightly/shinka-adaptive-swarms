#!/usr/bin/env python3
"""Analyze saved 200-peak MPSO population cases; no objective or model calls."""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from analyze_book_mpso import (aggregate_recovery, describe, episode_effects,
    find_case_manifest, load_cases, paired_effect, sha)
from adaptive_swarms.artifacts import read_json, resolve_json
from adaptive_swarms.simulator import _validated_config
from adaptive_swarms.comparison import validate_pair
from adaptive_swarms.engine_progress import terminal_failure_generations
from adaptive_swarms.figures import _save, _style
from adaptive_swarms.logging import atomic_json
import matplotlib.pyplot as plt
import numpy as np

SPEC_PATH = ROOT / 'docs/studies/book_mpso_population_200_v1/analysis_specification.json'
CONTROLS = ('target_3', 'target_5')
LABELS = {'target_3': 'Fixed target 3', 'target_5': 'Chapter 5+1 / target 5',
          'selected': 'Selected native rule', 'best_descendant': 'Best tested descendant'}
COLORS = {'target_3': '#596faf', 'target_5': '#d47b34', 'selected': '#187b80', 'best_descendant': '#187b80'}


def configs_from(path):
    """Reject accidental reuse of the ten-peak/eight-case study."""
    manifest = read_json(path)
    rows = manifest if isinstance(manifest, list) else manifest['cases']
    defaults = ({} if isinstance(manifest, list) else
                {key: value for key, value in manifest.items() if key in _validated_config({})})
    configs = [_validated_config({**defaults, **row}) for row in rows]
    if len(configs) != 4 or len({(c['environment_seed'], c['optimizer_seed']) for c in configs}) != 4:
        raise ValueError('Expected four distinct paired cases')
    required = {'budget': 500000, 'dimension': 5, 'npeaks': 200,
                'move_severity': 1., 'period': 5000, 'correlation': 0., 'nexcess': 1}
    if any(any(config[key] != value for key, value in required.items()) for config in configs):
        raise ValueError('Saved suite is not the frozen 200-peak chapter condition')
    return configs


def source_observations(path):
    """Describe explicitly referenced public fields; this is source use, not causality."""
    source = Path(path).read_text()
    tree = ast.parse(source)
    fields = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
            fields.add(node.slice.value)
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
              and node.func.attr == 'get' and node.args and isinstance(node.args[0], ast.Constant)
              and isinstance(node.args[0].value, str)):
            fields.add(node.args[0].value)
    workload = sorted(fields & {'swarm_count', 'total_particle_count'})
    history = sorted(fields & {'previous_requested_target', 'previous_conversion_count',
                              'recent_improvement', 'previous_best_fitness'})
    return {'source': source, 'literal_observation_fields': sorted(fields),
            'workload_fields': workload, 'history_fields': history,
            'interpretation': 'Static literal field references, requiring human source review; use does not establish an isolated causal effect.'}


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
        # Swarm identifiers survive within a lifetime; replacements receive fresh identifiers.
        # Ignore no-ops when measuring reversals of actual resizing direction.
        by_swarm = defaultdict(list)
        for decision in decisions:
            by_swarm[decision['swarm_id']].append(decision)
        histories = []
        for swarm, history in sorted(by_swarm.items()):
            history = sorted(history, key=lambda item: item['decided_at_evaluation'])
            targets = [item['requested_target'] for item in history]
            changes = [item['neutral_count_after'] - item['neutral_count_before'] for item in history]
            directions = [value for value in changes if value]
            histories.append({'swarm_id': swarm, 'recorded_decisions': len(history),
                'first_decision_evaluation': history[0]['decided_at_evaluation'],
                'last_decision_evaluation': history[-1]['decided_at_evaluation'],
                'distinct_requested_targets': sorted(set(targets)),
                'target_switches': sum(a != b for a, b in zip(targets, targets[1:])),
                'resize_direction_reversals': sum(a != b for a, b in zip(directions, directions[1:])),
                'additions': sum(value > 0 for value in changes),
                'removals': sum(value < 0 for value in changes)})
        row['swarm_histories'] = histories
        row['target_switches'] = sum(item['target_switches'] for item in histories)
        row['resize_direction_reversals'] = sum(item['resize_direction_reversals'] for item in histories)
        row['swarm_lifetimes_with_both_growth_and_shrinkage'] = sum(item['additions'] > 0 and item['removals'] > 0 for item in histories)
        row['first_resize_evaluation'] = min((item['decided_at_evaluation'] for item in decisions
                                             if item['neutral_count_after'] != item['neutral_count_before']), default=None)
        row['last_resize_evaluation'] = max((item['decided_at_evaluation'] for item in decisions
                                            if item['neutral_count_after'] != item['neutral_count_before']), default=None)
        row['query_share_groups'] = {
            'movement': sum(row['query_category_shares'].get(key, 0) for key in ('ordinary', 'temporary_quantum', 'permanent_quantum')),
            'detection_and_memory': sum(row['query_category_shares'].get(key, 0) for key in ('detection', 'memory')),
            'initialization_and_exclusion': sum(value for key, value in row['query_category_shares'].items()
                                               if key not in ('ordinary', 'temporary_quantum', 'permanent_quantum', 'detection', 'memory'))}
        rows.append(row)
    return {'cases': rows, 'decisions': sum(row['decisions'] for row in rows),
            'additions': sum(row['additions'] for row in rows), 'removals': sum(row['removals'] for row in rows),
            'target_switches': sum(row['target_switches'] for row in rows),
            'resize_direction_reversals': sum(row['resize_direction_reversals'] for row in rows),
            'swarm_lifetimes_with_both_growth_and_shrinkage': sum(row['swarm_lifetimes_with_both_growth_and_shrinkage'] for row in rows),
            'equal_case_query_share_groups': {key: statistics.mean(row['query_share_groups'][key] for row in rows)
                                            for key in rows[0]['query_share_groups']},
            'equal_case_trace_sampled_mean_swarms': statistics.mean(row['trace_sampled_mean_swarms'] for row in rows),
            'equal_case_trace_sampled_mean_total_particles': statistics.mean(row['trace_sampled_mean_total_particles'] for row in rows),
            'equal_case_trace_fraction_with_different_subswarm_neutral_counts': statistics.mean(row['trace_fraction_with_different_subswarm_neutral_counts'] for row in rows),
            'equal_case_fraction_detected_environments_with_multiple_requested_targets': statistics.mean(row['fraction_detected_environments_with_multiple_requested_targets'] for row in rows),
            'equal_case_requested_target_probabilities': {str(k): statistics.mean(row['requested_target_probabilities'][str(k)] for row in rows) for k in range(2,9)},
            'equal_case_realized_neutral_count_probabilities': {str(k): statistics.mean(row['realized_neutral_count_probabilities'][str(k)] for row in rows) for k in range(2,9)},
            'equal_case_query_category_shares': {key: statistics.mean(row['query_category_shares'].get(key,0) for row in rows) for key in sorted(set().union(*(row['query_category_shares'] for row in rows)))},
            'interpretation': 'Requests occur only at counted detections; at most one particle changes per decision. Update observations are not independent replicates. Population changes are within swarms, not inter-swarm transfers. Swarm count does not measure distinct-peak coverage. Reversals exclude no-op decisions and cannot bridge replacement swarm identities.'}


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
        period = selected[index]['config']['period']
        details[label] = {**chosen,
            'selected_trace': [point for point in selected[index]['trace'] if epoch*period < point['evaluations'] <= (epoch+1)*period],
            'reference_trace': [point for point in reference[index]['trace'] if epoch*period < point['evaluations'] <= (epoch+1)*period],
            'selected_decisions': [row for row in selected[index].get('response_log',[]) if epoch*period < row.get('decided_at_evaluation',0) <= (epoch+1)*period],
            'reference_decisions': [row for row in reference[index].get('response_log',[]) if epoch*period < row.get('decided_at_evaluation',0) <= (epoch+1)*period]}
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
        if not correct.exists() or read_json(correct).get('correct') is not True:
            continue
        if saved.get('identity', {}).get('program_sha256') != row['source_sha256']:
            raise ValueError(f'Completed checkpoint source hash mismatch: {folder}')
        cases=load_cases(folder/'results',configs,hashes,run)
        programs.append({**row,'mean_offline_error':statistics.mean(c['offline_error'] for c in cases),
                         'case_errors':[c['offline_error'] for c in cases],
                         'source_observations':source_observations(folder/'main.py'),
                         'behavior':population_behavior(cases)})
    seen={r['generation'] for r in slots}
    for generation in sorted(terminal_failure_generations(search)-seen):
        slots.append({'generation':generation,'status':'terminal_failed_proposal','objective_evaluation_submitted':False})
    return search,programs,sorted(slots,key=lambda r:r['generation'])


def partial_inventory(run, phase, configs, spec, manifest, output):
    """Preserve finished cases without assigning an incomplete-suite fitness."""
    folders = ({method: run/'references'/method for method in CONTROLS} if phase == 'development'
               else {method: run/'fresh'/method for method in (*CONTROLS, 'selected')})
    if phase == 'development':
        folders.update({str(folder.relative_to(run)): folder/'results'
                        for folder in sorted((run/'evolution').glob('*/gen_*'))})
    inventory, hashes, cases = {}, {}, {}
    for method, folder in folders.items():
        saved = {}
        for index, config in enumerate(configs):
            path = resolve_json(folder/f'case_{index:03d}.json')
            if not path.exists():
                continue
            case = read_json(path)
            if case['config'] != config:
                raise ValueError(f'Saved configuration differs from frozen suite: {path}')
            validate_pair(case, case)
            hashes[str(path.relative_to(run))] = sha(path)
            saved[index] = case
        cases[method] = saved
        inventory[method] = {'completed_case_indices': list(saved),
            'complete_suite': len(saved) == len(configs),
            'case_errors': {str(index): case['offline_error'] for index, case in saved.items()},
            'queries_in_saved_records': sum(case['evaluations'] for case in saved.values())}
    checks = {method: {str(index): validate_pair(cases['target_5'][index], case)
                      for index, case in values.items() if index in cases['target_5']}
              for method, values in cases.items()}
    result = {'study': 'book_mpso_population_200_v1', 'phase': phase, 'status': 'partial_inventory_only',
              'analyzed_at': datetime.now(timezone.utc).isoformat(), 'configs': configs,
              'analysis_settings': spec, 'analysis_specification_sha256': sha(SPEC_PATH),
              'analysis_source_sha256': sha(__file__), 'case_manifest_sha256': sha(manifest),
              'input_sha256': hashes, 'inventory': inventory, 'pair_checks': checks,
              'selected': None, 'best_fixed_target': None, 'fresh_comparison_required': None,
              'method_errors': {},
              'completed_case_diagnostics': {method: {str(index): {
                  'offline_error': case['offline_error'], 'evaluations': case['evaluations'],
                  'evaluation_counts': case['evaluation_counts'],
                  'population_behavior': population_behavior([case]),
                  'population_trajectory': population_curves([case]),
                  'interpretation': 'A completed individual case in an incomplete study; not a method-comparison estimate or native evolutionary result.'}
                  for index, case in saved.items()} for method, saved in cases.items()},
              'interpretation': 'Incomplete checkpoint inventory: no partial mean is ranked and no negative evolutionary conclusion or fresh-stage decision is made.'}
    output = Path(output) if output else run/'analysis'/f'{phase}_partial'
    output.mkdir(parents=True, exist_ok=True)
    atomic_json(output/'analysis.json', result)
    render_partial(result, output)
    return result


def render_partial(data, output):
    """Plot finished individual executions without implying a completed comparison."""
    records = [(method, index, row) for method, rows in data['completed_case_diagnostics'].items()
               for index, row in rows.items()]
    if not records:
        return
    _style()
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    swarm_ax = axes[0, 1].twinx()
    for method, index, record in records:
        trajectory = record['population_trajectory']
        queries = [row['evaluations'] for row in trajectory]
        label = f"{LABELS.get(method, method)}, case {int(index):03d}"
        color = COLORS.get(method, '#187b80')
        axes[0, 0].plot(queries, [row['mean_neutral_count'] for row in trajectory], color=color, label=label)
        axes[0, 0].fill_between(queries, [row['neutral_count_min'] for row in trajectory],
                              [row['neutral_count_max'] for row in trajectory], color=color, alpha=.1)
        axes[0, 1].plot(queries, [row['total_particle_count'] for row in trajectory], color=color, label='Total particles')
        swarm_ax.plot(queries, [row['swarm_count'] for row in trajectory], color='#596faf', ls=':', lw=1.2, label='Subswarms')
        axes[1, 0].plot(queries, [row['offline_error'] for row in trajectory], color=color)
        axes[1, 1].plot(queries, [row['current_error'] for row in trajectory], color=color, lw=.9)
    axes[0, 0].set(title='Realized neutral count within each subswarm', ylabel='Neutral particles', ylim=(1.8, 8.2))
    axes[0, 0].legend(frameon=False, fontsize=8)
    axes[0, 1].set(title='Optimizer population and subswarm count', ylabel='Total particles (solid)')
    swarm_ax.set(ylabel='Subswarms (dotted)')
    axes[0, 1].legend(frameon=False, fontsize=8, loc='upper left')
    swarm_ax.legend(frameon=False, fontsize=8, loc='upper right')
    axes[1, 0].set(title='Cumulative tracking error', ylabel='Offline error', yscale='log')
    axes[1, 1].set(title='Tracking through environmental changes', ylabel='Current best-discovered error')
    for ax in axes.flat:
        ax.set(xlabel='Counted objective evaluations', xlim=(0, 500000))
        ax.ticklabel_format(axis='x', style='sci', scilimits=(0, 0))
        ax.grid(alpha=.15)
    count = len(records)
    fig.suptitle(f"200-peak MPSO · {count} completed reference case{'s' if count != 1 else ''} · search not run", fontsize=14)
    fig.supxlabel('Five dimensions, severity 1, period 5,000; 500,000 counted queries per execution. Measured saved traces.\nRuntime-constrained stop before evolution: no paired control comparison, selected native rule or improvement claim.', fontsize=9)
    _save(fig, output/'population_and_tracking')
    atomic_json(output/'figure_provenance.json', {'analysis_sha256': sha(output/'analysis.json'),
        'source_sha256': sha(__file__), 'dimension': 5, 'npeaks': 200,
        'status': data['status'], 'completed_records': count, 'objective_calls': 0, 'model_calls': 0,
        'files': {path.name: sha(path) for path in sorted(output.glob('*.png')) + sorted(output.glob('*.svg'))}})


def analyze(run,phase='development',output=None,references_only=False,allow_partial=False):
    run=Path(run).resolve()
    spec=read_json(SPEC_PATH)
    manifest=find_case_manifest(run,phase)
    configs=configs_from(manifest)
    hashes={}
    programs,slots=[],[]
    best_descendant, descendant_cases = None, None
    selection=read_json(run/'selection.json') if (run/'selection.json').exists() else {}
    if allow_partial:
        folder = run/('references' if phase == 'development' else 'fresh')
        expected = CONTROLS if phase == 'development' else (*CONTROLS, 'selected')
        incomplete = any(not resolve_json(folder/method/f'case_{index:03d}.json').exists()
                         for method in expected for index in range(len(configs)))
        no_native = phase == 'development' and not references_only and not any(
            read_json(path).get('status') == 'completed'
            for path in (run/'evolution').glob('*/gen_*/results/evaluation-checkpoint.json'))
        if incomplete or no_native:
            return partial_inventory(run, phase, configs, spec, manifest, output)
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
            descendants = [row for row in programs if row['generation'] > 0]
            if descendants:
                best_descendant = min(descendants,key=lambda r:(r['mean_offline_error'],r['generation'],r['source_sha256']))
                descendant_cases = load_cases(search/f"gen_{best_descendant['generation']}/results",configs,hashes,run)
    else:
        best_fixed=selection.get('selected_fixed_target',selection.get('best_fixed_target'))
        if isinstance(best_fixed,int):
            best_fixed=f'target_{best_fixed}'
        if isinstance(best_fixed,dict):
            best_fixed=best_fixed.get('method', f"target_{best_fixed.get('target')}")
        if best_fixed not in CONTROLS:
            raise ValueError('Frozen development-selected fixed target missing')
        aliases=selection.get('execution_aliases',{})
        outcomes={method:load_cases(run/'fresh'/aliases.get(method,method),configs,hashes,run) for method in (*CONTROLS,'selected')}
        selected=selection.get('selected')
    aliases={}
    if 'selected' in outcomes:
        for method in CONTROLS:
            if method in outcomes and all(a['offline_error']==b['offline_error'] and a['evaluation_counts']==b['evaluation_counts'] and a['trace']==b['trace'] for a,b in zip(outcomes['selected'],outcomes[method])):
                aliases['selected']=method
                break
    errors={m:[c['offline_error'] for c in cases] for m,cases in outcomes.items()}
    checks={m:[validate_pair(a,b) for a,b in zip(outcomes['target_5'],cases,strict=True)] for m,cases in outcomes.items()}
    pairs=[(m,'target_5') for m in ('target_3',) if m in outcomes]
    if 'selected' in outcomes:
        pairs += [('selected', method) for method in CONTROLS]
    contrasts={f'{a}_minus_{b}':{'method':a,'reference':b,**paired_effect([x-y for x,y in zip(errors[a],errors[b])],spec)} for a,b in pairs}
    selected_error=statistics.mean(errors['selected']) if 'selected' in errors else None
    fresh_trigger=bool(selected_error is not None and selected and selected.get('generation',0)>0 and 'selected' not in aliases and selected_error<statistics.mean(errors['target_5']) and selected_error<statistics.mean(errors[best_fixed])) if phase=='development' else selection.get('fresh_comparison_required')
    result={'study':'book_mpso_population_200_v1','phase':phase,'analyzed_at':datetime.now(timezone.utc).isoformat(),
            'status': 'references_complete' if references_only else 'complete_program_analysis',
            'analysis_settings':spec,'analysis_specification_sha256':sha(SPEC_PATH),'analysis_source_sha256':sha(__file__),
            'case_manifest_sha256':sha(manifest),'input_sha256':hashes,'configs':configs,
            'selected':{k:v for k,v in selected.items() if k!='behavior'} if selected else None,
            'best_descendant': {k:v for k,v in best_descendant.items() if k!='behavior'} if best_descendant else None,
            'best_descendant_interpretation': 'Lowest-error complete descendant, even if worse than the seed. This is an explanatory comparison and does not replace selection including the seed.',
            'best_descendant_behavior': population_behavior(descendant_cases) if descendant_cases else None,
            'best_descendant_population_trajectories': population_curves(descendant_cases) if descendant_cases else None,
            'best_descendant_recovery': aggregate_recovery(descendant_cases) if descendant_cases else None,
            'best_descendant_versus_target_5': {'method':'best_descendant','reference':'target_5',**paired_effect([a['offline_error']-b['offline_error'] for a,b in zip(descendant_cases,outcomes['target_5'])],spec)} if descendant_cases else None,
            'best_descendant_versus_controls': {method: {'method':'best_descendant','reference':method,
                **paired_effect([a['offline_error']-b['offline_error'] for a,b in zip(descendant_cases,outcomes[method],strict=True)],spec)}
                for method in CONTROLS} if descendant_cases else {},
            'best_descendant_episode_influence': population_episode_effects(descendant_cases,outcomes['target_5']) if descendant_cases else None,
            'best_fixed_target':best_fixed,'fresh_comparison_required':fresh_trigger,'execution_aliases':aliases,
            'native_programs':programs,'native_slots':slots,'pair_checks':checks,
            'method_errors':{m:describe(v) for m,v in errors.items()},'contrasts':contrasts,
            'behavior':{m:population_behavior(c) for m,c in outcomes.items()},
            'population_trajectories':{m:population_curves(c) for m,c in outcomes.items()},
            'recovery':{m:aggregate_recovery(c) for m,c in outcomes.items()},
            'episode_influence':{m:population_episode_effects(outcomes['selected'],outcomes[m]) for m in CONTROLS} if 'selected' in outcomes else {},
            'query_category_totals':{m:dict(sum((Counter(c['evaluation_counts']) for c in cases),Counter())) for m,cases in outcomes.items()},
            'decision_examples': {m:[{'case_index':index,'examples':case['population_stats']['decision_examples']}
                                    for index,case in enumerate(cases)] for m,cases in outcomes.items()},
            'interpretation':spec['development_interpretation' if phase=='development' else 'fresh_interpretation']}
    result['development_finding'] = (
        'Reference stage only; no evolutionary conclusion.' if references_only else
        'Distinct native descendant improves on both development controls; frozen fresh comparison is warranted.' if fresh_trigger and phase == 'development' else
        'A promising fixed-target setting on development data; no additional evolutionary gain demonstrated.'
        if phase == 'development' and best_fixed == 'target_3' and errors['target_3'] != errors['target_5']
        and statistics.mean(errors['target_3']) < statistics.mean(errors['target_5']) else
        'No distinct native candidate improves development mean over both controls.' if phase == 'development' else
        'Fresh descriptive comparison of frozen methods; development selection remains unchanged.')
    output=Path(output) if output else run/'analysis'/phase
    output.mkdir(parents=True,exist_ok=True)
    atomic_json(output/'analysis.json',result)
    render(result,output)
    (output/'tables.md').write_text(markdown_tables(result))
    return result


def markdown_tables(data):
    methods=[m for m in data['method_errors'] if m not in data['execution_aliases']]
    lines=[f"## {data['phase'].capitalize()} paired outcomes",'']
    if data['execution_aliases']:
        lines += [f"Selected execution aliases {data['execution_aliases']['selected']} on the complete saved suite; it is not an additional distinct method.",'']
    lines += ['| Case | '+' | '.join(LABELS[m] for m in methods)+' |', '|---|'+'---:|'*len(methods)]
    for index in range(len(data['configs'])):
        lines.append(f'| {index:03d} | '+' | '.join(f"{data['method_errors'][m]['values'][index]:.6f}" for m in methods)+' |')
    contrasts={k:v for k,v in data['contrasts'].items() if not (v['method']=='selected' and data['execution_aliases'].get('selected')==v['reference'])}
    lines += ['', '| Case | '+' | '.join(k.replace('_',' ') for k in contrasts)+' |', '|---|'+'---:|'*len(contrasts)]
    for index in range(len(data['configs'])):
        lines.append(f'| {index:03d} | '+' | '.join(f"{row['values'][index]:+.6f}" for row in contrasts.values())+' |')
    lines += ['', '| Contrast | Mean | Median | SD | Descriptive 95% interval | W / L / T |', '|---|---:|---:|---:|---|---:|']
    for name,row in contrasts.items():
        low,high=row['descriptive_95_percent_interval']
        lines.append(f"| {name.replace('_',' ')} | {row['mean']:+.6f} | {row['median']:+.6f} | {row['sd']:.6f} | [{low:+.6f}, {high:+.6f}] | {row['wins']} / {row['losses']} / {row['ties']} |")
    return '\n'.join(lines)+'\n'


def render(data,output):
    _style()
    methods=[m for m in data['method_errors'] if m not in data['execution_aliases']]
    population_trajectories = dict(data['population_trajectories'])
    behavior_data, recovery_data = dict(data['behavior']), dict(data['recovery'])
    explanatory_descendant = bool(data['execution_aliases'].get('selected') and data.get('best_descendant'))
    if explanatory_descendant:
        methods.append('best_descendant')
        LABELS['best_descendant'] = f"Best descendant (g{data['best_descendant']['generation']}; seed retained)"
        population_trajectories['best_descendant'] = data['best_descendant_population_trajectories']
        behavior_data['best_descendant'] = data['best_descendant_behavior']
        recovery_data['best_descendant'] = data['best_descendant_recovery']
    fig,axes=plt.subplots(2,2,figsize=(12,8.4),constrained_layout=True)
    for method in methods:
        rows=population_trajectories[method]
        queries=[r['evaluations'] for r in rows]
        axes[0,0].fill_between(queries,[r['neutral_count_min'] for r in rows],[r['neutral_count_max'] for r in rows],color=COLORS[method],alpha=.075,lw=0)
        for ax,field in ((axes[0,0],'mean_neutral_count'),(axes[0,1],'total_particle_count'),(axes[1,0],'offline_error')):
            ax.plot(queries,[r[field] for r in rows],color=COLORS[method],label=LABELS[method],lw=1.65)
    axes[0,0].set(title='Realized neutral population per subswarm',ylabel='Mean neutral particles',ylim=(1.8,8.2))
    axes[0,1].set(title='Total optimizer population',ylabel='Neutral + permanent quantum particles')
    axes[1,0].set(title='Tracking over the full counted horizon',ylabel='Cumulative offline error (log scale)',yscale='log')
    for ax in (axes[0,0],axes[0,1],axes[1,0]):
        ax.set(xlabel='Counted objective evaluations',xlim=(0,500000))
        ax.ticklabel_format(axis='x',style='sci',scilimits=(0,0))
        ax.grid(alpha=.15)
    axes[0,0].legend(frameon=False,fontsize=8)
    contrast_keys=([k for k in data['contrasts'] if k.startswith('selected_')] if 'selected' not in data['execution_aliases'] else [])
    if not contrast_keys:
        contrast_keys=[k for k in data['contrasts'] if not k.startswith('selected_')]
    contrast_rows = ([data['best_descendant_versus_target_5']] if explanatory_descendant else [data['contrasts'][key] for key in contrast_keys])
    for index,row in enumerate(contrast_rows):
        axes[1,1].scatter(row['values'],np.arange(len(data['configs']))+index*.17,s=25,color=COLORS[row['method']],label=f"{LABELS[row['method']]} − {LABELS[row['reference']]}")
        axes[1,1].plot(row['descriptive_95_percent_interval'],[-1-index*.55]*2,color=COLORS[row['method']],lw=2)
        axes[1,1].scatter(row['mean'],-1-index*.55,marker='D',color=COLORS[row['method']],s=40)
    axes[1,1].axvline(0,color='#8796a5',ls='--',lw=1)
    axes[1,1].set(title='Every paired case, mean and descriptive 95% interval',xlabel='Paired offline-error difference (negative favors first)',yticks=range(len(data['configs'])),yticklabels=[f'{i:03d}' for i in range(len(data['configs']))])
    if len(contrast_rows)==1:
        row=contrast_rows[0]
        first=(f"Best descendant g{data['best_descendant']['generation']}" if row['method']=='best_descendant' else LABELS[row['method']])
        axes[1,1].set_title(f"{first} − {LABELS[row['reference']]}\n{len(data['configs'])} paired cases, mean and descriptive 95% interval",fontsize=11)
    else:
        axes[1,1].legend(frameon=False,fontsize=7,loc='best')
    axes[1,1].grid(alpha=.15)
    fig.suptitle(f"MPSO population allocation · {len(data['configs'])} {data['phase']} pairs · 500,000 queries per case",fontsize=14)
    fig.supxlabel('Five dimensions, 200 peaks, severity 1, period 5,000. Shading: average within-case population min/max, not uncertainty.\n'+('Development histories informed selection; intervals are descriptive, not fresh confirmation.' if data['phase']=='development' else 'Frozen rules on fresh histories; exploratory comparison in one chapter condition.'),fontsize=9)
    _save(fig,output/'population_and_tracking')
    fig,axes=plt.subplots(1,3,figsize=(13,4.5),constrained_layout=True)
    x=np.arange(2,9)
    width=.8/len(methods)
    for i,method in enumerate(methods):
        behavior=behavior_data[method]
        shift=(i-(len(methods)-1)/2)*width
        for panel,field in ((0,'equal_case_requested_target_probabilities'),(1,'equal_case_realized_neutral_count_probabilities')):
            axes[panel].bar(x+shift,[100*behavior[field][str(k)] for k in x],width=width,color=COLORS[method],label=LABELS[method])
        curve=recovery_data[method]
        axes[2].plot([r['offset'] for r in curve],[r['mean_error'] for r in curve],color=COLORS[method],lw=1.8,label=LABELS[method])
    axes[0].set(title='Requested population at counted detections',xlabel='Requested target',ylabel='Within-case decisions (%)',xticks=x)
    axes[1].set(title='Realized neutral population',xlabel='Neutral particles',ylabel='Within-case subswarm updates (%)',xticks=x)
    axes[2].set(title='Measured recovery',xlabel='Actual query offset after environmental change',ylabel='Best-discovered error')
    axes[0].legend(frameon=False,fontsize=7)
    for ax in axes:ax.grid(alpha=.15,axis='y')
    fig.suptitle('Requested targets, realized populations and recovery',fontsize=14)
    fig.supxlabel('Equal case weight. Dynamics include births, exclusions and detection; no particle transfers between subswarms.\nRecovery excludes initialization and uses saved actual query offsets without replay.',fontsize=9)
    _save(fig,output/'population_behavior')
    fig, (swarm_ax, query_ax) = plt.subplots(1, 2, figsize=(12, 4.4), constrained_layout=True)
    categories = sorted(set().union(*(behavior_data[method]['equal_case_query_category_shares'] for method in methods)))
    positions = np.arange(len(methods))
    bottoms = np.zeros(len(methods))
    for method in methods:
        trajectory = population_trajectories[method]
        swarm_ax.plot([row['evaluations'] for row in trajectory], [row['swarm_count'] for row in trajectory],
                      label=LABELS[method], color=COLORS[method], lw=1.4)
    swarm_ax.set(title='Subswarm population over counted queries', xlabel='Counted objective evaluations', ylabel='Mean subswarms', xlim=(0, 500000))
    swarm_ax.ticklabel_format(axis='x', style='sci', scilimits=(0, 0))
    swarm_ax.legend(frameon=False, fontsize=7)
    for index, category in enumerate(categories):
        values = np.array([100*behavior_data[method]['equal_case_query_category_shares'].get(category, 0) for method in methods])
        query_ax.bar(positions, values, bottom=bottoms, label=category.replace('_', ' '), color=plt.get_cmap('tab20')(index))
        bottoms += values
    query_ax.set(title='Allocation of the matched objective budget', ylabel='Counted objective queries (%)',
                 xticks=positions, xticklabels=[LABELS[method] for method in methods], ylim=(0, 100))
    query_ax.tick_params(axis='x', labelrotation=18, labelsize=8)
    query_ax.legend(frameon=False, fontsize=7, loc='center left', bbox_to_anchor=(1, .5))
    fig.supxlabel('Equal case weight. Swarm count does not measure distinct-peak coverage; query shares do not identify causal mechanisms.', fontsize=9)
    _save(fig, output/'population_query_allocation')
    episode_sets = ({'best_descendant': data['best_descendant_episode_influence']}
                    if explanatory_descendant else
                    ({'target_5': data['episode_influence']['target_5']} if data['episode_influence'] else {}))
    if episode_sets:
        details = next(iter(episode_sets.values()))
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), constrained_layout=True)
        for ax, key in zip(axes, ('most_favorable', 'most_unfavorable')):
            episode = details[key]
            for method, field, color in (('Best descendant' if explanatory_descendant else 'Selected native rule', 'selected_trace', COLORS['selected']),
                                          (LABELS['target_5'], 'reference_trace', COLORS['target_5'])):
                ax.plot([point['evaluations'] for point in episode[field]], [point['current_error'] for point in episode[field]], label=method, color=color)
            ax.set(title=f"{key.replace('_', ' ').capitalize()}: case {episode['case_index']:03d}, environment {episode['environment']}\nEnvironment mean difference {episode['difference']:+.4f}",
                   xlabel='Counted objective evaluations', ylabel='Current best-discovered error')
            ax.ticklabel_format(axis='x', style='plain', useOffset=False)
            ax.grid(alpha=.15)
        axes[0].legend(frameon=False, fontsize=8)
        fig.supxlabel('Post hoc extremes under the frozen selection rule; initialization excluded. Saved traces only. Episodes are not independent replicates.', fontsize=9)
        _save(fig, output/'tracking_episodes')
    if data['native_programs']:
        fig,(ax,heat_ax)=plt.subplots(1,2,figsize=(12.6,4.8),constrained_layout=True)
        rows=data['native_programs']
        ax.scatter([r['generation'] for r in rows],[r['mean_offline_error'] for r in rows],color=COLORS['selected'],s=55,label='Native program',zorder=3)
        for method in CONTROLS:
            if method in data['method_errors']:ax.axhline(data['method_errors'][method]['mean'],color=COLORS[method],ls='--',label=LABELS[method])
        valid_generations = {row['generation'] for row in rows}
        failed = [row['generation'] for row in data['native_slots'] if row['generation'] not in valid_generations and ('failed' in row['status'] or row['status']=='failure')]
        if failed:
            ax.scatter(failed,[.05]*len(failed),transform=ax.get_xaxis_transform(),marker='x',color='#bb4260',label='Terminal failure: no numerical score')
        ax.set(title='One bounded native population search',xlabel='Generation slot (zero is target 5)',ylabel='Mean development offline error',xticks=range(max(r['generation'] for r in data['native_slots'])+1))
        ax.legend(frameon=False,fontsize=8);ax.grid(alpha=.15)
        matrix=np.array([[row['behavior']['equal_case_requested_target_probabilities'][str(k)] for k in range(2,9)] for row in rows])
        heat=heat_ax.imshow(matrix,vmin=0,vmax=1,cmap='viridis',aspect='auto')
        for y,row in enumerate(matrix):
            for x,value in enumerate(row):
                if value:
                    heat_ax.text(x,y,f'{100*value:.1f}',ha='center',va='center',fontsize=8,color='black' if value>.55 else 'white')
        heat_ax.set(title='Actual requested-target behavior',xlabel='Requested neutral target',ylabel='Native program',xticks=range(7),xticklabels=range(2,9),yticks=range(len(rows)),yticklabels=[f"g{row['generation']}" for row in rows])
        fig.colorbar(heat,ax=heat_ax,label='Equal-case fraction of detected decisions',shrink=.8)
        fig.supxlabel('Every ranked native program uses all four frozen development cases. Heatmap labels show percentages, not fitness rewards.',fontsize=9)
        _save(fig,output/'native_search')
    atomic_json(output/'figure_provenance.json',{'analysis_sha256':sha(output/'analysis.json'),'source_sha256':sha(__file__),'dimension':5,'phase':data['phase'],'objective_calls':0,'model_calls':0,'files':{p.name:sha(p) for p in sorted(output.glob('*.png'))+sorted(output.glob('*.svg'))}})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--phase',choices=('development','fresh'),default='development')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--references-only',action='store_true')
    parser.add_argument('--allow-partial',action='store_true',help='Write an unranked checkpoint inventory if required suites are incomplete.')
    args=parser.parse_args()
    data=analyze(args.run,args.phase,args.output,args.references_only,args.allow_partial)
    print(json.dumps({'phase':data['phase'],'selected':data['selected'],'best_fixed_target':data['best_fixed_target'],'fresh_comparison_required':data['fresh_comparison_required'],'method_errors':data['method_errors']},indent=2),flush=True)


if __name__=='__main__':main()
