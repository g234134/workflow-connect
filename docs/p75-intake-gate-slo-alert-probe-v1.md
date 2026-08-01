# P7.5 Intake Gate — SLO / Alert Probe v1

> **票**：`P75-G5-slo-alert-probe-v1`  
> **性質**：本地最小 SLO／alert **探針**（L-local）· ≠ 生產 alert 配線 · ≠ Grafana · ≠ Phase closure  
> **對齊**：`docs/intake-gate-contract-v1.md` · Dashboard P7.5「UI / SLO / alert 未做」缺口的最小可驗收增量

---

## §0 non_claims

| 禁止宣稱 | 說明 |
|----------|------|
| 本探針 **≠** 生產 alert 已上線 | 無 PagerDuty／Slack webhook 真送 |
| 本探針 **≠** Grafana／Prometheus 儀表板 | 僅 CLI dict 輸出 |
| 本探針 **≠** Intake Gate 決策邏輯變更 | 不改 `routing/intake_gate_layer_v1.py` |
| 本探針 **≠** P7.5 closure／UI | 僅填補 SLO／alert **骨架探針** |

> **延伸（P75-G6）**：實際本地 sink（file／stub HTTP）見 `docs/p75-alert-sink-contract-v1.md`；本探針預設仍不寫外部 sink（僅 `would_emit`）。

---

## §1 Goal

提供可重跑的 **Intake Gate SLO／alert 探針**：

1. 讀取本地 fixture（延遲／決策樣本）  
2. 對照最小閾值（latency_ms、error_rate）  
3. 回傳穩定 `dict`：`ok`／`message`／`slo`／`alerts[]`／`probe_mode`

---

## §2 SLO 閾值（MVP · 本地）

| 指標 | 閾值 | 告警級別 |
|------|------|----------|
| `latency_ms` p95 | ≤ 2000 | `warn` if >2000；`critical` if >5000 |
| `error_rate` | ≤ 0.05 | `warn` if >0.05；`critical` if >0.20 |
| `gate_decision_coverage` | ≥ 1 sample | `warn` if 0 samples |

---

## §3 CLI

```text
python scripts/run_intake_slo_alert_probe_v1.py --fixture tests/fixtures/intake_slo_probe_sample_v1.json --format json
```

預設 `--dry-run`（不寫外部 sink）。`--emit-alert` 僅在 dict 內標記 `would_emit=true`，**不**發外網。

---

## §4 回傳形狀

```json
{
  "ok": true,
  "schema_version": "intake_slo_alert_probe_v1",
  "probe_mode": "dry_run",
  "message": "...",
  "slo": {
    "latency_ms_p95": 120,
    "error_rate": 0.0,
    "sample_count": 3,
    "thresholds": {"latency_ms_p95": 2000, "error_rate": 0.05}
  },
  "alerts": [],
  "would_emit": false,
  "doc": "docs/p75-intake-gate-slo-alert-probe-v1.md"
}
```

---

## §5 驗收

```text
python -m unittest tests.test_intake_slo_alert_probe_v1 -v
python scripts/run_intake_slo_alert_probe_v1.py --format json
```
