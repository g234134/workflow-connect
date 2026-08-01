# MC-METRICS — Multi-case metrics aggregation v1

> **Ticket**: MC-METRICS-multi-case-metrics-aggregation-v1  
> **Status**: implemented (2026-06-19)  
> **Scope**: Fleet-level read-only rollup over per-case `std_case_metrics_v1`

## Deliverables

| Path | Action |
|------|--------|
| `scripts/aggregate_multi_case_metrics_v1.py` | created |
| `tests/test_aggregate_multi_case_metrics_v1.py` | created |
| `04_Workflows/WORKFLOW_INDEX.md` | multi-case aggregate entry |
| `docs/WAVE_PROGRESS_DASHBOARD.md` | metrics block note |

## Aggregated metrics (`multi_case_metrics_v1.metrics`)

| Field | Source (per-case sum) |
|-------|------------------------|
| `total_pending_cases` | `pending_cases_count` |
| `total_blocked_cases` | `blocked_cases_count` |
| `total_completed_cases` | `completed_cases_count` |
| `total_notifications_emitted` | `notifications_emitted_count` |
| `total_notifications_failed_ack` | `notifications_failed_ack_count` |
| `total_notifications_pending_ack` | `notifications_with_pending_ack_count` |

## Default case set

Representative fleet (A1 / MVP mainline): `demo_phase`, `sampleco/2026-0001`. Override with `--cases`.

## Verification

```bash
python -m unittest tests.test_aggregate_multi_case_metrics_v1.py -v
python scripts/aggregate_multi_case_metrics_v1.py --format json
python scripts/aggregate_multi_case_metrics_v1.py --cases demo_phase,sampleco/2026-0001 --format text
```

## Notes

- Read-only; does not change `std_case_metrics_v1` schema or HTTP endpoint output.
- Calls `export_std_case_metrics` library function per case (no CLI subprocess).
- `ok=false` when any per-case export fails; totals still computed from available rows.
