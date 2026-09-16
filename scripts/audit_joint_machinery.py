#!/usr/bin/env python3
"""Read-only native V3 machinery accounting; no model or candidate execution.

Run during or after the three searches. Each output is an immutable snapshot;
logical requests, usable responses and local embedding calls remain distinct.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ROLES = ("mutation", "novelty", "meta")


def digest(value):
    return hashlib.sha256(value).hexdigest()


def utc(value):
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, timezone.utc)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.strptime(value, "%Y%m%dT%H%M%S.%fZ").replace(tzinfo=timezone.utc)


class Evidence:
    def __init__(self, root):
        self.root, self.files, self.limitations = root, {}, []

    def label(self, path):
        try:
            return str(path.resolve().relative_to(self.root.resolve()))
        except ValueError:
            return str(path.resolve())

    def bytes(self, path):
        data = path.read_bytes()
        self.files[self.label(path)] = {"bytes_read": len(data), "sha256_at_read": digest(data)}
        return data

    def json(self, path):
        return json.loads(self.bytes(path))

    def lines(self, path):
        if not path.exists():
            return []
        data = self.bytes(path)
        lines = data.splitlines(keepends=True)
        values = []
        for index, line in enumerate(lines):
            if not line.strip():
                continue
            try:
                values.append(json.loads(line))
            except json.JSONDecodeError:
                if index == len(lines) - 1 and not line.endswith(b"\n"):
                    self.limitations.append(f"Omitted incomplete final JSONL record at snapshot: {self.label(path)}")
                else:
                    raise
        return values


def role_totals(receipts):
    result = {}
    for role in ROLES:
        rows = [row for row in receipts if row["role"] == role]
        result[role] = {
            "native_wrapper_invocations": len(rows),
            "requested_logical_responses": sum(row["requested_logical_responses"] for row in rows),
            "usable_responses_returned": sum(row.get("valid_responses", 0) or 0 for row in rows),
            "status_counts": dict(Counter(row["status"] for row in rows)),
            "unclosed_wrapper_invocations": sum(row["status"] == "started" for row in rows),
            "logical_responses_in_unclosed_wrappers": sum(row["requested_logical_responses"] for row in rows if row["status"] == "started"),
            "closed_response_shortfall": sum(max(0, row["requested_logical_responses"] - (row.get("valid_responses") or 0)) for row in rows if row["status"] != "started"),
            "native_cost_estimate_sum": sum(response.get("reported_api_cost") or 0 for row in rows for response in row.get("responses", [])),
            "native_reported_routes": sorted({response["model_reported_by_native_client"] for row in rows for response in row.get("responses", []) if response.get("model_reported_by_native_client")}),
        }
    return result


def numbered_recommendations(text):
    """Extract complete numbered items without assuming one-line paragraphs."""
    if "# META RECOMMENDATIONS" not in text:
        return []
    section = text.split("# META RECOMMENDATIONS", 1)[1]
    return [match.group(2).strip() for match in re.finditer(r"(?ms)^\s*(\d+)[.)]\s+(.+?)(?=^\s*\d+[.)]\s+|\Z)", section)]


def database_rows(path):
    connection = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        rows = [dict(row) for row in connection.execute("SELECT id,code,parent_id,generation,correct,metadata,text_feedback,archive_inspiration_ids,top_k_inspiration_ids,migration_history,island_idx FROM programs")]
    finally:
        connection.close()
    for row in rows:
        for key in ("metadata", "archive_inspiration_ids", "top_k_inspiration_ids", "migration_history"):
            row[key] = json.loads(row[key]) if row[key] else ({} if key == "metadata" else [])
    return rows


def receipt_view(path, value, evidence):
    return {"path": evidence.label(path), **{key: value.get(key) for key in (
        "call_id", "role", "method", "status", "started_at", "finished_at",
        "requested_logical_responses", "valid_responses", "configured_models",
        "configured_client_settings", "explicit_request_kwargs", "effective_provider_effort", "error")},
        "system_prompt_sha256": digest((value.get("system_msg") or "").encode()),
        "message_sha256": digest(json.dumps(value.get("msg"), sort_keys=True).encode()),
        "responses": [{key: response.get(key) for key in ("model_reported_by_native_client", "input_tokens", "output_tokens", "reported_api_cost")}
                      for response in value.get("responses", [])]}


def audit_search(run, evidence):
    if not (run / "manifest.json").exists():
        return {"run": evidence.label(run), "status": "not_started", "role_receipts": []}, [], []
    manifest = evidence.json(run / "manifest.json")
    events = evidence.lines(run / "events.jsonl")
    by_event = defaultdict(list)
    request_contexts, last_sampling = {}, None
    for event in events:
        by_event[event["event"]].append(event)
        if event["event"] == "native_sampling":
            last_sampling = {key: event.get(key) for key in ("generation", "novelty_attempt", "resample_attempt", "parent_id")}
        elif event["event"] == "engine_role_call_start" and event.get("role") in {"mutation", "novelty"}:
            request_contexts[event["call_id"]] = last_sampling
    rows = database_rows(run / "programs.sqlite") if (run / "programs.sqlite").exists() else []
    by_id = {row["id"]: row for row in rows}
    originals = [row for row in rows if not any(row["metadata"].get(key) for key in ("_is_island_copy", "is_island_copy", "island_copy"))]
    raw_receipts = [(path, evidence.json(path)) for path in sorted((run / "engine_calls").glob("*.json"))]
    receipts = [receipt_view(path, value, evidence) for path, value in raw_receipts]
    for receipt in receipts:
        if receipt["call_id"] in request_contexts:
            receipt["preceding_native_sampling_context"] = request_contexts[receipt["call_id"]]
    call_ids = {row["call_id"] for row in receipts}
    starts = {row["call_id"] for row in by_event["engine_role_call_start"]}
    prompt_texts = {}
    for path in sorted(set(run.glob("gen_*/attempts/**/headless_prompt.md")) | set((run / "headless_prompts").glob("*.md"))):
        prompt_texts[path] = evidence.bytes(path).decode()
    task_path = run / "task_snapshot/task_system_prompt.txt"
    task = evidence.bytes(task_path).decode() if task_path.exists() else None
    samples = []
    for event in by_event["native_sampling"]:
        generation = event["generation"]
        candidates = [path for path in prompt_texts if path.is_relative_to(run / f"gen_{generation}" / "attempts")
                      and f"novelty_{event.get('novelty_attempt', 1)}" in path.parts
                      and f"resample_{event.get('resample_attempt', 1)}" in path.parts]
        checks = []
        for path in candidates:
            text = prompt_texts[path]
            ids = [event["parent_id"], *event.get("archive_inspiration_ids", []), *event.get("top_k_inspiration_ids", [])]
            source_checks = []
            for native_id in dict.fromkeys(ids):
                row = by_id.get(native_id)
                source_checks.append({"native_id": native_id, "row_present": row is not None,
                    **({"generation": row["generation"], "source_sha256": digest(row["code"].encode()),
                        "full_source_present": row["code"].strip() in text,
                        "feedback_sha256": digest((row["text_feedback"] or "").encode()),
                        "full_feedback_present": bool(row["text_feedback"]) and row["text_feedback"].strip() in text} if row else {})})
            checks.append({"prompt": evidence.label(path), "frozen_task_context_present": task in text if task else None,
                           "sources": source_checks})
        samples.append({**event, "saved_attempt_prompt_checks": checks,
                        "coverage": "saved attempt prompt inspected" if checks else "no saved attempt prompt available yet; not verified"})
    metas = []
    for path in sorted((run / "meta").glob("meta_*.txt"), key=lambda p: int(p.stem.removeprefix("meta_"))):
        text = evidence.bytes(path).decode()
        metas.append({"artifact": evidence.label(path), "recommendations": numbered_recommendations(text)})
    # The saved meta file and completion event are emitted in the same serial
    # update. Only associate by order when coverage is one-to-one; otherwise
    # retain exact text matches with timing explicitly unverified.
    if len(metas) == len(by_event["meta_update_complete"]):
        for meta, event in zip(metas, by_event["meta_update_complete"]):
            meta["observed_completion_time_by_update_order"] = event["time"]
    injections = []
    for path, value in raw_receipts:
        if value["role"] != "mutation":
            continue
        system = value.get("system_msg") or ""
        matches = []
        for meta in metas:
            completed = meta.get("observed_completion_time_by_update_order")
            if completed and utc(completed) > utc(value["started_at"]):
                continue
            for index, recommendation in enumerate(meta["recommendations"], 1):
                if recommendation and recommendation in system:
                    matches.append({"artifact": meta["artifact"], "recommendation_index": index,
                                    "observed_completion_time_by_update_order": completed,
                                    "recommendation_sha256": digest(recommendation.encode())})
        matches_by_text = {item["recommendation_sha256"] for item in matches}
        crossover_format = "perform crossover between the code scripts" in system
        recommendation_section = "# Potential Recommendations" in system
        earlier_updates = [event for event in by_event["meta_update_complete"] if utc(event["time"]) <= utc(value["started_at"])]
        if matches:
            interpretation = "exact recorded recommendation text present"
        elif crossover_format and not recommendation_section:
            interpretation = "observed crossover prompt without a recommendation section; native crossover format omits meta injection"
        elif not earlier_updates:
            interpretation = "before first observed completed meta update"
        else:
            interpretation = "no exact saved-text match; formatting/coverage gap or no injection, not assumed"
        injections.append({"receipt": evidence.label(path), "started_at": value["started_at"],
            "preceding_native_sampling_context": request_contexts.get(value["call_id"]),
            "matched_recommendations": matches, "unique_exact_recommendation_texts": len(matches_by_text),
            "crossover_format_observed": crossover_format, "recommendation_section_present": recommendation_section,
            "verification": interpretation})
    migrations = []
    seen = set()
    for row in rows:
        for movement in row["migration_history"]:
            key = (row["id"], json.dumps(movement, sort_keys=True))
            if key not in seen:
                migrations.append({"native_id": row["id"], "program_generation": row["generation"], **movement})
                seen.add(key)
    novelty = by_event["novelty_decision"]
    embeds = by_event["embedding_complete"]
    observed = {"native_wrapper_starts_without_receipt": sorted(starts - call_ids),
                "receipts_without_observed_start_event": sorted(call_ids - starts)}
    signatures = [{"native_id": row["id"], "generation": row["generation"], "parent_id": row["parent_id"],
                   "code_sha256": digest(row["code"].encode()), "island_at_snapshot": row["island_idx"],
                   "patch_type": row["metadata"].get("patch_type"), "correct": bool(row["correct"])} for row in rows]
    program_hashes = [{"sha256": digest(row["code"].encode()), "search": run.name, "native_id": row["id"], "generation": row["generation"]} for row in rows]
    for path in sorted(run.glob("gen_*/main.py")):
        program_hashes.append({"sha256": digest(evidence.bytes(path)), "search": run.name, "saved_source": evidence.label(path)})
    result = {"run": evidence.label(run), "status": manifest["status"], "started_at": manifest.get("started_at"), "finished_at": manifest.get("finished_at"),
        "original_evaluated_generation_ids": sorted({row["generation"] for row in originals}),
        "database_rows_including_copies": len(rows), "database_row_identity_digest": digest(json.dumps(signatures, sort_keys=True).encode()),
        "database_rows": signatures, "model_requested": manifest.get("model_requested"),
        "inner_effort_requested": manifest.get("inner_effort_requested"), "inner_effort_effective_manifest": manifest.get("inner_effort_effective"),
        "inner_effort_status_manifest": manifest.get("inner_effort_status"), "role_totals": role_totals(receipts),
        "role_receipts": receipts, "event_receipt_coverage": observed,
        "mutation_wrapper_counts_by_generation": dict(Counter(str(receipt.get("preceding_native_sampling_context", {}).get("generation"))
            for receipt in receipts if receipt["role"] == "mutation" and receipt.get("preceding_native_sampling_context"))),
        "sampling_attempt_counts_by_generation": dict(Counter(str(event["generation"]) for event in by_event["native_sampling"])),
        "retry_context_association": "Most recent native_sampling event before the wrapper-start event in saved event order; the frozen V3 launcher has one proposal worker. Saved prompt source/feedback checks separately verify this context.",
        "degradation_events": by_event["engine_feature_degraded"],
        "patch_types_original_evaluated_rows": dict(Counter(row["metadata"].get("patch_type", "unspecified") for row in originals)),
        "native_sampling": samples,
        "novelty": {"decision_count": len(novelty), "accepted": sum(bool(e["accepted"]) for e in novelty),
                    "rejected": sum(not e["accepted"] for e in novelty), "fallback": sum(bool(e["fallback"]) for e in novelty),
                    "decisions": novelty},
        "native_embeddings": {"starts": len(by_event["embedding_start"]), "completions": len(embeds),
            "dimensions": dict(Counter(str(event["dimensions"]) for event in embeds)),
            "events": by_event["embedding_start"] + embeds,
            "degraded": [e for e in by_event["engine_feature_degraded"] if e.get("role") == "embedding"]},
        "meta": {"updates_started": by_event["meta_update_start"], "updates_completed": by_event["meta_update_complete"],
                 "updates_noop": by_event["meta_update_noop"], "saved_artifacts": metas, "mutation_prompt_injections": injections},
        "migration_history": migrations, "native_migration_logs": by_event["native_migration_log"]}
    return result, raw_receipts, program_hashes


def embedding_service(root, searches, hashes, evidence):
    operations = root / "operations"
    freeze_path = operations / "embedding-freeze.json"
    freeze = evidence.json(freeze_path) if freeze_path.exists() else None
    freeze_time = utc(freeze["frozen_at"]) if freeze else None
    starts = [utc(s["started_at"]) for s in searches if s.get("started_at")]
    search_start = min(starts) if starts else None
    events = evidence.lines(operations / "embedding-service/events.jsonl")
    by_hash = defaultdict(list)
    for record in hashes:
        by_hash[record["sha256"]].append({key: value for key, value in record.items() if key != "sha256"})
    calibration_paths = sorted((operations / "embedding-calibration").glob("*/declaration.json"))
    calibration_sources = []
    for path in calibration_paths:
        declaration = evidence.json(path)
        for name, source in declaration.get("sources", {}).items():
            calibration_sources.append({"sha256": digest(source.encode()), "declaration": evidence.label(path), "source_name": name})
    calibration_by_hash = defaultdict(list)
    for source in calibration_sources:
        calibration_by_hash[source["sha256"]].append({key: value for key, value in source.items() if key != "sha256"})
    buckets = defaultdict(list)
    linked_requests = []
    for event in events:
        when = utc(event["timestamp"])
        phase = "development_before_freeze" if freeze_time and when < freeze_time else (
            "after_freeze_before_first_search" if search_start and when < search_start else "search_period_or_later")
        if not freeze_time:
            phase = "phase_unverified_without_freeze_record"
        buckets[phase].append(event)
        if event["event"] == "embedding_started":
            linked_requests.append({**event, "phase": phase, "input_hash_links": [
                {"sha256": value, "matching_saved_sources": by_hash.get(value, []),
                 "matching_declared_calibration_sources": calibration_by_hash.get(value, [])} for value in event.get("input_sha256", [])]})
    counts = {}
    for phase, values in buckets.items():
        requests = [e for e in values if e["event"] == "embedding_started"]
        completed = [e for e in values if e["event"] == "embedding_complete"]
        counts[phase] = {"request_starts": len(requests), "input_texts_requested": sum(e["input_count"] for e in requests),
                         "completion_events": len(completed), "input_texts_completed": sum(e["input_count"] for e in completed),
                         "completion_dimensions": dict(Counter(str(e["dimensions"]) for e in completed)),
                         "request_errors": sum(e["event"] == "request_error" for e in values),
                         "inference_errors": sum(e["event"] == "embedding_error" for e in values)}
    http_checks_path = operations / "embedding-http-checks.json"
    http_checks = evidence.json(http_checks_path) if http_checks_path.exists() else None
    return {"freeze_time": freeze["frozen_at"] if freeze else None,
            "first_search_start": search_start.isoformat() if search_start else None,
            "counts_by_observed_time": counts, "request_input_hash_links": linked_requests,
            "model_loaded_events": [e for e in events if e["event"] == "model_loaded"],
            "error_events": [e for e in events if e["event"] in {"request_error", "embedding_error"}],
            "readiness_http_check_record": http_checks,
            "readiness_error_interpretation": "The separately saved HTTP check declares an intentional unknown-model negative request. Error events are retained; time alone is not a unique request linkage.",
            "scope": "Local CPU service observations, separate from subscription-backed mutation/novelty/meta requests. Time buckets are not causal attribution; source hash links establish only exact text identity. Completion records have no request ID or input hashes, so concurrent requests are not individually paired to completions. Rejected/overwritten sources may remain unlinked. No hidden/retried requests are inferred."}


def audit(root):
    evidence = Evidence(root)
    searches, receipts, hashes = [], [], []
    for index, seed in enumerate((610001, 610002, 610003)):
        result, raw, sources = audit_search(root / "evolution" / f"search_{index}_seed_{seed}", evidence)
        searches.append(result); receipts.extend(receipt_view(path, value, evidence) for path, value in raw); hashes.extend(sources)
    service = embedding_service(root, searches, hashes, evidence)
    checks = [check for search in searches for event in search.get("native_sampling", []) for check in event["saved_attempt_prompt_checks"]]
    source_checks = [source for check in checks for source in check["sources"]]
    # Existing manually reviewed audit artifacts are linked, never silently treated as new checks.
    prior = []
    for pattern in ("search0-native-machinery-audit-*.json", "search0-first-meta-injection-audit.json", "native-feedback-wording-note.json", "webui-verification.json"):
        for path in sorted((root / "operations").glob(pattern)):
            evidence.bytes(path); prior.append(evidence.label(path))
    return {"format": "joint-v3-observed-native-machinery-v1", "audited_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root), "status": "completed_search_snapshot" if all(s["status"] == "search_complete" for s in searches) else "live_partial_snapshot",
        "role_totals": role_totals(receipts), "searches": searches, "local_embedding_service": service,
        "prompt_verification_summary": {"attempt_prompts_inspected": len(checks), "source_references_checked": len(source_checks),
            "missing_source_references": [s for s in source_checks if not s.get("full_source_present")],
            "missing_feedback_references": [s for s in source_checks if not s.get("full_feedback_present")],
            "missing_frozen_context": [c["prompt"] for c in checks if not c["frozen_task_context_present"]]},
        "existing_independent_audit_artifacts": prior, "source_files_at_read": evidence.files,
        "limitations": [
            "One native wrapper invocation may request multiple logical responses. Counts do not expose internal provider retries or total transport requests.",
            "Unclosed receipts are unresolved at this snapshot, not proof that a provider request is still running. During live execution, files/SQLite snapshots are read at different instants.",
            "Native-reported model routes and configured/requested effort are retained separately. Effective provider effort is unverified; outer Astra/Ultra mode is not inferred from internal calls.",
            "Cost fields are native estimates, not billing statements. Local embedding development, readiness and search-period service observations are reported separately.",
            "Exact source/feedback matching covers retained attempt prompts. Missing prompts, formatting differences or rewritten repair contexts remain explicit coverage gaps rather than assumed matches.",
            "Meta injection is exact saved-text matching. Duplicate recommendation text can match multiple earlier artifacts, so unique text counts and all provenance matches are retained; no unobserved recommendation selection is inferred. Artifact completion times are associated by order only when event/file coverage is one-to-one; otherwise timing remains unverified.",
            "The installed native sampler injects meta recommendations for diff/full formats and omits them for crossover. Actual crossover formatting and absence of the recommendation section are recorded; configured meta use does not imply every prompt receives a recommendation.",
            "Patch-type counts cover original evaluated DB rows, not every failed/rejected patch attempt. All native retry/novelty evidence remains in saved receipts and logs.",
            "Native 'passes all validation tests' wording refers to search evaluator correctness, not the protected V3 validation suite.",
            *evidence.limitations], "candidate_objective_or_model_calls_by_auditor": 0,
        "implementation_sha256": digest(Path(__file__).read_bytes())}


def write_exclusive(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(record, indent=2, allow_nan=False) + "\n").encode()
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".machinery-audit-", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(data); handle.flush(); os.fsync(handle.fileno())
    try:
        os.link(temporary, path)  # Atomic exclusive publication; existing evidence survives.
    finally:
        temporary.unlink()


def self_test():
    totals = role_totals([{"role": "meta", "requested_logical_responses": 5, "valid_responses": 3, "status": "degraded"},
                          {"role": "meta", "requested_logical_responses": 1, "valid_responses": None, "status": "started"}])["meta"]
    assert (totals["native_wrapper_invocations"], totals["requested_logical_responses"], totals["usable_responses_returned"], totals["closed_response_shortfall"], totals["logical_responses_in_unclosed_wrappers"]) == (2, 6, 3, 2, 1)
    assert numbered_recommendations("# META RECOMMENDATIONS\nIntro\n1. First\ncontinued.\n2. Second.") == ["First\ncontinued.", "Second."]
    with tempfile.TemporaryDirectory(prefix="joint-machinery-helper-") as directory:
        path = Path(directory) / "audit.json"
        write_exclusive(path, {"retained": 1})
        try:
            write_exclusive(path, {"retained": 2})
        except FileExistsError:
            pass
        else:
            raise AssertionError("Existing audit was overwritten")
        assert json.loads(path.read_text()) == {"retained": 1}
    return {"status": "passed", "scope": "logical-vs-wrapper accounting, numbered recommendation extraction and immutable output; no research/model calls"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT / "results/joint_relocation_v3")
    parser.add_argument("--output", type=Path, help="New immutable JSON path; defaults to timestamped operations filename")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), indent=2)); return
    root = args.root.resolve()
    output = args.output or root / "operations" / ("native-machinery-audit-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ") + ".json")
    if output.exists():
        raise FileExistsError(f"Preserve existing audit: {output}")
    result = audit(root)
    write_exclusive(output, result)
    print(json.dumps({"saved": str(output), "status": result["status"], "role_totals": result["role_totals"],
                      "prompt_verification_summary": result["prompt_verification_summary"],
                      "local_embedding_counts": result["local_embedding_service"]["counts_by_observed_time"]}, indent=2))


if __name__ == "__main__":
    main()
