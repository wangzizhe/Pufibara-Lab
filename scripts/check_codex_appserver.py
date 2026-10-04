"""Initialize Omnigent's contained Codex transport offline; never start a turn."""
import asyncio
import ast
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

from omnigent.inner.codex_executor import _CodexAppServerSession
from omnigent.inner.datamodel import OSEnvSpec, OSEnvSandboxSpec

root = Path(__file__).resolve().parents[1]
from physicslab.codex_harness import protect_worker_files
protect_worker_files(root)
work = root / ".runtime/appserver-probe"
work.mkdir(parents=True, exist_ok=True)
auth_home = root / ".runtime/codex-home"
parser = argparse.ArgumentParser()
parser.add_argument("--trusted-control", action="store_true")
parser.add_argument("--account-network", action="store_true",
    help="Permit trusted CLI account discovery only; no Agent/model turn is started")
parser.add_argument("--filtered-network", action="store_true",
    help="Validate account discovery through request-budget proxy; no model turn")
parser.add_argument("--live", action="store_true", help="One authorized live transport probe through budget gate")
args = parser.parse_args()
if args.live and not args.filtered_network:
    parser.error("--live requires --filtered-network")
# All ambient state is replaced; only the user's new project login is bridged.
os.environ.clear()
os.environ.update({"HOME": str(root / ".runtime/home"),
    "CODEX_HOME": str(auth_home), "PATH": "/opt/homebrew/bin:/usr/bin:/bin"})


async def main():
    gate_budget = None
    proxy_module = None
    original_check = None
    subscription_ready = False
    if args.filtered_network:
        sys.path.insert(0, str(root / "src"))
        from physicslab.request_budget import RequestBudget, SubscriptionRequestGate
        from omnigent.inner.egress import proxy as proxy_module
        pilot = json.loads((root / "configs/codex-pilot.json").read_text())
        if args.live and not pilot.get("authorization_confirmed"):
            raise PermissionError("Pilot authorization missing")
        gate_budget = RequestBudget(max_requests=pilot["max_model_requests"],
            wall_seconds=pilot["max_wall_seconds"],
            journal=root / ".runtime" / ("pilot-requests.jsonl" if args.live else "gate-probe-%d.jsonl" % time.time_ns()))
        gate = SubscriptionRequestGate(gate_budget, lambda: subscription_ready)
        original_check = proxy_module.check_request
        proxy_module.check_request = lambda rules, method, host, path: gate.check(
            original_check, rules, method, host, path)
    spec = OSEnvSpec(cwd=str(work), sandbox=OSEnvSandboxSpec(
        type="darwin_seatbelt", allow_network=args.account_network,
        read_paths=[str(auth_home), str(root / ".venv")], cwd_allow_hidden=["*"],
        egress_rules=["GET chatgpt.com/backend-api/**",
            "POST chatgpt.com/backend-api/codex/responses"] if args.filtered_network else None,
    ))
    if args.trusted_control:
        spec.sandbox = OSEnvSandboxSpec(type="none")
    session = _CodexAppServerSession(codex_path="/opt/homebrew/bin/codex",
        cwd=str(work), env=dict(os.environ), tool_executor=None,
        codex_config_overrides=['web_search="disabled"', 'model_provider="openai"',
            'cli_auth_credentials_store="file"',
            'features.memories=false', 'features.shell_tool=false',
            'features.unified_exec=false', 'features.responses_websockets=false',
            'features.responses_websockets_v2=false'],
        disable_native_tools=True, skills_filter="none", os_env=spec,
        thread_model_provider="openai")
    record = {"kind": "contained_omnigent_codex_initialize_no_model",
        "model_turn_started": False, "network_allowed": args.trusted_control or args.account_network,
        "trusted_control": args.trusted_control}
    stage = "initialize"
    try:
        await asyncio.wait_for(session.start(), 30)
        record.update({"initialized": True, "sandboxed": session._containment_confirmed})
        stage = "offline_account_type"
        response = await asyncio.wait_for(session._request("account/read", {
            "refreshToken": False}), 10)
        account = response.get("result", {}).get("account") or {}
        record.update({"initialized": True,
            "sandboxed": session._containment_confirmed,
            "account_type": account.get("type"),
            "passed": (session._containment_confirmed or args.trusted_control) and account.get("type") == "chatgpt"})
        if args.account_network or args.filtered_network:
            stage = "subscription_limits"
            limits_response = await asyncio.wait_for(session._request("account/rateLimits/read", {}), 10)
            limits_result = limits_response.get("result", {})
            limits = limits_result.get("rateLimits") or {}
            credits = limits.get("credits") or {}
            record["subscription_limits"] = {
                "primary_used_percent": (limits.get("primary") or {}).get("usedPercent"),
                "secondary_used_percent": (limits.get("secondary") or {}).get("usedPercent"),
                "has_credits": credits.get("hasCredits"),
                "credits_unlimited": credits.get("unlimited"),
            }
            if args.live:
                info = record["subscription_limits"]
                subscription_ready = (info["has_credits"] is False and
                    info["credits_unlimited"] is False and all(
                        isinstance(info[key], (int, float)) and info[key] < 90
                        for key in ["primary_used_percent", "secondary_used_percent"]))
                if not subscription_ready:
                    raise PermissionError("Subscription-only readiness unknown or unsafe")
                listing = await asyncio.wait_for(session._request("model/list", {}), 15)
                models = listing.get("result", {}).get("data", [])
                model = next((item["model"] for item in models if item.get("isDefault")), None)
                if model is None:
                    raise RuntimeError("No native default model available")
                record["model"] = model
                calls = []
                def probe_tool(name, payload):
                    if name != "public_probe" or payload != {}:
                        raise PermissionError("Unexpected tool or arguments")
                    calls.append(name)
                    return {"result": {"probe": "real_local_tool", "nonce": "thermal-probe-20261004"}}
                session._tool_executor = probe_tool
                from omnigent.inner.executor import TurnComplete
                stage = "live_transport"
                record["model_turn_started"] = True
                async def run_probe():
                    async for event in session.run_turn(messages=[{"role": "user", "content":
                        "Call public_probe exactly once, then report its nonce in one sentence."}],
                        tools=[{"name": "public_probe", "description": "Read a local transport probe nonce.",
                            "parameters": {"type": "object", "properties": {}, "additionalProperties": False}}],
                        system_prompt="You are checking transport, not conducting a scientific experiment. Use only public_probe.",
                        model=model, cwd=str(work), sandbox="read-only", reasoning_effort="low"):
                        if isinstance(event, TurnComplete):
                            record["response"] = event.response
                            record["usage"] = event.usage
                await asyncio.wait_for(run_probe(), max(1, gate_budget.deadline - time.monotonic()))
                record["tool_calls"] = calls
                record["passed"] = calls == ["public_probe"] and "thermal-probe-20261004" in record.get("response", "")
    except Exception as exc:
        # Do not serialize response bodies, auth metadata or exception messages.
        detail = str(exc).lower() + " " + " ".join(session._recent_stderr).lower()
        keywords = ["permission denied", "operation not permitted", "invalid", "client",
            "config", "sqlite", "database", "auth", "no such file", "timeout", "exited",
            "closed", "transport", "failed", "broken", "killed", "not found"]
        # App-server RPC errors are structured; retain only numeric code and
        # ordinary diagnostic words, never arbitrary strings/account identifiers.
        words = ["load", "loading", "state", "log", "directory", "create", "creating",
            "open", "read", "write", "file", "not", "initialized", "initialize",
            "persist", "runtime", "thread", "spawn", "working", "failed", "home",
            "preferences", "permission", "permitted", "access", "denied", "ipc",
            "credentials", "credential", "authentication", "account", "parse", "parsing",
            "symlink", "path", "reading", "keychain", "keyring", "refresh", "token",
            "blocking", "task", "thread", "resource", "temporarily", "unavailable",
            "fork", "child", "process", "connection", "proxy", "helper", "os", "error"]
        words += ["cannot", "could", "unable", "to", "subprocess", "permissiondenied",
            "sw", "vers", "security", "login", "status", "environment", "shell",
            "command", "resolve", "get", "current", "cache", "manager", "directory",
            "exec", "execution", "operation", "authorization", "aborted", "system",
            "service", "worker", "agent", "appserver", "user", "library", "tmp",
            "assertion", "activity", "sandbox", "homebrew", "bin", "codex"]
        record.update({"passed": False, "error_type": type(exc).__name__, "stage": stage,
            "errno_names": [name for name in ["EACCES", "ENOENT", "EPERM", "ENOMEM", "EAGAIN"] if name.lower() in detail],
            "generated_launcher_paths": re.findall(r"/tmp/omnigent[-_/a-z0-9.]+", detail),
            "diagnostic_words": [word for word in words if word in re.findall(r"[a-z]+", detail)],
            "error_keywords": [word for word in keywords if word in detail]})
        try:
            structured = ast.literal_eval(str(exc))
            if isinstance(structured, dict) and isinstance(structured.get("code"), int):
                record["rpc_error_code"] = structured["code"]
                record["rpc_message_is_spawn_failed"] = structured.get("message", "").lower() == "spawn failed"
                message = structured.get("message", "")
                if isinstance(message, str):
                    prefix = message.split("\n", 1)[0].split(":", 1)[0]
                    if re.fullmatch(r"[A-Za-z _-]{1,70}", prefix):
                        record["rpc_error_category"] = prefix
                if isinstance(message, str) and re.fullmatch(r"[a-z_]{1,40}", message):
                    record["rpc_error_identifier"] = message
        except (ValueError, SyntaxError):
            pass
    finally:
        await session.close()
        if gate_budget is not None:
            record["reserved_model_requests"] = gate_budget.requests
            gate_budget.close()
            proxy_module.check_request = original_check
    record["filtered_network"] = args.filtered_network
    record["scope"] = "Actual app-server initialized and account type checked; no inference or live tool delegation tested. Trusted account discovery may need network."
    filename = "codex-live-transport.json" if args.live else "codex-appserver-control.json" if args.trusted_control else "codex-appserver.json"
    (root / "evidence" / filename).write_text(json.dumps(record, indent=2))
    with (root / "evidence/codex-appserver-history.jsonl").open("a") as stream:
        stream.write(json.dumps(record) + "\n")
    print(json.dumps(record, indent=2))
    return 0 if record["passed"] else 1


raise SystemExit(asyncio.run(main()))
