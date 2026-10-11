"""Deterministic tests for the P2 Phase-B machinery (FG-5, FG-6, Phase B, report). Synthetic only.

A fake `BOps` stands in for Docker, Ollama, the probe gate and the task image. There is no image
pull, no container, no model call and no network. The real P2 registry is only read.

Run:  PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider \
          p2/harness/test_p2_phaseb.py
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import types
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import p2_edits as E  # noqa: E402
import p2_harness as H  # noqa: E402
import p2_phaseb as B  # noqa: E402

_DIFF = re.compile(r"^diff --git a/.* b/(.*)$", re.MULTILINE)
BASE_SRC = b"def f():\n    return 1\n"
GOLD = ("diff --git a/pkg/m.py b/pkg/m.py\n--- a/pkg/m.py\n+++ b/pkg/m.py\n"
        "@@ -1,2 +1,2 @@\n def f():\n-    return 1\n+    return 10\n")
U_OK = GOLD
S_OK = "<<<<<<< SEARCH pkg/m.py\n    return 1\n=======\n    return 10\n>>>>>>> REPLACE\n"
SYNTH = "diff --git a/pkg/m.py b/pkg/m.py\n--- a/pkg/m.py\n+++ b/pkg/m.py\n+synth\n"
MODS = {"velith/agent/proposer.py": "a" * 64, "velith/llm/client.py": "b" * 64,
        "velith/task.py": "c" * 64, "velith/batch/provenance.py": "d" * 64}
VERIFIER = "sha256:" + "e" * 64


@pytest.fixture(autouse=True)
def stub_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = types.ModuleType("probe")
    stub.patch_files = lambda patch: sorted(set(_DIFF.findall(patch)))  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "probe", stub)


def iid_of(i: int) -> str:
    return f"org__repo-{1000 + i}"


# ---- synthetic Phase-A evidence ---------------------------------------------------------------
def make_root(tmp: Path, n: int) -> Path:
    root = tmp / "evidence"
    slots = {}
    for i in range(1, n + 1):
        slot, iid = f"P2-{i:02d}", iid_of(i)
        slots[slot] = iid
        d = root / slot
        pr = H.build_prompts("org/repo", f"problem {i}", [("pkg/m.py", BASE_SRC.decode())])
        (d / "P").mkdir(parents=True)
        (d / "A").mkdir(parents=True)
        (d / "P" / "common.txt").write_bytes(pr.common.encode())
        (d / "P" / "prompt_U.txt").write_bytes(pr.prompt_u.encode())
        (d / "P" / "prompt_S.txt").write_bytes(pr.prompt_s.encode())
        (d / "P" / "leakage_audit.json").write_text("{}")
        digest = "sha256:" + hashlib.sha256(iid.encode()).hexdigest()
        image = "swebench/sweb.eval.x86_64." + iid
        spec = {"instance_id": iid, "digest": digest, "base_commit": "f" * 40,
                "platform": "linux/amd64", "protected_paths": ["pkg/tests/test_m.py"],
                "repo": "org/repo", "patch": GOLD, "image": image}
        (d / "A" / "spec.json").write_text(json.dumps(spec))
        rec = {"rank": i, "instance_id": iid, "repo": "org/repo", "image": image,
               "digest": digest, "ref": f"{image}@{digest}", "image_id": "sha256:img-" + iid,
               "compressed_bytes": 1000, "admitted": True,
               "steps": dict.fromkeys(H.ADMISSION_STEPS, True), "reason": None,
               "case_a_candidate_seconds": 120.0, "stage_x_timeout_s": 900.0,
               "stage_p": {"common_identity": pr.common_identity, "identity_u": pr.identity_u,
                           "identity_s": pr.identity_s, "seed": pr.seed,
                           "tokens": {"U": 500, "S": 489}, "gold_paths": ["pkg/m.py"]},
               "self_check_diagnostic": {"parse_code": "OK", "resolution_code": "OK",
                                         "gate": True, "harness_integrity_alarm": False,
                                         "no_newline_marker": False,
                                         "synthesized_diff_sha256": "0" * 64},
               "events": ["decision", "provenance_written", "remove"]}
        (d / "record.json").write_text(json.dumps(rec))
    rej = root / "_admission" / "01-org__repo-0999"
    rej.mkdir(parents=True)
    (rej / "record.json").write_text(json.dumps({
        "rank": 1, "instance_id": "org__repo-0999", "admitted": False,
        "reason": "F_OVER_BUDGET", "events": ["provenance_written"]}))
    (root / "_admission" / "02-org__repo-0998.interrupted-1").mkdir()
    (root / "_lottery").mkdir(parents=True)
    # small fixtures are marked OK so the machinery can run; n_min is tested in the report tests
    (root / "_lottery" / "admission_log.json").write_text(json.dumps(
        {"status": "OK", "n_admitted": n, "slots": slots}))
    return root


# ---- fake operations --------------------------------------------------------------------------
@dataclass
class Fake:
    completions: dict[tuple[str, str], str] = field(default_factory=dict)
    gen_status: dict[tuple[str, str], list[dict[str, Any]]] = field(default_factory=dict)
    gate_status: dict[tuple[str, str], list[tuple[str, str, str]]] = field(default_factory=dict)
    base: dict[str, E.BaseFile] = field(default_factory=lambda: {
        "pkg/m.py": E.BaseFile("100644", BASE_SRC)})
    image_id_override: str | None = None
    ram: int = 8 * 1024**3
    ps_loaded_after_stop: bool = False
    ctx: int | None = 16384
    prompt_tokens_delta: int = 0
    completion_tokens: int = 50
    remove_ok: bool = True
    module_sha: dict[str, str] = field(default_factory=lambda: dict(MODS))
    log: list[tuple[str, Any]] = field(default_factory=list)
    gate_calls: list[tuple[str, str]] = field(default_factory=list)

    def free_bytes(self) -> int:
        return 10**15

    def pull(self, ref: str) -> bool:
        self.log.append(("pull", ref))
        return True

    def inspect(self, ref: str) -> tuple[list[str], str, str] | None:
        iid = ref.split("x86_64.")[1].split("@")[0]
        return [ref], "linux/amd64", self.image_id_override or "sha256:img-" + iid

    def remove(self, ref: str) -> bool:
        self.log.append(("remove", ref))
        return self.remove_ok

    def free_ram(self) -> int:
        return self.ram

    def ollama_stop(self) -> dict[str, Any]:
        self.log.append(("stop", None))
        return {"rc": 0}

    def verifier_image_id(self) -> str:
        return VERIFIER

    def velith_pins(self) -> dict[str, Any]:
        return {"velith_commit": "1" * 40, "module_sha256": dict(MODS)}

    def generate(self, image_id: str, request: dict[str, Any], *, network: bool, name: str,
                 timeout: float) -> tuple[bytes, bytes, dict[str, Any]]:
        assert image_id == VERIFIER
        mode = request["mode"]
        base = {"mode": mode, "module_sha256": dict(self.module_sha)}
        # in-container assertions (as p2_gen.py does them)
        assert H.p1().derive_seed(request["common_identity"]) == request["seed"]
        assert hashlib.sha256(request["prompt"].encode()).hexdigest() == \
            request["prompt_identity"]
        if mode == "check":
            assert network is False
            self.log.append(("check", name))
            return b"", b"", {**base, "status": "CHECK_OK", "request_sent": False}
        assert network is True
        if mode == "ps":
            self.log.append(("ps", name))
            models = [{"name": H.p1().MODEL}] if self.ps_loaded_after_stop else []
            return b"", b"", {**base, "status": "PS_OK", "ps": {"models": models},
                              "request_sent": False}
        arm = "U" if request["prompt"].endswith(H.contract_u()) else "S"
        key = (request["instance_id"], arm)
        self.log.append(("generate", key))
        queued = self.gen_status.get(key)
        if queued:
            return b"raw", b"", dict(queued.pop(0))
        text = self.completions.get(key, U_OK if arm == "U" else S_OK)
        has_patch = text.startswith("diff --git")
        ps_after = {"models": [{"name": H.p1().MODEL, "context_length": self.ctx}]}
        return b"raw-out", b"raw-err", {
            **base, "status": "GENERATED", "completion_text": text,
            "patch": text if has_patch else None, "has_patch": has_patch,
            "prompt_tokens": (500 if arm == "U" else 489) + self.prompt_tokens_delta,
            "completion_tokens": self.completion_tokens, "latency_seconds": 1.0,
            "ps_after": ps_after, "request_sent": True, "seed": request["seed"]}

    def read_base(self, ref: str, base: str, paths: Sequence[str]) -> dict[str, E.BaseFile]:
        return {p: self.base[p] for p in paths if p in self.base}

    def synthesize(self, ref: str, edited: Mapping[str, E.BaseFile]) -> str:
        return SYNTH

    def gate(self, spec: dict[str, Any], patch: str, run_dir: Path, timeout: float, arm: str
             ) -> dict[str, Any]:
        self.gate_calls.append((spec["instance_id"], arm))
        q = self.gate_status.get((spec["instance_id"], arm))
        status, cls, reason = q.pop(0) if q else ("RAN", "PASSED", "ALL_REQUIRED_PASSED")
        ev = {"deterministic": {"candidate": {"status": status}, "classification": cls,
                                "reason": reason, "detail": ""}}
        run_dir.mkdir(parents=True)
        (run_dir / "evidence.json").write_text(json.dumps(ev))
        return ev


def pre_freeze_registry() -> bytes:
    """The FG-1 registry state (the real file was appended once at FG-6)."""
    reg = json.loads(B.REGISTRY.read_text())
    reg["p2_appended"] = []
    return json.dumps(reg).encode()


def frozen(tmp: Path, n: int, fake: Fake | None = None) -> tuple[Path, dict[str, Any], str, Fake]:
    root = make_root(tmp, n)
    fake = fake or Fake()
    reg, pilot_path = tmp / "registry.json", tmp / "PILOT_SET.json"
    reg.write_bytes(pre_freeze_registry())
    B.gencheck(fake, root, root / "_gencheck")
    shas = B.freeze(root, root / "_gencheck", reg, pilot_path)
    pilot = B.check_frozen(pilot_path, shas["PILOT_SET.json"], reg)
    fake.log.clear()
    return root, pilot, shas["PILOT_SET.json"], fake


# ---- pure rules -------------------------------------------------------------------------------
def test_arm_order_is_the_frozen_formula() -> None:
    orders = set()
    for i in range(40):
        iid = iid_of(i)
        even = hashlib.sha256((iid + "|velith-m2pv-p2-arm-order").encode()).digest()[0] % 2 == 0
        assert B.arm_order(iid) == (("U", "S") if even else ("S", "U"))
        orders.add(B.arm_order(iid))
    assert orders == {("U", "S"), ("S", "U")}


def test_gen_result_marker_rules() -> None:
    sent = b'P2GEN_SENT {"seed": 1}\nP2GEN_COMPLETION {"status": "GENERATED", "x": 1}\n'
    r = B.gen_result(sent, 0, False)
    assert r["status"] == "GENERATED" and r["request_sent"] is True
    r = B.gen_result(sent + b'P2GEN_RESULT {"status": "GENERATED", "x": 2}\n', 0, False)
    assert r["x"] == 2
    r = B.gen_result(b"noise\n", 3, False)
    assert r == {"status": "NO_RESULT_LINE", "exit_code": 3, "request_sent": False}
    r = B.gen_result(b"", -9, True)
    assert r["status"] == "HARNESS_TIMEOUT" and r["request_sent"] and r["no_retry"]
    assert "P1GEN" not in " ".join(B.MARKERS)


def test_no_retry_rules() -> None:
    assert B.no_retry({"status": "MODEL_UNAVAILABLE", "error_is_timeout": True})
    assert B.no_retry({"status": "HARNESS_TIMEOUT"})
    assert B.no_retry({"status": "MODEL_UNAVAILABLE", "error": "model requires more system "
                                                               "memory"})
    assert not B.no_retry({"status": "MODEL_UNAVAILABLE", "error": "connection reset"})


@pytest.mark.parametrize(("status", "cls", "reason", "expected"), [
    (None, "INFRA_ERROR", "DOCKER_FAILED", True),            # before the gate
    ("RAN", "INFRA_ERROR", "BASELINE_FAILED", True),         # baseline unhealthy
    (None, "INFRA_ERROR", "RESOURCE_KILLED", False),
    ("RAN", "INFRA_ERROR", "OTHER_AFTER_GATE", False),
    ("RAN", "FAILED", "CANDIDATE_TIMEOUT", False),
    ("RAN", "PASSED", "ALL_REQUIRED_PASSED", False),
    ("PATCH_APPLY_FAILED", "PATCH_APPLY_FAILED", "X", False),
])
def test_x_retry_rule(status: str | None, cls: str, reason: str, expected: bool) -> None:
    det = {"candidate": {"status": status} if status else None, "classification": cls,
           "reason": reason}
    assert B.x_retry_allowed(det) is expected


def test_context_state() -> None:
    m = H.p1().MODEL
    assert B.context_state({"ps_after": {"models": [{"name": m, "context_length": 16384}]}}) \
        == "CONFIRMED"
    assert B.context_state({"ps_after": {"models": [{"name": m, "context_length": 8192}]}}) \
        == "MISMATCH"
    assert B.context_state({"ps_after": {"models": []}}) == "NOT_CONFIRMED"


def test_p2_gen_differs_from_p1_gen_only_in_the_seed_rule() -> None:
    p1g = (H.RESEARCH / "p1" / "harness" / "p1_gen.py").read_text().replace("P1GEN_", "P2GEN_")
    p2g = B.GEN_SCRIPT.read_text()

    def body(src: str) -> list[str]:
        code = src.split('"""', 2)[2]
        return [ln for ln in code.splitlines() if ln.strip()]
    a, b = body(p1g), body(p2g)
    changed = [(x, y) for x, y in zip(a, b, strict=True) if x != y]
    assert changed == [
        ('    seed = provenance.derive_task_seed(req["identity"], 0)',
         '    seed = provenance.derive_task_seed(req["common_identity"], 0)'),
        ('    task = task_mod.Task(task_id=req["instance_id"], '
         'repo_path=Path("/nonexistent/p1-no-repo"),',
         '    task = task_mod.Task(task_id=req["instance_id"], '
         'repo_path=Path("/nonexistent/p2-no-repo"),'),
        ('    if hashlib.sha256(task.prompt.encode("utf-8")).hexdigest() != req["identity"]:',
         '    if hashlib.sha256(task.prompt.encode("utf-8")).hexdigest() != '
         'req["prompt_identity"]:'),
    ]


# ---- FG-5 / FG-6 ------------------------------------------------------------------------------
def test_gencheck_checks_every_slot_and_arm_without_network(tmp_path: Path) -> None:
    root, fake = make_root(tmp_path, 3), Fake()
    rec = B.gencheck(fake, root, root / "_gencheck")
    assert rec["verdict"] == "PASS" and len(rec["checks"]) == 6
    assert [k for k, _ in fake.log] == ["check"] * 6
    assert (root / "_gencheck" / "MANIFEST.sha256").exists()
    with pytest.raises(B.PhaseBStop, match="written once"):
        B.gencheck(fake, root, root / "_gencheck")


def test_gencheck_fails_on_module_mismatch(tmp_path: Path) -> None:
    root, fake = make_root(tmp_path, 2), Fake()
    fake.module_sha = {**MODS, "velith/task.py": "9" * 64}
    assert B.gencheck(fake, root, root / "_gencheck")["verdict"] == "FAIL"


def test_freeze_writes_pilot_set_and_appends_registry_once(tmp_path: Path) -> None:
    root, pilot, sha, _ = frozen(tmp_path, 3)
    reg = json.loads((tmp_path / "registry.json").read_text())
    orig = json.loads(B.REGISTRY.read_text())
    assert reg["initial_holdout"] == orig["initial_holdout"]
    assert [e["status"] for e in reg["p2_appended"]] == ["admitted"] * 3 + [
        "rejected_at_admission (exposed)"]
    assert reg["p2_appended"][3]["reason"] == "F_OVER_BUDGET"
    t = pilot["tasks"][0]
    assert t["arm_order"] == list(B.arm_order(t["instance_id"]))
    assert t["stage_x_timeout_s"] == 900.0 and t["predicted_prompt_eval_count"] == {
        "U": 500, "S": 489}
    assert pilot["code_sha256"] == B.code_shas() and pilot["n"] == 3
    assert pilot["model"]["num_predict"] == 1024 and pilot["model"]["temperature"] == 0.0
    with pytest.raises(B.PhaseBStop, match="written once"):
        B.freeze(root, root / "_gencheck", tmp_path / "registry.json", tmp_path / "PILOT_SET.json")
    (tmp_path / "PILOT_SET.json").unlink()
    with pytest.raises(B.PhaseBStop, match="append-once"):
        B.freeze(root, root / "_gencheck", tmp_path / "registry.json", tmp_path / "PILOT_SET.json")


def test_freeze_refuses_changed_code_and_a1_alarm(tmp_path: Path,
                                                   monkeypatch: pytest.MonkeyPatch) -> None:
    root, fake = make_root(tmp_path, 2), Fake()
    B.gencheck(fake, root, root / "_gencheck")
    reg = tmp_path / "registry.json"
    reg.write_bytes(pre_freeze_registry())
    rec_path = root / "P2-02" / "record.json"
    rec = json.loads(rec_path.read_text())
    rec["self_check_diagnostic"]["harness_integrity_alarm"] = True
    rec_path.write_text(json.dumps(rec))
    with pytest.raises(B.PhaseBStop, match="A-1"):
        B.build_freeze(root, root / "_gencheck", reg)
    monkeypatch.setattr(B, "code_shas", lambda: {"changed": "1"})
    with pytest.raises(B.PhaseBStop, match="code changed"):
        B.build_freeze(root, root / "_gencheck", reg)


def test_check_frozen_refuses_mismatch(tmp_path: Path) -> None:
    _root, _pilot, sha, _ = frozen(tmp_path, 2)
    with pytest.raises(B.PhaseBStop, match="FG-8"):
        B.check_frozen(tmp_path / "PILOT_SET.json", "0" * 64, tmp_path / "registry.json")
    (tmp_path / "registry.json").write_bytes(b"{}")
    with pytest.raises(B.PhaseBStop, match="registry changed"):
        B.check_frozen(tmp_path / "PILOT_SET.json", sha, tmp_path / "registry.json")


def test_phase_a_void_refuses_phase_b(tmp_path: Path) -> None:
    root = make_root(tmp_path, 2)
    (root / "_lottery" / "admission_log.json").write_text(json.dumps(
        {"status": "VOID", "n_admitted": 2, "slots": {}}))
    with pytest.raises(B.PhaseBStop, match="P2-D"):
        B.phase_a_slots(root)


# ---- Phase B: one task ------------------------------------------------------------------------
def test_happy_path_order_cold_start_endpoints(tmp_path: Path) -> None:
    root, pilot, sha, fake = frozen(tmp_path, 1)
    task = pilot["tasks"][0]
    ep = B.run_task(fake, pilot, task, root, sha)
    first, second = task["arm_order"]
    kinds = [k for k, _ in fake.log]
    assert kinds == ["pull", "stop", "ps", "generate", "stop", "ps",
                     "stop", "ps", "generate", "stop", "ps", "remove"]
    gens = [v for k, v in fake.log if k == "generate"]
    assert gens == [(task["instance_id"], first), (task["instance_id"], second)]
    assert fake.gate_calls == [(task["instance_id"], "U"), (task["instance_id"], "S")]
    assert ep["arms"]["U"]["applies"] is True and ep["arms"]["S"]["applies"] is True
    assert ep["arms"]["U"]["verified_pass"] is True and ep["arms"]["S"]["L2"] == "OK"
    assert ep["arms"]["S"]["L3"] == "GATE_PASS" and ep["infra_unresolved"] is False
    assert ep["pilot_set_sha256"] == sha and ep["image_removed"] is True
    d = root / task["slot"]
    assert (d / "S" / "synthesized.diff").read_text() == SYNTH
    assert (d / "X-U-1" / "evidence.json").exists() and (d / "X-S-1" / "evidence.json").exists()
    assert (d / "MANIFEST.sha256").exists()
    fake.log.clear()
    assert B.run_task(fake, pilot, task, root, sha) == ep and fake.log == []  # final, no rerun


def test_resume_never_regenerates_a_completed_arm(tmp_path: Path) -> None:
    root, pilot, sha, fake = frozen(tmp_path, 1)
    task = pilot["tasks"][0]
    second = task["arm_order"][1]
    fake.gen_status[(task["instance_id"], second)] = [{"status": "MODEL_ALREADY_LOADED",
                                                       "request_sent": False}]
    with pytest.raises(B.PhaseBStop, match="pre-request"):
        B.run_task(fake, pilot, task, root, sha)
    assert ("remove", task["ref"]) in fake.log
    fake.log.clear()
    ep = B.run_task(fake, pilot, task, root, sha)
    assert [v for k, v in fake.log if k == "generate"] == [(task["instance_id"], second)]
    assert ep["arms"][second]["generation"]["attempts"] == 1


def test_gen_infra_one_retry_then_na(tmp_path: Path) -> None:
    root, pilot, sha, fake = frozen(tmp_path, 1)
    task = pilot["tasks"][0]
    bad = {"status": "MODEL_UNAVAILABLE", "error": "connection reset", "request_sent": True}
    fake.gen_status[(task["instance_id"], "U")] = [dict(bad), dict(bad)]
    ep = B.run_task(fake, pilot, task, root, sha)
    assert ep["arms"]["U"]["applies"] == H.NA and ep["arms"]["U"]["generation"]["attempts"] == 2
    assert ep["na_reasons"] == {"U": "GEN_INFRA"} and ep["infra_unresolved"] is True
    assert ep["arms"]["S"]["applies"] is True


def test_no_retry_after_generation_timeout(tmp_path: Path) -> None:
    root, pilot, sha, fake = frozen(tmp_path, 1)
    task = pilot["tasks"][0]
    fake.gen_status[(task["instance_id"], "S")] = [{"status": "HARNESS_TIMEOUT",
                                                    "request_sent": True}]
    ep = B.run_task(fake, pilot, task, root, sha)
    assert ep["arms"]["S"]["generation"]["attempts"] == 1 and ep["arms"]["S"]["applies"] == H.NA


def test_d7_identity_mismatch_aborts_the_pair(tmp_path: Path) -> None:
    root, pilot, sha, fake = frozen(tmp_path, 1, Fake(image_id_override="sha256:other"))
    ep = B.run_task(fake, pilot, pilot["tasks"][0], root, sha)
    assert ep["arms"]["U"]["applies"] == ep["arms"]["S"]["applies"] == H.NA
    assert ep["na_reasons"] == {"U": "D7_ABORT", "S": "D7_ABORT"} and ep["d7"]["aborted"]
    assert not [k for k, _ in fake.log if k == "generate"] and fake.gate_calls == []
    assert ("remove", pilot["tasks"][0]["ref"]) in fake.log


@pytest.mark.parametrize(("completion", "code"), [
    ("<<<<<<< SEARCH pkg/m.py\n    return 2\n=======\n    x\n>>>>>>> REPLACE\n",
     E.S_SEARCH_NOT_FOUND),
    ("<<<<<<< SEARCH pkg/missing.py\n    return 1\n=======\n    x\n>>>>>>> REPLACE\n",
     E.S_PATH_INVALID),
    ("<<<<<<< SEARCH pkg/m.py\n    return 1\n=======\n    return 1\n>>>>>>> REPLACE\n",
     E.S_EMPTY_EDIT),
    ("I cannot help.", E.S_MALFORMED_BLOCK),
    ("   ", E.NO_OUTPUT),
])
def test_s_resolution_failures_are_false_without_gate(tmp_path: Path, completion: str,
                                                      code: str) -> None:
    root, pilot, sha, fake = frozen(tmp_path, 1)
    task = pilot["tasks"][0]
    fake.completions[(task["instance_id"], "S")] = completion
    ep = B.run_task(fake, pilot, task, root, sha)
    assert ep["arms"]["S"]["applies"] is False and ep["arms"]["S"]["L2"] == code
    assert fake.gate_calls == [(task["instance_id"], "U")]
    assert not (root / task["slot"] / "S" / "synthesized.diff").exists()


def test_u_without_patch_is_false_without_gate(tmp_path: Path) -> None:
    root, pilot, sha, fake = frozen(tmp_path, 1)
    task = pilot["tasks"][0]
    fake.completions[(task["instance_id"], "U")] = "no diff here"
    ep = B.run_task(fake, pilot, task, root, sha)
    assert ep["arms"]["U"]["applies"] is False and ep["arms"]["U"]["L1"] == E.NO_OUTPUT
    assert fake.gate_calls == [(task["instance_id"], "S")]


def test_u_gate_rejection_is_false(tmp_path: Path) -> None:
    root, pilot, sha, fake = frozen(tmp_path, 1)
    task = pilot["tasks"][0]
    fake.gate_status[(task["instance_id"], "U")] = [("PATCH_APPLY_FAILED", "PATCH_APPLY_FAILED",
                                                     "CANDIDATE_PATCH_APPLY_FAILED")]
    ep = B.run_task(fake, pilot, task, root, sha)
    assert ep["arms"]["U"]["applies"] is False
    assert ep["arms"]["U"]["L3"] == "PATCH_DOES_NOT_APPLY" and ep["arms"]["U"]["L4"] is None


def test_s_synth_integrity_stops_the_pilot(tmp_path: Path) -> None:
    root, pilot, sha, fake = frozen(tmp_path, 1)
    task = pilot["tasks"][0]
    fake.gate_status[(task["instance_id"], "S")] = [("PATCH_APPLY_FAILED", "PATCH_APPLY_FAILED",
                                                     "CANDIDATE_PATCH_APPLY_FAILED")]
    with pytest.raises(H.HarnessStop, match="S_SYNTH_INTEGRITY"):
        B.run_task(fake, pilot, task, root, sha)
    d = root / task["slot"]
    assert (d / "stop.json").exists() and not (d / "episode.json").exists()
    assert ("remove", task["ref"]) in fake.log


def test_stage_x_one_retry_on_pre_gate_infra_then_na(tmp_path: Path) -> None:
    root, pilot, sha, fake = frozen(tmp_path, 1)
    task = pilot["tasks"][0]
    infra = (None, "INFRA_ERROR", "DOCKER_FAILED")
    fake.gate_status[(task["instance_id"], "U")] = [infra, infra]  # type: ignore[list-item]
    ep = B.run_task(fake, pilot, task, root, sha)
    assert ep["arms"]["U"]["x_attempts"] == 2 and ep["arms"]["U"]["applies"] == H.NA
    assert ep["arms"]["U"]["L3"] == "PRE_GATE_INFRA" and ep["na_reasons"] == {
        "U": "PRE_GATE_INFRA"}


def test_model_still_loaded_after_stop_is_a_stop(tmp_path: Path) -> None:
    root, pilot, sha, fake = frozen(tmp_path, 1)
    fake.ps_loaded_after_stop = True
    with pytest.raises(B.PhaseBStop, match="not empty"):
        B.run_task(fake, pilot, pilot["tasks"][0], root, sha)
    assert not [k for k, _ in fake.log if k == "generate"]


def test_low_ram_is_a_stop_without_consuming_an_attempt(tmp_path: Path) -> None:
    root, pilot, sha, fake = frozen(tmp_path, 1, Fake(ram=1024))
    with pytest.raises(B.PhaseBStop, match="free RAM"):
        B.run_task(fake, pilot, pilot["tasks"][0], root, sha)
    assert not list((root / "P2-01").glob("G-*/attempt-*"))


def test_context_length_mismatch_is_a_stop(tmp_path: Path) -> None:
    root, pilot, sha, fake = frozen(tmp_path, 1, Fake(ctx=8192))
    with pytest.raises(B.PhaseBStop, match="context_length"):
        B.run_task(fake, pilot, pilot["tasks"][0], root, sha)


def test_token_mismatch_and_truncation_are_flags(tmp_path: Path) -> None:
    root, pilot, sha, fake = frozen(tmp_path, 1, Fake(prompt_tokens_delta=3,
                                                      completion_tokens=1024))
    ep = B.run_task(fake, pilot, pilot["tasks"][0], root, sha)
    for arm in B.ARMS:
        assert ep["arms"][arm]["generation"]["flags"] == ["TOKEN_COUNT_MISMATCH", "GEN_TRUNCATED"]
        assert ep["arms"][arm]["applies"] is True  # flags never change the endpoint


def test_image_delete_failure_is_a_stop(tmp_path: Path) -> None:
    root, pilot, sha, fake = frozen(tmp_path, 1, Fake(remove_ok=False))
    with pytest.raises(B.PhaseBStop, match="image delete failed"):
        B.run_task(fake, pilot, pilot["tasks"][0], root, sha)


def test_infra_stop_after_three_unresolved_tasks(tmp_path: Path) -> None:
    root, pilot, sha, fake = frozen(tmp_path, 4, Fake(image_id_override="sha256:other"))
    with pytest.raises(B.PhaseBStop, match="P2-D"):
        B.run_phase_b(fake, pilot, sha, root)
    assert sorted(p.parent.name for p in root.glob("P2-*/episode.json")) == [
        "P2-01", "P2-02", "P2-03"]


# ---- report -----------------------------------------------------------------------------------
def test_report_table_sign_test_and_conclusion(tmp_path: Path) -> None:
    root, pilot, sha, fake = frozen(tmp_path, 10)
    reject = ("PATCH_APPLY_FAILED", "PATCH_APPLY_FAILED", "CANDIDATE_PATCH_APPLY_FAILED")
    for t in pilot["tasks"][:6]:  # S-only on six tasks
        fake.gate_status[(t["instance_id"], "U")] = [reject]
    for t in pilot["tasks"][6:8]:  # neither
        fake.completions[(t["instance_id"], "U")] = "no diff"
        fake.completions[(t["instance_id"], "S")] = "nothing"
    B.run_phase_b(fake, pilot, sha, root)
    rep = B.report(pilot, root, tmp_path / "_report")
    assert rep["table"] == {"both": 2, "s_only": 6, "u_only": 0, "neither": 2, "n_v": 10,
                            "discordant": 6, "k_s": 8, "k_u": 2}
    assert rep["sign_test_p_one_sided"] == "1/64" and rep["conclusion"] == "P2-A"
    assert rep["verified_pass_secondary"] == {"U": 2, "S": 8}
    assert (tmp_path / "_report" / "report.json").exists()


def test_report_refuses_incomplete_phase_b(tmp_path: Path) -> None:
    root, pilot, _sha, _fake = frozen(tmp_path, 2)
    with pytest.raises(B.PhaseBStop, match="incomplete"):
        B.report(pilot, root, tmp_path / "_report")
