"""EPG-14 M-H0 synthetic stages (container entry point: ``python -m harness_tests.synth STAGE ...``).

Driver stages run through ``egrid.driver.run_stage`` (the production path). RAW stages bypass the
driver on purpose, to simulate a stage process that ignores its budget, spawns processes, dies
without a status, or forges records; only the host wrapper can classify those correctly.

This module deliberately forks and burns CPU. It lives outside the ``egrid`` package and is never
part of a validation stage.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Callable

from egrid.driver import Limits, StageContext, StopCondition, canonical_json, run_stage, sha256_bytes
from egrid.testgate import load_required, run_gate

HERE = Path(__file__).resolve().parent
REQUIRED_TESTS = HERE / "REQUIRED_TESTS.txt"
HARNESS_TEST_MODULES = (
    "harness_tests.test_driver",
    "harness_tests.test_classify",
    "harness_tests.test_testgate",
    "harness_tests.test_hostmon",
    "harness_tests.test_policy",
)
MIB = 1024 * 1024


def _burn() -> None:
    x = 0
    while True:
        x += 1


# --------------------------------------------------------------------------- driver stages


def syn_pass(ctx: StageContext) -> None:
    ctx.checkpoint()
    ctx.write_artifact("a.json", {"synthetic": True})
    ctx.write_artifact("b.txt", "ok\n")


def syn_burn_inproc(ctx: StageContext) -> None:
    ctx.write_artifact("started.json", {"phase": "started"})
    _burn()  # no cooperative checkpoint: the ITIMER_PROF monitor must stop this at cap - reserve


def syn_child(ctx: StageContext) -> None:
    pid = os.fork()
    if pid == 0:
        time.sleep(30)
        os._exit(0)
    _burn()  # the monitor must detect the child (STOP-2)


def syn_raise(ctx: StageContext) -> None:
    raise RuntimeError("synthetic ordinary failure")


def syn_oom(ctx: StageContext) -> None:
    hold = [b"\x01" * (16 * MIB) for _ in range(64)]  # 1 GiB touched; run with --test-memory 268435456
    ctx.write_artifact("unexpected_survival.txt", f"{len(hold)}\n")


def syn_aslimit(ctx: StageContext) -> None:
    hold = bytearray(3 * 1024 * MIB)  # exceeds RLIMIT_AS 2 GiB -> MemoryError
    ctx.write_artifact("unexpected_survival.txt", f"{len(hold)}\n")


def _gate_stage(ctx: StageContext, names: tuple[str, ...], required: list[str]) -> None:
    result = run_gate(names, required)
    ctx.write_artifact("test_gate.json", result.as_dict())
    if not result.ok:
        raise StopCondition("STOP-1", f"required-test gate rejected the run: {list(result.problems)}")


def syn_tests(ctx: StageContext) -> None:
    _gate_stage(ctx, HARNESS_TEST_MODULES, load_required(REQUIRED_TESTS))


def syn_tests_skip(ctx: StageContext) -> None:
    _gate_stage(ctx, ("harness_tests.fixture_suites.WithSkip",), ["harness_tests.fixture_suites.WithSkip.test_ok", "harness_tests.fixture_suites.WithSkip.test_skipped"])


DRIVER_STAGES: dict[str, tuple[Callable[[StageContext], None], tuple[str, ...]]] = {
    "SYN-PASS": (syn_pass, ("a.json", "b.txt")),
    "SYN-BURN-INPROC": (syn_burn_inproc, ("started.json", "result.json")),
    "SYN-CHILD": (syn_child, ()),
    "SYN-RAISE": (syn_raise, ()),
    "SYN-OOM": (syn_oom, ()),
    "SYN-ASLIMIT": (syn_aslimit, ()),
    "SYN-TESTS": (syn_tests, ("test_gate.json",)),
    "SYN-TESTS-SKIP": (syn_tests_skip, ("test_gate.json",)),
}


# --------------------------------------------------------------------------- raw stages (no driver)


def raw_burn(args: argparse.Namespace) -> int:
    _burn()
    return 0


def raw_burn2(args: argparse.Namespace) -> int:
    os.fork()  # parent and child both burn: aggregate CPU grows ~2x faster than either process's
    _burn()
    return 0


def raw_child(args: argparse.Namespace) -> int:
    if os.fork() == 0:
        time.sleep(30)
        os._exit(0)
    time.sleep(30)
    return 0


def raw_exit3(args: argparse.Namespace) -> int:
    os._exit(3)


def _forged_status(stage: str, run_id: str, artifacts: dict[str, str], required: list[str] | None = None) -> bytes:
    return canonical_json({
        "schema": "egrid.stage_status.v1", "stage": stage, "run_id": run_id,
        "outcome": "PASS", "stop_code": None, "stop_form": None, "reason": "forged by synthetic stage",
        "exit_code": 0, "artifacts": artifacts,
        "required_artifacts": sorted(artifacts) if required is None else sorted(required),
    })


# Forged-record writers are pure file writers (no kill, no CPU) so they are unit-testable.


def write_forged_complete(out: Path, stage: str, run_id: str) -> None:
    """A self-consistent forged PASS: only termination evidence can override it."""
    payload = b"partial\n"
    (out / "result.txt").write_bytes(payload)
    (out / "stage_status.json").write_bytes(_forged_status(stage, run_id, {"result.txt": sha256_bytes(payload)}))


def write_forged_partial(out: Path, stage: str, run_id: str) -> None:
    """A forged PASS over partial output: a required artifact never declared and an interrupted
    atomic write (temp file left behind)."""
    payload = b"partial\n"
    (out / "result.txt").write_bytes(payload)
    (out / ".tmp-summary.json.99").write_bytes(b'{"trunc')
    (out / "stage_status.json").write_bytes(
        _forged_status(stage, run_id, {"result.txt": sha256_bytes(payload)}, ["result.txt", "summary.json"])
    )


def write_forged_mismatch(out: Path, stage: str, run_id: str) -> None:
    """A forged PASS whose declared hash contradicts the artifact on disk."""
    (out / "result.txt").write_bytes(b"actual\n")
    (out / "stage_status.json").write_bytes(_forged_status(stage, run_id, {"result.txt": sha256_bytes(b"claimed\n")}))


def raw_forge_killed(args: argparse.Namespace) -> int:
    # Records are fully written BEFORE the fork, so the wrapper's process monitor (deterministic,
    # first poll after the fork, ~0 CPU used) terminates a stage whose forged PASS is on disk.
    # No CPU burn: a kernel RLIMIT_CPU kill cannot pre-empt the wrapper evidence.
    write_forged_complete(Path(args.out), args.stage, args.run_id)
    if os.fork() == 0:
        time.sleep(30)
        os._exit(0)
    time.sleep(30)
    return 0


def raw_forge_partial(args: argparse.Namespace) -> int:
    write_forged_partial(Path(args.out), args.stage, args.run_id)
    return 0


def raw_forge_mismatch(args: argparse.Namespace) -> int:
    write_forged_mismatch(Path(args.out), args.stage, args.run_id)
    return 0


RAW_STAGES: dict[str, Callable[[argparse.Namespace], int]] = {
    "SYN-RAW-BURN": raw_burn,
    "SYN-RAW-BURN2": raw_burn2,
    "SYN-RAW-CHILD": raw_child,
    "SYN-RAW-EXIT3": raw_exit3,
    "SYN-RAW-FORGE-KILLED": raw_forge_killed,
    "SYN-RAW-FORGE-PARTIAL": raw_forge_partial,
    "SYN-RAW-FORGE-MISMATCH": raw_forge_mismatch,
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="harness_tests.synth")
    ap.add_argument("stage")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cap-s", type=int, required=True)
    ap.add_argument("--reserve-s", type=float, required=True)
    ap.add_argument("--check-interval-s", type=float, required=True)
    ap.add_argument("--memory-max", type=int, required=True)
    args = ap.parse_args(argv)
    if args.stage in RAW_STAGES:
        return RAW_STAGES[args.stage](args)
    if args.stage not in DRIVER_STAGES:
        print(f"unknown synthetic stage {args.stage!r}", file=sys.stderr)
        return 2
    fn, required = DRIVER_STAGES[args.stage]
    limits = Limits(args.cap_s, args.reserve_s, args.check_interval_s, memory_max=args.memory_max)
    return run_stage(args.stage, fn, run_id=args.run_id, out_dir=args.out, limits=limits, required_artifacts=required)


if __name__ == "__main__":
    sys.exit(main())
