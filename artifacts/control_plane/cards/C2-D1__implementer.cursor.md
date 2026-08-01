# Cursor Instruction Card · C2-D1 · implementer

## Provenance
- **source_path**: 04_Workflows/tickets/C2-D1_state.md
- **generated_at**: 2026-06-07T07:36:46.215084+00:00
- **plan_snapshot**: artifacts/control_plane/dispatch_plan.latest.json

## Role
implementer

## Ticket
- **ID**: C2-D1
- **Title**: C2-D1
- **State file**: `04_Workflows/tickets/C2-D1_state.md`
- **Bucket**: runnable_now
- **Reason**: in_progress with implement/resume/wire/test next_action

## Must Read (before any edit)
1. `04_Workflows/tickets/C2-D1_state.md`（FRAME + STATE + 允許區 REPORT）
2. `.cursor/rules/multi_chat_roles.mdc` §Implementer
3. `AGENTS.md` §初始化校準（接戰時）

## AllowedPaths
- `cases/demo_phase/*`
- `notebooks/csv_cleaning/*`
- `docs/C2-D1_DEMO_WALKTHROUGH.md`
- ``docs/CASE_REPORTS/*`（C2-D1 相關）`
- ``04_Workflows/tickets/C2-D1_state.md`（B_REPORT 區塊）`

## BlockedPaths
- `core/*`、`skills/*`、`config/*`、`tests/*`
- `AGENTS.md`、`.cursor/rules/*`、`.github/workflows/*`
- `04_Workflows/00_Agent_Work_Progress.md`
- `其他 ticket state 檔`
- ``docs/PRODUCT_TABULAR_CLEANING.md`（C2-P1 主體）`

## Suggested Commands
- `Open Implementer chat; read 04_Workflows/tickets/C2-D1_state.md; execute next_action`

## Expected Output (implementer)
<!-- Implementer: update B_REPORT only -->
- changed_files:
- artifacts:
- verification:
- behavior_notes:
- deferred_items:

## Handoff
- 完成後更新 ticket STATE 的指定區塊；**勿改 FRAME**
- 若 plan 與 ticket FRAME 衝突，**以 ticket state FRAME 為權威**（AllowedPaths／BlockedPaths）
- plan 僅負責排序與建議，不得覆寫 FRAME 邊界
- Plan expected_output hint: B_REPORT updated; STATE overall_status in_progress
