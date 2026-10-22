"""EPG-14 environment recorder (environment preparation only; not part of V0-V5).

Writes two artifacts describing the interpreter/container it runs in:

* ``--lock PATH``   deterministic environment lock (no timestamps). Its SHA-256 is what the
                    RD authorization record pins. Computed by the HOST after the run
                    (``sha256sum``), never typed by hand.
* ``--record PATH`` full JSON environment record: platform, packages, BLAS config, CPU,
                    memory, cgroup v2 limits, rlimits, deterministic env vars, uid, and the
                    isolation controls this process can observe.

Network check: lists interfaces from /proc/net/dev and attempts ONE TCP connect to
192.0.2.1:9 (RFC 5737 TEST-NET-1, documentation-only, never routed). Under
``docker --network none`` (or ``unshare -n``) the only interface is ``lo`` and the connect
fails immediately. The script makes no other network call. Standard library only, plus an
optional numpy import to record its version and BLAS configuration.

Exit code is always 0 if the artifacts were written; controls are REPORTED (PASS/FAIL/
UNOBSERVABLE), not enforced here. Enforcement belongs to the docker run flags and to the
future V0-V5 stage driver.
"""

from __future__ import annotations

import argparse
import errno
import importlib.metadata as md
import json
import os
import platform
import resource
import socket
import sys

SCHEMA = "egrid.env_record.v1"
LOCK_SCHEMA = "egrid.env_lock.v1"
DET_VARS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
            "NUMEXPR_NUM_THREADS", "PYTHONHASHSEED", "PYTHONDONTWRITEBYTECODE")
EXPECTED_ENV = {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
                "NUMEXPR_NUM_THREADS": "1", "PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1"}
TWO_GIB = 2 * 1024 ** 3
TEST_NET = ("192.0.2.1", 9)


def _read(path: str) -> str | None:
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return None


def packages() -> list[str]:
    seen = {}
    for dist in md.distributions():
        name = (dist.metadata.get("Name") or "").strip()
        if name:
            seen[name.lower()] = f"{name}=={dist.version}"
    return [seen[k] for k in sorted(seen)]


def numpy_info() -> dict[str, object]:
    try:
        import numpy  # noqa: PLC0415
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "error": type(exc).__name__}
    info: dict[str, object] = {"available": True, "version": numpy.__version__}
    try:
        cfg = numpy.show_config(mode="dicts")
        deps = cfg.get("Build Dependencies", {}) if isinstance(cfg, dict) else {}
        info["blas"] = {k: deps.get("blas", {}).get(k) for k in ("name", "version", "openblas configuration")}
        info["lapack"] = {k: deps.get("lapack", {}).get(k) for k in ("name", "version")}
    except Exception as exc:  # noqa: BLE001
        info["config_error"] = type(exc).__name__
    return info


def interfaces() -> list[str]:
    raw = _read("/proc/net/dev")
    if raw is None:
        return []
    return sorted(line.split(":", 1)[0].strip() for line in raw.splitlines()[2:] if ":" in line)


def testnet_connect() -> dict[str, object]:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2.0)
    try:
        s.connect(TEST_NET)
        return {"result": "CONNECTED", "errno": None}
    except OSError as exc:
        code = exc.errno
        return {"result": "FAILED", "errno": code, "errno_name": errno.errorcode.get(code, str(code))}
    finally:
        s.close()


def rlimits() -> dict[str, list[int]]:
    out = {}
    for name in ("RLIMIT_AS", "RLIMIT_CPU", "RLIMIT_DATA", "RLIMIT_NOFILE", "RLIMIT_NPROC"):
        if hasattr(resource, name):
            out[name] = list(resource.getrlimit(getattr(resource, name)))
    return out


def rootfs_readonly() -> str:
    probe = "/usr/.egrid_rw_probe"
    try:
        with open(probe, "w", encoding="utf-8") as fh:
            fh.write("x")
        os.remove(probe)
        return "WRITABLE"
    except OSError as exc:
        return f"NOT_WRITABLE({errno.errorcode.get(exc.errno, exc.errno)})"


def build(venue: str) -> tuple[dict[str, object], str]:
    ifs = interfaces()
    conn = testnet_connect()
    cg = {k: _read(f"/sys/fs/cgroup/{k}") for k in ("cpu.max", "memory.max", "memory.swap.max", "pids.max")}
    rl = rlimits()
    env = {k: os.environ.get(k) for k in DET_VARS}
    pk = packages()
    npi = numpy_info()
    image_id = os.environ.get("EGRID_IMAGE_ID")
    base_digest = os.environ.get("EGRID_BASE_DIGEST")

    def status(ok: bool | None) -> str:
        return "UNOBSERVABLE" if ok is None else ("PASS" if ok else "FAIL")

    as_soft = rl.get("RLIMIT_AS", [None])[0]
    mem_max = cg.get("memory.max")
    controls = {
        "network_only_loopback": status(ifs == ["lo"] if ifs else None),
        "network_testnet_connect_fails": status(conn["result"] == "FAILED"),
        "cgroup_cpu_max_one_cpu": status(None if cg["cpu.max"] is None else cg["cpu.max"] == "100000 100000"),
        "cgroup_memory_max_2gib": status(None if mem_max is None else mem_max == str(TWO_GIB)),
        "rlimit_as_le_2gib": status(None if as_soft is None else (as_soft != resource.RLIM_INFINITY and as_soft <= TWO_GIB)),
        "deterministic_env_vars": status(all(env.get(k) == v for k, v in EXPECTED_ENV.items())),
        # PASS only for a genuinely read-only mount (EROFS); EACCES means "not permitted", not read-only.
        "rootfs_readonly": status(rootfs_readonly() == "NOT_WRITABLE(EROFS)"),
        "non_root_user": status(os.getuid() != 0),
    }
    record = {
        "schema": SCHEMA,
        "venue": venue,
        "image_id": image_id,
        "base_image_digest": base_digest,
        "python": {"version": sys.version, "implementation": platform.python_implementation(),
                   "executable": sys.executable},
        "platform": {"uname": list(platform.uname()), "os_release": _read("/etc/os-release")},
        "cpu": {"nproc_affinity": len(os.sched_getaffinity(0)),
                "model": next((ln.split(":", 1)[1].strip() for ln in (_read("/proc/cpuinfo") or "").splitlines()
                               if ln.startswith("model name")), None)},
        "meminfo_total": next((ln for ln in (_read("/proc/meminfo") or "").splitlines()
                               if ln.startswith("MemTotal")), None),
        "cgroup_v2": cg,
        "rlimits": rl,
        "env": env,
        "uid_gid": [os.getuid(), os.getgid()],
        "network": {"interfaces": ifs, "testnet_connect": conn, "target": list(TEST_NET)},
        "rootfs_write_probe": rootfs_readonly(),
        "numpy": npi,
        "packages": pk,
        "controls_observed": controls,
    }
    lock_lines = [
        f"schema={LOCK_SCHEMA}",
        f"image_id={image_id}",
        f"base_image_digest={base_digest}",
        f"python={platform.python_implementation()} {platform.python_version()}",
        f"machine={platform.machine()}",
        f"numpy_blas={(npi.get('blas') or {}).get('name') if isinstance(npi.get('blas'), dict) else None}",
        *[f"pkg={p}" for p in pk],
    ]
    return record, "\n".join(lock_lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lock", required=True)
    ap.add_argument("--record", required=True)
    ap.add_argument("--venue", default=os.environ.get("EGRID_VENUE", "UNSPECIFIED"))
    args = ap.parse_args()
    record, lock = build(args.venue)
    with open(args.lock, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(lock)
    with open(args.record, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(record, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    print(json.dumps(record["controls_observed"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
