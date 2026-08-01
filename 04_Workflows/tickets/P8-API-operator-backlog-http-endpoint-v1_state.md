# P8-API — Operator backlog HTTP endpoint v1

> **Ticket**: P8-API-operator-backlog-http-endpoint-v1  
> **Status**: implemented (2026-06-19)  
> **Scope**: Read-only HTTP GET for `operator_backlog_v1` read model; no mutation; sandbox/dev only

## Deliverables

| Path | Action |
|------|--------|
| `scripts/operator_http_api_v1.py` | created |
| `tests/test_operator_http_api_v1.py` | created |
| `docs/phase-8-operator-backlog-v1.md` | HTTP API v1 section |
| `04_Workflows/WORKFLOW_INDEX.md` | HTTP API entry |
| `docs/WAVE_PROGRESS_DASHBOARD.md` | Phase 8 HTTP mention |

## Endpoints

| Method | Path | Query | Response |
|--------|------|-------|----------|
| GET | `/operator/backlog` | `status` (optional: pending\|blocked\|completed), `case_ref` (optional) | `operator_backlog_v1` JSON |
| GET | `/health` | — | `{"ok": true, "service": "operator_http_api_v1", "read_only": true}` |

Invalid `status` → `400` + `{"error": "invalid status"}`.

## Verification

```bash
python -m unittest tests.test_operator_http_api_v1 -v

python scripts/operator_http_api_v1.py --port 8080
curl 'http://127.0.0.1:8080/operator/backlog?status=pending'
```

## Out of scope

- Production hardening (auth, TLS, rate limits)
- Mutation endpoints (approve, resume, gate run)
- Changes to `list_operator_backlog_v1.py` classification logic

---

## Wave Master schema append（W3-P89-SSOT · 2026-07-10 · 末尾追加 · 不刪歷史）

```yaml
overall_status: done
lifecycle_phase: O
wave_id: W3
phase_targets: [P8]
implementation_status: implemented · review_closed_historical
deferred_items:
  - Production hardening（auth · TLS · rate limits）
  - Mutation endpoints（approve · resume · gate run）
observability:
  verify_commands:
    - "python -m unittest tests.test_operator_http_api_v1 -v"
    - "python scripts/operator_http_api_v1.py --port 8080"
    - "curl 'http://127.0.0.1:8080/operator/backlog?status=pending'"
  contract_ref: docs/p8_p89_delivery_observability_contract_v1.md
  evidence_index_ref: docs/p8_p89_evidence_index_v1.md
  evidence_tier: L-local
non_claims:
  - sandbox/dev HTTP ≠ prod API / auth
  - GET backlog ≠ mutation / approve path
  - L-local green ≠ GA pass / Phase% 上調
alignment_ticket: W3-P89-SSOT-state-dashboard-alignment-v1
```

## cross_refs / notes append（W3-P8-BRG · 2026-07-10 · 末尾追加）

```yaml
cross_refs:
  - ticket: W3-P8-BRG-bridge-advisory-crossref-v1
  - runbook: docs/phase8_5-bridge-smoke-runbook-v1.md
  - operator_doc: docs/phase-8-operator-backlog-v1.md#Bridge-advisory
notes: >-
  Bridge advisory cross-ref only · HTTP backlog endpoint 不依賴 bridge smoke ·
  ≠ Phase 8 release gate。本票 deliverables 不變。
```

