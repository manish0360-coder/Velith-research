# P1 Environment-Readiness Audit (Windows + WSL). Research only.

**Status:** AUDIT COMPLETE (Part B tokenizer check pending, planned after the Python 3.12 install). Decision: `OD-ENV_CONSOLIDATED_DECISION_INPUT.md`.
- The CSE sandbox cannot reach the host, Docker Hub or huggingface.co (the proxy returns 403). Both audits are therefore RD-executed.
- **Precondition met:** OD-4 reachability PASS (`od4/results/od4-reachability-20260930T044125Z.json`).

## 1. Instruments

| File | Side | Mode | What it gathers |
|---|---|---|---|
| `Audit-P1Env-Windows.ps1` | native Windows | Part A read-only | OS, RAM, drives C/D/E; Python interpreters (py launcher, PATH, registry; Store stubs are not executed); proxy (WinINET registry, WinHTTP, `*_PROXY` environment variables in all scopes); Git `core.autocrlf`; Docker CLI/context; Docker Desktop settings (disk, memory, CPU, containerd keys); Docker VHDX paths and sizes; `.wslconfig` |
| same, `-TokenizerCheck -TokPython <exe>` | native Windows | Part B, opt-in, user-space | isolated venv in `%LOCALAPPDATA%\velith-audit\venv-tokcheck`; pinned `tokenizers==0.23.2` and `huggingface_hub==1.33.0`; `tokenizer.json` at commit `e434a23f…3a11`; runs the unmodified `check_tokenizer_equivalence.py` (SHA-256 `d8ea1576…9507`) |
| `audit_p1env_wsl.sh` | WSL | read-only | kernel and OS; host Python; Git; `df` for / and /mnt/c, /mnt/d, /mnt/e; `docker version`/`info`/`context`/`system df`/`image ls --digests`; `docker manifest inspect -v` for the 5 task images (registry metadata only, **no pull**); `summary.json` with compressed sizes, a unique-layer union, T1's digest against M2 `sha256:eaf59700…f1fba4`, and containerd-store detection |

**Sandbox validation of the WSL summarizer**, run against a stub `docker`:
- single-platform manifests and multi-platform indexes are both handled, with the amd64 entry selected;
- shared layers are counted once;
- a failed manifest is recorded, not fatal;
- the T1 digest comparison works.

## 2. How results will be judged (fixed now, before the results exist)

| Item | PASS | BLOCKER |
|---|---|---|
| Python 3.12 on Windows | a 3.12.x interpreter is present (for the pinned Velith harness, W3) | absent. This requires an authorized **install**. |
| Proxy | WinINET ProxyEnable = 0 **or** no `*_PROXY` variables that would affect loopback | Never a blocker. The harness always sets `NO_PROXY=127.0.0.1,localhost` (W6); it is recorded either way. |
| Tokenizer on Windows | VERDICT PASS, the same configuration (`messages_branch`), offset +1, `tokenizer.json` SHA-256 `091b9dad…8714` | any difference |
| Docker runtime | server reachable from WSL; `linux/amd64`; seccomp present | unreachable |
| Docker space | free space on the drive holding `docker_data.vhdx` ≥ **2.5 ×** the unique compressed layers of the images not already present **+ 10 GB** headroom | below that bound |
| T1 image | the tag digest equals the M2 digest, **or** the M2 digest is present locally | the tag moved and the M2 digest is not local. The pinned digest must then be pulled by digest in Stage 0. |

**About the 2.5 × factor:** it is an **engineering assumption**, not a measurement. Unpacked Python/conda image layers are typically 2–3 × their compressed size. With the containerd image store, the compressed blobs are kept alongside the unpacked snapshots, so they add roughly +1 ×. The real footprint is known only after a pull.

## 3. Results (RD-executed 2026-09-30)

**Evidence:** `results/windows-20260930T050540Z/audit.json`; `results/wsl-20260930T050931Z/` (`summary.json` and raw outputs).

| Item | Observed | Verdict under the §2 rules |
|---|---|---|
| Python 3.12 on Windows | only 3.10.7 (`C:\Users\Manish Raj\AppData\Local\Programs\Python\Python310`); two Store stubs | **BLOCKER.** A user-scope 3.12 install is required. |
| Proxy | WinINET off; WinHTTP direct; no `*_PROXY` variables | PASS. No change; the harness still sets `NO_PROXY` per process. |
| Tokenizer on Windows | not run (Part B not invoked) | PENDING. It runs on the 3.12 interpreter after the install. |
| Git | 2.39.0.windows.2; **system `core.autocrlf=true`** | Not a blocker. It confirms W7/W9: clone with `-c core.autocrlf=false`; never read material from a Windows checkout. |
| Docker runtime | Desktop 4.79.0, Engine 29.5.3, containerd 2.2.5, containerd snapshotter, cgroup 2, seccomp builtin, WSL integration (Ubuntu) | PASS |
| Docker disk | `docker_data.vhdx` 60.76 GB on C:; C: free 18.09 GB; E: free 71.81 GB | — |
| Docker space for P1 | unique compressed 6.177 GB, so required free = 25.44 GB; C: has 18.09 GB | **BLOCKER** (see OD-ENV §3) |
| T1 image | the tag digest equals the M2 digest `eaf59700…`; not local | PASS on identity; Stage 0 pulls it by digest. |
| Per-image compressed sizes | T1 1.146 GB; T2 3.138 GB; T3 1.496 GB; T4 1.113 GB; T5 1.926 GB (sum 8.818 GB; unique 6.177 GB) | — |

**Instrument note:** `py -0p` writes its header to stderr, so PowerShell 5.1 recorded a NativeCommandError. The data line (`-3.10-64 …`) was captured correctly.

## 4. Consolidated host changes and blockers

See `OD-ENV_CONSOLIDATED_DECISION_INPUT.md` §5: one gated plan covering Docker storage (measure, back up, reclaim build cache, compact, stay or move), the Python 3.12 user install, and the Windows tokenizer check. Task-image pulls require a separate authorization.
