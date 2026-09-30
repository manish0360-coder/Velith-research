# STAGE-0 INVENTORY — READ-ONLY EVIDENCE (M2-PV-P1)

**Status:** evidence only. **It contains no design decisions, no chosen values and no OD rulings.**
**Authority:** RD authorization of a read-only Stage-0 inventory, 2026-09-29.
**Collected by:** CSE, 2026-09-29.
**Methods:** unauthenticated public APIs read through the built-in browser; no downloads, pulls, model runs or container starts:
- GitHub git-trees API (recursive) at each base commit;
- Docker Hub tags API;
- Ollama library page;
- Hugging Face model API.

**Not collectable from the CSE sandbox:** the execution host (CPU, RAM, GPU, Docker, local Ollama). These facts are collected by the RD-run read-only script `stage0_inventory_readonly.sh` (SHA-256 `e95ea5a0…5850`), kept in the RD project folder outside both repositories.

**Labels used:**
- **OBSERVED** = returned by the API;
- **DERIVED** = arithmetic on observed values;
- **EXT** = still requires host observation.

---

## 1. Container images (OBSERVED, Docker Hub, tag `latest`, 2026-09-29)

| Task | Image | OCI index digest | linux/amd64 manifest digest | Compressed size | Last pushed |
|---|---|---|---|---|---|
| T1 | `swebench/sweb.eval.x86_64.pallets_1776_flask-5014` | `sha256:bde4fbda…ca5d72` | `sha256:eaf597005c159361cb8ee26018fb3741b320f331065f0c95726d83ccf2f1fba4`, **equal to the digest verified in M2** | 1,145,538,311 | 2026-08-13 |
| T2 | `…matplotlib_1776_matplotlib-24570` | `sha256:b223a057…223182` | `sha256:5d93272292526ed727fdbf8fcad24e751965c5d62d66f91c64be7119339b323c` | 3,137,932,335 | 2026-08-13 |
| T3 | `…scikit-learn_1776_scikit-learn-14629` | `sha256:66bce6f5…adc9` | `sha256:de0579911863656a0331adc8d2dd6080ccc2543d0a5fd2bd68d753c8df1ec7c8` | 1,495,941,692 | 2026-08-13 |
| T4 | `…astropy_1776_astropy-7336` | `sha256:7cc2c89f…cfcc6` | `sha256:481ebd12ef496853db01765b1dd57d9aebdedd056c22656b9f483fc1c8379da9` | 1,113,006,597 | 2026-08-13 |
| T5 | `…pydata_1776_xarray-6721` | `sha256:6397b462…a5bf` | `sha256:58c7f4ada7f3cbcfcde50e0b55157701100cf694faa87978c672e368c0531898` | 1,925,618,712 | 2026-08-13 |

- **DERIVED:** total compressed size is about 8.8 GB.
- **EXT:** whether each image is present locally on the host, and its local `RepoDigests`.

## 2. Repository trees at base commit (OBSERVED, GitHub; `truncated: false` for all five)

**Classification used for counting.** This is a counting lens only; it is **not** a pool or exclusion policy.
- **test:** a `.py` file under a path component `test`, `tests` or `testing`, or named `test_*.py`, `*_test.py` or `conftest.py`;
- **vendored:** under `extern`, `externals`, `_vendor`, `vendor`, `vendored`, `third_party`, `cextern`, `_externals`, `build` or `dist`;
- **non-library:** top-level `docs`, `doc`, `examples`, `benchmarks`, `asv_bench`, `tools`, `ci`, `tutorials`, `plot_types`, `properties`, `licenses`, `build_tools`, `maint_tools`, `astropy_helpers`;
- **remainder:** every other `.py` file.

| | T1 flask | T2 matplotlib | T3 scikit-learn | T4 astropy | T5 xarray |
|---|---|---|---|---|---|
| Base commit | `7ee9ceb7…` | `8f0003ae…` | `4aded39b…` | `732d89c2…` | `cc183652…` |
| Blobs (all files) | 251 | 4,417 | 1,213 | 1,810 | 312 |
| `.py` files | 80 | 905 | 739 | 710 | 166 |
| Test `.py` | 47 | 123 | 214 | 311 | 55 |
| Vendored `.py` | 0 | 0 | 9 | 14 | 0 |
| Non-library `.py` | 11 | 607 | 296 | 14 | 24 |
| **Remainder `.py`** | **22** | **175** | **220** | **371** | **87** |
| Remainder bytes | 321,579 | 4,953,229 | 4,327,363 | 5,142,469 | 2,320,741 |
| Remainder p50 / p90 / max bytes | 7,643 / 33,532 / 88,074 | 12,273 / 71,398 / 323,835 | 13,248 / 53,742 / 113,487 | 5,504 / 38,694 / 134,985 | 12,388 / 53,514 / 326,710 |
| Largest remainder files | `src/flask/app.py` 88,074; `scaffold.py` 35,380; `cli.py` 33,532 | `lib/matplotlib/axes/_axes.py` 323,835; `axes/_base.py` 177,707; `patches.py` 161,098 | `sklearn/preprocessing/data.py` 113,487; `ensemble/gradient_boosting.py` 99,733; `utils/estimator_checks.py` 98,008 | `astropy/modeling/core.py` 134,985; `wcs/wcs.py` 123,941; `io/votable/tree.py` 122,127 | `xarray/core/dataset.py` 326,710; `core/_reductions.py` 226,655; `core/dataarray.py` 196,980 |
| Vendored directories seen | — | `extern/` (top level) | `sklearn/externals` | `astropy/extern`, `cextern` | — |

**Observed remainder members that the counting lens does not flag but that are test- or build-related:**
- T2: `tests.py` (root test runner), `setup.py`, `setupext.py`.
- T3: 19 package-level `setup.py` build scripts.
- T5: `xarray/testing.py` (public test helpers, 14,401 bytes), `setup.py`, `xarray/static/…`.

## 3. Test files and configuration candidates (OBSERVED)

| Task | Official test file(s) (P1 §8) | Present at base? | Size (bytes) | `conftest.py` files in the test directory chain | Root / global config files present |
|---|---|---|---|---|---|
| T1 | `tests/test_blueprints.py` | yes | 28,799 | `tests/conftest.py` (5,265) | `pyproject.toml` (2,556), `tox.ini` (1,281). **No** `setup.cfg` or `pytest.ini`. |
| T2 | `lib/matplotlib/tests/test_offsetbox.py` | yes | 11,839 | `lib/matplotlib/tests/conftest.py` (119) | `pytest.ini` (446), `setup.cfg` (132), `pyproject.toml` (152), `tox.ini` (583), `.coveragerc` (227), `setup.py` (13,711). Also `lib/matplotlib/testing/conftest.py` (5,177), a test-support module outside the chain. |
| T3 | `sklearn/tests/test_multioutput.py` | yes | 20,072 | `sklearn/conftest.py` (592); root `conftest.py` (2,968); **no** `sklearn/tests/conftest.py` | `setup.cfg` (716), `.coveragerc` (121), `setup.py` (11,002) |
| T4 | `astropy/units/tests/test_quantity_annotations.py`, `…/test_quantity_decorator.py` | annotations: **absent at base** (created by the test patch); decorator: yes | —; 8,732 | `astropy/conftest.py` (1,127); root `conftest.py` (159) | `setup.cfg` (762), `setup.py` (4,623). Test-support package `astropy/tests/` includes `pytest_plugins.py`, `helper.py`, `runner.py`, `disable_internet.py`. |
| T5 | `xarray/tests/test_dataset.py` | yes | 256,378 | `xarray/tests/conftest.py` (169); root `conftest.py` (1,232) | `setup.cfg` (7,364), `pyproject.toml` (220), `.coveragerc` (163), `setup.py` (103) |

## 4. Prompt-size-relevant facts

**OBSERVED sizes:**
- `problem_statement` lengths in characters (P1 §8): T1 195, T2 1,356, T3 1,814, T4 1,572, T5 9,276.
- Gold-edited file sizes. **These are gold-derived, recorded only for the feasibility of whole-file inclusion, and must not be used to tune retrieval.**
  - T1: path not recorded in P1 §8; `src/flask/blueprints.py` is 24,356 bytes, **unconfirmed as the gold file**;
  - T2: `lib/matplotlib/offsetbox.py` 53,772;
  - T3: `sklearn/multioutput.py` 26,006;
  - T4: `astropy/units/decorators.py` 8,637;
  - T5: `xarray/core/common.py` 70,806.

**DERIVED token estimates.** These use an assumed 3–4 bytes (or characters) per token and are **not tokenizer-measured**:
- Problem statements: T1 ≈ 49–65; T2 ≈ 339–452; T3 ≈ 454–605; T4 ≈ 393–524; T5 ≈ 2,319–3,092 tokens.
- Gold-edited files: T1 ≈ 6.1k–8.1k; T2 ≈ 13.4k–17.9k; T3 ≈ 6.5k–8.7k; T4 ≈ 2.2k–2.9k; T5 ≈ 17.7k–23.6k tokens.
- Remainder medians: ≈ 1.4k–4.4k tokens per file across tasks.
- Largest files: up to ≈ 82k–109k tokens (T2 `_axes.py`, T5 `dataset.py`).

## 5. Model facts (OBSERVED, public registries; the host copy is EXT)

**Ollama library, `qwen2.5-coder:latest`:**
- id `dae161e27b0e`, 4.7 GB;
- arch qwen2, 7.62B parameters, Q4_K_M;
- SYSTEM "You are Qwen, created by Alibaba Cloud. You are a helpful assistant.";
- TEMPLATE 1.6 kB, with a FIM (`.Suffix`) branch and a chat branch;
- page reads "Updated 1 year ago".

**Hugging Face `Qwen/Qwen2.5-Coder-7B-Instruct`:**
- revision `c03e6d358207e414f1eca0bb1891e29f1db0e242`, Apache-2.0;
- `tokenizer.json` and `tokenizer_config.json` are present;
- `config.json`: `max_position_embeddings` 32768; 28 layers; 28 attention heads; 4 KV heads; hidden size 3584; vocabulary size 152064.

**DERIVED:** the KV cache at fp16 is 28 × 4 × 128 × 2 × 2 = 57,344 bytes per token:
- 4k tokens ≈ 0.22 GiB;
- 8k ≈ 0.44 GiB;
- 16k ≈ 0.88 GiB;
- 32k ≈ 1.75 GiB.

This assumes an fp16 KV cache; the real KV type is **EXT**.

**EXT, still to observe on the host:**
- which model tag and digest are pulled locally;
- the Ollama version;
- the `/api/show` output: `modelfile`, `parameters`, `template`, `system`, `model_info` (context length);
- the server default `num_ctx` and `num_predict`;
- whether the GGUF-embedded tokenizer equals the Hugging Face tokenizer;
- CPU, GPU and RAM;
- Docker resources;
- prompt-evaluation and generation throughput. Throughput needs a model run, which is **outside** this read-only authorization.

---

## 6. Execution host (OBSERVED)

**Source:** the RD ran `stage0_inventory_readonly.sh` (SHA-256 `e95ea5a0…`) at 2026-09-29 07:35:24 UTC, and the output was pasted to the CSE. Values below are transcribed; the RD retains the raw output (`~/velith_stage0.txt`).

**Host and OS:**
- WSL2 kernel `6.18.33.1-microsoft-standard-WSL2`; Ubuntu 26.04 LTS.
- CPU: AMD Ryzen 5 5500U with Radeon Graphics; 6 cores / 12 threads; AVX2, FMA and F16C present; L3 cache 4 MiB.
- Memory as seen by WSL: 16,410,882,048 bytes total, 15,097,851,904 available; swap 4 GiB.
- Disk: WSL root 1007G (952G available); `/mnt/e` 141G (67G available). The Docker VM disk location and free space were **not observed**.

**GPU:**
- `nvidia-smi` not found.
- Docker lists the `nvidia` runtime and a CDI device `docker.com/gpu=webgpu`. No NVIDIA GPU was observed. Whether any GPU is usable for Ollama is **not observed**.

**Docker:**
- Docker Desktop 4.79.0; Engine 29.5.3 (API 1.54); containerd v2.2.5; runc 1.3.6.
- Storage driver `overlayfs`, using the **containerd image store** (`io.containerd.snapshotter.v1`).
- cgroup v2 with the cgroupfs driver; seccomp builtin profile; default runtime runc.
- Docker VM: 12 CPUs, 15.28 GiB memory.
- HTTP(S) proxy `http.docker.internal:3128`.
- 5 containers exist (3 running), unrelated to Velith; 40 images.
- **None of the five `swebench/sweb.eval.*` images is present locally.**

**Ollama:**
- The API is **not reachable from WSL** at `localhost:11434` or at the gateway `172.21.144.1:11434`.
- Windows `ollama.exe` is reachable through interop: **version 0.34.4**.
- **`ollama.exe list` returned no models.** `qwen2.5-coder:latest` is **not found**.
- No `OLLAMA_*` variables are set on the WSL side.

**Velith:** no `.env` file, so no `VELITH_OLLAMA_*` override exists. The effective model setting is the code default `qwen2.5-coder` (`core/config.py:55`).

**Historical proposer (OBSERVED, read-only).** The only persisted episode in the gitignored Velith store (`data/episodes/episodes.jsonl`, 1 line) records `model = model_version = "qwen2.5:3b"`. The M1 run therefore used an override (`qwen2.5:3b`), **not** the code default `qwen2.5-coder`. Neither model is installed now.

## 7. Not observed (remaining EXT)

- The location of any other local models. The RD reports possibly having a DeepSeek model. The Windows Ollama instance lists **none**, and Docker Model Runner and other `OLLAMA_MODELS` paths were **not inspected**.
- The Docker VM disk location and free space.
- GPU usability.
- Every model-specific fact: tag, digest, template, system prompt, parameters, context length, default `num_ctx`/`num_predict`, tokenizer.
- Throughput. That needs a model run, which is outside this authorization.

## 8. Follow-up host observations (OBSERVED; RD-run, read-only; 2026-09-29)

**Ollama:**
- `ollama.exe ps`: no model loaded.
- Windows user environment: `OLLAMA_MODELS=D:\ollama\models`, `OLLAMA_KEEP_ALIVE=30m`.
- The running server is PID 10264: `"C:\Users\Manish Raj\AppData\Local\Programs\Ollama\ollama.exe" serve`.
- `ollama.exe list` is **empty**, and `ollama.exe show deepseek-coder-v2:16b` returns "not found", **although the model exists on D:**. *(Inference, not verified: the server process predates the `OLLAMA_MODELS` setting, so it is reading a different models directory.)*

**Model on disk: `D:\ollama\models`, 8.3 GB total.**
- Manifest `library/deepseek-coder-v2/16b`.
- Model layer `sha256:5ff0abeeac1d2dbdd5455c0b49ba3b29a9ce3c1fb181b2eef2e948689d55d046`, 8,905,109,984 bytes.
- Template layer `sha256:22091531…4914` (705 bytes).
- Parameters layer `sha256:19f2fb9e…968d`, content `{"stop":["User:","Assistant:"]}`.
- Config `sha256:34488e45…fa66`: `model_format gguf`, `model_family deepseek2`, `model_type 15.7B`, `file_type Q4_0`.
- **The manifest has no SYSTEM layer.**
- Template text, context length and tokenizer are **not yet observed**; they need `ollama show` after the server can see the model.

**Docker disk (`docker system df`):**
- Images: 40, 41.43 GB (15.21 GB reclaimable).
- Build cache: 32.06 GB (21.13 GB reclaimable).
- Volumes: 270.4 MB.
- The Docker Desktop disk-image location is **not observed**.

**Host drives:**
- C: 234G, **17G free (93% used)**.
- D: 101G, 28G free.
- E: 141G, 67G free.

**Docker Model Runner:** not running; not used.

## 9. Ollama state reconciliation (RD-run, read-only; upload SHA-256 `84937370…d9ab`)

**OBSERVED:**
- **Docker disk images are on C:.** Both `C:\Users\Manish Raj\AppData\Local\Docker\wsl\disk\docker_data.vhdx` and `…\wsl\main\ext4.vhdx` are there (lengths truncated in the display). C: has 17G free (§8).
- **The Ollama app directory** (`%LOCALAPPDATA%\Ollama`) contains:
  - `upgrade.log`, 427,960 bytes, 26-09-2026 11:25:21;
  - `server.log` and `app.log`, both **0 bytes as listed**, 26-09-2026 11:25:26;
  - `ollama.pid`, 26-09-2026 11:25:29;
  - `server-1.log`, 3,058 bytes, **last write 26-09-2026 11:21:57**;
  - `server-2.log` to `server-5.log` (older).
- **The running server** is PID 10264: `"C:\Users\Manish Raj\AppData\Local\Programs\Ollama\ollama.exe" serve`.
- **`server-1.log`** records one server start at 26-09-2026 11:21:42 +05:30:
  - `OLLAMA_MODELS:C:\Users\Manish Raj\.ollama\models`; `OLLAMA_KEEP_ALIVE:30m0s`; `OLLAMA_HOST:http://127.0.0.1:11434`;
  - `OLLAMA_CONTEXT_LENGTH:0`; `OLLAMA_VULKAN:true`; `OLLAMA_NOPRUNE:false`; `OLLAMA_NUM_PARALLEL:1`;
  - "total blobs: 0";
  - "Listening on 127.0.0.1:11434 (**version 0.34.2**)";
  - "dropping integrated GPU … AMD Radeon(TM) Graphics";
  - inference compute **cpu**, total **31.3 GiB**, available **21.9 GiB**;
  - "vram-based default context … **default_num_ctx=4096**".
- **CLI:** `ollama.exe --version` reports 0.34.4 (§6); `list` is empty; `show deepseek-coder-v2:16b` returns "not found".
- **The D: model set is complete by size.** It has 6 blobs, which is exactly the config plus 5 layers referenced by the manifest, and every size matches its manifest entry. **Content hashes are not verified.**
- **The last PowerShell `Select-String` diagnostic failed because of shell quoting.** The failure is *not* evidence about the system.

**INFERENCE (not verified):**
- **I-1:** `server-1.log` belongs to a **pre-upgrade** server instance, version 0.34.2, which ran at 11:21. The upgrade ran at 11:25:21 and the app restarted at 11:25:26–29. That is consistent with PID 10264 being the **post-upgrade** instance. The 0.34.4 CLI reports its version without a client/server mismatch warning, which suggests the running server is 0.34.4. So 0.34.2 and 0.34.4 are two different instances, not a contradiction.
- **I-2:** the running server's configuration is not in any file read so far. A 0-byte `server.log` may be a stale directory length for a file held open by the server.
- **I-3:** the server almost certainly still uses `C:\Users\Manish Raj\.ollama\models`, which holds 0 blobs. It inherited its environment from the Ollama app, and the app started before `OLLAMA_MODELS=D:\ollama\models` was set, or without it. That matches both the empty `list` and the "not found".
- **I-4:** Ollama resolves models through `manifests/` and `blobs/` under `OLLAMA_MODELS`. A server started with `OLLAMA_MODELS=D:\ollama\models` should list `deepseek-coder-v2:16b` with **no download or copy**. Because every blob is referenced by the manifest, startup pruning (`OLLAMA_NOPRUNE=false`) should remove nothing.

**UNKNOWN:**
- the running server's actual `OLLAMA_MODELS` and version;
- whether `OLLAMA_MODELS` is persisted at User or Machine scope;
- the start time of PID 10264;
- the from/to versions in `upgrade.log`;
- the SHA-256 integrity of the 8.9 GB model blob;
- the context length and template of the model (these need `show`).

## 10. Ollama reconciliation, round 2 (RD-run, read-only; upload SHA-256 `8643859b…0043`)

**OBSERVED:**
- **Environment scope:** `OLLAMA_MODELS` at User scope = `D:\ollama\models`. At Machine scope it is **empty**.
- **The running server started right after the upgrade.** PID 10264 started at **26 Sep 2026 11:25:27**. `ProductVersion` of `ollama.exe` is empty: the binary carries no version resource.
- **`upgrade.log`:** installation succeeded at 11:25:21.335. Its run entry, "Run as: Original user", executed `cmd.exe /C set PATH=…;%PATH% & "…\ollama app.exe"` at 11:25:21.529.
- **`server.log` tail (60 lines)** covers 2026-09-26 21:43 to 2026-09-29 13:54, with **no restart or startup-config line** in that span.
  - Every `POST /api/show` on 2026-09-29 returned **404**: 13:00:56 (×2), 13:05:34 (×2), 13:25:34/35 (×2), 13:54:30 and 13:54:45.
  - `GET /api/tags` returned 200 (the empty list).
  - There are repeated `lookup ollama.com: no such host` warnings (intermittent DNS or network).
- **Integrity:** SHA-256 of `D:\ollama\models\blobs\sha256-5ff0abee…d046` equals its digest name. The 8.9 GB model layer is **intact**.

**RECONCILED (inference from the evidence; strong but not directly observed):**
- **R-1 — version.** The 0.34.2 startup in `server-1.log` (11:21) is the **pre-upgrade** instance. PID 10264 (11:25:27), launched by the installer's run entry, is the **post-upgrade** instance. It matches the 0.34.4 CLI, with no mismatch warning. There is no contradiction.
- **R-2 — models path.** The running server has been up continuously since 11:25:27, with no restart. It was launched through the installer chain, so it inherited its environment from the pre-upgrade process tree, whose recorded value was `OLLAMA_MODELS=C:\Users\Manish Raj\.ollama\models` (0 blobs). The 404s on `show` and the empty `tags` agree. The User-scope `D:\ollama\models` value is therefore **not in effect** for PID 10264.
- **R-3 — reuse without download.** The D: set is complete by size, and the model layer is hash-verified. A server started with the User environment (a fresh launch of the Ollama app) should see `deepseek-coder-v2:16b` with no download, copy or import.

**UNKNOWN:**
- the running instance's own startup-config line, which is at the head of `server.log` and not in the tail;
- when the User `OLLAMA_MODELS` was set, relative to earlier server starts;
- the SHA-256 of the 5 small blobs (config, template, 2 licences, params).

## 11. Ollama reconciliation, round 3 (RD-run, read-only; upload SHA-256 `e0e33e68…9e6f`)

**CONFIRMED.** This is the head of the current `server.log`, i.e. the startup of the running instance, PID 10264, started 11:25:27:
- 2026-09-26 11:25:29 "server config" `OLLAMA_MODELS:C:\Users\Manish Raj\.ollama\models`; `OLLAMA_KEEP_ALIVE:30m0s`; `OLLAMA_CONTEXT_LENGTH:0`; `OLLAMA_HOST:http://127.0.0.1:11434`; `OLLAMA_NOPRUNE:false`; `OLLAMA_VULKAN:true`;
- "total blobs: 0"; "total unused blobs removed: 0";
- "Listening on 127.0.0.1:11434 (**version 0.34.4**)";
- integrated GPU (AMD Radeon, Vulkan) dropped; inference compute **cpu**, total 31.3 GiB, available 19.2 GiB;
- "vram-based default context … **default_num_ctx=4096**".

**This supersedes the inferences in §9 and §10:**
- R-1: the running server is 0.34.4 — **CONFIRMED**.
- R-2: the running server uses the C: path, which holds 0 blobs — **CONFIRMED**.

**CONFIRMED (§10):**
- The Windows User environment has `OLLAMA_MODELS=D:\ollama\models`; Machine scope is empty.
- The 8.9 GB model blob's SHA-256 equals its digest name.

**Environment propagation: residual, cause not determined.**
- The User-scope value was **not** in the environment of the process started at 11:25:27 by the installer's run entry ("Run as: Original user").
- **Not determined:**
  - when the User value was written;
  - whether the launching process tree ever held it;
  - how the D: artifacts (manifest directory dated 2026-09-03) were originally written.
- A fresh launch from the user's desktop session is the expected way to apply the User value. That is an expectation, not an observation.

**Small-blob hash discrepancy: a command artifact, not a system change.**
- The latest `find … -type f -size -1M -exec sha256sum {} \;` returned nothing. With GNU `find`, `-size -1M` **rounds each file's size up to whole MiB units**. Every non-empty file below 1 MiB rounds to 1, and "less than 1" then matches only **empty** files.
- The 5 small blobs (568, 705, 1,064, 13,768 and 32 bytes; §8, `find -printf`) are therefore **not** contradicted.
- **Their hashes remain unverified.** A byte-exact predicate (`-size -1048576c`) is needed.

## 12. Model activation (RD-performed host action; evidence upload SHA-256 `96d558c2…c0a8`)

**The RD reports** relaunching Ollama so that it reads `D:\ollama\models`. The relaunch was performed by the RD; it is not a CSE action. The model-path investigation is **closed**.

**OBSERVED (PowerShell, host):**
- `ollama list`: `deepseek-coder-v2:16b`, ID `63fb193b3a9b`, 8.9 GB, modified "7 weeks ago".
- `ollama show`: architecture deepseek2; parameters 15.7B; **context length 163840** (advertised model maximum); embedding length 2048; quantization Q4_0; capabilities `completion`, `insert`; parameters `stop "User:"`, `stop "Assistant:"`; licences: DEEPSEEK LICENSE AGREEMENT v1.0 and MIT.
- `ollama show --modelfile`: `FROM D:\ollama\models\blobs\sha256-5ff0abee…d046`, the blob whose SHA-256 was verified in §10. The model was recognized **without any download**.
- **TEMPLATE, verbatim structure:**
  - a FIM branch, when `.Suffix` is set;
  - a Messages branch, which emits `<｜begin▁of▁sentence｜>`, `User: …` and `Assistant:` turns;
  - an **else branch**, used when only `.Prompt` is set: `{{ if .System }}{{ .System }}{{ end }}{{ if .Prompt }}User: {{ .Prompt }}{{- end }}Assistant:{{ .Response }}`.
- **SYSTEM:** none. There is no SYSTEM directive in the Modelfile.

**DERIVED (from the code and the template; no model run):**
- The frozen Velith client sends `/api/generate` with `prompt` only, and no `raw`, `system` or `messages` (`llm/client.py:98–104`). Ollama therefore renders the **else branch**. The effective input is `User: <prompt>Assistant:`, with **no separator** between the prompt and `Assistant:`, because `{{-` trims whitespace.
- That branch emits **no** explicit begin-of-sentence token. Whether the tokenizer adds one automatically is **not observed**.
- Generation stops at the first emitted `User:` or `Assistant:`.
- The running server has `OLLAMA_CONTEXT_LENGTH=0` and `default_num_ctx=4096` (§11). The frozen client sends no `num_ctx`. **The effective context on Velith's client path is therefore expected to be 4096 tokens, not 163840.** How the server behaves when a prompt exceeds 4096 is **not yet observed**.

## 13. Timing run R0 — partial result (OBSERVED from `timing/runs/run-20260929T103440Z`)

**Provenance:**
- The RD executed runner **R0** (SHA-256 `0fdd8b3e…`), which was superseded by R1 `0510280e…`.
- Generator `3d9fc3ff…`; self-test PASSED on PowerShell 5.1.26100.
- Started 2026-09-29T10:34:42Z. **Status ABORTED** at 10:40:27Z with "The remote server returned an error: (400) Bad Request."
- The RD reports no runner process remains; the Ollama server is still running.
- Host: 33,635,815,424 bytes of physical RAM; Ollama 0.34.4; model digest `63fb193b3a9b4322…2fa5`.

**Completed requests** (no `num_ctx` sent; T = 0; seed 0; `num_predict` 256):

| # | Prompt bytes | `prompt_eval_count` | Prompt eval s | Prompt tok/s | Gen tok/s | Load s | Wall s | `/api/ps` size | `/api/ps` context_length |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 434 | 180 | 6.60 | 27.3 | 14.3 | 17.28 | 41.9 | 10,122,208,213 | **4096** |
| 1 | 3,415 | 1,752 | 64.33 | 27.2 | 9.3 | 0.04 | 92.1 | 10,122,208,213 | 4096 |
| 2 (same bytes as #1) | 3,415 | **1,752** | **0.11** | — | 9.1 | 0.04 | 28.2 | 10,122,208,213 | 4096 |
| 3 | 6,635 | 3,467 | 136.44 | 25.4 | 6.1 | 0.01 | 179.2 | 10,122,208,213 | 4096 |
| 4 | 15,183 | — | — | — | — | — | — | — | — |

- **Run #4 was the Q3 probe:** the approximately 8k-token prompt was sent with no `num_ctx`. The request was built (`raw/04_request.json`), and the server returned **HTTP 400**. R0 does not capture the error body, and no response file exists.
- **Observed bytes per token for the synthetic prompts:** 1.949 (run 1) and 1.914 (run 3).
- **Free RAM:** 16.64 GB at start; 6.75 GB after the model loaded; 6.13 GB after run 3.
- **Evidence gap:** `server_log_segment.txt` is empty (0 lines after the recorded start line 93), even though the RD observed the HTTP 400 in `server.log` at 16:10:27. The cause of the empty capture has **not** been determined.

## 14. Timing run R2 (OBSERVED from `timing/runs/run-20260929T113401Z`; runner SHA-256 `ce2fb7f6…d00d`)

**Status:** ABORTED at run #7 with HTTP 400, as designed for any non-#4 failure. `optional_32k` was SKIPPED because the projected free RAM (4,229,722,112 − 3,510,768,763 B) is below 4 GB. `server_log_status` = CAPTURED.

**Runs #0–#3** reproduce R0 within noise: 180, 1,752, 1,752 and 3,467 prompt tokens; 24–27 prompt tok/s; `/api/ps` context_length 4096.

**#4 (the Q3 probe):** about 8k tokens with no `num_ctx` gave **HTTP 400**, body `{"error":"the prompt is longer than the context length currently available to the model; shorten the prompt, adjust the context length in settings, or use a model with a longer context length"}`. **Q3 is resolved:** over-context prompts are rejected, not silently truncated.

**#5 (`num_ctx` 16384, tiny prompt):**
- load 17.83 s;
- `/api/ps` size **13,632,976,976 B** at context_length 16384, versus 10,122,208,213 B at 4096;
- free RAM afterwards 4,229,722,112 B.

**#6 (`num_ctx` 16384, 15,183 bytes):**
- `prompt_eval_count` 8,188; prompt evaluation 376.5 s (**21.7 tok/s**);
- generation 256 tokens at **3.08 tok/s**;
- wall time 460.2 s;
- free RAM afterwards 4,026,986,496 B.

**#7 (`num_ctx` 16384, N = 316, 30,471 bytes):** HTTP 400, with the same error body.

**Token model (DERIVED; exact on every measured point).** For the single-letter-nonce synthetic prompt:
- `tokens(N) = 48 + 43*min(N,10) + 49*(min(N,100)-10) + 55*(N-100)`;
- this reproduces N = 36 → 1,752, N = 71 → 3,467 and N = 160 → 8,188;
- it predicts N = 316 → **16,768** (> 16,384), consistent with #7's rejection;
- digits tokenize singly: +6 tokens per extra index digit;
- the context array confirms a BOS token (100000) and the `User:` template prefix.

The bytes-per-token ratio falls with prompt size (1.949 → 1.914 → 1.854), which is why #7's byte-based sizing overshot.

## 15. Supplemental S1 (OBSERVED from `timing/runs/supp16k-20260929T170742Z`; script SHA-256 `75ce8bee…ca2f`)

**Result:** COMPLETED; HTTP 200; `done_reason` = length.
- **Request:** `num_ctx` 16384, N = 304, nonce `stage0-H`, prompt 29,295 bytes (SHA-256 `f7a55df3…2bbd`), request SHA-256 `efc3b13a…14d0`.
- **Prompt tokens:** `prompt_eval_count` **16,108**, equal to the prediction. `prompt_tokens_minus_predicted` = **0**, so the token model is confirmed at 16k. The prompt plus the 256-token reserve is 16,364 ≤ 16,384.
- **Prompt evaluation:** 126.18 s (reported 127.7 tok/s). **Not a cold measurement; see the contamination note.**
- **Generation:** 256 tokens in 95.07 s = **2.69 tok/s**.
- **Timing:** load 0.004 s (model already resident); total 225.7 s; wall 225.9 s.
- **Memory:** `/api/ps` size 13,632,976,976 B; `llama-server` working set 13,689,171,968 B; free RAM 4,426,317,824 B before and 4,668,682,240 B after.
- **Server process:** `llama-server` PID 22788 was started **2026-09-29T16:58:17.92Z** with `-c 16384 -np 1 -b 1024 -ub 1024 --flash-attn auto`, under `ollama serve` PID 29896.

**Contamination of the prompt-evaluation figure (OBSERVED plus INFERENCE).**
- **Observed:** two earlier real S1 attempts left directories with pre-flight files and a request, but **no `S1_record.json`** (the process ended before its `finally` block ran):
  - `supp16k-20260929T165817Z`: `pre_ps` shows no model loaded; `llama-server` PID 22788 was created at exactly this attempt's start time;
  - `supp16k-20260929T170420Z`: `pre_ps` shows the model resident at 16384.
- **Observed:** both attempts carry the **identical** request bytes as S1.
- **Inference:** the server's prompt cache already held much of this exact prompt from the interrupted attempts. So 126.18 s is **not** the cold 16k prompt-evaluation time. R0 and R2 had already shown that a cached prompt keeps the full `prompt_eval_count` and cuts only the duration.
- **Unaffected:** the generation rate, the memory figures and the fit check.

**Cold measurements across R0, R2 and S1 (CPU only, Q4_0, T = 0, `num_predict` 256):**

| `num_ctx` | Prompt tokens | Prompt eval s | Prompt tok/s | Gen tok/s | Load s (cold) | `/api/ps` size | Free RAM after |
|---|---|---|---|---|---|---|---|
| 4096 | 180 | 6.60–6.63 | 27.2–27.3 | 14.3 | 17.3–17.6 | 10.12 GB | 6.74–6.75 GB |
| 4096 | 1,752 | 64.3–66.8 | 26.2–27.2 | 9.3–9.7 | — | 10.12 GB | 6.3–6.6 GB |
| 4096 | 1,752 (cached repeat) | 0.11–0.14 | — | 9.1–9.7 | — | 10.12 GB | — |
| 4096 | 3,467 | 136.4–143.4 | 24.2–25.4 | 6.1–6.3 | — | 10.12 GB | 5.9–6.1 GB |
| 4096 | ≈7.8k | **HTTP 400** | — | — | — | — | — |
| 16384 | 182 | 7.27 | 25.0 | 13.6 | 17.8 | 13.63 GB | 4.23 GB |
| 16384 | 8,188 | 376.5 | 21.7 | 3.08 | — | 13.63 GB | 4.03 GB |
| 16384 | 16,108 | 126.2 (**cache-contaminated**) | — | **2.69** | (resident) | 13.63 GB | 4.67 GB |
| 16384 | 16,768 | **HTTP 400** | — | — | — | — | — |
| 32768 | — | not run (stop rule) | — | — | — | — | — |

**Missing:** the **cold** prompt-evaluation time for about 16k tokens.

## 16. Supplemental S2 (cold) — attempt review

**`timing/runs/supp16k-cold-20260929T173106Z` (nonce `stage0-J`):**
- **Files:** `S2_prompt.txt` (SHA-256 `977f1602…a9aa`), `S2_request.json` (SHA-256 `b57635a4…e42b`; options `num_ctx` 16384, T 0, seed 0, `num_predict` 256), and `pre_version.json` (0.34.4), `pre_tags.json` and `pre_ps.json`, all written at 23:01:06 +05:30.
- **`pre_ps`:** the model was **resident at context_length 16384** (expiring 23:11:29), so the cold-load RAM check did not apply.
- **No `S2_record.json`** exists.
- **Next activity:** the next dry run was at 23:05:09; the guard then blocked real re-attempts, as designed.

**Findings:**
- **(1) Ollama was contacted: CONFIRMED.** version, tags and ps were retrieved.
- **(2) `/api/generate` was sent: INFERENCE, strongly supported.** Every pre-generate failure path would have written a record in `finally`. The absence of a record means the process ended abnormally after pre-flight, most plausibly while waiting on generation, for at most about 4 minutes.
- **(3) Usable evidence:** pre-flight state only. No timing.
- **Classification:** partial (pre-flight only). **Not usable** as the cold 16k measurement.
- **Consequence:** the `stage0-J` prefix may now be partly cached, so S2 is void. The replacement is **S2b**, with nonce `stage0-K` and a scoped guard (`timing/README.md`).

## 17. Supplemental S2b — COLD 16k measurement (OBSERVED from `timing/runs/supp16k-coldK-20260929T175204Z`; script SHA-256 `048f12c8…ac1f`)

**Result:** COMPLETED; HTTP 200; `done_reason` = length.
- **Request:** nonce `stage0-K` (never sent before), N = 304, prompt 29,295 bytes (SHA-256 `0b5e444b…5189`), request SHA-256 `cfb3f578…ca6c`.
- **`generate_sent` marker:** 2026-09-29T17:52:06.17Z.
- **Prompt tokens:** `prompt_eval_count` **16,108**; `prompt_tokens_minus_predicted` = 0. The prompt plus the 256 reserve is 16,364 ≤ 16,384.
- **Prompt evaluation (COLD):** **960.95 s = 16.76 tok/s.** The nonce is a fresh token at position 9, so no earlier prompt shares more than about 9 tokens.
- **Generation:** 256 tokens in 146.55 s = **1.75 tok/s**.
- **Totals:** total duration 1,108.5 s; wall time **1,108.9 s (18.5 min)**. Load 0.008 s (model resident at 16384).
- **Server process:** the same `llama-server` process, PID 22788 (`-c 16384`).
- **Memory:**
  - `/api/ps` size 13,632,976,976 B;
  - `llama-server` working set 15,029,702,656 B, private bytes **19,164,008,448 B**;
  - free RAM **2,553,708,544 B before** (below S1's 4.43 GB) and 5,304,381,440 B after.
  - Generation was slower than in S1 (1.75 vs 2.69 tok/s). *Possible memory pressure or paging: an INFERENCE, not measured.*

**Cold prompt-evaluation fit (DERIVED; least squares over the four cold points 1,752 / 3,467 / 8,188 / 16,108 tokens):**
- t(P) ≈ 0.03306·P + 1.647×10⁻⁶·P² seconds;
- it reproduces 63 / 134 / 381 / 960 s against measured 64–67 / 136–143 / 376.5 / 961 s.

**Status:** the cold 16k prompt-evaluation gap from §15 is **closed**.

## 18. Server token-ID ground truth (OBSERVED from existing run evidence; nothing new executed on the host)

- **Source:** the `context` arrays in the 7 successful responses. The prompt IDs are `context[:len(context) − eval_count]`. Frozen in `tokenizer/server_truth_manifest.json` (SHA-256 `4d0575a4…e76c`).

| Prompt | `prompt_eval_count` | Prompt IDs in `context` | Difference |
|---|---|---|---|
| R2#0 | 180 | 179 | +1 |
| R2#5 | 182 | 181 | +1 |
| R2#1 | 1,752 | 1,751 | +1 |
| R2#3 | 3,467 | 3,466 | +1 |
| R2#6 | 8,188 | 8,187 | +1 |
| S1 | 16,108 | 16,107 | +1 |
| S2b | 16,108 | 16,107 | +1 |

- **Offset:** the +1 is constant across all prompts. **Cause not determined.**
- **Token streams:** every stream starts `[100000, 5726, 25, …]` (BOS, then "User:"). Every stream ends `[…, 13, 185, 185, 185, 77398, 25]`. The first generated token is `4462`, which matches the response text beginning " Here".
- **Correction to §12 (DERIVED, not verified):** the claim that a prompt-only `/api/generate` renders the *else* branch is contradicted. Three 185 tokens after a prompt that ends in a single `\n` are consistent with the **Messages branch**: `<BOS>User: {prompt}\n\nAssistant:`. This remains an inference until the tokenizer check settles it.
- **Tokenizer check:** the Hugging Face tokenizer check (`tokenizer/check_tokenizer_equivalence.py`, SHA-256 `d8ea1576…9507`) is ready to run on the host. It could not run in the CSE sandbox because huggingface.co returned 403 through the proxy.

## 19. Tokenizer equivalence check (RD-executed in WSL; result `tokenizer/results/tokcheck-20260929T192640Z/result.json`, SHA-256 `1b6dbcb7…4024`)

**VERDICT: PASS.**

**Provenance:**
- script SHA-256 `d8ea1576…9507` and manifest `4d0575a4…e76c`, both unchanged since the check was written;
- Hugging Face `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct` at commit `e434a23f91ba5b4923cf6c9d9a238eb4a08e3a11`;
- `tokenizer.json` SHA-256 `091b9dadb9845f0e8386c38bdb87e98db8adc7b0aacf36cb9257c00d0a668714`;
- `tokenizers` 0.23.2, Python 3.14.4, WSL2.

**Result:**
- **Exact match of every token ID** for all 4 gating prompts (1,751, 3,466, 8,187 and 16,107 IDs) and for the 3 non-gating prompts.
- **Rendering confirmed:** `<BOS>User: {prompt}\n\nAssistant:`, the **Messages branch**. This confirms the §18 correction; the §12 else-branch derivation is **refuted**. `add_special_tokens` makes no difference.
- **Offset:** `prompt_eval_count − len(hf_ids)` = **+1** on all 7 prompts, with spread 0. Its cause is still not determined; it is a server-side count.
- **Counts alone would not have identified the rendering.** The wrong renderings also give constant offsets (+2 for no BOS text, +4 for the else branch, each with spread 0). Only the ID-level equality discriminated between them.

**GGUF comparison (supplementary):**
- `tokenizer.ggml.pre` = `deepseek-llm`;
- vocabulary identical on all 100,018 Hugging Face IDs;
- merges identical (99,757 = 99,757);
- the GGUF has 2,382 extra IDs (102,400 − 100,018) that the Hugging Face tokenizer cannot emit. Their contents were not inspected.

**Scope limit:** every tested prompt is synthetic ASCII. Equivalence on non-ASCII text, CRLF, tabs, and literal special-token strings inside repository content is **not** tested.

## 20. F2 derived model: creation and static identity verification (RD-performed host action; output archived as `model/F2_CREATE_AND_VERIFY_OUTPUT_2026-09-30.txt`)

**Pre-creation guard:** the base manifest file's SHA-256 is `63FB193B3A9B4322A18E8C6B250CA2E70A5FF531E962DBF95BA089B2566F2FA5`, equal to the expected value, so the base is verified.

**Creation:** `POST /api/create` with `model/P1_DERIVED_MODEL.F2.create.json` (SHA-256 `a51530d4…b3d`) returned `success`.

**Derived model `velith-p1-deepseek-coder-v2:16b-c16384-np1024`:**
- **Manifest SHA-256 (the pinned identity D\*):** `e196dcd918e4f54307db79c9fada1ff261c564e1df1624e20ae65d1ff0a4c45c`.
  - How it was obtained (DERIVED, verified): the manifest JSON printed by `Get-Content -Raw`, plus a trailing `\n`, hashes to this value.
  - It matches the 56-hex prefix shown by `Get-FileHash` (`E196DCD918E4…AE65D1F`) and the `ollama list` ID `e196dcd918e4`.
- **Manifest layers:**

| Layer | Digest | Size (bytes) | Check |
|---|---|---|---|
| Model | `5ff0abee…d046` | 8,905,109,984 | Same blob as the base, reused, not copied (hash verified in §10) |
| Template | `22091531faf0148fb166466743e30b7012ea7a6d13a9af7e3995ccfec3ed4914` | 705 | Equals the SHA-256 of the base TEMPLATE text from `/api/show` (705 bytes), so it is byte-identical |
| Licence | `4bb71764…c2b5` | 13,768 | Marked `from: deepseek-coder-v2:16b` |
| Licence | `1c8f573e…e1c7` | 1,064 | Marked `from: deepseek-coder-v2:16b` |
| Params | `6ba30c6931f4ed9ab48a7bd9ab885e2cd5fa7f625b89bb037e85c7a801800182` | 71 | See below |

- **No SYSTEM layer.**
- **Config:** `sha256:303f950e…a1e9`, 122 bytes. Its content is not displayed; it is pinned transitively by D\*.
- **Params blob, byte-exact:** the content is `{"num_ctx":16384,"num_predict":1024,"stop":["\nUser:","\nAssistant:"]}` followed by `\n`. That is 71 bytes, and its SHA-256 equals the layer digest.
  - The stop strings contain real newline characters, which `ollama show --modelfile` renders as line breaks.
  - The base stops `User:` and `Assistant:` are **not** present, so this parameter layer **replaced** the base parameters.

**Not yet verified (runtime; needs a generation call):**
- `/api/ps` shows `context_length` 16384 after the model loads;
- the default `num_predict` of 1024 applies when the client omits it;
- the line-anchored stop strings behave as intended.
