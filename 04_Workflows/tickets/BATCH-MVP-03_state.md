# TICKET STATE · BATCH-MVP-03 · Batch Implementer Prompt Builder & Mock Runner

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

<!-- Orchestrator 填 · 2026-06-15 凍結；後續變更僅 Orchestrator 顯式更新 -->

**Goal:**
- 實作 Implementer 專用 prompt builder，以及一個 mock runner，用來模擬 Worker 執行結果，驗證 batch scheduler + loader 的 end-to-end 契約。

**Scope:**
- 建立 `04_Workflows/_batch_orchestrator/prompt_builder.py`：
  - 輸入：subtask 定義（遵守 BATCH-MVP-01 schema）。
  - 輸出：Implementer prompt 結構，包含：
    - role（Implementer）
    - goal_statement
    - must_read 檔案列表（含父票 state）
    - allowed_paths / blocked_paths
    - acceptance_checks 摘要
- 建立 `04_Workflows/_batch_orchestrator/runner_mock.py`：
  - 模擬 Worker 執行：
    - 對每個 subtask 產生一個假的 `ExecutionResult`。
    - 支援設定成功/失敗比例與基本 latency。
- 建立 `tests/test_batch_prompt_and_runner.py`：
  - 驗證 prompt 結構符合 FRAME／multi_chat_roles 期望。
  - 驗證 mock runner 可在 concurrency_limit=2 下跑完一組 subtasks。

**NonScope:**
- 不實作 Reviewer/Scribe 的 prompt builder。
- 不呼叫真實 Worker API。
- 不寫入任何 tickets state 或 Progress。
- 不實作完整的 error recovery 或 retry 策略。
- 引用 §6.6.2 預設紅線（治理母本、全局 live STATE、CI／L2／L3、他人 core）。

**AllowedPaths:**
- `04_Workflows/_batch_orchestrator/prompt_builder.py`
- `04_Workflows/_batch_orchestrator/runner_mock.py`
- `tests/test_batch_prompt_and_runner.py`
- `04_Workflows/tickets/BATCH-MVP-03_state.md`（Implementer 僅 B_REPORT 區塊）

**BlockedPaths:**
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

**Dependencies:**
- **BATCH-MVP-01**（已完成）：`_batch_orchestrator/loader.py` 與 `batch_subtask.schema.json`；subtask 欄位語意（`subtask_id`、`parent_ticket_id`、`goal`、`scope` 等）。
- **BATCH-MVP-02**（進行中）：scheduler 產出的 waves／order／eligibility 結構；本票 prompt builder 可選消費 scheduler 輸出。
- 必讀：`.cursor/rules/multi_chat_roles.mdc` §Implementer（角色邊界）；`AGENTS.md` §紅線（禁硬編路徑、禁印金鑰等）。

**AcceptanceCriteria:**
1. **Prompt Builder**：
   - 提供 `build_implementer_prompt(subtask: dict, parent_frame: dict) -> dict`。
   - 回傳 dict 至少包含：
     - `role: "implementer"`
     - `goal_statement`
     - `must_read`（含父票 state 檔路徑）
     - `allowed_paths` / `blocked_paths`
     - `acceptance_checks_summary`
2. **Mock Runner**：
   - 提供 `run_subtasks_mock(subtasks: list[dict], concurrency_limit: int) -> list[ExecutionResult]`。
   - 在測試中可配置：
     - 所有成功。
     - 有少數失敗。
3. **測試可重跑**：
   - `pytest tests/test_batch_prompt_and_runner.py -q` 成功。
4. **多角色邊界**：
   - Prompt 內容引用 `.cursor/rules/multi_chat_roles.mdc` 和 `AGENTS.md`，但不修改這些檔案。
5. **合約穩定性**：
   - prompt builder 和 mock runner 僅消費 loader/scheduler 的輸出，不改動其回傳契約。

---

## STATE

<!-- Orchestrator 維護 · FRAME 已於 2026-06-15 凍結 -->

- **overall_status:** accepted
- **current_owner:** scribe
- **next_action:** scribe_progress_via_wprog_batch
- **last_updated:** 2026-07-13 · same_chat O/B/C
- **status_by_role:**
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: pending
- **ac_status:**
  - AC-1: pass
  - AC-2: pass
  - AC-3: pass
  - AC-4: pass
  - AC-5: pass
- **orchestrator_note:** |
    本票為 BATCH-MVP 系列第三張；上游 BATCH-MVP-01 loader 已完成，BATCH-MVP-02 scheduler 進行中。
    Prompt builder 消費 subtask 定義與 parent FRAME，產出 Implementer 專用 prompt 結構。
    Mock runner 模擬 Worker 執行，支援並行控制與成功/失敗配置，用於 end-to-end 驗證。

> **凍結聲明**：FRAME 與本輪工作邊界一致；Implementer／Reviewer **不得**改 FRAME。後續 scope 變更須 Orchestrator 顯式更新 FRAME 並留痕。

### STATE append · 2026-07-13 · P8-80 serial

- Implementer 完成 prompt_builder + runner_mock + tests；Reviewer same_chat 自檢 AC-1～5 通過。
- **proposed_delta_pct:** +8（L-local · 待 W-PROG）；`apply_phase_pct: false`
- 下一步：BATCH-MVP-04（不可與 03 並行改同一套 `_batch_orchestrator`）

---

## B_REPORT

<!-- Implementer 填：施工結果；只寫本區塊，不改 FRAME / STATE -->

- changed_files:
  - `04_Workflows/_batch_orchestrator/prompt_builder.py` (new)
  - `04_Workflows/_batch_orchestrator/runner_mock.py` (new)
  - `tests/test_batch_prompt_and_runner.py` (new)
- artifacts: 無外部 artifact；ExecutionResult dataclass + build_implementer_prompt dict
- verification: |
    ```powershell
    python -m unittest tests.test_batch_prompt_and_runner -v
    # → 5 tests OK
    ```
    （票面 AC-3 寫 pytest；本機無 pytest 模組，以 unittest 等價驗收）
- behavior_notes: |
    - `build_implementer_prompt` → role/goal/must_read/allowed/blocked/acceptance_checks_summary
    - `run_subtasks_mock` 支援 concurrency_limit、failure_ratio、force_failures；回傳 `list[ExecutionResult]`
    - 未改 loader／scheduler 契約；未寫其他 `*_state.md`／Progress
- deferred_items: Reviewer/Scribe prompt builder；真實 Worker API；retry／error recovery

### Phase 影響

- **影響 Phase**：P8
- **baseline**：07-13 W-PROG-triple · P8=46%
- **proposed_delta**：+8
- **實際上調**：待 W-PROG
- **non_claims**：≠ executor 真跑 · ≠ Phase closure · ≠ 自動 uplift Dashboard %

---

## C_REPORT

<!-- Reviewer 填：審查結論；只寫本區塊，不改 code -->

- conclusion: accepted
- blocking_issues: 無
- checks_summary: |
    AC-1 prompt 鍵齊全；AC-2 mock runner concurrency=2 + 成功／失敗配置；
    AC-3 unittest 5 OK（pytest 未安裝，unittest 等價）；
    AC-4 引用 multi_chat_roles／AGENTS 路徑字串、未改檔；
    AC-5 未改 loader／scheduler 回傳契約。AllowedPaths 內。
- risk_level: low
- suggestions: BATCH-MVP-04 串接 collector／reporter／CLI；勿與 03 並行大改同目錄。

### Phase 影響

- **影響 Phase**：P8
- **baseline**：07-13 W-PROG-triple · 46%
- **proposed_delta**：+8
- **實際上調**：待 W-PROG（本票 apply_phase_pct=false · 未越權寫 %）
- **non_claims**：≠ auto-uplift

---

## D_REPORT

<!-- Scribe 填：文檔與進度建議；只寫本區塊 -->

- docs_updates: 無獨立 playbook（契約見 FRAME）
- progress_entry: 見 Progress 末尾 · 待 W-PROG 匯總票
- followup_suggestions: BATCH-MVP-04 collector／reporter／CLI mock E2E

### Phase 影響

- **影響 Phase**：P8
- **proposed_delta**：+8
- **實際上調**：見 W-PROG 匯總
- **non_claims**：≠ Phase closure
