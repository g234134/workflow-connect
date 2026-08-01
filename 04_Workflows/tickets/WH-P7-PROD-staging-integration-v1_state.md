# WH-P7-PROD-staging-integration-v1 — Ticket State

> handoff 摘要檔；P7 **staging tier integration** 設計票 · **doc-only**。  
> 目的：定義「何時 / 如何」在 staging tier 真正啟用 retry / HMAC / URL / DLQ gate；sandbox 線已 validated、prod phase-1 wrap-up 已建立，四子線 impl + unittest 已交付但真 staging 環境仍關閉。  
> **本票不改 code / tests / docs / workflows / 其他票 / Progress**。

---

## FRAME

### handoff header

**P7 staging tier integration 設計票**：sandbox 線已 `validated`（`WH-P7-sandbox-line-wrapup-v1`）；prod phase-1 已收斂 DLQ 落盤 + inspect CLI、PROD-URL minimal gate、RETRY-prod / HMAC-prod tier gate 設計與 impl skeleton（含 unittest）；合約 §4.6.3–§4.6.6 已標 **partial** 且 §4.6.6.4 明確「真 staging/prod 不建議啟用」。本票作 **Wave-P7-5** 入口 SSOT：定義 staging rollout 步驟、gate 啟用順序（enforce vs shadow/advisory）、前置 checklist 與 follow-up 票索引；**不執行**真環境拔線、**不決定** prod rollout（→ 獨立 governance 票）。

---

### Background

| 面向 | 現況 | 證據 |
|------|------|------|
| **Sandbox 線** | emit → dispatch → localhost webhook → opt-in retry/HMAC/DLQ；advisory CI；**已封箱** | `WH-P7-sandbox-line-wrapup-v1` · `validated` |
| **Prod phase-1 wrap-up** | 四子線 partial 交付已索引；staging integration 列為刻意保留缺口 | `WH-P7-PROD-phase1-wrapup-v1` · `frame_ready` |
| **DLQ** | env-gated 落盤 + inspect CLI；default off · fail-open | `WH-P7-NOTIF-DLQ-impl-v1` · `validated` |
| **PROD-URL** | `TIER` + `URL_ALLOWLIST` minimal gate；staging/prod **僅 unittest** | `WH-P7-NOTIF-PROD-URL-impl-v1` · `validated` |
| **RETRY-prod** | tier readiness gate 設計 + 第一輪 impl（unittest only）；C 待收口 | `WH-P7-NOTIF-RETRY-prod-v1` · `design_accepted` · `*-impl-v1` · **`implementer_done_pending_review`** |
| **HMAC-prod** | tier mandatory gate 設計 + 第一輪 impl（unittest only）；C 待收口 | `WH-P7-NOTIF-HMAC-prod-mandatory-v1` · `frame_ready` · `*-impl-v1` · **`implementer_done_pending_review`** |
| **Receiver 側** | §4.6.5.2 contract SSOT 已落盤；fixtures / sample impl **not_implemented_yet** | `WH-P7-NOTIF-HMAC-receiver-contract-v1` |
| **真 staging 環境** | **關閉** — adapter gate 僅 unit test 生效；CI **禁止** `TIER=staging/prod`（§4.5 · §4.6.6） | 合約 §4.6.6.3 runtime 現況聲明 · Progress 2026-06-23 PROD-URL 收口 |

**一句話（現況）**：程式層已具備 staging/prod tier gate 骨架與 unittest 證據，但 **policy mandatory 欄位（HMAC/retry/DLQ reject）尚未在真 staging env 拔線**；缺 staging 專用 config、人工 E2E runbook、governance 雙人批准與 receiver 演練端點。

---

### Goal

**一句話 Goal**：定義 staging tier 從「unittest-only partial」到「真 env 可控啟用」的 **rollout 步驟、gate 順序與 go/no-go 條件** — 明確哪些 gate **先 enforce**、哪些 **先 shadow/advisory 再升格**，以及何時可宣告 staging wave 完成（仍 **不含** prod rollout）。

具體交付（本票 FRAME）：

1. **Staging integration checklist**（可打勾）— env/config、觀測性、風險管控、協調四域。
2. **Gate 啟用藍圖** — 對照 retry / HMAC / URL / DLQ 四子線，分 **Phase S0–S4** 敘述何時 flip `GOV_NOTIFICATION_WEBHOOK_TIER=staging` 及各 env 鍵。
3. **Shadow vs enforce 裁決表** — 每 gate 在 staging wave 的過渡模式與升格條件。
4. **Follow-up 票索引** — 將 checklist 項映射至可派工 impl/runbook 票（至少 env-config · smoke-runbook · metrics）。
5. **Hard stop 條件** — 未滿足 §4.6.6.4 或 governance 批文前 **must not** 啟用 staging tier。

---

### Staging gate 啟用藍圖（Phase S0–S4）

> **原則**：sandbox 行為 **零變更**；staging 僅在 **人工 env**（非 CI prod URL）演練；外層 dispatch 維持 fail-open；任一 gate 異常須可 **一鍵回退** 至 `TIER=sandbox` 或未設。

| Phase | 主題 | 啟用 gate / 模式 | Go 條件（摘要） |
|-------|------|------------------|-----------------|
| **S0 · 前置** | config + 批文 + receiver 端點 | **無 gate flip** — 仍 `TIER=sandbox` 或未設 | checklist §A–§D 全勾；Wave-H **governance_dual** 批准 |
| **S1 · URL enforce** | tier + allowlist | **URL gate · enforce**（fail-closed POST） | staging HTTPS URL + allowlist 已配置；dry-run POST 至 mock/staging endpoint 成功 |
| **S2 · DLQ observe** | 失敗可觀測 | **DLQ · advisory→enforce**：先 `DLQ_ENABLED=1` + 專用 path，觀察 0 誤寫再綁 mandatory | inspect CLI `list/stats` 可讀；DLQ path 與 prod 分軌 |
| **S3 · HMAC shadow→enforce** | 簽名與驗簽 | **HMAC sender · shadow**（僅 signed POST 至 sample receiver，tier gate 可先 log-only 若 impl 支援）→ **enforce**（缺簽名 reject POST） | receiver fixtures + sample impl 綠；staging secret 輪替 runbook 就緒 |
| **S4 · Retry enforce** | retry + DLQ 閉環 | **Retry tier readiness · enforce**（`max_attempts≥1` + DLQ=1 + HMAC ready 三 gate） | S1–S3 穩定 ≥48h；注入失敗 → retry 用盡 → DLQ 1 行可稽核 |

#### Shadow vs enforce 裁決（staging wave）

| Gate | Staging 首開模式 | 升格 enforce 條件 | 備註 |
|------|------------------|-------------------|------|
| **URL / allowlist** | **enforce**（無 shadow） | S1 即 enforce | 錯 URL 風險最高；先阻 POST |
| **DLQ** | **advisory**（enabled · 監控寫入量） | S2 末或 S4 前 bind mandatory | 與 retry mandatory 綁定（§4.6.6.3 `dlq_required`） |
| **HMAC sender** | **shadow**（signed POST 至 sample receiver；tier reject **可選延後** 至 receiver 綠） | receiver contract test 全綠 + 尚書省 staging 演練窗口 | staging **recommended** fixtures（§4.6.6.4） |
| **Retry** | **advisory**（`max_attempts=1` 最小演練） | S4 · 三 preflight gate 全 enforce | **must** 晚於 DLQ + HMAC |

**CI 邊界**：`p7-notification-smoke` **仍 sandbox-only · non-blocking**；staging 演練走 **人工 env runbook**（`WH-P7-PROD-staging-smoke-runbook-v1`），**禁止** CI workflow 設 `TIER=staging/prod`（§4.5 · §4.6.6 hard rule）。

---

### Staging integration checklist

> Orchestrator / Infra 逐項打勾；**全部 mandatory 項完成** 後方可進入 Phase S1 flip `TIER=staging`。

#### A. Env / config 層面

- [ ] **A-1** Staging-dedicated webhook URL 已登記（HTTPS · 非 bare IP · 在 allowlist grammar 內）— `GOV_NOTIFICATION_WEBHOOK_URL` + `GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST`
- [ ] **A-2** Staging-dedicated HMAC secret 已注入 env（**禁止入庫** · 輪替 procedure 已寫 runbook）
- [ ] **A-3** Staging-dedicated DLQ 目錄／path 已配置（與 sandbox/prod jsonl **分軌**）— `GOV_NOTIFICATION_WEBHOOK_DLQ_PATH`
- [ ] **A-4** `GOV_NOTIFICATION_WEBHOOK_TIER=staging` flip 僅在 **人工 env** 或 staging 專用 deployment slot；CI / default dev **仍 sandbox**
- [ ] **A-5** Retry env 鍵 staging 建議值已文件化（`max_attempts≥1` · backoff ms）— 對齊 `WH-P7-NOTIF-RETRY-prod-v1` tier default
- [ ] **A-6** Rollback env 包已備（一鍵：`TIER`  unset 或 `sandbox` + `DLQ_ENABLED=0` + `HMAC_ENABLED=0`）— 見 §C rollback

#### B. 觀測性

- [ ] **B-1** Log 可區分 `blocked_by_url_tier_policy` / `blocked_by_hmac_tier_policy` / retry readiness `blocked_rule`（不含 secret 原文）
- [ ] **B-2** DLQ inspect CLI 可對 staging path 跑 `list` / `stats`（`WH-P7-NOTIF-DLQ-inspect-cli-impl-v1`）
- [ ] **B-3** Metrics 或 structured log 可聚合 staging gate 命中次數（reject vs dispatched vs DLQ write）— follow-up `WH-P7-PROD-staging-metrics-v1`
- [ ] **B-4** Sample load / read-only smoke 可針對 staging tier 執行（**非** CI prod URL）— follow-up `WH-P7-PROD-staging-smoke-runbook-v1`

#### C. 風險管控

- [ ] **C-1** **Rollback plan** 已演練：unset `TIER` 或改 `sandbox` → 行為與 sandbox 封箱一致；無 orphan staging POST
- [ ] **C-2** URL gate fail-closed 已確認：allowlist miss → 不 POST · 外層 dispatch fail-open
- [ ] **C-3** DLQ 寫入 fail-open 已確認：磁碟不可寫不阻斷 dispatch
- [ ] **C-4** Staging 演練窗口 + on-call 已排（注入失敗 / retry 風暴 / HMAC 時鐘 skew 劇本）
- [ ] **C-5** Phase S4 完成前 **不** 對外宣稱 staging 等同 prod-ready

#### D. 協調

- [ ] **D-1** 尚書省已知 staging wave 範圍與 **Non-goals**（不含 prod rollout）
- [ ] **D-2** Infra 已 provision staging env 與 secret 注入路徑（對齊 `INSTANCE_ANCHOR_TANG` 類型 · 本票不寫具體路徑）
- [ ] **D-3** Downstream receiver（內部 mock 或客戶 staging endpoint）已同意接收 signed POST 與 idempotency 語意（§4.6.5.2）
- [ ] **D-4** Wave-H **governance_dual** 批文已留痕（staging tier flip 前置 · §4.6.6.3 `approval_required`）
- [ ] **D-5** Impl 票收口：`WH-P7-NOTIF-DLQ-impl-v1` · `WH-P7-NOTIF-PROD-URL-impl-v1` 已 **`validated`**；`WH-P7-NOTIF-RETRY-prod-impl-v1` · `WH-P7-NOTIF-HMAC-prod-impl-v1` 仍 **`implementer_done_pending_review`**（Reviewer C 待收口 · **非 blocking** 本設計票 `design_accepted`）

#### E. §4.6.6.4 enablement 對照（staging 最小集）

- [ ] **E-1** DLQ 設計 + 落盤 + inspect — **partial→staging required**
- [ ] **E-2** Retry 升格 impl — tier readiness gate **implemented**（unittest）
- [ ] **E-3** HMAC sender prod mandatory impl — tier gate **implemented**（unittest）
- [ ] **E-4** HMAC receiver contract — doc SSOT **done**
- [ ] **E-5** Receiver fixtures + sample impl — **staging recommended**（S3 前置）
- [ ] **E-6** PROD-URL-impl — minimal gate **partial**（unittest）
- [ ] **E-7** Advisory CI 穩定 — `p7-notification-smoke` sandbox-only **不變**

---

### Follow-up 票（staging wave · 建議開票順序）

| 票號 | 一句話 |
|------|--------|
| **`WH-P7-PROD-staging-env-config-v1`** | Provision staging 專用 URL / HMAC secret / DLQ path / env 模板與 rollback 一鍵包；對齊 checklist §A |
| **`WH-P7-PROD-staging-smoke-runbook-v1`** | 人工 env E2E runbook：emit → dispatch → signed POST → receiver 驗簽 → 失敗→retry→DLQ；含 sample load 與 go/no-go |
| **`WH-P7-PROD-staging-metrics-v1`** | staging gate 命中 / DLQ 寫入 / retry 分布之 log 或 metrics 聚合；對齊 checklist §B |
| `WH-P7-NOTIF-HMAC-receiver-fixtures-v1` | 已簽名樣本 + headers sidecar（S3 shadow 前置 · §4.6.6.4） |
| `WH-P7-NOTIF-HMAC-receiver-sample-impl-v1` | 最小 `verify_gov_webhook` reference + contract test（S3 enforce 前置） |
| `WH-P7-NOTIF-staging-integration-execute-v1` | checklist 全勾後 **執行** Phase S1–S4 拔線演練（impl · 非本設計票） |

> **Orchestrator 裁決**：本票（`WH-P7-PROD-staging-integration-v1`）= **設計 SSOT**；`WH-P7-NOTIF-staging-integration-v1`（合約 §4.6.6.4 索引名）可視為同 wave **execute** 票之別名 — 執行票建議用 `-execute-v1`  suffix 與本設計票區分。

---

### Non-Goals

- ❌ **不 touch** sandbox 行為 — default 單次 POST · opt-in retry/HMAC/DLQ · localhost gate **維持不變**。
- ❌ **不直接決定 prod rollout** — 尚書省 prod 批文 · Security sign-off · required CI 升格 → `WH-P7-NOTIF-prod-rollout-v1` · Wave-P7-6。
- ❌ **不修改** Python / tests / CI / docs / workflows / 其他票 / Progress。
- ❌ **不在本票執行** 真 staging POST 或 flip `TIER=staging`。
- ❌ **不升格** `p7-notification-smoke` 為 required check。
- ❌ **不合併** Phase 8.8 `orchestration_bridge_outbox` DLQ（§2.2 永久分軌）。
- ❌ **不宣稱** prod 通知 production-ready。

---

### Acceptance Criteria（本票 FRAME）

- **AC-1**：FRAME 含 Background / Goal / Phase S0–S4 藍圖 / Shadow vs enforce 表 / checklist / follow-up 票 / Non-goals。
- **AC-2**：Checklist 至少覆蓋 env、觀測性、風險管控、協調四域且項可打勾。
- **AC-3**：與 `WH-P7-PROD-phase1-wrapup-v1` · `WH-P7-PROD-roadmap-v1` Wave-P7-5 · 合約 §4.6.6.4 **無矛盾**。
- **AC-4**：Reviewer C 收口後 `STATE.overall_status` = `design_accepted`。
- **AC-5**：AllowedPaths 僅本票。

---

### AllowedPaths / BlockedPaths

| Allowed | Blocked |
|---------|---------|
| `04_Workflows/tickets/WH-P7-PROD-staging-integration-v1_state.md` | 其餘全 repo |

---

### Dependencies（只讀索引）

| 票號 / 文件 | 角色 |
|-------------|------|
| `WH-P7-PROD-phase1-wrapup-v1` | prod phase-1 收口 · 缺口索引 |
| `WH-P7-PROD-roadmap-v1` | Wave-P7-5 staging 整合 · DAG |
| `WH-P7-NOTIF-DLQ-impl-v1` · `*-inspect-cli-*` | DLQ partial · validated |
| `WH-P7-NOTIF-PROD-URL-impl-v1` | URL tier gate · validated |
| `WH-P7-NOTIF-RETRY-prod-v1` / `*-impl-v1` | retry tier readiness |
| `WH-P7-NOTIF-HMAC-prod-mandatory-v1` / `*-impl-v1` | HMAC tier mandatory |
| `WH-P7-NOTIF-HMAC-receiver-contract-v1` | §4.6.5.2 receiver SSOT |
| `docs/outbox-and-feedback-layer-contract-v1.md` §4.6.3–§4.6.6 | 合約 SSOT |

---

## STATE

- **overall_status**: `validated`
- **current_owner**: scribe
- **next_action**: Wave-P7-6 prod rollout · 可選 staging metrics
- **last_updated**: 2026-06-24 · P7 staging execution agent（execute 證據回填）
- **wave**: Wave-P7-5 · P7 staging tier integration · design
- **status_by_role**:
  - **Orchestrator (A)**: done — FRAME + checklist + follow-up 索引
  - **Implementer (B)**: n/a — 本票 doc-only
  - **Reviewer (C)**: done — 2026-06-24 execute 後 **validated**
  - **Scribe (D)**: done — 2026-06-23 · smoke-runbook 正文 handoff
- **notes**:
  - checklist S0–S4 · shadow/enforce 表 SSOT 不變
  - **首輪 staging smoke 完成** · execute run `20260623T165252Z` · 仍非 prod-ready

---

## B_REPORT

> Scribe · 2026-06-23 · staging integration 設計 SSOT + **S1–S4 完成 checklist**

### §1 何時算 staging S1–S4 完成

| Phase | 完成條件（checklist） | 證據類型 | 未完成 → 下一步票 |
|-------|----------------------|----------|-------------------|
| **S0** | §A–§D 全勾 · `governance_dual` 批文 | 批文留痕 | 尚書省 / Wave-H |
| **S1 URL** | allowlist match → POST 2xx；miss → `blocked_by_url_tier_policy` · HMAC co-ready | smoke-runbook §2 步驟 1–2 log | `WH-P7-NOTIF-staging-integration-execute-v1` |
| **S2 DLQ** | happy path 無 DLQ 行；故障注入 +1 行 staging jsonl | inspect CLI `list` · `tier=staging` | execute 票 |
| **S3 HMAC** | signed POST + receiver 驗簽；enforce：缺 HMAC → `blocked_by_hmac_tier_policy` | receiver fixtures 綠 · sample impl | `WH-P7-NOTIF-HMAC-receiver-*` |
| **S4 Retry** | 健康 endpoint 無 DLQ；503 至 retry 用盡 → DLQ 1 行 | smoke-runbook §5 · inspect `stats` | execute 票 |

### §2 doc 就緒 · execute pending

- env-config · smoke-runbook · 本票 checklist：**human-runnable**
- **未**有真 staging env 演練證據（本輪不 flip `TIER=staging`）
- 完成宣告仍留 execute 票 + Progress append

### §3 驗證

無 runtime（doc-only）。

---

## C_REPORT

- **review_date**: 2026-06-23
- **reviewer_role**: P7 staging integration Reviewer (C)
- **verdict**: **`accepted_with_gaps`**
- **conclusion**: Phase S0–S4 藍圖 + checklist + B_REPORT §1 完成條件表就緒。**doc/runbook ready · 真 env execute pending** · receiver fixtures S3 硬依賴。
- **scope**: FRAME Phase S0–S4

**一句話總結（core）**：本票定義了從 **unittest-only partial gate** 走到 **staging 真 env 可控啟用** 的 Phase S0–S4 rollout、shadow vs enforce 裁決表與 go/no-go checklist，作 Wave-P7-5 設計 SSOT；**不執行**拔線、**不含** prod rollout。

**審查摘要**

| 檢查項 | 結果 |
|--------|------|
| 與 phase-1 wrap-up 現況一致 | ✅ DLQ + PROD-URL **`validated`**；RETRY/HMAC impl **`implementer_done_pending_review`** — FRAME D-5 原寫「四票均 validated」**已修正** |
| Phase S0–S4 vs §4.6.6.4 / roadmap | ✅ 執行序 S1 URL enforce → S2 DLQ advisory → S3 HMAC shadow→enforce → S4 Retry enforce 與 tier policy 語意一致；§4.6.6.4 L717 為 **impl/checklist 完成序**，本票 S0–S4 為 **staging flip 序**，無矛盾 |
| Shadow vs enforce 表 | ✅ URL 首開 enforce；DLQ/HMAC/Retry 漸進升格；Retry must 晚於 DLQ + HMAC — 對齊 wrap-up §3 刻意缺口 |
| Follow-up 票索引 | ✅ env-config · smoke-runbook · metrics · receiver fixtures/sample-impl · `-execute-v1` 覆蓋 checklist §A–§E；未漏 governance / CI 邊界 |
| CI 邊界 | ✅ sandbox-only · 禁止 CI `TIER=staging/prod` — 與 §4.5 · §4.6.6 一致 |
| Blocking | 無 |

**最明確 gap（非 blocking 設計票）**

- **HMAC receiver fixtures + sample impl** 仍 `not_implemented_yet` — S3 僅能 **shadow**（signed POST 演練），tier HMAC **enforce 須延後**至 receiver contract test 全綠。
- **RETRY-prod-impl / HMAC-prod-impl** Reviewer C 待收口 — unittest 骨架已 landing，但不等同 staging env 已啟用。
- **Wave-H governance_dual 批文** — S0 硬 stop；本票 FRAME 已標，execute 票前置。

**兩句話（對 phase-1 handoff）**

- **已對齊**：staging integration 設計正確承接 phase-1「unittest partial 已就緒、真 env 刻意未啟」敘述，並把缺口拆成可派工 checklist + follow-up 票。
- **刻意保留**：receiver reference 鏈、真 `TIER=staging` flip、S1–S4 拔線演練仍留 **execute 票 + governance**，本設計票不宣稱 staging wave 完成。

---

## D_REPORT

- **handoff_date**: 2026-06-23
- **from**: P7 **staging integration 設計**（`design_accepted` · Reviewer C `accepted_with_gaps`）
- **to**: Orchestrator（開 staging wave impl / runbook 票）

**設計票（doc 就緒 · 本 wave 已交付）**

| 票 id | 狀態 | 角色 |
|-------|------|------|
| **`WH-P7-PROD-staging-env-config-v1`** | `implementer_done_pending_run` | env matrix / S1–S3 套件 SSOT |
| **`WH-P7-PROD-staging-smoke-runbook-v1`** | `implementer_done_pending_run` | S1–S4 人工 smoke 正文 |
| **`WH-P7-PROD-staging-integration-v1`** | `implementer_done_pending_run` | 本票 · Phase S0–S4 + checklist |

**Execution 入口票（2026-06-23 已建檔 · 下一批派工）**

| 票 id | 狀態 | 一句話 scope |
|-------|------|--------------|
| **`WH-P7-PROD-staging-env-bootstrap-v1`** | `frame_ready` | S0 provision · 不 flip tier |
| **`WH-P7-NOTIF-HMAC-receiver-fixtures-impl-v1`** | `frame_ready` | S3 receiver 鏈 · contract tests |
| **`WH-P7-NOTIF-staging-integration-execute-v1`** | `frame_ready` | checklist 全勾後 S1–S4 真 env · Progress |
| **`WH-P7-PROD-prod-rollout-governance-bootstrap-v1`** | `design_accepted` | Wave-P7-6 prod FRAME（可並行） |

**派工順序**：bootstrap → receiver-impl → execute。**完成 execute 後** staging wave 方可誠實宣稱 S1–S4 演練完成（仍非 prod-ready）。

**handoff 一句話**：staging 設計 + env-config + smoke-runbook **doc 就緒**；下一批 = bootstrap provision → execute 票；勿在 receiver fixtures 與 governance 批文未完成前 flip `TIER=staging`。

**Progress**：本輪未 append `00_Agent_Work_Progress.md`（任務邊界禁止改 Progress）；Scribe 可另輪 append。
