@echo off
REM ═══════════════════════════════════════════════
REM  戰車數據清洗 — 一鍵啟動所有服務
REM ═══════════════════════════════════════════════

setlocal
cd /d "D:\大唐三省六部\07_Knowledge\commercial"

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   戰車數據清洗 — 營運系統啟動中...        ║
echo  ╚══════════════════════════════════════════╝
echo.

REM 啟動 Webhook API (port 9000)
echo [1/2] 啟動收單 API (port 9000)...
start "Tank API" cmd /c "C:\Users\666LAG\crew_tank\Scripts\python.exe webhook_server.py --port 9000"
timeout /t 2 >nul

REM 啟動 Telegram Bot
echo [2/2] 啟動 Telegram 收單機器人...
start "Tank Bot" cmd /c "C:\Users\666LAG\crew_tank\Scripts\python.exe telegram_order_bot.py"

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   ✅ 所有服務已啟動！                     ║
echo  ╠══════════════════════════════════════════╣
echo  ║   📋 API Docs:  http://127.0.0.1:9000/docs ║
echo  ║   🤖 Telegram Bot: 已上線                 ║
echo  ║   📁 訂單目錄: orders/                    ║
echo  ║   📁 上傳目錄: uploads/                   ║
echo  ╚══════════════════════════════════════════╝
echo.
echo  按任意鍵關閉此視窗（服務會繼續運行）
pause >nul

endlocal
