"""Targeted native handoff regression; reuse an actual Analyst's accepted plan."""
import hashlib
import json
import time
from pathlib import Path
from physicslab.broker import ResearchSession, serve

root = Path(__file__).resolve().parents[1]
proof_path = root/'evidence/completion-regression.json'
if proof_path.exists():
    raise FileExistsError('Preserve prior regression; do not reset it')
source_id = 'session-d32b3336026842fcba860f2d22b06ec6'
source = json.loads((root/'evidence/sessions'/source_id/'session.json').read_text())
if source['stage'] != 'validated':
    raise ValueError('Complete the primary scientific loop before regression')
plan = source['analysis']['followup']
settings = json.loads((root/'configs/runtime-enhancement.json').read_text())
session = ResearchSession(root, settings)
session.kind = 'native_completion_regression_not_new_scientific_discovery'
provenance = {'source_broker_session_id':source_id,'source_plan_id':plan['id'],
              'source_plan_sha256':hashlib.sha256(json.dumps(plan,sort_keys=True).encode()).hexdigest(),
              'decision_source':'Real primary Analyst record_analysis; trusted operator reuses it, no simulated Planner'}
session.ledger.record('trusted_regression_reuses_agent_plan',provenance)
session.dispatch('record_plan',{'plan':plan})
session.persist()
rows = [json.loads(line) for line in (root/'.runtime/enhancement-requests.jsonl').read_text().splitlines()]
proof = {'kind':'targeted_native_completion_regression','broker_session_id':session.sid,
         **provenance,'started_unix':time.time(),'model_requests_at_setup':max(r.get('reserved_requests',0) for r in rows),
         'expected_trials':len(plan['runs']),'expected_final_stage':'analysis',
         'scope':'Two baseline-only native Executor/Modeler trials; not a new complete scientific loop or a speed benchmark',
         'operator_stage_recoveries':0,'verified':False}
proof_path.write_text(json.dumps(proof,indent=2)+'\n')
serve(root,settings,resume_id=session.sid)
