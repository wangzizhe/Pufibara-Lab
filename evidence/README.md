# Evidence navigation

## Primary completed demonstration

- [Actual session](sessions/session-789344082fe64fabadcdb06e415d8d0d/session.json): two hypotheses/plans, costed candidates, initial matched pair, analysis and executed follow-up; four trials and twelve deterministic runs.
- [Native Omnigent tree](omnigent-demo.json): actual research roles and dispatches. Preparation-time fields are nested separately and are not current request counters.
- [Native conversations](omnigent/e33643e43bc04dba8cd0fd538bbe4dde/): inspect the root and children for actual messages and tool calls.
- [Native timestamp observation](measurements/demo-observation.json): retrospective timing and control-input count, source hashes and limitations.
- The session's `attempts` and `final_run_id` fields resolve to `runs/<run-id>/`. Each result stores actual verdicts and provenance. Failed baselines are part of the evidence.

## Supporting measurements and engineering evidence

- [Historical workflow measurement](measurements/workflow-comparison.json): real human UI clicks and automatic-path observations, with confounds; no valid speedup claim.
- [Notification regression](completion-regression.json) and [bottleneck observation](measurements/completion-bottleneck.json): narrower engineering evidence, not a scientific performance benchmark.
- [Worker isolation](codex-worker-isolation.json), [container isolation](isolation.json), [role/tool parsing](agent-spec-check.json): bounded engineering checks, not universal security proof.

## Historical appendix

Other sessions, runs, usage journals and failure/recovery records remain for audit. They are not additional replicates of the primary demo. [Historical index](HISTORICAL_INDEX.md) and older index/manifest/verification files describe their own captured state and may predate the current code and latest run; do not treat them as current aggregates. Engineering fixtures and synthetic probes must remain distinct from Agent-generated experiments. Global usage records require attribution before summing tokens; missing costs are not zero.

No experiment or model call was performed during submission cleanup. Source files and run records remain evidence; the README workflow illustration is explanatory only.

Historical non-English text uses labeled editorial views; primary English run evidence is unchanged. See the [English-edition policy](../docs/ENGLISH_EDITION.md) and its source hashes before auditing exact historical wording.
