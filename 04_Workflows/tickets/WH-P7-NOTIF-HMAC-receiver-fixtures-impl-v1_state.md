# WH-P7-NOTIF-HMAC-receiver-fixtures-impl-v1 — Ticket State

> handoff 摘要檔；P7 **HMAC receiver 鏈最小 impl** execution 票。  
> 目的：落地 §4.6.5.2 receiver 最小實作——signed fixture + `verify_gov_webhook` reference + contract tests + 可部署 internal staging receiver；供 staging S3 驗簽。  
> 合併 roadmap 原 `WH-P7-NOTIF-HMAC-receiver-fixtures-v1` + `sample-impl-v1` 最小可演練 scope。

---

## FRAME

### Goal

解除 staging smoke-runbook S3 硬阻塞：receiver 可驗簽 adapter 產出的 signed POST，contract tests 對齊 `WH-P7-NOTIF-HMAC-receiver-contract-v1`。

### 核心 checklist

- [ ] 新增 `tests/fixtures/webhook_hmac/`（signed body + headers sidecar + README）。
- [ ] 實作最小 receiver 驗簽函式（成功 / 失簽 / 過期 timestamp / replay / event_id mismatch）。
- [ ] 新增 contract unittest（≥5 cases）對齊 receiver-contract SSOT。
- [ ] 提供可部署的 **internal staging receiver** 入口（FastAPI 或 CLI · non-prod only）。
- [ ] 跑通一筆 sender adapter 產出的 signed POST → receiver 2xx。
- [ ] 更新 smoke-runbook §3 前置條件 cross-ref（receiver 鏈就緒）。

### Non-goals

- ❌ 不 flip prod/staging tier env（execute 票負責）。
- ❌ 不實作 receiver 端 secret rotation 雙窗口（receiver team domain）。
- ❌ 不升格 CI required check。

### AllowedPaths

- `tests/fixtures/webhook_hmac/**`
- `tests/test_*hmac*receiver*`（或等價 contract test 模組）
- receiver reference 模組（路徑見 Implementer 裁決 · 對齊 `Master_Map.json`）
- `04_Workflows/tickets/WH-P7-NOTIF-HMAC-receiver-fixtures-impl-v1_state.md`

### BlockedPaths

- `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `.cursor/rules/**`
- prod deployment config · `.env` commit

### Acceptance Criteria

- **AC-1**：≥5 contract cases 綠 · fixture README 可審計。
- **AC-2**：signed POST → receiver 2xx 可重跑演示。
- **AC-3**：integration checklist §E-5 可勾 · execute 票 S3 可排程。

---

## STATE

- **overall_status**: `done_with_gaps`
- **current_owner**: scribe
- **next_action**: 客戶/prod receiver 上線 · secret rotation 雙窗口 → 另票
- **last_updated**: 2026-06-24 · P7 staging execution agent
- **wave**: Wave-P7-3 / Wave-P7-5 · HMAC receiver impl
- **status_by_role**:
  - **Orchestrator (A)**: done — 2026-06-23 開票
  - **Implementer (B)**: done — 2026-06-24 · fixtures + verify + contract tests + staging receiver
  - **Reviewer (C)**: done — 2026-06-24 · **`accepted_with_gaps`** → **`done_with_gaps`**
  - **Scribe (D)**: pending — Progress append
- **notes**:
  - 上游 **`WH-P7-NOTIF-HMAC-receiver-contract-v1`** SSOT
  - **7/7 contract tests OK** · staging receiver HTTPS on localhost:8765

---

## B_REPORT (Implementer)

- **status**: done
- **purpose**: receiver fixture + 驗簽 reference + contract tests，供 staging S3 驗簽演練。
- **deliverables**:
  - `delivery/webhook_hmac_receiver_v1.py` — `verify_gov_webhook` · `ReplayCache` · `sign_gov_webhook_headers`
  - `tests/fixtures/webhook_hmac/` — signed / invalid / expired / mismatch / replay fixtures + README
  - `tests/test_webhook_hmac_receiver_v1.py` — **7 contract cases**
  - `tools/staging_webhook_receiver_v1.py` — internal HTTPS receiver（non-prod · HMAC verify）
  - `tools/generate_webhook_hmac_fixtures_v1.py` — fixture 再生工具
- **verification**:
  - `python -m unittest tests.test_webhook_hmac_receiver_v1 -v` → **7/7 OK**
  - execute S3：signed POST receiver verify ok · HMAC off → `blocked_by_hmac_tier_policy`

---

## C_REPORT (Reviewer)

- **review_date**: 2026-06-24
- **verdict**: `accepted_with_gaps`
- **core**: staging S3 可驗簽 adapter signed POST；contract tests 對齊 §4.6.5.2；execute 票已驗證 E2E。
- **gaps**: 未在 prod / 客戶 receiver 上線 · seen-set 為 in-memory reference · 無 secret rotation 雙窗口
- **conclusion**: **7/7 contract tests** + execute **S3 E2E OK**；仍為 **reference impl**（in-memory replay cache），**未**上客戶/prod receiver。

---

## D_REPORT (Scribe)

- **handoff_date**: 2026-06-24
- **depends_on**: `WH-P7-NOTIF-HMAC-receiver-contract-v1` · `WH-P7-NOTIF-HMAC-prod-impl-v1`（sender · validated）
- **unlocks**:
  - `WH-P7-NOTIF-staging-integration-execute-v1` — **S3 已完成**
  - `WH-P7-PROD-staging-smoke-runbook-v1` S3 硬阻塞解除
  - `WH-P7-PROD-staging-integration-v1` checklist §E-5 可勾
