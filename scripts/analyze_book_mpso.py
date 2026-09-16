#!/usr/bin/env python3
"""Analyze saved chapter-aligned MPSO cases without objective or model calls."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
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
from adaptive_swarms.engine_progress import terminal_failure_generations
from adaptive_swarms.figures import _save, _style
from adaptive_swarms.logging import atomic_json
from adaptive_swarms.simulator import _validated_config

SPEC_PATH = ROOT / "docs/studies/book_mpso_schedule_v1/analysis_specification.json"
METHODS = ("mpso_5_0", "mpso_5_1", "selected")
LABELS = {"mpso_5_0": "Reconstructed MPSO 5+0", "mpso_5_1": "Reconstructed MPSO 5+1", "selected": "Selected native schedule"}
COLORS = {"mpso_5_0": "#8796a5", "mpso_5_1": "#d47b34", "selected": "#187b80"}
AGE_BINS = ("never_detected", "0", "1", "2-3", "4-7", "8-15", "16-31", "32+")
MOVEMENT_TYPES = ("ordinary", "temporary_quantum", "permanent_quantum")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def describe(values):
    values = [float(value) for value in values]
    if not values or not all(math.isfinite(value) for value in values):
        raise ValueError("Expected nonempty finite saved measurements")
    return {"n": len(values), "mean": statistics.mean(values), "median": statistics.median(values),
            "sd": statistics.stdev(values) if len(values) > 1 else None,
            "min": min(values), "max": max(values), "values": values}


def paired_effect(deltas, spec):
    values = np.asarray(deltas, dtype=float)
    settings = spec["bootstrap"]
    rng = np.random.default_rng(settings["seed"])
    samples = rng.choice(values, size=(settings["resamples"], len(values))).mean(axis=1)
    biggest = int(np.argmax(np.abs(values)))
    net = float(values.sum())
    return {**describe(values), "descriptive_95_percent_interval": np.quantile(samples, [.025, .975]).tolist(),
            "wins": int(np.sum(values < 0)), "losses": int(np.sum(values > 0)), "ties": int(np.sum(values == 0)),
            "leave_one_case_out_means": [float(np.delete(values, index).mean()) for index in range(len(values))],
            "largest_absolute_case_contribution": {"case_index": biggest, "difference": float(values[biggest]),
                "contribution_to_mean": float(values[biggest] / len(values)),
                "fraction_of_net_effect": float(values[biggest] / net) if net else None,
                "retained": True}}


def configs_from(path):
    manifest = read_json(path)
    if isinstance(manifest, list):
        rows, defaults = manifest, {}
    else:
        rows = manifest["cases"]
        defaults = {key: value for key, value in manifest.items() if key in _validated_config({})}
    configs = [_validated_config({**defaults, **row}) for row in rows]
    if len(configs) != 8 or len({(c["environment_seed"], c["optimizer_seed"]) for c in configs}) != 8:
        raise ValueError("Expected eight distinct paired cases")
    required = {"budget": 500000, "dimension": 5, "npeaks": 10, "move_severity": 1., "period": 5000, "correlation": 0.}
    if any(any(config[key] != value for key, value in required.items()) for config in configs):
        raise ValueError("Saved suite is not the frozen chapter-aligned scenario")
    return configs


def find_case_manifest(run, phase):
    options = ([run / "development_cases.json", run / "development_suite.json", run / "search_suite.json"]
               if phase == "development" else [run / "fresh/manifest.json", run / "fresh/cases.json"])
    return next((path for path in options if path.exists()), options[0])


def load_cases(folder, configs, input_hashes, run):
    values = []
    for index, config in enumerate(configs):
        path = resolve_json(folder / f"case_{index:03d}.json")
        case = read_json(path)
        if case["config"] != config:
            raise ValueError(f"Saved configuration differs from frozen suite: {path}")
        validate_pair(case, case)
        input_hashes[str(path.relative_to(run))] = sha(path)
        values.append(case)
    return values


def summarize_behavior(cases):
    result = []
    for case in cases:
        stats = case["schedule_stats"]
        updates = stats["updates"]
        histogram = [stats["count_histogram"].get(str(k), 0) for k in range(6)]
        if sum(histogram) != updates:
            raise ValueError("Saved schedule histogram does not cover every requested update")
        requested = sum(k * number for k, number in enumerate(histogram))
        if requested != stats["requested_neutral_conversions"]:
            raise ValueError("Schedule conversion accounting mismatch")
        bins = {}
        for key in AGE_BINS:
            row = stats["age_bins"].get(key, {})
            number = row.get("updates", 0)
            bins[key] = {**row, "mean_count": row.get("neutral_conversions", 0) / number if number else None}
        improvements = case.get("shared_best_improvements", stats.get("shared_best_improvements"))
        if improvements is None:
            raise ValueError("Missing ordinary/quantum shared-best contribution measurements")
        result.append({"updates": updates, "completed_updates": stats["completed_updates"],
            "detected_change_updates": stats["detected_change_updates"],
            "count_probabilities": [number / updates for number in histogram],
            "neutral_conversion_fraction": requested / (5 * updates),
            "requested_neutral_conversions": requested, "age_bins": bins,
            "shared_best_improvements": improvements,
            "query_category_shares": {key: count / case["evaluations"] for key, count in case["evaluation_counts"].items()}})
    age = {}
    for key in AGE_BINS:
        rows = [value["age_bins"][key]["mean_count"] for value in result if value["age_bins"][key]["mean_count"] is not None]
        age[key] = {"mean_count": statistics.mean(rows) if rows else None,
                    "case_mean_counts": rows, "contributing_cases": len(rows),
                    "pooled_updates": sum(value["age_bins"][key].get("updates", 0) for value in result)}
    improvements = {}
    for role in MOVEMENT_TYPES:
        counts = [value["shared_best_improvements"].get(role, {}).get("count", 0) for value in result]
        gains = [value["shared_best_improvements"].get(role, {}).get("total_gain", 0.) for value in result]
        queries = [case["evaluation_counts"].get(role, 0) for case in cases]
        improvements[role] = {"improvement_count": sum(counts), "total_gain": sum(gains), "queries": sum(queries),
            "mean_case_improvements_per_1000_queries": statistics.mean(1000 * c / q if q else 0 for c, q in zip(counts, queries)),
            "mean_case_gain_per_1000_queries": statistics.mean(1000 * g / q if q else 0 for g, q in zip(gains, queries))}
    return {"cases": result, "updates": sum(row["updates"] for row in result),
            "equal_case_count_probabilities": np.mean([row["count_probabilities"] for row in result], axis=0).tolist(),
            "equal_case_neutral_conversion_fraction": statistics.mean(row["neutral_conversion_fraction"] for row in result),
            "age_bins": age, "shared_best_improvements": improvements,
            "interpretation": "Actions and improvement attribution describe reached trajectories; update/particle observations are not independent replications or feature-level causal effects."}


def aggregate_recovery(cases):
    samples = defaultdict(list)
    for case in cases:
        for offset, row in recovery_case_curve(case)["offsets"].items():
            samples[int(offset)].append(row["mean_current_error"])
    return [{"offset": offset, "mean_error": statistics.mean(values), "contributing_cases": len(values)}
            for offset, values in sorted(samples.items())]


def episode_effects(selected, reference):
    rows = []
    for index, (candidate, control) in enumerate(zip(selected, reference, strict=True)):
        left = {row["completed_environment"]: row for row in candidate["environment_changes"]}
        right = {row["completed_environment"]: row for row in control["environment_changes"]}
        if set(left) != set(right):
            raise ValueError("Paired environmental epochs differ")
        for epoch in sorted(left):
            # Include initialization in complete effect decomposition, label it separately.
            length = left[epoch]["evaluations"] - left[epoch]["first_evaluation"] + 1
            difference = left[epoch]["environment_offline_error"] - right[epoch]["environment_offline_error"]
            rows.append({"case_index": index, "environment": epoch, "difference": difference,
                         "contribution_to_paired_mean": difference * length / candidate["evaluations"] / len(selected),
                         "initialization_environment": epoch == 0})
    extreme = max(rows, key=lambda row: abs(row["contribution_to_paired_mean"]))
    net = statistics.mean(a["offline_error"] - b["offline_error"] for a, b in zip(selected, reference))
    details = {"all_completed_environment_effects": rows,
               "largest_absolute_contribution": {**extreme, "fraction_of_net_effect": extreme["contribution_to_paired_mean"] / net if net else None},
               "interpretation": "Post hoc influence description; all epochs and cases remain retained. Complete trajectories differ."}
    eligible = [row for row in rows if not row["initialization_environment"]]
    for label, sign in (("most_favorable", 1), ("most_unfavorable", -1)):
        chosen = min(eligible, key=lambda row: (sign * row["difference"], row["environment"], row["case_index"]))
        epoch, index = chosen["environment"], chosen["case_index"]
        details[label] = {**chosen, "selected_trace": [point for point in selected[index]["trace"] if point["environment"] == epoch],
                          "reference_trace": [point for point in reference[index]["trace"] if point["environment"] == epoch]}
    return details


def native_programs(run, configs, hashes):
    searches = [folder for folder in (run / "evolution").glob("*") if folder.is_dir()]
    if len(searches) != 1:
        raise ValueError("Expected exactly one native search identity")
    search = searches[0]
    programs, slots = [], []
    for folder in sorted(search.glob("gen_*"), key=lambda path: int(path.name.split("_")[-1])):
        checkpoint = folder / "results/evaluation-checkpoint.json"
        if not checkpoint.exists():
            continue
        saved = read_json(checkpoint)
        slot = {"generation": int(folder.name.split("_")[-1]), "status": saved.get("status"),
                "source": str((folder / "main.py").relative_to(run)), "source_sha256": sha(folder / "main.py")}
        slots.append(slot)
        if saved.get("status") != "completed":
            continue
        correct = folder / "results/correct.json"
        if correct.exists() and read_json(correct).get("correct") is False:
            continue
        cases = load_cases(folder / "results", configs, hashes, run)
        programs.append({**slot, "mean_offline_error": statistics.mean(case["offline_error"] for case in cases),
                         "case_errors": [case["offline_error"] for case in cases], "behavior": summarize_behavior(cases)})
    recorded = {row["generation"] for row in slots}
    for generation in sorted(terminal_failure_generations(search) - recorded):
        source = search / f"gen_{generation}/main.py"
        slots.append({"generation": generation, "status": "terminal_failed_proposal", "objective_evaluation_submitted": False,
                      "source": str(source.relative_to(run)) if source.exists() else None,
                      "source_sha256": sha(source) if source.exists() else None})
    return search, programs, sorted(slots, key=lambda row: row["generation"])


def analyze(run, phase="development", selected_generation=None, output=None):
    run = Path(run).resolve()
    spec = read_json(SPEC_PATH)
    manifest = find_case_manifest(run, phase)
    configs = configs_from(manifest)
    hashes = {}
    programs, slots, selected = [], [], None
    if phase == "development":
        outcomes = {method: load_cases(run / "references" / method, configs, hashes, run) for method in METHODS[:2]}
        search, programs, slots = native_programs(run, configs, hashes)
        if not programs:
            raise ValueError("No completed valid native program exists")
        selected = min(programs, key=lambda row: (row["mean_offline_error"], row["generation"], row["source_sha256"]))
        if selected_generation is not None and selected_generation != selected["generation"]:
            raise ValueError("Requested generation disagrees with frozen selection ranking")
        outcomes["selected"] = load_cases(search / f"gen_{selected['generation']}/results", configs, hashes, run)
    else:
        outcomes = {method: load_cases(run / "fresh" / method, configs, hashes, run) for method in METHODS}
    checks = {method: [validate_pair(reference, candidate) for reference, candidate in zip(outcomes["mpso_5_1"], cases, strict=True)]
              for method, cases in outcomes.items()}
    errors = {method: [case["offline_error"] for case in cases] for method, cases in outcomes.items()}
    contrasts = {f"{method}_minus_{reference}": {"method": method, "reference": reference,
        **paired_effect([a - b for a, b in zip(errors[method], errors[reference], strict=True)], spec)}
        for method, reference in (("selected", "mpso_5_1"), ("selected", "mpso_5_0"), ("mpso_5_1", "mpso_5_0"))}
    result = {"study": "book_mpso_schedule_v1", "phase": phase, "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "analysis_settings": spec, "analysis_specification_sha256": sha(SPEC_PATH), "analysis_source_sha256": sha(__file__),
        "case_manifest_sha256": sha(manifest), "input_sha256": hashes, "configs": configs,
        "selected": {key: value for key, value in selected.items() if key != "behavior"} if selected else None,
        "execution_aliases": {"selected": "mpso_5_1"} if selected and selected["generation"] == 0 else {},
        "native_programs": programs, "native_slots": slots, "pair_checks": checks,
        "method_errors": {method: describe(values) for method, values in errors.items()}, "contrasts": contrasts,
        "behavior": {method: summarize_behavior(cases) for method, cases in outcomes.items()},
        "recovery": {method: aggregate_recovery(cases) for method, cases in outcomes.items()},
        "episode_influence": {reference: episode_effects(outcomes["selected"], outcomes[reference]) for reference in METHODS[:2]},
        "decision_examples": {method: [{"case_index": index, "examples": case.get("decision_examples", case["schedule_stats"].get("decision_examples", []))}
            for index, case in enumerate(cases)] for method, cases in outcomes.items()},
        "query_category_totals": {method: dict(sum((Counter(case["evaluation_counts"]) for case in cases), Counter())) for method, cases in outcomes.items()},
        "interpretation": spec["development_interpretation" if phase == "development" else "fresh_interpretation"]}
    output = Path(output) if output else run / "analysis" / phase
    output.mkdir(parents=True, exist_ok=True)
    atomic_json(output / "analysis.json", result)
    render(result, output)
    (output / "tables.md").write_text(markdown_tables(result))
    return result


def markdown_tables(data):
    if data.get("execution_aliases"):
        lines = [f"## {data['phase'].capitalize()} outcomes", "", "Selected native program is the published 5+1 seed; it is not a third distinct method.", "",
                 "| Case | 5+0 | 5+1 (selected seed) | 5+1 − 5+0 |", "|---|---:|---:|---:|"]
        for index in range(8):
            a, b = (data["method_errors"][method]["values"][index] for method in METHODS[:2])
            lines.append(f"| {index:03d} | {a:.6f} | {b:.6f} | {b-a:+.6f} |")
        row = data["contrasts"]["mpso_5_1_minus_mpso_5_0"]
        low, high = row["descriptive_95_percent_interval"]
        lines += ["", f"5+1 minus 5+0: mean {row['mean']:+.6f}; median {row['median']:+.6f}; SD {row['sd']:.6f}; descriptive 95% interval [{low:+.6f}, {high:+.6f}]; {row['wins']} wins / {row['losses']} losses / {row['ties']} ties."]
        return "\n".join(lines) + "\n"
    lines = [f"## {data['phase'].capitalize()} outcomes", "", "| Case | 5+0 | 5+1 | Selected | Selected − 5+0 | Selected − 5+1 |", "|---|---:|---:|---:|---:|---:|"]
    errors = data["method_errors"]
    for index in range(8):
        a, b, c = (errors[method]["values"][index] for method in METHODS)
        lines.append(f"| {index:03d} | {a:.6f} | {b:.6f} | {c:.6f} | {c-a:+.6f} | {c-b:+.6f} |")
    lines += ["", "| Contrast | Mean | Median | SD | Descriptive 95% interval | Wins / losses / ties |", "|---|---:|---:|---:|---|---:|"]
    for name, row in data["contrasts"].items():
        low, high = row["descriptive_95_percent_interval"]
        lines.append(f"| {name.replace('_', ' ')} | {row['mean']:+.6f} | {row['median']:+.6f} | {row['sd']:.6f} | [{low:+.6f}, {high:+.6f}] | {row['wins']} / {row['losses']} / {row['ties']} |")
    return "\n".join(lines) + "\n"


def render(data, output):
    _style()
    phase = data["phase"]
    seed_retained = bool(data.get("execution_aliases"))
    methods = METHODS[:2] if seed_retained else METHODS
    fig, axes = plt.subplots(2, 2, figsize=(12.3, 8.3), constrained_layout=True)
    comparison_keys = (["mpso_5_1_minus_mpso_5_0"] if seed_retained else
                       ["selected_minus_mpso_5_1", "selected_minus_mpso_5_0"])
    for column, key in enumerate(comparison_keys):
        ax = axes[0, column]
        row = data["contrasts"][key]
        ax.scatter(row["values"], np.arange(8), color=COLORS["selected"], s=35, zorder=3)
        ax.plot(row["descriptive_95_percent_interval"], [-1.3, -1.3], color="#243447", lw=2.5)
        ax.scatter(row["mean"], -1.3, marker="D", color="#243447", s=55, zorder=4)
        ax.axvline(0, color="#8796a5", lw=1, ls="--")
        ax.set_yticks([-1.3, *range(8)], ["Mean / 95% interval", *(f"Case {index:03d}" for index in range(8))])
        ax.set(title=("Reconstructed 5+1 − reconstructed 5+0" if seed_retained else f"Selected − {LABELS[row['reference']]}"),
               xlabel=("Paired offline error; negative favors 5+1" if seed_retained else "Paired offline error; negative favors selected"))
    for method in methods:
        rows = data["behavior"][method]["age_bins"]
        if not seed_retained:
            axes[1, 0].plot(range(len(AGE_BINS)), [rows[key]["mean_count"] if rows[key]["mean_count"] is not None else np.nan for key in AGE_BINS],
                            color=COLORS[method], label=LABELS[method], marker="o", markersize=4, lw=1.7)
        curve = data["recovery"][method]
        axes[1, 1].plot([row["offset"] for row in curve], [row["mean_error"] for row in curve], color=COLORS[method], label=LABELS[method], lw=1.8)
    if seed_retained:
        programs = sorted(data["native_programs"], key=lambda row: row["generation"])
        values = [row["mean_offline_error"] for row in programs]
        axes[0, 1].scatter([row["generation"] for row in programs], values, color=COLORS["selected"], s=45, zorder=3)
        for method in methods:
            axes[0, 1].axhline(data["method_errors"][method]["mean"], color=COLORS[method], ls="--", label=LABELS[method])
        axes[0, 1].set(title="No distinct descendant beats the seed", xlabel="Native generation slot", ylabel="Mean development offline error",
                       xticks=range(max(row["generation"] for row in data["native_slots"])+1))
        axes[0, 1].legend(frameon=False, fontsize=8)
        matrix = [[row["behavior"]["age_bins"][key]["mean_count"] if row["behavior"]["age_bins"][key]["mean_count"] is not None else np.nan for key in AGE_BINS] for row in programs]
        heat = axes[1, 0].imshow(matrix, vmin=0, vmax=5, cmap="viridis", aspect="auto")
        axes[1, 0].set_yticks(range(len(programs)), ["Both published schedules" if row["generation"] == 0 else f"Descendant {row['generation']}" for row in programs], fontsize=8)
        axes[1, 0].set_title("Actual conversion behavior of tested schedules")
        fig.colorbar(heat, ax=axes[1, 0], label="Mean count (of five)", shrink=.85)
    else:
        axes[1, 0].set(title="Measured temporary-conversion schedule", ylabel="Mean neutral particles converted (of five)", ylim=(-.15, 5.15))
    axes[1, 0].set_xticks(range(len(AGE_BINS)), ["No prior\ndetection", "Detected\nnow", "1", "2–3", "4–7", "8–15", "16–31", "32+"], fontsize=8)
    axes[1, 0].set_xlabel("Subswarm updates since its counted change detection")
    if not seed_retained:
        axes[1, 0].legend(frameon=False, fontsize=8, loc="upper right")
    axes[1, 1].set(title="Measured recovery after environmental change", xlabel="Actual recorded query offset", ylabel="Best-discovered error")
    axes[1, 1].legend(frameon=False, fontsize=8)
    for ax in axes.flat:
        ax.grid(alpha=.15)
    fig.suptitle(f"{'Published schedule retained after native search' if seed_retained else 'Original and evolved MPSO schedules'} · eight {phase} pairs · 500,000 queries each", fontsize=14)
    fig.supxlabel("Five dimensions, ten peaks, severity 1, period 5,000. Curves give each case equal weight.\n" +
                  ("Development data informed search and selection; uncertainty is descriptive and selection-biased." if phase == "development" else
                   "Frozen methods; independent cases. Descriptive uncertainty in one setting, not replication of the historical table."), fontsize=9)
    _save(fig, output / "schedule_and_performance")

    fig, axes = plt.subplots(1, 3, figsize=(13.1, 4.3), constrained_layout=True)
    x = np.arange(6)
    for index, method in enumerate(methods):
        behavior = data["behavior"][method]
        offset = (index - (len(methods)-1)/2) * .25
        axes[0].bar(x + offset, np.asarray(behavior["equal_case_count_probabilities"])*100, width=.25, color=COLORS[method], label=LABELS[method])
        gains = behavior["shared_best_improvements"]
        for panel, field in ((1, "mean_case_improvements_per_1000_queries"), (2, "mean_case_gain_per_1000_queries")):
            axes[panel].bar(np.arange(3)+offset, [gains[role][field] for role in MOVEMENT_TYPES], width=.25, color=COLORS[method])
    axes[0].set(title="Observed schedule decisions", xlabel="Temporary quantum count", ylabel="Mean within-case updates (%)", xticks=range(6))
    axes[0].legend(frameon=False, fontsize=7)
    for ax in axes[1:]:
        ax.set_xticks(range(3), ["Ordinary", "Temporary\nquantum", "Permanent\nquantum"])
    axes[1].set(title="Shared-best improvement frequency", ylabel="Improvements / 1,000 category queries")
    axes[2].set(title="Observed shared-best fitness gains", ylabel="Gain / 1,000 category queries")
    for ax in axes:
        ax.grid(alpha=.15, axis="y")
    fig.suptitle(f"Measured diversification and search contributions · {phase}", fontsize=14)
    fig.supxlabel("Attribution records the update that improved the shared best, on each method’s reached trajectory.\nIt does not isolate a causal contribution; query categories and opportunities differ.", fontsize=9)
    _save(fig, output / "schedule_contributions")
    if data["native_programs"]:
        fig, ax = plt.subplots(figsize=(9.8, 4.4), constrained_layout=True)
        rows = sorted(data["native_programs"], key=lambda row: row["generation"])
        values = [row["mean_offline_error"] for row in rows]
        ax.scatter([row["generation"] for row in rows], values, color=COLORS["selected"], s=55, zorder=3, label="Native evaluated program")
        ax.step([row["generation"] for row in rows], np.minimum.accumulate(values), where="post", color=COLORS["selected"], lw=1.6, label="Best native development error")
        for method in METHODS[:2]:
            ax.axhline(data["method_errors"][method]["mean"], color=COLORS[method], ls="--", lw=1.4, label=LABELS[method])
        valid_generations = {row["generation"] for row in rows}
        failed_generations = [row["generation"] for row in data["native_slots"] if row["generation"] not in valid_generations and ("failed" in row["status"] or row["status"] == "failure")]
        if failed_generations:
            ax.scatter(failed_generations, [.05]*len(failed_generations), transform=ax.get_xaxis_transform(), marker="x", color="#bb4260", label="Terminal failure (no numerical score)")
        ax.set(title="One bounded native ShinkaEvolve search", xlabel="Generation slot (zero is the published 5+1 schedule)", ylabel="Mean development offline error", xticks=range(max(row["generation"] for row in data["native_slots"])+1))
        ax.legend(frameon=False, fontsize=8)
        ax.grid(alpha=.15)
        fig.supxlabel("Every numerical point uses the same eight 500,000-query histories. Terminal failed slots are retained without numerical points.", fontsize=9)
        _save(fig, output / "native_search")
    atomic_json(output / "figure_provenance.json", {"analysis_sha256": sha(output / "analysis.json"), "source_sha256": sha(__file__),
        "dimension": 5, "phase": phase, "objective_calls": 0, "model_calls": 0,
        "files": {path.name: sha(path) for path in sorted(output.glob("*.png"))+sorted(output.glob("*.svg"))}})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--phase", choices=("development", "fresh"), default="development")
    parser.add_argument("--selected-generation", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyze(args.run, args.phase, args.selected_generation, args.output)
    print(json.dumps({"phase": result["phase"], "selected": result["selected"], "method_errors": result["method_errors"], "contrasts": result["contrasts"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
