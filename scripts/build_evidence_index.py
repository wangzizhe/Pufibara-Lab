"""Summarize saved runs without reclassifying engineering work as science."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
runs = [json.loads(p.read_text()) for p in sorted((root / "evidence/runs").glob("*/result.json"))]
native_file = root / "evidence/omnigent-research.json"
native = json.loads(native_file.read_text()) if native_file.exists() else {}
live_run_ids = set()
native_session_ids = {s['id'] for s in native.get('sessions', [])}
manual_native_file = root / 'evidence/omnigent-manual.json'
if manual_native_file.exists():
    manual_native = json.loads(manual_native_file.read_text())
    native_session_ids.update(s['id'] for s in manual_native.get('sessions', []))
conversation_file = root / 'evidence/modeler-conversations.jsonl'
audited_trials = {r['trial_id'] for r in
    (json.loads(line) for line in conversation_file.read_text().splitlines())
    if r.get('session_id') in native_session_ids} if conversation_file.exists() else set()
verified_reports = []
for session_file in (root / "evidence/sessions").glob("*/session.json"):
    session = json.loads(session_file.read_text())
    if session.get("kind") == "live_pending" and session.get("plans"):
        for trial in session["trials"]:
            if trial['trial_id'] not in audited_trials:
                continue
            live_run_ids.update(trial["attempts"])
            if trial.get("final_run_id"):
                live_run_ids.add(trial["final_run_id"])
    report_file = session_file.with_name('report.json')
    if session.get('stage') == 'validated' and report_file.exists():
        report = json.loads(report_file.read_text())
        if report.get('closed_loop_verified'):
            verified_reports.append(str(report_file.relative_to(root)))
comparison_file = root / 'evidence/measurements/workflow-comparison.json'
comparison = json.loads(comparison_file.read_text()) if comparison_file.exists() else {}
human_measured = bool(comparison.get('manual', {}).get('finished')) if comparison.get('manual') else False
phase_usage = {}
for phase in ("pilot", "research"):
    journal = root / f".runtime/{phase}-requests.jsonl"
    if journal.exists():
        rows = [json.loads(line) for line in journal.read_text().splitlines()]
        effective = next((r for r in reversed(rows) if r.get("event") == "budget_amended"), rows[0])
        phase_usage[phase] = {"requests":max((r.get("reserved_requests",0) for r in rows),default=0),
            "limit":effective["max_requests"], "deadline_unix":effective["deadline_unix"]}
record = {"status": "closed_loop_verified_measurement_pending" if verified_reports and not human_measured else
                    "closed_loop_and_workflow_observations_saved" if verified_reports and human_measured else
                    "live_research_in_progress" if native else "local_engineering_only",
          "live_omnigent_agents_run": bool(native.get("native_dispatch_observed")),
          "model_calls": sum(u["requests"] for u in phase_usage.values()),
          "phase_usage":phase_usage, "incremental_model_service_cost_usd":None,
          "billing":"existing_subscription_no_credit_purchase_no_api_fallback",
          "scientific_bottleneck_measurement": "actual_pair_with_confounds_no_speed_claim" if human_measured else "human_measurement_pending",
          "verified_closed_loop_reports": verified_reports,
          "live_origin_rule": "Broker trial plus actual native-session/modeler-thread audit; plan alone is insufficient",
          "runs": [dict({k: r.get(k) for k in ("run_id", "status", "source_sha256", "image", "seconds", "evaluation")},
                        origin="live_agent" if r["run_id"] in live_run_ids else "engineering") for r in runs],
          "limitations": ["Engineering fixtures are not agent experiments", "No mechanism-effect or research-speed claim", "Full closed-loop status must be checked in the selected broker report"]}
(root / "evidence/index.json").write_text(json.dumps(record, indent=2))
lines = ["# 本地证据索引", "", "日期：2026-10-04。工程夹具与真实 Agent 运行分别标注；真实来源须有原生建模会话审计，不因存在计划就计为 Agent 实验。未建立科研提速证据。", "",
         "| 来源 | Run ID | 工具状态 | 检查 | 仿真 | 行为 | 秒 |", "| --- | --- | --- | --- | --- | --- | --- |"]
for r in runs:
    e = r["evaluation"]
    lines.append(f'| {"Agent" if r["run_id"] in live_run_ids else "工程"} | [{r["run_id"]}](runs/{r["run_id"]}/result.json) | {r["status"]} | {e["model_checking"]} | {e["simulation"]} | {e["behavior"]["status"]} | {r["seconds"]:.3f} |')
lines += ["", "错误模型行为失败、可信修正夹具成功、语法错误下游未执行均已保存。最早一次仿真因工作区 noexec 失败，未删除。", "",
          "- [Modelica 容器隔离](isolation.json)", "- [研究进程合成标记隔离](agent-isolation.json)", "- [Omnigent 角色与工具解析](agent-spec-check.json)", "- [Omnigent 原生工具到 broker 往返](tool-roundtrip.json)", "",
          "实际模型请求以 index.json 阶段计数为准，包含失败与重试。订阅没有逐 token 美元账单，费用留空；工具结果中的 token/cost 缺测不能解释为真实 Agent 零开销。", "",
          "历史工程运行尚无完整实现哈希；当前实现和全部原始结果另见 manifest.json。后续运行将记录评价器/runner/诊断哈希。"]
lines += ['', '已核对闭环报告：'] + [f'- [{path}](../{path})' for path in verified_reports]
lines += ['', '真人流程测量：'+('已保存真实观察，包含混淆因素，不计算提速倍率。' if human_measured else '尚待完成，自动路径观察不能替代真人计时。')]
(root / "evidence/README.md").write_text("\n".join(lines) + "\n")
paths = []
for directory in ("src", "scripts", "agents", "tasks", "configs", "docs", "tests", "evidence"):
    paths += [p for p in (root / directory).rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.name != "manifest.json"]
paths += [root / f for f in ("pyproject.toml", "requirements.lock", "README.md")]
manifest = {"kind": "current_local_snapshot_not_historical_run_version", "sha256": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
(root / "evidence/manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
print(json.dumps({"saved_runs": len(runs), "status": record["status"]}))
