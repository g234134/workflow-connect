# Cursor Instruction Card · DEMO-ELIG · implementer

## Provenance

- **source_path**: tests/fixtures/skill_distillation/cards/one_card.cursor.md
- **generated_at**: 2026-06-13T08:00:00Z
- **plan_snapshot**: wc-t6-fixture-plan
- **eligibility_warning**: dependency WC-T1 pending on demo ticket

## Role

implementer

## Ticket

- **ID**: DEMO-ELIG
- **Title**: Skill distillation fixture — eligibility + verification
- **State file**: `04_Workflows/tickets/DEMO-ELIG_state.md`

## Allowed paths (from FRAME)

- `scripts/distill_control_plane_skills_lite.py`
- `tests/fixtures/skill_distillation/**`

## VerificationCommands

- `python -m unittest tests.test_distill_control_plane_skills_lite -v`
  - 预期：全绿

## Instructions

1. Run distillation CLI against fixtures only.
2. Do not touch `core/**` or production ticket state files.
