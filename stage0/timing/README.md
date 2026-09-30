# Stage-0 timing-only experiment — scripts (NOT EXECUTED)

**Status:** implemented under RD approval, which covers script creation only. **Not run.** Running requires a separate RD authorization.
**Design:** `../TIMING_EXPERIMENT_DESIGN_DRAFT.md`.

| File | Purpose |
|---|---|
| `Stage0SyntheticPrompt.ps1` | A deterministic generator of ASCII synthetic Python prompts (no project or benchmark content). It defines functions only. |
| `Invoke-Stage0Timing.ps1` | The Windows PowerShell 5.1 runner. It uses only the running local Ollama server and writes evidence under `runs\`. |

**File hashes (SHA-256), revision R2:**

| File | SHA-256 |
|---|---|
| `Invoke-Stage0Timing.ps1` | `ce2fb7f62d79535ca812646b10461bb55185ba1e396859ea31f3caf5d57dd00d` |
| `Stage0SyntheticPrompt.ps1` | `3d9fc3ffe012e7d5f52609c51703d122d9820ffa47645266c331cd6c5e6f63a1` |

**Revision R1 (RD-requested robustness fix).**
- **What changed:** `/api/generate` failures are now captured by `Invoke-GenerateCapture`. The HTTP status, error message and error body are saved to `raw/NN_error.json` and to the request record. The CSV gains `http_status` and `q3_outcome`.
- **Run #4 (the Q3 truncation probe):** a failure is recorded as `q3_outcome = GENERATE_FAILED_OBSERVED`, and the run continues with #5.
- **Every other run:** a failure is recorded first, and then the run aborts as before.
- **Unchanged:** sequence, model, seeds, context sizes, timeout, stop rules and OD-3 logic.
- **Superseded runner:** SHA-256 `0fdd8b3eeafd247f14668be3bfd2c4554ca1e9af1288d017df193184785eaa8f` (R0).

**Revision R2 (server-evidence capture; RD-requested after R0 found `server.log` empty for the run window).**
- **Why:** R0/R1 captured log lines by line count from a single `server.log`. The server that answered R0 did not write to that file (93 lines, none in the R0 window).
- **What R2 does:**
  - selects log lines by **timestamp window** (run start − 5 s to run end + 5 s) across **all** `%LOCALAPPDATA%\Ollama\server*.log` files, plus `-ServerLog` if given;
  - carries untimestamped loader lines along with the preceding timestamped line;
  - records a size and last-write snapshot of each file before and after;
  - records the identity of the server processes (`ollama.exe`, `ollama app.exe`, `llama-server.exe`: PID, parent, creation time, command line) before and after;
  - sets `server_log_status` to `CAPTURED`, `NO_LINES_IN_WINDOW` or `ERROR`.
- **Log capture is never fatal.**
- **The R1 `/api/generate` error capture** (status and body) is unchanged and remains the primary Q3 evidence.
- **Unchanged:** sequence, model, seeds, context sizes, timeout, stop rules and OD-3 logic.
- **Superseded runners:** R1 `0510280e893638f2e34fdc4a2e74c7d9fd8e322960016f45682937fa56244615`.

**Supplemental S1 (`Invoke-Stage0Supplemental16k.ps1`, SHA-256 `75ce8bee5f17fc88d4c48090342805385b92ef1e6dec7a8a091f96202964ca2f`).**
- **What it is:** a separate script that sends **one** request. It does not change R2.
- **Prompt:** N = 304 synthetic functions, nonce `stage0-H`, 29,295 bytes, SHA-256 `f7a55df3…2bbd`.
- **Tokens:** predicted prompt tokens are 16,108, from the exact token model fitted to the measured R0/R2 counts. With the 256-token generation reserve the total is ≤ 16,364 of the 16,384 context.
- **Settings:** `num_ctx` 16384, T = 0, seed 0, `num_predict` 256, 1800 s timeout.
- **Safety:** refuses a cold load when free RAM is below 16 GB.
- **Not run.**

**Supplemental S2 — cold (`Invoke-Stage0Supplemental16kCold.ps1`, SHA-256 `fbcba5ef7979d60beda8ef78a31e0c63ba62dfd995e94d4992df4fa05b926281`).**
- **What it is:** S1 with a **fresh nonce** `stage0-J` (N = 304, 29,295 bytes, prompt SHA-256 `977f1602…a9aa`; predicted prompt tokens 16,108). It measures the **cold** 16k prompt-evaluation time that S1's cache contamination left open.
- **Contamination guard:** it refuses a real run if any earlier `supp16k-cold-2*` attempt directory exists.
- **Settings:** identical to S1.
- **Not run.**

**S2 status: VOID.** The only real attempt, `supp16k-cold-20260929T173106Z`, has pre-flight files only and no record. The model was resident at 16384, so the `stage0-J` prefix may be partly cached. The guard correctly blocked every re-attempt.

**Supplemental S2b — cold, revision (`Invoke-Stage0Supplemental16kColdK.ps1`, SHA-256 `048f12c8efa14fd3ae7194a1bd83274f2455f04d5020d898f49ddbd3b2e4ac1f`).**
- **Prompt:** nonce `stage0-K` (never sent), N = 304, 29,295 bytes, prompt SHA-256 `0b5e444b…5189`; predicted prompt tokens 16,108.
- **Run directories:** prefix `supp16k-coldK-`, with the guard scoped to `supp16k-coldK-2*`.
- **New:** `S2_generate_sent.json` is written immediately before `/api/generate`, so a future interrupted attempt proves whether the request was sent.
- **Settings:** otherwise identical to S2 and S1.
- **S2b status: COMPLETED.** Run `supp16k-coldK-20260929T175204Z`: HTTP 200, 16,108 prompt tokens (difference 0), cold prompt evaluation 960.95 s, wall 1108.9 s. See evidence §17. No further timing runs are planned.

**Generator self-test.** The expected values were computed by an independent Python mirror of the generator. The runner aborts if either does not match.

| Nonce | N | Bytes | SHA-256 |
|---|---|---|---|
| `selftest` | 3 | 421 | `373e3a2d5b3e87e4aa80938ea9deb86a3e30b63d8578fa6b7ccdc56df1d8569b` |
| `selftest` | 50 | 4703 | `702e97ea14f7d3d9f6c7257230b51b83ebaa4b1d4e3db1cf60a3e1023569b673` |

**Verify the file hashes before any run (Windows PowerShell):**
```powershell
Get-FileHash -Algorithm SHA256 "E:\Projects\OpenSourceLab\repos\Velith-research\stage0\timing\*.ps1"
```

**Commands. Do not run without RD authorization.**
```powershell
# 1) Dry run: no network; builds prompts and hashes only
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "E:\Projects\OpenSourceLab\repos\Velith-research\stage0\timing\Invoke-Stage0Timing.ps1" -DryRun
# 2) The timing experiment
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "E:\Projects\OpenSourceLab\repos\Velith-research\stage0\timing\Invoke-Stage0Timing.ps1"
```

`-ExecutionPolicy Bypass` applies to that single process only. It does not change the persistent policy.
