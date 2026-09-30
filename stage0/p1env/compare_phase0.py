#!/usr/bin/env python3
"""Compare two phase0_wsl.sh result directories (+ an optional Phase0-Windows result). READ-ONLY.

Usage:
  python3 compare_phase0.py <baseline_wsl_dir> <post_wsl_dir> [<post_windows_dir>]

It checks that the shared Docker infrastructure and Velith main are unchanged, then applies the
frozen P1 space rule (free space on the drive holding docker_data.vhdx >= 25.443 GB) and prints GO/NO-GO.
Exit code: 0 = GO (all checks pass), 1 = NO-GO, 2 = error.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RULE_BYTES = int(2.5 * 6_177_118_311 + 10_000_000_000)  # frozen P1 readiness rule (25.443 GB)


def psv(path: Path) -> list[list[str]]:
    return [l.rstrip("\n").split("|") for l in path.read_text(encoding="utf-8", errors="replace").splitlines()
            if l.startswith("sha256:") or re.match(r"^[0-9a-f]{64}\|", l)]


def images(d: Path) -> dict[str, str]:
    return {r[0]: r[1] for r in psv(d / "inventory" / "images_inspect.psv")}


def containers(d: Path) -> dict[str, tuple[str, str]]:
    return {r[0]: (r[1], r[2]) for r in psv(d / "inventory" / "containers_inspect.psv")}


def volumes(d: Path) -> dict[str, str | None]:
    out = {}
    for f in sorted((d / "volumes").glob("*.json")):
        try:
            v = json.loads(f.read_text())
            out[v["volume"]] = (v.get("metadata") or {}).get("tree_sha256")
        except (ValueError, KeyError):
            out[f.stem] = None
    return out


def networks(d: Path) -> set[str]:
    names = set()
    for l in (d / "inventory" / "networks_post.jsonl").read_text().splitlines():
        try:
            names.add(json.loads(l)["Name"])
        except (ValueError, KeyError):
            pass
    return names


def pytest_result(d: Path) -> dict[str, int]:
    t = (d / "velith" / "05.txt").read_text(encoding="utf-8", errors="replace").splitlines()
    s = "".join(m.group(1) for l in t if (m := re.match(r"^([.sFExX]+)\s+\[\s*\d+%\]", l)))
    return {c: s.count(c) for c in ".sFExX" if s.count(c)} | {"total": len(s)}


def velith(d: Path) -> dict[str, object]:
    exits = {}
    for f in sorted((d / "velith").glob("0*.txt")):
        ex = re.findall(r"\[exit (\d+)\]", f.read_text(encoding="utf-8", errors="replace"))
        exits[f.name] = int(ex[-1]) if ex else None
    s = json.loads((d / "summary.json").read_text())
    return {"exits": exits, "head": s.get("velith_git_head"), "clean_pre": s.get("velith_git_clean_pre"),
            "clean_post": s.get("velith_git_clean_post"), "image": (s.get("velith_image") or "").split(" ")[0],
            "pytest": pytest_result(d)}


def engine(d: Path) -> dict[str, object]:
    info = json.loads((d / "inventory" / "docker_info.json").read_text())
    ds = dict(info.get("DriverStatus") or [])
    return {"ServerVersion": info.get("ServerVersion"), "driver_type": ds.get("driver-type"),
            "CgroupVersion": info.get("CgroupVersion")}


def main() -> int:
    if len(sys.argv) not in (3, 4):
        print(__doc__)
        return 2
    b, p = Path(sys.argv[1]), Path(sys.argv[2])
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, ok, detail))

    ib, ip = images(b), images(p)
    check("images: identical ID set", set(ib) == set(ip),
          f"missing={sorted(set(ib) - set(ip))} extra={sorted(set(ip) - set(ib))}")
    check("images: identical tags per ID", all(ib[k] == ip.get(k) for k in ib), "")
    cb, cp = containers(b), containers(p)
    check("containers: identical (id, name, image)", cb == cp, f"b={len(cb)} p={len(cp)}")
    vb, vp = volumes(b), volumes(p)
    check("volumes: identical names", set(vb) == set(vp), f"b={sorted(vb)} p={sorted(vp)}")
    diff = [k for k in vb if vb[k] is None or vb[k] != vp.get(k)]
    check("volumes: identical content tree hash", not diff, f"differs={diff}")
    check("networks: identical names", networks(b) == networks(p), "")
    eb, ep = engine(b), engine(p)
    check("engine: same version/snapshotter/cgroup", eb == ep, f"b={eb} p={ep}")
    lb, lp = velith(b), velith(p)
    check("velith: all checks exit 0 (post)", all(v == 0 for v in lp["exits"].values()) and len(lp["exits"]) == 5,
          str(lp["exits"]))
    check("velith: same HEAD, clean before/after", lp["head"] == lb["head"] and lp["clean_pre"] and lp["clean_post"],
          str(lp["head"]))
    check("velith: same image ID", lp["image"] == lb["image"], lp["image"])
    check("velith: identical pytest outcome (all passed, 0 skipped)", lp["pytest"] == lb["pytest"]
          and set(lp["pytest"]) <= {".", "total"}, f"b={lb['pytest']} p={lp['pytest']}")

    if len(sys.argv) == 4:
        w = json.loads(Path(sys.argv[3], "phase0_windows.json").read_text(encoding="utf-8-sig"))
        vhdx = next(v for v in w["docker_vhdx"] if v["path"].lower().endswith("docker_data.vhdx"))
        drive = vhdx["path"][0].upper()
        free = next(d["free_bytes"] for d in w["drives"] if d["drive"].upper() == drive)
        check(f"space rule: {drive}: free >= {RULE_BYTES:,} B", free >= RULE_BYTES,
              f"free={free:,} B; vhdx length={vhdx['length_bytes']:,} B allocated={vhdx['allocated_bytes']:,} B")

    for name, ok, detail in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({detail})" if detail and not ok or 'space' in name else ""))
    go = all(ok for _, ok, _ in checks) and len(sys.argv) == 4
    infra_ok = all(ok for n, ok, _ in checks if not n.startswith("space"))
    if len(sys.argv) == 4:
        print("VERDICT:", "GO (P1 image admission may be authorized)" if go else "NO-GO")
    else:
        print("VERDICT:", "INFRA UNCHANGED: PASS" if infra_ok else "INFRA UNCHANGED: FAIL", "(no space verdict)")
    return 0 if go or (len(sys.argv) == 3 and all(ok for _, ok, _ in checks)) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {type(exc).__name__}: {exc}")
        sys.exit(2)
