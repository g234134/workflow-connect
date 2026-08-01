# WH-P7-NOTIF-HMAC-receiver-contract-v1 — Ticket State

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Wave-H · **receiver contract 設計票（doc-only · fixture 需求）**  
> 定位：**接收方驗簽 / 重放防護 / idempotency 合約** SSOT 草案；不含 receiver 程式實作。  
> 上游：`WH-P7-NOTIF-HMAC-policy-v1`（policy · `frame_ready`）· `WH-P7-NOTIF-HMAC-impl-v1`（sender HMAC · `impl_done`）· `WH-P7-NOTIF-PROD-policy-v1`（§4.6 骨架 · `design_accepted`）  
> 產物：receiver contract 文檔草案 + fixture 需求索引；**零 sender code / 零 CI 變更**

---

## FRAME

### handoff header

本票為 **P7 通知鏈 receiver 端合約設計票**：定義客戶 webhook endpoint 應如何從 HTTP headers 取得 timestamp / signature / event id、如何驗簽、如何處理 timestamp 窗口與重放、以及如何映射 idempotency 至「已處理」狀態。**本輪僅 FRAME + 下一輪 Implementer 落盤合約文本**；不在本 repo 實作 receiver 程式碼、不改 sender adapter / tests / CI。

Sender 端 HMAC-SHA256 已 **partial 實作**（`WH-P7-NOTIF-HMAC-impl-v1` · env gated · sandbox default off）；合約 §4.6.5 已有 sender v1 摘要。**Receiver 端目前無 SSOT**：無 reference 實作、無 contract test fixture、無對「怎樣才算重放 / 驗簽失敗回什麼 status」的統一說法。

---

### 1. Background

| 層級 | 現況 | 證據 |
|------|------|------|
| Sender HMAC | **partial**（sandbox-only · env gated · default off） | `WH-P7-NOTIF-HMAC-impl-v1` · `notification_webhook_adapter_v1` · `tests.test_notification_webhook_dispatch_v1` **19/19**（含 3 HMAC scenario） |
| Sender headers（事實標準） | `X-Gov-Signature-256`（`sha256=<hex>`）· `X-Gov-Timestamp`（Unix epoch seconds UTC）· `X-Gov-Event-Id`（= body `event_id`） | adapter `_apply_hmac_headers` · signed string = `{timestamp}.{event_id}.{raw_body_utf8}` |
| Env gate | `GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED=1` **且** `GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET` 非空 | 缺 secret → fail-open unsigned |
| Retry（at-least-once 前提） | **partial**（sandbox-only · default 0） | `WH-P7-NOTIF-RETRY-SANDBOX-v1` · 同 `event_id` 可重送 |
| HTTP `Idempotency-Key` header | **not_implemented_yet** | sender 未送；receiver 合約須以 `X-Gov-Event-Id` / body `event_id` 為 SSOT |
| Receiver 驗簽 / 重放 / idempotency | **not_implemented_yet** | §4.6.5 僅一行 cross-ref 本票；無 fixture · 無 sample impl |
| DLQ / prod URL / HMAC 強制 | **not_implemented_yet** | §4.6.3–§4.6.6 · 本票僅引用 |

**缺口**：policy 票（`WH-P7-NOTIF-HMAC-policy-v1`）已定 sender/receiver 分工與 proposed defaults，但 **receiver contract 未擴寫**；impl 票僅覆 sender。客戶整合方無可審計的驗簽 pseudo-code、重放表、HTTP 語意與 idempotency 狀態機。

---

### 2. Goal

產出一份 **receiver 端合約草案**（Implementer 下一輪落盤），作為客戶 webhook endpoint 的 normative SSOT。

#### 交付位置裁決（本票）

**方案 A — 併入 `docs/outbox-and-feedback-layer-contract-v1.md` §4.6.5 子節 `§4.6.5.2 Receiver contract`（首選）**

| 理由 | 說明 |
|------|------|
| SSOT 單一 | §4.6 已是 prod-tier policy SSOT；sender v1 已在 §4.6.5 同節 |
| 上游對齊 | `WH-P7-NOTIF-HMAC-policy-v1` 已裁決 §4.6.5.1 sender · §4.6.5.2 receiver · §4.6.5.3 idempotency · §4.6.5.4 examples |
| 交叉引用 | §4.6.0 `webhook_hmac` policy 列可直接指向同節 receiver 小節 |
| 維護成本 | 避免 `policy doc` + `receiver doc` 雙 SSOT 漂移 |

> **不採方案 B**（獨立 `docs/notification-webhook-hmac-receiver-contract-v1.md`）：除非 Implementer 發現 §4.6.5 篇幅過長需客戶-facing PDF 匯出；屆時可 **自 §4.6.5.2 匯出**，非本票預設路徑。

#### 合約須明確定義（Implementer AC 對照）

| 主題 | 須定義內容 |
|------|------------|
| Header 擷取 | 從 `X-Gov-Timestamp` · `X-Gov-Signature-256` · `X-Gov-Event-Id` 讀值；header 名可 env override 時 receiver **must** 以 onboarding 文件為準（預設名見 sender impl） |
| 驗簽流程 | 讀 **原樣** HTTP body bytes（禁止 receiver 自行 re-serialize JSON）；recompute `{timestamp}.{event_id}.{body}` → HMAC-SHA256 → compare `sha256=<hex>`（constant-time） |
| Timestamp 窗口 | `proposed_default`：**±300 秒（5 分鐘）** UTC skew；窗口外 → **401**（或 403，Implementer 定稿擇一並說明） |
| Header ↔ body 一致 | `X-Gov-Event-Id` **must** 等於 JSON body `event_id`；不一致 → **400** |
| 重放防護 | 同一 `(event_id)` 或 `(event_id, timestamp)` 在 `max_seen_window` 內重複 → 視為 replay；**must not** 重複執行 side effect |
| Idempotency | 同 `event_id` 已處理 → 回 **2xx**（idempotent accept，建議 **200** 或 **202**）並跳過 side effect；與 §4.6.3 retry at-least-once 協作 |
| 驗簽失敗 | **401/403**；**must not** 回 5xx（避免 sender retry 風暴；對照 §4.6.3 可重試狀態碼） |
| 缺 HMAC headers | staging/prod tier（future）→ 拒絕；sandbox 無簽名 POST 仍可能存在 → receiver 依 tier 政策（本票僅文檔，不實作 tier gate） |

#### Fixture 需求（本票定義、下票實作）

Implementer 落盤合約時，**須在文檔末尾或 §4.6.5.4** 列出 fixture 目錄需求（實際檔案由衍伸票交付）：

- `tests/fixtures/webhook_hmac/`（建議）
  - `signed_delivery_bundle_ready.json` + sidecar `*.headers.json`（含假 hex signature）
  - `replay_same_event_id.json`（同 event_id 第二次 POST 預期行為說明）
  - `invalid_signature.json` · `expired_timestamp.json` · `event_id_mismatch.json`

---

### 3. Non-Goals

- ❌ **不在本 repo 實作** receiver 程式碼（含 mock server 驗簽邏輯、gateway、adapter）。
- ❌ **不決定**客戶實際採用何種語言 / framework / 持久化（Redis / DB / in-memory）。
- ❌ **不更改** sender HMAC header 格式、signed string、env 鍵名（本票假定 sender impl 為事實標準）。
- ❌ **不修改** `delivery/**` · `tests/**` · `.github/workflows/**` · routing / dispatch / gateway。
- ❌ **不改** retry / DLQ / prod URL policy 正文（僅引用 §4.6.3–§4.6.6）。
- ❌ **不送** HTTP `Idempotency-Key` header（仍 sender future；receiver 合約以 `event_id` 為鍵）。
- ❌ **不升格** advisory CI；不新增 CI secret。
- ❌ **不合併** Phase 8.8 `orchestration_bridge_outbox`（§2.2 永久分軌）。

---

### 4. Acceptance Criteria（合約落盤時 · Implementer 下一輪）

- **AC-1**：`docs/outbox-and-feedback-layer-contract-v1.md` **§4.6.5.2 Receiver contract**（或等價子標）擴寫完成，與 sender v1（§4.6.5 / impl 票）**無矛盾**。
- **AC-2**：含 **簽名驗證 pseudo-code** 段落（pseudo language；**非**可執行 Python/JS）。
- **AC-3**：含 **重放防護小表**（至少欄位：`timestamp_window` · `max_seen_window` · `storage_key` · `on_replay`）。
- **AC-4**：含 **時序圖**（sender POST → receiver 驗簽 → idempotency 檢查 → 狀態變更 / HTTP 回應）；Mermaid 或 ASCII 均可。
- **AC-5**：含 **HTTP 回應語意表**（驗簽失敗 / 過期 timestamp / replay / 首次成功 / 冪等重送）。
- **AC-6**：§4.6.0 `webhook_hmac` 或 §4.6.5 更新 receiver 相關 `impl_status` 為 **`partial`**（contract documented；reference impl **`not_implemented_yet`**）。
- **AC-7**：列出 ≥2 張 **future 實作票**（見下）；B_REPORT 含與 `WH-P7-NOTIF-HMAC-impl-v1` sender headers 對照。
- **AC-8**：文檔工單自檢（APP-DOC）：零本機絕對路徑、零真值 secret、禁區僅類型描述。

#### AC-2 / AC-3 / AC-4 草案骨架（Implementer 可逐字擴寫）

**Pseudo-code（驗簽 · 草案）**

```
FUNCTION verify_gov_webhook(request, shared_secret):
  body_bytes = READ_RAW_BODY(request)           // do NOT re-json.dumps
  timestamp  = HEADER(request, "X-Gov-Timestamp")
  event_id_h = HEADER(request, "X-Gov-Event-Id")
  sig_header = HEADER(request, "X-Gov-Signature-256")

  IF missing(timestamp) OR missing(sig_header):
    RETURN REJECT(401, "missing_signature_headers")

  IF NOT parse_int(timestamp) OR ABS(now_utc - timestamp) > TIMESTAMP_WINDOW:
    RETURN REJECT(401, "timestamp_out_of_window")

  event_id_b = JSON_FIELD(body_bytes, "event_id")
  IF event_id_h != event_id_b:
    RETURN REJECT(400, "event_id_mismatch")

  message = CONCAT(timestamp, ".", event_id_b, ".", UTF8(body_bytes))
  expected = "sha256=" + HMAC_SHA256_HEX(shared_secret, message)
  IF NOT constant_time_equals(sig_header, expected):
    RETURN REJECT(401, "invalid_signature")

  IF replay_cache_contains(storage_key(event_id_b)):
    RETURN ACCEPT_IDEMPOTENT(200)               // no side effect

  replay_cache_store(storage_key(event_id_b), TTL=max_seen_window)
  PROCESS_BUSINESS_LOGIC(body_bytes)
  RETURN ACCEPT(200)
```

**重放防護表（proposed_default · 草案）**

| 欄位 | proposed_default | 說明 |
|------|------------------|------|
| `timestamp_window` | **300 s** | 允許 UTC skew；超出拒絕（非 replay 快取） |
| `max_seen_window` | **86400 s（24 h）** | `event_id` 去重快取 TTL；應 ≥ retry 最大跨度 + clock skew |
| `storage_key` | `gov:webhook:event:{event_id}` | 邏輯鍵；實作可為 DB unique / Redis SET |
| `on_replay` | **200 + skip side effect** | 同 `event_id` 已處理；**must not** 回 5xx |

**時序圖（草案 · Mermaid）**

```mermaid
sequenceDiagram
  participant S as Gov Sender (adapter)
  participant R as Customer Receiver
  participant C as Replay Cache
  participant B as Business Handler

  S->>R: POST /webhook + body + HMAC headers
  R->>R: Read raw body; parse headers
  alt timestamp outside window or bad signature
    R-->>S: 401/403 (no retry storm)
  else event_id header != body
    R-->>S: 400
  else replay_cache hit (same event_id)
    R-->>S: 200 idempotent (no B)
  else first delivery
    R->>C: store event_id (TTL=max_seen_window)
    R->>B: process once
    B-->>R: ok
    R-->>S: 200
  end
  Note over S,R: Retry may resend same event_id;<br/>receiver must stay idempotent
```

---

### 5. 建議衍伸實作票（本票外 · AC-7 要求）

| 票號（建議） | 範圍摘要 | 依賴 |
|--------------|----------|------|
| `WH-P7-NOTIF-HMAC-receiver-fixtures-v1` | 在 `tests/fixtures/webhook_hmac/` 放置一組 **已簽名** 樣本（body + headers sidecar + README）；假 secret / 假 hex；供 contract test 與客戶對照 | 本票 AC-1–AC-5 定稿 · `WH-P7-NOTIF-HMAC-impl-v1` sender 輸出 |
| `WH-P7-NOTIF-HMAC-receiver-sample-impl-v1` | 最小 **reference receiver**（建議 Python stdlib `hmac` mock HTTP handler 或獨立 `verify_gov_webhook` 函式）+ contract test（成功 / 失簽 / 過期 / replay / event_id mismatch） | fixtures 票 · 本票 §4.6.5.2 |

> 註：原 `WH-P7-NOTIF-HMAC-policy-v1` 將 impl + receiver 合併為單票；現已拆分為 **impl**（done）· **receiver-contract**（本票 · doc）· **fixtures** · **sample-impl** 四段，職責更清晰。

---

### 6. AllowedPaths / BlockedPaths

#### AllowedPaths

- `04_Workflows/tickets/WH-P7-NOTIF-HMAC-receiver-contract-v1_state.md`（本票 STATE / B/C/D_REPORT）
- `docs/outbox-and-feedback-layer-contract-v1.md`（**下一輪 Implementer**：僅 §4.6.5.2–§4.6.5.4 receiver / idempotency / examples 擴寫；§4.6.0 可增 cross-ref）

#### BlockedPaths

- `delivery/**` · `routing/**` · `scripts/**` · `tests/**`（含 `tests/fixtures/**` — fixture **內容**下票再做）
- `.github/workflows/**`（含 `p7-notification-smoke.yml`）
- 暗部 `gov_core_system/core/**`
- `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `.cursor/rules/**`
- `.env` · secrets · 客戶實際 webhook URL
- `WH-P7-NOTIF-HMAC-impl-v1` 之 sender 程式（本票 **只讀** 對照）
- 任何 Python / YAML 實作檔

---

### 7. Dependencies

- `WH-P7-NOTIF-HMAC-impl-v1`（sender HMAC · `impl_done` · headers / signed string SSOT）
- `WH-P7-NOTIF-HMAC-policy-v1`（policy proposed defaults · §4.6.5 結構）
- `WH-P7-NOTIF-PROD-policy-v1`（§4.6 骨架 · fail-open / tier 引用）
- `WH-P7-NOTIF-RETRY-SANDBOX-v1`（at-least-once 冪等前提）
- `docs/outbox-and-feedback-layer-contract-v1.md` §4.6.5（現行 sender 摘要）
- `delivery/notification_webhook_adapter_v1.py`（只讀）
- `tests/test_notification_webhook_dispatch_v1.py`（只讀 · HMAC sender tests）

---

## STATE

- **overall_status**: `done_with_gaps`
- **current_owner**: scribe
- **next_action**: 開 `WH-P7-NOTIF-HMAC-receiver-fixtures-v1` · `WH-P7-NOTIF-HMAC-receiver-sample-impl-v1`（S3 staging 前置）
- **last_updated**: 2026-06-23 · reviewer + scribe (C/D)
- **wave**: Wave-H · P7 notification HMAC receiver contract design
- **status_by_role**:
  - **Orchestrator (A)**: pending — 待 Reviewer sign-off
  - **Implementer (B)**: done — 2026-06-22 · §4.6.5.2 合約落盤
  - **Reviewer (C)**: done — 2026-06-23 · **`accepted_with_gaps`**
  - **Scribe (D)**: done — 2026-06-23 · D_REPORT 收口
- **notes**:
  - §4.6.5.2 receiver contract **已落盤**；reference impl / fixtures 仍 **`not_implemented_yet`**
  - Sender headers 以 `WH-P7-NOTIF-HMAC-impl-v1` 為事實標準，本票未變更 sender

---

## B_REPORT

### §1 變更檔案

| 檔案 | 變更 |
|------|------|
| `docs/outbox-and-feedback-layer-contract-v1.md` | §4.6.5 重構：§4.6.5.1 sender · **§4.6.5.2 receiver contract** 完整落盤 |
| `04_Workflows/tickets/WH-P7-NOTIF-HMAC-receiver-contract-v1_state.md` | STATE + B_REPORT |

### §2 §4.6.5.2 落盤摘要

| 區塊 | 已寫入 |
|------|--------|
| Receiver 假設 | headers（`X-Gov-Signature-256` / `X-Gov-Timestamp` / `X-Gov-Event-Id`）、JSON raw body canonicalization、缺 header → 驗簽失敗 |
| 簽名驗證 pseudo-code | `verify_gov_webhook` 完整 pseudo-code（raw body · signed string · constant-time compare） |
| Timestamp / 重放 | `timestamp_window_sec=300` · `max_seen_window_sec=86400` · `storage_key=<tenant>/<endpoint>/<event_id>` · `on_replay` 表 |
| Idempotency | `processed_events` 映射 · 首次寫入 / 重送 skip side-effect · 與 §4.6.3 retry 協作 |
| HTTP 語意 | 驗簽失敗 401/403 · replay 200（推薦）或 409 · 禁止 5xx 誘發 retry 風暴 |
| 時序 | 3 行文本時序（Sender POST → Receiver 驗簽/idempotency → HTTP 回應） |
| Future 票 | `WH-P7-NOTIF-HMAC-receiver-fixtures-v1` · `WH-P7-NOTIF-HMAC-receiver-sample-impl-v1` |

### §3 與 sender impl 對照

| Sender（`WH-P7-NOTIF-HMAC-impl-v1`） | §4.6.5.2 receiver |
|--------------------------------------|-------------------|
| `X-Gov-Signature-256` = `sha256=<hex>` | pseudo-code 比對同一格式 |
| Signed string `{timestamp}.{event_id}.{body}` | 一致；禁止 receiver re-serialize |
| Env 可覆寫 header 名 | receiver 以 onboarding 文件為準 |
| Retry 同 `event_id` | receiver idempotency + seen-set 承接 |

### §4 驗證

- 無 runtime 驗證（純文檔票）。
- 人工對照：`notification_webhook_adapter_v1` HMAC headers / signed message 與 §4.6.5.2 pseudo-code **無矛盾**；`tests.test_notification_webhook_dispatch_v1` HMAC digest 測試與 canonicalization 一致。

### §5 阻塞

無。

### §6 刻意留待後續票

- seen-set 持久化後端（Redis / DB / in-memory）
- replay 回 **409** vs **200** 的客戶可配置策略
- staging/prod tier 缺 HMAC headers 強制拒絕（§4.6.6 gate）
- HTTP `Idempotency-Key` header
- fixture 目錄與 reference receiver 程式

---

## C_REPORT

- **review_date**: 2026-06-23
- **reviewer_role**: P7 HMAC receiver contract Reviewer (C)
- **verdict**: **`accepted_with_gaps`**
- **scope**: §4.6.5.2 落盤 vs `WH-P7-NOTIF-HMAC-impl-v1` sender headers / signed string · §4.6.3 retry at-least-once 冪等協作
- **conclusion**: pseudo-code · 重放表 · HTTP 語意 · 時序與 sender impl **無矛盾**；§4.6.0 `webhook_hmac` receiver 列可標 **contract documented**。
- **gaps（non-blocking）**: reference impl · `tests/fixtures/webhook_hmac/` · contract test **not_implemented_yet**（§5 future 票）。

---

## D_REPORT

- **handoff_date**: 2026-06-23
- **from**: P7 HMAC receiver contract（`done_with_gaps` · doc SSOT 已落盤）
- **to**: Orchestrator（fixtures + sample-impl 票 · staging S3 硬依賴）
- **notes**: 本票 **doc-only**；receiver 程式與 fixture 內容留衍伸票，不阻塞 sandbox 線 wrap-up。
