"""Offline tests for the P1 harness (no Docker, no Ollama, no network).

Run:  python3 -m pytest -q -p no:cacheprovider p1/harness/test_p1_harness.py
Optional: VELITH_SRC=<Velith>/src enables the p1_gen.py check-mode test (needs pydantic).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import types
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import p1_harness as H  # noqa: E402

_DIFF_FILE = re.compile(r"^diff --git a/.* b/(.*)$", re.MULTILINE)


@pytest.fixture(autouse=True)
def stub_probe(monkeypatch):
    stub = types.ModuleType("probe")
    stub.patch_files = lambda patch: sorted(set(_DIFF_FILE.findall(patch)))
    monkeypatch.setitem(sys.modules, "probe", stub)


def _od2_blocks() -> tuple[str, str]:
    doc = (H.RESEARCH / "P1_OD-2_OD-3_RETRIEVAL_SPEC_DRAFT.md").read_text(encoding="utf-8")
    section = doc.split("## 1. OD-2", 1)[1].split("## 2.", 1)[0]
    blocks = re.findall(r"^```\n(.*?)^```$", section, flags=re.MULTILINE | re.DOTALL)
    return blocks[0], blocks[1]


def test_template_is_the_approved_od2_text_byte_for_byte():
    main, file_block = _od2_blocks()
    prompt, _ = H.render("{repo}", "{problem_statement}",
                         [("{path}", "{verbatim file content, no line numbers}")])
    assert prompt == main.replace("{files}", file_block.rstrip("\n"))


def test_bos_text_matches_the_d_e_check_script():
    src = (H.RESEARCH / "stage0" / "tokenizer" / "check_tokenizer_equivalence.py").read_text(
        encoding="utf-8")
    assert f'BOS_TEXT = "{H.BOS_TEXT}"' in src


def test_render_spans_cover_verbatim_sources():
    prompt, spans = H.render("o/r", "issue text\n", [("a.py", "x = 1\n"), ("b.py", "y")])
    got = {label: prompt[s:e] for label, s, e in spans}
    assert got == {"issue": "issue text\n", "file:a.py": "x = 1\n", "file:b.py": "y"}
    assert "=== FILE: a.py ===\nx = 1\n=== END FILE: a.py ===\n\n=== FILE: b.py ===\ny\n" \
           "=== END FILE: b.py ===" in prompt


def test_tokenize_and_bm25_order():
    assert H.tokenize("Foo_bar(x1) İ-y") == ["foo_bar", "x1", "y"]
    docs = [{"path": "b.py", "text": "alpha beta"}, {"path": "a.py", "text": "alpha beta"},
            {"path": "c.py", "text": "gamma"}, {"path": "d.py", "text": "alpha alpha alpha"}]
    ranked = H.bm25_rank("alpha beta", docs)
    assert [p for _, p in ranked][:2] == ["a.py", "b.py"]  # tie -> path ascending
    assert "c.py" not in [p for _, p in ranked]  # score 0 excluded
    n, df_a, df_b = 4, 3, 2
    idf_a = H.math.log(1 + (n - df_a + 0.5) / (df_a + 0.5))
    idf_b = H.math.log(1 + (n - df_b + 0.5) / (df_b + 0.5))
    avg = (2 + 2 + 1 + 3) / 4
    norm = 1 - 0.75 + 0.75 * 2 / avg
    expect = (idf_a + idf_b) * 2.2 / (1 + 1.2 * norm)
    assert abs(dict((p, s) for s, p in ranked)["a.py"] - expect) < 1e-12


def test_exclusion_rules():
    cases = {"pkg/tests/x.py": "test", "pkg/test_x.py": "test", "pkg/x_test.py": "test",
             "conftest.py": "test", "testing/y.py": "test", "sklearn/externals/six.py": "vendored",
             "build/lib/z.py": "vendored", "pkg/testing.py": None, "pkg/mod.py": None,
             "tests.py": None}
    assert {p: H.exclusion_reason(p) for p in cases} == cases


def test_fit_rule_skips_and_stops_at_k(monkeypatch):
    monkeypatch.setattr(H, "B_PROMPT", 2000)
    base = len(H.render("r", "q", [])[0])
    texts = {f"f{i}.py": "x" * size for i, size in enumerate([5000, 100, 100, 100, 100, 100, 100])}
    ranked = [(10.0 - i, f"f{i}.py") for i in range(7)]
    inc, trace, base_count = H.select_files("r", "q", ranked, texts, len)
    assert base_count == base
    assert trace[0]["decision"] == "skipped_does_not_fit"
    assert [p for p, _ in inc] == ["f1.py", "f2.py", "f3.py", "f4.py", "f5.py"]
    assert len(H.render("r", "q", inc)[0]) <= 2000


def test_git_parsers_and_blob_oid(tmp_path):
    def git(*a, data=None):
        return subprocess.run(["git", "-C", str(tmp_path), *a], input=data, capture_output=True,
                              check=True).stdout
    git("init", "-q")
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "m.py").write_bytes(b"print('h\xc3\xa9')\n")
    (tmp_path / "name with space.py").write_text("x = 1\n")
    git("add", ".")
    git("-c", "user.email=a@b", "-c", "user.name=t", "commit", "-qm", "c")
    entries = H.parse_ls_tree(git("ls-tree", "-r", "-l", "-z", "HEAD"))
    assert {e[3] for e in entries} == {"pkg/m.py", "name with space.py"}
    blobs = H.parse_cat_file_batch(git("cat-file", "--batch",
                                       data=b"".join(e[2].encode() + b"\n" for e in entries)))
    for _mode, _t, oid, _p in entries:
        assert H.git_blob_oid(blobs[oid]) == oid


def _spec():
    gold = ("diff --git a/pkg/m.py b/pkg/m.py\n--- a/pkg/m.py\n+++ b/pkg/m.py\n@@ -1 +1 @@\n"
            "-    return old_value\n+    return fixed_value_unique\n")
    test = ("diff --git a/pkg/tests/test_m.py b/pkg/tests/test_m.py\n--- a/pkg/tests/test_m.py\n"
            "+++ b/pkg/tests/test_m.py\n@@ -1 +1,2 @@\n+def test_new_behaviour():\n")
    return {"patch": gold, "test_patch": test,
            "fail_to_pass": ["pkg/tests/test_m.py::test_new_behaviour"], "pass_to_pass": []}


def test_leakage_audit_attributes_regions():
    spec = _spec()
    prompt, spans = H.render("o/r", "issue mentions return old_value", [("pkg/m.py",
                             "def f():\n    return old_value\n")])
    a = H.leakage_audit(prompt, spans, spec, {"hints_text": ""}, {"pkg/m.py"}, ["pkg/m.py"])
    assert a["verdict"] == "PASS"
    occ = a["checks"]["gold_hunk_lines"]["occurrences_by_region"]
    assert occ == {"file": 1, "issue": 1}  # '-' line is base content / issue text: exempt


def test_leakage_audit_fails_on_test_path_in_pool_and_full_patch():
    spec = _spec()
    prompt, spans = H.render("o/r", "q", [("pkg/m.py", "x\n")])
    a = H.leakage_audit(prompt, spans, spec, {"hints_text": ""},
                        {"pkg/m.py", "pkg/tests/test_m.py"}, ["pkg/m.py"])
    assert a["verdict"] == "FAIL" and a["checks"]["test_patch_paths_in_pool"]
    prompt2, spans2 = H.render("o/r", spec["patch"], [("pkg/m.py", "x\n")])
    b = H.leakage_audit(prompt2, spans2, spec, {"hints_text": ""}, {"pkg/m.py"}, ["pkg/m.py"])
    assert b["verdict"] == "FAIL" and b["checks"]["gold_patch_full_text"]


def test_leakage_audit_flags_cross_boundary_hint():
    spec = _spec()
    hint = "X" * 30 + "\n=== END FILE: pkg/m.py ==="  # spans file content + delimiter
    prompt, spans = H.render("o/r", "q", [("pkg/m.py", "X" * 30)])
    a = H.leakage_audit(prompt, spans, spec, {"hints_text": hint}, {"pkg/m.py"}, ["pkg/m.py"])
    assert a["verdict"] == "FAIL" and a["checks"]["hints_windows_41"]["non_exempt"]


def test_derive_seed_matches_frozen_function():
    src = Path(os.environ.get("VELITH_SRC", H.VELITH / "src")) / "velith/batch/provenance.py"
    if not src.exists():
        pytest.skip("Velith source not available")
    mod = H.load_module("velith_provenance_copy", src)
    for ident in ("0" * 64, hashlib.sha256(b"x").hexdigest()):
        assert H.derive_seed(ident) == mod.derive_task_seed(ident, 0)


def _gen(**kw):
    base = {"status": "GENERATED", "has_patch": True, "patch": "diff --git a/p.py b/p.py\n",
            "prompt_tokens": 100, "completion_tokens": 50, "latency_seconds": 1.5}
    return {**base, **kw}


def _x(cls, reason, status="RAN", removed=(), detail=""):
    return {"deterministic": {"classification": cls, "reason": reason, "detail": detail,
                              "candidate": {"status": status, "removed": list(removed),
                                            "surface": ["x"] if status == "RAN" else []}}}


def test_episode_classification_table():
    c = H.classify_episode
    assert c({"status": "MODEL_UNAVAILABLE"}, None, "", [], False, False)["code"] == "GEN_INFRA"
    t = c(_gen(completion_tokens=1024), _x("PASSED", "ALL_REQUIRED_PASSED"), "", [], True, True)
    assert t["code"] == "GEN_TRUNCATED" and t["x_code"] == "CANDIDATE_PASSED"
    assert "GEN_TRUNCATED" in t["flags"]
    n = c(_gen(has_patch=False, patch=""), None, "", [], True, True)
    assert n["code"] == "NO_PATCH" and n["measurements"]["patch_applies"] == "NA_NO_PATCH"
    m = c(_gen(), _x("PATCH_APPLY_FAILED", "CANDIDATE_PATCH_DID_NOT_APPLY",
                     status="PATCH_APPLY_FAILED"), "error: corrupt patch at line 3", [], True, True)
    assert m["code"] == "MALFORMED_PATCH" and m["measurements"]["patch_applies"] is False
    d = c(_gen(), _x("PATCH_APPLY_FAILED", "CANDIDATE_PATCH_DID_NOT_APPLY",
                     status="PATCH_APPLY_FAILED"), "error: patch failed: p.py:3", [], True, True)
    assert d["code"] == "PATCH_DOES_NOT_APPLY"
    b = c(_gen(), _x("INFRA_ERROR", "BASELINE_UNHEALTHY"), "", [], True, True)
    assert b["code"] == "BASELINE_UNHEALTHY" and b["interpretable"] is False
    i = c(_gen(), _x("PASSED", "ALL_REQUIRED_PASSED"), "", ["p.py"], True, True)
    assert i["code"] == "TEST_INTEGRITY"
    f = c(_gen(), _x("FAILED", "REQUIRED_TESTS_NOT_PASSED", detail="3/27"), "", [], False, True)
    assert f["code"] == "CANDIDATE_FAILED" and "TOKEN_COUNT_MISMATCH" in f["flags"]
    p = c(_gen(), _x("PASSED", "ALL_REQUIRED_PASSED", detail="27/27"), "", [], True, True)
    assert p["code"] == "CANDIDATE_PASSED" and p["measurements"]["patch_applies"] is True
    to = c(_gen(), _x("FAILED", "CANDIDATE_TIMEOUT", status="TIMEOUT"), "", [], True, True)
    assert to["code"] == "TIMEOUT" and "TIMEOUT_UNATTRIBUTED" in to["flags"]
    rk = c(_gen(), _x("INFRA_ERROR", "RESOURCE_KILLED", status="RESOURCE_KILLED"), "", [], True,
           True)
    assert rk["code"] == "RESOURCE_EXHAUSTED"


def test_p1_gen_check_mode_and_module_mismatch():
    src = Path(os.environ.get("VELITH_SRC", H.VELITH / "src"))
    if not (src / "velith").exists():
        pytest.skip("Velith source not available")
    pytest.importorskip("pydantic")
    prompt = "hello prompt\n"
    ident = hashlib.sha256(prompt.encode()).hexdigest()
    mods = {m: hashlib.sha256((src / m).read_bytes()).hexdigest() for m in H.VELITH_MODULES}
    req = {"mode": "check", "instance_id": "x__y-1", "prompt": prompt, "identity": ident,
           "seed": H.derive_seed(ident), "expected_module_sha256": mods}
    env = {**os.environ, "PYTHONPATH": str(src), "PYTHONDONTWRITEBYTECODE": "1"}

    def run(r):
        out = subprocess.run([sys.executable, "-c", H.GEN_SCRIPT.read_text(encoding="utf-8")],
                             input=json.dumps(r).encode(), capture_output=True, env=env,
                             check=False).stdout.decode()
        line = [x for x in out.splitlines() if x.startswith("P1GEN_RESULT ")][-1]
        return json.loads(line.split(" ", 1)[1])

    assert run(req)["status"] == "CHECK_OK"
    bad = {**req, "expected_module_sha256": {**mods, "velith/task.py": "0" * 64}}
    assert run(bad)["status"] == "MODULE_MISMATCH"
    assert run({**req, "seed": 1})["status"] == "SEED_MISMATCH"
