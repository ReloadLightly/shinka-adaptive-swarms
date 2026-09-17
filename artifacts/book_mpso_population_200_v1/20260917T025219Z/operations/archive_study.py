"""Close the runtime-bounded study without manufacturing a native database."""
from pathlib import Path
from datetime import datetime, timezone
import json, sys
ROOT=Path.cwd()
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'src')]
from archive_joint_v3 import exclusion_reason,copy_bytes,file_digest
from adaptive_swarms.logging import atomic_json,EventLogger
run=ROOT/'results/book_mpso_population_200_v1/20260917T025219Z'
target=ROOT/'artifacts/book_mpso_population_200_v1/20260917T025219Z'
accounting=json.loads((run/'accounting.json').read_text())
assert accounting['status']=='bounded_stop_before_search'
assert accounting['totals']['physical_full_executions']==1
assert accounting['totals']['research_objective_queries']==500000
assert accounting['model']['requested_logical_responses']==0
assert json.loads((run/'operations/saved-case-audit.json').read_text())['status']=='bounded_stop_saved_case_passed_unranked'
assert not (run/'evolution').exists()
if target.exists(): raise FileExistsError('Never overwrite an existing archive')
with EventLogger(run/'operations') as log:log.event('archive_started',destination=str(target),status='bounded_stop_before_search')
target.mkdir(parents=True)
entries,skipped={},[]
for path in sorted(run.rglob('*')):
 if not path.is_file():continue
 relative=path.relative_to(run);reason=exclusion_reason(relative)
 if reason:skipped.append({'path':str(relative),'reason':reason});continue
 assert path.suffix not in {'.sqlite','.db'},'No native database should exist'
 operational=relative.parts[0]=='operations' and path.suffix in {'.log','.jsonl'}
 entries[str(relative)]=copy_bytes(path,target/relative,operational_snapshot=operational)
atomic_json(target/'ARCHIVE.json',{'schema':'book-mpso-population-200-bounded-archive-v1','status':'closed_bounded_stop_before_search','archive_completed_at':datetime.now(timezone.utc).isoformat(),'source_run':str(run),'prospective_task_commit':'9c0c938','accounting':accounting,'entries':entries,'excluded':skipped,'interpretation':'One complete planned reference case; no paired reference comparison, native seed, descendant, fresh identities, selection or native model call. Missing planned records are unexecuted, not negative outcomes.','privacy':'No credentials, raw authentication files or copyrighted chapter','publication_note':'Remote verification follows archive closure in separate publication receipt.'})
manifest=[{'path':str(p.relative_to(target)),'bytes':p.stat().st_size,'sha256':file_digest(p)} for p in sorted(target.rglob('*')) if p.is_file() and p.name!='MANIFEST.json']
atomic_json(target/'MANIFEST.json',manifest)
with EventLogger(run/'operations') as log:log.event('archive_complete',files=len(manifest),bytes=sum(r['bytes'] for r in manifest),excluded=len(skipped))
