# TICKET STATE · DEMO-ELIG · Demo Eligibility Ticket

> handoff 摘要檔；跨 chat 交棒以本檔為準
> Phase：Wave C · Control Plane · Test Fixture

---

## FRAME

- Goal: 測試 skill distillation 的 pattern 識別
- Scope: 包含 verification 與 changed_files 的完整 B_REPORT
- AllowedPaths:
  - `scripts/distill_control_plane_skills_lite.py`
  - `tests/fixtures/skill_distillation/reports/**`
- AcceptanceCriteria:
  - AC1: B_REPORT 包含 verification 區塊
  - AC2: B_REPORT 包含 changed_files 區塊

---

## B_REPORT

- changed_files:
  - `tests/fixtures/skill_distillation/reports/DEMO-ELIG_state.md`
  - `scripts/distill_control_plane_skills_lite.py`
- artifacts:
  - pattern fixture for testing
- verification:
  - `python -m unittest tests.test_distill_control_plane_skills_lite -v`
  - `python scripts/distill_control_plane_skills_lite.py --reports-dir tests/fixtures/skill_distillation/reports --pretty`
- behavior_notes: 此檔案作為 pattern（有 verification + changed_files）
- deferred_items: 無

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無
- checks_summary: AC1 ✓ AC2 ✓
- risk_level: low
- suggestions: 無
