"""Deliberately defective unittest suites used to prove the required-test gate rejects them.

Loaded only by explicit name (test_testgate, SYN-TESTS-SKIP); the class names do not start with
``Test`` and the module is never listed in REQUIRED_TESTS.txt.
"""

from __future__ import annotations

import unittest


class Clean(unittest.TestCase):
    def test_a(self) -> None:
        self.assertTrue(True)

    def test_b(self) -> None:
        self.assertEqual(1 + 1, 2)


class WithSkip(unittest.TestCase):
    def test_ok(self) -> None:
        self.assertTrue(True)

    @unittest.skip("deliberate skip")
    def test_skipped(self) -> None:
        self.fail("never runs")


class WithExpectedFailure(unittest.TestCase):
    @unittest.expectedFailure
    def test_xfail(self) -> None:
        self.assertEqual(1, 2)


class WithUnexpectedSuccess(unittest.TestCase):
    @unittest.expectedFailure
    def test_xpass(self) -> None:
        self.assertEqual(1, 1)


class WithFailure(unittest.TestCase):
    def test_fails(self) -> None:
        self.assertEqual(1, 2)


class WithError(unittest.TestCase):
    def test_errors(self) -> None:
        raise RuntimeError("deliberate error")
