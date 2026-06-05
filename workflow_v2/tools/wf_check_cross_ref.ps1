# wf_check_cross_ref.ps1 — G7/G8 cross-ref acceptance checks (AC bundle by Scope)
#
# Usage (from repo root):
#   powershell -NoProfile -File workflow_v2/tools/wf_check_cross_ref.ps1
#   powershell -NoProfile -File workflow_v2/tools/wf_check_cross_ref.ps1 -Scope G8Recon -CaseId W2-1
#   powershell -NoProfile -File workflow_v2/tools/wf_check_cross_ref.ps1 -ListScopes
#
# Exit: 0 = all checks pass; 1 = one or more failures; 2 = path/config error

[CmdletBinding()]
param(
    [string]$RepoRoot = "",
    [ValidateSet("G8Recon", "Default")]
    [string]$Scope = "G8Recon",
    [string]$CaseId = "",
    [string]$G7Dir = "",
    [string]$G8EngFile = "",
    [switch]$Strict,
    [switch]$ListScopes
)

$ErrorActionPreference = "Stop"

# CaseId → default Scope (hook for future pilot tickets; extend here only)
$Script:CaseScopeMap = @{
    "W2-1" = "G8Recon"
}

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

function Invoke-PatternCount {
    param(
        [string]$Pattern,
        [string[]]$Paths,
        [string]$Root,
        [switch]$SimpleMatch
    )
    $fullPaths = @()
    foreach ($p in $Paths) {
        $fp = Join-Path $Root ($p -replace '/', [IO.Path]::DirectorySeparatorChar)
        if (-not (Test-Path $fp)) { return @{ ok = $false; count = -1; error = "missing: $p" } }
        $fullPaths += $fp
    }

    $rg = Get-Command rg -ErrorAction SilentlyContinue
    if ($rg) {
        $out = & rg --count-matches $Pattern @fullPaths 2>$null
        if ($LASTEXITCODE -gt 1) { return @{ ok = $false; count = -1; error = "rg failed: $Pattern" } }
        if (-not $out) { return @{ ok = $true; count = 0; engine = "rg" } }
        $total = 0
        foreach ($line in $out) {
            if ($line -match ':(\d+)$') { $total += [int]$Matches[1] }
        }
        return @{ ok = $true; count = $total; engine = "rg" }
    }

    # Fallback: Select-String (no external rg required)
    $total = 0
    foreach ($fp in $fullPaths) {
        $ssArgs = @{
            Pattern     = $Pattern
            AllMatches  = $true
            ErrorAction = "SilentlyContinue"
        }
        if ($SimpleMatch) { $ssArgs["SimpleMatch"] = $true }
        if (Test-Path $fp -PathType Container) {
            $hits = Get-ChildItem -Path $fp -Recurse -File -ErrorAction SilentlyContinue |
                ForEach-Object { Select-String -Path $_.FullName @ssArgs }
        }
        else {
            $hits = Select-String -Path $fp @ssArgs
        }
        if ($hits) {
            foreach ($h in $hits) {
                if ($h.Matches) { $total += $h.Matches.Count } else { $total += 1 }
            }
        }
    }
    return @{ ok = $true; count = $total; engine = "Select-String" }
}

function Get-ScopeProfile {
    param([string]$Name)
    $profiles = @{
        Default = @{ AliasOf = "G8Recon" }
        G8Recon = @{
            Label    = "G8-RECON cross-ref bundle (W2-1 AC-1..AC-4)"
            G7Dir    = "workflow_v2/10_governance/G7_state_machine"
            G8EngFile = "workflow_v2/10_governance/G8_artifact_contract/30_engineering.md"
            AcBundle = "AC-1,AC-2,AC-3,AC-4"
        }
    }
    if (-not $profiles.ContainsKey($Name)) { return $null }
    $p = $profiles[$Name]
    if ($p.AliasOf) { return $profiles[$p.AliasOf] }
    return $p
}

function New-G8ReconCheckBundle {
    param(
        [string]$G7DirRel,
        [string]$G8EngRel
    )
    # Stale-placeholder literals (UTF-8). AC-2 = three SimpleMatch probes (equiv. rg "待 G8-[125]").
    $staleG8 = @(
        [char]0x5F85 + " G8-1"
        [char]0x5F85 + " G8-2"
        [char]0x5F85 + " G8-5"
    )
    $staleG102 = [char]0x5F85 + " G10-2"

    return @(
        @{
            Id = "AC-1"
            AcGroup = "AC-1"
            Desc = "No stale ART-REL-RECORD in G7-2 entry conditions"
            Pattern = "ART-REL-RECORD"
            Paths = @("$G7DirRel/20_entry_conditions.md")
            Want = 0
            Min = $null
            SimpleMatch = $false
        },
        @{
            Id = "AC-2a"
            AcGroup = "AC-2"
            Desc = "No stale placeholder 待 G8-1 (G7 entry + exit)"
            Pattern = $staleG8[0]
            Paths = @("$G7DirRel/20_entry_conditions.md", "$G7DirRel/30_exit_and_transitions.md")
            Want = 0
            Min = $null
            SimpleMatch = $true
        },
        @{
            Id = "AC-2b"
            AcGroup = "AC-2"
            Desc = "No stale placeholder 待 G8-2 (G7 entry + exit)"
            Pattern = $staleG8[1]
            Paths = @("$G7DirRel/20_entry_conditions.md", "$G7DirRel/30_exit_and_transitions.md")
            Want = 0
            Min = $null
            SimpleMatch = $true
        },
        @{
            Id = "AC-2c"
            AcGroup = "AC-2"
            Desc = "No stale placeholder 待 G8-5 (G7 entry + exit)"
            Pattern = $staleG8[2]
            Paths = @("$G7DirRel/20_entry_conditions.md", "$G7DirRel/30_exit_and_transitions.md")
            Want = 0
            Min = $null
            SimpleMatch = $true
        },
        @{
            Id = "AC-3"
            AcGroup = "AC-3"
            Desc = "No bare 待 G10-2 in G7-3 exit/transitions"
            Pattern = $staleG102
            Paths = @("$G7DirRel/30_exit_and_transitions.md")
            Want = 0
            Min = $null
            SimpleMatch = $true
        },
        @{
            Id = "AC-4a"
            AcGroup = "AC-4"
            Desc = "No wrong filename 10_states.md in G8-3 engineering contract"
            Pattern = "10_states"
            Paths = @($G8EngRel)
            Want = 0
            Min = $null
            SimpleMatch = $false
        },
        @{
            Id = "AC-4b"
            AcGroup = "AC-4"
            Desc = "Formal G7-1 path 10_workflow_states.md referenced in G8-3"
            Pattern = "10_workflow_states"
            Paths = @($G8EngRel)
            Want = $null
            Min = 1
            SimpleMatch = $false
        }
    )
}

function Get-ChecksForScope {
    param(
        [string]$ScopeName,
        [string]$G7DirRel,
        [string]$G8EngRel
    )
    switch ($ScopeName) {
        "Default" { $ScopeName = "G8Recon" }
        "G8Recon" { return New-G8ReconCheckBundle -G7DirRel $G7DirRel -G8EngRel $G8EngRel }
        default { throw "Unknown scope: $ScopeName" }
    }
}

if ($ListScopes) {
    Write-Host "wf_check_cross_ref — available scopes:"
    Write-Host "  G8Recon  — G7/G8 cross-ref bundle (AC-1..AC-4); alias: Default"
    Write-Host "  Default  — same as G8Recon"
    Write-Host ""
    Write-Host "CaseId presets (optional -CaseId):"
    foreach ($k in ($Script:CaseScopeMap.Keys | Sort-Object)) {
        Write-Host "  $k  ->  $($Script:CaseScopeMap[$k])"
    }
    exit 0
}

# Resolve Scope from CaseId when caller did not override Scope explicitly
$effectiveScope = $Scope
if ($Scope -eq "G8Recon" -and $CaseId -and $Script:CaseScopeMap.ContainsKey($CaseId)) {
    $effectiveScope = $Script:CaseScopeMap[$CaseId]
}
if ($Scope -eq "Default") { $effectiveScope = "G8Recon" }

$profile = Get-ScopeProfile -Name $effectiveScope
if (-not $profile) {
    Write-Error "Unknown scope '$effectiveScope'. Use -ListScopes."
    exit 2
}

$g7Rel = if ($G7Dir) { $G7Dir } else { $profile.G7Dir }
$g8Rel = if ($G8EngFile) { $G8EngFile } else { $profile.G8EngFile }

$root = Resolve-RepoRoot -Hint $RepoRoot
$g7Abs = Join-Path $root ($g7Rel -replace '/', [IO.Path]::DirectorySeparatorChar)
$g8Abs = Join-Path $root ($g8Rel -replace '/', [IO.Path]::DirectorySeparatorChar)

if (-not (Test-Path $g7Abs)) { Write-Error "G7 dir not found: $g7Abs"; exit 2 }
if (-not (Test-Path $g8Abs)) { Write-Error "G8 engineering contract not found: $g8Abs"; exit 2 }

$checks = Get-ChecksForScope -ScopeName $effectiveScope -G7DirRel $g7Rel -G8EngRel $g8Rel

$failed = 0
$caseLabel = if ($CaseId) { " | case: $CaseId" } else { "" }
Write-Host "wf_check_cross_ref — scope: $effectiveScope ($($profile.Label))$caseLabel"
Write-Host "repo root: $root"
Write-Host "G7: $g7Rel"
Write-Host "G8 eng: $g8Rel"
Write-Host "AC bundle: $($profile.AcBundle) (7 probes; AC-5 not automated)"
Write-Host ""

foreach ($c in $checks) {
    $simple = $false
    if ($c.ContainsKey("SimpleMatch")) { $simple = [bool]$c.SimpleMatch }
    $r = Invoke-PatternCount -Pattern $c.Pattern -Paths $c.Paths -Root $root -SimpleMatch:$simple
    $pass = $false
    $detail = ""

    if (-not $r.ok) {
        $pass = $false
        $detail = $r.error
    }
    elseif ($null -ne $c.Want) {
        $pass = ($r.count -eq $c.Want)
        $detail = "matches=$($r.count) want=$($c.Want)"
    }
    else {
        $pass = ($r.count -ge $c.Min)
        $detail = "matches=$($r.count) want>=$($c.Min)"
    }

    $icon = if ($pass) { "[PASS]" } else { "[FAIL]" }
    if (-not $pass) { $failed++ }
    $eng = if ($r.engine) { " via $($r.engine)" } else { "" }
    Write-Host "$icon $($c.Id) ($($c.AcGroup)): $($c.Desc)"
    Write-Host "       pattern: $($c.Pattern) | $detail$eng"
}

Write-Host ""
if ($failed -eq 0) {
    Write-Host "Summary: ALL PASS ($($checks.Count) checks) | exit 0"
    exit 0
}

Write-Host "Summary: $failed / $($checks.Count) FAILED | exit 1"
if ($Strict) { exit 1 }
exit 1
