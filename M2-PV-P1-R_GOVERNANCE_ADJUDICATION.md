# M2-PV-P1-R — Governance Adjudication (R-1 Stage-1 definition; R-2 real-task verifier ownership)

**Document type:** Read-only forensic governance audit (research workspace). **Not a decision. Not an amendment. Not an implementation authorization.**
**Author:** Chief Systems Engineer. **Requested by:** Research Director.
**Date:** 2026-09-28.
**Scope:** the two governance contradictions surfaced by `M2-PV-P1_PILOT_DESIGN.md`: R-1 (Stage-1 arm set) and R-2 (real-task verifier ownership after D30).

Evidence classes used in every conclusion:

| Tag | Meaning |
|---|---|
| **[FROZEN]** | A frozen specification (freeze tag or freeze commit), or the ratified constitution itself. |
| **[RATIFIED]** | An `Accepted` numbered decision in a `DECISIONS.md`, or a Research-Director-ratified record. |
| **[IMPL]** | Code, tests or git state, as observed at the baseline. |
| **[DRAFT]** | A research or draft document with no ratification. |
| **[INFERENCE]** | This audit's reasoning from the above. It is never presented as a record. |

---

## 1. Status

- **R-1: CONTRADICTION CONFIRMED. UNRESOLVED. BLOCKING for any real M10 execution.**
  - `DECISIONS.md` defines Stage 1 as **A0 vs A2**.
  - The frozen M9 specification and the M10 executor implement a **three-arm ordered go/no-go** (A1 > A0 and A2 > A1).
  - No record supersedes either one.
- **R-2: NO GOVERNANCE CONTRADICTION.**
  - Ownership is determined by the ratified constitution: Velith owns the oracle, Noetica owns the protocol.
  - D30 is ratified and supersedes nothing.
  - D30 does add binding obligations that the DRAFT M2-PV specification does not yet satisfy. Those obligations extend BC-2; they are not a new contradiction.
- **Pilot M2-PV-P1:** remains **BLOCKED** on its own gates (PB-1 harness authorization; OD-1 to OD-12). Neither R-1 nor R-2 blocks it, and neither unblocks it.
- **Nothing in any repository was modified by this audit.** The only artifact created is this file.

## 2. Repository baseline

**Engineering repository:** `E:\Projects\OpenSourceLab\repos\Velith`

- **HEAD = origin/main:** `0d247d982e48b30febe2fb53405e1c6d1ba29960`, 2026-09-28 02:38 +0530, "docs(governance): D30 adopts ecosystem Handbook v1.1…".
- **Working tree:** clean. `git status --porcelain` is empty; only ignored caches exist.
- **Relevant tags:**
  - `m7-complete` → `9e6f90f` (2026-07-25)
  - `m8-complete` → `fe2b3d7` (2026-08-02)
  - `m9-spec-frozen` → `36659cb` (2026-09-17)
  - `m9-complete` → `a218bca` (2026-09-23)
  - `m8-identity-v2-frozen` and `m9-spec-frozen-oed7-vm2` → `1b0b7a0` (2026-09-25)
- **`5476d82` (C-ID):** contained in `origin/main`.

**Ecosystem repository consulted for R-2:** `E:\Projects\OpenSourceLab\repos\Noetica-agent-lab`

- **HEAD:** `44d380bdcadf50fec463c2840bc5d181d7e7e0f7`, 2026-09-28 10:46 +0530, "release: publish Noetica as … `noetica` 1.0.0 (DN-9)".
- **Tag `v1.0.0`:** points to `44d380b`.
- **Refs:** the local ref `origin/main` contains `44d380b`.
- **Remote tag:** whether `v1.0.0` exists on the remote was **not verified**, because the sandbox has no network access.

**SHA-256 of the key inspected files:**

| File | SHA-256 |
|---|---|
| Velith `docs/DECISIONS.md` | `0b17d0322d6b9585de830237f3581c022f2ede6f9ceb7981c85e8d54671fd982` |
| Velith `docs/M9_SPEC.md` | `94dbdb9e075c5025f40b4e70305b74324971ae35439e5ca7a7a0f28370d1434e` |
| Velith `docs/M8_SPEC.md` | `9ddd16d881d7a6123897859ede95d719a8c123ba06b9a6c5337e41bd5db1c093` |
| Velith `docs/M7_SPEC.md` | `a481e64d20dc1115fc170a609a955ec819ffc05dde74b970dc3c08f6088b7f1e` |
| Velith `docs/M8_IDENTITY_V2_SPEC.md` | `746be5770993b51ad22f71a217f3108aeeab910d73f288dcf811132df4f5285a` |
| Velith `docs/M9_IMPLEMENTATION_HANDOFF.md` | `16c5ade045dbb0e78572a742e4f9555b049f522056dda9e6fc5e297094aa509b` |
| Velith `docs/PROJECT_STATE.md` | `c7a3becf43492e58e08237d1a5ffbe1fd502e6c91e33e160a4d3732d55103d2f` |
| Velith `src/velith/analysis/preregistration.py` | `57cdcaccb236d92b1406d2e29ec193b506692858ba34b2941b0907a606dd9741` |
| Velith `src/velith/analysis/executor.py` | `72ea5f67b006c1ba2e66b8d7c0a55c86bff1ac58a0fbd42f5bdaa43f134fc9e5` |
| Velith `src/velith/analysis/decision.py` | `5c159cbb0d50fed2e7c909e06e33983df1e30417abcdcc49795beaa1a70b02b7` |
| Velith `src/velith/evaluation/attempt.py` | `23cd1284961ace738ac6f89c3bb70fb99ccd47f8a443a25f4c15ec3e121d0528` |
| Velith `src/velith/batch/runner.py` | `1a31ecc48e3d49580a6fd981db5478540729efea8c726abd15a4c8d7a89c433b` |
| Velith `src/velith/harness/verifier_sandbox.py` | `698a21cdd9e60b660c80195e87ed210242071a67fa0b48f7e49a05077316b707` |
| Velith `src/velith/arms/identity.py` | `fc40d0b2e1ee92abfdc2e079b8655eedf24f622db9c3ef4edf2dab398dae7256` |
| Noetica `docs/constitution/HANDBOOK_v1.1.md` | `ad670d24eaab6acb2cca301223dfb58d9216b6ee89e87fd569638af3a00eafd0` (equal to the hash pinned by Velith D30) |
| Noetica `docs/decisions/DECISIONS.md` | `ab79cfc133d40ff3e280bd860d6507317dd6f37acd0fbc1395ed79cb439d76ef` |
| Noetica `src/noetica/interfaces/verification.py` | `828b7d664cede8a21d9276157f48a1b9856ccbad7193c85494542e8069c686bc` |
| Noetica `src/noetica/interfaces/provenance.py` | `02545bd4a2da6094924bc4993dfdc1272f51daeed135d2d58ab3a3036d7a0c42` |

## 3. Source hierarchy

The hierarchy is **not** chosen by this audit. It is read from the repositories.

**H-1 — The constitutional order [RATIFIED].**
- Velith D30.1 (`DECISIONS.md:661`) adopts Handbook v1.1 as Velith's governance, pinning SHA `ad670d24…`.
- Handbook P.2 (`HANDBOOK_v1.1.md:74–81`) fixes the order:
  1. the Handbook;
  2. the Decision Record `DECISIONS.md`;
  3. `VISION.md`;
  4. the scientific corpus;
  5. roadmaps, milestone specifications and project-state records ("must conform to everything above");
  6. code.

  The same section adds (`:83`): "No artifact below the Handbook may weaken a boundary the Handbook establishes."

**H-2 — The amendment rule [RATIFIED].**
- `DECISIONS.md:5`: "A ratified decision is changed only by a new dated entry that explicitly supersedes the prior one." The procedure is at `:679–686`.
- Handbook P.4 (`:97`): a genuine contradiction "is never resolved by quietly preferring one document".

**H-3 — Frozen specifications [FROZEN].**
- Each specification declares itself immutable once frozen (for example `M9_SPEC.md:10–12`) and is changed only by a versioned amendment.
- Specifications are at level 5, so they must conform to `DECISIONS.md`. A frozen specification cannot supersede a decision.

**H-4 — Implementation [IMPL].** Level 6. Code conforming to a frozen specification inherits that specification's standing, and no more.

**H-5 — The research workspace (`Velith-research`).** It is outside the repository hierarchy.
- An RD-ratified research record (for example `M2-PV-R_ARCHITECTURE_RATIFICATION_AMENDMENT.md`) binds the program's process by RD authority. It is **not** a `DECISIONS.md` entry.
- Its own enactment note says entering decisions into `DECISIONS.md` "each need a separate authorization". D26–D28 were so entered; the pilot sequencing (record `:272`, `:403`) was not.
- DRAFT research documents have no authority.

**Ordering applied below [INFERENCE, directly from H-1 to H-5]:**

Handbook > Velith `DECISIONS.md` (D1–D30) > frozen specifications (M7, M8, M8-IDv2, M9 VM2) > implementation handoffs > code > RD-ratified research records (process only) > DRAFT research.

## 4. R-1 evidence

| # | Path : line | Identifier | Status / class | Relevant wording | Supersedes |
|---|---|---|---|---|---|
| E1 | `docs/DECISIONS.md:148` | D6 H1 | Accepted [RATIFIED] | A2 "strictly higher held-out pass-rate… than (a) the same agent at episode 0, **and** (b) control agents… *without* the verification filter" | — |
| E2 | `docs/DECISIONS.md:170` | D7 | Accepted [RATIFIED] | "The decisive criterion is **A2 strictly beats A1**." | — |
| E3 | `docs/DECISIONS.md:186` | D8.2 | Accepted [RATIFIED] | "Pre-registration freeze of N, seed count, minimum effect size, exact arm contrasts, and metrics… before the first real Stage-1 run." | — |
| E4 | `docs/DECISIONS.md:189` | **D8.5** | Accepted [RATIFIED] | "**Stage 1 (A0 vs A2)** is a cheap go/no-go; **Stage 2 (add A1, A3)** is the decisive run… A Stage-1 win is… necessary-but-not-sufficient" | — |
| E5 | `docs/DECISIONS.md:194` | D8 Consequences | Accepted [RATIFIED] | "The harness is built to run all arms from the start (staging is a scheduling/spend decision, not an architectural one). Pre-registration is written against a running harness… (gate at roadmap M9)." | — |
| E6 | `docs/DECISIONS.md:254` | **D12** | Accepted [RATIFIED] | M7 = "A1/A2 write-filter policies"; M9 = "the **Stage-1 orchestrator + full A0/A2 run**"; M10 = "Stage-1 statistics + go/no-go report" | — |
| E7 | `docs/DECISIONS.md:260` | D12 Consequences | Accepted [RATIFIED] | "**Stage 2 (A1/A3)**… specified… *only after* M10's go/no-go verdict" | — |
| E8 | `docs/DECISIONS.md:315` | D15 | Postponed by design [RATIFIED] | "Stage 2 / ablation / replication milestone details — specified only after M10's verdict (D12)." | — |
| E9 | `docs/DECISIONS.md:624–626` | D29.10 | Accepted [RATIFIED] | "M9 statistical formulas and decision rules are unchanged… This decision changes identity and version plumbing, not statistical inference." | M8 v1 identity only |
| E10 | `docs/DECISIONS.md:658, :671` | D30 | Accepted [RATIFIED] | "Supersedes: nothing. D1–D29 remain in force exactly as written"; "**D12** (M0–M10 roadmap; M10 = Stage-1 statistics and go/no-go) remain[s] in force" | nothing |
| E11 | `HANDBOOK_v1.1.md:780` | Handbook §5.6 | RATIFIED [FROZEN] | "Staged spending. A cheap go/no-go stage precedes the decisive run; a stage-1 win is necessary but not sufficient". It names no arm set. | — |
| E12 | `HANDBOOK_v1.1.md:984` | Handbook §7.6 | RATIFIED [FROZEN] | "The decisive criterion is **A2 strictly beats A1**." | — |
| E13 | `docs/M1_IMPLEMENTATION_HANDOFF.md:403` | M1 handoff | frozen handoff [FROZEN] | "M9–M10: experiment orchestrator; **A0/A2 runs**; statistics; go/no-go report; pre-registration freeze." | — |
| E14 | `docs/M5_SPEC.md:48` | M5 | frozen [FROZEN] | "honoring D8's staged-spending discipline (Stage 1 is a cheap go/no-go)" | — |
| E15 | `docs/M7_SPEC.md:1, :44, :65` | M7 | frozen at `m7-complete` [FROZEN]. The header's "DRAFT" label is stale, as D29 records for M8. | Closed M7 set A1, A2 | — |
| E16 | `docs/M8_SPEC.md:1, :31, :232` | M8 v1 | frozen at `m8-complete`; the "DRAFT" header is stale per D29 (`DECISIONS.md:593`) [FROZEN] | "each of **A0, A1, and A2** is evaluated on the held-out partition" | — |
| E17 | `docs/M9_SPEC.md:12` | M9 VM2 | FROZEN (`m9-spec-frozen-oed7-vm2`) [FROZEN] | Governing decisions (`:17`) list D8, D12 and D15. **No supersession of D8.5 or D12 is declared.** | prior M9 freezes only |
| E18 | `docs/M9_SPEC.md:140` | M9 §3.1 | [FROZEN] | "the **arms** (the closed set A0, A1, A2)" | — |
| E19 | `docs/M9_SPEC.md:108, :217–222` | M9 §2, §3.5.2 | [FROZEN] | `H_a: P(A2) > P(A1) > P(A0)`; `H_a1`: "A1 is superior to A0…"; `H_a2`: "A2 is superior to A1…" | — |
| E20 | `docs/M9_SPEC.md:261–267` | M9 §3.5.5 (K = 1) | [FROZEN] | "two exact one-sided McNemar tests… `H_a1: P(A1_pass) > P(A0_pass)` and `H_a2: P(A2_pass) > P(A1_pass)`… GO requires **both**" | — |
| E21 | `docs/M9_SPEC.md:269–280` | M9 §3.5.6, §3.5.8 (K > 1) | [FROZEN] | Four-test family: EMM A1 vs A0, trend A1 vs A0, EMM A2 vs A1, interaction A2 vs A1; "**GO iff all four**" | — |
| E22 | `docs/M9_SPEC.md:65` | M9 VM2 block | [FROZEN] | "Explicitly not changed…: **The arms**" | — |
| E23 | `docs/M9_SPEC.md:395` | M9 §8 | [FROZEN] | "Stage-1 statistics and the go/no-go decision are M10" | — |
| E24 | `src/velith/analysis/preregistration.py:56` | M9-C2 | [IMPL] | `ARMS = (A0, A1, A2)` | — |
| E25 | `src/velith/analysis/executor.py:201–205` | M10-C1 | [IMPL] | rejects any pre-registration whose arms are not `ARMS` | — |
| E26 | `src/velith/analysis/executor.py:246–253` | M10 K = 1 branch | [IMPL] | McNemar A1 > A0 and A2 > A1 only | — |
| E27 | `src/velith/analysis/decision.py:56–59` | M9-C7 | [IMPL] | `K1_ORDERED_COMPARISONS = ((A1, A0), (A2, A1))` | — |
| E28 | `tests/unit/test_m9_statistics_unchanged.py:20–30` | C-ID | [IMPL] | the nine statistics modules, including `decision.py`, are byte-pinned to `1b0b7a0` | — |
| E29 | repository-wide search of `src/` and `docs/` | — | [IMPL] | **no test, estimand or decision rule compares A2 with A0** | — |
| E30 | `docs/PROJECT_STATE.md:128–130` | status | living record [IMPL-status] | "M10 — in progress… No real M8 evaluation, M9 pre-registration or M10 analysis artifact exists" | — |

## 5. R-1 chronology

| Date | Commit / tag | Event | Class |
|---|---|---|---|
| 2026-06-21 | `0780a52` | D8.5 and D12 recorded. Text identical to HEAD (verified: "Stage 1 (A0 vs A2)" present at both `0780a52` and `1b0b7a0`). | [RATIFIED] |
| 2026-06-24 | `cc4a1b4` | M1 handoff restates "A0/A2 runs" for M9–M10 (E13). | [FROZEN] |
| 2026-07 | M5 freeze | M5 cites "Stage 1 is a cheap go/no-go" (E14). | [FROZEN] |
| 2026-07-25 | `m7-complete` | A1/A2 write-filters frozen. Consistent with D12 M7 and D8 Consequences. | [FROZEN] |
| 2026-08-02 | `m8-complete` | Held-out evaluation of A0, A1 and A2. Consistent with D8 ("harness… all arms from the start"). | [FROZEN] |
| **2026-09-17** | **`36659cb` `m9-spec-frozen`** | **First divergence.** The pre-registered arm set and go/no-go rule become A0/A1/A2 with `H_a1` and `H_a2` (verified present at `36659cb`). No `DECISIONS.md` entry accompanies it. | [FROZEN] |
| 2026-09-18 | `3d98a84`, `c33cbb9` | OED-2 and OED-7 re-freezes. Arms and GO structure unchanged. | [FROZEN] |
| 2026-09-23 | `e04d7f9`; `a218bca` `m9-complete` | M10 executor enforces `ARMS`. M9 closed with no "full A0/A2 run" (see F-R1.4). | [IMPL] |
| 2026-09-25 | `1b0b7a0` | D26–D29 and VM2. D29.10 and VM2 explicitly leave the arms and the statistics unchanged. | [RATIFIED] / [FROZEN] |
| 2026-09-26 | `5476d82` | C-ID byte-pins the statistics modules. | [IMPL] |
| 2026-09-28 | `0d247d9` | D30 reaffirms D12 in force and supersedes nothing. | [RATIFIED] |

## 6. R-1 supersession analysis

- **S-R1.1 [RATIFIED].** No `DECISIONS.md` entry names D8 (item 5), D12 or D15 as superseded.
  - D16 is limited to M1 (`:326`: "None supersedes or alters D1–D15").
  - D23 freezes M4.
  - D26 supersedes D19 only (scoped).
  - D29 supersedes the M8 v1 identity only.
  - D30 supersedes nothing.
- **S-R1.2 [FROZEN].** `M9_SPEC.md` cites D8, D12 and D15 as *governing* (`:17`). It does not claim to supersede them and contains no amendment block about staging. Its amendments (OED-2, OED-7, VM2) are scoped elsewhere, and VM2 states that the arms are unchanged (E22).
- **S-R1.3 [INFERENCE from H-1 to H-3].** A frozen specification is level 5 and cannot supersede a level-2 decision. Code is level 6 and cannot either (H-4). The M9 and M10 three-arm go/no-go therefore has **no authority to redefine Stage 1**. It is a **non-conforming frozen artifact**, not a superseding one.
- **S-R1.4 [INFERENCE] — A1's presence is not the violation; A1's role in the go/no-go is.**
  - D8 Consequences (E5) and D12 M7 (E6) make A1 part of the ratified *harness*. So M7, M8, and M9 pre-registering A1 *as a measured arm* conforms.
  - What does not conform is the **Stage-1 decision rule**:
    - D8.5 fixes the Stage-1 go/no-go contrast as **A0 vs A2**, with A1 entering in Stage 2 as part of the decisive run.
    - M9 makes the go/no-go **A1 > A0 ∧ A2 > A1** (E19–E21). That rule (i) includes D7's decisive Stage-2 contrast (A2 > A1), (ii) adds A1 > A0, which no decision requires (D6 H1 does not require A1 > A0; E1), and (iii) never tests A2 vs A0 (E29).
  - These are two **different decision functions**, not a refinement of one by the other. Example: a population with A2 ≫ A1 ≈ A0 satisfies D6 H1 and would pass a D8.5 Stage 1 ("GO"), but the frozen M9 rule returns NO-GO because `H_a1` fails.

## 7. R-1 determination

- **A. What Stage 1 means in the authoritative architecture [RATIFIED].** The cheap go/no-go comparing **A0 with A2** (D8.5, E4), run as "the Stage-1 orchestrator + full A0/A2 run" (D12 M9, E6), with statistics and the go/no-go in M10 (D12, E6; reaffirmed by D30, E10).
  - The Handbook fixes staging only generically (E11), so it does not alter this.
  - A Stage-1 win is necessary-but-not-sufficient (D8.5).
- **B. A0/A2 or A0/A1/A2?**
  - Under the authoritative record: **A0/A2** [RATIFIED].
  - Under the frozen M9 specification and the M10 code: **A0/A1/A2**, with GO = A1 > A0 ∧ A2 > A1 [FROZEN] [IMPL].
  - These are **contradictory**. Under H-1 to H-4, the ratified A0/A2 definition governs.
- **C. Is A1 part of the frozen evaluation pipeline?** **Yes** [FROZEN] [IMPL].
  - A1 is frozen in M7, M8 and M9, and enforced in M10 code (E15–E18, E24–E27).
  - This is conforming *as harness* (D8 Consequences), and non-conforming *as a Stage-1 go/no-go term* (S-R1.4).
- **D. Which decision establishes the meaning?** **D8 item 5**, restated operationally by **D12** and protected by D15 [RATIFIED].
- **E. Does any later record formally supersede it?** **No** (S-R1.1, S-R1.2) [RATIFIED] [FROZEN]. Two later ratifications passed over the divergence without addressing it:
  - D29 and VM2 (2026-09-25) explicitly preserved the arms and the statistics;
  - D30 (2026-09-28) explicitly preserved D12.
- **F. Is an amendment required?** **Yes** [INFERENCE from H-2].
  - The frozen executor cannot produce a D8.5 Stage-1 result: it rejects two-arm pre-registrations (E25) and computes no A2-vs-A0 statistic (E29).
  - The authoritative record forbids treating the frozen three-arm result as the Stage-1 result without a superseding entry.
  - Neither side may be edited in place. **R-1 is BLOCKED pending a Director ruling** (§14).

**Additional R-1 findings (recorded, not adjudicated here):**

- **F-R1.4 [IMPL] [RATIFIED].** D12 assigns M9 "the Stage-1 orchestrator + full A0/A2 run".
  - `m9-complete` (`a218bca`) was tagged for the pre-registration layer, with no run.
  - D8 Consequences places the pre-registration gate "at roadmap M9", which partly supports that scope.
  - The "full A0/A2 run" deliverable of D12 M9 is undelivered and unassigned. Any R-1 amendment must also say where that run now lives.
- **O-1 [FROZEN] vs [RATIFIED], outside R-1 proper.** D8.2 (E3) requires the pre-registration to freeze "N, seed count, minimum effect size". The frozen M9 pre-registration carries one evaluation seed and no minimum effect size (searching `M9_SPEC.md` finds none). D8.6 ("effect size reported") is not operationalized by any frozen M9 artifact. This needs scientific review alongside R-1.

## 8. R-2 evidence

| # | Path : line | Identifier | Status / class | Relevant wording | Supersedes |
|---|---|---|---|---|---|
| V1 | `docs/DECISIONS.md:381–391` | D19 | Accepted, scoped by D26 [RATIFIED] | legacy two-phase `VerifierSandbox` | — |
| V2 | `docs/DECISIONS.md:484–524` | **D26** | Accepted 2026-09-25 [RATIFIED] | AR-2 placement: "trusted host verifier orchestrator → digest-pinned task container → candidate execution". "Not decided by D26: runner mechanics; R_b, R_g, R_c; limit values; … protected-surface policy; TaskSpec schema" (`:524`). | D19, for real tasks only |
| V3 | `docs/DECISIONS.md:528–556` | **D27** | Accepted 2026-09-25 [RATIFIED] | evidence (A), classification by "the trusted, hash-locked Velith verifier classifier" (B), host orchestration (C) | clarifies M0 §6 and D13 |
| V4 | `docs/DECISIONS.md:560–581` | **D28** | Accepted 2026-09-25 [RATIFIED] | handle → registry → adapter "registered behind the frozen M5 `TaskAdapter` seam". D-3 (`:572`): real-task `Task`s never reach the legacy `VerifierSandbox`. | — |
| V5 | `docs/DECISIONS.md:656–674` | **D30** | Accepted 2026-09-28, "Director ruling" [RATIFIED] | `:662`: M1–M9 machinery "frozen as historical research infrastructure… not migrated". `:663`: "**New engineering code consumes Noetica's platform mechanisms** (for example the `Verifier` protocol and `Provenance`) through a pinned, published package, and adds no new generic platform mechanism to Velith." `:674`: "Consuming Noetica is gated on Noetica publishing a package." | **nothing** (`:658`) |
| V6 | `HANDBOOK_v1.1.md:135` | Handbook N.3 | RATIFIED [FROZEN] | "The **concrete SWE verifier/oracle** remains **Velith**; the **verification protocol/harness interface** it implements is **Noetica**." | — |
| V7 | `HANDBOOK_v1.1.md:399` | Handbook §2.2 anti-pattern | [FROZEN] | "A `SweVerifier`… placed inside Noetica… is a boundary breach… the SWE oracle is Velith's." | — |
| V8 | `HANDBOOK_v1.1.md:435, :486` | Handbook §2.3 | [FROZEN] | Velith provides "concrete implementations of Noetica interfaces: the engineering `Verifier`/oracle"; "Velith's verifier implements Noetica's protocol" | — |
| V9 | `HANDBOOK_v1.1.md:1164` | **Law 15** | [FROZEN] | "Noetica owns the `Verifier` protocol and `Verdict` type; the concrete oracle is domain content. *Violation:* a domain verifier in the core, or **a domain re-defining the protocol**." | — |
| V10 | `HANDBOOK_v1.1.md:1150` | Law 8 | [FROZEN] | "Platform grows by extraction, not speculation… harvested from a working application." | — |
| V11 | Noetica `docs/decisions/DECISIONS.md:141–175` | **DN-9** | Accepted 2026-09-28 (Noetica) [RATIFIED] | `noetica` 1.0.0 published, tagged `v1.0.0`. "Consumers pin `noetica @ git+https://github.com/manish0360-coder/Noetica-agent-lab@v1.0.0`." "Not integrated with Velith… yet; that is theirs to do." | — |
| V12 | Noetica `src/noetica/interfaces/verification.py:1–13, :45–48` | Noetica PE-1 | [IMPL], frozen by `platform-engineering-v1` | "Owner: Noetica (Layer 2) owns the PROTOCOL and the `Verdict` type… Future implementation owner: the DOMAIN — Velith `SweVerifier`". The protocol is `verify(task: Any, candidate: Any) -> noetica.Verdict(status, confidence, detail, schema_version)`. | — |
| V13 | Noetica `src/noetica/verification/README.md` | Noetica PE-8 | [IMPL] | "No real oracle… those are **domain-owned** (Velith…)". | — |
| V14 | Noetica `src/noetica/compute/__init__.py:6`, `broker.py:13` | Noetica compute | [IMPL] | "No cloud/K8s/**Docker**/GPU/solver/provider code." Noetica has **no** sandboxed or container execution mechanism. | — |
| V15 | Noetica `src/noetica/interfaces/provenance.py:20` | Noetica `Provenance` | [IMPL] | `Provenance(source, transform, inputs, attributes, schema_version)` | — |
| V16 | Velith `src/velith/evaluation/attempt.py:62–65`; `src/velith/batch/runner.py:45–48` | frozen M8 and M5 seams | [FROZEN] via `m8-complete` / `m5-complete` [IMPL] | Velith-local `Verifier` protocol: `verify(task: Task, patch: str) -> velith.harness.verifier_sandbox.Verdict` | — |
| V17 | Velith `src/velith/harness/verifier_sandbox.py:120–137` | Velith `Verdict` | [IMPL] | `state, output, secondary_passed, flaky, duration_seconds`; pydantic, `extra="forbid"` | — |
| V18 | Velith `pyproject.toml:10–16` | packaging | [IMPL] | `requires-python = "==3.12.*"`; dependencies `pydantic`, `pydantic-settings`. **No `noetica` dependency.** | — |
| V19 | `Velith-research/M2-PV-R_ARCHITECTURE_RATIFICATION_AMENDMENT.md:272, :403` (SHA `84d67088…`) | M2-PV-R record | RD-ratified research record (H-5) | "architecture ratification → **5-task zero-experience base-rate pilot** → M2-PV production verifier automation" | — |
| V20 | `Velith-research/M2-PV_PRODUCTION_VERIFIER_SPEC_RESEARCH.md:1–3` (SHA `dcecb46b…`) | M2-PV spec | **DRAFT**, 2026-09-25 [DRAFT] | "Not frozen. Not an implementation authorization." It mentions Noetica **0** times. | — |
| V21 | `Velith-research/M2-PV_IMPLEMENTATION_HANDOFF.md:336–337` (SHA `8d193f10…`) | BC-1, BC-2 | research handoff, 2026-09-26 [DRAFT] | BC-1 is pilot-first sequencing; BC-2 is the D26-undecided items. It mentions Noetica **0** times. | — |
| V22 | `Velith-research/M2-PV-P1_PILOT_DESIGN.md` (SHA `89f931e0…`) | pilot design | research, 2026-09-26 [DRAFT] | PB-1; OD-1 to OD-12. It mentions Noetica **0** times. | — |

## 9. R-2 chronology

| Date | Record | Event | Class |
|---|---|---|---|
| 2026-06-25 | D19 | Legacy single-container verifier. | [RATIFIED] |
| 2026-07 / 2026-08 | `m5-complete`, `m8-complete` | Frozen Velith-local `Verifier` seams (V16). | [FROZEN] |
| 2026-07-01 | Noetica `e27bab4`, `6260306` | Handbook v1.1 enters Noetica (DN-1). Noetica `Verifier` protocol names Velith as the oracle owner (V12). | [RATIFIED] / [IMPL] |
| 2026-09-25 | M2-PV spec research | DRAFT. No Noetica reference. | [DRAFT] |
| 2026-09-25 | M2-PV-R record; `1b0b7a0` | D26–D28 accepted into Velith `DECISIONS.md`. The pilot sequencing is ratified in the research record only. | [RATIFIED] |
| 2026-09-26 | M2-PV handoff; pilot design | BC-1 and BC-2 recorded. No Noetica reference. | [DRAFT] |
| 2026-09-28 02:38 +0530 | Velith `0d247d9` | **D30** accepted. It supersedes nothing. New engineering code must consume Noetica, gated on a published package. | [RATIFIED] |
| 2026-09-28 10:46 +0530 | Noetica `44d380b`, `v1.0.0` | **DN-9**: `noetica` 1.0.0 published. The D30 gate condition is met on Noetica's side. | [RATIFIED] |

Every M2-PV research artifact predates D30 and DN-9. None of them could have accounted for D30.

## 10. R-2 supersession analysis

- **S-R2.1 [RATIFIED].** D30 "Supersedes: nothing. D1–D29 remain in force exactly as written" (`:658`). D26, D27 and D28 are therefore **in force unchanged**, including D26's AR-2 placement and D27's "trusted, hash-locked **Velith** verifier classifier".
- **S-R2.2 [FROZEN].** The Handbook (level 1, adopted by D30.1) assigns the concrete SWE oracle to Velith and the protocol to Noetica (V6–V9). D26–D28 place the real-task verifier in Velith. These **agree**. No record places the SWE oracle, the task-container orchestration or the classifier in Noetica. V13 and V14 exclude it, and V7 calls such placement a breach.
- **S-R2.3 [INFERENCE].** D30.3 does not transfer ownership of anything. It constrains *how* new Velith code is built:
  - it consumes Noetica's protocol and mechanisms through a pinned package;
  - it adds no *generic* platform mechanism.

  This is additive to D26–D28. It is not a contradiction.
- **S-R2.4 [INFERENCE] — the one reading question: is the D26 host orchestrator a "generic platform mechanism" barred by D30.3?**
  - (i) D26 is in force "exactly as written" (S-R2.1), and it places the orchestrator inside Velith's real-task verification.
  - (ii) Noetica has no counterpart to consume (V14).
  - (iii) Law 8 (V10) makes a domain application the place a mechanism is proven before extraction.

  The only reading consistent with all three ratified texts: the D26 orchestrator is **oracle-internal Velith content**, scoped to SWE real-task verification. It is permitted provided it is not exposed as a reusable platform service.
  - This is the harmonizing reading. It does not prefer one document over another (P.4), because it leaves every text operative.
  - Extracting the orchestrator into Noetica later would follow Law 8 and a Noetica CAP. That is not required now.
- **S-R2.5 [IMPL] [INFERENCE] — an interface gap, not a governance conflict.**
  - The frozen M5 and M8 seams consume a Velith-local `Verifier` returning a Velith `Verdict` (V16, V17). D30.2 freezes those seams unmigrated.
  - Noetica's protocol returns a different `Verdict` type (V12). That type lacks `output`, `secondary_passed`, `flaky` and `duration_seconds`, except through `detail`.
  - Law 15 forbids "a domain re-defining the protocol" (V9). The frozen Velith seam predates the Layer-2/Layer-3 split. Handbook N.3 (`:137`) reads it as the extraction seed, not a violation.
  - A new real-task verifier must therefore satisfy **both**:
    - the Noetica protocol (D30.3, Law 15);
    - the frozen Velith seam, so that M8 and M10 can use it (D30.2, D12).
  - No ratified or DRAFT record specifies that bridge. This is a specification obligation for the M2-PV freeze (an extension of BC-2), not a supersession question.

## 11. R-2 determination

- **A. Who owns the production real-task verifier?** **Velith (Layer 3).**
  - Sources: [FROZEN] Handbook `:135`, `:399`, `:435`, `:486`, Law 15; [RATIFIED] D26–D28, in force per D30; [IMPL] Noetica V12 and V13 name Velith as the oracle owner.
  - This covers the TaskSpec admission, the task-container orchestration, the D27 classifier and the D28 adapter.
- **B. What may Velith implement locally?** [RATIFIED] + [INFERENCE per S-R2.4]:
  - the SWE oracle in full: the D26 orchestrator (oracle-internal), the D27 hash-locked classifier, the D28 registry, adapter and static guard;
  - the TaskSpec schema once decided (D26 `:524`);
  - the bridge to the frozen Velith seams.
- **C. What must consume Noetica?** [RATIFIED] D30.3 + [FROZEN] Law 15:
  - the `Verifier` protocol and `Verdict` type: the new verifier *implements* Noetica's protocol and must not define a competing *new* protocol;
  - `Provenance`, for new provenance that the verifier emits (for example D27 classifier identity in verification evidence);
  - any other Noetica mechanism the new code needs, rather than a new Velith copy;
  - all of it through `noetica` 1.0.0 pinned at `v1.0.0` (V11).
- **D. Does D30 supersede earlier M2-PV decisions?** **No** [RATIFIED]. It explicitly supersedes nothing, and D26–D28 remain in force (S-R2.1). The M2-PV *research* documents were never decisions. They are stale with respect to D30 (0 Noetica references) and must be revised before any freeze.
- **E. Is D30 frozen/ratified or draft?** **Ratified.**
  - It is `Accepted` in Velith `DECISIONS.md` (index `:59`, entry `:656`), under "Director ruling of 2026-09-28", committed at `0d247d9` on `origin/main`.
  - It is not a draft.
- **F. Is a formal amendment required?** **No `DECISIONS.md` supersession is required for R-2.** Required instead, before any M2-PV freeze:
  - (i) the M2-PV specification must state its D30 conformance (items in §14, AM-2);
  - (ii) the D30 gate: its condition is met on Noetica's side (DN-9). Velith has not yet adopted the dependency (V18). Adding it is an implementation step under a future authorization, and it changes the D27 hash-locked classifier environment.

  A supersession would be needed only if the Director wants a *different* ownership, for example placing the container orchestrator in Noetica. That would require a Noetica CAP (Law 8) and a Velith decision naming D26.

## 12. Cross-impact on M2-PV-P1

- **R-1 does not block the pilot [INFERENCE].**
  - The pilot is ratified as an engineering feasibility base-rate measurement: "not evidence for A1/A2 effectiveness, not a production evaluation" (record `:274–281`).
  - Its value (base-rate headroom for D8.1, verifier feasibility) is the same under either Stage-1 definition.
  - R-1 does decide whether and how the pilot's result feeds a Stage-1 plan. That question is downstream of the pilot.
- **R-2 does not block the pilot [INFERENCE].**
  - The pilot harness is experiment-only (under `experiments/`), and the pilot design keeps it outside `src/`.
  - It implements no production `Verifier` and adds no platform mechanism.
  - One gap remains: the pilot design predates D30 and carries no D30 posture statement. Any harness authorization should state explicitly that the harness is **non-production experiment code, not "new engineering code" under D30.3**, or else that it consumes `noetica`. This is a one-line authorization condition, not a redesign.
- **The pilot remains BLOCKED [RATIFIED process + DRAFT design].** Its blockers are its own:
  - PB-1: the harness is not authorized; the RD has confirmed "NOT authorizing the pilot harness yet";
  - OD-1 to OD-12 are open.
- **The pilot remains the ratified predecessor of production-verifier automation (BC-1).** This rests on an RD-ratified research record (V19), not on a `DECISIONS.md` entry. It is binding as RD process. It is not a prerequisite of M10 in any decision or specification.

## 13. Cross-impact on the production verifier

- **Ownership and placement are settled** (§11 A–B). No contradiction blocks the M2-PV architecture.
- **Existing blockers stand unchanged:**
  - BC-1: pilot first (V19);
  - BC-2: the D26-undecided parameters; the specification is DRAFT (V2, V20).
- **New obligations from D30, which extend the BC-2 freeze scope [INFERENCE from V5, V9, V12, V16]:**
  1. Implement `noetica.interfaces.verification.Verifier`, returning `noetica.Verdict`, and specify a deterministic, lossless bridge to the frozen Velith `Verdict` consumed by the M5 and M8 seams. Alternatively, state the reverse direction and justify it.
  2. Specify which verification provenance uses `noetica.Provenance`.
  3. Record that the D26 orchestrator is oracle-internal and not a platform mechanism (S-R2.4).
  4. Pin `noetica` 1.0.0 into the hash-locked classifier environment (D27 items 2 and 7).
  5. Check compatibility: `noetica` requires Python ≥ 3.10 and Velith pins `==3.12.*` (V18). No conflict is indicated.
- **R-1 does not change the verifier.** It changes only what the verifier's real evaluations are ultimately *analyzed as*.

## 14. Required amendments

**AM-1 (R-1), REQUIRED — Director ruling; two admissible forms.** Neither may be done by editing a frozen text.

- **Option 1 — ratify the frozen M9/M10 rule as the Stage-1 go/no-go.**
  - Form: a new dated decision (D31) that names D8 (item 5), D12 (M9 and M10 descriptions) and, as needed, D15 as superseded, with evidence and justification.
  - Code or specification change: none.
  - It must also state:
    - (a) whether a three-arm GO still counts as "necessary-but-not-sufficient", given that it includes D7's decisive A2 > A1;
    - (b) what Stage 2 then contains (A3; replication);
    - (c) where D12's "full run" now lives (F-R1.4).
- **Option 2 — keep D8.5 and make M9/M10 conform.**
  - Form: a new M9 specification amendment with a new `spec_version` for a two-arm A0-vs-A2 Stage-1 pre-registration and decision rule, plus a matching M10 amendment.
  - Code impact: reopens the frozen `ARMS` (E24), the executor arm check (E25) and `decision.py`, which is byte-pinned (E28).
  - This is a larger change, and it re-enters the full freeze pipeline.

**AM-2 (R-2), REQUIRED — specification-level, not a supersession.** The M2-PV specification freeze must incorporate §13 items 1–5, alongside the BC-2 items, before any production-verifier handoff.

**AM-3 (pilot), CONDITION on any future harness authorization.** A one-line D30 posture statement (§12).

**AM-4 (O-1), RECOMMENDED for scientific review.** Resolve the D8.2 and D8.6 gap (minimum effect size; seed count) jointly with AM-1, because both change the pre-registration.

## 15. Minimum safe next action

1. **Scientific Review Council (Gemini) review of the R-1 question set — needed.** It is needed because the choice between AM-1 options is a statistical-validity question, not a governance one. Questions:
   - (Q1) Is the frozen M9 rule `A1 > A0 ∧ A2 > A1` a valid operationalization of D6 H1, which requires `A2 > A0 ∧ A2 > A1` and never `A1 > A0`?
   - (Q2) Should a Stage-1 go/no-go include D7's decisive contrast?
   - (Q3) Should the missing A2-vs-A0 test and the D8.2 minimum effect size be added?
   - (Q4) What is the compute cost of Option 1 vs Option 2? The A1 arm adds one accumulation and evaluation arm.
2. **Director ruling on AM-1**, recorded as a new dated decision (Option 1) or a new M9/M10 specification version (Option 2).
3. **No action on R-2 beyond AM-2.** It is folded into the existing BC-2 specification-freeze work.
4. **The pilot stays parked** until the RD issues the harness authorization with AM-3.

**Gemini is not needed** for the governance findings of this document. Every one of them is a direct textual or git fact.

## 16. Governance decision

| Question | Determination | Basis |
|---|---|---|
| R-1 authoritative Stage-1 | **A0 vs A2** (D8.5, D12) | [RATIFIED] |
| R-1 frozen M9/M10 | **A0/A1/A2**, GO = A1 > A0 ∧ A2 > A1; non-conforming; not superseding | [FROZEN] [IMPL] |
| R-1 supersession | **None** | [RATIFIED] |
| R-1 status | **BLOCKED — Director resolution required (AM-1)** | [INFERENCE from H-2] |
| R-2 owner | **Velith** owns the oracle; **Noetica** owns the protocol | [FROZEN] [RATIFIED] |
| R-2 D30 status | **Ratified**; supersedes nothing | [RATIFIED] |
| R-2 status | **No contradiction**; specification obligations AM-2 | [INFERENCE] |
| M10 real execution | **BLOCKED** (R-1; plus the absent real pipeline, E30) | [RATIFIED] [IMPL] |
| M2-PV production verifier | **BLOCKED** (BC-1, BC-2 extended by AM-2) | [RATIFIED process] [DRAFT] |
| M2-PV-P1 pilot | **BLOCKED** (PB-1 not authorized; OD-1 to OD-12); unaffected by R-1 and R-2 except AM-3 | [RATIFIED process] |

**Exact next gate:** **G-R1 — SRC scientific review of Q1–Q4, then a Director ruling on AM-1.**
