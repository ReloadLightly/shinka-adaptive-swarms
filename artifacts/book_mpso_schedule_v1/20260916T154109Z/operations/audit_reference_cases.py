"""Read-only audit of already planned, checkpointed chapter reference cases."""
import hashlib
import json
import math
from pathlib import Path
from datetime import datetime, timezone

from adaptive_swarms.artifacts import read_json
from adaptive_swarms.comparison import validate_pair

ROOT = Path(__file__).resolve().parents[4]
RUN = Path(__file__).resolve().parent.parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(path, permanent):
    r = read_json(path)
    validate_pair(r, r)
    cfg, counts, stats = r['config'], r['evaluation_counts'], r['schedule_stats']
    assert r['permanent_quantum'] == permanent
    assert r['evaluations'] == sum(counts.values()) == 500000
    assert cfg['dimension'] == 5 and cfg['npeaks'] == 10 and cfg['period'] == 5000
    assert cfg['move_severity'] == 1 and cfg['correlation'] == 0 and cfg['nexcess'] == 1
    assert len(r['environment_changes']) == 100
    assert [x['evaluations'] for x in r['environment_changes']] == list(range(5000,500001,5000))
    assert r['partial_environment'] is None
    assert len(r['initial_environment']['positions']) == 10
    assert all(len(x) == 5 for x in r['initial_environment']['positions'])
    assert r['initial_environment']['heights'] == [50.0] * 10
    assert all(1 <= x <= 12 for x in r['initial_environment']['widths'])
    assert stats['count_histogram']['5'] == stats['detected_change_updates']
    assert stats['count_histogram']['0'] + stats['count_histogram']['5'] == stats['updates']
    assert stats['selection_permutations'] == stats['updates']
    assert stats['requested_neutral_conversions'] == 5 * stats['detected_change_updates']
    assert math.isclose(stats['neutral_conversion_fraction'],stats['requested_neutral_conversions']/(5*stats['updates']))
    assert math.isclose(stats['executed_neutral_conversion_fraction'],counts.get('temporary_quantum',0)/(counts.get('temporary_quantum',0)+counts.get('ordinary',0)))
    assert sum(b['updates'] for b in stats['age_bins'].values()) == stats['updates']
    assert sum(b['neutral_conversions'] for b in stats['age_bins'].values()) == stats['requested_neutral_conversions']
    assert stats['completed_updates'] <= stats['updates'] <= stats['completed_updates'] + 1
    assert counts.get('permanent_quantum',0) == permanent*stats['completed_updates']
    for row in r['response_log']:
        assert row['decided_at_evaluation']-row['detected_at_evaluation'] == 5 + permanent
        assert row['observation']['change_detected']
        assert row['observation']['updates_since_detected_change'] == 0
        assert row['decision']['temporary_quantum_count'] == 5
        assert row['selected_neutral_indices'] == list(range(5))
    q_checks, ordinary_checks = 0, 0
    for row in stats['decision_examples']:
        for update in row['particle_updates']:
            before = row['particles_before'][update['index']]
            if update['kind'] != 'ordinary':
                assert math.dist(update['position'], update['center']) <= .5 + 1e-12
                assert update['velocity'] == before['velocity']
                q_checks += 1
            else:
                assert update['position'] == [x+v for x,v in zip(before['position'],update['velocity'])]
                ordinary_checks += 1
            assert (update['kind'] == 'permanent_quantum') == (update['index'] == 5)
    for category in stats['shared_best_improvements'].values():
        assert category['count'] >= 0 and math.isfinite(category['total_gain']) and category['total_gain'] >= 0
    if permanent:
        assert stats['shared_best_improvements']['permanent_quantum']['count'] > 0
    else:
        assert stats['shared_best_improvements']['permanent_quantum'] == {'count':0,'total_gain':0.0}
    assert r['final_swarm_count'] == 1 + stats['births'] - stats['removals']
    return r, {'artifact':str(path.relative_to(RUN)),'artifact_sha256':digest(path),'offline_error':r['offline_error'],
        'objective_queries':r['evaluations'],'query_partition':counts,'environment_boundaries':100,
        'permanent_quantum':permanent,'updates':stats['updates'],'completed_updates':stats['completed_updates'],
        'detected_change_updates':stats['detected_change_updates'],'count_histogram':stats['count_histogram'],
        'requested_conversion_fraction':stats['neutral_conversion_fraction'],
        'executed_conversion_fraction':stats['executed_neutral_conversion_fraction'],
        'permanent_quantum_shared_best_improvements':stats['shared_best_improvements']['permanent_quantum'],
        'observed_quantum_moves_within_radius_and_velocity_retained':q_checks,
        'observed_ordinary_moves_equal_previous_position_plus_new_velocity':ordinary_checks,
        'decision_examples':[{'criteria':x['example_criteria'],'evaluations':x['decided_at_evaluation'],
                              'count':x['decision']['temporary_quantum_count']} for x in stats['decision_examples']],
        'all_assertions_passed':True}


record = {'audit_at':datetime.now(timezone.utc).isoformat(),'new_objective_queries':0,'new_model_calls':0,
          'source_record_sha256':digest(ROOT/'docs/book_mpso_source_record.md'),
          'engine_sha256':digest(ROOT/'src/adaptive_swarms/book_mpso.py'),
          'source_conventions_review':'Actual chapter Algorithm3 and frozen source record agree: asynchronous neutral-first/permanent-last movement; quantum replaces PSO with retained neutral velocities; all-role counted memory refresh; per-subswarm exclusion; immediate counted newborn initialization; designated-neutral pairwise diameter approximation; counted exact horizon. Source-specific conventions are explicitly distinguished from exact historical reproduction.',
          'interpretive_limit':'Shared-best improvement gains aggregate gains across swarms and do not identify causal contribution to offline error. Requested conversions include any final partial update; executed fraction is separately recorded.',
          'methods':{},'status':'awaiting_first_5_plus_1_case'}
rows={}
for permanent,name in ((0,'mpso_5_0'),(1,'mpso_5_1')):
    path=RUN/'references'/name/'case_000.json.gz'
    if path.exists(): rows[name],record['methods'][name]=audit(path,permanent)
if len(rows)==2:
    record['pairing']=validate_pair(rows['mpso_5_0'],rows['mpso_5_1'])
    record['status']='passed'
(RUN/'operations/reference-audit.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
