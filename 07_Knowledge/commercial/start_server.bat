@echo off
REM ═══════════════════════════════════════════════
REM  戰車數據清洗 — 一鍵啟動腳本
REM  啟動 Webhook 收單 API (port 9000)
REM ═══════════════════════════════════════════════

setlocal
cd /d "D:\大唐三省六部\07_Knowledge\commercial"

echo.
echo  ╔══════════════════════════════════════╗
echo  ║   戰車數據清洗 — 收單服務啟動中...   ║
echo  ╚══════════════════════════════════════╝
echo.

REM 檢查 Python
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 找不到 Python，請先安裝 Python 3.11+
    pause
    exit /b 1
)

REM 安裝依賴（如果需要）
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [INFO] 首次執行，安裝 FastAPI + uvicorn...
    pip install fastapi uvicorn python-multipart --quiet
)

echo [OK] 依賴就緒
echo [INFO] 啟動收單 API...
echo [INFO] API Docs: http://127.0.0.1:9000/docs
echo [INFO] 按 Ctrl+C 停止
echo.

python webhook_server.py --port 9000

endlocal
