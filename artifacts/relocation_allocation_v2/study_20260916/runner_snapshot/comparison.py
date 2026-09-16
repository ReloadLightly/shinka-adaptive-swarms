"""Checkpointed comparison of frozen programs at matched objective budgets.

Program selection and any ablation definitions are frozen before the comparison
suite is read. Only simulator observations are passed to policies; this Python
execution boundary is not a security sandbox, so source review is still needed.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import re
import statistics
import time

import numpy as np

from .cli import load_policy, simulator_fingerprint, source_revision
from .logging import EventLogger, atomic_json
from .simulator import run_case, _validated_config
from .artifacts import read_json, resolve_json, write_compressed_json


ANALYSIS_VERSION = "paired_stratified_bootstrap_v1"
BOOTSTRAP_SEED = 20260915
BOOTSTRAP_REPLICATES = 20000
REGIME_FIELDS = ("dimension", "npeaks", "period", "move_severity", "correlation")


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _digest(value) -> str:
    return _sha256(json.dumps(value, sort_keys=True).encode())


def freeze_programs(folder: Path, selected: Path, variants: dict[str, Path],
                    selection: dict) -> dict:
    """Write the selection record without opening or evaluating the heldout suite."""
    if (folder / "manifest.json").exists() or (folder / "freeze.json").exists():
        raise ValueError(f"Run already exists: {folder}; use --resume.")
    if set(variants) & {"baseline", "selected"}:
        raise ValueError("Variant names cannot be baseline or selected.")
    for name in variants:
        if not re.fullmatch(r"[a-z][a-z0-9_]*", name):
            raise ValueError(f"Invalid variant name: {name!r}")
    sources = {"selected": selected, **variants}
    # Read all source files first so a missing variant cannot leave half a freeze.
    programs = {name: path.read_bytes() for name, path in sources.items()}
    (folder / "programs").mkdir(parents=True, exist_ok=True)
    methods = {"baseline": {"role": "fixed corrected book response",
                             "policy": None}}
    for name, content in programs.items():
        destination = folder / "programs" / f"{name}.py"
        destination.write_bytes(content)
        methods[name] = {"role": "selected native descendant" if name == "selected" else "mechanism comparison",
                         "policy": str(destination.relative_to(folder)),
                         "source_path": str(sources[name]), "sha256": _sha256(content)}
    record = {"frozen_at": datetime.now(timezone.utc).isoformat(),
              "source_revision": source_revision(), "selection": selection,
              "methods": methods, "simulator_sources": simulator_fingerprint(),
              "freeze_stage": "before comparison suite load or execution",
              "candidate_interface": "choose_response(observation) only; source inspection required because execution is not sandboxed"}
    atomic_json(folder / "freeze.json", record)
    return record


def verify_frozen_sources(folder: Path) -> dict:
    record = json.loads((folder / "freeze.json").read_text())
    if record["simulator_sources"] != simulator_fingerprint():
        raise ValueError("Simulator or corrected baseline changed after program freeze.")
    for name, method in record["methods"].items():
        if method["policy"] and _sha256((folder / method["policy"]).read_bytes()) != method["sha256"]:
            raise ValueError(f"Frozen source changed: {name}")
    return record


def load_suite(path: Path) -> tuple[str, list[dict]]:
    suite = json.loads(path.read_text())
    defaults = {key: value for key, value in suite.items()
                if key not in {"study", "cases", "description"}}
    cases = [_validated_config({**defaults, **overrides}) for overrides in suite["cases"]]
    if not cases:
        raise ValueError("Comparison suite is empty.")
    pairs = [(case["environment_seed"], case["optimizer_seed"]) for case in cases]
    if len(pairs) != len(set(pairs)):
        raise ValueError("Comparison requires unique environment/optimizer seed pairs.")
    return suite.get("study", "frozen_comparison"), cases


def _environment_hashes(case: dict) -> list[str]:
    return [case["initial_environment"]["sha256"],
            *(entry["next_environment"]["sha256"] for entry in case["environment_changes"])]


def validate_pair(reference: dict, candidate: dict) -> dict:
    """Reject unequal inputs, uncharged queries, or divergent environment histories."""
    if reference["config"] != candidate["config"]:
        raise ValueError("Paired methods used different case configurations.")
    budget = reference["config"]["budget"]
    for case in (reference, candidate):
        if case["evaluations"] != budget or sum(case["evaluation_counts"].values()) != budget:
            raise ValueError("Objective-query accounting differs from the paired budget.")
        if not math.isfinite(case["offline_error"]) or case["offline_error"] < 0:
            raise ValueError("Invalid offline-error measurement.")
    reference_hashes = _environment_hashes(reference)
    if reference_hashes != _environment_hashes(candidate):
        raise ValueError("Paired methods encountered different environmental histories.")
    return {"equal_objective_budgets": True, "matching_environment_hashes": True,
            "environment_hash_count": len(reference_hashes),
            "environment_history_sha256": _digest(reference_hashes)}


def regime_key(config: dict) -> str:
    return "; ".join(f"{key}={config[key]:g}" for key in REGIME_FIELDS)


def _paired_statistics(deltas: list[float], regimes: list[str]) -> dict:
    groups = defaultdict(list)
    for delta, regime in zip(deltas, regimes):
        groups[regime].append(delta)
    result = {"n": len(deltas), "mean_delta": statistics.mean(deltas),
              "sd_delta": statistics.stdev(deltas) if len(deltas) > 1 else None,
              "se_delta": statistics.stdev(deltas) / math.sqrt(len(deltas)) if len(deltas) > 1 else None,
              "improved_cases": sum(value < 0 for value in deltas),
              "worsened_cases": sum(value > 0 for value in deltas),
              "tied_cases": sum(value == 0 for value in deltas)}
    if all(len(group) > 1 for group in groups.values()):
        rng = np.random.default_rng(BOOTSTRAP_SEED)
        means = np.zeros(BOOTSTRAP_REPLICATES)
        variance = 0.0
        for group in groups.values():
            values = np.asarray(group)
            means += rng.choice(values, size=(BOOTSTRAP_REPLICATES, len(group))).sum(axis=1) / len(deltas)
            variance += (len(group) / len(deltas)) ** 2 * statistics.variance(group) / len(group)
        result["stratified_se_delta"] = math.sqrt(variance)
        result["bootstrap_95_percent_interval"] = np.quantile(means, [.025, .975]).tolist()
    else:
        result["stratified_se_delta"] = None
        result["bootstrap_95_percent_interval"] = None
    return result


def behavior_summary(cases: list[dict]) -> dict:
    responses = [response for case in cases for response in case["response_log"]]
    evaluations = sum(case["evaluations"] for case in cases)
    keys = sorted({key for case in cases for key in case["evaluation_counts"]})
    return {"response_count": len(responses),
            "mean_radius_scale": statistics.mean(r["decision"]["radius_scale"] for r in responses) if responses else None,
            "mean_relocated_fraction": statistics.mean(len(r["relocated_indices"]) / r["observation"]["swarm_size"] for r in responses) if responses else None,
            "memory_reset_response_fraction": statistics.mean(r["decision"]["memory"] == "reset" for r in responses) if responses else None,
            "velocity_reset_response_fraction": statistics.mean(r["decision"]["reset_velocity"] for r in responses) if responses else None,
            "evaluation_shares": {key: sum(c["evaluation_counts"].get(key, 0) for c in cases) / evaluations for key in keys},
            "note": "Descriptive pooled responses and evaluation use; responses are not independent replications."}


def summarize(outcomes: dict[str, list[dict]], total_cases: int) -> dict:
    methods = list(outcomes)
    count = min(map(len, outcomes.values()))
    reference = outcomes["baseline"][:count]
    regimes = [regime_key(case["config"]) for case in reference]
    comparisons = {}
    pairs = [(method, "baseline") for method in methods if method != "baseline"]
    pairs += [(method, "selected") for method in methods if method not in {"baseline", "selected"}]
    for method, comparator in pairs:
        current, control = outcomes[method][:count], outcomes[comparator][:count]
        checks = [validate_pair(a, b) for a, b in zip(control, current)]
        deltas = [b["offline_error"] - a["offline_error"] for a, b in zip(control, current)]
        groups = {}
        for regime in dict.fromkeys(regimes):
            group_deltas = [delta for delta, key in zip(deltas, regimes) if key == regime]
            indices = [i for i, key in enumerate(regimes) if key == regime]
            groups[regime] = {**_paired_statistics(group_deltas, [regime] * len(group_deltas)),
                             "mean_method_error": statistics.mean(current[i]["offline_error"] for i in indices),
                             "mean_comparator_error": statistics.mean(control[i]["offline_error"] for i in indices)}
        comparisons[f"{method}_minus_{comparator}"] = {
            "method": method, "comparator": comparator,
            "sign": "negative favors method; positive favors comparator",
            **_paired_statistics(deltas, regimes), "regimes": groups,
            "cases": [{"case_index": i, "environment_seed": b["config"]["environment_seed"],
                       "optimizer_seed": b["config"]["optimizer_seed"], "regime": regimes[i],
                       "method_offline_error": b["offline_error"], "comparator_offline_error": a["offline_error"],
                       "delta": delta, **check}
                      for i, (a, b, delta, check) in enumerate(zip(control, current, deltas, checks))]}
    return {"status": "completed" if count == total_cases else "partial", "paired_case_count": count,
            "planned_case_count": total_cases, "completed_method_cases": {name: len(cases) for name, cases in outcomes.items()},
            "method_mean_offline_errors": {name: statistics.mean(case["offline_error"] for case in cases[:count])
                                          for name, cases in outcomes.items()},
            "comparisons": comparisons,
            "behavior": {name: behavior_summary(cases[:count]) for name, cases in outcomes.items()},
            "uncertainty": {"analysis_version": ANALYSIS_VERSION,
                            "method": "95% percentile bootstrap of paired case differences, resampling within regimes and retaining the suite's regime weights",
                            "bootstrap_replicates": BOOTSTRAP_REPLICATES, "analysis_rng_seed": BOOTSTRAP_SEED,
                            "interpretation": "The pooled effect describes this fixed mixture of regimes. With only two cases per regime, uncertainty estimates are unstable and cannot establish broad generalization. No checkpoint or response is counted as an independent case.",
                            "se_delta": "Ordinary standard error across paired cases; stratified_se_delta instead conditions on the fixed regime mixture."}}


def run_comparison(folder: Path, suite_path: Path, resume: bool = False) -> dict:
    frozen = verify_frozen_sources(folder)
    study, cases = load_suite(suite_path)
    signature = _digest({"freeze": frozen, "cases": cases, "analysis_version": ANALYSIS_VERSION})
    manifest_path = folder / "manifest.json"
    if manifest_path.exists():
        if not resume:
            raise ValueError("Comparison already started; use --resume.")
        manifest = json.loads(manifest_path.read_text())
        if manifest["signature"] != signature:
            raise ValueError("Resume configuration or program provenance differs from saved run.")
    else:
        manifest = {"study": study, "signature": signature, "source_revision": source_revision(),
                    "python": platform.python_version(), "suite_source": str(suite_path),
                    "suite_sha256": _sha256(suite_path.read_bytes()), "cases": cases,
                    "frozen_at": frozen["frozen_at"], "comparison_started_at": datetime.now(timezone.utc).isoformat(),
                    "methods": frozen["methods"], "simulator_sources": frozen["simulator_sources"]}
    manifest["status"] = "running"
    atomic_json(manifest_path, manifest)
    outcomes = {name: [] for name in frozen["methods"]}
    summary = None
    try:
        with EventLogger(folder) as log:
            log.event("comparison_started", study=study, cases=len(cases), methods=list(outcomes),
                      frozen_at=frozen["frozen_at"], directory=str(folder))
            for index, config in enumerate(cases):
                for method, metadata in frozen["methods"].items():
                    case_path = resolve_json(folder / method / f"case_{index:03d}.json")
                    if resume and case_path.exists():
                        result = read_json(case_path)
                        if result.get("signature") != signature or result["config"] != config:
                            raise ValueError(f"Saved case provenance differs: {case_path}")
                        log.event("case_reused", method=method, case=index + 1, offline_error=result["offline_error"])
                    else:
                        verify_frozen_sources(folder)
                        log.set_activity(f"{method}, independent case {index + 1}/{len(cases)}")
                        log.event("case_started", method=method, case=index + 1, budget=config["budget"],
                                  completed_method_cases=sum(map(len, outcomes.values())),
                                  environment_seed=config["environment_seed"], optimizer_seed=config["optimizer_seed"])
                        def progress(event):
                            event = dict(event)
                            kind = event.pop("event", "simulation_progress")
                            # Config and latent environment remain in the evaluator, never in policy arguments.
                            event.pop("config", None)
                            log.event(kind, method=method, case=index + 1, **event)
                        start = time.monotonic()
                        policy = load_policy(folder / metadata["policy"]) if metadata["policy"] else None
                        result = run_case(config, policy=policy, progress=progress)
                        result.update(signature=signature, method=method, case_index=index,
                                      wall_time_seconds=time.monotonic() - start,
                                      policy_source_sha256=metadata.get("sha256"))
                        # Checkpoint immediately even if later pairing validation reveals a problem.
                        case_path = write_compressed_json(case_path, result)
                        log.event("case_completed", method=method, case=index + 1,
                                  offline_error=result["offline_error"], checkpoint=str(case_path),
                                  wall_time_s=result["wall_time_seconds"])
                    validate_pair(result, result)
                    if method != "baseline":
                        validate_pair(outcomes["baseline"][index], result)
                    outcomes[method].append(result)
                summary = summarize(outcomes, len(cases))
                atomic_json(folder / "summary.json", summary)
                log.event("pair_completed", case=index + 1, total_cases=len(cases),
                          selected_minus_baseline=summary["comparisons"]["selected_minus_baseline"]["cases"][-1]["delta"])
            manifest["status"] = "completed"
            manifest["completed_at"] = datetime.now(timezone.utc).isoformat()
            atomic_json(manifest_path, manifest)
            log.event("comparison_completed", paired_cases=len(cases),
                      method_mean_offline_errors=summary["method_mean_offline_errors"],
                      selected_minus_baseline=summary["comparisons"]["selected_minus_baseline"]["mean_delta"])
    except BaseException as exc:
        manifest["status"] = "interrupted_or_failed"
        manifest["completed_method_cases"] = {name: len(values) for name, values in outcomes.items()}
        manifest["last_error"] = f"{type(exc).__name__}: {exc}"
        atomic_json(manifest_path, manifest)
        raise
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True, help="New comparison directory, or existing directory with --resume")
    parser.add_argument("--config", type=Path, default=Path("configs/heldout.json"))
    parser.add_argument("--program", type=Path, help="Native selected source, frozen before comparison suite load")
    parser.add_argument("--selection-note", help="Search-only selection reason and native program identity")
    parser.add_argument("--selection-record", type=Path, help="Optional JSON with native lineage and source review")
    parser.add_argument("--variant", action="append", default=[], metavar="NAME=PATH", help="Mechanism comparison, frozen with selected program")
    parser.add_argument("--variant-note", default="", help="Mechanism question and how each variant changes the selected program")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--figures", type=Path, help="Render comparison figures to this directory after completion")
    args = parser.parse_args()
    if not args.resume:
        if args.program is None or not args.selection_note:
            parser.error("New comparison requires --program and --selection-note.")
        variants = {}
        for item in args.variant:
            name, separator, path = item.partition("=")
            if not separator or not path or name in variants:
                parser.error("Use unique --variant NAME=PATH entries.")
            variants[name] = Path(path)
        selection = {"reason": args.selection_note, "variant_note": args.variant_note}
        if args.selection_record:
            selection["native_record"] = json.loads(args.selection_record.read_text())
        freeze_programs(args.run, args.program, variants, selection)
    elif args.program or args.variant or args.selection_record:
        parser.error("Resume uses the existing frozen programs; omit new selection inputs.")
    summary = run_comparison(args.run, args.config, resume=args.resume)
    if args.figures:
        from .comparison_figures import render_comparison
        render_comparison(args.run, args.figures)
    print(json.dumps({"run": str(args.run), "status": summary["status"],
                      "paired_cases": summary["paired_case_count"],
                      "selected_minus_baseline": summary["comparisons"]["selected_minus_baseline"]["mean_delta"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
