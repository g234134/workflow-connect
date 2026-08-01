# TICKET STATE · W3-TL-T1 · Tabular Tool Catalog v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 3 · Tool Layer · **Tabular MVP**（gate / clean / bundle / E2E 工具層）

---

## FRAME

- Title: Tabular Tool Catalog v1（文件 + JSON 雙軌）
- Goal: 建立 Tabular MVP 工具層的單一權威 Catalog（人讀 spec + 機器 JSON），覆蓋 MVP 主鏈 entrypoints 與輔助工具，每條 `tool_id` 可對應 repo 內實際腳本／模組路徑。
- Scope:
  - 新建 `docs/tabular-tool-catalog-v1.md`（Onboarding / Reviewer 導向）
  - 新建 `tools/tabular_tool_catalog_v1.json`（僅 Tabular MVP 工具；含 `schema_version`、`catalog_revision`、`tools[]`）
  - 每工具欄位至少：`tool_id`、`type`、`display_name`、`module_path`、`entry_kind`、`enabled`、`applicable_conditions`、`risk_notes`、`verify_command`（摘要）
  - 文檔內 **對照表**（非 JSON 合併）：Gov Registry（`obs.*` / `kb.*`）→ `governed_by: gov_registry`；Phase 8.8 編排工具 → `governed_by: phase_8.8_spec`
  - 新建 `tests/test_tabular_tool_catalog.py`：JSON 路徑存在性、去重 `tool_id`、`enabled` 工具 module 可解析
  - 可選輕量 loader：`tools/tabular_tool_catalog_loader.py`（`load_tabular_catalog() -> dict`），若實作須回傳 `ok` / `message`
- NonScope:
  - 不修改 gate / clean / bundle / E2E **行為**或 CLI 旗標語意
  - 不把 Gov Registry（`skills/gov_cards/*`）或 Phase 8.8 `llm.*` 等塞入 `tabular_tool_catalog_v1.json`
  - 不合併 Wave8 `skill-clean-*` SKU schema
  - 不 rename / 觸碰既有 `W3-T1_state.md`–`W3-T4_state.md` 或 `04_Workflows/SPEC_tool_catalog_and_selector_v1.md` 正文
  - 不接入 ask selector / `routing_policy.yaml` / LangGraph
- AllowedPaths:
  - `docs/tabular-tool-catalog-v1.md`
  - `tools/tabular_tool_catalog_v1.json`
  - `tools/tabular_tool_catalog_loader.py`（可選）
  - `tests/test_tabular_tool_catalog.py`
  - `outbox/.gitkeep`（僅若需占位；本票非必）
  - `04_Workflows/tickets/W3-TL-T1-tabular-tool-catalog_state.md`
- BlockedPaths:
  - `HARNESS_CONSTITUTION.md`、`ENGINEERING_CONTRACT.md`、`AGENTS.md`、`.cursor/rules/*`
  - `04_Workflows/tickets/W3-T1_state.md`–`W3-T4_state.md`（Phase 8.8 draft；唯讀對照）
  - `skills/gov_cards/*`（唯讀對照）
  - `scripts/check_case_eligibility.py`、`notebooks/csv_cleaning/clean_phase_demo.py` 等 MVP 主鏈 **邏輯**（本票只 catalog，不改實作）
  - `core/*`（暗部 orchestration tool layer）
- Dependencies:
  - MVP 主鏈已穩：`docs/mvp-standard-trace-path.md`、`docs/mvp-mainline-regression.md`
  - 資產盤點：W3-COORD 回合（Tool 資產清單 §A）
  - 建議前置：`W2-T4` 或等價回歸基線（`run_mvp_mainline_regression` 6/6 OK）
- Risks:
  - Catalog 與磁碟路徑漂移 → unittest 路徑存在性攔截
  - 與 Gov / Phase 8.8 ID 混用 → JSON 禁入；文檔僅對照欄
  - `clean.phase_demo` 語義限制未寫清 → 必須在 `risk_notes` 標 Phase 專用規則
- Observability:
  - logs: catalog load `catalog_revision`、`tool_count`
  - metrics: N/A
  - traces: N/A
- OutputArtifacts:
  - `docs/tabular-tool-catalog-v1.md`
  - `tools/tabular_tool_catalog_v1.json`
  - `tests/test_tabular_tool_catalog.py`
  - （可選）`tools/tabular_tool_catalog_loader.py`
- AcceptanceCriteria:
  - **AC-1**：`tabular_tool_catalog_v1.json` 含 MVP trace §2.3 全部 hard entrypoints（intake / gate / clean / bundle / E2E）及盤點 §A 輔助工具（index / lookup / plan / local_ui 等）
  - **AC-2**：每條 `tools[].module_path` 指向 repo 內存在之 `scripts/` 或 `notebooks/` 路徑（unittest 驗證）
  - **AC-3**：`tool_id` 命名穩定（建議 `<domain>.<action>.<target>`，如 `validate.eligibility`、`clean.phase_demo`）；JSON 內無重複 `tool_id`
  - **AC-4**：Markdown spec 含 Gov Registry / Phase 8.8 **對照表**（分欄，非 JSON 合併）
  - **AC-5**：`python -m unittest tests.test_tabular_tool_catalog -v` 全綠
  - **AC-6（主鏈守護）**：`python scripts/run_mvp_mainline_regression.py -v` → 6/6 OK，exit 0（本票不得改主鏈行為）
- VerificationCommands:
  - `python -m unittest tests.test_tabular_tool_catalog -v`
    - 預期：全綠
  - `python scripts/run_mvp_mainline_regression.py -v`
    - 預期：6/6 OK，exit 0

---

## Minimal Read Set

| # | 路徑 | 用途 |
|---|------|------|
| 1 | `docs/governance-constitution-v1.md` §1、§3、§5 | 四流派、禁區、票邊界 |
| 2 | 本檔 FRAME + AllowedPaths | 硬邊界 |
| 3 | `docs/mvp-standard-trace-path.md` §2.3 | MVP 主鏈 entrypoints |
| 4 | `docs/mvp-mainline-regression.md` | 回歸守護命令 |
| 5 | `docs/SKILL_CATALOG_OVERVIEW.md` | Gov Registry 對照（**不**合併 JSON） |
| 6 | `04_Workflows/tickets/W3-T1_state.md`（唯讀） | Phase 8.8 分軌對照 |
| 7 | 盤點 §A 各腳本 docstring / `--help` | 適用條件與旗標 |

---

## §2 skeleton / placeholder

| 項 | 狀態 | 說明 |
|----|------|------|
| `tools/tabular_tool_catalog_v1.json` | **[待實作]** | Implementer 本票交付 |
| `docs/tabular-tool-catalog-v1.md` | **[待實作]** | 人讀 spec |
| `tools/tabular_tool_catalog_loader.py` | **[placeholder · 可選]** | 若省略，T2/T3 可直接讀 JSON |
| Gov / Phase 8.8 對照表 | **[待實作]** | 僅 markdown，不進 JSON |

> **分軌聲明（§2 / §8）**：本票僅涵蓋 tabular MVP 工具層（gate / clean / bundle / E2E）；與既有 Phase 8.8 `W3-T1`–`W3-T4` 編排 Tool Layer 分軌，票號前綴 `W3-TL-*` 僅用於 Tabular MVP。

---

## STATE

- overall_status: draft
- current_owner: orchestrator
- next_action: Assign to Implementer — 依 B_REPORT Implementation Plan 撰寫 catalog JSON + markdown spec + tests
- last_updated: 2026-06-10 · orchestrator (W3-COORD)
- status_by_role:
  - orchestrator: done
  - implementer: pending
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

> **Orchestrator 初版（2026-06-10）**：本票剛開票；Implementer 施工時更新下方欄位。

### 與 Phase 8.8 W3-T* 的邊界

- **本票（W3-TL-T1）**：戰車根 Tabular MVP；Catalog SSOT = `tools/tabular_tool_catalog_v1.json` + `docs/tabular-tool-catalog-v1.md`。
- **既有 draft（W3-T1–T4）**：暗部 Phase 8.8 編排 Tool Layer（`llm.ask`、outbox replay 等）；**禁止**在本票 rename、合併或修改其 state / SPEC。
- **Gov Registry（B-F1）**：`obs.*` / `kb.*` 權威在 `skills/gov_cards/`；本票 markdown 僅 **對照表** 引用。

### Implementation Plan (initial)

- [ ] 起草 `tools/tabular_tool_catalog_v1.json`（≥ MVP §2.3 五 entrypoints + §A 輔助工具）
- [ ] 撰寫 `docs/tabular-tool-catalog-v1.md`（類型、適用條件、風險、verify 命令、Gov/8.8 對照表）
- [ ] 實作 `tests/test_tabular_tool_catalog.py`（路徑存在、去重 tool_id）
- [ ] （可選）`tools/tabular_tool_catalog_loader.py`
- [ ] 跑 `run_mvp_mainline_regression.py -v` 確認主鏈未破

### Files To Touch

- `docs/tabular-tool-catalog-v1.md`
- `tools/tabular_tool_catalog_v1.json`
- `tests/test_tabular_tool_catalog.py`
- （可選）`tools/tabular_tool_catalog_loader.py`

- changed_files: **[待實作]**
- artifacts: **[待實作]**
- verification: **[待實作]** — 須含 `tests.test_tabular_tool_catalog` 與 `run_mvp_mainline_regression.py -v`（6/6 OK）
- behavior_notes: **[待實作]**
- deferred_items: Selector / Executor 留 W3-TL-T2、W3-TL-T3

---

## C_REPORT

- conclusion: **accepted_with_gaps**
- blocking_issues: 無
- checks_summary:
  - **AC-1 ✅**：11 條工具覆蓋 MVP trace §2.3 五主鏈 entrypoints + index/lookup/plan/local_ui；含 `validate.output_guard` 與 `orchestrate.mainline_regression` 合理擴展
  - **AC-2 ✅**：全部 enabled `module_path` 存在於 `scripts/` / `notebooks/` / `app/`（測試已允許 `app/` 前綴）
  - **AC-3 ✅**：`tool_id` 無重複、命名穩定（`ui.local` 略偏三段位，可接受）
  - **AC-4 ✅**：§2 四 Catalog 對照 + §1/§5 明確 Tabular-only JSON；§3「風險关键字」與 JSON `risk_notes` 有 drift（G1）
  - **AC-5 ✅**：`python -m unittest tests.test_tabular_tool_catalog -v` → 10/10 OK（2026-06-10 Reviewer 複核）
  - **AC-6 ⚠️**：本票 deliverable 未改主鏈腳本；`run_mvp_mainline_regression.py -v` 6/6 留合併前執行（G3）
- risk_level: low
- suggestions:
  - **G1**：`docs/tabular-tool-catalog-v1.md` §3 風險关键字改引用 JSON `risk_notes` 原文或加「以 JSON 為準」
  - **G2**：`tests/test_tabular_tool_catalog.py` 將 `orchestrate.mainline_regression` 納入 `_REQUIRED_TOOL_IDS`，或 spec 標 optional meta-tool
  - **G3**：合併前跑 `python scripts/run_mvp_mainline_regression.py -v` → 6/6 OK
  - **G4–G5**：未來正式 cleaner 須新 `tool_id`；`clean.phase_demo` 維持 `demo_non_prod` / `phase_like_only`；T2 Selector 須讀 `risk_notes` 防誤路由
  - **G6**：state §2 skeleton / B_REPORT verification 滯後（Scribe 本回合補 D_REPORT；Orchestrator 關票時更新 STATE）

---

## D_REPORT

- docs_updates:
  - **交付**：Tabular MVP 工具層 SSOT — `tools/tabular_tool_catalog_v1.json`（11 條 enabled 工具）+ 人讀 `docs/tabular-tool-catalog-v1.md`；機器驗證 `tests/test_tabular_tool_catalog.py`（10/10 OK）。
  - **用途**：W3-TL-T2 Selector 與 W3-TL-T3 Executor 的 `tool_id`、`module_path`、`applicable_conditions`、`risk_notes` 權威來源；與 Gov Registry（`obs.*`/`kb.*`）、Phase 8.8 編排（`llm.*`）、Wave8 `skill-clean-*` **分軌**（JSON 不含上述 ID）。
  - **何時必讀**：新增／變更 tabular CLI 或 `app/local_ui.py`；開 Selector／Executor 票；onboarding 需對照 MVP 主鏈 entrypoints 時。
  - **何時必跑**：改 catalog JSON 或 markdown 後 → `python -m unittest tests.test_tabular_tool_catalog -v`；合併前 → `python scripts/run_mvp_mainline_regression.py -v`（6/6）。
  - **non-blocking gaps（Reviewer G1–G3）**：§3 風險关键字與 JSON drift；測試未鎖 `orchestrate.mainline_regression`；合併前主鏈回歸未在本票 Reviewer 回合執行。
- progress_entry: |
    [W3-TL-T1] Tabular Tool Catalog v1 · accepted_with_gaps · SSOT `tools/tabular_tool_catalog_v1.json` + `docs/tabular-tool-catalog-v1.md`（11 tools）；與 Phase 8.8 W3-T1–T4 分軌。驗證：tests.test_tabular_tool_catalog 10/10 OK；主鏈回歸待合併前 G3。
- followup_suggestions:
  - W3-TL-T2 已接續：Selector 消費 catalog `tool_id` + `applicable_conditions` + `risk_notes`
  - 可選 follow-up：G1 文檔對齊；G2 測試鎖定 mainline_regression；`tabular_tool_catalog_loader.py`（FRAME 可選，未交付）

---

## §8 注意事項

- **分軌**：本票僅涵蓋 tabular MVP 工具層（gate / clean / bundle / E2E）；與既有 Phase 8.8 `W3-T1`–`W3-T4` 編排 Tool Layer 分軌，票號前綴 `W3-TL-*` 僅用於 Tabular MVP。
- **主鏈守護**：合併前必跑 `python scripts/run_mvp_mainline_regression.py -v`。
- **下游**：W3-TL-T2 Selector 依賴本票 `tool_id` 與 `applicable_conditions`。

---

## O_NOTES

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-10 | orchestrator (W3-COORD) | 開票 FRAME / Minimal Read Set / B_REPORT 初版 | 本檔 |
