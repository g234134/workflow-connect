# WH-P7-NOTIF-DLQ-inspect-cli-v1 — Ticket State

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Wave-H+1 · **P7 prod 線** · **唯讀 DLQ inspect CLI 設計票**（doc-only · FRAME）  
> 上游：`WH-P7-NOTIF-DLQ-v1` · `WH-P7-NOTIF-DLQ-impl-v1`（落盤已完成）  
> 範圍：定義 inspect CLI scope / 介面 / 非目標 / use case / test 方向；**零 code / 零 CI**  
> **實作另開票**：`WH-P7-NOTIF-DLQ-inspect-cli-impl-v1`

---

## FRAME

### handoff header

**唯讀 DLQ inspect CLI 設計票**：`WH-P7-NOTIF-DLQ-impl-v1` 已在 adapter 最終 webhook 失敗路徑 append `outbox/notification_dlq/events.jsonl`（env-gated · default off · fail-open）。本票定義 operator 可讀的 **list / stats inspect CLI** 介面、旗標、輸出形狀、use case 與 unittest 方向。**本輪僅建票 + 填 FRAME**；不實作 CLI、不更動 DLQ schema、不改 adapter 寫入行為、不設計 replay。

---

### 1. Background

| 層級 | 現況 | 證據 |
|------|------|------|
| DLQ 落盤 | **partial · implemented**（opt-in env） | `WH-P7-NOTIF-DLQ-impl-v1` · `delivery/notification_webhook_adapter_v1.py` |
| 落盤路徑 | append-only **`outbox/notification_dlq/events.jsonl`**（可經 `GOV_NOTIFICATION_WEBHOOK_DLQ_PATH` 覆寫） | impl B_REPORT · §4.6.4.1 |
| Record schema | `schema_id=notification_webhook_dlq_v1`；欄位含 `timestamp` · `dlq_written_at` · `tier` · `endpoint` · `http_status` · embed `webhook_result`；**無** raw payload | §4.6.4.2 · `_build_dlq_record` |
| 合約 inspect 摘要 | §4.6.4.4 已有 list/stats 子命令、旗標、`--json` stdout 形狀草案 | `docs/outbox-and-feedback-layer-contract-v1.md` §4.6.4.4 |
| Operator 工具 | **無**可執行 inspect CLI；只能手動 `tail` / `jq` jsonl | §4.6.4.4 標 **design only** |
| 參考模式 | `tools/inspect_tabular_outbox.py` — `--json` + human table + filter 旗標 | W3-TL-T4 |

**缺口**：DLQ 已落盤，但缺少人類友善、schema-aware 的唯讀檢視工具。operator 無法快速列出最近 N 條失敗、依 tier/endpoint/http_status 過濾，或做簡單聚合統計；§4.6.4.4 為 high-level 草案，尚不足以指導 Implementer 選模組路徑、對齊 impl env 鍵（`DLQ_PATH` vs `DLQ_ROOT`）、或寫 T-5–T-7 unittest。

**impl 與合約對齊備註（本票 FRAME 採納）**

| 項 | 合約 §4.6.4.4 | impl 現況 | 本票設計裁決 |
|----|---------------|-----------|--------------|
| 路徑旗標 | `--dlq-root` → `outbox/notification_dlq` | env `GOV_NOTIFICATION_WEBHOOK_DLQ_PATH` → 直指 jsonl | CLI **must** 支援 `--dlq-path`（預設 `outbox/notification_dlq/events.jsonl`）；**may** 支援 `--dlq-root` 作為目錄捷徑（自動 resolve `events.jsonl`） |
| 欄位名 | `endpoint` · `tier` | 同 impl | inspect 投影與 filter 用 **`endpoint`** / **`tier`**（非 legacy `endpoint_url` / `endpoint_tier`） |
| 時間欄位 | `dlq_written_at` 或 `timestamp` | 兩者皆寫 | 預設 filter 基於 **`dlq_written_at`**；`--since`/`--until` **may** 加 `--time-field timestamp` 切換 |

---

### 2. Goal

定義一個 **唯讀** DLQ inspect CLI，供 operator / CI fixture 驗證使用。不決定最終模組路徑，但 **must** 描述可預期 invocation、子命令、旗標與 stdout 契約。

#### 2.1 Invocation（proposed · Implementer 票定稿）

下列為 **等價候選** invocation；impl 票擇一或提供 wrapper，本票不要求全部實作：

```text
# 候選 A — 獨立腳本（對齊 tabular inspect）
python tools/inspect_notification_dlq_v1.py list --limit 20

# 候選 B — delivery 模組
python -m delivery.inspect_notification_dlq_v1 stats --tier prod --json

# 候選 C — 未來 console entry（僅命名示意）
gov-dlq inspect --since 2026-06-01 --tier prod --endpoint api.customer.com --json
```

**子命令**

| 子命令 | 預設 | 用途 |
|--------|------|------|
| **`list`** | yes（省略子命令時） | 列出最近 N 條 DLQ record（**newest first**） |
| **`stats`** | — | 對符合 filter 的記錄做簡單聚合 |

#### 2.2 CLI 旗標（proposed_default）

| 旗標 | 適用 | 說明 |
|------|------|------|
| `--dlq-path PATH` | list · stats | 預設 `outbox/notification_dlq/events.jsonl`；對齊 `GOV_NOTIFICATION_WEBHOOK_DLQ_PATH` |
| `--dlq-root PATH` | list · stats | **可選**；目錄捷徑，resolve 為 `<root>/events.jsonl` |
| `--json` | list · stats | stdout 輸出結構化 JSON（單次 invocation 一個 JSON 物件）；**非** NDJSON per record |
| `--since ISO8601` | list · stats | 時間下限（inclusive）；預設欄位 `dlq_written_at` |
| `--until ISO8601` | list · stats | 時間上限（inclusive） |
| `--time-field dlq_written_at\|timestamp` | list · stats | 可選；切換時間 filter 欄位 |
| `--tier sandbox\|staging\|prod` | list · stats | 精確 `tier` 過濾 |
| `--endpoint SUBSTR` | list · stats | `endpoint` 子字串匹配（case-sensitive 預設；impl 可選 `--ignore-case`） |
| `--event-id ID` | list · stats | 精確 `event_id` |
| `--code HTTP_STATUS` | list · stats | 過濾 `http_status`（整數；如 `500`）；`null` 連線失敗用 `--code null` 或專旗標 `--no-http-status`（impl 票二選一） |
| `--limit N` | list | 列表上限；預設 **50** |
| `--include-webhook-result` | list | **可選**；detail 模式展開 embed `webhook_result`（預設 list 僅投影 top-level） |

**退出碼（proposed_default）**

| code | 條件 |
|------|------|
| `0` | 成功（含 `count=0` / `total_count=0`） |
| `1` | 用法錯誤 / 無效旗標 |
| `2` | DLQ 檔不存在或不可讀（**非**「空檔」；空 jsonl 仍 exit 0） |

#### 2.3 輸出模式

**Human-readable（預設 · list）**

- 固定欄寬表格，至少列：`dlq_written_at` · `tier` · `event_id` · `endpoint` · `http_status` · `attempt_count` · `last_error`（截斷至合理寬度）
- 無匹配時印 `(no entries)` 類似 tabular inspect

**`--json`（list）**

stdout 單一 JSON 物件：

| 欄位 | 型別 | Required |
|------|------|----------|
| `ok` | bool | yes |
| `count` | int | yes |
| `entries` | array | yes |

`entries[]` 每項 **must** 至少投影（對齊 §4.6.4.2 · **must not** 含 raw payload / secret headers）：

`dlq_written_at` · `timestamp` · `event_id` · `event_type` · `endpoint` · `tier` · `attempt_count` · `retry_exhausted` · `last_error` · `http_status` · `payload_digest`（若有）

**`--json`（stats）**

| 欄位 | 型別 | 說明 |
|------|------|------|
| `ok` | bool | |
| `total_count` | int | 符合 filter 的總筆數 |
| `by_endpoint` | object | `{ "<endpoint>": count }` |
| `by_tier` | object | `{ "sandbox": n, "staging": n, "prod": n }` |
| `by_http_status` | object | key 為 status 字串；`null` 表連線失敗等無 HTTP 狀態 |

#### 2.4 Use cases（operator · 本票 AC 要求）

| # | Use case | 典型命令（pseudo） | 預期結果 |
|---|----------|-------------------|----------|
| **UC-1** | 找出 **最近一週 prod 環境 HTTP 5xx** 失敗 | `gov-dlq inspect list --since 2026-06-15 --tier prod --code 500 --limit 100 --json` | `entries[]` 僅含 `tier=prod` 且 `http_status=500`；按 `dlq_written_at` 降序 |
| **UC-2** | 看 **staging 某 endpoint** 的失敗分佈 | `gov-dlq inspect stats --tier staging --endpoint hooks.staging.example.com --json` | `by_http_status` / `by_endpoint` 反映該 endpoint 各 status 計數 |
| **UC-3** | 依 **event_id** 追查單次 dispatch 失敗 | `python tools/inspect_notification_dlq_v1.py list --event-id evt-20260622-abc --include-webhook-result --json` | 0 或 1 條；含 embed `webhook_result` 供對照 adapter SSOT |
| **UC-4** | **Sandbox 除錯**（讀 fixture 或本機 opt-in DLQ） | `python tools/inspect_notification_dlq_v1.py list --dlq-path tests/fixtures/notification_dlq/events.jsonl --limit 5` | 表格可讀；不依賴 prod env |

#### 2.5 Test 方向（本票定義 · impl 票實作）

Implementer 票 **should** 新增 `tests/test_notification_dlq_inspect_v1.py`（或擴充既有 dispatch 測試檔）+ fixture：

| # | 場景 | 斷言方向 |
|---|------|----------|
| T-5 | inspect list `--json` | fixture jsonl → `ok` · `count` · `entries` 形狀；required 投影欄位齊 |
| T-6 | inspect filter | `--endpoint` / `--code` / `--since` / `--tier` 過濾正確；空結果 `count=0` exit 0 |
| T-7 | inspect stats `--json` | `by_endpoint` · `by_tier` · `by_http_status` 計數正確 |
| T-8 | missing file | 不存在 `--dlq-path` → exit 2 · `ok=false`（若 `--json`） |
| T-9 | privacy | list/stats 輸出 **must not** 含 raw webhook body · HMAC secret · 完整 `Authorization` |

Fixture 建議：`tests/fixtures/notification_dlq/events.jsonl`（2–4 行 synthetic；`tier`/`endpoint`/`http_status` 多樣；無真實 URL / secret）。

#### 2.6 後續 impl 票索引

| 票號 | 範圍 |
|------|------|
| **`WH-P7-NOTIF-DLQ-inspect-cli-impl-v1`** | CLI 模組 + fixture + unittest T-5–T-9；可選 §4.6.4.4 文案微調（若 impl 定稿模組路徑 / 旗標） |
| `WH-P7-NOTIF-contract-doc-sync-v1`（既有建議） | §4.6.0 `webhook_dlq_enabled` · env `DLQ_PATH` vs `DLQ_ROOT` 對齊 |

---

### 3. Non-Goals

- ❌ **不實作** replay / requeue / 自動重送 DLQ 事件（→ 未來 `WH-P7-NOTIF-DLQ-replay-v1` 或同主題票）。
- ❌ **不更動** DLQ jsonl schema 或 `notification_webhook_dlq_v1` 欄位語意。
- ❌ **不改** `notification_webhook_adapter_v1.py` 寫入行為、env gate、fail-open 語意。
- ❌ **不導出** raw webhook payload、HMAC secret、完整 signed body、`Authorization` 或任何 §4.6.4.2 禁止內容；inspect 僅投影已落盤之 redacted / digest 欄位。
- ❌ **不寫入** DLQ 檔案（唯讀）；不 truncate / rotate / retention cron。
- ❌ **不新增** required CI workflow 或 advisory smoke（impl 票可選 local unittest only）。
- ❌ **不合併** Phase 8.8 `orchestration_bridge_outbox` inspect（§2.2 永久分軌）。

---

### 4. Acceptance Criteria（設計層 · 本票 FRAME）

- **AC-1**：FRAME 含 Background / Goal / Non-goals / AC / AllowedPaths / BlockedPaths（本檔）。
- **AC-2**：含 **pseudo-usage** 範例（§2.1 候選 C 或等價一行完整命令）。
- **AC-3**：定義 **≥3** 個主要 use case（§2.4 共 4 個 UC-1–UC-4）。
- **AC-4**：list / stats 子命令、旗標表、list/stats `--json` stdout 形狀均已具體寫入（§2.2–§2.3）。
- **AC-5**：明確指向 **`WH-P7-NOTIF-DLQ-inspect-cli-impl-v1`** 為實作票（§2.6）。
- **AC-6**：test 方向 ≥3 條（§2.5 共 T-5–T-9）。
- **AC-7**：對齊 impl 已落盤 schema（`tier` · `endpoint` · `GOV_NOTIFICATION_WEBHOOK_DLQ_PATH`）與 §4.6.4.4 草案。
- **AC-8**：文檔工單自檢（APP-DOC）：FRAME 正文零本機絕對路徑、零 secret 範例值。

#### Pseudo-usage（AC-2 交付）

```bash
gov-dlq inspect list --since 2026-06-01 --tier prod --endpoint api.customer.com --json
```

等價展開（獨立腳本候選）：

```bash
python tools/inspect_notification_dlq_v1.py list \
  --since 2026-06-01T00:00:00Z \
  --tier prod \
  --endpoint api.customer.com \
  --json
```

---

### 5. AllowedPaths / BlockedPaths

#### AllowedPaths

- `04_Workflows/tickets/WH-P7-NOTIF-DLQ-inspect-cli-v1_state.md`（本票 STATE / FRAME / B/C/D_REPORT）
- `docs/outbox-and-feedback-layer-contract-v1.md`（**僅 §4.6.4.4** 文案微調；若與本 FRAME 定稿旗標 / `--dlq-path` 對齊 — **可選**、由 impl 或 doc-sync 票執行）

#### BlockedPaths

- `delivery/**`（含 `notification_webhook_adapter_v1.py` — 本票 **只讀** 對照）
- `tools/**` · `scripts/**`（inspect CLI 實作留 impl 票）
- `tests/**`（含 `tests/fixtures/**`）
- `.github/workflows/**`
- 暗部 `gov_core_system/**`
- `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `.cursor/rules/**`
- `.env` · secrets · 客戶實際 webhook URL

---

### 6. Dependencies

- `WH-P7-NOTIF-DLQ-v1`（設計 SSOT · §4.6.4 擴寫）
- `WH-P7-NOTIF-DLQ-impl-v1`（落盤 partial · adapter append）
- `docs/outbox-and-feedback-layer-contract-v1.md` §4.6.4.2 · §4.6.4.4
- `delivery/notification_webhook_adapter_v1.py`（只讀 · `_build_dlq_record` / `_append_dlq_record`）
- `tools/inspect_tabular_outbox.py`（只讀 · CLI 模式參考）

---

## STATE

- **overall_status**: `validated`
- **current_owner**: done
- **next_action**: 無 — 本票為 **doc-only 設計票**；CLI 實作已由 `WH-P7-NOTIF-DLQ-inspect-cli-impl-v1` 落盤並 validated
- **last_updated**: 2026-06-22 · scribe (D) — P7 DLQ inspect 設計線 closure
- **wave**: Wave-H+1 · P7 prod line · notification DLQ inspect CLI design
- **status_by_role**:
  - **Orchestrator (A)**: done — 票建立 + FRAME
  - **Implementer (B)**: n/a — 實作在 `WH-P7-NOTIF-DLQ-inspect-cli-impl-v1`
  - **Reviewer (C)**: done — design accepted（見 C_REPORT）
  - **Scribe (D)**: done — Progress append · 2026-06-22 P7 DLQ 收口

---

## B_REPORT

待 Implementer (B) 填寫（impl 票 `WH-P7-NOTIF-DLQ-inspect-cli-impl-v1`）。

---

## C_REPORT

- **reviewer_date**: 2026-06-22
- **verdict**: `accepted`

### 1. 設計 vs 實作分軌

- 本票 **doc-only FRAME**：list/stats 子命令 · 旗標表 · `--json` stdout 形狀 · UC-1–UC-4 · test 方向 T-5–T-9。
- 與 `WH-P7-NOTIF-DLQ-impl-v1` 落盤 schema（`tier` · `endpoint` · `GOV_NOTIFICATION_WEBHOOK_DLQ_PATH`）對齊；§4.6.4.4 草案一致。
- **實作票** `WH-P7-NOTIF-DLQ-inspect-cli-impl-v1` 已交付 `tools/inspect_notification_dlq_v1.py` 並 **validated**。

### 2. 阻塞

無。

---

## D_REPORT

- **scribe_date**: 2026-06-22
- **verdict**: `validated`（設計票 · doc-only）
- **handoff_summary**: P7 prod 線 **DLQ inspect CLI 設計** 已封箱；operator 可執行入口由 impl 票 `tools/inspect_notification_dlq_v1.py` 提供（list / stats · filter · `--json`）。
- **Progress**: `00_Agent_Work_Progress.md` — **2026-06-22 · P7 · DLQ 線收口**（Scribe append）
