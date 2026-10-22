# P4 sizing probe: freeze decision record (DRAFT for RD signature; NOT a freeze)

**Prepared:** 2026-10-16 by the CSE, on RD request.

**Status:**
- This record **freezes nothing, edits no lock, and authorizes no execution.**
- It becomes effective only through the separate RD acts in §6.

## 1. Freeze target (verified 2026-10-16T08:09Z)

| Item | SHA-256 |
|---|---|
| Document `p4/P4_SIZING_PROBE_PROTOCOL_v0.3.md` | `a34a729de53e47cf021a9cecf886327c39c161252fd862540f6c57e7ded77bb4` |
| Marked block (BEGIN marker through END marker inclusive, UTF-8, §3–§6) | `f8a7e398609a70b83a2cad9ad29571aad9ebaecc2d56f8aa3e7502df261a4d8d` |

- Both values were recomputed from the files on disk at the time above.
- `sizing_probe.protocol_block_sha()` returns the block value.
- `FROZEN_PROTOCOL_SHA` is still `None`.

## 2. G-6 (RD decision, recorded here)

> **An INCOMPLETE outcome does not support a census-v2 proposal, even if its lower bound M_v,LB ≥ 500. Any exception requires a separate governance decision.**

- This resolves the option left open in block §5 ("The RD may decide whether a lower bound M_v,LB ≥ 500 suffices (G-6)") as **no**.
- The block text is unchanged. G-6 is recorded here, so the block hash stays the same.
- **Census v2 may be proposed only on EXACT with M_v ≥ 500.**

## 3. STOP-POLICY arithmetic (M_v ≤ 62): a conservative policy threshold

**Bounds that hold for any yield.**
- Each unseen repo contributes at most **4** cap-adjusted candidates, because the cap-4 count is Σ min(4, c_r) by definition.
- Each unseen repo contributes at most **1** candidate-bearing repo.

**Comparison with run 1, using matching units:**

| Baseline (run 1) | Unseen maximum at M_v = 62 | Share | 25% of baseline |
|---|---|---|---|
| Cap-adjusted candidates **996** | 4 × 62 = **248** | 24.9% | 249: 248 < 249 ✓ |
| Candidate-bearing repos **320** | 62 | 19.4% | 80: 62 < 80 ✓ |

At M_v = 63 the capped maximum is 252, which is ≥ 249. The capped criterion is the binding one.

**On "10,245 candidates" (CSE challenge; the record is not changed to use it).**
- 10,245 is the **uncapped** raw count. Under the cap-4 rule, an unseen repo's *uncapped* contribution has **no per-repo bound**: one run-1 repo alone had 1,408 candidates.
- So "4 × 62 = 248 vs 10,245 (2.4%)" mixes capped and uncapped units, and is **not** a valid basis.
- Block §5 already uses the matching pair (996 capped, 320 repos). The arithmetic above follows the block.
- Basing the rule on 10,245 would be a different, unsound rule. It would need a block change, and therefore a new hash.

**Label.**
- **62 is a conservative policy threshold**, not a uniquely derived mathematical boundary.
- It is the largest integer that satisfies both arithmetic bounds at a **policy-chosen** 25% materiality level.
- Another materiality level gives another number. Any value below 62 also satisfies the bounds.

**Companion threshold.** M_v ≥ 500 is a policy threshold for *proposing* census v2: at least +50% more repos than run 1 examined. It is not a yield bound and not proof of task sufficiency.

## 4. Protocol completeness ≠ search-index completeness

- **EXACT** means only this: semantic calibration S0 passed, every final partition was enumerated, and checks C0–C6 passed within their stated tolerances.
- M_v counts **search-visible** repositories.
- **An EXACT outcome is not proof that GitHub search exposes every qualifying repository**, nor that its counts are error-free. Repositories absent from the search index are unobservable by this probe.
- This wording is in block §4.9 and is written into every result (`exact_semantics`).

## 5. Final artifacts and checks

| File | SHA-256 |
|---|---|
| `p4/probe/sizing_probe.py` (v0.3.1; lock `None`) | `0b0584cee916455f39554270ef96dd31fd747ae4202ed7a0cfd1f169cddb9925` |
| `p4/probe/test_sizing_probe.py` (v0.3.1) | `fdfc97b684752dbcf5c974cda04c671248c0758e8b87a51daf0047c2b54f86e9` |
| `p4/probe/run_live_probe.sh` (not run) | `904692c2474aefabdd8e0a73ad990d319920181b8d2817db4e733232effb428d` |
| Probe code after the one-line PR-2 edit (computed in memory, **not applied**) | `2c4acbcc0fc7bade265475abe1b5db9821bff1b7efd935fa20acd98b008f2494` |
| Frozen census code (unchanged) | `23e410ca68b087ba25710f77103fe567ac6de04b64fbce8f79aca6897843581d` |

**Executed by the CSE** (sandbox, on a copy of `p4/`, 2026-10-16T08:09Z):
- `pytest`: 36 probe + 39 census tests, **75 passed**;
- `ruff` (E, F, W, B, UP; line length 110): **all checks passed**;
- `mypy`: **no issues** (`sizing_probe.py`);
- `bash -n run_live_probe.sh`: **syntax OK**;
- file and block hashes above.

**Executed by the RD** (WSL):
- the offline P4C census check (2026-10-16): integrity intact, SCREEN-POSITIVE;
- the Q1 baseline check on probe v0.3 (`df8aee08…`): `BASELINE_OK`, 999 unique ids = 999 unique names, `COPY_STILL_VERIFIES`.
- Q1 holds for v0.3.1: a diff shows the baseline functions are byte-identical.

**Not independently reproduced by the RD:**
- the pytest, ruff, mypy and `bash -n` results;
- the post-edit hash `2c4acbcc…`;
- all synthetic-test claims (they use a fake GitHub, not the real API);
- the wrapper's behaviour (never run).

**Not verified by anyone:**
- real GitHub range semantics (to be checked by S0 at run time);
- live API behaviour;
- index completeness.

## 6. Authorization boundaries: three separate RD acts, none authorized by this record

| Act | What it is | Effect |
|---|---|---|
| **A. Protocol freeze** | RD records the freeze of block `f8a7e398…` in document `a34a729d…` | No file changes, no network |
| **B. PR-2 lock edit** | One line, line 38 of `p4/probe/sizing_probe.py`: `None` → `"f8a7e398609a70b83a2cad9ad29571aad9ebaecc2d56f8aa3e7502df261a4d8d"  # PR-2`. Expected file SHA after the edit: `2c4acbcc…` | Requires A first. No network |
| **C. One live probe** | One run of `run_live_probe.sh` with `P4_PROBE_RD_AUTH="PR-2 approved f8a7e398…"`. GitHub search only, ≤ 200 requests, ≤ 4.5 h | Requires A and B. The only network step |

**None of A, B or C is authorized by this review request or by this record.** Each needs its own explicit RD instruction.

**RD signature:** ________ **Date:** ________ **Acts approved (A/B/C):** ________
