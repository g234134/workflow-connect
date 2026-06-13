# TICKET STATE · WC-PRE-07 · P6 toolchain smoke mandatory CI runner v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。
> 设计 SSOT（待建）：`docs/toolchain-smoke-mandatory-ci-runner-v1.md`（CH-01）
> Rollout 决策：`docs/governance/WC_PRE_06_07_rollout_plan.md` §7

---

## FRAME

- Goal: 为 WC-PRE-06/07 toolchain smoke CI 升格路径提供**独立设计稿**与本 ticket state，使 smoke matrix runner 的 PR CI 行为（L1 advisory → L2 selective mandatory）可开票、可验收、可回滚。
- Scope:
  - 新建 `docs/toolchain-smoke-mandatory-ci-runner-v1.md`（L1/L2 行为 · YAML tier 对齐 · 与 eval-gate 去重 · rollback）
  - 维护本 state 檔 FRAME/STATE；Scribe 对齐 `04_Workflows/tickets/README.md` 与 rollout plan CH-01
  - 引用 rollout plan §7 已决策项（D1/D3/D4/D5）；**不**在本票直接改 workflow
- NonScope:
  - 修改 `.github/workflows/*`、branch protection、P3.5 正文表（留 `WC-IMPL-SMOKE-CI-L1` / `L2` · `WA-T3-AMEND-*`）
  - INT Tier-A 进 PR CI（CH-50）、toolchain health dashboard 升格（WC-PRE-06 / `WC-IMPL-L1`）
  - 将 `aggregated_health_score` 或 matrix `estimated_seconds` 写成 SLA
- AllowedPaths:
  - `docs/toolchain-smoke-mandatory-ci-runner-v1.md`（新建）
  - `04_Workflows/tickets/WC-PRE-07_state.md`（本檔）
  - `docs/governance/WC_PRE_06_07_rollout_plan.md`（交叉引用 · 非本票 primary）
  - `routing/toolchain_smoke_matrix_v1.yaml`（只读引用；YAML 变更另票 CH-12）
- BlockedPaths:
  - `.github/workflows/*` · branch protection settings
  - `docs/phase3-5-cost-model-governance-contract-v1.md` 正文表
  - 暗部 `core/*` · venv 树 · `.env`
- Dependencies:
  - **WC-PRE-06**（`docs/toolchain-observability-governance-upgrade-v1.md` · design_ready · pending_approval）
  - **WC-PRE-05**（本地 smoke runner · accepted_with_gaps）
  - Rollout plan §7 D5 = YES（授权本票 doc + state）
- AcceptanceCriteria:
  - 独立设计稿存在且覆盖：L1 `--tier optional_ci` advisory · L2 白名单 `TS-TOOLCHAIN-DASHBOARD-UNIT` + `TS-W3TL-UNIT` · 明确 **不含** `TS-ROUTING-EVAL-*` · 挂载点 = `eval-gate-ci.yml`
  - 本 state `overall_status` 从 `draft` → `design_ready` 时 FRAME 已冻结
  - 设计稿含 `approval_status` 或等效批文栏；无批文不得宣称为 PR required

---

## STATE

- overall_status: **draft**
- current_owner: orchestrator
- next_action: Scribe 按 CH-01 起草 `docs/toolchain-smoke-mandatory-ci-runner-v1.md`；Orchestrator 冻结 FRAME 后转 review
- last_updated: 2026-06-13 · orchestrator
- status_by_role:
  - orchestrator: in_progress
  - implementer: n/a
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

<!-- Implementer 填 -->

---

## C_REPORT

<!-- Reviewer 填 -->

---

## D_REPORT

<!-- Scribe 填 -->
