# P5 Metrics · Grafana JSON Stub Contract (v1)

> **Ticket**: `P5-metrics-grafana-stub-v1` · Wave 1 · P5  
> **Implementation**: `observability/p5_metrics_grafana_stub_v1.py` · CLI `scripts/run_p5_metrics_grafana_stub_v1.py`  
> **Schema**: `shared/schemas/p5_metrics_grafana_stub_v1.json`  
> **Date**: 2026-07-13

---

## Non-claims（置頂）

| 本契約 **不是** | 說明 |
|-----------------|------|
| ≠ **Grafana** 已部署／已接資料源 | 僅本地 JSON 對照 stub |
| ≠ **PG soak** 已跑通 | soak 仍見 `docs/grafana-pg-soak-deferred-index-v1.md` Deferred |
| ≠ **Web UI**／Operator 面板 | UI → 全線計劃 Wave 4 |
| ≠ **P5 Phase closure**／擅自上調 Dashboard % | stub 綠 ≠ 結案；`apply_phase_pct=false` |
| ≠ 暗部 `/monitoring/*` 接管或改 `alert_event_v1` | `alert_budget_summary` 僅敘事對齊 severity 語意 |
| ≠ 重寫 MP-METRICS／toolchain health | **只讀聚合**既有輸出 |

---

## 1. Purpose

把 Wave 4 Grafana／Operator **必讀欄位**凍成一份可重跑的本地 JSON：

| 欄位（計劃 §2.3） | 本 stub 路徑 |
|------------------|--------------|
| `health.ok` | `health.ok`（來自 `toolchain_health_v1`） |
| `metrics.scrape_ok` | `metrics.scrape_ok`（來自 MP-METRICS Prometheus 文字形狀） |
| `alert_budget_summary` | `alert_budget_summary`（可選掃 P75 sink；否則零值敘事 stub） |

**位階**

| 文件 | 角色 |
|------|------|
| **本檔** | stub 契約 SSOT |
| `docs/toolchain-health-dashboard-v1.md` | health 來源 |
| `docs/fleet-metrics-dashboard-operator-v1.md` | metrics CLI／HTTP 讀法 |
| `docs/grafana-pg-soak-deferred-index-v1.md` | 真 Grafana／PG soak deferred |
| `observability/dashboard/dashboard_metrics_v1.json` | 暗部 monitoring 面板 hint（旁路；本 stub 不取代） |

---

## 2. Schema shape (`p5_metrics_grafana_stub_v1`)

```json
{
  "schema_version": "p5_metrics_grafana_stub_v1",
  "ok": true,
  "mode": "local_stub",
  "generated_at": "2026-07-13T00:00:00Z",
  "case_ref": "demo_phase",
  "health": {
    "ok": true,
    "source": "toolchain_health_v1",
    "sections_ok": 3,
    "aggregated_health_score": 0.75,
    "gate_class": "optional"
  },
  "metrics": {
    "scrape_ok": true,
    "source": "std_case_metrics_v1",
    "exporter_status": 200,
    "has_error_comment": false,
    "prometheus_line_count": 12,
    "std_case_metrics_v1": {}
  },
  "alert_budget_summary": {
    "source": "p75_alert_sink_scan|narrative_stub",
    "warn_count": 0,
    "critical_count": 0,
    "total_events": 0,
    "note": "severity narrative aligned to alert_event_v1; ≠ dark-ops takeover"
  },
  "grafana_read_hints": [
    {"field": "health.ok", "panel_role": "stat"},
    {"field": "metrics.scrape_ok", "panel_role": "stat"},
    {"field": "alert_budget_summary", "panel_role": "table"}
  ],
  "artifact_path": null,
  "doc": "docs/p5-metrics-grafana-stub-contract-v1.md",
  "message": "local grafana stub assembled"
}
```

---

## 3. Sources（只讀）

| Block | Upstream | Failure policy |
|-------|----------|----------------|
| `health` | `scripts.run_toolchain_health_dashboard.build_toolchain_health(dry_run=True)` | 失敗 → `health.ok=false` · 頂層可 `ok=false` |
| `metrics` | `scripts.metrics_http_endpoint_v1.get_metrics_text` + exporter dict | 含 `# error:` → `scrape_ok=false` |
| `alert_budget_summary` | 可選讀 `outbox/p75_alert_sink/events.jsonl`；缺檔 → 零值 `narrative_stub` | 永不崩潰 |

---

## 4. CLI

```powershell
python scripts/run_p5_metrics_grafana_stub_v1.py --format json
python scripts/run_p5_metrics_grafana_stub_v1.py --case-ref demo_phase --format json --write
# → artifacts/p5_metrics/grafana_stub.latest.json
```

| Flag | Default | 說明 |
|------|---------|------|
| `--case-ref` | `demo_phase` | metrics scrape case |
| `--format` | `json` | `json` \| `text` |
| `--write` | off | 寫入 `artifacts/p5_metrics/` |
| `--no-write` | on（與 `--write` 互斥時以顯式為準） | 只 stdout |
| `--alert-sink` | `outbox/p75_alert_sink/events.jsonl` | 可選 override（相對 repo） |

---

## 5. Verification

```powershell
python -m unittest tests.test_p5_metrics_grafana_stub_v1 -v
python scripts/run_p5_metrics_grafana_stub_v1.py --format json
```

---

## 6. Wave 4 handoff（placeholder）

Grafana／Operator UI **應讀**本 stub 的 `health`／`metrics`／`alert_budget_summary`；**不得**把本檔視為已部署 Grafana 證據。真面板／PG soak 另開 infra 票。
