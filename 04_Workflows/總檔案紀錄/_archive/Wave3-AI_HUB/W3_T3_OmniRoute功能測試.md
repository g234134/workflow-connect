# WAVE 3 — T3: OmniRoute Compression 功能性測試

> 測試時間: $(date '+%Y-%m-%d %H:%M')

---

## 測試一：API 連通性

| 測試項目 | 結果 |
|---------|------|
| GET /v1/models | ✅ **成功 (HTTP 200)** — 返回模型列表（含 Groq/Nvidia/OpenRouter） |
| POST /v1/chat/completions | ⚠️ **返回 HTML** ("API is running") 而非 JSON，chat 端點可能未正確路由 |
| Dashboard :3000 | ❌ **無法連接** — 可能 dashboard 未啟動 |

## 發現

| ID | 嚴重度 | 描述 |
|----|--------|------|
| W3-008 | 🟠 MAJOR | POST /v1/chat/completions 回傳 HTML 而非 JSON，無法確認壓縮管線是否生效 |
| W3-009 | 🟠 MAJOR | Dashboard (:3000) 無法連接，無法確認壓縮設定狀態 |

## 建議

1. 檢查 OmniRoute 的 routing/upstream 配置
2. 確認 dashboard 服務是否獨立啟動
3. 待修復後重新測試 compression pipeline 效果
