# TICKET STATE · BATCH-MVP-01 · Batch orchestrator loader MVP

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

<!-- Orchestrator 填 · 2026-06-15 凍結；後續變更僅 Orchestrator 顯式更新 -->

- Goal: 交付 batch orchestrator MVP——以 JSON Schema 驗證 subtask／batch manifest，並提供結構化 `dict` loader API（`ok` / `data` / `errors`）。
- Scope:
  - 新增 `04_Workflows/_templates/batch_subtask.schema.json`（`$defs.subtask` + `$defs.batch_manifest`）
  - 新增 `04_Workflows/_batch_orchestrator/loader.py`：`validate_subtask`、`validate_batch_manifest`、`load_subtask`、`load_batch_manifest`、`load_batch_document`、`default_schema_path`
  - 新增 `04_Workflows/_batch_orchestrator/__init__.py` 匯出上述 API
  - 新增 `tests/test_batch_loader.py`：合法／缺欄／enum／dependency／manifest 一致性
  - 對外 API 名稱：`load_subtasks_from_path`、`load_batch_manifest_from_path`（可經 alias 對齊實作名 `load_subtask` / `load_batch_manifest`）
  - subtask 必填鍵含 `preferred_model`（允許 `null` 值）
- NonScope:
  - 不建 CLI runner、dispatch executor、DB 持久化或 Multi-Chat 排程器
  - 不改 `core/*`、`skills/*`、`AGENTS.md`、CI workflow
  - 不支援 document root 為純 subtasks array（root 須為 JSON object；manifest 用 `subtasks` 陣列）
- AllowedPaths:
  - `04_Workflows/_templates/batch_subtask.schema.json`
  - `04_Workflows/_batch_orchestrator/**`
  - `tests/test_batch_loader.py`
  - `04_Workflows/tickets/BATCH-MVP-01_state.md`（Implementer 僅 B_REPORT 區塊）
- BlockedPaths:
  - `core/*`、`skills/*`、`observability/*`
  - `AGENTS.md`、`ENGINEERING_CONTRACT.md`、`HARNESS_CONSTITUTION.md`
  - `.github/workflows/*`、`config/*`
  - 其他 `04_Workflows/tickets/*_state.md`（本票除外）
- Dependencies: repo 既有 `jsonschema` / `referencing`（loader import 失敗時回傳結構化錯誤，不崩潰）
- AcceptanceCriteria:
  - AC-1：schema 覆蓋 subtask 與 batch_manifest；`preferred_model` 為 required（值可為 `null`）
  - AC-2：loader 對 path／JSON string／mapping 皆回傳穩定 `dict`（含 `ok`、`data`、`errors`）
  - AC-3：`load_batch_document` 依 payload 是否含 `subtasks` 自動分流 manifest vs 單 subtask
  - AC-4：dependency 語意驗證（自引用、manifest 內未知 id、parent_ticket_id 不一致）
  - AC-5：`python -m unittest tests.test_batch_loader -v` 全綠（含省略 `preferred_model` → `ok: false`；`preferred_model: null` → `ok: true`）
  - AC-6：公開 API 名稱與 FRAME／B_REPORT 一致（alias 可接受）

---

## STATE

<!-- Orchestrator 維護 · FRAME 已於 2026-06-15 凍結 -->

- overall_status: ready_for_scribe
- current_owner: scribe
- next_action: scribe_sync_b_report_and_write_d_report
- last_updated: 2026-06-15 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: pending
- ac_status:
  - AC-1: met
  - AC-2: met
  - AC-3: met
  - AC-4: met
  - AC-5: met
  - AC-6: met
- b_report_sync_strategy: path_a
- b_report_sync_note: |
    Orchestrator 採路徑 A（推薦）：Scribe 一次性授權同步票檔 B_REPORT 區塊。
    來源：第二輪 C_REPORT（verdict: approved）＋ Implementer chat 第二輪 B_REPORT 草稿。
    同步欄位：changed_files / artifacts / verification / behavior_notes / deferred_items。
    Implementer 不再修改 B_REPORT（避免多角色交叉寫同一區）。
- orchestrator_note: |
    本票 loader MVP 完成；schema 與 loader 合約固定。
    第二輪 Reviewer verdict: approved；程式層 R1–R3 已收口，無開放必改項。
    R4 僅為票檔 B_REPORT 文案同步，已委派 Scribe（path_a）。
    殘餘風險見 C_REPORT residual_risks（breaking change: 省略 preferred_model；venv 須 gov_core）。
    下一步：Scribe 同步 B_REPORT → 撰寫 D_REPORT → Progress 末尾追加。

> **凍結聲明**：FRAME 與本輪 Implementer／Reviewer 工作邊界一致；Implementer／Reviewer **不得**改 FRAME。後續 scope 變更須 Orchestrator 顯式更新 FRAME 並留痕。

---

## B_REPORT

<!-- Implementer 第二輪施工（R1–R4 · 2026-06-15） -->
- changed_files:
  - `04_Workflows/_templates/batch_subtask.schema.json`（修改：`preferred_model` 列入 `required`）
  - `04_Workflows/_batch_orchestrator/loader.py`（修改：公開 API alias）
  - `04_Workflows/_batch_orchestrator/__init__.py`（修改：`__all__` 匯出 alias）
  - `tests/test_batch_loader.py`（修改：`preferred_model` 缺欄／null 測試）
- artifacts:
  - `batch_subtask.schema.json` — subtask + batch_manifest JSON Schema（Draft 2020-12）；`preferred_model` required（值可為 `null`）
  - `_batch_orchestrator/loader.py` — validate / load API + FRAME 公開名稱 alias
- verification:
  - `python -m pytest tests/test_batch_loader.py -q` → **12 passed**（gov_core venv）
  - `python -m unittest tests.test_batch_loader -v` → **12/12 OK**
  - 抽檢：省略 `preferred_model` → `ok: false`；`preferred_model: null` → `ok: true`
  - 抽檢：`from _batch_orchestrator import load_subtasks_from_path, load_batch_manifest_from_path` 可 import 且與 `load_subtask` / `load_batch_manifest` 為同一物件
- behavior_notes:
  - 實作函式名：`load_subtask`、`load_batch_manifest`、`load_batch_document`
  - 公開 API alias：`load_subtasks_from_path = load_subtask`、`load_batch_manifest_from_path = load_batch_manifest`；`__init__.py` 均已 export
  - `preferred_model` 為 subtask required 鍵；省略 → `ok: false`；`null` → `ok: true`
  - `_parse_json_source`：document root **須為 JSON object**；**不**支援 root 為純 subtasks array（manifest 以 object 內 `subtasks` 陣列承載）
  - manifest 載入時逐 subtask 做 dependency 與 `parent_ticket_id` 交叉檢查
  - 驗收須在具 `jsonschema` 的環境（gov_core venv）；無依賴時 loader 回傳結構化 `invalid schema` 錯誤
- deferred_items:
  - 無（R1–R4 本輪已收口）

---

## C_REPORT

<!-- Reviewer 填 · 第二輪審查 · 2026-06-15 定稿 -->

- conclusion: approved
- blocking_issues: 無（第一輪 R1–R3 已關閉；R4 文案待 Scribe／Orchestrator 同步票檔 B_REPORT，不阻塞程式驗收）
- checks_summary: |
    - **邊界**：第二輪 diff 僅限 AllowedPaths（schema、`_batch_orchestrator/**`、`tests/test_batch_loader.py`）；未觸 FRAME／STATE／C_REPORT／BlockedPaths — 通過。
    - **R1 / AC-1**：`$defs.subtask.required` 已含 `"preferred_model"`（schema L23）；型別仍為 `["string", "null"]` — 通過。
    - **R2 / AC-5**：`test_missing_preferred_model`（省略 → `ok: false`）、`test_preferred_model_null_accepted`（`null` → `ok: true`）存在且語意正確 — 通過。
    - **R3 / AC-6**：`loader.py` L266–268 alias；`__init__.py` 匯出實作名與 alias；獨立驗證 `load_subtasks_from_path is load_subtask` 與 `load_batch_manifest_from_path is load_batch_manifest` 皆 `True` — 通過。
    - **AC-2 / AC-3 / AC-4**：第一輪既有行為未 regression；第二輪 12/12 測試全綠 — 通過。
    - **Rule 11**：Reviewer 獨立重跑 `pytest tests/test_batch_loader.py -q` → 12 passed；`python -m unittest tests.test_batch_loader -v` → 12 OK — 通過。
    - **R4 / 票檔 B_REPORT**：票檔 B_REPORT 仍為第一輪文案（缺 alias、`preferred_model` 敘述過時）；Implementer 於 chat 提供勘誤草稿，依 FRAME AllowedPaths 應由 Implementer 寫入 B_REPORT 或由 Scribe 代同步 — **非程式阻塞**，列收口待辦。
- risk_level: low
- residual_risks:
  - **Breaking change**：既有 subtask JSON 若省略 `preferred_model` 現為 `ok: false`；下游 fixture／manifest 須補欄（可 `null`）。
  - **venv 依賴**：無 `jsonschema` 環境 loader 回傳 `invalid schema: jsonschema is required...`（第一輪已知；CI 須在 gov_core venv 驗收）。
- suggestions:
  - **Orchestrator**：更新 STATE（`overall_status: ready_for_scribe`、`current_owner: scribe`、`status_by_role.implementer: done`、`status_by_role.reviewer: done`）。
  - **Implementer 或 Scribe**：將第二輪 B_REPORT 勘誤文案寫入票檔 B_REPORT 區塊（API alias、root object、`preferred_model` 必填語意、12/12 驗證結果）。
  - **Scribe**：依 D_REPORT 流程追加 Progress 末尾條目；可選在 `docs/` 或 runbook 交叉引用 batch loader API（若 FRAME 後續擴 scope）。
- first_round_archive: |
    第一輪 `approved_with_changes`（R1–R4）；第二輪關閉 R1–R3；R4 轉 Scribe 收口。

---

## D_REPORT

<!-- Scribe 填 · 2026-06-15 · 第二輪 Reviewer approved 後 -->

- docs_updates: 無（本票未新增 `docs/batch_orchestrator_mvp.md` 等說明文件；API 與行為以 `batch_subtask.schema.json`、`_batch_orchestrator/loader.py` 及票檔 B/C_REPORT 為 SSOT）
- progress_entry: BATCH-MVP-01：batch_subtask schema + loader MVP 完成；preferred_model required；12/12 tests OK（gov_core venv）。
- followup_suggestions:
  - 既有 subtask JSON fixture／manifest 若省略 `preferred_model` 須補欄（可設 `null`）— 見 C_REPORT residual_risks
  - 後續 batch orchestrator 票（CLI runner、dispatch executor）可選在 `docs/` 或 runbook 交叉引用 loader 公開 API
