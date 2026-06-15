# TICKET STATE · W9-T2 · Non-Tabular Decision Rules v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 9 · Non-Tabular Shadow · Intake Decision Helper v2 extension

---

## FRAME

- Title: W9-T2 · non-tabular-decision-rules-v1
- Goal: 在 `intake-decision-rules-v2` 基礎上，為 `non_tabular.*` family 增加初版 decision helper（NT-A / NT-B profile 識別、結構化 decision）；Tabular 行為完全不變。
- Scope:
  - 擴展 `routing/intake_decision_rules_v2.py`（`non_tabular.*` 分支 · NT-A/NT-B profile · R-NT1 reject）
  - 更新 `docs/intake-decision-rules-v2.md`（§3.1 NT-A/NT-B · reject table R5/R6）
  - 更新 `scripts/run_agent_intake_decision_demo.py`（文檔 · `--use-v2` 支援 non_tabular.*）
  - 更新 `tests/test_intake_decision_rules_v2.py`（NT-A/NT-B · corrupt/unparseable · Tabular regression）
  - 更新 `04_Workflows/WORKFLOW_INDEX.md`、`docs/WAVE_PROGRESS_DASHBOARD.md`
- NonScope:
  - **不**改 `routing/intake_decision_rules_v1.py`
  - **不**改 Tabular decision 結果
  - **不**實作 non-tabular glue / tool catalog（W9-T3/T4）
  - **不**建真實 docu-corp / log-analytics-co fixtures（W9-T5/T6）
  - **不**接主鏈 / orchestrator 預設路徑
- AllowedPaths:
  - `routing/intake_decision_rules_v2.py`
  - `docs/intake-decision-rules-v2.md`
  - `scripts/run_agent_intake_decision_demo.py`
  - `tests/test_intake_decision_rules_v2.py`
  - `04_Workflows/tickets/W9-T2-non-tabular-decision-rules-v1_state.md`
  - `04_Workflows/WORKFLOW_INDEX.md`
  - `docs/WAVE_PROGRESS_DASHBOARD.md`
- BlockedPaths:
  - `routing/intake_decision_rules_v1.py`
  - `routing/intake_to_tabular_glue.py`
  - `scripts/run_agent_standard_case_experiment.py`
- Dependencies:
  - **W8-T2** · v2 Tabular tiers
  - **W8-T4** · non-tabular blueprint (NT-A/NT-B · R-NT1)
  - **W9-T1** · routing catalog（optional；未就緒時依 blueprint path/task_type 解析）
- AcceptanceCriteria:
  - **AC-1**：`non_tabular.document.extract` + docu-corp hints → `NT-A` · `needs_review` / medium
  - **AC-2**：`non_tabular.log.analyze` + log-analytics hints → `NT-B` · `needs_review` / medium
  - **AC-3**：corrupt / unparseable intake → `reject` / high（R-NT1）
  - **AC-4**：Tabular A/B/C/D 與 v1 一致（unittest 未破）
  - **AC-5**：`gov.*` 等非 supported family 仍 `reject`
  - **AC-6**：`python -m unittest tests.test_intake_decision_rules_v2 -v` 全綠

---

## STATE

- overall_status: accepted_with_gaps
- current_owner: orchestrator
- next_action: closed — 後續追蹤：W9-T5/T6 real fixtures、W9-T4 glue 消費 planned_tools、W9-T1 catalog 強制整合（見 C_REPORT gaps）
- last_updated: 2026-06-15 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

- changed_files:
  - `routing/intake_decision_rules_v2.py`（non_tabular.* 分支 · NT-A/NT-B · R-NT1 reject）
  - `docs/intake-decision-rules-v2.md`（§2.3–§3.1 · reject table）
  - `scripts/run_agent_intake_decision_demo.py`（non_tabular.* 用法）
  - `tests/test_intake_decision_rules_v2.py`（NT-A/NT-B · corrupt/unparseable）
  - `04_Workflows/tickets/W9-T2-non-tabular-decision-rules-v1_state.md`（本檔）
  - `04_Workflows/WORKFLOW_INDEX.md`（W9-T2 條目）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（Wave 9 W9-T2 行）
- skeleton: `suggested_route.planned_tools=[]` · shadow_only stub（待 W9-T4 glue）
- placeholder: W9-T1 catalog YAML 未就緒；profile 依 blueprint task_type + path + intake.json
- verification:
  - `python -m unittest tests.test_intake_decision_rules_v2 -v`
  - Tabular regression：`test_demo_phase_tier_a_*` · `test_sampleco_tier_b_*` · `test_additional_demo_*` · `test_sandbox_client_*`
- blockers: 無
- next_steps: W9-T1 catalog · W9-T4 glue · W9-T5/T6 fixtures
- reviewer_reverification: 2026-06-15 · `python -m unittest tests.test_intake_decision_rules_v2 -v` → 15/15 OK

---

## C_REPORT

- conclusion: **accepted_with_gaps**
- blocking_issues: 無
- checks_summary:
  - **AC-1 ✅**: NT-A `non_tabular.document.extract` → `needs_review` / medium（`test_nt_a_document_extract_needs_review`）
  - **AC-2 ✅**: NT-B `non_tabular.log.analyze` → `needs_review` / medium（`test_nt_b_log_analyze_needs_review`）
  - **AC-3 ✅**: corrupt / unparseable → `reject` / high R-NT1（2 tests）
  - **AC-4 ✅**: Tabular A/B/C/D tier regression 未破（6 tests）
  - **AC-5 ✅**: 非 supported family（含 `gov.*`）→ `reject`（`test_non_tabular_family_reject_with_shadow_hook`）
  - **AC-6 ✅**: v2 suite 15/15 · Reviewer 複驗 2026-06-15
- risk_level: low
- gaps:
  - `suggested_route.planned_tools=[]` shadow stub（待 W9-T4 glue 消費）
  - profile 解析 fallback blueprint path/task_type（W9-T1 catalog 未強制）
  - real docu-corp / log-analytics fixtures 未建（W9-T5/T6）
- suggestions: 下輪接 W9-T4 preview glue 與 fixture 票

---

## D_REPORT

- docs_updates: `docs/intake-decision-rules-v2.md` §3.1 NT-A/NT-B 已交付；Dashboard/Progress 註解留 Orchestrator Step 5
- progress_entry: W9-T2 implementer done → **accepted_with_gaps** — v2 non_tabular.* NT-A/NT-B + R-NT1 reject + Tabular regression 15/15 OK
- followup_suggestions: W9-T5/T6 fixtures · W9-T4 glue 消費 planned_tools

---

## O_NOTES

| date | role | action |
|------|------|--------|
| 2026-06-15 | scribe | W9-T2 Reviewer→Scribe 收口 · accepted_with_gaps · D_REPORT filled based on reviewer acceptance |
| 2026-06-15 | orchestrator | STATE 關票 · overall_status accepted_with_gaps · Dashboard/Progress 收口 |
