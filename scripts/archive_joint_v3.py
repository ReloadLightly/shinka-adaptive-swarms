#!/usr/bin/env python3
"""Publish a new completed V3 artifact tree without changing research sources.

Databases use SQLite's consistent backup API; other scientific files are copied
byte-for-byte. Operational logs are explicitly bounded snapshots. Existing
archive directories, historical V1/V2 artifacts and the global inventory are
never overwritten. --self-test uses only temporary files and a tiny SQLite DB.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from adaptive_swarms.artifacts import read_json
from adaptive_swarms.joint_study import (verify_registration, verify_review,
                                         assert_cases, native_search_record)
from adaptive_swarms.logging import atomic_json
from audit_joint_progress import audit

BLOCKED_DIRS = {".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache",
                ".cache", ".codex", ".git", "huggingface", "model_weights"}
BLOCKED_SUFFIXES = {".pyc", ".pyo", ".pid", ".lock", ".onnx", ".safetensors", ".pt", ".pth", ".bin", ".ckpt", ".pem", ".key"}
AUTH_NAMES = {"auth.json", "credentials.json", "credential.json", "tokens.json", "token.json",
              "access_token", "refresh_token", "id_token", ".netrc", ".npmrc"}
OPERATION_SUFFIXES = {".json", ".jsonl", ".log", ".txt", ".md", ".png", ".svg", ".csv", ".gz"}
OPERATION_SUBDIRECTORIES = {"embedding-calibration", "embedding-service"}
OPERATION_OMISSIONS = {"progress-audit-cache.json"}
SQLITE_SUFFIXES = {".sqlite", ".sqlite3", ".db"}


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def file_digest(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def exclusion_reason(relative):
    if any(part in BLOCKED_DIRS for part in relative.parts):
        return "dependency cache, environment or authentication directory"
    name = relative.name.lower()
    if name.startswith(".env") or name in AUTH_NAMES or name.removesuffix(".gz") in AUTH_NAMES:
        return "credential or authentication filename"
    if name.endswith(("-wal", "-shm", "-journal")):
        return "SQLite sidecar represented by consistent database backup"
    if relative.suffix.lower() in BLOCKED_SUFFIXES or name.endswith(".lock"):
        return "runtime lock/PID/bytecode, model weights or private-key material"
    return None


def _json_auth_check(path):
    """Reject recognizable raw credential JSON, while retaining model receipts."""
    if path.suffix != ".json":
        return
    value = read_json(path)
    sensitive = {"access_token", "refresh_token", "id_token", "OPENAI_API_KEY", "CODEX_API_KEY"}
    def visit(item):
        if isinstance(item, dict):
            for key, child in item.items():
                if key in sensitive and isinstance(child, str) and child:
                    raise ValueError(f"Refusing credential-bearing JSON in publication input: {path}")
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)
    visit(value)


def copy_bytes(source, destination, operational_snapshot=False):
    """Exclusive destination creation; copy only bytes present when source opens."""
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite archive file: {destination}")
    if source.is_symlink():
        raise ValueError(f"Unexpected symlink requires explicit review: {source}")
    _json_auth_check(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    started = timestamp()
    with source.open("rb") as reader, destination.open("xb") as writer:
        before = os.fstat(reader.fileno())
        remaining = before.st_size
        while remaining:
            block = reader.read(min(1024 * 1024, remaining))
            if not block:
                raise RuntimeError(f"Source truncated during copy: {source}")
            writer.write(block)
            digest.update(block)
            remaining -= len(block)
        writer.flush()
        os.fsync(writer.fileno())
        after = os.fstat(reader.fileno())
    if not operational_snapshot and (before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns or source.stat().st_ino != before.st_ino):
        raise RuntimeError(f"Completed scientific source changed while copying: {source}")
    if operational_snapshot and after.st_size < before.st_size:
        raise RuntimeError(f"Operational source truncated during snapshot: {source}")
    checksum = digest.hexdigest()
    if file_digest(destination) != checksum:
        raise RuntimeError(f"Archive byte verification failed: {destination}")
    return {"kind": "operational_snapshot" if operational_snapshot else "byte_identical_copy",
            "source": str(source), "bytes": before.st_size, "sha256": checksum,
            "copy_started_at": started, "copy_finished_at": timestamp(),
            "source_size_at_close": after.st_size,
            "source_grew_during_snapshot": after.st_size > before.st_size}


def _quoted_identifier(name):
    return '"' + name.replace('"', '""') + '"'


def database_logical_inventory(connection):
    schema = connection.execute("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name").fetchall()
    tables = {}
    def typed(value):
        if isinstance(value, bytes):
            return ["bytes", value.hex()]
        if isinstance(value, float):
            return ["float", value.hex()]
        return [type(value).__name__, value]
    for name, in connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
        row_hashes = []
        for row in connection.execute(f"SELECT * FROM {_quoted_identifier(name)}"):
            encoded = json.dumps([typed(value) for value in row], ensure_ascii=True, separators=(",", ":")).encode()
            row_hashes.append(hashlib.sha256(encoded).hexdigest())
        # Sorted row digests preserve duplicates while avoiding row-order assumptions.
        checksum = hashlib.sha256("\n".join(sorted(row_hashes)).encode()).hexdigest()
        tables[name] = {"rows": len(row_hashes), "row_multiset_sha256": checksum}
    return {"schema": schema, "tables": tables,
            "user_version": connection.execute("PRAGMA user_version").fetchone()[0],
            "application_id": connection.execute("PRAGMA application_id").fetchone()[0]}


def backup_database(source, destination):
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite archive database: {destination}")
    if source.is_symlink():
        raise ValueError(f"Unexpected SQLite symlink: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    started = timestamp()
    reader = sqlite3.connect(f"file:{source.resolve()}?mode=ro", uri=True)
    writer = sqlite3.connect(destination)
    try:
        reader.execute("PRAGMA query_only=ON")
        reader.execute("BEGIN")
        source_inventory = database_logical_inventory(reader)
        reader.backup(writer)
        target_inventory = database_logical_inventory(writer)
        if source_inventory != target_inventory:
            raise RuntimeError(f"SQLite schema/table contents differ after backup: {source}")
        if writer.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError(f"Archived SQLite integrity check failed: {destination}")
        # Make the published database self-contained rather than requiring WAL files.
        writer.execute("PRAGMA journal_mode=DELETE")
    finally:
        writer.close()
        reader.close()
    return {"kind": "sqlite_consistent_backup", "source": str(source),
            "backup_started_at": started, "backup_finished_at": timestamp(),
            "source_open_mode": "SQLite URI mode=ro plus query_only and one read transaction",
            "all_schema_and_table_rows_match": True, "integrity_check": "ok",
            "database_logical_inventory": source_inventory,
            "bytes": destination.stat().st_size, "sha256": file_digest(destination)}


def copy_tree(source, destination, entries, skipped, prefix=Path(), operational=False):
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        reason = exclusion_reason(relative)
        if reason:
            if path.is_file() or path.is_symlink():
                skipped.append({"source": str(path), "reason": reason})
            continue
        if path.is_symlink():
            raise ValueError(f"Unexpected publication symlink: {path}")
        if not path.is_file():
            continue
        target = destination / relative
        record = backup_database(path, target) if path.suffix in SQLITE_SUFFIXES else copy_bytes(path, target, operational)
        entries[str(prefix / relative)] = record


def complete_evidence(study):
    """Read existing completion records and measurements; never run a stage."""
    registration = verify_registration(study)
    shortlists = verify_review(study)
    required = ["selection.json", "final_cases.json", "analysis.json", "validation/manifest.json", "validation/summary.json", "final/manifest.json", "final/summary.json"]
    if any(not (study / name).exists() for name in required):
        raise ValueError("V3 archive requires selection, final cases, completed comparison stages and analysis.")
    searches = [native_search_record(identity, registration) for identity in registration["searches"]]
    selection, final_cases, analysis = [read_json(study / name) for name in ("selection.json", "final_cases.json", "analysis.json")]
    for stage, count in (("validation", 8), ("final", 20)):
        manifest = read_json(study / stage / "manifest.json")
        summary = read_json(study / stage / "summary.json")
        if manifest["status"] != "completed" or summary["status"] != "completed":
            raise ValueError(f"Cannot label unfinished {stage} as complete.")
        assert_cases(manifest["cases"], count)
        if any(len(paths) != len(manifest["cases"]) for paths in manifest["case_artifacts"].values()):
            raise ValueError(f"{stage} is missing planned method cases.")
    validation = read_json(study / "validation/manifest.json")
    final = read_json(study / "final/manifest.json")
    if validation["cases"] != registration["validation_cases"]:
        raise ValueError("Validation inputs differ from prospective registration.")
    if final["cases"] != final_cases["cases"] or final["methods"] != selection["methods"]:
        raise ValueError("Final execution inputs differ from frozen methods/cases.")
    if final["freeze_sha256"] != file_digest(study / "selection.json") or final_cases["selection_sha256"] != final["freeze_sha256"]:
        raise ValueError("Final selection fingerprints differ.")
    if analysis["status"] != "completed" or analysis["paired_case_count"] != 80 or analysis["selection"] != selection:
        raise ValueError("Completed final analysis does not match the frozen selection.")
    measured = audit(study)
    if not measured["totals"]["all_searches_ready_for_shortlisting"]:
        raise ValueError("All three registered searches must complete before publication.")
    # Keep the audit compact; source databases and the full run records retain rows.
    return {"registration": registration, "registered_searches": registration["searches"],
            "shortlist_unique_sources": len(shortlists["programs"]),
            "terminal_slots_per_search": [len(search["terminal_generation_ids"]) for search in searches],
            "completed_measurements": measured, "analysis_sha256": file_digest(study / "analysis.json"),
            "selection_sha256": file_digest(study / "selection.json")}


def archive(study, destination, preparation, additional_operations=()):
    destination = destination.resolve()
    if destination.parent != (ROOT / "artifacts").resolve() or not destination.name.startswith("joint_relocation_v3"):
        raise ValueError("The publication destination must be a new artifacts/joint_relocation_v3* directory.")
    if destination.exists():
        raise FileExistsError(f"Preserving existing archive destination: {destination}")
    print(f"[{timestamp()}] Checking saved V3 stage completion and checkpoint accounting before publication.", flush=True)
    evidence = complete_evidence(study)
    operations = study.parent / "operations"
    for identity in evidence["registered_searches"]:
        if not Path(identity["run"]).resolve().is_relative_to(study.parent.resolve() / "evolution"):
            raise ValueError("Registered V3 search lies outside its V3 evolution directory.")
    destination.mkdir(parents=True, exist_ok=False)
    entries, skipped = {}, []
    source_hashes = {str(study / name): file_digest(study / name) for name in ("registration.json", "shortlists.json", "source_review.json", "selection.json", "analysis.json")}
    try:
        for identity in evidence["registered_searches"]:
            source = Path(identity["run"])
            prefix = Path("evolution") / source.name
            print(f"[{timestamp()}] Archiving search {identity['search_index']}: {source.name}; completed copied files={len(entries)}", flush=True)
            copy_tree(source, destination / prefix, entries, skipped, prefix)
        print(f"[{timestamp()}] Archiving frozen study and checkpointed comparisons; completed copied files={len(entries)}", flush=True)
        copy_tree(study, destination / study.name, entries, skipped, Path(study.name))
        selected = []
        for path in operations.iterdir():
            if path.name in OPERATION_OMISSIONS or exclusion_reason(Path(path.name)):
                skipped.append({"source": str(path), "reason": "disposable operational state"})
            elif path.is_file() and path.suffix in OPERATION_SUFFIXES:
                selected.append(path)
            elif path.is_dir() and path.name in OPERATION_SUBDIRECTORIES:
                selected.append(path)
        for relative in additional_operations:
            path = operations / relative
            if not path.resolve().is_relative_to(operations.resolve()):
                raise ValueError("Additional operation path escapes V3 operations.")
            if not path.exists():
                raise FileNotFoundError(path)
            selected.append(path)
        selected = sorted(set(selected))
        for path in selected:
            if any(parent != path and parent.is_dir() and parent in path.parents for parent in selected):
                continue
            relative = path.relative_to(operations)
            prefix = Path("operations") / relative
            reason = exclusion_reason(relative)
            if reason:
                skipped.append({"source": str(path), "reason": reason})
                continue
            if path.is_dir():
                copy_tree(path, destination / prefix, entries, skipped, prefix, operational=True)
            else:
                entries[str(prefix)] = copy_bytes(path, destination / prefix, operational_snapshot=True)
        preparation_record = None
        if preparation.exists():
            preparation_record = {"path": str(preparation), "files": {str(path.relative_to(preparation)): file_digest(path) for path in sorted(preparation.rglob("*")) if path.is_file() and not exclusion_reason(path.relative_to(preparation))}}
        for path, expected in source_hashes.items():
            if file_digest(Path(path)) != expected:
                raise RuntimeError(f"Frozen source record changed during archival: {path}")
        record = {"format": "joint-v3-verified-publication-v1", "payload_verified_at": timestamp(),
                  "source_study": str(study.resolve()), "destination": str(destination),
                  "source_stage_status": "all three searches, validation, final comparison and analysis completed",
                  "publication_complete_marker": "MANIFEST.json must exist and all inventory hashes must verify",
                  "source_is_read_only": True, "source_frozen_record_sha256": source_hashes,
                  "completion_evidence": evidence["completed_measurements"],
                  "shortlist_unique_sources": evidence["shortlist_unique_sources"],
                  "copy_records": entries, "excluded": skipped,
                  "prospective_preparation_archive_reference": preparation_record,
                  "database_note": "Each database is a consistent SQLite backup including WAL-visible state; every schema object/table row was verified. Database bytes need not equal the original file.",
                  "operations_note": "Selected operations are per-file snapshots at recorded copy times. Appending services may continue after the copied byte prefix; this is not a global simultaneous operations snapshot.",
                  "preservation": "No original research file, V1/V2 artifact, preparation archive or global artifacts/MANIFEST.json is changed."}
        atomic_json(destination / "ARCHIVE.json", record)
        inventory = {str(path.relative_to(destination)): {"bytes": path.stat().st_size, "sha256": file_digest(path)} for path in sorted(destination.rglob("*")) if path.is_file()}
        manifest = {"format": "joint-v3-file-inventory-v1", "archive_status": "completed", "created_at": timestamp(),
                    "root": str(destination), "file_count": len(inventory), "files": inventory,
                    "inventory_excludes": ["MANIFEST.json"], "source_actions": "read only; no simulations/model calls/checkpoint writes"}
        for relative, expected in inventory.items():
            path = destination / relative
            if path.stat().st_size != expected["bytes"] or file_digest(path) != expected["sha256"]:
                raise RuntimeError(f"Final archive inventory mismatch: {relative}")
        # This is the completion marker and is published only after every file
        # has passed its final digest check.
        atomic_json(destination / "MANIFEST.json", manifest)
        return {"status": "completed", "destination": str(destination), "files": len(inventory),
                "sqlite_backups": sum(record["kind"] == "sqlite_consistent_backup" for record in entries.values()),
                "source_case_executions": evidence["completed_measurements"]["totals"]["saved_case_executions"]}
    except BaseException as exc:
        # Preserve the newly created incomplete tree for review, never relabel it.
        atomic_json(destination / "ARCHIVE_FAILURE.json", {"status": "incomplete", "failed_at": timestamp(), "error": f"{type(exc).__name__}: {exc}", "completed_copy_records": len(entries), "source_modified": False})
        raise


def self_test():
    with tempfile.TemporaryDirectory(prefix="joint-v3-archive-check-") as temporary:
        root = Path(temporary)
        source = root / "source"
        source.mkdir()
        (source / "result.json").write_text('{"offline_error": 1.25}\n')
        connection = sqlite3.connect(source / "programs.sqlite")
        connection.execute("PRAGMA journal_mode=WAL")
        for name in ("programs", "metadata_store", "attempt_log"):
            connection.execute(f"CREATE TABLE {name}(id INTEGER PRIMARY KEY, text_value TEXT, blob_value BLOB)")
            connection.execute(f"INSERT INTO {name} VALUES (1,?,?)", ("saved\nlogical row", b"\x00\x01"))
        connection.commit()
        destination = root / "destination"
        destination.mkdir()
        entries, skipped = {}, []
        copy_tree(source, destination, entries, skipped)
        assert (source / "result.json").read_bytes() == (destination / "result.json").read_bytes()
        assert entries["programs.sqlite"]["all_schema_and_table_rows_match"]
        assert entries["programs.sqlite"]["database_logical_inventory"]["tables"]["attempt_log"]["rows"] == 1
        assert not (destination / "programs.sqlite-wal").exists()
        assert any(item["source"].endswith("-wal") for item in skipped)
        try:
            copy_bytes(source / "result.json", destination / "result.json")
        except FileExistsError:
            pass
        else:
            raise AssertionError("Existing destination was overwritten")
        assert exclusion_reason(Path("validation/cache/saved-case.json.gz")) is None
        assert exclusion_reason(Path("auth.json"))
        assert exclusion_reason(Path(".venv/module.py"))
        connection.close()
        return {"status": "passed", "scope": "tiny temporary WAL SQLite tables and one JSON file only; no research archival", "checks": ["WAL-visible table backup", "schema/all-row equality", "byte-identical non-DB copy", "sidecar exclusion", "destination overwrite refusal", "scientific case cache retained", "auth/dependency exclusions"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, default=ROOT / "results/joint_relocation_v3/study_20260916")
    parser.add_argument("--destination", type=Path, default=ROOT / "artifacts/joint_relocation_v3")
    parser.add_argument("--preparation", type=Path, default=ROOT / "artifacts/preparation_joint_v3/20260916-execution-readiness")
    parser.add_argument("--operation", action="append", default=[], help="Additional relative V3 operations file/directory snapshot")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    result = self_test() if args.self_test else archive(args.study.resolve(), args.destination, args.preparation, args.operation)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
