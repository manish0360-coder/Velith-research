"""EPG-14 M-H0 acceptance evaluator (host side, standard library only).

    python3 -I stats/egrid/harness_tests/acceptance.py stats/egrid/runs <RUN_ID>

Reads the wrapper, stage and outcome records written by run_stage.sh for every synthetic case,
compares them with the expected classification, and prints one verdict per RD acceptance
criterion (1-8). Exit 0 only if every case matches. It reads records only; it runs nothing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional

BURN_TOLERANCE_S = 1.0  # documented: wrapper kill must land in [cap, cap + 1.0] s aggregate CPU


def load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


Check = Callable[[Dict[str, Any]], Optional[str]]


def preflight_all_ok(r: dict[str, Any]) -> str | None:
    checks = (r["status"] or {}).get("preflight") or {}
    bad = sorted(k for k, v in checks.items() if not v.get("ok"))
    return None if checks and not bad else f"in-container preflight not all ok: {bad or 'missing'}"


def burn_window(r: dict[str, Any]) -> str | None:
    mon = r["wrapper"].get("monitor") or {}
    last, cap = mon.get("last_cpu_s"), mon.get("cap_s")
    if mon.get("terminated_by") != "cpu_budget":
        return f"terminated_by={mon.get('terminated_by')!r}, expected 'cpu_budget'"
    if not isinstance(last, (int, float)) or not (cap <= last <= cap + BURN_TOLERANCE_S):
        return f"aggregate CPU at kill {last} outside [{cap}, {cap} + {BURN_TOLERANCE_S}]"
    return None


def oom_observed(r: dict[str, Any]) -> str | None:
    return None if (r["wrapper"].get("container") or {}).get("oom_killed") is True else "docker did not report OOMKilled=true"


def exit_code(code: int) -> Check:
    return lambda r: None if (r["wrapper"].get("container") or {}).get("exit_code") == code else f"exit code != {code}"


def artifacts(state: str) -> Check:
    return lambda r: None if r["outcome"].get("artifact_state") == state else f"artifact_state != {state}"


def conflict_recorded(r: dict[str, Any]) -> str | None:
    return None if r["outcome"].get("conflicts") else "driver/wrapper conflict not recorded"


def forged_pass_on_disk(r: dict[str, Any]) -> str | None:
    """Proves the fixture reached its intended condition: a PASS claim was present when classified."""
    return None if (r["status"] or {}).get("outcome") == "PASS" else "forged PASS status not present on disk"


def rule(name: str) -> Check:
    return lambda r: None if r["outcome"].get("rule") == name else f"rule {r['outcome'].get('rule')!r} != {name!r}"


def reason_starts(prefix: str) -> Check:
    return lambda r: None if str(r["outcome"].get("reason", "")).startswith(prefix) else f"reason does not start with {prefix!r}"


# case -> (criteria, outcome, stop_code, stop_form, allowed sources, extra checks, run-id suffix)
CASES: list[tuple[str, tuple[int, ...], str, str | None, str | None, set[str], list[Check], str]] = [
    ("SYN-PASS", (8,), "PASS", None, None, {"driver"}, [preflight_all_ok, artifacts("COMPLETE")], ""),
    ("SYN-TESTS", (7,), "PASS", None, None, {"driver"}, [artifacts("COMPLETE")], ""),
    ("SYN-TESTS-SKIP", (7,), "FAIL", "STOP-1", None, {"driver"}, [], ""),
    ("SYN-BURN-INPROC", (2, 6), "FAIL", "STOP-8", "IN-PROCESS", {"driver"}, [artifacts("INCOMPLETE")], ""),
    ("SYN-RAW-BURN2", (1,), "FAIL", "STOP-8", "BACKSTOP", {"wrapper"}, [burn_window], ""),
    ("SYN-RAW-BURN", (1,), "FAIL", "STOP-8", "BACKSTOP", {"wrapper", "kernel"}, [], ""),
    ("SYN-CHILD", (3,), "FAIL", "STOP-2", None, {"driver", "wrapper"}, [], ""),
    ("SYN-RAW-CHILD", (3,), "FAIL", "STOP-2", "BACKSTOP", {"wrapper"}, [], ""),
    ("SYN-RAISE", (4,), "FAIL", "UNCLASSIFIED", None, {"driver"}, [reason_starts("RuntimeError")], ""),
    ("SYN-RAW-EXIT3", (4,), "FAIL", "UNCLASSIFIED", None, {"classifier"}, [exit_code(3)], ""),
    ("SYN-OOM", (5,), "FAIL", "UNCLASSIFIED", None, {"classifier"}, [oom_observed], ""),
    ("SYN-ASLIMIT", (8,), "FAIL", "UNCLASSIFIED", None, {"driver"}, [reason_starts("MemoryError")], ""),
    ("SYN-RAW-FORGE-KILLED", (6,), "FAIL", "STOP-2", "BACKSTOP", {"wrapper"},
     [forged_pass_on_disk, conflict_recorded, rule("R3"), artifacts("COMPLETE")], ""),
    ("SYN-RAW-FORGE-PARTIAL", (6,), "FAIL", "UNCLASSIFIED", None, {"classifier"},
     [forged_pass_on_disk, rule("R10"), artifacts("INCOMPLETE")], ""),
    ("SYN-RAW-FORGE-MISMATCH", (6,), "FAIL", "UNCLASSIFIED", None, {"classifier"},
     [forged_pass_on_disk, rule("R10"), artifacts("CONTRADICTORY")], ""),
    ("SYN-PASS", (8,), "FAIL", "UNCLASSIFIED", None, {"wrapper"}, [reason_starts("wrapper preflight failed")], "-imgneg"),
]
CRITERIA = {
    1: "aggregate CPU budget -> STOP-8 (BACKSTOP), FAIL",
    2: "in-process stop -> STOP-8 (IN-PROCESS), FAIL",
    3: "unexpected child process -> STOP-2, FAIL",
    4: "non-zero exit without STOP code -> UNCLASSIFIED, FAIL",
    5: "OOM not labelled as CPU exhaustion",
    6: "interrupted / partial / forged artifacts never PASS",
    7: "required tests: no skip / xfail / xpass accepted",
    8: "image identity and resource limits checked at runtime",
}


def evaluate(runs: Path, run_id: str) -> int:
    crit_ok = {c: True for c in CRITERIA}
    all_ok = True
    print(f"{'case':34} {'outcome':7} {'stop':13} {'form':10} {'source':10} {'cpu_s':>6}  verdict")
    for stage, crits, outcome, stop, form, sources, extras, suffix in CASES:
        base = runs / f"{run_id}{suffix}" / stage
        rec = {
            "outcome": load(base / "outcome" / "stage_outcome.json"),
            "wrapper": load(base / "wrapper" / "wrapper_status.json"),
            "status": load(base / "stage" / "stage_status.json"),
        }
        problems: list[str] = []
        o = rec["outcome"]
        if not isinstance(o, dict) or not isinstance(rec["wrapper"], dict):
            problems.append("outcome or wrapper record missing")
            o = {}
        else:
            if (o.get("outcome"), o.get("stop_code")) != (outcome, stop):
                problems.append(f"got {o.get('outcome')}/{o.get('stop_code')}, expected {outcome}/{stop}")
            if form is not None and o.get("stop_form") != form:
                problems.append(f"stop_form {o.get('stop_form')!r} != {form!r}")
            if o.get("stop_source") not in sources:
                problems.append(f"stop_source {o.get('stop_source')!r} not in {sorted(sources)}")
            if not suffix and not (base / "wrapper" / "container_removed").exists():
                problems.append("container not removed after inspection")
            problems += [p for p in (chk(rec) for chk in extras) if p]
        cpu = ((rec["wrapper"] or {}).get("monitor") or {}).get("last_cpu_s") if isinstance(rec["wrapper"], dict) else None
        verdict = "OK" if not problems else "MISMATCH: " + "; ".join(problems)
        label = stage + suffix
        print(f"{label:34} {str(o.get('outcome')):7} {str(o.get('stop_code')):13} {str(o.get('stop_form')):10} "
              f"{str(o.get('stop_source')):10} {str(cpu):>6}  {verdict}")
        if problems:
            all_ok = False
            for c in crits:
                crit_ok[c] = False
    print()
    for c, text in CRITERIA.items():
        print(f"criterion {c}: {'MET' if crit_ok[c] else 'NOT MET'} - {text}")
    print(f"\nM-H0 ACCEPTANCE: {'ALL CRITERIA MET' if all_ok else 'FAILED'} (run_id {run_id})")
    return 0 if all_ok else 1


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(evaluate(Path(sys.argv[1]), sys.argv[2]))
