"""Checkpoint/failure risks checked with synthetic saved records, no objective calls."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from adaptive_swarms.artifacts import read_json, write_compressed_json
from adaptive_swarms.particle_retention import retention_fingerprint, RetentionPolicyError
from adaptive_swarms.simulator import _validated_config

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def setup(tmp_path):
    spec = importlib.util.spec_from_file_location('retention_evaluator', ROOT/'tasks/particle_retention_v1/evaluate.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    program = tmp_path/'main.py'
    program.write_bytes((ROOT/'tasks/particle_retention_v1/initial.py').read_bytes())
    config = _validated_config({'budget':1000, 'period':100, 'environment_seed':813, 'optimizer_seed':814})
    result = {'case_id':'case_000', 'config':config, 'evaluations':1000, 'evaluation_counts':{'particle':1000},
              'offline_error':2.0, 'initial_environment':{'sha256':'synthetic'}, 'environment_changes':[], 'response_log':[]}
    artifact = write_compressed_json(tmp_path/'reference.json.gz',result)
    ref = {'method':'synthetic check only', 'case_artifacts':[str(artifact.resolve())],
           'case_sha256':[hashlib.sha256(artifact.read_bytes()).hexdigest()],
           'source_sha256':hashlib.sha256(program.read_bytes()).hexdigest(),
           'scientific_sources':retention_fingerprint()}
    suite=tmp_path/'suite.json';suite.write_text(json.dumps({'cases':[config], 'feedback_references':{'random':ref,'seed':ref}}))
    return module,program,suite,tmp_path/'evaluated',artifact


def test_exact_seed_checkpoint_reuse_without_objective_calls(setup,monkeypatch):
    module,program,suite,folder,artifact=setup
    def forbidden(*args,**kwargs): raise AssertionError('no numerical calls on exact reuse')
    monkeypatch.setattr(module,'run_case',forbidden)
    assert module.evaluate(program,folder,suite)==0
    digest=hashlib.sha256((folder/'case_000.json.gz').read_bytes()).hexdigest()
    assert module.evaluate(program,folder,suite)==0
    assert hashlib.sha256((folder/'case_000.json.gz').read_bytes()).hexdigest()==digest
    assert read_json(folder/'metrics.json')['private']['cases'][0]['paired_differences']=={'random':0.,'seed':0.}
    assert not (folder/'execution-attempts.json').exists()


def test_terminal_invalid_score_preserves_exact_partial_work(setup,monkeypatch):
    module,program,suite,folder,_=setup
    program.write_text(program.read_text()+'\n# different source\n')
    calls=[]
    def invalid(*args,**kwargs):
        calls.append(1)
        exc=RetentionPolicyError('synthetic invalid score; no actual objective calls in fixture')
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
