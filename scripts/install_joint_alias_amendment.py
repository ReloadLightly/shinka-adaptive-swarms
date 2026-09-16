#!/usr/bin/env python3
"""Install the exact committed component-alias amendment before protected V3 work.

The original registration and runner snapshot are never rewritten. This writes
only an explicit amendment receipt and separate study-relative source snapshots.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from adaptive_swarms.artifacts import read_json
from adaptive_swarms.joint_alias_amendment import (
    AMENDMENT_FILE, AMENDMENT_VERSION, SNAPSHOT_DIR, CONTROLLER, SUPPORT,
    digest, file_sha, registry_fingerprint, require_domain, require_preprotected,
    validate_source_delta, verify_amendment, verify_original_registration,
)
from adaptive_swarms.joint_study import execution_fingerprint

PENDING = ".controller-amendment-pending.json"
TOOL_SOURCES = ("scripts/install_joint_alias_amendment.py", "scripts/certify_joint_constants.py",
                "docs/v3_component_alias_amendment.md")


def encoded(record):
    return (json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def write_once(path, content):
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError(f"Preserving conflicting amendment artifact: {path}")
        return
    with path.open("xb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def committed_sources(source_paths, revision=None):
    revision = revision or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    hashes = {}
    for name in source_paths:
        committed = subprocess.check_output(["git", "show", f"{revision}:{name}"], cwd=ROOT)
        actual = (ROOT / name).read_bytes()
        if committed != actual:
            raise ValueError(f"Commit the exact amendment source before installation: {name}")
        hashes[name] = file_sha(ROOT / name)
    return revision, hashes


def install(folder):
    import fcntl
    folder = Path(folder).resolve()
    if not folder.is_dir():
        raise ValueError("An existing registered V3 study is required.")
    with (folder / ".study-controller.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require_preprotected(folder)
        original = verify_original_registration(folder)
        current = execution_fingerprint()
        validate_source_delta(original["execution_sources"], current)
        for config in original["search_cases"] + original["validation_cases"]:
            require_domain(config)
        source_paths = (CONTROLLER, SUPPORT, *TOOL_SOURCES)
        expected_paths = {name: str(Path(SNAPSHOT_DIR) / name.replace("/", "__")) for name in source_paths}
        revision, snapshot_sources = committed_sources(source_paths)
        final, pending = folder / AMENDMENT_FILE, folder / PENDING
        if final.exists():
            record = verify_amendment(folder, original, current)
            if record["snapshot_sources"] != snapshot_sources:
                raise ValueError("Existing amendment may not be reinstalled with changed tools or sources.")
            committed_sources(source_paths, record["source_revision"])
            return record
        if pending.exists():
            record = read_json(pending)
            if digest({key: value for key, value in record.items() if key != "amendment_id"}) != record.get("amendment_id") or record.get("version") != AMENDMENT_VERSION or record["registration_sha256"] != file_sha(folder / "registration.json") or record["original_execution_sources"] != original["execution_sources"] or record["new_execution_sources"] != current or record["snapshot_sources"] != snapshot_sources or record["snapshot_paths"] != expected_paths or record["partial_output_registry_sha256"] != registry_fingerprint() or record["protected_artifacts_present_at_install"] != []:
                raise ValueError("Pending amendment differs; refusing changed recovery inputs.")
            committed_sources(source_paths, record["source_revision"])
        else:
            record = {"version": AMENDMENT_VERSION, "installed_at": datetime.now(timezone.utc).isoformat(),
                "registration_sha256": file_sha(folder / "registration.json"),
                "original_execution_sources": original["execution_sources"], "new_execution_sources": current,
                "source_revision": revision, "snapshot_sources": snapshot_sources,
                "snapshot_paths": expected_paths,
                "partial_output_registry_sha256": registry_fingerprint(), "protected_artifacts_present_at_install": [],
                "commit_verification": "Every recorded source matched git show at the recorded full commit before installation.",
                "scope": "Only exact-reviewed partial-output component aliases and their nominal-action interpretation. Ranking, selection, candidate calls for non-aliased components, simulator, budgets, controls and statistics are unchanged.",
                "chronology": "Implementation amendment after development search outcomes, before source review, validation, selection and final seeds; never relabeled pre-search implementation.",
                "actions": {"candidate_calls": 0, "objective_queries": 0, "model_calls": 0,
                            "original_registration_writes": 0, "original_snapshot_writes": 0}}
            record["amendment_id"] = digest(record)
            write_once(pending, encoded(record))
        snapshot = folder / SNAPSHOT_DIR
        if snapshot.resolve().parent != folder:
            raise ValueError("Amendment snapshot directory escapes the study.")
        snapshot.mkdir(exist_ok=True)
        for name in source_paths:
            content = (ROOT / name).read_bytes()
            if file_sha(ROOT / name) != record["snapshot_sources"][name]:
                raise ValueError("Committed amendment source changed during installation.")
            write_once(folder / record["snapshot_paths"][name], content)
        require_preprotected(folder)
        if file_sha(folder / "registration.json") != record["registration_sha256"]:
            raise ValueError("Original registration changed during amendment installation.")
        write_once(final, encoded(record))
        verify_amendment(folder, original, execution_fingerprint())
        pending.unlink()
        return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    result = install(parser.parse_args().run)
    print(json.dumps({"amendment_id": result["amendment_id"], "source_revision": result["source_revision"],
                      "installed_at": result["installed_at"], "actions": result["actions"]}, indent=2), flush=True)
