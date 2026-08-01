# WD-P85-T4-bridge-negative-plan-fixture-v1 — Ticket State

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Wave-E follow-up · optional · 源自 Wave-D P85-T1 accepted_with_gaps（負例 plan fixture 集中化）

---

## FRAME

- **summary**: 把 bridge 負例 browser plan（invalid plan / force error 等）從 inline dict 抽到 `tests/fixtures/orchestration_bridge/`，與 P85-T1 正例 fixture 同一目錄維護。（**optional** · 不阻 Wave-E 主線）

- **goal**:
  - 新增 JSON fixture（至少 `invalid_plan_force_error.json`；可選 `reject_gate_with_plan.json`）對應現有 inline 負例。
  - 重構 `test_force_browser_invalid_plan_fails_overall`（及相關負例）改用 `_load_fixture()`，刪除重複 inline plan dict。
  - fixture 目錄加 **README 一行索引**（檔名 → 對應 test → 預期 `ok` / `skip_reason`）。
  - 保持 unittest 全綠；若 test 數變動，同步 P85-T3 權威計數位置。
  - 不改 bridge runtime 錯誤處理語意，僅測試資料集中化。

- **non_goals**:
  - 不改 `browser_runner.py` / `minimal_orchestration_bridge.py` 錯誤碼或 stage 訊息（除非 fixture 載入暴露既有 bug，則另票）。
  - 不搬移 `HAPPY_BROWSER_PLAN` / `SAMPLE_HTML`（正例可留 inline 或後續票）。
  - 不做 Phase 8.6 API / WORKFLOW_INDEX 大改。
  - 不引入 Playwright 或新 browser action 類型。
  - 不阻塞 Wave-E 主線（P85-T3 可先獨立交付）。

- **allowed_paths**:
  - `01_Environments/python_venvs/gov_core_system/tests/fixtures/orchestration_bridge/*.json`（新增負例）
  - `01_Environments/python_venvs/gov_core_system/tests/fixtures/orchestration_bridge/README.md`（可選，一行索引）
  - `01_Environments/python_venvs/gov_core_system/tests/test_minimal_orchestration_bridge.py`（負例 test 重構）
  - `04_Workflows/tickets/WD-P85-T4-bridge-negative-plan-fixture-v1_state.md`
  - `docs/phase8_5-bridge-smoke-runbook-v1.md`（可選：fixtures 目錄 cross-ref 一句）

- **blocked_paths**:
  - `gov_core_system/core/**`
  - `shared/schemas/orchestration_bridge_v1.json`（除非純註解）
  - CI workflow · dashboard · 其它 Phase 測試

- **acceptance_criteria**:
  - **AC-1**：至少一個原 inline 負例 plan 已改為 JSON fixture 載入；對應 test 仍 assert `ok=false` 或預期 skip 行為不變。
  - **AC-2**：`tests/fixtures/orchestration_bridge/` 含新負例 JSON；檔名與 test 對照可查（README 或 test docstring）。
  - **AC-3**：`python -m unittest tests.test_minimal_orchestration_bridge -v` 全綠；計數變動時已更新 P85-T3 權威位置。
  - **AC-4**：無 hard-coded 磁碟絕對路徑；fixture 仍經 `_load_fixture()` 相對載入。
  - **AC-5**：B_REPORT 列 changed_files + before/after 對照（哪些 inline dict 已移除）。

---

## STATE

- **overall_status**: done_with_gaps
- **current_owner**: orchestrator
- **next_action**: 無（文書收口完成 · WD-WG-SCRIBE-REVIEW-closure-v1）
- **last_updated**: 2026-06-22 · scribe
- **notes**: Wave-E 新票 · **optional**；源自 Wave-D P85-T1 suggestion；Wave-F 最小交付已完成
- **status_by_role**:
  - **Orchestrator (A)**: done — 2026-06-20 開票落盤
  - **Implementer (B)**: done — 2026-06-20 Wave-F 負例 fixture 最小交付
  - **Reviewer (C)**: done — 2026-06-22（文書回填 · 依 Wave-E/F 收口證據）
  - **Scribe (D)**: done — 2026-06-22

---

## B_REPORT (Implementer)

- **changed_files**:
  - `tests/fixtures/orchestration_bridge/negative_invalid_browser_plan.json` — 新增負例 plan（`#missing` click → browser step fail）
  - `tests/fixtures/orchestration_bridge/README.md` — 追加 `negative_invalid_browser_plan.json` → test 對照列
  - `tests/test_minimal_orchestration_bridge.py` — `test_force_browser_invalid_plan_fails_overall` 改 `_load_fixture("negative_invalid_browser_plan.json")`；移除 inline bad plan dict
- **negative_test_extracted**: `test_force_browser_invalid_plan_fails_overall`（原 inline plan with `#missing` click → 現改 fixture 載入）
- **fixture_added**: `negative_invalid_browser_plan.json`（`plan_id`: `bad-001`；預期 overall `ok=false`、browser result `ok=false`）
- **before_after**: `test_force_browser_invalid_plan_fails_overall` 內嵌 `{"plan_id":"bad-001","steps":[navigate+click #missing]}` dict 已刪；其餘負例（如 `test_reject_with_plan_skipped_by_default`）仍用 inline `HAPPY_BROWSER_PLAN`（FRAME non_goal 允許）
- **verification**: `python -m unittest tests.test_minimal_orchestration_bridge -v`（`gov_core_system` cwd）→ **14/14 OK**（2026-06-20 · Wave-F）；test 計數未變，P85-T3 `EXPECTED_TEST_COUNT=14` 無需更新
- **not_changed**: bridge core / browser_runner 錯誤語意 / CI / WORKFLOW_INDEX

---

## C_REPORT (Reviewer)

- **review_date**: 2026-06-20（文書回填 · 依 Wave-E/F 收口與 Progress 驗證證據；本輪未追加重跑）
- **reviewer_role**: Wave-E Reviewer (C) · WD-WG-SCRIBE-REVIEW-closure-v1 文書回填
- **conclusion**: **accepted_with_gaps**
- **blocking_issues**: 無 blocking；gaps 已記錄於 B_REPORT / D_REPORT / suggestions
- **verification_rerun**:
  - `python -m unittest tests.test_minimal_orchestration_bridge -v`（暗部 `gov_core_system` cwd）→ **14/14 OK**
- **checks_summary**:
  - **AC-1～AC-5 ✅**: `test_force_browser_invalid_plan_fails_overall` 改載入 `negative_invalid_browser_plan.json`；README 索引已補；計數仍 **14**（P85-T3 權威位置無需更新）
  - **Rule 3/8 ✅**: 僅 fixture + test 資料集中化；未改 bridge runtime 錯誤語意
- **risk_level**: low
- **suggestions**: 可選第二負例 `reject_gate_with_plan.json` 未做；`test_reject_with_plan_skipped_by_default` 等仍 inline

---

## D_REPORT (Scribe)

- **verdict_echo**: Reviewer **`accepted_with_gaps`** — Wave-F 最小交付：`test_force_browser_invalid_plan_fails_overall` 改載入 `negative_invalid_browser_plan.json`；**14/14 OK**；未改 bridge runtime。
- **closure_summary**: 負例 inline dict → JSON fixture + README 索引；unittest 計數維持 **14**。可選第二負例 fixture 未做。
- **gaps**: `test_reject_with_plan_skipped_by_default` 等仍 inline 正例 plan；bridge 仍 in-memory stub。
- **progress_entry**: WD-P85-T4 負例 fixture — **`accepted_with_gaps`**；bridge unittest **14/14 OK**。
- **scribe_date**: 2026-06-22 · WD-WG-SCRIBE-REVIEW-closure-v1
