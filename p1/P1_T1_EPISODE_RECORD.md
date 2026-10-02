# P1 episode record: T1 `pallets__flask-5014` (2026-10-02)

**Status:** this is the official, one-generation P1 episode for slot T1 (the anchor task). The frozen classification below is final. §3 states only what the preserved evidence supports.

**Evidence:** `p1/evidence/T1/`
- `MANIFEST.sha256` (SHA-256 `b56cfad3d51c3d21…`) lists 21 files; `sha256sum -c` is OK.
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
- the T1 prepare manifest equals `PILOT_SET.json`;
- the in-container Velith module SHAs equal the frozen generation route.

## 1. Identity and generation

| Item | Value |
|---|---|
| instance_id | `pallets__flask-5014` |
| Prompt identity (SHA-256 of prompt UTF-8) | `e2671b01f018f025d04a3b1c5b708cd5eb27ce3c2b75d82a09b93cbf6e2253f8` |
| Seed | `derive_task_seed(identity, 0)` = `940057046043497027` |
| Model | `velith-p1-deepseek-coder-v2:16b-c16384-np1024`. The `/api/tags` digest `e196dcd918e4f54307db79c9fada1ff261c564e1df1624e20ae65d1ff0a4c45c` equals the pin. Ollama 0.34.4. |
| Temperature / context length | **0.0** / **16384**, confirmed by `/api/ps` `context_length` after the call. `num_predict` 1024. |
| Cold start | `/api/ps` was empty before the request |
| Prompt tokens | predicted **15197**, observed **15197**. The token-count assertion holds. Budget 15232. |
| Completion tokens | **87**, so not truncated |
| Generation latency | **910.27 s**. Attempt window 16:53:43Z → 17:08:56Z. |
| Generation attempts | **1**. No retry, no regeneration. |
| Free RAM (Windows) | 17,696,698,368 B before generation; 18,173,263,872 B after unload (`/api/ps` empty) |
| Retrieved files (prompt) | `src/flask/debughelpers.py`, `src/flask/wrappers.py`, `src/flask/scaffold.py`, `src/flask/templating.py`, `examples/celery/src/task_app/views.py` |

## 2. Official frozen outcome (not reinterpreted)

| Layer | Value |
|---|---|
| `patch_produced` | **true** |
| Patch SHA-256 | `3a4bb3927e0149e00f66b8dc142f49cee02e93e004a7f9a8086ce259ddefe9c0`. It is byte-identical to the patch the probe applied (`X-1/candidate/velith/candidate.patch`). |
| Probe classification (`verified_outcome`) | **PATCH_APPLY_FAILED**, reason `CANDIDATE_PATCH_DID_NOT_APPLY`; candidate container exit 92 |
| P1 §18 failure-table code (`code` = `x_code`) | **PATCH_DOES_NOT_APPLY** |
| `patch_applies` | **false** |
| Flags | none. `interpretable` = true. |

**Exact generated patch** (`G/attempt-1/patch.diff`):
```diff
--- a/src/flask/scaffold.py
+++ b/src/flask/scaffold.py
@@ -1,5 +1,5 @@
 import importlib.util
 import os
-from collections import defaultdict
+from collections.abc import defaultdict
 from datetime import timedelta
 from functools import update_wrapper
```
The raw completion is in `G/attempt-1/completion.txt`. It is a single fenced `diff` block with one leading space before the fence. It also ends with a blank context line, which the frozen `_extract_patch` removed when it stripped surrounding whitespace.

**Exact verifier error** (`X-1/candidate/stdout.txt`):
```
error: patch failed: src/flask/scaffold.py:1
error: src/flask/scaffold.py: patch does not apply
```

**Baseline run:**
- It ran with `status` RAN, `network_mode` none, network probe blocked, 4.56 s, and all 60 required IDs mapped.
- **59 of 60 passed.** The one failure is `tests/test_blueprints.py::test_empty_name_not_allowed` (`Failed: DID NOT RAISE <class 'ValueError'>`).
- The probe went on to judge the candidate, which under the frozen `classify` order happens only after these baseline checks pass:
  - every PASS_TO_PASS test passed;
  - no FAIL_TO_PASS test passed.
- So this failing test is the FAIL_TO_PASS test, and its failure is the required healthy-baseline condition.

**Candidate run:**
- It ran with `status` PATCH_APPLY_FAILED (exit 92), `network_mode` none, 1.42 s, on HEAD `966bb873…` whose parent is base `7ee9ceb7…`.
- **The candidate tests did not run.** 0 required IDs were mapped and no pytest exit code was recorded.

## 3. Forensic observations (evidence-limited; not a replacement verdict)

| Failure type | Supported by the evidence? | Basis |
|---|---|---|
| **Patch format / application failure** | **Application failure: yes. Format defect: no.** | The hunk header `-1,5 +1,5` is consistent with the body: 5 old lines (4 context + 1 removed) and 5 new lines (4 context + 1 added). `git apply` did not report `corrupt patch`; it reported `patch failed … :1`, a context mismatch. That is why the frozen code is PATCH_DOES_NOT_APPLY, not MALFORMED_PATCH. |
| **Wrong context** | **Yes (context).** Wrong location: **not assessed.** | `src/flask/scaffold.py` was in the prompt verbatim. In it, lines 1–9 are `import importlib.util`, `import os`, `import pathlib`, `import pkgutil`, `import sys`, `import typing as t`, `from collections import defaultdict`, `from datetime import timedelta`, `from functools import update_wrapper`. Each of the patch's five old-side lines exists in the file, but the patch omits lines 3–6, so its old-side block is not contiguous in the base file and does not match at line 1. The gold patch is not part of the T1 evidence, so this record does not assess whether `scaffold.py` is the right location. |
| **Semantic failure** | **Not assessable** | The patch never applied and no candidate test ran. The F2P test (from `X-1/baseline/velith/test.patch`) asserts that `flask.Blueprint("", __name__)` raises `ValueError`. This record makes no claim on whether the edit would or would not satisfy it. |

## 4. Binding statements

1. **T1 is one-generation evidence (R7). It must not be rerun or regenerated.** This completion and this classification are final for P1.
2. **No post-hoc experiment tuning is authorized:** no harness, prompt, retrieval, token-budget, model, generation-parameter, extraction or verifier change. Any change informed by this episode would be outcome-informed tuning, prohibited by P1 §22, R7 and P-2.
3. Raw counts only (P-3): for T1, `patch_produced` true, `patch_applies` false.
4. Velith main and all frozen P1 artifacts are unchanged.
