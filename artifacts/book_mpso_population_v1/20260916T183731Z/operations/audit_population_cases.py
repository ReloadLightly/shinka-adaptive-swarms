"""Read-only independent accounting/role/pairing audit of saved population cases."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from adaptive_swarms.artifacts import read_json
from adaptive_swarms.book_population import from_compatible_fixed_five_result
from adaptive_swarms.logging import atomic_json

RUN = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inspect_case(result, target=None):
    assert result['evaluations'] == result['config']['budget'] == 500000
    assert sum(result['evaluation_counts'].values()) == 500000
    assert result['permanent_quantum'] == 1
    assert math.isfinite(result['offline_error'])
    assert len(result['environment_changes']) == 100
    integrated = sum(row['environment_offline_error'] * row['environment_evaluations'] for row in result['environment_changes']) / 500000
    assert math.isclose(integrated, result['offline_error'], abs_tol=1e-10)
    known_categories = {'initialization', 'birth', 'exclusion', 'detection', 'memory', 'ordinary', 'temporary_quantum', 'permanent_quantum'}
    assert set(result['evaluation_counts']) <= known_categories
    stats = result['population_stats']
    schedule = result['schedule_stats']
    assert stats['policy_calls'] == stats['population_decisions'] == len(result['response_log']) == schedule['detected_change_updates']
    requested, additions, removals, previous = Counter(), 0, 0, {}
    for row in result['response_log']:
        obs = row['observation']
        before, after, request = row['neutral_count_before'], row['neutral_count_after'], row['requested_target']
        assert type(request) is int and 2 <= request <= 8
        if target is not None: assert request == target
        assert obs['change_detected'] is True
        assert row['decided_at_evaluation'] - row['detected_at_evaluation'] == before + 1
        assert obs['neutral_count'] == before and obs['swarm_size'] == before + 1
        assert obs['evaluations_since_detected_change'] == before + 1
        assert obs['updates_since_detected_change'] == 0
        assert 2 <= before <= 8 and 2 <= after <= 8
        assert after == before + (1 if request > before else -1 if request < before else 0)
        if row['swarm_id'] not in previous:
            assert before == 5 and obs['previous_requested_target'] == 5
        else:
            last_count, last_request = previous[row['swarm_id']]
            assert before == last_count and obs['previous_requested_target'] == last_request
        previous[row['swarm_id']] = (after, request)
        assert row['decision']['temporary_quantum_count'] == after
        assert row['selected_neutral_indices'] == list(range(after))
        assert row['total_particle_count'] == row['total_neutral_count'] + obs['swarm_count']
        if after > before:
            assert row['decision']['added_neutral_index'] == before
            additions += 1
        elif after < before:
            assert 0 <= row['decision']['removed_neutral_index'] < before
            assert math.isfinite(row['decision']['removed_best_fitness'])
            removals += 1
        requested[str(request)] += 1
    assert additions == stats['additions'] and removals == stats['removals']
    assert {k:v for k,v in stats['requested_target_histogram'].items() if v} == dict(requested)
    assert sum(stats['realized_neutral_count_histogram'].values()) == stats['total_neutral_updates'] == schedule['updates']
    assert sum(int(k)*v for k,v in stats['realized_neutral_count_histogram'].items()) == stats['neutral_count_sum']
    for point in result['trace']:
        swarms = point['swarm_count']
        assert point['total_particle_count'] == point['total_neutral_count'] + swarms
        assert 2 <= point['neutral_count_min'] <= point['neutral_count_max'] <= 8
        assert point['neutral_count_min']*swarms <= point['total_neutral_count'] <= point['neutral_count_max']*swarms
    example_updates = 0
    for example in stats['decision_examples']:
        before_particles = example['particles_before']
        assert len(before_particles) == example['neutral_count_after'] + 1
        for update in example['particle_updates']:
            permanent = update['index'] == example['neutral_count_after']
            assert (update['kind'] == 'permanent_quantum') == permanent
            quantum = permanent or example['observation']['change_detected']
            assert (update['kind'] != 'ordinary') == quantum
            if quantum:
                assert math.dist(update['position'], update['center']) <= .5 + 1e-10
                assert update['velocity'] == before_particles[update['index']]['velocity']
            example_updates += 1
    return {'offline_error': result['offline_error'], 'queries': 500000,
            'decisions': len(result['response_log']), 'additions': additions, 'removals': removals,
            'recorded_particle_updates_checked': example_updates,
            'landscape_hashes': [result['initial_environment']['sha256']] + [r['next_environment']['sha256'] for r in result['environment_changes']],
            'query_categories': result['evaluation_counts'], 'requested_target_counts': dict(requested)}


def main():
    cases = read_json(RUN / 'development_cases.json')['cases']
    ledger = read_json(RUN / 'references/execution_ledger.json')
    completed = {}
    for target in (3,5,7):
        completed[str(target)] = []
        for i, config in enumerate(cases):
            path = RUN / f'references/target_{target}/case_{i:03d}.json.gz'
            if not path.exists(): continue
            result = read_json(path)
            assert result['config'] == config and result['case_id'] == f'case_{i:03d}'
            entry = inspect_case(result, target)
            matching = [a for a in ledger['attempts'] if a['method'] == f'target_{target}' and a['case_index'] == i]
            assert len(matching) == 1 and matching[0]['status'] in ('completed','reused')
            assert matching[0]['artifact_sha256'] == sha(path)
            if target == 5:
                old = ROOT / f'artifacts/book_mpso_schedule_v1/20260916T154109Z/references/mpso_5_1/case_{i:03d}.json.gz'
                expected = from_compatible_fixed_five_result(read_json(old))
                actual = dict(result); actual.pop('reuse_provenance')
                assert actual == expected
                assert result['reuse_provenance']['new_objective_queries'] == 0
                assert result['population_stats']['diagnostic_origin'] == 'derived_exactly_from_certified_fixed_five_archive'
                assert matching[0]['actual_queries'] == 0
            entry.update(case_index=i, artifact=str(path.relative_to(RUN)), sha256=sha(path))
            completed[str(target)].append(entry)
    paired = 0
    for i in range(8):
        rows = [next((r for r in completed[str(target)] if r['case_index'] == i), None) for target in (3,5,7)]
        if all(rows):
            assert rows[0]['landscape_hashes'] == rows[1]['landscape_hashes'] == rows[2]['landscape_hashes']
            paired += 1
    done = sum(map(len, completed.values())) == 24
    record = {'status':'passed' if done else 'partial_saved_cases_passed',
        'recorded_at':datetime.now(timezone.utc).isoformat(), 'complete_case_records':sum(map(len,completed.values())),
        'fully_paired_cases':paired, 'physical_new_executions':sum(a['status']=='completed' for a in ledger['attempts']),
        'new_queries':sum(a.get('actual_queries',0) for a in ledger['attempts']), 'cases':completed,
        'checks':['Exact 500000 category accounting and offline-error integral','101 paired landscape states including final boundary',
            'All existing memories refreshed before every policy call','Five-neutral start for each observed swarm identity',
            'One-step changes, correct neutral bounds, permanent role last','Published quantum response for every current neutral on change',
            'No extra population initialization evaluation category','Recorded quantum move replaces PSO and retains velocity',
            'Archived target-five outcomes exact after documented diagnostic enrichment'],
        'scope_note':'Saved evidence plus prospective small fixtures establish adapter mechanics. Exhaustive before/after survivor memories are not logged for every event; no replay was performed.',
        'objective_or_model_queries_in_this_audit':0}
    atomic_json(RUN / ('operations/reference-audit.json' if done else 'operations/reference-audit-partial.json'), record)
    print(json.dumps({k:v for k,v in record.items() if k not in ('cases','checks')}, indent=2))


if __name__ == '__main__': main()
