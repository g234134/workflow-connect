# TICKET STATE · W5-T1 · Intake Decision Rules v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 5 · Tabular MVP · Intake Decision Helper

---

## FRAME

- Title: W5-T1 · Intake Decision Rules v1
- Goal: 在 Tabular MVP 基礎上新增接案決策規則 v1，對 intake case 輸出 `decision` / `risk_level` / `rationale` / `suggested_route`；本票為內部判斷 helper，不改主鏈 routing。
- Scope:
  - 新增 `routing/intake_decision_rules_v1.py` → `evaluate_intake_decision(task_type, case_dir) -> dict`
  - 新增 `docs/intake-decision-rules-v1.md`
  - 新增 `tests/test_intake_decision_rules_v1.py`
  - v1 支援 Tabular 家族：`tabular.cleaning.mvp`、`tabular.cleaning.regression`、`tabular.intake.new_case`
  - 消費 W4-T1 `plan_tabular_route`；allowlist fixture（demo_phase / sampleco）
  - 模組內建 CLI demo（`--task-type` / `--case-dir` / `--json`）
  - 更新 `04_Workflows/WORKFLOW_INDEX.md`、`docs/WAVE_PROGRESS_DASHBOARD.md` Wave 5 區塊
- NonScope:
  - **不**改 `scripts/new_cleaning_case.py`、`app/local_ui.py`
  - **不**接真實下單或金流
  - **不**改主鏈 routing / intake 行為
  - **不**接 LLM judge
  - **不**改 Gov routing、Selector、Executor
- AllowedPaths:
  - `routing/intake_decision_rules_v1.py`
  - `docs/intake-decision-rules-v1.md`
  - `tests/test_intake_decision_rules_v1.py`
  - `04_Workflows/tickets/W5-T1-intake-decision-rules-v1_state.md`
  - `04_Workflows/WORKFLOW_INDEX.md`
  - `docs/WAVE_PROGRESS_DASHBOARD.md`
- BlockedPaths:
  - `scripts/new_cleaning_case.py`
  - `app/local_ui.py`
  - `routing/intake_to_tabular_glue.py`（唯讀消費）
  - `HARNESS_CONSTITUTION.md` · `ENGINEERING_CONTRACT.md` · `AGENTS.md` · `.cursor/rules/*`
- Dependencies:
  - **W4-T1** · `routing/intake_to_tabular_glue.py`
  - **W2-T1** · `routing/intake_routing_catalog_v1.yaml`
  - **W3-TL-T1** · `tools/tabular_tool_catalog_v1.json`
- Risks:
  - 決策規則與 glue notes 漂移 → 以 glue `notes` / `inferred_gate_notes` 為信號來源
  - 誤接主鏈 → 本票僅 helper，無 feature flag 接入
- OutputArtifacts:
  - `routing/intake_decision_rules_v1.py`
  - `docs/intake-decision-rules-v1.md`
  - `tests/test_intake_decision_rules_v1.py`
- AcceptanceCriteria:
  - **AC-1**：`demo_phase` + `tabular.cleaning.mvp` → `needs_review` 或 `auto_accept`（依規則）；`tabular.intake.new_case` → `auto_accept`
  - **AC-2**：`sampleco` + `tabular.cleaning.mvp` → `needs_review`（ambiguity / human_review 信號）
  - **AC-3**：non-tabular / bad case_dir → `reject`
  - **AC-4**：輸出結構含 `decision` / `risk_level` / `rationale` / `suggested_route`
  - **AC-5**：`python -m unittest tests.test_intake_decision_rules_v1 -v` 全綠
  - **AC-6**：未修改禁改檔
- VerificationCommands:
  - `python -m unittest tests.test_intake_decision_rules_v1 -v`
  - `python routing/intake_decision_rules_v1.py --task-type tabular.cleaning.mvp --case-dir cases/demo_phase --json`

---

## STATE

- overall_status: implementer done
- current_owner: orchestrator
- next_action: Reviewer 審查 AC-1–AC-6；Scribe 可選收口 Progress
- last_updated: 2026-06-10 · implementer
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

- changed_files:
  - `routing/intake_decision_rules_v1.py`（新增）
  - `docs/intake-decision-rules-v1.md`（新增）
  - `tests/test_intake_decision_rules_v1.py`（新增）
  - `04_Workflows/tickets/W5-T1-intake-decision-rules-v1_state.md`（新增）
  - `04_Workflows/WORKFLOW_INDEX.md`（Wave 5 索引）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（Wave 5 區塊）
- artifacts: 無
- verification: 見 implementer 回覆 §4 測試結果
- behavior_notes:
  - `tabular.intake.new_case` 在 allowlist 上 `auto_accept`（intake 請求，不繼承 cleaning 審查信號）
  - `tabular.cleaning.mvp` 在 demo_phase 因 `manual_review_required` → `needs_review`
  - sampleco 因 `human_review_required` / `schema_ambiguous` → `needs_review`
- deferred_items:
  - 接入主鏈 intake CLI / Local UI（另票）
  - LLM judge 覆核層（另票）

---

## C_REPORT

- conclusion: pending
- blocking_issues: 無
- checks_summary: pending Reviewer
- risk_level: low
- suggestions: 無

---

## D_REPORT

- docs_updates: 本票已新增 `docs/intake-decision-rules-v1.md`；Dashboard / WORKFLOW_INDEX 已更新
- progress_append: 建議 Scribe 於 `00_Agent_Work_Progress.md` 末尾追加 W5-T1 條目
