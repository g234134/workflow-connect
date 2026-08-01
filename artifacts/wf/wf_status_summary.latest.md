# WF status summary (Gate / Index / Trace)

> Generated: `2026-06-07T07:49:23Z`

## 1. Gate health

- **Samples (N)**: 3
- **needs_review**: 2 (66.7%)
- **Confidence**: high

### Top tags

| Tag | Count |
|-----|-------|
| `high_retry` | 1 |
| `infra_risk` | 1 |

## 2. Index readiness

| case_id | kb_index_status | job_id | file_count | chunk_count | last_updated |
|---------|-----------------|--------|------------|-------------|--------------|
| W2-1 | ready | repo_index_v1_job__W2-1__wave_b_gov_scope | 190 | 1204 | 2026-06-05T08:47:16Z |

## 3. Trace join (flagged rows)

- **Status**: ok
- **Flagged rows**: 2
- **Trace hits**: 1
- **Hit rate**: 50.0%

## Reviewer shortcuts

```bash
python -m observability.eval_trace_correlate --eval tests/fixtures/eval/eval_export_sample.jsonl --trace tests/fixtures/trace/sample_traces.jsonl --format markdown
python -m observability.trace_query --file tests/fixtures/trace/sample_traces.jsonl --trace-id <id> --format json
```
