"""Start the project Omnigent host with broker role capabilities, never print them."""
import json
import os
import subprocess
import argparse
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--phase', choices=['research', 'enhancement', 'demo'], default='research')
phase = parser.parse_args().phase
capfile = root / ".runtime/capabilities.json"
caps = json.loads(capfile.read_text())["capabilities"]
(root / ".runtime/active-model-phase.json").write_text(json.dumps({"phase": phase}))
env = {"HOME": str(root / ".runtime/home"), "CODEX_HOME": str(root / ".runtime/codex-home"),
    "OMNIGENT_DATA_DIR": str(root / ".runtime/omnigent-ui"),
    "OMNIGENT_CONFIG_HOME": str(root / ".runtime/omnigent-ui"),
    "PATH": str(root / ".venv/bin") + ":/opt/homebrew/bin:/usr/bin:/bin",
    "OMNIGENT_CODEX_PATH": "/opt/homebrew/bin/codex",
    "OMNIGENT_RUNNER_ZYGOTE": "0",
    "PHYSICSLAB_MODEL_PHASE": phase}
for role in ["coordinator", "planner", "executor", "analyst", "modeler"]:
    env["PHYSICSLAB_" + role.upper() + "_CAPABILITY"] = caps[role]
env["OMNIGENT_RUNNER_ENV_PASSTHROUGH"] = ",".join("PHYSICSLAB_" + role.upper() + "_CAPABILITY" for role in ["coordinator", "planner", "executor", "analyst", "modeler"])
print("Starting dedicated research host; role capabilities are not printed.", flush=True)
raise SystemExit(subprocess.call([str(root / ".venv/bin/omnigent"), "host", "--server",
    "http://127.0.0.1:6768", "--no-open", "--non-interactive"],
    env=env, cwd=root / ".runtime/agent-work"))
