clear
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "   🚀 666lag Agent 基地全自動健康檢查啟動" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan

# --- 第一關：底層環境與 GPU ---
Write-Host "`n[1/4] 正在檢查底層環境與 GPU..." -ForegroundColor Yellow
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
python -c "import torch; print(f'✅ Torch 版本: {torch.__version__}'); print(f'✅ CUDA 是否可用: {torch.cuda.is_available()}')" 2>$null

# --- 第二關：橋接層健康度 (FastAPI) ---
Write-Host "`n[2/4] 正在檢查 FastAPI (Port 8001)..." -ForegroundColor Yellow
try {
    $apiResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8001/" -Method Get -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✅ FastAPI 正常運作: $($apiResponse.msg)" -ForegroundColor Green
} catch {
    Write-Host "❌ 無法連接到 FastAPI (8001)。請確認 python main.py 是否已啟動。" -ForegroundColor Red
}

# --- 第三關：生產工具狀態 (SD Forge API) ---
Write-Host "`n[3/4] 正在檢查 SD Forge 引擎 (Port 7860)..." -ForegroundColor Yellow
try {
    $sdResponse = Invoke-RestMethod -Uri "http://127.0.0.1:7860/sdapi/v1/options" -Method Get -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✅ SD Forge API 已開啟！模型準備就緒。" -ForegroundColor Green
} catch {
    Write-Host "❌ 無法連接到 SD Forge (7860)。請檢查黑視窗是否開著。" -ForegroundColor Red
}

# --- 第四關：傳送門狀態 (ngrok) ---
Write-Host "`n[4/4] 正在檢查 ngrok 外網傳送門..." -ForegroundColor Yellow
try {
    $ngrokStatus = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -Method Get -TimeoutSec 2 -ErrorAction Stop
    $publicUrl = $ngrokStatus.tunnels[0].public_url
    Write-Host "✅ 外網網址已就緒: $publicUrl" -ForegroundColor Green
} catch {
    Write-Host "❌ ngrok 尚未啟動。" -ForegroundColor Red
}

Write-Host "`n===============================================" -ForegroundColor Cyan
Write-Host "   檢查結束！" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
