# TICKET STATE · W9-T6 · non-tabular-fixture-log-analytics-co-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 9 · Non-Tabular Shadow Flow · Fixture NT-B

---

## FRAME

- **Title**: W9-T6 · non-tabular-fixture-log-analytics-co-v1
- **Wave / Motivation**: Wave 9 NT-B 實體 fixture；承接 W8-T4 §2 Case Type B、W9-T1 catalog、W9-T2 v2 path hints（`log-analytics-co`），取代 `_experiment_samples/nt_log_stub`，供 non-tabular preview / decision / W10-T1 CI helper 消費。**不**進 Tabular 主鏈。

- **Goal**: 建立 `cases/log-analytics-co/2026-0001` 最小可跑 fixture（Log Analysis · NT-B），含 `intake.json`、樣本 server log、unittest 驗證結構與 decision 對齊。

- **Scope**:
  1. `cases/log-analytics-co/2026-0001/intake.json`（`client_ref=log-analytics-co`、`content_type=server_logs`、`schema_hint=semi-structured` 等）
  2. `cases/log-analytics-co/2026-0001/raw/server_logs/` 最小樣本（≥1 `.log` 或 `.jsonl`）
  3. `tests/test_non_tabular_fixture_log_analytics_co_v1.py`
  4. 本票 `*_state.md` B_REPORT

- **NonScope / non_goals**:
  - ❌ 不實作 log parser / anomaly detector
  - ❌ 不改 Tabular 主鏈、W9-T5 docu-corp fixture
  - ❌ 不寫 production outbox
  - ❌ 不更新 Dashboard / Progress / WORKFLOW_INDEX（Scribe 輪）

- **Minimal Read Set**:
  - `docs/non-tabular-shadow-flow-blueprint-v1.md` §2 Case Type B
  - `docs/non-tabular-routing-catalog-v1.md` §3.2
  - `routing/non_tabular_routing_catalog_v1.yaml`（NT-B entry）
  - `routing/intake_decision_rules_v2.py`（`_NT_B_PATH_HINTS`）
  - `cases/_experiment_samples/nt_log_stub/intake.json`

- **AllowedPaths**:
  - `cases/log-analytics-co/**`
  - `tests/test_non_tabular_fixture_log_analytics_co_v1.py`
  - `04_Workflows/tickets/W9-T6-non-tabular-fixture-log-analytics-co-v1_state.md`

- **BlockedPaths / non_scope_paths**:
  - `cases/docu-corp/**`（W9-T5 邊界）
  - `scripts/run_mvp_mainline_regression.py` · `scripts/run_agent_standard_case_experiment.py`
  - `routing/*.py` · `tools/*` · `core/*` · `.github/workflows/*`
  - `04_Workflows/00_Agent_Work_Progress.md` · `docs/WAVE_PROGRESS_DASHBOARD.md`
  - 其他票 `*_state.md`

- **Dependencies**:
  - **W9-T1** · NT-B catalog spec
  - **W9-T2** · v2 decision NT-B branch
  - **W9-T4** · preview CLI（可選 smoke）

- **AcceptanceCriteria**:
  - **AC-1**：`cases/log-analytics-co/2026-0001/intake.json` 含 NT-B 必填欄位（`client_ref`、`content_type`、`schema_hint`、`time_range` 或等價 hint）
  - **AC-2**：`raw/server_logs/` 含 ≥1 可解析樣本 log 檔
  - **AC-3**：v2 decision 對該 case_dir 回傳 NT-B family / shadow `needs_review`（unittest）
  - **AC-4**：unittest 全綠；Tabular 主鏈檔案未改

- **VerificationCommands**:
  - `python -m unittest tests.test_non_tabular_fixture_log_analytics_co_v1 -v`
  - （可選）`python routing/intake_decision_rules_v2.py --task-type non-tabular.log.parse_and_summarize --case-dir cases/log-analytics-co/2026-0001 --json`

---

## STATE

- **overall_status**: `accepted_with_gaps_pending_scribe`
- **current_owner**: `scribe`
- **next_action**: Scribe：根據 B_REPORT/C_REPORT 更新 Dashboard/Progress；Orchestrator：決定 follow-up 票
- **last_updated**: 2026-06-15 · orchestrator
- **status_by_role**:
  - orchestrator: `done`
  - implementer: `done`
  - reviewer: `done`
  - scribe: `pending`

---

## B_REPORT

- **changed_files**:
  - `cases/log-analytics-co/2026-0001/intake.json`（新建）
  - `cases/log-analytics-co/2026-0001/raw/server_logs/app_server.log`（新建）
  - `tests/test_non_tabular_fixture_log_analytics_co_v1.py`（新建）
- **artifacts**:
  - NT-B fixture `cases/log-analytics-co/2026-0001`：`client_ref=log-analytics-co`、`content_type=server_logs`、`schema_hint=semi-structured`、`time_range=2026-05-01 to 2026-05-31`、`data_source=raw/server_logs/`
  - 樣本 log：`raw/server_logs/app_server.log`（5 行 semi-structured text log）
  - unittest 4 cases：目錄結構、intake 必填鍵、raw log 存在、v2 decision NT-B / `needs_review`
- **verification**:
  - `python -m unittest tests.test_non_tabular_fixture_log_analytics_co_v1 -v` → **4/4 OK**
  - （spot-check）`python routing/intake_decision_rules_v2.py --task-type non_tabular.log.analyze --case-dir cases/log-analytics-co/2026-0001 --json` → `ok=true`, `fixture_profile_tier=NT-B`, `decision=needs_review`, `risk_level=medium`
- **behavior_notes**:
  - Fixture 對齊 `docs/non-tabular-routing-catalog-v1.md` §3.2 與 `routing/non_tabular_routing_catalog_v1.yaml` NT-B entry；取代 `_experiment_samples/nt_log_stub` 的 placeholder 地位供 preview / CI helper 消費
  - 未實作 log parser / anomaly detector；未改 Tabular 主鏈、`routing/*`、`scripts/*`
  - unittest 同時驗證 `non_tabular.log.analyze` 與 catalog 別名 `non-tabular.log.parse_and_summarize`
- **deferred_items**:
  - 無（AC-1～AC-4 均已滿足）
  - optional：`volume_estimate` / `log_format` routing 欄位僅在 catalog domain_hints，未寫入 intake（非 AC 必填）
  - optional：W9-T4 preview CLI smoke 與 W10-T1 CI helper 指向本 fixture（後續票）

---

## C_REPORT

- **conclusion**: `accepted_with_gaps`
- **blocking_issues**: None
- **checks_summary**:
  - **已讀**：FRAME AC-1–AC-4；B_REPORT；`cases/log-analytics-co/2026-0001/intake.json`；`raw/server_logs/app_server.log`；`tests/test_non_tabular_fixture_log_analytics_co_v1.py`；`docs/non-tabular-routing-catalog-v1.md` §2.3／§3.2；`routing/non_tabular_routing_catalog_v1.yaml` NT-B entry；`routing/intake_decision_rules_v2.py`（`_NT_B_PATH_HINTS`、`_resolve_non_tabular_profile`、`_evaluate_non_tabular_decision_v2`）；對照 W9-T5 `test_non_tabular_fixture_docu_corp_v1.py` 對稱性；`cases/_experiment_samples/nt_log_stub/intake.json`（placeholder 對照）。
  - **AC-1**：`intake.json` 含 `client_ref=log-analytics-co`、`content_type=server_logs`、`schema_hint=semi-structured`、`time_range=2026-05-01 to 2026-05-31`（AC 等價 hint 成立）；並含 `case_id`、`sensitivity`、`data_source=raw/server_logs/`、`volume_gb=2`，與 catalog §3.2／yaml `intake_pattern` 語義一致。
  - **AC-2**：`app_server.log` 為 5 行 semi-structured text log（ISO 時間戳、LEVEL、key=value 欄位，含 INFO/WARN/ERROR），非空且可作為解析示例；符合「≥1 可解析樣本」門檻。
  - **AC-3**：測試 `test_v2_decision_nt_b_shadow_needs_review` 對 `non_tabular.log.analyze` 與 catalog 別名 `non-tabular.log.parse_and_summarize` 均斷言 `flow_family=non_tabular`、`fixture_profile_tier`／`case_profile_tier=NT-B`、`decision=needs_review`、`risk_level=medium`、`log_analysis_profile` signal、`shadow_flow_hook.eligible=true`；與 W9-T2 NT-B shadow 保守路徑一致。
  - **AC-4**：變更範圍僅新建 `cases/log-analytics-co/**` 與 `tests/test_non_tabular_fixture_log_analytics_co_v1.py`（git 為 untracked 新增）；未觸及 Tabular 主鏈、`routing/*`、`scripts/*`。
  - **測試覆蓋**：4 tests 分別覆蓋目錄結構、intake 必填鍵與值、`raw/server_logs` 樣本存在與最小長度、v2 decision；僅 import `evaluate_intake_decision_v2`，無外部 heavy pipeline／runner 依賴。
  - **重跑驗證**：
    - `python -m unittest tests.test_non_tabular_fixture_log_analytics_co_v1 -v` → **4/4 OK**
    - `python routing/intake_decision_rules_v2.py --task-type non_tabular.log.analyze --case-dir cases/log-analytics-co/2026-0001 --json` → `ok=true`, `fixture_profile_tier=NT-B`, `decision=needs_review`, `risk_level=medium`, `fixture_profile=log-analytics-co`
    - 同上 `--task-type non-tabular.log.parse_and_summarize` → 同 NT-B／`needs_review`；額外 `unsupported_non_tabular_task_type` signal（v2 預期行為，非 fixture 缺陷）
- **risk_level**: `low`
- **suggestions**:
  - **可選 intake 對齊**：catalog `domain_hints` 的 `volume_estimate`（如 `1-10GB`）與 `log_format`（如 `["text","json"]`）可於後續票補入 `intake.json` 或 README sidecar，利於 preview／CI 消費者不必再查 yaml。
  - **樣本擴充（非阻塞）**：現有 5 行 text log 已滿足 AC-2；若 W9-T4 preview 需展示多格式，可另增 `.jsonl` 樣本（catalog 支援 `text`／`json`）。
  - **測試微強化（可選）**：可增 assert `volume_gb` 與 catalog `intake_pattern` 範圍（現 intake 已有 `volume_gb: 2` 但 unittest 未斷言）。
  - **下游接線**：建議 W9-T4 preview CLI smoke 與 W10-T1 CI helper 將本 fixture 列為 NT-B 預設 case_dir，取代 `_experiment_samples/nt_log_stub`（stub 缺 `data_source`／`time_range`／raw 樣本）。
  - **`data_source` 慣例**：intake 為 `raw/server_logs/`（目錄尾斜線），catalog 示例為 `raw/server_logs/*.log`；兩者皆符合 yaml `^raw/server_logs/.*$`，無需本輪修改。

---

## D_REPORT

- **docs_updates**:
  - `docs/non-tabular-routing-catalog-v1.md` §3.2 — 新增 **Example fixture**: `cases/log-analytics-co/2026-0001`
  - `docs/WAVE_PROGRESS_DASHBOARD.md` — Wave 9 表追加 W9-T6 列、驗證命令、註解（NT fixtures landed / real-data gap unblocked）
  - `04_Workflows/00_Agent_Work_Progress.md` — 新增「W9-T5/T6：Non-Tabular fixtures」收口小節
- **progress_entry**: W9-T6 交付 NT-B fixture `cases/log-analytics-co/2026-0001`（`client_ref=log-analytics-co`、`server_logs`、`semi-structured`、`time_range` + `raw/server_logs/app_server.log`）；v2 decision → NT-B / `needs_review` / medium risk；4/4 tests OK；Reviewer `accepted_with_gaps`。
- **followup_suggestions**:
  - **W9-T7-nt-multi-format-log-samples-v1** — 增 `.jsonl` 樣本、`volume_estimate` / `log_format` intake 對齊（C_REPORT optional）
  - **W9-T4-preview-fixture-rewire-v1** — preview CLI NT-B 預設 case_dir 改指向本 fixture
  - **W10-T1-ci-nt-fixtures-v1** — CI helper 取代 `_experiment_samples/nt_log_stub`
  - **W9-T8-stub-deprecate-v1** — stub 清理與 cases index 更新

---

## O_NOTES

| date | role | action |
|------|------|--------|
| 2026-06-15 | orchestrator | 起票 FRAME 草稿（本檔） |
| 2026-06-15 | implementer | 建 `cases/log-analytics-co/2026-0001` fixture + unittest；B_REPORT 填寫；4/4 tests OK |
| 2026-06-15 | orchestrator | reviewer accepted_with_gaps；等待 Scribe 更新 Wave 9 NT fixture 段落 |
