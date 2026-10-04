# Historical report: Initialization diagnostic-fidelity study

Broker session: `session-d32b3336026842fcba860f2d22b06ec6`. Stage recorded: **validated**. This is an English editorial summary of preserved evidence, not a new Agent analysis or experiment. The latest demonstration is linked from the repository README.

## Research decision and result

Initial raw/structured repair trials tied: both passed after an unchanged baseline and one correction. The Analyst rejected the proposed structured acceptance advantage and selected a different, baseline-only diagnostic-fidelity audit. Both follow-up trials passed model checking, failed initialization and had behavior not_run, as expected for unchanged baselines. The final Analyst found structured output retained 5 of 29 baseline log lines, omitting 24, while preserving the initialization error and omitting explicit successful model-check evidence and a logging hint. This supports only a narrow information-preservation observation.

| Plan | Feedback | Development attempts | Checking | Simulation | Behavior | Tool seconds | Final evidence |
| --- | --- | ---: | --- | --- | --- | ---: | --- |
| initial-logs | raw | 2 | passed | passed | passed | 11.566 | [Result](../../runs/run-402cd43df7014d05a4efe6d37b41bd3c/result.json) |
| initial-logs | structured | 2 | passed | passed | passed | 8.704 | [Result](../../runs/run-45c2192cbdef477d89b13a05c38b6df9/result.json) |
| cooling-diagnostic-fidelity-v2 | raw | 1 | passed | failed | not_run | 9.697 | [Result](../../runs/run-6608b681883d4299b6e1a6aed2f54851/result.json) |
| cooling-diagnostic-fidelity-v2 | structured | 1 | passed | failed | not_run | 6.675 | [Result](../../runs/run-8fcfc673a4024ad8933d020113c82bb1/result.json) |

## Limits and original sources

Includes six recorded native control inputs and engineering recovery. The final parent could not collect the last Analyst result because its inbox tool was unavailable; the Analyst messages are preserved separately. Do not call this run fully automatic. Baseline-only follow-ups are not repair trials or evidence of a simulation pass.

Tool seconds are not model or end-to-end workflow time. Seed/temperature were not exposed matched controls, even when historical Agent plans assumed them. Missing token attribution and monetary costs remain unknown. Small samples cannot establish efficacy, equivalence or workflow acceleration. Failed runs and recovery remain part of the history.

[Original report JSON](report.json) and [session JSON](session.json) are reader-facing views; affected historical text fields are explicitly marked as editorial summaries. Exact original wording and hashes are linked in the [English-edition provenance](../../english-edition-provenance.json). Native conversation records are under `evidence/omnigent/`; affected historical text fields have the same provenance labeling. The [historical workflow measurement](../../measurements/workflow-comparison.json) documents manual/automatic observations and confounds.
