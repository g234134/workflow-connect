# TICKET STATE · WC-IMPL-L2 · toolchain-governance-l2-selective-mandatory-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。
> **定位**：L2 selective mandatory 治理升格票——在 L1 advisory 稳定观测后，将 **选定** health assert + smoke 白名单升格为 PR merge gate；**branch protection 变更须 repo admin + 尚書省留痕，本票 FRAME 仅定义 workflow 侧行为与验收边界。**

---

## FRAME

- Goal: 在尚書省批准 L2 且满足升格门槛后，交付 toolchain governance **L2 selective mandatory** 的 **可实施 FRAME + 制度留痕**；使 `eval-gate-pr` 路径上 health hard assert 与 smoke 白名单（`TS-TOOLCHAIN-DASHBOARD-UNIT` · `TS-W3TL-UNIT`）成为 PR required 语义，并具备 documented rollback 路径。
- Scope:
  - 引用并冻结设计 SSOT：`docs/governance/WC_TOOLCHAIN_GOVERNANCE_L2_design_draft.md`（§2 gate 条件 · §3 workflow/ci_context · §4 升格门槛 · §5 回滚）。
  - 起草/维护本票 FRAME 内 **AllowedPaths / BlockedPaths / NonScope**，供后续 Implementer 施工票（可为本票实施阶段或子票）引用。
  - 确认 L1→L2 升格证据清单（G1–G8）收集位点：GHA metrics · ops 周报 · Progress 战报 · rollback 演练记录。
  - 定义 branch protection required check **命名与启用顺序**（文档层）；实际 GitHub settings 操作由 Platform + 尚書省执行并留痕。
  - 更新 rollout plan 或 design doc 的 `approval_status.L2` 栏位（Scribe / Governance）。
- NonScope:
  - **禁止**在本票未获 `approval_status.L2=approved` 前修改 workflow pass/fail 或启用 required check。
  - **禁止** Implementer 自行修改 GitHub branch protection / repo settings（含 `gh api` 改 protection rules）。
  - **禁止**将 `aggregated_health_score` 或 advisory 结论升格为 SLA 文案。
  - **禁止**将 INT Tier-A · `TS-MVP-MAINLINE` · P3.5 mandatory trio 升格为本票 L2 范围。
  - **禁止**跳级（L0→L2）；须 L1 观察期满足设计稿 §4。
  - **不**在本票 FRAME 阶段直接 patch P3.5 §2 正文表（须 `WA-T3-AMEND-OG-TOOLCHAIN` / CH-43 独立票）。
- AllowedPaths:
  - `docs/governance/WC_TOOLCHAIN_GOVERNANCE_L2_design_draft.md`（本票 SSOT · 可追加 approval 栏）
  - `docs/governance/WC_PRE_06_07_rollout_plan.md`（§4 Phase 4 · §7 决策对齐 · L2 状态索引）
  - `docs/toolchain-observability-governance-upgrade-v1.md`（§8 `approval_status` · rollback 交叉引用）
  - `04_Workflows/tickets/WC-IMPL-L2_state.md`（本票）
  - `04_Workflows/00_Agent_Work_Progress.md`（**末尾 append** rollback 演练 / 升格留痕）
  - 实施阶段（须另列子 FRAME 或 expand Scope 后）才允许：
    - `.github/workflows/eval-gate-ci.yml`（job `eval-gate` · `ci_context=eval-gate-pr`）
    - `scripts/generate_toolchain_governance_snapshot.py`（L2 fail 语义 · 白名单 smoke 观测扩展）
    - `scripts/run_toolchain_health_dashboard.py`（**仅** CI 调用包装 / threshold assert · **不改**评分哲学）
    - `scripts/run_toolchain_smoke_matrix.py`（白名单 execute · summary JSON）
    - `tests/test_toolchain_governance_snapshot_v1.py` · `tests/test_toolchain_health_dashboard_v1.py` · `tests/test_run_toolchain_smoke_matrix_v1.py`
    - `routing/toolchain_smoke_matrix_v1.yaml`（**仅**新增 PR mandatory tier / gate_class 提案字段 · 须 Reviewer 对照 P6）
- BlockedPaths:
  - GitHub branch protection / repo settings / GitHub Environments（**本票 Implementer 不可直接操作**）
  - `docs/phase3-5-cost-model-governance-contract-v1.md` §2 正文表（须 `WA-T3-AMEND-*` 票）
  - `.github/workflows/core-agent-smoke.yml`（**不得**在本票升格 toolchain L2 required；保留 L1 advisory）
  - `core/wave7_regression_gate.py` · INT Tier-A CI 路径
  - `scripts/run_toolchain_health_dashboard.py` 内评分/section 聚合哲学（非 threshold assert 包装）
  - Observability Wave B 路径（`artifacts/wf/` 升格为 merge blocker）
- Dependencies:
  - **设计稿** — `docs/governance/WC_TOOLCHAIN_GOVERNANCE_L2_design_draft.md`（本票 SSOT）
  - **WC-PRE-06** — `docs/toolchain-observability-governance-upgrade-v1.md`（L0/L1/L2 母本 · rollback §7）
  - **WC-PRE-06/07 rollout** — `docs/governance/WC_PRE_06_07_rollout_plan.md` §3.6 · §7 D2–D4
  - **WC-IMPL-L1** — snapshot advisory 已落地（`04_Workflows/tickets/WC-IMPL-L1_state.md`）
  - **WC-IMPL-HOOKS** — G3 门槛（`audit_health` · `smoke_matrix_health`）· 可并行但 L2 启用前须 merged 或 governance waiver 留痕
  - **尚書省批文** — `approval_status.L2=approved` · rollback 演练 G4 · 升格门槛 G1–G8 证据
  - **Platform / repo admin** — branch protection 增删 required check（CH-40 · **非** Implementer 自助）
- AcceptanceCriteria:
  1. **设计批文**：尚書省／治理委员会审阅 `docs/governance/WC_TOOLCHAIN_GOVERNANCE_L2_design_draft.md`，填写 `approval_status`（L2_design_review · L2_selective_mandatory_scope · L2_health_hard_assert · L2_rollback_drill）为 `approved` 或附条件 approved。
  2. **升格证据**：设计稿 §4 G1–G8 每项有可追溯证据链接或 Progress/ops 周报条目（可标 `infra_gap` 排除项）。
  3. **Rollback 演练**：按设计稿 §5.3 完成 **1 次** L2→L1 桌面演练（含 branch protection 取消步骤 **模拟或 staging**），战报 append 至 Progress 末尾。
  4. **FRAME 冻结**：本票 FRAME 与 design draft §2–§3 一致；Reviewer 确认 NonScope 含「Implementer 不得改 branch protection」。
  5. **实施票前置**：FRAME 获批后，方可开 Implementer 施工（本票 `overall_status` → `in_progress` 或独立 `WC-IMPL-L2-EXEC` 子票）；**本 AcceptanceCriteria 不包含**具体 workflow exit code / unittest 绿度——该等验收写入施工阶段 FRAME 扩展或 B_REPORT。
  6. **制度登记前置**：列出 `WA-T3-AMEND-OG-TOOLCHAIN` / CH-43 是否为 L2 启用阻塞项，并在 FRAME 或 Dependencies 冻结。

---

## STATE

- overall_status: frame_frozen_pending_governance
- overall_status_rationale: FRAME 经 Reviewer 对照 `WC_TOOLCHAIN_GOVERNANCE_L2_design_draft.md` §2–§3 核对后冻结；NonScope 正确约束 branch protection / CI required 变更须批文与 Platform 操作。实施阶段（workflow exit fail · required check 启用）须待 G1–G8 证据 + `approval_status.L2=approved` + rollback 演练后方可 `in_progress`。
- current_owner: orchestrator
- next_action: 启动 L1 观察期（自 2026-06-13）；并行收集 G1–G8 证据（GHA metrics · ops 周报 · Progress 战报）；安排 L2→L1 rollback 桌面演练；等待尚書省 `approval_status.L2=approved` 后方可开 Implementer 施工
- last_updated: 2026-06-13 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: pending
  - reviewer: done
  - scribe: done

---

## B_REPORT

- changed_files: （待填 · 实施阶段）
- artifacts: （待填）
- verification: （待填）
- behavior_notes: （待填）
- deferred_items:
  - branch protection 实际操作（Platform + 尚書省）
  - P3.5 表增行（`WA-T3-AMEND-*`）

---

## C_REPORT

- conclusion: frame_reviewed_pending_governance
- blocking_issues:
  - `approval_status.L2` 仍为 **pending**（设计稿 §approval_status 未填 approved）
  - G1–G8 升格证据**收集中**（无完整 Progress/ops 周报链接闭环）
  - L2→L1 **rollback 桌面演练未做**（设计稿 §5.3 · AC-3 未满足）
  - 以上三项阻塞 Implementer 施工，**不阻塞** FRAME 冻结与制度留痕
- checks_summary:
  - FRAME 与 `docs/governance/WC_TOOLCHAIN_GOVERNANCE_L2_design_draft.md` §2 gate 条件 · §3 workflow/ci_context 对齐
  - NonScope 正确约束：Implementer 不得改 branch protection / repo settings；未获 `approval_status.L2=approved` 前不得改 workflow pass/fail 或启用 required check
  - AllowedPaths 分层清晰：FRAME 阶段仅 docs + 本票 state；workflow/scripts 属实施阶段 expand
  - Dependencies 冻结 WC-IMPL-L1 · WC-PRE-06/07 · WC-IMPL-HOOKS · Platform admin 分工
  - AC-4（FRAME 冻结）满足；AC-1/2/3/5/6 留待治理阶段
- risk_level: medium
- suggestions: 观察期并行推进 WC-IMPL-HOOKS（G3）；`WA-T3-AMEND-OG-TOOLCHAIN` / CH-43 是否在 L2 启用前为硬阻塞项——尚書省裁決后写入 FRAME Dependencies

---

## D_REPORT

- docs_updates:
  - `docs/governance/WC_TOOLCHAIN_GOVERNANCE_L2_design_draft.md` — `approval_status` 栏待尚書省填写（L2_design_review · L2_selective_mandatory_scope · L2_health_hard_assert · L2_rollback_drill）
  - `docs/governance/WC_PRE_06_07_rollout_plan.md` §4 Phase 4 · §7 D2–D4 — 补 L2 `frame_frozen_pending_governance` 索引一句
  - `docs/toolchain-observability-governance-upgrade-v1.md` §8 — cross-ref L1 观察期与 L2 升格门槛
- progress_entry: WC-IMPL-L2 FRAME 冻结关票（非实施关票）：L2 selective mandatory 制度边界已落盘；实施待治理批文。
- followup_suggestions:
  - **L1 观察期起始日：2026-06-13**（与 WC-IMPL-L1 关票同步）
  - **G1–G8 证据收集位点**：GHA workflow run metrics（eval-gate-pr snapshot advisory 样本）· ops 周报 · `04_Workflows/00_Agent_Work_Progress.md` 末尾战报 · rollback 演练记录（Progress append）
  - **尚書省批文要求**：`approval_status.L2=approved`（或附条件 approved）+ rollback 演练 G4 完成 + G1–G8 可追溯证据 + Platform 执行 branch protection required check 留痕（CH-40）
  - 批文前禁止 Implementer patch `.github/workflows/eval-gate-ci.yml` exit 语义
