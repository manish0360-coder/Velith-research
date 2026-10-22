from __future__ import annotations

import unittest

from egrid.testgate import run_gate

FS = "harness_tests.fixture_suites"


def ids(cls: str, *names: str) -> list[str]:
    return [f"{FS}.{cls}.{n}" for n in names]


class TestGate(unittest.TestCase):
    def test_clean_suite_accepted(self) -> None:
        r = run_gate([f"{FS}.Clean"], ids("Clean", "test_a", "test_b"))
        self.assertTrue(r.ok, r.problems)
        self.assertEqual(r.tests_run, 2)

    def test_skip_rejected(self) -> None:
        r = run_gate([f"{FS}.WithSkip"], ids("WithSkip", "test_ok", "test_skipped"))
        self.assertFalse(r.ok)
        self.assertTrue(any(p.startswith("skipped:") for p in r.problems))

    def test_expected_failure_rejected(self) -> None:
        r = run_gate([f"{FS}.WithExpectedFailure"], ids("WithExpectedFailure", "test_xfail"))
        self.assertFalse(r.ok)
        self.assertTrue(any(p.startswith("expected failure:") for p in r.problems))

    def test_unexpected_success_rejected(self) -> None:
        r = run_gate([f"{FS}.WithUnexpectedSuccess"], ids("WithUnexpectedSuccess", "test_xpass"))
        self.assertFalse(r.ok)
        self.assertTrue(any(p.startswith("unexpected success:") for p in r.problems))

    def test_failure_and_error_rejected(self) -> None:
        r = run_gate([f"{FS}.WithFailure", f"{FS}.WithError"], ids("WithFailure", "test_fails") + ids("WithError", "test_errors"))
        self.assertFalse(r.ok)
        self.assertTrue(any(p.startswith("failure:") for p in r.problems))
        self.assertTrue(any(p.startswith("error:") for p in r.problems))

    def test_absent_required_test_rejected(self) -> None:
        r = run_gate([f"{FS}.Clean"], ids("Clean", "test_a", "test_b", "test_missing"))
        self.assertFalse(r.ok)
        self.assertIn(f"absent: {FS}.Clean.test_missing", r.problems)

    def test_extra_collected_test_rejected(self) -> None:
        r = run_gate([f"{FS}.Clean"], ids("Clean", "test_a"))
        self.assertFalse(r.ok)
        self.assertIn(f"extra (not in required list): {FS}.Clean.test_b", r.problems)

    def test_load_error_rejected(self) -> None:
        r = run_gate([f"{FS}.DoesNotExist"], [])
        self.assertFalse(r.ok)


if __name__ == "__main__":
    unittest.main()
