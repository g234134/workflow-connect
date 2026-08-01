# eval_gate export & CI (v1)

> **Modules**: `observability/eval_exporter.py`, `observability/eval_ci_check.py`, `observability/eval_stats.py`, `observability/eval_report.py`, `observability/eval_trace_correlate.py`, `observability/wf_status_summary.py`  
> **Schema**: `observability/eval_export_schema.json` (`eval_export/v1`)  
> **Gate logic**: `observability/eval_gate.py` → `evaluate_task_record` (unchanged)  
> **Distribution / CI thresholds (analysis only)**: `observability/eval_stats_report.md`  
> **Wave B report artifacts**: `artifacts/eval/eval_report.latest.{md,json}` (CI upload; local via `eval_report`)

---

## Wave B eval gate report (`WAVE-B-P1-EVAL-GATE-REPORT-BOOTSTRAP`)

Generate Markdown + JSON summary from `eval_export/v1` JSONL (does **not** change gate logic or default CI thresholds):

```bash
# Fixture-aligned smoke (N=3)
python -m observability.eval_report tests/fixtures/eval/eval_export_sample.jsonl --out-dir artifacts/eval

# Nightly export when present
python -m observability.eval_report artifacts/eval/eval_export_v1_shadow_nightly.latest.jsonl --out-dir artifacts/eval
```

**CI**: `.github/workflows/eval-gate-ci.yml` uploads `eval-gate-report-pr` (PR job) and `eval-gate-report-nightly` (nightly job).

**Wave C 留项**: HTML dashboard / Slack 通知 / 14 日 baseline 自动 tighten（见 `docs/WAVE_B_EXECUTION_PLAN.md`）。

---

## WF status summary (`WAVE-B-P3-WF-STATUS-SUMMARY-CLI`)

One-page **Executive summary** across gate report, index status, and trace join stats (read-only assembly):

```bash
python -m observability.wf_status_summary \
  --eval tests/fixtures/eval/eval_export_sample.jsonl \
  --index-status workflow_v2/20_pilot/W3-B/index_status_W2-1.json \
  --trace-jsonl tests/fixtures/trace/sample_traces.jsonl \
  --out-dir artifacts/wf
```

**Output**: `artifacts/wf/wf_status_summary.latest.{md,json}` — see `docs/observability.md` §8.

**Suggested follow-up**: wire summary artifact into CI (not in scope for this ticket).

---

## eval / trace correlate (`WAVE-B-P2-EVAL-TRACE-CORRELATE`)

Join `eval_export/v1` rows with local `gov-trace-v2` JSONL so `needs_review` / `infra_risk` rows show trace summaries without manual ID copy-paste into `trace_query`.

**Join key priority** (first match wins):

1. `trace_id` (from row or `source_ref.trace_id`)
2. `task_id` (from row or `source_ref.task_id`)
3. `session_id` (from row or `source_ref.session_id`)

**Default scope**: only **flagged** rows — `gate_result=needs_review` or tags intersecting `--fail-on-tags` (default `infra_risk`). Use `--no-only-flagged` to correlate every export line.

```bash
# Fixture smoke (JSON envelope)
python -m observability.eval_trace_correlate \
  --eval tests/fixtures/eval/eval_export_sample.jsonl \
  --trace tests/fixtures/trace/sample_traces.jsonl \
  --format json

# Markdown appendix for ops triage
python -m observability.eval_trace_correlate \
  --eval tests/fixtures/eval/eval_export_sample.jsonl \
  --trace tests/fixtures/trace/sample_traces.jsonl \
  --format markdown \
  -o artifacts/eval/eval_trace_correlate.latest.md

# Per-row JSONL (one correlated object per line)
python -m observability.eval_trace_correlate \
  --eval artifacts/eval/eval_results.latest.jsonl \
  --trace runtime/task_traces.jsonl \
  --format jsonl \
  --no-only-flagged
```

**Output fields** (each correlated row): `gate_result`, `tags`, `join_key` / `join_value`, `trace_found`, `message`, and when matched `trace_summary` (`event_count`, `first_event`, `last_event`, `trace_completeness` from gov-trace-v2).

**Follow-up**: after correlate, verify a single trace with `python -m observability.trace_query --trace-id <id> --file <trace.jsonl>`.

### Flagged triage enrich (`WAVE-B-P3-FLAGGED-TRIAGE-ENRICH`)

One-page **triage** view for `needs_review` rows: gate reasons + trace summary + `kb_index_status` (from eval export when present; otherwise `unknown`).

| Control | Default | Notes |
|---------|---------|--------|
| `--format triage-md` | — | Fixed block per flagged row (tags, reasons, join, trace, index) |
| `--only-needs-review` | **true** | Only `gate_result=needs_review` (narrower than `--only-flagged`) |
| JSON / JSONL rows | — | Each row includes stable `triage` sub-object: `why_flagged`, `primary_tags`, `trace_ref`, `kb_index_status` |

**Reviewer workflow (3 commands)**:

```bash
GOV_EVAL_EXPORT_KB_INDEX_STATUS=1 \
  python -m observability.eval_exporter tests/fixtures/eval/ibridge_records.jsonl \
  --case-index-map tests/fixtures/eval/case_index_map_W2-1.json \
  -o /tmp/e.jsonl

python -m observability.eval_trace_correlate \
  --eval /tmp/e.jsonl \
  --trace tests/fixtures/trace/sample_traces.jsonl \
  --format triage-md

python -m observability.trace_query \
  --file tests/fixtures/trace/sample_traces.jsonl \
  --trace-id tr-3 \
  --format triage
```

When `GOV_EVAL_EXPORT_KB_INDEX_STATUS=1`, export lines also mirror `kb_index_status` to `source_ref.kb_index_status` and `trace_metadata_sidecar` (observability only — does **not** write gov-trace-v2 JSONL).

**Wave C 留项**: nightly artifact upload, Langfuse deep links, Web UI.

---

## JSONL line schema (`eval_export/v1`)

Each line is a compact eval result (not a full `ibridge_record`):

| Field | Description |
|-------|-------------|
| `schema_version` | Always `eval_export/v1` |
| `trace_id` / `task_id` | From source record |
| `timestamp` | `end_time` → `start_time` → `timestamp` |
| `exported_at` | UTC ISO time when the line was built |
| `gate_result` | `pass` or `needs_review` |
| `tags` / `reasons` | From `evaluate_task_record` |
| `metrics` | Summary only: `retry_count`, `handoff_count`, `error_type`, `context_tokens_total`, `trace_completeness_score`, optional `agent_name`, `step_count` |
| `source_ref` | Optional join keys (`task_id`, `trace_id`, `line_index`) |
| `kb_index_status` | **Optional** (Wave B P3): `ready` \| `stale` \| `missing` \| `null` — only when `GOV_EVAL_EXPORT_KB_INDEX_STATUS=1` |
| `kb_index_job_id` | **Optional** (Wave B P3): repo index job id aligned with case `index_status_*.json` |

---

## kb_index_status export sidecar (`WAVE-B-P3-KB-INDEX-EVAL-OBSERVABILITY`)

**Observability only** — does **not** change `eval_gate` rules, `eval_ci_check` thresholds, or prod selector hook (`GOV_KB_INDEX_SELECTOR_HOOK_ENABLED` stays default **0**).

| Control | Default | Notes |
|---------|---------|--------|
| `GOV_EVAL_EXPORT_KB_INDEX_STATUS` | `0` (off) | Set `1` to attach `kb_index_status` / optional `kb_index_job_id` on export lines |
| `--case-index-map` | *(none)* | JSON `case_id → kb_index_status` or nested `{kb_index_status, kb_index_job_id}` |

**Resolution priority** (frozen):

1. `metadata.kb_index_status` / `metadata.kb_index_job_id`
2. `selector_hints.kb_index_status` / `selector_hints.kb_index_job_id`
3. `--case-index-map` entry for record `case_id`

**Report**: `eval_report` adds **Index context** subsection (`index_context_breakdown` in JSON) — per-status sample counts and `needs_review` ratios. See `observability/eval_stats_report.md`.

```bash
# Flag off (default) — no new fields on export lines
python -m observability.eval_exporter tests/fixtures/eval/ibridge_records.jsonl -o /tmp/eval.jsonl

# Flag on — W2-1 fixture map + metadata on t-infra row
GOV_EVAL_EXPORT_KB_INDEX_STATUS=1 \
  python -m observability.eval_exporter tests/fixtures/eval/ibridge_records.jsonl \
  --case-index-map tests/fixtures/eval/case_index_map_W2-1.json \
  -o /tmp/eval_kb.jsonl

python -m observability.eval_report tests/fixtures/eval/eval_export_sample.jsonl --out-dir artifacts/eval
```

**Wave C 留项**: auto wiring from case / ENG-CTX at runtime; trace JSONL mirror implemented as export-line sidecar only (see `WAVE-B-P3-FLAGGED-TRIAGE-ENRICH`).

---

## Batch export (local)

```bash
# From repo root
python -m observability.eval_exporter path/to/ibridge_records.jsonl -o eval_results.jsonl

# Directory of .json / .jsonl files
python -m observability.eval_exporter path/to/records_dir -o out/eval_results.jsonl

# Only needs_review rows
python -m observability.eval_exporter path/to/records.jsonl --filter needs_review
```

---

## CI hook

### Wired in GitHub Actions

Workflow: `.github/workflows/eval-gate-ci.yml` (`Eval gate CI`).

| Setting | CI value (push / PR) | Notes |
|---------|----------------------|--------|
| Input | `artifacts/eval/ibridge_records.latest.jsonl` | Chat A ibridge export; `workflow_dispatch` can override or select fixture |
| `--limit` | `50` | Last N records in the file |
| `--max-needs-review-ratio` | `0.72` | Chat B `suggested_range` floor (was `0.8` on fixture-only CI); current in-repo sample ~66.7% needs_review |
| `--fail-on-tags` | *(disabled in default CI)* | Target: `infra_risk` per `eval_stats_report.md`; enable when nightly export has no synthetic infra demo rows |

The job runs **after** `unittest` for `tests.test_eval_exporter`, `tests.test_eval_ci_check`, `tests.test_eval_gate`, and `tests.test_ibridge_exporter`. Non-zero `eval_ci_check` exit code fails the workflow.

### Prod shadow nightly (Phase 1 · K-2 playbook)

Same workflow file (`.github/workflows/eval-gate-ci.yml`), job **`eval-shadow-nightly`**:

| Setting | Nightly value | Notes |
|---------|---------------|--------|
| Schedule | `0 6 * * *` UTC | Daily; also `workflow_dispatch` with **Run shadow nightly** = true |
| Export | `python -m observability.ibridge_exporter --source shadow …` | Writes `artifacts/eval/shadow_ibridge_records.latest.jsonl` |
| `eval_ci_check` input | `artifacts/eval/shadow_ibridge_records.latest.jsonl` | Flat ibridge rows (not `eval_export/v1`) |
| `--limit` | `100` | Phase 1 shadow sample window |
| `--max-needs-review-ratio` | **`0.60`** | Phase 1 shadow threshold (`docs/k2_deployment_governance.md` §6.2) |
| `--fail-on-tags` | **`infra_risk`** | PR job keeps tags disabled at **0.72** |

**Shadow export** (`observability/ibridge_exporter.py`):

- `--source shadow` accepts K-2 `run_k2_flow` lines, merge `k2_metrics_record`, or `k2_summary` comparison rows.
- `--profile shadow` names `shadow_ibridge_records.latest.jsonl` / dated `shadow_ibridge_records.YYYYMMDD.jsonl`.

```bash
# Local dry-run (repo root)
python -m observability.ibridge_exporter --source shadow --profile shadow --force \
  tests/fixtures/eval/shadow_raw_records.jsonl \
  -o artifacts/eval/shadow_ibridge_records.latest.jsonl --no-latest

python -m observability.eval_ci_check artifacts/eval/shadow_ibridge_records.latest.jsonl \
  --limit 100 --max-needs-review-ratio 0.60 --fail-on-tags infra_risk
```

**Prod spool** (Wave 1 hook): `artifacts/eval/k2_shadow_spool.jsonl` (override name via `K2_SHADOW_SPOOL_FILENAME`; directory via `IBRIDGE_EXPORT_ROOT` / `resolve_artifact_dir`). Nightly CI bootstraps from `tests/fixtures/eval/shadow_raw_records.jsonl` only when spool is empty.

**Manual / fixture path** (`workflow_dispatch`):

- Set **Use fixture** = true → `tests/fixtures/eval/ibridge_records.jsonl` (local parity / regression).
- Or set **eval_input** to any repo-relative JSONL path.
- Optional **fail_on_tags** (e.g. `infra_risk`) and **max_needs_review_ratio** overrides for strict smoke runs.

### Threshold change process

1. Export or refresh `artifacts/eval/ibridge_records.latest.jsonl` (Chat A) and `eval_export/v1` JSONL for analysis.
2. Run Chat B: `python -m observability.eval_stats artifacts/eval/eval_results.latest.jsonl` and update `observability/eval_stats_report.md`.
3. Adjust `EVAL_CI_MAX_NEEDS_REVIEW_RATIO` / `EVAL_CI_FAIL_ON_TAGS` in `.github/workflows/eval-gate-ci.yml` and mirror values in this section.
4. Re-run CI locally and via `workflow_dispatch` before merging.

Do **not** change ratio or tag gates without a fresh `eval_stats` report (minimum **N≥30** for production lock-in per Chat B).

### Reproduce CI locally (repo root)

```bash
python -m unittest tests.test_eval_exporter tests.test_eval_ci_check tests.test_eval_gate -v

# Default CI (real artifact path, tightened ratio)
python -m observability.eval_ci_check artifacts/eval/ibridge_records.latest.jsonl \
  --limit 50 \
  --max-needs-review-ratio 0.72
```

Expect exit code `0` and JSON with `"ok": true` on the current committed export (~66.7% needs_review).

Fixture regression (same gate params):

```bash
python -m observability.eval_ci_check tests/fixtures/eval/ibridge_records.jsonl \
  --limit 50 --max-needs-review-ratio 0.72
```

Strict ratio smoke (should fail, exit `1`):

```bash
python -m observability.eval_ci_check artifacts/eval/ibridge_records.latest.jsonl \
  --limit 50 --max-needs-review-ratio 0.5
```

Tag gate smoke (should fail on current sample; row `t-infra` has `infra_risk`):

```bash
python -m observability.eval_ci_check artifacts/eval/ibridge_records.latest.jsonl \
  --limit 50 --max-needs-review-ratio 0.72 --fail-on-tags infra_risk
```

Target staging gate once export is clean of intentional infra failures (Chat B provisional):

```bash
python -m observability.eval_ci_check artifacts/eval/ibridge_records.latest.jsonl \
  --limit 100 --max-needs-review-ratio 0.72 --fail-on-tags infra_risk
```

`observability_gap` remains **monitor / nightly only** until baseline shows stable ~0% (see `eval_stats_report.md`).

### CLI reference

```bash
# Fail when >50% of last 100 records need review (module default ratio)
python -m observability.eval_ci_check path/to/records.jsonl --limit 100 --max-needs-review-ratio 0.5

# Also fail if any sampled row has infra_risk (production / nightly)
python -m observability.eval_ci_check path/to/records.jsonl --fail-on-tags infra_risk
```

Exit code `1` when the check fails; stdout is a JSON report with `ok`, `message`, and `stats` (including `tag_counts`, `fail_tag_rows` when applicable).

Module defaults (when flags omitted):

| Flag | Default |
|------|---------|
| `--limit` | 100 |
| `--max-needs-review-ratio` | 0.5 |
| `--min-samples` | 1 |

---

## Real `ibridge_records` JSONL artifacts (P-line exporter)

> **Module**: `observability/ibridge_exporter.py`  
> **Scope**: **dev / staging only** — production export is blocked unless `IBRIDGE_EXPORT_ALLOW_PRODUCTION=1` (tests only).

### Where records come from

| Source | CLI `--source` | Description |
|--------|----------------|-------------|
| In-process metrics | `collector` (default) | `metrics.MetricsCollector` after ask / K-1 / K-2 / skills runs (`GOV_CORE_ASK_IBRIDGE_V0=1` or `ibridge_v0=True`). Ended tasks only unless `--include-in-progress`. |
| Saved JSON/JSONL | `file` | API debug dumps, wrapped `{"ibridge_record": {...}}` lines, or flat records (same shape as `tests/fixtures/eval/ibridge_records.jsonl`). |
| *(not wired)* | — | `runtime/task_traces.jsonl` (gov_core Langfuse correlation) is trace metadata, not a full ibridge_record; use collector or file dumps for eval export. |

### Output paths (default)

Under repo root `artifacts/eval/` (override with `IBRIDGE_EXPORT_ROOT`):

| File | Purpose |
|------|---------|
| `ibridge_records.YYYYMMDD.jsonl` | Dated batch for nightly / manual export |
| `ibridge_records.latest.jsonl` | Most recent export (symlink-like convenience) |
| `shadow_ibridge_records.latest.jsonl` | Prod K-2 shadow path for Phase 1 `eval_ci_check` nightly |
| `shadow_ibridge_records.YYYYMMDD.jsonl` | Dated prod shadow export |

Each line is a **flat** ibridge/metrics record (not `eval_export/v1`). Fields align with the CI fixture: `task_id`, `trace_id`, `end_time` / `timestamp`, `success`, `retry_count`, `handoff_count`, `error_type`, `context_token_usage`, `trace_completeness`, etc.

### Enable / disable

Export runs only when:

- `GOV_DEPLOY_ENV` (or `GOV_ENV`) is `dev`, `staging`, `local`, `test`, `ci`, etc., **or**
- `IBRIDGE_EXPORT_ENABLED=1`

**Blocked** when deploy env is `production` / `prod` (prevents accidental volume + data leakage).

### Commands

```bash
# After dev ask runs (in-memory collector)
export GOV_DEPLOY_ENV=dev
export IBRIDGE_EXPORT_ENABLED=1
python -m observability.ibridge_exporter --source collector --limit 100

# From an existing JSONL dump
python -m observability.ibridge_exporter --source file tests/fixtures/eval/ibridge_records.jsonl \
  -o artifacts/eval/ibridge_records.latest.jsonl --env staging

# Then run P+ eval export (unchanged)
python -m observability.eval_exporter artifacts/eval/ibridge_records.latest.jsonl -o artifacts/eval/eval_results.jsonl
```

Structured stdout is a JSON object with `ok`, `written`, `output_path`, `latest_path`, `deploy_env`.

### Distribution analysis (Chat B)

After `eval_exporter` produces `eval_export/v1` JSONL:

```bash
python -m observability.eval_stats artifacts/eval/eval_results.latest.jsonl --format text
python -m observability.eval_stats path/to/eval_results.YYYYMMDD.jsonl --group-by date
```

See `observability/eval_stats_report.md` for provisional `max-needs-review-ratio` and `fail-on-tags` recommendations. This does **not** change CI YAML or `eval_ci_check` defaults.

### Chat B / C handoff

- **Chat B (P+ thresholds)**: run `eval_stats` on `artifacts/eval/eval_results.*.jsonl`; report in `eval_stats_report.md`.
- **Chat C (CI wiring)**: wired — `EVAL_CI_INPUT` → `artifacts/eval/ibridge_records.latest.jsonl`; ratio `0.72`; enable `EVAL_CI_FAIL_ON_TAGS=infra_risk` after N≥30 real rows without synthetic infra demos.
