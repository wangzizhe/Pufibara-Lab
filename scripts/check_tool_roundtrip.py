"""Actual Omnigent local-tool subprocess -> broker; no LLM and no experiment."""
import json
import os
import signal
import subprocess
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
home = root / ".runtime/agent-home"
env = {"HOME": str(root / ".runtime/home"), "PATH": str(root / ".venv/bin") + ":/usr/bin:/bin", "PYTHONPATH": str(root / "src")}
cap_path = root / ".runtime/capabilities.json"
cap_path.unlink(missing_ok=True)
broker = subprocess.Popen([str(root / ".venv/bin/python"), "-m", "physicslab.cli", "broker"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
try:
    deadline = time.monotonic() + 10
    while not cap_path.is_file():
        if broker.poll() is not None: raise RuntimeError("Broker failed to start")
        if time.monotonic() > deadline: raise TimeoutError("Broker startup")
        time.sleep(0.05)
    caps = json.loads(cap_path.read_text())
    agent_env = {"HOME": str(home), "TMPDIR": str(home), "PATH": str(root / ".venv/bin") + ":/usr/bin:/bin", "PHYSICSLAB_COORDINATOR_CAPABILITY": caps["capabilities"]["coordinator"]}
    code = '''import json, socket
from pathlib import Path
from omnigent.spec.parser import parse
from omnigent.tools.local import load_local_python_tools
from omnigent.tools.base import ToolContext
folder = Path(%r)
spec = parse(folder, expand_env=False)
tools = load_local_python_tools(spec.local_tools, folder, srt_available=False, uv_available=False)
tool = next(t for t in tools if t.name() == "status")
response = json.loads(tool.invoke("{}", ToolContext(task_id="engineering-roundtrip", agent_id="coordinator")))
assert response["stage"] == "planning", response
try:
    socket.create_connection(("127.0.0.1", 9), timeout=0.5)
    network_denied = False
except PermissionError:
    network_denied = True
except OSError:
    network_denied = False
assert network_denied
print(json.dumps({"status_tool": "passed", "session_id": response["session_id"], "other_network_denied": network_denied, "kind": "tool_transport_check_not_multi_agent_research"}))
''' % str(root / "agents/lab")
    command = ["/usr/bin/sandbox-exec", "-f", str(root / ".runtime/agent.sb"), str(root / ".venv/bin/python"), "-c", code]
    child = subprocess.run(command, env=agent_env, cwd=home, capture_output=True, text=True, timeout=30)
    record = {"exit_code": child.returncode, "stdout": child.stdout, "stderr": child.stderr, "passed": child.returncode == 0, "kind": "tool_transport_check_not_live_agent_handoff"}
    session_file = root / "evidence/sessions" / caps["session_id"] / "session.json"
    session = json.loads(session_file.read_text()); session["kind"] = "engineering_tool_transport_check"
    session_file.write_text(json.dumps(session, indent=2))
    (root / "evidence/tool-roundtrip.json").write_text(json.dumps(record, indent=2))
    with (root / "evidence/tool-roundtrip-history.jsonl").open("a") as stream:
        stream.write(json.dumps(record) + "\n")
    print(json.dumps(record, indent=2))
    if child.returncode: raise SystemExit(child.returncode)
finally:
    broker.send_signal(signal.SIGINT)
    try: broker.communicate(timeout=5)
    except subprocess.TimeoutExpired: broker.kill(); broker.communicate()
    cap_path.unlink(missing_ok=True)
