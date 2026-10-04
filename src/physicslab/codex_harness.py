"""Budgeted Codex transport inside Omnigent's real session/agent runtime."""
import asyncio
import json
import os
import time
import sys
import inspect
from pathlib import Path

from omnigent.inner.codex_executor import CodexExecutor, _CodexAppServerSession
from omnigent.inner.datamodel import OSEnvSpec, OSEnvSandboxSpec
from omnigent.inner.egress import proxy
from omnigent.runtime.harnesses._executor_adapter import ExecutorAdapter
from omnigent.inner.executor import TurnComplete

from .request_budget import SharedRequestBudget, SubscriptionRequestGate, validate_demo_authorization

RESEARCH_TOOLS = frozenset({"status", "record_plan", "start_trial", "finish_trial", "task", "attempt",
                           "raw_log", "trial_evidence", "record_analysis", "sys_session_send", "sys_read_inbox"})


def scoped_tool_specs(tools):
    """Advertise only the capability surface enforced by this research runtime."""
    return [tool for tool in tools if tool.get("name") in RESEARCH_TOOLS]


def check_dispatch(tool_name, args):
    """Reject alternate runtimes and broad host tools before native dispatch."""
    forbidden = ("sys_os_", "sys_terminal_", "sys_agent_", "web_", "sys_session_create", "sys_session_share")
    if any(tool_name.startswith(prefix) for prefix in forbidden):
        raise PermissionError("Tool outside research capability surface")
    if tool_name.startswith("sys_session_") and tool_name != "sys_session_send":
        raise PermissionError("Session discovery/history outside declared child handoffs is unavailable")
    if tool_name == "sys_session_send" and ("session_id" in args or set(args) & {"harness", "model", "cost_budget"}):
        raise PermissionError("Only named declared child handoffs are permitted")
    if tool_name == "sys_session_send" and isinstance(args.get("args"), dict):
        if set(args["args"]) & {"harness", "model", "cost_budget"}:
            raise PermissionError("Agent cannot override trusted model, harness or budget")


def protect_worker_files(root):
    """Hide installed trusted evaluator code despite the Python runtime grant."""
    from omnigent.inner import codex_worker
    import physicslab
    from dataclasses import replace
    if getattr(codex_worker.create_exec_launcher, "_physicslab_protected", False):
        return
    original = codex_worker.create_exec_launcher
    private_package = Path(physicslab.__file__).resolve().parent
    def protected(executable, policy, *args, **kwargs):
        # Serialize explicit literal denials into the policy passed to the new
        # launcher process. Parent-process SBPL patches do not survive exec.
        files = [path.resolve() for path in private_package.rglob("*") if path.is_file()]
        policy = replace(policy, credential_source_paths=list(dict.fromkeys(
            [*(policy.credential_source_paths or []), *files])))
        return original(executable, policy, *args, **kwargs)
    protected._physicslab_protected = True
    codex_worker.create_exec_launcher = protected


def build_app():
    from .completion import require_runner_completion_patch
    require_runner_completion_patch()
    root = Path(os.environ["HOME"]).resolve().parent.parent
    if not (root / "configs/codex-pilot.json").is_file():
        raise PermissionError("Dedicated project HOME required")
    protect_worker_files(root)
    phase_file = root / ".runtime/active-model-phase.json"
    phase = json.loads(phase_file.read_text())["phase"] if phase_file.exists() else "pilot"
    if phase not in {"pilot", "research", "enhancement", "demo"}:
        raise PermissionError("Unknown authorized phase")
    pilot = json.loads((root / f"configs/codex-{phase}.json").read_text())
    if not pilot.get("authorization_confirmed") or pilot.get("allow_api_fallback"):
        raise PermissionError("Subscription-only authorization missing")
    if phase == "demo":
        validate_demo_authorization(root, pilot)
    if phase == "enhancement":
        historical = 0
        for old_phase in ("pilot", "research"):
            rows = [json.loads(line) for line in (root / f".runtime/{old_phase}-requests.jsonl").read_text().splitlines()]
            historical += max((r.get("reserved_requests", 0) for r in rows), default=0)
        if historical != pilot["historical_pilot_requests"] + pilot["historical_research_requests"]:
            raise PermissionError("Historical usage changed; audit cumulative authorization before calling")
        if historical + pilot["max_model_requests"] > pilot["cumulative_request_ceiling"]:
            raise PermissionError("Cumulative request authorization would be exceeded")
    budget = SharedRequestBudget(max_requests=pilot["max_model_requests"],
        wall_seconds=pilot["max_wall_seconds"], journal=root / f".runtime/{phase}-requests.jsonl",
        resume=(root / f".runtime/{phase}-requests.jsonl").exists(),
        start_on_first_request=pilot.get("start_on_first_request", False))
    import hashlib
    with (root / "evidence/harness-loads.jsonl").open("a") as stream:
        stream.write(json.dumps({"phase":phase,"at_unix":time.time(),"pid":os.getpid(),
            "implementation_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "requests":budget.requests})+"\n")
    app_ref = {}
    def native_identity():
        app = app_ref.get("app")
        return getattr(app.state, "conversation_id", None) if app is not None else None
    readiness = {"ready": False, "checked_at": 0}
    original = proxy.check_request
    gate = SubscriptionRequestGate(budget, lambda: readiness["ready"]
        and time.monotonic() - readiness["checked_at"] < 60)
    proxy.check_request = lambda rules, method, host, path: gate.check(
        original, rules, method, host, path)

    class PilotSession(_CodexAppServerSession):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            original_tool = self._tool_executor
            async def audited_tool(name, arguments):
                verification = None
                if name in {"task", "attempt"}:
                    import fcntl
                    payload = json.loads(arguments) if isinstance(arguments, str) else arguments
                    trial_id = payload["trial_id"]
                    native_id = native_identity()
                    if not native_id or not self.thread_id or not self._containment_confirmed:
                        raise PermissionError("Native conversation and Codex thread required before attempt")
                    verification = {"verified":True,"session_id":native_id,"codex_thread_id":self.thread_id,
                        "worker_sandboxed":self._containment_confirmed,"base_model":"gpt-6.1-sol",
                        "output_limit":"same_native_cli_default_for_all_trials",
                        "cross_trial_reuse_rejected_before_submission":True}
                    file = root / "evidence/modeler-conversations.jsonl"
                    with file.open("a+") as stream:
                        fcntl.flock(stream, fcntl.LOCK_EX)
                        stream.seek(0)
                        prior = [json.loads(line) for line in stream]
                        for record in prior:
                            if record["trial_id"] != trial_id and (
                                record["codex_thread_id"] == self.thread_id or record["session_id"] == native_id):
                                raise PermissionError("Each trial requires a fresh independent modeler conversation")
                        stream.write(json.dumps({"trial_id":trial_id, "session_id":native_id,
                            "codex_thread_id":self.thread_id, "worker_pid":os.getpid(),
                            "at_unix":time.time(), "verified_before_attempt":True,"checked_before_tool":name}) + "\n")
                        stream.flush()
                        os.fsync(stream.fileno())
                result = original_tool(name, arguments)
                result = await result if inspect.isawaitable(result) else result
                if verification is not None:
                    result = dict(result) if isinstance(result, dict) else {"result":result}
                    result["runtime_verification"] = verification
                if name in {"status", "task"}:
                    rows = [json.loads(line) for line in budget.journal.read_text().splitlines()]
                    auth = next((r for r in reversed(rows) if r.get("event") in {"budget_amended", "budget_started"}), rows[0])
                    result = dict(result) if isinstance(result, dict) else {"result":result}
                    result["model_budget"] = {"phase":phase,"used_requests":max(r.get("reserved_requests",0) for r in rows),
                        "max_requests":auth["max_requests"],"deadline_unix":auth["deadline_unix"],
                        "billing":"existing_subscription_no_extra_credits_no_api"}
                if time.monotonic() - readiness["checked_at"] >= 30:
                    await self.start()
                return result
            self._tool_executor = audited_tool

        async def start(self):
            await super().start()
            if readiness["ready"] and time.monotonic() - readiness["checked_at"] < 30:
                return
            account = (await self._request("account/read", {"refreshToken": False})).get("result", {}).get("account") or {}
            limits = (await self._request("account/rateLimits/read", {})).get("result", {}).get("rateLimits") or {}
            credits = limits.get("credits") or {}
            windows = [limits.get("primary") or {}, limits.get("secondary") or {}]
            ready = account.get("type") == "chatgpt" and credits.get("hasCredits") is False
            ready = ready and credits.get("unlimited") is False and all(
                isinstance(window.get("usedPercent"), (int, float)) and window["usedPercent"] < 90 for window in windows)
            if not ready:
                readiness["ready"] = False
                raise PermissionError("Subscription-only readiness not verified")
            readiness.update(ready=True, checked_at=time.monotonic())

        async def run_turn(self, **kwargs):
            remaining = budget.refresh_deadline() - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Authorized phase deadline exhausted")
            # Pending first-call budgets use a conservative per-turn timeout.
            # The shared journal still anchors the phase clock at the first request.
            if remaining == float("inf"):
                remaining = pilot["max_wall_seconds"]
            try:
                async with asyncio.timeout(remaining):
                    async for event in super().run_turn(**kwargs):
                        if isinstance(event, TurnComplete):
                            import fcntl
                            from omnigent.runtime.telemetry import current_session_id
                            session_key = next((m.get("session_id") for m in kwargs.get("messages", []) if m.get("session_id")), None)
                            record = {"session_id": native_identity() or current_session_id(),
                                "session_key":session_key,"kind":"actual_codex_turn_usage",
                                "usage":event.usage,"usd":None,"billing":"subscription","at_unix":time.time()}
                            with (root / "evidence/codex-role-usage.jsonl").open("a") as stream:
                                fcntl.flock(stream, fcntl.LOCK_EX)
                                stream.write(json.dumps(record)+"\n")
                                stream.flush()
                        yield event
            except Exception as exc:
                import traceback
                record = {"phase":phase,"session_id":native_identity(),"error_type":type(exc).__name__,
                          "at_unix":time.time(),"remaining_at_entry":remaining,
                          "frames":[{"file":Path(f.filename).name,"line":f.lineno,"function":f.name}
                                    for f in traceback.extract_tb(exc.__traceback__)]}
                with (root / "evidence/codex-runtime-errors.jsonl").open("a") as stream:
                    stream.write(json.dumps(record)+"\n")
                raise

    class ScopedCodexExecutor(CodexExecutor):
        async def run_turn(self, messages, tools, system_prompt, config=None):
            async for event in super().run_turn(messages, scoped_tool_specs(tools), system_prompt, config):
                yield event

    def executor_factory():
        work = root / ".runtime/agent-work"
        work.mkdir(parents=True, exist_ok=True)
        spec = OSEnvSpec(cwd=str(work), sandbox=OSEnvSandboxSpec(
            type="darwin_seatbelt", read_paths=[str(root / ".venv"), str(root / ".runtime/codex-home")],
            cwd_allow_hidden=["*"], allow_network=False,
            egress_rules=["GET chatgpt.com/backend-api/**", "POST chatgpt.com/backend-api/codex/responses"]))
        os.environ["CODEX_HOME"] = str(root / ".runtime/codex-home")
        executor = ScopedCodexExecutor(cwd=str(work), os_env=spec, model="gpt-6.1-sol",
            codex_path="/opt/homebrew/bin/codex", model_provider_override="openai",
            app_session_factory=PilotSession, enable_web_search=False,
            disable_native_tools=True, skills_filter="none")
        if any(key.startswith("PHYSICSLAB_") for key in executor._env):
            raise PermissionError("Scoped broker capabilities must not reach model worker")
        executor._codex_config_overrides.extend(['cli_auth_credentials_store="file"',
            'features.memories=false', 'features.shell_tool=false', 'features.unified_exec=false',
            'features.responses_websockets=false', 'features.responses_websockets_v2=false',
            'features.apps=false', 'features.plugins=false'])
        return executor

    class ResearchAdapter(ExecutorAdapter):
        async def run_turn(self, request, ctx):
            native_id = native_identity()
            if not native_id:
                raise PermissionError("Native Omnigent app conversation identity required")
            return await super().run_turn(request, ctx)

        async def _stable_tool_executor(self, tool_name, args, **kwargs):
            check_dispatch(tool_name, args)
            return await super()._stable_tool_executor(tool_name, args, **kwargs)

    app = ResearchAdapter(executor_factory=executor_factory).build()
    app_ref["app"] = app
    app.state.physicslab_native_identity = native_identity
    return app
