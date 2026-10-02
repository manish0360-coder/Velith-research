# P1 episode record: T5 `pydata__xarray-7393` (2026-10-02)

**Status:** this is the official, one-generation P1 episode for slot T5 (OD-6 replacement R1, admitted 73/73). It is the final P1 generation episode. The frozen classification below is final. §3 states only what the preserved evidence and the frozen artifacts support.

**Evidence:** `p1/evidence/T5/`
- `MANIFEST.sha256` (SHA-256 `c2ee286d270bce86…`) lists 21 files; `sha256sum -c` is OK.
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
- the T5 prepare manifest equals `PILOT_SET.json`;
- the in-container Velith module SHAs equal the frozen generation route;
- frozen spec `stage0/p1env/results/admission-T5R1/T5R1.spec.json`;
- Stage X timeout 1800 s (OD-7, slot T5).

## 1. Identity and generation

| Item | Value |
|---|---|
| Slot / instance_id | T5 / `pydata__xarray-7393` |
| Prompt identity (SHA-256 of prompt UTF-8) | `c3109b06e90f948038e972811605c6f054e5de834d59288f79d099a453ebb392` |
| Seed | `derive_task_seed(identity, 0)` = `5007947557582598968` |
| Model | `velith-p1-deepseek-coder-v2:16b-c16384-np1024`. The `/api/tags` digest `e196dcd918e4f54307db79c9fada1ff261c564e1df1624e20ae65d1ff0a4c45c` equals the pin. Ollama 0.34.4. |
| Temperature / context length | **0.0** / **16384**, confirmed by `/api/ps` `context_length` after the call. `num_predict` 1024. |
| Cold start | `/api/ps` was empty before the request |
| Prompt tokens | predicted **14953**, observed **14953**. The token-count assertion holds. Budget 15232. |
| Completion tokens | **143**, so not truncated |
| Generation latency | **852.22 s**. Attempt window 18:26:39Z → 18:40:54Z. |
| Generation attempts | **1**. No retry, no regeneration. |
| Free RAM (Windows) | 17,440,202,752 B before generation; 17,641,021,440 B after unload (`/api/ps` empty) |
| Retrieved files (prompt) | `xarray/util/print_versions.py`, `doc/conf.py`, `xarray/util/generate_aggregations.py`, `ci/min_deps_check.py`, `doc/gallery/plot_rasterio.py` |

## 2. Official frozen outcome (not reinterpreted)

| Layer | Value |
|---|---|
| `patch_produced` | **true** |
| Patch SHA-256 | `9dae249b6fb21420aee73e143a8826c83e2b897e42a4ac931d5aadf44c353ae2`. It is byte-identical to the patch the probe applied (`X-1/candidate/velith/candidate.patch`). |
| Probe classification (`verified_outcome`) | **PATCH_APPLY_FAILED**, reason `CANDIDATE_PATCH_DID_NOT_APPLY`; candidate container exit 92 |
| P1 §18 failure-table code (`code` = `x_code`) | **PATCH_DOES_NOT_APPLY** |
| `patch_applies` | **false** |
| Flags | none. `interpretable` = true. |

**Exact generated patch** (`G/attempt-1/patch.diff`):
```diff
--- a/xarray/core/dataset.py
+++ b/xarray/core/dataset.py
@@ -1239,7 +1239,7 @@
         if dim is None:
             dim = list(self.dims)
         if axis is not None:
-            dim = normalize_axis_tuple(dim, self.ndim)
+            dim = normalize_axis_tuple(dim, self.ndim, self.dims)
         if keep_attrs is None:
             keep_attrs = OPTIONS["keep_attrs"]
         if keep_attrs is True:
```
The raw completion is in `G/attempt-1/completion.txt`. It is a single fenced `diff` block with one leading space before the fence, and no other text.

**Exact `git apply` error** (`X-1/candidate/stdout.txt`):
```
error: patch failed: xarray/core/dataset.py:1239
error: xarray/core/dataset.py: patch does not apply
```

**Baseline run:**
- It ran with `status` RAN, `network_mode` none, network probe blocked, 11.2 s, and 0 collection failures. pytest collected 73 tests; JUnit shows 73 tests, 2 failures, 0 skipped.
- **73 mapped required tests (`mapped_required` = 73): 71 passed, 2 failed.**
  - `xarray/tests/test_indexes.py::test_restore_dtype_on_multiindexes[int32]` (`AssertionError: assert 'int64' == 'int32'`)
  - `xarray/tests/test_indexes.py::test_restore_dtype_on_multiindexes[float32]` (`AssertionError: assert 'float64' == 'float32'`)
- Both failing IDs are the frozen spec's two `fail_to_pass` entries. All 71 P2P tests passed. This is the required healthy-baseline condition under the frozen `classify`.

**Candidate run:**
- It ran with `status` PATCH_APPLY_FAILED (exit 92), `network_mode` none, 0.865 s, on HEAD `df828cec…` whose parent is base `41fef6f1…`.
- **The patch failed to apply. `mapped_required` = 0, and no candidate tests ran.**

## 3. Forensic observations (evidence-limited; not a replacement verdict)

- **Classification of the observed failure: patch-context / application failure.**
  - The hunk header `-1239,7 +1239,7` is consistent with the body: 7 old lines (6 context + 1 removed) and 7 new lines (6 context + 1 added).
  - `git apply` reported `patch failed … :1239`, a context mismatch, not `corrupt patch`. So this is not a format defect, which matches the frozen code PATCH_DOES_NOT_APPLY.
- **Context source.** The edited file `xarray/core/dataset.py` was **not** in the prompt.
  - BM25 ranked it 4th, but the frozen fit rule skipped it (`tokens_if_included` 101,682 > 15,232).
  - So the hunk's line number and context lines could not have been copied from the prompt, and they did not match the base tree.
- **Location (factual only).** The edited file differs from the frozen spec's only gold-patch file, `xarray/core/indexing.py`. That file was also not in the prompt: it was skipped by the fit rule at 23,401 tokens.
- **No semantic correctness claim.** The patch never applied and no candidate test ran. This record makes no claim that the intended change was semantically correct or incorrect.

## 4. Binding statements

1. **T5 is permanently one-generation evidence (R7). It must not be rerun or regenerated.** This completion and this classification are final for P1.
2. **No P1 tuning or modification is authorized:** no prompt, retrieval, token-budget, model, generation-parameter, harness, extraction or verifier change. Any change informed by this episode would be outcome-informed tuning, prohibited by P1 §22, R7 and P-2.
3. Raw counts only (P-3): for T5, `patch_produced` true, `patch_applies` false.
4. Velith main and all frozen P1 artifacts are unchanged.
