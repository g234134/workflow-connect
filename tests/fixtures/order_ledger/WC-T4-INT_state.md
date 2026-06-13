# TICKET STATE · WC-T4-INT · Order ledger integration sample

> handoff 摘要檔；跨 chat 交棒以本檔為準。  
> Wave：Wave C · Control Plane · WC-T4 integration fixture

---

## FRAME

- Title: WC-T4 order ledger integration fixture
- Goal: Exercise real ticket state → order intake path (ready gate + JSONL ledger).
- Scope:
  - Integration test only; not a production ticket
- NonScope:
  - Payment / outbox / REST
- VerificationCommands:
  - `python -m unittest tests.test_order_ledger_integration -v`

---

## STATE

- overall_status: in_progress
- implementation_status: done
- current_owner: orchestrator
- next_action: ready_for_order — create commercial order intake record for WC-T4-INT
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

- changed_files:
  - `tests/fixtures/order_ledger/WC-T4-INT_state.md`
