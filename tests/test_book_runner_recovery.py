"""Synthetic recovery and freeze checks; no objective or model calls."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("book_runner", Path(__file__).parents[1] / "scripts/run_book_mpso.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class RunnerRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.case = {"config": {"budget": 500000}, "evaluations": 500000,
                     "permanent_quantum": 1, "offline_error": 2.0,
                     "evaluation_counts": {"synthetic": 500000},
                     "initial_environment": {"sha256": "synthetic"}, "environment_changes": []}
        self.path = self.folder / "completed_case.json"
        self.path.write_text(json.dumps(self.case))
        self.ledger = {"attempts": [{"method": "mpso_5_1", "case_index": 0,
                         "status": "running", "reserved_queries": 500000}]}

    def tearDown(self):
        self.temp.cleanup()

    def test_mode_is_part_of_saved_case_identity(self):
        runner.validate_completed_case(self.case, self.case["config"], {"permanent_quantum": 1})
        with self.assertRaisesRegex(ValueError, "quantum mode"):
            runner.validate_completed_case(self.case, self.case["config"], {"permanent_quantum": 0})

    def test_atomic_completed_case_recovers_running_ledger_without_evaluation(self):
        self.assertTrue(runner.recover_completed_artifact(self.ledger, "mpso_5_1", 0, self.case, self.path))
        attempt = self.ledger["attempts"][0]
        self.assertEqual(attempt["actual_queries"], 500000)
        self.assertEqual(attempt["recovery_previous_status"], "running")
        self.assertTrue(attempt["recovered_from_completed_artifact"])
        self.assertFalse(runner.recover_completed_artifact(self.ledger, "mpso_5_1", 0, self.case, self.path))
        self.path.write_text("changed")
        with self.assertRaisesRegex(ValueError, "artifact changed"):
            runner.recover_completed_artifact(self.ledger, "mpso_5_1", 0, self.case, self.path)

    def test_missing_or_duplicate_original_attempt_is_not_invented(self):
        for attempts in ([], self.ledger["attempts"] * 2):
            with self.assertRaisesRegex(ValueError, "exactly one"):
                runner.recover_completed_artifact({"attempts": attempts}, "mpso_5_1", 0, self.case, self.path)

    def test_reserved_budget_mismatch_cannot_recover(self):
        self.ledger["attempts"][0]["reserved_queries"] = 100000
        with self.assertRaisesRegex(ValueError, "reserved objective budget"):
            runner.recover_completed_artifact(self.ledger, "mpso_5_1", 0, self.case, self.path)

    def test_fresh_stage_binds_selection_review_methods_and_analysis(self):
        analysis = self.folder / "analysis.json"
        analysis.write_text('{"bootstrap":20000}')
        selection = {"methods": {"selected": {"sha256": "source", "permanent_quantum": 1}},
                     "analysis_specification": "analysis.json", "analysis_sha256": runner.sha(analysis)}
        (self.folder / "selection.json").write_text(json.dumps(selection))
        (self.folder / "source_review.json").write_text('{"approved_source_sha256":"source"}')
        manifest = {"methods": selection["methods"],
                    "selection_sha256": runner.sha(self.folder / "selection.json"),
                    "source_review_sha256": runner.sha(self.folder / "source_review.json")}
        with patch.object(runner, "ROOT", self.folder):
            runner.verify_fresh_manifest(self.folder, manifest)
            for key in ("selection_sha256", "source_review_sha256", "methods"):
                changed = copy.deepcopy(manifest)
                changed[key] = {} if key == "methods" else "changed"
                with self.assertRaises(ValueError):
                    runner.verify_fresh_manifest(self.folder, changed)
            analysis.write_text("changed")
            with self.assertRaisesRegex(ValueError, "analysis specification"):
                runner.verify_fresh_manifest(self.folder, manifest)


if __name__ == "__main__":
    unittest.main()
