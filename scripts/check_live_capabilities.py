"""Check native runner env -> registered local tools -> current broker, no model."""
import json
import os
from pathlib import Path
root = Path(__file__).resolve().parents[1]
os.environ.clear()
os.environ.update(HOME=str(root / '.runtime/home'), PATH=str(root / '.venv/bin') + ':/usr/bin:/bin')
from omnigent.host.connect import _build_runner_env
from omnigent.inner.codex_executor import _clean_codex_env
from omnigent.spec.parser import parse
from omnigent.tools.manager import ToolManager
from omnigent.tools.base import ToolContext
caps = json.loads((root / '.runtime/capabilities.json').read_text())['capabilities']
base = dict(os.environ)
for role, token in caps.items():
    base['PHYSICSLAB_' + role.upper() + '_CAPABILITY'] = token
base['OMNIGENT_RUNNER_ENV_PASSTHROUGH'] = ','.join(k for k in base if k.startswith('PHYSICSLAB_'))
runner_env = _build_runner_env(base, server_url='http://127.0.0.1:6768', runner_id='synthetic-probe', binding_token='synthetic-probe', workspace=str(root / '.runtime/agent-work'), parent_pid=os.getpid())
os.environ.clear(); os.environ.update(runner_env)
assert all(os.environ.get('PHYSICSLAB_' + role.upper() + '_CAPABILITY') == token for role, token in caps.items())
assert not any(k.startswith('PHYSICSLAB_') for k in _clean_codex_env())
checks = []
for role, path in [('coordinator',''), ('planner','agents/planner'), ('executor','agents/executor'), ('analyst','agents/analyst')]:
    folder = root / 'agents/lab' / path
    spec = parse(folder, expand_env=False)
    manager = ToolManager(spec, workdir=folder)
    try:
        response = json.loads(manager.call_tool('status', '{}', ToolContext(task_id='capability-probe', agent_id=role)))
        assert response['stage'] in ('planning','experiment','analysis','followup','validated')
        checks.append({'role': role, 'stage': response['stage'], 'native_registered_status': True})
    finally:
        manager.shutdown()
record = {'kind':'native_env_and_local_tool_transport_no_model', 'capabilities_forwarded_to_trusted_runner':True, 'capabilities_absent_from_model_env':True, 'checks': checks, 'passed':True}
(root / 'evidence/live-capabilities.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2))
