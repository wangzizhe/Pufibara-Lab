"""Loopback capability broker. Agents receive JSON, never host paths/oracles.

Trusted operator starts this outside the agent sandbox. Bearer capabilities are
created in a private runtime directory. No generic shell/file/network endpoint.
"""
import hashlib
import json
import secrets
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .contracts import identifier, validate_analysis, validate_plan
from .ledger import Ledger
from .runner import DockerRunner


class ResearchSession:
    def __init__(self, root, settings, resume_id=None):
        self.root = Path(root)
        self.settings = settings
        self.runner = DockerRunner(root, settings)
        self.sid = identifier(resume_id) if resume_id else "session-" + uuid.uuid4().hex
        self.folder = self.root / "evidence/sessions" / self.sid
        self.kind = "live_pending"
        if resume_id:
            if self.folder.is_symlink() or not self.folder.is_dir():
                raise ValueError("Existing trusted session directory required")
            saved = json.loads((self.folder / "session.json").read_text())
            if saved["session_id"] != self.sid or saved["runtime"] != settings:
                raise ValueError("Session or runtime changed; do not resume with different controls/budgets")
            self.stage = saved["stage"]
            self.plans = saved["plans"]
            self.trials = saved["trials"]
            self.analysis = saved["analysis"]
            self.kind = saved["kind"]
        else:
            self.folder.mkdir(parents=True, exist_ok=False)
            self.stage = "planning"
            self.plans = []
            self.trials = []
            self.analysis = None
        self.ledger = Ledger(self.folder / "ledger.sqlite", settings)
        if resume_id and self.ledger.unsettled():
            raise RuntimeError("Unsettled work exists; inspect actual processes and evidence before resuming. No automatic retry or budget reset.")
        self.lock = threading.Lock()
        self.capabilities = {secrets.token_urlsafe(32): role for role in ("coordinator", "planner", "executor", "analyst", "modeler")}
        if resume_id:
            self.ledger.record("session_resumed", {"session_id": self.sid, "stage": self.stage, "capabilities_rotated": True})
        self.persist()

    def persist(self):
        record = {"session_id": self.sid, "stage": self.stage, "plans": self.plans, "trials": self.trials, "analysis": self.analysis,
                  "kind": self.kind, "runtime": self.settings}
        staging = self.folder / "session.tmp"
        staging.write_text(json.dumps(record, indent=2))
        staging.replace(self.folder / "session.json")

    def call(self, role, action, payload):
        allowed = {
            "coordinator": {"status"}, "planner": {"status", "record_plan"},
            "executor": {"status", "start_trial", "finish_trial"},
            "modeler": {"task", "attempt", "raw_log"},
            "analyst": {"status", "trial_evidence", "record_analysis"},
        }
        if action not in allowed.get(role, set()):
            raise PermissionError("Role cannot use this tool")
        with self.lock:
            self.ledger.record("tool_request", {"role": role, "action": action, "payload_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()})
            try:
                result = self.dispatch(action, payload)
            except Exception as exc:
                self.ledger.record("tool_failure", {"role": role, "action": action, "error": str(exc)})
                self.persist()
                raise
            self.ledger.record("tool_response", {"role": role, "action": action, "result": result})
            self.persist()
            return result

    def dispatch(self, action, payload):
        if action == "status":
            return {"session_id": self.sid, "stage": self.stage, "plans": self.plans,
                    "available_tasks": [{"id": task_id, "baseline_first": task_id == "cooling-init-v1",
                                         "description": "Lumped thermal cooling; initialization diagnostic case" if task_id == "cooling-init-v1" else "Lumped thermal cooling; sign error case"}
                                        for task_id in self.task_catalog()],
                    "max_tool_runs": self.settings["max_tool_runs"],
                    "trials": [dict({k: v for k, v in t.items() if k not in ("source", "attempts")},
                                    attempt_count=len(t["attempts"])) for t in self.trials], "analysis": self.analysis}
        if action == "trial_evidence":
            trial_id = identifier(payload["trial_id"])
            trial = next((t for t in self.trials if t["trial_id"] == trial_id), None)
            if trial is None or not trial["finished"]:
                raise PermissionError("Only this session's finished trials may be analyzed")
            include_raw = payload.get("include_raw", False)
            if type(include_raw) is not bool:
                raise ValueError("include_raw must be a boolean")
            attempts = []
            for rid in trial["attempts"]:
                record = json.loads((self.root / "evidence/runs" / identifier(rid) / "result.json").read_text())
                feedback = dict(record["feedback"])
                if "raw" in feedback:
                    raw = feedback.pop("raw")
                    feedback.update(raw_characters=len(raw), raw_available=True)
                entry = {"run_id": rid, "status": record["status"], "seconds": record["seconds"],
                         "mechanism": record["mechanism"], "feedback": feedback}
                if include_raw:
                    entry.update(raw=record["raw"][:32000], raw_truncated=len(record["raw"]) > 32000)
                attempts.append(entry)
            return {"trial_id": trial_id, "config": trial["config"], "attempt_count": len(attempts),
                    "attempts": attempts, "final_run_id": trial["final_run_id"],
                    "evaluation": trial["evaluation"], "tool_seconds": trial["tool_seconds"],
                    "scope": "Development feedback and public final verdict only; no source or hidden oracle"}
        if action == "record_plan":
            if self.stage != "planning": raise ValueError("Not accepting initial plans")
            plan = validate_plan(payload["plan"], self.settings["max_tool_runs"])
            self.check_task_ids(plan)
            # Include per-trial final evaluation in total deterministic tool budget.
            if sum(r["max_attempts"] + 1 for r in plan["runs"]) > self.settings["max_tool_runs"]:
                raise ValueError("Plan worst-case tool cost exceeds session budget")
            self.plans.append(plan); self.stage = "experiment"
            return {"accepted": True, "plan_id": plan["id"]}
        if action == "start_trial":
            if self.stage not in ("experiment", "followup"): raise ValueError("Not executing")
            if any(not t["finished"] for t in self.trials): raise ValueError("One active trial at a time")
            plan = self.plans[-1]
            done = sum(t["plan_id"] == plan["id"] for t in self.trials)
            if done >= len(plan["runs"]): raise ValueError("All planned trials started")
            config = plan["runs"][done]
            trial = {"trial_id": "trial-" + uuid.uuid4().hex, "plan_id": plan["id"], "config": config,
                     "attempts": [], "source": None, "finished": False}
            self.trials.append(trial)
            return {"trial_id": trial["trial_id"], "config": config, "task": self.task(config["task_id"])}
        if action == "task":
            trial = self.active(payload["trial_id"])
            return {"config": trial["config"], "task": self.task(trial["config"]["task_id"])}
        if action == "attempt":
            trial = self.active(payload["trial_id"])
            if len(trial["attempts"]) >= trial["config"]["max_attempts"]: raise RuntimeError("Repair budget exhausted")
            source = payload["source"]
            if not isinstance(source, str): raise ValueError("Source must be text")
            task = self.task(trial["config"]["task_id"])
            if task.get("baseline_first") and not trial["attempts"] and source != task["source"]:
                raise ValueError("First attempt must run the unmodified public baseline; it counts toward the allowance")
            result = self.execute(source, trial["config"]["diagnostics"], False)
            trial["attempts"].append(result["run_id"]); trial["source"] = source
            # No hidden behavior criterion, oracle or final evaluation is returned.
            return {"run_id": result["run_id"], "status": result["status"], "feedback": result["feedback"],
                    "attempts_remaining": trial["config"]["max_attempts"] - len(trial["attempts"])}
        if action == "raw_log":
            trial = self.active(payload["trial_id"])
            rid = identifier(payload["run_id"])
            if rid not in trial["attempts"]: raise PermissionError("Only current trial logs accessible")
            return {"run_id": rid, "raw": (self.root / "evidence/runs" / rid / "raw.log").read_text()}
        if action == "finish_trial":
            trial = self.active(payload["trial_id"])
            if trial["source"] is None: raise ValueError("No candidate submitted")
            result = self.execute(trial["source"], trial["config"]["diagnostics"], True)
            trial["finished"] = True
            trial["final_run_id"] = result["run_id"]
            evaluation = result["evaluation"]
            trial["evaluation"] = {"model_checking": evaluation["model_checking"], "simulation": evaluation["simulation"],
                                   "behavior": evaluation["behavior"]["status"], "all_passed": evaluation["all_passed"]}
            trial["tool_seconds"] = sum(json.loads((self.root / "evidence/runs" / rid / "result.json").read_text())["seconds"] for rid in trial["attempts"] + [result["run_id"]])
            plan = self.plans[-1]
            if sum(t["plan_id"] == plan["id"] and t["finished"] for t in self.trials) == len(plan["runs"]):
                self.stage = "analysis" if len(self.plans) == 1 else "validated"
            return {"trial_id": trial["trial_id"], "run_id": result["run_id"], "evaluation": trial["evaluation"], "stage": self.stage}
        if action == "record_analysis":
            if self.stage != "analysis": raise ValueError("Initial experiments must finish first")
            run_ids = [t["final_run_id"] for t in self.trials if t["finished"]]
            analysis = validate_analysis(payload["analysis"], run_ids, self.plans[0])
            self.check_task_ids(analysis["followup"])
            planned = sum(r["max_attempts"] + 1 for p in self.plans + [analysis["followup"]] for r in p["runs"])
            if planned > self.settings["max_tool_runs"]: raise ValueError("Followup exceeds combined worst-case budget")
            self.analysis = analysis; self.plans.append(analysis["followup"]); self.stage = "followup"
            return {"accepted": True, "followup_id": self.plans[-1]["id"]}
        raise ValueError("Unknown action")

    def execute(self, source, mechanism, final):
        rid = self.ledger.reserve("tool")
        try:
            result = self.runner.execute(source, mechanism, final)
            self.ledger.record("run", result)
            return result
        except Exception as exc:
            self.ledger.record("tool_failure", {"error": str(exc)})
            raise
        finally:
            self.ledger.settle(rid, 0, 0)

    def active(self, trial_id):
        identifier(trial_id)
        for trial in self.trials:
            if trial["trial_id"] == trial_id and not trial["finished"]: return trial
        raise ValueError("No such active trial")

    def check_task_ids(self, plan):
        if any(r["task_id"] not in self.task_catalog() for r in plan["runs"]):
            raise ValueError("Unsupported task; configure trusted task catalog first")

    def task(self, task_id):
        catalog = self.task_catalog()
        if task_id not in catalog: raise ValueError("Unknown task")
        folder = self.root / "tasks" / catalog[task_id]
        task = json.loads((folder / "task.json").read_text())
        task["source"] = (folder / "Cooling.mo").read_text()
        return task

    def task_catalog(self):
        # Catalog selected by trusted configuration, never by agent paths.
        if self.settings.get("task_catalog") == "initialization-v1":
            return {"cooling-init-v1": "cooling-init"}
        return {"cooling-sign-v1": "cooling"}


def serve(root, settings, port=8765, resume_id=None):
    session = ResearchSession(root, settings, resume_id=resume_id)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass  # Never log authentication headers.

        def do_POST(self):
            try:
                if self.path != "/call": raise ValueError("Unknown endpoint")
                token = self.headers.get("Authorization", "").removeprefix("Bearer ")
                role = session.capabilities.get(token)
                if role is None: raise PermissionError("Unauthorized")
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 65536: raise ValueError("Invalid request size")
                data = json.loads(self.rfile.read(length))
                result = session.call(role, data["action"], data.get("payload", {}))
                code = 200
            except PermissionError as exc: result, code = {"error": str(exc)}, 403
            except (ValueError, KeyError, RuntimeError, TypeError) as exc: result, code = {"error": str(exc)}, 400
            except Exception: result, code = {"error": "Infrastructure error; see trusted evidence"}, 500
            content = json.dumps(result).encode()
            self.send_response(code); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(content))); self.end_headers(); self.wfile.write(content)
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    file = Path(root) / ".runtime/capabilities.json"
    staging = file.with_suffix(".tmp")
    staging.touch(mode=0o600)
    staging.chmod(0o600)
    staging.write_text(json.dumps({"session_id": session.sid, "url": f"http://127.0.0.1:{port}/call", "capabilities": {r: t for t, r in session.capabilities.items()}}))
    staging.replace(file)
    print(json.dumps({"session_id": session.sid, "broker": f"http://127.0.0.1:{port}", "stage": session.stage}), flush=True)
    try: server.serve_forever()
    finally: server.server_close(); file.unlink(missing_ok=True)
