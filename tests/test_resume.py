import copy
import json
import tempfile
import unittest
from pathlib import Path
from physicslab.broker import ResearchSession
from test_core import example_plan


ROOT = Path(__file__).resolve().parents[1]


class ResumeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.settings = json.loads((ROOT / "configs/runtime.json").read_text())

    def tearDown(self): self.temp.cleanup()

    def test_resume_retains_plan_and_spend_and_rotates_capabilities(self):
        old = ResearchSession(self.root, self.settings)
        old.kind = "engineering_contract_check"
        old.call("planner", "record_plan", {"plan": example_plan()})
        rid = old.ledger.reserve("tool")
        old.ledger.settle(rid, 0, 0)
        restored = ResearchSession(self.root, self.settings, resume_id=old.sid)
        self.assertEqual(restored.plans, old.plans)
        self.assertEqual(restored.stage, "experiment")
        self.assertEqual(restored.kind, "engineering_contract_check")
        self.assertFalse(set(restored.capabilities) & set(old.capabilities))
        with restored.ledger.connect() as db:
            self.assertEqual(db.execute("SELECT SUM(calls) FROM reservations").fetchone()[0], 1)

    def test_unsettled_work_blocks_resume_without_resetting_budget(self):
        old = ResearchSession(self.root, self.settings)
        old.ledger.reserve("tool")
        with self.assertRaisesRegex(RuntimeError, "Unsettled work"):
            ResearchSession(self.root, self.settings, resume_id=old.sid)
        self.assertEqual(len(old.ledger.unsettled()), 1)

    def test_resume_cannot_change_controls_or_limits(self):
        old = ResearchSession(self.root, self.settings)
        changed = copy.deepcopy(self.settings)
        changed["max_tool_runs"] += 1
        with self.assertRaisesRegex(ValueError, "runtime changed"):
            ResearchSession(self.root, changed, resume_id=old.sid)

    def test_path_traversal_and_missing_sessions_are_rejected(self):
        for sid in ("../../secret", "session-missing"):
            with self.assertRaises(ValueError): ResearchSession(self.root, self.settings, resume_id=sid)
