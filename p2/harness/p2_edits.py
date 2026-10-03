"""P2 structured-edit parser and resolver (P2_SPEC.md §6; D2, G-6). Pure functions, no I/O.

Implements exactly the frozen grammar and semantics:
- region selection mirroring Velith `_extract_patch`: the first fenced block, or the whole
  completion; drop a first line equal to diff/patch/udiff/python (case-insensitive, stripped);
  strip leading and trailing whitespace;
- blocks `<<<<<<< SEARCH <PATH>` / `=======` / `>>>>>>> REPLACE`, with lines split on "\\n" only;
- exact byte matching against the ORIGINAL base content at line-boundary starts:
  0 -> S_SEARCH_NOT_FOUND, 1 -> resolved, >1 -> S_SEARCH_AMBIGUOUS;
- non-overlapping spans per file (else S_OVERLAP); all replacements applied at once;
- no content change -> S_EMPTY_EDIT.

There is no fuzzy matching, normalization, occurrence selection or repair of any kind.

Reading of the grammar used here (forced by the frozen productions; not a new rule):
- inside a block, every line up to the first SEP_LINE is a search line;
- every line up to the first REPLACE_LINE is a replacement line;
- between blocks only empty lines ("") are allowed.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

FENCE = "```"
LANGUAGE_TAGS = frozenset({"diff", "patch", "udiff", "python"})
SEARCH_PREFIX = "<<<<<<< SEARCH "
SEP_LINE = "======="
REPLACE_LINE = ">>>>>>> REPLACE"
REGULAR_MODES = frozenset({"100644", "100755"})

OK = "OK"
NO_OUTPUT = "NO_OUTPUT"
S_MALFORMED_BLOCK = "S_MALFORMED_BLOCK"
S_PATH_INVALID = "S_PATH_INVALID"
S_SEARCH_NOT_FOUND = "S_SEARCH_NOT_FOUND"
S_SEARCH_AMBIGUOUS = "S_SEARCH_AMBIGUOUS"
S_OVERLAP = "S_OVERLAP"
S_EMPTY_EDIT = "S_EMPTY_EDIT"
RESOLVED = "RESOLVED"


@dataclass(frozen=True)
class Block:
    index: int
    path: str
    search: bytes
    replace: bytes


@dataclass(frozen=True)
class ParseResult:
    code: str  # OK | NO_OUTPUT | S_MALFORMED_BLOCK
    region: str
    blocks: tuple[Block, ...]
    error: str = ""


@dataclass(frozen=True)
class BaseFile:
    mode: str  # git tree mode at base_commit
    content: bytes


@dataclass
class Resolution:
    code: str  # OK | S_PATH_INVALID | S_SEARCH_NOT_FOUND | S_SEARCH_AMBIGUOUS | S_OVERLAP | ...
    statuses: list[dict[str, object]] = field(default_factory=list)
    edited: dict[str, BaseFile] = field(default_factory=dict)  # changed files only


def select_region(completion: str) -> str:
    """Frozen region rule (mirrors `_extract_patch` fence handling, lines split on '\\n')."""
    text = completion
    if FENCE in completion:
        start = completion.find(FENCE) + len(FENCE)
        end = completion.find(FENCE, start)
        if end != -1:
            lines = completion[start:end].split("\n")
            if lines and lines[0].strip().lower() in LANGUAGE_TAGS:
                lines = lines[1:]
            text = "\n".join(lines)
    return text.strip()


def _path_ok(path: str) -> bool:
    if not path or any(ch.isspace() for ch in path):
        return False
    if path.startswith(("/", "a/", "b/")):
        return False
    return ".." not in path.split("/")


def parse(completion: str) -> ParseResult:
    region = select_region(completion)
    if region == "":
        return ParseResult(NO_OUTPUT, region, ())
    lines = region.split("\n")
    blocks: list[Block] = []
    i = 0

    def bad(msg: str) -> ParseResult:
        return ParseResult(S_MALFORMED_BLOCK, region, tuple(blocks), f"line {i + 1}: {msg}")

    while i < len(lines):
        line = lines[i]
        if line == "":
            i += 1
            continue
        if not line.startswith(SEARCH_PREFIX):
            return bad("expected SEARCH line")
        path = line[len(SEARCH_PREFIX):]
        if not _path_ok(path):
            return bad("invalid PATH")
        i += 1
        search: list[str] = []
        while i < len(lines) and lines[i] != SEP_LINE:
            search.append(lines[i])
            i += 1
        if i == len(lines):
            return bad("missing ======= line")
        if not search:
            return bad("empty SEARCH")
        i += 1
        replace: list[str] = []
        while i < len(lines) and lines[i] != REPLACE_LINE:
            replace.append(lines[i])
            i += 1
        if i == len(lines):
            return bad("missing >>>>>>> REPLACE line")
        i += 1
        blocks.append(Block(len(blocks), path,
                            "".join(s + "\n" for s in search).encode("utf-8"),
                            "".join(r + "\n" for r in replace).encode("utf-8")))
    return ParseResult(OK, region, tuple(blocks))


def line_starts(content: bytes) -> list[int]:
    starts = [0] if content else []
    pos = content.find(b"\n")
    while pos != -1:
        if pos + 1 < len(content):
            starts.append(pos + 1)
        pos = content.find(b"\n", pos + 1)
    return starts


def match_positions(content: bytes, search: bytes) -> list[int]:
    """Exact byte occurrences of `search` that start at a line boundary (overlaps included)."""
    return [s for s in line_starts(content) if content.startswith(search, s)]


def resolve(blocks: tuple[Block, ...], base: Mapping[str, BaseFile]) -> Resolution:
    """Resolve every block against the ORIGINAL base content, then apply all at once."""
    statuses: list[dict[str, object]] = []
    spans: dict[str, list[tuple[int, int, int]]] = {}
    for b in blocks:
        st: dict[str, object] = {"index": b.index, "path": b.path}
        f = base.get(b.path)
        if f is None or f.mode not in REGULAR_MODES:
            st["status"] = S_PATH_INVALID
        else:
            pos = match_positions(f.content, b.search)
            st["matches"] = len(pos)
            if len(pos) == 0:
                st["status"] = S_SEARCH_NOT_FOUND
            elif len(pos) > 1:
                st["status"] = S_SEARCH_AMBIGUOUS
            else:
                st["status"] = RESOLVED
                st["span"] = [pos[0], pos[0] + len(b.search)]
                spans.setdefault(b.path, []).append((pos[0], pos[0] + len(b.search), b.index))
        statuses.append(st)
    overlapping: set[int] = set()
    for file_spans in spans.values():
        ordered = sorted(file_spans)
        for (_s1, e1, i1), (s2, _e2, i2) in zip(ordered, ordered[1:], strict=False):
            if s2 < e1:
                overlapping.update((i1, i2))
    for st in statuses:
        if st["index"] in overlapping:
            st["status"] = S_OVERLAP
    first_fail = next((st["status"] for st in statuses if st["status"] != RESOLVED), None)
    if first_fail is not None:
        return Resolution(str(first_fail), statuses)
    edited: dict[str, BaseFile] = {}
    for path, file_spans in sorted(spans.items()):
        original = base[path].content
        out, cursor = [], 0
        for start, end, idx in sorted(file_spans):
            out.append(original[cursor:start])
            out.append(blocks[idx].replace)
            cursor = end
        out.append(original[cursor:])
        new = b"".join(out)
        if new != original:
            edited[path] = BaseFile(base[path].mode, new)
    if not edited:
        return Resolution(S_EMPTY_EDIT, statuses)
    return Resolution(OK, statuses, edited)


def parse_and_resolve(completion: str, base: Mapping[str, BaseFile]
                      ) -> tuple[ParseResult, Resolution]:
    parsed = parse(completion)
    if parsed.code != OK:
        return parsed, Resolution(parsed.code)
    return parsed, resolve(parsed.blocks, base)
