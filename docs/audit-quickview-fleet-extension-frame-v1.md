# Audit Quickview — Fleet Extension FRAME (v1)

> **Ticket**: `FP-G5-T4-audit-quickview-fleet-extension-v1` · Full-Phase G5 · P5 · **doc/spec · FRAME** · evidence_tier **L-local**  
> **Date**: 2026-07-10  
> **对齐**：`W-MASTER-full-phase-plan_state.md#G5` · WB-T5 `docs/audit-quickview-and-case-history-spec-v1.md` · 上游 `docs/fleet-metrics-dashboard-operator-v1.md`（FP-G5-T1）

---

## non_claims（置顶 · 必读）

| 本 FRAME **不是** | 说明 |
|-------------------|------|
| ≠ audit／fleet **已上线**产品交付 | 本页仅 **规划 FRAME**（MVP vs stretch）；不改 quickview runtime |
| ≠ 多 case 聚合 CLI **已实现** | 现有 `run_agent_audit_quickview.py` 仍为 **单 `--case-ref`**（WB-T5／W10-T3） |
| ≠ Grafana／PG soak 已接 | 见 `grafana-pg-soak-deferred-index-v1.md`；本 FRAME 不含监控台 |
| ≠ **P5 closure**／Phase% 上调 | FRAME 齐 ≠ Phase 5 结案 |

**位阶**

| 文件 | 角色 |
|------|------|
| **本档** | 多 case audit quickview **聚合扩展 FRAME**（规划） |
| [`docs/audit-quickview-and-case-history-spec-v1.md`](./audit-quickview-and-case-history-spec-v1.md) | WB-T5 **单 case** investigation 契约 SSOT |
| [`docs/agent-lines-audit-quickview-v1.md`](./agent-lines-audit-quickview-v1.md) | 实现附录指针 |
| [`docs/fleet-metrics-dashboard-operator-v1.md`](./fleet-metrics-dashboard-operator-v1.md) | **T1 依赖**：fleet metrics 读法／聚合边界（本 FRAME 叙事前置） |
| INDEX §1.5 · W10-T3 | CLI／unittest 入口（只读引用） |

---

## 1. Purpose

在 **不改 runtime** 的前提下，冻结「audit quickview 多 case／fleet 聚合」的 MVP vs stretch 边界，并显式依赖 FP-G5-T1 fleet operator 语义（case 集合、rollup 诚实边界）。

---

## 2. 依赖叙事（硬串行 T1）

| 上游 | 本 FRAME 如何消费 |
|------|-------------------|
| FP-G5-T1 `fleet-metrics-dashboard-operator-v1.md` | 代表性 case 集、`total_*` 读法、non_claims（≠ Grafana） |
| WB-T5 audit-quickview spec | 单 case wire／investigation view 字段；fleet 扩展 **不得**破坏单 case 契约 |
| `scripts/run_agent_audit_quickview.py` | 现状：一次一案；fleet = **编排层**聚合（另票实作） |

**无 T1 artifact 不得宣称本 FRAME 可执行实作票。**（本轮 T1 已 `done`，故本 FRAME 可写。）

---

## 3. MVP vs stretch

### 3.1 MVP（规划可验收形状 · 另票实作）

| 项 | 说明 |
|----|------|
| 输入 | case 列表（默认对齐 MC-METRICS／T1 代表性集：`demo_phase` · `sampleco/2026-0001`） |
| 行为 | 对每案调用既有单 case quickview（library／CLI 子进程）；**只读** |
| 输出 | fleet summary：`ok_count`／`fail_count`／per-case `gaps` 计数摘要；可选嵌入 metrics `total_*` 交叉引用（读 T1／MC-METRICS，不写） |
| 非目标 | 不写 outbox／checkpoint；不改 WB-T5 JSON schema 必填键 |

### 3.2 Stretch（明确延后）

| 项 | 说明 |
|----|------|
| 跨 case 时间线合并 UI／Grafana | 属监控／产品；链 T2 deferred |
| 全库自动发现全部 `cases/` | 须策略票；默认仍显式 `--cases` |
| 将 fleet audit 升格 required CI／PR block | WC-PRE／批文；非本 FRAME |
| 改暗部／PG 直查 | 宪法 §7；禁止本 FRAME 授权 |

---

## 4. 与 metrics fleet 的分界

| 面 | SSOT／入口 | 本 FRAME |
|----|------------|----------|
| Backlog／ack **数字** rollup | MC-METRICS · T1 operator doc | **可引用**；不重定义字段 |
| Decision／route／CP **调查视图** | WB-T5 · audit quickview CLI | **本 FRAME 扩展对象** |
| Grafana／soak | T2 deferred 索引 | **不包含** |

---

## 5. Mini checklist（后续实作票／Reviewer）

- [ ] 实作票 AllowedPaths 明示；本 FRAME **不**当 runtime 已交付证据  
- [ ] 单 case WB-T5 契约保持；fleet 为编排层  
- [ ] 文案未写「fleet audit 已上线」「P5 closure」  
- [ ] 未改 `scripts/run_agent_audit_quickview.py`（除非另开实作票）  

---

## 6. Verification（本票 AC · `rg`）

```bash
rg "audit-quickview|fleet|non_claims" docs/audit-quickview-fleet-extension-frame-v1.md
```

期望命中：`non_claims`、fleet／MVP／stretch、T1／WB-T5 依赖叙事。
