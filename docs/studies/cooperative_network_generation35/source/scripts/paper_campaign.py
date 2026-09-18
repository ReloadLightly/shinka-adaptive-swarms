#!/usr/bin/env python3
"""One bounded controller for paper_trajectory_v2; references precede gated discovery."""
from __future__ import annotations
import argparse
import dataclasses
import fcntl
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from cooperative.native import atomic_json, terminal_failures, sanitize_environment
from paper_trajectory_v2.design import CAMPAIGN,EXPERIMENT,RESULTS,MANIFEST,SEARCH,canonical,sha
from paper_trajectory_v2.runtime import engine_digest,run_panel,verify_reference_engine
from scripts.campaign_state import database_fingerprint,standalone_backup,compatible_subset
from scripts.paper_review_target import review_target, review_reached, record_review_pause, set_review_target


def read(path):return json.loads(Path(path).read_text())

def status():
    result={'campaign_id':CAMPAIGN,'output_path':str(RESULTS),'database_path':str(SEARCH/'programs.sqlite'),
            'database_exists':(SEARCH/'programs.sqlite').is_file(),
            'descendant_proposal_ceiling':50,'planned_initialization_programs':1,'initialization_programs':0,
            'terminal_slots':[],'valid_descendants':0,'unique_evaluated_programs':0,'administrative_copies':0,
            'model_responses':0,'model_attempts':0,'model_retries':0,'usage_by_role':{},'usage_by_arm':{},'usage_by_subrole':{}}
    if (SEARCH/'programs.sqlite').exists():
        fingerprint=database_fingerprint(SEARCH/'programs.sqlite');originals=[r for r in fingerprint['records'] if not r.get('administrative_copy')]
        failures=terminal_failures(SEARCH)
        result.update(database=fingerprint,terminal_slots=sorted({r['generation'] for r in originals}|failures),
            initialization_programs=sum(r['generation']==0 for r in originals),
            failed_proposal_slots=sorted(failures),valid_descendants=sum(r['generation']>0 and bool(r['correct']) for r in originals),
            invalid_descendants=sum(r['generation']>0 and not r['correct'] for r in originals),
            unique_evaluated_programs=len(originals),administrative_copies=len(fingerprint['records'])-len(originals))
    for p in (SEARCH/'usage').glob('*.json'):
        u=read(p);result['model_attempts']+=1;result['model_responses']+=u['status']=='returned'
        result['model_retries']+=bool(u.get('is_retry'))
        for field,key in [('usage_by_role',u['role']),('usage_by_arm',u.get('route','unknown')),
                          ('usage_by_subrole',u['role']+'/'+str(u.get('subrole') or 'unspecified'))]:
            v=result[field].setdefault(key,{'attempts':0,'responses':0,'elapsed_seconds':0.,'input_tokens':0,'output_tokens':0})
            v['attempts']+=1;v['responses']+=u['status']=='returned';v['elapsed_seconds']+=u.get('elapsed_seconds',0.)
            for token in ['input_tokens','output_tokens']:v[token]+=u.get('response',{}).get(token,0) or 0
    result['locally_denied_provider_attempts']=sum(
        read(p).get('error','').startswith('Batch model elapsed allowance exhausted')
        for p in (SEARCH/'usage').glob('*.json'))
    recovered=RESULTS/'operations/provider-timeout-drain/completed-provider-evidence.json'
    result['provider_completions_preserved_after_adapter_failure']=0
    if recovered.exists():
        evidence=read(recovered);response=ROOT/evidence['final_response_path']
        usage=read(SEARCH/'usage'/(evidence['usage_receipt_id']+'.json'))
        if sha(response.read_bytes())!=evidence['final_response_sha256']:raise RuntimeError('Preserved provider response changed')
        if evidence['final_response_available'] and usage['status']!='returned':
            result['provider_completions_preserved_after_adapter_failure']=1
            result['preserved_provider_token_usage']=evidence['usage_events'][-1]['info']['total_token_usage']
    result['logical_completed_model_responses']=result['model_responses']+result['provider_completions_preserved_after_adapter_failure']
    result['remaining_descendant_slots']=50-len([g for g in result['terminal_slots'] if g>0])
    if (RESULTS/'reference-index.json').exists():
        index=read(RESULTS/'reference-index.json');result['reference_completed']=index['completed'];result['reference_planned']=index['planned']
        result['reference_blocked_pending_cases']=index.get('blocked_pending_cases',0)
        result['reference_feasible_remaining']=index.get('feasible_remaining',index['planned']-index['completed'])
    counts={'completed_physical_trajectories':0,'failed_trajectories':0,'exact_cache_reuses':0,'evaluation_invocations':0,'serial_numerical_seconds':0.}
    if (RESULTS/'evaluation_usage.jsonl').exists():
        for line in (RESULTS/'evaluation_usage.jsonl').read_text().splitlines():
            v=json.loads(line)
            if v['kind']=='numerical_case':counts['completed_physical_trajectories' if v['completed'] else 'failed_trajectories']+=1;counts['serial_numerical_seconds']+=v.get('elapsed_seconds',0.)
            elif v['kind']=='cache_reuse':counts['exact_cache_reuses']+=1
            elif v['kind']=='evaluation':counts['evaluation_invocations']+=1
    result['numerical']=counts
    if result['remaining_descendant_slots']<0:raise RuntimeError('Native descendant ceiling was exceeded')
    return result


def checkpoint(manifest,state):
    # Same proven publication step as v1: after the child drains, materialize
    # WAL data in place before making/replacing standalone primary snapshots.
    for name in ('programs.sqlite','prompts.sqlite'):
        path=SEARCH/name
        if not path.exists():continue
        connection=sqlite3.connect(path,timeout=10)
        try:
            result=connection.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()
            if result[0]!=0:raise RuntimeError(f'SQLite checkpoint still busy for {name}: {result}')
            if connection.execute('PRAGMA journal_mode=DELETE').fetchone()[0].lower()!='delete':
                raise RuntimeError('Cannot materialize standalone primary database: '+name)
        finally:connection.close()
    snapshot=status()
    review=record_review_pause(snapshot, SEARCH)
    if review:
        state='paused_for_generation_'+str(review['generation'])+'_review'
        manifest['review_pause']=review
    manifest.update(status=state,updated_at=time.time(),accounting=snapshot,
                    operational_review_target=review_target(SEARCH))
    if 'database' in snapshot:
        count=len(snapshot['terminal_slots']);target=SEARCH/'checkpoints'/f'programs-{count:03d}.sqlite'
        backup=standalone_backup(SEARCH/'programs.sqlite',target)
        if backup['records']!=snapshot['database']['records']:raise RuntimeError('Live/snapshot program records differ')
        # Primary and standalone published bytes each contain all completed WAL state.
        standalone_backup(target,SEARCH/'programs.sqlite')
        publication={'path':str(target.relative_to(ROOT)),'sqlite_sha256':sha(target.read_bytes()),'records_sha256':backup['records_sha256'],
                     'program_rows':backup['program_rows'],'generations':backup['generations'],'best_program_id':backup['best_program_id'],
                     'best_generation':backup['best_generation'],'best_score':backup['best_score'],'verified_at':time.time()}
        native=SEARCH/'checkpoints'/f'native-{count:03d}';native.mkdir(parents=True,exist_ok=True)
        native_hashes={}
        for relative in ['prompts.sqlite','bandit_state.pkl','phase-b-bandit-summary.json','native-task-identity.json',
                         'native_memory/state.json','native_memory/native-meta-export.json']:
            source=SEARCH/relative
            if not source.exists():continue
            destination=native/relative;destination.parent.mkdir(parents=True,exist_ok=True)
            if relative.endswith('.sqlite'):
                standalone_backup(source,destination,programs=False)
                standalone_backup(destination,source,programs=False)
            else:shutil.copy2(source,destination)
            native_hashes[relative]=sha(destination.read_bytes())
        publication.update(native_state_path=str(native.relative_to(ROOT)),native_state_sha256=native_hashes,
                           terminal_slots=snapshot['terminal_slots'])
        manifest['publication']=publication
    atomic_json(RESULTS/'report'/'accounting.json',snapshot)
    atomic_json(MANIFEST,manifest)
    from scripts.paper_research_log import write_research_log
    print(write_research_log(ROOT,snapshot),flush=True)
    return snapshot


def verify_resume(manifest):
    if manifest.get('campaign_id')!=CAMPAIGN:
        raise RuntimeError('Campaign manifest identity does not match paper_trajectory_v2; refusing admission')
    for field,path in [('design_sha256',EXPERIMENT/'design.json'),('reference_cases_sha256',EXPERIMENT/'reference_cases.json')]:
        if manifest[field]!=sha(path.read_bytes()):raise RuntimeError('Declared reference design changed: '+str(path))
    verify_reference_engine()
    if manifest.get('discovery_frozen'):
        from paper_trajectory_v2.evaluate import verify_contract
        verify_contract()
    publication=manifest.get('publication')
    if publication:
        published=ROOT/publication['path']
        if sha(published.read_bytes())!=publication['sqlite_sha256']:raise RuntimeError('Published snapshot bytes changed')
        saved=database_fingerprint(published)
        if saved['records_sha256']!=publication['records_sha256']:raise RuntimeError('Published database content mismatch')
        if not (SEARCH/'programs.sqlite').exists():standalone_backup(published,SEARCH/'programs.sqlite')
        current=database_fingerprint(SEARCH/'programs.sqlite');compatible_subset(saved['records'],current['records'])
        same_population=current['records_sha256']==saved['records_sha256']
        for field in ['program_rows','generations','best_program_id','best_generation','best_score']:
            if saved[field]!=publication[field]:raise RuntimeError('Published database/report disagreement: '+field)
        report=manifest.get('accounting',{}).get('database',{})
        if report.get('records_sha256')!=saved['records_sha256']:raise RuntimeError('Published database/accounting content differs')
        for relative,expected in publication.get('native_state_sha256',{}).items():
            snapshot=ROOT/publication['native_state_path']/relative
            if sha(snapshot.read_bytes())!=expected:raise RuntimeError('Published native state changed: '+relative)
            current=SEARCH/relative
            if not current.exists():
                if not same_population:raise RuntimeError('Later local population lacks its matching native state; refusing older snapshot import')
                current.parent.mkdir(parents=True,exist_ok=True)
                if relative.endswith('.sqlite'):standalone_backup(snapshot,current,programs=False)
                else:shutil.copy2(snapshot,current)


def blocked_methods(manifest):
    """Skip only explicitly evidenced infeasible methods; they remain required."""
    records=[]
    for record in manifest.get('blocked_methods',[]):
        if record.get('status')!='blocked':continue
        path=ROOT/record['evidence_path']
        if sha(path.read_bytes())!=record['evidence_sha256']:raise RuntimeError('Recorded method blocker evidence changed')
        if not record.get('reason') or record.get('consequential') is not True:raise RuntimeError('Method block lacks an explicit consequential cause')
        records.append(record)
    return records


def method_is_blocked(case,blocked):
    return any(all(case[key]==record[key] for key in ['n','sampling','interpretation']) for record in blocked)


def references(args,deadline,manifest):
    mode='benchmark' if args.action=='benchmark' else 'reference'
    if manifest.get('reference_execution_deferred'):
        raise RuntimeError('Additional reference/benchmark admissions are deferred by the explicit execution amendment')
    declared=read(EXPERIMENT/(mode+'_cases.json'));cases=declared
    blocked=blocked_methods(manifest)
    if mode=='reference' and args.reference_method!='all':
        n,sampling,interpretation=args.reference_method.split(':')
        cases=[c for c in cases if c['n']==int(n) and c['sampling']==sampling and c['interpretation']==interpretation]
    indexpath=RESULTS/(mode+'-index.json');identity=engine_digest()
    old=read(indexpath) if indexpath.exists() else {}
    if old and old.get('engine_sha256')!=identity:
        raise RuntimeError('Saved reference index has a different frozen engine; preserve it for explicit versioned reconciliation')
    records={r['case_id']:r for r in old.get('cases',[])}
    allowed={c['case_id']:c for c in declared}
    if len(records)!=len(old.get('cases',[])) or old.get('completed',len(records))!=len(records):raise RuntimeError('Reference index has duplicate or inconsistent completion counts')
    for case_id,receipt in records.items():
        if case_id not in allowed or receipt['identity']['case']!=allowed[case_id] or receipt['identity']['engine_sha256']!=identity:
            raise RuntimeError('Saved reference case/configuration identity changed')
        if sha((ROOT/receipt['trajectory_path']).read_bytes())!=receipt['trajectory_sha256']:raise RuntimeError('Saved reference trajectory changed')
    started=time.time();before=len(records)
    def save():
        blocked_pending=sum(c['case_id'] not in records and method_is_blocked(c,blocked) for c in declared)
        atomic_json(indexpath,{'campaign_id':CAMPAIGN,'engine_sha256':identity,'planned':12 if mode=='benchmark' else 34560,
            'completed':len(records),'cases':list(records.values()),'updated_at':time.time(),
            'blocked_methods':blocked,'blocked_pending_cases':blocked_pending,
            'feasible_remaining':len(declared)-len(records)-blocked_pending})
    def progress(r,count,elapsed):
        if r['identity']['engine_sha256']!=identity or r['identity']['case']!=allowed.get(r['case_id']):
            raise RuntimeError('Returned reference receipt differs from the admitted engine or declared case')
        records[r['case_id']]=r
        if count%10==0 or mode=='benchmark':
            save();print(json.dumps({'kind':mode,'completed':len(records),'last_seconds':r['elapsed_seconds'],'last_case':r['identity']['case'],'wall_seconds':elapsed}),flush=True)
    profile={}
    for path in [RESULTS/'benchmark-index.json',indexpath]:
        if not path.exists():continue
        saved=read(path)
        if saved.get('engine_sha256')!=identity:continue
        for receipt in saved.get('cases',[]):
            c=receipt['identity']['case'];key=(c['n'],c['sampling'],c['interpretation'])
            profile[key]=max(profile.get(key,0.),receipt['elapsed_seconds'])
    try:run_panel([c for c in cases if c['case_id'] not in records and not method_is_blocked(c,blocked)],
        deadline=deadline,workers=args.workers,role=mode,progress=progress,timing_profile=profile,
        stop_requested=lambda:(SEARCH/'pause-request.json').exists())
    finally:
        save();manifest.setdefault('numerical_sessions',[]).append({'kind':mode,'started_at':started,'finished_at':time.time(),'workers':args.workers,'new_trajectories':len(records)-before,'wall_seconds':time.time()-started})
        checkpoint(manifest,'reference_paused' if mode=='reference' else 'benchmark_completed' if len(records)==len(declared) else 'benchmark_paused')
    if mode=='benchmark':
        measured=[{'case':r['identity']['case'],'seconds':r['elapsed_seconds']} for r in records.values()]
        atomic_json(RESULTS/'operations/runtime-benchmark.json',{'measured':measured,'workers':args.workers,'wall_seconds':time.time()-started,'serial_seconds':sum(r['elapsed_seconds'] for r in records.values()),'extrapolation_warning':'Sparse/moderate/dense measurements are workload probes, not guaranteed campaign runtime or subscription capacity.'})


OPERATIONAL_AMENDMENT = EXPERIMENT / 'provider_timeout_amendment_v1.json'


def provider_operations(manifest=None):
    """Versioned operational override; retain historical scientific identity bytes."""
    manifest = read(MANIFEST) if manifest is None else manifest
    record = manifest.get('provider_timeout_amendment', {})
    if record.get('path') != str(OPERATIONAL_AMENDMENT.relative_to(ROOT)) or record.get('sha256') != sha(OPERATIONAL_AMENDMENT.read_bytes()):
        raise RuntimeError('Provider operational amendment is absent or mismatched')
    settings = read(OPERATIONAL_AMENDMENT)
    from paper_trajectory_v2.evaluate import verify_contract
    if settings['scientific_identity_sha256'] != verify_contract()['identity_sha256']:
        raise RuntimeError('Provider amendment targets a different scientific contract')
    return settings


def proposal_admission_seconds(contract, settings):
    from paper_trajectory_v2.evaluate import evaluation_admission_seconds
    evaluation_and_checkpoint = evaluation_admission_seconds(contract) - contract['model_and_proposal_drain_seconds']
    attempts = sum(settings['maximum_provider_attempts'].values())
    return (evaluation_and_checkpoint + attempts * (settings['per_request_seconds'] + 2)
            + attempts / 2 + settings['preflight_reserve_seconds'] + settings['final_meta_drain_seconds'])


def batch(target):
    # Only admitted by controller while retaining the same OS-lock file descriptor.
    inherited=os.environ.get('PAPER_CONTROLLER_LOCK_FD')
    if inherited is None:raise RuntimeError('Native batch must be admitted by its campaign controller')
    lockstat=os.fstat(int(inherited));expected_lock=(ROOT/'campaigns'/(CAMPAIGN+'.lock')).stat()
    if (lockstat.st_dev,lockstat.st_ino)!=(expected_lock.st_dev,expected_lock.st_ino):raise RuntimeError('Native batch inherited the wrong campaign lock')
    fcntl.flock(int(inherited),fcntl.LOCK_EX|fcntl.LOCK_NB)
    # A second admission guard also protects a controller loaded before the
    # operational boundary was installed. No provider or native proposal runs.
    if target-1>review_target(SEARCH):
        if not record_review_pause(status(), SEARCH):
            raise RuntimeError('Review boundary reached with missing terminal proposal slots')
        return 0
    # Verify before importing provider setup or installing any call observer.
    from paper_trajectory_v2.evaluate import verify_contract
    contract=verify_contract()
    from paper_trajectory_v2.gate import require_discovery_readiness
    require_discovery_readiness(require_seed=True)
    sanitize_environment()
    # Match the already verified free preflight environment for every native
    # provider check/call; avoid npm registry access for the pinned cached bridge.
    os.environ.update(npm_config_offline='true',NPM_CONFIG_OFFLINE='true',
        npm_config_update_notifier='false',npm_config_audit='false',npm_config_fund='false')
    from shinka.core import EvolutionConfig
    from shinka.database import DatabaseConfig
    from shinka.launch import LocalJobConfig
    from cooperative.native import install_usage_observer,install_role_context
    from paper_trajectory_v2.native import configuration,make_runner_class
    from scripts.paper_embedding_metadata import subscription_preflight
    settings=configuration()
    preflight=subscription_preflight()
    atomic_json(SEARCH/'operations'/f'preflight-{target:03d}-{time.time_ns()}.json',preflight)
    # Reuse this batch's actual successful pinned-binary check. Native route and
    # environment validation still run; repeating npm --check adds no evidence.
    import shinka.model_availability as availability
    def verified_bridge():
        if preflight.get('headless_check_passed') is not True:raise RuntimeError('Pinned bridge preflight failed')
    availability.check_headless_available=verified_bridge
    install_usage_observer(SEARCH,allowed_routes=settings['evolution']['llm_models'],phase=CAMPAIGN)
    deadline=float(os.environ['PAPER_SESSION_DEADLINE'])
    from paper_trajectory_v2.evaluate import evaluation_admission_seconds
    evaluation_and_checkpoint=evaluation_admission_seconds(contract)-contract['model_and_proposal_drain_seconds']
    operations=provider_operations()
    required=proposal_admission_seconds(contract,operations)-operations['preflight_reserve_seconds']
    if deadline-time.time()<required:
        raise RuntimeError('Window cannot admit the full native request/retry sequence and frozen evaluator after preflight')
    atomic_json(SEARCH/'operations'/f'provider-admission-{target:03d}-{time.time_ns()}.json',{
        'operational_amendment_sha256':sha(OPERATIONAL_AMENDMENT.read_bytes()),
        'per_request_seconds':operations['per_request_seconds'],'shared_model_timer':False,
        'maximum_provider_attempts':operations['maximum_provider_attempts'],
        'required_seconds':required,'evaluation_and_checkpoint_reserved_seconds':evaluation_and_checkpoint,
        'session_deadline':deadline})
    install_provider_request_timeout(operations['per_request_seconds'],deadline=deadline,
        reserve_after_request=evaluation_and_checkpoint)
    evolution=EvolutionConfig(task_sys_msg=(SEARCH/'frozen/task_prompt.md').read_text(),init_program_path=str(SEARCH/'frozen/CandidatePolicy.java'),results_dir=str(SEARCH),num_generations=target,**settings['evolution'])
    database=DatabaseConfig(**settings['database'])
    job=LocalJobConfig(eval_program_path=str(ROOT/'paper_trajectory_v2/evaluate.py'),python_executable=sys.executable,time=contract['evaluation_timeout'],numeric_threads_per_job=1)
    atomic_json(SEARCH/'resolved-settings'/f'target-{target:03d}.json',{'evolution':dataclasses.asdict(evolution),'database':dataclasses.asdict(database),'job':dataclasses.asdict(job)})
    Runner=make_runner_class(SEARCH,scientific_identity=contract['identity_sha256'],immutable_prompt_path=SEARCH/'frozen/task_prompt.md',search_prompt_path=SEARCH/'frozen/search_prompt.md')
    runner=Runner(evo_config=evolution,db_config=database,job_config=job,max_evaluation_jobs=1,max_proposal_jobs=1,max_db_workers=1,verbose=True)
    if runner.novelty_judge:install_role_context(runner.novelty_judge.async_llm_client,'novelty')
    runner.run()
    return 3 if (SEARCH/'subscription-pause.json').exists() else 4 if (SEARCH/'infrastructure-pause.json').exists() else 0


def install_provider_request_timeout(seconds, *, deadline=None, reserve_after_request=0):
    """Bound Codex provider time and drain the entire owned subprocess group.

    Command arguments/environment remain the pinned provider's. Numerical jobs
    are outside this wrapper. A timeout cannot leave npm's Codex grandchildren
    alive holding its stdout pipe indefinitely.
    """
    import asyncio
    import signal
    from shinka.llm.providers import headless
    from shinka.llm.providers.errors import NonRetryableLLMError
    allowance=float(seconds)
    if allowance<=0:raise ValueError('Positive per-request provider timeout required')
    def timeout():
        return allowance
    def pause(reason, **details):
        receipt={'reason':reason,'campaign_id':CAMPAIGN,'recorded_at':time.time(),
                 'per_request_seconds':allowance,'shared_model_timer':False,**details}
        atomic_json(SEARCH/'provider-infrastructure-pause.json',receipt)
        if not (SEARCH/'infrastructure-pause.json').exists():
            atomic_json(SEARCH/'infrastructure-pause.json',receipt)
    async def bounded(*,model,command):
        if model.agent!='codex':raise NonRetryableLLMError('Only the authorized Codex subscription process is permitted')
        if (SEARCH/'provider-infrastructure-pause.json').exists():
            raise NonRetryableLLMError('Provider infrastructure pause retained; no additional external request admitted')
        if deadline is not None and time.time()+allowance+reserve_after_request>deadline:
            pause('Insufficient window for a full provider request and accepted-work drain; no child launched',
                  session_deadline=deadline,reserve_after_request=reserve_after_request)
            raise NonRetryableLLMError('Full provider request does not fit; request timeout was not shortened')
        started=time.monotonic();process=None;communication=None
        async def stop_group():
            signals=[]
            for sig in (signal.SIGTERM,signal.SIGKILL):
                try:os.killpg(process.pid,sig);signals.append(sig.name)
                except ProcessLookupError:pass
                try:
                    result=await asyncio.wait_for(asyncio.shield(communication),timeout=1.)
                    # A remaining group may contain a detached stdout-free child.
                    try:os.killpg(process.pid,signal.SIGKILL);signals.append('SIGKILL_remaining_group')
                    except ProcessLookupError:pass
                    return result,signals
                except asyncio.TimeoutError:continue
            communication.cancel()
            # No unbounded communicate after the group has been killed.
            raise RuntimeError('Owned provider group was killed but pipe drainage did not finish within2seconds')
        try:
            process=await asyncio.create_subprocess_exec(*command,stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,env=headless._subprocess_env(model),start_new_session=True)
            communication=asyncio.create_task(process.communicate())
            try:
                stdout,stderr=await asyncio.wait_for(asyncio.shield(communication),timeout=allowance)
            except asyncio.TimeoutError:
                (stdout,stderr),signals=await stop_group()
                stem=SEARCH/'operations'/f'headless-timeout-{time.time_ns()}'
                stem.parent.mkdir(parents=True,exist_ok=True)
                stem.with_suffix('.stdout').write_bytes(stdout);stem.with_suffix('.stderr').write_bytes(stderr)
                atomic_json(stem.with_suffix('.json'),{'reason':'Owned Headless/Codex process group exceeded its admitted provider duration',
                    'admitted_seconds':allowance,'elapsed_seconds':time.monotonic()-started,'pid':process.pid,
                    'signals':signals,'returncode':process.returncode,'command':command,'late_clean_exit':process.returncode==0})
                if process.returncode!=0:
                    pause('Provider request timed out; owned process group drained; inspect before new submissions',
                          timeout_receipt=str(stem.with_suffix('.json').relative_to(SEARCH)))
                    raise
                # Preserve an already completed successful response observed while
                # draining; the unchanged native parser must still validate it.
            except asyncio.CancelledError:
                await stop_group()
                raise
            return subprocess.CompletedProcess(command,process.returncode,stdout.decode('utf-8',errors='replace'),stderr.decode('utf-8',errors='replace'))
        except (OSError, RuntimeError) as error:
            pause('Provider process infrastructure failure',error=str(error))
            raise
    headless.headless_timeout=timeout
    headless._run_headless_command_async=bounded


def discovery(args,deadline,manifest,lock):
    from paper_trajectory_v2.gate import require_discovery_readiness
    require_discovery_readiness(require_seed=True)
    if not manifest.get('discovery_frozen'):raise RuntimeError('Source-fidelity/scientific-contract gate is not complete; discovery remains pending')
    from paper_trajectory_v2.evaluate import verify_contract,evaluation_admission_seconds
    contract=verify_contract()
    operations=provider_operations(manifest)
    full_panel_admission_seconds=proposal_admission_seconds(contract,operations)
    if (SEARCH/'infrastructure-pause.json').exists():raise RuntimeError('Infrastructure pause retained; inspect receipt before resuming')
    if (SEARCH/'subscription-pause.json').exists():raise RuntimeError('Subscription capacity pause retained; inspect receipt before a new attempt')
    while len(status()['terminal_slots'])<51:
        snapshot=status()
        if review_reached(snapshot, SEARCH):break
        if (SEARCH/'pause-request.json').exists():break
        durations=[v['seconds'] for v in manifest.get('native_batches',[]) if v['returncode']==0]
        forecast=max(full_panel_admission_seconds,max(durations[-5:],default=0.)*1.25)
        if time.time()+forecast>deadline:
            manifest['admission_pause']={'reason':'Remaining window cannot accommodate full native bounded retries/roles, frozen evaluation and checkpoint',
                'required_seconds':forecast,'remaining_seconds':max(0.,deadline-time.time()),'recorded_at':time.time()}
            break
        manifest.pop('admission_pause',None)
        snapshot=status();target=min(51,max(snapshot['terminal_slots'] or [-1])+2)
        if target-1>review_target(SEARCH):raise RuntimeError('Cannot admit beyond operational review target')
        env=os.environ.copy();env['PAPER_CONTROLLER_LOCK_FD']=str(lock.fileno());env['SHINKA_HEADLESS_TIMEOUT']=str(operations['per_request_seconds']);env['PAPER_SESSION_DEADLINE']=str(deadline)
        log=SEARCH/'session-logs'/f'{target:03d}-{time.time_ns()}.log';log.parent.mkdir(parents=True,exist_ok=True)
        started=time.time()
        with log.open('w') as output:
            p=subprocess.Popen([sys.executable,str(Path(__file__)),'_batch','--target',str(target)],cwd=ROOT,env=env,stdout=output,stderr=subprocess.STDOUT,pass_fds=(lock.fileno(),))
            manifest['active_batch']={'pid':p.pid,'target':target,'log':str(log.relative_to(ROOT))};atomic_json(MANIFEST,manifest)
            print(json.dumps(manifest['active_batch']),flush=True)
            code=p.wait() # Accepted evaluations drain; never kill one to satisfy a checkpoint clock.
        manifest.pop('active_batch',None);manifest.setdefault('native_batches',[]).append({'target':target,'returncode':code,'seconds':time.time()-started,'log':str(log.relative_to(ROOT))})
        checkpoint(manifest,'discovery_paused')
        if code:break
    checkpoint(manifest,'discovery_complete' if len(status()['terminal_slots'])==51 else 'discovery_paused')


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['status','benchmark','reference','resume','publish','_batch']);p.add_argument('--session-minutes',type=float,default=30);p.add_argument('--workers',type=int,default=1);p.add_argument('--reference-method',default='all');p.add_argument('--target',type=int)
    p.add_argument('--refresh-report',action='store_true',help='With publish, rebuild analysis from cached reference trajectories under the campaign lock; runs no simulations')
    p.add_argument('--review-target',type=int,help='Explicitly set an operational review generation; the frozen ceiling remains 50')
    args=p.parse_args()
    if args.review_target is not None and args.action!='resume':p.error('--review-target requires resume')
    if args.refresh_report and args.action!='publish':p.error('--refresh-report is only valid with publish')
    if args.action=='status':print(json.dumps(status(),indent=2));return 0
    if args.action=='_batch':return batch(args.target)
    if args.session_minutes<=0 or not 1<=args.workers<=4:raise ValueError('Positive bounded session and1..4 workers required')
    deadline=time.time()+args.session_minutes*60
    manifest=read(MANIFEST);active=manifest.get('active_batch',{})
    if active.get('pid') and Path('/proc/'+str(active['pid'])+'/cmdline').exists():raise RuntimeError('A native batch is still running; inspect it before maintenance')
    with (ROOT/'campaigns'/(CAMPAIGN+'.lock')).open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);verify_resume(manifest)
        lock.seek(0);lock.truncate();lock.write(str(os.getpid())+'\n');lock.flush()
        if args.review_target is not None:set_review_target(args.review_target, SEARCH)
        if args.action in ['benchmark','reference']:references(args,deadline,manifest)
        elif args.action=='resume':
            if not manifest.get('discovery_frozen') and manifest.get('reference_execution_deferred'):
                raise RuntimeError('Reference admissions deferred by user; finish finite discovery readiness and seed evaluation before resume')
            elif not manifest.get('discovery_frozen'):references(args,deadline,manifest)
            else:discovery(args,deadline,manifest,lock)
        else:
            # Publication is a coherent report/index boundary, not merely an
            # accounting refresh. The report may truthfully remain incomplete.
            if args.refresh_report:
                from paper_trajectory_v2.analysis import generate_report
                generate_report(RESULTS/'reference-index.json',RESULTS/'reference-report')
            from scripts.verify_paper_checkpoint import publication_inventory
            manifest['reference_report']=publication_inventory(ROOT,deferred_reference=manifest.get('reference_execution_deferred',False))
            checkpoint(manifest,'paused_clean')
    return 0

if __name__=='__main__':raise SystemExit(main())
