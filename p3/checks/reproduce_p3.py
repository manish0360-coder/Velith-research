"""Independent reproduction of P3 verification outcomes (no API call, no model, no regeneration).

For each selected episode it re-pulls the frozen task image by digest, checks its identity,
re-runs the frozen probe gate (P1 `stage_x`) on the RECORDED patch in a fresh container, and
compares the classification and every per-test outcome with the original evidence.
Original evidence is never touched; output goes to p3/evidence/_repro/<slot>/<mode>/.

  python3 -B p3/checks/reproduce_p3.py passes        the six claimed passes (recorded patch.diff)
  python3 -B p3/checks/reproduce_p3.py extractor-fn  DIAGNOSTIC ONLY: P3-01 and P3-10 with the
                                                     fenced block before `.strip()` (quantifies
                                                     the extractor defect; never an endpoint)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "p3" / "harness"))
import p3_run as R  # noqa: E402

PASSES = ("P3-04", "P3-05", "P3-07", "P3-08", "P3-09", "P3-11")
EXTRACTOR_FN = ("P3-01", "P3-10")
OUT = R.EVIDENCE / "_repro"


def unstripped_block(completion: str) -> str:
    st = completion.find("```") + 3
    block = completion[st:completion.find("```", st)].split("\n")
    if block and block[0].strip().lower() in ("diff", "patch", "udiff", "python"):
        block = block[1:]
    return "\n".join(block).strip("\n") + "\n"


def compare(orig: dict[str, Any] | None, new: dict[str, Any]) -> dict[str, Any]:
    n = new["deterministic"]
    out: dict[str, Any] = {"classification": n["classification"], "reason": n["reason"],
                           "detail": n["detail"], "gate": R.H.p1().patch_applies(n)}
    if orig is not None:
        o = orig["deterministic"]
        oc_o = (o.get("candidate") or {}).get("outcomes") or {}
        oc_n = (n.get("candidate") or {}).get("outcomes") or {}
        out["same_classification"] = o["classification"] == n["classification"]
        out["same_patch"] = o["candidate_patch_sha256"] == n["candidate_patch_sha256"]
        out["outcome_diffs"] = {k: (oc_o.get(k), oc_n.get(k)) for k in set(oc_o) | set(oc_n)
                                if oc_o.get(k) != oc_n.get(k)}
        out["reproduced"] = out["same_classification"] and out["same_patch"] and \
            not out["outcome_diffs"]
    return out


def reproduce(ops: Any, mode: str, out_root: Path = OUT) -> dict[str, Any]:
    pilot = R.load_pilot()
    by_slot = {"P3-" + t["slot"][3:]: t for t in pilot["tasks"]}
    slots = PASSES if mode == "passes" else EXTRACTOR_FN
    results: dict[str, Any] = {}
    for slot in slots:
        t = by_slot[slot]
        d = R.EVIDENCE / slot
        dst = out_root / slot / mode
        if (dst / "result.json").exists():
            results[slot] = R.B.load_json(dst / "result.json")
            continue
        spec = R.B.load_json(R.P2_EVIDENCE / t["slot"] / "A" / "spec.json")
        if mode == "passes":
            patch = (d / "E" / "patch.diff").read_text(encoding="utf-8")
            orig = R.B.load_json(sorted(d.glob("X-U-*/evidence.json"))[-1])
        else:
            patch = unstripped_block((d / "G" / "attempt-1" / "completion.txt")
                                     .read_text(encoding="utf-8"))
            orig = None
        need, free = R.A.storage_need(int(t["compressed_bytes"])), ops.free_bytes()
        if free < need:
            raise R.P3Stop(f"storage gate: free {free} < need {need} before {slot}")
        ref = t["ref"]
        pulled = ops.pull(ref) or ops.pull(ref)
        try:
            insp = ops.inspect(ref) if pulled else None
            if insp is None or ref not in insp[0] or insp[2] != t["image_id"]:
                res: dict[str, Any] = {"status": "IDENTITY_OR_PULL_FAILED", "inspect": insp}
            else:
                new = ops.gate(spec, patch, dst / "run", float(t["stage_x_timeout_s"]), "U")
                res = {"status": "RAN", "mode": mode, **compare(orig, new)}
        finally:
            if pulled:
                ops.remove(ref)
        res["diagnostic_only"] = mode != "passes"
        R.A.write(dst / "result.json", res)
        results[slot] = res
    return results


def main() -> int:  # pragma: no cover
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in ("passes", "extractor-fn"):
        print(__doc__)
        return 2
    res = reproduce(R.DockerP3Ops(), mode)
    print(json.dumps({s: {k: r.get(k) for k in ("status", "classification", "detail",
                                                "reproduced", "outcome_diffs")}
                      for s, r in res.items()}, indent=2))
    if mode == "passes":
        return 0 if all(r.get("reproduced") for r in res.values()) else 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
