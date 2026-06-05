#Requires -Version 5.1
# Start-ScoutEngine.ps1 — 啟動 v2.55b 前線偵察兵（gov_agency venv）
# 用法：
#   . .\04_Workflows\Enter-Agency.ps1
#   .\04_Workflows\Start-ScoutEngine.ps1 --simulate
# 環境變數：SCOUT_PLATFORM、SCOUT_TARGET_URL（http 模式）
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$VenvPy = Join-Path $Root '01_Environments\python_venvs\gov_agency\Scripts\python.exe'
$Script = Join-Path $PSScriptRoot '_scout_engine.py'

if (-not (Test-Path $VenvPy)) {
    Write-Error "[gov_agency] venv 未就緒：$VenvPy"
    exit 1
}

$env:TANG_GOV_ROOT = $Root
$env:PYTHONUTF8 = '1'
$AgentsCore = Join-Path $Root '02_Agents_Core'
$Workflows = Join-Path $Root '04_Workflows'
$env:PYTHONPATH = "$Root;$AgentsCore;$Workflows"

& $VenvPy $Script @args
