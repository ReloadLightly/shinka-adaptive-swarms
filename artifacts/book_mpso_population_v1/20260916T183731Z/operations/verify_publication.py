"""Read-only closed-archive and portable-analysis check; no research calls."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import sqlite3
import subprocess

ROOT = Path.cwd()
ARCHIVE = ROOT / 'artifacts/book_mpso_population_v1/20260916T183731Z'
OUT = ROOT / 'artifacts/book_mpso_population_v1_publication'
OUT.mkdir(parents=True, exist_ok=True)

def read(path): return json.loads(path.read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

manifest = read(ARCHIVE / 'MANIFEST.json')
failures = [r['path'] for r in manifest
            if (ARCHIVE/r['path']).stat().st_size != r['bytes']
            or sha(ARCHIVE/r['path']) != r['sha256']]
assert not failures, failures
database = ARCHIVE / 'evolution/search_seed_650001/programs.sqlite'
with sqlite3.connect(f'file:{database}?mode=ro', uri=True) as connection:
    integrity = connection.execute('PRAGMA integrity_check').fetchone()[0]
    rows = connection.execute('SELECT COUNT(*) FROM programs').fetchone()[0]
    slots = connection.execute('SELECT COUNT(DISTINCT generation) FROM programs').fetchone()[0]
assert integrity == 'ok'

selection = read(ARCHIVE / 'selection.json')
phases = ['development'] + (['fresh'] if selection['fresh_comparison_required'] else [])
analyses = {}
env = dict(os.environ, MPLCONFIGDIR='/tmp/book-population-publication-matplotlib')
for phase in phases:
    output = Path('/tmp') / f'book-population-portable-{phase}'
    command = [str(ROOT/'.venv/bin/python'), 'scripts/analyze_book_population.py',
               '--run', str(ARCHIVE), '--phase', phase, '--output', str(output)]
    process = subprocess.run(command, capture_output=True, text=True, env=env)
    (OUT/f'portable-{phase}.log').write_text(process.stdout+process.stderr)
    assert process.returncode == 0, process.stderr[-2000:]
    original = read(ARCHIVE/f'analysis/{phase}/analysis.json')
    restored = read(output/'analysis.json')
    original.pop('analyzed_at', None); restored.pop('analyzed_at', None)
    assert original == restored, f'Portable {phase} analysis differs beyond timestamp'
    figures = {p.name: sha(p) == sha(ARCHIVE/f'analysis/{phase}'/p.name)
               for p in output.glob('*.png')}
    assert all(figures.values()), figures
    analyses[phase] = {'command': command, 'exit_code': process.returncode,
        'all_numerical_and_other_analysis_payloads_exactly_equal': True,
        'ignored_generated_fields': ['analyzed_at'], 'PNG_byte_reproducibility': figures}

record = {'status': 'passed', 'checked_at': datetime.now(timezone.utc).isoformat(),
    'archive': str(ARCHIVE.relative_to(ROOT)), 'archive_status': 'read-only; no changes made',
    'manifest_payloads_checked': len(manifest), 'payload_bytes_checked': sum(r['bytes'] for r in manifest),
    'manifest_sha256': sha(ARCHIVE/'MANIFEST.json'), 'manifest_failures': failures,
    'sqlite_integrity_check': integrity, 'sqlite_program_rows': rows,
    'sqlite_unique_generation_slots': slots, 'portable_analysis': analyses,
    'objective_queries': 0, 'model_requests': 0}
(OUT/'portable-verification.json').write_text(json.dumps(record, indent=2)+'\n')
print(json.dumps(record, indent=2))
