"""Read-only active-process evidence; never reads environment or authentication."""
from pathlib import Path
from datetime import datetime, timezone
import json
import hashlib
import psutil

study = Path(__file__).resolve().parent.parent
run = study / 'evolution/search_seed_650001'
path = study / 'operations/native-codex-process-settings-observed.json'
record = json.loads(path.read_text()) if path.exists() else {'observations': [], 'scope': 'Local process arguments only, no authentication/environment files. Provider execution settings beyond visible CLI are not independently attested.'}
receipts=[]
raw_receipts=[]
for source in (run/'engine_calls').glob('*.json'):
    item=json.loads(source.read_text())
    raw_receipts.append(item)
    if item['status']=='started':
        receipts.append({'call_id':item['call_id'],'role':item['role'],'started_at':item['started_at'],'configured_models':item['configured_models']})
observations=[]
for process in psutil.process_iter(['pid','ppid','name','cmdline','create_time']):
    try:
        args=process.info['cmdline'] or []
        if not args or not any(Path(arg).name in {'codex','codex.js'} for arg in args[:2]): continue
        if 'exec' not in args: continue
        parents=process.parents()
        # Tie the process to this exact run using its launcher ancestry.
        if not any(str(run) in ' '.join(p.cmdline()) for p in parents): continue
        prompt_paths=[]
        for parent in parents:
            parent_args=parent.cmdline()
            if '--prompt-file' in parent_args:
                candidate=Path(parent_args[parent_args.index('--prompt-file')+1])
                if candidate.is_relative_to(run) and candidate.is_file():prompt_paths.append(candidate)
        prompt_evidence=[]
        for prompt in dict.fromkeys(prompt_paths):
            content=prompt.read_text()
            matched=[]
            for receipt in raw_receipts:
                messages=receipt.get('msg')
                messages=messages if isinstance(messages,list) else [messages]
                system=receipt.get('system_msg')
                if isinstance(system,str) and system in content and any(isinstance(m,str) and m in content for m in messages):
                    matched.append({'call_id':receipt['call_id'],'role':receipt['role']})
            prompt_evidence.append({'path':str(prompt),'sha256':hashlib.sha256(content.encode()).hexdigest(),'exact_system_and_user_message_matches':matched})
        settings=[]
        for i,arg in enumerate(args[:-1]):
            if arg in {'--model','-m'}: settings.append([arg,args[i+1]])
            if arg in {'-c','--config'} and args[i+1].startswith(('model_reasoning_effort=','model=')):settings.append([arg,args[i+1]])
        item={'pid':process.pid,'parent_pid':process.ppid(),'started_at':datetime.fromtimestamp(process.info['create_time'],timezone.utc).isoformat(),
              'observed_at':datetime.now(timezone.utc).isoformat(),'visible_model_and_effort_arguments':settings,'active_native_receipts':receipts,'headless_prompt_evidence':prompt_evidence,
              'receipt_role_association':'Active receipt set at observation; concurrent batched meta subprocesses may share one receipt.'}
        previous=next((p for p in record['observations'] if p['pid']==item['pid'] and p['started_at']==item['started_at']),None)
        if previous is None:record['observations'].append(item)
        else:previous.update(item)
        observations.append(item)
    except (psutil.NoSuchProcess,psutil.AccessDenied):pass
record['last_inspected_at']=datetime.now(timezone.utc).isoformat()
record['model_requests_from_audit']=0
path.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'active_codex_processes':len(observations),'total_unique_process_observations':len(record['observations']),'roles':sorted({r['role'] for item in observations for r in item['active_native_receipts']})}))
