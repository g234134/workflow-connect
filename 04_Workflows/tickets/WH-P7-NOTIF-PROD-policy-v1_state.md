# WH-P7-NOTIF-PROD-policy-v1 — Ticket State

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Wave-H · **純設計票**（policy & contract only）  
> 上游：WD-P7-T1 / T2 / T3（sandbox 實作已收口）  
> 產物：合約 §4.6 Notification governance (prod tier)；**零程式、零 CI 變更**

---

## FRAME

### 背景（Background）

P7 Wave-D/E/G 已交付 **sandbox 級**通知鏈路：

| 層級 | 現況 | 證據 |
|------|------|------|
| Orchestrator emit | `intake.gate_decision` / `delivery.bundle_ready`；fail-open | WD-P7-T1 · `tests.test_orchestrator_notifications` **7/7** |
| Dispatch registry | local handler + `webhook_dispatch_v1` 雙 sink | WD-P7-T2 · `tests.test_notification_webhook_dispatch_v1` **12/12** |
| 全鏈 smoke | orchestrator → gateway → dispatch → localhost mock POST | WD-P7-T3 · **5/5** |
| Advisory CI | `p7-notification-smoke`；`continue-on-error`；僅 `127.0.0.1` | 合約 §4.5 |

**缺口**：prod 級 **retry / DLQ / HMAC / prod URL policy** 僅在 §4.4 以「future phases」一句帶過；無統一 policy 表、無威脅模型、無 delivery semantics 裁決、無環境分級（sandbox vs staging vs prod）的書面規則。本票填補該制度真空，**不啟用 prod 通知、不改現有 sandbox 行為**。

### Goal

產出一份可審計的 **prod-tier 通知治理合約**（擴充 `docs/outbox-and-feedback-layer-contract-v1.md` → **§4.6 Notification governance (prod tier)**），內容僅含：

- policy 表（欄位：`policy_item` / `default` / `can_override` / `owner` / `impl_status`）
- env / config 鍵命名草案（**不**寫入 repo secrets、不給具體 URL 範例值）
- 與現有 §4.2–§4.5 行為的對照矩陣（何者已實作、何者 `not_implemented_yet`）

### Scope

1. **§4.6.3 Retry & backoff policy** — 定義 webhook 層重試語意（次數、間隔、最大延遲、可重試 HTTP 狀態碼、與 gateway emit fail-open 的邊界）。
2. **§4.6.4 DLQ / audit log** — 定義失敗事件落盤路徑命名、`schema_id`、保留期、與 `notification_events.jsonl` / `outbox/feedback/acks/` 的關係；**明確區分** Phase 8.8 `orchestration_bridge_outbox`（§2.2 永久分軌）。
3. **§4.6.5 Webhook HMAC & idempotency** — 算法（建議 HMAC-SHA256）、header 名、timestamp / nonce 重放防護、`event_id` 冪等契約、receiver 驗簽失敗語意。
4. **§4.6.6 URL policy & environment gates** — sandbox / staging / prod 三級 URL allowlist 規則；禁止在未授權 tier 直接指向外部客戶 endpoint；與現有 `localhost/127.0.0.1` sandbox 護欄的升格路徑。
5. **Policy 總表（§4.6.0）** — 彙總 policy 欄位；本輪先落盤表頭 + 代表性 subset，完整列待 Reviewer 收口擴充。
6. **Env / config 鍵草案表** — 僅命名與語意，無 code（含既有 `GOV_NOTIFICATION_WEBHOOK_*` 與 proposed prod-tier 鍵）。
7. **衍伸實作票索引**（本票僅列出，不實作）。

### Non-Goals

- ❌ **不開啟 prod 通知** — 不設定 prod URL、不啟用非 localhost 實際 POST、不要求尚書省 prod 批文執行。
- ❌ **不改現有 sandbox 行為** — §4.4 env gate、localhost 護欄、fail-open、dry-run 語意維持不變。
- ❌ **不修改任何 Python / YAML 實作** — 含 `delivery/notification_*`、`routing/notification_handlers_v1.yaml`。
- ❌ **不修改 unittest / CI workflow** — 含 `tests/test_orchestrator_*`、`tests/test_notification_webhook_*`、`.github/workflows/p7-notification-smoke.yml`。
- ❌ **不合併 Phase 8.8 bridge outbox** — 遵守 §2.2 永久分軌。
- ❌ **不寫 Slack/Email/多通道** — 僅 webhook prod governance。
- ❌ **不升格 advisory CI 為 required check**。

### AllowedPaths

- `docs/outbox-and-feedback-layer-contract-v1.md`（新增 §4.6；§4.4 末改為交叉引用 §4.6）
- `docs/notification-governance-prod-tier-v1.md`（可選獨立附錄；本輪採方案 A 併入 §4.6）
- `04_Workflows/tickets/WH-P7-NOTIF-PROD-policy-v1_state.md`（本票 STATE / B_REPORT 文書）

### BlockedPaths

- `delivery/**` · `routing/**` · `scripts/**` · `tests/**`
- `.github/workflows/**`
- 暗部 `gov_core_system/core/**`
- `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `.cursor/rules/**`（除非尚書省另批 governance 票）
- `.env` · secrets · 客戶實際 webhook URL
- `WD-P7-T1` / `T2` / `T3` 的 FRAME / C_REPORT / D_REPORT

### Acceptance Criteria

- **AC-1**：合約新增 **§4.6**，含完整目錄（§4.6.0–§4.6.7）與 **policy 總表**（本輪 subset；完整 12+ 列待 Reviewer 擴充）。
- **AC-2**：每一 policy 列明 `impl_status` ∈ {`implemented`, `partial`, `not_implemented_yet`}，且與現碼一致（例：retry=0、HMAC=off、URL=localhost-only、DLQ=無）。
- **AC-3**：**不矛盾**現有 fail-open 雙層語意（gateway emit + dispatch/webhook）；若 prod tier 建議「at-least-once + DLQ」，須明文標示為 **future opt-in**，預設不改 sandbox。
- **AC-4**：HMAC 小節含：算法、header 名、payload canonicalization 原則、timestamp skew 窗口、重放拒絕規則（可為建議值，標 `proposed_default`）。
- **AC-5**：URL policy 小節含：三級 tier 定義、禁止「sandbox CI / 開發機直接 POST 至客戶 production endpoint」的硬規則、staging 例外流程（雙人批准 / allowlist 檔案位置類型，不寫實例路徑）。
- **AC-6**：至少列出 **2 張未來實作票**（見下），附建議 AC 一句話，**不含在本票 scope**。
- **AC-7**：B_REPORT 含「與 WD-P7-T2 NonScope 對照」— 確認本設計為 T2 明確 deferred 項的制度化承接。
- **AC-8**：文檔工單自檢（APP-DOC）：零本機絕對路徑、零 secret 範例值、禁區僅類型描述。

### 建議衍伸實作票（本票外）

| 票號（建議） | 範圍摘要 | 依賴 |
|--------------|----------|------|
| `WH-P7-NOTIF-RETRY-v1` | 在 `notification_webhook_adapter_v1` 實作可配置 retry + backoff；失敗寫入 DLQ 路徑；unittest 覆蓋 5xx/timeout | 本票 AC-4 policy 定稿 |
| `WH-P7-NOTIF-HMAC-v1` | HMAC 簽名發送 + header；receiver 驗簽 contract test；secret 僅 env | 本票 AC-4 + Security review |
| `WH-P7-NOTIF-DLQ-v1`（可併入 RETRY） | DLQ jsonl + inspect CLI skeleton；與 `notification_events.jsonl` 關聯 | 本票 AC-5 DLQ 小節 |
| `WH-P7-NOTIF-PROD-URL-v1` | `GOV_NOTIFICATION_WEBHOOK_TIER` + non-localhost allowlist；staging 整合測試 | 尚書省 prod/staging 批文 |

### Dependencies

- WD-P7-T1 / T2 / T3（sandbox 基線 SSOT）
- `docs/outbox-and-feedback-layer-contract-v1.md` §4.2–§4.5
- P8.9-T2/T3 downstream ack / dispatch registry 語意

---

## STATE

- **overall_status**: `design_accepted`
- **current_owner**: orchestrator
- **next_action**: 在現有 **local slot S1–S4 GO** 證據（run_id `20260623T165252Z` · execute **`validated`** · wrapup 票）基礎上，規劃真 Infra / 客戶 staging endpoint、**`WH-P7-PROD-prod-rollout-governance-bootstrap-v1`** Wave-P7-6 rollout bootstrap、governance / CI gate 設計；policy subset `impl_status` 與真 env 敘述留 doc-sync 另票
- **last_updated**: 2026-06-24 · P7 DOCSYNC agent (phase-refresh)
- **wave**: Wave-H · notification governance design
- **status_by_role**:
  - **Orchestrator (A)**: pending — 待 Reviewer sign-off 後裁決
  - **Implementer (B)**: n/a — 本票純設計，無程式交付
  - **Reviewer (C)**: done — 2026-06-22
  - **Scribe (D)**: done — 2026-06-22（開票 + §4.6 骨架落盤）
- **notes**:
  - **policy-only**：本票 scope 止於 §4.6 骨架；runtime 由衍伸 impl 票承接（DLQ/URL/RETRY/HMAC impl 均已 **validated** · unittest only）
  - **Wave-P7-5 local slot**：首輪 S1–S4 GO（run_id `20260623T165252Z` · execute **`validated`** · bootstrap / receiver-impl **`done_with_gaps`**）— **不等同** prod-ready · **仍缺**真 Infra / 客戶 staging endpoint · 真 governance_dual · 48h 觀測
  - **Execution 入口**：`WH-P7-PROD-prod-rollout-governance-bootstrap-v1` 將收口 Wave-P7-6 FRAME（FRAME pending）
  - **仍缺 Wave-P7-6**：prod rollout / registry gate / required CI / Security sign-off · **不宣稱 prod flip 已執行**
  - **為何不標 `validated`**：§4.6.0 仍 subset · 真 env / required CI 未啟用

---

## B_REPORT (Scribe · design doc landing)

### §1 變更檔案清單

| 檔案路徑 | 變更類型 | 說明 |
|----------|----------|------|
| `04_Workflows/tickets/WH-P7-NOTIF-PROD-policy-v1_state.md` | 新增 | 本票 FRAME / STATE / B_REPORT |
| `docs/outbox-and-feedback-layer-contract-v1.md` | 修改 | 新增 §4.6.0–§4.6.7 骨架；§4.4 末「future phases」改為交叉引用 §4.6 |

### §2 與 WD-P7-T2 NonScope 對照

| WD-P7-T2 NonScope | 本票承接方式 |
|-------------------|--------------|
| 不實作 retry / DLQ / HMAC 簽名 | §4.6.3–§4.6.5 標 `not_implemented_yet`；僅 policy 草案 |
| 不寫入 prod URL / secret | §4.6.6 tier gate + 禁止未授權客戶 endpoint；零 secret 範例 |
| 不改 sandbox 行為 | Non-Goals 明列；§4.4 行為不變，僅加 cross-ref |

### §3 驗證

- 無 runtime 驗證（純文檔票）。
- 人工對照：§4.4 現行 localhost-only / fail-open / 單次 POST 與 §4.6 policy subset `impl_status` 一致。

### §4 阻塞

無 blocking。完整 policy 表擴充待 Reviewer。

### §5 Execution 入口 cross-ref（2026-06-24 refresh）

| 票 id | 與 §4.6 關係 |
|-------|--------------|
| `WH-P7-PROD-prod-rollout-governance-bootstrap-v1` | Wave-P7-6 prod flip / required CI · 對照本 policy · FRAME pending |
| `WH-P7-NOTIF-staging-integration-execute-v1` | **`validated`** · local slot S1–S4 GO（run_id `20260623T165252Z`）· 不 flip prod · **仍缺**真 Infra / 客戶 staging endpoint |

---

## C_REPORT (Reviewer)

- **review_date**: 2026-06-22
- **reviewer_role**: Wave-H Reviewer (C)
- **verdict**: **`accepted_with_gaps`**
- **conclusion**: 純設計票 §4.6 骨架與 policy subset 可接受；sandbox 基線（fail-open、localhost-only、advisory CI）與 WD-P7-T1/T2/T3 現碼一致；prod-tier 能力（retry / DLQ / HMAC / non-localhost URL）正確標為 `not_implemented_yet`，未宣稱實作完成。缺口：§4.6.0 僅 7 列 subset（backoff 參數、DLQ retention、idempotency header 等完整列待後續 scribe 擴充），不阻擋 design sign-off。

### impl_consistency_check（§4.6 vs 現碼）

| policy_item / 能力 | §4.6 impl_status | 現碼對照 | 一致？ |
|--------------------|------------------|----------|--------|
| `emit_fail_open` | implemented | `notification_gateway_v1` post-emit dispatch 包 try/except；orchestrator `emit_notification_safe` fail-open | ✅ |
| `dispatch_fail_open` | implemented | `notification_dispatch_v1` / webhook handler 失敗回 `fail_open: True`，不 raise | ✅ |
| `webhook_url_tier` (sandbox) | implemented | `notification_webhook_adapter_v1._is_sandbox_safe_url()` 僅允許 localhost/127.0.0.1 | ✅ |
| `webhook_url_tier` (prod/staging) | not_implemented_yet | 無 `GOV_NOTIFICATION_WEBHOOK_TIER` / allowlist 讀取 | ✅ |
| `webhook_hmac` | not_implemented_yet | adapter 註解明列 future phase；`secret_key` 欄位未簽名 | ✅ |
| `webhook_retry_max_attempts` | not_implemented_yet（default=0） | 單次 POST，無 retry/backoff 邏輯 | ✅ |
| `webhook_dlq_enabled` | not_implemented_yet | 無 DLQ 路徑 / jsonl | ✅ |
| `advisory_ci_blocking` | implemented（false） | `p7-notification-smoke.yml`：`continue-on-error: true`；URL 固定 `127.0.0.1:8080`；無 prod env | ✅ |
| `event_id` / idempotency | partial | gateway emit 產生 `event_id`；webhook payload 帶入；HTTP `Idempotency-Key` header 未送 | ✅ |
| proposed env keys (`TIER` / `ALLOWLIST` / `HMAC_SECRET`) | not_implemented_yet | 程式未讀取 | ✅ |

**WD-P7-T2 NonScope 對照**：T2 明確 deferred 的 retry / DLQ / HMAC / prod URL，§4.6 均已制度化承接且 `impl_status` 與 T2 B_REPORT skeleton 標示一致。

### acceptance_criteria_review

| AC | 結果 | 備註 |
|----|------|------|
| AC-1 §4.6.0–§4.6.7 骨架 | pass | 目錄完整；policy 表為 subset（gap，非 blocking） |
| AC-2 impl_status 與現碼一致 | pass | 見上表 |
| AC-3 不矛盾 fail-open | pass | §4.6.2/§4.6.3 明文 retry/DLQ 為 future opt-in |
| AC-4 HMAC 小節 | pass | 算法、header、canonicalization、timestamp 窗口均有 proposed_default |
| AC-5 URL policy 三級 tier | pass | sandbox/staging/prod 定義 + CI 禁止未授權客戶 endpoint |
| AC-6 ≥2 張衍伸實作票 | pass | §4.6.7 + FRAME 已列 |
| AC-7 B_REPORT T2 NonScope 對照 | pass | B_REPORT §2 已填 |
| AC-8 APP-DOC | pass | 合約無本機絕對路徑、無 secret 範例值 |

### blocking_issues

**無技術 blocking。** 本票為 policy SSOT；sandbox 行為未被 §4.6 改寫。剩餘工作均屬**未來實作票**或**文檔擴充**（完整 policy 表），不得在本輪宣稱 prod 通知已就緒。

### suggested_followup_tickets

| 票號 | 一句話 |
|------|--------|
| `WH-P7-NOTIF-RETRY-v1` | 在 `notification_webhook_adapter_v1` 實作可配置 retry + backoff；失敗寫入 DLQ 路徑；unittest 覆蓋 5xx/timeout |
| `WH-P7-NOTIF-HMAC-v1` | HMAC-SHA256 簽名發送 + receiver contract test；secret 僅 env |
| `WH-P7-NOTIF-PROD-URL-v1` | `GOV_NOTIFICATION_WEBHOOK_TIER` + non-localhost allowlist；staging 整合測試（須尚書省 prod/staging 批文） |

（`WH-P7-NOTIF-DLQ-v1` 可併入 RETRY 票，依 §4.6.4 建議。）

### risk_level

low — 純文檔；未觸 runtime / CI / secrets。

### suggestions（非 blocking）

- Scribe 後續小票可將 §4.6.0 擴至 FRAME 所述 12+ 列（backoff、DLQ retention、idempotency header 等）。
- 開 RETRY / HMAC / PROD-URL 實作票前，Orchestrator 確認尚書省 staging/prod 批文門檻（§4.6.7）。

---

## D_REPORT (Scribe)

- **handoff_date**: 2026-06-23
- **from**: P7 prod-tier policy 骨架（`design_accepted` · doc-only）
- **to**: 衍伸 impl / doc-sync / staging wave

- **policy_scope_only**: 本票 **不宣稱** prod 通知已就緒；§4.6 為 governance SSOT，runtime 由下列票承接：

| 能力 | 設計票 | 實作票 |
|------|--------|--------|
| DLQ | `WH-P7-NOTIF-DLQ-v1` | `*-impl-v1` · `*-inspect-cli-*`（**validated**） |
| URL tier | `WH-P7-NOTIF-PROD-URL-v1`（**done_with_gaps**） | `*-impl-v1`（**validated**） |
| Retry prod | `WH-P7-NOTIF-RETRY-prod-v1`（**done_with_gaps**） | `*-impl-v1`（**validated**） |
| HMAC prod | `WH-P7-NOTIF-HMAC-prod-mandatory-v1`（**done_with_gaps**） | `WH-P7-NOTIF-HMAC-prod-impl-v1`（**validated**） |

- **why_not_validated**: 本票維持 `design_accepted` — 僅 policy 骨架；§4.6.0 完整列 · `impl_status` 與真 env 啟用留 doc-sync / Wave-P7-6 CI governance 票。Wave-P7-5 首輪 **local slot** execute 已 GO（run_id `20260623T165252Z` · execute **`validated`**）— **仍缺**真 Infra / 客戶 staging endpoint · 真 governance_dual · 48h 觀測 · prod rollout / required CI。

**Execution 入口票（2026-06-24 refresh）**

| 票 id | 狀態 | 與本 policy 關係 |
|-------|------|------------------|
| **`WH-P7-PROD-prod-rollout-governance-bootstrap-v1`** | `design_accepted` | Wave-P7-6 prod flip / required CI G1–G8 · 對照本票 §4.6 · FRAME pending |
| **`WH-P7-NOTIF-staging-integration-execute-v1`** | **`validated`** | local slot S1–S4 GO · run_id `20260623T165252Z` · 不 flip prod |

完成 prod-rollout-governance-bootstrap 後本 policy 票可升 **`done_with_gaps`**（design 收口 · **不宣稱 prod 已啟用**）。
