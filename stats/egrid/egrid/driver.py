"""EPG-14 M-H0 stage driver (in-container side of the execution harness).

One stage = one Python process (contract §11.1). The driver:

* sets ``RLIMIT_AS`` (2 GiB) and verifies it, then runs a preflight that checks the runtime limits
  and isolation the host wrapper is supposed to have applied (RLIMIT_CPU = stage cap, cgroup CPU /
  memory / pids limits, loopback-only network, non-root, read-only root, deterministic env vars,
  availability of the child-process check);
* runs the stage function under an in-process monitor driven by ``ITIMER_PROF`` (process CPU time):
  at ``cap - reserve`` it raises STOP-8 (IN-PROCESS); any live or reaped child process raises STOP-2;
* writes artifacts atomically (temp file + fsync + ``os.replace`` + directory fsync);
* writes ``stage_status.json`` last, and exits with a code bound to the recorded STOP code.

The driver is defence in depth only. Aggregate CPU enforcement and termination evidence belong to
the host wrapper (``run_stage.sh`` / ``hostmon.py``), whose evidence overrides this status
(``egrid.classify``). No statistical computation lives here.
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import platform
import resource
import signal
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping

STATUS_SCHEMA = "egrid.stage_status.v1"
STATUS_FILE = "stage_status.json"
TMP_PREFIX = ".tmp-"
TWO_GIB = 2 * 1024**3
PIDS_MAX = 64
CPU_MAX_ONE_CPU = "100000 100000"
UNCLASSIFIED = "UNCLASSIFIED"
STOP_CODES = tuple(f"STOP-{i}" for i in range(1, 10))
EXPECTED_ENV = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONDONTWRITEBYTECODE": "1",
}


def exit_code_for(stop_code: str | None) -> int:
    """Process exit code bound to a recorded outcome: 0 PASS, 64+n STOP-n, 80 UNCLASSIFIED."""
    if stop_code is None:
        return 0
    if stop_code == UNCLASSIFIED:
        return 80
    if stop_code in STOP_CODES:
        return 64 + int(stop_code.split("-")[1])
    raise ValueError(f"unknown stop code {stop_code!r}")


class StageTermination(BaseException):
    """Base of driver-recognised terminations (carries the recorded code and reason).

    Derives from BaseException so that a stage's ``except Exception`` cannot swallow it; the
    context also latches the first termination so a swallowed one still determines the outcome.
    """

    def __init__(self, code: str, reason: str) -> None:
        super().__init__(f"{code}: {reason}")
        self.code = code
        self.reason = reason


class StopCondition(StageTermination):
    """A contract STOP (STOP-1 .. STOP-9) raised by the driver or a stage."""

    def __init__(self, code: str, reason: str) -> None:
        if code not in STOP_CODES:
            raise ValueError(f"invalid STOP code {code!r}")
        super().__init__(code, reason)


class MonitorFault(StageTermination):
    """The in-process monitor itself failed; fail closed as UNCLASSIFIED (never PASS)."""

    def __init__(self, reason: str) -> None:
        super().__init__(UNCLASSIFIED, reason)


@dataclass(frozen=True)
class Limits:
    cpu_cap_s: int
    reserve_s: float
    check_interval_s: float
    memory_max: int = TWO_GIB
    as_limit: int = TWO_GIB
    pids_max: int = PIDS_MAX

    def __post_init__(self) -> None:
        if self.cpu_cap_s <= 0 or not (0 < self.reserve_s < self.cpu_cap_s):
            raise ValueError("require cpu_cap_s > 0 and 0 < reserve_s < cpu_cap_s")
        if not (0 < self.check_interval_s < self.reserve_s):
            raise ValueError("require 0 < check_interval_s < reserve_s")


# --------------------------------------------------------------------------- measurements


def process_cpu_s() -> float:
    ru = resource.getrusage(resource.RUSAGE_SELF)
    return ru.ru_utime + ru.ru_stime


def children_cpu_s() -> float:
    ru = resource.getrusage(resource.RUSAGE_CHILDREN)
    return ru.ru_utime + ru.ru_stime


def live_children(proc_root: str = "/proc") -> list[int]:
    """PIDs of this process's children (live or zombie), from /proc/self/task/*/children.

    A thread can exit between listing and reading; its entry is skipped (its children are
    reparented within the thread group and seen at the next check). If no task's children file
    can be read at all, the check is unavailable and raises OSError (fail closed).
    """
    task_dir = os.path.join(proc_root, "self", "task")
    kids: list[int] = []
    readable = 0
    for tid in os.listdir(task_dir):
        try:
            with open(os.path.join(task_dir, tid, "children"), encoding="ascii") as fh:
                kids.extend(int(tok) for tok in fh.read().split())
            readable += 1
        except (FileNotFoundError, ProcessLookupError):
            continue
    if readable == 0:
        raise FileNotFoundError(f"no readable children file under {task_dir}")
    return sorted(kids)


def check_budget(
    limits: Limits,
    cpu_fn: Callable[[], float] = process_cpu_s,
    children_fn: Callable[[], list[int]] = live_children,
    child_cpu_fn: Callable[[], float] = children_cpu_s,
) -> None:
    """Raise STOP-2 on any child process, STOP-8 when CPU reaches cap - reserve."""
    kids = children_fn()
    child_cpu = child_cpu_fn()
    if kids or child_cpu > 0.0:
        raise StopCondition("STOP-2", f"child process detected: live={kids} reaped_cpu_s={child_cpu:.6f}")
    used = cpu_fn()
    if used >= limits.cpu_cap_s - limits.reserve_s:
        raise StopCondition(
            "STOP-8",
            f"IN-PROCESS: cpu {used:.3f}s >= cap {limits.cpu_cap_s}s - reserve {limits.reserve_s}s",
        )


# --------------------------------------------------------------------------- atomic output


def canonical_json(obj: object) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | os.PathLike[str]) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def atomic_write(path: str | os.PathLike[str], payload: bytes) -> None:
    """Write ``payload`` to ``path`` so that ``path`` is either absent or complete."""
    final = Path(path)
    tmp = final.with_name(f"{TMP_PREFIX}{final.name}.{os.getpid()}")
    fd = -1
    try:
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        view = memoryview(payload)
        while view:
            view = view[os.write(fd, view):]
        os.fsync(fd)
        os.close(fd)
        fd = -1
        os.replace(tmp, final)
    except BaseException:
        if fd >= 0:
            os.close(fd)
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise
    dfd = os.open(final.parent, os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)


# --------------------------------------------------------------------------- preflight


def _read(path: str) -> str | None:
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return None


def _interfaces(proc_root: str) -> list[str] | None:
    raw = _read(os.path.join(proc_root, "net", "dev"))
    if raw is None:
        return None
    return sorted(ln.split(":", 1)[0].strip() for ln in raw.splitlines()[2:] if ":" in ln)


def _rootfs_readonly(probe: str) -> str:
    try:
        with open(probe, "w", encoding="utf-8") as fh:
            fh.write("x")
        os.remove(probe)
        return "WRITABLE"
    except OSError as exc:
        return f"NOT_WRITABLE({errno.errorcode.get(exc.errno or 0, exc.errno)})"


def preflight(
    limits: Limits,
    *,
    proc_root: str = "/proc",
    cgroup_root: str = "/sys/fs/cgroup",
    rootfs_probe: str = "/usr/.egrid_rw_probe",
    environ: Mapping[str, str] = os.environ,
) -> dict[str, dict[str, object]]:
    """Observe runtime limits and isolation. Returns {check: {"ok": bool, "observed": value}}."""

    def chk(ok: bool, observed: object) -> dict[str, object]:
        return {"ok": bool(ok), "observed": observed}

    cg = {k: _read(os.path.join(cgroup_root, k)) for k in ("cpu.max", "memory.max", "memory.swap.max", "pids.max")}
    rl_as = list(resource.getrlimit(resource.RLIMIT_AS))
    rl_cpu = list(resource.getrlimit(resource.RLIMIT_CPU))
    ifs = _interfaces(proc_root)
    env = {k: environ.get(k) for k in EXPECTED_ENV}
    try:
        kids: object = live_children(proc_root)
        child_check_ok = True
    except OSError as exc:
        kids = f"unavailable: {exc.__class__.__name__}"
        child_check_ok = False
    rootfs = _rootfs_readonly(rootfs_probe)
    return {
        "rlimit_as": chk(rl_as == [limits.as_limit, limits.as_limit], rl_as),
        "rlimit_cpu_equals_cap": chk(rl_cpu == [limits.cpu_cap_s, limits.cpu_cap_s], rl_cpu),
        "cgroup_cpu_max_one_cpu": chk(cg["cpu.max"] == CPU_MAX_ONE_CPU, cg["cpu.max"]),
        "cgroup_memory_max": chk(cg["memory.max"] == str(limits.memory_max), cg["memory.max"]),
        "cgroup_swap_max_zero": chk(cg["memory.swap.max"] == "0", cg["memory.swap.max"]),
        "cgroup_pids_max": chk(cg["pids.max"] == str(limits.pids_max), cg["pids.max"]),
        "network_loopback_only": chk(ifs == ["lo"], ifs),
        "non_root_user": chk(os.getuid() != 0, os.getuid()),
        "rootfs_readonly": chk(rootfs == "NOT_WRITABLE(EROFS)", rootfs),
        "deterministic_env_vars": chk(env == EXPECTED_ENV, env),
        "child_check_available_and_clear": chk(child_check_ok and kids == [], kids),
    }


# --------------------------------------------------------------------------- stage context


class StageContext:
    """Handle passed to a stage function: cooperative checkpoints and atomic artifacts."""

    def __init__(
        self, stage: str, run_id: str, out_dir: Path, limits: Limits,
        checker: Callable[[Limits], None] = check_budget,
    ) -> None:
        self.stage = stage
        self.run_id = run_id
        self.out_dir = out_dir
        self.limits = limits
        self._checker = checker
        self.latched: StageTermination | None = None
        self._artifacts: dict[str, str] = {}
        self._closed = False

    def checkpoint(self) -> None:
        """Cooperative check before each work unit (the ITIMER_PROF monitor also runs)."""
        self._guarded_check()

    def _guarded_check(self) -> None:
        if self.latched is not None:
            return
        try:
            self._checker(self.limits)
        except StopCondition as stop:
            self.latched = stop
            raise
        except Exception as exc:  # noqa: BLE001 - a broken monitor must not pass silently
            fault = MonitorFault(f"in-process monitor failed: {type(exc).__name__}: {exc}")
            self.latched = fault
            raise fault from exc

    def write_artifact(self, name: str, data: bytes | str | dict | list) -> str:
        if self._closed:
            raise RuntimeError("stage context closed; artifacts can no longer be written")
        if (
            not name
            or name != os.path.basename(name)
            or name in (".", "..", STATUS_FILE)
            or name.startswith(TMP_PREFIX)
        ):
            raise ValueError(f"invalid artifact name {name!r}")
        if name in self._artifacts:
            raise ValueError(f"artifact {name!r} already written")
        if isinstance(data, (dict, list)):
            payload = canonical_json(data)
        elif isinstance(data, str):
            payload = data.encode("utf-8")
        else:
            payload = bytes(data)
        atomic_write(self.out_dir / name, payload)
        digest = sha256_bytes(payload)
        self._artifacts[name] = digest
        return digest

    @property
    def artifacts(self) -> dict[str, str]:
        return dict(self._artifacts)

    def close(self) -> None:
        self._closed = True


# --------------------------------------------------------------------------- execution

StageFn = Callable[[StageContext], None]


def execute(ctx: StageContext, stage_fn: StageFn, required_artifacts: Iterable[str]) -> tuple[str | None, str]:
    """Run ``stage_fn`` and map its termination to (stop_code or None for PASS, reason).

    Precedence: a latched STOP (first STOP observed, even if the stage swallowed it) wins.
    """
    stop: str | None
    try:
        stage_fn(ctx)
        ctx._guarded_check()  # final child / budget check after the stage returns
        missing = sorted(set(required_artifacts) - set(ctx.artifacts))
        if missing:
            stop, reason = UNCLASSIFIED, f"required artifacts missing: {missing}"
        else:
            stop, reason = None, "stage returned; all required artifacts written"
    except StageTermination as exc:
        stop, reason = exc.code, exc.reason
    except AssertionError as exc:
        stop, reason = "STOP-2", f"assertion: {exc!r}"
    except BaseException as exc:  # MemoryError, SystemExit, KeyboardInterrupt, any Exception
        stop, reason = UNCLASSIFIED, f"{type(exc).__name__}: {exc}"
    if ctx.latched is not None and stop != ctx.latched.code:
        reason = f"latched {ctx.latched.code} ({ctx.latched.reason}) overrides: {stop} {reason}"
        stop = ctx.latched.code
    return stop, reason


def _install_monitor(ctx: StageContext) -> None:
    def handler(signum: int, frame: object) -> None:
        ctx._guarded_check()

    signal.signal(signal.SIGPROF, handler)
    interval = ctx.limits.check_interval_s
    signal.setitimer(signal.ITIMER_PROF, interval, interval)


def _remove_monitor() -> None:
    signal.setitimer(signal.ITIMER_PROF, 0.0, 0.0)
    signal.signal(signal.SIGPROF, signal.SIG_IGN)  # also drops a tripped-but-unhandled SIGPROF


def _disarm() -> StageTermination | None:
    """Remove the monitor even if it fires during removal.

    The handler raises at most once (the first termination is latched and later calls return),
    so this loop terminates; a termination raised while disarming is returned, not propagated.
    """
    caught: StageTermination | None = None
    while True:
        try:
            _remove_monitor()
            return caught
        except StageTermination as exc:
            caught = exc


def build_status(
    ctx: StageContext,
    stop: str | None,
    reason: str,
    preflight_checks: Mapping[str, object],
    required_artifacts: Iterable[str],
) -> dict[str, object]:
    return {
        "schema": STATUS_SCHEMA,
        "stage": ctx.stage,
        "run_id": ctx.run_id,
        "outcome": "PASS" if stop is None else "FAIL",
        "stop_code": stop,
        "stop_form": "IN-PROCESS" if stop == "STOP-8" else None,
        "reason": reason,
        "exit_code": exit_code_for(stop),
        "cpu_self_s": round(process_cpu_s(), 6),
        "cpu_children_s": round(children_cpu_s(), 6),
        "limits": asdict(ctx.limits),
        "preflight": dict(preflight_checks),
        "artifacts": ctx.artifacts,
        "required_artifacts": sorted(set(required_artifacts)),
        "python": platform.python_version(),
    }


def run_stage(
    stage: str,
    stage_fn: StageFn,
    *,
    run_id: str,
    out_dir: str | os.PathLike[str],
    limits: Limits,
    required_artifacts: Iterable[str] = (),
) -> int:
    """Production entry point for one stage process. Returns the process exit code."""
    out = Path(out_dir)
    required = tuple(required_artifacts)
    ctx = StageContext(stage, run_id, out, limits)
    if any(out.iterdir()):
        return exit_code_for(UNCLASSIFIED)  # never write over an existing stage directory
    try:
        resource.setrlimit(resource.RLIMIT_AS, (limits.as_limit, limits.as_limit))
    except (ValueError, OSError):
        pass  # recorded as a failed preflight check below
    checks = preflight(limits)
    failed = sorted(name for name, c in checks.items() if not c["ok"])
    if failed:
        stop, reason = UNCLASSIFIED, f"preflight failed: {failed}"
    else:
        _install_monitor(ctx)
        try:
            stop, reason = execute(ctx, stage_fn, required)
            _disarm()
        except StageTermination as exc:  # the monitor's single raise landed outside execute's handlers
            stop, reason = exc.code, exc.reason
            _disarm()
        if ctx.latched is not None and stop != ctx.latched.code:
            stop, reason = ctx.latched.code, ctx.latched.reason
    ctx.close()
    status = build_status(ctx, stop, reason, checks, required)
    atomic_write(out / STATUS_FILE, canonical_json(status))  # written last
    sys.stdout.flush()
    return int(status["exit_code"])
