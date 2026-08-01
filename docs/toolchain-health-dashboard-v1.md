# Toolchain Health Dashboard v1

> **Ticket**: WB-T4 · agent-lines-ci-and-metrics-dashboard-v1  
> **Implementation**: `scripts/run_toolchain_health_dashboard.py`  
> **Date**: 2026-06-11  
> **Status**: offline read-only dashboard — **optional** class per WA-T3 P3.5; **does not** block PR merge

---

## 1. Purpose

One-command **toolchain health summary** (JSON + Markdown) merging:

| Section | Source |
|---------|--------|
| `agent_ci` | Latest `outbox/agent_ci/*_ci_summary.json` (W10-T1) |
| `metrics_summary` | `outbox/agent_metrics/metrics_summary.json` (W10-T2) |
| `monthly_report_head` | Latest `outbox/agent_metrics/monthly_report_*.md` or synthetic head from metrics (W11-T3) |
| `fixture_maturity_tiers` | Merged from metrics + CI `by_fixture_maturity` (W12-T2) |
| `catalog_health` | `tools/tabular_tool_catalog_v1.json` + `tools/non_tabular_tool_catalog_v1.json` (WB-T1) |
| `wf_status_summary` | Optional read-only `artifacts/wf/wf_status_summary.latest.json` (Wave B observability) |

**Gate classification (WA-T3 alignment)**

- `gate_class`: `optional`
- `blocks_mainline`: `false`
- Not a PR required check; does not modify `eval-gate-ci.yml` or `core-agent-smoke.yml`

---

## 2. CLI usage

```bash
# JSON to stdout (AC-1); default dry-run reads outbox only
python scripts/run_toolchain_health_dashboard.py --format json

# Write artifacts (AC-4)
python scripts/run_toolchain_health_dashboard.py --format json
# → artifacts/toolchain/toolchain_health.latest.json
# → artifacts/toolchain/toolchain_health.latest.md

# Explicit dry-run (default): never triggers agent CI suite (AC-3)
python scripts/run_toolchain_health_dashboard.py --dry-run --no-write

# Optional wf_status_summary block (AC-9)
python scripts/run_toolchain_health_dashboard.py --include-wf-status --format json

# Non-dry-run: may invoke run_agent_lines_ci_suite (optional hook only)
python scripts/run_toolchain_health_dashboard.py --no-dry-run
```

| Flag | Default | Description |
|------|---------|-------------|
| `--format` | `text` | `json` or `text` (Markdown) on stdout |
| `--dry-run` / `--no-dry-run` | **`--dry-run` (on)** | Read outbox only vs optional CI suite hook |
| `--include-wf-status` | **off** | Include `wf_status_summary` section when artifact exists |
| `--no-write` | off | Skip `artifacts/toolchain/` writes |
| `--output-dir` | `artifacts/toolchain` | Artifact directory |

### 2.1 Default gate behavior（Phase 5）

| 行为 | 默认 | 如何开启 | 如何关闭 |
|------|------|----------|----------|
| Read-only assembly | **`--dry-run`** | 默认即 on | `--no-dry-run`（可触发 `run_agent_lines_ci_suite` hook） |
| PR / merge block | **off** | 需 WC-PRE-06 批文 + 制度修订 | N/A — 本 runner 不接入 required CI |
| `gate_class` in JSON | `optional` | 代码常量 | 批文前不得改为 `mandatory` |
| Artifact write | **on** | 默认写入 `artifacts/toolchain/` | `--no-write` |
| wf_status block | **off** | `--include-wf-status` | 省略 flag |

**与 Phase 5 关系**：health dashboard 提供 **offline observability skeleton**；`aggregated_health_score` 仅作 Progress / Scribe 引用，**不**驱动 Phase% 变更。

---

## 3. Output schema (`toolchain_health_v1`)

### 3.1 Top-level keys

| Key | Type | Notes |
|-----|------|-------|
| `ok` | bool | `true` when **≥3** core sections have `status=ok` (`sections_ok >= 3`); not a prod SLA |
| `schema_version` | str | Always `toolchain_health_v1` |
| `generated_at` | str | UTC ISO8601 (`…Z`) assembly timestamp |
| `message` | str | Human summary incl. `sections_populated` and `aggregated_health_score` |
| `gate_class` | str | Always `optional` (WA-T3 / P3.5 alignment) |
| `blocks_mainline` | bool | Always `false` — **does not** block PR merge |
| `aggregated_health_score` | int | 0–100 heuristic weighted sum; **not** SLA / SLO |
| `sections_populated` | int | Core sections with `status` in `{ok, degraded}` (max 5) |
| `sections_ok` | int | Core sections with `status=ok` (max 5); drives top-level `ok` |
| `sections` | object | Per-block detail (see §3.2) |
| `dry_run` | bool | `true` = read outbox only; `false` = may have invoked agent CI suite hook |
| `output_paths` | object | `{json, markdown}` repo-relative paths when `--no-write` not set |

Section `status` values: `ok` · `degraded` · `missing` (`wf_status_summary` when not requested).

### 3.2 Section blocks (`sections.*`)

Each section includes **`status`**, **`ok`**, **`message`**; optional **`source_path`**.

| Section key | Populated when | Key fields (beyond meta) |
|-------------|----------------|---------------------------|
| `agent_ci` | Latest `outbox/agent_ci/*_ci_summary.json` | `suite_id`, `scope`, `scopes_run`, `tabular_ok`, `non_tabular_ok`, `by_fixture_maturity`, `written_at`, `schema_version` |
| `metrics_summary` | `outbox/agent_metrics/metrics_summary.json` | `aggregate.{total_runs,successful_runs,failed_runs,error_rate,checkpoint_a_trigger_rate,checkpoint_b_trigger_rate}`, `by_source`, `by_fixture_maturity`, `runs_parsed` |
| `monthly_report_head` | Latest `monthly_report_*.md` or synthetic from metrics | `month`, `headlines[]`, `report_path` |
| `fixture_maturity_tiers` | Merge of metrics + CI maturity buckets | `tiers[]` → `{tier, metrics_total_runs, metrics_error_rate, ci_passed, ci_total}`, `tier_count` |
| `catalog_health` | Tabular + NT catalog JSON | `tabular_tool_count`, `non_tabular_tool_count`, `total_tool_count`, `*_catalog_revision`, `stale_revision`, `revision_aligned`, `expected_catalog_revision` |
| `wf_status_summary` | Optional `--include-wf-status` | `gate_sample_count`, `needs_review_ratio`, `index_cases_count`, `trace_hit_rate`, `generated_at` |

### 3.3 Phase 5 dashboard alignment

| P5 指标（见 `wave-progress-dashboard-skeleton-v1.md` §6） | JSON 路径 |
|----------------------------------------------------------|-----------|
| `P5-HEALTH-DASH` | full payload |
| `P5-HEALTH-SCORE` | `aggregated_health_score` |
| `P5-HEALTH-SECTIONS` | `sections_populated` / `sections_ok` |
| `P5-GATE-CLASS` | `gate_class` + `blocks_mainline` |

Phase% **不在此 runner 输出** — Governance-only per Dashboard SSOT.

### 3.4 Extension slot（新增健康检查）

新增检查 **MUST**：

1. 在 `run_toolchain_health_dashboard.py` 增加 `load_*_section()` + 注册到 `build_toolchain_health()` `sections` dict。
2. 若属 core 观测：加入 `_CORE_SECTIONS` 并更新 `compute_aggregated_health_score` weights。
3. 更新本 spec §3.2 表 + `tests/test_toolchain_health_dashboard_v1.py`。
4. 可选：在 `routing/toolchain_smoke_matrix_v1.yaml` 增加 `TS-*` 条目（`gate_class: optional`）。

**禁止** ad-hoc 顶层键不文档化 · 禁止默认 `gate_class=mandatory`。

---

## 4. Degraded / missing data behavior

- Empty `outbox/agent_ci/` → `agent_ci.status = degraded` (not overall `ok` without other signals).
- Missing `metrics_summary.json` → `metrics_summary.status = degraded`.
- Missing monthly report → synthetic head from metrics when possible; else `degraded`.
- Missing wf artifact with `--include-wf-status` → `wf_status_summary.ok = false`; **does not** crash dashboard.
- Tolerant parsing of `metrics_summary` additive schema drift (extra keys ignored).

---

## 5. Observability

| Channel | Behavior |
|---------|----------|
| **logs / artifacts** | Writes `artifacts/toolchain/toolchain_health.latest.json` |
| **metrics** | Consumes `outbox/agent_metrics/metrics_summary.json`; emits `aggregated_health_score` |
| **traces** | Merges `case_ref` / `fixture_maturity` / run modes from CI + metrics; no mandatory `trace_id` |

Does **not** write `gov-trace-v2`.

---

## 6. Cross-references

| Doc | Relationship |
|-----|--------------|
| `docs/agent-lines-ci-suite-v1.md` | CI summary source shape |
| `docs/agent-lines-metrics-and-monitoring-v1.md` | Metrics scan roots + schema |
| `docs/phase3-5-cost-model-governance-contract-v1.md` | Optional gate class (`OG-*`) |
| `docs/toolchain-observability-governance-upgrade-v1.md` | WC-PRE-06 治理升格 proposal（§9） |
| `docs/phase6-int-regression-gate-contract-v1.md` | Appendix: Tool-chain optional smoke matrix |
| `docs/wave-progress-dashboard-skeleton-v1.md` | P5 指标槽 · Dashboard 双轨权责 |
| `docs/smoke-and-regression-contract-v1.md` | MP/MC/CI smoke（与 health 分轨） |
| `docs/tool-catalog-and-selector-contract-v1.md` | `catalog_tool_count` / revision SSOT |
| `observability/wf_status_summary.py` | Optional wf block assembler |

---

## 7. Verification

```bash
python -m unittest tests.test_toolchain_health_dashboard_v1 -v
python scripts/run_toolchain_health_dashboard.py --format json --dry-run
```

---

## 8. Non-scope

- No Prometheus / Grafana / external APM
- No PR required-check integration
- No modification to `analyze_agent_lines_metrics.py` schema
- No Slack / PagerDuty alerting

---

## 9. Governance upgrade proposal (WC-PRE-06)

> **現況**：本 dashboard 為 **L0 · optional · offline** gate（`gate_class=optional` · `blocks_mainline=false`）；**非** PR required check · **非** SLA。

**升格路徑設計稿**（doc-only · 不含 CI 實作）：

- `docs/toolchain-observability-governance-upgrade-v1.md` — L0 optional → L1 PR optional → L2 PR required 分階段路徑、`OG-TOOLCHAIN-HEALTH` 提案行、hooks 清單、rollback playbook、`approval_status` 批文欄位

在 `approval_status` 獲批前，本檔 §1–§8 行為與 gate 分類**不變**。

---

**Related**: WC-C1-01 local gaps quickview (`scripts/run_toolchain_local_gaps_quickview.py` · `docs/toolchain-local-gaps-quickview-v1.md`) can be used alongside this dashboard as a developer-facing auxiliary tool; it does not change dashboard gate semantics.

---

*TOOLCHAIN-HEALTH-DASHBOARD-v1 · WB-T4 · 2026-06-11*
