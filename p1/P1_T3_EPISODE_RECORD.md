# P1 episode record: T3 `scikit-learn__scikit-learn-14629` (2026-10-02)

**Status:** this is the official, one-generation P1 episode for slot T3.
- The frozen classification below is final.
- §3 is an analysis observation, not a replacement verdict.

**Evidence:** `p1/evidence/T3/`
- `MANIFEST.sha256` (SHA-256 `73c477f6ce289aa8…`) lists 45 files; `sha256sum -c` is OK.
- `G/attempt-1/` holds the generation.
- `G/post_unload.json` holds the post-generation unload check.
- `X-1/` holds the Stage X probe run.
- `episode.json` holds the classification.

**Frozen inputs** (unchanged; verified against the Milestone 1 commit `b7e8cab`):
- `PILOT_SET.json` `0f0e8715…`;
- harness `c4ad73e3…`;
- `p1_gen.py` `c84a614c…`;
- probe `560834d5…`;
- Velith `6ca531f5…`;
- T3 prepare manifest matches `PILOT_SET.json`.

## 1. Identity and generation

| Item | Value |
|---|---|
| Prompt identity (SHA-256 of prompt UTF-8) | `115f516e2519e2acbb4cae28b43bb2857da70bd2e9e9f1f34516f13402cbcb48` |
| Seed | `derive_task_seed(identity, 0)` = `5174882623180139665`. Re-derived inside the container with the frozen function; equal. |
| Model | `velith-p1-deepseek-coder-v2:16b-c16384-np1024`. The `/api/tags` digest `e196dcd9…c45c` equals the pin. Ollama 0.34.4, Q4_0, 15.7B. |
| Generation route | `velith-verifier:m0`, image `sha256:36c4c00b…`, Python 3.12.7. Velith module SHAs equal `6ca531f`. |
| Parameters | temperature 0.0; `num_ctx` 16384, confirmed by `/api/ps` `context_length` = 16384; `num_predict` 1024; stops `\nUser:` and `\nAssistant:` |
| Cold start | The model was not loaded before the request (`/api/ps` showed no models). `ollama stop` returned rc 0. |
| Prompt tokens | predicted **14892**, observed `prompt_eval_count` **14892**. The token-count assertion holds. Budget 15232. |
| Completion tokens | **154**, below 1024, so not truncated |
| Generation latency | **927.85 s** for the single client call. Attempt window 13:17:31Z → 13:33:02Z. |
| Free RAM (Windows) | 17,231,708,160 B before generation; 17,479,602,176 B after unload (`/api/ps` empty) |
| Attempts | 1. No retry, no regeneration. |

## 2. Official frozen outcome (not reinterpreted)

| Layer | Value |
|---|---|
| `patch_produced` | **true** (extracted by the frozen `_extract_patch`) |
| Patch SHA-256 | `1a8b91d8bcbe7914398efa88c053eabe3dc81283c5d35e726c4d0dc781e0b015`. It is byte-identical to the patch the probe applied (`X-1/candidate/velith/candidate.patch`). |
| Probe classification (`verified_outcome`) | **PATCH_APPLY_FAILED**, reason `CANDIDATE_PATCH_DID_NOT_APPLY`; candidate container exit 92 |
| P1 §18 code | **PATCH_DOES_NOT_APPLY** (`x_code` the same). This is the frozen label for the same event: a well-formed diff whose context doesn't match. |
| `patch_applies` | **false** |
| Flags | none. `interpretable` = true. |

**Exact patch produced** (`G/attempt-1/patch.diff`):
```diff
--- a/sklearn/model_selection/_validation.py
+++ b/sklearn/model_selection/_validation.py
@@ -857,7 +857,7 @@
         for i in range(len(estimator.estimators_)):
             y_prob[:, i] = estimator.estimators_[i].predict_proba(X)[:, 1]
 
-    classes_ = estimator.classes_
+    classes_ = estimator.estimators_[0].classes_
     if len(classes_) == 2:
         y_prob = np.hstack([1 - y_prob, y_prob])
     else:
```
The raw completion is in `G/attempt-1/completion.txt`. It is a single fenced `diff` block with one leading space before the fence, and no other text.

**Exact patch-application failure** (`X-1/candidate/stdout.txt`):
```
error: patch failed: sklearn/model_selection/_validation.py:857
error: sklearn/model_selection/_validation.py: patch does not apply
```
- The candidate container ran with `network_mode` none, on HEAD `eb6f3698…` whose parent is base `4aded39b…`.
- It took 1.65 s.
- No tests ran.

**Baseline run:**
- It ran with `status` RAN, `network_mode` none, network probe blocked, 35.8 s, and all 27 required IDs mapped.
- 26 passed. One failed: `sklearn/tests/test_multioutput.py::test_multi_output_classes_[estimator1]`, with `AttributeError: 'MultiOutputClassifier' object has no attribute 'classes_'`.
- That test is T3's only **FAIL_TO_PASS** test. Under the frozen `classify`, its failure at baseline is the *required* healthy-baseline condition, not an infrastructure fault. All P2P tests passed at baseline.

## 3. Semantic diagnosis (analysis observation; NOT a verdict)

- **Target file.** The patch edits `sklearn/model_selection/_validation.py`. That file was **not** in the prompt.
  - BM25 ranked it 21st (score 70.32).
  - It was skipped by the frozen fit rule: including it would have made the prompt 29,045 tokens, over the 15232 budget.
  - The five retrieved files were `setup.py`, `sklearn/utils/testing.py`, `sklearn/utils/_show_versions.py`, `sklearn/exceptions.py` and `examples/compose/plot_digits_pipe.py`.
- **Where the edit came from.** The issue text names that file and a line range (`_validation.py#L857-L866`, at a different upstream commit `3be7110d`). It also suggests `estimators_[i].classes_`.
  - The model followed the issue's pointer.
  - The hunk header line (857) and the context lines could not have come from the prompt. They were reconstructed, plausibly from pretraining memory (residual RS-P1). They do not match the base tree, and `git apply` rejected them.
- **Gold location.** The gold fix edits `sklearn/multioutput.py`: it adds `MultiOutputClassifier.fit`, which sets `classes_`. BM25 ranked that file 6th. It was skipped by the fit rule at 19,146 tokens.
  - The F2P test checks `MultiOutputClassifier.classes_` directly after `fit`.
  - **By inspection only (not executed),** an edit to `_validation.py` alone would not create that attribute. So even a correctly applying version of this patch would be expected to leave the F2P test failing.
- **Diff format.** The format was compliant: a fenced `diff` block, `a/` and `b/` prefixes, a single hunk whose line counts are consistent (7/7), and no text outside the block. The failure is context and location, not syntax.
- **Attribution (P1 §24 framing, no generalization).** This is one observation (n = 1).
  - The frozen M-C context contract did not deliver the gold file or the file the model chose to edit.
  - So this outcome cannot be read as evidence about the proposer's capability given the right code. It is consistent with the pre-generation observation that the fit rule excludes large gold files (T2, T3, T5).
  - The diagnosis used gold information after the episode, for analysis only. It changes nothing.

## 4. Binding statements

1. **T3 was a one-generation episode (R7). It must not be rerun or regenerated.** This completion and this classification are final for P1.
2. **No harness, prompt, retrieval, token-budget, model or generation-parameter change is authorized** by this record. Any change informed by this episode would be gold-informed or outcome-informed tuning, prohibited by P1 §22, R7 and P-2.
3. Raw counts only (P-3): for T3, `patch_produced` true, `patch_applies` false.
4. Velith main and all frozen P1 artifacts are unchanged.
