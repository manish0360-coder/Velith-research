# Stage-0 Timing-Only Experiment — Design (DRAFT, NOT AUTHORIZED, NOT EXECUTED)

**Type:** research design for RD authorization. **No run, no P1, no SWE-bench content, no Docker change, no Velith change.**
**Author:** CSE.
**Date:** 2026-09-29.
**Basis:** Stage-0 evidence §§6–12 (`e2aea559…`); P1 OD-2 (approved) and the OD-3 principles (frozen by the RD); `llm/client.py`, `core/config.py` and `runner/spike.py` at Velith `5452efc`.

## 0. Why this experiment exists

**The OD-3 numeric values** (`num_ctx`, output reserve, margin, retrieval budget) cannot be fixed from the advertised context length (163840). They depend on four behaviours of this host and server:
1. prompt-evaluation throughput;
2. generation throughput;
3. what happens to a prompt longer than the effective context on the frozen client path;
4. the memory cost of a larger `num_ctx`.

**Correction to earlier drafts.** The 120 s timeout is a **default**, not frozen. `Settings.ollama_timeout_seconds` is 120.0 and can be overridden through `VELITH_OLLAMA_TIMEOUT_SECONDS`, and the caller passes it into `OllamaClient` (`runner/spike.py:125–128`). Changing it is a **configuration** decision (OD-7/OD-8), not a code change.

## 1. Questions and measured quantities

| Q | Question | Measured by |
|---|---|---|
| Q1 | Prompt-evaluation rate p (tokens/s) as a function of prompt length L | `prompt_eval_count` and `prompt_eval_duration` on **uncached** prompts |
| Q2 | Generation rate g (tokens/s) | `eval_count` and `eval_duration`, with `num_predict` fixed |
| Q3 | Truncation on the frozen-client path: the effective context when **no `num_ctx`** is sent (expected 4096) | `prompt_eval_count` for an L ≈ 8k prompt sent without `num_ctx`; `done_reason`; truncation lines in `server.log` |
| Q4 | Memory at each `num_ctx` | `/api/ps` (`size`), the load-time KV lines in `server.log`, and the working set of the Ollama process |
| Q5 | Cold load time per `num_ctx` (a `num_ctx` change reloads the model) | `load_duration` |
| Q6 | Prompt-cache effect on `prompt_eval_count`: the OD-3 principle "measure length independently" | an exact repeat of one prompt |
| Q7 | Tokenizer calibration: bytes per token for code on this model | uncached `prompt_eval_count` divided by prompt bytes |

## 2. Synthetic prompts (no task content)

- **Generator:** a deterministic script, fixed and hashed before the run. It emits N synthetic Python functions, for example
  `def f_{i}(x_{i}, y_{i}):` / docstring `"Synthetic function {i}."` / `return (x_{i} * {i%7+1}) + (y_{i} // {i%5+1})`.
- **Cache defeat:** each request starts with a unique **nonce line** (`# nonce: <fixed list entry>`), so no KV-prefix cache is reused, except in the planned Q6 repeat.
- **Instruction tail:** "Continue writing more functions in exactly the same style." This elicits long code-like generation. Content quality is irrelevant.
- **The rendered input** follows the Modelfile TEMPLATE else-branch (`User: …Assistant:`), exactly as on the Velith client path.
- **Targets:** L ≈ 1k, 3.5k, 8k and 16k tokens. Optional: ≈ 30k (§4). N is calibrated from the Q7 ratio measured on the first request. Actual L is always the **measured** uncached `prompt_eval_count`.

## 3. Request settings

| Setting | Value | Reason |
|---|---|---|
| Endpoint | `POST http://127.0.0.1:11434/api/generate`, `stream: false` | The same endpoint as the Velith client |
| Caller | A PowerShell script **on Windows** | The server listens on 127.0.0.1 only and is not reachable from WSL (§6). No Docker is needed. |
| `temperature` / `seed` | 0.0 / 0 | The same as the P1 configuration |
| `num_predict` | 256 | Enough to measure g; bounded runtime |
| `num_ctx` | Omitted for the frozen-path runs; explicit (4096, 16384, and optionally 32768) for the measurement runs | Q3 vs Q1/Q4 |
| Client timeout | 1800 s | Must observe the *true* latency, not cut it at 120 s |
| Recorded per request | Full JSON response (`total_duration`, `load_duration`, `prompt_eval_count`/`_duration`, `eval_count`/`_duration`, `done_reason`), request hash, prompt bytes, wall time; `/api/ps` after the request | — |

## 4. Run sequence (about 11 requests; one sitting)

| # | `num_ctx` | Prompt | Purpose |
|---|---|---|---|
| 0 | omitted | tiny | warm load; server default confirmed |
| 1 | omitted | ≈ 1k, nonce A | Q1/Q2/Q7 baseline |
| 2 | omitted | the same bytes as #1 | **Q6** cache effect |
| 3 | omitted | ≈ 3.5k, nonce B | Q1 near the default limit |
| 4 | omitted | ≈ 8k, nonce C | **Q3** frozen-path truncation probe |
| 5 | 16384 | tiny | reload at 16k: Q4, Q5 |
| 6 | 16384 | ≈ 8k, nonce D | Q1 at 8k (untruncated) |
| 7 | 16384 | ≈ 16k minus 300, nonce E | Q1 at about 16k; Q2 |
| 8 | 16384 | ≈ 8k, nonce F | repeat of #6 for variance |
| 9* | 32768 | tiny | *optional* reload at 32k: Q4 |
| 10* | 32768 | ≈ 30k, nonce G | *optional* Q1 at about 30k |

**Stop rules:**
- Skip #9 and #10 if, after #5, `/api/ps` shows a size above about 16 GB, or available RAM would fall below about 4 GB. These thresholds are proposed operator safety values, not scientific parameters.
- Abort on any error.
- At the end, `keep_alive` is left at the server default. No model is deleted.

## 5. Outputs (evidence only; no OD-3 values chosen)

- p(L), g, load(`num_ctx`) and memory(`num_ctx`).
- The Q3 truncation behaviour.
- The Q6 cache delta.
- The Q7 bytes/token ratio.
- A latency model T(L, G) ≈ load + L/p(L) + G/g, from which the RD can read the feasible (L, G, timeout) region for OD-3/OD-7.

## 6. Invariants

- No SWE-bench, pilot or held-out content.
- No write to Velith, memory, episodes or the evaluation sink.
- No Docker action.
- No model pull, create, copy or delete.
- No server-configuration change.
- Evidence goes to `Velith-research/stage0/timing/`, along with the script and its SHA-256.
