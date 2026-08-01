# WH-P7-NOTIF-DLQ-impl-v1 — Ticket State

> Phase：Wave-H+1 · **P7 prod 線** · webhook DLQ 落盤實作  
> 上游：`WH-P7-NOTIF-DLQ-v1`（設計 + §4.6.4 合約）· `WH-P7-NOTIF-RETRY-SANDBOX-v1`  
> 範圍：adapter retry 失敗路徑 append DLQ jsonl + unittest；**不改** retry policy / dispatch / gateway

---

## STATE

- **overall_status**: `validated`
- **current_owner**: done
- **next_action**: 無 — DLQ 落盤 partial 已 validated；inspect CLI 見 `WH-P7-NOTIF-DLQ-inspect-cli-impl-v1`；合約 env 表見 `WH-P7-NOTIF-contract-doc-sync-v1`（DLQ 段）
- **last_updated**: 2026-06-22 · scribe (D) — P7 DLQ 線 closure
- **wave**: Wave-H+1 · P7 prod line · notification DLQ impl
- **status_by_role**:
  - **Orchestrator (A)**: done — 票 scope 與 FRAME 對齊
  - **Implementer (B)**: done — adapter DLQ append + unittest
  - **Reviewer (C)**: done — accepted_with_nits（見 C_REPORT）
  - **Scribe (D)**: done — Progress append · 2026-06-22 P7 DLQ 收口

---

## B_REPORT

- **implementer_date**: 2026-06-22
- **scope**: adapter DLQ fail-open append + unittest；無 CI / docs / dispatch 變更

### 1. Changed files

| 檔案 | 變更摘要 |
|------|----------|
| `delivery/notification_webhook_adapter_v1.py` | DLQ env gate、record builder、final-failure append（fail-open） |
| `tests/test_notification_webhook_dispatch_v1.py` | 新增 `TestNotificationWebhookDlq`（4 cases） |
| `04_Workflows/tickets/WH-P7-NOTIF-DLQ-impl-v1_state.md` | 本票 STATE / B_REPORT |

### 2. DLQ env / 行為

| Env 鍵 | Default | 行為 |
|--------|---------|------|
| `GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED` | `0` | `1` 時最終 webhook 失敗 append jsonl |
| `GOV_NOTIFICATION_WEBHOOK_DLQ_PATH` | `outbox/notification_dlq/events.jsonl` | append-only DLQ stream 路徑 |
| `GOV_NOTIFICATION_WEBHOOK_DLQ_TIER` | （空 → `sandbox`） | 可覆寫 `tier` 欄位 |

**行為一句話**：`DLQ_ENABLED=0` 完全不寫；`DLQ_ENABLED=1` 且 HTTP POST 最終失敗（含 retry 用盡 / 單次失敗 / 不可重試 4xx）時 append 一條 `notification_webhook_dlq_v1` jsonl；寫檔失敗僅 log warning，adapter 仍 fail-open `ok=True`。

### 3. 新增測試場景

| # | 場景 | 斷言 |
|---|------|------|
| T-DLQ-1 | DLQ disabled（default / `0`）+ persistent 500 retry 用盡 | 無 `events.jsonl`；`webhook_result` 不變 |
| T-DLQ-2 | DLQ enabled + persistent 500 retry 用盡 | jsonl 1 行；`endpoint` / `attempt_count` / `http_status` / `last_error` / embed `webhook_result` |
| T-DLQ-3 | DLQ enabled + 503→200 最終成功 | 不寫 DLQ（0 條） |

### 4. 驗證

```bash
python -m unittest tests.test_notification_webhook_dispatch_v1 -v
```

**結果**：23/23 OK（含 4 DLQ cases + 既有 19 cases）✅

### 5. skeleton / placeholder

無。

### 6. 阻塞

無。

### 7. override

無。

---

## C_REPORT

- **reviewer_date**: 2026-06-22
- **verdict**: `accepted_with_nits`

### 1. 合約對齊（§4.6.4）

- **Env / 行為**：與 B_REPORT 一致。`GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED` default off 完全不寫；`=1` 時僅在 HTTP POST **最終失敗**（`send_webhook_notification` 的 `not dispatched` 分支、retry loop 結束後）append 一行 jsonl；`_maybe_append_dlq_record` try/except + warning，**不**改外層 `ok=True`（fail-open）。
- **Record schema**：`_build_dlq_record` 含 §4.6.4.2 核心欄位（`timestamp` · `tier` · `event_id` · `endpoint` · `http_status` · `attempt_count` · `last_error` · embed `webhook_result`）；未寫 raw payload，改以 `payload_digest` + `endpoint` query redact + `response_body` ≤512 截斷。
- **觸發時機**：僅最終失敗分支呼叫 DLQ；retry 中途與 2xx 成功路徑不寫；dry-run / disabled / URL gate 拒絕在 POST 前 return，不寫 DLQ。

### 2. 測試對齊

`TestNotificationWebhookDlq` 四 case 語意清晰，覆蓋 user 指定三 scenario：

| 測試 | 斷言 |
|------|------|
| `test_dlq_disabled_no_jsonl_on_retry_exhausted` / `test_dlq_disabled_explicit_zero_no_jsonl` | disabled + persistent 500 → 不寫 |
| `test_dlq_enabled_writes_record_on_retry_exhausted` | enabled + failure → 1 行 jsonl + required 欄位 |
| `test_dlq_enabled_no_write_on_eventual_success` | enabled + 503→200 → 不寫 |

**驗證**：`python -m unittest tests.test_notification_webhook_dispatch_v1 -v` → **27/27 OK**（含 4 DLQ cases；較 B_REPORT 23 多出的為 tier URL policy cases，非 regression）。

### 3. Nits（不阻擋合併）

| # | 項目 | 建議 |
|---|------|------|
| N-1 | 合約 env 表寫 `GOV_NOTIFICATION_WEBHOOK_DLQ_ROOT`；實作用 `GOV_NOTIFICATION_WEBHOOK_DLQ_PATH`（直指 jsonl） | 後續 doc-sync 票對齊 §4.6.4 / §4.6.6 env 表 |
| N-2 | 觸發表「不可重試 4xx 單次失敗亦寫 DLQ」— 程式路徑已覆蓋，但 **無** 專測（FRAME T-3） | inspect-cli 或 follow-up 補 `400 + DLQ_ENABLED=1` case |
| N-3 | FRAME T-4「DLQ write fail-open（磁碟不可寫）」未測 | 可併入 inspect-cli 票或小型 follow-up |
| N-4 | `request_headers` 固定 `{}` — 合約允許，但未投影 `Content-Type` / `X-Gov-*` 摘要 | 未來 schema 微調可選 |
| N-5 | §4.6.0 `webhook_dlq_enabled` / §4.6.4 `impl_status` 仍 `not_implemented_yet`（本票 scope 未改 docs） | 專開 doc-sync 標 **partial** |

### 4. fail-open / fail-close

- Webhook 失敗：外層 dispatch **fail-open** ✅
- DLQ 寫入失敗：log warning、不阻斷 ✅（程式；缺 unittest 見 N-3）
- 無 fail-close 誤用 ✅

### 5. 阻塞

無。

---

## D_REPORT

- **scribe_date**: 2026-06-22
- **verdict**: `validated`（Reviewer `accepted_with_nits` · Scribe 收口）
- **handoff_summary**: P7 prod 線 DLQ **落盤 partial** 已 validated：adapter 受 `GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED` / `DLQ_PATH` / `DLQ_TIER` env gate 控制；default off；HTTP POST **最終失敗** append `outbox/notification_dlq/events.jsonl`；DLQ 寫入 fail-open；schema 對齊 §4.6.4.2。Sandbox 預設行為不變。
- **驗證**：`python -m unittest tests.test_notification_webhook_dispatch_v1 -v` → **27/27 OK**（含 4 DLQ cases · Reviewer 重跑）
- **Progress**: `00_Agent_Work_Progress.md` — **2026-06-22 · P7 · DLQ 線收口**（Scribe append）

### 已接棒下游

| 票號 | 狀態 |
|------|------|
| `WH-P7-NOTIF-DLQ-inspect-cli-v1` / `*-impl-v1` | **validated** — operator inspect CLI |
| `WH-P7-NOTIF-contract-doc-sync-v1` | DLQ 段 §4.6.4 **partial** + env 表已對齊 |

### 仍 deferred（非本票 blocking）

- 400 + DLQ 專測 · DLQ write fail-open 磁碟 mock · `request_headers` 投影微調（Reviewer nits N-2–N-4）
- replay / requeue — 未開票
