# WH-P7-NOTIF-HMAC-prod-impl-v1 — Ticket State

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Wave-H+1 · **P7 HMAC prod 線 tier mandatory gate 實作票**  
> 上游：`WH-P7-NOTIF-HMAC-prod-mandatory-v1`（staging/prod mandatory policy · `frame_ready`）· `WH-P7-NOTIF-HMAC-impl-v1`（sender partial · `impl_done`）· `WH-P7-NOTIF-HMAC-receiver-contract-v1`（§4.6.5.2 · `implementer_done_pending_review`）· `WH-P7-NOTIF-PROD-URL-impl-v1`（URL tier gate partial · `review_done_pending_scribe`）· `WH-P7-sandbox-line-wrapup-v1`（sandbox validated）· `WH-P7-PROD-roadmap-v1`（Wave-P7-3）  
> 產物：adapter tier-aware HMAC mandatory gate + unittest matrix；**合約 doc 更新由 doc-sync 票處理，本票不直接改 docs**

---

## FRAME

### handoff header

**staging/prod tier HMAC mandatory gate 實作票**：依 `WH-P7-NOTIF-HMAC-prod-mandatory-v1` 設計與合約 §4.6.5 / §4.6.6.3，在 `notification_webhook_adapter_v1` 實作 tier-aware HMAC gate——`TIER ∈ {staging, prod}` 時驗證 HMAC_ENABLED + secret + event_id + 簽名成功；任一失敗 → **不 POST** 並標記 `blocked_by_hmac_tier_policy` + `blocked_rule`；sandbox 行為（opt-in · fail-open unsigned）**維持不變**。本輪僅 FRAME 骨架；**零 code / 零 test / 零 CI 變更（本輪）**。

---

### 1. Background

| 層級 | 現況 | 證據 |
|------|------|------|
| **Sender HMAC** | **partial**（sandbox-only · env gated · default off · **fail-open unsigned**） | `WH-P7-NOTIF-HMAC-impl-v1` · `notification_webhook_adapter_v1._apply_hmac_headers` |
| **Env gate** | `GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED=1` **且** `GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET` 非空 → 簽名；否則不簽名 | `_should_apply_hmac_signature()` |
| **Receiver contract** | §4.6.5.2 normative SSOT 已落盤；reference impl / fixtures **`not_implemented_yet`** | `WH-P7-NOTIF-HMAC-receiver-contract-v1` |
| **Tier policy** | §4.6.6.3 matrix：`staging`/`prod` **`hmac_required=true`**；sandbox `false` | `WH-P7-NOTIF-PROD-URL-v1` · 合約 §4.6.6.3 |
| **URL tier gate** | `TIER` + `URL_ALLOWLIST` minimal gate **partial**（staging/prod https + allowlist） | `WH-P7-NOTIF-PROD-URL-impl-v1` |
| **HMAC tier gate** | policy 已宣告 mandatory；adapter **尚未** enforce — staging/prod 仍可能 unsigned POST | `WH-P7-NOTIF-HMAC-prod-mandatory-v1` §2.2 |

**缺口**：§4.6.6.3 已標 staging/prod HMAC mandatory，但 sender adapter 無 tier-aware fail-closed 分支；缺 `HMAC_ENABLED`、空 secret、缺 `event_id`、簽名計算異常時，staging/prod 與 sandbox 行為相同（fail-open unsigned）。本票填補 **runtime tier HMAC gate**。

#### Tier HMAC 行為摘要（一句話 · 供 AC 對照）

| tier | HMAC 行為 |
|------|-----------|
| **sandbox** | HMAC **可選**；預設不簽名；缺 secret / 簽名失敗 **fail-open** 仍 POST。 |
| **staging** | HMAC **強制**；未啟用、缺 secret、缺 `event_id` 或簽名失敗 → **拒 POST** 並記 `blocked_by_hmac_tier_policy`。 |
| **prod** | 同 staging mandatory；語意更嚴（§4.6.6.3「缺簽名 reject POST」）；須尚書省批文後才啟用 tier。 |

---

### 2. Goal

在 adapter 實作 **staging/prod tier HMAC mandatory gate**（Implementer 下一輪 landing），至少交付：

1. **Tier gate 分支**：`TIER ∈ {staging, prod}` 且 URL tier gate 通過後、第一次 HTTP POST 前，驗證 HMAC master gate + secret + event_id + 簽名可計算。
2. **Fail-closed POST**：任一檢查失敗 → 不 POST；回傳 `blocked_reason=blocked_by_hmac_tier_policy` + `blocked_rule`（見 §2.1）；外層 dispatch 仍 fail-open `ok=True`。
3. **Sandbox regression**：`TIER=sandbox`（或未設）→ 跳過 tier HMAC gate；既有 fail-open unsigned 行為不變。
4. **Unittest matrix**：≥6 scenario（見 §2.3）；sandbox regression + staging/prod mandatory cases。
5. **Gate 順序**：env master switch → URL tier gate（PROD-URL-impl · **不改其邏輯**）→ **HMAC tier gate（本票）** → HTTP POST + retry loop。

#### 2.1 `blocked_rule` 枚舉（normative · 來自 mandatory 設計票）

| `blocked_rule` | 觸發條件 | staging | prod |
|----------------|----------|---------|------|
| `hmac_disabled` | `HMAC_ENABLED` 未設 / `0` / 非 truthy | reject | reject |
| `hmac_secret_missing` | `HMAC_ENABLED=1` 但 secret 空 | reject | reject |
| `hmac_event_id_missing` | payload 無 `event_id` 或空字串 | reject | reject |
| `hmac_signing_failed` | 簽名計算拋錯或產物不完整 | reject | reject |

**Blocked 回傳欄位（proposed_default）**：

| 欄位 | 值 |
|------|-----|
| `webhook_result.ok` | `True`（外層 dispatch fail-open 不變） |
| `webhook_result.dispatched` | `False` |
| `webhook_result.dry_run` | `True` |
| `webhook_result.blocked_reason` | `blocked_by_hmac_tier_policy` |
| `webhook_result.blocked_rule` | 見上表 |
| log | tier + rule + **不含** secret 原文 |

#### 2.2 未來實作 touch points

| 類型 | 路徑 | 預期變更 |
|------|------|----------|
| **adapter** | `delivery/notification_webhook_adapter_v1.py` | 新增 tier-aware HMAC gate（preflight）；staging/prod fail-closed vs sandbox fail-open 分支；與既有 `_apply_hmac_headers` / URL gate 串接 |
| **unittest** | `tests/test_notification_webhook_dispatch_v1.py` | 新增 `TestNotificationWebhookTierHmacPolicy`（或等價 class）；staging/prod mandatory cases + sandbox regression |

**必跑測試**：

```bash
python -m unittest tests.test_notification_webhook_dispatch_v1 -v
```

**合約更新**：§4.6.0 / §4.6.5.1 tier gate / §4.6.6.3 enforce 脚注 → **`WH-P7-NOTIF-contract-doc-sync-v1`**（或子票）；**本票不直接修改 docs**。

#### 2.3 建議 unittest scenario（Implementer AC）

| # | Scenario | 斷言 |
|---|----------|------|
| 1 | sandbox · HMAC off | unsigned POST 仍成功（regression） |
| 2 | sandbox · HMAC on · secret 空 | fail-open unsigned POST（regression） |
| 3 | staging · HMAC off | 不 POST · `blocked_rule=hmac_disabled` |
| 4 | staging · HMAC on · secret 空 | 不 POST · `blocked_rule=hmac_secret_missing` |
| 5 | staging · HMAC ready · allowlist OK | signed POST · headers 存在 |
| 6 | prod · HMAC ready · allowlist missing | URL gate 先阻（與 HMAC gate 順序 regression） |
| 7 | staging · payload 無 `event_id` | 不 POST · `blocked_rule=hmac_event_id_missing` |

---

### 3. Non-Goals

- ❌ **不實作** receiver 端驗簽程式、fixtures、sample impl（→ `WH-P7-NOTIF-HMAC-receiver-fixtures-v1` · `WH-P7-NOTIF-HMAC-receiver-sample-impl-v1`）。
- ❌ **不改** sandbox 行為 — default HMAC off · fail-open unsigned · opt-in 演練 **維持不變**。
- ❌ **不改** PROD-URL gate 邏輯本身（`WH-P7-NOTIF-PROD-URL-impl-v1` 已交付；本票僅在其後串接 HMAC gate）。
- ❌ **不修改** `docs/outbox-and-feedback-layer-contract-v1.md`（→ doc-sync 票）。
- ❌ **不改** sender header 格式、signed string、env 鍵名（以 `WH-P7-NOTIF-HMAC-impl-v1` 為事實標準）。
- ❌ **不實作** retry / DLQ tier readiness gate 本體（→ `WH-P7-NOTIF-RETRY-prod-impl-v1`）；本票僅定義 HMAC gate 與其 **順序 / 依賴**。
- ❌ **不啟用**真實 staging/prod endpoint 或要求尚書省執行 prod rollout。
- ❌ **不升格** advisory CI；staging/prod HMAC gate CI 驗證留 `WH-P7-NOTIF-HMAC-prod-ci-v1`。
- ❌ **不合併** Phase 8.8 `orchestration_bridge_outbox`（§2.2 永久分軌）。

---

### 4. Acceptance Criteria（實作層 · Implementer 下一輪）

- **AC-1**：`TIER ∈ {staging, prod}` 且 URL gate 通過後，缺 HMAC_ENABLED / secret / event_id / 簽名失敗 → 不 POST + `blocked_by_hmac_tier_policy` + 正確 `blocked_rule`。
- **AC-2**：`TIER=sandbox`（或未設）→ tier HMAC gate **跳過**；scenario 1–2 regression 通過。
- **AC-3**：staging · HMAC ready · allowlist OK → signed POST 含 `X-Gov-Signature-256` · `X-Gov-Timestamp` · `X-Gov-Event-Id`。
- **AC-4**：Gate 順序：URL gate 先於 HMAC gate（scenario 6 regression）。
- **AC-5**：外層 dispatch fail-open：`ok=True` · blocked 時 `dispatched=False` · `dry_run=True`。
- **AC-6**：`python -m unittest tests.test_notification_webhook_dispatch_v1 -v` 全綠（含新增 scenario）。
- **AC-7**：與 `WH-P7-NOTIF-HMAC-prod-mandatory-v1` §2.2 · §4.6.6.3 matrix **無矛盾**。
- **AC-8**：log 不含 secret 原文；FRAME 正文零本機絕對路徑。

---

### 5. AllowedPaths / BlockedPaths

#### AllowedPaths（Implementer 下一輪）

- `delivery/notification_webhook_adapter_v1.py`
- `tests/test_notification_webhook_dispatch_v1.py`
- `04_Workflows/tickets/WH-P7-NOTIF-HMAC-prod-impl-v1_state.md`

#### BlockedPaths

- `docs/**`（合約更新 → doc-sync 票）
- `delivery/notification_dispatch_v1.py` · `delivery/notification_gateway_v1.py`
- `routing/**` · `.github/workflows/**` · 暗部 `gov_core_system/core/**`
- 其他票檔 · `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `.cursor/rules/**`
- `.env` · secrets · 客戶實際 webhook URL
- `04_Workflows/00_Agent_Work_Progress.md`（Progress append 留 Scribe 輪）

---

### 6. Dependencies

- `WH-P7-NOTIF-HMAC-prod-mandatory-v1`（tier mandatory policy SSOT · `frame_ready`）
- `WH-P7-NOTIF-HMAC-impl-v1`（sender HMAC partial · headers / signed string SSOT）
- `WH-P7-NOTIF-HMAC-receiver-contract-v1`（§4.6.5.2 receiver 驗簽 / idempotency · 只讀對照）
- `WH-P7-NOTIF-PROD-URL-impl-v1`（URL tier gate partial · gate 順序依賴）
- `WH-P7-sandbox-line-wrapup-v1`（sandbox 封箱 · regression baseline）
- `WH-P7-PROD-roadmap-v1`（Wave-P7-3 HMAC prod mandatory 索引）
- `docs/outbox-and-feedback-layer-contract-v1.md` §4.6.5 · §4.6.6（只讀）

---

## STATE

- **overall_status**: `validated`
- **current_owner**: scribe
- **next_action**: Scribe (D) Progress append；Orchestrator 開 `WH-P7-NOTIF-HMAC-prod-ci-v1` / doc-sync / receiver fixtures
- **notes**:
  - sandbox 對照：`WH-P7-NOTIF-HMAC-impl-v1` · fail-open unsigned
  - staging S3 演練：`WH-P7-PROD-staging-smoke-runbook-v1` · receiver fixtures 硬依賴
  - staging/prod HMAC mandatory gate **validated**（unittest only · 非真 env）
  - 合約 §4.6.5.1 tier gate 擴寫留 doc-sync 票
- **last_updated**: 2026-06-23 · progress agent
- **wave**: Wave-H+1 · P7 prod line · HMAC tier mandatory impl
- **status_by_role**:
  - **Orchestrator (A)**: done — FRAME 骨架已落盤
  - **Implementer (B)**: done — 2026-06-23 · adapter tier HMAC gate + unittest
  - **Reviewer (C)**: done — 2026-06-23 · **`accepted`**
  - **Scribe (D)**: pending — D_REPORT 已由 Reviewer 代填

---

## B_REPORT

### changed_files

| 檔案 | 變更 |
|------|------|
| `delivery/notification_webhook_adapter_v1.py` | 新增 `_check_hmac_tier_policy`；URL gate 之後、retry readiness 之前串接 HMAC tier gate |
| `tests/test_notification_webhook_dispatch_v1.py` | 新增 `TestNotificationWebhookHmacTierPolicy`（7 scenario）；更新 retry 票 HMAC-off 斷言對齊 gate 順序 |
| `04_Workflows/tickets/WH-P7-NOTIF-HMAC-prod-impl-v1_state.md` | B_REPORT + STATE |

### staging/prod HMAC gate 行為

**Gate 順序**：env master → URL tier gate → **HMAC tier gate** → tier retry readiness → HTTP POST + retry。

**staging / prod**（URL gate 通過後）：

| 條件 | 行為 |
|------|------|
| `HMAC_ENABLED` 未設 / `0` | 不 POST · `blocked_reason=blocked_by_hmac_tier_policy` · `blocked_rule=hmac_disabled` |
| `HMAC_ENABLED=1` 但 secret 空 | 不 POST · `blocked_rule=hmac_secret_missing` |
| payload 無 `event_id` | 不 POST · `blocked_rule=hmac_event_id_missing` |
| 簽名計算失敗 | 不 POST · `blocked_rule=hmac_signing_failed` |
| 全部通過 | 進入 retry readiness → signed POST（沿用 `_apply_hmac_headers`） |

**外層 dispatch 語意（§4.6.5 / §4.6.6 對齊）**：被 HMAC gate 阻擋時 **`ok=True`**（fail-open orchestrator）、`dispatched=False`、`dry_run=True`；**不 POST**。

**sandbox**（或未設 `TIER`）：HMAC tier gate **跳過**；HMAC off / 缺 secret / 簽名失敗仍 fail-open unsigned POST（regression 不變）。

### 新增測試

| TestCase | Scenario |
|----------|----------|
| `test_sandbox_tier_hmac_gate_regression_allows_post` | sandbox · HMAC on/off 均 POST · 無 blocked_reason |
| `test_staging_tier_hmac_ready_allows_signed_post` | staging · HMAC ready · signed POST + headers 可驗算 |
| `test_staging_tier_hmac_disabled_blocks_post` | staging · HMAC off · `hmac_disabled` |
| `test_staging_tier_hmac_secret_missing_blocks_post` | staging · secret 空 · `hmac_secret_missing` |
| `test_staging_tier_hmac_signing_failed_blocks_post` | staging · 簽名拋錯 · `hmac_signing_failed` |
| `test_staging_tier_missing_event_id_blocks_post` | staging · 無 event_id · `hmac_event_id_missing` |
| `test_prod_tier_url_gate_blocks_before_hmac_gate` | prod · URL gate 先阻 · HMAC gate 未觸發 |

### 驗證

```bash
python -m unittest tests.test_notification_webhook_dispatch_v1 -v
```

- **exit code**: 0
- **tests**: 39/39 OK（含 7 個新增 HMAC tier scenario；既有 regression 仍綠）

---

## C_REPORT

- **review_date**: 2026-06-23
- **reviewer_role**: P7 prod line Reviewer (C)
- **verdict**: **`accepted`**
- **conclusion**: `_check_hmac_tier_policy` 在 URL gate 之後、retry readiness 之前 enforce staging/prod mandatory HMAC（enabled + secret + event_id + 簽名 dry-run）；四種 `blocked_rule` 枚舉與 `WH-P7-NOTIF-HMAC-prod-mandatory-v1` §2.2.2 一致；sandbox 跳過 tier gate · fail-open unsigned 不退化；外層 dispatch fail-open 對齊 §4.6.5 / PROD-URL blocked 路徑。

**一句話（gate 行為）**：staging/prod 在 URL 通過後，HMAC 未就緒或簽名不可算 → 不 POST · `blocked_by_hmac_tier_policy` + 細粒度 `blocked_rule`；sandbox 仍 opt-in · fail-open unsigned。

### impl_consistency_check

| 檢查項 | 設計 / 合約 §4.6.5 / §4.6.6.3 | 現碼 / 測試 | 結果 |
|--------|-------------------------------|-------------|------|
| Gate 順序 URL 先於 HMAC | §2.2.3 | `send_webhook_notification` · `test_prod_tier_url_gate_blocks_before_hmac_gate` | ✅ |
| HMAC off | `hmac_disabled` | L698–703 · scenario 3 | ✅ |
| Secret 空 | `hmac_secret_missing` | L705–711 · scenario 4 | ✅ |
| 缺 `event_id` | `hmac_event_id_missing` | L713–718 · scenario 7 | ✅ |
| 簽名失敗 | `hmac_signing_failed` | L731–737 · scenario 5（patch `_compute_hmac_sha256_hex`） | ✅ |
| HMAC ready → signed POST | §4.6.5.1 headers | `test_staging_tier_hmac_ready_allows_signed_post` | ✅ |
| Blocked 回傳形狀 | `ok=True` · `dispatched=False` · `dry_run=True` | blocked 路徑 L1051–1067 | ✅ |
| Sandbox regression | fail-open · 無 tier gate | `test_sandbox_tier_hmac_gate_regression_allows_post` | ✅ |
| Sandbox secret 空仍 POST | §2.1 baseline | 含於 sandbox regression subTest | ✅ |
| 合約 doc tier gate 擴寫 | 待 doc-sync | 本票 Non-goal | ✅ 邊界內 |

### acceptance_criteria_review（AC-1～AC-8）

| AC | 結果 |
|----|------|
| AC-1 staging/prod 四 failure → blocked | **pass** |
| AC-2 sandbox regression | **pass** |
| AC-3 signed POST + headers | **pass** |
| AC-4 URL 先於 HMAC | **pass** |
| AC-5 fail-open dispatch | **pass** |
| AC-6 unittest 全綠 | **pass** — Reviewer 重跑 **39/39 OK** |
| AC-7 與 mandatory 設計票無矛盾 | **pass** |
| AC-8 log 無 secret · 零絕對路徑 | **pass** |

### 驗證證據

```bash
python -m unittest tests.test_notification_webhook_dispatch_v1 -v
```

**結果**：39/39 OK ✅

### non-blocking nits

- 無 prod tier HMAC-ready happy path 專測（staging 已覆 signed POST · prod 語意同 staging mandatory）。
- §4.6.5.1 tier gate 小節 / §4.6.6.3 enforce 脚注仍待 doc-sync（預期非本票 scope）。

---

## D_REPORT

- **scribe_date**: 2026-06-23 · Reviewer 代填（本輪邊界 · 未 append Progress）
- **verdict_echo**: Reviewer **`accepted`** — staging/prod HMAC mandatory gate **validated**；`overall_status` → **`validated`**
- **handoff_one_liner**: adapter 已 tier-aware fail-closed HMAC preflight；與 RETRY-prod-impl · DLQ-impl 串成 staging/prod 三 mandatory 前置鏈；receiver 端與合約正文仍 deferred。
- **value_for_p7**: Wave-P7-3 HMAC prod mandatory 之 **sender runtime enforce** 落地；解除 staging/prod unsigned POST 與 §4.6.6.3 `hmac_required=true` 的 policy/runtime 落差（仍 unittest-only · 無 prod rollout）。
- **next_tickets**（建議順序）:

| 順序 | 票號 | 說明 |
|------|------|------|
| 1 | **`WH-P7-NOTIF-contract-doc-sync-v1`**（或子票） | §4.6.5.1 tier HMAC gate · §4.6.0 / §4.6.6 env 表 · `impl_status` |
| 2 | **`WH-P7-NOTIF-HMAC-prod-ci-v1`** | CI/doc lint 驗 HMAC gate 與 §4.6.6.3 一致 |
| 3 | **`WH-P7-NOTIF-HMAC-receiver-fixtures-v1`** | 已簽名 body + headers sidecar |
| 4 | **`WH-P7-NOTIF-HMAC-receiver-sample-impl-v1`** | 最小 reference receiver + contract test |
| 5 | **`WH-P7-NOTIF-staging-integration-v1`** | sender 三 gate + mock receiver 整合 |

- **progress_entry**: 本輪 **未** append `00_Agent_Work_Progress.md`（任務邊界）
