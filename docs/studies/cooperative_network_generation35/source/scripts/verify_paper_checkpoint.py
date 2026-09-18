#!/usr/bin/env python3
"""Verify Git-exported reference evidence; never rerun Java, models, or analyses."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from contextlib import closing
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sqlite3
import statistics
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = "paper_trajectory_v2"
RESULTS = "results/" + CAMPAIGN
REPORT = RESULTS + "/reference-report"
PRIMARY_DECISION = "experiments/paper_trajectory_v2/primary_reference_decision.json"
SOURCE_APPENDIX = "docs/paper_trajectory_v2/controller_history_appendix.json"
SEARCH = RESULTS + "/search"
DEFERRED_SCHEMA = "paper-deferred-reference-publication-inventory-v1"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def _path(value):
    if not isinstance(value, str):
        raise RuntimeError("Invalid exported repository path")
    path = PurePosixPath(value)
    if not value or path.is_absolute() or str(path) != value or any(p in (".", "..") for p in path.parts) or any(c in value for c in ("\n", "\r", "\0", ":", "\\")):
        raise RuntimeError("Invalid exported repository path: " + value)
    return value


def _add(expected, path, digest):
    path = _path(path)
    if not isinstance(digest, str) or re.fullmatch("[0-9a-f]{64}", digest) is None:
        raise RuntimeError("Invalid SHA256 for " + path)
    if path in expected and expected[path] != digest:
        raise RuntimeError("Conflicting recorded hashes for " + path)
    expected[path] = digest


def _read_json(data, path):
    try:
        return json.loads(data)
    except (ValueError, UnicodeError) as error:
        raise RuntimeError("Invalid exported JSON: " + path) from error


def publication_inventory(root=ROOT, *, deferred_reference=False):
    """Read a manifest-ready inventory after the report matches a drained index.

    Store the returned value as manifest.reference_report under the caller's
    campaign lock after final report generation. This helper writes nothing.
    """
    root = Path(root)
    if deferred_reference:
        return _deferred_inventory(root)
    index_bytes = (root / RESULTS / "reference-index.json").read_bytes()
    report_path, summary_path = REPORT + "/reference-report.json", REPORT + "/summary.json"
    report = _read_json((root / report_path).read_bytes(), report_path)
    summary = _read_json((root / summary_path).read_bytes(), summary_path)
    snapshot = _path(report["index_snapshot_path"])
    index = _read_json(index_bytes, "reference-index.json")
    if ((root / snapshot).read_bytes() != index_bytes or report["index_sha256"] != sha(index_bytes)
            or summary["input_index_sha256"] != sha(index_bytes)
            or report["verified_completed_cases"] != index["completed"]
            or summary["completed_cases"] != index["completed"]):
        raise RuntimeError("Scientific report is stale relative to the drained reference index; regenerate before publication")
    files = {p.relative_to(root).as_posix(): sha(p.read_bytes())
             for p in sorted((root / REPORT).rglob("*")) if p.is_file()}
    recorded = {REPORT + "/" + _path(name): digest for name, digest in report.get("artifacts_sha256", {}).items()}
    actual = {name: digest for name, digest in files.items() if name not in (report_path, summary_path)}
    if not recorded or recorded != actual:
        raise RuntimeError("Report artifact inventory is absent or does not describe all generated report files")
    sources = set()
    for panel in report["panels"]:
        sources.update(panel.get("source", [])); sources.update(panel.get("code", []))
    if report.get("decisions_path"):
        sources.add(report["decisions_path"])
    sources.update(report.get("behavior_precedence", {}).get("source_paths", []))
    for name in ("experiments/paper_trajectory_v2/benchmark_cases.json", RESULTS + "/benchmark-index.json",
                 "docs/paper_trajectory_v2/scheduling_source_recheck.md",
                 "docs/paper_trajectory_v2/smart_defect_review.md",
                 "docs/paper_trajectory_v2/figure1_provenance.md",
                 "docs/paper_trajectory_v2/source_behavior_mapping.md", PRIMARY_DECISION, SOURCE_APPENDIX,
                 "docs/paper_trajectory_v2/sources/controller_commits_2026-09-17.json",
                 "upstream/multiplex/README.md", "upstream/multiplex/Agents/GamePlayerAgent.java"):
        if (root / name).is_file():
            sources.add(name)
    source_files = {_path(name): sha((root / name).read_bytes()) for name in sorted(sources)}
    return {"schema": "paper-reference-publication-inventory-v1", "path": report_path,
            "sha256": files[report_path], "summary_path": summary_path, "summary_sha256": files[summary_path],
            "index_snapshot_path": snapshot, "index_sha256": sha(index_bytes),
            "completed_cases": index["completed"], "artifacts": files, "source_files": source_files}


class GitExport:
    def __init__(self, commit, root):
        self.root = Path(root)
        self.commit = subprocess.check_output(["git", "rev-parse", "--verify", "--end-of-options", str(commit) + "^{commit}"], cwd=self.root, text=True).strip()

    def read(self, path):
        try:
            return subprocess.check_output(["git", "show", self.commit + ":" + _path(path)], cwd=self.root, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as error:
            raise RuntimeError("Missing exported Git object: " + path) from error

    def json(self, path):
        return _read_json(self.read(path), path)

    def exists(self, path):
        return subprocess.run(["git", "cat-file", "-e", self.commit + ":" + _path(path)], cwd=self.root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

    def paths(self, prefix):
        return subprocess.check_output(["git", "ls-tree", "-r", "--name-only", self.commit, "--", _path(prefix)], cwd=self.root, text=True).splitlines()

    def verify_bytes(self, expected):
        # Stream compressed trajectories from Git; never load the cache in RAM.
        paths = sorted(expected)
        with tempfile.TemporaryFile() as requests:
            requests.write("".join(self.commit + ":" + path + "\n" for path in paths).encode()); requests.seek(0)
            proc = subprocess.Popen(["git", "cat-file", "--batch"], cwd=self.root, stdin=requests, stdout=subprocess.PIPE)
            try:
                for path in paths:
                    header = proc.stdout.readline().decode().strip().split()
                    if len(header) != 3 or header[1] != "blob":
                        raise RuntimeError("Missing exported object: " + path)
                    remaining = int(header[2]); digest = hashlib.sha256()
                    while remaining:
                        data = proc.stdout.read(min(1024 * 1024, remaining))
                        if not data:
                            raise RuntimeError("Truncated Git object: " + path)
                        digest.update(data); remaining -= len(data)
                    if proc.stdout.read(1) != b"\n" or digest.hexdigest() != expected[path]:
                        raise RuntimeError("Exported bytes mismatch: " + path)
                if proc.wait() != 0:
                    raise RuntimeError("Git export verification failed")
            finally:
                if proc.poll() is None:
                    proc.terminate(); proc.wait()
                proc.stdout.close()


def _declaration(cases):
    result = {}
    for case in cases:
        case_id = case["case_id"]
        if case_id in result or case_id != sha(canonical({k: v for k, v in case.items() if k != "case_id"}))[:24]:
            raise RuntimeError("Duplicate or invalid declared case identity")
        result[case_id] = case
    return result


def _deferred_inventory(root):
    """Anchor retained analyses as historical subsets, never as a fresh report."""
    amendment = "experiments/paper_trajectory_v2/discovery_execution_amendment.json"
    authority = _read_json((root / amendment).read_bytes(), amendment)
    if authority.get("supersedes_complete_reproduction_before_discovery") is not True:
        raise RuntimeError("Deferred reference publication requires the explicit execution amendment")
    index_path = RESULTS + "/reference-index.json"
    index = _read_json((root / index_path).read_bytes(), index_path)
    reports = []
    report_paths = [root / REPORT / "reference-report.json"]
    report_paths += sorted((root / RESULTS / "checkpoints").glob("*/reference-report.json"))
    for path in report_paths:
        if not path.is_file():
            continue
        report = _read_json(path.read_bytes(), str(path))
        files = {p.relative_to(root).as_posix(): sha(p.read_bytes())
                 for p in sorted(path.parent.rglob("*")) if p.is_file()}
        reports.append({"path": path.relative_to(root).as_posix(), "sha256": sha(path.read_bytes()),
                        "index_snapshot_path": report["index_snapshot_path"],
                        "index_sha256": report["index_sha256"],
                        "completed_cases": report["verified_completed_cases"],
                        "artifacts": files, "status": "retained_historical_subset_not_current_analysis"})
    sources = {amendment, PRIMARY_DECISION, SOURCE_APPENDIX}
    for folder in ("docs/paper_trajectory_v2", "experiments/paper_trajectory_v2"):
        sources.update(p.relative_to(root).as_posix() for p in (root / folder).rglob("*")
                       if p.is_file() and p.suffix in (".json", ".md", ".java"))
    appendix = root / SOURCE_APPENDIX
    if appendix.is_file():
        sources.update(_read_json(appendix.read_bytes(), SOURCE_APPENDIX).get("unchanged_local_files_sha256", {}))
    decisions_path = "experiments/paper_trajectory_v2/analysis_decisions.json"
    if (root / decisions_path).is_file():
        decisions = _read_json((root / decisions_path).read_bytes(), decisions_path)
        for group in ("resolutions", "comparison_reviews"):
            for decision in decisions.get(group, {}).values():
                sources.update(record["path"] for record in decision.get("evidence", []))
    return {"schema": DEFERRED_SCHEMA, "index_path": index_path,
            "index_sha256": sha((root / index_path).read_bytes()), "completed_cases": index["completed"],
            "reference_status": "unfinished_deferred", "analysis_regenerated": False,
            "execution_amendment": {"path": amendment, "sha256": sha((root / amendment).read_bytes())},
            "historical_reports": reports,
            "retained_analysis_artifacts": {p.relative_to(root).as_posix(): sha(p.read_bytes())
                for p in sorted((root / RESULTS / "checkpoints").rglob("*")) if p.is_file()},
            "operational_evidence_files": {p.relative_to(root).as_posix(): sha(p.read_bytes())
                for p in sorted((root / RESULTS / "operations").rglob("*"))
                if p.is_file() and p.suffix in (".json", ".txt")},
            "source_files": {name: sha((root / name).read_bytes()) for name in sorted(sources) if (root / name).is_file()}}


def _deferred_report(export, manifest, index, index_bytes, records, expected):
    inventory = manifest["reference_report"]
    amendment = inventory["execution_amendment"]
    _add(expected, amendment["path"], amendment["sha256"])
    authority = export.json(amendment["path"])
    if (authority.get("campaign_id") != CAMPAIGN or authority.get("supersedes_complete_reproduction_before_discovery") is not True
            or authority.get("publication_requirement") is None or inventory.get("reference_status") != "unfinished_deferred"
            or inventory.get("analysis_regenerated") is not False):
        raise RuntimeError("Deferred reference publication lacks explicit scope authority")
    identity = {k: v for k, v in authority.items() if k != "identity_sha256"}
    if authority.get("identity_sha256") != sha(canonical(identity)):
        raise RuntimeError("Execution amendment identity differs")
    if (inventory["index_path"] != RESULTS + "/reference-index.json" or inventory["index_sha256"] != sha(index_bytes)
            or inventory["completed_cases"] != index["completed"]):
        raise RuntimeError("Deferred reference inventory differs from the retained current index")
    for path, digest in inventory["source_files"].items():
        _add(expected, path, digest)
    for path, digest in inventory.get("retained_analysis_artifacts", {}).items():
        _add(expected, path, digest)
    for path, digest in inventory.get("operational_evidence_files", {}).items():
        _add(expected, path, digest)
    _source_history(export, inventory, expected)
    decisions_path = "experiments/paper_trajectory_v2/analysis_decisions.json"
    if export.exists(decisions_path):
        decisions = export.json(decisions_path)
        for group in ("resolutions", "comparison_reviews"):
            for decision in decisions.get(group, {}).values():
                for record in decision.get("evidence", []):
                    if inventory["source_files"].get(record["path"]) != record["sha256"]:
                        raise RuntimeError("Applied analysis-decision evidence differs from deferred publication")
                    _add(expected, record["path"], record["sha256"])
    for retained in inventory["historical_reports"]:
        for path, digest in retained["artifacts"].items():
            _add(expected, path, digest)
        _add(expected, retained["path"], retained["sha256"])
        report = export.json(retained["path"])
        snapshot_bytes = export.read(retained["index_snapshot_path"])
        snapshot = _read_json(snapshot_bytes, retained["index_snapshot_path"])
        if (retained["status"] != "retained_historical_subset_not_current_analysis"
                or sha(snapshot_bytes) != retained["index_sha256"] or report["index_sha256"] != retained["index_sha256"]
                or report["index_snapshot_path"] != retained["index_snapshot_path"]
                or report["verified_completed_cases"] != retained["completed_cases"]
                or len(snapshot["cases"]) != retained["completed_cases"]
                or report["engine_sha256"] != index["engine_sha256"] or report.get("complete") is not False):
            raise RuntimeError("Historical reference report identity/count/snapshot differs")
        for receipt in snapshot["cases"]:
            current = records.get(receipt["case_id"])
            if current is None or receipt["identity"] != current["identity"] or receipt["cache_key"] != current["cache_key"]:
                raise RuntimeError("Historical reference report contains a missing or divergent history")
        folder = str(PurePosixPath(retained["path"]).parent)
        for relative, digest in report.get("artifacts_sha256", {}).items():
            if retained["artifacts"].get(folder + "/" + _path(relative)) != digest:
                raise RuntimeError("Historical report artifact changed")
    registration = manifest.get("scientific_contract_decisions", {}).get("primary_reference")
    if not registration or registration["path"] != PRIMARY_DECISION:
        raise RuntimeError("Deferred checkpoint lacks the explicit primary-reference decision")
    _add(expected, registration["path"], registration["sha256"])
    primary = export.json(PRIMARY_DECISION)
    if (primary.get("primary") != "source_executable" or primary.get("engine_sha256") != index["engine_sha256"]
            or primary["identity_sha256"] != sha(canonical({k: v for k, v in primary.items() if k != "identity_sha256"}))):
        raise RuntimeError("Deferred checkpoint primary authority differs")
    for path, digest in primary["equivalence_evidence"].items():
        _add(expected, path, digest)
    return {"index_sha256": sha(index_bytes), "complete": False, "behavior_precedence": {"primary": "source_executable"},
            "publication_mode": "current_receipt_inventory_with_retained_historical_analysis",
            "retained_report_counts": [r["completed_cases"] for r in inventory["historical_reports"]]}


def _index(index, declared, engine, program, mode, blocked, expected):
    if index["campaign_id"] != CAMPAIGN or index["engine_sha256"] != engine or index["planned"] != len(declared) or index["completed"] != len(index["cases"]):
        raise RuntimeError("Exported " + mode + " identity/count mismatch")
    records = {}
    for receipt in index["cases"]:
        identity = receipt["identity"]; case_id = receipt["case_id"]
        if case_id in records or identity["case"] != declared.get(case_id) or identity["case"]["case_id"] != case_id:
            raise RuntimeError("Duplicate or undeclared exported " + mode + " case")
        if identity.get("schema") != "paper-trajectory-case-v1" or identity["engine_sha256"] != engine or identity["program_sha256"] != program or receipt["role"] != mode:
            raise RuntimeError("Exported case engine/program/role mismatch")
        key = sha(canonical(identity)); base = RESULTS + "/cache/" + key[:2] + "/" + key
        if receipt["cache_key"] != key or receipt["trajectory_path"] not in (base + ".json.gz", base + ".json.xz"):
            raise RuntimeError("Exported case cache key/path mismatch")
        _add(expected, receipt["trajectory_path"], receipt["trajectory_sha256"])
        _add(expected, base + ".json", sha((json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()))
        records[case_id] = receipt
    if index.get("blocked_methods", []) != blocked:
        raise RuntimeError("Exported blocked-method evidence differs from manifest")
    pending = sum(case_id not in records and any(all(case[k] == method[k] for k in ("n", "sampling", "interpretation")) for method in blocked)
                  for case_id, case in declared.items())
    if index.get("blocked_pending_cases", 0) != pending or index.get("feasible_remaining", len(declared) - len(records)) != len(declared) - len(records) - pending:
        raise RuntimeError("Exported pending/feasible counts differ from declared cases")
    return records


def _primary_reference(export, manifest, report, inventory, expected):
    """Bind the explicit precedence amendment without rewriting older exports."""
    registration = manifest.get("scientific_contract_decisions", {}).get("primary_reference")
    behavior = report.get("behavior_precedence", {})
    if not registration and not export.exists(PRIMARY_DECISION) and not behavior.get("valid"):
        return
    if not registration or registration.get("path") != PRIMARY_DECISION:
        raise RuntimeError("Primary-reference decision exists without its manifest authority binding")
    authority_ref = {key: registration[key] for key in ("path", "sha256")}
    _add(expected, authority_ref["path"], authority_ref["sha256"])
    authority = export.json(authority_ref["path"])
    if authority.get("schema") != "paper-primary-reference-decision-v1" or authority.get("campaign_id") != CAMPAIGN:
        raise RuntimeError("Primary-reference decision schema/campaign mismatch")
    identity = {"primary": "source_executable", "sensitivity": ["paper_directed"],
                "outcome_independent": True, "engine_sha256": report["engine_sha256"],
                "upstream_commit": "b3d7737613578da260fee561b6f73122dc4f2ab0"}
    if any(authority.get(key) != value for key, value in identity.items()):
        raise RuntimeError("Primary-reference authority contradicts frozen engine/interpretation")
    if authority.get("identity_sha256") != sha(canonical({k: v for k, v in authority.items() if k != "identity_sha256"})):
        raise RuntimeError("Primary-reference decision identity hash mismatch")
    if behavior.get("valid") is not True or behavior.get("errors") or behavior.get("authority") != authority_ref:
        raise RuntimeError("Scientific report lacks verified primary-reference precedence")
    if behavior.get("decision_id") != authority.get("decision_id") or any(behavior.get(key) != value for key, value in identity.items()):
        raise RuntimeError("Scientific report precedence differs from its authority")
    if not report.get("decisions_path"):
        raise RuntimeError("Primary-reference report lacks analysis-decision evidence")
    decisions = export.json(report["decisions_path"])
    binding = decisions.get("behavior_precedence", {})
    if binding.get("authority") != authority_ref or any(binding.get(key) != value for key, value in identity.items()):
        raise RuntimeError("Analysis decisions differ from the manifest primary authority")
    mapping = behavior.get("source_mapping")
    if not mapping or binding.get("source_mapping") != mapping:
        raise RuntimeError("Primary-reference source mapping differs between report and decisions")
    _add(expected, mapping["path"], mapping["sha256"])
    dependencies = {authority_ref["path"]: authority_ref["sha256"], mapping["path"]: mapping["sha256"]}
    dependencies.update(authority.get("equivalence_evidence", {}))
    if not dependencies or "docs/paper_trajectory_v2/engine_checks.json" not in dependencies:
        raise RuntimeError("Primary-reference authority lacks source-equivalence evidence")
    for path, digest in dependencies.items():
        if inventory["source_files"].get(path) != digest:
            raise RuntimeError("Primary-reference dependency lacks its published source hash: " + path)
        _add(expected, path, digest)
    if not set(dependencies) <= set(behavior.get("source_paths", [])):
        raise RuntimeError("Scientific report omits primary-reference evidence paths")
    checks = export.json("docs/paper_trajectory_v2/engine_checks.json")
    if checks.get("pass") is not True or checks.get("checks", 0) <= 0 or checks.get("engine_sha256") != report["engine_sha256"]:
        raise RuntimeError("Primary source-equivalence receipt does not attest to the frozen engine")
    roles = {"source_executable": "primary", "paper_directed": "sensitivity"}
    for panel in report["panels"]:
        config, comparison = panel.get("configuration", {}), panel.get("comparison", {})
        if (config.get("primary_interpretation") != identity["primary"]
                or config.get("sensitivity_interpretations") != identity["sensitivity"]
                or config.get("precedence_authority") != authority_ref
                or config.get("source_behavior_mapping") != mapping
                or comparison.get("interpretation_roles") != roles
                or comparison.get("agreement_between_interpretations_required") is not False
                or comparison.get("historical_seed_recovery_required") is not False):
            raise RuntimeError("Panel does not preserve the authorized primary/sensitivity roles")
        for value in comparison.get("values", []):
            if value.get("method") and value.get("interpretation_role") != roles.get(value["method"][0]):
                raise RuntimeError("Panel comparison mislabels its interpretation role")


def _source_history(export, inventory, expected):
    if not export.exists(SOURCE_APPENDIX):
        return
    appendix = export.json(SOURCE_APPENDIX)
    dependencies = dict(appendix["unchanged_local_files_sha256"])
    dependencies[appendix["response"]["path"]] = appendix["response"]["sha256"]
    if SOURCE_APPENDIX not in inventory["source_files"]:
        raise RuntimeError("Source-history appendix lacks its publication hash")
    for path, digest in dependencies.items():
        if inventory["source_files"].get(path) != digest:
            raise RuntimeError("Source-history dependency differs from publication inventory")
        _add(expected, path, digest)


def _analysis_resolutions(export, report, inventory, expected):
    if not report.get("decisions_path"):
        return
    decisions = export.json(report["decisions_path"])
    for key, resolution in decisions.get("resolutions", {}).items():
        evidence = resolution.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            raise RuntimeError("Analysis resolution lacks path/hash evidence: " + key)
        paths = set()
        for record in evidence:
            path, digest = record["path"], record["sha256"]
            _add(expected, path, digest)
            if inventory["source_files"].get(path) != digest:
                raise RuntimeError("Analysis-resolution evidence differs from publication: " + key)
            paths.add(path)
        checked = report.get("resolution_evidence", {}).get(key, {})
        if checked.get("valid") is not True or checked.get("errors") or set(checked.get("source_paths", [])) != paths:
            raise RuntimeError("Report lacks verified analysis-resolution evidence: " + key)
        for panel in report["panels"]:
            for ambiguity in panel.get("ambiguities", []):
                if ambiguity["id"] != key:
                    continue
                if not paths <= set(panel["source"]):
                    raise RuntimeError("Panel omits its analysis-resolution evidence: " + key)
                if ambiguity.get("resolved_for_v2") and (
                        ambiguity.get("evidence_valid") is not True
                        or ambiguity.get("classification") != resolution.get("classification")
                        or ambiguity.get("resolution") != resolution):
                    raise RuntimeError("Panel analysis-resolution identity differs: " + key)
    for target, review in decisions.get("comparison_reviews", {}).items():
        evidence = review.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            raise RuntimeError("Comparison review lacks path/hash evidence: " + target)
        paths = set()
        for record in evidence:
            path, digest = record["path"], record["sha256"]
            _add(expected, path, digest)
            if inventory["source_files"].get(path) != digest:
                raise RuntimeError("Comparison-review evidence differs from publication: " + target)
            paths.add(path)
        checked = report.get("comparison_review_evidence", {}).get(target, {})
        if checked.get("valid") is not True or checked.get("errors") or set(checked.get("source_paths", [])) != paths:
            raise RuntimeError("Report lacks verified comparison-review evidence: " + target)
        panels = [panel for panel in report["panels"] if panel["id"] == target]
        if len(panels) != 1 or not paths <= set(panels[0]["source"]):
            raise RuntimeError("Comparison review lacks its panel/evidence: " + target)
        comparison = panels[0]["comparison"]
        if comparison.get("discrepancy_review") is not None and (
                comparison["discrepancy_review"] != review or comparison.get("review_evidence_valid") is not True
                or comparison.get("status") != "executed_discrepant" or comparison.get("consequential") is not False):
            raise RuntimeError("Panel comparison-review identity differs: " + target)


def _report(export, manifest, index, index_bytes, records, expected):
    inventory = manifest.get("reference_report")
    if inventory and inventory.get("schema") == DEFERRED_SCHEMA:
        return _deferred_report(export, manifest, index, index_bytes, records, expected)
    if not inventory or inventory.get("schema") != "paper-reference-publication-inventory-v1":
        raise RuntimeError("Missing manifest-anchored scientific report inventory")
    for field in ("artifacts", "source_files"):
        for path, digest in inventory[field].items():
            _add(expected, path, digest)
    _add(expected, inventory["path"], inventory["sha256"])
    _add(expected, inventory["summary_path"], inventory["summary_sha256"])
    report, summary = export.json(inventory["path"]), export.json(inventory["summary_path"])
    if inventory["path"] != REPORT + "/reference-report.json" or inventory["summary_path"] != REPORT + "/summary.json":
        raise RuntimeError("Unexpected scientific report location")
    snapshot = report["index_snapshot_path"]
    if snapshot != inventory["index_snapshot_path"] or snapshot != REPORT + "/" + summary["input_index_snapshot"] or export.read(snapshot) != index_bytes:
        raise RuntimeError("Scientific report snapshot differs from the committed reference index")
    index_hash = sha(index_bytes)
    if any(value != index_hash for value in (report["index_sha256"], inventory["index_sha256"], summary["input_index_sha256"], report["baseline_identity"]["index_sha256"])):
        raise RuntimeError("Scientific report index hashes disagree")
    if any(value != index["completed"] for value in (report["verified_completed_cases"], summary["completed_cases"], inventory["completed_cases"])):
        raise RuntimeError("Scientific report and reference index counts differ")
    if report["campaign_id"] != CAMPAIGN or report["engine_sha256"] != index["engine_sha256"] or report["declared_cases"] != index["planned"] or summary["declared_cases"] != index["planned"]:
        raise RuntimeError("Scientific report campaign/engine/declaration differs")
    programs = {r["identity"]["program_sha256"] for r in records.values()}
    if programs and programs != {report["program_sha256"]}:
        raise RuntimeError("Scientific report refers to a different reference policy")
    if summary["reference_complete"] != report["complete"] or (report["complete"] and (index["completed"] != index["planned"] or report["blocking_ambiguities"])):
        raise RuntimeError("Scientific report falsely claims complete evidence")
    reported = {REPORT + "/" + _path(path): digest for path, digest in report.get("artifacts_sha256", {}).items()}
    actual = {path: digest for path, digest in inventory["artifacts"].items() if path not in (inventory["path"], inventory["summary_path"])}
    if not reported or reported != actual:
        raise RuntimeError("Scientific report artifact hashes differ from publication inventory")
    required = {REPORT + "/" + _path(path) for path in summary.get("artifacts", [])}
    required.update(REPORT + "/" + _path(path) for values in summary.get("tables", {}).values() for path in values)
    required.update((snapshot, REPORT + "/coverage.json", REPORT + "/coverage.md"))
    if not required <= set(actual):
        raise RuntimeError("Scientific report contains unanchored plots/tables/coverage")
    if export.json(REPORT + "/coverage.json") != summary["coverage"]:
        raise RuntimeError("Scientific coverage artifact differs from summary")
    for path, digest in report["baseline_identity"]["files"].items():
        if inventory["artifacts"].get(path) != digest:
            raise RuntimeError("Baseline artifact differs from the report inventory")
        _add(expected, path, digest)
    if report.get("decisions_path"):
        _add(expected, report["decisions_path"], report["decisions_sha256"])
    _primary_reference(export, manifest, report, inventory, expected)
    _source_history(export, inventory, expected)
    _analysis_resolutions(export, report, inventory, expected)
    panel_ids = [panel["id"] for panel in report["panels"]]
    if len(panel_ids) != 11 or set(panel_ids) != {"Figure2", "Figure3", "Figure4", "Figure5", "Figure6", "Figure7", "S1", "S2", "S3", "S4", "TableS1"}:
        raise RuntimeError("Scientific report does not account for all eleven required panels")
    for panel in report["panels"]:
        if not set(panel.get("executed_case_ids", [])) <= set(records):
            raise RuntimeError("Panel cites cases absent from its exact reference snapshot")
        for path in panel.get("source", []) + panel.get("code", []):
            if path not in inventory["source_files"]:
                raise RuntimeError("Scientific report source/code dependency lacks a frozen hash")
        fixture = panel.get("configuration", {}).get("engine_fixture")
        if fixture:
            _add(expected, fixture["path"], fixture["sha256"])
            if export.json(fixture["path"])["engine_sha256"] != index["engine_sha256"]:
                raise RuntimeError("Panel fixture refers to a different engine")
    cdf = export.json(REPORT + "/utility_cdf_reference.json")
    if cdf != summary["utility_cdf"] or cdf.get("scope") != "per_method" or cdf.get("cross_method_pooling") is not False or cdf.get("candidate_values_in_pool") is not False:
        raise RuntimeError("Scientific CDF identity/pooling differs from the summary")
    grouped = defaultdict(set)
    for case_id, receipt in records.items():
        case = receipt["identity"]["case"]; grouped[(case["interpretation"], case["n"], case["sampling"])].add(case_id)
    seen = set(); total = 0
    for pool in cdf["pools"]:
        method = tuple(pool["method"])
        if method in seen or len(set(pool["reference_cases"])) != len(pool["reference_cases"]) or set(pool["reference_cases"]) != grouped.get(method):
            raise RuntimeError("CDF pool case identities differ from its method snapshot")
        seen.add(method)
        observations = sum((records[i]["identity"]["case"]["horizon"] + 1) * records[i]["identity"]["case"]["n"] for i in grouped[method])
        if observations != pool["observations"]:
            raise RuntimeError("CDF pool observation count differs from its complete histories")
        total += observations
        metadata_path, pool_path = REPORT + "/" + _path(pool["metadata_file"]), REPORT + "/" + _path(pool["pool_file"])
        if export.json(metadata_path) != pool or inventory["artifacts"].get(pool_path) != pool["pool_sha256"]:
            raise RuntimeError("CDF method metadata/data differs from the report")
    if seen != set(grouped) or total != cdf["observations"]:
        raise RuntimeError("CDF does not cover exactly the report's reference methods")
    return report


def _sqlite_export(data, *, programs=False):
    """Inspect committed main bytes only; no WAL, runner, or pickle execution."""
    with tempfile.TemporaryDirectory(prefix="paper-export-sqlite-") as folder:
        path = Path(folder) / "database.sqlite"
        path.write_bytes(data)
        with closing(sqlite3.connect(path.as_uri() + "?immutable=1&mode=ro", uri=True)) as db:
            if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise RuntimeError("Exported SQLite integrity failure")
            if db.execute("PRAGMA journal_mode").fetchone()[0].lower() != "delete":
                raise RuntimeError("Exported SQLite is not a standalone DELETE-journal snapshot")
            schema = db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name").fetchall()
            tables = {}
            for kind, name, _, _ in schema:
                if kind != "table":
                    continue
                quoted = '"' + name.replace('"', '""') + '"'
                columns = [row[1] for row in db.execute("PRAGMA table_info(" + quoted + ")")]
                rows = db.execute("SELECT * FROM " + quoted).fetchall()
                safe = lambda row: [({"sqlite_blob_hex": v.hex()} if isinstance(v, bytes) else v) for v in row]
                tables[name] = {"columns": columns, "rows": sorted((safe(row) for row in rows), key=canonical)}
            result = {"tables_sha256": sha(canonical({"schema": schema, "tables": tables})), "tables": tables}
        if programs:
            sys.path.insert(0, str(ROOT))
            from scripts.campaign_state import database_fingerprint
            result["fingerprint"] = database_fingerprint(path)
        return result


def _native_export(export, manifest, accounting, expected):
    publication = manifest.get("publication")
    if not publication:
        if accounting["terminal_slots"] or accounting["model_responses"] or export.exists(SEARCH + "/programs.sqlite"):
            raise RuntimeError("Native state exists without a matching publication")
        return {"present": False, "case_keys": set()}
    _add(expected, publication["path"], publication["sqlite_sha256"])
    primary = _sqlite_export(export.read(SEARCH + "/programs.sqlite"), programs=True)
    snapshot = _sqlite_export(export.read(publication["path"]), programs=True)
    if primary != snapshot:
        raise RuntimeError("Committed primary and snapshot differ in SQLite schema or full table contents")
    fingerprint = primary["fingerprint"]
    if fingerprint != accounting.get("database"):
        raise RuntimeError("Native full population fingerprint differs from committed accounting")
    for key in ("records_sha256", "program_rows", "generations", "best_program_id", "best_generation", "best_score"):
        if publication.get(key) != fingerprint[key]:
            raise RuntimeError("Native publication/accounting mismatch: " + key)
    records = fingerprint["records"]
    originals = [row for row in records if not row.get("administrative_copy")]
    original_ids = {row["id"] for row in originals}
    table = primary["tables"]["programs"]
    full_rows = {row["id"]: row for row in (dict(zip(table["columns"], values)) for values in table["rows"])}
    failures = set()
    for path in export.paths(SEARCH):
        if re.fullmatch(re.escape(SEARCH) + r"/gen_\d+/failure\.json", path):
            failure = export.json(path); generation = int(PurePosixPath(path).parent.name[4:])
            if failure.get("generation") != generation:
                raise RuntimeError("Failed proposal receipt generation differs")
            if failure.get("node_kind") == "failed_proposal" and failure.get("downstream_eval_submitted") is False:
                failures.add(generation)
    evaluated = {row["generation"] for row in originals}
    if evaluated & failures:
        raise RuntimeError("Slot counted as both evaluated and failed proposal")
    terminal = sorted(evaluated | failures)
    if not terminal or terminal[0] != 0 or any(not 0 <= value <= 50 for value in terminal):
        raise RuntimeError("Native campaign lacks seed or exceeds the 50-descendant ceiling")
    values = {"terminal_slots": terminal, "initialization_programs": sum(row["generation"] == 0 for row in originals),
              "failed_proposal_slots": sorted(failures), "unique_evaluated_programs": len(originals),
              "valid_descendants": sum(row["generation"] > 0 and bool(row["correct"]) for row in originals),
              "invalid_descendants": sum(row["generation"] > 0 and not row["correct"] for row in originals),
              "administrative_copies": len(records) - len(originals),
              "remaining_descendant_slots": 50 - sum(value > 0 for value in terminal)}
    if any(accounting.get(key) != value for key, value in values.items()) or publication["terminal_slots"] != terminal:
        raise RuntimeError("Native slot, validity, copy or failure accounting differs")
    contract_path = "experiments/paper_trajectory_v2/scientific_contract.json"
    contract = export.json(contract_path)
    identity = sha(canonical({k: v for k, v in contract.items() if k != "identity_sha256"}))
    registration = manifest.get("scientific_contract", {})
    if registration.get("path") != contract_path or registration.get("identity_sha256") != identity:
        raise RuntimeError("Native scientific contract lacks its manifest binding")
    _add(expected, contract_path, registration["sha256"])
    if (contract.get("identity_sha256") != identity or contract.get("schema") != "paper-extension-contract-v1"
            or contract["engine_sha256"] != manifest["reference_engine"]["engine_sha256"]):
        raise RuntimeError("Native scientific contract identity differs")
    for path, digest in contract["files"].items():
        from scripts.paper_operational_compatibility import resolved_digest
        _add(expected, path, resolved_digest(path, digest, export.read))
    readiness = export.json("experiments/paper_trajectory_v2/discovery_readiness.json")
    admission = export.json("experiments/paper_trajectory_v2/seed_admission.json")
    for receipt in (readiness, admission):
        if (receipt.get("campaign_id") != CAMPAIGN
                or receipt.get("identity_sha256") != sha(canonical({k: v for k, v in receipt.items() if k != "identity_sha256"}))):
            raise RuntimeError("Native readiness/seed-admission identity differs")
    if (contract["reference_milestone_identity"] != readiness["identity_sha256"]
            or admission.get("readiness_identity") != readiness["identity_sha256"]
            or admission.get("scientific_identity") != identity or admission.get("correct") is not True
            or admission.get("score") != 0 or admission.get("completed_cases") != 288):
        raise RuntimeError("Native task lacks its exact completed full-panel seed admission")
    for path, digest in admission["files"].items():
        _add(expected, path, digest)
    task = export.json(SEARCH + "/native-task-identity.json")
    task_identity = sha(json.dumps(task, sort_keys=True, allow_nan=False).encode())
    if (task.get("campaign_id") != CAMPAIGN or task.get("scientific_identity") != identity
            or task.get("initialization_programs") != 1 or task.get("max_descendant_proposals") != 50):
        raise RuntimeError("Native task/scientific identity differs")
    for field, source, destination in (("seed_sha256", contract["seed_path"], "CandidatePolicy.java"),
                                      ("immutable_prompt_sha256", contract["task_prompt_path"], "task_prompt.md"),
                                      ("search_prompt_sha256", "experiments/paper_trajectory_v2/search_prompt.md", "search_prompt.md")):
        if sha(export.read(source)) != task[field] or sha(export.read(SEARCH + "/frozen/" + destination)) != task[field]:
            raise RuntimeError("Native executed scientific copy differs: " + destination)
    if task["job"]["eval_program_sha256"] != contract["evaluator_sha256"]:
        raise RuntimeError("Native executed evaluator differs from frozen contract")
    if task["evolution"].get("task_sys_msg") != export.read(contract["task_prompt_path"]).decode():
        raise RuntimeError("Native configured scientific prompt differs from frozen bytes")
    seed = next(row for row in originals if row["generation"] == 0)
    if seed["candidate_sha256"] != admission["candidate_sha256"] or not seed["correct"] or seed["combined_score"] != 0:
        raise RuntimeError("Native initializer differs from admitted zero-score seed")
    required_state = {"prompts.sqlite", "bandit_state.pkl", "phase-b-bandit-summary.json", "native-task-identity.json", "native_memory/state.json"}
    if not required_state <= set(publication["native_state_sha256"]):
        raise RuntimeError("Native publication lacks required lifecycle snapshots")
    for relative, digest in publication["native_state_sha256"].items():
        _add(expected, publication["native_state_path"] + "/" + relative, digest)
        current = export.read(SEARCH + "/" + relative)
        if relative.endswith(".sqlite"):
            if _sqlite_export(current) != _sqlite_export(export.read(publication["native_state_path"] + "/" + relative)):
                raise RuntimeError("Native prompt SQLite differs from checkpoint")
        elif sha(current) != digest:
            raise RuntimeError("Native lifecycle bytes differ from checkpoint: " + relative)
    memory = export.json(SEARCH + "/native_memory/state.json")
    bandit = export.json(SEARCH + "/phase-b-bandit-summary.json")
    for state in (memory, bandit):
        if state.get("campaign_id") != CAMPAIGN or state.get("campaign_identity_sha256") != task_identity:
            raise RuntimeError("Native lifecycle task identity differs")
    continuity = memory["_continuity"]
    if continuity.get("operation") or continuity["bootstrap"]["status"] in ("started", "failed"):
        raise RuntimeError("Native publication has an unresolved memory operation")
    if continuity["identity"]["immutable_prompt_sha256"] != task["immutable_prompt_sha256"]:
        raise RuntimeError("Native memory scientific prompt differs")
    arms = task["evolution"]["llm_models"]
    if arms != ["headless/codex@gpt-6-astra?effort=xhigh", "headless/codex@gpt-5.6-sol?effort=xhigh"]:
        raise RuntimeError("Native model portfolio differs from authorized subscription routes")
    if (bandit["native_state"]["arm_names"] != arms or bandit.get("monetary_cost_weight") != 0
            or not set(bandit["rewarded_program_ids"]) <= original_ids - {row["id"] for row in originals if row["generation"] == 0}):
        raise RuntimeError("Native UCB arms/reward attribution differs")
    counts = {"model_attempts": 0, "model_responses": 0, "model_retries": 0,
              "usage_by_role": {}, "usage_by_arm": {}, "usage_by_subrole": {}}
    for path in export.paths(SEARCH + "/usage"):
        if not path.endswith(".json"):
            continue
        usage = export.json(path)
        if usage.get("route") not in arms or usage.get("paid_api_authorized") is not False or usage.get("status") == "started":
            raise RuntimeError("Unfinished or unauthorized native provider receipt")
        counts["model_attempts"] += 1; counts["model_responses"] += usage["status"] == "returned"
        counts["model_retries"] += bool(usage.get("is_retry"))
        for field, key in (("usage_by_role", usage["role"]), ("usage_by_arm", usage["route"]),
                           ("usage_by_subrole", usage["role"] + "/" + str(usage.get("subrole") or "unspecified"))):
            value = counts[field].setdefault(key, {"attempts": 0, "responses": 0, "elapsed_seconds": 0., "input_tokens": 0, "output_tokens": 0})
            value["attempts"] += 1; value["responses"] += usage["status"] == "returned"
            value["elapsed_seconds"] += usage.get("elapsed_seconds", 0.)
            for token in ("input_tokens", "output_tokens"):
                value[token] += usage.get("response", {}).get(token, 0) or 0
    for field, value in counts.items():
        if field.startswith("usage_"):
            # Directory iteration order can change the last floating sum bit.
            actual = accounting.get(field, {})
            if set(actual) != set(value) or any(any(actual[key][name] != item for name, item in group.items() if name != "elapsed_seconds")
                    or abs(actual[key]["elapsed_seconds"] - group["elapsed_seconds"]) > 1e-8 for key, group in value.items()):
                raise RuntimeError("Native usage role/arm accounting differs: " + field)
        elif accounting.get(field) != value:
            raise RuntimeError("Native model accounting differs: " + field)
    panel = _declaration(export.json(contract["development_cases_path"])); case_keys = set()
    baselines = export.json(contract["development_baseline_path"])
    if len(panel) != 288:
        raise RuntimeError("Native development panel must contain all 288 declared conditions")
    for row in records:
        full = full_rows[row["id"]]
        folder = SEARCH + "/gen_" + str(row["generation"])
        metrics, correct = export.json(folder + "/results/metrics.json"), export.json(folder + "/results/correct.json")
        if (sha(export.read(folder + "/main.java")) != row["candidate_sha256"]
                or correct.get("correct") is not bool(row["correct"]) or metrics["combined_score"] != row["combined_score"]
                or metrics["private"].get("candidate_sha256") != row["candidate_sha256"]):
            raise RuntimeError("Native source/correctness/score artifact differs")
        for field, key in (("public_metrics", "public"), ("private_metrics", "private"), ("text_feedback", "text_feedback")):
            saved = full[field]
            if field.endswith("_metrics"):
                saved = json.loads(saved) if isinstance(saved, str) else saved
            if saved != metrics.get(key):
                raise RuntimeError("Native full metrics/feedback differ from evaluated artifacts: " + field)
        if row.get("administrative_copy"):
            source = full_rows[row["copied_from_program_id"]]
            for field in ("code", "generation", "correct", "combined_score", "language", "public_metrics", "private_metrics", "text_feedback"):
                if full[field] != source[field]:
                    raise RuntimeError("Administrative copy changed scientific content")
            continue
        elif row["generation"] > 0:
            prepared = export.json(folder + "/prepared-patch.json")
            if prepared["parent_id"] != row["parent_id"] or prepared["candidate_sha256"] != row["candidate_sha256"]:
                raise RuntimeError("Native prepared candidate lineage differs")
        if row["correct"]:
            if metrics["private"].get("scientific_identity") != identity:
                raise RuntimeError("Evaluated candidate scientific identity differs")
            keys = metrics["private"]["case_cache_keys"]
            if len(keys) != len(panel) or len(set(keys)) != len(panel):
                raise RuntimeError("Valid candidate lacks full exact panel")
            effects = export.json(folder + "/results/case_results.json")
            if len(effects) != len(panel) or [effect["cache_key"] for effect in effects] != keys:
                raise RuntimeError("Native saved case effects differ from evaluated key sequence")
            seen = set(); grouped = {}; raw_effects = []
            for key, effect in zip(keys, effects):
                base = RESULTS + "/cache/" + key[:2] + "/" + key
                receipt = export.json(base + ".json")
                ident = receipt["identity"]; case_id = receipt["case_id"]
                if (receipt["cache_key"] != key or sha(canonical(ident)) != key or ident["case"] != panel.get(case_id)
                        or ident["engine_sha256"] != contract["engine_sha256"] or ident["program_sha256"] != row["candidate_sha256"]
                        or case_id in seen or receipt["trajectory_path"] not in (base + ".json.gz", base + ".json.xz")):
                    raise RuntimeError("Native evaluated case identity differs")
                case = panel[case_id]
                condition_id = sha(canonical({k: case[k] for k in ("n", "d", "e", "cost_before", "cost_after", "shock_count")}))[:24]
                raw = receipt["terminal_mean_utility"] - baselines[case_id]["terminal_mean_utility"]
                scaled = raw / contract["utility_scale"]
                if (effect["case_id"] != case_id or effect["condition_id"] != condition_id
                        or effect["candidate_terminal_population_utility"] != receipt["terminal_mean_utility"]
                        or effect["baseline_terminal_population_utility"] != baselines[case_id]["terminal_mean_utility"]
                        or effect["raw_terminal_population_utility_difference"] != raw or effect["scaled_difference"] != scaled):
                    raise RuntimeError("Native saved case effects differ from frozen comparator/receipts")
                grouped.setdefault(condition_id, []).append(scaled); raw_effects.append(raw)
                seen.add(case_id); case_keys.add(key)
                _add(expected, receipt["trajectory_path"], receipt["trajectory_sha256"])
                _add(expected, base + ".json", sha(export.read(base + ".json")))
            if (set(grouped) != set(contract["condition_weights"])
                    or sum(contract["condition_weights"][key] * statistics.mean(values) for key, values in grouped.items()) != row["combined_score"]
                    or statistics.mean(raw_effects) != metrics["public"]["raw_mean_terminal_population_utility_difference"]):
                raise RuntimeError("Native aggregate score differs from frozen full-panel effects")
    late = {"completed_provider_responses_not_returned_to_native": 0}
    late_path = RESULTS + "/operations/provider-timeout-drain/completed-provider-evidence.json"
    if export.exists(late_path):
        observed = export.json(late_path)
        _add(expected, late_path, sha(export.read(late_path)))
        _add(expected, observed["final_response_path"], observed["final_response_sha256"])
        usage = export.json(SEARCH + "/usage/" + observed["usage_receipt_id"] + ".json")
        if (observed.get("schema") != "paper-owned-provider-trace-snapshot-v1"
                or observed.get("final_response_available") is not True or usage.get("status") == "returned"
                or usage.get("model_requested") != observed["model"] or usage.get("effort_requested") != observed["effort"]):
            raise RuntimeError("Late provider completion attribution differs from its failed native attempt")
        late = {"completed_provider_responses_not_returned_to_native": 1,
                "observed_provider_tokens": observed["usage_events"][-1]["info"]["total_token_usage"],
                "scope": "Retained owned-provider evidence; no native candidate fitness or reward implied"}
    return {"present": True, "program_rows": len(records), "full_tables_sha256": primary["tables_sha256"],
            "records_sha256": fingerprint["records_sha256"], "best_program_id": fingerprint["best_program_id"],
            "best_score": fingerprint["best_score"], "scientific_identity": identity,
            "native_task_identity": task_identity, "case_keys": case_keys, **late, **values}


def verify(commit, root=ROOT):
    export = GitExport(commit, root); expected = {}
    manifest = export.json("campaigns/paper_trajectory_v2.json")
    index_path = RESULTS + "/reference-index.json"; index_bytes = export.read(index_path); index = _read_json(index_bytes, index_path)
    accounting = export.json(RESULTS + "/report/accounting.json")
    if manifest["campaign_id"] != CAMPAIGN or accounting != manifest["accounting"] or accounting["reference_completed"] != index["completed"]:
        raise RuntimeError("Exported accounting/manifest/reference index mismatch")
    for key, name in (("design_sha256", "design.json"), ("reference_cases_sha256", "reference_cases.json")):
        _add(expected, "experiments/paper_trajectory_v2/" + name, manifest[key])
    declared = _declaration(export.json("experiments/paper_trajectory_v2/reference_cases.json"))
    freeze = manifest.get("reference_engine")
    if not freeze:
        raise RuntimeError("Missing frozen reference engine")
    _add(expected, freeze["path"], freeze["sha256"]); engine = export.json(freeze["path"])
    if engine["engine_sha256"] != index["engine_sha256"] or freeze["engine_sha256"] != index["engine_sha256"] or sha(canonical(engine["sources"])) != index["engine_sha256"]:
        raise RuntimeError("Exported frozen engine/index/source-map mismatch")
    if engine["design_sha256"] != manifest["design_sha256"] or engine["reference_cases_sha256"] != manifest["reference_cases_sha256"]:
        raise RuntimeError("Frozen engine uses another reference declaration")
    for path, digest in engine["sources"].items():
        _add(expected, path, digest)
    for name in ("behavior_contract", "build_verifier", "engineering_checks"):
        _add(expected, engine[name + "_path"], engine[name + "_sha256"])
    program = engine["reference_program_sha256"]
    if program != "reference:" + sha(export.read("java-paper/paper/ReferencePolicy.java")):
        raise RuntimeError("Frozen reference policy source differs")
    if export.json(engine["engineering_checks_path"])["engine_sha256"] != index["engine_sha256"]:
        raise RuntimeError("Engineering checks do not match the frozen engine")
    blocked = manifest.get("blocked_methods", [])
    for method in blocked:
        _add(expected, method["evidence_path"], method["evidence_sha256"])
    for amendment in manifest.get("amendments", []):
        _add(expected, amendment["path"], amendment["sha256"])
    records = _index(index, declared, index["engine_sha256"], program, "reference", blocked, expected)
    for field, index_field in (("reference_planned", "planned"), ("reference_blocked_pending_cases", "blocked_pending_cases"), ("reference_feasible_remaining", "feasible_remaining")):
        if accounting[field] != index[index_field]:
            raise RuntimeError("Accounting reference coverage differs: " + field)
    report = _report(export, manifest, index, index_bytes, records, expected)
    native = _native_export(export, manifest, accounting, expected)
    benchmarks = {}
    if export.exists(RESULTS + "/benchmark-index.json"):
        benchmark = export.json(RESULTS + "/benchmark-index.json")
        benchmark_cases = _declaration(export.json("experiments/paper_trajectory_v2/benchmark_cases.json"))
        benchmarks = _index(benchmark, benchmark_cases, index["engine_sha256"], program, "benchmark", blocked, expected)
        if set(records) & set(benchmarks):
            raise RuntimeError("Operational benchmark cases were counted as reference evidence")
    numerical = Counter(); seconds = 0.0; completed_keys = set()
    for line in export.read(RESULTS + "/evaluation_usage.jsonl").splitlines():
        entry = json.loads(line)
        if entry["kind"] == "numerical_case":
            numerical["completed_physical_trajectories" if entry["completed"] else "failed_trajectories"] += 1
            seconds += entry.get("elapsed_seconds", 0.0)
            if entry["completed"]: completed_keys.add(entry["cache_key"])
        elif entry["kind"] == "cache_reuse": numerical["exact_cache_reuses"] += 1
        elif entry["kind"] == "evaluation": numerical["evaluation_invocations"] += 1
    actual = {name: numerical[name] for name in ("completed_physical_trajectories", "failed_trajectories", "exact_cache_reuses", "evaluation_invocations")}
    actual["serial_numerical_seconds"] = seconds
    if (actual != accounting["numerical"]
            or not ({r["cache_key"] for r in [*records.values(), *benchmarks.values()]} | native.pop("case_keys")) <= completed_keys):
        raise RuntimeError("Numerical ledger differs from accounting or lacks completed indexed cases")
    export.verify_bytes(expected)
    return {"commit": export.commit, "campaign_id": CAMPAIGN, "reference_completed": index["completed"],
            "reference_planned": index["planned"], "benchmark_completed": len(benchmarks),
            "reference_engine_sha256": index["engine_sha256"], "reference_report_index_sha256": report["index_sha256"],
            "reference_report_complete": report["complete"], "verified_git_objects": len(expected),
            "primary_reference": report.get("behavior_precedence", {}).get("primary"),
            "publication_mode": report.get("publication_mode", "current_full_reference_report"),
            "retained_report_counts": report.get("retained_report_counts", []), "native": native,
            "terminal_slots": accounting["terminal_slots"], "model_responses": accounting["model_responses"],
            "remaining_descendant_slots": accounting["remaining_descendant_slots"],
            "verification": "Exact Git-exported declarations, engine/contract/checks, reference and benchmark cache bytes, explicitly scoped report inventories, physical/model accounting and any published native full SQLite/state/artifacts; no numerical reruns or pickle execution"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--commit", default="HEAD"); parser.add_argument("--output")
    args = parser.parse_args(); result = verify(args.commit)
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
