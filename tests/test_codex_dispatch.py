import unittest
from physicslab.codex_harness import check_dispatch


class DispatchTests(unittest.TestCase):
    def test_named_child_keeps_native_omnigent_dispatch(self):
        check_dispatch("sys_session_send", {"agent": "planner", "args": "Plan a thermal experiment"})

    def test_agent_cannot_escape_via_harness_or_model_override(self):
        for field in ["harness", "model", "cost_budget"]:
            with self.assertRaises(PermissionError):
                check_dispatch("sys_session_send", {"agent": "planner", "args": {"input": "hi", field: "alternate"}})

    def test_host_tools_and_public_sharing_denied(self):
        for tool in ["sys_os_read", "sys_os_shell", "sys_terminal_create", "sys_agent_download", "web_fetch", "sys_session_share", "sys_session_create"]:
            with self.assertRaises(PermissionError):
                check_dispatch(tool, {})

    def test_foreign_session_read_or_send_cannot_cross_project_boundary(self):
        for name in ['sys_session_get_history', 'sys_session_list', 'sys_session_get_info']:
            with self.assertRaises(PermissionError):
                check_dispatch(name, {'session_id':'foreign'})
        with self.assertRaises(PermissionError):
            check_dispatch('sys_session_send', {'session_id':'foreign','args':'read files'})
