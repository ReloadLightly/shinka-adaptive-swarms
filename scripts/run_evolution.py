#!/usr/bin/env python3
"""Run native ShinkaEvolve with visible phases and subscription-backed Codex."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
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
from adaptive_swarms.logging import EventLogger, atomic_json
from adaptive_swarms.execution import InfrastructureError, INFRASTRUCTURE_EXIT_CODE
from adaptive_swarms.storage_runner import ResumeRunnerMixin
from adaptive_swarms.campaign_resume import CampaignResumeRunnerMixin, reuse_existing_native_seed
from adaptive_swarms.engine_config import resolve_engine, native_settings, feature_state, check_embedding_endpoint
from adaptive_swarms.engine_runtime import install_engine_observers, install_sampling_observer
from adaptive_swarms.engine_progress import terminal_failure_generations
from adaptive_swarms.sprint_budget import SprintLimitReached
from check_runtime import HEADLESS_COMMAND, PINNED_SHINKA, inspect_runtime

EVALUATION_VERSION = "search_v1_score_reciprocal"
TASK_VERSIONS = {
    "adaptive_swarm": EVALUATION_VERSION,
    "relocation_allocation_v2": "relocation_allocation_v2_score_reciprocal",
    "joint_relocation_v3": "joint_relocation_v3_score_reciprocal",
    "radius_velocity_sprint": "fixed_four_radius_velocity_sprint_score_reciprocal_v1",
    "particle_retention_v1": "particle_retention_v1_reciprocal_v1",
    "book_mpso_schedule_v1": "book_mpso_schedule_v1_reciprocal_v1",
    "book_mpso_population_v1": "book_mpso_population_v1_reciprocal_v1",
    "book_mpso_population_200_v1": "book_mpso_population_200_v1_reciprocal_v1",
    "book_mpso_population_200_v2": "book_mpso_population_200_v2_reciprocal_v1",
}
TASK_ADAPTERS = {"relocation_allocation_v2": "relocation_allocation.py", "joint_relocation_v3": "joint_relocation.py", "radius_velocity_sprint": "recovery_response.py", "particle_retention_v1": "particle_retention.py", "book_mpso_schedule_v1": "book_schedule.py", "book_mpso_population_v1": "population_policy.py", "book_mpso_population_200_v1": "population_policy.py", "book_mpso_population_200_v2": "population_policy_v2.py"}
TASK_PROTOCOLS = {"relocation_allocation_v2": "followup_relocation_allocation_v2.md", "joint_relocation_v3": "followup_joint_relocation_v3.md", "radius_velocity_sprint": "radius_velocity_sprint_protocol.md", "particle_retention_v1": "particle_retention_v1_protocol.md", "book_mpso_schedule_v1": "book_mpso_schedule_v1_protocol.md", "book_mpso_population_v1": "book_mpso_population_v1_protocol.md", "book_mpso_population_200_v1": "book_mpso_population_200_v1_protocol.md", "book_mpso_population_200_v2": "book_mpso_population_200_v2_protocol.md"}


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
        return {"generation_records": 0, "valid_programs": 0, "valid_descendants": 0,
                "terminal_generation_ids": sorted(terminal_failure_generations(run_dir)), "valid_seed": False}
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
        rows = connection.execute("SELECT generation, correct, combined_score, metadata FROM programs").fetchall()
        terminal_failures = terminal_failure_generations(run_dir, connection)
    # Native island copies must not count as new proposals or evaluations.
    originals = []
    for row in rows:
        metadata = json.loads(row[3] or "{}")
        if metadata.get("_is_island_copy") or metadata.get("is_island_copy") or metadata.get("island_copy"):
            continue
        originals.append(row)
    valid = [row for row in originals if row[1]]
    evaluated = {row[0] for row in originals}
    failed_without_evaluation = terminal_failures - evaluated
    return {
        "generation_records": len(evaluated),
        "evaluated_programs": len(originals),
        "evaluated_generation_ids": sorted(evaluated),
        "terminal_failed_generation_ids": sorted(failed_without_evaluation),
        "terminal_generation_ids": sorted(evaluated | terminal_failures),
        "terminal_slots": len(evaluated | terminal_failures),
        "valid_seed": any(row[0] == 0 for row in valid),
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
    task = getattr(args, "task", None) or "adaptive_swarm"
    task_source = ROOT / "tasks" / task
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
        if task != "adaptive_swarm":
            for name in (TASK_ADAPTERS[task], *(("book_population_v2.py", "book_population.py", "book_mpso.py", "enclosing_ball.py", "population_policy.py") if task == "book_mpso_population_200_v2" else ("book_mpso.py",) if task == "book_mpso_schedule_v1" else ("book_population.py", "book_mpso.py") if task in {"book_mpso_population_v1", "book_mpso_population_200_v1"} else ())):
                if file_hash(ROOT / "src/adaptive_swarms" / name) != hashes[name]:
                    raise RuntimeError(f"Cannot resume with changed task adapter: {name}.")
                if file_hash(destination / name) != hashes[name]:
                    raise RuntimeError(f"Saved task adapter snapshot changed: {name}.")
            for name in ("task_prompt.txt", "task_system_prompt.txt", "protocol.md"):
                if file_hash(destination / name) != hashes[name]:
                    raise RuntimeError(f"Saved task context changed: {name}.")
        return hashes
    destination.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name in ("evaluate.py", "initial.py"):
        source = task_source / name
        # Legacy seed-only runs already contain the exact initial program.
        if args.resume and name == "initial.py" and (run_dir / "gen_0/main.py").exists():
            source = run_dir / "gen_0/main.py"
        shutil.copyfile(source, destination / name)
        hashes[name] = file_hash(source)
    for name in ("simulator.py", "policies.py"):
        hashes[name] = file_hash(ROOT / "src/adaptive_swarms" / name)
    hashes["movingpeaks.py"] = file_hash(ROOT / "vendor/deap/movingpeaks.py")
    context = ROOT / "docs/evolution_context.md" if task == "adaptive_swarm" else task_source / "context.md"
    if context.exists():
        shutil.copyfile(context, destination / "evolution_context.md")
        hashes["evolution_context.md"] = file_hash(context)
    if task != "adaptive_swarm":
        for source, name in ((ROOT / "src/adaptive_swarms" / TASK_ADAPTERS[task], TASK_ADAPTERS[task]),
                             (task_source / "task_prompt.txt", "task_prompt.txt"),
                             (ROOT / "docs" / TASK_PROTOCOLS[task], "protocol.md")):
            shutil.copyfile(source, destination / name)
            hashes[name] = file_hash(source)
        if task in {"book_mpso_schedule_v1", "book_mpso_population_v1", "book_mpso_population_200_v1"}:
            source = ROOT / "src/adaptive_swarms" / ("book_mpso.py" if task == "book_mpso_schedule_v1" else "book_population.py")
            shutil.copyfile(source, destination / source.name)
            hashes[source.name] = file_hash(source)
            if task in {"book_mpso_population_v1", "book_mpso_population_200_v1"}:
                source = ROOT / "src/adaptive_swarms/book_mpso.py"
                shutil.copyfile(source, destination / source.name)
                hashes[source.name] = file_hash(source)
        if task == "book_mpso_population_200_v2":
            for name in ("book_population_v2.py", "book_population.py", "book_mpso.py", "enclosing_ball.py", "population_policy.py"):
                source = ROOT / "src/adaptive_swarms" / name
                shutil.copyfile(source, destination / name)
                hashes[name] = file_hash(source)
        prompt = (destination / "task_prompt.txt").read_text()
        prompt += "\n\n# Scientific context supplied to mutation\n\n" + (destination / "evolution_context.md").read_text()
        (destination / "task_system_prompt.txt").write_text(prompt)
        hashes["task_system_prompt.txt"] = file_hash(destination / "task_system_prompt.txt")
    hashes["snapshot_created_at"] = datetime.now(timezone.utc).isoformat()
    hashes["snapshot_created_on_resume"] = bool(args.resume)
    source_record.write_text(json.dumps(hashes, indent=2))
    return hashes


def prepare_storage_evaluator(run_dir: Path) -> Path:
    """Record a compatible evaluator while preserving the frozen research source.

    The historical directory and provenance key names remain readable; each
    adapter gets its own hash, so prior executable snapshots are never replaced.
    """
    import ast
    original = run_dir / "task_snapshot/evaluate.py"
    manifest_path = run_dir / "manifest.json"
    task = json.loads(manifest_path.read_text()).get("task", "adaptive_swarm") if manifest_path.exists() else "adaptive_swarm"
    if task != "adaptive_swarm":
        # New task executes its exact frozen evaluator. Legacy compatibility
        # adaptations below apply only to the historical v1 evaluator.
        hashes = json.loads((run_dir / "task_snapshot/source_hashes.json").read_text())
        if file_hash(original) != hashes["evaluate.py"]:
            raise RuntimeError(f"Saved {task} evaluator changed.")
        return original
    current = ROOT / "tasks/adaptive_swarm/evaluate.py"
    def scientific_nodes(path):
        tree = ast.parse(path.read_text())
        return {node.name: ast.dump(node, include_attributes=False) for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name in {
                    "load_policy", "load_cases", "case_diagnostics", "describe_case"}}
    if scientific_nodes(original) != scientific_nodes(current):
        raise RuntimeError("Compatibility evaluator changes scientific policy loading or feedback helpers.")
    digest = file_hash(current)
    support_sources = {p.name: file_hash(p) for p in (ROOT / "src/adaptive_swarms").glob("*.py")}
    bundle = {"evaluator": digest, "launcher": file_hash(Path(__file__)), "support_sources": support_sources}
    bundle_digest = hashlib.sha256(json.dumps(bundle, sort_keys=True).encode()).hexdigest()
    folder = run_dir / "storage_runtime" / bundle_digest[:16]
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / "evaluate.py"
    if not destination.exists():
        shutil.copyfile(current, destination)
    elif file_hash(destination) != digest:
        raise RuntimeError("Recorded compatibility evaluator adapter has changed.")
    atomic_json(folder / "provenance.json", {
        "frozen_evaluator_sha256": file_hash(original), "storage_evaluator_sha256": digest,
        "evaluation_version": EVALUATION_VERSION,
        "scope": "Lossless case serialization and checkpoint reuse; actual I/O failures remain operational; fixed simulator and scientific feedback helpers retained; no free-space execution rules",
        "launcher_sha256": bundle["launcher"], "support_sources": support_sources,
    })
    # Native initialization can refresh this file even when the catalog is the
    # same. Retain its incoming bytes independently before handing control back.
    pricing = run_dir / "pricing_snapshot.json"
    if pricing.exists():
        saved_pricing = folder / ("pricing-before-resume-" + file_hash(pricing) + ".json")
        if not saved_pricing.exists():
            shutil.copyfile(pricing, saved_pricing)
    return destination


def run_native(args, run_dir: Path, log):
    from shinka.core import EvolutionConfig, ShinkaEvolveRunner
    from shinka.database import DatabaseConfig
    from shinka.launch import LocalJobConfig
    from adaptive_swarms.native_storage import NativeStorageMixin, install_native_storage
    # Upstream imports may load a local .env. The only model route below remains
    # Headless/Codex; remove API authentication variables again before spawning it.
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("CODEX_API_KEY", None)
    os.environ.pop("ADAPTIVE_SWARMS_STORAGE_CONFIG", None)

    class VisibleRunner(CampaignResumeRunnerMixin, ResumeRunnerMixin, NativeStorageMixin, ShinkaEvolveRunner):
        # These wrappers add observability only; upstream owns search and persistence.
        async def _setup_async(self):
            await super()._setup_async()
            install_sampling_observer(self, log)

        async def _setup_initial_program(self, code):
            if await reuse_existing_native_seed(self, resuming=bool(args.resume), log=log):
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
            log.event("native_attempt", message=f"Generation {generation}: {stage} {status}", generation=generation, stage=stage, status=status, details=details)
            await super()._record_attempt_event(generation, stage, status, details)

        async def _record_generation_event(self, generation, status, source_job_id=None, details=None):
            log.set_activity(f"generation {generation}: {status}")
            log.event("native_generation", message=f"Generation {generation}: {status}", generation=generation, status=status, details=details)
            await super()._record_generation_event(generation, status, source_job_id, details)

    suite_snapshot = run_dir / "search-suite.json"
    if not suite_snapshot.exists():
        suite_snapshot.write_bytes(args.suite.read_bytes())
    task_snapshot = run_dir / "task_snapshot"
    context_path = task_snapshot / "evolution_context.md"
    context = context_path.read_text() if context_path.exists() else ""
    task_base = (task_snapshot / "task_prompt.txt").read_text() if (task_snapshot / "task_prompt.txt").exists() else TASK_PROMPT
    task_prompt = task_base + ("\n\n# Scientific context supplied to mutation\n\n" + context if context else "")
    # This file is the actual task system message, before native parent/feedback composition.
    prompt_snapshot = task_snapshot / "task_system_prompt.txt"
    if prompt_snapshot.exists():
        task_prompt = prompt_snapshot.read_text()
    else:
        prompt_snapshot.write_text(task_prompt)
    evolution_settings, database_settings = native_settings(args.engine_config, seed_only=args.seed_only)
    evo = EvolutionConfig(
        task_sys_msg=task_prompt,
        init_program_path=str(task_snapshot / "initial.py"),
        results_dir=str(run_dir),
        num_generations=1 if args.seed_only else (args.session_generation_target if args.session_max_descendants is not None else args.generations),
        **evolution_settings,
    )
    database = DatabaseConfig(**database_settings)
    from dataclasses import asdict
    # Native defaults are recorded too, including any settings not overridden by
    # this profile. Task prompts already have their own immutable snapshot.
    resolved_native = {"evolution": asdict(evo), "database": asdict(database)}
    resolved_native["evolution"].pop("task_sys_msg", None)
    config_path = run_dir / ("native-config-resume-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ") + ".json" if args.resume else "native-config.json")
    atomic_json(config_path, resolved_native)
    runner = VisibleRunner(
        evo_config=evo,
        db_config=database,
        job_config=LocalJobConfig(eval_program_path=str(prepare_storage_evaluator(run_dir)), extra_cmd_args={"suite": str(suite_snapshot)}, time=args.evaluation_timeout),
        max_evaluation_jobs=1,
        max_proposal_jobs=1,
        max_db_workers=1,
        verbose=True,
    )
    runner.configure_resume(log)
    if args.session_max_descendants is not None:
        runner.configure_campaign(campaign_generations=args.generations, log=log,
            deadline_utc=args.session_deadline_utc, admission_seconds=args.admission_seconds,
            response_reserve=args.session_response_reserve, admission_overhead_seconds=args.admission_overhead_seconds)
    remove_observers = install_engine_observers(runner, log, run_dir, logical_response_limit=args.logical_response_limit,
        session_response_limit=args.session_response_limit, session_response_start=args.session_response_start)
    log.event("engine_initialized", message="Native engine components initialized; subsequent events establish actual use",
              meta_created=runner.meta_summarizer is not None, novelty_created=runner.novelty_judge is not None,
              embedding_created=runner.embedding_client is not None, resolved_native_config=str(config_path))
    log.on_io_error = runner._fail_infrastructure
    try:
        with install_native_storage(runner):
            runner.run()
            return {"effective_session_generation_target": runner.evo_config.num_generations,
                    "campaign_pause_reason": getattr(runner, "_campaign_pause_reason", None),
                    "resume_rng_state_restored": bool(getattr(runner, "_campaign_rng_restored", False))}
    finally:
        log.on_io_error = None
        remove_observers()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=list(TASK_VERSIONS), default=None,
                        help="Task interface; inferred from saved manifest on resume, otherwise adaptive_swarm")
    parser.add_argument("--generations", type=int, default=20, help="Native target generation count including the initial generation 0")
    parser.add_argument("--seed-only", action="store_true", help="Native generation 0 evaluation/archive only; zero model calls")
    parser.add_argument("--model", default=None, help="Inner Codex model; defaults to gpt-6-astra, or the recorded value on resume")
    parser.add_argument("--effort", default=None, help="Explicit inner Codex effort; distinct from outer Ultra mode")
    parser.add_argument("--engine-profile", type=Path, help="Explicit native machinery profile; historical settings remain the default")
    parser.add_argument("--embedding-model", help="Served local embedding route: local/<model>@http://127.0.0.1:<port>/v1")
    parser.add_argument("--print-engine-config", action="store_true", help="Print resolved task and model roles, then exit without model calls or run creation")
    parser.add_argument("--search-seed", type=int, default=None, help="Seed Python/NumPy native search sampling on a new run; resume retains provenance without reseeding")
    parser.add_argument("--suite", type=Path, default=None, help="Defaults to configs/search.json, or the saved suite when resuming")
    parser.add_argument("--results-root", type=Path, default=None)
    destinations = parser.add_mutually_exclusive_group()
    destinations.add_argument("--resume", type=Path, help="Resume an existing native run directory, preserving completed records")
    destinations.add_argument("--run-dir", type=Path, help="Predeclared new run identity; must be absent or empty. Use --resume for saved work.")
    parser.add_argument("--heartbeat-seconds", type=float, default=20)
    parser.add_argument("--evaluation-timeout", default="01:00:00", help="Native per-candidate evaluator timeout HH:MM:SS")
    parser.add_argument("--proposal-timeout-seconds", type=float, default=3600)
    parser.add_argument("--logical-response-limit", type=int, default=None,
                        help="Optional run-local allowance including exposed native retries and batched meta responses; inherited unchanged on resume")
    parser.add_argument("--session-max-descendants", type=int, default=None,
                        help="Opt into resumable campaign mode; --generations remains the immutable campaign total including seed")
    parser.add_argument("--session-stop-generation", type=int, default=None,
                        help="Optional cumulative session terminal-slot target including seed; cannot exceed session or campaign ceilings")
    parser.add_argument("--session-response-limit", type=int, default=None)
    parser.add_argument("--session-response-start", type=int, default=None,
                        help="Receipt count at the outer user session start; retain across recovery launches")
    parser.add_argument("--session-response-reserve", type=int, default=12,
                        help="Do not admit a proposal with fewer unreserved responses than this")
    parser.add_argument("--session-deadline-utc", default=None,
                        help="ISO UTC research cutoff; provider waits and new-work admission respect it")
    parser.add_argument("--admission-seconds", type=float, default=0,
                        help="Conservative time required for mutation, full paired evaluation, meta and checkpoint")
    parser.add_argument("--admission-overhead-seconds", type=float, default=None,
                        help="Optional measured mutation/meta/checkpoint allowance; raises admission to 1.35 times max complete evaluator duration plus this overhead")
    args = parser.parse_args()
    if args.generations < 1 or args.heartbeat_seconds <= 0 or args.proposal_timeout_seconds <= 0:
        parser.error("Generation count and timeout/heartbeat values must be positive.")
    if args.search_seed is not None and not 0 <= args.search_seed < 2**32:
        parser.error("--search-seed must be an integer from 0 through 2**32 - 1.")
    if args.logical_response_limit is not None and args.logical_response_limit < 1:
        parser.error("--logical-response-limit must be positive.")
    if args.admission_overhead_seconds is not None and (args.admission_overhead_seconds < 0 or not math.isfinite(args.admission_overhead_seconds)):
        parser.error("Admission overhead must be a finite nonnegative number.")
    if args.session_max_descendants is not None and not 1 <= args.session_max_descendants <= 6:
        parser.error("Session descendant ceiling must be from one through six.")
    if args.session_response_limit is not None and (args.session_response_limit < 1 or args.logical_response_limit is None and not args.resume):
        parser.error("Session response limit requires a positive campaign response limit.")
    if args.session_deadline_utc:
        try:
            datetime.fromisoformat(args.session_deadline_utc.replace("Z", "+00:00"))
        except ValueError:
            parser.error("Session deadline must be an ISO UTC timestamp.")
    saved_manifest = None
    if args.resume:
        args.resume = args.resume.resolve()
        if not (args.resume / "manifest.json").is_file() or not (args.resume / "programs.sqlite").is_file():
            parser.error("--resume requires a native run with manifest.json and programs.sqlite.")
        saved_manifest = json.loads((args.resume / "manifest.json").read_text())
        saved_task = saved_manifest.get("task", "adaptive_swarm")
        if args.task is not None and args.task != saved_task:
            parser.error("--task differs from the saved run; start a separate study.")
        args.task = saved_task
        saved_seed = saved_manifest.get("search_seed")
        if args.search_seed is not None and args.search_seed != saved_seed:
            parser.error("--search-seed differs from the saved run; start a separate search replicate.")
        args.search_seed = saved_seed
        saved_limit = saved_manifest.get("logical_response_limit")
        if args.logical_response_limit is not None and args.logical_response_limit != saved_limit:
            parser.error("--logical-response-limit differs from the saved run; a run-local allowance cannot silently change on resume.")
        args.logical_response_limit = saved_limit
        saved_campaign = saved_manifest.get("campaign_generations")
        if saved_campaign is not None:
            if args.generations != saved_campaign or args.session_max_descendants is None:
                parser.error("Resume must retain --generations campaign total and explicit --session-max-descendants.")
    args.task = args.task or "adaptive_swarm"
    if args.task not in TASK_VERSIONS:
        parser.error(f"Unknown saved task: {args.task}")
    evaluation_version = TASK_VERSIONS[args.task]
    try:
        args.engine_config = resolve_engine(profile_path=args.engine_profile, model=args.model, effort=args.effort,
                                            embedding_model=args.embedding_model, saved_manifest=saved_manifest)
    except (OSError, ValueError, TypeError) as exc:
        parser.error(str(exc))
    args.model, args.effort = args.engine_config["default_model"], args.engine_config["default_effort"]
    engine_features = feature_state(args.engine_config, seed_only=args.seed_only)
    if args.print_engine_config:
        print(json.dumps({"task": args.task, "evaluation_version": evaluation_version,
                          "search_seed": args.search_seed, "engine_config": args.engine_config,
                          "logical_response_limit": args.logical_response_limit,
                          "features": engine_features, "model_calls": 0}, indent=2), flush=True)
        return 0
    default_results = ROOT / ("results/evolution" if args.task == "adaptive_swarm" else f"results/{args.task}/evolution")
    if args.run_dir:
        args.run_dir = args.run_dir.resolve()
        if args.results_root and args.results_root.resolve() != args.run_dir.parent:
            parser.error("--results-root must be the parent of --run-dir.")
    args.results_root = (args.resume.parent if args.resume else args.run_dir.parent if args.run_dir else args.results_root or default_results).resolve()
    default_suite = ROOT / ("configs/search.json" if args.task == "adaptive_swarm" else f"configs/{args.task}/search.json")
    args.suite = (args.suite or (args.resume / "search-suite.json" if args.resume else default_suite)).resolve()
    if not args.suite.is_file():
        parser.error(f"Evaluation suite does not exist: {args.suite}")
    os.environ["PYTHONUNBUFFERED"] = "1"
    os.environ.setdefault("SHINKA_HEADLESS_COMMAND", HEADLESS_COMMAND)
    os.environ.setdefault("SHINKA_PRICING_MODE", "offline")
    os.environ["SHINKA_HEADLESS_TIMEOUT"] = str(args.proposal_timeout_seconds)
    # Explicit subscription route and authentication check avoid API-key fallback.
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("CODEX_API_KEY", None)
    os.environ.pop("ADAPTIVE_SWARMS_STORAGE_CONFIG", None)
    os.environ["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")
    os.environ["ADAPTIVE_SWARMS_PROJECT_ROOT"] = str(ROOT)
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    run_dir = args.resume or args.run_dir or (args.results_root / (stamp + ("-seed" if args.seed_only else "-search")))
    target = 1 if args.seed_only else args.generations
    if args.session_max_descendants is not None:
        existing = summarize_database(run_dir) if args.resume else {"terminal_generation_ids": []}
        existing_terminal = set(existing.get("terminal_generation_ids", []))
        # Terminal failures are allocated slots. Accepted pending proposals also
        # retain their IDs and fit within this session's cumulative boundary.
        next_slot = max(existing_terminal | {0}) + 1
        args.session_generation_target = min(args.generations, next_slot + args.session_max_descendants)
        if args.session_stop_generation is not None:
            if not next_slot <= args.session_stop_generation <= args.session_generation_target:
                parser.error("Session stop target must extend existing work within the session slot ceiling.")
            args.session_generation_target = args.session_stop_generation
    else:
        args.session_generation_target = target
    try:
        if not args.resume and run_dir.exists() and (not run_dir.is_dir() or any(run_dir.iterdir())):
            parser.error("New run directory contains saved work; use --resume instead of overwriting it.")
        with exclusive_controller(args.results_root), EventLogger(run_dir, heartbeat_seconds=args.heartbeat_seconds) as log:
            log.set_activity("checking native runtime and subscription route")
            report = inspect_runtime(args.model, args.effort, args.seed_only)
            if args.resume:
                manifest = json.loads((run_dir / "manifest.json").read_text())
                if manifest.get("evaluation_version") != evaluation_version:
                    raise RuntimeError("Evaluation version differs from this run. Use a new run for a revised scoring method.")
                if manifest.get("suite_sha256") != file_hash(args.suite) or manifest.get("suite_sha256") != file_hash(run_dir / "search-suite.json"):
                    raise RuntimeError("Evaluation suite differs from the saved run; pass --suite with the saved search-suite.json or start a new study.")
                active = {**report, "started_at": stamp, "generation_target": target, "previous_status": manifest.get("status"), "status": "preflight"}
                manifest.setdefault("resume_attempts", []).append(active)
            else:
                manifest = {**report, "upstream_commit": PINNED_SHINKA, "task": args.task, "evaluation_version": evaluation_version, "generation_target": target,
                        "started_at": stamp, "suite_sha256": hashlib.sha256(args.suite.read_bytes()).hexdigest(),
                        "status": "preflight", "run_dir": str(run_dir)}
                active = manifest
            manifest.setdefault("engine_config", args.engine_config)
            manifest.setdefault("search_seed", args.search_seed)
            manifest.setdefault("logical_response_limit", args.logical_response_limit)
            if args.session_max_descendants is not None:
                manifest.setdefault("campaign_generations", args.generations)
                active["session_limits"] = {"max_descendants": args.session_max_descendants,
                    "generation_target": args.session_generation_target, "logical_responses": args.session_response_limit,
                    "response_start": args.session_response_start, "research_cutoff_utc": args.session_deadline_utc,
                    "admission_seconds": args.admission_seconds, "admission_overhead_seconds": args.admission_overhead_seconds}
                active["campaign_status"] = "open"
            active["engine_features"] = engine_features
            active["execution_support_sha256"] = {
                str(path.relative_to(ROOT)): file_hash(path)
                for path in [Path(__file__), ROOT / "scripts/check_runtime.py",
                             *[ROOT / "src/adaptive_swarms" / name for name in
                               ("engine_config.py", "engine_runtime.py", "engine_progress.py", "storage_runner.py", "native_storage.py", "sprint_budget.py", "campaign_resume.py")]]
            }
            active["search_randomness"] = {"search_seed": args.search_seed,
                                          "seed_applied": args.search_seed is not None and not bool(args.resume),
                                          "resume_rng_state_restored": False,
                                          "note": "Resume preserves completed evidence; native sampling RNG state is not restored, so the uninterrupted proposal sequence is not promised."}
            hashes = prepare_snapshot(args, run_dir)
            if "source_hashes" not in manifest:
                manifest["source_hashes"] = hashes
            active["source_hashes"] = hashes
            atomic_json(run_dir / "manifest.json", manifest)
            log.event("configuration", message="Declared native run configuration", task=args.task, model=args.model, inner_effort=args.effort,
                      effective_effort="unverified until Codex invocation", generation_target=target, seed_only=args.seed_only, resuming=bool(args.resume))
            if args.logical_response_limit is not None:
                log.event("sprint_model_allowance", message="Run-local receipt-based model allowance; hidden provider retries remain unobserved",
                          logical_response_limit=args.logical_response_limit)
            log.event("engine_configuration", message=f"Native engine profile: {args.engine_config['profile_name']}", **engine_features)
            log.event("search_randomness", message="Native search sampling seed and resume scope", **active["search_randomness"])
            if not report["ready"]:
                active["status"] = "blocked_runtime"
                atomic_json(run_dir / "manifest.json", manifest)
                for error in report["errors"]:
                    log.event("runtime_error", message=error)
                return 2
            try:
                active["embedding_preflight"] = check_embedding_endpoint(args.engine_config, seed_only=args.seed_only)
            except RuntimeError as exc:
                active.update(status="blocked_embedding", error=str(exc))
                atomic_json(run_dir / "manifest.json", manifest)
                log.event("runtime_error", message=str(exc))
                return 2
            atomic_json(run_dir / "manifest.json", manifest)
            if args.search_seed is not None and not args.resume:
                import random
                import numpy as np
                random.seed(args.search_seed)
                np.random.seed(args.search_seed)
            log.event("runtime_ready", message="Runtime check passed; starting native ShinkaEvolve", results=str(run_dir))
            stop = threading.Event()
            monitor = threading.Thread(target=relay_evaluator_events, args=(run_dir, log, stop, bool(args.resume)), daemon=True)
            monitor.start()
            def interrupted(signum, frame):
                raise KeyboardInterrupt
            previous_term = signal.signal(signal.SIGTERM, interrupted)
            try:
                run_result = run_native(args, run_dir, log) or {}
                active["search_randomness"]["resume_rng_state_restored"] = run_result.get("resume_rng_state_restored", False)
                if args.session_max_descendants is not None:
                    active["search_randomness"]["note"] = "Python/NumPy sampler state restored from the last validated drained boundary when present; interrupted proposals and LLM outputs are not replay-guaranteed."
                    active["effective_session_generation_target"] = run_result.get("effective_session_generation_target", args.session_generation_target)
                    active["campaign_pause_reason"] = run_result.get("campaign_pause_reason")
                summary = summarize_database(run_dir)
                expected = run_result.get("effective_session_generation_target", args.session_generation_target)
                terminal_ids = set(summary.get("terminal_generation_ids", range(summary["generation_records"])))
                missing_slots = sorted(set(range(expected)) - terminal_ids)
                if missing_slots or not summary.get("valid_seed", bool(summary["valid_programs"])):
                    raise RuntimeError(f"Native run did not finish a valid seed and all requested terminal slots; missing={missing_slots}, summary={summary}")
                campaign_complete = args.session_max_descendants is not None and set(range(args.generations)).issubset(terminal_ids)
                status = ("campaign_complete" if campaign_complete else "campaign_paused") if args.session_max_descendants is not None else "seed_complete" if args.seed_only else "search_complete"
                active.update({"status": status, **summary})
                if args.session_max_descendants is not None:
                    active["campaign_status"] = "complete" if campaign_complete else "open"
                if args.resume:
                    manifest.update({"status": active["status"], "latest_summary": summary})
                log.event("run_complete", message="Campaign session paused; no final selection or fresh evaluation" if status == "campaign_paused" else "Native seed evaluation complete; no mutation calls" if args.seed_only else "Native search complete; inspect scientific outcomes and descendants", **summary)
                return 0
            except SprintLimitReached as exc:
                summary = summarize_database(run_dir)
                active.update(status="sprint_limit_reached", error=str(exc), **summary)
                manifest.update(status="sprint_limit_reached", latest_summary=summary)
                log.event("sprint_stopped", message=str(exc), scientific_failure=False, **summary)
                return 77
            except InfrastructureError as exc:
                active.update(status="infrastructure_failed", error=str(exc))
                manifest["status"] = "infrastructure_failed"
                print(f"Infrastructure failure: {exc}", file=sys.stderr, flush=True)
                log.event("infrastructure_failed", message=str(exc))
                return INFRASTRUCTURE_EXIT_CODE
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
                if active.get("status") in {"interrupted", "failed", "infrastructure_failed", "sprint_limit_reached"}:
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
                atomic_json(run_dir / "manifest.json", manifest)
    except InfrastructureError as exc:
        print(f"Infrastructure failure: {exc}", file=sys.stderr, flush=True)
        return INFRASTRUCTURE_EXIT_CODE
    except (OSError, RuntimeError) as exc:
        print(f"Cannot start evolution: {exc}", file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
