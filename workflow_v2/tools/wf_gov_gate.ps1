# wf_gov_gate.ps1 — read-only governance gate prototype (v0.1)
#
# Usage (from repo root):
#   powershell -NoProfile -File workflow_v2/tools/wf_gov_gate.ps1 -Gate GATE-RISK-EXIT -CaseDir workflow_v2/20_pilot/W2-3_case
#   powershell -NoProfile -File workflow_v2/tools/wf_gov_gate.ps1 -Gate GATE-REL-ENTRY -CaseDir workflow_v2/20_pilot/W2-1_case -GovRiskPath workflow_v2/20_pilot/W2-3_case/art_gov_risk.json
#
# Exit: 0 = allow; 1 = require-human-override; 2 = deny; 3 = config/usage error

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("GATE-RISK-EXIT", "GATE-REL-ENTRY")]
    [string]$Gate,

    [Parameter(Mandatory = $true)]
    [string]$CaseDir,

    [string]$RepoRoot = "",
    [string]$GovRiskPath = "",
    [switch]$AllowFallback,
    [string]$ImpState = ""
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

function Read-JsonObject {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    $raw = Get-Content -Path $Path -Raw -Encoding UTF8
    return ($raw | ConvertFrom-Json)
}

function Get-CaseImpState {
    param(
        [string]$CaseDirAbs,
        [string]$ExplicitImpState
    )
    if ($ExplicitImpState) {
        return @{ value = $ExplicitImpState.Trim(); source = "parameter" }
    }

    $mdCandidates = @(
        (Join-Path $CaseDirAbs "W2-1_case.md"),
        (Join-Path $CaseDirAbs "W2-3_case.md")
    )
  foreach ($md in $mdCandidates) {
        if (-not (Test-Path $md)) { continue }
        $text = Get-Content -Path $md -Raw -Encoding UTF8
        if ($text -match '\*\*`imp_state`[^|]*\|\s*\*\*`(IMP-[A-Z-]+)`') {
            return @{ value = $Matches[1]; source = "case_md" }
        }
        if ($text -match 'imp_state`[^|]*\|\s*\*\*`(IMP-[A-Z-]+)`') {
            return @{ value = $Matches[1]; source = "case_md" }
        }
        if ($text -match '\|\s*\*\*`imp_state`[^|]*\|\s*\*\*`(IMP-[A-Z-]+)`') {
            return @{ value = $Matches[1]; source = "case_md" }
        }
    }
    return @{ value = $null; source = "unreadable" }
}

function Test-OpenHighCriticalRisks {
    param($GovRisk)
    if (-not $GovRisk -or -not $GovRisk.risk_items) { return $false }
    foreach ($item in @($GovRisk.risk_items)) {
        if ($item.disposition -eq "open" -and $item.severity -in @("high", "critical")) {
            return $true
        }
    }
    return $false
}

function Get-GovRiskBaselineChecks {
    param(
        $GovRisk,
        [bool]$GovExists,
        [bool]$AllowFallback,
        [string]$GateLabel
    )
    $failed = [System.Collections.Generic.List[string]]::new()
    $notes = [System.Collections.Generic.List[string]]::new()
    $verdict = "allow"

    if (-not $GovExists) {
        $failed.Add("missing_gov")
        if ($AllowFallback) {
            $verdict = "require-human-override"
            $notes.Add("ART-GOV-RISK missing; -AllowFallback => require-human-override per fallback chain")
        }
        else {
            $verdict = "deny"
            $notes.Add("ART-GOV-RISK missing; default deny")
        }
        return @{ verdict = $verdict; checks_failed = $failed; notes = $notes }
    }

    if ($GovRisk.schema_version -and $GovRisk.schema_version -ne "0.1") {
        $failed.Add("schema_version_unrecognized")
        $notes.Add("schema_version=$($GovRisk.schema_version) (v0.1 gate expects 0.1)")
    }

    if ($GovRisk.status -ne "signed") {
        $failed.Add("status_not_signed")
        $verdict = "deny"
        $notes.Add("status=$($GovRisk.status); require signed")
    }

    if ($GovRisk.status -eq "stale") {
        $failed.Add("gov_stale")
        if ($GateLabel -eq "GATE-REL-ENTRY" -and $verdict -eq "allow") {
            $verdict = "require-human-override"
        }
        elseif ($verdict -eq "allow") {
            $verdict = "deny"
        }
        $notes.Add("ART-GOV-RISK status is stale")
    }

    $allRequired = $false
    if ($GovRisk.nbt_validation) {
        $allRequired = [bool]$GovRisk.nbt_validation.all_required
    }
    if (-not $allRequired) {
        $failed.Add("nbt_all_required_false")
        $verdict = "deny"
        $notes.Add("nbt_validation.all_required is not true")
    }

    $mustStop = $false
    $overrideEffective = $false
    if ($null -ne $GovRisk.must_stop_work) { $mustStop = [bool]$GovRisk.must_stop_work }
    if ($null -ne $GovRisk.override_effective) { $overrideEffective = [bool]$GovRisk.override_effective }

    if ($mustStop -and -not $overrideEffective) {
        $failed.Add("stop_work_no_override")
        $verdict = "deny"
        $notes.Add("must_stop_work=true and override_effective=false")
    }
    elseif ($mustStop -and $overrideEffective -and $verdict -eq "allow") {
        $failed.Add("stop_work_with_override")
        $verdict = "require-human-override"
        $notes.Add("must_stop_work=true but override_effective=true => human override path")
    }

    if (Test-OpenHighCriticalRisks -GovRisk $GovRisk) {
        $failed.Add("open_high_critical_risk")
        $verdict = "deny"
        $notes.Add("risk_items contain open high/critical")
    }

    $fallbackUsed = $false
    if ($GovRisk.nbt_validation -and $null -ne $GovRisk.nbt_validation.fallback_used) {
        $fallbackUsed = [bool]$GovRisk.nbt_validation.fallback_used
    }
    if ($fallbackUsed) {
        $failed.Add("fallback_used")
        if ($AllowFallback) {
            if ($verdict -eq "allow") {
                $notes.Add("fallback_used=true; -AllowFallback permits proceed with human-override awareness")
            }
        }
        else {
            if ($verdict -eq "allow") { $verdict = "require-human-override" }
            $notes.Add("fallback_used=true; default require-human-override (pass -AllowFallback to acknowledge)")
        }
    }

    return @{ verdict = $verdict; checks_failed = $failed; notes = $notes }
}

function Invoke-GateRiskExit {
    param(
        [string]$CaseDirAbs,
        [bool]$AllowFallback
    )
    $govPath = Join-Path $CaseDirAbs "art_gov_risk.json"
    $gov = Read-JsonObject -Path $govPath
    $govExists = ($null -ne $gov)

    $base = Get-GovRiskBaselineChecks -GovRisk $gov -GovExists $govExists -AllowFallback:$AllowFallback -GateLabel "GATE-RISK-EXIT"

    $imp = Get-CaseImpState -CaseDirAbs $CaseDirAbs -ExplicitImpState $ImpState
    if ($imp.source -eq "unreadable") {
        $base.checks_failed.Add("imp_state_unreadable")
        $base.notes.Add("imp_state not provided and case markdown not parsed (v0.1: use -ImpState)")
    }
    elseif ($imp.value -and $imp.value -ne "IMP-RISK-VALIDATION") {
        $base.checks_failed.Add("imp_state_not_risk_validation")
        $base.notes.Add("imp_state=$($imp.value) (R1 expects IMP-RISK-VALIDATION at exit; v0.1 warning only)")
    }

    return @{
        gate = "GATE-RISK-EXIT"
        verdict = $base.verdict
        checks_failed = @($base.checks_failed)
        summary = ($base.notes -join "; ")
        imp_state = $imp.value
        gov_artifact = if ($govExists) { $gov.artifact_instance_id } else { $null }
    }
}

function Test-ToolingChecks {
    param($QaRev)
    $failed = [System.Collections.Generic.List[string]]::new()
    $notes = [System.Collections.Generic.List[string]]::new()
    $verdict = "allow"

    if (-not $QaRev) {
        $failed.Add("qa_artifact_missing")
        return @{ verdict = "deny"; checks_failed = $failed; notes = $notes }
    }

    if (-not $QaRev.verdict) {
        $failed.Add("qa_verdict_missing")
        return @{ verdict = "deny"; checks_failed = $failed; notes = $notes }
    }

    if ($QaRev.verdict -eq "rejected") {
        $failed.Add("qa_verdict_rejected")
        return @{ verdict = "deny"; checks_failed = $failed; notes = @("QA verdict is rejected") }
    }

    if ($QaRev.verdict -notin @("accepted", "accepted_with_gaps")) {
        $failed.Add("qa_verdict_not_accepted")
        return @{ verdict = "deny"; checks_failed = $failed; notes = @("QA verdict=$($QaRev.verdict)") }
    }

    $tc = $QaRev.tooling_checks
    if (-not $tc) {
        $failed.Add("tooling_checks_missing")
        $verdict = "require-human-override"
        $notes.Add("ART-QA-REV has no tooling_checks; v0.1 degrade (W2-1 manual T01-T05 not retro-fitted)")
        if ($QaRev.verdict -eq "accepted_with_gaps") {
            $failed.Add("gaps_t06_not_machine_checked")
            $notes.Add("accepted_with_gaps but T06 gaps_owner_and_release_judged not in JSON")
        }
        return @{ verdict = $verdict; checks_failed = $failed; notes = $notes }
    }

    $tKeys = @(
        "no_queue_or_eng_ok_only",
        "re_ran_ac_grep",
        "read_diff_or_change_list",
        "ac5_semantic_review",
        "ticket_artifacts_indexed"
    )
    foreach ($k in $tKeys) {
        $val = $tc.$k
        if ($null -eq $val -or -not [bool]$val) {
            $failed.Add("tooling_$k" + "_false")
            $verdict = "deny"
        }
    }

    if ($QaRev.verdict -eq "accepted_with_gaps") {
        $t06 = $tc.gaps_owner_and_release_judged
        if ($null -eq $t06) {
            $failed.Add("tooling_t06_missing")
            if ($verdict -eq "allow") { $verdict = "require-human-override" }
            $notes.Add("accepted_with_gaps requires gaps_owner_and_release_judged (T06)")
        }
        elseif (-not [bool]$t06) {
            $failed.Add("tooling_t06_false")
            $verdict = "deny"
        }
    }

    if ($notes.Count -eq 0 -and $verdict -eq "allow") {
        $notes.Add("tooling_checks T01-T05 satisfied")
    }

    return @{ verdict = $verdict; checks_failed = $failed; notes = $notes }
}

function Merge-Verdict {
    param([string]$Current, [string]$Incoming)
    $rank = @{ allow = 0; "require-human-override" = 1; deny = 2 }
    if ($rank[$Incoming] -gt $rank[$Current]) { return $Incoming }
    return $Current
}

function Invoke-GateRelEntry {
    param(
        [string]$CaseDirAbs,
        [string]$GovPath,
        [bool]$AllowFallback
    )
    $allFailed = [System.Collections.Generic.List[string]]::new()
    $allNotes = [System.Collections.Generic.List[string]]::new()
    $verdict = "allow"

    $gov = Read-JsonObject -Path $GovPath
    $govExists = ($null -ne $gov)
    $govBase = Get-GovRiskBaselineChecks -GovRisk $gov -GovExists $govExists -AllowFallback:$AllowFallback -GateLabel "GATE-REL-ENTRY"
    $verdict = Merge-Verdict -Current $verdict -Incoming $govBase.verdict
    foreach ($f in $govBase.checks_failed) { $allFailed.Add($f) }
    foreach ($n in $govBase.notes) { $allNotes.Add($n) }

    if ($govExists -and $gov.risk_types -contains "release_exit_blocked") {
        $openBlocked = $false
        if ($gov.risk_items) {
            foreach ($item in @($gov.risk_items)) {
                if ($item.risk_type -eq "release_exit_blocked" -and $item.disposition -eq "open") {
                    $openBlocked = $true
                    break
                }
            }
        }
        if ($openBlocked) {
            $allFailed.Add("release_exit_blocked_open")
            $verdict = Merge-Verdict -Current $verdict -Incoming "deny"
            $allNotes.Add("open release_exit_blocked risk item")
        }
    }

    $qaPath = Join-Path $CaseDirAbs "06_art_qa_rev.json"
    $qa = Read-JsonObject -Path $qaPath
    $qaResult = Test-ToolingChecks -QaRev $qa
    $verdict = Merge-Verdict -Current $verdict -Incoming $qaResult.verdict
    foreach ($f in $qaResult.checks_failed) { $allFailed.Add($f) }
    foreach ($n in $qaResult.notes) { $allNotes.Add($n) }

    $imp = Get-CaseImpState -CaseDirAbs $CaseDirAbs -ExplicitImpState $ImpState
    if ($imp.source -eq "unreadable") {
        $allFailed.Add("imp_state_unreadable")
        $verdict = Merge-Verdict -Current $verdict -Incoming "require-human-override"
        $allNotes.Add("imp_state not readable from case; pass -ImpState for explicit check")
    }
    else {
        $allNotes.Add("imp_state=$($imp.value) (source=$($imp.source))")
        if ($imp.value -and $imp.value -notin @("IMP-RELEASE-DECISION", "IMP-RELEASED", "IMP-OBSERVING")) {
            $allFailed.Add("imp_state_not_release_track")
            $allNotes.Add("soft gate: expected IMP-RELEASE-DECISION entry context; got $($imp.value)")
        }
    }

    return @{
        gate = "GATE-REL-ENTRY"
        verdict = $verdict
        checks_failed = @($allFailed | Select-Object -Unique)
        summary = ($allNotes -join "; ")
        imp_state = $imp.value
        gov_artifact = if ($govExists) { $gov.artifact_instance_id } else { $null }
        qa_verdict = if ($qa) { $qa.verdict } else { $null }
    }
}

function Write-GateOutput {
    param($Result)
    Write-Host ""
    Write-Host "wf_gov_gate — $($Result.gate)"
    Write-Host "verdict: $($Result.verdict)"
    if ($Result.imp_state) { Write-Host "imp_state: $($Result.imp_state)" }
    if ($Result.gov_artifact) { Write-Host "gov_artifact: $($Result.gov_artifact)" }
    if ($Result.qa_verdict) { Write-Host "qa_verdict: $($Result.qa_verdict)" }
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

# --- main ---
$root = Resolve-RepoRoot -Hint $RepoRoot
$caseAbs = Resolve-UnderRoot -Root $root -RelPath $CaseDir
if (-not $caseAbs) {
    Write-Error "CaseDir not found under repo: $CaseDir"
    exit 3
}

$result = $null
switch ($Gate) {
    "GATE-RISK-EXIT" {
        $result = Invoke-GateRiskExit -CaseDirAbs $caseAbs -AllowFallback:$AllowFallback
    }
    "GATE-REL-ENTRY" {
        if ($GovRiskPath) {
            $govAbs = Resolve-UnderRoot -Root $root -RelPath $GovRiskPath
        }
        else {
            $govAbs = Join-Path $caseAbs "art_gov_risk.json"
            if (-not (Test-Path $govAbs)) { $govAbs = $null }
        }
        if (-not $govAbs -or -not (Test-Path $govAbs)) {
            Write-Error "GovRiskPath required or art_gov_risk.json in CaseDir for GATE-REL-ENTRY"
            exit 3
        }
        $result = Invoke-GateRelEntry -CaseDirAbs $caseAbs -GovPath $govAbs -AllowFallback:$AllowFallback
    }
}

Write-GateOutput -Result $result

switch ($result.verdict) {
    "allow" { exit 0 }
    "require-human-override" { exit 1 }
    "deny" { exit 2 }
    default { exit 3 }
}
