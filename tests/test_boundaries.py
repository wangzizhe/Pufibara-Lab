import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from physicslab.broker import ResearchSession
from physicslab.runner import DockerRunner
from physicslab.evaluator import evaluate_csv
from test_core import example_plan


ROOT = Path(__file__).resolve().parents[1]


class BoundaryTest(unittest.TestCase):
    def test_model_advertisement_omits_denied_generic_tools(self):
        from physicslab.codex_harness import scoped_tool_specs, check_dispatch
        names = ['task', 'attempt', 'raw_log', 'sys_session_send', 'sys_read_inbox', 'sys_session_info',
                 'sys_os_exec', 'sys_session_history', 'sys_session_share', 'web_search']
        selected = scoped_tool_specs([{'name':name,'parameters':{'type':'object'}} for name in names])
        self.assertEqual([tool['name'] for tool in selected], names[:5])
        check_dispatch('sys_read_inbox',{})
        for name in names[5:]:
            with self.assertRaises(PermissionError):
                check_dispatch(name,{})

    def test_initialization_protocol_requires_observed_baseline(self):
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            settings = json.loads((ROOT / 'configs/runtime-enhancement.json').read_text())
            session = ResearchSession(root, settings)
            session.task = Mock(return_value={'baseline_first':True,'source':'public baseline'})
            session.execute = Mock(return_value={'run_id':'run-baseline','status':'completed','feedback':{'error':'init failed'}})
            session.trials.append({'trial_id':'trial-init','finished':False,'attempts':[],
                                   'config':{'task_id':'cooling-init-v1','max_attempts':2,'diagnostics':'raw'}})
            with self.assertRaises(ValueError):
                session.call('modeler','attempt',{'trial_id':'trial-init','source':'blind correction'})
            session.execute.assert_not_called()
            first = session.call('modeler','attempt',{'trial_id':'trial-init','source':'public baseline'})
            self.assertEqual(first['attempts_remaining'],1)
            self.assertEqual(first['feedback']['error'],'init failed')
            session.call('modeler','attempt',{'trial_id':'trial-init','source':'feedback-informed correction'})
            with self.assertRaises(RuntimeError):
                session.call('modeler','attempt',{'trial_id':'trial-init','source':'extra correction'})

    def test_analyst_evidence_is_session_scoped_and_omits_answers(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            settings = json.loads((ROOT / "configs/runtime.json").read_text())
            session = ResearchSession(root, settings)
            trial = {"trial_id": "trial-owned", "finished": True, "attempts": ["run-owned"],
                     "source": "private submitted source", "config": {"diagnostics": "structured"},
                     "final_run_id": "run-final", "evaluation": {"all_passed": True}, "tool_seconds": 2}
            session.trials.append(trial)
            folder = root / "evidence/runs/run-owned"
            folder.mkdir(parents=True)
            raw = "Error: overdetermined initialization\n" + "x" * 40000
            record = {"status": "completed", "seconds": 1, "mechanism": "structured", "raw": raw,
                      "feedback": {"diagnostic_lines": ["Error: overdetermined initialization"], "omitted_lines": 1},
                      "evaluation": {"hidden_answer": "synthetic oracle"}}
            (folder / "result.json").write_text(json.dumps(record))
            self.assertEqual(session.call("analyst", "status", {})["trials"][0]["attempt_count"], 1)
            evidence = session.call("analyst", "trial_evidence", {"trial_id": "trial-owned"})
            self.assertEqual(evidence["attempt_count"], 1)
            self.assertNotIn("raw", evidence["attempts"][0])
            self.assertNotIn("synthetic oracle", json.dumps(evidence))
            self.assertNotIn("private submitted source", json.dumps(evidence))
            logs = session.call("analyst", "trial_evidence", {"trial_id": "trial-owned", "include_raw": True})
            self.assertTrue(logs["attempts"][0]["raw_truncated"])
            self.assertEqual(len(logs["attempts"][0]["raw"]), 32000)
            for role in ("modeler", "planner", "executor", "coordinator"):
                with self.assertRaises(PermissionError):
                    session.call(role, "trial_evidence", {"trial_id": "trial-owned"})
            with self.assertRaises(PermissionError):
                session.call("analyst", "trial_evidence", {"trial_id": "trial-foreign"})
            trial["finished"] = False
            with self.assertRaises(PermissionError):
                session.call("analyst", "trial_evidence", {"trial_id": "trial-owned"})

    def test_role_acl_rejects_generic_shell_and_evaluator_access(self):
        with tempfile.TemporaryDirectory() as temp:
            settings = json.loads((ROOT / "configs/runtime.json").read_text())
            session = ResearchSession(Path(temp), settings)
            for role in ("planner", "modeler", "analyst"):
                for action in ("read_file", "shell", "evaluate", "set_limits"):
                    with self.assertRaises(PermissionError): session.call(role, action, {"path": "evaluator.py"})
            with self.assertRaises(PermissionError): session.call("modeler", "status", {})

    def test_modeler_cannot_query_other_trial_logs_or_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            settings = json.loads((ROOT / "configs/runtime.json").read_text())
            session = ResearchSession(Path(temp), settings)
            session.trials.append({"trial_id": "trial-test", "finished": False, "attempts": ["run-owned"]})
            with self.assertRaises(PermissionError): session.call("modeler", "raw_log", {"trial_id": "trial-test", "run_id": "run-other"})
            with self.assertRaises(ValueError): session.call("modeler", "raw_log", {"trial_id": "trial-test", "run_id": "../../oracle"})

    def test_final_artifact_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "synthetic-answer"
            target.write_text("do-not-read")
            output = Path(temp) / "trajectory.csv"
            output.symlink_to(target)
            result = evaluate_csv(output)
            self.assertEqual(result["status"], "failed")
            self.assertIn("Symlink", result["reason"])

    def test_timeout_and_log_limit_are_actual_process_bounds(self):
        with tempfile.TemporaryDirectory() as temp:
            settings = json.loads((ROOT / "configs/runtime.json").read_text())
            settings["docker_executable"] = "/usr/bin/true"  # Cleanup stub; no real Docker or scientific run.
            settings["max_tool_seconds"] = 0.1
            runner = DockerRunner(Path(temp), settings)
            result = runner.call([sys.executable, "-c", "import time; time.sleep(2)"], "unit-timeout")
            self.assertEqual(result["status"], "timeout")
            settings["max_tool_seconds"] = 2
            result = runner.call([sys.executable, "-c", "print('x'*2000000)"], "unit-output")
            self.assertEqual(result["status"], "output_limit")
            self.assertLessEqual(len(result["raw"]), 1000000)
