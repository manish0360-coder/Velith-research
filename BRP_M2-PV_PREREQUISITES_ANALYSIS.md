# What must be completed in M2-PV before the BRP can run?

**Type:** research / decision preparation. **No parameters chosen, nothing implemented, nothing executed, no statistical review reopened.**
**Author:** Chief Systems Engineer.
**Date:** 2026-09-29.

**Basis:**
- RD-2b = Option V (CLOSED, 2026-09-29).
- RD-0 amendment R1 (proposed, unratified) `98391696…`.
- D26, D27, D28, D29 in `DECISIONS.md` `57e228d6…`.
- M2-PV implementation handoff `8d193f10…` (§§7–21, 25–27).
- M2 freeze record; P1 design `89f931e0…`.
- Velith `5452efc`, clean.

**Current state (not overclaimed):**
- production verifier: **not complete**; no implementation exists;
- M2-PV specification: **DRAFT, not frozen** (BC-2);
- P1: **not executed**; blocked by PB-1 and OD-1 to OD-12;
- BRP: **not authorized**;
- successor M9/M10 specification: **not frozen**.

---

## 0. Governing principle (derived; no new parameter)

Under Option V, p0 is the base rate of **R_V**, the verdict function of the production verifier *as frozen and implemented*.
- For the BRP's p0 and the confirmatory Δ20 to refer to the same random variable (SM7), **every component that can change a verdict — or change which tasks are admitted — must be identical between the BRP and the confirmatory evaluation.**
- **Corollary 1:** every verdict-affecting or admission-affecting M2-PV decision must be **frozen before the BRP runs**.
- **Corollary 2:** the verifier and classifier **implementation identity** (D27 item 7: commit, lock hash, interpreter; D29 item 8: one classifier identity per evaluation of record) must be pinned at the BRP and **reused** by the confirmatory evaluation.
- **Corollary 3:** any post-BRP change to a verdict- or admission-affecting component makes the BRP p0 refer to a different variable. That p0 is then **invalid for SM10**, and the BRP would have to be repeated. This follows from SM7 and the RD-2b ruling; it is not a new rule.

---

## A. M2-PV specification decisions (PV-freeze, BC-2)

| Item | Source | Affects verdict / admission? | Required before the BRP? |
|---|---|---|---|
| R_b, R_g (baseline admission, gold reruns) | D26 `:524`; handoff §12 | Admission | **Yes** |
| R_c (candidate confirmation reruns) | D26; handoff §13, §17 | Verdict | **Yes** |
| Runner mechanics (launcher, `-c`, import mode) | D26; handoff §15 | Verdict (L3, L4) | **Yes** |
| Protected-surface policy | D26; handoff §14 | Verdict | **Yes** |
| Limit values (time, memory, CPU, PIDs, disk, output) | D26 item 4; handoff §19 | Verdict (timeout/OOM gives FAILED or INFRA_ERROR) | **Yes** |
| Non-root / read-only root / hardened runtime | D26 (undecided) | Can affect verdicts (writes, permissions) | **Yes**, decided either way |
| Result-consistency rule and canary design | Handoff §16 (FD-9) | Verdict (inconsistency gives FAILED) | **Yes** |
| Attribution and anti-VOID rules (AV-1 to AV-6) | Handoff §18 | Verdict vs halt | **Yes** |
| Halt vs INFRA_ERROR boundary (integration note I-3) | D19 vs D26.8 | Verdict and sweep completion | **Yes** |
| TaskSpec schema | D26 `:524`; D28 | Defines hidden tests and bundle, hence verdict | **Yes** |
| Evidence-ledger schema (classifier identity, evidence digests) | D29 item 8; handoff §21 | Not the verdict itself, but required to *prove* identity equivalence (Corollary 2) | **Yes**, at least the identity recording |
| The FD items listed for PV-freeze (FD-2/3/4/5/6/7/8/9/12/14/15/16) | Handoff §27 | Mostly verdict or admission | **Yes**, where verdict- or admission-affecting |

**Conclusion A.** The **complete** verdict- and admission-affecting part of the M2-PV specification must be frozen before the BRP. No legitimate subset can be left open, by Corollary 1.

## B. Production-verifier implementation

| Item | Required before the BRP? |
|---|---|
| Host orchestrator (D26 items 1–8), fail-closed | **Yes** |
| D27 hash-locked classifier with self-verified identity | **Yes** |
| D28 real-task adapter, TaskSpec registry, digest recomputation, D-3 static guard | **Yes** |
| Evidence collector and ledger (identity recording) | **Yes** |
| Pinned implementation identity (commit, lock hash, interpreter, image digests) | **Yes** (Corollary 2) |
| Integration with the M8 runner for evaluations of record | **No** for the BRP. The BRP needs a production-verifier execution path that writes **no** M8 evaluation-of-record artifact (D31 decision 10). That path is BRP-specific infrastructure (§D). |

## C. Production-verifier validation

| Item | Source | Required before the BRP? |
|---|---|---|
| Adversarial validation matrix, groups 1–22 | Handoff §26 | **OPEN, RD decision (RD-10).** It is needed for verifier *acceptance* (D27). What the BRP needs is only that the verdict function is **final** (Corollary 3). |
| Cross-machine deterministic classification | D27 (mandatory acceptance requirement, not yet demonstrated) | **Required for the production verifier's acceptance regardless.** For BRP–confirmatory equivalence it is additionally necessary **iff** the BRP and the confirmatory evaluation run on different hosts. Host policy is an RD/engineering decision. |
| Admission (gold) validation on BRP tasks | Handoff §12 | **Yes.** BRP tasks must be admitted through the production path. |

**The RD-10 trade-off (no choice made):**
- **(i) BRP after full acceptance.** p0 cannot be invalidated by validation-driven changes, but the BRP comes later.
- **(ii) BRP after a frozen specification and implementation, before full acceptance.** The BRP comes earlier, but any validation-driven change to a verdict-affecting component invalidates p0 (Corollary 3) and forces a rerun.

## D. BRP-specific infrastructure (can be designed in parallel with A–C; cannot *run* before them)

1. **Real corpus and confirmatory-population definition:** dataset revision, eligibility rules, material rule (D28 D-2).
2. **Confirmatory material → prompt function:** the one the D28 adapter implements. P1's OD-1 evidence (M-A vs M-C) informs its design; P1 itself supplies no p0.
3. **BRP task draw rule** (outcome-blind) and the **exclusion registry** covering P1 and BRP tasks, keyed by `instance_id` and identity.
4. **Proposer identity pinning:** model weights digest, Ollama server version, effective `num_ctx`/`num_predict` (EXT, Stage-0-type inventory); T = 0 enforcement mechanism (G-A7); seed rule (N = 1); attempt policy (one attempt, as M8); timeout.
5. **A segregated BRP execution path and evidence store.** It uses the production verifier, writes no memory, episode, M8-sink or pre-registration artifact, and records verifier, classifier and proposer identity for Corollary 2.
6. **BRP completion rule.** An incomplete BRP sweep must not yield p0. The rule is not frozen; see RD-12.
7. **BRP computation:** p0 = k/n over admitted BRP tasks, and the two-sided 95% CP interval (frozen SM8/SM10).

## E. BRP RD decisions

- **RD-1:** BRP size.
- **RD-2:** BRP scope and draw source (held-out-eligible pool vs available partition, and its effect on N_avail).
- **RD-10 (new):** the validation extent required before the BRP, option (i) or (ii) above.
- **RD-11 (new):** host policy — must the BRP run on the confirmatory host(s), or does cross-machine determinism make the host irrelevant?
- **RD-12 (new):** the BRP completion rule, for example mirroring the confirmatory completed-sweep invariant. This is a design rule for the BRP only and changes no frozen SRC quantity.
- **Authorizations**, each a separate gate: BRP design freeze; BRP implementation; BRP execution; RD-0 amendment ratification.

## F. Successor M9/M10 specification dependencies

- The BRP **does not need** the successor specification frozen in order to run.
- The successor specification **must** reference: the BRP as the sole p0 source (P1 excluded); the RD-2b verdict-level requirement; and the matching of verifier and classifier identity between the BRP and the confirmatory evaluation (Corollary 2).
- **Pre-registration sealing** needs both the BRP result and the frozen successor specification.
- Successor-specification drafting and freeze (G-A8) can proceed in parallel.

## Ordering (derived; no new rule)

P1 (BC-1) → PV-freeze of every item in §A (BC-2) → implementation (§B) → validation to the RD-10 extent (§C) → BRP (with the §D infrastructure ready) → p0 and 95% CP interval → δ (RD-4) → Δ_true (RD-5) → power_plan → n_conf → N_avail adequacy → sealing → confirmatory evaluation.

**Contradiction check:** D26, D27, D28, D29, D31, BC-1/BC-2, SM7–SM11, RD-2b, P1 and M2-PV-R. **No contradiction found.** D27 item 4's refusal rule applies to evaluations of record. The BRP is not one, but Corollary 2 requires the same identity verification for equivalence, so the two are consistent.
