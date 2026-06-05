# Shadow run ??w4a-int-20260529-pilot

> **stream**: W4-A-INTERNAL-K2-STREAM-v1  
> **phase**: P1 shadow (fixture-backed)  
> **env**: staging-internal  
> **user-facing**: primary_source=ask (no prod switch)

## Summary

| Field | Value |
|-------|-------|
| release_id | `w4a-int-20260529-pilot` |
| started_at | 2026-05-29T19:08:55.4934619+08:00 |
| eval_ok | True |
| eval_message | CI check passed: needs_review 1/4 (25.00%), threshold 60.00% |
| export_lines | indexed under `artifacts/eval` in run dir |

## Commands (semantic)

1. `python -m observability.ibridge_exporter --source shadow --profile shadow --force <fixture> -o <run>/eval/shadow_ibridge_records.latest.jsonl --no-latest`
2. `python -m observability.eval_ci_check <export> --max-needs-review-ratio 0.6 --fail-on-tags infra_risk`

## Observation (O-S3 / O-S4)

- merge sidecar only; **does not** change ask user response.
- spool/export indexed in run directory; full ??d window still required for production promotion (W3-A-SHADOW-PILOT).

