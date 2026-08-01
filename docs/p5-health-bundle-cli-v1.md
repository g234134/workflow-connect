# P5 Health Bundle CLI v1

> **Ticket**: `P5-HEALTH-BUNDLE-CLI-v1`  
> **CLI**: `scripts/run_p5_health_bundle_cli_v1.py`  
> **Date**: 2026-07-15 · Wave A

---

## Purpose

一入口串起本地 **toolchain health** + **std_case metrics scrape** + **Grafana/JSON stub**，回傳結構化 `dict`（`ok`／`sections`／`message`）。

**non_claims**：≠ 真 Grafana · ≠ PG soak · ≠ prod Prometheus · ≠ DarkOps 接管。

---

## Commands

```powershell
python scripts/run_p5_health_bundle_cli_v1.py --format json
python scripts/run_p5_health_bundle_cli_v1.py --format text
python scripts/run_p5_health_bundle_cli_v1.py --write
python -m unittest tests.test_p5_health_bundle_cli_v1 tests.test_p5_metrics_grafana_stub_v1 -v
```

**Expected**：頂層 `ok: true`；`sections.health.ok` · `sections.metrics.scrape_ok` · `sections.grafana_stub.ok` 皆為 true（本地 fixture 可用時）。

---

## Composition

| Section | Source |
|---------|--------|
| health | `scripts/run_toolchain_health_dashboard.build_toolchain_health`（dry_run） |
| metrics | `export_std_case_metrics_v1` + `get_metrics_text`（Prometheus 文本形狀） |
| grafana_stub | `observability.p5_metrics_grafana_stub_v1.build_grafana_stub` |

既有單入口 stub CLI（`run_p5_metrics_grafana_stub_v1.py`）仍可用；本 bundle 顯式分欄三節，供 operator 一命令驗收。

---

## Phase% proposal (not applied)

| Field | Value |
|-------|-------|
| phase_targets | P5 |
| baseline_pct | 72 |
| proposed_delta_pct | +3 ～ +5 |
| apply_phase_pct | **false** |

---

*P5-HEALTH-BUNDLE-CLI-v1*
