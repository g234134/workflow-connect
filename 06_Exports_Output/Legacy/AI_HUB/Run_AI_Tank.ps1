Write-Host "--- AI 戰車：全自動化流水線啟動 ---" -ForegroundColor Cyan
$PYTHON_EXEC = "python"
$BASE_DIR = "C:\Users\666LAG"

# 先切換到腳本所在的 C 槽目錄，確保 Python 讀取相對路徑 (config/) 時不會出錯
Push-Location $BASE_DIR

# 1. 數據清洗
Write-Host "[1/3] 啟動 V7 處理器..." -ForegroundColor Yellow
& $PYTHON_EXEC "scripts\08_數據處理器V7.py"

# 2. 路由決策
Write-Host "[2/3] 執行 Smart Router..." -ForegroundColor Yellow
& $PYTHON_EXEC "smart_router.py"

# 3. 執行主程式
Write-Host "[3/3] 啟動 AI 戰車主程式..." -ForegroundColor Green
& $PYTHON_EXEC "01_AI戰車主程式.py"

Pop-Location
Read-Host "任務完成！按 Enter 鍵關閉視窗..."
