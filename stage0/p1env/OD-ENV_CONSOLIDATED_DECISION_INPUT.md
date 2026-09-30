# OD-ENV — Consolidated Environment-Readiness Decision Input (Velith main + P1 + shared Docker)

**Status:** RESEARCH / DECISION INPUT.
- Nothing has been pulled, pruned, moved or installed.
- Velith main is untouched at `5452efc`.

**Evidence:**
- `results/windows-20260930T050540Z/audit.json`;
- `results/wsl-20260930T050931Z/` (`summary.json`, `docker_df.txt`, `docker_images.txt`, `disk.txt`);
- the P1 pass/blocker rules fixed **before** the results in `P1_ENV_READINESS_AUDIT.md` §2.

**Scope rule (RD):** Docker is **shared project infrastructure**: Velith main, P1, and other local projects (MiniPrometheus `mp-verifier`/`mini-prometheus-verifier`, `districore`). Any change is judged against all of them.

## 1. Facts (observed)

| # | Fact | Source |
|---|---|---|
| F1 | C: free **18,091,028,480 B** (≈ 18.1 GB, 93 % used). D: free 29.35 GB. E: free **71.81 GB** (53 % used). | audit.json, disk.txt |
| F2 | The Docker data disk `C:\Users\Manish Raj\AppData\Local\Docker\wsl\disk\docker_data.vhdx` is **60,763,930,624 B** (logical length). `main\ext4.vhdx` is 100.7 MB. Both are on C:. | audit.json |
| F3 | Docker Desktop 4.79.0, Engine 29.5.3, containerd v2.2.5, runc 1.3.6. **containerd snapshotter enabled.** cgroup v2; seccomp builtin; 12 CPU; VM memory 16.41 GB. `.wslconfig` absent. | docker_info.json, audit.json |
| F4 | `docker system df`: Images 41.43 GB (15.21 GB reclaimable); **build cache 32.06 GB (21.13 GB reclaimable)**; volumes 6, 270.4 MB (0 reclaimable); containers 5, 327.7 kB. | docker_df.txt |
| F5 | 39 local images. **Velith:** `velith-verifier:m0` (952 MB), `velith-gate:i1`/`phaseA`, `velith-audit:i0`. **MiniPrometheus:** 23 `mp-verifier` tags plus `mini-prometheus-verifier:rm4`. **districore:** app, `flutter` 8.88 GB, postgres, caddy. Base images: `python:*-slim`. | docker_images.txt |
| F6 | The five P1 images are **not local**. Compressed total 8,818,037,647 B; **unique compressed layers 6,177,118,311 B**; shared-layer saving 2.64 GB. All are multi-platform indexes; the linux/amd64 manifest was selected. | summary.json |
| F7 | The T1 tag's amd64 manifest digest **equals** the M2-verified `sha256:eaf59700…f1fba4`. The tag has not moved, but the image is no longer local. | summary.json |
| F8 | Windows Python: **3.10.7 only**. **No 3.12.** | audit.json |
| F9 | Proxy: WinINET ProxyEnable 0; WinHTTP direct; no `*_PROXY` variables in any scope. | audit.json |
| F10 | Git for Windows 2.39.0 with **system `core.autocrlf=true`**; global unset. | audit.json |
| F11 | The Windows tokenizer check (Part B) was **not run**. | audit.json (no `tokenizer_check`) |
| F12 | The Velith main gate (`d31_placement_gate.sh`, `cid_gate_commit.sh`) builds with **`docker compose build --no-cache verifier`** and then runs ruff, format, mypy and pytest in the container. **It never consumes build cache.** | the gate scripts, `docker-compose.yml` |

## 2. Engineering assumptions (not measured, and stated as such)

| # | Assumption | Why it matters |
|---|---|---|
| A1 | The P1 on-disk footprint is 2.5 × the unique compressed size: 6.18 GB of containerd blobs kept, plus unpacked snapshots at about 1.5–2 ×. **Pre-declared P1 space rule:** free space on the Docker drive ≥ 2.5 × 6.177 GB + 10 GB = **25.44 GB**. | The true size is known only after a pull. **Hard lower bound: at least 12.35 GB** (blobs 1 × plus unpacked ≥ 1 ×). |
| A2 | A WSL2 dynamic VHDX **does not shrink** by itself when data is deleted inside it. New writes may or may not reuse freed blocks (ext4 allocation does not track VHDX allocation). | Pruning alone guarantees internal space, **not** host-drive space. |
| A3 | Host-file shrink after pruning needs **compaction** (diskpart `compact vdisk`, with Docker and WSL shut down, as admin; Windows Home has no `Optimize-VHD`), or a sparse VHDX with TRIM. How much it shrinks is **unknown until measured**. | Every option below depends on it. |
| A4 | "Reclaimable" build cache (21.13 GB) is regenerable and does not overlap the retained image content. | It is Docker's estimate. It is verified by measuring before and after. |
| A5 | A system drive should keep ≥ 15 GB free after any planned growth. | This is an operational-safety threshold, not a measurement. |
| A6 | Rough scaling estimate: ≈ 1.24 GB unique compressed per task, times 2.5, gives ≈ 3.1 GB per task. 50 tasks would be ≈ 150 GB. | It indicates the scale of later BRP- or evaluation-scale needs. It is not a plan. |

## 3. Is C: a credible blocker? **Yes.**

- **Rule (A1):** 18.09 GB < 25.44 GB, so it is a **BLOCKER**.
- **At the hard lower bound (12.35 GB):** C: would drop to about 5.7 GB free (97.7 % used). That violates A5 for the system drive, and Windows Update, the page file and temp files share that margin.
- **The only way C: suffices without a change** is if VHDX growth is absorbed by already-allocated free space inside `docker_data.vhdx`. That is **not guaranteed** (A2).
- **Conclusion:** C: cannot credibly host the five P1 images in its current state.

## 4. Moving the Docker data disk to E: — evaluation

| Scenario | Arithmetic | Verdict |
|---|---|---|
| Move **as-is** (VHDX 60.76 GB) | E: free after the move = 71.81 − 60.76 = **11.05 GB**. That is below the 25.44 GB rule and even below the 12.35 GB lower bound. | **Not a solution.** It moves the problem and fills E:, which also holds both repositories and the P1 evidence root. |
| Move **after** a build-cache prune and compaction | E: satisfies the rule if the compacted VHDX is ≤ 71.81 − 25.44 = **46.37 GB**, i.e. it shrinks by ≥ 14.39 GB (reclaimable build cache: 21.13 GB). | **Feasible** if compaction works (A3). After P1, E: would have about 17 GB free (≈ 89 % used). |
| **Stay on C:** after a build-cache prune and compaction | C: satisfies the rule if the VHDX shrinks by ≥ 25.44 − 18.09 = **7.35 GB**. After P1, C: would have about 24 GB free, if the full 21 GB is returned. | **Feasible**, needs the smallest shrink, and involves **no move**. |
| **Long-term** (BRP or evaluation scale, A6) | Tens to hundreds of GB of task images | **Neither C: nor E: is adequate.** Moving to E: is a zero-sum redistribution. |

**Evaluation of E: as the long-term shared solution:**
- **Rejected as long-term.** E: cannot hold the current disk plus P1 without reclaiming space first, and it has no room for BRP-scale growth.
- **As an interim location** it is numerically equivalent to staying on C: after reclaiming space, but it carries the risk of a move. That move risk falls on three projects' images.
- A later move to dedicated storage would then be a **second migration** (C: → E: → new drive).

**Recommendation:**
- **Interim:** reclaim regenerable build cache, compact, and **stay on C:**.
- **Long-term:** migrate **once**, directly to **dedicated storage** (a new internal or external SSD, ≥ 500 GB suggested; acquiring hardware is the RD's call), when BRP or evaluation-scale images are needed.
- **Fallback:** if compaction returns < 7.35 GB, go to E: only if its gate (§4 row 2) passes; otherwise dedicated storage becomes a prerequisite for P1.

## 5. Consolidated host-change plan (one maintenance window, gated; each phase needs RD authorization)

**Phase 0 — Measure (read-only; no state change except throw-away `--pull never` containers)**

| # | Measurement | Command |
|---|---|---|
| M0 | Velith main **baseline gate on the existing image, no build**: pass, skip and fail counts, including that the SYS_ADMIN isolation tests ran | From the Velith main directory in WSL: `docker compose run --rm -T verifier ruff check .`; `… ruff format --check .`; `… mypy src tests`; `… pytest -q -rs` |
| M1 | VHDX sparse flag and allocated size | `fsutil sparse queryflag "<vhdx>"`; if it is sparse, `fsutil sparse queryrange "<vhdx>"` (sum the ranges). Also record Explorer's "Size on disk". |
| M2 | Per-object usage | `docker system df -v`; `docker buildx du --verbose` |
| M3 | Used bytes inside the Docker data filesystem | `docker run --rm --pull never --network none --entrypoint df python:3.12-slim -B1 /` |
| M4 | WSL distributions and their VHDX sizes | `wsl -l -v`; the Lxss registry `BasePath`, then the size of each `ext4.vhdx` |
| M5 | Restore inventory | `docker image ls --digests --no-trunc --format json`; `docker ps -a --no-trunc --format json`; `docker volume ls --format json`; `docker volume inspect $(docker volume ls -q)`; `docker network ls --format json`; `docker buildx ls`; `docker context ls --format json`; a copy of `settings-store.json` |

**Phase 1 — Back up** to `E:\docker-safety\<UTC>\`, with SHA-256 for every file.
- **B1:** the M5 inventories and `settings-store.json`.
- **B2:** each of the 6 named volumes, as tar through a read-only mount:
  `docker run --rm --pull never --network none -v <vol>:/v:ro -v <backup>:/b python:3.12-slim tar -C /v -cpf /b/<vol>.tar .`
- **B3:** `docker save` of the **locally built** images that cannot be re-pulled. The set is to be confirmed by the RD as owner of all three projects. The candidates are:
  - `velith-verifier:m0`, `velith-gate:*`, `velith-audit:i0`;
  - `mp-verifier:*`, `mini-prometheus-verifier:rm4`;
  - `districore-app`, and `districore/flutter` if it was built locally.
- **B4:** registry images are recorded by digest only, because they can be re-pulled.

**Phase 2 — Reclaim regenerable content only**
- Command: `docker builder prune --all --force`.
- It removes **no image, container or volume**.
- Velith main's gate is unaffected by construction (F12). Other projects lose only rebuild speed.

**Phase 3 — Compact**
- Quit Docker Desktop, then run `wsl --shutdown`.
- As admin, run diskpart:
  - `select vdisk file="<vhdx>"`
  - `attach vdisk readonly`
  - `compact vdisk`
  - `detach vdisk`
- Then restart Docker Desktop and measure the VHDX size again.
- **Location decision (numbers fixed now):**
  - **Stay on C:** if C: free ≥ 25.44 GB.
  - **Else move to E:** through Docker Desktop's Settings → Resources → Advanced → Disk image location, only if E: free − the compacted VHDX size ≥ 25.44 GB.
  - **Else STOP:** dedicated storage becomes a P1 prerequisite.

**Phase 4 — Verification gates** (§6). If any gate fails, restore from Phase 1.

**Phase 5 — The remaining P1 host changes** (independent of Docker; batched into the same authorization)
- **H2:** install Python 3.12.x for the current user only, with no PATH change, used through the `py -3.12` launcher (F8).
- **H3:** the Windows tokenizer check (Part B) on the 3.12 interpreter.
- **No change** to the proxy (F9; the harness sets `NO_PROXY` per process) or to Git configuration (F10; the harness clones with `-c core.autocrlf=false`).

**Phase 6 — P1 Stage-0 image pulls: separate authorization. Not part of this plan.**
- Pull by **digest**.
- Recompute the space gate before each pull.

## 6. Post-change verification gates (prove that Velith main and the shared infrastructure still work)

| Gate | Pass criterion |
|---|---|
| V1 Engine identity | `docker version` and `docker info` show Server 29.5.3, the containerd snapshotter, cgroup 2 and seccomp builtin. Context `desktop-linux` works from **both** Windows and WSL. |
| V2 Inventory | Every image ID from M5 is present and identical: 39 images, 5 containers, 6 volumes. The contents of every volume re-hash identically to the B2 tar. |
| V3 Velith main, no build | The same ruff, format, mypy and pytest sequence gives **identical pass, skip and fail counts** to M0. The isolation tests executed and were not skipped. |
| V4 Velith main, full gate | `docker compose build --no-cache verifier`, then the D31 or C-ID gate sequence, is green. *This pulls Velith's own base image `python:3.12.7-slim-bookworm`; the RD confirms this is not covered by the "no task-image pulls" rule.* |
| V5 WSL | The Ubuntu distribution starts; `/mnt/e` is readable; the Docker CLI in WSL reaches the engine. |
| V6 Ollama | `od4/Probe-OD4-Reachability.ps1` PASS, with an unchanged digest. |
| V7 Disk accounting | VHDX path and size, and C:, D: and E: free space, recorded. The P1 space rule is recomputed as PASS. |
| V8 Other projects | Image IDs are equal (V2). Their own gates are out of Velith scope but can be run by the RD. |

**Rollback:**
- Point Docker Desktop back to the original disk (if the move path was used and the old disk was retained).
- Otherwise `docker load` the B3 tar and restore B2 volumes by tar extraction.
- Re-pull the B4 registry images by digest.

## 7. Phase 0 (RD-authorized 2026-09-30: Phase 0 ONLY)

**Instruments:**
- `Phase0-Windows.ps1` (read-only): VHDX logical length and **allocated** bytes (via `GetCompressedFileSizeW`), sparse flag, WSL distribution VHDX files, drive free space, a redacted copy of the Docker settings.
- `phase0_wsl.sh` (read-only, `--pull never` everywhere): the Velith main checks on the existing `velith-verifier:m0` with no build, with git status checked before and after; `docker system df -v`, `buildx du`; the internal data-filesystem `df`; the full inventory (image IDs, digests, containers, mounts, volumes, networks, contexts; no container env); per-volume content metadata (a file-tree SHA-256 over path, mode, owner, size and content, with in-use volumes flagged).
- `phase0_wsl.sh` was validated in the sandbox against a stub `docker`.

**Decision formulas, fixed before the numbers.** GB = 10⁹ bytes.
- **Inputs:**
  - **A0** = the allocated bytes of `docker_data.vhdx`;
  - **U** = the bytes used in the internal data filesystem (`df`);
  - **R** = the reclaimable build cache (`buildx du`, cross-checked against `system df`);
  - **Cf, Ef** = free space on C: and E:;
  - **N** = 25.44 GB (A1 rule).
- **Estimated compacted size** A1\* ≈ max(U − R, 0) + 1 GB of filesystem overhead. This is an assumption. Compaction cannot go below the used bytes, and it may achieve less than A1\*.
- **Option A, remain on C:** feasible if Cf + (A0 − A1\*) ≥ N, i.e. **A1\* ≤ A0 − (N − Cf)**.
- **Option B, move to E:** feasible if Ef − A1\* ≥ N, i.e. **A1\* ≤ Ef − N**. C: then gains A0.
- **Option C, defer P1:** if neither A nor B holds even with A1\*.
- **Robustness margin:** the option is recommended only if it still holds with A1 = A1\* + 5 GB (partial compaction).

## 8. Phase 0 results and independent verification of Option A

**Evidence:** `results/phase0-windows-20260930T053232Z/`, `results/phase0-wsl-20260930T053241Z/`.

**Measured (facts):**
- **A0** (`docker_data.vhdx`) = 60,763,930,624 B: **allocated = length, not sparse**. The file occupies its full size on C:.
- **U** (internal used) = 46,745,726,976 B. The allocated-but-free space inside the disk is therefore 14.02 GB.
- **Build cache (`buildx du`, builder `default`):** Shared 10.92 GB, **Private 21.13 GB**, Reclaimable 32.06 GB. `docker system df` gives 21.13 GB reclaimable. **R = 21.13 GB**, the conservative value per the §7 cross-check rule. Shared records hold data that images also reference, so pruning them frees no bytes.
- **Free space:** Cf = 18,078,765,056 B; Ef = 71,814,492,160 B. Ubuntu `ext4.vhdx` is 6.58 GB.
- **Velith main:** HEAD `5452efc`, clean before and after. The checks on `velith-verifier:m0` (`sha256:36c4c00b…`, built 2026-09-28T11:45Z): ruff, format (132 files), mypy (132 files) and **pytest 741 passed, 0 skipped, 0 failed** (from the progress count; `-q` in addopts plus `-q` suppresses the summary line).
- **Inventory:** 40 images and 5 containers. The DistriCore database (`districore-db-1`) was running, with `districore_db_data` 102.7 MB and `districore_wal_archive` 167.8 MB. Networks unchanged.
- The builder `desktop-linux` is unreachable from WSL ("protocol not available"). The WSL current builder is `default` (docker driver, BuildKit v0.30.0).

**Formulas from §7.** N = 25.443 GB; A1\* = U − R + 1 GB = **26.62 GB**.

| Option | Condition | Estimate | Robust (+5 GB) |
|---|---|---|---|
| **A** (prune + compact, stay on C:) | A1\* ≤ A0 − (N − Cf) = 53.40 GB | 26.62 ✓, C: free after ≈ **52.2 GB** | 31.62 ✓ (≈ 47.2 GB) |
| A′ (compact only, no prune) | A1\* = U + 1 = 47.75 ≤ 53.40 | ✓, C: free ≈ 31.1 GB | 52.75 ✓, but only a **0.65 GB** margin |
| **B** (prune + compact + move to E:) | A1\* ≤ Ef − N = 46.37 GB | ✓, E: free ≈ 45.2 GB | ✓ |
| C (defer) | only if A and B both fail | not indicated | — |

**CSE verdict: Option A is confirmed, with four refinements:**
1. Take a **byte-exact VHDX backup before the prune** (two shutdown cycles), so that rollback also covers the prune.
2. **Stop the DistriCore database cleanly** before any backup or shutdown, and restart it afterwards.
3. Use the **narrower prune** `docker buildx prune --builder default --force` (no `--all`).
4. Run **detached** diskpart compaction first (no attach, so no Windows "format disk" prompt on ext4).

Option B satisfies the rule too, but adds the risk of a move for no extra capacity. Pruning is kept, rather than A′, because A′'s robust margin is 0.65 GB and it would leave C: at about 15.7 GB after P1.

**Prune-scope finding:**
- In BuildKit, prune without `--all` skips records that are **shared, internal or frontend**. `--all` additionally removes those records.
- Shared records hold data that images still reference, so removing them frees no bytes. Frontend images would only be re-downloaded on the next build that needs them.
- Therefore `docker buildx prune --builder default --force` is expected to free ≈ the Private 21.13 GB and is the narrower, sufficient operation. `--all` is unnecessary.
- The explicit `--builder default` avoids the `desktop-linux` builder, which is unreachable from WSL.
- Neither form removes images, containers, volumes or networks. Step 8 of the runbook verifies this.

**Residual uncertainty:** the shrink from compaction depends on whether freed ext4 blocks reached the VHDX as TRIM. It is measured in Step 10 and gated in Step 13.

**Procedure:** `PHASE1_RUNBOOK.md`. **Comparator:** `compare_phase0.py`, validated in the sandbox on the real Phase-0 data: all infrastructure checks PASS on identical data, the space rule currently FAILs, and injected changes to an image, a volume and pytest were all detected.
