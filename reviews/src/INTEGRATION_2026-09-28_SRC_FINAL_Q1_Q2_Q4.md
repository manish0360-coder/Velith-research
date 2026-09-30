# CSE Final Integration Audit — SRC Q1 / Q2 / Q4 (closes the Stage-1 statistical review loop)

**Type:** research-only. **It decides no open parameter, freezes nothing and implements nothing.**
**Date:** 2026-09-28.
**Baseline:** Velith `5452efc`, clean.

**Inputs:**

| Input | SHA-256 |
|---|---|
| SRC final response (`SRC_2026-09-28_Q1_Q2_Q4_final_response.txt`, byte copy of the upload) | `3c0a79bd…688e` |
| Prior audit | `c1f0b3d0…` |
| RD Freeze Decision Input | `e69f4f48…` |
| D31 in `DECISIONS.md` | `57e228d6…` |

**Authority order:** Handbook > DECISIONS > frozen specs > code > RD-ratified research > draft research.

**Verdict: no genuine contradiction.** There are six integration notes (§D). None of them is a statistical question.

---

## A. Accepted / integrated

| # | Rule (SRC final) | Checked against | Result |
|---|---|---|---|
| A1 | Primary cells are exactly {A0@0, A2@K} | D31 decision 6 | Consistent |
| A2 | Completed primary-sweep invariant: every admitted task has its primary records, or the sweep halts. A partial sweep is run-level global-incomplete and therefore VOID. | M8 runner `runner.py:92–111` (halt, no partial record); M9 §3.5.1 run-level wording; D31 decision 9 (global-incomplete retained) | Consistent; preserves the frozen invariant |
| A3 | n_cc = n_admitted. MCAR is **not** assumed. There is **no** post-execution missing-cell branch. INFRA_ERROR is an observed 0, not a missing cell. | D16.7; M9 §3.5.1 encoding; prior audit C1 and C3 (resolved) | Consistent; the earlier MCAR objection is closed |
| A4 | A1, intermediate A2 and secondary GEE never affect GO/NO-GO. Primary-first ordering. | D31 decisions 6 and 11 | Consistent |
| A5 | A1 outcomes are never decoded, routed or reported. Only pre-registered identities are tolerated. Foreign identities keep structural protection. | D31 decision 11; P6/P7 purpose | Consistent |
| A6 | Global-incomplete is run-level. D31's retained VOIDs (global-incomplete, n = 0, empty VM) are retained. | D31 decision 9 | Consistent. n = 0 is unreachable in practice (it is caught before execution), but it stays listed. |
| A7 | power_plan(n) = min over p0 ∈ the 95% CP pilot interval of ExactPower(n; p0, Δ_true, scenario, δ, α, γ, ε, η) | SRC final review items 4–5 | Consistent; the per-n minimization is now explicit |
| A8 | n_conf = the smallest n ≤ N_avail with power_plan(m) ≥ 0.80 for every m ∈ [n, N_avail]. If no such n exists, VOID before execution. | **D31 decision 9** | **Exactly equivalent.** VOID ⟺ power_plan(N_avail) < 0.80 (m = N_avail must hold; and if it holds, n = N_avail qualifies). This is decision 9's "power below 0.80 at the maximum usable n". Option B only adds saw-tooth robustness: every n_admitted ∈ [n_conf, N_avail] has power ≥ 0.80. |
| A9 | n_analyzed = n_admitted. No truncation to n_conf. | D31 decision 9 ("usable held-out n"); SRC final review item 5 (post-hoc reduction forbidden) | Consistent |
| A10 | Over-enrollment is optional, pre-execution and outcome-blind. The "P(n_cc ≥ n_conf) high" wording is withdrawn. | D31 (silent); D31 decision 10 (no confirmatory contamination) | Consistent |
| A11 | Pre-execution VOID if n_admitted < n_conf (prior response, re-confirmed by Q1) | D31 decision 9 | Consistent |

## B. Historical M9 VM2 rules requiring successor supersession

**Mechanism.** Supersession happens **prospectively**, through the versioned successor authorized by D31 decisions 3–4. VM2 (`m9-spec-frozen-oed7-vm2`, code at `5476d82` / `m9-complete`) stays **frozen, unedited and reproducible at its tags**. Nothing below modifies VM2.

**Superseded in the successor:**

| VM2 rule / path | Successor rule |
|---|---|
| §3.1 arm set {A0, A1, A2} as analysis arms (`preregistration.py:56`; `executor.py:201`) | Primary arms A0 and A2@K. A1 is sealed if collected. |
| §2 / §3.2 / §3.5.2 ordered hypothesis A2 ≻ A1 ≻ A0 (H_a1, H_a2) | H0: Δ20 ≤ δ (A-iv) |
| §3.5.3–§3.5.4 gating GEE (A1 vs A0 additive; A2 vs A1 interaction), Interpretation-A EMM, gating trend tests | A secondary, non-gating A2-only GEE |
| §3.5.5 K = 1 two-test McNemar with Holm | Certified exact unconditional B-ii test, applied at every K |
| §3.5.6 four-test Holm family | A single primary test (Stage-2 multiplicity is open under D15) |
| §3.5.7 model failure gives p = 1.0 and NO-GO (P1) | Recorded as `NOT_ESTIMABLE`, with no effect on the decision |
| §3.5.8 GO iff all four tests reject | GO iff the B-ii test rejects |
| §3.5.1 **cell-level** complete-case over K × 3 cells (P3) | Run-level invariant, with n_cc = n_admitted |
| P2 (statsmodels aborts the run) and P5 (`GeeError` aborts) | Secondary-only failures, isolated |
| P4 (secondary tests in the gating family) | Removed from gating |
| P6 / P7 (unexpected identities abort) | Re-scoped: pre-registered sealed or secondary identities are tolerated; foreign identities abort |
| `spec_version = …-vm2` (D29 item 3) | A new version (scoped supersession already made by D31) |

**Retained (not superseded):**
- run-level global-incomplete VOID (re-scoped to the primary sweeps);
- OED-7 n = 0 VOID;
- empty-VerificationManifest rejection;
- PASSED = 1 / else 0 encoding;
- α = 0.01;
- OED-2 A0 time-invariance (A0 at episode 0);
- content-addressed, write-once, sealed-from-results pre-registration (§3.3–§3.4);
- checkpoint-identity binding;
- M8 identity v2, including `verification_manifest_hash` and `eval_seed` (N = 1);
- the pinned single-thread numeric environment.

## C. Remaining RD decisions (required before the successor pre-registration can be sealed)

| ID | Decision | Dependency |
|---|---|---|
| RD-1 / RD-2 | Pilot size, scope and configuration: proposer-level equivalence (model **weights digest**, T = 0, seed derivation, `num_ctx`/`num_predict`, prompt, attempts); task representativeness; the research amendment needed because the ratified record says "exactly 5" | First on the critical path |
| RD-4 | δ (MCID), recorded with justification after the pilot | Pilot |
| RD-5 | Δ_true | — |
| RD-6 | Governing planning discordance scenario (the SRC concurs with independence) | — |
| RD-6b | **Values of the two positive-correlation sensitivity scenarios.** The SRC mandated the grid but did not specify these values. They are reporting-only if RD-6 = independence, but they must be pre-specified before sealing. | RD-6 |
| RD-3 | N_avail: the real-corpus held-out partition, net of pilot exclusions | Real corpus (M4 adapter, D28, D26 schema) |
| RD-8 | Optional admission buffer, and its size | RD-3 |
| S-R3 | The scheduled SRC acceptability check of the recorded δ, MCID and power computation (RD Freeze Decision Input; D31 governance draft §8.7). This is a parameter-level check, not an open framework question. The RD may confirm or waive it. | RD-4 |

**Not needed for sealing, but needed for the successor-specification freeze and implementation:**
- G-A8: specification form and `spec_version` string;
- G-A7: implementation architecture, including result-record structure under primary-first ordering and the mechanism that enforces T = 0.

## D. Contradictions

**None found.** Each of the following is an integration requirement that the successor specification must state. None is a conflict:

- **I-1 — the completion flag must be verifiable.** Frozen M10 takes `evaluation_run_complete` as a **caller-asserted** boolean (`executor.py:317`). Under Q1, the successor must *verify* that every admitted task has both primary records. A flag that says "complete" while a record is missing is a **structural error (abort)**, never an analysis.
- **I-2 — sequencing.** The VerificationManifest (D29) binds the TaskSpecs of the evaluated population into the pre-registration identity, and D31 decision 9 freezes n before evaluation. The order is therefore: admission → VM → power check (n_admitted ≥ n_conf) → **seal** → A0/A2 generation.
- **I-3 — halt vs INFRA_ERROR boundary.** Legacy D19 maps `SandboxExecutionError` to an INFRA_ERROR record. D26.8 (real tasks) says only "raises". Which real-task faults halt the sweep and which produce an INFRA_ERROR record (verdict 0) must be defined in the M2-PV specification (BC-2). The endpoint encoding itself is frozen.
- **I-4 — computational feasibility of Option B.** Evaluating power_plan at every m up to N_avail needs the certified rejection region for each m. For fixed D, the certified p-value is monotone in c, so each critical value can be found by bisection. The cost is still substantial and needs engineering, not SRC.
- **I-5 — tie authority.** The case |p − α| ≤ 10⁻⁶ is decided by the pinned-environment evaluation of record, consistent with SRC reproducibility level (ii). This is specification wording.
- **I-6 — "READY FOR RD FREEZE".** This means the statistical **framework** is ready to be written into the successor specification and frozen by the RD. It does **not** mean the pre-registration parameters (§C) are frozen.

## E. Final freeze readiness

- **Statistical framework: complete.** **No further SRC review is required** for the framework. The only remaining SRC touchpoint is the scheduled, parameter-level S-R3 check of the RD's δ, which the RD may confirm or waive.
- **Successor specification freeze:** unblocked on the statistical side. It still needs G-A8 (form and version), a drafted specification text, and an RD freeze act.
- **Pre-registration sealing:** blocked until §C is complete (RD-1 to RD-8, plus S-R3 unless waived).
- **Implementation and the pilot:** not authorized. Each needs its own gate.
