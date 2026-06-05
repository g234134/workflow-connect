# eval_gate export schema (`eval_export/v1`)

> **Producer**: `observability/eval_exporter.py`  
> **Consumer**: analytics, dashboards, CI (`observability/eval_ci_check.py`)  
> **Gate logic**: `observability/eval_gate.evaluate_task_record` (unchanged)

Each JSONL line is one eval export row. The full `ibridge_record` / `metrics_record` is **not** stored—only identifiers, gate outcome, tags, and a compact `metrics` summary.

---

## Line object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string | yes | `"eval_export/v1"` |
| `trace_id` | string \| null | yes | From record `trace_id` |
| `task_id` | string \| null | yes | From record `task_id` |
| `timestamp` | string \| null | yes | `end_time`, else `start_time` / `timestamp` |
| `exported_at` | string | yes | ISO 8601 UTC when the line was produced |
| `gate_result` | string | yes | `"pass"` or `"needs_review"` |
| `tags` | string[] | yes | Machine tags from eval_gate |
| `reasons` | string[] | yes | Human-readable reasons (aligned with tags) |
| `metrics` | object | yes | Gate-relevant field subset (see below) |
| `source_ref` | object | no | `{ task_id?, trace_id?, line_index? }` for traceability |

### `source_ref.line_index` (semantics and limits)

`line_index` is the **1-based line number in the exporter input JSONL** (typically `ibridge_records.jsonl` or an equivalent intermediate format), **not** the line number in the eval export output file. It is optional metadata for manual traceability only; gate logic, CI, and stats **do not** read or assert on it.

| Layer | What `line_index` points to |
|-------|----------------------------|
| Unit-test fixtures (`tests/fixtures/eval/`) | Line in `ibridge_records.jsonl` for the same `task_id` / `trace_id` |
| Smoke artifacts (`artifacts/eval/smoke_eval_results.jsonl`) | Line in `tests/fixtures/eval/ibridge_records.jsonl` (shared `task_id` / `trace_id`); **not** the smoke export line number and **not** `artifacts/eval/smoke_ibridge_records.jsonl` row order (that file reorders rows for pipeline smoke) |
| Shadow artifacts (`artifacts/eval/shadow_eval_results.latest.jsonl`) | Line in the **ibridge intermediate** input (e.g. `shadow_raw_records.jsonl` after export), **not** a guaranteed 1:1 map to raw K-2 spool rows |

**Smoke fixture notes:** `smoke_eval_results.jsonl` is composite illustrative data (same three tasks as unit fixtures, export row order differs from `ibridge_records.jsonl`). `source_ref.line_index` values were **manually corrected in fixtures** to the canonical `ibridge_records.jsonl` 1-based lines; gate/CI/stats ignore this field. Do not infer a unique raw K-2 or prod spool row from smoke `line_index` alone.

**Known limits:** fixture rows are illustrative; most production exports do not guarantee 100% alignment when input is reordered, filtered, or wrapped (`ibridge_record`, `k2_summary`, etc.). Shadow provenance stops at the intermediate format—do not assume `line_index` reaches raw source spool line numbers without verifying the upstream export profile.

### `gate_result`

| Value | Meaning |
|-------|---------|
| `pass` | `evaluate_task_record` returned `pass: true` |
| `needs_review` | At least one review tag fired |

### `metrics`

| Field | Type | Description |
|-------|------|-------------|
| `success` | bool \| null | Business outcome |
| `retry_count` | int | Retries after initial attempt |
| `handoff_count` | int | Agent handoffs |
| `error_type` | string \| null | Primary failure category |
| `context_tokens_total` | int | `context_token_usage.total_tokens` |
| `trace_completeness_score` | float \| null | `trace_completeness.score` |
| `agent_name` | string | optional |
| `step_count` | int | optional |

---

## Example line

```json
{
  "schema_version": "eval_export/v1",
  "trace_id": "trace-xyz",
  "task_id": "t-abc",
  "timestamp": "2026-05-23T12:00:00Z",
  "exported_at": "2026-05-23T12:05:00Z",
  "gate_result": "needs_review",
  "tags": ["high_retry"],
  "reasons": ["retry_count=2 >= 2"],
  "metrics": {
    "success": true,
    "retry_count": 2,
    "handoff_count": 0,
    "error_type": null,
    "context_tokens_total": 1000,
    "trace_completeness_score": 0.95
  },
  "source_ref": {
    "task_id": "t-abc",
    "trace_id": "trace-xyz",
    "line_index": 3
  }
}
```

---

## CLI

```bash
python -m observability.eval_exporter path/to/records.jsonl -o eval_results.jsonl
python -m observability.eval_exporter path/to/dir -o out.jsonl --filter needs_review
```

Input may be `.json`, `.jsonl`, or a directory (recursive `*.json` / `*.jsonl`). Lines may wrap the record as `ibridge_record`, `record`, or `metrics_record`.

## CI

```bash
python -m observability.eval_ci_check path/to/records.jsonl --limit 50 --max-needs-review-ratio 0.4
python -m observability.eval_ci_check path/to/records.jsonl --fail-on-tags infra_risk,observability_gap
```

Exit code `0` = within thresholds; non-zero = pipeline signal (ratio, `fail_on_tags`, or insufficient samples).
