#!/usr/bin/env python3
"""Small, saved-data-only radius/velocity sprint analysis; no objective calls.

Phase A has eight balanced development cases and six frozen methods. The pilot
has two frozen methods ordered as selected, comparator in its own manifest.
All error effects are computed within case before descriptive aggregation.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from adaptive_swarms.allocation_figures import recovery_case_curve
from adaptive_swarms.artifacts import read_json, resolve_json
from adaptive_swarms.comparison import validate_pair
from adaptive_swarms.figures import _save, _style
from adaptive_swarms.logging import atomic_json
from adaptive_swarms.simulator import _validated_config

METHODS = ("c4_r1_retain", "c4_r1p5_retain", "c4_r1_reset", "c4_r1p5_reset", "baseline", "v3_selected")
LABELS = dict(zip(METHODS, ("4 / 1 / retain", "4 / 1.5 / retain", "4 / 1 / reset", "4 / 1.5 / reset", "Original baseline", "Frozen V3 policy")))
COLORS = ("#187b80", "#d47b34", "#7057a3", "#bb4260", "#477ab2", "#697988")
PILOT_BOOTSTRAP_SEED = 2026091605
PILOT_BOOTSTRAP_RESAMPLES = 2000


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def regime(config):
    return f"severity={config['move_severity']:g};period={config['period']}"


def describe(values):
    values = [float(value) for value in values]
    if not values or not all(np.isfinite(values)):
        raise ValueError("Expected nonempty finite saved measurements")
    return {"n": len(values), "mean": statistics.mean(values),
            "sd": statistics.stdev(values) if len(values) > 1 else None,
            "min": min(values), "max": max(values), "values": values}


def paired_effect(values, configs, *, pilot=False):
    groups = defaultdict(list)
    for value, config in zip(values, configs, strict=True):
        groups[regime(config)].append(float(value))
    result = {**describe(values), "regimes": {key: describe(group) for key, group in sorted(groups.items())}}
    result["equal_regime_mean"] = statistics.mean(statistics.mean(group) for group in groups.values())
    result["improved_cases"] = sum(value < 0 for value in values)
    result["worsened_cases"] = sum(value > 0 for value in values)
    result["tied_cases"] = sum(value == 0 for value in values)
    if pilot:
        rng = np.random.default_rng(PILOT_BOOTSTRAP_SEED)
        resamples = np.zeros(PILOT_BOOTSTRAP_RESAMPLES)
        for _, group in sorted(groups.items()):
            resamples += rng.choice(group, (PILOT_BOOTSTRAP_RESAMPLES, len(group))).mean(axis=1) / len(groups)
        result["descriptive_bootstrap_95_percent_interval"] = np.quantile(resamples, [.025, .975]).tolist()
    return result


def phase_a_effects(errors, configs):
    pairs = {f"{method}_minus_baseline": (method, "baseline") for method in METHODS if method != "baseline"}
    pairs.update({"radius_effect_retain": ("c4_r1p5_retain", "c4_r1_retain"),
                  "radius_effect_reset": ("c4_r1p5_reset", "c4_r1_reset"),
                  "reset_effect_radius_1": ("c4_r1_reset", "c4_r1_retain"),
                  "reset_effect_radius_1p5": ("c4_r1p5_reset", "c4_r1p5_retain"),
                  "v3_minus_direct_constant_4_1p5": ("v3_selected", "c4_r1p5_retain")})
    effects = {name: {"method": method, "comparator": control,
                      **paired_effect([a - b for a, b in zip(errors[method], errors[control], strict=True)], configs)}
               for name, (method, control) in pairs.items()}
    interaction = [(reset15 - reset1) - (retain15 - retain1)
                   for reset15, reset1, retain15, retain1 in zip(
                       errors["c4_r1p5_reset"], errors["c4_r1_reset"],
                       errors["c4_r1p5_retain"], errors["c4_r1_retain"], strict=True)]
    effects["radius_by_velocity_interaction"] = {
        "expression": "(r1.5_reset - r1_reset) - (r1.5_retain - r1_retain)",
        "interpretation": "Negative: increasing radius is more beneficial / less harmful with reset; not evidence of an overshoot mediator.",
        **paired_effect(interaction, configs)}
    return effects


def action_summary(case):
    counts = Counter()
    for response in case["response_log"]:
        decision = response["decision"]
        if decision["memory"] != "reevaluate":
            raise ValueError("Personal-best memory reevaluation was not fixed")
        count = len(response["relocated_indices"])
        if len(set(response["relocated_indices"])) != count or count > response["observation"]["swarm_size"]:
            raise ValueError("Invalid relocated particle allocation")
        if "requested_count" in response and response["requested_count"] != count:
            raise ValueError("Requested count disagrees with allocated count")
        counts[(count, float(decision["radius_scale"]), bool(decision["reset_velocity"]))] += 1
    total = sum(counts.values())
    return {"response_count": total,
            "incomplete_responses": sum(not row["completed"] for row in case["response_log"]),
            "joint_actions": [{"count": count, "radius_scale": radius, "reset_velocity": reset,
                               "responses": number, "probability": number / total}
                              for (count, radius, reset), number in sorted(counts.items())],
            "note": "Allocation counts include a final budget-truncated response; selected particles may not all receive their relocation evaluation."}


def mean_actions(summaries):
    probability = defaultdict(float)
    observed = [summary for summary in summaries if summary["response_count"]]
    for summary in observed:
        for row in summary["joint_actions"]:
            probability[(row["count"], row["radius_scale"], row["reset_velocity"])] += row["probability"] / len(observed)
    return {"equal_case_joint_actions": [{"count": count, "radius_scale": radius, "reset_velocity": reset,
                                         "probability": value}
                                        for (count, radius, reset), value in sorted(probability.items())],
            "no_response_cases": len(summaries) - len(observed),
            "pooled_response_count": sum(summary["response_count"] for summary in summaries)}


def aggregate_recovery(curves):
    values = defaultdict(list)
    for curve in curves:
        for offset, row in curve["offsets"].items():
            values[int(offset)].append(row["mean_current_error"])
    return [{"query_offset": offset, "mean_current_error": statistics.mean(rows),
             "sd_between_case_means": statistics.stdev(rows) if len(rows) > 1 else None,
             "contributing_cases": len(rows)} for offset, rows in sorted(values.items())]


def load_outcomes(run, phase):
    manifest_path = run / phase / "manifest.json"
    if phase == "phase_a" and not manifest_path.exists():
        manifest_path = run / "manifest.json"
    manifest = read_json(manifest_path)
    configs = [_validated_config(config) for config in manifest["cases"]]
    if len(configs) != 8 or Counter((c["move_severity"], c["period"]) for c in configs) != Counter({(1., 2500): 2, (1., 5000): 2, (3., 2500): 2, (3., 5000): 2}):
        raise ValueError("Sprint analysis requires eight balanced cases across the four specified regimes")
    if any(c["budget"] != 100000 or c["dimension"] != 5 or c["npeaks"] != 10 for c in configs):
        raise ValueError("Unexpected sprint budget, dimension or peak count")
    if len({(c["environment_seed"], c["optimizer_seed"]) for c in configs}) != 8:
        raise ValueError("Repeated environment/optimizer case identities")
    methods = list(manifest["methods"])
    if phase == "phase_a" and methods != list(METHODS):
        raise ValueError("Phase A requires the six declared methods in their frozen order")
    if phase == "pilot" and len(methods) != 2:
        raise ValueError("Pilot manifest must order exactly two methods: selected, comparator")
    outcomes, inputs, checks = {}, {}, {}
    for method in methods:
        outcomes[method] = []
        for index, config in enumerate(configs):
            path = resolve_json(run / phase / method / f"case_{index:03d}.json")
            case = read_json(path)
            if case["config"] != config:
                raise ValueError(f"Saved case differs from frozen configuration: {method}/{index}")
            reference = case if method == methods[0] else outcomes[methods[0]][index]
            checks[f"{method}/{index}"] = validate_pair(reference, case)
            outcomes[method].append(case)
            inputs[str(path.relative_to(run))] = sha(path)
    return configs, methods, outcomes, inputs, checks, manifest_path


def analyze(run, phase, output=None):
    run = Path(run)
    configs, methods, outcomes, inputs, checks, manifest_path = load_outcomes(run, phase)
    errors = {method: [case["offline_error"] for case in cases] for method, cases in outcomes.items()}
    summaries, recovery = {}, {}
    for method, cases in outcomes.items():
        summaries[method], curves = [], []
        for index, case in enumerate(cases):
            curve = recovery_case_curve(case)
            curves.append(curve)
            summaries[method].append({"case_index": index, "environment_seed": case["config"]["environment_seed"],
                "optimizer_seed": case["config"]["optimizer_seed"], "regime": regime(case["config"]),
                "offline_error": case["offline_error"], "actions": action_summary(case),
                "evaluation_counts": case["evaluation_counts"],
                "query_shares": {key: number / case["evaluations"] for key, number in case["evaluation_counts"].items()},
                "recovery": curve})
        recovery[method] = {key: aggregate_recovery([curve for curve, config in zip(curves, configs, strict=True) if regime(config) == key]) for key in sorted({regime(c) for c in configs})}
    effects = phase_a_effects(errors, configs) if phase == "phase_a" else {
        "selected_minus_comparator": {"method": methods[0], "comparator": methods[1],
            **paired_effect([a - b for a, b in zip(errors[methods[0]], errors[methods[1]], strict=True)], configs, pilot=True)}}
    result = {"phase": phase, "status": "completed", "analyzed_at": datetime.now(timezone.utc).isoformat(),
              "methods": methods, "configs": configs, "paired_case_count": 8,
              "method_errors": {method: describe(values) for method, values in errors.items()},
              "paired_effects": effects, "cases": summaries, "recovery_by_regime": recovery,
              "behavior": {method: mean_actions([row["actions"] for row in summaries[method]]) for method in methods},
              "query_category_totals": {method: dict(sum((Counter(case["evaluation_counts"]) for case in cases), Counter())) for method, cases in outcomes.items()},
              "pair_checks": checks, "manifest_sha256": sha(manifest_path), "source_sha256": sha(__file__), "input_sha256": inputs,
              "interpretation": "Eight independent paired histories, two per regime; exploratory complete closed-loop methods. Dots/SD/range describe dispersion, not a significance gate. An outcome interaction does not identify overshoot.",
              "recovery_definition": "Actual saved query offsets ((evaluation-1) % period)+1; initial environment excluded. Average environments within case, then cases equally. A boundary query belongs to the completed environment. No interpolation or unrecorded immediate post-change error.",
              "pilot_uncertainty": ({"resamples": PILOT_BOOTSTRAP_RESAMPLES, "seed": PILOT_BOOTSTRAP_SEED,
                  "method": "95% percentile paired bootstrap resampling two histories within each regime with equal regime weights; unstable at this sample size, descriptive only."} if phase == "pilot" else None)}
    output = Path(output) if output else run / phase
    output.mkdir(parents=True, exist_ok=True)
    atomic_json(output / "analysis.json", result)
    with (output / "paired_effects.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["case_index", "environment_seed", "optimizer_seed", "regime", *effects])
        for index, config in enumerate(configs):
            writer.writerow([index, config["environment_seed"], config["optimizer_seed"], regime(config), *(value["values"][index] for value in effects.values())])
    render(result, output)
    return result


def render(result, output):
    _style()
    fig, axes = plt.subplots(2, 2, figsize=(12.8, 8.5), constrained_layout=True)
    phase_a = result["phase"] == "phase_a"
    effect = result["paired_effects"]["radius_by_velocity_interaction" if phase_a else "selected_minus_comparator"]
    for index, (group, summary) in enumerate(effect["regimes"].items()):
        y = 4 - index
        axes[0, 0].scatter(summary["values"], y + np.linspace(-.08, .08, summary["n"]), color=COLORS[index], s=35)
        axes[0, 0].scatter(summary["mean"], y, marker="D", color="#243447", s=45)
    axes[0, 0].scatter(effect["mean"], 0, marker="D", color="#243447", s=65)
    axes[0, 0].set_yticks([4, 3, 2, 1, 0], [*(key.replace(";", "\n") for key in effect["regimes"]), "Equal-regime mean"])
    axes[0, 0].axvline(0, color="#8796a5", ls="--", lw=1)
    axes[0, 0].set(title="Radius × velocity interaction" if phase_a else "Frozen selected − comparator", xlabel="Paired offline-error interaction" if phase_a else "Paired offline-error difference")
    control = "baseline" if phase_a else result["methods"][1]
    control_errors = result["method_errors"][control]["values"]
    for index, method in enumerate(result["methods"]):
        values = [a - b for a, b in zip(result["method_errors"][method]["values"], control_errors, strict=True)]
        axes[0, 1].scatter(values, index + np.linspace(-.12, .12, len(values)), color=COLORS[index], s=20, alpha=.72)
        axes[0, 1].scatter(statistics.mean(values), index, color="#243447", marker="D", s=48)
    axes[0, 1].set_yticks(range(len(result["methods"])), [LABELS.get(method, method) for method in result["methods"]])
    axes[0, 1].axvline(0, color="#8796a5", ls="--", lw=1)
    axes[0, 1].set(title="All case effects retained", xlabel=f"Offline error − {'original baseline' if phase_a else control}\nNegative favors named method")
    for ax, period in zip(axes[1], (2500, 5000)):
        for index, method in enumerate(result["methods"]):
            curves = [row["recovery"] for row, config in zip(result["cases"][method], result["configs"], strict=True) if config["period"] == period]
            values = aggregate_recovery(curves)
            ax.plot([row["query_offset"] for row in values], [row["mean_current_error"] for row in values], color=COLORS[index], lw=1.45,
                    linestyle="--" if method.endswith("reset") else "-", label=LABELS.get(method, method))
        ax.set(title=f"Measured recovery · period {period:,}", xlabel="Actual query offset after change", ylabel="Best-discovered error (mean)")
    axes[1, 1].legend(frameon=False, fontsize=8, ncol=2)
    for ax in axes.flat:
        ax.grid(alpha=.16)
    fig.suptitle(f"Radius / velocity {'mechanism diagnostic' if phase_a else 'exploratory transfer probe'} · 5D · 8 paired histories", fontsize=14)
    fig.supxlabel("Dots: individual paired cases; diamonds: means. Recovery averages environments within case, then cases; no inferred immediate response.\n"
                  "Both severities have equal weight within each period. Outcome interactions alone do not demonstrate overshoot.", fontsize=9)
    stem = "interaction_recovery" if phase_a else "pilot_effect_recovery"
    _save(fig, output / stem)
    atomic_json(output / "figure_provenance.json", {"analysis_sha256": sha(output / "analysis.json"),
        "source_sha256": sha(__file__), "dimension": 5, "cases": 8, "measurements_only": True,
        "files": {f"{stem}.{extension}": sha(output / f"{stem}.{extension}") for extension in ("png", "svg")}})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    phases = parser.add_mutually_exclusive_group(required=True)
    phases.add_argument("--phase-a", action="store_true")
    phases.add_argument("--pilot", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyze(args.run, "phase_a" if args.phase_a else "pilot", args.output)
    print(json.dumps({"phase": result["phase"], "method_errors": result["method_errors"], "paired_effects": result["paired_effects"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
