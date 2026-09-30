# M9-ST1 — RD Decision Register (Stage-1 successor)

**Type:** research / decision preparation only. **It decides nothing, freezes nothing, implements nothing and authorizes nothing.** It is not committed to Velith.
**Author:** Chief Systems Engineer, for the Research Director.
**Date:** 2026-09-28.

**Baseline:**
- Velith `5452efc44274c575c781673eb9c6287facfb94e6` (= origin/main at the last push); working tree clean; 15 tags.
- `DECISIONS.md` `57e228d6…` (D31 at line 680).

**Authoritative basis:**
- the CSE Final Integration Audit (`reviews/src/INTEGRATION_2026-09-28_SRC_FINAL_Q1_Q2_Q4.md`, `b3038799…`);
- the SRC responses `c1ced0a2…`, `6524233d…` and `3c0a79bd…`;
- the RD Freeze Decision Input `e69f4f48…`;
- the M2-PV-R ratification record `84d67088…`;
- the M2-PV handoff `8d193f10…`;
- the P1 pilot design `89f931e0…`.

> **Package status: BLOCKED BY ONE CONTRADICTION (§7, C-1).** The register is complete, but it cannot be declared ready until the RD rules on **RD-0**.
>
> **Update 2026-09-29.** The RD ruled RD-0 = Option (B). The proposed amendment is `RD-0_C-1_RESOLUTION_AMENDMENT_PROPOSED.md`, **awaiting ratification**. From here on, RD-1, RD-2 and RD-2b apply to the new **Base-Rate Design Pilot (BRP)**, not to P1. P1 stays feasibility-only and its own OD-1 to OD-12 are unchanged.

---

## 1. Current-state audit

| # | Statement | Evidence | Result |
|---|---|---|---|
| A | The statistical framework is closed | SRC `3c0a79bd…` "READY FOR RD FREEZE"; integration audit "No further SRC review is required" (the S-R3 parameter check excepted) | TRUE |
| B | VM2 is frozen | `M9_SPEC.md` `94dbdb9e…` unchanged; tag `m9-spec-frozen-oed7-vm2`; the 9 statistics modules match their byte pins (`completeness` `80dfdadf…` … `wald` `9a28e334…`) | TRUE |
| C | D31 is ratified | `DECISIONS.md:60, :680`; commit `5452efc`; status "Accepted" | TRUE |
| D | C-ID is implemented | `5476d82` is in history ("feat(m8-m9): implement evaluation identity v2") | TRUE |
| E | The pilot is not authorized | P1 design §1 "Not authorized for execution"; PB-1 and OD-1 to OD-12 open | TRUE |
| F | The successor M9/M10 specification is not frozen | No successor specification in `docs/`; only a research draft (`M9-M10_STAGE1_AMENDMENT_SPEC_DRAFT.md`, predating the SRC closure) | TRUE |
| G | Implementation is not authorized | D31 decision 3 ("authorizes no implementation"); no successor code | TRUE |

## 2. RD decision register

Each entry uses the same fields. "Frozen" means D31/DECISIONS, frozen specifications, or SRC-accepted machinery (SM1–SM11, S-R1, Q1/Q2/Q4).

### RD-0 — Pilot role reconciliation (from contradiction C-1)

- **Why it exists.** D31 decision 8 and the SRC-accepted chain require a pilot that yields a **base rate p0 with a two-sided 95% Clopper–Pearson (CP) interval**, run under the **identical confirmatory A0 configuration**. The only designed pilot, M2-PV-P1, is RD-ratified as **"not a solve-rate estimate"**, and it forbids rates and intervals (§7).
- **Frozen constraints.**
  - D31 decisions 8 and 10 (the pilot base rate informs design only; pilot tasks are excluded from the held-out population).
  - The SRC chain and configuration equivalence (SM10, SM11).
  - The hierarchy: DECISIONS > RD-ratified research.
- **Evidence available.** P1 design §2, §6, §17, §24; M2-PV-R §9 (`:272–283`; P-3 proposed at `:291`, ratified through P1 §6); the SRC final review item 5.
- **Evidence missing.** None. This is a governance choice.
- **Allowed decision space.**
  - (a) Amend P1 through a research amendment (purpose, P-3, endpoint, selection, size, configuration) so that it *is* the base-rate pilot.
  - (b) Keep P1 as the feasibility pilot and define a **separate base-rate design pilot**.
  - (c) Another RD-defined arrangement that satisfies D31 and SM10/SM11.
- **Must NOT change.** D31; the SRC chain; pilot/confirmatory separation; held-out exclusion.
- **Dependency.** None. This decision is first.
- **Downstream.** RD-1, RD-2, RD-2b, RD-4 and the whole power chain.
- **Consequences.**
  - (a) P1 inherits every base-rate requirement: representative selection, confirmatory endpoint, a single confirmatory material → prompt function, and a size adequate for power planning. It can no longer run under its current design. BC-1's "pilot before production-verifier automation" must then be reconciled with the confirmatory configuration, which needs the production path.
  - (b) P1 can proceed as designed, as feasibility only. The base-rate pilot comes later: it needs the confirmatory A0 configuration to exist (D28 adapter, material → prompt function), and possibly the production verifier for a confirmatory-endpoint p0. δ is delayed accordingly.
  - (c) Must be shown to satisfy both D31 and SM11.
- **Who decides.** RD, by recording a research amendment. No D31 change is needed.
- **Status.** **RULED: Option (B)** (RD, 2026-09-29). The amendment text is drafted and **not ratified**. C-1 closes on ratification.

### RD-1 — Pilot size (BRP; since RD-0 = B)

- **Why it exists.** P1 says "exactly 5 … unless a later approved research amendment changes this" (M2-PV-R `:275`). The SRC chain makes adequacy a function of the power computation: no fixed n, and n = 30 is rescinded.
- **Frozen constraints.** A 95% CP interval (γ_pilot = 0.05). The planning p0 is the power-minimizing value inside that interval. The design is VOID if n_conf > N_avail.
- **Evidence available.** Arithmetic in the prior CSE audit, illustrative only: with 0 successes, the 95% upper confidence limit falls below (1 − Δ)/2 = 0.45 only when n_pilot ≥ 7, using Δ = 0.10 as an example value.
- **Evidence missing.** δ and Δ_true (to know whether a narrower interval matters), N_avail.
- **Allowed decision space.** Any size, justified by the dependency chain. A size other than 5 requires the research amendment.
- **Must NOT change.** γ_pilot; the design-only role.
- **Dependency.** RD-0.
- **Downstream.** The p0 interval, power_plan, n_conf.
- **Consequences.**
  - A small pilot gives a wide interval. The worst-case planning p0 is then near maximum variance, which pushes n_conf up and makes VOID more likely.
  - A larger pilot narrows the interval but consumes candidate held-out tasks (exclusions reduce N_avail).
- **Who decides.** RD.
- **Status.** OPEN.

### RD-2 — Pilot scope (task population and selection) (BRP)

- **Why it exists.** p0 only plans the confirmatory population if pilot tasks are drawn from it.
- **Frozen constraints.**
  - Pilot tasks are permanently excluded from the held-out population (D31 decision 10; P-1).
  - Selection is outcome-blind.
- **Evidence available.** The P1 selection: fixed anchor `pallets__flask-5014`; filters (a)–(e) (pytest-only, `.py` test patches, ≥ 1 P2P, 1–5 F2P, single-file gold); repository exclusions; a salted lottery over a pool of 98.
- **Evidence missing.** The definition of the confirmatory population, from the real corpus (RD-3).
- **Allowed decision space.** A selection rule matching the confirmatory population's eligibility rules, or a documented deviation with its consequence for p0 validity.
- **Must NOT change.** Outcome-blindness; exclusion permanence.
- **Dependency.** RD-0; RD-3 (the population definition).
- **Downstream.** Validity of p0 as a nuisance estimate.
- **Consequences.** The P1 filters and the fixed anchor are not a random sample of any held-out population. A p0 from them would be biased in an unknown direction.
- **Who decides.** RD.
- **Status.** OPEN.

### RD-2b — BRP configuration equivalence — **CLOSED: OPTION V (verdict-level)**

- **Decision.** The BRP SHALL obtain p0 from the same PASSED endpoint used by the eventual Stage-1 analysis: material → TaskSpec → proposer → candidate → production verifier (D26) → hash-locked Velith classifier (D27) → PASSED / non-PASSED. The M2 probe PASSED and `patch_applies` are **not** substitutes.
- **Authority.** Research Director ruling, 2026-09-29.
- **Rationale (RD):**
  - D31 decision 6 defines the estimand on PASSED.
  - SM7 (p2 = p0 + Δ_true) requires one endpoint.
  - SM8/SM10 handle sampling uncertainty, not instrument bias.
  - R_P,probe = R_V is not established.
  - D26/D27/D28 make the production verifier the real-task source of truth.
  - Reopening SM8/SM10/SM11 for a proxy rule is **not authorized**.
- **Record.** `RD-2b_BRP_VERIFIER_REQUIREMENT_ANALYSIS.md` §9.
- **Consequences:**
  - Option P is rejected.
  - No SRC review, because no frozen statistical quantity changes.
  - The BRP cannot execute before a validated production verifier exists.
  - RD-0 amendment clause 4 is updated (revision R1, still unratified).
- **Dependencies:**
  - P1 (BC-1) → M2-PV specification freeze (BC-2) → production-verifier implementation → validation → BRP;
  - plus the real corpus, the D28 adapter and registry, and the pinned proposer identity.
- **Remaining engineering / design questions:**
  - the extent of validation required before the BRP;
  - how verifier and classifier identity are pinned and matched between the BRP and the confirmatory run;
  - a BRP execution path that writes no M8 evaluation-of-record artifacts;
  - the BRP completion rule.

  These are analysed in `BRP_M2-PV_PREREQUISITES_ANALYSIS.md`.
- **Current state:** production verifier **not complete**; M2-PV specification **not frozen**; BRP, its implementation and its execution **not authorized**.
- **Status.** **CLOSED.**

### RD-3 — N_avail

- **Why it exists.** It is the upper bound in the n_conf definition and in the VOID test (SM10, Q2).
- **Frozen constraints.**
  - n_conf ≤ N_avail.
  - VOID ⟺ power_plan(N_avail) < 0.80.
  - Pilot exclusions reduce N_avail.
  - The VerificationManifest (VM) covers the held-out evaluation population (D29).
- **Evidence available.** M4 machinery: identity = SHA-256(material) (`corpus/manifest.py`), a partition manifest with a stable hash, and the loader. The SWE-bench Verified revision is `78f471bf…` (P1 §10).
- **Evidence missing.** The real corpus, its partition, the exclusion registry, and the TaskSpec transport (see §5).
- **Allowed decision space.** The held-out partition rule and fraction, and the corpus revision.
- **Must NOT change.** Held-out lock (D8.3); identity semantics.
- **Dependency.** RD-0/RD-2 (exclusions); M4 real-dataset adapter; D28 registry; D26 TaskSpec schema.
- **Downstream.** n_conf, the adequacy check, RD-8, the VM, sealing.
- **Consequences.** A larger held-out share gives more power but leaves fewer available tasks for M5 accumulation, which A2's memory depends on.
- **Who decides.** RD (the partition), from engineering evidence.
- **Status.** OPEN; evidence missing.

### RD-4 — δ / MCID

- **Why it exists.** It is the margin in H0: Δ20 ≤ δ (D31 decision 6).
- **Frozen constraints.**
  - 0 < δ < 1, as an absolute pass-rate difference.
  - It must be the minimum clinically important difference (MCID): practically meaningful, not merely the smallest detectable effect.
  - It is recorded with justification **after** the pilot base rate is known (D31 decision 8).
  - It may not be lowered merely to pass adequacy (Freeze Input D-5).
- **Evidence available.** None yet.
- **Evidence missing.** The pilot p0 interval; a program-level rationale for what lift justifies Stage-2 spend.
- **Allowed decision space.** Any δ in (0, 1) with a recorded MCID rationale.
- **Must NOT change.** The response scale; the post-pilot timing.
- **Dependency.** RD-0, RD-1, RD-2, RD-2b, then the pilot.
- **Downstream.** power_plan, n_conf, VOID or continue, the pre-registration.
- **Consequences.** A larger δ is a stricter gate and needs more n for the same power.
- **Who decides.** RD; S-R3 SRC check unless waived.
- **Status.** OPEN.

### RD-5 — Δ_true

- **Why it exists.** It is the assumed true effect in ExactPower (SM7, Q2).
- **Frozen constraints.** p2 = p0 + Δ_true. For the design to be powered it must satisfy Δ_true > δ, since power at Δ_true ≤ δ is at most α.
- **Evidence available / missing.** No empirical estimate exists; the pilot cannot estimate A2.
- **Allowed decision space.** Δ_true > δ, with a justification.
- **Must NOT change.** Frozen planning use only; no post-hoc revision.
- **Dependency.** RD-4.
- **Downstream.** power_plan, n_conf.
- **Consequences.** An optimistic Δ_true gives a smaller n_conf but a real risk of an underpowered true effect. It is used only for planning and never enters inference.
- **Who decides.** RD.
- **Status.** OPEN.

### RD-6 — Governing planning discordance scenario

- **Why it exists.** The adequacy gate needs one scenario (SM9).
- **Frozen constraints.** The sensitivity grid is mandatory. Independence is an empirical assumption, not a bound.
- **Evidence available.** The SRC concurs with independence (`c1ced0a2…` item 4).
- **Evidence missing.** None required.
- **Allowed decision space.** Independence; Fréchet maximum discordance; a positive-correlation scenario.
- **Must NOT change.** The grid must still be reported.
- **Dependency.** None.
- **Downstream.** power_plan, n_conf.
- **Consequences.**
  - Fréchet is most conservative: largest n_conf, highest VOID risk.
  - A positive-correlation scenario is least conservative.
- **Who decides.** RD.
- **Status.** OPEN.

### RD-6b — The two positive-correlation sensitivity scenarios

- **Why it exists.** The SRC mandated them without values.
- **Frozen constraints.** There are exactly two, and they are reported. They gate only if chosen under RD-6.
- **Evidence available / missing.** None / none required.
- **Allowed decision space.** Any two correlations (or p11 values) within the Fréchet bounds.
- **Must NOT change.** The grid composition.
- **Dependency.** RD-6.
- **Downstream.** The power report.
- **Consequences.** Reporting-only if RD-6 = independence.
- **Who decides.** RD.
- **Status.** OPEN.

### RD-8 — Optional admission buffer

- **Why it exists.** Admission losses can make n_admitted < n_conf, which is VOID before execution.
- **Frozen constraints.** The buffer is optional, pre-execution and outcome-blind. n_analyzed = n_admitted, with no truncation (Q4).
- **Evidence available / missing.** The admission failure rate is unknown until real TaskSpec admission is run.
- **Allowed decision space.** No buffer, or a pre-declared rule and size bounded by N_avail.
- **Must NOT change.** No selection based on outcomes; no truncation.
- **Dependency.** RD-3; admission evidence.
- **Downstream.** The probability of pre-execution VOID.
- **Consequences.** No buffer means a higher VOID risk. If every N_avail task goes to admission, a buffer is moot.
- **Who decides.** RD.
- **Status.** OPEN.

### RD-9 (D31 draft G-A5) — Option C (A1 concurrent, sealed) vs Option A (A0/A2 only)

- **Why it exists.** It fixes the evaluated arms, and therefore the pre-registered identity set and the compute.
- **Frozen constraints.** If A1 is collected it is sealed (D31 decision 11). Only pre-registered identities are tolerated (S-R1).
- **Evidence available / missing.** None / compute budget.
- **Allowed decision space.** C or A.
- **Must NOT change.** The A1 seal; the primary cells.
- **Dependency.** None. It interacts with G-A4 (Stage-2 timing), which is **not** required for Stage-1 sealing.
- **Downstream.** The pre-registration identity set; compute; Stage-2 options.
- **Consequences.**
  - C: about 50% more compute, and it preserves Stage-2 data options.
  - A: cheapest, and Stage 2 needs new A1 runs.
- **Who decides.** RD.
- **Status.** OPEN.

### S-R3 — Retain or waive the scheduled SRC check of δ, MCID and power

- **Why it exists.** It is listed in the RD Freeze Decision Input and the D31 governance draft §8.7.
- **Frozen constraints.** It does not reopen the framework.
- **Allowed decision space.** Retain or waive.
- **Dependency.** RD-4 to RD-6.
- **Consequences.**
  - Retain: one more parameter-level check before sealing.
  - Waive: the RD alone owns the numbers.
- **Who decides.** RD.
- **Status.** OPEN.

### G-A8 — Successor specification form and version

- **Why it exists.** It is needed to draft and freeze the successor.
- **Frozen constraints.** VM2 is not edited (D31 decision 4). There is a new `spec_version` (D29 item 3, scoped by D31).
- **Allowed decision space.**
  - A separate successor file (for example `docs/M9_STAGE1_SPEC.md`), or an appended block.
  - The version string and freeze tag.
- **Dependency.** None.
- **Downstream.** Successor specification drafting and freeze.
- **Consequences.** A separate file keeps VM2 byte-identical, consistent with D30.2 as scoped by D31.
- **Who decides.** RD.
- **Status.** OPEN.

### G-A7 — Implementation architecture

- **Why it exists.** It is needed before the implementation handoff.
- **Frozen constraints.** VM2 stays reproducible at its tags. D30.3 is read per D31 decision 5.
- **Allowed decision space.**
  - In-place single path vs parallel successor modules.
  - Re-pinning `test_m9_statistics_unchanged.py`.
  - The T = 0 enforcement mechanism (temperature is not in identity v2).
  - The result-record structure under primary-first ordering.
  - Verifying completion from records (I-1).
- **Dependency.** Successor specification freeze.
- **Downstream.** The implementation handoff.
- **Who decides.** RD, on engineering evidence.
- **Status.** OPEN; not needed for pre-registration sealing.

## 3. Pilot decision package

| Item | Currently frozen | Open for RD | Requires evidence | Requires implementation design | Requires SRC check |
|---|---|---|---|---|---|
| Role (feasibility vs base rate) | D31 decision 8 needs a base rate; P1 is ratified as feasibility-only | **RD-0** | — | — | — |
| Size | "Exactly 5" (P1, M2-PV-R `:275`), amendable | RD-1 | δ, Δ_true, N_avail (for the adequacy logic) | — | only within S-R3 |
| Task scope | Exclusion is permanent; selection is outcome-blind | RD-2 | The confirmatory population (RD-3) | — | — |
| Representative selection | — | RD-2 | Population eligibility rules | — | — |
| Exclusion registry | Principle P-1 [RATIFIED]; mechanism proposed (P1 §10; OD-9) | OD-9 | — | Future code-enforced check (class C) | — |
| "Exactly 5" amendment | M2-PV-R `:275` requires an approved research amendment | RD-0 / RD-1 | — | — | — |
| Model weights digest | Required (RD-2b = V) | — | **EXT-5** (`ollama show`, `/api/tags`) | Record the digest, not only the tag | — |
| Proposer configuration | `ProposerAgent`/`OllamaClient` unmodified (P1 §12); BRP = the confirmatory A0 configuration (RD-2b = V) | Pinning values (engineering) | — | — | — |
| T = 0 | **FROZEN** (D31 decision 7) | — | — | Enforcement (G-A7) | — |
| Seed derivation | N = 1 frozen | OD-12 (`derive_task_seed(id, 0)` proposed) | — | — | — |
| `num_ctx` / `num_predict` | Server defaults today | OD-3 (defaults + inadmissibility, or a Modelfile model) | EXT-5 effective `num_ctx` | Modelfile identity, if chosen | — |
| Prompt template | D28 D-2 (a pure function of material) | OD-1 (material), OD-2 (template) | — | The confirmatory material → prompt function (D28 adapter) | — |
| Attempt policy | One attempt per task (M8, P1) | OD-8 retries | — | — | — |
| Timeout / resources | Client 120 s | OD-7 | Host capacity | — | — |
| Candidate patch contract | `_extract_patch` (EXISTING) | — | — | Pilot harness (PB-1) | — |
| Demonstrating equivalence | SM11 at verdict level (RD-2b = V: verifier and classifier identity plus proposer configuration) | Identity-matching mechanism | — | Config manifest hashed into evidence | — |
| What counts as pilot data | P1 §17 measurements (raw counts) | RD-0 (whether p0 is added) | — | — | — |
| Explicitly not confirmatory | D31 decision 10; P1 §2, §24 | — | — | — | — |
| Use of p0 for δ and power | SM8, SM10 (95% CP interval) | RD-0 | Pilot result | Power tool (I-4) | S-R3 |
| Harness / execution | Not authorized | **OD-4 (PB-1)** | Stage-0 EXT facts | Pilot harness + generation script | — |

## 4. δ / power dependency chain

| Arrow | Why | Frozen? |
|---|---|---|
| pilot → pilot base rate | Only nuisance source for p0 (SM10) | Chain frozen by SRC; **the pilot's ability to produce p0 is blocked by C-1** |
| base rate → 95% CP interval | γ_pilot = 0.05 (SRC) | Frozen |
| interval → δ / MCID | D31 decision 8 (δ after the base rate) | Frozen order; value open (RD-4) |
| δ → Δ_true | Δ_true must exceed δ for a powered design | Order frozen (SRC chain); value open (RD-5) |
| Δ_true → planning discordance | ψ_plan uses p2 = p0 + Δ_true (SM7) | Formula frozen; scenario open (RD-6) |
| discordance → power_plan(n) | min over p0 ∈ CI of ExactPower (Q2) | Frozen |
| power_plan → n_conf | Option B: smallest n with power_plan(m) ≥ 0.80 for all m ∈ [n, N_avail] (Q2) | Frozen |
| n_conf ↔ N_avail | VOID iff power_plan(N_avail) < 0.80 (D31 decision 9) | Frozen rule; N_avail open (RD-3) |
| N_avail → admission decision | Admission → VM → n_admitted ≥ n_conf, or VOID before execution (I-2, Q1) | Frozen rule |
| admission → confirmatory evaluation | Seal first; n_analyzed = n_admitted; completed-sweep invariant | Frozen; needs the production verifier (BC-1/BC-2) and the successor implementation |

## 5. N_avail evidence requirements

1. **Corpus identity.** A real corpus from a pinned dataset revision (P1 uses SWE-bench Verified `78f471bf…`). Every task's identity is SHA-256(material). Material must follow D28 D-2 and **must not** contain gold, test or protected-surface data.
2. **Held-out partition.** An M4 partition spec, with the partition manifest hash = `manifest_hash`, part of M8 identity v2.
3. **Pilot exclusions.** Registry keyed by `instance_id` **and** identity (P1 §10), frozen before partitioning or sealing. Enforcement is procedural today (a class-C future amendment).
4. **Identity / version.** Dataset revision, material → identity rule, partition manifest hash, and corpus loader version, all recorded.
5. **TaskSpec transport (D28).** `CorpusTask.handle` → content-addressed TaskSpec registry → digest, recomputed at read, adapter and verifier. The TaskSpec schema is still undecided (D26 `:524`; BC-2).
6. **VerificationManifest.** VM(Π) over the **admitted** held-out population. `verification_manifest_hash` enters the M8 identity and the successor pre-registration (D29). Construction fails closed.
7. **Content addressing and sealing.** Held-out partition minus exclusions gives N_avail, recorded as a count bound to `manifest_hash` and the registry hash. After admission, n_admitted and the VM are fixed. Then the power check. Then sealing.
8. **Before entering the pre-registration:** the real corpus exists; the partition is frozen; the exclusion registry is frozen; the D26/D28 TaskSpec schema and registry exist; admission has run through the production verifier (D26/D27). **No number can be stated today.**

## 6. Successor specification readiness checklist

Every item below is **SUCCESSOR-SPEC REQUIRED** as well. The columns show whether each item is already frozen, needs an RD or engineering decision, or is not yet resolved.

| Item | Frozen | RD decision | Engineering decision | Not yet resolved |
|---|---|---|---|---|
| Primary estimand A-iv | ✔ D31 decision 6 | | | |
| Cells A0@0, A2@K | ✔ S-R1 | | | |
| A1 isolation / seal | ✔ D31 decision 11, S-R1 | RD-9 (whether A1 is collected) | | |
| Completed-sweep invariant | ✔ Q1 | | | |
| n_cc = n_admitted; no MCAR | ✔ Q1 | | | |
| Run-level global-incomplete VOID | ✔ D31 decision 9, Q1 | | | |
| Retained VOIDs (n = 0, empty VM) | ✔ D31 decision 9 | | | |
| Certified B-ii test | ✔ SM1–SM5 | | | |
| power_plan (Option B) | ✔ Q2 | | Computation cost (I-4) | |
| n_conf definition | ✔ Q2 | | | |
| Pre-execution admission rule | ✔ Q1/Q4 | | | |
| n_analyzed = n_admitted; no truncation | ✔ Q4 | | | |
| Optional outcome-blind over-enrollment | ✔ Q4 | RD-8 | | |
| VerificationManifest binding | ✔ D29 | | | |
| Sealing order: admission → VM → power check → seal → generation | ✔ (I-2, derived) | | | |
| Primary-first ordering | ✔ S-R1 | | Record structure (G-A7) | |
| Secondary / GEE isolation (P1–P7 dispositions) | ✔ S-R1 | | G-A7 | |
| Completion verified from records (I-1) | ✔ (derived from Q1) | | G-A7 | |
| Halt vs INFRA_ERROR boundary (I-3) | Endpoint frozen | | M2-PV specification (BC-2) | ✔ |
| Tie authority \|p − α\| ≤ 10⁻⁶ (I-5) | Derived from SM6 (ii) | | | |
| T = 0 enforcement | T frozen | | G-A7 | ✔ |
| Implementation architecture | | ✔ G-A7 | ✔ | ✔ |
| Successor `spec_version` / form | | ✔ G-A8 | | ✔ |
| VM2 supersession (prospective) | ✔ D31 decisions 3–4 | | | |
| Provenance / identity fields: δ, Δ_true, scenario and sensitivity values, γ, ε, η, α, power target, pilot CI and pilot configuration hash, N_avail, n_conf, n_admitted, registry hash, `manifest_hash`, `verification_manifest_hash`, checkpoint schedule, `spec_version` | Structure implied | Values: RD-1 to RD-8 | Schema (G-A7) | ✔ |

## 7. Contradiction check

Sources checked:
- Handbook;
- `DECISIONS.md` / D31;
- M8 identity v2; M9 VM2; M10 code;
- M2-PV-R ratification record; M2-PV handoff; P1 pilot design;
- SRC Q1/Q2/Q4; the integration audit.

**C-1 — CONTRADICTION FOUND.**

**Side 1: the base-rate pilot required by D31 and the SRC chain.**
- D31 decision 8 (`DECISIONS.md`): δ is recorded "after the pilot base rate is obtained".
- The SRC-accepted chain (`c1ced0a2…` item 5): "Pilot observation → p0 two-sided Clopper-Pearson CI → …". The pilot "must use identical confirmatory A0 configurations".

**Side 2: the only designed and ratified pilot.**
- M2-PV-R §9 (`:272–283`, RD-ratified):
  - "exactly 5";
  - purpose "**only** to measure whether the current proposer can produce usable candidate patches";
  - P-3 (`:291`; proposed there, then RD-ratified in the P1 design task and recorded as P1 §6 **[RATIFIED]**): the pilot "cannot estimate a solve rate".
- P1 design §2 **[RATIFIED]**: "not a benchmark, **not a solve-rate estimate**".
- P1 §17: "**Forbidden:** composite scores, rankings, **rates, percentages, confidence intervals**."
- P1 §24 (P-3): "Report raw counts only … **Never a percentage, interval**".
- P1 structure, which is incompatible with the SRC's configuration equivalence:
  - primary endpoint = `patch_applies`, with `PASSED` explicitly "probe-level evidence, not a production-verifier verdict";
  - non-representative selection (fixed anchor, single-file gold, pytest-only, repository exclusions);
  - two material conditions (M-A/M-C), whereas the confirmatory configuration has one material → prompt function, which does not yet exist (D28 adapter).

**Hierarchy.** D31 outranks the RD-ratified research record. So **D31 is not contradicted; it cannot be satisfied by P1 as ratified**. Resolving this requires an RD research amendment or a separate pilot (RD-0). It must not be resolved by the CSE.

**Note.** The prior CSE audits did not test P1 §2, §17 or §24 against the SRC chain. This finding corrects them.

**No other contradiction found.** Items A–G of §1 are TRUE. The integration audit's six integration notes stand.

**Result: CONTRADICTION FOUND — the RD decision package is NOT READY until RD-0 is ruled.**

**Update 2026-09-29.** RD-0 is ruled (B). The proposed amendment's own audit (amendment §6) finds **no new contradiction**. C-1 is **resolved upon ratification** of the amendment.

## 8. Critical-path order (gates kept separate)

**A. RD decisions, in order:**
1. **RD-0**: ruled (B); **ratify the amendment**.
2. ~~RD-2b~~ **CLOSED (Option V)**. Next: P1 OD-1 to OD-12 (feasibility pilot only; P1 precedes production-verifier automation, BC-1); then RD-1 and RD-2 for the BRP, once the real corpus and population definition exist.
3. G-A8.
4. RD-9, RD-6, RD-6b (independent; any time).
5. After the pilot: RD-4, then RD-5.
6. After the real corpus: RD-3, RD-8.
7. S-R3.
8. G-A7 (after the successor specification freeze).

**B. Evidence the CSE must gather (each needs its own authorization where it touches the execution host):**
- Stage-0 EXT facts: image digests, model weights digest, server version, effective `num_ctx`;
- confirmatory-population eligibility rules;
- corpus / partition / exclusion evidence for N_avail;
- admission failure-rate evidence;
- a feasibility estimate for the power computation (I-4).

**C. SRC:**
- none for the framework;
- S-R3 only, if retained;
- no review of RD-0 is needed unless the RD's chosen arrangement changes a statistical quantity.

**D. Successor specification drafting:** after G-A8, using the §6 checklist. It can proceed in parallel with the pilot decisions, and parameters stay unset.

**E. Implementation:**
- pilot harness (PB-1/OD-4);
- M4 real-dataset adapter;
- D28 registry and adapter;
- production verifier (BC-1/BC-2);
- successor analysis layer;
- power tool.

**F. Separate authorizations:**
- the RD-0 amendment record;
- pilot harness implementation;
- Stage-0 inventory;
- pilot execution;
- successor specification freeze;
- successor implementation handoff;
- production-verifier specification freeze;
- confirmatory evaluation.
