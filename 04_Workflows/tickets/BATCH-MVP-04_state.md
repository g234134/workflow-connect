# TICKET STATE · BATCH-MVP-04 · Batch collector / reporter / CLI mock E2E

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

<!-- Orchestrator 填 · 2026-06-15 凍結；後續變更僅 Orchestrator 顯式更新 -->

- Goal: 實作 collector 與 reporter，將 mock runner 的結果聚合成 batch-level summary 和 state patch 建議，並提供一個 CLI 入口，讓使用者可以從 manifest/subtasks JSON 一鍵跑完整個 mock 流程。
- Scope:
  - 建立 `04_Workflows/_batch_orchestrator/collector.py`：
    - 聚合 `ExecutionResult` 列表，產生 `BatchResult`（含各 subtask 結果與總結）。
    - 公開 API：`collect_results(results: list[ExecutionResult]) -> BatchResult`。
  - 建立 `04_Workflows/_batch_orchestrator/reporter.py`：
    - 從 `BatchResult` 產生 `batch_result.json`（供工具消費）與 `state_patch_suggestion.json`（建議更新父票 STATE，**不**直接寫入票檔）。
    - 公開 API：`render_batch_result_json(batch_result) -> dict`、`render_state_patch_suggestion(batch_result) -> dict`。
  - 建立 `04_Workflows/_batch_orchestrator/cli.py`：
    - 命令：`python -m _batch_orchestrator.cli run --manifest path/to/manifest.json --mode mock --limit 3`
    - 串接 loader + scheduler + prompt_builder + runner_mock + collector + reporter。
  - 建立 `tests/test_batch_e2e_mock.py`：
    - 驗證簡單 manifest 可整條跑完（mock 模式），並產出預期 `BatchResult` 形狀。
  - 可選：`docs/batch_orchestrator_mvp.md`（CLI 用法與輸出檔說明）。
- NonScope:
  - 不呼叫真實 Worker API。
  - 不修改任何 `*_state.md`（reporter 僅產生建議檔）。
  - 不寫入 `artifacts/control_plane/*`；只在測試或 `output/` 下寫 mock 產物。
  - 不處理 production 等級的錯誤重試策略。
  - 不修改 loader／scheduler／prompt_builder／runner_mock 的回傳契約（僅消費輸出）。
  - 引用 §6.6.2 預設紅線（治理母本、全局 live STATE、CI／L2／L3、他人 core）。
- AllowedPaths:
  - `04_Workflows/_batch_orchestrator/collector.py`
  - `04_Workflows/_batch_orchestrator/reporter.py`
  - `04_Workflows/_batch_orchestrator/cli.py`
  - `04_Workflows/_batch_orchestrator/__init__.py`（僅 export 本票新增 API，若需要）
  - `tests/test_batch_e2e_mock.py`
  - `tests/fixtures/sample_manifest.json`（測試用 manifest fixture；僅本票 scope）
  - `docs/batch_orchestrator_mvp.md`（可選）
  - `04_Workflows/tickets/BATCH-MVP-04_state.md`（Implementer 僅 B_REPORT 區塊）
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
  - **BATCH-MVP-01**（已完成）：`_batch_orchestrator/loader.py` — manifest／subtask 載入（`ok`／`data`／`errors`）。
  - **BATCH-MVP-02**（進行中）：`_batch_orchestrator/scheduler.py` — `plan_from_subtasks`（waves／order／eligibility）。
  - **BATCH-MVP-03**（前置票）：`_batch_orchestrator/prompt_builder.py`、`_batch_orchestrator/runner_mock.py` — `ExecutionResult` 契約與 mock 執行；本票 CLI 串接其輸出。
  - 必讀：本票 FRAME；`04_Workflows/tickets/BATCH-MVP-01_state.md`、`BATCH-MVP-02_state.md`、`BATCH-MVP-03_state.md`（若已開票）；既有 `_batch_orchestrator/*` 模組與測試 fixture。
- AcceptanceCriteria:
  - AC-1 **Collector API**：提供 `collect_results(results: list[ExecutionResult]) -> BatchResult`；`BatchResult` 至少含 `batch_id`、`summary`（total/success/failed/blocked/timeout）、`subtask_results`（每 subtask 狀態）。
  - AC-2 **Reporter API**：提供 `render_batch_result_json(batch_result) -> dict` 與 `render_state_patch_suggestion(batch_result) -> dict`；不直接寫入父票 state，只生成建議 dict／檔案。
  - AC-3 **CLI**：`python -m _batch_orchestrator.cli run --manifest tests/fixtures/sample_manifest.json --mode mock --limit 2` 成功執行（自 repo 根或 `04_Workflows` 目錄，路徑以 B_REPORT 留痕實際 cwd 約定）。
  - AC-4 **測試可重跑**：`pytest tests/test_batch_e2e_mock.py -q` 成功；覆蓋 mock 整條 pipeline 與 `BatchResult` 形狀。
  - AC-5 **合約穩定性**：不改變 loader／scheduler／prompt_builder／runner_mock 回傳契約，只消費輸出。

---

## STATE

<!-- Orchestrator 維護 · FRAME 已於 2026-06-15 凍結 -->

- overall_status: accepted
- current_owner: scribe
- next_action: scribe_progress_via_wprog_batch
- last_updated: 2026-07-13 · same_chat O/B/C
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: pending
- ac_status:
  - AC-1: pass
  - AC-2: pass
  - AC-3: pass
  - AC-4: pass
  - AC-5: pass
- orchestrator_note: |
    本票為 BATCH-MVP 系列第四張；上游 MVP-01 loader 已完成，MVP-02 scheduler 進行中，MVP-03 prompt_builder + runner_mock 為 CLI 串接硬依賴。
    若 MVP-03 尚未合併，Implementer 應先讀 `_batch_orchestrator/` 現況；缺模組時在 B_REPORT 標阻塞，勿 workaround 改 BlockedPaths。
    reporter 的 state_patch_suggestion 僅建議檔，禁止寫入任何 `*_state.md` 或 Progress。

> **凍結聲明**：FRAME 與本輪工作邊界一致；Implementer／Reviewer **不得**改 FRAME。後續 scope 變更須 Orchestrator 顯式更新 FRAME 並留痕。

### STATE append · 2026-07-13 · P8-80 serial

- MVP-03 accepted 後串行完成 collector／reporter／cli／e2e；reporter `writes_ticket_state=false`。
- **proposed_delta_pct:** +10（L-local · 待 W-PROG）；`apply_phase_pct: false`

---

## B_REPORT

<!-- Implementer 填：施工結果；只寫本區塊，不改 FRAME / STATE -->

- changed_files:
  - `04_Workflows/_batch_orchestrator/collector.py` (new)
  - `04_Workflows/_batch_orchestrator/reporter.py` (new)
  - `04_Workflows/_batch_orchestrator/cli.py` (new)
  - `04_Workflows/_batch_orchestrator/__init__.py` (export 本票 API)
  - `tests/test_batch_e2e_mock.py` (new)
  - `tests/fixtures/sample_manifest.json` (new)
- artifacts: optional output `batch_result.json` + `state_patch_suggestion.json` under `--output-dir` only
- verification: |
    ```powershell
    $env:PYTHONPATH = "04_Workflows"
    python -m unittest tests.test_batch_e2e_mock -v
    # → 3 tests OK
    python -m _batch_orchestrator.cli run --manifest tests/fixtures/sample_manifest.json --mode mock --limit 2
    # → ok=true · writes_ticket_state=false
    ```
- behavior_notes: |
    - collector → BatchResult(summary total/success/failed/blocked/timeout)
    - reporter 僅 suggestion；禁止寫 `*_state.md`
    - CLI 串 loader→scheduler→prompt→mock→collect→report
- deferred_items: 真實 Worker API；production retry；docs/batch_orchestrator_mvp.md（可選未寫）

### Phase 影響

- **影響 Phase**：P8
- **baseline**：07-13 W-PROG-triple · P8=46%
- **proposed_delta**：+10
- **實際上調**：待 W-PROG
- **non_claims**：≠ 真 Worker · ≠ 自動改票 state · ≠ Phase closure

---

## C_REPORT

<!-- Reviewer 填：審查結論；只寫本區塊，不改 code -->

- conclusion: accepted
- blocking_issues: 無
- checks_summary: |
    AC-1～5 通過；E2E 3 OK；CLI mock limit=2 ok；
    reporter suggestion_only／writes_ticket_state=false 硬約束成立；
    未改 loader／scheduler／prompt／runner 契約。
- risk_level: low
- suggestions: P8-T2b 接 batch-approve／resume-latest；勿再開真 webhook（P8-T3）

### Phase 影響

- **影響 Phase**：P8
- **proposed_delta**：+10
- **實際上調**：待 W-PROG
- **non_claims**：≠ auto-uplift

---

## D_REPORT

<!-- Scribe 填：文檔與進度建議；只寫本區塊 -->

- docs_updates: 可選 `docs/batch_orchestrator_mvp.md` 未寫（NonScope 可選）
- progress_entry: 見 Progress 末尾 · 待 W-PROG 匯總
- followup_suggestions: P8-T2b operator batch-approve／resume-latest

### Phase 影響

- **影響 Phase**：P8
- **proposed_delta**：+10
- **實際上調**：見 W-PROG 匯總
- **non_claims**：≠ Phase closure
