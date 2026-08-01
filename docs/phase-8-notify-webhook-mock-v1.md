# Phase 8 Notify Webhook Mock v1（P8-T3 mock MVP）

> **性質**：本地探針／契約骨架  
> **票**：`P8-T3-notify-webhook-mock-mvp-v1`  
> **日期**：2026-07-13

---

## non_claims（置頂）

| 本交付 **不是** | 說明 |
|-----------------|------|
| ≠ **prod webhook** | 無真實對外 HTTP；`external_http=false` |
| ≠ **staging／prod URL rollout** | `mode=live` **fail-close** |
| ≠ **P7 adapter 替換** | 不改 `delivery/notification_webhook_adapter_v1.py` |
| ≠ **Phase 8 closure** | mock 綠 ≠ 商業化交付結案 |
| ≠ **Email／Slack／Telegram／SLA** | 計畫 §5 可延後項仍延後 |

---

## 目的

對齊 `04_Workflows/plans/phase-8-commercial-delivery-to-80-plan.md` §2.3／§3 **P8-T3** 的可驗收本地層：

1. `delivery.bundle_ready` mock dispatch（模擬 `delivered_at`）
2. 失敗路徑：retry max 3 → file DLQ
3. DLQ list + mock replay CLI

---

## 模組／CLI

| 路徑 | 用途 |
|------|------|
| `delivery/p8_notify_webhook_mock_v1.py` | mock API |
| `scripts/run_p8_notify_webhook_mock_v1.py` | CLI |
| `outbox/p8_notify_dlq_mock/events.jsonl` | 預設 DLQ（可覆寫） |

```bash
python scripts/run_p8_notify_webhook_mock_v1.py dispatch --case-ref demo_phase
python scripts/run_p8_notify_webhook_mock_v1.py dispatch --case-ref demo_phase --force-fail
python scripts/run_p8_notify_webhook_mock_v1.py list-dlq --format json
python scripts/run_p8_notify_webhook_mock_v1.py replay --event-id <id> --dry-run
python scripts/run_p8_notify_webhook_mock_v1.py replay --event-id <id> --no-dry-run
```

---

## 驗收

```bash
python -m unittest tests.test_p8_notify_webhook_mock_v1 -v
```

---

## 與 P7 webhook 關係

P7 sandbox adapter（retry／HMAC／DLQ env-gate）是**通知主線參考實作**。本票為 **P8 商業化 Notify v1.5 的獨立 mock 命名空間**，供 Operator／計畫缺口閉合，**不**宣稱已接真 Worker 或 prod sink。

真 webhook／prod DLQ replay 另開授權票。

---

## Append · 2026-07-13

真 sandbox／staging／prod 路徑已落地：`docs/phase-8-notify-webhook-v1.md` · 票 `P8-T3-notify-webhook-staging-prod-v1`。  
本 mock 模組仍保留為本地探針；**勿**把 mock 標成 prod-ready。
