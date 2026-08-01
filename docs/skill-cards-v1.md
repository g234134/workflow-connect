# Skill Cards v1 — Tabular MVP 標準清洗工作流

> **Repo SSOT**: `docs/TABULAR_MVP_SSOT.md` — product mainline landing doc  
> **Ticket**: W6-T1 · Skill Card & Skill Map v1  
> **Date**: 2026-06-10  
> **Role**: Architect + Scribe  
> **Purpose**: 將 Tabular MVP 穩定工作流抽象為可重用 Skill Card，供未來 Agent 按卡片執行

---

## 概述

本文件定義 **Tabular MVP（表格資料清洗）** 的標準 Skill Cards。每張卡片描述一個完整的工作流（從 intake 到 delivery），包含適用條件、輸入輸出、路由決策、工具選擇、執行計畫與驗收標準。

**背景文件**

| 文件 | 用途 |
|------|------|
| `docs/mvp-standard-trace-path.md` | L1 trace 節點對照 |
| `docs/tabular-tool-catalog-v1.md` | Tool ID 權威清單 |
| `docs/tabular-tool-selector-spec.md` | Selector 規則表 |
| `routing/intake_routing_catalog_v1.yaml` | Task type 路由 |

---

## Skill Card A：demo_phase 標準清洗案

### 基本資訊

| 欄位 | 值 |
|------|-----|
| **Skill Name** | `tabular.cleaning.phase_demo` |
| **Alias** | Phase 表最小 demo 清洗 |
| **Source Case** | `cases/demo_phase` |
| **Maturity** | stable · v1.0 |
| **ticket_type** | `tabular.cleaning.mvp` |

### 適用條件

- **Input Schema**: Phase 表四列（`Phase`, `Start_Date`, `End_Date`, `Status`）
- **Data Volume**: 小於 100 行（gate 觸發 `review_needed`）
- **Gate Status**: `review_needed`（exit 2）— 需 `--force` 執行
- **Client Profile**: `internal-demo`

### 輸入

```yaml
intake.json:
  client_ref: "internal-demo"
  case_id: "demo_phase"
  data_file: "raw/Phase.csv"
  product_sku: "clean-tabular-v1"

raw/Phase.csv:
  - 7 行原始資料（含 2 行重複/無效）
```

### 路由 / Glue

| 階段 | 輸出 |
|------|------|
| `intake_routing_catalog_v1` | `task_type: tabular.cleaning.mvp` → `preferred_tool_family: tabular_mvp` |
| `plan_tabular_route` (W4-T1) | `selector_task_type: e2e` → `planned_tools: [validate.eligibility, clean.phase_demo, export.delivery_bundle]` |

### Selector / planned_tools

| 步驟 | Tool ID | Selector Rule | Flags |
|------|---------|---------------|-------|
| P2 Gate | `validate.eligibility` | `gate_only.eligibility` | — |
| P3 Cleaning | `clean.phase_demo` | `phase_demo.clean.force` | `requires_force: true` |
| P4 Bundle | `export.delivery_bundle` | `bundle.delivery` | — |
| E2E Orch | `orchestrate.e2e` | （包裝以上三步）| `non_single_step` |

### Executor / 預期產物

| 產物 | 路徑 | 內容摘要 |
|------|------|----------|
| eligibility_result.json | `cases/demo_phase/reports/` | `status: review_needed`, `reason_code: rows<100` |
| report.json | `cases/demo_phase/reports/` | `accepted_rows: 5`, `rejected_rows: 2` |
| cleaning_stats.json | `cases/demo_phase/reports/` | 清洗統計 |
| Phase_cleaned.csv | `cases/demo_phase/cleaned/` | 5 行清洗後資料 |
| delivery_signoff.md | `cases/demo_phase/` | 交付簽核 |
| outbox record | `outbox/demo_phase/{run_id}.json` | executor audit trail |

**預期輸出比例**: 7 → 5 行（約 71%）

### Outbox / Trace 關聯

| Trace 層 | 鍵 / 檔案 | 說明 |
|----------|-----------|------|
| L1 Business | `reports/report.json` | 權威業務輸出 |
| L1 Business | `reports/eligibility_result.json` | Gate 判定 |
| L1 Tool | `outbox/demo_phase/*.json` | Per-run 執行記錄 |
| L1 Events | `outbox/events.jsonl` | Append-only 執行日誌 |
| L2 Infra | — | **未接線**（adjacent）|

### 完成定義（DoD）

- [ ] `intake.json` + `raw/Phase.csv` 存在
- [ ] Gate 執行 exit 2（`review_needed`）為預期行為
- [ ] Cleaning 執行 `--force` 後 `ok: true`
- [ ] Bundle 執行 `ok: true`, `output_guard.status: ok`
- [ ] E2E 執行 `overall_ok: true`
- [ ] 產出 5 行清洗後 CSV + 4 份 reports

### 常見失敗模式

| 失敗模式 | 症狀 | 處理 |
|----------|------|------|
| Gate 誤判 | `eligibility=accepted` 但 row<100 | 檢查 `dimensions.schema.notes` 是否含 `phase_like` |
| Force 遺漏 | Cleaning exit 1, `requires_force=true` | 確認 CLI 加上 `--force` 或 `--force-review` |
| Row 數異常 | output_rows ≠ 5 | 檢查 raw CSV 是否被修改（應為 7 行）|
| Outbox 缺失 | 無 `outbox/demo_phase/` | Executor 未啟用或 case_ref 解析錯誤 |

### Human Checkpoint（HITL 預留）

| 檢查點 | 條件 | 預設動作 |
|--------|------|----------|
| Gate 黃燈 | `review_needed` | 提示 `--force` 風險，需確認 |
| Output Guard | `status=ok` | 自動通過（本案例無警告）|
| Final Signoff | 報告生成後 | 可選人工確認 `delivery_signoff.md` |

---

## Skill Card B：sampleco/2026-0001 標準清洗案

### 基本資訊

| 欄位 | 值 |
|------|-----|
| **Skill Name** | `tabular.cleaning.sampleco_milestone` |
| **Alias** | Multi-milestone Sprint 模式清洗 |
| **Source Case** | `cases/sampleco/2026-0001` |
| **Maturity** | stable · v1.0 |
| **ticket_type** | `tabular.cleaning.mvp` |

### 適用條件

- **Input Schema**: Sprint milestone export（多欄位，含 `Milestone`, `Sprint`, `Status`, `Assignee` 等）
- **Data Volume**: 100+ 行（本案例 115 行，Gate `accepted`）
- **Gate Status**: `accepted`（exit 0）— 可直接清洗
- **Client Profile**: `sampleco`（近真實客戶樣本）
- **Schema Notes**: `multi_row_export`, `schema_ambiguous`（Selector 標記 `human_review_required`）

### 輸入

```yaml
intake.json:
  client_ref: "sampleco"
  case_id: "2026-0001"
  data_file: "raw/sampleco_milestone_export.csv"
  product_sku: "clean-tabular-v1"

raw/sampleco_milestone_export.csv:
  - 115 行原始資料（多 milestone、多 Sprint 模式）
  - Schema: 含 `Milestone`, `Sprint`, `Status`, `Assignee`, `Start_Date`, `End_Date`
```

### 路由 / Glue

| 階段 | 輸出 |
|------|------|
| `intake_routing_catalog_v1` | `task_type: tabular.cleaning.mvp` → `preferred_tool_family: tabular_mvp` |
| `plan_tabular_route` (W4-T1) | `selector_task_type: e2e` → `planned_tools: [validate.eligibility, clean.phase_demo, export.delivery_bundle]` |
| `inferred_gate_notes` | `["phase_like", "multi_row_export", "schema_ambiguous"]` |

### Selector / planned_tools

| 步驟 | Tool ID | Selector Rule | Flags |
|------|---------|---------------|-------|
| P2 Gate | `validate.eligibility` | `gate_only.eligibility` | — |
| P3 Cleaning | `clean.phase_demo` | `sampleco.clean.review` | `human_review_required: true` |
| P4 Bundle | `export.delivery_bundle` | `bundle.delivery` | — |
| E2E Orch | `orchestrate.e2e` | （包裝以上三步）| `non_single_step` |

**與 Card A 的差異**: 
- Cleaning 不需 `--force`（Gate 已 `accepted`）
- Selector 標記 `human_review_required`（因 `multi_row_export` + `schema_ambiguous`）

### Executor / 預期產物

| 產物 | 路徑 | 內容摘要 |
|------|------|----------|
| eligibility_result.json | `cases/sampleco/2026-0001/reports/` | `status: accepted` |
| report.json | `cases/sampleco/2026-0001/reports/` | `accepted_rows: 8`, `duplicate_rows_removed: 106` |
| cleaning_stats.json | `cases/sampleco/2026-0001/reports/` | 清洗統計（含去重明細）|
| *_cleaned.csv | `cases/sampleco/2026-0001/cleaned/` | 8 行清洗後資料 |
| delivery_signoff.md | `cases/sampleco/2026-0001/` | 交付簽核 |
| outbox record | `outbox/sampleco/2026-0001/{run_id}.json` | executor audit trail |

**預期輸出比例**: 115 → 8 行（約 7%，Output Guard `warning`）

### Outbox / Trace 關聯

| Trace 層 | 鍵 / 檔案 | 說明 |
|----------|-----------|------|
| L1 Business | `reports/report.json` | 權威業務輸出 |
| L1 Business | `reports/eligibility_result.json` | Gate 判定 `accepted` |
| L1 Tool | `outbox/sampleco/2026-0001/*.json` | Per-run 執行記錄 |
| L1 Events | `outbox/events.jsonl` | Append-only 執行日誌 |
| L2 Infra | — | **未接線**（adjacent）|

### 完成定義（DoD）

- [ ] `intake.json` + `raw/sampleco_milestone_export.csv` 存在
- [ ] Gate 執行 exit 0（`accepted`）
- [ ] Cleaning 執行 **無需** `--force`，`ok: true`
- [ ] Bundle 執行 `ok: true`, `output_guard.status: warning`（預期）
- [ ] E2E 執行 `overall_ok: true`
- [ ] 產出 8 行清洗後 CSV + 4 份 reports

### 常見失敗模式

| 失敗模式 | 症狀 | 處理 |
|----------|------|------|
| Gate 誤判 | `review_needed` 但 row>100 | 檢查 `dimensions.schema.notes` 是否遺漏 `multi_row_export` |
| Row 數異常 | output_rows ≠ 8 | 檢查 milestone 模式變更（預期 106 行去重）|
| Output Guard 錯誤 | `status=unknown` | 檢查 `reports/report.json` 是否存在且含行數欄位 |
| Schema drift | Selector `error.unknown_schema` | 確認 `gate_notes` 含 `phase_like` 或更新 Selector 規則 |

### Human Checkpoint（HITL 預留）

| 檢查點 | 條件 | 預設動作 |
|--------|------|----------|
| Gate 綠燈 | `accepted` | 自動通過 |
| Schema 歧義 | `schema_ambiguous` in notes | 提示 `human_review_required`，建議人工檢視 |
| Output Guard | `status=warning` | 提示比例異常（115→8），建議確認去重邏輯 |
| Final Signoff | 報告生成後 | 可選人工確認 `delivery_signoff.md` |

---

## Skill Card C：additional_demo 擴展 Phase 清洗案（W7-T1 · 實驗線）

### 基本資訊

| 欄位 | 值 |
|------|-----|
| **Skill Name** | `tabular.cleaning.additional_demo` |
| **Alias** | 擴展 Phase 表 demo（12 行） |
| **Source Case** | `cases/additional_demo` |
| **Maturity** | experimental · v1.0 |
| **ticket_type** | `tabular.cleaning.mvp` |
| **Scope** | **實驗線 only** — 不進 production contract |

### 適用條件

- **Input Schema**: Phase 表四列（同 Card A）
- **Data Volume**: 12 行（`<100`，gate `review_needed`）
- **Client Profile**: `additional-demo`
- **Decision Signal**: `unknown_fixture_profile`（W5-T1 非 production allowlist）

### 輸入

```yaml
intake.json:
  client_ref: "additional-demo"
  case_id: "additional_demo"
  data_file: "raw/Phase_extended.csv"

raw/Phase_extended.csv:
  - 12 行 Phase 表（實驗線擴展樣本）
```

### 路由 / Glue / Selector

| 階段 | 輸出 |
|------|------|
| `plan_tabular_route` | `case_profile=additional_demo`；`planned_tools` 同 Card A |
| Orchestrator mock S11 | `mock_profile_additional_demo`；`removal_ratio=0.25` |

### Human Checkpoint

| 檢查點 | 條件 | 預設動作 |
|--------|------|----------|
| Checkpoint A | `needs_review` + `unknown_fixture_profile` | `would_pause` |
| Checkpoint B | mock `forced_cleaning=true` | `would_trigger=true`（preview） |

---

## Skill Card D：sandbox_client 沙盒客戶清洗案（W7-T1 · 實驗線）

### 基本資訊

| 欄位 | 值 |
|------|-----|
| **Skill Name** | `tabular.cleaning.sandbox_client` |
| **Alias** | 沙盒客戶 milestone export（55 行） |
| **Source Case** | `cases/sandbox_client` |
| **Maturity** | experimental · v1.0 |
| **ticket_type** | `tabular.cleaning.mvp` |
| **Scope** | **實驗線 only** — 不進 production contract |

### 適用條件

- **Input Schema**: Phase / milestone 混合 export（四列 Phase 表格式）
- **Data Volume**: 55 行（`<100`，gate `review_needed`）
- **Client Profile**: `sandbox-client`
- **Decision Signal**: `unknown_fixture_profile`

### 輸入

```yaml
intake.json:
  client_ref: "sandbox-client"
  case_id: "sandbox_client"
  data_file: "raw/sandbox_milestone_export.csv"

raw/sandbox_milestone_export.csv:
  - 55 行 milestone 模式 export（子集自 sampleco 樣式）
```

### 路由 / Glue / Selector

| 階段 | 輸出 |
|------|------|
| `plan_tabular_route` | `case_profile=sandbox_client`；catalog default tools |
| Orchestrator mock S11 | `mock_profile_sandbox_client`；`removal_ratio=0.35` |

### Human Checkpoint

| 檢查點 | 條件 | 預設動作 |
|--------|------|----------|
| Checkpoint A | `needs_review` | `would_pause` |
| Checkpoint B | mock `status=ok` | `would_trigger=false`（removal_ratio ≤ 0.5） |

---

## Skill Card 對照表

| 維度 | Card A: demo_phase | Card B: sampleco/2026-0001 | Card C: additional_demo | Card D: sandbox_client |
|------|-------------------|---------------------------|-------------------------|------------------------|
| **輸入行數** | 7 | 115 | 12 | 55 |
| **Gate Status** | `review_needed` | `accepted` | `review_needed` | `review_needed` |
| **Production Contract** | 錨點 | 錨點 | **實驗線 only** | **實驗線 only** |
| **Decision Signal** | allowlist + review_needed | allowlist + schema_ambiguous | unknown_fixture_profile | unknown_fixture_profile |
| **Output Guard (mock)** | `ok` | `warning` | `ok` | `ok` |
| **主要用途** | 最小示範 / CI smoke | 近真實客戶樣本 | 擴展 Phase 實驗 | 沙盒客戶實驗 |

---

## Skill Card 對照表（legacy · Card A/B 詳細）

| 維度 | Card A: demo_phase | Card B: sampleco/2026-0001 |
|------|-------------------|---------------------------|
| **輸入行數** | 7 | 115 |
| **Gate Status** | `review_needed` | `accepted` |
| **Need Force** | 是 | 否 |
| **Schema Notes** | `phase_like`, `phase_demo` | `phase_like`, `multi_row_export`, `schema_ambiguous` |
| **Selector Rule** | `phase_demo.clean.force` | `sampleco.clean.review` |
| **Human Review** | 否（Force 自動） | 是（schema_ambiguous）|
| **輸出行數** | 5 | 8 |
| **Output Guard** | `ok` | `warning`（比例）|
| **主要用途** | 最小示範 / CI smoke | 近真實客戶樣本 |

---

## 延伸：建立新 Skill Card 的檢查清單

| 步驟 | 檢查項 | 參考文件 |
|------|--------|----------|
| 1. 定義案例 | 確認 `cases/{client}/{case_id}/` 結構 | `cases/README.md` |
| 2. 填寫 intake | 建立 `intake.json` + 放置 raw 檔 | `docs/mvp-standard-trace-path.md` §3 |
| 3. 執行 Gate | 記錄 `eligibility` 與 exit code | `docs/tabular-tool-selector-spec.md` §3.1 |
| 4. 選擇 Rule | 對照 Selector rule table | `docs/tabular-tool-selector-spec.md` §3 |
| 5. 執行 E2E | 驗證 `overall_ok: true` | `docs/mvp-mainline-regression.md` §2 |
| 6. 記錄產物 | 列出預期輸出檔案 | 本檔 §Executor |
| 7. 標註風險 | 標記 `requires_force`, `human_review_required` | 本檔 §Human Checkpoint |
| 8. 回歸測試 | 加入 `run_mvp_mainline_regression.py` | `docs/mvp-mainline-regression.md` §6.2 |

---

## 版本記錄

| 版本 | 日期 | 變更 |
|------|------|------|
| v1.0 | 2026-06-10 | W6-T1 初始建立；Card A/B 完成 |
| v1.1 | 2026-06-10 | W7-T1 新增 Card C/D（additional_demo / sandbox_client · 實驗線） |

---

*SKILL-CARDS-v1 · W6-T1 · 2026-06-10*
