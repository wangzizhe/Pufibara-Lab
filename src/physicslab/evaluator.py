"""Trusted evaluator, never mounted into an agent workspace.

The analytic oracle is an engineering test, not experimental evidence.
"""
import csv
import math
from pathlib import Path


def evaluate_csv(path, capacity=1000, conductance=10):
    try:
        if Path(path).is_symlink():
            raise ValueError("Symlink results are rejected")
        with open(path, newline="") as stream:
            rows = list(csv.DictReader(stream))
        if len(rows) < 10 or len(rows) > 10000:
            raise ValueError("Unexpected sample count")
        points = [(float(row["time"]), float(row["T"])) for row in rows]
        if not all(math.isfinite(t) and math.isfinite(v) for t, v in points):
            raise ValueError("Nonfinite trajectory")
        times = [p[0] for p in points]
        if abs(times[0]) > 1e-8 or abs(times[-1] - 300) > 1e-6:
            raise ValueError("Wrong time domain")
        if any(b < a for a, b in zip(times, times[1:])):
            raise ValueError("Nonmonotone time")
        error = max(abs(value - (293.15 + 40 * math.exp(-conductance * t / capacity))) for t, value in points)
        passed = error <= 0.02 and all(293.15 - 0.02 <= v <= 333.15 + 0.02 for _, v in points)
        return {"status": "passed" if passed else "failed", "max_abs_error_k": error, "samples": len(points)}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {"status": "failed", "reason": str(exc)}
