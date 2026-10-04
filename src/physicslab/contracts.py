"""Validate decisions without making them or changing the evaluator."""
import math
import re


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", value):
        raise ValueError("Invalid identifier")
    return value


def finite_nonnegative(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError("Expected finite nonnegative number")
    return value


def validate_plan(plan, max_runs=12):
    """Require two costed candidates, fixed controls, and explicit falsification."""
    identifier(plan["id"])
    for key in ("hypothesis", "falsification", "selection_reason"):
        if not isinstance(plan.get(key), str) or not plan[key].strip():
            raise ValueError(f"Missing {key}")
    candidates = plan["candidates"]
    if not isinstance(candidates, list) or len(candidates) < 2:
        raise ValueError("At least two candidate experiments required")
    ids = set()
    for candidate in candidates:
        cid = identifier(candidate["id"])
        if cid in ids:
            raise ValueError("Duplicate candidate")
        ids.add(cid)
        for key in ("learning_value", "feasibility"):
            if not isinstance(candidate.get(key), str) or not candidate[key].strip():
                raise ValueError(f"Missing candidate {key}")
        finite_nonnegative(candidate["estimated_tool_runs"])
    if plan["selected_candidate"] not in ids:
        raise ValueError("Selected candidate not declared")
    runs = plan["runs"]
    if not runs or len(runs) > max_runs:
        raise ValueError("Tool budget exceeded or empty plan")
    controls = None
    for run in runs:
        if set(run) != {"task_id", "diagnostics", "replicate", "max_attempts"}:
            raise ValueError("Unexpected experiment fields (evaluation cannot be changed)")
        identifier(run["task_id"])
        if run["diagnostics"] not in ("raw", "structured"):
            raise ValueError("Unsupported mechanism")
        if type(run["replicate"]) is not int or run["replicate"] < 0:
            raise ValueError("Invalid replicate")
        if type(run["max_attempts"]) is not int or not 1 <= run["max_attempts"] <= 3:
            raise ValueError("Invalid repair limit")
        if controls is None:
            controls = run["max_attempts"]
        elif controls != run["max_attempts"]:
            raise ValueError("Repair budget must remain matched")
    return plan


def validate_analysis(analysis, run_ids, previous_plan):
    """An agent must cite real evidence and make an executable next choice."""
    if analysis.get("support") not in ("supported", "not_supported", "inconclusive"):
        raise ValueError("Invalid hypothesis support")
    refs = analysis.get("evidence_run_ids", [])
    if not refs or not set(refs) <= set(run_ids):
        raise ValueError("Analysis must reference existing runs")
    for key in ("limitations", "adjustment_reason"):
        if not isinstance(analysis.get(key), str) or not analysis[key].strip():
            raise ValueError(f"Missing {key}")
    followup = validate_plan(analysis["followup"])
    if followup["id"] == previous_plan["id"]:
        raise ValueError("Follow-up needs a new plan id")
    if followup["runs"] == previous_plan["runs"] and not analysis.get("repeat_reason"):
        raise ValueError("Unchanged configuration requires evidence-driven repeat reason")
    return analysis
