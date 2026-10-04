Own the initial scientific decision, not the evaluation criteria. Use status.
Return and record a plan with exactly the contract below; hypotheses are tentative.

{"id":"initial-logs","hypothesis":"Agent-generated falsifiable hypothesis",
 "falsification":"Observable result that would count against it",
 "candidates":[{"id":"logs","learning_value":"...","feasibility":"...","estimated_tool_runs":4},
               {"id":"information-loss","learning_value":"...","feasibility":"...","estimated_tool_runs":2}],
 "selected_candidate":"logs","selection_reason":"Learning value, feasibility and budget",
 "runs":[{"task_id":"cooling-sign-v1","diagnostics":"raw","replicate":0,"max_attempts":2},
         {"task_id":"cooling-sign-v1","diagnostics":"structured","replicate":0,"max_attempts":2}]}

The example is a schema, not a preselected scientific choice. Choose based on the
actual available task and budget. At most 12 deterministic tool runs cover initial
and followup experiments together; each trial costs max_attempts+1 including final
validation. Leave sufficient budget for followup. Task, exposed model configuration, tools, repair budget and evaluation stay
matched; mechanism is raw vs structured logs. Record unavailable seed/temperature
controls as limitations rather than assuming they are matched.
At least two candidate tests; no invented empirical facts. No hidden answers.

Read status.available_tasks and use those task IDs, not the example ID above.
For baseline_first tasks, max_attempts includes the unmodified diagnostic baseline
and all repair candidates. Use at least two attempts to leave one correction.
Do not claim that this controlled exposure protocol proves logs are necessary.

After dispatching a child, end your turn with a pending status. Omnigent wakes
you automatically on completion. Do not poll session info/history/inbox while
a child is running; polling consumes the shared model request budget.
