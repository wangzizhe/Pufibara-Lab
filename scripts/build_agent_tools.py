"""Generate narrow Omnigent tools. No model or host filesystem endpoint."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HEADER = '''from omnigent_client.tools import tool
import json
import os
import urllib.request


def _call(action, payload):
    token = os.environ.get("PHYSICSLAB_%s_CAPABILITY")
    if not token:
        raise PermissionError("Operator must provision a scoped broker capability")
    request = urllib.request.Request("http://127.0.0.1:8765/call", data=json.dumps({"action": action, "payload": payload}).encode(), headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.load(response)

'''
STATUS = '''@tool
def status() -> dict:
    """Read accepted plans and public run summaries, never evaluator answers."""
    return _call("status", {})

'''
FUNCTIONS = {
    "coordinator": STATUS,
    "planner": STATUS + '''@tool
def record_plan(plan: dict) -> dict:
    """Validate and persist a hypothesis, two candidates and budgeted matched runs."""
    return _call("record_plan", {"plan": plan})
''',
    "executor": STATUS + '''@tool
def start_trial() -> dict:
    """Start the next fixed trial and return only its public task and configuration."""
    return _call("start_trial", {})

@tool
def finish_trial(trial_id: str) -> dict:
    """Submit the last candidate to the trusted final evaluator."""
    return _call("finish_trial", {"trial_id": trial_id})
''',
    "modeler": '''@tool
def task(trial_id: str) -> dict:
    """Read only the active public task and its approved controls."""
    return _call("task", {"trial_id": trial_id})

@tool
def attempt(trial_id: str, source: str) -> dict:
    """Run a candidate in the confined OpenModelica tool; return diagnostic feedback."""
    return _call("attempt", {"trial_id": trial_id, "source": source})

@tool
def raw_log(trial_id: str, run_id: str) -> dict:
    """Query current trial's original compiler/simulation log; no hidden evaluation."""
    return _call("raw_log", {"trial_id": trial_id, "run_id": run_id})
''',
    "analyst": STATUS + '''@tool
def record_analysis(analysis: dict) -> dict:
    """Cite existing results and commit an evidence-driven, budgeted followup."""
    return _call("record_analysis", {"analysis": analysis})
''',
}
PATHS = {"coordinator": "", "planner": "agents/planner", "executor": "agents/executor", "analyst": "agents/analyst", "modeler": "agents/executor/agents/modeler"}
for role, location in PATHS.items():
    folder = ROOT / "agents/lab" / location / "tools/python"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "research.py").unlink(missing_ok=True)
    for function in FUNCTIONS[role].split("@tool\n"):
        if not function.strip():
            continue
        name = re.match(r"def ([a-z_]+)\(", function).group(1)
        (folder / (name + ".py")).write_text(HEADER % role.upper() + "@tool\n" + function)
