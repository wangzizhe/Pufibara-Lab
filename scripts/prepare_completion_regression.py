"""Prepare a minimal English native-notification regression bundle, no model."""
import shutil
from pathlib import Path
root = Path(__file__).resolve().parents[1]
source = root/'.runtime/enhancement-validation-agent'
target = root/'.runtime/completion-regression-agent'
if target.exists():
    raise FileExistsError('Do not overwrite the regression bundle')
shutil.copytree(source,target,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
for name in ('planner','analyst'):
    shutil.rmtree(target/'agents'/name)
config = (target/'config.yaml').read_text().replace('agents: [planner, executor, analyst]','agents: [executor]')
(target/'config.yaml').write_text(config)
(target/'AGENTS.md').write_text('''You coordinate a targeted native-completion engineering regression in English.
This is not a new scientific discovery study. The trusted broker has reused the
primary Analyst's real accepted baseline-only diagnostic-fidelity plan.
1. Read status, then delegate the accepted plan to the declared executor.
2. End your turn while the child works. Do not poll any session or inbox.
3. On the native child wake, call sys_read_inbox to collect its actual final result.
4. Read broker status and report actual final run IDs and each evaluation layer.
Stop when both accepted trials finish and stage is analysis; do not dispatch any
new Planner or Analyst, record a new plan, or attempt another research phase.
Model checking may pass while initialization fails: preserve the expected baseline
failures and behavior not_run. No repair benefit or research speed claim.
Only packaged tools and declared children. No source editing, hidden answers,
history/session discovery, credentials, network, shell, publication or installation.
Budget remains the existing enhancement phase, no reset, credits or API fallback.
Keep visible output brief and English. Preserve every actual error and stop on
quota, isolation or authorization error. Do not ask the operator to trigger stages.
''')
print({'bundle_prepared':str(target),'model_requests':0})
