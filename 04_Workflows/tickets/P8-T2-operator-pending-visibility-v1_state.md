# P8-T2 — Operator pending visibility v1

> **Ticket**: P8-T2-operator-pending-visibility-v1  
> **Status**: implemented (2026-06-19)  
> **Scope**: Read-only operator backlog CLI (pending/blocked/completed); no Web UI; no batch approve / resume-latest (deferred)

## Deliverables

| Path | Action |
|------|--------|
| `scripts/list_operator_backlog_v1.py` | created |
| `tests/test_operator_backlog_v1.py` | created |
| `docs/phase-8-operator-backlog-v1.md` | created |
| `04_Workflows/plans/phase-8-commercial-delivery-to-80-plan.md` | P8-T2 v1 section |
| `docs/WAVE_PROGRESS_DASHBOARD.md` | Phase 8 P8-T2 row |
| `04_Workflows/WORKFLOW_INDEX.md` | operator backlog entry |
| `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md` | operator command |
| `docs/audit-quickview-and-case-history-spec-v1.md` | cross-ref |

## Deferred (full P8-T2 scope)

- `--resume-latest-approved` → **delivered in P8-T2b**（2026-07-13 · path resolution + fail-close）
- `--batch-approve` → **delivered in P8-T2b**（2026-07-13 · same task_type）
- checkpoint preview CLI → **delivered in P8-T2c**（2026-07-13 · `scripts/preview_checkpoint_v1.py`）

## Verification

```bash
python -m unittest tests.test_operator_backlog_v1 -v

python scripts/list_operator_backlog_v1.py --status pending --format json
python scripts/list_operator_backlog_v1.py --status blocked --format table
```

## Classification (summary)

| status | Rule |
|--------|------|
| `pending` | CP-A `awaiting_human`; or gate `review_needed` without resolved CP-A; or mid-run after CP-A resolved |
| `blocked` | Latest terminal `run.blocked`/`run.failed`; or CP-A `rejected`; or gate `reject` |
| `completed` | Latest terminal `run.completed` and CP-A not `awaiting_human` |

---

## Wave Master schema append（W3-P89-SSOT · 2026-07-10 · 末尾追加 · 不刪歷史）

```yaml
overall_status: done
lifecycle_phase: O
wave_id: W3
phase_targets: [P8]
implementation_status: implemented · review_closed_historical
deferred_items:
  - --resume-latest-approved
  - --batch-approve
  - checkpoint preview CLI
  - Web UI
observability:
  verify_commands:
    - "python -m unittest tests.test_operator_backlog_v1 -v"
    - "python scripts/list_operator_backlog_v1.py --status pending --format json"
    - "python scripts/run_multi_phase_smoke_v1.py --case-ref demo_phase --format json"
  contract_ref: docs/p8_p89_delivery_observability_contract_v1.md
  evidence_index_ref: docs/p8_p89_evidence_index_v1.md
  evidence_tier: L-local
non_claims:
  - backlog CLI v1 ≠ batch approve / resume-latest / Web UI
  - read-only visibility ≠ mutation / prod operator console
  - L-local green ≠ required CI / Phase% 上調
alignment_ticket: W3-P89-SSOT-state-dashboard-alignment-v1
```

## cross_refs / notes append（W3-P8-BRG · 2026-07-10 · 末尾追加）

```yaml
cross_refs:
  - ticket: W3-P8-BRG-bridge-advisory-crossref-v1
  - runbook: docs/phase8_5-bridge-smoke-runbook-v1.md
  - operator_doc: docs/phase-8-operator-backlog-v1.md#Bridge-advisory
notes: >-
  Bridge = optional advisory 側線（in-memory stub）· ≠ operator backlog 前置 ·
  ≠ Phase 8 release gate。本票 deliverables 不變。
```

