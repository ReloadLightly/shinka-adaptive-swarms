"""Identity receipt for the isolated v2 Java build; no research or campaign state writes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "build/paper-build-identity.json"
BEFORE = ROOT / "build/paper-source-before.json"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sources():
    paths = sorted(list((ROOT / "java-paper").rglob("*.java"))
                   + list((ROOT / "upstream/multiplex/Agents").glob("*.java"))
                   + list((ROOT / "vendor").glob("*.jar"))
                   + [ROOT / "scripts/build_paper_java.sh"])
    return {str(path.relative_to(ROOT)): sha(path.read_bytes()) for path in paths if "policies" not in path.parts}


def classes():
    return {str(path.relative_to(ROOT)): sha(path.read_bytes())
            for path in sorted((ROOT / "build/paper-classes").rglob("*.class"))}


def main(mode):
    current = sources()
    if mode == "prepare":
        BEFORE.parent.mkdir(parents=True, exist_ok=True)
        BEFORE.write_bytes(canonical(current) + b"\n")
    elif mode == "finish":
        if json.loads(BEFORE.read_text()) != current:
            raise SystemExit("Engine source changed during compilation; rebuild before running")
        receipt = {"schema": "paper-java-build-v1", "source_files": current,
                   "engine_sha256": sha(canonical(current)), "class_files": classes(),
                   "seed_policy_sha256": sha((ROOT / "java-paper/policies/CandidatePolicy.java").read_bytes()),
                   "upstream_commit": "b3d7737613578da260fee561b6f73122dc4f2ab0",
                   "created_at_utc": datetime.now(timezone.utc).isoformat()}
        RECEIPT.write_bytes(canonical(receipt) + b"\n")
        print(json.dumps({"engine_sha256": receipt["engine_sha256"], "receipt": str(RECEIPT.relative_to(ROOT))}))
    elif mode == "verify":
        receipt = json.loads(RECEIPT.read_text())
        if receipt["source_files"] != current or receipt["engine_sha256"] != sha(canonical(current)):
            raise SystemExit("Stale Java build: source identity differs")
        if receipt["class_files"] != classes():
            raise SystemExit("Stale or altered Java build: compiled class identity differs")
        print(json.dumps({"pass": True, "engine_sha256": receipt["engine_sha256"]}))
    else:
        raise SystemExit("Usage: build_identity.py prepare|finish|verify")


if __name__ == "__main__":
    main(sys.argv[1])
