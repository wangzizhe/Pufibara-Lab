"""Constrained Docker execution. No host shell or user-provided mount paths."""
import hashlib
import json
import os
import re
import selectors
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from .evaluator import evaluate_csv
from .diagnostics import present


class DockerRunner:
    def __init__(self, root, settings):
        self.root = Path(root).resolve()
        self.settings = settings
        self.image = settings.get("omc_image_digest")
        if not self.image or not re.fullmatch(r"sha256:[0-9a-f]{64}", self.image):
            raise ValueError("Pinned local image ID required")
        self.docker = settings.get("docker_executable", "/usr/local/bin/docker")
        self.host = "unix://" + str(Path.home() / ".docker/run/docker.sock")
        self.env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "DOCKER_CONFIG": str(self.root / ".runtime/docker-config")}
        Path(self.env["DOCKER_CONFIG"]).mkdir(parents=True, exist_ok=True)

    def base(self, name):
        return [self.docker, "--host", self.host, "run", "--rm", "--pull=never", "--name", name,
                "--network=none", "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges",
                "--pids-limit=128", "--memory=768m", "--cpus=1", "--user=65534:65534",
                "--tmpfs", "/tmp:rw,nosuid,size=128m,mode=1777",
                "--tmpfs", "/work:rw,exec,nosuid,size=128m,mode=1777", "--workdir=/work",
                "--env", "HOME=/tmp"]

    def call(self, command, name):
        started = time.monotonic()
        try:
            proc = subprocess.Popen(command, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            raw = bytearray()
            status = None
            with selectors.DefaultSelector() as selector:
                selector.register(proc.stdout, selectors.EVENT_READ)
                while selector.get_map():
                    if time.monotonic() - started > self.settings["max_tool_seconds"]:
                        status = "timeout"; break
                    for key, _ in selector.select(timeout=0.1):
                        chunk = os.read(key.fd, 65536)
                        if not chunk:
                            selector.unregister(key.fileobj)
                        else:
                            raw.extend(chunk)
                    if len(raw) > 1_000_000:
                        status = "output_limit"; break
            if status:
                subprocess.run([self.docker, "--host", self.host, "rm", "-f", name], env=self.env, capture_output=True, timeout=10)
                proc.kill()
            proc.wait(timeout=10)
            proc.stdout.close()
            status = status or ("completed" if proc.returncode == 0 else "tool_error")
            return {"status": status, "exit_code": proc.returncode,
                    "seconds": time.monotonic() - started, "raw": raw[:1_000_000].decode(errors="replace"),
                    "log_truncated": len(raw) > 1_000_000}
        except (OSError, subprocess.SubprocessError) as exc:
            return {"status": "infrastructure_error", "seconds": time.monotonic() - started, "raw": str(exc), "exit_code": None}

    def probe(self):
        """Synthetic marker verifies exact mount policy; no private path is read."""
        with tempfile.TemporaryDirectory(dir=self.root / ".runtime") as folder:
            folder = Path(folder)
            outside = folder / "unmounted-canary"
            outside.write_text(uuid.uuid4().hex)
            allowed = folder / "allowed"
            allowed.mkdir()
            (allowed / "marker").write_text("allowed")
            name = "physicslab-probe-" + uuid.uuid4().hex
            # Only the newly created allowed directory is mounted.
            script = f'test "$(cat /input/marker)" = allowed && test ! -e "{outside}" && test ! -e /var/run/docker.sock && test ! -e /evaluator && test ! -w /usr && omc --version && echo ISOLATION_PROBE_OK'
            command = self.base(name) + ["--mount", f"type=bind,source={allowed},target=/input,readonly", self.image, "sh", "-c", script]
            result = self.call(command, name)
            result["passed"] = result["status"] == "completed" and "ISOLATION_PROBE_OK" in result["raw"]
            result["image"] = self.image
            result["scope"] = "Synthetic unmounted host canary, no docker socket, read-only root, unprivileged process, no network per run flags. Not an exploit-proof claim."
            (self.root / ".runtime/isolation.json").write_text(json.dumps(result, indent=2))
            return result

    def execute(self, source, mechanism, final=False):
        isolation = json.loads((self.root / ".runtime/isolation.json").read_text())
        if not isolation.get("passed") or isolation.get("image") != self.image:
            raise PermissionError("Matching isolation probe required")
        if len(source.encode()) > 32768:
            raise ValueError("Source too large")
        # Defense in depth; runtime confinement is the actual filesystem boundary.
        if re.search(r"\b(external|import|annotation)\b|Modelica\.Utilities", source):
            raise ValueError("External code, imports, annotations and utilities not permitted")
        if not re.search(r"\bmodel\s+Cooling\b", source) or not re.search(r"end\s+Cooling\s*;", source):
            raise ValueError("Expected Cooling model")
        rid = "run-" + uuid.uuid4().hex
        with tempfile.TemporaryDirectory(dir=self.root / ".runtime") as folder:
            folder = Path(folder)
            input_dir, output_dir = folder / "input", folder / "output"
            input_dir.mkdir(); output_dir.mkdir(); output_dir.chmod(0o777)
            (input_dir / "Cooling.mo").write_text(source)
            script = 'loadFile("/input/Cooling.mo");\ngetErrorString();\nprint("CHECK_BEGIN\\n");\ncheckModel(Cooling);\ngetErrorString();\nprint("CHECK_END\\n");\nsimulate(Cooling, startTime=0, stopTime=300, numberOfIntervals=300, tolerance=1e-7, outputFormat="csv", fileNamePrefix="cooling");\ngetErrorString();\n'
            if final:
                script += 'simulate(Cooling, startTime=0, stopTime=300, numberOfIntervals=300, tolerance=1e-7, outputFormat="csv", fileNamePrefix="validation", simflags="-override=C=2000,G=5");\ngetErrorString();\n'
            (input_dir / "run.mos").write_text(script)
            command = self.base(rid) + ["--mount", f"type=bind,source={input_dir},target=/input,readonly",
                       "--mount", f"type=bind,source={output_dir},target=/output", self.image,
                       "sh", "-c", 'omc /input/run.mos; status=$?; cp *_res.csv /output/ 2>/dev/null || true; exit "$status"']
            result = self.call(command, rid)
            raw = result["raw"]
            check = "passed" if re.search(r"Check of Cooling completed successfully", raw) else "failed"
            csv_path = output_dir / "cooling_res.csv"
            simulation_records = re.findall(r"record SimulationResult\b(.*?)end SimulationResult;", raw, re.S)
            simulation_succeeded = bool(simulation_records and re.search(
                r'resultFile\s*=\s*"[^"\n]+"', simulation_records[0]))
            simulation = "not_run" if check == "failed" else "passed" if simulation_succeeded and result["status"] == "completed" and not csv_path.is_symlink() and csv_path.is_file() and csv_path.stat().st_size <= 2_000_000 else "failed"
            behavior = evaluate_csv(csv_path) if simulation == "passed" else {"status": "not_run"}
            if final and behavior["status"] == "passed":
                other = evaluate_csv(output_dir / "validation_res.csv", capacity=2000, conductance=5)
                if other["status"] != "passed":
                    behavior = {"status": "failed", "reason": "Independent parameter validation failed"}
            result.update({"run_id": rid, "source_sha256": hashlib.sha256(source.encode()).hexdigest(), "image": self.image,
                           "implementation_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__), Path(__file__).with_name("evaluator.py"), Path(__file__).with_name("diagnostics.py"))},
                           "mechanism": mechanism, "final": final,
                           "evaluation": {"model_checking": check, "simulation": simulation, "behavior": behavior,
                                          "all_passed": check == simulation == behavior["status"] == "passed"},
                           "feedback": present(raw, mechanism), "tokens": None, "cost_usd": None})
            destination = self.root / "evidence/runs" / rid
            destination.mkdir(parents=True)
            (destination / "submitted.mo").write_text(source)
            (destination / "raw.log").write_text(raw)
            for csv_file in output_dir.glob("*.csv"):
                if not csv_file.is_symlink() and csv_file.is_file() and csv_file.stat().st_size <= 2_000_000:
                    (destination / csv_file.name).write_bytes(csv_file.read_bytes())
            (destination / "result.json").write_text(json.dumps(result, indent=2, allow_nan=False))
            return result
