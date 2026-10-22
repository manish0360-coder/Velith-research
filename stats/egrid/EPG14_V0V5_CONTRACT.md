# EPG-14 — V0–V5 Software-Mechanics Validation: Consolidated Candidate Contract

| Field | Value |
|---|---|
| Version | **CAND-5** (candidate; supersedes CAND-4) |
| Date | 2026-10-22 |
| Status | **BODY ACCEPTED BY RD 2026-10-22 (R-ACC, L11) AS A SPECIFICATION FOR BOUNDED SOFTWARE-MECHANICS VALIDATION ONLY. R-V5 PROVISIONAL. R-MD PENDING. NOT FROZEN. NO FROZEN HASH RECORDED. NOT AN AUTHORIZATION.** |
| Prepared by | CSE |
| Sources | EPG-14 recovery Parts 1–4; CSE targeted adjudication; CAND-1 audit AUD-1 – AUD-18; CAND-2 acceptance-gate review; CAND-3 final gate review (chat record, 2026-10-21/22). |
| Edit authority | RD-authorized acceptance clarifications of 2026-10-22 (CAND-5; documentation edits to this file only); R-ACC recording of 2026-10-22 (L11; status, ledger and provenance fields only). |
| Execution | Nothing in this document authorizes implementation, V0–V5, the full grid, any experiment, hashing as frozen, commit or push. |

Saving, reviewing or hashing this file does not authorize anything. Only an explicitly recorded RD authorization (§19) can.

---

## 0. Provenance legend and acceptance ledger

| Tag | Meaning |
|---|---|
| **[ACC]** | Explicitly accepted by the RD (L6 only): Closure Amendments **E1–E5** ("subject to implementation and test verification") and **n = 1–80, 400 design-point configurations**. |
| **[D31]** | Fixed by ratified Velith decision D31 (`Velith/docs/DECISIONS.md` L680–770, status Accepted; "one-sided α = 0.01" at L722). External to this contract. |
| **[RD-NEW]** | New RD governance decision of 2026-10-21. Not part of any previously accepted text. |
| **[RD-PROV]** | Provisionally accepted by the RD on 2026-10-21 subject to a stated condition. Not previously accepted. |
| **[COR]** | Class-(b) correction made in a candidate pass: consistent with accepted text, no new scientific or governance choice. Effective only when the RD accepts this contract (R-ACC). |
| **[PROP]** | Recovered proposed text (CSE drafts or RD *proposed* rulings), not explicitly accepted. Effective only on R-ACC. |
| **[PEND]** | New RD decision required. Not effective until decided. |
| **[BLOCKED]** | Required content is not specified. The item cannot be performed and cannot count toward any PASS until specified and approved. |

Expected-result classes (used in §9, §10.3, §13.5, §14):

| Class | Meaning |
|---|---|
| **IND** | Independent expected result: a fixed value written in this contract (hand-derived, never executed), a mathematical property, or a direct definitional formula. Not produced by any implementation code path. |
| **XCHK** | **Same-author cross-check — not an independent expected result.** The comparison value comes from a separate code path written by the same author (V0-7b, V0-7c, B1, B7 because it uses the B1 reference, B2 interior case-I fixtures because they are checked through B1, and P2). It is mandatory where stated but is never described or reported as independent validation. |
| **STRUCT** | Structural/completeness requirement (presence, counts, recorded settings); no numerical expected value. |

RD acceptance ledger (exact quotations):

- L1 (proposed rulings M1–M5 + scope): "Research Director's **proposed** rulings …".
- L2: "The RD is **provisionally willing to accept** decision-equivalent certification … **subject to validation**."
- L3: "Verdict: **ACCEPT WITH CORRECTIONS for bounded validation only**."
- L4: "Bounded V0–V5 is **conditionally acceptable** as software-mechanics validation only, subject to a corrected specification and explicit RD authorization."
- L5: lists SRC verdicts and "two **mandatory** amendments" (instruction, not acceptance of the resulting text).
- L6: "**Accept E1–E5** as the current specification amendments, subject to implementation and test verification. **Use n = 1–80, yielding 400 design-point configurations.** … U-2, U-3, and U-4 remain blocked. V0–V5 have not been authorized or executed."
- L7 (2026-10-21): "R-P11: **ADOPT** as a new governance rule …"; "R-V5: **PROVISIONALLY ACCEPT** `{100, 300, 600} × {1/50, 1/10}` … subject to checking consistency with the stated R1′ objective"; "R-ACC: **NOT DECIDED**."
- L8 (2026-10-21, binding for CAND-3): "R-TINY: V0-7d is non-mandatory, `[BLOCKED]`, and `NOT PERFORMED`"; V0-7b, V0-7c and B1 "mandatory, but label them `same-author cross-check — not an independent expected result`"; "R-E1A1: … REJECTED by RD 2026-10-21; not part of the contract"; "`R-PROJ: decided 2026-10-21; full-grid projection remains BLOCKED`"; "R-V5 remains provisional"; R-ACC still pending.
- L9 (2026-10-22, binding for CAND-4): D1 — P2 (b) "both comparison paths use literal R1 on the already specified P2 validation sets"; D2 — P2 (c) power-agreement test "removed from the mandatory acceptance gate … `BLOCKED — NOT PERFORMED`"; D3 — "B2 is `IND` only for outcomes independently determined by explicit rules in §3.3 … B2 interior case-I fixtures checked through B1 are `XCHK` … B3 is `STRUCT`".
- L10 (2026-10-22, CAND-5): RD accepts CAND-4's substantive corrections D1–D3 and authorizes two clarifications only: (A) the δ set for B3/B6 at n = 600, to be stated only if established by source material; (B) B6 as a necessary-condition property check with an explicit claim boundary.
- L11 (2026-10-22, R-ACC): "Accept CAND-5's contract corrections D1–D3 and clarifications A–B." "Confirm the five-value delta set `{1/50, 1/25, 3/50, 2/25, 1/10}` for B3 and B6 at n=600" — an explicit RD decision; its original source was CSE-proposed text (restricted-MLE correction memo §5–§6), which is not thereby independently validated. "Accept the contract only as a specification for bounded software-mechanics validation. This does not establish statistical validity, exact size, general Lemma M correctness, or worst-case power." "Keep R-V5 provisional and preserve the existing R-MD boundary: unresolved result-affecting implementation details remain blockers for the affected stage." No freeze and no V0–V5 authorization (R-AUTH pending).

---

## 1. Scope and limits

1.1 [PROP] (EPG-0) Offline, design-exploratory exact-power software for Stage-1 planning. It does not freeze δ, Δ_true, RD-6, N_avail or SM1–SM11. It is not a pre-registration input.

1.2 [PROP] (L4, X7) **V0–V5 are software-mechanics validation only.** A pass establishes deterministic, isolated execution and agreement between internal checks. It does **not** establish:

- U-2 (level-α control over the composite null), Lemma M in general, or at any (n, δ, τ) not exactly certified;
- U-3 (rigorous numerical error bounds);
- U-4 (certified worst-case/global power);
- any sample size, Stage-1 feasibility, confirmatory statistical validity;
- any engineering or manufacturing capability.

1.3 [PROP] The full exact-power grid (EPG-4 grid, EPG-7 24 CPU-h cap) remains **blocked** pending V0–V5 evidence, the X4 SRC code review, and separate RD authorization. Confirmatory use remains blocked pending U-2, U-3, U-4 (§21).

1.4 [PROP] (EPG-9) All code and outputs live under `Velith-research/stats/egrid/`. Production Velith is never modified. No staging, commit or push without separate approval.

1.5 [RD-NEW] (R-P11, 2026-10-21) **V0–V5 output must not be used to select δ, g, Δ_true or n.**

---

## 2. Parameters (exact values)

| Symbol | Value | Tag | Source |
|---|---|---|---|
| α | 0.01 (one-sided) | [D31] | D31 (L722) |
| γ | 0.001 (Berger–Boos) | [PROP] SRC-accepted, RD freeze pending | SM2/SM4 |
| η | 10⁻⁹ | [PROP] | SM1/SM2 |
| ε | 10⁻⁷ (B&B gap) | [PROP] | SM1 |
| φ | 10⁻⁶ (flag band half-width) | [PROP] | C1 |
| ρ | 10⁻¹⁰ (per-quantity probability rounding allowance; estimate, not proof) | [PROP] | C9 |
| ρ_P | 10⁻⁹ (power rounding allowance; estimate) | [PROP] | EPG-14 |
| τ₀ | 1/10¹⁰ exactly (rational); per-outcome τ_x = τ₀·max(1, \|T(x)\|) | [PROP] | EPG-2, M2, Q1 |
| θ | α − η − γ = 0.008999999 | [PROP] | C1 |
| δ set | {1/50, 1/25, 3/50, 2/25, 1/10} (exact rationals) | [PROP] | D-U4/EPG-4, Q1 |
| g set (full grid only) | {1/20, 1/10, 3/20, 1/5, 1/4} | [PROP] | EPG-4 |
| V0 n-range and count | n = 1…80; 400 design-point configurations | **[ACC]** | L6 |
| k schedule | k₀ = min(64, k_max); kᵢ₊₁ = min(2kᵢ, k_max); production k_max = 200 → 64, 128, 200; k_max an integer ≥ 1 | [COR] | §4.7 |
| B&B depth cap | 64 bisections | [PROP] | C1 |

---

## 3. Statistic and restricted MLE

3.1 [PROP] (EPG-1, M1(a)) Labels: x = n₁₀ = #(A2 pass, A0 fail), y = n₀₁ = #(A2 fail, A0 pass), z = n − x − y, following `velith/analysis/mcnemar.py` **L107–108** [COR: citation corrected from "L108–109"], with superior arm A2 and reference arm A0.

3.2 [PROP] Statistic: **T = (x − y − nδ) / √( n·(2q̃ + δ·(1 − δ)) )**. Write N = x − y − nδ (exact rational) and V = 2q̃ + δ(1 − δ).

3.3 [PROP] q̃ = restricted MLE of p₀₁ under p₁₀ = p₀₁ + δ on [0, u], u = (1 − δ)/2. Case algorithm:

1. Validate n ≥ 1, integer counts ≥ 0, δ ∈ ℚ ∩ (0, 1); otherwise STOP-2.
2. If z = 0: q̃ = u (case **U**).
3. If y = 0 and x(1 − δ) ≤ 2zδ: q̃ = 0 (case **0**).
4. If y = 0 and x(1 − δ) > 2zδ: q̃ = [x(1 − δ) − 2zδ]/(2n) (case **I0**).
5. Otherwise (y > 0, z > 0, case **I**): q̃ is the root in (0, u) of 2n·q² + B·q + C with B = −(x + y) + (2n − x + y)δ, C = −yδ(1 − δ). Float path: (−B + s)/(4n) if B ≤ 0, else 2C/(−B − s), s = √(B² − 8nC).
6. Assert 0 < q̃ < u in case I; violation → STOP-9; there is no clamp.

Case selection on the exact path uses exact rational tests.

3.4 Exact representation of V:

- [ACC] (E3) "Every V is written as r + s√D with **s = 1/(2n)** and **D = B² − 8nC** exactly as computed in case I, and with s = 0 otherwise. Radicands are passed to S1 and S2 unsimplified; `sqrt_rat` reduces them itself. Test vectors must use this form."
- [PROP] (Q2.5) In case I, r = δ(1 − δ) − B/(2n) and the exact path uses q̃ = (−B + √D)/(4n), equal to the float formula 2C/(−B − √D) because (−B + √D)(−B − √D) = B² − D = 8nC. In cases U, 0, I0, V is rational: U: V = 1 − δ²; 0: V = δ(1 − δ); I0: V = 2q̃ + δ(1 − δ).
- [COR] (fills a gap in E3) **D := 0 whenever s = 0.**

3.5 [PROP] Invariants (Amendment A): after validation, V ≥ δ(1 − δ) > 0; in case I, B² − 8nC > B² ≥ 0. V ≤ 0, discriminant ≤ 0, or q̃ ∉ [0, u] → STOP-9. [PROP] (Q2.5) Exact invariant S1(r, s, D) = +1 for every V; otherwise STOP-9. sign(T) = sign(N).

3.6 [PROP] Attribution: "score statistic attributed to Tango (1998); **not checked against the publication**" (U-1).

---

## 4. Tail, comparison semantics, exact tier, interval tier

### 4.1 Tail definition

[PROP] (EPG-2) R(x₀) = {y : T(y) ≥ T(x₀) − τ_x₀}, τ_x₀ = τ₀·max(1, \|T(x₀)\|). Inclusion within τ is part of the **test definition** (an exact inequality with rational τ₀), not a tie classification. Deterministic processing order: (T descending, x descending, y ascending).

[ACC] (E1) A tail is built **only if N(x₀) > 0**, decided exactly. N(x₀) ≤ 0 reaching tail construction → STOP-9. (SM5: Δ̂ ≤ δ ⟺ N ≤ 0 ⇒ p = 1.)

### 4.2 Comparison outcomes (exact-tie semantics) [COR]

Every comparison has exactly one of three outcomes:

- **(A) Exact equality (certified tie):** same outcome; N_a = N_b = 0; or an exact sign result of 0 from S1/S2.
- **(B) Certified order:** an exact non-zero sign (S1/S2), or strictly disjoint rational intervals (§4.7 step 7).
- **(C) UNRESOLVED:** intervals still not strictly disjoint at k_max. **Never a tie.** In R1′ classification and region construction (V1–V5): include when computing Ū, exclude when computing L̲ (bracket rule); final UNRESOLVED classification → STOP-7. In the V0 Lemma M check: the design point becomes UNCERTIFIED (not STOP-7).

[COR] (replaces the conflicting sentence in EPG-2 and R5) **Float tie diagnostic:** report every relative float gap between consecutive T values in (10⁻¹², 10⁻⁹] as a *diagnostic only*; such pairs are routed to the exact/interval tier and are never treated as ties on float evidence.

### 4.3 T-versus-T sign table

[PROP] (Amendment A; √n cancels)

| Case | Rule |
|---|---|
| Invalid inputs | STOP-2 |
| V ≤ 0, discriminant ≤ 0, q̃ ∉ [0, u] | STOP-9 |
| Same outcome | Equal (identity) |
| sign(N_a) > sign(N_b) (+/0, +/−, 0/−) | T_a > T_b |
| sign(N_a) < sign(N_b) | T_a < T_b |
| N_a = N_b = 0 | Certified tie, T = 0 |
| N_a, N_b > 0 | T_a ≥ T_b ⟺ N_a²V_b − N_b²V_a ≥ 0 |
| N_a, N_b < 0 | T_a ≥ T_b ⟺ N_a²V_b − N_b²V_a **≤ 0** |

[PROP] (Q2.5) In S2 form: α = N_a²r_b − N_b²r_a, β = N_a²s_b, c = D_b, γ = −N_b²s_a, e = D_a.

### 4.4 Exact sign algorithms S1 and S2

[PROP] (Q2.1) Inputs are `Fraction`; radicands c, e ≥ 0, else STOP-2; non-`Fraction` coefficient → STOP-2. S1/S2 are total: they always return an exact sign in {−1, 0, +1}.

[PROP] (Q2.2) `sqrt_rat(c)`: reduce c = p/q; if p = isqrt(p)² and q = isqrt(q)², return isqrt(p)/isqrt(q); else None; c = 0 gives 0.

[PROP] (Q2.3) **S1(a, b, c) = sign(a + b√c):**

| Step | Condition | Return |
|---|---|---|
| 1 | b = 0 or c = 0 | sign(a) |
| 2 | r = sqrt_rat(c) not None | sign(a + b·r) |
| 3 | a = 0 | sign(b) |
| 4 | sign(a) = sign(b) | sign(a) |
| 5 | opposite signs; d = a² − b²c | d > 0 → sign(a); d < 0 → sign(b); d = 0 → 0 |

Step 2 is a shortcut; step 5 must agree (tested by the T-dual runs).

[PROP] (Q2.4) **S2(α, β, c, γ, e) = sign(α + β√c + γ√e).** Normalisation in order: N1 β = 0 or c = 0 → S1(α, γ, e); N2 γ = 0 or e = 0 → S1(α, β, c); N3 r = sqrt_rat(c) → S1(α + βr, γ, e); N4 s = sqrt_rat(e) → S1(α + γs, β, c); N5 c = e → S1(α, β + γ, c); N6 k = sqrt_rat(c/e) (e > 0) → S1(α, βk + γ, e). General branch: G1 s_A = S1(α, β, c), s_G = sign(γ); G2 s_A = 0 → s_G; G3 s_A = s_G → s_A; G4 s_d = S1(α² + β²c − γ²e, 2αβ, c); G5 s_d > 0 → s_A, s_d < 0 → s_G, s_d = 0 → 0. Squaring is applied only to compare magnitudes of terms whose signs are already known; no equation is solved.

[ACC] (E2) After N1–N6 the general-branch value is non-zero (proof: squaring α + β√c = −γ√e gives (α² + β²c − γ²e) + 2αβ√c = 0; √c irrational ⇒ 2αβ = 0 ⇒ α = 0 ⇒ c/e = (γ/β)², contradiction). Hence G2 and the zero outcome of G5 are unreachable after normalisation and S1 step 5 cannot give d = 0 for non-square c; these branches remain as defensive code, tested only with `normalize` or `s1_square_shortcut` off.

### 4.5 Threshold branches and membership

[ACC] (E1) For x₀ with N(x₀) > 0:

| Branch | Exact test | τ_x₀ | Threshold |
|---|---|---|---|
| T(x₀) ≥ 1 | S1(N² − n·r, −n·s, D) ≥ 0 (N² ≥ nV) | τ₀·T(x₀) | (1 − τ₀)·T(x₀) |
| 0 < T(x₀) < 1 | S1(…) < 0 | τ₀ | T(x₀) − τ₀ |
| T(x₀) ≤ 0 | — | — | not constructed; STOP-9 if reached |

[ACC] (E1) **Multiplicative membership** (T(x₀) ≥ 1), k = (1 − τ₀)² = (10¹⁰ − 1)²/10²⁰: N_y ≤ 0 → not a member; N_y > 0 → member ⟺ S2(α = N_y²r_x₀ − k·N_x₀²r_y, β = N_y²s_x₀, c = D_x₀, γ = −k·N_x₀²s_y, e = D_y) ≥ 0. Equality is membership.

[ACC] (E1) **Additive membership** (0 < T(x₀) < 1): pre-check 1: if T(y) ≥ T(x₀) (exact, §4.3) → member. Pre-check 2: if N_y ≤ 0 and T(x₀) > τ₀ (exact: S1(N² − nτ₀²r, −nτ₀²s, D) > 0) → not a member. Otherwise interval tier on T(y) − T(x₀) + τ₀ (§4.7): lower bound ≥ 0 → member; upper bound < 0 → not a member; anything else, after refinement to **k = 200**, is UNRESOLVED and goes to the bracket rule.

[COR] The test-only `k_max` of E4 applies only inside the named V0 tests (V0-5, V0-6); it never alters the accepted production boundary k = 200 (§4.7 step 1, step 8).

**R-E1A1 — REJECTED by RD 2026-10-21; not part of the contract.** No additional exact additive pre-check exists beyond E1's pre-checks 1 and 2.

**Documented limitation:** the additive case involves nested radicals 1/√(r + s√D) and is not of the S2 form; no exact decision is claimed for case-I or mixed rational/irrational additive comparisons. If such a comparison is exactly at its threshold, the interval tier cannot resolve it and the outcome is UNRESOLVED (STOP-7 in V1–V5; UNCERTIFIED in V0 Lemma M).

### 4.6 Float pre-screen

[PROP] (X2 tier 1) At production scale (V1–V5 region construction) a float pre-screen may order outcomes; any pair with relative float difference ≤ 10⁻⁹, and any membership test within 10⁻⁹ of its threshold, must be decided by §4.3–§4.5/§4.7. Pairs decided by float alone rely on the assumption that float T error ≪ 10⁻⁹ relative — **an unproven assumption covered by U-3** (§20 MD-3).

[PROP] (Q1) For the V0 Lemma M check, every T is enclosed by rational intervals and **every** comparison and membership is settled by intervals, with non-disjoint pairs sent to the exact tier or refined; no float-only decision is used in V0 Lemma M.

### 4.7 Interval tier (exact algorithm)

All arithmetic on `Fraction`; an interval is (lo, hi) with lo ≤ hi.

1. [COR] **Precision schedule:** k_max must be an integer ≥ 1, else STOP-2. k₀ = min(64, k_max); kᵢ₊₁ = min(2kᵢ, k_max); stop at k_max. **Production k_max is fixed at 200** (sequence 64, 128, 200), matching E1's "refinement to k = 200". A different k_max (e.g., 10) is permitted only inside the named V0 tests (V0-5 M3, V0-6 KS tests) and never in production or V1–V5 (STOP-2, step 8). At each step, every enclosure involved in a decision is recomputed at the same k.
2. **√x enclosure**, x ∈ ℚ, x ≥ 0 (else STOP-2), precision k:
   - [ACC] (E4) L = isqrt(⌊x·4ᵏ⌋) / 2ᵏ; t = isqrt(⌈x·4ᵏ⌉), U = (t + [t² ≠ ⌈x·4ᵏ⌉]) / 2ᵏ; L ≤ √x ≤ U.
   - [COR] Exact integer forms for x = p/q (q > 0): ⌊x·4ᵏ⌋ = (p·4ᵏ) // q; ⌈x·4ᵏ⌉ = −((−p·4ᵏ) // q).
3. [ACC] (E4) **V enclosure:** if s = 0, V = [r, r]; else V ∈ [r + s·L_√D, r + s·U_√D]; intersect with [δ(1 − δ), ∞). [PROP] lo > hi → STOP-9.
4. [ACC] (E4) **√(nV) enclosure:** [L√(n·V_lo), U√(n·V_hi)]. [PROP] (Q2.6) Division requires a positive lower bound; [COR] a lower bound ≤ 0 at k = k_max → STOP-9.
5. [ACC] (E4) **T enclosure:** N = 0 → [0, 0]; N > 0 → [N/U_√nV, N/L_√nV]; N < 0 → [N/L_√nV, N/U_√nV].
6. [COR] **Difference:** for T(y) − T(x₀) + τ₀ use [T_y.lo − T_x₀.hi + τ₀, T_y.hi − T_x₀.lo + τ₀].
7. [COR] **Decisions:** two intervals are **strictly disjoint** iff hi_a < lo_b or hi_b < lo_a; touching (hi_a = lo_b) is not disjoint. Strictly disjoint → certified order. A membership difference interval with lower bound ≥ 0 → certified member; upper bound < 0 → certified non-member. Otherwise refine; not decided at k_max → UNRESOLVED (never a tie). [PROP] lower > upper → STOP-9; an exact-tier result contradicting a strictly disjoint enclosure → STOP-9.
8. [ACC] (E4) Test-only settings `k_max` (default 200), `exact_precheck` (on), `normalize` (on), `s1_square_shortcut` (on) exist only in the test harness; production fixes the defaults; `run_manifest` records all four; any non-default value in V1–V5 → STOP-2.

[COR] Citation: the √x enclosure argument is in Q2.6/E4 (E4's phrase "the E2-proven √x enclosure" is a mis-citation; E2 proves non-zero).

---

## 5. Test decision and certification

5.1 [PROP] (EPG-5 revised, SM1/SM2/SM5) p = min(1, U_cert + η + γ); reject iff p ≤ α. SM5 shortcut: p = 1 when Δ̂ ≤ δ. Flags: |p − α| ≤ 10⁻⁶, determined through bounds (C2). Power reported with flagged outcomes counted as reject and as non-reject.

5.2 [PROP] (C4) Berger–Boos set from a two-sided (1 − γ) Clopper–Pearson interval on ψ, D = x + y: ψ_L = Beta⁻¹(γ/2; D, n − D + 1), ψ_U = Beta⁻¹(1 − γ/2; D + 1, n − D); ψ_U := 1 when D = n; D = 0 is caught by the shortcut. Nuisance domain Q(x) = [max(0, (ψ_L − δ)/2), (ψ_U − δ)/2]. Computed with `scipy.stats.beta.ppf` (pinned) and cross-checked by mpmath bisection on validation sets.

5.3 [PROP] (SM1) Upper bound over q ∈ [a, b]: U[a, b] = Σ_R n!/(x!y!z!)·(b + δ)^x·b^y·(1 − 2a − δ)^z.

5.4 [PROP] (C3) pmf terms evaluated in log space with zero-count cells masked (0⁰ = 1); positive count on a zero-probability cell contributes 0; the same masking applies to the SM1 bound when b = 0 or 1 − 2a − δ = 0. Log-factorials from a table computed in 50-digit mpmath and rounded to float (C9).

5.5 [PROP] (C1 / EPG-10; R1′ provisional per L2) **Decision-equivalent certification:**

- Ū = (SM1 bound maximised over a finite interval cover of Q(x), float) + ρ; L̲ = (largest computed P_q(R(x)) over evaluated q ∈ Q(x), always including both endpoints) − ρ. Mathematically L̲ ≤ S\* ≤ Ū, conditional on rounding ≤ ρ (U-3). The initial cover is an implementation parameter, deterministic and recorded in `run_manifest` before V1 (§20 MD-1).
- Classification in order: (1) Δ̂ ≤ δ → NONREJECT, basis SHORTCUT, p = 1; (2) Ū < θ − φ → REJECT, basis BOUND; (3) L̲ > θ + φ → NONREJECT, basis BOUND; (4) otherwise refine by deterministic bisection (largest-U interval first, ties by left endpoint) until Ū − L̲ ≤ ε; then p_cert = U_float + η + γ; REJECT iff p_cert ≤ α; FLAGGED iff |p_cert − α| ≤ φ; basis REFINED; (5) depth cap (64 bisections) or non-finite value → UNRESOLVED.
- [PROP] (C2) An outcome may be finalised without refinement only if its whole bracket lies outside F = [θ − φ, θ + φ].
- Equivalence (conditional on ρ, ε + 2ρ < φ): for every outcome neither FLAGGED nor UNRESOLVED the R1′ decision equals every literal R1 implementation's decision; flag sets may differ only where S\* lies within ε + 2ρ of θ ± φ.
- FLAGGED: listed; power both ways. UNRESOLVED: never a default non-rejection; record [P_lo, P_hi]; STOP-7. FAILED: STOP-2.
- Decision-certified rejection region = REJECT set plus flagged list; fully numerically certified p-value only for REFINED outcomes and literal-R1 validation sets; others carry [L̲ + η + γ, Ū + η + γ].
- Ledger fields per outcome: `decision`, `basis ∈ {SHORTCUT, BOUND, REFINED}`, `p_lo`, `p_hi`, `p_cert` (or null), `flagged`, `unresolved`.

---

## 6. Scenarios, grid and power reporting (full grid; blocked)

6.1 [PROP] (EPG-4) Independence: p₁₀ = (1 − p₀)p₂, p₀₁ = p₀(1 − p₂). Fréchet: p₀₁ = min(p₀, 1 − p₂), p₁₀ = p₀₁ + δ + g. p₂ = p₀ + δ + g. Cells non-negative over [0, 1 − δ − g]; Fréchet has a kink at (1 − δ − g)/2. Grid n = 50…600 step 1; n = 600 is a computational limit, not N_avail.

6.2 [PROP] (EPG-3 revised, K-b/X3) p₀ swept over exact rationals k/200 within [0, 1 − δ − g], plus the trimmed range [1/20, 1 − δ − g − 1/20]; δ, g, p₀ and all search nodes generated as exact rationals, membership tested exactly, converted to float only afterwards; optional local golden-section points must stay inside I. Report the minimum over all evaluated points. Exploratory only; SM8 binding.

6.3 [PROP] (EPG-14) Flagged and unresolved outcomes counted as reject (R_high) for upper bounds on size and power, and as non-reject (R_low) for lower bounds on power.

6.4 [PROP] (EPG-14 (a)–(e), K-b, K-c, K-d) "If n\*(600) exists for the stated scenario, (δ, g) and I, then n\*(600) ≥ n_G(600)", proven conditional on U-3 and on: (a) R_high; (b) threshold 0.80 − ρ_P; (c) same p₀ range, G ⊆ I; (d) same upper end N (not a lower bound for Option B over [n, N_avail] when N_avail < 600); (e) the stated planning assumptions; K-b exact grid; K-c existence (n_G does not imply a feasible n exists); K-d floor at n = 50.

6.5 [PROP] (K-a, X5) Infeasibility at N_avail = M only if some p₀ ∈ G has P_hi(M, p₀) + ρ_P < 0.80; relative to the exploratory range I; conditional on U-3; not SM8 VOID. **n_G > N_avail does not establish infeasibility.**

6.6 [PROP] (C5) Grid minima are upper bounds on true minimum power; global minimum not certified.

---

## 7. Composite-null validity and Lemma M

7.1 [PROP] (X1) Model X ~ Multinomial(n; p₁₀, p₀₁, p_c); Δ = p₁₀ − p₀₁, ψ = p₁₀ + p₀₁; Θ₀ = {p₁₀, p₀₁ ≥ 0, ψ ≤ 1, Δ ≤ δ}. Frozen test domain A(x) = Θ_B ∩ C(x) (SM3/SM4), unchanged.

7.2 [PROP] **Lemma M (unproven):** at fixed (n, δ, τ), every R(x) with Δ̂(x) > δ is upward-closed under z→x (x + 1, y, z − 1) and y→z (x, y − 1, z + 1).

7.3 [PROP] Coupling lemma and theorem (X1, full text in recovery Part 2 §8): if Lemma M holds at (n, δ, τ), sup_{Θ₀} P_θ(p(X) ≤ α) ≤ α. Relies on standard Clopper–Pearson coverage and discrete super-uniformity (cited, not re-derived) and on computed p ≥ true p (U-3 or the SM6 η model). SRC reviewed the coupling lemma and conditional theorem as PASS (review evidence, not RD acceptance; not independently re-verified here). The SRC segment expansion is not adopted.

7.4 [PROP] (Amendment B) **Lemma M check** at fixed (n, δ, τ): consider outcomes a with T(a) at least the smallest threshold; for each valid move a → a′ (z→x needs z ≥ 1; y→z needs y ≥ 1): T(a′) ≥ T(a) certified → fine; otherwise test whether some observed x₀ with N(x₀) > 0 has a ∈ R(x₀), a′ ∉ R(x₀) (both certified) → VIOLATED witness; any unresolved required comparison/membership → UNCERTIFIED; otherwise CERTIFIED. This supersedes B8 (C7).

7.5 [PROP] One record per DPID in `v0_lemmaM.jsonl` with DPID, n, δ and τ as exact strings, specification and code hashes, status, counts, any witness with exact certificate, and verbatim:

> `CERTIFICATION APPLIES ONLY TO THIS (n, δ, τ), STATISTIC VERSION AND CODE VERSION. IT CONFERS NOTHING ON ANY OTHER n, δ OR τ, INCLUDING ANY CONFIRMATORY DESIGN. NO INTERPOLATION OR EXTRAPOLATION.`

Results listed per DPID only; no aggregate claim; a VIOLATED or UNCERTIFIED status is a reported finding, not a STOP; non-CERTIFIED status makes dense R3b mandatory in V3.

7.6 [PROP] U-2 status: **BLOCKED** for confirmatory use (Lemma M at the confirmatory design point, independent review, U-3).

---

## 8. Numerical assurance tiers

[PROP] (X6) Empirical agreement ≠ decision-certified under assumptions ≠ rigorous error bound ≠ certified global lower bound on power. U-3 obligations: rigorous enclosures of pmf sums, q̃ and T, Clopper–Pearson endpoints, certified B&B termination. U-4 obligations: U-3 for power, a proven lower-bound function on p₀ subintervals, certified covering of I, R_low region, independent review. **V0–V5 cannot close U-3 or U-4.**

---

## 9. Acceptance criteria

| ID | Criterion | Tag |
|---|---|---|
| R1 | Literal: every Δ̂ > δ outcome reaches max U − L ≤ 10⁻⁷; applied on validation sets only | [PROP] |
| R1′ | §5.5 at production scale (provisional, L2) | [PROP] |
| R2 | Dense-grid lower bound (≥ 2,001 points plus Berger–Boos endpoints) never exceeds U + 10⁻¹² | [PROP] |
| R3 | Exact size on a 2,001-point grid of p₀₁ along the null boundary ≤ α + 10⁻¹², computed on R_high; **diagnostic only, stops on violation, certifies nothing** | [PROP] |
| R3b | Exact size at interior null points Δ < δ on a 21 × 21 grid over (p₀₁, Δ ∈ [0, δ]) ≤ α + 10⁻¹² on R_high; dense 101 × 101 where Lemma M is not CERTIFIED; diagnostic only (does not probe Δ < 0) | [PROP] |
| R4 | Flagged cells listed and counted (flags via bounds, C2) | [PROP] |
| R5 | Float gap diagnostic per §4.2 (report-only; never a tie) | [COR] |
| R6 | Two runs give byte-identical ledger SHA-256 (n ∈ {50, 100}); single-threaded BLAS; units merged in sorted order | [PROP] |
| P1 | `math.fsum` of all trinomial probabilities = 1 ± 10⁻¹² | [PROP] |
| P2 | Same-author mpmath cross-check (50 digits, brute-force tails, own B&B), n ∈ {50, 51, 80} × 5 δ. Class XCHK. **(a) Per-quantity agreement** [COR]: for every SM1 bound U[a, b] and every point probability P_q(R(x)) evaluated on the float path, the mpmath path recomputes **the same quantity on the same interval or point and the same tail region**; \|float − mpmath\| ≤ ρ/100. **(b) Decision agreement** [COR] (comparison domain per L9 D1): **both paths run literal R1** (row R1) on the P2 validation sets, so every Δ̂ > δ outcome is refined to max U − L ≤ 10⁻⁷ on each path and has U_cert and p_cert on both paths; if any Δ̂ > δ outcome does not satisfy R1 on either path, the comparison is undefined for it and P2 fails (STOP-4). On this domain: decisions identical on outcomes unflagged by both paths; **flag-set differences are allowed only where the mpmath p_cert lies within φ ± (ε + 2ρ) of α; any other flag-set difference → STOP-4**; \|U_cert,float − U_cert,mpmath\| ≤ ε + 2ρ for every Δ̂ > δ outcome. **(c) Power agreement — [BLOCKED] — NOT PERFORMED** (L9 D2): the 10⁻¹⁰ power-agreement test is removed from the mandatory gate because no evaluation points are specified; it awaits a separately specified finite evaluation set and acceptance rule. It is **not a pass and does not establish power agreement**. **(d)** Clopper–Pearson endpoints agree. Literal-R1 agreement on these sets shows only cross-path consistency of the implementation; it does not establish statistical validity. **Not independent certification** | [PROP]/[COR] |
| P3 | Power at the null boundary ≤ α (diagnostic, with R3) | [PROP] |
| P4 | Differences from spike v0.11 planning figures reported for information only | [PROP] |
| B1 | Every outcome n ≤ 20 × δ ∈ {10⁻⁶, 1/50, 1/25, 3/50, 2/25, 1/10, 1/4, 1/2, 9/10, 1 − 10⁻⁶}: q̃ matches the high-precision KKT reference within 10⁻¹³ absolute; no grid point or endpoint has higher log-likelihood within 10⁻²⁵ relative. Reference method (as used in the recovered scratch evidence, restricted-MLE correction memo §5): mpmath at 40 significant digits, bisection on ℓ′, boundary cases decided by KKT. This method is [PROP], not accepted. **Class XCHK: same-author cross-check — not an independent expected result** | [PROP] |
| B2 | Boundary fixtures: all-x, all-y, all-z; single and paired zeros; n = 1 per cell; exact switch at rational δ and neighbours. [COR] (L9 D3) Class **IND** only for fixtures whose q̃ is determined by the explicit §3.3 rules (case U: z = 0 → q̃ = u; case 0: y = 0 and x(1 − δ) ≤ 2zδ → q̃ = 0; case I0: q̃ = [x(1 − δ) − 2zδ]/(2n)); class **XCHK** for interior case-I fixtures (y > 0, z > 0), which are checked through the B1 reference | [PROP] |
| B3 | Each case U, 0, I0, I hit in B1 and at production scale. [COR] (L10 A) Production scale = **n = 600 × δ ∈ {1/50, 1/25, 3/50, 2/25, 1/10}** (the five EPG-4 grid values, equal to the §2 δ set), as defined by the source of B3/B6 (restricted-MLE correction memo §5: "Production-scale float check, n = 600 × 5 grid values of δ (904,505)"; §6 B3/B6 "at production scale"). [COR] (L9 D3) Class **STRUCT** (coverage count) | [PROP]; n = 600 δ set **confirmed by RD 2026-10-22 (L11)** — source CSE-proposed text, not independently validated |
| B4 | V ≥ δ(1 − δ)·(1 − 10⁻¹⁵); T finite | [PROP] |
| B5 | sign(T) = sign(x − y − nδ) when \|x − y − nδ\| > 10⁻¹² | [PROP] |
| B6 | Zero interior-root assertion failures at production scale (n = 600 × δ ∈ {1/50, 1/25, 3/50, 2/25, 1/10}; source as for B3). [COR] (L10 B) **Necessary-condition property check:** for every evaluated case-I outcome, the computed root q̃ is checked for strict membership in (0, u) (§3.3 step 6). Passing establishes **only that no violation was observed in the evaluated cases**. It does **not** establish root correctness, numerical accuracy, structural completeness, or the general mathematical claim that the case-I root always lies in (0, u) (that derivation is CSE text, not independently reviewed). Class **IND** only for the stated property, which the contract specifies (§3.3 steps 5–6); no implementation is thereby independently validated | [PROP]; n = 600 δ set **confirmed by RD 2026-10-22 (L11)** — source CSE-proposed text, not independently validated |
| B7 | \|T_float − T_ref\| ≤ 10⁻¹²·max(1, \|T\|) on B1. Class XCHK (T_ref comes from the B1 same-author reference) | [PROP] |
| B8 | Superseded by the Lemma M check (§7.4) | [PROP] |

Any failure stops the run; thresholds may not change after any power output exists (EPG-6).

---

## 10. V0–V5 checklist

10.1 Preconditions [PROP]: R-ACC decided; this contract frozen and its SHA-256 recorded (§13.1); RD authorization recorded (§19); venue, `env.lock` SHA-256 and network method entered; thresholds fixed as of the record.

10.2 **Stage outcome states** [COR]: each stage reports exactly one of **PASS** (every **mandatory** item executed and passed; no mandatory item BLOCKED), **FAIL** (a STOP occurred), or **BLOCKED** (a mandatory item is [BLOCKED] or [PEND] and was not performed). **BLOCKED is never PASS.** A **non-mandatory** [BLOCKED] item is reported as NOT PERFORMED; it does not prevent PASS and never counts toward PASS. A stage that is BLOCKED or FAIL stops the chain; no later stage starts.

10.3 **V0 — test manifest** ([COR] merge, components tagged; "Mandatory" column per R-TINY and L8):

| # | Item | Mandatory | Expected result / oracle | Class | Tag | STOP on failure |
|---|---|---|---|---|---|---|
| V0-1 | Design-point matrix: n = 1…80 × δ ∈ {1/50, 1/25, 3/50, 2/25, 1/10} × τ₀ = 1/10¹⁰; order (n, δ) ascending | Yes | Exactly 400 unique DPIDs | STRUCT | [ACC] n-range and 400 count; [PROP] δ set, τ₀, order (Q1) | STOP-2 (count ≠ 400) |
| V0-2 | Exact rational grid construction (K-b/X3) | Yes | All points exact rationals; membership tested exactly | STRUCT | [PROP] | STOP-2 |
| V0-3 | B1–B7 (B1 on n ≤ 20 × the 10-value δ set; B3 and B6 also at n = 600 × the §2 δ set {1/50, 1/25, 3/50, 2/25, 1/10}) | Yes | §9 criteria | B1, B7: **XCHK**; B2: **IND** for §3.3 rule-determined fixtures (cases U, 0, I0), **XCHK** for interior case-I fixtures (via B1); B3: **STRUCT**; B4, B5: IND; B6: **IND (necessary-condition property only; not root correctness)** | [PROP]; B2/B3 classes [COR] (L9 D3); B3/B6 δ set and B6 boundary [COR] (L10) | STOP-1 |
| V0-4 | Full Amendment A degeneracy matrix: every §4.3 row exercised by the vectors mapped in §10.3.1 | Yes | §14 expected values via the §10.3.1 mapping | IND | [PROP]; A1-rev, A3-rev, A4-self [COR] (L8) | STOP-1 |
| V0-5 | `v0_exactcmp.json`: T1–T15, T16, T17, I1, T-dual (T4, T5, T16 with `s1_square_shortcut` off), U1–U14, U14′, U16, U17, U9d, U18, A1–A9 (A7 in E3 form), A1-rev, A3-rev, A4-self, M1, M1′, M2, M3, TB1, TB2, I2 | Yes | §14 expected values | IND | NEW rows [ACC] (E5); A7 form [ACC] (E3); M2 path [ACC] (E1); M3 settings [ACC] (E4); A1-rev, A3-rev, A4-self [COR] (L8); others [PROP] | STOP-1 |
| V0-6 | Interval-tier tests IV1–IV6 and schedule tests KS1–KS5 (§14) | Yes | §14 expected values | IND | [COR] | STOP-1 (IV, KS1–KS4); STOP-2 (KS5) |
| V0-7a | Tiny-n (n ≤ 6), exact pmf values for every outcome and every rational parameter point in the listed cases | Yes | The multinomial formula n!/(x!y!z!)·p₁₀^x·p₀₁^y·p_c^z evaluated in `Fraction`, compared exactly with the production pmf | IND | [PROP] (X4); oracle definition [COR] | STOP-1 |
| V0-7b | Tiny-n T ordering for every outcome pair at each δ in the δ set | Yes | A separate reference implementation of §4.3/§4.4 in the test module, compared with production ordering | **XCHK — same-author cross-check — not an independent expected result** | [PROP]/[COR] | STOP-1 |
| V0-7c | Tiny-n tail sets R(x₀) for every x₀ with N(x₀) > 0 | Yes | Tail sets built from V0-7b comparisons and §4.5, compared with production tail construction | **XCHK — same-author cross-check — not an independent expected result** | [PROP]/[COR] | STOP-1 |
| V0-7d | Tiny-n exact size at rational null points, including ψ < δ | **No** (R-TINY) | **[BLOCKED] — NOT PERFORMED.** No source specifies the null-point set, the rejection region to evaluate or an acceptance criterion; none is defined here | — | [BLOCKED] (R-TINY, L8) | — |
| V0-8 | Lemma M check (§7.4) for all 400 DPIDs | Yes | Exactly 400 records, each with status ∈ {CERTIFIED, VIOLATED, UNCERTIFIED} and the verbatim §7.5 scope text | STRUCT | [PROP] | STOP-2 (missing record or scope text) |
| V0-9 | E4 test-only settings used only inside V0-5/V0-6 named tests; production defaults recorded | Yes | Manifest check | STRUCT | [ACC] | STOP-2 |
| V0-10 | Static network-import check (§12.3) | Yes | No forbidden import in `egrid` sources | STRUCT | [COR] | STOP-1 |
| V0-11 | Outputs `v0_mle.json`, `v0_exactcmp.json`, `v0_interval.json`, `v0_tiny_exact.json`, `v0_lemmaM.jsonl` present and listed in `run_manifest` | Yes | Presence and SHA-256 recorded | STRUCT | [PROP] (+ `v0_interval.json` [COR]) | INCOMPLETE → not PASS |

10.3.1 **Degeneracy-row mapping** [COR] (every §4.3 row; inputs and expected results in §14):

| §4.3 row | Vectors | Coverage note |
|---|---|---|
| Invalid inputs → STOP-2 | I2 (δ = 1, n = 0, negative count); T17, U18 (negative radicand); I1 (non-`Fraction`) | Trigger exercised |
| V ≤ 0, discriminant ≤ 0, q̃ ∉ [0, u] → STOP-9 | A9 (invariant S1(r, s, D) = +1 holds for every V) | Positive invariant only. With valid inputs this STOP-9 trigger is unreachable (Amendment A invariant); its trigger path is **not exercised** by any vector. Coverage limitation, recorded in the V0 report |
| Same outcome → equal | A4-self | Trigger exercised |
| sign(N_a) > sign(N_b) | A1 (+/−), A3 (0/−) | Sub-case +/0 not separately exercised |
| sign(N_a) < sign(N_b) | A1-rev, A3-rev | Trigger exercised |
| N_a = N_b = 0 → certified tie | A2 | Trigger exercised |
| N_a, N_b > 0 | A4, A8 | Trigger exercised |
| N_a, N_b < 0 (reversed inequality) | A5, A7 | Trigger exercised |

**Fail-closed rules** [COR]:

- V0 = FAIL (STOP-1) if any mandatory test or check in V0-3 – V0-7c or V0-10, or any test ID listed in V0-5 or V0-6, is absent, skipped, errors, or lacks a recorded expected result.
- V0 = FAIL (STOP-2) if V0-8 has fewer or more than 400 records or any record lacks the scope text.
- **V0 PASS is determined only by the mandatory items V0-1 – V0-7c and V0-8 – V0-11.** V0-7d is non-mandatory, [BLOCKED] and NOT PERFORMED (R-TINY). The V0 report must state verbatim: `EXACT-SIZE VALIDATION (V0-7d) WAS NOT COMPLETED AND WAS NOT PART OF PASS.`
- The V0 report lists separately the mandatory checks with **IND** expected results, the mandatory **XCHK** checks (V0-7b, V0-7c, B1, B7, B2 interior case-I fixtures), each XCHK labelled `same-author cross-check — not an independent expected result`, and the **STRUCT** checks (including B3).
- A Lemma M VIOLATED or UNCERTIFIED status is a reported finding and does not by itself change V0's outcome state.
- STOP-8 applies at the V0 cap (§11.1).

10.4 **V1** [PROP]: literal R1 vs R1′ on n ∈ {50, 51, 80} × 5 δ: identical decisions on outcomes unflagged by both; flag-set differences only where literal \|p_lit − α\| lies within φ ± (ε + 2ρ); zero UNRESOLVED. STOP-3, STOP-7; STOP-8. Output `v1_r1_vs_r1p.jsonl`.

10.5 **V2** [PROP]: P2 on the same sets as V1 (class XCHK), with **both paths running literal R1** (L9 D1). Mandatory: P2 (a), (b) and (d). **P2 (c) is non-mandatory, [BLOCKED], NOT PERFORMED** (L9 D2); it is not a pass and does not establish power agreement, and the V2 report must state verbatim: `P2 (c) POWER AGREEMENT WAS NOT PERFORMED AND WAS NOT PART OF PASS.` STOP-4; STOP-8. Output `v2_p2.jsonl`.

10.6 **V3** [PROP]: R2; R3 and R3b on R_high (boundary, segment, interior; dense where Lemma M is not CERTIFIED); P1; P3; all within 10⁻¹²; diagnostics only. STOP-5; STOP-8. Output `v3_diag.json`.

10.7 **V4** [PROP]: R6, two runs at n ∈ {50, 100}, byte-identical ledger SHA-256. STOP-6; STOP-8. Output `v4_hashes.txt`.

10.8 **V5** — **[RD-PROV] scope** (R-V5, 2026-10-21; provisional, subject to consistency with the R1′ objective; not previously accepted): rejection-region construction only (R1′), **no power**, at **n ∈ {100, 300, 600} × δ ∈ {1/50, 1/10}** (six regions). Provenance: carried forward from superseded package §E6 and reconciliation §2 tables; consistent with Amendment C's "6 regions up to n = 600".

- **Observed timings (required for V5 PASS):** CPU seconds per region, outcome counts and basis counts (SHORTCUT/BOUND/REFINED/FLAGGED/UNRESOLVED) per region, with the MD-1 cover recorded. Output `v5_timing.json`. These are reported **only as observations**. STOP-7; STOP-8.
- **Projected full-grid cost: [BLOCKED]** (`R-PROJ: decided 2026-10-21; full-grid projection remains BLOCKED`). No projection method is specified in any source. **Not computed and not reported**, and not part of V5 PASS.
- **CSE assessment only; not an RD finding; R-V5 remains provisional:** the six regions exercise R1′ region construction at both ends and the middle of n = 50…600 and at both extreme δ values; as an observed-timing probe of R1′ this appears consistent with the R1′ objective. The assessment does not cover any projection.

10.9 **Report** [PROP]: manifest, environment record and final report complete with labels; a missing artifact → run reported **INCOMPLETE** (not PASS).

---

## 11. Resource budget and STOP rules

11.1 **STOP-8 / budget statement** ([PROP] cap values from Amendment C; [COR] consolidated wording and enforcement):

- **Process model** [COR]: each stage runs as a **single Python process with no worker or child processes**. Spawning any process → STOP-2. The caps below are enforced as stated only under this process model; the contract permits no other.
- CPU time is measured per stage as process CPU time (`getrusage`, self; children are not permitted).
- Hard caps: **V0 1800 s, V1 900 s, V2 5400 s, V3 900 s, V4 1800 s, V5 3600 s; total 14,400 s (4 CPU-h)**. Budget unused by one stage never transfers to another. No cap may be raised without a new RD decision. No automatic S8.
- **In-process monitor:** the stage driver checks its accumulated CPU time before each work unit and at a recorded periodic interval within long units, and stops voluntarily at (cap − reserve), where the reserve is a recorded implementation parameter intended to leave time to write STOP-8 artifacts. It then writes partial artifacts, CPU used and STOP-8.
- **Host-side backstop:** the container runs with a hard CPU limit equal to the stage cap (`--ulimit cpu=<cap>`). If the kernel terminates the stage (e.g., SIGXCPU or SIGKILL), the host-side wrapper records **STOP-8 (BACKSTOP)** with the exit status; artifacts from that stage **may be incomplete and are never claimed complete**.
- On STOP-8 in any form: no later stage starts; the result is reported unchanged.
- The 24 CPU-hour cap (EPG-7) applies only to the full grid, which is blocked.

11.2 Consolidated STOP rules [PROP unless tagged]:

| STOP | Condition |
|---|---|
| STOP-1 | A B-test fails; [COR] any mandatory V0 test or check with a specified expected result fails, errors, is skipped, is absent or lacks its expected result (V0-3 – V0-7c, V0-10; not V0-7d, which is non-mandatory and not performed) |
| STOP-2 | Invalid input (including invalid k_max [COR]); NaN or Inf; an assertion; a negative probability; an empty Berger–Boos domain when Δ̂ > δ; a negative radicand or non-`Fraction` coefficient; DPID count ≠ 400 ([ACC] count; [PROP] check); Lemma M record count ≠ 400 or missing scope text [COR]; a non-default test-only setting in V1–V5 [ACC E4]; any spawned worker or child process [COR] |
| STOP-3 | R1 vs R1′ mismatch outside the permitted sliver (§10.4) |
| STOP-4 | P2 (a), (b) or (d) failure (§9), including a flag-set difference outside φ ± (ε + 2ρ) of α or any Δ̂ > δ outcome not satisfying R1 on either path. (P2 (c) is not performed and cannot trigger STOP-4.) |
| STOP-5 | R2, R3, R3b, P1 or P3 violation (diagnostics; they stop but certify nothing) |
| STOP-6 | R6 hash mismatch |
| STOP-7 | [COR scope] Any UNRESOLVED outcome in R1′ classification or region construction (V1–V5; §5.5 step 5 or final tail-membership status); stop after recording the unit's power bracket. Not applicable to the V0 Lemma M check, where unresolved comparisons yield UNCERTIFIED |
| STOP-8 | §11.1 (in-process or BACKSTOP) |
| STOP-9 | V ≤ 0; discriminant ≤ 0; q̃ outside its domain; S1(r, s, D) ≠ +1; an inverted interval; an exact result contradicting a strictly disjoint enclosure; tail construction reached with N(x₀) ≤ 0 [ACC E1]; [COR] √(nV) lower bound ≤ 0 at k_max |

On any STOP: halt, keep artifacts, change no threshold, report unchanged.

---

## 12. Environment and reproducibility

12.1 [PROP] (Amendment D, as reworded [COR]) The environment record consists of `env.lock` and `env_record.json` produced by `stats/egrid/env/make_env_record.py` inside the pinned image: venue, OS/kernel, CPU model, Python version/build, the **sorted installed-distribution list (`importlib.metadata`) recorded in `env.lock`, pinned by the immutable image ID** [COR, replaces "`pip freeze` and its SHA-256"], numpy BLAS configuration, image ID and base-image digest, deterministic variables (`OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, `NUMEXPR_NUM_THREADS` = 1; `PYTHONHASHSEED=0`; `PYTHONDONTWRITEBYTECODE=1`), `RLIMIT_AS` = 2 GiB per process, cgroup limits, and observed isolation controls.

12.2 [PROP] Execution flags (documented in `env/README_ENV.md` §4): `--network none --cpus=1 --memory=2g --memory-swap=2g --pids-limit=64 --read-only --tmpfs /tmp --cap-drop=ALL --security-opt=no-new-privileges --user 1000:1000`, per-stage `--ulimit cpu=<cap>` as the host-side backstop (§11.1), in-process `RLIMIT_AS` 2 GiB. The image is never rebuilt between V0 and V5. `Dockerfile` and `requirements.txt` are build inputs and are not modified.

12.3 [COR] (rewords Amendment D's static check) A V0 unit test AST-scans the future `stats/egrid/egrid/` sources and fails if any module imports `socket`, `http`, `urllib`, `requests`, `ssl`, `ftplib`, `smtplib` or `subprocess`. `env/make_env_record.py` is excluded (it imports `socket` intentionally for the runtime probe). Isolation evidence remains `--network none` plus the runtime probe.

12.4 Current evidence (owner-generated; content checked by CSE; not entered into any record):

| Item | Value |
|---|---|
| Venue | `wsl-docker` (kernel `6.18.33.1-microsoft-standard-WSL2`) |
| Image ID | `sha256:dbae1d05a21601ef6de1ea2d970237f0d6d86b189b0cc19bbb1f90d9821706cb` |
| Base digest | `python@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db` |
| `env.lock` SHA-256 | `02153e0965ecdd02f1c607f37498996df181b03da1308f093ba0db6917fdd1ca` |
| `env_record.json` SHA-256 | `8878ad8bf796215649c06630fac167fee45f547b8c8bae94f0da10a19a9b98f4` |
| Observed controls | all 8 PASS (loopback only, ENETUNREACH, cpu.max 1 CPU, memory.max 2 GiB, RLIMIT_AS 2 GiB, deterministic env vars, EROFS root, uid 1000) |
| Note | 12 CPUs visible vs 1-CPU quota: the stage driver must not size worker pools from `os.cpu_count()` |

---

## 13. Identity, manifest, ledgers and outputs

13.1 [COR] **Contract identity.**

- *Candidate identity* (this file, unfrozen): `EPG14-CONTRACT@CAND-2-UNFROZEN`. Any DPID or ledger computed with the candidate identity is development-only and **must not appear in any validation ledger**.
- *Frozen identity*: `EPG14-CONTRACT@<sha256>`, where `<sha256>` is the SHA-256 of the frozen contract file recorded in the RD authorization. V0–V5 require the frozen identity (§10.1).
- **Hash method** [COR]: the contract SHA-256 is calculated over the exact file bytes with **LF line endings**, using `sha256sum` in WSL on the **committed** file; the method is recorded alongside the hash. No hash computed before the file is committed is a frozen identity.
- *Authorization-record hash*: its format remains to be fixed when the authorization record is created. **No authorization record exists.**
- *Environment identity* (image ID, `env.lock` SHA-256, §12.4) is distinct from the contract identity and from DPIDs; it is bound to runs only through `run_manifest`.

13.2 [PROP]/[COR] DPID = SHA-256 of canonical JSON `{"schema":"egrid.dp.v1","n":…,"delta":"p/q","tau":"p/q","statistic":"EPG14-CONTRACT@<sha256>#S3","tie_rule":"EPG14-CONTRACT@<sha256>#S4","test":"EPG14-CONTRACT@<sha256>#S5"}`; sorted keys, `(",", ":")` separators, UTF-8; δ and τ in lowest terms. Power-evaluation identity adds `g`, `p0` (exact), `scenario`, `range`. (Schema [PROP], Amendment D; hash fields [COR].)

13.3 [PROP] `run_manifest.json`: run_id; authorization record hash; frozen contract identity; code SHA-256 per file; all thresholds as exact strings; grids as exact rationals; environment record hash; per stage start/end, CPU (self + children), outcome state (PASS/FAIL/BLOCKED), STOP code; the MD-1 cover, the STOP-8 reserve and check interval; every output with SHA-256; label strings; the four E4 test-only settings.

13.4 [PROP] Ledgers: canonical JSON; floats via `float.hex()`; rationals as strings; records in sorted DPID order.

13.5 [PROP] Final report `v_report.json` + `v_report.md`: outcome state and STOP code per stage; CPU vs each cap; counts of flagged, unresolved and certified-tie outcomes; Lemma M status per DPID with scope text; list of [BLOCKED] items not performed, including the verbatim V0-7d statement (§10.3) and the verbatim P2 (c) statement (§10.5); [COR] separate lists of IND and XCHK checks, each XCHK labelled `same-author cross-check — not an independent expected result`; the §10.3.1 coverage limitations; labels (§17); prohibited claims (§16).

---

## 14. Test vectors and tests

Hand-derived, **never executed**; expected values are claims to be tested, not verified results.

**S1(a, b, c):** T1 (3, 0, 7) → +1; T2 (−2, 5, 0) → −1; T3 (0, 0, 5) → 0; T4 (1, −1, 4) → −1; T5 (−3, 2, 9/4) → 0; T6 (2, 3, 2) → +1; T7 (−2, −3, 2) → −1; T8 (0, −1, 3) → −1; T9 (3, −2, 2) → +1; T10 (−3, 2, 2) → −1; T11 (1, −1, 2) → −1; T12 (99, −70, 2) → +1; T13 (−99, 70, 2) → −1; T14 (577, −408, 2) → +1; T15 (1, −1, (10³⁰ + 1)/10³⁰) → −1; T16 (−2, 1, Fraction(8, 2)) → 0; T17 c = −1 → STOP-2; **I1** a = 0.5 (float) → STOP-2 [ACC]; T-dual: T4, T5, T16 with the shortcut off → same results. [PROP] except I1.

**S2(α, β, c, γ, e):** U1 (1, 0, 5, −1, 2) → −1; U2 (−1, 7, 0, 1, 3) → +1; U3 (2, −1, 5, 0, 7) → −1; U4 (−2, 1, 5, 3, 0) → +1; U5 (1, 1, 4, −1, 10) → −1; U6 (0, 1, 2, −1, 9/4) → −1; U7 (1, 2, 3, −2, 3) → +1; U8 (0, 1, 5, −1, 5) → 0; U9 (0, 1, 8, −2, 2) → 0; U10 (1, 1, 2, 1, 3) → +1; U11 (0, 1, 3, −1, 2) → +1; U12 (0, 1, 2, −1, 3) → −1; U13 (1, 1, 2, −1, 6) → −1; U14 (−157313/50000, 1, 2, 1, 3) → +1; U14′ (−314627/100000, 1, 2, 1, 3) → −1; U16 (0, 5, 0, −4, 0) → 0. (There is no U15.) [PROP]. **U17** (−2, 1, 4, 1, 3), `normalize` off → +1 via G2; **U9d** (0, 1, 8, −2, 2), `normalize` off → 0 via G5; **U18** e = −1/4 → STOP-2. [ACC]

**Application (δ = 1/10):** A1 n = 5, a = (5, 0, 0), b = (0, 5, 0) → T_a > T_b; A2 n = 10, a = (1, 0, 9), b = (2, 1, 7) → certified tie (T = 0); A3 n = 10, a = (1, 0, 9), b = (0, 0, 10) → T_a > T_b; A4 n = 5, a = (5, 0, 0) [U, V = 99/100, N = 9/2], b = (2, 0, 3) [I0, q̃ = 3/25, V = 33/100, N = 3/2] → Δ_ab = 891/200 > 0, T_a > T_b; A5 n = 5, a = (0, 5, 0) [V = 99/100, N = −11/2], b = (0, 0, 5) [case 0, V = 9/100, N = −1/2] → Δ_ab = 990/400 > 0, both negative ⇒ **T_a < T_b**; A6 n = 5, a = (0, 2, 3) [I, B = −4/5, C = −9/50, D = 196/25, q̃ = 9/50, r = 17/100, s = 1/10, V = 9/20] → T = −5/3 exactly; **A7** n = 3, a = (1, 1, 1) [I, B = −7/5, C = −9/100, D = 103/25, r = 97/300, s = 1/6, N = −3/10], b = (0, 0, 3) [case 0, V = 9/100, N = −3/10] → S1(−21/1000, −3/200, 103/25) = −1 ⇒ T_a > T_b [ACC form, E3]; A8 n = 6, a = (3, 1, 2) [B = −3, D = 333/25, r = 17/50, s = 1/12, N = 7/5], b = (2, 1, 3) [B = −19/10, D = 793/100, r = 149/600, s = 1/12, N = 2/5] → S2(1297/3000, 49/300, 793/100, −1/75, 333/25) = +1 ⇒ T_a > T_b; A9 every V: S1(r, s, D) = +1, else STOP-9. [PROP] except A7 form.

**Added degeneracy vectors** [COR] (L8; derived from the §4.3 rules, no new thresholds; δ = 1/10): **A1-rev** n = 5, a = (0, 5, 0) [N = −11/2], b = (5, 0, 0) [N = 9/2] → sign(N_a) < sign(N_b) ⇒ **T_a < T_b**; **A3-rev** n = 10, a = (0, 0, 10) [N = −1], b = (1, 0, 9) [N = 0] → sign(N_a) < sign(N_b) ⇒ **T_a < T_b**; **A4-self** n = 5, a = b = (5, 0, 0) (A4's a on both sides) → same outcome ⇒ **equal**.

**Membership/boundary:** M1 n = 5, x₀ = y = (5, 0, 0) → member (T ≥ 1, multiplicative); M1′ same x₀, y = (2, 0, 3) → not a member [PROP]; **M2** n = 1, x₀ = y = (1, 0, 0) → member by exact pre-check 1 [ACC path]; **M3** as M2 with `exact_precheck` off, `k_max` = 10 → UNRESOLVED, bracket rule [ACC]; **TB1** n = 100, x₀ = (13, 0, 87) [case 0, V = 9/100, N = 3] → T = 1 exactly, multiplicative branch, threshold 1 − τ₀ [ACC]; **TB2** n = 5, tail for x₀ = (0, 0, 5) → STOP-9 [ACC]; **I2** δ = 1, n = 0 or a negative count → STOP-2 [ACC].

**Interval-enclosure invariant tests** [COR] (expected properties of §4.7 step 2; to be tested, not claimed proven here). For x in a recorded list of rationals including 0, 1, 2, 9/4, 103/25, 793/100, (10³⁰ + 1)/10³⁰ and 1/10¹⁰, and for every k in the production schedule:

- **IV1** L ≥ 0.
- **IV2** L² ≤ x ≤ U² (exact rational comparison).
- **IV3** If x is a rational square (`sqrt_rat` not None) and √x·2ᵏ is an integer, L = U = √x.
- **IV4** Non-widening across the schedule: for k < k′, L_k ≤ L_k′ and U_k′ ≤ U_k.
- **IV5** T enclosure contains the exact T for A4, A6 (T = −5/3) and TB1 (T = 1), with the correct orientation for N > 0 and N < 0, and [0, 0] for N = 0 (A2).
- **IV6** Strict disjointness: touching intervals (hi_a = lo_b) are reported as not disjoint.

**Precision-schedule tests** [COR]: **KS1** k_max = 200 → (64, 128, 200); **KS2** k_max = 10 → (10); **KS3** k_max = 64 → (64); **KS4** k_max = 100 → (64, 100); **KS5** k_max ∈ {0, −1, 2.5, "200"} → STOP-2.

Full hand derivations for T/U/A/M/TB/I vectors: recovery Part 4 §12.

---

## 15. Common-mode mitigation

[PROP] (X4, K-g) Tiny-n exact checks in V0: V0-7a (IND) and V0-7b/7c (XCHK — same-author cross-check — not an independent expected result); V0-7d non-mandatory, [BLOCKED], NOT PERFORMED (R-TINY). P2, B1, B7 and the B2 interior case-I fixtures are likewise same-author cross-checks. **Precondition for any full-grid authorization:** an SRC code-against-spec review of the core and region modules.

---

## 16. Prohibited claims

Never claim, including after V0–V5 pass:

1. [PROP] Level-α control over the composite null, or at any untested (n, δ, τ) (U-2).
2. [PROP] Worst-case or global power, or ≥ 80% power; a grid minimum is not a worst-case bound (U-4).
3. [PROP] That any n is n_conf, a required sample size, or an upper bound on the required n.
4. [PROP] That n_G is unconditional or implies a feasible n. n_G is only a conditional lower bound on the Option-B threshold (§6.4). **n_G > N_avail does not establish infeasibility**; infeasibility at N_avail requires §6.5, relative to I, conditional on U-3, and is not SM8 VOID.
5. [PROP] Certification beyond "decision-certified, conditional on U-3", or freedom from floating-point error (U-3).
6. [PROP] Lemma M beyond the exactly certified (n, δ, τ) (§7.5).
7. [PROP] That the code is proven correct, or that V0–V5 is independent certification; [COR] (L8) or that any XCHK check (V0-7b, V0-7c, B1, B7, B2 interior case-I fixtures, P2) is an independent expected result.
8. [PROP] That the formula has been verified against Tango (1998).
9. [PROP] That the SM9 sensitivity analysis is complete (positive-correlation scenarios absent).
10. [PROP] Statistical validity of any kind, or any engineering or manufacturing capability.
11. **[RD-NEW] (R-P11, adopted 2026-10-21)** Using V0–V5 output to select δ, g, Δ_true or n.
12. (Follows from RD decision R-PROJ, 2026-10-21) Any full-grid cost projection from V5; V5 timings are observations only.
13. (Follows from RD decision R-TINY, 2026-10-21) That exact-size validation has been performed or passed: V0-7d was not performed.

---

## 17. Labels

[PROP] Every artifact: `SOFTWARE-MECHANICS VALIDATION ONLY — NOT EVIDENCE OF STATISTICAL VALIDITY OR POWER` (X7) and `EXPLORATORY — NOT CONFIRMATORY EVIDENCE OF ≥80% WORST-CASE POWER; level-α over the composite null UNPROVEN (U-2); SM8 governs confirmatory sizing; incomplete SM9 grid (positive-correlation scenarios ABSENT).` (EPG-14 label 9). [RD-NEW] Every artifact also carries: `MUST NOT BE USED TO SELECT δ, g, Δ_true OR n (R-P11).` Each design point: `LEMMA-M: CERTIFIED | VIOLATED (certified witness) | UNCERTIFIED at (n,δ,τ)` plus the §7.5 scope text. Full-grid labels (blocked): EPG-8 §2.4 labels 1–5 and EPG-14 labels 1–5, 7, 8 (recovery Part 1); EPG-14 label 6 is superseded by §6.5.

---

## 18. K-a – K-g dispositions

[PROP] K-a ACCEPT (§6.5); K-b ACCEPT WITH CORRECTION (X3, §6.2); K-c ACCEPT (§6.4); K-d ACCEPT (§6.4); K-e REJECT, replaced by §4.2–§4.7; K-f ACCEPT WITH CORRECTION (X1, §7); K-g ACCEPT WITH CORRECTION (X4, §15).

---

## 19. Authorization template — PROPOSED, NOT RECORDED

> **RD AUTHORIZATION — EPG BOUNDED VALIDATION V0–V5 (SOFTWARE MECHANICS ONLY).** The Research Director accepts the EPG-14 consolidated contract [CONTRACT VERSION: ____; frozen SHA-256 (method per §13.1): ____], with R-P11 **adopted (2026-10-21)**; R-TINY **decided (2026-10-21): V0-7d non-mandatory, BLOCKED, not performed**; R-E1A1 **rejected (2026-10-21)**; R-PROJ **decided (2026-10-21): projection remains BLOCKED**; R-V5 [final status: ____].
>
> This record does not freeze SM1–SM11, δ, Δ_true, RD-6 or N_avail, and does not change the SM3/SM4 nuisance domain. U-2, U-3 and U-4 remain BLOCKED for confirmatory use.
>
> **Authorized:** offline implementation of `Velith-research/stats/egrid/` and execution of V0–V5 only.
> - Venue: [K2 VENUE: ____]
> - Environment lock: [env.lock SHA-256: ____]
> - Network: [NETWORK ISOLATION METHOD: ____]
> - CPU: per-stage hard caps of §11.1 (total 4 CPU-h), no borrowing, single process per stage, in-process monitor plus host backstop.
> - Single-threaded numerical libraries; at most 2 GiB per process; no network use.
>
> All thresholds and STOP-1 to STOP-9 are fixed as of this record. Validation-set powers are implementation-check artifacts only. V5 computes no power and no projection. BLOCKED items are reported as not performed and never count as PASS; exact-size validation (V0-7d) and P2 (c) power agreement are not part of this authorization. Same-author cross-checks are reported as such, never as independent validation. Every Lemma M result carries the §7.5 scope text; every artifact carries the §17 labels. V0–V5 output must not be used to select δ, g, Δ_true or n.
>
> **Prohibited until separately approved:** full-grid execution; any confirmatory sample-size, power, validity or efficacy claim; any full-grid cost projection; real-task experiments, A2 pilot, generator calls, admission tests; network access; repository-selection changes; any change to production Velith; automatic S8; raising any budget; staging, commit or push.
>
> **On any STOP:** halt and report unchanged.

Evidence available for the fields (§12.4): venue `wsl-docker`; `env.lock` SHA-256 `02153e09…d1ca`; network `docker --network none` (loopback only, ENETUNREACH). Contract SHA-256: not computed (this candidate is unfrozen).

---

## 20. Missing source details (identified, not invented)

| ID | Missing detail | Status in CAND-2 | Classification |
|---|---|---|---|
| MD-1 | Initial interval cover of Q(x) for R1′ | Implementation parameter, deterministic, recorded before V1 (§5.5, §13.3) | Safe deferment |
| MD-2 | Placement of the R2/R3 2,001-point grids and R3b 21 × 21 / 101 × 101 grids | Uniform exact-rational grids including endpoints, recorded in the manifest; R3b does not probe Δ < 0 | Safe deferment (diagnostics) |
| MD-3 | Soundness bound for float-only T comparisons outside the 10⁻⁹ band | Unproven assumption, stated in the report | Blocks scientific claims (U-3) |
| MD-4 | Tiny-n expected values | V0-7a oracle defined (IND); V0-7b/7c defined as XCHK; V0-7d non-mandatory, **BLOCKED**, NOT PERFORMED (R-TINY decided) | 7a–7c resolved for V0; 7d does not affect V0 PASS but exact-size validation is not completed |
| MD-5 | Internals of the P2 mpmath branch-and-bound | Internals deferred; comparison rule fixed (P2 (a)/(b)) | Safe deferment |
| MD-6 | DPID `<hash>` fields | Defined (§13.1, §13.2) | Resolved |
| MD-7 | Test runner | `unittest` | Safe editorial |
| MD-8 | STOP-8 reserve and periodic check interval | Implementation parameters, recorded (§11.1, §13.3) | Safe deferment |
| MD-9 | Full-grid cost projection method | **BLOCKED** (R-PROJ decided 2026-10-21); not computed | Blocks only the projection, not V5 PASS |
| MD-10 | V0-7d null-point set, region and acceptance criterion | **BLOCKED** (R-TINY decided 2026-10-21); V0-7d non-mandatory and not performed | Does not block V0 PASS; exact-size validation remains incomplete |
| MD-11 | Trigger path of the §4.3 "V ≤ 0 / discriminant ≤ 0 / q̃ ∉ [0, u]" STOP-9 row | Unreachable with valid inputs; only the positive invariant (A9) is tested (§10.3.1) | Safe deferment; recorded coverage limitation |
| MD-12 | Finite evaluation set and acceptance rule for P2 (c) power agreement | **BLOCKED** (L9 D2); P2 (c) non-mandatory and not performed | Does not block V2 PASS; power agreement is not established |

---

## 21. Unresolved decisions register

| ID | Decision | Owner | Status |
|---|---|---|---|
| R-ACC | Accept this contract body ([PROP] and [COR] items) | RD | **Accepted 2026-10-22** (L11): as a specification for bounded software-mechanics validation only; establishes no statistical validity, exact size, general Lemma M correctness or worst-case power. [RD-PROV], [PEND] and [BLOCKED] items keep their status |
| R-P11 | No selection of δ, g, Δ_true or n from V0–V5 output | RD | **Adopted 2026-10-21** [RD-NEW] |
| R-V5 | Six-region V5 scope {100, 300, 600} × {1/50, 1/10} | RD | **Provisional 2026-10-21** [RD-PROV], condition: consistency with the R1′ objective (CSE assessment only, §10.8) |
| R-TINY | V0-7d scope | RD | **Decided 2026-10-21**: V0-7d non-mandatory, [BLOCKED], NOT PERFORMED; exact-size validation not completed and not part of PASS |
| R-XCHK | Expected-result provenance of V0-7b, V0-7c, B1 | RD | **Decided 2026-10-21**: mandatory; labelled `same-author cross-check — not an independent expected result` |
| R-E1A1 | Optional exact additive pre-check | RD | **Rejected 2026-10-21**; not part of the contract; E1 unchanged |
| R-PROJ | Full-grid cost projection | RD | **Decided 2026-10-21**: projection remains BLOCKED; V5 reports observed timings only |
| R-P2 | P2 comparison domain and power test | RD | **Decided 2026-10-22** (L9): (b) both paths literal R1 on the P2 sets; (c) BLOCKED — NOT PERFORMED pending a specified finite evaluation set and acceptance rule |
| R-B2B3 | B2/B3 evidence classes | RD | **Decided 2026-10-22** (L9): B2 IND for §3.3 rule-determined fixtures, XCHK for interior case-I fixtures; B3 STRUCT |
| R-MD | Accept the §20 handling of MD-1, MD-2, MD-5, MD-7, MD-8, MD-11 | RD | Pending (class b); boundary preserved (L11): unresolved result-affecting implementation details remain blockers for the affected stage |
| R-AUTH | After freezing and hashing: record §19 with fields filled | RD | Pending |
| U-1 | Tango (1998) correspondence | SRC / owner | Open |
| U-2 | Lemma M at a confirmatory (n, δ, τ); independent review of X1 | SRC / reviewer | Blocked |
| U-3 | Rigorous floating-point bounds (includes MD-3) | CSE / reviewer | Blocked |
| U-4 | Certified global lower bound on power; SM8 minimisation method | SRC | Blocked |
| Other | SM1–SM11 RD freeze; δ, Δ_true, RD-6, N_avail; SM9(c) scenarios; X4 SRC code review before any full grid | RD / SRC | Open |

---

## 22. Version and change summary

**CAND-5 (2026-10-22)** — acceptance clarifications only (L10); R-ACC then recorded (L11). No accepted text altered; D1–D3 unchanged; the 400-point V0 design is unchanged.

| Change | Section | Basis |
|---|---|---|
| B3/B6 production scale stated as n = 600 × {1/50, 1/25, 3/50, 2/25, 1/10}, cited to the defining source (restricted-MLE correction memo §5–§6) | §9 B3, B6; §10.3 V0-3 | L10 A |
| B6 clarified as a necessary-condition property check with explicit claim boundary; IND only for the stated property | §9 B6; §10.3 V0-3 | L10 B |
| R-ACC recorded (version label unchanged; no body text altered): status, ledger L11, B3/B6 provenance, R-ACC and R-MD rows | Header, §0, §9, §21 | L11 |

**CAND-4 (2026-10-22)** — RD-directed bounded correction (L9) (superseded). No accepted text altered; E1 unchanged; no new numerical criterion.

| Change | Section | RD decision |
|---|---|---|
| P2 (b): both paths run literal R1 on the P2 validation sets; comparison defined for every Δ̂ > δ outcome; R1 failure on either path → STOP-4 | §9 P2, §10.5, §11.2 STOP-4 | D1 |
| P2 (c): removed from the mandatory gate; [BLOCKED] — NOT PERFORMED; not a pass; verbatim V2 report statement; MD-12 | §9 P2, §10.5, §11.2 STOP-4, §13.5, §19, §20, §21 | D2 |
| B2: IND only for §3.3 rule-determined fixtures, XCHK for interior case-I fixtures; B3: STRUCT; class lists updated | §0, §9 B2/B3, §10.3 V0-3 and reporting rule, §15, §16 item 7, §21 | D3 |

**CAND-3 (2026-10-21)** — RD-directed correction milestone (L8) (superseded). No accepted text altered; E1's literal production boundary k = 200 restored.

| Change | Section | RD decision |
|---|---|---|
| V0-7d non-mandatory, [BLOCKED], NOT PERFORMED; PASS defined by mandatory items; verbatim report statement | §10.2, §10.3, §11.2, §13.5, §20, §21 | R-TINY |
| Expected-result classes IND / XCHK / STRUCT; V0-7b, V0-7c, B1 (and B7, P2) labelled same-author cross-check | §0, §9, §10.3, §13.5, §15, §16 item 7, §21 | Expected-result provenance |
| Every §4.3 row mapped to vectors; A1-rev, A3-rev, A4-self added; STOP-9 invariant-row limitation recorded (MD-11) | §10.3.1, §14, §20 | Degeneracy coverage |
| Prohibited claim 13 (exact-size validation) | §16 | R-TINY |
| E1 additive boundary "k = 200" restored; test-only k_max limited to V0 tests | §4.5, §4.7 step 1 | E1 |
| Pre-check 3 recorded as REJECTED; conditional text removed; conservative limitation kept | §4.2, §4.5, §19, §21 | R-E1A1 |
| Projection BLOCKED by RD decision; prohibited claim 12 re-labelled; V5 timings observations only | §10.8, §16, §20, §21 | R-PROJ |
| Six-region rationale relabelled CSE assessment only | §10.8, §21 | R-V5 |
| P2 flag-set rule and like-for-like power comparison; STOP-4 extended (historical: power comparison made BLOCKED — NOT PERFORMED in CAND-4) | §9, §10.5, §11.2 | P2 |
| Single-process stage model; process spawn → STOP-2 | §11.1, §11.2, §19 | STOP-8 process model |
| Contract hash method (LF bytes, `sha256sum` in WSL on committed file); authorization-record hash format deferred; environment identity separated | §13.1, §19 | Contract identity |

**CAND-2 (2026-10-21)** — documentation corrections from the CAND-1 audit (superseded). No accepted text altered; one proposed amendment to accepted E1 is shown as [PEND] and is not effective.

| Change | Tag | Audit item |
|---|---|---|
| Test IDs listed explicitly (no U15); full V0 test manifest (V0-1 – V0-11) | [COR] | AUD-1 |
| Fail-closed V0 rules; stage outcome states PASS/FAIL/BLOCKED (BLOCKED never PASS) | [COR] | AUD-2 |
| P2 split into per-quantity agreement (same interval/point/region, ≤ ρ/100) and final certified agreement (≤ ε + 2ρ) | [COR] | AUD-3 |
| Tiny-n oracle defined for pmf, ordering, tail sets; exact-size part BLOCKED (R-TINY) | [COR]/[BLOCKED] | AUD-4 |
| Candidate vs frozen contract identity; DPID hash fields defined | [COR] | AUD-5 |
| Additive pre-check 3 proposed as pending amendment R-E1A1; E1 unchanged; limitation documented (historical: R-E1A1 rejected by RD 2026-10-21, removed in CAND-3) | [PEND] at CAND-2 | AUD-6 |
| Strict interval disjointness; k_max validation; same-k recomputation | [COR] | AUD-7, AUD-8 |
| Provenance split: §4.7 integer formulas [COR]; §3.4 E3 [ACC] vs Q2.5 [PROP]; V0-1 n-range [ACC] vs Q1 [PROP]; §11.1 values [PROP] vs wording [COR]; [D31] legend entry added (supported by `DECISIONS.md` L680, L722) | provenance | AUD-9 – AUD-12 |
| STOP-8: in-process monitor with recorded reserve plus host-side hard-kill backstop; no completeness guarantee after a kill | [COR] | AUD-13 |
| STOP-7 scope limited to R1′ classification/region construction; V0 Lemma M → UNCERTIFIED | [COR] | AUD-14 |
| Interval invariant tests IV1–IV6 and schedule tests KS1–KS5; B1 reference stated from recovered scratch method, tagged [PROP] | [COR]/[PROP] | AUD-15 |
| R-P11 adopted and applied in §1.5, §16, §17, §19, §21 | [RD-NEW] | AUD-16 |
| R-V5 provisional in §10.8, §19, §21; observed timings separated from projection; projection BLOCKED (R-PROJ) | [RD-PROV]/[BLOCKED] | AUD-17, AUD-18 |

**CAND-1 (2026-10-21)** — first consolidated candidate (superseded).
