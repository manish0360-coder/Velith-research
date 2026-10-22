"""IC-1: parametric reference implementation of the I-2 material/prompt builder (research only).

Scope (RD authorization, 2026-10-16): synthetic fixtures and local tests only. This module makes
no network request, imports no dataset loader or LLM client, selects or admits no real task,
runs no verification, and makes no generator-viability or base-rate claim. Standard library only.

Three explicit, deterministic operations:
  * canonical material serialization  -> ``canonical_material_text`` / ``canonical_material_bytes``
  * prompt rendering (material + injected template) -> ``render_prompt``
  * task identity = SHA-256 of the canonical material bytes -> ``material_identity``
    This equals Velith's ratified rule ``task_identity(material) = sha256(material.encode())``
    (D28 invariants; ``velith/corpus/manifest.py``) applied to the canonical material text.
    It is NOT P1's prompt-hash identity (P1 harness R2).

Every unresolved Stage-1 setting is INJECTED, never defaulted: exclusion policy (incl. OD-5 and
vendored directories), retrieval parameters, material budget, prompt budget, tokenizer and
template. Invalid configuration, tokenizer failure or an unestablished budget fails closed.

Design consequence (reported to the RD): so that a template change cannot change identity, file
selection is budgeted on the token count of the canonical MATERIAL text against an injected
material budget, not on the rendered prompt (P1 counted the whole prompt). The rendered prompt
is then checked against the prompt budget and fails closed if it does not fit; files are never
dropped or truncated to make it fit.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass

SCHEMA = "velith.ic1.material.v1"
REGIONS = ("template", "metadata", "issue", "retrieved_files", "cross_boundary")
ISSUE_POLICY = "REPORT_ONLY: issue-region policy is an open RD decision; no exclusion is applied"

Tokenizer = Callable[[str], int]


# ---- errors (all fail closed) ------------------------------------------------------------------
class IC1Error(Exception):
    """Base error. Every IC-1 failure is loud and typed; nothing degrades silently."""


class ConfigError(IC1Error):
    """An injected configuration is missing, malformed or inconsistent."""


class TokenizerError(IC1Error):
    """The injected tokenizer raised or returned a non-count."""


class BudgetError(IC1Error):
    """A budget cannot be established or is exceeded."""


class IntegrityError(IC1Error):
    """Input bytes are inconsistent (duplicate paths, blob-id mismatch, protected path in pool)."""


# ---- helpers -----------------------------------------------------------------------------------
def _check_path(path: str) -> None:
    if (not isinstance(path, str) or not path or path.startswith("/") or "\\" in path
            or "\0" in path or any(p in ("", ".", "..") for p in path.split("/"))):
        raise ConfigError(f"invalid repository-relative path: {path!r}")


def _str_set(value: object, name: str) -> None:
    if not isinstance(value, frozenset) or not all(isinstance(v, str) and v for v in value):
        raise ConfigError(f"{name} must be a frozenset of non-empty strings")


def _str_tuple(value: object, name: str) -> None:
    if not isinstance(value, tuple) or not all(isinstance(v, str) and v for v in value):
        raise ConfigError(f"{name} must be a tuple of non-empty strings")


def git_blob_oid(content: bytes) -> str:
    """Git's blob object id (SHA-1 of ``blob <len>\\0`` + content)."""
    return hashlib.sha1(b"blob %d\0" % len(content) + content).hexdigest()


def count_tokens(tokenizer: Tokenizer, text: str) -> int:
    """Call the injected tokenizer; any exception or non-count result fails closed."""
    if not callable(tokenizer):
        raise ConfigError("tokenizer must be callable")
    try:
        n = tokenizer(text)
    except Exception as e:  # noqa: BLE001 - any tokenizer failure must fail closed
        raise TokenizerError(f"tokenizer raised {type(e).__name__}: {e}") from e
    if isinstance(n, bool) or not isinstance(n, int) or n < 0:
        raise TokenizerError(f"tokenizer returned a non-count: {n!r}")
    return n


# ---- exclusion policy and pool -----------------------------------------------------------------
@dataclass(frozen=True)
class ExclusionPolicy:
    """Injected pool policy. Nothing here is a Stage-1 default; values are RD decisions.

    ``protected_paths`` are exact per-task OD-5 paths (e.g. the task's test-patch files);
    ``protected_basenames`` are OD-5 config basenames; ``vendored_dir_names`` match any directory
    component. No list supplied here is claimed comprehensive for any repository population.
    """

    include_suffixes: tuple[str, ...]
    allowed_modes: frozenset[str]
    test_dir_names: frozenset[str]
    test_file_names: frozenset[str]
    test_file_prefixes: tuple[str, ...]
    test_file_suffixes: tuple[str, ...]
    vendored_dir_names: frozenset[str]
    protected_basenames: frozenset[str]
    protected_paths: frozenset[str]

    def __post_init__(self) -> None:
        _str_tuple(self.include_suffixes, "include_suffixes")
        if not self.include_suffixes:
            raise ConfigError("include_suffixes must not be empty")
        for name in ("allowed_modes", "test_dir_names", "test_file_names", "vendored_dir_names",
                     "protected_basenames", "protected_paths"):
            _str_set(getattr(self, name), name)
        if not self.allowed_modes:
            raise ConfigError("allowed_modes must not be empty")
        _str_tuple(self.test_file_prefixes, "test_file_prefixes")
        _str_tuple(self.test_file_suffixes, "test_file_suffixes")
        for p in self.protected_paths:
            _check_path(p)


def exclusion_reason(path: str, policy: ExclusionPolicy) -> str | None:
    """Reason a path is excluded, checked in a fixed order, or None if it may enter the pool."""
    parts = path.split("/")
    name, dirs = parts[-1], parts[:-1]
    if path in policy.protected_paths:
        return "protected_path"
    if (any(d in policy.test_dir_names for d in dirs) or name in policy.test_file_names
            or name.startswith(policy.test_file_prefixes)
            or name.endswith(policy.test_file_suffixes)):
        return "test"
    if any(d in policy.vendored_dir_names for d in dirs):
        return "vendored"
    if name in policy.protected_basenames:
        return "protected_basename"
    return None


@dataclass(frozen=True)
class SourceFile:
    """One synthetic base-tree entry. ``oid`` (git blob id) is verified when supplied."""

    path: str
    content: bytes
    mode: str = "100644"
    oid: str | None = None


@dataclass(frozen=True)
class PoolFile:
    path: str
    text: str


@dataclass(frozen=True)
class Pool:
    files: tuple[PoolFile, ...]
    excluded: tuple[tuple[str, str], ...]  # (path, reason), sorted by path bytes

    @property
    def paths(self) -> frozenset[str]:
        return frozenset(f.path for f in self.files)


def build_pool(tree: Iterable[SourceFile], policy: ExclusionPolicy) -> Pool:
    """Filter a base tree into the retrieval pool. Every exclusion is recorded with its reason."""
    if not isinstance(policy, ExclusionPolicy):
        raise ConfigError("policy must be an ExclusionPolicy")
    entries = list(tree)
    seen: set[str] = set()
    for f in entries:
        if not isinstance(f, SourceFile) or not isinstance(f.content, bytes):
            raise ConfigError("tree entries must be SourceFile with bytes content")
        _check_path(f.path)
        if f.path in seen:
            raise IntegrityError(f"duplicate path in tree: {f.path}")
        seen.add(f.path)
    files: list[PoolFile] = []
    excluded: list[tuple[str, str]] = []
    for f in sorted(entries, key=lambda e: e.path.encode("utf-8")):
        if f.oid is not None and git_blob_oid(f.content) != f.oid:
            raise IntegrityError(f"blob id mismatch for {f.path}")
        if f.mode not in policy.allowed_modes or not f.path.endswith(policy.include_suffixes):
            excluded.append((f.path, "not_included_type"))
            continue
        reason = exclusion_reason(f.path, policy)
        if reason:
            excluded.append((f.path, reason))
            continue
        try:
            text = f.content.decode("utf-8")
        except UnicodeDecodeError:
            excluded.append((f.path, "non_utf8"))
            continue
        files.append(PoolFile(f.path, text))
    pool = Pool(tuple(files), tuple(excluded))
    leaked = pool.paths & policy.protected_paths
    if leaked:  # defensive: unreachable by construction, kept as an explicit assertion
        raise IntegrityError(f"protected paths entered the pool: {sorted(leaked)}")
    return pool


# ---- deterministic retrieval -------------------------------------------------------------------
@dataclass(frozen=True)
class RetrievalParams:
    """Injected retrieval settings (not ratified for Stage 1)."""

    k1: float
    b: float
    top_k: int
    token_pattern: str
    lowercase: bool
    per_file_cap_tokens: int | None

    def __post_init__(self) -> None:
        if not (isinstance(self.k1, (int, float)) and not isinstance(self.k1, bool)
                and math.isfinite(self.k1) and self.k1 > 0):
            raise ConfigError("k1 must be a finite number > 0")
        if not (isinstance(self.b, (int, float)) and not isinstance(self.b, bool)
                and 0.0 <= self.b <= 1.0):
            raise ConfigError("b must be in [0, 1]")
        if isinstance(self.top_k, bool) or not isinstance(self.top_k, int) or self.top_k < 1:
            raise ConfigError("top_k must be an int >= 1")
        if not isinstance(self.token_pattern, str) or not self.token_pattern:
            raise ConfigError("token_pattern must be a non-empty regex string")
        try:
            re.compile(self.token_pattern)
        except re.error as e:
            raise ConfigError(f"token_pattern does not compile: {e}") from e
        if not isinstance(self.lowercase, bool):
            raise ConfigError("lowercase must be a bool")
        cap = self.per_file_cap_tokens
        if cap is not None and (isinstance(cap, bool) or not isinstance(cap, int) or cap < 1):
            raise ConfigError("per_file_cap_tokens must be None or an int >= 1")


def terms(text: str, params: RetrievalParams) -> list[str]:
    found = re.findall(params.token_pattern, text)
    return [t.lower() for t in found] if params.lowercase else found


def bm25_rank(query: str, pool: Pool, params: RetrievalParams) -> tuple[tuple[float, str], ...]:
    """Okapi BM25 with idf = ln(1 + (N - df + 0.5)/(df + 0.5)), distinct query terms, scores > 0
    only, ordered by score descending then path ascending bytewise (UTF-8). Deterministic."""
    q = sorted(set(terms(query, params)))
    counters = [Counter(terms(f.text, params)) for f in pool.files]
    lengths = [sum(c.values()) for c in counters]
    n = len(pool.files)
    avgdl = (sum(lengths) / n) if n else 0.0
    df = {t: sum(1 for c in counters if t in c) for t in q}
    scored: list[tuple[float, str]] = []
    for f, counts, dl in zip(pool.files, counters, lengths, strict=True):
        score = 0.0
        for t in q:
            tf = counts.get(t, 0)
            if tf == 0:
                continue
            idf = math.log(1.0 + (n - df[t] + 0.5) / (df[t] + 0.5))
            norm = 1.0 - params.b + params.b * (dl / avgdl if avgdl else 0.0)
            score += idf * tf * (params.k1 + 1.0) / (tf + params.k1 * norm)
        if score > 0.0:
            scored.append((score, f.path))
    return tuple(sorted(scored, key=lambda x: (-x[0], x[1].encode("utf-8"))))


# ---- canonical material and identity -----------------------------------------------------------
@dataclass(frozen=True)
class Material:
    """Canonical task material: repository label, issue text, retrieved files in rank order."""

    repo: str
    issue_text: str
    files: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.repo, str) or not isinstance(self.issue_text, str):
            raise ConfigError("repo and issue_text must be strings")
        if not isinstance(self.files, tuple):
            raise ConfigError("files must be a tuple of (path, content) pairs")
        seen: set[str] = set()
        for item in self.files:
            if (not isinstance(item, tuple) or len(item) != 2
                    or not all(isinstance(x, str) for x in item)):
                raise ConfigError("each file must be a (path, content) pair of strings")
            _check_path(item[0])
            if item[0] in seen:
                raise IntegrityError(f"duplicate file in material: {item[0]}")
            seen.add(item[0])


def canonical_material_text(m: Material) -> str:
    """Deterministic JSON: sorted keys, no insignificant whitespace, non-ASCII kept verbatim.
    File order is the selection (rank) order and is part of the material."""
    doc = {"schema": SCHEMA, "repo": m.repo, "issue": m.issue_text,
           "files": [{"path": p, "content": c} for p, c in m.files]}
    return json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_material_bytes(m: Material) -> bytes:
    return canonical_material_text(m).encode("utf-8")


def material_identity(m: Material) -> str:
    """SHA-256 of the canonical material bytes (== Velith task_identity(canonical text))."""
    return hashlib.sha256(canonical_material_bytes(m)).hexdigest()


@dataclass(frozen=True)
class Selection:
    material: Material
    trace: tuple[dict[str, object], ...]
    base_tokens: int


def select_material(repo: str, issue_text: str, pool: Pool, ranked: Iterable[tuple[float, str]],
                    params: RetrievalParams, material_budget: int, tokenizer: Tokenizer
                    ) -> Selection:
    """Fit rule on the canonical material text: walk the ranked list, include a file iff the
    material stays within ``material_budget``, otherwise record it as skipped; stop at top_k.
    Never truncates. Fails closed if the issue alone exceeds the budget."""
    if (isinstance(material_budget, bool) or not isinstance(material_budget, int)
            or material_budget < 1):
        raise BudgetError("material_budget must be an int >= 1")
    texts = {f.path: f.text for f in pool.files}
    base = count_tokens(tokenizer, canonical_material_text(Material(repo, issue_text, ())))
    if base > material_budget:
        raise BudgetError(f"issue material alone ({base}) exceeds material budget "
                          f"({material_budget})")
    included: list[tuple[str, str]] = []
    trace: list[dict[str, object]] = []
    for score, path in ranked:
        if len(included) == params.top_k:
            break
        if path not in texts:
            raise IntegrityError(f"ranked path not in pool: {path}")
        if params.per_file_cap_tokens is not None:
            own = count_tokens(tokenizer, texts[path])
            if own > params.per_file_cap_tokens:
                trace.append({"path": path, "score": score, "file_tokens": own,
                              "decision": "skipped_per_file_cap"})
                continue
        trial = (*included, (path, texts[path]))
        n = count_tokens(tokenizer, canonical_material_text(Material(repo, issue_text, trial)))
        fits = n <= material_budget
        trace.append({"path": path, "score": score, "material_tokens_if_included": n,
                      "decision": "included" if fits else "skipped_does_not_fit"})
        if fits:
            included = list(trial)
    return Selection(Material(repo, issue_text, tuple(included)), tuple(trace), base)


# ---- prompt rendering and prompt budget --------------------------------------------------------
@dataclass(frozen=True)
class PromptTemplate:
    """Injected template. Values are concatenated verbatim (never str.format on task text).
    ``preamble`` may contain the literal ``{repo}`` once; ``file_open``/``file_close`` may
    contain ``{path}``."""

    preamble: str
    issue_heading: str
    files_heading: str
    file_open: str
    file_close: str
    file_separator: str
    tail: str

    def __post_init__(self) -> None:
        for name in ("preamble", "issue_heading", "files_heading", "file_open", "file_close",
                     "file_separator", "tail"):
            if not isinstance(getattr(self, name), str):
                raise ConfigError(f"template field {name} must be a string")
        if self.preamble.count("{repo}") > 1:
            raise ConfigError("preamble may contain {repo} at most once")

    def template_id(self) -> str:
        fields = {k: getattr(self, k) for k in ("preamble", "issue_heading", "files_heading",
                                               "file_open", "file_close", "file_separator",
                                               "tail")}
        blob = json.dumps(fields, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RenderedPrompt:
    text: str
    spans: tuple[tuple[str, int, int], ...]  # ("metadata" | "issue" | "file:<path>", start, end)


def render_prompt(m: Material, t: PromptTemplate) -> RenderedPrompt:
    """Render material with an injected template; the material (and its identity) is unchanged."""
    if not isinstance(t, PromptTemplate):
        raise ConfigError("template must be a PromptTemplate")
    parts: list[str] = []
    spans: list[tuple[str, int, int]] = []

    def add(text: str, label: str | None = None) -> None:
        start = sum(len(p) for p in parts)
        parts.append(text)
        if label is not None:
            spans.append((label, start, start + len(text)))

    if "{repo}" in t.preamble:
        before, after = t.preamble.split("{repo}", 1)
        add(before)
        add(m.repo, "metadata")
        add(after)
    else:
        add(t.preamble)
    add(t.issue_heading)
    add(m.issue_text, "issue")
    add(t.files_heading)
    for i, (path, content) in enumerate(m.files):
        if i:
            add(t.file_separator)
        add(t.file_open.replace("{path}", path))
        add(content, f"file:{path}")
        sep = "" if content == "" or content.endswith("\n") else "\n"
        add(sep + t.file_close.replace("{path}", path))
    add(t.tail)
    return RenderedPrompt("".join(parts), tuple(spans))


@dataclass(frozen=True)
class PromptBudget:
    """Injected prompt budget: B_prompt = context_limit - output_reserve - safety_margin."""

    context_limit: int
    output_reserve: int
    safety_margin: int

    def __post_init__(self) -> None:
        for name in ("context_limit", "output_reserve", "safety_margin"):
            v = getattr(self, name)
            if isinstance(v, bool) or not isinstance(v, int) or v < 0:
                raise ConfigError(f"{name} must be an int >= 0")
        if self.prompt_budget < 1:
            raise BudgetError("prompt budget (context - reserve - margin) must be >= 1")

    @property
    def prompt_budget(self) -> int:
        return self.context_limit - self.output_reserve - self.safety_margin


def check_prompt_budget(prompt: RenderedPrompt, tokenizer: Tokenizer, budget: PromptBudget
                        ) -> int:
    """Count the rendered prompt; fail closed if it exceeds the prompt budget."""
    if not isinstance(budget, PromptBudget):
        raise ConfigError("budget must be a PromptBudget")
    n = count_tokens(tokenizer, prompt.text)
    if n > budget.prompt_budget:
        raise BudgetError(f"prompt ({n}) exceeds prompt budget ({budget.prompt_budget})")
    return n


# ---- end-to-end build --------------------------------------------------------------------------
@dataclass(frozen=True)
class BuildResult:
    pool: Pool
    ranked: tuple[tuple[float, str], ...]
    selection: Selection
    material_text: str
    identity: str
    prompt: RenderedPrompt
    prompt_tokens: int
    template_id: str


def build(*, repo: str, issue_text: str, tree: Iterable[SourceFile], policy: ExclusionPolicy,
          params: RetrievalParams, material_budget: int, template: PromptTemplate,
          budget: PromptBudget, tokenizer: Tokenizer) -> BuildResult:
    """Pool -> rank -> select (material budget) -> identity -> render -> prompt-budget check."""
    if not isinstance(params, RetrievalParams):
        raise ConfigError("params must be RetrievalParams")
    pool = build_pool(tree, policy)
    ranked = bm25_rank(issue_text, pool, params)
    selection = select_material(repo, issue_text, pool, ranked, params, material_budget,
                                tokenizer)
    prompt = render_prompt(selection.material, template)
    n = check_prompt_budget(prompt, tokenizer, budget)
    return BuildResult(pool, ranked, selection, canonical_material_text(selection.material),
                       material_identity(selection.material), prompt, n, template.template_id())


# ---- synthetic leakage audit -------------------------------------------------------------------
@dataclass(frozen=True)
class Needles:
    """Literal needles supplied by the caller (synthetic only in IC-1)."""

    gold_patch: str = ""
    test_patch: str = ""
    hidden_test_material: tuple[str, ...] = ()
    test_ids: tuple[str, ...] = ()
    hints: str = ""
    hint_window: int = 0
    identifiers: tuple[str, ...] = ()
    protected_surface: tuple[str, ...] = ()
    test_patch_paths: frozenset[str] = frozenset()
    protected_paths: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        for name in ("hidden_test_material", "test_ids", "identifiers", "protected_surface"):
            v = getattr(self, name)
            if not isinstance(v, tuple) or not all(isinstance(s, str) and s.strip() for s in v):
                raise ConfigError(f"{name} must be a tuple of non-blank strings")
        _str_set(self.test_patch_paths, "test_patch_paths")
        _str_set(self.protected_paths, "protected_paths")
        if isinstance(self.hint_window, bool) or not isinstance(self.hint_window, int):
            raise ConfigError("hint_window must be an int")
        if self.hints and self.hint_window < 1:
            raise ConfigError("hint_window must be >= 1 when hints are supplied")


def hunk_lines(patch: str) -> list[str]:
    out = set()
    for line in patch.splitlines():
        if line.startswith(("+++", "---")) or line[:1] not in ("+", "-"):
            continue
        s = line[1:].strip()
        if s:
            out.add(s)
    return sorted(out)


@dataclass(frozen=True)
class Finding:
    kind: str
    region: str
    offset: int
    excerpt: str


@dataclass(frozen=True)
class AuditReport:
    findings: tuple[Finding, ...]
    occurrences_by_kind_region: dict[str, dict[str, int]]
    issue_region_report: dict[str, object]
    path_checks: dict[str, list[str]]
    hard_failures: tuple[str, ...]  # structural only; NOT an admission decision


def audit_leakage(prompt: RenderedPrompt, needles: Needles, pool_paths: frozenset[str],
                  included_paths: frozenset[str]) -> AuditReport:
    """Attribute every needle occurrence to its region (template, metadata, issue,
    retrieved_files, or cross_boundary). Issue-region matches are reported separately and never
    exclude. Only structural failures are flagged; policy verdicts are left to the RD."""
    gaps: list[tuple[str, int, int]] = []
    last = 0
    for _label, s, e in prompt.spans:
        gaps.append(("template", last, s))
        last = e
    gaps.append(("template", last, len(prompt.text)))
    regions = [*gaps, *prompt.spans]

    def attribute(i: int, j: int) -> str:
        for label, s, e in regions:
            if s <= i and j <= e:
                return "retrieved_files" if label.startswith("file:") else label
        return "cross_boundary"

    kinds: list[tuple[str, list[str]]] = [
        ("gold_patch_full_text", [needles.gold_patch] if needles.gold_patch else []),
        ("test_patch_full_text", [needles.test_patch] if needles.test_patch else []),
        ("gold_hunk_line", hunk_lines(needles.gold_patch)),
        ("test_patch_hunk_line", hunk_lines(needles.test_patch)),
        ("hidden_test_material", list(needles.hidden_test_material)),
        ("test_id", list(needles.test_ids)),
        ("hint_window", sorted({needles.hints[i:i + needles.hint_window]
                                for i in range(len(needles.hints) - needles.hint_window + 1)})
         if needles.hints else []),
        ("identifier", list(needles.identifiers)),
        ("protected_surface", list(needles.protected_surface)),
    ]
    findings: list[Finding] = []
    table: dict[str, dict[str, int]] = {}
    for kind, items in kinds:
        counts: Counter[str] = Counter()
        for needle in items:
            i = prompt.text.find(needle)
            while i != -1:
                region = attribute(i, i + len(needle))
                counts[region] += 1
                findings.append(Finding(kind, region, i, needle[:120]))
                i = prompt.text.find(needle, i + 1)
        table[kind] = dict(sorted(counts.items()))
    findings.sort(key=lambda f: (f.offset, f.kind, f.excerpt))
    path_checks = {
        "test_patch_paths_in_pool": sorted(needles.test_patch_paths & pool_paths),
        "test_patch_paths_in_prompt": sorted(needles.test_patch_paths & included_paths),
        "protected_paths_in_pool": sorted(needles.protected_paths & pool_paths),
        "protected_paths_in_prompt": sorted(needles.protected_paths & included_paths),
    }
    hard: list[str] = []
    if table["gold_patch_full_text"]:
        hard.append("gold_patch_full_text_present")
    if table["test_patch_full_text"]:
        hard.append("test_patch_full_text_present")
    hard += sorted({f"cross_boundary:{f.kind}" for f in findings if f.region == "cross_boundary"})
    hard += [k for k, v in path_checks.items() if v]
    issue = [f for f in findings if f.region == "issue"]
    return AuditReport(
        findings=tuple(findings),
        occurrences_by_kind_region=table,
        issue_region_report={"policy": ISSUE_POLICY, "count": len(issue),
                             "by_kind": dict(sorted(Counter(f.kind for f in issue).items()))},
        path_checks=path_checks,
        hard_failures=tuple(hard),
    )
