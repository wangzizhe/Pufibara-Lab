"""Trusted engineering checks. Never expose this fixture to evaluated agents."""
import json
from pathlib import Path
from physicslab.runner import DockerRunner
from physicslab.ledger import Ledger


root = Path(__file__).resolve().parents[1]
settings = json.loads((root / "configs/runtime.json").read_text())
runner = DockerRunner(root, settings)
ledger = Ledger(root / ".runtime/ledger.sqlite", settings)
source = (root / "tasks/cooling/Cooling.mo").read_text()
cases = [("trusted-corrected-fixture", source.replace("G * (T - T_ambient)", "G * (T_ambient - T)")),
         ("syntax-error-fixture", source.replace("C * der(T) =", "C * der(T) =="))]
summary = {"kind": "engineering_smoke_not_agent_research", "cases": []}
for label, candidate in cases:
    reservation = ledger.reserve("tool")
    try:
        result = runner.execute(candidate, "raw", final=True)
        result["engineering_label"] = label
        ledger.record("engineering_run", result)
        summary["cases"].append({"label": label, "run_id": result["run_id"], "evaluation": result["evaluation"], "seconds": result["seconds"]})
    finally:
        ledger.settle(reservation, 0, 0)
(root / "evidence/engineering-smoke.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
assert summary["cases"][0]["evaluation"]["all_passed"]
assert summary["cases"][1]["evaluation"]["model_checking"] == "failed"
assert summary["cases"][1]["evaluation"]["behavior"]["status"] == "not_run"
