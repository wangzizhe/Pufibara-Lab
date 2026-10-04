from omnigent_client.tools import tool
import json
import os
import urllib.request


def _call(action, payload):
    token = os.environ.get("PHYSICSLAB_PLANNER_CAPABILITY")
    if not token:
        raise PermissionError("Operator must provision a scoped broker capability")
    request = urllib.request.Request("http://127.0.0.1:8765/call", data=json.dumps({"action": action, "payload": payload}).encode(), headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.load(response)

@tool
def record_plan(plan: dict) -> dict:
    """Validate and persist a hypothesis, two candidates and budgeted matched runs."""
    return _call("record_plan", {"plan": plan})
