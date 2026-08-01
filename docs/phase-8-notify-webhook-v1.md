# Phase 8 Notify Webhook v1（真 sandbox／staging／prod 路徑）

> **票**：`P8-T3-notify-webhook-staging-prod-v1`  
> **日期**：2026-07-13  
> **依賴**：P7 `delivery/notification_webhook_adapter_v1.py` tier／HMAC／allowlist／DLQ

---

## non_claims

| 本交付 **不是** | 說明 |
|-----------------|------|
| ≠ 本 repo 寫入真實 prod URL／金鑰 | 僅讀 env；CLI 不印 secret |
| ≠ SLA／exactly-once | 計畫 §5 → Phase 9 |
| ≠ 取代 P8-T3 mock 探針 | mock 模組仍在；本檔為真 HTTP 路徑 |
| ≠ 自動開啟 prod | 須顯式 `--tier staging|prod` + env gates |

---

## 模組／CLI

| 路徑 | 用途 |
|------|------|
| `delivery/p8_notify_webhook_v1.py` | `dispatch_bundle_ready`／`list_dlq`／`staging_prod_readiness_check` |
| `scripts/run_p8_notify_webhook_v1.py` | CLI |

```powershell
python scripts/run_p8_notify_webhook_v1.py readiness --tier staging
python scripts/run_p8_notify_webhook_v1.py dispatch --case-ref demo_phase --tier sandbox
python scripts/run_p8_notify_webhook_v1.py list-dlq --format json
```

---

## Env gates（staging／prod · 僅列鍵名）

- `GOV_NOTIFICATION_WEBHOOK_ENABLED`
- `GOV_NOTIFICATION_WEBHOOK_URL`
- `GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST`
- `GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST`
- `GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED` + `GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET`
- `GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED`（建議）

Sandbox 仍僅允許 localhost（P7 政策）；staging／prod 須 HTTPS + allowlist + HMAC。

---

## 驗收

```powershell
python -m unittest tests.test_p8_notify_webhook_v1 -v
```
