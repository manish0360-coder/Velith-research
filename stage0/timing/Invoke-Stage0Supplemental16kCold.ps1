# Stage-0 supplemental timing request S2 (COLD): ONE near-maximum prompt at num_ctx = 16384 (Velith-research; evidence only).
#
# Why S2: S1 (supp16k-20260929T170742Z) fitted exactly (16,108 prompt tokens) but its prompt-evaluation time was
# contaminated by the server prompt cache: two interrupted S1 attempts had sent the identical request. S2 is S1 with a
# FRESH nonce ('stage0-J', never sent before), so the cached prefix shared with any earlier prompt ends after the
# nonce token (about 9 tokens); the remaining ~16,099 prompt tokens must be evaluated cold. Same N=304, so the
# token model predicts exactly 16,108 prompt tokens again (a single-letter nonce is one token, as observed for A/D).
# Contamination guard: S2 refuses to run if any earlier real S2 attempt directory exists (a re-attempt would be
# cache-contaminated by the first); a re-attempt needs a new nonce and a new script revision.
#
# Derived from S1 (Invoke-Stage0Supplemental16k.ps1, SHA-256 75ce8bee...ca2f); the S1 header follows.
#
# Stage-0 supplemental timing request S1: ONE near-maximum prompt at num_ctx = 16384 (Velith-research; evidence only).
#
# Why: R2 run-20260929T113401Z run #7 (16k target, N=316 functions) was rejected with HTTP 400, "the prompt is longer
# than the context length currently available to the model". Its prompt was sized by an assumed bytes/token ratio, but
# the ratio falls as function indices gain digits. The exact token model, fitted to the measured prompt_eval_count of
# R0/R2 (N=36: 1752; N=71: 3467; N=160: 8188; all reproduced exactly), is:
#     tokens(N) = 48 + 43*min(N,10) + 49*(min(N,100)-10) + 55*(N-100)      for 100 < N, single-letter nonce
# (48 = BOS + "User:" template + header + footer + "Assistant:"; +6 tokens per extra index digit, since digits tokenize singly.)
# S1 uses N = 304, the largest N with tokens(N) <= 16384 - 256 = 16128:
#     predicted prompt tokens = 16108; generation reserve 256; total <= 16364 <= 16384 (20 tokens of slack).
#
# Fixed settings, identical to the approved design: model deepseek-coder-v2:16b, temperature 0, seed 0, num_predict 256,
# num_ctx 16384, request timeout 1800 s. No OD-3 value is selected by this request.
# Scope: only the running local Ollama server (/api/version, /api/tags, /api/ps, /api/generate). No pull/create/copy/delete,
# no configuration change, no Docker, no Velith repository access. Writes only under -OutRoot.
# Windows PowerShell 5.1 compatible.

[CmdletBinding()]
param(
    [string]$OllamaUrl = 'http://127.0.0.1:11434',
    [string]$Model = 'deepseek-coder-v2:16b',
    [string]$ExpectedIdPrefix = '63fb193b3a9b',
    [string]$OutRoot = '',
    [switch]$DryRun
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$TEMPERATURE = 0.0; $SEED = 0; $NUM_PREDICT = 256; $NUM_CTX = 16384; $REQUEST_TIMEOUT_SEC = 1800
$NONCE = 'stage0-J'; $NUM_FUNCTIONS = 304
$PREDICTED_PROMPT_TOKENS = 16108
$EXPECTED_PROMPT_BYTES = 29295
$EXPECTED_PROMPT_SHA256 = '977f160298bb7838490d2e90c2fdf86ddec354edaaf9d0e33cd3a919bf3aa9aa'
$MIN_FREE_RAM_BEFORE_COLD_LOAD = 16GB   # R2 loaded 16384 safely from 16.57 GB free; refuse a cold load below 16 GB

$ScriptDir = Split-Path -Parent $PSCommandPath
if ([string]::IsNullOrEmpty($OutRoot)) { $OutRoot = Join-Path $ScriptDir 'runs' }
$GeneratorPath = Join-Path $ScriptDir 'Stage0SyntheticPrompt.ps1'
. $GeneratorPath
$LogDir = Join-Path $env:LOCALAPPDATA 'Ollama'
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Write-Utf8File([string]$Path, [string]$Text) { [System.IO.File]::WriteAllText($Path, $Text, $Utf8NoBom) }
function Get-P($Obj, [string]$Name) {
    if ($null -eq $Obj) { return $null }
    $p = $Obj.PSObject.Properties[$Name]
    if ($null -eq $p) { return $null }
    return $p.Value
}
function Get-FreeRamBytes { return [int64](Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory * 1024 }
function Invoke-Get([string]$Path) { return (Invoke-WebRequest -Uri ($OllamaUrl + $Path) -Method Get -UseBasicParsing -TimeoutSec 60).Content }
function Get-ServerProcesses {
    return @(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(ollama|ollama app|llama-server)\.exe$' } | ForEach-Object {
        $created = $null; if ($null -ne $_.CreationDate) { $created = $_.CreationDate.ToUniversalTime().ToString('o') }
        [ordered]@{ pid = $_.ProcessId; parent_pid = $_.ParentProcessId; name = $_.Name; creation_utc = $created; command_line = $_.CommandLine }
    })
}
function Get-OllamaProcessMemory {
    return @(Get-Process | Where-Object { $_.ProcessName -match 'ollama|llama' } | ForEach-Object {
        [ordered]@{ name = $_.ProcessName; id = $_.Id; working_set = $_.WorkingSet64; private_bytes = $_.PrivateMemorySize64 }
    })
}
function Get-PsModelEntry([string]$PsRaw) {
    $ps = $PsRaw | ConvertFrom-Json
    foreach ($m in @(Get-P $ps 'models')) { if ((Get-P $m 'name') -eq $Model -or (Get-P $m 'model') -eq $Model) { return $m } }
    return $null
}
function Invoke-GenerateCapture([byte[]]$BodyBytes, [int]$TimeoutSec) {
    try {
        $r = Invoke-WebRequest -Uri ($OllamaUrl + '/api/generate') -Method Post -Body $BodyBytes -ContentType 'application/json' -UseBasicParsing -TimeoutSec $TimeoutSec
        return [pscustomobject]@{ Ok = $true; Status = [int]$r.StatusCode; Body = $r.Content; Error = $null }
    }
    catch {
        $err = $_
        $status = $null; $errBody = $null
        $resp = Get-P $err.Exception 'Response'
        if ($null -ne $resp) {
            try { $status = [int]$resp.StatusCode } catch { $status = $null }
            try { $reader = New-Object System.IO.StreamReader($resp.GetResponseStream()); $errBody = $reader.ReadToEnd(); $reader.Close() } catch { $errBody = $null }
        }
        if ([string]::IsNullOrEmpty($errBody) -and $null -ne $err.ErrorDetails) { $errBody = $err.ErrorDetails.Message }
        return [pscustomobject]@{ Ok = $false; Status = $status; Body = $errBody; Error = $err.Exception.Message }
    }
}

# ---- deterministic prompt (verified against the independently computed hash) ----
$text = New-Stage0SyntheticPrompt -Nonce $NONCE -NumFunctions $NUM_FUNCTIONS
$promptBytes = Get-Stage0Utf8Bytes -Text $text
$promptSha = Get-Stage0Sha256Hex -Bytes $promptBytes
if ($promptBytes.Length -ne $EXPECTED_PROMPT_BYTES -or $promptSha -ne $EXPECTED_PROMPT_SHA256) {
    throw "Prompt determinism check failed: bytes=$($promptBytes.Length) sha256=$promptSha"
}
$opts = [ordered]@{ temperature = $TEMPERATURE; seed = $SEED; num_predict = $NUM_PREDICT; num_ctx = $NUM_CTX }
$bodyJson = ([ordered]@{ model = $Model; prompt = $text; stream = $false; options = $opts }) | ConvertTo-Json -Depth 5 -Compress
$bodyBytes = $Utf8NoBom.GetBytes($bodyJson)
$requestSha = Get-Stage0Sha256Hex -Bytes $bodyBytes

$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$kind = 'supp16k-cold'; if ($DryRun) { $kind = 'supp16k-cold-dryrun' }
# Contamination guard: any earlier REAL S2 attempt (completed or interrupted) makes a new real attempt non-cold.
if (-not $DryRun -and (Test-Path -LiteralPath $OutRoot)) {
    $prior = @(Get-ChildItem -LiteralPath $OutRoot -Directory -Filter 'supp16k-cold-2*' -ErrorAction SilentlyContinue)
    if ($prior.Count -gt 0) { throw ('Contamination guard: an earlier S2 attempt exists (' + $prior[0].Name + '); a re-attempt needs a new nonce and script revision') }
}
$RunDir = Join-Path $OutRoot ($kind + '-' + $stamp)
New-Item -ItemType Directory -Path $RunDir -Force | Out-Null
Write-Utf8File (Join-Path $RunDir 'S2_prompt.txt') $text
Write-Utf8File (Join-Path $RunDir 'S2_request.json') $bodyJson

$rec = [ordered]@{
    experiment = 'velith-stage0-timing-supplemental-S2-cold'
    basis = 'S1 supp16k-20260929T170742Z (prompt-eval cache-contaminated); RD decision OD-3 context regime 16384'
    mode = $kind; status = 'STARTED'; started_utc = (Get-Date).ToUniversalTime().ToString('o')
    script_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $PSCommandPath).Hash.ToLower()
    generator_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $GeneratorPath).Hash.ToLower()
    model = $Model; num_ctx_sent = $NUM_CTX; temperature = $TEMPERATURE; seed = $SEED; num_predict = $NUM_PREDICT; request_timeout_sec = $REQUEST_TIMEOUT_SEC
    nonce = $NONCE; num_functions = $NUM_FUNCTIONS; prompt_bytes = $promptBytes.Length; prompt_sha256 = $promptSha; request_sha256 = $requestSha
    predicted_prompt_tokens = $PREDICTED_PROMPT_TOKENS; predicted_total_tokens_max = ($PREDICTED_PROMPT_TOKENS + $NUM_PREDICT)
    advertised_context_length = 163840; od3_values_selected = $false; error = $null
}

try {
    if (-not $DryRun) {
        $ver = Invoke-Get '/api/version'; $tags = Invoke-Get '/api/tags'; $ps0 = Invoke-Get '/api/ps'
        Write-Utf8File (Join-Path $RunDir 'pre_version.json') $ver; Write-Utf8File (Join-Path $RunDir 'pre_tags.json') $tags; Write-Utf8File (Join-Path $RunDir 'pre_ps.json') $ps0
        $found = $null
        foreach ($m in @(Get-P ($tags | ConvertFrom-Json) 'models')) { if ((Get-P $m 'name') -eq $Model) { $found = $m } }
        if ($null -eq $found) { throw "Model $Model is not listed by /api/tags" }
        $digest = [string](Get-P $found 'digest'); $rec['model_digest'] = $digest
        if (-not $digest.StartsWith($ExpectedIdPrefix)) { throw "Model digest $digest does not start with $ExpectedIdPrefix" }
        $rec['ollama_version'] = Get-P ($ver | ConvertFrom-Json) 'version'
        $rec['server_processes_start'] = Get-ServerProcesses
        $free0 = Get-FreeRamBytes; $rec['free_ram_bytes_before'] = $free0
        $loaded = Get-PsModelEntry $ps0
        $rec['preloaded_context_length'] = Get-P $loaded 'context_length'
        if ($null -eq $loaded -and $free0 -lt $MIN_FREE_RAM_BEFORE_COLD_LOAD) {
            throw "Safety stop: free RAM $free0 B is below 16 GB for a cold load at num_ctx 16384; close other applications and retry"
        }

        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $gen = Invoke-GenerateCapture $bodyBytes $REQUEST_TIMEOUT_SEC
        $sw.Stop()
        $rec['wall_time_ms'] = $sw.ElapsedMilliseconds
        $rec['http_status'] = $gen.Status
        if (-not $gen.Ok) {
            $rec['error_message'] = $gen.Error; $rec['error_body'] = $gen.Body
            Write-Utf8File (Join-Path $RunDir 'S2_error.json') (([ordered]@{ http_status = $gen.Status; error_message = $gen.Error; error_body = $gen.Body }) | ConvertTo-Json -Depth 4)
            throw ("S2 /api/generate failed (HTTP " + $gen.Status + "): " + $gen.Error)
        }
        Write-Utf8File (Join-Path $RunDir 'S2_response.json') $gen.Body
        $j = $gen.Body | ConvertFrom-Json
        foreach ($f in @('done', 'done_reason', 'total_duration', 'load_duration', 'prompt_eval_count', 'prompt_eval_duration', 'eval_count', 'eval_duration')) { $rec[$f] = Get-P $j $f }
        $pec = Get-P $j 'prompt_eval_count'; $ped = Get-P $j 'prompt_eval_duration'; $ec = Get-P $j 'eval_count'; $ed = Get-P $j 'eval_duration'
        if ($pec -and $ped) { $rec['prompt_tokens_per_s'] = [double]$pec / ([double]$ped / 1e9) }
        if ($ec -and $ed) { $rec['gen_tokens_per_s'] = [double]$ec / ([double]$ed / 1e9) }
        if ($pec) { $rec['prompt_tokens_minus_predicted'] = [int]$pec - $PREDICTED_PROMPT_TOKENS }
        $ps1 = Invoke-Get '/api/ps'; Write-Utf8File (Join-Path $RunDir 'post_ps.json') $ps1
        $pm = Get-PsModelEntry $ps1
        $rec['ps_size'] = Get-P $pm 'size'; $rec['ps_context_length'] = Get-P $pm 'context_length'
        $rec['ollama_processes'] = Get-OllamaProcessMemory
        $rec['free_ram_bytes_after'] = Get-FreeRamBytes
        $rec['server_processes_end'] = Get-ServerProcesses
    }
    $rec['status'] = 'COMPLETED'
}
catch {
    $rec['status'] = 'ABORTED'; $rec['error'] = $_.Exception.Message
    Write-Error ("S2 aborted: " + $_.Exception.Message) -ErrorAction Continue
}
finally {
    $rec['finished_utc'] = (Get-Date).ToUniversalTime().ToString('o')
    Write-Utf8File (Join-Path $RunDir 'S2_record.json') ($rec | ConvertTo-Json -Depth 6)
    Write-Host ("Stage-0 supplemental S2 (cold) " + $rec['status'] + ": " + $RunDir)
}
