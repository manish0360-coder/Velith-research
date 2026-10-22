"""P4 supply census: read-only GitHub metadata count of post-cutoff Python issue->PR candidates.

Implements exactly the frozen protocol in p4/P4_SUPPLY_CENSUS.md §1 (SHA-256 checked below).
Read-only: GitHub REST/GraphQL GET-style queries only. No clones, builds, model calls or writes
outside --out. Standard library only.

  python3 -B p4/census/supply_census.py run    --out DIR   # network; resumable (cache)
  python3 -B p4/census/supply_census.py report --out DIR   # offline re-analysis of the cache

Token: GITHUB_TOKEN, else `gh auth token`. Never printed or written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROTOCOL_DOC = HERE.parent / "P4_SUPPLY_CENSUS.md"
PROTOCOL_SHA256 = "a642efdb2660e328dd9db7a8b3c9583abe0347e900a77be4ed46e4f39898e89f"

B = "2026-08-01T00:00:00Z"
T_CUT = "2026-10-12T00:00:00Z"
SEARCH_Q = "language:Python stars:>=1000 pushed:>=2026-08-01 archived:false fork:false"
PKG_FILES = ("pyproject.toml", "setup.py", "setup.cfg")
TEST_SIGNALS = ("tests", "test", "testing", "pytest.ini", "conftest.py", "tox.ini")
TEST_RE = re.compile(r"(^|/)(tests?|testing)/|(^|/)test_[^/]*\.py$|_test\.py$|(^|/)conftest\.py$")
PAGE_CAP = 50
MAX_COMMITS = 100
SURV_LO, SURV_HI = 0.40, 0.80
REQ_MIN, REQ_MAX = 157, 252
SCENARIOS: dict[str, dict[str, Any]] = {
    "delta_0.15": {"R": "105-115", "req": [157, 167]},
    "delta_0.10": {"R": "190-200", "req": [242, 252]},
}
API = "https://api.github.com"


class CensusError(Exception):
    pass


# ---- pure rules (unit-tested) ----------------------------------------------------------------
def in_window(ts: str | None) -> bool:
    return ts is not None and B <= ts < T_CUT


def is_test_file(path: str) -> bool:
    return bool(TEST_RE.search(path))


def classify_files(paths: list[str]) -> tuple[bool, bool]:
    """(changes >= 1 test file, changes >= 1 non-test .py file)."""
    tests = any(is_test_file(p) for p in paths)
    src = any(p.endswith(".py") and not is_test_file(p) for p in paths)
    return tests, src


def stage1(pr: dict[str, Any]) -> bool:
    login = (pr.get("author") or {}).get("login") or ""
    return (
        in_window(pr.get("mergedAt"))
        and pr.get("createdAt", "") >= B
        and not login.endswith("[bot]")
    )


def stage2(pr: dict[str, Any]) -> str:
    """PASS | FAIL | UNDETERMINED (more closing references than fetched: cannot verify all)."""
    refs = pr.get("closingIssuesReferences") or {}
    nodes = refs.get("nodes") or []
    if refs.get("totalCount", 0) > len(nodes):
        return "UNDETERMINED"
    if not nodes:
        return "FAIL"
    return "PASS" if all((n.get("createdAt") or "") >= B for n in nodes) else "FAIL"


def stage3(detail: dict[str, Any]) -> str:
    """PASS | FAIL | UNDETERMINED (more than MAX_COMMITS commits)."""
    commits = detail.get("commits") or {}
    if commits.get("totalCount", 0) > MAX_COMMITS:
        return "UNDETERMINED"
    dates = [
        d
        for n in commits.get("nodes") or []
        for d in (n["commit"]["authoredDate"], n["commit"]["committedDate"])
    ]
    if not dates:
        return "UNDETERMINED"
    return "PASS" if min(dates) >= B else "FAIL"


def stage4(detail: dict[str, Any]) -> tuple[bool, bool]:
    """(passes, truncated_file_list)."""
    files = detail.get("files") or {}
    paths = [n["path"] for n in files.get("nodes") or []]
    tests, src = classify_files(paths)
    return tests and src, files.get("totalCount", 0) > len(paths)


def stage5(compare: dict[str, Any] | None) -> str:
    if not compare or "merge_base_commit" not in compare:
        return "UNDETERMINED"
    date = compare["merge_base_commit"]["commit"]["committer"]["date"]
    return "PASS" if date >= B else "FAIL"


def repo_ok(r: dict[str, Any]) -> dict[str, bool]:
    return {
        "U1_python": (r.get("primaryLanguage") or {}).get("name") == "Python",
        "U2_packaging": any(r.get(f"pkg{i}") for i in range(len(PKG_FILES))),
        "U3_tests": any(r.get(f"tst{i}") for i in range(len(TEST_SIGNALS))),
        "U4_not_fork_archived": not r.get("isFork") and not r.get("isArchived"),
    }


def classify(n: int, req_hi: int, req_lo: int) -> str:
    """§1.7 mechanical class for a count n (thresholds unchanged from the frozen protocol)."""
    if n * SURV_LO >= req_hi:
        return "PROCEED-TO-SPIKE"
    if n * SURV_HI < req_lo:
        return "WINDOW-INFEASIBLE"
    return "SPIKE-DECIDES"


def gated(n_cand: int, n_max: int, complete_data: bool, req_hi: int, req_lo: int) -> dict[str, Any]:
    """FINAL only with complete data and an undetermined-robust class. Otherwise PROVISIONAL:
    only PROCEED-TO-SPIKE survives (as a lower bound on positively supported, deduplicated
    candidates); incomplete data never yields WINDOW-INFEASIBLE or SPIKE-DECIDES."""
    lo, hi = classify(n_cand, req_hi, req_lo), classify(n_max, req_hi, req_lo)
    if complete_data and lo == hi:
        return {"status": "FINAL", "class": lo}
    verdict = "PROCEED-TO-SPIKE" if lo == "PROCEED-TO-SPIKE" else "NO-VERDICT (incomplete)"
    return {
        "status": "PROVISIONAL",
        "class": verdict,
        "basis": "lower bound" if lo == "PROCEED-TO-SPIKE" else "insufficient data",
        "class_at_lower_bound": lo,
        "class_at_upper_bound": hi,
    }


def decision_class(
    n_cand: int, n_max: int | None = None, complete_data: bool = True
) -> dict[str, Any]:
    n_max = n_cand if n_max is None else n_max
    out: dict[str, Any] = {
        "overall": gated(n_cand, n_max, complete_data, REQ_MAX, REQ_MIN),
        "N_cand_lower": n_cand,
        "N_cand_upper": n_max,
        "complete_data": complete_data,
        "projected_admitted_range": [round(n_cand * SURV_LO), round(n_cand * SURV_HI)],
        "survival_assumption": [SURV_LO, SURV_HI],
    }
    for name, s in SCENARIOS.items():
        out[name] = {
            "R_not_ratified": s["R"],
            "requirement": s["req"],
            **gated(n_cand, n_max, complete_data, s["req"][1], s["req"][1]),
        }
    return out


def protocol_sha(doc: Path = PROTOCOL_DOC) -> str:
    t = doc.read_text(encoding="utf-8")
    s = t.index("<!-- PROTOCOL-BEGIN -->")
    e = t.index("<!-- PROTOCOL-END -->") + len("<!-- PROTOCOL-END -->")
    return hashlib.sha256(t[s:e].encode("utf-8")).hexdigest()


# ---- cached transport ------------------------------------------------------------------------
class Client:
    def __init__(
        self,
        out: Path,
        offline: bool,
        opener: Callable[[urllib.request.Request], Any] | None = None,
    ) -> None:
        self.cache = out / "cache"
        self.cache.mkdir(parents=True, exist_ok=True)
        self.offline = offline
        self.opener = opener or (lambda req: urllib.request.urlopen(req, timeout=60))
        self.failures: list[dict[str, Any]] = []
        self._token: str | None = None

    def token(self) -> str:
        if self._token is None:
            tok = os.environ.get("GITHUB_TOKEN", "")
            if not tok:
                try:
                    tok = subprocess.run(
                        ["gh", "auth", "token"],
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=30,
                    ).stdout.strip()
                except (OSError, subprocess.TimeoutExpired):
                    tok = ""
            if not tok:
                raise CensusError("no GITHUB_TOKEN and `gh auth token` unavailable")
            self._token = tok
        return self._token

    def _key(self, method: str, url: str, body: dict[str, Any] | None) -> Path:
        h = hashlib.sha256(json.dumps([method, url, body], sort_keys=True).encode()).hexdigest()
        return self.cache / f"{h}.json"

    def call(self, method: str, url: str, body: dict[str, Any] | None = None, tag: str = "") -> Any:
        path = self._key(method, url, body)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))["response"]
        if self.offline:
            self.failures.append({"tag": tag, "error": "not in cache (offline)"})
            return None
        data = json.dumps(body).encode() if body is not None else None
        for attempt in range(6):
            req = urllib.request.Request(
                url,
                data=data,
                method=method,
                headers={
                    "Authorization": f"Bearer {self.token()}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                    "User-Agent": "velith-p4-census",
                },
            )
            try:
                with self.opener(req) as r:
                    resp = json.loads(r.read().decode("utf-8"))
                    remaining = r.headers.get("X-RateLimit-Remaining")
                    reset = r.headers.get("X-RateLimit-Reset")
                if remaining is not None and int(remaining) < 50 and reset:
                    time.sleep(max(0, int(reset) - int(time.time())) + 5)
                if isinstance(resp, dict) and resp.get("errors") and not resp.get("data"):
                    raise CensusError(json.dumps(resp["errors"])[:500])
                tmp = path.with_suffix(".tmp")
                tmp.write_text(
                    json.dumps({"request": [method, url, body], "response": resp, "utc": now()}),
                    encoding="utf-8",
                )
                os.replace(tmp, path)  # atomic: an interrupted write never leaves a partial file
                return resp
            except urllib.error.HTTPError as e:
                if e.code in (403, 429, 502, 503) and attempt < 5:
                    time.sleep(min(600, 30 * 2**attempt))
                    continue
                self.failures.append({"tag": tag, "error": f"HTTP {e.code}"})
                return None
            except (urllib.error.URLError, TimeoutError, CensusError) as e:
                if attempt < 5:
                    time.sleep(10 * (attempt + 1))
                    continue
                self.failures.append({"tag": tag, "error": f"{type(e).__name__}: {e}"[:300]})
                return None
        return None

    def gql(self, query: str, variables: dict[str, Any], tag: str) -> Any:
        resp = self.call("POST", f"{API}/graphql", {"query": query, "variables": variables}, tag)
        if isinstance(resp, dict) and resp.get("errors"):
            first = resp["errors"][0] if isinstance(resp["errors"], list) else resp["errors"]
            self.failures.append(
                {"tag": tag, "error": "graphql partial error: " + json.dumps(first)[:300]}
            )
        return (resp or {}).get("data")


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---- queries ---------------------------------------------------------------------------------
def repo_filter_query(n: int) -> str:
    objs = "".join(
        f' pkg{i}: object(expression: "HEAD:{f}") {{ __typename }}' for i, f in enumerate(PKG_FILES)
    )
    objs += "".join(
        f' tst{i}: object(expression: "HEAD:{f}") {{ __typename }}'
        for i, f in enumerate(TEST_SIGNALS)
    )
    parts = [
        f"r{i}: repository(owner: $o{i}, name: $n{i}) {{ nameWithOwner isFork isArchived "
        f"primaryLanguage {{ name }}{objs} }}"
        for i in range(n)
    ]
    args = ", ".join(f"$o{i}: String!, $n{i}: String!" for i in range(n))
    return f"query({args}) {{ {' '.join(parts)} }}"


PR_LIST_Q = """query($o: String!, $n: String!, $c: String) { repository(owner: $o, name: $n) {
 pullRequests(states: MERGED, first: 100, after: $c,
  orderBy: {field: UPDATED_AT, direction: DESC}) {
  pageInfo { hasNextPage endCursor }
  nodes { number createdAt mergedAt updatedAt author { login }
   closingIssuesReferences(first: 10) { totalCount nodes { number createdAt } } } } } }"""

PR_DETAIL_FIELDS = """baseRefOid headRefOid
 commits(first: 100) { totalCount nodes { commit { authoredDate committedDate } } }
 files(first: 100) { totalCount nodes { path } }"""


def pr_detail_query(numbers: list[int]) -> str:
    parts = " ".join(
        f"p{num}: pullRequest(number: {num}) {{ {PR_DETAIL_FIELDS} }}" for num in numbers
    )
    return f"query($o: String!, $n: String!) {{ repository(owner: $o, name: $n) {{ {parts} }} }}"


# ---- census ----------------------------------------------------------------------------------
def build_universe(cl: Client) -> list[dict[str, Any]]:
    repos: list[dict[str, Any]] = []
    for page in range(1, 11):
        q = urllib.parse.urlencode(
            {"q": SEARCH_Q, "sort": "stars", "order": "desc", "per_page": 100, "page": page}
        )
        resp = cl.call("GET", f"{API}/search/repositories?{q}", tag=f"search:p{page}")
        if isinstance(resp, dict) and resp.get("incomplete_results"):
            cl.failures.append({"tag": f"search:p{page}", "error": "incomplete_results=true"})
        items = (resp or {}).get("items") or []
        repos += [{"full_name": it["full_name"], "stars": it["stargazers_count"]} for it in items]
        if len(items) < 100:
            break
    for i in range(0, len(repos), 20):
        batch = repos[i : i + 20]
        variables: dict[str, Any] = {}
        for j, r in enumerate(batch):
            variables[f"o{j}"], variables[f"n{j}"] = r["full_name"].split("/", 1)
        data = cl.gql(repo_filter_query(len(batch)), variables, f"repofilter:{i}") or {}
        for j, r in enumerate(batch):
            node = data.get(f"r{j}")
            verdict = repo_ok(node) if isinstance(node, dict) else None
            r["filters"] = verdict
            r["in_universe"] = verdict is not None and all(verdict.values())
    return repos


def walk_repo(cl: Client, full: str) -> dict[str, Any]:
    owner, name = full.split("/", 1)
    res: dict[str, Any] = {
        "F0": 0,
        "F1": 0,
        "F2": 0,
        "F3": 0,
        "F4": 0,
        "F5": 0,
        "F2_undetermined": 0,
        "F3_undetermined": 0,
        "F5_undetermined": 0,
        "files_truncated": 0,
        "F4_truncated_excluded": 0,
        "duplicates_skipped": 0,
        "page_cap_hit": False,
        "cands": [],
    }
    survivors: list[dict[str, Any]] = []
    seen: set[Any] = set()
    cursor = None
    for page in range(PAGE_CAP):
        data = cl.gql(PR_LIST_Q, {"o": owner, "n": name, "c": cursor}, f"prs:{full}:{page}")
        conn = (((data or {}).get("repository") or {}).get("pullRequests")) or {}
        nodes = conn.get("nodes") or []
        for pr in nodes:
            if pr.get("number") in seen:  # reordering between pages: never count twice
                res["duplicates_skipped"] += 1
                continue
            seen.add(pr.get("number"))
            if in_window(pr.get("mergedAt")):
                res["F0"] += 1
                if stage1(pr):
                    res["F1"] += 1
                    s2 = stage2(pr)
                    if s2 == "UNDETERMINED":
                        res["F2_undetermined"] += 1
                    elif s2 == "PASS":
                        res["F2"] += 1
                        survivors.append(pr)
        if (
            not nodes
            or all((p.get("updatedAt") or "") < B for p in nodes)
            or not (conn.get("pageInfo") or {}).get("hasNextPage")
        ):
            break
        cursor = conn["pageInfo"]["endCursor"]
    else:
        res["page_cap_hit"] = True
    for i in range(0, len(survivors), 10):
        batch = survivors[i : i + 10]
        data = (
            cl.gql(
                pr_detail_query([p["number"] for p in batch]),
                {"o": owner, "n": name},
                f"detail:{full}:{i}",
            )
            or {}
        )
        repo = data.get("repository") or {}
        for pr in batch:
            d = repo.get(f"p{pr['number']}")
            if not d:
                res["F3_undetermined"] += 1
                continue
            s3 = stage3(d)
            if s3 == "UNDETERMINED":
                res["F3_undetermined"] += 1
                continue
            if s3 != "PASS":
                continue
            res["F3"] += 1
            ok4, trunc = stage4(d)
            res["files_truncated"] += int(trunc)
            if not ok4:
                res["F4_truncated_excluded"] += int(trunc)  # may be a missed candidate
                continue
            res["F4"] += 1
            cmp_ = cl.call(
                "GET",
                f"{API}/repos/{full}/compare/{d['baseRefOid']}..." f"{d['headRefOid']}?per_page=1",
                tag=f"compare:{full}#{pr['number']}",
            )
            s5 = stage5(cmp_)
            if s5 == "UNDETERMINED":
                res["F5_undetermined"] += 1
            elif s5 == "PASS":
                res["F5"] += 1
                res["cands"].append(
                    {"repo": full, "number": pr["number"], "merged_month": pr["mergedAt"][:7]}
                )
    return res


def manifest(out: Path) -> str:
    lines = [
        f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(out).as_posix()}"
        for p in sorted((out / "cache").glob("*.json"))
    ]
    data = "\n".join(lines) + "\n"
    (out / "MANIFEST.sha256").write_text(data, encoding="utf-8")
    return hashlib.sha256(data.encode()).hexdigest()


def census(out: Path, offline: bool, cl: Client | None = None) -> dict[str, Any]:
    if protocol_sha() != PROTOCOL_SHA256:
        raise CensusError("P4_SUPPLY_CENSUS.md §1 protocol changed since freeze")
    cl = cl or Client(out, offline)
    meta_path = out / "run_meta.json"
    if not meta_path.exists():
        if offline:
            raise CensusError("no run_meta.json: run `run` first")
        meta_path.write_text(
            json.dumps({"T_SEL": now(), "protocol_sha256": PROTOCOL_SHA256}, indent=2),
            encoding="utf-8",
        )
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    repos = build_universe(cl)
    uni = [r for r in repos if r.get("in_universe")]
    uni_bytes = json.dumps(repos, sort_keys=True).encode()
    (out / "universe.json").write_bytes(uni_bytes)
    totals: Counter[str] = Counter()
    per_repo: dict[str, int] = {}
    months: Counter[str] = Counter()
    truncated: list[str] = []
    for r in uni:
        w = walk_repo(cl, r["full_name"])
        for k in (
            "F0",
            "F1",
            "F2",
            "F3",
            "F4",
            "F5",
            "F2_undetermined",
            "F3_undetermined",
            "F5_undetermined",
            "files_truncated",
            "F4_truncated_excluded",
            "duplicates_skipped",
        ):
            totals[k] += w[k]
        if w["page_cap_hit"]:
            truncated.append(r["full_name"])
        if w["F5"]:
            per_repo[r["full_name"]] = w["F5"]
        months.update(c["merged_month"] for c in w["cands"])
    n_cand = totals["F5"]
    n_max = n_cand + sum(
        totals[k]
        for k in ("F2_undetermined", "F3_undetermined", "F4_truncated_excluded", "F5_undetermined")
    )
    null_filters = sum(1 for r in repos if r.get("filters") is None)
    complete_data = not cl.failures and not truncated and null_filters == 0
    result = {
        "protocol_sha256": PROTOCOL_SHA256,
        "T_SEL": meta["T_SEL"],
        "B": B,
        "T_CUT": T_CUT,
        "universe": {
            "searched": len(repos),
            "kept": len(uni),
            "filter_null_api": null_filters,
            "sha256": hashlib.sha256(uni_bytes).hexdigest(),
        },
        "funnel": dict(totals),
        "N_cand": n_cand,
        "N_cand_upper_bound": n_max,
        "complete_data": complete_data,
        "distinct_repos": len(per_repo),
        "N_cand_cap4_sensitivity": sum(min(4, v) for v in per_repo.values()),
        "per_repo_top20": sorted(per_repo.items(), key=lambda kv: -kv[1])[:20],
        "per_month": dict(sorted(months.items())),
        "page_cap_truncated_repos": truncated,
        "api_failures": {"count": len(cl.failures), "first_20": cl.failures[:20]},
        "decision_class": decision_class(n_cand, n_max, complete_data),
        "labels": {
            "N_cand": "CANDIDATE count, not verified eligible (E1-E3, Case A, build, "
            "F2P, budget, leakage unchecked)",
            "survival": "ASSUMPTION 0.40-0.80",
            "R": "CSE computation, NOT ratified",
        },
        "manifest_sha256": manifest(out),
    }
    (out / "census_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (out / "census_summary.md").write_text(summary_md(result), encoding="utf-8")
    return result


def summary_md(res: dict[str, Any]) -> str:
    """Human-readable status; the FINAL/PROVISIONAL distinction is stated first."""
    dc = res["decision_class"]
    ov = dc["overall"]
    lines = [
        f"# P4 supply census summary (protocol {res['protocol_sha256'][:12]})",
        "",
        f"**Status: {ov['status']}** — decision class: **{ov['class']}**",
    ]
    if ov["status"] == "PROVISIONAL":
        lines.append(
            f"PROVISIONAL ({ov['basis']}): incomplete or undetermined data "
            "never supports WINDOW-INFEASIBLE or SPIKE-DECIDES; only "
            "PROCEED-TO-SPIKE survives, as a lower bound."
        )
    lines += [
        "",
        f"- N_cand (candidates, deduplicated, positively supported): {res['N_cand']}",
        f"- N_cand upper bound (adding undetermined/truncated): " f"{res['N_cand_upper_bound']}",
        f"- complete_data: {res['complete_data']} (API failures: "
        f"{res['api_failures']['count']}, page-cap truncated repos: "
        f"{len(res['page_cap_truncated_repos'])}, null repo filters: "
        f"{res['universe']['filter_null_api']})",
        f"- funnel: {json.dumps(res['funnel'], sort_keys=True)}",
    ]
    for name in SCENARIOS:
        s = dc[name]
        lines.append(
            f"- {name} (R {s['R_not_ratified']}, NOT ratified): {s['status']} " f"{s['class']}"
        )
    lines += [
        "",
        "Labels: N_cand is a CANDIDATE count, not verified eligibility; survival "
        "0.40-0.80 is an ASSUMPTION; R is a CSE computation, NOT ratified.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    ap = argparse.ArgumentParser(prog="supply_census")
    ap.add_argument("cmd", choices=("run", "report"))
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args(argv)
    try:
        res = census(a.out.expanduser(), offline=a.cmd == "report")
    except CensusError as e:
        print(f"STOP: {e}", file=sys.stderr)
        return 1
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
