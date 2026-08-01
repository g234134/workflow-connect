# P8.9 Operator Fields Projection v1

> **Ticket**: `P89-W2-narrative-t4-obs-projection-v1` · Wave 2 #2 · 2026-07-13  
> **Goal**：把計劃 §2.2 UI 必讀欄位草案投影成可測、只讀 JSON；並固定敘事：**P8.9-T4 = WD-P7-T2（已落地）**。

---

## Non-claims

| 聲明 | 狀態 |
|------|------|
| 本投影 = Web UI | **否** |
| 本投影 = 重造 webhook adapter | **否** — 只讀既有 sinks |
| T4 未落地／deferred | **否** — T4 ≡ `WD-P7-T2`／`notification_webhook_adapter_v1` |
| 本票授權 Dashboard Phase% 上調 | **否** — `apply_phase_pct=false` · 僅 estimate |

---

## T4 對齊（敘事 SSOT）

| 別名 | 實際票／產物 | 狀態 |
|------|--------------|------|
| **P8.9-T4** HTTP webhook sandbox | **WD-P7-T2** · `delivery/notification_webhook_adapter_v1.py` · registry `webhook_dispatch_v1` | **landed**（勿重造） |
| 仍 deferred | staging／prod allowlist + SLA 敘事 · Wave 4 UI 消費 | 未做 |

---

## UI 必讀欄位（投影鍵）

| Key | Source |
|-----|--------|
| `event_id` | consumer `native_id`（notification stream） |
| `ack_status` | `tracking_status` → `pending_ack`／`acked`／`failed`（checkpoint → `recorded`） |
| `handler_id` | `downstream_ack.handler_id`（若有） |
| `dispatch_registry_hit` | `routing/notification_handlers_v1.yaml` 是否為該 `event_type` 註冊 handler |
| `dlq_flag` | webhook DLQ jsonl（預設 `outbox/notification_dlq/events.jsonl`）是否含同 `event_id` |

---

## API / CLI

```text
delivery.p89_operator_fields_v1.project_operator_fields(case_ref, ...) → dict
python scripts/inspect_p89_operator_fields_v1.py --case-ref demo_phase --format json
python -m unittest tests.test_p89_operator_fields_v1 -v
```

頂層穩定鍵：`ok` · `schema_version=p89_operator_fields_v1` · `read_only` · `case_ref` · `count` · `fields` · `rows[]` · `t4_alignment` · `non_claims`。

---

## Related

- Observability contract：`docs/p8_p89_delivery_observability_contract_v1.md`
- Consumer：`delivery/workflow_event_consumer_v1.py`
- Dispatch registry：`delivery/notification_dispatch_v1.py`
- Webhook（T4）：`delivery/notification_webhook_adapter_v1.py`
