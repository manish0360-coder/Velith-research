#!/usr/bin/env python3
"""P2 FG-3 lottery (P2_SPEC.md §9–§11): eligible pool plus deterministic order. Nothing else.

There is no image pull, no admission and no model call. The admission walk, with its cap of 4
per repository and no backfill, is implemented here as the pure function `walk`, but it is only
executed in FG-4. The frozen P1 lottery helpers are imported read-only and pinned by SHA-256.

Usage (WSL; run from the research repo root):
    python3 -B p2/harness/p2_lottery.py selftest     # synthetic checks only, no network
    python3 -B p2/harness/p2_lottery.py run          # selftest, then revision check, fetch,
                                                      # revision check, pool, order
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from collections import Counter
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parents[1]
OUT = RESEARCH / "p2" / "evidence" / "_lottery"
SPEC = RESEARCH / "p2" / "P2_SPEC.md"
SPEC_SHA256 = "b2d29c5cdfba65b24c514763412c0807704c88f52d39e663f3fc6cc7a6d21c32"
REGISTRY = RESEARCH / "p2" / "P2_EXCLUSION_REGISTRY.json"
REGISTRY_SHA256 = "37e8fc718e176766e066af0d3db59fbc3836c3683f2a7d61563ff03277961123"
P1_LOTTERY = RESEARCH / "stage0" / "p1env" / "p1_lottery.py"
P1_LOTTERY_SHA256 = "7ae70326b794850e91efd882d7262adfc528c8b970b52cbca463db3e53cedf60"

DATASET = "SWE-bench/SWE-bench_Verified"
REVISION = "78f471bf655a3137b2e8a75af1501690ec009ec3"  # D3
SALT = "|velith-m2pv-p2-pilot-v1"  # §10
REPOS = ("pallets/flask", "matplotlib/matplotlib", "scikit-learn/scikit-learn",
         "astropy/astropy", "pydata/xarray")  # G-1
CAP, N_TARGET = 4, 20  # D3
SUSPICIOUS = re.compile(r"\s")  # (g), with the bracket-balance rule below


class LotteryStop(Exception):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canon(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def dump(obj: Any) -> bytes:
    return (json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def p1_lottery() -> Any:
    """The frozen P1 lottery helpers (rows, as_list, is_test, DIFF_FILE, dataset_revision)."""
    if "p1_lottery" in sys.modules:
        return sys.modules["p1_lottery"]
    if sha256_bytes(P1_LOTTERY.read_bytes()) != P1_LOTTERY_SHA256:
        raise LotteryStop("stage0/p1env/p1_lottery.py differs from its frozen SHA-256")
    spec = importlib.util.spec_from_file_location("p1_lottery", P1_LOTTERY)
    if spec is None or spec.loader is None:
        raise LotteryStop("cannot import p1_lottery")
    module = importlib.util.module_from_spec(spec)
    sys.modules["p1_lottery"] = module
    spec.loader.exec_module(module)
    return module


# ---- eligibility (§9): (a)–(e) as frozen in P1 §7, plus (g) -----------------------------------
def first_failing_filter(r: dict[str, Any]) -> str | None:
    """None if eligible. (a) the pytest command holds for all five repositories (P1 design §7(a);
    flask: P1 T1 admission ran pytest via the frozen probe), so it is not a per-row test."""
    lot = p1_lottery()
    tp = sorted(set(lot.DIFF_FILE.findall(r["test_patch"])))
    gold = sorted(set(lot.DIFF_FILE.findall(r["patch"])))
    f2p, p2p = lot.as_list(r["FAIL_TO_PASS"]), lot.as_list(r["PASS_TO_PASS"])
    if not all(p.endswith(".py") for p in tp):
        return "b_test_patch_not_py"
    if len(p2p) < 1:
        return "c_no_pass_to_pass"
    if not 1 <= len(f2p) <= 5:
        return "d_fail_to_pass_count"
    if not (len([g for g in gold if not lot.is_test(g)]) == 1 and all(not lot.is_test(g)
                                                                     for g in gold)):
        return "e_gold_not_single_nontest_file"
    if any(SUSPICIOUS.search(i) or i.count("[") != i.count("]") for i in [*f2p, *p2p]):
        return "g_test_id_screen"
    return None


def key(instance_id: str) -> str:
    return sha256_bytes((instance_id + SALT).encode("utf-8"))


def registry_ids() -> list[str]:
    if sha256_bytes(REGISTRY.read_bytes()) != REGISTRY_SHA256:
        raise LotteryStop("P2_EXCLUSION_REGISTRY.json differs from its FG-1 SHA-256")
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    ids = [e["instance_id"] for e in reg["initial_holdout"]]
    if len(ids) != 11 or len(set(ids)) != 11 or reg["p2_appended"]:
        raise LotteryStop("registry is not in its FG-1 state (11 initial IDs, nothing appended)")
    return ids


def build_pool(rows: Sequence[dict[str, Any]], excluded: Sequence[str]) -> dict[str, Any]:
    stats: dict[str, Counter[str]] = {repo: Counter() for repo in REPOS}
    eligible: list[dict[str, str]] = []
    excl = set(excluded)
    seen: set[str] = set()
    for r in rows:
        iid = r["instance_id"]
        if iid in seen:
            raise LotteryStop(f"duplicate dataset row {iid}")
        seen.add(iid)
        if r["repo"] not in stats:
            continue
        s = stats[r["repo"]]
        s["rows"] += 1
        fail = first_failing_filter(r)
        if fail:
            s[fail] += 1
            continue
        if iid in excl:
            s["excluded_registry"] += 1
            continue
        s["eligible"] += 1
        eligible.append({"instance_id": iid, "repo": r["repo"], "row_sha256":
                         sha256_bytes(canon(r))})
    eligible.sort(key=lambda e: e["instance_id"])
    if excl & {e["instance_id"] for e in eligible}:
        raise LotteryStop("a registry hold-out ID entered the pool")
    return {"eligible": eligible, "per_repo": {k: dict(sorted(v.items())) for k, v in
                                              stats.items()}}


def order(eligible: Sequence[dict[str, str]]) -> list[dict[str, Any]]:
    ranked = sorted(eligible, key=lambda e: (key(e["instance_id"]), e["instance_id"]))
    per_repo: Counter[str] = Counter()
    out = []
    for i, e in enumerate(ranked, start=1):
        per_repo[e["repo"]] += 1
        out.append({"rank": i, "instance_id": e["instance_id"], "repo": e["repo"],
                    "key": key(e["instance_id"]), "repo_rank": per_repo[e["repo"]]})
    return out


def walk(ordered: Sequence[tuple[str, str]], admit: Callable[[str], bool], cap: int = CAP,
         n: int = N_TARGET) -> tuple[list[str], list[dict[str, Any]]]:
    """§10 admission walk (executed in FG-4): global order; skip a repository at the cap; continue
    past inadmissible tasks; stop at n or exhaustion. No backfill beyond the cap."""
    admitted: list[str] = []
    per_repo: Counter[str] = Counter()
    log: list[dict[str, Any]] = []
    for iid, repo in ordered:
        if len(admitted) == n:
            break
        if per_repo[repo] >= cap:
            log.append({"instance_id": iid, "outcome": "skipped_repo_at_cap"})
            continue
        ok = admit(iid)
        log.append({"instance_id": iid, "outcome": "admitted" if ok else "inadmissible"})
        if ok:
            admitted.append(iid)
            per_repo[repo] += 1
    return admitted, log


# ---- synthetic self-test (runs before any network access) -------------------------------------
def _row(iid: str, repo: str, *, f2p: int = 1, p2p: int = 2, test_files: tuple[str, ...] = (
        "pkg/tests/test_x.py",), gold: tuple[str, ...] = ("pkg/x.py",), ids: tuple[str, ...] = ()
         ) -> dict[str, Any]:
    def diff(paths: tuple[str, ...]) -> str:
        return "".join(f"diff --git a/{p} b/{p}\n--- a/{p}\n+++ b/{p}\n" for p in paths)
    f = [f"pkg/tests/test_x.py::t{i}" for i in range(f2p)]
    p = list(ids) or [f"pkg/tests/test_x.py::p{i}" for i in range(p2p)]
    return {"instance_id": iid, "repo": repo, "test_patch": diff(test_files), "patch": diff(gold),
            "FAIL_TO_PASS": json.dumps(f), "PASS_TO_PASS": json.dumps(p)}


def selftest() -> None:
    p1_lottery()
    if sha256_bytes(SPEC.read_bytes()) != SPEC_SHA256:
        raise LotteryStop("P2_SPEC.md differs from the FG-0 frozen specification")
    ids = registry_ids()
    R = "pydata/xarray"
    cases = {
        None: _row("a__a-1", R),
        "b_test_patch_not_py": _row("a__a-2", R, test_files=("pkg/tests/data.txt",)),
        "c_no_pass_to_pass": _row("a__a-3", R, p2p=0),
        "d_fail_to_pass_count": _row("a__a-4", R, f2p=6),
        "e_gold_not_single_nontest_file": _row("a__a-5", R, gold=("pkg/x.py", "pkg/y.py")),
        "g_test_id_screen": _row("a__a-6", R, ids=("t.py::test_x[a b]",)),
    }
    for expect, r in cases.items():
        assert first_failing_filter(r) == expect, (expect, first_failing_filter(r))
    assert first_failing_filter(_row("a__a-7", R, ids=("t.py::test_x[a",))) == "g_test_id_screen"
    assert first_failing_filter(_row("a__a-8", R, gold=("pkg/tests/test_y.py",))) is not None
    rows = [_row(f"{repo.split('/')[1]}__x-{i}", repo) for repo in REPOS for i in range(6)]
    rows += [_row(ids[0], "pallets/flask"), _row("other__repo-1", "psf/requests")]
    pool = build_pool(rows, ids)
    assert ids[0] not in {e["instance_id"] for e in pool["eligible"]}
    assert pool["per_repo"]["pallets/flask"]["excluded_registry"] == 1
    assert all(e["repo"] in REPOS for e in pool["eligible"]) and len(pool["eligible"]) == 30
    o1, o2 = order(pool["eligible"]), order(list(reversed(pool["eligible"])))
    assert o1 == o2 and [x["rank"] for x in o1] == list(range(1, 31))  # input-order invariant
    assert all(o1[i]["key"] <= o1[i + 1]["key"] for i in range(len(o1) - 1))
    pairs = [(x["instance_id"], x["repo"]) for x in o1]
    adm, _ = walk(pairs, lambda _i: True)
    assert len(adm) == 20 and max(Counter(r for i, r in pairs if i in adm).values()) == 4
    short = [p for p in pairs if p[1] != "pallets/flask" or p[0].endswith(("-0", "-1"))]
    adm2, _ = walk(short, lambda _i: True)  # flask has only 2: no backfill -> n = 18
    assert len(adm2) == 18 and Counter(r for i, r in short if i in adm2)["pallets/flask"] == 2
    adm3, log3 = walk(pairs, lambda i: not i.endswith("-0"))  # inadmissible -> continue walking
    assert len(adm3) == 20 and all(not i.endswith("-0") for i in adm3)
    assert any(e["outcome"] == "inadmissible" for e in log3)
    try:
        build_pool([*rows, rows[0]], ids)
        raise AssertionError("duplicate row not detected")
    except LotteryStop:
        pass


# ---- execution (FG-3) -------------------------------------------------------------------------
def run() -> int:
    if OUT.exists():
        raise LotteryStop(f"{OUT} exists: FG-3 artifacts are written once")
    selftest()
    lot = p1_lottery()
    rev_before = lot.dataset_revision()
    if rev_before != REVISION:
        raise LotteryStop(f"dataset revision before fetch {rev_before} != {REVISION}")
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = lot.rows()
    rev_after = lot.dataset_revision()
    if rev_after != REVISION:
        raise LotteryStop(f"dataset revision after fetch {rev_after} != {REVISION}")
    shared = [r for r in rows if r["repo"] in REPOS and r["repo"] in lot.REPOS]
    mismatch = [r["instance_id"] for r in shared
                if (first_failing_filter(r) in (None, "g_test_id_screen")) != lot.eligible(r)]
    if mismatch:  # (a)–(e) must equal the frozen P1 predicate on the shared repositories
        raise LotteryStop(f"(a)-(e) disagree with frozen P1 eligibility: {mismatch[:5]}")
    ids = registry_ids()
    pool = build_pool(rows, ids)
    ordered = order(pool["eligible"])
    rows_digest = sha256_bytes(canon(sorted((r["instance_id"], sha256_bytes(canon(r)))
                                            for r in rows)))
    prov = {"dataset": DATASET, "revision_required": REVISION, "revision_before": rev_before,
            "revision_after": rev_after, "fetched_utc": started, "rows_fetched": len(rows),
            "rows_digest_sha256": rows_digest, "source": "datasets-server rows API via frozen "
            "p1_lottery.rows()", "spec_sha256": SPEC_SHA256, "registry_sha256": REGISTRY_SHA256,
            "p1_lottery_sha256": P1_LOTTERY_SHA256,
            "lottery_sha256": sha256_bytes(Path(__file__).read_bytes()),
            "p1_equivalence_rows_checked": len(shared)}
    queues = {repo: [x["instance_id"] for x in ordered if x["repo"] == repo] for repo in REPOS}
    preview, _ = walk([(x["instance_id"], x["repo"]) for x in ordered], lambda _i: True)
    OUT.mkdir(parents=True)
    (OUT / "pool.json").write_bytes(dump({"provenance": prov, "repos": list(REPOS),
                                          "filters": "(a)-(e) P1 §7; (g) D4 test-ID screen",
                                          "excluded_registry_ids": ids, **pool}))
    (OUT / "order.json").write_bytes(dump({
        "provenance": prov, "salt": SALT, "order": ordered, "per_repo_queue": queues,
        "walk_rule": "FG-4: global order; skip repo at cap 4; continue past inadmissible; stop "
                     "at n=20 or exhaustion; no backfill",
        "preview_if_every_candidate_admitted": preview,
        "preview_note": "NOT a selection. Admission (FG-4) decides; shown only to expose "
                        "the cap."}))
    files = sorted(p for p in OUT.iterdir() if p.is_file())
    (OUT / "MANIFEST.sha256").write_bytes("".join(
        f"{sha256_bytes(p.read_bytes())}  ./{p.name}\n" for p in files).encode())
    print(json.dumps({"revision_before": rev_before, "revision_after": rev_after,
                      "rows_fetched": len(rows), "eligible_total": len(pool["eligible"]),
                      "per_repo": pool["per_repo"],
                      "holdouts_in_pool": sorted(set(ids) & {e["instance_id"]
                                                             for e in pool["eligible"]}),
                      "pool_sha256": sha256_bytes((OUT / "pool.json").read_bytes()),
                      "order_sha256": sha256_bytes((OUT / "order.json").read_bytes())}, indent=2))
    return 0


def main(argv: list[str]) -> int:
    try:
        if argv[1:] == ["selftest"]:
            selftest()
            print("SELFTEST PASS")
            return 0
        if argv[1:] == ["run"]:
            return run()
        print(__doc__)
        return 2
    except (LotteryStop, AssertionError) as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
