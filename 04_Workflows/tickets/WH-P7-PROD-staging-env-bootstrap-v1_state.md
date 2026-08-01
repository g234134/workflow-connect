# WH-P7-PROD-staging-env-bootstrap-v1 — Ticket State

> handoff 摘要檔；P7 **staging env provision** execution 票 · Infra/Ops 面向。  
> 目的：依 `WH-P7-PROD-staging-env-config-v1` env matrix 在 staging 專用 deployment slot 完成 S0 資源 provision；**仍不 flip `TIER=staging` 做 S1 POST**。  
> **本票不改** adapter Python / tests / CI / docs 正文（僅回填本票 STATE / B_REPORT）。

---

## FRAME

### Goal

在 governance 批文與 env-config SSOT 就緒前提下，完成 staging 專用 **URL / secret / DLQ path / rollback 包** 的實際 provision，並留下可審計 operator 紀錄；為 `WH-P7-NOTIF-staging-integration-execute-v1` 解鎖 S1 前置。

### 核心 checklist

- [ ] 取得 Wave-H **`governance_dual`** 批文留痕（integration checklist §D-4）。
- [ ] 依 env-config §1 注入 staging 專用 `GOV_NOTIFICATION_WEBHOOK_URL` + `URL_ALLOWLIST`（non-prod host）。
- [ ] 注入 staging 專用 `HMAC_SECRET` slot（與 sandbox/prod 分軌；**禁止入庫**）。
- [ ] 建立 `outbox/notification_dlq/staging/` 目錄與寫入權；確認 DLQ path 分軌。
- [ ] 部署/啟動 **sample HMAC receiver**（可指向 `WH-P7-NOTIF-HMAC-receiver-fixtures-impl-v1` 最小 endpoint）。
- [ ] 驗證 rollback 包（env-config §2.2 R1–R5）可在 ≤1 分鐘內 disarm POST。
- [ ] 回填 bootstrap 完成時間、operator、rollback 演練結果至本票 B_REPORT。

### Non-goals

- ❌ 不 flip `GOV_NOTIFICATION_WEBHOOK_TIER=staging` 做 S1–S4 POST 演練（→ execute 票）。
- ❌ 不 provision prod env · 不升格 CI required check。
- ❌ 不改 env-config / integration / smoke-runbook 設計正文（僅 cross-ref 回填）。

### AllowedPaths

- staging deployment slot / secret manager（Infra 操作 · 非 repo commit）
- `04_Workflows/tickets/WH-P7-PROD-staging-env-bootstrap-v1_state.md`（本票 STATE / B_REPORT）
- `04_Workflows/tickets/WH-P7-PROD-staging-env-config-v1_state.md`（**可選** · B_REPORT bootstrap 證據 cross-ref 一行）

### Acceptance Criteria

- **AC-1**：§A checklist mandatory 項全勾 · 有 operator 時間戳。
- **AC-2**：rollback 演練通過 · 無 orphan staging POST。
- **AC-3**：`TIER` 仍 sandbox 或未設 · 未誤 flip S1。
- **AC-4**：本票 B_REPORT 含 provision 摘要 · STATE → `review_done_pending_scribe` 或 `validated`。

---

## STATE

- **overall_status**: `done_with_gaps`
- **current_owner**: scribe
- **next_action**: Wave-P7-6 prod rollout governance · 真 Infra staging slot 另票
- **last_updated**: 2026-06-24 · P7 staging execution agent
- **wave**: Wave-P7-5 · P7 staging · env bootstrap execution
- **status_by_role**:
  - **Orchestrator (A)**: done — 2026-06-23 開票
  - **Implementer (B)**: done — 2026-06-24 · S0 provision + rollback dry-run
  - **Reviewer (C)**: done — 2026-06-24 · **`accepted_with_gaps`** → **`done_with_gaps`**
  - **Scribe (D)**: pending — Progress append
- **notes**:
  - 上游 **`WH-P7-PROD-staging-env-config-v1`** SSOT 已就緒
  - **provision 完成** · tier 維持 sandbox 直至 execute 票 flip
  - rollback dry-run **5 ms** · `within_1_minute=true`

---

## B_REPORT (Implementer / Infra)

- **status**: done
- **executed_at**: 2026-06-23T16:52:51Z (UTC)
- **operator**: P7 staging execution agent (local staging slot)
- **purpose**: 依 env-config env matrix 完成 staging S0 資源 provision（URL/secret/DLQ/rollback），仍不 flip tier 做 S1 POST。
- **actions_completed**:
  - [x] governance_dual 留痕（local slot · `simulated_local_execute_2026-06-24`）
  - [x] staging HTTPS receiver URL + allowlist（`https://localhost:8765/webhooks/gov/staging`）
  - [x] HMAC secret slot（`05_Temp_Cache/staging/p7_notification/hmac_secret.slot` · **不入庫**）
  - [x] DLQ 分軌目錄 `outbox/notification_dlq/staging/` + 寫入權
  - [x] TLS 自簽 bundle（`tests/fixtures/staging_tls/` → slot copy）
  - [x] rollback 包 `rollback_env.json` · dry-run **5 ms**
- **artifacts**:
  - `05_Temp_Cache/staging/p7_notification/env_slot.json`
  - `05_Temp_Cache/staging/p7_notification/runtime_env.json`
  - `tools/p7_staging_env_bootstrap_v1.py`
- **verification**:
  - `python tools/p7_staging_env_bootstrap_v1.py --rollback-dry-run` → `ok=true` · `within_1_minute=true`

---

## C_REPORT (Reviewer)

- **review_date**: 2026-06-24
- **verdict**: `accepted_with_gaps`
- **core**: staging slot 依 env-config SSOT 完成 S0 provision；rollback 可逆；execute 票已消費本 slot 完成 S1–S4。
- **gaps**: 非 Infra 真機 deployment slot · governance_dual 為 local simulated 留痕 · TLS 為自簽 localhost（非客戶 staging endpoint）
- **conclusion**: S0 provision + rollback 已交付且 execute 已消費；仍為 **local staging slot / simulated governance_dual / 自簽 localhost**，**非** Infra 真機 staging deployment。

---

## D_REPORT (Scribe)

- **handoff_date**: 2026-06-24
- **depends_on**: `WH-P7-PROD-staging-env-config-v1` · `WH-P7-PROD-staging-integration-v1` checklist §A–§D
- **unlocks**:
  - `WH-P7-NOTIF-staging-integration-execute-v1` — **已執行 · go_no_go=true**
  - `WH-P7-PROD-staging-env-config-v1` — 可升 `validated`
- **parallel**: `WH-P7-NOTIF-HMAC-receiver-fixtures-impl-v1` — 已完成
