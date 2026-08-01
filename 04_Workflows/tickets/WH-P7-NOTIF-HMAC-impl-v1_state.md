# WH-P7-NOTIF-HMAC-impl-v1 — Ticket State

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Wave-H · **HMAC-SHA256 sender 實作小票（sandbox-only / env gated）**  
> 上游：`WH-P7-NOTIF-HMAC-policy-v1`（`frame_ready`）· `WH-P7-NOTIF-PROD-policy-v1`（§4.6 骨架）  
> 產物：adapter sender 端 HMAC 簽名 + unittest；**不含 receiver 合約、prod URL、HMAC 強制**

---

## FRAME

### handoff header

本票為 **HMAC-SHA256 sender-side 實作小票**：在 `notification_webhook_adapter_v1` 依 env 決定是否簽名；sandbox 預設 off；不啟 prod URL / 不強制 HMAC / 不改 fail-open。

### 從 `WH-P7-NOTIF-HMAC-policy-v1` 擷取之 subset（sender only）

| 規格項 | 本票實作 |
|--------|----------|
| 算法 | HMAC-SHA256 |
| 簽名 header | `X-Gov-Signature-256`（值 `sha256=<hex>`） |
| Timestamp header | `X-Gov-Timestamp`（Unix epoch seconds UTC） |
| 事件識別 header | `X-Gov-Event-Id`（等於 JSON body `event_id`） |
| Signed string | `{timestamp}.{event_id}.{raw_body_utf8}` |
| Env gate | `GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED=1` **且** `GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET` 非空 |
| 簽名失敗 / secret 缺失 | fail-open：log warning，仍發送非簽名 webhook |

**不含**：receiver 驗簽、timestamp 窗口拒絕、重放去重、`Idempotency-Key` header、staging/prod tier gate、HMAC 強制。

### 明確目標

1. adapter 根據 env 決定是否簽名（`HMAC_ENABLED` + secret 雙 gate）。
2. 發送時加上 HMAC header + timestamp + event id（有 `event_id` 時）。
3. unittest 覆蓋 on / off / enabled-but-no-secret 三 scenario。
4. 合約 §4.6.0 `webhook_hmac` → `partial`；§4.6.5 補 sender v1 實作說明。

### Non-Goals

- ❌ **不實作** receiver 驗簽 contract test（→ `WH-P7-NOTIF-HMAC-receiver-contract-v1`）。
- ❌ **不啟用** prod / staging URL tier 或 HMAC 強制（無 `GOV_NOTIFICATION_WEBHOOK_TIER`）。
- ❌ **不送** HTTP `Idempotency-Key` header（仍 future）。
- ❌ **不改** `notification_dispatch_v1` · `notification_gateway_v1` · YAML registry · CI workflow。
- ❌ **不升格** fail-close；整體 dispatch / emit fail-open 不變。
- ❌ **不寫** secret 實體值或非 localhost URL 範例。

### AllowedPaths

- `delivery/notification_webhook_adapter_v1.py`
- `tests/test_notification_webhook_dispatch_v1.py`
- `docs/outbox-and-feedback-layer-contract-v1.md`（§4.6.0 · §4.6.5 小改）
- `04_Workflows/tickets/WH-P7-NOTIF-HMAC-impl-v1_state.md`

### BlockedPaths

- `delivery/notification_dispatch_v1.py` · `delivery/notification_gateway_v1.py`
- `routing/notification_handlers_v1.yaml`
- `.github/workflows/**`
- P8.5 / P9 相關檔案

---

## STATE

- **overall_status**: `validated`
- **current_owner**: scribe
- **next_action**: Orchestrator 裁決 `WH-P7-NOTIF-HMAC-receiver-fixtures-v1` / `sample-impl-v1` 開票順序
- **last_updated**: 2026-06-23 · reviewer + scribe (C/D)
- **wave**: Wave-H · P7 notification HMAC sender impl
- **status_by_role**:
  - **Orchestrator (A)**: pending
  - **Implementer (B)**: done — 2026-06-22
  - **Reviewer (C)**: done — 2026-06-23 · **`accepted_with_gaps`**
  - **Scribe (D)**: done — 2026-06-23 · D_REPORT 收口

---

## B_REPORT

### changed_files

| 檔案 | 變更 |
|------|------|
| `04_Workflows/tickets/WH-P7-NOTIF-HMAC-impl-v1_state.md` | 新增 |
| `delivery/notification_webhook_adapter_v1.py` | HMAC env gate + sender 簽名 |
| `tests/test_notification_webhook_dispatch_v1.py` | `TestNotificationWebhookHmac` 三 scenario |
| `docs/outbox-and-feedback-layer-contract-v1.md` | §4.6.0 · §4.6.5 impl_status / sender note |

### env 行為總結（on/off）

| 條件 | 行為 |
|------|------|
| `HMAC_ENABLED` 未設 / `0` | **不簽名**（預設；與改動前一致） |
| `HMAC_ENABLED=1` 且 secret 非空 | **簽名**：附加 `X-Gov-Signature-256` · `X-Gov-Timestamp` · `X-Gov-Event-Id` |
| `HMAC_ENABLED=1` 且 secret 空 | **不簽名**；log warning；仍 fail-open 發送 |
| env 解析失敗 | 視為 disabled；log warning |

Env 鍵：`GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED` · `GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET` · `GOV_NOTIFICATION_WEBHOOK_HMAC_HEADER`（default `X-Gov-Signature-256`）· `GOV_NOTIFICATION_WEBHOOK_TIMESTAMP_HEADER`（default `X-Gov-Timestamp`）· `GOV_NOTIFICATION_WEBHOOK_EVENT_ID_HEADER`（default `X-Gov-Event-Id`）。

### 新增測試 scenario

| TestCase | Scenario |
|----------|----------|
| `test_hmac_disabled_by_default_no_signature_headers` | 預設無 HMAC env → 無簽名 header |
| `test_hmac_enabled_with_valid_secret_adds_headers_and_digest` | enabled + secret → header 存在且 digest 可驗算 |
| `test_hmac_enabled_missing_secret_fail_open_unsigned` | enabled + 空 secret → 不簽名、仍 200、warning log |

### §4.6.0 `webhook_hmac` impl_status

**`partial`** — sandbox-only sender-side HMAC-SHA256（env gated；default off）；receiver contract / prod URL / DLQ / HMAC 強制仍 `not_implemented_yet`。

### 驗證

```bash
python -m unittest tests.test_notification_webhook_dispatch_v1 -v
```

- **exit code**: 0
- **tests**: 19/19 OK（含 3 個新增 HMAC scenario；既有 16 個 regression 仍綠）

---

## C_REPORT

- **review_date**: 2026-06-23
- **reviewer_role**: P7 sandbox HMAC sender Reviewer (C)
- **verdict**: **`accepted_with_gaps`**
- **verification**: `python -m unittest tests.test_notification_webhook_dispatch_v1 -v` → **39/39 OK**（含 HMAC on/off/missing-secret 三 scenario + 既有 regression）
- **conclusion**: sender HMAC env gate · signed string · fail-open unsigned 與 §4.6.5.1 · adapter 現碼一致；sandbox default off 不退化。
- **gaps（non-blocking）**: receiver verification / fixtures / staging-prod mandatory gate 仍 **`not_implemented_yet`**（→ receiver-contract · fixtures · HMAC-prod-impl 票）。

---

## D_REPORT

- **handoff_date**: 2026-06-23
- **from**: P7 sandbox HMAC sender impl（`validated` · Reviewer C `accepted_with_gaps`）
- **to**: Orchestrator（receiver fixtures / sample-impl 衍伸票）
- **notes**: 本票 **sandbox-only sender**；勿將 sandbox opt-in HMAC 誤讀為 staging/prod mandatory。
