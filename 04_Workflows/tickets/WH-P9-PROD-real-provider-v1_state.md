# WH-P9-PROD-real-provider-v1 — Ticket State

> handoff 摘要檔；P9 **真实 payment provider / prod ledger** 入口票 · **blocked · 需尚书省 prod 金流批文**。  
> 目的：定义 prod provider adapter · env gate · prod path 制度 FRAME；**本票不开工直至批文**。

---

## META

| 欄位 | 值 |
|------|-----|
| **Phase** | P9 |
| **Lane** | prod closure · WC-M3 升格 |
| **Parent wave** | Wave-P9 · payment prod follow-up |
| **Owner** | orchestrator |
| **Ticket type** | prod impl · gated |

---

## FRAME

### Goal（一行目的）

在尚书省 **prod 金流批文** 后，接入真实 payment provider（如 Stripe）与 prod order ledger 路径；与 sandbox adapter 分轨 · fail-closed。

### 核心 checklist

- [ ] 尚书省 prod 金流批文留痕（env · provider · ledger 路径 · rollback）。
- [ ] Prod provider adapter：与 `payment_adapter.py` sandbox 分接口或分模块 · 禁止 sandbox env 误触 prod。
- [ ] Prod env gate（独立键 · default off）· 密钥走 instance anchor · **禁止** 写入 repo 或 CI log。
- [ ] Prod ledger 路径与 `WC_M3_payment_closure_scope_v1` non-goals _lift_ 对照表。
- [ ] 状态机复用 `transition_order` · prod charge webhook / idempotency 设计。
- [ ] unittest + staging 演练（若有 staging slot）· **无 prod 默认 CI**。
- [ ] Progress / scope doc 更新 prod closure 诚实边界。

### Non-goals

- ❌ **无批文不施工** · 不把 sandbox happy-path 升格为 prod 闭环。
- ❌ 不默认开启 prod provider · 不把 demo `WC-DEMO-*` 护栏扩展到 prod 票。
- ❌ 不替代 INT Tier-A · 不升格 merge-blocking CI。

### AllowedPaths

- （批文后 Implementer 裁决 · 预期）prod payment adapter 模块 · prod ledger 配置
- `docs/wave_c/WC_M3_payment_closure_scope_v1.md`（non-goals lift 附录 · 需 Governance 裁决）
- `04_Workflows/tickets/WH-P9-PROD-real-provider-v1_state.md`
- **禁**：`.env` 原文 · runtime checkpoints · 无授权暗部 core

### Acceptance Criteria

- **AC-0**：尚书省 prod 金流批文 ✅（**当前 blocked**）。
- **AC-1**：prod / sandbox adapter 分轨 · env gate default off。
- **AC-2**：staging 或 dry-run 演练证据 · 无 secret 原文泄露。
- **AC-3**：WC-M3 scope non-goals 更新或 override 留痕。

---

## STATE

- **overall_status**: `blocked`
- **current_owner**: orchestrator
- **next_action**: 等待尚书省 prod 金流批文 · 批文前不得改 code / env / prod path
- **last_updated**: 2026-06-24 · P9 payment sandbox follow-up 票落地代理
- **wave**: Wave-P9 · prod real payment provider
- **status_by_role**:
  - **Orchestrator (A)**: done — 2026-06-24 开 FRAME · 标 blocked
  - **Implementer (B)**: blocked
  - **Reviewer (C)**: blocked
  - **Scribe (D)**: blocked
- **notes**:
  - **等待尚书省 prod 金流批文** — sandbox 线已完成 mock adapter + happy-path；prod provider 另轨
  - WC-M3 scope §5 明示不接 Stripe / 真实 provider · 本票为升格入口 · 须批文 + override 留痕

---

## B_REPORT (Implementer)

- **status**: blocked · frame_only
- **written_date**: —
- **purpose**: prod 真实 payment provider 与 prod ledger 接入（批文后）；与 sandbox 分轨。
- **planned_operations**（批文后大纲）:
  1. Governance 确认 prod provider 选型 · env 键 · ledger 路径 · rollback playbook。
  2. 实现 prod adapter · webhook / idempotency · 与 order transition 集成。
  3. Staging 演练 → 尚书省 go/no-go → prod 启用（canary 若 playbook 要求）。
  4. 更新 WC-M3 scope non-goals lift · Progress 战报。

---

## C_REPORT (Reviewer)

- **verdict**: `not_yet_reviewed`
- **review_date**: —
- **core**: prod 真实金流 provider 可审计接入；sandbox 与 prod 分轨；须批文。
- **gaps**: 尚未实作 · **blocked 等待尚书省 prod 金流批文** · 无 prod provider · 无 prod ledger。

---

## D_REPORT (Scribe)

- **handoff_date**: 2026-06-24
- **depends_on**:
  - `WH-P9-PROD-payment-closure-bootstrap-v1`（WC-M3 scope SSOT）
  - `WH-P9-PROD-order-status-transition-impl-v1`
  - `WH-P9-PROD-payment-sandbox-adapter-v1`（sandbox 契约参考 · 分轨）
  - `WH-P9-PROD-payment-happy-path-execute-v1`（sandbox 演练证据）
  - **外部**：尚书省 prod 金流批文
- **unlocks**（预计升级 · 批文 + 完工后 · 本票不修改他票）:
  - `WH-P9-PROD-payment-closure-bootstrap-v1` — WC-M3 prod 闭环语义升格（非 sandbox-only）
  - P9 Phase 订单/金流 % — prod 子线可诚实上调（Dashboard 由授权方更新）
  - `WH-P9-PROD-payment-happy-path-execute-v1` — 仍保持 sandbox 证据 · prod _claim 另述
