# CrewAI + 本機 Ollama：一鍵執行（雙擊或在 Cursor「執行工作」呼叫）
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$TangRoot = 'D:\大唐三省六部'
$EnterAgency = Join-Path $TangRoot '04_Workflows\Enter-Agency.ps1'

if (-not (Test-Path -LiteralPath $EnterAgency)) {
    Write-Host "[錯誤] 找不到副艙進入腳本：$EnterAgency" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot 'main.py'))) {
    Write-Host "[錯誤] 找不到 main.py：$ProjectRoot" -ForegroundColor Red
    exit 1
}

. $EnterAgency
Set-Location -LiteralPath $ProjectRoot
Write-Host "[INFO] 目錄：$ProjectRoot" -ForegroundColor Cyan
Write-Host "[INFO] 執行 python main.py ...`n" -ForegroundColor Cyan

python .\main.py
$code = $LASTEXITCODE
Write-Host "`n[INFO] 結束代碼：$code" -ForegroundColor $(if ($code -eq 0) { 'Green' } else { 'Red' })
Write-Host "[INFO] 結果檔：$(Join-Path $ProjectRoot 'output.txt')" -ForegroundColor Cyan
exit $code
