# RD-2b — Does the Base-Rate Design Pilot (BRP) require the production verifier?

**Type:** research / decision preparation only. **No recommendation, no ratification, no implementation, no execution.**
**Author:** Chief Systems Engineer.
**Date:** 2026-09-29.

**Baseline:**
- Velith `5452efc` (clean); `DECISIONS.md` `57e228d6…`.
- RD-0 amendment (proposed, unratified, not modified) `0c049807…`.
- SRC `c1ced0a2…`, `3c0a79bd…`; integration audit `b3038799…`.
- M2 container freeze record `experiments/m2_container_prototype/FREEZE_RECORD.md`.
- P1 design `89f931e0…`; M2-PV-R `84d67088…`; M2-PV handoff `8d193f10…`.

---

## 1. The two interpretations

- **Option V (verdict level):** material → TaskSpec → proposer → candidate → **production verifier (D26) → hash-locked Velith classifier (D27)** → verdict. The BRP waits until the production verifier is available and validated.
- **Option P (proposer level):** an identical proposer-side A0 configuration (weights, identity, prompt function, material, T = 0, seed derivation, `num_ctx`, `num_predict`, attempts, timeouts), with a **non-production probe endpoint**.

## 2. Authority trace

Column key: **Est** = concerns the statistical estimand; **Cfg** = configuration equivalence; **Ver** = verifier authority; **Plan** = constrains a planning-only pilot; **Non-prod** = permits a non-production endpoint.

| Source | Exact requirement | Est | Cfg | Ver | Plan | Non-prod |
|---|---|---|---|---|---|---|
| Handbook Law 15 (`:1164`) | Noetica owns the protocol; "the concrete oracle is domain content" | – | – | ✔ (the oracle is Velith's) | – | Silent |
| Handbook §5.6 (`:777`) | Pre-register "sample size, seeds, minimum effect size, exact contrasts, and metrics" | ✔ | – | – | Indirect | Silent |
| D3 (`DECISIONS.md:95`) | The V0.1 verifier is deterministic, zero model-gap; the verdict is computed by "compile + run hidden tests + static analysis" | ✔ (defines truth) | – | ✔ | – | Silent |
| D6 (`:148`) | H1 is defined on the held-out **pass-rate** | ✔ | – | – | – | Silent |
| D7 / D8 (`:170, :186–190`) | Arms; D8.2 pre-registers "metrics"; D8.4 frozen evaluation | ✔ | – | – | – | Silent |
| D10 (`:216`) | Free-energy framework: no build constraint | – | – | – | – | Not relevant |
| D26 (`:484–524`) | Real-task verification boundary. "Untrusted-side evidence … may support PASSED **only** through the integrity checks the frozen M2-PV specification will define." Undecided: R_b/R_g/R_c, limits, protected-surface policy, TaskSpec schema. | ✔ (conditions for PASSED) | – | ✔ | – | **No**: a PASSED needs the frozen M2-PV checks |
| D27 (`:528–556`) | The real-task verdict is "A interpreted by B" (container evidence plus the hash-locked Velith classifier). The host "is not the scientific source of truth". Cross-machine determinism is a mandatory acceptance requirement that has not yet been demonstrated. | ✔ | – | ✔ | – | **No** for a real-task verdict |
| D28 (`:560–581`), D-3 `:572` | Real-task `Task` instances "use only the production container verifier/orchestrator". D-2: prompt = f(material). | – | ✔ (prompt function) | ✔ | Applies if the BRP builds real-task `Task`s through the adapter | **No**, for `Task`s built that way |
| D31 decision 6 | Δ20 = P(A2 **pass**) − P(A0 **pass**) | ✔ | – | – | – | Silent |
| D31 decision 8 | δ is recorded after "the pilot base rate is obtained" | ✔ | – | – | ✔ | Silent |
| D31 decision 10 | The pilot informs design only; its tasks are excluded | – | – | – | ✔ | Silent |
| M9 VM2 §3.5.1, retained | PASSED = 1, every other verdict 0 | ✔ | – | – | – | Silent |
| M8 identity v2 / D29 | `verification_manifest_hash` binds the verification contract into evaluation identity: differently verified evaluations are different measurements | ✔ | ✔ | ✔ | Evaluations of record only | – |
| M10 code | Consumes verdicts from the evaluation sink | – | – | – | Not the pilot | – |
| M2-PV-R §9 | P1 (feasibility) comes before production-verifier automation; P1 is "only … usable candidate patches" | – | – | – | P1 only | P1 only |
| M2 freeze record (`:3–6, :97–119, :161`) | "feasibility experiment only … not a production specification". Open holes L1–L12, among them L3 (pytest manipulation), L4 (import-path hijack), L5 (hand-picked protected set), L12 (self-reported evidence). "Still unresolved for production." | – | – | ✔ (the probe is not the production verifier) | – | Only as feasibility evidence |
| P1 §17, §26 | Probe PASSED is "probe-level evidence, **not a production-verifier verdict**"; residuals L4, E3, E4 are "acceptable here only because the pilot claims feasibility, not verdict integrity" | ✔ | – | ✔ | P1 | For feasibility only |
| SM7 (SRC `c1ced0a2…` item 4) | ψ_plan = p0(1−p2) + p2(1−p0), with **p2 = p0 + Δ_true** | ✔ (p0 and p2 on one endpoint) | – | – | ✔ | Silent |
| SM8 / SM10 (items 4–5) | "Pilot observation → p0 two-sided CP CI → …"; the planning p0 minimizes power within that interval | ✔ | – | – | ✔ | Silent |
| SM11 (item 5) | "The pilot must use **identical confirmatory A0 configurations**" | – | ✔ | Undefined scope | ✔ | Silent |
| SRC Q1/Q2/Q4 | power_plan is computed over the pilot interval; n_conf; completed-sweep rule | ✔ | – | – | ✔ | Silent |
| M2-PV handoff: BC-1 / BC-2 | Pilot (P1) before production-verifier automation. The production-verifier parameters are undecided and the specification is DRAFT. | – | – | ✔ | – | – |

**No source grants permission for a non-production endpoint to produce a real-task PASSED.** D26, D27 and D28 D-3 restrict it. Silence is not permission.

## 3. What "configuration" in SM11 means

- **SM11 does not define the word.**
- **The quantity SM11 protects is p0 as used by SM7, where p2 = p0 + Δ_true.** Δ_true is the assumed true value of Δ20 = P(A2 pass) − P(A0 pass) (D31 decision 6). So p0 must be P(A0 pass) on the same endpoint, otherwise p0 + Δ_true is not a probability of anything defined.
- **"Pass" for real tasks is a specific measurement.** It is the PASSED verdict (the M9 encoding) produced by D27's source of truth ("A interpreted by B") under D26's integrity conditions.
- **The probe is not that measurement.** The P1 record says so explicitly (§17), and the freeze record declares the probe non-production, with open holes L1–L12.
- **Conclusion:**
  - A configuration that changes the verification instrument changes the random variable p0 refers to.
  - Reading (A), proposer configuration only, keeps SM11 literally satisfiable but breaks SM7's coherence.
  - Reading (B), the complete scientific measurement configuration, is the only reading under which SM7, SM8 and SM10 stay internally consistent.
  - This is a determination from the frozen definitions, not a preference.
  - **It is not stated verbatim anywhere.** SM11's text alone remains ambiguous.

## 4. Random-variable test

- **R_V(t)** = 1{the production verifier (D26 orchestrator with the frozen M2-PV integrity checks) plus the D27 hash-locked classifier returns PASSED for A0's single T = 0 proposal on task t}.
  - **Note:** R_V is **not yet fully defined.** Its components (R_b/R_g/R_c, protected-surface policy, TaskSpec schema) are undecided (D26 `:524`; BC-2).
- **R_P,probe(t)** = 1{the frozen M2 probe (`probe_sha256 560834d5…`) `classify` returns PASSED for the same proposal, under a hand-picked protected set}.
- **R_P,usable(t)** = 1{`patch_applies`} (P1 §17). This is a different event: application, not test success.

**What the frozen records establish:**
- R_P,probe = R_V: **not established.** The records assert the opposite status: the probe is non-production (freeze record; P1 §17), with open holes L3, L4, L12, E3 and E4 by which a candidate can influence the probe's outcome channel.
- A quantified correlation between them: **not established.** No record measures it.
- A comparison **cannot be made** until R_V exists, which requires BC-2 and the production verifier.
- R_P,usable ≠ R_V by definition: different events.

**Substitution.** A correlated proxy is not the nuisance parameter SM7 and SM8 use. The CP interval and the "power-minimizing p0 within the interval" rule protect against **sampling** error in p0 for the same variable. They give **no** protection against **measurement-instrument bias** between R_P and R_V. The frozen machinery contains no term for such bias.

## 5. Power-planning consequence

- **Case V.** p0 = the base rate of the confirmatory endpoint. SM7, SM8, SM10 and Q2 apply exactly as frozen.
- **Case P.** p0 = the base rate of a different endpoint. ExactPower(n; p0, Δ_true, …) would then combine a probe-endpoint p0 with a Δ_true defined on the verifier endpoint.
  - The frozen machinery does **not** define this combination.
  - Making Case P valid needs either an established identity R_P = R_V, which is unavailable, or a **bridging rule** (for example a declared bias bound that widens the planning interval).
  - A bridging rule is new statistical content. It changes the definition of the planning p0 (SM8) and therefore the chain (SM10).

## 6. BC-1 / BC-2 consequence

- **V requires the production verifier.**
  - It does not violate or bypass BC-1: P1 still precedes production-verifier automation.
  - It is compatible with BC-2: the BRP waits for the M2-PV specification freeze and validation.
  - It **delays** the BRP, and so δ, n_conf and sealing, until the production verifier is validated. D27 cross-machine determinism is part of its acceptance matrix; whether the full matrix must be complete before the BRP is unresolved (§H).
- **P allows the probe endpoint.**
  - It does not bypass BC-1 for confirmatory evaluation.
  - It **does** create a **second verification path** feeding a scientific input (p0) into the frozen chain, and it makes the probe a **new scientific instrument**. The freeze record scopes the probe to feasibility.
  - It requires SRC review **and** an amendment of the frozen planning definitions (§5).

## 7. Governance result (classification only; no recommendation)

**Option V**
- **Advantages:**
  - p0 is on the confirmatory random variable;
  - SM7, SM8, SM10, Q2 and SM11 apply literally;
  - consistent with D26, D27 and D28 D-3 and with BC-1/BC-2;
  - no SRC review.
- **Disadvantages:**
  - the BRP, δ, n_conf and sealing wait for the validated production verifier;
  - the BRP consumes production-verifier capacity;
  - BRP tasks must be admitted, and admission failures reduce the BRP's n.
- **Frozen-record compatibility:** full.
- **Unresolved:**
  - the validation extent required before the BRP;
  - how the BRP runs the production path without writing M8 evaluation records (segregated store; engineering);
  - R_V is undefined until BC-2 is frozen.
- **Gates:** M2-PV specification freeze (BC-2) → production-verifier implementation and validation → BRP design freeze → BRP authorization.
- **Classification: A — AUTHORIZED BY CURRENT FROZEN RECORD.** The compatibility is authorized; the BRP itself still needs RD-0 ratification and its own gates.

**Option P**
- **Advantages:** an earlier planning input; lower compute; reuses the frozen probe.
- **Disadvantages:**
  - p0 is on a different random variable;
  - the probe has open holes L1–L12, E3 and E4;
  - it creates a second verifier path and a new scientific instrument;
  - it needs a bridging rule;
  - it reopens the closed framework.
- **Frozen-record compatibility:** SM11 is satisfiable only under reading (A), which breaks SM7's coherence. D28 D-3 applies if real-task `Task`s are built through the adapter.
- **Unresolved:** the bridging rule's form; bias bounds; whether any bound is estimable before R_V exists.
- **Gates:** SRC review → amendment of SM8/SM10 (and the SM11 scope) → RD ratification → BRP design freeze.
- **Classification: C — REQUIRES AMENDMENT TO FROZEN STATISTICAL MACHINERY.** SRC interpretation alone (class B) is not sufficient: even with SM11 read narrowly, SM7 and SM8 define p0 on the confirmatory endpoint.

**Correction to my own draft (not a frozen artifact).** RD-0 amendment clause 4 says a proposer-level choice needs "SRC confirmation of that reading of SM11". This analysis shows that is **necessary but not sufficient**: an SM8/SM10 amendment would also be required. The amendment is not modified here, as instructed. The RD should note this before ratification.

## 8. Critical question

> *"If the BRP uses a probe endpoint that is not proven identical to the production-verifier PASSED endpoint, can its observed p0 legally enter the already-frozen SM10 power-planning chain without changing the statistical framework?"*

**NO.**
- (1) SM7 defines p2 = p0 + Δ_true, with Δ_true on the D31 decision 6 endpoint. p0 must therefore be the base rate of that endpoint.
- (2) The frozen records do not establish R_P = R_V. They record the probe as non-production, with open outcome-channel holes (freeze record; P1 §17, §26; D26; D27).
- (3) SM8's interval-minimization handles sampling uncertainty only, not instrument bias.
- (4) No frozen authority provides a proxy or bridging rule.

Entering a probe-endpoint p0 therefore changes what p0 means, which is a change to the frozen planning machinery.

**No contradiction with the frozen authority hierarchy was found.** SM11's wording is ambiguous, but SM7, SM8 and D31 decision 6 resolve its scope without conflict.

---

## 9. RD RULING (2026-09-29) — RD-2b = OPTION V, CLOSED

- **Decision.** Verdict-level equivalence. The BRP SHALL obtain p0 from the same PASSED endpoint as the eventual Stage-1 analysis: material → TaskSpec → proposer → candidate → production verifier → hash-locked Velith classifier → PASSED / non-PASSED. The M2 probe PASSED and `patch_applies` are not admissible substitutes.
- **Authority.** Research Director ruling, 2026-09-29.
- **RD rationale, as stated by the RD:**
  1. D31 defines the Stage-1 estimand on PASSED.
  2. SM7's p2 = p0 + Δ_true forces a single endpoint.
  3. SM8/SM10 cover sampling uncertainty, not instrument bias.
  4. R_P,probe = R_V is not established, and the records distinguish the probe from the production verifier.
  5. D26/D27/D28 make the production verifier the real-task source of truth.
  6. A probe-derived p0 cannot enter SM10 without reopening the framework.
  7. Reopening SM8/SM10/SM11 to create a proxy rule is **not authorized**.
- **Consequences:**
  - Option P is rejected as the current path.
  - No SRC review is required, because no frozen statistical quantity changes.
  - SM7, SM8, SM10, SM11, D31, P1 and VM2 are unchanged.
- **Current state. Nothing below is claimed to exist:**
  - production verifier: **not complete**;
  - M2-PV specification: **not frozen**;
  - BRP: **not authorized**; BRP implementation and execution: **not authorized**;
  - successor M9/M10 specification: **not frozen**.
