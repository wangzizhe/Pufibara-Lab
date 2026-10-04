# Pufibara Lab

<h3 align="center"><strong>Live Demo</strong></h3>

<p align="center">
  <a href="https://wangzizhe.github.io/Pufibara-Lab/">https://wangzizhe.github.io/Pufibara-Lab</a>
</p>

<p align="center"><em>Interactive replay of a real saved run; no live model calls.</em></p>

## Overview

**An automatic research environment for studying how Harness mechanisms affect AI agents building physical models.** A Harness provides an agent's context, tools, feedback and execution rules. Our question: which mechanisms improve modeling success, completion time or token use?

## The research loop

![Architecture illustration: evidence-driven research loop](docs/assets/research-loop.svg)

Omnigent coordinates a **Planner, Executor, isolated Modelers and Analyst** through hypothesis → experiment → analysis → adjustment → follow-up validation. Agents decide what to investigate; a trusted broker runs OpenModelica and applies fixed **model checking, simulation and behavior** criteria. [Actual Agent handoffs](evidence/omnigent-demo.json).

## What we demonstrated

**Agent-generated hypothesis:** structured diagnostics improve repair acceptance within two attempts. The initial raw/structured pair tied; the Analyst chose and executed a fresh pair to verify that finding. The completed study contains **four trials and twelve deterministic runs**, including failed baselines and final validations. [Plans, controls and results](evidence/sessions/session-789344082fe64fabadcdb06e415d8d0d/session.json).

| Observed outcome | Raw | Structured |
| --- | ---: | ---: |
| Final accepted trials | 2/2 | 2/2 |
| Development attempts per trial | 2 | 2 |
| Initial-pair tool seconds | 12.208 | 10.258 |
| Follow-up tool seconds | 9.750 | 11.672 |

**No acceptance advantage was observed; tool-time ordering reversed.** Two pairs on one task do not establish general efficacy or equivalence. Tool seconds exclude model/workflow overhead; seed and temperature were unavailable controls.

The latest run took **766 seconds from goal to summary**, excluding setup. **Overall speedup and token savings remain unproven:** the historical manual/automatic observations were confounded. [Bottleneck measurements and limitations](docs/MEASUREMENT.md).

## Verify the evidence

- **Research decisions and follow-up:** [completed session](evidence/sessions/session-789344082fe64fabadcdb06e415d8d0d/session.json).
- **Real orchestration:** [native role tree](evidence/omnigent-demo.json) and [parent messages/tool calls](evidence/omnigent/e33643e43bc04dba8cd0fd538bbe4dde/e33643e43bc04dba8cd0fd538bbe4dde-items.json).
- **Actual execution:** [compiler log](evidence/runs/run-fef27c31a32143f6923faa8836a69dca/raw.log), [simulation trajectory](evidence/runs/run-fef27c31a32143f6923faa8836a69dca/cooling_res.csv) and [fixed evaluation](evidence/runs/run-fef27c31a32143f6923faa8836a69dca/result.json).

[Full submission map](SUBMISSION.md) · [Evidence navigation](evidence/README.md) · [Public citations](docs/SOURCES.md) · [Historical English-edition provenance](docs/ENGLISH_EDITION.md).

## Run it and continue

[Local setup](docs/LOCAL_SETUP.md) · [Research execution](docs/RESEARCH_RUN.md) · [Agent specifications](agents/lab/AGENTS.md) · [Policies and human approval gates](docs/SECURITY.md).

New live runs require dedicated model access and authorized budgets; archived execution authority is disabled. An [offline walkthrough](docs/research-walkthrough.html) is available to download and open locally.

**Next experiment (proposed):** a matched manual-trigger versus automatic-workflow benchmark, including waits, failures, operator work and reliable token accounting. [Protocol](docs/MEASUREMENT.md). Before real-world use, broader tasks, repetitions, physical validation and qualified engineering review are still needed.

## License

Project code and documentation are [MIT licensed](LICENSE). Tasks marked CC0-1.0 and third-party dependencies retain their respective licenses.
