# WD-P85-T3-bridge-index-test-count-closure-v1 — Ticket State

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Wave-E follow-up · 源自 Wave-D P85-T2 accepted_with_gaps（bridge 計數 10→14 索引收口）

---

## FRAME

- **summary**: 將 bridge smoke 相關 **docs / 索引 / Progress** 中過時的 **10** 對齊至實際 **14**，並建立 **單一權威來源** 供日後增刪 test 時同步更新。

- **goal**:
  - 修正 `WORKFLOW_INDEX.md` §1.4 等仍寫 **10/10** 的 bridge 計數 → **14/14**（或「見 runbook 權威計數」+ 正確數字）。
  - 在 **單一權威位置** 登錄 bridge unittest 模組與預期計數（建議：`docs/phase8_5-bridge-smoke-runbook-v1.md` Smoke A + `test_minimal_orchestration_bridge.py` 模組 docstring / `EXPECTED_TEST_COUNT` 互引）。
  - 若 `Master_Map.json` runners 或 `PHASE8_6_*` spec 有 stale 計數，一併對齊（僅數字 / cross-ref，不改 bridge 邏輯）。
  - Progress **末尾 append** Wave-E 修正條（**不重寫** 歷史戰報段落）。
  - 可選：runbook 加「更新計數 checklist」（新增 test → 改 docstring 權威行 → 改 WORKFLOW_INDEX → append Progress）。

- **non_goals**:
  - 不修改 `minimal_orchestration_bridge.py` 商務邏輯或 bridge API 契約。
  - 不引入 Playwright、真 browser、或 bridge → HTTP E2E 新功能。
  - 不改 `docs/WAVE_PROGRESS_DASHBOARD.md` P8.5 百分比。
  - 不全庫替換所有「10/10」（僅 **orchestration bridge / test_minimal_orchestration_bridge** 語境）。
  - 不強制 CI 新增 bridge job（Smoke B fastapi 依賴仍維持 runbook 聲明）。

- **allowed_paths**:
  - `04_Workflows/WORKFLOW_INDEX.md`（§1.4 及 bridge 交叉引用）
  - `04_Workflows/00_Agent_Work_Progress.md`（**僅末尾 append**）
  - `docs/phase8_5-bridge-smoke-runbook-v1.md`
  - `04_Workflows/PHASE8_6_MINIMAL_ORCHESTRATION_BRIDGE_MVP_v0.1.md`（若含 stale 計數）
  - `04_Workflows/Master_Map.json`（bridge smoke runner 描述欄位）
  - `01_Environments/python_venvs/gov_core_system/tests/test_minimal_orchestration_bridge.py`（**僅** docstring / 權威計數常數或註解）
  - `04_Workflows/tickets/WD-P85-T3-bridge-index-test-count-closure-v1_state.md`

- **blocked_paths**:
  - `gov_core_system/core/**`（bridge / intake / browser 實作）
  - `gov_core_system/app_api.py`
  - `.github/workflows/**`
  - `docs/WAVE_PROGRESS_DASHBOARD.md`
  - 其它 Phase ticket `_state.md`（除非純 cross-ref 一行）

- **acceptance_criteria**:
  - **AC-1**：`python -m unittest tests.test_minimal_orchestration_bridge -v`（暗部 `gov_core_system` cwd）→ **14/14 OK**；B_REPORT 附命令輸出語意。
  - **AC-2**：`WORKFLOW_INDEX.md` §1.4「最近一次通過紀錄」已改為 **14/14**（或指向 runbook 權威計數且數字正確）。
  - **AC-3**：`docs/phase8_5-bridge-smoke-runbook-v1.md` Smoke A 明示 **權威計數 = 14** 及更新 checklist。
  - **AC-4**：`test_minimal_orchestration_bridge.py` docstring 或 `EXPECTED_TEST_COUNT = 14` 與實際 test method 數一致。
  - **AC-5**：Progress **末尾**有一條 Wave-E 收口戰報，說明 10→14 修正與權威位置。
  - **AC-6**：grep `test_minimal_orchestration_bridge` 搭配 `10/10` 在 bridge 語境下 **零 stale 命中**（B_REPORT 附 grep 證據或已修正清單）。
  - **AC-7**：未改 bridge 行為；Smoke B fastapi 依賴說明仍與 WD-P85-T2 一致。

---

## STATE

- **overall_status**: done_with_gaps
- **current_owner**: orchestrator
- **next_action**: 無（文書收口完成 · WD-WG-SCRIBE-REVIEW-closure-v1）
- **last_updated**: 2026-06-22 · scribe
- **notes**: Wave-E 新票；源自 Wave-D P85-T2 gap（WORKFLOW_INDEX / Progress 仍寫 10 tests，實際 14/14）
- **status_by_role**:
  - **Orchestrator (A)**: done — 2026-06-20 開票落盤
  - **Implementer (B)**: done — 2026-06-20 索引／runbook 10→14；權威計數互引；Progress append
  - **Reviewer (C)**: done — 2026-06-22（文書回填 · 依 Wave-E 收口證據）
  - **Scribe (D)**: done — 2026-06-22

---

## B_REPORT (Implementer)

- **changed_files**:
  - `docs/phase8_5-bridge-smoke-runbook-v1.md` — Smoke A 權威計數 **14**、pass criteria 14/14、count-update checklist
  - `04_Workflows/WORKFLOW_INDEX.md` §1.4 — 最近一次通過紀錄 → **14/14** + runbook/常數 cross-ref
  - `tests/test_minimal_orchestration_bridge.py` — module docstring + `EXPECTED_TEST_COUNT = 14`
  - `04_Workflows/00_Agent_Work_Progress.md` — Wave-E append（本條）
  - `04_Workflows/tickets/WD-P85-T3-bridge-index-test-count-closure-v1_state.md` — B_REPORT + STATE
- **authoritative_count**: `docs/phase8_5-bridge-smoke-runbook-v1.md` Smoke A ↔ `EXPECTED_TEST_COUNT` in test module
- **verification**:
  - `python -m unittest tests.test_minimal_orchestration_bridge -v` → **14/14 OK**（2026-06-20）
  - Wave-F hotfix（2026-06-20）：修正 `from __future__ import annotations` 須緊接 module docstring、`EXPECTED_TEST_COUNT` 置後；本 cwd 重跑 **14/14 OK**（無 SyntaxError）
  - Wave-F Scribe 複核（2026-06-20）：熱修**僅**調整 `from __future__ import annotations` 至 module docstring 直後（SyntaxError 修正）；`gov_core_system` cwd 重跑 `python -m unittest tests.test_minimal_orchestration_bridge -v` → **14/14 OK**
- **not_changed**: bridge core / `app_api.py` / CI workflows / `WAVE_PROGRESS_DASHBOARD.md` / historical Progress paragraphs
- **grep_note**: `WORKFLOW_INDEX` + runbook bridge 語境無 stale 10/10；歷史 Progress（P85-T2 條、Wave-D「仍寫 10 tests」）依 FRAME 保留

---

## C_REPORT (Reviewer)

- **review_date**: 2026-06-20（文書回填 · 依 Wave-E 收口與 Progress 驗證證據；本輪未追加重跑）
- **reviewer_role**: Wave-E Reviewer (C) · WD-WG-SCRIBE-REVIEW-closure-v1 文書回填
- **conclusion**: **accepted_with_gaps**
- **blocking_issues**: 無 blocking；gaps 已記錄於 B_REPORT / D_REPORT / suggestions
- **verification_rerun**:
  - `python -m unittest tests.test_minimal_orchestration_bridge -v`（暗部 `gov_core_system` cwd）→ **14/14 OK**
- **checks_summary**:
  - **AC-1～AC-4、AC-6～AC-7 ✅**: 權威計數 **14** 互引（runbook Smoke A ↔ `EXPECTED_TEST_COUNT`）；WORKFLOW_INDEX §1.4 已對齊；未改 bridge runtime
  - **AC-5 ✅**: Progress 末尾 Wave-E 條目已 append（歷史 Wave-D 段落依 FRAME 保留）
  - **Rule 3/8 ✅**: 僅 docs/索引/docstring；無 bridge 邏輯 diff
- **risk_level**: low
- **suggestions**: bridge 仍 in-memory stub；Smoke B 需 venv `fastapi`；advisory CI 雙 job（`p85-bridge-smoke-a` **14/14** · `p85-bridge-smoke-b` **7/7**）仍 non-blocking · GA Scenario 1 pass（Wave-H+1）

---

## D_REPORT (Scribe)

- **verdict_echo**: Reviewer **`accepted_with_gaps`** — 索引／runbook／`EXPECTED_TEST_COUNT` 權威計數 **14** 對齊；未改 bridge runtime。
- **closure_summary**: WORKFLOW_INDEX §1.4、runbook Smoke A、`EXPECTED_TEST_COUNT=14` 互引；bridge 語境 stale 10/10 已清除。Wave-G/H 已接 `.github/workflows/bridge-smoke.yml` jobs **`p85-bridge-smoke-a`**（**14/14**）· **`p85-bridge-smoke-b`**（**7/7**）· advisory · non-blocking；仍非 merge-blocking required check。CI / 索引 full sweep 見 **`WH-P85-CI-LAND-doc-sync-v1`**。
- **gaps**: bridge 仍為 in-memory stub；Smoke B 需 venv `fastapi`；歷史 Progress（P85-T2、Wave-D 收口）仍保留 10 tests 敘述（FRAME 刻意不重寫）。
- **progress_entry**: WD-P85-T3 計數收口 — **`accepted_with_gaps`**；bridge unittest **14/14 OK**。
- **scribe_date**: 2026-06-22 · WD-WG-SCRIBE-REVIEW-closure-v1
