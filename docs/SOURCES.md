# 公开来源与原创材料

2026-10-04 核对：

- 本项目 `Challenge.pdf` 全四页：Omnigent 实时多 Agent、至少两个候选实验、结果更新决策、瓶颈实测和两分钟演示要求。PDF 未列明实际截止日期，未确认复用/再分发许可；不据此推导提交授权。
- [Omnigent 官方仓库](https://github.com/omnigent-ai/omnigent)：赛事 PDF 指向的项目。安装版本 0.16.0；实现以安装包解析器和工具加载器为准，仓库当前文档可能与版本不同。Omnigent 默认启动可能发现环境和 CLI 凭据，所以项目使用干净环境，不直接沿用启动默认。
- [Agent image 规范](https://github.com/omnigent-ai/omnigent/blob/main/omnigent/spec/AGENTSPEC.md)：目录、子 Agent 和工具结构；本地实测以 `evidence/agent-spec-check.json` 为证。
- [OpenModelica Docker](https://openmodelica.org/download/docker/)：命令行镜像方案；本项目使用用户已有 1.26.1，未采用文档中挂载主目录的示例。
- [simulate 接口](https://build.openmodelica.org/Documentation/OpenModelica.Scripting.simulate.html)：编译与仿真、CSV 和运行参数；本项目具体执行证据保留在原始日志中。
- [HeatCapacitor](https://build.openmodelica.org/Documentation/Modelica.Thermal.HeatTransfer.Components.HeatCapacitor.html) 与 [ThermalConductor](https://build.openmodelica.org/Documentation/Modelica.Thermal.HeatTransfer.Components.ThermalConductor.html)：常热容/热导的集中参数热模型背景。项目样例为新建方程，不复制 MSL 源码，不需要安装 MSL。

可信工程评价推导：无热源、均匀温度、常热容与热导、恒温环境条件下，能量平衡得到指数趋近轨迹。参数情景和容差属于固定验收实现，只保存在可信侧；Agent 只接收公开物理任务。此理想化模型不等于真实设备验证。

新建任务由本项目独立编写，任务元数据标 CC0-1.0；代码许可尚需用户确认后再对外发布。第三方依赖的各自许可保留在安装元数据；发布前核对汇总。没有访问其他私有项目。

