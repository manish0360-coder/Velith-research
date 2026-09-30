<#
OD-ENV Phase 1 execution (PHASE1_RUNBOOK.md Steps 6-14) with hard stops, in three runs:
  -Phase Prune    normal PowerShell  : start Docker, prechecks, buildx cache prune (no --all), verify, stop Docker+WSL
  -Phase Compact  ADMIN PowerShell   : diskpart compact of the DETACHED docker_data.vhdx (no attach -> no format prompt)
  -Phase Verify   normal PowerShell  : restart Docker, re-audit, compare_phase0 vs B0, restart DistriCore DB, Velith check
Docker Desktop is never started from an elevated shell. No image pulls; no image/container/volume/network removal;
no Docker move; Velith main is read-only. Evidence: stage0\p1env\results\phase1-<UTC>\
#>
param([Parameter(Mandatory = $true)][ValidateSet('Prune', 'Compact', 'Verify')][string]$Phase)
$ErrorActionPreference = 'Continue'
$P1Env  = 'E:\Projects\OpenSourceLab\repos\Velith-research\stage0\p1env'
$WslEnv = '/mnt/e/Projects/OpenSourceLab/repos/Velith-research/stage0/p1env'
$B0     = 'results/phase0-wsl-20260930T064850Z'
$Vhdx   = 'C:\Users\Manish Raj\AppData\Local\Docker\wsl\disk\docker_data.vhdx'
$DDExe  = 'C:\Program Files\Docker\Docker\Docker Desktop.exe'
$Bk     = 'E:\docker-safety\P1-20260930\docker-disk'
$Distro = 'Ubuntu'; $WslUser = 'manish_raj'
$Cur    = Join-Path $P1Env 'results\phase1-current.txt'
if ($Phase -eq 'Prune') {
    $name = 'phase1-' + (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ'); Set-Content $Cur $name
} else {
    if (-not (Test-Path $Cur)) { Write-Host 'FAIL: run -Phase Prune first'; exit 1 }; $name = (Get-Content $Cur).Trim()
}
$Out = Join-Path $P1Env "results\$name"; $WslOut = "$WslEnv/results/$name"
New-Item -ItemType Directory -Force $Out | Out-Null
Start-Transcript -Path (Join-Path $Out "transcript-$Phase.txt") | Out-Null
$SumFile = Join-Path $Out 'summary.json'
$S = [ordered]@{}; if (Test-Path $SumFile) { (Get-Content $SumFile -Raw | ConvertFrom-Json).PSObject.Properties | ForEach-Object { $S[$_.Name] = $_.Value } }
$S.Remove('hard_stop'); $S.Remove('next_action')

function Save { ($S | ConvertTo-Json -Depth 6) | Set-Content $SumFile -Encoding UTF8 }
function Act([string]$a) { Write-Host "`n=== ACTION: $a" -ForegroundColor Cyan }
function Ok([string]$r, [string]$next) { Write-Host "RESULT: $r"; Write-Host 'PASS' -ForegroundColor Green; if ($next) { Write-Host "NEXT ACTION: $next" } }
function Halt([string]$r, [string]$next) {
    Write-Host "RESULT: $r"; Write-Host 'FAIL -- HARD STOP' -ForegroundColor Red; Write-Host "NEXT ACTION: $next"
    $S.hard_stop = "[$Phase] $r"; $S.next_action = $next; Save; Stop-Transcript | Out-Null; exit 1 }
function IsAdmin { ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator) }
function WslStep([string]$sub) { & wsl.exe -d $Distro -u $WslUser -- bash "$WslEnv/phase1_wsl_steps.sh" $sub $WslOut | Out-Host; return $LASTEXITCODE }
function WslState { $p = [Console]::OutputEncoding
    try { [Console]::OutputEncoding = [Text.Encoding]::Unicode; return ((wsl.exe -l -v) | Out-String) } finally { [Console]::OutputEncoding = $p } }
function DockerProcs { @(Get-Process -Name 'Docker Desktop', 'com.docker.backend', 'com.docker.build', 'vmmemWSL' -ErrorAction SilentlyContinue) }
function AllStopped { $w = WslState; return (($w -match 'Ubuntu\s+Stopped') -and ($w -match 'docker-desktop\s+Stopped') -and ((DockerProcs).Count -eq 0)) }
function WaitEngine { for ($i = 0; $i -lt 72; $i++) { $v = (& docker version --format '{{.Server.Version}}' 2>$null); if ($v -eq '29.5.3') { return $true }; Start-Sleep 5 }; return $false }
function WaitWslDocker { for ($i = 0; $i -lt 36; $i++) { $v = (& wsl.exe -d $Distro -u $WslUser -- docker version --format '{{.Server.Version}}' 2>$null | Out-String).Trim(); if ($v -eq '29.5.3') { return $true }; Start-Sleep 5 }; return $false }
function StartDocker { Start-Process -FilePath $DDExe; if (-not (WaitEngine)) { return $false }; return (WaitWslDocker) }   # engine AND Ubuntu WSL integration
function StopAll {
    & docker desktop stop | Out-Host
    for ($i = 0; $i -lt 30 -and (@(Get-Process -Name 'Docker Desktop', 'com.docker.backend' -ErrorAction SilentlyContinue).Count -gt 0); $i++) { Start-Sleep 5 }
    if (@(Get-Process -Name 'Docker Desktop', 'com.docker.backend' -ErrorAction SilentlyContinue).Count -gt 0) { return $false }  # never wsl --shutdown under a live Docker Desktop
    & wsl.exe --shutdown; Start-Sleep 15
    if (-not (AllStopped)) { return $false }
    Start-Sleep 20; return (AllStopped) }                                                                                         # detect auto-restart
function CFree { [int64](Get-PSDrive C).Free }

switch ($Phase) {
'Prune' {
    if (IsAdmin) { Halt 'run -Phase Prune from a NORMAL (non-admin) PowerShell' 'Open a normal PowerShell and re-run' }
    Act 'Precondition: Docker/WSL stopped; backup copies intact (full SHA-256)'
    if (-not (AllStopped)) { Halt "Docker/WSL not fully stopped:`n$(WslState)" 'docker desktop stop; wsl --shutdown; re-run -Phase Prune' }
    $h1 = (Get-FileHash "$Bk\docker_data.vhdx" -Algorithm SHA256).Hash; $h2 = (Get-FileHash "$Bk\ext4.vhdx" -Algorithm SHA256).Hash
    $S.backup_sha256 = [ordered]@{ docker_data_vhdx = $h1; ext4_vhdx = $h2 }
    if (-not $h1 -or -not $h2 -or -not $h1.StartsWith('C4EBE6D915B182C1A24F25BFF081F52630A584B19E8985E4977DA4FE') -or -not $h2.StartsWith('CE7339208404904419D28BD1527A94D603AE768764E1DB0B16A7FC27')) {
        Halt "backup hash differs from the verified value: $h1 / $h2" 'Do not proceed; report the hashes' }
    $S.vhdx_before_bytes = [int64](Get-Item $Vhdx).Length; $S.c_free_before_bytes = CFree; Save
    Ok "backups intact; VHDX $($S.vhdx_before_bytes) B; C: free $($S.c_free_before_bytes) B"

    Act 'Start Docker Desktop; wait for engine 29.5.3'
    if (-not (StartDocker)) { Halt 'engine or Ubuntu WSL integration not ready within 9 min' 'Check the Docker Desktop UI (Settings > Resources > WSL integration); do not prune' }
    Ok 'engine 29.5.3'

    Act 'Velith check; DistriCore DB stopped; P1 images absent; volumes present; inventory == B0'
    if ((WslStep velith) -ne 0)   { Halt 'Velith main HEAD/clean changed' 'Inspect Velith main; do not prune' }
    if ((WslStep db-stop) -ne 0)  { Halt 'districore-db-1 not cleanly stopped' 'docker logs --tail 50 districore-db-1' }
    if ((WslStep precheck) -ne 0) { Halt 'precheck failed (see output above)' 'Report the named diff file; do not prune' }
    Ok 'precheck passed'

    Act 'docker buildx prune --builder default --force (build cache only), then verify'
    if ((WslStep prune) -ne 0) { Halt 'prune verification failed (see output above)' 'Report output; Rollback R is available' }
    $S.prune_numbers = (Get-Content (Join-Path $Out 'prune_numbers.txt') -Raw).Trim(); Save
    Ok $S.prune_numbers

    Act 'Stop Docker Desktop (graceful), then wsl --shutdown; verify stopped and staying stopped'
    if ((WslStep db-stop) -ne 0) { Halt 'districore-db-1 restarted and could not be stopped cleanly' 'docker logs --tail 50 districore-db-1' }
    if (-not (StopAll)) { Halt "not fully stopped / restarted:`n$(WslState)`n$((DockerProcs | Select-Object Name, Id | Out-String))" 'Quit Docker Desktop from the tray, then wsl --shutdown, then re-check' }
    $S.vhdx_after_prune_bytes = [int64](Get-Item $Vhdx).Length; Save
    Ok "fully stopped; VHDX $($S.vhdx_after_prune_bytes) B" 'Open PowerShell AS ADMINISTRATOR and run -Phase Compact'
}
'Compact' {
    if (-not (IsAdmin)) { Halt 'run -Phase Compact from PowerShell AS ADMINISTRATOR' 'Re-run elevated' }
    if (-not $S.prune_numbers) { Halt '-Phase Prune has not completed' 'Run -Phase Prune first' }
    Act 'Verify stopped; diskpart select vdisk + compact vdisk (detached)'
    if (-not (AllStopped)) { Halt "Docker/WSL running:`n$(WslState)" 'Quit Docker Desktop, wsl --shutdown, re-run -Phase Compact' }
    $dp = Join-Path $Out 'diskpart-compact.txt'
    Set-Content -Path $dp -Encoding ASCII -Value "select vdisk file=`"$Vhdx`"", 'compact vdisk', 'exit'
    $dpOut = (& diskpart /s $dp | Out-String); $dpOut | Set-Content (Join-Path $Out 'diskpart-output.txt'); Write-Host $dpOut
    if ($dpOut -notmatch 'successfully compacted') { Halt 'diskpart did not report success' 'Report diskpart-output.txt; do NOT retry with attach until reviewed' }
    $S.vhdx_after_compact_bytes = [int64](Get-Item $Vhdx).Length; $S.c_free_after_bytes = CFree; Save
    Ok ("VHDX {0:N0} -> {1:N0} B; C: free {2:N0} -> {3:N0} B" -f [int64]$S.vhdx_before_bytes, $S.vhdx_after_compact_bytes, [int64]$S.c_free_before_bytes, $S.c_free_after_bytes) 'Close this admin window; in a NORMAL PowerShell run -Phase Verify'
}
'Verify' {
    if (IsAdmin) { Halt 'run -Phase Verify from a NORMAL (non-admin) PowerShell' 'Open a normal PowerShell and re-run' }
    if (-not $S.vhdx_after_compact_bytes) { Halt '-Phase Compact has not completed' 'Run -Phase Compact first' }
    Act 'Restart Docker Desktop'
    if (-not (StartDocker)) { Halt 'engine or Ubuntu WSL integration not ready after restart' 'Report; check Docker Desktop Settings > Resources > WSL integration (Ubuntu). Rollback R only if the ENGINE fails' }
    Ok 'engine 29.5.3'

    Act 'Phase-0 Windows + WSL re-audit; compare_phase0.py vs B0'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $P1Env 'Phase0-Windows.ps1') | Out-Null
    $W1 = (Get-ChildItem (Join-Path $P1Env 'results') -Directory -Filter 'phase0-windows-*' | Sort-Object Name | Select-Object -Last 1).Name
    if ((WslStep db-stop) -ne 0) { Halt 'districore-db-1 could not be kept stopped for the audit' 'docker logs --tail 50 districore-db-1' }
    & wsl.exe -d $Distro -u $WslUser -- bash "$WslEnv/phase0_wsl.sh" | Out-Host
    $B1 = (Get-ChildItem (Join-Path $P1Env 'results') -Directory -Filter 'phase0-wsl-*' | Sort-Object Name | Select-Object -Last 1).Name
    $cmp = (& wsl.exe -d $Distro -u $WslUser --cd $WslEnv -- python3 compare_phase0.py $B0 "results/$B1" "results/$W1" | Out-String)
    $cmp | Set-Content (Join-Path $Out 'compare_phase0.txt'); Write-Host $cmp
    $S.b1 = $B1; $S.w1 = $W1; $S.compare = $cmp.Trim(); Save
    $infraFails = @(($cmp -split "`n") | Where-Object { $_ -match '^\[FAIL\]' -and $_ -notmatch 'space rule' })
    if ($infraFails.Count -gt 0) { Halt "infrastructure regression: $($infraFails -join '; ')" 'Keep the DB stopped; Rollback R (PHASE1_RUNBOOK.md)' }
    $go = $cmp -match 'VERDICT: GO'
    Ok ('infrastructure unchanged; verdict ' + $(if ($go) { 'GO' } else { 'NO-GO (space rule only)' }))

    Act 'Start districore-db-1 (wait for healthy); final Velith check'
    if ((WslStep db-start) -ne 0) { Halt 'districore-db-1 did not become healthy' 'docker logs --tail 80 districore-db-1' }
    if ((WslStep velith) -ne 0)   { Halt 'Velith main HEAD/clean changed' 'Inspect Velith main git status' }
    $S.verdict = $(if ($go) { 'GO' } else { 'NO-GO' }); $S.finished_utc = (Get-Date).ToUniversalTime().ToString('o'); Save
    Ok 'DistriCore healthy; Velith 5452efc clean'

    Write-Host "`n===== PHASE 1 SUMMARY ====="
    Write-Host "1 cache:     $($S.prune_numbers)"
    Write-Host ("2 VHDX:      {0:N0} -> {1:N0} B" -f [int64]$S.vhdx_before_bytes, [int64]$S.vhdx_after_compact_bytes)
    Write-Host ("3 C: free:   {0:N0} -> {1:N0} B (rule 25,442,795,777)" -f [int64]$S.c_free_before_bytes, [int64]$S.c_free_after_bytes)
    Write-Host '4 inventory: unchanged vs B0   5 DistriCore: healthy   6 Velith: 5452efc clean'
    Write-Host "7 verdict:   $($S.verdict)   evidence: $Out"
    Write-Host ('8 next:      ' + $(if ($go) { 'P1 Stage-0 image admission (pull by digest, one at a time) - needs RD authorization' } else { 'RD decision: Option B (E:) vs C (defer)' }))
}
}
Stop-Transcript | Out-Null
