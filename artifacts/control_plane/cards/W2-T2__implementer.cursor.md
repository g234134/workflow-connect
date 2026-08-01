# Cursor Instruction Card · W2-T2 · implementer

## Provenance
- **source_path**: 04_Workflows/tickets/W2-T2_state.md
- **generated_at**: 2026-06-07T07:36:46.215084+00:00
- **plan_snapshot**: artifacts/control_plane/dispatch_plan.latest.json

## Role
implementer

## Ticket
- **ID**: W2-T2
- **Title**: Multi-Chat Ticket B→C→D→O 參照票（可重跑契約）
- **State file**: `04_Workflows/tickets/W2-T2_state.md`
- **Bucket**: draft
- **Reason**: draft ticket assigned to implementer

## Must Read (before any edit)
1. `04_Workflows/tickets/W2-T2_state.md`（FRAME + STATE + 允許區 REPORT）
2. `.cursor/rules/multi_chat_roles.mdc` §Implementer
3. `AGENTS.md` §初始化校準（接戰時）

## AllowedPaths
- `04_Workflows/tickets/W2-REF-001_state.md`
- `docs/testing.md`
- `04_Workflows/tickets/README.md`

## BlockedPaths
- `core/*`
- `skills/*`
- `tests/*`
- `AGENTS.md`

## Suggested Commands
- `Open Implementer chat; read 04_Workflows/tickets/W2-T2_state.md; execute next_action`
- `檢查 W2-REF-001_state.md 四 REPORT 完整`

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
