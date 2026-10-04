import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys

from physicslab.request_budget import RequestBudget, SubscriptionRequestGate


class RequestBudgetTests(unittest.TestCase):
    def test_first_request_starts_shared_clock_without_reset_on_resume(self):
        from physicslab.request_budget import SharedRequestBudget
        import json
        with tempfile.TemporaryDirectory() as folder:
            now = [100]
            args = dict(max_requests=2, wall_seconds=60, journal=Path(folder)/'calls.jsonl',
                        clock=lambda:now[0], wall_clock=lambda:now[0], start_on_first_request=True)
            parent = SharedRequestBudget(**args)
            child = SharedRequestBudget(**args, resume=True)
            try:
                now[0] = 1000
                self.assertEqual(parent.refresh_deadline(), float('inf'))
                self.assertTrue(child.reserve())
                self.assertEqual(parent.refresh_deadline(), 1060)
                now[0] = 1059
                self.assertTrue(parent.reserve())
                now[0] = 1060
                self.assertFalse(child.reserve())
                rows = [json.loads(s) for s in args['journal'].read_text().splitlines()]
                self.assertEqual(sum(r['event']=='budget_started' for r in rows),1)
                self.assertEqual(rows[-1]['reason'],'time_limit')
            finally:
                parent.close(); child.close()

    def test_separate_processes_share_one_call_ceiling(self):
        with tempfile.TemporaryDirectory() as folder:
            journal = Path(folder) / "requests.jsonl"
            budget = RequestBudget(max_requests=12, wall_seconds=900, journal=journal,
                                   start_on_first_request=True)
            budget.close()
            code = "from pathlib import Path; from physicslab.request_budget import SharedRequestBudget; import sys; b=SharedRequestBudget(max_requests=12,wall_seconds=900,journal=Path(sys.argv[1]),resume=True); print(int(b.reserve())); b.close()"
            processes = [subprocess.Popen([sys.executable, "-c", code, str(journal)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(20)]
            outputs = [process.communicate(timeout=10) for process in processes]
            self.assertTrue(all(process.returncode == 0 for process in processes), outputs)
            self.assertEqual(sum(int(out[0].strip()) for out in outputs), 12)
            import json
            rows = [json.loads(line) for line in journal.read_text().splitlines()]
            self.assertEqual(sum(row['event']=='budget_started' for row in rows),1)

    def test_creator_appends_after_child_reservations(self):
        from physicslab.request_budget import SharedRequestBudget
        import json
        with tempfile.TemporaryDirectory() as folder:
            journal = Path(folder) / "requests.jsonl"
            parent = SharedRequestBudget(max_requests=3, wall_seconds=900, journal=journal)
            child = SharedRequestBudget(max_requests=3, wall_seconds=900, journal=journal, resume=True)
            try:
                self.assertTrue(parent.reserve())
                self.assertTrue(child.reserve())
                self.assertTrue(parent.reserve())
                self.assertFalse(child.reserve())
                records = [json.loads(line) for line in journal.read_text().splitlines()]
                self.assertEqual([r["reserved_requests"] for r in records[1:]], [1,2,3,3])
            finally:
                parent.close()
                child.close()

    def test_resume_keeps_consumed_requests_and_deadline(self):
        with tempfile.TemporaryDirectory() as folder:
            now = [0]
            journal = Path(folder) / "requests.jsonl"
            budget = RequestBudget(max_requests=2, wall_seconds=900, journal=journal,
                clock=lambda: now[0], wall_clock=lambda: now[0])
            self.assertTrue(budget.reserve())
            budget.close()
            now[0] = 899
            resumed = RequestBudget(max_requests=2, wall_seconds=900, journal=journal,
                resume=True, clock=lambda: now[0], wall_clock=lambda: now[0])
            self.assertEqual(resumed.deadline, 900)
            self.assertTrue(resumed.reserve())
            self.assertFalse(resumed.reserve())
            now[0] = 900
            self.assertFalse(resumed.reserve())
            resumed.close()

    def test_concurrent_reservations_stop_before_thirteenth_request(self):
        with tempfile.TemporaryDirectory() as folder:
            budget = RequestBudget(max_requests=12, wall_seconds=900,
                journal=Path(folder) / "requests.jsonl")
            try:
                with ThreadPoolExecutor(max_workers=16) as pool:
                    results = list(pool.map(lambda _: budget.reserve(), range(32)))
                self.assertEqual(sum(results), 12)
                self.assertEqual(budget.requests, 12)
            finally:
                budget.close()

    def test_time_limit_and_journal_reuse_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            now = [0]
            journal = Path(folder) / "requests.jsonl"
            budget = RequestBudget(max_requests=12, wall_seconds=900,
                journal=journal, clock=lambda: now[0])
            now[0] = 900
            self.assertFalse(budget.reserve())
            budget.close()
            with self.assertRaises(FileExistsError):
                RequestBudget(max_requests=12, wall_seconds=900, journal=journal)

    def test_unknown_subscription_or_alternate_route_cannot_consume(self):
        with tempfile.TemporaryDirectory() as folder:
            budget = RequestBudget(max_requests=12, wall_seconds=900,
                journal=Path(folder) / "requests.jsonl")
            try:
                gate = SubscriptionRequestGate(budget, lambda: None)
                original = lambda *args: True
                self.assertFalse(gate.check(original, [], "POST", "chatgpt.com",
                    "/backend-api/codex/responses"))
                gate.subscription_ready = lambda: True
                for method, host, path in [
                    ("GET", "chatgpt.com", "/backend-api/codex/responses"),
                    ("POST", "api.openai.com", "/v1/responses"),
                    ("POST", "chatgpt.com", "/backend-api/codex/responses?x=1"),
                ]:
                    self.assertFalse(gate.check(original, [], method, host, path))
                self.assertEqual(budget.requests, 0)
                self.assertTrue(gate.check(original, [], "POST", "chatgpt.com",
                    "/backend-api/codex/responses"))
                self.assertEqual(budget.requests, 1)
            finally:
                budget.close()

    def test_explicit_amendment_preserves_original_origin_and_consumption(self):
        import json
        with tempfile.TemporaryDirectory() as folder:
            journal = Path(folder) / 'requests.jsonl'
            initial = RequestBudget(max_requests=1, wall_seconds=10, journal=journal, clock=lambda:0,wall_clock=lambda:100)
            self.assertTrue(initial.reserve()); initial.close()
            with journal.open('a') as stream:
                stream.write(json.dumps({'event':'budget_amended','max_requests':2,'wall_seconds':20,'deadline_unix':120})+'\n')
            resumed = RequestBudget(max_requests=2,wall_seconds=20,journal=journal,resume=True,clock=lambda:5,wall_clock=lambda:105)
            try:
                self.assertEqual(resumed.requests,1)
                self.assertEqual(resumed.deadline,20)
                self.assertTrue(resumed.reserve())
                self.assertFalse(resumed.reserve())
            finally: resumed.close()
            self.assertEqual(json.loads(journal.read_text().splitlines()[0])['deadline_unix'],110)

class DemoAuthorizationTests(unittest.TestCase):
    def test_preserved_history_and_new_window_share_cumulative_ceiling(self):
        import json
        from physicslab.request_budget import validate_demo_authorization
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / '.runtime').mkdir()
            cfg = {'authorization_confirmed': True, 'allow_api_fallback': False,
                   'allow_credit_purchase': False, 'prior_phase_requests': 321,
                   'max_model_requests': 100, 'cumulative_request_ceiling': 500}
            for phase, count in [('pilot', 7), ('research', 199), ('enhancement', 115)]:
                cfg['historical_' + phase + '_requests'] = count
                (root / '.runtime' / (phase + '-requests.jsonl')).write_text(
                    json.dumps({'reserved_requests':count})+'\n')
            self.assertEqual(validate_demo_authorization(root,cfg),321)
            cfg['max_model_requests'] = 180
            with self.assertRaises(PermissionError): validate_demo_authorization(root,cfg)
            cfg['max_model_requests'] = 100
            cfg['historical_enhancement_requests'] = 0
            with self.assertRaises(PermissionError): validate_demo_authorization(root,cfg)
            cfg['historical_enhancement_requests'] = 115
            cfg['allow_credit_purchase'] = True
            with self.assertRaises(PermissionError): validate_demo_authorization(root,cfg)
