#!/usr/bin/env python3
"""Immutable per-session campaign snapshot using existing publication primitives."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from adaptive_swarms.artifacts import read_json
from adaptive_swarms.logging import atomic_json
from archive_joint_v3 import copy_bytes,backup_database,exclusion_reason,file_digest


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    run=a.run.resolve();out=a.output.resolve()
    if out.exists():raise RuntimeError('Session archive exists; never overwrite a published checkpoint')
    state=read_json(run/'campaign_state.json')
    if state['session_status'] not in {'research_paused','controls_checkpoint','runtime_constrained_pause','controls_incomplete_pause','publication_ready'}:
        raise RuntimeError('Archive requires a recorded drained/reviewed research pause')
    dbs=list((run/'evolution').glob('*/programs.sqlite'))
    if dbs:
        checkpoint=read_json(dbs[0].parent/'campaign-checkpoint.json')
        if not checkpoint['drained']:raise RuntimeError('Native campaign checkpoint is not drained')
    records={};omitted={}
    for path in sorted(run.rglob('*')):
        if not path.is_file():continue
        rel=path.relative_to(run);reason=exclusion_reason(rel)
        if reason:omitted[str(rel)]=reason;continue
        if path.suffix.lower()=='.pdf':raise RuntimeError('Copyrighted PDF is not a campaign artifact')
        target=out/rel
        records[str(rel)]=backup_database(path,target) if path.suffix in {'.sqlite','.sqlite3','.db'} else copy_bytes(path,target,operational_snapshot=path.suffix in {'.log','.jsonl'})
    atomic_json(out/'ARCHIVE.json',{'schema':'population-campaign-session-archive-v2','created_at':datetime.now(timezone.utc).isoformat(),'source':str(run),'session_status':state['session_status'],'campaign_status':'in_progress','files':records,'omitted':omitted,'note':'Per-session immutable snapshot; live campaign and later snapshots continue separately. SQLite uses consistent backup and logical verification.'})
    atomic_json(out/'MANIFEST.json',{'status':'complete_session_snapshot','campaign_complete':False,'files':{str(path.relative_to(out)):{'sha256':file_digest(path),'bytes':path.stat().st_size} for path in sorted(out.rglob('*')) if path.is_file()}})
    print(f'Archived {len(records)} files to {out}',flush=True)
if __name__=='__main__':main()
