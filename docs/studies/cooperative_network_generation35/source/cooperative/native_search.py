"""Phase B persistence/telemetry around native Shinka UCB and island operators.

Hooks apply only to explicitly registered campaign database paths. They do not
replace native selection, rewards, copying, migration or spawning algorithms.
"""
from __future__ import annotations

import contextvars
from contextlib import closing
import hashlib
import json
import pickle
import random
import shutil
import sqlite3
from pathlib import Path
import threading
import time

import numpy as np

_ROOTS = {}
_INSTALLED = False
_EVENT_LOCK = threading.Lock()
_CONTEXT = contextvars.ContextVar("phase_b_search_context", default={})

DATABASE_SETTINGS = dict(num_islands=3, parent_selection_strategy="weighted",
    parent_selection_lambda=10.0, archive_size=64, num_archive_inspirations=1,
    num_top_k_inspirations=1, island_selection_strategy="uniform",
    migration_interval=10, migration_rate=0.1, island_elitism=True,
    enforce_island_separation=True, enable_dynamic_islands=True,
    stagnation_threshold=20, island_spawn_strategy="archive_random",
    island_spawn_subtree_size=1)
UCB_SETTINGS = {"cost_aware_coef": 0.0}


def _jsonable(value):
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [_jsonable(item) for item in value]
    if isinstance(value, np.generic):
        return _jsonable(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def _event(root, kind, **values):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    with _EVENT_LOCK, (root / "phase-b-search-events.jsonl").open("a") as stream:
        stream.write(json.dumps(_jsonable({"time": time.time(), "event": kind, **values}), allow_nan=False) + "\n")


def _atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(_jsonable(value), indent=2, sort_keys=True, allow_nan=False) + "\n")
    temporary.replace(path)


def _atomic_pickle(path, value):
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as stream:
        pickle.dump(value, stream)
    temporary.replace(path)


def _root(database_or_manager):
    path = getattr(database_or_manager.config, "db_path", None)
    return _ROOTS.get(str(Path(path).resolve())) if path else None


def _metadata(manager, key, value):
    manager.cursor.execute("INSERT OR REPLACE INTO metadata_store(key,value) VALUES (?,?)", (key, str(value)))
    manager.conn.commit()


def _effective_islands(manager, *, persist):
    maximum = manager.cursor.execute("SELECT MAX(island_idx) FROM programs").fetchone()[0]
    saved = manager.cursor.execute("SELECT value FROM metadata_store WHERE key='phase_b_effective_islands'").fetchone()
    count = max(3, (maximum + 1) if maximum is not None else 0, int(saved[0]) if saved else 0)
    manager.config.num_islands = count
    if persist and (saved is None or int(saved[0]) != count):
        _metadata(manager, "phase_b_effective_islands", count)
    return count


def _mark_copy(manager, new_id, source_id, reason):
    source = manager.cursor.execute("SELECT metadata FROM programs WHERE id=?", (source_id,)).fetchone()
    source_metadata = json.loads(source[0] or "{}")
    original = source_metadata.get("copied_from_program_id", source_id)
    row = manager.cursor.execute("SELECT metadata FROM programs WHERE id=?", (new_id,)).fetchone()
    metadata = json.loads(row[0] or "{}")
    metadata.update(administrative_copy=True, copied_from_program_id=original,
                    copy_reason=reason, immediate_copy_source_id=source_id)
    manager.cursor.execute("UPDATE programs SET metadata=? WHERE id=?", (json.dumps(metadata), new_id))
    manager.conn.commit()
    _event(_root(manager), "administrative_copy", program_id=new_id,
           copied_from_program_id=original, immediate_copy_source_id=source_id, copy_reason=reason)


def install_phase_b_hooks(search):
    """Install scoped hooks before constructing native runner/database workers."""
    global _INSTALLED
    search = Path(search).resolve()
    _ROOTS[str(search / "programs.sqlite")] = search
    if _INSTALLED:
        return
    from shinka.database.dbase import ProgramDatabase
    from shinka.database.islands import CombinedIslandManager

    original_init = ProgramDatabase.__init__
    original_copy = CombinedIslandManager.copy_program_to_islands
    original_dynamic_copy = CombinedIslandManager._copy_program_to_island
    original_spawn = CombinedIslandManager.spawn_new_island
    original_migrate = CombinedIslandManager.perform_migration
    original_sample = ProgramDatabase.sample_with_fix_mode

    def database_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        if _root(self):
            _effective_islands(self.island_manager, persist=not self.read_only)

    def copy_initial(self, source):
        ids = original_copy(self, source)
        if _root(self):
            for program_id in ids:
                _mark_copy(self, program_id, source.id, "phase_b_initial_island")
        return ids

    def copy_dynamic(self, source_program, *args, **kwargs):
        program_id = original_dynamic_copy(self, source_program, *args, **kwargs)
        if _root(self):
            _mark_copy(self, program_id, source_program["id"], "native_dynamic_island")
        return program_id

    def spawn(self):
        root = _root(self)
        before = _effective_islands(self, persist=True) if root else None
        result = original_spawn(self)
        if root and result:
            effective = _effective_islands(self, persist=True)
            _event(root, "native_island_spawn", previous_islands=before,
                   effective_islands=effective, strategy=self.config.island_spawn_strategy,
                   subtree_size=self.config.island_spawn_subtree_size)
        return result

    def migrate(self, current_generation):
        root = _root(self)
        if not root:
            return original_migrate(self, current_generation)
        effective = _effective_islands(self, persist=True)
        key = f"phase_b_migration_generation_{current_generation}"
        if self.cursor.execute("SELECT value FROM metadata_store WHERE key=?", (key,)).fetchone():
            _event(root, "native_migration_already_applied", generation=current_generation)
            return False
        # The native migration commits internally. Its per-program history is
        # evidence if a process exited between that commit and our receipt.
        committed = []
        for row in self.cursor.execute("SELECT id,migration_history FROM programs"):
            for entry in json.loads(row["migration_history"] or "[]"):
                if entry.get("generation") == current_generation:
                    committed.append({"program_id": row["id"], "from": entry["from"], "to": entry["to"]})
        if committed:
            _metadata(self, key, json.dumps({"moved": committed, "effective_islands": effective,
                                            "recovered_from_native_history": True}))
            _metadata(self, "phase_b_last_migration_generation", current_generation)
            _event(root, "native_migration_receipt_recovered", generation=current_generation, moves=committed)
            return False
        before = {row["id"]: row["island_idx"] for row in self.cursor.execute("SELECT id,island_idx FROM programs")}
        result = original_migrate(self, current_generation)
        moves = [{"program_id": row["id"], "from": before[row["id"]], "to": row["island_idx"]}
                 for row in self.cursor.execute("SELECT id,island_idx FROM programs")
                 if row["island_idx"] != before[row["id"]]]
        _metadata(self, key, json.dumps({"moved": moves, "effective_islands": effective}))
        _metadata(self, "phase_b_last_migration_generation", current_generation)
        _event(root, "native_migration", generation=current_generation,
               effective_islands=effective, rate=self.config.migration_rate,
               elite_protection=self.config.island_elitism, moves=moves)
        return result

    def sample(self, *args, **kwargs):
        result = original_sample(self, *args, **kwargs)
        root = _root(self)
        if root:
            parent, archive, top, *rest = result
            _event(root, "native_parent_sample", generation=kwargs.get("target_generation"),
                   parent_id=parent.id, island=parent.island_idx,
                   archive_inspiration_ids=[program.id for program in archive],
                   top_k_inspiration_ids=[program.id for program in top],
                   effective_islands=self.config.num_islands)
        return result

    ProgramDatabase.__init__ = database_init
    ProgramDatabase.sample_with_fix_mode = sample
    CombinedIslandManager.copy_program_to_islands = copy_initial
    CombinedIslandManager._copy_program_to_island = copy_dynamic
    CombinedIslandManager.spawn_new_island = spawn
    CombinedIslandManager.perform_migration = migrate
    _INSTALLED = True


def _bandit_state(bandit, rewarded_ids=()):
    state = bandit.get_state()
    state["phase_b_extension"] = {
        "version": 1, "sampler_class": "AsymmetricUCB",
        "python_random_state": random.getstate(), "numpy_random_state": np.random.get_state(),
        "bandit_rng_state": bandit.rng.bit_generator.state,
        "rewarded_program_ids": sorted(rewarded_ids),
        "rng_limitation": "SQLite ORDER BY RANDOM and UUID generation cannot be restored through supported native RNG state; bit-identical continuation is not claimed."}
    return state


def initialize_phase_b(search, db_config, arm_routes, *, ucb_kwargs=None, boundary_generation=27):
    """Explicit one-time migration under caller-held campaign lock; no inference."""
    from shinka.database.dbase import ProgramDatabase
    from shinka.llm.prioritization import AsymmetricUCB
    search = Path(search)
    install_phase_b_hooks(search)
    receipt_path = search / "phase-b-initialization.json"
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if receipt["arm_routes"] != list(arm_routes):
            raise RuntimeError("Phase B already initialized with different arms")
        with (search / "bandit_state.pkl").open("rb") as stream:
            state = pickle.load(stream)
        if state.get("arm_names") != list(arm_routes) or not state.get("phase_b_extension"):
            raise RuntimeError("Initialized Phase B has missing/divergent native UCB state")
        preserved = search / receipt["archived_fixed_sampler"]
        if hashlib.sha256(preserved.read_bytes()).hexdigest() != receipt["archived_fixed_sampler_sha256"]:
            raise RuntimeError("Archived Phase A fixed sampler changed")
        with closing(sqlite3.connect((search / "programs.sqlite").resolve().as_uri() + "?mode=ro", uri=True)) as connection:
            for program_id in receipt["administrative_copy_ids"]:
                row = connection.execute("SELECT metadata FROM programs WHERE id=?", (program_id,)).fetchone()
                if row is None or not json.loads(row[0] or "{}").get("administrative_copy"):
                    raise RuntimeError("Recorded initial native island copy is missing or unmarked")
        return receipt
    pending_path = search / "phase-b-initialization.pending.json"
    if pending_path.exists():
        raise RuntimeError("Partial Phase B initialization receipt exists; reconcile before repeating native copies")
    db_config.db_path = str((search / "programs.sqlite").resolve())
    database = ProgramDatabase(db_config)
    try:
        existing = database.get_all_programs()
        if any((program.metadata or {}).get("administrative_copy") for program in existing):
            raise RuntimeError("Partial Phase B copy migration found without receipt; reconcile without duplicating copies")
        islands = {program.island_idx for program in existing}
        if islands != {0} or database.config.num_islands != 3:
            raise RuntimeError("Phase B initialization requires one existing island and configured count three")
        best = database.get_best_program()
        if best is None or not best.correct:
            raise RuntimeError("An existing evaluated correct source is required for native island copies")
        old_state = search / "bandit_state.pkl"
        if not old_state.exists():
            raise RuntimeError("Existing fixed-sampler state must be preserved before Phase B")
        archive = search / "phase-b-history" / f"fixed-bandit-{time.time_ns()}.pkl"
        archive.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(old_state, archive)
        options = dict(UCB_SETTINGS if ucb_kwargs is None else ucb_kwargs)
        if options.get("cost_aware_coef", 0.0) != 0.0:
            raise RuntimeError("Subscription Phase B requires native UCB monetary cost weight zero")
        bandit = AsymmetricUCB(arm_names=list(arm_routes), **options)
        bandit.set_baseline_score(0.0)
        _atomic_json(pending_path, {"source_program_id": best.id, "arm_routes": list(arm_routes),
                     "archived_fixed_sampler": str(archive.relative_to(search)),
                     "started_at": time.time(), "meaning": "Native copy methods commit internally; incomplete migration must be reconciled explicitly"})
        copies = database.island_manager.copy_program_to_islands(best)
        if set(database.island_manager.get_initialized_islands()) != {0, 1, 2}:
            raise RuntimeError("Native island-copy initialization did not populate all three islands")
        _atomic_pickle(old_state, _bandit_state(bandit))
        _metadata(database.island_manager, "phase_b_boundary_generation", boundary_generation)
        receipt = {"phase": "B", "initialized_at": time.time(),
                   "boundary_generation": boundary_generation, "arm_routes": list(arm_routes),
                   "ucb_kwargs": options, "native_sampler": "AsymmetricUCB",
                   "ucb_history": "Explicit fresh arm counts, no fabricated Phase A trials; fixed sampler archived",
                   "archived_fixed_sampler": str(archive.relative_to(search)),
                   "archived_fixed_sampler_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                   "original_program_rows": len(existing), "administrative_copy_ids": copies,
                   "initial_copy_source_id": best.id, "initial_islands": [0, 1, 2],
                   "stagnation_best_score_generation": database.best_score_generation,
                   "stagnation_best_score_ever": database.best_score_ever,
                   "rng_limitation": _bandit_state(bandit)["phase_b_extension"]["rng_limitation"]}
        _atomic_json(receipt_path, receipt)
        pending_path.replace(archive.with_suffix(".initialization-completed.json"))
        _event(search, "phase_b_initialized", **receipt)
        return receipt
    finally:
        database.close()


def make_search_runner_class(base):
    """Compose above campaign continuation/memory mixins; preserve native UCB."""
    class PhaseBSearchRunner(base):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            from shinka.llm.prioritization import AsymmetricUCB
            if not isinstance(self.llm_selection, AsymmetricUCB):
                raise RuntimeError("Phase B requires the native AsymmetricUCB sampler")
            if self.llm_selection.cost_aware_coefficient != 0.0:
                raise RuntimeError("Phase B requires UCB monetary cost weight zero")
            self._phase_b_rewarded_ids = set()
            bandit = self.llm_selection
            original_update = bandit.update
            original_submit = bandit.update_submitted
            original_select = bandit.select_llm
            original_cost = bandit.update_cost

            def update(arm, reward, baseline=None):
                context = _CONTEXT.get()
                program_id = context.get("program_id")
                if program_id and program_id in self._phase_b_rewarded_ids:
                    _event(self.results_dir, "native_ucb_reward_already_applied", **context)
                    return None
                effective = original_update(arm, reward, baseline)
                if program_id:
                    self._phase_b_rewarded_ids.add(program_id)
                self._save_bandit_state()
                _event(self.results_dir, "native_ucb_reward", **context, arm=arm,
                       raw_reward=reward, parent_baseline=baseline, native_update_result=effective,
                       n_completed=bandit.n_completed, cost_weight=bandit.cost_aware_coefficient)
                return effective

            def submit(arm):
                result = original_submit(arm)
                self._save_bandit_state()
                _event(self.results_dir, "native_ucb_submitted", **_CONTEXT.get(), arm=arm,
                       n_submitted=bandit.n_submitted)
                return result

            def select(*args, **kwargs):
                selected, posterior = original_select(*args, **kwargs)
                self._save_bandit_state()
                _event(self.results_dir, "native_ucb_selection", **_CONTEXT.get(),
                       selected=selected, posterior=posterior, arm_names=bandit._arm_names)
                return selected, posterior

            def cost(arm, cost):
                result = original_cost(arm, cost)
                self._save_bandit_state()
                return result

            bandit.update, bandit.update_submitted = update, submit
            bandit.select_llm, bandit.update_cost = select, cost

        def _save_bandit_state(self):
            path = Path(self.results_dir) / "bandit_state.pkl"
            _atomic_pickle(path, _bandit_state(self.llm_selection, getattr(self, "_phase_b_rewarded_ids", ())))
            _atomic_json(path.with_name("phase-b-bandit-summary.json"), {
                "native_state": self.llm_selection.get_state(),
                "rewarded_program_ids": sorted(getattr(self, "_phase_b_rewarded_ids", ())),
                "monetary_cost_weight": self.llm_selection.cost_aware_coefficient})

        def _load_bandit_state(self):
            path = Path(self.results_dir) / "bandit_state.pkl"
            with path.open("rb") as stream:
                state = pickle.load(stream)
            extension = state.get("phase_b_extension")
            if not extension or extension.get("sampler_class") != "AsymmetricUCB":
                raise RuntimeError("Phase B UCB state lacks explicit initialization/provenance")
            if state["arm_names"] != self.llm_selection._arm_names:
                raise RuntimeError("Saved Phase B UCB arms differ from configured arms")
            self.llm_selection.set_state(state)
            random.setstate(extension["python_random_state"])
            np.random.set_state(extension["numpy_random_state"])
            self.llm_selection.rng.bit_generator.state = extension["bandit_rng_state"]
            self._phase_b_rewarded_ids = set(extension["rewarded_program_ids"])
            _event(self.results_dir, "native_ucb_state_restored", arm_names=state["arm_names"],
                   n_completed=self.llm_selection.n_completed,
                   rewarded_program_ids=sorted(self._phase_b_rewarded_ids))

        async def _generate_proposal_async(self, generation, task_id):
            token = _CONTEXT.set({"generation": generation})
            try:
                return await super()._generate_proposal_async(generation, task_id)
            finally:
                _CONTEXT.reset(token)

        async def _apply_persisted_program_side_effects(self, persisted_event):
            program = persisted_event.program
            token = _CONTEXT.set({"generation": program.generation, "program_id": program.id,
                                  "parent_id": program.parent_id, "island": program.island_idx})
            try:
                await super()._apply_persisted_program_side_effects(persisted_event)
                self._save_bandit_state()
            finally:
                _CONTEXT.reset(token)

    return PhaseBSearchRunner
