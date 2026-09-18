#!/usr/bin/env python3
"""Plot saved native development scores; never run simulations or model calls."""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--through-generation", type=int, required=True)
    args = parser.parse_args()
    with sqlite3.connect(f"file:{args.database.resolve()}?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute(
            "SELECT id, parent_id, generation, correct, public_metrics, code "
            "FROM programs WHERE generation <= ? ORDER BY generation",
            (args.through_generation,),
        ).fetchall()
    data = []
    for row in rows:
        metrics = json.loads(row["public_metrics"])
        valid = bool(row["correct"])
        if valid and metrics.get("cases_completed") != 4:
            raise ValueError(f"Generation {row['generation']} lacks four complete cases")
        data.append({
            "generation": row["generation"], "id": row["id"],
            "parent_id": row["parent_id"], "correct": valid,
            "source_sha256": hashlib.sha256(row["code"].encode()).hexdigest(),
            "mean_offline_error": metrics["mean_offline_error"] if valid else None,
        })
    valid_rows = [row for row in data if row["correct"]]
    leader = min(valid_rows, key=lambda row: row["mean_offline_error"])
    fig, ax = plt.subplots(figsize=(9, 4.5), layout="constrained")
    ax.scatter([row["generation"] for row in valid_rows],
               [row["mean_offline_error"] for row in valid_rows],
               s=58, color="#26778b", zorder=3, label="Complete valid program")
    by_id = {row["id"]: row for row in valid_rows}
    for row in valid_rows:
        parent = by_id.get(row["parent_id"])
        if parent:
            ax.plot([parent["generation"], row["generation"]],
                    [parent["mean_offline_error"], row["mean_offline_error"]],
                    color="#a8c0c6", linewidth=1, zorder=1)
    seed = next(row for row in valid_rows if row["generation"] == 0)
    ax.axhline(seed["mean_offline_error"], linestyle="--", color="#a67830",
               label="Corrected reconstructed 5+1 seed")
    ax.scatter([leader["generation"]], [leader["mean_offline_error"]],
               color="#215c31", marker="*", s=190, zorder=4, label="Interim development leader")
    for row in data:
        if not row["correct"]:
            ax.text(row["generation"], .05, "Invalid\nno score", ha="center",
                    transform=ax.get_xaxis_transform(), color="#a3483f", fontsize=9)
    ax.set_xticks(range(args.through_generation + 1))
    ax.set_xlabel("Native generation (0 = seed; lines connect parents to descendants)")
    ax.set_ylabel("Mean offline error · lower is better")
    ax.set_title("Observed evolution on four reused 5D development histories")
    ax.grid(axis="y", alpha=.2)
    ax.legend(loc="upper right", fontsize=8)
    fig.suptitle("500,000 objective queries per case · no fresh confirmation", fontsize=10)
    args.output.mkdir(parents=True, exist_ok=True)
    for suffix in ("png", "svg"):
        fig.savefig(args.output / f"native_evolution.{suffix}", dpi=160)
    plt.close(fig)
    (args.output / "native_evolution.json").write_text(json.dumps({
        "database": str(args.database), "through_generation": args.through_generation,
        "new_objective_evaluations": 0, "new_model_calls": 0,
        "interpretation": "Development comparison of whole policies, not isolated causal effects",
        "programs": data,
    }, indent=2) + "\n")
    print(f"Plotted {len(data)} saved rows; leader generation {leader['generation']}")


if __name__ == "__main__":
    main()
