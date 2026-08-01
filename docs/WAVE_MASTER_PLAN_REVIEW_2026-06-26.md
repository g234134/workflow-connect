# Wave Master Plan Review — SSOT

> **Authority**: Master Plan Review 两轮结论 + 第三輪 Orchestrator 修訂沿革的**单一落盘来源**  
> **Scope**: `04_Workflows/tickets/W-MASTER-wave-plan_state.md` Wave 1–5 规划层  
> **Checklist**: `docs/wave-master-ticketing-playbook.md` §5.3  
> **Review date**: 2026-06-26  
> **Transcripts**（归档引用，非 SSOT）:  
> - Round 1: [Wave Master Plan Review](7d630001-ec4e-4561-bbef-2f7e4dcf49d9)  
> - Round 2: [Wave Master Plan Review Round 2](26967be7-cc5c-4cf8-a7d4-9c8f11f805d7)

---

## Executive Summary

| 轮次 | Verdict | 状态 |
|------|---------|------|
| **Round 1** | `PLAN_WITH_GAPS` | 已归档 · 见 §Round 1 |
| **Round 2** | `PLAN_WITH_GAPS` | 已归档 · 见 §Round 2 |
| **Round 3（Orchestrator 修訂）** | — | RB-1/RB-2/RB-3 文档修訂完成 · **待 Master Reviewer 轻量复验** |
| **当前有效 verdict** | **`PLAN_WITH_GAPS`** | 第三輪 Reviewer 复验通过前 **不得** 宣告 `PLAN_READY` 或全量开 Implementer |

五 Wave 规划**整体诚实、Wave 3/4 尤其可施工**；经 Round 2 Planner 修正与 Round 3 Orchestrator 裁定（方案 A），Master CP SSOT、高阶 Ownership/Cross-Wave 与 STATE 元数据已对齐。**individual ticket FRAME 未改** — 第三輪 Review 为轻量文档一致性复验。

---

## Round 1 Summary（压缩版）

**Reviewer**: Wave Master Reviewer / Code Inspector  
**Date**: 2026-06-26  
**Verdict**: **`PLAN_WITH_GAPS`**

### 优点（摘要）

- >80% Phase 仅补 doc/SSOT/observability 缺口，未重开大工程
- Human/infra/security 标记诚实；Wave 4 AC-AI / AC-HUMAN 分栏为良好范本
- Advisory / sandbox 叙事强；B/C/D/O 四阶段可落地
- Multi-Chat 施工链（template → commands → observer → checklist）设计完整

### Blocking Issues（B-1〜B-8）

| ID | 摘要 | Round 2 状态 |
|----|------|-------------|
| **B-1** | Wave 1 ↔ Wave 5 大面积重复（schema/commands/INDEX） | → **Partially** → Round 3 **Resolved**（方案 A · 见 §RB-1） |
| **B-2** | Wave 2 缺 G-1–G-5 resume-loop 票 | **Resolved** — `W2-P7-matrix-G1-G5-resume-loop-v1` |
| **B-3** | Wave 2 缺 P7 advisory CI 诚实索引票 | **Resolved** — `W2-P7-advisory-ci-ssot-index-v1` |
| **B-4** | §Cross-Wave 与 notify 接線票不符 | **Resolved** — notify 线边界裁定（本 Plan 不含 transport 施工票） |
| **B-5** | Wave 1 与 §Wave Ownership 焦点偏离 | → **Partially** → Round 3 **Resolved**（见 §RB-2） |
| **B-6** | W-MASTER STATE 元数据过期 | → **Partially** → Round 3 **Resolved**（见 §RB-3） |
| **B-7** | Wave 2 W2-T1–T4 缺 `verify_commands` | **Resolved** |
| **B-8** | Wave 5 缺 WC-PRE-06/07 批文/设计票 | **Resolved** — `W5-WC-PRE-06` · `W5-WC-PRE-07` |

### Round 1 Playbook §5.3 快照

| # | 结果 |
|---|------|
| 1 每 Wave ≥1 票 | ✅ |
| 2 ID 前缀一致 | ⚠️ W1/W5 `W*-T*` 混用 |
| 3 cycles ≤2 | ✅ |
| 4 >80% 仅补缺口 | ✅ |
| 5 human/infra/security | ⚠️ Wave 5 缺 WC-PRE |
| 6 observability 抽样 | ⚠️ Wave 2 部分缺 verify_commands |
| 7 无 Phase% 上调 | ✅ |
| 8 Cross-wave 一致 | ❌ |
| 9 与 W-ORCH 无 hard conflict | ⚠️ |

**Round 1 结论**：架构成熟、诚实性高；Wave 1/5 去重、Wave 2 关键缺口、Cross-wave 叙事、STATE 同步完成前不宜 `PLAN_READY`。

---

## Round 2 Summary

**Reviewer**: Wave Master Reviewer / Code Inspector（第二輪）  
**Date**: 2026-06-26  
**Verdict**: **`PLAN_WITH_GAPS`**

### 相对 Round 1 的实质改善

- Wave 2 补 G-1–G-5 matrix 票 + P7 advisory CI SSOT 票
- Wave 2 observability（W2-T1–T5 + 新票）补全 `verify_commands`
- Wave 5 增 WC-PRE-06/07；Wave 1 收敛为四张 `W1-P75-*` P7.5 票
- notify 线边界（B-4 裁定）写入 Cross-Wave

### Round 2 剩余 Blocking（RB-1〜RB-3）

| ID | 来源 | 摘要 |
|----|------|------|
| **RB-1** | B-1 残余 | Master CP schema/commands **双向 defer** · 无 active 票承接 |
| **RB-2** | B-5 残余 | §Wave Ownership / §Cross-Wave 仍列 W1-T1–T5 · 与 Wave 1 实际 `W1-P75-*` 不符 |
| **RB-3** | B-6 残余 | STATE / Ready-for-Parallelization / C_REPORT 过期 · Review 未落盘 |

### Round 2 Playbook §5.3 快照

| # | 结果 |
|---|------|
| 1–7 | ✅（Wave 2 observability 已闭合） |
| 8 Cross-wave 一致 | ❌ W1 CP SSOT 悬空 + 表与票不符 |
| 9 与 W-ORCH | ⚠️ W4 SSOT 票已规划 · 待施工 |

**Round 2 结论**：显著改善 Wave 2/5/1 聚焦；**尚不足以 `PLAN_READY`** — Orchestrator 须完成 RB-1 + RB-2 后触发第三輪轻量 Review。

---

## RB-1〜RB-3 沿革

### RB-1 — Master CP 骨架 SSOT

| 阶段 | 状态 | 处置 |
|------|------|------|
| **Round 1（B-1）** | Blocking | W1-T1/T2/T3/T4 与 W5-T1/T2/T5 大面积重复 · Implementer 双份施工风险 |
| **Round 2 Planner** | Partially | Wave 1 删 W1-T1–T4 defer W5；Wave 5 删 W5-T1/T2 defer W1 → **双向 defer · 无 active 票** |
| **Round 3 Orchestrator** | **Resolved** | **方案 A 裁定**：**Wave 5 = Master CP SSOT**（W5-T1 commands · W5-T2 schema/instruction · W5-T5 lane index）；Wave 1 = 四张 `W1-P75-*` **只消费、不维护** CP 模板 |

**当前 SSOT 表**（见 `W-MASTER` §Wave 1 / Wave 5 去重裁定）：

| Capability | 权威 Wave | Active 票 |
|------------|-----------|-----------|
| ticket schema 模板 | W5 | W5-T2 |
| Multi-Chat commands | W5 | W5-T1 |
| instruction / reviewer 附页 | W5 | W5-T2 + W5-T4 |
| lane / playbook 索引 | W5 | W5-T5 |
| P7.5 上游功能 | W1 | W1-P75-*（4 票） |

### RB-2 — §Wave Ownership / §Cross-Wave 与高阶表同步

| 阶段 | 状态 | 处置 |
|------|------|------|
| **Round 1（B-4/B-5）** | Blocking | Ownership 列 Master CP · 实际票偏 P7.5；Cross-Wave W2→W3 notify 无对应票 |
| **Round 2** | Partially | B-4 notify 边界已裁定；Ownership/Cross-Wave 仍引用已删 W1-T1–T4 |
| **Round 3 Orchestrator** | **Resolved** | §Wave Ownership 表同步至 `W1-P75-*` + W5 CP SSOT；§Cross-Wave Dependencies 移除 W1-T1–T4 引用；Wave 5 内依赖图改为 W5-T1/T2 → W5-T4/T5；并行规则更新 |

### RB-3 — STATE / 并行清单 / C_REPORT / Review 落盘

| 阶段 | 状态 | 处置 |
|------|------|------|
| **Round 1（B-6）** | Blocking | `planning_status` / notes 仍写「待 Planner 填 Wave 區塊」 |
| **Round 2** | Partially | `planning_status: wave5_round2_revised` 反映修正中；Ready-for-Parallelization / C_REPORT 仍过期；Review 仅 transcript |
| **Round 3 Orchestrator + Scribe** | **Resolved** | STATE 元数据更新（`master_plan_revised_round3`）；Ready-for-Parallelization 勾选五 Wave 已填；**本檔落盘** 为 Review SSOT；第三輪 Reviewer 复验 pending |

---

## Master Plan Review Verdict（playbook §5.4）

- **reviewer_date**: 2026-06-26
- **verdict**: **`PLAN_WITH_GAPS`**
- **waves_reviewed**: W1–W5
- **review_rounds_completed**: 2（Reviewer）+ 1（Orchestrator 文档修訂）
- **summary**: 两轮 Review 均判定 `PLAN_WITH_GAPS`。Round 2 闭合 Wave 2 缺口、observability、WC-PRE 与 notify 边界；Round 3 Orchestrator 以方案 A 闭合 RB-1/RB-2/RB-3。**待第三輪 Master Reviewer 轻量复验**后方可升格 `PLAN_READY`。
- **blocking_issues**:
  - 无 **新** P0 blocking（RB-1/RB-2/RB-3 已由 Orchestrator 修訂）
  - **Gate**: 第三輪 Reviewer 须确认高阶表与 Wave 1/5 active 票一致 · 无 residual 双向 defer
- **over_claims_found**: 无新增（Round 1 已标 W-ORCH 快照误读风险 · W4 SSOT 票已规划修正）
- **per_wave_notes**:
  - **W1**: 四张 `W1-P75-*` · 只消费 W5 CP · 不维护 schema/commands
  - **W2**: 解阻五票 + matrix/advisory · observability 合格 · spec-only 诚实
  - **W3**: Round 1 已达标 · 未重跑 Round 2 · 无新 blocking
  - **W4**: 最佳实践 AC-AI/AC-HUMAN · 与 Dashboard 06-25 一致
  - **W5**: Master CP SSOT（W5-T1/T2/T5）+ observer/checklist + WC-PRE doc-only
- **next_action**: 召 **Master Reviewer 第三輪（轻量）** → 目标 `PLAN_READY` → 通过后开 Implementer 并行

---

## 何时可以宣告 `PLAN_READY`

须**同时**满足 `docs/wave-master-ticketing-playbook.md` §5.3 checklist **全部 blocking 项（#1–#7, #9）** 与下列 gate：

### 第三輪 Reviewer 轻量复验（必做）

1. **RB-1 闭合确认**：Master CP 单一 Wave SSOT = **Wave 5**（W5-T1/T2/T5 active）· Wave 1 无 CP 主施工票 · 无双向 defer
2. **RB-2 闭合确认**：§Wave Ownership · §Cross-Wave Dependencies · Wave 5 内依赖图与 **active 票 ID** 一致 · 无 W1-T1–T4 幽灵引用
3. **RB-3 闭合确认**：STATE `planning_status` / `reviewer_verdict` / Ready-for-Parallelization 与本文档一致
4. **Playbook §5.3 #8**（非 blocking 但应记录）：Cross-wave 叙事与票区一致 — Round 3 修訂后预期 ✅

### `PLAN_READY` 定义（摘自 `W-MASTER` §Review Protocol）

- 五 Wave 均有 ≥1 票（或 explicit blocked/解阻说明）
- 无 over-claim · 依赖 / human 标注完整
- 无跨 Wave ID 冲突
- **无 open P0 blocking**（含 RB 残余）

### 宣告 `PLAN_READY` 后的允许动作

- Orchestrator 更新 STATE：`planning_status: ready_for_execution` · `reviewer_verdict: PLAN_READY`
- 开 Chat 1–5 Implementer 并行（遵守 Wave 内依赖与 human blocked 表）
- Scribe 可选更新 `04_Workflows/WORKFLOW_INDEX.md`

### 仍 **不在** `PLAN_READY` 范围（诚实 defer）

- P10 runtime gap（S15 notify · intake API · prod 闭环）
- Wave 2 notify transport 接線（须另开执行票）
- Human GA / CI workflow_dispatch（Wave 4 AC-HUMAN）
- WC-PRE-06/07 尚書省批文（design 票 AI 可交付 · approval 仍 human）

---

## 索引

| 类型 | 路径 |
|------|------|
| Master state | `04_Workflows/tickets/W-MASTER-wave-plan_state.md` |
| Playbook | `docs/wave-master-ticketing-playbook.md` |
| Reviewer checklist（施工后） | `04_Workflows/review_checklists/wave-master-plan-reviewer-v1.md`（W5-T4 交付物） |
| Phase% SSOT | `docs/WAVE_PROGRESS_DASHBOARD.md` |

---

*版本：v1 · 2026-06-26 · Master Scribe 落盘 · Round 1+2 Review + Round 3 Orchestrator 修訂沿革*
