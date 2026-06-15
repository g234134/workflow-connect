# TICKET STATE · W8-T2 · Decision Rules v2 Profile and Reject Reduction

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 8 · Tabular MVP · Intake Decision Helper v2

---

## FRAME

- Title: W8-T2 · decision-rules-v2-profile-and-reject-reduction
- Goal: 在 W5-T1 / W6-T5 / W7-T1–T4 基礎上升級 intake decision rules：A/B/C/D fixture profile 偵測、降低不必要 reject、預留 non-Tabular shadow flow 鉤子。
- Scope:
  - 新增 `docs/intake-decision-rules-v2.md`
  - 新增 `routing/intake_decision_rules_v2.py` → `evaluate_intake_decision_v2(task_type, case_dir, *, use_v1_fallback=True)`
  - 更新 `scripts/run_agent_intake_decision_demo.py`（`--use-v2` opt-in）
  - 新增 `tests/test_intake_decision_rules_v2.py`
  - 更新 `04_Workflows/WORKFLOW_INDEX.md`、`docs/WAVE_PROGRESS_DASHBOARD.md`
- NonScope:
  - **不**改主鏈 / UI / Gov
  - **不**改 W5-T1 production decision allowlist（demo_phase / sampleco only）
  - **不**改 `routing/intake_to_tabular_glue.py`
  - **不**改 orchestrator 預設 decision 路徑（仍 v1）
- AllowedPaths:
  - `docs/intake-decision-rules-v2.md`
  - `routing/intake_decision_rules_v2.py`
  - `scripts/run_agent_intake_decision_demo.py`
  - `tests/test_intake_decision_rules_v2.py`
  - `04_Workflows/tickets/W8-T2-decision-rules-v2-profile-and-reject-reduction_state.md`
  - `04_Workflows/WORKFLOW_INDEX.md`
  - `docs/WAVE_PROGRESS_DASHBOARD.md`
- BlockedPaths:
  - `scripts/new_cleaning_case.py`
  - `app/local_ui.py`
  - `routing/intake_decision_rules_v1.py`（不修改 v1 行為）
  - `scripts/run_agent_standard_case_experiment.py`（仍 v1）
- Dependencies:
  - **W5-T1** · `routing/intake_decision_rules_v1.py`
  - **W4-T1** · `routing/intake_to_tabular_glue.py`
  - **W7-T1** · C/D fixtures
  - **W7-T4** · governance v2
- AcceptanceCriteria:
  - **AC-1**：A/B fixture cleaning 與 v1 一致（needs_review）
  - **AC-2**：C/D fixture → needs_review（非 reject）；`experimental_fixture_profile` 信號
  - **AC-3**：non-tabular → reject + shadow_flow_hook
  - **AC-4**：`--use-v2` opt-in；默認 demo CLI 仍 v1
  - **AC-5**：v1 fallback 正常工作
  - **AC-6**：`python -m unittest tests.test_intake_decision_rules_v2 -v` 全綠
  - **AC-7**：v1 unittest 未破壞

---

## STATE

- overall_status: accepted_with_gaps
- current_owner: orchestrator
- next_action: closed — 後續追蹤：non-Tabular shadow pipeline 實作（W9-T2/T4 等）、demo CLI `--use-v2` 預設升格（另票）、shadow hook metadata 消費（見 C_REPORT gaps）
- last_updated: 2026-06-15 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

- changed_files:
  - `docs/intake-decision-rules-v2.md`（新增 · A/B/C/D profile tiers · reject table · shadow hook 契約）
  - `routing/intake_decision_rules_v2.py`（新增 · `evaluate_intake_decision_v2(task_type, case_dir, *, use_v1_fallback=True)`）
  - `scripts/run_agent_intake_decision_demo.py`（`--use-v2` opt-in · 預設仍 v1）
  - `tests/test_intake_decision_rules_v2.py`（新增 · 15 cases）
  - `04_Workflows/tickets/W8-T2-decision-rules-v2-profile-and-reject-reduction_state.md`（本檔 · B_REPORT 完稿）
- skeleton: 無
- placeholder:
  - non-Tabular shadow flow：v2 僅 `shadow_flow_hook` metadata（`routing/intake_decision_rules_v2.py`）；實際 shadow 管線留 W8-T4／W8-T5
- verification:
  - command: `python -m unittest tests.test_intake_decision_rules_v2 tests.test_intake_decision_rules_v1 tests.test_agent_intake_decision_demo -v`
  - exit: 0 · **29 tests OK**（v2: 15 · v1: 8 · demo: 6）
  - AC-1: `test_demo_phase_tier_a_needs_review_consistent_with_v1` · `test_sampleco_tier_b_needs_review_consistent_with_v1` — A/B → needs_review 與 v1 一致
  - AC-2: `test_additional_demo_tier_c_needs_review_not_reject` · `test_sandbox_client_tier_d_needs_review_not_reject` — C/D → needs_review + `experimental_fixture_profile`
  - AC-3: `test_non_tabular_family_reject_with_shadow_hook` — non-tabular → reject + `shadow_flow_hook`
  - AC-4: `scripts/run_agent_intake_decision_demo.py` 含 `--use-v2`（`action=store_true`）；demo 預設 `use_v2=False` · `test_non_tabular_reject_high` 等 v1 路徑未變
  - AC-5: `test_v1_fallback_on_internal_error` · `test_v1_fallback_disabled_raises` — fallback 正常
  - AC-6: v2 suite 全綠（15/15）
  - AC-7: v1 + demo suite 全綠（14/14）· v1 行為未破壞
  - spot-check: `routing/intake_decision_rules_v2.py` 匯出 `evaluate_intake_decision_v2` · non-tabular 分支含 `shadow_flow_hook` · C/D tier 含 `experimental_fixture_profile`
- blockers: 無
- deferred_items:
  - `04_Workflows/WORKFLOW_INDEX.md` v2 條目 — Orchestrator Step 5（本輪 implementer 未改）
  - `docs/WAVE_PROGRESS_DASHBOARD.md` Wave 8 W8-T2 行 — Orchestrator Step 5（本輪 implementer 未改）
  - non-Tabular shadow flow 實作 — metadata hook only；W8-T4 blueprint / W8-T5 後續票
  - demo CLI `--use-v2` 升格為預設 — 需另票；orchestrator 預設 decision 路徑仍 v1（FRAME NonScope）
- next_steps: Reviewer 審查 AC-1–AC-7；Orchestrator Step 5 補 WORKFLOW_INDEX／WAVE_PROGRESS_DASHBOARD

---

## C_REPORT

- conclusion: **accepted_with_gaps**
- blocking_issues: 無
- checks_summary:
  - **AC-1 ✅**: A/B tier → needs_review 與 v1 一致（2 tests）
  - **AC-2 ✅**: C/D → needs_review + `experimental_fixture_profile`（2 tests）
  - **AC-3 ✅**: non-tabular → reject + `shadow_flow_hook`（1 test）
  - **AC-4 ✅**: `--use-v2` opt-in；demo 預設 v1（6 demo tests）
  - **AC-5 ✅**: v1 fallback 正常（2 tests）
  - **AC-6 ✅**: v2 suite 15/15
  - **AC-7 ✅**: v1 + demo 14/14 未破壞
  - **Reviewer 複驗 2026-06-15**: 29 tests OK in ~0.6s
- risk_level: low
- suggestions: shadow flow 僅 metadata hook；`--use-v2` 預設升格需另票

---

## D_REPORT

- docs_updates: `docs/intake-decision-rules-v2.md` 已交付；WORKFLOW_INDEX / Dashboard 註解留 Step 5
- progress_entry: W8-T2 implementer done → **accepted_with_gaps** — v2 rules + C/D profile + shadow hook + 29 tests OK · v1 未改
- followup_suggestions: W9-T2 non-tabular decision 擴展 · demo CLI v2 預設升格票

---

## O_NOTES

| date | role | action |
|------|------|--------|
| 2026-06-15 | scribe | W8-T2 Reviewer→Scribe 收口 · accepted_with_gaps |
| 2026-06-15 | orchestrator | STATE 關票 · overall_status accepted_with_gaps · Dashboard/Progress 收口 |
