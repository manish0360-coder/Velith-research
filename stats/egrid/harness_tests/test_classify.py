from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from egrid.classify import check_stage_dir, classify, classify_paths
from egrid.driver import canonical_json, exit_code_for, sha256_bytes

STAGE, RUN = "SYN-UNIT", "run-1"


def wrapper(**over: object) -> dict:
    w = {
        "schema": "egrid.wrapper_status.v1", "stage": STAGE, "run_id": RUN,
        "preflight": {"ok": True, "problems": []},
        "monitor": {"terminated_by": None, "cap_s": 5, "poll_s": 0.25, "max_poll_gap_s": 0.3, "last_cpu_s": 0.2},
        "monitor_exit_code": 0,
        "container": {"exit_code": 0, "oom_killed": False},
        "test_settings": {},
    }
    w.update(over)
    return w


def status(stop: str | None = None, artifacts: dict | None = None, required: list | None = None) -> dict:
    return {
        "schema": "egrid.stage_status.v1", "stage": STAGE, "run_id": RUN,
        "outcome": "PASS" if stop is None else "FAIL", "stop_code": stop, "reason": "r",
        "exit_code": exit_code_for(stop), "artifacts": artifacts or {}, "required_artifacts": required or [],
    }


COMPLETE = {"state": "COMPLETE"}


class TestRules(unittest.TestCase):
    def check(self, w: dict, s: dict | None, report: dict, outcome: str, stop: str | None, source: str | None = None) -> dict:
        r = classify(w, s, None if s is not None else "missing", report)
        self.assertEqual((r["outcome"], r["stop_code"]), (outcome, stop), r["reason"])
        if source:
            self.assertEqual(r["stop_source"], source)
        return r

    def test_clean_pass(self) -> None:
        self.check(wrapper(), status(), COMPLETE, "PASS", None, "driver")

    def test_invalid_wrapper(self) -> None:
        self.check({"schema": "x"}, status(), COMPLETE, "FAIL", "UNCLASSIFIED")
        self.check(None, status(), COMPLETE, "FAIL", "UNCLASSIFIED")

    def test_preflight_failure(self) -> None:
        self.check(wrapper(preflight={"ok": False, "problems": ["img"]}), None, {"state": "NO_STATUS"}, "FAIL", "UNCLASSIFIED", "wrapper")

    def test_monitor_missing_or_failed(self) -> None:
        self.check(wrapper(monitor=None), status(), COMPLETE, "FAIL", "UNCLASSIFIED")
        self.check(wrapper(monitor_exit_code=1), status(), COMPLETE, "FAIL", "UNCLASSIFIED")

    def test_cpu_budget_overrides_driver_pass(self) -> None:
        w = wrapper(monitor={**wrapper()["monitor"], "terminated_by": "cpu_budget", "last_cpu_s": 5.1},
                    container={"exit_code": 137, "oom_killed": False})
        r = self.check(w, status(), COMPLETE, "FAIL", "STOP-8", "wrapper")
        self.assertEqual(r["stop_form"], "BACKSTOP")
        self.assertTrue(r["conflicts"])

    def test_child_process_backstop(self) -> None:
        w = wrapper(monitor={**wrapper()["monitor"], "terminated_by": "child_process"}, container={"exit_code": 137, "oom_killed": False})
        self.check(w, None, {"state": "NO_STATUS"}, "FAIL", "STOP-2", "wrapper")

    def test_wall_limit_and_monitor_fault_unclassified(self) -> None:
        for term in ("wall_limit", "monitor_fault"):
            w = wrapper(monitor={**wrapper()["monitor"], "terminated_by": term}, container={"exit_code": 137, "oom_killed": False})
            self.check(w, None, {"state": "NO_STATUS"}, "FAIL", "UNCLASSIFIED")

    def test_oom_never_stop8(self) -> None:
        w = wrapper(monitor={**wrapper()["monitor"], "last_cpu_s": 4.99}, container={"exit_code": 137, "oom_killed": True})
        self.check(w, None, {"state": "NO_STATUS"}, "FAIL", "UNCLASSIFIED")

    def test_exit_137_alone_is_unclassified(self) -> None:
        w = wrapper(monitor={**wrapper()["monitor"], "last_cpu_s": None}, container={"exit_code": 137, "oom_killed": False})
        self.check(w, None, {"state": "NO_STATUS"}, "FAIL", "UNCLASSIFIED")
        w = wrapper(monitor={**wrapper()["monitor"], "last_cpu_s": 2.0}, container={"exit_code": 137, "oom_killed": False})
        self.check(w, None, {"state": "NO_STATUS"}, "FAIL", "UNCLASSIFIED")

    def test_kernel_rlimit_attribution_requires_cpu_evidence(self) -> None:
        w = wrapper(monitor={**wrapper()["monitor"], "last_cpu_s": 4.8}, container={"exit_code": 137, "oom_killed": False})
        r = self.check(w, None, {"state": "NO_STATUS"}, "FAIL", "STOP-8", "kernel")
        self.assertEqual(r["stop_form"], "BACKSTOP")
        w = wrapper(monitor={**wrapper()["monitor"], "last_cpu_s": 4.8}, container={"exit_code": 143, "oom_killed": False})
        self.check(w, None, {"state": "NO_STATUS"}, "FAIL", "UNCLASSIFIED")  # SIGTERM is not an rlimit signal

    def test_nonzero_or_zero_exit_without_status(self) -> None:
        for code in (3, 0):
            self.check(wrapper(container={"exit_code": code, "oom_killed": False}), None, {"state": "NO_STATUS"}, "FAIL", "UNCLASSIFIED", "classifier")

    def test_exit_code_contradiction(self) -> None:
        self.check(wrapper(container={"exit_code": 0, "oom_killed": False}), status("STOP-8"), COMPLETE, "FAIL", "UNCLASSIFIED")
        self.check(wrapper(container={"exit_code": 1, "oom_killed": False}), status(), COMPLETE, "FAIL", "UNCLASSIFIED")

    def test_driver_stop8_in_process(self) -> None:
        r = self.check(wrapper(container={"exit_code": 72, "oom_killed": False}), status("STOP-8"), {"state": "INCOMPLETE"}, "FAIL", "STOP-8", "driver")
        self.assertEqual(r["stop_form"], "IN-PROCESS")

    def test_pass_with_incomplete_or_contradictory_artifacts(self) -> None:
        for state in ("INCOMPLETE", "CONTRADICTORY", "NO_STATUS", None):
            self.check(wrapper(), status(), {"state": state}, "FAIL", "UNCLASSIFIED")

    def test_test_settings_on_nonsynthetic_stage(self) -> None:
        w = wrapper(stage="V0", test_settings={"memory": 1})
        s = status()
        s["stage"] = "V0"
        self.check(w, s, COMPLETE, "FAIL", "UNCLASSIFIED")

    def test_invalid_status_fields(self) -> None:
        bad = status()
        bad["run_id"] = "other"
        self.check(wrapper(), bad, COMPLETE, "FAIL", "UNCLASSIFIED")
        bad = status("STOP-8")
        bad["stop_code"] = "STOP-11"
        self.check(wrapper(container={"exit_code": 72, "oom_killed": False}), bad, COMPLETE, "FAIL", "UNCLASSIFIED")


class TestStageDir(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.d = Path(self._td.name)
        (self.d / "r.txt").write_bytes(b"x")
        self.good = status(artifacts={"r.txt": sha256_bytes(b"x")}, required=["r.txt"])

    def tearDown(self) -> None:
        self._td.cleanup()

    def write_status(self, s: dict) -> None:
        (self.d / "stage_status.json").write_bytes(canonical_json(s))

    def test_complete(self) -> None:
        self.write_status(self.good)
        self.assertEqual(check_stage_dir(self.d, self.good)["state"], "COMPLETE")

    def test_hash_mismatch_contradictory(self) -> None:
        s = copy.deepcopy(self.good)
        s["artifacts"]["r.txt"] = sha256_bytes(b"y")
        self.assertEqual(check_stage_dir(self.d, s)["state"], "CONTRADICTORY")

    def test_undeclared_file_contradictory(self) -> None:
        (self.d / "extra.txt").write_bytes(b"e")
        self.assertEqual(check_stage_dir(self.d, self.good)["state"], "CONTRADICTORY")

    def test_temp_leftover_incomplete(self) -> None:
        (self.d / ".tmp-r2.txt.1").write_bytes(b"p")
        self.assertEqual(check_stage_dir(self.d, self.good)["state"], "INCOMPLETE")

    def test_required_not_declared_incomplete(self) -> None:
        s = copy.deepcopy(self.good)
        s["required_artifacts"] = ["r.txt", "never.txt"]
        self.assertEqual(check_stage_dir(self.d, s)["state"], "INCOMPLETE")

    def test_declared_missing_incomplete(self) -> None:
        s = copy.deepcopy(self.good)
        s["artifacts"]["gone.txt"] = sha256_bytes(b"g")
        self.assertEqual(check_stage_dir(self.d, s)["state"], "INCOMPLETE")

    def test_classify_paths_end_to_end(self) -> None:
        self.write_status(self.good)
        wpath = self.d.parent / f"{self.d.name}-wrapper.json"
        try:
            wpath.write_text(json.dumps(wrapper()), encoding="utf-8")
            self.assertEqual(classify_paths(str(wpath), str(self.d))["outcome"], "PASS")
            (self.d / "r.txt").write_bytes(b"tampered")
            self.assertEqual(classify_paths(str(wpath), str(self.d))["outcome"], "FAIL")
        finally:
            wpath.unlink()


class TestForgedFixtures(unittest.TestCase):
    """The criterion-6 synthetic writers, classified deterministically (no kill, no CPU race)."""

    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.d = Path(self._td.name)
        self.wpath = self.d / "wrapper_status.json"
        self.stage_dir = self.d / "stage"
        self.stage_dir.mkdir()

    def tearDown(self) -> None:
        self._td.cleanup()

    def run_case(self, writer: str, **wrapper_over: object) -> dict:
        from harness_tests import synth

        getattr(synth, writer)(self.stage_dir, STAGE, RUN)
        self.wpath.write_text(json.dumps(wrapper(**wrapper_over)), encoding="utf-8")
        return classify_paths(str(self.wpath), str(self.stage_dir))

    def test_forged_complete_overridden_by_wrapper_termination(self) -> None:
        o = self.run_case("write_forged_complete",
                          monitor={**wrapper()["monitor"], "terminated_by": "child_process"},
                          container={"exit_code": 137, "oom_killed": False})
        self.assertEqual((o["outcome"], o["stop_code"], o["stop_form"], o["stop_source"], o["rule"]),
                         ("FAIL", "STOP-2", "BACKSTOP", "wrapper", "R3"))
        self.assertEqual(o["artifact_state"], "COMPLETE")
        self.assertTrue(o["conflicts"])

    def test_forged_complete_overridden_by_kernel_cpu_kill(self) -> None:
        # The path observed on WSL for the old single-process SYN-RAW-FORGE.
        o = self.run_case("write_forged_complete",
                          monitor={**wrapper()["monitor"], "last_cpu_s": 4.770481, "max_poll_gap_s": 0.250554},
                          container={"exit_code": 137, "oom_killed": False})
        self.assertEqual((o["outcome"], o["stop_code"], o["stop_form"], o["stop_source"]), ("FAIL", "STOP-8", "BACKSTOP", "kernel"))
        self.assertTrue(o["conflicts"])

    def test_forged_partial_with_clean_exit_never_passes(self) -> None:
        o = self.run_case("write_forged_partial")
        self.assertEqual((o["outcome"], o["stop_code"], o["rule"], o["artifact_state"]), ("FAIL", "UNCLASSIFIED", "R10", "INCOMPLETE"))
        self.assertEqual(o["artifact_report"]["required_missing"], ["summary.json"])
        self.assertTrue(o["artifact_report"]["temp_files"])

    def test_forged_mismatch_with_clean_exit_never_passes(self) -> None:
        o = self.run_case("write_forged_mismatch")
        self.assertEqual((o["outcome"], o["stop_code"], o["rule"], o["artifact_state"]), ("FAIL", "UNCLASSIFIED", "R10", "CONTRADICTORY"))

    def test_documented_limit_self_consistent_forgery_with_clean_exit(self) -> None:
        # M_H0_HARNESS.md section 4 item 1: stage code is trusted; a fully self-consistent forged PASS
        # with a clean exit and no termination evidence is indistinguishable from a real PASS.
        o = self.run_case("write_forged_complete")
        self.assertEqual(o["outcome"], "PASS")


if __name__ == "__main__":
    unittest.main()
