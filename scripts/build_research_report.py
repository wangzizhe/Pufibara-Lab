"""Build a reviewable report from one actual broker session and native tree."""
import argparse
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('session_id')
parser.add_argument('--manual',action='store_true')
parser.add_argument('--enhancement',action='store_true')
parser.add_argument('--validation',action='store_true')
args = parser.parse_args()
from physicslab.contracts import identifier
identifier(args.session_id)
folder = root / 'evidence/sessions' / args.session_id
session = json.loads((folder / 'session.json').read_text())
native = json.loads((root / ('evidence/omnigent-enhancement-validation.json' if args.validation else 'evidence/omnigent-enhancement.json' if args.enhancement else 'evidence/omnigent-manual.json' if args.manual else 'evidence/omnigent-research.json')).read_text())
roles = {s.get('research_role') or s.get('sub_agent_name') for s in native.get('sessions', [])}
conversations_file = root / 'evidence/modeler-conversations.jsonl'
conversations = [json.loads(line) for line in conversations_file.read_text().splitlines()] if conversations_file.exists() else []
trials = session['trials']
trial_ids = {t['trial_id'] for t in trials}
conversations = [c for c in conversations if c['trial_id'] in trial_ids]
unique_threads = {c['codex_thread_id'] for c in conversations}
unique_sessions = {c['session_id'] for c in conversations}
ownership = {}
for c in conversations:
    for key in ("codex_thread_id", "session_id"):
        owner_key = (key,c[key])
        ownership.setdefault(owner_key,set()).add(c["trial_id"])
separated = (bool(trials) and all(len(owners)==1 for owners in ownership.values())
             and all(any(c['trial_id']==t['trial_id'] for c in conversations) for t in trials))

finished = [t for t in trials if t['finished']]
verified = session['stage'] == 'validated' and {'planner','executor','analyst','modeler'} <= roles and separated
usage_path = root / 'evidence/codex-role-usage.jsonl'
usage = [json.loads(line) for line in usage_path.read_text().splitlines()] if usage_path.exists() else []
role_map = {s['id']: s.get('research_role') or s.get('sub_agent_name') or 'coordinator' for s in native.get('sessions', [])}
role_usage = {}
unknown_usage = []
for record in usage:
    sid = record.get('session_id')
    if sid in role_map:
        role_usage.setdefault(role_map[sid], []).append(record)
    elif sid is None or 'session_key' not in record:
        unknown_usage.append(record)
record = {'kind':'actual_omnigent_broker_report', 'session_id':args.session_id,
    'parent_session_id':native['parent_session_id'], 'stage':session['stage'],
    'closed_loop_verified':verified, 'modeler_conversation_separation':separated,
    'plans':session['plans'], 'analysis':session['analysis'], 'trials':trials,
    'role_usage_records':role_usage, 'unattributed_early_usage_records':unknown_usage,
    'cost_usd':None, 'billing':'existing_subscription_no_credit_purchase_no_api_fallback',
    'workflow_measurement':'pending_actual_manual_automatic_pair',
    'unattributed_usage_scope':'Global historical records, not attributable to this study; do not sum as study cost',
    'limitations':['Small acceptance example cannot establish mechanism efficacy',
        'No measured research speed improvement yet', 'No human timing inferred from Codex operation',
        'Codex CLI does not expose matched temperature/seed control; same configured base model and reasoning route',
        'Early runtime usage keys were not native conversation IDs; those role costs remain unknown']}
comparison_file = root / 'evidence/measurements/workflow-comparison.json'
comparison = json.loads(comparison_file.read_text()) if comparison_file.exists() else {}
human = comparison.get('manual')
if human and args.session_id not in {human.get('session_id'), human.get('auto_session')}:
    human = None
if human and human.get('finished'):
    record['workflow_measurement'] = 'actual_manual_automatic_observations_with_confounds'
    record['workflow_observations'] = {
        'manual_seconds': human['elapsed_seconds'], 'manual_ui_actions': human['operator_actions'],
        'manual_preparation_seconds': human.get('setup_seconds'),
        'automatic_seconds': comparison['automatic']['elapsed_seconds'],
        'automatic_recorded_native_control_inputs': comparison['automatic']['recorded_native_control_inputs'],
        'automatic_total_operator_actions': None, 'speed_improvement_established': False,
        'evidence': 'evidence/measurements/workflow-comparison.json'}
if args.enhancement:
    final_analyst_id = 'f83d0d9902fa433492a70c4d96f227fa'
    items_path = root / 'evidence/omnigent' / native['parent_session_id'] / (final_analyst_id + '-items.json')
    final_messages = [item for item in json.loads(items_path.read_text())
                      if item.get('type') == 'message' and item.get('role') == 'assistant']
    record['followup_interpretation'] = {'agent_session_id': final_analyst_id,
        'source': str(items_path.relative_to(root)), 'actual_messages': final_messages,
        'root_collection_failed_in_primary_run': True}
    record['workflow_measurement'] = 'historical_actual_pair_no_speed_improvement_established'
    record['workflow_measurement_source'] = 'evidence/measurements/workflow-comparison.json'
    record['primary_native_operator_control_inputs'] = 6
    record['unintervened_full_scientific_loop'] = False
(folder / 'report.json').write_text(json.dumps(record,ensure_ascii=False,indent=2))
lines = ['# Actual research run report','',f'Broker session: `{args.session_id}` . Omnigent parent: `{native["parent_session_id"]}`。',
    '',f'Stage: **{session["stage"]}** ; closed-loop verification: **{verified}** ; Modeler conversation separation: **{separated}**。',
    '', '## Agent hypotheses and selection','']
for plan in session['plans']:
    lines += [f'### {plan["id"]}', '', 'Hypothesis (untested): '+plan['hypothesis'], '', 'Falsification: '+plan['falsification'], '',
        '| Candidate | Learning value | Feasibility | Estimated tool runs |', '| --- | --- | --- | --- |']
    for c in plan['candidates']:
        lines += [f'| {c["id"]} | {c["learning_value"]} | {c["feasibility"]} | {c["estimated_tool_runs"]} |']
    lines += ['', 'Selection: '+plan['selected_candidate']+'。'+plan['selection_reason'], '']
lines += ['## Actual experiments','', '| Plan | Mechanism | Development attempts (including baseline) | Checking | Simulation | Behavior | Tool seconds | Evidence |', '| --- | --- | --- | --- | --- | --- | --- | --- |']
for t in finished:
    e=t['evaluation']; rid=t['final_run_id']
    lines += [f'| {t["plan_id"]} | {t["config"]["diagnostics"]} | {len(t["attempts"])} | {e["model_checking"]} | {e["simulation"]} | {e["behavior"]} | {t["tool_seconds"]:.3f} | [{rid}](../../runs/{rid}/result.json) |']
for t in trials:
    if not t['finished']:
        lines += [f'\nUnfinished trial: `{t["trial_id"]}`; saved {len(t["attempts"])} development runs; not counted as final acceptance.']
if session['analysis']:
    a=session['analysis']; lines += ['', '## Evidence-driven adjustment','', 'Support: '+a['support'], '', 'Adjustment reason: '+a['adjustment_reason'], '', 'Limitations: '+a['limitations'], '', 'References: '+', '.join(a['evidence_run_ids'])]
bottleneck = 'Workflow bottleneck: a real manual/automatic comparison is pending; no improvement reported.'
if args.enhancement:
    bottleneck = 'Historical manual/automatic measurements: evidence/measurements/workflow-comparison.json. No overall speedup established. This run includes six recorded native controls and engineering recovery; do not infer reduced human work.'
    interpretation = record['followup_interpretation']
    lines += ['', '## Actual follow-up interpretation', '', 'Source: `'+interpretation['source']+'`. The parent lacked its inbox tool and could not collect the last result. Failure is preserved; do not claim uninterrupted automation.']
    for message in interpretation['actual_messages']:
        lines += ['', *[content['text'] for content in message.get('content', []) if content.get('type') == 'output_text']]
if human and human.get('finished'):
    observation = record['workflow_observations']
    bottleneck = (f"Observed workflow bottleneck: human manual {observation['manual_seconds']:.1f} seconds, "
        f"{observation['manual_ui_actions']} UI actions; automatic path {observation['automatic_seconds']:.1f} seconds, "
        f"{observation['automatic_recorded_native_control_inputs']} recorded native controls. "
        'Automatic shell/edit actions are incompletely recorded; operator and infrastructure maturity differ. No speed factor is computed.')
lines += ['', '## Usage and limitations','', 'The phase gateway counts actual requests, including infrastructure failures and retries. Research/modeling tokens are attributed only when bound to actual conversations. Early anonymous keys remain unattributed global history, not this study cost. Subscription billing does not provide per-token dollar charges; monetary cost stays unknown.', '',
    bottleneck, '', *('- '+x for x in record['limitations']), '',
    'Original messages: `evidence/omnigent/'+native['parent_session_id']+'`; plans, source, logs and model artifacts are preserved in evidence.']
(folder / 'report.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'report':str(folder / 'report.md'), 'stage':session['stage'], 'closed_loop_verified':verified},ensure_ascii=False))
