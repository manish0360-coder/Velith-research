"""P4 sizing probe: protocol `p4/P4_SIZING_PROBE_PROTOCOL_v0.2.md` (PR-1 offline implementation).

Measures M_v = |S_W minus B0|: distinct repository ids returned by GitHub search for the frozen census
qualifiers at stars >= 1000 during the probe window, excluding the run-1 baseline ids.

LIVE EXECUTION IS LOCKED. `run` refuses unless FROZEN_PROTOCOL_SHA equals the SHA-256 of the
marked protocol block AND P4_PROBE_PR2=AUTHORIZED is set. FROZEN_PROTOCOL_SHA stays None until
PR-2 (a separately reviewed edit after the RD freeze). Requests go only through the frozen
`supply_census.Client` (imported, unchanged). Standard library only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import sys
import time
import urllib.parse
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
CENSUS_DIR = HERE.parent / "census"
PROTOCOL_DOC = HERE.parent / "P4_SIZING_PROBE_PROTOCOL_v0.2.md"
CENSUS_CODE_SHA = "23e410ca68b087ba25710f77103fe567ac6de04b64fbce8f79aca6897843581d"
RUN1_MANIFEST_SHA = "e6171986f102167419526aed9a3a3c868ea0f98c52c27c0a0267f10337a897fe"
FROZEN_PROTOCOL_SHA: str | None = None  # set ONLY at PR-2 by a reviewed edit

API = "https://api.github.com"
BASELINE_Q = "language:Python stars:>=1000 pushed:>=2026-08-01 archived:false fork:false"
STAR_MIN, SPLIT_AT, MAX_DEPTH = 1000, 900, 40
MAX_CALLS, MAX_SECONDS = 200, 4.5 * 3600
DAY_LO, DAY_HI = dt.date(1970, 1, 1).toordinal(), dt.date(2100, 12, 31).toordinal()
STOP_RIGOROUS_MAX, ELIGIBLE_MIN = 62, 500
PROJECTION_YIELDS = {"decile10": 0.82, "decile9": 0.62, "decile_max": 1.31}


class Stop(Exception):
    """Protocol or baseline defect (HTTP 422, missing ids, wrong fingerprints): no result."""


class CapReached(Exception):
    pass


# ---- protocol identity ------------------------------------------------------------------------
def protocol_block_sha(doc: Path = PROTOCOL_DOC) -> str:
    t = doc.read_text(encoding="utf-8")
    s = t.index("<!-- PROBE-PROTOCOL-BEGIN -->")
    e = t.index("<!-- PROBE-PROTOCOL-END -->") + len("<!-- PROBE-PROTOCOL-END -->")
    return hashlib.sha256(t[s:e].encode("utf-8")).hexdigest()


def sha_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ---- bands (protocol 4.3) ---------------------------------------------------------------------
@dataclass(frozen=True)
class Band:
    lo: int
    hi: int | None  # None = open upper bound
    dlo: int | None = None  # created-day ordinals (only for one-star bands)
    dhi: int | None = None

    def query(self) -> str:
        stars = f"stars:>={self.lo}" if self.hi is None else f"stars:{self.lo}..{self.hi}"
        q = f"language:Python {stars} pushed:>=2026-08-01 archived:false fork:false"
        if self.dlo is not None:
            d1 = dt.date.fromordinal(self.dlo).isoformat()
            d2 = dt.date.fromordinal(self.dhi).isoformat()  # type: ignore[arg-type]
            q += f" created:{d1}..{d2}"
        return q

    def split(self) -> tuple[Band, Band] | None:
        if self.dlo is not None:
            if self.dlo >= self.dhi:  # type: ignore[operator]
                return None
            m = (self.dlo + self.dhi) // 2  # type: ignore[operator]
            return Band(self.lo, self.hi, self.dlo, m), Band(self.lo, self.hi, m + 1, self.dhi)
        if self.hi is None:
            return Band(self.lo, 2 * self.lo - 1), Band(2 * self.lo, None)
        if self.lo < self.hi:
            m = (self.lo + self.hi) // 2
            return Band(self.lo, m), Band(m + 1, self.hi)
        return Band(self.lo, self.hi, DAY_LO, DAY_HI).split()  # one star value -> created tiling


def tiling_ok(bands: list[Band]) -> bool:
    """Invariants P1 (star tiling of [1000, inf)) and P2 (created tiling per one-star value)."""
    stars: list[tuple[int, int | None]] = []
    created: dict[int, list[tuple[int, int]]] = {}
    for b in bands:
        if b.dlo is not None:
            created.setdefault(b.lo, []).append((b.dlo, b.dhi))  # type: ignore[arg-type]
            if not stars or stars[-1] != (b.lo, b.hi):
                stars.append((b.lo, b.hi))
        else:
            stars.append((b.lo, b.hi))
    stars.sort(key=lambda r: r[0])
    if not stars or stars[0][0] != STAR_MIN or stars[-1][1] is not None:
        return False
    for (a_lo, a_hi), (b_lo, _) in zip(stars, stars[1:]):
        if a_hi is None or b_lo != a_hi + 1 or a_hi < a_lo:
            return False
    for days in created.values():
        days.sort()
        if days[0][0] != DAY_LO or days[-1][1] != DAY_HI:
            return False
        if any(n[0] != p[1] + 1 for p, n in zip(days, days[1:])):
            return False
    return True


# ---- baseline B0 (protocol 3) -----------------------------------------------------------------
def search_key(page: int) -> str:
    q = urllib.parse.urlencode(
        {"q": BASELINE_Q, "sort": "stars", "order": "desc", "per_page": 100, "page": page}
    )
    return hashlib.sha256(
        json.dumps(["GET", f"{API}/search/repositories?{q}", None], sort_keys=True).encode()
    ).hexdigest()


def manifest_sha(run: Path) -> str:
    files = sorted((run / "cache").glob("*.json"))
    lines = [f"{sha_file(p)}  {p.relative_to(run).as_posix()}" for p in files]
    return hashlib.sha256(("\n".join(lines) + "\n").encode()).hexdigest()


def load_baseline(copy: Path, expected_manifest: str = RUN1_MANIFEST_SHA) -> dict[int, str]:
    """Read-only: ids of the 10 frozen cached search pages of run 1. Refuses on any defect."""
    if manifest_sha(copy) != expected_manifest:
        raise Stop("baseline copy manifest does not match run 1")
    ids: dict[int, str] = {}
    n_items = 0
    for page in range(1, 11):
        f = copy / "cache" / f"{search_key(page)}.json"
        if not f.exists():
            raise Stop(f"baseline search page {page} missing")
        for it in json.loads(f.read_text(encoding="utf-8"))["response"].get("items") or []:
            n_items += 1
            if not isinstance(it.get("id"), int):
                raise Stop("baseline item without numeric id (name matching is not allowed)")
            ids[it["id"]] = it["full_name"]
    if n_items != 1000:
        raise Stop(f"baseline has {n_items} items, expected 1000")
    return ids


# ---- probe -------------------------------------------------------------------------------------
@dataclass
class BandResult:
    band: Band
    T: int | None = None
    ids: dict[int, dict[str, Any]] = field(default_factory=dict)
    pages: int = 0
    status: str = "ok"  # ok | failed | incomplete_results | unenumerable | shortfall | cap
    reenumerated: bool = False
    T_re: int | None = None

    @property
    def tol(self) -> int:
        return max(3, math.ceil(0.01 * (self.T or 0)))


class Prober:
    def __init__(self, client: Any, baseline: dict[int, str], now: Callable[[], float] = time.monotonic,
                 max_calls: int = MAX_CALLS, max_seconds: float = MAX_SECONDS) -> None:
        self.cl, self.b0, self.now = client, baseline, now
        self.max_calls, self.max_seconds = max_calls, max_seconds
        self.calls, self.t0 = 0, now()
        self.seen: dict[int, dict[str, Any]] = {}

    def search(self, q: str, page: int, per_page: int, tag: str) -> dict[str, Any] | None:
        if self.calls >= self.max_calls or self.now() - self.t0 > self.max_seconds:
            raise CapReached
        params = {"q": q, "sort": "stars", "order": "desc", "per_page": per_page, "page": page}
        url = f"{API}/search/repositories?{urllib.parse.urlencode(params)}"
        before = len(self.cl.failures)
        self.calls += 1
        resp = self.cl.call("GET", url, tag=tag)
        new = self.cl.failures[before:]
        if any("HTTP 422" in f.get("error", "") for f in new):
            raise Stop(f"HTTP 422 for {tag}")
        if new or not isinstance(resp, dict):
            return None
        return resp

    def _add(self, br: BandResult, items: list[dict[str, Any]]) -> None:
        for it in items:
            rec = {"full_name": it.get("full_name"), "stars": it.get("stargazers_count"),
                   "created_at": it.get("created_at"), "pushed_at": it.get("pushed_at")}
            br.ids[it["id"]] = rec
            self.seen[it["id"]] = rec

    def _pages(self, br: BandResult, per_page: int, start: int) -> bool:
        q = br.band.query()
        for k in range(start, math.ceil((br.T or 0) / per_page) + 1):
            r = self.search(q, k, per_page, f"page:{q}:{per_page}:{k}")
            if r is None:
                br.status = "failed"
                return False
            br.pages += 1
            if r.get("incomplete_results"):
                br.status = "incomplete_results"
            items = r.get("items") or []
            self._add(br, items)
            if len(items) < per_page:
                break
        return True

    def resolve(self, band: Band, depth: int, out: list[BandResult]) -> None:
        br = BandResult(band)
        out_index = len(out)
        out.append(br)
        r = self.search(band.query(), 1, 100, f"size:{band.query()}")
        if r is None:
            br.status = "failed"
            return
        br.T, br.pages = int(r.get("total_count", 0)), 1
        if r.get("incomplete_results"):
            br.status = "incomplete_results"
        if br.T >= SPLIT_AT:
            parts = band.split() if depth < MAX_DEPTH else None
            if parts is None:
                br.status = "unenumerable"
                self._add(br, r.get("items") or [])
                return
            del out[out_index]
            self.resolve(parts[0], depth + 1, out)
            self.resolve(parts[1], depth + 1, out)
            return
        self._add(br, r.get("items") or [])
        if not self._pages(br, 100, 2):
            return
        if br.status == "ok" and abs(len(br.ids) - br.T) > br.tol:
            br.reenumerated = True
            if self._pages(br, 99, 1) and abs(len(br.ids) - br.T) > br.tol:
                br.status = "shortfall"

    def sweep(self, s: int) -> dict[str, Any]:
        w = max(5, math.ceil(0.02 * s))
        band = Band(max(STAR_MIN, s - w), s + w - 1)
        before = set(self.seen)
        parts: list[BandResult] = []
        self.resolve(band, 0, parts)  # same partition rules (4.3), incl. created-date fallback
        status = "ok" if all(b.status == "ok" for b in parts) else "sweep_incomplete"
        return {"s": s, "w": w, "status": status, "recovered": len(set(self.seen) - before),
                "sub_bands": len(parts)}

    def count(self, q: str, tag: str) -> int | None:
        r = self.search(q, 1, 1, tag)
        return None if r is None or r.get("incomplete_results") else int(r.get("total_count", 0))


def decide(outcome: str, m_v: int | None) -> str:
    if outcome == "STOPPED":
        return "STOPPED"
    if outcome != "EXACT" or m_v is None:
        return "INCOMPLETE (no proposal by default; M_v,LB reported as a lower bound only)"
    if m_v <= STOP_RIGOROUS_MAX:
        return "STOP-RIGOROUS"
    if m_v < ELIGIBLE_MIN:
        return "RD-JUDGMENT"
    return "ELIGIBLE-TO-PROPOSE census v2 (measured-count threshold; not a yield bound)"


def histogram(stars: list[int]) -> dict[str, int]:
    edges = [(1000, 1499), (1500, 1999), (2000, 2999), (3000, 4999), (5000, 6608), (6609, None)]
    out = {}
    for lo, hi in edges:
        out[f"{lo}-{hi if hi else 'inf'}"] = sum(1 for s in stars if s >= lo and (hi is None or s <= hi))
    return out


def probe(client: Any, baseline: dict[int, str], **kw: Any) -> dict[str, Any]:
    p = Prober(client, baseline, **kw)
    root = Band(STAR_MIN, None)
    bands: list[BandResult] = []
    sweeps: list[dict[str, Any]] = []
    T_start = T_end = None
    cap = False
    try:
        T_start = p.count(root.query(), "count:start")
        p.resolve(root, 0, bands)
        lows = sorted({br.band.lo for br in bands if br.band.lo != STAR_MIN})
        sweeps = [p.sweep(s) for s in lows]
        for br in bands:
            if br.status in ("ok",) and br.T is not None:
                br.T_re = p.count(br.band.query(), f"recheck:{br.band.query()}")
        T_end = p.count(root.query(), "count:end")
    except CapReached:
        cap = True
    except Stop as e:
        return {"outcome": "STOPPED", "reason": str(e), "decision": "STOPPED", "calls": p.calls}
    s_w = set(p.seen)
    m_lb = len(s_w - set(baseline))
    missing = sorted(set(baseline) - s_w)
    recovered = sum(sw.get("recovered", 0) for sw in sweeps)
    drift_ok = all(br.T_re is not None and abs(br.T_re - br.T) <= max(3, math.ceil(0.02 * br.T))
                   for br in bands if br.T is not None)
    checks = {
        "C0_partition_tiles": tiling_ok([br.band for br in bands]) and not cap,
        "C1_all_enumerable": all(br.T is not None and br.T < SPLIT_AT for br in bands) and not cap,
        "C2_counts_agree": all(br.T is not None and abs(len(br.ids) - br.T) <= br.tol for br in bands),
        "C3_drift": drift_ok and T_start is not None and T_end is not None
        and abs(T_end - T_start) <= math.ceil(0.02 * T_start),
        "C4_baseline_recall": len(missing) <= 9,
        "C5_movers_rare": recovered <= math.ceil(0.01 * max(1, len(s_w))),
        "C6_no_unresolved": not cap and all(br.status == "ok" for br in bands)
        and all(sw["status"] == "ok" for sw in sweeps),
    }
    outcome = "EXACT" if all(checks.values()) else "INCOMPLETE"
    m_v = m_lb if outcome == "EXACT" else None
    unseen_stars = [p.seen[i]["stars"] for i in s_w - set(baseline) if p.seen[i]["stars"] is not None]
    return {
        "outcome": outcome,
        "M_v": m_v,
        "M_v_lower_bound": m_lb,
        "decision": decide(outcome, m_v),
        "S_W": len(s_w),
        "B0": len(baseline),
        "baseline_missing_ids": missing,
        "T_start": T_start,
        "T_end": T_end,
        "cap_reached": cap,
        "calls": p.calls,
        "checks": checks,
        "bands": [
            {"query": br.band.query(), "T": br.T, "E": len(br.ids), "tol": br.tol, "T_re": br.T_re,
             "pages": br.pages, "status": br.status, "reenumerated": br.reenumerated,
             "ids": sorted(br.ids)}
            for br in bands
        ],
        "sweeps": sweeps,
        "unseen_star_histogram": histogram(unseen_stars),
        "projections_non_decisive": {
            "assumption": "unseen repos yield like observed run-1 deciles; extrapolation outside the "
            "observed star range; not a bound in either direction; never used in the decision",
            **{k: (None if m_v is None else m_v * v) for k, v in PROJECTION_YIELDS.items()},
        },
    }


# ---- evidence + CLI ----------------------------------------------------------------------------
def write_evidence(out: Path, result: dict[str, Any], meta: dict[str, Any]) -> str:
    (out / "probe_result.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    (out / "run_meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8")
    files = sorted(p for p in out.rglob("*") if p.is_file() and p.name != "MANIFEST.sha256")
    data = "".join(f"{sha_file(p)}  {p.relative_to(out).as_posix()}\n" for p in files)
    (out / "MANIFEST.sha256").write_text(data, encoding="utf-8")
    return hashlib.sha256(data.encode()).hexdigest()


def live_authorized() -> tuple[bool, str]:
    if FROZEN_PROTOCOL_SHA is None:
        return False, "LOCKED: FROZEN_PROTOCOL_SHA is None (PR-2 not performed)"
    if protocol_block_sha() != FROZEN_PROTOCOL_SHA:
        return False, "LOCKED: protocol block SHA differs from the frozen SHA"
    if sha_file(CENSUS_DIR / "supply_census.py") != CENSUS_CODE_SHA:
        return False, "LOCKED: census code SHA changed"
    if os.environ.get("P4_PROBE_PR2") != "AUTHORIZED":
        return False, "LOCKED: P4_PROBE_PR2=AUTHORIZED not set"
    return True, "authorized"


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - live path is locked in PR-1
    ap = argparse.ArgumentParser(prog="sizing_probe")
    ap.add_argument("cmd", choices=("identity", "run"))
    ap.add_argument("--out", type=Path)
    ap.add_argument("--baseline", type=Path)
    a = ap.parse_args(argv)
    if a.cmd == "identity":
        print(f"protocol_block_sha {protocol_block_sha()}")
        print(f"census_code_ok {sha_file(CENSUS_DIR / 'supply_census.py') == CENSUS_CODE_SHA}")
        print(f"frozen_protocol_sha {FROZEN_PROTOCOL_SHA}")
        return 0
    ok, why = live_authorized()
    if not ok:
        print(why, file=sys.stderr)
        return 3
    if a.out is None or a.baseline is None or a.out.exists():
        print("STOP: --out must be a NEW directory and --baseline the read-only run-1 copy", file=sys.stderr)
        return 2
    sys.path.insert(0, str(CENSUS_DIR))
    import supply_census as C  # noqa: PLC0415

    baseline = load_baseline(a.baseline)
    a.out.mkdir(parents=True)
    t0 = dt.datetime.now(dt.timezone.utc).isoformat()
    result = probe(C.Client(a.out, offline=False), baseline)
    meta = {"protocol_block_sha": protocol_block_sha(), "census_code_sha": CENSUS_CODE_SHA,
            "probe_code_sha": sha_file(Path(__file__)), "utc_start": t0,
            "utc_end": dt.datetime.now(dt.timezone.utc).isoformat(), "caps": [MAX_CALLS, MAX_SECONDS]}
    print(json.dumps({k: result[k] for k in ("outcome", "M_v", "M_v_lower_bound", "decision", "calls")}))
    print(f"evidence_manifest_sha256 {write_evidence(a.out, result, meta)}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
