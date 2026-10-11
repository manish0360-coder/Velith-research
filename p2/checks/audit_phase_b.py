"""Read-only audit of P2 Phase B against P2_SPEC.md and the raw evidence.

Run (from the Velith-research root; no Docker, no model, no network, writes nothing):
    python3 -B p2/checks/audit_phase_b.py

Checks:
  A. frozen inputs: PILOT_SET / registry / code / spec SHA-256 equal the frozen values;
  B. per slot: episode present, bound to the PILOT_SET SHA, MANIFEST.sha256 complete and correct,
     one generation per arm, token counts and context confirmed, image removed, no stop record;
  C. endpoints re-derived from raw evidence (completion text, S parse, resolution, gate status)
     and compared with episode.json;
  D. independent local replay against the gold files embedded verbatim in the prompt
     (git apply --check for U; parse + exact resolution + git diff synthesis for S);
  E. paired table, exact one-sided sign test and the §8 conclusion recomputed from scratch;
  F. failure-mode tabulation.
Exit 0 iff A-E have no defect.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from collections import Counter
from fractions import Fraction
from math import comb
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
P2 = ROOT / "p2"
EV = P2 / "evidence"
sys.path.insert(0, str(P2 / "harness"))
import p2_edits as E  # noqa: E402

PILOT_SHA = "44b884125f37ce296dcc59d0fdc29038f15ecece13cc9a393ecbfe2673213305"
REGISTRY_SHA = "7befdc0b025d60049ac4b8fca51ad637199e1037ce0c9b2e5a1a990d33ad687f"
APPLIED = ("RAN", "TEST_PATCH_FAILED", "RESTORE_FAILED")
defects: list[str] = []


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def check(cond: bool, msg: str) -> None:
    if not cond:
        defects.append(msg)


def gate(x: dict[str, Any]) -> bool | str:
    """Frozen P1 patch_applies rule (§7)."""
    c = x["deterministic"].get("candidate") or {}
    if c.get("status") == "PATCH_APPLY_FAILED":
        return False
    if c.get("status") in APPLIED or c.get("surface"):
        return True
    return "NA"


def last_x(d: Path, arm: str) -> dict[str, Any] | None:
    xs = sorted(d.glob(f"X-{arm}-*/evidence.json"))
    return load(xs[-1]) if xs else None


def gold_files(common: str, paths: list[str]) -> dict[str, bytes]:
    out = {}
    for p in paths:
        head, end = f"=== FILE: {p} ===\n", f"=== END FILE: {p} ==="
        i = common.index(head) + len(head)
        out[p] = common[i:common.index(end, i)].encode("utf-8")
    return out


def git(repo: Path, *args: str, stdin: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", "-C", str(repo), "-c", "core.quotepath=false", *args],
                          input=stdin, capture_output=True, check=False)


def local_repo(tmp: Path, files: dict[str, bytes]) -> Path:
    repo = tmp / "r"
    repo.mkdir()
    git(repo, "init", "-q")
    for p, c in files.items():
        (repo / p).parent.mkdir(parents=True, exist_ok=True)
        (repo / p).write_bytes(c)
    git(repo, "add", "-A")
    git(repo, "-c", "user.email=a@b", "-c", "user.name=a", "commit", "-qm", "base")
    return repo


def normalize(diff: bytes) -> bytes:
    """Drop `index` lines (object-id abbreviation length depends on repository size) and mode
    lines (reported separately); every other byte must be identical."""
    keep = [ln for ln in diff.split(b"\n")
            if not ln.startswith((b"index ", b"old mode ", b"new mode "))]
    return b"\n".join(keep)


def manifest_ok(d: Path) -> tuple[bool, int]:
    listed = {}
    for line in (d / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        h, rel = line.split("  ", 1)
        listed[rel[2:]] = h
    actual = {f.relative_to(d).as_posix() for f in d.rglob("*")
              if f.is_file() and f.name != "MANIFEST.sha256"}
    ok = set(listed) == actual and all(sha((d / r).read_bytes()) == h for r, h in listed.items())
    return ok, len(listed)


def main() -> int:
    # ---- A. frozen inputs ----
    pilot_raw = (P2 / "PILOT_SET.json").read_bytes()
    check(sha(pilot_raw) == PILOT_SHA, "A: PILOT_SET SHA differs")
    pilot = json.loads(pilot_raw)
    check(sha((P2 / "P2_EXCLUSION_REGISTRY.json").read_bytes()) == REGISTRY_SHA == pilot[
        "registry_sha256"], "A: registry SHA differs")
    code = {n: sha((P2 / "harness" / n).read_bytes()) for n in pilot["code_sha256"]
            if n != "P2_SPEC.md"}
    code["P2_SPEC.md"] = sha((P2 / "P2_SPEC.md").read_bytes())
    check(code == pilot["code_sha256"], "A: harness/spec code SHA differs from PILOT_SET")
    print(f"A frozen inputs: PILOT_SET {sha(pilot_raw)[:12]} registry {REGISTRY_SHA[:12]} "
          f"code+spec match={code == pilot['code_sha256']}")

    rows, pairs, fm = [], [], Counter()
    replay = Counter()
    for t in pilot["tasks"]:
        slot, d = t["slot"], EV / t["slot"]
        # ---- B. completeness / integrity ----
        epf = d / "episode.json"
        check(epf.exists(), f"B {slot}: no episode.json")
        ep = load(epf)
        mok, nfiles = manifest_ok(d)
        check(mok, f"B {slot}: MANIFEST.sha256 incomplete or wrong")
        check(ep["pilot_set_sha256"] == PILOT_SHA, f"B {slot}: episode not bound to PILOT_SET")
        check(ep["image_removed"] is True and not ep["d7"]["aborted"], f"B {slot}: D7/image")
        check(not (d / "stop.json").exists(), f"B {slot}: stop.json present")
        common = (d / "P" / "common.txt").read_text(encoding="utf-8")
        gold = gold_files(common, t["gold_paths"])
        a = ep["arms"]
        gens = {}
        for arm in ("U", "S"):
            res_files = sorted((d / f"G-{arm}").glob("attempt-*/result.json"))
            check(len(res_files) == 1, f"B {slot}/{arm}: {len(res_files)} generation results")
            r = load(res_files[-1])
            gens[arm] = r
            comp = (res_files[-1].parent / "completion.txt").read_bytes()
            g = a[arm]["generation"]
            check(r["status"] == "GENERATED" and sha(comp) == g["completion_sha256"],
                  f"B {slot}/{arm}: completion hash/status")
            check(r["seed"] == t["seed"], f"B {slot}/{arm}: seed differs from PILOT_SET")
            check(r["prompt_tokens"] == t["predicted_prompt_eval_count"][arm],
                  f"B {slot}/{arm}: TOKEN_COUNT_MISMATCH")
            check(g["context"] == "CONFIRMED", f"B {slot}/{arm}: context not confirmed")
            check((d / f"G-{arm}" / "post_unload.json").exists(), f"B {slot}/{arm}: no unload")
        # ---- C. endpoints from raw evidence ----
        xu = last_x(d, "U")
        if not gens["U"]["has_patch"]:
            u = False
            check(xu is None, f"C {slot}/U: gate ran without a patch")
        else:
            check(xu is not None, f"C {slot}/U: patch but no gate evidence")
            u = gate(xu) if xu else "NA"
            check(sha(gens["U"]["patch"].encode()) == xu["deterministic"]["candidate_patch_sha256"]
                  if xu else False, f"C {slot}/U: gated patch differs from extracted patch")
        parsed = E.parse(gens["S"]["completion_text"])
        blocks_json = load(d / "S" / "blocks.json")
        resolution = load(d / "S" / "resolution.json")
        check(parsed.code == blocks_json["parse_code"], f"C {slot}/S: parse code mismatch")
        check([sha(b.search) for b in parsed.blocks] ==
              [b["search_sha256"] for b in blocks_json["blocks"]], f"C {slot}/S: blocks differ")
        xs = last_x(d, "S")
        if resolution["code"] != E.OK:
            s: bool | str = False
            check(xs is None, f"C {slot}/S: gate ran on an unresolved edit")
        else:
            check(xs is not None, f"C {slot}/S: resolved but no gate evidence")
            s = gate(xs) if xs else "NA"
            synth = (d / "S" / "synthesized.diff").read_bytes()
            check(sha(synth) == resolution["synthesized_diff_sha256"] ==
                  (xs or {}).get("deterministic", {}).get("candidate_patch_sha256"),
                  f"C {slot}/S: synthesized diff hash chain broken")
        check(u == a["U"]["applies"], f"C {slot}/U: endpoint {a['U']['applies']} != derived {u}")
        check(s == a["S"]["applies"], f"C {slot}/S: endpoint {a['S']['applies']} != derived {s}")
        for arm, x in (("U", xu), ("S", xs)):
            vp = bool(x) and a[arm]["applies"] is True and \
                x["deterministic"]["classification"] == "PASSED"
            check(vp == a[arm]["verified_pass"], f"C {slot}/{arm}: VERIFIED_PASS mismatch")
        # ---- D. independent local replay against the embedded gold files ----
        with tempfile.TemporaryDirectory() as tmp:
            repo = local_repo(Path(tmp), gold)
            if gens["U"]["has_patch"]:
                touched = {ln[6:] for ln in gens["U"]["patch"].splitlines()
                           if ln.startswith(("--- a/", "+++ b/"))}
                if touched and touched <= set(gold):
                    ok = git(repo, "apply", "--check", "-", stdin=gens["U"]["patch"].encode())
                    agree = (ok.returncode == 0) == (u is True)
                    replay["U_compared"] += 1
                    replay["U_agree"] += agree
                    check(agree, f"D {slot}/U: local git apply disagrees with the gate")
                else:
                    replay["U_not_replayable"] += 1
            if parsed.code == E.OK and {b.path for b in parsed.blocks} <= set(gold):
                base = {p: E.BaseFile("100644", c) for p, c in gold.items()}
                r2 = E.resolve(parsed.blocks, base)
                replay["S_compared"] += 1
                agree = r2.code == resolution["code"]
                if r2.code == E.OK:
                    for p, f in r2.edited.items():
                        (repo / p).write_bytes(f.content)
                    diff = git(repo, "diff", "--no-color", "--no-ext-diff", "--",
                               *sorted(r2.edited)).stdout
                    recorded = (d / "S" / "synthesized.diff").read_bytes()
                    same = normalize(diff) == normalize(recorded)
                    agree &= same
                    replay["S_synth_equal_modulo_index_and_mode"] += same
                    if b"\nold mode " in recorded:
                        replay["S_synth_with_mode_change"] += 1
                replay["S_agree"] += agree
                check(agree, f"D {slot}/S: local resolution/synthesis disagrees")
            elif parsed.code == E.OK:
                replay["S_not_replayable"] += 1
        pairs.append((u, s))
        lu = a["U"].get("L3") or a["U"].get("L1")
        ls = a["S"].get("L3") if a["S"].get("L2") == E.OK else a["S"].get("L2")
        fm[f"U:{lu}"] += 1
        fm[f"S:{ls}"] += 1
        rows.append((slot, t["instance_id"], u, s, lu, a["U"].get("L4"), ls, a["S"].get("L4"),
                     gens["U"]["completion_tokens"], gens["S"]["completion_tokens"],
                     xu and xu["deterministic"]["detail"], xs and xs["deterministic"]["detail"],
                     nfiles))
    # ---- E. statistics (§8) ----
    valid = [(u, s) for u, s in pairs if "NA" not in (u, s)]
    both = sum(1 for u, s in valid if u and s)
    s_only = sum(1 for u, s in valid if s and not u)
    u_only = sum(1 for u, s in valid if u and not s)
    neither = len(valid) - both - s_only - u_only
    m = s_only + u_only
    p = Fraction(sum(comb(m, k) for k in range(s_only, m + 1)), 2**m) if m else None
    if len(valid) < 10:
        concl = "P2-D"
    elif both == s_only == u_only == 0:
        concl = "P2-C"
    elif s_only > u_only and p is not None and p < Fraction(5, 100):
        concl = "P2-A"
    else:
        concl = "P2-B"
    rep = load(EV / "_report" / "report.json")
    mine = {"both": both, "s_only": s_only, "u_only": u_only, "neither": neither,
            "n_v": len(valid), "discordant": m, "k_s": both + s_only, "k_u": both + u_only}
    check(rep["table"] == mine, f"E: report table {rep['table']} != recomputed {mine}")
    check(rep["sign_test_p_one_sided"] == str(p), "E: sign-test p differs")
    check(rep["conclusion"] == concl, "E: conclusion differs")

    print("\nslot  instance                          U      S      U-layer(L3/L4)                "
          "       S-layer(L2/L3/L4)                 tok U/S   tests U | S       files")
    for r in rows:
        print(f"{r[0]} {r[1]:<33} {r[2]!s:<6} {r[3]!s:<6} {r[4]!s:<20} {r[5]!s:<16} "
              f"{r[6]!s:<18} {r[7]!s:<16} {r[8]:>4}/{r[9]:<4} {r[10]!s:>6} | {r[11]!s:<6} "
              f"{r[12]}")
    print(f"\nE table {mine}  p_one_sided={p} ({float(p) if p is not None else None})  "
          f"conclusion={concl}  report_agrees={rep['table'] == mine and rep['conclusion'] == concl}")
    print(f"D local replay {dict(replay)}")
    print(f"F failure layers {dict(sorted(fm.items()))}")
    print(f"\nDEFECTS: {len(defects)}")
    for x in defects:
        print("  -", x)
    return 0 if not defects else 1


if __name__ == "__main__":
    sys.exit(main())
