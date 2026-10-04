# 实际科研运行报告

Broker 会话：`session-378f6c2e28144a238a1e63638457cb02`。Omnigent 父会话：`f975c1d27d8e41ca8ecb8e88e4c71dcb`。

当前阶段：**validated**；完整闭环核对：**True**；建模会话分离：**True**。

## Agent 提出与选择

### initial-logs

假设（待验证）：在固定 cooling-sign-v1 任务、模型、温度、工具、修复预算及既定检查/仿真/行为评价的条件下，structured 日志比 raw 日志更有助于定位并修复冷却符号错误，表现为在相同尝试上限内通过既定最终验证，且所需修复尝试更少；这是待检验假设。

证伪条件：初始 matched 对照中，structured 的既定最终验证结果差于 raw，或两者验证结果相同而 structured 所需修复尝试不少于 raw，均计为本次对照不支持该假设；单次配对不用于断言普遍效应。

| 候选 | 学习价值 | 可行性 | 预计工具运行 |
| --- | --- | --- | --- |
| logs | 直接比较 raw 与 structured 日志机制对既定任务修复及最终验证的影响；所有其他条件匹配。 | 固定 cooling-sign-v1，raw/structured 各一次，replicate=0、max_attempts=2；每个 trial 按 max_attempts+1 计3次确定性工具运行，初始共6次，保留6次后续预算。 | 6 |
| information-loss | 比较等信息量的 raw 与 structured 表达，以区分日志组织效果与信息遗漏的影响；仅为后续候选，不改评价标准。 | 需要确认两种日志的信息等价性；可在剩余6次预算内安排另一组同任务、同条件、max_attempts=2的 matched 对照，本轮不执行也不承诺启动。 | 6 |

选择：logs。直接检验日志机制，且符合用户指定的初始 matched raw/structured 对照。初始预算6次，后续保留6次，总计不超过12次确定性工具运行。沿用本阶段200模型请求/60分钟总上限及原起算时间，所有角色推理和失败重试均计入；当前公开状态已使用154/200请求，截止时间1791107297.777293。不更改任务、模型、温度、工具、修复预算或既定检查/仿真/行为评价；本轮只记录计划，不执行实验或派发子角色。

### matched-logs-replicate-1

假设（待验证）：固定 cooling-sign-v1、原基础模型、温度、工具、max_attempts=2 和原评价，structured 相较 raw 能在最终三项评价均通过的条件下减少实际修复尝试；该收益仍待检验。

证伪条件：新增配对中 structured 最终评价差于 raw，或最终评价相同且 structured 实际修复尝试不少于 raw，则该配对不支持假设；若实际尝试数仍未记录，则减少尝试的假设保持不可判定。新增一对不能证明普遍机制收益。

| 候选 | 学习价值 | 可行性 | 预计工具运行 |
| --- | --- | --- | --- |
| matched-repeat | 增加同条件 raw/structured 配对，检验最终评价稳定性；若补齐实际尝试数，可直接判断原假设。保留原始诊断用于审计信息损失，不改变输入或评价。 | 两 trial，各 max_attempts=2，按每 trial最多3次工具运行计，共6次；加初始6次不超过12。仅在原请求和时间预算仍允许时另行执行，本轮不执行。 | 6 |
| structured-only-repeat | 检验 structured 最终通过能否复现，但缺少同期 raw 对照，对机制比较的解释力较低。 | 一个 structured trial、replicate=1、max_attempts=2，最多3次工具运行；加初始6次为9次。 | 3 |

选择：matched-repeat。两现有 final runs 的最终评价持平，需要保留同期匹配对照来解释新增结果。配对重复比单独 structured 重复更直接服务原假设，最多消耗剩余6次工具额度；成本为工具次数上限，实际token和货币成本未知。继承同任务、基础模型及全部原评价与修复条件，不派发、不执行，不重置200请求/60分钟总上限或原起算时间。

## 实际实验

| 计划 | 机制 | 修复次数 | 检查 | 仿真 | 行为 | 工具秒 | 证据 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| initial-logs | raw | 1 | passed | passed | passed | 9.936 | [run-601bfbe255a44421a446d7f5644a26fb](../../runs/run-601bfbe255a44421a446d7f5644a26fb/result.json) |
| initial-logs | structured | 1 | passed | passed | passed | 7.319 | [run-f2021aaae52a41879f0a9c3aa878f7b3](../../runs/run-f2021aaae52a41879f0a9c3aa878f7b3/result.json) |
| matched-logs-replicate-1 | raw | 1 | passed | passed | passed | 10.465 | [run-2ee73bcb64764d738e07364e6edb213a](../../runs/run-2ee73bcb64764d738e07364e6edb213a/result.json) |
| matched-logs-replicate-1 | structured | 1 | passed | passed | passed | 8.050 | [run-d5e33d4ed40248199b67931e1035fbb9](../../runs/run-d5e33d4ed40248199b67931e1035fbb9/result.json) |

## 结果驱动的调整

支持程度：inconclusive

调整理由：run-601bfbe255a44421a446d7f5644a26fb 与 run-f2021aaae52a41879f0a9c3aa878f7b3 在既定三项最终评价上均通过，未显示最终成功率优势；又缺少实际尝试数，因此当前假设支持程度为 inconclusive。下一步从宣称机制收益转为补充一个匹配重复，检验结果稳定性，并要求保留实际尝试数及诊断内容以判断原假设；本轮只记录，不启动验证。

限制：raw 最终 run-601bfbe255a44421a446d7f5644a26fb 与 structured 最终 run-f2021aaae52a41879f0a9c3aa878f7b3 的 model_checking、simulation、behavior 均分别 passed。status 未提供独立 compiler 字段，编译结果不能单独认定通过；任何 not_run 均不算通过。每种条件只有一个 trial，且没有实际修复尝试次数，不能判定 structured 是否减少尝试，也不能从两者最终均通过推断机制收益。两 run 的 tool_seconds 分别为9.935757166007534和7.319038040994201，仅为工具时间，缺少端到端工作流耗时、token、实际货币成本及各角色推理/失败重试分项；不能据此宣称研究提速或10倍收益。status 未展示诊断内容及保留字段，无法排除 structured 丢失诊断信息或两条件信息不等价。按已接受初始预算6次、剩余6次保守计费，总工具额度12；status 未列出逐次工具账本。沿用本阶段200请求/60分钟及原起算时间，不重置；当前status为177/200，deadline_unix=1791108497.777293，与初始计划文字中的1791107297.777293存在差异，记录此差异，不自行延长或重算截止时间。

引用：run-601bfbe255a44421a446d7f5644a26fb, run-f2021aaae52a41879f0a9c3aa878f7b3

## 用量与限制

模型实际请求由阶段网关计数，包含基础设施失败和重试。研究与建模 token 仅在能对应真实会话时分列；早期匿名键不强行归因，属于全局历史缺测，不能算成本次研究的全部未知成本。订阅没有逐 token 美元账单，费用留空。

科研流程瓶颈实测：真人手工 814.0 秒、6 次界面动作；自动路径 2293.8 秒、10 次已记录原生控制输入。自动路径的终端/修改总动作未完整记录，操作员与基础设施成熟度不同；不计算提速倍率。

- Small acceptance example cannot establish mechanism efficacy
- No measured research speed improvement yet
- No human timing inferred from Codex operation
- Codex CLI does not expose matched temperature/seed control; same configured base model and reasoning route
- Early runtime usage keys were not native conversation IDs; those role costs remain unknown

原始消息：`evidence/omnigent/f975c1d27d8e41ca8ecb8e88e4c71dcb`；原始计划、源代码、日志和模型产物保留于本项目证据目录。
