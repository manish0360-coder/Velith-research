from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from egrid import driver
from egrid.classify import validate_status
from egrid.driver import Limits, StageContext, StopCondition, check_budget, execute, exit_code_for

BIG = Limits(cpu_cap_s=100_000, reserve_s=1.0, check_interval_s=0.05)


class TestCodes(unittest.TestCase):
    def test_exit_codes(self) -> None:
        self.assertEqual(exit_code_for(None), 0)
        self.assertEqual(exit_code_for("STOP-1"), 65)
        self.assertEqual(exit_code_for("STOP-8"), 72)
        self.assertEqual(exit_code_for("STOP-9"), 73)
        self.assertEqual(exit_code_for("UNCLASSIFIED"), 80)
        with self.assertRaises(ValueError):
            exit_code_for("STOP-10")

    def test_stop_condition_is_not_an_exception_subclass(self) -> None:
        self.assertFalse(issubclass(StopCondition, Exception))
        with self.assertRaises(ValueError):
            StopCondition("STOP-0", "bad")

    def test_limits_validation(self) -> None:
        with self.assertRaises(ValueError):
            Limits(cpu_cap_s=5, reserve_s=5, check_interval_s=0.05)
        with self.assertRaises(ValueError):
            Limits(cpu_cap_s=5, reserve_s=1, check_interval_s=1)


class TestBudget(unittest.TestCase):
    lim = Limits(cpu_cap_s=5, reserve_s=1.0, check_interval_s=0.05)

    def test_below_threshold_passes(self) -> None:
        check_budget(self.lim, cpu_fn=lambda: 3.99, children_fn=list, child_cpu_fn=lambda: 0.0)

    def test_threshold_raises_stop8(self) -> None:
        with self.assertRaises(StopCondition) as cm:
            check_budget(self.lim, cpu_fn=lambda: 4.0, children_fn=list, child_cpu_fn=lambda: 0.0)
        self.assertEqual(cm.exception.code, "STOP-8")

    def test_live_child_raises_stop2(self) -> None:
        with self.assertRaises(StopCondition) as cm:
            check_budget(self.lim, cpu_fn=lambda: 0.1, children_fn=lambda: [42], child_cpu_fn=lambda: 0.0)
        self.assertEqual(cm.exception.code, "STOP-2")

    def test_reaped_child_cpu_raises_stop2(self) -> None:
        with self.assertRaises(StopCondition) as cm:
            check_budget(self.lim, cpu_fn=lambda: 0.1, children_fn=list, child_cpu_fn=lambda: 0.01)
        self.assertEqual(cm.exception.code, "STOP-2")

    def test_live_children_reads_proc(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            for tid, kids in (("1", "7 9 "), ("2", "")):
                p = Path(d, "self", "task", tid)
                p.mkdir(parents=True)
                (p / "children").write_text(kids, encoding="ascii")
            self.assertEqual(driver.live_children(d), [7, 9])
            Path(d, "self", "task", "3").mkdir()  # thread that exited before its file was read
            self.assertEqual(driver.live_children(d), [7, 9])

    def test_no_readable_children_file_raises(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            Path(d, "self", "task", "1").mkdir(parents=True)
            with self.assertRaises(OSError):
                driver.live_children(d)

    def test_monitor_internal_error_fails_closed(self) -> None:
        def broken(limits: Limits) -> None:
            raise OSError("proc gone")

        with tempfile.TemporaryDirectory() as d:
            ctx = StageContext("SYN-UNIT", "run-1", Path(d), BIG, checker=broken)
            stop, reason = execute(ctx, lambda c: c.checkpoint(), [])
        self.assertEqual(stop, "UNCLASSIFIED")
        self.assertIn("monitor failed", reason)


class TestAtomicWrite(unittest.TestCase):
    def test_write_complete_and_no_temp(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            driver.atomic_write(Path(d, "x.bin"), b"abc")
            self.assertEqual(Path(d, "x.bin").read_bytes(), b"abc")
            self.assertEqual(os.listdir(d), ["x.bin"])

    def test_interrupted_write_leaves_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as d, mock.patch.object(driver.os, "write", side_effect=OSError("boom")):
            with self.assertRaises(OSError):
                driver.atomic_write(Path(d, "x.bin"), b"abc")
            self.assertEqual(os.listdir(d), [])


class TestContextAndExecute(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.out = Path(self._td.name)
        self.ctx = StageContext("SYN-UNIT", "run-1", self.out, BIG)

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_artifact_names_validated(self) -> None:
        for bad in ("", "../x", "a/b", "stage_status.json", ".tmp-x"):
            with self.assertRaises(ValueError):
                self.ctx.write_artifact(bad, "x")
        self.ctx.write_artifact("ok.json", {"b": 1, "a": 2})
        self.assertEqual((self.out / "ok.json").read_bytes(), b'{"a":2,"b":1}\n')
        with self.assertRaises(ValueError):
            self.ctx.write_artifact("ok.json", "again")
        self.ctx.close()
        with self.assertRaises(RuntimeError):
            self.ctx.write_artifact("late.txt", "x")

    def test_pass(self) -> None:
        stop, _ = execute(self.ctx, lambda c: c.write_artifact("r.txt", "x"), ["r.txt"])
        self.assertIsNone(stop)

    def test_missing_required_is_unclassified(self) -> None:
        stop, reason = execute(self.ctx, lambda c: None, ["r.txt"])
        self.assertEqual(stop, "UNCLASSIFIED")
        self.assertIn("r.txt", reason)

    def test_exception_mapping(self) -> None:
        def raiser(exc: BaseException):
            def fn(c: StageContext) -> None:
                raise exc
            return fn

        cases = [
            (StopCondition("STOP-5", "x"), "STOP-5"),
            (AssertionError("x"), "STOP-2"),
            (RuntimeError("x"), "UNCLASSIFIED"),
            (MemoryError(), "UNCLASSIFIED"),
            (SystemExit(0), "UNCLASSIFIED"),
            (KeyboardInterrupt(), "UNCLASSIFIED"),
        ]
        for exc, want in cases:
            ctx = StageContext("SYN-UNIT", "run-1", self.out, BIG)
            self.assertEqual(execute(ctx, raiser(exc), [])[0], want, repr(exc))

    def test_swallowed_stop_is_latched(self) -> None:
        tiny = Limits(cpu_cap_s=1, reserve_s=0.999, check_interval_s=0.0005)
        ctx = StageContext("SYN-UNIT", "run-1", self.out, tiny)

        def swallow(c: StageContext) -> None:
            try:
                c.checkpoint()
            except BaseException:  # noqa: BLE001 - simulates a misbehaving stage
                pass

        stop, reason = execute(ctx, swallow, [])
        self.assertEqual(stop, "STOP-8")

    def test_status_round_trip_is_valid(self) -> None:
        self.ctx.write_artifact("r.txt", "x")
        for stop in (None, "STOP-8", "UNCLASSIFIED"):
            status = driver.build_status(self.ctx, stop, "r", {}, ["r.txt"])
            self.assertEqual(validate_status(status, "SYN-UNIT", "run-1"), [])
            self.assertEqual(status["exit_code"], exit_code_for(stop))

    def test_run_stage_refuses_nonempty_dir(self) -> None:
        (self.out / "existing").write_text("x", encoding="ascii")
        rc = driver.run_stage("SYN-UNIT", lambda c: None, run_id="run-1", out_dir=self.out, limits=BIG)
        self.assertEqual(rc, 80)
        self.assertEqual(sorted(os.listdir(self.out)), ["existing"])


class TestPreflight(unittest.TestCase):
    def test_observes_fake_roots(self) -> None:
        lim = Limits(cpu_cap_s=5, reserve_s=1.0, check_interval_s=0.05)
        with tempfile.TemporaryDirectory() as d:
            proc, cg = Path(d, "proc"), Path(d, "cg")
            (proc / "self" / "task" / "1").mkdir(parents=True)
            (proc / "self" / "task" / "1" / "children").write_text("", encoding="ascii")
            (proc / "net").mkdir()
            (proc / "net" / "dev").write_text("h1\nh2\n    lo: 0 0\n", encoding="ascii")
            cg.mkdir()
            for name, val in (("cpu.max", "100000 100000"), ("memory.max", str(2**31)), ("memory.swap.max", "0"), ("pids.max", "64")):
                (cg / name).write_text(val + "\n", encoding="ascii")
            checks = driver.preflight(lim, proc_root=str(proc), cgroup_root=str(cg),
                                      rootfs_probe=str(Path(d, "probe")), environ=driver.EXPECTED_ENV)
        for name in ("cgroup_cpu_max_one_cpu", "cgroup_memory_max", "cgroup_swap_max_zero", "cgroup_pids_max",
                     "network_loopback_only", "deterministic_env_vars", "child_check_available_and_clear"):
            self.assertTrue(checks[name]["ok"], name)
        self.assertFalse(checks["rootfs_readonly"]["ok"])  # the temp dir is writable

    def test_missing_children_file_fails_closed(self) -> None:
        lim = Limits(cpu_cap_s=5, reserve_s=1.0, check_interval_s=0.05)
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "self" / "task" / "1").mkdir(parents=True)
            checks = driver.preflight(lim, proc_root=d, cgroup_root=d, rootfs_probe=str(Path(d, "p")), environ={})
        self.assertFalse(checks["child_check_available_and_clear"]["ok"])
        self.assertFalse(checks["cgroup_cpu_max_one_cpu"]["ok"])


if __name__ == "__main__":
    unittest.main()
