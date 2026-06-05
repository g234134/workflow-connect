clear
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "   🚀 666lag AI 基地：一鍵全系統啟動" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan

# 1. 啟動 SD Forge 引擎 (在獨立視窗)
Write-Host "👉 正在啟動 SD Forge 引擎..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\666LAG\AI_Project\stable-diffusion-webui-forge'; .\webui-user.bat"

# 2. 啟動 FastAPI Agent (在獨立視窗)
Write-Host "👉 正在啟動 FastAPI Agent..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\dev\agency-agents'; . .\.venv\Scripts\activate; python main.py"

# 3. 啟動 ngrok 傳送門 (在獨立視窗)
Write-Host "👉 正在啟動 ngrok 傳送門..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\dev\agency-agents'; .\ngrok.exe http 8001"

Write-Host "`n✅ 三大系統啟動指令已發送！" -ForegroundColor Green
Write-Host "請檢查彈出的三個視窗是否正常運作。" -ForegroundColor Gray
Write-Host "===============================================" -ForegroundColor Cyan
