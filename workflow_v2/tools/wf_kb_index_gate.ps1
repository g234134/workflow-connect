# wf_kb_index_gate.ps1 — KB/index precheck gate for IMP-AI-READY (W4-B)
#
# Usage (from repo root):
#   powershell -NoProfile -File workflow_v2/tools/wf_kb_index_gate.ps1 -CaseDir workflow_v2/20_pilot/W2-1_case -TargetImpState IMP-AI-READY
#
# Exit: 0 = allow; 1 = require-human-override; 2 = deny; 3 = config/usage error
#
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$CaseDir,

    [ValidateSet("IMP-AI-READY")]
    [string]$TargetImpState = "IMP-AI-READY",

    [string]$RepoRoot = "",
    [switch]$AllowStaleWithAck
)

$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
    param([string]$Hint)
    if ($Hint -and (Test-Path (Join-Path $Hint "workflow_v2"))) {
        return (Resolve-Path $Hint).Path
    }
    $here = $PSScriptRoot
    if ($here) {
        $candidate = Split-Path (Split-Path $here -Parent) -Parent
        if (Test-Path (Join-Path $candidate "workflow_v2")) { return $candidate }
    }
    return (Get-Location).Path
}

function Resolve-UnderRoot {
    param([string]$Root, [string]$RelPath)
    $p = Join-Path $Root ($RelPath -replace '/', [IO.Path]::DirectorySeparatorChar)
    if (-not (Test-Path $p)) { return $null }
    return (Resolve-Path $p).Path
}

function Find-CaseMarkdown {
    param([string]$CaseDirAbs)
    $files = @(Get-ChildItem -Path $CaseDirAbs -File -Filter "*_case.md" -ErrorAction SilentlyContinue)
    if ($files.Count -eq 1) { return $files[0].FullName }
    if ($files.Count -gt 1) {
        foreach ($f in $files) {
            if ($f.Name -match '^W\d+-\d+_case\.md$') { return $f.FullName }
        }
        return $files[0].FullName
    }
    return $null
}

function Read-CaseText {
    param([string]$CaseMdPath)
    if (-not (Test-Path $CaseMdPath)) { return $null }
    return (Get-Content -Path $CaseMdPath -Raw -Encoding UTF8)
}

function Get-KbIndexField {
    param(
        [string]$CaseText,
        [string]$FieldName
    )

    $pattern = '\|\s*\*\*`' + [Regex]::Escape($FieldName) + '`\*\*\s*\|\s*`([^`]*)`\s*\|'
    $m = [regex]::Match($CaseText, $pattern)
    if ($m.Success) { return $m.Groups[1].Value.Trim() }

    $pattern2 = '\|\s*\*\*`' + [Regex]::Escape($FieldName) + '`[^|]*\*\*\s*\|\s*`([^`]*)`\s*\|'
    $m2 = [regex]::Match($CaseText, $pattern2)
    if ($m2.Success) { return $m2.Groups[1].Value.Trim() }

    return ""
}

function To-Bool {
    param([string]$Val)
    if (-not $Val) { return $false }
    $s = $Val.Trim().ToLowerInvariant()
    return ($s -eq "true" -or $s -eq "1" -or $s -eq "yes")
}

function Merge-Verdict {
    param([string]$Current, [string]$Incoming)
    $rank = @{ allow = 0; "require-human-override" = 1; deny = 2 }
    if ($rank[$Incoming] -gt $rank[$Current]) { return $Incoming }
    return $Current
}

function New-Result {
    param([string]$Gate)
    return @{
        gate = $Gate
        target_imp_state = $TargetImpState
        verdict = "allow"
        checks_failed = @()
        summary = ""
        kb_index = @{
            kb_index_status = $null
            kb_index_source = $null
            kb_index_job_id = $null
            kb_index_last_updated = $null
            kb_index_blocker = $null
            kb_index_stale_ack = $null
            kb_index_stale_reason = $null
            kb_index_reindex_ticket = $null
        }
    }
}

function Write-GateOutput {
    param($Result)
    Write-Host ""
    Write-Host "wf_kb_index_gate — $($Result.gate)"
    Write-Host "target_imp_state: $($Result.target_imp_state)"
    Write-Host "verdict: $($Result.verdict)"
    Write-Host ""
    Write-Host "checks_failed:"
    if ($Result.checks_failed.Count -eq 0) {
        Write-Host "  (none)"
    }
    else {
        foreach ($c in $Result.checks_failed) { Write-Host "  - $c" }
    }
    Write-Host ""
    Write-Host "summary: $($Result.summary)"
    Write-Host ""

    $failedCsv = if ($Result.checks_failed.Count -gt 0) {
        ($Result.checks_failed -join ",")
    }
    else {
        "none"
    }
    Write-Host "VERDICT=$($Result.verdict)"
    Write-Host "CHECKS_FAILED=$failedCsv"
}

function Invoke-AiReadyGate {
    param([string]$CaseText)

    $r = New-Result -Gate "GATE-AI-READY-INDEX"
    $failed = [System.Collections.Generic.List[string]]::new()
    $notes = [System.Collections.Generic.List[string]]::new()

    $status = Get-KbIndexField -CaseText $CaseText -FieldName "kb_index_status"
    $source = Get-KbIndexField -CaseText $CaseText -FieldName "kb_index_source"
    $jobId = Get-KbIndexField -CaseText $CaseText -FieldName "kb_index_job_id"
    $lastUpdated = Get-KbIndexField -CaseText $CaseText -FieldName "kb_index_last_updated"
    $blocker = Get-KbIndexField -CaseText $CaseText -FieldName "kb_index_blocker"
    $staleAck = Get-KbIndexField -CaseText $CaseText -FieldName "kb_index_stale_ack"
    $staleReason = Get-KbIndexField -CaseText $CaseText -FieldName "kb_index_stale_reason"
    $reindexTicket = Get-KbIndexField -CaseText $CaseText -FieldName "kb_index_reindex_ticket"

    $r.kb_index.kb_index_status = $status
    $r.kb_index.kb_index_source = $source
    $r.kb_index.kb_index_job_id = $jobId
    $r.kb_index.kb_index_last_updated = $lastUpdated
    $r.kb_index.kb_index_blocker = $blocker
    $r.kb_index.kb_index_stale_ack = $staleAck
    $r.kb_index.kb_index_stale_reason = $staleReason
    $r.kb_index.kb_index_reindex_ticket = $reindexTicket

    if (-not $status) {
        $failed.Add("kb_index_status_missing")
        $r.verdict = "deny"
        $notes.Add("kb_index_status not found in case")
        $r.checks_failed = @($failed)
        $r.summary = ($notes -join "; ")
        return $r
    }

    $statusNorm = $status.Trim().ToLowerInvariant()
    switch ($statusNorm) {
        "ready" {
            $notes.Add("kb_index_status=ready")
        }
        "missing" {
            $failed.Add("kb_index_missing")
            $r.verdict = "deny"
            if ($blocker -and ($blocker.Trim() -notmatch '^[\-\u2014]+$')) {
                $failed.Add("kb_index_blocker_present")
                $notes.Add("blocker=$blocker")
            }
            else {
                $notes.Add("missing: no successful index covering scope")
            }
        }
        "stale" {
            $failed.Add("kb_index_stale")
            $ack = To-Bool -Val $staleAck
            $hasReason = ($staleReason -and $staleReason.Trim() -and ($staleReason.Trim() -notmatch '^[\-\u2014]+$'))
            $hasTicket = ($reindexTicket -and $reindexTicket.Trim() -and ($reindexTicket.Trim() -notmatch '^[\-\u2014]+$'))
            if (-not $ack) { $failed.Add("kb_index_stale_ack_false") }
            if (-not $hasReason) { $failed.Add("kb_index_stale_reason_missing") }
            if (-not $hasTicket) { $failed.Add("kb_index_reindex_ticket_missing") }

            if ($ack -and $hasReason -and $hasTicket) {
                if ($AllowStaleWithAck) {
                    $r.verdict = Merge-Verdict -Current $r.verdict -Incoming "require-human-override"
                    $notes.Add("stale_ack accepted (AllowStaleWithAck): proceed with human-override awareness")
                }
                else {
                    $r.verdict = "deny"
                    $notes.Add("stale requires explicit -AllowStaleWithAck to proceed")
                    $failed.Add("kb_index_stale_requires_allow_flag")
                }
            }
            else {
                $r.verdict = "deny"
                $notes.Add("stale without complete ack fields blocks AI-READY")
            }
        }
        default {
            $failed.Add("kb_index_status_unrecognized")
            $r.verdict = "deny"
            $notes.Add("kb_index_status=$status (expected ready|stale|missing)")
        }
    }

    if (-not $source) {
        $failed.Add("kb_index_source_missing")
        if ($r.verdict -eq "allow") { $r.verdict = "require-human-override" }
    }

    $r.checks_failed = @($failed | Select-Object -Unique)
    $r.summary = ($notes -join "; ")
    return $r
}

# --- main ---
$root = Resolve-RepoRoot -Hint $RepoRoot
$caseAbs = Resolve-UnderRoot -Root $root -RelPath $CaseDir
if (-not $caseAbs) {
    Write-Error "CaseDir not found under repo: $CaseDir"
    exit 3
}

$caseMd = Find-CaseMarkdown -CaseDirAbs $caseAbs
if (-not $caseMd) {
    Write-Error "No *_case.md found under CaseDir: $CaseDir"
    exit 3
}

$text = Read-CaseText -CaseMdPath $caseMd
if (-not $text) {
    Write-Error "Failed to read case markdown: $caseMd"
    exit 3
}

$result = Invoke-AiReadyGate -CaseText $text
Write-GateOutput -Result $result

switch ($result.verdict) {
    "allow" { exit 0 }
    "require-human-override" { exit 1 }
    "deny" { exit 2 }
    default { exit 3 }
}

