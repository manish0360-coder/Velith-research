<#
OD-ENV Phase 0, Windows side. READ-ONLY.
Measures: the Docker data-disk VHDX (logical length, allocated size, sparse flag), the WSL
distributions and their VHDX files, drive free space, and a redacted copy of the Docker Desktop
settings. It changes nothing, stops nothing and compacts nothing.
Output: stage0\p1env\results\phase0-windows-<UTC>\phase0_windows.json (+ settings copy)
#>
$ErrorActionPreference = 'Continue'
$ts     = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$OutDir = Join-Path $PSScriptRoot "results\phase0-windows-$ts"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

Add-Type -TypeDefinition @"
using System; using System.Runtime.InteropServices;
public static class P0Alloc {
  [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
  static extern uint GetCompressedFileSizeW(string name, out uint high);
  // Bytes actually allocated on disk for sparse/compressed files; equals the length otherwise.
  public static long Allocated(string path) {
    uint high; uint low = GetCompressedFileSizeW(path, out high);
    int err = Marshal.GetLastWin32Error();
    if (low == 0xFFFFFFFF && err != 0) return -err;
    return ((long)high << 32) + low;
  }
}
"@

function FileFacts([string]$p) {
    try {
        $i = Get-Item -LiteralPath $p -Force -ErrorAction Stop
        [ordered]@{ path = $p; length_bytes = [int64]$i.Length; allocated_bytes = [P0Alloc]::Allocated($p)
                    sparse = [bool]($i.Attributes -band [IO.FileAttributes]::SparseFile)
                    attributes = $i.Attributes.ToString(); last_write_utc = $i.LastWriteTimeUtc.ToString('o') }
    } catch { [ordered]@{ path = $p; error = $_.Exception.Message } }
}

$R = [ordered]@{ utc = (Get-Date).ToUniversalTime().ToString('o'); host = $env:COMPUTERNAME }
$R.drives = @(Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Name -in 'C','D','E' } |
              ForEach-Object { [ordered]@{ drive = $_.Name; free_bytes = [int64]$_.Free; used_bytes = [int64]$_.Used } })

# Docker Desktop VHDX files
$R.docker_vhdx = @(Get-ChildItem "$env:LOCALAPPDATA\Docker\wsl" -Recurse -Filter *.vhdx -ErrorAction SilentlyContinue |
                   ForEach-Object { FileFacts $_.FullName })

# WSL distributions (wsl.exe prints UTF-16)
$prev = [Console]::OutputEncoding
try { [Console]::OutputEncoding = [Text.Encoding]::Unicode; $R.wsl_list = ((wsl.exe -l -v) 2>&1 | Out-String).Trim() }
finally { [Console]::OutputEncoding = $prev }
$R.wsl_distros = @(Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss' -ErrorAction SilentlyContinue | ForEach-Object {
    $d = Get-ItemProperty $_.PSPath
    $base = [string]$d.BasePath; if ($base.StartsWith('\\?\')) { $base = $base.Substring(4) }
    $vhdName = $(if ($d.VhdFileName) { $d.VhdFileName } else { 'ext4.vhdx' })
    [ordered]@{ name = $d.DistributionName; base_path = $base; version = $d.Version
                vhdx = $(if ($base) { FileFacts (Join-Path $base $vhdName) } else { $null }) } })

# Docker Desktop settings: redacted copy (never credentials)
$settings = "$env:APPDATA\Docker\settings-store.json"
if (Test-Path $settings) {
    $j = Get-Content $settings -Raw | ConvertFrom-Json
    foreach ($prop in @($j.PSObject.Properties)) { if ($prop.Name -match '(?i)pass|token|secret|auth|cred|proxy') { $prop.Value = '<redacted>' } }
    ($j | ConvertTo-Json -Depth 10) | Set-Content -Path (Join-Path $OutDir 'docker-settings-store.redacted.json') -Encoding UTF8
    $R.docker_settings_disk_keys = [ordered]@{}
    foreach ($prop in $j.PSObject.Properties) { if ($prop.Name -match '(?i)disk|vhd|data|size') { $R.docker_settings_disk_keys[$prop.Name] = $prop.Value } }
}

($R | ConvertTo-Json -Depth 8) | Set-Content -Path (Join-Path $OutDir 'phase0_windows.json') -Encoding UTF8
$R | ConvertTo-Json -Depth 8
"PHASE0 WINDOWS WRITTEN: $OutDir"
