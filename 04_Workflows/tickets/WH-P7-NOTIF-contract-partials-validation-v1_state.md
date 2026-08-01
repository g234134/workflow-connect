# WH-P7-NOTIF-contract-partials-validation-v1 — Ticket State

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Wave-H+1 · **P7 retry + HMAC `impl_status=partial` 合約驗證票（doc-only）**  
> 上游：`WH-P7-NOTIF-RETRY-SANDBOX-v1`（done）· `WH-P7-NOTIF-HMAC-impl-v1`（impl_done）· `WH-P7-NOTIF-PROD-policy-v1`（design_accepted）  
> 產物：合約 §4.6.0 / §4.6.3 / §4.6.5 與現碼一致性審計；**零程式、零 CI、零其他票、零 Progress 變更**

---

## FRAME

本票為 **P7 通知鏈 partial 能力合約一致性驗證**（Reviewer-only · doc-only）。不修改任何 code / tests / workflows / docs 正文 / 其他票檔 / Progress。

須確認三件事：

1. **Retry partial**：sandbox-only、default=0 維持單次 POST、合約 §4.6.0 / §4.6.3 描述與 `notification_webhook_adapter_v1` + `TestNotificationWebhookRetry` 一致。
2. **HMAC partial**：sender-only、env gated（enabled + secret）、sandbox-only（localhost URL gate 不變）、合約 §4.6.5 sender v1 描述與 adapter + `TestNotificationWebhookHmac` 一致。
3. **Prod 級能力仍 `not_implemented_yet`**：DLQ / prod-staging URL tier / receiver HMAC 驗簽 / allowlist 等仍標未實作；FRAME 與 §4.6.5 提及的後續票號（如 `WH-P7-NOTIF-HMAC-receiver-contract-v1`）reference 正確。

### AllowedPaths

- `04_Workflows/tickets/WH-P7-NOTIF-contract-partials-validation-v1_state.md`（本票）

### BlockedPaths

- 任何其他票檔 · `delivery/**` · `tests/**` · `docs/**` · `.github/workflows/**` · `04_Workflows/00_Agent_Work_Progress.md`

---

## STATE

- **overall_status**: `validated`
- **current_owner**: orchestrator
- **next_action**: 可開後續票（HMAC receiver contract · DLQ · prod URL）；§4.6.6 env 表 `HMAC_SECRET` impl_status 與 §4.6.7 票號索引可由 Scribe 小票對齊（非 blocking）
- **last_updated**: 2026-06-22 · reviewer (C)
- **wave**: Wave-H+1 · P7 partial contract validation
- **status_by_role**:
  - **Orchestrator (A)**: pending — 裁決後續票開立順序
  - **Implementer (B)**: n/a — 本票 doc-only 驗證
  - **Reviewer (C)**: done — 2026-06-22 · **`accepted`**
  - **Scribe (D)**: done — 2026-06-22（本票自包含收口；未改 Progress）

---

## B_REPORT (Reviewer · contract vs impl cross-check)

> **範圍聲明**：本票僅檢查合約與實作一致性，**不修改**任何 code / tests / workflows / docs / 其他票 / Progress。

### A. Retry partial

| 檢查項 | 合約 / 票 | 現碼 / 測試 | 結果 |
|--------|-----------|-------------|------|
| §4.6.0 `webhook_retry_max_attempts` `impl_status` | **`partial`**（§4.6.0 L324） | `WH-P7-NOTIF-RETRY-SANDBOX-v1` B_REPORT §5 抄錄一致 | ✅ |
| 描述：sandbox localhost only / 無 DLQ / default=0 單次 POST | 「sandbox localhost webhook only；無 DLQ；prod/staging URL / HMAC 未實作」；§4.6.3 Runtime 摘要同 | adapter docstring L10–12；`_is_safe_sandbox_url` 仍 localhost/127.0.0.1 only；無 DLQ 寫入 | ✅ |
| env 讀取與 retry 條件 | `GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS` default `0`；BASE/MAX delay ms；可重試 408/429/5xx+連線/timeout；其他 4xx 不重試 | `DEFAULT_RETRY_MAX_ATTEMPTS=0`；`_get_retry_config` 三鍵；`max_attempts<=0` → `total_attempts=1`；`_is_retriable_http_result` 邏輯符合 | ✅ |
| tests 四 case 覆蓋 | default=0 / 503→200 / 穩定 500 / 4xx 不重試 | `TestNotificationWebhookRetry` 四測試均存在且語意對應：`test_default_no_retry_env_single_post_only` · `test_retry_503_then_200_succeeds` · `test_retry_exhausted_on_persistent_500` · `test_non_retriable_400_no_retry` | ✅ |

**Retry partial 一句結論**：合約 §4.6.0/§4.6.3 之 **`partial`** 標記與 adapter env 驅動 retry（default=0 單次 POST、sandbox localhost only、無 DLQ）及四個 retry unittest 完全對齊。

**非 blocking 缺口**（沿用 RETRY-SANDBOX C_REPORT）：408 / 429 / timeout / URLError 可重試分支無專測；全量 suite Windows 偶發 flaky。

---

### B. HMAC partial

| 檢查項 | 合約 / 票 | 現碼 / 測試 | 結果 |
|--------|-----------|-------------|------|
| §4.6.0 `webhook_hmac` `impl_status` | **`partial`**（§4.6.0 L323） | `WH-P7-NOTIF-HMAC-impl-v1` B_REPORT §4.6.0 抄錄一致 | ✅ |
| §4.6.5 sender 描述含 env gate | `GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED=1` **且** `HMAC_SECRET` 非空；預設 off | `_should_apply_hmac_signature()` 雙 gate；enabled+空 secret → warning + 不簽名 | ✅ |
| 簽名演算法 | HMAC-SHA256；`sha256=<hex>` | `_compute_hmac_sha256_hex` + header `sha256={digest_hex}` | ✅ |
| header 名稱與 timestamp / event id | `X-Gov-Signature-256` · `X-Gov-Timestamp`（epoch seconds）· `X-Gov-Event-Id` | `DEFAULT_HMAC_*` 常數；可 env override header 名；signed string `{timestamp}.{event_id}.{raw_body_utf8}` | ✅ |
| sandbox-only、prod URL / receiver 未實作 | sender v1 sandbox-only default off；**Receiver contract** `not_implemented_yet` → `WH-P7-NOTIF-HMAC-receiver-contract-v1` | 無 tier gate；`_is_safe_sandbox_url` 不變；無 receiver 驗簽 | ✅ |
| tests 覆蓋 disabled / enabled+secret / enabled+secret 缺失 fail-open | 三 scenario | `test_hmac_disabled_by_default_no_signature_headers` · `test_hmac_enabled_with_valid_secret_adds_headers_and_digest`（含 digest 驗算）· `test_hmac_enabled_missing_secret_fail_open_unsigned`（warning log + 仍 200） | ✅ |

**HMAC partial 一句結論**：合約 §4.6.0/§4.6.5 sender v1 之 **`partial`** 標記與 adapter env-gated HMAC-SHA256（default off、sandbox-only、fail-open）及三個 HMAC unittest 完全對齊；receiver / prod 強制仍正確標 `not_implemented_yet`。

---

### C. prod 能力仍 `not_implemented_yet`

| policy_item / 能力 | §4.6 位置 | impl_status | 現碼對照 | 一致？ |
|--------------------|-----------|-------------|----------|--------|
| `webhook_dlq_enabled` | §4.6.0 L325 · §4.6.4 | **not_implemented_yet** | adapter docstring L20「No DLQ」；無 DLQ 路徑 | ✅ |
| `webhook_url_tier` (prod/staging) | §4.6.0 L322 · §4.6.6 | prod tier **not_implemented_yet** | 無 `GOV_NOTIFICATION_WEBHOOK_TIER` / allowlist 讀取 | ✅ |
| `GOV_NOTIFICATION_WEBHOOK_TIER` | §4.6.6 env 表 L360 | **not_implemented_yet** | 程式未讀取 | ✅ |
| `GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST` | §4.6.6 env 表 L361 | **not_implemented_yet** | 程式未讀取 | ✅ |
| Receiver HMAC 驗簽 | §4.6.5 L350 | **not_implemented_yet** | adapter docstring L21；無驗簽邏輯 | ✅ |
| HTTP `Idempotency-Key` header | §4.6.5 L348 | **not_implemented_yet** | `_send_http_post` 未送該 header | ✅ |
| HMAC prod 強制 / tier gate | §4.6.0 L323 註 | receiver / prod 強制 **not_implemented_yet** | 無 staging/prod HMAC 強制 | ✅ |

**後續票 reference 對照**

| 合約 / FRAME 提及 | 實際票檔狀態 | 備註 |
|-------------------|--------------|------|
| `WH-P7-NOTIF-HMAC-receiver-contract-v1`（§4.6.5 L350） | `WH-P7-NOTIF-HMAC-policy-v1` FRAME §5 已列；票檔待開 | ✅ reference 正確 |
| `WH-P7-NOTIF-RETRY-SANDBOX-v1` | done · `accepted_with_gaps` | ✅ 已交付 partial retry |
| `WH-P7-NOTIF-HMAC-impl-v1` | impl_done · C pending | ✅ sender partial 已落地 |
| §4.6.7 舊索引 `WH-P7-NOTIF-RETRY-v1` / `WH-P7-NOTIF-HMAC-v1` | 實際已拆分為 RETRY-SANDBOX / HMAC-impl / HMAC-receiver-contract | ⚠️ **非 blocking 文檔 staleness**（§4.6.7 未同步新票號） |

**非 blocking 文檔缺口**：§4.6.6 env 表 L362 `GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET` 仍標 **`not_implemented_yet`**，但 sender partial 已透過該 env 讀取 secret；與 §4.6.0 `webhook_hmac` **partial** 語意略不一致，建議 Scribe 小票將該列改為 **partial**（sender read-only）或加 footnote。不阻擋本驗證票 `validated`。

---

### 驗證方法

- 只讀對照：`docs/outbox-and-feedback-layer-contract-v1.md` §4.6.0 / §4.6.3 / §4.6.5 / §4.6.6
- 只讀對照：`delivery/notification_webhook_adapter_v1.py`
- 只讀對照：`tests/test_notification_webhook_dispatch_v1.py`（`TestNotificationWebhookRetry` 4 cases · `TestNotificationWebhookHmac` 3 cases）
- 上游票：`WH-P7-NOTIF-RETRY-SANDBOX-v1` · `WH-P7-NOTIF-HMAC-impl-v1` · `WH-P7-NOTIF-PROD-policy-v1`

### blocking_issues

**無 blocking。** retry partial 與 HMAC partial 合約描述與現碼一致；prod 級能力仍正確標 `not_implemented_yet`。

---

## C_REPORT (Reviewer)

- **review_date**: 2026-06-22
- **reviewer_role**: P7 Contract Reviewer (C)
- **verdict**: **`accepted`**
- **conclusion**: retry partial + HMAC partial 已對齊 — §4.6.0 `webhook_retry_max_attempts` 與 `webhook_hmac` 均為 **partial**，sandbox-only / default-off 語意與 adapter + unittest 一致；DLQ / prod URL / receiver HMAC 仍 **not_implemented_yet**。

---

## D_REPORT (Scribe · 本票自包含收口)

- **verdict_echo**: Reviewer **`accepted`**（2026-06-22）— P7 partial 能力合約驗證通過；無 blocking。
- **dependency_note**: P7 partial 能力合約已更新（retry + HMAC sender），可作為後續 **HMAC receiver contract** / **DLQ** / **prod URL** 票的依賴基線。
- **deferred_doc_touch**（非本票 scope）：§4.6.6 `HMAC_SECRET` env 列 impl_status 對齊；§4.6.7 票號索引同步 RETRY-SANDBOX / HMAC-impl 拆分。
- **progress_entry**: 本票 doc-only；**未** append `00_Agent_Work_Progress.md`（依任務邊界）。
