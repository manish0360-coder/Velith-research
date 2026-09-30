# P1 OD-3 / OD-7 / OD-8 — Freeze Decision Input (research; NO values chosen)

**Basis:** Stage-0 evidence §§11–17 (`STAGE0_INVENTORY_EVIDENCE_2026-09-29.md`, SHA-256 `5ddb413f…`).

**Frozen:**
- OD-1 = M-C;
- OD-2 template;
- the OD-3 principles;
- **OD-3 context regime = 16384**;
- sequential generation and task-container execution.

**Model:** `deepseek-coder-v2:16b` (digest `63fb193b…`), Ollama 0.34.4, CPU only.

## 1. Measured facts the values must respect

| Quantity | Value | Source |
|---|---|---|
| Over-context prompt | Rejected with HTTP 400 (not truncated) | §14 |
| Model memory at 16384 | 13.63 GB (`/api/ps`). The `llama-server` working set was 13.7–15.0 GB and private bytes up to 19.2 GB. | §§14–17 |
| Cold load at 16384 | 17.8 s | §14 |
| Cold prompt evaluation | 1,752 tok: 64–67 s; 3,467: 136–143 s; 8,188: 376.5 s; **16,108: 961 s**. Fit: t(P) ≈ 0.0331·P + 1.65e-6·P² s. | §§13–17 |
| Generation rate | about 3.1 tok/s at 8k; 1.75–2.69 tok/s at 16k | §§14–17 |
| Measured near-max request (16,108 + 256) | **1,108.9 s wall** | §17 |
| `num_predict` = 256 | Hit the limit (`done_reason` = length) on every request | all |
| Frozen Velith client | Sends **no** `num_ctx` and **no** `num_predict` (`llm/client.py:98–104`). The timeout defaults to 120 s and is configurable through `VELITH_OLLAMA_TIMEOUT_SECONDS`. | code |

## 2. Decisions required (the RD decides)

| ID | Decision | Options (evidence-based consequences) |
|---|---|---|
| **D-A** | **Mechanism that applies 16384 and the output reserve on the Velith path** | **(a) A derived Modelfile** (`FROM deepseek-coder-v2:16b`, `PARAMETER num_ctx 16384`, `PARAMETER num_predict <R_out>`), used through `VELITH_OLLAMA_MODEL`. It is a distinct, recordable model identity that sets both values; creating it is a host change (`ollama create`, reusing the existing blobs). **(b) `OLLAMA_CONTEXT_LENGTH=16384`** at server level. It sets the context only and affects all models, so R_out stays unenforced unless it is also set elsewhere. *The server's default `num_predict` when none is sent is not verified on this host (EXT).* |
| **D-B** | **Output reserve R_out** (`num_predict`) | Generation time at 16k is about R_out / (1.75–2.69) s: 256 → 95–147 s; 512 → 190–293 s; 1024 → 381–586 s. A larger R_out lowers the risk of truncated diffs but raises latency and lowers the prompt budget. |
| **D-C** | **Margin M** | Covers counting uncertainty only. Template and BOS tokens are already inside the measured counts; the synthetic token model was exact (difference 0) at 1.7k, 3.5k, 8.2k and 16.1k. The margin size depends on D-E. |
| **D-D** | **Prompt budget B_prompt** | B_prompt = 16384 − R_out − M, derived once D-B and D-C are set. |
| **D-E** | **Pre-flight token-counting mechanism** (OD-3 principle: count the prompt independently of `prompt_eval_count`) | (i) the Hugging Face DeepSeek-Coder-V2-Lite tokenizer, validated against the measured counts; (ii) the GGUF-embedded tokenizer through llama.cpp tooling; (iii) an Ollama tokenize endpoint, if 0.34.4 has one (EXT). An exact counter permits a small M; an estimate needs a large M. |
| **OD-7** | **Client timeout** | Worst case ≈ cold load (18 s) + t(B_prompt) + R_out / g_min. At B_prompt ≈ 16k: 256 → about 1,125 s; 512 → about 1,270 s; 1024 → about 1,565 s. It must exceed the chosen worst case with headroom. The 120 s default fits only prompts of about 1.5k tokens. |
| **OD-8** | **Retries** | The P1 proposal is up to 2 retries, on GEN_INFRA only. Each retry at the maximum costs another about 19–26 min. An over-budget prompt must never reach the server, since pre-flight blocks it (a 400 would otherwise surface as GEN_INFRA). |
| **Memory precondition** | Free RAM before the P1 generation stage | S2b started with only 2.55 GB free and generated more slowly than S1 (4.43 GB free). A pre-flight free-RAM floor for the generation stage is a candidate. The value is the RD's. |

## 3. Dependencies

D-A → D-B (enforced only via Modelfile or the request) → D-E → D-C → D-D → OD-7 → OD-8. D-A needs its own host-change authorization.

## 4. RD FREEZE DECISION (2026-09-30), recorded verbatim in substance

| ID | Frozen value | Condition |
|---|---|---|
| D-A | A derived Ollama model identity from `deepseek-coder-v2:16b`, with `num_ctx` 16384 and `num_predict` 1024 | It is **not created** until the D-E check passes. |
| D-B | Output reserve R_out = 1024 | — |
| D-E | The offline Hugging Face tokenizer is the authoritative pre-send counter | Only after the read-only equivalence check on all 4 measured prompts passes |
| D-C | Margin M = 128 | Only if the D-E check passes |
| D-D | Prompt budget B_prompt = 16384 − 1024 − 128 = **15232** | — |
| OD-7 | Client timeout 1800 s | — |
| OD-8 | At most 1 retry, for infrastructure failures only | Never for over-budget, timeout or out-of-memory failures |
| Memory | At least 4 GB free RAM before generation | An engineering safety guard, not an estimated threshold |
| Execution | Generation and verifier run sequentially | — |

**Prohibited for now:** another timing experiment, creating the derived model, changes to Velith main, changes to Docker.

## 5. CSE findings after the ruling (read-only)

**F-1: ground truth is the exact token IDs, not just counts.** Every measured response's `context` holds the server's prompt token IDs. They are frozen in `tokenizer/server_truth_manifest.json`.

**F-2: the reported count is one more than the stored prompt tokens.** `prompt_eval_count = len(prompt IDs in context) + 1` on **all 7** measured prompts (180 to 16,108 tokens). The cause of the +1 has **not** been determined. Consequence: the counting rule binds on the server's `prompt_eval_count`, so the offset must be part of the frozen counting rule. The check measures it.

**F-3: §12 used the wrong template branch.** Its derivation said a prompt-only request renders the template's *else* branch. The observed token streams contradict that:
- they begin `100000` (BOS), then `5726, 25` ("User", ":");
- they end `…, 13, 185, 185, 185, 77398, 25` ("Assistant", ":");
- the prompt file ends with a single `\n`, so three consecutive 185 tokens are consistent with the **Messages branch**: `<BOS>User: {prompt}\n\nAssistant:`.

That reading is an inference: it takes 185 to be `\n` and assumes no newline merging. The check tests all three renderings and settles it.

**F-4 (D-F, new; blocks creation): the stop policy against the frozen OD-3 principle "no silent truncation".**
- The base model's stops are `User:` and `Assistant:`.
- As far as I know, Ollama stops match any substring of the generated text. This has not been observed on this host.
- A correct patch containing, for example, `-> User:` or `class User:` would be cut off at that point, and the response gives `done_reason` "stop", indistinguishable from a normal end.
- **Options:**
  - **F1** keeps the base stops. This is what the Modelfile draft does. It accepts the risk, and the harness classifies a diff without its closing fence as MALFORMED.
  - **F2** anchors the stops to the start of a line: `"\nUser:"` and `"\nAssistant:"`. No unified-diff line can begin with `User:`, because every diff line starts with `+`, `-`, a space, `@` or `\`, so these stops can never fire inside a diff. They still catch a hallucinated next turn.
  - F2 should be created through `/api/create` with JSON parameters, because the JSON gives exact `\n` escaping. The Modelfile parser's escape handling is unverified.
- **CSE recommendation: F2.** Post-creation verification must confirm the parameter layer holds exactly `{"num_ctx":16384,"num_predict":1024,"stop":["\nUser:","\nAssistant:"]}`.

**F-5: which Velith setting carries the model name is undecided (OD-4 scope).**
- Velith has two model settings: `ollama_model` (`VELITH_OLLAMA_MODEL`) and `batch_base_model` (`VELITH_BATCH_BASE_MODEL`). Which one the P1 harness passes to `generate(model=…)` is decided by the harness (OD-4).
- The default `ollama_host` is `host.docker.internal:11434`, while Ollama listens only on 127.0.0.1. Container-to-host reachability is an OD-4 item.

## 6. Identity and pinning plan (for after D-E passes and D-F is ruled)

1. **Guard before creation (read-only).** `ollama list` shows the base ID `63fb193b3a9b`. The base manifest's layers are unchanged: weights `5ff0abee…d046`, template `22091531…4914`, parameters `19f2fb9e…968d`.
2. **Create.** One command. It reuses the existing weights blob, so it downloads nothing and copies nothing. The Modelfile or JSON body is stored in `stage0/model/` with its SHA-256.
3. **Verify after creation (read-only).**
   - `ollama show <name> --modelfile`, `--parameters` and `/api/show`.
   - The derived manifest must reference the same weights blob and the same template layer, have no SYSTEM layer, and carry exactly the expected parameter JSON.
   - Record the derived manifest digest **D\***, the `ollama list` ID.
4. **Pin.** P1's pre-registration records:
   - the name, D\*, the Ollama version (0.34.4) and the base digest;
   - for the tokenizer: the HF commit, the `tokenizer.json` SHA-256, the `tokenizers` version, the rendering configuration and the offset;
   - B_prompt 15232, R_out 1024, M 128 and timeout 1800.
5. **Runtime assertions in P1's pre-flight.**
   - The `/api/tags` digest for the name equals D\*.
   - After load, `/api/ps` shows `context_length` 16384.
   - Predicted `prompt_eval_count` ≤ 15232, or the request is not sent.
   - Free RAM ≥ 4 GB.
   - After each call, the observed `prompt_eval_count` equals the prediction. Any mismatch is a recorded integrity failure.
   - Any change in identity invalidates P1.

## 7. D-E check result (evidence §19): PASS, so the D-E and D-C conditions are met

**Counting rule, now determined by evidence:**

`predicted_prompt_eval_count = len(HF.encode("<｜begin▁of▁sentence｜>User: " + P + "\n\nAssistant:", add_special_tokens=False)) + 1`

A request is sent only if this is ≤ **15232**.

**Pin:** HF commit `e434a23f…3a11`, `tokenizer.json` SHA-256 `091b9dad…8714`, `tokenizers` 0.23.2.

**Required P1 runtime assertion:** after each call, the observed `prompt_eval_count` must equal the prediction. This covers the untested non-ASCII and real-content scope; any mismatch is a recorded integrity failure.

**Still blocking model creation:**
- D-F (stop policy, §5 F-4);
- RD authorization for the host `create` action.

The F2 body is drafted in `model/P1_DERIVED_MODEL.F2.create.json`; F1 is in `model/P1_DERIVED_MODEL.Modelfile.DRAFT`.

## 8. F2 status (evidence §20): creation and static identity COMPLETE; runtime acceptance pending

**Pinned model identity for P1:**
- name `velith-p1-deepseek-coder-v2:16b-c16384-np1024`;
- manifest D\* = `e196dcd918e4f54307db79c9fada1ff261c564e1df1624e20ae65d1ff0a4c45c`;
- params blob `6ba30c69…0182`, content `{"num_ctx":16384,"num_predict":1024,"stop":["\nUser:","\nAssistant:"]}`;
- weights `5ff0abee…d046`; template `22091531…4914`;
- Ollama 0.34.4.

**Runtime acceptance, to be checked at the first authorized P1 generation call:**
- `/api/ps` shows `context_length` = 16384;
- `completion_tokens` ≤ 1024;
- observed `prompt_eval_count` = predicted count (§7 rule).

**Frozen-client compatibility (read-only review of `llm/client.py`):**
- The `Completion` object exposes `prompt_tokens` (= `prompt_eval_count`) and `completion_tokens` (= `eval_count`). Both the OD-3 truncation rule (`completion_tokens` == 1024) and the post-call count assertion can therefore be implemented **without modifying the client**.
- The client does not expose `done_reason` or the model digest. The digest check must run in the harness's pre-flight through `/api/tags`.
