"""Separate complete-paper verification from explicitly amended discovery readiness.

The immutable execution amendment permits the complete N40 development panel
before the deferred paper matrix. Pre-seed readiness fixes its science; final
admission additionally requires an actually completed, identity-matched seed.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from paper_trajectory_v2.design import CAMPAIGN, EXPERIMENT, MANIFEST, RESULTS, ROOT, GRID, NOISE, canonical, sha, reference_cases, case, conditions
from paper_trajectory_v2.runtime import engine_digest, engine_identity

EXPECTED_REFERENCE_CASES = 34560
REQUIRED_PANELS = frozenset({"Figure2", "Figure3", "Figure4", "Figure5", "Figure6", "Figure7",
                             "TableS1", "S1", "S2", "S3", "S4"})


def _fail(message):
    raise RuntimeError("Scientific admission/reference gate: " + message)


def _read(path):
    path = Path(path)
    if not path.is_file():
        _fail("required evidence is missing: " + str(path))
    try:
        return json.loads(path.read_text())
    except (ValueError, OSError) as exc:
        _fail("invalid JSON evidence: " + str(path) + ": " + str(exc))


def _path(relative):
    path = Path(relative)
    if path.is_absolute() or not (ROOT / path).resolve().is_relative_to(ROOT.resolve()):
        _fail("evidence path must stay within this checkout: " + str(relative))
    return ROOT / path


def _verified_file(relative, expected):
    path = _path(relative)
    if not path.is_file():
        _fail("frozen evidence changed or is missing: " + str(relative))
    from scripts.paper_operational_compatibility import resolved_digest
    resolved_digest(relative, expected, lambda name: (ROOT / name).read_bytes())
    return path


def _verify_panel(panel, known_case_ids, files):
    name = panel["id"]
    if panel.get("execution_status") != "complete" or panel.get("complete") is not True:
        _fail(name + " has not completed its declared execution and comparison")
    expected, executed = panel.get("expected_case_ids"), panel.get("executed_case_ids")
    if (not isinstance(expected, list) or not isinstance(executed, list)
            or len(set(expected)) != len(expected) or len(set(executed)) != len(executed)
            or set(expected) != set(executed) or not set(expected) <= known_case_ids):
        _fail(name + " has incomplete, duplicate or foreign case coverage")
    if name != "Figure4" and not expected:
        _fail(name + " has no declared numerical cases")
    comparison = panel.get("comparison", {})
    if comparison.get("status") not in {"executed_agreement", "executed_discrepant"}:
        _fail(name + " lacks an executed comparison with the publication")
    if comparison.get("consequential") is True or panel.get("consequential_ambiguities"):
        _fail(name + " retains a consequential unresolved discrepancy or ambiguity")
    if comparison["status"] == "executed_discrepant" and (
            comparison.get("consequential") is not False or not comparison.get("justification")):
        _fail(name + " discrepancy has not been explicitly resolved or bounded")
    if not panel.get("source") or not panel.get("code") or not panel.get("configuration"):
        _fail(name + " lacks source-to-code-to-configuration provenance")
    for relative in panel["source"] + panel["code"]:
        if relative not in files:
            _fail(name + " references unfrozen source/code evidence: " + str(relative))
    if name == "Figure4":
        fixture = panel["configuration"].get("engine_fixture")
        if not isinstance(fixture, dict) or fixture.get("path") not in files:
            _fail("Figure4 requires the executed engine fixture, not an algebra-only calculation")
        if fixture.get("sha256") != files[fixture["path"]]:
            _fail("Figure4 fixture identity differs from the frozen executed evidence")


def require_complete_reference_milestone():
    """Return the frozen milestone only when all mandatory evidence agrees.

    The controller invokes this before provider setup or admitting discovery;
    evaluator contract verification invokes it again. A session boundary never
    reduces the declaration or changes an incomplete report into a valid gate.
    """
    manifest = _read(MANIFEST)
    design_path, cases_path = EXPERIMENT / "design.json", EXPERIMENT / "reference_cases.json"
    for key, path in (("design_sha256", design_path), ("reference_cases_sha256", cases_path)):
        if manifest.get(key) != sha(path.read_bytes()):
            _fail("declared scientific configuration changed: " + str(path))
    if manifest.get("campaign_id") != CAMPAIGN or manifest.get("descendant_proposal_ceiling") != 50:
        _fail("campaign identity or descendant ceiling changed")
    declared = _read(cases_path)
    if len(declared) != EXPECTED_REFERENCE_CASES or declared != reference_cases():
        _fail("the complete frozen reference condition structure differs from the declaration")
    declared_by_id = {case["case_id"]: case for case in declared}
    if len(declared_by_id) != len(declared):
        _fail("duplicate declared reference case IDs")
    index_path = RESULTS / "reference-index.json"
    index = _read(index_path)
    records = index.get("cases", [])
    if (index.get("planned") != EXPECTED_REFERENCE_CASES
            or index.get("completed") != EXPECTED_REFERENCE_CASES
            or len(records) != EXPECTED_REFERENCE_CASES):
        _fail(f"reference execution is incomplete ({index.get('completed', 0)}/{EXPECTED_REFERENCE_CASES}); no mutation may be submitted")
    current_engine = engine_digest()
    reference_program = "reference:" + sha((ROOT / "java-paper/paper/ReferencePolicy.java").read_bytes())
    if index.get("campaign_id") != CAMPAIGN or index.get("engine_sha256") != current_engine:
        _fail("reference index belongs to another campaign or engine")
    seen = set()
    for receipt in records:
        case_id = receipt.get("case_id")
        identity = receipt.get("identity", {})
        if case_id in seen or case_id not in declared_by_id:
            _fail("duplicate or foreign completed reference case: " + str(case_id))
        expected = {"schema": "paper-trajectory-case-v1", "engine_sha256": current_engine,
                    "program_sha256": reference_program, "case": declared_by_id[case_id]}
        if identity != expected or receipt.get("cache_key") != sha(canonical(expected)):
            _fail("completed reference engine/program/configuration identity differs: " + case_id)
        key = receipt["cache_key"]
        cached = _read(RESULTS / "cache" / key[:2] / (key + ".json"))
        if cached != receipt:
            _fail("reference index differs from its exact-case cache receipt: " + case_id)
        _verified_file(receipt["trajectory_path"], receipt["trajectory_sha256"])
        for metric in ("terminal_mean_utility", "pre_shock_mean_utility"):
            if not isinstance(receipt.get(metric), (int, float)) or not math.isfinite(receipt[metric]):
                _fail("missing/nonfinite completed reference metric: " + case_id)
        seen.add(case_id)
    if seen != set(declared_by_id):
        _fail("completed reference IDs do not match the full declared matrix")

    milestone = _read(EXPERIMENT / "reference_milestone.json")
    identity = dict(milestone)
    identity.pop("identity_sha256", None)
    if milestone.get("identity_sha256") != sha(canonical(identity)):
        _fail("reference milestone identity does not match its frozen contents")
    required_identities = {"campaign_id": CAMPAIGN, "engine_sha256": current_engine,
        "program_sha256": reference_program, "design_sha256": sha(design_path.read_bytes()),
        "reference_cases_sha256": sha(cases_path.read_bytes()), "reference_index_sha256": sha(index_path.read_bytes())}
    if any(milestone.get(key) != value for key, value in required_identities.items()):
        _fail("reference milestone identifies different science, baseline, engine or execution")
    files = milestone.get("files", {})
    if not files:
        _fail("reference milestone has no frozen source/behavior/report/baseline files")
    for relative, expected_hash in files.items():
        _verified_file(relative, expected_hash)
    for path in (design_path, cases_path, index_path):
        if str(path.relative_to(ROOT)) not in files:
            _fail("reference milestone omitted a mandatory frozen configuration or index")
    for relative, expected_hash in engine_identity().items():
        if files.get(relative) != expected_hash:
            _fail("reference milestone omitted or changed engine source: " + relative)
    for relative in ("paper_trajectory_v2/design.py", "paper_trajectory_v2/runtime.py", "paper_trajectory_v2/analysis.py"):
        if files.get(relative) != sha((ROOT / relative).read_bytes()):
            _fail("reference milestone omitted or changed scientific orchestration: " + relative)
    required_paths = [milestone.get(key) for key in ("report_path", "behavior_contract_path", "source_provenance_path")]
    baseline_paths = milestone.get("baseline_paths")
    if (any(not path or path not in files for path in required_paths)
            or not isinstance(baseline_paths, list) or not baseline_paths
            or any(path not in files for path in baseline_paths)):
        _fail("report, behavior contract, primary sources or baseline identities are not frozen")
    provenance = _read(_path(milestone["source_provenance_path"]))
    if not provenance.get("files"):
        _fail("primary-source provenance contains no retained artifacts")
    for source in provenance["files"]:
        if files.get(source["path"]) != source["sha256"]:
            _fail("retained source artifact missing from the scientific freeze: " + source["path"])

    report = _read(_path(milestone["report_path"]))
    expected_report = {"campaign_id": CAMPAIGN, "index_sha256": required_identities["reference_index_sha256"],
        "engine_sha256": current_engine, "program_sha256": reference_program,
        "declared_cases": EXPECTED_REFERENCE_CASES, "verified_completed_cases": EXPECTED_REFERENCE_CASES,
        "complete": True}
    if any(report.get(key) != value for key, value in expected_report.items()):
        _fail("reference comparison report is incomplete or belongs to different evidence")
    if report.get("blocking_ambiguities"):
        _fail("reference report retains consequential unresolved source/model discrepancies")
    panels = report.get("panels", [])
    if len(panels) != len(REQUIRED_PANELS) or {p.get("id") for p in panels} != REQUIRED_PANELS:
        _fail("reference report does not cover every required main/supplement computational panel")
    for panel in panels:
        _verify_panel(panel, seen, files)
    baseline = report.get("baseline_identity", {})
    if (baseline.get("index_sha256") != required_identities["reference_index_sha256"]
            or not baseline.get("files") or set(baseline["files"]) != set(baseline_paths)
            or any(files.get(path) != value for path, value in baseline["files"].items())):
        _fail("reference report's normalization/baseline identity is not frozen consistently")
    return milestone


AMENDMENT_PATH = "experiments/paper_trajectory_v2/discovery_execution_amendment.json"
AMENDMENT_SHA256 = "946d1c733cb0bf2e729b786d068bd2e9db77508417cfca2129475e33a8203ecd"
AMENDMENT_IDENTITY = "e9855e6d5bfd4d181550fb27304df1ce2cbc79c99ae9e9a25a7530345f4217ce"
PRIMARY_PATH = "experiments/paper_trajectory_v2/primary_reference_decision.json"
PRIMARY_SHA256 = "6070d9f9e7ee98bc1c6791279626921ab21d1cae860f37d6c92764866adb47e3"
READINESS_SCHEMA = "paper-discovery-readiness-v1"


def _identity(value, schema):
    body = dict(value)
    body.pop("identity_sha256", None)
    if value.get("schema") != schema or value.get("identity_sha256") != sha(canonical(body)):
        _fail("invalid " + schema + " identity")
    return value["identity_sha256"]


def _required_frozen(files, relative):
    if relative not in files:
        _fail("discovery readiness omitted frozen evidence: " + relative)
    return _verified_file(relative, files[relative])


def _discovery_basis():
    """Verify the non-cyclic basis; never call the evaluator from this stage."""
    manifest = _read(MANIFEST)
    if manifest.get("campaign_id") != CAMPAIGN or manifest.get("descendant_proposal_ceiling") != 50:
        _fail("campaign identity or descendant ceiling changed")
    for key, filename in (("design_sha256", "design.json"), ("reference_cases_sha256", "reference_cases.json")):
        if manifest.get(key) != sha((EXPERIMENT / filename).read_bytes()):
            _fail("original reference declaration changed rather than being preserved")
    amendment = _read(_verified_file(AMENDMENT_PATH, AMENDMENT_SHA256))
    if _identity(amendment, "paper-discovery-execution-amendment-v1") != AMENDMENT_IDENTITY:
        _fail("execution amendment identity changed")
    authority = {"path": AMENDMENT_PATH, "sha256": AMENDMENT_SHA256, "identity_sha256": AMENDMENT_IDENTITY}
    if manifest.get("scientific_contract_decisions", {}).get("discovery_execution") != authority:
        _fail("execution amendment is not registered in the campaign")

    readiness = _read(EXPERIMENT / "discovery_readiness.json")
    _identity(readiness, READINESS_SCHEMA)
    if readiness.get("campaign_id") != CAMPAIGN or readiness.get("amendment") != {"path": AMENDMENT_PATH, "sha256": AMENDMENT_SHA256}:
        _fail("discovery readiness does not bind the explicit user amendment")
    if readiness.get("primary_reference") != {"path": PRIMARY_PATH, "sha256": PRIMARY_SHA256}:
        _fail("discovery readiness must retain the original primary-reference authority")
    files = readiness.get("files", {})
    if not files:
        _fail("discovery readiness has no frozen evidence")
    for relative, digest in files.items():
        _verified_file(relative, digest)
    current_engine = engine_digest()
    program = "reference:" + sha((ROOT / "java-paper/paper/ReferencePolicy.java").read_bytes())
    if readiness.get("engine_sha256") != current_engine or readiness.get("reference_program_sha256") != program:
        _fail("discovery engine/reference program changed")
    for relative, digest in engine_identity().items():
        if files.get(relative) != digest:
            _fail("discovery readiness omitted/changed engine source: " + relative)
    for relative in [AMENDMENT_PATH, PRIMARY_PATH] + ["paper_trajectory_v2/" + name + ".py" for name in
            ("evaluate", "runtime", "design", "gate", "policy_guard", "native", "recovery")] + ["scripts/paper_recover_evaluation.py"]:
        _required_frozen(files, relative)
    primary = _read(_required_frozen(files, PRIMARY_PATH))
    if files[PRIMARY_PATH] != PRIMARY_SHA256 or primary.get("engine_sha256") != current_engine or primary.get("primary") != "source_executable":
        _fail("primary source behavior changed")
    for relative, digest in primary["equivalence_evidence"].items():
        if files.get(relative) != digest:
            _fail("source/interface equivalence evidence is missing or changed: " + relative)
    checks = _read(_required_frozen(files, "docs/paper_trajectory_v2/engine_checks.json"))
    if checks.get("pass") is not True or checks.get("engine_sha256") != current_engine:
        _fail("primary engine/interface proof is not passed for this engine")

    paths = [readiness[key] for key in ("comparator_pool_path", "comparator_selection_path", "development_cases_path", "development_baseline_path", "seed_path")]
    for relative in paths:
        _required_frozen(files, relative)
    pool = _read(_path(readiness["comparator_pool_path"]))
    expected = {c["case_id"]: c for d in GRID for e in GRID for p in NOISE for before, after, count in conditions(40)
                for c in [case(40, d, e, p, before, after, count, 0, "source_executable", "random")]}
    records = {}
    for receipt in pool:
        cid = receipt.get("case_id")
        if cid in records or cid not in expected:
            _fail("comparator pool has duplicate or foreign case identity")
        identity = {"schema": "paper-trajectory-case-v1", "engine_sha256": current_engine,
                    "program_sha256": program, "case": expected[cid]}
        key = sha(canonical(identity))
        if receipt.get("identity") != identity or receipt.get("cache_key") != key:
            _fail("comparator pool engine/program/case identity changed")
        relative = str((RESULTS / "cache" / key[:2] / (key + ".json")).relative_to(ROOT))
        if _read(_required_frozen(files, relative)) != receipt:
            _fail("comparator differs from its retained cache receipt")
        trajectory = receipt.get("trajectory_path")
        if files.get(trajectory) != receipt.get("trajectory_sha256"):
            _fail("comparator trajectory identity is not frozen")
        _required_frozen(files, trajectory)
        if type(receipt.get("terminal_mean_utility")) not in (int, float) or not math.isfinite(receipt["terminal_mean_utility"]):
            _fail("nonfinite comparator terminal utility")
        records[cid] = receipt
    if set(records) != set(expected) or len(records) != 1152:
        _fail("global comparator choice requires all 1152 fixed-noise reference cases")
    means = {p: math.fsum(r["terminal_mean_utility"] for r in records.values() if r["identity"]["case"]["p"] == p) / 288 for p in NOISE}
    selected = min(NOISE, key=lambda p: (-means[p], p))
    selection = _read(_path(readiness["comparator_selection_path"]))
    if selection.get("selected_p") != selected or type(selection.get("utility_scale")) not in (int, float) or not math.isfinite(selection["utility_scale"]) or selection["utility_scale"] <= 0:
        _fail("comparator must be the globally best constant noise with one positive global scale")
    if selection.get("pool_sha256") != files[readiness["comparator_pool_path"]]:
        _fail("comparator selection references another complete fixed-noise pool")
    for p, mean in means.items():
        row = selection.get("by_p", {}).get(str(p), {})
        if row.get("count") != 288 or not math.isclose(row.get("mean_terminal_population_utility", math.nan), mean, rel_tol=1e-12, abs_tol=1e-12):
            _fail("global comparator summary differs from its complete numerical pool")
    scale = max(1., math.sqrt(math.fsum(r["terminal_mean_utility"] ** 2 for r in records.values() if r["identity"]["case"]["p"] == selected) / 288))
    if not math.isclose(selection["utility_scale"], scale, rel_tol=1e-12, abs_tol=1e-12):
        _fail("utility scale is not the single RMS of the selected comparator panel")
    panel = _read(_path(readiness["development_cases_path"]))
    chosen = {cid: c for cid, c in expected.items() if c["p"] == selected}
    if len(panel) != 288 or {c["case_id"]: c for c in panel} != chosen:
        _fail("development panel must contain all 288 external conditions at the one selected noise")
    baseline = _read(_path(readiness["development_baseline_path"]))
    if baseline != {cid: records[cid] for cid in chosen}:
        _fail("development baseline differs from the globally selected comparator")
    return readiness, panel, baseline, selection


def _seed_evidence(readiness, contract, output):
    """Validate actual completed seed outputs and each candidate cache identity."""
    files = {}
    def retain(path):
        path = Path(path).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
            _fail("seed admission evidence is missing or outside this checkout")
        relative = str(path.relative_to(ROOT.resolve()))
        files[relative] = sha(path.read_bytes())
        return _read(path)
    output = Path(output)
    correct = retain(output / "correct.json")
    metrics = retain(output / "metrics.json")
    effects = retain(output / "case_results.json")
    seed_sha = readiness["files"][readiness["seed_path"]]
    if (correct.get("correct") is not True or metrics.get("combined_score") != 0
            or metrics.get("private", {}).get("candidate_sha256") != seed_sha
            or metrics.get("private", {}).get("scientific_identity") != contract["identity_sha256"]
            or metrics.get("public", {}).get("development_trajectories") != 288
            or metrics.get("public", {}).get("external_conditions") != 288):
        _fail("seed must be valid, complete, identity-matched and equal to its fixed comparator")
    panel = _read(_path(readiness["development_cases_path"]))
    by_id = {c["case_id"]: c for c in panel}
    baseline = _read(_path(readiness["development_baseline_path"]))
    if len(effects) != 288 or {e["case_id"] for e in effects} != set(by_id):
        _fail("seed did not finish the complete 288-case panel")
    keys = []
    for effect in effects:
        if effect.get("raw_terminal_population_utility_difference") != 0 or effect.get("scaled_difference") != 0:
            _fail("seed differs from unchanged reference behavior")
        identity = {"schema": "paper-trajectory-case-v1", "engine_sha256": contract["engine_sha256"],
                    "program_sha256": seed_sha, "case": by_id[effect["case_id"]]}
        key = sha(canonical(identity))
        receipt = retain(RESULTS / "cache" / key[:2] / (key + ".json"))
        if receipt.get("identity") != identity or receipt.get("cache_key") != key or effect.get("cache_key") != key:
            _fail("seed numerical cache identity differs from its panel/source")
        trajectory = _verified_file(receipt["trajectory_path"], receipt["trajectory_sha256"])
        files[str(trajectory.relative_to(ROOT))] = receipt["trajectory_sha256"]
        if receipt.get("terminal_mean_utility") != effect.get("candidate_terminal_population_utility"):
            _fail("seed metrics differ from retained numerical receipt")
        if receipt["terminal_mean_utility"] != baseline[effect["case_id"]]["terminal_mean_utility"]:
            _fail("seed numerical result differs from its unchanged reference comparator")
        keys.append(key)
    if metrics["private"].get("case_cache_keys") != keys:
        _fail("seed cache-key sequence differs from its completed effects")
    return {"schema": "paper-discovery-seed-admission-v1", "campaign_id": CAMPAIGN,
            "readiness_identity": readiness["identity_sha256"], "scientific_identity": contract["identity_sha256"],
            "candidate_sha256": seed_sha, "output_path": str(output.resolve().relative_to(ROOT.resolve())),
            "correct": True, "score": 0, "completed_cases": 288, "case_cache_keys": keys, "files": files}


def require_discovery_readiness(*, require_seed=False):
    """Pre-seed science check, or final model admission with completed seed evidence."""
    readiness, _, _, selection = _discovery_basis()
    if require_seed:
        from paper_trajectory_v2.evaluate import verify_contract
        contract = verify_contract()
        if (contract["utility_scale"] != selection["utility_scale"]
                or any(contract[key] != readiness[key] for key in ("development_cases_path", "development_baseline_path", "seed_path"))):
            _fail("evaluator contract differs from amended readiness")
        admission = _read(EXPERIMENT / "seed_admission.json")
        _identity(admission, "paper-discovery-seed-admission-v1")
        expected = _seed_evidence(readiness, contract, _path(admission["output_path"]))
        body = dict(admission)
        body.pop("identity_sha256")
        if body != expected:
            _fail("completed seed admission changed or belongs to different science")
    return readiness


def require_reference_milestone():
    """Compatibility entry for evaluator pre-seed validation, under the amendment."""
    return require_discovery_readiness(require_seed=False)


def write_seed_admission(output):
    """Record only already-completed seed evidence; never run an evaluation."""
    from cooperative.native import atomic_json
    from paper_trajectory_v2.evaluate import verify_contract
    readiness = require_discovery_readiness()
    contract = verify_contract()
    value = _seed_evidence(readiness, contract, output)
    value["identity_sha256"] = sha(canonical(value))
    path = EXPERIMENT / "seed_admission.json"
    if path.exists() and _read(path) != value:
        _fail("refusing to replace different seed-admission evidence")
    if not path.exists():
        atomic_json(path, value)
    require_discovery_readiness(require_seed=True)
    return value
