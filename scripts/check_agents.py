"""Parse agent packages without model calls or reading environment credentials."""
import json
from pathlib import Path
from omnigent.spec.parser import parse
from omnigent.tools.local import load_local_python_tools
from omnigent.spec.validator import validate


root = Path(__file__).resolve().parents[1]
spec = parse(root / "agents/lab", expand_env=False)
def check(spec, folder):
    result = validate(spec)
    if not result.valid:
        raise ValueError([(e.path, e.message) for e in result.errors])
    tools = load_local_python_tools(spec.local_tools, folder, srt_available=False, uv_available=False)
    advertised = {t.name() for t in tools}
    declared = {t.name for t in spec.local_tools}
    if advertised != declared:
        raise ValueError("Tool file stems must match decorated names for native dispatch")
    record = {"name": spec.name, "tools": [t.name() for t in tools], "children": []}
    for child in spec.sub_agents:
        record["children"].append(check(child, folder / "agents" / child.name))
    return record

result = {"status": "schema_and_tools_checked_not_live", "agent": check(spec, root / "agents/lab")}
(root / "evidence/agent-spec-check.json").write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
