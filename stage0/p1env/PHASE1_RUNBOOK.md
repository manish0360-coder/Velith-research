# OD-ENV Phase 1 Runbook: Docker storage (Option A, stay on C:). NOT YET AUTHORIZED.

**Scope:** reclaim **build cache only**, then compact `docker_data.vhdx` in place.
- No image, container, volume or network is removed.
- No Docker move, no Python install, no SWE-bench pulls.
- Velith main is untouched (checked by `git status` before and after in every audit).

**Preserved (each verified by `compare_phase0.py`):**
- the 40 image IDs, including `velith-verifier:m0` `sha256:36c4c00b…` (the frozen M2/M8/M9 gate environment);
- the 5 containers and 6 DistriCore volumes (content tree hash);
- the networks;
- Velith main HEAD `5452efc`;
- the Velith checks: 741 passed, 0 skipped.

**Fixed values:**
- `TS = P1-20260930`
- Docker disk: `C:\Users\Manish Raj\AppData\Local\Docker\wsl\disk\docker_data.vhdx`
- Research folder: `E:\Projects\OpenSourceLab\repos\Velith-research\stage0\p1env` (WSL: `/mnt/e/Projects/OpenSourceLab/repos/Velith-research/stage0/p1env`)

## NEVER do during this procedure

- `docker system prune`, `docker image prune`, `docker rmi`, `docker volume prune`/`rm`, `docker container prune`/`rm`, `docker network prune`.
- `docker compose down -v` (DistriCore).
- Docker Desktop **Troubleshoot → Clean / Purge data** or **Reset to factory defaults**. Do not change Docker Desktop's disk-image location. Do not accept a Docker Desktop update.
- `wsl --unregister`, or deleting, moving or renaming any `.vhdx` (except in Rollback R, with an explicit decision).
- Clicking **Format** if Windows ever offers to format a disk. Always click **Cancel**.
- Enabling Hyper-V or using `Optimize-VHD` (neither exists on Windows 11 Home).
- Any build, commit or file change in Velith main.
- Deleting anything under `E:\docker-safety` or `D:\docker-safety` until GO is confirmed.

---

## Step 1 — WSL: record, then cleanly stop, the DistriCore database (for a consistent backup)

```bash
docker inspect districore-db-1 --format '{{.HostConfig.RestartPolicy.Name}} | {{.State.Status}} | {{.State.Health.Status}}'
docker stop --time 120 districore-db-1
docker inspect districore-db-1 --format '{{.State.Status}} {{.State.ExitCode}}'
```

- **Expected:** first `<policy> | running | healthy`; then `districore-db-1`; then `exited 0`.
- **STOP** if the exit code is not 0. Run `docker logs --tail 50 districore-db-1` and report the output.

## Step 2 — WSL: consistent baseline B0 (database stopped)

```bash
cd /mnt/e/Projects/OpenSourceLab/repos/Velith-research/stage0/p1env
bash phase0_wsl.sh
B0=results/<the phase0-wsl-... directory just printed>
python3 compare_phase0.py results/phase0-wsl-20260930T053241Z "$B0"
```

- **Expected:** every line PASS, **except possibly** `volumes: identical content tree hash (differs=['districore_db_data', 'districore_wal_archive'])`, caused by the clean-shutdown checkpoint. B0 is the baseline from here on.
- **STOP** on any other FAIL.

## Step 3 — WSL: logical backup of all 6 volumes to D:

```bash
TS=P1-20260930; mkdir -p /mnt/d/docker-safety/$TS/volumes
for v in $(docker volume ls -q); do
  docker run --rm --pull never --network none -v "$v":/v:ro -v /mnt/d/docker-safety/$TS/volumes:/b \
    python:3.12-slim tar -C /v -cpf "/b/$v.tar" . && echo "OK $v"
done
( cd /mnt/d/docker-safety/$TS/volumes && sha256sum *.tar | tee SHA256SUMS && ls -l )
```

- **Expected:** 6 `OK` lines and 6 tar files. `districore_wal_archive` is about 168 MB and `districore_db_data` about 103 MB.
- **STOP** on any tar error.

## Step 4 — Windows: stop Docker and WSL completely

1. **Quit Docker Desktop first.** Use the system tray (right-click the whale → **Quit Docker Desktop**), or run `docker desktop stop --force --timeout 60` (observed to work on 4.79). Wait 30 s.
   - *Lesson from execution 2026-09-30:* running `wsl --shutdown` while Docker Desktop is still running makes Docker Desktop **restart both distributions**. The VHDX is then live again.
2. In PowerShell (normal, not admin):
   ```powershell
   wsl --shutdown
   wsl -l -v
   Get-Process -Name 'Docker Desktop','com.docker.backend' -ErrorAction SilentlyContinue
   ```

- **Expected:** `Ubuntu` and `docker-desktop` both **Stopped**, and no process listed. Your WSL terminal closes; this is expected. Ollama (native Windows) is unaffected.

## Step 5 — Windows: full byte-exact backup of the Docker disks to E: (pre-change state; covers Rollback R)

```powershell
$TS  = 'P1-20260930'
$Src = 'C:\Users\Manish Raj\AppData\Local\Docker\wsl'
$Bk  = "E:\docker-safety\$TS"
New-Item -ItemType Directory -Force $Bk | Out-Null
(Get-PSDrive E).Free
robocopy "$Src\disk" "$Bk\disk" docker_data.vhdx /J /COPY:DAT /R:1 /W:5 /NP /LOG:"$Bk\robocopy-disk.log"; "robocopy exit: $LASTEXITCODE"
robocopy "$Src\main" "$Bk\main" ext4.vhdx /J /COPY:DAT /R:1 /W:5 /NP /LOG:"$Bk\robocopy-main.log"; "robocopy exit: $LASTEXITCODE"
$h = Get-FileHash "$Src\disk\docker_data.vhdx","$Bk\disk\docker_data.vhdx","$Src\main\ext4.vhdx","$Bk\main\ext4.vhdx" -Algorithm SHA256
$h | Format-Table Hash, Path -AutoSize
$h | Export-Csv "$Bk\SHA256.csv" -NoTypeInformation
($h[0].Hash -eq $h[1].Hash) -and ($h[2].Hash -eq $h[3].Hash)
```

- **Expected:**
  - E: free is greater than 61,000,000,000 bytes;
  - each robocopy reports `robocopy exit: 1` (one file copied);
  - the last line is **True**.
- It takes several minutes; hashing reads about 122 GB in total.
- Afterwards E: has about 11 GB free.
- **STOP** if robocopy exits with ≥ 8, or if the result is `False`. Do not continue without a verified backup.
- **The copy is only valid if** the Step 4 check passed immediately before it, **and** nothing restarted Docker or WSL between the copy and the hash. Otherwise the copy is void: redo Step 4, then Step 5. Robocopy overwrites the old copy in place.

## Step 6 — Windows: start Docker Desktop and wait for the engine

Start menu → **Docker Desktop**. Then:

```powershell
$n=0; do { Start-Sleep 5; $n++; $v = (docker version --format '{{.Server.Version}}' 2>$null) } until ($v -eq '29.5.3' -or $n -ge 60); "server: $v"
```

- **Expected:** `server: 29.5.3`.
- **STOP** if it is empty or a different version after 5 minutes.
- Then reopen the WSL terminal.

## Step 7 — WSL: keep the database stopped

```bash
docker inspect districore-db-1 --format '{{.State.Status}}'
```

If it prints `running` (its restart policy restarted it), run `docker stop --time 120 districore-db-1`. **Expected:** `exited`.

## Step 8 — WSL: reclaim build cache only, then prove nothing else changed

```bash
docker buildx ls
docker buildx du --builder default | tail -4
docker buildx prune --builder default --force
docker buildx du --builder default | tail -4
docker system df
docker run --rm --pull never --network none --entrypoint df python:3.12-slim -B1 /
B0=/mnt/e/Projects/OpenSourceLab/repos/Velith-research/stage0/p1env/<B0 from Step 2>
diff <(cut -d'|' -f1 "$B0/inventory/images_inspect.psv" | sort -u) <(docker image ls -a -q --no-trunc | sort -u) && echo IMAGES-UNCHANGED
diff <(cut -d'|' -f1 "$B0/inventory/containers_inspect.psv" | sort) <(docker ps -aq --no-trunc | sort) && echo CONTAINERS-UNCHANGED
diff <(ls "$B0/volumes" | sed 's/\.json$//' | sort) <(docker volume ls -q | sort) && echo VOLUMES-UNCHANGED
```

- **Expected:**
  - `default*` shows `running`;
  - before the prune: Shared about 10.92 GB, Private about 21.13 GB;
  - the prune ends with `Total:` of about 21 GB;
  - after the prune: **Private about 0 B, Shared about 10.92 GB** (the records whose data belongs to images are kept);
  - `df` Used drops from 46.75 GB to about **25.6 GB**;
  - all three `…-UNCHANGED` lines appear.
- **STOP, then Rollback R**, if any `diff` prints differences.
- **STOP and report** (do not compact) if Used dropped by less than 15 GB.

## Step 9 — Windows: stop Docker and WSL again

Repeat Step 4. If the database auto-restarted, first run Step 7 in WSL. Then:

```powershell
(Get-Item 'C:\Users\Manish Raj\AppData\Local\Docker\wsl\disk\docker_data.vhdx').Length
```

**Expected:** about 60,763,930,624. The prune does not shrink the file.

## Step 10 — Windows, **PowerShell as Administrator**: compact in place (Windows 11 Home: built-in `diskpart`)

```powershell
$Vhdx = 'C:\Users\Manish Raj\AppData\Local\Docker\wsl\disk\docker_data.vhdx'
wsl -l -v
$dp = Join-Path $env:TEMP 'velith-compact.txt'
Set-Content -Path $dp -Encoding ASCII -Value "select vdisk file=`"$Vhdx`"", "compact vdisk", "exit"
Get-Content $dp
diskpart /s $dp
(Get-Item $Vhdx).Length
```

- **Expected:**
  - both distributions Stopped;
  - `DiskPart successfully selected the virtual disk file.`, then a progress count to `100 percent completed`, then `DiskPart successfully compacted the virtual disk file.`;
  - the new length is smaller.
- Target: about 26–27 GB if TRIM information is present. How much it actually shrinks is unknown until measured.
- **If** diskpart reports the file is in use, Docker or WSL is not fully stopped. Repeat Step 9.
- **If** diskpart refuses to compact a detached disk, use this fallback (and **Cancel** any "format disk" prompt):
  ```powershell
  Set-Content -Path $dp -Encoding ASCII -Value "select vdisk file=`"$Vhdx`"", "attach vdisk readonly", "compact vdisk", "detach vdisk", "exit"
  diskpart /s $dp
  ```
- **STOP and report** on any other diskpart error. Do not retry blindly.

## Step 11 — Windows: start Docker Desktop

Repeat Step 6. **Expected:** `server: 29.5.3`. **STOP, then Rollback R**, if Docker fails to start.

## Step 12 — Windows: post-change storage audit

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "E:\Projects\OpenSourceLab\repos\Velith-research\stage0\p1env\Phase0-Windows.ps1"
```

This prints `PHASE0 WINDOWS WRITTEN: …\phase0-windows-<ts>`.

## Step 13 — WSL: post-change infrastructure audit and GO/NO-GO (database still stopped; Step 7 if needed)

```bash
cd /mnt/e/Projects/OpenSourceLab/repos/Velith-research/stage0/p1env
bash phase0_wsl.sh
B1=results/<the new phase0-wsl-... directory>
W1=results/<the phase0-windows-... directory from Step 12>
python3 compare_phase0.py "$B0" "$B1" "$W1"
```

- **Expected:** every line PASS and `VERDICT: GO`.
- **Rollback R** on any infrastructure FAIL.
- If **only** the space rule fails, the state is valid but too small: no rollback. That is a decision point between Option B (E:) and Option C (defer).

## Step 14 — WSL: restore DistriCore to its original running state

```bash
docker start districore-db-1
sleep 60; docker inspect districore-db-1 --format '{{.State.Status}} {{.State.Health.Status}}'
```

**Expected:** `running healthy`. If it shows `starting`, re-check after another minute.

## GO / NO-GO for pulling the five P1 images (the pulls need a separate authorization)

**GO requires all of the following:**
- `compare_phase0.py` prints `VERDICT: GO`:
  - identical image, container, volume and network inventories;
  - the same engine;
  - Velith checks identical to B0 (741 passed, 0 skipped), same HEAD, clean tree;
  - **C: free ≥ 25,442,795,777 bytes**.
- The database is healthy again (Step 14).
- Your authorization.

**Pull discipline (Stage 0):**
- Pull by digest, one image at a time.
- Before each pull: C: free ≥ 2.5 × that image's compressed size + 10 GB.
- After each pull: re-measure.
- Stop if C: free is below 10 GB.

## Rollback R: restore the exact pre-change Docker disk from E:

1. Quit Docker Desktop, run `wsl --shutdown`, then `wsl -l -v` (Stopped).
2. In PowerShell:
   ```powershell
   $Vhdx = 'C:\Users\Manish Raj\AppData\Local\Docker\wsl\disk\docker_data.vhdx'; $Bk = 'E:\docker-safety\P1-20260930'
   Rename-Item $Vhdx 'docker_data.vhdx.failed'
   (Get-PSDrive C).Free
   ```
3. If C: free is below 66,000,000,000 bytes, **STOP**. Deleting `docker_data.vhdx.failed` is **your** explicit decision (the E: backup is hash-verified).
4. Restore and verify:
   ```powershell
   robocopy "$Bk\disk" 'C:\Users\Manish Raj\AppData\Local\Docker\wsl\disk' docker_data.vhdx /J /COPY:DAT /R:1 /W:5 /NP; "robocopy exit: $LASTEXITCODE"
   (Get-FileHash $Vhdx -Algorithm SHA256).Hash -eq (Import-Csv "$Bk\SHA256.csv")[0].Hash
   ```
   **Expected:** `robocopy exit: 1`, then `True`.
5. Start Docker (Step 6).
6. Run `phase0_wsl.sh`, then `compare_phase0.py "$B0" <new>`. **Expected:** INFRA UNCHANGED: PASS. The build cache is restored too.
7. Volume-level fallback: extract the tar files from `D:\docker-safety\P1-20260930\volumes` into the matching volumes. Do this only on explicit decision.

---

## Automated execution of Steps 6–14 (added 2026-09-30)

**Precondition met:**
- the volume tar files are on `E:\docker-safety\P1-20260930\volumes`, not D:;
- the VHDX copies are hash-verified (`C4EBE6D9…`, `CE733920…`);
- the post-stop baseline is B0 = `results/phase0-wsl-20260930T064850Z`. It differs from Phase 0 only in `districore_db_data`, as expected after the clean shutdown.

**`Phase1-Execute.ps1`** applies exactly the steps above, with the same hard stops. It runs in three invocations:

| Run | Shell | Covers |
|---|---|---|
| `-Phase Prune` | normal | Steps 6–9 (with Step 7 DB guard) |
| `-Phase Compact` | Administrator | Step 10, detached only; no automatic attach fallback |
| `-Phase Verify` | normal | Steps 11–14, with GO/NO-GO |

- Docker Desktop is never started elevated.
- WSL-side logic: `phase1_wsl_steps.sh`, validated in the sandbox against a stub `docker`, including detection of an injected inventory change.
- Evidence: `results/phase1-<UTC>/`.
