# Adversarial review request for the Scientific Review Council (Gemini): P3 audit

**Your role:** falsify. For each claim below, either show it is wrong (with reasoning or a counter-example) or state what would be needed to accept it. Do not take the CSE's conclusions as given.

## Context (brief)

- **Velith:** an engineering-intelligence system. The program's core experiment, Stage 1, asks whether *verified experience* (propose → verify → log, plus memory) compounds an agent's bug-fixing competence.
- **Pilots:**
  - **P1/P2** (local DeepSeek-Coder-V2-Lite 16B, temperature 0, one generation per task, gold file given in the prompt): 0 verified tasks.
  - **P3:** the same 13 frozen SWE-bench Verified tasks and byte-identical prompts, with `claude-opus-5-5` through the API. `max_tokens` 1024. No temperature, because the API rejected it (amendment A-1, before any generation). One generation per task.
- **Gate:** a frozen container probe. It runs `git apply` on the candidate patch, then applies the upstream test patch, restores protected test files, and runs the FAIL_TO_PASS and PASS_TO_PASS tests with network `none`.
- **Pre-declared rule:** k verified ≥ 3 → P3-A; = 2 → P3-B; ≤ 1 → P3-C; n_v < 10 → P3-D.

## Observed results

| Slot | Instance | Applies | Verified | Changed lines vs gold |
|---|---|---|---|---|
| P3-01 | astropy-12907 | no (corrupt patch) | no | identical |
| P3-02 | sklearn-13496 | no (corrupt) | no | ratio 1.00, 11 vs 10 lines |
| P3-03 | sklearn-25931 | no (corrupt) | no | 0.68 |
| P3-04 | xarray-4966 | yes | **yes** (4/4 F2P, 21/21 P2P) | identical (8 lines) |
| P3-05 | sklearn-14141 | yes | **yes** (1/1, 2/2) | identical (1 line) |
| P3-06 | astropy-13579 | no (corrupt) | no | 1.00, 3 vs 4 lines |
| P3-07 | sklearn-14496 | yes | **yes** (1/1, 39/39) | 0.46 (different fix) |
| P3-08 | xarray-4075 | yes | **yes** (2/2, 958/958) | identical (9 lines, including the comment "GH4074") |
| P3-09 | astropy-14365 | yes | **yes** (1/1, 8/8) | identical (4 lines) |
| P3-10 | astropy-13453 | no (corrupt) | no | identical |
| P3-11 | xarray-3151 | yes | **yes** (1/1, 66/66) | 0.25 (different fix) |
| P3-12 | xarray-7233 | no (corrupt) | no | identical, but hunk header `-973,8` vs gold `-973,7` |
| P3-13 | matplotlib-20859 | no (corrupt) | no | 0.98 |

**k = 6, n_v = 13, so P3-A.**

## Claims to challenge

- **C1. The six passes are valid.** The audit re-derived from raw evidence that:
  - the gated patch equals the extracted patch;
  - all required tests are `passed`;
  - the baseline was healthy;
  - no protected test file was touched;
  - the network was blocked.

  The Docker re-run of the 6 passes is pending. *Is there any way the gate could pass without a real fix?* For example: test selection, the PASS_TO_PASS definition, or the test-patch application order.
- **C2. Velith extractor defect (F-1).** Velith's `_extract_patch` runs:
  ```python
  lines = text[start:end].splitlines()
  if lines and lines[0].strip().lower() in {"diff","patch","udiff","python"}: lines = lines[1:]
  candidate = "\n".join(lines).strip()
  return candidate + "\n"
  ```
  - **Claim:** `.strip()` deletes a final context line consisting of a single space (a blank source line). The hunk is then one line short, and `git apply` reports "corrupt patch".
  - **Observed in exactly three generations:** P3-01, P3-10, P2-11 (U arm). All three apply when only newlines are stripped.
  - **Not an F-1 case (erratum, 2026-10-11):** P1-T1 had a stripped trailing line too, but it was surplus beyond its hunk's own count. Its patch fails for an unrelated content reason (four source import lines are missing from its context), and it is an unchanged guard case under the fix.
  - **Fix landed:** Velith commit `29fd12ffb289defd3a490e6d7c5f16151aa856b7`, governed by DECISIONS.md D32. Frozen pilot results are unchanged.
  - **Real-gate diagnostic:** the un-stripped P3-01 and P3-10 diffs **PASS all required tests** (15/15 and 10/10).
  - **The 6 recorded passes** were re-run in fresh containers: 6/6 identical per-test outcomes.
  - **Is this reasoning correct and complete?** Are there other extractor failure modes?
- **C3. Contamination (F-2).** 7/13 diffs have changed lines verbatim identical to the upstream fix. P3-08 includes the upstream issue number "GH4074", which is absent from the prompt.
  - **Claim:** the P3 success on this set is substantially confounded by memorization, and SWE-bench Verified is not a valid Stage-1 substrate for this generator.
  - **Alternative explanation to rule out:** small fixes are convergent. Is that plausible for 8–9-line verbatim matches that include comments?
- **C4. Attribution.** The P2 → P3 change (0 → 6 verified) cannot be attributed to model capability alone. The model, the decoding setting and the memorization exposure all changed.
- **C5. Proposed next step.**
  1. **First:** fix F-1 in Velith (preserve whitespace-only context lines; strip only surrounding empty lines), with regression tests built from the 3 real cases. Re-score past evidence diagnostically only; the frozen results stay unchanged.
  2. **Then:** a contamination-controlled P4 on tasks created after the generator's training cutoff, before any Stage-1 run.

  **Is this the highest-information next step?** What would you do instead?

## What we do not want

- Agreement for its own sake.
- Speculation presented as fact. Please label assumptions.
