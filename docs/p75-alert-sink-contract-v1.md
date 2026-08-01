# P7.5 Alert Sink Contract v1

> **票**：`P75-G6-alert-sink-contract-v1`  
> **性質**：本地 **真 sink**（file JSONL + stub HTTP）· ≠ Web UI · ≠ 生產 alert · ≠ Phase closure  
> **上游**：`docs/p75-intake-gate-slo-alert-probe-v1.md`（P75-G5 probe；`would_emit` → 本契約實際投遞）  
> **對齊**：`docs/intake-gate-contract-v1.md` · 計劃 `04_Workflows/plans/full-line-to-100-wave-plan-2026-07-13.md`  
> **Schema**：`shared/schemas/p75_alert_sink_event_v1.json`

---

## §0 non_claims

| 禁止宣稱 | 說明 |
|----------|------|
| 本 sink **≠** 生產 alert 已上線 | 無 PagerDuty／Slack／外網真送 |
| 本 sink **≠** Operator Web UI | UI 欄位契約見計劃 Wave 0；實作延後 Wave 4 |
| 本 sink **≠** P7.5 Phase closure | 僅契約／本地投遞增量 |
| 本 sink **≠** 暗部 monitoring 接管 | 與 `alert_event_v1`（gov_core）**分軌**；僅 severity 敘事可對照 |
| 本 sink **≠** 改 Intake Gate 決策 | 不改 `routing/intake_gate_layer_v1.py` |

---

## §1 Goal

1. 定義穩定 envelope：`p75_alert_sink_event_v1`  
2. **file** 模式：append JSONL 至 `outbox/p75_alert_sink/events.jsonl`（可覆寫）  
3. **stub_http** 模式：POST 至本地 stub recorder（預設 in-process；可選 loopback URL）  
4. 可從 P75-G5 probe `alerts[]` 映射並投遞  
5. 回傳穩定 `dict`：`ok`／`message`／`emitted`／`events`／`sink_mode`

---

## §2 Event 形狀（摘要）

```json
{
  "schema_version": "p75_alert_sink_event_v1",
  "event_id": "…",
  "source": "intake_slo_alert_probe_v1",
  "severity": "warn",
  "code": "latency_p95_warn",
  "message": "…",
  "detail": "p95=2500 > 2000",
  "fired_at": "2026-07-13T00:00:00Z",
  "probe_snapshot": { "latency_ms_p95": 2500, "sample_count": 2 },
  "sink": {
    "mode": "file",
    "delivered": true,
    "path": "outbox/p75_alert_sink/events.jsonl",
    "http_status": null,
    "target": null
  }
}
```

**severity 對照**：probe `level=warn|critical` → sink `severity`；暗部 `warning` ≈ `warn`（敘事 only）。

---

## §3 API

```python
from delivery.p75_alert_sink_v1 import emit_alerts, alerts_from_probe_result

emit_alerts(
    alerts,                     # list[dict] with level/code/detail
    *,
    mode="file",                # file | stub_http
    source="intake_slo_alert_probe_v1",
    probe_snapshot=None,
    sink_path_override=None,    # file only
    stub_url=None,              # stub_http; None → in-process recorder
    force_fail=False,           # stub_http test hook
    repo_root=None,
) -> dict
```

---

## §4 CLI

```text
python scripts/run_p75_alert_sink_v1.py --from-probe --mode file --format json
python scripts/run_p75_alert_sink_v1.py --from-probe --mode stub_http --format json
python scripts/run_p75_alert_sink_v1.py --alert-json '[{"level":"warn","code":"demo","detail":"x"}]' --mode file
```

`--from-probe` 會跑 G5 probe（`emit_alert` 語意）並把非空 `alerts[]` 丟進 sink。健康 fixture 無 alert 時 `emitted=0` 且 `ok=true`。

---

## §5 驗收

```text
python -m unittest tests.test_p75_alert_sink_v1 -v
python scripts/run_p75_alert_sink_v1.py --from-probe --mode file --format json
```

---

## §6 UI 欄位（Wave 4 · placeholder · 本票不實作）

| 欄位 | 說明 |
|------|------|
| `sink.last_delivered_at` | 最近一次 delivered |
| `sink.mode` | file／stub_http／（未來 prod） |
| `alerts[]` | 與 probe／sink 對齊 |
| `operator_actions[]` | **placeholder** |
