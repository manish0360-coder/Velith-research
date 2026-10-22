"""Synthetic tests for the P4 supply census (no network).

Run: PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider \
     p4/census/test_supply_census.py
"""

from __future__ import annotations

import json
import sys
import urllib.error
from pathlib import Path
from typing import Any

import pytest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import supply_census as C  # noqa: E402

IN = "2026-09-01T00:00:00Z"
OLD = "2026-07-15T00:00:00Z"


def pr(
    num: int,
    created: str = IN,
    merged: str = IN,
    updated: str = IN,
    issues: list[str] | None = None,
    login: str = "dev",
    total: int | None = None,
) -> dict[str, Any]:
    nodes = [{"number": 1, "createdAt": d} for d in (issues if issues is not None else [IN])]
    return {
        "number": num,
        "createdAt": created,
        "mergedAt": merged,
        "updatedAt": updated,
        "author": {"login": login},
        "closingIssuesReferences": {
            "totalCount": len(nodes) if total is None else total,
            "nodes": nodes,
        },
    }


def detail(
    commit_dates: list[str] | None = None,
    files: list[str] | None = None,
    total_commits: int | None = None,
) -> dict[str, Any]:
    cds = commit_dates if commit_dates is not None else [IN]
    fs = files if files is not None else ["pkg/mod.py", "tests/test_mod.py"]
    return {
        "baseRefOid": "b" * 40,
        "headRefOid": "h" * 40,
        "commits": {
            "totalCount": len(cds) if total_commits is None else total_commits,
            "nodes": [{"commit": {"authoredDate": d, "committedDate": d}} for d in cds],
        },
        "files": {"totalCount": len(fs), "nodes": [{"path": f} for f in fs]},
    }


def compare(date: str = IN) -> dict[str, Any]:
    return {"merge_base_commit": {"commit": {"committer": {"date": date}}}}


def test_protocol_hash_matches_frozen_doc() -> None:
    assert C.protocol_sha() == C.PROTOCOL_SHA256


def test_window_and_stage1() -> None:
    assert C.in_window("2026-08-01T00:00:00Z") and not C.in_window("2026-10-12T00:00:00Z")
    assert C.stage1(pr(1))
    assert not C.stage1(pr(1, created=OLD))
    assert not C.stage1(pr(1, merged="2026-10-12T00:00:01Z"))
    assert not C.stage1(pr(1, login="dependabot[bot]"))


def test_stage2_all_closing_issues_post_cutoff() -> None:
    assert C.stage2(pr(1)) == "PASS"
    assert C.stage2(pr(1, issues=[])) == "FAIL"
    assert C.stage2(pr(1, issues=[IN, OLD])) == "FAIL"
    assert C.stage2(pr(1, issues=[IN], total=11)) == "UNDETERMINED"  # more refs than fetched


def test_stage3_earliest_commit() -> None:
    assert C.stage3(detail()) == "PASS"
    assert C.stage3(detail([IN, OLD])) == "FAIL"
    assert C.stage3(detail(total_commits=101)) == "UNDETERMINED"
    assert C.stage3(detail([])) == "UNDETERMINED"


@pytest.mark.parametrize(
    ("files", "ok"),
    [
        (["pkg/mod.py", "tests/test_mod.py"], True),
        (["pkg/mod.py", "pkg/test_mod.py"], True),
        (["pkg/mod.py", "pkg/mod_test.py"], True),
        (["pkg/mod.py", "conftest.py"], True),
        (["pkg/mod.py"], False),
        (["tests/test_mod.py"], False),
        (["docs/index.rst", "tests/test_x.py"], False),
    ],
)
def test_stage4_file_classification(files: list[str], ok: bool) -> None:
    assert C.stage4(detail(files=files))[0] is ok


def test_stage5_merge_base() -> None:
    assert C.stage5(compare()) == "PASS"
    assert C.stage5(compare(OLD)) == "FAIL"
    assert C.stage5(None) == "UNDETERMINED"


@pytest.mark.parametrize(
    ("n", "cls"),
    [
        (630, "PROCEED-TO-SPIKE"),
        (629, "SPIKE-DECIDES"),
        (197, "SPIKE-DECIDES"),
        (196, "WINDOW-INFEASIBLE"),
        (0, "WINDOW-INFEASIBLE"),
    ],
)
def test_decision_class_boundaries(n: int, cls: str) -> None:
    assert C.decision_class(n)["overall"] == {"status": "FINAL", "class": cls}


@pytest.mark.parametrize(
    ("name", "n", "cls"),
    [
        ("delta_0.15", 418, "PROCEED-TO-SPIKE"),
        ("delta_0.15", 417, "SPIKE-DECIDES"),
        ("delta_0.15", 209, "SPIKE-DECIDES"),
        ("delta_0.15", 208, "WINDOW-INFEASIBLE"),
        ("delta_0.10", 630, "PROCEED-TO-SPIKE"),
        ("delta_0.10", 629, "SPIKE-DECIDES"),
        ("delta_0.10", 315, "SPIKE-DECIDES"),
        ("delta_0.10", 314, "WINDOW-INFEASIBLE"),
    ],
)
def test_per_delta_boundaries(name: str, n: int, cls: str) -> None:
    assert C.decision_class(n)[name]["class"] == cls


def test_incomplete_data_never_yields_infeasible_or_spike_decides() -> None:
    for n in (0, 196, 300, 629):
        d = C.decision_class(n, n, complete_data=False)
        assert d["overall"]["status"] == "PROVISIONAL"
        assert d["overall"]["class"] == "NO-VERDICT (incomplete)"
        assert all(
            d[k]["class"] in ("PROCEED-TO-SPIKE", "NO-VERDICT (incomplete)") for k in C.SCENARIOS
        )
    d = C.decision_class(700, 700, complete_data=False)
    assert d["overall"] == {
        "status": "PROVISIONAL",
        "class": "PROCEED-TO-SPIKE",
        "basis": "lower bound",
        "class_at_lower_bound": "PROCEED-TO-SPIKE",
        "class_at_upper_bound": "PROCEED-TO-SPIKE",
    }


def test_undetermined_that_could_flip_the_class_makes_it_provisional() -> None:
    d = C.decision_class(190, 250, complete_data=True)  # 190 infeasible, 250 not
    assert d["overall"]["status"] == "PROVISIONAL"
    assert d["overall"]["class"] == "NO-VERDICT (incomplete)"
    assert C.decision_class(100, 120)["overall"] == {
        "status": "FINAL",
        "class": "WINDOW-INFEASIBLE",
    }


class FakeClient:
    def __init__(
        self,
        pages: list[list[dict[str, Any]]],
        details: dict[int, dict[str, Any]],
        compares: dict[int, dict[str, Any] | None],
        fail_pages: set[int] | None = None,
        always_next: bool = False,
    ) -> None:
        self.pages, self.details, self.compares = pages, details, compares
        self.fail_pages = fail_pages or set()
        self.always_next = always_next
        self.failures: list[dict[str, Any]] = []

    def gql(self, query: str, variables: dict[str, Any], tag: str) -> Any:
        if tag.startswith("prs:"):
            page = int(tag.rsplit(":", 1)[1])
            if page in self.fail_pages:
                self.failures.append({"tag": tag, "error": "HTTP 502"})
                return None
            if self.always_next:
                return {
                    "repository": {
                        "pullRequests": {
                            "pageInfo": {"hasNextPage": True, "endCursor": str(page)},
                            "nodes": [pr(10_000 + page)],
                        }
                    }
                }
            nodes = self.pages[page] if page < len(self.pages) else []
            return {
                "repository": {
                    "pullRequests": {
                        "pageInfo": {
                            "hasNextPage": page + 1 < len(self.pages),
                            "endCursor": str(page),
                        },
                        "nodes": nodes,
                    }
                }
            }
        if tag.startswith("detail:"):
            return {"repository": {f"p{k}": v for k, v in self.details.items()}}
        raise AssertionError(tag)

    def call(self, method: str, url: str, body: Any = None, tag: str = "") -> Any:
        num = int(tag.rsplit("#", 1)[1])
        return self.compares.get(num)


def test_walk_repo_funnel_and_paging_stop() -> None:
    page0 = [pr(1), pr(2, created=OLD), pr(3, issues=[OLD]), pr(4), pr(5), pr(6)]
    page1 = [pr(7, merged=OLD, updated=OLD)]  # whole page older -> stop
    page2 = [pr(8)]  # must never be read
    fc = FakeClient(
        [page0, page1, page2],
        {1: detail(), 4: detail([OLD]), 5: detail(files=["a.py"]), 6: detail()},
        {1: compare(), 6: compare(OLD)},
    )
    w = C.walk_repo(fc, "o/r")  # type: ignore[arg-type]
    assert (w["F0"], w["F1"], w["F2"], w["F3"], w["F4"], w["F5"]) == (6, 5, 4, 3, 2, 1)
    assert w["cands"] == [{"repo": "o/r", "number": 1, "merged_month": "2026-09"}]
    assert not w["page_cap_hit"]


def test_repo_filters() -> None:
    node = {
        "primaryLanguage": {"name": "Python"},
        "isFork": False,
        "isArchived": False,
        "pkg0": {"__typename": "Blob"},
        "tst0": {"__typename": "Tree"},
    }
    assert all(C.repo_ok(node).values())
    assert not C.repo_ok({**node, "pkg0": None})["U2_packaging"]
    assert not C.repo_ok({**node, "isFork": True})["U4_not_fork_archived"]


def test_duplicate_prs_across_pages_are_counted_once() -> None:
    fc = FakeClient(
        [[pr(1), pr(2)], [pr(2), pr(3)], [pr(9, merged=OLD, updated=OLD)]],
        {1: detail(), 2: detail(), 3: detail()},
        {1: compare(), 2: compare(), 3: compare()},
    )
    w = C.walk_repo(fc, "o/r")  # type: ignore[arg-type]
    assert w["F0"] == 3 and w["F5"] == 3 and w["duplicates_skipped"] == 1


def test_page_cap_is_flagged() -> None:
    fc = FakeClient([], {}, {}, always_next=True)
    w = C.walk_repo(fc, "o/r")  # type: ignore[arg-type]
    assert w["page_cap_hit"] is True and w["F0"] == C.PAGE_CAP


def test_failed_pr_page_is_recorded_not_silent() -> None:
    fc = FakeClient([[pr(1)]], {}, {}, fail_pages={0})
    w = C.walk_repo(fc, "o/r")  # type: ignore[arg-type]
    assert w["F0"] == 0 and fc.failures == [{"tag": "prs:o/r:0", "error": "HTTP 502"}]


def test_undetermined_and_truncated_counters() -> None:
    big = detail(files=["docs/a.md"])
    big["files"]["totalCount"] = 150  # truncated and failing F4 -> possible missed candidate
    fc = FakeClient(
        [[pr(1), pr(2), pr(3), pr(4, issues=[IN], total=12)]],
        {1: detail(total_commits=101), 2: big, 3: detail()},
        {3: None},
    )
    w = C.walk_repo(fc, "o/r")  # type: ignore[arg-type]
    assert w["F2_undetermined"] == 1 and w["F3_undetermined"] == 1
    assert w["F4_truncated_excluded"] == 1 and w["F5_undetermined"] == 1 and w["F5"] == 0


class FakeResponse:
    def __init__(self, payload: Any, remaining: str = "4000") -> None:
        self.payload = payload
        self.headers = {"X-RateLimit-Remaining": remaining, "X-RateLimit-Reset": "0"}

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *a: Any) -> None:
        return None


def make_client(
    tmp: Path, payloads: list[Any], monkeypatch: pytest.MonkeyPatch, offline: bool = False
) -> C.Client:
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_SECRET_TOKEN_VALUE")
    monkeypatch.setattr("supply_census.time.sleep", lambda s: None)
    seq = list(payloads)

    def opener(req: Any) -> Any:
        item = seq.pop(0)
        if isinstance(item, Exception):
            raise item
        return FakeResponse(item)

    return C.Client(tmp, offline, opener=opener)


def test_graphql_partial_errors_are_recorded_live_and_cached(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    resp = {"data": {"repository": None}, "errors": [{"type": "NOT_FOUND"}]}
    cl = make_client(tmp_path, [resp], monkeypatch)
    assert cl.gql("q", {"o": "a"}, "prs:a/b:0") == {"repository": None}
    assert len(cl.failures) == 1 and "partial error" in cl.failures[0]["error"]
    cl2 = make_client(tmp_path, [], monkeypatch, offline=True)  # from cache, offline
    cl2.gql("q", {"o": "a"}, "prs:a/b:0")
    assert len(cl2.failures) == 1 and "partial error" in cl2.failures[0]["error"]


def test_http_failure_is_recorded_not_cached_and_visible_offline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    err = urllib.error.HTTPError("u", 404, "nf", None, None)  # type: ignore[arg-type]
    cl = make_client(tmp_path, [err], monkeypatch)
    assert cl.call("GET", "https://api.github.com/x", tag="t") is None
    assert cl.failures == [{"tag": "t", "error": "HTTP 404"}]
    assert not list((tmp_path / "cache").glob("*.json"))
    off = make_client(tmp_path, [], monkeypatch, offline=True)
    assert off.call("GET", "https://api.github.com/x", tag="t") is None
    assert off.failures == [{"tag": "t", "error": "not in cache (offline)"}]


def test_retry_then_success_and_resume_from_cache_without_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    err = urllib.error.HTTPError("u", 502, "bad", None, None)  # type: ignore[arg-type]
    cl = make_client(tmp_path, [err, {"items": []}], monkeypatch)
    assert cl.call("GET", "https://api.github.com/y", tag="t") == {"items": []}
    assert not cl.failures and not list((tmp_path / "cache").glob("*.tmp"))
    resumed = make_client(tmp_path, [], monkeypatch)  # no payloads: must hit cache only
    assert resumed.call("GET", "https://api.github.com/y", tag="t") == {"items": []}


def test_token_never_written_to_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cl = make_client(tmp_path, [{"data": {"x": 1}}], monkeypatch)
    cl.gql("q", {}, "t")
    for f in tmp_path.rglob("*"):
        if f.is_file():
            assert "ghp_SECRET_TOKEN_VALUE" not in f.read_text(encoding="utf-8")


def test_search_incomplete_results_is_recorded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cl = make_client(tmp_path, [{"incomplete_results": True, "items": []}], monkeypatch)
    assert C.build_universe(cl) == []
    assert cl.failures == [{"tag": "search:p1", "error": "incomplete_results=true"}]


def test_summary_states_provisional_explicitly() -> None:
    res = {
        "protocol_sha256": "a" * 64,
        "N_cand": 10,
        "N_cand_upper_bound": 12,
        "complete_data": False,
        "api_failures": {"count": 1},
        "page_cap_truncated_repos": [],
        "universe": {"filter_null_api": 0},
        "funnel": {"F5": 10},
        "decision_class": C.decision_class(10, 12, False),
    }
    md = C.summary_md(res)
    assert "**Status: PROVISIONAL**" in md and "NO-VERDICT (incomplete)" in md
