# Skill Map v1 — Tabular MVP 模組流程映射

> **Ticket**: W6-T1 · Skill Card & Skill Map v1  
> **Date**: 2026-06-10  
> **Role**: Architect + Scribe  
> **Purpose**: 將 Tabular MVP 相關模組映射至標準流程步驟，供 Agent 快速定位實作入口

---

## 流程步驟總覽

```
┌─────────┐    ┌──────────┐    ┌───────┐    ┌─────────┐    ┌─────────┐    ┌────────┐    ┌─────────────┐    ┌────────────┐
│  intake │───▶│ decision │───▶│ glue  │───▶│selector │───▶│executor │───▶│ outbox │───▶│inspect/replay│───▶│release/reg │
│  (接案)  │    │ (決策)   │    │(路由膠)│    │(工具選) │    │ (執行)  │    │(出箱)  │    │  (檢視/重演) │    │(發布/回歸) │
└─────────┘    └──────────┘    └───────┘    └─────────┘    └─────────┘    └────────┘    └─────────────┘    └────────────┘
```

---

## 步驟映射表

### 1. Intake（接案）

| 欄位 | 內容 |
|------|------|
| **Step** | intake |
| **Module/File** | `scripts/new_cleaning_case.py` |
| **Input** | CLI args: `--client-ref`, `--case-id`, `--raw-file`, `--product-sku` |
| **Output** | `cases/{client}/{case_id}/intake.json` + `raw/` 目錄 + `.gitkeep` |
| **Current Maturity** | **done** |
| **Tool ID** | `intake.new_case` |
| **Catalog Ref** | `docs/tabular-tool-catalog-v1.md` §4.1 |
| **Notes** | 手工建案 CLI；未來可銜接自動 intake API |

**輔助模組**

| Module | Purpose | Maturity |
|--------|---------|----------|
| `scripts/build_cases_index.py` | 刷新 `cases/index.json` | done |
| `scripts/lookup_case_history.py` | 查詢 case 歷史 | done |
| `notebooks/csv_cleaning/case_intake_loader.py` | intake 載入庫 | done (internal) |

---

### 2. Decision（決策）

| 欄位 | 內容 |
|------|------|
| **Step** | decision |
| **Module/File** | `routing/intake_decision_rules_v1.py` |
| **Input** | `task_type`, `case_dir`, `intake.json`, `glue_plan` |
| **Output** | `decision: auto_accept / needs_review / reject` + `reason` |
| **Current Maturity** | **done** · v1 |
| **Tool ID** | — (decision helper, not catalog tool) |
| **Catalog Ref** | `docs/intake-decision-rules-v1.md` |
| **Notes** | W5-T1 交付；消費 W4-T1 glue 輸出；**不**改主鏈 routing |

**決策條件對照**

| Fixture | `tabular.cleaning.mvp` | `tabular.intake.new_case` |
|---------|------------------------|---------------------------|
| `demo_phase` | `needs_review` | `auto_accept` |
| `sampleco` | `needs_review` | `auto_accept` |

---

### 3. Glue（路由膠合）

| 欄位 | 內容 |
|------|------|
| **Step** | glue |
| **Module/File** | `routing/intake_to_tabular_glue.py` |
| **Input** | `task_type` (from routing catalog), `case_dir` |
| **Output** | `plan_tabular_route()` dict: `selector_task_type`, `planned_tools[]`, `case_profile` |
| **Current Maturity** | **done** · v1 |
| **Tool ID** | — (mapping layer) |
| **Catalog Ref** | `docs/routing-tool-layer-glue-v1.md` |
| **Notes** | W4-T1 交付；純 mapping，不調用 Selector/Executor |

**Glue Output 範例**

```python
{
    "ok": True,
    "selector_task_type": "e2e",
    "planned_tools": [
        "validate.eligibility",
        "clean.phase_demo",
        "export.delivery_bundle"
    ],
    "case_profile": "demo_phase",
    "inferred_gate_notes": ["phase_like", "phase_demo"]
}
```

---

### 4. Selector（工具選擇）

| 欄位 | 內容 |
|------|------|
| **Step** | selector |
| **Module/File** | `tools/tabular_tool_selector.py` |
| **Input** | `case_dir`, `task_type` (intent), `intake`, `gate_notes` |
| **Output** | `candidate_tools[]` with `tool_id`, `reason`, `requires_force`, `human_review_required` |
| **Current Maturity** | **done** · v1 |
| **Tool ID** | — (recommendation engine) |
| **Catalog Ref** | `docs/tabular-tool-selector-spec.md` |
| **Notes** | W3-TL-T2 交付；recommendation-only，**不**驅動 E2E |

**Selector Rule 摘要**

| `selector_rule_id` | 條件 | `candidate_tools` | Flags |
|--------------------|------|-------------------|-------|
| `gate_only.eligibility` | `task_type=gate_only` | `validate.eligibility` | — |
| `phase_demo.clean.force` | `phase_like` + `review_needed` | `clean.phase_demo` | `requires_force: true` |
| `sampleco.clean.review` | `multi_row_export` / `schema_ambiguous` | `clean.phase_demo` | `human_review_required: true` |
| `bundle.delivery` | `cleaned/*_cleaned.csv` 存在 | `export.delivery_bundle` | — |

---

### 5. Executor（執行）

| 欄位 | 內容 |
|------|------|
| **Step** | executor |
| **Module/File** | `tools/tabular_tool_executor.py` + `tools/tabular_outbox_writer.py` |
| **Input** | `tool_id`, `case_dir`, `extra_args` |
| **Output** | subprocess result + `outbox/{case_ref}/{run_id}.json` |
| **Current Maturity** | **done** · v1 |
| **Tool ID** | N/A (executor framework) |
| **Catalog Ref** | `docs/tabular-tool-outbox-spec.md` |
| **Notes** | W3-TL-T3 交付；寫入 per-run JSON + `events.jsonl` |

**Executor 可執行 Tools**

| Tool ID | Module | Entry Kind | CLI 範例 |
|---------|--------|------------|----------|
| `validate.eligibility` | `scripts/check_case_eligibility.py` | cli | `python scripts/check_case_eligibility.py --case-dir {case_dir} --json` |
| `clean.phase_demo` | `notebooks/csv_cleaning/clean_phase_demo.py` | cli | `python notebooks/csv_cleaning/clean_phase_demo.py --case-dir {case_dir} --skip-eligibility [--force]` |
| `export.delivery_bundle` | `scripts/build_case_delivery_bundle.py` | cli | `python scripts/build_case_delivery_bundle.py --case-dir {case_dir} --json` |
| `orchestrate.e2e` | `scripts/run_case_e2e_validation.py` | cli | `python scripts/run_case_e2e_validation.py --case-dir {case_dir} --json` |
| `orchestrate.mainline_regression` | `scripts/run_mvp_mainline_regression.py` | cli | `python scripts/run_mvp_mainline_regression.py [-v]` |
| `index.cases` | `scripts/build_cases_index.py` | cli | `python scripts/build_cases_index.py` |
| `ui.local` | `app/local_ui.py` | cli | `python app/local_ui.py` |

---

### 6. Outbox（出箱）

| 欄位 | 內容 |
|------|------|
| **Step** | outbox |
| **Module/File** | `tools/tabular_outbox_writer.py` (write) / `tools/tabular_outbox_consumer.py` (read) |
| **Input** | Executor run result |
| **Output** | `outbox/{case_ref}/{run_id}.json` + `outbox/events.jsonl` append |
| **Current Maturity** | **done** · v1 |
| **Tool ID** | — (audit layer) |
| **Catalog Ref** | `docs/tabular-tool-outbox-spec.md` |
| **Notes** | W3-TL-T3/T4 交付；**≠** Phase 8.8 orchestration outbox |

**Outbox Schema**

| 欄位 | 說明 |
|------|------|
| `schema_version` | `tabular_outbox_v1` |
| `case_ref` | Case slug (e.g., `demo_phase`, `sampleco/2026-0001`) |
| `run_id` | `{UTC_timestamp_compact}_{tool_slug}` |
| `tool_id` | Catalog tool id |
| `ok` | Executor-level success |
| `exit_code` | Subprocess exit code |
| `artifacts[]` | Output file pointers |

---

### 7. Inspect / Replay（檢視/重演）

| 欄位 | 內容 |
|------|------|
| **Step** | inspect / replay |
| **Module/File** | `tools/tabular_outbox_consumer.py` + `tools/inspect_tabular_outbox.py` |
| **Input** | `case_ref`, `tool_id` (filter), `run_id` (single) |
| **Output** | Run summaries / full record / history join view |
| **Current Maturity** | **done** · v1 (inspect) · **planned** (replay) |
| **Tool ID** | — (consumer layer) |
| **Catalog Ref** | `docs/tabular-outbox-consumer-spec.md` |
| **Notes** | W3-TL-T4 交付；**replay 未實作**（Phase 8.8 / future ticket）|

**Consumer CLI**

```bash
# List runs for a case
python tools/inspect_tabular_outbox.py --case-ref demo_phase

# Filter by tool
python tools/inspect_tabular_outbox.py --case-ref demo_phase --tool-id validate.eligibility

# Single run detail
python tools/inspect_tabular_outbox.py --case-ref demo_phase --run-id 2026-06-10T01-52-00Z_eligibility

# History join (with cases/index.json)
python tools/inspect_tabular_outbox.py --case-ref demo_phase --join-history
```

---

### 8. Release / Regression（發布/回歸）

| 欄位 | 內容 |
|------|------|
| **Step** | release / regression |
| **Module/File** | `scripts/run_mvp_mainline_regression.py` |
| **Input** | — (built-in fixtures: `demo_phase`, `sampleco/2026-0001`) |
| **Output** | Regression report (6 tests) + `overall_ok` |
| **Current Maturity** | **done** · v1 |
| **Tool ID** | `orchestrate.mainline_regression` |
| **Catalog Ref** | `docs/mvp-mainline-regression.md` |
| **Notes** | E2E gate → clean → bundle for both fixtures |

**Release Checklist**

| 檢查項 | 命令 | 預期結果 |
|--------|------|----------|
| Wave 1 主鏈回歸 | `python scripts/run_mvp_mainline_regression.py -v` | 6/6 OK |
| Wave 2 catalog 一致性 | `python -m unittest tests.test_intake_routing_catalog tests.test_routing_eval_cases -v` | 18/18 OK |
| Wave 3-TL 四件套 | `python -m unittest tests.test_tabular_tool_catalog tests.test_tabular_tool_selector tests.test_tabular_tool_executor tests.test_tabular_outbox_consumer -v` | All OK |
| Wave 4 routing eval | `python scripts/run_routing_eval.py --dry-run --format json` | 4/4 aligned |

詳見：`docs/tabular-mvp-release-checklist.md`

---

## 模組依賴圖

```
                         ┌─────────────────────────────────────┐
                         │   routing/intake_routing_catalog    │
                         │        (_catalog_v1.yaml)            │
                         └──────────────┬──────────────────────┘
                                        │ task_type
                                        ▼
┌─────────────────┐    ┌─────────────────────────────────────┐    ┌─────────────────┐
│   intake/new    │───▶│  routing/intake_to_tabular_glue     │───▶│ decision helper │
│   (new_case)    │    │      (plan_tabular_route)           │    │ (rules_v1.py)   │
└─────────────────┘    └──────────────┬──────────────────────┘    └─────────────────┘
                                      │ glue_plan
                                      ▼
                         ┌─────────────────────────────────────┐
                         │   tools/tabular_tool_selector       │
                         │      (select_tabular_tools)         │
                         │   [task_type: gate_only/clean/      │
                         │            bundle/e2e]              │
                         └──────────────┬──────────────────────┘
                                        │ candidate_tools[]
                                        ▼
┌─────────────────┐    ┌─────────────────────────────────────┐    ┌─────────────────┐
│ tools/tabular_  │───▶│    tools/tabular_tool_executor      │───▶│  tools/tabular_  │
│ tool_catalog    │    │      (execute_tabular_tool)         │    │ outbox_writer    │
│ (_v1.json)      │    │                                     │    │                  │
└─────────────────┘    └──────────────┬──────────────────────┘    └────────┬────────┘
                                      │ subprocess + outbox                 │
                                      ▼                                   ▼
                         ┌────────────────────────┐          ┌─────────────────────────┐
                         │  scripts/* (actual CLI) │          │  outbox/{case_ref}/      │
                         │  notebooks/csv_cleaning │          │  {run_id}.json         │
                         └────────────────────────┘          │  events.jsonl          │
                                                              └─────────────────────────┘
                                                                           │
                                                                           ▼
                                                              ┌─────────────────────────┐
                                                              │ tools/inspect_tabular_  │
                                                              │ outbox.py (consumer)    │
                                                              └─────────────────────────┘
```

---

## 檔案路徑速查

| 類別 | 路徑 | 說明 |
|------|------|------|
| **Catalog** | `tools/tabular_tool_catalog_v1.json` | SSOT tool 定義 |
| **Routing** | `routing/intake_routing_catalog_v1.yaml` | Task type → family 路由 |
| **Eval Cases** | `routing/routing_eval_cases_v1.yaml` | Routing eval 對照案例 |
| **Glue** | `routing/intake_to_tabular_glue.py` | W4-T1 glue 實作 |
| **Selector** | `tools/tabular_tool_selector.py` | W3-TL-T2 selector |
| **Executor** | `tools/tabular_tool_executor.py` | W3-TL-T3 executor |
| **Outbox** | `outbox/` | Executor 輸出（gitignored）|
| **Cases** | `cases/demo_phase/`, `cases/sampleco/2026-0001/` | 標準案例 |
| **Reports** | `cases/*/reports/` | 業務輸出（eligibility, report, stats）|
| **Cleaned** | `cases/*/cleaned/` | 清洗後 CSV |

---

## 版本記錄

| 版本 | 日期 | 變更 |
|------|------|------|
| v1.0 | 2026-06-10 | W6-T1 初始建立；8 步驟映射完成 |

---

*SKILL-MAP-v1 · W6-T1 · 2026-06-10*
