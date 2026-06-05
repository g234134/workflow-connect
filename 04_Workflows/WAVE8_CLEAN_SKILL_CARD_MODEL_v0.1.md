# Wave 8 – CLEAN-SKILL-CARD 知識蒸餾模型（v0.1）

> **票號**：`CLEAN-SKILL-CARD-MODEL`  
> **性質**：spec / knowledge model（**知識資產規格，非 runtime contract**）  
> **受眾**：intake agent、orchestrator、operator、知識檢索系統設計者  
> **前置**：`WAVE6_CLEAN_PRODUCT_MATRIX_v0.1.md`、`WAVE6_CLEAN_DELIVERABLE_TEMPLATES_v0.1.md`、`WAVE7_CLEAN_ORCH_TASK_MODEL_v0.1.md`、`WAVE7_CLEAN_ORCH_TOOL_INTEGRATION_v0.1.md`、`WAVE8_CLEAN_ORDER_MODEL_v0.1.md`  
> **預期下游**：`WAVE8_CLEAN_RUN_SUMMARY_SCHEMA_v0.1.md`（run 摘要結構，本稿先引用預期結構）  
> **狀態**：**DRAFT-v0.1**

---

## 0. 文件目的

CLEAN 產品線（BASIC / ENRICH）已具備 intake → orchestrator → QA → 交付的完整流水線。本文定義 **CLEAN-SKILL-CARD** 模型，用於從「成功的清洗 run」中提煉可複用的經驗與模式，沉澱為知識資產。

**核心定位**：
- Skill Card 是**知識層**的摘要卡片，供未來 intake / orchestrator / operator 在相似 case 下**檢索參考**
- **不取代**正式產品規格（Wave 6/7/8 specs），不作為強制執行規則
- **不預設**底層檢索系統實作，僅定義邏輯欄位與引用契約

---

## 1. 什麼樣的 Run 可以升級為 Skill

並非所有完成的 run 都適合沉澱為 Skill Card。需同時滿足以下**准入條件**：

### 1.1 品質門檻（QA Status）

| 條件 | 要求 | 說明 |
|------|------|------|
| `qa_status` | `pass` 或 `pass_with_warnings` | M1/M2 無 P0 失敗；P1 僅警告不阻塞 |
| `completion_variant` | `completed` 或 `completed_with_failures` | 允許部分行 rejected，但核心模式有效 |
| 無嚴重合規問題 | 無 `PATH-LEAK`、`SCHEMA-VIOLATION` 等 P0 錯誤類別 | 確保 Skill 本身不傳播違規模式 |

### 1.2 可複用性門檻（Pattern Reusability）

| 條件 | 要求 | 說明 |
|------|------|------|
| 非一次性特例 | `applicable_scenarios[]` 至少涵蓋 2 個以上相似場景 | 排除極特殊資料畸形 case |
| 工具鏈穩定 | `used_tools[]` 皆為已發布版本（非實驗/臨時 patch） | 確保其他 agent 可重現 |
| 有明確成功信號 | `success_signals[]` 可觀測、可驗證 | 方便後續檢索時比對匹配度 |

### 1.3 資訊完整性門檻

| 條件 | 要求 |
|------|------|
| `evidence_refs[]` 非空 | 至少指向一個 run summary / report / artifact 邏輯引用 |
| `input_profile` 可描述 | 典型資料形態可被抽象描述（如「CSV 應用日誌」、「客戶地址表」） |

### 1.4 升級流程（建議）

```
Run 完成（S5 finalize）
    │
    ▼
[自動標記] ──▶ qa_status=pass ──▶ candidate_pool（等待人工複審）
    │
    ▼
[人工複審] ──▶ operator / CS 確認可複用性 ──▶ 產生 Skill Card（review_status=draft）
    │
    ▼
[知識策展] ──▶ 治理方批准 ──▶ review_status=approved ──▶ 進入檢索索引
```

**注意**：本稿僅定義 Skill Card **資料結構**，不涉及 candidate_pool 實作或自動升級 workflow。

---

## 2. CLEAN-SKILL-CARD 頂層欄位

### 2.1 欄位總覽

```json
{
  "skill_id": "skill-clean-basic-csv-logs-001",
  "title": "批量 CSV 應用日誌清洗：時間戳標準化 + 必填欄補全",
  "applicable_scenarios": ["application_log_csv", "structured_server_logs"],
  "product_sku_scope": "CLEAN-BASIC",
  "input_profile": { ... },
  "used_tools": ["CLEAN-CSV-TRANSFORM", "CLEAN-VALIDATE-SCHEMA", "CLEAN-QA-M1"],
  "key_patterns": [ ... ],
  "gotchas": [ ... ],
  "success_signals": [ ... ],
  "evidence_refs": [ ... ],
  "review_status": "approved",
  "metadata": { ... }
}
```

### 2.2 欄位詳細規格

#### `skill_id`（必填）

| 屬性 | 規格 |
|------|------|
| 類型 | string |
| 格式 | `skill-{product}-{domain}-{seq}` |
| 範例 | `skill-clean-basic-csv-logs-001`、`skill-clean-enrich-address-api-042` |
| 唯一性 | 全域唯一，建議以產生時 timestamp + 雜湊後綴確保 |

#### `title`（必填）

| 屬性 | 規格 |
|------|------|
| 類型 | string |
| 長度 | 建議 80 字元內 |
| 內容 | 簡潔描述本 Skill 解決的問題與核心手法 |
| 範例 | 「批量 CSV 應用日誌清洗：時間戳標準化 + 必填欄補全」 |

#### `applicable_scenarios[]`（必填）

| 屬性 | 規格 |
|------|------|
| 類型 | string[] |
| 用途 | 檢索標籤，描述本 Skill 適用的場景分類 |
| 建議值域 | `application_log_csv`、`structured_server_logs`、`customer_address_table`、`product_catalog_json`、`legacy_db_export`、`iot_sensor_logs`、`webhook_payload_logs` |
| 數量 | 建議 1–5 個，過多降低檢索精準度 |

#### `product_sku_scope`（必填）

| 屬性 | 規格 |
|------|------|
| 類型 | enum |
| 可選值 | `CLEAN-BASIC`、`CLEAN-ENRICH`、`both` |
| 說明 | 本 Skill 適用的產品包；`both` 表示模式可跨產品複用（如 schema 校驗邏輯） |

#### `input_profile`（必填）

描述「典型資料形態」，供 intake 比對相似度。

| 子欄位 | 類型 | 說明 |
|--------|------|------|
| `format` | string | `CSV`、`NDJSON`、`structured_log`、`JSON` |
| `encoding` | string | `UTF-8`、`ASCII` |
| `typical_size_range` | object | `{min_rows, max_rows, min_bytes, max_bytes}` |
| `schema_signature` | object | 關鍵欄位名稱與類型提示（非嚴格 schema） |
| `sample_fields` | string[] | 具代表性的欄位名稱清單（3–10 個） |
| `common_issues` | string[] | 此類資料常見的原始問題（如「時間戳格式混亂」、「欄位名大小寫不一致」） |

#### `used_tools[]`（必填）

對齊 `WAVE7_CLEAN_ORCH_TOOL_INTEGRATION_v0.1.md` 定義的 **CLEAN-* 工具類別**。

| 屬性 | 規格 |
|------|------|
| 類型 | string[] |
| 值域 | `CLEAN-INTAKE-GATE`、`CLEAN-SAMPLE-ANALYZE`、`CLEAN-CSV-TRANSFORM`、`CLEAN-VALIDATE-SCHEMA`、`CLEAN-ENVELOPE-WRITE`、`CLEAN-MANIFEST-WRITE`、`CLEAN-QA-M1`、`CLEAN-QA-M2`、`CLEAN-REPORT-BUILD`、`CLEAN-REPORT-RENDER`、`CLEAN-ARTIFACT-STORE`、... |
| 用途 | 明確本 Skill 依賴的工具鏈，供 orchestrator 評估可執行性 |

#### `key_patterns[]`（建議）

這類 case 常見的成功做法（heuristics / 最佳實踐）。

| 子欄位 | 類型 | 說明 |
|--------|------|------|
| `pattern_id` | string | 內部識別（如 `p-001`） |
| `title` | string | 簡短標題 |
| `description` | string | 詳細說明 |
| `applies_to_stage` | string | 對應 S0–S5 階段 |
| `tool_id` | string | 相關工具（可選） |

#### `gotchas[]`（建議）

常見坑 / 風險提示，供未來 operator 參考避開。

| 子欄位 | 類型 | 說明 |
|--------|------|------|
| `severity` | enum | `warning`、`error`、`info` |
| `title` | string | 風險標題 |
| `description` | string | 詳細說明 |
| `trigger_condition` | string | 何種情境下會觸發此風險 |
| `mitigation_hint` | string | 建議的規避或處理方式 |

#### `success_signals[]`（建議）

什麼結果代表這條路徑有效（可用於驗證後續應用是否成功）。

| 子欄位 | 類型 | 說明 |
|--------|------|------|
| `signal_id` | string | 內部識別 |
| `metric_name` | string | 指標名稱（對齊 `report.json` 欄位） |
| `threshold_operator` | enum | `>=`、`<=`、`==`、`in_range` |
| `threshold_value` | number / object | 門檻值（如 `95`、`{min: 90, max: 100}`） |
| `description` | string | 為何此指標代表成功 |

#### `evidence_refs[]`（必填）

指向 run summary / report / artifact 的**邏輯引用**（非絕對路徑）。

| 子欄位 | 類型 | 說明 |
|--------|------|------|
| `ref_type` | enum | `run_summary`、`report_json`、`report_md`、`manifest`、`sidecar_methodology` |
| `logical_uri` | string | 邏輯路徑，遵循 `w6://delivery/{job_id}/{kind}` 格式（見 `WAVE6_CLEAN_DELIVERABLE_TEMPLATES_v0.1.md` §2.3） |
| `snapshot_hint` | object | 關鍵數據快照（如 `accepted_units: 15000`、`qa_status: pass`） |
| `description` | string | 此證據支持 Skill 的哪個論點 |

#### `review_status`（必填）

| 屬性 | 規格 |
|------|------|
| 類型 | enum |
| 可選值 | `draft`（草稿）、`approved`（已批准）、`deprecated`（已棄用） |
| 轉換規則 | `draft` → `approved`（知識策展人批准）；`approved` → `deprecated`（發現更好替代或模式過時） |

#### `metadata`（建議）

| 子欄位 | 類型 | 說明 |
|--------|------|------|
| `created_at` | ISO-8601 | Skill Card 建立時間 |
| `created_by` | string | 建立者（agent / operator / system） |
| `approved_at` | ISO-8601 | 批准時間（若已批准） |
| `approved_by` | string | 批准者 |
| `version` | string | Skill Card 版本（如 `v0.1`） |
| `derived_from_job_id` | string | 來源 run 的 job_id |
| `supersedes` | string[] | 若本 Skill 取代舊版，列出舊 `skill_id` |
| `tags` | string[] | 額外標籤（如 `batch-processing`、`api-integration`、`time-series`） |

---

## 3. Skill Card 的使用方式

### 3.1 檢索觸發時機

| 使用方 | 觸發時機 | 檢索意圖 |
|--------|----------|----------|
| **intake** | S0 intake 階段，客戶需求初判後 | 「這種資料形態過去有成功案例嗎？」 |
| **orchestrator** | S1–S2 階段，規則配置前 | 「相似 case 用了什麼工具鏈？」 |
| **operator** | S4 QA 失敗或 S5 交付前 | 「這個 P1 警告過去怎麼處理的？」 |
| **CS** | 客戶詢問「過去有沒有做過類似資料？」 | 快速調用相關案例佐證 |

### 3.2 檢索匹配維度（建議）

檢索系統可基於以下維度計算相似度：

1. **產品對齊**：`product_sku_scope` 與當前 order/job 的 SKU 匹配
2. **場景對齊**：`applicable_scenarios[]` 與 intake 標記的資料類型標籤重疊度
3. **輸入形態相似度**：`input_profile` 的 `format`、`encoding`、`typical_size_range` 區間重疊
4. **問題模式相似度**：`input_profile.common_issues` 與當前資料的預檢問題列表重疊
5. **工具可執行性**：`used_tools[]` 是否在當前環境可用

### 3.3 使用原則（重要）

> **Skill Card 是參考，不是強制規則**

- **不取代正式 spec**：Wave 6/7/8 的產品規格、QA 規則、工具行為定義仍為權威
- **不強制執行**：orchestrator 可選擇採納或忽略 Skill Card 的建議
- **需人工確認**：涉及 `gotchas[]` 中的高風險項目時，建議 operator 人工確認
- **版本意識**：檢索時應優先 `review_status=approved` 且非 `deprecated` 的 Skill

### 3.4 反饋閉環（建議）

當 Skill Card 被檢索並應用後，建議記錄：

- `applied_to_job_id`：應用到哪個 job
- `application_result`：`succeeded`、`partial`、`failed`（相對於 `success_signals` 的達成度）
- `operator_feedback`：operator 的主觀評價（1–5 分或文字）

此反饋可用於未來 Skill Card 的策展與汰換。

---

## 4. 完整示例

### 4.1 示例一：CLEAN-BASIC – 批量應用日誌 / CSV 清洗

```json
{
  "skill_id": "skill-clean-basic-csv-logs-001",
  "title": "批量 CSV 應用日誌清洗：時間戳標準化 + 必填欄補全",
  "applicable_scenarios": [
    "application_log_csv",
    "structured_server_logs",
    "nginx_access_log_export"
  ],
  "product_sku_scope": "CLEAN-BASIC",
  "input_profile": {
    "format": "CSV",
    "encoding": "UTF-8",
    "typical_size_range": {
      "min_rows": 1000,
      "max_rows": 100000,
      "min_bytes": 10240,
      "max_bytes": 104857600
    },
    "schema_signature": {
      "required_fields": ["timestamp", "level", "message"],
      "optional_fields": ["user_id", "request_id", "duration_ms"]
    },
    "sample_fields": ["timestamp", "level", "message", "user_id", "request_id"],
    "common_issues": [
      "時間戳格式混亂（ISO-8601 / Unix ms / 自定義格式混用）",
      "欄位名大小寫不一致（Timestamp / timestamp / TIMESTAMP）",
      "缺失值以字串 'null' 或 'N/A' 標記而非空值",
      "CSV 含 BOM 頭導致欄位名解析異常"
    ]
  },
  "used_tools": [
    "CLEAN-INTAKE-GATE",
    "CLEAN-CSV-TRANSFORM",
    "CLEAN-VALIDATE-SCHEMA",
    "CLEAN-ENVELOPE-WRITE",
    "CLEAN-MANIFEST-WRITE",
    "CLEAN-QA-M1",
    "CLEAN-REPORT-BUILD",
    "CLEAN-ARTIFACT-STORE"
  ],
  "key_patterns": [
    {
      "pattern_id": "p-001",
      "title": "時間戳多格式自動偵測與標準化",
      "description": "優先嘗試 ISO-8601，其次 Unix ms，最後嘗試常見自定義格式（yyyy-MM-dd HH:mm:ss）。失敗時標記為 null，不阻塞流程。",
      "applies_to_stage": "S3",
      "tool_id": "CLEAN-CSV-TRANSFORM"
    },
    {
      "pattern_id": "p-002",
      "title": "欄位名大小寫統一為 snake_case",
      "description": "intake 階段即正規化欄位名，避免後續 schema 校驗失敗。",
      "applies_to_stage": "S0",
      "tool_id": "CLEAN-INTAKE-GATE"
    },
    {
      "pattern_id": "p-003",
      "title": "缺失值標準化為空字串而非 'null' 字面值",
      "description": "在 transform 階段統一替換常見缺失標記（'null', 'N/A', 'NULL', 'None'）為真正空值。",
      "applies_to_stage": "S3",
      "tool_id": "CLEAN-CSV-TRANSFORM"
    }
  ],
  "gotchas": [
    {
      "severity": "error",
      "title": "BOM 頭導致欄位名解析錯位",
      "description": "UTF-8 BOM 會讓第一個欄位名變成 '\ufefftimestamp'，導致 schema 校驗失敗。",
      "trigger_condition": "CSV 以 UTF-8 with BOM 編碼",
      "mitigation_hint": "intake 階段偵測 BOM 並 strip，或在 transform 階段處理。"
    },
    {
      "severity": "warning",
      "title": "超大 CSV（>1GB）可能觸發記憶體限制",
      "description": "BASIC 產品單文件上限 1GB，超過需走 batch partition。",
      "trigger_condition": "input_profile.typical_size_range.max_bytes > 1073741824",
      "mitigation_hint": "建議客戶先分割檔案，或升級至含 partition 邏輯的企業方案。"
    },
    {
      "severity": "warning",
      "title": "時間戳時區資訊缺失",
      "description": "原始資料常缺失時區，統一視為 UTC 可能導致語意錯誤。",
      "trigger_condition": "時間戳不含 +0800 或 Z 後綴",
      "mitigation_hint": "在 cleaning_profile 中明確指定預設時區，或於 intake 與客戶確認。"
    }
  ],
  "success_signals": [
    {
      "signal_id": "sig-001",
      "metric_name": "accepted_units_rate",
      "threshold_operator": ">=",
      "threshold_value": 95,
      "description": "95% 以上行通過清洗，表示格式標準化邏輯有效"
    },
    {
      "signal_id": "sig-002",
      "metric_name": "schema_violations.count",
      "threshold_operator": "<=",
      "threshold_value": 0,
      "description": "無 schema 違規，表示欄位映射正確"
    },
    {
      "signal_id": "sig-003",
      "metric_name": "processing_time_ms_per_1000_rows",
      "threshold_operator": "<=",
      "threshold_value": 5000,
      "description": "每千行處理時間 < 5 秒，表示無異常效能問題"
    }
  ],
  "evidence_refs": [
    {
      "ref_type": "report_json",
      "logical_uri": "w6://delivery/w7-basic-acme-20250604-001/report_json",
      "snapshot_hint": {
        "accepted_units": 87500,
        "rejected_units": 420,
        "qa_status": "pass",
        "schema_violations": 0
      },
      "description": "原始成功案例的完整報告，驗證上述 success_signals"
    },
    {
      "ref_type": "sidecar_methodology",
      "logical_uri": "w6://delivery/w7-basic-acme-20250604-001/sidecars/cleaning_rules_applied.md",
      "snapshot_hint": {
        "rules_applied": ["timestamp_normalize", "snake_case_fields", "null_literal_clean"]
      },
      "description": "記錄了本 Skill 關鍵 pattern 的實際應用規則"
    }
  ],
  "review_status": "approved",
  "metadata": {
    "created_at": "2026-06-04T10:00:00Z",
    "created_by": "operator-chen",
    "approved_at": "2026-06-04T14:30:00Z",
    "approved_by": "knowledge-curator-wang",
    "version": "v0.1",
    "derived_from_job_id": "w7-basic-acme-20250604-001",
    "tags": ["batch-processing", "timestamp-cleaning", "csv", "logs"]
  }
}
```

---

### 4.2 示例二：CLEAN-ENRICH – 客戶地址標準化 + 外部 API enrich

```json
{
  "skill_id": "skill-clean-enrich-address-api-042",
  "title": "客戶地址標準化 + 外部 API Enrich：郵遞區號補全與座標地理編碼",
  "applicable_scenarios": [
    "customer_address_table",
    "crm_contact_export",
    "shipping_address_list"
  ],
  "product_sku_scope": "CLEAN-ENRICH",
  "input_profile": {
    "format": "CSV",
    "encoding": "UTF-8",
    "typical_size_range": {
      "min_rows": 500,
      "max_rows": 50000,
      "min_bytes": 5120,
      "max_bytes": 52428800
    },
    "schema_signature": {
      "required_fields": ["address_line1", "city"],
      "optional_fields": ["address_line2", "state", "postal_code", "country", "customer_name"]
    },
    "sample_fields": ["customer_id", "address_line1", "address_line2", "city", "state", "postal_code", "country"],
    "common_issues": [
      "地址欄位混用全半形標點（，, ／ /）",
      "城市名稱非標準（如 '台北市' vs '台北' vs 'Taipei'）",
      "郵遞區號缺失或格式錯誤",
      "state/province 欄位與 city 混淆（如把 '台中市' 寫在 state）",
      "country 欄位缺失（預設為當地語系但 enrich API 需明確國碼）"
    ]
  },
  "used_tools": [
    "CLEAN-INTAKE-GATE",
    "CLEAN-SAMPLE-ANALYZE",
    "CLEAN-CSV-TRANSFORM",
    "CLEAN-VALIDATE-SCHEMA",
    "CLEAN-ENVELOPE-WRITE",
    "CLEAN-MANIFEST-WRITE",
    "CLEAN-QA-M1",
    "CLEAN-QA-M2",
    "CLEAN-M2-SAMPLING-PLAN",
    "CLEAN-REPORT-BUILD",
    "CLEAN-REPORT-RENDER",
    "CLEAN-ARTIFACT-STORE"
  ],
  "key_patterns": [
    {
      "pattern_id": "p-101",
      "title": "S1 預檢抽樣驗證地址多樣性",
      "description": "ENRICH 需確保地址樣本涵蓋不同城市與格式，避免 enrich API 在某類地址上系統性失敗。建議 sample 中各主要城市至少 5 筆。",
      "applies_to_stage": "S1",
      "tool_id": "CLEAN-SAMPLE-ANALYZE"
    },
    {
      "pattern_id": "p-102",
      "title": "地址欄位合併策略：line1 + line2 + city + state",
      "description": "多數 enrich API 接受單一 address 字串，建議將多欄位合併為完整地址後發送，回傳結果再拆解回填。",
      "applies_to_stage": "S2",
      "tool_id": "CLEAN-CSV-TRANSFORM"
    },
    {
      "pattern_id": "p-103",
      "title": "Enrich 失敗降級：保留原始值，標記 _enrich_failed",
      "description": "外部 API 可能因地址模糊或服務異常失敗，不阻塞整批，單行標記失敗並繼續。",
      "applies_to_stage": "S3",
      "tool_id": "CLEAN-CSV-TRANSFORM"
    },
    {
      "pattern_id": "p-104",
      "title": "M2 抽樣驗證 enrich 品質：郵遞區號格式與座標合理性",
      "description": "ENRICH 必須啟用 M2 抽樣，驗證 enrich 回傳結果（如 postal_code 是否為 5 碼、lat/lng 是否在合理範圍）。",
      "applies_to_stage": "S4",
      "tool_id": "CLEAN-QA-M2"
    }
  ],
  "gotchas": [
    {
      "severity": "error",
      "title": "PII 外發 enrich API 需 DPA 簽署",
      "description": "客戶地址屬個資，發送至第三方 enrich API 需確認已簽署資料處理協議（DPA）。",
      "trigger_condition": "enrich_plan_ref 指向外部地址標準化服務",
      "mitigation_hint": "intake 階段檢查客戶合約是否含 DPA 條款，或改用內部離線地址庫。"
    },
    {
      "severity": "error",
      "title": "ENRICH 規模上限 10 萬行 / 500MB",
      "description": "超過此上限可能觸發 enrich API 速率限制或記憶體問題。",
      "trigger_condition": "input_profile.typical_size_range.max_rows > 100000",
      "mitigation_hint": "建議分批處理或申請提高 API 配額。"
    },
    {
      "severity": "warning",
      "title": "Enrich API 成本波動",
      "description": "按呼叫計費的 enrich API 在大批量時可能產生意外費用。",
      "trigger_condition": "批次行數 > 10000 且使用第三方付費 API",
      "mitigation_hint": "建議先抽樣 100 筆測試成本與成功率，或與客戶預先確認費用上限。"
    },
    {
      "severity": "warning",
      "title": "Fuzzy match 去重存在假陽性風險",
      "description": "ENRICH 的去重依賴 fuzzy match，可能誤判相似地址為同一筆（如 '中山路 1 號' vs '中山路 1-1 號'）。",
      "trigger_condition": "啟用 dedup_policy.fuzzy_match",
      "mitigation_hint": "關鍵業務去重建議人工複核，或調高 similarity 門檻。"
    },
    {
      "severity": "info",
      "title": "預設時區與國碼可能影響 enrich 結果",
      "description": "部分 enrich API 依賴國碼決定地址解析策略，預設值可能導致誤判。",
      "trigger_condition": "country 欄位缺失或為 'TW' / 'CN' 等模糊值",
      "mitigation_hint": "在 enrich_plan_ref 中明確指定 default_country_code。"
    }
  ],
  "success_signals": [
    {
      "signal_id": "sig-101",
      "metric_name": "enrich_coverage_pct",
      "threshold_operator": ">=",
      "threshold_value": 95,
      "description": "95% 以上行成功 enrich，表示地址格式與 API 相容性良好"
    },
    {
      "signal_id": "sig-102",
      "metric_name": "enrich_fallback_rate",
      "threshold_operator": "<=",
      "threshold_value": 5,
      "description": "降級率低於 5%，表示 enrich 邏輯穩定"
    },
    {
      "signal_id": "sig-103",
      "metric_name": "m2_sample_pass_rate",
      "threshold_operator": ">=",
      "threshold_value": 98,
      "description": "M2 抽樣驗證通過率 98% 以上，表示 enrich 結果品質達標"
    },
    {
      "signal_id": "sig-104",
      "metric_name": "postal_code_validity_rate",
      "threshold_operator": ">=",
      "threshold_value": 99,
      "description": "郵遞區號格式有效性 99% 以上（依據當地郵編規則）"
    }
  ],
  "evidence_refs": [
    {
      "ref_type": "report_json",
      "logical_uri": "w6://delivery/w7-enrich-retailcorp-20250604-042/report_json",
      "snapshot_hint": {
        "accepted_units": 42300,
        "rejected_units": 180,
        "enrich_coverage_pct": 96.5,
        "enrich_fallback_rate": 3.2,
        "qa_status": "pass"
      },
      "description": "原始成功案例報告，展示 ENRICH 指標達標情況"
    },
    {
      "ref_type": "manifest",
      "logical_uri": "w6://delivery/w7-enrich-retailcorp-20250604-042/manifest",
      "snapshot_hint": {
        "enrich_fields_added": ["_enrich_postal_code_std", "_enrich_lat", "_enrich_lng", "_enrich_address_full"],
        "has_enrichment": true
      },
      "description": "manifest 顯示 enrich 欄位正確注入"
    },
    {
      "ref_type": "sidecar_methodology",
      "logical_uri": "w6://delivery/w7-enrich-retailcorp-20250604-042/sidecars/enrichment_algorithms_v0.1.md",
      "snapshot_hint": {
        "api_used": "address-standardization-v2",
        "fallback_strategy": "preserve_original_mark_failed"
      },
      "description": "enrich 演算法說明文件，記錄本 Skill 的 API 選型與降級策略"
    }
  ],
  "review_status": "approved",
  "metadata": {
    "created_at": "2026-06-04T11:00:00Z",
    "created_by": "agent-enrich-specialist",
    "approved_at": "2026-06-04T16:00:00Z",
    "approved_by": "knowledge-curator-wang",
    "version": "v0.1",
    "derived_from_job_id": "w7-enrich-retailcorp-20250604-042",
    "tags": ["address-cleaning", "external-api", "enrichment", "geocoding", "pii-aware"]
  }
}
```

---

## 5. 與上下游文件的對齊

### 5.1 上游引用（本稿依賴）

| 文件 | 引用內容 |
|------|----------|
| `WAVE6_CLEAN_PRODUCT_MATRIX_v0.1.md` | `product_sku_scope` 值域（CLEAN-BASIC / CLEAN-ENRICH）、輸入輸出規格 |
| `WAVE6_CLEAN_DELIVERABLE_TEMPLATES_v0.1.md` | `w6://delivery/{job_id}/{kind}` 邏輯 URI 格式、`report.json` 欄位名稱 |
| `WAVE7_CLEAN_ORCH_TASK_MODEL_v0.1.md` | S0–S5 階段對齊、`orchestrator` 使用時機 |
| `WAVE7_CLEAN_ORCH_TOOL_INTEGRATION_v0.1.md` | `used_tools[]` 值域（CLEAN-* 工具類別） |
| `WAVE8_CLEAN_ORDER_MODEL_v0.1.md` | milestone 概念、Order 狀態（間接參考，Skill Card 非商務層） |

### 5.2 下游預期（引用本稿）

| 預期文件 | 對齊內容 |
|----------|----------|
| `WAVE8_CLEAN_RUN_SUMMARY_SCHEMA_v0.1.md` | run 摘要欄位應涵蓋 Skill Card 所需的 `success_signals[]` 指標 |
| （未來）Skill Registry 實作 | 可選擇性實作本稿定義的欄位結構 |
| （未來）intake 相似度匹配模組 | 可基於 `input_profile` 設計匹配演算法 |

---

## 6. 非目標（本稿 v0.1）

| 項 | 說明 |
|----|------|
| 檢索系統實作 | 本稿僅定義 Skill Card 結構，不涉及搜尋引擎、向量資料庫、相似度演算法 |
| Skill Card 自動生成 workflow | 從 run → candidate → draft → approved 的流程自動化另票 |
| 版本控制機制 | `supersedes` 欄位預留，但差異比對、合併衝突處理另票 |
| 多語言 Skill Card | 本稿範例為繁體中文，國際化結構另票 |
| 量化相似度評分 | `input_profile` 的匹配演算法（如 embedding similarity）另票 |

---

## 7. 版本歷史

| 版本 | 日期 | 變更 |
|------|------|------|
| v0.1 | 2026-06-04 | 初始草稿：Skill Card 頂層欄位、升級規則、使用方式、BASIC/ENRICH 雙示例 |

**下一版預期**：
- 補充 `WAVE8_CLEAN_RUN_SUMMARY_SCHEMA_v0.1.md` 發布後的欄位對齊
- 增加 Skill Card 檢索 API 草案（如需）
- 補充更多產品線（如未來的 CLEAN-ENTERPRISE）適用欄位

---

*Wave 8 CLEAN-SKILL-CARD Knowledge Model · `04_Workflows/WAVE8_CLEAN_SKILL_CARD_MODEL_v0.1.md`*
