# wf_emit_gov_gate_metrics.ps1 — CI/manual JSONL emitter for gov-metrics-0.1 (W4-C)
#
# Contract:
# - Always writes gov-metrics-0.1 JSONL lines (NDJSON).
# - Never fails CI by non-zero exit from helper/gate scripts (swallow exit codes).
# - Parses stdout from:
#   - workflow_v2/tools/wf_check_cross_ref.ps1
#   - workflow_v2/tools/wf_gov_gate.ps1
#
# Out-of-scope:
# - deny runtime / enforcement / fail-on-deny escalation (Wave 5+)

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("pr", "nightly", "manual", "agent")]
    [string]$Pipeline,

    [Parameter(Mandatory = $true)]
    [string]$JsonlPath,

    [string]$RunId = "",

    [switch]$DoCrossRef,
    [switch]$DoGateRiskExit,
    [switch]$DoGateRelEntry
)

$ErrorActionPreference = "Stop"

function Ensure-ParentDir {
    param([string]$Path)
    $dir = Split-Path -Path $Path -Parent
    if (-not $dir) { return }
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

function Write-JsonlLine {
    param([hashtable]$Record)
    Ensure-ParentDir -Path $JsonlPath
    $json = ($Record | ConvertTo-Json -Compress)
    Add-Content -Encoding UTF8 -Path $JsonlPath -Value $json
}

function New-Envelope {
    param(
        [string]$Helper,
        [string]$Gate
    )
    $ts = [DateTime]::UtcNow.ToString("o")
    $rec = @{
        schema_version = "gov-metrics-0.1"
        ts = $ts
        pipeline = $Pipeline
        helper = $Helper
        gate = $Gate
        exit_code = 0
        checks_failed = @()
    }
    if ($RunId) { $rec["run_id"] = $RunId }
    return $rec
}

function Invoke-CrossRef {
    $scope = "G8Recon"
    $caseId = "W2-1"

    $out = @()
    $exitCode = 2
    try {
        $out = & powershell -NoProfile -ExecutionPolicy Bypass -File workflow_v2/tools/wf_check_cross_ref.ps1 -Scope $scope -CaseId $caseId 2>&1
        $exitCode = $LASTEXITCODE
    }
    catch {
        $out = @("EXCEPTION: $($_.Exception.Message)")
        $exitCode = 2
    }

    $verdict = if ($exitCode -eq 0) { "allow" } else { "deny" }
    $failIds = [System.Collections.Generic.List[string]]::new()
    foreach ($line in @($out)) {
        if ($null -eq $line) { continue }
        $s = [string]$line
        if ($s -match '^\[FAIL\]\s+(AC-[A-Za-z0-9-]+)\s') {
            $failIds.Add($Matches[1])
        }
    }

    $summary = ""
    foreach ($line in @($out)) {
        if ($null -eq $line) { continue }
        $s = [string]$line
        if ($s -match '^Summary:') { $summary = $s; break }
    }

    $rec = New-Envelope -Helper "wf_check_cross_ref" -Gate "GATE-CROSS-REF-G8RECON"
    $rec["scope"] = $scope
    $rec["case_id"] = $caseId
    $rec["verdict"] = $verdict
    $rec["checks_failed"] = @($failIds | Select-Object -Unique)
    $rec["exit_code"] = [int]$exitCode
    if ($summary) { $rec["message"] = $summary }

    Write-JsonlLine -Record $rec

    # Always swallow exit code (PR/nightly must not fail).
    return @{ ok = $true; exit_code = $exitCode; verdict = $verdict }
}

function Parse-StdoutKV {
    param(
        [string[]]$Lines,
        [string]$Key
    )
    foreach ($line in @($Lines)) {
        if ($null -eq $line) { continue }
        $s = [string]$line
        if ($s -match ("^" + [Regex]::Escape($Key) + "=(.*)$")) {
            return $Matches[1].Trim()
        }
    }
    return ""
}

function Parse-StdoutField {
    param(
        [string[]]$Lines,
        [string]$Prefix
    )
    foreach ($line in @($Lines)) {
        if ($null -eq $line) { continue }
        $s = [string]$line
        if ($s -match ("^" + [Regex]::Escape($Prefix) + "\s*(.*)$")) {
            return $Matches[1].Trim()
        }
    }
    return ""
}

function CsvToArray {
    param([string]$Csv)
    if (-not $Csv -or $Csv -eq "none") { return @() }
    return @($Csv.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ })
}

function Invoke-GovGate {
    param(
        [string]$Gate,
        [string]$CaseId,
        [string]$CaseDir,
        [string]$ImpState,
        [string]$GovRiskPath
    )

    $args = @(
        "-Gate", $Gate,
        "-CaseDir", $CaseDir
    )
    if ($ImpState) { $args += @("-ImpState", $ImpState) }
    if ($GovRiskPath) { $args += @("-GovRiskPath", $GovRiskPath) }

    $out = @()
    $exitCode = 3
    try {
        $out = & powershell -NoProfile -ExecutionPolicy Bypass -File workflow_v2/tools/wf_gov_gate.ps1 @args 2>&1
        $exitCode = $LASTEXITCODE
    }
    catch {
        $out = @("EXCEPTION: $($_.Exception.Message)")
        $exitCode = 3
    }

    $verdict = Parse-StdoutKV -Lines $out -Key "VERDICT"
    if (-not $verdict) {
        # Keep schema enums; on parse failure, treat as deny with an explicit check failure.
        $verdict = "deny"
    }

    $checksCsv = Parse-StdoutKV -Lines $out -Key "CHECKS_FAILED"
    $checksFailed = CsvToArray -Csv $checksCsv
    if (-not $checksCsv) { $checksFailed = @("checks_failed_unparsed") }

    $impStateOut = Parse-StdoutField -Lines $out -Prefix "imp_state:"
    $govArtifactOut = Parse-StdoutField -Lines $out -Prefix "gov_artifact:"
    $qaVerdictOut = Parse-StdoutField -Lines $out -Prefix "qa_verdict:"

    $rec = New-Envelope -Helper "wf_gov_gate" -Gate $Gate
    $rec["case_id"] = $CaseId
    $rec["case_dir"] = $CaseDir
    $rec["verdict"] = $verdict
    $rec["checks_failed"] = @($checksFailed | Select-Object -Unique)
    $rec["exit_code"] = [int]$exitCode

    if ($ImpState) { $rec["imp_state"] = $ImpState }
    elseif ($impStateOut) { $rec["imp_state"] = $impStateOut }

    if ($govArtifactOut) { $rec["gov_artifact"] = $govArtifactOut }
    if ($qaVerdictOut) { $rec["qa_verdict"] = $qaVerdictOut }

    Write-JsonlLine -Record $rec

    return @{ ok = $true; exit_code = $exitCode; verdict = $verdict }
}

# --- main ---

$didAny = $false
if ($DoCrossRef) {
    $didAny = $true
    Invoke-CrossRef | Out-Null
}
if ($DoGateRiskExit) {
    $didAny = $true
    $null = Invoke-GovGate `
        -Gate "GATE-RISK-EXIT" `
        -CaseId "W2-3" `
        -CaseDir "workflow_v2/20_pilot/W2-3_case" `
        -ImpState "IMP-RISK-VALIDATION" `
        -GovRiskPath ""
}
if ($DoGateRelEntry) {
    $didAny = $true
    $null = Invoke-GovGate `
        -Gate "GATE-REL-ENTRY" `
        -CaseId "W2-1" `
        -CaseDir "workflow_v2/20_pilot/W2-1_case" `
        -ImpState "" `
        -GovRiskPath "workflow_v2/20_pilot/W2-3_case/art_gov_risk.json"
}

if (-not $didAny) {
    $rec = New-Envelope -Helper "wf_emit_gov_gate_metrics" -Gate "GATE-NOOP"
    $rec["verdict"] = "allow"
    $rec["checks_failed"] = @()
    $rec["exit_code"] = 0
    $rec["message"] = "noop: no switches enabled"
    Write-JsonlLine -Record $rec
}

# Hard swallow: this wrapper must not fail PR/nightly (W4-C requirement).
exit 0

