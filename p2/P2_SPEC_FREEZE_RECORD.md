# P2 specification freeze record (FG-0)

**Date:** 2026-10-03.
**Frozen document:** `p2/P2_SPEC.md`, SHA-256 `b2d29c5cdfba65b24c514763412c0807704c88f52d39e663f3fc6cc7a6d21c32`.
**Review history (retained, not authoritative):** `p2/P2_DESIGN_DRAFT.md`, SHA-256 `79f6f0bd627a20b95ea7629c292cc664aa00a8e096000dd0e745c7413cd1c27f`.
**Scope of this freeze:** the specification only. Nothing of the following exists:
- harness code;
- a lottery computation;
- an image pull;
- a real-task run;
- a model output.

P1 is unmodified.

## 1. Ratification chain

| Step | Source | Result |
|---|---|---|
| 1 | P1 final report (`1476af0c…`, commit `fdbe91a`) | C1 under M-C. Motivates P2. |
| 2 | SRC review 1 (Gemini), on D1–D12 | ACCEPT WITH AMENDMENTS |
| 3 | RD | D1–D12 ratified; Amendments A–F mandatory |
| 4 | SRC review 2 (Gemini), on G-1…G-10 | READY FOR RD FREEZE, conditional on the G-10 amendment |
| 5 | RD | G-1, G-3, G-6, G-7, G-8 ratified; G-10 diagnostic-only amendment; seed-wording amendment |
| 6 | SRC G-2 review (Gemini) | ACCEPT, with no required amendments. Five observations are non-blocking and do not modify the specification. |
| 7 | RD freeze instruction (2026-10-03) | G-2 ratified/accepted. G-1, G-3, G-4, G-5, G-6, G-7, G-8, G-9, G-10 and A-1 confirmed ratified. FG-0 closed. |

**Provenance note.** For G-4, G-5, G-9 and A-1, the RD freeze instruction of 2026-10-03 is the written ratification of record. No earlier written ruling on these four items appears in this workspace. They are ratified exactly as specified in `P2_SPEC.md`:
- G-4: 300 s → 900 s, otherwise 1800 s;
- G-5: no backfill, n_min = 10;
- G-9: the P1 per-pull rule, no attempt cap;
- A-1: halt for RD review, with no population effect.

**SRC G-2 non-blocking observations**, recorded only. They introduce no amendment and no change:
1. strict newline behaviour for files without a trailing newline;
2. the PATH no-whitespace constraint;
3. first-line `diff`/`patch`/`udiff`/`python` stripping;
4. matching against original content rather than cascading edits;
5. Stage-X synthesized-diff alignment.

## 2. Governance markers changed at freeze (no rule content changed)

1. The header status became FROZEN SPECIFICATION (FG-0 CLOSED).
2. The `[G-2, PENDING]` markers in §5 and §6 became RATIFIED. The CONTRACT_S text, the COMMON heading and the region-selection rule are unchanged.
3. The `[G-5, PENDING]` markers in §8 and §10, `[G-9, PENDING]` in §12 and `[G-4, PENDING]` in §14 became RATIFIED.
   - §14 "Proposed rule" became "Rule", with the same thresholds.
   - §12 now states the ratified G-9 content in full ("no cap on admission attempts"), exactly as proposed in §20.
4. The A-1 reference in §13 became "RATIFIED as written".
5. §4 gained "Arms: exactly two (U, S). There is no third arm (D10)." This is an explicit statement of the already ratified D10, not a new rule.
6. The §20 status column now shows every item ratified, and "Remaining ambiguity: none".
7. FG-0 is CLOSED; FG-1…FG-8 remain NOT STARTED.

## 3. Consistency audit (automated against `P2_SPEC.md`; all PASS)

| Check | Result |
|---|---|
| No PENDING or OPEN markers remain; every G-1…G-10, A-1, D1–D12 and A–F is ratified | PASS |
| No contradictory rules: n_min = 10 in §8 matches §20; A-1 halting in §13 matches §17; the timeout rule in §14 matches §20; 4 per repository in §10 matches G-1 | PASS |
| No hidden harness repair: exact byte matching; no fuzzy matching, normalization or occurrence selection; the region rule is declared grammar | PASS |
| P1 registry unchanged: SHA-256 `9fc0157b3c21b99a10753cb0075b0b7f990da248b1ecdb2bf8af51b82a4bcd60`, "never modified" | PASS |
| P2 registry rule: initial content is exactly the 11 P1 IDs as the permanent hold-out set; append-once at FG-6 | PASS |
| No third arm: exactly U and S (D10) | PASS |
| No post-hoc eligibility filtering: (g) frozen before the lottery; G-10 self-check non-excluding; the self-check never influences pool, order, walk or substitution | PASS |
| G-10 MUST NOT list complete (all seven items) | PASS |
| No power or equivalence claim: n = 20 is a feasibility sample; sign-test limitations stated | PASS |
| Same unmodified Stage-X gate for U and S (frozen probe `560834d5…`; no arm-specific gate) | PASS |
| COMMON byte-identical across arms; the only intended difference is CONTRACT_arm | PASS |
| Exact matching: 0 → S_SEARCH_NOT_FOUND, 1 → continue, more than 1 → S_SEARCH_AMBIGUOUS | PASS |
| Primary PATCH_APPLIES (U_APPLIES, S_APPLIES); VERIFIED_PASS secondary | PASS |
| Seed wording: controls the seed input; does not eliminate all stochastic variation | PASS |
| No implementation code or lottery computation in the specification | PASS |

## 4. Freeze-gate status at this record

| Gate | Status |
|---|---|
| FG-0 Governance | **CLOSED** |
| FG-1 Registry | NOT STARTED (the P1 registry has been verified unchanged) |
| FG-2 Harness code | NOT STARTED |
| FG-3 Lottery | NOT STARTED |
| FG-4 Phase A | NOT STARTED |
| FG-5 Generation route | NOT STARTED |
| FG-6 PILOT_SET | NOT STARTED |
| FG-7 No-model proof | NOT STARTED |
| FG-8 Commit and review | NOT STARTED |

## 5. Binding statements

1. `P2_SPEC.md` at the SHA above is the frozen P2 specification. It changes only through a new, separately ratified amendment, and it is not optimized further after freeze.
2. The P1 artifacts and Velith main are unchanged.
3. No P2 implementation, lottery, pull, run or generation is authorized by this record. FG-1 onward each require their own step.
