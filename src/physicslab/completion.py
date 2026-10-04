"""Version-scoped fix for premature nested completion in Omnigent 0.16.0."""
from importlib.metadata import version


def require_runner_completion_patch():
    from pathlib import Path
    from omnigent.runner import app as runtime
    if version('omnigent') != '0.16.0' or 'Pufibara: pending descendants are not terminal completion.' not in Path(runtime.__file__).read_text():
        raise RuntimeError('Apply and verify the project-local Omnigent runner completion patch before models')


def install_completion_guard():
    # Keep native dispatch, inbox delivery and wakes. Only defer a successful
    # parent completion while its registered children still have live work.
    from omnigent.runner import app as runtime
    if getattr(runtime.mark_subagent_work_terminal, '_pufibara_guard', False):
        return
    if version('omnigent') != '0.16.0':
        raise RuntimeError('Revalidate the completion guard for this Omnigent version')
    original = runtime.mark_subagent_work_terminal

    def guarded(child_session_id, *, status, output):
        pending = [entry for entry in runtime.list_subagent_work(child_session_id)
                   if entry.status in {'launching', 'running', 'waiting'}]
        if status == 'completed' and pending:
            return runtime._SubagentDeliveryAck(
                entry=runtime.get_subagent_work(child_session_id), delivered=False,
                delivered_now=False, reason='pufibara_children_still_pending')
        return original(child_session_id, status=status, output=output)

    guarded._pufibara_guard = True
    guarded._pufibara_original = original
    runtime.mark_subagent_work_terminal = guarded
