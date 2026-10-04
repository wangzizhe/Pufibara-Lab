"""Record an actual operator measurement; never estimate missing human time."""
import argparse
import json
import time
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
sub = parser.add_subparsers(dest="command", required=True)
start = sub.add_parser("start")
start.add_argument("mode", choices=["manual", "automatic"])
start.add_argument("--operator", required=True)
start.add_argument("--condition", required=True, help="Matched task, model, budget and tools identifier")
event = sub.add_parser("event")
event.add_argument("measurement_id"); event.add_argument("label")
end = sub.add_parser("end")
end.add_argument("measurement_id"); end.add_argument("--report", required=True)
args = parser.parse_args()
folder = root / "evidence/measurements"; folder.mkdir(parents=True, exist_ok=True)
if args.command == "start":
    mid = "measurement-" + uuid.uuid4().hex
    data = {"id": mid, "mode": args.mode, "operator": args.operator, "condition": args.condition,
            "started_at": time.time(), "events": [], "status": "running", "setup_seconds": None}
else:
    mid = args.measurement_id
    from physicslab.contracts import identifier
    identifier(mid)
    data = json.loads((folder / (mid + ".json")).read_text())
    if data["status"] != "running": raise ValueError("Measurement already finished")
    if args.command == "event":
        data["events"].append({"at": time.time(), "label": args.label})
    else:
        report = Path(args.report).resolve()
        if not report.is_file() or not report.is_relative_to(root): raise ValueError("Existing project report required")
        data.update(status="finished", ended_at=time.time(), report=str(report.relative_to(root)))
        data["elapsed_seconds"] = data["ended_at"] - data["started_at"]
        data["operator_actions"] = len(data["events"])
(folder / (mid + ".json")).write_text(json.dumps(data, indent=2, ensure_ascii=False))
print(json.dumps(data, indent=2, ensure_ascii=False))
