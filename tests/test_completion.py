import asyncio
import unittest
from omnigent.runner import app as runtime
from physicslab.completion import install_completion_guard


class CompletionTest(unittest.TestCase):
    def setUp(self):
        self.original = runtime.mark_subagent_work_terminal
        self.inboxes = runtime._session_inboxes_ref
        self.parent = 'pufibara-test-parent'
        self.executor = 'pufibara-test-executor'
        self.modeler = 'pufibara-test-modeler'
        self.inboxes[self.parent] = asyncio.Queue()
        self.inboxes[self.executor] = asyncio.Queue()
        runtime.register_subagent_work(parent_session_id=self.parent,
            child_session_id=self.executor, agent='executor', title='Experiment')
        runtime.register_subagent_work(parent_session_id=self.executor,
            child_session_id=self.modeler, agent='modeler', title='Repair')

    def tearDown(self):
        runtime.mark_subagent_work_terminal = self.original
        for sid in (self.parent, self.executor, self.modeler):
            runtime._subagent_work_by_child.pop(sid, None)
            runtime._subagent_work_by_parent.pop(sid, None)
            runtime._drained_delivered_subagent_children.discard(sid)
            self.inboxes.pop(sid, None)

    def test_native_inbox_receives_final_nested_result_once(self):
        install_completion_guard()
        early = runtime.mark_subagent_work_terminal(self.executor,
            status='completed', output='Waiting for modeler')
        self.assertFalse(early.delivered)
        self.assertTrue(self.inboxes[self.parent].empty())
        runtime.mark_subagent_work_terminal(self.modeler,
            status='completed', output='Actual submitted run')
        self.assertEqual(self.inboxes[self.executor].get_nowait()['output'], 'Actual submitted run')
        final = runtime.mark_subagent_work_terminal(self.executor,
            status='completed', output='Trial completed with actual verdict')
        self.assertTrue(final.delivered_now)
        self.assertEqual(self.inboxes[self.parent].get_nowait()['output'],
                         'Trial completed with actual verdict')
        duplicate = runtime.mark_subagent_work_terminal(self.executor,
            status='completed', output='Duplicate completion')
        self.assertFalse(duplicate.delivered_now)
        self.assertTrue(self.inboxes[self.parent].empty())

    def test_failure_is_delivered_even_with_pending_child(self):
        install_completion_guard()
        failure = runtime.mark_subagent_work_terminal(self.executor,
            status='failed', output='Actual executor error')
        self.assertTrue(failure.delivered_now)
        self.assertEqual(self.inboxes[self.parent].get_nowait()['status'], 'failed')
