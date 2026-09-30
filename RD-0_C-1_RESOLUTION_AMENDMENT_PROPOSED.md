# RD-0 — C-1 Resolution Amendment (PROPOSED, NOT RATIFIED)

**Type:** research amendment draft, prepared for Research Director ratification. **Not ratified. Not in `DECISIONS.md`. Authorizes no design freeze, implementation or execution.**
**Author:** Chief Systems Engineer.
**Date:** 2026-09-29.
**RD rulings implemented:** RD-0 = **Option (B)** (RD instruction of 2026-09-29); **RD-2b = Option V, verdict-level equivalence** (RD ruling of 2026-09-29).
**Revision R1 (2026-09-29):** clause 4 and every sentence that depended on RD-2b being open are updated to the RD-2b ruling. The prior text (SHA-256 `0c049807…`) is superseded by this draft. It is still **not ratified**.

**Baseline:**
- Velith `5452efc` (clean); D31 in `DECISIONS.md` `57e228d6…`.
- M2-PV-R ratification record `84d67088…`.
- P1 pilot design `89f931e0…`.
- SRC final `c1ced0a2…`, `3c0a79bd…`.
- Integration audit `b3038799…`.
- RD Decision Register (before this amendment) `47b3d957…`.

**Does not modify:**
- D31, D6, D7, D8, D12, D15, D26–D30;
- M8 identity v2; M9 VM2; the M10 code;
- the M2-PV-R record; the P1 pilot design (neither is edited in place);
- any SRC-frozen statistical quantity (SM1–SM11, S-R1, Q1/Q2/Q4).

---

## 1. Problem (C-1, restated)

D31 decision 8 and the SRC-accepted chain need a pilot that yields p0 and a two-sided 95% Clopper–Pearson (CP) interval under the identical confirmatory A0 configuration (SM10, SM11).

The only designed pilot, M2-PV-P1, is RD-ratified as feasibility-only:
- M2-PV-R §9;
- P1 §2 [RATIFIED];
- P1 §6 P-3 [RATIFIED];
- P1 §17: "Forbidden: … rates, percentages, confidence intervals";
- P1 §24: raw counts only.

## 2. Evidence on item 11 — does the base-rate pilot need the production verifier?

This section reports evidence only. **The frozen record does not decide the question.**

**Evidence that p0 must be measured at verdict level, under the confirmatory verification instrument:**

| # | Source | Content |
|---|---|---|
| E-1 | D31 decision 6 | Δ20 = P(A2 **pass** @K) − P(A0 **pass**). "Pass" is the primary endpoint. |
| E-2 | M9 §3.5.1 encoding, retained by the successor | PASSED = 1, every other verdict = 0 |
| E-3 | D27 | For real tasks the scientific source of truth is "A interpreted by B": container evidence plus the **hash-locked Velith classifier** |
| E-4 | D26 trust boundary | Untrusted-side evidence may support PASSED **only** through the integrity checks the frozen M2-PV specification will define. That specification is not frozen (BC-2). |
| E-5 | M2 prototype freeze record (`experiments/m2_container_prototype/FREEZE_RECORD.md:3–6, :161`) | "feasibility experiment only … not a production specification"; "Still unresolved for production: L1–L12" |
| E-6 | P1 §17 | Probe `PASSED` is "probe-level evidence, **not a production-verifier verdict**" |
| E-7 | SM11 (SRC `c1ced0a2…` item 5) | "The pilot must use **identical confirmatory A0 configurations**" |

**Evidence that a proposer/probe-level endpoint might be enough for the planning purpose:**

| # | Source | Content |
|---|---|---|
| E-8 | D31 decision 10 | Pilot information informs **design only**; it never enters confirmatory inference |
| E-9 | SRC Q4 rationale; SM8 | p0 is a **nuisance input to power planning**. A biased p0 degrades planned power; it cannot affect the Type-I control of the confirmatory test. |

**What is not established:**
- SM11 does not say whether "configuration" means only the proposer-level configuration, or also the verification instrument. My earlier planning treated this as RD-2b.
- No frozen artifact states that probe-level PASSED and D27-classifier PASSED coincide. E-5 and E-6 say they are not yet equivalent.

**Consequence for governance:**
- If the RD scopes equivalence to **verdict level**, the base-rate pilot must follow production-verifier availability. That is consistent with BC-1/BC-2 and bypasses nothing.
- The proposer-level branch was analysed in `RD-2b_BRP_VERIFIER_REQUIREMENT_ANALYSIS.md`. It would require amending SM7/SM8/SM10, not only SRC confirmation.
- **Ruled (RD-2b = Option V, 2026-09-29):** the BRP obtains p0 from the confirmatory PASSED endpoint through the production verifier and the hash-locked classifier. Option P is rejected as the current path. No reopening of SM7/SM8/SM10/SM11 is authorized.

## 3. Governance boundary

| | **A. M2-PV-P1 feasibility pilot** | **B. Base-rate design pilot (new)** | **C. Confirmatory Stage-1 evaluation** |
|---|---|---|---|
| Authority | M2-PV-R §9; P1 design (ratified items unchanged) | This amendment, once ratified; D31 decisions 8 and 10; SM8–SM11 | D31; successor specification (not yet frozen) |
| Question | Can the current proposer produce usable patches under the sealed architecture? | What is the zero-experience A0 base rate p0 on the confirmatory population, for planning only? | H0: Δ20 ≤ δ (D31 decision 6) |
| Output | Raw counts only. No rate, percentage or interval. | p0 observation and a two-sided 95% CP interval, used only as SM10 inputs | GO / NO-GO / VOID |
| Endpoint | `patch_applies`; probe-level outcome | **PASSED under the production verifier and the D27 hash-locked classifier** (the same endpoint as C; RD-2b = V). The M2 probe PASSED and `patch_applies` are **not** admissible substitutes. | PASSED under the production verifier (D27) |
| Configuration | Current proposer; M-A/M-C conditions; probe | The confirmatory A0 configuration (SM11) at **verdict level**: proposer configuration, material → prompt function, TaskSpec, production verifier and classifier identity (RD-2b = V) | The confirmatory configuration of record |
| Tasks | 5 tasks, fixed anchor, lottery, filters | Drawn outcome-blind from the confirmatory population definition; size is RD-1 | The admitted held-out population |
| Exclusion | Permanent (P1 §10) | Permanent. Its tasks are excluded from the confirmatory held-out population (D31 decision 10). | — |
| Writes | Evidence outside the repository only | Segregated pilot evidence only. **No** memory or episode writes, **no** M8 evaluation-sink records, **no** pre-registration identities. | Evaluation sink of record; result record |
| Inferential status | None | **None**: design input only; never a confirmatory result; never promoted | Confirmatory |
| Order | Before production-verifier automation (BC-1) | After its prerequisites (§4). **Cannot bypass the production-verifier gate.** | After the production verifier, successor implementation, and sealing |
| May feed | Architecture decisions | δ context, power_plan, n_conf, the adequacy decision | The M10 decision |

**Separation rules:**
1. **P1 data never enters B or C.** No p0 may be derived from P1.
2. **B data never enters C:** no confirmatory estimate, test, gate, memory or evaluation record.
3. **A B result is never relabelled as a Stage-1 result**, whatever its size.
4. **B tasks and P1 tasks are both in the exclusion registry**, keyed by `instance_id` and identity.

## 4. Prerequisites for the base-rate pilot

| Component | Needed to **design** B | Needed to **execute** B | Status today |
|---|---|---|---|
| Real corpus and confirmatory-population definition (eligibility rules, dataset revision) | ✔ | ✔ | Missing: no real corpus or real-dataset adapter |
| Pilot/held-out separation plan: the draw source (held-out-eligible pool vs available partition) and its effect on N_avail | ✔ | ✔ | Missing (RD-2) |
| Material → prompt function (D28 D-2), the one the confirmatory A0 uses | ✔ (frozen definition) | ✔ (implemented) | Missing: no real-task adapter |
| D28 TaskSpec transport and registry | ✔ (required by RD-2b = V) | ✔ | Missing; schema undecided (D26 `:524`, BC-2) |
| Proposer configuration identity (agent, client, prompt function, attempt policy, timeout) | ✔ | ✔ | Partly existing; unpinned |
| Model weights digest | ✔ (to pin) | ✔ | Missing (EXT) |
| Ollama server version | ✔ | ✔ | Missing (EXT) |
| Effective `num_ctx` / `num_predict` | ✔ | ✔ | Server defaults; unknown (EXT) |
| T = 0 enforcement | ✔ (mechanism) | ✔ | T frozen (D31 decision 7); mechanism missing (G-A7) |
| Seed derivation (N = 1) | ✔ | ✔ | Rule open (P1 OD-12 applies to P1 only) |
| Attempt policy (one attempt per task, as M8) | ✔ | ✔ | Frozen for M8; B must match |
| Verifier configuration | ✔ (required by RD-2b = V) | ✔: the D26/D27 production verifier, **validated**. The required extent of validation before the BRP is an open RD decision (see the prerequisites analysis). | **Not complete.** The M2-PV specification is not frozen (BC-2); the implementation does not exist. |
| Probe configuration | Not applicable (Option P rejected) | Not applicable | The probe stays feasibility evidence only |
| Exclusion registry, covering P1 and B | ✔ | ✔ | Proposed (P1 §10, OD-9); not frozen |
| Segregated pilot evidence store (no sink, memory or episode writes) | ✔ | ✔ | Missing (engineering) |
| RD-1 pilot size | ✔ | — | Open |

**Conclusion:** the base-rate pilot **cannot be designed to freeze or executed now**. At minimum it waits for:
- the real corpus and population definition;
- the confirmatory material → prompt function;
- the Stage-0-type EXT facts;
- **the validated production verifier** (RD-2b = V), which itself follows P1 (BC-1), the M2-PV specification freeze (BC-2), implementation and validation.

## 5. Proposed amendment wording (for RD ratification; NOT ratified)

> **RD-0 Amendment — Resolution of C-1 by a distinct base-rate design pilot.**
> *Authority:* Research Director ruling RD-0 = Option (B), 2026-09-29. *Tier:* RD-ratified research record, subordinate to D31. *Supersedes:* nothing. It does not edit M2-PV-R or the M2-PV-P1 design.
>
> 1. **M2-PV-P1 remains the ratified feasibility pilot, unchanged.** Its purpose, raw-count-only reporting, prohibition of rates, percentages and confidence intervals, feasibility/probe endpoint, task selection and exclusions remain exactly as ratified. P1 produces no solve-rate estimate, and **no p0 or other input to D31 decision 8 or the SRC power-planning chain may be derived from P1**.
> 2. **A distinct Base-Rate Design Pilot (BRP) is established.** Its sole statistical purpose is to provide the pilot observation required by D31 decision 8 and the SRC-accepted chain: pilot observation → p0 → two-sided 95% Clopper–Pearson interval (γ_pilot = 0.05) → δ → Δ_true → planning discordance → power_plan(n) → n_conf → N_avail adequacy.
> 3. **The BRP is not a confirmatory evaluation.**
>    - It informs design only (D31 decision 10).
>    - It writes no memory, episode, evaluation-sink or pre-registration artifact.
>    - Its result is never reported or relabelled as a Stage-1 result.
>    - It carries no inferential claim about A0, A1 or A2.
> 4. **Configuration (verdict-level equivalence; RD-2b = Option V).** The BRP SHALL satisfy SM11 at verdict level. It SHALL obtain p0 from the same PASSED endpoint used by the confirmatory Stage-1 analysis, through material → TaskSpec → proposer → candidate → production verifier (D26) → hash-locked Velith classifier (D27) → PASSED / non-PASSED, under the eventual confirmatory A0 configuration: the exact proposer-level configuration, the confirmatory real-task material → prompt function, the TaskSpec transport (D28), and the production-verifier and classifier identity that the confirmatory evaluation will use. Neither the M2 probe PASSED nor `patch_applies` may substitute for this endpoint. The BRP therefore requires the **validated production verifier**, and cannot execute before it exists. No reopening of SM7, SM8, SM10 or SM11 is authorized.
> 5. **Tasks.**
>    - BRP tasks are drawn outcome-blind from the confirmatory population definition.
>    - They are recorded in the content-addressed exclusion registry by `instance_id` and task identity, together with the P1 tasks.
>    - They are excluded from the confirmatory held-out population (D31 decision 10).
>    - The draw source and the size are RD decisions (RD-2, RD-1).
> 6. **Ordering.**
>    - The BRP is designed only after its prerequisites exist: the real corpus and population definition; the confirmatory material → prompt function; the pinned proposer identity, including model weights digest, server version and effective context/generation limits; the T = 0 enforcement mechanism; the seed rule; and the validated production verifier (clause 4).
>    - The BRP does not alter or bypass the ratified ordering "architecture ratification → P1 → production-verifier automation" (BC-1), or BC-2.
>    - Confirmatory evaluation continues to require the production verifier.
> 7. **Unchanged open decisions:** BRP size (RD-1), scope (RD-2), δ (RD-4), Δ_true (RD-5), N_avail (RD-3), discordance scenario (RD-6, RD-6b), admission buffer (RD-8), and the final confirmatory partition.
> 8. **Authorization.** This amendment authorizes no BRP design freeze, no implementation and no execution. Each requires its own RD authorization.

## 6. Contradiction audit of the proposed amendment

| Source | Check | Result |
|---|---|---|
| Handbook v1.1 | Velith content; no new platform mechanism; no layer violation | No conflict |
| DECISIONS / D31 | Decision 8 is satisfied by the BRP (not P1). Decision 10: design-only and excluded. Decision 3: no implementation. D31 is not modified. | No conflict |
| D8.3 held-out lock | BRP and P1 tasks are excluded | No conflict |
| D28 D-3 | If the BRP builds real-task `Task`s through the D28 adapter, those `Task`s may not reach the legacy `VerifierSandbox`. The amendment routes them only to the production verifier (clause 4; RD-2b = V). | No conflict; constraint recorded |
| M2-PV-R §9 | P1 unchanged; "exactly 5" applies to P1 only; sequencing preserved | No conflict |
| P1 design | Not edited; ratified restrictions reaffirmed; no p0 from P1 | No conflict |
| SRC Q1/Q2/Q4; SM1–SM11 | No frozen statistical quantity changed. SM11 is applied at verdict level, which keeps SM7/SM8/SM10 coherent (p0 and Δ_true on one endpoint). | No conflict; no SRC review required |
| CSE integration audit | Integration notes I-1 to I-6 unaffected | No conflict |
| M2-PV architecture ratification (D26/D27) | The production verifier stays the confirmatory instrument; the BRP does not bypass it | No conflict |
| M2-PV implementation handoff | BC-1/BC-2 preserved | No conflict |

**Result: no new contradiction.** C-1 is resolved **once this amendment is ratified**.
