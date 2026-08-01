# MP-METRICS — Standard-case metrics exporter v1

> **Ticket**: MP-METRICS-std-case-metrics-exporter-v1  
> **Status**: implemented (2026-06-19)  
> **Scope**: Read-only per-case metrics export for P7.5 / P8.9 / Phase 8 operator views

## Deliverables

| Path | Action |
|------|--------|
| `scripts/export_std_case_metrics_v1.py` | created |
| `tests/test_export_std_case_metrics_v1.py` | created |
| `04_Workflows/WORKFLOW_INDEX.md` | metrics entry |
| `docs/WAVE_PROGRESS_DASHBOARD.md` | brief MP-METRICS row |

## Metrics (`std_case_metrics_v1`)

| Field | Definition |
|-------|------------|
| `pending_cases_count` | 1 when operator backlog status is `pending`, else 0 (per-case v1) |
| `blocked_cases_count` | 1 when status is `blocked`, else 0 |
| `completed_cases_count` | 1 when status is `completed`, else 0 |
| `notifications_emitted_count` | Notification stream rows in workflow consumer |
| `notifications_with_pending_ack_count` | Notifications with `tracking_status=pending_ack` |
| `notifications_failed_ack_count` | Notifications with `tracking_status=failed` |

## Verification

```bash
python -m unittest tests.test_export_std_case_metrics_v1.py -v
python scripts/export_std_case_metrics_v1.py --case-ref demo_phase --format json
python scripts/export_std_case_metrics_v1.py --case-ref demo_phase --format text
```

## Notes

- Read-only; no gateway emit, gate, CP-A, rules, or policy changes.
- Data sources: `build_backlog_entry`, `load_workflow_events`, `ingest_pending_events`.
- Future: aggregate across cases, scrape endpoint, histograms for latency.
