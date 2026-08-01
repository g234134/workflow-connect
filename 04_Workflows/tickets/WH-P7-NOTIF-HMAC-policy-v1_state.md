# WH-P7-NOTIF-HMAC-policy-v1 — Ticket State

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Wave-H · **HMAC & idempotency policy 設計票（doc-only）**  
> 上游：`WH-P7-NOTIF-PROD-policy-v1`（§4.6 prod-tier 骨架）· `WH-P7-NOTIF-RETRY-SANDBOX-v1`（retry partial）  
> 產物：HMAC 簽名與冪等性 sender/receiver 合約草案；**零程式、零 CI 變更**

---

## FRAME

### 1. Background

P7 通知鏈 sandbox 基線已收口；prod-tier policy 骨架已落於合約 §4.6（`WH-P7-NOTIF-PROD-policy-v1`）。現況摘要：

| 能力 | impl_status | 證據 |
|------|-------------|------|
| Gateway emit `event_id` | **partial** | gateway 產生 `event_id`；webhook payload 帶入 |
| Webhook POST（sandbox） | **implemented** | `notification_webhook_adapter_v1` · localhost-only · fail-open |
| Retry loop | **partial**（sandbox-only） | `WH-P7-NOTIF-RETRY-SANDBOX-v1` · env `GOV_NOTIFICATION_WEBHOOK_RETRY_*` · default=0 |
| HMAC 簽名 | **not_implemented_yet** | adapter 模組 docstring 明列 future phase；`_send_http_post` 僅送 `Content-Type` / `X-Webhook-Sent-At` / `X-Webhook-Version` |
| HTTP `Idempotency-Key` header | **not_implemented_yet** | 測試僅 assert JSON body `event_id`；無簽名／冪等 header |
| DLQ | **not_implemented_yet** | §4.6.4 僅 policy 草案 |
| prod / staging URL tier | **not_implemented_yet** | §4.6.6 · `_is_safe_sandbox_url()` 僅 localhost/127.0.0.1 |
| Advisory CI | **implemented**（non-blocking） | `p7-notification-smoke.yml` · `127.0.0.1:8080` mock · 無 HMAC env |

**§4.6.5 現況**：合約中僅一段摘要（算法／header 名／timestamp／`event_id` 冪等鍵／sender vs receiver 分工），標記 `not_implemented_yet`；**缺少**可審計的 canonicalization 規則、header 格式範例、timestamp 窗口數值、重放拒絕語意、receiver 驗簽失敗處置、與 retry/at-least-once 的冪等協作說明。

**合約對 HMAC 的需求（待本票定稿）**：

- **算法**：HMAC-SHA256（對稱 secret；禁止 secret 入庫）
- **Header 名稱**：簽名、timestamp、事件識別（見 Goal）
- **Payload canonicalization**：簽名覆蓋範圍須唯一、可重現（JSON 排序 vs 原樣 body 須裁決）
- **Timestamp 窗口**：skew 容忍（如 ±5 分鐘）與時鐘漂移處理
- **重放防護**：timestamp + `event_id` / nonce 去重語意
- **Idempotency key**：以 gateway `event_id` 為 SSOT；HTTP `Idempotency-Key` header 與 body 一致性規則

**威脅模型（引用 §4.6.1，本票不擴寫）**：偽造 payload、重放攻擊、secret 洩漏、客戶 endpoint 誤配；HMAC 為 staging/prod 升格前的必要 trust boundary。

### 2. Goal / Scope（明確 doc-only）

產出一份 **HMAC & idempotency 設計草案**，作為 §4.6.5 的完整規格（sender contract + receiver contract + 範例 + future ticket 索引）。

#### 交付位置偏好（本票裁決）

**方案 A — 併入 `docs/outbox-and-feedback-layer-contract-v1.md` §4.6.5（首選）**

- 理由：§4.6 已是 prod-tier policy SSOT；`WH-P7-NOTIF-PROD-policy-v1` Reviewer 已 sign-off §4.6.5 小節存在；避免雙 SSOT；§4.6.0 policy 表 `webhook_hmac` 列可直接 cross-ref 同節。
- 作法：將現 §4.6.5 一段摘要**擴寫**為完整小節（含子標題 §4.6.5.1 sender · §4.6.5.2 receiver · §4.6.5.3 idempotency · §4.6.5.4 examples），不另建新檔。

> 不採方案 B（獨立 `docs/notification-webhook-hmac-contract-v1.md`）：HMAC 與 retry/DLQ/URL 同屬 §4.6 治理面，拆檔易與 §4.6.0 policy 表脫節；若日後客戶-facing 需獨立 PDF，可由 Scribe 自 §4.6.5 匯出，非本票 scope。

#### 本票須定義的規格項

| 項目 | 建議 default（`proposed_default`） | 備註 |
|------|----------------------------------|------|
| HMAC 算法 | `HMAC-SHA256` | secret = `GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET`（env only） |
| 簽名 header | `X-Gov-Signature-256` | 值格式：`sha256=<hex>` 或 `v1=<hex>`（本票定稿擇一） |
| Timestamp header | `X-Gov-Timestamp` | Unix epoch **seconds**（UTC）；receiver 拒絕超出窗口者 |
| 事件識別 header | `X-Gov-Event-Id` | 必須等於 JSON body `event_id` |
| Timestamp 容忍窗口 | **±300 秒（5 分鐘）** | 可 env override（future）；sandbox 未啟用 HMAC 時不適用 |
| Payload canonicalization | **原樣 HTTP body bytes**（`Content-Type: application/json; charset=utf-8` 下 `json.dumps` 產物） | 簽名覆蓋：`{timestamp}.{event_id}.{body}` 或等價 documented string；**禁止** receiver 自行 re-serialize JSON key 順序 |
| 重放防護 | receiver 維護 `(event_id)` 或 `(event_id, timestamp)` 去重快取；窗口外 timestamp 拒絕 | staging/prod 建議；sandbox mock 可省略 |
| Idempotency | SSOT = gateway `event_id`；HTTP header `Idempotency-Key: {event_id}`（future impl） | 與 §4.6.2 at-least-once（retry 後）協作：receiver 對同 `event_id` 回 2xx 視已處理 |
| Secret 存放 | env / secret 管理系統 | **本票僅類型**；不決定 Vault/KMS 供應商 |
| impl_status | 全文維持 **`not_implemented_yet`** | 直至 `WH-P7-NOTIF-HMAC-impl-v1` 合併 |

#### Sender contract（本 repo · future impl 對照）

- 當 `GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET` 非空 **且** tier ≥ staging（future gate）時，adapter **must** 計算 HMAC 並附加 §4.6.5 定義之 headers。
- **Sandbox 預設**：secret 未設 → **不簽名**（維持現行無 HMAC 行為；與 Non-Goals 一致）。
- 簽名失敗（secret 格式錯誤等）：**fail-open** 語意下記錄 `webhook_result.signature_error`（future 欄位名）；不 raise 至 orchestrator（對齊 §4.6.2 dispatch fail-open）。
- 與 retry：每次 retry **must** 使用相同 `event_id` 與相同 canonical body；timestamp 可刷新（本票須明文裁決）。

#### Receiver contract（客戶 webhook · 文檔義務）

- **Must** 驗證 HMAC、timestamp 窗口、`X-Gov-Event-Id` ↔ body `event_id` 一致。
- **Must** 對重複 `event_id` 回 2xx（idempotent accept）或 409（本票擇一並說明與 retry 互動）。
- 驗簽失敗：**401/403**（本票定稿）；**must not** 以 5xx 誘發無限 retry（對照 §4.6.3 可重試狀態碼）。
- 提供至少一個 **non-secret** header 格式範例（假值 hex）。

### 3. Non-Goals

- ❌ **不實作**任何簽名、驗簽、或 header 注入邏輯（含 `notification_webhook_adapter_v1`、tests、CI mock）。
- ❌ **不決定** secret 存放的具體產品（Vault/KMS/CI secret store）；僅 env/secret-manager **類型**。
- ❌ **不修改**現有 sandbox 行為（仍可無簽名 POST；retry partial 不變）。
- ❌ **不更改** retry / DLQ / prod URL policy（僅引用 §4.6.3–§4.6.6；不重寫）。
- ❌ **不升格** advisory CI 為 required check；不新增 CI secret。
- ❌ **不合併** Phase 8.8 `orchestration_bridge_outbox`（§2.2 永久分軌）。
- ❌ **不修改** `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `.cursor/rules/**`（除非尚書省另批 governance 票）。

### 4. Acceptance Criteria

- **AC-1**：`docs/outbox-and-feedback-layer-contract-v1.md` **§4.6.5** 擴寫完成，含 §4.6.5.1 sender contract · §4.6.5.2 receiver contract · §4.6.5.3 idempotency · §4.6.5.4 examples（或等價子標題）。
- **AC-2**：至少 **一個 HMAC header 格式範例**（假 secret / 假 hex；**零真值 secret**）。
- **AC-3**：canonicalization 規則**唯一且可重現**（明確寫出 signed string 拼接順序或「原樣 body bytes」裁決）。
- **AC-4**：timestamp 窗口有 `proposed_default` 數值（±300s）與 receiver 拒絕語意。
- **AC-5**：`impl_status` 全文維持 **`not_implemented_yet`**，並連結 ≥2 張 future 實作票（見下）。
- **AC-6**：與 §4.6.0 `webhook_hmac` policy 列、`event_id` partial 狀態、adapter 現碼（無簽名 header）**一致**。
- **AC-7**：B_REPORT 含與 `WH-P7-NOTIF-PROD-policy-v1` AC-4 / §4.6.5 摘要的對照（本票為深度擴寫，非 policy 矛盾）。
- **AC-8**：文檔工單自檢（APP-DOC）：零本機絕對路徑、零 secret 範例值、禁區僅類型描述。

### 5. 建議衍伸實作票（本票外 · AC-5 要求）

| 票號（建議） | 範圍摘要 | 依賴 |
|--------------|----------|------|
| `WH-P7-NOTIF-HMAC-impl-v1` | 在 `notification_webhook_adapter_v1` 實作 HMAC-SHA256 簽名與 §4.6.5 定義 headers；env-gated（sandbox 預設 off）；unittest 覆蓋 signed POST mock | 本票 AC-1–AC-4 定稿 + Security review |
| `WH-P7-NOTIF-HMAC-receiver-contract-v1` | 客戶端驗簽 reference doc + contract test fixture（mock receiver 驗簽成功/失敗/重放/idempotency）；可含 `tests/fixtures/webhook_hmac/` | 本票 receiver contract + `WH-P7-NOTIF-HMAC-impl-v1` 簽名輸出 |

> 註：`WH-P7-NOTIF-PROD-policy-v1` 原列 `WH-P7-NOTIF-HMAC-v1` 由本票拆分為 **impl** 與 **receiver-contract** 兩票，職責更清晰。

### 6. AllowedPaths / BlockedPaths

#### AllowedPaths

- `04_Workflows/tickets/WH-P7-NOTIF-HMAC-policy-v1_state.md`（本票 STATE / B/C/D_REPORT）
- `docs/outbox-and-feedback-layer-contract-v1.md`（**僅 §4.6.5 擴寫**；§4.6.0 可增 cross-ref 列，不重寫 §4.6.3–§4.6.4/§4.6.6）

#### BlockedPaths

- `delivery/**` · `routing/**` · `scripts/**` · `tests/**`
- `.github/workflows/**`（含 `p7-notification-smoke.yml`）
- 暗部 `gov_core_system/core/**`
- `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `.cursor/rules/**`
- `.env` · secrets · 客戶實際 webhook URL
- `WH-P7-NOTIF-PROD-policy-v1` 之 C_REPORT / D_REPORT（只讀引用）
- 任何 Python / YAML 實作檔

### 7. Dependencies

- `WH-P7-NOTIF-PROD-policy-v1`（§4.6 骨架 · `design_accepted`）
- `WH-P7-NOTIF-RETRY-SANDBOX-v1`（retry partial · at-least-once 冪等前提）
- `docs/outbox-and-feedback-layer-contract-v1.md` §4.2–§4.6.5（現行 SSOT）
- `delivery/notification_webhook_adapter_v1.py`（只讀對照 · Non-scope 註解）
- `tests/test_notification_webhook_dispatch_v1.py`（只讀 · 12/12 + retry cases）
- P8.9-T2/T3 downstream ack / dispatch registry 語意（`event_id` 權威）

---

## STATE

- **overall_status**: `design_accepted`
- **current_owner**: scribe
- **next_action**: 合約 §4.6.5 已由 HMAC-impl / receiver-contract 票分段落盤；後續 doc-sync 可選微調
- **last_updated**: 2026-06-23 · progress agent (§4.6.5 內容已由衍伸票承接)
- **wave**: Wave-H · P7 notification HMAC policy design
- **status_by_role**:
  - **Orchestrator (A)**: done — FRAME 已落盤
  - **Implementer (B)**: done — §4.6.5.1 sender（HMAC-impl）· §4.6.5.2 receiver（receiver-contract）已落盤
  - **Reviewer (C)**: done — 2026-06-23 · **`accepted_with_gaps`**（母 FRAME 已由衍伸票拆分交付）
  - **Scribe (D)**: done — 2026-06-23
- **notes**:
  - 本票 FRAME 為 policy 母本；實際 §4.6.5 擴寫由 `WH-P7-NOTIF-HMAC-impl-v1` · `WH-P7-NOTIF-HMAC-receiver-contract-v1` 承接
  - Idempotency-Key HTTP header 仍 **`not_implemented_yet`**

---

## B_REPORT

- **status**: policy 母 FRAME · 交付已拆分至 HMAC-impl（sender）· receiver-contract（receiver）· HMAC-prod-mandatory（tier gate）
- **cross_ref**: 合約 §4.6.5.1–§4.6.5.2 · `WH-P7-NOTIF-contract-doc-sync-v1` v2 索引

---

## C_REPORT

- **review_date**: 2026-06-23
- **verdict**: **`accepted_with_gaps`**
- **conclusion**: FRAME 規格與已落盤 §4.6.5 子節 **無矛盾**；sender partial · receiver contract documented 與 FRAME 一致。
- **gaps**: HTTP `Idempotency-Key` · receiver reference impl 仍 future。

---

## D_REPORT

- **handoff_date**: 2026-06-23
- **to**: contract-doc-sync 可選 §4.6.5 索引 refresh
