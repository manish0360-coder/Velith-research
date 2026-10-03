"""FG-2 deterministic test suite for the P2 harness. Synthetic inputs only.

No model, no Docker, no image, no lottery, no network. Diff synthesis is exercised by running
the exact synthesis script in a local git repository instead of a container.

Run:  PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider \
          p2/harness/test_p2_harness.py
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import itertools
import re
import subprocess
import sys
from collections.abc import Mapping
from fractions import Fraction
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import p2_edits as E  # noqa: E402
import p2_harness as H  # noqa: E402

B = E.BaseFile


def blk(path: str, search: str, replace: str) -> str:
    return f"<<<<<<< SEARCH {path}\n{search}=======\n{replace}>>>>>>> REPLACE\n"


BASE = {
    "pkg/a.py": B("100644", b"def f():\n    return 1\n\n\ndef g():\n    return 2\n"),
    "pkg/b.py": B("100755", b"x = 1\ny = 2\n"),
    "pkg/dup.py": B("100644", b"a\na\na\n"),
    "pkg/noeol.py": B("100644", b"first\nlast"),
    "pkg/crlf.py": B("100644", b"one\r\ntwo\r\n"),
    "link.py": B("120000", b"pkg/a.py"),
}


# ---- frozen-spec fidelity ---------------------------------------------------------------------
def _spec_block(label: str) -> str:
    text = H.SPEC.read_text(encoding="utf-8")
    after = text.split(label, 1)[1]
    m = re.search(r"^```\n(.*?)^```$", after, flags=re.MULTILINE | re.DOTALL)
    assert m
    return m.group(1)


def test_spec_and_p1_pins() -> None:
    H.check_spec()
    assert hashlib.sha256(H.P1_HARNESS.read_bytes()).hexdigest() == H.P1_HARNESS_SHA256


def test_contract_texts_are_the_frozen_spec_bytes() -> None:
    spec_s = _spec_block("**CONTRACT_S** [G-2, RATIFIED verbatim]:")
    spec_u = _spec_block("**CONTRACT_U**: the remainder of the P1 OD-2 template")
    assert spec_s == H.CONTRACT_S
    assert spec_u == H.contract_u()


# ---- prompts: COMMON byte-identical; only the contract differs (Amendment A, G-6) ------------
def test_common_prompt_bytes_identical_and_shared_seed() -> None:
    p = H.build_prompts("o/r", "Issue text\n", [("pkg/a.py", "def f():\n    return 1\n")])
    assert p.common.endswith("\n\n## Instructions\n")
    assert p.prompt_u.encode()[: len(p.common.encode())] == p.common.encode()
    assert p.prompt_s.encode()[: len(p.common.encode())] == p.common.encode()
    assert p.prompt_u[len(p.common):] == H.contract_u()
    assert p.prompt_s[len(p.common):] == H.CONTRACT_S
    assert p.prompt_u == H.p1().render("o/r", "Issue text\n", [("pkg/a.py",
                                       "def f():\n    return 1\n")])[0]  # U = P1 rendering
    assert p.common_identity == hashlib.sha256(p.common.encode()).hexdigest()
    assert p.seed == H.p1().derive_seed(p.common_identity)  # one seed, from COMMON only
    assert p.identity_u != p.identity_s


# ---- parser -----------------------------------------------------------------------------------
def test_parse_valid_single_and_multi_with_separator_lines() -> None:
    text = (blk("pkg/a.py", "    return 1\n", "    return 10\n") + "\n"
            + blk("pkg/b.py", "y = 2\n", ""))
    r = E.parse(text)
    assert r.code == E.OK and [b.path for b in r.blocks] == ["pkg/a.py", "pkg/b.py"]
    assert r.blocks[0].search == b"    return 1\n" and r.blocks[1].replace == b""


def test_region_selection_first_fence_tag_and_prose_outside() -> None:
    inner = blk("pkg/b.py", "x = 1\n", "x = 3\n")
    for tag in ("diff", "Patch", " udiff ", "python", ""):
        out = f"Here is the fix:\n```{tag}\n{inner}```\nThanks, more prose.\n```\nignored\n```"
        assert E.parse(out).code == E.OK
    assert E.parse("prose before\n" + inner).code == E.S_MALFORMED_BLOCK  # unfenced prose
    assert E.parse(f"```\nnote\n{inner}```").code == E.S_MALFORMED_BLOCK  # prose inside region
    assert E.parse("   \n").code == E.NO_OUTPUT
    assert E.parse("``````").code == E.NO_OUTPUT


@pytest.mark.parametrize("bad", [
    "<<<<<< SEARCH pkg/b.py\nx = 1\n=======\nx\n>>>>>>> REPLACE",     # 6 '<'
    "<<<<<<<< SEARCH pkg/b.py\nx = 1\n=======\nx\n>>>>>>> REPLACE",   # 8 '<'
    "<<<<<<< SEARCH  pkg/b.py\nx = 1\n=======\nx\n>>>>>>> REPLACE",   # double space
    "<<<<<<< SEARCH pkg/b.py\nx = 1\n======\nx\n>>>>>>> REPLACE",     # 6 '='
    "<<<<<<< SEARCH pkg/b.py\nx = 1\n=======\nx\n>>>>>> REPLACE",     # 6 '>'
    "<<<<<<< SEARCH pkg/b.py \nx = 1\n=======\nx\n>>>>>>> REPLACE",   # trailing space in PATH
    "<<<<<<< SEARCH pkg/b.py\r\nx = 1\n=======\nx\n>>>>>>> REPLACE",  # CR on marker line
    "<<<<<<< SEARCH pkg/b.py\n=======\nx\n>>>>>>> REPLACE",            # empty SEARCH
    "<<<<<<< SEARCH pkg/b.py\nx = 1\nx\n>>>>>>> REPLACE",              # no separator
    "<<<<<<< SEARCH pkg/b.py\nx = 1\n=======\nx\n",                    # no REPLACE line
    "<<<<<<< SEARCH /pkg/b.py\nx\n=======\ny\n>>>>>>> REPLACE",
    "<<<<<<< SEARCH a/pkg/b.py\nx\n=======\ny\n>>>>>>> REPLACE",
    "<<<<<<< SEARCH b/pkg/b.py\nx\n=======\ny\n>>>>>>> REPLACE",
    "<<<<<<< SEARCH pkg/../b.py\nx\n=======\ny\n>>>>>>> REPLACE",
    "<<<<<<< SEARCH pkg/my file.py\nx\n=======\ny\n>>>>>>> REPLACE",
])
def test_malformed_blocks(bad: str) -> None:
    assert E.parse(bad).code == E.S_MALFORMED_BLOCK


def test_region_edges_are_stripped_per_frozen_rule_only() -> None:
    inner = blk("pkg/b.py", "x = 1\n", "x = 3\n")
    assert E.parse("\n  " + inner + "   \n").code == E.OK  # region leading/trailing whitespace


def test_literal_reading_non_exact_marker_lines_are_content() -> None:
    # Frozen productions: search_line+ ends at the first exact SEP_LINE; replace_line* ends at
    # the first exact REPLACE_LINE. A near-marker line is therefore content, not a terminator.
    text = ("<<<<<<< SEARCH pkg/b.py\nx = 1\n=======\nx\n>>>>>>> REPLACE \n"
            "<<<<<<< SEARCH pkg/b.py\ny = 2\n=======\ny\n>>>>>>> REPLACE")
    r = E.parse(text)
    assert r.code == E.OK and len(r.blocks) == 1
    assert r.blocks[0].replace.startswith(b"x\n>>>>>>> REPLACE \n<<<<<<< SEARCH")


def test_whitespace_only_separator_line_is_malformed() -> None:
    text = blk("pkg/b.py", "x = 1\n", "x = 3\n") + "  \n" + blk("pkg/b.py", "y = 2\n", "y = 4\n")
    assert E.parse(text).code == E.S_MALFORMED_BLOCK


# ---- exact matcher: 0 / 1 / >1; no fuzzy matching ---------------------------------------------
def _resolve(text: str) -> E.Resolution:
    return E.parse_and_resolve(text, BASE)[1]


def test_zero_one_many_matches() -> None:
    assert _resolve(blk("pkg/a.py", "    return 3\n", "x\n")).code == E.S_SEARCH_NOT_FOUND
    assert _resolve(blk("pkg/a.py", "    return 1\n", "    return 9\n")).code == E.OK
    assert _resolve(blk("pkg/dup.py", "a\na\n", "b\n")).code == E.S_SEARCH_AMBIGUOUS  # overlapping
    assert _resolve(blk("pkg/a.py", "    return 2\n", "    return 3\n")).code == E.OK


def test_only_line_boundary_starts_count() -> None:
    assert _resolve(blk("pkg/a.py", "return 1\n", "return 9\n")).code == E.S_SEARCH_NOT_FOUND


@pytest.mark.parametrize("variant", ["    return 1 \n", "\treturn 1\n", "    Return 1\n",
                                     "    return  1\n", "    return 1\r\n"])
def test_no_fuzzy_or_normalized_matching(variant: str) -> None:
    assert _resolve(blk("pkg/a.py", variant, "x\n")).code == E.S_SEARCH_NOT_FOUND


def test_crlf_file_and_missing_final_newline_are_exact() -> None:
    assert _resolve(blk("pkg/crlf.py", "one\n", "uno\n")).code == E.S_SEARCH_NOT_FOUND
    assert _resolve(blk("pkg/noeol.py", "last\n", "end\n")).code == E.S_SEARCH_NOT_FOUND
    assert _resolve(blk("pkg/noeol.py", "first\n", "start\n")).code == E.OK


def test_path_invalid() -> None:
    assert _resolve(blk("pkg/missing.py", "x\n", "y\n")).code == E.S_PATH_INVALID
    assert _resolve(blk("link.py", "pkg/a.py\n", "y\n")).code == E.S_PATH_INVALID  # symlink


def _resolver_functions() -> list[ast.FunctionDef]:
    tree = ast.parse(Path(E.__file__).read_text(encoding="utf-8"))
    names = {"resolve", "match_positions", "line_starts", "parse"}
    return [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]


def test_static_no_repair_or_normalization_in_resolver_and_parser() -> None:
    forbidden = {"strip", "lstrip", "rstrip", "lower", "upper", "casefold", "replace",
                 "expandtabs", "normalize", "splitlines", "get_close_matches", "SequenceMatcher"}
    src = (Path(E.__file__).read_text(encoding="utf-8")
           + Path(H.__file__).read_text(encoding="utf-8"))
    assert "difflib" not in src and "fuzz" not in src.lower().replace("fuzzy matching", "")
    for fn in _resolver_functions():
        called = {n.func.attr for n in ast.walk(fn) if isinstance(n, ast.Call)
                  and isinstance(n.func, ast.Attribute)}
        assert not (called & forbidden), (fn.name, called & forbidden)


# ---- original-content matching, overlap, empty edit, multi-file -------------------------------
def test_original_content_not_cascading() -> None:
    text = blk("pkg/b.py", "x = 1\n", "x = 5\n") + blk("pkg/b.py", "x = 5\n", "x = 6\n")
    assert _resolve(text).code == E.S_SEARCH_NOT_FOUND


def test_overlap_and_adjacent() -> None:
    over = blk("pkg/b.py", "x = 1\ny = 2\n", "z\n") + blk("pkg/b.py", "y = 2\n", "w\n")
    r = _resolve(over)
    assert r.code == E.S_OVERLAP and [s["status"] for s in r.statuses] == [E.S_OVERLAP] * 2
    adj = blk("pkg/b.py", "x = 1\n", "x = 7\n") + blk("pkg/b.py", "y = 2\n", "y = 8\n")
    r2 = _resolve(adj)
    assert r2.code == E.OK and r2.edited["pkg/b.py"].content == b"x = 7\ny = 8\n"


def test_empty_edit() -> None:
    assert _resolve(blk("pkg/b.py", "x = 1\n", "x = 1\n")).code == E.S_EMPTY_EDIT


def test_multi_file_and_apply_in_span_order() -> None:
    text = (blk("pkg/a.py", "    return 2\n", "    return 20\n")
            + blk("pkg/b.py", "y = 2\n", "")
            + blk("pkg/a.py", "    return 1\n", "    return 10\n"))
    r = _resolve(text)
    assert r.code == E.OK and sorted(r.edited) == ["pkg/a.py", "pkg/b.py"]
    assert r.edited["pkg/a.py"].content == b"def f():\n    return 10\n\n\ndef g():\n    return 20\n"
    assert r.edited["pkg/b.py"] == B("100755", b"x = 1\n")


def test_first_failing_block_in_output_order_and_all_statuses_recorded() -> None:
    text = (blk("pkg/a.py", "    return 1\n", "x\n") + blk("pkg/dup.py", "a\n", "b\n")
            + blk("pkg/a.py", "nope\n", "x\n"))
    r = _resolve(text)
    assert r.code == E.S_SEARCH_AMBIGUOUS
    assert [s["status"] for s in r.statuses] == [E.RESOLVED, E.S_SEARCH_AMBIGUOUS,
                                                E.S_SEARCH_NOT_FOUND]


def test_deterministic_parse_and_resolve() -> None:
    text = blk("pkg/a.py", "    return 1\n", "    return 10\n") + blk("pkg/b.py", "y = 2\n", "")
    runs = [E.parse_and_resolve(text, BASE) for _ in range(3)]
    assert all(r == runs[0] for r in runs)


# ---- diff synthesis (same script, local git instead of a container) ---------------------------
def _git(repo: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=True).stdout


def _local_runner(_image: str, script: str, stdin: bytes) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["bash", "-c", script], input=stdin, capture_output=True, check=False)


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "testbed"
    r.mkdir()
    _git(r, "init", "-q")
    (r / "pkg").mkdir()
    for p in ("pkg/a.py", "pkg/b.py", "pkg/noeol.py"):
        (r / p).write_bytes(BASE[p].content)
    (r / "pkg/b.py").chmod(0o755)
    _git(r, "add", ".")
    _git(r, "-c", "user.email=a@b", "-c", "user.name=t", "commit", "-qm", "base")
    return r


def _base_from_repo(r: Path) -> dict[str, E.BaseFile]:
    p1 = H.p1()
    entries = p1.parse_ls_tree(_git(r, "ls-tree", "-r", "-l", "-z", "HEAD"))
    blobs = p1.parse_cat_file_batch(subprocess.run(
        ["git", "-C", str(r), "cat-file", "--batch"], input=b"".join(e[2].encode() + b"\n"
                                                                    for e in entries),
        capture_output=True, check=True).stdout)
    return {path: E.BaseFile(mode, blobs[oid]) for mode, _t, oid, path in entries}


def _applies_on_fresh_clone(r: Path, tmp: Path, diff: str) -> bool:
    clone = tmp / "clone"
    subprocess.run(["git", "clone", "-q", str(r), str(clone)], check=True)
    (tmp / "c.patch").write_text(diff, encoding="utf-8")
    return subprocess.run(["git", "-C", str(clone), "apply", str(tmp / "c.patch")],
                          capture_output=True).returncode == 0


def test_synthesis_deterministic_applies_and_keeps_mode(repo: Path, tmp_path: Path) -> None:
    base = _base_from_repo(repo)
    text = blk("pkg/a.py", "    return 1\n", "    return 10\n") + blk("pkg/b.py", "y = 2\n", "")
    _, res = E.parse_and_resolve(text, base)
    assert res.code == E.OK
    assert H.edited_tar(res.edited) == H.edited_tar(res.edited)
    d1 = H.synthesize_diff("img@sha256:x", str(repo), res.edited, _local_runner)
    _git(repo, "checkout", "-q", "--", ".")
    d2 = H.synthesize_diff("img@sha256:x", str(repo), res.edited, _local_runner)
    assert d1 == d2 and "old mode" not in d1 and "diff --git a/pkg/a.py b/pkg/a.py" in d1
    _git(repo, "checkout", "-q", "--", ".")
    assert _applies_on_fresh_clone(repo, tmp_path, d1)


def test_synthesis_handles_file_without_final_newline(repo: Path, tmp_path: Path) -> None:
    base = _base_from_repo(repo)
    _, res = E.parse_and_resolve(blk("pkg/noeol.py", "first\n", "start\n"), base)
    d = H.synthesize_diff("img", str(repo), res.edited, _local_runner)
    assert "\\ No newline at end of file" in d
    _git(repo, "checkout", "-q", "--", ".")
    assert _applies_on_fresh_clone(repo, tmp_path, d)


def test_synthesis_refuses_empty_edit() -> None:
    with pytest.raises(H.HarnessStop):
        H.synthesize_diff("img", "/nonexistent", {}, _local_runner)


# ---- same Stage-X gate for both arms (Amendment D) --------------------------------------------
def test_both_arms_use_the_same_unmodified_stage_x(monkeypatch: pytest.MonkeyPatch, repo: Path
                                                   ) -> None:
    calls: list[tuple[str, str]] = []

    def fake_stage_x(spec: dict, patch: str, run_dir: Path, timeout: float, case: str) -> dict:
        calls.append((patch, case))
        return {"deterministic": {"classification": "PASSED", "candidate": {"status": "RAN"}}}

    monkeypatch.setattr(H.p1(), "stage_x", fake_stage_x)
    base = _base_from_repo(repo)
    _, res = E.parse_and_resolve(blk("pkg/b.py", "x = 1\n", "x = 3\n"), base)
    s_diff = H.synthesize_diff("img", str(repo), res.edited, _local_runner)
    u_patch = "--- a/pkg/b.py\n+++ b/pkg/b.py\n@@ -1 +1 @@\n-x = 1\n+x = 3\n"
    xu = H.stage_x_gate({}, u_patch, Path("/tmp/u"), 900.0, "U")
    xs = H.stage_x_gate({}, s_diff, Path("/tmp/s"), 900.0, "S")
    assert calls == [(u_patch, "P2-X-U"), (s_diff, "P2-X-S")]  # identical gate, S gets the diff
    assert H.gate_pass(xu) is True and H.gate_pass(xs) is True
    with pytest.raises(H.HarnessStop):
        H.stage_x_gate({}, u_patch, Path("/tmp/x"), 900.0, "C")  # no third arm
    src = Path(H.__file__).read_text(encoding="utf-8")
    assert src.count("p1().stage_x(") == 1  # a single gate entry point


# ---- endpoints (§7, G-3) ----------------------------------------------------------------------
def _x(status: str, cls: str = "FAILED", surface: bool = True) -> dict:
    return {"deterministic": {"classification": cls,
                              "candidate": {"status": status, "surface": ["s"] if surface else []}}}


def test_endpoint_definitions() -> None:
    ok = E.Resolution(E.OK)
    assert H.u_applies(True, True, _x("RAN", "PASSED")) is True
    assert H.u_applies(True, True, _x("PATCH_APPLY_FAILED", surface=False)) is False
    assert H.u_applies(True, False, None) is False
    assert H.u_applies(False, False, None) == H.NA
    assert H.u_applies(True, True, _x("CONTAINER_START_FAILED", surface=False)) == H.NA
    assert H.s_applies(True, ok, _x("RAN")) is True
    for code in (E.NO_OUTPUT, E.S_MALFORMED_BLOCK, E.S_PATH_INVALID, E.S_SEARCH_NOT_FOUND,
                 E.S_SEARCH_AMBIGUOUS, E.S_OVERLAP, E.S_EMPTY_EDIT):
        assert H.s_applies(True, E.Resolution(code), None) is False
    assert H.s_applies(True, ok, _x("RAN"), aborted=True) == H.NA
    # G-3: a baseline problem does not change the primary endpoint
    x = _x("RAN", "INFRA_ERROR")
    assert H.u_applies(True, True, x) is True and H.verified_pass(True, x) is False
    assert H.verified_pass(True, _x("RAN", "PASSED")) is True
    assert H.verified_pass(False, None) is False and H.verified_pass(H.NA, None) == H.NA


# ---- G-10: diagnostic-only self-check ---------------------------------------------------------
GOLD = ("diff --git a/pkg/a.py b/pkg/a.py\n--- a/pkg/a.py\n+++ b/pkg/a.py\n"
        "@@ -1,2 +1,2 @@\n def f():\n-    return 1\n+    return 10\n")


def test_gold_to_blocks_uses_hunk_counts() -> None:
    gold = ("--- a/m.py\n+++ b/m.py\n@@ -1,2 +1,2 @@\n--- old dashes\n+++ new pluses\n keep\n")
    text, _ = H.gold_to_blocks(gold)
    r = E.parse(text)
    assert r.code == E.OK and r.blocks[0].search == b"-- old dashes\nkeep\n"
    assert r.blocks[0].replace == b"++ new pluses\nkeep\n"


def test_self_check_records_and_alarms_but_never_gates(repo: Path) -> None:
    base = _base_from_repo(repo)

    def synth(ed: Mapping[str, E.BaseFile]) -> str:
        out = H.synthesize_diff("img", str(repo), ed, _local_runner)
        _git(repo, "checkout", "-q", "--", ".")
        return out

    good = H.self_check(GOLD, base, synth, lambda d: _x("RAN"))
    bad = H.self_check(GOLD, base, synth, lambda d: _x("PATCH_APPLY_FAILED", surface=False))
    amb = H.self_check("--- a/pkg/dup.py\n+++ b/pkg/dup.py\n@@ -1,1 +1,1 @@\n-a\n+b\n",
                       {"pkg/dup.py": BASE["pkg/dup.py"]}, synth, lambda d: _x("RAN"))
    assert good["resolution_code"] == E.OK and good["gate"] is True
    assert not good["harness_integrity_alarm"] and good["diagnostic_only"]
    assert bad["harness_integrity_alarm"] is True  # A-1 halt signal, not a task outcome
    assert amb["resolution_code"] == E.S_SEARCH_AMBIGUOUS and amb["gate"] is None
    for steps in itertools.product([True, False], repeat=len(H.ADMISSION_STEPS)):
        s = dict(zip(H.ADMISSION_STEPS, steps, strict=True))
        decisions = {H.phase_a_record(s, rec)["admitted"] for rec in (good, bad, amb, None)}
        assert decisions == {all(steps)}  # identical for every self-check outcome


def test_admission_cannot_take_the_self_check() -> None:
    assert list(inspect.signature(H.admission_decision).parameters) == ["steps"]
    steps = dict.fromkeys(H.ADMISSION_STEPS, True)
    with pytest.raises(H.HarnessStop):
        H.admission_decision({**steps, "self_check": False})
    assert "self" not in " ".join(H.ADMISSION_STEPS)


# ---- statistics (§8) --------------------------------------------------------------------------
def test_sign_test_arithmetic() -> None:
    assert H.sign_test_p(5, 0) == Fraction(1, 32)
    assert H.sign_test_p(4, 0) == Fraction(1, 16)
    assert H.sign_test_p(8, 2) == Fraction(56, 1024)
    assert H.sign_test_p(0, 0) is None
    assert H.sign_test_p(0, 3) == 1


def test_paired_table_and_conclusions() -> None:
    pairs = [(False, True)] * 5 + [(False, False)] * 5 + [(H.NA, True)]
    t = H.paired_table(pairs)
    assert (t["n_v"], t["s_only"], t["u_only"], t["discordant"], t["k_s"]) == (10, 5, 0, 5, 5)
    assert H.conclusion(t, 0) == "P2-A"
    assert H.conclusion(H.paired_table([(False, True)] * 4 + [(False, False)] * 6), 0) == "P2-B"
    assert H.conclusion(H.paired_table([(False, False)] * 12), 0) == "P2-C"
    assert H.conclusion(H.paired_table([(False, True)] * 9), 0) == "P2-D"
    assert H.conclusion(t, 3) == "P2-D"
    assert H.conclusion(H.paired_table([(True, False)] * 10), 0) == "P2-B"
