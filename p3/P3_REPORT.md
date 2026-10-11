# M2-PV-P3 report and evidence audit: generator capability probe

**Date:** 2026-10-11.
**Spec:** `p3/P3_SPEC.md`, including A-1.
**Harness:** `p3_run.py` `69adad6c`, `p3_extract.py` `8a27dcc8`.
**Population:** the P2 PILOT_SET `44b88412` (13 frozen tasks; frozen U prompts byte-identical).
**Generator:** `claude-opus-5-5`, `max_tokens` 1024, no temperature (A-1), one generation per task.

**Status of this report:** the read-only audit is complete. The independent Docker reproduction of all 6 passes is complete: **6/6 reproduced exactly** (§4). The extractor diagnostic is complete: P3-01 and P3-10 both **PASSED** when the diff is left un-stripped.

## 1. Result (pre-declared rule, §4 of the spec)

| | |
|---|---|
| n / n_v | 13 / 13 (0 unresolved infrastructure failures, 0 D7 aborts) |
| PATCH_APPLIES | 6 |
| **VERIFIED_PASS (k)** | **6** (P3-04, -05, -07, -08, -09, -11) |
| **Decision** | **P3-A** (k ≥ 3) |

## 2. Audit (`p3/checks/audit_p3.py`, read-only): 0 evidence defects

| Check | Result |
|---|---|
| Frozen inputs | P2 PILOT_SET `44b88412`; P2 code and spec equal the PILOT_SET values; Velith `proposer.py` equals the pin `91d32296` (Velith HEAD `6ca531f5`) |
| Provenance (13/13) | MANIFEST complete and correct (17–18 files per episode). Each episode is bound to the PILOT_SET and produced by `p3_run.py` `69adad6c`. Prompt SHA equals the frozen `identity.U`. Image identity matches; image removed. |
| Requests (13/13) | Exactly `{model: claude-opus-5-5, max_tokens: 1024, one user message}`. No temperature, system prompt or tools. Exactly one consumed attempt per task. |
| Response chain (13/13) | `response_raw.json` → `completion.txt` → `result.json` → `episode.json` agree on model, message ID, `stop_reason` (all `end_turn`, no truncation) and text |
| Extraction (13/13) | Re-running the pinned `_extract_patch` source reproduces every `patch.diff` and `has_patch` |
| Gate (13/13) | Gated-patch SHA equals the extracted patch; test-patch SHA and protected paths equal the spec; no patch touches protected test files |
| Verification (6 passes) | Every FAIL_TO_PASS and PASS_TO_PASS test is `passed` (P3-04 4/4 + 21/21; -05 1/1 + 2/2; -07 1/1 + 39/39; -08 2/2 + 958/958; -09 1/1 + 8/8; -11 1/1 + 66/66). Baseline healthy (RAN). Network `none` and blocked. Nothing removed, no tampering. |
| Local replay (13/13) | `git apply --check` against the gold files in the prompt agrees with the probe gate 13/13 |
| A-1 | The HTTP 400 (`temperature`) rejection is preserved in `P3-01/G/fatal-1-1791698138.json` and **not** counted as an attempt |
| Decision | k = 6, applies = 6, n_v = 13 → P3-A; identical to `_report/report.json` |

## 3. The 7 non-passing tasks: all MALFORMED_PATCH ("corrupt patch")

None are infrastructure failures, empty responses, truncations or apply-then-fail cases.

| Slot | Cause (directly observed) |
|---|---|
| **P3-01, P3-10** | **Velith extractor false negative** (§5, F-1). The model's fenced diff applies as written. Velith's `_extract_patch` `.strip()` deleted its final whitespace-only context line, so `git apply` reports it as corrupt. Both diffs' changed lines are **identical to the gold patch**. |
| P3-02, P3-03, P3-06, P3-12, P3-13 | **Model hunk-header errors.** The line counts in the `@@` headers don't match the hunk bodies. All five apply with `git apply --recount` (exploratory only). P3-12's changed lines are identical to gold, but its header says `-973,8` where gold says `-973,7`. |

Exploratory, outside the endpoints: all **13/13** P3 patches are mechanically applicable once the hunk counts are recounted.

## 4. Independent reproduction (2026-10-11, WSL + Docker; no API calls, no regeneration)

**Method.** `p3/checks/reproduce_p3.py passes` was run on the **recorded** `patch.diff` of each pass:
1. Re-pull the image by digest and check its identity.
2. Re-run the frozen probe gate in fresh containers.
3. Compare the classification, the patch SHA and **every per-test outcome** with the original run.

Output is in `p3/evidence/_repro/<slot>/passes/`; the original evidence is untouched.

**Results (6/6 reproduced exactly, 0 outcome differences):**

| Slot | Re-run classification | Required tests | Same classification, same patch, 0 outcome diffs |
|---|---|---|---|
| P3-04 | PASSED | 25/25 | yes |
| P3-05 | PASSED | 3/3 | yes |
| P3-07 | PASSED | 40/40 | yes |
| P3-08 | PASSED | 960/960 | yes |
| P3-09 | PASSED | 9/9 | yes |
| P3-11 | PASSED | 67/67 | yes |

**Extractor diagnostic (`extractor-fn`; DIAGNOSTIC ONLY, never an endpoint).** This re-runs the model's fenced diff *before* `.strip()`.
- **P3-01:** gate pass, **PASSED 15/15**. The extractor defect turned a fully verified fix into "corrupt patch".
- **P3-10:** gate pass, **PASSED 10/10**.
- **Net effect of F-1 on P3:** 2 verified fixes recorded as failures. With a correct extractor the count would be **8/13 instead of 6/13** (diagnostic; the frozen result stays 6/13, P3-A).

## 5. Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| **F-1** | **HIGH (Velith main)** | **`_extract_patch` corrupts correct diffs.** `candidate = "\n".join(lines).strip()` deletes trailing whitespace-only lines, which are valid blank context lines in a unified diff. That makes the hunk one line short, so a correct patch is reported as corrupt. | Velith `src/velith/agent/proposer.py` line 78 (fenced path; the unfenced path at line 81 has the same `.strip()`). Genuine false negatives: **exactly three — P2-11 (U arm), P3-01, P3-10** (3/31 across the pilots); for each, the un-stripped diff applies against the gold file (local replay). *Erratum (2026-10-11):* an earlier version of this row also listed P1-T1. P1-T1 is **not** an F-1 case: its stripped line was surplus beyond its hunk's own count, its patch fails for an unrelated content reason (the model omitted four import lines of the source), and it is an unchanged guard case under the fix. **Fixed in Velith commit `29fd12ffb289defd3a490e6d7c5f16151aa856b7`, governed by DECISIONS.md D32** (frozen pilot results unchanged). **On the real gate, the un-stripped diffs pass every required test: P3-01 15/15, P3-10 10/10 (§4).** The bug converts verified fixes into recorded failures. |
| **F-2** | **HIGH (validity)** | **Benchmark contamination is directly evidenced.** In 7/13 episodes the changed lines are **verbatim identical** to the upstream gold patch (P3-01, -04, -05, -08, -09, -10, -12), including 4 of the 6 passes. P3-08 reproduces the gold comment, with the upstream issue number "GH4074", which **does not appear anywhere in the prompt**. | `audit_p3.py` gold-similarity column; `grep -c 4074 p2/evidence/P2-08/P/prompt_U.txt` = 0 |
| D-1 | LOW (protocol) | The spec's "no extended thinking" (D3) was not enforced by the request. The model emitted 363 thinking tokens on P3-10 (content redacted). | `P3-10/G/attempt-1/response_raw.json`. P3-10 is a failure, so the decision is unaffected. |
| D-2 | LOW (P2 erratum candidate) | Through F-1, P2-11's U arm was a false negative. Rescoring it (exploratory) would make the P2 table both 1 / S-only 3 / U-only 3 / neither 6: still P2-B, and VERIFIED unknown. The frozen P2 result is not changed. | `audit_p3.py` / local replay |

## 6. What the evidence supports, and what it doesn't

1. **Directly observed:**
   - 6/13 verified under the frozen gate.
   - 7/13 failures were diff-format failures: 2 caused by Velith's extractor, 5 by the model.
   - 7/13 diffs are verbatim gold reproductions.
2. **Independently reproduced:**
   - Extraction (13/13), local apply (13/13) and endpoint derivation (13/13) were re-derived from raw evidence.
   - **All 6 passes were re-run in fresh containers with identical per-test outcomes (§4).**
   - The extractor false negatives were confirmed on the real gate for P3-01 and P3-10.
3. **Supported interpretation:**
   - P3-A holds as defined. With this generator, the floor is lifted *on this public benchmark*.
   - **On this task set, the success is substantially confounded by memorization.** Only P3-07 and P3-11 passed with solutions clearly different from gold (similarity 0.46 and 0.25).
4. **Unresolved:**
   - How much genuine repair capability remains on uncontaminated tasks.
   - How much of the P2 → P3 change is due to model size or quality versus the decoding change (temperature 0 → default) versus memorization.
5. **Not justified:**
   - Any claim about autonomous software repair, production readiness, or generalization beyond these 13 public tasks.
   - Attributing the 0 → 6 change to "model capability" alone.
   - Using SWE-bench Verified as the Stage-1 substrate with this generator. Memorized solutions would make "compounding from verified experience" unmeasurable.

## 7. P2 → P3

| | P2 U (DeepSeek-Coder-V2-Lite 16B, local, temperature 0) | P3 (Opus 5.5, API, default sampling) |
|---|---|---|
| Applies | 3/13 | 6/13 |
| Verified | 0/13 | **6/13** |
| Corrupt or malformed diffs | 5 | 7 (2 of them caused by the extractor) |
| Verbatim gold reproduction | 0/13 | 7/13 |

Two things changed at once: the model and the decoding setting (A-1). Memorization is a third confound that is present only in P3.
