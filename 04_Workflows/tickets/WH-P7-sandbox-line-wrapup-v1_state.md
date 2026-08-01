# WH-P7-sandbox-line-wrapup-v1 — Ticket State

> handoff 摘要檔；P7 **sandbox 通知線**總 wrap-up · doc-only 收口票。  
> 涵蓋：emit → dispatch → webhook sandbox → retry → HMAC sender → receiver 合約 → advisory CI。  
> 目的：為 **prod 線**繼承提供單一入口索引；**本票不改 code / tests / workflows / docs / 其他票 / Progress**。

---

## FRAME

### handoff header

**P7 sandbox 通知線總 wrap-up**：自 orchestrator emit（`intake.gate_decision` / `delivery.bundle_ready`）經 gateway → dispatch registry → localhost webhook adapter（含 opt-in retry 與 env-gated HMAC sender），至合約 §4.2–§4.6 SSOT、receiver contract 文檔與 advisory CI（`p7-notification-smoke`）。本票僅**彙總與封箱索引**；prod 級 DLQ / staging/prod URL tier / receiver reference impl / required CI 留給後續 prod 線票。

### 技術面向（adapter · tests · CI）

| 層級 | sandbox 現況 | 證據 |
|------|--------------|------|
| **Emit** | orchestrator 路徑 emit `intake.gate_decision` / `delivery.bundle_ready`；fail-open；CLI 或 env gate 啟用 | `WD-P7-T1` · `tests.test_orchestrator_notifications` **7/7** |
| **Gateway / dispatch** | post-emit registry；local file + webhook 雙 sink；dispatch fail-open | §4.2 · `WD-P7-T2` |
| **Webhook adapter** | localhost/127.0.0.1 only；case allowlist；env master switch；單次 POST 為預設 | `notification_webhook_adapter_v1` · `WD-P7-T2` |
| **Retry** | env 驅動、**default `max_attempts=0`**；sandbox localhost only；無 DLQ | `WH-P7-NOTIF-RETRY-SANDBOX-v1` · `TestNotificationWebhookRetry` 4 cases |
| **HMAC sender** | env 雙 gate（`HMAC_ENABLED` + secret）；default off；fail-open unsigned；`X-Gov-*` headers | `WH-P7-NOTIF-HMAC-impl-v1` · `TestNotificationWebhookHmac` 3 cases |
| **全鏈 smoke** | orchestrator → gateway → dispatch → mock webhook；env-only gate assert | `WD-P7-T3` · `tests.test_orchestrator_dispatch_full_smoke_v1` **5/5** |
| **Tests 匯總** | notifications **7/7** · webhook dispatch **19/19**（12 基線 + 4 retry + 3 HMAC）· full smoke **5/5** | 各票 B_REPORT / Progress 2026-06-22 |
| **CI 形狀** | `.github/workflows/p7-notification-smoke.yml` · job `p7-notification-smoke` · **advisory** · `continue-on-error: true` · localhost mock `:8080` · 跑 full_smoke + notifications + webhook_dispatch（**預設無 retry/HMAC env**） | `WD-P7-T3` AC-7 · Wave-G |

**Adapter 行為要點**：預設零 HTTP（env 關）；sandbox URL gate 拒絕 non-localhost；webhook 失敗不改 orchestrator `ok`；retry 用盡仍外層 `ok=True`；HMAC enabled 但 secret 空 → warning + 非簽名 POST。

### 合約面向（§4.2–§4.6 SSOT）

| 節 | sandbox 線角色 | 狀態摘要 |
|----|----------------|----------|
| **§4.2** | event_type 枚舉、emit/dispatch fail-open、downstream ack 追蹤語意 | **implemented**（gateway + dispatch 已接線） |
| **§4.3** | `feedback` envelope 嵌套摘要 | 引用層；非本線主交付 |
| **§4.4** | webhook sandbox dispatch env gates、safety、mock 測試指引 | **implemented**（localhost-only v1）；retry/HMAC 詳見 §4.6 |
| **§4.5** | advisory CI smoke workflow | **implemented**（non-blocking） |
| **§4.6.0** | policy 對照表 | 見 B_REPORT §4.6 真實狀態 |
| **§4.6.3** | retry & backoff | **partial**（sandbox adapter only） |
| **§4.6.4** | DLQ | **not_implemented_yet** |
| **§4.6.5** | HMAC & idempotency | sender **partial**；receiver **contract documented**（§4.6.5.2）；reference impl / fixtures **not_implemented_yet** |
| **§4.6.6** | URL tier / prod env 表 | sandbox URL check **implemented**；`TIER` / `URL_ALLOWLIST` / prod HMAC 強制 **not_implemented_yet** |
| **§4.6.7** | future work 索引 | 部分票號 stale（見 `WH-P7-NOTIF-contract-partials-validation-v1` 非 blocking 註） |

**Partial 能力邊界**（retry / HMAC sender）：僅 sandbox localhost webhook；無 DLQ；無 staging/prod URL；無 receiver 驗簽程式；無 HTTP `Idempotency-Key`；CI 不預設開 retry/HMAC env。

### 票的演進（WD-P7-T* → WH-*）

```
Wave-D/E（sandbox 基線）
  WD-P7-T1  orchestrator emit gate/bundle notify     → done_with_gaps · accepted_with_gaps
  WD-P7-T2  webhook sandbox dispatch + 雙 sink       → done · accepted
  WD-P7-T3  全鏈 smoke + env-only gate + advisory CI → done_with_gaps · accepted_with_gaps

Wave-H / H+1（sandbox 加深 + 合約）
  WH-P7-NOTIF-PROD-policy-v1        §4.6 prod-tier 骨架（design_accepted）     → prod 線政策母本
  WH-P7-NOTIF-RETRY-SANDBOX-v1      retry partial（sandbox-only）              → done · accepted_with_gaps
  WH-P7-NOTIF-HMAC-policy-v1        HMAC policy 設計票（doc-only）             → frame_ready（§4.6.5 擴寫待 B）
  WH-P7-NOTIF-HMAC-impl-v1          HMAC sender partial                        → impl_done · C pending
  WH-P7-NOTIF-HMAC-receiver-contract-v1  receiver contract §4.6.5.2 落盤       → implementer_done_pending_review
  WH-P7-NOTIF-contract-partials-validation-v1  retry+HMAC partial 合約審計     → validated · accepted

本票
  WH-P7-sandbox-line-wrapup-v1      sandbox 線總索引 + 封箱判準                  → frame_ready
```

### non-goals

- ❌ **不再改**任何 Python / tests / workflows / docs / 其他票檔 / Progress。
- ❌ 不宣稱 prod tier、DLQ、receiver reference impl 已交付。
- ❌ 不將 advisory CI 升格為 required check。
- ❌ 不拆分 `intake.gate_decision` accept/reject event_type（維持 Wave-D Orchestrator 裁決）。

### AllowedPaths / BlockedPaths

| Allowed | Blocked |
|---------|---------|
| `04_Workflows/tickets/WH-P7-sandbox-line-wrapup-v1_state.md` | 其餘全 repo |

---

## STATE

- **overall_status**: `validated`
- **current_owner**: orchestrator
- **next_action**: prod 線依 D_REPORT 開 DLQ / PROD-URL / receiver fixtures / sample-impl 票；sandbox 線內部 follow-up：`WH-P7-NOTIF-HMAC-impl-v1` · `WH-P7-NOTIF-HMAC-receiver-contract-v1` C 收口（非 blocking）
- **last_updated**: 2026-06-22 · reviewer (C)
- **wave**: Wave-H+1 · P7 sandbox line wrap-up
- **status_by_role**:
  - **Orchestrator (A)**: done — FRAME 落盤
  - **Implementer (B)**: n/a — 本票 doc-only
  - **Reviewer (C)**: done — 2026-06-22 · **`accepted`**
  - **Scribe (D)**: done — 2026-06-22 · D_REPORT prod handoff（本輪 Reviewer 代填；Progress append 另輪）

---

## B_REPORT (Reviewer / Scribe · sandbox 線收口)

> **範圍**：彙總截至 2026-06-22 之 sandbox 線交付；依賴各票 B/C/D_REPORT 與 `WH-P7-NOTIF-contract-partials-validation-v1` 審計。**本輪未重跑 unittest。**

### 1. 目前 sandbox 線**能做什麼**

P7 sandbox 通知線已可在 **env opt-in** 下完成 **orchestrator emit → gateway → dispatch registry → localhost webhook POST** 全鏈，並附 **advisory CI**（`p7-notification-smoke` · non-blocking · localhost mock）。具體能力：

- **Emit / dispatch**：`intake.gate_decision` 與 `delivery.bundle_ready`（及 registry 內其他 event_type）經 gateway 寫 outbox/jsonl 後 dispatch；emit 與 dispatch **fail-open**（`WD-P7-T1` · `WD-P7-T2`）。
- **Webhook sandbox**：`GOV_NOTIFICATION_WEBHOOK_*` env 開啟 + case allowlist 命中時，對 **localhost/127.0.0.1** mock endpoint POST；預設關閉時零 HTTP（`WD-P7-T2` · **12/12** 基線測試）。
- **Retry（partial）**：`GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS` **default=0** 維持單次 POST；設 `≥1` 時 sandbox adapter 對 5xx/408/429/連線錯誤退避重試，外層仍 fail-open（`WH-P7-NOTIF-RETRY-SANDBOX-v1` · **+4** retry cases）。
- **HMAC sender（partial）**：`HMAC_ENABLED=1` 且 secret 非空時附加 `X-Gov-Signature-256` / `X-Gov-Timestamp` / `X-Gov-Event-Id`；預設 off；缺 secret fail-open 非簽名（`WH-P7-NOTIF-HMAC-impl-v1` · **+3** HMAC cases · **19/19** webhook suite）。
- **全鏈 + env-only gate**：僅 env、無 CLI flag 亦可 assert outbox/jsonl 與 mock POST（`WD-P7-T3` · **5/5**）。
- **Advisory CI**：PR path filter + daily cron + `workflow_dispatch`；上傳 smoke log artifact；失敗不阻 merge（§4.5 · `p7-notification-smoke.yml`）。
- **Receiver 合約（文檔）**：§4.6.5.2 normative SSOT（驗簽 pseudo-code、重放表、HTTP 語意、idempotency）已落盤（`WH-P7-NOTIF-HMAC-receiver-contract-v1`）；**無** reference 程式。

**一句話（能做什麼）**：sandbox 線可在 localhost mock 上端到端演練 **emit → dispatch → webhook**（含 opt-in retry 與 env-gated HMAC 發送），並以 advisory CI 做非阻斷回歸，合約 §4.6.5.2 已定 receiver 驗簽/idempotency 文檔義務。

### 2. 目前 sandbox 線**不能做什麼**（留給 prod 線）

下列能力在合約或程式中仍為 **`not_implemented_yet`** 或僅 policy 草案，**不得**由 sandbox 線宣稱已交付：

| 能力 | 狀態 | prod 線入口 |
|------|------|-------------|
| **DLQ** | 失敗事件落盤 / inspect | 新票（§4.6.4） |
| **prod / staging URL tier** | 非 localhost endpoint、`GOV_NOTIFICATION_WEBHOOK_TIER`、URL allowlist | `WH-P7-NOTIF-PROD-policy-v1` §4.6.6 實作票 |
| **Receiver HMAC 驗簽** | 無 reference impl / contract test | `WH-P7-NOTIF-HMAC-receiver-fixtures-v1` · `WH-P7-NOTIF-HMAC-receiver-sample-impl-v1` |
| **HMAC prod 強制 / tier gate** | staging/prod 缺簽名須拒絕 | prod URL + security 票 |
| **HTTP `Idempotency-Key` header** | sender 未送 | sender v2 或 prod 票 |
| **Required CI gate** | `p7-notification-smoke` 仍 advisory | CI governance 票 |
| **408/429/timeout retry 專測** | 邏輯有、測試缺口 | 可選 sandbox 硬化票 |

**一句話（不能做什麼）**：sandbox 線**不能**對外客戶 URL 送 webhook、**不能**落 DLQ、**不能**在 repo 內驗簽 HMAC 或提供 receiver reference impl，且 CI **不能**作為 merge 必要條件——這些全部留給 prod 線。

### 3. 合約 §4.6 真實狀態（§4.6.0 policy 表）

| `policy_item` | `impl_status` | sandbox 線說明 |
|---------------|---------------|----------------|
| `emit_fail_open` | **implemented** | gateway notify 失敗不改 orchestrator `ok` |
| `dispatch_fail_open` | **implemented** | webhook/dispatch 失敗不改 emit `ok` |
| `webhook_url_tier` | **implemented**（sandbox）· prod tier **not_implemented_yet** | `_is_safe_sandbox_url` localhost-only；無 `TIER` env |
| `webhook_hmac` | **partial** | sender env-gated HMAC-SHA256；default off；receiver impl **not_implemented_yet** |
| `webhook_retry_max_attempts` | **partial** | sandbox localhost only；default=0；無 DLQ |
| `webhook_dlq_enabled` | **not_implemented_yet** | 無 DLQ 路徑 |
| `advisory_ci_blocking` | **implemented**（值=false） | CI 存在但 **non-blocking** |

**§4.6.5 細項**

| 子項 | `impl_status` |
|------|---------------|
| Sender HMAC v1（§4.6.5.1） | **partial** |
| Receiver contract（§4.6.5.2） | **contract documented**；reference impl / fixtures **not_implemented_yet** |
| HTTP `Idempotency-Key` | **not_implemented_yet** |
| `event_id` 冪等鍵（emit 層） | **partial**（gateway 產生；webhook payload 帶入） |

**§4.6.6 env 表（精簡）**

| Env | `impl_status` |
|-----|---------------|
| `GOV_NOTIFICATION_WEBHOOK_ENABLED` / `URL` | **implemented** |
| `GOV_NOTIFICATION_WEBHOOK_TIER` | **not_implemented_yet** |
| `GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST` | **not_implemented_yet** |
| `GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET` | 讀取已用於 sender partial；§4.6.6 表仍標 **not_implemented_yet**（文檔 staleness · 非 blocking） |

**Partial 標記真意**：retry 與 HMAC **僅**在 sandbox localhost adapter 上 opt-in 實作；合約刻意註明「無 DLQ / 無 prod URL / receiver 未實作」，避免 prod 線誤繼承為完整交付。

### 4. 票封箱 vs prod 線未來入口

#### 可視為「sandbox 線已封箱」（交付完成 · 僅文書/審計待收口）

| 票號 | Verdict / 狀態 | 封箱語意 |
|------|----------------|----------|
| `WD-P7-T1` | `accepted_with_gaps` · done_with_gaps | orchestrator emit 交付；gap 已由 T3 補強 |
| `WD-P7-T2` | `accepted` · done | webhook sandbox 雙 sink 完整 |
| `WD-P7-T3` | `accepted_with_gaps` · done_with_gaps | 全鏈 smoke + advisory CI；無 retry/HMAC env 在 CI |
| `WH-P7-NOTIF-RETRY-SANDBOX-v1` | `accepted_with_gaps` · done | retry **partial** 落地 |
| `WH-P7-NOTIF-contract-partials-validation-v1` | `accepted` · **validated** | partial 合約審計通過 |

#### 已交付 impl/doc 但 **C/Scribe 未完全收口**（sandbox 線內部 follow-up）

| 票號 | 狀態 | 待辦 |
|------|------|------|
| `WH-P7-NOTIF-HMAC-impl-v1` | `impl_done` · C pending | Reviewer sign-off sender partial |
| `WH-P7-NOTIF-HMAC-receiver-contract-v1` | `implementer_done_pending_review` | Reviewer sign-off §4.6.5.2 |

#### 設計/frame 票（非 sandbox runtime 交付）

| 票號 | 狀態 | 角色 |
|------|------|------|
| `WH-P7-NOTIF-PROD-policy-v1` | design_accepted | **prod 線政策母本**（§4.6 骨架） |
| `WH-P7-NOTIF-HMAC-policy-v1` | frame_ready | policy 擴寫票；§4.6.5 深度已由 receiver-contract 部分承接 |

#### 專門給 **prod 線** 的未來入口（本 repo 尚未開票或僅 FRAME 索引）

| 建議票號 / 主題 | 依賴 |
|-----------------|------|
| DLQ 實作（§4.6.4） | prod policy · retry partial |
| `GOV_NOTIFICATION_WEBHOOK_TIER` + URL allowlist（§4.6.6） | `WH-P7-NOTIF-PROD-policy-v1` |
| HMAC prod 強制 / staging gate | URL tier + security |
| `WH-P7-NOTIF-HMAC-receiver-fixtures-v1` | receiver contract · HMAC-impl |
| `WH-P7-NOTIF-HMAC-receiver-sample-impl-v1` | fixtures 票 |
| CI 升格 required check | advisory smoke 穩定 N 週後 |
| §4.6.6 `HMAC_SECRET` 列 / §4.6.7 票號 doc-sync | Scribe 小票（非 blocking） |

### 5. 驗證索引（引用 · 本票未重跑）

| 模組 | 計數 | 來源票 |
|------|------|--------|
| `tests.test_orchestrator_notifications` | **7/7** | WD-P7-T1 · T3 |
| `tests.test_notification_webhook_dispatch_v1` | **19/19** | WD-P7-T2 · RETRY · HMAC-impl |
| `tests.test_orchestrator_dispatch_full_smoke_v1` | **5/5** | WD-P7-T3 |
| `p7-notification-smoke`（GA） | advisory job | WD-P7-T3 · §4.5 |

### 6. 阻塞

無 blocking。sandbox 線技術交付與 `WH-P7-NOTIF-contract-partials-validation-v1` 審計一致；待收口項為兩張 WH 票的 Reviewer C_REPORT 與本票 `validated` 裁決。

---

## C_REPORT

- **review_date**: 2026-06-22
- **verdict**: **`accepted`**
- **scope**: B_REPORT 封箱判準 · §4.6.0 policy 表 / `impl_status` 交叉核對 · 引用票號存在性與狀態合理性（本輪未重跑 unittest）

**封箱判準（兩句 · 直接引用 B_REPORT §1–§2）**

- **能做什麼**：sandbox 線可在 localhost mock 上端到端演練 **emit → dispatch → webhook**（含 opt-in retry 與 env-gated HMAC 發送），並以 advisory CI 做非阻斷回歸，合約 §4.6.5.2 已定 receiver 驗簽/idempotency 文檔義務。
- **不能做什麼**：sandbox 線**不能**對外客戶 URL 送 webhook、**不能**落 DLQ、**不能**在 repo 內驗簽 HMAC 或提供 receiver reference impl，且 CI **不能**作為 merge 必要條件——這些全部留給 prod 線。

**審查摘要**

| 檢查項 | 結果 |
|--------|------|
| B_REPORT 一句話能做 / 不能做 | ✅ 清晰、互斥 |
| §4.6.0 policy 表 / `impl_status` | ✅ 與 `docs/outbox-and-feedback-layer-contract-v1.md` §4.6.0–§4.6.6 一致；`HMAC_SECRET` env 表 staleness 已由 doc-sync 票標 **partial**（非 blocking） |
| 引用票號 | ✅ `WD-P7-T1/T2/T3` · `WH-P7-NOTIF-RETRY-SANDBOX-v1` · `WH-P7-NOTIF-HMAC-impl-v1` · `WH-P7-NOTIF-HMAC-receiver-contract-v1` · `WH-P7-NOTIF-contract-partials-validation-v1` · `WH-P7-NOTIF-contract-doc-sync-v1` 均存在；狀態與 B_REPORT §4 分類一致 |
| Advisory CI | ✅ `p7-notification-smoke.yml` · `continue-on-error: true` · localhost mock · 預設無 retry/HMAC env |
| Blocking | 無 |

**非 blocking follow-up**（sandbox 線內 · 不阻擋本票 `validated`）：`WH-P7-NOTIF-HMAC-impl-v1` · `WH-P7-NOTIF-HMAC-receiver-contract-v1` 子票 C 收口；408/429/timeout retry 專測可選硬化。

---

## D_REPORT

- **handoff_date**: 2026-06-22
- **from**: P7 **sandbox 線**（`validated`）
- **to**: P7 **prod 線**（Orchestrator 開票）

**prod 線後續入口建議**（依 B_REPORT §2 / §4 · 優先序供 Orchestrator 裁決）：

| 建議票號 | 範圍摘要 | 依賴 |
|----------|----------|------|
| **`WH-P7-NOTIF-DLQ-v1`** | §4.6.4 失敗事件 DLQ 落盤 / inspect 路徑 | retry partial · prod policy |
| **`WH-P7-NOTIF-PROD-URL-v1`** | §4.6.6 `GOV_NOTIFICATION_WEBHOOK_TIER` + URL allowlist；staging/prod endpoint | `WH-P7-NOTIF-PROD-policy-v1` |
| **`WH-P7-NOTIF-HMAC-receiver-fixtures-v1`** | `tests/fixtures/webhook_hmac/` 已簽名樣本 + headers sidecar | §4.6.5.2 receiver contract · HMAC-impl sender |
| **`WH-P7-NOTIF-HMAC-receiver-sample-impl-v1`** | 最小 reference receiver + contract test（驗簽 / replay / mismatch） | fixtures 票 |

**handoff 一句話**：sandbox 線已封箱為 localhost 端到端通知演練 + advisory CI + partial retry/HMAC sender + receiver 合約 SSOT；prod 線從 DLQ → URL tier → receiver fixtures/impl 依上表接棒，勿將 sandbox partial 誤繼承為 prod 完整交付。

**Progress**：本輪未 append `00_Agent_Work_Progress.md`（任務邊界禁止改 Progress）；Orchestrator / Scribe 可另輪 append。
