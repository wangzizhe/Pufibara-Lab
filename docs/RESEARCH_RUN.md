# 科研运行与复现说明

## 初始化案例入口

新案例是 `cooling-init-v1`，真实初始化错误需在修正前执行一次原始基线；基线计入尝试上限。这控制日志暴露顺序，不证明源码推理无法修复。固定三层评价不变。分析角色用 `trial_evidence` 读取实际尝试次数、开发日志和信息遗漏；隐藏行为答案仍不可查询。

启动前在项目 `.venv` 应用版本限定的原生通知补丁，并做无模型检查：

```sh
.venv/bin/python scripts/patch_omnigent_completion.py
.venv/bin/python scripts/check_omnigent_completion.py
.venv/bin/python scripts/probe_codex_worker.py
PYTHONPATH=src .venv/bin/python scripts/check_initialization_case.py
```

补丁只修改项目内 Omnigent 0.16.0 的完成条件：有未完成子任务时不能通知父任务完成；保留原生派发、收件箱和唤醒。脚本拒绝其他版本、异常源码或全局安装目录，幂等执行。重新安装 Omnigent 后需重新应用。实际 runner 回调探针使用合成任务，不替代真实科研闭环验证。新角色代码修改后，先等所有角色空闲再安装、重启 host；host 关闭预加载，避免旧代码继承。

新环境必须使用自己的专用登录和明确的新请求／时间预算。提交副本中所有模型授权默认关闭；历史额度和同意不适用于复现。请求失败和重试均计入预算，首次调用起算，跨进程或重启不重置；不自动购买额度或转付费 API。下面仅给出已有实现的启动入口，不授予执行权限。

```sh
.venv/bin/python scripts/prepare_live_demo.py --enhancement
.venv/bin/python -m physicslab.cli --root "$PWD" --runtime enhancement broker
.venv/bin/python scripts/research_host.py --phase enhancement
.venv/bin/python scripts/start_handoff.py --enhancement --host-id YOUR_PROJECT_HOST_ID
.venv/bin/python scripts/collect_omnigent_evidence.py --enhancement
```

以上分别在本机终端启动；先准备专用 Omnigent server。使用本机服务报告的项目 host ID，不能复用别人的主机标识。准备脚本拒绝覆盖旧包，启动脚本拒绝覆盖已有会话；恢复当前研究需保留 broker、父会话、日志和预算，不能删除记录重跑。保存所有实际角色消息、源码、日志、固定评价和失败，不将历史结果写成新运行结果。

## 提交中的实际运行

主要证据是 `evidence/sessions/session-789344082fe64fabadcdb06e415d8d0d/session.json` 和 `evidence/omnigent-demo.json`：最新用户演示完成两组匹配对照及结果驱动的后续验证。上面的 enhancement 入口复现同类初始化案例，不承诺逐消息或逐结果一致。

历史初始研究、人工流程和工程恢复记录用于可追溯性，不代表当前正在运行。模型随机性及未暴露的 seed/temperature 控制限制精确重现；固定评价不因复现结果变化而调整。跨试次必须使用新的建模会话，禁止提供其他组源码、隐藏评价或测试答案。真实费用未知时保留未知，不将订阅写成免费无限调用。
