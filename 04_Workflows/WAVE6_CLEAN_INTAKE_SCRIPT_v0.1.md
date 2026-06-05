# Wave 6 – CLEAN Intake 對話腳本（v0.1）

> **票號**：`WAVE6-CLEAN-INTAKE-SCRIPT`  
> **性質**：spec / 對話設計  
> **範圍**：定義 CLEAN-BASIC / CLEAN-ENRICH 兩產品的 intake 對話流程、核心問題集、推斷策略與 JSON 輸出格式  
> **前置**：`WAVE6_CLEAN_PRODUCT_MATRIX_v0.1.md`、`WAVE6_CLEAN_DELIVERABLE_TEMPLATES_v0.1.md`  
> **不做**：實際 LLM prompt engineering、前端 UI 實作、自動推斷演算法開發

---

## 0. 產品速查

| 產品代碼 | 定位 | 核心差異 | 適用場景 |
|----------|------|----------|----------|
| `CLEAN-BASIC` | 基礎清洗 | Schema 驗證、格式標準化、缺失值標記，無外部 API 調用 | 日誌格式統一、CSV 基礎校驗、快速質檢 |
| `CLEAN-ENRICH` | 增強清洗 | 含 BASIC 全部功能 + 外部 API enrich、去重、語義標籤、質量評分 | 地址標準化、客戶數據補全、多語言內容處理 |

**Intake 目標**：在 5-10 輪對話內，收集足夠資訊以生成結構化 `intake_record`，供 orchestrator 建立 job。

---

## 1. CLEAN-BASIC Intake 問卷

### 1.1 核心問題集（8 題）

| 題號 | 問題 | 目的 | 推斷策略 | 必填 |
|------|------|------|----------|------|
| B-1 | 「請問您的數據來源是？（例如：應用日誌、CRM 匯出、感測器數據、其他）」 | 確定數據性質與 schema 複雜度 | 🧠 **可推斷**：從文件副檔名 + 欄位名稱特徵推測 | 是 |
| B-2 | 「數據文件格式是？（CSV、JSON Lines、NDJSON、其他）」 | 決定 parser 與編碼處理策略 | 🔍 **明問**：格式影響下游整個 pipeline，不可猜錯 | 是 |
| B-3 | 「文件編碼確認為 UTF-8？是否有 BOM？」 | 避免編碼錯誤導致亂碼 | 🧠 **可推斷**：試讀前 1KB 偵測，但須用戶確認 | 是 |
| B-4 | 「請提供 schema 描述或欄位說明文件（或指向 schema registry 的 ID）」 | 建立欄位驗證規則 | 🔍 **明問**：schema_ref 為必需輸入，無法推斷 | 是 |
| B-5 | 「數據量大約多少？（行數、文件大小、是否壓縮）」 | 決定資源配置與 batch 策略 | 🧠 **可推斷**：實際掃描文件統計，但需用戶預估時程 | 是 |
| B-6 | 「數據中是否包含敏感欄位（PII）？如姓名、電話、地址、身份證號等」 | 決定是否需要 PII mask 與 DPA 流程 | 🔍 **明問**：涉及合規，必須明確用戶聲明 | 是 |
| B-7 | 「是否有必填欄位或特定業務規則需要驗證？（例如：訂單金額必須 > 0）」 | 識別 BASIC 不承諾範圍，提前設定預期 | 🔍 **明問**：業務規則需用戶明確說明 | 否 |
| B-8 | 「期望的交付時程？（標準 3 工作日 / 加急 1 工作日）」 | 資源排程與 SLA 對齊 | 🔍 **明問**：商務約定，必須明問 | 是 |

### 1.2 推斷 vs 明問對照（BASIC）

| 欄位 | 推斷來源 | 推斷置信度 | 失敗 fallback |
|------|----------|------------|---------------|
| `data_source_type` | 文件路徑關鍵字 + 欄位名稱（log/timestamp → 日誌；customer/email → CRM） | 75% | 明問 B-1 |
| `file_format` | 副檔名（.csv, .json, .jsonl, .gz） | 90% | 明問 B-2 |
| `encoding` | 文件頭 BOM 偵測 + chardet | 85% | 明問 B-3 |
| `schema_ref` | 無 | N/A | **必須明問** B-4 |
| `row_count_estimate` | 掃描行數 / 檔案大小 ÷ 平均行長 | 95% | 用戶預估值 |
| `contains_pii` | 欄位名稱比對（name/phone/address/ssn/email） | 60% | **必須明問** B-6 |
| `has_business_rules` | 用戶自陳 | N/A | 明問 B-7 |
| `deadline_utc` | 用戶輸入轉換 | N/A | **必須明問** B-8 |

### 1.3 風險警示問句（自動觸發）

當系統偵測到以下情境，自動追加警示說明：

| 情境 | 觸發條件 | 系統回應 |
|------|----------|----------|
| 大文件 | `file_size > 1GB` | 「檔案超過 1GB，將啟用 batch partition，處理時間可能延長 2-4 小時」 |
| 非 UTF-8 | `encoding ∉ {UTF-8, ASCII}` | 「偵測到非 UTF-8 編碼，可能產生亂碼，建議先轉碼」 |
| PII 高風險 | `contains_pii=true` 且無 DPA 記錄 | 「數據含 PII，需先完成 DPA 簽署方可進入 enrich 階段（如後續升級 ENRICH）」 |
| 業務規則 | `has_business_rules=true` | 「BASIC 僅做格式校驗，業務規則正確性需由上游保證」 |

---

## 2. CLEAN-ENRICH Intake 問卷

### 2.1 核心問題集（10 題）

ENRICH 繼承 BASIC 全部問題（B-1 ~ B-8），並追加以下 2 題：

| 題號 | 問題 | 目的 | 推斷策略 | 必填 |
|------|------|------|----------|------|
| E-1 | 「需要調用哪些 enrich API？（地址標準化、公司名補全、手機號歸屬地、語言檢測、其他）」 | 建立 `enrich_plan_ref` | 🔍 **明問**：ENRICH 核心差異，必須明確 | 是 |
| E-2 | 「對外部 API 失敗的容忍度？（嚴格：失敗即停 / 寬鬆：允許部分失敗並標記）」 | 設定 enrich fallback 策略 | 🧠 **可推斷**：預設 `lenient`，但關鍵業務場景須明問 | 否 |
| E-3 | 「去重策略？（精確匹配欄位 / Fuzzy match / 無需去重）」 | 決定 dedup 演算法與成本 | 🔍 **明問**：影響處理時間與計價 | 否 |
| E-4 | 「數據是否含多語言內容？主要語言分布是？」 | 預估 LLM 調用成本與處理時間 | 🧠 **可推斷**：抽樣 100 行檢測 | 否 |
| E-5 | 「enrich API 的金鑰與配額是否已就緒？」 | 驗證前置依賴 | 🔍 **明問**：ENRICH 必需，必須確認 | 是 |

> **注**：E-1 ~ E-5 為追加題，BASIC 的 B-1 ~ B-8 仍全部適用。

### 2.2 ENRICH 特有欄位推斷策略

| 欄位 | 推斷來源 | 推斷置信度 | 失敗 fallback |
|------|----------|------------|---------------|
| `enrich_plan_ref` | 無 | N/A | **必須明問** E-1 |
| `enrich_fallback_policy` | 用戶歷史偏好 / 預設 `lenient` | 50% | 明問 E-2 |
| `dedup_strategy` | 無 | N/A | **建議明問** E-3 |
| `language_distribution` | langdetect 抽樣 | 80% | 用戶自陳 |
| `api_key_ready` | 無 | N/A | **必須明問** E-5 |

### 2.3 ENRICH 風險警示問句

| 情境 | 觸發條件 | 系統回應 |
|------|----------|----------|
| 規模超過 enrich 限制 | `row_count > 100k` | 「ENRICH 建議單文件 ≤10 萬行，當前規模建議分批或改用 BASIC」 |
| PII 外發風險 | `contains_pii=true` + enrich 含地址/電話 API | 「⚠️ 地址/手機號將外發至第三方 API，請確認已簽署 DPA」 |
| 成本波動風險 | `row_count > 50k` + 多 enrich API | 「預估 enrich API 調用費用可能較高，建議先抽樣 1000 行測試」 |
| API 可用性 | `api_key_ready=false` | 「ENRICH 需有效 API Key，請先完成金鑰配置」 |

---

## 3. 對話 → Intake JSON 欄位對照表

### 3.1 頂層結構

```json
{
  "intake_id": "uuid",
  "product_sku": "CLEAN-BASIC | CLEAN-ENRICH | CLEAN-ENRICH-LLM",
  "intake_status": "in_progress | complete | needs_clarification",
  "created_at": "ISO-8601",
  "completed_at": "ISO-8601 | null",
  "dialogue_turns": 7,
  
  "data_profile": { /* §3.2 */ },
  "schema_definition": { /* §3.3 */ },
  "security_compliance": { /* §3.4 */ },
  "enrich_configuration": { /* §3.5 — 僅 ENRICH */ },
  "scheduling": { /* §3.6 */ },
  "inferred_flags": { /* §3.7 */ },
  
  "user_explicit_answers": [ /* 記錄明問題的答案 */ ],
  "system_inferred_values": [ /* 記錄推斷值與置信度 */ ]
}
```

### 3.2 data_profile（數據輪廓）

| JSON 欄位 | 來源問題 | 值類型 | 推斷/明問 |
|-----------|----------|--------|-----------|
| `data_source_type` | B-1 | enum: log/crm/sensor/other | 🧠 推斷 |
| `file_format` | B-2 | enum: csv/ndjson/jsonl | 🔍 明問 |
| `encoding` | B-3 | enum: utf-8/utf-8-bom/ascii | 🧠 推斷 |
| `compression` | B-5 | enum: none/gzip/zstd | 🧠 推斷 |
| `file_size_bytes` | B-5 | int | 🧠 推斷 |
| `row_count_estimate` | B-5 | int | 🧠 推斷 |
| `has_header_row` | 系統偵測 | bool | 🧠 推斷 |
| `avg_row_size_bytes` | 計算 | int | 🧠 推斷 |

### 3.3 schema_definition（Schema 定義）

| JSON 欄位 | 來源問題 | 值類型 | 推斷/明問 |
|-----------|----------|--------|-----------|
| `schema_ref` | B-4 | string | 🔍 明問 |
| `schema_registry_id` | B-4 | string | 🔍 明問 |
| `embedded_schema` | B-4 | object | 🔍 明問 |
| `record_id_field` | 系統推斷 | string | 🧠 推斷 |
| `required_fields[]` | B-7 | array<string> | 🔍 明問 |
| `pii_fields[]` | B-6 | array<string> | 🔍 明問 |

### 3.4 security_compliance（安全與合規）

| JSON 欄位 | 來源問題 | 值類型 | 推斷/明問 |
|-----------|----------|--------|-----------|
| `contains_pii` | B-6 | bool | 🔍 明問 |
| `pii_types[]` | B-6 | array<enum> | 🔍 明問 |
| `dpa_signed` | 系統查詢 | bool | 🧠 推斷 |
| `encryption_required` | B-6 | bool | 🔍 明問 |
| `business_rules[]` | B-7 | array<object> | 🔍 明問 |
| `user_acknowledged_limitations` | 結束確認 | bool | 🔍 明問 |

### 3.5 enrich_configuration（ENRICH 特有）

| JSON 欄位 | 來源問題 | 值類型 | 推斷/明問 |
|-----------|----------|--------|-----------|
| `enrich_plan_ref` | E-1 | string | 🔍 明問 |
| `enrich_apis[]` | E-1 | array<enum> | 🔍 明問 |
| `api_key_status` | E-5 | enum: ready/pending/missing | 🔍 明問 |
| `fallback_policy` | E-2 | enum: strict/lenient | 🧠 推斷 |
| `dedup_strategy` | E-3 | enum: exact/fuzzy/none | 🔍 明問 |
| `dedup_key_fields[]` | E-3 | array<string> | 🔍 明問 |
| `language_distribution` | E-4 | object | 🧠 推斷 |
| `enrich_coverage_threshold` | 預設 | float | 🧠 預設 0.95 |

### 3.6 scheduling（排程）

| JSON 欄位 | 來源問題 | 值類型 | 推斷/明問 |
|-----------|----------|--------|-----------|
| `deadline_utc` | B-8 | ISO-8601 | 🔍 明問 |
| `priority` | B-8 | enum: standard/expedite | 🔍 明問 |
| `estimated_processing_time` | 計算 | string | 🧠 推斷 |
| `queue_position_hint` | 計算 | int | 🧠 推斷 |

### 3.7 inferred_flags（推斷標記）

```json
{
  "inferred_flags": {
    "data_source_type": {"value": "log", "confidence": 0.75, "source": "path_keyword"},
    "file_format": {"value": "csv", "confidence": 0.90, "source": "extension"},
    "encoding": {"value": "utf-8", "confidence": 0.85, "source": "bom_detection"},
    "language_distribution": {"value": {"zh": 0.8, "en": 0.2}, "confidence": 0.80, "source": "sample_100"}
  }
}
```

---

## 4. 對話範例

### 4.1 CLEAN-BASIC 對話範例

> **場景**：用戶有應用日誌 CSV 需清洗，無 PII，3 日後需要

---

**系統**：您好，我是 CLEAN 數據清洗服務助手。請問您需要哪種清洗服務？
- 1. 基礎清洗（BASIC）：格式標準化、Schema 驗證
- 2. 增強清洗（ENRICH）：含地址補全、去重、語義標籤

**用戶**：選 1，基礎清洗就好

**系統**：收到。請問您的數據來源是？（例如：應用日誌、CRM 匯出、感測器數據）

**用戶**：應用日誌，我們後端產生的

**系統**：了解。請上傳您的數據文件（或直接提供文件路徑）。

*[用戶上傳 `app_logs_202506.csv.gz`]*

**系統**：檔案已接收。我偵測到：
- 格式：CSV（壓縮 gzip）
- 編碼：UTF-8
- 估計行數：約 50,000 行
- 檔案大小：2.3 MB

請確認以上資訊是否正確？

**用戶**：正確

**系統**：請問您是否已有 schema 描述文件？或者我可以從 CSV 表頭自動推斷？

**用戶**：從表頭推斷就好，標準日誌格式

**系統**：好的。數據中是否包含敏感欄位（PII），例如：用戶姓名、電話、地址、身份證號？

**用戶**：沒有，只有 timestamp、level、message、request_id

**系統**：收到。最後一題：期望的交付時程？
- 標準：3 工作日
- 加急：1 工作日（費用 +50%）

**用戶**：標準，本週五前給我

**系統**：確認訂單摘要：

| 項目 | 內容 |
|------|------|
| 產品 | CLEAN-BASIC |
| 數據 | 應用日誌 CSV，50,000 行，UTF-8 |
| PII | 無 |
| Schema | 自動推斷（timestamp, level, message, request_id）|
| 交付 | 2025-06-06（標準）|
| 預估計價 | 50 U（$50）|

請問確認無誤即可建立工單？

**用戶**：確認

**系統**：工單已建立，ID: `CLEAN-BASIC-20250604-a1b2c3d4`。您可隨時輸入「狀態」查詢進度。

---

### 4.2 CLEAN-ENRICH 對話範例

> **場景**：用戶有客戶資料 CSV 需地址標準化 + 去重，含電話號碼（PII），已簽 DPA

---

**系統**：您好，我是 CLEAN 數據清洗服務助手。請問您需要哪種清洗服務？
- 1. 基礎清洗（BASIC）
- 2. 增強清洗（ENRICH）

**用戶**：選 2，我們客戶資料需要地址標準化

**系統**：收到。請上傳您的數據文件。

*[用戶上傳 `customers_may.csv`]*

**系統**：檔案偵測結果：
- 格式：CSV
- 編碼：UTF-8
- 行數：約 12,000 行
- 欄位：customer_id, name, phone, address_raw, city, signup_date

⚠️ 偵測到可能含 PII（name, phone, address）。請問數據是否包含個人識別資訊？

**用戶**：有，但已簽 DPA

**系統**：DPA 記錄已確認。現在詢問 enrich 需求：

**E-1** 您需要調用哪些 enrich API？
- [x] 地址標準化（地址轉標準格式 + 經緯度）
- [ ] 公司名補全
- [ ] 手機號歸屬地
- [ ] 語言檢測
- [ ] 其他：___

**用戶**：地址標準化就好

**系統**：**E-3** 去重策略？
- A. 精確匹配 customer_id（推薦）
- B. Fuzzy match name + phone（較慢，可能有誤判）
- C. 無需去重

**用戶**：選 A，用 customer_id

**系統**：**E-5** 請確認 enrich API 金鑰狀態：
- 地址標準化 API：✅ 已就緒（配額剩餘 45,000 次/月）

**用戶**：OK

**系統**：**E-2** 對於外部 API 失敗的容忍度？
- 嚴格：任一失敗即停止整個工單
- 寬鬆：允許部分失敗，失敗欄位留空並標記（推薦）

**用戶**：寬鬆就好

**系統**：最後，期望交付時程？
- 標準：3 工作日
- 加急：1 工作日

**用戶**：標準

**系統**：⚠️ **風險提示**：
- 您的數據含地址與電話，將外發至第三方 API 進行標準化
- DPA 已簽署，符合合規要求
- 預估 enrich API 調用：12,000 次，費用約 $12

確認訂單摘要：

| 項目 | 內容 |
|------|------|
| 產品 | CLEAN-ENRICH |
| 數據 | 客戶資料 CSV，12,000 行 |
| PII | 是（name, phone, address）|
| DPA | ✅ 已簽署 |
| Enrich | 地址標準化 |
| 去重 | 精確匹配 customer_id |
| Fallback | 寬鬆（標記失敗）|
| 交付 | 標準 3 工作日 |
| 預估計價 | 120 U + $12 API 費 |

請問確認無誤即可建立工單？

**用戶**：確認

**系統**：工單已建立，ID: `CLEAN-ENRICH-20250604-e5f6g7h8`。地址標準化預計在清洗階段 2/4 執行，您可輸入「狀態」追蹤進度。

---

## 5. 輸出 Intake JSON 範例

### 5.1 BASIC Case JSON

```json
{
  "intake_id": "c1b2a3d4-5678-90ab-cdef-1234567890ab",
  "product_sku": "CLEAN-BASIC",
  "intake_status": "complete",
  "created_at": "2025-06-04T09:15:30Z",
  "completed_at": "2025-06-04T09:18:45Z",
  "dialogue_turns": 7,
  
  "data_profile": {
    "data_source_type": "log",
    "file_format": "csv",
    "compression": "gzip",
    "encoding": "utf-8",
    "file_size_bytes": 2411724,
    "row_count_estimate": 50000,
    "has_header_row": true,
    "avg_row_size_bytes": 48
  },
  
  "schema_definition": {
    "schema_ref": "auto_inferred://app_logs_standard",
    "record_id_field": "request_id",
    "required_fields": ["timestamp", "level", "message"],
    "pii_fields": []
  },
  
  "security_compliance": {
    "contains_pii": false,
    "pii_types": [],
    "dpa_signed": false,
    "encryption_required": false,
    "business_rules": [],
    "user_acknowledged_limitations": true
  },
  
  "enrich_configuration": null,
  
  "scheduling": {
    "deadline_utc": "2025-06-06T23:59:59Z",
    "priority": "standard",
    "estimated_processing_time": "45 minutes",
    "queue_position_hint": 12
  },
  
  "inferred_flags": {
    "data_source_type": {"value": "log", "confidence": 0.90, "source": "path_keyword+field_names"},
    "file_format": {"value": "csv", "confidence": 0.95, "source": "extension"},
    "encoding": {"value": "utf-8", "confidence": 0.90, "source": "bom_detection"},
    "row_count_estimate": {"value": 50000, "confidence": 0.95, "source": "file_scan"}
  },
  
  "user_explicit_answers": [
    {"question_id": "B-2", "question": "文件格式確認", "answer": "csv", "inferred": false},
    {"question_id": "B-6", "question": "是否含PII", "answer": "否", "inferred": false},
    {"question_id": "B-8", "question": "交付時程", "answer": "標準-3工作日", "inferred": false}
  ],
  
  "system_inferred_values": [
    {"field": "file_format", "value": "csv", "confidence": 0.95, "method": "extension_detection"},
    {"field": "encoding", "value": "utf-8", "confidence": 0.90, "method": "bom_detection"},
    {"field": "row_count_estimate", "value": 50000, "confidence": 0.95, "method": "line_count_scan"}
  ]
}
```

### 5.2 ENRICH Case JSON

```json
{
  "intake_id": "e5f6g7h8-1234-5678-90ab-cdef12345678",
  "product_sku": "CLEAN-ENRICH",
  "intake_status": "complete",
  "created_at": "2025-06-04T10:22:15Z",
  "completed_at": "2025-06-04T10:28:33Z",
  "dialogue_turns": 9,
  
  "data_profile": {
    "data_source_type": "crm",
    "file_format": "csv",
    "compression": "none",
    "encoding": "utf-8",
    "file_size_bytes": 1843200,
    "row_count_estimate": 12000,
    "has_header_row": true,
    "avg_row_size_bytes": 153
  },
  
  "schema_definition": {
    "schema_ref": "auto_inferred://customer_csv",
    "record_id_field": "customer_id",
    "required_fields": ["customer_id", "name", "address_raw"],
    "pii_fields": ["name", "phone", "address_raw"]
  },
  
  "security_compliance": {
    "contains_pii": true,
    "pii_types": ["name", "phone", "address"],
    "dpa_signed": true,
    "dpa_reference": "DPA-2025-0342",
    "encryption_required": false,
    "business_rules": [],
    "user_acknowledged_limitations": true,
    "user_acknowledged_pii_external": true
  },
  
  "enrich_configuration": {
    "enrich_plan_ref": "enrich_plan://address_std_v1",
    "enrich_apis": ["address_standardization"],
    "api_key_status": "ready",
    "api_quota_remaining": 45000,
    "fallback_policy": "lenient",
    "dedup_strategy": "exact",
    "dedup_key_fields": ["customer_id"],
    "language_distribution": {"zh": 0.85, "en": 0.15},
    "enrich_coverage_threshold": 0.95
  },
  
  "scheduling": {
    "deadline_utc": "2025-06-09T23:59:59Z",
    "priority": "standard",
    "estimated_processing_time": "2.5 hours",
    "queue_position_hint": 8
  },
  
  "inferred_flags": {
    "data_source_type": {"value": "crm", "confidence": 0.80, "source": "field_names"},
    "file_format": {"value": "csv", "confidence": 0.95, "source": "extension"},
    "encoding": {"value": "utf-8", "confidence": 0.90, "source": "bom_detection"},
    "language_distribution": {"value": {"zh": 0.85, "en": 0.15}, "confidence": 0.80, "source": "sample_100"}
  },
  
  "user_explicit_answers": [
    {"question_id": "B-6", "question": "是否含PII", "answer": "是", "inferred": false},
    {"question_id": "E-1", "question": "Enrich API 選擇", "answer": "address_standardization", "inferred": false},
    {"question_id": "E-2", "question": "Fallback 策略", "answer": "lenient", "inferred": false},
    {"question_id": "E-3", "question": "去重策略", "answer": "exact_match_customer_id", "inferred": false},
    {"question_id": "E-5", "question": "API Key 狀態", "answer": "ready", "inferred": false}
  ],
  
  "system_inferred_values": [
    {"field": "data_source_type", "value": "crm", "confidence": 0.80, "method": "field_name_heuristic"},
    {"field": "language_distribution", "value": {"zh": 0.85, "en": 0.15}, "confidence": 0.80, "method": "langdetect_sample_100"}
  ],
  
  "risk_disclosures": [
    {
      "type": "pii_external_api",
      "severity": "warning",
      "message": "地址與電話將外發至第三方 API",
      "mitigation": "DPA 已簽署",
      "user_acknowledged": true
    },
    {
      "type": "cost_estimate",
      "severity": "info",
      "api_calls": 12000,
      "estimated_api_cost_usd": 12.00,
      "user_acknowledged": true
    }
  ]
}
```

---

## 6. 實作指引（給開發團隊）

### 6.1 對話管理

- **回合限制**：建議上限 15 回合，超過仍未收集必要欄位時轉人工
- **狀態機**：`greeting` → `product_selection` → `file_upload` → `basic_questions` → `enrich_questions` (if ENRICH) → `risk_disclosure` → `confirmation` → `complete`
- **上下文保留**：每回合更新 `intake_status`，中斷後可從 `in_progress` 恢復

### 6.2 推斷引擎優先順序

1. **高置信度（≥90%）**：自動採用，不問用戶（如 file_format from extension）
2. **中置信度（70-89%）**：主動確認「我偵測到 X，請問正確嗎？」
3. **低置信度（<70%）**：直接明問，不猜測

### 6.3 校驗規則

| 階段 | 校驗項 | 失敗處理 |
|------|--------|----------|
| Intake | `schema_ref` 必須存在 | 阻塞，要求補充 |
| Intake | `contains_pii` 必須明問確認 | 阻塞，不可僅靠推斷 |
| Intake | ENRICH 必須 `api_key_ready=true` | 阻塞，轉金鑰配置流程 |
| Pre-job | 文件實際掃描驗證 `row_count_estimate` | 偏差 >20% 時重新估價 |

### 6.4 與下游 Orchestrator 對接

Intake 完成後生成 `intake_record`，由 `intake → orchestrator` 轉換器映射為 `job_input`：

```python
# 虛擬碼
job_input = {
    "product_sku": intake_record["product_sku"],
    "source_path": upload_path,
    "schema_ref": intake_record["schema_definition"]["schema_ref"],
    "enrich_plan_ref": intake_record.get("enrich_configuration", {}).get("enrich_plan_ref"),
    "priority": intake_record["scheduling"]["priority"],
    "deadline_utc": intake_record["scheduling"]["deadline_utc"],
    "metadata": {
        "intake_id": intake_record["intake_id"],
        "contains_pii": intake_record["security_compliance"]["contains_pii"],
        "dpa_signed": intake_record["security_compliance"].get("dpa_signed", False)
    }
}
```

---

## 7. 版本與演進

| 版本 | 日期 | 變更 |
|------|------|------|
| v0.1 | 2026-06-04 | 初始草案：BASIC/ENRICH 問卷各 8-10 題、推斷/明問標註、JSON 對照表、對話範例 |

**下一版預期內容**：
- 增加 `CLEAN-ENTERPRISE` 專屬問題（KMS 加密、SLA 承諾）
- 補充多語言對話範例（英文、日文）
- 推斷引擎 confidence threshold 調校數據
- 與 Wave 7 orchestrator 實際對接欄位對照

---

*Wave 6 CLEAN Intake Script · `04_Workflows/WAVE6_CLEAN_INTAKE_SCRIPT_v0.1.md`*
