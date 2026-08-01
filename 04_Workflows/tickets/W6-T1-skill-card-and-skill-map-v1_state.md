# W6-T1 — Skill Card & Skill Map v1 · State

> **Role**: Architect + Scribe  
> **Status**: implementer done · Reviewer pending  
> **Date**: 2026-06-10  
> **DoD**: Document-only ticket — 3 files created, 2 files updated

---

## 1. 任務摘要

將已穩定的 Tabular MVP 工作流抽象成 **Skill Card**（可重用工作流卡片），並建立 **Skill Map**（模組流程映射），讓未來 Agent 能按卡片重用工作流。

### 交付範圍

| 項 | 狀態 |
|---|---|
| Skill Card A（demo_phase 標準清洗案）| ✅ 完成 |
| Skill Card B（sampleco/2026-0001 標準清洗案）| ✅ 完成 |
| Skill Map（8 步驟模組映射表）| ✅ 完成 |
| WORKFLOW_INDEX 更新（Wave 6 區塊）| ✅ 完成 |
| WAVE_PROGRESS_DASHBOARD 更新（Wave 6 區塊）| ✅ 完成 |

---

## 2. 已讀清單（施工前盤點）

### P0 已讀

- [x] `ENGINEERING_CONTRACT.mdc`（本檔 `.cursor/rules/`）— 四流派 / 12-rule
- [x] `AGENTS.md` — 接戰／封存協議
- [x] `docs/mvp-standard-trace-path.md` — L1 trace 節點對照
- [x] `docs/mvp-mainline-regression.md` — 回歸 runner 說明
- [x] `docs/intake-routing-catalog-v1.md` — W2-T1 task_type 路由
- [x] `docs/routing-tool-layer-glue-v1.md` — W4-T1 glue plan
- [x] `docs/routing-eval-runner-v1.md` — W4-T2 eval runner
- [x] `docs/tabular-tool-catalog-v1.md` — W3-TL-T1 tool SSOT
- [x] `docs/tabular-tool-selector-spec.md` — W3-TL-T2 selector 規則
- [x] `docs/tabular-tool-outbox-spec.md` — W3-TL-T3 executor/outbox
- [x] `docs/tabular-outbox-consumer-spec.md` — W3-TL-T4 consumer
- [x] `docs/tabular-intake-tool-path-v1.md` — W4-T3-A intake path preview
- [x] `docs/tabular-mvp-release-checklist.md` — W4-T4 release checklist
- [x] `04_Workflows/WORKFLOW_INDEX.md` — 工作流索引
- [x] `docs/WAVE_PROGRESS_DASHBOARD.md` — Wave 進度總覽

### 狀態依據

- Wave 1–5 已全部 **done** 或 **accepted_with_gaps**（見 DASHBOARD）
- 本票為 **Wave 6** 啟動，純文檔化，不改程式碼
- 依 `ENGINEERING_CONTRACT.mdc` §OUT-7.4：文檔工單須附 APP-DOC 自檢

---

## 3. 變更檔案清單

### 3.1 新增檔案

| 檔案 | 類型 | 說明 |
|------|------|------|
| `docs/skill-cards-v1.md` | 主交付 | 兩張 Skill Card（A/B）+ 延伸檢查清單 |
| `docs/skill-map-v1.md` | 主交付 | 8 步驟模組映射表 + 依賴圖 + 路徑速查 |
| `04_Workflows/tickets/W6-T1-skill-card-and-skill-map-v1_state.md` | 票 state | 本檔 |

### 3.2 修改檔案

| 檔案 | 變更內容 |
|------|----------|
| `04_Workflows/WORKFLOW_INDEX.md` | 新增 §1.8 Wave 6 — Skill Card & Skill Map 區塊 |
| `docs/WAVE_PROGRESS_DASHBOARD.md` | 新增 Wave 6 區塊；更新總覽表；新增驗證命令 |

---

## 4. Skill Card 摘要

### Card A：demo_phase 標準清洗案

| 欄位 | 值 |
|------|-----|
| **Skill Name** | `tabular.cleaning.phase_demo` |
| **Input Rows** | 7 |
| **Gate Status** | `review_needed`（exit 2）|
| **Requires Force** | 是 |
| **Output Rows** | 5 |
| **Output Guard** | `ok` |
| **Key Tool IDs** | `validate.eligibility`, `clean.phase_demo`, `export.delivery_bundle` |
| **Selector Rule** | `phase_demo.clean.force` |
| **Human Review** | 否（Force 自動）|

### Card B：sampleco/2026-0001 標準清洗案

| 欄位 | 值 |
|------|-----|
| **Skill Name** | `tabular.cleaning.sampleco_milestone` |
| **Input Rows** | 115 |
| **Gate Status** | `accepted`（exit 0）|
| **Requires Force** | 否 |
| **Output Rows** | 8 |
| **Output Guard** | `warning`（比例）|
| **Key Tool IDs** | `validate.eligibility`, `clean.phase_demo`, `export.delivery_bundle` |
| **Selector Rule** | `sampleco.clean.review` |
| **Human Review** | 是（schema_ambiguous）|

---

## 5. Skill Map 步驟摘要

| Step | Module/File | Input | Output | Maturity |
|------|-------------|-------|--------|----------|
| **intake** | `scripts/new_cleaning_case.py` | CLI args | `intake.json` + `raw/` | done |
| **decision** | `routing/intake_decision_rules_v1.py` | glue_plan | `auto_accept/needs_review/reject` | done |
| **glue** | `routing/intake_to_tabular_glue.py` | task_type, case_dir | `planned_tools[]` | done |
| **selector** | `tools/tabular_tool_selector.py` | case_dir, task_type | `candidate_tools[]` | done |
| **executor** | `tools/tabular_tool_executor.py` | tool_id, case_dir | subprocess + outbox | done |
| **outbox** | `tools/tabular_outbox_writer.py` | run result | `{run_id}.json` + `events.jsonl` | done |
| **inspect/replay** | `tools/tabular_outbox_consumer.py` | case_ref, tool_id | run summaries / history | done / planned (replay) |
| **release/regression** | `scripts/run_mvp_mainline_regression.py` | — | 6 tests + `overall_ok` | done |

---

## 6. 驗證（本票 DoD）

本票為 **文檔工單**，不產出可執行程式碼。驗證以結構檢查為主：

### 6.1 文件結構檢查

```bash
# 確認新增檔案存在
ls docs/skill-cards-v1.md
ls docs/skill-map-v1.md
ls 04_Workflows/tickets/W6-T1-skill-card-and-skill-map-v1_state.md

# 確認索引更新
grep -n "Wave 6" 04_Workflows/WORKFLOW_INDEX.md
grep -n "Wave 6" docs/WAVE_PROGRESS_DASHBOARD.md
```

### 6.2 引用一致性檢查

- [x] `skill-cards-v1.md` 引用 `docs/mvp-standard-trace-path.md` §3 案例表
- [x] `skill-cards-v1.md` 引用 `docs/tabular-tool-selector-spec.md` §3 selector 規則
- [x] `skill-map-v1.md` 引用所有 8 步驟對應模組
- [x] `skill-map-v1.md` 工具 ID 與 `tools/tabular_tool_catalog_v1.json` 一致
- [x] 無硬編碼絕對路徑（遵循 `ENGINEERING_CONTRACT.mdc` META-0.4）

### 6.3 APP-DOC 文檔工單自檢

| 檢查項 | 結果 | 證據 |
|--------|------|------|
| 可移植正文零本機絕對路徑 | ✅ 是 | 全文使用 repo 相對路徑 |
| 地圖涵蓋任務卡約定範圍 | ✅ 是 | 8 步驟 + 2 張 Skill Card |
| Cabin 僅角色/用途 | ✅ 是 | 無 venv/DB 路徑 |
| 禁區僅類型 | ✅ 是 | 無具體禁區路徑 |
| Pipeline 制度在可移植層 | ✅ 是 | 引用既有 spec |
| 對齊 W0 | ✅ 是 | 無 Conditions/Progress/AGENTS 衝突 |
| 未偷寫 `.cursor/rules` | ✅ 是 | 僅 `docs/` + `04_Workflows/` |

---

## 7. Skeleton / Placeholder

| 項 | 狀態 | 說明 |
|---|---|---|
| Skill Card 結構 | 完成 | 10 欄位模板（名稱/條件/輸入/路由/Selector/Executor/Outbox/DoD/失敗模式/HITL）|
| Skill Map 步驟 | 完成 | 8 步驟全映射 |
| Wave 6 Dashboard | 完成 | 區塊已建立，含 W6-T1/T2 placeholder |
| **延伸 Card** | Skeleton | W6-T2 或其他 Wave 可套用模板 |

---

## 8. 阻塞（Blockers）

無阻塞。本票純文檔化，不依賴未實作功能。

---

## 9. 下一步（Next Steps）

| 優先 | 項目 | 指派 |
|------|------|------|
| P1 | Reviewer 審閱 `docs/skill-cards-v1.md` | Reviewer |
| P1 | Reviewer 審閱 `docs/skill-map-v1.md` | Reviewer |
| P2 | W6-T2 — Skill Card 延伸（可選新案例）| 待開票 |
| P3 | 若 W6-T1 驗收通過，更新 `docs/WAVE_PROGRESS_DASHBOARD.md` Wave 6 狀態為 done | Scribe |

---

## 10. 交叉引用

| 文件 | 用途 |
|------|------|
| `docs/skill-cards-v1.md` | Skill Card A/B 全文 |
| `docs/skill-map-v1.md` | 8 步驟映射表全文 |
| `04_Workflows/WORKFLOW_INDEX.md` §1.8 | Wave 6 索引 |
| `docs/WAVE_PROGRESS_DASHBOARD.md` §Wave 6 | Wave 6 進度區塊 |
| `docs/mvp-standard-trace-path.md` | Card A/B 來源案例定義 |
| `docs/tabular-tool-catalog-v1.md` | Tool ID 權威 |
| `docs/tabular-tool-selector-spec.md` | Selector 規則 |

---

## 11. 工作報告（Work Report 七節對照）

| 節 | 內容 |
|---|---|
| §1 任務/角色/日期 | W6-T1 · Architect + Scribe · 2026-06-10 |
| §2 變更檔案 | 3 新增 + 2 修改（見 §3）|
| §3 Skeleton | 僅「延伸 Card」為 skeleton（見 §7）|
| §4 驗證證據 | 文件結構檢查 + APP-DOC 自檢（見 §6）|
| §5 阻塞 | 無（見 §8）|
| §6 下一步 | Reviewer 審閱 + W6-T2（見 §9）|
| §7 Override/留痕 | 無 override；本票純文檔化，無禁區接觸 |

---

---

## C_REPORT (Reviewer)

- conclusion: **accepted_with_gaps**
- blocking_issues: 無
- checks_summary:
  - **AC-1 ✅**: Skill Card A/B 10 欄位模板已初版完成
  - **AC-2 ✅**: Skill Map 8 步驟已對齊現行 pipeline
  - **AC-3 ✅**: 文件結構檢查 + APP-DOC 自檢通過
- risk_level: low
- gaps:
  - Skill Card A/B 10 欄位模板已初版完成，待後續 Sprint 追加「實戰回填」樣本
  - Skill Map 8 步驟已對齊現行 pipeline，可視需要增加更多案例映射（非 blocking）
- suggestions:
  - 後續 Sprint 可追加更多 fixture 案例實戰回填
  - Skill Map 可視 Wave 7-8 新案例擴充映射

---

*W6-T1-STATE · Skill Card & Skill Map v1 · 2026-06-10 · Reviewer: accepted_with_gaps*
