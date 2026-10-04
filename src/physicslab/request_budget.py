"""Pre-forward gate for subscription model requests; never records headers/body."""
import json
import threading
import time
import os
from pathlib import Path


def validate_demo_authorization(root, config):
    """Bind this new authorization to all preserved earlier phase journals."""
    if (not config.get("authorization_confirmed") or config.get("allow_api_fallback")
            or config.get("allow_credit_purchase")):
        raise PermissionError("Subscription-only demo authorization required")
    historical = 0
    for phase in ("pilot", "research", "enhancement"):
        rows = [json.loads(line) for line in
                (root / f".runtime/{phase}-requests.jsonl").read_text().splitlines()]
        actual = max((r.get("reserved_requests", 0) for r in rows), default=0)
        if actual != config[f"historical_{phase}_requests"]:
            raise PermissionError("Historical usage changed; do not reset it")
        historical += actual
    if (historical != config["prior_phase_requests"]
            or historical + config["max_model_requests"] > config["cumulative_request_ceiling"]):
        raise PermissionError("Demo would exceed cumulative authorization")
    return historical


class RequestBudget:
    def __init__(self, *, max_requests: int, wall_seconds: float, journal: Path,
                 clock=time.monotonic, resume=False, wall_clock=time.time,
                 start_on_first_request=False):
        if max_requests <= 0 or wall_seconds <= 0:
            raise ValueError("Positive request/time limits required")
        self.max_requests = max_requests
        self.clock = clock
        self.wall_clock = wall_clock
        self.wall_seconds = wall_seconds
        self.deadline = float("inf") if start_on_first_request else clock() + wall_seconds
        self.journal = journal
        self.journal.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.requests = 0
        if resume:
            records = [json.loads(line) for line in journal.read_text().splitlines()]
            headers = [r for r in records if r.get("event") in {"budget_started", "budget_authorized"}]
            origins = [r for r in headers if r.get("event") == "budget_authorized"]
            if origins:
                if len(origins) != 1 or len(headers) > 2:
                    raise ValueError("Ambiguous authorization origin")
                headers = [headers[-1]]
            if len(headers) != 1:
                raise ValueError("Budget origin unavailable; do not reset or infer authorization")
            amendments = [r for r in records if r.get("event") == "budget_amended"]
            header = amendments[-1] if amendments else headers[0]
            if header["max_requests"] != max_requests or header["wall_seconds"] != wall_seconds:
                raise ValueError("Pilot limits cannot change during resume")
            counts = [r["reserved_requests"] for r in records if r.get("event") == "request_gate"]
            self.requests = max(counts, default=0)
            self.deadline = (clock() + header["deadline_unix"] - wall_clock()
                             if header["deadline_unix"] is not None else float("inf"))
            self.stream = journal.open("a", encoding="utf-8")
        else:
            self.stream = journal.open("x", encoding="utf-8")
            self.stream.write(json.dumps({"event": "budget_authorized" if start_on_first_request else "budget_started",
                "max_requests": max_requests, "wall_seconds": wall_seconds,
                "deadline_unix": None if start_on_first_request else wall_clock() + wall_seconds}) + "\n")
            self.stream.flush()
            os.fsync(self.stream.fileno())
            self.stream.close()
            self.stream = journal.open("a", encoding="utf-8")

    def reserve(self) -> bool:
        """Count before forwarding, including failed requests and retries."""
        with self.lock:
            if self.deadline == float("inf"):
                self.deadline = self.clock() + self.wall_seconds
                self.stream.write(json.dumps({"event": "budget_started", "max_requests": self.max_requests,
                    "wall_seconds": self.wall_seconds, "started_unix": self.wall_clock(),
                    "deadline_unix": self.wall_clock() + self.wall_seconds}) + "\n")
            reason = "allowed"
            if self.clock() >= self.deadline:
                reason = "time_limit"
            elif self.requests >= self.max_requests:
                reason = "request_limit"
            if reason == "allowed":
                self.requests += 1
            self.stream.write(json.dumps({"event": "request_gate", "reason": reason,
                "reserved_requests": self.requests}) + "\n")
            self.stream.flush()
            os.fsync(self.stream.fileno())
            return reason == "allowed"

    def close(self):
        self.stream.close()


class SubscriptionRequestGate:
    """Install only in the dedicated pilot process's Omnigent egress proxy.

    Narrow HTTP/1 rules prohibit unrestricted HTTP/2 tunnels. Native websocket
    inference must be disabled/denied before using this gate in a live pilot.
    Subscription/no-credit checks are independent and remain required.
    """
    def __init__(self, budget: RequestBudget, subscription_ready):
        self.budget = budget
        self.subscription_ready = subscription_ready

    def check(self, original, rules, method, host, path):
        if not original(rules, method, host, path):
            return False
        # Exact paths only: reject websocket GET, alternate inference routes,
        # query suffixes and non-ChatGPT providers rather than silently bypass.
        if host != "chatgpt.com":
            return False
        if method == "POST" and path == "/backend-api/codex/responses":
            return self.subscription_ready() is True and self.budget.reserve()
        return (method == "GET" and path.startswith("/backend-api/")
            and not path.startswith("/backend-api/codex/responses"))


class SharedRequestBudget(RequestBudget):
    """Cross-process reservations for separately spawned Omnigent harnesses."""
    def refresh_deadline(self):
        import fcntl
        with self.journal.with_suffix(".lock").open("a") as lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_SH)
            records = [json.loads(line) for line in self.journal.read_text().splitlines()]
            header = next(r for r in reversed(records)
                          if r.get("event") in {"budget_started", "budget_amended", "budget_authorized"})
            self.deadline = (self.clock() + header["deadline_unix"] - self.wall_clock()
                             if header["deadline_unix"] is not None else float("inf"))
            return self.deadline

    def reserve(self):
        import fcntl
        with self.journal.with_suffix(".lock").open("a") as lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            try:
                records = [json.loads(line) for line in self.journal.read_text().splitlines()]
                self.requests = max((r["reserved_requests"] for r in records
                    if r.get("event") == "request_gate"), default=0)
                header = next((r for r in reversed(records)
                               if r.get("event") in {"budget_started", "budget_amended", "budget_authorized"}), None)
                if header is None:
                    raise ValueError("Missing budget authorization")
                self.deadline = (self.clock() + header["deadline_unix"] - self.wall_clock()
                                 if header["deadline_unix"] is not None else float("inf"))
                return super().reserve()
            finally:
                fcntl.flock(lock_file, fcntl.LOCK_UN)
