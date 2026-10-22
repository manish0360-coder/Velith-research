"""IC-1 tests: synthetic fixtures only (no real tasks, datasets, network or model).

General tests use deliberately non-P1 synthetic configuration, so that no P1 value is silently
treated as a Stage-1 default. Constants named ``P1_ONLY_*`` replicate frozen P1 harness values
(``p1/harness/p1_harness.py``, read-only, never imported) and are used ONLY in tests whose names
start with ``test_p1_only_``.
"""

from __future__ import annotations

import ast
import builtins
import hashlib
import importlib.util
import json
import os
import random
import socket
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

import material_builder as mb

MODULE = Path(mb.__file__).resolve()


def char_tok(text: str) -> int:
    """Synthetic deterministic tokenizer: one token per character."""
    return len(text)


# ---- synthetic (non-P1) configuration ----------------------------------------------------------
SYN_POLICY = mb.ExclusionPolicy(
    include_suffixes=(".py",),
    allowed_modes=frozenset({"100644", "100755"}),
    test_dir_names=frozenset({"tests"}),
    test_file_names=frozenset({"conftest.py"}),
    test_file_prefixes=("test_",),
    test_file_suffixes=("_test.py",),
    vendored_dir_names=frozenset({"vendored_x"}),
    protected_basenames=frozenset({"settings_x.py"}),
    protected_paths=frozenset({"pkg/protected_mod.py"}),
)
SYN_PARAMS = mb.RetrievalParams(k1=1.5, b=0.5, top_k=3, token_pattern=r"[A-Za-z_]+",
                                lowercase=True, per_file_cap_tokens=None)
SYN_TEMPLATE = mb.PromptTemplate(
    preamble="SYN repo={repo}\n", issue_heading="[issue]\n", files_heading="\n[files]\n",
    file_open="<<{path}>>\n", file_close="<</{path}>>", file_separator="\n", tail="\n[end]\n")
BIG_BUDGET = mb.PromptBudget(context_limit=100_000, output_reserve=1_000, safety_margin=100)
ISSUE = "parse_header fails on empty header value; parse_header should return default"


def syn_tree() -> list[mb.SourceFile]:
    def f(path: str, text: str | bytes, mode: str = "100644") -> mb.SourceFile:
        data = text if isinstance(text, bytes) else text.encode("utf-8")
        return mb.SourceFile(path, data, mode, mb.git_blob_oid(data))

    return [
        f("pkg/core.py", "def parse_header(value):\n    return value.split(':')\n"),
        f("pkg/util.py", "def default():\n    return None  # header default\n"),
        f("pkg/other.py", "def unrelated():\n    return 1\n"),
        f("tests/test_core.py", "def test_parse_header():\n    assert parse_header('')\n"),
        f("pkg/test_mod.py", "parse_header header\n"),
        f("pkg/mod_test.py", "parse_header header\n"),
        f("conftest.py", "parse_header\n"),
        f("pkg/protected_mod.py", "parse_header header\n"),
        f("pkg/settings_x.py", "parse_header header\n"),
        f("vendored_x/lib.py", "parse_header header\n"),
        f("pkg/latin1.py", b"# parse_header \xff\xfe\n"),
        f("README.md", "parse_header header\n"),
        f("pkg/run.py", "def run():\n    parse_header('x')\n", mode="100755"),
        f("pkg/link.py", "pkg/core.py", mode="120000"),
    ]


def syn_build(**overrides: object) -> mb.BuildResult:
    kwargs: dict[str, object] = dict(
        repo="synthetic/repo", issue_text=ISSUE, tree=syn_tree(), policy=SYN_POLICY,
        params=SYN_PARAMS, material_budget=10_000, template=SYN_TEMPLATE, budget=BIG_BUDGET,
        tokenizer=char_tok)
    kwargs.update(overrides)
    return mb.build(**kwargs)  # type: ignore[arg-type]


# ---- 1. determinism: byte-identical material and prompt ----------------------------------------
def test_repeat_build_is_byte_identical() -> None:
    a, b = syn_build(), syn_build()
    assert mb.canonical_material_bytes(a.selection.material) == \
        mb.canonical_material_bytes(b.selection.material)
    assert a.material_text.encode() == b.material_text.encode()
    assert a.prompt.text.encode() == b.prompt.text.encode()
    assert a.prompt.spans == b.prompt.spans
    assert a.identity == b.identity
    assert a.selection.trace == b.selection.trace


def test_build_independent_of_tree_input_order() -> None:
    ref = syn_build()
    for seed in range(5):
        tree = syn_tree()
        random.Random(seed).shuffle(tree)
        r = syn_build(tree=tree)
        assert (r.identity, r.prompt.text, r.ranked) == (ref.identity, ref.prompt.text, ref.ranked)


def test_canonical_serialization_is_strict_json() -> None:
    m = mb.Material("r", "é issue\n", (("a.py", "x = 'ü'\n"),))
    text = mb.canonical_material_text(m)
    assert text == ('{"files":[{"content":"x = \'ü\'\\n","path":"a.py"}],"issue":"é issue\\n",'
                    '"repo":"r","schema":"velith.ic1.material.v1"}')
    assert json.loads(text)["files"][0]["path"] == "a.py"


# ---- 2/3. identity: template-independent, material-sensitive -----------------------------------
def test_template_change_does_not_change_identity() -> None:
    a = syn_build()
    alt = replace(SYN_TEMPLATE, preamble="COMPLETELY DIFFERENT HEADER {repo}\n" * 1,
                  tail="\n## other instructions\n" + "x" * 500)
    b = syn_build(template=alt)
    assert a.prompt.text != b.prompt.text
    assert a.template_id != b.template_id
    assert a.material_text == b.material_text
    assert a.identity == b.identity


def test_template_cannot_change_selection_even_when_prompt_is_tight() -> None:
    """Under P1's whole-prompt fit rule a longer template could drop a file and so change the
    identity. Here selection is budgeted on material only; a too-long prompt fails closed."""
    a = syn_build()
    huge = replace(SYN_TEMPLATE, tail="x" * 50_000)
    b = syn_build(template=huge)  # still within BIG_BUDGET
    assert b.selection.material == a.selection.material and b.identity == a.identity
    tight = mb.PromptBudget(context_limit=len(a.prompt.text) + 10, output_reserve=0,
                            safety_margin=0)
    syn_build(budget=tight)  # original template fits
    with pytest.raises(mb.BudgetError, match="exceeds prompt budget"):
        syn_build(template=huge, budget=tight)


def test_material_change_changes_identity() -> None:
    base = syn_build()
    assert syn_build(issue_text=ISSUE + "!").identity != base.identity
    assert syn_build(repo="synthetic/repo2").identity != base.identity
    tree = [replace(f, content=f.content + b"# edit\n", oid=None) if f.path == "pkg/core.py"
            else f for f in syn_tree()]
    assert syn_build(tree=tree).identity != base.identity
    m = base.selection.material
    reordered = mb.Material(m.repo, m.issue_text, tuple(reversed(m.files)))
    assert len(m.files) >= 2 and mb.material_identity(reordered) != base.identity


def test_identity_is_sha256_of_canonical_bytes() -> None:
    r = syn_build()
    assert r.identity == hashlib.sha256(r.material_text.encode("utf-8")).hexdigest()


def test_identity_matches_velith_task_identity_rule(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cross-check against the ratified Velith rule, loaded by file path (no package import)."""
    path = os.environ.get("VELITH_MANIFEST")
    if not path or not Path(path).is_file():
        pytest.skip("VELITH_MANIFEST not set; formula is checked by the previous test")
    spec = importlib.util.spec_from_file_location("_velith_manifest_readonly", path)
    assert spec is not None and spec.loader is not None
    manifest = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, manifest)  # removed again after the test
    spec.loader.exec_module(manifest)
    r = syn_build()
    assert manifest.task_identity(r.material_text) == r.identity


# ---- 4. deterministic retrieval and tie-breaking -----------------------------------------------
def test_constructed_score_ties_break_by_path_bytes() -> None:
    body = b"def parse_header():\n    pass\n"
    tree = [mb.SourceFile(p, body) for p in ("zeta/m.py", "alpha/m.py", "mid/m.py")]
    tree.append(mb.SourceFile("other.py", b"def unrelated():\n    pass\n"))
    pool = mb.build_pool(tree, SYN_POLICY)
    ranked = mb.bm25_rank("parse_header", pool, SYN_PARAMS)
    assert len({s for s, _ in ranked}) == 1  # an exact tie was constructed
    assert [p for _, p in ranked] == ["alpha/m.py", "mid/m.py", "zeta/m.py"]
    assert "other.py" not in [p for _, p in ranked]  # score 0 excluded


def test_ranking_order_and_top_k() -> None:
    r = syn_build()
    scores = [s for s, _ in r.ranked]
    assert scores == sorted(scores, reverse=True) and all(s > 0 for s in scores)
    assert [p for p, _ in r.selection.material.files] == [p for _, p in r.ranked[:SYN_PARAMS.top_k]]
    r1 = syn_build(params=replace(SYN_PARAMS, top_k=1))
    assert [p for p, _ in r1.selection.material.files] == [r.ranked[0][1]]


def test_retrieval_params_are_injected_not_hardcoded() -> None:
    pool = mb.build_pool(syn_tree(), SYN_POLICY)
    a = mb.bm25_rank(ISSUE, pool, SYN_PARAMS)
    b = mb.bm25_rank(ISSUE, pool, replace(SYN_PARAMS, k1=0.3, b=1.0))
    assert [s for s, _ in a] != [s for s, _ in b]
    upper = mb.bm25_rank("PARSE_HEADER", pool, replace(SYN_PARAMS, lowercase=False))
    assert upper == ()


# ---- 5. exclusions (injected) ------------------------------------------------------------------
def test_exclusions_are_enforced_with_reasons() -> None:
    pool = mb.build_pool(syn_tree(), SYN_POLICY)
    assert sorted(pool.paths) == ["pkg/core.py", "pkg/other.py", "pkg/run.py", "pkg/util.py"]
    assert dict(pool.excluded) == {
        "README.md": "not_included_type",
        "conftest.py": "test",
        "pkg/latin1.py": "non_utf8",
        "pkg/link.py": "not_included_type",
        "pkg/mod_test.py": "test",
        "pkg/protected_mod.py": "protected_path",
        "pkg/settings_x.py": "protected_basename",
        "pkg/test_mod.py": "test",
        "tests/test_core.py": "test",
        "vendored_x/lib.py": "vendored",
    }
    keys = [p.encode() for p, _ in pool.excluded]
    assert keys == sorted(keys)


def test_excluded_files_never_reach_prompt() -> None:
    r = syn_build()
    excluded = {p for p, _ in r.pool.excluded}
    assert not excluded & {p for p, _ in r.selection.material.files}
    for p in excluded:
        assert f"<<{p}>>" not in r.prompt.text


def test_exclusion_sets_are_injected() -> None:
    no_vendor = replace(SYN_POLICY, vendored_dir_names=frozenset())
    assert "vendored_x/lib.py" in mb.build_pool(syn_tree(), no_vendor).paths
    other_od5 = replace(SYN_POLICY, protected_paths=frozenset({"pkg/core.py"}),
                        protected_basenames=frozenset())
    pool = mb.build_pool(syn_tree(), other_od5)
    assert "pkg/core.py" not in pool.paths and "pkg/protected_mod.py" in pool.paths
    assert "pkg/settings_x.py" in pool.paths
    with_md = replace(SYN_POLICY, include_suffixes=(".py", ".md"))
    assert "README.md" in mb.build_pool(syn_tree(), with_md).paths


def test_blob_id_mismatch_and_duplicates_fail_closed() -> None:
    with pytest.raises(mb.IntegrityError, match="blob id mismatch"):
        mb.build_pool([mb.SourceFile("a.py", b"x", oid="0" * 40)], SYN_POLICY)
    with pytest.raises(mb.IntegrityError, match="duplicate"):
        mb.build_pool([mb.SourceFile("a.py", b"x"), mb.SourceFile("a.py", b"y")], SYN_POLICY)
    for bad in ("/abs.py", "../up.py", "a\\b.py", "a//b.py", "./a.py", ""):
        with pytest.raises(mb.ConfigError):
            mb.build_pool([mb.SourceFile(bad, b"x")], SYN_POLICY)


# ---- 7. fail closed: tokenizer, budgets, configuration -----------------------------------------
def test_tokenizer_exception_fails_closed() -> None:
    def boom(_: str) -> int:
        raise RuntimeError("tokenizer unavailable")

    with pytest.raises(mb.TokenizerError, match="RuntimeError"):
        syn_build(tokenizer=boom)


@pytest.mark.parametrize("value", [-1, 1.5, True, "3", None])
def test_tokenizer_non_count_fails_closed(value: object) -> None:
    with pytest.raises(mb.TokenizerError, match="non-count"):
        syn_build(tokenizer=lambda _s: value)


def test_tokenizer_failure_late_in_selection_fails_closed() -> None:
    calls = {"n": 0}

    def flaky(text: str) -> int:
        calls["n"] += 1
        if calls["n"] == 3:
            raise ValueError("late failure")
        return len(text)

    with pytest.raises(mb.TokenizerError):
        syn_build(tokenizer=flaky)


def test_non_callable_tokenizer_is_config_error() -> None:
    with pytest.raises(mb.ConfigError):
        syn_build(tokenizer=42)


def test_issue_over_material_budget_fails_closed() -> None:
    with pytest.raises(mb.BudgetError, match="issue material alone"):
        syn_build(material_budget=10)


@pytest.mark.parametrize("value", [0, -5, True, 1.0])
def test_invalid_material_budget_fails_closed(value: object) -> None:
    with pytest.raises(mb.BudgetError):
        syn_build(material_budget=value)


def test_prompt_budget_cannot_be_established() -> None:
    with pytest.raises(mb.BudgetError):
        mb.PromptBudget(context_limit=100, output_reserve=60, safety_margin=40)
    for bad in (-1, True, 1.5):
        with pytest.raises(mb.ConfigError):
            mb.PromptBudget(context_limit=bad, output_reserve=0, safety_margin=0)  # type: ignore[arg-type]
    assert mb.PromptBudget(8192, 1024, 64).prompt_budget == 7104


def test_prompt_over_budget_fails_closed_without_dropping_files() -> None:
    ref = syn_build()
    n = len(ref.prompt.text)
    with pytest.raises(mb.BudgetError, match="exceeds prompt budget"):
        syn_build(budget=mb.PromptBudget(n - 1, 0, 0))
    ok = syn_build(budget=mb.PromptBudget(n, 0, 0))
    assert ok.prompt.text == ref.prompt.text and ok.prompt_tokens == n


def test_material_fit_skips_are_recorded_never_silent() -> None:
    ref = syn_build()
    first = mb.canonical_material_text(mb.Material(
        "synthetic/repo", ISSUE, ref.selection.material.files[:1]))
    r = syn_build(material_budget=len(first))
    decisions = {t["path"]: t["decision"] for t in r.selection.trace}
    top = ref.ranked[0][1]
    assert [p for p, _ in r.selection.material.files] == [top]
    assert decisions[top] == "included"
    assert all(decisions[p] == "skipped_does_not_fit" for _, p in r.ranked[1:])
    for p, c in r.selection.material.files:  # never truncated
        assert c == dict((f.path, f.text) for f in r.pool.files)[p]


def test_per_file_cap_is_injected_and_recorded() -> None:
    r = syn_build(params=replace(SYN_PARAMS, per_file_cap_tokens=40))
    decisions = {t["path"]: t["decision"] for t in r.selection.trace}
    assert decisions["pkg/core.py"] == "skipped_per_file_cap"
    assert "pkg/core.py" not in {p for p, _ in r.selection.material.files}


@pytest.mark.parametrize("field,value", [
    ("k1", 0), ("k1", float("nan")), ("k1", True), ("b", 1.5), ("b", -0.1), ("top_k", 0),
    ("top_k", 2.0), ("token_pattern", ""), ("token_pattern", "("), ("lowercase", 1),
    ("per_file_cap_tokens", 0)])
def test_invalid_retrieval_params(field: str, value: object) -> None:
    with pytest.raises(mb.ConfigError):
        replace(SYN_PARAMS, **{field: value})  # type: ignore[arg-type]


@pytest.mark.parametrize("field,value", [
    ("include_suffixes", ()), ("include_suffixes", [".py"]), ("allowed_modes", frozenset()),
    ("vendored_dir_names", {"x"}), ("protected_paths", frozenset({"/abs.py"})),
    ("test_file_prefixes", ("",))])
def test_invalid_exclusion_policy(field: str, value: object) -> None:
    with pytest.raises(mb.ConfigError):
        replace(SYN_POLICY, **{field: value})  # type: ignore[arg-type]


def test_invalid_template_and_injected_objects() -> None:
    with pytest.raises(mb.ConfigError):
        replace(SYN_TEMPLATE, preamble="{repo}{repo}")
    with pytest.raises(mb.ConfigError):
        replace(SYN_TEMPLATE, tail=None)  # type: ignore[arg-type]
    with pytest.raises(mb.ConfigError):
        syn_build(policy={"vendored": []})
    with pytest.raises(mb.ConfigError):
        syn_build(params={"k1": 1.2})


# ---- rendering ---------------------------------------------------------------------------------
def test_render_spans_and_no_format_injection() -> None:
    m = mb.Material("r{x}", "issue {path} {repo} {0}", (("a.py", "x"), ("b.py", "y\n")))
    p = mb.render_prompt(m, SYN_TEMPLATE)
    assert p.text == ("SYN repo=r{x}\n[issue]\nissue {path} {repo} {0}\n[files]\n"
                      "<<a.py>>\nx\n<</a.py>>\n<<b.py>>\ny\n<</b.py>>\n[end]\n")
    for label, s, e in p.spans:
        expected = {"metadata": "r{x}", "issue": m.issue_text, "file:a.py": "x",
                    "file:b.py": "y\n"}[label]
        assert p.text[s:e] == expected


# ---- 6. synthetic leakage audit: region and kind attribution -----------------------------------
GOLD = ("--- a/pkg/core.py\n+++ b/pkg/core.py\n"
        "-    return value.split(':')\n+    return value.split(':') if value else DEFAULT_SENTINEL\n")
TESTP = ("--- a/tests/test_core.py\n+++ b/tests/test_core.py\n"
         "+def test_empty_header_returns_default_sentinel():\n")


def leak_prompt() -> tuple[mb.RenderedPrompt, mb.Material]:
    m = mb.Material(
        "synthetic/repo",
        "Header bug. Hint: use DEFAULT_SENTINEL when empty. Ends with SPAN_A",
        (("pkg/core.py", "def parse_header(value):\n    return value.split(':')\n"),
         ("pkg/util.py", "HIDDEN_FIXTURE_TOKEN = 1\nPROTECTED_SURFACE_KNOB = 2\n")))
    tpl = replace(SYN_TEMPLATE, issue_heading="[issue]\n", files_heading="SPAN_B\n[files]\n",
                  tail="\n[end] TEMPLATE_ONLY_MARK\n")
    return mb.render_prompt(m, tpl), m


def test_leakage_attributed_by_region_and_kind() -> None:
    prompt, m = leak_prompt()
    needles = mb.Needles(
        gold_patch=GOLD, test_patch=TESTP,
        hidden_test_material=("HIDDEN_FIXTURE_TOKEN",),
        test_ids=("tests/test_core.py::test_empty_header_returns_default_sentinel",),
        hints="use DEFAULT_SENTINEL when empty", hint_window=12,
        identifiers=("TEMPLATE_ONLY_MARK", "synthetic/repo", "DEFAULT_SENTINEL"),
        protected_surface=("PROTECTED_SURFACE_KNOB", "SPAN_ASPAN_B"))
    rep = mb.audit_leakage(prompt, needles, pool_paths=frozenset({"pkg/core.py", "pkg/util.py"}),
                           included_paths=frozenset(p for p, _ in m.files))
    t = rep.occurrences_by_kind_region
    assert t["identifier"] == {"issue": 1, "metadata": 1, "template": 1}
    assert t["gold_hunk_line"] == {"retrieved_files": 1}  # "return value.split(':')"
    assert t["hidden_test_material"] == {"retrieved_files": 1}
    assert t["protected_surface"] == {"cross_boundary": 1, "retrieved_files": 1}
    assert set(t["hint_window"]) == {"issue"} and t["hint_window"]["issue"] > 0
    assert t["test_id"] == {} and t["test_patch_hunk_line"] == {}
    assert t["gold_patch_full_text"] == {} and t["test_patch_full_text"] == {}
    for f in rep.findings:
        assert f.region in mb.REGIONS
        assert prompt.text[f.offset:f.offset + len(f.excerpt)] == f.excerpt
    # issue region: reported separately, never an exclusion
    assert str(rep.issue_region_report["policy"]).startswith("REPORT_ONLY")
    assert rep.issue_region_report["count"] == sum(1 for f in rep.findings if f.region == "issue")
    assert rep.issue_region_report["by_kind"] == {"hint_window": t["hint_window"]["issue"],
                                                  "identifier": 1}
    assert not any("issue" in h for h in rep.hard_failures)
    assert rep.hard_failures == ("cross_boundary:protected_surface",)


def test_template_region_isolated_from_material_regions() -> None:
    prompt, m = leak_prompt()
    rep = mb.audit_leakage(prompt, mb.Needles(identifiers=("[end]",)), frozenset(), frozenset())
    assert rep.occurrences_by_kind_region["identifier"] == {"template": 1}
    assert rep.hard_failures == () and rep.issue_region_report["count"] == 0


def test_full_patch_text_and_paths_are_structural_failures() -> None:
    m = mb.Material("r", "see patch", (("pkg/x.py", "# copied\n" + GOLD + TESTP),))
    prompt = mb.render_prompt(m, SYN_TEMPLATE)
    needles = mb.Needles(gold_patch=GOLD, test_patch=TESTP,
                         test_patch_paths=frozenset({"tests/test_core.py"}),
                         protected_paths=frozenset({"pkg/x.py"}))
    rep = mb.audit_leakage(prompt, needles, pool_paths=frozenset({"pkg/x.py", "tests/test_core.py"}),
                           included_paths=frozenset({"pkg/x.py"}))
    assert rep.occurrences_by_kind_region["gold_patch_full_text"] == {"retrieved_files": 1}
    assert rep.occurrences_by_kind_region["test_patch_full_text"] == {"retrieved_files": 1}
    assert set(rep.hard_failures) == {
        "gold_patch_full_text_present", "test_patch_full_text_present",
        "test_patch_paths_in_pool", "protected_paths_in_pool", "protected_paths_in_prompt"}


def test_needles_validation() -> None:
    with pytest.raises(mb.ConfigError):
        mb.Needles(identifiers=("",))
    with pytest.raises(mb.ConfigError):
        mb.Needles(hidden_test_material=["x"])  # type: ignore[arg-type]
    with pytest.raises(mb.ConfigError):
        mb.Needles(hints="some hint", hint_window=0)


def test_hunk_lines() -> None:
    assert mb.hunk_lines(GOLD) == ["return value.split(':')",
                                   "return value.split(':') if value else DEFAULT_SENTINEL"]


# ---- P1-ONLY compatibility fixtures (frozen P1 values; NOT Stage-1 configuration) --------------
P1_ONLY_VENDORED = frozenset({"extern", "externals", "_vendor", "vendor", "vendored", "third_party",
                              "cextern", "_externals", "build", "dist"})
P1_ONLY_POLICY = mb.ExclusionPolicy(
    include_suffixes=(".py",), allowed_modes=frozenset({"100644", "100755"}),
    test_dir_names=frozenset({"test", "tests", "testing"}),
    test_file_names=frozenset({"conftest.py"}), test_file_prefixes=("test_",),
    test_file_suffixes=("_test.py",), vendored_dir_names=P1_ONLY_VENDORED,
    protected_basenames=frozenset({"setup.cfg", "pyproject.toml", "tox.ini", "pytest.ini",
                                   "conftest.py"}),
    protected_paths=frozenset())
P1_ONLY_PARAMS = mb.RetrievalParams(k1=1.2, b=0.75, top_k=5, token_pattern=r"[A-Za-z0-9_]+",
                                    lowercase=True, per_file_cap_tokens=None)
P1_ONLY_TEMPLATE = mb.PromptTemplate(
    preamble=("You are fixing a bug in the Python repository `{repo}` at a fixed commit.\n"
              "You cannot run code or see any files other than those shown below.\n\n"),
    issue_heading="## Issue\n",
    files_heading="\n\n## Source files (retrieved automatically from the repository; "
                  "may be incomplete)\n",
    file_open="=== FILE: {path} ===\n", file_close="=== END FILE: {path} ===",
    file_separator="\n\n",
    tail=("\n\n## Instructions\n"
          "Reply with exactly one fenced ```diff block containing a single unified diff that "
          "fixes the issue.\n"
          "Use git-style paths relative to the repository root, prefixed a/ and b/\n"
          "(for example: --- a/pkg/module.py and +++ b/pkg/module.py).\n"
          "Copy unchanged context lines exactly as they appear in the files above.\n"
          "Do not modify or add test files. Do not include any text outside the diff block.\n"))


def test_p1_only_render_reproduces_p1_layout() -> None:
    m = mb.Material("o/r", "bug", (("a.py", "x"), ("b.py", "")))
    text = mb.render_prompt(m, P1_ONLY_TEMPLATE).text
    expected = (P1_ONLY_TEMPLATE.preamble.replace("{repo}", "o/r") + "## Issue\n" + "bug"
                + P1_ONLY_TEMPLATE.files_heading
                + "=== FILE: a.py ===\nx\n=== END FILE: a.py ===" + "\n\n"
                + "=== FILE: b.py ===\n=== END FILE: b.py ===" + P1_ONLY_TEMPLATE.tail)
    assert text == expected


def test_p1_only_exclusion_order_and_vendored_names() -> None:
    tree = [mb.SourceFile(p, b"x = 1\n") for p in (
        "build/tests/m.py", "pkg/vendor/m.py", "dist/m.py", "pkg/testing/m.py", "pkg/ok.py")]
    reasons = dict(mb.build_pool(tree, P1_ONLY_POLICY).excluded)
    assert reasons == {"build/tests/m.py": "test", "pkg/vendor/m.py": "vendored",
                       "dist/m.py": "vendored", "pkg/testing/m.py": "test"}
    # The P1 vendored list is a P1 fixture only; it is not claimed comprehensive.
    assert "site-packages/m.py" in mb.build_pool(
        [mb.SourceFile("site-packages/m.py", b"x\n")], P1_ONLY_POLICY).paths


def test_p1_only_bm25_digits_in_tokens() -> None:
    pool = mb.build_pool([mb.SourceFile("a.py", b"h2o = 1\n"), mb.SourceFile("b.py", b"h = 1\n")],
                         P1_ONLY_POLICY)
    assert [p for _, p in mb.bm25_rank("h2o", pool, P1_ONLY_PARAMS)] == ["a.py"]
    # The synthetic pattern splits on digits, so "h" also matches b.py: the pattern is injected.
    assert {p for _, p in mb.bm25_rank("h2o", pool, SYN_PARAMS)} == {"a.py", "b.py"}


# ---- 8. anti-drift boundary --------------------------------------------------------------------
ALLOWED_IMPORTS = {"__future__", "hashlib", "json", "math", "re", "collections",
                   "collections.abc", "dataclasses"}


def test_module_imports_are_stdlib_allowlist_only() -> None:
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0 and node.module
            found.add(node.module)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"open", "__import__", "exec", "eval", "compile"}
    assert found <= ALLOWED_IMPORTS, found - ALLOWED_IMPORTS


def test_fresh_import_loads_no_network_dataset_or_llm_modules() -> None:
    code = ("import sys; sys.path.insert(0, sys.argv[1]); import material_builder; "
            "print('\\n'.join(sorted(sys.modules)))")
    out = subprocess.run([sys.executable, "-I", "-B", "-c", code, str(MODULE.parent)],
                         capture_output=True, text=True, check=True, timeout=60).stdout.split()
    forbidden = ("socket", "ssl", "http", "urllib", "requests", "httpx", "datasets",
                 "huggingface_hub", "velith", "anthropic", "openai", "ollama", "subprocess")
    bad = [m for m in out if m.split(".")[0] in forbidden]
    assert bad == [], bad


def test_build_runs_with_network_files_and_processes_blocked(monkeypatch: pytest.MonkeyPatch
                                                             ) -> None:
    def deny(*_a: object, **_k: object) -> None:
        raise AssertionError("forbidden side effect")

    monkeypatch.setattr(socket, "socket", deny)
    monkeypatch.setattr(socket, "create_connection", deny)
    monkeypatch.setattr(subprocess, "Popen", deny)
    monkeypatch.setattr(builtins, "open", deny)
    r = syn_build()
    rep = mb.audit_leakage(r.prompt, mb.Needles(gold_patch=GOLD), r.pool.paths,
                           frozenset(p for p, _ in r.selection.material.files))
    assert r.identity and isinstance(rep.hard_failures, tuple)


def test_no_dataset_or_llm_module_loaded_in_test_process() -> None:
    loaded = {m.split(".")[0] for m in sys.modules}
    assert not loaded & {"datasets", "huggingface_hub", "velith", "anthropic", "openai", "ollama"}
