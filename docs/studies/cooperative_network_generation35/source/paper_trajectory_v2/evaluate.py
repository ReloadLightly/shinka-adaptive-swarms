#!/usr/bin/env python3
"""Population terminal-utility extension under the explicit amended readiness gate."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import re
import statistics
import sys
import time
import traceback
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from cooperative.native import atomic_json
from paper_trajectory_v2.design import EXPERIMENT,RESULTS,SEARCH,GRID,NOISE,canonical,sha,case,conditions
from paper_trajectory_v2.runtime import append_ledger,run_case,engine_digest,compile_policy

PRIMARY_DECISION_PATH='experiments/paper_trajectory_v2/primary_reference_decision.json'
PRIMARY_DECISION_SHA256='6070d9f9e7ee98bc1c6791279626921ab21d1cae860f37d6c92764866adb47e3'
PRIMARY_DECISION_IDENTITY='fc3fa6fe30970f98aed5c732870c02d66b3bae112ff4b47f04104e12cbbf68d3'
PRIMARY_UPSTREAM_COMMIT='b3d7737613578da260fee561b6f73122dc4f2ab0'


def _validate_primary_decision(contract):
    if contract.get('primary_reference_decision_path')!=PRIMARY_DECISION_PATH:
        raise RuntimeError('Contract must bind the explicit user primary-reference decision')
    path=_frozen(contract,PRIMARY_DECISION_PATH)
    expected={'path':PRIMARY_DECISION_PATH,'sha256':PRIMARY_DECISION_SHA256,'identity_sha256':PRIMARY_DECISION_IDENTITY}
    manifest=json.loads((ROOT/'campaigns/paper_trajectory_v2.json').read_text())
    if (manifest.get('scientific_contract_decisions',{}).get('primary_reference')!=expected
        or contract['files'][PRIMARY_DECISION_PATH]!=PRIMARY_DECISION_SHA256):
        raise RuntimeError('Primary-reference decision registration/hash is absent or changed')
    decision=json.loads(path.read_text());identity=dict(decision);identity.pop('identity_sha256',None)
    if (decision.get('schema')!='paper-primary-reference-decision-v1'
        or sha(canonical(identity))!=PRIMARY_DECISION_IDENTITY or decision.get('identity_sha256')!=PRIMARY_DECISION_IDENTITY
        or decision.get('primary')!='source_executable' or decision.get('sensitivity')!=['paper_directed']
        or decision.get('upstream_commit')!=PRIMARY_UPSTREAM_COMMIT or decision.get('engine_sha256')!=contract['engine_sha256']):
        raise RuntimeError('Frozen primary must remain the pinned source executable; paper-directed is sensitivity only')
    for relative,digest in decision['equivalence_evidence'].items():
        _frozen(contract,relative)
        if contract['files'][relative]!=digest:raise RuntimeError('Primary source-equivalence evidence changed: '+relative)


def condition_id(c):
    """External conditions exclude fixed-noise and partner-sampling comparators."""
    return sha(canonical({k:c[k] for k in ('n','d','e','cost_before','cost_after','shock_count')}))[:24]


def history_id(c):
    return sha(canonical({k:c[k] for k in ('split','n','d','e','repetition','seed','shock_seed')}))[:24]


def _finite(value, *, positive=False):
    return type(value) in (int,float) and math.isfinite(value) and (not positive or value>0)


def evaluation_admission_seconds(contract):
    """Return the frozen full-evaluation deadline plus explicit draining budgets."""
    value=contract.get('evaluation_timeout','')
    if not isinstance(value,str) or not re.fullmatch(r'\d+:[0-5]\d:[0-5]\d',value):
        raise RuntimeError('Evaluation timeout must be an explicit HH:MM:SS full-panel budget')
    hours,minutes,seconds=map(int,value.split(':'));evaluation=hours*3600+minutes*60+seconds
    allowances=[contract.get(name) for name in ('model_and_proposal_drain_seconds','checkpoint_drain_seconds')]
    if evaluation<=0 or any(not _finite(x,positive=True) for x in allowances):
        raise RuntimeError('Positive finite evaluation/model/checkpoint drain allowances required')
    return evaluation+sum(allowances)


def _validate_timing(contract,panel):
    admission=evaluation_admission_seconds(contract)
    timing=json.loads(_frozen(contract,contract['evaluation_timing_path']).read_text())
    if (timing.get('schema')!='paper-extension-evaluation-timing-v1' or timing.get('numerical_workers')!=1
        or timing.get('development_cases_sha256')!=contract['files'][contract['development_cases_path']]
        or timing.get('budget_basis') not in ('measured_upper_bound','predeclared_upper_bound')
        or not timing.get('justification') or not timing.get('evidence_paths')):
        raise RuntimeError('Require a justified frozen timing budget for this exact full panel')
    for path in timing['evidence_paths']:_frozen(contract,path)
    bounds=timing['case_upper_seconds'];overhead=timing['startup_and_finalize_seconds']
    if (set(bounds)!={c['case_id'] for c in panel} or not _finite(overhead,positive=True)
        or any(not _finite(v,positive=True) or v>contract['per_case_timeout_seconds'] for v in bounds.values())):
        raise RuntimeError('Timing budget must bound every panel case and startup/finalization')
    evaluation=admission-contract['model_and_proposal_drain_seconds']-contract['checkpoint_drain_seconds']
    if evaluation<math.fsum(bounds.values())+overhead:
        raise RuntimeError('Evaluation timeout is shorter than the full-panel timing budget')
    if (timing.get('model_and_proposal_drain_seconds')!=contract['model_and_proposal_drain_seconds']
        or timing.get('checkpoint_drain_seconds')!=contract['checkpoint_drain_seconds']):
        raise RuntimeError('Drain allowances differ from their frozen timing justification')


def _frozen(contract, relative):
    path=ROOT/relative
    if Path(relative).is_absolute() or not path.resolve().is_relative_to(ROOT.resolve()):
        raise RuntimeError('Frozen artifact must be a repository-relative path')
    if relative not in contract['files'] or not path.is_file():
        raise RuntimeError('Required frozen scientific artifact missing or changed: '+relative)
    from scripts.paper_operational_compatibility import resolved_digest
    resolved_digest(relative,contract['files'][relative],lambda name:(ROOT/name).read_bytes())
    return path


def _validate_panel(panel, declaration, coverage):
    """Require the full incentive x eight-condition product, without selecting cases."""
    populations=declaration['populations'];repetitions=declaration['repetitions']
    if (not populations or len(set(populations))!=len(populations) or any(type(n) is not int or n not in (40,100) for n in populations)
        or not repetitions or len(set(repetitions))!=len(repetitions) or any(type(r) is not int or r<0 for r in repetitions)
        or declaration['split'] not in ('reference','development')):
        raise RuntimeError('Invalid predeclared population/history structure')
    expected={}
    for n in populations:
        for d in GRID:
            for e in GRID:
                for before,after,count in conditions(n):
                    for repetition in repetitions:
                        c=case(n,d,e,coverage['reference_noise'],before,after,count,repetition,
                               coverage['interpretation'],coverage['sampling'],split=declaration['split'])
                        expected[c['case_id']]=c
    actual={c['case_id']:c for c in panel}
    if len(actual)!=len(panel) or actual!=expected:
        raise RuntimeError('Panel must contain exactly every declared incentive/cost/shock/control/history case; no noise or sampling cross')
    if declaration['case_map']!={key:sha(canonical(value)) for key,value in expected.items()}:
        raise RuntimeError('Frozen panel case map/lineage differs from its predeclared exact cases')
    return expected


def _validate_confirmation_protocol(robust):
    """Validate public coverage only; never create or open confirmation seeds/cases."""
    if set(robust)!={'scope','populations','repetitions','protocol','protocol_sha256'}:
        raise RuntimeError('Confirmation coverage must contain only a public protocol, not case paths, maps or seed material')
    repetitions=robust['repetitions']
    if (not repetitions or len(set(repetitions))!=len(repetitions)
        or any(type(r) is not int or r<0 for r in repetitions)):
        raise RuntimeError('Confirmation repetitions must be predeclared without seed material')
    required={'schema':'paper-post-selection-confirmation-v1',
              'condition_structure':'full_grid_by_eight_numeric_conditions',
              'seed_derivation':'sha256-post-selection-nonce-v1','nonce_bits':256,
              'nonce_creation':'after_selection_frozen_and_discovery_stopped',
              'case_generation':'separate_confirmation_stage','discovery_access':'protocol_only'}
    if robust['protocol']!=required or robust['protocol_sha256']!=sha(canonical(required)):
        raise RuntimeError('Fresh confirmation requires the exact post-selection private-nonce protocol identity')


def _validate_coverage(contract):
    coverage=json.loads(_frozen(contract,contract['coverage_path']).read_text())
    if (coverage.get('schema')!='paper-extension-coverage-v1' or coverage.get('grid')!=GRID
        or coverage.get('interpretation')!='source_executable' or coverage.get('sampling') not in ('random','smart')
        or not _finite(coverage.get('reference_noise')) or coverage['reference_noise'] not in NOISE):
        raise RuntimeError('Require full-grid source_executable primary coverage and one reference comparator; paper_directed is sensitivity only')
    decision=json.loads(_frozen(contract,contract['scientific_decision_path']).read_text())
    if (decision.get('status')!='frozen_before_discovery' or decision.get('native_descendant_proposals_at_freeze')!=0
        or decision.get('coverage_sha256')!=contract['files'][contract['coverage_path']]
        or decision.get('primary_reference_identity')!=PRIMARY_DECISION_IDENTITY
        or not decision.get('justification') or not decision.get('evidence')):
        raise RuntimeError('Coverage/comparator choices require a recorded scientific decision before descendants')
    panel=json.loads(_frozen(contract,contract['development_cases_path']).read_text())
    declaration=coverage['development']
    if 40 not in declaration['populations'] or declaration['split']=='confirmation':
        raise RuntimeError('Discovery must include the complete main N40 structure and cannot use confirmation histories')
    expected=_validate_panel(panel,declaration,coverage)
    robust=coverage['n100_robustness']
    if robust.get('scope')=='deferred_by_execution_amendment':
        amendment=json.loads(_frozen(contract,contract['execution_amendment_path']).read_text())
        if (amendment.get('schema')!='paper-discovery-execution-amendment-v1'
            or amendment.get('supersedes_complete_reproduction_before_discovery') is not True
            or amendment.get('primary_reference')!='source_executable'
            or amendment.get('development_scope',{}).get('n')!=40
            or amendment['development_scope'].get('development_repetitions')!=1
            or amendment['development_scope'].get('external_conditions_per_repetition')!=288
            or declaration['populations']!=[40] or declaration['repetitions']!=[0]
            or coverage['sampling']!='random' or declaration['split']!='reference'):
            raise RuntimeError('Deferred N100 requires the exact user-authorized complete N40 one-repetition development amendment')
        selection=json.loads(_frozen(contract,contract['comparator_selection_path']).read_text())
        if (selection['selected_p']!=coverage['reference_noise'] or selection['utility_scale']!=contract['utility_scale']
            or decision.get('execution_amendment_sha256')!=contract['files'][contract['execution_amendment_path']]):
            raise RuntimeError('Global comparator/scale or execution authority differs from the frozen declaration')
    else:
        if robust['populations']!=[100] or robust['scope'] not in ('development','confirmation'):
            raise RuntimeError('Complete N100 robustness must have an explicit frozen development/confirmation scope')
        if robust['scope']=='development':
            robust_panel=json.loads(_frozen(contract,robust['panel_path']).read_text())
            robust_expected=_validate_panel(robust_panel,robust,coverage)
            if robust_expected!={key:value for key,value in expected.items() if value['n']==100}:
                raise RuntimeError('N100 development robustness differs from the evaluated panel')
        else:
            if 100 in declaration['populations']:
                raise RuntimeError('N100 confirmation cannot also appear in the development panel')
            _validate_confirmation_protocol(robust)
    weights=contract['condition_weights'];expected_conditions={condition_id(c) for c in panel}
    if (set(weights)!=expected_conditions or any(not _finite(v,positive=True) for v in weights.values())
        or not math.isclose(math.fsum(weights.values()),1.0,rel_tol=0,abs_tol=1e-12)):
        raise RuntimeError('Condition weights must be positive, finite, normalized and cover every external condition')
    if robust.get('scope')=='deferred_by_execution_amendment' and any(not math.isclose(v,1/288,rel_tol=0,abs_tol=1e-15) for v in weights.values()):
        raise RuntimeError('Amended development objective requires equal weight for all288 external conditions')
    baselines=json.loads(_frozen(contract,contract['development_baseline_path']).read_text())
    if set(baselines)!=set(expected):raise RuntimeError('Baseline must cover exactly the frozen panel case IDs')
    for key,c in expected.items():
        receipt=baselines[key]
        identity={'schema':'paper-trajectory-case-v1','engine_sha256':contract['engine_sha256'],
                  'program_sha256':contract['reference_program_sha256'],'case':c}
        if (receipt.get('identity')!=identity or receipt.get('case_id')!=key
            or receipt.get('cache_key')!=sha(canonical(identity)) or not _finite(receipt.get('terminal_mean_utility'))):
            raise RuntimeError('Baseline source/engine/case/cache identity or utility mismatch: '+key)
        cache_key=receipt['cache_key']
        saved_path=str((RESULTS/'cache'/cache_key[:2]/(cache_key+'.json')).relative_to(ROOT))
        if json.loads(_frozen(contract,saved_path).read_text())!=receipt:
            raise RuntimeError('Baseline differs from the exact saved case-cache receipt: '+key)
        _frozen(contract,receipt['trajectory_path'])
        if receipt['trajectory_sha256']!=contract['files'][receipt['trajectory_path']]:
            raise RuntimeError('Baseline trajectory identity mismatch: '+key)
    return panel,baselines


def verify_contract(*, recovery_inspection=False):
    """Read-only science verification; inspection alone never admits an evaluation."""
    from paper_trajectory_v2.gate import require_reference_milestone
    milestone=require_reference_milestone()
    if not recovery_inspection and ((SEARCH/'infrastructure-pause.json').exists() or (SEARCH/'recovery-pending.json').exists()):
        raise RuntimeError('Unresolved infrastructure pause; preserve and explicitly reconcile its evidence before resume')
    path=EXPERIMENT/'scientific_contract.json'
    if not path.exists():raise RuntimeError('The all-actor extension contract has not been frozen after reference reproduction')
    contract=json.loads(path.read_text());identity=dict(contract);identity.pop('identity_sha256',None)
    if contract.get('schema')!='paper-extension-contract-v1':raise RuntimeError('Explicit extension contract schema required')
    if sha(canonical(identity))!=contract['identity_sha256']:raise RuntimeError('Scientific contract identity mismatch')
    _validate_primary_decision(contract)
    required=['paper_trajectory_v2/'+name+'.py' for name in ('evaluate','runtime','design','gate','policy_guard','native','recovery')]
    required.append('scripts/paper_recover_evaluation.py')
    for field in ('development_cases_path','development_baseline_path','coverage_path','scientific_decision_path','evaluation_timing_path','seed_path','task_prompt_path'):
        required.append(contract[field])
    # Check only artifacts consumed by discovery. An arbitrary extra file-map
    # entry must not cause this process to open a held-out artifact.
    for relative in set(required):_frozen(contract,relative)
    from paper_trajectory_v2.policy_guard import guard_identity
    if contract.get('compiled_guard_identity')!=guard_identity():raise RuntimeError('Compiled guard scientific identity mismatch')
    if contract.get('evaluator_sha256')!=contract['files']['paper_trajectory_v2/evaluate.py']:
        raise RuntimeError('Explicit evaluator scientific identity mismatch')
    if contract.get('reference_program_sha256')!='reference:'+sha((ROOT/'java-paper/paper/ReferencePolicy.java').read_bytes()):
        raise RuntimeError('Frozen comparator reference source identity mismatch')
    if not _finite(contract.get('utility_scale'),positive=True):raise RuntimeError('Utility scale must be finite and positive')
    if not _finite(contract.get('per_case_timeout_seconds'),positive=True):raise RuntimeError('Per-case timeout must be finite and positive')
    if contract['engine_sha256']!=engine_digest():raise RuntimeError('Reference/discovery engine identity changed')
    if contract['reference_milestone_identity']!=milestone['identity_sha256']:raise RuntimeError('Reference milestone changed after extension freeze')
    for name,source in [('CandidatePolicy.java',contract['seed_path']),('task_prompt.md',contract['task_prompt_path'])]:
        if sha((SEARCH/'frozen'/name).read_bytes())!=contract['files'][source]:raise RuntimeError('Executed immutable copy differs: '+name)
    panel,_=_validate_coverage(contract)
    _validate_timing(contract,panel)
    return contract


def evaluate(program_path,output):
    started=time.time();output=Path(output);output.mkdir(parents=True,exist_ok=True)
    candidate_sha=None;stage='contract';receipts=[];effects=[]
    try:
        candidate_sha=sha(Path(program_path).read_bytes())
        from paper_trajectory_v2.recovery import evaluation_permit
        recovering=evaluation_permit(ROOT,SEARCH,program_path,output)
        contract=verify_contract(recovery_inspection=True) if recovering else verify_contract()
        panel,baselines=_validate_coverage(contract)
        if any((output/name).exists() for name in ('metrics.json','correct.json','evaluation-interrupted.json')):
            raise RuntimeError('Existing evaluation evidence requires explicit reconciliation; refusing overwrite or retry')
        stage='candidate_compile';compile_policy(program_path);stage='numerical_case'
        for c in panel:
            receipt=run_case(c,program_path,role='discovery_evaluation',timeout=contract['per_case_timeout_seconds'])
            expected={'schema':'paper-trajectory-case-v1','engine_sha256':contract['engine_sha256'],'program_sha256':candidate_sha,'case':c}
            if (receipt.get('identity')!=expected or receipt.get('cache_key')!=sha(canonical(expected))
                or not _finite(receipt.get('terminal_mean_utility'))):
                raise RuntimeError('Candidate returned a foreign/nonfinite case receipt')
            base=baselines[c['case_id']];raw=receipt['terminal_mean_utility']-base['terminal_mean_utility']
            effects.append({'case_id':c['case_id'],'condition_id':condition_id(c),'history_id':history_id(c),
                'raw_terminal_population_utility_difference':raw,'scaled_difference':raw/contract['utility_scale'],
                'candidate_terminal_population_utility':receipt['terminal_mean_utility'],
                'baseline_terminal_population_utility':base['terminal_mean_utility'],'cache_key':receipt['cache_key']})
            receipts.append(receipt)
        stage='aggregation'
        grouped={}
        for e in effects:grouped.setdefault(e['condition_id'],[]).append(e['scaled_difference'])
        if set(grouped)!=set(contract['condition_weights']):raise RuntimeError('Incomplete applicable paper condition structure')
        score=sum(contract['condition_weights'][k]*statistics.mean(v) for k,v in grouped.items())
        if not _finite(score):raise RuntimeError('Nonfinite aggregate evaluation')
        atomic_json(output/'case_results.json',effects)
        raw=statistics.mean(e['raw_terminal_population_utility_difference'] for e in effects)
        feedback=(f'All-actor full-trajectory development evaluation: {len(effects)} trajectories in {len({e["history_id"] for e in effects})} history-seed families across {len(grouped)} declared external conditions. Related cost/shock cases share a family and are not independent replications. '
                  f'Mean terminal population utility difference {raw:.8g}; frozen scaled score {score:.8g}. '
                  'This development selection does not establish generalization, lower-tail improvement or mutual benefit; inspect trajectories and shocked/unshocked distributions.')
        metrics={'combined_score':score,'public':{'development_trajectories':len(effects),'history_seed_families':len({e['history_id'] for e in effects}),'external_conditions':len(grouped),'raw_mean_terminal_population_utility_difference':raw},
                 'private':{'candidate_sha256':candidate_sha,'scientific_identity':contract['identity_sha256'],'case_cache_keys':[r['cache_key'] for r in receipts]},'text_feedback':feedback}
        atomic_json(output/'metrics.json',metrics);atomic_json(output/'correct.json',{'correct':True,'error':None})
    except Exception as exc:
        error=type(exc).__name__+': '+str(exc)
        # Runtime currently exposes plain exceptions. Only known compilation/guard
        # violations or an actual candidate Java stack frame justify invalidity.
        from paper_trajectory_v2.policy_guard import PolicyValidationError
        invalid=(stage=='candidate_compile' and (
            (isinstance(exc,PolicyValidationError) and 'changed after import' not in str(exc))
            or (type(exc) is ValueError and str(exc).startswith(('Expected public final CandidatePolicy',
                'Policy attempted undeclared runtime access','Only paper capability imports')))
            or (type(exc) is ValueError and str(exc).startswith('Candidate compilation failed:')
                and bool(re.search(r'CandidatePolicy\.java:\d+: error:',str(exc))))))
        invalid=invalid or (stage=='numerical_case' and bool(re.search(r'java\.lang\.(?:NullPointerException|ArithmeticException|IllegalArgumentException|IndexOutOfBoundsException|ArrayIndexOutOfBoundsException|StackOverflowError)',str(exc))) and bool(re.search(r'\bat CandidatePolicy\.',str(exc))))
        category='candidate_invalidity' if invalid else 'infrastructure_interruption'
        failure={'schema':'paper-evaluation-failure-v1','time':time.time(),'failure_classification':category,
                 'reason':error,'stage':stage,'candidate_sha256':candidate_sha,'program_path':str(Path(program_path).resolve()),
                 'results_dir':str(output.resolve()),'completed_case_cache_keys':[r['cache_key'] for r in receipts],
                 'partial_effects':effects,'traceback':traceback.format_exc(),'automatic_retry':False}
        evidence=output/'failures'/(str(time.time_ns())+'-'+uuid.uuid4().hex+'.json');atomic_json(evidence,failure)
        if invalid:
            atomic_json(output/'metrics.json',{'combined_score':-1e9,'public':{},'private':{'candidate_sha256':candidate_sha,'failure_classification':category},'text_feedback':'Invalid candidate policy: '+error[-4000:]})
            atomic_json(output/'correct.json',{'correct':False,'error':error[-6000:],'failure_classification':category})
        else:
            pause={**failure,'evidence_path':str(evidence.resolve()),'reason':'Evaluation infrastructure interruption; inspect saved source, lineage and exact-case evidence before explicit recovery'}
            if not (output/'evaluation-interrupted.json').exists():atomic_json(output/'evaluation-interrupted.json',pause)
            if not (SEARCH/'infrastructure-pause.json').exists():atomic_json(SEARCH/'infrastructure-pause.json',pause)
            # No numeric fitness or correct=False claim for infrastructure failure.
        append_ledger({'kind':'evaluation','completed':False,'candidate_sha256':candidate_sha,'failure_classification':category,'elapsed_seconds':time.time()-started,'error':error[-2000:],'evidence_path':str(evidence.resolve())})
        return 1 if invalid else 4
    append_ledger({'kind':'evaluation','completed':True,'candidate_sha256':candidate_sha,'elapsed_seconds':time.time()-started,'trajectories':len(effects)})
    return 0

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--program_path',required=True);p.add_argument('--results_dir',required=True);a=p.parse_args();raise SystemExit(evaluate(a.program_path,a.results_dir))
