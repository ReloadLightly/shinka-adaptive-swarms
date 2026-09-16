#!/usr/bin/env python3
"""Plot measured native Shinka search outcomes without executing candidates."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def render(run: Path, output: Path) -> dict:
    database = run / "programs.sqlite"
    with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        records = [dict(row) for row in connection.execute(
            "SELECT id, parent_id, generation, combined_score, correct, "
            "public_metrics, code FROM programs ORDER BY generation, id"
        )]
    grouped: dict[int, list[dict]] = {}
    for record in records:
        grouped.setdefault(record["generation"], []).append(record)
    points = []
    best_error = float("inf")
    for generation, group in sorted(grouped.items()):
        # Native initialization copies the evaluated seed to another island.
        # Different outcomes within a slot are ambiguous and need inspection.
        identities = {(r["code"], r["combined_score"], r["correct"],
                       r["public_metrics"]) for r in group}
        if len(identities) != 1:
            raise ValueError(f"Generation {generation} contains different outcomes")
        record = group[0]
        if not record["correct"]:
            continue
        metrics = json.loads(record["public_metrics"])
        error = metrics["mean_offline_error"]
        best_error = min(best_error, error)
        points.append({"generation": generation,
                       "program_ids": [r["id"] for r in group],
                       "mean_offline_error": error,
                       "best_so_far_offline_error": best_error,
                       "combined_score": record["combined_score"],
                       "cases_completed": metrics["cases_completed"]})
    if not points:
        raise ValueError("No completed valid native evaluations to plot")
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.titleweight": "bold", "text.color": "#243447",
                         "axes.labelcolor": "#243447", "figure.facecolor": "white",
                         "savefig.facecolor": "white"})
    fig, ax = plt.subplots(figsize=(10.5, 4.8), constrained_layout=True)
    generations = [p["generation"] for p in points]
    errors = [p["mean_offline_error"] for p in points]
    ax.plot(generations, errors, color="#8796a5", marker="o", markersize=4.5,
            linewidth=1.15, label="Evaluated program")
    ax.step(generations, [p["best_so_far_offline_error"] for p in points],
            where="post", color="#187b80", linewidth=2.5, label="Best so far")
    seed = next((p for p in points if p["generation"] == 0), None)
    if seed:
        ax.axhline(seed["mean_offline_error"], color="#d47b34", linestyle="--",
                   linewidth=1.2, label="Corrected baseline seed")
    best = min(points, key=lambda p: p["mean_offline_error"])
    ax.scatter([best["generation"]], [best["mean_offline_error"]],
               marker="*", color="#187b80", edgecolor="white", s=180, zorder=5)
    ax.annotate(f"Best: generation {best['generation']}\n"
                f"offline error {best['mean_offline_error']:.4f}",
                (best["generation"], best["mean_offline_error"]),
                xytext=(12, 17), textcoords="offset points", fontsize=9,
                color="#13676b", arrowprops={"arrowstyle": "-", "color": "#187b80"})
    ax.set(xlabel="Native generation slot (0 = evaluated seed)",
           ylabel="Mean offline error (lower is better)",
           title="Native ShinkaEvolve search · measured 5D outcomes")
    ax.set_xticks(generations)
    ax.grid(axis="y", alpha=.18)
    ax.legend(frameon=False, loc="upper right")
    suite = json.loads((run / "search-suite.json").read_text())
    fig.supxlabel(f"{len(suite['cases'])} search cases × {suite['budget']:,} objective queries per program"
                  " · repeated search suite; generalization assessed separately", fontsize=9)
    artifacts = []
    for suffix in ("png", "svg"):
        target = output / f"search_progress.{suffix}"
        fig.savefig(target, dpi=180, bbox_inches="tight")
        artifacts.append({"path": target.name,
                          "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
    plt.close(fig)
    provenance = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_run": str(run), "database": str(database),
        "database_record_count": len(records),
        "plotted_evaluations": len(points),
        "database_rows_sha256": hashlib.sha256(json.dumps(
            records, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "suite_sha256": hashlib.sha256((run / "search-suite.json").read_bytes()).hexdigest(),
        "dimension": suite["dimension"], "case_budget": suite["budget"],
        "case_count": len(suite["cases"]), "points": points, "artifacts": artifacts,
        "deduplication": "Identical rows in the same generation represent one evaluated program; native seed island copy deduplicated.",
        "interpretation": "Measured search-suite performance, not held-out generalization. No candidate or objective evaluations were executed to generate this figure.",
    }
    (output / "figure_provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    return provenance


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("assets/evolution"))
    args = parser.parse_args()
    result = render(args.run, args.output)
    print(f"[{result['generated_at']}] Saved {result['plotted_evaluations']} measured "
          f"program outcomes to {args.output}; candidates executed: 0", flush=True)
