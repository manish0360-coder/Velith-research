# P4 B-1 source-direction decision record: run-1 post-cutoff candidate-repository frame

**Date:** 2026-10-16.
**Decision authority:** Research Director (ChatGPT). **Prepared by:** Chief Systems Engineer (Claude).
**Status:** a **source-direction decision only.** This record does not complete P4 governance and edits no existing document.

## 1. Ruling (as issued by the RD)

> **B-1b is selected as the preferred P4 source direction:** the run-1 post-cutoff candidate-repository frame, rather than the currently documented SWE-bench-Live Python snapshot.
>
> **Reason:** the documented SWE-bench-Live Python snapshot ends on 2025-08-30, before the frozen cutoff B = 2026-08-01, while the run-1 candidate population aligns more closely with the proposed Stage-1 held-out population under RD-2.
>
> **Does NOT:** ratify the draft's 60-repository frame size, authorize task selection, establish admission sufficiency, authorize the sizing probe, or authorize a build spike.

**Mechanism.** `P4_SPEC.md` v0.2 L72 requires that "any change of source is a new RD decision". This record is that decision, for the source **direction**. It supersedes the source choice of U-3 (`P4_SPEC.md` L318) as the preferred direction. `P4_SPEC.md` v0.2 is **not edited**; a later P4 specification version must incorporate the change.

## 2. Supporting evidence (read-only, verified 2026-10-16)

| # | Fact | Source |
|---|---|---|
| E1 | B = 2026-08-01, and "**The cutoff is never weakened.**" A task is eligible only if **every** timestamp is ≥ B; exclusions E1–E5 apply | `p4/P4_SPEC.md` L49, L51, L62–66; U-2 at L317 |
| E2 | Documented SWE-bench-Live Python: `created_at` 2024-01-01 → **2025-08-30** (3,688 rows; retrieved 2026-10-12). "Until FG-1 measures it, the expected eligible count is **zero**" | `p4/P4_SPEC.md` L74; `p4/P4_SOURCE_SCAN.md` L17 |
| E3 | U-3 names "One fixed, versioned SWE-bench-Live Python-only snapshot … **No silent source change**" | `p4/P4_SPEC.md` L72, L318 |
| E4 | Census run 1: 1,000 repos searched, 589 kept, **320 repositories with ≥ 1 candidate**. "**No task is selected, admitted or eligible** as a result of this census." E1–E3 history checks were not run, and the base commit is approximated by the merge base | `p4/P4_SUPPLY_CENSUS.md` L109, L189–197 |
| E5 | Draft partition: "The 320 repos are split by lottery into F (60) and R (260)". Status: **DRAFT**, "Nothing here is authorized to run" | `p4/P4_BUILD_SPIKE_SPEC_v0.11.md` L3, L157, L200 |
| E6 | Planning estimate "C_F ≈ 60/320 × 996 ≈ 187, so 50 / C_F ≈ 0.27" | `p4/P4_BUILD_SPIKE_SPEC_v0.11.md` L232 |
| E7 | P4 selection: frozen-order walk, **repository cap ≤ 4**, no backfill, until **n = 50** admitted. **P4-POOL-INSUFFICIENT** if fewer than 40 admitted, or N_eligible < R + 52 | `p4/P4_SPEC.md` L150–152, L83 |
| E8 | RD rulings of 2026-10-16: **DU-1** Cap 1 for the confirmatory held-out sample (provisional); **DE-1** repository-disjoint experience; **DE-2** pre-B experience preferred; **DE-4** P4 pilot tasks and repositories excluded from the confirmatory held-out pool | `p4/P4_SIZING_PROBE_GOVERNANCE_NOTE_GN1-r1.md` L17–21 |
| E9 | Pilot information never enters memory or confirmatory inference; pilot tasks are excluded from held-out | Velith `docs/DECISIONS.md` D31 item 10, L738–740 |
| E10 | RD-2: "p0 only plans the confirmatory population if pilot tasks are drawn from it." **Scope:** RD-2 applies to the **Base-Rate Design Pilot (BRP)** under RD-0 = Option (B). That amendment is **awaiting ratification** | `M9-ST1_RD_DECISION_REGISTER.md` L22, L41–63, L80–95; `RD-0_C-1_RESOLUTION_AMENDMENT_PROPOSED.md` L1–3 |
| E11 | `P4_SPEC.md` asserts "P4 supplies the pilot base rate D31 item 8 requires" | `p4/P4_SPEC.md` L196 |

**Why the documented SWE-bench-Live snapshot fails B.** Every task in the documented snapshot has a PR creation date ≤ 2025-08-30, which is before B = 2026-08-01 (E1, E2). Under the frozen rule that every timestamp must be ≥ B, none is eligible.

**A different snapshot.** Any different SWE-bench-Live (or other) post-B snapshot would require a **separate RD source decision** and a read-only inventory. It must **not** be silently substituted (E3).

**No blocking ratified decision found.** Velith `DECISIONS.md` names no P4 source; its "P4" in D22 refers to a different, unrelated principle. U-3 sits in a draft specification's decision log and itself requires a new RD decision for any source change.

## 3. Evidence matrix

| Class | Items |
|---|---|
| **Verified documentary facts** | E1–E11. The 320 candidate-bearing repositories. The 60/260 split appears **only** in a draft. P4 cap ≤ 4; confirmatory Cap 1 is provisional (DU-1). The 50-admitted target and the fewer-than-40 failure gate. DE-4 exclusions. The documented SWE-bench-Live end date 2025-08-30 |
| **Derived arithmetic** | 320 − 60 = 260, conditional on the draft frame. P4's survival requirement implied by E6: 50 / 187 ≈ 0.27, or 40 / 187 ≈ 0.21 at the failure gate. Both are conditional on the 187 estimate |
| **Planning assumptions** | **187 capped candidate slots is a planning estimate, not an admitted-task count.** It assumes the capped total spreads in proportion to repository count. The **60/260 split is a draft parameter, not ratified** |
| **Unresolved empirical quantities** | **Admission survival** (chronology E1–E5, environment build, gold Case A) **is unmeasured.** The exact per-repository candidate distribution, which needs the offline export. Whether P4 can reach 40–50 admitted from any frame. The size of the additional repository pool (M_v, unmeasured). Leakage and cross-repository dependence |

**Explicit non-inferences:**
- **Removing 60 repositories does not prove the remaining pool is sufficient.** Stage-1 sufficiency depends on the unresolved D31 planning inputs and on admission survival.
- **The M_v probe** (frozen block `f8a7e398…`; GN1-r1) counts repositories visible to the frozen query beyond run 1's 999. It is a lower bound on that search-visible pool, and only an approximate upper bound on eligible repositories. **It does not establish Stage-1 sufficiency.** Because the run-1 frame lies inside the baseline B0, it doesn't change M_v.

## 4. Exclusions and disjointness (to be made explicit in the next P4 specification)

- **P4 tasks and P4 repositories:** excluded from the confirmatory held-out pool (DE-4). P4 tasks and outputs never enter any arm's memory (D31 item 10).
- **Disjointness:** P4 frame repositories and Stage-1 held-out repositories are disjoint at the repository level. Experience-set repositories are disjoint from held-out repositories (DE-1).
- **M_v condition:** P4 contributes nothing to M_v only while the P4 frame is drawn **entirely** from run 1's 320 candidate repositories, all within B0. Any other pool requires the exclusion accounting to be redone (GN1-r1 item 6).

## 5. Open gates (not resolved by this record)

| Gate | Content |
|---|---|
| G-B1-1 | **Admission survival:** measurement method and authorization (the paused build spike, or P4's own admission step) |
| G-B1-2 | **Frame-size ratification:** the 60/260 split, and the partition design (U-S1, U-S6, U-S7) |
| G-B1-3 | **Stage-1 exclusions:** the exact registry and disjointness rules, P4 versus held-out versus experience |
| G-B1-4 | **DU-1** (Cap 1, provisional) and **DE-2/DE-3** (the experience source and its size) |
| G-B1-5 | **P4 ↔ BRP role:** RD-2 formally applies to the BRP, whose amendment awaits ratification (E10), while `P4_SPEC.md` claims P4 supplies the base rate (E11). The RD-2 representativeness rationale in §1 applies to P4 only if P4 is, or is ruled to be, the base-rate pilot. **Unresolved** |
| G-B1-6 | **Representativeness detail:** P4 samples up to 4 tasks per repository, while the confirmatory set takes 1. This affects how well p0 represents the held-out population. A planning consideration, unresolved |
| G-B1-7 | The source and design of the compatibility check (U-3 / U-S1) under the run-1 direction |
| G-B1-8 | A new P4 specification version incorporating the source direction, which needs separate authorization. The "R + 52" pool condition (E7) depends on the unratified R |
| Unchanged | B-2 (interface), B-3 (temperature) and SM11 (configuration equivalence) are still unresolved |

## 6. Authorization boundaries

**This record authorizes none of the following:**
- task selection, sampling, admission testing or builds;
- the build spike;
- Act B (setting `FROZEN_PROTOCOL_SHA`) or Act C (the live sizing probe), or any network activity;
- model calls;
- edits to any existing specification, the register, GN1 or GN1-r1, the frozen protocol, its marked block, probe code, lock, or the Act-A record;
- commits or pushes.

**Each requires its own explicit RD authorization.**

**Artifacts referenced (unchanged at creation):**

| Artifact | SHA-256 |
|---|---|
| `P4_SPEC.md` | `81af9ad2…` |
| `P4_SOURCE_SCAN.md` | `8fd21bb4…` |
| `P4_SUPPLY_CENSUS.md` | `3831b084…` |
| `P4_BUILD_SPIKE_SPEC_v0.11.md` | `551c3dc2…` |
| Register | `9fadfbcb…` |
| GN1-r1 | `c8941b07…` |
| Frozen protocol | `a34a729d…` (block `f8a7e398…`) |
| Probe code | `0b0584ce…` (lock `None`) |
| Act-A record | `68b6f301…` |
