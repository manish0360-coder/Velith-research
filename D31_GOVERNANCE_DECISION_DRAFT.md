# D31 — Governance Decision Draft (R-1 resolution: Stage-1 successor to M9/M10)

**Document type:** Research-only governance decision **DRAFT**. **Not ratified. Not entered in `DECISIONS.md`. Not an implementation or pilot authorization.**
**Author:** Chief Systems Engineer. **Requested by:** Research Director.
**Date:** 2026-09-28.

## 1. Status

- The Director has not ratified D31.
- Entering D31 into Velith `docs/DECISIONS.md` requires a separate, explicit placement authorization.
- **No engineering-repository file was changed in producing this draft.**
  - Velith HEAD = origin/main = `0d247d982e48b30febe2fb53405e1c6d1ba29960`, with a clean working tree.
  - `DECISIONS.md` SHA-256 is `0b17d0322d6b9585de830237f3581c022f2ede6f9ceb7981c85e8d54671fd982` (unchanged).
  - M9, M10, tags and the remote are untouched.

## 2. Inputs (content-addressed)

| Input | SHA-256 |
|---|---|
| `M2-PV-P1-R_GOVERNANCE_ADJUDICATION.md` (R-1 adjudication) | `9eaa07ebc365be1fc214aa1f5f1e4a61fad8be1597d6233f837da52ad29ce7d5` |
| `M9-M10_STAGE1_AMENDMENT_SPEC_DRAFT.md` (parameters A–S) | `544159cdce76ee98d41b32f71c5c97901d35b010b546e9019933906a851e5601` |
| Gemini SRC review 1 (R-1 Q1–Q6) | `1eaef4cf0d5c8e54be930b504f8a0f08792daafe7c1be30bc1bcbcf18681aef2` |
| Gemini SRC review 2 (Q1–Q4 on the amendment draft) | `11567fac30425e4b2c7a1c2ca060272372f42512d208b08dec62299b2c8c21e6` |
| Velith `docs/DECISIONS.md` @ `0d247d9` | `0b17d0322d6b9585de830237f3581c022f2ede6f9ceb7981c85e8d54671fd982` |
| Velith `docs/M9_SPEC.md` @ `0d247d9` (frozen VM2) | `94dbdb9e075c5025f40b4e70305b74324971ae35439e5ca7a7a0f28370d1434e` |

**Classification of every clause (exactly one class each):**

| Class | Meaning |
|---|---|
| **FROZEN FACT** | Already true in a ratified decision or frozen specification. D31 restates it; it does not create it. |
| **SRC RULING** | Decided by the Scientific Review Council (Gemini) in reviews 1 or 2. D31 records it. |
| **RD GOVERNANCE DECISION** | A decision D31 makes by Director authority, if ratified. |
| **OPEN DECISION** | Deliberately not decided by D31. |

---

## 3. SRC R-1 record

| # | SRC ruling | Source | Class |
|---|---|---|---|
| S1 | The frozen M9 GO rule `A1 > A0 ∧ A2 > A1` is non-equivalent to D6 H1 and creates a false-NO-GO failure mode. `A1 > A0` is scientifically unnecessary. | Review 1 §§1, 3 | SRC RULING |
| S2 | Stage-1 go/no-go evaluates A2 > A0 exclusively. Pulling the decisive A2 > A1 into Stage 1 defeats staged spending. | Review 1 §4 | SRC RULING |
| S3 | A2 vs A0 must be computed directly, not inferred by transitivity. | Review 1 §§3, 5 | SRC RULING |
| S4 | Governance route: Option 2, a versioned M9/M10 successor. Option 1 (ratifying the frozen rule) is rejected. D6, D7 and D8 text are unchanged. | Review 1 §§11, 14 | SRC RULING |
| S5 | The minimum effect size δ is a response-scale absolute pass-rate difference, and a **strict gate** via the shifted null `H0: Δ20 ≤ δ`. | Review 1 §7 | SRC RULING |
| S6 | **Primary estimand A-iv:** `Δ20 = P(A2 pass at final checkpoint K) − P(A0 pass at episode 0)`, a model-free paired contrast over held-out tasks. GEE is reserved **strictly** for the secondary longitudinal trend. Interpretation A (A0 extrapolated along A2's slope) violates D6 for this purpose. | Review 2 Q1 | SRC RULING |
| S7 | **K = 1 gate test B-ii:** an exact unconditional paired-proportion test (for example Berger–Boos type) of `H0: Δ20 ≤ δ` vs `H1: Δ20 > δ`. McNemar is inapplicable (it is anchored to margin 0). **Wald (B-iii) is rejected.** | Review 2 Q2 | SRC RULING |
| S8 | **Fallback:** if B-ii proves computationally prohibitive, the RD **may** authorize the Tango score test (B-i) as a deterministic asymptotic fallback. | Review 2 Q2 item 4 | SRC RULING (the permission); its use is OPEN |
| S9 | **F1-c:** keep proposer temperature `T = 0.0`. There are no multiple sampling seeds (N = 1). The task is the independent unit, and inference uses task-level uncertainty. The review-1 recommendation N ≥ 3 is **formally withdrawn, conditional on T = 0.0**. | Review 2 Q3 | SRC RULING |
| S10 | δ, n, K, N and target power are **jointly** designed and frozen. δ must be a practically meaningful improvement (MCID), not merely the smallest detectable effect. The pilot base rate legitimately supplies nuisance/base-rate information from a set **disjoint** from the confirmatory set. | Review 2 Q4 | SRC RULING |
| S11 | If power is **< 80%** at the maximum usable held-out n for the chosen δ, the confirmatory Stage-1 design is **VOID before execution**, not an uninterpretable NO-GO. | Review 2 Q4 | SRC RULING |
| S12 | The scalar δ is chosen, justified and recorded by the RD **after** the pilot base rate is obtained. | Review 2 Q4 item 4 | SRC RULING (sequencing); the value is OPEN |

**CSE pre-ratification notes.** None of these contradicts the SRC. Each marks where the rulings leave a parameter unset, so D31 must not claim it is set.

- **N-1 — B-ii names a test family, not one test.** An exact unconditional paired test is fully determined only once three things are fixed:
  - (a) the test statistic that orders the sample space (for example the Tango score statistic, or the observed difference);
  - (b) whether the Berger–Boos confidence-interval restriction is used, and its γ;
  - (c) the nuisance-maximization grid or precision, which is needed for determinism.

  These are scientific parameters, so they stay OPEN.
- **N-2 — Power in a paired design needs more than the base rate.** It also depends on the *discordance*, i.e. the joint distribution of (A2@K, A0) outcomes per task, not only on `p0`. A zero-experience pilot measures `p0` only. The planning assumption for discordance stays OPEN.
- **N-3 — A 5-task pilot pins `p0` down only loosely.** The ratified pilot is "exactly 5" tasks (M2-PV-R record `:275`). For example, 0/5 successes gives a 95% Clopper–Pearson upper bound of about 0.52. Whether a 5-task pilot is adequate for S10, or needs a conservative planning rule or a larger design pilot, stays OPEN. D31 does **not** set pilot scope.
- **N-4 — S9 holds only while T = 0.0 is actually used.** Temperature is not an identity-v2 component (D29.2). The code default is `0.0` (`agent/proposer.py:90`), but the proposer is injected into the M8 runner. D31 can require `T = 0.0` for evaluations of record. The **enforcement mechanism** is implementation architecture and stays OPEN.
- **N-5 — S6 and S7 imply the same primary test at K > 1.** S6 makes the K > 1 primary a model-free paired contrast "mirroring K = 1". The natural reading is that the S7 test applies at checkpoint K for every K. D31 records that reading. It must be confirmed in the SRC delta review of the successor specification.

---

## 4. D31 clauses

| ID | Clause | Class |
|---|---|---|
| **C1** | D6, D7 and D8 remain in force **with their literal text unchanged**. D31 supersedes none of them. | RD GOVERNANCE DECISION (adopting S4) |
| **C2** | The authoritative Stage-1 contrast is A0 vs A2, a cheap go/no-go. A Stage-1 GO is necessary-but-not-sufficient and is never reported as confirmation (D8.5). | FROZEN FACT |
| **C3** | The M9 VM2 go/no-go rule (K = 1: A1 > A0 ∧ A2 > A1; K > 1: the four-test family) **is not the Stage-1 go/no-go** of D8.5 and D12. No evaluation of record may be analyzed under it to produce the Stage-1 decision. **This resolves R-1.** | RD GOVERNANCE DECISION (on S1, S2) |
| **C4** | The resolution is **Option 2**: a versioned M9/M10 Stage-1 successor (a successor specification plus a successor analysis layer), frozen through the full pipeline (Specification → SRC → RD freeze → Handoff → Engineering → Verification). Option 1 is rejected. | RD GOVERNANCE DECISION (on S4) |
| **C5** | **Historical reproducibility.** Frozen M9 (`m9-spec-frozen-oed7-vm2`, and the earlier freezes), `docs/M9_SPEC.md`, the analysis code at `m9-complete` / `5476d82`, and their identities stay **exactly as they are** and remain reproducible at their tags. No VM2 pre-registration is converted, rehashed or reinterpreted. This follows the D29 precedent for M8 v1. | RD GOVERNANCE DECISION |
| **C6** | **Scoped supersession of D30.2.** For the analysis layer only, D30.2's historical freeze does not bar the versioned Stage-1 successor. D30.2 continues to govern all historical versions (C5) and all other M1–M9 machinery. | RD GOVERNANCE DECISION |
| **C7** | **D30.3 reading.** The successor analysis layer, including an exact unconditional test, completes the D12 M10 experiment in Velith. It is **not** a new generic platform mechanism under D30.3, is scoped to the compounding experiment, and is not exposed as a reusable service. Any later extraction to Noetica follows Law 8 and a Noetica CAP. | RD GOVERNANCE DECISION |
| **C8** | **Scoped supersession of D29 item 3, for the `spec_version` value only.** Successor pre-registrations carry a new `spec_version`, not `"m9-spec-frozen-oed7-vm2"`. All other D29 provisions remain in force, including identity v2, the VerificationManifest, fail-closed checks and the mixed-version join rejection (extended to VM2 ↔ successor). | RD GOVERNANCE DECISION |
| **C9** | **Primary Stage-1 estimand A-iv:** `Δ20 = P(A2 pass at final pre-registered checkpoint K) − P(A0 pass)`, a paired contrast over the held-out tasks. A0 is the zero-experience agent. At an empty checkpoint, A0, A1 and A2 prompts are bit-identical (`M8_SPEC.md:96–98`), so A0 is "the same agent at episode 0" of D6. | SRC RULING (S6) |
| **C10** | **Stage-1 hypotheses:** `H0: Δ20 ≤ δ` vs `H1: Δ20 > δ`, with **δ > 0**: a strict positive-margin superiority hypothesis. | SRC RULING (S5, S7) |
| **C11** | **K = 1 gate test:** an exact unconditional paired-proportion test (B-ii). Wald is excluded. McNemar is not the gate test. | SRC RULING (S7) |
| **C12** | **K > 1:** the primary gate applies the same exact unconditional test to the paired contrast at checkpoint K. GEE is used only for the secondary longitudinal trend. The trend is reported and never gates. | SRC RULING (S6), recorded per N-5, subject to SRC delta confirmation |
| **C13** | **Significance level:** the one-sided gate is tested at α = 0.01, the frozen M9 level, which the SRC applied. | FROZEN FACT (`M9_SPEC.md` α; SRC review 2 Q2) |
| **C14** | **Stage-1 gate:** GO iff the C11/C12 test rejects `H0` at α. NO-GO otherwise. VOID only under C19–C21. | RD GOVERNANCE DECISION (composing C10, C11, C13) |
| **C15** | **Sampling:** evaluations of record under the successor use proposer temperature **`T = 0.0`**. Any other temperature requires a new decision, and the S9 withdrawal of N ≥ 3 would then lapse. | SRC RULING (S9); adopted as a binding condition |
| **C16** | **Seeds: N = 1** evaluation seed per evaluation of record. D8.2's "seed count" is thereby frozen at 1. | SRC RULING (S9) |
| **C17** | **Unit and uncertainty:** the held-out task is the independent unit. Inference and reported uncertainty are task-level. The D8.6 reference to "seed-spread" is inapplicable at T = 0.0, N = 1, and is replaced for reporting by the task-level confidence bound on Δ20. This is an application of D8.6, not a change to its text. | SRC RULING (S9); the D8.6 application is an RD GOVERNANCE DECISION |
| **C18** | **δ is NOT selected by D31.** δ is a response-scale absolute pass-rate difference and must represent a practically meaningful improvement (MCID). The RD records it with justification after the pilot base rate is obtained. | SRC RULING (S5, S10, S12); the value is OPEN |
| **C19** | **Joint design before execution:** δ, the usable held-out n, K, N (= 1), α (= 0.01) and target power (≥ 0.80) are specified **jointly** and frozen in the successor pre-registration **before** any confirmatory evaluation of record is produced. | SRC RULING (S10) |
| **C20** | **Power VOID:** if the pre-execution power of the C11/C12 test is < 0.80 at the maximum usable held-out n for the chosen δ, the confirmatory Stage-1 design is **VOID before execution**. It is never run and never reported as NO-GO. | SRC RULING (S11) |
| **C21** | **Retained VOID dispositions:** M8 global-incomplete gives VOID; `n = 0` after complete-case gives VOID (OED-7); an empty held-out population is rejected at VerificationManifest construction (D29). VOID is never NO-GO. | FROZEN FACT |
| **C22** | **Design vs confirmatory boundary:** see §5. | RD GOVERNANCE DECISION |
| **C23** | **A1 seal.** If A1 is collected concurrently, the Stage-1 analysis reads no A1 outcome, and no A1 outcome is disclosed before the Stage-2 analysis plan is fixed. This keeps every Stage-2 timing option in D12/D15 open **without choosing one**. | RD GOVERNANCE DECISION |
| **C24** | **D12 clarification (not supersession):** the D12 "full A0/A2 run" is delivered as the confirmatory Stage-1 evaluation of record under the successor pre-registration, before M10 analysis. `m9-complete` remains the tag of the pre-registration layer as delivered. | RD GOVERNANCE DECISION |
| **C25** | **Stage-2 timing, its hypotheses and cross-stage multiplicity are not decided by D31.** D12 and D15 govern unchanged. C23 guarantees no option is foreclosed. | OPEN DECISION |
| **C26** | **Identity:** under C15 and C16, M8 identity v2 is used unchanged. No M8 identity v3 is created. | RD GOVERNANCE DECISION (follows from S9 and D29) |
| **C27** | **No authorization:** D31 authorizes no implementation, no pilot harness, no pilot execution, no production verifier, and no confirmatory evaluation. Each needs its own gate. | RD GOVERNANCE DECISION |

---

## 5. Pilot/design information vs confirmatory inference (C22)

**D1. Permitted use of the pilot.** Pilot outputs (base rate `p̂0`, feasibility, cost) may inform **design only**: δ selection context, the nuisance for power, usable n, K and cost limits. They never enter a confirmatory estimate, test, gate, arm memory, episode store or evaluation sink.
- Class: RD GOVERNANCE DECISION, consistent with S10 and the ratified pilot properties.

**D2. Disjointness.** Every pilot task is excluded from the confirmatory held-out population by a content-addressed exclusion registry, frozen before the successor pre-registration is sealed.
- Class: RD GOVERNANCE DECISION (S10 "disjoint").
- The registry mechanism is proposed in the pilot design (P-1). Its ratification is OPEN.

**D3. Sealing order.** δ, n, K, N, α and power are frozen and hashed in the successor pre-registration **after** the pilot and **before** any confirmatory evaluation of record. Any confirmatory outcome observed before sealing voids that pre-registration (M9 §3.4 principle).
- Class: RD GOVERNANCE DECISION.

**D4. No promotion.** A pilot result is never re-labelled as a Stage-1 result, whatever its size.
- Class: RD GOVERNANCE DECISION.

---

## 6. Supersession and preservation

| Record | Effect of D31 |
|---|---|
| D6, D7, D8 | **Preserved verbatim**; not superseded (C1). D8.6 "seed-spread" is *applied* as inapplicable at N = 1 (C17), which is not a text change. |
| D12 | Preserved. Its M9 "full A0/A2 run" is **clarified** (C24), not superseded. If the Director judges C24 substantive, it becomes a scoped supersession of D12 and must be marked as such. |
| D15 | Preserved; Stage-2 details remain post-M10 (C25). |
| D29 | **Scoped supersession of item 3, the `spec_version` value only** (C8). Everything else is preserved. |
| D30 | **Scoped supersession of item 2, for the analysis-layer successor only** (C6). Item 3 is read per C7. Items 1 and 4 and the D30 consequences are preserved. |
| M9 VM2 specification | Remains frozen and historical. It is superseded **prospectively** for new pre-registrations by the successor specification, once frozen. It is not edited. |
| M10 executor (`e04d7f9` / `5476d82`) | Remains the historical VM2 executor, reproducible at its tags. It is replaced for new analyses by the successor layer. The implementation architecture is OPEN (G-A7). |
| M8 identity v2 | Unchanged and in force (C26). |
| D26–D28 | Unaffected. |

**Contradiction check of the draft:** no clause edits a frozen text. Each supersession is scoped and named, as the amendment procedure (`DECISIONS.md:679–686`) requires. No clause chooses δ, Stage-2 timing, multiplicity, pilot scope or implementation architecture.

---

## 7. D31 proposed text

```markdown
## D31 — R-1 resolution: Stage-1 go/no-go realigned to D8.5 through a versioned M9/M10 Stage-1 successor

**Status:** Proposed (not ratified). **Date:** 2026-09-28. **Authority:** Director ruling on the R-1
governance adjudication and the Scientific Review Council rulings (SRC reviews 1 and 2).
**Supersedes (scoped, named):**
- D29 item 3 — only the literal `spec_version` value, for pre-registrations created under the
  Stage-1 successor. All other D29 provisions remain in force.
- D30 item 2 — only insofar as it would bar a versioned successor of the analysis layer. Historical
  versions remain frozen and reproducible.
**Does not supersede:** D6, D7, D8 (text unchanged), D12, D15, D26–D28, M8 identity v2.

**Evidence / flaw (amendment procedure).**
- D8.5 defines Stage 1 as A0 vs A2, a cheap go/no-go. D12 assigns Stage-1 statistics and the
  go/no-go to M10.
- Frozen M9 (VM2) and the M10 executor decide GO by A1 > A0 ∧ A2 > A1, and compute no A2-vs-A0
  statistic. No record superseded D8.5 (R-1 adjudication).
- The SRC ruled the frozen rule non-equivalent to D6 H1, with a false-NO-GO failure mode, and
  ruled that the minimum effect size and seed count required by D8.2 are unoperationalized.

**Decision.**
1. D6, D7 and D8 remain in force with their text unchanged.
2. The M9 VM2 go/no-go rule is not the Stage-1 go/no-go. No evaluation of record is analyzed
   under it for the Stage-1 decision. R-1 is resolved.
3. A versioned M9/M10 Stage-1 successor (specification and analysis layer) is authorized to be
   specified and frozen through the full pipeline. This decision authorizes no implementation.
4. Frozen M9 (all tags), `docs/M9_SPEC.md`, the analysis code at its tags and their identities
   stay exactly as they are and remain reproducible. Nothing is converted or rehashed.
5. The successor analysis layer completes the D12 M10 experiment in Velith. It is not a new
   generic platform mechanism under D30.3.
6. Stage 1:
   - primary estimand Δ20 = P(A2 pass at final checkpoint K) − P(A0 pass), a paired
     contrast over held-out tasks;
   - H0: Δ20 ≤ δ vs H1: Δ20 > δ, with δ > 0;
   - the test is an exact unconditional paired-proportion test at one-sided α = 0.01, applied
     at checkpoint K for every K;
   - Wald is excluded;
   - GEE is used only for a secondary, non-gating longitudinal trend.
   GO iff H0 is rejected; NO-GO otherwise. A Stage-1 GO is necessary-but-not-sufficient (D8.5).
7. Evaluations of record use proposer temperature T = 0.0 and one evaluation seed (N = 1).
   The held-out task is the unit. Uncertainty is task-level, and D8.6's seed-spread is
   inapplicable under these conditions. Any other temperature requires a new decision.
8. δ is not selected by this decision. δ is a response-scale absolute pass-rate difference that
   represents a practically meaningful improvement, and is recorded with justification by the
   Research Director after the pilot base rate is obtained.
9. δ, usable held-out n, K, N, α and target power (≥ 0.80) are specified jointly and frozen in the
   successor pre-registration before any confirmatory evaluation of record. If power is below
   0.80 at the maximum usable n, the confirmatory Stage-1 design is VOID before execution — never
   NO-GO. The frozen VOID dispositions (global-incomplete; n = 0; empty VerificationManifest) are
   retained.
10. Pilot information may inform design only, and never enters confirmatory inference, memory or
    evaluation records. Pilot tasks are excluded from the confirmatory held-out population by a
    frozen, content-addressed exclusion registry.
11. If A1 is collected concurrently, the Stage-1 analysis reads no A1 outcome, and no A1 outcome
    is disclosed before the Stage-2 analysis plan is fixed. Stage-2 timing, hypotheses and
    multiplicity are not decided here; D12 and D15 govern.
12. D12's "full A0/A2 run" is delivered as the confirmatory Stage-1 evaluation of record under
    the successor pre-registration.
13. M8 identity v2 is used unchanged.

**Rationale.** It realigns the go/no-go to the ratified D8.5 without rewriting D6, D7 or D8. It
removes a false-NO-GO dependency on A1. It tests the D6 contrast against the zero-experience agent
directly. It uses exact inference at small n. It prevents an underpowered study from producing an
uninterpretable NO-GO. It preserves the historical record.

**Alternatives rejected.**
- Option 1 (a supersession ratifying the frozen three-arm rule): it encodes the A1 > A0 dependency.
- Interpretation A for the primary estimand: it extrapolates A0 along A2's slope, contrary to D6.
- The asymptotic Wald gate: Type-I inflation at small n.
- Multiple sampling seeds at T = 0: degenerate replicates, no information.
- Choosing δ before the base rate is known: statistically blind.

**Consequences.**
- A successor specification, SRC delta review, RD freeze and implementation handoff are
  required, each separately authorized.
- The open decisions listed in the D31 governance draft remain open.
```

---

## 8. Remaining scientific decisions (SRC)

1. **Exact test specification (N-1):**
   - the ordering statistic;
   - whether the Berger–Boos restriction is used, and its γ;
   - the nuisance-maximization grid/precision, and a determinism requirement for the p-value.
2. **Power planning under discordance (N-2):** the planning assumption for the paired joint distribution, for example a conservative bound, since the pilot supplies `p0` only.
3. **Pilot adequacy for the nuisance (N-3):** whether a 5-task base rate suffices, or a conservative rule (for example an upper confidence bound on `p0`) or a larger design pilot is required. This is advice to the RD; the scope decision is governance.
4. **K > 1 confirmation (N-5):** confirm that the S7 test applies at checkpoint K, and specify the secondary GEE trend model for A2 alone (additive; reporting only).
5. **Complete-case scope for Stage 1:** A0 plus A2@K only, or all A2 checkpoints. Also how intermediate-checkpoint missingness affects the secondary trend only.
6. **Minimum analysable n** after complete-case exclusion (the D8.6 "uninterpretable" guard), where it differs from the C20 pre-execution check.
7. **δ acceptability review:** the SRC reviews the RD's recorded δ, its MCID rationale and the power calculation before freeze.

## 9. Remaining governance decisions (RD / Director)

1. **G-A1: Ratify D31** as drafted or amended. **Placement** into `DECISIONS.md` is a separate authorization.
2. **G-A2: Clause C24:** accept it as a D12 clarification, or mark it as a scoped supersession.
3. **G-A3: δ scalar** (after the pilot base rate), with its MCID justification.
4. **G-A4: Stage-2 timing, hypotheses and multiplicity** under D12/D15 (the H1, H2 and I options of the amendment draft).
5. **G-A5: Data collection:** Option-C derivative (A1 concurrent, sealed per C23) or Option A (A0/A2 only).
6. **G-A6: Pilot:**
   - harness authorization (PB-1);
   - execution scope and size (5 as ratified, or amended per SRC item 3);
   - OD-1 to OD-12;
   - the D30 posture statement;
   - ratification of the exclusion registry.
7. **G-A7: Implementation architecture:**
   - in-place single path or parallel successor modules;
   - re-pinning `test_m9_statistics_unchanged.py`;
   - the T = 0.0 enforcement mechanism (N-4).
8. **G-A8: Successor specification form and version:** a separate successor file or an appended block; the `spec_version` string and freeze tag.
9. **G-A9: B-i fallback:** authorize the Tango test only if B-ii is shown computationally prohibitive.
10. **G-A10: Usable held-out n:** fix the M4 held-out partition size for the real corpus, net of pilot exclusions.

## 10. Exact next gate

**G-D31 — Director review of this D31 draft.** The possible outcomes:

- **(a) Ratify.** The next step is a separately authorized placement of D31 into `DECISIONS.md`.
- **(b) Amend.** State which clauses change.
- **(c) Reject.**

After ratification, the critical path is:

1. the SRC delta items §8.1–§8.3;
2. the pilot decisions (G-A6), because the δ, n and power design (C19) cannot be completed without a base rate;
3. then the successor specification draft.
