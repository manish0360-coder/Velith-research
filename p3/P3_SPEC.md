# M2-PV-P3: generator capability probe (SPECIFICATION DRAFT, for RD ratification)

**Status:** DRAFT. Nothing runs before FG-0 (ratification) through FG-3.
**Predecessor:** P2 (`ec88462`, P2-B).
- Under the oracle-file condition, the pinned local model applied 3–4 of 13 patches and solved **0/13** tasks.
- **0 of 9** FAIL_TO_PASS tests passed among the patches that applied.

## 1. Question and why it matters

Does a frontier API model, under **exactly** P2's U-arm condition, solve enough tasks to make the Stage-1 compounding experiment informative?

At a verified-success rate of 0, the A0, A1 and A2 memory arms cannot differ (a floor effect). So Stage 1 needs a generator with a non-zero base rate.

## 2. Design (one variable changed: the generator)

| ID | Decision (proposed) |
|---|---|
| D1 Population | The 13 frozen P2 tasks, slots P2-01 … P2-13, in PILOT_SET `44b88412` order. No admission; no new tasks. |
| D2 Prompt | `p2/evidence/P2-NN/P/prompt_U.txt`, **byte-identical**, SHA equal to the PILOT_SET `identity.U`. Sent as one user message, with no system prompt. |
| D3 Generator | Anthropic Messages API, model **`claude-opus-5-5`** (pinned string; the response `model` field is recorded). `temperature` 0 *(superseded by A-1)*, `max_tokens` **1024** (equal to P2 `num_predict`), no tools, no extended thinking. |
| D4 Extraction | The frozen Velith `_extract_patch`, executed inside `velith-verifier:m0` with `--network none`. The `proposer.py` SHA must equal the PILOT_SET pin `91d32296…`. |
| D5 Gate and tests | The same frozen probe, via P1 `stage_x` (case label `P3-X`). Stage-X timeout from PILOT_SET. Re-pull by digest, check identity (D7 rule from P2 §12), delete the image afterwards. |
| D6 Arms | One arm (U, Velith's contract). P2 showed no evidence for S. |

## 3. Endpoints

- **Primary: VERIFIED_PASS.** Probe classification PASSED (ALL_REQUIRED_PASSED) on a patch that passed the gate.
- **Secondary: PATCH_APPLIES** (P2 §7 rule).
- **Diagnostics:** P2 §15 layer codes (U column); FAIL_TO_PASS and PASS_TO_PASS counts; `stop_reason`; token usage.

## 4. Pre-declared decision rule

Let k = the VERIFIED_PASS count over valid tasks (n_v; NA excluded).

| Code | Condition | Decision |
|---|---|---|
| P3-A | n_v ≥ 10 and **k ≥ 3** | The capability floor is lifted. Design the Velith provider interface and run Stage 1 with this generator. |
| P3-B | n_v ≥ 10 and k = 2 | Inconclusive. The RD decides. |
| P3-C | n_v ≥ 10 and **k ≤ 1** | The floor persists even for a frontier model. The next lever is the task setup (feedback loop or easier tasks), not the generator. |
| P3-D | n_v < 10, or unresolved infrastructure failures on ≥ 3 tasks | Not interpretable. |

The threshold 3/13 is an engineering threshold, not a significance test. It says the base rate is clearly above zero for this population.

## 5. Execution rules

- **One generation per task; never rerun.** The raw HTTP response is persisted before interpretation.
- **Generation retries:** at most one retry, and only when no completion was received (transport error, HTTP 429, 5xx, `overloaded_error`). Never after a completion. Never after `stop_reason = max_tokens`.
- **Stage-X retry:** P2 §14 rule (at most one fresh container, on INFRA_ERROR before the gate or BASELINE_UNHEALTHY).
- **Determinism:** no seed is sent, and under A-1 no temperature either (provider default sampling). Outputs are not reproducible. Single-attempt evidence only.
- **Secret handling:** the API key is read only from the `ANTHROPIC_API_KEY` environment variable (set by the RD). It is never written to evidence or logs.
- **Storage gate:** before every pull, free space must be at least 2.5 × compressed size + 10 GB (P1 per-pull rule).

## 6. Threats

| ID | Threat | Treatment |
|---|---|---|
| T-1 | **Contamination.** SWE-bench Verified is public, and a frontier model may have seen the fixes. | VERIFIED_PASS is an **upper bound** on genuine capability. It remains adequate for the D-rule, because Stage 1 compares memory arms *under the same generator*. Stated in the report. |
| T-2 | The 1024-token cap may truncate a verbose model. | Kept for one-variable comparability with P2; `stop_reason` is recorded per task. |
| T-3 | Oracle file context (no localization). | Same scope as P2; no end-to-end claim. |
| T-4 | n = 13; single host; single attempt. | Feasibility framing. |
| T-5 | A different provider and serving stack, not Ollama. | The research harness calls the API directly. Velith main is untouched; integration is a later, separate milestone. |

## 7. Evidence

```
p3/evidence/P3-NN/
  G/attempt-n/  request.json (no key), response_raw.json, completion.txt, result.json
  E/            extract.json (container result), patch.diff
  X-U-1/, X-U-2/  probe evidence (P2 directory convention, reused code)
  episode.json  MANIFEST.sha256
p3/evidence/_preflight/  token counts (count_tokens API; no generation), extractor check
p3/P3_REPORT.md
```

## 8. Freeze gates

| Gate | Content | Pass |
|---|---|---|
| FG-0 | RD ratifies D1–D6, §4 and §5 (model string, max_tokens) | Recorded |
| FG-1 | `p3/harness` synthetic tests; ruff | All pass |
| FG-2 | `preflight`: PILOT_SET and prompt SHAs; extractor container check (network none); `count_tokens` for 13 prompts (no generation); key present | PASS written once |
| FG-3 | Commit spec + harness + preflight | Pushed; RD go |

*No model generation before FG-3.*

## Amendment A-1 (2026-10-11, before any generation)

**What happened:** the first `run` call for P3-01 was rejected with HTTP 400 `invalid_request_error`: "`temperature` is deprecated for this model". No completion was produced and no attempt was consumed (`p3/evidence/P3-01/G/fatal-1-*.json`).

**Change:** `temperature` is omitted, so the provider's default sampling applies. Everything else in D3 is unchanged.

**Validity:**
- The P3 question (does the generator lift the floor) does not depend on greedy decoding.
- Single-attempt, never-rerun evidence was already required (§5).
- This is a recorded difference from P2 (temperature 0 there).
- FG-2 preflight remains valid: `count_tokens` never sent `temperature`, and the extractor is unchanged.
- Each episode records the harness SHA-256 that produced it.
