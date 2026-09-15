import asyncio
import gzip
import json
import logging
from pathlib import Path
import sqlite3
import sys
from types import SimpleNamespace

import pytest

from adaptive_swarms.native_storage import (
    EvidenceRotatingWriter, NativeStorageMixin, install_native_storage,
    recover_pending_spec, sha256_file, write_best_reference, read_rotated_text,
)


def test_rotated_evidence_roundtrips_and_append_retains_old_log(tmp_path):
    path = tmp_path / "job_log.out"
    path.write_text("historical parent evidence\n")
    writer = EvidenceRotatingWriter(path, max_bytes=8)
    writer.write("new outcome\n")
    writer.close()
    archives = list(tmp_path.glob("*.gz"))
    assert len(archives) == 1
    with gzip.open(archives[0], "rt") as archive:
        assert archive.read() == "historical parent evidence\n"
    assert path.read_text() == "new outcome\n"
    assert all(p.suffix == ".gz" for p in tmp_path.glob("*.segment-*"))


def test_rotation_disk_error_keeps_complete_original_and_does_not_retry(tmp_path, monkeypatch):
    path = tmp_path / "job_log.err"
    writer = EvidenceRotatingWriter(path, max_bytes=1)
    writer.write("an original error\n")
    calls = []
    def full(*args, **kwargs):
        calls.append(1)
        raise OSError(28, "No space left on device")
    monkeypatch.setattr(gzip, "open", full)
    with pytest.raises(OSError):
        writer.write("next error\n")
    with pytest.raises(OSError, match="no automatic output retry"):
        writer.write("next error\n")
    writer.close()
    segments = list(tmp_path.glob("*.segment-*"))
    assert len(segments) == 1
    assert segments[0].read_text() == "an original error\n"
    assert len(calls) == 1


def test_best_native_hook_uses_manifest_preserves_historical_tree_and_no_hardlinks(tmp_path):
    folder = tmp_path / "gen_1"
    results = folder / "results"
    results.mkdir(parents=True)
    (folder / "main.py").write_text("def choose_response(o): return {}\n")
    (results / "case_000.json").write_text('{"offline_error": 1.25}')
    (results / "run.log").write_text("mutable operational data")
    old = tmp_path / "best" / "results"
    old.mkdir(parents=True)
    (old / "historical.json").write_text("retained")
    program = SimpleNamespace(id="best-id", generation=1, code=(folder / "main.py").read_text(), combined_score=.5)
    class DB:
        async def get_top_programs_async(self, **kwargs):
            assert kwargs == {"n": 1, "correct_only": True}
            return [program]
    class Runner(NativeStorageMixin):
        async_db = DB()
        results_dir = tmp_path
        best_program_id = None
    runner = Runner()
    asyncio.run(runner._update_best_solution_async())
    best = tmp_path / "best"
    assert set(p.name for p in best.iterdir()) == {"main.py", "artifacts.json"}
    assert (best / "main.py").stat().st_ino != (folder / "main.py").stat().st_ino
    assert next(tmp_path.glob("best-before-storage-*/results/historical.json")).read_text() == "retained"
    manifest = json.loads((best / "artifacts.json").read_text())
    assert manifest["program_id"] == "best-id"
    assert len(manifest["artifacts"]) == 2
    for reference in manifest["artifacts"]:
        artifact = best / reference["path"]
        assert sha256_file(artifact) == reference["sha256"]
    assert json.loads((best / manifest["artifacts"][1]["path"]).read_text())["offline_error"] == 1.25


def test_real_native_scheduler_uses_rotated_appending_sinks_without_tree_staging(tmp_path):
    pytest.importorskip("shinka")
    from shinka.core.async_runner import RichTeeConsole
    from shinka.launch import scheduler, local
    from rich.console import Console
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    handler = logging.FileHandler(tmp_path / "evolution_run.log")
    root_logger.addHandler(handler)
    runner = SimpleNamespace(results_dir=tmp_path, console=RichTeeConsole(Console(), tmp_path / "evolution_run.log"))
    original_submit = scheduler.submit_local
    result_dir = tmp_path / "gen_1" / "results"
    result_dir.mkdir(parents=True)
    (result_dir / "job_log.out").write_text("historical evaluation\n")
    (result_dir / "metrics.json").write_text('{"combined_score": 0.25}')
    (result_dir / "correct.json").write_text('{"correct": true}')
    checks = []
    try:
        with install_native_storage(runner, check_write=lambda: checks.append(1), max_log_bytes=16):
            process = scheduler.submit_local(str(result_dir), [sys.executable, "-c", "import os; print(os.environ['PYTHONDONTWRITEBYTECODE']); print('new evaluation')"])
            assert process.wait(timeout=10) == 0
            process.cleanup_logging()
            runner.console.print("native console evidence")
            downstream = local.load_results(result_dir)
            assert downstream["stdout_log"] == "historical evaluation\n1\nnew evaluation\n"
            assert downstream["metrics"]["combined_score"] == .25
            assert downstream["correct"]["correct"] is True
        assert scheduler.submit_local is original_submit
        archives = sorted(result_dir.glob("job_log.out.segment-*.gz"))
        archive_text = "".join(gzip.open(p, "rt").read() for p in archives)
        assert "historical evaluation" in archive_text
        current_text = (result_dir / "job_log.out").read_text()
        assert "new evaluation" in current_text + archive_text
        assert "1\n" in current_text + archive_text
        assert checks
        assert not list(tmp_path.rglob(".venv"))
        assert not list(tmp_path.rglob("__pycache__"))
    finally:
        root_logger.handlers[:] = original_handlers


def test_full_pending_checkpoint_reuses_lineage_and_skips_completed_generation(tmp_path):
    database = sqlite3.connect(tmp_path / "programs.sqlite")
    database.execute("CREATE TABLE programs (id TEXT, code TEXT, generation INTEGER)")
    folder = tmp_path / "gen_3"
    folder.mkdir()
    (folder / "main.py").write_text("candidate")
    spec = {"generation": 3, "exec_fname": str(folder / "main.py"), "parent_id": "parent", "archive_insp_ids": ["inspiration"], "meta_patch_data": {"llm_result": {"content": "original response"}}}
    (folder / "storage-job.json").write_text(json.dumps(spec))
    assert recover_pending_spec(folder) == spec
    database.execute("INSERT INTO programs VALUES (?, ?, ?)", ("persisted", "candidate", 3))
    database.commit()
    assert recover_pending_spec(folder) is None
    database.close()


def test_existing_accepted_gen3_recovery_reads_only_retained_artifacts():
    # Existing tiny, interrupted native artifact is the real compatibility risk.
    folder = Path(__file__).resolve().parents[1] / "results/evolution/20260915T101024.562418Z-search/gen_3"
    if not folder.exists():
        pytest.skip("Historical local checkpoint unavailable")
    spec = recover_pending_spec(folder)
    if spec is None:
        pytest.skip("Historical proposal has since completed")
    assert spec["generation"] == 3
    assert spec["parent_id"] == "ee03e4eb-bfd7-4f8c-a648-aa4ed0b9f6ee"
    assert spec["archive_insp_ids"] == ["c1fbd9c9-0524-43f4-8b9a-420c5c96146f"]
    assert spec["meta_patch_data"]["patch_name"] == "anchored_severity_response"
    assert spec["meta_patch_data"]["api_costs"] == .160232


def test_partial_rotation_prefers_complete_original(tmp_path):
    path = tmp_path / "job_log.err"
    original = tmp_path / "job_log.err.segment-00001"
    original.write_text("retained outcome\n")
    original.with_name(original.name + ".gz").write_bytes(b"partial gzip")
    path.write_text("next\n")
    assert read_rotated_text(path) == "retained outcome\nnext\n"


def test_native_sink_disk_full_callback_latches_once(tmp_path):
    from adaptive_swarms.storage import StorageInterrupted
    calls = []
    def on_error(error):
        calls.append(error.errno)
        raise StorageInterrupted("paused")
    writer = EvidenceRotatingWriter(tmp_path / "run.log", on_error=on_error)
    original = writer._stream
    class FullStream:
        def write(self, text):
            raise OSError(28, "No space left")
        def close(self):
            original.close()
    writer._stream = FullStream()
    with pytest.raises(StorageInterrupted):
        writer.write("outcome")
    with pytest.raises(OSError, match="no automatic output retry"):
        writer.write("outcome")
    assert calls == [28]
    writer.close()


def test_pre_submission_pause_recovers_accepted_program_with_disabled_novelty(tmp_path):
    parent = "11111111-1111-1111-1111-111111111111"
    database = sqlite3.connect(tmp_path / "programs.sqlite")
    database.execute("CREATE TABLE programs (id TEXT, code TEXT, generation INTEGER)")
    database.execute("INSERT INTO programs VALUES (?, ?, ?)", (parent, "original", 0))
    database.commit()
    database.close()
    folder = tmp_path / "gen_1"
    attempt = folder / "attempts/novelty_1/resample_1/patch_1"
    attempt.mkdir(parents=True)
    (folder / "original.py").write_text("original")
    (folder / "main.py").write_text("accepted candidate")
    for name in ("llm_response.txt", "headless_prompt.md", "patch.txt"):
        (attempt / name).write_text("saved " + name)
    metadata = {"success": True, "generation": 1, "llm_cost": .1, "patch_name": "accepted", "patch_description": "hypothesis", "num_applied": 1, "novelty_attempt": 1, "resample_attempt": 1, "patch_attempt": 1, "llm_model": "headless/codex@gpt-6-astra"}
    (attempt / "metadata.json").write_text(json.dumps(metadata))
    (tmp_path / "evolution_run.log").write_text(f"Generating proposal for generation 1\nSampled parent {parent} (Gen: 0)\nGenerated patch type: full\n")
    (tmp_path / "storage-stop.json").write_text('{"status":"storage_paused"}')
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"storage_native_configuration":{"embedding_model":null,"novelty_llm_models":null}}')
    spec = recover_pending_spec(folder)
    assert spec["parent_id"] == parent
    assert spec["archive_insp_ids"] == []
    assert "before scheduling" in spec["meta_patch_data"]["storage_recovery"]["acceptance_evidence"]
    manifest.write_text('{}')
    with pytest.raises(ValueError, match="documented storage pause"):
        recover_pending_spec(folder)
