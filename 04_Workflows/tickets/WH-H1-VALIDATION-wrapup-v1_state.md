# WH-H1-VALIDATION-wrapup-v1 — Ticket State

> **handoff**：Wave-H+1 驗證補票 · **doc-only** · 小票  
> **收口範圍**：H1 validation / P7 HMAC FRAME / P8.5 首跑 Reviewer/Scribe 收口  
> **不修改**：code · tests · workflows · docs 正文 · 其它票檔 · Progress

---

## FRAME

Wave-H+1 三線交付物之 **wrap-up 匯總票**（非重驗、非施工）。本票只確認並匯總下列三件事是否已就緒：

1. **H1 validation** — `WH-H1-VALIDATION-v1` 已標 `validated`，整包三線（P7 Retry · P8.5 CI-LAND · P9 INT）無 blocking。
2. **P7 HMAC policy** — `WH-P7-NOTIF-HMAC-policy-v1` `frame_ready`；FRAME 清楚（§4.6.5 擴寫路徑 · sender/receiver/idempotency 規格 · 後續實作票已列）。
3. **P8.5 Smoke A/B CI** — `WH-P85-SMOKE-B-advisory-v1` + `WH-P85-CI-LAND-v1` Reviewer/Scribe 收口；Progress 已覆蓋 GA 首跑 Scenario 1 結果。

### AllowedPaths

- `04_Workflows/tickets/WH-H1-VALIDATION-wrapup-v1_state.md`（本檔 only）

### BlockedPaths

- 其它 `04_Workflows/tickets/**`
- 所有 `*.py` · `tests/**` · `.github/workflows/**` · `docs/**`
- `04_Workflows/00_Agent_Work_Progress.md`

---

## STATE

- **overall_status**: `validated`
- **current_owner**: Wave-H+1 Validation Scribe
- **last_updated**: 2026-06-22 · wrap-up scribe
- **wave**: Wave-H+1
- **status_by_role**:
  - **Validator / Scribe (B)**: done — 2026-06-22 · B_REPORT 匯總完成
  - **Reviewer (C)**: done — 2026-06-22 · 引用上游 validated / accepted · 無 blocking
  - **Scribe (D)**: done — 2026-06-22 · 本 wrap-up 票收口
- **notes**: 純匯總票；未改 code / tests / workflows / docs / Progress / 其它票檔

---

## B_REPORT (Validator / Scribe 匯總)

> **聲明**：本票 **不修改** 任何 code / tests / workflows / docs / Progress；僅對照已完成的 `WH-H1-VALIDATION-v1` · `WH-P7-NOTIF-HMAC-policy-v1` · `WH-P85-SMOKE-B-advisory-v1` / `WH-P85-CI-LAND-v1` 及 Progress 末尾條目作匯總。

---

### 1. P7 Retry sandbox（引用 WH-H1-VALIDATION-v1 · A 節）

- **default=0 → 單次 POST**：`DEFAULT_RETRY_MAX_ATTEMPTS = 0`；無 RETRY env 時 `attempt_count=1`、retry loop 不進退避；既有 fail-open 單 POST 行為未破壞。
- **retry 條件**：可重試 = `timeout` · 連線錯誤（`http_status is None`）· **408 / 429 / 5xx**；其它 4xx 不重試；退避 `base_delay_ms * 2^(attempt-1)` clamp 至 `max_delay_ms`，與 §4.6.3 / RETRY-SANDBOX 票一致。
- **四場景 unittest**：`test_default_no_retry_env_single_post_only` · `test_retry_503_then_200_succeeds` · `test_retry_exhausted_on_persistent_500` · `test_non_retriable_400_no_retry` — 均 **pass**；合約 §4.6.0 `webhook_retry_max_attempts` → **`partial`**（sandbox-only · 無 DLQ / HMAC / prod URL）。
- **known gaps（非 blocking）**：408 / 429 / timeout / URLError 可重試分支**無專測**；Windows 全量 suite 偶發 flaky（retry 子集 4/4 可綠）。

**一句話**：sandbox env 驅動 retry、預設關閉、fail-open 不變，四場景 unittest 與 §4.6.0 **partial** 一致，缺口僅缺專測與 flaky echo。

---

### 2. P7 HMAC policy（引用 WH-P7-NOTIF-HMAC-policy-v1 · FRAME）

- **交付位置（FRAME 裁決）**：擴寫 **`docs/outbox-and-feedback-layer-contract-v1.md` §4.6.5**（含 §4.6.5.1 sender · §4.6.5.2 receiver · §4.6.5.3 idempotency · §4.6.5.4 examples）；不另建新 SSOT 檔。
- **FRAME 決策摘要**：HMAC-SHA256 · `X-Gov-Signature-256` / `X-Gov-Timestamp` / `X-Gov-Event-Id` · 原樣 body bytes canonicalization · ±300s 窗口 · `event_id` 冪等 SSOT · sandbox 預設不簽名 · 全文 **`not_implemented_yet`** 直至 impl 票合併。
- **後續實作票（FRAME §5）**：

| 票號 | 一句話 |
|------|--------|
| **`WH-P7-NOTIF-HMAC-impl-v1`** | 在 `notification_webhook_adapter_v1` 實作 §4.6.5 簽名與 headers；env-gated（sandbox 預設 off）；unittest 覆蓋 signed POST mock。 |
| **`WH-P7-NOTIF-HMAC-receiver-contract-v1`** | 客戶端驗簽 reference doc + contract test fixture（驗簽成功/失敗/重放/idempotency）；可含 `tests/fixtures/webhook_hmac/`。 |

**一句話**：HMAC/idempotency 規格 FRAME 已就緒，目標 §4.6.5 擴寫，後續拆 **impl** 與 **receiver-contract** 兩票，現況仍 **not_implemented_yet**。

---

### 3. P8.5 CI（引用 WH-P85-SMOKE-B-advisory-v1 C/D_REPORT · Progress 首跑條目）

- **Reviewer verdict**：**`accepted`** — P8.5 advisory CI（Smoke A + B）與 runbook §0.3 一致；GA 首跑 Scenario 1 通過；仍 **non-blocking / 非 required check**。
- **Scenario 1 首跑結果**（Progress 2026-06-22 · Wave-H+1 · P8.5 bridge CI 首跑收口）：
  - Workflow **P85 Bridge Smoke CI (advisory)** · `workflow_dispatch` on **main** · run **completed**。
  - `p85-bridge-smoke-a` → `test_minimal_orchestration_bridge` **14/14 OK** · log `Bridge Smoke A passed`。
  - `p85-bridge-smoke-b` → `test_app_api_orchestration_bridge` **7/7 OK** · log `Bridge Smoke B passed`。
  - 兩 job 均未 skip · `continue-on-error: true` · Smoke C 仍 manual。
- **Scenario 2（skip 分支）**：**未實測** — 首跑 deps OK，未見 `Bridge Smoke B skipped::reason=…`；skip 邏輯依 workflow 靜態審查 + Smoke A 同型。**建議**：低優先 **doc-only 小票** 刻意觸發 skip 分支以複驗 AC-3（**非** P8.5 主線 blocking）。

**一句話**：GA 首跑 Scenario 1 雙 job 14/14 + 7/7 **accepted**，Scenario 2 skip 未實測、可留 doc-only follow-up。

---

### 4. Wrap-up 裁決

| 線 | 上游票 | 匯總結論 |
|----|--------|----------|
| H1 validation | `WH-H1-VALIDATION-v1` | **`validated`** · 無 blocking |
| P7 HMAC FRAME | `WH-P7-NOTIF-HMAC-policy-v1` | **`frame_ready`** · §4.6.5 路徑 + 兩張 impl 票已列 |
| P8.5 CI 收口 | `WH-P85-SMOKE-B-advisory-v1` · `WH-P85-CI-LAND-v1` | **Reviewer `accepted`** · Progress 已覆蓋 Scenario 1 |

**本票 overall_status**：`validated` — 三線 wrap-up 匯總完成，無新增 blocking。

---

## C_REPORT (Reviewer)

- **verdict**: validated — no blocking
- **review_date**: 2026-06-22
- **notes**: 匯總對照上游 WH-H1-VALIDATION-v1 / WH-P85-SMOKE-B C_REPORT；無 code 變更請求。

---

## D_REPORT (Scribe)

- **verdict_echo**: Wrap-up 匯總完成 · `overall_status=validated`
- **progress_entry**: **未 append**（本票邊界禁止改 Progress）
- **scribe_date**: 2026-06-22 · Wave-H+1 Validation wrap-up Scribe
