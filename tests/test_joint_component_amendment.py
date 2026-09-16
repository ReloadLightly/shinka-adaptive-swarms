"""Exact-source partial facts and amendment durability; no policy/objective calls."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

import pytest

from adaptive_swarms import joint_study as study
from adaptive_swarms import joint_alias_amendment as amendment
from adaptive_swarms.logging import atomic_json

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures/joint_component_aliases"


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load_script("install_joint_alias_amendment")
certifier = load_script("certify_joint_constants")
audit_tool = load_script("audit_joint_progress")


@pytest.fixture
def predecessor(tmp_path, monkeypatch):
    folder = tmp_path / "source" / "study"
    engine = tmp_path / "engine.json"
    atomic_json(engine, {"engine_config": {"profile_name": "metadata-only amendment fixture"}})
    record = study.register_study(folder, {index: tmp_path/f"absent_search_{index}" for index in range(3)}, engine)
    # Fabricated predecessor source bytes: no historical candidate or evaluator
    # is executed. This exercises the same immutable source-delta chain.
    old = b"# Original metadata-only controller snapshot; never executed.\n"
    name = amendment.CONTROLLER.replace("/", "__")
    (folder / "runner_snapshot" / name).write_bytes(old)
    record["execution_sources"][amendment.CONTROLLER] = hashlib.sha256(old).hexdigest()
    record["runner_snapshot"][name] = hashlib.sha256(old).hexdigest()
    record["execution_sources"].pop(amendment.SUPPORT)
    support_snapshot = amendment.SUPPORT.replace("/", "__")
    record["runner_snapshot"].pop(support_snapshot)
    (folder / "runner_snapshot" / support_snapshot).unlink()
    fields = ("settings", "searches", "engine_config", "search_cases", "validation_cases", "execution_sources", "task_sources", "analysis")
    record["signature"] = study.digest({key:record[key] for key in fields})
    atomic_json(folder / "registration.json", record)
    def committed(paths, revision=None):
        return revision or "1"*40, {name: amendment.file_sha(ROOT/name) for name in paths}
    monkeypatch.setattr(installer, "committed_sources", committed)
    monkeypatch.setattr(certifier, "certifier_identity", lambda: {"path":"scripts/certify_joint_constants.py", "sha256":amendment.file_sha(ROOT/"scripts/certify_joint_constants.py"), "source_revision":"1"*40})
    monkeypatch.setattr(certifier, "verify_recorded_certifier", lambda _: None)
    return folder, record


def add_source_shortlist(folder):
    programs = {}
    (folder / "programs").mkdir()
    for path in sorted(FIXTURES.glob("*.py")):
        source = path.read_bytes()
        checksum = hashlib.sha256(source).hexdigest()
        policy = f"programs/{checksum}.py"
        (folder / policy).write_bytes(source)
        programs["program_"+checksum] = {"policy":policy, "sha256":checksum, "proven_constant":None,
                                       "name":"program_"+checksum, "occurrences":[]}
    atomic_json(folder/"shortlists.json", {"registration_sha256":amendment.file_sha(folder/"registration.json"),
                "programs":programs, "searches":[], "selection_rule":"fixture; no measured outcomes"})
    return programs


def test_registry_is_only_six_exact_reviewed_nonconstant_sources():
    hashes = {hashlib.sha256(path.read_bytes()).hexdigest() for path in FIXTURES.glob("*.py")}
    assert len(hashes) == 6 and hashes == set(amendment.REVIEWED_OUTPUTS)
    for path in FIXTURES.glob("*.py"):
        source = path.read_bytes()
        checksum = hashlib.sha256(source).hexdigest()
        assert study.proven_constant(source.decode()) is None
        with pytest.raises(certifier.UnsupportedProof):
            certifier.prove_constant(source.decode())
        fact = amendment.reviewed_output_proof(checksum)
        assert fact["outputs"] == {"radius_scale":1.25 if path.name.startswith("search_1") else 1.5}
        assert amendment.reviewed_output_proof(hashlib.sha256(source+b"\n").hexdigest()) is None
    assert amendment.reviewed_output_proof("0"*64) is None


def test_adaptive_winner_and_component_aliases_keep_exact_nominal_semantics(predecessor):
    folder, record = predecessor
    installer.install(folder)
    add_source_shortlist(folder)
    certificate = certifier.certify(folder)
    assert certificate["controller_reference"]["kind"] == amendment.AMENDMENT_VERSION
    assert len(certificate["partial_output_proofs"]) == 6
    config = record["search_cases"][0]
    for program in study.verify_shortlists(folder)["programs"].values():
        assert program["proven_constant"] is None
        method = {"kind":"program", **program}
        assert study.method_identity(method, config) == {"kind":"joint_program", "sha256":program["sha256"]}
        radius = program["proven_constant_outputs"]["outputs"]["radius_scale"]
        replaced = {"kind":"component", "program":method, "component":"count", "replacement":4}
        assert study.method_identity(replaced, config) == study.method_identity({"kind":"fixed", "count":4, "radius_scale":radius}, config)
        assert study.nominal_constant_action(replaced, config) == {"count":4, "radius_scale":radius}
        zero = {**replaced, "replacement":0}
        assert study.method_identity(zero, config) == study.method_identity({"kind":"fixed", "count":0, "radius_scale":.5}, config)
        measured = {"config":config, "response_log":[{"requested_count":0, "requested_radius_scale":.5}]}
        untouched = deepcopy(measured)
        assert study.nominal_action_pairs(measured, zero) == [[0,radius]]
        assert measured == untouched and "original_candidate_action" not in measured["response_log"][0]
        radius_replaced = {**replaced, "component":"radius_scale", "replacement":1.0}
        assert study.method_identity(radius_replaced, config)["kind"] == "joint_component"
        assert study.nominal_constant_action(radius_replaced, config) is None


def test_partial_rule_supports_a_retained_count_without_adding_real_source_facts(monkeypatch):
    # A synthetic registry fact tests the generic two-output rule. It is never
    # written into the scientific registry or used on a candidate/source case.
    source = "a"*64
    fact = {"outputs":{"count":4}, "source_sha256":source}
    monkeypatch.setattr(amendment, "reviewed_output_proof", lambda checksum: fact if checksum==source else None)
    method = {"kind":"component", "program":{"sha256":source, "proven_constant_outputs":fact},
              "component":"radius_scale", "replacement":1.25}
    config = {"particles_per_swarm":5,"dimension":5,"move_severity":1.}
    assert amendment.component_constant_action(method, config) == {"count":4,"radius_scale":1.25}


def test_source_registry_and_domain_tampering_cannot_create_aliases(predecessor, monkeypatch):
    _, record = predecessor
    source = next(iter(amendment.REVIEWED_OUTPUTS))
    proof = amendment.reviewed_output_proof(source)
    method = {"kind":"component", "program":{"sha256":source,"proven_constant_outputs":proof}, "component":"count","replacement":4}
    config = record["search_cases"][0]
    for change in ({"particles_per_swarm":4},{"dimension":2},{"move_severity":2.}):
        with pytest.raises(ValueError,match="outside the declared"):
            study.method_identity(method,{**config,**change})
    bad = deepcopy(method)
    bad["program"]["sha256"] = "0"*64
    with pytest.raises(ValueError,match="exact reviewed source/registry"):
        study.method_identity(bad,config)
    bad = deepcopy(method)
    bad["program"]["proven_constant_outputs"]["outputs"]["radius_scale"] = 9.
    with pytest.raises(ValueError,match="exact reviewed source/registry"):
        study.method_identity(bad,config)
    monkeypatch.setitem(amendment.REVIEWED_OUTPUTS,source,{**amendment.REVIEWED_OUTPUTS[source],"outputs":{"radius_scale":2.}})
    with pytest.raises(ValueError,match="exact reviewed source/registry"):
        study.method_identity(method,config)


def test_install_preserves_predecessor_and_portable_verification_needs_no_git_or_old_paths(predecessor,tmp_path,monkeypatch):
    folder, original = predecessor
    before = {str(path.relative_to(folder)):path.read_bytes() for path in (folder/"runner_snapshot").iterdir()}
    registration_bytes = (folder/"registration.json").read_bytes()
    with pytest.raises(ValueError,match="without the explicit committed"):
        study.verify_registration(folder)
    amendment_record = installer.install(folder)
    assert installer.install(folder) == amendment_record
    assert study.verify_registration(folder) == original
    assert (folder/"registration.json").read_bytes() == registration_bytes
    assert before == {name:(folder/name).read_bytes() for name in before}
    copied = tmp_path/"archive"/"copied-study"
    shutil.copytree(folder,copied)
    shutil.rmtree(folder)
    def no_git(*_args,**_kwargs):
        raise AssertionError("Read-only archive verification must not invoke git")
    monkeypatch.setattr(installer.subprocess,"check_output",no_git)
    assert study.verify_registration(copied) == original
    assert amendment.controller_reference(copied)["amendment_id"] == amendment_record["amendment_id"]
    progress = audit_tool.audit(copied)
    assert progress["original_registration_and_snapshots_preserved"] is True
    assert progress["current_scientific_sources_match_original"] is False
    assert progress["active_controller_amendment"]["amendment_id"] == amendment_record["amendment_id"]
    assert "frozen_scientific_sources_unchanged" not in progress


def test_pending_install_resumes_exact_record_and_snapshot_tamper_is_rejected(predecessor,monkeypatch):
    folder, _ = predecessor
    write = installer.write_once
    def interrupted(path,content):
        if path.parent.name == amendment.SNAPSHOT_DIR:
            raise OSError("fixture snapshot interruption")
        write(path,content)
    monkeypatch.setattr(installer,"write_once",interrupted)
    with pytest.raises(OSError,match="fixture snapshot"):
        installer.install(folder)
    pending = (folder/installer.PENDING).read_bytes()
    assert not (folder/amendment.AMENDMENT_FILE).exists()
    monkeypatch.setattr(installer,"write_once",write)
    record = installer.install(folder)
    assert record == json.loads(pending)
    assert not (folder/installer.PENDING).exists()
    path = folder/record["snapshot_paths"][amendment.SUPPORT]
    path.write_bytes(path.read_bytes()+b"# changed\n")
    with pytest.raises(ValueError,match="snapshot changed"):
        study.verify_registration(folder)


@pytest.mark.parametrize("protected",[*amendment.PROTECTED,"constant_alias_certification.json"])
def test_install_refuses_protected_or_certified_study(predecessor,protected):
    folder,_ = predecessor
    (folder/protected).touch()
    with pytest.raises(ValueError,match="must precede"):
        installer.install(folder)
    assert not (folder/amendment.AMENDMENT_FILE).exists()


def test_changed_amendment_original_snapshot_and_chronology_are_rejected(predecessor):
    folder,_ = predecessor
    record = installer.install(folder)
    mutated = deepcopy(record)
    mutated["partial_output_registry_sha256"] = "0"*64
    mutated["amendment_id"] = amendment.digest({key:value for key,value in mutated.items() if key!="amendment_id"})
    atomic_json(folder/amendment.AMENDMENT_FILE,mutated)
    with pytest.raises(ValueError,match="registry"):
        study.verify_registration(folder)
    atomic_json(folder/amendment.AMENDMENT_FILE,record)
    atomic_json(folder/"source_review.json",{"reviewed_at":"2000-01-01T00:00:00+00:00"})
    with pytest.raises(ValueError,match="predates controller"):
        study.verify_registration(folder)
    (folder/"source_review.json").unlink()
    original_snapshot = folder/"runner_snapshot"/amendment.CONTROLLER.replace("/","__")
    original_snapshot.write_bytes(b"changed original")
    with pytest.raises(ValueError,match="Frozen source snapshot changed"):
        study.verify_registration(folder)


def test_installer_requires_exact_committed_tool_bytes(monkeypatch):
    monkeypatch.setattr(installer.subprocess,"check_output",lambda *_args,**_kwargs:b"different committed bytes")
    with pytest.raises(ValueError,match="Commit the exact amendment"):
        installer.committed_sources([amendment.SUPPORT],"1"*40)
