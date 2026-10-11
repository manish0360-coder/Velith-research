# M2-PV-P2 report: output-contract isolation pilot (U unified diff vs S search/replace)

**Date:** 2026-10-11.
**Spec:** `P2_SPEC.md` `b2d29c5c` (FG-0).
**PILOT_SET:** `44b88412…` (FG-6, commit `3b2aa5c`).
**Phase B:** 2026-10-10 12:58–18:24 UTC. 26 generations, one attempt each, 2.7 h of model time.

**Model:** `velith-p1-deepseek-coder-v2:16b-c16384-np1024`, manifest `e196dcd9…`. Digest checked before every call; context 16384 confirmed after every call. Temperature 0, `num_predict` 1024.

**Server:** Ollama **0.40.0** for all 26 calls. P1 used 0.34.4 (see §6).

## 1. Pre-declared result (§8)

| | count |
|---|---|
| n_v (valid pairs) | **13** (no NA, 0 unresolved infrastructure failures) |
| both / S-only / U-only / neither | **1 / 3 / 2 / 7** |
| discordant m | 5 |
| exact one-sided sign test P(X ≥ 3), X ~ Bin(5, ½) | **16/32 = 0.5** |
| k_S / n_v, k_U / n_v | 4/13 (0.31), 3/13 (0.23) |
| VERIFIED_PASS (secondary) | **U 0/13, S 0/13** |
| **Conclusion** | **P2-B**: no detectable S advantage at this sample size (not equivalence) |

Per the pre-registered rule, H1 is not supported. This pilot gives no evidence-based reason to replace Velith's unified-diff contract with S.

## 2. Audit (`p2/checks/audit_phase_b.py`, read-only): 0 defects

- **A. Frozen inputs.** PILOT_SET `44b88412`, registry `7befdc0b`, all 7 code files and the spec equal the PILOT_SET values.
- **B. Completeness, all 13 slots.**
  - Each slot has an `episode.json` bound to the PILOT_SET SHA.
  - Each `MANIFEST.sha256` is complete and correct (48–71 files per slot).
  - Exactly one generation per arm. Seed equals PILOT_SET. Prompt tokens equal the prediction (26/26, no TOKEN_COUNT_MISMATCH). Context confirmed. Unload recorded. Image removed. No `stop.json`.
- **C. Endpoints re-derived from raw evidence.** All 26 arm endpoints and all 26 VERIFIED_PASS values match `episode.json`. The derivation used the U `has_patch` flag and gate status, the S re-parse, the block hashes, `resolution.json`, and the synthesized-diff → gate hash chain.
- **D. Independent local replay** against the gold files embedded verbatim in the prompts:
  - U, `git apply --check`: agrees with the probe gate on 12/12 replayable patches.
  - S, re-parse plus exact resolution: agrees on 6/6. The local `git diff` synthesis is byte-identical on 4/4, ignoring `index` abbreviation length and mode lines.
- **E. Statistics.** Table, p and conclusion recomputed from scratch; identical to `report.json`.

## 3. Failure modes

| Layer | U (13) | S (13) |
|---|---|---|
| L1 no extractable output | 1 (P2-10: hit the 1024-token cap mid-diff, no closing fence) | 0 |
| Format failure | **5 MALFORMED_PATCH** (`corrupt patch` ×4, `fragment without header` ×1) | **7 S_MALFORMED_BLOCK**, all "line 1: expected SEARCH line" |
| Content/context failure | 4 PATCH_DOES_NOT_APPLY (context lines not in file) | 2 S_SEARCH_NOT_FOUND |
| Gate pass | 3 | 4 |
| Of which VERIFIED_PASS | 0 | 0 |

**The 7 "neither" tasks** (P2-04, 05, 07, 09, 10, 11, 13) fail in both arms, for independent format or content reasons:

- **S breaks the "nothing else" instruction.** In all 7 S_MALFORMED cases the model wrote an English explanation before (or instead of) the blocks. Valid-looking blocks follow the prose in 5 of the 7.
- **U writes hunks that git rejects.** Broken hunk structure (4 `corrupt patch`, 1 `fragment without header`), or context lines that don't exist in the file (4).
- **Truncation is a secondary factor.** 4/26 completions hit the 1024-token cap (P2-04 S, P2-09 U, P2-10 U and S).

**Zero verified passes is a capability floor, not a verification defect.** Every one of the 7 gate-passing patches ran the tests (status RAN), and **0 of 9 FAIL_TO_PASS tests passed**:

| Slot / arm | FAIL_TO_PASS | PASS_TO_PASS |
|---|---|---|
| P2-01 U | 0/2 | 6/13 (broke existing behaviour) |
| P2-02 S | 0/1 | 19/19 |
| P2-03 U | 0/1 | 20/21 |
| P2-03 S | 0/1 | 2/21 (broke the module) |
| P2-06 U | 0/1 | 39/40 |
| P2-08 S | 0/2 | 958/958 |
| P2-12 S | 0/1 | 189/189 |

The baselines were healthy and the gold fix passed every Case-A run. The model's edits apply but do not fix the bug. With the gold file supplied in context, this model and configuration solves **0/13** tasks.

## 4. Exploratory (post-hoc, outside the endpoints; for design only)

- **Prose-tolerant S** (extract blocks anywhere in the completion): 2 more S edits would resolve (P2-11, P2-13). P2-01, P2-05 and P2-09 would still miss the search text, and P2-06 would be an empty edit.
- **`git apply --recount` for U:** 1 more patch would apply (P2-11).
- Neither change touches the 0/9 FAIL_TO_PASS result.

## 5. Findings recorded as defects (no endpoint effect)

1. **G-7 mode artefact.**
   - The synthesized S diff for P2-02, and the gold self-check diffs for P2-01, P2-02 and P2-09, contain `old mode 100755 / new mode 100644`.
   - Cause: `edited_tar` (FG-2) writes the file mode recorded by `read_base` from the base-commit tree, while the image's index records 100755 for those files.
   - Effect: `git apply` accepts the mode change, and P2-02 S passed 19/19 PASS_TO_PASS, so neither endpoint is affected.
   - Fix for future pilots: take the mode from the image's index or working tree.
2. **Raw-output overwrite in P2-01.** The first P2-01 run stopped before sending its request (DIGEST_MISMATCH: Ollama had been reset to the wrong model directory). The rerun then wrote its raw output into the same `G-S/attempt-1/` directory, overwriting that attempt's raw stdout. That run's interpretation is preserved in `preflight-fail-2026-10-10T10:40:39Z.json`, and no attempt was consumed.
3. **Phase A defects** (recorded in `P2_PHASE_A_REPORT.md` §4): two infrastructure-caused rejections, and inconsistent handling of transient HTTP 502 errors.

## 6. Threats

- **Ollama 0.40.0 vs 0.34.4.** Within-pair validity is unaffected (same server, digest and context for both arms of every task). P2's U arm is not strictly comparable with P1.
- **Population and scope.** n = 13, below the target of 20 (repository caps; one task lost to infrastructure). Oracle gold-file context only. Results apply to this population and this model.
- **Feasibility sample (§8).** No power, equivalence or effect-size claim.

## 7. Implication for the program

- **P1's blocker is partly resolved.** Applicability went from 0/5 (P1) to 3/13 (U) and 4/13 (S) once the oracle file was in context. The output contract was **not** the dominant problem.
- **The new blocker is model capability:** 0/26 verified passes, 0/9 FAIL_TO_PASS among applied patches.
- **Consequence for the Stage-1 compounding experiment:** at a verified-success rate of 0 there is nothing for A1/A2 memory to compound on. A0, A1 and A2 would all measure 0 (a floor effect). Running Stage 1 with this generator would be uninformative.
