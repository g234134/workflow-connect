# TICKET STATE · W1-T3B-mvp-mainline-regression · MVP 主鏈回歸測試

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日志。  
> Wave：Wave 1 — Governance & Observability  
> **票號區分 `[待確認]`**：`W1-T3_state.md` = Eval／Trace／WF 觀測閉環 CI Artifact（in_review）；**本票** = tabular MVP 主鏈輕量回歸（Implementer 標 W1-T3）。

---

## FRAME

- Goal: 為 tabular 清洗主鏈建立輕量回歸（`demo_phase` + `sampleco/2026-0001`），一鍵確認 gate → cleaning → bundle 跑通。
- Scope:
  - `tests/test_mvp_mainline.py`
  - `scripts/run_mvp_mainline_regression.py`
  - `docs/mvp-mainline-regression.md`
- NonScope:
  - 不改憲法母本／`ENGINEERING_CONTRACT`／`AGENTS`／`.cursor/rules/*`
  - 不重寫 E2E 管線邏輯（只調用 `run_case_e2e_validation.py`）
  - 預設不接入 GitHub Actions CI
- AllowedPaths:
  - `tests/test_mvp_mainline.py`
  - `scripts/run_mvp_mainline_regression.py`
  - `docs/mvp-mainline-regression.md`
  - `04_Workflows/tickets/W1-T3B-mvp-mainline-regression_state.md`
- BlockedPaths:
  - `04_Workflows/tickets/W1-T3_state.md`（Eval CI 票 · 只讀引用）
  - `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `HARNESS_CONSTITUTION.md`
  - `.cursor/rules/*`
- Dependencies:
  - W1-T2-mvp-trace-path spec（標準樣本與 L1 信號對照）
  - `scripts/run_case_e2e_validation.py` 與既有 case 夾具
- AcceptanceCriteria:
  - 一鍵 `python scripts/run_mvp_mainline_regression.py` → exit 0 + PASS 訊息
  - 失敗路徑 exit ≠ 0 並印出可讀錯誤
  - 文檔說明何時重跑與失敗排查
- VerificationCommands:
  - `python scripts/run_mvp_mainline_regression.py -v` → exit 0；6 tests OK
  - `python -m unittest tests.test_mvp_mainline -v` → exit 0

---

## STATE

- overall_status: done
- implementation_status: done
- current_owner: scribe
- next_action: Orchestrator 讀 D_REPORT 更新 STATE／關票；可選 Reviewer 正式 AC 簽核
- last_updated: 2026-06-10 · scribe
- status_by_role:
  - orchestrator: n/a
  - implementer: done
  - reviewer: pending
  - scribe: done

---

## B_REPORT

> Implementer 施工摘要（本輪 Scribe 自 Implementer 回報整理；原無獨立 state 檔）。

### Work Report（Implementer）

| 節 | 內容 |
|----|------|
| §1 變更 | `tests/test_mvp_mainline.py`（新建 · 6 個回歸測試）· `scripts/run_mvp_mainline_regression.py`（新建 · 一鍵 runner）· `docs/mvp-mainline-regression.md`（新建 · 使用說明） |
| §2 skeleton | 無 |
| §3 placeholder | 未接入 GitHub Actions CI（文檔 §6 有 YAML 範例） |
| §4 驗證 | `python scripts/run_mvp_mainline_regression.py -v` → **6/6 OK** · exit **0** · `PASS MVP mainline regression (demo_phase + sampleco)` |
| §5 阻塞 | 無 |
| §6 下一步 | Scribe 收口 D_REPORT + WORKFLOW_INDEX 指針；可選加入 PR workflow 或 `docs/testing.md` 交叉引用 |
| §7 override | 無 |

- changed_files:
  - `tests/test_mvp_mainline.py`
  - `scripts/run_mvp_mainline_regression.py`
  - `docs/mvp-mainline-regression.md`
- behavior_notes:
  - 重用 `run_case_e2e_validation()`，不重複管線邏輯
  - `demo_phase`：`review_needed` + forced clean（7→5 行）
  - `sampleco/2026-0001`：`accepted` + `output_guard.status=warning`（115→8 行）
  - 失敗訊號：`TestMvpMainlineFailureSignals` 對不存在 case_dir 確認 exit ≠ 0
- deferred_items:
  - 正式 Reviewer AC 簽核
  - CI workflow 接線
  - 票號與 `W1-T3_state.md`（Eval CI）之 Orchestrator 層級統一命名 `[待確認]`

---

## C_REPORT

- conclusion: <!-- pending · reviewer -->
- blocking_issues: <!-- pending -->
- checks_summary: <!-- pending -->
- risk_level: <!-- pending -->
- suggestions: <!-- pending -->

---

## D_REPORT（Scribe · 收口）

- docs_updates:
  - **新增檔案**：
    - `tests/test_mvp_mainline.py` — unittest 回歸（兩案 E2E + CLI exit + 失敗訊號）
    - `scripts/run_mvp_mainline_regression.py` — 一鍵 wrapper；成功印 `PASS MVP mainline regression (demo_phase + sampleco)`，失敗 exit 1
    - `docs/mvp-mainline-regression.md` — 執行命令、何時重跑、失敗排查、相關單元測試索引
  - **回歸做什麼**：對 `cases/demo_phase` 與 `cases/sampleco/2026-0001` 跑既有 E2E driver（gate → cleaning → bundle）；成功 exit 0 + PASS；失敗 exit ≠ 0 並印 step 級錯誤／`overall_ok: False`
  - **何時必跑**：改 `notebooks/csv_cleaning/`、`scripts/check_case_eligibility.py`、`scripts/build_case_delivery_bundle.py`、`scripts/run_case_e2e_validation.py` 或標準 fixture 後；客戶 demo／Wave MVP 發布前建議跑
  - **交叉引用**：L1 信號對照 → `docs/mvp-standard-trace-path.md` §7；權威 DoD → `docs/MVP_CASE_E2E_DoD_v0.1.md`
  - **本輪索引**：`04_Workflows/WORKFLOW_INDEX.md` §1.5 已增指針
- progress_entry: |
    [W1-T3B-mvp-mainline-regression] done · 新增 `tests/test_mvp_mainline.py`、`scripts/run_mvp_mainline_regression.py`、`docs/mvp-mainline-regression.md` — demo_phase + sampleco 一鍵 E2E 回歸（6 tests OK）。與 `W1-T3_state.md` Eval CI 票區分；票號統一 `[待確認]`。
- followup_suggestions:
  - 可選：PR workflow 加入 `python scripts/run_mvp_mainline_regression.py`
  - 可選：`docs/testing.md` 交叉引用
  - Orchestrator 裁定 W1-T3 編號語境（Eval CI vs MVP 回歸）避免 dispatch 混淆

### Work Report（Scribe · 七節摘要）

| 節 | 內容 |
|----|------|
| §1 變更 | 本檔 `W1-T3B-mvp-mainline-regression_state.md`（新建 D_REPORT）；`04_Workflows/WORKFLOW_INDEX.md`（§1.5 增 2 條指針）；`W1-T2-mvp-trace-path_state.md`（C/D_REPORT） |
| §2 skeleton | 無 |
| §3 placeholder | W1-T3B 無正式 Reviewer C_REPORT；票號與 W1-T3 Eval CI 統一 `[待確認]` |
| §4 驗證 | `python scripts/run_mvp_mainline_regression.py -v` → 6/6 OK · exit 0 · PASS 訊息（Scribe 複驗 2026-06-10） |
| §5 阻塞 | 無 |
| §6 下一步 | Orchestrator 關票；可選 Reviewer 簽 W1-T3B；可選 CI 接線 |
| §7 override | 無 |
