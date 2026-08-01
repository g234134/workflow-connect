# Non-Tabular Shadow Flow Blueprint v1

> **Ticket**: W8-T4 · non-tabular-shadow-flow-blueprint-v1  
> **Type**: Architecture Design (shadow only — no production behavior)  
> **Date**: 2026-06-10  
> **Status**: design draft v1.0  
> **Upstream**: `docs/ninety-five-percent-automation-blueprint-v2.md` · `docs/agent-standard-line-v1-summary.md` · `docs/agent-standard-line-governance-view-v2.md` · `docs/skill-cards-v2.md`

---

## §1 目的與範圍

### 1.1 什麼是 Non-Tabular

**Non-Tabular** 指非結構化或半結構化資料案型，與現有 **Tabular MVP**（CSV/表格清洗）形成互補：

| 維度 | Tabular MVP | Non-Tabular Shadow |
|------|-------------|-------------------|
| **Input Schema** | CSV with known columns (`Phase`, `名稱`, `之前`, `現在`) | Schema-free or flexible schema |
| **Data Types** | Structured text/numbers | Documents, images, audio, JSON blobs, logs |
| **Cleaning Model** | Row filtering, column mapping | Content extraction, transformation, enrichment |
| **Validation** | Row count, removal ratio | Content quality, format compliance, semantic checks |
| **Delivery** | Cleaned CSV + report | Processed assets + metadata + manifest |

### 1.2 本藍圖範圍（v1 Shadow）

**In Scope（設計層 only）**:
- Non-Tabular 案型的 intake decision rules 擴展設計
- S1–S15 流程對照表（哪些沿用 Tabular、哪些需重新設計）
- Governance 與 HITL 策略繼承方案
- Wave 9 建議票列表（實作規劃）

**Explicitly Out of Scope**:
- ❌ 不改任何 Tabular 主鏈程式碼（`scripts/run_mvp_mainline_regression.py` 等）
- ❌ 不進 production 行為（無實際執行路徑）
- ❌ 不新建 cases/ 目錄（僅設計階段概念案型）
- ❌ 不修改 `routing/intake_decision_rules_v1.py`（保留 v1 allowlist）

### 1.3 與 Tabular 主鏈關係

```
┌─────────────────────────────────────────────────────────────────┐
│                    Intake Router (W4-T1 glue)                    │
│                         ┌─────────┐                              │
│              ┌─────────▶│ Tabular │──────────┐                   │
│              │          │ Family  │          │                   │
│   Case In    │          └─────────┘          │  Tool Layer        │
│   ───────────┤                                ▼                   │
│              │          ┌─────────┐    ┌──────────┐               │
│              └─────────▶│Non-Tab  │───▶│ Shadow   │ (v1 design)   │
│                         │ Family  │    │ Design   │               │
│                         └─────────┘    └──────────┘               │
│                           (v1: design only)                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## §2 典型 Non-Tabular 案型（未來目標示例）

> 以下為 Wave 9+ 潛在實作目標，**v1 shadow 僅設計、不實作**

### Case Type A: Document Processing Pipeline

**案型描述**: 客戶上傳混合格式文件夾（PDF, DOCX, PNG, JPG），需提取文字、分類、生成結構化摘要。

| 欄位 | 示例值 |
|------|--------|
| `client_ref` | `docu-corp` |
| `case_id` | `docu-2026-0001` |
| `data_source` | `raw/documents/` (mixed formats) |
| `document_count` | ~50 files |
| `schema_hint` | `schema-free` |
| `sensitivity` | `internal` |

**預期產出**:
- `cleaned/extracted_texts/*.txt`
- `cleaned/metadata.json` (per-file attributes)
- `reports/extraction_stats.json`

### Case Type B: Log Analysis & Anomaly Detection

**案型描述**: 客戶上傳系統日誌（非結構化、時間序列、無固定 schema），需解析、異常標記、生成摘要報告。

| 欄位 | 示例值 |
|------|--------|
| `client_ref` | `log-analytics-co` |
| `case_id` | `logs-2026-0001` |
| `data_source` | `raw/server_logs/*.log` |
| `volume_gb` | ~2 GB |
| `time_range` | `2026-05-01 to 2026-05-31` |
| `schema_hint` | `semi-structured` |

**預期產出**:
- `cleaned/parsed_logs.jsonl`
- `reports/anomaly_flags.json`
- `reports/summary.md`

---

## §3 Shadow Flow 結構：S1–S15 對照表

### 3.1 步驟映射總覽

| Step | 名稱 | Tabular v2 狀態 | Non-Tabular Shadow v1 | 設計策略 |
|------|------|-----------------|----------------------|----------|
| S1 | Intake Upload | HITL (human-only CLI) | **沿用設計** | 同 Tabular：`new_cleaning_case.py` 可擴展 |
| S2 | Index Refresh | auto | **沿用設計** | 需擴展 `cases/index.json` schema 支援 |
| S3 | Decision Evaluate | auto (W5-T1 rules) | **需擴展設計** | New rules for `non-tabular.*` family |
| S4 | Checkpoint A | HITL live (W6-T5) | **沿用治理模式** | Same human-in-the-loop pattern |
| S5 | Route Planning | auto (W4-T1 glue) | **需新設計** | `plan_non_tabular_route()` shadow spec |
| S6 | Tool Selection | auto (selector) | **需新設計** | Non-tabular tool catalog v1 |
| S7 | Gate Validation | auto (run path) | **需新設計** | Content-based gates (vs row-count) |
| S8 | Cleaning Execution | auto (executor) | **需新設計** | Content processors (vs CSV cleaners) |
| S9 | Outbox Write | auto | **沿用設計** | Same outbox pattern |
| S10 | Bundle Build | auto (demo run) | **需新設計** | Multi-format bundling |
| S11 | Output Guard | auto live read | **需新設計** | Content quality metrics |
| S12 | Checkpoint B | HITL live (W6-T6) | **沿用治理模式** | Same HITL pattern |
| S13 | Delivery Approval | HITL (manual) | **沿用設計** | Same signoff pattern |
| S14 | Ledger Update | auto partial | **沿用設計** | Same ledger pattern |
| S15 | Client Notify | experimental (W7-T3) | **沿用治理模式** | Same controlled notify pattern |

### 3.2 詳細設計對照

#### S3: Decision Evaluate — 擴展設計

**Tabular v1 Rules** (from `intake_decision_rules_v1.py`):
- `task_type` in `tabular.*` family → allow
- `case_profile` in `{demo_phase, sampleco}` → `needs_review` or `auto_accept`

**Non-Tabular Shadow 設計**:

```yaml
# Conceptual decision rules for non-tabular family
task_type_allowlist:
  - non-tabular.document.extract        # Document Type A
  - non-tabular.log.analyze            # Log Type B
  - non-tabular.generic.transform      # Generic catch-all

decision_factors:
  - schema_hint: {schema-free, semi-structured, structured}
  - content_type: {document, image, audio, log, json}
  - volume_estimate: {small, medium, large}  # thresholds TBD
  - sensitivity_level: {public, internal, confidential}

risk_signals_non_tabular:
  - large_volume: volume > threshold
  - unknown_format: file extensions not in known set
  - confidential_content: sensitivity=confidential
  - no_schema_hint: missing schema_hint field

decision_mapping:
  confidential + large_volume: reject        # High risk
  unknown_format + no_schema_hint: needs_review  # Medium risk
  known_format + internal: auto_accept       # Low risk
```

#### S5: Route Planning — 新設計

**Tabular**: `plan_tabular_route()` → selector_task_type + planned_tools

**Non-Tabular Shadow**:

```yaml
# Conceptual route planner for non-tabular
plan_non_tabular_route(task_type, case_dir) ->
  
  task_type: "non-tabular.document.extract"
  
  selector_view:
    rule_id: "document.extract.basic"
    content_adapters: ["pdfminer", "tika", "ocr"]
    
  planned_tools:
    - validate.content_accessible      # vs tabular's validate.eligibility
    - extract.text_content             # vs tabular's clean.phase_demo
    - transform.structure_metadata     # vs tabular's export.delivery_bundle
    
  inferred_gate_notes:
    - content_type: "mixed_documents"
    - requires_ocr: true               # if images present
    - schema_flexibility: high
```

#### S6-S8: Tool Layer — 新設計

**Tabular Tool Catalog** (11 tools): `clean.phase_demo`, `validate.eligibility`, etc.

**Non-Tabular Shadow Tool Catalog v1 (conceptual)**:

| Tool ID | Purpose | Input | Output |
|---------|---------|-------|--------|
| `validate.content_accessible` | Check files readable | case_dir/raw/ | accessibility report |
| `extract.text_content` | Extract text from docs | raw/*.{pdf,docx,png} | cleaned/extracted_texts/ |
| `extract.metadata` | Extract file metadata | raw/* | cleaned/metadata.json |
| `transform.normalize` | Normalize encodings/formats | extracted text | cleaned/normalized/ |
| `analyze.content_stats` | Generate quality metrics | cleaned/ | reports/content_stats.json |
| `bundle.multi_format` | Package outputs | cleaned/ + reports/ | delivery/bundle.zip |

#### S11: Output Guard — 擴展設計

**Tabular v2**: `cleaning_stats.json` → `removal_ratio`, `forced_cleaning`

**Non-Tabular Shadow**:

```yaml
# Conceptual output guard for non-tabular
output_guard_metrics:
  extraction_coverage: 0.0-1.0           # % of files successfully processed
  text_quality_score: 0.0-1.0            # OCR confidence / text coherence
  metadata_completeness: 0.0-1.0        # % of required metadata fields present
  anomaly_ratio: 0.0-1.0                # % flagged as anomalous/problematic

guard_conditions:
  extraction_coverage < 0.5: blocked
  text_quality_score < 0.3: warning
  anomaly_ratio > 0.1: warning
  all_ok + sensitivity=public: auto_approve_possible
```

### 3.3 Shadow Flow 架構圖

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Non-Tabular Shadow Flow v1                       │
│                        (Design Layer Only)                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  [S1 Intake] ──▶ [S2 Index] ──▶ [S3 Decision ─┬─▶ [S4 CP-A] (HITL)  │
│   (CLI)           (Auto)          (Extended)   │                    │
│                                     Rules      ▼                    │
│                                           ┌─────────┐                │
│                                           │ reject  │                │
│                                           └─────────┘                │
│                                                                      │
│  [S5 Route] ──▶ [S6 Select] ──▶ [S7 Gate] ──▶ [S8 Execute]          │
│   (New: NT    (New: NT         (New: Content  (New: Content          │
│    Route       Selector)        Validation)   Processors)            │
│    Planner)                                                        │
│                                                                      │
│                    │                                                 │
│                    ▼                                                 │
│  [S9 Outbox] ◀── [S10 Bundle]                                        │
│   (Same)          (New: Multi                                        │
│                    Format)                                           │
│                                                                      │
│  [S11 Guard] ──▶ [S12 CP-B] (HITL) ──▶ [S13 Approve]                │
│   (New: Content    (Same pattern)       (Same)                      │
│    Metrics)                                                          │
│                                                                      │
│  [S14 Ledger] ──▶ [S15 Notify]                                        │
│   (Same)          (Same pattern)                                      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

Legend:
  (Same)      = 直接繼承 Tabular 設計，無需變更
  (Extended)  = 在 Tabular 基礎上擴展
  (New: *)    = Non-Tabular 專屬新設計
```

---

## §4 決策與治理

### 4.1 可沿用 Tabular 標準線的治理規則

| 治理項目 | Tabular 來源 | Non-Tabular 繼承方式 |
|----------|-------------|---------------------|
| **Checkpoint A/B 模式** | W6-T5 / W6-T6 | **完全沿用**：decision → HITL → resume |
| **HITL 觸發條件** | `needs_review`, `medium/high` risk | **沿用**：unknown schema, sensitive content |
| **Auto-approve 閘門** | `--auto-approve-intake` | **沿用**：flag 控制，預設 false |
| **Outbox 寫入模式** | `outbox/{case_ref}/` | **沿用**：相同目錄結構 |
| **Notify 實驗控制** | W7-T3 `external_dispatch=false` | **沿用**：hardcoded 安全閘門 |
| **Audit log 格式** | `*_experiment_regression_*.json` | **沿用**：相同 JSON schema |

### 4.2 風險特別不同的領域（schema-free / unstructured）

| 風險類型 | Tabular 情境 | Non-Tabular 差異 | 建議 Safeguard |
|----------|-------------|------------------|----------------|
| **R-NT1: 內容不可讀** | N/A (CSV always readable) | 損壞 PDF, 加密文件, 不支援格式 | Pre-intake format scan |
| **R-NT2: 內容安全** | Row-level PII | 文件內嵌惡意程式碼, 超大檔案 | Sandboxing, size limits |
| **R-NT3: 處理時間不可預測** | Row count ∝ time | 圖片 OCR, 大文件解析時間差異大 | Async queue, timeout guards |
| **R-NT4: 品質難量化** | removal_ratio 客觀 | 文字提取準確度主觀性 | Confidence scoring, sampling review |
| **R-NT5: Schema drift** | Column rename/missing | 文件格式版本演進 | Schema registry, adapter versioning |

### 4.3 Governance View v2 對照

**Tabular Agent Standard Line Governance** (from `agent-standard-line-governance-view-v2.md`):

| Step | Driver | Decision Maker |
|------|--------|---------------|
| S3 | Agent | Agent |
| S4 | Agent + Human | Human |
| S7-S11 | Script | Auto |
| S12 | Agent + Human | Human |

**Non-Tabular Shadow 預計 Governance**:

| Step | Driver | Decision Maker | 差異說明 |
|------|--------|---------------|----------|
| S3 | Agent | Agent | **更複雜的 risk model** |
| S4 | Agent + Human | Human | **相同模式** |
| S7-S11 | Script | Auto | **New content processors** |
| S12 | Agent + Human | Human | **相同模式** |

---

## §5 Skill / Module 需求

### 5.1 需新增的 Skill 卡

**Skill Card NT-A: Document Extraction Pipeline**

| 欄位 | 設計值 |
|------|--------|
| **Skill Name** | `non-tabular.document.extract` |
| **Alias** | 混合文件文字提取 |
| **Source Case** | `cases/docu-corp/2026-0001` (conceptual) |
| **Maturity** | **shadow design only** |
| **Ticket Type** | `non-tabular.document.extract` |

**適用條件**:
- Input: Mixed documents in `raw/documents/`
- Document count: <100 (gate threshold TBD)
- Content type: PDF, DOCX, PNG, JPG

**Selector / Planned Tools**:
```yaml
P1 Content Access:  validate.content_accessible
P2 Text Extract:    extract.text_content (with OCR for images)
P3 Metadata:        extract.metadata
P4 Bundle:           bundle.multi_format
```

---

**Skill Card NT-B: Log Analysis Pipeline**

| 欄位 | 設計值 |
|------|--------|
| **Skill Name** | `non-tabular.log.analyze` |
| **Alias** | 日誌解析與異常偵測 |
| **Source Case** | `cases/log-analytics-co/2026-0001` (conceptual) |
| **Maturity** | **shadow design only** |
| **Ticket Type** | `non-tabular.log.analyze` |

**適用條件**:
- Input: Server logs in `raw/server_logs/`
- Volume: <5 GB (gate threshold TBD)
- Format: Text logs, JSON logs, CSV logs

**Selector / Planned Tools**:
```yaml
P1 Content Access:  validate.content_accessible
P2 Log Parse:       parse.log_structure
P3 Anomaly Detect:  analyze.anomaly_patterns
P4 Bundle:           bundle.multi_format
```

### 5.2 需新增的工具層模組

| 模組 | 用途 | 對照 Tabular |
|------|------|-------------|
| `tools/non_tabular_tool_catalog_v1.json` | Tool registry | `tabular_tool_catalog_v1.json` |
| `tools/non_tabular_tool_selector.py` | Tool selection logic | `tabular_tool_selector.py` |
| `tools/non_tabular_tool_executor.py` | Execution dispatcher | `tabular_tool_executor.py` |
| `tools/content_validators/` | Format validators | `validate.eligibility` |
| `tools/content_extractors/` | Text/OCR extractors | `clean.phase_demo` |
| `tools/content_analyzers/` | Quality metrics | `cleaning_stats.json` generator |
| `routing/intake_to_non_tabular_glue.py` | Route planner | `intake_to_tabular_glue.py` |

### 5.3 繼承的共用模組

| 模組 | 說明 |
|------|------|
| `hitl/checkpoint_a_integration_v1.py` | Checkpoint A 機制完全沿用 |
| `hitl/checkpoint_b_integration_v1.py` | Checkpoint B 機制完全沿用 |
| `tools/tabular_outbox_writer.py` | Outbox 寫入邏輯沿用 |
| `tools/inspect_tabular_outbox.py` | Outbox 檢視邏輯沿用 |
| `delivery/controlled_notify_experiment_v1.py` | Notify 控制邏輯沿用 |

---

## §6 Wave 9 建議票列表

### 6.1 Wave 9 目標

承接 `docs/ninety-five-percent-automation-blueprint-v2.md` §6 的缺口規劃（G8-5），Wave 9 目標為：

> **Non-Tabular 支援**：routing catalog 擴 family + shadow 設計實作

### 6.2 建議票明細

| 票號 | 標題 | 目標 | 依賴 | 預估工時 |
|------|------|------|------|----------|
| **W9-T1** | non-tabular-routing-catalog-v1 | `routing/intake_routing_catalog_v1.yaml` 擴展支援 `non-tabular.*` family | W8-T4 設計 | 2d |
| **W9-T2** | non-tabular-decision-rules-v1 | `routing/intake_decision_rules_v2.py` 擴展 non-tabular decision logic | W9-T1, W5-T1 | 3d |
| **W9-T3** | non-tabular-tool-catalog-v1 | `tools/non_tabular_tool_catalog_v1.json` + selector stub | W9-T2 | 2d |
| **W9-T4** | non-tabular-glue-layer-v1 | `routing/intake_to_non_tabular_glue.py` route planner | W9-T2, W4-T1 | 3d |
| **W9-T5** | non-tabular-fixture-docu-corp-v1 | `cases/docu-corp/` fixture 建立（Document Type A） | W9-T4 | 2d |
| **W9-T6** | non-tabular-fixture-logs-co-v1 | `cases/log-analytics-co/` fixture 建立（Log Type B） | W9-T4 | 2d |
| **W9-T7** | non-tabular-orchestrator-preview-v1 | `scripts/run_non_tabular_experiment.py` preview mode | W9-T4, W6-T4 | 3d |
| **W9-T8** | non-tabular-governance-view-v1 | `docs/agent-standard-line-governance-view-nt-v1.md` | W9-T1~T7 | 1d |
| **W9-T9** | non-tabular-shadow-ci-integration-v1 | PR CI dry-run for non-tabular family | W9-T7, W4-T4 | 2d |

### 6.3 Wave 9 票依賴圖

```
W8-T4 (Design Blueprint)
    │
    ├──▶ W9-T1 (Routing Catalog)
    │       │
    │       ├──▶ W9-T2 (Decision Rules)
    │       │       │
    │       │       ├──▶ W9-T3 (Tool Catalog)
    │       │       │
    │       │       └──▶ W9-T4 (Glue Layer)
    │       │               │
    │       │               ├──▶ W9-T5 (Fixture Docu-Corp)
    │       │               │
    │       │               ├──▶ W9-T6 (Fixture Logs-Co)
    │       │               │
    │       │               └──▶ W9-T7 (Orchestrator Preview)
    │       │                       │
    │       │                       └──▶ W9-T9 (CI Integration)
    │       │
    │       └──▶ W9-T8 (Governance View)
    │
    └──▶ (Wave 10: Run Path + HITL Integration)
```

### 6.4 Wave 9 DoD（設計完成標準）

- [ ] All tickets W9-T1~T9 have FRAME/STATE in `04_Workflows/tickets/`
- [ ] `routing/intake_routing_catalog_v1.yaml` includes `non-tabular.*` family definitions
- [ ] `routing/intake_decision_rules_v2.py` handles non-tabular task_types (design/structure, not full implementation)
- [ ] Tool catalog JSON schema defined for non-tabular tools
- [ ] Glue layer route planner spec documented
- [ ] Two conceptual fixtures (docu-corp, log-analytics-co) have intake.json designs
- [ ] Orchestrator preview CLI designed (dry-run only, no execution)
- [ ] CI integration plan documented (dry-run step, no mainline regression)
- [ ] Governance view doc aligns non-tabular with Tabular HITL patterns

---

## §7 附錄

### A. 與 Tabular 的關鍵差異速查表

| 項目 | Tabular | Non-Tabular Shadow |
|------|---------|-------------------|
| **核心資料單位** | Row | Document / File / Content chunk |
| **Schema** | Fixed (columns known upfront) | Flexible / Schema-on-read |
| **Gate 指標** | Row count, Removal ratio | Extraction coverage, Quality score |
| **Cleaning** | Filter, Map, Transform rows | Extract, Parse, Enrich content |
| **Validation** | Eligibility rules on columns | Content accessibility, Format compliance |
| **Bundle** | Single CSV + report | Multi-format manifest + metadata |

### B. 文件索引

| 主題 | 權威路徑 |
|------|----------|
| Tabular 標準線 | `docs/agent-standard-line-v1-summary.md` |
| 95% 自動化藍圖 | `docs/ninety-five-percent-automation-blueprint-v2.md` |
| 治理觀點 v2 | `docs/agent-standard-line-governance-view-v2.md` |
| Skill Cards v2 | `docs/skill-cards-v2.md` |
| Intake Decision Rules | `docs/intake-decision-rules-v1.md` |
| Routing Catalog | `docs/intake-routing-catalog-v1.md` |
| Multi-Agent 協作 | `docs/multi-agent-collaboration-spec-v1.md` |

### C. 風險聲明

1. **本設計為 Shadow 層**：所有內容為規劃設計，不觸及 production 行為
2. **Tabular 主鏈不變**：Non-tabular 為獨立 family，不改現有 Tabular routing/decision/tools
3. **Wave 9 實作需另開票**：本藍圖僅定義 Wave 9 票結構，不產出可執行程式
4. **HITL 模式繼承**：Non-tabular 維持相同的 Checkpoint A/B 人工介入模式

---

*Non-Tabular Shadow Flow Blueprint v1 · W8-T4 · 2026-06-10 · Architect*
