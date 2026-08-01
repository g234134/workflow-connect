# Cursor Instruction Card · W-next-DISPATCH-CARDS-MVP · implementer

## Provenance
- **source_path**: 04_Workflows/tickets/W-next-DISPATCH-CARDS-MVP_state.md
- **generated_at**: 2026-06-07T07:36:46.215084+00:00
- **plan_snapshot**: artifacts/control_plane/dispatch_plan.latest.json

## Role
implementer

## Ticket
- **ID**: W-next-DISPATCH-CARDS-MVP
- **Title**: Control Plane 指令卡自動化（Cursor *.cursor.md）
- **State file**: `04_Workflows/tickets/W-next-DISPATCH-CARDS-MVP_state.md`
- **Bucket**: draft
- **Reason**: draft ticket assigned to implementer

## Must Read (before any edit)
1. `04_Workflows/tickets/W-next-DISPATCH-CARDS-MVP_state.md`（FRAME + STATE + 允許區 REPORT）
2. `.cursor/rules/multi_chat_roles.mdc` §Implementer
3. `AGENTS.md` §初始化校準（接戰時）

## AllowedPaths
- ``04_Workflows/_dispatch_cards.py`（新增）`
- ``Scripts/run_dispatch_cards.py`（新增）`
- ``tests/test_dispatch_cards.py`（新增）`
- ``tests/fixtures/dispatch/`（可增 card 相關 fixture）`
- ``artifacts/control_plane/cards/`（生成物目錄；可 `.gitignore` 或 commit 樣本擇一，Implementer 在 B_REPORT 說明）`
- `docs/control_plane_dispatch_executor.md`

## BlockedPaths
- `core/**`
- `AGENTS.md`、`ENGINEERING_CONTRACT.md`、`HARNESS_CONSTITUTION.md`
- ``.cursor/rules/**`（除非尚書省另開制度票）`
- `.github/workflows/**`
- ``04_Workflows/tickets/*_state.md`（**只讀**；生成器不得寫入）`

## Suggested Commands
- `Open Implementer chat; read 04_Workflows/tickets/W-next-DISPATCH-CARDS-MVP_state.md; execute next_action`
- `python Scripts/run_dispatch_executor.py --json-out artifacts/control_plane/dispatch_plan.latest.json --md-out artifacts/control_plane/dispatch_plan.latest.md`

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
