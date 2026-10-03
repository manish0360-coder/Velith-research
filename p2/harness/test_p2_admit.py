"""FG-4 deterministic tests for Phase-A admission. Synthetic only.

A fake `Ops` stands in for Docker, the probe, the dataset and the tokenizer. There is no image
pull, no admission, no model call and no network. The real FG-3 artifacts are only read
(hash-checked), never written.

Run:  PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider \
          p2/harness/test_p2_admit.py
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
import types
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import p2_admit as A  # noqa: E402
import p2_edits as E  # noqa: E402
import p2_harness as H  # noqa: E402
import p2_lottery as L  # noqa: E402

_DIFF = re.compile(r"^diff --git a/.* b/(.*)$", re.MULTILINE)
BASE_SRC = b"def f():\n    return 1\n"
GOLD = ("diff --git a/pkg/m.py b/pkg/m.py\n--- a/pkg/m.py\n+++ b/pkg/m.py\n"
        "@@ -1,2 +1,2 @@\n def f():\n-    return 1\n+    return 10\n")
TEST = ("diff --git a/pkg/tests/test_m.py b/pkg/tests/test_m.py\n--- a/pkg/tests/test_m.py\n"
        "+++ b/pkg/tests/test_m.py\n@@ -1 +1,2 @@\n+def test_new():\n")


@pytest.fixture(autouse=True)
def stub_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = types.ModuleType("probe")
    stub.patch_files = lambda patch: sorted(set(_DIFF.findall(patch)))  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "probe", stub)


@dataclass
class Task:
    iid: str
    repo: str
    pull_failures: int = 0
    bad_identity: bool = False
    spec_fail: bool = False
    case_a: str = "PASSED"
    duration: float = 120.0
    h_mismatch: bool = False
    tokens: int | None = None
    leak: bool = False
    gold: str = GOLD
    base: bytes = BASE_SRC
    selfcheck_gate: str = "RAN"
    row_drift: bool = False

    def digest(self) -> str:
        return "sha256:" + hashlib.sha256(self.iid.encode()).hexdigest()

    def row(self) -> dict[str, Any]:
        problem = "Bug: f returns the wrong value.\n" + (self.gold if self.leak else "")
        return {"instance_id": self.iid, "repo": self.repo, "base_commit": "b" * 40,
                "patch": self.gold, "test_patch": TEST, "problem_statement": problem,
                "hints_text": ""}

    def spec(self) -> dict[str, Any]:
        return {"instance_id": self.iid, "repo": self.repo, "base_commit": "b" * 40,
                "patch": self.gold, "test_patch": TEST, "digest": self.digest(),
                "fail_to_pass": ["pkg/tests/test_m.py::test_new"],
                "pass_to_pass": ["pkg/tests/test_m.py::test_old"],
                "protected_paths": ["pkg/tests/test_m.py"]}


@dataclass
class FakeOps:
    tasks: dict[str, Task]
    free: int = 10**15
    log: list[tuple[str, str]] = field(default_factory=list)
    present: set[str] = field(default_factory=set)
    max_present: int = 0

    def _t(self, ref: str) -> Task:
        return next(t for t in self.tasks.values() if ref.startswith(A.image_name(t.iid) + "@"))

    def free_bytes(self) -> int:
        return self.free

    def resolve(self, image: str) -> tuple[str, int]:
        t = next(t for t in self.tasks.values() if A.image_name(t.iid) == image)
        self.log.append(("resolve", t.iid))
        return t.digest(), 1_000_000_000

    def pull(self, ref: str) -> bool:
        t = self._t(ref)
        self.log.append(("pull", t.iid))
        if t.pull_failures > 0:
            t.pull_failures -= 1
            return False
        self.present.add(ref)
        self.max_present = max(self.max_present, len(self.present))
        return True

    def inspect(self, ref: str) -> tuple[list[str], str, str] | None:
        t = self._t(ref)
        digests = [f"{A.image_name(t.iid)}@sha256:{'0' * 64}"] if t.bad_identity else [ref]
        return digests, A.PLATFORM, "sha256:img-" + t.iid

    def remove(self, ref: str) -> bool:
        self.log.append(("remove", self._t(ref).iid))
        self.present.discard(ref)
        return True

    def build_spec(self, iid: str, image: str, digest: str, out: Path) -> dict[str, Any] | None:
        t = self.tasks[iid]
        if t.spec_fail:
            return None
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(t.spec()), encoding="utf-8")
        return t.spec()

    def case_a(self, spec_path: Path, out_dir: Path, timeout: float) -> dict[str, Any] | None:
        t = self.tasks[json.loads(spec_path.read_text())["instance_id"]]
        self.log.append(("case_a", t.iid))
        assert timeout == A.ADMISSION_CASE_A_TIMEOUT
        return {"deterministic": {"classification": t.case_a, "reason": "x", "detail": "y"},
                "diagnostics": {"candidate": {"duration_seconds": t.duration}}}

    def blob_vs_worktree(self, ref: str, base: str, paths: Sequence[str]
                         ) -> dict[str, dict[str, str]]:
        t = self._t(ref)
        return {p: {"base_sha": "aa", "worktree_sha": "bb" if t.h_mismatch else "aa"}
                for p in paths}

    def read_base(self, ref: str, base: str, paths: Sequence[str]) -> dict[str, E.BaseFile]:
        return {p: E.BaseFile("100644", self._t(ref).base) for p in paths}

    def fetch_row(self, iid: str) -> dict[str, Any]:
        t = self.tasks[iid]
        row = t.row()
        if t.row_drift:
            row["problem_statement"] += "drift"
        return row

    def count_tokens(self, prompt: str) -> int:
        t = next(t for t in self.tasks.values() if f"`{t.repo}`" in prompt)
        return t.tokens if t.tokens is not None else len(prompt) // 4

    def synthesize(self, ref: str, edited: Mapping[str, E.BaseFile]) -> str:
        self.log.append(("synthesize", self._t(ref).iid))
        return "diff --git a/pkg/m.py b/pkg/m.py\n"

    def gate(self, spec: dict[str, Any], patch: str, run_dir: Path, timeout: float
             ) -> dict[str, Any]:
        t = self.tasks[spec["instance_id"]]
        self.log.append(("gate", t.iid))
        st = t.selfcheck_gate
        return {"deterministic": {"classification": "PASSED" if st == "RAN" else
                                  "PATCH_APPLY_FAILED",
                                  "candidate": {"status": st,
                                                "surface": ["s"] if st == "RAN" else []}}}


def world(cands: Sequence[tuple[str, str]], **over: Mapping[str, Any]
          ) -> tuple[list[A.Candidate], FakeOps]:
    tasks = {iid: Task(iid, repo) for iid, repo in cands}
    for iid, attrs in over.items():
        for k, v in attrs.items():
            setattr(tasks[iid], k, v)
    out = [A.Candidate(i, iid, repo, H.sha256_bytes(L.canon(Task(iid, repo,
                                                                 **{k: v for k, v in
                                                                    over.get(iid, {}).items()
                                                                    if k in ("leak", "gold")}
                                                                 ).row())))
           for i, (iid, repo) in enumerate(cands, start=1)]
    return out, FakeOps(tasks)


def five_repo_order(per_repo: int) -> list[tuple[str, str]]:
    repos = [r for r in L.REPOS if r != "pallets/flask"]
    return [(f"{r.split('/')[1]}__{r.split('/')[1]}-{i}", r) for i in range(per_repo)
            for r in repos]


# ---- FG-3 inputs and the real 16 ceiling ------------------------------------------------------
def test_fg3_artifacts_hash_checked_and_unchanged() -> None:
    cands = A.load_candidates()
    assert len(cands) == 54 and [c.rank for c in cands] == list(range(1, 55))
    assert Counter(c.repo for c in cands) == {"scikit-learn/scikit-learn": 24,
                                              "astropy/astropy": 13, "pydata/xarray": 13,
                                              "matplotlib/matplotlib": 4}


def test_real_order_all_admissible_reaches_ceiling_16(tmp_path: Path) -> None:
    real = A.load_candidates()
    cands, ops = world([(c.instance_id, c.repo) for c in real])
    cands = [A.Candidate(r.rank, c.instance_id, c.repo, c.row_sha256) for r, c in zip(real, cands,
                                                                                     strict=True)]
    s = A.run_phase_a(cands, ops, tmp_path)
    assert s["n_admitted"] == 16 and s["status"] == "OK"
    assert s["per_repo"] == {"pallets/flask": 0, "matplotlib/matplotlib": 4,
                             "scikit-learn/scikit-learn": 4, "astropy/astropy": 4,
                             "pydata/xarray": 4}
    order = json.loads((A.LOTTERY / "order.json").read_text())
    preview = order["preview_if_every_candidate_admitted"]
    assert list(s["slots"].values()) == preview  # matches the FG-3 preview exactly
    assert all((tmp_path / slot / "record.json").exists() for slot in s["slots"])
    assert ops.max_present == 1  # one image at a time


# ---- the walk: cap, continuation, no backfill, n boundaries -----------------------------------
def test_cap_and_continuation_after_inadmissible(tmp_path: Path) -> None:
    order = five_repo_order(6)
    first_xarray = next(i for i, r in order if r == "pydata/xarray")
    cands, ops = world(order, **{first_xarray: {"case_a": "FAILED"}})
    s = A.run_phase_a(cands, ops, tmp_path)
    assert s["n_admitted"] == 16 and first_xarray not in s["slots"].values()
    assert all(v == 4 for r, v in s["per_repo"].items() if r != "pallets/flask")
    assert {"instance_id": first_xarray, "outcome": "inadmissible"} in s["walk_log"]


def test_no_backfill_when_a_repo_queue_is_exhausted(tmp_path: Path) -> None:
    order = five_repo_order(4)
    mpl = [i for i, r in order if r == "matplotlib/matplotlib"]
    cands, ops = world(order, **{mpl[0]: {"case_a": "FAILED"}})
    s = A.run_phase_a(cands, ops, tmp_path)
    assert s["n_admitted"] == 15 and s["per_repo"]["matplotlib/matplotlib"] == 3
    assert max(v for v in s["per_repo"].values()) == 4  # no repo exceeds the cap to compensate


def test_n_10_boundary_ok_and_9_void(tmp_path: Path) -> None:
    order = five_repo_order(4)  # 16 candidates, 4 per repo
    fail6 = {iid: {"case_a": "FAILED"} for iid, _ in order[:6]}
    cands, ops = world(order, **fail6)
    s = A.run_phase_a(cands, ops, tmp_path / "ten")
    assert s["n_admitted"] == 10 and s["status"] == "OK"
    fail7 = {iid: {"case_a": "FAILED"} for iid, _ in order[:7]}
    cands, ops = world(order, **fail7)
    s2 = A.run_phase_a(cands, ops, tmp_path / "nine")
    assert s2["n_admitted"] == 9 and s2["status"] == "VOID"


# ---- every admission branch -------------------------------------------------------------------
@pytest.mark.parametrize("over,reason,step", [
    ({"pull_failures": 2}, "PULL_FAILED", "identity"),
    ({"bad_identity": True}, "IDENTITY_MISMATCH", "identity"),
    ({"spec_fail": True}, "SPEC_FAILED", "spec_built"),
    ({"case_a": "FAILED"}, "CASE_A_NOT_PASSED", "case_a_passed"),
    ({"case_a": "INFRA_ERROR"}, "CASE_A_NOT_PASSED", "case_a_passed"),
    ({"h_mismatch": True}, "H_BASE_WORKTREE_MISMATCH", "h_base_equals_worktree"),
    ({"tokens": 15233}, "F_OVER_BUDGET", "f_budget_and_audit"),
    ({"leak": True}, "F_LEAKAGE_AUDIT_FAIL", "f_budget_and_audit"),
    ({"base": b"\xff\xfe"}, "F_GOLD_FILE_UNREADABLE", "f_budget_and_audit"),
])
def test_each_admission_branch(tmp_path: Path, over: dict[str, Any], reason: str, step: str
                               ) -> None:
    cands, ops = world([("pydata__xarray-1", "pydata/xarray")], **{"pydata__xarray-1": over})
    rec = A.admit_candidate(cands[0], ops, tmp_path)
    assert rec["admitted"] is False and rec["reason"] == reason and rec["steps"][step] is False
    assert "self_check" not in rec["events"]  # never run for an inadmissible candidate
    if over.get("pull_failures") != 2:
        assert rec["events"].index("provenance_written") < rec["events"].index("remove")


def test_admitted_happy_path_records_everything(tmp_path: Path) -> None:
    cands, ops = world([("pydata__xarray-1", "pydata/xarray")])
    rec = A.admit_candidate(cands[0], ops, tmp_path)
    assert rec["admitted"] is True and all(rec["steps"].values())
    assert rec["stage_x_timeout_s"] == 900.0 and rec["image_id"] == "sha256:img-pydata__xarray-1"
    sp = rec["stage_p"]
    assert sp["audit"] == {"U": "PASS", "S": "PASS"} and sp["tokens"]["U"] <= A.B_PROMPT
    p = tmp_path / "P"
    common = (p / "common.txt").read_bytes()
    assert (p / "prompt_U.txt").read_bytes().startswith(common)
    assert (p / "prompt_S.txt").read_bytes().startswith(common)
    assert sp["seed"] == H.p1().derive_seed(sp["common_identity"])
    ev = rec["events"]
    assert ev.index("decision") < ev.index("self_check") < ev.index("provenance_written") \
        < ev.index("remove")


def test_one_pull_retry_then_success(tmp_path: Path) -> None:
    cands, ops = world([("pydata__xarray-1", "pydata/xarray")],
                       **{"pydata__xarray-1": {"pull_failures": 1}})
    rec = A.admit_candidate(cands[0], ops, tmp_path)
    assert rec["admitted"] is True and "pull_retry" in rec["events"]


def test_timeout_derivation() -> None:
    assert A.derive_timeout(0.0) == 900.0 and A.derive_timeout(300.0) == 900.0
    assert A.derive_timeout(300.001) == 1800.0 and A.derive_timeout(899.0) == 1800.0


def test_case_a_gold_timeout_is_exactly_1800_on_the_production_path(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert A.ADMISSION_CASE_A_TIMEOUT == 1800.0  # SRC ruling / RD 2026-10-03
    seen: list[float] = []
    cands, ops = world([("pydata__xarray-1", "pydata/xarray")],
                       **{"pydata__xarray-1": {"duration": 1700.0}})
    real_case_a = ops.case_a

    def spy(spec_path: Path, out_dir: Path, timeout: float) -> dict[str, Any] | None:
        seen.append(timeout)
        return real_case_a(spec_path, out_dir, timeout)

    monkeypatch.setattr(ops, "case_a", spy)
    rec = A.admit_candidate(cands[0], ops, tmp_path)
    assert seen == [1800.0]  # admit_candidate passes exactly 1800 s to Case A
    assert rec["admitted"] is True and rec["stage_x_timeout_s"] == 1800.0  # 1700 s gold run
    # DockerOps forwards it unchanged to the frozen probe CLI (no subprocess is executed here)
    calls: list[tuple[list[str], float]] = []

    def fake_run(args: list[str], stdin: bytes | None = None, timeout: float = 3600.0
                 ) -> Any:
        calls.append((args, timeout))
        return types.SimpleNamespace(returncode=0, stdout=b"", stderr=b"")

    monkeypatch.setattr(A.DockerOps, "_run", staticmethod(fake_run))
    A.DockerOps().case_a(tmp_path / "spec.json", tmp_path / "out", A.ADMISSION_CASE_A_TIMEOUT)
    args, sub_timeout = calls[0]
    assert args[args.index("--timeout") + 1] == "1800.0" and args[args.index("--case") + 1] == "A"
    assert sub_timeout == 1800.0 + 600


def test_timeout_recorded_from_case_a(tmp_path: Path) -> None:
    cands, ops = world([("pydata__xarray-1", "pydata/xarray")],
                       **{"pydata__xarray-1": {"duration": 301.0}})
    assert A.admit_candidate(cands[0], ops, tmp_path)["stage_x_timeout_s"] == 1800.0


# ---- stops are not task outcomes and cause no replacement -------------------------------------
def test_storage_failure_stops_before_pull_without_replacement(tmp_path: Path) -> None:
    order = five_repo_order(4)
    cands, ops = world(order)
    ops.free = A.storage_need(1_000_000_000) - 1
    with pytest.raises(A.AdmissionStop, match="storage gate"):
        A.run_phase_a(cands, ops, tmp_path)
    assert [x for x in ops.log if x[0] == "pull"] == []
    assert [x[1] for x in ops.log if x[0] == "resolve"] == [order[0][0]]  # nothing after
    assert not (tmp_path / "_lottery" / "admission_log.json").exists()
    assert A.storage_need(1_000_000_000) == 12_500_000_000


def test_row_drift_is_a_stop_and_image_is_still_removed(tmp_path: Path) -> None:
    cands, ops = world([("pydata__xarray-1", "pydata/xarray")],
                       **{"pydata__xarray-1": {"row_drift": True}})
    with pytest.raises(A.AdmissionStop, match="drift"):
        A.admit_candidate(cands[0], ops, tmp_path)
    assert ("remove", "pydata__xarray-1") in ops.log and not ops.present


def test_delete_happens_after_provenance_for_every_pulled_image(tmp_path: Path) -> None:
    order = five_repo_order(5)
    over: dict[str, dict[str, Any]] = {order[0][0]: {"bad_identity": True},
                                       order[1][0]: {"case_a": "FAILED"}}
    cands, ops = world(order, **over)
    A.run_phase_a(cands, ops, tmp_path)
    pulled = {i for k, i in ops.log if k == "pull"}
    removed = {i for k, i in ops.log if k == "remove"}
    assert pulled == removed and not ops.present and ops.max_present == 1
    for d in list((tmp_path / "_admission").iterdir()) + [tmp_path / s for s in
                                                          ("P2-01", "P2-02")]:
        rec = json.loads((d / "record.json").read_text())
        ev = rec["events"]
        assert ev.index("provenance_written") < ev.index("remove")
        assert rec["provenance"]["digest"] == rec["digest"]


# ---- G-10: the self-check cannot alter admission; A-1 halts after recording ------------------
def test_self_check_outcomes_do_not_change_admission(tmp_path: Path) -> None:
    dup = b"def f():\n    return 1\ndef f():\n    return 1\n"
    outcomes: dict[str, dict[str, Any]] = {"ok": {}, "ambiguous": {"base": dup},
                                           "alarm": {"selfcheck_gate": "PATCH_APPLY_FAILED"}}
    decisions = {}
    for name, over in outcomes.items():
        cands, ops = world([("pydata__xarray-1", "pydata/xarray")], **{"pydata__xarray-1": over})
        work = tmp_path / name
        if name == "alarm":
            with pytest.raises(A.AdmissionStop, match="A-1"):
                A.admit_candidate(cands[0], ops, work)
            rec = json.loads((work / "record.json").read_text())
            assert ("remove", "pydata__xarray-1") in ops.log  # removed before the halt
        else:
            rec = A.admit_candidate(cands[0], ops, work)
        decisions[name] = rec["admitted"]
        assert rec["events"].index("decision") < rec["events"].index("self_check")
    assert decisions == {"ok": True, "ambiguous": True, "alarm": True}
    amb = json.loads((tmp_path / "ambiguous" / "SELF-S" / "self_check.json").read_text())
    assert amb["resolution_code"] == E.S_SEARCH_AMBIGUOUS and amb["diagnostic_only"] is True


# ---- determinism, resume, no hidden replacement -----------------------------------------------
def test_deterministic_and_resumable(tmp_path: Path) -> None:
    order = five_repo_order(5)
    over = {order[2][0]: {"h_mismatch": True}}
    c1, o1 = world(order, **over)
    c2, o2 = world(order, **over)
    s1, s2 = A.run_phase_a(c1, o1, tmp_path / "a"), A.run_phase_a(c2, o2, tmp_path / "b")
    assert s1 == s2
    with pytest.raises(A.AdmissionStop, match="already completed"):
        A.run_phase_a(c1, o1, tmp_path / "a")
    # resume after an interruption: decided records are reused, never re-run
    c3, o3 = world(order, **over)
    root = tmp_path / "c"
    first = root / "_admission" / f"01-{order[0][0]}"
    first.mkdir(parents=True)
    A.admit_candidate(c3[0], o3, first)  # candidate 1 decided before the "interruption"
    before = len(o3.log)
    s3 = A.run_phase_a(c3, o3, root)
    assert s3 == s1 and ("resolve", order[0][0]) not in o3.log[before:]


def test_interrupted_partial_state_is_preserved_and_candidate_restarts_fresh(tmp_path: Path
                                                                             ) -> None:
    order = five_repo_order(4)
    cands, ops = world(order)
    first = tmp_path / "_admission" / f"01-{order[0][0]}"
    (first / "A").mkdir(parents=True)
    (first / "A" / "spec.json").write_text("stale partial spec")  # would block fetch-spec
    (first / "record.json").write_text(json.dumps({"events": ["resolve", "storage_ok", "pull"]}))
    older = first.with_name(first.name + ".interrupted-1")
    older.mkdir()
    (older / "marker").write_text("earlier interruption")
    s = A.run_phase_a(cands, ops, tmp_path)
    kept = first.with_name(first.name + ".interrupted-2")  # next free k; nothing overwritten
    assert (kept / "A" / "spec.json").read_text() == "stale partial spec"
    assert json.loads((kept / "record.json").read_text()) == {"events": ["resolve", "storage_ok",
                                                                          "pull"]}
    assert (older / "marker").read_text() == "earlier interruption"
    assert ("resolve", order[0][0]) in ops.log and ("case_a", order[0][0]) in ops.log  # fresh
    fresh = json.loads((tmp_path / "P2-01" / "record.json").read_text())
    assert fresh["instance_id"] == order[0][0] and fresh["admitted"] is True
    assert "provenance_written" in fresh["events"] and s["n_admitted"] == 16


def test_no_hidden_replacement_no_model_path_in_source() -> None:
    src = Path(A.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    assert "L.walk(" in src and not any(isinstance(n, ast.FunctionDef) and n.name == "walk"
                                        for n in ast.walk(tree))  # frozen FG-3 walk, reused
    names = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)} | \
        {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    imports = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import | ast.ImportFrom)
               for a in n.names}
    assert not {"generate", "OllamaClient", "OLLAMA_HOST", "run_gen", "p1_gen"} & (names | imports)
    assert "self_check" not in "".join(H.ADMISSION_STEPS)
