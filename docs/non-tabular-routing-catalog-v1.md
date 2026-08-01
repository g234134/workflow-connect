# Non-Tabular Routing Catalog v1

> **Cross-ref（Catalog + Selector SSOT）**：`docs/tool-catalog-and-selector-contract-v1.md` — Non-Tabular `tool_id`、NT catalog JSON、`planned_tools[]` 形状与四轨分轨；本档 routing 字段 **不改 YAML**，符号名映射见 W9-T3。  
> **Ticket**: W9-T1 · non-tabular-routing-catalog-v1  
> **Type**: Architecture / Structure (spec + skeleton)  
> **Date**: 2026-06-10  
> **Status**: v1.0 design draft  
> **Upstream**: `docs/non-tabular-shadow-flow-blueprint-v1.md` (W8-T4) · `docs/intake-routing-catalog-v1.md` (W2-T1)

---

## §1 目的與範圍

### 1.1 定位

本文檔定義 **non-tabular** 家族（`non-tabular.*`）的 routing catalog v1，作為 intake routing system 的擴展規格：

- **與 Tabular routing catalog 的關係**：平行家族，共用 intake router 架構，但擁有獨立的 `task_type` namespace 與 routing 欄位設計
- **實作階段**：本票僅 spec + catalog skeleton，**不**含 executable glue 或 Python 實作
- **Wave 9 目標**：為 W9-T2~T9 提供 routing catalog 基礎結構

### 1.2 兩類典型案型（v1 焦點）

| 案型代碼 | 名稱 | 說明 | 上游來源 |
|----------|------|------|----------|
| **NT-A** | Document Processing | 混合格式文件夾（PDF, DOCX, PNG, JPG）的文字提取與結構化 | W8-T4 §2 Case Type A |
| **NT-B** | Log Analysis | 系統日誌（非結構化、時間序列）的解析與異常標記 | W8-T4 §2 Case Type B |

---

## §2 Routing 欄位規格

### 2.1 共通欄位（All non-tabular task_types）

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `family` | string | 是 | 固定值 `"non-tabular"` |
| `task_type` | string | 是 | 格式：`non-tabular.{domain}.{action}`，如 `non-tabular.document.clean_and_annotate` |
| `case_profile` | string | 是 | 案型描述符，如 `"docu-corp"`、`"log-analytics-co"` |
| `intake_schema` | string | 是 | `"schema-free"` · `"semi-structured"` · `"structured"` |
| `target_tools` | array[string] | 是 | Symbolic tool names（暫時為符號名稱，非實際模組路徑） |

### 2.2 NT-A（Document Processing）專屬欄位

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `content_type` | string | 是 | 文件類型標記，如 `"mixed_documents"` |
| `document_count_hint` | string | 否 | 數量區間，如 `"<100"`、`"100-1000"`、`">1000"` |
| `requires_ocr` | boolean | 否 | 是否含圖片需 OCR |
| `schema_flexibility` | string | 否 | `"high"` · `"medium"` · `"low"` |

### 2.3 NT-B（Log Analysis）專屬欄位

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `content_type` | string | 是 | 內容類型標記，如 `"server_logs"` |
| `volume_estimate` | string | 否 | 資料量區間，如 `"<1GB"`、`"1-10GB"`、`">10GB"` |
| `time_range_hint` | string | 否 | 時間範圍描述，如 `"2026-05-01 to 2026-05-31"` |
| `log_format` | array[string] | 否 | 格式標記，如 `["text", "json", "csv"]` |

---

## §3 案型詳細規格

### 3.1 NT-A: Document Processing

**案型描述**：客戶上傳混合格式文件夾，需提取文字、分類、生成結構化摘要。

**典型 intake 欄位**：

```yaml
client_ref: "docu-corp"
case_id: "docu-2026-0001"
data_source: "raw/documents/"  # mixed formats
document_count: 50
schema_hint: "schema-free"
sensitivity: "internal"
```

**Routing 欄位示例**：

```yaml
family: "non-tabular"
task_type: "non-tabular.document.clean_and_annotate"
case_profile: "docu-corp"
intake_schema: "schema-free"
target_tools:
  - "validate.content_accessible"      # Symbolic
  - "extract.text_content"             # Symbolic
  - "extract.metadata"                 # Symbolic
  - "bundle.multi_format"              # Symbolic
content_type: "mixed_documents"
document_count_hint: "<100"
requires_ocr: true
schema_flexibility: "high"
```

**預期產出**：
- `cleaned/extracted_texts/*.txt`
- `cleaned/metadata.json` (per-file attributes)
- `reports/extraction_stats.json`

**Example fixture**: `cases/docu-corp/2026-0001`.

### 3.2 NT-B: Log Analysis

**案型描述**：客戶上傳系統日誌，需解析、異常標記、生成摘要報告。

**典型 intake 欄位**：

```yaml
client_ref: "log-analytics-co"
case_id: "logs-2026-0001"
data_source: "raw/server_logs/*.log"
volume_gb: 2
time_range: "2026-05-01 to 2026-05-31"
schema_hint: "semi-structured"
```

**Routing 欄位示例**：

```yaml
family: "non-tabular"
task_type: "non-tabular.log.parse_and_summarize"
case_profile: "log-analytics-co"
intake_schema: "semi-structured"
target_tools:
  - "validate.content_accessible"      # Symbolic
  - "parse.log_structure"              # Symbolic
  - "analyze.anomaly_patterns"         # Symbolic
  - "bundle.multi_format"              # Symbolic
content_type: "server_logs"
volume_estimate: "1-10GB"
time_range_hint: "2026-05-01 to 2026-05-31"
log_format: ["text", "json"]
```

**預期產出**：
- `cleaned/parsed_logs.jsonl`
- `reports/anomaly_flags.json`
- `reports/summary.md`

**Example fixture**: `cases/log-analytics-co/2026-0001`.

---

## §4 與 Tabular Routing Catalog 的差異

| 維度 | Tabular Routing | Non-Tabular Routing |
|------|-----------------|---------------------|
| **核心資料單位** | Row (CSV 行) | Document / File / Content chunk |
| **Schema 處理** | Fixed columns (預定義) | Schema-free / flexible / semi-structured |
| **Task Type 前綴** | `tabular.*` | `non-tabular.*` |
| **Gate 指標** | `removal_ratio` (行刪除比例) | `extraction_coverage`, `text_quality_score` |
| **Validation 焦點** | Column eligibility, Row count | Content accessibility, Format compliance |
| **Cleaning 模型** | Filter, Map, Transform rows | Extract, Parse, Enrich content |
| **Bundle 內容** | Single CSV + report | Multi-format manifest + metadata |
| **Tool Catalog** | `tabular_tool_catalog_v1.json` | `non_tabular_routing_catalog_v1.yaml` (本檔) |

---

## §5 Catalog YAML 結構

### 5.1 頂層結構

```yaml
version: "1.0"
family: "non-tabular"
generated_at: "2026-06-10"

# Task type entries
task_types:
  - task_type: "non-tabular.document.clean_and_annotate"
    ...
  - task_type: "non-tabular.log.parse_and_summarize"
    ...

# Risk tier definitions (reference)
risk_tiers:
  low:
    description: "Known format, small volume, internal sensitivity"
  medium:
    description: "Mixed formats, medium volume, needs review"
  high:
    description: "Unknown format, large volume, confidential"
```

### 5.2 Entry 欄位清單

每個 `task_type` entry 包含：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `task_type` | string | Full task type identifier |
| `description` | string | 人讀描述 |
| `case_profile` | string | 預設案型 profile |
| `intake_schema` | string | Schema 類型 |
| `intake_pattern` | object | Intake 欄位 pattern（regex/enum） |
| `risk_tier` | string | `low` · `medium` · `high` |
| `default_tools` | array[string] | Symbolic tool pipeline |
| `content_type` | string | 內容類型標記 |
| `domain_hints` | object | 領域專屬提示欄位 |
| `notes` | string | 設計備註 |

---

## §6 下游銜接

### 6.1 Wave 9 後續票

| 票號 | 目的 | 依賴本檔 |
|------|------|----------|
| W9-T2 | Decision rules v2 擴展 non-tabular logic | Catalog 定義的 `task_type` / `risk_tier` |
| W9-T3 | Tool catalog skeleton | Catalog 定義的 `default_tools` |
| W9-T4 | Glue layer route planner | Catalog 定義的 routing 欄位 |
| W9-T5/T6 | Fixtures | Catalog 定義的案型結構 |

### 6.2 與既有系統的邊界

- **不**修改 `routing/intake_routing_catalog_v1.yaml`（Tabular 專用）
- **不**修改 `routing/intake_decision_rules_v1.py` 或 `v2.py` 的現有邏輯
- **不**建立 `cases/docu-corp/` 或 `cases/log-analytics-co/`（設計階段僅概念案型）

---

## §7 附錄

### A. Symbolic Tool Names 對照（設計階段）

| Symbolic Name | 預計用途 | 對照 Tabular |
|---------------|----------|--------------|
| `validate.content_accessible` | 檢查文件可讀性 | `validate.eligibility` |
| `extract.text_content` | 文字提取（含 OCR） | `clean.phase_demo` |
| `extract.metadata` | 元數據提取 | — |
| `parse.log_structure` | 日誌結構解析 | — |
| `analyze.anomaly_patterns` | 異常模式分析 | — |
| `transform.normalize` | 編碼/格式標準化 | — |
| `analyze.content_stats` | 內容品質統計 | `cleaning_stats.json` 生成 |
| `bundle.multi_format` | 多格式打包 | `export.delivery_bundle` |

### B. 文件索引

| 文件 | 用途 |
|------|------|
| `docs/non-tabular-shadow-flow-blueprint-v1.md` | W8-T4 上游藍圖 |
| `routing/non_tabular_routing_catalog_v1.yaml` | 機器 readable catalog（本檔實例） |
| `docs/intake-routing-catalog-v1.md` | Tabular routing 規格（W2-T1） |

---

*Non-Tabular Routing Catalog v1 · W9-T1 · 2026-06-10 · Architect + Scribe*
