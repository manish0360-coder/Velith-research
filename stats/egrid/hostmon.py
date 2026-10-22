"""EPG-14 M-H0 host-side monitor and wrapper records (runs on the WSL host, never in the stage).

Invoked by ``run_stage.sh`` as ``python3 -I hostmon.py <command>``. Standard library only.

Commands
  verify-config  check ``docker inspect`` of the created (not yet started) container against the
                 required isolation and limits; writes config_check.json; exit 1 on any mismatch
  monitor        poll the Docker Engine API for the container's AGGREGATE cgroup CPU usage
                 (``/containers/{id}/stats?one-shot=true`` -> cpu_stats.cpu_usage.total_usage, which
                 counts every process in the container) and its process list (``/containers/{id}/top``);
                 SIGKILL the container on: CPU >= cap (cpu_budget), more than one process
                 (child_process), wall-clock limit (wall_limit), or repeated monitor faults
                 (monitor_fault, fail closed); writes monitor.json
  finalize       assemble wrapper_status.json from the recorded evidence
  classify       run egrid.classify on the wrapper and stage records

The wrapper's records live outside the directory mounted into the stage container, so the stage
cannot alter them. This module is outside the ``egrid`` package and is not subject to the in-stage
import policy; it needs a Unix-socket Docker endpoint.
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import platform
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from egrid.driver import EXPECTED_ENV, atomic_write, canonical_json, sha256_file  # noqa: E402

WRAPPER_SCHEMA = "egrid.wrapper_status.v1"
CODE_GLOBS = ("egrid/*.py", "harness_tests/*.py", "harness_tests/*.txt", "harness_tests/*.sh", "run_stage.sh", "hostmon.py")
MAX_FAULTS = 3


# --------------------------------------------------------------------------- Docker Engine API


class EngineError(RuntimeError):
    pass


class _UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, path: str, timeout: float) -> None:
        super().__init__("localhost", timeout=timeout)
        self._path = path

    def connect(self) -> None:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect(self._path)
        self.sock = sock


class Engine:
    def __init__(self, socket_path: str, timeout: float = 2.0) -> None:
        self.socket_path = socket_path
        self.timeout = timeout

    def request(self, method: str, path: str) -> tuple[int, bytes]:
        conn = _UnixHTTPConnection(self.socket_path, self.timeout)
        try:
            conn.request(method, path, headers={"Host": "docker"})
            resp = conn.getresponse()
            return resp.status, resp.read()
        finally:
            conn.close()

    def get_json(self, path: str) -> Any:
        status, body = self.request("GET", path)
        if status != 200:
            raise EngineError(f"GET {path} -> HTTP {status}")
        return json.loads(body)

    def running(self, cid: str) -> bool:
        return bool(self.get_json(f"/containers/{cid}/json")["State"]["Running"])

    def cpu_ns(self, cid: str) -> int:
        data = self.get_json(f"/containers/{cid}/stats?stream=false&one-shot=true")
        return int(data["cpu_stats"]["cpu_usage"]["total_usage"])

    def processes(self, cid: str) -> list[Any]:
        return list(self.get_json(f"/containers/{cid}/top").get("Processes") or [])

    def kill(self, cid: str) -> int:
        status, _ = self.request("POST", f"/containers/{cid}/kill?signal=KILL")
        return status


def docker_socket() -> str:
    host = os.environ.get("DOCKER_HOST") or subprocess.run(
        ["docker", "context", "inspect", "--format", "{{.Endpoints.docker.Host}}"],
        capture_output=True, text=True, check=True, timeout=20,
    ).stdout.strip()
    if not host.startswith("unix://"):
        raise SystemExit(f"hostmon: unsupported Docker endpoint {host!r}; a unix:// socket is required")
    return host[len("unix://"):]


# --------------------------------------------------------------------------- monitor


def decide(
    *, cpu_ns: int | None, n_procs: int | None, elapsed_s: float, faults: int,
    cap_s: float, proc_check: bool, wall_s: float, max_faults: int = MAX_FAULTS,
) -> str | None:
    """Termination decision for one poll; None means keep running."""
    if cpu_ns is not None and cpu_ns >= int(round(cap_s * 1_000_000_000)):
        return "cpu_budget"
    if proc_check and n_procs is not None and n_procs > 1:
        return "child_process"
    if elapsed_s >= wall_s:
        return "wall_limit"
    if faults >= max_faults:
        return "monitor_fault"
    return None


def monitor(
    engine: Engine, cid: str, *, cap_s: float, poll_s: float, wall_s: float, proc_check: bool,
    clock: Callable[[], float] = time.monotonic, sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    rec: dict[str, Any] = {
        "cpu_source": "docker-engine-api:/containers/{id}/stats one-shot cpu_stats.cpu_usage.total_usage (cgroup aggregate)",
        "process_source": "docker-engine-api:/containers/{id}/top" if proc_check else None,
        "cap_s": cap_s, "poll_s": poll_s, "wall_s": wall_s, "proc_check": proc_check,
        "samples": 0, "last_cpu_s": None, "max_poll_gap_s": 0.0, "faults_total": 0,
        "terminated_by": None, "processes": None, "kill_http_status": None, "kill_error": None, "end": "exited",
    }
    t0 = clock()
    prev: float | None = None
    faults = 0
    last_ns: int | None = None
    while True:
        t = clock()
        if prev is not None:
            rec["max_poll_gap_s"] = round(max(rec["max_poll_gap_s"], t - prev), 6)
        prev = t
        cpu_ns: int | None = None
        procs: list[Any] | None = None
        try:
            if not engine.running(cid):
                break
            cpu_ns = engine.cpu_ns(cid)
            if proc_check:
                procs = engine.processes(cid)
            faults = 0
        except Exception:  # noqa: BLE001 - classify as a fault unless the container has exited
            try:
                if not engine.running(cid):
                    break
            except Exception:  # noqa: BLE001
                pass
            faults += 1
            rec["faults_total"] += 1
            cpu_ns, procs = None, None
        if cpu_ns is not None:
            last_ns = cpu_ns if last_ns is None else max(last_ns, cpu_ns)
            rec["last_cpu_s"] = round(last_ns / 1e9, 6)
            rec["samples"] += 1
        reason = decide(
            cpu_ns=cpu_ns, n_procs=None if procs is None else len(procs), elapsed_s=clock() - t0,
            faults=faults, cap_s=cap_s, proc_check=proc_check, wall_s=wall_s,
        )
        if reason is not None:
            rec["terminated_by"] = reason
            rec["end"] = "killed"
            if reason == "child_process":
                rec["processes"] = procs
            try:
                rec["kill_http_status"] = engine.kill(cid)
            except Exception as exc:  # noqa: BLE001
                rec["kill_error"] = f"{type(exc).__name__}: {exc}"
            break
        sleep(max(0.0, poll_s - (clock() - t)))
    rec["elapsed_s"] = round(clock() - t0, 6)
    return rec


# --------------------------------------------------------------------------- config check


def verify_config(info: dict[str, Any], *, image_id: str, cap_s: int, memory: int, code_root: str, stage_dir: str) -> list[str]:
    hc, cfg = info.get("HostConfig") or {}, info.get("Config") or {}
    problems: list[str] = []

    def expect(name: str, observed: Any, wanted: Any) -> None:
        if observed != wanted:
            problems.append(f"{name}: observed {observed!r}, required {wanted!r}")

    expect("Image", info.get("Image"), image_id)
    expect("Config.Entrypoint (python must be PID 1)", cfg.get("Entrypoint") or None, None)
    expect("HostConfig.Init", bool(hc.get("Init")), False)
    expect("Config.Cmd[0]", (cfg.get("Cmd") or [None])[0], "python")
    expect("HostConfig.NetworkMode", hc.get("NetworkMode"), "none")
    expect("HostConfig.NanoCpus", hc.get("NanoCpus"), 1_000_000_000)
    expect("HostConfig.Memory", hc.get("Memory"), memory)
    expect("HostConfig.MemorySwap", hc.get("MemorySwap"), memory)
    expect("HostConfig.PidsLimit", hc.get("PidsLimit"), 64)
    expect("HostConfig.ReadonlyRootfs", hc.get("ReadonlyRootfs"), True)
    expect("HostConfig.Privileged", bool(hc.get("Privileged")), False)
    expect("HostConfig.CapDrop has ALL", "ALL" in [str(c).upper() for c in hc.get("CapDrop") or []], True)
    expect("HostConfig.CapAdd", hc.get("CapAdd") or None, None)
    expect(
        "HostConfig.SecurityOpt no-new-privileges",
        any(s in ("no-new-privileges", "no-new-privileges:true", "no-new-privileges=true") for s in hc.get("SecurityOpt") or []),
        True,
    )
    expect("HostConfig.Ulimits", hc.get("Ulimits"), [{"Name": "cpu", "Soft": cap_s, "Hard": cap_s}])
    expect("HostConfig.Tmpfs", hc.get("Tmpfs"), {"/tmp": "rw,size=64m"})
    expect("HostConfig.Binds", sorted(hc.get("Binds") or []), sorted([f"{code_root}:/egrid:ro", f"{stage_dir}:/out"]))
    expect("Config.User", cfg.get("User"), "1000:1000")
    env = set(cfg.get("Env") or [])
    missing = sorted(f"{k}={v}" for k, v in EXPECTED_ENV.items() if f"{k}={v}" not in env)
    expect("Config.Env deterministic variables missing", missing, [])
    return problems


# --------------------------------------------------------------------------- records


def _load(path: str | None) -> Any:
    if not path:
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def code_hashes(root: Path) -> dict[str, str]:
    files = sorted({p for pattern in CODE_GLOBS for p in root.glob(pattern) if p.is_file()})
    return {p.relative_to(root).as_posix(): sha256_file(p) for p in files}


def finalize(args: argparse.Namespace) -> dict[str, Any]:
    problems = list(json.loads(args.preflight_problems))
    config = _load(args.config_check)
    if args.config_check and (not isinstance(config, dict) or config.get("ok") is not True):
        problems.append("container configuration check failed or missing")
    final = _load(args.final_inspect)
    container: dict[str, Any] = {}
    if isinstance(final, list) and final:
        st = final[0].get("State") or {}
        container = {
            "exit_code": st.get("ExitCode"), "oom_killed": st.get("OOMKilled"), "error": st.get("Error"),
            "status": st.get("Status"), "started_at": st.get("StartedAt"), "finished_at": st.get("FinishedAt"),
            "image": final[0].get("Image"),
        }
        if container["image"] != args.image_id:
            problems.append(f"executed image {container['image']!r} != pinned {args.image_id!r}")
    return {
        "schema": WRAPPER_SCHEMA,
        "stage": args.stage,
        "run_id": args.run_id,
        "image_id": args.image_id,
        "preflight": {"ok": not problems, "problems": problems},
        "config_check": config,
        "monitor": _load(args.monitor),
        "monitor_exit_code": args.monitor_exit_code,
        "container": container,
        "limits": json.loads(args.limits),
        "test_settings": json.loads(args.test_settings),
        "code_sha256": code_hashes(Path(args.code_root)),
        "host": {"python": platform.python_version(), "platform": platform.platform()},
    }


# --------------------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["classify"]:  # pass the remaining options straight to egrid.classify
        from egrid.classify import main as classify_main  # noqa: PLC0415

        return classify_main(argv[1:])
    ap = argparse.ArgumentParser(prog="hostmon.py")
    sub = ap.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("verify-config")
    v.add_argument("--inspect", required=True)
    v.add_argument("--image-id", required=True)
    v.add_argument("--cap-s", type=int, required=True)
    v.add_argument("--memory", type=int, required=True)
    v.add_argument("--code-root", required=True)
    v.add_argument("--stage-dir", required=True)
    v.add_argument("--out", required=True)

    m = sub.add_parser("monitor")
    m.add_argument("--container", required=True)
    m.add_argument("--cap-s", type=float, required=True)
    m.add_argument("--poll-s", type=float, required=True)
    m.add_argument("--wall-s", type=float, required=True)
    m.add_argument("--proc-check", choices=("on", "off"), required=True)
    m.add_argument("--out", required=True)

    f = sub.add_parser("finalize")
    for name in ("--stage", "--run-id", "--image-id", "--code-root", "--out"):
        f.add_argument(name, required=True)
    f.add_argument("--preflight-problems", default="[]")
    f.add_argument("--config-check")
    f.add_argument("--monitor")
    f.add_argument("--monitor-exit-code", type=int)
    f.add_argument("--final-inspect")
    f.add_argument("--limits", default="{}")
    f.add_argument("--test-settings", default="{}")

    args = ap.parse_args(argv)
    if args.cmd == "verify-config":
        info = _load(args.inspect)
        info = info[0] if isinstance(info, list) and info else {}
        problems = verify_config(info, image_id=args.image_id, cap_s=args.cap_s, memory=args.memory,
                                 code_root=args.code_root, stage_dir=args.stage_dir)
        atomic_write(args.out, canonical_json({"ok": not problems, "problems": problems}))
        for p in problems:
            print(f"config mismatch: {p}", file=sys.stderr)
        return 0 if not problems else 1
    if args.cmd == "monitor":
        rec = monitor(Engine(docker_socket()), args.container, cap_s=args.cap_s, poll_s=args.poll_s,
                      wall_s=args.wall_s, proc_check=args.proc_check == "on")
        atomic_write(args.out, canonical_json(rec))
        return 0
    if args.cmd == "finalize":
        atomic_write(args.out, canonical_json(finalize(args)))
        return 0
    raise AssertionError(f"unhandled command {args.cmd!r}")


if __name__ == "__main__":
    sys.exit(main())
