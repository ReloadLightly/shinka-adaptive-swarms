#!/usr/bin/env python3
"""Independent Java evaluator. No model calls; every case uses a separate JVM."""
from __future__ import annotations
import argparse
import concurrent.futures
import contextlib
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/adaptive_exploration_v1"
CACHE = ROOT / "results/adaptive_exploration_v1/cache"
START = "// EVOLVE-BLOCK-START"
END = "// EVOLVE-BLOCK-END"
WRAPPER_PREFIX = '''import research.ExplorationPolicy;
import research.Observation;
import research.Memory;

public final class CandidatePolicy implements ExplorationPolicy {
    @Override
    public double explorationProbability(Observation observation, Memory memory) {
        // EVOLVE-BLOCK-START
'''
WRAPPER_SUFFIX = '''        // EVOLVE-BLOCK-END
    }
}
'''


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest_files(paths) -> str:
    values = [(str(p.relative_to(ROOT)), sha256(p.read_bytes())) for p in sorted(set(paths))]
    return sha256(canonical(values))


def java_binary(name: str) -> str:
    # Pin the locally installed Java 17 runtime; never silently use the host Java 11.
    java_home = os.environ.get("COOP_JAVA_HOME")
    directory = Path(java_home) if java_home else ROOT / ".tools/jdk-17.0.20.1+1"
    binary = directory / "bin" / name
    if not binary.is_file():
        raise RuntimeError(f"Pinned Java 17 tool missing: {binary}; run scripts/setup.sh")
    return str(binary)


def toolchain_identity() -> dict:
    versions = {}
    for command in ["java", "javac"]:
        proc = subprocess.run([java_binary(command), "-version"], capture_output=True, text=True, timeout=10)
        if proc.returncode:
            raise RuntimeError(f"Cannot query {command} version")
        versions[command] = (proc.stdout + proc.stderr).strip()
    if not versions["javac"].startswith("javac 17."):
        raise RuntimeError("Research engine requires the pinned Java 17 toolchain")
    return versions


def verify_build() -> None:
    manifest_path = ROOT / "build/build_manifest.json"
    if not manifest_path.exists():
        raise RuntimeError("Missing build identity; run scripts/build_java.sh")
    manifest = json.loads(manifest_path.read_text())
    expected_inputs = sorted([str(p.relative_to(ROOT)) for p in list((ROOT / "java").rglob("*.java")) + list((ROOT / "upstream/multiplex/Agents").glob("*.java")) + list((ROOT / "vendor").glob("*.jar")) + [ROOT / "scripts/build_java.sh", ROOT / "cooperative/build_identity.py"]])
    if sorted(manifest["inputs"]) != expected_inputs:
        raise RuntimeError("Java build input set changed; run scripts/build_java.sh")
    for relative, expected in manifest["files"].items():
        path = ROOT / relative
        if not path.is_file() or sha256(path.read_bytes()) != expected:
            raise RuntimeError(f"Stale engine build: {relative}; run scripts/build_java.sh")


def engine_digest() -> str:
    paths = list((ROOT / "java").rglob("*.java"))
    paths += list((ROOT / "vendor").glob("*.jar"))
    paths += list((ROOT / "vendor").glob("*.json"))
    paths += list((ROOT / "scripts").glob("build_java*"))
    paths += list((ROOT / "upstream/multiplex/Agents").glob("*.java"))
    if not paths:
        raise RuntimeError("No engine source or dependencies")
    return digest_files(paths)


def evaluator_digest() -> str:
    return digest_files([ROOT / "cooperative/evaluate.py", ROOT / "cooperative/design.py", ROOT / "cooperative/build_identity.py"])


def atomic_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    os.replace(tmp, path)


@contextlib.contextmanager
def locked(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield
        fcntl.flock(handle, fcntl.LOCK_UN)


def append_ledger(value):
    path = ROOT / "results/adaptive_exploration_v1/evaluation_usage.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with locked(path.with_suffix(".lock")):
        with path.open("a") as handle:
            handle.write(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())


def strip_comments(source: str) -> str:
    return re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)


def policy_source(body: str) -> str:
    return WRAPPER_PREFIX + body.rstrip() + "\n" + WRAPPER_SUFFIX


def validate_source(source: str) -> str:
    """A deliberately small expression/branch language embedded in Java.

    This is a scientific admissibility guard, not an OS sandbox. The fixed wrapper,
    closed set of receivers/methods, no allocation/loops/fields, and no arbitrary
    calls exclude simulator, file, process, clock, randomness and reflection access.
    """
    if len(source.encode()) > 8192 or not source.isascii() or "\\" in source:
        raise ValueError("Policy must be ASCII Java of <=8192 bytes without escapes")
    if source.count(START) != 1 or source.count(END) != 1:
        raise ValueError("Exactly one pair of EVOLVE-BLOCK markers is required")
    before, rest = source.split(START)
    body, after = rest.split(END)
    norm = lambda text: re.sub(r"\s+", "", strip_comments(text))
    if norm(before) != norm(WRAPPER_PREFIX.split(START)[0]) or norm(after) != norm(WRAPPER_SUFFIX.split(END)[1]):
        raise ValueError("Only the explorationProbability method body may evolve")
    code = strip_comments(body)
    if re.search(r'["\'\[\]@]', code):
        raise ValueError("No strings, chars, arrays, or annotations in policy body")
    forbidden = r"\b(new|class|interface|enum|record|static|public|private|protected|package|import|while|for|do|switch|try|catch|throw|throws|synchronized|assert|this|super|instanceof|var|Object|Class|System|Runtime|Thread|ProcessBuilder|java|javax|sun|Double|Float)\b"
    if re.search(forbidden, code):
        raise ValueError("Policy contains a forbidden construct")
    if re.search(r"(?:observation|memory|Math)\s*=", code):
        raise ValueError("Policy may not reassign API receivers")
    contract = json.loads((EXPERIMENT / "policy_contract.json").read_text())
    allowed = {
        "observation": set(contract["observation_methods"]),
        "memory": {"get", "set"},
        "Math": {"abs", "min", "max", "sqrt", "log", "log1p", "exp", "tanh", "pow", "signum", "floor", "ceil"},
    }
    # Strip numeric decimal points before checking member accesses.
    member_code = re.sub(r"\b(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", "0", code)
    for receiver, member in re.findall(r"\b([A-Za-z_$][\w$]*)\s*\.\s*([A-Za-z_$][\w$]*)", member_code):
        if receiver not in allowed or member not in allowed[receiver]:
            raise ValueError(f"Unapproved API member {receiver}.{member}")
    stripped_calls = re.sub(r"\b(?:observation|memory|Math)\s*\.\s*\w+\s*\(", "(", code)
    for call in re.findall(r"\b([A-Za-z_$][\w$]*)\s*\(", stripped_calls):
        if call not in {"if", "return"}:
            raise ValueError(f"Unapproved function call {call}")
    # Prevent member chaining, hexadecimal forms and syntax outside arithmetic/branches.
    if re.search(r"[.:]", re.sub(r"(?:\d+\.\d*|\.\d+)|\b(?:observation|memory|Math)\s*\.\s*\w+", "", code).replace(":", "")):
        raise ValueError("Unapproved member expression")
    if not re.search(r"\breturn\b", code):
        raise ValueError("Policy must return a probability")
    return body


def classpath(candidate_dir: Path | None = None) -> str:
    entries = [ROOT / "build/classes"] + sorted((ROOT / "vendor").glob("*.jar"))
    if candidate_dir:
        entries.append(candidate_dir)
    return os.pathsep.join(str(p) for p in entries)


def compile_candidate(source: str, engine_hash: str) -> tuple[Path, bool, float]:
    validate_source(source)
    identity = sha256(canonical({"candidate": sha256(source.encode()), "engine": engine_hash}))
    directory = CACHE / "compiled" / identity
    began = time.monotonic()
    with locked(directory.with_suffix(".lock")):
        if (directory / "CandidatePolicy.class").exists() and (directory / "complete.json").exists():
            return directory, True, time.monotonic() - began
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "CandidatePolicy.java").write_text(source)
        proc = subprocess.run([java_binary("javac"), "--release", "17", "-cp", classpath(), "-d", str(directory), str(directory / "CandidatePolicy.java")], capture_output=True, text=True, timeout=30, cwd=ROOT)
        if proc.returncode:
            raise ValueError("Candidate compilation failed: " + proc.stderr[-3000:])
        atomic_json(directory / "complete.json", {"candidate_sha256": sha256(source.encode()), "engine_sha256": engine_hash})
    return directory, False, time.monotonic() - began


def load_config():
    return json.loads((EXPERIMENT / "config.json").read_text())


def config_identity():
    return {
        "toolchain": toolchain_identity(),
        "engine_sha256": engine_digest(),
        "evaluator_sha256": evaluator_digest(),
        "config_sha256": sha256((EXPERIMENT / "config.json").read_bytes()),
        "cases_sha256": digest_files((EXPERIMENT / "cases").glob("*.json")),
        "contract_sha256": sha256((EXPERIMENT / "policy_contract.json").read_bytes()),
    }


def verify_freeze():
    frozen = json.loads((EXPERIMENT / "freeze.json").read_text())
    actual = config_identity()
    for key, value in actual.items():
        if frozen[key] != value:
            raise RuntimeError(f"Scientific configuration changed: {key}; frozen campaign cannot continue")
    for relative, digest in frozen["snapshots"].items():
        if sha256((ROOT / relative).read_bytes()) != digest:
            raise RuntimeError(f"Frozen inherited history changed: {relative}")
    for key, relative in [("reference_sha256", "reference.json"), ("scales_sha256", "scales.json")]:
        if frozen[key] != sha256((EXPERIMENT / relative).read_bytes()):
            raise RuntimeError(f"Frozen scoring data changed: {relative}")
    return frozen


def validate_outcome(outcome: dict, case: dict) -> None:
    """Independent completion checks; no native exception fallback can validate a seed."""
    rounds, n = case["recovery_rounds"], case["n"]
    if outcome["case_id"] != case["id"] or outcome["history_id"] != case["history_id"]:
        raise ValueError("Outcome case/history identity mismatch")
    if outcome["recovery_rounds"] != rounds or outcome["actor_turns"] != rounds * n or outcome["focal_turns"] != rounds:
        raise ValueError("Incomplete fixed-horizon evaluation")
    values = outcome["actor_cumulative_utilities"]
    if len(values) != n or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in values):
        raise ValueError("Invalid actor cumulative utility vector")
    focal = outcome["focal_index"]
    if not 0 <= focal < n or not math.isclose(values[focal], outcome["focal_cumulative_utility"], rel_tol=1e-12, abs_tol=1e-9):
        raise ValueError("Inconsistent focal cumulative utility")
    if not math.isfinite(outcome["focal_mean_utility"]) or not math.isclose(outcome["focal_mean_utility"] * rounds, values[focal], rel_tol=1e-12, abs_tol=1e-9):
        raise ValueError("Inconsistent focal mean utility")
    recipients = outcome["shock_recipients"]
    if len(set(recipients)) != case["shocked"] or len(recipients) != case["shocked"] or not all(0 <= i < n for i in recipients):
        raise ValueError("Wrong partial-shock recipients")
    if (focal in recipients) != (case["focal_mode"] == "direct"):
        raise ValueError("Wrong focal exposure status")
    if len(outcome["focal_utility_trajectory"]) != rounds:
        raise ValueError("Incomplete focal trajectory")


def run_case(case_path: Path, compiled: Path, candidate_hash: str, identities: dict) -> dict:
    case = json.loads(case_path.read_text())
    snapshot = ROOT / case["snapshot"]
    case_identity = {
        "candidate_sha256": candidate_hash,
        "engine_sha256": identities["engine_sha256"],
        "evaluator_sha256": identities["evaluator_sha256"],
        "case_sha256": sha256(case_path.read_bytes()),
        "snapshot_sha256": sha256(snapshot.read_bytes()),
    }
    key = sha256(canonical(case_identity))
    cache_file = CACHE / "cases" / (key + ".json")
    with locked(cache_file.with_suffix(".lock")):
        if cache_file.exists():
            result = json.loads(cache_file.read_text())
            if result["identity"] != case_identity:
                raise RuntimeError("Case cache identity mismatch")
            return {**result, "cache_hit": True}
        work = CACHE / "work" / (key + "." + uuid.uuid4().hex)
        work.mkdir(parents=True, exist_ok=True)
        output = work / "outcome.json"
        began = time.monotonic()
        cmd = [java_binary("java"), "-Xmx384m", "-cp", classpath(compiled), "agents.CaseRunner", "--case", str(case_path), "--policy", "CandidatePolicy", "--output", str(output)]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=load_config()["case_timeout_seconds"], cwd=ROOT)
            if proc.returncode:
                raise ValueError(f"Case {case['id']} failed: {proc.stderr[-2500:]}")
            outcome = json.loads(output.read_text())
            validate_outcome(outcome, case)
            result = {"identity": case_identity, "case_id": case["id"], "history_id": case["history_id"], "case": case, "outcome": outcome, "seconds": time.monotonic() - began}
            atomic_json(cache_file, result)
            append_ledger({"kind": "numerical_case", "case_id": case["id"], "cache_key": key, "candidate_sha256": candidate_hash, "seconds": result["seconds"], "completed": True, "unix_time": time.time()})
            return {**result, "cache_hit": False}
        except Exception as exc:
            append_ledger({"kind": "numerical_case", "case_id": case["id"], "candidate_sha256": candidate_hash, "seconds": time.monotonic() - began, "completed": False, "error": str(exc)[-1000:], "unix_time": time.time()})
            raise
        finally:
            shutil.rmtree(work, ignore_errors=True)


def evaluate_raw(source: str, cases: list[Path] | None = None) -> dict:
    verify_build()
    identities = config_identity()
    candidate_hash = sha256(source.encode())
    compiled, compilation_cached, compilation_seconds = compile_candidate(source, identities["engine_sha256"])
    cases = sorted(cases if cases is not None else (EXPERIMENT / "cases").glob("*.json"))
    if not cases:
        raise ValueError("Evaluation requires at least one case")
    began = time.monotonic()
    workers = min(load_config()["parallel_jvms"], max(1, len(cases)))
    outcomes = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(run_case, path, compiled, candidate_hash, identities) for path in cases]
        for future in concurrent.futures.as_completed(futures):
            outcomes.append(future.result())
    outcomes.sort(key=lambda r: r["case_id"])
    result = {"candidate_sha256": candidate_hash, "identities": identities, "cases": outcomes,
              "case_count": len(outcomes), "physical_cases": sum(not item["cache_hit"] for item in outcomes),
              "cached_cases": sum(item["cache_hit"] for item in outcomes),
              "compilation_cached": compilation_cached, "compilation_seconds": compilation_seconds,
              "wall_seconds": time.monotonic() - began}
    return result


def summarize(raw: dict) -> dict:
    reference = json.loads((EXPERIMENT / "reference.json").read_text())
    scales = json.loads((EXPERIMENT / "scales.json").read_text())
    paired, raw_diffs, history_values, regime_values, status_values = [], [], {}, {}, {}
    for result in raw["cases"]:
        case, outcome = result["case"], result["outcome"]
        diff = outcome["focal_cumulative_utility"] - reference["cases"][case["id"]]["focal_cumulative_utility"]
        scale = scales[case["regime_id"]] * case["recovery_rounds"]
        paired.append(diff / scale)
        raw_diffs.append(diff)
        history_values.setdefault(case["history_id"], []).append(diff / scale)
        regime_values.setdefault(case["regime_id"], []).append(diff / scale)
        status_values.setdefault(case.get("focal_mode", "unspecified"), []).append(diff / scale)
    score = statistics.mean(paired)
    clustered = [statistics.mean(values) for values in history_values.values()]
    se = statistics.stdev(clustered) / math.sqrt(len(clustered)) if len(clustered) > 1 else 0.0
    regimes = {key: statistics.mean(values) for key, values in sorted(regime_values.items())}
    feedback = (f"Development only: {len(paired)} paired cases/{len(clustered)} inherited histories. "
                f"Scaled mean focal gain vs selected fixed p={reference['selected_probability']:g}: {score:+.6f}; "
                f"raw cumulative gain {statistics.mean(raw_diffs):+.4f}; history-cluster descriptive SE {se:.6f}. "
                "Regime gains " + "; ".join(f"{k}={v:+.4f}" for k, v in regimes.items()) + ". "
                "Optimize state-dependent local exploration under autonomous consent/exit; these reused development cases do not establish generalization or mutual benefit.")
    mean = lambda key: statistics.mean(r["outcome"][key] for r in raw["cases"])
    public = {"focal_mean_utility": mean("focal_mean_utility"), "focal_cumulative_utility": mean("focal_cumulative_utility"),
              "paired_cumulative_gain": statistics.mean(raw_diffs), "scaled_gain_cluster_se": se,
              "development_case_count": len(paired), "independent_history_count": len(clustered),
              "regime_scaled_gains": regimes,
              "status_scaled_gains": {key: statistics.mean(values) for key, values in sorted(status_values.items())}}
    diagnostic_keys = ["others_mean_utility", "initial_partners_mean_utility", "final_mean_degree_layer0", "final_mean_degree_layer1", "final_mean_clustering_layer0", "final_mean_clustering_layer1", "final_mean_overlap"]
    private = {}
    for key in diagnostic_keys:
        available = [r["outcome"][key] for r in raw["cases"] if r["outcome"].get(key) is not None]
        if available:
            private[key] = statistics.mean(available)
            if len(available) != len(raw["cases"]):
                private[key + "_case_count"] = len(available)
    for key in ["others_mean_utility", "initial_partners_mean_utility"]:
        differences = [item["outcome"][key] - reference["cases"][item["case_id"]][key] for item in raw["cases"]
                       if item["outcome"].get(key) is not None and reference["cases"][item["case_id"]].get(key) is not None]
        if differences:
            private[key + "_paired_gain"] = statistics.mean(differences)
    private.update({"physical_cases": raw["physical_cases"], "cached_cases": raw["cached_cases"], "wall_seconds": raw["wall_seconds"], "candidate_sha256": raw["candidate_sha256"]})
    return {"combined_score": score, "public": public, "private": private, "text_feedback": feedback}


def evaluate_candidate(program_path, output_dir, require_frozen=True) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    began = time.monotonic()
    candidate_hash = None
    try:
        if require_frozen:
            verify_freeze()
        source = Path(program_path).read_text()
        candidate_hash = sha256(source.encode())
        raw = evaluate_raw(source)
        metrics = summarize(raw)
        atomic_json(output_dir / "case_results.json", raw)
        atomic_json(output_dir / "metrics.json", metrics)
        atomic_json(output_dir / "correct.json", {"correct": True, "error": None})
        append_ledger({"kind": "candidate_evaluation", "candidate_sha256": candidate_hash, "completed": True, "seconds": time.monotonic() - began, "physical_cases": raw["physical_cases"], "cached_cases": raw["cached_cases"], "unix_time": time.time()})
        return metrics
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        atomic_json(output_dir / "metrics.json", {"combined_score": -1e9, "public": {}, "private": {}, "text_feedback": "Invalid policy or evaluator failure: " + error[-3000:]})
        atomic_json(output_dir / "correct.json", {"correct": False, "error": error[-4000:]})
        append_ledger({"kind": "candidate_evaluation", "candidate_sha256": candidate_hash, "completed": False, "seconds": time.monotonic() - began, "error": error[-1000:], "unix_time": time.time()})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--program_path", required=True)
    parser.add_argument("--results_dir", required=True)
    args = parser.parse_args()
    try:
        metrics = evaluate_candidate(args.program_path, args.results_dir)
        print(json.dumps({"correct": True, "combined_score": metrics["combined_score"]}))
    except Exception as exc:
        print(f"Evaluation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
