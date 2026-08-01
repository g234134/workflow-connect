# WH-P7-PROD-RETRY-HMAC-microplan-v1 — Ticket State

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Wave-H+1 · **P7 prod 線 RETRY + HMAC impl 小計畫票（doc-only · micro-plan）**  
> 上游：`WH-P7-NOTIF-RETRY-prod-v1`（`design_accepted`）· `WH-P7-NOTIF-RETRY-prod-impl-v1`（`frame_ready`）· `WH-P7-NOTIF-HMAC-prod-mandatory-v1`（`frame_ready`）· `WH-P7-NOTIF-HMAC-prod-impl-v1`（`frame_ready`）· `WH-P7-PROD-roadmap-v1`（Wave-P7-2 / Wave-P7-3）  
> 產物：兩張 impl 票的 **可打勾實作步驟 + 驗收指標**；供 Orchestrator 派工 Implementer 時逐項勾選。**零 code / 零 test / 零 CI / 零合約 doc 變更（本輪）**

---

## FRAME

### handoff header

**P7 prod 線 RETRY + HMAC impl micro-plan 票**：針對 `WH-P7-NOTIF-RETRY-prod-impl-v1` 與 `WH-P7-NOTIF-HMAC-prod-impl-v1` 兩張 **frame_ready** 實作票，本票彙總設計票 SSOT（`RETRY-prod-v1` · `HMAC-prod-mandatory-v1`）與合約 §4.6.3 / §4.6.5 / §4.6.6 對 adapter 現碼（`notification_webhook_adapter_v1` retry / HMAC 段）的 **落地 checklist**。Implementer 依本票 §A / §B 逐項實作與驗收；**不改 sandbox 行為、不一次推到 prod rollout**。

---

### 1. 子目標摘要（per impl 票）

#### 1.1 `WH-P7-NOTIF-RETRY-prod-impl-v1`

1. **Tier readiness gate**：`TIER ∈ {staging, prod}` 時，第一次 HTTP POST 前驗證 `max_attempts ≥ 1`、`DLQ_ENABLED=1`、HMAC ready；缺一 → reject POST + `blocked_rule`。
2. **Tier default retry policy**：env 未設時 staging/prod 套用設計票建議 default（staging `3` / `500`/`8000` ms；prod `5` / `1000`/`30000` ms）；sandbox 仍 default `0`。
3. **Retry ↔ DLQ 整合**：三 gate 通過後進入既有 retry loop；最終失敗（retry 用盡或不可重試 4xx）經 `WH-P7-NOTIF-DLQ-impl-v1` 路徑 append jsonl；retry 中途不寫 DLQ。
4. **Blocked 語意對齊**：gate 拒絕仍 dispatch **fail-open** `ok=True` · `dispatched=False` · `dry_run=True`（對齊 PROD-URL-impl blocked 路徑）。
5. **Unittest matrix**：sandbox regression 全綠 + staging/prod gate reject/accept + retry→DLQ 場景。

#### 1.2 `WH-P7-NOTIF-HMAC-prod-impl-v1`

1. **Tier HMAC gate**：`TIER ∈ {staging, prod}` 且 URL gate 通過後，驗證 HMAC_ENABLED + secret + event_id + 簽名可計算；任一失敗 → **不 POST**。
2. **Fail-closed vs sandbox fail-open**：staging/prod 缺簽名/空 secret/簽名失敗 **reject POST**；sandbox 維持 opt-in · fail-open unsigned。
3. **`blocked_by_hmac_tier_policy` 訊號**：回傳 `blocked_reason` + `blocked_rule`（`hmac_disabled` / `hmac_secret_missing` / `hmac_event_id_missing` / `hmac_signing_failed`）。
4. **Gate 順序**：env master → URL tier gate → **HMAC tier gate（本票）** → tier readiness / retry loop；URL gate 先於 HMAC（regression）。
5. **Unittest matrix**：≥6 scenario（sandbox regression 2 + staging/prod mandatory 5+）；signed POST 含 §4.6.5.1 headers。

---

### 2. Non-Goals（本 micro-plan · 兩票共用邊界）

- ❌ **不改** sandbox 行為 — default 單次 POST · opt-in retry · DLQ default off · HMAC fail-open unsigned **維持不變**。
- ❌ **不啟用** 真實 staging/prod 環境；僅 unittest 驗 gate 行為（§4.6.6.4 enablement checklist 未完成前禁止 rollout）。
- ❌ **不一次推到 prod rollout** — Wave-P7-5 staging 整合 · Wave-P7-6 prod 批文留後續 wave。
- ❌ **不修改** 合約 doc（§4.6.3 / §4.6.5 / §4.6.6 擴寫 → `WH-P7-NOTIF-contract-doc-sync-v1`）。
- ❌ **不實作** receiver fixtures / sample impl · DLQ inspect CLI · prod registry gate。
- ❌ **不升格** advisory CI 為 required check（→ `WH-P7-NOTIF-RETRY-prod-ci-v1` · `WH-P7-NOTIF-HMAC-prod-ci-v1`）。

---

### 3. Gate 順序與協作（Implementer 裁決參考）

```
env master switch (WEBHOOK_ENABLED)
  → case allowlist
  → URL tier gate (PROD-URL-impl · 不改邏輯)
  → HMAC tier gate (HMAC-prod-impl-v1 · staging/prod only)
  → tier readiness gate (RETRY-prod-impl-v1 · retry + DLQ + HMAC ready 複核)
  → HTTP POST + retry loop
  → 最終失敗 → DLQ append (DLQ-impl-v1 · fail-open)
```

**裁決**：HMAC gate 與 retry readiness **may** 合併為單一 `tier_preflight()`；staging/prod 語意 **must not** 弱於兩張設計票 FRAME。

---

### A. `WH-P7-NOTIF-RETRY-prod-impl-v1` — Implementer checklist

> 每項可獨立打勾；完成後在 B_REPORT 逐項引用 unittest 或 assert 證據。

#### A.1 Adapter · tier readiness gate

- [ ] **A.1.1** 新增 `_check_tier_retry_readiness()`（或等價 preflight）：僅在 `TIER ∈ {staging, prod}` 執行；sandbox（或未設 `TIER`）**跳過**。
- [ ] **A.1.2** staging/prod · `max_attempts ≤ 0`（含 env 未設且 tier default 未生效）→ reject POST · `blocked_rule=retry_policy_violation` · `blocked_reason` 對齊 URL gate 慣例（如 `blocked_by_retry_tier_policy` 或設計票 `blocked_by_url_tier_policy` 同族命名 — Implementer 與 Reviewer 對照 RETRY-prod-v1 §2.2.4 定稿一個）。
- [ ] **A.1.3** staging/prod · `DLQ_ENABLED ≠ 1` → reject POST · `blocked_rule=dlq_policy_violation`。
- [ ] **A.1.4** staging/prod · HMAC 未 ready（`HMAC_ENABLED`  off / secret 空 / 缺 `event_id`）→ reject POST · `blocked_rule=hmac_policy_violation`（或 defer 至 HMAC-prod-impl 票若 gate 合併 — **must** 仍有可測 assert）。
- [ ] **A.1.5** Gate 拒絕路徑：外層 `ok=True` · `dispatched=False` · `dry_run=True` · 含 `blocked_reason` / `blocked_rule` / `tier`（對齊 `_check_url_tier_policy` blocked 形狀）。

#### A.2 Adapter · tier default retry policy

- [ ] **A.2.1** 擴充 `_get_retry_config()`（或 tier-aware wrapper）：`TIER=staging` 且 env `RETRY_MAX_ATTEMPTS` 未設 → default **`max_attempts=3`** · `base_delay_ms=500` · `max_delay_ms=8000`。
- [ ] **A.2.2** `TIER=prod` 且 env 未設 → default **`max_attempts=5`** · `base_delay_ms=1000` · `max_delay_ms=30000`。
- [ ] **A.2.3** `TIER=sandbox` → 維持現行 default **`max_attempts=0`** · `100`/`2000` ms（**不改** `_get_retry_config` sandbox 路徑行為）。
- [ ] **A.2.4** env 顯式設定 **override** tier default（staging/prod 設 `RETRY_MAX_ATTEMPTS=2` 仍須 `≥1` 才通過 readiness gate）。

#### A.3 Adapter · retry loop 與 DLQ（沿用 DLQ-impl-v1）

- [ ] **A.3.1** 三 gate 通過後才呼叫 `_send_http_post_with_retry()`；**不改** `_is_retriable_http_result` · backoff 公式。
- [ ] **A.3.2** retry 用盡（`retry_exhausted=true`）→ `_maybe_append_dlq_record()` 寫入 1 行 jsonl（需 `DLQ_ENABLED=1` — readiness gate 已保證）。
- [ ] **A.3.3** 不可重試 4xx（如 400）單次失敗 → 同樣觸發 DLQ append（§4.6.4 觸發表）。
- [ ] **A.3.4** retry 中途（尚未用盡）→ **不寫** DLQ。
- [ ] **A.3.5** 2xx 成功 → **不寫** DLQ。

#### A.4 Tests · `tests/test_notification_webhook_dispatch_v1.py`

- [ ] **A.4.1** **sandbox regression**：default env · 單次 POST · `attempt_count=1` · 無 tier readiness 拒絕。
- [ ] **A.4.2** **sandbox regression**：opt-in `RETRY_MAX_ATTEMPTS≥1` + mock 5xx → retry 行為與改動前一致。
- [ ] **A.4.3** **staging · reject**：`TIER=staging` · allowlist OK · `max_attempts=0` → 不 POST · `blocked_rule=retry_policy_violation`。
- [ ] **A.4.4** **staging · reject**：`TIER=staging` · `DLQ_ENABLED=0` → 不 POST · `blocked_rule=dlq_policy_violation`。
- [ ] **A.4.5** **staging · accept + retry success**：三 gate 通過 · mock 首次 503 第二次 200 → `dispatched=True` · `attempt_count≥2` · 無 DLQ 行。
- [ ] **A.4.6** **staging · accept + retry exhausted → DLQ**：三 gate 通過 · mock 全 503 · `retry_exhausted=true` → DLQ jsonl **+1 行** · `schema_id=notification_webhook_dlq_v1`。
- [ ] **A.4.7** **prod · tier default**：env 未設 retry 鍵 · `TIER=prod` · gate 通過 → 實際 `max_attempts` 為 **5**（可從 `webhook_result.attempt_count` 上限或 mock call 次數 assert）。

#### A.5 驗收命令與 AC 對照

- [ ] **A.5.1** `python -m unittest tests.test_notification_webhook_dispatch_v1 -v` **全綠**。
- [ ] **A.5.2** 對照 impl 票 AC-1～AC-7（sandbox regression · 三種 reject · retry+DLQ · 不改 docs）。

**驗收指標（Reviewer 用）**

| 指標 | 通過條件 |
|------|----------|
| Sandbox 零退化 | A.4.1–A.4.2 綠 · 現有 sandbox CI job 不受 staging/prod env 污染 |
| Staging/prod mandatory retry | `max_attempts≥1` enforce · tier default 生效 |
| DLQ 觸發正確 | 僅最終失敗寫入 · 與 §4.6.4 表一致 |
| Fail-open dispatch | gate 拒絕 / HTTP 失敗均 `ok=True` |

---

### B. `WH-P7-NOTIF-HMAC-prod-impl-v1` — Implementer checklist

> 每項可獨立打勾；完成後在 B_REPORT 逐項引用 unittest 或 assert 證據。

#### B.1 Adapter · tier HMAC gate

- [ ] **B.1.1** 新增 `_check_tier_hmac_readiness()`（或等價）：僅 `TIER ∈ {staging, prod}`；URL gate 通過後、第一次 POST 前執行；sandbox **跳過**。
- [ ] **B.1.2** `HMAC_ENABLED` 未設 / `0` / 非 truthy → reject POST · `blocked_rule=hmac_disabled` · `blocked_reason=blocked_by_hmac_tier_policy`。
- [ ] **B.1.3** `HMAC_ENABLED=1` 但 `HMAC_SECRET` 空（trim 後）→ reject POST · `blocked_rule=hmac_secret_missing`。
- [ ] **B.1.4** payload 無 `event_id` 或空字串 → reject POST · `blocked_rule=hmac_event_id_missing`。
- [ ] **B.1.5** 簽名計算拋錯或 headers 不完整 → reject POST · `blocked_rule=hmac_signing_failed`（staging/prod **不得** fallback unsigned — 與 sandbox `_apply_hmac_headers` fail-open **分支分離**）。
- [ ] **B.1.6** 全部通過 → POST **must** 含 `X-Gov-Signature-256` · `X-Gov-Timestamp` · `X-Gov-Event-Id`（§4.6.5.1）。
- [ ] **B.1.7** Blocked 回傳：`ok=True` · `dispatched=False` · `dry_run=True` · log **不含** secret 原文。

#### B.2 Adapter · 與既有 HMAC sender 整合

- [ ] **B.2.1** **不改** `_build_hmac_signed_message` · signed string 格式 · env 鍵名。
- [ ] **B.2.2** staging/prod gate 通過後沿用 `_apply_hmac_headers` 或等價簽名路徑；gate 失敗時 **不進入** `_send_http_post`。
- [ ] **B.2.3** Retry 每次 POST：**may** 刷新 timestamp + 重算 signature；**must** 沿用同一 `event_id` + canonical body（§4.6.5.1 · 與 RETRY-prod-impl 協作 regression）。

#### B.3 Adapter · gate 順序

- [ ] **B.3.1** URL gate（`_check_url_tier_policy`）**先於** HMAC gate；allowlist missing 時 HMAC gate **不執行**（scenario 6 regression）。
- [ ] **B.3.2** HMAC gate **先於** retry readiness / HTTP POST（與 §3 順序一致）。

#### B.4 Tests · `tests/test_notification_webhook_dispatch_v1.py`

- [ ] **B.4.1** **sandbox · HMAC off**：unsigned POST 仍成功（regression · 對照現碼 `_should_apply_hmac_signature` false）。
- [ ] **B.4.2** **sandbox · HMAC on · secret 空**：fail-open unsigned POST 仍 `dispatched=True`（regression）。
- [ ] **B.4.3** **staging · HMAC off**：allowlist OK · 不 POST · `blocked_rule=hmac_disabled` · `blocked_reason=blocked_by_hmac_tier_policy`。
- [ ] **B.4.4** **staging · HMAC on · secret 空**：不 POST · `blocked_rule=hmac_secret_missing`。
- [ ] **B.4.5** **staging · HMAC ready · allowlist OK**：signed POST · mock 200 · headers 含 signature + timestamp + event_id。
- [ ] **B.4.6** **prod · HMAC ready · allowlist missing**：URL gate 先阻 · `blocked_rule=url_allowlist_missing`（或等價）· **無** HMAC POST。
- [ ] **B.4.7** **staging · payload 無 `event_id`**：不 POST · `blocked_rule=hmac_event_id_missing`。

#### B.5 驗收命令與 AC 對照

- [ ] **B.5.1** `python -m unittest tests.test_notification_webhook_dispatch_v1 -v` **全綠**（含新增 `TestNotificationWebhookTierHmacPolicy` 或等價 class）。
- [ ] **B.5.2** 對照 impl 票 AC-1～AC-8（mandatory reject · sandbox skip · signed POST · gate 順序 · 不改 docs）。

**驗收指標（Reviewer 用）**

| 指標 | 通過條件 |
|------|----------|
| Sandbox fail-open 不變 | B.4.1–B.4.2 綠 |
| Staging/prod fail-closed | 缺 HMAC / secret / event_id / 簽名失敗均不 POST |
| 訊號完整 | `blocked_by_hmac_tier_policy` + 正確 `blocked_rule` 枚舉 |
| Gate 順序 | URL 先於 HMAC（B.4.6） |
| 簽名 headers | 成功路徑含 §4.6.5.1 三 headers |

---

### 4. 建議派工順序（Orchestrator）

| 順序 | 票號 | 說明 |
|------|------|------|
| **1（可並行）** | `WH-P7-NOTIF-HMAC-prod-impl-v1` | HMAC gate 較獨立；先 landing 可解 RETRY readiness 中 HMAC 檢查依賴 |
| **1（可並行）** | `WH-P7-NOTIF-RETRY-prod-impl-v1` | tier readiness + retry default + DLQ；與 HMAC gate 合併 preflight 時需協調 touch 同一 adapter 檔 |
| **2** | `WH-P7-NOTIF-contract-doc-sync-v1`（子票） | §4.6.3 tier retry · §4.6.5.1 tier HMAC gate · §4.6.6.3 enforce 脚注 |
| **3** | `WH-P7-NOTIF-RETRY-prod-ci-v1` · `WH-P7-NOTIF-HMAC-prod-ci-v1` | sandbox-only CI matrix（optional · 非 blocking impl） |

> **合併策略**：若同一 Implementer 連續施工，**建議單 PR** 合併 adapter preflight + 兩邊 unittest，避免 gate 順序衝突；Reviewer 對照本票 §3 + §A + §B 全勾。

---

### 5. AllowedPaths / BlockedPaths

#### AllowedPaths

- `04_Workflows/tickets/WH-P7-PROD-RETRY-HMAC-microplan-v1_state.md`（本票 STATE / FRAME / B/C/D_REPORT）

#### BlockedPaths

- `delivery/**` · `tests/**` · `docs/**` · `.github/workflows/**`
- 其他票檔 · `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `.cursor/rules/**`
- `.env` · secrets · 客戶實際 webhook URL
- `04_Workflows/00_Agent_Work_Progress.md`

---

### 6. Dependencies

- `WH-P7-NOTIF-RETRY-prod-v1`（`design_accepted`）
- `WH-P7-NOTIF-RETRY-prod-impl-v1`（`frame_ready`）
- `WH-P7-NOTIF-HMAC-prod-mandatory-v1`（`frame_ready`）
- `WH-P7-NOTIF-HMAC-prod-impl-v1`（`frame_ready`）
- `WH-P7-NOTIF-DLQ-impl-v1` · `WH-P7-NOTIF-PROD-URL-impl-v1` · `WH-P7-NOTIF-HMAC-impl-v1`
- `WH-P7-PROD-roadmap-v1`（Wave-P7-2 · Wave-P7-3）
- `docs/outbox-and-feedback-layer-contract-v1.md` §4.6.3 · §4.6.5 · §4.6.6（只讀）
- `delivery/notification_webhook_adapter_v1.py`（只讀 · retry / HMAC 段）

---

## STATE

- **overall_status**: `done_with_gaps`
- **current_owner**: scribe
- **next_action**: prod CI 升格 · 真 env 演練留 staging execute 票
- **last_updated**: 2026-06-23 · progress agent (§A/§B checklist 已由 impl 票 landing)
- **wave**: Wave-H+1 · P7 prod line · RETRY + HMAC impl micro-plan
- **status_by_role**:
  - **Orchestrator (A)**: done — micro-plan FRAME 落盤
  - **Implementer (B)**: done — `RETRY-prod-impl-v1` · `HMAC-prod-impl-v1` 均 **validated**
  - **Reviewer (C)**: done — 2026-06-23 · **`accepted_with_gaps`**（checklist 證據見 impl B/C_REPORT）
  - **Scribe (D)**: done — 2026-06-23

---

## B_REPORT

- **status**: micro-plan SSOT · impl 落地由 `WH-P7-NOTIF-RETRY-prod-impl-v1` · `WH-P7-NOTIF-HMAC-prod-impl-v1` 承接（均 **validated**）
- **verification_echo**: `python -m unittest tests.test_notification_webhook_dispatch_v1 -v` → **39/39 OK**（含 tier readiness + HMAC mandatory gate scenarios）
- **notes**: §A / §B checklist 逐項證據見各 impl 票 B_REPORT；本票 **doc-only 索引**

---

## C_REPORT

- **review_date**: 2026-06-23
- **verdict**: **`accepted_with_gaps`**
- **conclusion**: gate 順序 · fail-open dispatch 外層語意與 impl 現碼一致；sandbox regression 不退化。
- **gaps**: 真 env enforce · CI 升格仍 deferred。

---

## D_REPORT

- **handoff_date**: 2026-06-23
- **to**: staging integration execute wave
