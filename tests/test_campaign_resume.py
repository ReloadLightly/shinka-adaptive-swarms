"""No-model fixtures for opt-in campaign boundaries and native meta state."""
import asyncio
import json
import random
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from adaptive_swarms.campaign_resume import CampaignResumeRunnerMixin, validate_meta_state, _digest
from adaptive_swarms.execution import InfrastructureError
from adaptive_swarms.sprint_budget import LogicalResponseBudget, SprintLimitReached


class NativeFixture:
    async def _setup_async(self):
        self.setup_calls += 1

    async def _start_proposals(self, count):
        self.proposed.append(self.next_generation_to_submit)
        self.next_generation_to_submit += count

    async def _cleanup_async(self):
        self.cleanup_calls += 1

    async def _print_final_summary(self):
        self.final_prints += 1


class Runner(CampaignResumeRunnerMixin, NativeFixture):
    def __init__(self, root, programs, target=4):
        self.results_dir = root
        self.events = []
        self.log = SimpleNamespace(event=lambda name, **kw: self.events.append((name, kw)))
        self.db = SimpleNamespace(get_all_programs=lambda: list(programs))
        self.evo_config = SimpleNamespace(num_generations=target)
        self.next_generation_to_submit = max((p.generation for p in programs), default=0) + 1
        self.running_jobs, self.active_proposal_tasks = [], {}
        self.slot_available = asyncio.Event()
        self.finalization_complete = asyncio.Event()
        self.setup_calls = self.cleanup_calls = self.final_prints = 0
        self.proposed = []
        self.drains = []
        self.meta_calls = self.final_meta_calls = 0
        sync = SimpleNamespace(meta_summary=None, meta_scratch_pad=None, meta_recommendations=None,
            meta_recommendations_history=[], evaluated_since_last_meta=[], total_programs_processed=0)
        sync.add_evaluated_program = lambda p: sync.evaluated_since_last_meta.append(p)
        async def update(*args):
            self.meta_calls += 1
            sync.meta_summary = "tested changes"
            sync.meta_scratch_pad = "persistent scratch"
            sync.meta_recommendations = "1. measured recommendation"
            sync.meta_recommendations_history.append(sync.meta_recommendations)
            sync.total_programs_processed += len(sync.evaluated_since_last_meta)
            sync.evaluated_since_last_meta = []
            return sync.meta_recommendations, 0
        async def final(*args):
            self.final_meta_calls += 1
            return True, 0
        self.meta_summarizer = SimpleNamespace(sync_summarizer=sync, update_meta_memory_async=update,
            perform_final_summary_async=final)
        self._get_completed_job_work_count = lambda: 0
        self._has_background_side_effect_work = lambda: False

    def _fail_infrastructure(self, error):
        raise error

    async def _wait_for_completed_job_batches(self):
        self.drains.append("database")

    async def _wait_for_background_side_effects(self):
        self.drains.append("meta_and_maintenance")


def program(i):
    return SimpleNamespace(id=f"program-{i}", generation=i, metadata={})


def configured(tmp_path, programs, **kwargs):
    runner = Runner(tmp_path, programs)
    runner.configure_campaign(campaign_generations=51, log=runner.log, **kwargs)
    return runner


def test_roundtrip_meta_history_pending_processed_rng_and_next_generation(tmp_path):
    programs = [program(i) for i in range(6)]
    runner = configured(tmp_path, programs)
    meta = runner.meta_summarizer.sync_summarizer
    for p in programs[:5]:
        meta.add_evaluated_program(p)
    asyncio.run(runner.meta_summarizer.update_meta_memory_async())
    meta.add_evaluated_program(programs[5])
    random.seed(731)
    np.random.seed(827)
    runner._checkpoint_campaign("clean_pause", drained=True)
    expected = random.random(), np.random.random()
    random.seed(15)
    np.random.seed(19)
    restored = configured(tmp_path, programs)
    asyncio.run(restored._setup_async())
    actual = restored.meta_summarizer.sync_summarizer
    assert actual.meta_summary == meta.meta_summary
    assert actual.meta_scratch_pad == meta.meta_scratch_pad
    assert actual.meta_recommendations == meta.meta_recommendations
    assert actual.meta_recommendations_history == meta.meta_recommendations_history
    assert actual.total_programs_processed == 5
    assert [p.id for p in actual.evaluated_since_last_meta] == ["program-5"]
    assert (random.random(), np.random.random()) == expected
    asyncio.run(restored._start_proposals(1))
    assert restored.proposed == [6]
    # Repeated native side effects cannot duplicate pending/processed IDs.
    actual.add_evaluated_program(programs[0])
    actual.add_evaluated_program(programs[5])
    assert [p.id for p in actual.evaluated_since_last_meta] == ["program-5"]


def test_database_commit_ahead_of_checkpoint_reconciles_once(tmp_path):
    programs = [program(0)]
    runner = configured(tmp_path, programs)
    runner._restore_campaign()
    programs.append(program(1))
    resumed = configured(tmp_path, programs)
    resumed._restore_campaign()
    assert [p.id for p in resumed.meta_summarizer.sync_summarizer.evaluated_since_last_meta] == ["program-0", "program-1"]
    resumed._restore_campaign()
    assert len(resumed.meta_summarizer.sync_summarizer.evaluated_since_last_meta) == 2


def test_unknown_and_duplicate_ids_fail_explicitly(tmp_path):
    programs = [program(0)]
    runner = configured(tmp_path, programs)
    runner._restore_campaign()
    path = tmp_path / "campaign-checkpoint.json"
    state = json.loads(path.read_text())
    state["meta"]["pending_program_ids"].append("program-0")
    state["sha256"] = _digest({k:v for k,v in state.items() if k != "sha256"})
    with pytest.raises(InfrastructureError, match="duplicated"):
        validate_meta_state(state, {p.id:p for p in programs})
    state["meta"]["pending_program_ids"] = ["missing"]
    state["sha256"] = _digest({k:v for k,v in state.items() if k != "sha256"})
    with pytest.raises(InfrastructureError, match="missing database"):
        validate_meta_state(state, {p.id:p for p in programs})


def test_corrupted_checkpoint_and_missing_checkpoint_are_not_silent(tmp_path):
    runner = configured(tmp_path, [program(0)])
    runner._restore_campaign()
    path = tmp_path / "campaign-checkpoint.json"
    path.write_text(path.read_text().replace('"total_programs_processed": 0', '"total_programs_processed": 1'))
    with pytest.raises(InfrastructureError, match="integrity"):
        configured(tmp_path, [program(0)])._restore_campaign()
    path.unlink()
    with pytest.raises(InfrastructureError, match="without a meta checkpoint"):
        configured(tmp_path, [program(0), program(1)])._restore_campaign()


def test_intermediate_pause_suppresses_final_summary_but_keeps_normal_update(tmp_path):
    runner = configured(tmp_path, [program(0)])
    runner._restore_campaign()
    assert asyncio.run(runner.meta_summarizer.perform_final_summary_async()) == (False, 0)
    assert runner.final_meta_calls == 0
    asyncio.run(runner.meta_summarizer.update_meta_memory_async())
    assert runner.meta_calls == 1
    asyncio.run(runner._print_final_summary())
    assert runner.final_prints == 0


def test_full_campaign_allows_final_summary(tmp_path):
    runner = configured(tmp_path, [program(i) for i in range(51)])
    assert asyncio.run(runner.meta_summarizer.perform_final_summary_async()) == (True, 0)
    assert runner.final_meta_calls == 1


def test_clean_pause_drains_database_and_meta_before_rng_checkpoint(tmp_path):
    runner = configured(tmp_path, [program(0)])
    runner._restore_campaign()
    runner.finalization_complete.set()
    asyncio.run(runner._cleanup_async())
    state = json.loads((tmp_path / "campaign-checkpoint.json").read_text())
    assert runner.drains == ["database", "meta_and_maintenance"]
    assert state["drained"] and state["status"] == "campaign_paused"
    assert runner.cleanup_calls == 1


def test_deadline_closes_admission_without_assigning_extra_slot(tmp_path):
    runner = configured(tmp_path, [program(0), program(1)], deadline_utc="2000-01-01T00:00:00Z", admission_seconds=900)
    asyncio.run(runner._start_proposals(1))
    assert runner.proposed == []
    assert runner.next_generation_to_submit == runner.evo_config.num_generations == 2
    assert runner._campaign_size == 51


def test_proposal_waits_for_background_meta(tmp_path):
    runner = configured(tmp_path, [program(0)])
    runner._has_background_side_effect_work = lambda: True
    asyncio.run(runner._start_proposals(1))
    assert runner.proposed == []


def test_session_receipt_cap_is_delta_not_campaign_limit(tmp_path):
    prior = tmp_path / "engine_calls" / "old.json"
    prior.parent.mkdir()
    prior.write_text(json.dumps({"requested_logical_responses": 40}))
    budget = LogicalResponseBudget(tmp_path, 400, session_limit=80, session_start=40)
    receipt = {"call_id":"meta-test", "role":"meta", "requested_logical_responses": 80}
    budget.reserve(prior.parent / "new.json", receipt, 80)
    assert budget.used == 120 and budget.limit == 400
    with pytest.raises(SprintLimitReached):
        budget.reserve(prior.parent / "declined.json", {"call_id":"next", "role":"mutation"}, 1)
    assert not (prior.parent / "declined.json").exists()
    next_session = LogicalResponseBudget(tmp_path, 400, session_limit=80)
    assert next_session.used == next_session.session_start == 120


def test_native_generation_zero_seed_resume_skips_re_evaluation(tmp_path):
    from adaptive_swarms.campaign_resume import reuse_existing_native_seed
    from shinka.core.async_runner import ShinkaEvolveRunner
    async def count(): return 1
    runner = SimpleNamespace(db=SimpleNamespace(last_iteration=0),
        async_db=SimpleNamespace(get_total_program_count_async=count),
        _count_completed_generations_from_db=count)
    async def restore():
        await ShinkaEvolveRunner._restore_resume_progress(runner)
    runner._restore_resume_progress = restore
    events = []
    log = SimpleNamespace(event=lambda event, **kw: events.append(event))
    assert asyncio.run(reuse_existing_native_seed(runner, resuming=True, log=log))
    assert runner.completed_generations == runner.next_generation_to_submit == 1
    assert events == ["seed_reused"]
    assert not asyncio.run(reuse_existing_native_seed(runner, resuming=False, log=log))


def test_past_deadline_stops_before_transport_not_candidate_failure(tmp_path):
    from adaptive_swarms.engine_runtime import install_engine_observers
    import time
    calls = []
    async def transport(*args, **kwargs):
        calls.append(1)
        return SimpleNamespace(content="should not run")
    def fail(error): raise error
    client = SimpleNamespace(model_names=["headless/codex@gpt-6-astra"], query=transport, batch_kwargs_query=transport)
    runner = SimpleNamespace(llm=client, meta_summarizer=None, novelty_judge=None, embedding_client=None,
        _fail_infrastructure=fail, _campaign_deadline=time.time() - 1, _campaign_monotonic_deadline=time.monotonic() - 1)
    log = SimpleNamespace(event=lambda *a, **kw: None, set_activity=lambda *a: None)
    cleanup = install_engine_observers(runner, log, tmp_path, logical_response_limit=400, session_response_limit=80)
    try:
        with pytest.raises(SprintLimitReached, match="cutoff"):
            asyncio.run(client.query("mutation request"))
    finally:
        cleanup()
    assert not calls
    receipt = json.loads(next((tmp_path / "engine_calls").glob("*.json")).read_text())
    assert receipt["status"] == "stopped_allowance"
    assert receipt["logical_response_limit"] == 400
    assert receipt["session_response_limit"] == 80
