#Requires -Version 5.1
# Enter-Agency.ps1 — 啟動副艙 (gov_agency)，驗證 crewai 並設定跨艙 PYTHONPATH
# 用法：
#   .\Enter-Agency.ps1          ← 僅做驗證 (activation 退出後失效)
#   . .\Enter-Agency.ps1        ← 點源後 activation 持續至本 shell 結束
$ErrorActionPreference = 'Stop'

$Root     = Split-Path -Parent $PSScriptRoot
$VenvDir  = Join-Path $Root '01_Environments\python_venvs\gov_agency'
$Activate = Join-Path $VenvDir 'Scripts\Activate.ps1'
$VenvPy   = Join-Path $VenvDir 'Scripts\python.exe'

if (-not (Test-Path $VenvPy)) {
    Write-Error "[gov_agency] venv 尚未建立: $VenvDir`n請先執行 Bootstrap (建立雙艙)。"
    return
}

$ProjectRoot = $Root
$AgentsCore  = Join-Path $Root '02_Agents_Core'
$Workflows   = Join-Path $Root '04_Workflows'
$AgencyHome  = Join-Path $AgentsCore 'agency-agents'
$env:PYTHONPATH = "$ProjectRoot;$AgentsCore;$Workflows;$AgencyHome"
$env:PYTHONUTF8 = '1'
$env:TANG_GOV_ROOT = $Root

. (Join-Path $PSScriptRoot '_Load-TangEnv.ps1')
Initialize-TangEnv -Root $Root -Label 'gov_agency' | Out-Null

Write-Host '──────── gov_agency ────────'
& $VenvPy -c "import sys; print(f'Python   : {sys.version.split()[0]}')`ntry:`n  import crewai; print(f'crewai   : {crewai.__version__}')`nexcept Exception as e:`n  print(f'crewai 載入失敗: {e!r}')"

. $Activate
Write-Host "[gov_agency] activated."
Write-Host "PYTHONPATH    = $env:PYTHONPATH"
Write-Host "TANG_GOV_ROOT = $env:TANG_GOV_ROOT"
Write-Host "提示：若 prompt 沒有 (gov_agency) 字樣，請改用：  . .\Enter-Agency.ps1"
