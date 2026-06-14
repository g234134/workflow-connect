# WC Toolchain Governance L2 — Selective Mandatory Design Draft

> **票号**：WC-IMPL-L2 前置设计稿（**doc-only**；**不**改 CI / branch protection）  
> **角色**：Governance / Design Engineer  
> **成文日期**：2026-06-13  
> **性质**：L2 selective mandatory 升格设计草案 · 供尚書省／治理委员会批文  
> **上位 SSOT**：`docs/toolchain-observability-governance-upgrade-v1.md` · `docs/governance/WC_PRE_06_07_rollout_plan.md` §3.6 · §7 · `04_Workflows/tickets/WC-IMPL-L1_state.md`

---

## 背景（L0 / L1 已实现摘要）

| 级别 | 已交付能力 | 对 PR merge 的影响 |
|------|------------|-------------------|
| **L0** | `scripts/run_toolchain_health_dashboard.py`（`toolchain_health_v1` · 默认 `--dry-run`）+ 本地 `artifacts/toolchain/`；`scripts/generate_toolchain_governance_snapshot.py` 嵌入 health/matrix 只读快照 | **无** |
| **L1（snapshot advisory）** | `WC-IMPL-L1`：`toolchain_governance_snapshot_v1` 增 `advisory_level` / `advisory_findings[]` / MissingSignalRules v1；`eval-gate-ci.yml` · `core-agent-smoke.yml` 既有 snapshot step 打印 L1 advisory block + `::warning`；**`--non-blocking` · `continue-on-error: true` 不变** | **无**（job 始终 pass） |
| **L1（rollout 待办）** | rollout plan CH-30/32：独立 health dry-run step 与 smoke matrix `optional_ci` advisory step（**尚未**作为本稿前提；L2 可与之并行或后续合并） | **无** |

**现状结论**：PR 路径上已有 **结构化可见度**（L0 snapshot + L1 advisory），但 **无任何 toolchain health / smoke 升格为 merge blocker**；P3.5 表尚无 `OG-TOOLCHAIN-HEALTH` 正式行。

---

## 目标 — L2 selective mandatory 要 gate 什么

> **命名**：本稿 L2 指 **toolchain health + smoke matrix 治理级别**；与 Monitoring Graph L0/L1/L2（`AGENTS.md`）**不同轴**，禁止混用。

### 2.1 总定位

在 **不破坏** P3.5 mandatory trio（eval-gate + core-agent-smoke）、**不将** `aggregated_health_score` 升格为 SLA、**不将** INT Tier-A / `TS-MVP-MAINLINE` 默认塞进 PR 的前提下，对 **选定 workflow / ci_context** 启用 **selective mandatory**：

1. **Toolchain health hard assert**（dashboard dry-run 或 snapshot 内嵌 health 等价路径）
2. **Smoke matrix 白名单 hard assert**（最小 mandatory 子集，非全长矩阵）

仍保持 `blocks_mainline=false`：L2 失败阻 PR merge，**不等同** MVP mainline regression 失败语义。

### 2.2 Health gate 条件（hard assert · 对齐 rollout §7 D2）

| 条件 | 类型 | 说明 |
|------|------|------|
| `ok == true` | **hard** | 顶层健康旗标 |
| `sections_populated >= 4` | **hard** | 五核心区块至少四块为 `ok` 或 `degraded`（非 `missing`） |
| `sections.catalog_health.ok == true` | **hard** | 双 catalog JSON 可读且 revision 未 stale |
| `aggregated_health_score >= N` | **不采用** | 启启发式分数；**非** SLA；仅 artifact / 人工 triage |
| `gate_class` metadata | doc | L2 实施时可提案 `toolchain_health_v1.1` 标记 `required`；须 semver bump 专票 |

**infra_gap 缓解（设计约束）**：当 outbox 长期空导致 section `missing` 时，实施票须区分 **可恢复 infra_gap** 与 **真 regression**；禁止「全 missing → 全 PR 红」无分类硬 fail（见 rollout §4.1）。

### 2.3 Smoke selective mandatory 白名单（对齐 rollout §7 D3）

| smoke_id | L2 mandatory | 理由 |
|----------|--------------|------|
| `TS-TOOLCHAIN-DASHBOARD-UNIT` | **YES** | 战车根 dashboard contract · 低耗时 · 与 health 同轴 |
| `TS-W3TL-UNIT` | **YES** | tabular tool catalog 最小单元覆盖 |
| `TS-ROUTING-EVAL-UNIT` | **NO** | 已在 `eval-gate-ci.yml` PR job 执行；避免重复与超时 |
| `TS-ROUTING-EVAL-DRYRUN` | **NO** | 同上 |
| `TS-CORE-AGENT-SMOKE-PR` | **NO** | 属 P3.5 mandatory trio · `core-agent-smoke.yml` |
| `TS-MVP-MAINLINE` | **NO** | `release_only` · 不进 PR CI（rollout C3） |
| `TS-AGENT-LINES-CI` 全长 | **NO** | 超时 / flaky 风险（~120s+） |

**L1 对比**：L1 仍可对 `--tier optional_ci`（含 routing eval entries）作 advisory；L2 required **仅**上表白名单。

### 2.4 Snapshot advisory → L2 升格关系

| 信号 | L1（现况） | L2（目标） |
|------|------------|------------|
| MissingSignalRules `critical` | `::warning` · exit 0 | 选定规则 **升格为 step/job fail**（规则子集由实施票冻结） |
| MissingSignalRules `warn` | advisory only | **仍为 advisory**（不阻 merge） |
| `--non-blocking` | 必须 exit 0 | L2 required step **移除** `--non-blocking` 或等价 hard fail 路径 |

建议 L2 hard fail 最小规则集（与 health + smoke 对齐）：

- `MS-HEALTH-ASSEMBLY` · `MS-HEALTH-SECTIONS` · `MS-MATRIX-LOAD` · `MS-MATRIX-EMPTY`
- 对白名单 smoke：`MS-CI-SMOKE-MISSING` · `MS-CI-SMOKE-FAILED`（**限定** `TS-TOOLCHAIN-DASHBOARD-UNIT` · `TS-W3TL-UNIT`）
- **不**将 `MS-OPTIONAL-CI-GAP` · `MS-HEALTH-DEGRADED`（warn 级）升格为 fail

---

## 范围 — 仅针对哪些 workflow / ci_context

### 3.1 挂载点（对齐 rollout §7 D4）

| 项 | 决策 |
|----|------|
| **主 workflow** | `.github/workflows/eval-gate-ci.yml` → job `eval-gate` |
| **ci_context** | `eval-gate-pr`（`generate_toolchain_governance_snapshot.py` 已锚定） |
| **不新建** | 默认 **不**新增第四 workflow（`toolchain-gate-ci.yml`）；required check job name 由 `WC-IMPL-L2` 冻结 |
| **core-agent-smoke** | **不在本稿 L2 范围**升格 toolchain health required check；该 workflow 保留 L1 snapshot advisory only |

### 3.2 本稿覆盖的 gate 类型

| gate 轴 | L2 selective mandatory | 说明 |
|---------|------------------------|------|
| Toolchain health dashboard | **是** | hard assert §2.2 |
| Smoke matrix 白名单 | **是** | §2.3 两 id |
| Governance snapshot advisory | **部分升格** | §2.4 critical 子集 → fail |
| INT Tier-A / Wave 7 regression | **否** | 另票 CH-50 |
| Observability `obs.*` / wf_status | **否** | Wave B 永久分轨 |

### 3.3 P3.5 / Phase 6 登记（非本稿直接改表）

L2 实施前须独立票：

- `WA-T3-AMEND-OG-TOOLCHAIN` — P3.5 增 `OG-TOOLCHAIN-HEALTH`（L2 时 class 改 `mandatory` 须批文）
- `WA-T3-AMEND` 或等价 — smoke 白名单升格 `OG-TOOLCHAIN-SMOKE-CI` mandatory 行（CH-43）
- P6 附录 A 新增 `TS-TOOLCHAIN-DASHBOARD-PR` / smoke CI PR entries（CH-12）

---

## 升格条件 — 从 L1 到 L2 所需观测数据 / 稳定性指标

> 来源：`docs/toolchain-observability-governance-upgrade-v1.md` §2.2 L1→L2 · rollout §4.2 P4 · **须全部满足 + 尚書省批文**。**禁止跳级**（L0→L2）。

| # | 门槛 | 证据类型 | 观测窗口 / 阈值 |
|---|------|----------|-----------------|
| **G1** | L1 连续稳定 | GHA metrics · ops 周报 | **21 日**；PR optional/advisory step 失败率 **< 5%**（排除 outbox 空档已知 degraded · 须分类 `infra_gap`） |
| **G2** | 上游 outbox 存在率 | nightly / scheduled 产出 · main 分支 | `outbox/agent_ci/` + `outbox/agent_metrics/metrics_summary.json` **7 日滚动**存在率 **≥ 95%** |
| **G3** | Dashboard hooks 全量 | contract unittest | §5 hooks 含 `audit_gaps_count` · `smoke_matrix_health` 接入且 investigation spec 投影稳定（`WC-IMPL-HOOKS` merged） |
| **G4** | Rollback 演练 | 战报 | 本稿 §7  playbook **1 次**演练并留痕 Progress |
| **G5** | 治理批文 | design doc | `approval_status.L2` = `approved` + 治理委员会签核 |
| **G6** | 实施票 FRAME | ticket state | `WC-IMPL-L2` 已 FRAME 且 NonScope 不含未授权 branch protection |
| **G7** | L1 snapshot advisory 基线 | GHA artifact 抽样 | **≥ 80%** 活跃 PR 可产出 `governance_snapshot.json` 且 `sections_populated ≥ 3`（与 WC-PRE-06 G2 对齐） |
| **G8** | Smoke CI L1 观察（若 CH-32 已上） | smoke summary JSON | 白名单 smoke 在 `eval-gate-pr` **14 日**内 `last_result != failed` 占比 **≥ 95%** |

**L1 子状态说明（2026-06-13）**：`WC-IMPL-L1` snapshot advisory **已落地**；rollout CH-30/32 独立 step **未**必为 G1 计数前提——G1 可以 snapshot step + 本地 health CLI 周报为主，但 G8 依赖 smoke step 实际上线。

**score 阈值**：rollout §7 D2 已裁 **不采用** `aggregated_health_score` hard assert；本稿 L2 不包含 score gate。

---

## 风险与回滚 — L2 开启后如何退回 L1

### 5.1 触发条件

- 误报率升高（outbox 空 → 全 PR 红）
- 白名单 smoke flaky / CI 超时
- 开发者投诉 merge 阻塞
- 尚書省下令紧急回退

### 5.2 决策权（RACI）

| 动作 | 裁决 |
|------|------|
| **L2 → L1**（降为 advisory · 保留 snapshot step） | 工程 on-call **可先执行**；**24h 内**尚書省备案 |
| **L2 → L0**（移除 PR toolchain step） | 须尚書省或治理委员会书面／口头批文 |
| **恢复 L2** | 重新满足 §4 升格门槛 G1–G8 + **新批文** + rollback 根因已修复 |

### 5.3 L2 → L1 回退步骤（建议顺序）

| 步 | 动作 | 验证 |
|----|------|------|
| 1 | GitHub branch protection **取消** toolchain health / smoke L2 required check（**repo admin + 尚書省留痕**） | Settings 截图或 `gh api` 输出 |
| 2 | Revert / disable `WC-IMPL-L2`：workflow step 恢复 `continue-on-error: true` · 移除 `--fail-on-critical` 等等价 hard fail；smoke step 改 advisory / dry-run | 试跑 PR 绿 |
| 3 | 更新 `approval_status.L2` = `rolled_back`；若保留 advisory 则 `L1` = `approved` | `docs/toolchain-observability-governance-upgrade-v1.md` §8 |
| 4 | `04_Workflows/00_Agent_Work_Progress.md` **末尾** append：原因 · 影响 · 是否一次性 | 战报 |
| 5 | 本地确认基线未破坏 | `python scripts/run_toolchain_health_dashboard.py --format json --dry-run --no-write` · `python -m unittest tests.test_toolchain_governance_snapshot_v1 -v` |

### 5.4 L2 → L0（额外）

| 步 | 动作 |
|----|------|
| 6 | 移除 PR 内所有 toolchain L2 hard fail step（含 smoke mandatory execute） |
| 7 | 可选：移除 L1 advisory step（须批文） |
| 8 | `approval_status.L1` = `rolled_back`；通知 Wave C 消费方：toolchain health **非** PR 信号 |

### 5.5 回退后禁止事项

- **禁止**回退未留痕前宣稱「gate 仍为 required」
- **禁止**用 rollback 期间 degraded outbox 判定为产品质量 regression（应标 `infra_gap`）
- **禁止**顺手永久关闭 gate 而不开 governance 回顾票

### 5.6 恢复 L2 检查清单

- [ ] §4 G1–G8 重新满足
- [ ] rollback 根因已修（outbox 恢复 · 阈值调整 · 假阳性修复 · smoke flaky 修复）
- [ ] §5.3 演练记录已审阅
- [ ] 新 `approval_status.L2` = `approved` 批文日期

---

## 下游实施票边界（本稿不开工）

| 票号 | 依赖 | 交付（概要） |
|------|------|--------------|
| **`WC-IMPL-L2`** | 本稿获批 · §4 门槛 · `approval_status.L2` | eval-gate hard fail + selective smoke mandatory + required check 定义（branch protection **单独步骤** · repo admin） |
| **`WC-IMPL-HOOKS`** | WC-PRE-02/04/05 | `audit_health` · `smoke_matrix_health` dashboard sections |
| **`WA-T3-AMEND-OG-TOOLCHAIN`** | OG-TOOLCHAIN-HEALTH 批文 | P3.5 §2.3 正式增行 |
| **`WC-IMPL-SMOKE-CI-L2`** | 可并入 WC-IMPL-L2 | CH-42/43 smoke 白名单 + P3.5 mandatory 修订 |

**FRAME SSOT**：`04_Workflows/tickets/WC-IMPL-L2_state.md`（AllowedPaths / BlockedPaths · branch protection 由 Platform + 尚書省执行 · Implementer 不得自助改 repo settings）

---

## approval_status（L2 专栏 · 待填）

| 字段 | 值 | 填寫人 | 日期 | 备注 |
|------|-----|--------|------|------|
| **L2_design_review** | `pending` | | | 本设计稿整體审阅 |
| **L2_selective_mandatory_scope** | `pending` | | | 确认 §3 workflow / smoke 白名单 |
| **L2_health_hard_assert** | `pending` | | | 确认 §2.2 不含 score |
| **L2_rollback_drill** | `pending` | | | §5.3 演练完成 |
| **L2_effective_date** | — | | | 不得早于 WC-IMPL-L2 merge |

---

## 交叉引用

| 路径 | 关系 |
|------|------|
| `docs/toolchain-observability-governance-upgrade-v1.md` | WC-PRE-06 完整 L0/L1/L2 路径 · §7 rollback 母本 |
| `docs/governance/WC_PRE_06_07_rollout_plan.md` | CH-40～45 · §3.6 L1 snapshot · §7 D1–D5 决策 |
| `04_Workflows/tickets/WC-IMPL-L1_state.md` | L1 advisory 已交付 FRAME / MissingSignalRules |
| `scripts/generate_toolchain_governance_snapshot.py` | L0/L1 snapshot · `_CI_OBSERVED_SMOKES` |
| `routing/toolchain_smoke_matrix_v1.yaml` | Smoke SSOT |
| `docs/toolchain-health-dashboard-v1.md` | WB-T4 health dashboard SSOT |

---

*WC-TOOLCHAIN-GOVERNANCE-L2-DESIGN-DRAFT · doc-only · 2026-06-13 · 未改 CI · 未改 branch protection*
