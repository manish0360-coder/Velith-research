"""EPG-14 required-test gate.

``unittest`` reports ``wasSuccessful() == True`` even when tests are skipped. The contract (STOP-1,
§10.3) treats a required test that is absent, skipped, errors, fails, or lacks its expected result
as a failure. This gate runs a fixed list of test IDs and accepts only an exact, clean run:

* the collected test IDs equal the required IDs (no absent, no extra, no duplicate, no load error);
* every required test ran; no failure, error, skip, expected failure or unexpected success.
"""

from __future__ import annotations

import io
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True)
class GateResult:
    ok: bool
    problems: tuple[str, ...]
    tests_run: int
    collected: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {"ok": self.ok, "problems": list(self.problems), "tests_run": self.tests_run, "collected": list(self.collected)}


def load_required(path: str | Path) -> list[str]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.lstrip().startswith("#")]


def _flatten(suite: unittest.TestSuite) -> list[unittest.TestCase]:
    out: list[unittest.TestCase] = []
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            out.extend(_flatten(item))
        else:
            out.append(item)
    return out


def run_gate(names: Iterable[str], required_ids: Sequence[str]) -> GateResult:
    """Load ``names`` (modules / classes), run them, and apply the strict acceptance rule."""
    problems: list[str] = []
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for name in names:
        try:
            suite.addTest(loader.loadTestsFromName(name))
        except Exception as exc:  # noqa: BLE001 - any load failure is a gate problem, never a pass
            problems.append(f"load error: {name}: {type(exc).__name__}: {exc}")
    problems.extend(f"load error: {e.strip().splitlines()[-1]}" for e in loader.errors)
    cases = _flatten(suite)
    ids = [c.id() for c in cases]
    failed_imports = [i for i in ids if i.startswith("unittest.loader._FailedTest")]
    problems.extend(f"failed import: {i}" for i in failed_imports)
    if len(set(ids)) != len(ids):
        problems.append("duplicate test ids collected")
    required = list(required_ids)
    if len(set(required)) != len(required):
        problems.append("duplicate ids in the required list")
    absent = sorted(set(required) - set(ids))
    extra = sorted(set(ids) - set(required))
    problems.extend(f"absent: {i}" for i in absent)
    problems.extend(f"extra (not in required list): {i}" for i in extra)

    result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    problems.extend(f"failure: {t.id()}" for t, _ in result.failures)
    problems.extend(f"error: {t.id()}" for t, _ in result.errors)
    problems.extend(f"skipped: {t.id()} ({why})" for t, why in result.skipped)
    problems.extend(f"expected failure: {t.id()}" for t, _ in result.expectedFailures)
    problems.extend(f"unexpected success: {t.id()}" for t in result.unexpectedSuccesses)
    if result.testsRun != len(required):
        problems.append(f"tests run {result.testsRun} != required {len(required)}")
    return GateResult(not problems, tuple(problems), result.testsRun, tuple(sorted(ids)))
