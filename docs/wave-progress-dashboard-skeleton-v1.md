# Wave Progress Dashboard Skeleton v1

> **Ticket lane**: G5 / G6 · Lane B Implementer · Foundation round  
> **Parent SSOT**: `docs/WAVE_PROGRESS_DASHBOARD.md`（Phase% 唯一数字 SSOT · **本 skeleton 不重算 %**）  
> **Date**: 2026-06-26  
> **Status**: doc-only skeleton — structure + ownership + P5/P6 indicator fields

---

## 1. Purpose

本档定义 **Wave Progress Dashboard** 的**结构骨架**与**更新权责**，解决三类常见混淆：

1. **数字轨（Phase%）** 与 **叙事轨（脚注 / Wave-next / 子线表）** 混写于同一读者路径；
2. **blocked / advisory / validated** 等状态词与 Phase% 升降混读；
3. **P5 离线健康度** 与 **P6 smoke / regression** 证据未在 Dashboard 索引层分栏。

**读者**：Orchestrator · Governance · Scribe · Lane planner。  
**非目标**：修改 Phase% 数字 · 替代 `*_state.md` C_REPORT · 宣称 closure。

---

## 2. SSOT 位阶

| 层级 | 文档 / 机制 | 内容 |
|------|-------------|------|
| **Phase% 数字** | `docs/WAVE_PROGRESS_DASHBOARD.md` §Phase 完成度表 | 唯一 % SSOT |
| **结构 / 权责** | **本档** `wave-progress-dashboard-skeleton-v1.md` | 字段定义 · 更新流程 · P5/P6 指标槽 |
| **票级细节** | `04_Workflows/tickets/*_state.md` | C/D_REPORT · STATE |
| **战报 append** | `04_Workflows/00_Agent_Work_Progress.md` **末尾** | 命令证据 · blocked · evidence_tier |
| **里程碑** | `04_Workflows/project_status/master_status.md` | Governance 独占 |

冲突时：**Dashboard Phase% 表** ＞ Progress 口述 ＞ chat 摘要。

---

## 3. 双轨模型（Numeric vs Narrative）

```text
┌─────────────────────────────────────────────────────────────┐
│  NUMERIC TRACK (Governance-only Phase%)                     │
│  WAVE_PROGRESS_DASHBOARD.md §Phase 完成度表               │
│  列：基线 · 当前% · 主要票 · 证据摘要（短）                 │
└───────────────────────────┬─────────────────────────────────┘
                            │ 只引用，不混写长叙事
┌───────────────────────────▼─────────────────────────────────┐
│  NARRATIVE TRACK (Scribe-only footnotes)                    │
│  §Wave-next 敘事刷新 · §子线票级进度 · §Multi-phase smoke   │
│  §完成度躍升說明（历史）· 各 Wave 分栏「註（…）」             │
└─────────────────────────────────────────────────────────────┘
```

**硬规则**

- 叙事节 **MUST** 以「**Phase% 不变**」或等价语句开头（若仅刷新脚注）。
- Scribe **MUST NOT** 在叙事节内插入新的 Phase% 数字作为 SSOT。
- Governance **MUST NOT** 用长篇叙事替换 Phase 表「证据摘要」列（摘要 ≤ 一行关键词）。

---

## 4. Dashboard 结构地图

| 区块 | 位置（父 Dashboard） | 轨 | 可更新角色 |
|------|----------------------|-----|------------|
| Wave A · Phase Foundations | 文首表 | 叙事 + 票状态 | Scribe 脚注 · Orchestrator 状态列 |
| 命名空間 | §命名空間 | 结构 | Governance / Scribe |
| **Phase 完成度表** | §Phase 完成度表 | **数字** | **Governance only** |
| Phase 7.5 + P8.9 能力摘要 | Scribe 收錄表 | 叙事 | Scribe |
| 完成度躍升說明 | `>` 脚注块 | 叙事（历史） | Scribe append · 标注日期 |
| Wave-next 敘事刷新 | `>` 脚注块 | 叙事 | Scribe · **Phase% 不变** |
| P7/P8.5/P9 子线票级进度 | 子表 + mapping 脚注 | 叙事（算术） | Scribe · 来源 `*_state.md` |
| Multi-phase smoke & metrics | 工具表 + release 流程 | **证据索引** | Implementer doc · Scribe 交叉引用 |
| 總覽表 / Wave 1–12 分栏 | 各 Wave 节 | 叙事 + 票 | Scribe 註脚 · 不改 Phase% |
| Wave B · Toolchain | WB-T* 表 | 叙事 + 证据 | Scribe · cross-ref P5/P6 |

---

## 5. 字段权责表

### 5.1 Governance-only（仅治理决议可写）

| 字段 | 所在 | 更新触发 | 证据要求 |
|------|------|----------|----------|
| Phase **当前 %** | Phase 完成度表 | 尚書省 / 授权 Governance 决议 | 票 STATE 加权或 explicit 裁定 · Progress append |
| Phase **基线 %** | 同表「基线」列 | 同上（大版本刷新） | 战报日期锚点 |
| `master_status` 里程碑 | 非 Dashboard 内 | Governance append | OPS_CYCLE / 里程碑协议 |

### 5.2 Scribe-only（工作流可更新叙事）

| 字段 | 所在 | 更新触发 | 禁止 |
|------|------|----------|------|
| Wave-next 敘事段落 | Dashboard 脚注 | Reviewer verdict · runbook · STATE 变更 | 写入新 Phase% SSOT |
| 子线 **当前 %**（P7 sandbox 等） | 子线表 | `*_state.md` 算术 · `_progress_recalc_*.py` 输出 | 覆盖 Phase 主表 P7 % |
| 完成度躍升說明 | 历史脚注 | 日期戳 · 说明「未上调/已上调」 | 与主表 % 矛盾且无解释 |
| Wave 分栏「註（…）」 | 各 Wave 节 | 关票 · deferred 变更 | 宣称 mandatory CI 已开 |
| Multi-phase smoke 建议流程 | §Multi-phase smoke | WORKFLOW_INDEX / 契约同步 | 宣称 GA-ready |

### 5.3 Worker-updatable（Implementer / 票施工 · 非 Phase%）

| 字段 | 所在 | 更新方式 | 验证 |
|------|------|----------|------|
| 票 **状态** / Reviewer verdict | Wave 分栏表 · `*_state.md` | 票 C/D_REPORT | unittest / runner |
| **证据摘要**关键词 | Phase 表第四列 | Governance 摘 Scribe 索引 | 命令 + ok 计数 |
| 工具 / runner 链接 | smoke / health 节 | doc PR cross-ref | WORKFLOW_INDEX |
| P5/P6 **指标槽**（见 §6–§7） | 本 skeleton → Dashboard 引用 | 契约 doc 版本 bump | 对应 runner JSON |

---

## 6. Phase 5 专属指标槽（Dashboard / 离线健康度）

> **Dashboard 当前姿态（06-26）**：P5 **70%** · 主要票 WB-T4 · MP-METRICS-HTTP · Grafana/PG soak placeholder。  
> **本節只定义字段，不上调 %。**

| 指标 ID | 含义 | 数据源 | 更新角色 | skeleton / verify |
|---------|------|--------|----------|-------------------|
| `P5-HEALTH-DASH` | Toolchain 离线健康汇总 | `scripts/run_toolchain_health_dashboard.py` → `toolchain_health_v1` | Implementer 跑 runner · Scribe 索引 | `docs/toolchain-health-dashboard-v1.md` |
| `P5-HEALTH-SCORE` | `aggregated_health_score` 0–100 | 同上 JSON | Observe only | **非 SLA** · optional gate |
| `P5-HEALTH-SECTIONS` | `sections_populated` / `sections_ok` | 同上 | Observe only | 5 core sections |
| `P5-METRICS-HTTP` | `GET /metrics?case_ref=` | `scripts/metrics_http_endpoint_v1.py` | Implementer | MP-METRICS-HTTP 票 |
| `P5-AUDIT-SPEC` | Audit quickview 契约 | `docs/audit-quickview-and-case-history-spec-v1.md` | Scribe cross-ref | WB-T5 |
| `P5-FLEET-METRICS` | MC-METRICS 聚合 | `scripts/aggregate_multi_case_metrics_v1.py` | Implementer | fleet rollup |
| `P5-GRAFANA-SOAK` | Grafana/PG soak | — | **placeholder** | blocked · infra |
| `P5-GATE-CLASS` | Health dashboard gate | `gate_class=optional` | Governance 批文前不变 | WC-PRE-06 |

**P5 更新流程（证据 → 叙事，不改 %）**

1. Implementer 跑 health dashboard dry-run → JSON 存 artifact 或贴 Progress。
2. Scribe 在 Dashboard **Multi-phase / Toolchain** 或 Progress 末尾引用 `aggregated_health_score` / degraded sections。
3. Phase% 上调 **仅** Governance 在 Phase 表改数字并 append Progress 依据。

---

## 7. Phase 6 专属指标槽（测试 / Smoke / Regression）

> **Dashboard 当前姿态（06-26）**：P6 **72%** · WB-T7 · CI-SMOKE · MC-SMOKE · INT gate contract。  
> **本節只定义字段，不上调 %。**

| 指标 ID | 含义 | 数据源 | tier | skeleton / verify |
|---------|------|--------|------|-------------------|
| `P6-INT-TIER-A` | Wave 6/7/8 装配 INT gate | `04_Workflows/_wave7_regression_gate.py --tier A` | L-local mandatory（装配变更） | `docs/phase6-int-regression-gate-contract-v1.md` |
| `P6-MP-SMOKE` | 单 case 七步 release sanity | `scripts/run_multi_phase_smoke_v1.py` | L-local recommended | `docs/smoke-and-regression-contract-v1.md` |
| `P6-MC-SMOKE` | 多 case fleet smoke | `scripts/run_multi_case_smoke_v1.py` | L-local recommended | 同上 |
| `P6-CI-SMOKE` | smoke + metrics wrapper | `scripts/run_ci_smoke_check_v1.py` | L-local · **CI-advisory when wired** | exit 0/1 · non-required default |
| `P6-SMOKE-MATRIX` | Toolchain smoke YAML | `routing/toolchain_smoke_matrix_v1.yaml` | 索引 SSOT | unittest matrix |
| `P6-PR-SMOKE` | PR mandatory trio 之一 | `core-agent-smoke.yml` | CI required | **≠ INT Tier-A** |
| `P6-EVAL-GATE` | eval-gate-ci | `eval-gate-ci.yml` | CI required | routing dry-run |
| `P6-AGENT-LINES-CI` | Agent lines suite | `run_agent_lines_ci_suite.py` | optional | W10-T1 |

**P6 更新流程**

1. MP/MC/CI 绿 → 写 `outbox/verification/**` JSON + Progress（`evidence_tier: L-local`）。
2. Scribe 更新 Dashboard §Multi-phase smoke 流程或脚注 · **不**写「P6 closure」。
3. INT Tier-A 与 MP-SMOKE **分表记录**（见 smoke contract §2）。
4. Phase% 变更 **仅** Governance。

---

## 8. Multi-phase smoke 流程（Dashboard 节对齐）

父 Dashboard §Multi-phase smoke 描述 **release sanity 命令链**；权责如下：

| 步骤 | 命令族 | 产物 | 叙事更新 |
|------|--------|------|----------|
| Fleet 1–3 | MC-SMOKE · MC-METRICS · deny 探针 | `multi_case_smoke_run.json` | Scribe 可引 failed_cases |
| Single 4–7 | MP-SMOKE · MP-METRICS · CI-SMOKE | per-case JSON · exit code | Progress append |

**不得**将七步全绿写成 P7 Round-2 GO · P8 operator 全功能 · GA-ready。

---

## 9. Phase% 更新流程（Governance-only）

```text
1. 收集：*_state.md` C_REPORT · Progress 末尾战报 · recalc 脚本输出（若有）
2. 裁定：尚書省 / 授权 Governance（非 lane Implementer 自裁）
3. 写入：WAVE_PROGRESS_DASHBOARD.md Phase 表「当前%」「证据摘要」「主要票」
4. 留痕：00_Agent_Work_Progress.md 末尾 append（日期 · 旧→新 · 依据票号）
5. 可选：master_status 里程碑（Governance 独占）
```

**禁止**：Scribe 在「Wave-next 敘事刷新」内偷偷改主表 %；Worker 以 local smoke 绿请求上调 P6/P5 %。

---

## 10. 叙事更新流程（Scribe-only）

```text
1. 读：Reviewer verdict · 相关 runbook · 子票 STATE · evidence index
2. 写：Dashboard 脚注 / 子线表 / Wave 註（标注日期 · 「Phase% 不变」若适用）
3. 交叉引用：WORKFLOW_INDEX · 契约 doc · matrix · 不复制 FRAME 全文
4. append：Progress 末尾（ticket_id · group_id · evidence_tier · blocked/next）
```

---

## 11. Non-Claims

| 禁止宣稱 | 正确表述 |
|----------|----------|
| Dashboard skeleton 完成 = Phase 5/6 closure | 结构 SSOT · Phase% 仍见主表 |
| 叙事刷新 = Phase% 重算 | 脚注与数字分轨 |
| health score 高 = prod healthy | offline heuristic · optional |
| MP-SMOKE 绿 = INT Tier-A 绿 | 分表 · 不同 runner |
| CI-SMOKE exit 0 = PR required check 已接入 | 默认 L-local；CI wiring 另票 + 批文 |
| 子线 90% = P7 主表应同 % | 子线为叙事算术 · 主表可保守扣减 |

---

## 12. Verification（本 skeleton）

```bash
# 结构契约（无 venv 要求）
python -m unittest tests.test_phase6_int_regression_gate_contract_v1 tests.test_phase6_toolchain_smoke_matrix_v1 -v

# P5 health skeleton
python scripts/run_toolchain_health_dashboard.py --format json --dry-run --no-write

# P6 smoke skeleton（L-local）
python scripts/run_multi_phase_smoke_v1.py --case-ref demo_phase --format json
python scripts/run_multi_case_smoke_v1.py --cases demo_phase,sampleco --format json
python scripts/run_ci_smoke_check_v1.py --format text
```

---

## 13. Cross-References

| 文档 | 关系 |
|------|------|
| `docs/WAVE_PROGRESS_DASHBOARD.md` | Phase% SSOT · 父文档 |
| `docs/toolchain-health-dashboard-v1.md` | P5 runner spec |
| `docs/smoke-and-regression-contract-v1.md` | P6 MP/MC/CI 契约 |
| `docs/phase6-int-regression-gate-contract-v1.md` | INT gate · 附录 A matrix |
| `docs/full-phase-master-planning-playbook.md` | G5/G6 lane 读法 |
| `04_Workflows/tickets/W-MASTER-full-phase-plan_state.md` | G5/G6 票索引 |

---

*wave-progress-dashboard-skeleton-v1 · Lane B · doc-only · Phase% frozen at Dashboard 2026-06-26*
