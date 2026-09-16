"""Close one new sprint archive using the existing byte/SQLite publication helpers.
Run from the repository root after all numerical stages and audits have finished.
"""
from pathlib import Path
import datetime
import json
import sys

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'src'))
from archive_joint_v3 import exclusion_reason, copy_bytes, backup_database, file_digest
from adaptive_swarms.logging import atomic_json, EventLogger

run = ROOT / 'results/radius_velocity_sprint/20260916T113359Z'
target = ROOT / 'artifacts/radius_velocity_sprint/20260916T113359Z'
if target.exists():
    raise FileExistsError('An existing archive is never overwritten.')
accounting = json.loads((run / 'accounting.json').read_text())
assert accounting['status'] == 'research_complete'
assert accounting['totals']['objective_queries'] == 16000000
assert json.loads((run / 'pilot/execution_ledger.json').read_text())['status'] == 'completed'
assert json.loads((run / 'evolution/search_seed_620001/manifest.json').read_text())['status'] == 'search_complete'
assert json.loads((run / 'operations/pilot-analysis-review.json').read_text())
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
with EventLogger(run / 'operations') as log:
    log.event('archive_started', destination=str(target), research_complete=True)
target.mkdir(parents=True)
entries, skipped = {}, []
for path in sorted(run.rglob('*')):
    if not path.is_file() and not path.is_symlink():
        continue
    relative = path.relative_to(run)
    reason = exclusion_reason(relative)
    if reason:
        skipped.append({'path': str(relative), 'reason': reason})
        continue
    destination = target / relative
    if path.suffix in {'.sqlite', '.sqlite3', '.db'}:
        record = backup_database(path, destination)
    else:
        # Only operational outputs may append while their bounded prefix is copied.
        operational = relative.parts[0] == 'operations' and path.suffix in {'.log', '.jsonl'}
        record = copy_bytes(path, destination, operational_snapshot=operational)
    entries[str(relative)] = record
archive = {'schema': 'radius-velocity-sprint-archive-v1', 'status': 'closed_complete',
           'source_run': str(run), 'archive_started_at': started,
           'archive_completed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'source_implementation_commit': '9a909f209030aa80144a385baf58123879357437',
           'research_queries': 16000000, 'separate_fixture_queries': 14000,
           'archived_case_records': 168, 'new_full_case_executions': 160,
           'model_logical_responses': 45, 'entries': entries, 'excluded': skipped,
           'integrity': 'Scientific files byte-identical; SQLite backup schema/all table rows verified; operational logs explicitly bounded prefixes.',
           'privacy': 'No credentials, raw authentication files, dependency caches, model weights or copyrighted book included.',
           'historical_preservation': 'operations/historical-preservation-check.json',
           'publication_note': 'Remote verification occurs after closing this immutable research archive and is recorded in the local operations directory and completion response.'}
atomic_json(target / 'ARCHIVE.json', archive)
manifest = [{'path': str(path.relative_to(target)), 'bytes': path.stat().st_size, 'sha256': file_digest(path)}
            for path in sorted(target.rglob('*')) if path.is_file() and path.name != 'MANIFEST.json']
atomic_json(target / 'MANIFEST.json', manifest)
with EventLogger(run / 'operations') as log:
    log.event('archive_complete', destination=str(target), files=len(manifest), bytes=sum(row['bytes'] for row in manifest), excluded=len(skipped))
print(json.dumps({'archive': str(target), 'files': len(manifest), 'bytes': sum(row['bytes'] for row in manifest), 'excluded': len(skipped)}, indent=2))
