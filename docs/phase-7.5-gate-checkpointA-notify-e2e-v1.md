# Phase 7.5 — Gate + Checkpoint A + Notify E2E Behavior Samples (v1)

> **Ticket**: P75-REGRESSION-gate-checkpointA-notify-e2e-v1  
> **Regression test**: `tests/test_intake_gate_checkpointA_notify_e2e_v1.py`  
> **Related**: `docs/intake-gate-contract-v1.md` · `docs/intake-gate-policy-v1.md` · `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md` §7.2

## Purpose

Three frozen **behavior samples** for the Intake Gate three-state vocabulary, Checkpoint A trigger rules, and `intake.gate_decision` notification payload. Future changes to gate layer, policy YAML, or notification gateway should keep these scenarios green.

## Wiring under test

Each sample runs the same integration path:

1. `evaluate_intake_gate(..., mode="run")` — durable outbox record  
2. `emit_intake_gate_decision_notification(...)` — best-effort `intake.gate_decision` (G4 CLI hook)  
3. `decision_result_from_gate()` → `maybe_create_checkpoint_a()` — CP-A integration (W6-T5)

Notification verification uses `load_workflow_events()` (same read model as `scripts/inspect_workflow_events.py`).

## Scenario 1 — `accept` (low risk, no CP-A)

| Field | Value |
|-------|-------|
| `task_type` | `tabular.intake.new_case` |
| `case_dir` / `case_ref` | `cases/demo_phase` / `demo_phase` |
| Gate `decision` | `accept` |
| `risk_level` | `low` |
| CP-A | **Skipped** — `status=skipped`; no `checkpoint_*.json` |
| `intake.gate_decision` | **Present** when notifications enabled (run mode + outbox record) |
| Key `reason_codes` | `allowlist_fixture`, `supported_task` |

## Scenario 2 — `review_needed` (CP-A pause)

| Field | Value |
|-------|-------|
| `task_type` | `tabular.cleaning.mvp` |
| `case_dir` / `case_ref` | `cases/demo_phase` / `demo_phase` |
| Gate `decision` | `review_needed` |
| `risk_level` | `medium` |
| CP-A | **Triggered** — `status=awaiting_human`; checkpoint file under `outbox/<case_ref>/` |
| Checkpoint payload | `agent_output.intake_gate.decision=review_needed` + matching `intake_decision_id` |
| `intake.gate_decision` | **Present**; `status_summary.decision=review_needed` |
| Key `reason_codes` | `manual_review_required`, `allowlist_fixture` |

## Scenario 3 — `reject` (policy deny, no CP-A)

| Field | Value |
|-------|-------|
| `task_type` | `tabular.intake.new_case` |
| `case_dir` / `case_ref` | Synthetic PHI case under temp `cases/` (v2 would `auto_accept`; policy denies) |
| Gate `decision` | `reject` |
| CP-A | **Not applicable** — orchestrator S3 early-exit; no checkpoint file |
| `intake.gate_decision` | **Present**; payload includes deny `reason_codes` |
| Required deny code | `policy_deny_phi` (from `POLICY-DENY-PHI`) |

## Verification

```bash
python -m unittest tests.test_intake_gate_checkpointA_notify_e2e_v1.py -v
```

Optional CLI smoke (gate-only, same notify event):

```bash
python scripts/run_intake_gate_cli.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode run --enable-notifications --format json \
  --outbox-root <tmp>/outbox

python scripts/inspect_workflow_events.py \
  --case-ref demo_phase \
  --event-type intake.gate_decision \
  --format json \
  --outbox-root <tmp>/outbox
```

## Non-goals (this regression)

- Does not assert orchestrator S3 notify hook (G4 scoped to gate CLI + direct emit helper).  
- Does not change gate contract schema, CP-A trigger functions, or notification envelope schema.
