"""Prepare an English Omnigent demo bundle without starting services or models."""
import io
import json
import shutil
import tarfile
import argparse
from pathlib import Path

from omnigent.spec.parser import parse
from omnigent.spec.validator import validate
from omnigent.tools.local import load_local_python_tools

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--enhancement', action='store_true')
parser.add_argument('--validation', action='store_true')
args = parser.parse_args()
enhancement = args.enhancement or args.validation
source = root / 'agents/lab'
target = root / ('.runtime/enhancement-validation-agent' if args.validation else '.runtime/enhancement-live-agent' if enhancement else '.runtime/live-demo-agent')
if target.exists():
    raise FileExistsError('Preserve the previous prepared bundle; do not overwrite it')
shutil.copytree(source, target, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
style = '''
Live demonstration presentation:
- Use English for every visible message, child-session title, hypothesis,
  experiment selection, analysis, limitation and final summary.
- Use brief stage messages: Goal, Plan, Experiment, Analysis, Validation.
  Report what actually happened and what happens next in one or two sentences.
- Keep details in real tool records. Include actual run IDs with results.
  Never conceal errors, recovery, missing measurements or inconclusive evidence.
- Delegate with short English titles and English instructions.
- All original scientific, role, isolation and budget rules remain in force.
  Presentation changes do not authorize a model call or change an experiment.
'''
for instructions in target.rglob('AGENTS.md'):
    text = instructions.read_text().replace('provide a concise Chinese report with run IDs',
                                            'provide a concise English report with run IDs')
    instructions.write_text(text + style)

def inspect(spec, folder):
    result = validate(spec)
    if not result.valid:
        raise ValueError([(e.path, e.message) for e in result.errors])
    tools = load_local_python_tools(spec.local_tools, folder, srt_available=False, uv_available=False)
    if {t.name() for t in tools} != {t.name for t in spec.local_tools}:
        raise ValueError('Declared and loaded tools differ')
    return {'name': spec.name, 'tools': [t.name() for t in tools],
            'children': [inspect(c, folder / 'agents' / c.name) for c in spec.sub_agents]}
record = inspect(parse(target, expand_env=False), target)
output = root / ('artifacts/enhancement-validation' if args.validation else 'artifacts/enhancement-live' if enhancement else 'artifacts/live-demo')
output.mkdir(parents=True, exist_ok=True)
buffer = io.BytesIO()
with tarfile.open(fileobj=buffer, mode='w:gz') as bundle:
    for path in sorted(target.rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts:
            bundle.add(path, arcname=str(path.relative_to(target)))
(output / 'agent-bundle.tar.gz').write_bytes(buffer.getvalue())
prompt = ('Study whether structured diagnostics help an AI repair a physical model. '
          'Propose a falsifiable hypothesis and compare two feasible experiments. '
          'Run a matched raw/structured comparison, analyze the actual results, '
          'then select and run a follow-up experiment. Use the broker public task '
          'and fixed evaluation. Keep all visible communication in English and concise. '
          'Preserve every failure and cite actual run IDs. Stop at validated or any '
          'budget or isolation error. Do not invent results or repair the model yourself.')
(output / 'goal.txt').write_text(prompt + '\n')
proof = {'status': 'english_bundle_and_tools_checked_not_live',
         'agent': record, 'model_requests': 0,
         'scientific_controls_changed': False, 'live_authorization_granted_by_preparation': False}
(output / 'preparation.json').write_text(json.dumps(proof, indent=2))
print(json.dumps({'status': proof['status'], 'bundle': str(output / 'agent-bundle.tar.gz'),
                  'model_requests': 0}))
