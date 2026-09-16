#!/usr/bin/env python3
"""Audit prospective v2 seeds against saved research evidence before outcomes.

The inventory intentionally reserves numeric seed values across both roles:
an old optimizer seed cannot become a new environment seed, or vice versa.
This utility never executes the optimizer or rewrites a historical artifact.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from adaptive_swarms.logging import atomic_json

SEED_KEYS = ("environment_seed", "optimizer_seed")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seed_values(value) -> dict[str, set[int]]:
    """Collect explicitly named environment and optimizer seeds recursively."""
    found = {key: set() for key in SEED_KEYS}

    def visit(item):
        if isinstance(item, dict):
            for key, child in item.items():
                if key in found:
                    if type(child) is not int:
                        raise ValueError(f"Noninteger {key} in seed evidence: {child!r}")
                    found[key].add(child)
                else:
                    visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    visit(value)
    return found


def collect_seed_inventory(roots, exclude_paths=()) -> dict:
    """Read JSON/GZ evidence and return role sets, their union, and source hashes.

    Roots may be files or directories. Exclusions also cover descendants, making
    the function usable before final seed generation without treating its own
    output as fresh independent evidence. Invalid saved JSON is surfaced rather
    than silently weakening the exclusion set.
    """
    excluded = [Path(path).resolve() for path in exclude_paths]
    candidates = set()
    for root in roots:
        root = Path(root).resolve()
        paths = [root] if root.is_file() else root.rglob("*")
        for path in paths:
            if not path.is_file() or not (path.name.endswith(".json") or path.name.endswith(".json.gz")):
                continue
            if any(path == parent or parent in path.parents for parent in excluded):
                continue
            candidates.add(path)
    seeds = {key: set() for key in SEED_KEYS}
    sources = []
    for path in sorted(candidates):
        opener = gzip.open if path.suffix == ".gz" else open
        try:
            with opener(path, "rt", encoding="utf-8") as stream:
                found = seed_values(json.load(stream))
        except (ValueError, OSError) as exc:
            raise ValueError(f"Cannot inventory seed evidence {path}: {exc}") from exc
        if not any(found.values()):
            continue
        for key in SEED_KEYS:
            seeds[key].update(found[key])
        try:
            label = str(path.relative_to(ROOT))
        except ValueError:
            label = str(path)
        sources.append({"path": label, "sha256": file_hash(path),
                        **{key + "s": sorted(found[key]) for key in SEED_KEYS}})
    return {"source_files": sources, "json_files_inspected": len(candidates),
            **{key + "s": sorted(seeds[key]) for key in SEED_KEYS},
            "reserved_seed_values": sorted(set().union(*seeds.values()))}


def prospective_cases(path: Path):
    suite = json.loads(path.read_text())
    if isinstance(suite, list):
        return suite
    defaults = suite.get("base", suite.get("defaults"))
    if defaults is None:
        defaults = {key: value for key, value in suite.items()
                    if key not in {"cases", "study", "description"}}
    return [{**defaults, **case} for case in suite["cases"]]


def audit_splits(search: Path, validation: Path, output: Path) -> dict:
    suites = {"search": search.resolve(), "validation": validation.resolve()}
    suite_hashes = {name: file_hash(path) for name, path in suites.items()}
    if output.exists():
        saved = json.loads(output.read_text())
        if saved["suite_hashes"] != suite_hashes:
            raise ValueError("Prospective suites changed after the saved seed audit; retain the audit and use a new output path.")
        return saved
    inventory = collect_seed_inventory(
        [ROOT / "configs", ROOT / "artifacts", ROOT / "results"],
        exclude_paths=[*suites.values(), output],
    )
    historical = set(inventory["reserved_seed_values"])
    seen = {}
    collisions = []
    stages = {}
    for stage, path in suites.items():
        cases = prospective_cases(path)
        stages[stage] = {"source": str(path.relative_to(ROOT)), "case_count": len(cases), "cases": []}
        for index, case in enumerate(cases):
            record = {"case_index": index, "case_id": case.get("case_id", case.get("id", f"case_{index:03d}")),
                      "move_severity": case["move_severity"], "period": case["period"]}
            for role in SEED_KEYS:
                seed = case[role]
                if type(seed) is not int:
                    raise ValueError(f"Noninteger proposed seed in {stage}/{index}/{role}")
                location = {"stage": stage, "case_index": index, "role": role}
                if seed in historical:
                    collisions.append({**location, "seed": seed, "with": "historical evidence"})
                if seed in seen:
                    collisions.append({**location, "seed": seed, "with": seen[seed]})
                seen[seed] = location
                record[role] = seed
            stages[stage]["cases"].append(record)
    report = {
        "format": "relocation-allocation-v2-prospective-seed-audit-v1",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if not collisions else "collisions",
        "scope": "All saved JSON and compressed JSON under configs, artifacts and results; numeric seeds excluded across both roles.",
        "suite_hashes": suite_hashes, "stages": stages,
        "historical_inventory": inventory,
        "collisions": collisions, "replacements": [],
        "all_stage_seed_values": sorted(seen),
        "final_generation_rule": "Generate final pairs only after selection and mechanism control are frozen; exclude historical and all stage numeric seeds in both roles.",
    }
    atomic_json(output, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--search", type=Path, default=ROOT / "configs/relocation_allocation_v2/search.json")
    parser.add_argument("--validation", type=Path, default=ROOT / "configs/relocation_allocation_v2/validation.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results/relocation_allocation_v2/operations/seed-audit.json")
    args = parser.parse_args()
    report = audit_splits(args.search, args.validation, args.output.resolve())
    print(f"[{datetime.now(timezone.utc).isoformat()}] Prospective seed audit {report['status']}: "
          f"{sum(stage['case_count'] for stage in report['stages'].values())} cases, "
          f"{len(report['historical_inventory']['reserved_seed_values'])} historical seed values, "
          f"{len(report['collisions'])} collisions, {len(report['replacements'])} replacements; "
          f"saved {args.output}", flush=True)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
