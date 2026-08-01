# TICKET STATE · TEST-DEP · Unresolved dependency sample

## FRAME

- Title: In-progress ticket with unresolved dependency
- AllowedPaths:
  - `tests/fixtures/dispatch/**`
  - `04_Workflows/_dispatch_cards.py`
- BlockedPaths:
  - `core/**`
  - `AGENTS.md`
- Dependencies:
  - W9-T9 missing prerequisite
- VerificationCommands:
  - `python -m unittest tests.test_dispatch_cards -v`
    - 預期：全綠

## STATE

- overall_status: in_progress
- implementation_status: pending
- current_owner: implementer
- next_action: Implement after W9-T9 closes
- status_by_role:
  - orchestrator: done
  - implementer: in_progress
  - reviewer: pending
  - scribe: pending

## B_REPORT

- changed_files: 无
