# Cursor Instruction Card · W2-T3 · implementer

## Provenance
- **source_path**: 04_Workflows/tickets/W2-T3_state.md
- **generated_at**: 2026-06-07T07:36:46.215084+00:00
- **plan_snapshot**: artifacts/control_plane/dispatch_plan.latest.json

## Role
implementer

## Ticket
- **ID**: W2-T3
- **Title**: Cursor Subagents Dispatch 回歸包（TEST-SUB 系列擴充）
- **State file**: `04_Workflows/tickets/W2-T3_state.md`
- **Bucket**: draft
- **Reason**: draft ticket assigned to implementer

## Must Read (before any edit)
1. `04_Workflows/tickets/W2-T3_state.md`（FRAME + STATE + 允許區 REPORT）
2. `.cursor/rules/multi_chat_roles.mdc` §Implementer
3. `AGENTS.md` §初始化校準（接戰時）

## AllowedPaths
- `tests/test_dispatch_guide_scenarios.py`
- `04_Workflows/_dispatch_regression.py`
- `.cursor/agents/DISPATCH_GUIDE.md`

## BlockedPaths
- `AGENTS.md`
- `.cursor/agents/*.md（除 DISPATCH_GUIDE 小節）`
- `core/*`

## Suggested Commands
- `Open Implementer chat; read 04_Workflows/tickets/W2-T3_state.md; execute next_action`
- `python -m unittest tests.test_dispatch_guide_scenarios -v`

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
