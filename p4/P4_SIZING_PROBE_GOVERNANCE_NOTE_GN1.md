# P4 sizing probe: governance interpretation note GN-1

**Status:** RD-authorized draft (2026-10-16). It is an interpretation of existing frozen material. It **does not modify** the frozen protocol, its marked block, the probe code, the lock, or the Act-A freeze record. It **authorizes nothing**: Act B and Act C remain unauthorized.

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

## Interpretations

1. **EXACT is protocol completion only.**
   - EXACT means that semantic calibration S0 passed, every final partition was enumerated, and checks C0–C6 passed within their stated tolerances (frozen block §4.9).
   - It does **not** establish that GitHub's search index is complete, or that it exposes every qualifying repository.
   - It does **not** establish that the counts are error-free.

2. **What M_v bounds, and in which direction.** Two reference quantities apply, and both statements hold:
   - **(a) Frozen §3 (unchanged):** M_v counts search-visible repositories returned during the probe window W, excluding run 1's 999 baseline ids. With respect to that union estimand, every reported id was really returned, so an INCOMPLETE M_v,LB is a **lower bound**.
   - **(b) This note:** with respect to repositories that could become eligible or admitted held-out units under the same frozen query, an EXACT M_v is an **upper bound**. Such repositories must first be visible under the query during W, and must then pass the filters (U1–U4), candidate detection and admission, all of which only remove repositories.
   - **M_v is not an estimate of eligible repositories, candidate tasks or admitted tasks.**
   - It says nothing about repositories outside the frozen query (for example, fewer than 1,000 stars), or about repositories that become visible only after W.

3. **M_v ≥ 500 (on EXACT) permits proposing census v2 and nothing more.**
   - It does **not** establish Stage-1 sufficiency.
   - It does **not** authorize census v2. Census v2 requires its own frozen protocol, SRC review and an RD freeze.
   - Under DU-1 (Cap 1), the result means only that at most M_v additional repositories are visible. How many of them would yield admitted held-out tasks is unknown, and is what census v2 would measure.

4. **The M_v ≤ 62 STOP rule is a prespecified governance threshold, not a statistical-power result.**
   - Its basis is arithmetic under the cap-4 definition, at a policy-chosen 25% materiality level against run 1's 996 capped candidates and 320 candidate-bearing repositories (frozen §5; Act-A record).
   - Context only (the rule is unchanged): under Cap 1, added candidate-bearing repositories ≤ M_v ≤ 62, which is less than 25% of the 260-repository Cap-1 baseline after excluding P4.

5. **Cap 1 gives repository-level separation, not proven statistical independence.**
   - D31 item 7 keeps the held-out *task* as the statistical unit. DU-1 is a sampling rule, not an amendment of D31.
   - **Unresolved eligibility and design risks** (none is measured or resolved by the probe):
     - **cross-repository dependence:** shared upstream libraries, forks or near-forks, common organizations, maintainers or tooling, and correlated A0/A2 outcomes across repositories;
     - **leakage:** cross-repository near-duplicate fixes or vendored code; and, under DE-1/DE-2, overlap between pre-B experience sources and held-out repositories. This overlap is unverified, because the pre-B source isn't chosen yet.

6. **P4 exclusions.**
   - P4 pilot tasks and P4 repositories are excluded from the confirmatory held-out pool (DE-4).
   - P4 pilot information never enters any arm's memory (D31 item 10, frozen).
   - **Condition:** P4 can't contribute to M_v only because P4's frame is drawn entirely from run 1's 320 candidate repositories, all of which lie in the baseline B0.
   - That condition is **not yet established**: P4's source decision is still open, and `P4_SPEC.md` v0.2 still names SWE-bench-Live (B-1).
   - If P4 is drawn, in whole or in part, from any other pool, this interpretation and the exclusion accounting must be redone before any M_v-based decision.

7. **INCOMPLETE never supports a census-v2 proposal**, regardless of its lower bound (G-6, settled in the Act-A record). Any exception requires a separate governance decision.

## Assumptions and open items recorded

- DU-1 is **provisional**.
- The pre-B experience source (DE-2) is not selected, so any held-out repositories lost to repository-disjointness are uncounted.
- The probe can't see two pools, which would need separately reviewed protocols:
  - the 269 run-1 repositories that passed the filters but had no candidates, over a later window;
  - repositories below 1,000 stars.
- `total_count` semantics and real GitHub range semantics are unverified until a live run's S0 and C2 checks.
