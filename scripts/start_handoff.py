"""Create a real Omnigent parent and let its model dispatch a declared child."""
import io
import json
import tarfile
import argparse
from pathlib import Path
import httpx

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--research", action="store_true")
parser.add_argument("--enhancement", action="store_true")
parser.add_argument("--validation", action="store_true")
parser.add_argument("--completion-regression", action="store_true")
parser.add_argument("--host-id", default="b4930df7cea24c0f93b5c03f51aa9f3e")
parser.add_argument("--resume-study", action="store_true")
args = parser.parse_args()
if args.validation and not args.enhancement:
    raise ValueError('Validation uses the same enhancement authorization; pass --enhancement')
if args.completion_regression and (not args.enhancement or args.validation):
    raise ValueError('Completion regression requires --enhancement and uses its unchanged budget')
if args.enhancement and (args.research or args.resume_study):
    raise ValueError("Enhancement is separate from historical studies")
phase = 'enhancement' if args.enhancement else 'research'
is_study = args.research or args.enhancement
folder = root / ("agents/lab" if args.research else "agents/pilot")
if args.enhancement:
    folder = root / ('.runtime/enhancement-validation-agent' if args.validation else '.runtime/enhancement-live-agent')
    if (root / ('evidence/omnigent-completion-regression.json' if args.completion_regression else 'evidence/omnigent-enhancement-validation.json' if args.validation else 'evidence/omnigent-enhancement.json')).exists():
        raise FileExistsError('Enhancement already started; preserve its parent')
if args.completion_regression:
    folder = root/'.runtime/completion-regression-agent'
if is_study:
    if not (root / ".runtime/capabilities.json").is_file():
        raise RuntimeError("Start trusted broker and research_host first")
    authorization = json.loads((root / f"configs/codex-{phase}.json").read_text())
    if not authorization.get("authorization_confirmed"):
        raise RuntimeError("Research authorization missing")
    journal_path = root / f".runtime/{phase}-requests.jsonl"
    if journal_path.exists():
        import time
        rows = [json.loads(line) for line in journal_path.read_text().splitlines()]
        header = next((r for r in reversed(rows) if r.get("event") in {"budget_amended", "budget_started"}), rows[0])
        if header["deadline_unix"] is not None and header["deadline_unix"] <= time.time():
            raise RuntimeError("Research authorization expired; do not reset journal")

bundle = io.BytesIO()
with tarfile.open(fileobj=bundle, mode="w:gz") as tar:
    for path in sorted(folder.rglob("*")):
        if path.is_file():
            tar.add(path, arcname=str(path.relative_to(folder)))
metadata = {"title": "Pufibara Lab: Handoff Verification" if args.completion_regression else "Pufibara Lab: Initialization Study" if args.enhancement else "物理建模 Harness 科研闭环" if args.research else "受限科研规划交接试运行", "host_id": args.host_id,
    "workspace": str(root / ".runtime/agent-work"), "reasoning_effort": "low"}
with httpx.Client(base_url="http://127.0.0.1:6768", timeout=60) as client:
    hosts = client.get('/v1/hosts'); hosts.raise_for_status()
    if not any(h['host_id'] == args.host_id and h['status'] == 'online' for h in hosts.json()['hosts']):
        raise RuntimeError('Selected project host is not online')
    response = client.post("/v1/sessions", data={"metadata": json.dumps(metadata)},
        files={"bundle": ("pilot.tar.gz", bundle.getvalue(), "application/gzip")})
    response.raise_for_status()
    created = response.json()
    session_id = created.get("id") or created.get("session_id")
    if not session_id:
        raise RuntimeError("Session create returned no ID")
    record = {"parent_session_id": session_id, "kind": "real_completion_regression_pending" if args.completion_regression else "real_research_pending" if is_study else "real_omnigent_handoff_pending",
        "bundle": str(folder.relative_to(root)), "session_created": True}
    output = root / ("evidence/omnigent-completion-regression.json" if args.completion_regression else "evidence/omnigent-enhancement-validation.json" if args.validation else "evidence/omnigent-enhancement.json" if args.enhancement else "evidence/omnigent-research.json" if args.research else "evidence/omnigent-handoff.json")
    if output.exists():
        previous = json.loads(output.read_text())
        history = root / "evidence" / ("research-attempts.jsonl" if args.research else "handoff-attempts.jsonl")
        with history.open("a") as stream:
            stream.write(json.dumps(previous, ensure_ascii=False) + "\n")
        record["previous_parent_session_id"] = previous["parent_session_id"]
        if args.resume_study:
            record["root_session_ids"] = list(dict.fromkeys(previous.get("root_session_ids", [previous["parent_session_id"]]) + [session_id]))
            record["operator_recovery"] = "New orchestrator restores existing broker plan/trial after nested inbox unavailable; no reset"
    output.write_text(json.dumps(record, indent=2))
    prompt = ((root / 'artifacts/enhancement-live/goal.txt').read_text() if args.enhancement else ("这是持久化研究恢复：先status核对现有initial-logs计划和试次。raw已结束三层passed，不重做；structured已有active trial但尚无attempt。请派发新executor角色以继续现有active structured trial（不要start_trial重复创建）；executor将trial_id/config交给新modeler，modeler.task获取原公共模型，不可获得别的trial源码。runtime自动检查独立Codex thread和原生child ID。完成初次配对后，让analyst据真实结果record_analysis调整并派发executor完成followup，到validated停止。全部使用Omnigent真实派发，新角色派发后结束当前轮等自动通知，不轮询、不读历史/发现其他会话。所有旧失败保留，原200次/60分钟总预算与起算不变。不要自行修复模型或编造结果。" if args.resume_study else "按职责约定完成真实科研闭环：规划选择、受限实验、分析调整、后续验证。使用 broker 的当前状态和真实证据，不自行修复模型或编造结果。遇到额度/期限停止并报告已覆盖阶段。")) if is_study else "请按你的约定向 planner 发起一次真实研究规划交接，并返回 child session ID。不要执行实验。"
    if args.completion_regression:
        prompt = "Execute the targeted native-completion engineering regression using the broker accepted Agent-authored plan. Delegate executor for its two baseline-only trials; receive its actual final result through the native inbox after automatic wake. Report run IDs and evaluation, then stop at analysis. No new research plan or follow-up. Preserve expected initialization failures, all errors, and the existing enhancement deadline/request budget. Keep visible output English and brief."
    event = client.post(f"/v1/sessions/{session_id}/events", json={"type":"message", "data":{"role":"user","content":[{"type":"input_text","text":prompt}]}})
    event.raise_for_status()
    record["message_submitted"] = True
    output.write_text(json.dumps(record, indent=2))
    print(json.dumps(record, indent=2))
