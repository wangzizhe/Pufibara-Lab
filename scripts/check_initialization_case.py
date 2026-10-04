"""Trusted engineering fixture; not a model-assisted research result."""
import json
from pathlib import Path
from physicslab.runner import DockerRunner

root = Path(__file__).resolve().parents[1]
settings = json.loads((root / "configs/runtime-enhancement.json").read_text())
runner = DockerRunner(root, settings)
source = (root / "tasks/cooling-init/Cooling.mo").read_text()
cases = []
for label, candidate, final in (
    ("unmodified-initialization-failure", source, False),
    ("trusted-initialization-correction", source.replace("initial equation\n  T = T_ambient;\n", ""), True),
):
    result = runner.execute(candidate, "structured", final)
    cases.append({"label":label,"run_id":result["run_id"],"evaluation":result["evaluation"],
                  "feedback":result["feedback"],"seconds":result["seconds"]})
proof = {"kind":"trusted_engineering_not_agent_research","cases":cases,"model_requests":0,
         "interpretation":"Real initialization feedback exists; baseline-first exposure is a protocol, not proof that source-only repair is impossible."}
(root / "evidence/initialization-case-verification.json").write_text(json.dumps(proof, indent=2)+"\n")
print(json.dumps(proof, indent=2))
assert cases[0]["evaluation"]["model_checking"] == "passed"
assert cases[0]["evaluation"]["simulation"] == "failed"
assert cases[0]["evaluation"]["behavior"]["status"] == "not_run"
assert cases[1]["evaluation"]["all_passed"]
