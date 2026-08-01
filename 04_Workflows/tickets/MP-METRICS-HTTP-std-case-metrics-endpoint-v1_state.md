# MP-METRICS-HTTP — Standard-case metrics HTTP endpoint v1

> **Ticket**: MP-METRICS-HTTP-std-case-metrics-endpoint-v1  
> **Status**: implemented (2026-06-19)  
> **Scope**: Expose `export_std_case_metrics_v1` via minimal `GET /metrics` for Prometheus / curl smoke

## Deliverables

| Path | Action |
|------|--------|
| `scripts/metrics_http_endpoint_v1.py` | created |
| `tests/test_metrics_http_endpoint_v1.py` | created |
| `scripts/export_std_case_metrics_v1.py` | expose `format_std_case_metrics_prometheus` (library render) |
| `04_Workflows/WORKFLOW_INDEX.md` | metrics HTTP entry |
| `docs/WAVE_PROGRESS_DASHBOARD.md` | `/metrics` endpoint note |

## Endpoint

| Route | Query | Response |
|-------|-------|----------|
| `GET /metrics` | `case_ref=<slug>` (optional, default `demo_phase`) | `text/plain` Prometheus exposition |
| `GET /health` | — | `application/json` service probe |

## Error policy

- **HTTP 200** always on `/metrics` (scrape-friendly).
- When exporter returns `ok: false`, body includes `# error: <message>` comment line; gauge values are zeroed.
- Unknown paths → **HTTP 404** with `# error: not_found`.

## Verification

```bash
python -m unittest tests.test_metrics_http_endpoint_v1 -v
python scripts/metrics_http_endpoint_v1.py --port 9090 &
curl 'http://localhost:9090/metrics?case_ref=demo_phase'
```

## Notes

- Reuses `export_std_case_metrics` + `format_std_case_metrics_prometheus`; no schema or gate changes.
- Skeleton aligned with `scripts/operator_http_api_v1.py` (P8-API).
- Future: multi-case scrape, auth, histograms — see exporter ticket notes.
