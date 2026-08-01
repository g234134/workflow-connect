# WH-P7-PROD-prod-rollout-governance-bootstrap-v1 — Ticket State

> handoff 摘要檔；P7 **Wave-P7-6 prod rollout guardrails** 入口票 · **doc-only / gov bootstrap**。  
> 目的：在不 flip prod env 前提下，產出 rollout guardrails FRAME（required CI 升格條件、branch protection 草案、rollback playbook 索引）；承接 policy/roadmap 收口。

---

## FRAME

### Goal

Wave-P7-6 **prod 收口入口**——盤點 phase-1 validated impl 與 staging 演練證據缺口，起草 prod flip 前置 checklist 與 Wave-P7-6 下游票索引；**不宣稱 prod 已啟用**。

### 核心 checklist

- [ ] 盤點 prod phase-1 已 validated impl（DLQ/URL/RETRY/HMAC）與 **Wave-P7-5 證據現況**：已有 **local slot S1–S4 GO**（run_id `20260623T165252Z` · execute **`validated`** · wrapup 票）；**尚缺**真 Infra / 客戶 staging endpoint · 真 Wave-H **governance_dual** · 48h 穩定觀測 · prod flip decision。
- [ ] 起草 prod flip 前置 checklist（尚書省 + Security sign-off · §4.6.6.3）。
- [ ] 定義 `p7-notification-smoke` 升格 **required check** 的 G1–G8 證據模板（仍 default advisory）。

#### G1–G8 證據模板 · current_status（2026-06-24 · Round-2 開票後）

| Gate | 描述 | current_status | 證據 / 備註 |
|------|------|----------------|-------------|
| **G1** | Phase-1 adapter unittest validated | `done` | `tests.test_notification_webhook_dispatch_v1` 等 · 39/39 |
| **G2** | Round-1 local slot S1–S4 GO | `done` | run_id `20260623T165252Z` · execute-v1 **`validated`** |
| **G3** | 真 Infra / 客戶 staging endpoint S1–S4 GO | `partial` | Round-2 票 `WH-P7-NOTIF-staging-integration-execute-v2` 已開 · **blocked** · 未跑真 endpoint |
| **G4** | Wave-H **governance_dual** 真批文 | `open` | Round-1 僅 `simulated_local_execute_2026-06-24` |
| **G5** | 48h staging 穩定觀測 | `partial` | 票已排程觀測指標 · **未啟動**（待 Round-2 execute GO） |
| **G6** | Security 外部 POST sign-off | `open` | 無書面留痕 |
| **G7** | Rollback playbook（真 env ≤1min disarm） | `partial` | local slot rollback dry-run 5 ms（Round-1）· **未**驗證 Infra 真 slot |
| **G8** | Required CI 升格證據 | `open` | `p7-notification-smoke` 仍 advisory · non-blocking |
- [ ] 對照 **`WH-P7-NOTIF-PROD-policy-v1`** · **`WH-P7-PROD-roadmap-v1`** 標記可收口 vs 仍 open 項。
- [ ] 列出 Wave-P7-6 下游 impl 票索引（prod registry gate · ci-required · prod execute）。
- [ ] Scribe：Progress 末尾一行 prod rollout 入口索引（可選 · 本票 B 完成後）。

### Non-goals

- ❌ 不 flip prod env · 不設定 prod URL · 不開 required CI。
- ❌ 不改 adapter / tests / workflows。
- ❌ 不取代 `WH-P7-NOTIF-PROD-policy-v1` SSOT（僅 cross-ref）。

### AllowedPaths

- `04_Workflows/tickets/WH-P7-PROD-prod-rollout-governance-bootstrap-v1_state.md`
- `04_Workflows/plans/**`（可選 rollout 草案 · Orchestrator 裁決）
- `04_Workflows/00_Agent_Work_Progress.md`（**末尾 append only** · Scribe）

### Acceptance Criteria

- **AC-1**：prod flip 前置 checklist + G1–G8 模板可審計。
- **AC-2**：Wave-P7-6 下游票索引 ≥3 張。
- **AC-3**：明確 non-claim：prod 未啟用 · CI 仍 advisory default。

---

## STATE

- **overall_status**: `design_accepted`
- **current_owner**: orchestrator
- **next_action**: 在現有 **local slot GO** 證據基礎上起草 FRAME · Implementer（文檔）落盤 prod flip 前置 checklist · G1–G8 模板 · Wave-P7-6 下游索引；**不宣稱 prod flip 已執行**
- **last_updated**: 2026-06-24 · P7 staging Round-2 execution agent（G3/G5/G7 partial）
- **wave**: Wave-P7-6 · prod rollout governance bootstrap
- **status_by_role**:
  - **Orchestrator (A)**: done — 2026-06-23 開票
  - **Implementer (B)**: pending — doc FRAME
  - **Reviewer (C)**: pending
  - **Scribe (D)**: pending
- **notes**:
  - **Wave-P7-5 證據**：local slot S1–S4 GO（run_id `20260623T165252Z` · execute-v1 **`validated`** · bootstrap / receiver-impl **`done_with_gaps`**）— 可引用 wrapup 票 · **不等同** prod-ready
  - **仍缺**：真 Infra / 客戶 staging endpoint execute · 真 governance_dual · 48h 觀測完成 · registry gate · required CI · Security sign-off
  - **Round-2**：`WH-P7-NOTIF-staging-integration-execute-v2` 已開 · **blocked** · **未跑 S1–S4** · G3/G5/G7 → **`partial`**（非 `done`）
  - 完成後可將 policy/roadmap 標 **design 收口** · 仍非 prod 啟用

### 下一位 human 該做什麼（Round-2 解阻 checklist）

> 對齊 `WH-P7-NOTIF-staging-integration-execute-v2` §解阻最短路徑；**全部勾完**後才分配新 `run_id` 跑 S1–S4。

- [ ] **拿批文**：尚書省 Wave-H **`governance_dual`** 真批文留痕（≠ `simulated_local_execute_2026-06-24`）→ 解 G4 / execute-v2 P-1
- [ ] **配 staging endpoint**：Infra provision 真 staging slot + non-prod HTTPS endpoint（allowlist 內）→ 解 G3 / execute-v2 P-2
- [ ] **Security review**：外部 POST 風險書面 sign-off（allowlist · secret · 無 prod URL）→ 解 G6 / execute-v2 P-3
- [ ] **allowlist**：客戶 staging endpoint allowlist 部署（**禁止** prod URL）→ 解 execute-v2 P-4
- [ ] **receiver deploy**：reference impl 或客戶 receiver 上 staging slot · 驗簽探針 OK → 解 execute-v2 P-5
- [ ] **之後才能 execute**：Implementer 分配新 `run_id` · 依 smoke-runbook 跑 **S1–S4** · rollback · Progress append · 啟動 48h 觀測窗口（G5 仍 `partial` 直至窗口完成）

**G3 / G5 / G7 現況**：均 **`partial`** — G3 缺真 endpoint GO · G5 觀測未啟動 · G7 僅 local slot rollback 已驗。

---

## B_REPORT (Implementer · doc)

- **status**: pending
- **purpose**: prod rollout guardrails FRAME · G1–G8 · Wave-P7-6 下游索引；不 flip prod。
- **core_checklist_summary**: phase-1 盤點 · **local slot GO 已存在** · 真 staging endpoint / 48h / flip decision 仍 open · prod flip checklist · CI 升格模板 · policy/roadmap 對照 · 下游票索引
- **verification**: doc-only · Reviewer 對照 §4.6.6.3 · roadmap Wave-P7-6

---

## C_REPORT (Reviewer)

- **verdict**: `not_yet_reviewed`
- **core**: Wave-P7-6 入口 SSOT；prod flip 前置與 required CI 升格門檻可審計；不宣稱 prod 已啟用。
- **gaps**: 尚未落盤 FRAME · **local slot S1–S4 GO 證據可引用**（run_id `20260623T165252Z`）· **仍缺**真 Infra / 客戶 staging endpoint · 真 governance_dual · 48h 觀測 · prod flip / required CI / Security sign-off。

---

## D_REPORT (Scribe)

- **handoff_date**: 2026-06-23
- **depends_on**: `WH-P7-NOTIF-PROD-policy-v1` · `WH-P7-PROD-roadmap-v1` · `WH-P7-PROD-phase1-wrapup-v1`（local slot GO · run_id `20260623T165252Z`）· execute **`validated`**
- **staging_gap（仍 open）**: 真 Infra / 客戶 staging endpoint · 真 Wave-H governance_dual · 48h 穩定觀測
- **unlocks（完成後）**:
  - `WH-P7-PROD-roadmap-v1` → `done_with_gaps`（design 收口）
  - `WH-P7-NOTIF-PROD-policy-v1` → `done_with_gaps`（design 收口）
  - Wave-P7-6 下游：`WH-P7-NOTIF-prod-rollout-v1` · `WH-P7-NOTIF-ci-required-v1`（候選）
