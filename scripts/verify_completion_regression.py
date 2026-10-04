"""Audit real native inbox delivery, without requesting another model turn."""
import hashlib
import json
import time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
proof_path=root/'evidence/completion-regression.json'
proof=json.loads(proof_path.read_text())
native=json.loads((root/'evidence/omnigent-completion-regression.json').read_text())
parent=native['parent_session_id']
folder=root/'evidence/omnigent'/parent
session=json.loads((root/'evidence/sessions'/proof['broker_session_id']/'session.json').read_text())
assert session['stage']==proof['expected_final_stage'] and len(session['trials'])==2
assert len(native['sessions'])==4 and all(s['status']=='idle' and not s['last_task_error'] for s in native['sessions'])
source=json.loads((root/'evidence/sessions'/proof['source_broker_session_id']/'session.json').read_text())['analysis']['followup']
assert source==session['plans'][0]
assert hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest()==proof['source_plan_sha256']
items=json.loads((folder/(parent+'-items.json')).read_text())
def contents(item): return '\n'.join(c.get('text','') for c in item.get('content',[]))
users=[x for x in items if x.get('role')=='user']
controls=[x for x in users if not contents(x).startswith('[System:')]
wakes=[x for x in users if contents(x).startswith('[System:')]
assert len(controls)==1 and len(wakes)==1
calls=[x for x in items if x.get('type')=='function_call' and x.get('name')=='sys_read_inbox']
assert len(calls)==1
output=next(x for x in items if x.get('type')=='function_call_output' and x.get('call_id')==calls[0]['call_id'])
final=next(x for x in reversed(items) if x.get('role')=='assistant' and x.get('type')=='message')
for t in session['trials']:
    assert t['finished'] and len(t['attempts'])==1
    assert t['final_run_id'] in output['output'] and t['final_run_id'] in contents(final)
    assert t['evaluation']['model_checking']=='passed' and t['evaluation']['simulation']=='failed' and t['evaluation']['behavior']=='not_run'
    original=root/'tasks/cooling-init/Cooling.mo'
    for rid in t['attempts']+[t['final_run_id']]:
        assert (root/'evidence/runs'/rid/'submitted.mo').read_bytes()==original.read_bytes()
executor=next(s for s in native['sessions'] if s['research_role']=='executor')
executor_items=json.loads((folder/(executor['id']+'-items.json')).read_text())
executor_last=max(x['created_at'] for x in executor_items if x.get('role')=='assistant')
assert wakes[0]['created_at']>=executor_last
proof.update(verified=True,verified_at_unix=time.time(),parent_session_id=parent,
             native_control_inputs=1,operator_stage_recoveries=0,
             final_run_ids=[t['final_run_id'] for t in session['trials']],
             native_inbox_collected_final_run_ids=True,all_four_native_actors_idle=True,
             parent_wakes=1,root_inbox_reads=1,
             root_wake_after_executor_final=True,
             final_executor_to_parent_summary_seconds=final['created_at']-executor_last,
             elapsed_goal_to_summary_seconds=final['created_at']-controls[0]['created_at'],
             full_unintervened_scientific_loop_verified=False)
proof_path.write_text(json.dumps(proof,indent=2)+'\n')
patch_path=root/'evidence/omnigent-completion-patch.json'
patch=json.loads(patch_path.read_text());patch.update(live_verified=True,live_verification_source='evidence/completion-regression.json',live_scope=proof['scope']);patch_path.write_text(json.dumps(patch,indent=2)+'\n')
print(json.dumps(proof))
