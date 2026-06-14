# TICKET STATE · WC-IMPL-SMOKE-CI-L1 · optional-ci-smoke-advisory-wiring-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。
> **定位**：rollout CH-32～CH-34 · D1/D4 决策下的 smoke matrix `optional_ci` PR advisory 接线；**不**升格 merge gate。

---

## FRAME

- Goal: 在 `eval-gate-ci.yml` job `eval-gate` 上接线 smoke matrix runner（`--tier optional_ci`），产出结构化 `smoke_ci_summary.json` 并供 governance snapshot / artifact 消费；全程 **advisory · non-blocking**。
- Scope:
  - `.github/workflows/eval-gate-ci.yml` 增 smoke matrix step（`continue-on-error: true`）；建议命令对齐 rollout CH-32
  - `scripts/run_toolchain_smoke_matrix.py` 或 thin wrapper 输出 `smoke_ci_summary.json`（CH-33 类比 core-agent-smoke）
  - snapshot step 传入 `--smoke-results-json`（若与 matrix summary 合并）或扩展 `_CI_OBSERVED_SMOKES` 观测
  - 上传 smoke CI summary + governance snapshot 为 PR artifact
  - `tests/test_phase6_toolchain_smoke_matrix_v1.py` 或新 contract test：CI 命令与 YAML `optional_ci` entries 对齐（CH-34）
  - 更新 `docs/governance/WC_PRE_06_07_rollout_plan.md` Phase 3/Phase 2 索引
- NonScope:
  - **禁止**改 branch protection / required checks
  - **禁止**将 smoke step 升格为 mandatory 或移除 `continue-on-error: true`
  - **禁止**跑 `release_only` · 全长 `TS-AGENT-LINES-CI` · INT Tier-A
  - **不**在本票改 P3.5 正文表（须 `WA-T3-AMEND-*`）
  - **不**实现 L2 selective mandatory（见 `WC-IMPL-L2` · `WC-IMPL-SMOKE-CI-L2`）
- AllowedPaths:
  - `.github/workflows/eval-gate-ci.yml`（job `eval-gate` · advisory only）
  - `scripts/run_toolchain_smoke_matrix.py`
  - `scripts/generate_toolchain_governance_snapshot.py`（观测字段 / external JSON 映射）
  - `tests/test_phase6_toolchain_smoke_matrix_v1.py` · `tests/test_run_toolchain_smoke_matrix_v1.py`
  - `docs/governance/WC_PRE_06_07_rollout_plan.md`
  - `04_Workflows/tickets/WC-IMPL-SMOKE-CI-L1_state.md`（本票）
- BlockedPaths:
  - GitHub branch protection / repo settings
  - `docs/phase3-5-cost-model-governance-contract-v1.md` §2 正文表
  - `routing/toolchain_smoke_matrix_v1.yaml` gate_class 升格（L2 另票 CH-42）
  - `.github/workflows/core-agent-smoke.yml` mandatory smoke 语义
- Dependencies:
  - **WC-IMPL-L1** — snapshot advisory 已落地（`04_Workflows/tickets/WC-IMPL-L1_state.md` · done）
  - **WC-PRE-05** — 本地 smoke runner（accepted_with_gaps）
  - **WC-PRE-07** — smoke CI 设计稿（CH-01 · draft；D5=YES 授权 doc）
  - **Rollout D1/D4** — health + optional_ci advisory 一并上 · 挂载 `eval-gate-ci.yml`
  - **批文** — `approval_status.L1=approved` 或尚書省等价 observability 授权（CH-30/32 施工前提）
- AcceptanceCriteria:
  1. PR workflow 含 smoke matrix step；`continue-on-error: true`；失败不阻 merge
  2. `optional_ci` tier（`TS-ROUTING-EVAL-UNIT` · `TS-ROUTING-EVAL-DRYRUN`）在 CI 有 `last_result` 观测；`MS-OPTIONAL-CI-GAP` 在 eval-gate-pr 路径可消减
  3. 结构化 summary JSON 可被 snapshot 或 artifact upload 消费
  4. Contract test 验证 CI 命令与 `routing/toolchain_smoke_matrix_v1.yaml` optional_ci entries 一致
  5. **未**新增 required check；**未**改 mandatory trio 语义
- Parallelizable: **是** — 可与 `WC-IMPL-HOOKS` 并行；须在 `WC-IMPL-L1` merged 后；**不可**与 `WC-IMPL-L2` 并行启用 hard fail

---

## STATE

- overall_status: frame_ready
- current_owner: orchestrator
- next_action: 等待 `approval_status.L1` 或尚書省 observability 授权后派 Implementer；可先补 CH-01 design spec
- last_updated: 2026-06-13 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: pending
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
