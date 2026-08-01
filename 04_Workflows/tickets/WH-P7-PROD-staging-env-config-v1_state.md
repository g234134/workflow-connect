# WH-P7-PROD-staging-env-config-v1 — Ticket State

> handoff 摘要檔；P7 **staging tier env / rollout config** 設計票 · **doc-only**。  
> 目的：為 Infra / Ops 提供自洽的 staging 專用 env、secret、資源與 rollback 一鍵包 SSOT；對齊 `WH-P7-PROD-staging-integration-v1` checklist §A 與 Phase S0–S4 藍圖。  
> **本票不改 code / tests / docs / workflows / 其他票 / Progress**。

---

## FRAME

### handoff header

**P7 staging tier env / config 設計票（Infra / Ops 面向）**：上游 `WH-P7-PROD-staging-integration-v1` 已 `design_accepted`，定義 Phase S0–S4 rollout 與 shadow vs enforce 裁決。本票將 checklist §A 具體化為 **env matrix、secret 注入位、資源分軌、一鍵 flip / rollback 包**，並整理 **S1-ready / S2-ready / S3-ready 最小 config 套件**，供 `WH-P7-NOTIF-staging-integration-execute-v1` 與 `WH-P7-PROD-staging-smoke-runbook-v1` 直接照表開 env。**不 provision 真機、不 flip 真 env**（execute 票 + governance_dual 後）。

**狀態依據**：adapter tier gate 已在 unittest 驗證（`WH-P7-NOTIF-PROD-URL-impl-v1` · `WH-P7-NOTIF-HMAC-prod-impl-v1` · `WH-P7-NOTIF-RETRY-prod-impl-v1` · `WH-P7-NOTIF-DLQ-impl-v1` 均 `validated`）；真 staging env **仍關閉**（合約 §4.6.6.4 · §4.6.6.3 `approval_required=governance_dual`）。

---

### Background

| 面向 | 現況 | 本票填補 |
|------|------|----------|
| **Rollout 藍圖** | Phase S0–S4 · shadow vs enforce 表已落盤 | 每 phase 對應 **具體 env 值 / flip 順序** |
| **Adapter env 鍵** | 合約 §4.6.0 / §4.6.6 env 表 + impl 已讀取 | staging **建議值** · 分軌 path · allowlist grammar 範例 |
| **Secret 管理** | HMAC secret env-only · 禁止入庫 | staging 專用 secret slot · 與 sandbox/prod **分軌** · rotation placeholder |
| **DLQ 分軌** | default `outbox/notification_dlq/events.jsonl` | staging 專用 `…/staging/events.jsonl` · inspect CLI 可讀 |
| **CI 邊界** | §4.5 / §4.6.6：**禁止** CI `TIER=staging/prod` | 本票 env **僅** 人工 deployment slot / staging 專用 process env |

**一句話**：程式 gate 骨架與 unittest 已就緒；缺 **staging 專用 env 模板、flip 關鍵鍵、rollback 包、S1–S3 readiness checklist** — 本票補此 SSOT。

---

### Goal

1. **Env matrix**：列出 staging wave 所需 env / secret / 檔案資源（名稱、tier 適用、建議值、flip 時機）。
2. **Rollout controls**：標示一鍵 flip 關鍵 env 與 **rollback 至 sandbox 行為** 的最小 env 集合。
3. **安全 / 隔離**：staging URL 必 non-production receiver；HMAC secret 不可 reuse prod；rotation 策略 placeholder。
4. **最小 staging config 套件**：S1-ready / S2-ready / S3-ready 三階 checklist（execute 票開 env 用）。
5. **Non-goals**：不含 prod rollout；不含 receiver 端內部 env。

---

### 1. Env matrix

> **符號**：`*` = secret（env 注入 · **禁止入庫**）；`(repo-relative)` = 相對戰車根路徑；具體 secret 注入機制見 `INSTANCE_ANCHOR_TANG` 類型（本票不寫本機絕對路徑）。

#### 1.1 Core tier & URL（S1 起用 · URL gate enforce）

| Env 鍵 | Staging 建議值 | Default（未設） | 用途 | Flip 時機 |
|--------|----------------|-----------------|------|-----------|
| `GOV_NOTIFICATION_WEBHOOK_TIER` | `staging` | `sandbox` | tier 分支；staging 啟用 https + allowlist + mandatory gate 鏈 | **S1 execute**（governance_dual + checklist §A 後） |
| `GOV_NOTIFICATION_WEBHOOK_URL` | `https://<staging-receiver-host>/…` * | *(empty → dry-run)* | POST 目標；**must** 為 non-production internal / mock staging endpoint | S1 provision；S1 execute 生效 |
| `GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST` | `<staging-receiver-host>` 或 `host/path-prefix` grammar（§4.6.6.2） | *(unset → staging 拒 POST)* | URL tier gate match；**must** 涵蓋 `URL` host | S1 provision（與 URL 同步） |
| `GOV_NOTIFICATION_WEBHOOK_ENABLED` | `1` | off | master switch；`0` = 全線 dry-run / 不 POST | S1 execute 或 rollback kill-switch |
| `GOV_NOTIFICATION_WEBHOOK_TIMEOUT` | `10`–`30`（秒） | `10` | HTTP timeout | S1（可沿用 default） |

**Allowlist 範例（grammar only · 非真實域名）**：

```text
GOV_NOTIFICATION_WEBHOOK_URL=https://notify-staging.internal.example/webhooks/gov
GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST=notify-staging.internal.example/webhooks/gov
```

**硬規則**：staging `URL` host **must** ∈ allowlist；**must not** 指向客戶 production hostname（§4.6.6.2 negative example）。

#### 1.2 HMAC sender（S2 shadow · S3 enforce）

| Env 鍵 | Staging 建議值 | Default | 用途 | Flip 時機 |
|--------|----------------|---------|------|-----------|
| `GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED` | `1` | `0` | sender 簽名 master gate | **S2-ready** 起 `1`（shadow 簽名 POST） |
| `GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET` | *staging-dedicated secret* | *(empty)* | HMAC-SHA256 signing key；**與 sandbox/prod 分軌** | S2 provision secret slot |
| `GOV_NOTIFICATION_WEBHOOK_HMAC_HEADER` | *(optional · 沿用 sender default)* | adapter default | 簽名 header 名 | 通常不改 |
| `GOV_NOTIFICATION_WEBHOOK_TIMESTAMP_HEADER` | *(optional)* | adapter default | timestamp header | 通常不改 |
| `GOV_NOTIFICATION_WEBHOOK_EVENT_ID_HEADER` | *(optional)* | adapter default | event id header | 通常不改 |

**Runtime 語意（現碼 · 2026-06-23）**：`TIER=staging` 時 HMAC tier gate **enforce** — `HMAC_ENABLED≠1` 或 secret 空 → **拒 POST**（`blocked_by_hmac_tier_policy`）。故 **S1-ready 不可** 在 `TIER=staging` 下期望 unsigned POST；S1 運行態應 **維持 `TIER=sandbox`（或未設）** 直至 S2 HMAC secret 就緒，或 S1 僅做 **config slot provision**（env 模板已填、process 尚未 reload）。

**S2 shadow 定義（本票）**：`TIER=staging` + HMAC on + signed POST 至 **sample / internal staging receiver**；receiver 驗簽結果 **僅觀測**（log / metrics），**不** 作為 dispatch 決策輸入（adapter 無 log-only reject 分支 — shadow = 簽名已發、人工比對 receiver log）。

#### 1.3 DLQ（S2-ready 起用 · S3 綁 mandatory）

| Env 鍵 | Staging 建議值 | Default | 用途 | Flip 時機 |
|--------|----------------|---------|------|-----------|
| `GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED` | `1` | `0` | 最終失敗 append jsonl | **S2-ready** 起 `1`（advisory 觀察寫入量） |
| `GOV_NOTIFICATION_WEBHOOK_DLQ_PATH` | `outbox/notification_dlq/staging/events.jsonl` `(repo-relative)` | `outbox/notification_dlq/events.jsonl` | append-only DLQ stream；**與 sandbox/prod 分軌** | S2 provision 目錄 + 寫入權 |
| `GOV_NOTIFICATION_WEBHOOK_DLQ_TIER` | `staging` | *(empty → record 內 `sandbox`)* | DLQ record `tier` 欄位 | S2 建議顯式 `staging` |

**資源**：Infra **must** 確保 `outbox/notification_dlq/staging/` 目錄存在、process 可 append；與 sandbox default path **不得** 共用同一 jsonl 檔。

#### 1.4 Retry（S3-ready 觀察 · S4 enforce）

| Env 鍵 | Staging 建議值 | Default（tier fallback） | 用途 | Flip 時機 |
|--------|----------------|--------------------------|------|-----------|
| `GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS` | `3`（或 explicit `≥1`） | staging tier fallback `3` | retry 次數；staging **mandatory ≥1** | **S4 execute** enforce 閉環 |
| `GOV_NOTIFICATION_WEBHOOK_RETRY_BASE_DELAY_MS` | `500` | staging fallback `500` | 指數退避起點 | S4（可沿用 tier default） |
| `GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_DELAY_MS` | `8000` | staging fallback `8000` | 退避上限 | S4（可沿用 tier default） |

**Tier readiness（現碼）**：`TIER=staging` 且進入 POST 路徑時 **must** `DLQ_ENABLED=1` 且 `max_attempts≥1` 且 HMAC gate 通過；S3-ready 可維持 `max_attempts=0` **僅當** 尚未進 S4 — 但 `TIER=staging` + HMAC/DLQ on 時 retry readiness 會在 POST 前檢查，**S4 前若需避免 retry loop** 可暫設 `max_attempts=1` 做最小演練（對齊 integration 票 S4 advisory）。

#### 1.5 資源 / secret 摘要表

| 資源類型 | Staging 專用 | 分軌要求 |
|----------|--------------|----------|
| Webhook receiver URL | `https://<non-prod-staging-host>/…` | **must not** = prod / 客戶 production host |
| HMAC secret | `GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET` slot | **must not** reuse sandbox 演練 secret 或 prod secret |
| DLQ jsonl path | `outbox/notification_dlq/staging/events.jsonl` | **must not** 與 sandbox / prod jsonl 共用 |
| Allowlist 條目 | 僅 staging receiver host / path-prefix | prod registry 條目 **不在** staging wave scope |
| Deployment slot | 人工 env / staging-only process | CI / default dev **仍 sandbox** |

---

### 2. Rollout controls

#### 2.1 一鍵 flip 關鍵 env（forward）

| 優先序 | Env 鍵 | Flip 值 | 效果 | 對應 integration Phase |
|--------|--------|---------|------|--------------------------|
| **F0 · master arm** | `GOV_NOTIFICATION_WEBHOOK_ENABLED` | `1` | 允許真 POST（非 dry-run） | S1 execute 前 |
| **F1 · tier declare** | `GOV_NOTIFICATION_WEBHOOK_TIER` | `staging` | 啟用 staging URL + mandatory gate 鏈 | S1 |
| **F2 · URL bind** | `GOV_NOTIFICATION_WEBHOOK_URL` + `URL_ALLOWLIST` | staging receiver | URL gate enforce | S1 |
| **F3 · DLQ observe** | `GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED` | `1` + staging `DLQ_PATH` | 失敗可落 staging DLQ | S2 |
| **F4 · HMAC sign** | `HMAC_ENABLED=1` + `HMAC_SECRET` * | 非空 secret | signed POST；tier HMAC enforce | S2–S3 |
| **F5 · retry enforce** | `RETRY_MAX_ATTEMPTS` | `≥1`（建議 `3`） | retry loop + DLQ 閉環 | S4 |

> **說明**：repo **無** 單一 `STAGING_GATES_ENABLED` 鍵；rollout 以 **`TIER` + 各 gate master env** 組合達成。若未來 adapter 新增 shadow-mode flag，本票可 append 一列 — **現階段以 F0–F5 為 SSOT**。

#### 2.2 Rollback 包（回到 sandbox 等價行為）

**目標**：任一 staging 演練異常時，**≤1 分鐘** 內恢復與 sandbox 封箱一致之外部可觀測行為（localhost-only · opt-in retry/HMAC/DLQ · 無 staging POST）。

| 步驟 | Env 設定 | 效果 |
|------|----------|------|
| **R1 · tier 回退** | `GOV_NOTIFICATION_WEBHOOK_TIER=sandbox`（或 **unset**） | 跳過 staging mandatory gate 鏈 |
| **R2 · master disarm（可選）** | `GOV_NOTIFICATION_WEBHOOK_ENABLED=0` | 立即停止一切 POST |
| **R3 · gate 全 off** | `HMAC_ENABLED=0` · `DLQ_ENABLED=0` · `RETRY_MAX_ATTEMPTS=0`（或 unset） | 與 sandbox default 對齊 |
| **R4 · URL 回退** | `GOV_NOTIFICATION_WEBHOOK_URL` → localhost 或 empty | §4.4 sandbox localhost gate |
| **R5 · allowlist 清** | `URL_ALLOWLIST` unset | sandbox tier ignore allowlist |

**最快 kill-switch**：僅設 `GOV_NOTIFICATION_WEBHOOK_ENABLED=0`（R2）即可立即停止一切 POST，無須等待 R3–R5 逐項清 env；完整 sandbox 等價仍建議跑完 R1–R5。

**一鍵 rollback 最小集（建議 Infra 模板）**：

```text
GOV_NOTIFICATION_WEBHOOK_TIER=sandbox
GOV_NOTIFICATION_WEBHOOK_ENABLED=0
GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED=0
GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED=0
GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS=0
# unset or clear: GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST, GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET
GOV_NOTIFICATION_WEBHOOK_URL=
GOV_NOTIFICATION_WEBHOOK_DLQ_PATH=outbox/notification_dlq/events.jsonl
```

**驗收**：rollback 後跑 sandbox smoke（`p7-notification-smoke` 語意 · localhost）行為與 `WH-P7-sandbox-line-wrapup-v1` 封箱一致；**無 orphan staging POST**（checklist C-1）。

#### 2.3 Flip 前置 hard stop

- [ ] Wave-H **governance_dual** 批文留痕（§4.6.6.3 `approval_required`）
- [ ] Checklist §A–§D（`WH-P7-PROD-staging-integration-v1`）mandatory 項已勾
- [ ] **禁止** 在 CI workflow env 設 `TIER=staging|prod`（§4.5 · §4.6.6 hard rule）

---

### 3. 安全 / 隔離要求

| # | 要求 | 驗收方式 |
|---|------|----------|
| **SEC-1** | Staging `GOV_NOTIFICATION_WEBHOOK_URL` **must** 指向 **non-production** receiver（internal mock · 客戶 **staging** tier endpoint · 非 prod hostname） | allowlist + 人工 URL 審查；對照 §4.6.6.2 negative example |
| **SEC-2** | Staging `HMAC_SECRET` **must not** reuse prod secret 或 sandbox 共用演練 secret | secret store 分 slot；rotation 表獨立列 |
| **SEC-3** | Secret **禁止入庫** — 僅 env / secret manager 注入 | repo 無 `.env` commit；糧草驗證 `[OK]`/`[FAILED]` only |
| **SEC-4** | DLQ jsonl **must** 與 prod 分軌；operator inspect 需 RBAC（read-only） | path = `…/staging/events.jsonl`；inspect CLI 僅 staging operator role |
| **SEC-5** | Log / DLQ record **must not** 含 `HMAC_SECRET` 原文 | 對照 adapter blocked log 語意 |
| **SEC-6** | Staging 演練 **must not** 寫入 prod DLQ 或 prod receiver | SEC-1 + DLQ path 分軌 |

#### HMAC secret rotation 策略（placeholder · Infra runbook 待補）

| 階段 | 動作 | 備註 |
|------|------|------|
| **Initial provision** | 生成 staging-only secret → 注入 `GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET` slot | 與 prod 不同 key material |
| **Planned rotation** | 雙 secret 窗口：receiver 接受 `current` + `next`（receiver 端配置 — **非本票**）→ flip sender secret → 廢止 old | 詳細步驟 → `WH-P7-PROD-staging-smoke-runbook-v1` |
| **Emergency revoke** | R1–R3 rollback + 作廢 secret + 重新 provision | 先 disarm POST 再 rotation |

---

### 4. 最小 staging config 套件（S1 / S2 / S3-ready）

> **用途**：execute 票 / smoke-runbook **照表開 env**；與 integration 票 Phase S0–S4 **對齊但粒度為 config readiness**。

#### 4.1 一句話定義

**最小 staging config 套件** = 在 **不觸 prod** 前提下，按 **S1 → S2 → S3** 三階逐步 provision **URL/allowlist → HMAC+DLQ 分軌 → mandatory gate enforce 就緒**，每階可獨立驗收且具 **一鍵 rollback** 至 sandbox。

#### 4.2 S1-ready（config provision · shadow · 無 mandatory POST）

**目標**：staging 專用 URL / allowlist **已登記**；runtime **仍 sandbox 等價**（或 master disarm），為 S1 execute 備妥模板。

| 項 | 要求 | Env / 資源 |
|----|------|------------|
| S1-1 | Staging receiver URL 已確認（non-prod HTTPS） | `URL` template 已填 · **process 可仍 `ENABLED=0`** |
| S1-2 | Allowlist 條目已寫入 secret store / env template | `URL_ALLOWLIST` provisioned |
| S1-3 | `TIER` **尚未** flip `staging` **或** flip 前 `ENABLED=0` | 避免誤 POST |
| S1-4 | HMAC / DLQ / retry gate env **全 off** | `HMAC_ENABLED=0` · `DLQ_ENABLED=0` · `max_attempts=0` |
| S1-5 | Rollback 包 R1–R5 已文件化並 dry-run | checklist A-6 |
| S1-6 | governance_dual **未** 批准前 **must not** F1 flip | integration S0 |

**S1 execute（integration Phase S1）追加 flip**：F0 + F1 + F2 → `TIER=staging` + URL enforce；此時 **must** 同步準備 S2 HMAC secret（否則 HMAC gate 拒 POST）。

**Integration 對照**：`WH-P7-PROD-staging-integration-v1` Phase S1「URL enforce」在此 SSOT 解讀為 **F1+F2 gate 就緒**（tier + allowlist armed）；因 `TIER=staging` 時 HMAC tier gate **enforce**（§1.2），首個成功 staging POST 須 **S2 HMAC secret 同步就緒**，非 unsigned POST 演練。

#### 4.3 S2-ready（HMAC shadow + DLQ 分軌 · advisory observe）

**目標**：signed POST 可達 staging receiver；DLQ 寫入 staging path；**retry enforce 尚未**（S4）。

| 項 | 要求 | Env / 資源 |
|----|------|------------|
| S2-1 | S1 execute 已完成（URL gate enforce） | F0–F2 已 flip |
| S2-2 | Staging HMAC secret 已注入 | `HMAC_ENABLED=1` + `HMAC_SECRET` * |
| S2-3 | DLQ 導向 staging 分軌 path | `DLQ_ENABLED=1` · `DLQ_PATH=…/staging/events.jsonl` · `DLQ_TIER=staging` |
| S2-4 | HMAC **shadow** 觀測 | signed POST 成功；receiver / log 人工比對 signature · **不** 依賴 adapter log-only 模式 |
| S2-5 | Retry **advisory** | `max_attempts=0` 或 unset（tier fallback 在 POST 路徑會衝突 — **實務 S2 建議 `max_attempts=1` 最小演練但標 advisory**）或暫不注入失敗劇本 |
| S2-6 | inspect CLI 可讀 staging DLQ | `list` / `stats` on staging path |
| S2-7 | Receiver fixtures / sample impl **recommended**（integration E-5） | S3 enforce 前置 |

**對齊 integration Phase**：S2（DLQ observe）+ S3 前半（HMAC shadow）。

#### 4.4 S3-ready（mandatory gate enforce 就緒 · 待 S4 retry 閉環）

**目標**：允許 enforce staging tier 全 mandatory preflight（HMAC + DLQ + URL）；receiver contract test 綠；可進入 retry 閉環演練。

| 項 | 要求 | Env / 資源 |
|----|------|------------|
| S3-1 | S2-ready 全勾 | — |
| S3-2 | HMAC tier gate **enforce** 已確認 | 缺簽名 / secret → `blocked_by_hmac_tier_policy` · 不 POST |
| S3-3 | DLQ **enforce 綁定** retry mandatory 前置 | `DLQ_ENABLED=1` 穩定 · 0 誤寫確認 |
| S3-4 | Receiver fixtures + sample impl **contract test 全綠** | integration S3 go 條件 |
| S3-5 | Retry env 模板就緒（**S4 才 flip F5**） | `max_attempts=3` · backoff `500`/`8000` 已寫 template |
| S3-6 | 48h 穩定觀測（integration S4 前置） | metrics / log 聚合 — `WH-P7-PROD-staging-metrics-v1` |
| S3-7 | Rollback 演練通過 | checklist C-1 |

**S4 execute 追加 flip**：F5 → `RETRY_MAX_ATTEMPTS≥1`；注入失敗 → retry 用盡 → DLQ 1 行（integration Phase S4）。

#### 4.5 套件對照表（quick reference）

| 套件 | TIER | URL/allowlist | HMAC | DLQ path | Retry | POST 語意 |
|------|------|---------------|------|----------|-------|-----------|
| **S1-ready** | sandbox 或 disarm | provisioned | off | off / default | off | 無 staging POST |
| **S1 execute** | staging | enforce | **must on for POST** | off | off | URL gate only · HMAC 未就緒則 blocked |
| **S2-ready** | staging | enforce | on · shadow 觀測 | staging 分軌 · on | advisory (`1` 最小) | signed POST + DLQ observe |
| **S3-ready** | staging | enforce | enforce | enforce bind | template ready | 全 preflight enforce · S4 開 retry 閉環 |
| **Rollback** | sandbox | localhost/empty | off | off | off | sandbox 封箱等價 |

---

### 5. Non-Goals

- ❌ **不設計 prod rollout** — prod env 模板 · 批文 · required CI → `WH-P7-PROD-prod-rollout-governance-v1` · Wave-P7-6。
- ❌ **不定義 receiver 端內部 env** — 驗簽 secret、雙 secret 窗口、idempotency store → receiver team domain（§4.6.5.2）。
- ❌ **不 provision 真機 / 不 flip 真 env** — 本票 doc-only；execute → `WH-P7-NOTIF-staging-integration-execute-v1`。
- ❌ **不改** Python / tests / CI / docs / workflows / 其他票 / Progress。
- ❌ **不新增** adapter env 鍵（若需 `STAGING_GATES_MODE` 類 shadow flag → 另開 impl 票）。
- ❌ **不宣稱** staging = prod-ready 或 production-ready。

---

### 6. Acceptance Criteria（本票 FRAME）

- **AC-1**：FRAME 含 Env matrix（≥ tier / URL / HMAC / DLQ / retry）· Rollout controls · 安全 / 隔離 · S1–S3 套件 · Non-goals。
- **AC-2**：與 `WH-P7-PROD-staging-integration-v1` Phase S0–S4 · checklist §A **無矛盾**。
- **AC-3**：Rollback 包可讓 staging 回到 sandbox 等價行為（§2.2）。
- **AC-4**：HMAC secret / DLQ path / URL **分軌**要求明確。
- **AC-5**：AllowedPaths 僅本票；Implementer 接棒後 `STATE.overall_status` = `frame_ready`。

---

### 7. AllowedPaths / BlockedPaths

| Allowed | Blocked |
|---------|---------|
| `04_Workflows/tickets/WH-P7-PROD-staging-env-config-v1_state.md` | 其餘全 repo |

---

### 8. Dependencies（只讀索引）

| 票號 / 文件 | 角色 |
|-------------|------|
| `WH-P7-PROD-staging-integration-v1` | staging rollout 設計 SSOT · `design_accepted` |
| `WH-P7-PROD-phase1-wrapup-v1` | prod phase-1 現況 |
| `WH-P7-NOTIF-PROD-URL-impl-v1` | URL / tier gate · `validated` |
| `WH-P7-NOTIF-HMAC-prod-impl-v1` | HMAC tier gate · `validated` |
| `WH-P7-NOTIF-RETRY-prod-impl-v1` | retry readiness · `validated` |
| `WH-P7-NOTIF-DLQ-impl-v1` | DLQ append · `validated` |
| `docs/outbox-and-feedback-layer-contract-v1.md` §4.6.3–§4.6.6 | 合約 env / tier matrix |
| `WH-P7-PROD-staging-smoke-runbook-v1`（待開） | E2E flip 步驟 consume 本票 |
| `WH-P7-NOTIF-staging-integration-execute-v1`（待開） | 真 env 拔線 consume 本票 |

---

## STATE

- **overall_status**: `validated`
- **current_owner**: scribe
- **next_action**: Wave-P7-6 prod rollout governance（可並行）· staging metrics 可選 follow-up
- **last_updated**: 2026-06-24 · P7 staging execution agent（execute 證據回填）
- **wave**: Wave-P7-5 · P7 staging tier · env / rollout config design
- **status_by_role**:
  - **Orchestrator (A)**: done — FRAME 落盤 · follow-up 票索引見 D_REPORT
  - **Implementer (B)**: done — FRAME env matrix / S1–S3 套件 / rollback 包
  - **Reviewer (C)**: done — 2026-06-23 · **`accepted_with_gaps`** → 2026-06-24 execute 後 **validated**
  - **Scribe (D)**: pending — Progress append
- **notes**:
  - env matrix SSOT 已就緒 · **bootstrap + execute 已完成首輪 local staging smoke**
  - execute run `20260623T165252Z` · go_no_go=true

---

## B_REPORT

> Implementer (B) · 2026-06-23 · doc-only · env matrix / S1–S3 套件 / rollback 包 SSOT

### §1 交付摘要

| 區塊 | 內容 |
|------|------|
| Env matrix | §1.1–§1.5 tier/URL/HMAC/DLQ/retry 鍵 + staging 建議值 |
| Rollout controls | F0–F5 flip 序 · §2.2 rollback R1–R5 + kill-switch `ENABLED=0` |
| 安全 / 隔離 | SEC-1–SEC-6 · HMAC/DLQ/URL 分軌 |
| S1–S3 套件 | §4.2–§4.4 readiness checklist |

### §2 與 impl 票 cross-ref

| impl 票 | 角色 |
|---------|------|
| `WH-P7-NOTIF-PROD-URL-impl-v1` | URL/tier gate · **validated** |
| `WH-P7-NOTIF-HMAC-prod-impl-v1` | HMAC tier enforce · **validated** |
| `WH-P7-NOTIF-RETRY-prod-impl-v1` | retry readiness · **validated** |
| `WH-P7-NOTIF-DLQ-impl-v1` | DLQ append · **validated** |

### §3 誠實邊界

- **本 runbook/doc 就緒** · **未** provision 真 staging env（bootstrap / execute 票）
- **未** flip `TIER=staging` 直至 governance_dual + checklist §A–§D

### §4 驗證

無 runtime（doc-only）。

---

## C_REPORT

- **review_date**: 2026-06-23
- **reviewer_role**: P7 staging env config Reviewer (C)
- **verdict**: **`accepted_with_gaps`**
- **conclusion**: env matrix / S1–S3 套件 / rollback SSOT 就緒；與 smoke-runbook · integration checklist **一致**。**doc ready · 真 env 演練仍 pending** bootstrap / execute 票。
- **scope**: FRAME env matrix · rollout/rollback · 安全隔離 · S1–S3 套件 vs `WH-P7-PROD-staging-integration-v1` · `WH-P7-PROD-phase1-wrapup-v1` · 四子線 impl STATE · 合約 §4.6.3–§4.6.6 · adapter env 鍵（本輪未重跑 unittest）

**一句話總結（core）**：定義 staging tier 的最小 env 套件（tier/URL/allowlist → HMAC+DLQ 分軌 → retry 模板）與一鍵 rollback 開關，確保 URL/HMAC/Retry/DLQ 可在 **不觸 prod** 下按 S1→S2→S3 分階 provision 與 flip。

**審查摘要**

| 檢查項 | 結果 |
|--------|------|
| Env 鍵名 vs 合約 §4.6.0 / §4.6.3–§4.6.6 / adapter | ✅ `TIER` · `URL` · `URL_ALLOWLIST` · `HMAC_ENABLED` · `HMAC_SECRET` · `DLQ_*` · `RETRY_*` · `ENABLED` · `TIMEOUT` 均一致且 impl 已讀取 |
| 四子線 impl 狀態 | ✅ PROD-URL / HMAC-prod / RETRY-prod / DLQ impl 均 **`validated`**（unittest only · 非真 env 啟用） |
| phase1 wrap-up「不觸 prod / 一鍵 rollback」 | ✅ Non-goals 排除 prod rollout；§2.2 R1–R5 + kill-switch `ENABLED=0` 對齊 sandbox 封箱 |
| staging integration Phase S0–S4 順序 | ✅ F0–F5 flip 序 URL→DLQ→HMAC→retry 與 integration S1→S2→S3→S4 相容；S2-ready 對照 integration S2+S3 前半已明示 |
| S1–S3 config 套件 vs integration scope | ✅ S1-ready 維持 sandbox 等價；S1 execute 補 integration S1/HMAC co-ready 對照（§4.2 微調） |
| CI 邊界 | ✅ 本票 env 僅人工 deployment slot；禁止 CI `TIER=staging/prod` |
| Blocking | 無 |

**最明確 gap（非 blocking 設計 SSOT）**

- **HMAC receiver fixtures + sample impl** 仍 `not_implemented_yet` — S3-ready enforce 須延後至 receiver contract test 全綠。
- **真 env provision / flip** 本票 doc-only — Infra 側創建 secret slot / DLQ 目錄 / process env 留 **bootstrap 或 execute 票**。
- **Integration S1「dry-run POST 成功」** 與 runtime `TIER=staging` HMAC enforce 需 execute runbook 以「URL gate armed + HMAC co-ready」操作化（FRAME §4.2 已對照）。

---

## D_REPORT

- **handoff_date**: 2026-06-23
- **from**: P7 **staging env config 設計**（`design_accepted` · Reviewer C `accepted_with_gaps`）
- **to**: Orchestrator（Infra provision + staging wave execute）

**Execution 入口票（2026-06-23 已建檔 · FRAME）**

| 票 id | 狀態 | 角色 |
|-------|------|------|
| **`WH-P7-PROD-staging-env-bootstrap-v1`** | `frame_ready` | Infra provision URL/secret/DLQ/rollback · **不 flip tier** |
| **`WH-P7-NOTIF-HMAC-receiver-fixtures-impl-v1`** | `frame_ready` | receiver fixture + 驗簽 + contract tests（S3 硬依賴） |
| **`WH-P7-NOTIF-staging-integration-execute-v1`** | `frame_ready` | 真 env S1–S4 首輪演練 + Progress |
| **`WH-P7-PROD-prod-rollout-governance-bootstrap-v1`** | `design_accepted` | Wave-P7-6 prod rollout FRAME（doc-only · 可並行） |

**建議派工順序**：bootstrap → receiver-impl → execute；prod-rollout-governance 可並行。

**S3 硬依賴**：`WH-P7-NOTIF-HMAC-receiver-fixtures-impl-v1`（合併原 fixtures + sample-impl 最小 scope）。

**handoff 一句話**：staging env config SSOT 已就緒；下一批從 **env-bootstrap + smoke-runbook** 開工，勿在 receiver fixtures 與 governance 批文未完成前 flip `TIER=staging`。

**Progress**：本輪未 append `00_Agent_Work_Progress.md`（任務邊界禁止改 Progress）；Scribe 可另輪 append。
