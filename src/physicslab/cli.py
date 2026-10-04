import argparse
import json
from pathlib import Path
from .contracts import validate_plan
from .ledger import Ledger
from .runner import DockerRunner


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--runtime", choices=["default", "enhancement"], default="default")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("probe")
    broker = commands.add_parser("broker")
    broker.add_argument("--port", type=int, default=8765)
    broker.add_argument("--resume", help="Resume a session with unchanged runtime and settled work only")
    check = commands.add_parser("validate-plan")
    check.add_argument("plan")
    run = commands.add_parser("evaluate")
    run.add_argument("source")
    run.add_argument("--diagnostics", choices=["raw", "structured"], default="raw")
    run.add_argument("--final", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    settings = json.loads((root / ("configs/runtime-enhancement.json" if args.runtime == "enhancement" else "configs/runtime.json")).read_text())
    if args.command == "broker":
        from .broker import serve
        serve(root, settings, args.port, args.resume)
        return
    if args.command == "validate-plan":
        result = validate_plan(json.loads(Path(args.plan).read_text()), settings["max_tool_runs"])
    else:
        runner = DockerRunner(root, settings)
        if args.command == "probe":
            result = runner.probe()
            (root / "evidence/isolation.json").write_text(json.dumps(result, indent=2))
        else:
            ledger = Ledger(root / ".runtime/ledger.sqlite", settings)
            reservation = ledger.reserve("tool")
            try:
                result = runner.execute(Path(args.source).read_text(), args.diagnostics, args.final)
                ledger.record("run", result)
            except Exception as exc:
                ledger.record("tool_failure", {"error": str(exc)})
                raise
            finally:
                ledger.settle(reservation, 0, 0)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
