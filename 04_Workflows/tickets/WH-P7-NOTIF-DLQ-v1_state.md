# WH-P7-NOTIF-DLQ-v1 — Ticket State

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Wave-H+1 · **P7 prod 線第一張設計票**（doc-only · FRAME）  
> 範圍：**webhook DLQ / audit log 層** — 合約、檔案結構、inspect CLI 介面、test 方向；**零 code / 零 CI**  
> 上游：`WH-P7-sandbox-line-wrapup-v1` · `WH-P7-NOTIF-RETRY-SANDBOX-v1` · `WH-P7-NOTIF-PROD-policy-v1` §4.6.4  
> 產物：本票 FRAME（設計 SSOT 草案）；§4.6.4 具體擴寫留給下一張 Implementer 票

---

## FRAME

### handoff header

**P7 prod 線第一張設計票**：在 sandbox 線已封箱（emit → dispatch → localhost webhook → opt-in retry → env-gated HMAC sender → receiver contract 文檔）的基礎上，定義 **webhook 失敗事件 DLQ / audit log 層** 的合約、落盤結構、inspect CLI 介面與 unittest 方向。**本輪僅建票 + 填 FRAME**；不實作落盤、不實作 CLI、不變更 retry / HMAC 程式語意、不設計 prod URL tier。

---

### 1. Background

| 層級 | 現況 | 證據 |
|------|------|------|
| Sandbox retry | env 驅動、**default `max_attempts=0`**；retry 用盡後外層仍 **fail-open**（`ok=True`） | `WH-P7-NOTIF-RETRY-SANDBOX-v1` · `notification_webhook_adapter_v1` |
| 失敗可觀測性 | 僅 **記憶體 `webhook_result` + log warning**；**無 persist DLQ** | adapter docstring「No DLQ」；`test_retry_exhausted_on_persistent_500` 只 assert `retry_exhausted` |
| `webhook_result` 欄位（retry partial） | `attempt_count` · `retry_exhausted` · `last_error` · `http_status` · `endpoint_url` · `timestamp` | `WH-P7-NOTIF-RETRY-SANDBOX-v1` B_REPORT §2 |
| HMAC sender | **partial**（sandbox-only · env gated · default off）；與 retry 同路徑 | `WH-P7-NOTIF-HMAC-impl-v1` |
| 合約 §4.6.4 | 僅 high-level 一句：建議 `outbox/notification_dlq/` 或 jsonl；保留期 90 天；**`impl_status: not_implemented_yet`** | `docs/outbox-and-feedback-layer-contract-v1.md` §4.6.4 |
| §4.6.0 policy | `webhook_dlq_enabled` = `false` · **not_implemented_yet** | §4.6.0 policy 表 |
| Phase 8.8 分軌 | notification DLQ **must not** 與 `orchestration_bridge_outbox` 混用 | §2.2 |

**缺口**：prod 線需要比 sandbox 更強的 **失敗補償可觀測性**（§4.6.1 威脅模型已假設 retry/DLQ 補償）；現 retry 用盡或單次 POST 失敗後，operator 只能從 process log 反查，無法離線稽核、統計 per-endpoint 失敗率，也無 inspect 工具。§4.6.4 尚不足以指導 Implementer 落盤或寫測試。

---

### 2. Goal

產出 **webhook DLQ 設計 SSOT 草案**（下一輪 Implementer 擴寫 §4.6.4 或等價 doc），至少定義下列四塊。

#### 2.1 落盤格式與路徑（設計定案 · 待 Implementer 落盤）

**交付位置裁決（本票）**

| 方案 | 路徑 | 採用 |
|------|------|------|
| **A — 併入 §4.6.4** | `docs/outbox-and-feedback-layer-contract-v1.md` §4.6.4 擴寫 | **首選**（與 §4.6.3 retry · §4.6.5 HMAC 同 SSOT） |
| **B — 獨立附錄** | `docs/notification-dlq-contract-v1.md` | **可選**；僅當 §4.6.4 + inspect CLI 規格過長時，由 Implementer 自 §4.6.4 cross-ref |

**命名空間與檔案布局（proposed_default）**

| 項 | 定案 |
|----|------|
| 根目錄 | **`outbox/notification_dlq/`**（repo-relative；對齊 §4.6.4 既有建議與 §2 outbox 命名空間模型；**不**採 `artifacts/` — artifacts 非本 repo outbox SSOT） |
| 主 stream | **`outbox/notification_dlq/events.jsonl`** — append-only，一行一筆 DLQ 事件 |
| 可選 sidecar | **`outbox/notification_dlq/<event_id>_<dlq_ts>.json`** — 完整 snapshot（Implementer 可二選一或雙寫；本票要求 jsonl **至少**存在） |
| `schema_id` | **`notification_webhook_dlq_v1`** |
| Retention | **90 天**（與 §2 多數 outbox namespace 一致；Implementer 在 §4.6.4 寫清 operator 清理責任，本 repo 不強制 cron） |
| Git | **gitignored**（與其他 `outbox/` 樹一致） |

**DLQ 寫入觸發（與 retry / HMAC 互補 · 不改現有語意）**

| 條件 | 是否寫 DLQ | 說明 |
|------|------------|------|
| HTTP POST 成功（2xx） | **否** | 正常路徑 |
| `dry_run` / webhook disabled / URL gate 拒絕 | **否** | 未實際投遞 |
| 單次 POST 失敗且 `max_attempts=0`（default） | **是**（prod DLQ enabled 時） | sandbox 現況不寫；prod impl 票啟用 |
| Retry 進行中、尚未用盡 | **否** | 僅最終失敗落 DLQ |
| `retry_exhausted=True` | **是** | 對齊 sandbox `webhook_result` 語意 |
| 不可重試 4xx（400 等）單次失敗 | **是** | 與 retry 用盡同等對待 |

> **互補原則**：retry / HMAC **行為不變**；DLQ 為 **事後 audit** 層。adapter 仍 fail-open；DLQ 寫入失敗 **must not** 阻斷 dispatch（與 emit fail-open 對齊）。

#### 2.2 DLQ 記錄欄位（minimum · proposed_default）

每筆 jsonl 物件 **must** 含下列欄位；Implementer 可增 optional 欄位但不得刪 required。

| 欄位 | 型別 | Required | 說明 |
|------|------|----------|------|
| `schema_id` | string | yes | 固定 `notification_webhook_dlq_v1` |
| `dlq_written_at` | string (ISO-8601 UTC) | yes | DLQ 落盤時間 |
| `event_id` | string | yes | 與 gateway emit / webhook payload 一致 |
| `event_type` | string | yes | 如 `delivery.bundle_ready` |
| `case_ref` | string \| null | yes | dispatch context |
| `endpoint_url` | string | yes | 實際 POST URL（redact query secrets if any） |
| `endpoint_tier` | string | yes | `sandbox` \| `staging` \| `prod`；sandbox impl 固定 `sandbox`；tier 來源留 PROD-URL 票 |
| `attempt_count` | int | yes | 來自 `webhook_result.attempt_count` |
| `retry_exhausted` | bool | yes | 來自 `webhook_result.retry_exhausted` |
| `last_error` | string \| null | yes | 來自 `webhook_result.last_error` |
| `http_status` | int \| null | yes | 最後一次 HTTP 狀態 |
| `webhook_result` | object | yes | **完整** adapter `webhook_result` snapshot（非破壞性引用 SSOT） |
| `source_notification_path` | string \| null | no | 可選：對應 `outbox/notification_events.jsonl` 或 per-event JSON 路徑 |

**與 `webhook_result` 關聯**：DLQ 列 **must** embed 當次 `webhook_result` 物件；inspect CLI **may** 僅投影 top-level 欄位，detail 模式展開 `webhook_result`。

#### 2.3 Inspect CLI 基本需求（介面 only · 不實作）

建議模組名（Implementer 票定稿）：`delivery/inspect_notification_dlq_v1.py` 或 `scripts/inspect_notification_dlq_v1.py` — 對齊 `tools.inspect_tabular_outbox` list + `--json` 模式。

**子命令 / 模式**

| 模式 | 用途 |
|------|------|
| **list**（default） | 列出 DLQ 條目（newest first） |
| **stats** | 輸出簡單聚合 |

**CLI 旗標（proposed_default）**

| 旗標 | 說明 |
|------|------|
| `--dlq-root PATH` | 預設 `outbox/notification_dlq` |
| `--json` | stdout 結構化 JSON（與 tabular inspect 一致） |
| `--since ISO8601` / `--until ISO8601` | 時間範圍過濾（基於 `dlq_written_at`） |
| `--endpoint URL_SUBSTR` | endpoint_url 子字串過濾 |
| `--event-id ID` | 精確 event_id |
| `--tier sandbox\|staging\|prod` | endpoint_tier 過濾 |
| `--code HTTP_STATUS` | 過濾 `http_status`（如 `500`） |
| `--limit N` | 列表上限 |

**list 模式 stdout JSON 形狀（草案）**

| 欄位 | 型別 | Required |
|------|------|----------|
| `ok` | bool | yes |
| `count` | int | yes |
| `entries` | array | yes |

`entries[]` 每項至少：`dlq_written_at` · `event_id` · `event_type` · `endpoint_url` · `endpoint_tier` · `attempt_count` · `last_error` · `http_status` · `retry_exhausted`。

**stats 模式 stdout JSON 形狀（草案）**

| 欄位 | 型別 | 說明 |
|------|------|------|
| `ok` | bool | |
| `total_count` | int | 符合 filter 的總筆數 |
| `by_endpoint` | object | `{ "<endpoint_url>": count }` |
| `by_tier` | object | `{ "sandbox": n, ... }` |
| `by_http_status` | object | `{ "500": n, "null": n }` |

#### 2.4 Test 方向（本票定義 · 下票實作）

Implementer / DLQ-impl 票 **should** 在 `tests/test_notification_webhook_dispatch_v1.py` 或新檔 `tests/test_notification_dlq_v1.py` 覆蓋：

| # | 場景 | 斷言方向 |
|---|------|----------|
| T-1 | DLQ disabled（default / sandbox） | retry 用盡 → **無** jsonl 寫入；`webhook_result` 行為不變 |
| T-2 | DLQ enabled + retry exhausted | `events.jsonl` 新增 1 行；required 欄位齊；`webhook_result` 嵌套一致 |
| T-3 | DLQ enabled + 不可重試 400 | 單次失敗亦落 DLQ |
| T-4 | DLQ write fail-open | 模擬磁碟不可寫 → adapter 仍 `ok=True`；log warning |
| T-5 | inspect list `--json` | fixture jsonl → `count` / `entries` 形狀 |
| T-6 | inspect filter | `--endpoint` / `--code` / `--since` 過濾正確 |
| T-7 | inspect stats | `by_endpoint` 計數正確 |

Fixture 建議：`tests/fixtures/notification_dlq/events.jsonl`（2–3 行 synthetic；無真實 URL / secret）。

#### 2.5 Env gate（設計 · 對齊 §4.6.6 future）

| Env 鍵 | Default | 說明 |
|--------|---------|------|
| `GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED` | `0` | `1` 時失敗事件落 DLQ |
| `GOV_NOTIFICATION_WEBHOOK_DLQ_ROOT` | `outbox/notification_dlq` | 可覆寫根目錄 |

> sandbox 線 **維持 default off**；prod impl 票才接線。§4.6.0 `webhook_dlq_enabled` 在 doc 落盤後標 **partial** 或 **implemented**（依 impl 票範圍）。

---

### 3. Non-Goals

- ❌ **不實作**任何落盤邏輯、inspect CLI 程式碼、或 CI workflow。
- ❌ **不設計**「自動重送 DLQ / replay pipeline」（→ 未來 `WH-P7-NOTIF-DLQ-replay-v1` 或同主題票）。
- ❌ **不變更** retry 或 HMAC 現有語意；僅描述 DLQ 如何 **讀取** `webhook_result` 並 **事後** 落盤。
- ❌ **不設計** prod / staging URL tier、`GOV_NOTIFICATION_WEBHOOK_TIER`、non-localhost allowlist（→ `WH-P7-NOTIF-PROD-URL-v1`）。
- ❌ **不修改** `docs/outbox-and-feedback-layer-contract-v1.md`（本輪）；§4.6.4 擴寫留 Implementer 下一票。
- ❌ **不合併** Phase 8.8 `orchestration_bridge_outbox` DLQ（§2.2 永久分軌）。
- ❌ **不升格** advisory CI；不新增 required check。

---

### 4. Acceptance Criteria（設計層 · 本票 FRAME）

- **AC-1**：FRAME 含 Background / Goal / Non-goals / AC / AllowedPaths / BlockedPaths（本檔）。
- **AC-2**：路徑、jsonl 格式、`schema_id`、required 欄位、retention、DLQ 觸發條件均已 **具體** 寫入 FRAME §2（Implementer 下一票照抄擴寫 §4.6.4）。
- **AC-3**：inspect CLI 介面（list / stats、旗標、stdout JSON 形狀）已寫入 FRAME §2.3（**無**程式）。
- **AC-4**：test 方向 ≥5 條（本票 §2.4 共 7 條）。
- **AC-5**：明確 **與 `webhook_result` 關聯**（embed snapshot + 觸發條件表）。
- **AC-6**：列出 ≥2 張 **後續實作票**（§5）。
- **AC-7**：§4.6.4 擴寫位置裁決：**首選 §4.6.4 本節**；可選 `docs/notification-dlq-contract-v1.md` cross-ref（§2.1）。
- **AC-8**：文檔工單自檢（APP-DOC）：FRAME 正文零本機絕對路徑、零 secret 範例值。

#### AC 交付物對照（下一輪 Implementer · 非本票）

| 交付物 | 位置 | 本票狀態 |
|--------|------|----------|
| §4.6.4 具體擴寫 | `docs/outbox-and-feedback-layer-contract-v1.md` | **待下一票** |
| 可選獨立 DLQ doc | `docs/notification-dlq-contract-v1.md` | **optional** |
| §4.6.0 `webhook_dlq_enabled` 更新 | 同上 | **待 impl 票** |

---

### 5. 建議衍伸實作票（本票外 · AC-6）

| 票號（建議） | 範圍摘要 | 依賴 |
|--------------|----------|------|
| `WH-P7-NOTIF-DLQ-impl-v1` | adapter 失敗路徑寫入 `outbox/notification_dlq/events.jsonl`；env gate；fail-open；unittest T-1–T-4；§4.6.4 + §4.6.0 更新 | 本票 FRAME sign-off · `WH-P7-NOTIF-RETRY-SANDBOX-v1` |
| `WH-P7-NOTIF-DLQ-inspect-cli-v1` | inspect list/stats CLI + fixture + unittest T-5–T-7 | DLQ-impl-v1 或並行（可讀 fixture jsonl） |

> 註：原 §4.6.7 索引將 `WH-P7-NOTIF-DLQ-v1` 標為「落盤 + inspect 合一」；prod 線拆為 **design（本票）→ impl → inspect-cli** 三段，職責對齊 HMAC 線。

---

### 6. AllowedPaths / BlockedPaths

#### AllowedPaths

- `04_Workflows/tickets/WH-P7-NOTIF-DLQ-v1_state.md`（本票 STATE / FRAME / B/C/D_REPORT）
- **下一輪 Implementer 可碰**：
  - `docs/outbox-and-feedback-layer-contract-v1.md`（**僅 §4.6.4** 擴寫；§4.6.0 cross-ref）
  - `docs/notification-dlq-contract-v1.md`（**可選**新增）

#### BlockedPaths

- `delivery/**`（含 `notification_webhook_adapter_v1.py` — 本票 **只讀** 對照）
- `tests/**`（含 `tests/fixtures/**`）
- `.github/workflows/**`（含 `p7-notification-smoke.yml`）
- `routing/**` · `scripts/**`（inspect 實作下票才開）
- 暗部 `gov_core_system/core/**`
- `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `.cursor/rules/**`
- `.env` · secrets · 客戶實際 webhook URL

---

### 7. Dependencies

- `WH-P7-sandbox-line-wrapup-v1`（sandbox 封箱 · prod 入口索引）
- `WH-P7-NOTIF-RETRY-SANDBOX-v1`（`webhook_result` 欄位 SSOT）
- `WH-P7-NOTIF-HMAC-impl-v1`（只讀 · 同 adapter 路徑）
- `WH-P7-NOTIF-PROD-policy-v1`（§4.6.4 骨架 · `design_accepted`）
- `docs/outbox-and-feedback-layer-contract-v1.md` §4.6.3–§4.6.4 · §2.2
- `delivery/notification_webhook_adapter_v1.py`（只讀）
- `tests/test_notification_webhook_dispatch_v1.py`（只讀）

---

## STATE

- **overall_status**: `validated`
- **current_owner**: done
- **next_action**: 無 — 設計 SSOT 已交付；落盤與 inspect CLI 分別由 `WH-P7-NOTIF-DLQ-impl-v1` · `WH-P7-NOTIF-DLQ-inspect-cli-v1` / `*-impl-v1` 接棒並已收口
- **last_updated**: 2026-06-22 · scribe (D) — P7 DLQ 設計線 closure
- **wave**: Wave-H+1 · P7 prod line · notification DLQ design
- **status_by_role**:
  - **Orchestrator (A)**: done — FRAME 落盤
  - **Implementer (B)**: done — §4.6.4 四子節擴寫（layout / schema / retention / inspect CLI design）
  - **Reviewer (C)**: done — design accepted（見 C_REPORT）
  - **Scribe (D)**: done — Progress append · 2026-06-22 P7 DLQ 收口

---

## B_REPORT

- **implementer_date**: 2026-06-22
- **scope**: doc-only · `docs/outbox-and-feedback-layer-contract-v1.md` §4.6.4 擴寫；無 code / CI / 其他 docs 變更

### 1. §4.6.4 子節交付

| 子節 | 內容摘要 |
|------|----------|
| **§4.6.4.1 DLQ file layout** | 定案 `outbox/notification_dlq/events.jsonl`（append-only · UTF-8 · 一行一 JSON）；可選 sidecar；`schema_id=notification_webhook_dlq_v1`；gitignored |
| **§4.6.4.2 DLQ record schema** | required 欄位表（含 `timestamp` · `tier` · `event_id` · `endpoint` · `http_status` · `attempt_count` · `last_error` · `request_headers` · `payload_digest` · embed `webhook_result`）；redact / digest 規則 |
| **§4.6.4.3 Retention & privacy** | 90 天保留；禁止長期備份/非必要複製；secret 禁令；DLQ 寫入 fail-open |
| **§4.6.4.4 Inspect CLI (design only)** | list/stats 子命令、旗標、`--json` stdout 形狀；明確標 **design only**，實作留 `WH-P7-NOTIF-DLQ-impl-v1` / `WH-P7-NOTIF-DLQ-inspect-cli-v1` |

另於 §4.6.4 本節補：DLQ 寫入觸發表 · env gate 表 · 與 §4.6.3 retry / §2.2 分軌 cross-ref。

### 2. Schema 核心欄位（§4.6.4.2）

`schema_id` · `timestamp` · `dlq_written_at` · `tier` · `event_id` · `event_type` · `case_ref` · `endpoint` · `http_status` · `attempt_count` · `retry_exhausted` · `last_error` · `request_headers` · `payload_digest`（optional）· `webhook_result`（embed snapshot）

### 3. Inspect CLI scope（一句話）

設計目標為唯讀 list/stats CLI，可過濾時間/tier/endpoint/http_status 並以 `--json` 投影 DLQ 列，**不含落盤或 replay**——實作分屬後續 impl 與 inspect-cli 票。

### 4. 驗證

- 文檔工單自檢（APP-DOC）：§4.6.4 正文零本機絕對路徑、零 secret 範例值 ✅
- 無 runtime 命令（doc-only 票）

### 5. 阻塞

無。

---

## C_REPORT

- **reviewer_date**: 2026-06-22
- **verdict**: `accepted`

### 1. 設計完整性

- FRAME §2 已具體定案：路徑 `outbox/notification_dlq/events.jsonl` · `schema_id=notification_webhook_dlq_v1` · 觸發表 · env gate · inspect CLI 介面 · test 方向 T-1–T-7。
- B_REPORT §4.6.4 四子節（layout / schema / retention / inspect CLI design-only）與 FRAME 一致；§2.2 分軌 cross-ref 正確。

### 2. 下游接棒

- 落盤：`WH-P7-NOTIF-DLQ-impl-v1` — **validated**
- inspect CLI 設計：`WH-P7-NOTIF-DLQ-inspect-cli-v1` — **validated**；實作：`WH-P7-NOTIF-DLQ-inspect-cli-impl-v1` — **validated**

### 3. 阻塞

無。

---

## D_REPORT

- **scribe_date**: 2026-06-22
- **verdict**: `validated`（設計票 · doc-only）
- **handoff_summary**: P7 prod 線 **DLQ 設計 SSOT** 已封箱：§4.6.4 layout / schema / retention / inspect CLI 設計目標由本票 FRAME + B_REPORT 定案；實作與 operator 工具已分票交付並收口。
- **Progress**: `00_Agent_Work_Progress.md` — **2026-06-22 · P7 · DLQ 線收口**（Scribe append）
