"""P2 Phase B machinery (P2_SPEC.md §4, §7, §8, §12-§17; FG-5, FG-6, Phase B, report).

Commands (WSL, from the Velith-research root):
  python3 -B p2/harness/p2_phaseb.py gencheck            FG-5: every slot x arm, network none
  python3 -B p2/harness/p2_phaseb.py freeze              FG-6: PILOT_SET.json + registry append
  python3 -B p2/harness/p2_phaseb.py run --pilot-sha S   Phase B (after FG-8 only); resumable
  python3 -B p2/harness/p2_phaseb.py report              paired table, sign test, conclusion

Frozen inputs are never modified: P2_SPEC.md, the FG-1 initial registry entries, the FG-3
artifacts, the Phase-A evidence, P1. P1 code is imported read-only through `p2_harness.p1()`.
Every Docker/Ollama action goes through `BOps`; the tests use a fake and never call a model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import p2_admit as A  # noqa: E402
import p2_edits as E  # noqa: E402
import p2_harness as H  # noqa: E402

P2 = H.RESEARCH / "p2"
EVIDENCE = A.EVIDENCE
PILOT_SET = P2 / "PILOT_SET.json"
REGISTRY = P2 / "P2_EXCLUSION_REGISTRY.json"
GENCHECK = EVIDENCE / "_gencheck"
REPORT = EVIDENCE / "_report"
GEN_SCRIPT = HERE / "p2_gen.py"
CODE_FILES = ("p2_edits.py", "p2_harness.py", "p2_lottery.py", "p2_admit.py", "p2_phaseb.py",
              "p2_gen.py")
ARM_ORDER_SALT = "|velith-m2pv-p2-arm-order"
ARMS = ("U", "S")
MARKERS = ("P2GEN_SENT", "P2GEN_COMPLETION", "P2GEN_RESULT")


class PhaseBStop(Exception):
    """Pilot-level stop (§17). Never a task outcome; the run is resumable after RD review."""


# ---- pure rules -------------------------------------------------------------------------------
def arm_order(instance_id: str) -> tuple[str, str]:
    """§13: U first iff the first byte of SHA-256(instance_id + salt) is even."""
    first = hashlib.sha256((instance_id + ARM_ORDER_SALT).encode("utf-8")).digest()[0]
    return ("U", "S") if first % 2 == 0 else ("S", "U")


def code_shas() -> dict[str, str]:
    shas = {name: H.sha256_bytes((HERE / name).read_bytes()) for name in CODE_FILES}
    shas["P2_SPEC.md"] = H.sha256_bytes(H.SPEC.read_bytes())
    return shas


def parse_markers(raw: bytes) -> dict[str, Any]:
    marks: dict[str, Any] = {}
    for line in raw.decode("utf-8", errors="replace").splitlines():
        for key in MARKERS:
            if line.startswith(key + " "):
                marks[key] = json.loads(line[len(key) + 1:])
    return marks


def gen_result(stdout: bytes, returncode: int, timed_out: bool) -> dict[str, Any]:
    """Interpretation of one container run (same rules as the frozen P1 `run_gen`)."""
    marks = parse_markers(stdout)
    fallback: dict[str, Any] = ({"status": "HARNESS_TIMEOUT", "no_retry": True} if timed_out
                                else {"status": "NO_RESULT_LINE", "exit_code": returncode})
    result = dict(marks.get("P2GEN_RESULT") or marks.get("P2GEN_COMPLETION") or fallback)
    # conservative: a harness timeout counts as a sent request (attempt consumed, no retry)
    result["request_sent"] = "P2GEN_SENT" in marks or timed_out
    return result


def gen_request(mode: str, task: Mapping[str, Any], arm: str, prompt: str,
                route: Mapping[str, Any]) -> dict[str, Any]:
    p1 = H.p1()
    return {"mode": mode, "instance_id": task["instance_id"], "prompt": prompt,
            "prompt_identity": task["identity"][arm], "common_identity": task["common_identity"],
            "seed": task["seed"], "model": p1.MODEL, "model_digest": p1.MODEL_DIGEST,
            "host": p1.OLLAMA_HOST, "timeout": p1.GEN_TIMEOUT_S,
            "expected_module_sha256": route["module_sha256"]}


def no_retry(res: Mapping[str, Any]) -> bool:
    """§14 / OD-8: never retry after a timeout or an out-of-memory failure."""
    err = str(res.get("error", "")).lower()
    return bool(res.get("error_is_timeout")) or res.get("status") == "HARNESS_TIMEOUT" or \
        "memory" in err


def ps_models(ps_result: Mapping[str, Any]) -> list[Any]:
    return list((ps_result.get("ps") or {}).get("models", []))


def context_state(gen: Mapping[str, Any]) -> str:
    """CONFIRMED | MISMATCH (a §17 stop) | NOT_CONFIRMED (flag only)."""
    model = H.p1().MODEL
    loaded = [m for m in (gen.get("ps_after") or {}).get("models", [])
              if model in (m.get("name"), m.get("model"))]
    if not loaded or loaded[0].get("context_length") is None:
        return "NOT_CONFIRMED"
    return "CONFIRMED" if loaded[0]["context_length"] == H.p1().NUM_CTX else "MISMATCH"


def x_retry_allowed(det: Mapping[str, Any]) -> bool:
    """§14: one fresh-container retry on INFRA_ERROR before the gate or BASELINE_UNHEALTHY;
    never after RESOURCE_KILLED or a timeout."""
    if det["classification"] != "INFRA_ERROR" or det["reason"] == "RESOURCE_KILLED":
        return False
    pre_gate = not isinstance(H.p1().patch_applies(dict(det)), bool)
    return pre_gate or str(det["reason"]).startswith("BASELINE_")


def l3_l4(arm: str, x: Mapping[str, Any], cand_stdout: str, patch: str,
          protected: Sequence[str]) -> dict[str, Any]:
    """§15 layers L3 (same gate) and L4 (verification, only if L3 = GATE_PASS)."""
    p1 = H.p1()
    det = x["deterministic"]
    g = p1.patch_applies(det)
    touched = bool(p1.touched_paths(patch) & set(protected)) or \
        bool((det.get("candidate") or {}).get("removed"))
    if g is True:
        return {"L3": "GATE_PASS", "L4": p1.x_code(det, cand_stdout, touched),
                "test_integrity": touched}
    if g is False:
        l3 = p1.x_code(det, cand_stdout, touched) if arm == "U" else "S_SYNTH_INTEGRITY"
        return {"L3": l3, "L4": None, "test_integrity": touched}
    return {"L3": "PRE_GATE_INFRA", "L4": None, "test_integrity": touched}


# ---- operations boundary ----------------------------------------------------------------------
class BOps(Protocol):
    def free_bytes(self) -> int: ...
    def pull(self, ref: str) -> bool: ...
    def inspect(self, ref: str) -> tuple[list[str], str, str] | None: ...
    def remove(self, ref: str) -> bool: ...
    def free_ram(self) -> int: ...
    def ollama_stop(self) -> dict[str, Any]: ...
    def generate(self, image_id: str, request: dict[str, Any], *, network: bool, name: str,
                 timeout: float) -> tuple[bytes, bytes, dict[str, Any]]: ...
    def read_base(self, ref: str, base: str, paths: Sequence[str]) -> dict[str, E.BaseFile]: ...
    def synthesize(self, ref: str, edited: Mapping[str, E.BaseFile]) -> str: ...
    def gate(self, spec: dict[str, Any], patch: str, run_dir: Path, timeout: float, arm: str
             ) -> dict[str, Any]: ...
    def verifier_image_id(self) -> str: ...
    def velith_pins(self) -> dict[str, Any]: ...


# ---- inputs from Phase A ----------------------------------------------------------------------
def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def phase_a_slots(root: Path = EVIDENCE) -> dict[str, str]:
    log_path = root / "_lottery" / "admission_log.json"
    if not log_path.exists():
        raise PhaseBStop("Phase A has not completed (no admission_log.json)")
    log = load_json(log_path)
    if log["status"] != "OK":
        raise PhaseBStop(f"Phase A status {log['status']} (n={log['n_admitted']}): P2-D, no "
                         "Phase B")
    return dict(log["slots"])


def slot_inputs(slot: str, iid: str, root: Path = EVIDENCE) -> dict[str, Any]:
    """One admitted slot, cross-checked: decision, prompts vs identities, common prefix, seed."""
    d = root / slot
    rec = load_json(d / "record.json")
    if rec["instance_id"] != iid or rec.get("admitted") is not True or \
            not H.admission_decision(rec["steps"]):
        raise PhaseBStop(f"{slot}: record is not an admitted {iid}")
    sp = rec["stage_p"]
    common = (d / "P" / "common.txt").read_bytes()
    prompts = {arm: (d / "P" / f"prompt_{arm}.txt").read_bytes() for arm in ARMS}
    ident = {"U": sp["identity_u"], "S": sp["identity_s"]}
    if H.sha256_bytes(common) != sp["common_identity"] or \
            any(H.sha256_bytes(prompts[a]) != ident[a] for a in ARMS) or \
            not all(prompts[a].startswith(common) for a in ARMS) or \
            int(H.p1().derive_seed(sp["common_identity"])) != sp["seed"]:
        raise PhaseBStop(f"{slot}: Stage-P prompts/identities/seed are inconsistent")
    spec_bytes = (d / "A" / "spec.json").read_bytes()
    spec = json.loads(spec_bytes)
    if spec["instance_id"] != iid or spec["digest"] != rec["digest"]:
        raise PhaseBStop(f"{slot}: spec.json does not match the admission record")
    return {"rec": rec, "spec": spec, "spec_sha256": H.sha256_bytes(spec_bytes),
            "prompts": {a: prompts[a].decode("utf-8") for a in ARMS}, "identity": ident}


# ---- FG-5 gencheck ----------------------------------------------------------------------------
def gencheck(ops: BOps, root: Path = EVIDENCE, out: Path = GENCHECK) -> dict[str, Any]:
    if (out / "gencheck.json").exists():
        raise PhaseBStop("gencheck.json exists (FG-5 evidence is written once)")
    slots = phase_a_slots(root)
    pins, img = ops.velith_pins(), ops.verifier_image_id()
    route = {"module_sha256": pins["module_sha256"]}
    checks: dict[str, dict[str, Any]] = {}
    for slot, iid in slots.items():
        si = slot_inputs(slot, iid, root)
        sp = si["rec"]["stage_p"]
        task = {"instance_id": iid, "identity": si["identity"],
                "common_identity": sp["common_identity"], "seed": sp["seed"]}
        for arm in ARMS:
            stdout, stderr, res = ops.generate(img, gen_request("check", task, arm,
                                                                si["prompts"][arm], route),
                                               network=False, name=f"p2gen-check-{slot}-{arm}",
                                               timeout=600)
            A.write(out / slot / arm / "result.json", res)
            (out / slot / arm / "raw_stdout.txt").write_bytes(stdout)
            (out / slot / arm / "raw_stderr.txt").write_bytes(stderr)
            checks[f"{slot}/{arm}"] = {"status": res.get("status"),
                                       "modules_match": res.get("module_sha256") ==
                                       pins["module_sha256"]}
    ok = bool(checks) and all(c["status"] == "CHECK_OK" and c["modules_match"]
                              for c in checks.values())
    record = {"utc": H.p1().utc(), "fg": "FG-5", "verdict": "PASS" if ok else "FAIL",
              "image": H.p1().VERIFIER_IMAGE, "image_id": img, "network": "none",
              "pins": pins, "checks": checks, "code_sha256": code_shas()}
    A.write(out / "gencheck.json", record)
    H.p1().manifest(out)
    return record


# ---- FG-6 freeze ------------------------------------------------------------------------------
def build_freeze(root: Path = EVIDENCE, gencheck_dir: Path = GENCHECK,
                 registry_path: Path = REGISTRY) -> tuple[dict[str, Any], dict[str, Any]]:
    """PILOT_SET and the appended registry, built in memory (written by `freeze`)."""
    gen = load_json(gencheck_dir / "gencheck.json")
    shas = code_shas()
    if gen["verdict"] != "PASS":
        raise PhaseBStop("FG-5 gencheck is not PASS")
    if gen["code_sha256"] != shas:
        raise PhaseBStop("harness code changed since gencheck; rerun FG-5")
    p1 = H.p1()
    log_path = root / "_lottery" / "admission_log.json"
    slots = phase_a_slots(root)
    tasks = []
    for slot, iid in slots.items():
        si = slot_inputs(slot, iid, root)
        rec, spec, sp = si["rec"], si["spec"], si["rec"]["stage_p"]
        sc = rec["self_check_diagnostic"]
        d = root / slot
        tasks.append({
            "slot": slot, "instance_id": iid, "repo": rec["repo"], "rank": rec["rank"],
            "base_commit": spec["base_commit"], "spec": f"p2/evidence/{slot}/A/spec.json",
            "spec_sha256": si["spec_sha256"], "image": rec["image"], "digest": rec["digest"],
            "ref": rec["ref"], "image_id": rec["image_id"],
            "compressed_bytes": rec["compressed_bytes"], "platform": spec["platform"],
            "protected_paths": spec["protected_paths"], "gold_paths": sp["gold_paths"],
            "common_identity": sp["common_identity"], "identity": si["identity"],
            "seed": sp["seed"], "predicted_prompt_eval_count": sp["tokens"],
            "arm_order": list(arm_order(iid)),
            "case_a_candidate_seconds": rec["case_a_candidate_seconds"],
            "stage_x_timeout_s": rec["stage_x_timeout_s"],
            "self_check_diagnostic": {k: sc[k] for k in (
                "parse_code", "resolution_code", "gate", "harness_integrity_alarm",
                "no_newline_marker", "synthesized_diff_sha256")},
            "record_sha256": H.sha256_bytes((d / "record.json").read_bytes()),
            "prompt_sha256": {a: H.sha256_bytes((d / "P" / f"prompt_{a}.txt").read_bytes())
                              for a in ARMS},
            "leakage_audit_sha256": H.sha256_bytes((d / "P" / "leakage_audit.json").read_bytes()),
        })
        if p1.derive_seed(sp["common_identity"]) != sp["seed"] or \
                rec["stage_x_timeout_s"] != A.derive_timeout(rec["case_a_candidate_seconds"]):
            raise PhaseBStop(f"{slot}: seed or Stage-X timeout differs from the frozen rule")
        if sc["harness_integrity_alarm"]:
            raise PhaseBStop(f"{slot}: A-1 alarm recorded; freeze refused pending RD review")
    reg = load_json(registry_path)
    if reg["p2_appended"]:
        raise PhaseBStop("P2 registry already appended (append-once rule)")
    rejected = []
    adm = root / "_admission"
    for d in sorted(adm.iterdir()) if adm.exists() else []:
        f = d / "record.json"
        if ".interrupted-" in d.name or not f.exists():
            continue
        r = load_json(f)
        if r.get("admitted") is False:
            rejected.append({"instance_id": r["instance_id"], "status":
                             "rejected_at_admission (exposed)", "reason": r["reason"],
                             "rank": r["rank"], "evidence": f"p2/evidence/_admission/{d.name}/"})
    appended = [{"instance_id": t["instance_id"], "status": "admitted", "slot": t["slot"],
                 "common_identity": t["common_identity"]} for t in tasks] + rejected
    new_reg = {**reg, "p2_appended": appended}
    reg_bytes = A.dump(new_reg)
    pilot = {
        "pilot": "M2-PV-P2", "dataset": p1.DATASET, "dataset_revision": reg["dataset_revision"],
        "spec_sha256": H.SPEC_SHA256, "n": len(tasks), "task_order": list(slots),
        "tasks": tasks,
        "model": {"name": p1.MODEL, "manifest_digest": p1.MODEL_DIGEST, "num_ctx": p1.NUM_CTX,
                  "num_predict": p1.NUM_PREDICT, "stop": ["\nUser:", "\nAssistant:"],
                  "temperature": 0.0, "client_timeout_s": p1.GEN_TIMEOUT_S},
        "budget": {"b_prompt": A.B_PROMPT},
        "generation_route": {"image": p1.VERIFIER_IMAGE, "image_id": gen["image_id"],
                             "velith_commit": gen["pins"]["velith_commit"],
                             "module_sha256": gen["pins"]["module_sha256"],
                             "host": p1.OLLAMA_HOST},
        "code_sha256": shas, "p1_harness_sha256": H.P1_HARNESS_SHA256,
        "fg3_sha256": dict(A.FG3_SHA256),
        "admission_log_sha256": H.sha256_bytes(log_path.read_bytes()),
        "gencheck_sha256": H.sha256_bytes((gencheck_dir / "gencheck.json").read_bytes()),
        "registry_sha256": H.sha256_bytes(reg_bytes),
    }
    return pilot, new_reg


def freeze(root: Path = EVIDENCE, gencheck_dir: Path = GENCHECK, registry_path: Path = REGISTRY,
           pilot_path: Path = PILOT_SET) -> dict[str, str]:
    if pilot_path.exists():
        raise PhaseBStop("PILOT_SET.json exists (written once)")
    pilot, new_reg = build_freeze(root, gencheck_dir, registry_path)
    pilot["frozen_utc"] = H.p1().utc()
    registry_path.write_bytes(A.dump(new_reg))
    pilot_path.write_bytes(A.dump(pilot))
    return {"PILOT_SET.json": H.sha256_bytes(pilot_path.read_bytes()),
            "P2_EXCLUSION_REGISTRY.json": H.sha256_bytes(registry_path.read_bytes())}


# ---- Phase B: one task ------------------------------------------------------------------------
def check_frozen(pilot_path: Path, pilot_sha: str, registry_path: Path) -> dict[str, Any]:
    raw = pilot_path.read_bytes()
    if H.sha256_bytes(raw) != pilot_sha:
        raise PhaseBStop("PILOT_SET.json SHA differs from the reviewed FG-8 value")
    pilot = json.loads(raw)
    if pilot["code_sha256"] != code_shas():
        raise PhaseBStop("harness/parser/spec SHA changed after freeze (§17)")
    if H.sha256_bytes(registry_path.read_bytes()) != pilot["registry_sha256"]:
        raise PhaseBStop("P2 registry changed after freeze (§17)")
    return dict(pilot)


def ps_check(ops: BOps, img: str, request: dict[str, Any], name: str) -> dict[str, Any]:
    _o, _e, ps = ops.generate(img, {**request, "mode": "ps"}, network=True, name=name,
                              timeout=300)
    return ps


def unload(ops: BOps, img: str, request: dict[str, Any], name: str) -> dict[str, Any]:
    """`ollama stop`, then /api/ps must list no model (§13)."""
    stop = ops.ollama_stop()
    ps = ps_check(ops, img, request, name)
    if ps.get("status") != "PS_OK" or ps_models(ps):
        raise PhaseBStop(f"/api/ps not empty after ollama stop: {ps.get('status')} "
                         f"{ps_models(ps)} (resumable)")
    return {"ollama_stop": stop, "ps": ps}


def generate_arm(ops: BOps, task: Mapping[str, Any], arm: str, prompt: str,
                 route: Mapping[str, Any], gdir: Path) -> dict[str, Any]:
    """One generation per (task, arm); resumable; never regenerates once a completion exists."""
    p1 = H.p1()
    img = route["image_id"]
    request = gen_request("generate", task, arm, prompt, route)
    attempts = sorted(gdir.glob("attempt-*/result.json"))
    consumed = [load_json(f) for f in attempts]
    gen = next((r for r in consumed if r.get("status") == "GENERATED"), None)
    while gen is None:
        if consumed and (len(consumed) >= p1.MAX_GEN_ATTEMPTS or consumed[-1].get("no_retry")):
            gen = consumed[-1]
            break
        pre = unload(ops, img, request, f"p2gen-ps-pre-{task['slot']}-{arm}-{int(time.time())}")
        ram = ops.free_ram()
        if ram < p1.MIN_FREE_RAM:
            A.write(gdir / f"preflight-fail-{p1.utc()}.json", {"free_ram": ram, "pre": pre})
            raise PhaseBStop(f"free RAM {ram} < {p1.MIN_FREE_RAM} (no attempt consumed)")
        n = len(consumed) + 1
        adir = gdir / f"attempt-{n}"
        started = p1.utc()
        stdout, stderr, res = ops.generate(img, request, network=True,
                                           name=f"p2gen-{task['slot']}-{arm}-{n}-"
                                                f"{int(time.time())}",
                                           timeout=p1.GEN_TIMEOUT_S + 600)
        adir.mkdir(parents=True, exist_ok=True)
        (adir / "raw_stdout.txt").write_bytes(stdout)  # raw first, before interpretation
        (adir / "raw_stderr.txt").write_bytes(stderr)
        res.update({"attempt": n, "arm": arm, "started_utc": started, "ended_utc": p1.utc(),
                    "free_ram_before": ram, "pre_unload": pre})
        if not res.get("request_sent"):
            A.write(gdir / f"preflight-fail-{started}.json", res)
            raise PhaseBStop(f"{arm}: pre-request failure {res.get('status')} (rerunnable)")
        if res.get("status") == "GENERATED":
            (adir / "completion.txt").write_bytes(res["completion_text"].encode("utf-8"))
            (adir / "patch.diff").write_bytes((res["patch"] or "").encode("utf-8"))
            gen = res
        else:
            res["no_retry"] = no_retry(res)
        A.write(adir / "result.json", res)
        consumed.append(res)
    post_path = gdir / "post_unload.json"
    if not post_path.exists():
        post = unload(ops, img, request, f"p2gen-ps-post-{task['slot']}-{arm}-{int(time.time())}")
        A.write(post_path, post)
    return {**gen, "gen_attempts": len(consumed)}


def generation_record(gen: Mapping[str, Any], predicted: int) -> dict[str, Any]:
    ok = gen.get("status") == "GENERATED"
    flags = []
    ctx = context_state(gen) if ok else None
    if ok and gen["prompt_tokens"] != predicted:
        flags.append("TOKEN_COUNT_MISMATCH")
    if ok and gen["completion_tokens"] == H.p1().NUM_PREDICT:
        flags.append("GEN_TRUNCATED")
    if ctx == "NOT_CONFIRMED":
        flags.append("CONTEXT_LENGTH_NOT_CONFIRMED")
    return {"gen_ok": ok, "status": gen.get("status"), "flags": flags, "context": ctx,
            "attempts": gen.get("gen_attempts"), "prompt_tokens": gen.get("prompt_tokens"),
            "predicted_prompt_tokens": predicted,
            "completion_tokens": gen.get("completion_tokens"),
            "latency_seconds": gen.get("latency_seconds"),
            "completion_sha256": H.sha256_bytes(gen["completion_text"].encode("utf-8"))
            if ok else None}


def block_paths(parsed: E.ParseResult) -> list[str]:
    return sorted({b.path for b in parsed.blocks})


def resolve_s(ops: BOps, ref: str, base_commit: str, completion: str, sdir: Path
              ) -> tuple[E.ParseResult, E.Resolution, str | None]:
    """§6: region → grammar → exact resolution on base_commit content → synthesis (G-7)."""
    parsed = E.parse(completion)
    sdir.mkdir(parents=True, exist_ok=True)
    (sdir / "region.txt").write_bytes(parsed.region.encode("utf-8"))
    A.write(sdir / "blocks.json", {"parse_code": parsed.code, "error": parsed.error,
                                   "blocks": [{"index": b.index, "path": b.path,
                                               "search_sha256": H.sha256_bytes(b.search),
                                               "replace_sha256": H.sha256_bytes(b.replace)}
                                              for b in parsed.blocks]})
    if parsed.code != E.OK:
        res = E.Resolution(parsed.code)
    else:
        base = ops.read_base(ref, base_commit, block_paths(parsed))
        res = E.resolve(parsed.blocks, base)
    diff = ops.synthesize(ref, res.edited) if res.code == E.OK else None
    A.write(sdir / "resolution.json", {"code": res.code, "statuses": res.statuses,
                                       "edited_paths": sorted(res.edited),
                                       "synthesized_diff_sha256": None if diff is None
                                       else H.sha256_bytes(diff.encode("utf-8"))})
    if diff is not None:
        (sdir / "synthesized.diff").write_bytes(diff.encode("utf-8"))
    return parsed, res, diff


def stage_x(ops: BOps, task: Mapping[str, Any], spec: dict[str, Any], patch: str, arm: str,
            root: Path) -> tuple[dict[str, Any], str, int]:
    """Same gate for both arms; resumable; at most one fresh-container retry (§14)."""
    x: dict[str, Any] = {}
    cand_stdout, n = "", 0
    for n in range(1, H.p1().MAX_X_ATTEMPTS + 1):
        xdir = root / f"X-{arm}-{n}"
        evf = xdir / "evidence.json"
        x = load_json(evf) if evf.exists() else ops.gate(spec, patch, xdir,
                                                         float(task["stage_x_timeout_s"]), arm)
        cs = xdir / "candidate" / "stdout.txt"
        cand_stdout = cs.read_text(encoding="utf-8") if cs.exists() else ""
        if not x_retry_allowed(x["deterministic"]):
            break
    return x, cand_stdout, n


def run_task(ops: BOps, pilot: Mapping[str, Any], task: Mapping[str, Any], root: Path,
             pilot_sha: str) -> dict[str, Any]:
    """§13 step 3 for one slot. Returns the episode (already-written episodes are final)."""
    d = root / task["slot"]
    ep_path = d / "episode.json"
    if ep_path.exists():
        return dict(load_json(ep_path))
    spec_path = d / "A" / "spec.json"
    if H.sha256_bytes(spec_path.read_bytes()) != task["spec_sha256"]:
        raise PhaseBStop(f"{task['slot']}: spec changed after freeze")
    spec = load_json(spec_path)
    prompts = {a: (d / "P" / f"prompt_{a}.txt").read_bytes() for a in ARMS}
    if any(H.sha256_bytes(prompts[a]) != task["identity"][a] for a in ARMS):
        raise PhaseBStop(f"{task['slot']}: prompt bytes differ from the frozen identities")
    route = pilot["generation_route"]
    if ops.verifier_image_id() != route["image_id"]:
        raise PhaseBStop("velith-verifier:m0 image ID changed after freeze")
    ref = task["ref"]
    episode: dict[str, Any] = {"slot": task["slot"], "instance_id": task["instance_id"],
                               "arm_order": task["arm_order"], "seed": task["seed"],
                               "common_identity": task["common_identity"],
                               "pilot_set_sha256": pilot_sha, "d7": {}, "arms": {}}
    need, free = A.storage_need(int(task["compressed_bytes"])), ops.free_bytes()
    if free < need:
        raise PhaseBStop(f"storage gate: free {free} < need {need} before {task['slot']}")
    pulled = ops.pull(ref) or ops.pull(ref)
    stop: Exception | None = None
    try:
        insp = ops.inspect(ref) if pulled else None
        aborted = insp is None or ref not in insp[0] or insp[1] != A.PLATFORM or \
            insp[2] != task["image_id"]
        episode["d7"] = {"pulled": pulled, "inspect": insp, "aborted": aborted}
        gens: dict[str, dict[str, Any]] = {}
        if not aborted:
            for arm in task["arm_order"]:
                gens[arm] = generate_arm(ops, task, arm, prompts[arm].decode("utf-8"), route,
                                         d / f"G-{arm}")
                if context_state(gens[arm]) == "MISMATCH" and gens[arm]["status"] == "GENERATED":
                    raise PhaseBStop(f"{task['slot']}/{arm}: context_length != "
                                     f"{H.p1().NUM_CTX} (§17)")
        arms = episode["arms"]
        for arm in ARMS:
            gen = gens.get(arm, {"status": "D7_ABORT"})
            arms[arm] = {"generation": generation_record(gen, task[
                "predicted_prompt_eval_count"][arm]) if not aborted else None}
        # S resolution and synthesis (§13 step 6), then X(U), X(S) (step 7)
        res: E.Resolution | None = None
        s_diff: str | None = None
        if not aborted and gens["S"].get("status") == "GENERATED":
            parsed, res, s_diff = resolve_s(ops, ref, task["base_commit"],
                                            gens["S"]["completion_text"], d / "S")
            arms["S"]["L1"] = E.NO_OUTPUT if parsed.code == E.NO_OUTPUT else "OUTPUT"
            arms["S"]["L2"] = res.code
        xs: dict[str, dict[str, Any] | None] = {"U": None, "S": None}
        patches = {"U": gens["U"].get("patch") if not aborted and gens["U"].get("has_patch")
                   and gens["U"].get("status") == "GENERATED" else None, "S": s_diff}
        if not aborted and gens["U"].get("status") == "GENERATED":
            arms["U"]["L1"] = "OUTPUT" if gens["U"].get("has_patch") else E.NO_OUTPUT
        for arm in ARMS:
            patch = patches[arm]
            if patch is None:
                continue
            x, cand_stdout, n = stage_x(ops, task, spec, patch, arm, d)
            xs[arm] = x
            layers = l3_l4(arm, x, cand_stdout, patch, task["protected_paths"])
            arms[arm].update(layers, x_attempts=n,
                             patch_sha256=H.sha256_bytes(patch.encode("utf-8")),
                             classification=x["deterministic"]["classification"],
                             reason=x["deterministic"]["reason"])
            if layers["L3"] == "S_SYNTH_INTEGRITY":
                stop = H.HarnessStop(f"{task['slot']}: S_SYNTH_INTEGRITY (gate rejected a "
                                     "harness-synthesized diff) — stop and report (§17)")
        gen_ok = {a: (not aborted) and gens[a].get("status") == "GENERATED" for a in ARMS}
        u = H.u_applies(gen_ok["U"], gen_ok["U"] and bool(gens["U"].get("has_patch")), xs["U"],
                        aborted)
        s = H.s_applies(gen_ok["S"], res, xs["S"], aborted)
        arms["U"].update(applies=u, verified_pass=H.verified_pass(u, xs["U"]))
        arms["S"].update(applies=s, verified_pass=H.verified_pass(s, xs["S"]))
        episode["infra_unresolved"] = aborted or H.NA in (u, s)
        episode["na_reasons"] = {a: ("D7_ABORT" if aborted else "GEN_INFRA" if not gen_ok[a]
                                     else "PRE_GATE_INFRA")
                                 for a, v in (("U", u), ("S", s)) if v == H.NA}
    finally:
        if pulled:
            removed = ops.remove(ref)
            episode["image_removed"] = removed
            if not removed and stop is None:
                stop = PhaseBStop(f"image delete failed for {ref}")
    if stop is not None:
        A.write(d / "stop.json", {"stop": str(stop), "episode_partial": episode})
        raise stop
    episode["utc"] = H.p1().utc()
    A.write(ep_path, episode)
    H.p1().manifest(d)
    return dict(load_json(ep_path))  # the persisted form is the only form returned


def run_phase_b(ops: BOps, pilot: dict[str, Any], pilot_sha: str, root: Path = EVIDENCE
                ) -> list[dict[str, Any]]:
    episodes: list[dict[str, Any]] = []
    for task in pilot["tasks"]:
        if sum(bool(e.get("infra_unresolved")) for e in episodes) >= H.INFRA_STOP:
            raise PhaseBStop(f"unresolved infrastructure failures on >= {H.INFRA_STOP} tasks "
                             "(§17 → P2-D)")
        episodes.append(run_task(ops, pilot, task, root, pilot_sha))
    return episodes


# ---- report (§8) ------------------------------------------------------------------------------
def report(pilot: Mapping[str, Any], root: Path = EVIDENCE, out_dir: Path = REPORT
           ) -> dict[str, Any]:
    eps = []
    for t in pilot["tasks"]:
        f = root / t["slot"] / "episode.json"
        if not f.exists():
            raise PhaseBStop(f"{t['slot']}: no episode (Phase B incomplete)")
        eps.append(load_json(f))
    pairs = [(e["arms"]["U"]["applies"], e["arms"]["S"]["applies"]) for e in eps]
    table = H.paired_table(pairs)
    infra = sum(1 for e in eps if e["infra_unresolved"])
    p = H.sign_test_p(table["s_only"], table["u_only"])
    valid = [e for e in eps if H.NA not in (e["arms"]["U"]["applies"], e["arms"]["S"]["applies"])]
    out = {
        "n": len(eps), "table": table, "infra_unresolved_tasks": infra,
        "sign_test_p_one_sided": None if p is None else str(p),
        "sign_test_p_float": None if p is None else float(p),
        "conclusion": H.conclusion(table, infra),
        "applicability": {"k_S": table["k_s"], "k_U": table["k_u"], "n_v": table["n_v"]},
        "verified_pass_secondary": {a: sum(1 for e in valid if e["arms"][a]["verified_pass"]
                                           is True) for a in ARMS},
        "na_tasks": {e["slot"]: e["na_reasons"] for e in eps if e["na_reasons"]},
        "per_task": [{"slot": e["slot"], "instance_id": e["instance_id"],
                      **{a: {k: e["arms"][a].get(k) for k in
                             ("applies", "verified_pass", "L1", "L2", "L3", "L4")}
                         | {"flags": (e["arms"][a].get("generation") or {}).get("flags")}
                         for a in ARMS}} for e in eps],
    }
    A.write(out_dir / "report.json", out)
    return out


# ---- real operations (never called by the tests) ----------------------------------------------
class DockerBOps(A.DockerOps):  # pragma: no cover
    def free_ram(self) -> int:
        return int(H.p1().free_ram())

    def ollama_stop(self) -> dict[str, Any]:
        return dict(H.p1().ollama_stop())

    def verifier_image_id(self) -> str:
        return str(H.p1().image_id(H.p1().VERIFIER_IMAGE))

    def velith_pins(self) -> dict[str, Any]:
        return dict(H.p1().velith_pins())

    def generate(self, image_id: str, request: dict[str, Any], *, network: bool, name: str,
                 timeout: float) -> tuple[bytes, bytes, dict[str, Any]]:
        """P1 R6 route (frozen `run_gen` flags) with the P2 container script."""
        args = ["docker", "run", "--rm", "-i", "--name", name, "--read-only", "--cap-drop",
                "ALL", "--security-opt", "no-new-privileges"]
        args += (["--add-host", "host.docker.internal:host-gateway"] if network
                 else ["--network", "none"])
        args += ["--entrypoint", "python", image_id, "-c", GEN_SCRIPT.read_text(encoding="utf-8")]
        try:
            p = subprocess.run(args, input=json.dumps(request).encode("utf-8"),
                               capture_output=True, timeout=timeout, check=False)
            return p.stdout, p.stderr, gen_result(p.stdout, p.returncode, False)
        except subprocess.TimeoutExpired as exc:
            subprocess.run(["docker", "rm", "-f", name], capture_output=True, check=False)
            out = exc.stdout if isinstance(exc.stdout, bytes) else b""
            err = exc.stderr if isinstance(exc.stderr, bytes) else b""
            return out, err, gen_result(out, -9, True)

    def read_base(self, ref: str, base: str, paths: Sequence[str]) -> dict[str, E.BaseFile]:
        """Missing-path tolerant: absent paths are omitted (→ S_PATH_INVALID); non-blob entries
        keep their git mode with empty content (→ S_PATH_INVALID). Literal pathspecs only."""
        p1 = H.p1()
        listed = self._run(["docker", "run", "--rm", "--network", "none", "--entrypoint", "bash",
                            ref, "-c", f"cd {A.REPO_DIR} && git --literal-pathspecs ls-tree -l -z "
                            f"{shlex.quote(base)} -- " + " ".join(shlex.quote(p) for p in paths)])
        if listed.returncode != 0:
            raise H.HarnessStop(f"ls-tree failed: {listed.stderr.decode(errors='replace')}")
        entries = {e[3]: e for e in p1.parse_ls_tree(listed.stdout) if e[3] in set(paths)}
        blobs_wanted = [e for e in entries.values() if e[1] == "blob"]
        blobs: dict[str, bytes] = {}
        if blobs_wanted:
            blobs = p1.parse_cat_file_batch(self._run(
                ["docker", "run", "--rm", "-i", "--network", "none", "--entrypoint", "bash", ref,
                 "-c", f"cd {A.REPO_DIR} && git cat-file --batch"],
                stdin=b"".join(e[2].encode() + b"\n" for e in blobs_wanted)).stdout)
        return {p: E.BaseFile(e[0], blobs.get(e[2], b"") if e[1] == "blob" else b"")
                for p, e in entries.items()}

    def gate(self, spec: dict[str, Any], patch: str, run_dir: Path, timeout: float,
             arm: str = "S") -> dict[str, Any]:
        return H.stage_x_gate(spec, patch, run_dir, timeout, arm)


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    ap = argparse.ArgumentParser(prog="p2_phaseb")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("gencheck")
    sub.add_parser("freeze")
    r = sub.add_parser("run")
    r.add_argument("--pilot-sha", required=True)
    sub.add_parser("report")
    args = ap.parse_args(argv)
    try:
        H.check_spec()
        if args.cmd == "gencheck":
            rec = gencheck(DockerBOps())
            print(json.dumps({"verdict": rec["verdict"], "image_id": rec["image_id"],
                              "velith_commit": rec["pins"]["velith_commit"],
                              "checks": rec["checks"]}, indent=2))
            return 0 if rec["verdict"] == "PASS" else 1
        if args.cmd == "freeze":
            print(json.dumps(freeze(), indent=2))
            return 0
        if args.cmd == "run":
            pilot = check_frozen(PILOT_SET, args.pilot_sha, REGISTRY)
            eps = run_phase_b(DockerBOps(), pilot, args.pilot_sha)
            print(json.dumps([{"slot": e["slot"], "U": e["arms"]["U"]["applies"],
                               "S": e["arms"]["S"]["applies"]} for e in eps], indent=2))
            return 0
        pilot = load_json(PILOT_SET)
        print(json.dumps({k: v for k, v in report(pilot).items() if k != "per_task"}, indent=2))
        return 0
    except (PhaseBStop, H.HarnessStop, A.AdmissionStop) as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
