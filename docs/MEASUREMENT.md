# Measurement results, limits and next experiment

## Existing observations

- Historical manual workflow: 813.986 seconds and six human UI actions; reusable preparation by Codex was recorded separately. Historical automatic workflow: 2293.816 seconds and ten recorded native control inputs, including engineering recovery. Operator, infrastructure maturity and incomplete action accounting prevent a valid speedup claim. [Source](../evidence/measurements/workflow-comparison.json).
- Latest user-started run: native goal-to-final-summary timestamp span of 766 seconds, one human goal input and no additional native root control inputs. This retrospective span excludes preparation and has no matched manual control. Do not divide it by the historical manual time. [Source](../evidence/measurements/demo-observation.json).
- A targeted notification regression recorded 22 seconds from final Executor completion to parent summary with no stage recovery. This narrower engineering observation is not a matched full-workflow acceleration measurement. [Source](../evidence/measurements/completion-bottleneck.json).

## Mechanism comparison

On cooling-init-v1, raw and structured feedback both passed two of two trials, each in two development attempts. Initial tool seconds were raw 12.208 / structured 10.258; follow-up was raw 9.750 / structured 11.672. Timing order reversed. Tool seconds exclude model and other workflow overhead. Two pairs on one task cannot establish general benefit or equivalence. Per-trial token savings and overall speedup remain unproven. [Actual plans and results](../evidence/sessions/session-789344082fe64fabadcdb06e415d8d0d/session.json).

## Next experiment — proposed, not executed

Compare a manual six-stage trigger workflow with a single-goal automatic workflow on the same prepared environment, physical task, exposed model route, tools, repair allowance and fixed evaluation. Start at the accepted research goal and finish at a complete traceable report containing the same required planning, experiment, analysis and follow-up evidence. Include model waits, retries, failures and operator recovery; separately report reusable setup and human actions. Alternate order if repeated. Seed and temperature are not exposed controls and must remain documented limitations. Validate token attribution before claiming savings.

For a valid matched comparison only, define speed factor as manual time / automatic time, and time saved as (manual time − automatic time) / manual time × 100%. No such matched speed result is available in this submission. Any future execution requires its own applicable authorization. No new experiment was performed during submission cleanup.
