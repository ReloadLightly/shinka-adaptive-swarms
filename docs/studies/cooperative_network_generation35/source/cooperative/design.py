#!/usr/bin/env python3
"""Bounded baseline characterization and irreversible scientific protocol freeze."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cooperative import evaluate as ev

PANEL = [("none", 0.0, 0.0), ("moderate", 0.4, 0.4), ("strong", 1.2, 1.2)]
CONSTANTS = [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75]
BASELINE_DIR = ev.ROOT / "results/adaptive_exploration_v1/baselines"


def baseline_bodies():
    result = {f"constant_{p:g}": ("constant", p, f"        return {p};") for p in CONSTANTS}
    for high in [0.25, 0.5]:
        result[f"loss_response_{high:g}"] = (
            "loss_response", high,
            f"""        // Increase exploration after a local utility loss, otherwise stay cautious.
        if (observation.utilityChange() < -0.1 || observation.utility() < 0.0) {{
            return {high};
        }}
        return 0.05;""",
        )
        result[f"stagnation_{high:g}"] = (
            "stagnation", high,
            f"""        // Four non-improving own-action observations trigger exploration.
        if (!observation.incomingOffer()) {{
            double count = observation.utilityChange() <= 0.01 ? memory.get(0) + 1.0 : 0.0;
            memory.set(0, Math.min(4.0, count));
        }}
        return memory.get(0) >= 4.0 ? {high} : 0.05;""",
        )
    return result


def initialize(histories=4, workers=2):
    if (ev.EXPERIMENT / "freeze.json").exists():
        ev.verify_freeze()
        print("Existing frozen protocol verified; initialization is a no-op.")
        return
    config_path = ev.EXPERIMENT / "config.json"
    config = {
        "campaign_id": "adaptive_exploration_v1", "protocol_version": 1,
        "status": "prespecified_before_baseline_characterization",
        "n": 40, "layers": 2, "pre_rounds": 50, "recovery_rounds": 50,
        "shocked": 26, "search_size": 10,
        "inherited_p": 0.25, "others_p": 0.25,
        "incentive_panel": [{"name": name, "triangle": d, "spillover": e} for name, d, e in PANEL],
        "cost_transitions": [[0.2, 0.6], [0.6, 0.2]],
        "focal_modes": ["direct", "indirect"],
        "independent_histories_per_regime_direction": histories,
        "constant_grid": CONSTANTS,
        "simple_adaptive_tuning": {"loss_response_high": [0.25, 0.5], "stagnation_high": [0.25, 0.5]},
        "scale": "max(1,mean(abs(per-case focal mean utility))) under focal constant p=.25 within incentive x cost direction",
        "score": "mean((candidate cumulative focal utility - selected constant cumulative focal utility)/(50*regime_scale))",
        "weights": "equal incentive regimes, cost directions, focal statuses, histories",
        "uncertainty": "descriptive SE of paired scaled differences averaged within each inherited-history cluster; no confirmatory inference",
        "selection": "strongest fixed p across all development cases by equally weighted scaled mean utility; ascending-p tie-break",
        "case_timeout_seconds": 90,
        "parallel_jvms": workers,
        "fresh_confirmation": "not constructed or accessible to discovery; separate post-selection stage required",
        "baseline_panel_choice": "fixed a priori coverage: absent, moderate, strong triangle/spillover complements within paper range; no outcome-driven regime selection",
    }
    if config_path.exists() and json.loads(config_path.read_text()) != config:
        raise RuntimeError("Existing configuration differs; refusing silent replacement")
    ev.atomic_json(config_path, config)
    observation_methods = ["utility", "costLayer0", "costLayer1", "degreeLayer0", "degreeLayer1", "trianglesLayer0", "trianglesLayer1", "overlap", "utilityChange", "degreeChange", "incomingOffer", "offerUtilityDelta", "lastProposalOutcome", "lastActionExplored"]
    ev.atomic_json(ev.EXPERIMENT / "policy_contract.json", {
        "observation_methods": observation_methods,
        "memory_slots": 4, "memory_min": -1e6, "memory_max": 1e6,
        "probability_min": 0.0, "probability_max": 0.75,
        "invocation": "before own scheduled action; before non-improving incoming-offer consent; beneficial offers always accepted without invocation",
        "deltas": "relative to previous policy invocation for the deciding actor",
        "initial_memory": "four zero registers at recovery start; actor-local thereafter",
        "body_only": True, "source_limit_bytes": 8192,
        "forbidden": ["I/O", "reflection", "processes", "threads", "clock", "randomness", "allocation", "loops", "mutable fields", "helper methods", "simulator reference", "counterpart private parameters", "future shock information"],
    })
    for panel_index, (panel_name, triangle, spillover) in enumerate(PANEL):
        for direction_index, (direction, before, after) in enumerate([("increase", 0.2, 0.6), ("decrease", 0.6, 0.2)]):
            regime_id = f"{panel_name}_{direction}"
            for replicate in range(histories):
                history_id = f"{regime_id}_h{replicate:02d}"
                # Separate namespaces ensure recipients never consume policy-dependent draws.
                serial = (panel_index * 2 + direction_index) * histories + replicate
                for mode in ["direct", "indirect"]:
                    case_id = f"{history_id}_{mode}"
                    case = {"id": case_id, "regime_id": regime_id, "history_id": history_id,
                            "history_seed": 1701001 + serial * 104729,
                            "action_seed": 2902003 + serial * 130363,
                            "shock_seed": 4303009 + serial * 155921,
                            "triangle": triangle, "spillover": spillover,
                            "cost_before": before, "cost_after": after,
                            "focal_mode": mode,
                            "snapshot": f"experiments/adaptive_exploration_v1/histories/{history_id}.json",
                            **{k: config[k] for k in ["inherited_p", "others_p", "pre_rounds", "recovery_rounds", "n", "shocked", "search_size"]}}
                    ev.atomic_json(ev.EXPERIMENT / "cases" / (case_id + ".json"), case)
    for name, (family, parameter, body) in baseline_bodies().items():
        path = ev.ROOT / "policies/baselines" / name / "CandidatePolicy.java"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(ev.policy_source(body))
    print(json.dumps({"cases": len(list((ev.EXPERIMENT / "cases").glob("*.json"))), "histories": histories * 6, "baselines": len(baseline_bodies())}))


def prepare_histories():
    seen = set()
    for path in sorted((ev.EXPERIMENT / "cases").glob("*.json")):
        case = json.loads(path.read_text())
        if case["history_id"] in seen:
            continue
        seen.add(case["history_id"])
        output = ev.ROOT / case["snapshot"]
        if output.exists():
            continue
        output.parent.mkdir(parents=True, exist_ok=True)
        began = time.monotonic()
        proc = subprocess.run([ev.java_binary("java"), "-Xmx384m", "-cp", ev.classpath(), "agents.CaseRunner", "--prepare-history", "--case", str(path), "--output", str(output)], capture_output=True, text=True, timeout=ev.load_config()["case_timeout_seconds"], cwd=ev.ROOT)
        if proc.returncode:
            raise RuntimeError(f"History failed {case['history_id']}: {proc.stderr[-3000:]}")
        ev.append_ledger({"kind": "inherited_history", "history_id": case["history_id"], "seconds": time.monotonic() - began, "completed": True, "unix_time": time.time()})
        print(json.dumps({"history": case["history_id"], "seconds": round(time.monotonic() - began, 3)}), flush=True)


def characterize():
    if (ev.EXPERIMENT / "freeze.json").exists():
        ev.verify_freeze()
        print("Already frozen; preserving baseline characterization.")
        return
    prepare_histories()
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    raws = {}
    for name in baseline_bodies():
        source = (ev.ROOT / "policies/baselines" / name / "CandidatePolicy.java").read_text()
        began = time.monotonic()
        raw = ev.evaluate_raw(source)
        raws[name] = raw
        ev.atomic_json(BASELINE_DIR / name / "case_results.json", raw)
        print(json.dumps({"baseline": name, "cases": raw["case_count"], "physical": raw["physical_cases"], "seconds": round(time.monotonic() - began, 3)}), flush=True)
    by_regime = {}
    for item in raws["constant_0.25"]["cases"]:
        by_regime.setdefault(item["case"]["regime_id"], []).append(abs(item["outcome"]["focal_mean_utility"]))
    scales = {key: max(1.0, statistics.mean(values)) for key, values in sorted(by_regime.items())}
    ev.atomic_json(ev.EXPERIMENT / "scales.json", scales)
    scores = {}
    for name, raw in raws.items():
        scores[name] = statistics.mean(item["outcome"]["focal_mean_utility"] / scales[item["case"]["regime_id"]] for item in raw["cases"])
    selected = max([name for name in raws if name.startswith("constant_")], key=lambda name: (scores[name], -float(name.removeprefix("constant_"))))
    selected_p = float(selected.removeprefix("constant_"))
    reference = {"selected_baseline": selected, "selected_probability": selected_p,
                 "selection_scaled_mean_utility": scores[selected],
                 "cases": {item["case_id"]: item["outcome"] for item in raws[selected]["cases"]}}
    ev.atomic_json(ev.EXPERIMENT / "reference.json", reference)
    seed_source = (ev.ROOT / "policies/baselines" / selected / "CandidatePolicy.java").read_text()
    (ev.ROOT / "policies/CandidatePolicy.java").write_text(seed_source)
    summary = {"selected_constant": selected, "selected_probability": selected_p, "scales": scales, "baselines": {}}
    for name, raw in raws.items():
        metrics = ev.summarize(raw)
        ev.atomic_json(BASELINE_DIR / name / "metrics.json", metrics)
        ev.atomic_json(BASELINE_DIR / name / "correct.json", {"correct": True, "error": None})
        summary["baselines"][name] = {**metrics, "selection_scaled_mean_utility": scores[name]}
    ev.atomic_json(BASELINE_DIR / "summary.json", summary)
    print(json.dumps({"selected_constant": selected, "selected_probability": selected_p, "scales": scales}, indent=2))


def freeze():
    path = ev.EXPERIMENT / "freeze.json"
    if path.exists():
        ev.verify_freeze()
        print("Existing freeze verified.")
        return
    if not (BASELINE_DIR / "summary.json").exists():
        raise RuntimeError("Run bounded baseline characterization before freezing")
    seed = ev.ROOT / "policies/CandidatePolicy.java"
    ev.validate_source(seed.read_text())
    frozen = {**ev.config_identity(),
              "campaign_id": "adaptive_exploration_v1",
              "frozen_at_unix": time.time(),
              "seed_sha256": ev.sha256(seed.read_bytes()),
              "reference_sha256": ev.sha256((ev.EXPERIMENT / "reference.json").read_bytes()),
              "scales_sha256": ev.sha256((ev.EXPERIMENT / "scales.json").read_bytes()),
              "snapshots": {str(p.relative_to(ev.ROOT)): ev.sha256(p.read_bytes()) for p in sorted((ev.EXPERIMENT / "histories").glob("*.json"))}}
    ev.atomic_json(path, frozen)
    ev.verify_freeze()
    print(json.dumps(frozen, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["initialize", "histories", "characterize", "freeze"])
    parser.add_argument("--histories", type=int, default=4)
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    if args.command == "initialize":
        initialize(args.histories, args.workers)
    elif args.command == "histories":
        prepare_histories()
    elif args.command == "characterize":
        characterize()
    else:
        freeze()


if __name__ == "__main__":
    main()
