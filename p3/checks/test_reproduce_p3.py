"""Synthetic tests for reproduce_p3.py (no Docker). Run with pytest -p no:cacheprovider."""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from typing import Any

import pytest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import reproduce_p3 as RP  # noqa: E402

EV = RP.R.EVIDENCE


@pytest.fixture(autouse=True)
def stub_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "probe", types.ModuleType("probe"))


class Ops:
    def __init__(self, pilot: dict[str, Any], flip: str | None = None) -> None:
        self.pilot, self.flip, self.removed = pilot, flip, 0

    def free_bytes(self) -> int:
        return 10**15

    def pull(self, ref: str) -> bool:
        return True

    def inspect(self, ref: str) -> tuple[list[str], str, str]:
        t = next(t for t in self.pilot["tasks"] if t["ref"] == ref)
        return [ref], "linux/amd64", t["image_id"]

    def remove(self, ref: str) -> bool:
        self.removed += 1
        return True

    def gate(self, spec: dict[str, Any], patch: str, run_dir: Path, timeout: float, arm: str
             ) -> dict[str, Any]:
        slot = "P3-" + next(t["slot"] for t in self.pilot["tasks"]
                            if t["instance_id"] == spec["instance_id"])[3:]
        orig = json.loads(sorted((EV / slot).glob("X-U-*/evidence.json"))[-1].read_text())
        if self.flip == slot:
            k = next(iter(orig["deterministic"]["candidate"]["outcomes"]))
            orig["deterministic"]["candidate"]["outcomes"][k] = "failed"
        return dict(orig)


def test_replay_of_recorded_evidence_reproduces(tmp_path: Path) -> None:
    ops = Ops(RP.R.load_pilot())
    res = RP.reproduce(ops, "passes", tmp_path)
    assert set(res) == set(RP.PASSES) and all(r["reproduced"] for r in res.values())
    assert ops.removed == 6


def test_a_changed_test_outcome_is_detected(tmp_path: Path) -> None:
    res = RP.reproduce(Ops(RP.R.load_pilot(), flip="P3-07"), "passes", tmp_path)
    assert res["P3-07"]["reproduced"] is False and res["P3-07"]["outcome_diffs"]


def test_unstripped_block_keeps_trailing_whitespace_context_line() -> None:
    comp = "```diff\n--- a/x.py\n+++ b/x.py\n@@ -1,2 +1,2 @@\n-a\n+b\n \n```"
    assert RP.unstripped_block(comp).endswith("+b\n \n")
