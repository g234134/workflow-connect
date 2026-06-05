#Requires -Version 5.1
# Start-InboundWatchdog.ps1 — 啟動刑部 raw_inbound 生料哨兵（gov_main + watchdog）
# 用法：
#   . .\04_Workflows\Enter-Main.ps1
#   .\04_Workflows\Start-InboundWatchdog.ps1
# 追加參數會原樣轉給 _inbound_watchdog.py，例如：
#   .\Start-InboundWatchdog.ps1 --no-bootstrap
#   .\Start-InboundWatchdog.ps1 --bootstrap-only
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$VenvPy = Join-Path $Root '01_Environments\python_venvs\gov_main\Scripts\python.exe'
$Script = Join-Path $PSScriptRoot '_inbound_watchdog.py'

if (-not (Test-Path $VenvPy)) {
    Write-Error "[gov_main] venv 未就緒：$VenvPy"
    exit 1
}

$env:TANG_GOV_ROOT = $Root
$env:PYTHONUTF8 = '1'
$AgentsCore = Join-Path $Root '02_Agents_Core'
$Workflows = Join-Path $Root '04_Workflows'
$env:PYTHONPATH = "$Root;$AgentsCore;$Workflows"

& $VenvPy $Script @args
