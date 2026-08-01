# Standard-Case HITL / Resume / Notify — Test Matrix

> **Scope**: Agent standard-case experiment line (`scripts/run_agent_standard_case_experiment.py`), HITL checkpoint integration (W6-T5/T6), resume loop (W6-T11), notification gateway (W6-T10), delivery approval CLI (W8-T3).  
> **Authoritative behavior**: orchestrator + `hitl/*` + `delivery/notification_gateway_v1.py` + closure report `04_Workflows/reports/W6-standard-case-v2-closure-report.md`.  
> **CLI template** (orchestrator):

```bash
python scripts/run_agent_standard_case_experiment.py \
  --task-type <task_type> \
  --case-dir <case_dir> \
  --mode {preview|run} \
  [--auto-approve-intake] \
  [--auto-approve-delivery] \
  [--sandbox-end-to-end] \
  [--resume-checkpoint <path>] \
  [--enable-notifications] \
  [--outbox-root <path>] \
  --format json
```

> **Notification enablement**: `--enable-notifications` **or** env `GOV_NOTIFICATION_GATEWAY_ENABLED=1`. Emits **only** when `mode=run` and gateway enabled. Preview always suppresses orchestrator notifications.

---

## 1. Primary dimensions

| Dimension | Values used in matrix |
|-----------|----------------------|
| **Checkpoint** | A (`A-intake-confirmation`), B (`B-delivery-confirmation`) |
| **Checkpoint status** (on-disk / orchestrator) | `awaiting_human` / `written` / `would_pause` / `approved` / `auto_approved` / `rejected` / `revise_needed` / `on_hold` / `skipped` / `stopped_before_delivery` |
| **Mode** | `preview`, `run` |
| **Delivery** | N/A (pre-delivery), first delivery (B resume → S13), duplicate delivery (second B resume), stale artifacts (missing eligibility/cleaned) |
| **Notification** | disabled (default), enabled, dry_run (gateway unit), sink failure (mock), human vs auto approval source |
| **Resume** | none (forward flow), `--resume-checkpoint` after human decision |

### Orchestrator `final_status` vocabulary (matrix-relevant)

| Value | Typical trigger |
|-------|-----------------|
| `preview_ready` | Preview, no HITL pause |
| `waiting_for_human` | Checkpoint A/B pause (preview or run) |
| `resume_plan_ready` | Run stopped before tool execution (edge) |
| `stopped_at_checkpoint_b` | Run profile `stop_at=checkpoint_b` |
| `stopped_at_cleaning_preview` | Run profile `stop_at=cleaning_preview` |
| `run_complete` | Run finished including delivery export |
| `sandbox_e2e_complete` | Sandbox bundle path OK |
| `sandbox_e2e_blocked_at_checkpoint_b` | Sandbox E2E blocked at CP-B |
| `blocked` | Fail-close (decision reject, resume invalid, stale artifacts, etc.) |
| `checkpoint_mismatch` | Resume cross-check failure (`case_ref` / `task_type`) |
| `duplicate_delivery` | Second B resume with existing outbox marker |
| `stale_checkpoint` | Resume while `status=awaiting_human` and `expires_at` passed |

### Notification `event_type` vocabulary (orchestrator + CLI)

| event_type | When emitted (run + enabled) |
|------------|------------------------------|
| `checkpoint.awaiting_human` | CP-A `status=written` or CP-B `status=written` |
| `checkpoint.approved` | CP-A `auto_approved`; CP-B `skipped`/`auto_approved`; human via delivery CLI |
| `delivery.bundle_ready` | Sandbox bundle success |
| `run.completed` | Run ends `ok=true` with non-block terminal status |
| `run.blocked` | Run ends `ok=false` or terminal blocked status |

**Intake Gate CLI** (`scripts/run_intake_gate_cli.py`): when `mode=run` and `--enable-notifications` (or env), emits **`intake.gate_decision`** — independent of orchestrator checkpoint events.

**Not emitted in v1**: `checkpoint.rejected`, `checkpoint.changes_requested`, `run.failed` (use `run.blocked`).

---

## 2. Forward flow — Checkpoint A (intake)

| ID | CP status (result) | Mode | Auto intake | Input | Expected `final_status` | Notification (enabled, run) | Unit test(s) |
|----|-------------------|------|-------------|-------|-------------------------|------------------------------|--------------|
| A-F1 | `would_pause` | preview | no | `--task-type tabular.cleaning.mvp --case-dir cases/demo_phase --mode preview` | `waiting_for_human` | **No** (preview gate) | `test_demo_phase_preview_produces_decision_route_checkpoint_a` |
| A-F2 | `would_pause` | preview | no | `--case-dir cases/sampleco/2026-0001 --mode preview` | `waiting_for_human` | **No** | `test_sampleco_preview_checkpoint_a_needs_human_review` |
| A-F3 | — (no write) | preview | no | preview + `--outbox-root <tmp>` | `waiting_for_human`; **no** checkpoint file | **No** | `test_preview_does_not_write_checkpoint_state_by_default` |
| A-F4 | `written` | run | no | demo_phase run, no auto intake, external outbox | `waiting_for_human` | **Yes**: `checkpoint.awaiting_human` (A), `run.completed` | `test_run_mode_writes_checkpoint_a_when_needed` |
| A-F5 | `auto_approved` | run | yes | demo_phase `--auto-approve-intake` | `run_complete` / `waiting_for_human` / `resume_plan_ready` (profile-dependent) | **Yes**: `checkpoint.approved` (`approval_source=auto`), `run.completed` | `test_run_mode_auto_approve_intake_resume_plan`, `test_run_mode_auto_approve_intake_resume_plan_via_integration_layer` |
| A-F6 | no file | run | yes | auto intake; list outbox | no checkpoint JSON | (same as A-F5 notify) | `test_auto_approve_intake_does_not_write_checkpoint_a_file` |
| A-F7 | — | preview | — | `--task-type gov.observability.eval --case-dir cases/demo_phase` (reject decision) | `blocked` | **No** | `test_non_tabular_blocked` |
| A-F8 | integration SSOT | preview | no | demo_phase preview | `waiting_for_human`; `integration_layer=hitl.checkpoint_a_integration_v1` | **No** | `test_checkpoint_a_uses_w6_t5_integration_layer` |

---

## 3. Forward flow — Checkpoint B (delivery gate)

| ID | CP status (result) | Mode | Case / flags | Input | Expected `final_status` | Notification (enabled, run) | Unit test(s) |
|----|-------------------|------|--------------|-------|-------------------------|------------------------------|--------------|
| B-F1 | `planned`, `would_trigger=true` | preview | sampleco | preview, warning guard implied | `waiting_for_human` | **No** | `test_checkpoint_b_preview_has_integration_layer_field` |
| B-F2 | `written` / `stopped_before_delivery` | run | sampleco | run + auto intake; profile `stop_at=checkpoint_b` | `stopped_at_checkpoint_b` | **Yes**: `checkpoint.awaiting_human` (B), `run.completed` | `test_sampleco_run_mode_stops_at_checkpoint_b`, `test_sampleco_run_writes_checkpoint_b_via_w6_t6_integration` |
| B-F3 | `stopped_before_delivery` | run | additional_demo | run, no sandbox e2e | `stopped_at_checkpoint_b` | **Yes**: `run.completed` (CP-B stopped, may not write file) | `test_run_mode_checkpoint_b_stops_without_auto_approve_delivery`, `test_additional_demo_run_mode_stops_at_checkpoint_b` |
| B-F4 | delivery executed | run | demo_phase | run + auto intake; profile `stop_at=bundle` | `run_complete` (CP-B skipped) | **Yes**: `checkpoint.approved` (B auto/skip), `run.completed` | `test_demo_phase_run_mode_executes_to_bundle` |
| B-F5 | `skipped` | run | additional_demo | `--sandbox-end-to-end` + ok guard | `sandbox_e2e_complete` | **Yes**: `delivery.bundle_ready`, `run.completed` | `test_sandbox_e2e_checkpoint_b_skipped_ok_path_completes_bundle`, `test_additional_demo_sandbox_end_to_end_produces_bundle` |
| B-F6 | `written` | run | additional_demo | sandbox e2e + mocked `output_guard.status=warning` | `sandbox_e2e_blocked_at_checkpoint_b` | **Yes**: `checkpoint.awaiting_human` (B), `run.completed` | `test_sandbox_e2e_warning_writes_checkpoint_b_and_blocks_bundle` |
| B-F7 | integration contract | run | additional_demo | sandbox e2e ok | `sandbox_e2e_complete` | (same as B-F5) | `test_sandbox_e2e_checkpoint_b_status_integration_layer_structure` |
| B-F8 | `awaiting_human` (file) | unit | demo_phase fixture | `maybe_create_checkpoint_b` + warning guard | N/A (integration dict) | N/A | `test_warning_creates_checkpoint_b` |
| B-F9 | skipped file | unit | demo_phase | `maybe_create_checkpoint_b` + ok guard + `auto_approve=True` | N/A | N/A | `test_ok_auto_approve_skips_checkpoint` |

---

## 4. Resume loop (`--resume-checkpoint`)

> Preconditions: checkpoint JSON on disk; human decision applied via `run_hitl_checkpoint_cli --apply-decision` (or test helper `_apply_human_decision_to_checkpoint_file`). Resume requires **`--mode run`**.

| ID | CP | On-disk status | Human action | Mode | Delivery | Input / precondition | Expected `final_status` | Notification | Unit test(s) |
|----|-----|----------------|--------------|------|----------|----------------------|-------------------------|--------------|--------------|
| R-1 | A | `approved` | `approve` | run | N/A | demo_phase CP-A approved → resume | `waiting_for_human` / `run_complete` (profile); `resume.resume_from_step=S7` | Not asserted in resume tests (forward notify tests cover gateway) | `test_approved_checkpoint_a_resume_runs_s7_path` |
| R-2 | B | `approved` | `approve_delivery` | run | **first delivery** | sampleco CP-B + warning guard mock → resume | `run_complete`; S13 executed | Not asserted | `test_approved_checkpoint_b_resume_runs_s13_delivery` |
| R-3 | A | `awaiting_human` | (none) | run | N/A | resume before `--apply-decision` | `blocked` | **No** | `test_resume_checkpoint_awaiting_human_blocked` |
| R-4 | A | `approved` | `approve` | preview | N/A | `--mode preview --resume-checkpoint` | `blocked` | **No** | `test_resume_checkpoint_preview_mode_blocked` |
| R-5 | A | `approved` | `approve` | run | mismatch | CP-A `demo_phase`, CLI `--case-dir cases/sampleco/2026-0001` | `checkpoint_mismatch` | **No** | `test_resume_checkpoint_case_ref_mismatch_blocked` |
| R-6 | A | `approved` | `approve` | run | mismatch | CP-A task `tabular.cleaning.mvp`, CLI `--task-type gov.observability.eval` | `checkpoint_mismatch` | **No** | `test_resume_checkpoint_task_type_mismatch_blocked` |
| R-7 | A | `rejected` | `reject` | run | N/A | manually set `status=rejected` | `blocked` | **No** | `test_resume_checkpoint_rejected_status_blocked` |
| R-8 | B | `approved`* | `request_changes`† | run | N/A | status approved but action tampered to `request_changes` | `blocked` | **No** | `test_resume_checkpoint_wrong_human_action_blocked` |
| R-9 | B | `approved` | `approve_delivery` | run | **duplicate** | second resume same CP-B after successful first | `duplicate_delivery` | **No** | `test_resume_checkpoint_duplicate_delivery_blocked` |
| R-10 | B | `approved` | `approve_delivery` | run | **stale artifacts** | tamper `resume_context.artifacts` + hide `cleaned/` | `blocked` (message: stale checkpoint artifacts) | **No** | `test_resume_checkpoint_b_stale_artifacts_blocked` |
| R-11 | A | `awaiting_human` | — | run | **stale checkpoint** | `expires_at` in past, status still `awaiting_human` | `stale_checkpoint` | **No** | — *(no unittest)* |
| R-12 | A | `revise_needed` | `revise_plan` | run | N/A | after human revise | `blocked` | **No** | — *(no orchestrator resume test; integration only)* |
| R-13 | B | `on_hold` | `hold` | run | N/A | after human hold | `blocked` | **No** | — *(no orchestrator resume test; integration/CLI only)* |
| R-14 | — | — | — | run | N/A | invalid / missing checkpoint path | `blocked` | **No** | — *(no dedicated unittest)* |
| R-15 | A | `approved` | `approve` | run | N/A | `case_ref` not in allowlist | `blocked` | **No** | — *(no dedicated unittest)* |

\* Test sets `status=approved` after apply-decision helper.  
† Wrong-action guard: v1 requires `approve` (A) or `approve_delivery` (B).

---

## 5. Human decision layer (HITL core + integration)

| ID | Checkpoint | Human action | Result status / plan | Orchestrator resume? | Unit test(s) |
|----|------------|--------------|----------------------|----------------------|--------------|
| H-1 | A | `approve` | `resume_from=selector`, plan `final_status=approved` | Yes (R-1) | `test_record_human_decision_checkpoint_a_approve`, `test_human_decision_resume_plans` (subTest approve) |
| H-2 | A | `revise_plan` | `resume_from=gate`, plan `final_status=revise_needed` | **No** (v1) | `test_human_decision_resume_plans` (subTest revise_plan), `test_resume_context_revise_plan_uses_gate` |
| H-3 | A | `reject` | plan `final_status=rejected` | **No** (R-7) | `test_human_decision_resume_plans` (subTest reject), `test_resume_plan_from_checkpoint_a_reject` |
| H-4 | B | `approve_delivery` | `resume_from=delivery`, proceed | Yes (R-2) | `test_record_human_decision_checkpoint_b_approve_delivery`, `test_delivery_plan_approve_delivery` |
| H-5 | B | `request_changes` | plan action `request_changes` | **No** | `test_delivery_plan_request_changes_defaults_cleaning`, `test_request_changes_defaults_cleaning` (CLI) |
| H-6 | B | `hold` | `update_case_status=on_hold` | **No** | `test_delivery_plan_hold`, `test_hold_on_hold` (CLI) |
| H-7 | B | `approve` (CLI) | checkpoint updated + optional notify | CLI path | `test_approve_delivery_writes_decision`, `test_notify_experiment_called_on_approve` |

---

## 6. Delivery scenarios (cross-cutting)

| ID | Scenario | Preconditions | Expected outcome | Notification | Unit test(s) |
|----|----------|---------------|------------------|--------------|--------------|
| D-1 | **First delivery** | CP-B approved; artifacts present; no resume marker | S13 runs; `final_status=run_complete`; marker written | Not asserted in resume test | `test_approved_checkpoint_b_resume_runs_s13_delivery` |
| D-2 | **Duplicate delivery** | Same CP-B resumed twice | Second: `duplicate_delivery`, `ok=false` | **No** | `test_resume_checkpoint_duplicate_delivery_blocked` |
| D-3 | **Stale artifacts** | Missing `eligibility_report` / `cleaned_csv` | `blocked`, stale message | **No** | `test_resume_checkpoint_b_stale_artifacts_blocked` |
| D-4 | **Stopped before delivery** | Run profile stops at CP-B | No `export.delivery_bundle` in first pass | `checkpoint.awaiting_human` if file written | `test_sampleco_run_mode_stops_at_checkpoint_b`, `test_run_mode_checkpoint_b_stops_without_auto_approve_delivery` |
| D-5 | **Sandbox bundle (non-production)** | sandbox e2e ok | Bundle under outbox; `notify_triggered=false` on sandbox_delivery | `delivery.bundle_ready` when notifications enabled | `test_sandbox_e2e_checkpoint_b_skipped_ok_path_completes_bundle` |

---

## 7. Notification gateway matrix

| ID | Notify config | Mode | Trigger | Expected emit? | Expected `event_type`(s) | Side effects if emit | Unit test(s) |
|----|---------------|------|---------|----------------|---------------------------|----------------------|--------------|
| N-1 | **disabled** (default) | run | any | **No** | — | no files | `test_disabled_returns_skipped`, `test_returns_none_when_disabled` |
| N-2 | enabled + **dry_run** | run | unit `send_notification` | **No write** | any | `channel=dry_run` | `test_dry_run_returns_no_write` |
| N-3 | **enabled** | run | auto intake demo_phase | **Yes** | `checkpoint.approved`, `run.completed` (+ others profile-dependent) | files under `outbox/notifications/<case_ref>/`, jsonl | `test_enable_notifications_produces_notification_files` |
| N-4 | enabled | **preview** | `--enable-notifications` | **No** | — | empty `notifications[]` | `test_preview_mode_does_not_emit_notifications` |
| N-5 | env `GOV_NOTIFICATION_GATEWAY_ENABLED=1` | run | auto intake | **Yes** | ≥1 event | same as N-3 | `test_env_var_enables_notifications` |
| N-6 | enabled | run | CP-A awaiting (needs_review run) | **Yes** | `checkpoint.awaiting_human`, `run.completed` | per-event JSON + jsonl | *(orchestrator behavior; covered indirectly by N-3 / integration)* |
| N-7 | enabled | run | CP-B written (sampleco run) | **Yes** | `checkpoint.awaiting_human`, `run.completed` | per-event JSON + jsonl | *(orchestrator; see B-F2)* |
| N-8 | enabled | run | sandbox bundle ok | **Yes** | `delivery.bundle_ready`, `run.completed` | per-event JSON + jsonl | *(orchestrator; see B-F5)* |
| N-9 | **sink failure** (mock) | run | unit | emit attempted | `send_notification` returns `ok=false` | orchestrator **not** downgraded | `test_send_notification_handles_write_failure_gracefully` |
| N-10 | exception in safe emit | run | unit | error dict | `emit_notification_safe` → `ok=false`, `skipped_main_flow=true` | no raise | `test_emit_notification_safe_handles_exception_gracefully` |
| N-11 | **human** approval | CLI | delivery CLI `_emit_checkpoint_approved_for_human` | **Yes** | `checkpoint.approved` (`approval_source=human`) | 1 file in notifications dir | `test_checkpoint_approved_event_for_human` |
| N-12 | human disabled | CLI | `enabled=False` | **No** | — | returns `None` | `test_disabled_human_approval_returns_none` |
| N-13 | auto vs human source | run / CLI | auto: orchestrator S4/S12; human: delivery CLI | **Yes** | same `event_type`, different `approval_source` | — | `test_enable_notifications_produces_notification_files` (auto); `test_checkpoint_approved_event_for_human` (human) |
| N-14 | delivery CLI notify experiment | CLI | `--run-notify-experiment` on approve | separate experiment hook (not gateway jsonl) | controlled notify experiment | `test_notify_experiment_called_on_approve` |
| N-15 | delivery CLI notify skipped | CLI | default / request_changes | experiment skipped | — | `test_notify_experiment_skipped_by_default`, `test_notify_experiment_skipped_for_request_changes` |
| N-16 | concurrent jsonl | unit | multiple sends | **Yes** | valid jsonl lines | best-effort lock | `test_concurrent_appends_produce_valid_jsonl`, `test_concurrent_writes_different_cases` |

---

## 7.2 Intake Gate notify (P75-G4)

> **CLI**: `scripts/run_intake_gate_cli.py` — upstream documented entry for gate-only runs.

```bash
python scripts/run_intake_gate_cli.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode run --enable-notifications --format json \
  [--outbox-root <tmp>]

python scripts/inspect_workflow_events.py --case-ref demo_phase --format json
```

| ID | Notify config | Mode | Trigger | Expected emit? | Expected `event_type` | Side effects | Unit test(s) |
|----|---------------|------|---------|----------------|----------------------|--------------|--------------|
| G4-1 | **enabled** | **run** | gate outbox record written | **Yes** | `intake.gate_decision` | `outbox/notifications/<case_ref>/`, jsonl | `test_gate_run_mode_emits_intake_gate_decision_notification` |
| G4-2 | enabled | **preview** | `--enable-notifications` | **No** | — | no notification files | `test_gate_preview_mode_does_not_emit_notification` |
| G4-3 | **disabled** (default) | run | gate run | **No** | — | gate record only | `test_gate_notifications_can_be_disabled_via_flag` |
| G4-4 | enabled + sink failure | run | mock `send_notification` fail | attempted | `intake.gate_decision` returns `ok=false` | gate result **still** `ok=true` | `test_notify_failure_does_not_break_gate_result` |
| G4-5 | enabled | unit | `build_intake_gate_decision_event` | envelope only | payload fields in `artifacts` + `status_summary` | — | `test_build_intake_gate_decision_event_payload_shape` |

## 7.3 Gate + CP-A + notify E2E regression (P75-REGRESSION)

> **Doc**: `docs/phase-7.5-gate-checkpointA-notify-e2e-v1.md` — three frozen behavior samples.

| ID | Gate `decision` | Input (`task_type` / `case_ref`) | CP-A expected | Notify (`intake.gate_decision`) | Unit test(s) |
|----|-----------------|----------------------------------|---------------|----------------------------------|--------------|
| REG-1 | `accept` | `tabular.intake.new_case` / `demo_phase` | **skipped**; no checkpoint file | **Yes** (run + enabled) | `test_accept_low_risk_skips_checkpoint_a_and_emits_gate_notify` |
| REG-2 | `review_needed` | `tabular.cleaning.mvp` / `demo_phase` | **awaiting_human**; checkpoint written | **Yes** | `test_review_needed_triggers_checkpoint_a_and_emits_gate_notify` |
| REG-3 | `reject` (policy deny) | `tabular.intake.new_case` / synthetic PHI case | **not_applicable** (S3 early-exit); no checkpoint | **Yes**; `reason_codes` includes `policy_deny_phi` | `test_policy_deny_reject_skips_checkpoint_a_and_emits_gate_notify` |

```bash
python -m unittest tests.test_intake_gate_checkpointA_notify_e2e_v1.py -v
```

**Payload contract (minimum)**: `case_ref`, `intake_decision_id`, canonical `decision`, `reason_codes[]`, `policy_version`, `outbox_record_path` (in `artifacts` and mirrored in `status_summary`).

**Optional doc-only mapping**: gate `reject` may be cross-referenced with orchestrator `run.blocked` semantics — distinct events; do not dedupe in v1.

---

## 7.1 Feedback ingest / downstream ack (P8.9-T2)

| ID | Condition | Expected | Ack written? | Audit gap | Tools / commands | Unit test(s) |
|----|-----------|----------|--------------|-----------|------------------|--------------|
| F-1 | notification emitted, no ack | `tracking_status=pending_ack` | **No** | `missing_downstream_ack` | `python scripts/inspect_workflow_events.py --case-ref <case_ref> --format json`; `python scripts/run_feedback_ingest.py --case-ref <case_ref> --dry-run` | `test_ingest_pending_events_lists_unacked_notifications`, `test_consumer_pending_ack_when_notification_without_ack` |
| F-2 | `record_downstream_ack(received)` | `tracking_status=acked` | **Yes** | gap cleared | `python scripts/inspect_workflow_events.py --case-ref <case_ref> --format json` (see `downstream_ack` + `ack_path`) | `test_record_downstream_ack_received_writes_ack_file`, `test_consumer_merges_downstream_ack_into_tracking_status` |
| F-3 | `record_downstream_ack(failed)` | `tracking_status=failed`, `last_error=message` | **Yes** | `downstream_ack_failed` | `python scripts/inspect_workflow_events.py --case-ref <case_ref> --format json` (see `last_error`) | `test_record_downstream_ack_failed_sets_message_and_status`, `test_consumer_failed_ack_surfaces_last_error` |
| F-4 | duplicate ack same content | idempotent skip | unchanged file | — | — | `test_duplicate_ack_is_idempotent` |
| F-5 | `--dry-run` ingest CLI | lists pending only | **No** | gaps unchanged | `python scripts/run_feedback_ingest.py --case-ref <case_ref> --dry-run` | `test_ingest_dry_run_does_not_write_ack_files` |

Operator commands:

```bash
python scripts/inspect_workflow_events.py --case-ref demo_phase --format json
python scripts/inspect_workflow_events.py --case-ref demo_phase --format text
python scripts/run_feedback_ingest.py --case-ref demo_phase --dry-run
python scripts/list_operator_backlog_v1.py --status pending --format json
python scripts/run_agent_audit_quickview.py --case-ref demo_phase --view investigation --format json
```

Per-case operator backlog index: `docs/phase-8-operator-backlog-v1.md` (P8-T2).

---

## 7.2 Operator backlog (P8-T2)

| ID | Condition | Expected `status` | Tools / commands | Unit test(s) |
|----|-----------|-------------------|------------------|--------------|
| O-1 | CP-A `awaiting_human` on disk | `pending` | `python scripts/list_operator_backlog_v1.py --status pending --format json` | `test_backlog_lists_case_with_open_checkpoint_a` |
| O-2 | CP-A `approved` + latest `run.completed` | `completed`; excluded from `--status pending` | same CLI with `--status completed` / `pending` | `test_backlog_does_not_list_completed_case` |
| O-3 | `run.blocked` terminal vs open CP-A | `blocked` vs `pending` filter separation | `--status blocked` / `--status pending` | `test_backlog_filters_by_status` |

---

## 7.3 P8.9 verification bundle (REGRESSION v1)

| ID | Condition | Expected | Verdict (2026-06-27) | Tools / commands | Unit test(s) |
|----|-----------|----------|----------------------|------------------|--------------|
| P89-REG-1 | `demo_phase` run + notifications + dispatch | Bundle dir contains 4 JSON artifacts; events include `checkpoint.approved` + `run.completed`; `run.completed` acked when dispatch on | **PASS** · `ok: true` · report `docs/p8_9-verification-report-v1.md` · gaps: T4 webhook deferred | `python scripts/run_p8_9_verification_bundle_v1.py --case-ref demo_phase --format json` | `test_verification_bundle_script_produces_expected_files`, `test_verification_bundle_contains_expected_event_types_and_ack_statuses` |

Artifacts: `outbox/verification/<case_slug>/` — see `docs/p8_9-verification-bundle-v1.md` · executed report: `docs/p8_9-verification-report-v1.md`.

---

## 7.4 Multi-phase smoke / metrics (MP-SMOKE + MP-METRICS)

> **Scope**: Cross-phase release sanity — orchestrates existing CLIs without changing them. **Not** a replacement for §2–§7 unit tests; indirectly exercises rows below in one pass.

| ID | Tool | Steps / metrics | Indirect matrix coverage | Tools / commands | Unit test(s) |
|----|------|-----------------|--------------------------|------------------|--------------|
| MP-1 | **Multi-phase smoke v1** | 7 steps: gate preview → gate run+notify → std-case experiment → events inspect → feedback dry-run → P8.9 bundle collect → operator backlog | §7.2 G4-* (gate notify) · §7.1 F-1/F-5 (feedback dry-run) · §7.2 O-1–O-3 (backlog) · §7.3 P89-REG-1 (bundle) · §2–§3 forward experiment path (smoke step 3) | `python scripts/run_multi_phase_smoke_v1.py --case-ref demo_phase --format json` · optional `--enable-dispatch` | `tests/test_multi_phase_smoke_v1.py` |
| MP-2 | **Std-case metrics exporter v1** | Read-only: `pending_cases_count` · `blocked_cases_count` · `completed_cases_count` · `notifications_emitted_count` · `notifications_with_pending_ack_count` · `notifications_failed_ack_count` | §7.1 F-1/F-3 (pending_ack / failed ack visibility) · §7.2 O-1–O-3 (operator status) · post-smoke drift check for §7 G-6/N-6–N-8 (aggregate, not per-event) | `python scripts/export_std_case_metrics_v1.py --case-ref demo_phase --format json` · `--format prometheus` | `tests/test_export_std_case_metrics_v1.py` |

**Indirect gap coverage (§9)**: MP-1/MP-2 together **partially** cover **G-6** (cross-step notify presence via smoke + metrics counts), **G-7** (dispatch path when `--enable-dispatch`), and **G-11** (`run.blocked` / terminal ack visibility via bundle + metrics); they **do not** cover resume-loop gaps **G-1–G-5**, webhook **G-10**, or per-step orchestrator event assertions.

### 7.4.1 Control-plane trace (W1-P75-TRACE · upstream observability only)

> **Scope**: Gate → outbox → MP-SMOKE steps 1–2 → metrics trace SSOT — **not** G-1–G-5 resume **runtime** · **not** staging · doc-only contract.

| ID | Layer | Trace fields | Tools / commands | Unit test(s) |
|----|-------|--------------|------------------|--------------|
| CP-T1 | Gate CLI / layer | `decision` · `reason_codes[]` · `p75_policy_decision` · `deny_reason` · `gate_checks[]` | `python scripts/run_intake_gate_cli.py --task-type tabular.cleaning.mvp --case-dir cases/demo_phase --mode preview --format json` | `tests/test_intake_gate_policy_integration_v1.py` |
| CP-T2 | MP-SMOKE step 1–2 | `steps[gate_*].detail`：`intake_decision_id` · `case_ref` · `decision`/`gate_decision` · `event_type=intake.gate_decision` · `artifact_paths.outbox_record_path` | `python scripts/run_multi_phase_smoke_v1.py --case-ref demo_phase --format json` | `tests/test_multi_phase_smoke_v1.py` |
| CP-T2b | MC-SMOKE per-case | `cases[].gate_decision` · `failed_steps[]`（**非** top-level `gate_status`） | `python scripts/run_multi_case_smoke_v1.py --cases demo_phase --format json` | `tests/test_multi_case_smoke_v1.py` |
| CP-T3 | MP-METRICS post-smoke | `notifications_failed_ack_count` · `notifications_with_pending_ack_count` · backlog counts | `python scripts/export_std_case_metrics_v1.py --case-ref demo_phase --format json` | `tests/test_export_std_case_metrics_v1.py` |
| CP-T4 | G-1–G-5 upstream only | `resume_eligibility` · `resume_blocked_reason` · `checkpoint_load_error` · `case_allowlist_block` | `rg "G-1|upstream observability only" docs/p75-intake-gate-control-plane-trace-v1.md` | **No runtime** — Wave 2 `W2-P7-matrix-G1-G5-resume-loop-v1` |

**Doc SSOT**: `docs/p75-intake-gate-control-plane-trace-v1.md` · ticket `W1-P75-TRACE-UPSTREAM-v1` · deny cross-ref `docs/p75-policy-deny-path-mvp-v1.md` §Trace fields · intake CLI cross-ref `docs/p75-intake-cli-upstream-mvp-v1.md`.

### 7.4.2 Delivery trace 契約（W3-P89-OBS · P8/P8.9 主鏈）

| ID | Layer | Trace fields / artifacts | Tools / commands | Notes |
|----|-------|--------------------------|------------------|-------|
| OBS-T1 | P8/P8.9 delivery observability contract | `case_ref` · `run_id`/`experiment_id` · `multi_phase_smoke.ok` · `events_summary.count` · `acks_summary.pending_count` · `notifications_failed_ack_count` · MP steps 1–7 · P8.9 四檔 | 見 `docs/p8_p89_delivery_observability_contract_v1.md` §3 | **doc-only** · ≠ prod SLO · bridge HTTP **optional** |

**Doc SSOT**: `docs/p8_p89_delivery_observability_contract_v1.md` · ticket `W3-P89-OBS-delivery-trace-contract-v1` · evidence tier → `docs/p8_p89_evidence_index_v1.md`.

---

## 7.5 Multi-case smoke / metrics (MC-SMOKE + MC-METRICS)

> **Scope**: Fleet-level release sanity — wraps MP-SMOKE / MP-METRICS across multiple representative cases. **Not** a replacement for §2–§7 unit tests; indirectly exercises multi-profile risk, gate/policy paths, and cross-case backlog/ack drift in one pass.

| ID | Tool | Cases / profiles | Indirect matrix coverage | Tools / commands | Unit test(s) |
|----|------|------------------|--------------------------|------------------|--------------|
| MC-1 | **Multi-case smoke v1** | Default: `demo_phase` (bundle) · `sampleco/2026-0001` (CP-B) · `phi_demo` (PHI deny / gate reject) | §2 A-F4/A-F5 (demo bundle vs auto-approve) · §3 B-F2/B-F4 (sampleco CP-B vs demo skip) · §7 REG-3 (policy deny via `phi_demo` synthetic) · §7.1–§7.3 (seven-step MP-SMOKE per case) · multi-profile run-path risk (stable vs controlled stop) | `python scripts/run_multi_case_smoke_v1.py --cases demo_phase,sampleco --format json` · full default (incl. deny probe): omit `--cases` | `tests/test_multi_case_smoke_v1.py` |
| MC-2 | **Multi-case metrics aggregator v1** | Default fleet: `demo_phase` · `sampleco/2026-0001` | §7.1 F-1/F-3 (fleet pending_ack / failed ack totals) · §7.2 O-1–O-3 (cross-case pending/blocked/completed) · post-smoke fleet drift after MC-1 | `python scripts/aggregate_multi_case_metrics_v1.py --format json` · `--cases demo_phase,sampleco/2026-0001 --format text` | `tests/test_aggregate_multi_case_metrics_v1.py` |

**Release sanity pairing (doc-only)**: run **MC-1** first to see which `case_ref` / profile fails (`failed_cases`, `failed_steps`); then **MC-2** for fleet-level `total_pending_cases` / `total_blocked_cases` / `total_notifications_failed_ack`. For single-case drill-down, use §7.4 MP-1/MP-2.

**Indirect gap coverage (§9)**: MC-1/MC-2 extend MP-1/MP-2 to **multi-profile** and **policy-deny** paths; they **still do not** cover resume-loop gaps **G-1–G-5**, webhook **G-10**, extended experimental fixtures (`additional_demo` / `sandbox_client`), or per-step orchestrator event assertions.

---

## 7.6 Policy deny upstream (W1-P75 · doc/MVP)

> **Scope**: P7.5 policy deny path observability — **not** full gate · **not** staging · **not** G-1–G-5 resume runtime.

| ID | Path / probe | Expected deny signals | Tools / commands | Unit test(s) |
|----|--------------|----------------------|------------------|--------------|
| PD-1 | Golden `deny_*.json` (4 fixtures) | `decision=reject` · `policy_deny_*` in `reason_codes` · `p75_policy_decision=policy_deny` | `python -m unittest tests.test_intake_gate_policy_integration_v1 -v` | `test_golden_deny_fixtures_snapshot` |
| PD-2 | MC-SMOKE `phi_demo` (ephemeral PHI) | Gate reject · smoke `ok=false` · `failed_steps` includes downstream steps | `python scripts/run_multi_case_smoke_v1.py --cases phi_demo --format json` | `test_phi_demo_intake_matches_policy_deny_trace` · `test_multi_case_smoke_summary_top_level_ok_false_when_any_case_fails` |
| PD-3 | Trace field SSOT | `p75_policy_decision` · `deny_reason` · `reason_codes[]` · `gate_checks[]` · `intake.gate_decision` | `rg "p75_policy_decision|deny_reason" docs/p75-policy-deny-path-mvp-v1.md` | `test_derive_p75_policy_trace_deny_phi` |

**Doc SSOT**: `docs/p75-policy-deny-path-mvp-v1.md` · ticket `W1-P75-POLICY-DENY-MVP-v1` · full upstream trace chain → `docs/p75-intake-gate-control-plane-trace-v1.md` §Cross-references.

---

## 8. Registry / fail-close (orchestrator adjacent)

| ID | Condition | Expected `final_status` | Checkpoints written? | Unit test(s) |
|----|-----------|-------------------------|----------------------|--------------|
| X-1 | Selector registry fail-closed | `blocked_at_selector_registry` | **No** A/B files | `test_registry_fail_closed_blocks_run_path_no_checkpoints` |
| X-2 | Registry not approved (preview) | `blocked_at_selector_registry` | **No** | `test_registry_not_approved_blocks_preview_mode` |
| X-3 | Ok path after registry wiring | not blocked | normal | `test_ok_path_regression_after_registry_wiring` |

---

## 9. Coverage gaps (documented, no new tests in this ticket)

Cells with **implementation behavior** but **no dedicated orchestrator/resume unittest**:

> **G-1–G-5 spec/trace contract (spec-only)**: `docs/p7-resume-loop-g1-g5-spec-v1.md` · YAML `04_Workflows/testing/p7-resume-loop-g1-g5-matrix-v1.yaml` · ticket `W2-P7-matrix-G1-G5-resume-loop-v1`. **Not a runtime prod gate.**

| Gap ID | Matrix cell | Notes | trace_fields | verify_command | expected `ok` / `final_status` |
|--------|-------------|-------|--------------|----------------|--------------------------------|
| G-1 | R-11 `stale_checkpoint` | `validate_resume_eligibility` returns `stale_checkpoint` when `awaiting_human` + expired `expires_at`; no orchestrator test | `resume_eligibility=stale_checkpoint` | `rg "G-1|stale_checkpoint" docs/p7-resume-loop-g1-g5-spec-v1.md` · `python scripts/verify_g_matrix.py` | `ok=false` · `stale_checkpoint` |
| G-2 | R-12 `revise_needed` resume | Integration tests cover plan; resume blocked — no orchestrator resume test | `resume_blocked_reason=revise_needed` | `rg "G-2|revise_needed" docs/p7-resume-loop-g1-g5-spec-v1.md` | `ok=false` · `blocked` |
| G-3 | R-13 `on_hold` resume | CLI/integration cover hold; resume blocked — no orchestrator resume test | `resume_blocked_reason=on_hold` | `rg "G-3|on_hold" docs/p7-resume-loop-g1-g5-spec-v1.md` | `ok=false` · `blocked` |
| G-4 | R-14 missing checkpoint file | Load error → `blocked`; no dedicated test | `checkpoint_load_error` | `rg "G-4|checkpoint_load_error" docs/p7-resume-loop-g1-g5-spec-v1.md` | `ok=false` · `blocked` |
| G-5 | R-15 non-allowlisted case resume | `_run_experiment_resume_from_checkpoint` early block; no dedicated test | `case_allowlist_block` | `rg "G-5|case_allowlist_block" docs/p7-resume-loop-g1-g5-spec-v1.md` | `ok=false` · `blocked` |
| G-6 | N-6 / N-7 / N-8 explicit event assertions | Orchestrator emits events; only N-3 asserts file counts, not per-step event types for awaiting_human / bundle_ready |
| G-7 | Resume path + notifications enabled | **Partial (T3)**: dispatch registry + post-emit hook for `delivery.bundle_ready` / terminal events when `GOV_NOTIFICATION_DISPATCH_ENABLED=1`; resume-path notification list still matrix gap — see `tests/test_notification_dispatch_v1.py` |
| G-8 | `checkpoint.rejected` / `changes_requested` events | Documented as **not emitted** in v1; no tests (intentional omission) |
| G-9 | Approved checkpoint + expired `expires_at` | v1 intentionally **does not** re-check expiry on approved (closure report) |
| G-10 | Webhook adapter live dispatch | Skeleton dry-run only; deferred to P8.9-T4 |
| G-11 | `run.blocked` explicit orchestrator test | **Partial (T3)**: `run_terminal_log_v1` handler + dispatch unittest for `run.blocked` ack path; dedicated orchestrator CLI test still open |
| G-12 | **Multi-phase smoke / metrics** (MP-SMOKE + MP-METRICS) | **Partial (indirect)**: §7.4 MP-1 seven-step smoke + MP-2 metrics catch cross-phase wiring regressions (gate → experiment → consumer → backlog) and ack/backlog drift; **not** resume-path, stale-checkpoint, or per-event-type assertions — see §7.4 indirect coverage note |
| G-13 | **Multi-case smoke / metrics** (MC-SMOKE + MC-METRICS) | **Partial (indirect)**: §7.5 MC-1/MC-2 extend MP-1/MP-2 to multi-profile (`demo_phase` vs `sampleco`) and policy-deny (`phi_demo`); fleet ack/backlog totals; **not** extended fixtures, resume-loop, or per-event-type assertions — see §7.5 indirect coverage note |

---

## 10. Quick run index

```bash
# Full suites referenced by this matrix
python -m unittest tests.test_checkpoint_a_integration_v1 -v
python -m unittest tests.test_checkpoint_b_integration_v1 -v
python -m unittest tests.test_hitl_checkpoints_v1 -v
python -m unittest tests.test_delivery_approval_cli_v1 -v
python -m unittest tests.test_notification_gateway_v1 -v
python -m unittest tests.test_intake_gate_notify_v1 -v
python -m unittest tests.test_agent_standard_case_experiment -v

# Multi-phase smoke + metrics (release sanity)
python scripts/run_multi_phase_smoke_v1.py --case-ref demo_phase --format json
python scripts/export_std_case_metrics_v1.py --case-ref demo_phase --format json
python -m unittest tests.test_multi_phase_smoke_v1 tests.test_export_std_case_metrics_v1 -v

# Multi-case smoke + metrics (fleet release sanity)
python scripts/run_multi_case_smoke_v1.py --cases demo_phase,sampleco --format json
python scripts/aggregate_multi_case_metrics_v1.py --format json
python -m unittest tests.test_multi_case_smoke_v1 tests.test_aggregate_multi_case_metrics_v1 -v
```

**Row counts (this document)**: §2 **8** + §3 **9** + §4 **15** + §5 **7** + §6 **5** + §7 **16** + §7.5 **2** + §8 **3** ≈ **65** scenario rows.

---

## 11. References

| Artifact | Path |
|----------|------|
| Orchestrator | `scripts/run_agent_standard_case_experiment.py` |
| Resume validation | `validate_resume_eligibility()` in same file |
| Checkpoint A integration | `hitl/checkpoint_a_integration_v1.py` |
| Checkpoint B integration | `hitl/checkpoint_b_integration_v1.py` |
| HITL core | `hitl/checkpoints_v1.py`, `scripts/run_hitl_checkpoint_cli.py` |
| Notification gateway | `delivery/notification_gateway_v1.py` |
| Delivery approval CLI | `delivery/delivery_approval_cli_v1.py` |
| Closure report | `04_Workflows/reports/W6-standard-case-v2-closure-report.md` |
| HITL design doc | `docs/hitl-checkpoints-v1.md` |
| Multi-phase smoke runner | `scripts/run_multi_phase_smoke_v1.py` |
| Std-case metrics exporter | `scripts/export_std_case_metrics_v1.py` |
| Multi-case smoke runner | `scripts/run_multi_case_smoke_v1.py` |
| Multi-case metrics aggregator | `scripts/aggregate_multi_case_metrics_v1.py` |
| Release sanity dashboard | `docs/WAVE_PROGRESS_DASHBOARD.md` §Multi-phase smoke & metrics |
