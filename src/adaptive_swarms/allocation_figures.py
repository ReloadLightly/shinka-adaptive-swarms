"""Measured v2 allocation figures; rendering never executes a candidate."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .artifacts import read_json
from .figures import COLORS, _save, _style
from .logging import atomic_json


def regime(case: dict) -> tuple[float, int]:
    config = case["config"]
    return float(config["move_severity"]), int(config["period"])


def regime_label(value) -> str:
    severity, period = value
    return f"Shift {severity:g} · period {period:,}"


def count_value(response: dict) -> int:
    return response.get("executed_count", len(response["relocated_indices"]))


def case_distribution(case: dict) -> np.ndarray | None:
    responses = case["response_log"]
    if not responses:
        return None
    counts = Counter(count_value(response) for response in responses)
    return np.asarray([counts[k] / len(responses) for k in range(6)])


def average_distributions(cases: list[dict]) -> tuple[np.ndarray, int]:
    """Equal case weight; no-response cases have no empirical action mix."""
    distributions = [case_distribution(case) for case in cases]
    observed = [value for value in distributions if value is not None]
    return (np.mean(observed, axis=0) if observed else np.zeros(6),
            len(distributions) - len(observed))


def _save_pair_effects(cases, contrasts, output):
    evolved = cases["evolved"]
    regimes = sorted({regime(case) for case in evolved})
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.4), constrained_layout=True)
    titles = [("primary", "Primary: evolved − selected constant"),
              ("mechanism", "Mechanism: evolved − state-free control")]
    records = {}
    for ax, (name, title) in zip(axes, titles):
        contrast = contrasts[name]
        comparator = "constant" if name == "primary" else "control"
        delta = np.asarray([a["offline_error"] - b["offline_error"]
                            for a, b in zip(evolved, cases[comparator])])
        for index, group in enumerate(regimes):
            values = delta[[regime(case) == group for case in evolved]]
            y = len(regimes) - index
            ax.scatter(values, y + np.linspace(-.14, .14, len(values)),
                       s=24, alpha=.78, color=COLORS[index % len(COLORS)], zorder=3)
            ax.scatter(np.mean(values), y, s=64, marker="D", color="#243447", zorder=4)
        mean = contrast["mean_delta"]
        interval = contrast["bootstrap_95_percent_interval"]
        ax.plot(interval, [0, 0], lw=3, color="#243447", zorder=3)
        ax.scatter(mean, 0, s=80, marker="D", color="#243447", zorder=4)
        ax.axvline(0, color="#8796a5", ls="--", lw=1)
        ax.axhline(.5, color="#c5cdd5", lw=.8)
        ax.set_yticks([*range(len(regimes), 0, -1), 0],
                      [*(regime_label(group) for group in regimes), "Equal-regime mean\n95% bootstrap interval"])
        ax.set(title=title, xlabel="Paired offline-error difference\nNegative favors evolved allocation")
        ax.grid(alpha=.16, axis="x")
        records[name] = {"case_differences": delta.tolist(), "mean_delta": mean,
                         "bootstrap_95_percent_interval": interval}
    fig.suptitle(f"Frozen allocation comparison · 5D · {len(evolved)} independent paired histories", fontsize=14)
    fig.supxlabel("Dots: cases. Diamonds: means. Interval: 20,000 paired resamples within four equally weighted regimes.\n"
                  "The mechanism contrast is predeclared; its interval is descriptive.", fontsize=9)
    _save(fig, output / "primary_mechanism_effects")
    return records


def _save_distributions(cases, targets, output):
    regimes = sorted({regime(case) for case in cases["evolved"]})
    fig, axes = plt.subplots(2, 2, figsize=(11.8, 7.0), constrained_layout=True)
    records = {}
    for ax, group in zip(axes.flat, regimes):
        evolved, missing_evolved = average_distributions([case for case in cases["evolved"] if regime(case) == group])
        control, missing_control = average_distributions([case for case in cases["control"] if regime(case) == group])
        target = np.asarray(targets[group])
        for offset, values, color, label in [(-.25, target, "#8796a5", "Frozen validation mix"),
                                             (0, evolved, COLORS[0], "Final evolved"),
                                             (.25, control, COLORS[1], "Final state-free control")]:
            ax.bar(np.arange(6) + offset, values * 100, width=.23, color=color, label=label)
        ax.set(title=regime_label(group), xlabel="Particles allocated to relocation", ylabel="Mean within-case responses (%)",
               xticks=range(6), ylim=(0, 103))
        ax.grid(alpha=.16, axis="y")
        records[regime_label(group)] = {"validation_target": target.tolist(),
            "final_evolved": evolved.tolist(), "final_control": control.tolist(),
            "evolved_no_response_cases": missing_evolved, "control_no_response_cases": missing_control}
    axes.flat[0].legend(frameon=False, fontsize=8)
    fig.suptitle("Allocation distributions · each independent case receives equal weight", fontsize=14)
    fig.supxlabel("The control samples a frozen regime-specific distribution with an independent RNG.\n"
                  "Final proportions can differ through sampling and changed optimizer trajectories.", fontsize=9)
    _save(fig, output / "allocation_distributions")
    return records


def _state_value(response, feature):
    observation = response["observation"]
    if feature == "relative_fitness_drop":
        return observation[feature]
    return observation["swarm_diameter"] / max(observation["default_radius"] * 2, 1e-12)


def _save_state(cases, output):
    regimes = sorted({regime(case) for case in cases["evolved"]})
    features = [("relative_fitness_drop", "Observed relative fitness loss"),
                ("relative_diameter", "Swarm diameter / relocation radius")]
    fig, axes = plt.subplots(4, 2, figsize=(12.0, 12.2), constrained_layout=True)
    records = {}
    for row, group in enumerate(regimes):
        group_cases = {method: [case for case in cases[method] if regime(case) == group]
                       for method in ("evolved", "control")}
        for column, (feature, label) in enumerate(features):
            ax = axes[row, column]
            observations = [_state_value(response, feature) for method_cases in group_cases.values()
                            for case in method_cases for response in case["response_log"]]
            if not observations:
                ax.set_visible(False)
                continue
            edges = np.unique(np.quantile(observations, [0, .25, .5, .75, 1]))
            if len(edges) == 1:
                edges = np.asarray([edges[0], edges[0]])
            bins = max(1, len(edges) - 1)
            data = {}
            for method, color, method_label in [("evolved", COLORS[0], "Evolved"),
                                                 ("control", COLORS[1], "State-free control")]:
                per_case = []
                responses_per_bin = np.zeros(bins, dtype=int)
                for case in group_cases[method]:
                    values = [[] for _ in range(bins)]
                    for response in case["response_log"]:
                        index = min(bins - 1, int(np.searchsorted(edges[1:-1], _state_value(response, feature), side="right")))
                        values[index].append(count_value(response))
                        responses_per_bin[index] += 1
                    per_case.append([np.mean(value) if value else np.nan for value in values])
                array = np.asarray(per_case)
                contributing = np.sum(np.isfinite(array), axis=0)
                means = np.divide(np.nansum(array, axis=0), contributing,
                                  out=np.full(bins, np.nan), where=contributing > 0)
                ax.plot(range(bins), means, marker="o", ms=5, color=color, label=method_label)
                data[method] = {"mean_count": [float(x) if np.isfinite(x) else None for x in means],
                                "contributing_cases": contributing.tolist(),
                                "response_counts": responses_per_bin.tolist()}
            ax.set(title=f"{regime_label(group)} · {label}", ylim=(-.15, 5.15),
                   ylabel="Mean relocation count", xlabel="Shared observation bins (low → high)")
            ax.set_xticks(range(bins), [f"{edges[i]:.3g} to {edges[i+1]:.3g}" for i in range(bins)], fontsize=8)
            ax.grid(alpha=.16, axis="y")
            if row == 0 and column == 0:
                ax.legend(frameon=False, fontsize=8)
            records[f"{regime_label(group)} / {feature}"] = {"bin_edges": edges.tolist(), **data}
    fig.suptitle("Allocation and observed state · descriptive within-case averages", fontsize=14)
    fig.supxlabel("Bin edges: pooled final observations within each regime. Cases contribute equally within occupied bins.\n"
                  "Responses are repeated measurements. State, action and subsequent recovery share trajectory dependence; these lines are not causal effects.", fontsize=9)
    _save(fig, output / "allocation_by_observed_state")
    return records


def _save_tracking(cases, method_labels, output):
    fig, axes = plt.subplots(2, 2, figsize=(12.0, 8.2), constrained_layout=True)
    methods = list(cases)
    trace_maps = {method: [{point["evaluations"]: point for point in case["trace"]}
                           for case in values] for method, values in cases.items()}
    common = set.intersection(*(set(trace) for values in trace_maps.values() for trace in values))
    if not common:
        raise ValueError("No common measured trajectory checkpoints to average")
    grid = np.asarray(sorted(common))
    for index, method in enumerate(methods):
        color = COLORS[index % len(COLORS)]
        for ax, field in [(axes[0, 0], "offline_error"), (axes[0, 1], "swarm_count")]:
            trajectories = [[trace[evaluation][field] for evaluation in grid]
                            for trace in trace_maps[method]]
            ax.plot(grid / 1000, np.mean(trajectories, axis=0), color=color,
                    label=method_labels[method], lw=1.6)
    axes[0, 0].set(title="Mean cumulative offline error", ylabel="Offline error", yscale="symlog")
    axes[0, 1].set(title="Mean active subswarms", ylabel="Subswarm count")
    for ax in axes[0]:
        ax.set_xlabel("Objective evaluations (thousands)")
        ax.grid(alpha=.16)
    axes[0, 0].legend(frameon=False, fontsize=8)
    regimes = sorted({regime(case) for case in cases["evolved"]})
    for index, method in enumerate(methods):
        values = []
        for group in regimes:
            case_means = [np.mean([change["environment_final_error"] for change in case["environment_changes"]])
                          for case in cases[method] if regime(case) == group]
            values.append(np.mean(case_means))
        axes[1, 0].plot(range(len(regimes)), values, marker="o", color=COLORS[index % len(COLORS)])
    axes[1, 0].set_xticks(range(len(regimes)), [regime_label(group).replace(" · ", "\n") for group in regimes], fontsize=8)
    axes[1, 0].set(title="Error remaining before the next change", ylabel="Mean interval-end error")
    axes[1, 0].grid(alpha=.16, axis="y")
    kinds = sorted({kind for method in methods for case in cases[method] for kind in case["evaluation_counts"]})
    left = np.zeros(len(methods))
    for index, kind in enumerate(kinds):
        shares = np.asarray([np.mean([case["evaluation_counts"].get(kind, 0) / case["evaluations"] for case in cases[method]]) * 100
                             for method in methods])
        axes[1, 1].barh(range(len(methods)), shares, left=left, label=kind, color=COLORS[index % len(COLORS)])
        left += shares
    axes[1, 1].set_yticks(range(len(methods)), [method_labels[method] for method in methods], fontsize=8)
    axes[1, 1].set(xlim=(0, 100), title="All objective queries are charged", xlabel="Objective-query budget (%)")
    axes[1, 1].legend(frameon=False, ncol=3, fontsize=8, loc="upper left", bbox_to_anchor=(0, -.16))
    fig.suptitle("Tracking and evaluation use · means over independent final cases", fontsize=14)
    fig.supxlabel("Trajectory checkpoints and environment intervals are repeated measurements; figures show descriptive means.\n"
                  "Detection and personal-memory reevaluation remain within each exact 100,000-query budget.", fontsize=9)
    _save(fig, output / "tracking_diagnostics")


def render_allocation_data(cases: dict[str, list[dict]], contrasts: dict, targets: dict,
                           method_labels: dict, output: Path, provenance: dict):
    """Render an already loaded, verified, completed final comparison."""
    output.mkdir(parents=True, exist_ok=True)
    _style()
    paired = _save_pair_effects(cases, contrasts, output)
    distributions = _save_distributions(cases, targets, output)
    state = _save_state(cases, output)
    _save_tracking(cases, method_labels, output)
    provenance.update(generated_at=datetime.now(timezone.utc).isoformat(),
        primary_and_mechanism=paired, distributions=distributions, observed_state=state,
        interpretation="Measured 5D final outcomes. No model calls, candidate executions or objective evaluations. Responses/checkpoints are repeated measurements, not independent cases.",
        outputs_sha256={path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                        for stem in ("primary_mechanism_effects", "allocation_distributions",
                                     "allocation_by_observed_state", "tracking_diagnostics")
                        for path in (output / f"{stem}.png", output / f"{stem}.svg")})
    atomic_json(output / "allocation_figure_provenance.json", provenance)
    print(f"[{provenance['generated_at']}] Saved measured v2 allocation figures to {output}; candidate executions: 0", flush=True)
    return provenance


def render_allocation_study(run_dir: Path, output: Path | None = None):
    """Load the protocol runner's immutable stages, retaining explicit aliases."""
    from .allocation_study import load_stage_outcomes
    from .comparison import regime_key

    run_dir = Path(run_dir).resolve()
    analysis = read_json(run_dir / "analysis.json")
    selection = read_json(run_dir / "selection.json")
    if analysis.get("status") != "completed":
        raise ValueError("V2 figures require completed final analysis")
    manifest, outcomes = load_stage_outcomes(run_dir, "final")
    rename = {"baseline": "baseline", "constant_three": "constant_three",
              "best_constant": "constant", "evolved": "evolved", "state_free_control": "control"}
    cases = {rename[name]: values for name, values in outcomes.items()}
    if len(cases["evolved"]) != 40:
        raise ValueError("V2 figures require all 40 planned independent final cases")
    contrasts = {"primary": analysis["comparisons"]["evolved_minus_best_constant"],
                 "mechanism": analysis["comparisons"]["evolved_minus_state_free_control"]}
    for contrast, comparator in ((contrasts["primary"], "constant"), (contrasts["mechanism"], "control")):
        actual = [a["offline_error"] - b["offline_error"] for a, b in zip(cases["evolved"], cases[comparator])]
        if actual != [case["delta"] for case in contrast["cases"]]:
            raise ValueError("Saved inferential analysis does not match final checkpoints")
    targets = {regime(case): selection["control"]["distributions"][regime_key(case["config"])]
               for case in cases["evolved"]}
    labels = {"baseline": "Corrected baseline", "constant_three": "Count three",
              "constant": f"Selected constant ({selection['selected_constant']})",
              "evolved": "Selected evolved", "control": "State-free control"}
    paths = [run_dir / name for name in ("analysis.json", "selection.json", "shortlist.json",
                                        "source_review.json", "final_cases.json", "final/manifest.json")]
    paths += sorted({run_dir / "final" / path for values in manifest["case_artifacts"].values() for path in values})
    provenance = {"input_run": str(run_dir), "dimension": 5, "independent_cases": 40,
                  "case_budget": 100000, "methods": labels, "aliases": manifest["aliases"],
                  "inputs_sha256": {str(path.relative_to(run_dir)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
                  "state_bin_weighting": "Equal-case means within bins occupied by that case; bin edges from pooled final observations of evolved/control.",
                  "distribution_weighting": "Equal-case means; final cases with no observed response are omitted and counted explicitly, with no imputed empirical actions."}
    return render_allocation_data(cases, contrasts, targets, labels,
                                  output or run_dir / "figures", provenance)
