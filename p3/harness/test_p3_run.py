"""Synthetic tests for the P3 harness. No API call, no Docker, no network.

The real frozen P2 PILOT_SET, prompts and specs are read (hash-checked), never written.
Run:  PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider p3/harness/test_p3_run.py
"""
from __future__ import annotations

import json
import re
import sys
import types
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import p3_run as R  # noqa: E402

_DIFF = re.compile(r"^diff --git a/.* b/(.*)$", re.MULTILINE)
PATCH = "diff --git a/m.py b/m.py\n--- a/m.py\n+++ b/m.py\n@@ -1 +1 @@\n-a\n+b\n"
GOOD = f"```diff\n{PATCH}```"


@pytest.fixture(autouse=True)
def stub_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = types.ModuleType("probe")
    stub.patch_files = lambda patch: sorted(set(_DIFF.findall(patch)))  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "probe", stub)


def msg(text: str, stop: str = "end_turn") -> tuple[int, bytes, None]:
    return 200, json.dumps({"type": "message", "id": "msg_1", "model": R.MODEL,
                            "content": [{"type": "text", "text": text}], "stop_reason": stop,
                            "usage": {"input_tokens": 100, "output_tokens": 50}}).encode(), None


@dataclass
class FakeApi:
    queue: list[tuple[int | None, bytes, str | None]] = field(default_factory=list)
    default: str = GOOD
    calls: list[str] = field(default_factory=list)

    def post(self, path: str, body: dict[str, Any]) -> tuple[int | None, bytes, str | None]:
        self.calls.append(path)
        if path == "/messages/count_tokens":
            assert set(body) == {"model", "messages"}
            return 200, json.dumps({"input_tokens": 1234}).encode(), None
        assert body == R.payload(body["messages"][0]["content"])
        return self.queue.pop(0) if self.queue else msg(self.default)


@dataclass
class FakeOps:
    pilot: dict[str, Any]
    gate_status: list[tuple[str, str]] = field(default_factory=list)
    module_ok: bool = True
    image_mismatch: bool = False
    log: list[str] = field(default_factory=list)

    def free_bytes(self) -> int:
        return 10**15

    def pull(self, ref: str) -> bool:
        self.log.append("pull")
        return True

    def inspect(self, ref: str) -> tuple[list[str], str, str] | None:
        t = next(t for t in self.pilot["tasks"] if t["ref"] == ref)
        return [ref], "linux/amd64", "sha256:other" if self.image_mismatch else t["image_id"]

    def remove(self, ref: str) -> bool:
        self.log.append("remove")
        return True

    def verifier_image_id(self) -> str:
        return str(self.pilot["generation_route"]["image_id"])

    def extract(self, image_id: str, completion: str, proposer_sha: str) -> dict[str, Any]:
        assert proposer_sha == self.pilot["generation_route"]["module_sha256"][
            "velith/agent/proposer.py"]
        if not self.module_ok:
            return {"status": "MODULE_MISMATCH"}
        patch = completion.split("```diff\n", 1)[1].split("```", 1)[0] if "```diff" in \
            completion else ""
        return {"status": "OK", "patch": patch, "has_patch": bool(patch.strip())}

    def gate(self, spec: dict[str, Any], patch: str, run_dir: Path, timeout: float, arm: str
             ) -> dict[str, Any]:
        self.log.append("gate")
        status, cls = self.gate_status.pop(0) if self.gate_status else ("RAN", "PASSED")
        oc = {i: ("passed" if cls == "PASSED" else "failed") for i in spec["fail_to_pass"]}
        ev = {"deterministic": {"candidate": {"status": status, "outcomes": oc},
                                "classification": cls, "reason": "X", "detail": ""}}
        run_dir.mkdir(parents=True)
        (run_dir / "evidence.json").write_text(json.dumps(ev))
        return ev


@pytest.fixture
def env(tmp_path: Path) -> tuple[dict[str, Any], Path, FakeApi, FakeOps]:
    pilot = R.load_pilot()
    api, ops = FakeApi(), FakeOps(pilot)
    R.preflight(api, ops, pilot, tmp_path / "_preflight")
    api.calls.clear()
    return pilot, tmp_path, api, ops


# ---- pure rules -------------------------------------------------------------------------------
def test_payload_is_one_user_message_no_system_no_tools() -> None:
    p = R.payload("hello")
    assert p == {"model": "claude-opus-5-5", "max_tokens": 1024, "temperature": 0.0,
                 "messages": [{"role": "user", "content": "hello"}]}


def test_interpret() -> None:
    g = R.interpret(*msg("a"))
    assert g["status"] == "GENERATED" and g["completion_text"] == "a" and g["output_tokens"] == 50
    assert R.interpret(None, b"", "URLError")["status"] == "RETRYABLE"
    for code in (429, 500, 529):
        assert R.interpret(code, b"{}")["status"] == "RETRYABLE"
    over = json.dumps({"type": "error", "error": {"type": "overloaded_error"}}).encode()
    assert R.interpret(400, over)["status"] == "RETRYABLE"
    bad = json.dumps({"type": "error", "error": {"type": "authentication_error",
                                                 "message": "invalid x-api-key"}}).encode()
    assert R.interpret(401, bad) == {"status": "FATAL", "http_status": 401,
                                     "error": "authentication_error",
                                     "message": "invalid x-api-key"}


@pytest.mark.parametrize(("k", "n_v", "infra", "code"), [
    (3, 13, 0, "P3-A"), (2, 13, 0, "P3-B"), (1, 13, 0, "P3-C"), (0, 13, 0, "P3-C"),
    (9, 9, 0, "P3-D"), (5, 13, 3, "P3-D")])
def test_decision_rule(k: int, n_v: int, infra: int, code: str) -> None:
    assert R.decision(k, n_v, infra) == code


# ---- preflight --------------------------------------------------------------------------------
def test_preflight_counts_all_13_prompts_without_generation(tmp_path: Path) -> None:
    pilot = R.load_pilot()
    api = FakeApi()
    rec = R.preflight(api, FakeOps(pilot), pilot, tmp_path / "pf")
    assert rec["verdict"] == "PASS" and len(rec["input_tokens"]) == 13
    assert api.calls == ["/messages/count_tokens"] * 13
    with pytest.raises(R.P3Stop, match="written once"):
        R.preflight(api, FakeOps(pilot), pilot, tmp_path / "pf")


def test_preflight_fails_on_extractor_module_mismatch(tmp_path: Path) -> None:
    pilot = R.load_pilot()
    rec = R.preflight(FakeApi(), FakeOps(pilot, module_ok=False), pilot, tmp_path / "pf")
    assert rec["verdict"] == "FAIL"


def test_run_requires_preflight_pass(tmp_path: Path) -> None:
    pilot = R.load_pilot()
    with pytest.raises(R.P3Stop, match="preflight"):
        R.run(FakeApi(), FakeOps(pilot), pilot, tmp_path)


def test_prompt_tamper_is_refused(tmp_path: Path) -> None:
    pilot = R.load_pilot()
    t = pilot["tasks"][0]
    fake = tmp_path / "p2" / t["slot"] / "P"
    fake.mkdir(parents=True)
    (fake / "prompt_U.txt").write_text("tampered")
    with pytest.raises(R.P3Stop, match="frozen identity"):
        R.prompt_u(t, tmp_path / "p2")


# ---- one task ---------------------------------------------------------------------------------
def test_verified_task(env: Any) -> None:
    pilot, root, api, ops = env
    t = pilot["tasks"][0]
    ep = R.run_task(api, ops, pilot, t, root)
    assert ep["applies"] is True and ep["verified_pass"] is True
    assert ep["slot"] == "P3-01" and ep["generation"]["attempts"] == 1
    assert ep["tests"]["fail_to_pass"].split("/")[0] == ep["tests"]["fail_to_pass"].split("/")[1]
    assert ops.log == ["pull", "gate", "remove"] and api.calls == ["/messages"]
    d = root / "P3-01"
    assert (d / "G" / "attempt-1" / "response_raw.json").exists()
    assert (d / "E" / "patch.diff").read_text() == PATCH and (d / "MANIFEST.sha256").exists()
    req = json.loads((d / "G" / "attempt-1" / "request.json").read_text())
    assert "content" not in req["messages"][0] and "x-api-key" not in json.dumps(req)
    api.calls.clear()
    assert R.run_task(api, ops, pilot, t, root) == ep and api.calls == []  # final, never rerun


def test_no_patch_is_false_without_gate(env: Any) -> None:
    pilot, root, api, ops = env
    api.default = "I think the bug is in m.py."
    ep = R.run_task(api, ops, pilot, pilot["tasks"][1], root)
    assert ep["applies"] is False and ep["verified_pass"] is False and "gate" not in ops.log
    assert ep["layers"] == {"L1": "NO_OUTPUT"}


def test_gate_rejection_and_test_failure(env: Any) -> None:
    pilot, root, api, ops = env
    ops.gate_status = [("PATCH_APPLY_FAILED", "PATCH_APPLY_FAILED"), ("RAN", "FAILED")]
    a = R.run_task(api, ops, pilot, pilot["tasks"][0], root)
    b = R.run_task(api, ops, pilot, pilot["tasks"][1], root)
    assert (a["applies"], a["verified_pass"]) == (False, False)
    assert (b["applies"], b["verified_pass"]) == (True, False)


def test_one_retry_only_without_completion(env: Any) -> None:
    pilot, root, api, ops = env
    api.queue = [(529, b"{}", None), msg(GOOD)]
    ep = R.run_task(api, ops, pilot, pilot["tasks"][0], root)
    assert ep["generation"]["attempts"] == 2 and ep["verified_pass"] is True
    api.queue = [(None, b"", "URLError"), (503, b"{}", None)]
    ep2 = R.run_task(api, ops, pilot, pilot["tasks"][1], root)
    assert ep2["applies"] == "NA" and ep2["infra_unresolved"] is True


def test_truncated_completion_is_not_retried(env: Any) -> None:
    pilot, root, api, ops = env
    api.queue = [msg("```diff\n--- a/m.py\n", stop="max_tokens")]
    ep = R.run_task(api, ops, pilot, pilot["tasks"][0], root)
    assert ep["generation"]["attempts"] == 1 and ep["generation"]["stop_reason"] == "max_tokens"
    assert api.calls == ["/messages"]


def test_fatal_api_error_stops_without_consuming_an_attempt(env: Any) -> None:
    pilot, root, api, ops = env
    api.queue = [(401, json.dumps({"error": {"type": "authentication_error"}}).encode(), None)]
    with pytest.raises(R.P3Stop, match="no attempt consumed"):
        R.run_task(api, ops, pilot, pilot["tasks"][0], root)
    assert not (root / "P3-01" / "G" / "attempt-1").exists() and "remove" in ops.log
    ep = R.run_task(api, ops, pilot, pilot["tasks"][0], root)
    assert ep["generation"]["attempts"] == 1 and ep["verified_pass"] is True


def test_d7_abort_makes_na_without_api_call(env: Any) -> None:
    pilot, root, api, ops = env
    ops.image_mismatch = True
    ep = R.run_task(api, ops, pilot, pilot["tasks"][0], root)
    assert ep["applies"] == ep["verified_pass"] == "NA" and api.calls == []


def test_extractor_mismatch_is_a_harness_stop(env: Any) -> None:
    pilot, root, api, ops = env
    ops.module_ok = False
    with pytest.raises(R.H.HarnessStop, match="extractor"):
        R.run_task(api, ops, pilot, pilot["tasks"][0], root)
    assert ops.log[-1] == "remove"


def test_full_run_and_report(env: Any) -> None:
    pilot, root, api, ops = env
    ops.gate_status = [("RAN", "PASSED")] * 3 + [("RAN", "FAILED")] * 10
    R.run(api, ops, pilot, root)
    rep = R.report(pilot, root)
    assert rep["k_verified"] == 3 and rep["n_v"] == 13 and rep["decision"] == "P3-A"
    assert rep["applies"] == 13 and (root / "_report" / "report.json").exists()
