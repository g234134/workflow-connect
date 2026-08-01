# WH-P7-NOTIF-DLQ-inspect-cli-impl-v1 — Ticket State

> Phase：Wave-H+1 · **P7 prod 線** · notification DLQ inspect CLI 實作  
> 上游：`WH-P7-NOTIF-DLQ-inspect-cli-v1`（FRAME）· `WH-P7-NOTIF-DLQ-impl-v1`（落盤）  
> 範圍：唯讀 list/stats CLI + fixture + unittest；**不改** adapter / dispatch / 合約 docs

---

## STATE

- **overall_status**: `validated`
- **current_owner**: done
- **next_action**: 無 — inspect CLI partial 已 validated；§4.6.4.4 doc 狀態更新可併入 `WH-P7-NOTIF-contract-doc-sync-v1` 或 follow-up runbook 票
- **last_updated**: 2026-06-22 · scribe (D) — P7 DLQ 線 closure
- **wave**: Wave-H+1 · P7 prod line · notification DLQ inspect CLI impl
- **status_by_role**:
  - **Orchestrator (A)**: done — 票 scope 對齊 inspect-cli FRAME
  - **Implementer (B)**: done — CLI + fixture + unittest
  - **Reviewer (C)**: done — accepted_with_nits（見 C_REPORT）
  - **Scribe (D)**: done — Progress append · 2026-06-22 P7 DLQ 收口

---

## B_REPORT

- **implementer_date**: 2026-06-22
- **scope**: 唯讀 DLQ inspect CLI + fixture + unittest；無 adapter / CI / docs 變更

### 1. Changed files

| 檔案 | 變更摘要 |
|------|----------|
| `tools/inspect_notification_dlq_v1.py` | 新增 list / stats 子命令、filter 旗標、human table + `--json` 輸出 |
| `tests/fixtures/notification_dlq/events.jsonl` | 4 行 synthetic DLQ fixture（sandbox / staging / prod · 多 http_status） |
| `tests/test_notification_dlq_inspect_cli_v1.py` | UC-1–UC-4 + invalid-line skip + default list 子命令 |
| `04_Workflows/tickets/WH-P7-NOTIF-DLQ-inspect-cli-impl-v1_state.md` | 本票 STATE / B_REPORT |

### 2. CLI 子命令與旗標

- **子命令**：`list`（預設）· `stats`
- **旗標**：`--dlq-path` · `--dlq-root` · `--since` · `--until` · `--time-field` · `--tier` · `--endpoint` · `--event-id` · `--code` · `--limit` · `--include-webhook-result` · `--json`

### 3. Use case 覆蓋

| UC | 測試 | 斷言摘要 |
|----|------|----------|
| **UC-1** | `test_uc1_list_json_basic` | fixture → `ok=true` · `count=4` · entries 含 required 投影欄位；subprocess `--json` 一致 |
| **UC-2** | `test_uc2_filter_by_tier_endpoint_code` | `--tier prod` · `--endpoint` · `--code 500` 過濾正確 |
| **UC-3** | `test_uc3_stats_json` | `stats --json` → `by_http_status` · `by_endpoint` · `by_tier` · `total_count` |
| **UC-4** | `test_uc4_missing_or_empty_file` | 不存在 / 空檔 → `ok=true` · `count=0` / `total_count=0` · exit 0 |

額外：`test_skips_invalid_json_line`（單列 parse 失敗 skip 不崩潰）· `test_default_subcommand_is_list`（省略子命令預設 list）

### 4. 驗證

```bash
python -m unittest tests.test_notification_dlq_inspect_cli_v1 -v
```

### 5. skeleton / placeholder

無。

### 6. 阻塞

無。

### 7. override

- 任務 UC-4 採 `ok=true` + `count=0`（不存在 / 空檔 exit 0）；FRAME T-8「missing file exit 2」未採用，以 Implementer 任務卡為準。

---

## C_REPORT

- **reviewer_date**: 2026-06-22
- **verdict**: `accepted_with_nits`

### 1. §4.6.4.4 / FRAME 對齊

| 項 | 預期 | 實作 | 結果 |
|----|------|------|------|
| 子命令 | `list`（default）· `stats` | `main()` 預設 `list`；省略子命令可跑 | ✅ |
| 旗標 | `--dlq-path` · `--dlq-root` · `--since` · `--until` · `--time-field` · `--tier` · `--endpoint` · `--event-id` · `--code` · `--limit` · `--include-webhook-result` · `--json` | 全數支援 | ✅ |
| list `--json` | `{ok, count, entries}`；entries 投影 schema 安全欄位 | `LIST_ENTRY_FIELDS` 投影；`webhook_result` 僅 `--include-webhook-result` | ✅ |
| stats `--json` | `total_count` · `by_endpoint` · `by_tier` · `by_http_status` | `inspect_stats()` 一致 | ✅ |
| 排序 | newest first（`dlq_written_at`） | `_load_filtered_records` reverse sort | ✅ |
| 容錯 | 不存在/空檔 `ok=true` · count 0 · exit 0 | `_iter_dlq_records` 非檔案即空 iterable；`main` 恆 return 0 | ✅（見 N-1） |
| invalid JSON | stderr warning + skip | line-level `JSONDecodeError` → stderr warning | ✅ |
| 隱私 | 不外流 raw payload / secret | 預設不投影 `webhook_result`；`_assert_no_sensitive_leak` on `--json` | ✅（缺專測見 N-4） |

**一句話**：CLI 完整覆蓋 §4.6.4.4 / inspect-cli FRAME 的 list/stats use cases（UC-1–UC-4 語意），旗標與 stdout 形狀對齊；模組路徑採 FRAME 候選 A `tools/inspect_notification_dlq_v1.py`。

### 2. 測試

```bash
python -m unittest tests.test_notification_dlq_inspect_cli_v1 -v
```

**結果**：**6/6 OK** — UC-1 list/json · UC-2 filter · UC-3 stats · UC-4 missing/empty · invalid-line skip · default subcommand。

### 3. Nits（不阻擋驗收）

| # | 項目 | 說明 |
|---|------|------|
| N-1 | missing file exit code | FRAME T-8 草案 exit 2；本票任務卡 + B_REPORT override 採 exit 0 · `ok=true` · `count=0` — ** intentional ** |
| N-2 | human table 欄位 | FRAME §2.3 列 `attempt_count`；表格未含該欄（僅 `--json` 有）— 可接受小差異 |
| N-3 | UC-3 event-id 專測 | FRAME UC-3 為 `--event-id` + `--include-webhook-result`；測試檔 UC-3 實為 stats — 功能已實作、缺專測 |
| N-4 | T-9 privacy unittest | `_assert_no_sensitive_leak` 存在但無獨立 assert case |
| N-5 | §4.6.4.4 doc 狀態 | 合約仍標 **design only** — 待 doc-sync 票更新 impl 狀態 |

### 4. 阻塞

無。

---

## D_REPORT

- **scribe_date**: 2026-06-22
- **handoff_summary**: P7 prod 線 **DLQ inspect CLI** 就緒：`tools/inspect_notification_dlq_v1.py` 提供 operator / CI 可重跑的唯讀 **list / stats** 入口，對齊 `outbox/notification_dlq/events.jsonl`（或 `--dlq-path` / fixture）；filter by tier · endpoint · http_status · time · event_id；`--json` 輸出結構化 dict，預設 human table；不含 replay / 寫入。

### prod 線 / ops 用途

- **標準化 debug DLQ**：取代手動 `tail` / `jq`，快速列出最近 N 條 webhook 失敗、依 prod/staging tier 或 endpoint 過濾 5xx。
- **離線稽核 / sandbox 除錯**：可指向本機 opt-in DLQ 或 `tests/fixtures/notification_dlq/events.jsonl`，無需 prod env。
- **stats 聚合**：`by_http_status` / `by_endpoint` / `by_tier` 支援 incident triage 與 per-endpoint 失敗分佈。

### 建議下一張票（至少）

| 票號 | 理由 |
|------|------|
| **`WH-P7-NOTIF-DLQ-inspect-cli-docs-v1`** | 簡短 runbook / operator 手冊；§4.6.4.4 標 **implemented**；常用命令範例 |
| `WH-P7-NOTIF-DLQ-replay-design-v1` | replay / requeue 僅設計；本 CLI 明確 non-goal |
| `WH-P7-NOTIF-contract-doc-sync-v1` | §4.6.0 `webhook_dlq_enabled` · env `DLQ_PATH` vs `DLQ_ROOT` 對齊（延續 DLQ-impl-v1） |

### Scribe closure

- **verdict**: `validated`（Reviewer `accepted_with_nits` · Scribe 收口）
- **驗證**：`python -m unittest tests.test_notification_dlq_inspect_cli_v1 -v` → **6/6 OK**
- **Progress**: `00_Agent_Work_Progress.md` — **2026-06-22 · P7 · DLQ 線收口**（Scribe append）
