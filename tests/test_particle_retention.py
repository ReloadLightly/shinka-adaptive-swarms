"""Focused retention timing, purity, allocation, randomness and legacy checks."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType, SimpleNamespace
from datetime import datetime, timezone

import pytest

from adaptive_swarms import simulator
from adaptive_swarms.logging import atomic_json
from adaptive_swarms.particle_retention import (best_memory_priority, fixed_retention_response,
    inspect_priority_source, load_retention_priority, random_priority, retention_snapshot,
    select_retained_particle, selection_rng_for_seed, RetentionPolicyError)

ROOT = Path(__file__).resolve().parents[1]
LEDGER = Path(os.environ.get("PARTICLE_RETENTION_FIXTURE_LEDGER", Path(tempfile.gettempdir()) /
                             f"particle-retention-fixtures-{os.getpid()}.json"))
SMALL = {"dimension": 5, "npeaks": 10, "budget": 1000, "period": 100,
         "environment_seed": 817, "optimizer_seed": 819, "move_severity": 1,
         "trace_interval": 25, "snapshot_interval": 0, "progress_interval": 0}


def recorded_run(run, config, label, **kwargs):
    try:
        result = run(config, **kwargs)
    except Exception as exc:
        record = {"status": "failed_fixture", "error": f"{type(exc).__name__}: {exc}",
                  "objective_queries": getattr(exc, "objective_queries", None),
                  "evaluation_counts": getattr(exc, "evaluation_counts", None)}
        raise
    else:
        record = {"status": "completed", "objective_queries": result["evaluations"],
                  "offline_error": result["offline_error"], "evaluation_counts": result["evaluation_counts"]}
        return result
    finally:
        ledger = json.loads(LEDGER.read_text()) if LEDGER.exists() else {"scope": "small implementation fixtures; separate from research", "executions": []}
        ledger["executions"].append({"time": datetime.now(timezone.utc).isoformat(), "label": label,
                                     "config": config, **record})
        ledger["total_objective_queries"] = sum(r["objective_queries"] or 0 for r in ledger["executions"])
        atomic_json(LEDGER, ledger)


def legacy_simulator():
    source = subprocess.check_output(["git", "show", "6d5aa0be55715001f7f546e936c524c5998f18a2:src/adaptive_swarms/simulator.py"], cwd=ROOT).decode()
    module = ModuleType("adaptive_swarms._retention_legacy_fixture")
    module.__file__ = str(ROOT / "src/adaptive_swarms/simulator.py")
    module.__package__ = "adaptive_swarms"
    sys.modules[module.__name__] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module


@pytest.mark.parametrize("policy", [None, fixed_retention_response])
def test_absent_hook_is_exact_legacy_numerical_and_record_equivalence(policy):
    label = "baseline" if policy is None else "fixed_four"
    old = recorded_run(legacy_simulator().run_case, SMALL, f"legacy_{label}", policy=policy)
    current = recorded_run(simulator.run_case, SMALL, f"no_hook_{label}", policy=policy)
    assert current == old
    # Includes identical traces, particle response indices, accounting and hashes.
    assert json.dumps(current, sort_keys=True) == json.dumps(old, sort_keys=True)


def particles():
    return [SimpleNamespace(position=[float(i), 0.0], velocity=[float(i - 2), 0.0],
                            best=[float(i), 0.0], best_fitness=value)
            for i, value in enumerate([10.0, 30.0, 30.0, 20.0, 5.0])]


def snapshot():
    return retention_snapshot(particles(), [1.0, 0.0], {"default_radius": 0.5, "relative_fitness_drop": 0.1})


def test_snapshot_immutable_finite_and_rank_direction_order_invariant():
    source = particles();f,s = retention_snapshot(source, [1.0, 0.0], {"default_radius":0.5,"relative_fitness_drop":0.1})
    assert [v["personal_best_rank"] for v in f] == [4,1,1,3,5]
    assert [v["personal_best_rank_fraction"] for v in f] == [.75,0,0,.5,1]
    assert f[2]["speed"] == 0 and f[2]["velocity_alignment"] == 0
    for row in f:
        assert not (set(row) & {"index","id","seed","optimum","offline_error"})
        assert all(math.isfinite(n) for v in row.values() for n in (v if isinstance(v, tuple) else (v,)))
        with pytest.raises(TypeError): row["speed"] = 0
        with pytest.raises(TypeError): row["velocity_normalized"][0] = 0
    with pytest.raises(TypeError): s["diameter"] = 0
    original = [dict(v) for v in f]; source[0].position[0] = 999
    assert [dict(v) for v in f] == original
    order = [3,1,4,0,2];reordered=[particles()[i] for i in order]
    g,t = retention_snapshot(reordered,[1.0,0.0],{"default_radius":0.5,"relative_fitness_drop":0.1})
    assert [dict(v) for v in g] == [original[i] for i in order]
    assert dict(s) == dict(t)


def test_selection_consumes_one_fixed_permutation_independent_of_ties():
    f,s=snapshot();a=selection_rng_for_seed(123);b=selection_rng_for_seed(123)
    heuristic=select_retained_particle(best_memory_priority,f,s,a)
    random=select_retained_particle(random_priority,f,s,b)
    assert a.getstate()==b.getstate()
    assert heuristic["tie_order"]==random["tie_order"]
    assert random["selected_index"]==random["tie_order"][0]
    assert heuristic["selected_index"] in [1,2]
    assert heuristic["agrees_with_heuristic"]
    assert sorted(heuristic["tie_order"])==list(range(5))


def test_completed_refresh_precedes_frozen_scoring_and_movement(monkeypatch):
    from adaptive_swarms import particle_retention
    actual_snapshot=particle_retention.retention_snapshot
    inspected=[]
    def inspect(particles,best,observation):
        before=[(list(p.position),list(p.velocity),p.best_fitness) for p in particles]
        f,s=actual_snapshot(particles,best,observation)
        assert [r['personal_best_fitness'] for r in f]==[p.best_fitness for p in particles]
        assert max(p.best_fitness for p in particles)==next(p.best_fitness for p in particles if p.best==best)
        inspected.append(before)
        return f,s
    monkeypatch.setattr(particle_retention,"retention_snapshot",inspect)
    result=recorded_run(simulator.run_case,SMALL,"hook_best_refreshed_memory",policy=fixed_retention_response,retention_priority=best_memory_priority)
    decisions=[r for r in result['response_log'] if 'retention' in r]
    assert len(decisions)==len(inspected)>1
    assert result['evaluations']==sum(result['evaluation_counts'].values())==SMALL['budget']
    for response,before in zip(decisions,inspected):
        record=response['retention'];chosen=record['selected_index']
        assert record['decided_at_evaluation']==response['detected_at_evaluation']+5
        assert response['relocated_indices']==sorted(set(range(5))-{chosen})
        assert record['selected_before']=={'position':before[chosen][0],'velocity':before[chosen][1]}
        assert record['agrees_with_heuristic']
        if response['completed']:
            assert record['selected_update_reached'] and record['selected_objective_queried']
    examples=[r for r in decisions if 'example' in r['retention']]
    assert len(examples)==1 and examples[0]['completed']
    example=examples[0]['retention']['example']; assert example['criteria']==['first_completed_response']
    # Relocated velocities are retained, whereas the exempt particle has an ordinary PSO update.
    for index in examples[0]['relocated_indices']:
        assert example['particles_before'][index]['velocity']==example['particles_after'][index]['velocity']


def test_invalid_priority_attaches_exact_partial_query_accounting():
    with pytest.raises(RetentionPolicyError) as err:
        recorded_run(simulator.run_case,SMALL,"invalid_score_partial_accounting",policy=fixed_retention_response,
                     retention_priority=lambda p,s: math.nan)
    assert 5 < err.value.objective_queries < SMALL['budget']
    assert err.value.objective_queries==sum(err.value.evaluation_counts.values())
    assert err.value.evaluation_counts['memory']==5


@pytest.mark.parametrize("body", ['import random\ndef retention_priority(particle_features,swarm_features): return random.random()',
    'counter=0\ndef retention_priority(particle_features,swarm_features): return counter',
    'def retention_priority(particle_features,swarm_features,state=[]): return 0',
    'def retention_priority(particle_features,swarm_features): return open("file").read()',
    'def retention_priority(particle_features,swarm_features):\n import os\n return 0'])
def test_loader_rejects_external_state_and_access(body,tmp_path):
    path=tmp_path/'priority.py';path.write_text(body)
    with pytest.raises(RetentionPolicyError) as err:load_retention_priority(path)
    assert err.value.objective_queries==0


def test_loader_accepts_simple_pure_rule_and_math(tmp_path):
    path=tmp_path/'priority.py';path.write_text('import math\ndef retention_priority(particle_features, swarm_features):\n return -particle_features["personal_best_rank"] - math.sqrt(particle_features["speed_normalized"])\n')
    choose=load_retention_priority(path);f,s=snapshot()
    assert math.isfinite(choose(f[0],s))
