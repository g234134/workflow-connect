# TICKET STATE · W10-T3 · orchestrator-registry-fail-closed-wiring-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準。  
> Wave：Wave 10 · Agent Lines / Skill Registry 整合  
> 承接 W10-T2 selector fail-closed 訊號，在 experiment orchestrator 層阻斷清洗 run path。

---

## FRAME

- **Title**: W10-T3 · orchestrator-registry-fail-closed-wiring-v1
- **Goal**: 讓 `error.registry_fail_closed` / `error.registry_not_approved`（或 `selector_view.ok=false`）在 S6 後 fail-close orchestrator，不進 S7–S10、不寫 CP-A/B。
- **AllowedPaths**: `scripts/run_agent_standard_case_experiment.py` · `tests/test_agent_standard_case_experiment.py` · 本票 state

---

## STATE

- **overall_status**: `implementer_done_pending_review`
- **current_owner**: `reviewer`
- **last_updated**: 2026-06-16 · implementer

---

## B_REPORT

- **changed_files**:
  - `scripts/run_agent_standard_case_experiment.py` — `_should_fail_close_due_to_registry` + S6 後 early return
  - `tests/test_agent_standard_case_experiment.py` — 3 tests（fail-closed run、not_approved preview、ok 回歸）
- **behavior_notes**:
  - S6 tool path 完成後讀 `selector_view`；若 `selector_rule_id` 為 `error.registry_fail_closed` 或 `error.registry_not_approved` → `final_status=blocked_at_selector_registry`
  - 跳過 S4 checkpoint A、S7–S10 run path；`checkpoint_a/b_status=not_applicable`；不寫 outbox checkpoint 檔
  - ok 路徑行為不變
- **verification**:
  - `python -m unittest tests.test_agent_standard_case_experiment -v` → **32 tests OK**

---

## O_NOTES

| date | role | action |
|------|------|--------|
| 2026-06-16 | implementer | registry fail-closed wiring 完成：orchestrator S6 fail-close + 3 unittest |
