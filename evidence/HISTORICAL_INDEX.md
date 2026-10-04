# 本地证据索引

日期：2026-10-04。工程夹具与真实 Agent 运行分别标注；真实来源须有原生建模会话审计，不因存在计划就计为 Agent 实验。未建立科研提速证据。

| 来源 | Run ID | 工具状态 | 检查 | 仿真 | 行为 | 秒 |
| --- | --- | --- | --- | --- | --- | --- |
| Agent | [run-05cf3e79d9f3426b9f45535ddd2f5bfc](runs/run-05cf3e79d9f3426b9f45535ddd2f5bfc/result.json) | completed | passed | passed | passed | 5.765 |
| Agent | [run-08c3de744b8545dab7ff5bd96c400ac0](runs/run-08c3de744b8545dab7ff5bd96c400ac0/result.json) | completed | passed | passed | passed | 2.801 |
| 工程 | [run-2a177c8720d64385aa4fe78b8fa8e236](runs/run-2a177c8720d64385aa4fe78b8fa8e236/result.json) | completed | passed | passed | passed | 6.716 |
| Agent | [run-2ee73bcb64764d738e07364e6edb213a](runs/run-2ee73bcb64764d738e07364e6edb213a/result.json) | completed | passed | passed | passed | 5.188 |
| 工程 | [run-321fe9c36fee4b20808c6e2fac5d2d44](runs/run-321fe9c36fee4b20808c6e2fac5d2d44/result.json) | completed | passed | passed | failed | 4.728 |
| Agent | [run-333565a46cd245a8939dfe98b765a0d9](runs/run-333565a46cd245a8939dfe98b765a0d9/result.json) | completed | passed | passed | passed | 2.677 |
| Agent | [run-34781cb833e64ceca39201ef9c5f5d77](runs/run-34781cb833e64ceca39201ef9c5f5d77/result.json) | completed | passed | passed | passed | 3.675 |
| Agent | [run-415aca30d3504ebb9ae8ab7c7b35e29d](runs/run-415aca30d3504ebb9ae8ab7c7b35e29d/result.json) | completed | passed | passed | passed | 4.661 |
| Agent | [run-42d3ebbc005f4e70b26bcb51de073cb0](runs/run-42d3ebbc005f4e70b26bcb51de073cb0/result.json) | completed | passed | passed | passed | 5.314 |
| Agent | [run-4bb6d695fddc4ad2aa1a59f8c682ba6d](runs/run-4bb6d695fddc4ad2aa1a59f8c682ba6d/result.json) | completed | passed | passed | passed | 3.096 |
| 工程 | [run-4cac03e51b674c73bd5f2b7d45693aeb](runs/run-4cac03e51b674c73bd5f2b7d45693aeb/result.json) | completed | failed | not_run | not_run | 0.258 |
| Agent | [run-531d0e53cc804e278f95733118c72950](runs/run-531d0e53cc804e278f95733118c72950/result.json) | completed | passed | passed | passed | 4.730 |
| Agent | [run-601bfbe255a44421a446d7f5644a26fb](runs/run-601bfbe255a44421a446d7f5644a26fb/result.json) | completed | passed | passed | passed | 5.074 |
| Agent | [run-71558ae35ec046a2b20f66d4e463cd19](runs/run-71558ae35ec046a2b20f66d4e463cd19/result.json) | completed | passed | passed | passed | 4.861 |
| 工程 | [run-a63ba848e0514af58b6e16f532074797](runs/run-a63ba848e0514af58b6e16f532074797/result.json) | completed | passed | passed | passed | 4.848 |
| Agent | [run-ada46c10bd8c4ed083a9ab4fa2c2c4d3](runs/run-ada46c10bd8c4ed083a9ab4fa2c2c4d3/result.json) | completed | passed | passed | passed | 5.066 |
| 工程 | [run-ae0e62135a054eadb3371ea4f102a8c7](runs/run-ae0e62135a054eadb3371ea4f102a8c7/result.json) | completed | passed | failed | not_run | 5.597 |
| Agent | [run-ba0c4282ae8544d9b388a9a243179275](runs/run-ba0c4282ae8544d9b388a9a243179275/result.json) | completed | passed | passed | passed | 4.360 |
| Agent | [run-d5e33d4ed40248199b67931e1035fbb9](runs/run-d5e33d4ed40248199b67931e1035fbb9/result.json) | completed | passed | passed | passed | 4.374 |
| Agent | [run-d808782963964417a95fab56db187ccb](runs/run-d808782963964417a95fab56db187ccb/result.json) | completed | passed | passed | passed | 5.278 |
| Agent | [run-e3fdef192fb0486b93a054ba325e0b7a](runs/run-e3fdef192fb0486b93a054ba325e0b7a/result.json) | completed | passed | passed | failed | 4.613 |
| Agent | [run-f2021aaae52a41879f0a9c3aa878f7b3](runs/run-f2021aaae52a41879f0a9c3aa878f7b3/result.json) | completed | passed | passed | passed | 4.518 |
| 工程 | [run-fc08fd7309fd4664b67fdcc393574a1f](runs/run-fc08fd7309fd4664b67fdcc393574a1f/result.json) | completed | failed | not_run | not_run | 0.173 |

错误模型行为失败、可信修正夹具成功、语法错误下游未执行均已保存。最早一次仿真因工作区 noexec 失败，未删除。

- [Modelica 容器隔离](isolation.json)
- [研究进程合成标记隔离](agent-isolation.json)
- [Omnigent 角色与工具解析](agent-spec-check.json)
- [Omnigent 原生工具到 broker 往返](tool-roundtrip.json)

实际模型请求以 index.json 阶段计数为准，包含失败与重试。订阅没有逐 token 美元账单，费用留空；工具结果中的 token/cost 缺测不能解释为真实 Agent 零开销。

历史工程运行尚无完整实现哈希；当前实现和全部原始结果另见 manifest.json。后续运行将记录评价器/runner/诊断哈希。

已核对闭环报告：
- [evidence/sessions/session-378f6c2e28144a238a1e63638457cb02/report.json](../evidence/sessions/session-378f6c2e28144a238a1e63638457cb02/report.json)
- [evidence/sessions/session-adba2f1eb4944d29a2b5a996284c772d/report.json](../evidence/sessions/session-adba2f1eb4944d29a2b5a996284c772d/report.json)

真人流程测量：已保存真实观察，包含混淆因素，不计算提速倍率。
