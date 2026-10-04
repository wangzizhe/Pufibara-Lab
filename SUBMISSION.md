# Submission evidence map

For a quick overview, read the [README](README.md). This page maps the requested deliverables to reviewable material. The repository is on GitHub; formal hackathon submission is a separate author action.

| Requested item | Material |
| --- | --- |
| Repository and reproducible experiment code | [Local setup](docs/LOCAL_SETUP.md), [research execution](docs/RESEARCH_RUN.md), `src/`, `scripts/`, `tasks/`, `tests/`, `requirements.lock`. |
| Agent specifications and policies | [Role package](agents/lab/AGENTS.md) and [permissions/approval gates](docs/SECURITY.md). |
| Two-minute demo | Supplied separately by the author. |
| Cited evidence and results | [Public sources](docs/SOURCES.md), [primary session](evidence/sessions/session-789344082fe64fabadcdb06e415d8d0d/session.json), [native role tree](evidence/omnigent-demo.json), [evidence navigation](evidence/README.md). |
| Measured improvement | [Timing observations and limits](docs/MEASUREMENT.md). Overall speedup and token savings remain unproven. |
| Next experiment | Matched manual-trigger/automatic workflow benchmark, proposed only in [MEASUREMENT](docs/MEASUREMENT.md). |

## Scientific status

**Agent hypothesis:** structured diagnostics improve acceptance under the same two-attempt allowance. **Observed:** both arms passed both trials in two attempts; tool-time ordering reversed. **Conditional conclusion:** no advantage observed on this task; the sample cannot establish general efficacy or equivalence. The [primary session](evidence/sessions/session-789344082fe64fabadcdb06e415d8d0d/session.json) preserves candidate costs, controls, initial results and the reason for selecting a fresh follow-up pair.

The [latest native timestamp observation](evidence/measurements/demo-observation.json) records 766 seconds and one human goal input, excluding preparation. The [older workflow comparison](evidence/measurements/workflow-comparison.json) has operator and infrastructure confounds. These do not establish causal acceleration. Missing token attribution/costs are not zero.

Task, exposed model route, tools, attempt allowance and fixed evaluation were matched; seed/temperature controls were unavailable. Separate modeling conversations, failed baselines and final run provenance are retained. Engineering probes are not counted as research replicates.

Before real-world use: independent tasks, broader repetitions, reliable cost/time instrumentation, measured physical data, numerical robustness and qualified review remain outstanding. Current file hashes are in `PACKAGE_MANIFEST.json`. A repository-wide code license remains undecided.
