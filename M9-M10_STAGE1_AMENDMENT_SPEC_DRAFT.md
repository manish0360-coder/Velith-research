# M9/M10 Stage-1 Amendment — Specification Draft (R-1 resolution)

**Document type:** Research-only amendment specification **DRAFT**. **Not frozen. Not ratified. Not an implementation authorization.**
**Author:** Chief Systems Engineer. **Requested by:** Research Director.
**Date:** 2026-09-28.

**Inputs (content-addressed):**

| Input | SHA-256 |
|---|---|
| `M2-PV-P1-R_GOVERNANCE_ADJUDICATION.md` (Velith-research) | `9eaa07ebc365be1fc214aa1f5f1e4a61fad8be1597d6233f837da52ad29ce7d5` |
| Gemini SRC review of R-1 (uploaded text) | `1eaef4cf0d5c8e54be930b504f8a0f08792daafe7c1be30bc1bcbcf18681aef2` |
| Velith `docs/DECISIONS.md` @ `0d247d9` | `0b17d0322d6b9585de830237f3581c022f2ede6f9ceb7981c85e8d54671fd982` |
| Velith `docs/M9_SPEC.md` @ `0d247d9` (frozen `m9-spec-frozen-oed7-vm2`) | `94dbdb9e075c5025f40b4e70305b74324971ae35439e5ca7a7a0f28370d1434e` |
| Velith `docs/M8_IDENTITY_V2_SPEC.md` | `746be5770993b51ad22f71a217f3108aeeab910d73f288dcf811132df4f5285a` |
| Velith `src/velith/analysis/preregistration.py` | `57cdcaccb236d92b1406d2e29ec193b506692858ba34b2941b0907a606dd9741` |
| Velith `src/velith/analysis/executor.py` | `72ea5f67b006c1ba2e66b8d7c0a55c86bff1ac58a0fbd42f5bdaa43f134fc9e5` |
| Velith `src/velith/analysis/decision.py` | `5c159cbb0d50fed2e7c909e06e33983df1e30417abcdcc49795beaa1a70b02b7` |

**Engineering baseline:** Velith HEAD = origin/main = `0d247d982e48b30febe2fb53405e1c6d1ba29960`. The working tree is clean.

---

## 0. Status and scope

**What this draft does:**
- reconciles the R-1 adjudication, the Gemini SRC ruling, frozen M9 (VM2), the frozen M10 executor, M8 identity v2, D6/D7/D8 and D29/D30;
- enumerates every parameter the amendment needs;
- classifies each proposed change;
- lists what the RD and SRC must decide.

**What it does not do:**
- it chooses no open decision;
- it edits no frozen text;
- it authorizes neither the pilot nor the production verifier.

**Classification legend.** Every proposed change carries exactly one of:

| Class | Meaning |
|---|---|
| **FROZEN FACT** | True in a frozen or ratified artifact at `0d247d9`. Not changeable by this amendment. |
| **REQUIRED BY GEMINI** | Mandated by the SRC ruling (review §§1–14). |
| **DERIVED STATISTICAL CONSEQUENCE** | Follows necessarily from frozen facts plus Gemini requirements. No choice is involved. |
| **OPEN DECISION** | Requires an RD and/or SRC ruling. Not chosen here. |
| **PROPOSED VALUE** | A CSE recommendation for an open decision. It has no force until ratified. |

---

## 1. Frozen baseline relevant to the amendment

| # | Fact | Source | Class |
|---|---|---|---|
| B1 | D6 H1: A2 beats (a) "the same agent at episode 0" and (b) unfiltered controls "after N grounded episodes"; the pass-rate "increases monotonically in expectation with accumulated verified experience". | `DECISIONS.md:148` | FROZEN FACT |
| B2 | D7: decisive criterion A2 > A1. | `DECISIONS.md:170` | FROZEN FACT |
| B3 | D8.2 requires the pre-registration to freeze N, **seed count**, **minimum effect size**, **exact arm contrasts** and metrics, before the first real Stage-1 run. | `DECISIONS.md:186` | FROZEN FACT |
| B4 | D8.5 staging. Stage 1 = A0 vs A2, a cheap go/no-go. Stage 2 = add A1 and A3; the decisive run. A Stage-1 win is necessary-but-not-sufficient. | `DECISIONS.md:189` | FROZEN FACT |
| B5 | D8 Consequences: the harness runs all arms from the start; staging is a spend decision. | `DECISIONS.md:194` | FROZEN FACT |
| B6 | D12 and D15: Stage-2 details are specified only after M10's verdict. | `DECISIONS.md:260, :315` | FROZEN FACT |
| B7 | M9 GO rule: K = 1 → McNemar A1 > A0 and A2 > A1 (two-test Holm). K > 1 → four-test Holm (EMM + trend for A1 vs A0; EMM + interaction for A2 vs A1). α = 0.01 family-wise. | `M9_SPEC.md:261–280` | FROZEN FACT |
| B8 | OED-2: A0 is time-invariant, with exactly one observation per task at `checkpoint_id_c = 0`. A1 vs A0 uses an additive model; A2 vs A1 uses an interaction model. | `M9_SPEC.md:226–235` | FROZEN FACT |
| B9 | **EMM "Interpretation A" (RD ruling, implemented).** The EMM evaluates A0 at every checkpoint `x_k` on the fitted surface, `p̂(A0, k) = σ(β0 + β_c·x_k)`. So the reference arm is **extrapolated along the treatment arm's slope**, which is identified only by the treatment arm. | `emm.py:22–30, :199–205` | FROZEN FACT |
| B10 | K = 1 McNemar is exact and conditional, and tests only the null of equal marginals (margin 0). `mcnemar_test` is generic over any arm pair. It requires exactly one endpoint per task per arm. | `mcnemar.py:83–130` | FROZEN FACT |
| B11 | `one_sided_wald(estimate, se)` tests `estimate > 0`. It has no margin parameter. | `wald.py:74–106` | FROZEN FACT |
| B12 | `gee.Comparison` is a closed enum `{A1_VS_A0, A2_VS_A1}`, with `DESIGN_COLUMNS` fixed per member. | `gee.py:85–99, :112–115` | FROZEN FACT |
| B13 | `PreRegistration` fields: `spec_version`, `arms`, `manifest_hash`, `verification_manifest_hash`, `checkpoint_identities`, `base_model`, **`eval_seed: int`** (a single seed), `max_*`, `primary_endpoint`, `statistic_identifier`, `alpha`, `decision_rule`, `missing_data_rule`, `global_incomplete_disposition`, `empty_dataset_disposition`, `k1_family_size = 2`, `kgt1_family_size = 4`, `a0_time_invariant`, `a0_checkpoint_id_c`. `extra="forbid"`. | `preregistration.py:68–107` | FROZEN FACT |
| B14 | M8 evaluation identity v2 has ten keys, including `eval_seed`. **Sampling temperature is not an identity component.** | D29.2 (`DECISIONS.md:601–606`); `evaluation/provenance.py` | FROZEN FACT |
| B15 | **The proposer's sampling temperature defaults to `0.0`.** No `Settings` field exposes it. The per-task seed is `derive_task_seed(task_identity, eval_seed)`. | `agent/proposer.py:90`; `evaluation/attempt.py:122`; `core/config.py:149` | FROZEN FACT |
| B16 | D16.1: proposal-level determinism at temperature 0 is attempted but not guaranteed across runs or hardware. | `DECISIONS.md:329` | FROZEN FACT |
| B17 | The nine statistics modules are byte-pinned by a test to `1b0b7a0`. | `tests/unit/test_m9_statistics_unchanged.py` | FROZEN FACT |
| B18 | D29.3 and D29.5: the pre-registration carries `spec_version = "m9-spec-frozen-oed7-vm2"` and binds only to identity-v2 evaluations; mixed-version joins are rejected. D29.7: there is no dual code path. | `DECISIONS.md:608–621` | FROZEN FACT |
| B19 | D30.2: the M1–M9 generic machinery, "including … the analysis layer", is "frozen as historical research infrastructure… Its identities…, specifications and results stay exactly as they are." D30.3: new engineering code adds no new generic platform mechanism to Velith. | `DECISIONS.md:662–663` | FROZEN FACT |
| B20 | No real M8 evaluation, M9 pre-registration or M10 analysis artifact exists. | `PROJECT_STATE.md:128–130`; D29 | FROZEN FACT |

---

## 2. The Gemini ruling, as binding inputs

| ID | Requirement | Gemini § | Class |
|---|---|---|---|
| G-1 | The frozen rule `A1 > A0 ∧ A2 > A1` is non-equivalent to D6 and must not be the Stage-1 GO rule (false-NO-GO risk). | §1, §3 | REQUIRED BY GEMINI |
| G-2 | Stage-1 GO evaluates **A2 > A0** only; the A2 > A1 contrast is not pulled into Stage 1. | §4, §9 | REQUIRED BY GEMINI |
| G-3 | A2 vs A0 is a **directly computed** estimand and contrast (not inferred by transitivity), for K = 1 and K > 1. | §3, §5, §13.1 | REQUIRED BY GEMINI |
| G-4 | Minimum effect size δ is on the **response scale** (absolute pass-rate difference), with an explicit scalar, frozen before execution. | §7, §13.2 | REQUIRED BY GEMINI |
| G-5 | δ is a **strict gate**: a superiority margin tested against the shifted null `H0: P(A2) − P(A0) ≤ δ`. | §7 | REQUIRED BY GEMINI |
| G-6 | Multiple evaluation seeds, with the integer frozen. N > 1 is required; N ≥ 3 is recommended. | §8, §13.3 | REQUIRED BY GEMINI |
| G-7 | The multiplicity method across the Stage-1 and Stage-2 families is explicitly specified. | §5, §13.4 | REQUIRED BY GEMINI |
| G-8 | Data collection follows an Option-C derivative (A0, A1 and A2 collected concurrently), with GO analytically separated. Option A applies if compute is strictly constrained. | §6, §9 | REQUIRED BY GEMINI (C preferred; A is a conditional fallback) |
| G-9 | Governance: Option 2, a new M9 `spec_version` plus M10 code amendment. D6, D7 and D8 literal text are unchanged. | §10, §11, §14 | REQUIRED BY GEMINI |
| G-10 | Nothing is implemented yet. | RD instruction | REQUIRED BY GEMINI / RD |

---

## 3. CSE critical review of the ruling — points the ruling does not settle

The ruling is scientifically sound on its central point (G-1, G-2). Eight technical gaps remain. Each blocks an exact freeze, so each is routed to an OPEN decision below.

| ID | Issue | Why it matters | Class | Needs |
|---|---|---|---|---|
| **X1** | **Seeds at temperature 0 are nearly degenerate.** G-6 assumes "temperature-induced" variance (Gemini §8). The frozen proposer samples at `T = 0.0` (B15), where the seed has, in principle, no effect on greedy decoding. N eval-seed replicates would then be near-identical pseudo-replicates that add no information. The only residual variance is hardware nondeterminism (B16). | N ≥ 3 is meaningful only if (a) `T > 0` or (b) seeds index something else, such as independent accumulation replicates. | OPEN DECISION (F) | **SRC re-review** |
| **X2** | **Temperature is outside identity v2** (B14). If X1 is resolved with `T > 0`, two evaluations differing only in temperature would share an evaluation identity. | This is the same class of defect as CX-A1, which D29 resolved for TaskSpecs. | OPEN DECISION (Q) | RD |
| **X3** | **Exact McNemar cannot test a shifted null.** B10 tests margin 0 only; G-5 requires `H0: Δ ≤ δ`, `δ > 0`. | K = 1 needs a different test (candidates in §4-B). | DERIVED STATISTICAL CONSEQUENCE → method choice OPEN (B) | SRC |
| **X4** | **The "A2 vs A0 interaction contrast" (Gemini §5) is not estimable under OED-2.** A0 has one design point (`x = 0`), so no arm × checkpoint interaction is identified. | The K > 1 A2 vs A0 model is necessarily additive, mirroring A1 vs A0. | DERIVED STATISTICAL CONSEQUENCE | — |
| **X5** | **Reusing Interpretation A (B9) for A2 vs A0 would extrapolate A0 along A2's learning slope.** The EMM would then compare A2 with a counterfactual A0 that "learns", not with the time-invariant baseline D6 names ("the same agent at episode 0"). Under a δ gate this changes the go/no-go boundary. | The estimand must be chosen explicitly (options in §4-A). | OPEN DECISION (A) | **SRC** |
| **X6** | **Stage-2 timing conflicts with D12/D15.** Gemini §9 has Stage 2 "immediately authorized… using Holm-corrected" levels, but D12 and D15 (B6) specify Stage-2 details only after M10's verdict. Also, if the A2 > A1 analysis is specified *after* Stage-1 results on the *same* data, it is not sealed from A2's results (M9 §3.4 principle). | Pre-registering A2 > A1 now needs a D15 reading or ruling. Specifying it later needs fresh data or explicit exploratory status. | OPEN DECISION (H, I, J) | RD |
| **X7** | **Option 2 reopens the analysis layer frozen by D30.2** (B19). Gemini §11 lists D30 as unchanged but does not address D30.2. Amending eight byte-pinned modules (B17) needs explicit Director authority, separate from the SRC scientific ruling. | This is a governance precondition. | OPEN DECISION (N, O) | RD / Director |
| **X8** | **A δ-shifted gate at α = 0.01 is sample-hungry** (see the §4-D table). "Cheap" Stage 1 (B4) and "strict δ gate" (G-5) pull against each other. δ, the held-out size n, K and N must be set jointly, using the pilot's base rate. | The pilot's base-rate output becomes an **input** to δ and n (DERIVED); it does not become an M10 prerequisite by decision. | OPEN DECISION (D) | RD + SRC |

---

## 4. Parameter specification (A–S)

Each parameter gives: the frozen fact, the Gemini requirement, derived consequences, the open decision and options, and any proposed value. Options are listed so the RD and SRC can choose; none is chosen here.

### A. Exact A2-vs-A0 estimand

- **REQUIRED BY GEMINI (G-3, G-4).** A directly computed response-scale difference `Δ20 = P(A2 pass) − P(A0 pass)`.
- **DERIVED STATISTICAL CONSEQUENCE.** At K = 1: `Δ20 = p_A2 − p_A0` at the single pre-registered checkpoint, over the complete-case task set, with each task weighted equally.
- **OPEN DECISION A (K > 1).** Which `Δ20`?

  | Option | Estimand |
  |---|---|
  | A-i | Interpretation A: `(1/K) Σ_k [σ(η_A2(x_k)) − σ(η_A0(x_k))]`. A0 is extrapolated along the fitted slope (X5). |
  | A-ii | Time-invariant A0: `(1/K) Σ_k σ(η_A2(x_k)) − σ(η_A0(0))`. |
  | A-iii | D6-literal final state ("after N grounded episodes"): `σ(η_A2(x_K)) − σ(η_A0(0))`. |
  | A-iv | Model-free final-checkpoint paired contrast, identical in form to K = 1 at `k = K`. GEE is used only for the trend. |

- **PROPOSED VALUE.** A-iii or A-iv, because D6 H1(a) is stated "after N grounded episodes" and against the episode-0 agent. A-iv also unifies K = 1 and K > 1 under one test. **Needs SRC.**

### B. Exact test for K = 1

- **FROZEN FACT (B10).** Exact McNemar tests margin 0 only.
- **DERIVED STATISTICAL CONSEQUENCE (X3).** Under G-5, McNemar cannot be the gate test.
- **OPEN DECISION B.**

  | Option | Test |
  |---|---|
  | B-i | Tango (1998) score test for a paired difference against margin δ. Equivalently: the lower bound of the one-sided (1 − α) Tango score interval exceeds δ. |
  | B-ii | Exact unconditional test for a paired difference with margin δ (for example Berger–Boos, maximizing the nuisance discordance). |
  | B-iii | Asymptotic Wald on the paired difference, `Z = (d̂ − δ)/SE(d̂)`, with `SE² = (ψ̂ − d̂²)/n`, where `ψ̂` is the discordant proportion. |
  | B-iv | "Both" form: McNemar at margin 0 must reject **and** the point estimate `d̂ ≥ δ`. This deviates from G-5's shifted null and needs an explicit SRC waiver. |

- **PROPOSED VALUE.** B-i or B-ii. Exact or score methods behave better than Wald at the small n and boundary rates expected on SWE-bench-scale held-out sets. **Needs SRC.**
- **If N > 1 (see F):** the paired unit becomes a task with N replicate pairs. B-i to B-iii then need a cluster-adjusted variance (for example the Obuchowski clustered paired-proportion variance), or tasks are aggregated first. This is chosen under F.

### C. Exact K > 1 GEE/EMM contrast

- **DERIVED STATISTICAL CONSEQUENCE (X4, B8).** The A2 vs A0 model is additive: `verdict ~ checkpoint_id_c + arm`, coded A0 = 0 and A2 = 1. A0 enters with one observation per task (per seed, if F adds seeds) at `x = 0`. There is no interaction term.
- **DERIVED STATISTICAL CONSEQUENCE.** The δ-shifted one-sided Wald is `Z = (Δ̂20 − δ)/SE(Δ̂20)`, `p = 1 − Φ(Z)`, using the delta-method SE for the estimand chosen in A. It can be computed by passing `Δ̂20 − δ` to the frozen `one_sided_wald` (B11) without changing `wald.py`. SE = 0 then follows the frozen disposition: `estimate − δ > 0` gives p = 0; otherwise p = 1.
- **DERIVED STATISTICAL CONSEQUENCE.** The existing correlation structure, covariance and link are retained: Binomial, logit, exchangeable, robust sandwich, grouped by task. The model-failure disposition (§3.5.7) extends: a failed A2 vs A0 model gives p = 1.0 and NO-GO.
- **OPEN DECISION C.** Whether K > 1 uses GEE at all for the gate (A-i to A-iii), or only for the trend (A-iv).

### D. Minimum effect size δ

- **REQUIRED BY GEMINI (G-4, G-5).** An exact scalar, response scale, absolute pass-rate points, frozen before execution.
- **OPEN DECISION D1: the scalar value.** Not chosen here. The frozen record gives no value, and choosing one without the base rate would be inventing it.
- **OPEN DECISION D2: the rationale.** Two candidate framings:
  - (a) the smallest lift that justifies Stage-2 spend (Gemini's "worthy of Stage-2 compute");
  - (b) the smallest lift detectable at the chosen n with target power.
- **DERIVED STATISTICAL CONSEQUENCE: response-scale definition.** `δ` is in the same units as `Δ20` (probability difference, `0 < δ < 1`), applied to the estimand fixed in A.
- **DERIVED STATISTICAL CONSEQUENCE: sample-size pressure (X8).** Illustrative only. Assumptions: K = 1, N = 1, paired normal approximation, one-sided α = 0.01, power 0.80, `n ≈ 10.04·ψ / g²`, where `g = Δtrue − δ` and ψ is the discordant proportion. These are assumptions, not values.

  | ψ | g = 0.05 | g = 0.10 | g = 0.15 |
  |---|---|---|---|
  | 0.20 | ≈ 803 tasks | ≈ 201 | ≈ 89 |
  | 0.30 | ≈ 1205 | ≈ 301 | ≈ 134 |

  SWE-bench Verified has 500 tasks in total, and only its held-out partition is usable. **Consequence: δ, n, K and N must be chosen together, or the gate is under-powered by construction.**
- **PROPOSED VALUE: the procedure, not a number.**
  1. Obtain the pilot's zero-experience base rate `p̂0` (the M2-PV-P1 output).
  2. Fix the held-out size n from the M4 partition.
  3. The SRC sets δ and verifies power ≥ 0.80 at a pre-declared plausible `Δtrue`.
  4. Freeze all four together.

### E. Seed count N

- **REQUIRED BY GEMINI (G-6).** An integer N > 1. Gemini recommends N ≥ 3.
- **OPEN DECISION E.** The exact integer. It is **conditional on F**: under temperature 0 with eval-only seeds, any N is near-degenerate (X1).
- **PROPOSED VALUE.** Decide F first. Then N = 3 if the replicate mechanism is non-degenerate, as Gemini's minimum recommendation.

### F. How seeds enter the observation and statistical model

- **FROZEN FACT (B13–B16).** There is one `eval_seed` per pre-registration, and per-task seeds are derived from it. Temperature is 0.0. The seed is an identity component of each evaluation.
- **OPEN DECISION F1: what a seed indexes.**

  | Option | Seed indexes | Consequence |
  |---|---|---|
  | F1-a | Evaluation-sampling seeds with a pre-registered `T > 0` | Requires X2 to be resolved (temperature bound into identity or pinned as a frozen constant). |
  | F1-b | Independent accumulation replicates, each with its own M5 sweep and checkpoint schedule | Requires a non-degenerate replicate source at T = 0, for example a seeded task-order permutation, which is a frozen-M5 change. It also turns `checkpoint_identities` into per-replicate schedules. |
  | F1-c | An SRC waiver of G-6 on the ground of X1: N = 1 at T = 0, with task-level uncertainty only | — |

- **OPEN DECISION F2: model entry.**

  | Option | Model entry |
  |---|---|
  | F2-a | One row per (task, seed, checkpoint, arm), clustered by task in GEE (exchangeable). |
  | F2-b | Per-task aggregation across seeds before testing. |
  | F2-c | Per-seed analyses combined by a pre-declared rule. |

- **DERIVED STATISTICAL CONSEQUENCE.** Any N > 1 breaks OED-2's literal "exactly one A0 observation per task". This becomes one per task **per seed**, which is an explicit amendment of the OED-2 wording. It also breaks McNemar's one-pair-per-task precondition (B10).
- **PROPOSED VALUE.** F1-a with F2-a, if the SRC confirms sampling variance is the target. Otherwise F1-b. **Needs SRC re-review (X1).**

### G. Stage-1 hypothesis and gate

- **REQUIRED BY GEMINI (G-2, G-5).** `H0_S1: Δ20 ≤ δ` versus `H1_S1: Δ20 > δ`.
  - GO_S1 iff `H0_S1` is rejected at the Stage-1 level.
  - NO-GO otherwise.
  - VOID per L.
- **OPEN DECISION G1: the Stage-1 level.** Either retain α = 0.01 (frozen M9 value, B7) or declare another value. **PROPOSED VALUE:** retain 0.01.
- **OPEN DECISION G2: the Stage-1 trend.** Should Stage 1 also require the A2-vs-A0 checkpoint trend (`β_checkpoint > 0`) for K > 1? D6 H1 includes monotonicity (B1); Gemini gates "exclusively" on A2 > A0 + δ. **PROPOSED VALUE:** report the trend as secondary, not as a gate, consistent with G-2 and the "cheap screen" intent.
- **DERIVED STATISTICAL CONSEQUENCE.** GO_S1 is necessary-but-not-sufficient (B4) and must never be reported as confirmation. The M10 report carries this text verbatim.

### H. Stage-2 hypothesis and gate

- **FROZEN FACT (B2, B4, B6).** The decisive criterion is A2 > A1. Stage 2 adds A1 **and A3**. Stage-2 details come only after M10's verdict. A3 does not exist in the harness (the M7 set is closed).
- **OPEN DECISION H1: timing** (X6).

  | Option | Timing |
  |---|---|
  | H1-a | Pre-register the Stage-2 A2 > A1 test now, in this amendment, reading D15's "details" as A3, ablation and replication only. |
  | H1-b | Specify Stage 2 after the M10 verdict, per D15's literal text, on fresh held-out data. |
  | H1-c | Specify Stage 2 after the verdict, on the concurrently collected A1 data, labelled exploratory rather than confirmatory. |

- **OPEN DECISION H2: margin.** Whether A2 > A1 also carries a margin δ₂.
- **PROPOSED VALUE.** H1-a, **only if** the Director rules it compatible with D15. It is the only option that keeps the decisive test sealed from all results while reusing concurrently collected data. Otherwise H1-b.

### I. Multiplicity across stages

- **REQUIRED BY GEMINI (G-7).** The method is explicit.
- **DERIVED STATISTICAL CONSEQUENCE.**
  - If Stage 1 is a single test, it needs no within-stage correction.
  - If G2 adds the trend, the Stage-1 family has two members, and frozen Holm (`holm.py`, generic) applies unchanged.
- **OPEN DECISION I.**

  | Option | Method |
  |---|---|
  | I-a | Fixed-sequence (serial gatekeeping): H_S1 at α; H_S2 at α only if H_S1 is rejected. This gives strong FWER control at α on shared data and matches the staging logic. Requires H1-a. |
  | I-b | Holm over {H_S1, H_S2} simultaneously (Gemini §9 phrasing). This makes Stage 2 part of the M10 decision and is in tension with G-2 and D15. |
  | I-c | Independent families on independent data (H1-b). No cross-stage correction is needed. |

- **PROPOSED VALUE.** I-a with H1-a, or I-c with H1-b. I-b is not proposed.

### J. Option-C data collection versus the staged analytical decision

- **REQUIRED BY GEMINI (G-8).** Collect A0, A1 and A2 concurrently; GO_S1 reads only A0 and A2.
- **DERIVED STATISTICAL CONSEQUENCE.** Under J, the Stage-1 executor must **not read** A1 records:
  - A1 outcomes stay unexamined until the Stage-2 analysis is pre-registered;
  - otherwise H1-b and H1-c lose their seal.
  - This is enforceable as a binder rule: the Stage-1 expected identity set excludes A1.
- **OPEN DECISION J1.** C-derivative (Gemini's preference, B5-consistent) or Option A (D8.5 literal, cheapest; A1 not collected in Stage 1).
- **OPEN DECISION J2.** Whether the M10 Stage-1 report may disclose A1 descriptives. **PROPOSED VALUE:** no, if H1-b or H1-c is chosen; yes only under H1-a (already sealed by pre-registration).

### K. Missing-data rules

- **FROZEN FACT (B7).** Per-task complete-case over all K × 3 cells.
- **DERIVED STATISTICAL CONSEQUENCE.** Stage-1 complete-case must be defined over the cells Stage 1 reads.
- **OPEN DECISION K1: scope.** Either complete over **A0 and A2 only**, or over all collected arms (so a task missing A1 is also excluded from Stage 1). **PROPOSED VALUE:** A0 and A2 only. Including A1 would make Stage-1 inference depend on the A1 arm, which G-2 excludes.
- **OPEN DECISION K2: seeds.** Whether a task missing any seed replicate is excluded entirely, or per-seed exclusion applies. This is conditional on F.

### L. VOID rules

- **FROZEN FACT.** The frozen VOID dispositions:
  - global-incomplete M8 run gives VOID (§3.5.1);
  - `n = 0` after complete-case gives VOID (OED-7);
  - an empty held-out population is rejected at VerificationManifest construction (D29.1).
- **DERIVED STATISTICAL CONSEQUENCE.** All three are retained unchanged. VOID is never NO-GO.
- **OPEN DECISION L1.** Is "global-incomplete" judged over the Stage-1 arms only, or over all collected arms? It must match K1.
- **OPEN DECISION L2.** Is a minimum analysable n (below which the δ gate is VOID for insufficient information rather than NO-GO) pre-registered? **PROPOSED VALUE:** yes, set from the D power calculation. Otherwise an under-powered NO-GO is indistinguishable from a true NO-GO, which D8.6 forbids ("an underpowered… positive is treated as uninterpretable").

### M. Identity and content-addressing consequences

- **DERIVED STATISTICAL CONSEQUENCE.** Any change to the plan fields yields a new `PreRegistration.identity` (canonical hash, B13). No existing artifact is rehashed (B20).
- **DERIVED STATISTICAL CONSEQUENCE.** Multiple seeds mean N evaluations per (arm, checkpoint), each with its own identity-v2 identity (`eval_seed` is already a component). The M10 expected-identity reconstruction (binder and executor) expands per seed.
- **DERIVED STATISTICAL CONSEQUENCE.** `AnalysisResultRecord.eval_seed: int` (`result_record.py:101`) must become a seed set. The result-record identity changes.
- **OPEN DECISION M1 (tied to X2).** If `T > 0` is adopted, temperature must either:
  - (a) enter the M8 evaluation identity (M8 identity **v3**, a D29 successor decision); or
  - (b) be pinned as a frozen, pre-registered constant with a runner check.

### N. M9 specification versioning and supersession

- **FROZEN FACT (B18, B19).** Versioned supersession is the precedent (D29/VM2). D30.2 keeps prior specifications "exactly as they are".
- **OPEN DECISION N1: form.**
  - (a) an "Amendment ST1" block appended to `M9_SPEC.md` and re-frozen (the VM2 precedent);
  - (b) a separate successor file, for example `docs/M9_STAGE1_SPEC.md` (the M8-IDv2 precedent), with `M9_SPEC.md` untouched.
  - **PROPOSED VALUE:** (b). D30.2, adopted after VM2, favors leaving frozen specification text byte-identical.
- **OPEN DECISION N2.** The new `spec_version` string. **PROPOSED VALUE:** `m9-spec-frozen-oed7-vm2-st1` (lineage-preserving) and tag `m9-spec-frozen-st1`.
- **OPEN DECISION N3: governing record.** Is a new dated `DECISIONS.md` entry required to authorize reopening the D30.2-frozen analysis layer (X7)?
  - **PROPOSED VALUE:** yes, a single entry (D31) that:
    - records the SRC ruling;
    - authorizes the versioned M9/M10 amendment;
    - scopes D30.2 as "historical *versions* remain reproducible";
    - supersedes **nothing** in D6, D7 or D8 (G-9).
  - Mixed-version rules (D29.5 analog): an ST1 pre-registration binds only to identity-v2 evaluations produced under the ST1 seed/temperature rules. VM2 pre-registrations are rejected by ST1 code.

### O. Required M10 implementation changes

- **DERIVED STATISTICAL CONSEQUENCE.**
  - The executor's `SPEC_VERSION` equality check (`executor.py:196–200`) and `ARMS` check (`:201`) change.
  - The Stage-1 branches replace `_k1_holm` (`:246–253`) and the four-model K > 1 path.
  - The executor's reconstruction handles seeds.
- **OPEN DECISION O1.** Replace in place (single path, the D29.7 precedent) or add parallel ST1 modules that leave the nine byte-pinned modules untouched (the D30.2-favoring precedent).
  - **Constraint:** `gee.Comparison` is a closed enum, so an A2 vs A0 GEE needs an edit to `gee.py`, `emm.py` and `trend.py` (or parallel copies, which D30.3 disfavours as duplicate logic).
  - **PROPOSED VALUE:** in-place, versioned, single path (D29.7), under the explicit authority of N3. The byte-pin test is re-pinned to the new baseline by the same authorization.

### P. Exact frozen code and modules affected

See §8 (implementation impact map).

### Q. Compatibility with M8 identity v2

- **DERIVED STATISTICAL CONSEQUENCE.** Compatible without change **iff** seeds are eval seeds and temperature is fixed:
  - `eval_seed` is already an identity component;
  - `verification_manifest_hash`, `checkpoint_identity`, `arm`, `base_model` and `max_*` are unchanged.
- **OPEN DECISION Q1.** Under F1-a (`T > 0`), M8 identity v2 is **insufficient** (X2). Resolution M1-a (v3) or M1-b (pinned constant) is required.
- **OPEN DECISION Q2.** Under F1-b, checkpoint identities differ per replicate. v2 is compatible, but the pre-registration's schedule structure changes.

### R. Pre-registration fields needing amendment

| Field (B13) | Change | Class |
|---|---|---|
| `spec_version` | New value (N2) | DERIVED → value OPEN (N2) |
| `arms` | Stays (A0, A1, A2) under J1 = C with a new role map (Stage-1 arms A0, A2), or becomes (A0, A2) under J1 = A | OPEN (J1) |
| `eval_seed: int` | Becomes `eval_seeds: tuple[int, ...]` (length N), or per-replicate structure under F1-b | DERIVED (G-6) → shape OPEN (F) |
| `checkpoint_identities` | Unchanged (F1-a), or per-replicate (F1-b) | OPEN (F) |
| `statistic_identifier` | New closed-set member | DERIVED |
| `decision_rule` | New constant (for example `stage1_margin_reject_go_else_nogo`) | DERIVED → wording OPEN |
| `k1_family_size`, `kgt1_family_size` | 1 (or 2 if G2 adds the trend) | OPEN (G2) |
| `a0_time_invariant`, `a0_checkpoint_id_c` | Retained; the semantics become "per seed" if N > 1 | DERIVED |
| `alpha` | Retained, or a per-stage value | OPEN (G1) |
| **new** `min_effect_size` (δ) and `effect_scale = "response_absolute"` | Added | REQUIRED BY GEMINI → value OPEN (D1) |
| **new** `stage1_estimand` identifier | Added | REQUIRED BY GEMINI → content OPEN (A) |
| **new** `stage1_test` identifier (K = 1) | Added | OPEN (B) |
| **new** `sampling_temperature` | Added iff F1-a with M1-b | OPEN (M1) |
| **new** `stage2_plan` / `multiplicity_procedure` | Added iff H1-a / I-a | OPEN (H1, I) |
| **new** `minimum_analysable_n` | Added iff L2 = yes | OPEN (L2) |
| `missing_data_rule`, `global_incomplete_disposition` | New scoped constants | OPEN (K1, L1) |
| `empty_dataset_disposition` | Unchanged (VOID) | FROZEN FACT |

### S. δ as gate, reporting threshold, or both

- **REQUIRED BY GEMINI (G-5).** δ is a **gate**, via the shifted null.
- **DERIVED STATISTICAL CONSEQUENCE (D8.6, B3).** The effect estimate `Δ̂20` with its (1 − 2α) two-sided or (1 − α) one-sided confidence bound is **always reported**, whatever the gate outcome. So δ is both a gate and a reporting reference; the gate is binding.
- **OPEN DECISION S1.** Only if the SRC waives G-5 in favour of B-iv (the "both" form). Not proposed.

---

## 5. Contradiction audit

| # | Records | Finding | Resolved by this draft? |
|---|---|---|---|
| CA-1 | D8.5 (Stage 1 = A0 vs A2) vs frozen M9 and M10 (GO = A1 > A0 ∧ A2 > A1) | Confirmed contradiction (R-1). | **Yes, by design (G-1, G-2)**, once ratified. |
| CA-2 | D6 H1 ("after N episodes", against the episode-0 agent) vs M9's uniform 1/K EMM with Interpretation A | Estimand mismatch (X5). | **No — OPEN A.** |
| CA-3 | D6 H1 monotonicity vs a Stage-1 gate on A2 > A0 only | Monotonicity is untested as a gate in Stage 1. | **No — OPEN G2** (proposed: secondary). |
| CA-4 | D8.2 (seed count; minimum effect size) vs M9 (one seed; no δ) | Missing parameters. | **Partially.** Fields are defined; values are OPEN (D1, E). |
| CA-5 | D8.2 seed count / Gemini N ≥ 3 vs frozen `T = 0.0` (B15) | Seeds are nearly degenerate at T = 0 (X1). | **No — OPEN F. SRC re-review needed.** |
| CA-6 | Frozen exact McNemar (margin 0) vs Gemini G-5 (shifted null) | Test incompatible (X3). | **No — OPEN B.** |
| CA-7 | Gemini "A2 vs A0 interaction" vs OED-2 A0 single design point | Not estimable (X4). | **Yes** — derived additive model (§4-C). |
| CA-8 | Gemini §9 (Stage 2 immediately) vs D12/D15 (Stage 2 specified after M10) | Timing conflict and seal risk (X6). | **No — OPEN H1, I, J2** (Director). |
| CA-9 | D8.5 Stage 2 "add A1, A3" vs the harness (no A3; M7 closed set) | Stage 2 as D8.5 defines it is not executable on the current harness. | **Out of scope** (D15). Recorded. |
| CA-10 | D29.3 (`spec_version = …-vm2`) vs a new ST1 version | D29 fixes VM2 as the identity-v2 lineage. A new M9 version must restate the v2 binding. | **Yes** — N2 plus mixed-version rules (§4-N). |
| CA-11 | D29 identity v2 (no temperature) vs F1-a (T > 0) | Identity gap (X2). | **No — OPEN M1 / Q1.** |
| CA-12 | D30.2 (analysis layer frozen as historical) vs Option 2 (amend analysis code) | Governance precondition (X7). | **No — OPEN N3** (proposed D31). |
| CA-13 | D30.3 (no new generic platform mechanism in Velith) vs new statistical tests (for example the Tango score test) | Noetica has no statistics mechanism (its `evaluation/` measures only). Adding generic tests to Velith is in tension with D30.3. | **No — OPEN**, folded into N3. Proposed reading: completion of the D12 M10 historical experiment, not new platform capability. |
| CA-14 | M9 VM2 "Explicitly not changed: the arms" vs this amendment | Not a contradiction: VM2 constrains VM2 only. ST1 is a successor version. | **Yes.** |
| CA-15 | D12 M9 "full A0/A2 run" (undelivered) vs `m9-complete` | Carried over from the adjudication (F-R1.4). | **No — the D31 text must assign it** (N3). |
| CA-16 | M8 identity v2 vs multi-seed eval | Compatible (per-seed evaluation identities). | **Yes** (§4-Q), conditional on F. |
| CA-17 | Gemini G-5 (strict δ gate) vs D8.5 "cheap" Stage 1 | Sample-size tension (X8). | **No — OPEN D** (joint δ/n/K/N freeze). |

---

## 6. Exact unresolved decisions requiring RD/SRC approval

**SRC (scientific), where Gemini review is required:**

1. **A** — the K > 1 A2-vs-A0 estimand: A-i, A-ii, A-iii or A-iv (X5).
2. **B** — the K = 1 shifted-null test: B-i, B-ii or B-iii. B-iv would need a waiver of G-5.
3. **F1 / E** — seed semantics under T = 0 (X1): F1-a, F1-b or F1-c; then the integer N.
4. **F2** — how seeds enter the model: F2-a, F2-b or F2-c.
5. **D1 / D2** — the δ scalar and its rationale, jointly with n, K and N and power, after the pilot base rate.
6. **G2** — whether the Stage-1 trend is a gate or secondary.
7. **L2** — a minimum analysable n (VOID for insufficient information).

**RD / Director (governance):**

8. **N3** — whether a D31 entry authorizes reopening the D30.2-frozen analysis layer, and its scope (including CA-13 and CA-15).
9. **H1 / I / J2** — Stage-2 timing under D15: H1-a, H1-b or H1-c; the cross-stage multiplicity; A1 disclosure.
10. **J1** — Option-C derivative or Option A collection.
11. **M1 / Q1** — if T > 0: M8 identity v3, or a pinned temperature constant.
12. **N1 / N2** — the amendment form (appended block or successor file) and the `spec_version` string.
13. **O1** — in-place single-path modification, or parallel modules.
14. **G1** — the Stage-1 α.
15. **K1 / K2 / L1** — the complete-case and global-incomplete scope (Stage-1 arms only, or all collected arms; the seed-level rule).

---

## 7. Proposed amendment structure

1. **`DECISIONS.md` D31** (Director; drafted separately):
   - records the SRC R-1 ruling;
   - authorizes a versioned M9/M10 successor;
   - scopes D30.2 (historical versions remain reproducible);
   - assigns D12's "full run";
   - states Stage-2 timing under D15;
   - supersedes **nothing** in D6, D7 or D8.
2. **Successor specification** `docs/M9_STAGE1_SPEC.md` (spec_version per N2). Sections:
   1. purpose and authority;
   2. design (arms and roles, seeds, temperature, checkpoints);
   3. Stage-1 estimand (A);
   4. K = 1 test (B);
   5. K > 1 model and test (C);
   6. δ, n, power and the minimum analysable n (D, L2);
   7. seeds in the model (F);
   8. Stage-1 gate (G);
   9. the Stage-2 plan or deferral (H);
   10. multiplicity (I);
   11. data collection and seal (J);
   12. missing data and VOID (K, L);
   13. identity and versioning (M, N, Q);
   14. the pre-registration schema (R);
   15. δ semantics (S);
   16. researcher degrees of freedom (the §3.5.10 analog);
   17. explicitly unchanged items.
3. **If M1-a is chosen:** an M8 identity v3 specification (D29 successor), for temperature.
4. **Implementation handoff** — only after 1 and 2 (and 3 if chosen) are frozen.
5. **SRC delta review** of 2 before freeze. **RD freeze gate** with tag (N2).

---

## 8. Implementation impact map

Descriptive only; nothing is authorized. "Pinned" means byte-pinned by `test_m9_statistics_unchanged.py`.

| Module | Pinned | Impact | Driver |
|---|---|---|---|
| `analysis/preregistration.py` | no | New constants (`SPEC_VERSION`, statistic identifier, decision rule, family sizes); new fields (δ, scale, estimand, test, seeds, optional temperature, Stage-2 plan, minimum n) | R, N2 |
| `analysis/binder.py` | no | Expected identity set per seed; Stage-1 arm scope (excludes A1 under J) | M, J |
| `analysis/executor.py` | no | Version and arm checks; Stage-1 branches replace `_k1_holm` and the four-model path; seed handling; δ shift before `one_sided_wald` | O, C |
| `analysis/result_record.py` | no | `eval_seed` becomes a seed set; δ and Stage fields; new record identity | M |
| `analysis/prereg_store.py` | no | Expected unchanged | — |
| `analysis/completeness.py` | **yes** | Required cells scoped to Stage-1 arms, and per seed | K, L |
| `analysis/decision.py` | **yes** | New Stage-1 decision (single margin test, or a two-test family if G2), with the VOID short-circuit retained | G |
| `analysis/gee.py` | **yes** | `Comparison.A2_VS_A0` (additive); `DESIGN_COLUMNS`; replicate rows per seed | C, F |
| `analysis/emm.py` | **yes** | A2 vs A0 branch; estimand per A (possibly a non-Interpretation-A gradient) | A |
| `analysis/trend.py` | **yes** | A2 vs A0 coefficient mapping, if the trend is reported or gated | G2 |
| `analysis/mcnemar.py` | **yes** | Unchanged if B excludes McNemar. It is not a gate test under G-5 | B |
| **new** paired-margin test module | — | Tango score or exact unconditional test (B-i / B-ii); D30.3 reading needed (CA-13) | B |
| `analysis/wald.py` | **yes** | **Unchanged** — the shift is applied by the caller | C (derived) |
| `analysis/holm.py` | **yes** | **Unchanged** — generic | I |
| `analysis/encoding.py` | **yes** | **Unchanged** — PASSED = 1 | — |
| `evaluation/provenance.py` (M8 v2) | no | Unchanged, unless M1-a (v3 adds temperature) | M1 |
| `agent/proposer.py`, `llm/client.py` (frozen M1) | no | Temperature wiring, if F1-a | F1 |
| `batch/runner.py` (frozen M5) | no | Seeded replicate order, if F1-b | F1 |
| `tests/unit/test_m9_statistics_unchanged.py` | — | Re-pinned to the new baseline under N3/O1 authority | O1 |
| `docs/M9_SPEC.md` | frozen | **Untouched** under N1-b | N1 |
| `docs/DECISIONS.md` | ratified | New D31 only; D6, D7 and D8 untouched | N3, G-9 |

**Explicitly unchanged in every option:**
- the frozen verdict taxonomy and the PASSED = 1 encoding;
- the held-out lock;
- `VerificationManifest` and identity-v2 key semantics;
- D26–D28 verifier ownership;
- the D6, D7 and D8 text.

---

## 9. Statement

**No production code, frozen specification, decision record, test, tag or remote was changed in producing this draft.**

- The Velith engineering repository remains at `0d247d982e48b30febe2fb53405e1c6d1ba29960` with a clean working tree.
- The only artifact created is this research file in `Velith-research`.
- This document authorizes nothing: not the amendment, the pilot harness, the pilot execution, or the production verifier.
