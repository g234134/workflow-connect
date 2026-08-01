# Cursor Instruction Card · W1-T4 · implementer

## Provenance
- **source_path**: 04_Workflows/tickets/W1-T4_state.md
- **generated_at**: 2026-06-07T07:36:46.215084+00:00
- **plan_snapshot**: artifacts/control_plane/dispatch_plan.latest.json

## Role
implementer

## Ticket
- **ID**: W1-T4
- **Title**: KB Index Selector Gate 最小 Prod 接線（dev-only）
- **State file**: `04_Workflows/tickets/W1-T4_state.md`
- **Bucket**: draft
- **Reason**: draft ticket assigned to implementer

## Must Read (before any edit)
1. `04_Workflows/tickets/W1-T4_state.md`（FRAME + STATE + 允許區 REPORT）
2. `.cursor/rules/multi_chat_roles.mdc` §Implementer
3. `AGENTS.md` §初始化校準（接戰時）

## AllowedPaths
- `core/kb_index_selector_hook.py`
- `core/ask_rag_selector.py（接線點）`
- `skills/gov_cards/kb_index_selector_gate.json`
- `docs/KB_INDEX_SELECTOR_DEV_RUNBOOK.md`
- `tests/test_kb_index_selector_hook.py`

## BlockedPaths
- `AGENTS.md`
- `.cursor/rules/*`
- `04_Workflows/00_Agent_Work_Progress.md`

## Suggested Commands
- `Open Implementer chat; read 04_Workflows/tickets/W1-T4_state.md; execute next_action`
- `python -m unittest tests.test_kb_index_selector_hook -v`

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
