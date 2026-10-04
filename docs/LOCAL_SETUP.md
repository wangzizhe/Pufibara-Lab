# 本地使用说明

日期：2026-10-04。无需先配置模型即可进行工程验收。真实研究入口见 [RESEARCH_RUN.md](RESEARCH_RUN.md)，使用本项目专用登录与显式阶段预算。

## 当前环境

- Python 3.14.8；Omnigent 0.16.0 在本项目 `.venv`，依赖固定于 `requirements.lock`。
- 用户已有 OpenModelica 1.26.1 arm64 镜像，内容 ID 固定在 `configs/runtime.json`。
- 只用本项目新建材料；没有读取或复用其他私有项目。
- Docker 使用本项目空配置目录；不挂载主目录、Docker socket 或评价器。`--pull=never` 避免意外拉取。

## 无模型检查

在仓库根运行：

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/check_agents.py
PYTHONPATH=src .venv/bin/python -m physicslab.cli probe
PYTHONPATH=src .venv/bin/python -m physicslab.cli evaluate tasks/cooling/Cooling.mo --final
PYTHONPATH=src .venv/bin/python scripts/engineering_smoke.py
.venv/bin/python scripts/probe_agent_sandbox.py
.venv/bin/python scripts/check_tool_roundtrip.py
.venv/bin/python scripts/build_evidence_index.py
```

Docker 命令需要本机 Docker 服务访问权限。沙箱 probe 用 macOS `sandbox-exec`，当前仅针对 macOS 验证。正确夹具脚本属于可信工程侧，不能提供给建模 Agent。工具检查有累计额度，耗尽后先审查记录；不要静默重置计数。

如在新环境复现安装，先确认安装授权，再执行：

```sh
python3 -m venv .venv
env -i HOME="$PWD/.runtime/home" PATH="$PWD/.venv/bin:/usr/bin:/bin" \
  .venv/bin/python -m pip --isolated install --no-cache-dir -r requirements.lock
.venv/bin/python -m pip install --no-deps --no-build-isolation .
```

先创建 `.runtime/home`。跨平台可能需要不同平台的锁文件与 Docker 地址；镜像内容 ID 需经可信操作员核对，再更新配置并重新 probe。不会自动下载替代镜像。

## 接入真实 Agent 前

1. 与用户选定模型服务、模型、凭据提供方式和费用/调用/token 上限；离线审阅包默认模型授权为 false、额度为 0；本机配置只代表本次已授权会话。
2. 本项目已接入原生 Codex 出口的共享请求闸门、墙钟期限与实际 token 记录。订阅账单没有逐 token 美元费用，费用未知；不得把请求上限称为任意美元费用封顶。新环境必须重新取得模型授权，不能复用本次配置中的历史同意。
3. 完整启动 Omnigent 时核对框架附加工具、子进程、日志和模型出口。已有真实 worker 启动器的合成文件/网络拒绝、账户控制与实时模型/工具证据；该有限范围不能等同于全系统最小权限证明。
4. 验证每个机制试次使用全新建模会话，未共享历史、先前解或最终答案。
5. 实时运行研究与后续验证，保存完整实际消息、调用、配置、失败、用量和结果，再生成科研报告。

不要直接执行无参数 `omnigent`：官方启动流程可能自动发现已有凭据；本项目不会利用该默认行为。

## 当前 broker

```sh
PYTHONPATH=src .venv/bin/python -m physicslab.cli broker
```

只监听 `127.0.0.1:8765`，能力文件位于忽略目录 `.runtime`，启动后创建新的 session。角色工具访问固定 `/call`，没有任意文件、shell、URL 或评价标准修改接口。broker 是可信宿主侧程序，Agent 不能访问其源代码、数据库和隐藏评价器。

正常结算后可用 `broker --resume session-id` 恢复同一会话，保留计划/结果/累计预算并轮换能力。配置必须与原会话一致；有未结算工作时拒绝恢复，先检查实际进程和产物，不自动重跑或清零。崩溃期间尚未归档到试次的产物仍需可信操作员核对。勿并发启动两个 broker。

模型路线为 Omnigent → 项目 physics-codex 插件 → Codex CLI → 专用订阅登录。新环境需要自己的专用登录与明确授权，不复制主目录或其他项目凭据。订阅调用仍消耗账户额度，不允许自动购买 credits 或回退到付费 API。

社区插件需正常 wheel 安装，不能 editable 安装：运行时允许 `.venv`，可信包所有已安装文件通过真实启动器额外拒读；修改安装后重做 `scripts/probe_codex_worker.py`。工具按文件名注册，每个工具函数一个同名文件，`check_agents.py` 校验声明与加载结果一致。`check_live_capabilities.py` 在 broker 在线时验证原生 runner 传递及角色往返，不调用模型。

`check_tool_roundtrip.py` 是独立工程探针，会更换能力文件并占用 broker 端口。仅在所有科研服务停止后运行；在线科研/手工测量使用 `check_live_capabilities.py`，避免覆盖当前会话能力。材料包默认禁用历史模型授权；不打包 `.runtime`、登录、能力、虚拟环境或第三方题目 PDF。


## 提交副本范围

此副本不含登录、能力、运行目录、虚拟环境、题目 PDF 或演示素材。模型配置中的历史执行授权已禁用。当前副本文件哈希见根目录 PACKAGE_MANIFEST.json。历史验证记录不代表清理后重新执行了实验。

复现初始化案例前应用 `scripts/patch_omnigent_completion.py`，见 RESEARCH_RUN.md。保存科学证据可无模型复核：`.venv/bin/python scripts/verify_enhancement_evidence.py`；它核对历史补齐运行，不替代最新演示原生记录。
