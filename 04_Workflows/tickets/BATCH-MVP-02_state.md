# TICKET STATE · BATCH-MVP-02 · Batch subtask scheduler MVP

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

<!-- Orchestrator 填 · 2026-06-15 凍結；2026-07-13 補 Phase 影響欄（不改 Scope） -->

- Goal: 實作批次子任務 scheduler，從 BATCH-MVP-01 loader 輸出（subtasks／batch_manifest JSON）產生執行順序與 wave 分組，並輸出 batch_manifest 與 eligibility 資訊。
- Scope:
  - 建立 `04_Workflows/_batch_orchestrator/scheduler.py`：
    - 輸入：loader 返回的 `{"ok": true, "data": ...}` 結構（消費 `data` 內 subtasks 列表）。
    - 輸出：包含 `waves`（每波可並行 `subtask_id` 列表）、`order`、`eligibility`。
    - 公開 API：`plan_from_subtasks(subtasks: list[dict]) -> dict`。
  - 建立 `04_Workflows/_templates/batch_manifest.template.json`：
    - 包含 `batch_id`、`parent_ticket_id`、`subtasks`、`waves` 基本欄位。
  - 建立 `tests/test_batch_scheduler.py`：
    - 覆蓋簡單 DAG（線性依賴）與並行場景。
  - Scheduler 只負責「排序與分組」，不執行任何 Worker、不修改 tickets state。
- NonScope:
  - 不執行 Worker（無 API 呼叫、無 CLI runner、無 dispatch executor）。
  - 不寫入 `artifacts/control_plane/batches/*` 真實檔案（僅在測試中使用 tempdir）。
  - 不修改任何 `*_state.md`（本票 Implementer 僅可寫 B_REPORT 區塊）。
  - 不處理複雜依賴環（cycle detection 可標為 deferred，但須在 `eligibility["errors"]` 定義清楚行為）。
  - 不實作優先級調整策略（僅使用簡單 `priority` + `dependency` 排序）。
  - 不修改 loader 契約（`ok`／`data`／`errors`）或 `batch_subtask.schema.json`。
  - 引用 §6.6.2 預設紅線（治理母本、全局 live STATE、CI／L2／L3、他人 core）。
- AllowedPaths:
  - `04_Workflows/_batch_orchestrator/scheduler.py`
  - `04_Workflows/_templates/batch_manifest.template.json`
  - `tests/test_batch_scheduler.py`
  - `04_Workflows/tickets/BATCH-MVP-02_state.md`（Implementer 僅 B_REPORT 區塊）
- BlockedPaths:
  - `04_Workflows/tickets/*_state.md`（本票除外）
  - `04_Workflows/00_Agent_Work_Progress.md`
  - `04_Workflows/project_status/master_status.md`
  - `04_Workflows/handoff.md`
  - `.cursor/rules/**`
  - `AGENTS.md`
  - `ENGINEERING_CONTRACT.md`
  - `HARNESS_CONSTITUTION.md`
  - `artifacts/control_plane/**`
  - `.github/workflows/**`
  - `core/**`
  - `skills/**`
  - `observability/**`
  - `config/**`
- Dependencies:
  - **BATCH-MVP-01**（已完成）：`_batch_orchestrator/loader.py` 與 `batch_subtask.schema.json`；subtask 必填鍵含 `priority`、`dependencies`、`subtask_id`。
  - 必讀：本票 FRAME；`04_Workflows/tickets/BATCH-MVP-01_state.md`（loader 合約）；`04_Workflows/_templates/batch_subtask.schema.json`（subtask 欄位語意）。
- AcceptanceCriteria:
  - AC-1 **Scheduler API**：提供 `plan_from_subtasks(subtasks: list[dict]) -> dict`；返回 `dict` 至少含 `waves: list[list[str]]`、`order: list[str]`、`eligibility: dict`（標記可並行與不可並行原因）。
  - AC-2 **依賴與拓撲**：同一 wave 內不得有依賴衝突（B 依賴 A 則 B 不得與 A 同 wave）；若存在依賴環，應在 `eligibility["errors"]` 標記並設定 `ok: false`（cycle detection 可 deferred，但行為須清楚、測試或 B_REPORT 留痕）。
  - AC-3 **Priority**：同一 wave 內，優先級較高（`priority` 數值較小）的 subtask 應優先出現在 `order` 中。
  - AC-4 **測試可重跑**：`pytest tests/test_batch_scheduler.py -q` 成功；覆蓋（a）無依賴全在 wave1；（b）線性鏈 A→B→C；（c）部分並行 A→C、B 無依賴。
  - AC-5 **合約穩定性**：Scheduler 僅依賴 loader 的 `data` 內容，不變更 loader 回傳契約；不直接存取 tickets state 或 Progress。

### Wave Master 擴展

- phase_targets: [P8]
- baseline_pct: "07-13 W-PROG-B · P8=45%"
- proposed_delta_pct: "P8 +1"
- evidence_gate: L-local
- impact_size: small
- apply_phase_pct: false
- non_claims:
  - ≠ BATCH-MVP-03/04 executor · ≠ control_plane write · ≠ Phase closure

---

## STATE

- overall_status: done
- current_owner: none
- next_action: 無 · 已 accepted；P8 Δ 由 W-PROG-triple-batch-2026-07-13 匯總寫入
- last_updated: 2026-07-13 · orchestrator（same_chat 收口）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- ac_status:
  - AC-1: pass
  - AC-2: pass
  - AC-3: pass
  - AC-4: pass
  - AC-5: pass
- orchestrator_note: |
    2026-07-13 same_chat：scheduler + tests 落地；cycle → ok:false + eligibility.errors。
    趴數經 W-PROG 匯總票 apply（本票 apply_phase_pct=false）。

> **凍結聲明**：FRAME Scope 與本輪工作邊界一致；Phase 影響欄為 07-13 補填。

---

## B_REPORT

- changed_files:
  - `04_Workflows/_batch_orchestrator/scheduler.py`（added）
  - `04_Workflows/_batch_orchestrator/__init__.py`（export plan_*）
  - `04_Workflows/_templates/batch_manifest.template.json`（added）
  - `tests/test_batch_scheduler.py`（added）
- artifacts: 無
- verification: |
    python -m unittest tests.test_batch_scheduler -v → Ran 6 tests OK
- behavior_notes: |
    plan_from_subtasks 回傳 ok/waves/order/eligibility；Kahn 分波；同波 priority 升序；
    cycle → ok=false + eligibility.errors。
- deferred_items: Worker 執行／control_plane 寫入 → BATCH-MVP-03+

### Phase 影響

- **影響 Phase**：P8
- **baseline**：07-13 W-PROG-B · 45%
- **proposed_delta**：+1
- **實際上調**：待 W-PROG-triple-batch-2026-07-13
- **non_claims**：≠ executor · ≠ Phase closure

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無
- checks_summary: |
    AC-1～AC-5 對照通過；6 unittest OK；未觸禁區／未改 loader 契約。
- risk_level: low
- suggestions: BATCH-MVP-03 另票接 executor；勿與 02 同目錄大改並行。

### Phase 影響

- **影響 Phase**：P8
- **baseline**：07-13 W-PROG-B · 45%
- **proposed_delta**：+1
- **實際上調**：待 W-PROG（本票 apply_phase_pct=false · 未越權寫 %）
- **non_claims**：≠ auto-uplift

---

## D_REPORT

- docs_updates: template JSON 已入 AllowedPaths；無額外 playbook
- progress_entry: 見 Progress 末尾 · W-PROG-triple-batch-2026-07-13
- followup_suggestions: BATCH-MVP-03 排程執行器

### Phase 影響

- **影響 Phase**：P8
- **proposed_delta**：+1
- **實際上調**：見 W-PROG 匯總
- **non_claims**：≠ Phase closure
