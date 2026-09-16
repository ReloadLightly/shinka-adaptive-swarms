#!/usr/bin/env python3
"""Certify a restricted pure constant subset before protected V3 evaluation.

Candidate text is parsed, never imported or executed. Original shortlist bytes
and registration remain preserved. The source-review freeze must happen after
this explicit metadata amendment. Original registrations/snapshots are retained;
an explicitly installed controller amendment can authorize partial-output facts.
"""
from __future__ import annotations

import argparse
import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from adaptive_swarms.artifacts import read_json
from adaptive_swarms.joint_study import assert_cases, verify_registration, verify_shortlists
from adaptive_swarms.joint_alias_amendment import controller_reference, reviewed_output_proof, require_domain

VERSION = "joint-v3-static-constant-certificate-v2"
CERTIFICATE = "constant_alias_certification.json"
ORIGINAL = "shortlists.pre-alias-certification.json"
PROTECTED = ("source_review.json", "validation", "selection.json", "final_cases.json", "final", "analysis.json")


class UnsupportedProof(ValueError):
    pass


def _doc(node):
    return isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and type(node.value.value) is str


def prove_constant(source, swarm_size=5):
    """Interpret only whitelist syntax over known scalar constants, not Python."""
    if type(swarm_size) is not int or swarm_size != 5:
        raise UnsupportedProof("Proof domain requires exactly five particles per swarm.")
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise UnsupportedProof("Source is not a valid Python syntax tree.") from exc
    nodes = [node for node in tree.body if not _doc(node)]
    if len(nodes) != 1 or not isinstance(nodes[0], ast.FunctionDef):
        raise UnsupportedProof("Module must contain only docstrings and one function definition.")
    fn = nodes[0]
    args = fn.args.posonlyargs + fn.args.args
    if fn.name != "choose_relocation" or len(args) != 1 or fn.decorator_list or fn.args.defaults or fn.args.kw_defaults or fn.args.vararg or fn.args.kwarg or fn.args.kwonlyargs or getattr(fn, "type_params", []):
        raise UnsupportedProof("Function signature or initialization is unsupported.")
    if any(annotation is not None and not (isinstance(annotation, ast.Name) and annotation.id in {"dict", "int", "float"}) for annotation in (fn.returns, args[0].annotation)):
        raise UnsupportedProof("Potentially executable annotation is unsupported.")
    observation = args[0].arg
    if observation in {"int", "min", "dict", "float"}:
        raise UnsupportedProof("Observation argument shadows a recognized builtin.")
    local = {}

    def numeric(value):
        try:
            valid = type(value) in (int, float) and math.isfinite(value)
        except OverflowError:
            valid = False
        if not valid:
            raise UnsupportedProof("Only finite integer/float constants are supported.")
        return value

    def expression(node):
        if isinstance(node, ast.Constant):
            return numeric(node.value)
        if isinstance(node, ast.Name) and node.id in local:
            return local[node.id]
        if isinstance(node, ast.Tuple):
            return tuple(expression(item) for item in node.elts)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = numeric(expression(node.operand))
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == observation and isinstance(node.slice, ast.Constant) and node.slice.value == "swarm_size":
            return swarm_size
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
            values = [numeric(expression(item)) for item in node.args]
            if node.func.id == "int" and len(values) == 1:
                return int(values[0])
            if node.func.id == "min" and len(values) >= 2:
                return min(values)
        raise UnsupportedProof(f"Unsupported or state-dependent expression: {type(node).__name__}")

    def assign(target, value):
        if isinstance(target, ast.Name) and target.id not in {observation, "int", "min", "dict", "float"}:
            local[target.id] = value
            return
        if isinstance(target, ast.Tuple) and isinstance(value, tuple) and len(target.elts) == len(value):
            if any(not isinstance(item, ast.Name) for item in target.elts) or len({item.id for item in target.elts}) != len(target.elts):
                raise UnsupportedProof("Tuple assignment requires distinct simple local names.")
            for child, item in zip(target.elts, value):
                assign(child, item)
            return
        raise UnsupportedProof("Assignment may target only simple locals or a matching local tuple.")

    body = [node for node in fn.body if not _doc(node)]
    if not body or not isinstance(body[-1], ast.Return) or not isinstance(body[-1].value, ast.Dict):
        raise UnsupportedProof("Function must end in a direct output dictionary return.")
    for statement in body[:-1]:
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            raise UnsupportedProof("Only simple/tuple local assignments before return are supported.")
        assign(statement.targets[0], expression(statement.value))
    returned = body[-1].value
    if len(returned.keys) != 2 or any(not isinstance(key, ast.Constant) or type(key.value) is not str for key in returned.keys):
        raise UnsupportedProof("Return requires exactly two literal output keys.")
    action = {key.value: expression(value) for key, value in zip(returned.keys, returned.values)}
    if set(action) != {"count", "radius_scale"} or type(action["count"]) is not int or not 0 <= action["count"] <= swarm_size:
        raise UnsupportedProof("Proven return violates the integer-count output contract.")
    radius = numeric(action["radius_scale"])
    if radius < 0:
        raise UnsupportedProof("Proven radius is negative.")
    return {"count": action["count"], "radius_scale": float(radius)}


def checksum(content):
    return hashlib.sha256(content).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def certifier_identity():
    relative = str(Path(__file__).resolve().relative_to(ROOT))
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    committed = subprocess.check_output(["git", "show", f"{revision}:{relative}"], cwd=ROOT)
    current = Path(__file__).read_bytes()
    if committed != current:
        raise ValueError("Commit the exact certifier before certifying protected-study metadata.")
    return {"path": relative, "sha256": checksum(current), "source_revision": revision}


def verify_recorded_certifier(identity):
    if not re.fullmatch(r"[0-9a-f]{40,64}", identity["source_revision"]):
        raise ValueError("Recorded certifier revision must be a complete commit hash.")
    relative = str(Path(__file__).resolve().relative_to(ROOT))
    if identity["path"] != relative:
        raise ValueError("Recorded certifier path differs from this helper.")
    committed = subprocess.check_output(["git", "show", f"{identity['source_revision']}:{relative}"], cwd=ROOT)
    if checksum(committed) != identity["sha256"]:
        raise ValueError("Recorded historical revision does not contain the certified helper bytes.")


def require_unprotected(folder):
    present = [name for name in PROTECTED if (folder / name).exists()]
    if present:
        raise ValueError(f"Certification must precede source review and all protected stages: {present}")


def amended_shortlist(original, certificate):
    amended = deepcopy(original)
    provenance = {key: certificate[key] for key in ("version", "certificate_id", "certified_at", "certifier", "original_shortlists_sha256", "domain", "controller_reference")}
    provenance.update(certificate_file=CERTIFICATE, original_shortlists_file=ORIGINAL)
    amended["constant_alias_certification"] = provenance
    for name, proof in certificate["program_proofs"].items():
        if proof["status"] == "proved":
            amended["programs"][name]["proven_constant"] = proof["action"]
            amended["programs"][name]["constant_proof"] = {
                "certificate_id": certificate["certificate_id"], "certificate_file": CERTIFICATE,
                "source_sha256": proof["source_sha256"], "domain": certificate["domain"]}
    for name, proof in certificate["partial_output_proofs"].items():
        amended["programs"][name]["proven_constant_outputs"] = proof
        amended["programs"][name]["partial_output_proof"] = {
            "certificate_id": certificate["certificate_id"], "certificate_file": CERTIFICATE,
            "controller_reference": certificate["controller_reference"]}
    return amended


def exclusive_bytes(path, content):
    with path.open("xb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def replace_shortlist(path, content):
    # Called only while the study lock is held and the current hash is exactly
    # the original or certified hash recorded in the append-only certificate.
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".shortlists-certification-", delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def certify(folder):
    import fcntl
    folder = Path(folder).resolve()
    if not folder.is_dir():
        raise ValueError("A registered study with frozen native shortlists is required.")
    with (folder / ".study-controller.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require_unprotected(folder)
        registration = verify_registration(folder)
        assert_cases(registration["search_cases"], 4)
        assert_cases(registration["validation_cases"], 8)
        for config in registration["search_cases"] + registration["validation_cases"]:
            require_domain(config)
        controller = controller_reference(folder)
        identity = certifier_identity()
        path, backup, record_path = folder / "shortlists.json", folder / ORIGINAL, folder / CERTIFICATE
        current = path.read_bytes()
        if record_path.exists():
            certificate = read_json(record_path)
            basis = {key: value for key, value in certificate.items() if key not in {"certificate_id", "certified_shortlists_sha256"}}
            if checksum(json_bytes(basis)) != certificate["certificate_id"]:
                raise ValueError("Existing proof certificate content changed.")
            if any(certificate["certifier"][key] != identity[key] for key in ("path", "sha256")) or certificate["registration_sha256"] != checksum((folder / "registration.json").read_bytes()):
                raise ValueError("Existing certification cannot be changed under another certifier or registration.")
            if certificate["controller_reference"] != controller:
                raise ValueError("Existing certification is bound to another controller amendment chain.")
            # Later unrelated commits do not change an already recorded proof.
            # Verify its historical commit, retaining that revision verbatim.
            verify_recorded_certifier(certificate["certifier"])
            original_bytes = backup.read_bytes()
            if checksum(original_bytes) != certificate["original_shortlists_sha256"]:
                raise ValueError("Preserved original shortlist bytes changed.")
            amended = json_bytes(amended_shortlist(json.loads(original_bytes), certificate))
            if checksum(amended) != certificate["certified_shortlists_sha256"] or checksum(current) not in {certificate["original_shortlists_sha256"], certificate["certified_shortlists_sha256"]}:
                raise ValueError("Existing certification or shortlist was changed.")
            verify_shortlists(folder)
            if current != amended:
                replace_shortlist(path, amended)  # Finish a crash before metadata publication.
            return certificate
        verify_shortlists(folder)
        if backup.exists() and backup.read_bytes() != current:
            raise ValueError("Preserved original shortlist differs; refusing ambiguous recovery.")
        original = json.loads(current)
        if "constant_alias_certification" in original:
            raise ValueError("Certified shortlist lacks its immutable proof certificate.")
        proofs, partial_proofs = {}, {}
        for name, program in original["programs"].items():
            policy = (folder / program["policy"]).resolve()
            if not policy.is_relative_to(folder / "programs"):
                raise ValueError("Frozen candidate path escapes the study programs directory.")
            source = policy.read_bytes()
            if checksum(source) != program["sha256"]:
                raise ValueError("Candidate source differs from its frozen SHA-256.")
            partial = reviewed_output_proof(program["sha256"])
            if partial is not None:
                partial_proofs[name] = partial
            try:
                action = prove_constant(source.decode())
            except UnsupportedProof as exc:
                proofs[name] = {"status": "not_proved", "source_sha256": program["sha256"], "reason": str(exc)}
            else:
                old = program.get("proven_constant")
                if old is not None and {**old, "count": 5 if old["count"] == "swarm_size" else old["count"]} != action:
                    raise ValueError("Static certificate disagrees with the registered constant recognizer.")
                proofs[name] = {"status": "proved", "source_sha256": program["sha256"], "action": action,
                    "reason": "Whitelist AST proof over fixed swarm_size=5; no candidate import or execution, unknown state, external access, mutation, branches, loops or persistent effects."}
        certificate = {"version": VERSION, "certified_at": datetime.now(timezone.utc).isoformat(),
            "certifier": identity, "registration_sha256": checksum((folder / "registration.json").read_bytes()),
            "original_shortlists_sha256": checksum(current), "domain": {"particles_per_swarm": 5, "swarm_size_python_type": "int"},
            "program_proofs": proofs, "partial_output_proofs": partial_proofs,
            "controller_reference": controller, "protected_stages_existed": False,
            "amendment": "Exact source proof metadata supersedes the original shortlist hash before source-review/validation freeze. Search ranks, candidate sources, program set and selection rules are unchanged. Original registration/snapshots remain intact; the active controller is bound by the explicit referenced amendment when present. Added after development search outcomes; not represented as pre-search implementation.",
            "telemetry": "Aliases retain the representative execution checkpoint unchanged. Nominal component interventions and proven action pairs come from method metadata; absent component_substitution/original_candidate_action fields are not fabricated.",
            "actions": {"candidate_calls": 0, "objective_queries": 0, "model_calls": 0}}
        certificate["certificate_id"] = checksum(json_bytes(certificate))
        amended = json_bytes(amended_shortlist(original, certificate))
        certificate["certified_shortlists_sha256"] = checksum(amended)
        require_unprotected(folder)
        if path.read_bytes() != current:
            raise ValueError("Shortlist changed during certification.")
        if not backup.exists():
            exclusive_bytes(backup, current)
        # Persist proof before replacing active metadata, making interrupted
        # publication resumable only to the already certified bytes.
        exclusive_bytes(record_path, json_bytes(certificate))
        replace_shortlist(path, amended)
        verify_shortlists(folder)
        return certificate


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    result = certify(parser.parse_args().run)
    print(json.dumps({"certificate_id": result["certificate_id"],
                      "proved_programs": sum(p["status"] == "proved" for p in result["program_proofs"].values()),
                      "partial_output_proofs": len(result["partial_output_proofs"]),
                      "original_shortlists_sha256": result["original_shortlists_sha256"],
                      "certified_shortlists_sha256": result["certified_shortlists_sha256"],
                      "actions": result["actions"]}, indent=2), flush=True)
