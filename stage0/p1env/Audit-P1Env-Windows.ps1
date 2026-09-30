<#
P1 environment-readiness audit, native Windows side (PowerShell 5.1+).

PART A (default) is READ-ONLY. It gathers:
  OS, RAM and drive facts; Python interpreters; proxy state; Git line-ending config;
  Docker CLI/context and Docker Desktop settings; Docker VHDX locations and sizes; .wslconfig.
  It installs nothing and changes no setting, service or environment variable persistently.

PART B (-TokenizerCheck -TokPython <python.exe>) is OPT-IN. It creates an isolated venv under
  %LOCALAPPDATA%\velith-audit\venv-tokcheck, pip-installs the pinned tokenizers/huggingface_hub,
  downloads tokenizer.json at the pinned HF commit, and runs the unmodified
  check_tokenizer_equivalence.py. That is user-space only: no system or config change.

Output: stage0\p1env\results\windows-<UTC>\audit.json (+ tokenizer result under stage0\tokenizer\results\).
#>
param([switch]$TokenizerCheck, [string]$TokPython)
$ErrorActionPreference = 'Continue'
$Stage0  = Split-Path $PSScriptRoot -Parent
$ts      = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$OutDir  = Join-Path $PSScriptRoot "results\windows-$ts"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function Run([scriptblock]$sb) { try { ((& $sb) 2>&1 | Out-String).Trim() } catch { "ERROR: $($_.Exception.Message)" } }
$A = [ordered]@{ utc = (Get-Date).ToUniversalTime().ToString('o'); host = $env:COMPUTERNAME; ps_version = $PSVersionTable.PSVersion.ToString() }

# --- OS / RAM / drives
$os = Get-CimInstance Win32_OperatingSystem
$A.os = [ordered]@{ caption = $os.Caption; version = $os.Version; build = $os.BuildNumber
                    ram_total_bytes = [int64]$os.TotalVisibleMemorySize * 1024; ram_free_bytes = [int64]$os.FreePhysicalMemory * 1024 }
$A.drives = @(Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Name -in 'C','D','E' } |
              ForEach-Object { [ordered]@{ drive = $_.Name; free_bytes = [int64]$_.Free; used_bytes = [int64]$_.Used } })

# --- 1. Python interpreters (stubs under \WindowsApps\ are recorded, never executed)
$py = [ordered]@{}
$py.py_launcher_list = Run { if (Get-Command py -ErrorAction SilentlyContinue) { py -0p } else { 'py launcher not found' } }
$paths = @(Get-Command python, python3 -All -ErrorAction SilentlyContinue | ForEach-Object { $_.Source } | Select-Object -Unique)
$regPaths = @('HKCU:\Software\Python\PythonCore\*\InstallPath','HKLM:\Software\Python\PythonCore\*\InstallPath','HKLM:\Software\WOW6432Node\Python\PythonCore\*\InstallPath')
foreach ($rp in $regPaths) { Get-ItemProperty $rp -ErrorAction SilentlyContinue | ForEach-Object {
    $exe = $_.ExecutablePath; if (-not $exe -and $_.'(default)') { $exe = Join-Path $_.'(default)' 'python.exe' }
    if ($exe) { $paths += $exe } } }
$paths = @($paths | Where-Object { $_ } | Select-Object -Unique)
$py.interpreters = @(foreach ($p in $paths) {
    if ($p -match '\\WindowsApps\\') { [ordered]@{ path = $p; note = 'App Execution Alias stub (not executed)' } }
    elseif (Test-Path $p) { [ordered]@{ path = $p; info = (Run { & $p -c "import sys,platform;print(sys.version.split()[0], platform.architecture()[0], sys.prefix)" }) } }
    else { [ordered]@{ path = $p; note = 'registered but missing' } } })
$py.has_312 = [bool](($py.interpreters | Where-Object { $_.info -match '^3\.12\.' }) -or ($py.py_launcher_list -match '3\.12'))
$A.python = $py

# --- 2. Proxy state (all read-only)
$is = Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' -ErrorAction SilentlyContinue
$A.proxy = [ordered]@{
    wininet_ProxyEnable = $is.ProxyEnable; wininet_ProxyServer = $is.ProxyServer; wininet_ProxyOverride = $is.ProxyOverride
    wininet_AutoConfigURL = $is.AutoConfigURL; winhttp = (Run { netsh winhttp show proxy })
    env = [ordered]@{} }
foreach ($n in 'HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','NO_PROXY','http_proxy','https_proxy','all_proxy','no_proxy') {
    foreach ($scope in 'Process','User','Machine') { $v = [Environment]::GetEnvironmentVariable($n, $scope); if ($v) { $A.proxy.env["$scope`:$n"] = $v } } }

# --- Git (needed for the pinned clean clone, W9)
$A.git = [ordered]@{ version = (Run { git --version }); autocrlf_global = (Run { git config --global --get core.autocrlf })
                     autocrlf_system = (Run { git config --system --get core.autocrlf }) }

# --- 4/5. Docker CLI, Desktop settings, disk images
$A.docker = [ordered]@{ version = (Run { docker version --format '{{json .}}' }); context = (Run { docker context ls }) }
$settings = @("$env:APPDATA\Docker\settings-store.json", "$env:APPDATA\Docker\settings.json") | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($settings) {
    $j = Get-Content $settings -Raw | ConvertFrom-Json
    $A.docker.settings_file = $settings
    $A.docker.settings_selected = [ordered]@{}
    foreach ($prop in $j.PSObject.Properties) { if ($prop.Name -match '(?i)disk|data|memory|cpu|swap|containerd|wsl|vhd') { $A.docker.settings_selected[$prop.Name] = $prop.Value } }
}
$vhdRoots = @("$env:LOCALAPPDATA\Docker\wsl")
if ($A.docker.settings_selected -and $A.docker.settings_selected['CustomWslDistroDir']) { $vhdRoots += $A.docker.settings_selected['CustomWslDistroDir'] }
if ($A.docker.settings_selected -and $A.docker.settings_selected['dataFolder']) { $vhdRoots += $A.docker.settings_selected['dataFolder'] }
$A.docker.vhdx = @(foreach ($r in ($vhdRoots | Select-Object -Unique)) { if (Test-Path $r) {
    Get-ChildItem $r -Recurse -Filter *.vhdx -ErrorAction SilentlyContinue | ForEach-Object { [ordered]@{ path = $_.FullName; size_bytes = [int64]$_.Length; drive = $_.FullName.Substring(0,1) } } } })
$A.wslconfig = $(if (Test-Path "$env:USERPROFILE\.wslconfig") { Get-Content "$env:USERPROFILE\.wslconfig" -Raw } else { 'absent' })

# --- 3. OPT-IN tokenizer reproducibility on Windows Python
if ($TokenizerCheck) {
    $tk = [ordered]@{ python = $TokPython }
    $venv = Join-Path $env:LOCALAPPDATA 'velith-audit\venv-tokcheck'
    $tk.venv_create = Run { & $TokPython -m venv $venv }
    $vpy = Join-Path $venv 'Scripts\python.exe'
    $tk.pip = Run { & $vpy -m pip install --disable-pip-version-check "tokenizers==0.23.2" "huggingface_hub==1.33.0" }
    $env:PYTHONUTF8 = '1'; $env:PYTHONDONTWRITEBYTECODE = '1'; $env:NO_PROXY = '127.0.0.1,localhost'   # this process only
    $tk.venv_python = Run { & $vpy -c "import sys,tokenizers,huggingface_hub;print(sys.version.split()[0],tokenizers.__version__,huggingface_hub.__version__)" }
    $tk.check_output = Run { & $vpy (Join-Path $Stage0 'tokenizer\check_tokenizer_equivalence.py') --revision e434a23f91ba5b4923cf6c9d9a238eb4a08e3a11 }
    $A.tokenizer_check = $tk
}

($A | ConvertTo-Json -Depth 8) | Set-Content -Path (Join-Path $OutDir 'audit.json') -Encoding UTF8
$A | ConvertTo-Json -Depth 8
"WINDOWS AUDIT WRITTEN: $OutDir"
