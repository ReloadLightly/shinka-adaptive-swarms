#!/usr/bin/env python3
"""Run native ShinkaEvolve with visible phases and subscription-backed Codex."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import signal
import shutil
import sqlite3
import sys
import threading
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from adaptive_swarms.logging import EventLogger
from check_runtime import HEADLESS_COMMAND, PINNED_SHINKA, inspect_runtime

EVALUATION_VERSION = "search_v1_score_reciprocal"


TASK_PROMPT = """You are evolving an interpretable response policy for dynamic
multiswarm particle swarm optimization, based on Blackwell's chapter in Swarm
Intelligence: Introduction and Applications and the DEAP multiswarm example.
The fixed simulator performs PSO, exclusion, swarm birth/death, change detection,
and Moving Peaks objective evaluations. Change only the marked evolve block.
Evolve choose_response(observation), using optimizer-visible observations to
select relocation radius_scale, fraction, memory (reevaluate or reset), and
reset_velocity. Baseline relocates all particles around the previous swarm best
with radius 0.5 times benchmark movement severity, retaining velocities and
reevaluating memories. Discover an adaptive, comprehensible rule that tracks
changing peaks better under the same objective-evaluation budget. Lower mean
offline error is better; combined_score=1/(1+mean_offline_error). Use feedback across
cases to reason about when relocation helps and when it destroys useful memory.
Do not import the simulator, read task/results files or hidden landscape state,
access the network, invoke other models, change random seeds, or alter evaluator
behavior. The result must be a reusable policy, not case-specific answers.
Explain the behavioral hypothesis of the proposed change in the patch description.
"""


@contextlib.contextmanager
def exclusive_controller(results_root: Path):
    """A process lock disappears on exit; existing run artifacts are preserved."""
    import fcntl

    results_root.mkdir(parents=True, exist_ok=True)
    with (results_root / ".controller.lock").open("a+") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError(f"Another evolution controller owns {results_root}. Inspect its live log before launching another.") from exc
        lock.seek(0)
        lock.truncate()
        lock.write(str(os.getpid()))
        lock.flush()
        try:
            yield
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def relay_evaluator_events(run_dir: Path, log, stop: threading.Event, resuming=False):
    """Relay native evaluator child progress while Shinka captures child stdout."""
    offsets = {str(path): path.stat().st_size for path in run_dir.glob("gen_*/results/events.jsonl")} if resuming else {}
    while not stop.wait(1):
        for path in run_dir.glob("gen_*/results/events.jsonl"):
            try:
                with path.open() as stream:
                    stream.seek(offsets.get(str(path), 0))
                    while True:
                        offset = stream.tell()
                        line = stream.readline()
                        if not line or not line.endswith("\n"):
                            stream.seek(offset)
                            break
                        event = json.loads(line)
                        phase = event.pop("phase", event.pop("event", "evaluation_progress"))
                        message = event.pop("message", str(phase))
                        for key in ("time", "timestamp", "elapsed_seconds", "elapsed_s", "pid"):
                            event.pop(key, None)
                        log.set_activity(f"{path.parents[1].name}: {message}")
                        log.event(str(phase), message=f"{path.parents[1].name}: {message}", **event)
                    offsets[str(path)] = stream.tell()
            except (OSError, ValueError):
                continue


def summarize_database(run_dir: Path) -> dict:
    database = run_dir / "programs.sqlite"
    if not database.exists():
        return {"generation_records": 0, "valid_programs": 0, "valid_descendants": 0}
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
        rows = connection.execute("SELECT generation, correct, combined_score, metadata FROM programs").fetchall()
    # Native island copies must not count as new proposals or evaluations.
    originals = []
    for row in rows:
        metadata = json.loads(row[3] or "{}")
        if metadata.get("_is_island_copy") or metadata.get("is_island_copy") or metadata.get("island_copy"):
            continue
        originals.append(row)
    valid = [row for row in originals if row[1]]
    return {
        "generation_records": len({row[0] for row in originals}),
        "valid_programs": len(valid),
        "valid_descendants": sum(row[0] > 0 for row in valid),
        "best_combined_score": max((row[2] for row in valid), default=None),
        "database": str(database),
    }


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_snapshot(args, run_dir: Path) -> dict:
    """Freeze the evaluator and literature context; preserve simulator provenance."""
    destination = run_dir / "task_snapshot"
    source_record = destination / "source_hashes.json"
    if source_record.exists():
        hashes = json.loads(source_record.read_text())
        for name in ("simulator.py", "policies.py"):
            if file_hash(ROOT / "src/adaptive_swarms" / name) != hashes[name]:
                raise RuntimeError(f"Cannot resume with changed {name}; retain the recorded implementation or start a new run for the revised method.")
        if "movingpeaks.py" in hashes and file_hash(ROOT / "vendor/deap/movingpeaks.py") != hashes["movingpeaks.py"]:
            raise RuntimeError("Cannot resume with a changed Moving Peaks implementation.")
        for name in ("evaluate.py", "initial.py"):
            if file_hash(destination / name) != hashes[name]:
                raise RuntimeError(f"Saved task snapshot changed: {name}.")
        if "evolution_context.md" in hashes and file_hash(destination / "evolution_context.md") != hashes["evolution_context.md"]:
            raise RuntimeError("Saved scientific context snapshot changed.")
        return hashes
    destination.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name in ("evaluate.py", "initial.py"):
        source = ROOT / "tasks/adaptive_swarm" / name
        # Legacy seed-only runs already contain the exact initial program.
        if args.resume and name == "initial.py" and (run_dir / "gen_0/main.py").exists():
            source = run_dir / "gen_0/main.py"
        shutil.copyfile(source, destination / name)
        hashes[name] = file_hash(source)
    for name in ("simulator.py", "policies.py"):
        hashes[name] = file_hash(ROOT / "src/adaptive_swarms" / name)
    hashes["movingpeaks.py"] = file_hash(ROOT / "vendor/deap/movingpeaks.py")
    context = ROOT / "docs/evolution_context.md"
    if context.exists():
        shutil.copyfile(context, destination / "evolution_context.md")
        hashes["evolution_context.md"] = file_hash(context)
    hashes["snapshot_created_at"] = datetime.now(timezone.utc).isoformat()
    hashes["snapshot_created_on_resume"] = bool(args.resume)
    source_record.write_text(json.dumps(hashes, indent=2))
    return hashes


def run_native(args, run_dir: Path, log):
    from shinka.core import EvolutionConfig, ShinkaEvolveRunner
    from shinka.database import DatabaseConfig
    from shinka.launch import LocalJobConfig
    # Upstream imports may load a local .env. The only model route below remains
    # Headless/Codex; remove API authentication variables again before spawning it.
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("CODEX_API_KEY", None)

    class VisibleRunner(ShinkaEvolveRunner):
        # These wrappers add observability only; upstream owns search and persistence.
        async def _setup_initial_program(self, code):
            if args.resume and await self.async_db.get_total_program_count_async() > 0:
                # Pinned upstream recognizes resumes only at last_iteration > 0.
                # Restore native counters for an existing generation-0 seed too.
                await self._restore_resume_progress()
                log.event("seed_reused", message="Existing native seed retained without another evaluation", completed_generations=self.completed_generations)
                return
            log.set_activity("native seed evaluation")
            log.event("seed_evaluation", message="Native Shinka is evaluating the initial response program")
            await super()._setup_initial_program(code)
            log.event("seed_evaluated", message="Native seed evaluation returned; results stored in programs.sqlite")

        async def _generate_proposal_async(self, generation, task_id):
            log.set_activity(f"generation {generation}: parent sampling and Codex proposal")
            log.event("proposal_start", message=f"Generation {generation}: native parent/inspiration sampling and mutation", generation=generation)
            result = await super()._generate_proposal_async(generation, task_id)
            log.event("proposal_returned", message=f"Generation {generation}: proposal stage returned", generation=generation)
            return result

        async def _record_attempt_event(self, generation, stage, status, details=None):
            log.set_activity(f"generation {generation}: {stage} {status}")
            log.event("native_attempt", message=f"Generation {generation}: {stage} {status}", generation=generation, stage=stage, status=status)
            await super()._record_attempt_event(generation, stage, status, details)

        async def _record_generation_event(self, generation, status, source_job_id=None, details=None):
            log.set_activity(f"generation {generation}: {status}")
            log.event("native_generation", message=f"Generation {generation}: {status}", generation=generation, status=status)
            await super()._record_generation_event(generation, status, source_job_id, details)

    route = f"headless/codex@{args.model}" + (f"?effort={args.effort}" if args.effort else "")
    suite_snapshot = run_dir / "search-suite.json"
    if not suite_snapshot.exists():
        suite_snapshot.write_bytes(args.suite.read_bytes())
    task_snapshot = run_dir / "task_snapshot"
    context_path = task_snapshot / "evolution_context.md"
    context = context_path.read_text() if context_path.exists() else ""
    task_prompt = TASK_PROMPT + ("\n\n# Scientific context supplied to mutation\n\n" + context if context else "")
    # This file is the actual task system message, before native parent/feedback composition.
    prompt_snapshot = task_snapshot / "task_system_prompt.txt"
    if prompt_snapshot.exists():
        task_prompt = prompt_snapshot.read_text()
    else:
        prompt_snapshot.write_text(task_prompt)
    model_pool = [] if args.seed_only else [route]
    evo = EvolutionConfig(
        task_sys_msg=task_prompt,
        init_program_path=str(task_snapshot / "initial.py"),
        results_dir=str(run_dir),
        num_generations=1 if args.seed_only else args.generations,
        llm_models=model_pool,
        llm_dynamic_selection=None if args.seed_only else "fixed",
        llm_kwargs={"temperatures": [0.0], "max_tokens": 16384},
        patch_types=["diff", "full", "cross"],
        patch_type_probs=[0.5, 0.3, 0.2],
        max_patch_resamples=1,
        max_patch_attempts=1,
        max_novelty_attempts=1,
        embedding_model=None,
        novelty_llm_models=None,
        meta_rec_interval=None,
        meta_llm_models=None,
        evolve_prompts=False,
        use_text_feedback=True,
        enable_wandb_logging=False,
    )
    runner = VisibleRunner(
        evo_config=evo,
        db_config=DatabaseConfig(num_islands=2, archive_size=40, num_archive_inspirations=1, num_top_k_inspirations=1),
        job_config=LocalJobConfig(eval_program_path=str(task_snapshot / "evaluate.py"), extra_cmd_args={"suite": str(suite_snapshot)}, time=args.evaluation_timeout),
        max_evaluation_jobs=1,
        max_proposal_jobs=1,
        max_db_workers=1,
        verbose=True,
    )
    runner.run()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generations", type=int, default=20, help="Native target generation count including the initial generation 0")
    parser.add_argument("--seed-only", action="store_true", help="Native generation 0 evaluation/archive only; zero model calls")
    parser.add_argument("--model", default="gpt-6-astra")
    parser.add_argument("--effort", default=None, help="Explicit inner Codex effort; distinct from outer Ultra mode")
    parser.add_argument("--suite", type=Path, default=None, help="Defaults to configs/search.json, or the saved suite when resuming")
    parser.add_argument("--results-root", type=Path, default=ROOT / "results/evolution")
    parser.add_argument("--resume", type=Path, help="Resume an existing native run directory, preserving completed records")
    parser.add_argument("--heartbeat-seconds", type=float, default=20)
    parser.add_argument("--evaluation-timeout", default="01:00:00", help="Native per-candidate evaluator timeout HH:MM:SS")
    parser.add_argument("--proposal-timeout-seconds", type=float, default=3600)
    args = parser.parse_args()
    if args.generations < 1 or args.heartbeat_seconds <= 0 or args.proposal_timeout_seconds <= 0:
        parser.error("Generation count and timeout/heartbeat values must be positive.")
    args.results_root = args.results_root.resolve()
    if args.resume:
        args.resume = args.resume.resolve()
        args.results_root = args.resume.parent
        if not (args.resume / "manifest.json").is_file() or not (args.resume / "programs.sqlite").is_file():
            parser.error("--resume requires a native run with manifest.json and programs.sqlite.")
    args.suite = (args.suite or (args.resume / "search-suite.json" if args.resume else ROOT / "configs/search.json")).resolve()
    if not args.suite.is_file():
        parser.error(f"Evaluation suite does not exist: {args.suite}")
    os.environ["PYTHONUNBUFFERED"] = "1"
    os.environ.setdefault("SHINKA_HEADLESS_COMMAND", HEADLESS_COMMAND)
    os.environ.setdefault("SHINKA_PRICING_MODE", "offline")
    os.environ["SHINKA_HEADLESS_TIMEOUT"] = str(args.proposal_timeout_seconds)
    # Explicit subscription route and authentication check avoid API-key fallback.
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("CODEX_API_KEY", None)
    os.environ["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")
    os.environ["ADAPTIVE_SWARMS_PROJECT_ROOT"] = str(ROOT)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    run_dir = args.resume or (args.results_root / (stamp + ("-seed" if args.seed_only else "-search")))
    target = 1 if args.seed_only else args.generations
    try:
        with exclusive_controller(args.results_root), EventLogger(run_dir, heartbeat_seconds=args.heartbeat_seconds) as log:
            log.set_activity("checking native runtime and subscription route")
            report = inspect_runtime(args.model, args.effort, args.seed_only)
            if args.resume:
                manifest = json.loads((run_dir / "manifest.json").read_text())
                if manifest.get("evaluation_version") != EVALUATION_VERSION:
                    raise RuntimeError("Evaluation version differs from this run. Use a new run for a revised scoring method.")
                if manifest.get("suite_sha256") != file_hash(args.suite) or manifest.get("suite_sha256") != file_hash(run_dir / "search-suite.json"):
                    raise RuntimeError("Evaluation suite differs from the saved run; pass --suite with the saved search-suite.json or start a new study.")
                active = {**report, "started_at": stamp, "generation_target": target, "previous_status": manifest.get("status"), "status": "preflight"}
                manifest.setdefault("resume_attempts", []).append(active)
            else:
                manifest = {**report, "upstream_commit": PINNED_SHINKA, "evaluation_version": EVALUATION_VERSION, "generation_target": target,
                        "started_at": stamp, "suite_sha256": hashlib.sha256(args.suite.read_bytes()).hexdigest(),
                        "status": "preflight", "run_dir": str(run_dir)}
                active = manifest
            hashes = prepare_snapshot(args, run_dir)
            if "source_hashes" not in manifest:
                manifest["source_hashes"] = hashes
            active["source_hashes"] = hashes
            (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
            log.event("configuration", message="Declared native run configuration", model=args.model, inner_effort=args.effort,
                      effective_effort="unverified until Codex invocation", generation_target=target, seed_only=args.seed_only, resuming=bool(args.resume))
            if not report["ready"]:
                active["status"] = "blocked_runtime"
                (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
                for error in report["errors"]:
                    log.event("runtime_error", message=error)
                return 2
            log.event("runtime_ready", message="Runtime check passed; starting native ShinkaEvolve", results=str(run_dir))
            stop = threading.Event()
            monitor = threading.Thread(target=relay_evaluator_events, args=(run_dir, log, stop, bool(args.resume)), daemon=True)
            monitor.start()
            def interrupted(signum, frame):
                raise KeyboardInterrupt
            previous_term = signal.signal(signal.SIGTERM, interrupted)
            try:
                run_native(args, run_dir, log)
                summary = summarize_database(run_dir)
                expected = target
                if summary["generation_records"] < expected or not summary["valid_programs"]:
                    raise RuntimeError(f"Native run did not finish the requested valid seed and generation records: {summary}")
                active.update({"status": "seed_complete" if args.seed_only else "search_complete", **summary})
                if args.resume:
                    manifest.update({"status": active["status"], "latest_summary": summary})
                log.event("run_complete", message="Native seed evaluation complete; no mutation calls" if args.seed_only else "Native search complete; inspect scientific outcomes and descendants", **summary)
                return 0
            except KeyboardInterrupt:
                active["status"] = "interrupted"
                manifest["status"] = "interrupted"
                log.event("interrupted", message="Run interrupted; completed native records are retained")
                return 130
            except Exception as exc:
                active.update({"status": "failed", "error": f"{type(exc).__name__}: {exc}"})
                manifest["status"] = "failed"
                error_path = run_dir / (f"resume-error-{stamp}.txt" if args.resume else "error.txt")
                error_path.write_text(traceback.format_exc())
                log.event("run_failed", message=active["error"])
                return 1
            finally:
                signal.signal(signal.SIGTERM, previous_term)
                stop.set()
                monitor.join(timeout=3)
                if active.get("status") in {"interrupted", "failed"}:
                    import psutil
                    children = psutil.Process().children(recursive=True)
                    for child in children:
                        with contextlib.suppress(psutil.NoSuchProcess):
                            child.terminate()
                    _, alive = psutil.wait_procs(children, timeout=3)
                    for child in alive:
                        with contextlib.suppress(psutil.NoSuchProcess):
                            child.kill()
                active["finished_at"] = datetime.now(timezone.utc).isoformat()
                (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    except (OSError, RuntimeError) as exc:
        print(f"Cannot start evolution: {exc}", file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
