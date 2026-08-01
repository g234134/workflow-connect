# Agent Lines Metrics & Monitoring v1

> **Ticket**: W10-T2 · agent-lines-metrics-and-monitoring-v1  
> **Implementation**: `scripts/analyze_agent_lines_metrics.py`  
> **Date**: 2026-06-10  
> **Status**: offline metrics extractor — **does not** connect to external monitoring systems

---

## 1. Purpose

Provide a **read-only, filesystem-based metrics extractor** for:

- Tabular Agent standard line regression artifacts
- Non-tabular preview experiment artifacts
- Future `outbox/agent_ci/` CI artifacts (when present)

No changes to outbox write logic. No Prometheus / PG / external DB.

---

## 2. Scan roots

| Source | Path | Notes |
|--------|------|-------|
| Tabular regression | `outbox/agent_experiment_regression/` | W6-T8 regression JSON |
| Agent CI | `outbox/agent_ci/` | Optional; skipped if missing |
| Non-tabular preview | `outbox/non_tabular_experiment/` | W9-T4 preview JSON |

Subdirectories named `_checkpoint_scratch` are skipped.

---

## 3. Metrics extracted

### 3.1 Run success / error rate

| Field | Logic |
|-------|-------|
| `successful_runs` | `case_summary.ok == true`, or `final_status` in success set |
| `failed_runs` | inverse |
| `error_rate` | `failed_runs / total_runs` |

### 3.2 HITL checkpoint trigger rates (CP-A / CP-B)

Applicable to Tabular regression artifacts only (`agent_experiment_regression`, `agent_ci`).

| Checkpoint | Triggered when |
|------------|----------------|
| **CP-A** | `checkpoint_a_status` in `would_pause`, `auto_approved`, `written`, … **or** `experiment.checkpoint_a_status.would_trigger == true` |
| **CP-B** | `checkpoint_b_would_trigger == true`, `checkpoint_b_status` in `would_trigger`, `stopped_before_delivery`, … **or** `experiment.checkpoint_b_status.would_trigger == true` |

Non-tabular preview artifacts report `checkpoint_*_triggered: null` in per-run detail (HITL not integrated on that line in v1).

### 3.3 Time-to-completion (rough duration)

When both timestamps exist:

```text
duration_seconds = written_at − regression_meta.timestamp
```

Fallback: filename prefix `<YYYYMMDDTHHMMSSZ>_*.json` as start time.

---

## 4. How to run

```bash
python scripts/analyze_agent_lines_metrics.py
python scripts/analyze_agent_lines_metrics.py --format json
python scripts/analyze_agent_lines_metrics.py --no-write --format json
```

### Unittest

```bash
python -m unittest tests.test_analyze_agent_lines_metrics_v1 -v
```

---

## 5. Output artifacts

| File | Description |
|------|-------------|
| `outbox/agent_metrics/metrics_summary.json` | Full structured summary |
| `outbox/agent_metrics/metrics_summary.csv` | Flat rows: aggregate + by_source + by_case_ref |

---

## 6. `metrics_summary.json` schema

Top-level keys:

| Key | Type | Description |
|-----|------|-------------|
| `ok` | bool | Analyzer completed without fatal error |
| `schema_version` | string | `agent_lines_metrics_v1` |
| `generated_at` | string | ISO-8601 UTC |
| `repo_root` | string | Repo root used for scan |
| `sources_scanned` | array | Per scan root: `source`, `path`, `exists`, `json_files_parsed` |
| `aggregate` | object | Totals across all parsed runs |
| `by_source` | object | Bucket per scan source name |
| `by_case_ref` | object | Bucket per `case_ref` |
| `by_fixture_maturity` | object | **W12-T2** — Tabular tier buckets (`stable` / `controlled_experimental` / `experimental` / `unknown`) |
| `runs` | array | Per-artifact detail records |
| `output_paths` | object | Relative paths to written JSON/CSV |
| `message` | string | Human summary |

### Aggregate / bucket object fields

| Field | Description |
|-------|-------------|
| `total_runs` | Parsed artifact count |
| `successful_runs` | Success count |
| `failed_runs` | Failure count |
| `error_rate` | 0.0–1.0 |
| `checkpoint_a_triggered` | CP-A trigger count |
| `checkpoint_a_trigger_rate` | 0.0–1.0 |
| `checkpoint_b_triggered` | CP-B trigger count |
| `checkpoint_b_trigger_rate` | 0.0–1.0 |
| `duration_samples` | Runs with computable duration |
| `duration_seconds_mean` | Mean duration (or null) |
| `duration_seconds_median` | Median duration (or null) |
| `duration_seconds_min` | Min duration (or null) |
| `duration_seconds_max` | Max duration (or null) |

### Per-run record fields (`runs[]`)

| Field | Description |
|-------|-------------|
| `source` | e.g. `agent_experiment_regression` |
| `path` | Repo-relative JSON path |
| `schema_version` | Source artifact schema |
| `case_ref` | Case identifier |
| `fixture_maturity` | Tabular tier label (or `null` for non-tabular) — **W12-T2** |
| `ok` | Inferred success |
| `final_status` | From artifact |
| `checkpoint_a_triggered` | bool or null (non-tabular) |
| `checkpoint_b_triggered` | bool or null (non-tabular) |
| `duration_seconds` | float or null |
| `written_at` | Source artifact timestamp |

---

## 7. `metrics_summary.csv` columns

| Column | Used in sections |
|--------|------------------|
| `section` | `aggregate` · `by_source` · `by_case_ref` · `by_fixture_maturity` |
| `source` | `by_source` rows |
| `case_ref` | `by_case_ref` rows |
| `fixture_maturity` | `by_fixture_maturity` rows — **W12-T2** |
| `total_runs` | all |
| `successful_runs` | all |
| `failed_runs` | all |
| `error_rate` | all |
| `checkpoint_a_triggered` | all |
| `checkpoint_a_trigger_rate` | all |
| `checkpoint_b_triggered` | all |
| `checkpoint_b_trigger_rate` | all |
| `duration_samples` | all |
| `duration_seconds_mean` | all |
| `duration_seconds_median` | all |
| `duration_seconds_min` | all |
| `duration_seconds_max` | all |

---

## 8. Fixture maturity tiers (W12-T2)

Tabular regression / CI artifacts may carry `fixture_maturity` (W11-T1). The metrics extractor:

1. Reads `case_summary.fixture_maturity` or `experiment.fixture_maturity` when present.
2. Falls back to `get_fixture_maturity(case_ref)` from `run_agent_standard_case_experiment.py`.
3. Groups **tabular sources only** into `by_fixture_maturity` (non-tabular runs omit this field and bucket).

| Tier | Typical fixtures |
|------|------------------|
| `stable` | `demo_phase`, `sampleco/2026-0001` |
| `controlled_experimental` | `additional_demo`, `sandbox_client` |
| `experimental` | Reserved label for pre-promotion fixtures |
| `unknown` | Legacy artifacts without maturity metadata |

**Backward compatibility**: existing top-level keys unchanged; `by_fixture_maturity` is additive. Text stdout adds a one-line-per-tier rollup when data exists.

---

## 9. Monthly report (W11-T3 / W12-T2)

Offline Markdown rollup built **only** from an existing `metrics_summary.json` (`runs[]`). No rescan of outbox directories; no notifications; no external services.

### 9.1 How to run

```bash
python scripts/generate_agent_lines_monthly_report.py
python scripts/generate_agent_lines_monthly_report.py --input outbox/agent_metrics/metrics_summary.json
python scripts/generate_agent_lines_monthly_report.py --month 2026-06
python scripts/generate_agent_lines_monthly_report.py --no-write --format json
```

Typical flow: run W10-T2 extractor first, then generate monthly reports:

```bash
python scripts/analyze_agent_lines_metrics.py
python scripts/generate_agent_lines_monthly_report.py
```

### 9.2 Output artifacts

| File | Description |
|------|-------------|
| `outbox/agent_metrics/monthly_report_YYYY-MM.md` | Human-readable monthly summary (one file per month with data) |

### 9.3 Monthly aggregation

Runs are bucketed by `written_at` month (`YYYY-MM`). Runs without `written_at` are skipped.

| Bucket | Sources |
|--------|---------|
| **Tabular** | `agent_experiment_regression`, `agent_ci` |
| **Non-tabular preview** | `non_tabular_experiment` |

Per month (overall + tabular + non-tabular columns):

| Metric | Notes |
|--------|-------|
| `total_runs` | Parsed run count in month |
| `error_rate` | `failed_runs / total_runs` |
| `checkpoint_a_trigger_rate` | Tabular only; non-tabular shows `—` |
| `checkpoint_b_trigger_rate` | Tabular only; non-tabular shows `—` |
| `non_tabular_preview_count` | Count of `non_tabular_experiment` runs |

### 9.4 Fixture maturity table (W12-T2)

Each `monthly_report_YYYY-MM.md` includes a **Tabular fixture maturity (tier rollup)** table when tabular runs exist for that month:

| Tier | Runs | Error rate | CP-A rate | CP-B rate |

Runs without `fixture_maturity` roll up as `unknown`.

### 9.5 Unittest

```bash
python -m unittest tests.test_generate_agent_lines_monthly_report_v1 -v
```

### 9.6 Ticket state

`04_Workflows/tickets/W11-T3-agent-lines-monthly-metrics-report-v1_state.md`

---

## 10. Non-scope

- Does **not** modify outbox writers (`run_agent_standard_case_regression.py`, etc.)
- Does **not** integrate with Observability PG / Langfuse / Prometheus
- Does **not** replace W6-T7 eval guide success definitions for acceptance gating
- Monthly report (W11-T3) does **not** send email / Slack / Telegram or call external APIs

---

## 11. Upstream references

- `docs/agent-standard-case-regression-v1.md` — regression artifact envelope
- `docs/agent-run-experiment-eval-guide-v1.md` — success / checkpoint semantics
- `docs/agent-standard-line-governance-view-v2.md` — audit material paths
- `docs/non-tabular-orchestrator-preview-v1.md` — non-tabular outbox shape

---

## 12. Ticket state

- W10-T2: `04_Workflows/tickets/W10-T2-agent-lines-metrics-and-monitoring-v1_state.md`
- W11-T3: `04_Workflows/tickets/W11-T3-agent-lines-monthly-metrics-report-v1_state.md`
- W12-T2: `04_Workflows/tickets/W12-T2-tabular-fixture-maturity-aware-metrics-and-ci-v1_state.md`

---

## 13. Toolchain health dashboard (WB-T4)

Offline metrics output is consumed read-only by the unified toolchain dashboard:

```bash
python scripts/run_toolchain_health_dashboard.py --format json --dry-run
```

See `docs/toolchain-health-dashboard-v1.md` for `toolchain_health_v1` schema, `aggregated_health_score`, and optional `wf_status_summary` integration. Dashboard class: **optional** (`blocks_mainline=false` per WA-T3 P3.5).
