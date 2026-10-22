# P4 role ruling: operational feasibility/admission only; separate BRP preserved

**Date:** 2026-10-16. **Authority:** Research Director (ChatGPT). **Recorded by:** Chief Systems Engineer (Claude).
**Status:** RD governance ruling, recorded. It edits no existing document and **authorizes no execution, task selection, admission testing, data collection, builds, network requests or model calls.**

## 1. Ruling

1. **P4 is operational-feasibility/admission-only under its current specification.**
2. **A separate Base-Rate Design Pilot (BRP) remains required and is not authorized to execute.**
3. **The BRP must use the production-verifier PASSED endpoint required by RD-2b.** P4's frozen-probe gate and its SVR outcome are **not** substitutes.
4. **Combining P4 and the BRP is not authorized**, and is not to be adopted by implication. It would require a separate, explicit RD/SRC governance decision, and a demonstrated resolution of the endpoint, estimand, sampling, weighting, dependence and configuration-equivalence issues.
5. **The B-1 run-1 source direction remains a direction only.** The 60-repository frame, Cap 1 (DU-1), the experience source and the other open gates remain unratified.
6. **Supersession note.** Interpretation 3 of the CSE's P4 role brief (2026-10-16), "base-rate pilot after redesign + ratification", is **not adopted**. That brief was advisory, and no file recorded it.

## 2. Primary evidence (read-only, 2026-10-16)

| # | Evidence | Class | Citation |
|---|---|---|---|
| P1 | RD-0 = Option (B): "P1 stays feasibility-only … RD-1, RD-2 and RD-2b apply to the new **Base-Rate Design Pilot (BRP)**". Option (b): "define a **separate base-rate design pilot**". The amendment text is **not ratified** | Closed RD ruling (the RD-0 decision); unratified amendment text | `M9-ST1_RD_DECISION_REGISTER.md` L21, L52, L59, L62; `RD-0_C-1_RESOLUTION_AMENDMENT_PROPOSED.md` L1–3 |
| P2 | RD-2b, **CLOSED (Option V)**: "The BRP SHALL obtain p0 from the same PASSED endpoint used by the eventual Stage-1 analysis: material → TaskSpec → proposer → candidate → production verifier (D26) → hash-locked Velith classifier (D27) → PASSED / non-PASSED. The M2 probe PASSED and `patch_applies` are **not** substitutes." Also: "The BRP cannot execute before a validated production verifier exists." Current state: "production verifier **not complete** … BRP … **not authorized**" | Closed RD ruling | Register L96–125 (esp. L98, L111, L123–124); `RD-2b_BRP_VERIFIER_REQUIREMENT_ANALYSIS.md` §9, L151–153 |
| P3 | P4's endpoint: Case A on "the frozen gate"; the primary outcome SVR rests on the gate's VERIFIED_PASS, plus extended regression and no disqualifier | Draft specification | `p4/P4_SPEC.md` L145, L159–163 |
| P4 | The draft claims "P4 supplies the pilot base rate D31 item 8 requires." The spec is "DRAFT v0.2 … Not ratified" | Draft specification (superseded on this point by §1) | `p4/P4_SPEC.md` L196, L3 |
| P5 | D31 item 10: pilot information may inform **design only**, never confirmatory inference, memory or evaluation records; pilot tasks excluded by a frozen, content-addressed registry. Item 8: δ is recorded after the pilot base rate is obtained | Ratified decision | Velith `docs/DECISIONS.md` L730–740 |
| P6 | SM11, configuration equivalence: "The pilot uses the confirmatory A0 configuration". Accepted by the SRC, **awaiting RD freeze** into the successor specification | SRC ruling, not yet frozen | `reviews/src/SRC_2026-09-28_M9-ST1_final_statistical_review.txt` L49–57; `M9-ST1_RD_FREEZE_DECISION_INPUT.md` L23, L37 |
| P7 | RD-1 (pilot size): "A size other than 5 requires the research amendment" (**OPEN**). RD-2 (scope): pilot tasks drawn from the confirmatory population, outcome-blind, permanent exclusion (**OPEN**) | Open RD decisions | Register L64–79, L80–95 |
| P8 | B-2 (Stage-1 interface) and B-3 (generation settings): FG-0b requires ratified D-entries | Draft blockers | `p4/P4_SPEC.md` L13–14, L290 |
| P9 | Rulings of 2026-10-16: DU-1 Cap 1 (provisional); DE-1 repository-disjoint experience; DE-2 pre-B preferred; DE-4 P4 tasks and repositories excluded from held-out | RD rulings (provisional where stated) | `p4/P4_SIZING_PROBE_GOVERNANCE_NOTE_GN1-r1.md` L17–21 |
| P10 | B-1b: a source direction only; open gates G-B1-1 to G-B1-8 | RD source-direction record | `p4/P4_B1_RUN1_SOURCE_DECISION_RECORD.md` §1, L62–69 |

**Deductions:**
- (D1) P3 combined with P2 means P4's current endpoint can't supply a BRP p0.
- (D2) Under DU-1, the confirmatory base rate is a repository-weighted mean. P4's cap-4 walk would estimate a task-weighted mixture of SVR rates (`P4_SPEC.md` L150, L159–166). The estimands differ even setting the endpoint aside.

## 3. What P4 may and may not establish

**P4 may establish**, under its current draft, once a separately authorized specification and execution exist:
- whether the source frame yields eligible tasks under B and E1–E5;
- admission yield under its admission steps;
- operational process checks (gate, adapter, image pinning);
- P4's own feasibility decision code, under its 90% Clopper–Pearson bands (`P4_SPEC.md` L166–184).

**P4 must not claim:**
- a validated Stage-1 base rate, or a planning p0 for SM8/SM10;
- statistical power, n_conf, or Stage-1 sufficiency;
- any confirmatory inference.

P4 tasks and outputs never enter memory or evaluation records (D31 item 10).

## 4. Separate BRP: minimum prerequisites

| # | Prerequisite | Basis |
|---|---|---|
| 1 | Production-verifier PASSED endpoint; a **validated** production verifier must exist before the BRP executes | **Rule:** RD-2b (P2) |
| 2 | Confirmatory A0 configuration equivalence | **SRC ruling awaiting RD freeze:** SM11 (P6). Depends on B-2 and B-3 (P8) |
| 3 | Pilot tasks from the confirmatory population; outcome-blind selection; permanent exclusion | **Open decision:** RD-2 (P7) |
| 4 | Pilot size, with the research amendment if ≠ 5 | **Open decision:** RD-1 (P7) |
| 5 | Ratification of the RD-0 amendment (the BRP itself) | **Unratified amendment** (P1) |
| 6 | Exclusion of BRP tasks from held-out through a frozen, content-addressed registry; design-only use | **Rule:** D31 item 10 (P5) |
| 7 | Repository-level sampling (one pre-declared task per repository, random repository order) and a repository-level 95% CP interval, matching the Cap-1 estimand | **Recommendation** (CSE), conditional on DU-1. Not required by any cited decision |
| 8 | BRP repositories disjoint from held-out and experience repositories | **Recommendation**, by analogy with DE-1 and DE-4. Not explicitly decided for the BRP |

## 5. Minimum decision order (no gate grants permission to proceed)

1. **Finalize the P4 operational specification.** A new version, separately authorized, that:
   - records the operational-only role, removing or qualifying `P4_SPEC.md` L196;
   - adopts the B-1 direction;
   - resolves B-2 and B-3 for P4's configuration.
2. **Decide P4's frame size and source details** (G-B1-2; U-S1, U-S6, U-S7; G-B1-7) and the admission-survival plan (G-B1-1).
3. **Resolve DU-1 and the experience-source exclusions** (G-B1-3, G-B1-4; DE-2, DE-3), and the full exclusion registry across P4, BRP, experience and held-out.
4. **Specify the separate BRP:**
   - ratify the RD-0 amendment;
   - RD-1 and RD-2;
   - freeze SM11;
   - the production-verifier milestones of RD-2b's dependency chain (register L113–115).
5. **Authorize any execution:** P4, the BRP, the sizing probe (Act B / Act C) or the build spike. **Each act is a separate, explicit authorization.**

## 6. Authorization boundaries

This ruling authorizes **none** of:
- execution;
- task selection or sampling;
- admission testing or data collection;
- builds;
- network requests;
- model calls;
- Act B or Act C;
- edits to existing files;
- commits or pushes.

**Artifacts referenced (unchanged at creation):**

| Artifact | SHA-256 |
|---|---|
| `P4_SPEC.md` | `81af9ad2…` |
| Register | `9fadfbcb…` |
| GN1 | `8b7c97cd…` |
| GN1-r1 | `c8941b07…` |
| B-1 record | `9ac0ef91…` |
| Frozen probe protocol | `a34a729d…` (block `f8a7e398…`) |
| Probe code | `0b0584ce…` (lock `None`) |
| Act-A record | `68b6f301…` |
| Velith `DECISIONS.md` | `54e5331d…` |
