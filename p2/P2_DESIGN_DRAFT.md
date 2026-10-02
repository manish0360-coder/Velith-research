# M2-PV-P2: output-contract isolation pilot (CANDIDATE SPECIFICATION)

**Status: CANDIDATE SPECIFICATION, not frozen.**
- It incorporates the RD ratification of D1–D12 and Amendments A–F, following SRC review "ACCEPT WITH AMENDMENTS" (`reviews/src`, Gemini).
- It contains no implementation.
- The lottery has not been computed.
- P1 is permanently frozen and is not modified.
- Items marked **[G-n]** are the remaining governance decisions (§20).

**Date:** 2026-10-03.

**Basis:**
- P1 final report `p1/P1_FINAL_REPORT.md` (SHA-256 `1476af0c…`, commit `fdbe91a`): conclusion C1 under M-C.
- P1 design `89f931e0…`, P1 harness specification, and the P1 episode records.

---

## 1. Research question

With the edit-target file supplied identically in the prompt, does replacing model-authored **unified diffs** (arm U) with a **harness-applied exact search/replace representation** (arm S) change how often the model's output passes the same, unmodified patch-application gate?

P2 is a **feasibility / mechanistic pilot** (D11):
- it is not an evaluation of record;
- it is not a powered effectiveness study (Amendment E);
- it does not evaluate file localization (D1).

**Origin in P1 evidence:**
- In P1, missing context (T2, T3, T5) and the raw-diff output contract acted together, so their effects can't be separated.
- In the two episodes where the edited file was in the prompt (T1, T4), the patch failed anyway: T1 had mismatched context lines, T4 had a malformed hunk header.

## 2. Estimand

> The within-task effect of switching the model-to-edit contract from raw unified-diff generation (U) to strict harness-applied exact search/replace (S) on **patch applicability**.
>
> It is conditional on the target file(s) being supplied identically in a byte-identical common prompt. It covers the eligible, admitted SWE-bench Verified task population defined in §9–§10, with the pinned model and generation parameters.

It is summarized by the paired counts `(both, S-only, U-only, neither)`. The inferential target is P(S applies | exactly one arm applies).

## 3. Hypotheses

| ID | Statement |
|---|---|
| H0 | P(S-only \| discordant) ≤ 0.5 |
| **H1 (primary)** | P(S-only \| discordant) > 0.5. That is, S yields an applicable edit on more tasks than U, beyond chance among the discordant pairs. |

**H1 is not supported if any of these holds:**
- the exact one-sided sign test gives p ≥ 0.05;
- U-only ≥ S-only;
- both arms fail everywhere (both = S-only = U-only = 0).

**A non-significant result is not evidence of equivalence or of no difference** (D5, Amendment E). This document makes no claim that S will work.

## 4. Two-arm protocol

- **Unit:** the task.
- **Design:** within-task, paired, with two arms:
  - **U:** a raw unified diff, extracted by the frozen Velith `_extract_patch` and applied by the gate;
  - **S:** exact search/replace blocks, resolved and applied by the harness to an in-memory copy of the base file. The harness then synthesizes a unified diff, and that diff is applied by the **same** gate.
- **Generations:** exactly one per (task, arm). No regeneration once a completion exists. Total = 2n.
- **Same in both arms:**
  - the model `velith-p1-deepseek-coder-v2:16b-c16384-np1024` (digest `e196dcd9…c45c`);
  - temperature 0.0, `num_ctx` 16384, `num_predict` 1024 (D8);
  - the same stops;
  - the same generation route (`velith-verifier:m0`, frozen `OllamaClient`);
  - the same seed (D6);
  - the same common prompt (Amendment A);
  - the same Stage-X gate.
- **Gate (both arms).** The frozen M2 probe (`560834d5…`) used as an unmodified library. In a fresh `--network none` container from the pinned image, it applies the candidate with `git apply` (exit 92 means not applied). It also runs a baseline container and the tests.

## 5. Exact prompt construction (Amendment A)

`prompt_arm = COMMON + CONTRACT_arm`. `COMMON` is byte-identical across arms. The only textual difference is `CONTRACT_arm`.

**COMMON**, which reuses the P1 OD-2 renderer up to the instructions heading:
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
- `{files}` holds the **gold-patch file(s)** only (the C-O oracle context), in path order, using the P1 delimiter and separator rules.
- The heading line is kept verbatim from OD-2, even though the files are oracle-selected. This avoids any change to the common text [G-2].
- `problem_statement` is verbatim. `hints_text` is never included.

**CONTRACT_U**: the remainder of the P1 OD-2 template, verbatim:
```
Reply with exactly one fenced ```diff block containing a single unified diff that fixes the issue.
Use git-style paths relative to the repository root, prefixed a/ and b/
(for example: --- a/pkg/module.py and +++ b/pkg/module.py).
Copy unchanged context lines exactly as they appear in the files above.
Do not modify or add test files. Do not include any text outside the diff block.
```

**CONTRACT_S** (proposed verbatim text; [G-2]):
```
Reply with one or more edit blocks that fix the issue, and nothing else, in exactly this form:
<<<<<<< SEARCH path/relative/to/repository/root.py
exact existing lines, copied character for character from the file above
=======
replacement lines
>>>>>>> REPLACE
Each SEARCH section must match exactly one place in the file. Do not modify or add test files.
```

**Recorded for each task:**
- `common_identity` = SHA-256(COMMON in UTF-8);
- `identity_U`, `identity_S` = SHA-256 of each full prompt;
- the exact pre-flight token count for both prompts, using the frozen HF counting rule (+1).

Both prompts must be ≤ B_prompt = 15232 tokens, with no truncation.

## 6. Exact S grammar and semantics (D2, Amendment D)

**Region selection (mirrors `_extract_patch`):**
- If the completion contains a "```" fence, the region is the content of the **first** fenced block. A first line equal to a language tag (`diff`, `patch`, `udiff`, `python`, case-insensitive, stripped) is dropped.
- Otherwise the region is the whole completion.
- Leading and trailing whitespace of the region is removed.

This is declared grammar, applied identically to every output. It is not repair [G-2].

**Grammar.** The region must be a sequence of one or more blocks, optionally separated by empty lines. Lines are split on `\n` (LF). Any other content is `S_MALFORMED_BLOCK`.
```
block        := SEARCH_LINE search_line+ SEP_LINE replace_line* REPLACE_LINE
SEARCH_LINE  := "<<<<<<< SEARCH " PATH        (exactly 7 '<', single spaces)
SEP_LINE     := "======="                     (exactly 7 '=')
REPLACE_LINE := ">>>>>>> REPLACE"             (exactly 7 '>')
PATH         := non-empty, no whitespace, no leading "/" or "a/" or "b/", no ".." component
```
- `search_text` = concatenation of `line + "\n"` over the search lines. At least one line is required: an empty SEARCH is `S_MALFORMED_BLOCK`.
- `replace_text` is defined the same way, and may be empty, which means a deletion.

**Resolution** (exact byte matching; no fuzzy matching, normalization, occurrence selection or repair):
1. PATH must be a tracked regular file at `base_commit` (`100644` or `100755`). Otherwise `S_PATH_INVALID`.
2. Occurrences are counted in the **original** base content of that file, starting only at line boundaries (offset 0, or immediately after `\n`), overlapping starts included:
   - **0** → `S_SEARCH_NOT_FOUND`;
   - **1** → resolved;
   - **> 1** → `S_SEARCH_AMBIGUOUS`.
3. Resolved spans in the same file must not overlap. Otherwise `S_OVERLAP`.
4. All replacements are applied at once to each file's original content, in span order.
5. If no file content changed, the code is `S_EMPTY_EDIT`. No gate run is made: the empty-patch case is the analogue of U's NO_OUTPUT.

The first failing block, in output order, determines the code. Every block's status is recorded.

**Diff synthesis.**
- In a fresh `--network none` container from the pinned task image, the edited file contents are written over the working tree and `git diff --no-color --no-ext-diff --` is run on the edited paths [G-7].
- The output is used byte-for-byte as the candidate patch.
- It runs on the image's own pinned git, so no host-side differ is involved.
- If the probe gate rejects a synthesized diff, the code is `S_SYNTH_INTEGRITY`. That is a **harness failure → stop and report** (§17).

**Pre-condition** (admissibility (h), §9): each gold-file blob at `base_commit` is byte-identical to that file in the image working tree (HEAD), because the gate applies patches to the working tree.

## 7. Endpoint definitions (primary and secondary)

**Gate pass.** In the probe candidate run, the `git apply` step succeeded. The candidate `status` is not `PATCH_APPLY_FAILED` and is not a failure that happened before the apply step. Concretely, status ∈ {RAN, TEST_PATCH_FAILED, RESTORE_FAILED}, or VELITH_SURFACE markers are present. This is the frozen P1 `patch_applies` rule.

| Endpoint | Definition | Values |
|---|---|---|
| **U_APPLIES** (primary) | U produced an extractable patch (`Proposal.has_patch`) **and** the gate passed on that patch | true / false / NA |
| **S_APPLIES** (primary) | **All** blocks parsed, **every** SEARCH resolved exactly once, replacements applied without overlap, the harness generated a non-empty diff, **and** the same gate passed on that diff | true / false / NA |
| VERIFIED_PASS (secondary) | Probe classification = PASSED (`ALL_REQUIRED_PASSED`) for that arm. Reported only. Never replaces or adjusts the primary endpoint. | true / false / NA |

- **false:** any model-attributable failure. That covers NO_OUTPUT, S_* resolution codes, S_EMPTY_EDIT, and a gate rejection (U: MALFORMED_PATCH / PATCH_DOES_NOT_APPLY).
- **NA:** unresolved GEN_INFRA, or an infrastructure failure of the candidate container before the apply step (after the OD-8 retry), or a task aborted under D7.
- **GEN_TRUNCATED** is recorded as an explicit state. A truncated completion is still evaluated if it parses (D8).
- **Gate independence [G-3]:** the primary endpoint is read from the candidate container's gate step. Baseline health affects only VERIFIED_PASS.

## 8. Statistical analysis (D5, Amendment E)

**Analysis set:** tasks where both U_APPLIES and S_APPLIES are non-NA (valid pairs, n_v). Tasks with an NA are listed separately, with their reasons.

**Report, all mandatory:**
- `both`, `S-only`, `U-only`, `neither`;
- `discordant` m = S-only + U-only;
- raw applicability per arm, as counts and fractions over n_v (k_S/n_v, k_U/n_v), with no intervals;
- **exact one-sided p** = P(X ≥ S-only), X ~ Binomial(m, 0.5). If m = 0, it is reported as "no discordant pairs; test not computable" and H1 is not supported.
- VERIFIED_PASS counts per arm, as secondary and descriptive only.

**Pre-declared conclusions:**

| Code | Condition |
|---|---|
| P2-A | n_v ≥ n_min, S-only > U-only, and p < 0.05: H1 supported, on this population under C-O |
| P2-B | n_v ≥ n_min, at least one arm applies somewhere, and P2-A doesn't hold: no detectable S advantage at this sample size. **Not** equivalence. |
| P2-C | n_v ≥ n_min and both = S-only = U-only = 0: neither contract produced an applicable edit even with the target file present |
| P2-D | n_v < n_min, or unresolved infrastructure failures (GEN_INFRA, EXEC_INFRA or D7 abort) on ≥ 3 tasks: not interpretable |

`n_min` = 10 (D3).

**Limitations of the exact paired sign test (Amendment E):**
- It uses only discordant pairs. Concordant tasks (both/neither) carry no information about H1.
- With m discordant pairs, p < 0.05 requires S-only ≥ k(m). Even m = 5 with all five S-only gives p = 0.03125, and m ≤ 4 can never reach significance. n = 20 is therefore a feasibility sample, not a powered study.
- It is one-sided: a U advantage is reported descriptively (U-only), not tested.
- It assumes tasks are exchangeable units. Task heterogeneity and the per-repository cap are not modelled.
- There is a single primary test, so no multiplicity adjustment applies. Secondary results are descriptive only.
- No power or equivalence claim is made, and no effect size is estimated.

## 9. Eligibility and admission

**Eligibility** (outcome-blind; computed from the dataset only):
- **(a)–(e)** P1 §7, reused: a `pytest` command; `.py` test-patch files; ≥ 1 PASS_TO_PASS; 1 ≤ |FAIL_TO_PASS| ≤ 5; the gold patch edits exactly one non-test file and no test file.
- **(f)** Both arm prompts (§5) are ≤ 15232 tokens under the exact pre-flight count. Computed at Phase A Stage P.
- **(g)** (D4) The test-ID screen. Exclude the task if any FAIL_TO_PASS or PASS_TO_PASS ID matches `\s`, or has `count("[") != count("]")`. Deterministic; frozen before the lottery.
- **Repository:** one of the five P2 repositories [G-1].
- **Exclusion:** not in `p2/P2_EXCLUSION_REGISTRY.json` (§11).

**Admission (Phase A; per lottery candidate):**
1. Pull by pinned linux/amd64 digest, and check identity (P1 `p1_admit.sh` procedure).
2. Build the OD-5 protected-config spec with the fixed P1 inspection logic, used read-only.
3. Run Case A (the gold patch) through the probe. It must give **PASSED** with every required ID mapped (P1 §9).
4. **(h)** Each gold-file blob at `base_commit` equals the working-tree file in the image.
5. Stage P for both arms: (f) holds, and the leakage audit passes under the P1 frozen definition (RD freeze, 2026-10-02), applied to both prompts.
6. Run the S-path integrity self-check (§13): the gate must accept the harness-synthesized diff of gold-derived blocks.

Failing step 1–5 makes the task inadmissible; the lottery continues. A failure at step 6 is a harness defect: stop before freeze.

## 10. Lottery (not yet computed)

- **Pool:** all eligible tasks under §9 (a)–(e), (g), repository and exclusion, at dataset revision `78f471bf655a3137b2e8a75af1501690ec009ec3` (D3). The revision is checked before and after the fetch.
- **Order:** SHA-256(instance_id + `"|velith-m2pv-p2-pilot-v1"`) ascending, ties broken by instance_id.
- **Walk:** take candidates in order, skipping any whose repository already has **4** admitted tasks (D3). Admit until **n = 20** are admitted or the pool is exhausted. An inadmissible task is replaced by continuing the walk.
- **Repository exhaustion:** a repository with fewer than 4 admissible tasks contributes fewer. There is **no backfill** beyond the cap. n may then end up below 20, and is recorded.
- **Replacement after generation starts:** none.
- **Slots:** `P2-01 … P2-20`, in admission order.
- The pool listing, the ordered candidate list and every admission outcome are written to evidence.

## 11. Exclusion registry rules (Amendment B)

- `p1/PILOT_EXCLUSION_REGISTRY.json` (`9fc0157b…`) is **never modified**.
- `p2/P2_EXCLUSION_REGISTRY.json` is created before the lottery. It contains all **11** P1 registry instance IDs, each with its P1 status and a source reference.
- The lottery pool excludes all 11, and the lottery code asserts this.
- After Phase A, the P2 registry is extended once, append-only, at freeze, with:
  - every P2 admitted task (with `common_identity`);
  - every P2 candidate rejected at admission (exposed).

  It then becomes part of the freeze.
- Both registries are audit and safety registries, not selection rules for anything outside P2.

## 12. Image lifecycle (D7)

- **Phase A:** pull by digest → admit → Stage P → S self-check → record → **delete the image**. Deletion is authorized by D7; the digest and image ID are recorded first.
- **Phase B:** re-pull **only by the recorded immutable digest**, then check identity (RepoDigests contain the pinned reference, platform linux/amd64, image ID equal to the Phase A record).
  - **Any mismatch or failed identity check aborts that task.** Its pair becomes NA (D7 abort). There is no replacement.
- After the task's Stage X runs, delete the image again.
- Before every pull, the free-space gate is checked: C: free ≥ 2.5 × compressed size + 10 GB (the P1 per-pull rule) [G-9].

## 13. Deterministic execution (Amendment C)

1. **Phase A** (§9–§12), for all lottery candidates until n is admitted.
2. **Freeze** (§18): `p2/PILOT_SET.json` plus the extended P2 registry.
3. **Phase B**, per task in slot order:
   1. Re-pull and check identity.
   2. **First arm:** `ollama stop`, then confirm `/api/ps` shows no P2 model, then check free RAM ≥ 4 GiB, then generate.
   3. **Unload and reset:** `ollama stop`, then confirm `/api/ps` is empty.
   4. **Second arm:** generate in the same way.
   5. Unload.
   6. Run S resolution and diff synthesis.
   7. Run Stage X(U), then Stage X(S), each in fresh probe containers.
   8. Delete the image.
- **Arm order:** frozen per task in PILOT_SET. U goes first iff the first byte of SHA-256(instance_id + `"|velith-m2pv-p2-arm-order"`) is even.
- **Seed (D6):** `derive_task_seed(common_identity, 0)`, shared by both arms. It is recomputed in-container with the frozen Velith function and asserted.
- **Cold start per generation:** no KV-cache sharing between arms. The observed `prompt_eval_count` must equal the prediction; otherwise the TOKEN_COUNT_MISMATCH flag is recorded.
- **Self-checks** (no model; Phase A):
  - U path = Case A itself.
  - S path: build exact blocks from the gold patch hunks (SEARCH = old side, REPLACE = new side) and run them through the frozen parser, resolver, synthesis and gate. The probe classification must be PASSED.
  - If gold-derived blocks are themselves ambiguous, that is **recorded, and the task is not excluded**, so that selection doesn't favour S. A synthesis or gate rejection is a harness defect.
- **Resumable:** raw output is persisted before interpretation. A completed generation is never repeated (P1 R7 discipline).

## 14. Timeout and retry rules

- **Generation:** client timeout 1800 s.
- **Generation retries (OD-8):** at most 1 retry, for infrastructure failures only, where the request was sent but no completion came back. Never after a timeout, out-of-memory or over-budget failure. Failures before the request is sent are not attempts.
- **Stage X timeout (D12):** frozen per task in PILOT_SET from the Phase A Case-A evidence. 900 s if the Case-A candidate container duration is ≤ 300 s, otherwise 1800 s [G-4].
- **Stage X retry:** at most 1 fresh-container retry, on INFRA_ERROR before the gate or on BASELINE_UNHEALTHY. Never after RESOURCE_KILLED or a timeout.
- **Admission:** Case A once per candidate. A pull failure may be retried once.

## 15. Failure taxonomy (Amendment F): four separately measurable layers

Each (task, arm) records one code per layer reached. The overall code is the first failing layer.

| Layer | Codes | Arm |
|---|---|---|
| **L1 Generation** | GEN_INFRA; GEN_TRUNCATED (state flag); NO_OUTPUT (U: no extractable diff; S: no text in the region) | both |
| **L2 Structured-edit resolution** | S_MALFORMED_BLOCK, S_PATH_INVALID, S_SEARCH_NOT_FOUND, S_SEARCH_AMBIGUOUS, S_OVERLAP, S_EMPTY_EDIT; S_SYNTH_INTEGRITY (harness → stop) | S only (U: not applicable) |
| **L3 Patch application (gate)** | GATE_PASS; U: MALFORMED_PATCH, PATCH_DOES_NOT_APPLY (P1 definitions, from `git apply` stderr); S: GATE_REJECT (= S_SYNTH_INTEGRITY); PRE_GATE_INFRA | both |
| **L4 Verification** | CANDIDATE_PASSED, CANDIDATE_FAILED, BASELINE_UNHEALTHY, EXEC_INFRA, TIMEOUT, RESOURCE_EXHAUSTED, TEST_INTEGRITY (P1 definitions) | both, only if L3 = GATE_PASS |
| Harness | HARNESS_FAILURE, S_SYNTH_INTEGRITY → stop | — |

Per arm, counts are reported for every code in every layer.

## 16. Evidence structure

```
p2/
  P2_DESIGN_DRAFT.md → (ratified) P2_SPEC.md
  P2_EXCLUSION_REGISTRY.json      (pre-lottery; append-once at freeze)
  PILOT_SET.json                  (freeze)
  harness/                        (D9; code + synthetic-only tests; SHAs in PILOT_SET)
  evidence/
    _lottery/      pool.json, order.json, admission_log.json, revision checks
    _gencheck/     container integrity check (network none)
    P2-NN/
      A/           pull, inspect, spec, Case-A probe run, (h) check, timeout derivation
      P/           common.txt, prompt_U.txt, prompt_S.txt, material.json, preflight.json, leakage_audit.json
      SELF-S/      gold-derived blocks, resolution.json, synthesized.diff, probe run
      G-U/attempt-n/, G-S/attempt-n/   raw_stdout, raw_stderr, completion.txt, result.json
      S/           region.txt, blocks.json, resolution.json, synthesized.diff
      X-U-n/, X-S-n/                   probe evidence (baseline/candidate, junit, stdout)
      episode.json (per-arm L1–L4 codes, endpoints, flags, hashes), MANIFEST.sha256
  P2_REPORT.md                    (after Phase B)
```

Every file is written as bytes (LF) and hashed. Each directory has a `MANIFEST.sha256`.

## 17. Stopping rules (no efficacy stopping; fixed n)

**Stop the pilot and report** on any of:
- S_SYNTH_INTEGRITY or HARNESS_FAILURE;
- the harness, parser, template, PILOT_SET or registry SHA changing after freeze;
- the model digest changing, or `context_length` ≠ 16384;
- a systemic leakage-audit failure;
- unresolved infrastructure failures (GEN_INFRA / EXEC_INFRA / D7 abort) on ≥ 3 tasks (→ P2-D);
- the free-space gate failing with no authorized remedy;
- any write to Velith main or to a Velith store;
- a probe network mode other than `none`.

**Task-level abort (pair NA, no replacement):** a D7 identity mismatch after freeze.

## 18. Freeze checklist (all before any generation)

See the "Proposed freeze gates" at the end of this document: FG-0 … FG-8.

## 19. Threats to validity

| ID | Threat | Mitigation / scope |
|---|---|---|
| T-1 | Instruction wording and length differ (CONTRACT_U vs CONTRACT_S), so the instruction effect is confounded with the format effect | Byte-identical COMMON (Amendment A). Comparable instruction length; token counts recorded. Acknowledged; not removable. |
| T-2 | Oracle context leaks location | No localization or end-to-end claim (D1, D11) |
| T-3 | Filter (f) selects tasks with smaller gold files | Results are scoped to the admitted population |
| T-4 | Pretraining contamination (public fixes) | Primary endpoint is mechanical; VERIFIED_PASS especially exposed; stated |
| T-5 | Exact matching penalizes S for trivial whitespace slips, and the final-line newline edge case | Declared strictness (D2); per-block codes make the cause observable |
| T-6 | The 1024-token cap may disadvantage S (SEARCH repeats context) | D8 keeps comparability; GEN_TRUNCATED per arm reported |
| T-7 | Small n and the sign test's discordant-only use (§8) | Feasibility framing; no power or equivalence claim |
| T-8 | Single host, temperature-0 reproducibility | Single-attempt evidence; not bit-reproducibility |
| T-9 | Repository cap and exhaustion change composition | Pre-declared walk; n recorded |
| T-10 | Baseline/gate independence choice [G-3] | Primary endpoint read only from the candidate gate step |

## 20. Open governance decisions (remaining after the D1–D12 ratification)

| ID | Decision | CSE proposal | Body |
|---|---|---|---|
| **G-1** | **Which five repositories.** D3 says "five repos including Flask", but the draft's candidate set had seven (six P1 repos plus Flask). | Flask plus the four repositories P1 actually admitted from: matplotlib, scikit-learn, astropy, xarray. Drop seaborn and pylint. | RD |
| **G-2** | Verbatim CONTRACT_S text; keeping the COMMON heading "retrieved automatically"; the region-selection rule mirroring `_extract_patch` | As in §5 and §6 | SRC + RD |
| **G-3** | Primary endpoint read from the candidate gate step regardless of baseline health | Adopt (the gate is independent of the baseline) | SRC |
| **G-4** | Stage-X timeout rule thresholds (300 s → 900/1800 s) | As in §14 | RD |
| **G-5** | No backfill beyond the cap of 4 per repository; n may fall below 20; n_min = 10 | Adopt | RD |
| **G-6** | S semantics details: match against original content (not sequential); empty SEARCH forbidden; empty diff → S_EMPTY_EDIT (= false); multi-file blocks allowed; no special handling of a missing final newline | Adopt | SRC |
| **G-7** | Diff synthesis with the task image's own git, in a network-none container | Adopt | SRC |
| **G-8** | Admissibility (h): gold blobs at base equal the working-tree files | Adopt | SRC + RD |
| **G-9** | Storage threshold and the maximum number of admission attempts (pull budget) | P1 per-pull rule; no attempt cap, but stop if the pool is exhausted | RD |
| **G-10** | Self-check S on every admitted task, non-excluding on ambiguity | Adopt | SRC |

---

## Proposed freeze gates (each must PASS, in order; nothing generates before FG-8)

| Gate | Content | Pass criterion | Evidence |
|---|---|---|---|
| **FG-0 Governance** | This specification ratified as `p2/P2_SPEC.md`, with the G-1…G-10 rulings | RD and SRC ratification recorded; spec SHA-256 | ratification record |
| **FG-1 Registry** | `p2/P2_EXCLUSION_REGISTRY.json` created with all 11 P1 IDs; P1 registry unchanged (`9fc0157b…`) | 11 entries; P1 registry hash equal | registry plus hash check |
| **FG-2 Harness code** | `p2/harness/` (P1 imported read-only): parser, resolver, synthesis, lottery, Phase A/B commands; tests on **synthetic inputs only** (grammar, 0/1/>1 matches, overlap, empty edit, region rule, synthesis against local git, endpoint mapping, sign-test arithmetic) | Tests pass; ruff/mypy clean; harness and parser SHAs recorded; no model or real-task output used | test log, SHAs |
| **FG-3 Lottery** | Revision check `78f471bf…` before and after; eligible pool under (a)–(e), (g), repos, exclusions; ordered list | Revision equal; the 11 IDs absent from the pool (asserted); pool and order hashed | `_lottery/pool.json`, `order.json` |
| **FG-4 Phase A** | Admission walk until n = 20 or exhaustion: Case A PASSED; (h) holds; Stage P (both prompts ≤ 15232, both audits PASS); S self-check gate accepted; Case-A duration and timeout derived; images deleted after recording digests | Every admitted task meets all of these; n recorded; every rejection logged with its reason | `_lottery/admission_log.json`, `P2-NN/{A,P,SELF-S}` |
| **FG-5 Generation route** | `gencheck` in `velith-verifier:m0` with network none: module SHAs equal the pinned Velith commit; seed and prompt identity assertions; image ID recorded | CHECK_OK | `_gencheck/` |
| **FG-6 PILOT_SET** | `p2/PILOT_SET.json` frozen, containing: tasks; digests and image IDs; spec SHAs; `common_identity`, `identity_U`, `identity_S`; token counts for both arms; seed; arm order; Stage-X timeout; harness, parser and spec SHAs; model and parameters; P2 registry appended (admitted plus rejected) | Written once; SHA recorded; `run` refuses on any later mismatch | `PILOT_SET.json`, registry |
| **FG-7 No-model proof** | The Ollama log shows no `/api/generate` request between FG-0 and FG-6 | Last generate timestamp earlier than FG-0 | log excerpt |
| **FG-8 Commit** | One commit containing FG-0…FG-7 artifacts; RD review of the Phase A evidence | Pushed; RD go for Phase B | commit SHA |

*End of the candidate specification. No implementation, lottery, execution or P1 modification is authorized by this document.*
