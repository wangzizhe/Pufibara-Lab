"""Verify recorded science artifacts; does not call models or rerun experiments."""
import hashlib
import json
import time
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sid = 'session-d32b3336026842fcba860f2d22b06ec6'
folder = root / 'evidence/sessions' / sid
session = json.loads((folder / 'session.json').read_text())
report = json.loads((folder / 'report.json').read_text())
assert session['stage'] == 'validated' and report['closed_loop_verified']
assert len(session['plans']) == 2 and len(session['trials']) == 4
assert all(len(p['candidates']) >= 2 for p in session['plans'])
assert session['analysis']['support'] == 'not_supported'
assert session['analysis']['followup'] == session['plans'][1]
assert session['plans'][0]['selected_candidate'] != session['plans'][1]['selected_candidate']
checks = []
base = (root / 'tasks/cooling-init/Cooling.mo').read_bytes()
for trial in session['trials']:
    assert trial['finished']
    expected_attempts = 2 if trial['plan_id'] == session['plans'][0]['id'] else 1
    assert len(trial['attempts']) == expected_attempts
    baseline = root / 'evidence/runs' / trial['attempts'][0]
    assert (baseline / 'submitted.mo').read_bytes() == base
    final = root / 'evidence/runs' / trial['final_run_id']
    result = json.loads((final / 'result.json').read_text())
    assert result['final'] and result['run_id'] == trial['final_run_id']
    assert result['source_sha256'] == hashlib.sha256((final / 'submitted.mo').read_bytes()).hexdigest()
    evaluation = result['evaluation']
    expected = ('passed','passed','passed') if expected_attempts == 2 else ('passed','failed','not_run')
    observed = (evaluation['model_checking'],evaluation['simulation'],evaluation['behavior']['status'])
    assert observed == expected, (trial['trial_id'], observed)
    for name, digest in result['implementation_sha256'].items():
        assert hashlib.sha256((root / 'src/physicslab' / name).read_bytes()).hexdigest() == digest
    assert result['image'] == session['runtime']['omc_image_digest']
    checks.append({'trial_id':trial['trial_id'],'final_run_id':result['run_id'],
                   'attempts':expected_attempts,'evaluation':observed,'source_hash_verified':True})
interpretation = report['followup_interpretation']
items = json.loads((root / interpretation['source']).read_text())
assert any(x.get('type') == 'function_call' and x.get('name') == 'trial_evidence' for x in items)
assert len(interpretation['actual_messages']) >= 2
proof = {'kind':'recorded_scientific_artifact_verification','verified_at_unix':time.time(),
         'broker_session_id':sid,'closed_loop_verified':True,'actual_agent_followup_changed':True,
         'trials':checks,'baseline_first_verified':True,'final_source_and_evaluator_hashes_verified':True,
         'actual_analyst_evidence_calls_verified':True,'full_unintervened_run':False,
         'scope':'Saved primary science, not notification stability or universal efficacy',
         'historical_workflow_speed_improvement_established':False}
(root / 'evidence/enhancement-scientific-verification.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof))
