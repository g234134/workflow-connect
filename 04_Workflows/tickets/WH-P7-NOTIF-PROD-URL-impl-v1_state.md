# WH-P7-NOTIF-PROD-URL-impl-v1 — Ticket State

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Wave-H+1 · **prod URL / tier / allowlist adapter 實作票**  
> 上游：`WH-P7-NOTIF-PROD-URL-v1`（§4.6.6.1–4 設計 · `implementer_done_pending_review`）· `WH-P7-sandbox-line-wrapup-v1`（sandbox 線 validated）  
> 產物：adapter 讀取 `TIER` / `URL_ALLOWLIST`；staging/prod minimal gate；sandbox 行為不變；unittest

---

## FRAME

### handoff header

本票在 `notification_webhook_adapter_v1` 實作 §4.6.6 tier / URL allowlist **minimal gate**；sandbox localhost-only 不變；staging/prod 僅 unit test 驗證，**未**在真環境啟用。

### 依賴

- `WH-P7-NOTIF-PROD-URL-v1` — §4.6.6.1–§4.6.6.4 normative SSOT
- `docs/outbox-and-feedback-layer-contract-v1.md` §4.4 · §4.6.6

### Non-Goals（本票）

- ❌ 不啟用真實 staging/prod endpoint
- ❌ 不實作 per-customer registry match（prod 完整 gate → 後續票）
- ❌ 不實作 staging/prod mandatory HMAC / retry / DLQ reject
- ❌ 不改 CI workflow · 不改合約 doc · 不改 dispatch/gateway

---

## STATE

- **overall_status**: `validated`
- **current_owner**: done
- **next_action**: 無 — adapter `TIER` / `URL_ALLOWLIST` minimal gate **partial** 已 validated；staging/prod 真環境啟用見 §4.6.6.4 checklist · 後續票見 D_REPORT §2
- **notes**:
  - sandbox 對照：`WH-P7-sandbox-line-wrapup-v1` · localhost-only · opt-in partial
  - staging 演練：`WH-P7-PROD-staging-smoke-runbook-v1` S1 URL gate · 非 CI prod URL
  - prod registry · required CI 仍 future
- **last_updated**: 2026-06-23 · progress agent (sandbox/staging cross-ref)
- **status_by_role**:
  - **Orchestrator (A)**: done — 開票 / 派工
  - **Implementer (B)**: done — adapter + unittest + B_REPORT
  - **Reviewer (C)**: done — §4.6.6 minimal gate 對照 · 27/27 OK · `accepted_with_gaps`
  - **Scribe (D)**: done — Progress append · §4.6.6 doc-sync · 2026-06-23

---

## B_REPORT

> Implementer (B) · 2026-06-22 · adapter + unittest

### §1 變更檔案

| 檔案 | 變更 |
|------|------|
| `delivery/notification_webhook_adapter_v1.py` | 讀取 `GOV_NOTIFICATION_WEBHOOK_TIER` / `URL_ALLOWLIST`；tier 分支 gate；`blocked_reason` / `blocked_rule` |
| `tests/test_notification_webhook_dispatch_v1.py` | 新增 `TestNotificationWebhookTierUrlPolicy`（4 scenario） |
| `04_Workflows/tickets/WH-P7-NOTIF-PROD-URL-impl-v1_state.md` | 本票 STATE / B_REPORT |

### §2 新增 env 與行為

| Env | Default | 行為 |
|-----|---------|------|
| `GOV_NOTIFICATION_WEBHOOK_TIER` | `sandbox`（未設等同 sandbox） | `sandbox` → §4.4 localhost-only（**ignore** URL_ALLOWLIST）；`staging`/`prod` → https + allowlist gate |
| `GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST` | *(unset)* | staging/prod：**must** 設且可解析；否則 `url_allowlist_missing` 拒 POST |

**Gate 阻擋時**（fail-closed at URL gate · dispatch 外層 **fail-open** `ok=True`）：

- `webhook_result.blocked_reason` = `blocked_by_url_tier_policy`
- `webhook_result.blocked_rule` ∈ {`sandbox_localhost_only`, `https_required`, `bare_ip_forbidden`, `url_allowlist_missing`, `url_allowlist_mismatch`, `invalid_url`}
- log 含 tier + rule

**未實作（留後續票）**：prod registry ∩ allowlist、staging/prod mandatory HMAC/retry/DLQ reject。

### §3 測試 scenario

| # | Scenario | 斷言 |
|---|----------|------|
| 1 | sandbox + URL_ALLOWLIST 設為 staging host | localhost POST 仍成功（allowlist 不阻擋） |
| 2 | TIER=staging + allowlist match | mock POST 被呼叫、`dispatched=True` |
| 3 | TIER=staging + allowlist miss | 不 POST、`blocked_rule=url_allowlist_mismatch` |
| 4 | TIER=prod + allowlist 未設 | 不 POST、`blocked_rule=url_allowlist_missing` + warning log |

### §4 與 §4.6.6 policy matrix 對齊

| tier | impl 狀態（本票後） |
|------|---------------------|
| `sandbox` | **implemented** — localhost-only；與 §4.4 一致 |
| `staging` | **partial** — URL/https/allowlist gate 僅 unit test；HMAC/retry/DLQ mandatory **未** enforce |
| `prod` | **partial** — 同上 + registry **未** implement |

staging/prod **未**在真環境 / CI 啟用（CI 仍 sandbox localhost · §4.5）。

### §5 驗證

```bash
python -m unittest tests.test_notification_webhook_dispatch_v1 -v
```

**結果**：27 tests · **OK**（2026-06-22 implementer run）

### §6 skeleton / placeholder

無。

### §7 阻塞

無。

### §8 fail-open 裁決

§4.6.6：URL gate **fail-closed**（拒 POST）；外層 dispatch **fail-open**（`ok=True`）。本票 blocked 路徑回傳 `ok=True`、`dispatched=False`、`dry_run=True`，與 sandbox unsafe URL 既有語意一致。

---

## C_REPORT

> Reviewer (C) · 2026-06-22 · 對照 §4.6.6.1–4 · sandbox wrap-up · B_REPORT §2–§8

### verdict

**`accepted_with_gaps`**

TIER / URL_ALLOWLIST minimal gate 與 §4.6.6 matrix 在**本票範圍內**一致；staging/prod 完整 policy mandatory（HMAC / retry / DLQ reject · prod registry）依 Non-Goals 留後續票，不構成本票 blocking。

### §1 實作 vs 合約對照

| 檢查項 | 結果 | 證據 |
|--------|------|------|
| `GOV_NOTIFICATION_WEBHOOK_TIER` default `sandbox` | ✅ | `_get_webhook_tier()`：未設或 invalid → `sandbox` |
| `URL_ALLOWLIST` grammar（host / host:port / host/path-prefix） | ✅ | `_parse_allowlist_entry()` · `*.` 子域 · path `/*` glob |
| sandbox：localhost-only · **ignore** allowlist | ✅ | `_check_url_tier_policy()` tier==sandbox 分支不讀 allowlist |
| staging/prod：https + allowlist match · bare IP forbidden | ✅ | `https_required` · `bare_ip_forbidden` · `url_allowlist_*` rules |
| gate 時不 POST · `blocked_reason` / `blocked_rule` | ✅ | 回傳前阻斷 `_send_http_post_with_retry` |
| 外層 dispatch **fail-open** `ok=True` | ✅ | blocked 路徑 `ok=True` · `dispatched=False` · `dry_run=True`（對齊 §4.4 / §4.6.6 硬規則） |
| sandbox 線 regression | ✅ | `test_sandbox_tier_ignores_url_allowlist_regression` + 全 suite **27/27 OK** |

**fail-open vs fail-close 裁決（重申）**：URL gate **fail-closed**（拒 POST、設 `blocked_*`）；orchestrator / dispatch 外層 **fail-open**（`ok=True`）。與 §4.6.6 normative 句及 sandbox unsafe URL 既有語意一致。

### §2 測試 scenario 覆蓋

| # | Scenario | 測試方法 | 覆蓋 |
|---|----------|----------|------|
| 1 | sandbox + allowlist 設 staging host · localhost 仍 POST | `test_sandbox_tier_ignores_url_allowlist_regression` | ✅ |
| 2 | staging + allowlist OK → 發送 | `test_staging_tier_allowlist_match_allows_post` | ✅ |
| 3 | staging + allowlist miss → `url_allowlist_mismatch` | `test_staging_tier_allowlist_miss_blocks_post` | ✅ |
| 4 | prod + allowlist 未設 → `url_allowlist_missing` | `test_prod_tier_missing_allowlist_blocks_post` | ✅ |

**驗證命令**：`python -m unittest tests.test_notification_webhook_dispatch_v1 -v` → **27 tests OK**（Reviewer 2026-06-22 複跑）。

### §3 已知 gap（非本票 blocking）

- prod **per-customer registry** ∩ allowlist — 未實作（FRAME Non-Goals）
- staging/prod **HMAC / retry / DLQ mandatory reject** — 未 enforce（→ 衍伸票）
- **prod tier 不建議在真環境啟用**；僅 unit test 驗證 gate 邏輯；CI 仍 sandbox localhost（§4.5）

### §4 阻塞

無 blocking。

---

## D_REPORT

> Scribe (D) · 2026-06-23 · 依 Reviewer C `accepted_with_gaps` 收口

### §1 本票收口摘要

`WH-P7-NOTIF-PROD-URL-impl-v1` 交付 adapter 讀取 `TIER` / `URL_ALLOWLIST` 之 **minimal URL gate**；sandbox §4.4 行為不變；staging/prod gate 僅 unittest 覆蓋。**prod tier 目前仍不建議啟用**，只用於單元測試與後續升格鏈前置。Reviewer verdict：**`accepted_with_gaps`** · `python -m unittest tests.test_notification_webhook_dispatch_v1 -v` → **27/27 OK**。

### §2 建議後續票

| 票號 | 優先 | 範圍摘要 |
|------|------|----------|
| **`WH-P7-NOTIF-staging-integration-v1`** | P1 | 真 staging env 人工整合測試 allowlist + https gate（非 CI prod URL） |
| **`WH-P7-NOTIF-HMAC-prod-mandatory-v1`** | P1 | staging/prod 缺 HMAC 拒 POST（fail-closed · 與 sandbox fail-open 分支） |
| `WH-P7-NOTIF-RETRY-prod-v1` | P2 | retry 從 sandbox partial 升格至 staging/prod tier gate |
| `WH-P7-NOTIF-DLQ-v1` | P2 | §4.6.4 DLQ 落盤 · staging/prod retry 失敗可觀測 |
| prod registry gate（待 Orchestrator 定 id） | P2 | allowlist ∩ per-customer registry match |

**升格順序（對齊 §4.6.6.4）**：DLQ → retry prod → HMAC prod mandatory → receiver fixtures → **staging-integration** → prod 批文後 rollout。

### §3 Scribe 完成項

- STATE → **`validated`** · `current_owner` → **`done`**
- 合約 §4.6.6.3 / §4.4 極小 doc-sync（runtime 現況 · CI cross-ref；**未改** `impl_status`）
- Progress append（2026-06-23 · P7 PROD-URL-impl 收口）
- **未宣稱** prod tier production-ready
