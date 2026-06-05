#Requires -Version 5.1
<#
.SYNOPSIS
    Setup-Schedule.ps1 — v2.53 Windows 任務排程：註冊 / 撤銷 Tang_Chariot_Auto_Refine

.DESCRIPTION
    -Install ：
      · 任務名稱：Tang_Chariot_Auto_Refine（可改 -TaskName）
      · 觸發：每日低負載時段（預設 03:00）+ 使用者登入時
      · 動作：powershell -ExecutionPolicy Bypass -EncodedCommand …（隱藏視窗）
      · 輸出：Start-Transcript → 06_Exports_Output\reports\scheduler\last_run.log
      · 設定：最高權限；單次超過 2 小時由排程器停止；MultipleInstances IgnoreNew

    -Remove ：一鍵撤銷同名工作。

    「不論使用者是否登入均執行」：
      · -PrincipalMode System（預設）以 NT AUTHORITY\SYSTEM 註冊。
      · 或以 -Credential 指定本機帳戶並儲存密碼。
      · -PrincipalMode Interactive 僅在目前使用者已登入時可靠執行。

.PARAMETER Install
    註冊排程（需提高權限執行）。

.PARAMETER Remove
    移除排程。

.PARAMETER PrincipalMode
    System | Interactive（預設 System）。

.PARAMETER Credential
    若指定，優先於 PrincipalMode；以該帳戶 + 儲存密碼註冊。

.EXAMPLE
    .\Setup-Schedule.ps1 -Install
    .\Setup-Schedule.ps1 -Install -DailyHour 2 -DailyMinute 30
    .\Setup-Schedule.ps1 -Remove
#>

[CmdletBinding(DefaultParameterSetName = 'None')]
param(
    [Parameter(ParameterSetName = 'Install', Mandatory = $true)]
    [switch]$Install,

    [Parameter(ParameterSetName = 'Remove', Mandatory = $true)]
    [switch]$Remove,

    [string]$TaskName = 'Tang_Chariot_Auto_Refine',

    [ValidateRange(0, 23)]
    [int]$DailyHour = 3,

    [ValidateRange(0, 59)]
    [int]$DailyMinute = 0,

    [int]$WaveN = 100,

    [ValidateSet('System', 'Interactive')]
    [string]$PrincipalMode = 'System',

    [PSCredential]$Credential = $null,

    [switch]$SkipLogonTrigger
)

$ErrorActionPreference = 'Stop'

$Root       = Split-Path -Parent $PSScriptRoot
$LaunchPs1  = Join-Path $Root '04_Workflows\Launch-Warpath.ps1'
$LogDir     = Join-Path $Root '06_Exports_Output\reports\scheduler'
$LastRunLog = Join-Path $LogDir 'last_run.log'
$SetupLog   = Join-Path $LogDir 'setup_register.log'

function Test-IsAdministrator {
    $p = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Ensure-SchedulerDir {
    if (-not (Test-Path -LiteralPath $LogDir)) {
        New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    }
}

function Escape-SingleQuoted {
    param([string]$Text)
    if ($null -eq $Text) { return '' }
    return $Text.Replace("'", "''")
}

function Build-InvokeScriptBlockSource {
    param(
        [string]$LaunchPath,
        [string]$TranscriptPath,
        [string]$GovRoot,
        [int]$Wave
    )
    $lp = Escape-SingleQuoted $LaunchPath
    $tp = Escape-SingleQuoted $TranscriptPath
    $gr = Escape-SingleQuoted $GovRoot
    return @"
`$ErrorActionPreference = 'Stop'
`$env:PYTHONPATH = '$gr'
`$env:PYTHONUTF8 = '1'
`$env:TANG_GOV_ROOT = '$gr'
New-Item -ItemType Directory -Force -Path (Split-Path -LiteralPath '$tp') | Out-Null
`$exitCode = 1
try {
  Start-Transcript -LiteralPath '$tp' -Force | Out-Null
  try {
    & '$lp' -WaveN $Wave
    `$exitCode = `$LASTEXITCODE
  }
  finally {
    try { Stop-Transcript | Out-Null } catch { }
  }
}
catch {
  `$_.Exception.Message | Out-File -LiteralPath '$tp' -Encoding utf8 -Append
  `$exitCode = 1
}
exit `$exitCode
"@
}

function Write-SetupAuditLog {
    param([string]$TaskNm)
    Ensure-SchedulerDir
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine("=== Setup-Schedule audit $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss K') ===")
    [void]$sb.AppendLine("TaskName: $TaskNm")
    try {
        $t = Get-ScheduledTask -TaskName $TaskNm -ErrorAction Stop
        [void]$sb.AppendLine('--- Get-ScheduledTask ---')
        [void]$sb.AppendLine(($t | Format-List * | Out-String))
        $info = Get-ScheduledTaskInfo -InputObject $t -ErrorAction Stop
        [void]$sb.AppendLine('--- Get-ScheduledTaskInfo ---')
        [void]$sb.AppendLine(($info | Format-List * | Out-String))
        [void]$sb.AppendLine('--- Principal / Settings (摘要) ---')
        [void]$sb.AppendLine(('UserId={0} LogonType={1} RunLevel={2}' -f $t.Principal.UserId, $t.Principal.LogonType, $t.Principal.RunLevel))
        [void]$sb.AppendLine(('ExecutionTimeLimit={0} MultipleInstances={1} AllowStartIfOnBatteries={2}' -f $t.Settings.ExecutionTimeLimit, $t.Settings.MultipleInstances, $t.Settings.AllowStartIfOnBatteries))
        $idx = 1
        foreach ($tr in $t.Triggers) {
            [void]$sb.AppendLine(('Trigger[{0}] CimClass={1}' -f $idx, $tr.CimClass.CimClassName))
            [void]$sb.AppendLine(($tr | Format-List * | Out-String))
            $idx++
        }
    }
    catch {
        [void]$sb.AppendLine("ERROR: $($_.Exception.Message)")
    }
    Set-Content -LiteralPath $SetupLog -Value $sb.ToString() -Encoding UTF8
    Write-Host "Audit written: $SetupLog" -ForegroundColor Green
}

# ── Remove ────────────────────────────────────────────────
if ($PSCmdlet.ParameterSetName -eq 'Remove') {
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
        Write-Host "[OK] Removed scheduled task: $TaskName" -ForegroundColor Green
    }
    catch [Microsoft.Management.Infrastructure.CimException] {
        $msg = $_.Exception.Message
        if ($msg -match 'Access is denied') {
            Write-Error "Remove failed: run PowerShell as Administrator (task may be registered as SYSTEM)."
        }
        elseif ($msg -match 'cannot find|No mapping|not found|Invalid class') {
            Write-Host "[INFO] Task not present: $TaskName" -ForegroundColor Yellow
        }
        else { throw }
    }
    exit 0
}

# ── Install ───────────────────────────────────────────────
if (-not (Test-IsAdministrator)) {
    Write-Error 'Install requires elevated PowerShell (Run as administrator).'
    exit 1
}

if (-not (Test-Path -LiteralPath $LaunchPs1)) {
    Write-Error "Launch-Warpath.ps1 not found: $LaunchPs1"
    exit 2
}

Ensure-SchedulerDir

$scriptSrc = Build-InvokeScriptBlockSource -LaunchPath $LaunchPs1 -TranscriptPath $LastRunLog -GovRoot $Root -Wave $WaveN
$encoded = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($scriptSrc))
$argFull = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -EncodedCommand $encoded"

$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $argFull

$today = [datetime]::Today
$atDaily = $today.AddHours($DailyHour).AddMinutes($DailyMinute)
$triggerDaily = New-ScheduledTaskTrigger -Daily -At $atDaily

$triggers = @($triggerDaily)
if (-not $SkipLogonTrigger) {
    $triggerLogon = New-ScheduledTaskTrigger -AtLogOn
    $triggers += $triggerLogon
}

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -MultipleInstances IgnoreNew `
    -RestartCount 0 `
    -StartWhenAvailable

$userIdForPrint = ''

if ($null -ne $Credential) {
    $userId = $Credential.UserName
    $plain = $Credential.GetNetworkCredential().Password
    $principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Password -RunLevel Highest
    Register-ScheduledTask -TaskName $TaskName `
        -Description 'Tang Chariot v2.53 - Launch-Warpath auto (Doctor+Register+Refine+Alert)' `
        -Action $action -Trigger $triggers -Settings $settings `
        -Principal $principal -User $userId -Password $plain -Force | Out-Null
    $userIdForPrint = $userId
}
elseif ($PrincipalMode -eq 'System') {
    $principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
    Register-ScheduledTask -TaskName $TaskName `
        -Description 'Tang Chariot v2.53 - Launch-Warpath auto (Doctor+Register+Refine+Alert)' `
        -Action $action -Trigger $triggers -Settings $settings `
        -Principal $principal -Force | Out-Null
    $userIdForPrint = 'SYSTEM'
}
else {
    $userId = "$env:USERDOMAIN\$env:USERNAME"
    $principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Highest
    Register-ScheduledTask -TaskName $TaskName `
        -Description 'Tang Chariot v2.53 - Launch-Warpath auto (Doctor+Register+Refine+Alert)' `
        -Action $action -Trigger $triggers -Settings $settings `
        -Principal $principal -Force | Out-Null
    $userIdForPrint = $userId
}

Enable-ScheduledTask -TaskName $TaskName | Out-Null

Write-Host "[OK] Registered: $TaskName" -ForegroundColor Green
Write-Host "  Daily at    : $($atDaily.ToString('HH:mm'))"
Write-Host "  Logon trig  : $(-not $SkipLogonTrigger)"
Write-Host "  WaveN       : $WaveN"
Write-Host "  Last run log: $LastRunLog"
Write-Host "  Principal   : $userIdForPrint"

Write-SetupAuditLog -TaskNm $TaskName
Get-Content -LiteralPath $SetupLog -Encoding UTF8
