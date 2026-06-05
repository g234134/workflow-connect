# eval_export distribution analysis & CI threshold recommendations

> **Tool**: `python -m observability.eval_stats` (`observability/eval_stats.py`)  
> **Input**: `eval_export/v1` JSONL (from `eval_exporter`, not raw `ibridge_records`)  
> **Scope**: Wave X / Chat B — analysis only; does **not** change `.github/workflows` or `eval_ci_check` defaults.

---

## Executive summary (current samples)

| Dataset | N | needs_review | Ratio | Top tags |
|---------|---|--------------|-------|----------|
| `tests/fixtures/eval/eval_export_sample.jsonl` | 3 | 2 | **66.7%** | `infra_risk` (1), `high_retry` (1) |
| `artifacts/eval/smoke_eval_results.jsonl` | 3 | 2 | **66.7%** | same fixture shape |
| Combined (duplicate smoke + sample) | 6 | 4 | **66.7%** | `infra_risk` (2), `high_retry` (2) |

**Status**: Real dev/staging nightly batches from Chat A are **not yet attached** in-repo. Numbers above mirror the committed CI fixture / smoke export. Re-run after `artifacts/eval/eval_results.latest.jsonl` (or dated `eval_results.YYYYMMDD.jsonl`) lands.

---

## Recommended CI thresholds (provisional)

### `max-needs-review-ratio`

| Item | Value | Rationale |
|------|-------|-----------|
| **Observed (fixture-aligned)** | ~67% | 2/3 rows are `needs_review` by design (`t-infra`, `t-retry`). |
| **Suggested range** | **0.72 – 0.87** | Ceiling ~5–20 pp above observed ratio so normal batch noise does not fail CI, while a jump toward ~90%+ still fails. |
| **Current CI (fixture)** | 0.80 | Passes fixture; appropriate **only** while `EVAL_CI_INPUT` points at unit-test data. |
| **After real baseline (N≥30)** | Tighten toward **0.45 – 0.60** if staging stabilizes near 30–50% needs_review (typical healthy dev mix). | Re-run `eval_stats` on nightly export; use `suggested_range` from tool output. |

**Policy**: Set `--max-needs-review-ratio` to the **high** end of `suggested_range` initially when switching from fixture to real data; lower it once two weeks of nightly stats cluster.

### `fail-on-tags`

| Tag | Recommendation | Rationale |
|-----|----------------|-----------|
| **infra_risk** | **Enable** (`--fail-on-tags infra_risk`) | Timeout / context_overflow are hard infra failures; one row should fail CI even if ratio is under ceiling. Fixture row `t-infra` demonstrates this. |
| **observability_gap** | **Optional / nightly only** | Not present in current 3-row sample. Enable fail when baseline is ~0% and instrumentation is stable; until then use dashboard alert. |
| **high_retry** | **Monitor only** | Often reflects workload, not broken deploy; ratio gate is enough unless SRE policy says otherwise. |
| **context_heavy**, **many_handoffs** | **Monitor only** | Absent in current sample. |

**Suggested CLI (staging / nightly, once real export is clean of intentional infra failures):**

```bash
python -m observability.eval_ci_check artifacts/eval/eval_results.latest.jsonl \
  --limit 100 \
  --max-needs-review-ratio 0.87 \
  --fail-on-tags infra_risk
```

(Chat C wires path/thresholds into workflow; this chat does not edit YAML.)

---

## Anomalies & watch items

1. **infra_risk rate (33% in 3-row sample)** — Expected in fixture (one timeout row). On real data, **any** `infra_risk` in a CI sample should trigger investigation; fail-on-tags is appropriate.
2. **No `observability_gap` / `context_heavy` / `many_handoffs` in sample** — Cannot calibrate warn vs fail yet; need Chat A export with low trace completeness and heavy context runs.
3. **Duplicate smoke + sample** — Doubling files duplicates rows; use **one** canonical export per analysis run.

---

## How to reproduce

```bash
# Single fixture-aligned export (N=3)
python -m observability.eval_stats tests/fixtures/eval/eval_export_sample.jsonl --format text

# JSON for automation / battle report
python -m observability.eval_stats artifacts/eval/smoke_eval_results.jsonl --format json

# Group by run date (timestamp field)
python -m observability.eval_stats path/to/eval_results.YYYYMMDD.jsonl --group-by date --format text

# Append markdown section to this report
python -m observability.eval_stats artifacts/eval/eval_results.latest.jsonl \
  --write-report observability/eval_stats_report.md
```

---

## Limitations

- **Sample size**: N=3 is sufficient for **tooling** verification only, not production threshold lock-in (`min_samples` default 10).
- **Representativeness**: Fixture skews toward `needs_review` (~67%). Real dev/staging distribution may be lower; thresholds must be recomputed.
- **Chat A dependency**: Final P-line sign-off waits on `artifacts/eval/eval_results.*.jsonl` from dev/staging exporter pipeline.

---

## Wave 3 campaign note（2026-05-24 · Chat C）

Answer-side skill 化与 selector 收敛完成后，eval export 批次可包含：

- answer 步 `external_call_count` / `retry_count`（与 retrieve 对称）
- `selector_decision` / `retrieve_fallback`（S2 无 RAG、S3 fallback）

完整战役 Summary 见 `_workflow_upgrade/campaign_wave3_answer_selector_summary.md`。  
CI 实挂（`P+-eval-ci-wire`）仍待下一工单；本 Chat 未改 `.github/workflows`。

---

## Analysis run (fixture sample, 2026-05-23)

```text
ok: True
message: analyzed 3 sample(s); needs_review 66.67%

=== Overall ===
N=3  needs_review=2  ratio=66.67%
pass=1  rows_with_tags=2

=== Tags (row-level appearances) ===
  high_retry: 1 (33.33% of N)
  infra_risk: 1 (33.33% of N)

=== CI: max-needs-review-ratio ===
  suggested range: 0.72 – 0.87
  observed: 66.67%

=== CI: fail-on-tags ===
  infra_risk: fail
  observability_gap: optional_fail

=== Suggested CLI (provisional) ===
  --max-needs-review-ratio 0.87 --fail-on-tags infra_risk
```
