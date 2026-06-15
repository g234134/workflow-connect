# TICKET STATE · W3-T1 · Tool Catalog v1 權威化（版本 + 校驗 + Gov 對照）

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 3 - Tool Layer

---

## FRAME

- Title: Tool Catalog v1 權威化（版本 + 校驗 + Gov 對照）
- Goal: 單一權威 catalog 含 catalog_revision、schema 校驗、與 B-F1 Gov catalog 建立映射表。
- Scope:
  - 固化 shared/schemas/tool_catalog_v1.json + core/tool_catalog.py
  - 每工具含 tool_id、enabled、executor_binding、risk_level、cost_hint
  - 新增 docs/TOOL_CATALOG_AUTHORITY.md：Gov obs.*/kb.* 與 orchestration 對照
  - 測試 tests.test_tool_layer_schemas 全綠
- NonScope:
  - 動態 MCP 註冊
  - 合併 Wave8 skill-clean-* SKU
  - 改 LangGraph 圖
- AllowedPaths:
  - shared/schemas/tool_catalog_v1.json
  - core/tool_catalog.py
  - docs/TOOL_CATALOG_AUTHORITY.md
  - tests/test_tool_layer_schemas.py
- BlockedPaths:
  - skills/gov_cards/*（唯讀對照）
  - AGENTS.md
- Dependencies:
  - 04_Workflows/SPEC_tool_catalog_and_selector_v1.md
  - B-F1 Gov Tool Registry（對照）
  - W2-T4（回歸基線穩定）
- Risks:
  - 雙份 catalog（戰車根 vs 暗部）漂移 → 本票宣告 SSOT
  - enabled: false 被 selector 選中 → 校驗層攔截
- Observability:
  - logs: catalog load revision、enabled_count
  - metrics: N/A
  - traces: N/A
- OutputArtifacts:
  - shared/schemas/tool_catalog_v1.json
  - core/tool_catalog.py
  - docs/TOOL_CATALOG_AUTHORITY.md
  - unittest 擴充
- AcceptanceCriteria:
  - load_catalog() → ok: true，tool_count >= 6，catalog_revision 有值
  - 重複 tool_id 校驗失敗可測
  - mapping 表覆蓋 Tool Flow 白名單工具
- VerificationCommands:
  - `python -m unittest tests.test_tool_layer_schemas -v`
    - 預期：全綠
  - `load_catalog() 手動或測試`
    - 預期：tool_count >= 6

---

## STATE

- overall_status: accepted_with_gaps
- implementation_status: review_passed
- current_owner: orchestrator
- next_action: closed — 後續追蹤：selector 整合（enabled:false 攔截）、暗部 venv catalog sync、MCP 動態註冊、Wave8 SKU 合 schema（見 D_REPORT / C_REPORT gaps）
- last_updated: 2026-06-15 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

> **Orchestrator 預填（2026-06-15）**：Implementer 依「Orchestrator 施工說明」施工；完成後更新 deliverable 欄位。**保留本節歷史，不刪除。**

### Orchestrator 施工說明（Implementer 依此執行）

**Goal（1 句）**：確立 Phase 8.8 編排 Tool Layer 的**單一權威 catalog**（`shared/schemas/tool_catalog_v1.json` + `core/tool_catalog.py`），含 `catalog_revision`、schema 校驗、與 B-F1 Gov catalog 的對照映射表。

**Files to touch**

- `shared/schemas/tool_catalog_v1.json`（**新建** · wire contract；`schema_version` + `catalog_revision` + `tools[]`；每工具含 `tool_id`、`enabled`、`executor_binding`、`risk_level`、`cost_hint`）
- `core/tool_catalog.py`（**新建** · `load_catalog() -> dict`；校驗 schema_version、去重 `tool_id`、`enabled: false` 仍載入但可被 selector 層攔截）
- `docs/TOOL_CATALOG_AUTHORITY.md`（**新建** · SSOT 宣告 + 四軌分軌表：Tabular MVP / Gov Registry / Phase 8.8 / Wave8 SKU；Gov `obs.*`/`kb.*` ↔ orchestration 映射）
- `tests/test_tool_layer_schemas.py`（**新建** · load 成功、重複 tool_id 失敗、enabled 計數、`catalog_revision` 存在）

**Non-Scope（Implementer 不得做）**

- 動態 MCP 註冊、pip 安裝、執行期擴池
- 合併 Wave8 `skill-clean-*` SKU 進本 catalog JSON
- 改 LangGraph 圖、暗部 selector 生產行為、`skills/gov_cards/*`（**唯讀對照**）
- 與 `W3-TL-*` Tabular catalog（`tools/tabular_tool_catalog_v1.json`）rename／merge
- 改 `AGENTS.md`

**Steps**

1. 對照 `04_Workflows/SPEC_tool_catalog_and_selector_v1.md` §3–§4 與 `tests/test_gov_tool_registry.py` 白名單工具，起草 `tool_catalog_v1.json`（**tool_count >= 6**，含至少一個 `enabled: false` 用例）。
2. 實作 `core/tool_catalog.py`：`load_catalog(repo_root=None)` 回傳 `{ok, message, catalog_revision, tool_count, tools, ...}` 穩定 dict 形狀。
3. 撰寫 `TOOL_CATALOG_AUTHORITY.md`：明確 SSOT 路徑、與 `docs/tabular-tool-catalog-v1.md` / `docs/SKILL_CATALOG_OVERVIEW.md` 分軌；映射表覆蓋 Tool Flow 白名單（`obs.*`/`kb.*`/`llm.*` 等 SPEC 提及項）。
4. 新增 unittest：happy path、duplicate `tool_id` raises/returns `ok: false`、revision 非空。
5. B_REPORT 記錄 `load_catalog()` 手動或測試輸出語意（tool_count、enabled_count）。

**Tests / Verification**

- `python -m unittest tests.test_tool_layer_schemas -v` → 全綠
- 測試或 one-liner：`load_catalog()` → `ok: true`，`tool_count >= 6`，`catalog_revision` 有值
- 目視：`TOOL_CATALOG_AUTHORITY.md` 映射表與 Gov cards spot-check 一致（不要求 100% Gov 卡入 catalog）

**Deferred / out-of-scope**

- 暗部 venv 第二份 catalog 同步腳本（僅文檔宣告 SSOT 在戰車根）
- selector 消費 `enabled: false` 攔截的整合測試（W3-T2+ 或 WB-T*）
- MCP 動態註冊、Wave8 SKU 合 schema

### Implementation Plan (initial)

- [x] 固化 tool_catalog_v1.json schema
- [x] 實作/收口 core/tool_catalog.py load + validate
- [x] 撰寫 TOOL_CATALOG_AUTHORITY.md 映射表
- [x] 擴充 test_tool_layer_schemas

### Files To Touch

- shared/schemas/tool_catalog_v1.json
- core/tool_catalog.py
- docs/TOOL_CATALOG_AUTHORITY.md
- tests/test_tool_layer_schemas.py

- changed_files:
  - `shared/schemas/tool_catalog_v1.json`（新建 · 8 tools · 1 enabled:false）
  - `core/tool_catalog.py`（新建 · `load_catalog()` + `validate_catalog_document()`）
  - `docs/TOOL_CATALOG_AUTHORITY.md`（新建 · Phase 8.8 / Tabular / Gov / Wave8 分軌）
  - `tests/test_tool_layer_schemas.py`（新建 · happy/duplicate/missing fields）
- artifacts:
  - SSOT catalog JSON `catalog_revision: 1.0.0`
  - Authority doc with Gov `obs.*`/`kb.*` mapping table
- verification:
  - `python -m unittest tests.test_tool_layer_schemas -v` → **6 tests OK**
  - `python -c "from core.tool_catalog import load_catalog; import json; print(json.dumps(load_catalog(), indent=2))"` → `ok: true`, `tool_count: 8`, `enabled_count: 7`, `catalog_revision: 1.0.0`
- behavior_notes: `browser.dom_task` 為 `enabled: false` 用例；duplicate `tool_id` 與缺欄位由 `validate_catalog_document` 回傳 `ok: false` + `message`；未 merge Tabular / gov_cards
- deferred_items: 暗部 venv catalog 同步腳本；selector 消費 `enabled: false` 整合測試（W3-T2+）；MCP 動態註冊；Wave8 SKU 合 schema

---

## C_REPORT

<!-- Reviewer 填：審查結論；只寫本區塊，不改 code -->

> **Orchestrator 預填草稿（2026-06-15）**：Reviewer 依 AC 勾選後填 `conclusion`。

### Reviewer Checklist（對照 FRAME AcceptanceCriteria）

| AC | 檢查項 | 通過條件 |
|----|--------|----------|
| **AC-1** | `load_catalog()` 成功 | `ok: true`；`tool_count >= 6`；`catalog_revision` 非空（Reviewer 重跑 unittest 或 spot-check B_REPORT verification） |
| **AC-2** | 重複 `tool_id` 校驗 | 測試覆蓋 duplicate 失敗路徑；回傳 `ok: false` + 可讀 `message` |
| **AC-3** | 映射表覆蓋白名單 | `TOOL_CATALOG_AUTHORITY.md` 含 Gov `obs.*`/`kb.*` 與 orchestration 對照；與 SPEC §3 一致 |
| **AC-4** | 分軌邊界 | 未 merge Tabular JSON / gov_cards；文檔明示 SSOT vs `tools/tabular_tool_catalog_v1.json` |
| **AC-5** | 工具欄位完整 | 每 catalog 工具含 `tool_id`、`enabled`、`executor_binding`、`risk_level`、`cost_hint` |
| **AC-6** | BlockedPaths | 未改 `skills/gov_cards/*`、`AGENTS.md`、LangGraph |

### 結論門檻

- **`accepted`**：AC-1～AC-6 全 ✅；unittest 全綠；無 blocking。
- **`accepted_with_gaps`**：AC-1/2/5/6 ✅；AC-3 映射表缺少數非白名單工具或 AC-4 文檔 cross-ref 可再補；**deferred 項已列 B_REPORT**。
- **`needs_changes`**：AC-1 或 AC-2 ❌（load 失敗、校驗漏洞、tool_count < 6）。
- **`rejected`**：merge Tabular/Gov catalog、改 BlockedPaths、或觸 `core/ask_rag_selector` 等禁區。

- conclusion: accepted_with_gaps
- blocking_issues: 無
- checks_summary: |
    - **AC-1** ✅ 達成 — Reviewer 重跑 `tests.test_tool_layer_schemas` 6/6 OK；`load_catalog()` → `ok: true`, `tool_count: 8`, `catalog_revision: 1.0.0`。
    - **AC-2** ✅ 達成 — `test_duplicate_tool_id_fails` 覆蓋；`validate_catalog_document` 回傳 `ok: false` + `duplicate tool_id` message。
    - **AC-3** ✅ 達成 — `docs/TOOL_CATALOG_AUTHORITY.md` §2 含 Gov `obs.*`/`kb.*` 與 orchestration 映射表；對齊 SPEC Tool Flow 白名單。
    - **AC-4** ✅ 達成 — 四軌分軌表明示 SSOT vs Tabular / Gov / Wave8；未 merge `tools/tabular_tool_catalog_v1.json` 或 `gov_cards`。
    - **AC-5** ✅ 達成 — 8 工具均含 `tool_id`、`enabled`、`executor_binding`、`risk_level`、`cost_hint`；含 `browser.dom_task` `enabled: false` 用例。
    - **AC-6** ✅ 達成 — 未改 `skills/gov_cards/*`、`AGENTS.md`、LangGraph。
- risk_level: low
- gaps: |
    - selector 消費 `enabled: false` 攔截的整合測試（W3-T2+ 或 WB-T*）。
    - 暗部 venv 第二份 catalog 同步腳本。
    - MCP 動態註冊、Wave8 `skill-clean-*` SKU 合 schema。
- suggestions: |
    1. W3-T2+ 或 WB-T* 票整合 selector 與 `enabled: false` 攔截。
    2. 暗部 catalog 同步腳本另票；本票 SSOT 已在戰車根宣告。

---

## D_REPORT

> **Scribe skeleton（2026-06-15）** — 基於 Reviewer `accepted_with_gaps`；Orchestrator 關票前為草稿。

- **Summary**: Phase 8.8 Tool Catalog SSOT 落地：`shared/schemas/tool_catalog_v1.json`（8 tools）、`core/tool_catalog.py`（`load_catalog` + `validate_catalog_document`）、`docs/TOOL_CATALOG_AUTHORITY.md`（四軌分軌 + Gov 映射）、`tests/test_tool_layer_schemas.py`（6 tests OK）。
- **Scope**: 戰車根 catalog wire contract 與 loader；不負責 Tabular catalog merge、Gov cards 寫入、LangGraph 改動、MCP 動態註冊。
- **Deferred**: selector `enabled: false` 整合測試；暗部 venv catalog 同步；MCP 註冊；Wave8 SKU 合 schema。

- docs_updates: 建議更新 `docs/WAVE_PROGRESS_DASHBOARD.md` Wave 3-TL 註解（W3-T1 SSOT `accepted_with_gaps`）；Progress 末尾追加條目。
- progress_entry: W3-T1 Tool Catalog 權威化 Reviewer `accepted_with_gaps` — SSOT JSON/loader/authority doc/tests 6/6 OK；selector 整合與暗部 sync deferred。
- followup_suggestions: W3-T2+ selector 消費 catalog；暗部 sync 腳本另票。

---

## O_NOTES

> **O 區**：Orchestrator 維護 run log 與戰報連結；Observe / Operate 計畫。

### Observability Plan

- SSOT 路徑寫入 TOOL_CATALOG_AUTHORITY.md

### Rollout / Ops Notes

- SSOT 路徑寫入 TOOL_CATALOG_AUTHORITY.md

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-07 | orchestrator | 開票 FRAME/STATE/B_REPORT 預填 | 本檔 |
| 2026-06-15 | orchestrator | B_REPORT 施工說明 + C_REPORT Reviewer checklist 預填；STATE → implementer in_progress | 本檔 |
| 2026-06-15 | reviewer | C_REPORT `needs_changes` — catalog SSOT 四檔未交付；交棒 implementer | 本檔 |
| 2026-06-15 | implementer | B_REPORT deliverables 回填 — catalog JSON/loader/authority/tests | 本檔 |
| 2026-06-15 | reviewer | C_REPORT `accepted_with_gaps` — AC-1～AC-6 達成；selector 整合 deferred；交棒 scribe | 本檔 |
| 2026-06-15 | scribe | D_REPORT filled based on reviewer acceptance (with gaps) | 本檔 |
