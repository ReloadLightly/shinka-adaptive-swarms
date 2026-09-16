"""Read native terminal proposal failures without calling them evaluations."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path


def terminal_failure_generations(run_dir: Path, connection=None) -> set[int]:
    """Honor native failure.json/attempt_log outcomes, including crash boundaries.

    Native writes failure.json before its best-effort attempt log. Either durable
    terminal record suffices; an interrupted partial edit is not a terminal slot.
    """
    failures = set()
    for path in run_dir.glob("gen_*/failure.json"):
        record = json.loads(path.read_text())
        generation = record.get("generation")
        try:
            folder_generation = int(path.parent.name.removeprefix("gen_"))
        except ValueError as exc:
            raise RuntimeError(f"Malformed native failure folder: {path}") from exc
        if type(generation) is not int or generation != folder_generation or generation < 1:
            raise RuntimeError(f"Native failure generation disagrees with its artifact folder: {path}")
        if record.get("node_kind") == "failed_proposal" and record.get("downstream_eval_submitted") is False:
            failures.add(generation)

    def read_attempts(connection):
        if not connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='attempt_log'").fetchone():
            return
        for generation, details in connection.execute("SELECT generation, details FROM attempt_log WHERE status='failed'"):
            record = json.loads(details or "{}")
            if record.get("node_kind") == "failed_proposal" and record.get("downstream_eval_submitted") is False:
                if type(generation) is not int or generation < 1:
                    raise RuntimeError("Native terminal attempt has an invalid generation identity.")
                failures.add(generation)

    if connection is not None:
        read_attempts(connection)
    elif (run_dir / "programs.sqlite").exists():
        with sqlite3.connect(f"file:{run_dir / 'programs.sqlite'}?mode=ro", uri=True) as database:
            read_attempts(database)
    return failures
