# P4 sizing probe: governance interpretation note GN1-r1 (revision of GN1)

**Status:** RD-authorized revision (2026-10-16).
- It supersedes GN1 for interpretation only. GN1 (`p4/P4_SIZING_PROBE_GOVERNANCE_NOTE_GN1.md`, SHA-256 `8b7c97cd51d9d40c7e1586cb19953bb1a1387c77c7a42bfbe236e7be534ee027`) is kept unchanged.
- It **does not modify** the frozen protocol, its marked block, the probe code, the lock, or the Act-A freeze record.
- It **authorizes nothing**: Act B and Act C remain unauthorized.

**Interprets (unchanged):**

| Artifact | SHA-256 |
|---|---|
| `p4/P4_SIZING_PROBE_PROTOCOL_v0.3.md` | `a34a729de53e47cf021a9cecf886327c39c161252fd862540f6c57e7ded77bb4` |
| Its marked block | `f8a7e398609a70b83a2cad9ad29571aad9ebaecc2d56f8aa3e7502df261a4d8d` |
| `p4/P4_SIZING_PROBE_FREEZE_RECORD_ACT_A.md` | `68b6f301a943c6d73027a0dad410be74cacd30df2db9500a4c0fca1690c23050` |
| `p4/probe/sizing_probe.py` (`FROZEN_PROTOCOL_SHA = None`) | `0b0584cee916455f39554270ef96dd31fd747ae4202ed7a0cfd1f169cddb9925` |

**Context:** RD governance rulings of 2026-10-16:
- DU-1: Cap 1 for the confirmatory held-out sample (provisional);
- DE-1: E-a, repository-disjoint experience;
- DE-2: a verified pre-B experience source preferred, subject to provenance and leakage controls;
- DE-4: P4 pilot tasks and repositories excluded from the confirmatory held-out pool;
- DU-2 and DE-3 deferred;
- no amendment to D31 or the frozen SRC test.

## Changes from GN1

| # | GN1 location | Change |
|---|---|---|
| R1 | Item 2(b) | The EXACT upper-bound statement is qualified: it holds only to within the protocol's completeness tolerances and residual mover risk. It is not an exact upper bound |
| R2 | Item 4 | STOP-POLICY is restated as a governance decision on the **measured** result. The 260-repository Cap-1 baseline is made conditional on the draft P4 frame, and the completeness slack is acknowledged |
| R3 | Item 6 | The P4 source-frame qualification is added: the run-1 frame is only a draft proposal, `P4_SPEC.md` v0.2 names SWE-bench-Live, neither is ratified, and B-1 is unresolved |

Items 1, 3, 5 and 7 are unchanged from GN1.

## Interpretations

1. **EXACT is protocol completion only.**
   - EXACT means that semantic calibration S0 passed, every final partition was enumerated, and checks C0–C6 passed within their stated tolerances (frozen block §4.9).
   - It does **not** establish that GitHub's search index is complete, or that it exposes every qualifying repository.
   - It does **not** establish that the counts are error-free.

2. **What M_v bounds, and in which direction.** One calculation, M_v = |S_W \ B0| (frozen §3; code: `m_lb = len(s_w - set(baseline))`, and `m_v = m_lb` only on EXACT), is read against two reference quantities:
   - **(a) Lower bound (always valid):** every reported id was really returned. So M_v, or M_v,LB on INCOMPLETE, is a lower bound on |U\*_W \ B0|, where U\*_W is the set of repositories that matched the frozen query and were search-visible at some time during W. This is frozen §3's "union estimand".
   - **(b) Upper bound (conditional and approximate, R1):** let V be the repositories that could become eligible or admitted held-out units under the same frozen query, visible during W. Then V ⊆ U\*_W \ B0, so |V| ≤ |U\*_W \ B0|.
     - An EXACT M_v bounds |V| from above **only to within the protocol's completeness tolerances**: per-band slack under C2, up to 9 baseline misses under C4, mover recovery under C5, and the undetected residual movers of frozen §4.5. That is, |V| ≤ M_v + slack.
     - **It is not an exact upper bound.**
   - M_v is not an estimate of eligible repositories, candidate tasks or admitted tasks.
   - It says nothing about repositories outside the frozen query (for example, fewer than 1,000 stars), or about repositories that become visible only after W.

3. **M_v ≥ 500 (on EXACT) permits proposing census v2 and nothing more.**
   - It does **not** establish Stage-1 sufficiency.
   - It does **not** authorize census v2. Census v2 requires its own frozen protocol, SRC review and an RD freeze.
   - This rule uses the lower-bound direction (true pool ≥ M_v ≥ 500), so it is logically valid without completeness. Requiring EXACT (G-6) is stricter.

4. **STOP-POLICY is a governance decision on the measured result (R2).**
   - **The rule (frozen §5, unchanged).** On EXACT with measured M_v ≤ 62, stop expanding the ≥ 1,000-star slice. This prespecified threshold is valid as a policy choice. It is **not** a statistical-power result.
   - **What it does not establish.** A STOP-POLICY outcome does **not** establish that the true additional search-visible pool, or the true additional candidate-bearing pool, is ≤ 62, small, or insufficient. A "≤" conclusion about the true pool does not follow from a lower-bound quantity, and EXACT's tolerances permit undetected misses.
   - **How to read the frozen wording.** Frozen §5's rationale ("the unseen pool cannot add 25% … candidate-bearing repos ≤ M_v ≤ 62") and the code label "STOP-POLICY (cannot add 25% to either baseline under cap-4 maxima)" are to be read as statements about the **measured** unseen pool. For the true pool they hold only to within the completeness slack in item 2(b). The frozen text and code are not changed.
   - **Context only.** If P4's frame is the draft spike-spec proposal (60 of run 1's 320 repositories), the Cap-1 run-1 baseline would be 260. Under that assumption, added candidate-bearing repositories ≤ M_v + completeness slack, compared against 25% of 260 = 65.

5. **Cap 1 gives repository-level separation, not proven statistical independence.**
   - D31 item 7 keeps the held-out *task* as the statistical unit. DU-1 is a sampling rule, not an amendment of D31.
   - **Unresolved eligibility and design risks** (none is measured or resolved by the probe):
     - **cross-repository dependence:** shared upstream libraries, forks or near-forks, common organizations, maintainers or tooling, and correlated A0/A2 outcomes across repositories;
     - **leakage:** cross-repository near-duplicate fixes or vendored code; and, under DE-1/DE-2, overlap between pre-B experience sources and held-out repositories. This overlap is unverified, because the pre-B source isn't chosen yet.

6. **P4 exclusions and source frame (R3).**
   - P4 pilot tasks and P4 repositories are excluded from the confirmatory held-out pool (DE-4).
   - P4 pilot information never enters any arm's memory (D31 item 10, frozen).
   - **Source frame (unresolved):**
     - The 60-repository run-1 frame exists **only as a draft proposal** (`P4_BUILD_SPIKE_SPEC_v0.11.md` §2.2 and §2.4, status DRAFT).
     - `P4_SPEC.md` v0.2 (status DRAFT, not ratified) names a SWE-bench-Live Python snapshot as P4's source (U-3), with "no silent source change".
     - **Neither is ratified. B-1, P4's source decision, is unresolved.**
   - **Condition:** P4 can't contribute to M_v only if P4's frame is drawn entirely from run 1's 320 candidate repositories, all of which lie in the baseline B0.
   - If P4 is drawn, in whole or in part, from any other pool, the exclusion accounting must be redone before any M_v-based decision.

7. **INCOMPLETE never supports a census-v2 proposal**, regardless of its lower bound (G-6, settled in the Act-A record). Any exception requires a separate governance decision.

## Assumptions and open items recorded

- DU-1 is **provisional**.
- **B-1 (P4 source) is unresolved.**
- The pre-B experience source (DE-2) is not selected, so any held-out repositories lost to repository-disjointness are uncounted.
- **Frozen-text imprecision, reported and not changed:**
  - frozen §3 defines S_W operationally but refers to an implicit "union estimand";
  - frozen §5's STOP rationale and the code label state a true-pool bound that holds only for the measured pool.
- The probe can't see two pools, which would need separately reviewed protocols:
  - the 269 run-1 repositories that passed the filters but had no candidates, over a later window;
  - repositories below 1,000 stars.
- `total_count` semantics and real GitHub range semantics are unverified until a live run's S0 and C2 checks.
