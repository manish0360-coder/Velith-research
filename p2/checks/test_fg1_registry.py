"""FG-1 deterministic checks: p2/P2_EXCLUSION_REGISTRY.json against the frozen P2 specification.

Stdlib only, no network, no Docker, no model. It reads three files and writes nothing.
Run either way:  python3 -B p2/checks/test_fg1_registry.py
                 python3 -m pytest -q -p no:cacheprovider p2/checks/test_fg1_registry.py
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P1_REGISTRY = ROOT / "p1" / "PILOT_EXCLUSION_REGISTRY.json"
P2_REGISTRY = ROOT / "p2" / "P2_EXCLUSION_REGISTRY.json"
SPEC = ROOT / "p2" / "P2_SPEC.md"
# frozen P1 registry (P2_SPEC §11) and the FG-0 frozen specification
P1_REGISTRY_SHA256 = "9fc0157b3c21b99a10753cb0075b0b7f990da248b1ecdb2bf8af51b82a4bcd60"
SPEC_SHA256 = "b2d29c5cdfba65b24c514763412c0807704c88f52d39e663f3fc6cc7a6d21c32"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def spec_ids() -> list[str]:
    """The 11 IDs exactly as listed in the frozen P2_SPEC.md §11 table, in table order."""
    text = SPEC.read_text(encoding="utf-8")
    section = text.split("## 11.", 1)[1].split("## 12.", 1)[0]
    return re.findall(r"^\| \d+ \| `([^`]+)` \|", section, flags=re.MULTILINE)


def p1_entries() -> list[dict]:
    return json.loads(P1_REGISTRY.read_text(encoding="utf-8"))["excluded"]


def p2() -> dict:
    return json.loads(P2_REGISTRY.read_text(encoding="utf-8"))


def p2_ids() -> list[str]:
    return [e["instance_id"] for e in p2()["initial_holdout"]]


def test_p1_registry_byte_identical() -> None:
    assert sha256(P1_REGISTRY) == P1_REGISTRY_SHA256


def test_spec_is_the_frozen_spec() -> None:
    assert sha256(SPEC) == SPEC_SHA256


def test_exactly_11_entries() -> None:
    assert len(spec_ids()) == 11
    assert len(p2_ids()) == 11


def test_all_11_are_p1_ids_in_frozen_order() -> None:
    p1_ids = [e["instance_id"] for e in p1_entries()]
    assert p2_ids() == spec_ids() == p1_ids


def test_no_duplicates() -> None:
    assert len(set(p2_ids())) == len(p2_ids())


def test_no_ids_outside_frozen_list() -> None:
    assert set(p2_ids()) == set(spec_ids())
    assert p2()["p2_appended"] == []  # FG-1 state: nothing appended before FG-6


def test_entries_carry_exact_p1_status_and_identity() -> None:
    for mine, src in zip(p2()["initial_holdout"], p1_entries(), strict=True):
        assert mine["instance_id"] == src["instance_id"]
        assert mine["p1_status"] == src["status"]
        assert mine["p1_pilot_task_identity"] == src["pilot_task_identity"]
        assert mine["source"] == "p1/PILOT_EXCLUSION_REGISTRY.json"


def test_provenance_fields_match_files() -> None:
    reg = p2()
    assert reg["registry"] == "velith-p2-exclusion" and reg["pilot"] == "M2-PV-P2"
    assert reg["source_registry_sha256"] == sha256(P1_REGISTRY)
    assert reg["spec_sha256"] == sha256(SPEC)
    p1 = json.loads(P1_REGISTRY.read_text(encoding="utf-8"))
    assert (reg["dataset"], reg["dataset_revision"]) == (p1["dataset"], p1["dataset_revision"])


def test_canonical_deterministic_serialization() -> None:
    canonical = json.dumps(p2(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    assert P2_REGISTRY.read_bytes() == canonical.encode("utf-8")


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS {name}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {name} {exc}")
    print(f"{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
