"""Saved-artifact analysis tests; no numerical simulator or model requests."""
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

spec=importlib.util.spec_from_file_location('retention_analysis',Path(__file__).resolve().parents[1]/'scripts/analyze_particle_retention.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)


def response(query=100, selected=2, completed=True):
    features=[{'personal_best_rank':i+1,'speed_normalized':i*.5,'distance_to_best_normalized':i*.2,'velocity_alignment':i*.1} for i in range(5)]
    return {'completed':completed,'swarm_id':1,'relocated_indices':[i for i in range(5) if i!=selected],
            'decision':{'radius_scale':1.25,'reset_velocity':False,'memory':'reevaluate'},
            'retention':{'features':features,'selected_index':selected,'heuristic_index':0,
               'agrees_with_heuristic':selected==0,'tie_order':[0,2,1,4,3],
               'scores':[10. if i==selected else 0. for i in range(5)], 'decided_at_evaluation':query,
               'selected_update_reached':completed,'selected_objective_queried':completed}}


def test_retention_audit_checks_same_snapshot_heuristic_and_complement():
    c={'response_log':[response()]};assert a.summarize_case_behavior(c)['chosen_features']['personal_best_rank']['mean']==3
    c['response_log'][0]['retention']['heuristic_index']=1
    with pytest.raises(ValueError,match='snapshot'):a.retention_rows(c)
    c={'response_log':[response()]};c['response_log'][0]['relocated_indices']=[0,1,2,3]
    with pytest.raises(ValueError,match='exemption'):a.retention_rows(c)


def test_no_decision_partial_memory_refresh_is_not_a_completed_choice():
    case={'response_log':[{'completed':False,'relocated_indices':[]}]}
    assert a.summarize_case_behavior(case)['no_decision']
    case['response_log'][0]['completed']=True
    with pytest.raises(ValueError,match='no saved decision'):a.retention_rows(case)


def test_decision_recovery_never_crosses_environment_boundary_or_interpolates():
    case={'config':{'period':2500,'budget':100000},'trace':[{'evaluations':2500,'current_error':9.},
          {'evaluations':2525,'current_error':8.},{'evaluations':2625,'current_error':7.},
          {'evaluations':3000,'current_error':6.}]}
    result=a.decision_recovery(case,2480)
    assert all(row['actual_query_offset'] is None for row in result['recorded_samples'])
    result=a.decision_recovery(case,2500)
    assert [row['actual_query_offset'] for row in result['recorded_samples']]==[25,125,500]
    assert [row['current_error'] for row in result['recorded_samples']]==[8.,7.,6.]


def test_examples_follow_prospective_query_rule_and_completed_responses():
    case={'config':{'period':2500,'budget':100000,'environment_seed':1,'optimizer_seed':2},'trace':[],
          'response_log':[response(80,completed=False),response(100),response(49999),response(50000),response(50001)]}
    examples=a.decision_examples(case,7)
    assert [row['retention']['decided_at_evaluation'] for row in examples]==[100,50000]
    assert all(row['case_index']==7 for row in examples)


def test_behavior_equal_case_weight_not_pooling_and_bootstrap_no_case_deletion():
    summary=a.summarize_behavior([{'response_log':[response(selected=0)]*50},{'response_log':[response(selected=4)]}])
    assert summary['equal_case_rank_probabilities']==[.5,0.,0.,0.,.5]
    assert summary['equal_case_heuristic_agreement']==.5
    configs=[{'move_severity':s,'period':p} for s in (1,3) for p in (2500,5000) for _ in range(2)]
    values=[-.1]*7+[8.]
    stats=a.paired_effect(values,configs)
    assert stats['values']==values and stats['largest_absolute_contribution']['case_index']==7
    assert stats['largest_absolute_contribution']['contribution_to_eight_case_mean']==1.
    assert stats['improved_cases']==7 and stats['worsened_cases']==1
    assert a.ANALYSIS_SETTINGS['bootstrap_seed']==2026091607
    # Pooled episode ties follow the registered chronological rule, not case order.
    def episode(environment, error):
        return {'config': {'period': 2500}, 'response_log': [], 'trace': [],
                'environment_changes': [{'completed_environment': environment,
                    'environment_offline_error': error, 'environment_initial_error': error,
                    'environment_final_error': error, 'first_evaluation': environment*2500+1,
                    'evaluations': (environment+1)*2500}]}
    extremes=a.extreme_episodes([episode(2,3.),episode(1,3.)], [episode(2,1.),episode(1,1.)])
    assert extremes['most_unfavorable']['case_index']==1
    assert extremes['most_favorable']['environment']==1
