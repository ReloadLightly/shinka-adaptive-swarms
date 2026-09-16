"""Read-only evidence milestones for this one study; no research/model calls."""
from pathlib import Path
from datetime import datetime, timezone
import json, sqlite3, subprocess, sys, time
study=Path(__file__).resolve().parent.parent
run=study/'evolution/search_seed_650001'
root=study.parents[2]
deadline=datetime.fromisoformat(json.loads((study/'session.json').read_text())['deadline_utc'])
while datetime.now(timezone.utc)<deadline:
    manifest_path=run/'manifest.json'
    if not manifest_path.exists(): time.sleep(20);continue
    manifest=json.loads(manifest_path.read_text())
    with sqlite3.connect(f'file:{run}/programs.sqlite?mode=ro',uri=True) as db:
        descendants={row[0] for row in db.execute('select distinct generation from programs where generation>0')}
    if len(descendants)>=4 and not (study/'operations/native-inspection-4.json').exists():
        subprocess.run([sys.executable,str(study/'operations/audit_native_book.py'),'--run',str(run),'--label','4'],cwd=root,check=True)
    if manifest.get('status')=='search_complete':
        if not (study/'operations/native-inspection-final.json').exists():
            subprocess.run([sys.executable,str(study/'operations/audit_native_book.py'),'--run',str(run),'--label','final'],cwd=root,check=True)
        print(json.dumps({'at':datetime.now(timezone.utc).isoformat(),'completed':'final_native_audit','objective_queries':0,'model_calls':0}),flush=True)
        break
    time.sleep(20)
