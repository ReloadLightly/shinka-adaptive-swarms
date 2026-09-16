"""Figures for independent comparisons, generated only from saved case data."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .figures import COLORS, _save, _style
from .logging import atomic_json
from .artifacts import case_artifacts, read_json


def _label(name: str) -> str:
    return {"baseline": "Corrected baseline", "selected": "Selected program"}.get(name, name.replace("_", " ").capitalize())


def _regime_label(config: dict) -> str:
    return f"shift {config['move_severity']:g}, period {config['period']:,}"


def render_comparison(run_dir: Path, output: Path | None = None):
    manifest = json.loads((run_dir / "manifest.json").read_text())
    summary = json.loads((run_dir / "summary.json").read_text())
    if summary["status"] != "completed":
        raise ValueError("Comparison figures require the completed planned cases.")
    output = output or run_dir / "figures"
    output.mkdir(parents=True, exist_ok=True)
    methods = list(manifest["methods"])
    cases = {method: [read_json(path) for path in case_artifacts(run_dir / method)]
             for method in methods}
    count = summary["paired_case_count"]
    baseline = cases["baseline"]
    _style()

    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.8), constrained_layout=True,
                             gridspec_kw={"width_ratios": [1.3, 1]})
    x = np.arange(count)
    for i, method in enumerate(methods):
        offset = (i - (len(methods) - 1) / 2) * .18
        axes[0].scatter(x + offset, [case["offline_error"] for case in cases[method]],
                        color=COLORS[i % len(COLORS)], label=_label(method), s=40, zorder=3)
    for i in range(count):
        ys = [cases[method][i]["offline_error"] for method in methods]
        xs = [i + (j - (len(methods) - 1) / 2) * .18 for j in range(len(methods))]
        axes[0].plot(xs, ys, color="#c5cdd5", lw=.8, zorder=1)
    axes[0].set_xticks(x, [f"{case['config']['environment_seed']}\n{_regime_label(case['config'])}" for case in baseline], rotation=38, ha="right", fontsize=8)
    axes[0].set(title="Independent landscape histories", xlabel="Environment seed and regime",
                ylabel="Offline error (lower is better)")
    axes[0].legend(frameon=False, fontsize=8)
    comparisons = [(key, comparison) for key, comparison in summary["comparisons"].items()
                   if comparison["comparator"] == "baseline"]
    for index, (_, comparison) in enumerate(comparisons):
        y = len(comparisons) - 1 - index
        deltas = [case["delta"] for case in comparison["cases"]]
        axes[1].scatter(deltas, np.full(len(deltas), y) + np.linspace(-.13, .13, len(deltas)),
                        color=COLORS[(index + 1) % len(COLORS)], alpha=.7, s=25)
        interval = comparison["bootstrap_95_percent_interval"]
        mean = comparison["mean_delta"]
        if interval:
            axes[1].plot(interval, [y, y], color="#243447", lw=2)
        axes[1].scatter([mean], [y], marker="D", color="#243447", s=48, zorder=4)
    axes[1].axvline(0, color="#8796a5", lw=1, ls="--")
    axes[1].set_yticks(range(len(comparisons)), [_label(comparison["method"]) for _, comparison in reversed(comparisons)])
    axes[1].set(title="Paired effect at equal evaluation budgets",
                xlabel="Method − baseline offline error\nNegative favors the method")
    for ax in axes:
        ax.grid(alpha=.18, axis="y" if ax is axes[0] else "x")
    fig.suptitle(f"Frozen program comparison · {baseline[0]['config']['dimension']}D · {count} independent paired cases", fontsize=14)
    fig.text(.52, -.10, "Dots: individual cases. Diamond: paired mean. Line: stratified bootstrap 95% interval.\nOnly two cases per regime; interval coverage is uncertain.", ha="center", fontsize=8)
    _save(fig, output / "paired_offline_error")

    regimes = list(dict.fromkeys(_regime_label(case["config"]) for case in baseline))
    fig, axes = plt.subplots(2, 2, figsize=(11.8, 7.2), constrained_layout=True, squeeze=False)
    for ax, regime in zip(axes.flat, regimes):
        indices = [i for i, case in enumerate(baseline) if _regime_label(case["config"]) == regime]
        for j, method in enumerate(methods):
            for k, index in enumerate(indices):
                trace = cases[method][index]["trace"]
                ax.plot([point["evaluations"] / 1000 for point in trace],
                        [point["offline_error"] for point in trace], color=COLORS[j % len(COLORS)],
                        ls="-" if k == 0 else "--", lw=1.4,
                        label=_label(method) if k == 0 else None)
        ax.set(title=regime, xlabel="Objective evaluations (thousands)",
               ylabel="Cumulative offline error", yscale="symlog")
        ax.grid(alpha=.18)
    for ax in list(axes.flat)[len(regimes):]:
        ax.set_visible(False)
    axes.flat[0].legend(frameon=False, fontsize=8)
    fig.suptitle("Tracking across changed conditions · line styles distinguish the two seeds", fontsize=14)
    _save(fig, output / "tracking_by_regime")

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.0), constrained_layout=True)
    kinds = sorted({kind for method in methods for case in cases[method] for kind in case["evaluation_counts"]})
    left = np.zeros(len(methods))
    for index, kind in enumerate(kinds):
        values = np.array([sum(case["evaluation_counts"].get(kind, 0) for case in cases[method]) /
                           sum(case["evaluations"] for case in cases[method]) * 100 for method in methods])
        axes[0].barh(range(len(methods)), values, left=left, label=kind.replace("_", " "), color=COLORS[index % len(COLORS)])
        left += values
    axes[0].set_yticks(range(len(methods)), [_label(method) for method in methods])
    axes[0].set(xlim=(0, 100), xlabel="All objective queries (%)", title="Evaluation allocation")
    axes[0].legend(ncol=3, frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(0, -.18))
    for j, method in enumerate(methods):
        per_case = [sum(len(response["relocated_indices"]) / response["observation"]["swarm_size"]
                        for response in case["response_log"]) / max(1, len(case["response_log"]))
                    for case in cases[method]]
        axes[1].scatter(np.full(count, j) + np.linspace(-.15, .15, count), per_case,
                        color=COLORS[j % len(COLORS)], s=35)
    axes[1].set_xticks(range(len(methods)), [_label(method) for method in methods], rotation=15, ha="right")
    axes[1].set(ylim=(-.04, 1.04), ylabel="Mean relocated fraction\nper response",
                title="Response behavior · one dot per case")
    axes[1].grid(alpha=.18, axis="y")
    fig.suptitle("Behavioral diagnostics include detection and memory costs", fontsize=14)
    _save(fig, output / "response_behavior")

    paths = [run_dir / "manifest.json", run_dir / "freeze.json", run_dir / "summary.json"]
    paths += [path for method in methods for path in case_artifacts(run_dir / method)]
    atomic_json(output / "figure_provenance.json", {
        "input_run": str(run_dir), "dimension": baseline[0]["config"]["dimension"],
        "independent_cases": count, "methods": methods,
        "inputs_sha256": {str(path.relative_to(run_dir)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
        "note": "Measured five-dimensional frozen-program comparisons. Response decisions and checkpoints are descriptive repeated measurements, not independent replications."})
    print(f"Comparison figures saved to {output}", flush=True)
