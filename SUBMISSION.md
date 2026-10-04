# Submission review entry — existing results only

Prepared 2026-10-04. No new experiments, model calls, publication or formal submission are implied by this index. Start here; the older handoff history below is retained for provenance.

## What the project demonstrates

An Omnigent-orchestrated research environment for physical-modeling Harness mechanisms: propose a falsifiable hypothesis, compare costed experiments, execute isolated modeling agents, analyze fixed evaluation results, and select and execute a result-driven follow-up. The completed user-started demonstration is the primary evidence, not a replay or the older engineering-recovery session.

## Submission contents

| Required item | Review entry / evidence |
| --- | --- |
| Repository and reproducible environment | [README](README.md), [local setup](docs/LOCAL_SETUP.md), [research run instructions](docs/RESEARCH_RUN.md), src/, scripts/, tasks/, requirements.lock |
| Agent specifications and policies | [Coordinator](agents/lab/AGENTS.md), agents/lab/agents/ (Planner, Executor, Analyst, Modeler), [security and approval gates](docs/SECURITY.md); capabilities and live credentials excluded |
| Two-minute demo | Submitted separately by the author; recording and presentation assets are not included in this repository copy. |
| Cited evidence | [Public sources](docs/SOURCES.md); claim-to-record table below. Internal observations cite actual native messages and deterministic run records, not general documentation. |
| Experiment code and results | [Completed demo session](evidence/sessions/session-789344082fe64fabadcdb06e415d8d0d/session.json), [native role tree](evidence/omnigent-demo.json), evidence/omnigent/e33643e43bc04dba8cd0fd538bbe4dde/; each final run ID resolves to evidence/runs/ with source, raw log and result. |
| Measured improvement and limitations | [Historical workflow measurements](evidence/measurements/workflow-comparison.json), [completion bottleneck observation](evidence/measurements/completion-bottleneck.json), [latest demo observation](evidence/measurements/demo-observation.json). No defensible overall speedup or token reduction has been established. |
| Next experiment | Proposed only: matched manual-trigger versus automatic workflow on the same prepared environment and task; consistent start/end and completion criteria, all failures counted, operator actions and time recorded separately. If authorized later, repeat with alternating order; repair token attribution before claiming token savings. This is not a completed experiment. |

## Claim-to-evidence map

| Label | Claim | Source and boundary |
| --- | --- | --- |
| Agent-generated hypothesis | Structured diagnostics improve final acceptance under the same two-attempt allowance. | Demo session plans[0], including falsification, candidate costs and selected controls. A hypothesis, not a result. |
| Observation | Two matched raw/structured pairs completed; four trials passed fixed model checking, simulation and behavior, each in two development attempts. | Demo session trials and their final_run_id records. All four failed baselines are preserved. Twelve deterministic runs total. |
| Observation | Initial raw/structured tool seconds: 12.208/10.258; follow-up: 9.750/11.672. | Demo session tool_seconds. Tool runtime excludes other model/workflow overhead; ordering reversed. |
| Conditional conclusion | No observed pass-rate or attempt-count advantage on this task; no consistent tool-time advantage. | Native root final message 4986cff11c7546d088fd6430adcb38d9; follow-up selected in plans[1] from initial evidence. Two pairs do not establish equivalence or general efficacy. |
| Observation | One native human goal input; five system completion notifications; goal-to-final-summary timestamp span 766 seconds. | demo-observation.json with message IDs and source hashes. Retrospective span, excludes setup; zero additional native control inputs does not mean zero overall human work. |
| Unresolved | Overall workflow speedup and token savings. | Historical manual 813.986 seconds versus automatic 2293.816 seconds have operator/infrastructure confounds. Latest 766-second run has no matched manual comparator. Do not divide these values to claim a gain. Per-trial token attribution is not validated; missing is not zero. |
| Engineering observation | A targeted post-fix notification regression completed without stage recovery; final Executor-to-parent summary took 22 seconds. | completion-bottleneck.json and completion-regression.json. Narrower task and no matched before/after latency measurement; not a quantified full-workflow acceleration. |

## Controls, approval and deployment limits

Harness feedback format is the variable. Public task, exposed model route, tools, two-attempt allowance and final model-checking/simulation/behavior criteria are held matched; seed and temperature are not exposed controls. Each modeling trial has separate native and Codex conversations. Failed runs remain evidence. Worker isolation probes test specific boundaries, not universal security.

Human gates cover installation, model service, request/time limits, quota extension, and publication/submission. Existing subscription only; no purchase or paid-API fallback. Archived model configs have live authority disabled. Any future experiment needs applicable authorization; packaging does not extend it.

Validation before real-world use remains outstanding: independent physical tasks, broader repetitions, reliable model/token/workflow instrumentation, numerical robustness, calibrated measured physical data and qualified engineering review. The idealized cooling task is not hardware validation.

Suggested truthful demo closing: **“The environment completed a real evidence-driven research loop. In this small study, structured diagnostics showed no pass-rate advantage, and tool-time ordering reversed. Overall speedup and token savings remain unproven; the next experiment is a matched workflow benchmark.”**

Submission readiness: evidence and code can be reviewed now; final user video, public-code licensing choice, deadline/rule check and explicit submission authorization remain human steps. No positive speed claim is manufactured to fill the measured-improvement field.

