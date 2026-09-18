"""Write/verify the exact Java build inputs and compiled outputs (no model calls)."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]


def inputs():
    return sorted(set(list((ROOT / "java").rglob("*.java")) + list((ROOT / "upstream/multiplex/Agents").glob("*.java")) + list((ROOT / "vendor").glob("*.jar")) + [ROOT / "scripts/build_java.sh", ROOT / "cooperative/build_identity.py"]))


def main():
    source = inputs()
    outputs = sorted((ROOT / "build/classes").rglob("*.class"))
    if not outputs:
        raise RuntimeError("Cannot record an empty Java build")
    manifest = {"inputs": [str(p.relative_to(ROOT)) for p in source],
                "files": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source + outputs}}
    (ROOT / "build/build_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
