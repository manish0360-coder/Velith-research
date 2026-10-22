from __future__ import annotations

import copy
import http.server
import json
import os
import socketserver
import tempfile
import threading
import unittest

import hostmon

IMG = "sha256:" + "a" * 64
GOOD = {
    "Image": IMG,
    "Config": {
        "Entrypoint": None, "Cmd": ["python", "-m", "harness_tests.synth"], "User": "1000:1000",
        "Env": [f"{k}={v}" for k, v in hostmon.EXPECTED_ENV.items()] + ["PATH=/usr/local/bin"],
    },
    "HostConfig": {
        "Init": None, "NetworkMode": "none", "NanoCpus": 1_000_000_000, "Memory": 2**31, "MemorySwap": 2**31,
        "PidsLimit": 64, "ReadonlyRootfs": True, "Privileged": False, "CapDrop": ["ALL"], "CapAdd": None,
        "SecurityOpt": ["no-new-privileges"], "Ulimits": [{"Name": "cpu", "Hard": 5, "Soft": 5}],
        "Tmpfs": {"/tmp": "rw,size=64m"}, "Binds": ["/r:/egrid:ro", "/r/runs/x/S/stage:/out"],
    },
}
KW = {"image_id": IMG, "cap_s": 5, "memory": 2**31, "code_root": "/r", "stage_dir": "/r/runs/x/S/stage"}


class TestVerifyConfig(unittest.TestCase):
    def test_good_config(self) -> None:
        self.assertEqual(hostmon.verify_config(GOOD, **KW), [])

    def test_each_violation_detected(self) -> None:
        mutations = [
            ("Image", None, "sha256:" + "b" * 64),
            ("Config", "Entrypoint", ["/bin/sh", "-c"]),
            ("HostConfig", "Init", True),
            ("HostConfig", "NetworkMode", "bridge"),
            ("HostConfig", "NanoCpus", 2_000_000_000),
            ("HostConfig", "Memory", 2**32),
            ("HostConfig", "PidsLimit", 0),
            ("HostConfig", "ReadonlyRootfs", False),
            ("HostConfig", "CapDrop", []),
            ("HostConfig", "SecurityOpt", []),
            ("HostConfig", "Ulimits", [{"Name": "cpu", "Hard": 6, "Soft": 5}]),
            ("HostConfig", "Binds", ["/r:/egrid", "/r/runs/x/S/stage:/out"]),
            ("Config", "User", "0:0"),
            ("Config", "Env", []),
        ]
        for section, key, value in mutations:
            info = copy.deepcopy(GOOD)
            if key is None:
                info[section] = value
            else:
                info[section][key] = value
            self.assertTrue(hostmon.verify_config(info, **KW), f"{section}.{key} not detected")


class TestDecide(unittest.TestCase):
    base = {"cpu_ns": 1, "n_procs": 1, "elapsed_s": 1.0, "faults": 0, "cap_s": 5, "proc_check": True, "wall_s": 60}

    def d(self, **over: object) -> str | None:
        return hostmon.decide(**{**self.base, **over})

    def test_decisions(self) -> None:
        self.assertIsNone(self.d())
        self.assertIsNone(self.d(cpu_ns=4_999_999_999))
        self.assertEqual(self.d(cpu_ns=5_000_000_000), "cpu_budget")
        self.assertEqual(self.d(n_procs=2), "child_process")
        self.assertIsNone(self.d(n_procs=2, proc_check=False))
        self.assertEqual(self.d(elapsed_s=60.0), "wall_limit")
        self.assertEqual(self.d(faults=3), "monitor_fault")
        self.assertIsNone(self.d(cpu_ns=None, n_procs=None, faults=2))


class FakeEngine:
    def __init__(self, cpu: list[int], procs: list[int], running_for: int = 1000, fail_at: set[int] | None = None) -> None:
        self.cpu, self.procs, self.running_for, self.fail_at = cpu, procs, running_for, fail_at or set()
        self.i = 0
        self.killed = False

    def running(self, cid: str) -> bool:
        return not self.killed and self.i < self.running_for

    def cpu_ns(self, cid: str) -> int:
        i = self.i
        self.i += 1
        if i in self.fail_at:
            raise hostmon.EngineError("boom")
        return self.cpu[min(i, len(self.cpu) - 1)]

    def processes(self, cid: str) -> list[list[str]]:
        n = self.procs[min(self.i - 1, len(self.procs) - 1)]
        return [["pid"]] * n

    def kill(self, cid: str) -> int:
        self.killed = True
        return 204


class FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def sleep(self, s: float) -> None:
        self.t += max(s, 0.25)


class TestMonitorLoop(unittest.TestCase):
    def run_mon(self, eng: FakeEngine, proc_check: bool = True, wall: float = 60.0) -> dict:
        clk = FakeClock()
        return hostmon.monitor(eng, "c", cap_s=5, poll_s=0.25, wall_s=wall, proc_check=proc_check, clock=clk, sleep=clk.sleep)

    def test_cpu_budget_kill(self) -> None:
        eng = FakeEngine(cpu=[int(x * 1e9) for x in (1, 2, 3, 4, 5.1)], procs=[1])
        rec = self.run_mon(eng)
        self.assertEqual(rec["terminated_by"], "cpu_budget")
        self.assertTrue(eng.killed)
        self.assertEqual(rec["kill_http_status"], 204)
        self.assertAlmostEqual(rec["last_cpu_s"], 5.1)

    def test_child_process_kill(self) -> None:
        eng = FakeEngine(cpu=[10], procs=[1, 2])
        rec = self.run_mon(eng)
        self.assertEqual(rec["terminated_by"], "child_process")
        self.assertEqual(len(rec["processes"]), 2)

    def test_normal_exit_no_kill(self) -> None:
        eng = FakeEngine(cpu=[10, 20], procs=[1], running_for=2)
        rec = self.run_mon(eng)
        self.assertIsNone(rec["terminated_by"])
        self.assertFalse(eng.killed)
        self.assertEqual(rec["end"], "exited")

    def test_faults_fail_closed(self) -> None:
        eng = FakeEngine(cpu=[10], procs=[1], fail_at={0, 1, 2, 3, 4})
        rec = self.run_mon(eng)
        self.assertEqual(rec["terminated_by"], "monitor_fault")

    def test_wall_limit(self) -> None:
        eng = FakeEngine(cpu=[10], procs=[1])
        rec = self.run_mon(eng, wall=1.0)
        self.assertEqual(rec["terminated_by"], "wall_limit")


class _Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args: object) -> None:
        pass

    def address_string(self) -> str:  # unix sockets have no (host, port)
        return "unix"

    def _send(self, code: int, obj: object | None) -> None:
        body = b"" if obj is None else json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path.startswith("/containers/c1/stats"):
            self._send(200, {"cpu_stats": {"cpu_usage": {"total_usage": 1234567}}})
        elif self.path == "/containers/c1/json":
            self._send(200, {"State": {"Running": True}})
        elif self.path == "/containers/c1/top":
            self._send(200, {"Titles": ["PID"], "Processes": [["1"], ["7"]]})
        else:
            self._send(404, {"message": "no"})

    def do_POST(self) -> None:
        self._send(204 if self.path == "/containers/c1/kill?signal=KILL" else 404, None)


class _UnixServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True


class TestEngineOverUnixSocket(unittest.TestCase):
    def test_engine_http_plumbing(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "s")
            srv = _UnixServer(path, _Handler)
            th = threading.Thread(target=srv.serve_forever, daemon=True)
            th.start()
            try:
                eng = hostmon.Engine(path)
                self.assertTrue(eng.running("c1"))
                self.assertEqual(eng.cpu_ns("c1"), 1234567)
                self.assertEqual(len(eng.processes("c1")), 2)
                self.assertEqual(eng.kill("c1"), 204)
                with self.assertRaises(hostmon.EngineError):
                    eng.get_json("/containers/zz/json")
            finally:
                srv.shutdown()
                srv.server_close()
                th.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
