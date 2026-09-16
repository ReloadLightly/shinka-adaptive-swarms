"""Static source proof and metadata freeze checks; never execute candidates."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from adaptive_swarms import joint_study as study
from adaptive_swarms.comparison import regime_key
from adaptive_swarms.logging import atomic_json

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("certify_joint_constants", ROOT / "scripts/certify_joint_constants.py")
cert = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cert)
FIXTURES = Path(__file__).parent / "fixtures/joint_alias_certification"
EXPECTED = {
    22: ("cf8db238a346baecfe592259f8e7fc75843c4df27e0fbe2dee09b8849a60aac2", 1.21875),
    17: ("f9935cf05f784c66c30ed8b3880be445a947ab028f758e14f77916b8b3a61a81", 1.1875),
    8: ("0c9f13d866080f1dbc9860b40215af46ba7ca3d9e5135af2f75341056fa6f815", 1.25),
}


@pytest.mark.parametrize("generation", [22, 17, 8])
def test_exact_completed_search_sources_prove_constants_without_execution(generation):
    source = (FIXTURES / f"gen_{generation}.py").read_bytes()
    checksum, radius = EXPECTED[generation]
    assert hashlib.sha256(source).hexdigest() == checksum
    assert study.proven_constant(source.decode()) is None
    assert cert.prove_constant(source.decode()) == {"count": 4, "radius_scale": radius}


@pytest.mark.parametrize("source", [
    "import os\ndef choose_relocation(o):\n return {'count':4,'radius_scale':1.0}\n",
    "def choose_relocation(o=open('secret')):\n return {'count':4,'radius_scale':1.0}\n",
    "def choose_relocation(o: print('side effect')):\n return {'count':4,'radius_scale':1.0}\n",
    "def choose_relocation(o):\n o['swarm_size']=4\n return {'count':4,'radius_scale':1.0}\n",
    "def choose_relocation(o):\n return {'count':min(4,int(o['swarm_size'])),'radius_scale':o['fitness_drop']}\n",
    "def choose_relocation(o):\n min=lambda *a: 0\n return {'count':min(4,5),'radius_scale':1.0}\n",
    "def choose_relocation(o):\n global x\n x=4\n return {'count':x,'radius_scale':1.0}\n",
    "def choose_relocation(o):\n if o['swarm_size']==5: return {'count':4,'radius_scale':1.0}\n",
    "def choose_relocation(o):\n return {'count':True,'radius_scale':1.0}\n",
    "def choose_relocation(o):\n return {'count':4,'radius_scale':1e999}\n",
    "def choose_relocation(o):\n return {'count':4,'radius_scale':-1.0}\n",
    "def choose_relocation(o):\n return {'count':6,'radius_scale':1.0}\n",
    "def choose_relocation(o):\n return {'count':4,'radius_scale':unknown()}\n",
])
def test_unsafe_unknown_or_out_of_contract_code_is_not_certified(source):
    with pytest.raises(cert.UnsupportedProof):
        cert.prove_constant(source)


@pytest.fixture
def frozen_fixture(tmp_path, monkeypatch):
    folder = tmp_path / "study"
    engine = tmp_path / "engine.json"
    atomic_json(engine, {"engine_config": {"profile_name": "static-proof-fixture"}})
    record = study.register_study(folder, {index: tmp_path/f"search_{index}" for index in range(3)}, engine)
    programs = {}
    (folder / "programs").mkdir()
    for generation, (checksum, _) in EXPECTED.items():
        policy = f"programs/{checksum}.py"
        (folder / policy).write_bytes((FIXTURES / f"gen_{generation}.py").read_bytes())
        name = "program_" + checksum
        programs[name] = {"name": name, "policy": policy, "sha256": checksum, "proven_constant": None,
                          "occurrences": [{"search_index": 0, "generation": generation, "search_rank": len(programs)+1}]}
    original = {"registration_sha256": cert.checksum((folder/"registration.json").read_bytes()),
                "programs": programs, "searches": [{"search_index": 0, "shortlist": list(programs)}],
                "selection_rule": "synthetic source-ranking metadata, no measured outcomes", "frozen_at": "fixture"}
    atomic_json(folder / "shortlists.json", original)
    identity = {"path": "scripts/certify_joint_constants.py", "sha256": cert.checksum(Path(cert.__file__).read_bytes()), "source_revision": "uncommitted-test-fixture-only"}
    monkeypatch.setattr(cert, "certifier_identity", lambda: identity)
    monkeypatch.setattr(cert, "verify_recorded_certifier", lambda _identity: None)
    return folder, record, original


def test_certification_preserves_original_sources_ranks_and_registration(frozen_fixture):
    folder, registration, original = frozen_fixture
    registration_bytes = (folder / "registration.json").read_bytes()
    original_bytes = (folder / "shortlists.json").read_bytes()
    record = cert.certify(folder)
    assert (folder / cert.ORIGINAL).read_bytes() == original_bytes
    assert (folder / "registration.json").read_bytes() == registration_bytes
    amended = study.verify_shortlists(folder)
    assert amended["searches"] == original["searches"]
    assert amended["selection_rule"] == original["selection_rule"]
    assert set(amended["programs"]) == set(original["programs"])
    for name, program in amended["programs"].items():
        assert {key: program[key] for key in ("sha256", "policy", "occurrences")} == {key: original["programs"][name][key] for key in ("sha256", "policy", "occurrences")}
        assert program["proven_constant"]["count"] == 4
    assert record["actions"] == {"candidate_calls": 0, "objective_queries": 0, "model_calls": 0}
    assert study.verify_registration(folder) == registration
    saved = {path.name: path.read_bytes() for path in (folder/cert.CERTIFICATE, folder/cert.ORIGINAL, folder/"shortlists.json")}
    assert cert.certify(folder) == record
    assert saved == {name: (folder/name).read_bytes() for name in saved}
    atomic_json(folder / "source_review.json", {"reviewed": True})
    with pytest.raises(ValueError, match="precede source review"):
        cert.certify(folder)


@pytest.mark.parametrize("protected", ["validation", "selection.json", "final_cases.json", "final", "analysis.json"])
def test_certification_refuses_any_protected_stage(frozen_fixture, protected):
    folder, _, _ = frozen_fixture
    (folder / protected).touch()
    with pytest.raises(ValueError, match="precede source review"):
        cert.certify(folder)
    assert not (folder / cert.CERTIFICATE).exists()


def test_interrupted_metadata_publication_resumes_only_certified_bytes(frozen_fixture, monkeypatch):
    folder, _, _ = frozen_fixture
    replace = cert.replace_shortlist
    def interrupted(*_args):
        raise OSError("synthetic interruption before metadata publication")
    monkeypatch.setattr(cert, "replace_shortlist", interrupted)
    with pytest.raises(OSError, match="synthetic interruption"):
        cert.certify(folder)
    original_certificate = (folder / cert.CERTIFICATE).read_bytes()
    assert (folder / cert.ORIGINAL).read_bytes() == (folder / "shortlists.json").read_bytes()
    monkeypatch.setattr(cert, "replace_shortlist", replace)
    cert.certify(folder)
    assert (folder / cert.CERTIFICATE).read_bytes() == original_certificate
    assert cert.checksum((folder / "shortlists.json").read_bytes()) == json.loads(original_certificate)["certified_shortlists_sha256"]
    changed = json.loads((folder / "shortlists.json").read_bytes())
    changed["selection_rule"] = "tampered"
    atomic_json(folder / "shortlists.json", changed)
    with pytest.raises(ValueError, match="shortlist was changed"):
        cert.certify(folder)


def test_recovery_allows_later_unrelated_commit_and_keeps_recorded_revision(frozen_fixture, monkeypatch):
    folder, _, _ = frozen_fixture
    replace = cert.replace_shortlist
    def interrupted(*_args):
        raise OSError("fixture interruption")
    monkeypatch.setattr(cert, "replace_shortlist", interrupted)
    with pytest.raises(OSError, match="fixture interruption"):
        cert.certify(folder)
    original_bytes = (folder / cert.CERTIFICATE).read_bytes()
    original = json.loads(original_bytes)
    newer = {**original["certifier"], "source_revision": "later-unrelated-test-commit"}
    verified = []
    monkeypatch.setattr(cert, "certifier_identity", lambda: newer)
    monkeypatch.setattr(cert, "verify_recorded_certifier", lambda identity: verified.append(identity))
    monkeypatch.setattr(cert, "replace_shortlist", replace)
    assert cert.certify(folder) == original
    assert verified == [original["certifier"]]
    assert (folder / cert.CERTIFICATE).read_bytes() == original_bytes
    assert json.loads((folder / "shortlists.json").read_bytes())["constant_alias_certification"]["certifier"] == original["certifier"]


def test_certificate_metadata_drives_existing_aliases_without_fabricated_telemetry(frozen_fixture):
    folder, registration, _ = frozen_fixture
    cert.certify(folder)
    program = {"kind": "program", **study.verify_shortlists(folder)["programs"]["program_" + EXPECTED[8][0]]}
    config = registration["search_cases"][0]
    expected = study.method_identity({"kind":"fixed", "count":4, "radius_scale":1.25}, config)
    assert study.method_identity(program, config) == expected
    count_unchanged = {"kind":"component", "program":program, "component":"count", "replacement":4}
    assert study.method_identity(count_unchanged, config) == expected
    radius_replaced = {"kind":"component", "program":program, "component":"radius_scale", "replacement":1.0}
    assert study.method_identity(radius_replaced, config) == study.method_identity({"kind":"fixed", "count":4, "radius_scale":1.0}, config)
    case = {"config": config, "response_log": [{"requested_count":4, "requested_radius_scale":1.25}]}
    raw = deepcopy(case)
    sampler = study.freeze_joint_sampler([case], program)
    assert study.method_identity(sampler, config) == expected
    assert study.nominal_action_pairs(case, count_unchanged) == [[4,1.25]]
    assert case == raw and "component_substitution" not in case["response_log"][0]
    empty = {"config": config, "response_log": []}
    mixed = study.freeze_joint_sampler([case, empty], program)
    assert study.method_identity(mixed, config)["kind"] == "joint_sampler"
    assert mixed["regime_cases"][regime_key(config)][1]["no_response_baseline_fallback"]
    zero_component = {**count_unchanged, "replacement":0}
    measured = {"config":config, "response_log":[{"requested_count":0, "requested_radius_scale":.5}]}
    original = deepcopy(measured)
    assert study.nominal_action_pairs(measured, zero_component) == [[0,1.25]]
    assert measured == original
