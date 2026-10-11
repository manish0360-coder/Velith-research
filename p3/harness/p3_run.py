"""P3 generator capability probe (p3/P3_SPEC.md). Research harness only; Velith main untouched.

Commands (WSL, from the Velith-research root; ANTHROPIC_API_KEY set by the RD):
  python3 -B p3/harness/p3_run.py preflight    FG-2: SHAs, extractor check, count_tokens (no generation)
  python3 -B p3/harness/p3_run.py run          13 tasks, one generation each; resumable
  python3 -B p3/harness/p3_run.py report       k, n_v, decision code (§4)

Reused read-only: P2 PILOT_SET + prompts, P2 Docker operations, the frozen P1 `stage_x`
(probe library), the P2 retry rule and layer mapping. Only the generator differs from P2-U.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Protocol

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parents[1]
sys.path.insert(0, str(RESEARCH / "p2" / "harness"))
import p2_admit as A  # noqa: E402
import p2_harness as H  # noqa: E402
import p2_phaseb as B  # noqa: E402

P3 = RESEARCH / "p3"
EVIDENCE = P3 / "evidence"
P2_EVIDENCE = RESEARCH / "p2" / "evidence"
PILOT_SET = RESEARCH / "p2" / "PILOT_SET.json"
PILOT_SHA = "44b884125f37ce296dcc59d0fdc29038f15ecece13cc9a393ecbfe2673213305"
SPEC = P3 / "P3_SPEC.md"
EXTRACT_SCRIPT = HERE / "p3_extract.py"
API_BASE = "https://api.anthropic.com/v1"
API_VERSION = "2023-06-01"
MODEL = "claude-opus-5-5"
MAX_TOKENS = 1024  # = P2 num_predict (one-variable comparability, D3)
TEMPERATURE = 0.0
HTTP_TIMEOUT_S = 600.0
MAX_GEN_ATTEMPTS = 2
RETRYABLE_HTTP = frozenset({408, 409, 429, 500, 502, 503, 504, 529})
K_PASS, K_FLOOR, N_MIN = 3, 1, 10


class P3Stop(Exception):
    """Pilot-level stop; never a task outcome. Resumable after the cause is fixed."""


# ---- pure rules -------------------------------------------------------------------------------
def payload(prompt: str) -> dict[str, Any]:
    """D2/D3: one user message, no system prompt, no tools, no thinking."""
    return {"model": MODEL, "max_tokens": MAX_TOKENS, "temperature": TEMPERATURE,
            "messages": [{"role": "user", "content": prompt}]}


def interpret(status: int | None, body: bytes, error: str | None = None) -> dict[str, Any]:
    """GENERATED | RETRYABLE (no completion received) | FATAL (request rejected; stop)."""
    if status is None:
        return {"status": "RETRYABLE", "error": error or "transport"}
    try:
        doc = json.loads(body.decode("utf-8")) if body else {}
    except (UnicodeDecodeError, json.JSONDecodeError):
        doc = {}
    if status == 200 and doc.get("type") == "message":
        text = "".join(c.get("text", "") for c in doc.get("content", []) if c.get("type") == "text")
        usage = doc.get("usage") or {}
        return {"status": "GENERATED", "completion_text": text, "model": doc.get("model"),
                "stop_reason": doc.get("stop_reason"), "input_tokens": usage.get("input_tokens"),
                "output_tokens": usage.get("output_tokens"), "message_id": doc.get("id")}
    err_type = (doc.get("error") or {}).get("type")
    if status in RETRYABLE_HTTP or err_type == "overloaded_error":
        return {"status": "RETRYABLE", "http_status": status, "error": err_type}
    return {"status": "FATAL", "http_status": status, "error": err_type,
            "message": (doc.get("error") or {}).get("message")}


def endpoints(gen_ok: bool, has_patch: bool, x: Mapping[str, Any] | None
              ) -> tuple[bool | str, bool | str]:
    """(PATCH_APPLIES, VERIFIED_PASS) — P2 §7 rules for one U arm."""
    applies = H.u_applies(gen_ok, has_patch, dict(x) if x else None)
    return applies, H.verified_pass(applies, dict(x) if x else None)


def decision(k: int, n_v: int, infra: int) -> str:
    if n_v < N_MIN or infra >= H.INFRA_STOP:
        return "P3-D"
    if k >= K_PASS:
        return "P3-A"
    return "P3-B" if k > K_FLOOR else "P3-C"


# ---- boundaries -------------------------------------------------------------------------------
class Api(Protocol):
    def post(self, path: str, body: dict[str, Any]) -> tuple[int | None, bytes, str | None]: ...


class HttpApi:  # pragma: no cover
    def __init__(self) -> None:
        self._key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not self._key:
            raise P3Stop("ANTHROPIC_API_KEY is not set in this shell")

    def post(self, path: str, body: dict[str, Any]) -> tuple[int | None, bytes, str | None]:
        req = urllib.request.Request(
            f"{API_BASE}{path}", data=json.dumps(body).encode("utf-8"), method="POST",
            headers={"x-api-key": self._key, "anthropic-version": API_VERSION,
                     "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S) as r:
                return r.status, r.read(), None
        except urllib.error.HTTPError as e:
            return e.code, e.read(), None
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            return None, b"", type(e).__name__


class Ops(Protocol):
    def free_bytes(self) -> int: ...
    def pull(self, ref: str) -> bool: ...
    def inspect(self, ref: str) -> tuple[list[str], str, str] | None: ...
    def remove(self, ref: str) -> bool: ...
    def verifier_image_id(self) -> str: ...
    def extract(self, image_id: str, completion: str, proposer_sha: str) -> dict[str, Any]: ...
    def gate(self, spec: dict[str, Any], patch: str, run_dir: Path, timeout: float, arm: str
             ) -> dict[str, Any]: ...


# ---- inputs -----------------------------------------------------------------------------------
def load_pilot() -> dict[str, Any]:
    raw = PILOT_SET.read_bytes()
    if H.sha256_bytes(raw) != PILOT_SHA:
        raise P3Stop("P2 PILOT_SET.json differs from 44b88412")
    return dict(json.loads(raw))


def prompt_u(task: Mapping[str, Any], p2_root: Path = P2_EVIDENCE) -> str:
    raw = (p2_root / task["slot"] / "P" / "prompt_U.txt").read_bytes()
    if H.sha256_bytes(raw) != task["identity"]["U"]:
        raise P3Stop(f"{task['slot']}: prompt_U.txt differs from the frozen identity")
    return raw.decode("utf-8")


# ---- FG-2 preflight ---------------------------------------------------------------------------
def preflight(api: Api, ops: Ops, pilot: Mapping[str, Any], out: Path = EVIDENCE / "_preflight",
              p2_root: Path = P2_EVIDENCE) -> dict[str, Any]:
    if (out / "preflight.json").exists():
        raise P3Stop("preflight.json exists (written once)")
    route = pilot["generation_route"]
    img = ops.verifier_image_id()
    sample = "```diff\n--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-a\n+b\n```"
    ex = ops.extract(img, sample, route["module_sha256"]["velith/agent/proposer.py"])
    tokens: dict[str, Any] = {}
    for t in pilot["tasks"]:
        body = {k: v for k, v in payload(prompt_u(t, p2_root)).items()
                if k in ("model", "messages")}
        status, raw, err = api.post("/messages/count_tokens", body)
        doc = json.loads(raw.decode("utf-8")) if status == 200 else {}
        tokens[t["slot"]] = doc.get("input_tokens") if status == 200 else \
            {"http_status": status, "error": err, "body": raw[:300].decode("utf-8", "replace")}
    ok = img == route["image_id"] and ex.get("status") == "OK" and ex.get("has_patch") is True \
        and all(isinstance(v, int) for v in tokens.values())
    rec = {"utc": H.p1().utc(), "fg": "FG-2", "verdict": "PASS" if ok else "FAIL",
           "model": MODEL, "max_tokens": MAX_TOKENS, "temperature": TEMPERATURE,
           "pilot_set_sha256": PILOT_SHA, "verifier_image_id": img, "extract_check": ex,
           "input_tokens": tokens, "spec_sha256": H.sha256_bytes(SPEC.read_bytes()),
           "harness_sha256": {p.name: H.sha256_bytes(p.read_bytes())
                              for p in sorted(HERE.glob("p3_*.py"))}}
    A.write(out / "preflight.json", rec)
    return rec


# ---- one task ---------------------------------------------------------------------------------
def generate(api: Api, prompt: str, gdir: Path) -> dict[str, Any]:
    """One generation; resumable; at most one retry, only if no completion was received."""
    done = sorted(gdir.glob("attempt-*/result.json"))
    consumed = [B.load_json(f) for f in done]
    gen = next((r for r in consumed if r["status"] == "GENERATED"), None)
    while gen is None:
        if len(consumed) >= MAX_GEN_ATTEMPTS:
            return {**consumed[-1], "attempts": len(consumed)}
        n = len(consumed) + 1
        adir = gdir / f"attempt-{n}"
        body = payload(prompt)
        A.write(adir / "request.json", {**body, "messages": [{"role": "user",
                "content_sha256": H.sha256_bytes(prompt.encode("utf-8"))}]})
        started = time.monotonic()
        status, raw, err = api.post("/messages", body)
        (adir / "response_raw.json").write_bytes(raw)  # raw first, before interpretation
        res = {**interpret(status, raw, err), "attempt": n, "utc": H.p1().utc(),
               "latency_seconds": round(time.monotonic() - started, 3)}
        if res["status"] == "FATAL":
            A.write(gdir / f"fatal-{n}-{int(time.time())}.json",
                    {**res, "raw": raw.decode("utf-8", "replace")[:4000]})
            (adir / "response_raw.json").unlink()
            (adir / "request.json").unlink()
            adir.rmdir()
            raise P3Stop(f"API rejected the request: HTTP {res.get('http_status')} "
                         f"{res.get('error')} {res.get('message')} (no attempt consumed)")
        if res["status"] == "GENERATED":
            (adir / "completion.txt").write_bytes(res["completion_text"].encode("utf-8"))
            gen = res
        A.write(adir / "result.json", res)
        consumed.append(res)
    return {**gen, "attempts": len(consumed)}


def run_task(api: Api, ops: Ops, pilot: Mapping[str, Any], task: Mapping[str, Any], root: Path,
             p2_root: Path = P2_EVIDENCE) -> dict[str, Any]:
    d = root / f"P3-{task['slot'][3:]}"
    epf = d / "episode.json"
    if epf.exists():
        return dict(B.load_json(epf))
    spec_path = p2_root / task["slot"] / "A" / "spec.json"
    if H.sha256_bytes(spec_path.read_bytes()) != task["spec_sha256"]:
        raise P3Stop(f"{task['slot']}: spec changed after P2 freeze")
    spec = B.load_json(spec_path)
    prompt = prompt_u(task, p2_root)
    route = pilot["generation_route"]
    if ops.verifier_image_id() != route["image_id"]:
        raise P3Stop("velith-verifier:m0 image ID changed")
    ref = task["ref"]
    need, free = A.storage_need(int(task["compressed_bytes"])), ops.free_bytes()
    if free < need:
        raise P3Stop(f"storage gate: free {free} < need {need} before {task['slot']}")
    ep: dict[str, Any] = {"slot": d.name, "p2_slot": task["slot"],
                          "instance_id": task["instance_id"], "model": MODEL,
                          "pilot_set_sha256": PILOT_SHA}
    pulled = ops.pull(ref) or ops.pull(ref)
    try:
        insp = ops.inspect(ref) if pulled else None
        aborted = insp is None or ref not in insp[0] or insp[1] != A.PLATFORM or \
            insp[2] != task["image_id"]
        ep["d7"] = {"pulled": pulled, "inspect": insp, "aborted": aborted}
        x: dict[str, Any] | None = None
        gen: dict[str, Any] = {}
        has_patch = False
        if not aborted:
            gen = generate(api, prompt, d / "G")
            if gen["status"] == "GENERATED":
                ex = ops.extract(route["image_id"], gen["completion_text"],
                                 route["module_sha256"]["velith/agent/proposer.py"])
                A.write(d / "E" / "extract.json", ex)
                if ex.get("status") != "OK":
                    raise H.HarnessStop(f"{d.name}: extractor {ex.get('status')}")
                has_patch = bool(ex["has_patch"])
                (d / "E" / "patch.diff").write_bytes(ex["patch"].encode("utf-8"))
                if has_patch:
                    x, cand_stdout, n = B.stage_x(ops, task, spec, ex["patch"], "U",  # type: ignore[arg-type]
                                                  d)
                    ep["layers"] = B.l3_l4("U", x, cand_stdout, ex["patch"],
                                           task["protected_paths"])
                    ep["x_attempts"] = n
                    det = x["deterministic"]
                    oc = (det.get("candidate") or {}).get("outcomes") or {}
                    ep["tests"] = {k: f"{sum(1 for i in spec[k] if oc.get(i) == 'passed')}/"
                                      f"{len(spec[k])}" for k in ("fail_to_pass", "pass_to_pass")}
                    ep["classification"] = det["classification"]
                    ep["reason"] = det["reason"]
                else:
                    ep["layers"] = {"L1": "NO_OUTPUT"}
        gen_ok = (not aborted) and gen.get("status") == "GENERATED"
        applies, verified = endpoints(gen_ok, has_patch, x)
        if aborted:
            applies = verified = H.NA
        ep.update(applies=applies, verified_pass=verified,
                  infra_unresolved=H.NA in (applies, verified),
                  generation={k: gen.get(k) for k in ("status", "attempts", "model",
                                                      "stop_reason", "input_tokens",
                                                      "output_tokens", "latency_seconds",
                                                      "message_id")})
    finally:
        if pulled:
            ep["image_removed"] = ops.remove(ref)
    if pulled and not ep.get("image_removed"):
        raise P3Stop(f"image delete failed for {ref}")
    ep["utc"] = H.p1().utc()
    A.write(epf, ep)
    H.p1().manifest(d)
    return dict(B.load_json(epf))


def run(api: Api, ops: Ops, pilot: Mapping[str, Any], root: Path = EVIDENCE,
        p2_root: Path = P2_EVIDENCE) -> list[dict[str, Any]]:
    pre = root / "_preflight" / "preflight.json"
    if not pre.exists() or B.load_json(pre)["verdict"] != "PASS":
        raise P3Stop("FG-2 preflight is not PASS")
    eps: list[dict[str, Any]] = []
    for t in pilot["tasks"]:
        if sum(bool(e.get("infra_unresolved")) for e in eps) >= H.INFRA_STOP:
            raise P3Stop(f"unresolved infrastructure failures on >= {H.INFRA_STOP} tasks (P3-D)")
        eps.append(run_task(api, ops, pilot, t, root, p2_root))
    return eps


def report(pilot: Mapping[str, Any], root: Path = EVIDENCE) -> dict[str, Any]:
    eps = []
    for t in pilot["tasks"]:
        f = root / f"P3-{t['slot'][3:]}" / "episode.json"
        if not f.exists():
            raise P3Stop(f"{f.parent.name}: no episode (run incomplete)")
        eps.append(B.load_json(f))
    valid = [e for e in eps if e["verified_pass"] != H.NA]
    k = sum(1 for e in valid if e["verified_pass"] is True)
    infra = sum(1 for e in eps if e["infra_unresolved"])
    out = {"n": len(eps), "n_v": len(valid), "k_verified": k,
           "applies": sum(1 for e in valid if e["applies"] is True), "infra_unresolved": infra,
           "decision": decision(k, len(valid), infra),
           "per_task": [{"slot": e["slot"], "instance_id": e["instance_id"],
                         "applies": e["applies"], "verified": e["verified_pass"],
                         "layers": e.get("layers"), "tests": e.get("tests"),
                         "stop_reason": e["generation"]["stop_reason"]} for e in eps]}
    A.write(root / "_report" / "report.json", out)
    return out


# ---- real operations --------------------------------------------------------------------------
class DockerP3Ops(B.DockerBOps):  # pragma: no cover
    def extract(self, image_id: str, completion: str, proposer_sha: str) -> dict[str, Any]:
        p = subprocess.run(
            ["docker", "run", "--rm", "-i", "--network", "none", "--read-only", "--cap-drop",
             "ALL", "--security-opt", "no-new-privileges", "--entrypoint", "python", image_id,
             "-c", EXTRACT_SCRIPT.read_text(encoding="utf-8")],
            input=json.dumps({"completion": completion,
                              "expected_proposer_sha256": proposer_sha}).encode("utf-8"),
            capture_output=True, timeout=300, check=False)
        for line in p.stdout.decode("utf-8", "replace").splitlines():
            if line.startswith("P3EXTRACT_RESULT "):
                return dict(json.loads(line[len("P3EXTRACT_RESULT "):]))
        return {"status": "NO_RESULT", "rc": p.returncode,
                "stderr": p.stderr.decode("utf-8", "replace")[-500:]}

    def gate(self, spec: dict[str, Any], patch: str, run_dir: Path, timeout: float,
             arm: str = "U") -> dict[str, Any]:
        return dict(H.p1().stage_x(spec, patch, run_dir, timeout, "P3-X"))


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    ap = argparse.ArgumentParser(prog="p3_run")
    ap.add_argument("cmd", choices=("preflight", "run", "report"))
    args = ap.parse_args(argv)
    try:
        pilot = load_pilot()
        if args.cmd == "report":
            r = report(pilot)
            print(json.dumps({k: v for k, v in r.items() if k != "per_task"}, indent=2))
            return 0
        api, ops = HttpApi(), DockerP3Ops()
        if args.cmd == "preflight":
            rec = preflight(api, ops, pilot)
            print(json.dumps({k: rec[k] for k in ("verdict", "model", "verifier_image_id",
                                                   "extract_check", "input_tokens")}, indent=2))
            return 0 if rec["verdict"] == "PASS" else 1
        eps = run(api, ops, pilot)
        print(json.dumps([{"slot": e["slot"], "applies": e["applies"],
                           "verified": e["verified_pass"]} for e in eps], indent=2))
        return 0
    except (P3Stop, H.HarnessStop, B.PhaseBStop, A.AdmissionStop) as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
