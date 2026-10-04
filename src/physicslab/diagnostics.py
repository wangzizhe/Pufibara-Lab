"""Loss-aware presentation; raw logs remain separately queryable."""
import re


def present(raw, mechanism):
    if mechanism == "raw":
        return {"mechanism": "raw", "raw": raw}
    if mechanism != "structured":
        raise ValueError("Unknown diagnostic mechanism")
    lines = raw.splitlines()
    selected = [line for line in lines if re.search(r"error|warning|failed|assert|singular", line, re.I)]
    return {
        "mechanism": "structured", "diagnostic_lines": selected,
        "parser": "keyword-v1", "total_lines": len(lines),
        "omitted_lines": len(lines) - len(selected),
        "raw_available": True, "interpretation": "Compiler messages only; no inferred repair or validation answer.",
        "empty_diagnostic": not selected,
    }
