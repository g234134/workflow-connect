# TICKET STATE · USER-APPROVAL-TABULAR-CLEANING-20260722 · Internal tabular cleaning execution

> User-authorized internal execution and delivery-readiness record. This ticket does not alter global DarkOps phase gates, production controls, SLA claims, or required CI.

---

## FRAME

- Goal: Record the user's explicit approval and run one reproducible internal C2-P2 tabular cleaning case.
- Scope:
  - Record the approval as an internal execution authorization.
  - Create a minimal isolated case from the existing demo input.
  - Run profile suggestion and intake-to-bundle E2E validation.
  - Record CP-B delivery approval and create a delivery ZIP for internal handoff.
  - Register the approved internal case in the existing local case index.
- NonScope:
  - Global `dark_ops_worker` phase-gate changes.
  - Production delivery, SLA, external notifications, API keys, or mandatory CI.
  - Actual invoicing, payment collection, external transmission, or customer-facing SLA claims.
- AllowedPaths:
  - `04_Workflows/tickets/USER-APPROVAL-TABULAR-CLEANING-20260722_state.md`
  - `cases/internal-approved/2026-0001/**`
  - `cases/index.json` (only if the existing case CLI updates it)
  - `scripts/suggest_cleaning_profile.py`
  - `tests/test_suggest_cleaning_profile.py`
  - `scripts/cases_index_lib.py`
  - `cases/index.json`
- BlockedPaths:
  - `04_Workflows/task_routing_table.json`
  - `04_Workflows/HARNESS_CONSTITUTION.md`
  - `04_Workflows/ENGINEERING_CONTRACT.md`
  - `.github/**`
- Dependencies: User approvals 「核准.開始吧」 and 「都放行交付」 received 2026-07-22; existing C2-P2 scripts and `gov_core_system` venv.
- relay_mode: same_chat
- AcceptanceCriteria:
  - A scoped approval record exists.
  - A new isolated case has `intake.json`, `raw/`, `cleaned/`, and `reports/` artifacts.
  - Profile suggestion and E2E validation return structured results.
  - CP-B is recorded, `delivery_ready=true`, and a local delivery ZIP is created.
  - No global gate is relaxed and no external delivery is claimed.

### Wave Master 擴展（Wave Master 子票 · 必填）

- wave_id: null
- group_id: null
- lifecycle_phase: O
- phase_targets: []
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: [User explicitly approved internal execution and CP-B; payment, invoicing, and external sending remain manual.]
- infra_only_prereqs: []
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: []
  - downstream_waves: []
  - blocks_if_missing: []
- risks: `internal_case_artifacts` · validation may write case outputs · low · low · use a new isolated case · no production effect.
- observability:
  - verify_commands:
    - `python scripts/suggest_cleaning_profile.py --case-dir cases/internal-approved-20260722 --json`
    - `python scripts/run_case_e2e_validation.py --case-dir cases/internal-approved-20260722 --json`
  - evidence_artifacts:
    - `cases/internal-approved-20260722/intake.json`
    - `cases/internal-approved-20260722/reports/report.json`
  - trace_fields: [case_id, cleaning_profile_id, output_guard.status]
  - success_signals: [E2E `ok: true`, output guard `ok`]
  - failure_signals: [E2E non-zero exit, output guard not ok]
- non_claims: [No global DarkOps ungate, no payment collected, no invoice issued, no external delivery sent, no SLA, no required CI.]
- ticket_class: scribe/ops
- evidence_tier: L-local
- parallel_ok: false

---

## STATE

- overall_status: review
- lifecycle_phase: O
- current_owner: reviewer
- next_action: Verify the CP-B record, local delivery ZIP contents, and that only payment/invoicing/external transmission remain manual.
- last_updated: 2026-07-22 · O
- ops_checklist: No external operations required; CP-B is intentionally excluded.
  - [x] User approval recorded for scoped internal execution.
  - [x] Isolated case created as `cases/internal-approved/2026-0001`.
  - [x] Isolated case validated.
  - [x] Delivery readiness evaluated before approval.
  - [x] Case registered in local index.
  - [x] CP-B approval recorded.
  - [x] Local delivery ZIP generated.
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: in_progress
  - scribe: pending

---

## B_REPORT

- changed_files:
  - `scripts/suggest_cleaning_profile.py` — added explicit `--apply` persistence for an operator-reviewed profile suggestion.
  - `tests/test_suggest_cleaning_profile.py` — added regression coverage for profile persistence.
  - `cases/internal-approved/2026-0001/**` — isolated input, cleaned output, and reports.
- artifacts:
  - `cases/internal-approved/2026-0001/intake.json` with `cleaning_profile=generic_low_risk_profile`.
  - `cases/internal-approved/2026-0001/cleaned/Phase_cleaned.csv`.
  - `cases/internal-approved/2026-0001/reports/report.json` and `cleaning_stats.json`.
  - `cases/internal-approved/2026-0001/delivery/2026-0001_delivery_20260722T131535Z.zip`.
  - `cases/internal-approved/2026-0001/delivery_approval.json` with `delivery_approval_status=approved` and `delivery_ready=true`.
- verification:
  - `python -m pytest tests/test_cleaning_profiles_v1.py tests/test_new_cleaning_case.py tests/test_suggest_cleaning_profile.py -q` → `13 passed`.
  - `python scripts/run_case_e2e_validation.py --case-dir cases/internal-approved/2026-0001 --json` → `ok: true`; output guard `ok` (7 input rows, 6 output rows).
  - `python scripts/approve_tabular_delivery.py --case-id internal-approved/2026-0001 --approve --by user-approved-internal --evaluate-only --json` → `delivery_ready: false`, only because CP-B remains unapproved.
  - `python scripts/build_cases_index.py --json` → 3 registered cases.
  - `python scripts/approve_tabular_delivery.py --case-id internal-approved/2026-0001 --approve --by user-authorized-lead --json` → `delivery_ready: true`, CP-B approved, index/signoff/state synchronized.
  - `python scripts/export_case_delivery_zip.py --case-dir cases/internal-approved/2026-0001 --json` → 9-artifact local ZIP.
  - `python -m pytest tests/test_approve_tabular_delivery.py tests/test_cleaning_profiles_v1.py tests/test_new_cleaning_case.py tests/test_suggest_cleaning_profile.py -q` → `19 passed`.
- behavior_notes: Scoped user approval authorized profile application, CP-B, and internal delivery readiness. `--apply` turns an accepted suggestion into an explicit, auditable runner selection; delivery ZIP is local-only and not externally transmitted.
- deferred_items: Payment collection, invoice issuance, external transmission, and all production/governance gate changes remain excluded.

---

## C_REPORT

- conclusion: pending
- blocking_issues: Pending execution.
- checks_summary: Pending execution.
- risk_level: low
- suggestions: Pending execution.

---

## D_REPORT

- docs_updates: No standalone documentation change planned; this state file is the execution record.
- progress_entry: Scoped user approval recorded for one internal C2-P2 validation case; no global gate changed.
- followup_suggestions: Request a separate, explicit CP-B approval only if an external delivery is intended.
