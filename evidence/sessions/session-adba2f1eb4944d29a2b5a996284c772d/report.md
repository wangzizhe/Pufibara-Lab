# 实际科研运行报告

Broker 会话：`session-adba2f1eb4944d29a2b5a996284c772d`。Omnigent 父会话：`93cb3317d6fa4eb2b8824034b9ae539a`。

当前阶段：**validated**；完整闭环核对：**True**；建模会话分离：**True**。

## Agent 提出与选择

### initial-logs

假设（待验证）：在任务 cooling-sign-v1 可用且其余执行条件保持一致的条件下，structured 日志比 raw 日志更有助于执行模型在同一修复预算内通过既定最终验证；此假设为暂定假设，尚无试验支持。

证伪条件：匹配试验中 structured 条件未通过既定最终验证而 raw 条件通过，构成反对假设的观察；两者均通过或均失败则本轮不能支持所假设的优势，不据此声称普遍效应。

| 候选 | 学习价值 | 可行性 | 预计工具运行 |
| --- | --- | --- | --- |
| logs | 直接检验日志呈现机制与既定验证结果的关系；采用同任务、同 replicate 的 raw/structured 配对，避免更换评价标准。 | 需要 broker 确认 cooling-sign-v1 是可用真实任务，并由 operator 授权 modeler 访问模型；任务、模型、温度、工具、修复预算及评价必须匹配。两次 trial 各 max_attempts=2，按每 trial max_attempts+1 计费，总计六次确定性工具运行；estimated_tool_runs=4 指最多四次修复尝试，另有两次最终验证。当前 status 未暴露任务清单、模型请求用量或期限，不能声称已核实这些条件。 | 4 |
| information-loss | 在相同任务和评价下以无修复配对检验日志呈现的信息损失是否足以改变最终验证结果；成本低，但不能观察日志对迭代修复的帮助。 | 若 broker 支持 max_attempts=0，可执行 raw/structured 各一次最终验证，总计两次确定性工具运行；仍需同一任务、模型、温度、工具和 operator 模型授权。该零修复配置的支持情况尚未由真实工具确认。 | 2 |

选择：logs。选择直接观察修复过程的日志配对，学习价值高于无修复测试；初始成本为六次确定性工具运行，在初始和后续合计最多十二次的上限内保留六次供后续使用。仅在 broker 接受任务与计划且 operator 确认原模型请求预算和原期限仍允许执行时交给 executor；不重置预算或期限、不变更评价、不自行修复模型或能力。当前唯一真实证据为 session-adba2f1eb4944d29a2b5a996284c772d 的 status：stage=planning、plans=[]、trials=[]、analysis=null；该响应没有独立证据 ID，也没有可见用量和期限。

### followup-logs-replicate1

假设（待验证）：在 cooling-sign-v1、新 replicate=1 且其余条件匹配、max_attempts=2 的条件下，structured 相比 raw 是否出现既定最终验证的通过优势；此为初始优势假设的独立配对复核，现有证据未支持该优势。

证伪条件：structured 任一原评价层未通过而 raw 三层均通过，构成反对优势的观察；两者均通过或均失败仍不能支持优势；structured 三层均通过而 raw 失败只作为单配对的方向性证据，不能推出普遍收益。工具失败、停止、not_run、未知评价须分别报告，不当作通过，不混同为行为失败。

| 候选 | 学习价值 | 可行性 | 预计工具运行 |
| --- | --- | --- | --- |
| matched-replicate1 | 以新 replicate 复核初始两者均通过的无区分观察，维持原任务、max_attempts=2 和三层评价，可与初始结果保持同预算可比。 | raw/structured 各一 trial，各最多两次修复加一次最终验证，配置成本上限共六次确定性工具运行；占用 followup 原预留六次。须由 broker 核实实际剩余额度及原请求/期限允许，固定相同模型、温度、工具、任务起点、评价及执行政策，仅 diagnostics 不同；不得重跑 replicate=0，不修复模型。 | 6 |
| matched-reduced-budget | 使用 replicate=1、raw/structured 各 max_attempts=1，以较紧预算探索初始双通过是否来自预算充足；但改变原修复预算，不能作为原同预算结果的直接复核。 | 两 trial 各最多一次修复加一次最终验证，总成本上限四次确定性工具运行；保留原任务与评价，配对内部其余条件匹配。模型请求/token/cost 未知，不能量化总体费用。 | 4 |

选择：matched-replicate1。初始 run-05cf3e79d9f3426b9f45535ddd2f5bfc 与 run-ba0c4282ae8544d9b388a9a243179275 均通过，首要不确定性是这一结果是否在新样本中重复。选择六次上限的原预算配对，避免四次候选引入修复预算变化；初始计划上限六次加 followup 上限六次为十二次。实际历史消耗当前不可见，不能以预留替代余额证明，交由 broker 核验；若额度不足或 quota 错误则停止，不派发或重试。原200请求、60分钟及起算保持不变。

## 实际实验

| 计划 | 机制 | 修复次数 | 检查 | 仿真 | 行为 | 工具秒 | 证据 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| initial-logs | raw | 2 | passed | passed | passed | 13.055 | [run-05cf3e79d9f3426b9f45535ddd2f5bfc](../../runs/run-05cf3e79d9f3426b9f45535ddd2f5bfc/result.json) |
| initial-logs | structured | 1 | passed | passed | passed | 9.090 | [run-ba0c4282ae8544d9b388a9a243179275](../../runs/run-ba0c4282ae8544d9b388a9a243179275/result.json) |
| followup-logs-replicate1 | raw | 1 | passed | passed | passed | 9.727 | [run-ada46c10bd8c4ed083a9ab4fa2c2c4d3](../../runs/run-ada46c10bd8c4ed083a9ab4fa2c2c4d3/result.json) |
| followup-logs-replicate1 | structured | 1 | passed | passed | passed | 8.410 | [run-42d3ebbc005f4e70b26bcb51de073cb0](../../runs/run-42d3ebbc005f4e70b26bcb51de073cb0/result.json) |

## 结果驱动的调整

支持程度：not_supported

调整理由：run-05cf3e79d9f3426b9f45535ddd2f5bfc 与 run-ba0c4282ae8544d9b388a9a243179275 三层评价均通过，使原优势假设本轮不获支持。保持原任务、修复预算和评价，改用新 replicate 的匹配配对，检验这一无区分结果在另一个执行样本中是否重复；不基于小样本 tool_seconds 选择机制或宣称速度收益。

限制：status 中 raw 的 final_run_id=run-05cf3e79d9f3426b9f45535ddd2f5bfc 与 structured 的 final_run_id=run-ba0c4282ae8544d9b388a9a243179275 的 model_checking、simulation、behavior 分别均为 passed；没有将 not_run 计为 passed。仅一个任务的一组配对，按 initial-logs 预先 falsification，两者均通过不能支持 structured 的同预算通过优势，也不足以证明无效或普遍机制。上述两 run 的 tool_seconds 分别为 13.054623665986583 和 9.089917165983934；单组确定性工具时间差不是模型端到端耗时、工作流速度、机制收益或现实应用收益。当前可调用 packaged 工具只有 status/record_analysis，没有逐 run 评价及资源读取接口；无法检查未出现在 status trials 中的旧停止、工具失败、未知 usage 或其他完成试次，不能断言它们不存在。token、成本、实际确定性工具已用/剩余次数、尝试轨迹以及 raw/structured 诊断保留与丢失字段未知，无法评价诊断信息损失。status model_budget 显示 used_requests=116、max_requests=200、deadline_unix=1791107297.777293，但后续调用仍消耗原预算；不重置原200请求/60分钟或原起算。followup 的六次为按 max_attempts+1 计算的配置上限，不是已核实余额；实际额度须由 broker 的资源账本校验，quota 错误立即停止，不能自行忽略或重试。

引用：run-05cf3e79d9f3426b9f45535ddd2f5bfc, run-ba0c4282ae8544d9b388a9a243179275

## 用量与限制

模型实际请求由阶段网关计数，包含基础设施失败和重试。研究与建模 token 仅在能对应真实会话时分列；早期匿名键不强行归因，属于全局历史缺测，不能算成本次研究的全部未知成本。订阅没有逐 token 美元账单，费用留空。

科研流程瓶颈实测：真人手工 814.0 秒、6 次界面动作；自动路径 2293.8 秒、10 次已记录原生控制输入。自动路径的终端/修改总动作未完整记录，操作员与基础设施成熟度不同；不计算提速倍率。

- Small acceptance example cannot establish mechanism efficacy
- No measured research speed improvement yet
- No human timing inferred from Codex operation
- Codex CLI does not expose matched temperature/seed control; same configured base model and reasoning route
- Early runtime usage keys were not native conversation IDs; those role costs remain unknown

原始消息：`evidence/omnigent/93cb3317d6fa4eb2b8824034b9ae539a`；原始计划、源代码、日志和模型产物保留于本项目证据目录。
