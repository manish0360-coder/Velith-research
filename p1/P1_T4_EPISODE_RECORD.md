# P1 episode record: T4 `astropy__astropy-7336` (2026-10-02)

**Status:** this is the official, one-generation P1 episode for slot T4.
- The frozen classification below is final.
- §3 records format observations only. It makes no claim about semantic correctness or semantic failure, because the patch never applied.

**Evidence:** `p1/evidence/T4/`
- `MANIFEST.sha256` (SHA-256 `b07a0fa495fa1b81…`) lists 21 files; `sha256sum -c` is OK.
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
- the T4 prepare manifest equals `PILOT_SET.json`;
- the in-container Velith module SHAs equal the frozen generation route.

## 1. Identity and generation

| Item | Value |
|---|---|
| instance_id | `astropy__astropy-7336` |
| Prompt identity (SHA-256 of prompt UTF-8) | `4d82ad4344dd94e4d2664fb8688e8cd78d15e226a4b7bde0e79919ce0ae886f7` |
| Seed | `derive_task_seed(identity, 0)` = `2676707852901449598` |
| Model | `velith-p1-deepseek-coder-v2:16b-c16384-np1024`. The `/api/tags` digest `e196dcd918e4f54307db79c9fada1ff261c564e1df1624e20ae65d1ff0a4c45c` equals the pin. Ollama 0.34.4. |
| Parameters | temperature **0.0**; `num_ctx` 16384, confirmed by `/api/ps` `context_length` = 16384; `num_predict` 1024 |
| Cold start | `/api/ps` was empty before the request |
| Prompt tokens | predicted **15227**, observed **15227**. The token-count assertion holds. Budget 15232. |
| Completion tokens | **116**, so not truncated |
| Generation latency | **933.34 s**. Attempt window 16:21:30Z → 16:37:07Z. |
| Free RAM (Windows) | 17,066,278,912 B before generation; 18,270,576,640 B after unload (`/api/ps` empty) |
| Attempts | 1. No retry, no regeneration. |
| Retrieved files | `astropy/utils/decorators.py`, `astropy/units/decorators.py`, `astropy/nddata/decorators.py`, `astropy/io/__init__.py`. The file the model edited, `astropy/units/decorators.py`, was in the prompt verbatim. |

## 2. Official frozen outcome (not reinterpreted)

| Layer | Value |
|---|---|
| `patch_produced` | **true** |
| Patch SHA-256 | `54273a36cab2ed2efec363880a8f6580ee9fc6c81c75c440d846f504ca1519e7`. It is byte-identical to the patch the probe applied (`X-1/candidate/velith/candidate.patch`). |
| Probe classification (`verified_outcome`) | **PATCH_APPLY_FAILED**, reason `CANDIDATE_PATCH_DID_NOT_APPLY`; candidate container exit 92 |
| P1 §18 code (`code` = `x_code`) | **MALFORMED_PATCH**. The `git apply` stderr matched the frozen malformed marker `corrupt patch`. |
| `patch_applies` | **false** |
| Flags | none. `interpretable` = true. |

**Exact generated patch** (`G/attempt-1/patch.diff`):
```diff
--- a/astropy/units/decorators.py
+++ b/astropy/units/decorators.py
@@ -224,7 +224,7 @@ def wrapper(*args, **kwargs):
                 return_.to(wrapped_signature.return_annotation)
             else:
                 return return_
-        return wrapper
+        return return_.to(wrapped_signature.return_annotation) if wrapped_signature.return_annotation is not inspect.Signature.empty else wrapper
```
The raw completion is in `G/attempt-1/completion.txt`. It is a single fenced `diff` block with one leading space before the fence, and no other text.

**Exact verifier error** (`X-1/candidate/stdout.txt`):
```
error: corrupt patch at line 9
```
- The candidate container ran with `network_mode` none, on HEAD `f1bdcc25…` whose parent is base `732d89c2…`.
- It took 1.66 s.
- **The candidate tests did not run.**

**Baseline run:**
- It ran with `status` RAN, `network_mode` none, network probe blocked, 12.8 s, and all 340 required IDs mapped.
- **339 of 340 passed.** The one failure is `astropy/units/tests/test_quantity_annotations.py::test_return_annotation_none`, with `AttributeError: 'NoneType' object has no attribute 'to'` at `astropy/units/decorators.py:224`.
- That test is T4's only **FAIL_TO_PASS** test. Its baseline failure is the required healthy-baseline condition under the frozen `classify`. All P2P tests passed.

## 3. Format observations (factual; no semantic claim)

- **Target.** The model targeted `astropy/units/decorators.py`. That is the gold patch's only file, and the file was present in the prompt. Unlike T3, the target location was right. **The patch format was invalid.**
- **Why `git apply` reports line 9.** The hunk header declares `-224,7 +224,7`, that is, 7 old and 7 new lines.
  - The body supplies 4 old lines (3 context + 1 removed) and 4 new lines (3 context + 1 added), then the file ends.
  - The patch has 8 lines, so `git apply` reaches end-of-input (line 9) while the hunk still owes lines. It reports `corrupt patch at line 9`.
  - This is a header and body line-count inconsistency: a syntactic defect.
- **Secondary, by inspection only.** `git apply` never reached context matching. Against the verbatim retrieved file in `P/prompt.txt`, the patch's first context line (`return_.to(wrapped_signature.return_annotation)`) does not match base line 224 (`return return_.to(wrapped_signature.return_annotation)`). The patch's 4-line context and removal block also does not appear contiguously in the base file. So a header-corrected version would not be expected to apply either. This is recorded as an observation, not a verdict.
- **No semantic conclusion.** Because the patch never applied and no candidate test ran, this record makes **no claim** that the intended change was semantically correct or incorrect.

## 4. Binding statements

1. **T4 is frozen as one-generation evidence (R7). It must not be rerun or regenerated.** This completion and this classification are final for P1.
2. **No experiment tuning is authorized:** no harness, prompt, retrieval, token-budget, model, generation-parameter, extraction or verifier change. Any change informed by this episode would be outcome-informed tuning, prohibited by P1 §22, R7 and P-2.
3. Raw counts only (P-3): for T4, `patch_produced` true, `patch_applies` false.
4. Velith main and all frozen P1 artifacts are unchanged.
