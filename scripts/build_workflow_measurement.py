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
lines = ['# 科研流程瓶颈实测', '',
         f"自动路径（Codex 操作）从已记录初始控制输入到报告保存：{automatic['elapsed_seconds']:.1f} 秒；记录到 {automatic['recorded_native_control_inputs']} 次原生控制输入。",
         '该时间包含排错与恢复。终端操作、代码修改和可复用准备未完整计时，人工总动作数未知；不能把原生消息数当成总人工步骤。', '']
if manual:
    lines += [f"真人手工路径：{manual['elapsed_seconds']:.1f} 秒，{manual['operator_actions']} 次界面动作（含错误／恢复），环境准备 {manual.get('setup_seconds')} 秒（Codex 操作，另列）。", '']
    lines += [f'手工路径期间另有 {len(operator_events)} 次已记录 Codex 界面维护动作，单独列出，不冒充真人点击。用户明确延长共享阶段时长20分钟；该次时间修改未增请求。另在后续验证结算后把总请求上限提升到500，未重置已用199次。', '']
else:
    lines += ['真人手工路径尚未完成，不填估计值。', '']
lines += ['尚未建立科研流程提速证据。两路径的操作员、先后次序和基础设施成熟度不同；不计算提速倍率或宣称因果改善。', '',
          '证据：`automatic-*.json`、`manual-*.json`、`workflow-comparison.json` 和实际原生消息／科研报告。']
(folder / 'workflow-comparison.md').write_text('\n'.join(lines) + '\n')
print(json.dumps({'automatic_seconds': automatic['elapsed_seconds'], 'manual_finished': bool(manual),
                  'speed_improvement_established': False}))
