# MP-SMOKE — Standard-case multi-phase smoke runner v1

> **Status**: implemented  
> **Role**: Implementer  
> **Scope**: Orchestrate P7.5 / P8 / P8.9 CLIs — no schema or core script behavior changes

## changed_files

### Added

- `scripts/run_multi_phase_smoke_v1.py` — seven-step multi-phase smoke orchestrator
- `tests/test_multi_phase_smoke_v1.py` — summary JSON + step coverage tests
- `04_Workflows/tickets/MP-SMOKE-std-case-multi-phase-smoke-v1_state.md` — this file

### Modified

- `04_Workflows/WORKFLOW_INDEX.md` — multi-phase smoke runner index entry
- `docs/WAVE_PROGRESS_DASHBOARD.md` — one-line multi-phase smoke runner v1 note

## steps (fixed order)

1. `gate_preview` — intake gate preview (no outbox write)
2. `gate_run_notify` — intake gate run + `intake.gate_decision` notification
3. `std_case_experiment` — `run_agent_standard_case_experiment` run + auto-approve intake
4. `workflow_events_inspect` — `load_workflow_events` read model
5. `feedback_ingest_dry_run` — pending scan only (dry-run)
6. `p89_verification_bundle` — collect bundle (`skip_experiment=True`)
7. `operator_backlog` — `list_operator_backlog` for case

## verification

```bash
python -m unittest tests.test_multi_phase_smoke_v1 -v

python scripts/run_multi_phase_smoke_v1.py \
  --case-ref demo_phase \
  --enable-dispatch \
  --format json
```

## notes

- Summary artifact: `outbox/verification/<case_slug>/multi_phase_smoke_run.json`
- P8.9 bundle step skips re-running experiment because step 3 already populated outbox
- `--enable-dispatch` sets `GOV_NOTIFICATION_DISPATCH_ENABLED=1` during experiment
