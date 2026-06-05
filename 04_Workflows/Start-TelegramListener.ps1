#Requires -Version 5.1
# Start Telegram listener (long poll + Groq chat). Single instance via lock file.
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Workflows = Join-Path $Root '04_Workflows'
$LockFile = Join-Path $Workflows '.telegram_listener.lock'
$LogDir = Join-Path (Join-Path $Root '06_Exports_Output') 'reports\telegram_listener'

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

if (Test-Path $LockFile) {
    try {
        $j = Get-Content $LockFile -Raw -Encoding UTF8 | ConvertFrom-Json
        $oldPid = [int]$j.pid
        $p = Get-Process -Id $oldPid -ErrorAction SilentlyContinue
        if ($p) {
            Write-Host "Already running PID=$oldPid"
            exit 0
        }
    }
    catch { }
    Remove-Item $LockFile -Force -ErrorAction SilentlyContinue
}

$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$outLog = Join-Path $LogDir "listener_$ts.out.log"
$errLog = Join-Path $LogDir "listener_$ts.err.log"

$proc = Start-Process -FilePath 'python' `
    -ArgumentList @('_telegram_listener.py', '--mode', 'loop') `
    -WorkingDirectory $Workflows `
    -RedirectStandardOutput $outLog `
    -RedirectStandardError $errLog `
    -WindowStyle Hidden `
    -PassThru

Write-Host "Started PID=$($proc.Id)"
Write-Host "stdout: $outLog"
Write-Host "stderr: $errLog"
