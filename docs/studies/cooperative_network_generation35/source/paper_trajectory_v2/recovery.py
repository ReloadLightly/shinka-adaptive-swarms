"""Evidence-bound recovery of one accepted evaluation; never propose another policy."""
from __future__ import annotations
import fcntl
import json
import math
import os
from pathlib import Path
import pickle
import shutil
import time

from cooperative.native import atomic_json,terminal_failures
from paper_trajectory_v2.design import canonical,sha
from scripts.campaign_state import database_fingerprint

SCHEMA='paper-accepted-evaluation-recovery-v1'


def digest(path):return sha(Path(path).read_bytes())
def read(path):return json.loads(Path(path).read_text())


def _sync_directory(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def _journal(path,payload):
    atomic_json(path,payload)
    with Path(path).open('rb') as stream:os.fsync(stream.fileno())
    _sync_directory(Path(path).parent)


def require_lock(root,fd):
    lock=Path(root)/'campaigns/paper_trajectory_v2.lock'
    actual=os.fstat(fd);expected=lock.stat()
    if (actual.st_dev,actual.st_ino)!=(expected.st_dev,expected.st_ino):raise RuntimeError('Wrong recovery campaign lock descriptor')
    fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)


def assert_no_active_work(root,search):
    import psutil
    root=Path(root);search=Path(search)
    needles=[str(search),str(root/'paper_trajectory_v2/evaluate.py'),str(root/'build/paper-classes')]
    for process in psutil.process_iter(['pid','cmdline','uids']):
        if process.pid==os.getpid():continue
        try:
            command=process.info['cmdline'] or []
            if any(needle in arg for needle in needles for arg in command):
                raise RuntimeError(f'Campaign work still active at PID {process.pid}; recovery refused')
        except (psutil.NoSuchProcess,psutil.ZombieProcess):continue
        except psutil.AccessDenied:
            if process.uids().real==os.getuid():raise RuntimeError('Cannot verify an owned process is inactive')


def _relative(root,value):
    path=Path(root)/value
    if Path(value).is_absolute() or not path.resolve().is_relative_to(Path(root).resolve()):raise RuntimeError('Recovery evidence must be repository-relative')
    return path


def _state(search):
    identity=read(search/'native-task-identity.json')
    with (search/'bandit_state.pkl').open('rb') as stream:bandit=pickle.load(stream)
    memory=read(search/'native_memory/state.json')
    from paper_trajectory_v2.native import configuration_hash
    identity_hash=configuration_hash(identity)
    if (identity.get('campaign_id')!='paper_trajectory_v2'
        or bandit.get('campaign_extension',{}).get('identity_sha256')!=identity_hash
        or memory.get('campaign_identity_sha256')!=identity_hash
        or memory.get('_continuity',{}).get('operation')):
        raise RuntimeError('Native identity or memory operation is inconsistent; recovery refused')
    return identity,bandit,memory


def verify_request(root,search,contract,resolution,lock_fd):
    """Read-only validation; caller must separately verify the full contract gate."""
    root,search=Path(root),Path(search);require_lock(root,lock_fd);assert_no_active_work(root,search)
    if (search/'recovery-pending.json').exists():raise RuntimeError('A recovery journal already exists; inspect its phase before any new admission')
    if (search/'subscription-pause.json').exists():raise RuntimeError('Subscription pause remains unresolved; evaluation recovery cannot waive it')
    if resolution.get('schema')!='paper-evaluation-recovery-resolution-v1' or resolution.get('campaign_id')!='paper_trajectory_v2':
        raise RuntimeError('Explicit campaign recovery resolution required')
    if resolution.get('resolved') is not True or not resolution.get('resolved_cause') or not resolution.get('resolution') or not resolution.get('evidence'):
        raise RuntimeError('Unknown/unresolved cause; an evidence-bound operator resolution is required')
    for relative,expected in resolution['evidence'].items():
        if digest(_relative(root,relative))!=expected:raise RuntimeError('Resolution evidence changed: '+relative)
    population=database_fingerprint(search/'programs.sqlite');records={r['id']:r for r in population['records']}
    terminal=set(population['generations'])|terminal_failures(search)
    pending=[]
    for folder in search.glob('gen_*'):
        if not folder.name[4:].isdigit():continue
        generation=int(folder.name[4:])
        if generation not in terminal and (folder/'accepted-job.json').exists():pending.append((generation,folder))
        elif generation not in terminal and generation>0:raise RuntimeError('Another unresolved proposal exists; recovery is not a generic retry')
    if len(pending)!=1:raise RuntimeError('Recovery requires exactly one pending accepted generation')
    generation,folder=pending[0]
    if generation!=max(terminal,default=-1)+1 or not 1<=generation<=50:raise RuntimeError('Accepted generation is not the next slot within the fixed budget')
    job=read(folder/'accepted-job.json');source=folder/'main.java';candidate=digest(source)
    if job.get('generation')!=generation or job.get('candidate_sha256')!=candidate:raise RuntimeError('Accepted source or generation changed')
    lineage=[job.get('parent_id'),*job.get('archive_insp_ids',[]),*job.get('top_k_insp_ids',[])]
    if any(pid not in records or records[pid]['generation']>=generation for pid in lineage):raise RuntimeError('Accepted lineage is missing or newer than the proposal')
    identity,bandit,memory=_state(search)
    if identity.get('scientific_identity')!=contract['identity_sha256']:raise RuntimeError('Accepted native state identifies another scientific contract')
    arm=job.get('meta_patch_data',{}).get('model_name')
    if arm not in bandit['arm_names']:raise RuntimeError('Accepted proposal has no exact saved native arm')
    pause=search/'infrastructure-pause.json';marker=folder/'results/evaluation-interrupted.json'
    expected={'generation':generation,'candidate_sha256':candidate,'accepted_job_sha256':digest(folder/'accepted-job.json'),
        'native_identity_sha256':digest(search/'native-task-identity.json'),'scientific_identity':contract['identity_sha256'],
        'pause_sha256':digest(pause),'interruption_sha256':digest(marker),'population_records_sha256':population['records_sha256']}
    if any(resolution.get(key)!=value for key,value in expected.items()):raise RuntimeError('Resolution does not identify this exact paused source/lineage/state')
    if resolution.get('recorded_pause_reason')!=read(pause).get('reason'):raise RuntimeError('Resolution names a different recorded pause cause')
    panel=read(_relative(root,contract['development_cases_path']));cache={}
    for case in panel:
        case_identity={'schema':'paper-trajectory-case-v1','engine_sha256':contract['engine_sha256'],'program_sha256':candidate,'case':case}
        key=sha(canonical(case_identity));path=search.parent/'cache'/key[:2]/(key+'.json')
        if not path.exists():continue
        receipt=read(path)
        if receipt.get('identity')!=case_identity or receipt.get('cache_key')!=key or receipt.get('case_id')!=case['case_id']:
            raise RuntimeError('Saved exact-case receipt has a foreign identity')
        if not isinstance(receipt.get('terminal_mean_utility'),(int,float)) or not math.isfinite(receipt['terminal_mean_utility']):raise RuntimeError('Nonfinite cached evaluation')
        trajectory=_relative(root,receipt['trajectory_path'])
        if digest(trajectory)!=receipt['trajectory_sha256']:raise RuntimeError('Saved exact-case trajectory changed')
        cache[str(path.relative_to(root))]=digest(path);cache[receipt['trajectory_path']]=receipt['trajectory_sha256']
    claimed=read(marker).get('completed_case_cache_keys',[])
    if any(not any(Path(path).name==key+'.json' for path in cache) for key in claimed):raise RuntimeError('Interrupted evaluation claims a missing exact-case cache')
    native_paths=[search/'native-task-identity.json',search/'bandit_state.pkl',search/'native_memory/state.json']
    native_paths += [p for p in [search/'prompts.sqlite',search/'prompts.sqlite-wal',search/'native_memory/native-meta-export.json'] if p.exists()]
    native_files={str(path.relative_to(search)):digest(path) for path in native_paths}
    return {**expected,'schema':SCHEMA,'target':generation+1,'parent_id':job['parent_id'],'lineage_program_ids':lineage,
        'native_files_sha256':native_files,'exact_case_files_sha256':cache,'bandit_submitted':list(bandit['n_submitted']),
        'accepted_arm':arm,'bandit_arm_names':list(bandit['arm_names']),'bandit_completed':list(bandit['n_completed']),'rewarded_program_ids':bandit['campaign_extension']['rewarded_program_ids'],
        'population_records_before':population['records'],'original_results_files_sha256':{str(p.relative_to(folder/'results')):digest(p) for p in sorted((folder/'results').rglob('*')) if p.is_file()},
        'resolution':resolution,'resolution_sha256':sha(canonical(resolution)),'created_at':time.time()}


def prepare(root,search,contract,resolution,lock_fd,deadline):
    """Journal before archival. A crash leaves ordinary resume blocked, never reset."""
    root,search=Path(root),Path(search);record=verify_request(root,search,contract,resolution,lock_fd)
    from paper_trajectory_v2.evaluate import evaluation_admission_seconds
    if time.time()+evaluation_admission_seconds(contract)>deadline:raise RuntimeError('Insufficient session allowance to drain this full accepted evaluation')
    record.update(deadline=deadline,phase='archiving')
    record['recovery_id']=sha(canonical(record));archive=search/'recoveries'/record['recovery_id']
    record['archive_path']=str(archive.relative_to(root));_journal(search/'recovery-pending.json',record)
    archive.mkdir(parents=True,exist_ok=False)
    _journal(archive/'plan.json',record)
    atomic_json(archive/'resolution.json',resolution)
    folder=search/f"gen_{record['generation']}"
    shutil.copyfile(folder/'accepted-job.json',archive/'accepted-job.json');shutil.copyfile(folder/'main.java',archive/'main.java')
    for relative in record['native_files_sha256']:
        destination=archive/'native-before'/relative;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(search/relative,destination)
    (folder/'results').rename(archive/'original-results')
    (search/'infrastructure-pause.json').rename(archive/'original-pause.json')
    for directory in (archive,folder,search):_sync_directory(directory)
    record['phase']='prepared';_journal(search/'recovery-pending.json',record)
    return record


def permit(root,search,recovery_id,lock_fd,*,program=None,results=None,target=None,evaluator_child=False):
    """Validate a prepared/running permit; never authorize a new proposal."""
    root,search=Path(root),Path(search)
    record=read(search/'recovery-pending.json')
    if evaluator_child:
        _require_worker_parent(root,record)
    else:require_lock(root,lock_fd)
    if record.get('schema')!=SCHEMA or record.get('recovery_id')!=recovery_id or record.get('phase') not in ('prepared','running'):
        raise RuntimeError('Recovery is unprepared, foreign or already finished')
    if time.time()>=record['deadline']:raise RuntimeError('Recovery session deadline expired')
    folder=search/f"gen_{record['generation']}";archive=_relative(root,record['archive_path'])
    plan=read(archive/'plan.json');base=dict(plan);base.pop('recovery_id');base.pop('archive_path')
    if sha(canonical(base))!=recovery_id or any(record.get(k)!=v for k,v in plan.items() if k!='phase'):
        raise RuntimeError('Recovery journal differs from its immutable evidence plan')
    if target is not None and target!=record['target']:raise RuntimeError('Recovery target must be exactly accepted generation + 1')
    if program is not None and Path(program).resolve()!=(folder/'main.java').resolve():raise RuntimeError('Recovery cannot evaluate another source')
    if results is not None and Path(results).resolve()!=(folder/'results').resolve():raise RuntimeError('Recovery result path changed')
    for path,key in [(folder/'main.java','candidate_sha256'),(folder/'accepted-job.json','accepted_job_sha256'),(search/'native-task-identity.json','native_identity_sha256')]:
        if digest(path)!=record[key]:raise RuntimeError('Recovery source/accepted/native identity changed')
    if digest(archive/'original-pause.json')!=record['pause_sha256'] or digest(archive/'original-results/evaluation-interrupted.json')!=record['interruption_sha256']:
        raise RuntimeError('Archived recovery evidence changed')
    for relative,expected in record['original_results_files_sha256'].items():
        if digest(archive/'original-results'/relative)!=expected:raise RuntimeError('Original evaluation evidence changed')
    for relative,expected in record['exact_case_files_sha256'].items():
        if digest(_relative(root,relative))!=expected:raise RuntimeError('Previously completed exact-case cache changed')
    if (search/'infrastructure-pause.json').exists():raise RuntimeError('Recovery encountered a new infrastructure interruption; new explicit resolution required')
    return record


def _process_start_identity(pid):
    """Linux process identity unaffected by wall-clock/boot-time adjustments."""
    boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    # comm may contain spaces or parentheses; fields after its final ')' begin
    # with field3 (state), so field22 (starttime) has index19 here.
    fields=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
    start_ticks=int(fields[19])
    if not boot_id or start_ticks<=0:raise RuntimeError('Stable process identity unavailable')
    return boot_id,start_ticks


def begin_worker(root,search,recovery_id,lock_fd):
    import psutil
    record=permit(root,search,recovery_id,lock_fd)
    if record['phase']!='prepared':raise RuntimeError('A previous recovery worker may have changed state; inspect rather than replay')
    for relative,expected in record['native_files_sha256'].items():
        if digest(Path(search)/relative)!=expected:raise RuntimeError('Native state changed before recovery admission')
    boot_id,start_ticks=_process_start_identity(os.getpid())
    record.update(phase='running',worker_pid=os.getpid(),worker_created_at=psutil.Process().create_time(),
                  worker_boot_id=boot_id,worker_start_ticks=start_ticks,lock_fd=lock_fd)
    _journal(Path(search)/'recovery-pending.json',record)
    return record


def _require_worker_parent(root,record):
    # The pinned local scheduler closes inherited descriptors in its evaluator.
    # The evaluator must therefore be the direct child of this exact live,
    # lock-owning native worker, not merely possess a copied environment token.
    import psutil
    if record.get('phase')!='running' or os.getppid()!=record.get('worker_pid'):
        raise RuntimeError('Recovery evaluator is not a child of its admitted native worker')
    if (not isinstance(record.get('worker_boot_id'),str) or not record['worker_boot_id']
        or type(record.get('worker_start_ticks')) is not int or record['worker_start_ticks']<=0):
        raise RuntimeError('Recovery worker lacks stable process identity; explicit reconciliation required')
    parent=psutil.Process(record['worker_pid'])
    if (parent.uids().real!=os.getuid()
        or _process_start_identity(parent.pid)!=(record['worker_boot_id'],record['worker_start_ticks'])):
        raise RuntimeError('Recovery worker identity changed')
    expected=(Path(root)/'campaigns/paper_trajectory_v2.lock').stat()
    actual=Path(f"/proc/{parent.pid}/fd/{record['lock_fd']}").stat()
    if (expected.st_dev,expected.st_ino)!=(actual.st_dev,actual.st_ino):raise RuntimeError('Recovery worker no longer retains the campaign lock')
    with (Path(root)/'campaigns/paper_trajectory_v2.lock').open('a+') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return
        raise RuntimeError('Campaign lock is not held by the recovery worker')


def evaluation_permit(root,search,program,results):
    if not (Path(search)/'recovery-pending.json').exists():return False
    token=os.environ.get('PAPER_RECOVERY_ID')
    if not token:raise RuntimeError('Ordinary evaluation cannot consume a recovery-pending slot')
    permit(root,search,token,None,program=program,results=results,evaluator_child=True)
    return True


def finish(root,search,recovery_id,lock_fd):
    root,search=Path(root),Path(search);record=permit(root,search,recovery_id,lock_fd)
    population=database_fingerprint(search/'programs.sqlite')
    rows=[r for r in population['records'] if r['generation']==record['generation'] and not r.get('administrative_copy')]
    if len(rows)!=1 or rows[0]['candidate_sha256']!=record['candidate_sha256'] or rows[0]['parent_id']!=record['parent_id']:
        raise RuntimeError('Recovery did not persist exactly the accepted source and lineage; journal retained')
    from scripts.campaign_state import compatible_subset
    compatible_subset(record['population_records_before'],population['records'],'pre-recovery population')
    if any(r['generation']>record['generation'] for r in population['records']):raise RuntimeError('Recovery admitted a later generation')
    identity,bandit,memory=_state(search)
    expected_completed=list(record['bandit_completed']);expected_completed[record['bandit_arm_names'].index(record['accepted_arm'])]+=1
    if (list(bandit['n_submitted'])!=record['bandit_submitted']
        or list(bandit['arm_names'])!=record['bandit_arm_names']
        or list(bandit['n_completed'])!=expected_completed
        or set(bandit['campaign_extension']['rewarded_program_ids'])!=set(record['rewarded_program_ids'])|{rows[0]['id']}):
        raise RuntimeError('Recovery pull/reward accounting differs; journal retained for inspection')
    record.update(phase='completed',completed_at=time.time(),recovered_program_id=rows[0]['id'],population_records_sha256_after=population['records_sha256'])
    archive=_relative(root,record['archive_path']);atomic_json(archive/'completion.json',record)
    (search/'recovery-pending.json').rename(archive/'recovery-journal.json')
    return record
