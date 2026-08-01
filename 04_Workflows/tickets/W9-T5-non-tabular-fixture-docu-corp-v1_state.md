# TICKET STATE · W9-T5 · non-tabular-fixture-docu-corp-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 9 · Non-Tabular Shadow Flow · Fixture NT-A

---

## FRAME

- **Title**: W9-T5 · non-tabular-fixture-docu-corp-v1
- **Wave / Motivation**: Wave 9 NT-A 實體 fixture；承接 W8-T4 §2 Case Type A、W9-T1 catalog、W9-T2 v2 decision path hints（`docu-corp`），取代 `_experiment_samples/nt_docu_stub` 的 placeholder 地位，供 preview CLI / decision demo / 後續 CI helper 使用。**不**進 Tabular 主鏈。

- **Goal**: 建立 `cases/docu-corp/2026-0001` 最小可跑 fixture（Document Processing · NT-A），含 `intake.json`、樣本 raw 文件、結構化 unittest 驗證；對齊 `docs/non-tabular-routing-catalog-v1.md` §3.1 與 `routing/non_tabular_routing_catalog_v1.yaml` NT-A 欄位。

- **Scope**:
  1. `cases/docu-corp/2026-0001/intake.json`（`client_ref=docu-corp`、`content_type=mixed_documents`、`schema_hint=schema-free` 等）
  2. `cases/docu-corp/2026-0001/raw/documents/` 最小樣本（≥1 個 text/markdown 檔；PDF/OCR **optional skeleton**）
  3. `tests/test_non_tabular_fixture_docu_corp_v1.py` — 目錄結構、intake 必填鍵、v2 decision path hint 對齊
  4. 本票 `*_state.md` B_REPORT

- **NonScope / non_goals**:
  - ❌ 不實作 heavy extractors / OCR pipeline
  - ❌ 不改 Tabular `cases/demo_phase` / `sampleco` / 主鏈腳本
  - ❌ 不寫入 production outbox；不跑 `run_non_tabular_experiment_preview` execute 模式
  - ❌ 不建 `cases/log-analytics-co/`（W9-T6）
  - ❌ 不更新 WORKFLOW_INDEX / WAVE_PROGRESS_DASHBOARD（留 Scribe 輪）

- **Minimal Read Set**:
  - `docs/non-tabular-shadow-flow-blueprint-v1.md` §2 Case Type A
  - `docs/non-tabular-routing-catalog-v1.md` §3.1
  - `routing/non_tabular_routing_catalog_v1.yaml`（NT-A entry）
  - `routing/intake_decision_rules_v2.py`（`_NT_A_PATH_HINTS`）
  - `cases/_experiment_samples/nt_docu_stub/intake.json`（對照）

- **AllowedPaths**:
  - `cases/docu-corp/**`
  - `tests/test_non_tabular_fixture_docu_corp_v1.py`
  - `04_Workflows/tickets/W9-T5-non-tabular-fixture-docu-corp-v1_state.md`

- **BlockedPaths / non_scope_paths**:
  - `scripts/run_mvp_mainline_regression.py` · `scripts/run_agent_standard_case_experiment.py`
  - `routing/*.py`（除唯讀對照外不修改）
  - `tools/*` · `core/*` · `.github/workflows/*`
  - `04_Workflows/00_Agent_Work_Progress.md` · `docs/WAVE_PROGRESS_DASHBOARD.md`
  - 其他票 `*_state.md`（FRAME/STATE/C/D）

- **Dependencies**:
  - **W9-T1** · non-tabular routing catalog spec
  - **W9-T2** · v2 decision rules NT-A branch
  - **W9-T4** · preview CLI（可選 smoke；本票不強制改 preview 腳本）

- **AcceptanceCriteria**:
  - **AC-1**：`cases/docu-corp/2026-0001/intake.json` 存在且含 `client_ref`、`case_id`、`content_type`、`schema_hint`、`sensitivity`
  - **AC-2**：`raw/documents/` 含 ≥1 可讀樣本檔；路徑符合 catalog `data_source` 慣例
  - **AC-3**：`evaluate_intake_decision`（v2，`non_tabular.document.*`）對該 case_dir 回傳 NT-A family / `needs_review` 或等價 shadow 決策（unittest 斷言）
  - **AC-4**：`tests/test_non_tabular_fixture_docu_corp_v1.py` 全綠；未修改 Tabular 主鏈檔案

- **VerificationCommands**:
  - `python -m unittest tests.test_non_tabular_fixture_docu_corp_v1 -v`
  - （可選 spot-check）`python routing/intake_decision_rules_v2.py --task-type non-tabular.document.clean_and_annotate --case-dir cases/docu-corp/2026-0001 --json`

---

## STATE

- **overall_status**: `draft`
- **current_owner**: `orchestrator`
- **next_action**: Implementer：依 FRAME 建 `cases/docu-corp/` 目錄與 unittest skeleton
- **last_updated**: 2026-06-15 · orchestrator（起票草稿）
- **status_by_role**:
  - orchestrator: `done`
  - implementer: `pending`
  - reviewer: `pending`
  - scribe: `pending`

---

## B_REPORT

- **changed_files**:
  - `cases/docu-corp/2026-0001/intake.json`（新建）
  - `cases/docu-corp/2026-0001/raw/documents/sample_brief.md`（新建）
  - `tests/test_non_tabular_fixture_docu_corp_v1.py`（新建）
  - `04_Workflows/tickets/W9-T5-non-tabular-fixture-docu-corp-v1_state.md`（B_REPORT / O_NOTES 本輪填寫）
- **artifacts**:
  - NT-A fixture：`cases/docu-corp/2026-0001/`（intake + 1× markdown raw sample）
  - unittest：`tests/test_non_tabular_fixture_docu_corp_v1.py`（4 tests）
- **verification**:
  - `python -m unittest tests.test_non_tabular_fixture_docu_corp_v1 -v` → **OK**（4/4 passed）
  - （spot-check）`python routing/intake_decision_rules_v2.py --task-type non-tabular.document.clean_and_annotate --case-dir cases/docu-corp/2026-0001 --json` → `ok=true`, `flow_family=non_tabular`, `fixture_profile_tier=NT-A`, `decision=needs_review`
  - AC-4：本輪僅 touch AllowedPaths；未改 Tabular 主鏈 / routing / scripts / CI
- **behavior_notes**:
  - `intake.json` 對齊 stub 升級：`client_ref=docu-corp`、`case_id=docu-2026-0001`、`content_type=mixed_documents`、`schema_hint=schema-free`、`sensitivity=internal`；另含 catalog 慣例 `data_source=raw/documents/`、`document_count=1`
  - v2 decision 以 `docu-corp` path hint + `mixed_documents` content_type 解析 NT-A；`non_tabular.document.extract` 與 `non-tabular.document.clean_and_annotate` 皆回 `needs_review` shadow 決策
  - raw 樣本為純 text/markdown（`sample_brief.md`），無 binary PDF/DOCX
- **deferred_items**:
  - PDF / DOCX / PNG / JPG 實體樣本與 OCR pipeline（NonScope）
  - `run_non_tabular_experiment_preview` execute 模式 smoke（本票不強制）
  - `cases/_experiment_samples/nt_docu_stub` 保留未刪（下游可另票 deprecate）
  - cases index / WORKFLOW_INDEX 更新留 Scribe 輪

---

## C_REPORT

- **conclusion**: <!-- Reviewer 填 -->
- **blocking_issues**: <!-- Reviewer 填 -->
- **checks_summary**: <!-- Reviewer 填 -->
- **risk_level**: <!-- Reviewer 填 -->
- **suggestions**: <!-- Reviewer 填 -->

---

## D_REPORT

- **docs_updates**:
  - `docs/non-tabular-routing-catalog-v1.md` §3.1 — 新增 **Example fixture**: `cases/docu-corp/2026-0001`
  - `docs/WAVE_PROGRESS_DASHBOARD.md` — Wave 9 表追加 W9-T5 列、驗證命令、註解（NT fixtures landed / real-data gap unblocked）
  - `04_Workflows/00_Agent_Work_Progress.md` — 新增「W9-T5/T6：Non-Tabular fixtures」收口小節
- **progress_entry**: W9-T5 交付 NT-A fixture `cases/docu-corp/2026-0001`（`client_ref=docu-corp`、`mixed_documents`、`schema-free` + `raw/documents/sample_brief.md`）；v2 decision → NT-A / `needs_review` / medium risk；4/4 tests OK；PDF/OCR 樣本 deferred。
- **followup_suggestions**:
  - **W9-T7-nt-ocr-samples-v1** — PDF/DOCX/PNG/JPG 實體樣本與 OCR pipeline（B_REPORT deferred）
  - **W9-T4-preview-fixture-rewire-v1** — preview CLI smoke 改指向 `cases/docu-corp/2026-0001` 取代 `nt_docu_stub`
  - **W10-T1-ci-nt-fixtures-v1** — CI helper NT-A 預設 case_dir 升格至 real fixture
  - **W9-T8-stub-deprecate-v1** — 標記 deprecate `cases/_experiment_samples/nt_docu_stub` 並更新 cases index

---

## O_NOTES

| date | role | action |
|------|------|--------|
| 2026-06-15 | orchestrator | 起票 FRAME 草稿（本檔） |
| 2026-06-15 | implementer | 建 `cases/docu-corp/2026-0001` fixture + unittest；AC-1–AC-4 驗收綠燈；填 B_REPORT |
