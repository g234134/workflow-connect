# WH-P7-NOTIF-RETRY-prod-impl-v1 — Ticket State

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Wave-H+1 · **P7 prod 線 staging/prod tier retry 行為實作票**  
> 上游：`WH-P7-NOTIF-RETRY-prod-v1`（`design_accepted` · tier retry policy SSOT）· `WH-P7-NOTIF-RETRY-SANDBOX-v1` · `WH-P7-NOTIF-DLQ-impl-v1` · `WH-P7-NOTIF-PROD-URL-impl-v1` · `WH-P7-PROD-roadmap-v1` Wave-P7-2  
> 產物：adapter tier readiness gate（staging/prod retry + DLQ + HMAC preflight）· tier default env fallback · unittest matrix；**合約 doc 更新交 doc-sync 票 · 本票不直接改 docs**

---

## FRAME

### handoff header

**staging/prod tier retry 行為實作票**：依 `WH-P7-NOTIF-RETRY-prod-v1` 設計，在 `notification_webhook_adapter_v1` 實作 **tier readiness gate** — staging/prod 須 `max_attempts≥1`、`DLQ_ENABLED=1`、HMAC ready 才進入 retry loop；sandbox 維持 opt-in · default 單次 POST 不變。最終失敗（retry 用盡或不可重試 4xx）須落 DLQ（沿用 `WH-P7-NOTIF-DLQ-impl-v1` 路徑）。本票 **frame_ready** 骨架；Implementer 接棒後才動 adapter / tests。

---

### 1. 設計票摘錄（`WH-P7-NOTIF-RETRY-prod-v1`）

#### 1.1 Sandbox 現行行為（baseline · 本票 **不變**）

| 項 | 定案 |
|----|------|
| **Default attempts** | `GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS` 未設或 `≤0` → **單次 POST** |
| **Opt-in retry** | 設 `≥1` → 指數退避 retry loop（408/429/5xx/連線/timeout 可重試） |
| **DLQ** | **無 mandatory**；`DLQ_ENABLED` default `0` |
| **HMAC** | **無 mandatory**；default off · fail-open unsigned |
| **Tier gate** | sandbox tier → 僅 localhost URL gate；**不**檢查 retry/DLQ/HMAC mandatory |

**一句話**：sandbox 上 retry / DLQ / HMAC 全 **opt-in** · default **零 retry** · 失敗靠 log。

#### 1.2 Staging / prod retry 目標（本票 normative 實作範圍）

**一句話目標**：staging/prod tier 下須 **retry≥1 + DLQ=1 + HMAC ready** 三 gate 全通過才 POST；retry 用盡或不可重試 4xx **最終失敗必落 DLQ**；gate 拒絕仍 dispatch **fail-open** `ok=True`。

| 項 | staging | prod |
|----|---------|------|
| **`max_attempts` 下限** | **≥ 1**（mandatory） | **≥ 1** |
| **建議 tier default**（env 未設） | `3` / backoff `500`/`8000` ms | `5` / `1000`/`30000` ms |
| **`DLQ_ENABLED`** | **must be `1`** | **must be `1`** |
| **HMAC** | enabled + secret 非空 | 同上 |
| **Tier readiness gate** | 第一次 POST 前驗證上述三項；缺任一 → reject POST · `blocked_rule` ∈ {`retry_policy_violation`, `dlq_policy_violation`, `hmac_policy_violation`} | 同上 |
| **DLQ 寫入** | 僅最終失敗；retry 中途不寫 | 同上 |
| **外層語意** | gate 拒絕 / retry 用盡仍 **fail-open** dispatch | 同上 |

**依賴**：HMAC tier gate 可與 `WH-P7-NOTIF-HMAC-prod-mandatory-v1` 合併或串行；Implementer 裁決但 **must** 在 retry loop 前完成 preflight。

#### 1.3 Sandbox vs staging vs prod 三層差異（對照表）

| 維度 | **sandbox** | **staging** | **prod** |
|------|-------------|-------------|----------|
| Retry mandatory | 否（default 0） | **是**（≥1） | **是** |
| DLQ mandatory | 否（default off） | **是**（=1） | **是** |
| HMAC mandatory | 否（opt-in） | **是** | **是** |
| Tier readiness gate | 無 | retry + DLQ + HMAC | 同上 + registry（URL 票） |
| 最終失敗落 DLQ | opt-in enabled 時 | **必寫** | **必寫** |

#### 1.4 合約對照（只讀 · 本票不直接改 doc）

- §4.6.3：`staging/prod retry mandatory` 現 **not_implemented_yet**
- §4.6.4：DLQ 落盤 **partial**（`WH-P7-NOTIF-DLQ-impl-v1` · default off）
- §4.6.6.3 tier matrix：`retry_required=true` · `dlq_required=true`（staging/prod）
- §4.6.6.4 enablement checklist：Retry 升格 → 本票

---

### 2. 未來 Implementer touch points

#### 2.1 可能 touch 的檔案

| 檔案 | 預期變更 |
|------|----------|
| `delivery/notification_webhook_adapter_v1.py` | tier readiness gate；staging/prod tier default attempts/backoff fallback；`blocked_rule` 擴充（`retry_policy_violation` / `dlq_policy_violation` / `hmac_policy_violation`）；sandbox regression 不退化 |
| `tests/test_notification_webhook_dispatch_v1.py` | 新增 staging/prod retry gate cases（reject：attempts=0 / DLQ off / HMAC missing；accept：三 gate 通過 + retry→DLQ）；sandbox regression |

#### 2.2 必跑驗證

```bash
python -m unittest tests.test_notification_webhook_dispatch_v1 -v
```

#### 2.3 不在本票 scope

| 項 | 交給 |
|----|------|
| `docs/outbox-and-feedback-layer-contract-v1.md` §4.6.3 擴寫 · §4.6.0 / §4.6.6 `impl_status` | `WH-P7-NOTIF-contract-doc-sync-v1`（或子票） |
| CI workflow 納入 tier gate matrix | `WH-P7-NOTIF-RETRY-prod-ci-v1` |
| prod per-customer registry gate | 後續 URL 票 |
| HMAC prod mandatory gate 本體（若未合併） | `WH-P7-NOTIF-HMAC-prod-mandatory-v1` |

---

### 3. Non-Goals（本票）

- ❌ **不改** sandbox 行為 — default `max_attempts=0` · opt-in retry · DLQ default off · HMAC fail-open **維持不變**。
- ❌ **不改** 現有 retry loop 算法（`_is_retriable_http_result` · backoff 公式）— 僅加 tier **policy 層** gate 與 default。
- ❌ **不在本票觸碰** PROD-URL gate 以外的 URL/registry 邏輯（`WH-P7-NOTIF-PROD-URL-impl-v1` 已交付 minimal gate）。
- ❌ **不修改** `docs/**` · `.github/workflows/**` · 其他票檔（本輪 skeleton 僅建本票）。
- ❌ **不啟用** 真實 staging/prod 環境；僅 unittest 驗證 gate 行為。
- ❌ **不實作** DLQ inspect CLI · replay pipeline。
- ❌ **不合併** Phase 8.8 `orchestration_bridge_outbox` DLQ。

---

### 4. Acceptance Criteria（Implementer 交付 · 待填 B_REPORT）

- **AC-1**：sandbox tier regression — default 單次 POST · opt-in retry · DLQ off 行為不變。
- **AC-2**：staging/prod tier · `max_attempts≤0` → reject POST · `blocked_rule=retry_policy_violation` · 外層 fail-open。
- **AC-3**：staging/prod tier · `DLQ_ENABLED≠1` → reject POST · `blocked_rule=dlq_policy_violation`。
- **AC-4**：staging/prod tier · HMAC 未 ready → reject POST · `blocked_rule=hmac_policy_violation`（或與 HMAC-prod-mandatory 票合併）。
- **AC-5**：staging/prod tier · 三 gate 通過 + persistent failure → retry 用盡 + DLQ jsonl 1 行。
- **AC-6**：`python -m unittest tests.test_notification_webhook_dispatch_v1 -v` 全綠。
- **AC-7**：不修改合約 doc（doc-sync 另票）。

---

### 5. AllowedPaths / BlockedPaths

#### AllowedPaths（Implementer 接棒後）

- `delivery/notification_webhook_adapter_v1.py`
- `tests/test_notification_webhook_dispatch_v1.py`
- `04_Workflows/tickets/WH-P7-NOTIF-RETRY-prod-impl-v1_state.md`（本票 STATE / B/C/D_REPORT）

#### BlockedPaths

- `docs/**`（合約更新 → doc-sync 票）
- `.github/workflows/**`
- 其他票檔 · `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `.cursor/rules/**`
- `.env` · secrets · 客戶實際 webhook URL
- 暗部 `gov_core_system/core/**`

---

### 6. Dependencies

- `WH-P7-NOTIF-RETRY-prod-v1`（`design_accepted`）
- `WH-P7-NOTIF-RETRY-SANDBOX-v1`（retry loop SSOT · sandbox partial）
- `WH-P7-NOTIF-DLQ-impl-v1`（DLQ append partial）
- `WH-P7-NOTIF-PROD-URL-impl-v1`（tier / URL gate partial · blocked 路徑語意對齊）
- `WH-P7-NOTIF-HMAC-impl-v1` · `WH-P7-NOTIF-HMAC-prod-mandatory-v1`（HMAC gate · 可並行）
- `WH-P7-PROD-roadmap-v1` Wave-P7-2
- `docs/outbox-and-feedback-layer-contract-v1.md` §4.6.3 · §4.6.4 · §4.6.6（只讀）

---

## STATE

- **overall_status**: `validated`
- **current_owner**: scribe
- **next_action**: Scribe (D) Progress append；Orchestrator 開 `WH-P7-NOTIF-RETRY-prod-ci-v1` / doc-sync 子段
- **notes**:
  - sandbox 對照：`WH-P7-NOTIF-RETRY-SANDBOX-v1` · default max_attempts=0
  - staging S4 演練：`WH-P7-PROD-staging-smoke-runbook-v1` · retry+DLQ E2E · execute 票
- **last_updated**: 2026-06-23 · scribe (D)
- **wave**: Wave-H+1 · P7 prod line · notification retry prod impl
- **status_by_role**:
  - **Orchestrator (A)**: done — 開票 FRAME skeleton
  - **Implementer (B)**: done — adapter tier retry gate + unittest
  - **Reviewer (C)**: done — 2026-06-23 · **`accepted_with_nits`**
  - **Scribe (D)**: pending — D_REPORT 已由 Reviewer 代填

---

## B_REPORT

- **implementer_date**: 2026-06-23
- **scope**: adapter tier-aware retry defaults + staging/prod readiness gate（retry + DLQ）；unittest matrix；sandbox regression 不退化

### 1. Changed files

| 檔案 | 變更摘要 |
|------|----------|
| `delivery/notification_webhook_adapter_v1.py` | `TIER_RETRY_DEFAULTS`；`_get_retry_config(tier=)` tier fallback；`_check_tier_retry_readiness`（staging/prod：`max_attempts≥1` + `DLQ_ENABLED=1`）；HMAC 沿用既有 `_check_hmac_tier_policy`（gate 順序：URL → HMAC → retry readiness → POST） |
| `tests/test_notification_webhook_dispatch_v1.py` | 新增 `TestNotificationWebhookStagingProdRetry`（5 cases）；staging tier 既有測試補 DLQ/HMAC env；HMAC tier 測試補 DLQ + header case fix |
| `04_Workflows/tickets/WH-P7-NOTIF-RETRY-prod-impl-v1_state.md` | 本票 STATE / B_REPORT |

### 2. Staging/prod retry 行為

| Tier | env 未設時 default `max_attempts` | backoff default (base / max ms) | Readiness gate |
|------|-----------------------------------|----------------------------------|----------------|
| **sandbox** | `0`（單次 POST） | `100` / `2000` | 無（opt-in retry/DLQ/HMAC） |
| **staging** | `3` | `500` / `8000` | `max_attempts≥1` **且** `DLQ_ENABLED=1`；HMAC 由 `_check_hmac_tier_policy` 在前段強制 |
| **prod** | `5` | `1000` / `30000` | 同 staging |

**Precondition 失敗**：不進 retry loop；`webhook_result.blocked_rule` ∈ {`retry_policy_violation`, `dlq_policy_violation`}；HMAC 未就緒時由 HMAC gate 回 `hmac_disabled` / `hmac_secret_missing` 等。外層 dispatch 仍 **fail-open** `ok=True` · `dispatched=False` · `dry_run=True`。

**最終失敗**：retry 用盡或不可重試 4xx → `_maybe_append_dlq_record` **append 一次**（沿用 DLQ-impl 路徑；retry 中途不寫）。

Env 鍵仍為 `GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS` / `RETRY_BASE_DELAY_MS` / `RETRY_MAX_DELAY_MS`；explicit env 覆寫 tier default。

### 3. 新增/調整測試

| 測試名稱 | 場景 |
|----------|------|
| `test_staging_retry_503_then_200_succeeds_no_dlq` | staging readiness 通過 → 503→200 retry 成功、無 DLQ |
| `test_staging_retry_exhausted_writes_one_dlq_record` | staging persistent 500 → 3 attempts、jsonl 1 行 |
| `test_staging_precondition_dlq_disabled_blocks_retry` | DLQ off → `dlq_policy_violation`、無 POST |
| `test_staging_precondition_hmac_disabled_blocks_retry` | HMAC off → `hmac_disabled`（HMAC gate 先於 retry）、無 POST |
| `test_sandbox_tier_single_post_regression` | sandbox 顯式 tier → 仍單次 POST |

### 4. 驗證

```bash
python -m unittest tests.test_notification_webhook_dispatch_v1 -v
```

**結果**：39/39 OK ✅

### 5. skeleton / placeholder

無。

### 6. 阻塞

無。

### 7. override

無。

---

## C_REPORT

- **review_date**: 2026-06-23
- **reviewer_role**: P7 prod line Reviewer (C)
- **verdict**: **`accepted_with_nits`**
- **conclusion**: staging/prod tier readiness gate（`max_attempts≥1` + `DLQ_ENABLED=1`）與 tier default backoff 已落地；gate 順序 URL → HMAC → retry readiness → POST+retry loop 與 `WH-P7-NOTIF-RETRY-prod-v1` §2.2.4 一致；sandbox 單次 POST regression 不退化；precondition 失敗外層 fail-open `ok=True` · 不進 retry loop。

**一句話（gate 行為）**：staging/prod 須 HMAC gate 通過後再驗 retry+DLQ readiness，任一 precondition 失敗即拒 POST（`blocked_by_tier_retry_policy` + 具體 `blocked_rule`），通過則 tier default retry（staging 3 / prod 5）+ 最終失敗落 DLQ；sandbox 無 mandatory gate。

### impl_consistency_check

| 檢查項 | 設計 / 合約 | 現碼 / 測試 | 結果 |
|--------|-------------|-------------|------|
| Gate 順序 | URL → HMAC → retry readiness → POST | `send_webhook_notification` L1008–1131 | ✅ |
| staging/prod `max_attempts≥1` | `retry_policy_violation` | `_check_tier_retry_readiness` L444–446 | ✅ 行為 |
| staging/prod `DLQ_ENABLED=1` | `dlq_policy_violation` | L448–449 | ✅ |
| HMAC precondition | 設計票列 `hmac_policy_violation`；實作由 HMAC gate 先阻 | `_check_hmac_tier_policy` 在前段 · `hmac_disabled` 等 | ✅（nit：retry 票 AC-4 文案 vs 細粒度 rule） |
| Precondition 失敗 | 不進 retry loop · fail-open dispatch | blocked 路徑無 `_send_http_post_with_retry` | ✅ |
| Tier defaults | staging 3/500/8000 · prod 5/1000/30000 | `TIER_RETRY_DEFAULTS` + `_get_retry_config(tier=)` | ✅ |
| Sandbox regression | 單次 POST · 無 mandatory | `test_sandbox_tier_single_post_regression` | ✅ |
| staging 503→200 | happy path · 無 DLQ | `test_staging_retry_503_then_200_succeeds_no_dlq` | ✅ |
| staging 最終失敗 → DLQ 1 行 | retry 用盡 | `test_staging_retry_exhausted_writes_one_dlq_record` | ✅ |
| precondition DLQ off | `dlq_policy_violation` | `test_staging_precondition_dlq_disabled_blocks_retry` | ✅ |
| precondition HMAC off | HMAC gate 先阻 | `test_staging_precondition_hmac_disabled_blocks_retry` | ✅ |
| AC-2 `max_attempts≤0` reject | 須 unittest | **無** 專用 case | ⚠️ nit |
| 合約 §4.6.3 staging/prod mandatory | doc 仍 `not_implemented_yet` | 本票 Non-goal · 留 doc-sync | ✅ 邊界內 |

### acceptance_criteria_review（AC-1～AC-7）

| AC | 結果 | 備註 |
|----|------|------|
| AC-1 sandbox regression | **pass** | |
| AC-2 attempts≤0 reject | **pass（行為）** · **nit（缺測）** | 邏輯在 `_check_tier_retry_readiness`；建議補 `retry_policy_violation` case |
| AC-3 DLQ off reject | **pass** | |
| AC-4 HMAC 未 ready | **pass** | 經 HMAC gate · rule=`hmac_disabled` |
| AC-5 三 gate 通過 + DLQ | **pass** | |
| AC-6 unittest 全綠 | **pass** | Reviewer 重跑 **39/39 OK** |
| AC-7 不改合約 doc | **pass** | |

### 驗證證據

```bash
python -m unittest tests.test_notification_webhook_dispatch_v1 -v
```

**結果**：39/39 OK ✅

### non-blocking nits

- 缺 staging `RETRY_MAX_ATTEMPTS=0` → `retry_policy_violation` 專測（AC-2 覆蓋缺口）。
- 設計 FRAME `hmac_policy_violation` 與 impl 細粒度 HMAC `blocked_rule` 命名差 — 行為正確（HMAC gate 串行在前）。
- §4.6.3 / §4.6.6.3 合約 `impl_status` 仍 stale — 預期留 `WH-P7-NOTIF-contract-doc-sync-v1`。

---

## D_REPORT

- **scribe_date**: 2026-06-23 · Reviewer 代填（本輪邊界 · 未 append Progress）
- **verdict_echo**: Reviewer **`accepted_with_nits`** — staging/prod tier retry readiness + tier defaults **validated**；`overall_status` → **`validated`**
- **handoff_one_liner**: P7 prod retry impl 已 enforce staging/prod「retry≥1 + DLQ=1」preflight（HMAC 由同 adapter HMAC gate 前置）；sandbox 零 retry 預設不變；合約/doc/CI 升格留 follow-up 票。
- **value_for_p7**: 完成 Wave-P7-2 retry 升格之 **runtime gate** 半環（與 HMAC-prod-impl · DLQ-impl 組合後 staging wave 具備三 mandatory preflight）；仍 **unittest-only** · 不宣稱真 staging/prod 啟用（§4.6.6.4 checklist 未齊）。
- **next_tickets**（建議順序）:

| 順序 | 票號 | 說明 |
|------|------|------|
| 1 | **`WH-P7-NOTIF-contract-doc-sync-v1`**（或子票） | §4.6.3 tier defaults / readiness gate · §4.6.0 / §4.6.6.3 `impl_status` 更新 |
| 2 | **`WH-P7-NOTIF-RETRY-prod-ci-v1`** | sandbox-only CI / doc lint 驗 tier retry gate 與合約一致 |
| 3 | **`WH-P7-NOTIF-staging-integration-v1`** | 人工 env 三 gate 整合 smoke（非 CI prod URL） |
| 4（nit 可選） | impl 票 follow-up 或 RETRY-prod-ci 子 case | 補 `retry_policy_violation` unittest |

- **progress_entry**: 本輪 **未** append `00_Agent_Work_Progress.md`（任務邊界）
