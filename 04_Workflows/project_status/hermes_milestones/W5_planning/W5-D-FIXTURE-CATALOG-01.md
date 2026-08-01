# W5-D-FIXTURE-CATALOG-01: Eval / Shadow / Gate Fixture Catalog

> **Status:** Read-only survey (只讀＋文件)
> **Scope:** All fixture + sample data related to eval gate, shadow, dryrun, and governance gate.
> **Hard boundary:** No file modifications, no new fixtures, no CI changes.

---

## A. Fixture Type Overview

| Type | Schema / Format | Record Count | Location | Used By |
|---|---|---|---|---|
| **Smoke (ibridge)** | `task_id`, `trace_id`, `end_time`, `success`, `retry_count`, `handoff_count`, `error_type`, `context_token_usage`, `trace_completeness` | 3 | `artifacts/eval/smoke_ibridge_records.jsonl` | eval-shadow-smoke CI job |
| **Smoke (eval export)** | `schema_version`, `trace_id`, `task_id`, `gate_result` (pass/needs_review), `tags`, `reasons`, `metrics`, `source_ref` | 3 | `artifacts/eval/smoke_eval_results.jsonl` | eval-shadow-smoke CI job |
| **Fixture (ibridge)** | ibridge format (same schema as smoke_ibridge) | 3 | `tests/fixtures/eval/ibridge_records.jsonl` | `test_eval_ci_check.py`, `test_ibridge_exporter.py`, `test_eval_exporter.py`; CI `workflow_dispatch use_fixture=true` |
| **Fixture (eval export)** | eval_export/v1 schema | 3 | `tests/fixtures/eval/eval_export_sample.jsonl` | `test_eval_stats.py` |
| **Fixture (shadow raw)** | Mixed K-2 spool: `{ok, record}`, `k2_metrics_record`, `k2_summary` | 4 | `tests/fixtures/eval/shadow_raw_records.jsonl` | `test_ibridge_exporter.py` (shadow profile); CI nightly SHADOW_SPOOL_BOOTSTRAP |
| **Shadow batch (prod)** | `{ok, record}` structure | 5 | `artifacts/eval/shadow_batch_20260530.jsonl` | Shadow eval pipeline |
| **Shadow export (ibridge)** | ibridge format + `agent_name`, `tags` | 6 | `artifacts/eval/shadow_ibridge_records.latest.jsonl` | CI eval-shadow-nightly |
| **Shadow export (eval)** | eval_export/v1 | 4 | `artifacts/eval/shadow_eval_results.latest.jsonl` | Dryrun verify step |
| **K-2 spool** | `{ok, record}` K-2 raw spool format | 4 | `artifacts/eval/k2_shadow_spool.jsonl` | CI eval-shadow-nightly (SHADOW_SPOOL) |
| **Latest ibridge** | ibridge format (same as smoke) | 3 | `artifacts/eval/ibridge_records.latest.jsonl` | CI default `eval_input` (workflow_dispatch) |
| **AC2 shadow** | ibridge + `agent_name`, `tags` | 6 | `artifacts/eval/_ac2_shadow_ibridge.jsonl` | AC2 pipeline (internal) |
| **AC2 dryrun** | `actual_verdict`, `ideal_verdict`, `verdict_match`, `dryrun_rule`, `gate_result`, `tags`, `metrics` | 6 | `artifacts/eval/_dryrun_ac2/20260531T030111Z_per_record.jsonl` | CI dryrun (AC2 -> gate) |
| **Verify dryrun** | Same dryrun schema | 9 | `artifacts/eval/_dryrun_verify/20260531T030106Z_per_record.jsonl` | CI dryrun (verify -> gate) |
| **Observability dryrun (×6)** | Same dryrun schema | 3–8 each | `observability/dryrun/20260530T*.jsonl` | Historical logs (not CI-driven) |
| **Schema definition** | JSON Schema draft 2020-12 | 1 file (74 lines) | `observability/eval_export_schema.json` | Reference only |
| **Governance gate metrics** | `exit_code`, `verdict`, `gate`, `checks_failed`, `schema_version: gov-metrics-0.1` | 3 | `workflow_v2/observability/gov_gate_metrics/local.jsonl` | Manual/local runs (not CI) |

---

## B. Usage & Risk Details

### B1. Smoke Fixtures (4 records total across 2 files)

- **`artifacts/eval/smoke_ibridge_records.jsonl`** (3 records) + **`artifacts/eval/smoke_eval_results.jsonl`** (3 records)
- Covers 3 scenarios: healthy pass, retry-heavy needs_review, timeout needs_review
- **Risk:** Only 3 records, all with the same `exported_at` timestamp. No variety in date ranges, no mixed `gate_result` distributions beyond the 1-pass/2-needs_review ratio. Does **not** represent real production distributions (e.g., real-world pass ratios, varied error types, mixed agent_names).
- Used by: CI eval-shadow-smoke job (push/PR trigger).

### B2. Test Fixtures (tests/fixtures/eval/)

- **`ibridge_records.jsonl`** — 3 records (same data as smoke_ibridge but in tests/ directory). Primary unit test input.
- **`shadow_raw_records.jsonl`** — 4 records, intentionally **heterogeneous** format (some `{ok, record}`, some flat with `k2_metrics_record`, some `k2_summary`). Tests the ibridge exporter's parsing resilience.
- **`eval_export_sample.jsonl`** — 3 records (same content as `smoke_eval_results.jsonl`). Used by `test_eval_stats.py`.
- **Risk:** The test fixtures are small (3–4 records each) and hand-crafted. They verify format compliance but cannot catch regressions in production-scale distributions or edge cases found in real shadow data.

### B3. Production Shadow Fixtures

- **`shadow_batch_20260530.jsonl`** (5 records) — Recent production batch, `{ok, record}` format.
- **`shadow_eval_results.latest.jsonl`** (4 records) — Gate results from the shadow batch (eval_export/v1 format).
- **`shadow_ibridge_records.latest.jsonl`** (6 records) — Export result: ibridge records with extra `agent_name` and `tags` fields not present in smoke fixtures.
- **`k2_shadow_spool.jsonl`** (4 records) — Raw K-2 spool format.
- **Risk:** These are closer to real data but still small (<10 records each). They may not reflect the full diversity of production traffic (e.g., missing error types, uniform `context_token_usage` ranges, limited agent names).

### B4. Dryrun Outputs

- **`artifacts/eval/_dryrun_ac2/`** and **`_dryrun_verify/`** — Gate dryrun verdict records generated by CI.
- **`observability/dryrun/*.jsonl`** (6 files) — Historical dryrun artifacts from 2026-05-30. Each contains 3–8 records with `actual_verdict` vs `ideal_verdict` comparison.
- **Risk:** These are outputs, not input fixtures. Their existence documents past run results but should not be used as regression fixtures without understanding their generation context.

### B5. Governance Gate Metrics

- **`workflow_v2/observability/gov_gate_metrics/local.jsonl`** — 3 records from local manual runs. Different schema (`gov-metrics-0.1`, separate from eval_export). Not consumed by CI.
- **Risk:** Not part of the eval gate CI pipeline. Only relevant for W2 governance gate workflow debugging.

---

## C. CI Workflow Usage Summary (eval-gate-ci.yml)

| CI Job | Fixture / Input | When |
|---|---|---|
| **eval-ci (unit tests)** | `tests/fixtures/eval/ibridge_records.jsonl` (via `use_fixture=true`) | On PR/push + workflow_dispatch |
| **eval-ci (production)** | `artifacts/eval/ibridge_records.latest.jsonl` (default) | On workflow_dispatch |
| **eval-shadow-smoke** | `artifacts/eval/smoke_ibridge_records.jsonl` + `smoke_eval_results.jsonl` | On PR/push |
| **eval-shadow-nightly** | `k2_shadow_spool.jsonl` → `shadow_ibridge_records.latest.jsonl` → `shadow_eval_results.latest.jsonl` | Schedule (06:00 UTC daily) + workflow_dispatch |

---

## D. Principles for Adding New Fixtures

1. **名實相符 (Name accurately reflects content)**
   - `smoke_*` = small, hand-crafted, covers happy + failure paths
   - `shadow_*` = generated from or representing real production data
   - `_dryrun_*` = gate dryrun verdict output (not an input fixture)
   - Don't store a production shadow batch as `smoke_*` or mix data types in a single file.

2. **最小但夠用 (Minimum viable coverage)**
   - Smoke fixture: 3–5 records covering pass, needs_review (retry), needs_review (infra_risk/error)
   - Test fixture: mirror the smoke data but in `tests/fixtures/eval/` for unit tests; only add records when a new test scenario requires it
   - Shadow batch: keep at `artifacts/eval/shadow_batch_<date>.jsonl` with date suffix; do not overwrite without archiving the old one

3. **Schema一致性 (Schema consistency)**
   - All eval gate fixtures must conform to `eval_export/v1` schema (documented in `observability/eval_export_schema.json`) or the corresponding ibridge/K-2 source schema
   - If adding a new format (e.g., `_ac2_shadow_ibridge.jsonl` with `agent_name`), suffix the filename to differentiate it from the base schema
   - `source_ref.line_index` in eval_export fixtures must accurately point to the source row; manually correct if row order changes

4. **不重複 (No duplication)**
   - `artifacts/eval/ibridge_records.latest.jsonl` is currently identical to `smoke_ibridge_records.jsonl` and `tests/fixtures/eval/ibridge_records.jsonl` only differs by field ordering. When adding new records, pick one authoritative source and derive the others.
   - Future: consider declaring `tests/fixtures/eval/ibridge_records.jsonl` as the canonical source and symlinking/copying to `artifacts/eval/`.

5. **可追溯 (Traceability)**
   - Shadow batch files: include date in filename (`shadow_batch_YYYYMMDD.jsonl`)
   - Dryrun output: timestamped subdirectory (`_dryrun_*/YYYYMMDDTHHMMSSZ_`)
   - When a fixture is generated by a CI step (not hand-crafted), document the generation script in the file header comment or adjacent README

---

## File Stats

- **Total fixture files cataloged:** 20 JSON/JSONL files across 4 directories
- **Total records (sum):** ~75–80 (varies by observability dryrun)
- **Smoke records:** 3 (ibridge) + 3 (eval_export)
- **Test fixture records:** 3 (ibridge) + 4 (shadow_raw) + 3 (eval_export) = 10
- **Production shadow records:** 5 (batch) + 6 (ibridge export) + 4 (eval export) + 4 (k2 spool) = 19
- **AC2/Verify records:** 6 (ac2_shadow) + 6 + 9 = 21

---

*Generated: 2026-05-31 by W5-D-FIXTURE-CATALOG-01*
