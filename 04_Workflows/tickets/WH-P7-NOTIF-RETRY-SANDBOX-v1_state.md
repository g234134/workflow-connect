# WH-P7-NOTIF-RETRY-SANDBOX-v1 — Ticket State

> Wave-H+1 · sandbox localhost webhook retry loop（env 驅動、預設關閉）  
> 上游：`WH-P7-NOTIF-PROD-policy-v1` §4.6.3 · WD-P7-T2 sandbox adapter

---

## FRAME

### Goal

在 `notification_webhook_adapter_v1` 加入 env 驅動 retry loop（預設 `max_attempts=0` 維持單次 POST），unittest 覆蓋，合約 §4.6.0 `webhook_retry_max_attempts` 標 **partial**。

### AllowedPaths

- `delivery/notification_webhook_adapter_v1.py`
- `tests/test_notification_webhook_dispatch_v1.py`
- `docs/outbox-and-feedback-layer-contract-v1.md`
- 本票 STATE / B_REPORT

---

## STATE

- **overall_status**: `done`
- **current_owner**: orchestrator
- **last_updated**: 2026-06-22 · scribe
- **wave**: Wave-H+1
- **status_by_role**:
  - **Implementer (B)**: done — 2026-06-22
  - **Reviewer (C)**: done — 2026-06-22 · **`accepted_with_gaps`**
  - **Scribe (D)**: done — 2026-06-22

---

## B_REPORT (Implementer)

### §1 變更檔案清單

| 檔案 | 變更 |
|------|------|
| `delivery/notification_webhook_adapter_v1.py` | env 讀取 + retry loop + `webhook_result` 擴充欄位 |
| `tests/test_notification_webhook_dispatch_v1.py` | 新增 `TestNotificationWebhookRetry`（4 cases） |
| `docs/outbox-and-feedback-layer-contract-v1.md` | §4.6.0 / §4.6.3 / Runtime 摘要更新 `partial` |
| `04_Workflows/tickets/WH-P7-NOTIF-RETRY-SANDBOX-v1_state.md` | 本 B_REPORT |

### §2 adapter retry 行為與 env 定案

| env 鍵 | default | 說明 |
|--------|---------|------|
| `GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS` | `0` | `≤0` → 單次 POST（legacy）；`≥1` → 至多 N 次 |
| `GOV_NOTIFICATION_WEBHOOK_RETRY_BASE_DELAY_MS` | `100` | 指數退避起點（ms） |
| `GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_DELAY_MS` | `2000` | 退避上限（ms） |

- 可重試：連線錯誤 / timeout、408、429、5xx
- 不可重試：其他 4xx（400/401/403/404 等）
- 退避：`base * 2^(attempt-1)`，clamp 至 `max_delay_ms`
- 解析失敗：log 一行 warning，safe fallback（attempts→0 或 delay 預設）
- `webhook_result` 新增：`attempt_count`、`retry_exhausted`、`last_error`（與 `error` 同值）；外層 **fail-open 不變**（`ok=True`）

### §3 新增測試

| 測試 | 場景 |
|------|------|
| `test_default_no_retry_env_single_post_only` | AC-1：無 RETRY env → 單 POST + `attempt_count=1` |
| `test_retry_503_then_200_succeeds` | AC-2：`max_attempts=2`，503→200 → `dispatched=True` |
| `test_retry_exhausted_on_persistent_500` | AC-3：穩定 500 → `retry_exhausted=True`，外層 `ok=True` |
| `test_non_retriable_400_no_retry` | 400 只打一次，不進 retry |

### §4 驗證命令

```bash
python -m unittest tests.test_notification_webhook_dispatch_v1 -v
```

僅 retry 子集：

```bash
python -m unittest tests.test_notification_webhook_dispatch_v1.TestNotificationWebhookRetry -v
```

**結果**：16/16 passed（原 12 + 新 4）。

### §5 §4.6.0 更新列（抄錄）

| `webhook_retry_max_attempts` | `0`（單次 POST） | yes（env） | Wave-H | **partial**（sandbox localhost webhook only；無 DLQ；prod/staging URL / HMAC 未實作） |

### §6 阻塞

無。

### §7 skeleton / placeholder

無。

---

## C_REPORT (Reviewer)

- **review_date**: 2026-06-22
- **reviewer_role**: Wave-H+1 Reviewer (C)
- **verdict**: **`accepted_with_gaps`**
- **conclusion**: sandbox env 驅動 retry loop 與票意一致；預設 `max_attempts=0` 維持單次 POST；fail-open 未破壞；`webhook_result` 僅增欄位；合約 §4.6.0 / §4.6.3 已標 **partial** 且仍註明 sandbox-only / 無 DLQ / 無 HMAC / 無 prod URL。缺口：408 / 429 / timeout / 連線錯誤可重試路徑無專測；Windows 全量 suite 偶發 flaky（見 §4 驗證）。

### acceptance_criteria_review

| AC | 票意 | 結果 | 證據 |
|----|------|------|------|
| **AC-1** | 預設行為不變：`GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS` 未設或 `≤0` → 單次 POST | **pass** | `DEFAULT_RETRY_MAX_ATTEMPTS=0`；`_send_http_post_with_retry` 在 `max_attempts<=0` 時 `total_attempts=1`；`test_default_no_retry_env_single_post_only` 綠；既有 `test_webhook_failure_is_fail_open` 仍單次 POST（log `attempts=1`） |
| **AC-2** | 可重試：連線錯誤、timeout、408、429、5xx；不可重試：其他 4xx | **pass**（測試覆蓋 partial） | `_is_retriable_http_result` 邏輯符合 §4.6.3；`test_retry_503_then_200_succeeds`（5xx）、`test_non_retriable_400_no_retry`（4xx）綠；408 / 429 / timeout / URLError **無專測** |
| **AC-3** | fail-open：retry 用盡仍外層 `ok=True` | **pass** | `send_webhook_notification` 失敗分支仍 `ok: True`；`test_retry_exhausted_on_persistent_500`、`test_webhook_failure_is_fail_open` 綠 |
| **AC-4** | `webhook_result` 非破壞性擴充：`attempt_count`、`retry_exhausted`、`last_error` | **pass** | 實際 POST 路徑保留原欄位並新增三欄；`last_error` 與 `error` 同值；dry-run / disabled 路徑未刪欄位（新欄位不出現，向後相容） |
| **§4.6.0** | `webhook_retry_max_attempts` → **partial**；sandbox-only / 無 DLQ / 無 HMAC / 無 prod URL | **pass** | 合約 §4.6.0 列 **partial** 並註明限制；§4.6.3 Runtime 摘要一致；adapter 仍 `_is_safe_sandbox_url` localhost-only |

### impl_consistency_check（vs `WH-P7-NOTIF-PROD-policy-v1` §4.6.3）

| 項目 | 票 / 合約 | 現碼 | 一致？ |
|------|-----------|------|--------|
| default `max_attempts` | `0` 單次 POST | env 缺省 → `0` | ✅ |
| backoff env 鍵 | BASE / MAX delay ms | 三鍵讀取 + parse fallback | ✅ |
| 可重試狀態碼 | 408 / 429 / 5xx + 連線/timeout | `_is_retriable_http_result` | ✅ |
| 不可重試 4xx | 400 等 | 400 測試 + break 邏輯 | ✅ |
| DLQ | 無 | 無 DLQ 寫入 | ✅ |
| HMAC / prod URL | 未實作 | docstring + sandbox URL gate 不變 | ✅ |
| fail-open | dispatch 不阻斷 | 外層 `ok=True` | ✅ |

### §4 驗證（Reviewer 重跑）

```bash
python -m unittest tests.test_notification_webhook_dispatch_v1 -v
# 結果：15/16 passed；test_retry_exhausted_on_persistent_500 首跑 flaky
# （第 2 次 POST WinError 10053 → http_status=None；retry_exhausted 仍 True，ok 仍 True）

python -m unittest tests.test_notification_webhook_dispatch_v1.TestNotificationWebhookRetry -v
# 結果：4/4 passed（含 persistent 500）
```

### blocking_issues

**無 blocking。** 實作可合併；flaky 與缺專測不阻擋 sandbox retry 交付。

### gaps（非 blocking · 不順手修 code）

1. **缺專測**：408、429、`timeout=True`、URLError 可重試分支各一 case（現僅 503 / 500 / 400）。
2. **Windows flaky**：`test_retry_exhausted_on_persistent_500` 在極短 backoff 下偶發連線中止，`http_status` 可為 `None` 而非 `500`；retry 子集重跑可綠。建議後續票用更穩 mock（固定回 500）或略增 delay。

### risk_level

**low** — sandbox localhost only；預設關閉；fail-open 不變；無 secrets / prod URL。

---

## D_REPORT (Scribe)

- **verdict_echo**: Reviewer **`accepted_with_gaps`**（2026-06-22）— AC-1～AC-4 與 §4.6.0 **partial** 對照通過；無 blocking；缺口為 408/429/timeout/連線錯誤缺專測與 Windows 全量 suite 偶發 flaky。
- **delivery_scope**: sandbox localhost webhook **opt-in retry**（`GOV_NOTIFICATION_WEBHOOK_RETRY_*` env）；**default `max_attempts=0`** 維持單次 POST，現網預設行為不變。
- **verification**:
  - Implementer / Reviewer：`tests.test_notification_webhook_dispatch_v1` **16/16**（Reviewer 全量首跑 **15/16**，retry 子集 **4/4** 綠）
  - Scribe 重跑（repo 根 cwd）：**16/16 OK**
- **contract_change**: 合約 §4.6.0 `webhook_retry_max_attempts` **`not_implemented_yet` → `partial`**（sandbox localhost only；無 DLQ；prod/staging URL / HMAC 未實作）；§4.6.3 Runtime 摘要已對齊。
- **deferred**（仍 **not_implemented_yet** 或未升格）:
  - **DLQ** — 失敗事件落盤 / inspect
  - **HMAC** — 簽名發送與驗簽 contract
  - **prod/staging URL tier** — `GOV_NOTIFICATION_WEBHOOK_TIER` + non-localhost allowlist
  - **required CI gate** — `p7-notification-smoke` 仍 advisory · `continue-on-error`
- **progress_entry**: WH-P7-NOTIF-RETRY-SANDBOX-v1 — sandbox-only retry · **`accepted_with_gaps`** · **16/16 OK** · §4.6.0 **partial**。
- **scribe_date**: 2026-06-22 · Wave-H+1 Scribe
