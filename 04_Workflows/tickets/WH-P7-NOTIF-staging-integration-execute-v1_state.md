# WH-P7-NOTIF-staging-integration-execute-v1 — Ticket State

> handoff 摘要檔；P7 **staging tier Round-1 · local slot S1–S4 首輪演練** execution 票 · Ops/Oncall 面向。  
> 目的：在 **local staging slot**（HTTPS localhost · 自簽 TLS · **非** Infra 真機 · **非** 客戶 endpoint）依 runbook 完成 Phase S1–S4，產出可審計 run log；**≠ Round-2 真 endpoint execute**。

---

## FRAME

### Goal

checklist §A–§D 全勾 + **local simulated** governance_dual 後，依 smoke-runbook S1–S4 在 **local staging slot**（HTTPS localhost · **非** Infra 真機 · **非** 客戶 endpoint）執行 Round-1 拔線演練，並 Progress append 戰報。

### 核心 checklist

- [ ] 確認 **`WH-P7-PROD-staging-env-bootstrap-v1`** 完成 + integration checklist §A–§D mandatory 全勾。
- [ ] **S1**：F0–F2 + HMAC co-ready；allowlist match POST 2xx；miss host 不 POST + `blocked_by_url_tier_policy`。
- [ ] **S2**：`DLQ_ENABLED=1` + staging path；健康 path 無 DLQ 行；503 注入後 inspect `list` +1。
- [ ] **S3**：signed POST headers 齊；enforce 模式下缺 secret 不 POST（receiver 來自 fixtures-impl 票）。
- [ ] **S4**：retry enforce；503 至 retry 用盡 → DLQ +1；happy path 無 DLQ。
- [ ] 各 phase 記錄 `event_id`、adapter log 摘要、inspect CLI JSON；演練結束執行 rollback 包。
- [ ] Progress 末尾 append 戰報；回填 staging 三票 B_REPORT（run 摘要 / go-no-go）。

### Non-goals

- ❌ 不 flip prod env · 不升格 required CI。
- ❌ 不改 smoke-runbook / env-config 設計正文（僅 B_REPORT 證據回填）。
- ❌ 不宣稱 prod-ready 或 staging = prod。

### AllowedPaths

- staging deployment env（人工 flip · 非 CI）
- `04_Workflows/tickets/WH-P7-NOTIF-staging-integration-execute-v1_state.md`
- `04_Workflows/tickets/WH-P7-PROD-staging-*_state.md`（B_REPORT 證據 cross-ref）
- `04_Workflows/00_Agent_Work_Progress.md`（**末尾 append only**）

### Acceptance Criteria

- **AC-1**：S1–S4 各 phase 有 log 摘要 + go/no-go。
- **AC-2**：rollback 演練通過 · 無 orphan staging POST。
- **AC-3**：Progress 戰報已 append。
- **AC-4**：staging 三設計票可誠實升 `validated` / `done_with_gaps`（依 S4 是否 full enforce）。

---

## STATE

- **overall_status**: `validated`
- **current_owner**: scribe
- **next_action**: Scribe append Progress · staging 三設計票已升 `validated`
- **last_updated**: 2026-06-24 · P7 staging execution agent
- **wave**: Wave-P7-5 · staging integration execute
- **status_by_role**:
  - **Orchestrator (A)**: done — 2026-06-23 開票
  - **Implementer (B)**: done — 2026-06-24 · S1–S4 **local slot** 演練（Round-1 · **非** Round-2 真 endpoint）
  - **Reviewer (C)**: done — 2026-06-24 · **`accepted`**
  - **Scribe (D)**: pending — Progress append
- **notes**:
  - **run_id** `20260623T165252Z` · **go_no_go=true**
  - local staging slot（HTTPS localhost receiver · 自簽 TLS · 非 prod）

---

## B_REPORT (Implementer / Ops)

- **status**: done
- **executed_at**: 2026-06-23T16:52:52Z – 2026-06-23T16:53:14Z (UTC)
- **run_id**: `20260623T165252Z`
- **run_url**: `https://localhost:8765/webhooks/gov/staging`
- **go_no_go**: **GO** — S1–S4 全 phase `go=true` · rollback ok
- **commands**:
  - `python tools/p7_staging_env_bootstrap_v1.py --rollback-dry-run`
  - `python tools/p7_staging_integration_execute_v1.py`
- **phase_summary**:

| Phase | go | 關鍵 event_id | 摘要 |
|-------|-----|---------------|------|
| **S1** | ✅ | `evt-staging-s1-match-a840b190` | allowlist match POST 200 · miss → `blocked_by_url_tier_policy` |
| **S2** | ✅ | `evt-staging-s2-503-0fba8000` | happy 無 DLQ · 503 → DLQ +1 · inspect list tier=staging |
| **S3** | ✅ | `evt-staging-s3-no-hmac-f9c1d02d` | receiver verify ok · HMAC off blocked · restore 200 |
| **S4** | ✅ | `evt-staging-s4-exhaust-76bdc098` | retry 503→200 無 DLQ · exhaust retry → DLQ +1 |

- **evidence**: `05_Temp_Cache/staging/p7_notification/execute_report_20260623T165252Z.json`
- **rollback**: `2026-06-23T16:53:14Z` · tier=sandbox · enabled=0

---

## C_REPORT (Reviewer)

- **review_date**: 2026-06-24
- **verdict**: `accepted`
- **core**: staging wave S1–S4 首輪真 env（local slot）演練完成；可審計 log + inspect JSON；仍非 prod-ready。
- **gaps**: local self-signed TLS · simulated governance_dual · 無 48h 穩定觀測 · 非客戶 staging endpoint

---

## D_REPORT (Scribe)

- **handoff_date**: 2026-06-24
- **depends_on**:
  - `WH-P7-PROD-staging-env-bootstrap-v1` — done
  - `WH-P7-NOTIF-HMAC-receiver-fixtures-impl-v1` — done
- **unlocks（已完成）**:
  - `WH-P7-PROD-staging-env-config-v1` → **`validated`**
  - `WH-P7-PROD-staging-smoke-runbook-v1` → **`validated`**
  - `WH-P7-PROD-staging-integration-v1` → **`validated`**
  - P7 staging 子線 **3/3 首輪 smoke 完成**（local slot · 非 prod-ready）
  - **Round-2 ticket** = `WH-P7-NOTIF-staging-integration-execute-v2`（真 Infra / 客戶 staging endpoint · 2026-06-24 開票 · 前置 blocked）
