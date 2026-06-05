# wf_k2_rollout_run.ps1 — W4-A K-2 shadow + internal canary (runtime-only)
#
# Config: workflow_v2/20_pilot/W3-A/rollout_pipeline_config.json
# Runbook: workflow_v2/20_pilot/W3-A_case/W4-A_rollout_runbook.md
#
# Usage (repo root):
#   powershell -NoProfile -ExecutionPolicy Bypass -File workflow_v2/tools/wf_k2_rollout_run.ps1 -Phase full
#   powershell -NoProfile -ExecutionPolicy Bypass -File workflow_v2/tools/wf_k2_rollout_run.ps1 -Phase shadow
#   powershell -NoProfile -ExecutionPolicy Bypass -File workflow_v2/tools/wf_k2_rollout_run.ps1 -Phase canary
#   powershell -NoProfile -ExecutionPolicy Bypass -File workflow_v2/tools/wf_k2_rollout_run.ps1 -Phase rollback
#   powershell -NoProfile -ExecutionPolicy Bypass -File workflow_v2/tools/wf_k2_rollout_run.ps1 -Phase override -OverrideBy release -OverrideReason "approved waiver"
#
# Exit: 0 ok; 1 gate fail; 2 step fail; 3 config/usage

[CmdletBinding()]
param(
    [ValidateSet("shadow", "canary", "full", "rollback", "override")]
    [string]$Phase = "full",
    [string]$ConfigJson = "",
    [string]$CaseDir = "",
    [string]$RepoRoot = "",
    [string]$OverrideBy = "",
    [string]$OverrideReason = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
    param([string]$Hint)
    if ($Hint -and (Test-Path (Join-Path $Hint "workflow_v2"))) { return (Resolve-Path $Hint).Path }
    $here = $PSScriptRoot
    if ($here) {
        $c = Split-Path (Split-Path $here -Parent) -Parent
        if (Test-Path (Join-Path $c "workflow_v2")) { return $c }
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
    return (Get-Content -Path $Path -Raw -Encoding UTF8 | ConvertFrom-Json)
}

function Write-JsonFile {
    param([string]$Path, [object]$Obj)
    $dir = Split-Path -Path $Path -Parent
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($Path, (($Obj | ConvertTo-Json -Depth 12) + "`n"), $utf8)
}

function Write-JsonLine {
    param([string]$Path, [hashtable]$Obj)
    $dir = Split-Path -Path $Path -Parent
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    Add-Content -Path $Path -Value (($Obj | ConvertTo-Json -Compress -Depth 10)) -Encoding UTF8
}

function Invoke-PythonCommand {
    param([string]$RepoRootAbs, [string[]]$ArgumentList)
    $prev = $ErrorActionPreference
    Push-Location $RepoRootAbs
    try {
        $ErrorActionPreference = "Continue"
        $lines = & python @ArgumentList 2>&1
        $code = $LASTEXITCODE
        if ($null -eq $code) { $code = 0 }
        $stdout = ($lines | Out-String)
        return @{ exit_code = [int]$code; stdout = [string]$stdout }
    } finally {
        $ErrorActionPreference = $prev
        Pop-Location
    }
}

function Invoke-ShadowStep {
    param(
        [string]$RepoRootAbs,
        [object]$Config,
        [string]$RunDir,
        [string]$TracePath,
        [bool]$IsDryRun
    )

    $shadowCfg = $Config.shadow_step
    $modules = @($shadowCfg.unittest_modules)
    $unittestArgs = @("-m", "unittest") + $modules + @("-q")
    $ut = @{ step = "k2_shadow_unittest"; phase = "shadow"; exit_ok = $false; note = "" }

    if ($IsDryRun) {
        $ut.exit_ok = $true
        $ut.note = "dry-run"
        Write-JsonLine -Path $TracePath -Obj $ut
        Write-JsonLine -Path $TracePath -Obj @{
            step = "shadow"
            phase = "shadow"
            kind = "phase_summary"
            exit_ok = $true
            note = "dry-run"
        }
        return @{ ok = $true }
    }

    $pyUt = Invoke-PythonCommand -RepoRootAbs $RepoRootAbs -ArgumentList $unittestArgs
    $ut.exit_ok = ($pyUt.exit_code -eq 0)
    $ut.note = if ($ut.exit_ok) { "unittest pass" } else { "unittest fail" }
    Write-JsonLine -Path $TracePath -Obj $ut

    $fixture = $shadowCfg.shadow_export_fixture
    if (-not $fixture) { $fixture = "tests/fixtures/eval/shadow_raw_records.jsonl" }
    $fixtureAbs = Resolve-UnderRoot -Root $RepoRootAbs -RelPath $fixture
    $evalDir = Join-Path $RunDir "eval"
    New-Item -ItemType Directory -Path $evalDir -Force | Out-Null
    $exportOut = Join-Path $evalDir "shadow_ibridge_records.latest.jsonl"

    $exportOk = $false
    $evalOk = $false
    $evalMsg = "skipped"

    if ($fixtureAbs) {
        $pyEx = Invoke-PythonCommand -RepoRootAbs $RepoRootAbs -ArgumentList @(
            "-m", "observability.ibridge_exporter",
            "--source", "shadow", "--profile", "shadow", "--force",
            $fixtureAbs, "-o", $exportOut, "--no-latest"
        )
        $exStep = @{ step = "ibridge_exporter_shadow"; phase = "shadow"; exit_ok = ($pyEx.exit_code -eq 0) }
        Write-JsonLine -Path $TracePath -Obj $exStep
        $exportOk = $exStep.exit_ok

        if ($exportOk) {
            $ratio = [string]$shadowCfg.eval_ci_max_needs_review_ratio
            if (-not $ratio) { $ratio = "0.6" }
            $tags = [string]$shadowCfg.eval_ci_fail_on_tags
            if (-not $tags) { $tags = "infra_risk" }
            $pyEv = Invoke-PythonCommand -RepoRootAbs $RepoRootAbs -ArgumentList @(
                "-m", "observability.eval_ci_check",
                $exportOut,
                "--max-needs-review-ratio", $ratio,
                "--fail-on-tags", $tags
            )
            $evalOk = ($pyEv.exit_code -eq 0)
            try {
                if ($pyEv.stdout.Trim()) {
                    $parsed = $pyEv.stdout.Trim() | ConvertFrom-Json
                    $evalMsg = [string]$parsed.message
                }
            } catch { $evalMsg = "eval parse error" }
            Write-JsonLine -Path $TracePath -Obj @{ step = "eval_ci_check_shadow"; phase = "shadow"; exit_ok = $evalOk; note = $evalMsg }
        }
    }

    $ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $runMd = Join-Path $RunDir "shadow_run_01.md"
    $lines = @(
        "# W4-A shadow run — $ts",
        "",
        "| Field | Value |",
        "|-------|-------|",
        "| pilot_stream | $($Config.pilot_stream_id) |",
        "| primary_source | ask (user-visible) |",
        "| unittest_ok | $($ut.exit_ok) |",
        "| export_ok | $exportOk |",
        "| eval_ci_ok | $evalOk |",
        "| eval_message | $evalMsg |",
        "",
        "> Shadow does not change user-facing answers."
    )
    $lines | Set-Content -Path $runMd -Encoding UTF8

    $caseDir = Split-Path $RunDir -Parent
    Copy-Item -Path $runMd -Destination (Join-Path $caseDir "shadow_run_latest.md") -Force

    Write-JsonFile -Path (Join-Path $RunDir "shadow_state.json") -Obj @{
        schema_version = "w4a-shadow-state-v0.1"
        ok = ($ut.exit_ok -and $evalOk)
        unittest_ok = $ut.exit_ok
        eval_ok = $evalOk
        eval_message = $evalMsg
        recorded_at = $ts
    }

    $ok = $ut.exit_ok -and $evalOk
    if (-not $IsDryRun) {
        Write-JsonLine -Path $TracePath -Obj @{
            step = "shadow"
            phase = "shadow"
            kind = "phase_summary"
            exit_ok = $ok
            note = "shadow phase gate"
        }
    }
    return @{ ok = $ok; shadow_run_md = $runMd }
}

function Invoke-CanaryStep {
    param(
        [string]$RepoRootAbs,
        [string]$ConfigPath,
        [string]$CaseDirAbs,
        [string]$RunDir,
        [string]$RunId,
        [string]$TracePath,
        [bool]$IsDryRun
    )

    if ($IsDryRun) {
        Write-JsonLine -Path $TracePath -Obj @{ step = "internal_canary"; phase = "canary"; exit_ok = $true; note = "dry-run" }
        Write-JsonLine -Path $TracePath -Obj @{ step = "canary"; phase = "canary"; kind = "phase_summary"; exit_ok = $true; note = "dry-run" }
        return @{ ok = $true }
    }

    $sim = Join-Path $RepoRootAbs "workflow_v2/tools/wf_k2_rollout_canary_sim.py"
    if (-not (Test-Path $sim)) { return @{ ok = $false; message = "missing wf_k2_rollout_canary_sim.py" } }

    $py = Invoke-PythonCommand -RepoRootAbs $RepoRootAbs -ArgumentList @(
        $sim, "--config", $ConfigPath, "--case-dir", $CaseDirAbs, "--run-id", $RunId
    )
    $parsed = $null
    try { if ($py.stdout.Trim()) { $parsed = $py.stdout.Trim() | ConvertFrom-Json } } catch { }

    $step = @{
        step = "internal_canary"
        phase = "canary"
        exit_ok = ($py.exit_code -eq 0)
        note = if ($parsed) { "cohort=$($parsed.cohort_in_count)/$($parsed.sample_count)" } else { "parse failed" }
    }
    Write-JsonLine -Path $TracePath -Obj $step
    $canaryOk = ($py.exit_code -eq 0)
    Write-JsonLine -Path $TracePath -Obj @{
        step = "canary"
        phase = "canary"
        kind = "phase_summary"
        exit_ok = $canaryOk
        note = "canary phase gate"
    }
    if ($py.exit_code -ne 0) { return @{ ok = $false } }

    $ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $canaryMd = Join-Path $RunDir "canary_run_01.md"
    $assignJson = ($parsed.assignments | ConvertTo-Json -Depth 6 -Compress)
    @(
        "# W4-A canary run — $ts",
        "",
        "| Field | Value |",
        "|-------|-------|",
        "| run_id | $RunId |",
        "| traffic_percent | $($parsed.traffic_percent) |",
        "| cohort_in | $($parsed.cohort_in_count) / $($parsed.sample_count) |",
        "",
        "## Assignments (JSON)",
        "",
        $assignJson,
        ""
    ) | Set-Content -Path $canaryMd -Encoding UTF8

    Copy-Item -Path $canaryMd -Destination (Join-Path $CaseDirAbs "canary_run_latest.md") -Force
    return @{ ok = $true; canary_run_md = $canaryMd }
}

function Invoke-RollbackStep {
    param([object]$Config, [string]$CaseDirAbs, [string]$RunId, [string]$TracePath, [bool]$IsDryRun)

    $rbPath = Join-Path $CaseDirAbs $Config.rollback.record_filename
    $doc = @{
        schema = "w4a_rollback/v0.1"
        run_id = $RunId
        action = $Config.rollback.default_action
        applied_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        traffic_percent = 0
        primary_source = "ask"
        message = "W4-A pilot rollback - ask-only, no prod CI change"
    }
    if (-not $IsDryRun) { Write-JsonFile -Path $rbPath -Obj $doc }
    Write-JsonLine -Path $TracePath -Obj @{ step = "rollback"; exit_ok = $true }
    Write-Host "VERDICT=OK step=rollback record=$rbPath"
    return @{ ok = $true }
}

function Invoke-OverrideStep {
    param(
        [object]$Config, [string]$CaseDirAbs, [string]$RunId,
        [string]$TracePath, [string]$By, [string]$Reason, [bool]$IsDryRun
    )

    $allowed = @($Config.override.allowed_roles)
    if (-not $By -or ($allowed -notcontains $By)) {
        Write-Host "VERDICT=FAILED step=override reason=role_not_allowed"
        return @{ ok = $false }
    }
    if (-not $Reason) {
        Write-Host "VERDICT=FAILED step=override reason=missing_reason"
        return @{ ok = $false }
    }

    $ovPath = Join-Path $CaseDirAbs $Config.override.record_filename
    $doc = @{
        schema = "w4a_override/v0.1"
        run_id = $RunId
        override_by_role = $By
        reason = $Reason
        recorded_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    }
    if (-not $IsDryRun) { Write-JsonFile -Path $ovPath -Obj $doc }
    Write-JsonLine -Path $TracePath -Obj @{ step = "override"; exit_ok = $true; by = $By }
    Write-Host "VERDICT=OK step=override record=$ovPath"
    return @{ ok = $true }
}

# --- main ---
$root = Resolve-RepoRoot -Hint $RepoRoot
$defaultConfig = Join-Path $root "workflow_v2/20_pilot/W3-A/rollout_pipeline_config.json"
$configPath = if ($ConfigJson) { Resolve-UnderRoot -Root $root -RelPath $ConfigJson } else { $defaultConfig }
$config = Read-JsonObject -Path $configPath
if (-not $config) {
    Write-Host "VERDICT=FAILED reason=config_missing path=$configPath"
    exit 3
}

$caseRel = if ($CaseDir) { $CaseDir } else { $config.paths.case_dir }
$caseAbs = Resolve-UnderRoot -Root $root -RelPath $caseRel
if (-not $caseAbs) {
    Write-Host "VERDICT=FAILED reason=case_dir_missing"
    exit 3
}

$runId = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd_HHmmss")
$runDir = Join-Path $caseAbs "run_records\$runId"
if (-not $DryRun) { New-Item -ItemType Directory -Path $runDir -Force | Out-Null }
$tracePath = Join-Path $runDir "rollout_trace.jsonl"

$exitCode = 0

switch ($Phase) {
    "shadow" {
        $s = Invoke-ShadowStep -RepoRootAbs $root -Config $config -RunDir $runDir -TracePath $tracePath -IsDryRun:$DryRun
        if (-not $s.ok) { $exitCode = 1 }
        else { Write-Host "VERDICT=OK step=shadow run_dir=$runDir" }
    }
    "canary" {
        $c = Invoke-CanaryStep -RepoRootAbs $root -ConfigPath $configPath -CaseDirAbs $caseAbs -RunDir $runDir -RunId $runId -TracePath $tracePath -IsDryRun:$DryRun
        if (-not $c.ok) { $exitCode = 1 }
        else { Write-Host "VERDICT=OK step=canary run_dir=$runDir" }
    }
    "full" {
        $s = Invoke-ShadowStep -RepoRootAbs $root -Config $config -RunDir $runDir -TracePath $tracePath -IsDryRun:$DryRun
        if (-not $s.ok) {
            Write-Host "VERDICT=FAILED step=shadow"
            exit 1
        }
        Write-Host "VERDICT=OK step=shadow run_dir=$runDir"
        $c = Invoke-CanaryStep -RepoRootAbs $root -ConfigPath $configPath -CaseDirAbs $caseAbs -RunDir $runDir -RunId $runId -TracePath $tracePath -IsDryRun:$DryRun
        if (-not $c.ok) { $exitCode = 1; Write-Host "VERDICT=FAILED step=canary" }
        else { Write-Host "VERDICT=OK step=canary run_dir=$runDir" }
    }
    "rollback" {
        Invoke-RollbackStep -Config $config -CaseDirAbs $caseAbs -RunId $runId -TracePath $tracePath -IsDryRun:$DryRun | Out-Null
    }
    "override" {
        $o = Invoke-OverrideStep -Config $config -CaseDirAbs $caseAbs -RunId $runId -TracePath $tracePath -By $OverrideBy -Reason $OverrideReason -IsDryRun:$DryRun
        if (-not $o.ok) { exit 3 }
    }
}

Write-Host "PILOT_STREAM=$($config.pilot_stream_id)"
Write-Host "RUN_ID=$runId"
Write-Host "TRACE=$tracePath"
exit $exitCode
