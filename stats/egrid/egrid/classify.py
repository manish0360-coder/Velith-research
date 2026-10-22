"""EPG-14 M-H0 stage-outcome classifier.

Combines the host wrapper's record (``wrapper_status.json``: preflight, container inspection,
aggregate CPU / process monitor) with the driver's ``stage_status.json`` and an independent check
of the stage directory, and produces ``stage_outcome.json``.

Rules (first match wins; wrapper evidence overrides the driver):

R0  wrapper record missing or invalid ............................ FAIL UNCLASSIFIED
R1  wrapper preflight failed (no stage ran or config mismatch) ... FAIL UNCLASSIFIED
R2  monitor record missing or monitor exited non-zero ............ FAIL UNCLASSIFIED
R3  wrapper terminated the container:
      cpu_budget -> STOP-8 (BACKSTOP); child_process -> STOP-2 (BACKSTOP);
      wall_limit / monitor_fault -> UNCLASSIFIED
R4  container OOM-killed (docker State.OOMKilled) ................. FAIL UNCLASSIFIED (never STOP-8)
R5  exit status unknown .......................................... FAIL UNCLASSIFIED
R6  terminated by a signal (exit >= 128): STOP-8 (BACKSTOP, kernel RLIMIT_CPU) only if the signal
    is SIGKILL/SIGXCPU AND the last observed aggregate CPU is within the attribution tolerance of
    the cap; otherwise UNCLASSIFIED. Exit 137 alone never establishes a cause.
R7  no valid driver status (any exit code, including 0) .......... FAIL UNCLASSIFIED
R8  driver status inconsistent with the exit code or stage/run ... FAIL UNCLASSIFIED
R9  driver status FAIL ............................................ FAIL with the driver's STOP code
R10 driver status PASS: PASS only if the stage directory is COMPLETE (every declared artifact
    present with matching SHA-256, every required artifact declared, no temp or undeclared files)
    and no non-default test setting applies to a non-synthetic stage; otherwise FAIL UNCLASSIFIED.

The classifier never derives PASS from file existence alone.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping

from egrid.driver import (
    STATUS_FILE,
    STATUS_SCHEMA,
    STOP_CODES,
    TMP_PREFIX,
    UNCLASSIFIED,
    atomic_write,
    canonical_json,
    exit_code_for,
    sha256_file,
)

OUTCOME_SCHEMA = "egrid.stage_outcome.v1"
WRAPPER_SCHEMA = "egrid.wrapper_status.v1"
SIGKILL, SIGXCPU = 9, 24


def load_json(path: str | os.PathLike[str]) -> tuple[Any, str | None]:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh), None
    except FileNotFoundError:
        return None, "missing"
    except (OSError, ValueError) as exc:
        return None, f"unreadable: {type(exc).__name__}"


def validate_status(status: Any, stage: str, run_id: str) -> list[str]:
    if not isinstance(status, dict):
        return ["status is not an object"]
    problems = []
    if status.get("schema") != STATUS_SCHEMA:
        problems.append("schema mismatch")
    if status.get("stage") != stage:
        problems.append(f"stage mismatch: {status.get('stage')!r}")
    if status.get("run_id") != run_id:
        problems.append(f"run_id mismatch: {status.get('run_id')!r}")
    outcome, stop = status.get("outcome"), status.get("stop_code")
    if outcome == "PASS":
        if stop is not None:
            problems.append("PASS with a stop code")
    elif outcome == "FAIL":
        if stop not in STOP_CODES and stop != UNCLASSIFIED:
            problems.append(f"FAIL with invalid stop code {stop!r}")
    else:
        problems.append(f"invalid outcome {outcome!r}")
    artifacts = status.get("artifacts")
    if not isinstance(artifacts, dict) or not all(isinstance(v, str) for v in artifacts.values()):
        problems.append("artifacts not a name->sha256 map")
    if not isinstance(status.get("required_artifacts"), list):
        problems.append("required_artifacts not a list")
    if not problems:
        try:
            if status.get("exit_code") != exit_code_for(stop):
                problems.append("recorded exit_code inconsistent with stop code")
        except ValueError:
            problems.append("invalid stop code")
    return problems


def check_stage_dir(stage_dir: str | os.PathLike[str], status: Mapping[str, Any] | None) -> dict[str, Any]:
    """Independent artifact check: COMPLETE, INCOMPLETE, CONTRADICTORY or NO_STATUS."""
    root = Path(stage_dir)
    names = sorted(p.name for p in root.iterdir()) if root.is_dir() else []
    temps = [n for n in names if n.startswith(TMP_PREFIX)]
    report: dict[str, Any] = {"files": names, "temp_files": temps}
    if status is None:
        report["state"] = "NO_STATUS"
        return report
    declared = status.get("artifacts") or {}
    required = status.get("required_artifacts") or []
    missing = sorted(n for n in declared if not (root / n).is_file())
    mismatched = sorted(n for n, h in declared.items() if (root / n).is_file() and sha256_file(root / n) != h)
    undeclared = sorted(n for n in names if n not in declared and n != STATUS_FILE and n not in temps)
    required_missing = sorted(set(required) - set(declared))
    report.update(missing=missing, mismatched=mismatched, undeclared=undeclared, required_missing=required_missing)
    if mismatched or undeclared:
        report["state"] = "CONTRADICTORY"
    elif missing or required_missing or temps:
        report["state"] = "INCOMPLETE"
    else:
        report["state"] = "COMPLETE"
    return report


def _attribution_tolerance_s(monitor: Mapping[str, Any]) -> float:
    poll = float(monitor.get("poll_s") or 0.0)
    gap = float(monitor.get("max_poll_gap_s") or 0.0)
    return 2.0 * max(poll, gap) + 0.1


def classify(
    wrapper: Any,
    stage_status: Any,
    status_error: str | None,
    artifact_report: Mapping[str, Any],
) -> dict[str, Any]:
    stage = wrapper.get("stage") if isinstance(wrapper, dict) else None
    run_id = wrapper.get("run_id") if isinstance(wrapper, dict) else None
    out: dict[str, Any] = {
        "schema": OUTCOME_SCHEMA,
        "stage": stage,
        "run_id": run_id,
        "artifact_state": artifact_report.get("state"),
        "conflicts": [],
        "evidence": {},
    }

    def result(outcome: str, stop: str | None, form: str | None, source: str, rule: str, reason: str) -> dict[str, Any]:
        out.update(outcome=outcome, stop_code=stop, stop_form=form, stop_source=source, rule=rule, reason=reason)
        return out

    if not isinstance(wrapper, dict) or wrapper.get("schema") != WRAPPER_SCHEMA or not stage or not run_id:
        return result("FAIL", UNCLASSIFIED, None, "classifier", "R0", "wrapper status missing or invalid")

    container = wrapper.get("container") or {}
    monitor = wrapper.get("monitor")
    driver_claim = stage_status.get("outcome") if isinstance(stage_status, dict) else None
    out["evidence"] = {
        "exit_code": container.get("exit_code"),
        "oom_killed": container.get("oom_killed"),
        "terminated_by": (monitor or {}).get("terminated_by"),
        "last_cpu_s": (monitor or {}).get("last_cpu_s"),
        "driver_outcome": driver_claim,
        "driver_stop_code": stage_status.get("stop_code") if isinstance(stage_status, dict) else None,
        "status_error": status_error,
        "test_settings": wrapper.get("test_settings") or {},
    }
    preflight = wrapper.get("preflight") or {}
    if preflight.get("ok") is not True:
        return result("FAIL", UNCLASSIFIED, None, "wrapper", "R1", f"wrapper preflight failed: {preflight.get('problems')}")
    if not isinstance(monitor, dict) or wrapper.get("monitor_exit_code") != 0:
        return result("FAIL", UNCLASSIFIED, None, "wrapper", "R2", "monitor record missing or monitor failed")

    term = monitor.get("terminated_by")
    if term is not None:
        if driver_claim == "PASS":
            out["conflicts"].append("driver claimed PASS but the wrapper terminated the container")
        if term == "cpu_budget":
            return result("FAIL", "STOP-8", "BACKSTOP", "wrapper", "R3", "aggregate container CPU reached the stage cap")
        if term == "child_process":
            return result("FAIL", "STOP-2", "BACKSTOP", "wrapper", "R3", f"extra process observed: {monitor.get('processes')}")
        return result("FAIL", UNCLASSIFIED, None, "wrapper", "R3", f"wrapper terminated the container: {term}")

    if container.get("oom_killed") is True:
        if driver_claim == "PASS":
            out["conflicts"].append("driver claimed PASS but the container was OOM-killed")
        return result("FAIL", UNCLASSIFIED, None, "classifier", "R4", "container OOM-killed (cgroup memory limit)")

    exit_code = container.get("exit_code")
    if not isinstance(exit_code, int):
        return result("FAIL", UNCLASSIFIED, None, "classifier", "R5", "container exit status unknown")

    if exit_code >= 128:
        sig = exit_code - 128
        cap = float(monitor.get("cap_s") or 0.0)
        last = monitor.get("last_cpu_s")
        tol = _attribution_tolerance_s(monitor)
        out["evidence"]["attribution_tolerance_s"] = round(tol, 6)
        if driver_claim == "PASS":
            out["conflicts"].append(f"driver claimed PASS but the process died by signal {sig}")
        if sig in (SIGKILL, SIGXCPU) and isinstance(last, (int, float)) and cap > 0 and last >= cap - tol:
            return result(
                "FAIL", "STOP-8", "BACKSTOP", "kernel", "R6",
                f"signal {sig} with last observed aggregate CPU {last:.3f}s >= cap {cap}s - tolerance {tol:.3f}s",
            )
        return result("FAIL", UNCLASSIFIED, None, "classifier", "R6", f"terminated by signal {sig}; cause not established")

    if stage_status is None or status_error is not None:
        return result("FAIL", UNCLASSIFIED, None, "classifier", "R7", f"no valid driver status ({status_error}); exit {exit_code}")
    problems = validate_status(stage_status, stage, run_id)
    if problems:
        return result("FAIL", UNCLASSIFIED, None, "classifier", "R7", f"invalid driver status: {problems}")
    if stage_status["exit_code"] != exit_code:
        out["conflicts"].append(f"status exit_code {stage_status['exit_code']} != container exit {exit_code}")
        return result("FAIL", UNCLASSIFIED, None, "classifier", "R8", "driver status contradicts the exit code")

    if stage_status["outcome"] == "FAIL":
        stop = stage_status["stop_code"]
        return result("FAIL", stop, "IN-PROCESS" if stop == "STOP-8" else None, "driver", "R9", str(stage_status.get("reason")))

    if artifact_report.get("state") != "COMPLETE":
        return result("FAIL", UNCLASSIFIED, None, "classifier", "R10", f"PASS claimed but artifacts {artifact_report.get('state')}")
    if (wrapper.get("test_settings") or {}) and not stage.startswith("SYN-"):
        return result("FAIL", UNCLASSIFIED, None, "classifier", "R10", "non-default test settings on a non-synthetic stage")
    return result("PASS", None, None, "driver", "R10", "driver PASS confirmed by wrapper evidence and artifact check")


def classify_paths(wrapper_path: str, stage_dir: str) -> dict[str, Any]:
    wrapper, _ = load_json(wrapper_path)
    status, status_error = load_json(Path(stage_dir) / STATUS_FILE)
    report = check_stage_dir(stage_dir, status if status_error is None and isinstance(status, dict) else None)
    outcome = classify(wrapper, status if status_error is None else None, status_error, report)
    outcome["artifact_report"] = report
    return outcome


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--wrapper", required=True)
    ap.add_argument("--stage-dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    outcome = classify_paths(args.wrapper, args.stage_dir)
    atomic_write(args.out, canonical_json(outcome))
    print(json.dumps({k: outcome.get(k) for k in ("stage", "outcome", "stop_code", "stop_form", "stop_source", "rule", "reason")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
