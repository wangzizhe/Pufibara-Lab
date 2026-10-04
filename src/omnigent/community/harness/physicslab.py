"""Project-local Omnigent community plugin, with no edits to upstream code."""
from omnigent.harness_plugins import HarnessContribution, _BUILTIN_CAPABILITIES
from dataclasses import replace


def contribution():
    return HarnessContribution(name="physicslab",
        valid_harnesses=frozenset({"physics-codex"}),
        harness_modules={"physics-codex": "omnigent.community.harness.physicslab"},
        capabilities={"physics-codex": replace(_BUILTIN_CAPABILITIES["codex"], subagents=True)})


def create_app():
    from physicslab.codex_harness import build_app
    return build_app()
