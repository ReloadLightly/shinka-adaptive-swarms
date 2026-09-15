"""Storage adapters for the pinned native Shinka runner; search stays upstream.

Only artifact presentation and local output sinks change. No repository, virtual
environment, or result tree is copied into a candidate's evaluation workspace.
"""
from __future__ import annotations

import asyncio
from contextlib import contextmanager
import gzip
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import threading
import time
import uuid


LOG_CHUNK_BYTES = 4 * 1024 * 1024


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_text(path, text):
    path = Path(path)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


class EvidenceRotatingWriter:
    """A bounded active text log with losslessly compressed, retained segments.

    Old logs may contain the only sampling/lineage record before a crash. Keep
    every archive, verify its uncompressed checksum before unlinking a segment,
    and leave files alone on errors. Never retry a failed write automatically.
    """

    def __init__(self, path, max_bytes=LOG_CHUNK_BYTES, check_write=None, on_error=None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.max_bytes = max_bytes
        self.check_write = check_write
        self.on_error = on_error
        self._lock = threading.RLock()
        self._stream = self.path.open("a", encoding="utf-8", buffering=1)
        self._size = self.path.stat().st_size
        self._failed = False

    def write(self, text):
        with self._lock:
            if self._failed:
                raise OSError("Previous log write failed; no automatic output retry")
            try:
                result = 0
                for start in range(0, len(text), 256 * 1024):
                    chunk = text[start:start + 256 * 1024]
                    if self.check_write:
                        self.check_write()
                    if self._size >= self.max_bytes:
                        self._rotate()
                    result += self._stream.write(chunk)
                    self._size += len(chunk.encode("utf-8"))
                return result
            except BaseException as exc:
                self._failed = True
                if isinstance(exc, OSError):
                    if self.on_error is not None:
                        self.on_error(exc)
                    else:
                        from .storage import get_storage_guard
                        guard = get_storage_guard(self.path.parent)
                        if guard is not None:
                            guard.disk_full(exc, activity=f"native log {self.path.name}")
                raise

    def _rotate(self):
        self._stream.flush()
        self._stream.close()
        segment = self.path.with_name(self.path.name + f".segment-{time.time_ns():020d}-" + uuid.uuid4().hex)
        self.path.rename(segment)
        self._stream = self.path.open("a", encoding="utf-8", buffering=1)
        self._size = 0
        compressed = segment.with_name(segment.name + ".gz")
        digest = hashlib.sha256()
        try:
            with segment.open("rb") as source, gzip.open(compressed, "xb", compresslevel=3) as destination:
                for block in iter(lambda: source.read(256 * 1024), b""):
                    if self.check_write:
                        self.check_write()
                    digest.update(block)
                    destination.write(block)
            verified = hashlib.sha256()
            with gzip.open(compressed, "rb") as source:
                for block in iter(lambda: source.read(256 * 1024), b""):
                    verified.update(block)
            if verified.digest() != digest.digest():
                raise OSError(f"Compressed operational log failed verification: {compressed}")
            segment.unlink()
        except BaseException:
            # This partial compressed file belongs to this invocation. The
            # complete uncompressed segment remains the authoritative evidence.
            compressed.unlink(missing_ok=True)
            raise

    def flush(self):
        with self._lock:
            self._stream.flush()

    def close(self):
        with self._lock:
            self._stream.close()


def read_rotated_text(path):
    """Read retained segments in creation order followed by the active text log."""
    path = Path(path)
    chunks = []
    for segment in sorted(path.parent.glob(path.name + ".segment-*")):
        # A verified gzip supersedes its source; an interrupted compression
        # leaves only the original source. Do not duplicate a surviving pair.
        if segment.suffix == ".gz" and segment.with_suffix("").exists():
            continue
        opener = gzip.open if segment.suffix == ".gz" else open
        with opener(segment, "rt", encoding="utf-8") as stream:
            chunks.append(stream.read())
    if path.exists():
        chunks.append(path.read_text())
    return "".join(chunks)


class NativeStorageMixin:
    async def _update_best_solution_async(self):
        """Keep native best selection; reference completed immutable artifacts."""
        if not self.async_db:
            return
        if getattr(self, "_best_solution_lock", None) is None:
            self._best_solution_lock = asyncio.Lock()
        async with self._best_solution_lock:
            programs = await self.async_db.get_top_programs_async(n=1, correct_only=True)
            if not programs:
                return
            best = programs[0]
            destination = Path(self.results_dir) / "best"
            if best.id == self.best_program_id and (destination / "artifacts.json").exists():
                return
            try:
                await asyncio.to_thread(write_best_reference, self.results_dir, best)
            except OSError as exc:
                guard = getattr(self, "storage_guard", None)
                if guard is not None:
                    guard.disk_full(exc, activity="best artifact manifest")
                raise
            self.best_program_id = best.id
            logging.getLogger(__name__).info("Best gen %s id %s references its original artifacts", best.generation, best.id)


def write_best_reference(run_dir, program):
    run_dir = Path(run_dir)
    source = run_dir / f"gen_{program.generation}"
    main = source / "main.py"
    # Native archive code and candidate file should identify the same program.
    if main.read_text() != program.code:
        raise ValueError(f"Best candidate file differs from native archive: {main}")
    destination = run_dir / "best"
    if destination.exists() and not (destination / "artifacts.json").exists():
        # Preserve historical upstream copies by moving, never copying/deleting.
        retained = run_dir / ("best-before-storage-" + uuid.uuid4().hex)
        destination.rename(retained)
    destination.mkdir(exist_ok=True)
    references = []
    # These files are completed research evidence. Operational logs remain live
    # and are deliberately not represented as immutable checksum references.
    for path in sorted(source.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(source)
        if "__pycache__" in relative.parts or path.name in {"storage-job.json", "evaluation-checkpoint.json"}:
            continue
        if relative.parts[0] == "results" and not (
            path.name in {"metrics.json", "correct.json", "evaluation-checkpoint.json"}
            or re.fullmatch(r"case_\d+\.json(?:\.gz)?", path.name)
        ):
            continue
        references.append({"path": os.path.relpath(path, destination), "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    manifest = {
        "format": "shinka-best-reference-v1", "program_id": program.id,
        "generation": program.generation, "combined_score": program.combined_score,
        "generation_directory": os.path.relpath(source, destination),
        "artifacts": references,
        "main_py": "Independent compatibility copy; authoritative code is in the native archive and generation directory.",
    }
    _atomic_text(destination / "main.py", program.code)
    _atomic_text(destination / "artifacts.json", json.dumps(manifest, indent=2) + "\n")


class _StorageTeeConsole:
    def __init__(self, original, writer):
        self.original = original
        self.writer = writer

    def __getattr__(self, name):
        return getattr(self.original, name)

    def print(self, *objects, **kwargs):
        self.original._console.print(*objects, **kwargs)
        with self.original._lock:
            with self.original._capture_console.capture() as capture:
                self.original._capture_console.print(*objects, **kwargs)
            rendered = capture.get()
            if rendered:
                self.writer.write(rendered if rendered.endswith("\n") else rendered + "\n")
                self.writer.flush()


@contextmanager
def install_native_storage(runner, check_write=None, max_log_bytes=LOG_CHUNK_BYTES, on_error=None):
    """Wire storage sinks into native logging and its real local submit function."""
    from shinka.launch import scheduler, local
    from shinka.launch.local import ProcessWithLogging, _stream_output

    log_path = (Path(runner.results_dir) / "evolution_run.log").resolve()
    writer = EvidenceRotatingWriter(log_path, max_log_bytes, check_write, on_error)
    root_logger = logging.getLogger()
    replaced = []
    for handler in list(root_logger.handlers):
        if isinstance(handler, logging.FileHandler) and Path(handler.baseFilename).resolve() == log_path:
            replacement = logging.StreamHandler(writer)
            replacement.setFormatter(handler.formatter)
            replacement.setLevel(handler.level)
            root_logger.removeHandler(handler)
            handler.close()
            root_logger.addHandler(replacement)
            replaced.append(replacement)
    original_console = runner.console
    runner.console = _StorageTeeConsole(original_console, writer)
    original_submit = scheduler.submit_local
    original_load_results = local.load_results

    def load_results(results_dir):
        results = original_load_results(results_dir)
        for name, key in (("job_log.out", "stdout_log"), ("job_log.err", "stderr_log")):
            results[key] = read_rotated_text(Path(results_dir) / name)
        return results

    local.load_results = load_results
    job_writers = []

    def submit(log_dir, cmd, verbose=False, env_overrides=None):
        # Paths and environment are native inputs; no filesystem tree staging.
        if check_write:
            check_write()
        out = EvidenceRotatingWriter(Path(log_dir) / "job_log.out", max_log_bytes, check_write, on_error)
        err = EvidenceRotatingWriter(Path(log_dir) / "job_log.err", max_log_bytes, check_write, on_error)
        job_writers.extend((out, err))
        env = os.environ.copy()
        env.update({"PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"})
        if env_overrides:
            env.update(env_overrides)
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, env=env)
        except BaseException:
            out.close()
            err.close()
            raise
        threads = tuple(threading.Thread(target=_stream_output, args=(pipe, sink, "STDOUT" if verbose else None), daemon=True)
                        for pipe, sink in ((process.stdout, out), (process.stderr, err)))
        for thread in threads:
            thread.start()
        return ProcessWithLogging(process, (out, err), threads)

    scheduler.submit_local = submit
    try:
        yield
    finally:
        scheduler.submit_local = original_submit
        local.load_results = original_load_results
        runner.console = original_console
        for handler in replaced:
            root_logger.removeHandler(handler)
            handler.close()
        writer.close()
        for sink in job_writers:
            sink.close()


def reconstruct_pending_spec(run_dir, generation):
    """Recover an accepted pre-storage proposal using retained native evidence.

    New storage checkpoints carry the full dataclass instead. This compatibility
    path requires an unambiguous parent, native submission evidence, and archived
    accepted attempt. Missing usage/timing details are labelled, never invented.
    It does not execute a program, sample a parent, or call a model.
    """
    run_dir = Path(run_dir).resolve()
    generation_dir = run_dir / f"gen_{generation}"
    with sqlite3.connect(f"file:{run_dir / 'programs.sqlite'}?mode=ro", uri=True) as database:
        if database.execute("SELECT 1 FROM programs WHERE generation=?", (generation,)).fetchone():
            return None
        programs = {row[0]: row[1] for row in database.execute("SELECT id,code FROM programs")}
    attempts = sorted(generation_dir.glob("attempts/novelty_*/resample_*/patch_*/metadata.json"))
    accepted = [(path, json.loads(path.read_text())) for path in attempts]
    accepted = [(path, data) for path, data in accepted if data.get("success")]
    if len(accepted) != 1:
        raise ValueError(f"Expected one saved accepted attempt for generation {generation}, got {len(accepted)}")
    metadata_path, data = accepted[0]
    log_path = run_dir / "evolution_run.log"
    text = read_rotated_text(log_path)
    marker = f"Generating proposal for generation {generation}\n"
    if text.count(marker) != 1:
        raise ValueError(f"Cannot unambiguously recover generation {generation} sampling log")
    section = text.split(marker, 1)[1]
    submission = re.search(rf"Proposal → Eval: gen {generation} submitted for eval", section)
    acceptance = "native evaluation submission"
    if not submission:
        checkpoints = [run_dir / "storage-stop.json", *run_dir.glob("storage-stop-*.json")]
        interrupted = any(path.exists() and json.loads(path.read_text()).get("status") == "storage_paused" for path in checkpoints)
        manifest = json.loads((run_dir / "manifest.json").read_text())
        storage_config = manifest.get("storage_native_configuration", {})
        if not interrupted or storage_config.get("embedding_model", "unknown") is not None or storage_config.get("novelty_llm_models", "unknown") is not None:
            raise ValueError("Saved proposal lacks native submission or a documented storage pause with novelty disabled")
        acceptance = "saved successful patch before scheduling; storage pause with novelty disabled"
    else:
        section = section[:submission.end()]
    parent_matches = re.findall(r"Sampled parent ([0-9a-f-]{36}) ", section)
    if len(parent_matches) != 1:
        raise ValueError("Saved sampling log does not identify a unique parent")
    parent_id = parent_matches[0]
    if parent_id not in programs or (generation_dir / "original.py").read_text() != programs[parent_id]:
        raise ValueError("Recorded parent and original.py do not match")
    archive = []
    top_k = []
    for line in section.splitlines():
        if "Sampled " in line and " inspirations:" in line:
            ids = re.findall(r"([0-9a-f-]{36}) \(Gen:", line)
            if "archive inspirations:" in line:
                archive.extend(ids)
            elif "top" in line.lower():
                top_k.extend(ids)
    if any(identifier not in programs for identifier in archive + top_k):
        raise ValueError("Recorded inspiration missing from native archive")
    patch_types = re.findall(r"Generated patch type: (\w+)", section)
    if len(patch_types) != 1:
        raise ValueError("Saved sampling log does not identify a unique patch type")
    required = [generation_dir / "main.py", generation_dir / "original.py", metadata_path,
                metadata_path.parent / "llm_response.txt", metadata_path.parent / "headless_prompt.md",
                metadata_path.parent / "patch.txt", log_path]
    evidence = [{"path": str(path.relative_to(run_dir)), "sha256": sha256_file(path)} for path in required]
    patch = (metadata_path.parent / "patch.txt").read_text()
    # The exact wall-clock spans and per-token usage were not durably persisted
    # by this historical runner. Keep evidence, and identify recovery explicitly.
    meta = {"api_costs": data["llm_cost"], "patch_type": patch_types[0],
            "patch_name": data["patch_name"], "patch_description": data["patch_description"],
            "num_applied": data["num_applied"], "error_attempt": data.get("error_msg"),
            "novelty_attempt": data["novelty_attempt"], "resample_attempt": data["resample_attempt"],
            "patch_attempt": data["patch_attempt"], "system_prompt_id": None,
            "model_name": data["llm_model"], "headless_work_dir": str(run_dir),
            "storage_recovery": {"source": "native accepted attempt and sampling log", "evidence": evidence,
                                 "original_token_usage": "not durably recorded", "original_exact_timing": "not durably recorded",
                                 "acceptance_evidence": acceptance, "sampling_log_excerpt": section,
                                 "accepted_attempt_timestamp": data.get("timestamp")}}
    now = time.time()
    return {"exec_fname": str(generation_dir / "main.py"), "results_dir": str(generation_dir / "results"),
            "start_time": now, "proposal_started_at": now, "evaluation_submitted_at": now,
            "generation": generation, "parent_id": parent_id, "archive_insp_ids": archive,
            "top_k_insp_ids": top_k, "code_diff": patch, "meta_patch_data": meta,
            "code_embedding": None, "embed_cost": 0.0, "novelty_cost": 0.0,
            "proposal_task_id": f"recovered_generation_{generation}"}


def recover_pending_spec(generation_folder, db=None):
    """Load a full new checkpoint, or reconstruct accepted legacy evidence.

    ``db`` is accepted for the runner hook; an independent read-only connection
    checks completed generations to avoid duplicate native archive work.
    """
    folder = Path(generation_folder).resolve()
    generation = int(folder.name.removeprefix("gen_"))
    database_path = folder.parent / "programs.sqlite"
    with sqlite3.connect(f"file:{database_path}?mode=ro", uri=True) as database:
        if database.execute("SELECT 1 FROM programs WHERE generation=?", (generation,)).fetchone():
            return None
    checkpoint = folder / "storage-job.json"
    if checkpoint.exists():
        record = json.loads(checkpoint.read_text())
        if "job" in record:
            record = record["job"]
        record.pop("job_id", None)
        if record.get("generation") != generation:
            raise ValueError(f"Pending checkpoint generation differs: {checkpoint}")
        if Path(record["exec_fname"]).resolve() != folder / "main.py":
            raise ValueError(f"Pending checkpoint candidate path differs: {checkpoint}")
        return record
    accepted = [path for path in folder.glob("attempts/novelty_*/resample_*/patch_*/metadata.json")
                if json.loads(path.read_text()).get("success")]
    if not accepted:
        return None
    return reconstruct_pending_spec(folder.parent, generation)
