#Requires -Version 5.1
# Enter-Main.ps1 — 啟動主艙 (gov_main)，驗證 pydantic 並設定跨艙 PYTHONPATH
# 用法：
#   .\Enter-Main.ps1            ← 僅做驗證 (activation 退出後失效)
#   . .\Enter-Main.ps1          ← 點源後 activation 持續至本 shell 結束 (建議互動式用此)
$ErrorActionPreference = 'Stop'

$Root     = Split-Path -Parent $PSScriptRoot
$VenvDir  = Join-Path $Root '01_Environments\python_venvs\gov_main'
$Activate = Join-Path $VenvDir 'Scripts\Activate.ps1'
$VenvPy   = Join-Path $VenvDir 'Scripts\python.exe'

if (-not (Test-Path $VenvPy)) {
    Write-Error "[gov_main] venv 尚未建立: $VenvDir`n請先執行 Bootstrap (建立雙艙)。"
    return
}

# 跨艙路徑保護：讓 gov_paths.py 與既有 Agents/Workflows 都可被引用
$ProjectRoot = $Root
$AgentsCore  = Join-Path $Root '02_Agents_Core'
$Workflows   = Join-Path $Root '04_Workflows'
$env:PYTHONPATH = "$ProjectRoot;$AgentsCore;$Workflows"
$env:PYTHONUTF8 = '1'
$env:TANG_GOV_ROOT = $Root

. (Join-Path $PSScriptRoot '_Load-TangEnv.ps1')
Initialize-TangEnv -Root $Root -Label 'gov_main' | Out-Null

Write-Host '──────── gov_main ────────'
& $VenvPy -c "import sys, pydantic; print(f'Python   : {sys.version.split()[0]}'); print(f'pydantic : {pydantic.VERSION}'); print(f'sys.path[0:3]: {sys.path[:3]}')"

# 嘗試激活 (僅在被點源時持續生效)
. $Activate
Write-Host "[gov_main] activated."
Write-Host "PYTHONPATH    = $env:PYTHONPATH"
Write-Host "TANG_GOV_ROOT = $env:TANG_GOV_ROOT"
Write-Host "提示：若 prompt 沒有 (gov_main) 字樣，請改用：  . .\Enter-Main.ps1"
