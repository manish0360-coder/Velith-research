# P1 episode record: T2 `matplotlib__matplotlib-24970` (2026-10-02)

**Status:** this is the official, one-generation P1 episode for slot T2 (OD-6 replacement R5, admitted 254/254). The frozen classification below is final. §3 states only what the preserved evidence and the frozen artifacts support.

**Evidence:** `p1/evidence/T2/`
- `MANIFEST.sha256` (SHA-256 `7a77f071b7aaa23b…`) lists 21 files; `sha256sum -c` is OK.
- `G/attempt-1/` holds the generation.
- `G/post_unload.json` holds the post-generation unload check.
- `X-1/` holds the Stage X probe run.
- `episode.json` holds the classification.

**Frozen inputs** (unchanged):
- `PILOT_SET.json` `0f0e8715…`;
- harness `c4ad73e3…`;
- `p1_gen.py` `c84a614c…`;
- probe `560834d5…`;
- Velith `6ca531f5…`;
- the T2 prepare manifest equals `PILOT_SET.json`;
- the in-container Velith module SHAs equal the frozen generation route;
- frozen spec `stage0/p1env/results/admission-T2R1R1R1R1R1/T2R1R1R1R1R1.spec.json`.

## 1. Identity and generation

| Item | Value |
|---|---|
| Slot / instance_id | T2 / `matplotlib__matplotlib-24970` |
| Prompt identity (SHA-256 of prompt UTF-8) | `fe8e73c9bc08ac4e68d965f5a6b0fbb3b88cd3cc7591d5abd7c19635a1eb6683` |
| Seed | `derive_task_seed(identity, 0)` = `6363229982489726258` |
| Model | `velith-p1-deepseek-coder-v2:16b-c16384-np1024`. The `/api/tags` digest `e196dcd918e4f54307db79c9fada1ff261c564e1df1624e20ae65d1ff0a4c45c` equals the pin. Ollama 0.34.4. |
| Temperature / context length | **0.0** / **16384**, confirmed by `/api/ps` `context_length` after the call. `num_predict` 1024. |
| Cold start | `/api/ps` was empty before the request |
| Prompt tokens | predicted **15129**, observed **15129**. The token-count assertion holds. Budget 15232. |
| Completion tokens | **171**, so not truncated |
| Generation latency | **962.45 s**. Attempt window 17:38:13Z → 17:54:19Z. |
| Generation attempts | **1**. No retry, no regeneration. |
| Free RAM (Windows) | 17,868,804,096 B before generation; 17,774,145,536 B after unload (`/api/ps` empty) |
| Retrieved files (prompt) | `lib/matplotlib/_api/deprecation.py`, `setup.py`, `tutorials/introductory/customizing.py`, `tutorials/text/pgf.py`, `lib/matplotlib/backends/backend_wxcairo.py` |

## 2. Official frozen outcome (not reinterpreted)

| Layer | Value |
|---|---|
| `patch_produced` | **true** |
| Patch SHA-256 | `f9d63f09cc031385b9973c47f6ab5d4e5093f1ef146183ba459c4b6aa6546c3a`. It is byte-identical to the patch the probe applied (`X-1/candidate/velith/candidate.patch`). |
| Probe classification (`verified_outcome`) | **PATCH_APPLY_FAILED**, reason `CANDIDATE_PATCH_DID_NOT_APPLY`; candidate container exit 92 |
| P1 §18 failure-table code (`code` = `x_code`) | **PATCH_DOES_NOT_APPLY** |
| `patch_applies` | **false** |
| Flags | none. `interpretable` = true. |

**Exact generated patch** (`G/attempt-1/patch.diff`):
```diff
--- a/lib/matplotlib/colors.py
+++ b/lib/matplotlib/colors.py
@@ -727,7 +727,7 @@ def get_cmap()(np.empty((0, ), dtype=np.uint8))
         xa[xa < 0] = self._i_under
         xa[mask_bad] = self._i_bad
 
-        if self._is_colored:
+        if self._is_colored and self._i_over is not None:
             xa[xa > self.N - 1] = self._i_over
         else:
             xa[xa > self.N - 1] = self._i_over
```
The raw completion is in `G/attempt-1/completion.txt`. It is a single fenced `diff` block with one leading space before the fence, and no other text.

**Exact `git apply` error** (`X-1/candidate/stdout.txt`):
```
error: patch failed: lib/matplotlib/colors.py:727
error: lib/matplotlib/colors.py: patch does not apply
```

**Candidate run:**
- It ran with `status` PATCH_APPLY_FAILED (exit 92), `network_mode` none, 2.87 s, on HEAD `0b6aeb76…` whose parent is base `a3011dfd…`.
- **No tests ran:** `mapped_required` = 0 and no pytest exit code was recorded.

**Baseline run:**
- It ran with `status` RAN, `network_mode` none, network probe blocked, 25.4 s, and 0 collection failures.
- **Total collected (pytest / JUnit, all tests in the test file):** 256 collected; **253 passed, 2 failed, 1 skipped**.
  - failed `lib/matplotlib/tests/test_colors.py::test_index_dtype[uint8]` (`DeprecationWarning: NumPy will stop allowing conversion of out-of-bound Python integers to integer arrays …`)
  - failed `lib/matplotlib/tests/test_colors.py::test_double_register_builtin_cmap` (`MatplotlibDeprecationWarning: The register_cmap function was deprecated in Matplotlib 3.7 …`)
  - skipped `lib/matplotlib/tests/test_colors.py::test_norm_update_figs[svg]` (`Don't know how to convert .svg files to png`)
- **Frozen required mapping (what the probe judges):** `mapped_required` = **254** of 254 required IDs (1 F2P + 253 P2P in the frozen spec).
  - Within the required set, 253 passed and 1 failed: `test_index_dtype[uint8]`.
  - This is shown directly in the baseline `outcomes` map of `X-1/evidence.json`.
  - That ID is the spec's only `fail_to_pass` entry.
- `test_double_register_builtin_cmap` and `test_norm_update_figs[svg]` are **not** in the required set: they are absent from the `outcomes` map.
- **The two total failures do not make the baseline unhealthy.** The frozen health rule looks only at required IDs: every P2P passed, the F2P did not pass, and every required ID mapped. The probe accordingly proceeded to judge the candidate. The extra failure and the skip are outside the required set and are recorded for completeness only.

## 3. Forensic observations (evidence-limited; not a replacement verdict)

| Failure type | Supported by the evidence? | Basis |
|---|---|---|
| **Patch format / application failure** | **Application failure: yes. Format defect: no.** | The hunk header `-727,7 +727,7` is consistent with the body: 7 old lines (6 context + 1 removed) and 7 new lines (6 context + 1 added). `git apply` reported `patch failed … :727`, a context mismatch, not `corrupt patch`. That is why the frozen code is PATCH_DOES_NOT_APPLY. The header's trailing section text (`def get_cmap()(np.empty((0, ), dtype=np.uint8))`) is not part of what `git apply` checks. |
| **Wrong location / context** | **Context: yes, unsourced. Location: matches the gold file.** | The edited file `lib/matplotlib/colors.py` is the frozen spec's only gold-patch file. It was **not** in the prompt: BM25 ranked it 1st, but the frozen fit rule skipped it (`tokens_if_included` 29,222 > 15,232). So the hunk's line number and context lines could not have been copied from the prompt, and they did not match the base tree. Whether they were reconstructed from pretraining memory is not established by this evidence. |
| **Semantic failure** | **Not assessable** | The patch never applied and no candidate test ran. This record makes no claim that the intended change was semantically correct or incorrect. |

## 4. Binding statements

1. **T2 is one-generation evidence (R7). It must not be rerun or regenerated.** This completion and this classification are final for P1.
2. **No post-hoc experiment tuning is authorized:** no prompt, retrieval, token-budget, model, generation-parameter, harness, extraction or verifier change. Any change informed by this episode would be outcome-informed tuning, prohibited by P1 §22, R7 and P-2.
3. Raw counts only (P-3): for T2, `patch_produced` true, `patch_applies` false.
4. Velith main and all frozen P1 artifacts are unchanged.
