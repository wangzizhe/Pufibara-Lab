"""Exercise the actual patched runner end callback with synthetic native work."""
import asyncio
import hashlib
import json
from pathlib import Path
import httpx
from omnigent.runner import app as runtime
from physicslab.completion import require_runner_completion_patch

require_runner_completion_patch()
root = Path(__file__).resolve().parents[1]
client = httpx.AsyncClient(base_url='http://127.0.0.1:6768',
    transport=httpx.MockTransport(lambda request:httpx.Response(200,json={})))
app = runtime.create_runner_app(server_client=client,
    runner_workspace=root/'.runtime/agent-work',per_session_workspace=False)
parent, executor, modeler = ('pufibara-callback-root','pufibara-callback-executor','pufibara-callback-modeler')
for sid in (parent,executor):
    runtime._session_inboxes_ref[sid] = asyncio.Queue()
runtime.register_subagent_work(parent_session_id=parent,child_session_id=executor,agent='executor',title='Experiment')
runtime.register_subagent_work(parent_session_id=executor,child_session_id=modeler,agent='modeler',title='Repair')
app.state.on_proxy_stream_end(executor)
pending_deferred = runtime._session_inboxes_ref[parent].empty()
runtime.mark_subagent_work_terminal(modeler,status='completed',output='Synthetic repair result')
app.state.on_proxy_stream_end(executor)
final_delivered = not runtime._session_inboxes_ref[parent].empty()
runtime._session_inboxes_ref[parent].get_nowait()
app.state.on_proxy_stream_end(executor)
duplicate_absent = runtime._session_inboxes_ref[parent].empty()
asyncio.run(client.aclose())
proof = {'kind':'actual_runner_callback_with_synthetic_work_no_models',
    'pending_completion_deferred':pending_deferred,'final_completion_delivered':final_delivered,
    'duplicate_delivery_absent':duplicate_absent,'model_requests':0,
    'runner_sha256':hashlib.sha256(Path(runtime.__file__).read_bytes()).hexdigest(),
    'scope':'Native runner end callback and inbox delivery; external parent wake and real scientific closure require live evidence'}
(root/'evidence/runner-completion-callback.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof,indent=2))
assert pending_deferred and final_delivered and duplicate_absent
