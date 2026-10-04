# Historical report: Earlier automatic cooling-sign study

Broker session: `session-adba2f1eb4944d29a2b5a996284c772d`. Stage recorded: **validated**. This is an English editorial summary of preserved evidence, not a new Agent analysis or experiment. The latest demonstration is linked from the repository README.

## Research decision and result

The Agent proposed a tentative structured-feedback acceptance advantage, selected a costed matched raw/structured comparison, and then selected a fresh matched repeat after initial final acceptance tied. Both pairs passed final evaluation. Initial raw used two development attempts versus one for structured; follow-up used one each. These few observations do not establish a general benefit.

| Plan | Feedback | Development attempts | Checking | Simulation | Behavior | Tool seconds | Final evidence |
| --- | --- | ---: | --- | --- | --- | ---: | --- |
| initial-logs | raw | 2 | passed | passed | passed | 13.055 | [Result](../../runs/run-05cf3e79d9f3426b9f45535ddd2f5bfc/result.json) |
| initial-logs | structured | 1 | passed | passed | passed | 9.090 | [Result](../../runs/run-ba0c4282ae8544d9b388a9a243179275/result.json) |
| followup-logs-replicate1 | raw | 1 | passed | passed | passed | 9.727 | [Result](../../runs/run-ada46c10bd8c4ed083a9ab4fa2c2c4d3/result.json) |
| followup-logs-replicate1 | structured | 1 | passed | passed | passed | 8.410 | [Result](../../runs/run-42d3ebbc005f4e70b26bcb51de073cb0/result.json) |

## Limits and original sources

Includes infrastructure failures and recorded operator recovery. It is not an uninterrupted automatic run. The Analyst lacked per-trial attempt/diagnostic details at decision time; later saved artifacts must not be presented as evidence the Analyst had then.

Tool seconds are not model or end-to-end workflow time. Seed/temperature were not exposed matched controls, even when historical Agent plans assumed them. Missing token attribution and monetary costs remain unknown. Small samples cannot establish efficacy, equivalence or workflow acceleration. Failed runs and recovery remain part of the history.

[Original report JSON](report.json) and [session JSON](session.json) retain exact Agent hypotheses, candidates, selection reasons and limitations in their original language. Native conversation records are preserved under `evidence/omnigent/`. The [historical workflow measurement](../../measurements/workflow-comparison.json) documents manual/automatic observations and confounds.
