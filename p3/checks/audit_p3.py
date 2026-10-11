"""Read-only audit of P3 against p3/P3_SPEC.md (incl. A-1) and the raw evidence.

Run (Velith-research root; no Docker, no API, no network, writes nothing):
    python3 -B p3/checks/audit_p3.py

A. frozen inputs: P2 PILOT_SET, P2 code, P3 harness SHAs; Velith proposer.py pin
B. per episode: MANIFEST complete/correct; provenance (task, prompt SHA, request params, model,
   raw response -> completion -> result chain); exactly one consumed attempt; A-1 fatal record
C. extraction re-run with the frozen `_extract_patch` source (loaded from the SHA-pinned file,
   executed in isolation) and compared with extract.json / patch.diff
D. gate and verification re-derived from the probe evidence: patch hash chain, apply rule,
   per-test outcomes vs the spec's FAIL_TO_PASS / PASS_TO_PASS lists, protected paths,
   test-patch hash, network isolation, classification consistency
E. independent local replay: `git apply --check` against the gold files embedded in the prompt
F. decision rule recomputed; per-task comparison with P2; similarity to the gold patch
Exit 0 iff A-E have no defect.
"""
from __future__ import annotations

import ast
import difflib
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
P2, P3 = ROOT / "p2", ROOT / "p3"
EV, P2EV = P3 / "evidence", P2 / "evidence"
VELITH = Path("/mnt/e/Projects/OpenSourceLab/repos/Velith")
PILOT_SHA = "44b884125f37ce296dcc59d0fdc29038f15ecece13cc9a393ecbfe2673213305"
PROPOSER_SHA = "91d32296ab5e0c02f2a41ae0b843053d86cb0674c61adfb0aab5035e08b3b113"
APPLIED = ("RAN", "TEST_PATCH_FAILED", "RESTORE_FAILED")
defects: list[str] = []      # evidence / derivation defects (fail the audit)
deviations: list[str] = []   # protocol deviations observed in the evidence (reported)
findings: list[str] = []     # substantive findings (reported)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def check(cond: bool, msg: str) -> None:
    if not cond:
        defects.append(msg)


def frozen_extract_patch(velith: Path) -> Any:
    """Execute exactly the pinned `_extract_patch` and its module constants, nothing else."""
    raw = (velith / "src" / "velith" / "agent" / "proposer.py").read_bytes()
    check(sha(raw) == PROPOSER_SHA, "A: Velith proposer.py differs from the pin")
    tree = ast.parse(raw)
    keep: list[ast.stmt] = [n for n in tree.body if
            (isinstance(n, ast.Assign) and any(getattr(t, "id", "") in
             ("_FENCE", "_FENCE_LANGUAGE_TAGS", "_DIFF_PREFIXES") for t in n.targets)) or
            (isinstance(n, ast.AnnAssign) and getattr(n.target, "id", "") in
             ("_FENCE", "_FENCE_LANGUAGE_TAGS", "_DIFF_PREFIXES")) or
            (isinstance(n, ast.FunctionDef) and n.name == "_extract_patch")]
    ns: dict[str, Any] = {"Final": Any}
    exec(compile(ast.Module(body=keep, type_ignores=[]), "proposer.py", "exec"), ns)  # noqa: S102
    return ns["_extract_patch"]


def gate(det: dict[str, Any]) -> bool | str:
    c = det.get("candidate") or {}
    if c.get("status") == "PATCH_APPLY_FAILED":
        return False
    if c.get("status") in APPLIED or c.get("surface"):
        return True
    return "NA"


def gold_files(common: str, paths: list[str]) -> dict[str, bytes]:
    out = {}
    for p in paths:
        head, end = f"=== FILE: {p} ===\n", f"=== END FILE: {p} ==="
        i = common.index(head) + len(head)
        out[p] = common[i:common.index(end, i)].encode("utf-8")
    return out


def git(repo: Path, *a: str, stdin: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", "-C", str(repo), *a], input=stdin, capture_output=True,
                          check=False)


def changed_lines(patch: str) -> list[str]:
    return [ln for ln in patch.splitlines()
            if ln[:1] in "+-" and not ln.startswith(("+++", "---"))]


def manifest_ok(d: Path) -> tuple[bool, int]:
    listed = {}
    for line in (d / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        h, rel = line.split("  ", 1)
        listed[rel[2:]] = h
    actual = {f.relative_to(d).as_posix() for f in d.rglob("*")
              if f.is_file() and f.name != "MANIFEST.sha256"}
    return set(listed) == actual and all(sha((d / r).read_bytes()) == h
                                         for r, h in listed.items()), len(listed)


def main() -> int:
    velith = Path(sys.argv[1]) if len(sys.argv) > 1 else VELITH
    extract = frozen_extract_patch(velith)
    pilot_raw = (P2 / "PILOT_SET.json").read_bytes()
    check(sha(pilot_raw) == PILOT_SHA, "A: P2 PILOT_SET differs")
    pilot = json.loads(pilot_raw)
    code = {n: sha((P2 / "harness" / n).read_bytes()) for n in pilot["code_sha256"]
            if n != "P2_SPEC.md"}
    code["P2_SPEC.md"] = sha((P2 / "P2_SPEC.md").read_bytes())
    check(code == pilot["code_sha256"], "A: P2 code/spec changed")
    run_sha = sha((P3 / "harness" / "p3_run.py").read_bytes())
    ext_sha = sha((P3 / "harness" / "p3_extract.py").read_bytes())
    pre = load(EV / "_preflight" / "preflight.json")
    check(pre["verdict"] == "PASS" and pre["harness_sha256"]["p3_extract.py"] == ext_sha,
          "A: preflight not PASS or extractor changed since preflight")
    print(f"A: PILOT_SET {sha(pilot_raw)[:12]}  P2 code match={code == pilot['code_sha256']}  "
          f"p3_run {run_sha[:12]}  p3_extract {ext_sha[:12]}  proposer pin ok")

    rows, k, applies, valid = [], 0, 0, 0
    for t in pilot["tasks"]:
        slot = "P3-" + t["slot"][3:]
        d = EV / slot
        ep = load(d / "episode.json")
        spec = load(P2EV / t["slot"] / "A" / "spec.json")
        prompt = (P2EV / t["slot"] / "P" / "prompt_U.txt").read_bytes()
        # ---- B. provenance ----
        mok, nfiles = manifest_ok(d)
        check(mok, f"B {slot}: MANIFEST incomplete or wrong")
        check(ep["instance_id"] == t["instance_id"] == spec["instance_id"], f"B {slot}: task")
        check(ep["pilot_set_sha256"] == PILOT_SHA, f"B {slot}: PILOT_SET binding")
        check(ep["harness_sha256"] == run_sha, f"B {slot}: produced by a different p3_run.py")
        check(sha(prompt) == t["identity"]["U"], f"B {slot}: prompt differs from frozen U")
        check(ep["image_removed"] and not ep["d7"]["aborted"] and
              ep["d7"]["inspect"][2] == t["image_id"], f"B {slot}: image identity / removal")
        results = sorted((d / "G").glob("attempt-*/result.json"))
        check(len(results) == 1, f"B {slot}: {len(results)} consumed attempts")
        a = results[0].parent
        req = load(a / "request.json")
        check(req == {"model": "claude-opus-5-5", "max_tokens": 1024, "messages": [
            {"role": "user", "content_sha256": t["identity"]["U"]}]},
            f"B {slot}: request parameters differ from D3+A-1")
        raw = load(a / "response_raw.json")
        res = load(a / "result.json")
        text = "".join(c.get("text", "") for c in raw["content"] if c.get("type") == "text")
        comp = (a / "completion.txt").read_text(encoding="utf-8")
        check(raw["type"] == "message" and raw["model"] == "claude-opus-5-5" and
              raw["id"] == res["message_id"] == ep["generation"]["message_id"] and
              raw["stop_reason"] == res["stop_reason"] and text == comp ==
              res["completion_text"], f"B {slot}: raw -> completion -> result chain broken")
        thinking = (raw["usage"].get("output_tokens_details") or {}).get("thinking_tokens", 0)
        if thinking or [c["type"] for c in raw["content"]] != ["text"]:
            deviations.append(f"{slot}: model emitted {thinking} thinking tokens / content "
                              f"{[c['type'] for c in raw['content']]} although none was "
                              "requested (D3 'no extended thinking' not enforced by the request)")
        # ---- C. extraction ----
        ex = load(d / "E" / "extract.json")
        mine = extract(comp)
        check(ex["status"] == "OK" and ex["proposer_sha256"] == PROPOSER_SHA and
              ex["patch"] == mine and (d / "E" / "patch.diff").read_text(encoding="utf-8")
              == mine and ex["has_patch"] == bool(mine.strip()),
              f"B/C {slot}: extraction does not reproduce")
        # ---- D. gate / verification ----
        xs = sorted(d.glob("X-U-*/evidence.json"))
        x = load(xs[-1])["deterministic"] if xs else None
        if not ex["has_patch"]:
            check(x is None and ep["applies"] is False, f"D {slot}: no-patch handling")
            ap: bool | str = False
            vp: bool | str = False
            ftp = ptp = "-"
        else:
            assert x is not None
            check(x["candidate_patch_sha256"] == sha(mine.encode()), f"D {slot}: gated patch")
            check(x["test_patch_sha256"] == sha(spec["test_patch"].encode()) and
                  x["protected_paths"] == spec["protected_paths"], f"D {slot}: test gate inputs")
            ap = gate(x)
            oc = (x.get("candidate") or {}).get("outcomes") or {}
            req_ids = spec["fail_to_pass"] + spec["pass_to_pass"]
            all_pass = bool(req_ids) and all(oc.get(i) == "passed" for i in req_ids)
            vp = ap is True and x["classification"] == "PASSED"
            if x["classification"] == "PASSED":
                check(all_pass, f"D {slot}: PASSED but a required test is not 'passed'")
                c = x["candidate"]
                check(c["network_mode"] == "none" and c["net_probe"].startswith("blocked") and
                      not c["removed"] and not c["tampered"], f"D {slot}: isolation/tamper")
                base = x["baseline"] or {}
                check(base.get("status") == "RAN", f"D {slot}: baseline not healthy")
            if ap is True and x["classification"] != "PASSED":
                check(not all_pass, f"D {slot}: all required passed but not PASSED")
            touched = {ln[6:] for ln in mine.splitlines()
                       if ln.startswith(("--- a/", "+++ b/"))}
            check(not touched & set(spec["protected_paths"]), f"D {slot}: touches tests")
            ftp = f"{sum(oc.get(i) == 'passed' for i in spec['fail_to_pass'])}/" \
                  f"{len(spec['fail_to_pass'])}"
            ptp = f"{sum(oc.get(i) == 'passed' for i in spec['pass_to_pass'])}/" \
                  f"{len(spec['pass_to_pass'])}"
        check(ap == ep["applies"] and vp == ep["verified_pass"],
              f"D {slot}: endpoints {ep['applies']},{ep['verified_pass']} != {ap},{vp}")
        # ---- E. local replay against gold files from the prompt ----
        replay = "-"
        if ex["has_patch"]:
            gold = gold_files((P2EV / t["slot"] / "P" / "common.txt").read_text("utf-8"),
                              t["gold_paths"])
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                git(repo, "init", "-q")
                for p, c in gold.items():
                    (repo / p).parent.mkdir(parents=True, exist_ok=True)
                    (repo / p).write_bytes(c)
                r = git(repo, "apply", "--check", "-", stdin=mine.encode())
                replay = "apply" if r.returncode == 0 else \
                    "reject:" + r.stderr.decode().strip().splitlines()[0][:60]
                check((r.returncode == 0) == (ap is True), f"E {slot}: local apply != gate")
        # ---- E2. extractor false-negative probe: the fenced block WITHOUT .strip() ----
        unstripped = "-"
        if ex["has_patch"] and ap is False and "```" in comp:
            st = comp.find("```") + 3
            block = comp[st:comp.find("```", st)].split("\n")
            if block and block[0].strip().lower() in ("diff", "patch", "udiff", "python"):
                block = block[1:]
            cand = "\n".join(block).strip("\n") + "\n"
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                git(repo, "init", "-q")
                for p, c in gold.items():
                    (repo / p).parent.mkdir(parents=True, exist_ok=True)
                    (repo / p).write_bytes(c)
                ok = git(repo, "apply", "--check", "-", stdin=cand.encode()).returncode == 0
            unstripped = "APPLIES" if ok else "rejects"
            if ok:
                findings.append(f"{slot}: extractor false negative — the model's fenced diff "
                                "applies, but _extract_patch's .strip() removed a trailing "
                                "whitespace-only context line, making it a corrupt patch")
        # ---- F. gold similarity (contamination signal; not a defect) ----
        sim = difflib.SequenceMatcher(None, "\n".join(changed_lines(mine)),
                                      "\n".join(changed_lines(spec["patch"]))).ratio() \
            if ex["has_patch"] else 0.0
        identical = ex["has_patch"] and changed_lines(mine) == changed_lines(spec["patch"])
        p2ep = load(P2EV / t["slot"] / "episode.json")["arms"]["U"]
        valid += ep["verified_pass"] != "NA"
        k += ep["verified_pass"] is True
        applies += ep["applies"] is True
        layer = (ep.get("layers") or {})
        rows.append((slot, t["instance_id"], ap, vp, layer.get("L3") or layer.get("L1"),
                     layer.get("L4"), ftp, ptp, raw["stop_reason"], raw["usage"]["output_tokens"],
                     f"{sim:.2f}{' IDENTICAL' if identical else ''}", replay,
                     f"{p2ep['applies']}/{p2ep['verified_pass']}", nfiles, unstripped))
    fatal = sorted((EV / "P3-01" / "G").glob("fatal-*.json"))
    check(len(fatal) == 1 and load(fatal[0])["http_status"] == 400 and
          "temperature" in load(fatal[0])["message"], "B: A-1 fatal record missing/altered")
    decision = "P3-D" if valid < 10 else "P3-A" if k >= 3 else "P3-B" if k == 2 else "P3-C"
    rep = load(EV / "_report" / "report.json")
    check((rep["k_verified"], rep["n_v"], rep["applies"], rep["decision"]) ==
          (k, valid, applies, decision), "F: report differs from recomputation")

    print("\nslot   instance                          applies verified L3/L1              "
          "L4                 F2P   P2P      stop      out  gold-sim        local-replay"
          "                                    P2-U(app/ver) files")
    for row in rows:
        print(f"{row[0]}  {row[1]:<33} {row[2]!s:<7} {row[3]!s:<8} {row[4]!s:<20} "
              f"{row[5]!s:<18} {row[6]:<5} {row[7]:<8} {row[8]:<9} {row[9]:<4} {row[10]:<15} "
              f"{row[11]:<45} {row[12]:<13} {row[13]}  unstripped:{row[14]}")
    print(f"\nF: k_verified={k} applies={applies} n_v={valid} decision={decision} "
          f"report_agrees={rep['decision'] == decision}")
    print(f"B: A-1 fatal record: {fatal[0].name if fatal else None}")
    ident = [row[0] for row in rows if "IDENTICAL" in row[10]]
    print(f"F: changed lines identical to the gold patch: {len(ident)}/13 {ident}")
    for title, items in (("DEVIATIONS", deviations), ("FINDINGS", findings)):
        print(f"\n{title}: {len(items)}")
        for m in items:
            print("  -", m)
    print(f"\nDEFECTS: {len(defects)}")
    for m in defects:
        print("  -", m)
    return 0 if not defects else 1


if __name__ == "__main__":
    sys.exit(main())
