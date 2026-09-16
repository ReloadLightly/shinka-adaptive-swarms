"""Small fixtures for population intervention and exact fixed-five reuse."""
import copy
import math
import random
import unittest
from types import MappingProxyType

from adaptive_swarms import book_mpso, book_population
from adaptive_swarms.population_policy import PopulationPolicyError
from adaptive_swarms.simulator import Particle, Swarm, _validated_config


class PopulationEngineTests(unittest.TestCase):
    query_total = 0

    @classmethod
    def tearDownClass(cls):
        print(f"BOOK_POPULATION_SMALL_FIXTURE_OBJECTIVE_QUERIES={cls.query_total}")

    def execute(self, config, policy=None, engine=book_population.run_case):
        try:
            result = engine(config, policy)
        except Exception as exc:
            type(self).query_total += getattr(exc, "objective_queries", 0)
            raise
        type(self).query_total += result["evaluations"]
        return result

    def test_fixed_five_exact_reference_equivalence_and_cache_diagnostics(self):
        for budget, period in ((2501, 173), (101, 7), (6, 7)):
            cfg = {"budget": budget, "period": period, "trace_interval": 25,
                   "snapshot_interval": 100, "optimizer_seed": 76234}
            prior = self.execute(cfg, engine=book_mpso.run_case)
            new = self.execute(cfg, lambda _: 5)
            compatible = book_population.from_compatible_fixed_five_result(prior)
            for row in (compatible, new):
                row.pop("policy_name")
                row.pop("compatible_engine_origin", None)
                row["population_stats"].pop("diagnostic_origin", None)
            self.assertEqual(compatible, new)

    def test_noop_has_no_random_draws_and_preserves_every_particle(self):
        cfg = _validated_config({"dimension": 2})
        swarm = self.fixture_swarm()
        before = copy.deepcopy(swarm)
        rng = random.Random(96)
        rng_before = rng.getstate()
        event = book_population.resize_neutrals(swarm, 5, rng, cfg)
        self.assertEqual(event["resize"], "none")
        self.assertEqual(swarm, before)
        self.assertEqual(rng.getstate(), rng_before)

    @staticmethod
    def fixture_swarm():
        particles = [Particle([float(i), 1.0], [i + .1, .2], [float(i), 0.0], float(i), 0.0)
                     for i in range(6)]
        return Swarm(1, particles, list(particles[-1].best), particles[-1].best_fitness)

    def test_shrink_worst_latest_memory_ties_last_order_never_permanent(self):
        swarm = self.fixture_swarm()
        swarm.particles[1].best_fitness = -10.0
        swarm.particles[3].best_fitness = -10.0
        swarm.particles[-1].best_fitness = -20.0
        before = list(swarm.particles)
        frozen = copy.deepcopy(before)
        event = book_population.resize_neutrals(swarm, 2, random.Random(7), _validated_config({"dimension": 2}))
        self.assertEqual(event["removed_neutral_index"], 3)
        self.assertEqual(event["neutral_count_after"], 4)
        self.assertEqual(swarm.particles, before[:3] + before[4:])
        self.assertEqual(before, frozen)
        self.assertIs(swarm.particles[-1], before[-1])
        self.assertEqual(swarm.best_fitness, 4.0)
        self.assertEqual(swarm.best, before[4].best)

    def test_grow_only_velocity_initialized_survivors_unchanged(self):
        swarm = self.fixture_swarm()
        old = list(swarm.particles)
        frozen = copy.deepcopy(old)
        rng, oracle = random.Random(17), random.Random(17)
        event = book_population.resize_neutrals(swarm, 8, rng, _validated_config({"dimension": 2}))
        new = swarm.particles[-2]
        self.assertEqual(event["neutral_count_after"], 6)
        self.assertEqual(swarm.particles[:-2], old[:-1])
        self.assertIs(swarm.particles[-1], old[-1])
        self.assertEqual(old, frozen)
        self.assertIsNone(new.best)
        self.assertIsNone(new.best_fitness)
        self.assertIsNone(new.fitness)
        self.assertEqual(new.velocity, [oracle.uniform(-50, 50) for _ in range(2)])
        self.assertEqual(rng.getstate(), oracle.getstate())

    def test_neutral_only_geometry_uses_all_variable_neutrals(self):
        swarm = self.fixture_swarm()
        swarm.particles[-1].position = [1e9, 0.0]
        self.assertEqual(book_population.neutral_diameter(swarm), 4.0)
        swarm.particles.insert(-1, Particle([30.0, 1.0], [0.0, 0.0]))
        self.assertEqual(book_population.neutral_diameter(swarm), 30.0)

    def test_population_call_after_all_memory_refresh_before_movement(self):
        seen = []
        def inspect(observation):
            self.assertIsInstance(observation, MappingProxyType)
            self.assertTrue(observation["change_detected"])
            self.assertEqual(observation["evaluations_since_detected_change"], observation["swarm_size"])
            self.assertEqual(observation["updates_since_detected_change"], 0)
            self.assertFalse(set(observation) & {"npeaks", "optimum", "offline_error", "environment_seed", "period"})
            self.assertTrue(all(math.isfinite(value) for value in observation.values()))
            with self.assertRaises(TypeError):
                observation["neutral_count"] = 99
            seen.append(dict(observation))
            return 7
        result = self.execute({"budget": 1901, "period": 103, "trace_interval": 1}, inspect)
        stats = result["population_stats"]
        self.assertEqual(len(seen), stats["policy_calls"])
        self.assertEqual(len(seen), len(result["response_log"]))
        self.assertGreater(stats["additions"], 0)
        self.assertEqual(stats["removals"], 0)
        for row in result["response_log"]:
            self.assertLessEqual(abs(row["neutral_count_after"] - row["neutral_count_before"]), 1)
            self.assertEqual(row["decision"]["temporary_quantum_count"], row["neutral_count_after"])
            self.assertEqual(row["selected_neutral_indices"], list(range(row["neutral_count_after"])))
            self.assertEqual(row["decided_at_evaluation"] - row["detected_at_evaluation"], row["neutral_count_before"] + 1)
        self.assertTrue(any(row["neutral_count_after"] == 7 for row in result["response_log"]))
        self.assertNotIn("population_initialization", result["evaluation_counts"])
        for example in stats["decision_examples"]:
            for step in example["particle_updates"]:
                self.assertEqual(step["kind"] == "permanent_quantum", step["index"] == example["neutral_count_after"])
                if example["observation"]["change_detected"]:
                    self.assertNotEqual(step["kind"], "ordinary")
                    self.assertEqual(step["velocity"], example["particles_before"][step["index"]]["velocity"])

    def test_shrink_grow_pairing_and_exact_budget_partial_operations(self):
        cases = []
        for target in (2, 8):
            result = self.execute({"budget": 1303, "period": 103, "trace_interval": 100}, lambda _: target)
            cases.append(result)
            self.assertEqual(sum(result["evaluation_counts"].values()), 1303)
            self.assertEqual(result["evaluations"], 1303)
            self.assertTrue(all(2 <= int(key) <= 8 for key, count in result["population_stats"]["realized_neutral_count_histogram"].items() if count))
        self.assertEqual(cases[0]["initial_environment"], cases[1]["initial_environment"])
        self.assertEqual([r["next_environment"] for r in cases[0]["environment_changes"]],
                         [r["next_environment"] for r in cases[1]["environment_changes"]])
        self.assertGreater(cases[0]["population_stats"]["removals"], 0)
        self.assertGreater(cases[1]["population_stats"]["additions"], 0)
        for budget in (1, 5, 7, 31, 32, 33, 39):
            result = self.execute({"budget": budget, "period": 19}, lambda _: 8)
            self.assertEqual(result["evaluations"], budget)
            self.assertEqual(sum(result["evaluation_counts"].values()), budget)

    def test_invalid_target_is_recorded_failure(self):
        for invalid in (True, 2.0, 1, 9, math.nan):
            with self.assertRaises(PopulationPolicyError) as caught:
                self.execute({"budget": 300, "period": 31}, lambda _: invalid)
            self.assertGreater(caught.exception.objective_queries, 31)
            self.assertEqual(caught.exception.objective_queries, sum(caught.exception.evaluation_counts.values()))

    def test_instrumentation_does_not_change_numerical_outcome(self):
        cfg = {"budget": 901, "period": 97, "optimizer_seed": 8859}
        a = self.execute({**cfg, "trace_interval": 25}, lambda _: 3)
        b = self.execute({**cfg, "trace_interval": 100}, lambda _: 3)
        for row in (a, b):
            row.pop("trace")
            row["config"].pop("trace_interval")
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
