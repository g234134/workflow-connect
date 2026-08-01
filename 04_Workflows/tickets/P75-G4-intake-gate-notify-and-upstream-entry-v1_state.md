# P75-G4 — Intake Gate notify + upstream entry

| Field | Value |
|-------|-------|
| **Status** | `implemented` |
| **Owner** | Implementer |
| **Depends** | P75-G2 (outbox record path), P75-G3 (policy_version on result) |

## changed_files

### Added

- `tests/test_intake_gate_notify_v1.py`

### Modified

- `delivery/notification_gateway_v1.py` — `intake.gate_decision` event builder + `emit_intake_gate_decision_notification()`
- `scripts/run_intake_gate_cli.py` — `--enable-notifications`, `--outbox-root`, post-run notify hook
- `docs/outbox-and-feedback-layer-contract-v1.md` — workflow notification enum + G4 emit rules
- `docs/audit-quickview-and-case-history-spec-v1.md` — S3 gate record + `intake.gate_decision` in workflow_notifications
- `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md` — §7.2 G4 rows
- `04_Workflows/onboarding/standard-case-hitl-resume-notify_guide.md` — §2.4 upstream CLI + payload example
- `tests/test_notification_gateway_v1.py` — payload shape case

## Delivered

- Event type `intake.gate_decision` with required payload fields in `artifacts` + `status_summary`
- Gate CLI emits after run-mode outbox write when notifications enabled (env or flag)
- Fail-open: notify failure does not change gate `ok`
- Documented upstream entry: `scripts/run_intake_gate_cli.py` (preview / run + notify)

## Non-scope (honored)

- No changes to `routing/intake_gate_layer_v1.py` core decision logic
- No CP-A schema / trigger changes
- No orchestrator S3 notify hook (CLI entry only this ticket)

## verification

```bash
python -m unittest tests.test_intake_gate_notify_v1 tests.test_notification_gateway_v1.TestBuildNotificationEvent -v

python scripts/run_intake_gate_cli.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode run --enable-notifications --format json \
  --outbox-root <tmp>/outbox
```

## AC mapping

| AC | Evidence |
|----|----------|
| AC-1 | Three-state gate run + notify → `intake.gate_decision` in jsonl (`test_gate_run_mode_emits_*`) |
| AC-2 | Payload includes record path, decision, reason_codes, intake_decision_id, policy_version |
| AC-3 | Notify failure → gate still `ok=true` (`test_notify_failure_does_not_break_gate_result`) |
| AC-4 | `run_intake_gate_cli.py` documented in onboarding + matrix |
| AC-5 | Gateway unittest extended (`test_intake_gate_decision_event_payload_fields`) |
