# RD Freeze Decision Input — M9/M10 Stage-1 successor

**Document type:** research decision input. **It decides nothing and authorizes nothing: no implementation, no pilot.**
**Date:** 2026-09-28.
**Baseline:** Velith `5452efc` (D31 placed).
**Sources:**
- D31 (`DECISIONS.md` @ `57e228d6…`);
- the SRC final review (`reviews/src/SRC_2026-09-28_M9-ST1_final_statistical_review.txt`, `c1ced0a2…`).

---

## 1. SRC-accepted statistical machinery (ready for RD freeze into the successor specification)

**Frozen by D31 (governance):**
- Estimand A-iv: Δ20 = P(A2 pass @K) − P(A0 pass), paired over held-out tasks.
- Hypotheses: H0: Δ20 ≤ δ vs H1: Δ20 > δ, with δ > 0.
- One-sided α = 0.01.
- T = 0.0, N = 1, task-level uncertainty.
- Power ≥ 0.80, jointly designed with δ, n and K; inadequate power means VOID before execution.
- The pilot is design-only.
- GEE is secondary and non-gating.

**Accepted by the SRC (scientific), awaiting RD freeze:**

| # | Item | Exact content |
|---|---|---|
| SM1 | Certified supremum | Branch-and-bound with monotone-factor upper bounds U[a,b] = Σ_R n!/(x!y!z!)·(b+δ)^x·b^y·(1−2a−δ)^z. Stop when max U − L ≤ ε = 10⁻⁷. Local optimizers may only raise L. There is no grid or Brent certification. |
| SM2 | p-value | p = min(1, U_certified + η + γ), with η = 10⁻⁹ and γ = 0.001 |
| SM3 | Null domain | 0 < δ < 1. p01 ∈ [0, (1−δ)/2]. p10 = p01 + δ. p00 = 1 − 2p01 − δ. |
| SM4 | Berger–Boos set | Two-sided (1−γ) Clopper–Pearson interval [ψ_L, ψ_U] on ψ from D = n10 + n01, mapped to p01 ∈ [max(0, (ψ_L−δ)/2), (ψ_U−δ)/2] |
| SM5 | Shortcut | If Δ̂20 ≤ δ, p = 1 with no search (this covers D = 0) |
| SM6 | Reproducibility | (i) mathematical determinism; (ii) byte identity within the recorded pinned environment; (iii) cross-platform agreement of p within ε + η + 10⁻¹², and an identical GO/NO-GO whenever \|p − α\| > 10⁻⁶ |
| SM7 | Power | Exact trinomial sum over the certified rejection region. The primary planning assumption is conditional independence, ψ_plan = p0(1−p2) + p2(1−p0), with p2 = p0 + Δ_true. |
| SM8 | Planning p0 | The value inside the pilot's two-sided 95% Clopper–Pearson interval (γ_pilot = 0.05) that minimizes exact power |
| SM9 | Sensitivity grid (mandatory) | (a) independence; (b) Fréchet maximum discordance; (c) two positive-correlation scenarios |
| SM10 | Design chain | pilot → p0 CI → δ → Δ_true → planning discordance → exact power minimization → n_conf → compare with N_avail → VOID if n_conf > N_avail |
| SM11 | Configuration equivalence | The pilot uses the confirmatory A0 configuration |

**Not covered by the SRC final review.** These were listed as open scientific items in the D31 draft (§8) and need either SRC confirmation or an explicit RD designation of who decides them:
- **S-R1:** primary completeness and VOID scope limited to cells {A0, A2@K}, together with the secondary-failure isolation guards (the CSE A–F reconciliation, item F);
- **S-R2:** the minimum analysable n, i.e. the disposition when the realized n after admission and complete-case losses falls below the planned n_conf;
- **S-R3:** the SRC acceptability review of δ, once the RD has recorded it.

## 2. Remaining RD decisions

| ID | Decision | Notes |
|---|---|---|
| RD-1 | Pilot size | The ratified M2-PV-R record says "exactly 5 … unless a later approved research amendment changes this". Any other size needs that amendment. |
| RD-2 | Pilot scope | Must define "confirmatory A0 configuration" (see §3, D-2), task sampling and representativeness, and the scope of the exclusion registry |
| RD-3 | N_avail | The real-corpus M4 held-out partition size, net of pilot exclusions and expected admission and complete-case losses |
| RD-4 | δ | The minimum clinically important difference (MCID) on the absolute pass-rate scale, recorded with justification **after** the pilot (D31 decision 8) |
| RD-5 | Δ_true | The assumed true effect for power |
| RD-6 | Governing sensitivity scenario | The SRC *concurs* with independence. That concurrence is not the decision; the RD designates. |
| RD-7 | Designation of S-R1 and S-R2 | Refer them to the SRC, or rule that they are specification-level engineering guards |

## 3. Dependencies

- **D-1: order.** RD-1 and RD-2 come before the pilot. The pilot comes before RD-4 (D31 decision 8) and SM8. RD-4, RD-5 and RD-6 come before the n_conf computation. RD-3 is needed for the comparison.
- **D-2: RD-2 depends on BC-1.** The ratified sequencing runs pilot → production-verifier automation. The confirmatory *verifier* therefore cannot exist when the pilot runs. So "configuration equivalence" (SM11) can only be satisfied at the **proposer/agent level**:
  - model weights digest, not only the tag;
  - decoding T = 0 and seed derivation;
  - context and output limits (`num_ctx`/`num_predict`, pilot OD-3);
  - prompt construction and attempts.

  Verdict equivalence depends on D27 classifier rules and on M2-PV validation. RD-2 must state this scope explicitly.
- **D-3: RD-2 → SM8 validity.** p0 plans the confirmatory population only if the pilot tasks are representative of it. The current pilot design uses a fixed anchor task, repository exclusions and a lottery, which is not a random sample of the held-out population.
- **D-4: RD-3 ← the real corpus.** N_avail cannot be fixed before the real corpus and partition exist (M4 real-dataset adapter, D28 transport, D26 schema), because TaskSpec admission failures reduce it.
- **D-5: RD-4 is independent of power.** δ must be meaningful in its own right. It may not be lowered merely to pass the adequacy check.
- **D-6: freezing the specification needs none of RD-1 to RD-6.** δ, Δ_true, N_avail and the scenario are *pre-registration parameters*, not specification constants. The successor specification can be frozen with them unset (form and version still open, G-A8), once S-R1 and S-R2 are settled.

## 4. What cannot proceed until those decisions are frozen

| Step | Blocked by |
|---|---|
| Successor specification freeze | S-R1, S-R2 (RD-7); form and version (G-A8). **Not** blocked by RD-1 to RD-6. |
| Implementation handoff and code (SM1–SM11 machinery; successor M9/M10) | Successor specification freeze plus a separate implementation authorization (D31 decision 3; D31 C27) |
| Pilot harness and pilot execution | RD-1, RD-2; PB-1 harness authorization; OD-1 to OD-12 |
| n_conf computation | Pilot result, RD-4, RD-5, RD-6 |
| Adequacy check (VOID or continue) | n_conf plus RD-3 |
| Successor pre-registration sealing | All of RD-1 to RD-6, S-R3, and an adequacy pass |
| Confirmatory Stage-1 evaluation and M10 go/no-go | Sealed pre-registration; production verifier (BC-1, BC-2); real corpus |

## 5. Consequences of each unresolved or VOID condition

| Condition | Consequence |
|---|---|
| Pilot not authorized or not run | The chain has no p0 CI, so n_conf is undefined and the pre-registration cannot be sealed. M10 stays "in progress" with no verdict. Planning without a pilot would be a design change needing SRC review; it is not in the frozen chain. |
| δ unresolved | No hypothesis, so no power, no n_conf and no sealing |
| Δ_true unresolved | No power calculation, so no n_conf |
| Governing scenario unresolved | The adequacy gate is undefined, so there is no VOID/continue determination and no sealing |
| N_avail unresolved | No adequacy comparison, so no sealing |
| n_conf > N_avail | **Stage-1 design VOID before execution** (D31 decision 9; SRC SM10). It is **never NO-GO**; no confirmatory run occurs. The RD may enlarge the pilot, revise δ or Δ_true with a recorded justification (subject to D-5), or accept the VOID. |
| Realized n < n_conf after execution | **Not defined** by the SRC final review (S-R2). It must be settled before sealing. |
| Pilot configuration not equivalent (SM11) | p0 is invalid as a nuisance estimate. The planning is invalid, so the chain cannot proceed until the pilot is re-run or the difference is re-justified. |
| S-R1 or S-R2 unresolved | Successor specification freeze blocked |
