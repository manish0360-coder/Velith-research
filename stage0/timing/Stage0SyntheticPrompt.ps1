# Stage-0 timing-only experiment: deterministic synthetic prompt generator.
# Research artifact (Velith-research). Contains NO SWE-bench, pilot, held-out or project content.
# Output is ASCII only, with LF newlines. The generated text is a pure function of (Nonce, NumFunctions).
# Windows PowerShell 5.1 compatible. Dot-source this file; it defines functions only and performs no I/O.

Set-StrictMode -Version 2.0

function New-Stage0SyntheticPrompt {
    param(
        [Parameter(Mandatory = $true)][string]$Nonce,
        [Parameter(Mandatory = $true)][int]$NumFunctions
    )
    if ($Nonce -notmatch '^[A-Za-z0-9_-]+$') { throw "Nonce must match ^[A-Za-z0-9_-]+$" }
    if ($NumFunctions -lt 1) { throw "NumFunctions must be >= 1" }
    $nl = "`n"
    $q3 = '"""'
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.Append('# nonce: ' + $Nonce + $nl)
    [void]$sb.Append('# Synthetic Python code for a latency measurement. It is not a real project.' + $nl + $nl)
    for ($i = 0; $i -lt $NumFunctions; $i++) {
        $s = $i.ToString([System.Globalization.CultureInfo]::InvariantCulture)
        $a = (($i % 7) + 1).ToString([System.Globalization.CultureInfo]::InvariantCulture)
        $b = (($i % 5) + 1).ToString([System.Globalization.CultureInfo]::InvariantCulture)
        [void]$sb.Append('def f_' + $s + '(x_' + $s + ', y_' + $s + '):' + $nl)
        [void]$sb.Append('    ' + $q3 + 'Synthetic function ' + $s + '.' + $q3 + $nl)
        [void]$sb.Append('    return (x_' + $s + ' * ' + $a + ') + (y_' + $s + ' // ' + $b + ')' + $nl + $nl)
    }
    [void]$sb.Append('# Task: continue writing more functions in exactly the same style.' + $nl)
    return $sb.ToString()
}

function Get-Stage0Utf8Bytes {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text)
    $enc = New-Object System.Text.UTF8Encoding($false)
    return ,($enc.GetBytes($Text))
}

function Get-Stage0Sha256Hex {
    param([Parameter(Mandatory = $true)][byte[]]$Bytes)
    $h = [System.Security.Cryptography.SHA256]::Create()
    try {
        $digest = $h.ComputeHash($Bytes)
        return (($digest | ForEach-Object { $_.ToString('x2') }) -join '')
    }
    finally { $h.Dispose() }
}

function Get-Stage0PromptByteCount {
    param([Parameter(Mandatory = $true)][string]$Nonce, [Parameter(Mandatory = $true)][int]$NumFunctions)
    $t = New-Stage0SyntheticPrompt -Nonce $Nonce -NumFunctions $NumFunctions
    return (Get-Stage0Utf8Bytes -Text $t).Length
}

# Smallest NumFunctions whose prompt is >= TargetBytes (deterministic: doubling, then binary search).
function New-Stage0SizedPrompt {
    param([Parameter(Mandatory = $true)][string]$Nonce, [Parameter(Mandatory = $true)][double]$TargetBytes)
    $n = 1
    while ((Get-Stage0PromptByteCount -Nonce $Nonce -NumFunctions $n) -lt $TargetBytes) { $n = $n * 2 }
    $lo = [int][math]::Floor($n / 2); if ($lo -lt 1) { $lo = 1 }
    $hi = $n
    while ($lo -lt $hi) {
        $mid = [int][math]::Floor(($lo + $hi) / 2)
        if ((Get-Stage0PromptByteCount -Nonce $Nonce -NumFunctions $mid) -ge $TargetBytes) { $hi = $mid } else { $lo = $mid + 1 }
    }
    $text = New-Stage0SyntheticPrompt -Nonce $Nonce -NumFunctions $lo
    $bytes = Get-Stage0Utf8Bytes -Text $text
    return [pscustomobject]@{ Nonce = $Nonce; NumFunctions = $lo; Text = $text; Bytes = $bytes.Length; Sha256 = (Get-Stage0Sha256Hex -Bytes $bytes) }
}
