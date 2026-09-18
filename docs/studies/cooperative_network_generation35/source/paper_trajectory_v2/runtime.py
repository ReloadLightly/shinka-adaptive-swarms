"""Exact-identity, resumable full-history execution; no model calls."""
from __future__ import annotations
import concurrent.futures
import gzip
import json
import lzma
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
import uuid
from cooperative.evaluate import java_binary, locked
from cooperative.native import atomic_json
from paper_trajectory_v2.design import ROOT, RESULTS, canonical, sha


def engine_identity():
    paths = sorted(list((ROOT/'java-paper').rglob('*.java')) + list((ROOT/'upstream/multiplex/Agents').glob('*.java')) + list((ROOT/'vendor').glob('*.jar')) + [ROOT/'scripts/build_paper_java.sh'])
    paths = [p for p in paths if 'policies' not in p.parts]
    return {str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in paths}

def engine_digest():
    return sha(canonical(engine_identity()))

def verify_reference_engine():
    """Refuse scientific drift against the explicitly registered reference freeze."""
    manifest_path=ROOT/'campaigns/paper_trajectory_v2.json'
    if not manifest_path.is_file():raise RuntimeError('Reference campaign manifest is missing')
    manifest=json.loads(manifest_path.read_text());registered=manifest.get('reference_engine')
    if not registered:raise RuntimeError('Reference engine/behavior freeze has not been registered')
    path=ROOT/registered['path']
    if not path.is_file() or sha(path.read_bytes())!=registered['sha256']:
        raise RuntimeError('Registered reference engine freeze changed; explicit versioned reconciliation required')
    frozen=json.loads(path.read_text());sources=engine_identity();digest=sha(canonical(sources))
    if (frozen.get('schema')!='paper-reference-engine-freeze-v1' or frozen.get('sources')!=sources
        or frozen.get('engine_sha256')!=digest or registered.get('engine_sha256')!=digest):
        raise RuntimeError('Frozen reference engine/source identity changed; refusing a new scientific identity')
    for stem in ['behavior_contract','build_verifier','engineering_checks']:
        artifact=ROOT/frozen[stem+'_path']
        if not artifact.is_file() or sha(artifact.read_bytes())!=frozen[stem+'_sha256']:
            raise RuntimeError('Frozen reference '+stem+' changed')
    for stem,filename in [('design','design.json'),('reference_cases','reference_cases.json')]:
        digest=sha((ROOT/'experiments/paper_trajectory_v2'/filename).read_bytes())
        if frozen.get(stem+'_sha256')!=digest or manifest.get(stem+'_sha256')!=digest:
            raise RuntimeError('Frozen reference scientific configuration changed: '+filename)
    if frozen.get('reference_program_sha256')!='reference:'+sha((ROOT/'java-paper/paper/ReferencePolicy.java').read_bytes()):
        raise RuntimeError('Frozen reference policy changed')
    return frozen

def verify_build_identity():
    """Bind executions to the actual compiled classes, not source hashes alone."""
    path=ROOT/'build/paper-build-identity.json'
    if not path.is_file():raise RuntimeError('Missing v2 Java build receipt; build and verify before numerical execution')
    receipt=json.loads(path.read_text());sources=engine_identity();frozen=verify_reference_engine()
    classes={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted((ROOT/'build/paper-classes').rglob('*.class'))}
    if (receipt.get('schema')!='paper-java-build-v1' or receipt.get('source_files')!=sources
        or receipt.get('engine_sha256')!=sha(canonical(sources)) or not classes or receipt.get('class_files')!=classes
        or frozen.get('compiled_class_files')!=classes):
        raise RuntimeError('V2 Java build/source/class identity mismatch; preserve evidence and rebuild before execution')
    return receipt

def append_ledger(data):
    RESULTS.mkdir(parents=True,exist_ok=True)
    with locked(RESULTS/'evaluation_usage.lock'):
        with (RESULTS/'evaluation_usage.jsonl').open('a') as f:
            f.write(json.dumps({'time':time.time(),**data},sort_keys=True,allow_nan=False)+'\n')
            f.flush();os.fsync(f.fileno())

def validate_policy(source):
    # Capability interface is the only simulator access. Compile/runtime failure is a
    # terminal invalid proposal, never an excuse to expand its information budget.
    code=re.sub(r'/\*.*?\*/|//[^\n]*','',source,flags=re.S)
    if not re.search(r'public\s+final\s+class\s+CandidatePolicy\s+implements\s+ActorPolicy',code):
        raise ValueError('Expected public final CandidatePolicy implements ActorPolicy')
    forbidden=r'\b(?:System|Runtime|ProcessBuilder|Thread|ClassLoader|Class|reflect|Unsafe|File|Files|Path|Paths|Socket|URL|Random|SecureRandom|agents|javax|sun)\b|\bjava\.(?!lang\.Math\b)|\bstatic\b|\bpackage\b|\bgetClass\b'
    if re.search(forbidden,code):
        raise ValueError('Policy attempted undeclared runtime access or shared static state')
    imports=re.findall(r'\bimport\s+([^;]+);',code)
    if any(not (x=='paper.*' or re.fullmatch(r'paper\.[A-Za-z]+',x)) for x in imports):
        raise ValueError('Only paper capability imports are permitted; use Math directly')
    return source

def compile_policy(path):
    from paper_trajectory_v2.policy_guard import guard_identity, validate_compiled
    build=verify_build_identity()
    path=Path(path);source=validate_policy(path.read_text());program=sha(source.encode())
    destination=RESULTS/'compiled'/program
    identity={'program_sha256':program,'engine_sha256':build['engine_sha256'],'compiled_guard_identity':guard_identity()}
    with locked(destination.with_suffix('.lock')):
        receipt=destination/'identity.json'
        if receipt.exists():
            saved=json.loads(receipt.read_text())
            if all(saved.get(k)==v for k,v in identity.items()):
                classes={str(p.relative_to(destination)):sha(p.read_bytes()) for p in sorted(destination.rglob('*.class'))}
                if not classes or saved.get('class_files')!=classes:raise RuntimeError('Compiled candidate classes differ from their cache identity')
                checked=validate_compiled(destination)
                if checked!=saved.get('compiled_guard_receipt'):raise RuntimeError('Compiled policy guard receipt changed')
                return destination,program
        destination.mkdir(parents=True,exist_ok=True)
        local=destination/'CandidatePolicy.java';local.write_text(source)
        proc=subprocess.run([java_binary('javac'),'-proc:none','--release','17','-cp',str(ROOT/'build/paper-classes')+':'+str(ROOT/'vendor/mason.20.jar'),'-d',str(destination),str(local)],capture_output=True,text=True,timeout=45)
        (destination/'compile.log').write_text(proc.stdout+proc.stderr)
        if proc.returncode:raise ValueError('Candidate compilation failed: '+proc.stderr[-4000:])
        if verify_build_identity()!=build:raise RuntimeError('Java build changed while compiling the candidate')
        identity['class_files']={str(p.relative_to(destination)):sha(p.read_bytes()) for p in sorted(destination.rglob('*.class'))}
        identity['compiled_guard_receipt']=validate_compiled(destination)
        atomic_json(receipt,identity)
    return destination,program

def load_trajectory(receipt):
    path=ROOT/receipt['trajectory_path']
    opener=lzma.open if path.suffix=='.xz' else gzip.open if path.suffix=='.gz' else None
    if opener is None:raise RuntimeError('Unknown saved trajectory encoding: '+str(path))
    with opener(path,'rt') as f:return json.load(f)

def run_case(case, policy_path=None, *, role='reference', timeout=300):
    verify_reference_engine()
    if policy_path is None:
        program='reference:'+sha((ROOT/'java-paper/paper/ReferencePolicy.java').read_bytes())
        classpath=str(ROOT/'build/paper-classes')+':'+str(ROOT/'vendor/mason.20.jar')
        policy='paper.ReferencePolicy'
    else:
        classes,program=compile_policy(policy_path)
        classpath=str(classes)+':'+str(ROOT/'build/paper-classes')+':'+str(ROOT/'vendor/mason.20.jar')
        policy='CandidatePolicy'
    identity={'schema':'paper-trajectory-case-v1','engine_sha256':engine_digest(),'program_sha256':program,'case':case}
    key=sha(canonical(identity));base=RESULTS/'cache'/key[:2]/key
    with locked(base.with_suffix('.lock')):
        receipt_path=base.with_suffix('.json')
        if receipt_path.exists():
            receipt=json.loads(receipt_path.read_text())
            if receipt['identity']!=identity:raise RuntimeError('Case identity collision')
            trajectory=ROOT/receipt['trajectory_path']
            if not trajectory.exists() or sha(trajectory.read_bytes())!=receipt['trajectory_sha256']:
                raise RuntimeError('Completed trajectory hash mismatch; preserve evidence')
            append_ledger({'kind':'cache_reuse','role':role,'case_id':case['case_id'],'cache_key':key})
            return receipt
        base.parent.mkdir(parents=True,exist_ok=True)
        build=verify_build_identity()
        if build['engine_sha256']!=identity['engine_sha256']:raise RuntimeError('Engine changed before numerical execution')
        started=time.monotonic()
        with tempfile.TemporaryDirectory(prefix='paper-case-',dir='/tmp') as temp:
            inp=Path(temp)/'case.json';out=Path(temp)/'trajectory.json'
            inp.write_bytes(canonical(case))
            try:
                proc=subprocess.run([java_binary('java'),'-Xmx384m','-XX:ActiveProcessorCount=1','-cp',classpath,'agents.PaperRunner',str(inp),str(out),policy],capture_output=True,text=True,timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                elapsed=time.monotonic()-started
                atomic_json(RESULTS/'failures'/(key+'-'+uuid.uuid4().hex+'.json'),{'identity':identity,'error':'Numerical trajectory exceeded its declared timeout','timeout_seconds':timeout,'elapsed_seconds':elapsed})
                append_ledger({'kind':'numerical_case','completed':False,'role':role,'case_id':case['case_id'],'cache_key':key,'elapsed_seconds':elapsed,'reason':'timeout'})
                raise RuntimeError('Numerical trajectory timed out; preserve evidence and inspect before retry') from exc
            elapsed=time.monotonic()-started
            if proc.returncode or not out.exists():
                error=(proc.stdout+proc.stderr)[-6000:]
                atomic_json(RESULTS/'failures'/(key+'-'+uuid.uuid4().hex+'.json'),{'identity':identity,'error':error,'elapsed_seconds':elapsed})
                append_ledger({'kind':'numerical_case','completed':False,'role':role,'case_id':case['case_id'],'cache_key':key,'elapsed_seconds':elapsed})
                raise RuntimeError(error)
            try:
                if verify_build_identity()!=build:raise RuntimeError('Java build/source identity changed during numerical execution')
                data=json.loads(out.read_text());trajectory=data['trajectory']
                if (len(trajectory)!=case['horizon']+1 or [s['round'] for s in trajectory]!=list(range(case['horizon']+1))
                    or any(len(s['actors'])!=case['n'] or len({a['actor'] for a in s['actors']})!=case['n'] for s in trajectory)
                    or any(not math.isfinite(a['utility']) for s in trajectory for a in s['actors'])):
                    raise RuntimeError('Incomplete, duplicate-actor or nonfinite full trajectory')
            except Exception as exc:
                atomic_json(RESULTS/'failures'/(key+'-'+uuid.uuid4().hex+'.json'),{'identity':identity,'error':str(exc),'elapsed_seconds':elapsed})
                append_ledger({'kind':'numerical_case','completed':False,'role':role,'case_id':case['case_id'],'cache_key':key,'elapsed_seconds':elapsed,'reason':'output_or_build_validation'})
                raise
            compressed=base.with_suffix('.json.xz');temporary=compressed.with_suffix('.tmp')
            with lzma.open(temporary,'wb',preset=3) as f:f.write(canonical(data))
            temporary.replace(compressed)
            elapsed=time.monotonic()-started
            receipt={'cache_key':key,'identity':identity,'trajectory_path':str(compressed.relative_to(ROOT)),
                'trajectory_sha256':sha(compressed.read_bytes()),'elapsed_seconds':elapsed,'completed_at':time.time(),
                'role':role,'case_id':case['case_id'],'terminal_mean_utility':sum(a['utility'] for a in data['trajectory'][-1]['actors'])/case['n'],
                'pre_shock_mean_utility':sum(a['utility'] for a in data['trajectory'][case['shock_time']]['actors'])/case['n'],
                'usage':data.get('usage',{}),'timeout_seconds':timeout,'trajectory_encoding':'json+xz; preset=3'}
            atomic_json(receipt_path,receipt)
            append_ledger({'kind':'numerical_case','completed':True,'role':role,'case_id':case['case_id'],'cache_key':key,'elapsed_seconds':elapsed,'engine_sha256':identity['engine_sha256'],'program_sha256':program})
            return receipt

def run_panel(cases, *, deadline, workers=1, role='reference', policy_path=None, progress=None,
              stop_requested=None, timing_profile=None):
    """Admit bounded work and drain accepted histories. Completed exact cases survive restart."""
    receipts=[];pending={};iterator=iter(cases);exhausted=False;started=time.monotonic();failures=[]
    observed=dict(timing_profile or {})
    def method(c):return (c['n'],c['sampling'],c['interpretation'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        while pending or not exhausted:
            while not exhausted and len(pending)<workers:
                if (stop_requested and stop_requested()) or time.time()+5>deadline:
                    exhausted=True;break
                try:c=next(iterator)
                except StopIteration:exhausted=True;break
                # A documented operational timeout uses the measured method/N
                # maximum with a3x multiplier and10s startup margin, capped300s.
                # Unmeasured methods start at60s; timeout failures retain evidence.
                measured=observed.get(method(c))
                case_timeout=min(300.,max(30.,3*measured+10)) if measured is not None else 60.
                if (stop_requested and stop_requested()) or time.time()+case_timeout+5>deadline:
                    exhausted=True;break
                pending[pool.submit(run_case,c,policy_path,role=role,timeout=case_timeout)]=c
            if not pending:break
            done,_=concurrent.futures.wait(pending,return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                c=pending.pop(future)
                try:r=future.result()
                except Exception as exc:
                    failures.append(exc);exhausted=True
                    continue
                receipts.append(r)
                observed[method(c)]=max(observed.get(method(c),0.),r['elapsed_seconds'])
                if progress:progress(r,len(receipts),time.monotonic()-started)
    if failures:raise failures[0] # Every already accepted success was drained and indexed first.
    return receipts
