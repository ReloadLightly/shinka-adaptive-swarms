#!/usr/bin/env python3
"""Recompute V3 paired statistics from saved cases without writing any artifact.

This checks reproducibility with the registered analysis functions; it is not an
independent statistical implementation. It never imports or invokes candidates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from adaptive_swarms.artifacts import read_json
from adaptive_swarms.comparison import validate_pair
from adaptive_swarms.joint_study import (assert_cases, contrast_record, equal_regime_mean,
                                         load_stage_outcomes, verify_review)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_match(actual, expected, location="analysis"):
    """Check every recomputed field, allowing saved descriptive metadata."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            raise ValueError(f"Expected a mapping at {location}")
        for key, value in expected.items():
            if key not in actual:
                raise ValueError(f"Missing saved field: {location}.{key}")
            require_match(actual[key], value, f"{location}.{key}")
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise ValueError(f"Saved list length differs: {location}")
        for index, (left, right) in enumerate(zip(actual, expected)):
            require_match(left, right, f"{location}[{index}]")
    elif isinstance(expected, float):
        if not isinstance(actual, (float, int)) or isinstance(actual, bool) or not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError(f"Saved numeric result differs: {location}")
    elif actual != expected or type(actual) is not type(expected):
        raise ValueError(f"Saved value differs: {location}")


def recompute_statistics(selection, manifest, outcomes):
    overall = selection["overall_winner_method"]
    errors = {name: [case["offline_error"] for case in values] for name, values in outcomes.items()}
    comparisons = {}
    pairs = [(winner["method"], comparator) for winner in selection["per_search_winners"] for comparator in ("baseline", "best_fixed")]
    pairs += [(overall, comparator) for comparator in ("radius_replaced", "count_replaced", "joint_sampler")]
    for method, comparator in pairs:
        primary = method == overall and comparator in {"baseline", "best_fixed"}
        deltas = [left - right for left, right in zip(errors[method], errors[comparator])]
        comparisons[f"{method}_minus_{comparator}"] = {
            "method": method, "comparator": comparator,
            "role": "primary" if primary else "descriptive secondary",
            "sign": "negative favors named method",
            **contrast_record(deltas, manifest["cases"], .975 if primary else .95, errors[method], errors[comparator])}
    deltas = [e - radius - count + fixed for e, radius, count, fixed in zip(
        errors[overall], errors["radius_replaced"], errors["count_replaced"], errors["best_fixed"])]
    interaction = {"expression": "E - radius_replaced - count_replaced + best_fixed",
                   "role": "descriptive closed-loop component interaction",
                   **contrast_record(deltas, manifest["cases"], .95)}
    primary = [key for key, value in comparisons.items() if value["role"] == "primary"]
    claim = all(comparisons[key]["bootstrap_interval"] is not None and comparisons[key]["bootstrap_interval"][1] < 0 for key in primary)
    return {"status": "completed", "paired_case_count": len(manifest["cases"]),
            "overall_winner_method": overall,
            "method_mean_offline_errors": {name: equal_regime_mean(values) for name, values in outcomes.items()},
            "comparisons": comparisons, "interaction": interaction,
            "claim": {"superiority_over_both_primary_controls_supported": claim,
                      "rule": selection["analysis"]["claim_rule"], "primary_contrasts": primary},
            "aliases": manifest["aliases"], "uncertainty": selection["analysis"],
            "execution_accounting": {"final_unique_method_cases": len({path for paths in manifest["case_artifacts"].values() for path in paths}),
                                     "final_nominal_methods": len(outcomes)}}


def check_analysis(folder):
    folder = Path(folder).resolve()
    verify_review(folder)
    registration = read_json(folder / "registration.json")
    selection = read_json(folder / "selection.json")
    analysis = read_json(folder / "analysis.json")
    validation = read_json(folder / "validation/manifest.json")
    provenance = {"shortlists_sha256": sha(folder / "shortlists.json"),
                  "validation_signature": validation["signature"],
                  "validation_summary_sha256": sha(folder / "validation/summary.json")}
    if selection["provenance"] != provenance or selection["analysis"] != registration["analysis"]:
        raise ValueError("Frozen selection or analysis specification no longer matches validation/registration.")
    if analysis["selection"] != selection:
        raise ValueError("Saved analysis embeds a different frozen selection.")
    manifest, outcomes = load_stage_outcomes(folder, "final")
    assert_cases(manifest["cases"], 20)
    if manifest["freeze_sha256"] != sha(folder / "selection.json") or manifest["methods"] != selection["methods"]:
        raise ValueError("Saved final methods differ from the frozen selection.")
    if manifest["cases"] != read_json(folder / "final_cases.json")["cases"]:
        raise ValueError("Saved final cases differ from the frozen final suite.")
    pairing = {name: [validate_pair(reference, case) for reference, case in zip(outcomes["baseline"], values)]
               for name, values in outcomes.items()}
    require_match(analysis["pairing_checks"], pairing, "pairing_checks")
    expected = recompute_statistics(selection, manifest, outcomes)
    if set(analysis["comparisons"]) != set(expected["comparisons"]):
        raise ValueError("Saved comparison set differs from the frozen analysis plan.")
    require_match(analysis, expected)
    return {"status": "passed", "study": str(folder), "paired_case_count": 80,
            "comparisons_checked": len(expected["comparisons"]), "interaction_checked": True,
            "bootstrap_resamples": selection["analysis"]["bootstrap_resamples"],
            "analysis_seed": selection["analysis"]["analysis_seed"],
            "analysis_sha256": sha(folder / "analysis.json"), "registration_sha256": sha(folder / "registration.json"),
            "interpretation": "Recomputed frozen analysis functions on saved paired cases, including means, regime effects, standard errors, intervals and the primary claim; not an independent statistical implementation.",
            "original_search_directories_required": False,
            "simulations_launched": 0, "model_calls_launched": 0, "artifact_writes": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True, help="Completed live or archived study directory")
    print(json.dumps(check_analysis(parser.parse_args().run), indent=2), flush=True)
