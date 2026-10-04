"""macOS agent-process confinement probe using a new synthetic host marker."""
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
home = root / ".runtime/agent-home"
home.mkdir(parents=True, exist_ok=True)
canary = root / ".runtime/trusted-canary"
canary.write_text("synthetic-denied-marker")
allowed = root / "agents/sandbox-marker"
allowed.write_text("synthetic-allowed-marker")
read_roots = [str(root / ".venv"), str(root / "agents"), str(home)]
read_exclusions = "\n".join(f'(require-not (subpath {json.dumps(p)}))' for p in read_roots)
profile = f'''(version 1)
(allow default)
(deny file-read-data (require-all (subpath "/Users") {read_exclusions}))
(deny file-write* (require-all (require-not (subpath {json.dumps(str(home))})) (require-not (subpath "/dev"))))
(deny network-outbound (require-not (remote ip "localhost:8765")))
(deny network-inbound)
'''
profile_path = root / ".runtime/agent.sb"
profile_path.write_text(profile)
code = '''import json, pathlib
import omnigent
allowed = pathlib.Path(%r).read_text() == "synthetic-allowed-marker"
try:
    pathlib.Path(%r).read_text()
    denied = False
except PermissionError:
    denied = True
print(json.dumps({"allowed_marker_read": allowed, "trusted_marker_denied": denied, "omnigent_imported": True}))
assert allowed and denied
''' % (str(allowed), str(canary))
command = ["/usr/bin/sandbox-exec", "-f", str(profile_path), str(root / ".venv/bin/python"), "-c", code]
result = subprocess.run(command, env={"HOME": str(home), "PATH": str(root / ".venv/bin") + ":/usr/bin:/bin", "TMPDIR": str(home)}, cwd=home, capture_output=True, text=True, timeout=30)
record = {"kind": "agent_process_synthetic_marker_probe", "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
          "scope": "Host user data under /Users denied except venv, agent packages and agent-home; system runtime paths remain readable. Python/Omnigent import and synthetic marker allow/deny only. Full live Omnigent server, network boundary and per-trial conversation separation not yet verified.",
          "passed": result.returncode == 0}
(root / "evidence/agent-isolation.json").write_text(json.dumps(record, indent=2))
with (root / "evidence/agent-isolation-history.jsonl").open("a") as stream:
    stream.write(json.dumps(record) + "\n")
print(json.dumps(record, indent=2))
allowed.unlink(missing_ok=True); canary.unlink(missing_ok=True)
raise SystemExit(result.returncode)
