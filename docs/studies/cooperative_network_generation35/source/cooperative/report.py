"""Produce descriptive development tables and standalone figures from saved evidence.

This module never runs simulations or participates in discovery scoring.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import sqlite3
import statistics
import math
import random

from cooperative.native import terminal_failures

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results/adaptive_exploration_v1"


def read(path):
    return json.loads(path.read_text())


def paired_summary(candidate, comparator, scales):
    reference = {x["case_id"]: x for x in comparator["cases"]}
    groups = {}
    for item in candidate["cases"]:
        case, outcome = item["case"], item["outcome"]
        base = reference[item["case_id"]]["outcome"]
        keys = ["all", case["regime_id"], case["focal_mode"],
                case["regime_id"] + "/" + case["focal_mode"]]
        gain = outcome["focal_cumulative_utility"] - base["focal_cumulative_utility"]
        scaled = gain / (case["recovery_rounds"] * scales[case["regime_id"]])
        for key in keys:
            bucket = groups.setdefault(key, [])
            partner = outcome.get("initial_partners_mean_utility")
            partner_base = base.get("initial_partners_mean_utility")
            bucket.append({"history": item["history_id"], "regime": case["regime_id"], "gain": gain, "scaled": scaled,
                           "other_gain": outcome["others_mean_utility"] - base["others_mean_utility"],
                           "partner_gain": partner - partner_base if partner is not None and partner_base is not None else None})
    output = []
    for group, rows in sorted(groups.items()):
        histories = {}
        for row in rows:
            histories.setdefault(row["history"], []).append(row["scaled"])
        cluster = [statistics.mean(v) for v in histories.values()]
        se = statistics.stdev(cluster) / math.sqrt(len(cluster)) if len(cluster) > 1 else None
        partner_gains = [r["partner_gain"] for r in rows if r["partner_gain"] is not None]
        strata = {}
        for row in rows:
            strata.setdefault(row["regime"], {}).setdefault(row["history"], []).append(row["scaled"])
        strata = [[statistics.mean(v) for v in h.values()] for h in strata.values()]
        rng = random.Random(81721)
        draws = sorted(statistics.mean(rng.choice(s) for s in strata for _ in s) for _ in range(4000))
        output.append({"group": group, "cases": len(rows), "histories": len(cluster),
                       "paired_cumulative_gain": statistics.mean(r["gain"] for r in rows),
                       "scaled_gain": statistics.mean(r["scaled"] for r in rows),
                       "descriptive_cluster_se": se,
                       "descriptive_stratified_history_bootstrap_95": [draws[99], draws[3899]],
                       "other_mean_utility_gain": statistics.mean(r["other_gain"] for r in rows),
                       "initial_partner_mean_utility_gain": statistics.mean(partner_gains) if partner_gains else None,
                       "cases_with_initial_partners": len(partner_gains)})
    return output


def exposure_counts(raw):
    """Classify inherited exposure without conditioning case selection on it."""
    records = []
    for item in raw["cases"]:
        if item["case"]["focal_mode"] != "indirect":
            continue
        case, outcome = item["case"], item["outcome"]
        snapshot = read(ROOT / case["snapshot"])
        focal, neighbors, offset = outcome["focal_index"], set(), 0
        for _ in range(2):
            for i in range(case["n"]):
                for j in range(i + 1, case["n"]):
                    if snapshot["adjacency"][offset] == "1" and focal in (i, j):
                        neighbors.add(j if i == focal else i)
                    offset += 1
        records.append({"case_id": item["case_id"], "initial_partners": len(neighbors),
                        "initial_shocked_neighbors": len(neighbors.intersection(outcome["shock_recipients"]))})
    return records


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    destination = RESULTS / "report"
    destination.mkdir(parents=True, exist_ok=True)
    baseline_path = RESULTS / "baselines/summary.json"
    summary = read(baseline_path)
    baselines = summary["baselines"]
    source_paths = [baseline_path]
    example_raw_path = RESULTS / "baselines" / next(iter(baselines)) / "case_results.json"
    exposure = exposure_counts(read(example_raw_path))
    source_paths.append(example_raw_path)
    rows = []
    for name, metrics in baselines.items():
        rows.append({"policy": name, "score": metrics["combined_score"],
                     "focal_cumulative": metrics["public"]["focal_cumulative_utility"],
                     "paired_cumulative_gain": metrics["public"]["paired_cumulative_gain"],
                     "cluster_se": metrics["public"]["scaled_gain_cluster_se"]})

    programs = []
    database = RESULTS / "search/programs.sqlite"
    if database.exists():
        with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as db:
            db.row_factory = sqlite3.Row
            programs = [dict(r) for r in db.execute("SELECT id,generation,code,correct,combined_score,public_metrics,parent_id,metadata,island_idx,migration_history,system_prompt_id FROM programs ORDER BY generation,timestamp")]
        population_path = destination / "native_population.json"
        population_path.write_text(json.dumps(programs, indent=2) + "\n")
        source_paths.append(population_path)
    originals = [p for p in programs if not json.loads(p.get("metadata") or "{}").get("administrative_copy")]
    valid = [p for p in originals if p["correct"]]
    # SQL order makes exact score ties select the earliest generation.
    best = max(valid, key=lambda p: p["combined_score"]) if valid else None
    tied_best = [p for p in valid if best and p["combined_score"] == best["combined_score"]]
    failed_slots = sorted(terminal_failures(RESULTS / "search"))
    terminal_slots = sorted({p["generation"] for p in originals} | set(failed_slots))
    source_paths.extend(RESULTS / f"search/gen_{generation}/failure.json" for generation in failed_slots)
    comparisons = {}
    if best:
        public = json.loads(best["public_metrics"])
        name = f"native generation {best['generation']}"
        rows.append({"policy": name, "score": best["combined_score"],
                     "focal_cumulative": public["focal_cumulative_utility"],
                     "paired_cumulative_gain": public["paired_cumulative_gain"],
                     "cluster_se": public["scaled_gain_cluster_se"]})
        (destination / "CandidatePolicy.java").write_text(best["code"])
        raw_path = RESULTS / f"search/gen_{best['generation']}/results/case_results.json"
        if raw_path.exists():
            raw = read(raw_path)
            source_paths.append(raw_path)
            scales_path = ROOT / "experiments/adaptive_exploration_v1/scales.json"
            scales = read(scales_path)
            source_paths.append(scales_path)
            for baseline in baselines:
                path = RESULTS / f"baselines/{baseline}/case_results.json"
                if path.exists():
                    comparisons[baseline] = paired_summary(raw, read(path), scales)
                    source_paths.append(path)

    with (destination / "development_table.csv").open("w") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = {"status": "development selection only; independent confirmation not executed",
              "uncertainty": "4000 paired history bootstrap resamples within incentive/cost strata; related direct/indirect cases are averaged within each history, not counted as independent replicates; selection bias is not corrected, four histories per stratum; reported intervals and cluster SEs are for scaled effects",
              "program_rows": len(programs), "valid_descendants": sum(p["generation"] > 0 for p in valid),
              "unique_evaluated_programs": len(originals),
              "administrative_copies": len(programs) - len(originals),
              "terminal_slots": terminal_slots, "terminal_slot_count": len(terminal_slots),
              "failed_proposal_slots": failed_slots,
              "invalid_descendants": sum(p["generation"] > 0 and not p["correct"] for p in originals),
              "best_program_id": best["id"] if best else None,
              "best_generation": best["generation"] if best else None,
              "best_candidate_sha256": hashlib.sha256(best["code"].encode()).hexdigest() if best else None,
              "tied_best_program_ids": [p["id"] for p in tied_best],
              "tied_best_generations": [p["generation"] for p in tied_best],
              "best_selection_rule": "Highest development score among correct programs; earliest generation on an exact score tie",
              "unshocked_focal_inherited_exposure": exposure,
              "table": rows, "best_vs_baselines": comparisons}
    manifest_path = ROOT / "campaigns/adaptive_exploration_v1.json"
    if manifest_path.exists():
        manifest = read(manifest_path)
        report["active_search_phase"] = manifest.get("active_search_phase", "A")
        report["search_phases"] = manifest.get("search_phases", [])
        if manifest.get("active_search_phase") == "B":
            boundary = manifest["search_phases"][-1]["first_generation"]
            report["phase_accounting"] = {}
            for label, selected in (("A", [p for p in originals if p["generation"] < boundary]),
                                    ("B", [p for p in originals if p["generation"] >= boundary])):
                failures = [g for g in failed_slots if (g < boundary) == (label == "A")]
                report["phase_accounting"][label] = {"unique_evaluated_programs": len(selected),
                    "valid_descendants": sum(p["generation"] > 0 and bool(p["correct"]) for p in selected),
                    "invalid_descendants": sum(p["generation"] > 0 and not p["correct"] for p in selected),
                    "failed_proposal_slots": failures,
                    "terminal_slots": sorted([p["generation"] for p in selected] + failures)}
            report["phase_interpretation"] = "Two search configurations share the same frozen development experiment; later results do not isolate causal benefits of individual search mechanisms. Administrative island copies are not new evaluations."
    (destination / "summary.json").write_text(json.dumps(report, indent=2) + "\n")

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    ordered = sorted(rows, key=lambda r: r["score"])
    fig, ax = plt.subplots(figsize=(9, 5.5), layout="constrained")
    ax.barh([r["policy"] for r in ordered], [r["score"] for r in ordered],
            color=["#b35a25" if r["policy"].startswith("native") else "#447b89" for r in ordered])
    ax.axvline(0, color="#444444", linewidth=.8)
    ax.set_xlabel("Scaled paired focal utility gain versus selected fixed rule")
    ax.set_title("Fixed development histories: baseline and native selection scores")
    fig.text(.5, -.025, "Selection data only • baseline tuning and evolution reuse these histories • no confirmation claim", ha="center", fontsize=9)
    for suffix in ["svg", "png"]:
        fig.savefig(destination / f"development_scores.{suffix}", bbox_inches="tight", dpi=180)
    plt.close(fig)

    if valid:
        fig, ax = plt.subplots(figsize=(8, 4), layout="constrained")
        running = []
        current = -math.inf
        for p in valid:
            current = max(current, p["combined_score"])
            running.append(current)
        ax.scatter([p["generation"] for p in valid], [p["combined_score"] for p in valid], color="#447b89", s=25, label="Valid program")
        ax.step([p["generation"] for p in valid], running, where="post", color="#b35a25", label="Best retained score")
        ax.axhline(0, color="#666666", linewidth=.8, linestyle="--")
        ax.set(xlabel="Native generation slot (zero is seed)", ylabel="Scaled paired focal gain", title="Native discovery on reused development cases")
        ax.legend(frameon=False)
        for suffix in ["svg", "png"]:
            fig.savefig(destination / f"discovery_progress.{suffix}", dpi=180)
        plt.close(fig)
    provenance = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(source_paths))}
    provenance["report_script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (destination / "figure_provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(json.dumps({"report": str(destination), "best_generation": report["best_generation"], "valid_descendants": report["valid_descendants"]}))


if __name__ == "__main__":
    main()
