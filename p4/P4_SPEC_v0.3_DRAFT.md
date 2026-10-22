# M2-PV-P4: operational feasibility and admission pilot (SPECIFICATION DRAFT v0.3, UNRATIFIED)

**Status:** DRAFT v0.3, 2026-10-16. **Unratified.**
- Drafting is authorized by the RD (2026-10-16). **Nothing in this document authorizes implementation, execution, sampling, admission testing, data collection, network access, model calls, builds, commits or ratification.**
- It supersedes conflicting language in `p4/P4_SPEC.md` v0.2 (SHA `81af9ad2…`) **only for the purposes of this draft**. v0.2 is unchanged.

**Status labels used throughout:**

| Label | Meaning |
|---|---|
| **[RATIFIED]** | A decision in Velith `docs/DECISIONS.md` |
| **[CLOSED RULING]** | A closed RD ruling |
| **[PROVISIONAL RD]** | A provisional RD ruling |
| **[RD-v0.2]** | An RD decision recorded in the unratified v0.2 decision log (`P4_SPEC.md` L4, L312–323) |
| **[DRAFT]** | A draft proposal |
| **[UNRESOLVED]** | An open decision |
| **[UNMEASURED]** | An empirical quantity not yet measured |

**Governing RD rulings (2026-10-16):**

| # | Ruling | Status | Source |
|---|---|---|---|
| G1 | P4 is operational feasibility and admission only | [PROVISIONAL RD] | `p4/P4_ROLE_RULING_SEPARATE_BRP.md` §1 (L6–14) |
| G2 | A separate Base-Rate Design Pilot (BRP) is required. P4's frozen-gate/SVR result is never the validated Stage-1 base rate or the SM8 planning p0 | [PROVISIONAL RD], resting on [CLOSED RULING] RD-2b | Role ruling §1, §3 (L34–47); `M9-ST1_RD_DECISION_REGISTER.md` L96–125 |
| G3 | B-1b: prefer the run-1 post-cutoff candidate-repository frame. Direction only | [PROVISIONAL RD] | `p4/P4_B1_RUN1_SOURCE_DECISION_RECORD.md` §1 (L7–15) |
| G4 | The 60-repository frame is not ratified | [UNRESOLVED] | B-1 record §5, G-B1-2 (L63) |
| G5 | Cap 1 for the confirmatory held-out sample | [PROVISIONAL RD] (DU-1) | `p4/P4_SIZING_PROBE_GOVERNANCE_NOTE_GN1-r1.md` L18 |
| G6 | B = 2026-08-01, never weakened | [RD-v0.2] U-2 | `P4_SPEC.md` L49, L317 |
| G7 | D31 pilot-information restrictions; DE-4 exclusions | [RATIFIED] D31 item 10; [PROVISIONAL RD] DE-4 | Velith `DECISIONS.md` L738–740; GN1-r1 L21 |
| G8 | The sizing-probe artifacts are untouched; Act B and Act C are not authorized | — | `p4/P4_SIZING_PROBE_FREEZE_RECORD_ACT_A.md` |

## 1. Purpose and non-purpose

**Purpose** (G1):
- to establish whether the B-1 run-1 frame can supply eligible and admitted tasks under the frozen cutoff;
- to exercise the operational chain: chronology checks, exclusions, environment construction, gold Case A on the frozen gate, the interface, the adapter and the registry;
- optionally (§8, [UNRESOLVED]), to run a **generator-viability screen** on the frozen-gate SVR endpoint.

**Non-purpose. P4 does not and must not:**
- supply or claim the validated Stage-1 base rate, the SM8/SM10 planning p0, statistical power, n_conf, N_avail, or Stage-1 sample sufficiency;
- produce any confirmatory inference;
- serve as, or substitute for, the BRP (G2; RD-2b).

P4 tasks and outputs never enter any arm's memory or any evaluation record (D31 item 10).

**This replaces v0.2's statement** "P4 supplies the pilot base rate D31 item 8 requires" (`P4_SPEC.md` L196), for this draft only.

## 2. Generator (relevant to §8 only)

- **[RD-v0.2] U-1:** `claude-opus-5-5`, with recording and stop rules as in `P4_SPEC.md` L25–45 (unchanged).
- Used **only** by the optional §8 screen.
- **D8.1 context** ([RATIFIED] `DECISIONS.md` L186: "deliberately non-saturating base model"): §8's CEILING band detects saturation risk. Whether this generator satisfies D8.1 is **not** decided here.

## 3. Chronological eligibility ([RD-v0.2] U-2)

- **Unchanged from `P4_SPEC.md` L47–68:** B = 2026-08-01T00:00:00Z. A task is eligible only if **every** timestamp (issue, PR opened, earliest commit, merge, base commit) is ≥ B, and exclusions E1–E5 apply.
- **Base-commit definition: [UNRESOLVED].** The census approximates the base commit by the `compare` merge base (`P4_SUPPLY_CENSUS.md` L40, L196). The task's base commit, either the merge base or the PR `baseRefOid`, must be fixed before the FG-1 inventory.

## 4. Source frame and the task ladder

**Source: [PROVISIONAL RD] G3.** Census run 1 (frozen protocol `a642efdb…`; T_SEL 2026-10-12T07:55:04Z). Universe: 1,000 searched, 589 kept, **320 repositories with ≥ 1 candidate** (`P4_SUPPLY_CENSUS.md` L87, L109).

**The ladder** (each stage only removes; no stage's count implies the next):

| Stage | Definition | Count | Status |
|---|---|---|---|
| Candidate repositories | Run-1 repositories with ≥ 1 F5 candidate | 320 | Documented |
| Candidate tasks | Census F5 PRs (metadata only) | 10,245 raw; 996 at ≤ 4 per repository | Documented; `P4_SUPPLY_CENSUS.md` L113–118 (raw), L142–147 (capped) |
| Eligible tasks | Candidate tasks passing §3 in full (E1–E5, base commit) | — | **[UNMEASURED]**. "No task is selected, admitted or eligible" from the census (L197) |
| Admitted tasks | Eligible tasks passing §7 | — | **[UNMEASURED]** |
| Verified outcomes | §8 SVR / gate results | — | **[UNMEASURED]**; operational results only |

**Frame size: [UNRESOLVED] (G4).** The 60/260 split appears only in the draft spike spec (`P4_BUILD_SPIKE_SPEC_v0.11.md` L157, L200). The planning figure "C_F ≈ 187" (L232) is an **estimate of capped candidate slots, not admitted tasks**.

**Partition design: [UNRESOLVED].** U-S1, U-S6 and U-S7 (draft spike spec). Requirements once decided:
- the frame is a repository-level subset of the 320;
- it is drawn by a frozen, pre-declared lottery before any eligibility or admission check;
- it is disjoint from the confirmatory held-out repositories (DE-4) and from experience repositories (DE-1, §9).

**Pool condition: [DRAFT; UNRESOLVED].** v0.2 requires N_eligible ≥ R + 52 (`P4_SPEC.md` L83). R is unratified, so this condition can't be evaluated. Its form under the run-1 direction must be re-decided: whether it applies to the frame, to the whole frame plus reserve, and to which stage of the ladder.

**Compatibility check: [UNRESOLVED]** (U-S1 / G-B1-7). v0.2's 2-task design (L94) assumed SWE-bench-Live images.

## 5. Eligibility inventory (FG-1 analogue; needs separate authorization)

- For every candidate task in the P4 frame, apply §3. E1–E3 require `git` history over all refs of each upstream repository, and the chronology timestamps require API reads.
- **Both need network access, so they need a separate authorization.**
- **Output:** a pool manifest giving the frozen census identity, per-task chronology evidence (hashed), exclusion verdicts, and the eligible count. **No estimate is assumed.**

## 6. Interface, settings and equivalence

- **B-2 ([UNRESOLVED], blocking).** "P4 uses exactly the input interface Stage 1 will use. That interface does **not** yet exist" (`P4_SPEC.md` L98–108). It must be gold-blind (D28 D-2), deterministic, budgeted, and identical to Stage 1. It must be ratified as a Velith decision before frame selection (FG-0b, L290).
- **B-3 ([UNRESOLVED], blocking for §8).** D31 item 7 (T = 0.0) cannot hold for this generator (`P4_SPEC.md` L121–124; `DECISIONS.md` L727–729). A new decision is required.
- **SM11.** Configuration equivalence binds the **base-rate pilot** (SRC review L49–57; awaiting RD freeze, `M9-ST1_RD_FREEZE_DECISION_INPUT.md` L23, L37). For P4, the operative requirement is [RD-v0.2] U-4, "identical to Stage 1" (L108). **P4's compliance with U-4 does not make it the BRP.**

## 7. Admission and selection

- **Environment construction: [UNRESOLVED].** v0.2 assumed per-task SWE-bench-Live images pulled by digest (L142–143). The run-1 frame has **no pre-built images**. A construction method must be specified, for example an agentic builder (draft spike spec, U-S3, which excludes the generator under test). Its identity and pinning rules must be specified too.
- **Admission criteria** (adapted from `P4_SPEC.md` L142–149; [DRAFT]). A task is admitted only if all hold:
  1. its environment is constructed and pinned by digest;
  2. the spec is built;
  3. **Case A:** the gold patch PASSES the frozen gate;
  4. the base blob equals the working tree for the files the interface reads (depends on B-2);
  5. the prompt fits the token budget (depends on B-2);
  6. the leakage audit passes (depends on B-2);
  7. chronology eligibility is re-confirmed.
- **Selection: [DRAFT]**, from v0.2 L150: a frozen-order walk over the frame, **≤ 4 admitted tasks per repository**, no backfill, until **n = 50** are admitted.
  - The cap-4 policy is a P4 admission rule. It is **not** the confirmatory Cap 1 (G5), and it is not ratified.
- **Gates: [DRAFT]**, from v0.2 L151–153:
  - **P4-POOL-INSUFFICIENT** if fewer than 40 are admitted (or the pool condition of §4 fails, once it is re-decided);
  - **P4-D**: void for infrastructure reasons.
- **Admission-survival measurement: [UNRESOLVED prerequisite]** (G-B1-1). Choose either the paused build spike or this admission stage itself as the measurement.
  - **No survival rate is assumed.** The observed admission yield is an **operational test result**, not a population estimate for Stage 1.

## 8. Optional generator-viability screen ([UNRESOLVED]: retain or exclude)

- **If retained, as in v0.2 L155–196:**
  - one generation per admitted task under the frozen settings;
  - primary outcome SVR on the frozen gate;
  - the [RD-v0.2] U-6 bands (90% Clopper–Pearson; floor 0.10, ceiling 0.80);
  - the [RD-v0.2] U-7 stop at n = 50;
  - the semantic rubric, verifier image and contamination audit as in v0.2 §9–§11 (L198–248), unchanged.
- **Its output is a generator-viability code** (INFEASIBLE / INCONCLUSIVE / FEASIBLE / CEILING) on the frozen-gate endpoint. It is **not** a PASSED rate. It is **not** a base rate, a planning p0, a power or n_conf input, or a Stage-1 result.
  - The endpoint differs from RD-2b's production-verifier PASSED.
  - The estimand is task-weighted at cap 4, while Stage 1 is repository-weighted at Cap 1 (role ruling §2, D1–D2).
- **If excluded,** P4 ends at admission (§7), and no model call is ever needed.

## 9. Exclusions and registry (prerequisite; does not yet exist)

- **[RATIFIED] D31 item 10:** pilot information is design-only. It never enters confirmatory inference, memory or evaluation records. Pilot tasks are excluded through a **frozen, content-addressed exclusion registry**.
- **[PROVISIONAL RD] DE-4:** P4 tasks **and** P4 repositories are excluded from the confirmatory held-out pool.
- **[PROVISIONAL RD] DE-1:** experience repositories are disjoint from held-out repositories.
- **[DRAFT] recommendation:** also exclude P4 repositories from the experience set. DE-4 covers held-out only.
- **Registry requirements: [UNRESOLVED].** It must be content-addressed (task identity plus repository identity), cover every P4 task touched, and be frozen before any partition is sealed and before any Stage-1 pre-registration.
  - It **does not yet exist.** Enforcement is procedural today (register §5 item 3, L316).
  - Building it is a prerequisite to ratification.

## 10. Separate BRP (not part of P4)

- **[CLOSED RULING] RD-2b:** the BRP obtains p0 from the production-verifier PASSED endpoint (production verifier (D26) → hash-locked classifier (D27)). "The M2 probe PASSED and `patch_applies` are **not** substitutes." "The BRP cannot execute before a validated production verifier exists" (register L98, L111; `RD-2b_BRP_VERIFIER_REQUIREMENT_ANALYSIS.md` L151–153).
- The BRP's specification and authorization are **outside this document** (role ruling §4, L49–60).

## 11. Budget and stops

- **Admission phase:** environment-construction cost and time are **[UNMEASURED]**. Caps must be set in the execution authorization.
- **§8, if retained:** v0.2 L250–272 (API cap $20; model-identity stop; frozen-SHA stops).
- **Any write to frozen evidence is a stop.** That includes the census, P1–P3, the sizing-probe artifacts and the `m0` image.

## 12. Decisions required before ratification

| # | Decision | Depends on |
|---|---|---|
| R1 | B-2: the Stage-1 interface (a Velith D-entry) | — |
| R2 | B-3: generation settings (a Velith D-entry); needed only if §8 is retained | — |
| R3 | Retain or exclude §8 | G1, G2 |
| R4 | Frame size and partition design (G-B1-2; U-S1, U-S6, U-S7) | B-1 |
| R5 | Base-commit definition (§3) | — |
| R6 | Environment-construction method and pinning (§7; U-S3) | R4 |
| R7 | Admission-survival measurement plan (G-B1-1) | R6 |
| R8 | Re-decide the pool condition (§4); R | Stage-1 planning (U-R) |
| R9 | The exclusion registry (§9; G-B1-3), including P4-repository exclusion from experience | DU-1, DE-1, DE-2 |
| R10 | Compatibility check (G-B1-7) | R4, R6 |
| R11 | Confirm DU-1 (Cap 1) and DE-2/DE-3 | — |

## 13. Separate authorizations required before any execution

Each act below needs its own explicit RD instruction. **None is granted here.**
1. Ratification of this specification.
2. The FG-1 eligibility inventory (network, clones).
3. The partition lottery.
4. Environment construction and admission.
5. §8 generation (model calls), if retained.
6. Commits and pushes.

The sizing-probe Acts B and C, the build spike and the BRP are separate matters.

## 14. Claim classes

| Class | Meaning | Examples |
|---|---|---|
| **Draft proposal** | A design choice in this document | The cap-4 walk; the 50/40 gates; the §8 module |
| **Ratified decision** | A Velith DECISIONS entry | D31 items 7–10; D8.1; D28 D-2 |
| **Operational test result** | A measured count from an authorized run, valid for that run | Eligible count; admission yield; §8 code |
| **Scientific inference** | A population-level claim. **P4 makes none about Stage 1** | — |

## 15. Change log v0.2 → v0.3

**Changes:**
- Role restricted to operational feasibility and admission (G1, G2).
- The base-rate claim at L196 removed.
- Source direction changed to the run-1 frame (G3), with the frame size unresolved (G4).
- The task ladder made explicit.
- The base-commit definition and environment construction marked unresolved.
- §8 made optional and relabelled.
- The registry made a prerequisite.
- The separate BRP referenced.
- Status labels added.

**Unchanged in substance:** B and E1–E5; the generator pin; the interface requirements; the admission criteria (adapted to built environments); the 50/40 gates and the U-6/U-7 bands (as drafts).
