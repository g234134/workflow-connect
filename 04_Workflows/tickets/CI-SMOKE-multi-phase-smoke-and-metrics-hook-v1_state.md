# CI-SMOKE — Multi-phase smoke & metrics CI hook v1

> **Status**: implemented  
> **Role**: Implementer  
> **Scope**: CI wrapper only — no changes to core smoke/metrics scripts

## changed_files

### Added

- `scripts/run_ci_smoke_check_v1.py` — single-case CI gate (smoke + metrics + pass/fail)
- `tests/test_ci_smoke_check_v1.py` — unit tests with mocked smoke/metrics
- `04_Workflows/tickets/CI-SMOKE-multi-phase-smoke-and-metrics-hook-v1_state.md` — this file

### Modified

- `04_Workflows/WORKFLOW_INDEX.md` — CI smoke check entry
- `docs/WAVE_PROGRESS_DASHBOARD.md` — CI usage line in release sanity block

## pass/fail rules

1. `multi_phase_smoke.ok == true`
2. `std_case_metrics.ok == true`
3. `std_case_metrics_v1.notifications_failed_ack_count == 0`

Any violation → exit code 1 + human-readable failure summary on stdout.

## verification

```bash
python -m unittest tests.test_ci_smoke_check_v1 -v
python scripts/run_ci_smoke_check_v1.py --format text
```

## notes

- Does not re-run experiment beyond what `run_multi_phase_smoke_v1` already does
- Single case only (default `demo_phase`); no multi-case batching
- Blocked: `run_multi_phase_smoke_v1.py`, `export_std_case_metrics_v1.py`, emit/CP-A/orchestrator logic
