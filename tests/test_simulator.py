"""Focused tests of research-validity requirements and the upstream defect."""

import ast
import json
import math
import random
import unittest
from pathlib import Path
from types import SimpleNamespace

from adaptive_swarms.policies import book_response, no_relocation_response
from adaptive_swarms.simulator import _MPB, run_case, sample_uvd


class SimulatorTests(unittest.TestCase):
    def test_upstream_distribution_selector_bug_is_present(self):
        source = Path(__file__).resolve().parents[1] / "vendor/deap/multiswarm.py"
        tree = ast.parse(source.read_text())
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                        and n.name == "convertQuantum")
        namespace = {"random": random.Random(9), "math": math}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), "exec"), namespace)

        class DummyParticle(list):
            pass

        for distribution in ("uvd", "gaussian", "nuvd"):
            particle = DummyParticle([99.0, 99.0])
            particle.fitness = SimpleNamespace(values=(1.0,))
            particle.bestfit = SimpleNamespace(values=(1.0,))
            particle.best = [99.0, 99.0]
            namespace["convertQuantum"]([particle], 0.5, [0.0, 0.0], distribution)
            self.assertEqual(particle, [99.0, 99.0])
            self.assertIsNone(particle.best)

    def test_uvd_relocates_and_obeys_uniform_volume_distribution(self):
        rng = random.Random(5)
        center = [10.0, 20.0, 30.0]
        transformed_radii = []
        for _ in range(4000):
            point = sample_uvd(rng, center, 2.0)
            radius = math.dist(point, center)
            self.assertLessEqual(radius, 2.0 + 1e-12)
            transformed_radii.append((radius / 2.0) ** 3)
        self.assertAlmostEqual(sum(transformed_radii) / len(transformed_radii), 0.5, delta=0.025)
        self.assertEqual(sample_uvd(rng, center, 0.0), center)

    def test_every_access_uses_the_exact_budget(self):
        for budget in (1, 5, 6, 37, 100, 101, 503):
            result = run_case({"budget": budget, "period": 100, "trace_interval": 0})
            self.assertEqual(result["evaluations"], budget)
            self.assertEqual(sum(result["evaluation_counts"].values()), budget)
            self.assertEqual(result["trace"][-1]["evaluations"], budget)
            self.assertTrue(math.isfinite(result["offline_error"]))
        result = run_case({"budget": 1500, "period": 200})
        for kind in ("detection", "memory", "particle", "initialization"):
            self.assertGreater(result["evaluation_counts"][kind], 0)

    def test_environment_history_is_independent_of_policy_random_draws(self):
        cfg = {"budget": 1500, "period": 200, "environment_seed": 17}
        a = run_case(cfg, book_response)
        b = run_case({**cfg, "optimizer_seed": 900}, no_relocation_response)
        self.assertEqual(a["initial_environment"], b["initial_environment"])
        self.assertEqual([e["next_environment"]["sha256"] for e in a["environment_changes"]],
                         [e["next_environment"]["sha256"] for e in b["environment_changes"]])
        self.assertNotEqual(a["offline_error"], b["offline_error"])

    def test_offline_error_resets_on_first_evaluation_after_change(self):
        cfg = dict(_MPB.SCENARIO_2, period=2, lambda_=0.0)
        landscape = _MPB.MovingPeaks(dim=2, random=random.Random(1), **cfg)
        point = list(landscape.globalMaximum()[1])
        landscape(point)
        landscape(point)
        self.assertEqual(landscape.currentError(), 0.0)
        new_optimum = landscape.globalMaximum()[0]
        value = landscape([1000.0, 1000.0])[0]
        expected = abs(value - new_optimum)
        self.assertGreater(expected, 0.0)
        self.assertAlmostEqual(landscape.currentError(), expected)
        self.assertAlmostEqual(landscape.offlineError(), expected / 3)

    def test_trace_integrates_to_offline_error(self):
        result = run_case({"budget": 731, "period": 100, "trace_interval": 1})
        self.assertAlmostEqual(result["offline_error"],
                               sum(row["current_error"] for row in result["trace"]) / 731)
        completed = sum(e["environment_offline_error"] * e["environment_evaluations"]
                        for e in result["environment_changes"])
        partial = result["partial_environment"]
        self.assertAlmostEqual(result["offline_error"],
                               (completed + partial["offline_error"] * partial["evaluations"]) / 731)

    def test_policy_observations_and_json_output(self):
        observations = []

        def response(observation):
            observations.append(observation)
            return book_response(observation)

        events = []
        result = run_case({"budget": 1000, "period": 200, "snapshot_interval": 250},
                          response, events.append)
        self.assertTrue(observations)
        for observation in observations:
            self.assertFalse(set(observation) & {"optimum", "peaks", "environment_seed",
                                                "optimizer_seed", "offline_error"})
        self.assertEqual(events[0]["event"], "run_started")
        self.assertEqual(events[-1]["event"], "run_completed")
        self.assertEqual(sum(e["event"] == "environment_change" for e in events), 5)
        self.assertTrue(result["snapshots"])
        json.dumps(result, allow_nan=False)

    def test_static_case_has_no_response(self):
        result = run_case({"budget": 500, "period": 0})
        self.assertEqual(result["response_log"], [])
        self.assertEqual(result["environment_changes"], [])
        self.assertEqual(result["environments_evaluated"], 1)


if __name__ == "__main__":
    unittest.main()
