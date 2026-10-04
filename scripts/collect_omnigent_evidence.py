"""Collect only descendants of this project's explicitly recorded parent ID."""
import argparse
import json
import time
from pathlib import Path
import httpx

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--research", action="store_true")
parser.add_argument("--manual", action="store_true")
parser.add_argument("--enhancement", action="store_true")
parser.add_argument("--validation", action="store_true")
parser.add_argument("--completion-regression", action="store_true")
parser.add_argument("--demo", action="store_true")
args = parser.parse_args()
record_path = root / ("evidence/omnigent-demo.json" if args.demo else "evidence/omnigent-completion-regression.json" if args.completion_regression else "evidence/omnigent-enhancement-validation.json" if args.validation else "evidence/omnigent-enhancement.json" if args.enhancement else "evidence/omnigent-manual.json" if args.manual else "evidence/omnigent-research.json" if args.research else "evidence/omnigent-handoff.json")
record = json.loads(record_path.read_text())
parent_id = record["parent_session_id"]
folder = root / "evidence/omnigent" / parent_id
folder.mkdir(parents=True, exist_ok=True)
queue = [(sid, None) for sid in record.get("root_session_ids", [parent_id])]
seen = set()
sessions = []
with httpx.Client(base_url="http://127.0.0.1:6768", timeout=20) as client:
    while queue:
        sid, expected_parent = queue.pop(0)
        if sid in seen:
            raise RuntimeError("Repeated child session in tree")
        seen.add(sid)
        state_response = client.get(f"/v1/sessions/{sid}")
        state_response.raise_for_status()
        state = state_response.json()
        if expected_parent is not None and state.get("parent_session_id") != expected_parent:
            raise PermissionError("Child provenance mismatch")
        items = []
        after = None
        while True:
            params = {"limit": 1000}
            if after:
                params["after"] = after
            response = client.get(f"/v1/sessions/{sid}/items", params=params)
            response.raise_for_status()
            page = response.json()
            items.extend(page["data"])
            if not page.get("has_more"):
                break
            after = page["last_id"]
        (folder / (sid + "-items.json")).write_text(json.dumps(items, ensure_ascii=False, indent=2))
        # Avoid storing transport bindings, host auth metadata or full snapshots.
        summary = {key: state.get(key) for key in ["id", "status", "agent_name", "sub_agent_name",
            "kind", "parent_session_id", "harness", "usage_by_model", "last_task_error"]}
        summary["research_role"] = record.get("root_roles", {}).get(sid) or state.get("sub_agent_name")
        summary["item_count"] = len(items)
        summary["assistant_messages"] = sum(i.get("type") == "message" and i.get("role") == "assistant" for i in items)
        summary["dispatches"] = [i for i in items if i.get("type") == "function_call" and i.get("name") == "sys_session_send"]
        sessions.append(summary)
        child_response = client.get(f"/v1/sessions/{sid}/child_sessions")
        child_response.raise_for_status()
        children = child_response.json()
        if children.get("has_more"):
            raise RuntimeError("Child pagination needed; incomplete collection must not pass")
        queue.extend((child["id"], sid) for child in children["data"])
record["sessions"] = sessions
record["native_dispatch_observed"] = any(s["dispatches"] for s in sessions)
record["child_plan_completed"] = any((s.get("research_role") or s["sub_agent_name"]) == "planner" and s["assistant_messages"] for s in sessions)
record["collected_at_unix"] = time.time()
record["scope"] = "Actual Omnigent parent/child orchestration; scientific experiments require broker run evidence separately."
record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2))
print(json.dumps({"parent_session_id": parent_id, "sessions": len(sessions),
    "native_dispatch_observed": record["native_dispatch_observed"], "statuses": [s["status"] for s in sessions]}, indent=2))
