# Policies and tested boundaries

Agents make research decisions. Trusted code controls execution, evaluation and accounting. Evidence below establishes specific checks, not universal security.

## Role permissions

| Role | Permitted research actions |
| --- | --- |
| Coordinator | Delegate declared roles and collect results. |
| Planner | Inspect status and submit a costed plan. |
| Executor | Start and finish allowed trials; delegate Modelers. |
| Modeler | Obtain its public task, submit Modelica text and inspect its own logs. |
| Analyst | Inspect permitted trial evidence and propose a budgeted follow-up. |

Agents cannot redefine final evaluation, change budgets or use arbitrary host shell/web tools. Role capabilities remain on the trusted side, outside prompts and public evidence. [Role specifications](../agents/lab/AGENTS.md) and [broker implementation](../src/physicslab/broker.py).

## Tested execution boundaries

- **Modelica container:** fixed image, no network or home/socket mounts, non-root, read-only system, dropped capabilities, and resource/time/log limits. Input is read-only; output is bounded and symlink reads are rejected. [Container checks](../evidence/isolation.json).
- **Worker:** synthetic markers verify tested file/network denials. The launcher additionally denies trusted installed package files despite allowing the Python runtime. Retest after installation changes. Real private files are not used as probes. [Worker checks](../evidence/codex-worker-isolation.json).
- **Tools:** only reviewed role tools call the local broker. Parsing and role declarations are checked separately. [Tool/specification check](../evidence/agent-spec-check.json).

## Human approval and accounting

Installation, model service and request/time budgets require authorization. Budget extensions do not reset consumption or deadlines. Failed requests and retries count. The tested subscription route prohibits automatic credit purchases and paid-API fallback; unknown usage is not zero. [Budget implementation](../src/physicslab/request_budget.py).

Publication and formal submission require explicit user authorization. This repository has been pushed to GitHub with the author's permission; that does not authorize new model runs or a formal hackathon submission. Shipped model configurations disable execution authority.

## Limits and failure handling

The checks do not prove full operating-system isolation, vulnerability-free containers, resistance to arbitrary malicious Modelica, or safety of unreviewed Agent code. Keyword screening supplements isolation; it does not replace it. Shared role capabilities depend on trusted framework dispatch. Real deployments need further review.

Keep failed, timed-out and unexecuted stages. Do not change criteria to improve scores, delete budget logs, share solutions across trials, or treat empty diagnostics as success. A fixed final verdict determines acceptance.
