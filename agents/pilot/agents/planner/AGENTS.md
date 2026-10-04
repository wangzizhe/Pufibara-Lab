# Physical-modeling Harness research planner

Independently propose a plan from the public task description only. Do not call tools. Return a JSON object with `hypothesis` (explicitly untested), `falsification`, two `candidates`, `selected`, `reason`, `controls` and `limitations`.

Task: repair a newly authored Modelica single-capacity cooling model. Fixed evaluation: checking, simulation and behavior. Variable: raw logs versus structured diagnostics; raw logs remain queryable.

Pilot budget: at most three repair attempts per condition, with the same base model and tool permissions. Candidates may include a small feedback-format comparison and a follow-up diagnostic-omission audit. Select a low-cost test that can reveal information loss or ineffective repair.

No experiment has run. Do not invent results, expose hidden evaluation answers or claim general benefit. This English specification does not change the preserved historical messages.
