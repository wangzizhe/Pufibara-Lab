"""Exercise Omnigent's actual worker launcher; no model or credential read."""
import json
import os
import subprocess
import sys
from pathlib import Path

from omnigent.inner.codex_worker import prepare_codex_worker
from omnigent.inner.datamodel import OSEnvSpec, OSEnvSandboxSpec

root = Path(__file__).resolve().parents[1]
# Import the installed plugin, not a source-tree evaluator exposed to the worker.
from physicslab.codex_harness import protect_worker_files
import physicslab
protect_worker_files(root)
private_canary = Path(physicslab.__file__).resolve().parent / "worker-synthetic-canary"
private_canary.write_text("synthetic-private-package-marker")
work = root / ".runtime/worker-probe"
home = work / "home"
home.mkdir(parents=True, exist_ok=True)
canary = root / ".runtime/worker-denied-marker"
canary.write_text("synthetic-private-marker")
allowed = work / "allowed-marker"
allowed.write_text("synthetic-public-marker")
env = {"HOME": str(home), "CODEX_HOME": str(home), "PATH": "/opt/homebrew/bin:/usr/bin:/bin"}
spec = OSEnvSpec(cwd=str(work), sandbox=OSEnvSandboxSpec(
    type="darwin_seatbelt", allow_network=False,
    read_paths=[str(root / ".venv")], write_paths=[str(home)],
    cwd_allow_hidden=["*"],
))
checks = []
code = '''import json, pathlib, socket
allowed = pathlib.Path(%r).read_text() == "synthetic-public-marker"
try:
    pathlib.Path(%r).read_text()
    private_denied = False
except PermissionError:
    private_denied = True
try:
    pathlib.Path(%r).read_text()
    trusted_package_denied = False
except PermissionError:
    trusted_package_denied = True
try:
    socket.create_connection(("127.0.0.1", 9), timeout=0.2)
    network_denied = False
except PermissionError:
    network_denied = True
except OSError:
    network_denied = False
print(json.dumps({"allowed_read": allowed, "private_denied": private_denied, "network_denied": network_denied, "trusted_package_denied": trusted_package_denied}))
assert allowed and private_denied and network_denied and trusted_package_denied
''' % (str(allowed), str(canary), str(private_canary))
try:
    for executable, args, name in [
        (str(root / ".venv/bin/python"), ["-c", code], "synthetic_policy_probe"),
        ("/opt/homebrew/bin/codex", ["--version"], "actual_codex_binary"),
    ]:
        launcher = prepare_codex_worker(codex_path=executable, cwd=work,
            codex_home=home, os_env=spec, spawn_env_names=list(env), worker_env=env)
        try:
            result = subprocess.run([launcher.launch_path, *args], env=env,
                cwd=work, capture_output=True, text=True, timeout=30)
            checks.append({"name": name, "sandboxed": launcher.sandboxed,
                "exit_code": result.returncode, "stdout": result.stdout,
                "stderr": result.stderr, "passed": launcher.sandboxed and result.returncode == 0})
        finally:
            launcher.close()
finally:
    canary.unlink(missing_ok=True)
    allowed.unlink(missing_ok=True)
    private_canary.unlink(missing_ok=True)
record = {"kind": "actual_omnigent_worker_launcher_probe_no_model",
    "checks": checks, "passed": all(c["passed"] for c in checks),
    "scope": "Actual Omnigent Seatbelt launcher and Codex executable; synthetic file/network denial. Authenticated app-server and live model/tools still unverified."}
(root / "evidence/codex-worker-isolation.json").write_text(json.dumps(record, indent=2))
with (root / "evidence/codex-worker-isolation-history.jsonl").open("a") as stream:
    stream.write(json.dumps(record) + "\n")
print(json.dumps(record, indent=2))
raise SystemExit(0 if record["passed"] else 1)
