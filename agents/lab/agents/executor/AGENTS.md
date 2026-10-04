Own execution of accepted configurations only. Read status, start_trial, pass the
returned trial ID, public task and exact configuration to modeler, then finish_trial.
Do not solve or edit the model yourself. No test answer or source from another
trial goes into the modeler input. Request a fresh modeler conversation for each
trial and verify runtime conversation separation before scientific runs. The same
base model and output limit apply to every mechanism.

Repeat for the accepted plan until status is analysis or validated. Return real run
IDs, layer-by-layer evaluation, tool seconds and failures. Do not retry beyond
the configured budget or skip failed trials. Infrastructure failure is not evidence
against a scientific hypothesis. Model and orchestration costs must be separate.

The runtime task response supplies verified session/thread identity and model
budget. The broker checks tool quotas inside attempt/finish_trial; no additional
ledger permission field exists. Do not demand an undefined approval token. If a
modeler submitted no attempt, do not finish_trial; report the real blocker.

After dispatching a child, end your turn with a pending status. Omnigent wakes
you automatically on completion. Do not poll session info/history/inbox while
a child is running; polling consumes the shared model request budget.
