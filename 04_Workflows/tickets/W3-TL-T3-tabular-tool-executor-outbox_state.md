# TICKET STATE · W3-TL-T3 · Tabular Tool Executor + Outbox v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 3 · Tool Layer · **Tabular MVP**

---

## FRAME

- Title: Tabular Tool Executor + Outbox v1（dry-run / 執行 / 錯誤收斂）
- Goal: 以一致介面調用 Tabular Catalog 中 **enabled** 工具，並將每次 run 結果寫入標準 outbox（per-run JSON + 可選 events.jsonl），供後續 agent / UI 消費；**不**改 MVP 主鏈 CLI 語意。
- Scope:
  - 新建 `tools/tabular_tool_executor.py` — `execute_tabular_tool(...) -> dict`；支援 `dry_run: bool`
  - 新建 `tools/tabular_outbox_writer.py`（或合併於 executor 模組）— 寫入 outbox
  - 新建 `docs/tabular-tool-outbox-spec.md` — 定義：
    - `case_ref` / `run_id` 命名（對齊 `intake.json` 的 `client_ref` + `case_id`，或 `case_dir` 相對路徑 slug）
    - 必備欄位：`schema_version`, `case_ref`, `run_id`, `tool_id`, `started_at`, `finished_at`, `ok`, `exit_code`, `message`, `artifacts[]`（`path` 或 `logical_key`）
    - per-run 路徑：**必做** `outbox/<case_ref>/<run_id>.json`
    - append-only：**可選** `outbox/events.jsonl`（每行含 `case_ref`, `run_id`, `tool_id`, `result.ok` 等）
  - 執行方式：subprocess 包裝既有 CLI 或 import 庫函式（與 catalog `executor_binding` 對齊）；錯誤收斂為 `{ok, message, tool_id, exit_code, artifacts[], stderr_tail?}`
  - 新建 `tests/test_tabular_tool_executor.py`（dry-run + 真實執行 `demo_phase` 單步 gate 或 clean；失敗路徑缺 intake）
  - 新建 `outbox/.gitkeep` 或 `.gitignore` 規則（避免 commit 真實 run 產物；fixture 除外）
  - dry-run：只產 plan + outbox stub，不 spawn 子進程（或 spawn `--help` 級別 — Implementer 擇一並寫入 spec）
- NonScope:
  - Langfuse / `task_runs` / DLQ / `structured_errors` patch（Phase 8.8 `W3-T3` / `W3-T4`）
  - outbox replay CLI（可留 W3-TL-T4 follow-up）
  - 修改 `clean_phase_demo.py` / gate / bundle **邏輯**
  - 修改 `scripts/run_case_e2e_validation.py` 預設走 Executor
  - rename / 觸碰 `W3-T1`–`W3-T4` 與 `core/orchestration_bridge_outbox.py`
  - `app/local_ui.py` 接入（除非尚書省另授權；預設 non-goal）
- AllowedPaths:
  - `tools/tabular_tool_executor.py`
  - `tools/tabular_outbox_writer.py`（可選獨立檔）
  - `docs/tabular-tool-outbox-spec.md`
  - `tests/test_tabular_tool_executor.py`
  - `outbox/.gitkeep`、`outbox/.gitignore`（若需要）
  - `tests/fixtures/outbox/`（樣例 JSON，可選）
  - `04_Workflows/tickets/W3-TL-T3-tabular-tool-executor-outbox_state.md`
- BlockedPaths:
  - `scripts/run_case_e2e_validation.py`（主鏈 driver）
  - `notebooks/csv_cleaning/clean_phase_demo.py` 等 **業務邏輯** 修改
  - `HARNESS_CONSTITUTION.md`、`ENGINEERING_CONTRACT.md`、`AGENTS.md`、`.cursor/rules/*`
  - `04_Workflows/tickets/W3-T1_state.md`–`W3-T4_state.md`
  - `core/tool_executor.py`、`core/orchestration_bridge_outbox.py`（Phase 8.8）
- Dependencies:
  - **W3-TL-T1**（catalog + `executor_binding`）
  - **W3-TL-T2**（selector 輸出 `candidate_tools[]` — Executor 可接受显式 `tool_id` 或 selector 結果）
  - `docs/mvp-standard-trace-path.md`
- Risks:
  - subprocess 改變 cwd / env → 固定 repo 根；禁硬編磁碟路徑
  - outbox 寫入 git 污染 → `.gitignore` + 測試用 tmpdir
  - 真實 execute 改 case 產物 → 測試用 tmp case 或 dry-run 為主；merge 前仍跑 mainline regression 於 **標準 fixture**（未改）
- Observability:
  - logs: `tool_id`, `run_id`, `dry_run`, `exit_code`
  - metrics: N/A
  - traces: N/A
- OutputArtifacts:
  - `tools/tabular_tool_executor.py`
  - `tools/tabular_outbox_writer.py`（若獨立）
  - `docs/tabular-tool-outbox-spec.md`
  - `tests/test_tabular_tool_executor.py`
  - `outbox/.gitkeep`（及可選 `.gitignore`）
- AcceptanceCriteria:
  - **AC-1**：`execute_tabular_tool(..., dry_run=True)` → `ok: true`，outbox JSON 含 plan / stub，**無**副作用（或 spec 定義之最小副作用）
  - **AC-2**：對 `demo_phase` 執行 catalog 中一步（如 `validate.eligibility`）→ outbox 寫入 `outbox/<case_ref>/<run_id>.json`，欄位齊全
  - **AC-3**：失敗路徑（缺 `intake.json`）→ `ok: false`，outbox 仍記錄 `message` / `exit_code`
  - **AC-4**：`docs/tabular-tool-outbox-spec.md` 定義 `case_ref` / `run_id` 與 `cases/index.json` / `intake.json` 對齊規則
  - **AC-5**：（可選）`outbox/events.jsonl` append 一行 / run；若未實作須在 B_REPORT 標 deferred
  - **AC-6**：`python -m unittest tests.test_tabular_tool_executor -v` 全綠
  - **AC-7（主鏈守護）**：`python scripts/run_mvp_mainline_regression.py -v` → 6/6 OK，exit 0
- VerificationCommands:
  - `python -m unittest tests.test_tabular_tool_executor -v`
    - 預期：全綠
  - `python scripts/run_mvp_mainline_regression.py -v`
    - 預期：6/6 OK，exit 0

---

## Minimal Read Set

| # | 路徑 | 用途 |
|---|------|------|
| 1 | `docs/governance-constitution-v1.md` §1、§3、§5 | dict 契約、禁硬編路徑 |
| 2 | 本檔 FRAME + AllowedPaths | 硬邊界 |
| 3 | `04_Workflows/tickets/W3-TL-T1-tabular-tool-catalog_state.md` | catalog binding |
| 4 | `04_Workflows/tickets/W3-TL-T2-tabular-tool-selector_state.md` | selector 輸出形狀 |
| 5 | `tools/tabular_tool_catalog_v1.json` | executor_binding |
| 6 | `docs/mvp-standard-trace-path.md` | case_ref 對照 |
| 7 | `scripts/check_case_eligibility.py`、`notebooks/csv_cleaning/clean_phase_demo.py` | subprocess 契約（唯讀） |
| 8 | `04_Workflows/tickets/W3-T4_state.md`（唯讀） | Phase 8.8 outbox replay **分軌**對照 |

---

## §2 skeleton / placeholder

| 項 | 狀態 | 說明 |
|----|------|------|
| `tools/tabular_tool_executor.py` | **[待實作]** | execute + dry-run |
| `tools/tabular_outbox_writer.py` | **[placeholder · 可選獨立]** | 可併入 executor |
| `outbox/<case_ref>/<run_id>.json` | **[待實作 · 必做]** | per-run SSOT |
| `outbox/events.jsonl` | **[placeholder · 可選]** | append-only |
| outbox replay CLI | **[placeholder · W3-TL-T4]** | 本票 non-goal |

> **分軌聲明（§2 / §8）**：本票僅涵蓋 tabular MVP 工具層（gate / clean / bundle / E2E）；與既有 Phase 8.8 `W3-T1`–`W3-T4` 編排 Tool Layer 分軌，票號前綴 `W3-TL-*` 僅用於 Tabular MVP。

---

## STATE

- overall_status: draft
- current_owner: orchestrator
- next_action: Assign to Implementer — **待 W3-TL-T1（+ 建議 T2）就緒** 後實作 executor + outbox spec + tests
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

- **本票（W3-TL-T3）**：戰車根 Tabular outbox = `outbox/<case_ref>/<run_id>.json`（+ 可選 `events.jsonl`）；**不接** Langfuse / DLQ。
- **既有 draft W3-T3 / W3-T4**：暗部 `tool_decision_log_patch`、`orchestration_bridge_outbox replay` — **不同 schema / 路徑**；禁止混用或 rename。
- **主鏈**：E2E driver 仍直接 subprocess 既有 CLI；Executor 為 **平行** 統一介面，非本票替換主鏈。

### Implementation Plan (initial)

- [ ] 定義 outbox schema + `case_ref` / `run_id` 規則（spec）
- [ ] 實作 `execute_tabular_tool`（dry-run + execute）+ outbox writer
- [ ] 測試：dry-run、demo_phase 單步、失敗路徑
- [ ] （可選）`outbox/events.jsonl`
- [ ] `outbox/.gitkeep` / `.gitignore`
- [ ] `run_mvp_mainline_regression.py -v` 主鏈守護

### Files To Touch

- `tools/tabular_tool_executor.py`
- `tools/tabular_outbox_writer.py`（可選）
- `docs/tabular-tool-outbox-spec.md`
- `tests/test_tabular_tool_executor.py`
- `outbox/.gitkeep`

- changed_files: **[待實作]**
- artifacts: **[待實作]**
- verification: **[待實作]** — 須含 `tests.test_tabular_tool_executor` 與 `run_mvp_mainline_regression.py -v`
- behavior_notes: **[待實作]**
- deferred_items: outbox replay / Local UI 展示 → W3-TL-T4 或未來票

---

## C_REPORT

- conclusion: **accepted_with_gaps**
- blocking_issues: 無
- checks_summary:
  - **AC-1 ✅**：`dry_run=True` → `ok: true`，含 plan / stub，無 subprocess 副作用、無 outbox 檔
  - **AC-2 ✅**：`demo_phase` + `validate.eligibility` 真實執行 → `outbox/<case_ref>/<run_id>.json` 欄位齊全；`events.jsonl` 已 append
  - **AC-3 ✅**：缺 `intake.json` 失敗路徑 → `ok: false`，outbox 仍記錄 `message` / `exit_code`
  - **AC-4 ✅**：`docs/tabular-tool-outbox-spec.md` 定義 `case_ref` / `run_id` 與 `intake.json` / `cases/index.json` 對齊
  - **AC-5 ✅**：`outbox/events.jsonl` 已實作（FRAME 可選項已交付）
  - **AC-6 ✅**：`python -m unittest tests.test_tabular_tool_executor -v` → 6/6 OK
  - **AC-7 ⚠️**：`run_mvp_mainline_regression.py -v` 6/6 未在本票 Reviewer／Implementer 回合執行 — 留合併前硬門檻（G1）
- risk_level: low
- suggestions:
  - **G1**：合併前跑 `python scripts/run_mvp_mainline_regression.py -v` → 6/6 OK
  - **G2**：真實 execute 測試以 `validate.eligibility` / `demo_phase` 為主；`clean.phase_demo` / bundle 等 CLI 未經 executor 整合測試 — 接 prod 前補票或擴測
  - **G3**：`validate.eligibility` 將 exit 0/1/2 均視為 `ok: true`（gate 語意）— spec 已述，下游消費者須讀 `exit_code`
  - **G4**：Tabular outbox（`outbox/`）與 Phase 8.8 `orchestration_bridge_outbox` **不同 schema／路徑** — 禁止混用 replay CLI
  - **G5**：outbox replay / Local UI 展示 → W3-TL-T4 或未來票（FRAME deferred）

---

## D_REPORT

- docs_updates:
  - **交付**：`tools/tabular_tool_executor.py`（`execute_tabular_tool`）+ `tools/tabular_outbox_writer.py` + `docs/tabular-tool-outbox-spec.md` + `tests/test_tabular_tool_executor.py`（6/6 OK）+ `outbox/.gitkeep` + `outbox/.gitignore`。
  - **用途**：以一致介面調用 catalog **enabled** 工具（subprocess / dry-run）；每次 run 寫入 `outbox/<case_ref>/<run_id>.json`（schema `tabular_outbox_v1`）及可選 `outbox/events.jsonl`；**不**替換 MVP 主鏈 E2E driver、**不接** Langfuse / DLQ（Phase 8.8 `W3-T3`/`W3-T4` 分軌）。
  - **何時必讀**：改 executor 綁定、outbox schema、或 `case_ref`/`run_id` 規則；接 Selector 輸出執行工具；規劃 outbox replay（W3-TL-T4）時。
  - **何時必跑**：改 executor/outbox writer 後 → `python -m unittest tests.test_tabular_tool_executor -v`；合併前 → `python scripts/run_mvp_mainline_regression.py -v`（G1）。
  - **分軌聲明**：戰車根 Tabular outbox ≠ Phase 8.8 `orchestration_bridge_event_v1` / replay；票號 `W3-TL-*` 僅 Tabular MVP，與 `W3-T1`–`W3-T4` draft 禁止 rename／合併。
  - **non-blocking gaps（Reviewer G1–G2）**：主鏈回歸未跑；clean/bundle 工具未經 executor 真實執行整合測；replay CLI deferred。
- progress_entry: |
    [W3-TL-T3] Tabular Tool Executor + Outbox v1 · accepted_with_gaps · `execute_tabular_tool` + outbox spec + 6 tests OK；events.jsonl 已交付。與 Phase 8.8 outbox 分軌。Gaps：AC-7 主鏈回歸待合併前；clean/bundle executor 整合測待補。
- followup_suggestions:
  - 合併前 G1：主鏈回歸 6/6
  - W3-TL-T4（可選）：outbox replay CLI / Local UI 展示
  - 擴測：`clean.phase_demo`、`export.delivery_bundle` 經 executor 真實路徑

---

## §8 注意事項

- **分軌**：本票僅涵蓋 tabular MVP 工具層；與 Phase 8.8 `W3-T1`–`W3-T4` 分軌；`W3-TL-*` 前綴僅 Tabular MVP。
- **Outbox 與編排層**：Phase 8.8 `orchestration_bridge_event_v1` / replay CLI **不在本票**。
- **主鏈守護**：合併前必跑 `run_mvp_mainline_regression.py -v`。
- **依賴順序**：T1 catalog → T2 selector（建議）→ T3 executor；T3 最低僅需 T1 + 显式 `tool_id`。

---

## O_NOTES

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-10 | orchestrator (W3-COORD) | 開票 FRAME / Minimal Read Set / B_REPORT 初版 | 本檔 |
