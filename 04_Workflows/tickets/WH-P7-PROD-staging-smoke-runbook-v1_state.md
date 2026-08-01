# WH-P7-PROD-staging-smoke-runbook-v1 — Ticket State

> handoff 摘要檔；P7 **staging tier 手動 smoke runbook** 設計票 · **doc-only**。  
> 目的：定義 staging env 上人工／半自動 smoke 步驟，對齊 `WH-P7-PROD-staging-integration-v1` Phase S1–S4；供 ops / oncall / dev 在真環境演練 emit → dispatch → signed POST → retry → DLQ 閉環。  
> **本票不改 code / tests / docs / workflows / 其他票 / Progress**。

---

## FRAME

### handoff header

**P7 staging tier 手動 smoke runbook 設計票**：sandbox 線已 `validated`；staging integration 設計票（`WH-P7-PROD-staging-integration-v1` · `design_accepted`）已定義 Phase S0–S4 gate 啟用藍圖與 checklist；四子線 impl（DLQ · PROD-URL · RETRY-prod · HMAC-prod）已在 unittest 層 partial 交付。本票作 **Wave-P7-5** follow-up：將 S1–S4 各 phase 的 **人工 env smoke 步驟** 收斂為可執行 runbook 骨架；**不執行**真環境拔線、**不撰寫**腳本或 CI workflow。

**讀者與用途（一句話）**：供 **ops / oncall / dev** 在 staging 專用 deployment（非 CI）依 Phase S1–S4 逐項驗證 URL / HMAC / retry / DLQ gate 行為是否符合 shadow/enforce 設定，並以 go/no-go 判斷是否可進入下一 phase。

---

### 1. Scope

本 runbook 驗證下列能力在 **staging tier · 人工 env** 下的行為（對齊合約 §4.6.3–§4.6.6 · staging integration S0–S4）：

| 驗證域 | smoke 焦點 | 對齊 gate / 票 |
|--------|------------|----------------|
| **URL gate** | `TIER=staging` 時 allowlist **match → POST**、miss / non-https / bare IP → **不 POST**（fail-closed）；外層 dispatch 仍 fail-open | `WH-P7-NOTIF-PROD-URL-impl-v1` · S1 enforce |
| **HMAC shadow / enforce** | shadow：signed POST 送達 sample receiver 且可驗簽；enforce：缺簽名 / 空 secret / 缺 `event_id` → **不 POST** · `blocked_by_hmac_tier_policy` | `WH-P7-NOTIF-HMAC-prod-impl-v1` · S3 |
| **Retry + DLQ** | retry readiness 三 gate 通過後進入 retry loop；**無依賴錯誤**時 retry 成功 → **不寫** DLQ；注入故障（5xx 或不可重試 4xx）→ retry 用盡或單次失敗 → **寫 1 行** staging DLQ jsonl | `WH-P7-NOTIF-RETRY-prod-impl-v1` · `WH-P7-NOTIF-DLQ-impl-v1` · S2 / S4 |
| **觀測性** | log 可區分 `blocked_by_url_tier_policy` / `blocked_by_hmac_tier_policy` / retry readiness `blocked_rule`；inspect CLI 可對 **staging 專用 DLQ path** 跑 `list` / `stats` | `WH-P7-NOTIF-DLQ-inspect-cli-impl-v1` · checklist §B |
| **CI 邊界** | `p7-notification-smoke` **仍 sandbox-only · non-blocking**；本 runbook **禁止**在 CI workflow 設 `TIER=staging/prod` | 合約 §4.5 · §4.6.6 hard rule |

**Non-Goals（本票）**

- ❌ 不撰寫 smoke 腳本、fixture 或 CI job。
- ❌ 不 flip `GOV_NOTIFICATION_WEBHOOK_TIER=staging`（執行留 `WH-P7-NOTIF-staging-integration-execute-v1`）。
- ❌ 不 provision staging env / secret（→ `WH-P7-PROD-staging-env-config-v1`）。
- ❌ 不決定 prod rollout（→ `WH-P7-PROD-prod-rollout-governance-v1`）。
- ❌ 不改 sandbox 行為、不升格 advisory CI 為 required check。

---

### 2. Phases（對應 staging integration S1–S4）

> 每 phase 假設 **S0 前置已完成**（checklist §A–§D 全勾 · Wave-H `governance_dual` 批文 · `WH-P7-PROD-staging-env-config-v1` 交付 staging URL / secret / DLQ path / rollback 包）。  
> **Env 套件**：各 phase 依 env-config §4 **S1-ready / S2-ready / S3-ready** 套件 flip（F0–F5）；不要求逐字對齊 env 值，但概念須一致。  
> **現碼 caveat（S1）**：`TIER=staging` 時 adapter HMAC tier gate **enforce** — happy-path POST **须** `HMAC_ENABLED=1` + 非空 staging secret（env-config §4.2 S1 execute 註：S1 flip 须同步 S2 HMAC secret）；S1 **步驟 2**（allowlist miss）可獨立驗 URL gate block，無須 signed POST。  
> 演練窗口內 on-call 在場；任一異常可一鍵 rollback 至 `TIER=sandbox` 或未設。

| Phase | 主題 | Runbook smoke 步驟（1–2 步敘述） |
|-------|------|----------------------------------|
| **S1 · URL enforce** | tier + allowlist | **步驟 1**：依 env-config **S1 execute**（F0–F2）+ **S2 HMAC secret 子集**（`HMAC_ENABLED=1` + staging secret · 否則 POST 被 HMAC gate 拒）；`TIER=staging` + staging HTTPS URL + allowlist match；emit 一筆 P7 notification → 確認 adapter **POST 成功**（2xx）至 staging endpoint，log 無 URL gate block。**步驟 2**：將 `URL` 改為 allowlist **外** host 或 bare IP 再 emit → 確認 **不 POST** · `dispatched=False` · `blocked_by_url_tier_policy`（或等價 `blocked_rule`）· 外層 dispatch 仍 `ok=True`。 |
| **S2 · DLQ observe** | 失敗可觀測 · fail-open | **步驟 1**：開 `DLQ_ENABLED=1` + staging 專用 `DLQ_PATH`；保持 HMAC / retry 仍 advisory 或最小值；emit 一筆 **預期成功** 的通知 → 確認 **無 DLQ 行**。**步驟 2**：暫時將 staging endpoint 設為不可達或回固定 503（演練注入）→ emit → 確認 retry **尚未 enforce** 時行為符合當前 env（可能單次失敗或最小 retry）；若 DLQ 已 enabled 且最終失敗 → inspect CLI `list` 見 **+1 行** · `tier=staging` · `schema_id=notification_webhook_dlq_v1`；DLQ 寫入失敗時 dispatch 仍 fail-open。 |
| **S3 · HMAC shadow→enforce** | 簽名與驗簽 | **步驟 1（shadow）**：`HMAC_ENABLED=1` + staging secret；receiver sample impl / fixtures 就緒；emit → 確認 POST 含 `X-Gov-Signature-256` · `X-Gov-Timestamp` · `X-Gov-Event-Id`；sample receiver **驗簽通過**；tier HMAC reject **可選延後**（log-only 若 impl 支援）。**步驟 2（enforce 演練）**：切換至 HMAC tier **enforce**（缺簽名 reject POST）；`HMAC_ENABLED=0` 或 secret 空再 emit → 確認 **不 POST** · `blocked_by_hmac_tier_policy`；恢復正確 secret 後 signed POST 再綠。 |
| **S4 · Retry enforce · E2E** | retry + DLQ 閉環 | **步驟 1**：S1–S3 穩定後開 retry tier readiness **enforce**（`max_attempts≥1` · DLQ=1 · HMAC ready）；emit 至 **健康** endpoint → 確認 retry 成功 · **無 DLQ 行**。**步驟 2（E2E 故障注入）**：endpoint 持續 503 直至 retry 用盡 → 確認 `retry_exhausted=true` · DLQ **+1 行** 可稽核；inspect CLI `stats` 反映 staging tier；go/no-go：全 gate enforce 下 happy path + 故障 path 均符合 §4.6.4 觸發表。 |

---

### 3. Operators

| 角色 | 職責 |
|------|------|
| **Ops / Infra** | 依 `WH-P7-PROD-staging-env-config-v1` 注入 staging URL / secret / DLQ path；維護 rollback env 包；演練窗口內監控磁碟與 endpoint 健康 |
| **Oncall** | 執行本 runbook 步驟；故障注入與 rollback 決策；DLQ inspect 與 log 取證 |
| **Dev（P7 線）** | 解讀 `blocked_rule` / adapter 回傳形狀；協助 receiver sample 端點與 HMAC 驗簽；非 runbook 執行者時提供旁站 |

**前置條件（must 完成後方可執行本 runbook）**

- [ ] **`WH-P7-PROD-staging-env-config-v1`** — staging 專用 URL · HMAC secret · DLQ path · retry env 模板 · 一鍵 rollback 包（對齊 staging integration checklist §A）
- [ ] **`WH-P7-PROD-staging-integration-v1`** checklist §A–§D 全勾 · Wave-H **`governance_dual`** 批文
- [ ] **Receiver 鏈（S3 前置）** — `WH-P7-NOTIF-HMAC-receiver-fixtures-v1` · `WH-P7-NOTIF-HMAC-receiver-sample-impl-v1` 至少可驗簽一筆 signed POST
- [ ] **Impl 收口（建議）** — `WH-P7-NOTIF-RETRY-prod-impl-v1` · `WH-P7-NOTIF-HMAC-prod-impl-v1` Reviewer C 收口（unittest 骨架已 landing）
- [ ] **觀測（建議）** — `WH-P7-PROD-staging-metrics-v1` 或等價 log 聚合就緒（非 blocking runbook 設計）

**執行環境約束**

- 僅 **staging 專用 deployment slot** 或 **人工 env**（非 CI · 非 default dev sandbox）
- CI / `p7-notification-smoke` **must not** 設 `TIER=staging` 或 `prod`
- 演練結束 **must** 可 rollback：`TIER` unset 或 `sandbox` · `DLQ_ENABLED=0` · `HMAC_ENABLED=0`

---

### 4. 最小 smoke path（staging · 單次演練摘要）

在 staging env（checklist 與 env-config 就緒）依 **當前 phase 對應 env-config §4 S1/S2/S3-ready 套件**（`TIER=staging` 僅 S1 execute 起）執行：

1. **Emit** — 人工或既有 CLI／腳本發一筆 P7 notification（含 `event_id` · `event_type` · case context）；記錄 `event_id` 供後續對照。
2. **Dispatch → adapter** — 確認 adapter 讀取 staging `URL`；URL gate 放行後 POST 至 staging endpoint；HMAC 行為符合當前 **shadow 或 enforce** 設定（signed headers 或預期 block）。
3. **Retry 觀察** — 健康 endpoint：確認 `dispatched=True` · 無 DLQ 行；故障注入：觀察 retry 次數與 backoff；**無依賴錯誤且最終成功** → **不寫** DLQ；**retry 用盡或不可重試 4xx** → **寫 1 行** DLQ。
4. **DLQ inspect** — 對 staging 專用 path 執行 inspect CLI `list`（`--tier staging` · `--event-id <id>`）與 `stats`；確認 `tier=staging` · 無 secret 原文 · 與 adapter `webhook_result` 一致。
5. **Go/no-go** — 當 phase 步驟全綠 → 記錄證據（log 摘要 · inspect JSON · 時間戳）→ 裁決進入下一 phase 或 rollback。

---

### AllowedPaths / BlockedPaths

| Allowed | Blocked |
|---------|---------|
| `04_Workflows/tickets/WH-P7-PROD-staging-smoke-runbook-v1_state.md` | 其餘全 repo |

---

### Dependencies（只讀索引）

| 票號 / 文件 | 角色 |
|-------------|------|
| `WH-P7-PROD-staging-integration-v1` | S0–S4 藍圖 · checklist · follow-up 索引 SSOT |
| `WH-P7-PROD-staging-env-config-v1` | staging env 前置 · rollback 包 |
| `WH-P7-PROD-phase1-wrapup-v1` | prod phase-1 現況 · 缺口索引 |
| `WH-P7-NOTIF-DLQ-impl-v1` · `*-inspect-cli-*` | DLQ 落盤 · inspect CLI |
| `WH-P7-NOTIF-PROD-URL-impl-v1` | URL tier gate |
| `WH-P7-NOTIF-RETRY-prod-v1` / `*-impl-v1` | retry tier readiness |
| `WH-P7-NOTIF-HMAC-prod-mandatory-v1` / `*-impl-v1` | HMAC tier mandatory |
| `WH-P7-NOTIF-HMAC-receiver-fixtures-v1` · `*-sample-impl-v1` | S3 驗簽前置 |
| `docs/outbox-and-feedback-layer-contract-v1.md` §4.6.3–§4.6.6 | 合約 SSOT |

---

## STATE

- **overall_status**: `validated`
- **current_owner**: scribe
- **next_action**: 可選 `WH-P7-PROD-staging-metrics-v1` · prod rollout governance
- **last_updated**: 2026-06-24 · P7 staging execution agent（execute 證據回填）
- **wave**: Wave-P7-5 · P7 staging tier · manual smoke runbook · design
- **status_by_role**:
  - **Orchestrator (A)**: done — FRAME skeleton + S1–S4 smoke 步驟 + 最小 path
  - **Implementer (B)**: done — 2026-06-23 · B_REPORT 可執行正文（S1–S4 逐步 · env-config mapping · rollback）
  - **Reviewer (C)**: done — 2026-06-24 execute 後 **validated**
  - **Scribe (D)**: done — 2026-06-23 · handoff execute 票
- **notes**:
  - runbook 正文 human-runnable · **execute `20260623T165252Z` S1–S4 全綠**
  - runner: `tools/p7_staging_integration_execute_v1.py`

---

## B_REPORT (Implementer · 可執行 runbook 正文 · 2026-06-23)

> **性質**：人工 env 演練 SSOT；**非** CI job。**前置**：`WH-P7-PROD-staging-env-config-v1` S1/S2/S3-ready 套件 · integration checklist §A–§D · Wave-H `governance_dual` 批文。

### 0. 演練前自檢（must）

| # | 項 | 通過標準 |
|---|-----|----------|
| 0.1 | env-config provision | staging HTTPS URL · HMAC secret slot · DLQ path 已配置（**禁止** secret 入庫） |
| 0.2 | Rollback 包就緒 | 一鍵：`TIER` unset 或 `sandbox` · `DLQ_ENABLED=0` · `HMAC_ENABLED=0` · `WEBHOOK_ENABLED=0` |
| 0.3 | on-call 在場 | 演練窗口內可立即 rollback |
| 0.4 | unittest 回歸（可選本地） | `python -m unittest tests.test_notification_webhook_dispatch_v1 -v` → OK |

### 1. Env 套件 ↔ integration Phase mapping（env-config §4）

| Phase | env-config 套件 | 關鍵 env（概念） | integration |
|-------|-------------------|------------------|-------------|
| **S1** | S1-ready + S2 HMAC secret 子集 | `TIER=staging` · `URL` + `URL_ALLOWLIST` match · `HMAC_ENABLED=1` + secret | S1 URL enforce |
| **S2** | S2-ready | + `DLQ_ENABLED=1` · staging 專用 `DLQ_PATH` | S2 DLQ observe |
| **S3** | S3-ready | HMAC enforce（缺簽名 reject POST） | S3 shadow→enforce |
| **S4** | S4-ready | + retry tier readiness enforce · `RETRY_MAX_ATTEMPTS≥1` | S4 retry + DLQ E2E |

> **現碼 caveat**：`TIER=staging` 時 adapter HMAC tier gate **enforce** — S1 happy-path **须** 同步 `HMAC_ENABLED=1` + 非空 secret（見 env-config §4.2 S1 execute）。

### 2. Phase S1 · URL enforce

**Flip env（依 env-config S1 execute · F0–F2 + HMAC secret 子集）**

| Env 鍵 | 建議值（類型 · 非 secret 原文） |
|--------|----------------------------------|
| `GOV_NOTIFICATION_WEBHOOK_TIER` | `staging` |
| `GOV_NOTIFICATION_WEBHOOK_URL` | staging HTTPS endpoint（allowlist 內） |
| `GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST` | 含上述 host/path |
| `GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED` | `1` |
| `GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET` | staging 專用 secret（env 注入） |

**步驟 1 · allowlist match → POST 成功**

1. 記錄演練開始時間 · on-call 確認 rollback 包可用。
2. 以既有 P7 emit 路徑發一筆 notification（含 `event_id`）— 例：multi-phase smoke 的 gate+notify 步或等價 orchestrator emit（**勿**在 CI workflow 設 staging tier）。
3. 確認 adapter log：**無** `blocked_by_url_tier_policy` · **POST 2xx** 至 staging endpoint。
4. 若使用 signed POST：確認 headers 含 `X-Gov-Signature-256` · `X-Gov-Timestamp` · `X-Gov-Event-Id`。

**步驟 2 · allowlist miss → 不 POST**

1. 將 `GOV_NOTIFICATION_WEBHOOK_URL` 改為 allowlist **外** host 或 bare IP（**勿** commit secret/URL 原文至 repo）。
2. 再 emit 一筆。
3. 預期：`dispatched=False` · `dry_run=True` · `blocked_by_url_tier_policy`（或等價 `blocked_rule`）· 外層 dispatch 仍 `ok=True`。
4. **Go**：步驟 1–2 符合 → 記錄 log 摘要 · 進入 S2；否則 **rollback** 至 sandbox 等價 env。

### 3. Phase S2 · DLQ observe

**Flip env（S2-ready · + DLQ）**

| Env 鍵 | 建議值 |
|--------|--------|
| `GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED` | `1` |
| `GOV_NOTIFICATION_WEBHOOK_DLQ_PATH` | staging 專用 jsonl（與 sandbox/prod 分軌） |
| `GOV_NOTIFICATION_WEBHOOK_DLQ_TIER` | `staging` |

**步驟 1 · happy path 無 DLQ 行**

1. emit 至 **健康** staging endpoint。
2. 預期：POST 成功 · **無** 新 DLQ jsonl 行。

**步驟 2 · 故障注入 → DLQ +1 行**

1. 暫時將 endpoint 設為不可達或固定 503（演練注入 · 演練結束還原）。
2. emit · 觀察 retry 行為（依當前 retry env）。
3. 若最終失敗：inspect CLI — `python tools/inspect_notification_dlq_v1.py list --tier staging --json`（或 `--dlq-path <staging_path>`）。
4. 預期：+1 行 · `schema_id=notification_webhook_dlq_v1` · `tier=staging` · 無 secret 原文。

**Rollback 觸發**：DLQ 磁碟不可寫且 dispatch 被阻斷（**不應**發生 · fail-open）→ 停演練 · rollback · 開 incident follow-up。

### 4. Phase S3 · HMAC shadow→enforce

**前置（硬）**：`WH-P7-NOTIF-HMAC-receiver-fixtures-v1` · `sample-impl-v1` 至少可驗簽一筆 signed POST（若未就緒 → S3 enforce **延後** · 僅 shadow/log 比對）。

**步驟 1 · shadow（signed POST + receiver 驗簽）**

1. 確認 `HMAC_ENABLED=1` + staging secret。
2. emit → 確認 POST headers 完整 · sample receiver **驗簽通過**。

**步驟 2 · enforce（缺簽名 reject）**

1. 暫設 `HMAC_ENABLED=0` 或清空 secret（演練用 · 立即還原）。
2. emit → 預期：**不 POST** · `blocked_by_hmac_tier_policy` · `dispatched=False`。
3. 還原 secret · 再 emit → signed POST 恢復綠。

### 5. Phase S4 · Retry enforce · E2E

**Flip env（S4-ready · retry readiness enforce）**

| Env 鍵 | 建議值 |
|--------|--------|
| `GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS` | `≥1`（staging 建議 `3`） |
| DLQ + HMAC | 維持 S2/S3 就緒狀態 |

**步驟 1 · 健康 endpoint · 無 DLQ**

1. emit → retry 成功 · **無** 新 DLQ 行。

**步驟 2 · 503 至 retry 用盡 → DLQ 1 行**

1. 注入持續 503。
2. 預期：`retry_exhausted=true`（或等價 log）· DLQ +1 行。
3. `python tools/inspect_notification_dlq_v1.py stats --tier staging --json` 反映 staging tier。

**Go/no-go**：S1–S4 全綠 → 記錄證據（log 摘要 · inspect JSON · UTC 時間戳）→ 可進入 staging wave 完成宣告（**仍非** prod-ready）。

### 6. Rollback（任一 phase 異常）

1. 執行 env-config §2.2 rollback 包（`TIER` unset/sandbox · DLQ/HMAC off · `WEBHOOK_ENABLED=0` 若需 kill-switch）。
2. 確認行為回到 sandbox 封箱等價（localhost-only · opt-in partial）。
3. 記錄 rollback 時間 · 原因 · 未解決 gap → execute 票 follow-up。

### 7. 驗證（本票 doc · 未執行真 env）

- 本輪 Implementer 僅落盤正文；**未** flip `TIER=staging` · **未** 真 env 拔線。
- 本地回歸（可選）：`python -m unittest tests.test_notification_webhook_dispatch_v1 -v` → **39/39 OK**（2026-06-23 代理重跑）。

---

## C_REPORT

- **review_date**: 2026-06-23
- **reviewer_role**: P7 staging smoke runbook Reviewer (C)
- **verdict**: **`accepted_with_gaps`**
- **conclusion**: S1–S4 runbook 正文（B_REPORT §0–§6）已 human-runnable；覆蓋 URL gate · HMAC co-ready · retry/DLQ · rollback。**doc ready · 真 env 演練仍 pending execute 票**。
- **scope**: FRAME S1–S4

**一句話總結（core）**：為 ops / oncall / dev 提供 staging 人工 env 上 S1–S4 的手動 smoke 指南，覆蓋 URL / HMAC / retry / DLQ gate 的 shadow / enforce 行為與 go/no-go 判斷，作 Wave-P7-5 staging 演練 runbook 設計 SSOT；**不執行**真 env 拔線、**不含** prod rollout。

**審查摘要**

| 檢查項 | 結果 |
|--------|------|
| S1 URL enforce vs PROD-URL-impl / env-config | ✅ allowlist match → POST、miss / non-https / bare IP → 不 POST · `blocked_by_url_tier_policy` · 外層 fail-open — 與 integration S1 · §4.6.6.2 一致；**FRAME 已補** env-config S1 execute 須同步 HMAC secret（現碼 `TIER=staging` HMAC enforce） |
| S2 DLQ observe vs DLQ-impl / integration | ✅ `DLQ_ENABLED=1` + staging 分軌 path · happy path 無 DLQ 行 · 故障注入 +1 行 · fail-open 寫入 — 對齊 §4.6.4 觸發表 · integration S2 |
| S3 HMAC shadow→enforce vs HMAC-prod-impl / integration | ✅ shadow：signed POST + receiver 驗簽；enforce：缺簽名 / secret / event_id → `blocked_by_hmac_tier_policy` · 不 POST — 與 integration S3 · §4.6.5.1 tier 語意相容 |
| S4 Retry enforce · E2E vs RETRY-prod-impl / integration | ✅ 三 gate enforce · 健康 endpoint 無 DLQ · 503 至 retry 用盡 → DLQ 1 行 · inspect `stats` — 對齊 integration S4 · §4.6.3 |
| 最小 smoke path vs env-config 套件 | ✅ emit → dispatch → retry 觀察 → DLQ inspect → go/no-go；**已引用** env-config §4 S1/S2/S3-ready 概念套件 |
| CI 邊界 | ✅ sandbox-only · 禁止 CI `TIER=staging/prod` — 與 §4.5 · §4.6.6 hard rule 一致 |
| Blocking | 無 |

**最明確 gap（非 blocking）**

- **真 env execute** — 須 checklist 全勾 + governance_dual 後 **`WH-P7-NOTIF-staging-integration-execute-v1`**。
- **HMAC receiver fixtures + sample impl** — S3 enforce 演練前置仍 `not_implemented_yet`。

---

## D_REPORT

- **handoff_date**: 2026-06-23
- **from**: P7 **staging smoke runbook 設計**（`design_accepted` · Reviewer C `accepted_with_gaps`）
- **to**: Orchestrator / Ops（execute 派工 · Implementer 可選正文擴寫）

**Execution 入口票（2026-06-23 已建檔）**

| 票 id | 狀態 | 與本 runbook 關係 |
|-------|------|-------------------|
| **`WH-P7-PROD-staging-env-bootstrap-v1`** | `frame_ready` | S0 provision · execute 前置 |
| **`WH-P7-NOTIF-HMAC-receiver-fixtures-impl-v1`** | `frame_ready` | S3 enforce 硬依賴 |
| **`WH-P7-NOTIF-staging-integration-execute-v1`** | `frame_ready` | **依本 runbook S1–S4** 真 env 演練 + 證據回填 |
| **`WH-P7-PROD-prod-rollout-governance-bootstrap-v1`** | `design_accepted` | prod 收口（doc-only · 可並行） |

**建議派工順序**：bootstrap → receiver-impl → **execute（consume 本 runbook）**。

**可選**：`WH-P7-PROD-staging-metrics-v1` — S1–S4 觀測聚合（checklist §B · 非 blocking）

**handoff 一句話**：staging smoke runbook 設計 SSOT 已就緒；**勿**在 governance 批文與 env-config provision 完成前 flip `TIER=staging`；execute 票按本 runbook S1–S4 逐 phase 演練並留證據。

**Progress**：本輪未 append `00_Agent_Work_Progress.md`（任務邊界禁止改 Progress）；Scribe 可另輪 append。
