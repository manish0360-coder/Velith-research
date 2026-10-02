#!/usr/bin/env python3
"""M2-PV-P1 pilot harness (experiment-only; research workspace; Velith main is never written).

Frozen rules implemented here (see P1_HARNESS_SPEC.md for the authority of each):
  OD-1 = M-C, OD-2 template, OD-3 limits (num_ctx 16384, num_predict 1024, M 128, B_prompt 15232,
  HF-tokenizer counting rule +1), OD-5 protected configs, OD-7 timeouts, OD-8 retry <= 1 (infra
  only), RD rulings R1-R7 of 2026-10-02 (BM25 retrieval, identity/seed, no hints, exclusion
  registry, GEN_TRUNCATED, generation inside velith-verifier:m0, one-shot generation).

Commands (WSL; run with the tokenizer venv python for `prepare`):
  prepare SLOT...    Stage P: base-tree pool -> BM25 -> OD-2 prompt -> token pre-flight -> leakage
                     audit. No model, no Ollama. Re-running compares against the stored result.
  gencheck           Runs p1_gen.py in velith-verifier:m0 with --network none, mode=check (module
                     hashes vs pinned Velith commit, seed, Task construction). No model request.
  freeze             Writes p1/PILOT_SET.json and p1/PILOT_EXCLUSION_REGISTRY.json (once).
  selfcheck          Stage X through the harness path with T3's gold patch (must equal admission).
  run SLOT           Stage G + Stage X for one slot (Milestone 2; refuses unless PILOT_SET matches).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import shlex
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Callable
from typing import Any

sys.dont_write_bytecode = True  # never write __pycache__ (Velith main, research repo)

HERE = Path(__file__).resolve().parent
P1 = HERE.parent
RESEARCH = P1.parent
EVIDENCE = P1 / "evidence"
PILOT_SET = P1 / "PILOT_SET.json"
REGISTRY = P1 / "PILOT_EXCLUSION_REGISTRY.json"
P1ENV = RESEARCH / "stage0" / "p1env"
VELITH = Path("/mnt/e/Projects/OpenSourceLab/repos/Velith")
PROBE_PATH = VELITH / "experiments" / "m2_container_prototype" / "probe.py"
PROBE_SHA256 = "560834d559fbf1063c7ad33afa675abac59535e45469bc0d9da3e8254f138e1f"
GEN_SCRIPT = HERE / "p1_gen.py"

# ---- frozen pilot parameters ------------------------------------------------------------
DATASET = "SWE-bench/SWE-bench_Verified"
MODEL = "velith-p1-deepseek-coder-v2:16b-c16384-np1024"
MODEL_DIGEST = "e196dcd918e4f54307db79c9fada1ff261c564e1df1624e20ae65d1ff0a4c45c"
NUM_CTX, NUM_PREDICT, MARGIN = 16384, 1024, 128
B_PROMPT = NUM_CTX - NUM_PREDICT - MARGIN  # 15232
GEN_TIMEOUT_S = 1800.0
MAX_GEN_ATTEMPTS = 2  # OD-8: one retry, infrastructure only, never after a timeout
MAX_X_ATTEMPTS = 2  # OD-8: one fresh-container retry on EXEC_INFRA / BASELINE_UNHEALTHY
MIN_FREE_RAM = 4 * 1024**3
OLLAMA_HOST = "http://host.docker.internal:11434"
VERIFIER_IMAGE = "velith-verifier:m0"
VELITH_MODULES = (
    "velith/agent/proposer.py",
    "velith/llm/client.py",
    "velith/task.py",
    "velith/batch/provenance.py",
)
TOKENIZER_REPO = "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct"
TOKENIZER_COMMIT = "e434a23f91ba5b4923cf6c9d9a238eb4a08e3a11"
TOKENIZER_SHA256 = "091b9dadb9845f0e8386c38bdb87e98db8adc7b0aacf36cb9257c00d0a668714"
TOKENIZERS_VERSION = "0.23.2"
BOS_TEXT = "<｜begin▁of▁sentence｜>"
COUNT_OFFSET = 1
# R1 retrieval
BM25_K1, BM25_B, TOP_K = 1.2, 0.75, 5
TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
TEST_DIRS = frozenset({"test", "tests", "testing"})
VENDORED = frozenset({"extern", "externals", "_vendor", "vendor", "vendored", "third_party",
                      "cextern", "_externals", "build", "dist"})
CONFIG_NAMES = frozenset({"setup.cfg", "pyproject.toml", "tox.ini", "pytest.ini", "conftest.py"})
HINT_WINDOW = 41  # "any hints substring longer than 40 characters"

# slot -> admitted instance, frozen spec (admission evidence), OD-7 Stage-X timeout
SLOTS: dict[str, dict[str, Any]] = {
    "T1": {"instance": "pallets__flask-5014",
           "spec": "~/velith-prototype/flask-5014.json", "timeout": 900.0},
    "T2": {"instance": "matplotlib__matplotlib-24970",
           "spec": "stage0/p1env/results/admission-T2R1R1R1R1R1/T2R1R1R1R1R1.spec.json",
           "timeout": 900.0},
    "T3": {"instance": "scikit-learn__scikit-learn-14629",
           "spec": "stage0/p1env/results/admission-T3/T3.spec.json", "timeout": 900.0},
    "T4": {"instance": "astropy__astropy-7336",
           "spec": "stage0/p1env/results/admission-T4/T4.spec.json", "timeout": 900.0},
    "T5": {"instance": "pydata__xarray-7393",
           "spec": "stage0/p1env/results/admission-T5R1/T5R1.spec.json", "timeout": 1800.0},
}
SELFCHECK_ADMISSION = P1ENV / "results" / "admission-T3" / "A" / "evidence.json"
REJECTED = (  # exposed at admission (P1 §10); evidence under stage0/p1env/results/
    ("matplotlib__matplotlib-24570", "admission-T2"),
    ("matplotlib__matplotlib-26466", "admission-T2R1"),
    ("matplotlib__matplotlib-26342", "admission-T2R1R1"),
    ("matplotlib__matplotlib-24149", "admission-T2R1R1R1"),
    ("matplotlib__matplotlib-22719", "admission-T2R1R1R1R1"),
    ("pydata__xarray-6721", "admission-T5"),
)

# OD-2 template (approved as drafted, P1_OD-2_OD-3_RETRIEVAL_SPEC_DRAFT.md §1). Placeholders
# occupy whole lines; values are concatenated verbatim (never str.format on task text).
HEAD = ("You are fixing a bug in the Python repository `{repo}` at a fixed commit.\n"
        "You cannot run code or see any files other than those shown below.\n\n## Issue\n")
MID = "\n\n## Source files (retrieved automatically from the repository; may be incomplete)\n"
TAIL = ("\n\n## Instructions\n"
        "Reply with exactly one fenced ```diff block containing a single unified diff that "
        "fixes the issue.\n"
        "Use git-style paths relative to the repository root, prefixed a/ and b/\n"
        "(for example: --- a/pkg/module.py and +++ b/pkg/module.py).\n"
        "Copy unchanged context lines exactly as they appear in the files above.\n"
        "Do not modify or add test files. Do not include any text outside the diff block.\n")
FILE_SEP = "\n\n"
MALFORMED_MARKERS = ("corrupt patch", "No valid patches in input", "patch fragment without header",
                     "unrecognized input", "malformed patch")


class HarnessError(Exception):
    pass


# ---- small utilities ----------------------------------------------------------------------
def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def dump(obj: Any) -> bytes:
    return (json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def write(path: Path, data: bytes | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data.encode("utf-8") if isinstance(data, str) else data)


def manifest(directory: Path) -> str:
    """MANIFEST.sha256 over every file under `directory` (sorted, relative paths)."""
    lines = []
    for f in sorted(p for p in directory.rglob("*") if p.is_file() and p.name != "MANIFEST.sha256"):
        lines.append(f"{sha256_bytes(f.read_bytes())}  ./{f.relative_to(directory).as_posix()}")
    data = ("\n".join(lines) + "\n").encode("utf-8")
    write(directory / "MANIFEST.sha256", data)
    return sha256_bytes(data)


def load_module(name: str, path: Path, expect_sha: str | None = None) -> Any:
    if expect_sha is not None and sha256_bytes(path.read_bytes()) != expect_sha:
        raise HarnessError(f"{path} SHA-256 differs from the pinned {expect_sha[:12]}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise HarnessError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def probe() -> Any:
    return sys.modules.get("probe") or load_module("probe", PROBE_PATH, PROBE_SHA256)


def lottery() -> Any:
    return sys.modules.get("p1_lottery") or load_module("p1_lottery", P1ENV / "p1_lottery.py")


def spec_path(slot: str) -> Path:
    raw = SLOTS[slot]["spec"]
    return Path(raw).expanduser() if raw.startswith("~") else RESEARCH / raw


def load_slot_spec(slot: str) -> tuple[dict[str, Any], str]:
    path = spec_path(slot)
    spec = probe().load_spec(probe().outside_repo(path))
    if spec["instance_id"] != SLOTS[slot]["instance"]:
        raise HarnessError(f"{slot}: spec instance {spec['instance_id']} != frozen slot")
    return spec, sha256_bytes(path.read_bytes())


# ---- Stage P: base-tree pool (R1 §3.2-3.4) -------------------------------------------------
def parse_ls_tree(raw: bytes) -> list[tuple[str, str, str, str]]:
    """`git ls-tree -r -l -z` -> [(mode, type, oid, path)]."""
    out = []
    for rec in raw.split(b"\0"):
        if not rec:
            continue
        meta, _, path = rec.partition(b"\t")
        mode, otype, oid, _size = meta.decode("ascii").split(maxsplit=3)
        out.append((mode, otype, oid, path.decode("utf-8")))
    return out


def parse_cat_file_batch(raw: bytes) -> dict[str, bytes]:
    """`git cat-file --batch` output -> {oid: content}."""
    blobs: dict[str, bytes] = {}
    pos = 0
    while pos < len(raw):
        nl = raw.index(b"\n", pos)
        header = raw[pos:nl].decode("ascii").split()
        if len(header) != 3:
            raise HarnessError(f"unexpected cat-file header {header}")
        oid, _otype, size = header[0], header[1], int(header[2])
        start = nl + 1
        blobs[oid] = raw[start:start + size]
        pos = start + size + 1
    return blobs


def git_blob_oid(content: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(content) + content).hexdigest()


def exclusion_reason(path: str) -> str | None:
    parts = path.split("/")
    name = parts[-1]
    if any(p in TEST_DIRS for p in parts[:-1]) or name == "conftest.py" or (
            name.startswith("test_") and name.endswith(".py")) or name.endswith("_test.py"):
        return "test"
    if any(p in VENDORED for p in parts[:-1]):
        return "vendored"
    if name in CONFIG_NAMES:
        return "protected_config"
    return None


def docker_run_bytes(args: list[str], stdin: bytes | None = None, timeout: float = 900.0
                     ) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["docker", *args], input=stdin, capture_output=True, timeout=timeout,
                          check=False)


def build_pool(image_ref: str, repo_dir: str, base: str) -> tuple[list[dict[str, Any]], dict]:
    """Retriever input: tracked files at `base` read from the pinned image (network none).
    Reads only the base tree; never patch / test_patch / test ids / hints (P1 §22 item 2)."""
    git = f"cd {shlex.quote(repo_dir)} && git"
    listed = docker_run_bytes(["run", "--rm", "--network", "none", "--entrypoint", "bash",
                               image_ref, "-c", f"{git} ls-tree -r -l -z {shlex.quote(base)}"])
    if listed.returncode != 0:
        raise HarnessError(f"ls-tree failed: {listed.stderr.decode(errors='replace')}")
    entries = parse_ls_tree(listed.stdout)
    stats: Counter[str] = Counter()
    wanted: list[tuple[str, str]] = []
    for mode, otype, oid, path in entries:
        stats["tracked"] += 1
        if otype != "blob" or mode not in ("100644", "100755") or not path.endswith(".py"):
            continue
        stats["py"] += 1
        reason = exclusion_reason(path)
        if reason:
            stats[f"excluded_{reason}"] += 1
            continue
        wanted.append((path, oid))
    batch = docker_run_bytes(["run", "--rm", "-i", "--network", "none", "--entrypoint", "bash",
                              image_ref, "-c", f"{git} cat-file --batch"],
                             stdin=b"".join(oid.encode() + b"\n" for _, oid in wanted))
    if batch.returncode != 0:
        raise HarnessError(f"cat-file failed: {batch.stderr.decode(errors='replace')}")
    blobs = parse_cat_file_batch(batch.stdout)
    pool, non_utf8 = [], []
    for path, oid in wanted:
        content = blobs[oid]
        if git_blob_oid(content) != oid:
            raise HarnessError(f"blob hash mismatch for {path}")
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            non_utf8.append(path)
            continue
        pool.append({"path": path, "oid": oid, "text": text})
    stats["pool"] = len(pool)
    stats["excluded_non_utf8"] = len(non_utf8)
    return pool, {"counts": dict(sorted(stats.items())), "non_utf8": non_utf8}


# ---- Stage P: BM25 (R1) -----------------------------------------------------------------------
def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


def bm25_rank(query: str, docs: list[dict[str, Any]]) -> list[tuple[float, str]]:
    """Okapi BM25 (k1 1.2, b 0.75); idf = ln(1 + (N - df + 0.5) / (df + 0.5)); distinct query
    terms; score > 0 only; order score desc, then path bytewise ascending (R1 §3.7)."""
    terms = sorted(set(tokenize(query)))
    counters = [Counter(tokenize(d["text"])) for d in docs]
    lengths = [sum(c.values()) for c in counters]
    n = len(docs)
    avgdl = (sum(lengths) / n) if n else 0.0
    df = {t: sum(1 for c in counters if t in c) for t in terms}
    scored = []
    for doc, counts, dl in zip(docs, counters, lengths, strict=True):
        score = 0.0
        for t in terms:
            tf = counts.get(t, 0)
            if tf == 0:
                continue
            idf = math.log(1.0 + (n - df[t] + 0.5) / (df[t] + 0.5))
            norm = 1.0 - BM25_B + BM25_B * (dl / avgdl if avgdl else 0.0)
            score += idf * tf * (BM25_K1 + 1.0) / (tf + BM25_K1 * norm)
        if score > 0.0:
            scored.append((score, doc["path"]))
    return sorted(scored, key=lambda x: (-x[0], x[1].encode("utf-8")))


# ---- Stage P: OD-2 rendering, token count, fit rule -------------------------------------------
def render(repo: str, problem: str, files: list[tuple[str, str]]
           ) -> tuple[str, list[tuple[str, int, int]]]:
    """OD-2 prompt plus spans of the verbatim allowed sources ("issue" | "file:<path>", s, e)."""
    parts: list[str] = [HEAD.replace("{repo}", repo)]
    spans: list[tuple[str, int, int]] = []

    def add(text: str, label: str | None = None) -> None:
        start = sum(len(p) for p in parts)
        parts.append(text)
        if label:
            spans.append((label, start, start + len(text)))

    add(problem, "issue")
    add(MID)
    for i, (path, content) in enumerate(files):
        if i:
            add(FILE_SEP)
        add(f"=== FILE: {path} ===\n")
        add(content, f"file:{path}")
        add(("" if content == "" or content.endswith("\n") else "\n") + f"=== END FILE: {path} ===")
    add(TAIL)
    return "".join(parts), spans


class TokenCounter:
    """OD-3 D-E counting rule with the pinned HF tokenizer (local file only, no network)."""

    def __init__(self, tokenizer_json: Path | None) -> None:
        import tokenizers  # tokenizer venv

        if tokenizers.__version__ != TOKENIZERS_VERSION:
            raise HarnessError(f"tokenizers {tokenizers.__version__} != {TOKENIZERS_VERSION}")
        if tokenizer_json is None:
            from huggingface_hub import hf_hub_download

            tokenizer_json = Path(hf_hub_download(TOKENIZER_REPO, "tokenizer.json",
                                                  revision=TOKENIZER_COMMIT, local_files_only=True))
        if sha256_bytes(tokenizer_json.read_bytes()) != TOKENIZER_SHA256:
            raise HarnessError("tokenizer.json SHA-256 differs from the pinned value")
        self._tok = tokenizers.Tokenizer.from_file(str(tokenizer_json))
        self.provenance = {"repo": TOKENIZER_REPO, "commit": TOKENIZER_COMMIT,
                           "tokenizer_json_sha256": TOKENIZER_SHA256,
                           "tokenizers_version": tokenizers.__version__,
                           "rendering": "messages_branch|add_special_tokens=False",
                           "offset": COUNT_OFFSET}

    def __call__(self, prompt: str) -> int:
        rendered = BOS_TEXT + "User: " + prompt + "\n\nAssistant:"
        return len(self._tok.encode(rendered, add_special_tokens=False).ids) + COUNT_OFFSET


def select_files(repo: str, problem: str, ranked: list[tuple[float, str]], texts: dict[str, str],
                 count: Callable[[str], int]) -> tuple[list[tuple[str, str]], list[dict], int]:
    """R1 fit rule: walk the ranked list; include a file iff the whole prompt stays <= B_PROMPT;
    otherwise skip it; stop at TOP_K included. Never truncates."""
    included: list[tuple[str, str]] = []
    trace: list[dict[str, Any]] = []
    base = count(render(repo, problem, [])[0])
    if base > B_PROMPT:
        return included, trace, base
    for score, path in ranked:
        if len(included) == TOP_K:
            break
        trial = [*included, (path, texts[path])]
        n = count(render(repo, problem, trial)[0])
        fits = n <= B_PROMPT
        trace.append({"path": path, "score": score, "tokens_if_included": n,
                      "decision": "included" if fits else "skipped_does_not_fit"})
        if fits:
            included = trial
    return included, trace, base


# ---- Stage P: leakage audit (P1 §22 + OD-2 extension) -----------------------------------------
def hunk_lines(patch: str) -> list[str]:
    out = []
    for line in patch.splitlines():
        if line.startswith(("+++", "---")) or line[:1] not in ("+", "-"):
            continue
        s = line[1:].strip()
        if s:
            out.append(s)
    return sorted(set(out))


def leakage_audit(prompt: str, spans: list[tuple[str, int, int]], spec: dict[str, Any],
                  row: dict[str, Any], pool_paths: set[str], included: list[str]) -> dict[str, Any]:
    """Literal §22 needles, each occurrence attributed to the region that contains it.
    Allowed verbatim sources: the fixed OD-2 template text, the dataset issue text, and base-tree
    file content (blob-hash verified). FAIL iff a whole gold/test patch text is present, a needle
    occurs outside every allowed source (incl. across a region boundary), or a test_patch path is
    in the pool / prompt."""
    template_spans, last = [], 0
    for _label, s, e in spans:
        template_spans.append(("template", last, s))
        last = e
    template_spans.append(("template", last, len(prompt)))
    regions = [*template_spans, *spans]

    def attribute(i: int, j: int) -> str:
        for label, s, e in regions:
            if s <= i and j <= e:
                return label.split(":")[0]
        return "cross_boundary"

    def scan(needles: list[str]) -> dict[str, Any]:
        by_region: Counter[str] = Counter()
        flagged: list[str] = []
        hit = 0
        for needle in needles:
            i = prompt.find(needle)
            found = False
            while i != -1:
                found = True
                region = attribute(i, i + len(needle))
                by_region[region] += 1
                if region == "cross_boundary":
                    flagged.append(needle[:120])
                i = prompt.find(needle, i + 1)
            hit += found
        return {"needles": len(needles), "needles_found": hit,
                "occurrences_by_region": dict(sorted(by_region.items())),
                "non_exempt": sorted(set(flagged))}

    hints = str(row.get("hints_text") or "")
    windows = sorted({hints[i:i + HINT_WINDOW] for i in range(len(hints) - HINT_WINDOW + 1)})
    test_paths = set(probe().patch_files(spec["test_patch"]))
    checks: dict[str, Any] = {
        "gold_patch_full_text": spec["patch"] in prompt,
        "test_patch_full_text": spec["test_patch"] in prompt,
        "test_patch_paths_in_pool": sorted(test_paths & pool_paths),
        "test_patch_paths_in_prompt": sorted(test_paths & set(included)),
        "gold_hunk_lines": scan(hunk_lines(spec["patch"])),
        "test_patch_hunk_lines": scan(hunk_lines(spec["test_patch"])),
        "test_ids": scan([*spec["fail_to_pass"], *spec["pass_to_pass"]]),
        "hints_windows_41": scan(windows),
    }
    fail = (checks["gold_patch_full_text"] or checks["test_patch_full_text"]
            or checks["test_patch_paths_in_pool"] or checks["test_patch_paths_in_prompt"]
            or any(checks[k]["non_exempt"] for k in
                   ("gold_hunk_lines", "test_patch_hunk_lines", "test_ids", "hints_windows_41")))
    return {"verdict": "FAIL" if fail else "PASS", "checks": checks,
            "hints_text_sha256": sha256_text(hints)}


# ---- Stage P command -------------------------------------------------------------------------
def prepare_slot(slot: str, count: TokenCounter, force: bool) -> dict[str, Any]:
    out_dir = EVIDENCE / slot / "P"
    if PILOT_SET.exists():
        raise HarnessError("PILOT_SET.json exists: prompts are frozen; prepare refused")
    spec, spec_sha = load_slot_spec(slot)
    lot = lottery()
    rev_before = lot.dataset_revision()
    row = probe().fetch_row(DATASET, spec["instance_id"])
    rev_after = lot.dataset_revision()
    if not (rev_before == rev_after and rev_before.startswith(lot.DESIGN_REVISION_PREFIX)):
        raise HarnessError(f"dataset revision {rev_before}/{rev_after} is not the pinned one")
    for key, field in (("base_commit", "base_commit"), ("patch", "patch"),
                       ("test_patch", "test_patch"), ("repo", "repo")):
        if str(row[field]) != spec[key]:
            raise HarnessError(f"{slot}: dataset {field} differs from the frozen spec")
    problem = str(row["problem_statement"])
    pool, pool_stats = build_pool(f"{spec['image']}@{spec['digest']}", spec["repo_dir"],
                                  spec["base_commit"])
    ranked = bm25_rank(problem, pool)
    texts = {d["path"]: d["text"] for d in pool}
    oids = {d["path"]: d["oid"] for d in pool}
    included, trace, base_tokens = select_files(spec["repo"], problem, ranked, texts, count)
    prompt, spans = render(spec["repo"], problem, included)
    predicted = count(prompt)
    paths = [p for p, _ in included]
    audit = leakage_audit(prompt, spans, spec, row, set(texts), paths)
    reasons = []
    if base_tokens > B_PROMPT:
        reasons.append("PROMPT_WITHOUT_FILES_OVER_BUDGET")
    if not included:
        reasons.append("EMPTY_RETRIEVAL")
    if predicted > B_PROMPT:
        reasons.append("OVER_BUDGET")
    if audit["verdict"] != "PASS":
        reasons.append("LEAKAGE_AUDIT_FAIL")
    identity = sha256_text(prompt)
    material = {"slot": slot, "instance_id": spec["instance_id"], "repo": spec["repo"],
                "base_commit": spec["base_commit"], "pool": pool_stats,
                "ranked_top100": [{"path": p, "score": s, "oid": oids[p]} for s, p in ranked[:100]],
                "ranked_count": len(ranked), "fit_trace": trace,
                "included": [{"path": p, "oid": oids[p], "bytes": len(c.encode("utf-8"))}
                             for p, c in included]}
    preflight = {
        "slot": slot, "instance_id": spec["instance_id"], "spec_sha256": spec_sha,
        "dataset_revision": rev_before, "problem_statement_sha256": sha256_text(problem),
        "identity": identity, "seed": derive_seed(identity), "predicted_prompt_eval_count":
        predicted, "tokens_without_files": base_tokens, "b_prompt": B_PROMPT,
        "files_included": len(included), "prompt_chars": len(prompt),
        "prompt_bytes": len(prompt.encode("utf-8")), "admissible": not reasons,
        "inadmissible_reasons": reasons, "tokenizer": count.provenance,
        "retrieval": {"algorithm": "okapi-bm25", "k1": BM25_K1, "b": BM25_B, "k": TOP_K,
                      "idf": "ln(1+(N-df+0.5)/(df+0.5))", "query_terms": "distinct",
                      "token_re": TOKEN_RE.pattern, "vendored": sorted(VENDORED)},
        "harness_sha256": sha256_bytes(Path(__file__).read_bytes()),
        "probe_sha256": PROBE_SHA256,
    }
    files = {"prompt.txt": prompt.encode("utf-8"), "material.json": dump(material),
             "leakage_audit.json": dump(audit), "preflight.json": dump(preflight)}
    if (out_dir / "preflight.json").exists() and not force:
        old = json.loads((out_dir / "preflight.json").read_text(encoding="utf-8"))
        differ = [n for n, b in files.items() if (out_dir / n).read_bytes() != b]
        print(f"{slot}: re-prepared; stored identity {old['identity'][:16]} vs new "
              f"{identity[:16]}: " + (f"DIFFERS in {differ} (not overwritten)" if differ
                                      else "IDENTICAL (all four files byte-equal)"))
        return preflight
    for name, data in files.items():
        write(out_dir / name, data)
    preflight["manifest_sha256"] = manifest(out_dir)
    return preflight


def derive_seed(identity: str) -> int:
    """Replica of velith.batch.provenance.derive_task_seed(identity, 0); p1_gen.py re-derives it
    with the frozen function inside the container and asserts equality."""
    digest = hashlib.sha256(f"{identity}:0".encode()).digest()
    return int.from_bytes(digest[:8], "big") & ((1 << 63) - 1)


# ---- Velith pins / container generation ------------------------------------------------------
def velith_pins() -> dict[str, Any]:
    def git(*args: str) -> bytes:
        res = subprocess.run(["git", "-C", str(VELITH), *args], capture_output=True, check=False)
        if res.returncode != 0:
            raise HarnessError(f"git {args}: {res.stderr.decode(errors='replace')}")
        return res.stdout

    head = git("rev-parse", "HEAD").decode().strip()
    mods = {m: sha256_bytes(git("show", f"{head}:src/{m}")) for m in VELITH_MODULES}
    return {"velith_commit": head, "module_sha256": mods}


def image_id(ref: str) -> str:
    res = subprocess.run(["docker", "image", "inspect", ref, "--format", "{{.Id}}"],
                         capture_output=True, text=True, check=False)
    if res.returncode != 0:
        raise HarnessError(f"image inspect {ref}: {res.stderr.strip()}")
    return res.stdout.strip()


def run_gen(image: str, request: dict[str, Any], *, network: bool, name: str, timeout: float
            ) -> tuple[subprocess.CompletedProcess[bytes], dict[str, Any]]:
    args = ["run", "--rm", "-i", "--name", name, "--read-only", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges"]
    args += (["--add-host", "host.docker.internal:host-gateway"] if network
             else ["--network", "none"])
    args += ["--entrypoint", "python", image, "-c", GEN_SCRIPT.read_text(encoding="utf-8")]
    try:
        proc = docker_run_bytes(args, stdin=json.dumps(request).encode("utf-8"), timeout=timeout)
        raw, fallback = proc.stdout, {"status": "NO_RESULT_LINE", "exit_code": proc.returncode}
    except subprocess.TimeoutExpired as exc:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, check=False)
        raw = exc.stdout if isinstance(exc.stdout, bytes) else b""
        proc = subprocess.CompletedProcess(args, -9, raw,
                                           exc.stderr if isinstance(exc.stderr, bytes) else b"")
        fallback = {"status": "HARNESS_TIMEOUT", "no_retry": True}
    marks: dict[str, Any] = {}
    for line in raw.decode("utf-8", errors="replace").splitlines():
        for key in ("P1GEN_SENT", "P1GEN_COMPLETION", "P1GEN_RESULT"):
            if line.startswith(key + " "):
                marks[key] = json.loads(line[len(key) + 1:])
    result = marks.get("P1GEN_RESULT") or marks.get("P1GEN_COMPLETION") or fallback
    # conservative: a harness timeout counts as a sent request (attempt consumed, no retry)
    result["request_sent"] = "P1GEN_SENT" in marks or fallback["status"] == "HARNESS_TIMEOUT"
    return proc, result


def gen_request(mode: str, prep: dict[str, Any], prompt: str, pins: dict[str, Any]) -> dict:
    return {"mode": mode, "instance_id": prep["instance_id"], "prompt": prompt,
            "identity": prep["identity"], "seed": prep["seed"], "model": MODEL,
            "model_digest": MODEL_DIGEST, "host": OLLAMA_HOST, "timeout": GEN_TIMEOUT_S,
            "expected_module_sha256": pins["module_sha256"]}


def free_ram() -> int:
    res = subprocess.run(["powershell.exe", "-NoProfile", "-Command",
                          "(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory"],
                         capture_output=True, text=True, timeout=60, check=False)
    if res.returncode != 0 or not res.stdout.strip().isdigit():
        raise HarnessError(f"cannot read Windows free RAM: {res.stderr.strip()}")
    return int(res.stdout.strip()) * 1024


def ollama_stop() -> dict[str, Any]:
    res = subprocess.run(["powershell.exe", "-NoProfile", "-Command", f"ollama stop '{MODEL}'"],
                         capture_output=True, text=True, timeout=120, check=False)
    return {"rc": res.returncode, "stdout": res.stdout.strip(), "stderr": res.stderr.strip()}


def cmd_gencheck(_: argparse.Namespace) -> int:
    prep_dir = EVIDENCE / "T3" / "P"
    prep = json.loads((prep_dir / "preflight.json").read_text(encoding="utf-8"))
    prompt = (prep_dir / "prompt.txt").read_bytes().decode("utf-8")
    pins = velith_pins()
    img = image_id(VERIFIER_IMAGE)
    proc, result = run_gen(img, gen_request("check", prep, prompt, pins), network=False,
                           name=f"p1gen-check-{int(time.time())}", timeout=600)
    out = EVIDENCE / "_gencheck"
    write(out / "raw_stdout.txt", proc.stdout)
    write(out / "raw_stderr.txt", proc.stderr)
    record: dict[str, Any] = {
        "utc": utc(), "image": VERIFIER_IMAGE, "image_id": img, "network": "none",
        "pins": pins, "result": result, "free_ram_bytes": free_ram(),
        "harness_sha256": sha256_bytes(Path(__file__).read_bytes()),
        "gen_sha256": sha256_bytes(GEN_SCRIPT.read_bytes())}
    write(out / "gencheck.json", dump(record))
    print(json.dumps({"status": result.get("status"), "image_id": img,
                      "velith_commit": pins["velith_commit"],
                      "free_ram_gib": round(record["free_ram_bytes"] / 1024**3, 2),
                      "manifest": manifest(out)[:16]}, indent=2))
    return 0 if result.get("status") == "CHECK_OK" else 1


# ---- freeze ----------------------------------------------------------------------------------
def cmd_freeze(_: argparse.Namespace) -> int:
    if PILOT_SET.exists() or REGISTRY.exists():
        raise HarnessError("PILOT_SET.json / registry already exist (frozen; never rewritten)")
    gen = json.loads((EVIDENCE / "_gencheck" / "gencheck.json").read_text(encoding="utf-8"))
    if gen["result"].get("status") != "CHECK_OK":
        raise HarnessError("gencheck is not CHECK_OK")
    harness_sha = sha256_bytes(Path(__file__).read_bytes())
    gen_sha = sha256_bytes(GEN_SCRIPT.read_bytes())
    if gen["harness_sha256"] != harness_sha or gen["gen_sha256"] != gen_sha:
        raise HarnessError("harness/p1_gen changed since gencheck; rerun gencheck")
    tasks = []
    for slot in SLOTS:
        pdir = EVIDENCE / slot / "P"
        prep = json.loads((pdir / "preflight.json").read_text(encoding="utf-8"))
        if prep["harness_sha256"] != harness_sha:
            raise HarnessError(f"{slot}: prepared with a different harness; re-prepare")
        if sha256_bytes((pdir / "prompt.txt").read_bytes()) != prep["identity"]:
            raise HarnessError(f"{slot}: prompt.txt does not match its identity")
        spec, spec_sha = load_slot_spec(slot)
        if spec_sha != prep["spec_sha256"]:
            raise HarnessError(f"{slot}: spec changed since prepare")
        tasks.append({"slot": slot, "instance_id": spec["instance_id"], "repo": spec["repo"],
                      "base_commit": spec["base_commit"], "spec": SLOTS[slot]["spec"],
                      "spec_sha256": spec_sha, "image": spec["image"], "digest": spec["digest"],
                      "platform": spec["platform"], "protected_paths": spec["protected_paths"],
                      "stage_x_timeout_s": SLOTS[slot]["timeout"],
                      "identity": prep["identity"], "seed": prep["seed"],
                      "predicted_prompt_eval_count": prep["predicted_prompt_eval_count"],
                      "files_included": prep["files_included"],
                      "admissible": prep["admissible"],
                      "inadmissible_reasons": prep["inadmissible_reasons"],
                      "material_sha256": sha256_bytes((pdir / "material.json").read_bytes()),
                      "prepare_manifest_sha256": sha256_bytes(
                          (pdir / "MANIFEST.sha256").read_bytes())})
    pilot = {
        "pilot": "M2-PV-P1", "frozen_utc": utc(), "dataset": DATASET,
        "dataset_revision": json.loads((EVIDENCE / "T3" / "P" / "preflight.json").read_text(
            encoding="utf-8"))["dataset_revision"],
        "task_order": list(SLOTS), "tasks": tasks,
        "model": {"name": MODEL, "manifest_digest": MODEL_DIGEST, "num_ctx": NUM_CTX,
                  "num_predict": NUM_PREDICT, "stop": ["\nUser:", "\nAssistant:"],
                  "temperature": 0.0, "client_timeout_s": GEN_TIMEOUT_S},
        "budget": {"b_prompt": B_PROMPT, "margin": MARGIN, "r_out": NUM_PREDICT},
        "generation_route": {"image": VERIFIER_IMAGE, "image_id": gen["image_id"],
                             "velith_commit": gen["pins"]["velith_commit"],
                             "module_sha256": gen["pins"]["module_sha256"],
                             "host": OLLAMA_HOST},
        "harness_sha256": harness_sha, "gen_sha256": gen_sha, "probe_sha256": PROBE_SHA256,
        "spec_doc_sha256": sha256_bytes((HERE / "P1_HARNESS_SPEC.md").read_bytes()),
    }
    write(PILOT_SET, dump(pilot))
    excluded = [{"instance_id": t["instance_id"], "pilot_task_identity": t["identity"],
                 "status": "admitted", "slot": t["slot"]} for t in tasks]
    excluded += [{"instance_id": iid, "pilot_task_identity": None,
                  "status": "rejected_at_admission (exposed)",
                  "evidence": f"stage0/p1env/results/{d}/"} for iid, d in REJECTED]
    registry = {"registry": "velith-pilot-exclusion", "version": 1, "dataset": DATASET,
                "dataset_revision": pilot["dataset_revision"], "pilot": "M2-PV-P1",
                "note": "audit/safety registry (P1 §10, RD R4); not a task-selection rule",
                "excluded": excluded}
    write(REGISTRY, dump(registry))
    print(json.dumps({"PILOT_SET.json": sha256_bytes(PILOT_SET.read_bytes()),
                      "PILOT_EXCLUSION_REGISTRY.json": sha256_bytes(REGISTRY.read_bytes()),
                      "admissible": {t["slot"]: t["admissible"] for t in tasks}}, indent=2))
    return 0


# ---- Stage X (probe as a library, unmodified) -------------------------------------------------
def stage_x(spec: dict[str, Any], patch: str, run_dir: Path, timeout: float, case: str
            ) -> dict[str, Any]:
    pr = probe()
    run_dir = pr.outside_repo(run_dir)
    if run_dir.exists():
        raise HarnessError(f"refusing to overwrite {run_dir}")
    run_dir.mkdir(parents=True)
    defaults = pr.build_parser().parse_args(["run", "--spec", "-", "--case", "A", "--out-dir", "-"])
    limits = {"memory": defaults.memory, "cpus": defaults.cpus, "pids": defaults.pids,
              "timeout_seconds": timeout}
    contract = pr.read_frozen_contract()
    image_ok, img_id, image_detail = pr.verify_image(spec)
    baseline = candidate = None
    if image_ok:
        shared = {"env": contract["env"], "limits": limits, "workdir": run_dir}
        baseline = pr.run_container(spec, role="baseline", candidate_patch="", tamper=False,
                                    fault_cmd=None, **shared)
        candidate = pr.run_container(spec, role="candidate", candidate_patch=patch, tamper=False,
                                     fault_cmd=None, **shared)
        classification, reason, detail = pr.classify(spec, baseline, candidate)
    else:
        classification, reason, detail = pr.INFRA_ERROR, "IMAGE_IDENTITY_MISMATCH", image_detail
    duration = float(candidate["diagnostics"].get("duration_seconds", 0.0)) if candidate else 0.0
    protected = list(spec["protected_paths"])
    evidence = {
        "note": "P1 Stage X via the frozen M2 probe library -- probe-level evidence, NOT a verdict"
                " of record",
        "deterministic": {
            "instance_id": spec["instance_id"], "repo": spec["repo"],
            "base_commit": spec["base_commit"], "image": spec["image"], "digest": spec["digest"],
            "platform": spec["platform"], "image_id": img_id, "case": case,
            "candidate_patch_sha256": pr.sha256_text(patch),
            "test_patch_sha256": pr.sha256_text(spec["test_patch"]),
            "protected_paths": protected,
            "protected_set_sha256": pr.sha256_text("\n".join(protected)),
            "test_argv": pr.test_argv(spec), "deterministic_env": contract["env"],
            "limits": limits, "velith_commit": pr._velith_commit(),
            "probe_sha256": sha256_bytes(PROBE_PATH.read_bytes()),
            "harness_sha256": sha256_bytes(Path(__file__).read_bytes()),
            "baseline": None if baseline is None else baseline["deterministic"],
            "candidate": None if candidate is None else candidate["deterministic"],
            "classification": classification, "reason": reason, "detail": detail,
        },
        "diagnostics": {"baseline": None if baseline is None else baseline["diagnostics"],
                        "candidate": None if candidate is None else candidate["diagnostics"]},
        "verdict_projection": pr.verdict_projection(contract, classification, reason, duration),
    }
    write(run_dir / "evidence.json", dump(evidence))
    return evidence


def cmd_selfcheck(_: argparse.Namespace) -> int:
    spec, spec_sha = load_slot_spec("T3")
    gold, _tamper = probe()._case_inputs(spec, "A")
    out = EVIDENCE / "T3" / "X-selfcheck-gold"
    ev = stage_x(spec, gold, out / "run", SLOTS["T3"]["timeout"], "P1-X-SELFCHECK-GOLD")
    adm = json.loads(SELFCHECK_ADMISSION.read_text(encoding="utf-8"))["deterministic"]
    det = ev["deterministic"]
    compare = {k: (det[k], adm[k]) for k in ("classification", "reason", "detail",
                                              "candidate_patch_sha256", "protected_set_sha256",
                                              "image_id")}
    outcomes_equal = (det["candidate"] or {}).get("outcomes") == adm["candidate"]["outcomes"] and \
        (det["baseline"] or {}).get("outcomes") == adm["baseline"]["outcomes"]
    ok = all(a == b for a, b in compare.values()) and outcomes_equal
    record = {"utc": utc(), "spec_sha256": spec_sha, "compare_vs_admission": compare,
              "per_test_outcomes_equal": outcomes_equal, "verdict": "PASS" if ok else "FAIL",
              "admission_evidence": str(SELFCHECK_ADMISSION.relative_to(RESEARCH))}
    write(out / "selfcheck.json", dump(record))
    print(json.dumps({"verdict": record["verdict"], "classification": det["classification"],
                      "detail": det["detail"], "outcomes_equal": outcomes_equal,
                      "manifest": manifest(out)[:16]}, indent=2))
    return 0 if ok else 1


# ---- episode classification (P1 §17 / §18 + R5) ----------------------------------------------
def touched_paths(patch: str) -> set[str]:
    paths = set(probe().patch_files(patch))
    for line in patch.splitlines():
        for prefix in ("+++ b/", "--- a/"):
            if line.startswith(prefix):
                paths.add(line[len(prefix):].strip())
    return paths


def x_code(det: dict[str, Any], cand_stdout: str, touched_protected: bool) -> str:
    cls, reason = det["classification"], det["reason"]
    if cls == "PATCH_APPLY_FAILED":
        return "MALFORMED_PATCH" if any(m in cand_stdout for m in MALFORMED_MARKERS) \
            else "PATCH_DOES_NOT_APPLY"
    if cls == "INFRA_ERROR" and reason.startswith("BASELINE_"):
        return "BASELINE_UNHEALTHY"
    if cls == "INFRA_ERROR" and reason == "RESOURCE_KILLED":
        return "RESOURCE_EXHAUSTED"
    if cls == "INFRA_ERROR":
        return "EXEC_INFRA"
    if reason == "CANDIDATE_TIMEOUT":
        return "TIMEOUT"
    if touched_protected:
        return "TEST_INTEGRITY"
    return "CANDIDATE_PASSED" if cls == "PASSED" else "CANDIDATE_FAILED"


def patch_applies(det: dict[str, Any]) -> bool | str:
    cand = det.get("candidate") or {}
    status = cand.get("status")
    if status == "PATCH_APPLY_FAILED":
        return False
    if status in ("RAN", "TEST_PATCH_FAILED", "RESTORE_FAILED") or cand.get("surface"):
        return True
    return "NA_EXEC_INFRA"


def classify_episode(gen: dict[str, Any], x: dict[str, Any] | None, cand_stdout: str,
                     protected: list[str], token_ok: bool, ctx_ok: bool) -> dict[str, Any]:
    flags = []
    if not token_ok:
        flags.append("TOKEN_COUNT_MISMATCH")
    if not ctx_ok:
        flags.append("CONTEXT_LENGTH_NOT_CONFIRMED")
    if gen.get("status") != "GENERATED":
        na = "NA_GEN_INFRA"
        return {"code": "GEN_INFRA", "flags": flags, "interpretable": False,
                "measurements": {"patch_produced": na, "patch_applies": na,
                                 "verified_outcome": na, "token_count": na, "latency": na}}
    truncated = gen["completion_tokens"] == NUM_PREDICT
    if truncated:
        flags.append("GEN_TRUNCATED")
    produced = bool(gen["has_patch"])
    m: dict[str, Any] = {"patch_produced": produced,
                         "token_count": {"prompt_tokens": gen["prompt_tokens"],
                                         "completion_tokens": gen["completion_tokens"]},
                         "latency": gen["latency_seconds"]}
    xc = None
    interpretable = True
    if not produced:
        m["patch_applies"], m["verified_outcome"] = "NA_NO_PATCH", "NO_PATCH"
    elif x is None:
        raise HarnessError("patch produced but no Stage X evidence")
    else:
        det = x["deterministic"]
        touched = bool(touched_paths(gen["patch"]) & set(protected)) or \
            bool((det.get("candidate") or {}).get("removed"))
        if touched:
            flags.append("TEST_INTEGRITY")
        xc = x_code(det, cand_stdout, touched)
        if xc == "TIMEOUT":
            flags.append("TIMEOUT_UNATTRIBUTED")
        interpretable = xc not in ("EXEC_INFRA", "BASELINE_UNHEALTHY")
        m["patch_applies"] = patch_applies(det)
        m["verified_outcome"] = {"classification": det["classification"],
                                 "reason": det["reason"], "detail": det["detail"]}
    code = "GEN_TRUNCATED" if truncated else ("NO_PATCH" if not produced else xc)
    return {"code": code, "x_code": xc, "flags": flags, "interpretable": interpretable,
            "measurements": m}


# ---- Stage G + X: one episode (Milestone 2) ---------------------------------------------------
def x_retryable(det: dict[str, Any]) -> bool:
    return det["classification"] == "INFRA_ERROR" and det["reason"] != "RESOURCE_KILLED"


def cmd_run(args: argparse.Namespace) -> int:
    slot = args.slot
    pilot = json.loads(PILOT_SET.read_text(encoding="utf-8"))
    task = next(t for t in pilot["tasks"] if t["slot"] == slot)
    if pilot["harness_sha256"] != sha256_bytes(Path(__file__).read_bytes()) or \
            pilot["gen_sha256"] != sha256_bytes(GEN_SCRIPT.read_bytes()):
        raise HarnessError("harness or p1_gen.py changed after freeze (R7): refused")
    if not task["admissible"]:
        raise HarnessError(f"{slot} is inadmissible: {task['inadmissible_reasons']}")
    pdir, gdir, root = EVIDENCE / slot / "P", EVIDENCE / slot / "G", EVIDENCE / slot
    prompt_bytes = (pdir / "prompt.txt").read_bytes()
    if sha256_bytes(prompt_bytes) != task["identity"]:
        raise HarnessError("prompt.txt does not match the frozen identity")
    prep = json.loads((pdir / "preflight.json").read_text(encoding="utf-8"))
    spec, spec_sha = load_slot_spec(slot)
    if spec_sha != task["spec_sha256"]:
        raise HarnessError("spec changed after freeze")
    route = pilot["generation_route"]
    if image_id(VERIFIER_IMAGE) != route["image_id"]:
        raise HarnessError("velith-verifier:m0 image ID changed after freeze")
    pins = {"velith_commit": route["velith_commit"], "module_sha256": route["module_sha256"]}
    request = gen_request("generate", prep, prompt_bytes.decode("utf-8"), pins)

    # --- Stage G (resumable; never regenerates once a completion exists) ---
    gen: dict[str, Any] | None = None
    attempts = sorted(gdir.glob("attempt-*/result.json"))
    for f in attempts:
        r = json.loads(f.read_text(encoding="utf-8"))
        if r.get("status") == "GENERATED":
            gen = r
    consumed = [json.loads(f.read_text(encoding="utf-8")) for f in attempts]
    while gen is None:
        if consumed and (len(consumed) >= MAX_GEN_ATTEMPTS or consumed[-1].get("no_retry")):
            gen = consumed[-1]
            break
        ram = free_ram()
        stop = ollama_stop()
        if ram < MIN_FREE_RAM:
            write(gdir / f"preflight-fail-{utc()}.json", dump({"free_ram": ram, "stop": stop}))
            raise HarnessError(f"free RAM {ram} < {MIN_FREE_RAM}: STOP (no attempt consumed)")
        n = len(consumed) + 1
        adir = gdir / f"attempt-{n}"
        started = utc()
        proc, res = run_gen(route["image_id"], request, network=True,
                            name=f"p1gen-{slot}-{n}-{int(time.time())}",
                            timeout=GEN_TIMEOUT_S + 600)
        if proc is not None:  # raw first, before any interpretation
            write(adir / "raw_stdout.txt", proc.stdout)
            write(adir / "raw_stderr.txt", proc.stderr)
        res.update({"attempt": n, "started_utc": started, "ended_utc": utc(),
                    "free_ram_before": ram, "ollama_stop_before": stop})
        if not res.get("request_sent"):
            write(gdir / f"preflight-fail-{started}.json", dump(res))
            raise HarnessError(f"pre-request failure {res.get('status')}: STOP (rerunnable)")
        if res.get("status") == "GENERATED":
            write(adir / "completion.txt", res["completion_text"].encode("utf-8"))
            write(adir / "patch.diff", res["patch"].encode("utf-8"))
            gen = res
        else:
            res["no_retry"] = bool(res.get("error_is_timeout")) or res.get("status") in (
                "HARNESS_TIMEOUT",)
        write(adir / "result.json", dump(res))
        consumed.append(res)

    # --- post-call assertions + unload (sequential execution) ---
    token_ok = ctx_ok = False
    post: dict[str, Any] = {}
    if gen.get("status") == "GENERATED":
        token_ok = gen["prompt_tokens"] == task["predicted_prompt_eval_count"]
        loaded = [m for m in (gen.get("ps_after") or {}).get("models", [])
                  if m.get("name") == MODEL or m.get("model") == MODEL]
        ctx_ok = bool(loaded) and loaded[0].get("context_length") == NUM_CTX
        post["ollama_stop_after"] = ollama_stop()
        _, ps = run_gen(route["image_id"], {**request, "mode": "ps"}, network=True,
                        name=f"p1gen-ps-{slot}-{int(time.time())}", timeout=300)
        post["ps_after_unload"] = ps
        post["free_ram_after_unload"] = free_ram()
        if any(m.get("name") == MODEL for m in (ps.get("ps") or {}).get("models", [])):
            write(gdir / "post_unload.json", dump(post))
            raise HarnessError("model still loaded after ollama stop: STOP before Stage X "
                               "(resumable)")
    write(gdir / "post_unload.json", dump(post))

    # --- Stage X (resumable; one retry on infrastructure only) ---
    x = None
    cand_stdout = ""
    if gen.get("status") == "GENERATED" and gen["has_patch"]:
        for n in range(1, MAX_X_ATTEMPTS + 1):
            xdir = root / f"X-{n}"
            evf = xdir / "evidence.json"
            x = json.loads(evf.read_text(encoding="utf-8")) if evf.exists() else stage_x(
                spec, gen["patch"], xdir, task["stage_x_timeout_s"], "P1-X")
            cs = xdir / "candidate" / "stdout.txt"
            cand_stdout = cs.read_text(encoding="utf-8") if cs.exists() else ""
            if not x_retryable(x["deterministic"]):
                break
    episode = classify_episode(gen, x, cand_stdout, task["protected_paths"], token_ok, ctx_ok)
    episode.update({"slot": slot, "instance_id": task["instance_id"], "identity": task["identity"],
                    "seed": task["seed"], "predicted_prompt_eval_count":
                    task["predicted_prompt_eval_count"], "token_count_assertion": token_ok,
                    "context_length_assertion": ctx_ok, "gen_attempts": len(consumed) or 1,
                    "pilot_set_sha256": sha256_bytes(PILOT_SET.read_bytes()),
                    "patch_sha256": sha256_text(gen["patch"]) if gen.get("patch") is not None
                    else None, "utc": utc()})
    write(root / "episode.json", dump(episode))
    print(json.dumps({k: episode[k] for k in ("code", "flags", "measurements")}, indent=2))
    print("manifest", manifest(root)[:16])
    return 0


# ---- read-only Milestone-1 report -------------------------------------------------------------
def cmd_report(_: argparse.Namespace) -> int:
    def load(p: Path) -> Any:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    ok = True
    for slot in SLOTS:
        pdir = EVIDENCE / slot / "P"
        prep, audit, mat = (load(pdir / n) for n in
                            ("preflight.json", "leakage_audit.json", "material.json"))
        if prep is None:
            print(f"{slot}: NOT PREPARED")
            ok = False
            continue
        fits = prep["predicted_prompt_eval_count"] <= B_PROMPT
        ident_ok = sha256_bytes((pdir / "prompt.txt").read_bytes()) == prep["identity"]
        ok &= fits and ident_ok and prep["admissible"] and audit["verdict"] == "PASS"
        print(f"{slot} {prep['instance_id']}: tokens {prep['predicted_prompt_eval_count']}/"
              f"{B_PROMPT} (without files {prep['tokens_without_files']}) files "
              f"{prep['files_included']} chars {prep['prompt_chars']} admissible "
              f"{prep['admissible']} {prep['inadmissible_reasons']} audit {audit['verdict']} "
              f"identity {prep['identity'][:16]} prompt_sha_ok {ident_ok}")
        print(f"   pool {mat['pool']['counts']} ranked {mat['ranked_count']} "
              f"included {[f['path'] for f in mat['included']]}")
        c = audit["checks"]
        print(f"   full_gold {c['gold_patch_full_text']} full_test {c['test_patch_full_text']} "
              f"test_paths_in_pool {c['test_patch_paths_in_pool']} "
              f"in_prompt {c['test_patch_paths_in_prompt']}")
        for k in ("gold_hunk_lines", "test_patch_hunk_lines", "test_ids", "hints_windows_41"):
            print(f"   {k}: found {c[k]['needles_found']}/{c[k]['needles']} "
                  f"by_region {c[k]['occurrences_by_region']} non_exempt {c[k]['non_exempt']}")
    gen = load(EVIDENCE / "_gencheck" / "gencheck.json")
    if gen:
        r = gen["result"]
        same = r.get("module_sha256") == gen["pins"]["module_sha256"]
        ok &= r.get("status") == "CHECK_OK" and same
        print(f"gencheck: {r.get('status')} image {gen['image_id']} velith "
              f"{gen['pins']['velith_commit'][:12]} modules_match {same} "
              f"python {r.get('python')} free_ram_gib {round(gen['free_ram_bytes'] / 1024**3, 2)}")
    else:
        print("gencheck: NOT RUN")
        ok = False
    sc = load(EVIDENCE / "T3" / "X-selfcheck-gold" / "selfcheck.json")
    print("selfcheck:", json.dumps(sc and {"verdict": sc["verdict"],
                                           "compare": sc["compare_vs_admission"],
                                           "outcomes_equal": sc["per_test_outcomes_equal"]}))
    ok &= bool(sc) and sc["verdict"] == "PASS"
    for f in (PILOT_SET, REGISTRY):
        print(f"{f.name}: {sha256_bytes(f.read_bytes()) if f.exists() else 'NOT WRITTEN'}")
        ok &= f.exists()
    print("MILESTONE-1 CHECKS:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# ---- CLI --------------------------------------------------------------------------------------
def cmd_prepare(args: argparse.Namespace) -> int:
    count = TokenCounter(Path(args.tokenizer_json) if args.tokenizer_json else None)
    rc = 0
    for slot in args.slots:
        p = prepare_slot(slot, count, args.force)
        print(json.dumps({k: p[k] for k in ("slot", "instance_id", "predicted_prompt_eval_count",
                                            "tokens_without_files", "files_included",
                                            "prompt_chars", "admissible", "inadmissible_reasons",
                                            "identity")}))
        rc |= 0 if p["admissible"] else 1
    return rc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("slots", nargs="+", choices=list(SLOTS))
    p.add_argument("--tokenizer-json")
    p.add_argument("--force", action="store_true", help="overwrite (only before freeze)")
    p.set_defaults(fn=cmd_prepare)
    sub.add_parser("gencheck").set_defaults(fn=cmd_gencheck)
    sub.add_parser("freeze").set_defaults(fn=cmd_freeze)
    sub.add_parser("selfcheck").set_defaults(fn=cmd_selfcheck)
    sub.add_parser("report").set_defaults(fn=cmd_report)
    r = sub.add_parser("run")
    r.add_argument("slot", choices=list(SLOTS))
    r.set_defaults(fn=cmd_run)
    args = ap.parse_args(argv)
    try:
        return int(args.fn(args))
    except HarnessError as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
