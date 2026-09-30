# CSE Adversarial Audit — SRC response on S-R1 / S-R2

**Type:** research-only audit. **It resolves nothing that is not already fixed by a frozen artifact.**
**Date:** 2026-09-28.
**Baseline:** Velith `5452efc` (clean).

**Artifacts audited:**

| Artifact | SHA-256 |
|---|---|
| SRC response (`SRC_2026-09-28_S-R1_S-R2_response.txt`, byte copy of the upload) | `6524233d…f325` |
| Request | `00fe9a1b…` |
| RD Freeze Decision Input | `e69f4f48…` |
| D31 in `DECISIONS.md` | `57e228d6…` |

**Authority order:** Handbook > DECISIONS (D31, D8) > frozen specs (M9 VM2, M8 v1/IDv2) > code > RD-ratified research > draft research.

## 0. Frozen facts used by this audit (no interpretation)

- **FF-1 — D31 decision 6:** "GO iff H0 is rejected; NO-GO otherwise."
- **FF-2 — D31 decision 9:**
  - δ, "usable held-out n", K, N, α and power (≥ 0.80) are frozen before any confirmatory evaluation.
  - If power is < 0.80 at the maximum usable n, the design is **VOID before execution — never NO-GO**.
  - The frozen VOID dispositions "(global-incomplete; n = 0; empty VerificationManifest) are **retained**".
- **FF-3 — D31 decision 11:** if A1 is collected, "the Stage-1 analysis reads no A1 outcome, and no A1 outcome is disclosed before the Stage-2 analysis plan is fixed".
- **FF-4 — D8.6:** "an underpowered or noisy positive is treated as uninterpretable, not as a weak win."
- **FF-5 — M9 §3.5.1 (`M9_SPEC.md:215`):** the incomplete-evaluation hard stop is **run-level**: "If the M8 evaluation run did not complete for the full pre-registered held-out set, this pre-registration is void."
- **FF-6 — Frozen M8 runner (`evaluation/runner.py:92–111`).** The sweep writes exactly one record per held-out task for its (checkpoint, arm). Any failure — a cost-guard limit, an `EvaluationError`, or an exception from the attempt or verifier — **raises and halts** the sweep, with **no partial record**. INFRA_ERROR is a written record, with verdict 0. **In a sweep that completes, no primary cell can be missing.**
- **FF-7 — Exact Type-I control** (SRC, accepted) holds at every **fixed, non-outcome-selected** n. It does **not** by itself cover an analysis set selected by outcome-dependent loss.

---

## 1. S-R1 findings

| Item | Finding | Class |
|---|---|---|
| Primary cells = {A0@0, A2@K} | Consistent with D31 decision 6 ("applied at checkpoint K") and decision 11 | **ACCEPT** |
| Isolation (a) missing A1, (c) missing intermediate A2, (d–g) secondary failure / non-estimability / environment / p-value | Consistent with D31 decisions 6 and 11 and the accepted "GEE non-gating" ruling | **ACCEPT** |
| Influence: secondary never affects GO/NO-GO | Consistent with D31 decision 6 | **ACCEPT** |
| Ordering: primary computed and locked before any secondary computation; the primary result is persisted even if secondary aborts | Consistent. However, "recorded" conflicts with a single write-once `AnalysisResultRecord` (frozen C12 pattern) that also carries `secondary_status`. The record structure — a separate secondary record referencing the primary identity, or equivalent — is an **engineering/RD design item** (G-A7), not SRC. | **ACCEPT WITH CORRECTION** (record design open) |
| (b) and P6/P7: "binder must gracefully ignore (**or route to secondary**) A1 … records" | (i) Routing A1 to any analysis that decodes or reports its outcome **violates FF-3**. (ii) "Ignore" must not become "ignore any unexpected identity": that removes P6's structural-integrity guard against **foreign** records. **Correction, fixed by FF-3 plus P6's purpose:** only identities enumerated by the successor pre-registration (primary, sealed A1, secondary A2) are tolerated. A1 records are never decoded or reported. Any identity outside the full pre-registered set still aborts structurally. | **ACCEPT WITH CORRECTION** |
| Global-incomplete "re-scoped to evaluate completeness strictly over the expected primary cells" | This is ambiguous. It can be read as *cell-level*, where any missing primary cell VOIDs, which would contradict the complete-case rule in the same response. FF-5 fixes the frozen meaning as **run-level**. **Correction:** global-incomplete means the primary sweeps (A0 and A2@K over the admitted set) did not complete. This is retained per FF-2. | **ACCEPT WITH CORRECTION** |
| "Primary VOID **iff** n_cc < minimum powered n, or VM empty" | The list is incomplete and conflicts with FF-2, which **retains** global-incomplete, n = 0 and empty-VM as VOIDs. It also omits the pre-execution power VOID. It depends on S-R2's unresolved threshold. The closed list must at least contain the FF-2 dispositions; the S-R2 addition is still open. | **REJECT as written** |
| "WHAT REMAINS OPEN: None" | False. The VOID list depends on S-R2, and the record design is open. | **REJECT** |
| P1, P2, P4, P5 superseded; P3 re-scoped | Valid under D31 decisions 3–4 (versioned successor). VM2 code stays historical at its tags. | **ACCEPT** |
| "Bifurcated `PrimaryGate` / `SecondaryExploratory` pipeline wrapped in a **global** exception handler" | Implementation architecture is an **open RD decision** (G-A7), not an SRC matter. A *global* handler could also swallow **primary** integrity errors. It must be restricted to secondary computation. | **Non-binding**; correction noted |

## 2. S-R2 findings

**MCAR — UNSUPPORTED.**
- No ratified or frozen artifact asserts MCAR: not D31, not D8.6, not M9/M10 VM2, not the SRC design chain, and not D1–D30.
- The request stated explicitly that primary-cell loss "may depend on outcomes". Gemini introduced MCAR without justification.
- MCAR is **load-bearing**: complete-case analysis of an outcome-selected subset is not covered by FF-7. So Gemini's rationale ("Type-I … holds unconditionally at any n") does not carry over to its own post-execution rule.
- **However, FF-6 and FF-5 already establish something stronger for the frozen M8 runner:** post-execution primary-cell loss cannot occur within a completed sweep. Any loss implies an incomplete run, which gives **VOID** under global-incomplete (retained by FF-2).
- Whether the **successor** evaluation path — the real-task production verifier (BC-2) and the M8 runner as reused — must preserve this invariant is **not frozen**. That is the decision still required (Q1). It is not a replacement assumption.

**Post-execution alternate acceptance rule ("recompute power at n_cc; proceed if ≥ 0.80") — REJECT / UNSUPPORTED.**
- If n_conf := min{n : power(n) ≥ 0.80} and power is monotone in n, the rule is **vacuous**: every n < n_conf has power < 0.80.
- Exact power of discrete tests is **not in general monotone** in n (the "saw-tooth" effect). Where power is non-monotone, the rule creates a **second, post-execution acceptance threshold** below n_conf.
- That threshold is **inconsistent with Gemini's own pre-execution rule**. With n_admitted = n_conf − 1, the design is VOID before execution, yet with n_cc = n_conf − 1 after execution it could proceed.
- Under FF-6 the branch cannot arise anyway, unless the successor breaks the invariant.

**n_conf status — UNRESOLVED (governance).**
- FF-2 freezes "usable held-out n" before execution but does not say whether it is a **hard minimum** or a **planning target**.
- A post-execution **VOID_UNDERPOWERED** is a VOID class **not enumerated** in D31. D31 decision 6's "NO-GO otherwise" makes it at least **unestablished** whether the successor specification may add a post-execution VOID. FF-4 (D8.6) supports treating an underpowered *positive* as uninterpretable.
- Resolving this is an RD governance matter (Q3). It is **needed only if** Q1 is answered "invariant not preserved".

**Pre-execution rule (n_admitted < n_conf gives VOID before execution) — ACCEPT.**
- It is a direct application of FF-2: admission is outcome-blind, and n_admitted is the usable n at execution time.

**Recomputation only with frozen planning parameters; post-hoc reduction of n_conf FORBIDDEN — ACCEPT.**
- Consistent with FF-2 and with the SRC's prohibition of post-hoc adjustment.

**"minimum n = min{n ∈ ℤ⁺ : ExactPower(n, planning params) ≥ 0.80}" — ACCEPT WITH CORRECTION.**
- It is well-defined only as min over {n ≤ N_avail}, with the empty set giving the design VOID before execution (FF-2).
- It is **the same quantity as n_conf**, not a distinct threshold, provided n_conf is defined identically.
- **Two definitions must be pinned (SRC):**
  - (i) The planning-power function. Because planning p0 is "the value in the pilot CI minimizing exact power" and that minimizer can depend on n, it must be power_plan(n) = min over p0 ∈ CI of ExactPower(n; p0, Δ_true, scenario, δ, α, γ, ε, η).
  - (ii) Saw-tooth handling: the first n with power_plan ≥ 0.80, or the smallest n such that power_plan(m) ≥ 0.80 for every m in [n, N_avail].
- **Replacing OED-7 by this rule is rejected as worded.** FF-2 retains "n = 0" as a VOID. That disposition stays, and any new rule is additive.

**Over-enrolment ("SHALL … ensuring P(n_cc ≥ n_conf) is high") — UNRESOLVED.**
- It is **not required** by D31 or by frozen governance. As an SRC recommendation it is a *possible* new successor requirement, but it is not exact:
  - "high" has no stated probability;
  - under FF-6, post-execution losses are zero or VOID, so the buffer can only address **admission** losses, which are outcome-blind;
  - whether n_analyzed = n_cc (all admitted tasks) or is truncated to n_conf is unspecified;
  - if every N_avail task is sent to admission, a buffer may be moot.
- The buffer size stays an RD decision and is not chosen here.

**Reconciliation with D31 decision 9, D8.6 and exact Type-I control.**
- Pre-execution VOID on power (including n_admitted < n_conf): consistent with all three.
- Post-execution VOID on power: consistent with D8.6 in spirit, but not enumerated in D31 (Q3).
- Exact Type-I control: valid for the primary test **only** if the analyzed set is not outcome-selected. That is guaranteed by FF-6 if the invariant is kept (Q1).

---

## A. Accepted from Gemini

- Primary cells {A0@0, A2@K}.
- Isolation (a), (c), (d)–(g).
- Secondary never influences GO/NO-GO.
- The primary decision is computed and locked before any secondary computation.
- Secondary failures are recorded as NOT_ESTIMABLE(reason).
- P1, P2, P4 and P5 are superseded and P3 re-scoped, via D31 decisions 3–4.
- Pre-execution VOID when n_admitted < n_conf.
- Recomputation (if any) uses only the frozen planning parameters.
- Post-hoc reduction of n_conf is forbidden.
- No arbitrary minimum n.

## B. Accept with correction

1. Only pre-registered identities are tolerated. A1 is never decoded, routed or reported (FF-3). Foreign identities still abort (P6/P7).
2. Global-incomplete stays **run-level**, re-scoped to the primary sweeps (FF-5, FF-2).
3. The primary VOID list is closed and includes global-incomplete, n = 0 and empty-VM (FF-2), plus the pre-execution power VOID.
4. The result-record structure under primary-first ordering is an engineering design item (G-A7).
5. The exception handling is restricted to secondary computation. The architecture wording is non-binding.
6. The minimum-n formula is bounded by N_avail, with the empty set giving VOID before execution, and is identical to n_conf once (i) and (ii) are pinned.

## C. Reject / unsupported

1. The MCAR assumption for post-execution primary-cell loss.
2. "Type-I holds unconditionally at any n", as applied to an outcome-selected complete-case set.
3. The post-execution acceptance of n_cc < n_conf when recomputed power ≥ 0.80. It is vacuous or creates an inconsistent second threshold.
4. "Primary VOID iff …", as written (conflicts with FF-2).
5. OED-7 "replaced" (FF-2 retains it).
6. S-R1 "OPEN: None".
7. "READY FOR RD FREEZE" for S-R2.

## D. Exact open questions

- **Q1 (SRC, with RD):** must the successor evaluation path preserve the FF-6 invariant — a completed primary sweep writes one record per admitted task per primary cell, and any failure halts, giving run-level incomplete and VOID?
  - If **yes**, post-execution primary-cell loss is impossible, n_cc = n_admitted, and the post-execution branch and MCAR are unnecessary.
  - If **no**, the SRC must specify how post-execution primary-cell loss is handled so that Type-I control holds **without** MCAR, or else declare MCAR as an explicit, justified assumption for RD acceptance.
- **Q2 (SRC):** pin power_plan(n), including the per-n minimization over the pilot CI, and the saw-tooth convention that defines n_conf.
- **Q3 (RD governance, only if Q1 = no):** is n_conf a hard minimum? Is a post-execution VOID that D31 does not enumerate permitted under decision 6 ("NO-GO otherwise"), or does it require a D31 clarification or amendment?
- **Q4 (SRC/RD):** over-enrolment. Is it required at all given Q1 and the admission design? What probability target replaces "high"? Is n_analyzed = n_cc or truncated to n_conf? The buffer size is RD.
- **Q5 (RD, G-A7):** result-record structure under primary-first ordering.

## E. Is another SRC review required?

**Yes**, narrow: Q1, Q2 and Q4. The S-R1 corrections B1–B3 are fixed by frozen artifacts and need no new SRC ruling; include them for SRC acknowledgement. Q3 goes to the RD only if Q1 = no.

## F. Can S-R1 be frozen independently of S-R2?

**Partly.**
- **Independent:** the S-R1 isolation core (A items for S-R1, plus corrections B1, B2, B5) does not depend on S-R2 and can go into the RD Freeze Decision Input now.
- **Dependent:** the **primary VOID list** (B3) depends on S-R2's outcome (Q1/Q2) and cannot be closed yet.
- **Freeze path:** under D31 decision 3, the successor specification is frozen as a whole. "Independently" therefore means recording S-R1's core as settled input, not a separate freeze act.
