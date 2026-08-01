# 戰車數據清洗 — 營運手冊

## 快速開始

### 一鍵啟動
```batch
D:\大唐三省六部\07_Knowledge\commercial\start_all.bat
```

### 手動啟動
```bash
# 1. 啟動 Webhook API
cd D:\大唐三省六部\07_Knowledge\commercial
crew_tank\Scripts\python.exe webhook_server.py --port 9000

# 2. 啟動 Telegram Bot（另一個終端）
crew_tank\Scripts\python.exe telegram_order_bot.py
```

---

## 系統架構

```
客戶端
  │
  ├─→ Telegram Bot ─→ 訂單佇列 ─→ 清洗管線 ─→ 交付
  │
  └─→ Web API (9000) ─→ 訂單佇列 ─→ 清洗管線 ─→ 交付
```

### 收單管道
| 管道 | 用途 | 狀態 |
|------|------|------|
| Telegram Bot | 客戶直接傳檔案 | ✅ 已上線 |
| Web API (port 9000) | 網頁表單提交 | ✅ 運作中 |
| Landing Page | 官網展示 | ✅ 已部署 |

### 訂單處理流程
1. 客戶透過 Telegram 或 Web 上傳檔案
2. 系統自動建立訂單（`orders/` 目錄）
3. 營運方收到 Telegram 通知
4. 執行數據清洗管線
5. 交付乾淨檔案 + 清洗報告

---

## 日常作業

### 查看訂單
```bash
python ops_dashboard.py orders
```

### 處理待辦訂單
```bash
python ops_dashboard.py process
```

### 查看系統狀態
```bash
python ops_dashboard.py status
```

### 生成營運報告
```bash
python ops_dashboard.py report
```

---

## 定價方案

| 方案 | 價格 | 交付時間 | 檔案數 | 筆數上限 |
|------|------|----------|--------|----------|
| 基礎版 | $999 | 24hr | 1 | 5,000 |
| 專業版 | $2,999 | 12hr | 3 | 50,000 |
| 企業版 | 客製 | 依約 | 不限 | 不限 |

---

## 檔案結構

```
07_Knowledge/commercial/
├── landing_page.html      # 官網首頁
├── order_form.html        # 訂單表單
├── webhook_server.py      # Webhook API 服務
├── telegram_order_bot.py  # Telegram 收單機器人
├── ops_dashboard.py       # 營運管理面板
├── start_all.bat          # 一鍵啟動腳本
├── start_server.bat       # 僅啟動 API
├── orders/                # 訂單 JSON 檔案
├── uploads/               # 客戶上傳的原始檔案
├── processed/             # 已處理的訂單
├── reports/               # 營運報告
└── service_pricing.md     # 定價文件
```

---

## 監控與告警

### Telegram 通知
- 新訂單建立 → 營運方收到通知
- 訂單處理完成 → 客戶收到通知

### 健康檢查
```bash
curl http://127.0.0.1:9000/api/health
```

---

## 疑難排解

### API 無法啟動
```bash
# 檢查 port 是否被佔用
netstat -an | grep 9000

# 重新安裝依賴
pip install fastapi uvicorn python-multipart
```

### Telegram Bot 無回應
```bash
# 測試 Bot 連線
python telegram_order_bot.py --test

# 檢查 .env 設定
cat D:\Hermes\.env | grep TELEGRAM
```

---

## 下一步

1. **安裝 ngrok** — 讓 Web API 可從外網存取
2. **整合 Stripe** — 接入線上付款
3. **建立官網** — 將 landing_page.html 部署到公網
4. **啟動廣告** — Facebook/Google 小額投放
