# Sources and physical assumptions

Public sources explain the tools and model background. Specific execution claims are supported by [local run evidence](../evidence/README.md).

| Source | Use in this project |
| --- | --- |
| [Omnigent repository](https://github.com/omnigent-ai/omnigent) and [Agent image specification](https://github.com/omnigent-ai/omnigent/blob/main/omnigent/spec/AGENTSPEC.md) | Orchestration and role-package background. Installed version: 0.16.0; actual package/tool checks are recorded [here](../evidence/agent-spec-check.json). Current upstream documentation may differ. |
| [OpenModelica Docker](https://openmodelica.org/download/docker/) | Container background. Actual execution uses the configured local 1.26.1 image; its identifier is saved in run results. |
| [OpenModelica simulate interface](https://build.openmodelica.org/Documentation/OpenModelica.Scripting.simulate.html) | Compiler/simulator interface and output parameters. Actual logs and CSVs are retained per run. |
| [HeatCapacitor](https://build.openmodelica.org/Documentation/Modelica.Thermal.HeatTransfer.Components.HeatCapacitor.html) and [ThermalConductor](https://build.openmodelica.org/Documentation/Modelica.Thermal.HeatTransfer.Components.ThermalConductor.html) | Background for the constant-capacity/conductance lumped thermal model. Project equations were newly authored; no Modelica Standard Library source is copied. |

## Assumptions and validation scope

The cooling example assumes uniform body temperature, constant thermal capacity/conductance, constant ambient temperature and no internal heat source. Energy balance under these assumptions yields an exponential approach to ambient temperature. The fixed evaluator checks that idealized behavior using trusted scenarios and tolerances; those answers are not exposed to Modelers.

This is not measured-device validation. Independent tasks, physical data, numerical robustness and engineering review remain necessary before real-world use.

## Materials and licensing

Tasks were newly authored and their metadata declares CC0-1.0. No repository-wide code license has been selected; public visibility does not itself grant an open-source license. Third-party dependencies retain their own licenses.

The author-provided four-page Challenge PDF informed the requirements map. It is omitted because redistribution permission was not established; the repository does not claim to reproduce the full official rules or deadline. No private GateForge/Pufibara assets were used.
