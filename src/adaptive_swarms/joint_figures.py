"""Prospectively specified v3 figures from saved final outcomes only.

This module never executes candidate/simulator code or generates statistical
resamples. Inferential intervals come from the frozen study analysis.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .allocation_figures import regime, regime_label, recovery_case_curve
from .artifacts import read_json
from .comparison import regime_key
from .figures import _save, _style
from .logging import atomic_json


COLORS = ["#187b80", "#d47b34", "#7057a3", "#bb4260", "#477ab2",
          "#778c36", "#91624d", "#697988"]
RADIUS_EDGES = [.5, 1., 2., 4.]
RADIUS_LABELS = ["0", "(0, .5]", "(.5, 1]", "(1, 2]", "(2, 4]", ">4"]


def _regime_key(group):
    return regime_key({"dimension": 5, "npeaks": 10, "correlation": 0.,
                       "move_severity": group[0], "period": group[1]})


def interval(contrast):
    """Accept explicitly level-labelled analysis, never relabel a 95% band."""
    level = float(contrast["interval_level"])
    if "bootstrap_interval" in contrast:
        bounds = contrast["bootstrap_interval"]
    else:
        key = "bootstrap_97_5_percent_interval" if level == .975 else "bootstrap_95_percent_interval"
        bounds = contrast[key]
    if bounds is None or len(bounds) != 2 or not np.all(np.isfinite(bounds)):
        raise ValueError("A completed finite paired bootstrap interval is required")
    return level, bounds


def action_pair(response):
    count = response["requested_count"]
    radius = response["requested_radius_scale"]
    if count != response["allocated_count"] or count != len(response["relocated_indices"]):
        raise ValueError("Saved requested and allocated counts disagree")
    if response["allocated_fraction"] != count / response["observation"]["swarm_size"]:
        raise ValueError("Allocated fraction must mean count / swarm size")
    return int(count), float(radius)


def _case_pairs(case):
    """Respect explicit constant-alias nominal actions without rewriting traces."""
    from .joint_study import nominal_action_pairs
    pairs = [(int(count), float(radius)) for count, radius in nominal_action_pairs(case)]
    if len(pairs) != len(case["response_log"]):
        raise ValueError("Nominal action projection must align with actual response times")
    return pairs


def pair_histogram(pairs):
    """Fixed bins include an exact-zero radius cell; retain exact pairs elsewhere."""
    values = np.zeros((6, 6))
    for count, radius in pairs:
        if not (0 <= count <= 5 and np.isfinite(radius) and radius >= 0):
            raise ValueError("Invalid saved joint action")
        column = 0 if radius == 0 else 1 + int(np.searchsorted(RADIUS_EDGES, radius, side="left"))
        values[count, column] += 1
    return values / len(pairs) if pairs else None


def summarize_pairs(case_pairs):
    observed = [pairs for pairs in case_pairs if pairs]
    histograms = [pair_histogram(pairs) for pairs in observed]
    exact = Counter()
    for pairs in observed:
        for pair, number in Counter(pairs).items():
            exact[pair] += number / len(pairs) / len(observed)
    return {"histogram": np.mean(histograms, axis=0).tolist() if observed else np.zeros((6, 6)).tolist(),
            "independent_cases": len(case_pairs), "no_response_cases": len(case_pairs) - len(observed),
            "exact_pairs": [{"count": count, "radius_scale": radius, "probability": probability}
                            for (count, radius), probability in sorted(exact.items())]}


def _effect_panel(ax, contrast, title, groups, negative_label="Negative favors overall winner"):
    level, bounds = interval(contrast)
    for index, group in enumerate(groups):
        key = _regime_key(group)
        values = [case["delta"] for case in contrast["cases"] if case["regime"] == key]
        if not values:
            raise ValueError(f"Missing paired cases in {key}")
        y = len(groups) - index
        ax.scatter(values, y + np.linspace(-.15, .15, len(values)), color=COLORS[index], s=17, alpha=.72)
        ax.scatter(np.mean(values), y, color="#243447", marker="D", s=44, zorder=4)
    ax.plot(bounds, [0, 0], color="#243447", lw=3)
    ax.scatter(contrast["mean_delta"], 0, color="#243447", marker="D", s=62, zorder=4)
    ax.axvline(0, color="#8796a5", ls="--", lw=1)
    ax.axhline(.5, color="#c5cdd5", lw=.7)
    ax.set_yticks([*range(len(groups), 0, -1), 0],
                 [*(regime_label(group) for group in groups), f"Equal-regime mean\n{100 * level:g}% interval"])
    ax.set(title=title, xlabel=f"Paired offline-error difference\n{negative_label}")
    ax.grid(alpha=.16, axis="x")


def _save_effects(cases, analysis, overall, labels, output):
    groups = sorted({regime(case) for case in cases[overall]})
    comparisons = analysis["comparisons"]
    fig, axes = plt.subplots(1, 2, figsize=(12.6, 5.8), constrained_layout=True)
    for ax, comparator, title in zip(axes, ["baseline", "best_fixed"],
                                    ["Overall winner − corrected baseline", "Overall winner − selected fixed pair"]):
        contrast = comparisons[f"{overall}_minus_{comparator}"]
        if interval(contrast)[0] != .975:
            raise ValueError("Both primary contrasts must use two-sided 97.5% intervals")
        _effect_panel(ax, contrast, title, groups)
    fig.suptitle("Joint relocation · two predeclared primary comparisons", fontsize=14)
    fig.supxlabel("Dots: independent paired cases; diamonds: means. Paired bootstrap resamples within four equally weighted regimes.\n"
                  "Two 97.5% intervals give an approximate Bonferroni 95% family; superiority to both requires both upper bounds below zero.", fontsize=9)
    _save(fig, output / "primary_effects")

    winners = sorted(name for name in cases if name.startswith("winner_search_"))
    fig, axes = plt.subplots(3, 2, figsize=(12.6, 13.8), constrained_layout=True)
    for row, winner in enumerate(winners):
        for ax, comparator in zip(axes[row], ["baseline", "best_fixed"]):
            _effect_panel(ax, comparisons[f"{winner}_minus_{comparator}"],
                          f"{labels[winner]} − {labels[comparator]}", groups,
                          negative_label="Negative favors this search winner")
    fig.suptitle("All three validation-selected search winners", fontsize=14)
    fig.supxlabel("All winners share the same 80 final histories: these are not 240 independent cases.\n"
                  "Overall-winner primary bands: 97.5%. Other winner bands: descriptive 95%; three searches give limited reliability evidence.", fontsize=9)
    _save(fig, output / "search_winner_effects")

    fig, axes = plt.subplots(2, 2, figsize=(12., 7.6), constrained_layout=True)
    methods = [*winners, "baseline", "best_fixed"]
    means = {}
    for ax, group in zip(axes.flat, groups):
        group_means = []
        for index, method in enumerate(methods):
            values = [case["offline_error"] for case in cases[method] if regime(case) == group]
            ax.scatter(index + np.linspace(-.15, .15, len(values)), values, s=14, alpha=.6, color=COLORS[index])
            ax.scatter(index, np.mean(values), marker="D", s=64, color="#243447", zorder=4)
            group_means.append(float(np.mean(values)))
        ax.set(title=regime_label(group), ylabel="Final offline error (lower is better)")
        ax.set_xticks(range(len(methods)), [labels[method].replace(" · overall", "*") for method in methods], rotation=22, ha="right", fontsize=8)
        ax.grid(alpha=.16, axis="y")
        means[regime_label(group)] = dict(zip(methods, group_means))
    fig.suptitle("Final outcomes from each independently searched winner", fontsize=14)
    fig.supxlabel("Dots: cases; diamonds: means. *Overall winner was chosen on validation, before final seeds existed.", fontsize=9)
    _save(fig, output / "search_winner_outcomes")

    fig, axes = plt.subplots(2, 2, figsize=(12.6, 10.5), constrained_layout=True)
    contrasts = [(comparisons[f"{overall}_minus_radius_replaced"], "Overall − radius replaced"),
                 (comparisons[f"{overall}_minus_count_replaced"], "Overall − count replaced"),
                 (comparisons[f"{overall}_minus_joint_sampler"], "Overall − state-free joint sampler"),
                 (analysis["interaction"], "Interaction: E − radius replaced − count replaced + fixed")]
    for ax, (contrast, title) in zip(axes.flat, contrasts):
        if interval(contrast)[0] != .95:
            raise ValueError("Mechanism and interaction intervals must be descriptive 95% intervals")
        _effect_panel(ax, contrast, title, groups,
                      negative_label="Negative joint deviation from additive component effects" if contrast is analysis["interaction"] else "Negative favors overall winner")
    fig.suptitle("Component and state-association diagnostics · descriptive 95% intervals", fontsize=14)
    fig.supxlabel("Substitutions act on each method's reached state. The sampler preserves validation joint pairs but changes state association and temporal dependence.\n"
                  "These closed-loop comparisons and the interaction are not isolated causal effects of a single observation.", fontsize=9)
    _save(fig, output / "component_effects")
    return means


def _save_joint_distributions(cases, overall, targets, output):
    groups = sorted({regime(case) for case in cases[overall]})
    fig, axes = plt.subplots(4, 3, figsize=(12.4, 12.8), constrained_layout=True)
    records = {}
    for row, group in enumerate(groups):
        group_data = {"validation_target": summarize_pairs(targets[group])}
        for method in [overall, "joint_sampler"]:
            group_data[method] = summarize_pairs([_case_pairs(case)
                                                 for case in cases[method] if regime(case) == group])
        for column, (key, title) in enumerate([( "validation_target", "Frozen validation joint mix"),
                                              (overall, "Final overall winner"), ("joint_sampler", "Final joint sampler")]):
            ax = axes[row, column]
            shown = ax.imshow(np.asarray(group_data[key]["histogram"]) * 100, origin="lower", aspect="auto", vmin=0, vmax=100, cmap="Blues")
            ax.set(title=f"{regime_label(group)}\n{title}", ylabel="Allocated particle count", yticks=range(6))
            ax.set_xticks(range(6), RADIUS_LABELS, rotation=35, ha="right", fontsize=8)
            if row == 3:
                ax.set_xlabel("Radius multiplier (fixed display bins)")
        records[regime_label(group)] = group_data
    fig.colorbar(shown, ax=axes, shrink=.7, label="Mean within-case joint action probability (%)")
    fig.suptitle("Joint count × radius distributions · equal independent-case weighting", fontsize=14)
    fig.supxlabel("Exact count/radius pairs remain in the figure provenance; display bins are fixed before outcomes.\n"
                  "Final no-response cases are omitted and counted explicitly; validation fallback follows the frozen sampler definition.\n"
                  "Proven constant aliases display their nominal action pairs; the shared execution checkpoint is retained unchanged.", fontsize=9)
    _save(fig, output / "joint_action_distributions")
    return records


def _state(response, feature):
    obs = response["observation"]
    if feature == "relative_fitness_drop":
        return float(obs[feature])
    return float(obs["swarm_diameter"] / max(obs["default_radius"], 1e-12))


def _save_conditional(cases, overall, output):
    groups = sorted({regime(case) for case in cases[overall]})
    records = {}
    for feature, label, stem in [("relative_fitness_drop", "Observed relative fitness loss", "joint_actions_by_fitness_loss"),
                                  ("relative_diameter", "Swarm diameter / known default radius", "joint_actions_by_diameter")]:
        fig, axes = plt.subplots(4, 2, figsize=(12., 12.), constrained_layout=True)
        feature_records = {}
        for row, group in enumerate(groups):
            grouped = {method: [case for case in cases[method] if regime(case) == group]
                       for method in [overall, "joint_sampler"]}
            observed = [_state(response, feature) for method_cases in grouped.values()
                        for case in method_cases for response in case["response_log"]]
            if not observed:
                for ax in axes[row]:
                    ax.set_visible(False)
                feature_records[regime_label(group)] = {"no_observations": True}
                continue
            edges = np.unique(np.quantile(observed, [0, .25, .5, .75, 1]))
            if len(edges) == 1:
                edges = np.repeat(edges, 2)
            bins = len(edges) - 1
            group_record = {"bin_edges": edges.tolist(), "methods": {}}
            for index, (method, values) in enumerate(grouped.items()):
                case_means, response_counts = [], np.zeros(bins, dtype=int)
                for case in values:
                    bucket = [[] for _ in range(bins)]
                    for response, pair in zip(case["response_log"], _case_pairs(case)):
                        b = int(np.searchsorted(edges[1:-1], _state(response, feature), side="right"))
                        bucket[b].append(pair); response_counts[b] += 1
                    case_means.append([np.mean(value, axis=0) if value else [np.nan, np.nan] for value in bucket])
                array = np.asarray(case_means)
                contributing = np.sum(np.isfinite(array[:, :, 0]), axis=0)
                means = np.divide(np.nansum(array, axis=0), contributing[:, None],
                                  out=np.full((bins, 2), np.nan), where=contributing[:, None] > 0)
                for column, ax in enumerate(axes[row]):
                    ax.plot(range(bins), means[:, column], color=COLORS[index], marker="o", label="Overall winner" if method == overall else "Joint sampler")
                group_record["methods"][method] = {"mean_count_radius": [[float(x) if np.isfinite(x) else None for x in value] for value in means],
                    "contributing_cases": contributing.tolist(), "response_counts": response_counts.tolist()}
            for column, ax in enumerate(axes[row]):
                ax.set(title=regime_label(group), ylabel="Mean allocated count" if column == 0 else "Mean radius multiplier")
                ax.set_xticks(range(bins), [f"{edges[i]:.3g} to {edges[i+1]:.3g}" for i in range(bins)], fontsize=8)
                ax.set_xlabel(f"{label}\nShared final observation bins (low → high)")
                ax.grid(alpha=.16, axis="y")
                if column == 0:
                    ax.set_ylim(-.15, 5.15)
            feature_records[regime_label(group)] = group_record
        axes[0, 0].legend(frameon=False, fontsize=8)
        fig.suptitle(f"Joint actions and public state · {label.lower()}", fontsize=14)
        fig.supxlabel("Bin edges: pooled observed final states within each regime; equal case means within occupied bins. No response-level uncertainty.\n"
                      "These repeated, trajectory-dependent observations describe association. Known default radius precedes the current action.", fontsize=9)
        _save(fig, output / stem)
        records[feature] = feature_records
    return records


def _save_tracking_and_recovery(cases, labels, output):
    groups = sorted({regime(case) for case in next(iter(cases.values()))})
    fig, axes = plt.subplots(2, 2, figsize=(12.2, 8.1), constrained_layout=True)
    traces = {method: [{point["evaluations"]: point for point in case["trace"]} for case in values]
              for method, values in cases.items()}
    common = set.intersection(*(set(trace) for values in traces.values() for trace in values))
    if not common:
        raise ValueError("No shared measured trajectory checkpoints")
    grid = sorted(common)
    accounting = {}
    for index, (method, values) in enumerate(cases.items()):
        for ax, field in [(axes[0, 0], "offline_error"), (axes[0, 1], "swarm_count")]:
            ax.plot(np.asarray(grid) / 1000, np.mean([[trace[e][field] for e in grid] for trace in traces[method]], axis=0),
                    color=COLORS[index], label=labels[method], lw=1.6)
        end_error = [np.mean([np.mean([change["environment_final_error"] for change in case["environment_changes"]])
                             for case in values if regime(case) == group]) for group in groups]
        axes[1, 0].plot(range(len(groups)), end_error, marker="o", color=COLORS[index])
        accounting[method] = {"evaluations": [case["evaluations"] for case in values],
            "requested": sum(response["requested_count"] for case in values for response in case["response_log"]),
            "allocated": sum(response["allocated_count"] for case in values for response in case["response_log"]),
            "evaluated_relocations": sum(response["evaluated_relocation_count"] for case in values for response in case["response_log"]),
            "incomplete_responses": sum(not response["completed"] for case in values for response in case["response_log"])}
    axes[0, 0].set(title="Mean cumulative offline error", ylabel="Offline error", yscale="symlog")
    axes[0, 1].set(title="Mean active subswarms", ylabel="Subswarm count")
    axes[0, 0].legend(frameon=False, fontsize=7, ncol=2)
    for ax in axes[0]:
        ax.set_xlabel("Objective evaluations (thousands)"); ax.grid(alpha=.16)
    axes[1, 0].set(title="Error remaining before next change", ylabel="Mean interval-end error")
    axes[1, 0].set_xticks(range(len(groups)), [regime_label(group).replace(" · ", "\n") for group in groups], fontsize=8)
    axes[1, 0].grid(alpha=.16, axis="y")
    kinds = sorted({kind for values in cases.values() for case in values for kind in case["evaluation_counts"]})
    left = np.zeros(len(cases))
    for index, kind in enumerate(kinds):
        shares = np.asarray([np.mean([case["evaluation_counts"].get(kind, 0) / case["evaluations"] for case in values]) * 100 for values in cases.values()])
        axes[1, 1].barh(range(len(cases)), shares, left=left, color=COLORS[index], label=kind); left += shares
    axes[1, 1].set_yticks(range(len(cases)), [labels[method] for method in cases], fontsize=8)
    axes[1, 1].set(title="All objective queries are charged", xlabel="Objective-query budget (%)", xlim=(0, 100))
    axes[1, 1].legend(frameon=False, fontsize=7, ncol=3, loc="upper left", bbox_to_anchor=(0, -.16))
    fig.suptitle("Tracking and query accounting · all frozen final methods", fontsize=14)
    fig.supxlabel("Means over independent cases. Checkpoints and change intervals are repeated measurements.\n"
                  "Detection and memory refresh remain inside every exact 100,000-query budget; allocated particles need not all be queried at truncation.", fontsize=9)
    _save(fig, output / "tracking_diagnostics")

    fig, axes = plt.subplots(2, 2, figsize=(12.2, 8.), constrained_layout=True)
    records = {}
    for ax, group in zip(axes.flat, groups):
        curves = {method: [recovery_case_curve(case) for case in values if regime(case) == group] for method, values in cases.items()}
        offsets = sorted(set.intersection(*(set(curve["offsets"]) for values in curves.values() for curve in values)))
        if not offsets:
            raise ValueError("No common measured recovery offsets")
        records[regime_label(group)] = {"measured_offsets": offsets, "methods": {}}
        for index, (method, values) in enumerate(curves.items()):
            means = np.mean([[curve["offsets"][offset]["mean_current_error"] for offset in offsets] for curve in values], axis=0)
            ax.plot(np.asarray(offsets) / 1000, means, marker="o", ms=3, lw=1.5, color=COLORS[index], label=labels[method])
            records[regime_label(group)]["methods"][method] = {"mean_current_error": means.tolist(), "case_curves": values}
        ax.set(title=regime_label(group), xlabel="Objective evaluations after change (thousands)", ylabel="Mean best-discovered tracking error")
        ax.grid(alpha=.16)
    axes.flat[0].legend(frameon=False, fontsize=7, ncol=2)
    fig.suptitle("Recovery after change · measured 5D tracking error", fontsize=14)
    fig.supxlabel("Initial environment excluded; environments averaged within each case, then cases weighted equally.\n"
                  "Markers: saved offsets. Lines only join measurements; no unsampled immediate response is inferred.\n"
                  "Boundary query belongs to prior environment: offset=((evaluations−1) mod period)+1. Repeated measurements supply no independent-case uncertainty.", fontsize=9)
    _save(fig, output / "recovery_after_change")
    return {"query_accounting": accounting, "recovery": records}


def _target_pairs(selection, cases):
    records = selection["joint_sampler"]["regime_cases"]
    result = {}
    for group in sorted({regime(case) for case in cases}):
        key = _regime_key(group)
        result[group] = []
        for case in records[key]:
            pairs = []
            for value in case["action_pairs"]:
                pairs.append((int(value["count"]), float(value["radius_scale"])) if isinstance(value, dict) else (int(value[0]), float(value[1])))
            result[group].append(pairs or [(5, 1.)])
    return result


def render_joint_study(run_dir: Path, output: Path | None = None):
    """Render completed frozen analysis; verify case pairing and interval labels."""
    from .joint_study import load_stage_outcomes
    run_dir = Path(run_dir).resolve()
    output = output or run_dir / "figures"
    analysis, selection = read_json(run_dir / "analysis.json"), read_json(run_dir / "selection.json")
    if analysis.get("status") != "completed":
        raise ValueError("V3 figures require completed final analysis")
    manifest, cases = load_stage_outcomes(run_dir, "final")
    overall = selection["overall_winner_method"]
    methods = [*(f"winner_search_{i}" for i in range(3)), "baseline", "best_fixed", "radius_replaced", "count_replaced", "joint_sampler"]
    cases = {method: cases[method] for method in methods}
    expected = [case["config"] for case in cases[overall]]
    if len(expected) != 80 or sorted(Counter(regime(case) for case in cases[overall]).values()) != [20, 20, 20, 20]:
        raise ValueError("V3 figures require all 80 planned independent cases, 20 per regime")
    for method, values in cases.items():
        if [case["config"] for case in values] != expected:
            raise ValueError(f"Unpaired case configurations for {method}")
        for case in values:
            if case["evaluations"] != 100000 or sum(case["evaluation_counts"].values()) != 100000:
                raise ValueError("Final budget/accounting mismatch")
            for response in case["response_log"]:
                action_pair(response)
    for name, contrast in analysis["comparisons"].items():
        method, comparator = name.split("_minus_", 1)
        actual = [a["offline_error"] - b["offline_error"] for a, b in zip(cases[method], cases[comparator])]
        if actual != [case["delta"] for case in contrast["cases"]]:
            raise ValueError(f"Saved contrast disagrees with final checkpoints: {name}")
    actual_interaction = [e["offline_error"] - r["offline_error"] - c["offline_error"] + f["offline_error"]
                          for e, r, c, f in zip(cases[overall], cases["radius_replaced"], cases["count_replaced"], cases["best_fixed"])]
    if not np.allclose(actual_interaction, [case["delta"] for case in analysis["interaction"]["cases"]], rtol=0, atol=1e-12):
        raise ValueError("Saved interaction disagrees with final checkpoints")
    labels = {f"winner_search_{i}": f"Search {i+1} winner" + (" · overall" if overall == f"winner_search_{i}" else "") for i in range(3)}
    labels.update(baseline="Corrected baseline", best_fixed="Selected fixed pair", radius_replaced="Radius replaced", count_replaced="Count replaced", joint_sampler="Joint sampler")
    output.mkdir(parents=True, exist_ok=True); _style()
    means = _save_effects(cases, analysis, overall, labels, output)
    distributions = _save_joint_distributions(cases, overall, _target_pairs(selection, cases[overall]), output)
    state = _save_conditional(cases, overall, output)
    tracking = _save_tracking_and_recovery(cases, labels, output)
    names = ["primary_effects", "search_winner_effects", "search_winner_outcomes", "component_effects",
             "joint_action_distributions", "joint_actions_by_fitness_loss", "joint_actions_by_diameter",
             "tracking_diagnostics", "recovery_after_change"]
    paths = [run_dir / name for name in ("analysis.json", "selection.json", "shortlists.json", "source_review.json", "final_cases.json", "final/manifest.json")]
    paths += sorted({run_dir / "final" / path for values in manifest["case_artifacts"].values() for path in values})
    provenance = {"generated_at": datetime.now(timezone.utc).isoformat(), "input_run": str(run_dir),
        "independent_final_cases": 80, "dimension": 5, "case_budget": 100000, "methods": labels,
        "overall_winner_method": overall, "aliases": manifest["aliases"], "winner_regime_means": means,
        "nominal_action_projections": {method: [{"case_index": i, **case["nominal_action_projection"]}
            for i, case in enumerate(values) if case.get("nominal_action_projection")] for method, values in cases.items()},
        "joint_distributions": distributions, "conditional_state": state, **tracking,
        "radius_display_bins": RADIUS_LABELS,
        "interpretation": "Saved outcomes only: no candidate/model/objective calls. Equal independent-case weighting; observations and checkpoints are repeated measurements. Component and state-association contrasts alter closed-loop trajectories.",
        "inputs_sha256": {str(path.relative_to(run_dir)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
        "rendering_sources_sha256": {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest() for name in ("joint_figures.py", "allocation_figures.py", "figures.py")},
        "outputs_sha256": {f"{name}.{ext}": hashlib.sha256((output / f"{name}.{ext}").read_bytes()).hexdigest() for name in names for ext in ("png", "svg")}}
    atomic_json(output / "joint_figure_provenance.json", provenance)
    print(f"[{provenance['generated_at']}] Saved 9 measured v3 figure pairs to {output}; candidate executions: 0", flush=True)
    return provenance
