# TAB-AUTO-MANIFEST-v1 — Tabular Cleaning Automation Manifest

> **Status**: done (doc-only)  
> **Date**: 2026-06-27  
> **Deliverable**: `docs/tabular-cleaning-automation-manifest-v1.md`

## Scope

- Automation manifest: allowed/forbidden mutations, start/stop, HITL, output schema, retry, non-claims
- Near-full-auto runbook R1–R6 + CP-A/B skip rules
- Script mapping table vs repo entrypoints
- Gap triage A/B/C + top-5 critical path

## Out of scope (explicit)

- workflow yml / branch protection / Dashboard / governance Batch 1
- gate / Phase% / prod / closure claims

## Next (B-track, not this ticket)

1. A1 `automation_state.json` template
2. B1 `scripts/run_tabular_automation.py`
3. B5 CP resume wired to main chain
4. B3 `approve_delivery.py`
5. B7 cleaning profile abstraction

## Verification

- Doc cross-ref: `docs/TABULAR_MVP_SSOT.md` §9
- Main chain unchanged: `run_case_e2e_validation.py` · `run_mvp_mainline_regression.py`
