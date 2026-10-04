"""Report observed control inputs and wall time, preserving measurement limits."""
import argparse
import json
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('automatic_session')
parser.add_argument('--manual-session')
args = parser.parse_args()
from physicslab.contracts import identifier
identifier(args.automatic_session)
if args.manual_session:
    identifier(args.manual_session)
native = json.loads((root / 'evidence/omnigent-research.json').read_text())
report = json.loads((root / 'evidence/sessions' / args.automatic_session / 'report.json').read_text())
if not report['closed_loop_verified']:
    raise RuntimeError('Automatic full loop must be verified before ending observation')
events = []
for sid in native.get('root_session_ids', [native['parent_session_id']]):
    items = json.loads((root / 'evidence/omnigent' / native['parent_session_id'] / (sid + '-items.json')).read_text())
    for item in items:
        if item.get('type') != 'message' or item.get('role') != 'user':
            continue
        content = ''.join(c.get('text', '') for c in item.get('content', []))
        if content.startswith('[System:'):
            continue
        events.append({'session_id': sid, 'at_unix': item['created_at'], 'text': content})
folder = root / 'evidence/measurements'
folder.mkdir(exist_ok=True)
path = folder / ('automatic-' + args.automatic_session + '.json')
if path.exists():
    automatic = json.loads(path.read_text())
else:
    ended = time.time()
    automatic = {'operator': 'codex_native_control_inputs', 'started_at': min(e['at_unix'] for e in events),
                 'ended_at': ended, 'elapsed_seconds': ended - min(e['at_unix'] for e in events),
                 'recorded_native_control_inputs': len(events), 'events': events,
                 'total_operator_actions': None, 'reusable_setup_seconds': None,
                 'report': str((root / 'evidence/sessions' / args.automatic_session / 'report.md').relative_to(root)),
                 'limitations': ['Includes infrastructure failures, code repairs and operator recovery.',
                                 'Native messages are only recorded control inputs; shell/edit actions were not fully timed.',
                                 'Codex operation cannot stand in for human operation.']}
    path.write_text(json.dumps(automatic, ensure_ascii=False, indent=2))
manual = None
if args.manual_session:
    manual = json.loads((folder / ('manual-' + args.manual_session + '.json')).read_text())
    if not manual.get('finished'):
        raise RuntimeError('Human workflow has not finished; do not invent a duration')
operator_events = []
if args.manual_session:
    operator_file = folder / ('manual-' + args.manual_session + '-operator-events.jsonl')
    if operator_file.exists():
        operator_events = [json.loads(line) for line in operator_file.read_text().splitlines()]
comparison = {'automatic': automatic, 'manual': manual, 'manual_codex_interventions': operator_events, 'speed_improvement_established': False,
              'limitations': ['One task and sequential runs; different operators and infrastructure maturity.',
                              'Automatic total action count and reusable preparation time are incomplete.',
                              'Manual model time authorization was extended by the user; UI reload by Codex is recorded separately.',
                              'Report actual observations without a speedup ratio or causal claim.']}
(folder / 'workflow-comparison.json').write_text(json.dumps(comparison, ensure_ascii=False, indent=2))
lines = ['# Workflow bottleneck observations', '',
         f"Automatic path (Codex-operated), recorded initial control to report save: {automatic['elapsed_seconds']:.1f} seconds; recorded {automatic['recorded_native_control_inputs']} native control inputs.",
         'Includes debugging and recovery. Shell actions, edits and reusable setup are incompletely timed; total operator actions are unknown. Native message count is not total human steps.', '']
if manual:
    lines += [f"Human manual path: {manual['elapsed_seconds']:.1f} seconds, {manual['operator_actions']} UI actions (including failures/recovery); preparation {manual.get('setup_seconds')} seconds (Codex-operated, separately recorded).", '']
    lines += [f'During the manual path, another {len(operator_events)} Codex UI-maintenance actions are separate from human clicks. The user extended the shared deadline by 20 minutes without adding requests, then raised the request limit to 500 after follow-up settlement without resetting 199 consumed requests.', '']
else:
    lines += ['Human manual path incomplete; no estimated values inserted.', '']
lines += ['No workflow speedup established. Operators, order and infrastructure maturity differ; no speed factor or causal improvement claim.', '',
          'Evidence: automatic/manual JSON records, workflow-comparison.json and actual native messages/reports.']
(folder / 'workflow-comparison.md').write_text('\n'.join(lines) + '\n')
print(json.dumps({'automatic_seconds': automatic['elapsed_seconds'], 'manual_finished': bool(manual),
                  'speed_improvement_established': False}))
