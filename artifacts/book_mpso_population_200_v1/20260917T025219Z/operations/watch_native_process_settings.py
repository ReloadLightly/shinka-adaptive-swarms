"""Read-only observer for this one bounded study; no model requests."""
from pathlib import Path
from datetime import datetime, timezone
import json,runpy,time,traceback
study=Path(__file__).resolve().parent.parent
run=study/'evolution/search_seed_660001'
deadline=datetime.fromisoformat(json.loads((study/'session.json').read_text())['deadline_utc'])
script=study/'operations/observe_native_process_settings.py'
while datetime.now(timezone.utc)<deadline:
    if (run/'manifest.json').exists():
        try:
            runpy.run_path(str(script),run_name='__main__')
            state=json.loads((run/'manifest.json').read_text())
            if state.get('status') in {'search_complete','failed','blocked','sprint_limit_reached','blocked_runtime','blocked_embedding'}:
                print(json.dumps({'at':datetime.now(timezone.utc).isoformat(),'observer_finished':state['status']}),flush=True)
                break
        except Exception as exc:
            print(json.dumps({'at':datetime.now(timezone.utc).isoformat(),'observer_error':str(exc)}),flush=True)
    time.sleep(5)
