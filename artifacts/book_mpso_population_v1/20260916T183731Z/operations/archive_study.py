"""Close this bounded study using the existing publication copy/SQLite helpers."""
from pathlib import Path
from datetime import datetime, timezone
import json
import sys

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'src')]
from archive_joint_v3 import exclusion_reason, copy_bytes, backup_database, file_digest
from adaptive_swarms.logging import atomic_json, EventLogger

run = ROOT / 'results/book_mpso_population_v1/20260916T183731Z'
target = ROOT / 'artifacts/book_mpso_population_v1/20260916T183731Z'
accounting = json.loads((run / 'accounting.json').read_text())
assert accounting['status'] == 'research_complete'
assert accounting['totals']['physical_full_executions'] <= 96
assert accounting['totals']['research_objective_queries'] <= 48000000
assert accounting['model']['requested_logical_responses'] <= 36
assert json.loads((run / 'operations/native-inspection-final.json').read_text())['status'] == 'completed'
assert json.loads((run / 'operations/final-scientific-review.json').read_text())['status'] == 'passed'
if target.exists():
    raise FileExistsError('An existing archive is never overwritten.')
started = datetime.now(timezone.utc).isoformat()
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
        operational = relative.parts[0] == 'operations' and path.suffix in {'.log', '.jsonl'}
        record = copy_bytes(path, destination, operational_snapshot=operational)
    entries[str(relative)] = record
atomic_json(target / 'ARCHIVE.json', {
    'schema': 'book-mpso-population-archive-v1', 'status': 'closed_complete',
    'source_run': str(run), 'archive_started_at': started,
    'archive_completed_at': datetime.now(timezone.utc).isoformat(),
    'prospective_task_commit': 'aa89058e07cc301ff75c3c887b3a0588a685370b',
    'prospective_analysis_context_commit': 'aa89058e07cc301ff75c3c887b3a0588a685370b',
    'accounting': accounting, 'entries': entries, 'excluded': skipped,
    'integrity': 'Scientific files byte-identical; SQLite backup schema/all table rows verified; operational logs explicitly bounded prefixes.',
    'privacy': 'No credentials, authentication files, dependency caches, model weights or copyrighted book.',
    'historical_preservation': 'operations/historical-preservation-check.json',
    'publication_note': 'Remote verification follows archive closure and is recorded locally and in the completion response.'})
manifest = [{'path': str(path.relative_to(target)), 'bytes': path.stat().st_size, 'sha256': file_digest(path)}
            for path in sorted(target.rglob('*')) if path.is_file() and path.name != 'MANIFEST.json']
atomic_json(target / 'MANIFEST.json', manifest)
with EventLogger(run / 'operations') as log:
    log.event('archive_complete', destination=str(target), files=len(manifest), bytes=sum(row['bytes'] for row in manifest), excluded=len(skipped))
print(json.dumps({'archive': str(target), 'files': len(manifest), 'bytes': sum(row['bytes'] for row in manifest), 'excluded': len(skipped)}, indent=2))
