#!/usr/bin/env python3
"""Recompute the P1 task lottery (P1 design §7) and pick the OD-6 replacement for an inadmissible task.

Pool: SWE-bench Verified, repos {astropy, matplotlib, seaborn, xarray, pylint, scikit-learn}, with
  (b) every test_patch file is .py, (c) >= 1 PASS_TO_PASS, (d) 1 <= |FAIL_TO_PASS| <= 5,
  (e) the gold patch edits exactly one non-test file.  ((a) pytest command holds for all six repos.)
Order: SHA-256(instance_id + "|velith-m2pv-p1-pilot-v1") ascending. Self-check: the pool must have
98 tasks and the first task per repo must reproduce T2..T5. Then, for the repo of the task being
replaced, the next candidates in lottery order are listed, flagging required test ids that contain
whitespace (the dataset truncates them, so the frozen probe cannot map them -> inadmissible).
Selection is the LITERAL OD-6 text: the immediately next eligible task of the same repository.
The whitespace/bracket flag is printed for information only and does NOT influence selection
(a screening criterion derived from T2's observed failure would be an unratified, post-hoc rule).
The dataset revision is checked against the design's pinned revision prefix 78f471bf; mismatch -> STOP.
The chosen task's linux/amd64 digest is resolved (registry metadata only, no pull) and written to
p1_extra_tasks.txt for p1_admit.sh. Nothing is pulled or admitted by this script.

Usage (WSL): python3 p1_lottery.py <replaced_id> <replaced_instance>   e.g.  T2 matplotlib__matplotlib-24570
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SALT = "|velith-m2pv-p1-pilot-v1"
REPOS = {"astropy/astropy", "matplotlib/matplotlib", "mwaskom/seaborn", "pydata/xarray",
         "pylint-dev/pylint", "scikit-learn/scikit-learn"}
EXPECTED = {"matplotlib/matplotlib": "matplotlib__matplotlib-24570",
            "scikit-learn/scikit-learn": "scikit-learn__scikit-learn-14629",
            "astropy/astropy": "astropy__astropy-7336", "pydata/xarray": "pydata__xarray-6721"}
DIFF_FILE = re.compile(r"^diff --git a/.* b/(.*)$", re.MULTILINE)


def rows() -> list[dict]:
    out, offset = [], 0
    while True:
        q = urllib.parse.urlencode({"dataset": "SWE-bench/SWE-bench_Verified", "config": "default",
                                    "split": "test", "offset": offset, "length": 100})
        with urllib.request.urlopen(f"https://datasets-server.huggingface.co/rows?{q}", timeout=60) as r:
            batch = [e["row"] for e in json.load(r).get("rows", [])]
        if not batch:
            return out
        out += batch
        offset += 100


def as_list(v: object) -> list[str]:
    return [str(x) for x in (json.loads(v) if isinstance(v, str) else v)]


def is_test(path: str) -> bool:
    parts = path.split("/")
    return any(p in ("tests", "test", "testing") for p in parts[:-1]) or parts[-1].startswith("test_")


def eligible(r: dict) -> bool:
    tp = sorted(set(DIFF_FILE.findall(r["test_patch"])))
    gold = sorted(set(DIFF_FILE.findall(r["patch"])))
    f2p, p2p = as_list(r["FAIL_TO_PASS"]), as_list(r["PASS_TO_PASS"])
    return (r["repo"] in REPOS and all(p.endswith(".py") for p in tp) and len(p2p) >= 1
            and 1 <= len(f2p) <= 5 and len([g for g in gold if not is_test(g)]) == 1
            and all(not is_test(g) for g in gold))


def key(iid: str) -> str:
    return hashlib.sha256((iid + SALT).encode()).hexdigest()


DESIGN_REVISION_PREFIX = "78f471bf"


def dataset_revision() -> str:
    url = "https://huggingface.co/api/datasets/SWE-bench/SWE-bench_Verified"
    with urllib.request.urlopen(url, timeout=60) as r:
        return str(json.load(r).get("sha", ""))


def main() -> int:
    replaced_id, replaced = sys.argv[1], sys.argv[2]
    revision = dataset_revision()
    print(f"dataset revision: {revision} (design: {DESIGN_REVISION_PREFIX}...)")
    if not revision.startswith(DESIGN_REVISION_PREFIX):
        print("STOP: dataset revision differs from the design's pinned revision")
        return 1
    pool = sorted((r for r in rows() if eligible(r)), key=lambda r: key(r["instance_id"]))
    first: dict[str, str] = {}
    for r in pool:
        first.setdefault(r["repo"], r["instance_id"])
    check = {repo: first.get(repo) for repo in EXPECTED}
    print(f"pool size: {len(pool)} (design: 98)")
    print("first-per-repo reproduces T2..T5:", check == EXPECTED, check)
    if len(pool) != 98 or check != EXPECTED:
        print("STOP: lottery not reproduced; do not pick a replacement")
        return 1
    repo = next(r["repo"] for r in pool if r["instance_id"] == replaced)
    seq = [r for r in pool if r["repo"] == repo]
    after = seq[[r["instance_id"] for r in seq].index(replaced) + 1:]
    if not after:
        print("STOP: no further eligible task in this repository")
        return 1
    for r in after[:5]:  # information only
        ids = as_list(r["FAIL_TO_PASS"]) + as_list(r["PASS_TO_PASS"])
        bad = [i for i in ids if re.search(r"\s", i) or i.count("[") != i.count("]")]
        print(f"  next-in-order {r['instance_id']}: F2P={len(as_list(r['FAIL_TO_PASS']))} "
              f"P2P={len(as_list(r['PASS_TO_PASS']))} suspicious_ids(info only)={len(bad)}")
    chosen = after[0]  # literal OD-6: the immediately next eligible task
    iid = chosen["instance_id"]
    image = "swebench/sweb.eval.x86_64." + iid.replace("__", "_1776_")
    raw = subprocess.run(["docker", "manifest", "inspect", "-v", f"{image}:latest"],
                         capture_output=True, text=True, check=True).stdout
    entries = json.loads(raw)
    entries = entries if isinstance(entries, list) else [entries]
    e = next(x for x in entries if (x["Descriptor"].get("platform") or {}).get("architecture") == "amd64")
    man = e.get("SchemaV2Manifest") or e.get("OCIManifest")
    size = sum(int(layer["size"]) for layer in man["layers"])
    line = f"{replaced_id}R1|{iid}|{image}|{e['Descriptor']['digest']}|{size}|900"
    (HERE / "p1_extra_tasks.txt").write_text(line + "\n", encoding="utf-8")
    (HERE / "results" / f"lottery_replacement_{replaced_id}.json").write_text(json.dumps(
        {"replaced": replaced, "reason": "Case A INFRA_ERROR RESULT_MAPPING (truncated test id)",
         "dataset_revision": revision, "pool_size": len(pool), "rule": "next eligible, same repo",
         "chosen": iid, "task_line": line}, indent=2) + "\n", encoding="utf-8")
    print(f"REPLACEMENT {replaced_id} -> {iid}\n{line}\nwritten: p1_extra_tasks.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
