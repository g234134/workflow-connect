# TICKET STATE · TEST-REV · In review sample

## FRAME

- Title: Review gate ticket
- VerificationCommands:
  - `python -m unittest tests.test_sample -v`
    - 預期：全綠

## STATE

- overall_status: in_progress
- implementation_status: in_review
- current_owner: reviewer
- next_action: Reviewer 第二輪驗收 — 對照 AcceptanceCriteria
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: in_progress
  - scribe: pending

## B_REPORT

- changed_files:
  - `docs/sample.md`
