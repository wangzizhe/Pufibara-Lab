# Run a research session

The saved primary demonstration is [this completed session](../evidence/sessions/session-789344082fe64fabadcdb06e415d8d0d/session.json), with [native Omnigent messages](../evidence/omnigent-demo.json). The entry below runs the same initialization-case research environment; stochastic Agent decisions may differ.

## Before starting

Complete [local setup](LOCAL_SETUP.md). The operator must prepare a dedicated Omnigent server and project host, a dedicated Codex login, and an explicitly authorized request/time budget. Shipped configurations disable model calls. Use the host ID reported by your own server.

The case `cooling-init-v1` requires the unchanged baseline before a correction; it counts toward the two-attempt allowance. This controls feedback exposure, not whether source reasoning alone could solve the task. Checking, simulation and behavior criteria remain fixed.

## Apply and check the completion patch

```sh
.venv/bin/python scripts/patch_omnigent_completion.py
.venv/bin/python scripts/check_omnigent_completion.py
.venv/bin/python scripts/probe_codex_worker.py
PYTHONPATH=src .venv/bin/python scripts/check_initialization_case.py
```

The project-local patch supports Omnigent 0.16.0 only. It defers completion while children remain pending and preserves native dispatch, inbox and wake behavior. Reapply after reinstalling Omnigent. Synthetic checks are engineering evidence, not a replacement for the research run.

## Prepare and launch

Run these steps in order; keep the broker and host in separate terminals:

```sh
.venv/bin/python scripts/prepare_live_demo.py --enhancement
.venv/bin/python -m physicslab.cli --root "$PWD" --runtime enhancement broker
.venv/bin/python scripts/research_host.py --phase enhancement
.venv/bin/python scripts/start_handoff.py --enhancement --host-id YOUR_PROJECT_HOST_ID
```

The preparation and start scripts reject overwriting existing runs. The host disables preloading to avoid stale code. Only update packages or restart the host after roles have stopped; never restart to bypass budgets. The broker runs Docker and hidden evaluation on the trusted side; Modelers receive only their public task and permitted feedback.

## Collect and inspect

After the native roles finish:

```sh
.venv/bin/python scripts/collect_omnigent_evidence.py --enhancement
```

Keep plans, actual messages, source models, logs, CSVs, verdicts, failures and usage. Each Modeler trial requires a fresh native/Codex conversation. The Analyst may inspect bounded development evidence, not hidden answers or another trial's solution.

Requests, including failures and retries, share a locked counter and a deadline starting at the first call. Neither new children nor restarts reset them. Stop on budget, quota or isolation errors. Unknown tokens/costs remain unknown; the interface does not expose matched seed/temperature controls. Historical approvals do not authorize new execution.
