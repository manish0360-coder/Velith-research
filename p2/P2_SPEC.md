# M2-PV-P2: output-contract isolation pilot (SPECIFICATION)

**Status: FROZEN SPECIFICATION (FG-0 CLOSED, 2026-10-03).** Every decision is ratified (§20). The freeze record is `p2/P2_SPEC_FREEZE_RECORD.md`. After freeze, this document changes only through a new, separately ratified amendment.

**This document contains:**
- no implementation;
- no lottery computation;
- no image pull;
- no real-task run;
- no model output.

P1 is permanently frozen and is not modified.

**Date:** 2026-10-03.
**Supersedes:** `p2/P2_DESIGN_DRAFT.md` (candidate, SHA-256 `79f6f0bd…`), which is retained as review history.

**Authority chain:**
- P1 final report `p1/P1_FINAL_REPORT.md` (`1476af0c…`, commit `fdbe91a`): conclusion C1 under M-C.
- SRC review 1 (Gemini): "ACCEPT WITH AMENDMENTS".
- RD ratification of D1–D12 and Amendments A–F.
- SRC review 2 (Gemini) on G-1…G-10: "READY FOR RD FREEZE, conditional on G-10".
- RD ratification of G-1, G-3, G-6, G-7 and G-8; G-10 mandatory amendment; seed-wording amendment.

**Correction recorded.** SRC review 2 described the shared seed as "eliminating stochastic sampling noise". Per the RD wording amendment, this specification claims only that the seed **input** is controlled across the paired arms (§13).

---

## 1. Research question

With the edit-target file supplied identically in the prompt, does replacing model-authored **unified diffs** (arm U) with a **harness-applied exact search/replace representation** (arm S) change how often the model's output passes the same, unmodified patch-application gate?

P2 is a **feasibility / mechanistic pilot** (D11):
- it is not an evaluation of record;
- it is not a powered effectiveness study (Amendment E);
- it does **not** evaluate file localization (D1).

**Origin in P1 evidence:**
- In P1, missing context (T2, T3, T5) and the raw-diff output contract acted together, so their effects can't be separated.
- With the edited file present in the prompt (T1, T4), the patch still failed: T1 had mismatched context lines, T4 a malformed hunk header.

## 2. Estimand

> The within-task effect of switching the model-to-edit contract from raw unified-diff generation (U) to strict harness-applied exact search/replace (S) on **patch applicability**.
>
> It is conditional on the target file(s) being supplied identically in a byte-identical common prompt. It covers the eligible, admitted SWE-bench Verified task population of §9–§10, with the pinned model and generation parameters.

It is summarized by the paired counts `(both, S-only, U-only, neither)`. The inferential target is P(S applies | exactly one arm applies).

## 3. Hypotheses

| ID | Statement |
|---|---|
| H0 | P(S-only \| discordant) ≤ 0.5 |
| **H1 (primary)** | P(S-only \| discordant) > 0.5 |

**H1 is not supported if any of these holds:**
- the exact one-sided sign test gives p ≥ 0.05;
- U-only ≥ S-only;
- both = S-only = U-only = 0.

**A non-significant result is not evidence of equivalence or of no difference** (D5, Amendment E). No claim is made that S will work.

## 4. Two-arm protocol

- **Unit:** the task.
- **Design:** within-task, paired, with two arms.
  - **U:** a raw unified diff, extracted by the frozen Velith `_extract_patch` and applied by the gate.
  - **S:** exact search/replace blocks, resolved and applied by the harness to an in-memory copy of the base file. The harness then synthesizes a unified diff (§6), and that diff is applied by the **same** gate.
- **Generations:** exactly one per (task, arm). No regeneration once a completion exists. Total = 2n.
- **Arms:** exactly two (U, S). There is no third arm (D10).
- **Same in both arms:**
  - the model `velith-p1-deepseek-coder-v2:16b-c16384-np1024` (manifest digest `e196dcd918e4f54307db79c9fada1ff261c564e1df1624e20ae65d1ff0a4c45c`);
  - temperature 0.0, `num_ctx` 16384, `num_predict` 1024 (D8);
  - stops `"\nUser:"` and `"\nAssistant:"`;
  - the generation route (`velith-verifier:m0`, frozen `OllamaClient`);
  - the seed input (D6/G-6);
  - the common prompt (Amendment A);
  - the Stage-X gate.
- **Gate (both arms; Amendment D).**
  - It is the frozen M2 probe (`560834d559fbf1063c7ad33afa675abac59535e45469bc0d9da3e8254f138e1f`), used as an **unmodified** library.
  - In a fresh `--network none` container from the pinned task image, it runs `git apply` on the candidate patch (script exit 92 means not applied). It also runs a baseline container and the tests.
  - The same probe function and the same gate apply to both arms. There is no arm-specific gate.

## 5. Exact prompt construction (Amendment A)

`prompt_arm = COMMON + CONTRACT_arm`. **COMMON is byte-identical across U and S.** The only intended textual difference is `CONTRACT_arm`.

**COMMON** reuses the P1 OD-2 renderer up to and including the instructions heading:
```
You are fixing a bug in the Python repository `{repo}` at a fixed commit.
You cannot run code or see any files other than those shown below.

## Issue
{problem_statement}

## Source files (retrieved automatically from the repository; may be incomplete)
=== FILE: {path} ===
{verbatim base-commit content}
=== END FILE: {path} ===

## Instructions
```
- `{files}` holds the **gold-patch file(s)** only (C-O oracle context, D1), in path order, using the P1 delimiter and separator rules.
- `problem_statement` is verbatim. `hints_text` is never included.
- The heading wording is retained from OD-2 [G-2, RATIFIED].

**CONTRACT_U**: the remainder of the P1 OD-2 template, verbatim:
```
Reply with exactly one fenced ```diff block containing a single unified diff that fixes the issue.
Use git-style paths relative to the repository root, prefixed a/ and b/
(for example: --- a/pkg/module.py and +++ b/pkg/module.py).
Copy unchanged context lines exactly as they appear in the files above.
Do not modify or add test files. Do not include any text outside the diff block.
```

**CONTRACT_S** [G-2, RATIFIED verbatim]:
```
Reply with one or more edit blocks that fix the issue, and nothing else, in exactly this form:
<<<<<<< SEARCH path/relative/to/repository/root.py
exact existing lines, copied character for character from the file above
=======
replacement lines
>>>>>>> REPLACE
Each SEARCH section must match exactly one place in the file. Do not modify or add test files.
```

**Recorded per task:**
- `common_identity` = SHA-256(COMMON in UTF-8);
- `identity_U`, `identity_S` = SHA-256 of each full prompt;
- the exact pre-flight token count of both prompts, using the frozen HF counting rule (+1).

Both prompts must be ≤ B_prompt = 15232 tokens. There is no truncation.

## 6. Exact S grammar and semantics (D2, G-6, G-7)

**Region selection** (mirrors `_extract_patch`) [G-2, RATIFIED]:
- If the completion contains a "```" fence, the region is the content of the **first** fenced block. A first line equal to `diff`, `patch`, `udiff` or `python` (case-insensitive, stripped) is dropped.
- Otherwise the region is the whole completion.
- Leading and trailing whitespace is removed.

This is declared grammar, applied identically to every output. It is not repair.

**Grammar.** The region is one or more blocks, optionally separated by empty lines, with lines split on `\n`. Anything else is `S_MALFORMED_BLOCK`.
```
block        := SEARCH_LINE search_line+ SEP_LINE replace_line* REPLACE_LINE
SEARCH_LINE  := "<<<<<<< SEARCH " PATH        (exactly 7 '<', single spaces)
SEP_LINE     := "======="                     (exactly 7 '=')
REPLACE_LINE := ">>>>>>> REPLACE"             (exactly 7 '>')
PATH         := non-empty, no whitespace, no leading "/" or "a/" or "b/", no ".." component
```
- `search_text` = concatenation of `line + "\n"`. At least one line is required: an empty SEARCH is `S_MALFORMED_BLOCK` (G-6).
- `replace_text` is defined the same way and may be empty, which means a deletion.

**Resolution: exact byte matching (D2).** No fuzzy matching, no normalization, no automatic occurrence selection, no hidden harness repair.
1. PATH must be a tracked regular file at `base_commit` (`100644` or `100755`). Otherwise `S_PATH_INVALID`.
2. Occurrences are counted in the **original** base content (G-6: not sequential), at line-boundary starts only (offset 0, or right after `\n`), overlapping starts included:
   - **0 matches → `S_SEARCH_NOT_FOUND`**;
   - **1 match → continue**;
   - **more than 1 match → `S_SEARCH_AMBIGUOUS`**.
3. Resolved spans within a file must not overlap. Otherwise `S_OVERLAP`.
4. All replacements are applied at once to each file's original content, in span order. Blocks may span several files (G-6).
5. If no content changed, the code is `S_EMPTY_EDIT`, and `S_APPLIES` = false with no gate run (G-6).
6. A missing final newline gets no special handling (G-6). Such a SEARCH can fail as NOT_FOUND, and this is recorded per block.

The first failing block, in output order, determines the code. Every block's status is recorded.

**Diff synthesis (G-7).**
- In a fresh `--network none` container from the pinned task image, the edited contents are written over the working tree and `git diff --no-color --no-ext-diff --` is run on the edited paths, using the image's own pinned git.
- The output is used byte-for-byte as the candidate patch for the gate.
- If the gate rejects a synthesized diff for a model episode, the code is `S_SYNTH_INTEGRITY`. That is a harness failure: stop and report (§17).

**Pre-condition (G-8)** is admissibility (h) in §9: each gold-file blob at `base_commit` must be byte-identical to that file in the image working tree.

## 7. Endpoint definitions (Amendment D, G-3)

**Gate pass.** In the probe candidate run, the `git apply` step succeeded. That means the candidate `status` is not `PATCH_APPLY_FAILED` and the failure didn't happen before the apply step: status ∈ {RAN, TEST_PATCH_FAILED, RESTORE_FAILED}, or VELITH_SURFACE markers are present. This is the frozen P1 `patch_applies` rule.

| Endpoint | Definition | Values |
|---|---|---|
| **PATCH_APPLIES** (primary), recorded per arm as **U_APPLIES** and **S_APPLIES** | — | — |
| **U_APPLIES** | U produced an extractable patch (`Proposal.has_patch`) **and** the gate passed on that patch | true / false / NA |
| **S_APPLIES** | All of these hold:<br>• all blocks parsed;<br>• **every** SEARCH resolved exactly once;<br>• replacements applied without overlap;<br>• the harness generated a non-empty diff;<br>• **the same unmodified Stage-X gate** passed on that diff. | true / false / NA |
| **VERIFIED_PASS** (secondary) | Probe classification = PASSED (`ALL_REQUIRED_PASSED`) for that arm. **Secondary only; it never replaces or adjusts the primary endpoint.** | true / false / NA |

- **false:** a model-attributable failure. That covers NO_OUTPUT, S_* resolution codes, S_EMPTY_EDIT, and a gate rejection (U: MALFORMED_PATCH / PATCH_DOES_NOT_APPLY).
- **NA:** unresolved GEN_INFRA; an infrastructure failure of the candidate container before the apply step after the OD-8 retry; or a D7 task abort.
- **GEN_TRUNCATED** is an explicit recorded state. A truncated completion is still evaluated if it parses (D8).
- **G-3:** PATCH_APPLIES is read **only** from the candidate container's gate step. Baseline health affects only VERIFIED_PASS.
- **G-10:** the gold-derived self-check never enters any endpoint (§13).

## 8. Statistical analysis (D5, Amendment E)

**Analysis set:** valid pairs, where both U_APPLIES and S_APPLIES are non-NA (count n_v). NA tasks are listed separately, with their reasons.

**Mandatory report:**
- `both`, `S-only`, `U-only`, `neither`;
- `discordant` m = S-only + U-only;
- the **exact one-sided p** = P(X ≥ S-only), X ~ Binomial(m, 0.5). If m = 0, report "no discordant pairs; test not computable", and H1 is not supported.
- raw applicability per arm, k_S/n_v and k_U/n_v, as counts and fractions without intervals;
- VERIFIED_PASS counts per arm, as secondary and descriptive only.

**Pre-declared conclusions** (n_min = 10 [G-5, RATIFIED]):

| Code | Condition |
|---|---|
| P2-A | n_v ≥ n_min, S-only > U-only, and p < 0.05: H1 supported, on this population under C-O |
| P2-B | n_v ≥ n_min, at least one arm applies somewhere, and P2-A doesn't hold: no detectable S advantage at this sample size. **Not** equivalence or "no difference". |
| P2-C | n_v ≥ n_min and both = S-only = U-only = 0: neither contract produced an applicable edit with the target file present |
| P2-D | n_v < n_min, or unresolved infrastructure failures (GEN_INFRA, EXEC_INFRA or D7 abort) on ≥ 3 tasks: not interpretable |

**Limitations of the exact paired sign test (Amendment E):**
- It uses only discordant pairs. Concordant tasks carry no information about H1.
- Significance requires at least 5 discordant pairs: m = 5 with all five S-only gives p = 0.03125, and m ≤ 4 can never reach p < 0.05.
- It is one-sided: a U advantage is reported descriptively, not tested.
- Tasks are treated as exchangeable units. Heterogeneity and the repository cap are not modelled.
- There is a single primary test, so no multiplicity adjustment applies.
- **n = 20 is a feasibility sample.** No power claim, no equivalence claim and no effect-size estimate is made.

## 9. Eligibility and admission

**Eligibility** (outcome-blind; computed from the dataset only, before the lottery):
- **(a)–(e)** P1 §7, reused: a `pytest` command; `.py` test-patch files; ≥ 1 PASS_TO_PASS; 1 ≤ |FAIL_TO_PASS| ≤ 5; the gold patch edits exactly one non-test file and no test file.
- **(g)** (D4) The test-ID screen. Exclude the task if any FAIL_TO_PASS or PASS_TO_PASS ID matches `\s`, or has `count("[") != count("]")`. Deterministic, outcome-blind, frozen before the lottery.
- **Repository (G-1):** `pallets/flask`, `matplotlib/matplotlib`, `scikit-learn/scikit-learn`, `astropy/astropy`, `pydata/xarray`. No other repository.
- **Exclusion:** not in `p2/P2_EXCLUSION_REGISTRY.json` (§11).

**Admission** (Phase A; per lottery candidate, in lottery order):

| Step | Action | Effect on admission |
|---|---|---|
| 1 | Pull by pinned linux/amd64 digest and check identity (P1 admission procedure) | fail → inadmissible |
| 2 | Build the OD-5 protected-config spec with the P1 inspection logic, used read-only | fail → inadmissible |
| 3 | Run Case A (gold patch) through the probe. It must give PASSED with every required ID mapped (P1 §9). | fail → inadmissible |
| 4 | **(h) (G-8):** each gold-file blob at `base_commit` is byte-identical to the working-tree file in the image | fail → inadmissible |
| 5 | **(f):** both arm prompts ≤ 15232 tokens; leakage audit PASS on both prompts (P1 frozen definition, RD 2026-10-02) | fail → inadmissible |
| 6 | **Gold-derived S self-check (G-10; DIAGNOSTIC ONLY):** see §13 | **none**: the result is recorded and admission continues |

An inadmissible task is replaced by continuing the lottery walk (§10).

## 10. Lottery (specified; not computed)

- **Pool:** all tasks meeting §9 (a)–(e), (g), the repository rule and the exclusion rule, at dataset revision `78f471bf655a3137b2e8a75af1501690ec009ec3` (D3). The revision is checked before and after the fetch.
- **Order:** SHA-256(instance_id + `"|velith-m2pv-p2-pilot-v1"`) ascending, ties broken by instance_id.
- **Walk:**
  - take candidates in order, skipping any whose repository already has **4** admitted tasks (D3);
  - admit until **n = 20** are admitted or the pool is exhausted;
  - an inadmissible task is replaced by continuing the walk.
- **Repository exhaustion:** no backfill beyond the cap. n may end up below 20, and the shortfall is recorded [G-5, RATIFIED].
- **No replacement** after generation starts.
- **Slots:** `P2-01 … P2-20`, in admission order.
- **The self-check result (G-10) never influences the pool, the order, the walk, or any substitution.**

## 11. Exclusion registry rules (Amendment B)

- `p1/PILOT_EXCLUSION_REGISTRY.json` (SHA-256 `9fc0157b3c21b99a10753cb0075b0b7f990da248b1ecdb2bf8af51b82a4bcd60`) is **never modified**.
- `p2/P2_EXCLUSION_REGISTRY.json` is created at FG-1, before the lottery. Its **initial content is exactly these 11 instance IDs, as the permanent hold-out set inherited from P1**, with their P1 status and a source reference:

| # | instance_id | P1 status |
|---|---|---|
| 1 | `pallets__flask-5014` | admitted (identity `e2671b01…`) |
| 2 | `matplotlib__matplotlib-24970` | admitted (`fe8e73c9…`) |
| 3 | `scikit-learn__scikit-learn-14629` | admitted (`115f516e…`) |
| 4 | `astropy__astropy-7336` | admitted (`4d82ad43…`) |
| 5 | `pydata__xarray-7393` | admitted (`c3109b06…`) |
| 6 | `matplotlib__matplotlib-24570` | rejected at admission (exposed) |
| 7 | `matplotlib__matplotlib-26466` | rejected at admission (exposed) |
| 8 | `matplotlib__matplotlib-26342` | rejected at admission (exposed) |
| 9 | `matplotlib__matplotlib-24149` | rejected at admission (exposed) |
| 10 | `matplotlib__matplotlib-22719` | rejected at admission (exposed) |
| 11 | `pydata__xarray-6721` | rejected at admission (exposed) |

- The lottery pool excludes all 11, and the lottery code asserts this.
- At FG-6 the P2 registry is extended once, append-only, with P2's admitted tasks (with `common_identity`) and the P2 candidates rejected at admission (exposed). The 11 initial entries are never altered or removed.
- Both registries are audit and safety registries. They are not selection rules outside P2.

## 12. Image lifecycle (D7)

- **Phase A:** pull by digest → admit → Stage P → diagnostic S self-check → record the digest and image ID → **delete the image**.
- **Phase B:** re-pull **only by the recorded immutable digest**, then check identity: RepoDigests contain the pinned reference, the platform is linux/amd64, and the image ID equals the Phase-A record.
  - **A digest mismatch or failed identity check aborts that task.** Its pair becomes NA, with no replacement.
- Delete the image again after the task's Stage-X runs.
- **Free-space gate before every pull:** C: free ≥ 2.5 × compressed size + 10 GB (the P1 per-pull rule). No cap on admission attempts: the walk stops at n = 20 or when the pool is exhausted [G-9, RATIFIED].

## 13. Deterministic execution (Amendment C, G-6, G-10)

1. **Phase A** (§9–§12) until n is admitted or the pool is exhausted.
2. **Freeze** (FG-6): `p2/PILOT_SET.json` plus the appended P2 registry.
3. **Phase B**, per task in slot order:
   1. Re-pull and check identity.
   2. **First arm:** `ollama stop`, then confirm `/api/ps` shows no model, then check free RAM ≥ 4 GiB, then generate.
   3. **Unload and reset:** `ollama stop`, then confirm `/api/ps` is empty.
   4. **Second arm**, generated the same way.
   5. Unload.
   6. S resolution and diff synthesis.
   7. Stage X(U), then Stage X(S), each in fresh probe containers.
   8. Delete the image.

**Arm order:** a frozen deterministic schedule in PILOT_SET. U goes first iff the first byte of SHA-256(instance_id + `"|velith-m2pv-p2-arm-order"`) is even.

**Shared seed (G-6; wording amendment):**
- The seed is `derive_task_seed(common_identity, 0)`. It is derived only from the common prompt material, never from arm-specific instruction text, and it is recomputed in-container with the frozen Velith function and asserted.
- This **controls the seed input across the paired arms**. It **does not eliminate all stochastic variation**: outputs may still differ through the instruction text, numerical non-determinism, or server behaviour.

**Cold start per generation.** No KV-cache sharing between arms. The observed `prompt_eval_count` must equal the prediction; otherwise the TOKEN_COUNT_MISMATCH flag is recorded.

**Gold-derived S self-check (G-10 mandatory amendment): DIAGNOSTIC ONLY.**
- **Construction:** exact blocks from the gold patch hunks (SEARCH = old side, REPLACE = new side). They go through the frozen parser, resolver, diff synthesis and the same Stage-X gate.
- **It MUST:**
  - execute in Phase A, before any model generation;
  - record its result deterministically: per-block resolution status (resolved, `S_SEARCH_NOT_FOUND`, `S_SEARCH_AMBIGUOUS`, `S_OVERLAP`), the synthesized diff and its SHA, and the gate result;
  - be preserved in `P2-NN/SELF-S/` evidence and in PILOT_SET provenance;
  - remain available for post-pilot analysis.
- **It MUST NOT:**
  - reject a task;
  - affect eligibility;
  - affect lottery order;
  - cause substitution;
  - affect arm assignment;
  - alter the primary endpoint;
  - alter the final P2 population.
- If the gold-derived representation is ambiguous or cannot resolve exactly, that diagnostic state is recorded and **the task stays admitted**.
- **Harness-integrity note (pilot level, not task level).** Suppose the gold-derived blocks all resolved and the gate still rejects the harness-synthesized diff. That indicates a defect in the harness's synthesis code, not a task property.
  - It is recorded diagnostically.
  - It triggers the §17 harness-integrity stop before freeze, for RD review.
  - It does not remove or replace the task. [A-1, RATIFIED as written: halt for RD review; no effect on the population.]

**Resumable.** Raw output is persisted before interpretation. A completed generation is never repeated.

## 14. Timeout and retry rules

- **Generation:** client timeout 1800 s.
- **Generation retries (OD-8):** at most 1 retry, for infrastructure failures only, where the request was sent but no completion came back. Never after a timeout, out-of-memory or over-budget failure. Failures before the request is sent are not attempts.
- **Stage-X timeout (D12):** frozen per task in PILOT_SET from Phase-A Case-A evidence, before any generation. Rule: 900 s if the Case-A candidate container duration is ≤ 300 s, otherwise 1800 s [G-4, RATIFIED].
- **Stage-X retry:** at most 1 fresh-container retry, on INFRA_ERROR before the gate or on BASELINE_UNHEALTHY. Never after RESOURCE_KILLED or a timeout.
- **Admission:** Case A once per candidate; one retry of a failed pull.

## 15. Failure taxonomy (Amendment F): separately measurable layers

Each (task, arm) records one code per layer reached. The overall code is the first failing layer.

| Layer | Codes | Arm |
|---|---|---|
| **L1 Patch/edit generation** | GEN_INFRA; GEN_TRUNCATED (explicit state); NO_OUTPUT (U: no extractable diff; S: empty region) | both |
| **L2 Structured-edit resolution** | S_MALFORMED_BLOCK, S_PATH_INVALID, S_SEARCH_NOT_FOUND, S_SEARCH_AMBIGUOUS, S_OVERLAP, S_EMPTY_EDIT | S only |
| **L3 Patch application (same gate)** | GATE_PASS; U: MALFORMED_PATCH, PATCH_DOES_NOT_APPLY (P1 definitions, from `git apply` stderr); S: S_SYNTH_INTEGRITY (gate rejected a harness diff → harness stop); PRE_GATE_INFRA | both |
| **L4 Verification** | CANDIDATE_PASSED, CANDIDATE_FAILED, BASELINE_UNHEALTHY, EXEC_INFRA, TIMEOUT, RESOURCE_EXHAUSTED, TEST_INTEGRITY (P1 definitions) | both, only if L3 = GATE_PASS |
| Harness | HARNESS_FAILURE, S_SYNTH_INTEGRITY → stop | — |
| Diagnostic (G-10) | SELF_S_RESOLVED / SELF_S_NOT_FOUND / SELF_S_AMBIGUOUS / SELF_S_OVERLAP / SELF_S_GATE_PASS / SELF_S_GATE_REJECT | recorded only; no endpoint effect |

## 16. Evidence structure

```
p2/
  P2_SPEC.md                      (FG-0)   P2_DESIGN_DRAFT.md (review history)
  P2_EXCLUSION_REGISTRY.json      (FG-1: 11 P1 IDs; append-once at FG-6)
  PILOT_SET.json                  (FG-6)
  harness/                        (FG-2; D9; P1 imported read-only; synthetic-only tests)
  evidence/
    _lottery/      pool.json, order.json, admission_log.json, revision checks
    _gencheck/     container integrity (network none)
    P2-NN/
      A/        pull, inspect, spec, Case-A probe run, (h) check, timeout derivation
      P/        common.txt, prompt_U.txt, prompt_S.txt, material.json, preflight.json, leakage_audit.json
      SELF-S/   gold-derived blocks, resolution.json, synthesized.diff, probe run   (diagnostic only)
      G-U/attempt-n/, G-S/attempt-n/   raw_stdout, raw_stderr, completion.txt, result.json
      S/        region.txt, blocks.json, resolution.json, synthesized.diff
      X-U-n/, X-S-n/                   probe evidence (baseline/candidate, junit, stdout)
      episode.json, MANIFEST.sha256
  P2_REPORT.md                    (after Phase B)
```

Every file is written as bytes (LF), hashed, and listed in a per-directory `MANIFEST.sha256`.

## 17. Stopping rules (no efficacy stopping; fixed n)

**Stop and report** on any of:
- S_SYNTH_INTEGRITY or HARNESS_FAILURE (including the §13 harness-integrity case);
- the harness, parser, template, spec, PILOT_SET or registry SHA changing after freeze;
- the model digest changing, or `context_length` ≠ 16384;
- a systemic leakage-audit failure;
- unresolved infrastructure failures (GEN_INFRA / EXEC_INFRA / D7 abort) on ≥ 3 tasks (→ P2-D);
- the free-space gate failing with no authorized remedy;
- any write to Velith main or to a Velith store;
- a probe network mode other than `none`.

**Task-level abort (pair NA, no replacement):** a D7 identity mismatch after freeze.

## 18. Freeze checklist

The freeze gates FG-0 … FG-8 (below) must pass in order. Nothing generates before FG-8.

## 19. Threats to validity

| ID | Threat | Mitigation / scope |
|---|---|---|
| T-1 | The instruction text differs between CONTRACT_U and CONTRACT_S, so the instruction effect is confounded with the format effect | Byte-identical COMMON; comparable length; token counts recorded; acknowledged |
| T-2 | Oracle context leaks location | No localization or end-to-end claim (D1, D11) |
| T-3 | Filter (f) selects tasks with smaller gold files | Results are scoped to the admitted population |
| T-4 | Pretraining contamination | The primary endpoint is mechanical; VERIFIED_PASS is more exposed; stated |
| T-5 | Exact matching penalizes trivial whitespace slips and the missing-final-newline case | Declared strictness (D2, G-6); per-block codes |
| T-6 | The 1024-token cap may disadvantage S | D8 comparability; GEN_TRUNCATED per arm |
| T-7 | Small n; the sign test uses only discordant pairs | Feasibility framing (§8) |
| T-8 | Single host; temperature-0 reproducibility; a shared seed input does not remove all stochastic variation | Single-attempt evidence; wording per the RD amendment |
| T-9 | Repository cap and exhaustion change composition | Pre-declared walk; n recorded |
| T-10 | Selection bias toward S via self-check filtering | **Removed:** the G-10 self-check is diagnostic only |

## 20. Governance decisions: status

| ID | Decision | Status |
|---|---|---|
| D1–D12, Amendments A–F | As incorporated above | **RATIFIED** (RD) |
| G-1 | Repositories: flask, matplotlib, scikit-learn, astropy, xarray; at most 4 each; n = 20 | **RATIFIED** |
| G-2 | Verbatim CONTRACT_S; keeping the COMMON heading wording; the region-selection rule | **RATIFIED / ACCEPTED** (SRC G-2 review: ACCEPT, no required amendments; RD 2026-10-03). The five SRC observations are recorded as non-blocking, with no change to this specification. |
| G-3 | PATCH_APPLIES read only from the candidate gate step; baseline health affects only VERIFIED_PASS | **RATIFIED** |
| G-4 | Stage-X timeout rule thresholds (≤ 300 s → 900 s, otherwise 1800 s) | **RATIFIED** (RD freeze instruction, 2026-10-03) |
| G-5 | No backfill beyond the cap; n may fall below 20; n_min = 10 | **RATIFIED** (RD freeze instruction, 2026-10-03) |
| G-6 | S semantics: original-content matching, non-empty SEARCH, S_EMPTY_EDIT = false, multi-file blocks, no final-newline special case; seed-input control wording | **RATIFIED**, with the wording amendment |
| G-7 | Diff synthesis using the task image's own git, network none | **RATIFIED** |
| G-8 | Admissibility (h): base blob equals the working-tree file | **RATIFIED** |
| G-9 | Free-space threshold (the P1 per-pull rule); no admission-attempt cap | **RATIFIED** (RD freeze instruction, 2026-10-03) |
| G-10 | Gold-derived S self-check | **RATIFIED with the mandatory amendment: DIAGNOSTIC ONLY** (§13) |
| A-1 | §13 harness-integrity case (gold blocks resolve, yet the gate rejects the synthesized diff): halt before freeze for RD review; recorded diagnostically; no task removed or replaced | **RATIFIED as written** (RD freeze instruction, 2026-10-03) |

**Remaining ambiguity:** none. All governance items are ratified.

---

## Freeze gates (each must PASS, in order; no generation before FG-8)

| Gate | Content | Pass criterion | Status |
|---|---|---|---|
| **FG-0 Governance** | `p2/P2_SPEC.md` with every decision ruled | Every G-item and A-1 ruled; spec SHA-256 recorded in `P2_SPEC_FREEZE_RECORD.md` | **CLOSED** (2026-10-03) |
| **FG-1 Registry** | `p2/P2_EXCLUSION_REGISTRY.json` initialized with exactly the 11 P1 IDs (§11); P1 registry unchanged | 11 entries; P1 registry SHA = `9fc0157b…` | **NOT STARTED**; P1 registry verified unchanged |
| **FG-2 Harness code** | `p2/harness/` with P1 imported read-only: parser, resolver, diff synthesis, lottery, Phase A/B commands, diagnostic self-check. Tests on synthetic inputs only (grammar; 0/1/>1 matches; overlap; empty edit; region rule; synthesis against local git; endpoint mapping; self-check non-influence on population; sign-test arithmetic). | Tests pass; ruff/mypy clean; SHAs recorded; no model or real-task output used | **NOT STARTED** |
| **FG-3 Lottery** | Revision `78f471bf…` checked before and after; pool; ordered list | Revision unchanged; the 11 IDs asserted absent; pool and order hashed | **NOT STARTED** |
| **FG-4 Phase A** | Admission walk (§9–§12): Case A PASSED; (h); both prompts ≤ 15232 tokens; both audits PASS; diagnostic self-check recorded (non-excluding); timeout derived; images deleted after digests are recorded | Every admitted task meets steps 1–5; self-check recorded for every admitted task; n and every rejection logged | **NOT STARTED** |
| **FG-5 Generation route** | `gencheck` in `velith-verifier:m0`, network none | CHECK_OK; module SHAs equal the pinned Velith commit | **NOT STARTED** |
| **FG-6 PILOT_SET** | Tasks; digests and image IDs; spec SHAs; `common_identity`, `identity_U`, `identity_S`; token counts for both arms; seed; arm order; Stage-X timeout; self-check diagnostics; harness/parser/spec SHAs; model and parameters; P2 registry appended | Written once; SHA recorded; runs refuse on any later mismatch | **NOT STARTED** |
| **FG-7 No-model proof** | The Ollama log shows no `/api/generate` request between FG-0 and FG-6 | Last generate timestamp earlier than FG-0 | **NOT STARTED** |
| **FG-8 Commit and review** | One commit of the FG-0…FG-7 artifacts; RD review of the Phase-A evidence | Pushed; RD go for Phase B | **NOT STARTED** |

*End of the P2 specification. No implementation, lottery, image pull, real-task run or model output is authorized by this document.*
