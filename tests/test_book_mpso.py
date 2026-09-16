"""Focused source/ordering/accounting risks for the separate chapter path."""
import json
import math
import random
import unittest
from pathlib import Path
from types import MappingProxyType

from adaptive_swarms import book_mpso
from adaptive_swarms.book_schedule import BookScheduleError, load_schedule
from adaptive_swarms.simulator import Particle, Swarm, _validated_config, run_case as historical_run


class ChapterMPSOTests(unittest.TestCase):
    query_total = 0

    @classmethod
    def tearDownClass(cls):
        print(f"CHAPTER_MPSO_SMALL_FIXTURE_OBJECTIVE_QUERIES={cls.query_total}")

    def execute(self, config, schedule=None, **kwargs):
        try:
            result = book_mpso.run_case(config, schedule, **kwargs)
        except Exception as exc:
            type(self).query_total += getattr(exc, "objective_queries", 0)
            raise
        type(self).query_total += result["evaluations"]
        return result

    def test_quantum_replaces_pso_and_retains_velocity(self):
        cfg = _validated_config({"dimension": 2})
        particle = Particle([12.0, 5.0], [9.0, -3.0], [3.0, 4.0], 0.0)
        center = [30.0, 40.0]
        original_velocity = list(particle.velocity)
        book_mpso.move_particle(particle, center, random.Random(11), cfg, True)
        self.assertLessEqual(math.dist(particle.position, center), 0.5)
        self.assertEqual(particle.velocity, original_velocity)
        sampled = list(particle.position)
        book_mpso.move_particle(particle, center, random.Random(11), cfg, False)
        self.assertNotEqual(particle.velocity, original_velocity)
        self.assertEqual(particle.position, [x + v for x, v in zip(sampled, particle.velocity)])

    def test_convergence_excludes_permanent_quantum_role(self):
        neutrals = [Particle([float(i), 0.0], [0.0, 0.0]) for i in range(5)]
        swarm = Swarm(0, neutrals + [Particle([10000.0, 10000.0], [0.0, 0.0])])
        self.assertEqual(book_mpso.neutral_diameter(swarm), 4.0)
        swarm.particles[0].position[0] = -10.0
        self.assertEqual(book_mpso.neutral_diameter(swarm), 14.0)

    def test_exact_budgets_including_partial_refresh_and_initialization(self):
        for permanent in (0, 1):
            for budget in (1, 5, 6, 7, 100, 503):
                result = self.execute({"budget": budget, "period": 31, "trace_interval": 0},
                                      permanent_quantum=permanent)
                self.assertEqual(result["evaluations"], budget)
                self.assertEqual(sum(result["evaluation_counts"].values()), budget)
                self.assertTrue(math.isfinite(result["offline_error"]))
                self.assertEqual(result["trace"][-1]["evaluations"], budget)

    def test_permanent_and_temporary_roles_share_memory_refresh_and_attractors(self):
        result = self.execute({"budget": 1700, "period": 97, "trace_interval": 1})
        stats = result["schedule_stats"]
        self.assertGreater(result["evaluation_counts"]["permanent_quantum"], 0)
        self.assertGreater(stats["shared_best_improvements"]["permanent_quantum"]["count"], 0)
        self.assertEqual(stats["count_histogram"]["5"], stats["detected_change_updates"])
        self.assertEqual(stats["count_histogram"]["0"], stats["updates"] - stats["detected_change_updates"])
        self.assertEqual(stats["selection_permutations"], stats["updates"])
        for row in result["response_log"]:
            self.assertEqual(row["decided_at_evaluation"] - row["detected_at_evaluation"], 6)
            self.assertEqual(row["selected_neutral_indices"], list(range(5)))
            self.assertTrue(row["observation"]["change_detected"])
            self.assertEqual(row["observation"]["updates_since_detected_change"], 0)
        for example in stats["decision_examples"]:
            self.assertEqual(len(example["particles_before"]), 6)
            for particle_update in example["particle_updates"]:
                i = particle_update["index"]
                if particle_update["kind"] != "ordinary":
                    self.assertLessEqual(math.dist(particle_update["position"], particle_update["center"]), 0.5 + 1e-12)
                    self.assertEqual(particle_update["velocity"], example["particles_before"][i]["velocity"])
                self.assertEqual(particle_update["kind"] == "permanent_quantum", i == 5)
        self.assertAlmostEqual(result["offline_error"], sum(r["current_error"] for r in result["trace"]) / 1700)

    def test_seed_source_and_standalone_reference_are_identical(self):
        source = Path(__file__).parents[1] / "tasks/book_mpso_schedule_v1/initial.py"
        if not source.exists():
            self.fail("Native seed source must be present for prospective equivalence check")
        candidate = load_schedule(source)
        cfg = {"budget": 1100, "period": 100, "trace_interval": 100}
        reference = self.execute(cfg)
        seed = self.execute(cfg, candidate)
        reference.pop("policy_name")
        seed.pop("policy_name")
        self.assertEqual(reference, seed)

    def test_environment_pairing_and_count_independent_selection_stream(self):
        cfg = {"budget": 1100, "period": 100, "environment_seed": 812}
        zero = self.execute(cfg, lambda _: 0, permanent_quantum=0)
        full = self.execute(cfg, lambda _: 5, permanent_quantum=1)
        self.assertEqual(zero["initial_environment"], full["initial_environment"])
        self.assertEqual([e["next_environment"]["sha256"] for e in zero["environment_changes"]],
                         [e["next_environment"]["sha256"] for e in full["environment_changes"]])
        a = zero["schedule_stats"]["decision_examples"][0]["selection_permutation"]
        b = full["schedule_stats"]["decision_examples"][0]["selection_permutation"]
        self.assertEqual(a, b)
        self.assertEqual(zero["schedule_stats"]["requested_neutral_conversions"], 0)
        self.assertEqual(full["schedule_stats"]["requested_neutral_conversions"], 5 * full["schedule_stats"]["updates"])

    def test_observation_is_immutable_public_and_after_refresh(self):
        seen = []
        def inspect(observation):
            self.assertIsInstance(observation, MappingProxyType)
            with self.assertRaises(TypeError):
                observation["change_detected"] = False
            self.assertFalse(set(observation) & {"environment_seed", "optimizer_seed", "offline_error", "optimum", "peaks", "period"})
            self.assertTrue(all(isinstance(x, (int, float, bool)) and math.isfinite(x) for x in observation.values()))
            seen.append(dict(observation))
            return book_mpso.published_schedule(observation)
        result = self.execute({"budget": 901, "period": 101}, inspect)
        self.assertEqual(len(seen), result["schedule_stats"]["updates"])
        changed = [row for row in seen if row["change_detected"]]
        self.assertTrue(changed)
        self.assertTrue(all(row["evaluations_since_detected_change"] == 6 for row in changed))

    def test_invalid_candidate_is_failure_with_exact_consumed_queries(self):
        for invalid in (True, 2.0, -1, 6, float("nan")):
            with self.assertRaises(BookScheduleError) as caught:
                self.execute({"budget": 100}, lambda _: invalid)
            exc = caught.exception
            self.assertGreater(exc.objective_queries, 0)
            self.assertLess(exc.objective_queries, 100)
            self.assertEqual(sum(exc.evaluation_counts.values()), exc.objective_queries)
        def crash(_):
            raise RuntimeError("candidate failure")
        with self.assertRaisesRegex(RuntimeError, "candidate failure") as caught:
            self.execute({"budget": 100}, crash)
        self.assertEqual(sum(caught.exception.evaluation_counts.values()), caught.exception.objective_queries)

    def test_trace_resolution_is_observational_only_and_historical_path_unchanged(self):
        cfg = {"budget": 803, "period": 101, "optimizer_seed": 631}
        before = historical_run(cfg)
        type(self).query_total += before["evaluations"]
        sparse = self.execute({**cfg, "trace_interval": 100})
        dense = self.execute({**cfg, "trace_interval": 25})
        for result in (sparse, dense):
            result.pop("trace")
            result["config"].pop("trace_interval")
        self.assertEqual(sparse, dense)
        after = historical_run(cfg)
        type(self).query_total += after["evaluations"]
        self.assertEqual(before, after)
        self.assertEqual(json.loads(json.dumps(after)), after)


if __name__ == "__main__":
    unittest.main()
