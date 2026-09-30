# OD-4 read-only reachability check (native Windows, PowerShell 5.1+).
# Sends exactly two GET requests: /api/version and /api/tags. There is NO generation, NO load,
# NO create/pull/delete, and NO configuration change. It writes one JSON file under .\results\.
$ErrorActionPreference = 'Stop'
$Base          = 'http://127.0.0.1:11434'
$ExpectVersion = '0.34.4'
$P1Name        = 'velith-p1-deepseek-coder-v2:16b-c16384-np1024'
$P1Digest      = 'e196dcd918e4f54307db79c9fada1ff261c564e1df1624e20ae65d1ff0a4c45c'
$BaseName      = 'deepseek-coder-v2:16b'
$BaseDigest    = '63fb193b3a9b4322a18e8c6b250ca2e70a5ff531e962dbf95ba089b2566f2fa5'

$result = [ordered]@{ utc = (Get-Date).ToUniversalTime().ToString('o'); endpoint = $Base
                      host = $env:COMPUTERNAME; ps_version = $PSVersionTable.PSVersion.ToString() }
try {
    $ver  = Invoke-RestMethod -Method Get -Uri "$Base/api/version" -TimeoutSec 15
    $tags = Invoke-RestMethod -Method Get -Uri "$Base/api/tags"    -TimeoutSec 15
    $result.reachable = $true
    $result.version   = $ver.version
    $result.models    = @($tags.models | ForEach-Object { [ordered]@{ name = $_.name; digest = $_.digest; size = $_.size } })
    $p1   = @($tags.models | Where-Object { $_.name -eq $P1Name })
    $base = @($tags.models | Where-Object { $_.name -eq $BaseName })
    $result.check_version     = ($ver.version -eq $ExpectVersion)
    $result.check_p1_present  = ($p1.Count -eq 1)
    $result.check_p1_digest   = ($p1.Count -eq 1 -and $p1[0].digest -eq $P1Digest)
    $result.check_base_digest = ($base.Count -eq 1 -and $base[0].digest -eq $BaseDigest)
    $ok = $result.check_version -and $result.check_p1_present -and $result.check_p1_digest -and $result.check_base_digest
    $result.verdict = $(if ($ok) { 'PASS' } else { 'FAIL' })
} catch {
    $result.reachable = $false
    $result.error     = $_.Exception.Message
    $result.verdict   = 'FAIL'
}
$outDir = Join-Path $PSScriptRoot 'results'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$outFile = Join-Path $outDir ("od4-reachability-{0}.json" -f (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ'))
($result | ConvertTo-Json -Depth 6) | Set-Content -Path $outFile -Encoding UTF8
$result | ConvertTo-Json -Depth 6
"VERDICT: $($result.verdict)   evidence: $outFile"
