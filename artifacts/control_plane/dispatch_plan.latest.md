# Dispatch Plan (control plane · read-only)

- **Generated at**: 2026-06-23T20:15:39.318418+00:00
- **Tickets scanned**: 216
- **Recommended chats**: 4

## Summary

- **runnable_now**: 127
- **in_review**: 4
- **blocked**: 29
- **done**: 51
- **draft**: 5

## Parallel groups

1. BATCH-MVP-01, C2-D1, C2-P2, DEMO-1, W-MVP-W4A-MEMO-ORCH, W-MVP-W4A-MEMO-SCRIBE, W-next-DISPATCH-CARDS-MVP, W1-T1, W1-T2-mvp-trace-path, W1-T2, W1-T3B-mvp-mainline-regression, W2-T1, W4-T1, W4-T2, W4-T3-A, WB-T8, WC-C1-01
2. BATCH-MVP-02, BATCH-MVP-04, W4-T4, WA-T4, WA-T6
3. W-MVP-W1-INVENTORY, W1-T3, W2-REF-001, WA-T1
4. BATCH-MVP-01, BATCH-MVP-02, BATCH-MVP-04, W-MVP-W1-INVENTORY, W1-T3, W2-REF-001, W4-T4, WA-T1, WA-T4, WA-T6, C2-D1, C2-P2, DEMO-1, W-MVP-W4A-MEMO-ORCH, W-MVP-W4A-MEMO-SCRIBE, W-next-DISPATCH-CARDS-MVP, W1-T1, W1-T2-mvp-trace-path, W1-T2, W1-T3B-mvp-mainline-regression, W2-T1, W4-T1, W4-T2, W4-T3-A, WB-T8, WC-C1-01

## Suggested next

### BATCH-MVP-01 → scribe
- **Reason**: current_owner is scribe
- **Bucket**: runnable_now
- **Parallel**: True (group pg-1-scribe)
- **Expected**: D_REPORT + suggested Progress entry
- **Commands**:
  - `python 04_Workflows/_ops_cycle.py append-report --dry-run  # after D_REPORT`
  - `Open Scribe chat; read 04_Workflows/tickets/BATCH-MVP-01_state.md; write D_REPORT + Progress append`

### BATCH-MVP-02 → implementer
- **Reason**: in_progress with implement/resume/wire/test next_action
- **Bucket**: runnable_now
- **Parallel**: True (group pg-2-implementer)
- **Expected**: B_REPORT updated; STATE overall_status in_progress
- **Commands**:
  - `Open Implementer chat; read 04_Workflows/tickets/BATCH-MVP-02_state.md; execute next_action`

### BATCH-MVP-03 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/BATCH-MVP-03_state.md; update STATE`

### BATCH-MVP-04 → implementer
- **Reason**: in_progress with implement/resume/wire/test next_action
- **Bucket**: runnable_now
- **Parallel**: True (group pg-2-implementer)
- **Expected**: B_REPORT updated; STATE overall_status in_progress
- **Commands**:
  - `Open Implementer chat; read 04_Workflows/tickets/BATCH-MVP-04_state.md; execute next_action`

### C2-D1 → scribe
- **Reason**: done ticket pending scribe progress append
- **Bucket**: done
- **Parallel**: True (group pg-1-scribe)
- **Expected**: D_REPORT + suggested Progress entry
- **Commands**:
  - `python 04_Workflows/_ops_cycle.py append-report --dry-run  # after D_REPORT`
  - `Open Scribe chat; read 04_Workflows/tickets/C2-D1_state.md; write D_REPORT + Progress append`

### C2-P2 → scribe
- **Reason**: done ticket pending scribe progress append
- **Bucket**: done
- **Parallel**: True (group pg-1-scribe)
- **Expected**: D_REPORT + suggested Progress entry
- **Commands**:
  - `python 04_Workflows/_ops_cycle.py append-report --dry-run  # after D_REPORT`
  - `Open Scribe chat; read 04_Workflows/tickets/C2-P2_state.md; write D_REPORT + Progress append`
  - `python notebooks/csv_cleaning/run_tabular_cleaning_plan.py --stage all --case demo_phase`

### CI-SMOKE-multi-phase-smoke-and-metrics-hook-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/CI-SMOKE-multi-phase-smoke-and-metrics-hook-v1_state.md; update STATE`

### DEMO-1 → scribe
- **Reason**: done ticket pending scribe progress append
- **Bucket**: done
- **Parallel**: True (group pg-1-scribe)
- **Expected**: D_REPORT + suggested Progress entry
- **Commands**:
  - `python 04_Workflows/_ops_cycle.py append-report --dry-run  # after D_REPORT`
  - `Open Scribe chat; read 04_Workflows/tickets/DEMO-1_state.md; write D_REPORT + Progress append`

### MC-METRICS-multi-case-metrics-aggregation-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/MC-METRICS-multi-case-metrics-aggregation-v1_state.md; update STATE`

### MC-SCRIBE-multi-case-smoke-and-metrics-doc-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/MC-SCRIBE-multi-case-smoke-and-metrics-doc-v1_state.md; update STATE`

### MC-SMOKE-multi-case-smoke-runner-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/MC-SMOKE-multi-case-smoke-runner-v1_state.md; update STATE`

### MP-METRICS-HTTP-std-case-metrics-endpoint-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/MP-METRICS-HTTP-std-case-metrics-endpoint-v1_state.md; update STATE`

### MP-METRICS-std-case-metrics-exporter-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/MP-METRICS-std-case-metrics-exporter-v1_state.md; update STATE`

### MP-SMOKE-std-case-multi-phase-smoke-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/MP-SMOKE-std-case-multi-phase-smoke-v1_state.md; update STATE`

### P75-G2-intake-gate-layer-and-outbox-record-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/P75-G2-intake-gate-layer-and-outbox-record-v1_state.md; update STATE`

### P75-G3-intake-gate-policy-allowlist-denylist-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/P75-G3-intake-gate-policy-allowlist-denylist-v1_state.md; update STATE`

### P75-G4-intake-gate-notify-and-upstream-entry-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/P75-G4-intake-gate-notify-and-upstream-entry-v1_state.md; update STATE`

### P75-REGRESSION-gate-checkpointA-notify-e2e-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/P75-REGRESSION-gate-checkpointA-notify-e2e-v1_state.md; update STATE`

### P8-API-operator-backlog-http-endpoint-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/P8-API-operator-backlog-http-endpoint-v1_state.md; update STATE`

### P8-T2-operator-pending-visibility-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/P8-T2-operator-pending-visibility-v1_state.md; update STATE`

### P8.9-REGRESSION-standard-case-verification-bundle-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/P8.9-REGRESSION-standard-case-verification-bundle-v1_state.md; update STATE`

### P8.9-T2-feedback-ingest-and-downstream-ack-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/P8.9-T2-feedback-ingest-and-downstream-ack-v1_state.md; update STATE`

### P8.9-T3-downstream-dispatch-handler-registry-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/P8.9-T3-downstream-dispatch-handler-registry-v1_state.md; update STATE`

### W-DOCSYNC-2026-06-24-phase-refresh-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W-DOCSYNC-2026-06-24-phase-refresh-v1_state.md; update STATE`

### W-MVP-W1-INVENTORY → reviewer
- **Reason**: implementation or acceptance awaiting reviewer
- **Bucket**: in_review
- **Parallel**: True (group pg-3-reviewer)
- **Expected**: C_REPORT with conclusion accepted|needs_changes|rejected
- **Commands**:
  - `Open Reviewer chat; read 04_Workflows/tickets/W-MVP-W1-INVENTORY_state.md; write C_REPORT`

### W-MVP-W4A-MEMO-ORCH → scribe
- **Reason**: done ticket pending scribe progress append
- **Bucket**: done
- **Parallel**: True (group pg-1-scribe)
- **Expected**: D_REPORT + suggested Progress entry
- **Commands**:
  - `python 04_Workflows/_ops_cycle.py append-report --dry-run  # after D_REPORT`
  - `Open Scribe chat; read 04_Workflows/tickets/W-MVP-W4A-MEMO-ORCH_state.md; write D_REPORT + Progress append`

### W-MVP-W4A-MEMO-SCRIBE → scribe
- **Reason**: done ticket pending scribe progress append
- **Bucket**: done
- **Parallel**: True (group pg-1-scribe)
- **Expected**: D_REPORT + suggested Progress entry
- **Commands**:
  - `python 04_Workflows/_ops_cycle.py append-report --dry-run  # after D_REPORT`
  - `Open Scribe chat; read 04_Workflows/tickets/W-MVP-W4A-MEMO-SCRIBE_state.md; write D_REPORT + Progress append`

### W-MVP-W5-LOCAL-UI → orchestrator
- **Reason**: current_owner is orchestrator
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W-MVP-W5-LOCAL-UI_state.md; update STATE`

### W-next-DISPATCH-CARDS-MVP → scribe
- **Reason**: done ticket pending scribe progress append
- **Bucket**: done
- **Parallel**: True (group pg-1-scribe)
- **Expected**: D_REPORT + suggested Progress entry
- **Commands**:
  - `python 04_Workflows/_ops_cycle.py append-report --dry-run  # after D_REPORT`
  - `Open Scribe chat; read 04_Workflows/tickets/W-next-DISPATCH-CARDS-MVP_state.md; write D_REPORT + Progress append`
  - `python Scripts/run_dispatch_executor.py --json-out artifacts/control_plane/dispatch_plan.latest.json --md-out artifacts/control_plane/dispatch_plan.latest.md`

### W-PROG-phase-progress-refresh-2026-06 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W-PROG-phase-progress-refresh-2026-06_state.md; update STATE`

### W1-T1 → scribe
- **Reason**: done ticket pending scribe progress append
- **Bucket**: done
- **Parallel**: True (group pg-1-scribe)
- **Expected**: D_REPORT + suggested Progress entry
- **Commands**:
  - `python 04_Workflows/_ops_cycle.py append-report --dry-run  # after D_REPORT`
  - `Open Scribe chat; read 04_Workflows/tickets/W1-T1_state.md; write D_REPORT + Progress append`
  - `python 04_Workflows/_ops_cycle.py checklist --mode full`

### W1-T2-mvp-trace-path → scribe
- **Reason**: done ticket pending scribe progress append
- **Bucket**: done
- **Parallel**: True (group pg-1-scribe)
- **Expected**: D_REPORT + suggested Progress entry
- **Commands**:
  - `python 04_Workflows/_ops_cycle.py append-report --dry-run  # after D_REPORT`
  - `Open Scribe chat; read 04_Workflows/tickets/W1-T2-mvp-trace-path_state.md; write D_REPORT + Progress append`

### W1-T2 → scribe
- **Reason**: done ticket pending scribe progress append
- **Bucket**: done
- **Parallel**: True (group pg-1-scribe)
- **Expected**: D_REPORT + suggested Progress entry
- **Commands**:
  - `python 04_Workflows/_ops_cycle.py append-report --dry-run  # after D_REPORT`
  - `Open Scribe chat; read 04_Workflows/tickets/W1-T2_state.md; write D_REPORT + Progress append`
  - `python 04_Workflows/_phase5_pg_ingest_soak.py`

### W1-T3 → reviewer
- **Reason**: implementation or acceptance awaiting reviewer
- **Bucket**: in_review
- **Parallel**: True (group pg-3-reviewer)
- **Expected**: C_REPORT with conclusion accepted|needs_changes|rejected
- **Commands**:
  - `Open Reviewer chat; read 04_Workflows/tickets/W1-T3_state.md; write C_REPORT`
  - `python -m unittest tests.test_wf_status_summary tests.test_eval_trace_correlate -v`

### W1-T3B-mvp-mainline-regression → scribe
- **Reason**: done ticket pending scribe progress append
- **Bucket**: done
- **Parallel**: True (group pg-1-scribe)
- **Expected**: D_REPORT + suggested Progress entry
- **Commands**:
  - `python 04_Workflows/_ops_cycle.py append-report --dry-run  # after D_REPORT`
  - `Open Scribe chat; read 04_Workflows/tickets/W1-T3B-mvp-mainline-regression_state.md; write D_REPORT + Progress append`
  - `python scripts/run_mvp_mainline_regression.py -v`
  - `python -m unittest tests.test_mvp_mainline -v`

### W1-T4 → implementer
- **Reason**: draft ticket assigned to implementer
- **Bucket**: draft
- **Parallel**: False
- **Expected**: B_REPORT updated; STATE overall_status in_progress
- **Commands**:
  - `Open Implementer chat; read 04_Workflows/tickets/W1-T4_state.md; execute next_action`
  - `python -m unittest tests.test_kb_index_selector_hook -v`

### W10-T1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W10-T1-agent-lines-ci-workflow-hook-v1_state.md; update STATE`

### W10-T1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W10-T1-integrate-agent-lines-into-ci-v1_state.md; update STATE`

### W10-T2-agent-lines-metrics-and-monitoring-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W10-T2-agent-lines-metrics-and-monitoring-v1_state.md; update STATE`

### W10-T2 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W10-T2-selector-consumes-approved-registry-v1_state.md; update STATE`

### W10-T3 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W10-T3-agent-lines-audit-quickview-cli-v1_state.md; update STATE`

### W10-T3 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W10-T3-orchestrator-registry-fail-closed-wiring-v1_state.md; update STATE`

### W10-T4-agent-and-non-tabular-lines-readme-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W10-T4-agent-and-non-tabular-lines-readme-v1_state.md; update STATE`

### W11-T1-promote-experimental-tabular-fixtures-to-controlled-line-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W11-T1-promote-experimental-tabular-fixtures-to-controlled-line-v1_state.md; update STATE`

### W11-T2 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W11-T2-non-tabular-lightweight-content-checks-v1_state.md; update STATE`

### W11-T3-agent-lines-monthly-metrics-report-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W11-T3-agent-lines-monthly-metrics-report-v1_state.md; update STATE`

### W11-T4-agent-and-non-tabular-lines-readme-v2 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W11-T4-agent-and-non-tabular-lines-readme-v2_state.md; update STATE`

### W12-T1-tabular-controlled-end-to-end-delivery-sandbox-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W12-T1-tabular-controlled-end-to-end-delivery-sandbox-v1_state.md; update STATE`

### W12-T2-sandbox-e2e-checkpoint-b-full-integration-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W12-T2-sandbox-e2e-checkpoint-b-full-integration-v1_state.md; update STATE`

### W12-T2-tabular-fixture-maturity-aware-metrics-and-ci-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W12-T2-tabular-fixture-maturity-aware-metrics-and-ci-v1_state.md; update STATE`

### W12-T3 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W12-T3-non-tabular-first-real-processing-step-sandbox-v1_state.md; update STATE`

### W12-T4 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W12-T4-wave1-to-wave12-architecture-retrospective-v1_state.md; update STATE`

### W2-REF-001 → reviewer
- **Reason**: implementation or acceptance awaiting reviewer
- **Bucket**: in_review
- **Parallel**: True (group pg-3-reviewer)
- **Expected**: C_REPORT with conclusion accepted|needs_changes|rejected
- **Commands**:
  - `Open Reviewer chat; read 04_Workflows/tickets/W2-REF-001_state.md; write C_REPORT`

### W2-T1 → scribe
- **Reason**: done ticket pending scribe progress append
- **Bucket**: done
- **Parallel**: True (group pg-1-scribe)
- **Expected**: D_REPORT + suggested Progress entry
- **Commands**:
  - `python 04_Workflows/_ops_cycle.py append-report --dry-run  # after D_REPORT`
  - `Open Scribe chat; read 04_Workflows/tickets/W2-T1_state.md; write D_REPORT + Progress append`
  - `python 04_Workflows/_core_agent_smoke.py --tier PR`

### W2-T3 → implementer
- **Reason**: draft ticket assigned to implementer
- **Bucket**: draft
- **Parallel**: False
- **Expected**: B_REPORT updated; STATE overall_status in_progress
- **Commands**:
  - `Open Implementer chat; read 04_Workflows/tickets/W2-T3_state.md; execute next_action`
  - `python -m unittest tests.test_dispatch_guide_scenarios -v`

### W2-T4 → implementer
- **Reason**: draft ticket assigned to implementer
- **Bucket**: draft
- **Parallel**: False
- **Expected**: B_REPORT updated; STATE overall_status in_progress
- **Commands**:
  - `Open Implementer chat; read 04_Workflows/tickets/W2-T4_state.md; execute next_action`
  - `python 04_Workflows/_wave7_regression_gate.py --tier A`

### W3-T2 → implementer
- **Reason**: draft ticket assigned to implementer
- **Bucket**: draft
- **Parallel**: False
- **Expected**: B_REPORT updated; STATE overall_status in_progress
- **Commands**:
  - `Open Implementer chat; read 04_Workflows/tickets/W3-T2_state.md; execute next_action`
  - `python -m unittest tests.test_tool_selector tests.test_tool_decision_log -v`

### W4-T1 → scribe
- **Reason**: done ticket pending scribe progress append
- **Bucket**: done
- **Parallel**: True (group pg-1-scribe)
- **Expected**: D_REPORT + suggested Progress entry
- **Commands**:
  - `python 04_Workflows/_ops_cycle.py append-report --dry-run  # after D_REPORT`
  - `Open Scribe chat; read 04_Workflows/tickets/W4-T1-routing-to-tabular-glue_state.md; write D_REPORT + Progress append`
  - `python -m unittest tests.test_routing_tabular_glue -v`

### W4-T2 → scribe
- **Reason**: done ticket pending scribe progress append
- **Bucket**: done
- **Parallel**: True (group pg-1-scribe)
- **Expected**: D_REPORT + suggested Progress entry
- **Commands**:
  - `python 04_Workflows/_ops_cycle.py append-report --dry-run  # after D_REPORT`
  - `Open Scribe chat; read 04_Workflows/tickets/W4-T2-routing-eval-runner_state.md; write D_REPORT + Progress append`
  - `python scripts/run_routing_eval.py --dry-run --format json`

### W4-T2 → implementer
- **Reason**: draft ticket assigned to implementer
- **Bucket**: draft
- **Parallel**: False
- **Expected**: B_REPORT updated; STATE overall_status in_progress
- **Commands**:
  - `Open Implementer chat; read 04_Workflows/tickets/W4-T2_state.md; execute next_action`
  - `python 04_Workflows/_wave8_submit_clean_job.py ...`

### W4-T3-A → scribe
- **Reason**: done ticket pending scribe progress append
- **Bucket**: done
- **Parallel**: True (group pg-1-scribe)
- **Expected**: D_REPORT + suggested Progress entry
- **Commands**:
  - `python 04_Workflows/_ops_cycle.py append-report --dry-run  # after D_REPORT`
  - `Open Scribe chat; read 04_Workflows/tickets/W4-T3-intake-tabular-tool-path_state.md; write D_REPORT + Progress append`
  - `python -m unittest tests.test_tabular_intake_tool_path -v`

### W4-T4 → implementer
- **Reason**: current_owner is implementer
- **Bucket**: runnable_now
- **Parallel**: True (group pg-2-implementer)
- **Expected**: B_REPORT updated; STATE overall_status in_progress
- **Commands**:
  - `Open Implementer chat; read 04_Workflows/tickets/W4-T4-routing-ci-hooks_state.md; execute next_action`
  - `python -m unittest tests.test_routing_eval_runner -v`

### W5-T2-hitl-checkpoints-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W5-T2-hitl-checkpoints-v1_state.md; update STATE`

### W6-T1-skill-card-and-skill-map-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W6-T1-skill-card-and-skill-map-v1_state.md; update STATE`

### W6-T10 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W6-T10-client-notification-gateway-v1_state.md; update STATE`

### W6-T10 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W6-T10-orchestrator-checkpoint-wiring-v1_state.md; update STATE`

### W6-T11 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W6-T11-checkpoint-resume-orchestrator-loop-v1_state.md; update STATE`

### W6-T3-agent-run-standard-case-experiment-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W6-T3-agent-run-standard-case-experiment-v1_state.md; update STATE`

### W6-T4-agent-run-standard-case-orchestrator-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W6-T4-agent-run-standard-case-orchestrator-v1_state.md; update STATE`

### W6-T5-integrate-checkpoint-a-intake-confirmation → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W6-T5-integrate-checkpoint-a-intake-confirmation_state.md; update STATE`

### W6-T7-experiment-eval-and-replay-guide-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W6-T7-experiment-eval-and-replay-guide-v1_state.md; update STATE`

### W6-T8-agent-standard-case-experiment-regression-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W6-T8-agent-standard-case-experiment-regression-v1_state.md; update STATE`

### W6-T9-agent-standard-line-governance-view-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W6-T9-agent-standard-line-governance-view-v1_state.md; update STATE`

### W7-T1-extend-agent-standard-line-more-fixtures → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W7-T1-extend-agent-standard-line-more-fixtures_state.md; update STATE`

### W7-T2-increase-agent-run-mode-coverage-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W7-T2-increase-agent-run-mode-coverage-v1_state.md; update STATE`

### W8-T1-extend-run-path-profiles-for-experimental-fixtures-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W8-T1-extend-run-path-profiles-for-experimental-fixtures-v1_state.md; update STATE`

### W8-T4 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W8-T4-non-tabular-shadow-flow-blueprint-v1_state.md; update STATE`

### W9-NT-CONTROLLED-WALKTHROUGH-V1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。
> Wave：Wave 9 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W9-NT-CONTROLLED-WALKTHROUGH-V1_state.md; update STATE`

### W9-T1-non-tabular-routing-catalog-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W9-T1-non-tabular-routing-catalog-v1_state.md; update STATE`

### W9-T3 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W9-T3-non-tabular-tool-catalog-and-selector-stub-v1_state.md; update STATE`

### W9-T4 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W9-T4-non-tabular-orchestrator-preview-v1_state.md; update STATE`

### W9-T5 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W9-T5-non-tabular-fixture-docu-corp-v1_state.md; update STATE`

### W9-T6 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/W9-T6-non-tabular-fixture-log-analytics-co-v1_state.md; update STATE`

### WA-T1 → reviewer
- **Reason**: implementation or acceptance awaiting reviewer
- **Bucket**: in_review
- **Parallel**: True (group pg-3-reviewer)
- **Expected**: C_REPORT with conclusion accepted|needs_changes|rejected
- **Commands**:
  - `Open Reviewer chat; read 04_Workflows/tickets/WA-T1-phase2-knowledge-indexing-contract-v1_state.md; write C_REPORT`

### WA-T3 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WA-T3-phase3-5-cost-model-governance-contract-v1_state.md; update STATE`

### WA-T4 → implementer
- **Reason**: in_progress with implement/resume/wire/test next_action
- **Bucket**: runnable_now
- **Parallel**: True (group pg-2-implementer)
- **Expected**: B_REPORT updated; STATE overall_status in_progress
- **Commands**:
  - `Open Implementer chat; read 04_Workflows/tickets/WA-T4-phase4-multi-agent-collaboration-contract-v1_state.md; execute next_action`
  - `python -m unittest tests.test_phase4_multi_agent_contract_v1 -v`

### WA-T6 → implementer
- **Reason**: in_progress with implement/resume/wire/test next_action
- **Bucket**: runnable_now
- **Parallel**: True (group pg-2-implementer)
- **Expected**: B_REPORT updated; STATE overall_status in_progress
- **Commands**:
  - `Open Implementer chat; read 04_Workflows/tickets/WA-T6-phase6-int-regression-gate-runbook-and-ci-integration-v1_state.md; execute next_action`

### WB-T8 → scribe
- **Reason**: done ticket pending scribe progress append
- **Bucket**: done
- **Parallel**: True (group pg-1-scribe)
- **Expected**: D_REPORT + suggested Progress entry
- **Commands**:
  - `python 04_Workflows/_ops_cycle.py append-report --dry-run  # after D_REPORT`
  - `Open Scribe chat; read 04_Workflows/tickets/WB-T8-toolchain-wave-b-review-and-progress-closure-v1_state.md; write D_REPORT + Progress append`

### WC-C1-01 → scribe
- **Reason**: done ticket pending scribe progress append
- **Bucket**: done
- **Parallel**: True (group pg-1-scribe)
- **Expected**: D_REPORT + suggested Progress entry
- **Commands**:
  - `python 04_Workflows/_ops_cycle.py append-report --dry-run  # after D_REPORT`
  - `Open Scribe chat; read 04_Workflows/tickets/WC-C1-01-toolchain-local-gaps-quickview-v1_state.md; write D_REPORT + Progress append`

### WC-L2-CI-DESIGN → orchestrator
- **Reason**: current_owner is orchestrator
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WC-L2-CI-DESIGN_state.md; update STATE`

### WC-PRE-07 → orchestrator
- **Reason**: current_owner is orchestrator
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WC-PRE-07_state.md; update STATE`

### WD-DOC-BREPORT-backfill-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WD-DOC-BREPORT-backfill-v1_state.md; update STATE`

### WD-P7-T1-orchestrator-gate-bundle-notify-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WD-P7-T1-orchestrator-gate-bundle-notify-v1_state.md; update STATE`

### WD-P7-T2-webhook-sandbox-dispatch-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WD-P7-T2-webhook-sandbox-dispatch-v1_state.md; update STATE`

### WD-P7-T3-orchestrator-dispatch-full-smoke-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WD-P7-T3-orchestrator-dispatch-full-smoke-v1_state.md; update STATE`

### WD-P85-T1-bridge-browser-fixture-smoke-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WD-P85-T1-bridge-browser-fixture-smoke-v1_state.md; update STATE`

### WD-P85-T2-bridge-runbook-index-closure-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WD-P85-T2-bridge-runbook-index-closure-v1_state.md; update STATE`

### WD-P85-T3-bridge-index-test-count-closure-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WD-P85-T3-bridge-index-test-count-closure-v1_state.md; update STATE`

### WD-P85-T4-bridge-negative-plan-fixture-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WD-P85-T4-bridge-negative-plan-fixture-v1_state.md; update STATE`

### WD-P9-T1-wc-m2-order-demo-e2e-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WD-P9-T1-wc-m2-order-demo-e2e-v1_state.md; update STATE`

### WD-P9-T2-wc-m2-hitl-fixture-automation-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WD-P9-T2-wc-m2-hitl-fixture-automation-v1_state.md; update STATE`

### WD-WG-SCRIBE-REVIEW-closure-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WD-WG-SCRIBE-REVIEW-closure-v1_state.md; update STATE`

### WH-H1-VALIDATION-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-H1-VALIDATION-v1_state.md; update STATE`

### WH-H1-VALIDATION-wrapup-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-H1-VALIDATION-wrapup-v1_state.md; update STATE`

### WH-P7-NOTIF-contract-doc-sync-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-NOTIF-contract-doc-sync-v1_state.md; update STATE`

### WH-P7-NOTIF-contract-partials-validation-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-NOTIF-contract-partials-validation-v1_state.md; update STATE`

### WH-P7-NOTIF-DLQ-impl-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-NOTIF-DLQ-impl-v1_state.md; update STATE`

### WH-P7-NOTIF-DLQ-inspect-cli-impl-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-NOTIF-DLQ-inspect-cli-impl-v1_state.md; update STATE`

### WH-P7-NOTIF-DLQ-inspect-cli-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-NOTIF-DLQ-inspect-cli-v1_state.md; update STATE`

### WH-P7-NOTIF-DLQ-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-NOTIF-DLQ-v1_state.md; update STATE`

### WH-P7-NOTIF-HMAC-impl-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-NOTIF-HMAC-impl-v1_state.md; update STATE`

### WH-P7-NOTIF-HMAC-policy-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-NOTIF-HMAC-policy-v1_state.md; update STATE`

### WH-P7-NOTIF-HMAC-prod-impl-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-NOTIF-HMAC-prod-impl-v1_state.md; update STATE`

### WH-P7-NOTIF-HMAC-prod-mandatory-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-NOTIF-HMAC-prod-mandatory-v1_state.md; update STATE`

### WH-P7-NOTIF-HMAC-receiver-contract-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-NOTIF-HMAC-receiver-contract-v1_state.md; update STATE`

### WH-P7-NOTIF-HMAC-receiver-fixtures-impl-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-NOTIF-HMAC-receiver-fixtures-impl-v1_state.md; update STATE`

### WH-P7-NOTIF-PROD-policy-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-NOTIF-PROD-policy-v1_state.md; update STATE`

### WH-P7-NOTIF-PROD-URL-impl-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-NOTIF-PROD-URL-impl-v1_state.md; update STATE`

### WH-P7-NOTIF-PROD-URL-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-NOTIF-PROD-URL-v1_state.md; update STATE`

### WH-P7-NOTIF-RETRY-prod-impl-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-NOTIF-RETRY-prod-impl-v1_state.md; update STATE`

### WH-P7-NOTIF-RETRY-prod-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-NOTIF-RETRY-prod-v1_state.md; update STATE`

### WH-P7-NOTIF-RETRY-SANDBOX-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-NOTIF-RETRY-SANDBOX-v1_state.md; update STATE`

### WH-P7-NOTIF-staging-integration-execute-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-NOTIF-staging-integration-execute-v1_state.md; update STATE`

### WH-P7-PROD-phase1-wrapup-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-PROD-phase1-wrapup-v1_state.md; update STATE`

### WH-P7-PROD-prod-rollout-governance-bootstrap-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-PROD-prod-rollout-governance-bootstrap-v1_state.md; update STATE`

### WH-P7-PROD-RETRY-HMAC-microplan-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-PROD-RETRY-HMAC-microplan-v1_state.md; update STATE`

### WH-P7-PROD-roadmap-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-PROD-roadmap-v1_state.md; update STATE`

### WH-P7-PROD-staging-env-bootstrap-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-PROD-staging-env-bootstrap-v1_state.md; update STATE`

### WH-P7-PROD-staging-env-config-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-PROD-staging-env-config-v1_state.md; update STATE`

### WH-P7-PROD-staging-integration-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-PROD-staging-integration-v1_state.md; update STATE`

### WH-P7-PROD-staging-smoke-runbook-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-PROD-staging-smoke-runbook-v1_state.md; update STATE`

### WH-P7-sandbox-line-wrapup-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P7-sandbox-line-wrapup-v1_state.md; update STATE`

### WH-P85-bridge-fixture-dom-port-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P85-bridge-fixture-dom-port-v1_state.md; update STATE`

### WH-P85-bridge-run-record-jsonl-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P85-bridge-run-record-jsonl-v1_state.md; update STATE`

### WH-P85-CI-LAND-bridge-smoke-push-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P85-CI-LAND-bridge-smoke-push-v1_state.md; update STATE`

### WH-P85-CI-LAND-doc-sync-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P85-CI-LAND-doc-sync-v1_state.md; update STATE`

### WH-P85-CI-LAND-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P85-CI-LAND-v1_state.md; update STATE`

### WH-P85-SMOKE-B-advisory-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P85-SMOKE-B-advisory-v1_state.md; update STATE`

### WH-P85-SMOKE-B-scenario2-ops-run-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P85-SMOKE-B-scenario2-ops-run-v1_state.md; update STATE`

### WH-P85-SMOKE-B-scenario2-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P85-SMOKE-B-scenario2-v1_state.md; update STATE`

### WH-P85-wave-H2-closure-scribe-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P85-wave-H2-closure-scribe-v1_state.md; update STATE`

### WH-P85-wave-H2-entry-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P85-wave-H2-entry-v1_state.md; update STATE`

### WH-P9-CI-payment-sandbox-smoke-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P9-CI-payment-sandbox-smoke-v1_state.md; update STATE`

### WH-P9-M2-INT-alignment-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P9-M2-INT-alignment-v1_state.md; update STATE`

### WH-P9-M2-runner-step6-payment-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P9-M2-runner-step6-payment-v1_state.md; update STATE`

### WH-P9-PROD-order-status-transition-impl-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P9-PROD-order-status-transition-impl-v1_state.md; update STATE`

### WH-P9-PROD-payment-closure-bootstrap-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P9-PROD-payment-closure-bootstrap-v1_state.md; update STATE`

### WH-P9-PROD-payment-happy-path-execute-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P9-PROD-payment-happy-path-execute-v1_state.md; update STATE`

### WH-P9-PROD-payment-sandbox-adapter-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P9-PROD-payment-sandbox-adapter-v1_state.md; update STATE`

### WH-P9-PROD-real-provider-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P9-PROD-real-provider-v1_state.md; update STATE`

### WH-P9-WC-T7-runbook-payment-section-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-P9-WC-T7-runbook-payment-section-v1_state.md; update STATE`

### WH-REV-2026-06-P7-P8_5-P9-alignment-checklist-v1 → orchestrator
- **Reason**: fallback to orchestrator triage
- **Bucket**: runnable_now
- **Parallel**: True
- **Expected**: FRAME/STATE updated; ticket routed to next role
- **Commands**:
  - `Open Orchestrator chat; read 04_Workflows/tickets/WH-REV-2026-06-P7-P8_5-P9-alignment-checklist-v1_state.md; update STATE`

## Coordination notes

- workflow_v2 run_queue has 17 TODO rows (heuristic parse)
- 127 tickets runnable_now; check parallel_groups before opening chats
- 4 tickets in_review — prioritize Reviewer chats
- 17 done tickets suggest Scribe progress append

---
*Heuristic markdown parser · suggestion only · no auto-dispatch*