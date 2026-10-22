# P4 sizing probe: protocol freeze record (Act A)

**RD decision:** Act A approved only. Recorded 2026-10-16T09:23:57Z (UTC).

## Frozen

| Item | SHA-256 |
|---|---|
| Document `p4/P4_SIZING_PROBE_PROTOCOL_v0.3.md` | `a34a729de53e47cf021a9cecf886327c39c161252fd862540f6c57e7ded77bb4` |
| Marked protocol block (`<!-- PROBE-PROTOCOL-BEGIN -->` through `<!-- PROBE-PROTOCOL-END -->` inclusive, UTF-8) | `f8a7e398609a70b83a2cad9ad29571aad9ebaecc2d56f8aa3e7502df261a4d8d` |

- Both were verified equal to the RD-specified values immediately before this record was written.
- The protocol document itself was **not** modified; the freeze is recorded only in this file.
- Any change to the block is a new protocol version requiring a new freeze.

## Settled decisions

- **G-6:** an INCOMPLETE outcome does not support a census-v2 proposal, regardless of its lower bound. Any exception requires a separate governance decision. Census v2 may be proposed only on EXACT with M_v ≥ 500.
- **STOP-POLICY:** M_v ≤ 62 is a **conservative policy threshold**. It is based on the run-1 baselines of 996 capped candidates and 320 candidate-bearing repositories, at a policy-chosen 25% materiality level: 4 × 62 = 248 < 249, and 62 < 80. It is not a uniquely derived mathematical boundary.
- **EXACT** means protocol completeness only. It is not proof that GitHub search exposes every qualifying repository.

## State at freeze (not frozen by this act; recorded for traceability)

| Artifact | SHA-256 / state |
|---|---|
| `p4/probe/sizing_probe.py` | `0b0584cee916455f39554270ef96dd31fd747ae4202ed7a0cfd1f169cddb9925`; `FROZEN_PROTOCOL_SHA = None` (live network locked) |
| `p4/probe/test_sizing_probe.py` | `fdfc97b684752dbcf5c974cda04c671248c0758e8b87a51daf0047c2b54f86e9` |
| `p4/probe/run_live_probe.sh` | `904692c2474aefabdd8e0a73ad990d319920181b8d2817db4e733232effb428d` (never run) |
| `p4/census/supply_census.py` (frozen census code) | `23e410ca68b087ba25710f77103fe567ac6de04b64fbce8f79aca6897843581d` |
| Decision record draft | `p4/P4_SIZING_PROBE_FREEZE_DECISION_RECORD.md`, `0b8aef57478bffe523fb10f6f5c03b67629191654cbd55fcab5432d508922860` |

## Not authorized by this act

| Act | Content | Status |
|---|---|---|
| **B** | The one-line lock edit at `sizing_probe.py` line 38, setting `FROZEN_PROTOCOL_SHA` to the block SHA. Expected resulting file SHA: `2c4acbcc0fc7bade265475abe1b5db9821bff1b7efd935fa20acd98b008f2494` | Requires a separate RD authorization |
| **C** | One live probe via `run_live_probe.sh` | Requires Act B and a separate RD authorization |

No network request, build, task selection, model call, commit or push was made.
