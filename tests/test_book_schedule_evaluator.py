"""Checkpoint/failure risks checked with synthetic saved records, no objective calls."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from adaptive_swarms.artifacts import read_json, write_compressed_json
from adaptive_swarms.book_schedule import schedule_fingerprint, BookScheduleError
from adaptive_swarms.simulator import _validated_config

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def setup(tmp_path):
    spec = importlib.util.spec_from_file_location('book_schedule_evaluator', ROOT/'tasks/book_mpso_schedule_v1/evaluate.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    program = tmp_path/'main.py'
    program.write_bytes((ROOT/'tasks/book_mpso_schedule_v1/initial.py').read_bytes())
    config = _validated_config({'budget':1000, 'period':100, 'environment_seed':813, 'optimizer_seed':814})
    result = {'case_id':'case_000', 'config':config, 'evaluations':1000, 'evaluation_counts':{'particle':1000},
              'permanent_quantum':1, 'schedule_stats':{}, 'offline_error':2.0, 'initial_environment':{'sha256':'synthetic'}, 'environment_changes':[], 'response_log':[]}
    artifact = write_compressed_json(tmp_path/'reference_1.json.gz',result)
    zero_artifact = write_compressed_json(tmp_path/'reference_0.json.gz',{**result,'permanent_quantum':0})
    def reference(path):
        return {'method':'synthetic check only', 'case_artifacts':[str(path.resolve())],
           'case_sha256':[hashlib.sha256(path.read_bytes()).hexdigest()],
           'source_sha256':hashlib.sha256(program.read_bytes()).hexdigest(),
           'scientific_sources':schedule_fingerprint()}
    suite=tmp_path/'suite.json';suite.write_text(json.dumps({'cases':[config], 'feedback_references':{
        'mpso_5_0':reference(zero_artifact),'mpso_5_1':reference(artifact)}}))
    return module,program,suite,tmp_path/'evaluated',artifact


def test_exact_seed_checkpoint_reuse_without_objective_calls(setup,monkeypatch):
    module,program,suite,folder,artifact=setup
    def forbidden(*args,**kwargs): raise AssertionError('no numerical calls on exact reuse')
    monkeypatch.setattr(module,'run_case',forbidden)
    assert module.evaluate(program,folder,suite)==0
    digest=hashlib.sha256((folder/'case_000.json.gz').read_bytes()).hexdigest()
    assert module.evaluate(program,folder,suite)==0
    assert hashlib.sha256((folder/'case_000.json.gz').read_bytes()).hexdigest()==digest
    assert read_json(folder/'metrics.json')['private']['cases'][0]['paired_differences']=={'mpso_5_0':0.,'mpso_5_1':0.}
    assert not (folder/'execution-attempts.json').exists()


def test_terminal_invalid_score_preserves_exact_partial_work(setup,monkeypatch):
    module,program,suite,folder,_=setup
    program.write_text(program.read_text()+'\n# different source\n')
    calls=[]
    def invalid(*args,**kwargs):
        calls.append(1)
        exc=BookScheduleError('synthetic invalid score; no actual objective calls in fixture')
        exc.objective_queries=17
        raise exc
    monkeypatch.setattr(module,'run_case',invalid)
    assert module.evaluate(program,folder,suite)==1
    assert module.evaluate(program,folder,suite)==1
    assert len(calls)==1
    row=read_json(folder/'execution-attempts.json')[0]
    assert row['status']=='failed' and row['exact_objective_queries']==17 and row['reserved_objective_queries']==1000
    assert read_json(folder/'correct.json')['correct'] is False


def test_changed_reference_cannot_be_reused(setup):
    module,program,suite,folder,artifact=setup
    artifact.write_bytes(artifact.read_bytes()+b' ')
    with pytest.raises(ValueError,match='reference hash differs'):
        module.evaluate(program,folder,suite)
    assert not (folder/'correct.json').exists()


def test_wrong_reference_mode_not_aliased_to_seed(setup):
    module,program,suite,folder,artifact=setup
    stored=read_json(suite)
    stored['feedback_references']['mpso_5_0']=stored['feedback_references']['mpso_5_1']
    suite.write_text(json.dumps(stored))
    with pytest.raises(ValueError,match='permanent quantum mode differs'):
        module.evaluate(program,folder,suite)
    assert not folder.joinpath('case_000.json.gz').exists()


def test_local_math_program_executes_and_pairs_feedback(setup,monkeypatch):
    module,program,suite,folder,artifact=setup
    program.write_text('def choose_temporary_quantum_count(obs):\n import math\n return int(math.sqrt(16))\n')
    observed=[]
    def numerical(config,schedule,progress,permanent_quantum):
        observed.append((schedule({'change_detected':False}),permanent_quantum))
        result=read_json(artifact)
        return {key:value for key,value in result.items() if key!='case_id'}
    monkeypatch.setattr(module,'run_case',numerical)
    assert module.evaluate(program,folder,suite)==0
    assert observed==[(4,1)]
    feedback=read_json(folder/'metrics.json')['text_feedback']
    assert 'delta5+0=+0.000000' in feedback and 'delta5+1=+0.000000' in feedback
