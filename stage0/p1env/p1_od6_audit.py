#!/usr/bin/env python3
"""READ-ONLY OD-6 audit: the full remaining same-repo sequence after a given task, in the frozen order.

Imports p1_lottery.py's functions unchanged (same revision check, filters, pool=98 / T2-T5 checks,
salted order). Prints every remaining candidate with F2P, P2P and the information-only
suspicious-ID count, and registry metadata (amd64 digest + compressed size; no pull) for the next
`--sizes N` candidates. Selects nothing, writes no task line, pulls nothing, admits nothing.

Usage (WSL): python3 p1_od6_audit.py matplotlib__matplotlib-22719 [--sizes 3]
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import p1_lottery as L  # noqa: E402  (unchanged resolver functions)


def registry(iid: str) -> tuple[str, int]:
    image = "swebench/sweb.eval.x86_64." + iid.replace("__", "_1776_")
    raw = subprocess.run(["docker", "manifest", "inspect", "-v", f"{image}:latest"],
                         capture_output=True, text=True, check=True).stdout
    entries = json.loads(raw)
    entries = entries if isinstance(entries, list) else [entries]
    e = next(x for x in entries if (x["Descriptor"].get("platform") or {}).get("architecture") == "amd64")
    man = e.get("SchemaV2Manifest") or e.get("OCIManifest")
    return e["Descriptor"]["digest"], sum(int(layer["size"]) for layer in man["layers"])


def main() -> int:
    after_iid = sys.argv[1]
    n_sizes = int(sys.argv[sys.argv.index("--sizes") + 1]) if "--sizes" in sys.argv else 3
    revision = L.dataset_revision()
    if not revision.startswith(L.DESIGN_REVISION_PREFIX):
        print(f"STOP: dataset revision {revision}")
        return 1
    pool = sorted((r for r in L.rows() if L.eligible(r)), key=lambda r: L.key(r["instance_id"]))
    first: dict[str, str] = {}
    for r in pool:
        first.setdefault(r["repo"], r["instance_id"])
    if len(pool) != 98 or {k: first.get(k) for k in L.EXPECTED} != L.EXPECTED:
        print("STOP: lottery not reproduced")
        return 1
    repo = next(r["repo"] for r in pool if r["instance_id"] == after_iid)
    seq = [r for r in pool if r["repo"] == repo]
    ids = [r["instance_id"] for r in seq]
    pos = ids.index(after_iid)
    print(f"revision {revision}; pool 98 OK; {repo}: {len(seq)} eligible in frozen order; "
          f"{after_iid} is #{pos + 1}; remaining after it: {len(seq) - pos - 1}")
    print("full frozen order:", ", ".join(i.split("-")[-1] for i in ids))
    rows_out = []
    for k, r in enumerate(seq[pos + 1:], start=1):
        req = L.as_list(r["FAIL_TO_PASS"]) + L.as_list(r["PASS_TO_PASS"])
        bad = [i for i in req if re.search(r"\s", i) or i.count("[") != i.count("]")]
        rec = {"n": k, "instance_id": r["instance_id"], "f2p": len(L.as_list(r["FAIL_TO_PASS"])),
               "p2p": len(L.as_list(r["PASS_TO_PASS"])), "suspicious_info_only": len(bad)}
        if k <= n_sizes:
            rec["amd64_digest"], rec["compressed_bytes"] = registry(r["instance_id"])
        rows_out.append(rec)
        print(json.dumps(rec))
    out = HERE / "results" / f"od6_audit_after_{after_iid}.json"
    out.write_text(json.dumps({"revision": revision, "repo": repo, "after": after_iid,
                               "frozen_order": ids, "remaining": rows_out}, indent=2) + "\n",
                   encoding="utf-8")
    print(f"written: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
