# wf_kb_index_sync.ps1 — sync index_status JSON → case kb_index_* (W4-B)
#
# Usage (from repo root):
#   powershell -NoProfile -File workflow_v2/tools/wf_kb_index_sync.ps1 -CaseDir workflow_v2/20_pilot/W2-1_case -StatusJson workflow_v2/20_pilot/W3-B/index_status_W2-1.json
#
# Exit: 0 = updated/ok; 1 = no change; 2 = deny (schema/inputs); 3 = config/usage error
#
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$CaseDir,

    [Parameter(Mandatory = $true)]
    [string]$StatusJson,

    [string]$RepoRoot = "",
    [switch]$DryRun
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

function Read-JsonObject {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    $raw = Get-Content -Path $Path -Raw -Encoding UTF8
    return ($raw | ConvertFrom-Json)
}

function RelPathFromRoot {
    param([string]$RootAbs, [string]$PathAbs)
    $uRoot = (Resolve-Path $RootAbs).Path.TrimEnd('\')
    $uPath = (Resolve-Path $PathAbs).Path
    if ($uPath.StartsWith($uRoot, [StringComparison]::OrdinalIgnoreCase)) {
        $rel = $uPath.Substring($uRoot.Length).TrimStart('\')
        return ($rel -replace '\\', '/')
    }
    return ""
}

function Normalize-Dash {
    param([string]$Val)
    if (-not $Val) { return "-" }
    $t = $Val.Trim()
    if (-not $t) { return "-" }
    return $t
}

function Ensure-KbIndexSectionExists {
    param([string]$Text)
    return ($Text -match '###\s+KB\s*/\s*Repo\s+Index')
}

function Build-KbIndexTable {
    param(
        [hashtable]$Fields
    )
    $lines = @()
    $lines += "| Field | Value |"
    $lines += "|-------|-------|"
    $order = @(
        "kb_index_status",
        "kb_index_source",
        "kb_index_last_updated",
        "kb_index_job_id",
        "kb_index_scope_kind",
        "kb_index_subtree",
        "kb_index_baseline_ref",
        "kb_index_stale_ack",
        "kb_index_stale_reason",
        "kb_index_reindex_ticket",
        "kb_index_blocker",
        "kb_index_evidence_refs"
    )
    foreach ($k in $order) {
        $v = Normalize-Dash -Val ([string]$Fields[$k])
        $lines += "| **``$k``** | ``$v`` |"
    }
    return ($lines -join "`r`n")
}

function Replace-KbIndexTable {
    param(
        [string]$Text,
        [string]$NewTable
    )

    $lines = @($Text -split "\r?\n")
    $idxHeading = -1
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^###\s+KB\s*/\s*Repo\s+Index') { $idxHeading = $i; break }
    }
    if ($idxHeading -lt 0) { return @{ ok = $false; text = $Text; changed = $false; error = "kb_index heading not found" } }

    $idxTableStart = -1
    for ($i = $idxHeading; $i -lt ($lines.Count - 1); $i++) {
        $a = $lines[$i].Trim()
        $b = $lines[$i + 1].Trim()
        if ($a -match '^\|.*\|.*\|$' -and $b -match '^\|\s*-{3,}\s*\|\s*-{3,}\s*\|$') {
            $idxTableStart = $i
            break
        }
    }
    if ($idxTableStart -lt 0) { return @{ ok = $false; text = $Text; changed = $false; error = "kb_index table header not found" } }

    $idxTableEnd = $idxTableStart
    for ($i = $idxTableStart; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -notmatch '^\|') { $idxTableEnd = $i - 1; break }
        $idxTableEnd = $i
    }

    $oldTable = ($lines[$idxTableStart..$idxTableEnd] -join "`r`n")
    if ($oldTable.Trim() -eq $NewTable.Trim()) {
        return @{ ok = $true; text = $Text; changed = $false }
    }

    $newLines = New-Object System.Collections.Generic.List[string]
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($i -eq $idxTableStart) {
            foreach ($nl in ($NewTable -split "\r?\n")) { [void]$newLines.Add($nl) }
            $i = $idxTableEnd
            continue
        }
        [void]$newLines.Add($lines[$i])
    }

    return @{ ok = $true; text = ($newLines -join "`r`n"); changed = $true }
}

function Derive-CaseIdFromStatus {
    param($StatusObj)
    if ($StatusObj.case_id) { return [string]$StatusObj.case_id }
    return ""
}

function FieldsFromStatus {
    param(
        $StatusObj,
        [string]$StatusRelRef
    )

    $schema = [string]$StatusObj.schema_version
    if ($schema -ne "repo_index_status_v0.1") {
        return @{ ok = $false; error = "schema_version=$schema (expected repo_index_status_v0.1)" }
    }

    $jobType = [string]$StatusObj.job_type
    $jobId = [string]$StatusObj.job_id
    $st = [string]$StatusObj.status
    $finishedAt = [string]$StatusObj.finished_at
    $lastUpdated = [string]$StatusObj.last_updated

    $scopeKind = ""
    $subtree = ""
    $baseline = ""
    if ($StatusObj.scope) {
        $scopeKind = [string]$StatusObj.scope.kb_index_scope_kind
        $subtree = [string]$StatusObj.scope.kb_index_subtree
        $baseline = [string]$StatusObj.scope.kb_index_baseline_ref
    }

    $fields = @{
        kb_index_source = if ($jobType) { $jobType } else { "repo_index_v1" }
        kb_index_job_id = $jobId
        kb_index_scope_kind = if ($scopeKind) { $scopeKind } else { "repo_subtree" }
        kb_index_subtree = $subtree
        kb_index_baseline_ref = if ($baseline) { $baseline } else { "unpinned" }
        kb_index_stale_ack = "false"
        kb_index_stale_reason = "-"
        kb_index_reindex_ticket = "W4-B-INDEX-INTEGRATION"
        kb_index_evidence_refs = $StatusRelRef
    }

    if ($st -eq "succeeded") {
        $fields["kb_index_status"] = "ready"
        $fields["kb_index_last_updated"] = if ($finishedAt) { $finishedAt } else { $lastUpdated }
        $fields["kb_index_blocker"] = "-"
        return @{ ok = $true; fields = $fields }
    }

    if ($st -eq "failed" -or $st -eq "canceled") {
        $fields["kb_index_status"] = "missing"
        $fields["kb_index_last_updated"] = "-"
        $errType = [string]$StatusObj.error_type
        $errMsg = [string]$StatusObj.error_message
        if ($errType -eq "infra_unavailable") {
            $fields["kb_index_blocker"] = "infra_unavailable: " + (Normalize-Dash -Val $errMsg)
        }
        elseif ($errType) {
            $fields["kb_index_blocker"] = $errType + ": " + (Normalize-Dash -Val $errMsg)
        }
        else {
            $fields["kb_index_blocker"] = Normalize-Dash -Val $errMsg
        }
        return @{ ok = $true; fields = $fields }
    }

    if ($st -eq "running") {
        $fields["kb_index_status"] = "missing"
        $fields["kb_index_last_updated"] = "-"
        $fields["kb_index_blocker"] = "index job running (not yet succeeded)"
        return @{ ok = $true; fields = $fields }
    }

    return @{ ok = $false; error = "status=$st (expected running|succeeded|failed|canceled)" }
}

# --- main ---
$root = Resolve-RepoRoot -Hint $RepoRoot
$caseAbs = Resolve-UnderRoot -Root $root -RelPath $CaseDir
if (-not $caseAbs) {
    Write-Error "CaseDir not found under repo: $CaseDir"
    exit 3
}
$statusAbs = Resolve-UnderRoot -Root $root -RelPath $StatusJson
if (-not $statusAbs) {
    Write-Error "StatusJson not found under repo: $StatusJson"
    exit 3
}

$caseMd = Find-CaseMarkdown -CaseDirAbs $caseAbs
if (-not $caseMd) {
    Write-Error "No *_case.md found under CaseDir: $CaseDir"
    exit 3
}

$statusObj = Read-JsonObject -Path $statusAbs
if (-not $statusObj) {
    Write-Error "Failed to parse StatusJson: $StatusJson"
    exit 2
}

$statusRel = RelPathFromRoot -RootAbs $root -PathAbs $statusAbs
if (-not $statusRel) { $statusRel = $StatusJson }

$mapped = FieldsFromStatus -StatusObj $statusObj -StatusRelRef $statusRel
if (-not $mapped.ok) {
    Write-Error $mapped.error
    exit 2
}

$caseText = Get-Content -Path $caseMd -Raw -Encoding UTF8
if (-not (Ensure-KbIndexSectionExists -Text $caseText)) {
    Write-Error "kb_index_current section not found in case markdown (expected W4-B backfill section)."
    exit 2
}

$newTable = Build-KbIndexTable -Fields $mapped.fields
$rep = Replace-KbIndexTable -Text $caseText -NewTable $newTable
if (-not $rep.ok) {
    Write-Error $rep.error
    exit 2
}

if (-not $rep.changed) {
    Write-Host "wf_kb_index_sync — no change"
    exit 1
}

if ($DryRun) {
    Write-Host "wf_kb_index_sync — dry-run (would update): $caseMd"
    exit 0
}

Set-Content -Path $caseMd -Value $rep.text -Encoding UTF8
Write-Host "wf_kb_index_sync — updated: $caseMd"
exit 0

