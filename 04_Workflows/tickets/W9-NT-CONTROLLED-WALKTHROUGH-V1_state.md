# TICKET STATE · W9-NT-CONTROLLED-WALKTHROUGH-V1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。
> Wave：Wave 9 · Non-Tabular Controlled Shadow · End-to-End Walkthrough v1

---

## FRAME

- **Title**: W9-NT-CONTROLLED-WALKTHROUGH-V1 · Non-Tabular Controlled End-to-End Walkthrough
- **Wave / Motivation**: Wave 9 NT fixtures (docu-corp + log-analytics-co) 已落地，但一線無統一文件可循。建立單一 walkthrough，讓開發者可依序跑通 Tabular + Non-Tabular controlled 路徑，得到可解讀 JSON 輸出與 audit quickview，不必口頭詢問 Orchestrator。

- **Goal**: 
  1. 設計並驗證 8–10 步固定命令鏈（從環境確認到 audit quickview）。
  2. 在 `docs/agent-and-non-tabular-lines-readme-v2.md` 新增 `§ Non-Tabular Controlled Walkthrough (docu-corp + log-analytics-co)`。
  3. walkthrough 需覆蓋 NT-A (`docu-corp/2026-0001`) 與 NT-B (`log-analytics-co/2026-0001`)。
  4. 輸出：JSON 結果 + 可讀 audit quickview；明確標示 deferred 項目（OCR / heavy execute）。

- **Scope**:
  1. 讀取 W9-T5、W9-T6 的 fixture state，確認 AC 已滿足。
  2. 規劃命令序列（unittest → preview → audit quickview）。
  3. 實際 dry-run 驗證所有命令。
  4. 寫入 walkthrough 章節至 README v2。
  5. 本票 `*_state.md` B_REPORT / O_NOTES 填寫。

- **NonScope / non_goals**:
  - ❌ 不實作 heavy tools（OCR、log parser 真執行）。
  - ❌ 不改任何 `*.py` code 檔案。
  - ❌ 不改 Tabular 主鏈行為。
  - ❌ 不建立新 fixture（僅使用 W9-T5/T6 已交付者）。

- **Minimal Read Set**:
  - `04_Workflows/tickets/W9-T5*`, `W9-T6*` state 檔
  - `docs/agent-and-non-tabular-lines-readme-v2.md`
  - `cases/docu-corp/2026-0001/intake.json`
  - `cases/log-analytics-co/2026-0001/intake.json`

- **AllowedPaths**:
  - `docs/agent-and-non-tabular-lines-readme-v2.md`（新增 walkthrough 章節）
  - `04_Workflows/tickets/W9-NT-CONTROLLED-WALKTHROUGH-V1_state.md`

- **BlockedPaths / non_scope_paths**:
  - `cases/*`（僅讀取，不修改）
  - `scripts/*.py`（僅執行，不修改）
  - `tests/*.py`（僅執行，不修改）
  - 其他 tickets 的 state 檔
  - `04_Workflows/00_Agent_Work_Progress.md`

- **Dependencies**:
  - **W9-T5** · docu-corp fixture landed
  - **W9-T6** · log-analytics-co fixture landed

- **AcceptanceCriteria**:
  - **AC-1**：命令鏈 ≤10 步，一線可直接複製執行。
  - **AC-2**：覆蓋 NT-A + NT-B，輸出 `ok: true` 與 `decision: needs_review`。
  - **AC-3**：audit quickview 可讀取 non_tabular_experiment outbox 並顯示 `flow_family: non_tabular`。
  - **AC-4**：README v2 新增章節含：準備條件、步驟 1–N、預期輸出描述、錯誤排查提示。

- **VerificationCommands**:
  - `python -m unittest tests.test_non_tabular_fixture_docu_corp_v1 -v`
  - `python -m unittest tests.test_non_tabular_fixture_log_analytics_co_v1 -v`
  - `python scripts/run_non_tabular_experiment_preview.py --task-type non_tabular.document.extract --case-dir cases/docu-corp/2026-0001 --format json`
  - `python scripts/run_non_tabular_experiment_preview.py --task-type non_tabular.log.analyze --case-dir cases/log-analytics-co/2026-0001 --format json`
  - `python scripts/run_agent_audit_quickview.py --case-ref cases_docu-corp_2026-0001 --format json`
  - `python scripts/run_agent_audit_quickview.py --case-ref cases_log-analytics-co_2026-0001 --format json`

---

## STATE

- **overall_status**: `implementer_done_pending_review`
- **current_owner**: `implementer`
- **next_action**: Reviewer 驗證 walkthrough 步驟可重現
- **last_updated**: 2026-06-16 · implementer
- **status_by_role**:
  - orchestrator: `pending`
  - implementer: `done`
  - reviewer: `pending`
  - scribe: `pending`

---

## B_REPORT

- **changed_files**:
  - `docs/agent-and-non-tabular-lines-readme-v2.md`（新增 § Non-Tabular Controlled Walkthrough 章節）
  - `04_Workflows/tickets/W9-NT-CONTROLLED-WALKTHROUGH-V1_state.md`（本檔新建）

- **artifacts**:
  - Walkthrough 章節：`docs/agent-and-non-tabular-lines-readme-v2.md` § Non-Tabular Controlled Walkthrough
  - 命令鏈摘要：8 步驟（見下方 commands）

- **commands**:
  ```bash
  # Step 1: 確認 fixtures 存在 (NT-A)
  ls cases/docu-corp/2026-0001/
  cat cases/docu-corp/2026-0001/intake.json

  # Step 2: 確認 fixtures 存在 (NT-B)
  ls cases/log-analytics-co/2026-0001/
  cat cases/log-analytics-co/2026-0001/intake.json

  # Step 3: 驗證 NT-A fixture 結構（unittest）
  python -m unittest tests.test_non_tabular_fixture_docu_corp_v1 -v

  # Step 4: 驗證 NT-B fixture 結構（unittest）
  python -m unittest tests.test_non_tabular_fixture_log_analytics_co_v1 -v

  # Step 5: NT-A preview（Document Extraction）
  python scripts/run_non_tabular_experiment_preview.py \
    --task-type non_tabular.document.extract \
    --case-dir cases/docu-corp/2026-0001 --format json

  # Step 6: NT-B preview（Log Analysis）
  python scripts/run_non_tabular_experiment_preview.py \
    --task-type non_tabular.log.analyze \
    --case-dir cases/log-analytics-co/2026-0001 --format json

  # Step 7: NT-A audit quickview
  python scripts/run_agent_audit_quickview.py \
    --case-ref cases_docu-corp_2026-0001 --format json

  # Step 8: NT-B audit quickview
  python scripts/run_agent_audit_quickview.py \
    --case-ref cases_log-analytics-co_2026-0001 --format json
  ```

- **verification**:
  - Step 3 → **OK** (4/4 passed)：`test_case_directory_structure`, `test_intake_required_keys_and_values`, `test_raw_documents_has_readable_sample`, `test_v2_decision_nt_a_shadow_needs_review`
  - Step 4 → **OK** (4/4 passed)：同上四項對應 NT-B
  - Step 5 → **OK**：`ok: true`, `decision: needs_review`, `risk_level: medium`, `fixture_profile_tier: NT-A`, `final_status: preview_ready`, `flow_family: non_tabular`
  - Step 6 → **OK**：`ok: true`, `decision: needs_review`, `risk_level: medium`, `fixture_profile_tier: NT-B`, `final_status: preview_ready`, `flow_family: non_tabular`
  - Step 7 → **OK**：`ok: true`, `flow_family: non_tabular`, `source_kind: non_tabular_experiment`, `decision: needs_review`
  - Step 8 → **OK**：同上，NT-B 版本
  - AC-1～AC-4 均滿足

- **behavior_notes**:
  - Walkthrough 假設執行者已在 repo 根目錄，Python 環境已安裝相依套件（見 README v2 §6）。
  - Non-Tabular preview 為 **shadow-only**，不改 Tabular 主鏈，不執行 heavy tools。
  - Audit quickview 正確識別 `non_tabular_experiment` outbox，顯示 `flow_family: non_tabular`。
  - 輸出 JSON 可透過 `jq` 或 Python `json.tool` 進一步過濾（如 `| jq '.decision'`）。

- **deferred_items**:
  - **OCR / PDF extraction**：本 walkthrough 僅觸及 `preview` 模式；`--with-metadata-extraction` 與 heavy execute 不在 v1 範圍。
  - **Run mode**：W12+ 才解鎖真執行（OCR、parser），現階段僅 `preview_ready`。
  - **Checkpoint A/B**：Non-Tabular shadow 流程無 HITL checkpoint（設計如此），故 audit quickview 中 `checkpoint_a/b.on_disk: false` 為預期行為。

---

## C_REPORT

- **conclusion**: `accepted`
- **blocking_issues**: None
- **checks_summary**: |
    1. 對照 FRAME AC-1~AC-4 與 B_REPORT verification 表格：8 步命令鏈、NT-A/B 雙 fixture 驗證、audit quickview JSON 欄位均符合預期。
    2. 檢查 README v2 §3.5：準備條件、步驟 1–8、預期輸出三段（unittest/preview/audit）、錯誤排查 4 項均已到位。
    3. 確認 deferred 項目（OCR / heavy execute / Run mode）與 FRAME NonScope 一致，不視為 v1 blocking。
- **risk_level**: `low`
- **suggestions**: |
    - **W9-T7 後續**: OCR / PDF extraction 實作後，於 README §3.5 增設 Step 9 `--with-metadata-extraction` 示範。
    - **W12-T3 後續**: Run mode 解鎖後，增設 S7–S10 真執行步驟與 Checkpoint B 說明。
    - **Progress/Dashboard 連結**: 可於 `04_Workflows/00_Agent_Work_Progress.md` Wave 9 區塊追加「Walkthrough 已交付 → 見 README v2 §3.5」交叉引用，便於一線快速定位。

---

## D_REPORT

- **docs_updates**:
  - `docs/agent-and-non-tabular-lines-readme-v2.md` — 新增 § Non-Tabular Controlled Walkthrough (docu-corp + log-analytics-co)
- **progress_entry**: W9-NT controlled walkthrough v1：`accepted` · 8 步命令鏈（NT-A docu-corp + NT-B log-analytics-co）· audit quickview 整合 · README v2 §3.5；OCR/run mode deferred。
- **followup_suggestions**:
  - **W9-T7-nt-ocr-samples-v1** — heavy tools 實作後，更新 walkthrough 增設 `--with-metadata-extraction` 步驟。
  - **W12-T3-nt-run-mode-v1** — run mode 解鎖後，增設 S7-S10 真執行步驟與 Checkpoint B 說明。

---

## O_NOTES

| date | role | action |
|------|------|--------|
| 2026-06-16 | implementer | 依 FRAME 實作 walkthrough：8 步驟命令鏈設計、dry-run 驗證、README v2 章節新增、B_REPORT 填寫 |
