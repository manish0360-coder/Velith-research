"""P2 harness core (FG-2): synthetic-testable components of the frozen P2 specification.

Scope (P2_SPEC.md §4–§8, §13; FG-2):
- prompt construction: COMMON + CONTRACT_arm (Amendment A);
- shared seed (G-6);
- diff synthesis inside the pinned task image (G-7);
- the single Stage-X gate adapter shared by both arms (Amendment D);
- the endpoints U_APPLIES, S_APPLIES and VERIFIED_PASS (§7, G-3);
- the diagnostic, non-gating gold-derived self-check (G-10, A-1);
- the admission decision (§9 steps 1–5 only);
- sign-test arithmetic and the pre-declared conclusions (§8).

Not in FG-2: no lottery, no image pull or admission, no model call. P1 code is imported
read-only and pinned by SHA-256. Neither P1 nor the P2 specification is modified.
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import re
import shlex
import subprocess
import sys
import tarfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from math import comb
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import p2_edits as E  # noqa: E402

RESEARCH = HERE.parents[1]
SPEC = RESEARCH / "p2" / "P2_SPEC.md"
SPEC_SHA256 = "b2d29c5cdfba65b24c514763412c0807704c88f52d39e663f3fc6cc7a6d21c32"
P1_HARNESS = RESEARCH / "p1" / "harness" / "p1_harness.py"
P1_HARNESS_SHA256 = "c4ad73e3bdad1ebc0f2054c9f55bc89f24d2d1ac959a01c99a4a3f77aa28e963"
INSTR_HEADING = "\n\n## Instructions\n"
CONTRACT_S = (
    "Reply with one or more edit blocks that fix the issue, and nothing else, in exactly this "
    "form:\n"
    "<<<<<<< SEARCH path/relative/to/repository/root.py\n"
    "exact existing lines, copied character for character from the file above\n"
    "=======\n"
    "replacement lines\n"
    ">>>>>>> REPLACE\n"
    "Each SEARCH section must match exactly one place in the file. Do not modify or add test "
    "files.\n"
)
_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
ALPHA = Fraction(5, 100)
N_MIN = 10
INFRA_STOP = 3


class HarnessStop(Exception):
    """A harness-integrity condition (§17): stop and report; never a task outcome."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check_spec() -> None:
    if sha256_bytes(SPEC.read_bytes()) != SPEC_SHA256:
        raise HarnessStop("P2_SPEC.md differs from the FG-0 frozen specification")


def p1() -> Any:
    """The frozen P1 harness, imported read-only and pinned by SHA-256 (D9)."""
    if "p1_harness" in sys.modules:
        return sys.modules["p1_harness"]
    if sha256_bytes(P1_HARNESS.read_bytes()) != P1_HARNESS_SHA256:
        raise HarnessStop("p1/harness/p1_harness.py differs from its frozen SHA-256")
    spec = importlib.util.spec_from_file_location("p1_harness", P1_HARNESS)
    if spec is None or spec.loader is None:
        raise HarnessStop("cannot import the P1 harness")
    module = importlib.util.module_from_spec(spec)
    sys.modules["p1_harness"] = module
    spec.loader.exec_module(module)
    return module


# ---- prompts (Amendment A) and seed (G-6) -----------------------------------------------------
def contract_u() -> str:
    tail = p1().TAIL
    if not tail.startswith(INSTR_HEADING):
        raise HarnessStop("P1 OD-2 tail does not start with the instructions heading")
    return str(tail[len(INSTR_HEADING):])


@dataclass(frozen=True)
class Prompts:
    common: str
    prompt_u: str
    prompt_s: str
    common_identity: str
    identity_u: str
    identity_s: str
    seed: int


def build_prompts(repo: str, problem: str, files: list[tuple[str, str]]) -> Prompts:
    """COMMON is the P1 OD-2 rendering up to and including the instructions heading."""
    full, _spans = p1().render(repo, problem, files)
    if not full.endswith(p1().TAIL):
        raise HarnessStop("P1 render did not end with the OD-2 tail")
    common = full[: -len(p1().TAIL)] + INSTR_HEADING
    pu, ps = common + contract_u(), common + CONTRACT_S
    cid = sha256_bytes(common.encode("utf-8"))
    return Prompts(common, pu, ps, cid, sha256_bytes(pu.encode("utf-8")),
                   sha256_bytes(ps.encode("utf-8")), int(p1().derive_seed(cid)))


# ---- diff synthesis inside the pinned task image (G-7) ----------------------------------------
Runner = Callable[[str, str, bytes], "subprocess.CompletedProcess[bytes]"]


def docker_runner(image_ref: str, script: str, stdin: bytes) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["docker", "run", "--rm", "-i", "--network", "none", "--entrypoint",
                           "bash", image_ref, "-c", script], input=stdin, capture_output=True,
                          timeout=600, check=False)


def edited_tar(edited: Mapping[str, E.BaseFile]) -> bytes:
    """Deterministic tar of the edited files: sorted, mtime 0, uid/gid 0, base git mode."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        for path in sorted(edited):
            f = edited[path]
            info = tarfile.TarInfo(path)
            info.size, info.mtime, info.uid, info.gid = len(f.content), 0, 0, 0
            info.uname = info.gname = ""
            info.mode = 0o755 if f.mode == "100755" else 0o644
            tar.addfile(info, io.BytesIO(f.content))
    return buf.getvalue()


def synthesis_script(repo_dir: str, paths: list[str]) -> str:
    quoted = " ".join(shlex.quote(p) for p in sorted(paths))
    return (f"cd {shlex.quote(repo_dir)} && tar -x --no-same-owner -f - && "
            f"git -c core.quotepath=false diff --no-color --no-ext-diff -- {quoted}")


def synthesize_diff(image_ref: str, repo_dir: str, edited: Mapping[str, E.BaseFile],
                    runner: Runner = docker_runner) -> str:
    """Write the edited contents over the working tree in a fresh network-none container and
    return `git diff` byte-for-byte (decoded as UTF-8, as the probe writes it back)."""
    if not edited:
        raise HarnessStop("synthesis called without edits (S_EMPTY_EDIT must not reach here)")
    proc = runner(image_ref, synthesis_script(repo_dir, list(edited)), edited_tar(edited))
    if proc.returncode != 0:
        raise HarnessStop(f"diff synthesis failed: {proc.stderr.decode(errors='replace')}")
    diff = proc.stdout.decode("utf-8")
    if not diff:
        raise HarnessStop("diff synthesis produced no diff for a changed file (integrity)")
    return diff


# ---- the single Stage-X gate (Amendment D) ----------------------------------------------------
def stage_x_gate(spec: dict[str, Any], patch: str, run_dir: Path, timeout: float, arm: str
                 ) -> dict[str, Any]:
    """The same unmodified Stage-X path for both arms: P1 `stage_x` (frozen probe library)."""
    if arm not in ("U", "S"):
        raise HarnessStop(f"unknown arm {arm!r} (exactly two arms, D10)")
    return dict(p1().stage_x(spec, patch, run_dir, timeout, f"P2-X-{arm}"))


def gate_pass(x_evidence: dict[str, Any]) -> bool | str:
    """Frozen P1 `patch_applies` rule on the candidate container (G-3: baseline not consulted)."""
    return p1().patch_applies(x_evidence["deterministic"])  # type: ignore[no-any-return]


# ---- endpoints (§7) ---------------------------------------------------------------------------
NA = "NA"


def _gate(x: dict[str, Any] | None) -> bool | str:
    if x is None:
        raise HarnessStop("gate result missing for an arm that reached the gate")
    g = gate_pass(x)
    return g if isinstance(g, bool) else NA


def u_applies(gen_ok: bool, has_patch: bool, x: dict[str, Any] | None, aborted: bool = False
              ) -> bool | str:
    if aborted or not gen_ok:
        return NA
    if not has_patch:
        return False
    return _gate(x)


def s_applies(gen_ok: bool, resolution: E.Resolution | None, x: dict[str, Any] | None,
              aborted: bool = False) -> bool | str:
    if aborted or not gen_ok:
        return NA
    if resolution is None or resolution.code != E.OK:
        return False  # NO_OUTPUT, S_* resolution codes, S_EMPTY_EDIT
    return _gate(x)


def verified_pass(primary: bool | str, x: dict[str, Any] | None) -> bool | str:
    """Secondary only: classification PASSED. Never alters the primary endpoint."""
    if primary == NA:
        return NA
    if primary is False or x is None:
        return False
    return x["deterministic"]["classification"] == "PASSED"


# ---- gold-derived S self-check (G-10: DIAGNOSTIC ONLY; A-1) -----------------------------------
def gold_to_blocks(gold_patch: str) -> tuple[str, bool]:
    """Exact S blocks from the gold hunks (SEARCH = old side, REPLACE = new side).
    Returns (block text, saw_no_newline_marker)."""
    out: list[str] = []
    path, marker = "", False
    lines = gold_patch.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("+++ "):
            path = line[len("+++ b/"):] if line.startswith("+++ b/") else line[4:]
            i += 1
            continue
        hunk = _HUNK.match(line)
        if not hunk:
            i += 1
            continue
        old_left = int(hunk.group(2) or "1")
        new_left = int(hunk.group(4) or "1")
        old: list[str] = []
        new: list[str] = []
        i += 1
        while i < len(lines) and (old_left > 0 or new_left > 0 or lines[i].startswith("\\")):
            body = lines[i]
            if body.startswith("\\"):
                marker = True
            elif body.startswith("-"):
                old.append(body[1:])
                old_left -= 1
            elif body.startswith("+"):
                new.append(body[1:])
                new_left -= 1
            else:  # context line (" " prefix; an empty line is an empty context line)
                old.append(body[1:])
                new.append(body[1:])
                old_left -= 1
                new_left -= 1
            i += 1
        out.extend([E.SEARCH_PREFIX + path, *old, E.SEP_LINE, *new, E.REPLACE_LINE, ""])
    return "\n".join(out), marker


def self_check(gold_patch: str, base: Mapping[str, E.BaseFile],
               synthesize: Callable[[Mapping[str, E.BaseFile]], str],
               gate: Callable[[str], dict[str, Any]]) -> dict[str, Any]:
    """Diagnostic record only. It never decides admission, eligibility, order, substitution,
    arm assignment, endpoints or the population (G-10)."""
    text, marker = gold_to_blocks(gold_patch)
    parsed, res = E.parse_and_resolve(text, base)
    record: dict[str, Any] = {"diagnostic_only": True, "no_newline_marker": marker,
                              "parse_code": parsed.code, "resolution_code": res.code,
                              "block_statuses": res.statuses, "synthesized_diff_sha256": None,
                              "gate": None, "harness_integrity_alarm": False}
    if res.code == E.OK:
        diff = synthesize(res.edited)
        record["synthesized_diff_sha256"] = sha256_bytes(diff.encode("utf-8"))
        g = gate_pass(gate(diff))
        record["gate"] = g
        record["harness_integrity_alarm"] = g is False  # A-1: halt for RD review; no task effect
    return record


# ---- admission decision (§9 steps 1–5; the self-check is not an input) ------------------------
ADMISSION_STEPS = ("identity", "spec_built", "case_a_passed", "h_base_equals_worktree",
                   "f_budget_and_audit")


def admission_decision(steps: Mapping[str, bool]) -> bool:
    if set(steps) != set(ADMISSION_STEPS):
        raise HarnessStop(f"admission takes exactly steps {ADMISSION_STEPS}; got {sorted(steps)}")
    return all(steps[k] for k in ADMISSION_STEPS)


def phase_a_record(steps: Mapping[str, bool], self_check_record: dict[str, Any] | None
                   ) -> dict[str, Any]:
    return {"admitted": admission_decision(steps), "steps": dict(steps),
            "self_check_diagnostic": self_check_record}


# ---- statistics (§8) --------------------------------------------------------------------------
def sign_test_p(s_only: int, u_only: int) -> Fraction | None:
    """Exact one-sided P(X >= S-only), X ~ Binomial(m, 1/2); None if m == 0."""
    m = s_only + u_only
    if m == 0:
        return None
    return Fraction(sum(comb(m, k) for k in range(s_only, m + 1)), 2**m)


def paired_table(pairs: Sequence[tuple[bool | str, bool | str]]) -> dict[str, int]:
    valid = [(u, s) for u, s in pairs if u != NA and s != NA]
    t = {"both": sum(1 for u, s in valid if u and s),
         "s_only": sum(1 for u, s in valid if s and not u),
         "u_only": sum(1 for u, s in valid if u and not s),
         "neither": sum(1 for u, s in valid if not u and not s)}
    t["n_v"], t["discordant"] = len(valid), t["s_only"] + t["u_only"]
    t["k_s"], t["k_u"] = t["both"] + t["s_only"], t["both"] + t["u_only"]
    return t


def conclusion(table: Mapping[str, int], infra_failures: int) -> str:
    if table["n_v"] < N_MIN or infra_failures >= INFRA_STOP:
        return "P2-D"
    if table["both"] == table["s_only"] == table["u_only"] == 0:
        return "P2-C"
    p = sign_test_p(table["s_only"], table["u_only"])
    if table["s_only"] > table["u_only"] and p is not None and p < ALPHA:
        return "P2-A"
    return "P2-B"
