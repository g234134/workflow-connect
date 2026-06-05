#Requires -Version 5.1
# Stop Telegram listener and remove lock file.
$ErrorActionPreference = 'Continue'
$Workflows = $PSScriptRoot
$LockFile = Join-Path $Workflows '.telegram_listener.lock'

if (-not (Test-Path $LockFile)) {
    Write-Host 'No lock file; listener may not be running.'
    exit 0
}

try {
    $j = Get-Content $LockFile -Raw -Encoding UTF8 | ConvertFrom-Json
    $pidToKill = [int]$j.pid
    $p = Get-Process -Id $pidToKill -ErrorAction SilentlyContinue
    if ($p) {
        Stop-Process -Id $pidToKill -Force
        Write-Host "Stopped PID=$pidToKill"
    }
    else {
        Write-Host "Stale lock PID=$pidToKill (process gone); clearing lock."
    }
}
catch {
    Write-Host "Lock read error: $_"
}

Remove-Item $LockFile -Force -ErrorAction SilentlyContinue
Write-Host 'Done.'
