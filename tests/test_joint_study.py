"""Concrete V3 selection, terminal-slot, alias, intervention and analysis risks."""
from collections import Counter
import copy
import json
from pathlib import Path
import random
import sqlite3

import numpy as np
import pytest

from adaptive_swarms import joint_study as study
from adaptive_swarms.logging import atomic_json
from adaptive_swarms.simulator import _validated_config

BASELINE = 'def choose_relocation(observation: dict) -> dict:\n    return {"count": observation["swarm_size"], "radius_scale": 1.0}\n'
ZERO = 'def choose_relocation(observation):\n    return {"count": 0, "radius_scale": 4.0}\n'
ADAPTIVE = 'def choose_relocation(observation):\n    return {"count": 3 if observation["fitness_drop"] > 0 else 2, "radius_scale": 2.0}\n'


def registered(tmp_path):
    paths = {i: tmp_path / f"search_{i}" for i in range(3)}
    engine = tmp_path / "engine.json"
    atomic_json(engine, {"engine_config": {"profile_name": "synthetic_test_only"}})
    folder = tmp_path / "study"
    record = study.register_study(folder, paths, engine)
    return folder, record, paths, engine


def native_fixture(folder, registration, paths):
    for index, path in paths.items():
        path.mkdir()
        atomic_json(path / "search-suite.json", {"cases": registration["search_cases"]})
        (path / "task_snapshot").mkdir()
        for name in registration["task_sources"]:
            (path / "task_snapshot" / name).write_bytes((folder / "runner_snapshot" / ("task__" + name)).read_bytes())
        atomic_json(path / "manifest.json", {"task": "joint_relocation_v3", "evaluation_version": "joint_relocation_v3_score_reciprocal",
                    "status": "search_complete", "generation_target": 30, "search_seed": registration["searches"][index]["search_seed"],
                    "engine_config": registration["engine_config"], "source_hashes": registration["task_sources"]})
        connection = sqlite3.connect(path / "programs.sqlite")
        connection.execute("CREATE TABLE programs (id TEXT, code TEXT, parent_id TEXT, generation INTEGER, combined_score REAL, correct INTEGER, metadata TEXT, public_metrics TEXT, text_feedback TEXT)")
        for generation, code, error, correct in [(0, BASELINE, 3.0, 1), (1, ZERO, 2.0, 1), (2, ADAPTIVE, 2.0, 1), (3, BASELINE, 1.0, 0)]:
            connection.execute("INSERT INTO programs VALUES (?,?,NULL,?,?,?,?,?,NULL)",
                (f'{index}-{generation}', code, generation, 1/(1+error), correct, '{}', json.dumps({'mean_offline_error':error})))
        # Native copy metadata is not an extra evaluated slot or source.
        connection.execute("INSERT INTO programs VALUES (?,?,NULL,?,?,?,?,?,NULL)",
                           (f'{index}-copy', BASELINE, 0, .25, 1, '{"_is_island_copy":true}', '{"mean_offline_error":3.0}'))
        connection.commit()
        connection.close()
        for generation in range(4, 30):
            atomic_json(path / f"gen_{generation}/failure.json", {"generation": generation,
                        "node_kind": "failed_proposal", "downstream_eval_submitted": False})


def reviewed(tmp_path):
    folder, registration, paths, engine = registered(tmp_path)
    native_fixture(folder, registration, paths)
    shortlist = study.freeze_shortlists(folder)
    review = tmp_path / "review.json"
    atomic_json(review, {"reviewer": "synthetic test fixture", "notes": "Literal and public-observation functions only.",
                        "approved_source_sha256": [p["sha256"] for p in shortlist["programs"].values()]})
    study.record_source_review(folder, review)
    return folder, registration, shortlist, paths


def small_cases(n=2):
    return [_validated_config({"budget": 101, "period": 20, "environment_seed": 8700+i,
                               "optimizer_seed": 8800+i}) for i in range(n)]


def test_registration_is_durable_and_precedes_all_searches(tmp_path):
    folder, record, paths, engine = registered(tmp_path)
    assert [item['search_seed'] for item in record['searches']] == [610001, 610002, 610003]
    assert not any(path.exists() for path in paths.values())
    assert study.register_study(folder, paths, engine) == record
    changed = {**paths, 2: tmp_path / 'replacement'}
    with pytest.raises(ValueError, match='identities or prospective settings changed'):
        study.register_study(folder, changed, engine)
    paths[0].mkdir()
    atomic_json(paths[0] / 'gen_1/failure.json', {'generation':1})
    with pytest.raises(ValueError, match='before research outcomes'):
        study.register_study(tmp_path / 'late-study', paths, engine)


def test_completed_guard_counts_terminal_failures_not_30_successes(tmp_path):
    folder, registration, paths, _ = registered(tmp_path)
    native_fixture(folder, registration, paths)
    record = study.native_search_record(registration['searches'][0], registration)
    assert record['evaluated_generation_ids'] == [0, 1, 2, 3]
    assert record['terminal_failed_generation_ids'] == list(range(4,30))
    assert record['terminal_generation_ids'] == list(range(30))
    assert [row['generation'] for row in record['shortlist_rows']] == [1, 2, 0]
    (paths[0] / 'gen_29/failure.json').unlink()
    with pytest.raises(ValueError, match='Thirty terminal native slots'):
        study.native_search_record(registration['searches'][0], registration)


def test_cross_search_shortlists_deduplicate_exact_sources_not_scores(tmp_path):
    folder, _, shortlist, _ = reviewed(tmp_path)
    assert len(shortlist['programs']) == 3
    assert len(shortlist['cross_search_aliases']) == 3
    assert all(len(p['occurrences']) == 3 for p in shortlist['programs'].values())
    assert all(len(search['shortlist']) == 3 for search in shortlist['searches'])
    program = next(iter(shortlist['programs'].values()))
    (folder / program['policy']).write_text('raise RuntimeError()\n')
    with pytest.raises(ValueError, match='Frozen candidate source'):
        study.verify_review(folder)


def test_grid_has_24_labels_and_21_safe_execution_classes():
    config = small_cases(1)[0]
    grid = study.fixed_grid()
    assert len(grid)==24
    identities = {study.digest(study.method_identity(method, config)) for method in grid.values()}
    assert len(identities)==21
    assert study.proven_constant(BASELINE)=={'count':'swarm_size','radius_scale':1.0}
    dynamic={'kind':'program','sha256':'dynamic','proven_constant':None}
    assert study.method_identity(dynamic,config)['kind']=='joint_program'
    assert study.proven_constant('def choose_relocation(o):\n return {"count": 0 if o["previous_response_radius"] > 1 else 1, "radius_scale": 4.0}') is None
    assert study.proven_constant('def choose_relocation(o: exec("pass")):\n return {"count": 0, "radius_scale": 4.0}') is None


def test_joint_sampler_weights_cases_and_preserves_full_pairs():
    config=small_cases(1)[0]
    cases=[{'config':config,'response_log':[{'requested_count':1,'requested_radius_scale':.5}]*99},
           {'config':config,'response_log':[{'requested_count':5,'requested_radius_scale':4.0}]},
           {'config':config,'response_log':[]}]
    frozen=study.freeze_joint_sampler(cases)
    regime_cases=frozen['regime_cases'][study.regime_key(config)]
    assert regime_cases[2]['no_response_baseline_fallback']
    assert regime_cases[2]['action_pairs']==[[5,1.0]]
    first=study.joint_sampler_policy(regime_cases,11)
    second=study.joint_sampler_policy(regime_cases,11)
    chosen=[first({'any_state':i}) for i in range(6000)]
    counts=Counter((a['count'],a['radius_scale']) for a in chosen)
    assert set(counts)=={(1,.5),(5,4.0),(5,1.0)}
    assert all(1700 < count < 2300 for count in counts.values())
    random.seed(987)
    for _ in range(200): random.random()
    assert chosen==[second({'different_state':0}) for _ in range(6000)]
    assert study.nominal_action_pairs(cases[2])==[]


def test_component_substitutions_call_original_on_reached_state_and_validate():
    seen=[]
    def function(observation):
        seen.append(observation['previous_response_radius'])
        return {'count':len(seen), 'radius_scale':observation['previous_response_radius']*2}
    policy=study.ComponentPolicy(function,'radius_scale',.5)
    assert policy({'swarm_size':5,'previous_response_radius':1})=={'count':1,'radius_scale':.5}
    assert policy({'swarm_size':5,'previous_response_radius':4})=={'count':2,'radius_scale':.5}
    assert seen==[1,4] and [a['radius_scale'] for a in policy.original_decisions]==[2,8]
    invalid=study.ComponentPolicy(lambda observation:{'count':3,'radius_scale':float('nan')},'radius_scale',1)
    with pytest.raises(ValueError,match='finite'):
        invalid({'swarm_size':5})


def test_checkpoint_resume_keeps_measurements_and_projects_nominal_zero_radius(tmp_path,monkeypatch):
    folder, _, shortlist, _=reviewed(tmp_path)
    zero=next(p for p in shortlist['programs'].values() if p['proven_constant']=={'count':0,'radius_scale':4.0})
    methods={'fixed_zero_half':{'kind':'fixed','count':0,'radius_scale':.5},
             'evolved_zero_four':{'kind':'program',**zero},'fixed_one':{'kind':'fixed','count':1,'radius_scale':1.0}}
    cases=small_cases()
    original=study.run_case
    calls=[]
    def interrupt(config,policy=None,progress=None):
        calls.append(config['environment_seed'])
        if len(calls)==2: raise RuntimeError('interrupted protected stage')
        return original(config,policy,progress)
    monkeypatch.setattr(study,'run_case',interrupt)
    with pytest.raises(RuntimeError,match='interrupted protected'):
        study.run_stage(folder,'validation',cases,methods,study.file_sha(folder/'shortlists.json'))
    saved=list((folder/'validation/cache').glob('*.json.gz'))
    assert len(saved)==1
    before=saved[0].read_bytes()
    calls.clear()
    def tracked(config,policy=None,progress=None):
        calls.append(config['environment_seed'])
        return original(config,policy,progress)
    monkeypatch.setattr(study,'run_case',tracked)
    summary=study.run_stage(folder,'validation',cases,methods,study.file_sha(folder/'shortlists.json'))
    assert calls==[8700,8701,8701]
    assert summary['unique_executed_method_cases']==4 and len(summary['aliases'])==2
    assert saved[0].read_bytes()==before
    manifest,outcomes=study.load_stage_outcomes(folder,'validation')
    representative=outcomes['fixed_zero_half'][0]
    evolved=outcomes['evolved_zero_four'][0]
    assert representative['response_log']==evolved['response_log']
    assert all(r['requested_radius_scale']==.5 for r in evolved['response_log'])
    assert study.nominal_action_pairs(evolved)==[[0,4.0]]*len(evolved['response_log'])
    assert study.nominal_action_pairs(representative)==[[0,.5]]*len(representative['response_log'])
    assert evolved['nominal_action_projection']['executed_method']=='fixed_zero_half'
    sampler=study.freeze_joint_sampler(outcomes['evolved_zero_four'])
    assert all(pair==[0,4.0] for row in sampler['regime_cases'][study.regime_key(cases[0])] for pair in row['action_pairs'])
    assert saved[0].read_bytes()==before
    calls.clear()
    study.run_stage(folder,'validation',cases,methods,study.file_sha(folder/'shortlists.json'))
    assert not calls


def test_primary_interval_and_interaction_use_paired_fixed_regime_weights():
    deltas=[0,1,2,4,10,11,15,18]
    regimes=['a']*4+['b']*4
    primary=study.paired_statistics(deltas,regimes,.975)
    secondary=study.paired_statistics(deltas,regimes,.95)
    assert primary['mean_delta']==secondary['mean_delta']==statistics_mean(deltas)
    assert primary['bootstrap_interval'][0]<=secondary['bootstrap_interval'][0]
    assert primary['bootstrap_interval'][1]>=secondary['bootstrap_interval'][1]
    rng=np.random.default_rng(2026091603)
    samples=np.zeros(20000)
    for values in [np.array(deltas[:4]),np.array(deltas[4:])]:
        indices=rng.integers(0,4,size=(20000,4))
        samples+=values[indices].mean(axis=1)/2
    assert primary['bootstrap_interval']==np.quantile(samples,[.0125,.9875]).tolist()
    fixed=study.paired_statistics([-3,-3,5,5,5],['a','a','b','b','b'])
    assert fixed['mean_delta']==1 and fixed['stratified_se_delta']==0


def statistics_mean(values):
    import statistics
    return statistics.mean(values)


def test_full_selection_freezes_all_winners_grid_sampler_and_analysis_before_seeds(tmp_path,monkeypatch):
    folder,registration,shortlist,_=reviewed(tmp_path)
    methods=study.fixed_grid()
    methods.update({name:{'kind':'program',**p} for name,p in shortlist['programs'].items()})
    # Tiny mechanistic fixture, never a 100000-query research case.
    cases=small_cases()
    original=study.run_case
    def tied(config,policy=None,progress=None):
        result=original(config,policy,progress)
        result['offline_error']=1.0
        return result
    monkeypatch.setattr(study,'run_case',tied)
    study.run_stage(folder,'validation',cases,methods,study.file_sha(folder/'shortlists.json'))
    frozen=study.select_and_freeze(folder)
    assert len(frozen['methods'])==8
    assert [p['generation'] for p in frozen['per_search_winners']]==[0,0,0]
    assert frozen['overall_winner_method']=='winner_search_0'
    assert frozen['selected_fixed_pair']=={'kind':'fixed','count':0,'radius_scale':.5}
    assert frozen['analysis']['primary_interval_level']==.975
    assert not (folder/'final_cases.json').exists()
    selection_bytes=(folder/'selection.json').read_bytes()
    study.run_stage(folder,'validation',cases,methods,study.file_sha(folder/'shortlists.json'))
    assert study.select_and_freeze(folder)==frozen
    assert (folder/'selection.json').read_bytes()==selection_bytes
    monkeypatch.setattr(study,'run_case',original)
    # Exercise final analysis using the same tiny internal runner fixture, not
    # the public 80-case research stage. Real measured errors vary by policy.
    final_summary=study.run_stage(folder,'final',cases,frozen['methods'],study.file_sha(folder/'selection.json'))
    assert final_summary['unique_executed_method_cases'] < 8*len(cases)
    analyzed=study.analyze(folder)
    primary=[value for value in analyzed['comparisons'].values() if value['role']=='primary']
    assert len(primary)==2 and all(value['interval_level']==.975 for value in primary)
    assert len(analyzed['comparisons'])==9
    assert not analyzed['claim']['superiority_over_both_primary_controls_supported']
    _,outcomes=study.load_stage_outcomes(folder,'final')
    for index,row in enumerate(analyzed['interaction']['cases']):
        expected=(outcomes['winner_search_0'][index]['offline_error']
                  - outcomes['radius_replaced'][index]['offline_error']
                  - outcomes['count_replaced'][index]['offline_error']
                  + outcomes['best_fixed'][index]['offline_error'])
        assert row['delta']==expected
    assert analyzed['interaction']['interval_level']==.95
    historical=tmp_path/'historical.json'
    master=9
    first=random.Random(master).randrange(1,2**31)
    atomic_json(historical,{'optimizer_seed':first,'environment_seed':8,'search_seed':27,'analysis_seed':52})
    monkeypatch.setattr(study.secrets,'randbits',lambda _:master)
    final=study.generate_final_cases(folder,[historical])
    seeds=[case[key] for case in final['cases'] for key in ('environment_seed','optimizer_seed')]
    assert len(seeds)==len(set(seeds))==160
    assert not set(seeds)&{first,8,27,52,610001,610002,610003}
    assert final['selection_frozen_at']<final['generated_at']
    assert study.generate_final_cases(folder,[])==final


def test_empirical_action_summary_omits_empty_cases_instead_of_imputing_actions():
    config=small_cases(1)[0]
    def case(responses):
        return {'config':config,'response_log':responses,'evaluations':101,'evaluation_counts':{'particle':101},
                'offline_error':1.0,'environment_changes':[]}
    response={'requested_count':2,'requested_radius_scale':4.0,'decision':{'radius_scale':4.0,'memory':'reevaluate','reset_velocity':False},
              'observation':{'swarm_size':5},'relocated_indices':[0,1],'completed':True}
    summary=study.joint_behavior([case([response]),case([])])
    group=summary['regimes'][study.regime_key(config)]
    assert group['joint_actions']==[{'count':2,'radius_scale':4.0,'responses':1,'equal_case_probability':1.0}]
    assert group['no_response_cases_within_regime']==[1]
