# P1 OD-4 — Harness Execution Location: Decision Input (research only)

**Status:** RESEARCH / DESIGN GATE.
- Nothing is implemented and nothing is executed.
- Velith main is read-only at `5452efc`.
- No Ollama, Docker or network configuration change.

**Basis:**
- `M2-PV-P1_PILOT_DESIGN.md` §§14–15, 19–23, 29;
- DECISIONS D13, D16.2, D19, D26, D27, D28;
- `experiments/m2_container_prototype/probe.py` (SHA-256 `560834d5…8e1f`) and its FREEZE_RECORD;
- `src/velith/{llm/client.py, agent/proposer.py, core/config.py, core/logging.py, task.py, harness/verifier_sandbox.py}`;
- Stage-0 evidence §§11–20.

## 1. RD ruling recorded

**OD-4 location = the native Windows host.** The reasons:
- Ollama runs natively there on 127.0.0.1, and Stage-0 used that endpoint.
- WSL cannot reach Ollama.
- No exposure beyond localhost.
- No Docker or WSL networking dependency before P1.
- Docker Desktop stays available from Windows.

## 2. Contradiction check (performed before proceeding)

### K1 — HARD, technical: the frozen M2 probe cannot run unmodified on native Windows.

**Evidence:** `run_container` writes the in-container inputs in text mode, with no `newline=` argument:
```
probe.py:506  (stage / "test.patch").write_text(spec["test_patch"], encoding="utf-8")
probe.py:507  (stage / "candidate.patch").write_text(candidate_patch, encoding="utf-8")
probe.py:509  (stage / "run.sh").write_text(script, encoding="utf-8")
```

**Mechanism:**
- On Windows, Python text mode translates every `\n` to `\r\n`.
- `run.sh` is then executed by `/bin/bash` in a Linux container. Every line ends in `\r`; for example, the first line becomes `cd /testbed\r`, which exits 96.
- The patches carry CRLF, so `git apply` against LF trees fails.

**Consequences:**
- Every run would be misclassified as infrastructure or patch-apply failure.
- The probe's own docstring says "run from WSL", and every M2 evidence run came from a WSL home directory (FREEZE_RECORD §1).
- A secondary Windows issue: `docker()` uses `subprocess.run(..., text=True)` (`probe.py:362–369`), which decodes with the locale code page (cp1252). That can mis-decode or raise on non-ASCII test output.

**Why it is binding:** P1 requires the probe to be imported **unmodified** (`M2-PV-P1_PILOT_DESIGN.md` §15). Therefore **Stage 1 (admission) and Stage X (candidate execution) cannot run on native Windows** without forking or amending the frozen probe.

**Options:**

| Option | Description | Assessment |
|---|---|---|
| **X-a** | Stage 1 and Stage X run from **WSL**, the validated probe location. They use Docker Desktop's engine and do **not** need Ollama. | Recommended. No networking or config change; preserves probe identity and M2 evidence continuity. |
| X-b | Amend or port the probe | Breaks "unmodified" and the M2 freeze lineage. Needs its own validation. |
| X-c | A Windows harness re-implements the probe's file staging | A de-facto probe fork. Rejected, same as X-b. |
| X-d | The harness runs inside a Linux container with the Docker socket | AR-3, rejected by D26. |

**Recommendation — split location:**
- **Stage G (generation) runs on native Windows**, per the RD rationale.
- **Stage 0 (image inventory), Stage 1 and Stage X run in WSL.**
- The stages communicate only through a hashed file handoff on `E:`. This matches the frozen sequential policy: generation first, then verification.
- **This amends the RD ruling. The RD must confirm it.**

### K2 — Governance tension (not a blocker): D13 and D16.2 versus Velith code running on Windows Python.

- D13: "Velith is built on WSL2 + Ubuntu (Linux build/runtime)"; the native-Windows build was rejected. Its rationale is **verifier** reproducibility.
- D16.2 (M1-scoped): "the host Python (3.10) is never an execution target".
- `M2-PV-P1_PILOT_DESIGN.md` §15 proposed Stage G **inside the pinned Velith container** via `host.docker.internal`.
- **Assessment:**
  - Under K1's split, P1 verification stays in Linux containers, so D13's rationale is preserved.
  - Running `ProposerAgent` and `OllamaClient` on Windows Python is a **P1-only operational deviation** from D13's letter for the generation stage.
  - D16.2 is M1-scoped and does not bind P1.
- **Required:** the RD records this explicitly in the P1 design as a scoped, experiment-only choice. In my assessment, no DECISIONS amendment is needed because P1 is not an evaluation of record and changes no Velith build or runtime. If the RD judges the proposer run to be "Velith runtime" in D13's sense, a scoped D13 clarification is required instead.

### K3 — No contradiction.

- D26 and D27 bind the **production** real-task verifier.
- P1 uses the frozen probe and records **probe-level** evidence only (`M2-PV-P1_PILOT_DESIGN.md` §§4, 17; RD-0 Option B).
- The D27 classifier requirements (a hash-locked, Linux-resolved Python 3.12 environment; cross-machine determinism) therefore do not apply to P1.
- D28 D-3 is respected: real-task `Task` instances never reach the legacy `VerifierSandbox`. On Windows that component would fail closed anyway, because `unshare -n` does not exist there (`verifier_sandbox.py:79–95, 242–256`).

### K4 — Forward risk (not P1).

- The BRP and M2-PV production verifier must satisfy D27: a locked, Linux-resolved classifier environment (`constraints/analysis-py312.txt`, resolved in `python:3.12.7-slim-bookworm`).
- The Windows-host choice for P1 **must not be carried forward** to the production orchestrator or classifier without a separate decision.

## 3. Invocation map (under the recommended split)

```
[Windows, native]  Stage G (generation) — P1-G harness (future, research workspace)
  pre-flight:
    GET /api/tags            digest(velith-p1-…) == e196dcd9…c45c, else STOP
    free RAM (GlobalMemoryStatusEx) >= 4 GB, else STOP (not a retry)
    Task.prompt built per OD-1 (M-C) + OD-2 template
    predicted_pec = len(HF.encode("<BOS>User: "+prompt+"\n\nAssistant:", add_special_tokens=False)) + 1
      (tokenizer.json SHA 091b9dad…8714, tokenizers 0.23.2, local file, no network)
    predicted_pec <= 15232, else INADMISSIBLE (never sent)
  call:  ProposerAgent(OllamaClient(host="http://127.0.0.1:11434", timeout_seconds=1800),
                       model="velith-p1-deepseek-coder-v2:16b-c16384-np1024", temperature=0)
         .propose(task, seed=derive_task_seed(identity, 0))   [frozen code, imported unmodified]
  post-call:
    proposal.prompt_tokens == predicted_pec, else INTEGRITY_FAILURE (recorded)
    proposal.completion_tokens == 1024  -> TRUNCATED (OD-3 principle)
    first call only: GET /api/ps context_length == 16384 (F2 runtime acceptance)
  retry: at most 1, only on ModelUnavailableError that is not a timeout (OD-8)
  write: prompt, raw completion, extracted patch (bytes, LF, UTF-8), call record, SHA-256 each
  after all tasks: `ollama stop velith-p1-…` (frees about 19 GB before Stage X; runtime action, not config)

        |  hashed handoff: E:\…\p1-evidence\G\MANIFEST.sha256
        v

[WSL]  Stage 0 / 1 / X — P1-X harness (future, research workspace)
  verify the handoff manifest hash, then read patch bytes unchanged
  import probe.py unmodified (SHA 560834d5…8e1f): load_spec, verify_image,
    run_container(role=baseline|candidate, candidate_patch=<bytes as str>), classify
  Docker Desktop engine (docker CLI in WSL); --network none etc. as frozen in the probe
  evidence: under the evidence root (outside the repository); EVIDENCE_MANIFEST.sha256

[Report]  raw counts and §18 classification only (P-3 rules)
```

**Evidence root:** a single directory outside both repositories, readable from both sides, for example `E:\Projects\OpenSourceLab\p1-evidence\` (`/mnt/e/…` in WSL). Every file is written in binary or with `newline=""` and hashed. Final `EVIDENCE_MANIFEST.sha256`.

## 4. Windows-specific constraints (Stage G on native Windows)

| # | Constraint | Source | Harness rule |
|---|---|---|---|
| W1 | Text-mode newline translation (`\n` → `\r\n`) | Python on Windows; K1 | Every artifact is written as bytes or with `newline=""`. The patch is never re-encoded. |
| W2 | Locale code-page decoding (cp1252) in `open()` and `subprocess(text=True)` | Python on Windows | Run with `PYTHONUTF8=1`. Always pass explicit `encoding="utf-8"`. |
| W3 | Velith requires Python `==3.12.*` | `pyproject.toml` | The Windows host Python is **unknown** [EXT]; D16.2 recorded 3.10. A 3.12 install is a host change needing authorization. |
| W4 | `Settings` reads `.env` from the working directory and `VELITH_*` from the environment. Data paths are relative. | `config.py:37–40, 62–173` | Run from a controlled working directory with no `.env`. Assert that no unexpected `VELITH_*` variables exist. Pass host, model and timeout **explicitly** to the constructors. Never touch the store paths. |
| W5 | The client's default host is `host.docker.internal`; the default timeout is 120 s | `client.py:41–45`, `config.py:54–56` | Construct `OllamaClient("http://127.0.0.1:11434", 1800)` explicitly. |
| W6 | On Windows, `urllib` takes proxy settings from the registry when no `*_proxy` environment variable exists. With a system proxy enabled, `127.0.0.1` is **not** bypassed unless listed in ProxyOverride (`<local>` covers only dot-less hosts). | CPython `urllib.request` | Run with `NO_PROXY=127.0.0.1,localhost` and no `HTTP(S)_PROXY`. The environment then takes precedence, which is deterministic. Registry state is checked read-only [EXT]. |
| W7 | Prompt material bytes (M-C) | OD-1/OD-2 | Material is read from **git objects or image bytes**, decoded UTF-8, and never from a Windows working-tree checkout, where `core.autocrlf` would change bytes and therefore tokens. |
| W8 | Windows path semantics: MAX_PATH 260, case-insensitive, reserved names | Windows | Never materialize task repository trees on NTFS. Read blobs in memory. |
| W9 | Velith source must be byte-identical to the pinned commit, without writing into Velith main | `__pycache__` writes on import | Clone Velith at `5452efc` (or the RD-pinned commit) **outside** Velith main with `-c core.autocrlf=false`. Verify that `git status` is clean and HEAD equals the pin. Run with `PYTHONDONTWRITEBYTECODE=1`. |
| W10 | Tokenizer platform | D-E was demonstrated on Linux (WSL) | Re-run the D-E check on Windows Python (read-only) before relying on it. |
| W11 | Memory co-residency: the model (about 19 GB private), the Docker VM (up to 15.3 GiB) and WSL (16 GB) share 31.3 GiB | Stage-0 §§8, 17 | Stages run strictly in sequence. Unload the model before Stage X. Enforce the ≥ 4 GB guard. Use `GlobalMemoryStatusEx` through `ctypes` (standard library, no new dependency). |
| W12 | Velith logging writes to stdout | `core/logging.py:76–86` | Evidence comes from return values, never from parsing stdout. |

## 5. Implementation boundary for the future harness (not written now)

**Location:** the research workspace, `Velith-research/p1/harness/{g_windows,x_wsl}/`, not Velith main. Files, SHA-256s and the probe SHA-256 are recorded in the evidence (`M2-PV-P1_PILOT_DESIGN.md` §§15, 19).

**May:**
- import `velith.agent.proposer`, `velith.llm.client`, `velith.task`, `velith.batch.provenance.derive_task_seed` (from the pinned clean clone);
- import `probe.py` as a library;
- call Ollama `GET /api/tags` and `/api/ps`, and generation only through `OllamaClient`;
- run `ollama stop` (a runtime action);
- run the Docker CLI through the probe only;
- read the pinned `tokenizer.json`;
- write only under the evidence root.

**Must not:**
- modify, monkeypatch or wrap any frozen Velith or probe symbol, including an injected `transport`;
- write to any Velith store (episodes, index, sink, pre-registration, corpus, TaskSpec registry);
- pass `num_ctx`/`num_predict`/`raw`/`system`/`options` beyond the frozen client's own;
- change Ollama, Docker, WSL or network configuration;
- pull images outside Stage 0;
- put any gold, test or F2P/P2P data in material (§22 leakage audit);
- run a timing experiment.

**Frozen parameters consumed:**
- the model name and D\*;
- R_out 1024, M 128, B_prompt 15232;
- the counting rule with offset +1;
- timeout 1800 s;
- retry ≤ 1 (infrastructure only; never over-budget, timeout or out-of-memory);
- RAM ≥ 4 GB;
- sequential execution.

**Still OPEN before the harness can be written:**
- the RD's confirmation of the split (K1) and the K2 record;
- OD-5, OD-6, OD-9 to OD-12;
- the Python 3.12 install on Windows [EXT];
- Docker disk space on C: (17 GB free) for task images [EXT].

## 6. Read-only reachability check

**Script:** `od4/Probe-OD4-Reachability.ps1`.
- It sends exactly two GET requests (`/api/version`, `/api/tags`), with no generation.
- It asserts version 0.34.4, that the P1 model is present, that the P1 digest is `e196dcd9…c45c`, and that the base digest is `63fb193b…2fa5`.
- It writes `od4/results/od4-reachability-<UTC>.json`.

**Run with:**
`powershell.exe -NoProfile -ExecutionPolicy Bypass -File "E:\Projects\OpenSourceLab\repos\Velith-research\stage0\od4\Probe-OD4-Reachability.ps1"`

**Result: PASS** (RD-executed, 2026-09-30T04:41:24Z; evidence `od4/results/od4-reachability-20260930T044125Z.json`).
- Host LAPTOP-BKSNR343, PowerShell 5.1.26100.9549.
- Reachable: yes. Version: 0.34.4.
- `velith-p1-deepseek-coder-v2:16b-c16384-np1024`: digest `e196dcd918e4f54307db79c9fada1ff261c564e1df1624e20ae65d1ff0a4c45c`, size 8,905,125,714 bytes.
- `deepseek-coder-v2:16b`: digest `63fb193b…2fa5`.
- The `/api/tags` digest equals the manifest SHA-256 pinned in evidence §20.

## 7. RD decisions required

1. **OD-4a:** confirm the split: Stage G on native Windows; Stage 0, 1 and X in WSL (K1). Or choose X-b and accept a probe amendment with re-validation.
2. **OD-4b:** record K2 as a P1-scoped generation-environment deviation, or require a D13 clarification.
3. **OD-4c:** harness code location = the research workspace (recommended) or Velith `experiments/`.
