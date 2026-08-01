# TICKET STATE · W4-P85-OPTIONAL-BRIDGE-SMOKE-C-v1 · P85 bridge stub／Smoke C 可驗收小票

> **授權**：尚書省「全授權」A2 · 2026-07-29  
> **≠** required CI · **≠** prod browser · **≠** Phase% · **≠** Round-2

---

## FRAME

- Goal: 把 P85 closure gaps（bridge stub／Smoke C manual）收成可驗收 checklist 小票；docs ± 既有 advisory A/B 測；**不**默升 CI。
- Scope:
  - MUST：`docs/p85_optional_bridge_smoke_c_checklist_v1.md`
  - MUST：本 STATE + Progress 一句
  - MAY：複跑 Smoke A/B unittest（advisory 證據）
- NonScope:
  - 新建／改 required GitHub checks
  - Playwright／prod browser
  - bridge 持久化／outbox PG always-on
  - 重開 wave-H2 為 Phase closure
- AllowedPaths:
  - `docs/p85_optional_bridge_smoke_c_checklist_v1.md`
  - `docs/p85_h2_closure_prep_checklist_v1.md`（僅一行 cross-ref · 可選）
  - `docs/phase8_5-bridge-smoke-runbook-v1.md`（僅一行 cross-ref · 可選）
  - `04_Workflows/tickets/W4-P85-OPTIONAL-BRIDGE-SMOKE-C-v1_state.md`
  - `04_Workflows/00_Agent_Work_Progress.md`（末尾）
- BlockedPaths:
  - `.github/workflows/**` required／branch protection
  - 憲法 §7 · `.env` · DarkOps
- AcceptanceCriteria:
  - AC-1：checklist 明示 stub 邊界 + Smoke C 手跑矩陣
  - AC-2：non_claims 含 ≠ required CI／prod browser
  - AC-3：Smoke A/B advisory 可跑則附結果；Smoke C 未手跑 → DONE_WITH_GAPS 可接受

---

## STATE

- **overall_status**: `done_with_gaps`
- **current_owner**: closed
- **last_updated**: 2026-07-29T00:45+08:00
- **next_action**: 可選人類完成 Smoke C C1–C4；**勿**進 required CI
- **gaps**: Smoke C 手跑矩陣未在本輪 live curl（設計上 manual）

---

## B_REPORT

- changed_files:
  - `docs/p85_optional_bridge_smoke_c_checklist_v1.md`（新建）
  - `04_Workflows/tickets/W4-P85-OPTIONAL-BRIDGE-SMOKE-C-v1_state.md`（本檔）
- verification: 見全授權戰報 · Smoke A/B advisory 命令
- non_claims: ≠ required CI · ≠ prod browser · ≠ Phase%
