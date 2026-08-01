# W5-D-ARTEFACT-SPEC-01 — Eval / Dryrun / ENF Artefact Schema Specification

> **Status:** Read-only survey (只讀＋文件)
> **Scope:** All eval gate, dry-run, enforcement preview, and governance gate artifacts.
> **Hard boundary:** No code/CI modifications. Unstable fields marked **⚠ 暫定**.

---

## 1. Artefact Overview

| # | Artefact Type | Format | Location | Producer |
|---|--------------|--------|----------|----------|
| **T1** | eval_export/v1 | JSONL (per-line) | `artifacts/eval/smoke_eval_results.jsonl`, `shadow_eval_results.latest.jsonl` | `observability/eval_exporter.py` (manual only — never called in CI) |
| **T2** | ibridge records | JSONL (per-line) | `artifacts/eval/ibridge_records.latest.jsonl`, `smoke_ibridge_records.jsonl`, `tests/fixtures/eval/ibridge_records.jsonl` | `observability/ibridge_exporter.py` (CI: eval-shadow-nightly) |
| **T3** | shadow ibridge records | JSONL (per-line) | `artifacts/eval/shadow_ibridge_records.latest.jsonl`, `_ac2_shadow_ibridge.jsonl` | `ibridge_exporter.py` `source="shadow"` |
| **T4** | K-2 shadow spool (raw) | JSONL (per-line, mixed format) | `artifacts/eval/k2_shadow_spool.jsonl` | K-2 prod-shadow pipeline (manual upload) |
| **T5** | shadow batch | JSONL (per-line, mixed format) | `artifacts/eval/shadow_batch_YYYYMMDD.jsonl` | Manual export from prod K-2 |
| **T6** | dryrun per_record | JSONL (per-line) | `observability/dryrun/<stamp>_per_record.jsonl`, `artifacts/eval/_dryrun_*/*.jsonl` | `tools.dryrun.core` via `tools.dryrun.__main__` |
| **T7** | dryrun summary | Markdown | `observability/dryrun/<stamp>_summary.md` | `tools.dryrun.output.write_summary_markdown()` |
| **T8** | `[DRYRUN-LOG]` structured log | Text (space-separated key=value) | CI stdout (not persisted as file) | `tools/dryrun_ci_wrapper.py` |
| **T9** | `[GOV-ENF-PREVIEW]` structured log | Text (space-separated key=value) | CI stdout (not persisted as file) | `tools/enf_preview_wrapper.py` |
| **T10** | gov gate metrics | JSONL (per-line, BOM-prefixed) | `workflow_v2/observability/gov_gate_metrics/local.jsonl` | `wf_gov_gate.ps1` / `wf_check_cross_ref.ps1` |
| **T11** | eval_export schema definition | JSON Schema | `observability/eval_export_schema.json` | Manual |

---

## 2. Detailed Field Specifications

### T1. eval_export/v1 JSONL (`schema_version: "eval_export/v1"`)

| Field | Type | Required | Semantics | Example |
|-------|------|----------|-----------|---------|
| `schema_version` | `string` | ✅ | Literal `"eval_export/v1"` | `"eval_export/v1"` |
| `trace_id` | `string` \| `null` | ❌ | Unique trace identifier | `"tr-3"` |
| `task_id` | `string` \| `null` | ❌ | Task/case identifier | `"t-infra"` |
| `timestamp` | `string` \| `null` | ❌ | ISO 8601 UTC (from record end_time, start_time, or timestamp) | `"2026-05-23T10:02:00Z"` |
| `exported_at` | `string` | ✅ | ISO 8601 UTC when export line was built | `"2026-05-23T09:42:04Z"` |
| `gate_result` | `string` | ✅ | Enum: `"pass"` \| `"needs_review"` | `"needs_review"` |
| `tags` | `string[]` | ✅ | Risk/quality tags | `["infra_risk"]` |
| `reasons` | `string[]` | ✅ | Human-readable reason strings | `["error_type=timeout"]` |
| `metrics` | `object` | ✅ | Numeric metrics sub-object (see below) | — |
| `source_ref` | `object` \| `null` | ❌ | Traceability to source record (see below) | — |

**`metrics` sub-object:**

| Field | Type | Required | Semantics | Example |
|-------|------|----------|-----------|---------|
| `success` | `boolean` \| `null` | ❌ | Task execution success | `false` |
| `retry_count` | `integer` | ❌ | Number of retries | `0` |
| `handoff_count` | `integer` | ❌ | Number of handoffs | `0` |
| `error_type` | `string` \| `null` | ❌ | Error classification if failed | `"timeout"` |
| `context_tokens_total` | `integer` | ❌ | Total context tokens used | `500` |
| `trace_completeness_score` | `number` \| `null` | ❌ | Trace completeness (0.0–1.0) | `0.95` |
| `agent_name` | `string` | ❌ | Agent name (shadow exports only) ⚠ **暫定** | `"k2_shadow"` |
| `step_count` | `integer` | ❌ | Number of steps ⚠ **暫定** | `3` |

**`source_ref` sub-object:**

| Field | Type | Required | Semantics | Example |
|-------|------|----------|-----------|---------|
| `task_id` | `string` | ❌ | Source task_id (may differ from top-level if joined) | `"t-infra"` |
| `trace_id` | `string` | ❌ | Source trace_id | `"tr-3"` |
| `line_index` | `integer` | ❌ | 1-based line number in exporter input JSONL | `3` |

**Known variants (T1b):** `shadow_eval_results.latest.jsonl` has the same schema but records may carry `agent_name` in metrics and `source_ref` field name may differ slightly (source_file instead of source_ref). This is a **future normalization target**.

---

### T2. ibridge Records (Flat)

| Field | Type | Required | Semantics | Example |
|-------|------|----------|-----------|---------|
| `task_id` | `string` | ✅ | Task identifier | `"t-infra"` |
| `trace_id` | `string` | ✅ | Unique trace ID | `"tr-3"` |
| `end_time` | `string` | ❌ | ISO 8601 task completion time | `"2026-05-23T10:02:00Z"` |
| `timestamp` | `string` | ❌ | ISO 8601 (fallback to start_time or end_time) | `"2026-05-23T10:02:00Z"` |
| `success` | `boolean` | ❌ | Task success flag | `false` |
| `retry_count` | `integer` | ❌ | Number of retries | `0` |
| `handoff_count` | `integer` | ❌ | Number of handoffs | `0` |
| `error_type` | `string` \| `null` | ❌ | Error type if failed | `"timeout"` |
| `context_token_usage` | `object` | ❌ | Token usage sub-object: `{total_tokens: integer}` | `{"total_tokens": 500}` |
| `trace_completeness` | `object` | ❌ | Completeness sub-object: `{score: number}` | `{"score": 0.95}` |

---

### T3. Shadow ibridge Records (ibridge + Extra Fields)

Same as **T2** plus:

| Field | Type | Required | Semantics | Example |
|-------|------|----------|-----------|---------|
| `agent_name` | `string` | ❌ | Shadow pipeline agent alias | `"k2_shadow"` |
| `tags` | `string[]` | ❌ | Risk/quality tags carried from K-2 summary | `["infra_risk"]` |

**⚠ Important:** `tags` may be `[]` if the upstream K-2 eval gate did not populate them, or if they were stripped by a downstream transform.

---

### T4 / T5. K-2 Spool / Shadow Batch (Mixed Raw Format)

**Three different line formats coexist in the same file (⚠ 暫定 — unstable):**

**Format A — ok/record wrapper (most common):**

| Field | Type | Required | Semantics | Example |
|-------|------|----------|-----------|---------|
| `ok` | `boolean` | ❌ | Wrapper success flag | `true` |
| `record` | `object` | ❌ | Nested record with task fields | `{task_id: ..., trace_id: ...}` |

`record` sub-object fields are identical to T2 ibridge format.

**Format B — Flat with k2_metrics_record:**

| Field | Type | Required | Semantics | Example |
|-------|------|----------|-----------|---------|
| `task_id` | `string` | ❌ | Task identifier | `"shadow-merge-2"` |
| `trace_id` | `string` | ❌ | Trace identifier | `"tr-sk-2"` |
| `k2_metrics_record` | `object` | ❌ | K-2 structured metrics | `{retry_count: 0, handoff_count: 1, success: true, ...}` |

**Format C — case_name + k2_summary:**

| Field | Type | Required | Semantics | Example |
|-------|------|----------|-----------|---------|
| `case_name` | `string` | ❌ | Friendly case name | `"shadow-greeting"` |
| `end_time` | `string` | ❌ | ISO 8601 | `"2026-05-24T10:02:00Z"` |
| `k2_summary` | `object` | ❌ | K-2 summary (see below) | `{pipeline: "k2", ok: true, ...}` |

**`k2_summary` sub-object:**

| Field | Type | Semantics |
|-------|------|-----------|
| `pipeline` | `string` | Pipeline name (e.g. `"k2"`) |
| `ok` | `boolean` | Overall K-2 success |
| `retry_count` | `integer` | K-2 retry count |
| `handoff_count` | `integer` | K-2 handoff count |
| `error_type` | `string` \| `null` | Error type |
| `tags` | `string[]` | Risk tags from K-2 eval gate |

**Additional merge-level fields (spool lines from k2_merge):**
- `k2_merge.gate_result`: string (e.g. `"needs_review"`)
- `k2_merge.k2_eval_tags`: `string[]`
- `ask_summary.ok`: boolean
- `ask_summary.status`: string
- `ask_summary.error_type`: string

---

### T6. Dryrun per_record JSONL

| Field | Type | Required | Semantics | Example |
|-------|------|----------|-----------|---------|
| `task_id` | `string` | ✅ | Task identifier | `"t-infra"` |
| `trace_id` | `string` | ❌ | Trace identifier | `"tr-3"` |
| `actual_verdict` | `string` | ✅ | Real gate output: `"allow"` \| `"warn"` \| `"fail"` \| `"unknown"` | `"fail"` |
| `ideal_verdict` | `string` | ✅ | Dry-run ideal: `"allow"` \| `"warn"` \| `"deny"` \| `"unknown"` | `"deny"` |
| `verdict_match` | `boolean` | ✅ | Does actual == ideal? | `true` |
| `dryrun_rule` | `string` | ✅ | Matched rule name: `"gate_ok_score_high"` \| `"gate_ok_score_low"` \| `"gate_fail_deny"` \| `"gate_fail_needs_review"` \| `"edge_unknown"` | `"gate_fail_deny"` |
| `gate_result` | `string` | ❌ | Original gate_result from source | `"pass"` |
| `tags` | `string[]` | ❌ | Tags from source (**⚠ currently overwritten by synthetic tags — G3**) | `[]` |
| `metrics` | `object` | ❌ | Extracted metrics sub-object (see below) | — |
| `source_file` | `string` | ❌ | Input file name (relative) | `"shadow_ibridge_records.latest.jsonl"` |

**`metrics` sub-object in per_record:**

| Field | Type | Semantics | Example |
|-------|------|-----------|---------|
| `success` | `boolean` \| `null` | Task success | `true` |
| `retry_count` | `integer` \| `null` | Retry count | `0` |
| `handoff_count` | `integer` \| `null` | Handoff count | `0` |
| `error_type` | `string` \| `null` | Error type | `null` |
| `trace_completeness_score` | `number` \| `null` | Trace completeness (0.0–1.0) | `0.95` |

---

### T8. `[DRYRUN-LOG]` Structured Log Format

Prefix: `[DRYRUN-LOG]`

**Events (space-separated key=value):**

```
[DRYRUN-LOG] event=start disclaimer=... input=... min_score=0.875
[DRYRUN-LOG] event=inputs count=3 files=...|...|...
[DRYRUN-LOG] event=summary records=8 matches=7 mismatches=1 match_ratio=87.5% min_score=0.875
[DRYRUN-LOG] event=artefact per_record=observability/dryrun/..._per_record.jsonl summary=..._summary.md stamp=...
[DRYRUN-LOG] event=aggregate_gate ok=true verdict=allow source=...
[DRYRUN-LOG] event=mismatch task_id=t-infra actual=fail ideal=deny rule=gate_fail_deny
[DRYRUN-LOG] event=complete status=ok exit_policy=logging_only
```

Key fields:
- `event`: `start` | `inputs` | `summary` | `artefact` | `aggregate_gate` | `mismatch` | `mismatch_truncated` | `skip` | `error` | `complete`
- `records` / `matches` / `mismatches`: integer counts
- `match_ratio`: formatted percentage string
- `min_score`: float threshold

---

### T9. `[GOV-ENF-PREVIEW]` Structured Log Format

Prefix: `[GOV-ENF-PREVIEW]`

```
[GOV-ENF-PREVIEW] event=summary total=8 would_block=1 would_warn=2 would_noop=5 input=...
[GOV-ENF-PREVIEW] event=detail rule=ENF-RULE-1 would_block=1 min_score=0.7
[GOV-ENF-PREVIEW] event=detail rule=ENF-RULE-2 would_warn=2
[GOV-ENF-PREVIEW] event=would_block task_id=t-infra rule=ENF-RULE-1 dryrun_rule=gate_fail_deny
[GOV-ENF-PREVIEW] event=would_warn task_id=shadow-retry rule=ENF-RULE-2 dryrun_rule=gate_fail_needs_review
[GOV-ENF-PREVIEW] event=complete status=ok exit_policy=preview_only
```

Key fields:
- `event`: `summary` | `detail` | `would_block` | `would_warn` | `skip` | `complete`
- `would_block` / `would_warn` / `would_noop`: integer counts
- `rule`: `"ENF-RULE-1"` | `"ENF-RULE-2"` (future rules may add)
- `dryrun_rule`: `"gate_fail_deny"` | `"gate_fail_needs_review"`

**ENF Rules:**

| Rule | Outcome | Condition |
|------|---------|-----------|
| ENF-RULE-1 (L2 candidate) | `block` | `dryrun_rule == "gate_fail_deny"` + `error_type != null` + risk tag in (`infra_risk`, `security:critical`) + `score >= 0.7` |
| ENF-RULE-2 (L1 observe) | `warn` | `dryrun_rule == "gate_fail_needs_review"` + `high_retry` in tags + `retry_count >= 2` |
| (none) | `noop` | All other cases |

---

### T10. Gov Gate Metrics (`gov-metrics-0.1`)

**⚠ This is a separate schema track from eval_export/v1 — not directly comparable.**

| Field | Type | Semantics | Example |
|-------|------|-----------|---------|
| `exit_code` | `integer` | Script exit code | `0` |
| `run_id` | `string` | Run identifier | `"local"` |
| `schema_version` | `string` | Literal `"gov-metrics-0.1"` | `"gov-metrics-0.1"` |
| `ts` | `string` | ISO 8601 timestamp with fractional seconds | `"2026-05-29T10:25:22.8751691Z"` |
| `case_id` | `string` | Workflow case identifier | `"W2-1"` |
| `gate` | `string` | Gate name (e.g. `"GATE-CROSS-REF-G8RECON"`) | `"GATE-CROSS-REF-G8RECON"` |
| `pipeline` | `string` | Pipeline trigger (e.g. `"manual"`) | `"manual"` |
| `helper` | `string` | Helper script name | `"wf_check_cross_ref"` |
| `scope` | `string` | Scope identifier | `"G8Recon"` |
| `verdict` | `string` | Gate verdict | `"allow"` |
| `checks_failed` | `string[]` | List of failed check names | `["fallback_used"]` |
| `message` | `string` | Human-readable summary | `"Summary: ALL PASS (7 checks) \| exit 0"` |

---

## 3. Unified Schema for Analysis & Dashboard

### 3.1 Rationale

The six main JSONL types (T1–T6) share significant overlap. For dashboard / long-term monitoring, a single **unified analysis schema** is proposed below. Each unified field has a **primary source** and optional **fallback sources**.

### 3.2 Unified Analysis Schema

| # | Field | Type | Primary Source | Fallback Source(s) | Semantics |
|---|-------|------|---------------|--------------------|-----------|
| 1 | `date` | `string` (YYYY-MM-DD) | `exported_at` (T1) or `end_time` / `timestamp` (T2/T6) | Any artefact timestamp | Analysis date partition |
| 2 | `run_stamp` | `string` | Dryrun filename stamp (T6) or CI workflow run ID | T8/T9 event timestamp | Pipeline run identifier |
| 3 | `source_file` | `string` | T6 `source_file` (dryrun) or T1/T2 filename | — | Which artefact produced this record |
| 4 | `pipeline_stage` | `string` | Derived: `"eval_export"` \| `"ibridge"` \| `"shadow_ibridge"` \| `"raw_spool"` \| `"dryrun"` \| `"enf_preview"` | — | Which pipeline stage produced this record |
| 5 | `task_id` | `string` | T1/T2/T6 `task_id` | T4 `record.task_id`, T4 `case_name` | Task/case identifier |
| 6 | `trace_id` | `string` | T1/T2/T6 `trace_id` | T4 `record.trace_id` | Unique trace identifier |
| 7 | `success` | `boolean` | T1 `metrics.success` or T2 `success` | T6 `metrics.success` | Task execution result |
| 8 | `error_type` | `string` \| `null` | T1 `metrics.error_type` or T2 `error_type` | T6 `metrics.error_type` | Error classification |
| 9 | `retry_count` | `integer` | T1 `metrics.retry_count` or T2 `retry_count` | T6 `metrics.retry_count` | Number of retries |
| 10 | `handoff_count` | `integer` | Same pattern as retry_count | — | Number of handoffs |
| 11 | `score` | `number` \| `null` | T1 `metrics.trace_completeness_score` or T2 `trace_completeness.score` | T6 `metrics.trace_completeness_score` | Trace completeness (0.0–1.0) |
| 12 | **`tags`** | `string[]` | T1 `tags` or T3 `tags` | T6 `tags` (**⚠ currently synthetic — see G3**) | Risk/quality tags |
| 13 | `gate_result` | `string` | T1 `gate_result` or T6 `gate_result` | — | Original gate verdict |
| 14 | `actual_verdict` | `string` | T6 `actual_verdict` | T1 `gate_result` (mapped) | Real gate output bucket |
| 15 | `ideal_verdict` | `string` | T6 `ideal_verdict` | — | Dry-run ideal bucket |
| 16 | `verdict_match` | `boolean` | T6 `verdict_match` | — | Do actual and ideal agree? |
| 17 | `dryrun_rule` | `string` | T6 `dryrun_rule` | — | Which dry-run rule matched |
| 18 | `enf_rule` | `string` \| `null` | T9 `rule` + `outcome` | — | Which ENF rule triggered (`"ENF-RULE-1"`, `"ENF-RULE-2"`, or `null`) |
| 19 | `enf_outcome` | `string` \| `null` | T9: `"block"` / `"warn"` / `"noop"` | — | ENF preview outcome |
| 20 | `schema_version` | `string` | T1 `schema_version` | — | Schema version identifier |

### 3.3 CSV Export Column Order (Recommended for Dashboard)

```
date, run_stamp, pipeline_stage, task_id, trace_id, success, error_type,
retry_count, handoff_count, score, tags, gate_result, actual_verdict,
ideal_verdict, verdict_match, dryrun_rule, enf_rule, enf_outcome,
source_file, schema_version
```

### 3.4 Federation Strategy

A daily CSV exporter should:
1. **Scan** `artifacts/eval/*.jsonl` (T1–T5) and `observability/dryrun/*_per_record.jsonl` (T6).
2. **Parse each type** with its specific reader, mapping to the unified schema.
3. **Deduplicate by** `(task_id, trace_id, pipeline_stage, run_stamp)`.
4. **Merge** ENF preview outcomes from T9 (if captured) by matching `task_id` + `dryrun_rule`.
5. **Output** a single daily CSV partitioned by `date`.

---

## 4. Known Pitfalls for Future Exporter / Dashboard

### ⚠ P1 — Tags Are Not Reliable in Per-Record Files

Per `G3` (W5-D-CI-GAP-CHECKLIST-01): `dryrun/core.py` `_normalize_export_row()` overwrites real tags with synthetic tags derived from metrics. This means:
- `tags=[]` in per_record JSONL **does not mean** the original record had no tags.
- Real infra_risk tags from the K-2 eval gate are lost before ENF rules evaluate them.
- **Fix needed:** In `build_comparison_rows()`, merge `record.get("tags")` with synthetic tags rather than replacing them.
- **Temporary workaround:** Parse tags directly from the raw spool (T4) or shadow ibridge (T3) instead of the per_record file.

### ⚠ P2 — Three Raw Spool Formats Coexist in One File

`k2_shadow_spool.jsonl` and `shadow_batch_*.jsonl` contain **3 different line formats**:
- `{ok, record}` wrapper (most common)
- flat `{task_id, k2_metrics_record, ...}`
- `{case_name, k2_summary, ...}`

A robust reader must detect format at line level by checking for the presence of `ok`/`record`, `case_name`, or `task_id`. The `ibridge_exporter.normalize_shadow_record()` function already does this — reuse it rather than reimplementing.

### ⚠ P3 — JSON Lines in Observability/Dryrun Come from Multiple CI Runs

The `observability/dryrun/` directory accumulates `*_per_record.jsonl` files from both manual runs and CI, without a cleanup policy. A dashboard reader must pick the **latest** file by timestamp (which the `_discover_latest_per_record()` function does correctly) or provide a date range selector.

### ⚠ P4 — eval_export/v1 Has No CI Producer (G4)

`eval_export/v1` JSONLs only exist as hand-crafted fixtures (N=3). No CI job runs `eval_exporter`. Until G4 is fixed, any dashboard consuming `eval_export/v1` will see only smoke test data. **Recommendation:** Base the dashboard on dryrun per_record JSONL (T6) instead — it's the richest, most CI-produced dataset currently available.

### ⚠ P5 — Gov Gate Metrics Is a Different Schema Track

`gov-metrics-0.1` (T10) records governance gate verdicts from workflow_v2, not eval gate. Fields like `case_id`, `gate`, `checks_failed` are orthogonal to eval gate fields. If a unified dashboard needs both, two separate data sources must be ingested and joined by timestamp/case_id rather than merged into one schema.

### ⚠ P6 — Timestamp Precision Differs

- T1/T2: `"2026-05-23T10:02:00Z"` (seconds precision)
- T10: `"2026-05-29T10:25:22.8751691Z"` (sub-second precision with 7 decimal places)
- T8/T9: CI log timestamps (seconds or sub-second, depending on GitHub Actions log)
- **Recommendation:** All analysis should normalize timestamps to ISO 8601 with **seconds precision** (truncating fractional seconds) for join keys.

### ⚠ P7 — File Encoding: gov-metrics Has UTF-8 BOM

`local.jsonl` (T10) starts with a UTF-8 BOM (`\ufeff`). Standard JSONL parsers must handle this (e.g., `encoding='utf-8-sig'` in Python). The other JSONL files (T1–T6) are BOM-free.

### ⚠ P8 — Dryrun Summary Markdown Not Machine-Parsable

The dryrun summary (T7) is designed for human reading and contains natural language tables and commentary. For dashboard consumption, use the per_record JSONL (T6) + structured logs (T8/T9) instead.

---

## 5. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| v0.1 | 2026-05-31 | W5-D-ARTEFACT-SPEC-01 | Initial spec: 11 artefact types, unified schema (20 fields), 8 documented pitfalls |

---

*Generated: 2026-05-31 by W5-D-ARTEFACT-SPEC-01*
