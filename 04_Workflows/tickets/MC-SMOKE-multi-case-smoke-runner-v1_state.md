# MC-SMOKE — Multi-case smoke runner v1

> **Status**: implemented  
> **Role**: Implementer  
> **Scope**: Orchestrate MP-SMOKE across representative cases — no changes to underlying smoke / gate / metrics schema

## changed_files

### Added

- `scripts/run_multi_case_smoke_v1.py` — multi-case orchestrator over `run_multi_phase_smoke_v1`
- `tests/test_multi_case_smoke_v1.py` — summary coverage + top-level ok aggregation tests
- `04_Workflows/tickets/MC-SMOKE-multi-case-smoke-runner-v1_state.md` — this file

### Modified

- `04_Workflows/WORKFLOW_INDEX.md` — multi-case smoke runner index entry
- `docs/WAVE_PROGRESS_DASHBOARD.md` — one-line multi-case smoke runner note

## representative cases (built-in)

| case_ref | task_type | label |
|----------|-----------|-------|
| `demo_phase` | `tabular.cleaning.mvp` | standard cleaning (primary run lab → bundle) |
| `sampleco/2026-0001` | `tabular.cleaning.mvp` | controlled profile (stop at Checkpoint B) |
| `phi_demo` | `tabular.intake.new_case` | policy deny path (PHI sensitivity → gate reject) |

`phi_demo` uses ephemeral synthetic intake (no persistent `cases/phi_demo` fixture); expected to fail downstream smoke steps after gate reject.

## verification

```bash
python -m unittest tests.test_multi_case_smoke_v1 -v

python scripts/run_multi_case_smoke_v1.py --format json
python scripts/run_multi_case_smoke_v1.py --cases demo_phase,sampleco --format text
```

## notes

- Summary artifact (optional): `outbox/verification/multi_case_smoke_run.json`
- Per-case smoke summaries are **not** written (MP-SMOKE `write_summary=False` during orchestration)
- Release sanity for passing paths: `--cases demo_phase,sampleco` (exclude `phi_demo` deny probe)
