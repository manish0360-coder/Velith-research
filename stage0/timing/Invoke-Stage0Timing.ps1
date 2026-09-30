# Stage-0 timing-only experiment runner (Velith-research; evidence only).
# Implements stage0/TIMING_EXPERIMENT_DESIGN_DRAFT.md (RD-approved design).
#
# Scope limits, enforced by construction:
#   * Uses only the already-running local Ollama server: /api/version, /api/tags, /api/show, /api/ps, /api/generate.
#   * No model pull/create/copy/delete. No persistent Ollama configuration change. No Docker. No Velith repository access.
#   * Prompts are synthetic (Stage0SyntheticPrompt.ps1). No SWE-bench, pilot or held-out content.
#   * Writes only under -OutRoot (default: <script dir>\runs).
#
# The advertised model context length (163840, from `ollama show`) is NOT the effective context.
# The expected effective default is 4096, from server.log 2026-09-26T11:25:41 ("vram-based default context ...
# default_num_ctx=4096"; Stage-0 evidence section 11). Run #4 measures behaviour on the no-num_ctx path.
# This run selects NO OD-3 value.
#
# R2: server-log evidence is collected by TIMESTAMP WINDOW across all %LOCALAPPDATA%\Ollama\server*.log files
# (plus -ServerLog, if given), with file snapshots and server-process identity. A missing log is recorded, never fatal.
#
# Windows PowerShell 5.1 compatible.

[CmdletBinding()]
param(
    [string]$OllamaUrl = 'http://127.0.0.1:11434',
    [string]$Model = 'deepseek-coder-v2:16b',
    [string]$ExpectedIdPrefix = '63fb193b3a9b',
    [string]$OutRoot = '',
    [string]$ServerLog = '',
    [switch]$SkipOptional32k,
    [switch]$DryRun
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

# ---------------- constants (approved design, section 3) ----------------
$TEMPERATURE = 0.0
$SEED = 0
$NUM_PREDICT = 256
$REQUEST_TIMEOUT_SEC = 1800
$ADVERTISED_CONTEXT_LENGTH = 163840
$EXPECTED_DEFAULT_NUM_CTX = 4096
$ASSUMED_BYTES_PER_TOKEN = 3.5      # used ONLY to size run #1; later runs use the ratio measured in run #1
$SIZE_SAFETY_FACTOR = 0.97          # sized prompts target 97% of the byte estimate (see deviations)
$STOP_MAX_MODEL_BYTES_16K = 16GB    # design section 4 stop rule (operator safety value)
$STOP_MIN_FREE_RAM_BYTES = 4GB      # design section 4 stop rule (operator safety value)
$SELFTEST = @(
    @{ Nonce = 'selftest'; N = 3;  Bytes = 421;  Sha256 = '373e3a2d5b3e87e4aa80938ea9deb86a3e30b63d8578fa6b7ccdc56df1d8569b' },
    @{ Nonce = 'selftest'; N = 50; Bytes = 4703; Sha256 = '702e97ea14f7d3d9f6c7257230b51b83ebaa4b1d4e3db1cf60a3e1023569b673' }
)

$ScriptDir = Split-Path -Parent $PSCommandPath
if ([string]::IsNullOrEmpty($OutRoot)) { $OutRoot = Join-Path $ScriptDir 'runs' }
$LogDir = Join-Path $env:LOCALAPPDATA 'Ollama'   # R2: candidate server logs = $LogDir\server*.log plus optional -ServerLog
$GeneratorPath = Join-Path $ScriptDir 'Stage0SyntheticPrompt.ps1'
. $GeneratorPath

$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
function Write-Utf8File([string]$Path, [string]$Text) { [System.IO.File]::WriteAllText($Path, $Text, $Utf8NoBom) }
function Add-Utf8Line([string]$Path, [string]$Text) { [System.IO.File]::AppendAllText($Path, $Text + "`n", $Utf8NoBom) }
function Get-P($Obj, [string]$Name) {
    if ($null -eq $Obj) { return $null }
    $p = $Obj.PSObject.Properties[$Name]
    if ($null -eq $p) { return $null }
    return $p.Value
}
function Get-FreeRamBytes { return [int64](Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory * 1024 }
function Get-OllamaProcesses {
    return @(Get-Process | Where-Object { $_.ProcessName -match 'ollama|llama' } | ForEach-Object {
        [ordered]@{ name = $_.ProcessName; id = $_.Id; working_set = $_.WorkingSet64; private_bytes = $_.PrivateMemorySize64 }
    })
}
function Invoke-Get([string]$Path) {
    return (Invoke-WebRequest -Uri ($OllamaUrl + $Path) -Method Get -UseBasicParsing -TimeoutSec 60).Content
}
function Invoke-PostJson([string]$Path, [byte[]]$BodyBytes, [int]$TimeoutSec) {
    return (Invoke-WebRequest -Uri ($OllamaUrl + $Path) -Method Post -Body $BodyBytes -ContentType 'application/json' -UseBasicParsing -TimeoutSec $TimeoutSec).Content
}
# /api/generate with failure capture: returns Ok/Status/Body/Error instead of throwing, so that the
# HTTP status and error body are preserved as evidence (the caller decides whether to continue or abort).
function Invoke-GenerateCapture([byte[]]$BodyBytes, [int]$TimeoutSec) {
    try {
        $r = Invoke-WebRequest -Uri ($OllamaUrl + '/api/generate') -Method Post -Body $BodyBytes -ContentType 'application/json' -UseBasicParsing -TimeoutSec $TimeoutSec
        return [pscustomobject]@{ Ok = $true; Status = [int]$r.StatusCode; Body = $r.Content; Error = $null }
    }
    catch {
        $err = $_   # capture before nested try/catch blocks can rebind $_
        $status = $null; $errBody = $null
        $resp = Get-P $err.Exception 'Response'
        if ($null -ne $resp) {
            try { $status = [int]$resp.StatusCode } catch { $status = $null }
            try {
                $reader = New-Object System.IO.StreamReader($resp.GetResponseStream())
                $errBody = $reader.ReadToEnd(); $reader.Close()
            } catch { $errBody = $null }
        }
        if ([string]::IsNullOrEmpty($errBody) -and $null -ne $err.ErrorDetails) { $errBody = $err.ErrorDetails.Message }
        return [pscustomobject]@{ Ok = $false; Status = $status; Body = $errBody; Error = $err.Exception.Message }
    }
}
function Get-PsModelEntry([string]$PsRaw) {
    $ps = $PsRaw | ConvertFrom-Json
    foreach ($m in @(Get-P $ps 'models')) { if ((Get-P $m 'name') -eq $Model -or (Get-P $m 'model') -eq $Model) { return $m } }
    return $null
}

# ---------------- R2: server-evidence helpers (read-only) ----------------
function Get-ServerLogCandidates {
    $c = @()
    if (Test-Path -LiteralPath $LogDir) { $c += @(Get-ChildItem -LiteralPath $LogDir -Filter 'server*.log' -File -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }) }
    if (-not [string]::IsNullOrEmpty($ServerLog)) { $c += $ServerLog }
    return @($c | Select-Object -Unique)
}
function Get-LogSnapshot {
    return @(Get-ServerLogCandidates | ForEach-Object {
        if (Test-Path -LiteralPath $_) {
            $fi = Get-Item -LiteralPath $_
            [ordered]@{ path = $fi.FullName; length = $fi.Length; last_write_utc = $fi.LastWriteTimeUtc.ToString('o') }
        }
    })
}
function Get-ServerProcesses {
    return @(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(ollama|ollama app|llama-server)\.exe$' } | ForEach-Object {
        $created = $null; if ($null -ne $_.CreationDate) { $created = $_.CreationDate.ToUniversalTime().ToString('o') }
        [ordered]@{ pid = $_.ProcessId; parent_pid = $_.ParentProcessId; name = $_.Name; creation_utc = $created; command_line = $_.CommandLine; executable = $_.ExecutablePath }
    })
}
# Lines whose timestamp lies in [FromUtc, ToUtc]; untimestamped lines (e.g. llama.cpp loader output) inherit the
# in-window state of the preceding timestamped line. Handles "time=<ISO8601 with offset>" and "[GIN] yyyy/MM/dd - HH:mm:ss" (local).
function Get-LogLinesInWindow([string]$Path, [datetime]$FromUtc, [datetime]$ToUtc) {
    $out = New-Object System.Collections.ArrayList
    $inWin = $false
    $inv = [System.Globalization.CultureInfo]::InvariantCulture
    foreach ($line in @(Get-Content -LiteralPath $Path -ErrorAction Stop)) {
        $ts = $null
        $m1 = [regex]::Match($line, '^time=(\S+)')
        if ($m1.Success) {
            $dto = [DateTimeOffset]::MinValue
            if ([DateTimeOffset]::TryParse($m1.Groups[1].Value, $inv, [System.Globalization.DateTimeStyles]::None, [ref]$dto)) { $ts = $dto.UtcDateTime }
        } else {
            $m2 = [regex]::Match($line, '^\[GIN\] (\d{4}/\d{2}/\d{2} - \d{2}:\d{2}:\d{2})')
            if ($m2.Success) {
                $dt = [datetime]::MinValue
                if ([datetime]::TryParseExact($m2.Groups[1].Value, 'yyyy/MM/dd - HH:mm:ss', $inv, [System.Globalization.DateTimeStyles]::AssumeLocal, [ref]$dt)) { $ts = $dt.ToUniversalTime() }
            }
        }
        if ($null -ne $ts) { $inWin = (($ts -ge $FromUtc) -and ($ts -le $ToUtc)) }
        if ($inWin) { [void]$out.Add($line) }
    }
    return ,($out.ToArray())
}

# ---------------- generator self-test (determinism) ----------------
foreach ($t in $SELFTEST) {
    $txt = New-Stage0SyntheticPrompt -Nonce $t.Nonce -NumFunctions $t.N
    $b = Get-Stage0Utf8Bytes -Text $txt
    $h = Get-Stage0Sha256Hex -Bytes $b
    if ($b.Length -ne $t.Bytes -or $h -ne $t.Sha256) {
        throw "Generator self-test failed for N=$($t.N): bytes=$($b.Length) sha256=$h (expected $($t.Bytes) / $($t.Sha256))"
    }
}

# ---------------- run directory and manifest ----------------
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$kind = 'run'; if ($DryRun) { $kind = 'dryrun' }
$RunDir = Join-Path $OutRoot ($kind + '-' + $stamp)
$RawDir = Join-Path $RunDir 'raw'
New-Item -ItemType Directory -Path $RawDir -Force | Out-Null
$RecordsPath = Join-Path $RunDir 'requests.jsonl'

$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$cs = Get-CimInstance Win32_ComputerSystem
$os = Get-CimInstance Win32_OperatingSystem
$manifest = [ordered]@{
    experiment = 'velith-stage0-timing-only'
    design = 'stage0/TIMING_EXPERIMENT_DESIGN_DRAFT.md'
    mode = $kind
    status = 'STARTED'
    started_utc = (Get-Date).ToUniversalTime().ToString('o')
    runner_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $PSCommandPath).Hash.ToLower()
    generator_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $GeneratorPath).Hash.ToLower()
    generator_selftest = 'PASSED'
    powershell_version = $PSVersionTable.PSVersion.ToString()
    host = [ordered]@{ os = $os.Caption; os_version = $os.Version; cpu = $cpu.Name; logical_processors = $cpu.NumberOfLogicalProcessors; total_physical_memory = $cs.TotalPhysicalMemory }
    ollama_url = $OllamaUrl
    model = $Model
    expected_id_prefix = $ExpectedIdPrefix
    constants = [ordered]@{ temperature = $TEMPERATURE; seed = $SEED; num_predict = $NUM_PREDICT; request_timeout_sec = $REQUEST_TIMEOUT_SEC; assumed_bytes_per_token_for_run1 = $ASSUMED_BYTES_PER_TOKEN; size_safety_factor = $SIZE_SAFETY_FACTOR; stop_max_model_bytes_16k = $STOP_MAX_MODEL_BYTES_16K; stop_min_free_ram_bytes = $STOP_MIN_FREE_RAM_BYTES }
    context_note = [ordered]@{
        advertised_context_length = $ADVERTISED_CONTEXT_LENGTH
        advertised_source = 'ollama show deepseek-coder-v2:16b (context length 163840) - model maximum, NOT effective'
        expected_default_num_ctx = $EXPECTED_DEFAULT_NUM_CTX
        expected_default_source = 'server.log 2026-09-26T11:25:41 vram-based default context default_num_ctx=4096 (Stage-0 evidence section 11); verified or refuted by run #4'
    }
    od3_values_selected = $false
    server_log_candidates = @(Get-ServerLogCandidates)
    server_log_status = 'PENDING'
    optional_32k = 'PENDING'
    optional_32k_reason = ''
    error = $null
}

$RunStartUtc = (Get-Date).ToUniversalTime()

# ---------------- plan (approved design, section 4) ----------------
$plan = @(
    @{ Id = 0;  Label = 'warmup-default';    NumCtx = $null; Kind = 'tiny';   Nonce = 'stage0-warmup-default'; TargetTokens = 0;     Optional = $false; Purpose = 'warm load; server default confirmed' },
    @{ Id = 1;  Label = 'L1k-A';             NumCtx = $null; Kind = 'sized';  Nonce = 'stage0-A';              TargetTokens = 1000;  Optional = $false; Purpose = 'Q1/Q2/Q7 baseline' },
    @{ Id = 2;  Label = 'repeat-of-1';       NumCtx = $null; Kind = 'repeat'; Nonce = 'stage0-A';              TargetTokens = 1000;  Optional = $false; Purpose = 'Q6 prompt-cache effect (same bytes as #1)' },
    @{ Id = 3;  Label = 'L3.5k-B';           NumCtx = $null; Kind = 'sized';  Nonce = 'stage0-B';              TargetTokens = 3500;  Optional = $false; Purpose = 'Q1 near the default limit' },
    @{ Id = 4;  Label = 'L8k-C-no-num_ctx';  NumCtx = $null; Kind = 'sized';  Nonce = 'stage0-C';              TargetTokens = 8000;  Optional = $false; Purpose = 'Q3 truncation probe on the frozen-client path (no num_ctx)' },
    @{ Id = 5;  Label = 'warmup-16k';        NumCtx = 16384; Kind = 'tiny';   Nonce = 'stage0-warmup-16k';     TargetTokens = 0;     Optional = $false; Purpose = 'reload at 16384: Q4/Q5' },
    @{ Id = 6;  Label = 'L8k-D';             NumCtx = 16384; Kind = 'sized';  Nonce = 'stage0-D';              TargetTokens = 8000;  Optional = $false; Purpose = 'Q1 at 8k (untruncated)' },
    @{ Id = 7;  Label = 'L16k-E';            NumCtx = 16384; Kind = 'sized';  Nonce = 'stage0-E';              TargetTokens = 16084; Optional = $false; Purpose = 'Q1 at ~16k (16384-300); Q2' },
    @{ Id = 8;  Label = 'L8k-F';             NumCtx = 16384; Kind = 'sized';  Nonce = 'stage0-F';              TargetTokens = 8000;  Optional = $false; Purpose = 'variance repeat of #6' },
    @{ Id = 9;  Label = 'warmup-32k';        NumCtx = 32768; Kind = 'tiny';   Nonce = 'stage0-warmup-32k';     TargetTokens = 0;     Optional = $true;  Purpose = 'optional reload at 32768: Q4' },
    @{ Id = 10; Label = 'L30k-G';            NumCtx = 32768; Kind = 'sized';  Nonce = 'stage0-G';              TargetTokens = 30000; Optional = $true;  Purpose = 'optional Q1 at ~30k' }
)

$bytesPerToken = $ASSUMED_BYTES_PER_TOKEN
$bytesPerTokenSource = 'assumed (run #1 sizing only)'
$prompts = @{}
$psSizeDefault = $null
$results = New-Object System.Collections.ArrayList

try {
    if (-not $DryRun) {
        $verRaw = Invoke-Get '/api/version'; Write-Utf8File (Join-Path $RawDir 'pre_version.json') $verRaw
        $tagsRaw = Invoke-Get '/api/tags'; Write-Utf8File (Join-Path $RawDir 'pre_tags.json') $tagsRaw
        $psRaw0 = Invoke-Get '/api/ps'; Write-Utf8File (Join-Path $RawDir 'pre_ps.json') $psRaw0
        $showBody = $Utf8NoBom.GetBytes((([ordered]@{ model = $Model }) | ConvertTo-Json -Compress))
        $showRaw = Invoke-PostJson '/api/show' $showBody 60; Write-Utf8File (Join-Path $RawDir 'pre_show.json') $showRaw
        $manifest['ollama_version'] = Get-P ($verRaw | ConvertFrom-Json) 'version'
        $found = $null
        foreach ($m in @(Get-P ($tagsRaw | ConvertFrom-Json) 'models')) { if ((Get-P $m 'name') -eq $Model) { $found = $m } }
        if ($null -eq $found) { throw "Model $Model is not listed by /api/tags" }
        $digest = [string](Get-P $found 'digest')
        $manifest['model_digest'] = $digest
        if (-not $digest.StartsWith($ExpectedIdPrefix)) { throw "Model digest $digest does not start with expected ID $ExpectedIdPrefix" }
        $manifest['server_processes_start'] = Get-ServerProcesses
        $manifest['server_log_snapshot_start'] = Get-LogSnapshot
        $manifest['free_ram_bytes_at_start'] = Get-FreeRamBytes
    }

    foreach ($item in $plan) {
        if ($item.Optional) {
            if ($SkipOptional32k) { $manifest['optional_32k'] = 'SKIPPED'; $manifest['optional_32k_reason'] = '-SkipOptional32k'; continue }
            if ($manifest['optional_32k'] -eq 'SKIPPED') { continue }
        }

        # ---- build prompt ----
        if ($item.Kind -eq 'tiny') {
            $text = New-Stage0SyntheticPrompt -Nonce $item.Nonce -NumFunctions 3
            $nf = 3
        } elseif ($item.Kind -eq 'repeat') {
            $text = $prompts[1].Text; $nf = $prompts[1].NumFunctions
        } else {
            $targetBytes = $item.TargetTokens * $bytesPerToken * $SIZE_SAFETY_FACTOR
            $sp = New-Stage0SizedPrompt -Nonce $item.Nonce -TargetBytes $targetBytes
            $text = $sp.Text; $nf = $sp.NumFunctions
        }
        $promptBytes = Get-Stage0Utf8Bytes -Text $text
        $promptSha = Get-Stage0Sha256Hex -Bytes $promptBytes
        $prompts[$item.Id] = @{ Text = $text; NumFunctions = $nf }
        $nn = '{0:D2}' -f $item.Id
        Write-Utf8File (Join-Path $RawDir ($nn + '_prompt.txt')) $text

        $opts = [ordered]@{ temperature = $TEMPERATURE; seed = $SEED; num_predict = $NUM_PREDICT }
        if ($null -ne $item.NumCtx) { $opts['num_ctx'] = [int]$item.NumCtx }
        $body = [ordered]@{ model = $Model; prompt = $text; stream = $false; options = $opts }
        $bodyJson = $body | ConvertTo-Json -Depth 5 -Compress
        $bodyBytes = $Utf8NoBom.GetBytes($bodyJson)
        $requestSha = Get-Stage0Sha256Hex -Bytes $bodyBytes
        Write-Utf8File (Join-Path $RawDir ($nn + '_request.json')) $bodyJson

        $rec = [ordered]@{
            id = $item.Id; label = $item.Label; purpose = $item.Purpose; optional = $item.Optional
            num_ctx_sent = $item.NumCtx; kind = $item.Kind; nonce = $item.Nonce; num_functions = $nf
            target_tokens = $item.TargetTokens; bytes_per_token_used = $bytesPerToken; bytes_per_token_source = $bytesPerTokenSource
            prompt_bytes = $promptBytes.Length; prompt_sha256 = $promptSha; request_sha256 = $requestSha
        }

        if ($DryRun) {
            $rec['executed'] = $false
            Add-Utf8Line $RecordsPath ($rec | ConvertTo-Json -Depth 6 -Compress)
            [void]$results.Add([pscustomobject]$rec)
            continue
        }

        # ---- execute ----
        $rec['executed'] = $true
        $rec['free_ram_bytes_before'] = Get-FreeRamBytes
        $rec['started_utc'] = (Get-Date).ToUniversalTime().ToString('o')
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $gen = Invoke-GenerateCapture $bodyBytes $REQUEST_TIMEOUT_SEC
        $sw.Stop()
        $rec['wall_time_ms'] = $sw.ElapsedMilliseconds
        $rec['http_status'] = $gen.Status
        if (-not $gen.Ok) {
            # Preserve status and error body for ANY /api/generate failure.
            $rec['error_message'] = $gen.Error
            $rec['error_body'] = $gen.Body
            Write-Utf8File (Join-Path $RawDir ($nn + '_error.json')) (([ordered]@{ http_status = $gen.Status; error_message = $gen.Error; error_body = $gen.Body }) | ConvertTo-Json -Depth 4)
            if ($item.Id -eq 4) {
                # Run #4 is the Q3 truncation probe: a failure is an observed Q3 outcome, not an abort.
                $rec['q3_outcome'] = 'GENERATE_FAILED_OBSERVED'
                $rec['free_ram_bytes_after'] = Get-FreeRamBytes
                Add-Utf8Line $RecordsPath ($rec | ConvertTo-Json -Depth 6 -Compress)
                [void]$results.Add([pscustomobject]$rec)
                continue
            }
            Add-Utf8Line $RecordsPath ($rec | ConvertTo-Json -Depth 6 -Compress)
            [void]$results.Add([pscustomobject]$rec)
            throw ("/api/generate failed on run #" + $item.Id + " (HTTP " + $gen.Status + "): " + $gen.Error)
        }
        if ($item.Id -eq 4) { $rec['q3_outcome'] = 'HTTP_OK_SEE_PROMPT_EVAL_COUNT' }
        $respRaw = $gen.Body
        Write-Utf8File (Join-Path $RawDir ($nn + '_response.json')) $respRaw
        $j = $respRaw | ConvertFrom-Json
        foreach ($f in @('model', 'created_at', 'done', 'done_reason', 'total_duration', 'load_duration', 'prompt_eval_count', 'prompt_eval_duration', 'eval_count', 'eval_duration')) { $rec[$f] = Get-P $j $f }
        $respText = [string](Get-P $j 'response')
        $rec['response_bytes'] = $Utf8NoBom.GetByteCount($respText)
        $pec = Get-P $j 'prompt_eval_count'; $ped = Get-P $j 'prompt_eval_duration'
        $ec = Get-P $j 'eval_count'; $ed = Get-P $j 'eval_duration'
        if ($pec -and $ped) { $rec['prompt_tokens_per_s'] = [double]$pec / ([double]$ped / 1e9) } else { $rec['prompt_tokens_per_s'] = $null }
        if ($ec -and $ed) { $rec['gen_tokens_per_s'] = [double]$ec / ([double]$ed / 1e9) } else { $rec['gen_tokens_per_s'] = $null }
        if ($pec -and $item.Kind -eq 'sized') {
            $rec['bytes_per_token_observed'] = [double]$promptBytes.Length / [double]$pec
            $rec['expected_prompt_tokens_estimate'] = [double]$promptBytes.Length / $bytesPerToken
        }

        $psRaw = Invoke-Get '/api/ps'
        Write-Utf8File (Join-Path $RawDir ($nn + '_ps.json')) $psRaw
        $pm = Get-PsModelEntry $psRaw
        $rec['ps_size'] = Get-P $pm 'size'; $rec['ps_size_vram'] = Get-P $pm 'size_vram'; $rec['ps_context_length'] = Get-P $pm 'context_length'
        $rec['ollama_processes'] = Get-OllamaProcesses
        $rec['free_ram_bytes_after'] = Get-FreeRamBytes

        Add-Utf8Line $RecordsPath ($rec | ConvertTo-Json -Depth 6 -Compress)
        [void]$results.Add([pscustomobject]$rec)

        # ---- measured bytes/token for later sizing (from uncached run #1) ----
        if ($item.Id -eq 1 -and $pec) {
            $bytesPerToken = [double]$promptBytes.Length / [double]$pec
            $bytesPerTokenSource = 'measured in run #1 (prompt_bytes / prompt_eval_count, uncached)'
            $manifest['bytes_per_token_measured_run1'] = $bytesPerToken
        }
        if ($item.Id -eq 0) { $psSizeDefault = $rec['ps_size'] }

        # ---- stop rule for the optional 32k block (design section 4) ----
        if ($item.Id -eq 5) {
            $size16 = $rec['ps_size']
            $free = $rec['free_ram_bytes_after']
            if ($null -eq $size16) {
                $manifest['optional_32k'] = 'SKIPPED'; $manifest['optional_32k_reason'] = '/api/ps reported no size after run #5'
            } elseif ([int64]$size16 -gt $STOP_MAX_MODEL_BYTES_16K) {
                $manifest['optional_32k'] = 'SKIPPED'; $manifest['optional_32k_reason'] = "model size at 16384 ($size16 B) exceeds 16 GB"
            } else {
                $delta = 0
                if ($null -ne $psSizeDefault) { $delta = [int64]$size16 - [int64]$psSizeDefault; if ($delta -lt 0) { $delta = 0 } }
                if (([int64]$free - [int64]$delta) -lt $STOP_MIN_FREE_RAM_BYTES) {
                    $manifest['optional_32k'] = 'SKIPPED'; $manifest['optional_32k_reason'] = "projected free RAM at 32768 ($free - $delta B) below 4 GB"
                } else {
                    $manifest['optional_32k'] = 'ALLOWED'; $manifest['optional_32k_reason'] = "size16=$size16 B; free=$free B; projected increase=$delta B"
                }
            }
        }
    }
    $manifest['status'] = 'COMPLETED'
}
catch {
    $manifest['status'] = 'ABORTED'
    $manifest['error'] = $_.Exception.Message
    Write-Error ("Stage-0 timing aborted: " + $_.Exception.Message) -ErrorAction Continue
}
finally {
    $manifest['finished_utc'] = (Get-Date).ToUniversalTime().ToString('o')
    if (-not $DryRun) {
        try {
            $manifest['server_processes_end'] = Get-ServerProcesses
            $manifest['server_log_snapshot_end'] = Get-LogSnapshot
            $fromUtc = $RunStartUtc.AddSeconds(-5)
            $toUtc = (Get-Date).ToUniversalTime().AddSeconds(5)
            $manifest['server_log_window_utc'] = [ordered]@{ from = $fromUtc.ToString('o'); to = $toUtc.ToString('o') }
            $seg = New-Object System.Collections.ArrayList
            $perFile = @()
            foreach ($lp in @(Get-ServerLogCandidates)) {
                if (-not (Test-Path -LiteralPath $lp)) { continue }
                $w = @(Get-LogLinesInWindow $lp $fromUtc $toUtc)
                $perFile += [ordered]@{ path = $lp; lines_in_window = $w.Count }
                foreach ($l in $w) { [void]$seg.Add([System.IO.Path]::GetFileName($lp) + ' | ' + $l) }
            }
            $manifest['server_log_files'] = $perFile
            Write-Utf8File (Join-Path $RunDir 'server_log_segment.txt') ((@($seg) -join "`n") + "`n")
            $rel = @($seg | Where-Object { $_ -match 'truncat|num_ctx|context|kv|KV|llama_|offload|memory|load|runner|model|error|exceed' })
            Write-Utf8File (Join-Path $RunDir 'server_log_relevant.txt') (($rel -join "`n") + "`n")
            $manifest['server_log_segment_lines'] = $seg.Count
            if ($seg.Count -gt 0) { $manifest['server_log_status'] = 'CAPTURED' }
            else { $manifest['server_log_status'] = 'NO_LINES_IN_WINDOW (the active server may log to its console or to another file; see server_processes_*)' }
        } catch { $manifest['server_log_status'] = 'ERROR'; $manifest['server_log_error'] = $_.Exception.Message }
    }
    Write-Utf8File (Join-Path $RunDir 'manifest.json') ($manifest | ConvertTo-Json -Depth 8)
    if ($results.Count -gt 0) {
        $results | Select-Object id, label, num_ctx_sent, prompt_bytes, prompt_sha256, request_sha256, executed, http_status, q3_outcome, wall_time_ms, total_duration, load_duration, prompt_eval_count, prompt_eval_duration, eval_count, eval_duration, done_reason, prompt_tokens_per_s, gen_tokens_per_s, ps_size, ps_context_length, free_ram_bytes_after |
            Export-Csv -NoTypeInformation -Encoding UTF8 -LiteralPath (Join-Path $RunDir 'summary.csv')
    }
    Write-Host ("Stage-0 timing " + $manifest['status'] + ": " + $RunDir)
}
