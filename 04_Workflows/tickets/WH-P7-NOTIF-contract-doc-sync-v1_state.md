# WH-P7-NOTIF-contract-doc-sync-v1 — Ticket State

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Wave-H+1 · **P7 partial 能力合約 doc sync（doc-only）**  
> 上游：`WH-P7-NOTIF-RETRY-SANDBOX-v1`（done）· `WH-P7-NOTIF-HMAC-impl-v1`（impl_done）· `WH-P7-NOTIF-DLQ-impl-v1`（review_done_pending_scribe）· `WH-P7-NOTIF-PROD-URL-impl-v1`（review_done_pending_scribe）· `WH-P7-NOTIF-contract-partials-validation-v1`（validated）  
> 產物：合約 §4.6.0 / §4.6.4 / §4.6.6 / §4.6.7 與現實實作完全對齊；**零程式、零 CI 變更**

---

## FRAME

### 背景

sandbox 線已 `validated`（`WH-P7-sandbox-line-wrapup-v1`）。v1 doc-sync 已對齊 retry + HMAC sender env 表與 §4.6.7 部分票號；**v2** 需補齊 DLQ 落盤、URL tier/allowlist adapter gate 之 `impl_status` 落差。

### v2 要同步的點

| 區域 | 對齊內容 |
|------|----------|
| **§4.6.0 policy 表** | `webhook_retry_max_attempts` **partial**（sandbox-only · default off · prod Non-goals）；`webhook_hmac` **partial**（sender partial · receiver / prod mandatory not_implemented_yet）；`webhook_dlq_enabled` **not_implemented_yet → partial**；`webhook_url_tier` **implemented → partial**（sandbox implemented · staging/prod adapter gate partial · 尚不建議啟用） |
| **§4.6.4** | `impl_status` **not_implemented_yet → partial**；加 `WH-P7-NOTIF-DLQ-impl-v1` 落盤 reference；env 表 `DLQ_ROOT` → `DLQ_PATH` / `DLQ_TIER` 對齊 impl |
| **§4.6.6** | `GOV_NOTIFICATION_WEBHOOK_TIER` / `URL_ALLOWLIST` **not_implemented_yet → partial**；tier 語意表 staging/prod → partial；impl_status 摘要表更新 |
| **§4.6.7** | P7 票號索引更新至實票（sandbox wrap-up · DLQ 系列 · PROD-URL 系列 · PROD-roadmap · 衍伸票） |

### 非目標

- ❌ 不改任何程式碼或 tests
- ❌ 不修改 CI workflow
- ❌ 不變更 policy default / can_override / owner（僅 `impl_status` 與描述）
- ❌ 不修改其他票檔或 `00_Agent_Work_Progress.md`

### AllowedPaths

- `docs/outbox-and-feedback-layer-contract-v1.md`（限 §4.6 區域）
- `04_Workflows/tickets/WH-P7-NOTIF-contract-doc-sync-v1_state.md`（本票）

### BlockedPaths

- `delivery/**` · `tests/**` · `.github/workflows/**`
- 其他票檔 · `04_Workflows/00_Agent_Work_Progress.md`
- `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `.cursor/rules/**`

### Acceptance Criteria

- **AC-1**：§4.6.0 retry / HMAC / DLQ / URL tier 列 `impl_status` 與 adapter 現況一致（含 sandbox-only · prod Non-goals 描述）。
- **AC-2**：§4.6.4 `impl_status` = **partial** 且含 DLQ-impl / inspect-cli 票 reference。
- **AC-3**：§4.6.6 `TIER` / `URL_ALLOWLIST` env 與 tier 語意表 = **partial**；staging/prod 完整啟用仍 **not_implemented_yet**。
- **AC-4**：§4.6.7 票號索引涵蓋 v2 所列實票與狀態。
- **AC-5**：B_REPORT 記錄變更節與前後差異；明確聲明未改 code / tests / CI。

### Dependencies

- `WH-P7-NOTIF-RETRY-SANDBOX-v1` · `WH-P7-NOTIF-HMAC-impl-v1` · `WH-P7-NOTIF-DLQ-impl-v1` · `WH-P7-NOTIF-PROD-URL-impl-v1`
- `WH-P7-NOTIF-contract-partials-validation-v1` · `WH-P7-sandbox-line-wrapup-v1`
- `docs/outbox-and-feedback-layer-contract-v1.md` §4.6（現行 SSOT）

---

## STATE

- **overall_status**: `done_with_gaps`
- **current_owner**: scribe
- **next_action**: 可選 follow-up：§4.6.4.4 inspect CLI 文案升格 **implemented**（非 blocking）
- **last_updated**: 2026-06-23 · reviewer + scribe (C/D)
- **wave**: Wave-H+1 · P7 contract doc sync v2
- **status_by_role**:
  - **Orchestrator (A)**: pending
  - **Implementer (B)**: n/a — Scribe 兼任 doc sync
  - **Reviewer (C)**: done — 2026-06-23 · **`accepted_with_gaps`**
  - **Scribe (D)**: done — 2026-06-23 · v2 + C 收口
- **notes**:
  - v1 已對齊 retry/HMAC env 表；v2 補 DLQ partial + URL tier/allowlist partial + §4.6.7 全索引
  - 未改 Python / tests / workflows / Progress / 其他票

---

## B_REPORT (Scribe · doc sync v2 landing)

### §1 變更節與前後差異

| 節 | 行號區（約） | 前 | 後 |
|----|-------------|----|----|
| **§4.6 開頭 Runtime** | L312 | DLQ / non-localhost URL `not_implemented_yet` | DLQ **partial** · URL tier/allowlist **partial** · receiver/prod mandatory 未實作 |
| **§4.6.0** `webhook_url_tier` | L322 | **implemented**（sandbox）；prod **not_implemented_yet** | **partial**（sandbox implemented · staging/prod gate partial · prod Non-goals） |
| **§4.6.0** `webhook_hmac` | L323 | partial（微調描述） | 補 receiver verification / reference impl **not_implemented_yet** |
| **§4.6.0** `webhook_retry_max_attempts` | L324 | partial（寫無 DLQ） | partial + **sandbox-only** · prod Non-goals · 可搭配 opt-in DLQ |
| **§4.6.0** `webhook_dlq_enabled` | L325 | **not_implemented_yet** | **partial**（env gated · default off · inspect CLI not_implemented_yet） |
| **§4.6.3** | L340 | 無 DLQ | opt-in DLQ cross-ref · staging/prod retry mandatory not_implemented_yet |
| **§4.6.4** 開頭 | L342–346 | impl **not_implemented_yet** | impl **partial** + `WH-P7-NOTIF-DLQ-impl-v1` 落盤句 + inspect-cli 票 |
| **§4.6.4** env 表 | L359–364 | `DLQ_ROOT` · future | `DLQ_PATH` · `DLQ_TIER` · **partial**（對齊 impl） |
| **§4.6.4** 觸發表 | L354 | sandbox 現況不寫 | sandbox 預設不寫（`DLQ_ENABLED=0`）；opt-in 落盤 |
| **§4.6.6** impl_status 摘要 | L613–620 | TIER/ALLOWLIST **not_implemented_yet** | **partial** · staging/prod 完整啟用 **not_implemented_yet** |
| **§4.6.6.1** tier 表 | L628–634 | staging/prod **not_implemented_yet** | **partial**（adapter gate · unittest only · 尚不建議啟用） |
| **§4.6.6.2** | L638 | ALLOWLIST **not_implemented_yet** | **partial** |
| **§4.6.6.4** checklist | L702–707 | DLQ 設計 only | DLQ-impl **partial** + inspect-cli 票；PROD-URL-impl **partial** |
| **§4.6.6** env 表 | L731–735 | TIER/ALLOWLIST not_implemented；無 DLQ 列 | 新增 DLQ 三鍵 **partial**；TIER/ALLOWLIST → **partial** |
| **§4.6.7** | L738–758 | 7 張已交付 + 4 張衍伸（含 stale DLQ/PROD-URL 為 future） | 14 張已交付實票 + 7 張衍伸（含 DLQ-inspect-cli-impl · HMAC-prod-mandatory · RETRY-prod · staging-integration） |

### §2 未改動範圍

- **無** Python / tests / CI workflow 變更
- **無** 其他票檔或 Progress 變更

### §3 驗證

- 只讀對照：`WH-P7-NOTIF-DLQ-impl-v1` B_REPORT/C_REPORT · `WH-P7-NOTIF-PROD-URL-impl-v1` B_REPORT/C_REPORT · `delivery/notification_webhook_adapter_v1.py` env 鍵名
- 無 runtime 命令（doc-only 票）

### §4 阻塞

無。

---

## C_REPORT

- **review_date**: 2026-06-23
- **reviewer_role**: P7 contract doc-sync Reviewer (C)
- **verdict**: **`accepted_with_gaps`**
- **scope**: §4.6.0 / §4.6.4 / §4.6.6 / §4.6.7 vs DLQ-impl · PROD-URL-impl · inspect-cli STATE（只讀 spot-check）
- **conclusion**: v2 B_REPORT 前後差異表與 adapter env 鍵名一致；`impl_status` partial 敘述與 sandbox-only / prod Non-goals 無矛盾。
- **gaps（non-blocking）**: §4.6.4.4 inspect CLI 文案仍標 design-only（實作已 validated）；staging/prod runtime enable 仍 deferred。

---

## D_REPORT

### DLQ 段（Scribe · P7 DLQ 線收口 · 2026-06-22）

- **scope**：僅 DLQ 相關合約對齊；本票整體仍 `implementer_done_pending_review`（retry / HMAC / URL tier 段待 Reviewer 全票 spot-check）。
- **§4.6.4 impl_status**：已標 **partial** — `WH-P7-NOTIF-DLQ-impl-v1` 落盤 `outbox/notification_dlq/events.jsonl`（env gated · default off · fail-open）。
- **env 表鍵名 / 狀態**：§4.6.4 · §4.6.6 env 表已與 DLQ-impl / inspect-cli 對齊 — `GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED` · `GOV_NOTIFICATION_WEBHOOK_DLQ_PATH`（非 legacy `DLQ_ROOT`）· `GOV_NOTIFICATION_WEBHOOK_DLQ_TIER`；三鍵均 **partial**。
- **§4.6.0 `webhook_dlq_enabled`**：**partial**（opt-in · default off）；inspect CLI 實作已就緒（`tools/inspect_notification_dlq_v1.py`），§4.6.4.4 文案仍標 design-only — 全票 Reviewer 通過後可升格 **implemented** 敘述。
- **§4.6.7 索引**：DLQ 系列票（design · impl · inspect-cli · inspect-cli-impl）狀態見各票 STATE；本 DLQ 收口由 Scribe Progress **2026-06-22 · P7 · DLQ 線收口** 匯總。
- **未改**：Python / tests / workflows；本段不宣稱整票 `validated`。
