# P75-REGRESSION — Gate + Checkpoint A + Notify E2E v1

| Field | Value |
|-------|-------|
| **Status** | `implemented` |
| **Owner** | Implementer |
| **Depends** | P75-G2, P75-G3, P75-G4, W6-T5 |

## Goal

Regression guard for three-state gate + CP-A + `intake.gate_decision` wired behavior.

## changed_files

### Added

- `tests/test_intake_gate_checkpointA_notify_e2e_v1.py`
- `docs/phase-7.5-gate-checkpointA-notify-e2e-v1.md`

### Modified

- `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md` — §7.3 regression row
- `04_Workflows/WORKFLOW_INDEX.md` — doc entry

## Non-scope (honored)

- No changes to gate contract / schema
- No CP-A schema / trigger function changes
- No notification gateway emit schema changes

## verification

```bash
python -m unittest tests.test_intake_gate_checkpointA_notify_e2e_v1.py -v
```

## Scenarios

| # | Gate decision | case_ref | CP-A | Notify |
|---|---------------|----------|------|--------|
| 1 | `accept` | `demo_phase` (`tabular.intake.new_case`) | skipped | `intake.gate_decision` |
| 2 | `review_needed` | `demo_phase` (`tabular.cleaning.mvp`) | awaiting_human | `intake.gate_decision` |
| 3 | `reject` | synthetic PHI case | not_applicable (S3 early-exit) | `intake.gate_decision` + `policy_deny_phi` |
