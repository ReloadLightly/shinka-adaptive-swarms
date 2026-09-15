"""Publication-style figures generated exclusively from saved simulation traces."""
from __future__ import annotations
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import numpy as np

COLORS = ["#187b80", "#d47b34", "#7057a3", "#bb4260", "#477ab2"]


def _style():
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.titleweight": "bold", "axes.labelcolor": "#243447",
        "text.color": "#243447", "axes.edgecolor": "#8796a5",
        "figure.facecolor": "white", "savefig.facecolor": "white"})


def _save(fig, target):
    fig.savefig(target.with_suffix(".png"), dpi=180, bbox_inches="tight")
    fig.savefig(target.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)


def render_run(run_dir: Path, output: Path | None = None):
    cases = [json.loads(p.read_text()) for p in sorted(run_dir.glob("case_*.json"))]
    if not cases:
        raise ValueError(f"No saved cases found in {run_dir}")
    output = output or run_dir / "figures"
    output.mkdir(parents=True, exist_ok=True)
    _style()
    manifest_path = run_dir / "manifest.json"
    run_manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    is_baseline = run_manifest.get("policy") == "baseline"
    title_label = "Baseline reconstruction" if is_baseline else "Candidate policy evaluation"
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.1), constrained_layout=True)
    for i, case in enumerate(cases):
        trace = case["trace"]
        x = np.array([t["evaluations"] for t in trace]) / 1000
        label = f"Environment seed {case['config']['environment_seed']}"
        axes[0].plot(x, [t["offline_error"] for t in trace], color=COLORS[i % len(COLORS)],
                     lw=1.8, label=label)
        axes[1].plot(x, [t["swarm_count"] for t in trace], color=COLORS[i % len(COLORS)], lw=1.4)
    # Initialization error can dominate the scale; keep it visible with symlog.
    axes[0].set_yscale("symlog", linthresh=1)
    axes[0].set(title="Tracking a changing landscape", ylabel="Cumulative offline error (lower is better)")
    axes[1].set(title="Collective search organization", ylabel="Active subswarms")
    for ax in axes:
        ax.set_xlabel("Objective evaluations (thousands)")
        ax.grid(alpha=.18)
    axes[0].legend(frameon=False, fontsize=8)
    fig.suptitle(f"{title_label} · {cases[0]['config']['dimension']} dimensions · {len(cases)} runs", fontsize=14)
    _save(fig, output / "baseline_tracking")

    fig, ax = plt.subplots(figsize=(9, 3.5), constrained_layout=True)
    kinds = sorted(set().union(*(set(c["evaluation_counts"]) for c in cases)))
    left = np.zeros(len(cases))
    for i, kind in enumerate(kinds):
        vals = np.array([c["evaluation_counts"].get(kind, 0)/c["evaluations"]*100 for c in cases])
        ax.barh(range(len(cases)), vals, left=left, label=kind.replace("_", " "),
                color=COLORS[i % len(COLORS)])
        left += vals
    ax.set_yticks(range(len(cases)), [f"Seed {c['config']['environment_seed']}" for c in cases])
    ax.set(xlim=(0, 100), xlabel="Share of the complete objective-query budget (%)",
           title="Change detection and memory refresh consume real evaluations")
    ax.legend(ncol=min(len(kinds), 5), bbox_to_anchor=(0, -.2), loc="upper left", frameon=False)
    _save(fig, output / "evaluation_accounting")

    first = cases[0]
    changes = first["environment_changes"]
    if changes:
        fig, ax = plt.subplots(figsize=(10, 3.5), constrained_layout=True)
        epochs = np.arange(1, len(changes)+1)
        ax.plot(epochs, [c["environment_initial_error"] for c in changes], color="#b7c2cc",
                label="First query after change", lw=1)
        ax.plot(epochs, [c["environment_final_error"] for c in changes], color=COLORS[0],
                label="Best discovered by end of interval", lw=1.5)
        ax.set_yscale("symlog", linthresh=.1)
        ax.set(xlabel="Environment interval", ylabel="Tracking error (lower is better)",
               title=f"Recovery and missed opportunities · environment seed {first['config']['environment_seed']}")
        ax.legend(frameon=False)
        ax.grid(alpha=.18)
        _save(fig, output / "environment_recovery")
    if first["config"]["dimension"] == 2 and first.get("snapshots"):
        render_landscape(first, output, is_baseline)
    manifest = {"input_run": str(run_dir), "case_seeds": [c["config"]["environment_seed"] for c in cases],
                "dimension": first["config"]["dimension"], "policy": run_manifest.get("policy", "unrecorded"),
                "evolved_program": False if is_baseline else "requires_native_lineage_verification",
                "note": "2D landscape figures are illustrative runs; 5D plots report reconstruction measurements."}
    (output / "figure_provenance.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(f"Figures saved to {output}", flush=True)


def render_landscape(case, output, is_baseline):
    snapshots = case["snapshots"]
    lower, upper = case["config"]["bounds"]
    values = np.linspace(lower, upper, 100)
    xx, yy = np.meshgrid(values, values)

    def draw(ax, snap):
        ax.clear()
        peaks = snap["landscape"]
        z = np.full_like(xx, -np.inf)
        for point, height, width in zip(peaks["positions"], peaks["heights"], peaks["widths"]):
            z = np.maximum(z, height-width*np.sqrt((xx-point[0])**2+(yy-point[1])**2))
        ax.contourf(xx, yy, z, levels=18, cmap="Blues", alpha=.7)
        pp = np.array(peaks["positions"])
        ax.scatter(pp[:, 0], pp[:, 1], c="#1e2a39", marker="*", s=95, label="Peak centers")
        for s in snap["swarms"]:
            positions = np.array(s["particles"])
            ax.scatter(positions[:, 0], positions[:, 1], s=22, edgecolor="white", linewidth=.5,
                       color=COLORS[s["id"] % len(COLORS)])
        ax.set(xlim=(lower, upper), ylim=(lower, upper), aspect="equal", xlabel="Search coordinate 1",
               ylabel="Search coordinate 2", title=f"Evaluation {snap['evaluations']:,} · environment {snap['environment']}")

    fig, axes = plt.subplots(1, 3, figsize=(11.2, 4.0), constrained_layout=True)
    period = case["config"]["period"]
    desired = [max(100, period-100), period+100, 2*period-100]
    for ax, count in zip(axes, desired):
        draw(ax, min(snapshots, key=lambda x: abs(x["evaluations"]-count)))
    fig.suptitle("Illustrative 2D run · swarms redistribute around moving peaks", fontsize=14)
    _save(fig, output / "swarm_landscape")
    fig, ax = plt.subplots(figsize=(5.8, 5.5), constrained_layout=True)
    fig.suptitle(f"Illustrative 2D {'baseline' if is_baseline else 'candidate'} · stars mark peaks", fontsize=12)
    animation = FuncAnimation(fig, lambda i: draw(ax, snapshots[i]), frames=len(snapshots), interval=130)
    animation.save(output / "swarm_dynamics.gif", writer=PillowWriter(fps=8), dpi=100)
    plt.close(fig)
