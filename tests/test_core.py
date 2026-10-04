import concurrent.futures
import copy
import csv
import json
import math
import tempfile
import unittest
from pathlib import Path
from physicslab.contracts import validate_plan, validate_analysis
from physicslab.evaluator import evaluate_csv
from physicslab.ledger import Ledger
from physicslab.diagnostics import present


def example_plan():
    return {"id": "engineering-fixture", "hypothesis": "Test-only decision", "falsification": "No gain", "selection_reason": "Schema verification only",
            "candidates": [{"id": "logs", "learning_value": "Check logs", "feasibility": "Local", "estimated_tool_runs": 2},
                           {"id": "parser", "learning_value": "Check information loss", "feasibility": "Local", "estimated_tool_runs": 2}],
            "selected_candidate": "logs", "runs": [{"task_id": "cooling-sign-v1", "diagnostics": mode, "replicate": 0, "max_attempts": 3} for mode in ("raw", "structured")]}


class ContractsTest(unittest.TestCase):
    def test_evaluation_cannot_be_redefined(self):
        plan = example_plan()
        validate_plan(plan)
        plan["runs"][0]["tolerance"] = 100
        with self.assertRaises(ValueError): validate_plan(plan)

    def test_budget_controls_matched(self):
        plan = example_plan()
        plan["runs"][1]["max_attempts"] = 2
        with self.assertRaises(ValueError): validate_plan(plan)

    def test_analysis_requires_existing_evidence(self):
        plan = example_plan()
        followup = copy.deepcopy(plan); followup["id"] = "followup"
        analysis = {"support": "inconclusive", "evidence_run_ids": ["invented"], "limitations": "Few runs", "adjustment_reason": "Repeat", "repeat_reason": "Noise", "followup": followup}
        with self.assertRaises(ValueError): validate_analysis(analysis, ["real-run"], plan)
        analysis["evidence_run_ids"] = ["real-run"]
        validate_analysis(analysis, ["real-run"], plan)

    def test_structured_log_does_not_invent_a_repair(self):
        result = present("Compiler running\nError: undefined x\n", "structured")
        self.assertEqual(result["diagnostic_lines"], ["Error: undefined x"])
        self.assertEqual(result["omitted_lines"], 1)
        self.assertTrue(result["raw_available"])
        self.assertTrue(present("success", "structured")["empty_diagnostic"])


class AccountingTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.limits = {"max_tool_runs": 2, "max_model_calls": 2, "max_model_tokens": 100, "max_total_usd": 1, "model_calls_authorized": False}
        self.ledger = Ledger(Path(self.temp.name) / "ledger.sqlite", self.limits)

    def tearDown(self): self.temp.cleanup()

    def test_no_model_calls_without_explicit_authorization(self):
        with self.assertRaises(PermissionError): self.ledger.reserve("model")

    def test_concurrent_tool_reservations_cannot_overspend(self):
        def reserve(_):
            try: return self.ledger.reserve("tool")
            except RuntimeError: return None
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(reserve, range(8)))
        self.assertEqual(sum(r is not None for r in results), 2)

    def test_unknown_usage_stays_unknown_and_reserves_full_limit(self):
        self.limits["model_calls_authorized"] = True
        rid = self.ledger.reserve("model", tokens=100, usd=1)
        self.ledger.settle(rid)
        self.assertIsNone(self.ledger.events()[0]["payload"]["tokens"])
        with self.assertRaises(RuntimeError): self.ledger.reserve("model", tokens=1)


class EvaluatorTest(unittest.TestCase):
    def test_analytic_solution_passes_and_wrong_sign_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "result.csv"
            for sign, expected in ((-1, "passed"), (1, "failed")):
                with path.open("w", newline="") as stream:
                    writer = csv.writer(stream); writer.writerow(["time", "T"])
                    writer.writerows((t, 293.15 + 40 * math.exp(sign * t / 100)) for t in range(301))
                self.assertEqual(evaluate_csv(path)["status"], expected)

    def test_nonfinite_and_missing_trajectory_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "result.csv"
            self.assertEqual(evaluate_csv(path)["status"], "failed")
            path.write_text("time,T\n" + "0,nan\n" * 10)
            self.assertEqual(evaluate_csv(path)["status"], "failed")


if __name__ == "__main__": unittest.main()
