"""Trusted accounting. Do not expose storage paths as agent tools."""
import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from .contracts import finite_nonnegative


class Ledger:
    def __init__(self, path, limits):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.limits = limits
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, at REAL, kind TEXT, payload TEXT)")
            db.execute("CREATE TABLE IF NOT EXISTS reservations (id INTEGER PRIMARY KEY, category TEXT, calls INTEGER, tokens INTEGER, usd REAL, state TEXT)")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    def record(self, kind, payload):
        with self.connect() as db:
            db.execute("INSERT INTO events(at,kind,payload) VALUES(?,?,?)", (time.time(), kind, json.dumps(payload, allow_nan=False)))

    def reserve(self, category, tokens=0, usd=0):
        if category not in ("model", "tool"):
            raise ValueError("Unknown category")
        finite_nonnegative(tokens)
        finite_nonnegative(usd)
        if type(tokens) is not int:
            raise ValueError("Token reservation must be integer")
        if category == "model" and not self.limits["model_calls_authorized"]:
            raise PermissionError("No model authorization")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            rows = db.execute("SELECT category, SUM(calls), SUM(tokens), SUM(usd) FROM reservations GROUP BY category").fetchall()
            totals = {r[0]: r[1:] for r in rows}
            calls = totals.get(category, (0, 0, 0))[0]
            ceiling = self.limits["max_model_calls" if category == "model" else "max_tool_runs"]
            if calls + 1 > ceiling:
                raise RuntimeError("Call budget exhausted")
            all_tokens = sum(r[2] or 0 for r in rows)
            all_usd = sum(r[3] or 0 for r in rows)
            if all_tokens + tokens > self.limits["max_model_tokens"] or all_usd + usd > self.limits["max_total_usd"]:
                raise RuntimeError("Token or cost budget exhausted")
            cursor = db.execute("INSERT INTO reservations(category,calls,tokens,usd,state) VALUES(?,1,?,?,?)", (category, tokens, usd, "reserved"))
            return cursor.lastrowid

    def settle(self, rid, actual_tokens=None, actual_usd=None):
        # Unknown actual usage keeps the full reservation and remains unknown in evidence.
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT tokens,usd,state FROM reservations WHERE id=?", (rid,)).fetchone()
            if row is None or row[2] != "reserved":
                raise ValueError("Reservation absent or already settled")
            for actual, bound in ((actual_tokens, row[0]), (actual_usd, row[1])):
                if actual is not None and finite_nonnegative(actual) > bound:
                    raise RuntimeError("Actual usage exceeds reservation; halt provider")
            db.execute("UPDATE reservations SET tokens=?,usd=?,state='settled' WHERE id=?", (row[0] if actual_tokens is None else actual_tokens, row[1] if actual_usd is None else actual_usd, rid))
            db.execute("INSERT INTO events(at,kind,payload) VALUES(?,?,?)", (time.time(), "usage", json.dumps({"reservation": rid, "tokens": actual_tokens, "usd": actual_usd})))

    def events(self):
        with self.connect() as db:
            return [{"id": r[0], "at": r[1], "kind": r[2], "payload": json.loads(r[3])} for r in db.execute("SELECT * FROM events ORDER BY id")]

    def unsettled(self):
        with self.connect() as db:
            return [{"id": r[0], "category": r[1], "reserved_tokens": r[2], "reserved_usd": r[3]}
                    for r in db.execute("SELECT id,category,tokens,usd FROM reservations WHERE state='reserved' ORDER BY id")]
