"""Synthetic tests for the P4 sizing probe (PR-1). No network: a fake GitHub search server is
injected as the frozen Client's opener.

Run: PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider p4/probe/test_sizing_probe.py
"""

from __future__ import annotations

import datetime as dt
import hashlib
import io
import json
import random
import re
import sys
import urllib.error
import urllib.parse
from pathlib import Path
from typing import Any

import pytest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "census"))
import sizing_probe as P  # noqa: E402
import supply_census as C  # noqa: E402


# ---- fake GitHub search ------------------------------------------------------------------------
class Resp:
    def __init__(self, payload: Any) -> None:
        self.payload = payload
        self.headers = {"X-RateLimit-Remaining": "4000", "X-RateLimit-Reset": "0"}

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()

    def __enter__(self) -> Resp:
        return self

    def __exit__(self, *a: Any) -> None:
        pass


class FakeGitHub:
    """Repository search over a synthetic population, with GitHub's 1,000-result ceiling (422)."""

    _p4_test_double = True  # marks this opener as a synthetic test double (library lock, A1)

    def __init__(self, repos: list[dict[str, Any]]) -> None:
        self.repos = repos
        self.calls = 0
        self.urls: list[str] = []
        self.hooks: list[Any] = []  # callables(fake, q, page, per_page) -> optional override

    def match(self, q: str) -> list[dict[str, Any]]:
        out = list(self.repos)
        rp = re.search(r"repo:(\S+)", q)
        if rp:
            out = [r for r in out if r["full_name"] == rp.group(1)]
        m = re.search(r"stars:(>=)?(\d+)(?:\.\.(\d+))?", q)
        if m:
            lo = int(m.group(2))
            hi = None if m.group(1) or m.group(3) is None else int(m.group(3))
            out = [r for r in out if r["stargazers_count"] >= lo
                   and (hi is None or r["stargazers_count"] <= hi)]
        c = re.search(r"created:(\d{4}-\d\d-\d\d)\.\.(\d{4}-\d\d-\d\d)", q)
        if c:
            d1, d2 = c.group(1), c.group(2)
            out = [r for r in out if d1 <= r["created_at"][:10] <= d2]
        return sorted(out, key=lambda r: (-r["stargazers_count"], r["id"]))

    def __call__(self, req: Any) -> Resp:
        self.calls += 1
        self.urls.append(req.full_url)
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(req.full_url).query)
        q, page, per = qs["q"][0], int(qs["page"][0]), int(qs["per_page"][0])
        for h in self.hooks:
            r = h(self, q, page, per)
            if r is not None:
                return r
        if page * per > 1000:
            raise urllib.error.HTTPError(req.full_url, 422, "only first 1000", {}, io.BytesIO(b""))
        ms = self.match(q)
        return Resp({"total_count": len(ms), "incomplete_results": False,
                     "items": ms[(page - 1) * per: page * per]})


def population(n: int, seed: int = 1, star_lo: int = 1000, star_hi: int = 60000) -> list[dict[str, Any]]:
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        stars = int(star_lo + (star_hi - star_lo) * rnd.random() ** 4)  # dense at low stars
        day = dt.date(2010, 1, 1) + dt.timedelta(days=rnd.randrange(5000))
        out.append({"id": 10_000 + i, "full_name": f"o{i}/r{i}", "stargazers_count": stars,
                    "created_at": f"{day.isoformat()}T00:00:00Z", "pushed_at": "2026-09-01T00:00:00Z"})
    return out


def top_ids(repos: list[dict[str, Any]], k: int = 1000) -> dict[int, str]:
    s = sorted(repos, key=lambda r: (-r["stargazers_count"], r["id"]))[:k]
    return {r["id"]: r["full_name"] for r in s}


@pytest.fixture()
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    monkeypatch.setenv("GITHUB_TOKEN", "dummy-not-a-secret")

    def make(repos: list[dict[str, Any]], **kw: Any) -> tuple[FakeGitHub, Any]:
        fake = FakeGitHub(repos)
        out = tmp_path / f"probe{random.random()}"
        out.mkdir()
        return fake, (lambda b0, **k2: P.probe(C.Client(out, False, opener=fake), b0, **{**kw, **k2}))

    return make


# ---- partition ---------------------------------------------------------------------------------
def test_split_tiles_exactly() -> None:
    rnd = random.Random(7)
    for _ in range(500):
        lo = rnd.randint(1000, 50000)
        hi = lo + rnd.randint(1, 50000)
        a, b = P.Band(lo, hi).split()  # type: ignore[misc]
        assert a.lo == lo and b.hi == hi and b.lo == a.hi + 1  # type: ignore[operator]
    a, b = P.Band(1000, None).split()  # type: ignore[misc]
    assert (a.lo, a.hi, b.lo, b.hi) == (1000, 1999, 2000, None)
    a, b = P.Band(1234, 1234).split()  # type: ignore[misc]
    assert a.dlo == P.DAY_LO and b.dhi == P.DAY_HI and b.dlo == a.dhi + 1  # type: ignore[operator]
    assert P.Band(1234, 1234, 800000, 800000).split() is None


def test_tiling_checker_detects_gap_and_overlap() -> None:
    good = [P.Band(1000, 1999), P.Band(2000, None)]
    assert P.tiling_ok(good)
    assert not P.tiling_ok([P.Band(1000, 1998), P.Band(2000, None)])
    assert not P.tiling_ok([P.Band(1000, 2000), P.Band(2000, None)])
    assert not P.tiling_ok([P.Band(1000, 1999)])


# ---- end-to-end --------------------------------------------------------------------------------
def test_exact_count_and_never_exceeds_1000_results(env: Any) -> None:
    repos = population(2600)
    fake, run = env(repos)
    r = run(top_ids(repos))
    assert r["outcome"] == "EXACT", r["checks"]
    assert r["M_v"] == 1600 and r["S_W"] == 2600
    assert r["decision"].startswith("ELIGIBLE-TO-PROPOSE")
    assert all(b["T"] < 900 for b in r["bands"])
    for u in fake.urls:
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(u).query)
        assert int(qs["page"][0]) * int(qs["per_page"][0]) <= 1000
    assert r["projections_non_decisive"]["decile10"] == pytest.approx(1600 * 0.82)


def test_dense_single_star_uses_created_partition(env: Any) -> None:
    repos = population(1200, seed=2)
    for i in range(950):  # 950 repos at exactly 1000 stars, different creation days
        repos[i]["stargazers_count"] = 1000
    fake, run = env(repos)
    r = run(top_ids(repos))
    assert r["outcome"] == "EXACT", r["checks"]
    assert any("created:" in b["query"] for b in r["bands"])
    assert r["S_W"] == 1200


def test_unenumerable_partition_is_incomplete_with_lower_bound(env: Any) -> None:
    repos = population(1300, seed=3)
    for i in range(950):  # same star value AND same creation day
        repos[i]["stargazers_count"] = 1000
        repos[i]["created_at"] = "2015-05-05T00:00:00Z"
    fake, run = env(repos)
    r = run(top_ids(repos))
    assert r["outcome"] == "INCOMPLETE" and r["M_v"] is None
    assert r["M_v_lower_bound"] <= 1300 - 1000
    assert any(b["status"] == "unenumerable" for b in r["bands"])
    assert r["projections_non_decisive"]["decile10"] is None


def test_duplicates_across_pages_are_counted_once(env: Any) -> None:
    repos = population(1500, seed=4)
    fake, run = env(repos)

    def dup(f: FakeGitHub, q: str, page: int, per: int) -> Resp | None:
        if page == 2 and per == 100:
            ms = f.match(q)
            return Resp({"total_count": len(ms), "incomplete_results": False,
                         "items": ms[99:199]})  # page 2 repeats the last item of page 1
        return None

    fake.hooks.append(dup)
    r = run(top_ids(repos))
    assert r["S_W"] <= 1500 and len(set().union(*[set(b["ids"]) for b in r["bands"]])) == r["S_W"]


def test_skipped_items_trigger_reenumeration_and_recover(env: Any) -> None:
    repos = population(1500, seed=5)
    fake, run = env(repos)

    def skip(f: FakeGitHub, q: str, page: int, per: int) -> Resp | None:
        if page == 2 and per == 100:  # first pass silently loses 6 items
            ms = f.match(q)
            return Resp({"total_count": len(ms), "incomplete_results": False,
                         "items": ms[106:200]})
        return None

    fake.hooks.append(skip)
    r = run(top_ids(repos))
    assert any(b["reenumerated"] for b in r["bands"])
    assert r["outcome"] == "EXACT", r["checks"]
    assert r["S_W"] == 1500


def test_persistent_count_mismatch_is_incomplete(env: Any) -> None:
    repos = population(1500, seed=6)
    fake, run = env(repos)

    def inflate(f: FakeGitHub, q: str, page: int, per: int) -> Resp | None:
        if "stars:1000.." in q and per != 1:
            ms = f.match(q)
            return Resp({"total_count": len(ms) + 20, "incomplete_results": False,
                         "items": ms[(page - 1) * per: page * per]})
        return None

    fake.hooks.append(inflate)
    r = run(top_ids(repos))
    assert r["outcome"] == "INCOMPLETE" and not r["checks"]["C2_counts_agree"]


def test_incomplete_results_flag_is_incomplete(env: Any) -> None:
    repos = population(1500, seed=7)
    fake, run = env(repos)

    def flag(f: FakeGitHub, q: str, page: int, per: int) -> Resp | None:
        if page == 1 and per == 100 and "stars:2000" in q:
            ms = f.match(q)
            return Resp({"total_count": len(ms), "incomplete_results": True, "items": ms[:100]})
        return None

    fake.hooks.append(flag)
    r = run(top_ids(repos))
    assert r["outcome"] == "INCOMPLETE" and not r["checks"]["C6_no_unresolved"]


def test_api_failure_is_incomplete_and_422_is_stopped(env: Any) -> None:
    repos = population(1500, seed=8)
    fake, run = env(repos)

    def fail(f: FakeGitHub, q: str, page: int, per: int) -> Resp | None:
        if page == 2 and per == 100 and "stars:1000.." in q:
            raise urllib.error.HTTPError("u", 500, "boom", {}, io.BytesIO(b""))  # not retried
        return None

    fake.hooks.append(fail)
    r = run(top_ids(repos))
    assert r["outcome"] == "INCOMPLETE" and any(b["status"] == "failed" for b in r["bands"])

    fake2, run2 = env(repos)
    fake2.hooks.append(lambda f, q, page, per: (_ for _ in ()).throw(
        urllib.error.HTTPError("u", 422, "bad", {}, io.BytesIO(b""))))
    r2 = run2(top_ids(repos))
    assert r2["outcome"] == "STOPPED" and "M_v" not in r2


def test_call_cap_and_time_cap(env: Any) -> None:
    repos = population(2600, seed=9)
    fake, run = env(repos, max_calls=12)
    r = run(top_ids(repos))
    assert r["outcome"] == "INCOMPLETE" and r["cap_reached"] and r["calls"] == 12
    assert r["M_v_lower_bound"] < 1600

    clock = iter(range(0, 10**6, 1000))
    fake2, run2 = env(repos, now=lambda: next(clock), max_seconds=5000)
    r2 = run2(top_ids(repos))
    assert r2["outcome"] == "INCOMPLETE" and r2["cap_reached"]


def test_star_mover_recovered_by_boundary_sweep(env: Any) -> None:
    repos = population(1500, seed=10)
    mover = {"id": 1, "full_name": "mv/mv", "stargazers_count": 2001,
             "created_at": "2020-01-01T00:00:00Z", "pushed_at": "2026-09-01T00:00:00Z"}
    repos.append(mover)
    fake, run = env(repos)
    state = {"moved": False}

    def move(f: FakeGitHub, q: str, page: int, per: int) -> Resp | None:
        # after the [1000, 1999] band is enumerated, move the repo from 2001 to 1998 stars
        if not state["moved"] and re.search(r"stars:(>=2000|20\d\d\.\.)", q):
            mover["stargazers_count"] = 1998
            state["moved"] = True
        return None

    fake.hooks.append(move)
    r = run(top_ids(repos))
    assert not any(1 in b["ids"] for b in r["bands"])  # missed by every band...
    assert sum(s["recovered"] for s in r["sweeps"]) == 1  # ...recovered by the boundary sweep
    assert r["S_W"] == 1501 and r["outcome"] == "EXACT"


def test_rename_does_not_inflate_m_v_and_recall_check(env: Any) -> None:
    repos = population(2600, seed=11)
    b0 = top_ids(repos)
    next(r for r in repos if r["id"] in b0)["full_name"] = "renamed/after-tsel"
    fake, run = env(repos)
    r = run(b0)
    assert r["outcome"] == "EXACT" and r["M_v"] == 1600  # id matching: rename not counted as unseen

    gone = set(list(b0)[:10])
    repos2 = [x for x in repos if x["id"] not in gone]
    fake2, run2 = env(repos2)
    r2 = run2(b0)
    assert len(r2["baseline_missing_ids"]) == 10 and not r2["checks"]["C4_baseline_recall"]
    assert r2["outcome"] == "INCOMPLETE"


@pytest.mark.parametrize("m,exp", [(62, "STOP-POLICY"), (63, "RD-JUDGMENT"), (499, "RD-JUDGMENT"),
                                   (500, "ELIGIBLE-TO-PROPOSE"), (None, "INCOMPLETE")])
def test_decision_thresholds(m: int | None, exp: str) -> None:
    assert P.decide("EXACT" if m is not None else "INCOMPLETE", m).startswith(exp)


# ---- baseline, lock, evidence ------------------------------------------------------------------
def make_copy(root: Path, with_ids: bool = True) -> tuple[Path, str]:
    copy = root / "run1copy"
    (copy / "cache").mkdir(parents=True)
    for page in range(1, 11):
        items = [{"full_name": f"b{page}/{i}", "stargazers_count": 9000 - page * 100 - i,
                  **({"id": page * 1000 + i} if with_ids else {})} for i in range(100)]
        rec = {"request": ["GET", "u", None], "response": {"total_count": 4776, "items": items}}
        (copy / "cache" / f"{P.search_key(page)}.json").write_text(json.dumps(rec), encoding="utf-8")
    return copy, P.manifest_sha(copy)


def test_baseline_loader_reads_ids_and_refuses_defects(tmp_path: Path) -> None:
    copy, man = make_copy(tmp_path)
    b0 = P.load_baseline(copy, expected_manifest=man)
    assert len(b0) == 1000
    with pytest.raises(P.Stop):
        P.load_baseline(copy)  # real run-1 manifest expected -> mismatch
    copy2, man2 = make_copy(tmp_path / "x", with_ids=False)
    with pytest.raises(P.Stop):
        P.load_baseline(copy2, expected_manifest=man2)


def test_baseline_loader_is_read_only(tmp_path: Path) -> None:
    copy, man = make_copy(tmp_path)
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in copy.rglob("*") if p.is_file()}
    P.load_baseline(copy, expected_manifest=man)
    after = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in copy.rglob("*") if p.is_file()}
    assert before == after


def test_live_mode_is_locked_and_makes_no_request(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    assert P.FROZEN_PROTOCOL_SHA is None
    monkeypatch.setenv("P4_PROBE_PR2", "AUTHORIZED")
    ok, why = P.live_authorized()
    assert not ok and why.startswith("LOCKED")

    def boom(*a: Any, **k: Any) -> Any:
        raise AssertionError("network attempted")

    monkeypatch.setattr(C.urllib.request, "urlopen", boom)
    assert P.main(["run", "--out", str(tmp_path / "o"), "--baseline", str(tmp_path)]) == 3
    assert not (tmp_path / "o").exists()


def test_evidence_manifest_matches_files(tmp_path: Path) -> None:
    out = tmp_path / "ev"
    (out / "cache").mkdir(parents=True)
    (out / "cache" / "a.json").write_text("{}", encoding="utf-8")
    sha = P.write_evidence(out, {"outcome": "EXACT"}, {"m": 1})
    data = (out / "MANIFEST.sha256").read_text(encoding="utf-8")
    assert hashlib.sha256(data.encode()).hexdigest() == sha
    for line in data.splitlines():
        h, rel = line.split("  ", 1)
        assert hashlib.sha256((out / rel).read_bytes()).hexdigest() == h


def test_protocol_block_sha_is_computable() -> None:
    assert len(P.protocol_block_sha()) == 64


# ---- v0.3 pre-freeze audit blockers ------------------------------------------------------------
def test_library_probe_is_locked_even_with_env_set(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "dummy-not-a-secret")
    monkeypatch.setenv("P4_PROBE_PR2", "AUTHORIZED")
    attempts: list[str] = []

    def recorder(req: Any, timeout: Any = None) -> Any:
        attempts.append(req.full_url)
        raise AssertionError("network attempted")

    monkeypatch.setattr(C.urllib.request, "urlopen", recorder)
    out = tmp_path / "o"
    out.mkdir()
    r = P.probe(C.Client(out, offline=False), {})  # default (real) opener, not a test double
    assert r["outcome"] == "STOPPED" and "LOCKED" in r["reason"] and attempts == []
    assert not any((out / "cache").iterdir())


def test_unmarked_custom_opener_is_refused_while_locked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "dummy-not-a-secret")
    hits: list[Any] = []
    out = tmp_path / "o"
    out.mkdir()
    r = P.probe(C.Client(out, False, opener=lambda req: hits.append(req)), {})
    assert r["outcome"] == "STOPPED" and hits == []


def test_urlopen_stub_blocks_real_calls_during_test_double_runs(env: Any) -> None:
    repos = population(1200, seed=30)
    fake, run = env(repos)
    seen: list[Any] = []

    def sneaky(f: FakeGitHub, q: str, page: int, per: int) -> Resp | None:
        if not seen:
            seen.append(1)
            import urllib.request as ur
            ur.urlopen("https://api.github.com/")  # must hit the Locked stub, never the network
        return None

    fake.hooks.append(sneaky)
    r = run(top_ids(repos))
    assert r["outcome"] == "STOPPED" and "LOCKED" in r["reason"]


class _CreatedExclusive(FakeGitHub):
    def match(self, q: str) -> list[dict[str, Any]]:
        c = re.search(r"created:(\S+)\.\.(\S+)", q)
        base = super().match(re.sub(r" created:\S+", "", q))
        return [r for r in base if not c or c.group(1) <= r["created_at"][:10] < c.group(2)]


class _StarsExclusive(FakeGitHub):
    def match(self, q: str) -> list[dict[str, Any]]:
        m = re.search(r"stars:(\d+)\.\.(\d+)", q)
        base = super().match(q)
        return [r for r in base if not m or r["stargazers_count"] < int(m.group(2))]


@pytest.mark.parametrize("cls", [_CreatedExclusive, _StarsExclusive])
def test_semantic_calibration_stops_on_range_mismatch(cls: Any, tmp_path: Path,
                                                      monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "dummy-not-a-secret")
    repos = population(1300, seed=22)
    fake = cls(repos)
    out = tmp_path / "o"
    out.mkdir()
    r = P.probe(C.Client(out, False, opener=fake), top_ids(repos))
    assert r["outcome"] == "STOPPED" and "calibration" in r["reason"]


def test_calibration_passes_and_is_recorded(env: Any) -> None:
    repos = population(1500, seed=31)
    fake, run = env(repos)
    r = run(top_ids(repos))
    assert r["outcome"] == "EXACT" and r["checks"]["S0_calibration"] and r["calibration"]["attempt"] == 1
    assert r["exact_semantics"].startswith("EXACT = ") and "NOT a guarantee" in r["exact_semantics"]


def test_t_end_is_fresh_not_cached(env: Any) -> None:
    repos = population(1500, seed=32)
    extra = population(200, seed=33)
    for i, x in enumerate(extra):
        x["id"] = 900_000 + i
        x["full_name"] = f"late{i}/r"
    fake, run = env(repos)

    def grow(f: FakeGitHub, q: str, page: int, per: int) -> Resp | None:
        if per == 2 and not any(r["id"] >= 900_000 for r in f.repos):  # just before T_end
            f.repos.extend(extra)
        return None

    fake.hooks.append(grow)
    r = run(top_ids(repos))
    assert r["T_end"] == r["T_start"] + 200 and not r["checks"]["C3_drift"] and r["outcome"] == "INCOMPLETE"


def test_every_url_is_unique_across_phases(env: Any) -> None:
    repos = population(2600, seed=34)
    fake, run = env(repos)
    r = run(top_ids(repos))
    assert r["outcome"] == "EXACT"
    assert len(fake.urls) == len(set(fake.urls))  # no cache reuse anywhere in a clean run


def test_cross_phase_repeat_raises_stop() -> None:
    class Cl:
        failures: list[Any] = []

        def call(self, *a: Any, **k: Any) -> Any:
            return {"total_count": 0, "items": []}

    p = P.Prober(Cl(), {})
    p.search("q", 1, 100, "band")
    with pytest.raises(P.Stop):
        p.search("q", 1, 100, "sweep")


def test_out_path_guard(tmp_path: Path) -> None:
    base = tmp_path / "copy"
    base.mkdir()
    prot = (tmp_path / "run1", tmp_path / "archive")
    for bad in (base / "probe", tmp_path / "run1" / "x", tmp_path / "archive" / "p", base):
        with pytest.raises(P.Stop):
            P.check_out_path(bad, base, prot)
    existing = tmp_path / "exists"
    existing.mkdir()
    with pytest.raises(P.Stop):
        P.check_out_path(existing, base, prot)
    P.check_out_path(tmp_path / "probe1-new", base, prot)  # allowed, nothing created
    assert not (tmp_path / "probe1-new").exists()


def test_baseline_summary_flags_name_id_inconsistency(tmp_path: Path) -> None:
    copy, man = make_copy(tmp_path)
    f = copy / "cache" / f"{P.search_key(1)}.json"
    rec = json.loads(f.read_text(encoding="utf-8"))
    rec["response"]["items"][1]["full_name"] = rec["response"]["items"][0]["full_name"]  # 2 ids, 1 name
    f.write_text(json.dumps(rec), encoding="utf-8")
    s = P.baseline_summary(copy, expected_manifest=P.manifest_sha(copy))
    assert not s["ok"] and s["names_with_multiple_ids"]
    with pytest.raises(P.Stop):
        P.load_baseline(copy, expected_manifest=P.manifest_sha(copy))


def test_baseline_check_cli_is_read_only(
    tmp_path: Path, capsys: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    copy, man = make_copy(tmp_path)
    monkeypatch.setattr(P, "RUN1_MANIFEST_SHA", man)
    monkeypatch.setattr(P.baseline_summary, "__defaults__", (man,))
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in copy.rglob("*") if p.is_file()}
    assert P.main(["baseline-check", "--baseline", str(copy)]) == 0
    assert "BASELINE_OK" in capsys.readouterr().out
    after = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in copy.rglob("*") if p.is_file()}
    assert before == after
