# Local setup

Use this guide to install and check the environment. To inspect saved experiments, no installation or LLM connection is needed: start with the [README](../README.md).

## Tested environment

macOS, Python 3.14.8, Omnigent 0.16.0 and an existing OpenModelica 1.26.1 arm64 Docker image. Dependencies are pinned in `requirements.lock`; the image identifier is in `configs/runtime.json`. Other platforms and image identifiers need separate verification.

## Install

Run from the repository root after approving dependency installation:

```sh
python3 -m venv .venv
mkdir -p .runtime/home
env -i HOME="$PWD/.runtime/home" PATH="$PWD/.venv/bin:/usr/bin:/bin" \
  .venv/bin/python -m pip --isolated install --no-cache-dir -r requirements.lock
.venv/bin/python -m pip install --no-deps --no-build-isolation .
```

Use a regular installation, not editable mode: the worker launcher denies access to installed trusted package files. After changing the installation, repeat the worker isolation probe.

## Check without model calls

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/check_agents.py
PYTHONPATH=src .venv/bin/python -m physicslab.cli probe
.venv/bin/python scripts/probe_codex_worker.py
```

Docker must be running and the configured image must already exist; execution uses `--pull=never`. The worker probe uses macOS `sandbox-exec`. These are engineering checks, not new scientific results; preserve their failures and scope.

## Run a research session

Follow [RESEARCH_RUN.md](RESEARCH_RUN.md). New live runs require a dedicated login and explicit request/time limits. Archived model configurations have authorization disabled; historical approvals do not apply to a new run.

Do not launch the default Omnigent credential-discovery flow or copy existing home-directory credentials. Use project-local state and the restricted plugin. The tested model route is Omnigent → physics-codex → Codex CLI → dedicated subscription login. Subscription calls still consume account quota; no automatic credits purchase or paid-API fallback is permitted.

## Maintenance boundaries

- The trusted broker listens on `127.0.0.1:8765`; run only one broker per port.
- `check_tool_roundtrip.py` replaces capability state. Run it only after all research services stop. For an online broker, use `check_live_capabilities.py` instead; it does not call a model.
- `broker --resume session-id` retains a settled session's controls and budget and rotates capabilities. Unsettled work requires inspection; do not delete logs or reset limits to retry.
- Credentials, `.runtime`, `.venv` and demo media are excluded. Current file hashes are in `PACKAGE_MANIFEST.json`; historical checks describe their captured state, not a new installation.

See [security policies](SECURITY.md) for isolation limits.
